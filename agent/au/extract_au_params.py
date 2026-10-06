"""Extraction agent for the supported-Au CO-oxidation inputs, then the ACSA self-check on the extracted inputs.

Steps:
  1. pdf -> page-tagged text and page images (agent/extraction/pdf_to_text.py, same converter as methanol);
  2. one gpt-5.5 call per paper, local API-YES gateway first and the advisor key once API-YES is used up
     (agent/extraction/llm_route.py; streamed Responses API, store=false), strict JSON schema below; raw output in
     out/<slug>.json, usage in out/token_usage.csv;
  3. normalize: units to the chain basis, then the protocol's selection rules pick the anchor sample and the
     size-dependence series (no value is typed in by hand);
  4. au_chain.self_check() on the extracted inputs.

    python extract_au_params.py            # extract the papers in pdf/ that have no raw output yet, then check
    python extract_au_params.py --check    # normalize + self-check only

The prompt contains only the paper. Keys are handed straight to the client; they are never printed, logged or stored.
"""
from __future__ import annotations

import argparse
import base64
import csv
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "agent" / "extraction"))
sys.path.insert(0, str(HERE))
import au_chain  # noqa: E402

PDF_DIR, TEXT_DIR, OUT_DIR = HERE / "pdf", HERE / "text", HERE / "out"
USAGE_CSV = OUT_DIR / "token_usage.csv"
ANCHOR_DOI = "10.1016/j.jcat.2006.03.008"      # Janssens et al. 2006: absolute-rate anchor
SIZE_DOI = "10.1016/j.jcat.2006.04.018"        # Overbury et al. 2006: particle-size dependence
DOIS = (ANCHOR_DOI, SIZE_DOI)


def num(desc: str) -> dict:
    return {"type": "object", "additionalProperties": False,
            "required": ["value", "unit", "qualifier", "location", "page"],
            "description": desc,
            "properties": {"value": {"type": ["number", "null"]}, "unit": {"type": ["string", "null"]},
                           "qualifier": {"type": ["string", "null"], "enum": ["=", "<", ">", "<=", ">=", "~", None]},
                           "location": {"type": ["string", "null"]}, "page": {"type": ["integer", "null"]}}}


def obj(props: dict) -> dict:
    return {"type": "object", "additionalProperties": False, "required": list(props), "properties": props}


S = {"type": "string"}
S_N = {"type": ["string", "null"]}
SCHEMA = obj({
    "doi": S, "title": S,
    "samples": {"type": "array", "items": obj({
        "sample_label": S, "support": S_N,
        "au_loading": num("Au loading of the sample"),
        "average_au_diameter": num("average Au particle diameter"),
        "au_dispersion": num("fraction of Au atoms at the surface (dispersion)"),
        "co_oxidation_rate": num("measured CO oxidation rate per gram of catalyst; the stabilized/steady value if both are given"),
        "rate_is_stabilized": {"type": ["boolean", "null"]},
        "catalyst_mass": num("catalyst mass in the activity test"),
        "total_flow": num("total gas flow in the activity test"),
        "temperature": num("activity-test temperature"),
        "pressure": num("activity-test pressure"),
        "feed_co_fraction": num("CO mole fraction in the feed"),
        "feed_o2_fraction": num("O2 mole fraction in the feed"),
        "notes": S})},
    "size_dependence": {"type": "array", "items": obj({
        "series_label": S, "support": S_N,
        "au_loading": num("Au loading of the catalyst series"),
        "tof_size_exponent": num("n in TOF proportional to d^(-n), as a positive number"),
        "tof_size_exponent_uncertainty": num("the +/- uncertainty printed with n"),
        "temperature": num("temperature at which the size dependence was measured"),
        "expression_as_printed": S, "notes": S})},
    "extraction_notes": S})

SYSTEM_PROMPT = """You extract catalyst characterization and CO-oxidation kinetics from one paper on supported gold.
Return one JSON object that follows the schema.

samples: one entry per catalyst sample for which the paper reports an Au particle size, Au loading, dispersion or a
CO oxidation rate. Fill every field the paper states for that sample; use null where it does not. For the activity
test (catalyst mass, flow, temperature, pressure, feed), use the conditions under which the reported rate of that
sample was measured; a condition stated once for the whole test applies to every sample it covers.
size_dependence: one entry per catalyst series for which the paper reports a particle-size dependence of the TOF of
the form TOF ~ d^(-n) (or an equivalent slope of log TOF versus log d). Give n as a positive number with its printed
uncertainty and the Au loading of the series.

Every number is an object {value, unit, qualifier, location, page}:
- value: the number exactly as printed (a percentage stays a percentage, with unit "%"); null if not given;
- qualifier: one of = < > <= >= ~; a value read off a plot uses ~;
- location: the table, figure, equation or section the value is taken from; page: the 1-based PDF page.
Do not convert units and do not compute values the paper does not print, except a mole fraction stated as a
percentage of a gas mixture, which you may give as printed with unit "%".
Ignore values the paper quotes from other publications. Record anything ambiguous in notes."""


