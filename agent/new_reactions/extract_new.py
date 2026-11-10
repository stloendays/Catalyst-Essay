"""LLM extraction for the new reactions, on top of the Docling OCR (ocr/<rxn>/<stem>.md + figure crops).

Same rules as agent/extraction/extract_records.py (printed numbers copied as printed, plot readings '~', no derived
quantities), one call per paper, strict JSON schema, routed API-YES -> advisor key (llm_route.py).
Usage: python extract_new.py pdh|ch4 [--force] [--model gpt-5.5]
"""
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
sys.path.insert(0, str(HERE.parent / "extraction"))
from llm_route import Router  # noqa: E402

NUM = {"type": "object", "additionalProperties": False, "required": ["value", "unit", "qualifier"],
       "properties": {"value": {"type": ["number", "null"]}, "unit": {"type": ["string", "null"]},
                      "qualifier": {"type": "string", "enum": ["=", "~", "<", ">", "missing"]}}}
COMMON = {
    "entry_label": {"type": "string"},
    "catalyst_name": {"type": "string"},
    "components": {"type": "array", "items": {
        "type": "object", "additionalProperties": False,
        "required": ["component", "role", "loading_wt_pct"],
        "properties": {
            "component": {"type": "string"},
            "role": {"type": "string", "enum": ["active_metal", "active_oxide", "promoter", "support"]},
            "loading_wt_pct": {"type": ["number", "null"],
                               "description": "Only when the paper states wt% (also inside a name like '1%Pt'); else null."}}}},
    "temperature": NUM, "pressure": NUM, "feed_composition": {"type": ["string", "null"]},
    "space_velocity": NUM,
    "space_velocity_basis": {"type": "string", "enum": ["per_mass_catalyst", "per_volume_catalyst", "per_mass_metal", "unknown"]},
    "catalyst_mass": NUM, "total_flow": NUM, "time_on_stream": NUM,
}
RATE_BASIS = {"type": "string", "enum": ["per_g_catalyst", "per_g_metal", "per_site", "per_volume", "unknown"]}
RXN = {
    "pdh": dict(
        title="non-oxidative propane dehydrogenation (C3H8 -> C3H6 + H2)",
        extra={"h2_c3h8_ratio": NUM, "c3h8_fraction_pct": NUM,
               "propane_conversion": NUM, "propylene_selectivity": NUM, "propylene_yield": NUM,
               "propylene_rate": NUM, "propylene_rate_basis": RATE_BASIS, "deactivation_constant": NUM,
               "stability_initial_conversion": NUM, "stability_final_conversion": NUM, "stability_duration": NUM,
               "regeneration_cycles": {"type": ["integer", "null"]}},
        scope=("Out of scope: oxidative dehydrogenation (O2, CO2, N2O co-feeds), butane or ethane runs, chemical "
               "looping, equilibrium values, DFT, literature-comparison tables."),
        perf=("conversion", "selectivity", "yield", "propylene", "c3h6", "deactivation", "stability", "time on stream",
              "rate", "catalytic performance", "pdh")),
    "ch4": dict(
        title="thermocatalytic CO2 methanation (CO2 + 4 H2 -> CH4 + 2 H2O)",
        extra={"h2_co2_ratio": NUM, "co2_conversion": NUM, "ch4_selectivity": NUM, "co_selectivity": NUM,
               "ch4_yield": NUM, "ch4_rate": NUM, "ch4_rate_basis": RATE_BASIS,
               "stability_initial_conversion": NUM, "stability_final_conversion": NUM, "stability_duration": NUM},
        scope=("Out of scope: photocatalytic, electrochemical, plasma or photothermal runs, CO methanation without CO2, "
               "dry reforming, equilibrium values, DFT, literature-comparison tables."),
        perf=("conversion", "selectivity", "ch4", "methane", "methanation", "yield", "rate", "stability",
              "time on stream", "activity", "catalytic performance")),
}


def schema(rxn):
    props = dict(COMMON, **RXN[rxn]["extra"],
                 data_source_type={"type": "string", "enum": ["table", "text", "figure"]},
                 location={"type": "string"}, page={"type": ["integer", "null"]})
    rec = {"type": "object", "additionalProperties": False, "required": list(props), "properties": props}
    top = {"doi": {"type": "string"}, "title": {"type": "string"}, "records": {"type": "array", "items": rec},
           "extraction_notes": {"type": "string"}}
    return {"type": "object", "additionalProperties": False, "required": list(top), "properties": top}