def slug(doi: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", doi.lower()).strip("_")


# ------------------------------------------------------------------ 1. text --------------------------------------
def pdf_for(doi: str) -> Path | None:
    man = PDF_DIR / "manifest.csv"
    if man.exists():
        for r in csv.DictReader(man.open(encoding="utf-8-sig")):
            if r.get("doi", "").lower() == doi and r.get("file"):
                p = Path(r["file"])
                p = p if p.is_absolute() else PDF_DIR / p
                if p.exists():
                    return p
    hits = [p for p in PDF_DIR.glob("*.pdf") if slug(doi) in slug(p.stem)]
    return hits[0] if hits else None


def to_text(doi: str) -> Path:
    from pdf_to_text import convert, render_txt
    TEXT_DIR.mkdir(exist_ok=True)
    (TEXT_DIR / "img").mkdir(exist_ok=True)
    txt = TEXT_DIR / f"{slug(doi)}.txt"
    if not txt.exists():
        pdf = pdf_for(doi)
        if pdf is None:
            raise SystemExit(f"no PDF for {doi} in {PDF_DIR}")
        pages = convert(pdf, TEXT_DIR / "img" / slug(doi))
        txt.write_text(render_txt(pages), encoding="utf-8")
    return txt


# ------------------------------------------------------------------ 2. extraction --------------------------------
def extract(router, doi: str, model: str, effort: str) -> dict:
    text = to_text(doi).read_text(encoding="utf-8")
    content = [{"type": "input_text", "text": f"DOI: {doi}\n\nFULL TEXT WITH PAGE MARKERS:\n\n{text}"}]
    imgs = sorted((TEXT_DIR / "img").glob(f"{slug(doi)}_p*.jpg"), key=lambda p: int(p.stem.rsplit("_p", 1)[1]))
    for p in imgs:
        content.append({"type": "input_text", "text": f"Page image {p.stem.rsplit('_p', 1)[1]}:"})
        content.append({"type": "input_image", "detail": "high",
                        "image_url": "data:image/jpeg;base64," + base64.b64encode(p.read_bytes()).decode("ascii")})
    content.append({"type": "input_text", "text": "Extract now, following the system rules."})

    def call(client):
        stream = client.responses.create(
            model=model, instructions=SYSTEM_PROMPT, input=[{"role": "user", "content": content}],
            text={"format": {"type": "json_schema", "name": "au_co_oxidation_inputs", "strict": True, "schema": SCHEMA}},
            reasoning={"effort": effort}, store=False, stream=True)
        pieces, final = [], None
        for ev in stream:
            if ev.type == "response.output_text.delta":
                pieces.append(ev.delta)
            elif ev.type in ("response.completed", "response.incomplete"):
                final = ev.response
        return "".join(pieces), final, client._route

    t0 = time.time()
    text_out, final, route = router.call(call)
    data = json.loads(text_out)
    u = final.usage
    usage = {"timestamp": datetime.now().isoformat(timespec="seconds"), "doi": doi, "model": final.model,
             "reasoning_effort": effort, "images": len(imgs), "prompt_tokens": u.input_tokens,
             "completion_tokens": u.output_tokens, "total_tokens": u.total_tokens, "finish_reason": final.status,
             "seconds": round(time.time() - t0, 1)}
    data["_meta"] = usage | {"route": f"{route} responses"}
    OUT_DIR.mkdir(exist_ok=True)
    new = not USAGE_CSV.exists()
    with USAGE_CSV.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(usage))
        if new:
            w.writeheader()
        w.writerow(usage)
    return data


# ------------------------------------------------------------------ 3. normalize ---------------------------------
def frac(x: dict) -> float:
    """A loading, dispersion or mole fraction printed as % or as a fraction."""
    v, unit = float(x["value"]), (x["unit"] or "").lower()
    return v / 100.0 if ("%" in unit or "percent" in unit or v > 1.0) else v


def nm(x: dict) -> float:
    unit = (x["unit"] or "nm").lower().replace("å", "a")
    return float(x["value"]) * {"nm": 1.0, "a": 0.1, "angstrom": 0.1}.get(unit, 1.0)


def kelvin(x: dict) -> float:
    unit = (x["unit"] or "").lower().replace("°", "").replace(" ", "")
    return float(x["value"]) + (273.15 if unit in ("c", "degc", "celsius") else 0.0)


def mg(x: dict) -> float:
    unit = (x["unit"] or "").lower()
    return float(x["value"]) * {"mg": 1.0, "g": 1000.0}[unit]


def nml_min(x: dict) -> float:
    unit = (x["unit"] or "").lower().replace(" ", "").replace("−", "-")
    v = float(x["value"])
    if re.fullmatch(r"n?(ml|cm3|cm\^3|ml/min|nml/min|ml\.?min-1|mlmin-1|nmlmin-1|ml\(stp\)/min)(/min|min-1)?", unit) \
            or unit in ("mlmin^-1", "nmlmin^-1", "ml/min", "nml/min"):
        return v
    if unit in ("l/min", "nl/min", "lmin-1"):
        return v * 1000.0
    raise ValueError(f"flow unit not understood: {x['unit']}")


def umol_gcat_s(x: dict) -> float:
    unit = (x["unit"] or "").lower().replace(" ", "").replace("−", "-").replace("μ", "u").replace("µ", "u")
    v = float(x["value"])
    # amount of CO, per mass of catalyst, per time: "umol CO/(gcat s)", "umol g-1 s-1", "mmol/g/h", ...
    m = re.fullmatch(r"(umol|mmol|mol)(co)?[/(]*(k?g)(cat|catalyst|_cat)?[)]*(-1)?[/.·*(]*(s|sec|min|h|hr)(-1)?[)]*", unit)
    if m is None:
        raise ValueError(f"rate unit not understood: {x['unit']}")
    amt, mass, per = m.group(1), m.group(3), m.group(6)
    return (v * {"umol": 1.0, "mmol": 1e3, "mol": 1e6}[amt] / {"g": 1.0, "kg": 1e3}[mass]
            / {"s": 1.0, "sec": 1.0, "min": 60.0, "h": 3600.0, "hr": 3600.0}[per])