SYSTEM = """You extract experimental catalyst-performance data for {title} from one research paper, for use in a plant cost model.
The paper is given as a Docling layout parse: reading-order text with '=== PAGE n ===' markers, tables as Markdown under '[TABLE k] caption', and '[PICTURE k, page n] caption' placeholders. Images of the performance figures follow, each labelled with its picture number and caption.

Output one record per catalyst x reaction-condition entry that THIS paper measured (each catalyst at each temperature / pressure / feed / space velocity / time-on-stream point at which performance is reported). {scope}

Rules
- Copy every number exactly as printed, in the paper's own unit; do not convert units, round or average. Apply a power-of-ten multiplier from a column header or axis label to the value, and name the header in location.
- Missing values: value null, qualifier 'missing'. Never compute a quantity the paper does not report, except: a molar feed ratio from a stated feed composition, and a condition stated once for a whole table/figure/series or in the Experimental section applies to every entry it governs (say where in location).
- A printed number has qualifier '='; '<1' -> 1 with '<'. Values read from a plot have qualifier '~', data_source_type 'figure'; read only points tied unambiguously to one catalyst (legend) and one condition against a labelled axis. A number printed in a table or text wins over a plot reading; then do not repeat it from the plot.
- Stability / time-on-stream: give one record per catalyst and run with stability_initial_conversion, stability_final_conversion (first and last plotted or stated points) and stability_duration; also fill the main conversion/selectivity fields with the initial values. Deactivation constants (kd) as printed.
- Rates (formation rate, STY, productivity, TOF) exactly as printed with unit, and the basis they are normalised to.
- components: active metals/oxides, promoters, support, with wt% loading only when stated in wt%.
- The Docling table cells are machine-parsed; check them against the figure images when the same data are plotted, and against the text.
Be complete: every table row and every readable data point is a record. Be exact: a wrong number is worse than a null."""


def build(rxn, md_path, max_imgs=12):
    md = md_path.read_text(encoding="utf-8")
    figs = json.loads((md_path.parent / (md_path.stem + "_figs.json")).read_text(encoding="utf-8"))
    perf = RXN[rxn]["perf"]
    charac = ("xrd", "xps", "tem ", "tem image", "haadf", "stem", "exafs", "xanes", "raman", "ftir", "drift", "ir spectra",
              "nmr", "tpr", "tpd", "isotherm", "dft", "calculated", "schematic", "illustration", "structure model")
    def keep(c):
        c = (c or "").lower()
        if any(w in c for w in perf):
            return 2
        return 0 if any(w in c for w in charac) else 1
    chosen = sorted([f for f in figs if keep(f["caption"]) > 0], key=lambda f: -keep(f["caption"]))[:max_imgs]
    chosen = sorted(chosen, key=lambda f: f["file"])
    content = [{"type": "input_text", "text": md}]
    n = 0
    for f in chosen:
        p = md_path.parent / (md_path.stem + "_figs") / f["file"]
        if not p.exists():
            continue
        k = f["file"].split("_")[0].replace("fig", "")
        content.append({"type": "input_text", "text": f"[Image of PICTURE {k}, page {f['page']}] {f['caption'][:600]}"})
        content.append({"type": "input_image", "detail": "high",
                        "image_url": "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode()})
        n += 1
    return content, n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("rxn")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--only", default="")
    ap.add_argument("--shard", default="0/1")
    ap.add_argument("--model", default="gpt-5.5")
    ap.add_argument("--effort", default="medium")
    a = ap.parse_args()
    out = HERE / "raw" / a.rxn
    out.mkdir(parents=True, exist_ok=True)
    usage_csv = HERE / "token_usage.csv"
    sch = schema(a.rxn)
    system = SYSTEM.format(title=RXN[a.rxn]["title"], scope=RXN[a.rxn]["scope"])
    router = Router(a.model)
    k, n = map(int, a.shard.split("/"))
    for j, md in enumerate(sorted((HERE / "ocr" / a.rxn).glob("*.md"))):
        if j % n != k:
            continue
        dst = out / (md.stem + ".json")
        if a.only and a.only not in md.stem:
            continue
        if dst.exists() and not a.force:
            continue
        content, n_img = build(a.rxn, md)
        t0 = time.time()

        def call(client):
            stream = client.responses.create(
                model=a.model, instructions=system, input=[{"role": "user", "content": content}],
                text={"format": {"type": "json_schema", "name": f"{a.rxn}_records", "strict": True, "schema": sch}},
                reasoning={"effort": a.effort}, store=False, stream=True)
            pieces, final = [], None
            for ev in stream:
                if ev.type == "response.output_text.delta":
                    pieces.append(ev.delta)
                elif ev.type in ("response.completed", "response.incomplete"):
                    final = ev.response
            return "".join(pieces), final, client._route

        for attempt in range(3):
            try:
                text, final, route = router.call(call)
                if final is not None:
                    break
            except Exception as err:  # noqa: BLE001 - stream cut; retried
                print("  retry", md.stem, type(err).__name__, str(err)[:120], flush=True)
                final = None
        if final is None:
            print("  FAILED", md.stem, flush=True)
            continue
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            data = {"records": [], "extraction_notes": "UNPARSEABLE"}
        u = final.usage
        row = dict(timestamp=datetime.now().isoformat(timespec="seconds"), rxn=a.rxn, paper=md.stem,
                   model=final.model, route=route, images=n_img, prompt_tokens=u.input_tokens,
                   completion_tokens=u.output_tokens, total_tokens=u.total_tokens, status=final.status,
                   n_records=len(data.get("records", [])), seconds=round(time.time() - t0, 1))
        data["_meta"] = row
        dst.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
        new = not usage_csv.exists()
        with usage_csv.open("a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, list(row))
            if new:
                w.writeheader()
            w.writerow(row)
        print(row, flush=True)


if __name__ == "__main__":
    main()