def normalize(raw: dict[str, dict]) -> tuple[dict, dict]:
    """Protocol selection rules (fixed before extraction, identical to the hand-built control):
    anchor = the Au/TiO2 sample of the absolute-rate paper with a reported CO oxidation rate;
    size relation = the series of the size-dependence paper whose Au loading is closest to the anchor loading."""
    anchors = [s for s in raw[ANCHOR_DOI]["samples"]
               if "tio" in (s["support"] or s["sample_label"]).lower() and s["co_oxidation_rate"]["value"] is not None]
    if len(anchors) != 1:
        raise SystemExit(f"anchor rule matched {len(anchors)} samples: {[s['sample_label'] for s in anchors]}")
    a = anchors[0]
    ref = {"average_diameter_nm": nm(a["average_au_diameter"]),
           "au_loading_mass_fraction": frac(a["au_loading"]),
           "dispersion_fraction": frac(a["au_dispersion"]),
           "stabilized_activity_umol_CO_gcat_s": umol_gcat_s(a["co_oxidation_rate"]),
           "catalyst_mass_mg": mg(a["catalyst_mass"]),
           "reaction_flow_Nml_min": nml_min(a["total_flow"]),
           "feed_CO_mole_fraction": frac(a["feed_co_fraction"]),
           "reaction_temperature_K": kelvin(a["temperature"])}
    series = [s for s in raw[SIZE_DOI]["size_dependence"]
              if s["tof_size_exponent"]["value"] is not None and s["au_loading"]["value"] is not None]
    pick = min(series, key=lambda s: abs(frac(s["au_loading"]) - ref["au_loading_mass_fraction"]))
    size = {"tof_exponent": abs(float(pick["tof_size_exponent"]["value"])),
            "tof_exponent_sigma": (None if pick["tof_size_exponent_uncertainty"]["value"] is None
                                   else float(pick["tof_size_exponent_uncertainty"]["value"]))}
    provenance = {"anchor_sample": a["sample_label"],
                  "anchor_locations": {k: (a[f]["location"], a[f]["page"]) for k, f in
                                       zip(ref, ("average_au_diameter", "au_loading", "au_dispersion", "co_oxidation_rate",
                                                 "catalyst_mass", "total_flow", "feed_co_fraction", "temperature"))},
                  "size_series": pick["series_label"], "size_series_loading": frac(pick["au_loading"]),
                  "size_location": (pick["tof_size_exponent"]["location"], pick["tof_size_exponent"]["page"]),
                  "all_size_series": [(s["series_label"], frac(s["au_loading"]), s["tof_size_exponent"]["value"])
                                      for s in series]}
    return {"reference": ref, "size_activity": size}, provenance


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="skip extraction; normalize and self-check only")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--model", default="gpt-5.5")
    ap.add_argument("--effort", default="medium")
    args = ap.parse_args()
    OUT_DIR.mkdir(exist_ok=True)
    raw, router = {}, None
    for doi in DOIS:
        path = OUT_DIR / f"{slug(doi)}.json"
        if not args.check and (args.force or not path.exists()):
            print(f"extract {doi}", flush=True)
            if router is None:
                from llm_route import Router
                router = Router(args.model)
            data = extract(router, doi, args.model, args.effort)
            path.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
            print(f"  {len(data['samples'])} samples, {len(data['size_dependence'])} size series, "
                  f"{data['_meta']['total_tokens']:,} tokens, {data['_meta']['seconds']} s", flush=True)
        raw[doi] = json.loads(path.read_text(encoding="utf-8"))
    inputs, prov = normalize(raw)
    hand = au_chain.handbuilt_inputs()
    compare = [{"field": f"{grp}.{k}", "extracted": inputs[grp][k], "hand_built": hand[grp][k],
                "equal": inputs[grp][k] is not None and abs(inputs[grp][k] - hand[grp][k]) <= 1e-12 * max(1.0, abs(hand[grp][k]))}
               for grp in ("reference", "size_activity") for k in hand[grp]]
    (OUT_DIR / "inputs_extracted.json").write_text(json.dumps({"inputs": inputs, "provenance": prov}, indent=1,
                                                              ensure_ascii=False), encoding="utf-8")
    with (OUT_DIR / "inputs_vs_handbuilt.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(compare[0]))
        w.writeheader()
        w.writerows(compare)
    # A differing input is a source discrepancy only if the paper prints both values; record the pages.
    pages = {doi: re.split(r"=== PAGE (\d+) ===", to_text(doi).read_text(encoding="utf-8")) for doi in DOIS}

    def printed_on(doi, value):
        forms = {f"{value:.2f}", f"{value * 100:.2f}"} if value < 1 else {f"{value:.2f}", f"{value:g}"}
        chunks = pages[doi]
        return sorted({int(chunks[i]) for i in range(1, len(chunks), 2)
                       for f in forms if re.search(rf"(?<![\d.]){re.escape(f)}(?![\d])", chunks[i + 1])})

    discrepancies = []
    for c in compare:
        if c["equal"]:
            continue
        grp, key = c["field"].split(".")
        doi = ANCHOR_DOI if grp == "reference" else SIZE_DOI
        discrepancies.append({"field": c["field"], "doi": doi, "extracted": c["extracted"], "hand_built": c["hand_built"],
                              "pages_extracted_value": printed_on(doi, c["extracted"]),
                              "pages_hand_built_value": printed_on(doi, c["hand_built"])})
    (OUT_DIR / "source_discrepancies.json").write_text(json.dumps(discrepancies, indent=1), encoding="utf-8")
    for d in discrepancies:
        print(f"  source discrepancy {d['field']}: {d['extracted']} printed on p. {d['pages_extracted_value']}, "
              f"{d['hand_built']} on p. {d['pages_hand_built_value']}")
    # The chain consumes the size exponent and the anchor; the sigma is reported but not used by the chain.
    chain_inputs = {"reference": inputs["reference"], "size_activity": {"tof_exponent": inputs["size_activity"]["tof_exponent"]}}
    res = au_chain.self_check(chain_inputs, "extracted (agent)")
    res["inputs_vs_handbuilt"] = compare
    (OUT_DIR / "selfcheck_au_extracted.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    for c in compare:
        print(f"  {'OK ' if c['equal'] else 'DIFF'} {c['field']}: extracted {c['extracted']} / hand-built {c['hand_built']}")
    print(json.dumps(res["checks"], indent=1), "\nraw self-check:", "PASS" if res["pass"] else "FAIL",
          "(agent/selfcheck_gate.py applies the source-discrepancy rule and is authoritative)")


if __name__ == "__main__":
    main()
