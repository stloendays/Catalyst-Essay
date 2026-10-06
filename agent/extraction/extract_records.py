"""LLM extraction of CO2-to-methanol catalyst performance entries into schema.json.

Usage:
    python extract_records.py                    # every ok paper of paper_set.txt in fetch_manifest.json
    python extract_records.py --doi 10.1021/cs500979c --force
    python extract_records.py --pass figures --api-yes   # figure-digitisation pass -> out/raw_figures/
    python extract_records.py --pass si --api-yes        # Supporting Information pass -> out/raw_si/

Passes (same schema, same model):
  main     full text + all page images (the original extraction)            -> out/raw/
  figures  full text + high-resolution images of the pages that carry a
           figure caption; the model digitises every catalyst-performance
           data point of the main-text figures (qualifier '~')             -> out/raw_figures/
  si       Supporting Information text (text_si/) + images of SI pages that
           mention performance quantities; location is prefixed 'SI'       -> out/raw_si/
  si_figures  SI text + high-resolution images of the SI pages whose figure
           captions describe catalytic performance; the figure prompt is
           applied to the SI figures (location 'SI Figure S4a')             -> out/raw_si_figures/
The figure and SI passes are told the catalyst names the main pass used, so
the same catalyst keeps the same name; normalize.py merges the passes
(printed main text > SI > plot readings).

Input per paper: text/<slug>.txt (pypdfium2 text + pdfplumber tables, page
markers) and the rendered page images text/img/<slug>_p<n>.jpg. One API call
per paper, strict JSON-schema output, raw result in out/raw/<slug>.json.
Every call is logged to out/token_usage.csv. Hard caps: --max-papers
(default 30) and --token-cap (default 6,000,000 total tokens, counted from the
log, so the cap holds across reruns); --pass-cap limits the tokens of one pass
(default 1,500,000). Nothing from the evaluation datasets is
read here; the prompt contains only the paper itself.

The API key is resolved by the harness resolver, or with --api-yes taken from
the local API-YES gateway (127.0.0.1:8788) proxy key that serves the requested
model; once API-YES is used up or unavailable the calls move to the advisor key
(llm_route.py). Keys are handed straight to the client and never printed,
logged or stored.
"""
from __future__ import annotations

import argparse
import base64
import csv
import json
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEXT_DIR = HERE / "text"
OUT_DIR = HERE / "out"
RAW_DIR = OUT_DIR / "raw"
RAW_DIRS = {"main": OUT_DIR / "raw", "figures": OUT_DIR / "raw_figures", "si": OUT_DIR / "raw_si",
            "si_figures": OUT_DIR / "raw_si_figures"}
TEXT_SI_DIR = HERE / "text_si"
USAGE_CSV = OUT_DIR / "token_usage.csv"
SCHEMA = json.loads((HERE / "schema.json").read_text(encoding="utf-8"))
HARNESS_AGENT = r"D:\论文-AI4S\Catalyst_Economic_Leverage_Automation_Harness_v0.1\agent"

USAGE_FIELDS = ["timestamp", "doi", "model", "reasoning_effort", "images", "prompt_tokens", "cached_tokens",
                "completion_tokens", "reasoning_tokens", "total_tokens", "cumulative_total_tokens",
                "finish_reason", "n_records", "seconds", "pass"]

SYSTEM_PROMPT = """You extract experimental catalyst-performance data for CO2 hydrogenation to methanol from one research paper, for use in a methanol-plant model.

Output one record per catalyst x reaction-condition entry that THIS paper measured (each distinct catalyst at each distinct temperature / pressure / H2:CO2 / GHSV / time-on-stream point at which performance is reported). Do NOT output: results quoted from other papers (literature-comparison tables), equilibrium values, blank/support-only runs with no products, DFT or kinetic-model predictions, or CO-hydrogenation runs (CO-rich feeds without CO2 are out of scope; CO2 + CO co-feeds are allowed and must be described in feed_composition).

Rules for numbers
- Copy every number exactly as printed, in the paper's own unit; do not convert units, round, or average. Unit conversion is done later. The one transformation you must apply: a power-of-ten multiplier in a column header or axis label (e.g. 'Rate (10^-7 mol s-1 g-1)' with cell 3.34 -> value 3.34e-7, unit 'mol s-1 g-1'); mention the header in `location`.
- Missing values are null. Never estimate, interpolate, or compute a quantity the paper does not report, with two exceptions that must be stated in `location`: (a) H2/CO2 molar ratio from a stated feed composition (H2/CO2/N2 = 72/24/4 -> 3; CO2:H2 = 1:4 -> 4); (b) a condition stated once for a whole table/figure/series (caption, footnote, or Experimental section) applies to every entry it governs - fill it and point `location` to where it is stated.
- '<1' -> value 1 with qualifier '<'. A printed number has qualifier '='.
- Values from plots: only when a data point can be tied unambiguously to one catalyst and one condition and read against a labelled axis; use qualifier '~', data_source_type 'figure'. If the plot is too dense or unlabelled, skip it and say so in extraction_notes. A number printed in a table or text always wins over a plot reading.
- Selectivities: report CH3OH, CO and CH4 selectivity separately when given. If the paper says CO is the only by-product and gives only S(CH3OH), leave S(CO) null and mention it in notes. selectivity_basis = 'carbon_molar' only if the paper defines selectivity on a carbon/molar basis of converted CO2 (or the definition makes it so); otherwise 'unspecified'.
- methanol_sty: methanol space-time yield or formation rate exactly as reported (g/kg/mol/mmol/umol per g catalyst, per g metal, per mL, per h/s). sty_basis records what it is normalised to. Do not derive STY from conversion.
- GHSV/WHSV: value and unit as printed; ghsv_basis = per_mass_catalyst for mL g-1 h-1 (or L g-1 h-1, WHSV), per_volume_catalyst for h-1 with a catalyst volume basis.
- catalyst_mass: mass loaded in the reactor, when stated. total_flow: total feed flow rate as printed (e.g. 80 mL min-1, 30 NmL min-1), so GHSV can be computed later when the paper gives only flow and mass.
- components: list active metals/oxides, promoters and supports with their reported content (wt%, mol%, at%, ratio) when given; loading.value null when not given. Do not convert mol% to wt%.
- Temperature: as printed (K or °C). Pressure: as printed (MPa, bar, atm).
- page: the 1-based number in the nearest preceding '=== PAGE n ===' marker. Images are labelled with the same page numbers.

Sources inside the input
- Running text is in reading order. Lines after '--- pdfplumber table pN.k ---' are machine-parsed table cells: subscripts are lost (CO2 may appear as 'CO'), cells may be merged or split. Always check table values against the page image before using them.
- Tables printed as plain text without a pdfplumber block must be read from the text and the image.

Be complete: every table row and every readable data point is a record. Be exact: a wrong number is worse than a null."""


FIGURE_PROMPT = """You digitise catalyst-performance data from the FIGURES of one research paper on CO2 hydrogenation to methanol, for a methanol-plant model. A separate pass already took the numbers printed in tables and text; your job is the plotted data.

Output one record per plotted data point that THIS paper measured: each catalyst (legend entry) at each x-axis position (temperature, pressure, GHSV, H2:CO2, composition or loading) of every main-text figure that shows CO2 conversion, CH3OH/CO/CH4 selectivity, or methanol STY / formation rate. Combine the quantities that belong to the same catalyst and condition (for example conversion from panel a and selectivity from panel b) into one record.

Reading rules
- Every plotted value has qualifier '~', data_source_type 'figure', and location naming the figure and panel ('Figure 5a'). Read the value at the centre of the marker or the top of the bar against the axis that series uses (left or right axis; check the arrows or colours). Respect broken axes and the scale of each axis segment. Apply power-of-ten multipliers from the axis label.
- Map series to catalysts only through the legend, colours and markers. Never invent a series: if the legend lists five catalysts there are at most five series. If a series cannot be tied to one catalyst without doubt, skip it and say so in extraction_notes.
- Conditions not on the axis come from the caption or the Experimental section (state where in location). Report every condition exactly as printed in its own unit.
- Time-on-stream (stability) plots: report only the first and the last plotted point of each series.
- Skip: literature-comparison plots, simulated, modelled or equilibrium curves, DFT, characterisation (XRD, XPS, TPD, IR...), Arrhenius plots, and anything that is not a measured catalytic performance of this work.
- If a number is also printed in a table or the text, still report the plotted point (the merge keeps the printed value).
- Use the catalyst names listed under 'Catalyst names used for this paper' when the same catalyst appears; otherwise the paper's own label.
- page: the 1-based number in the '=== PAGE n ===' marker; images are labelled with the same numbers.

Be complete over all main-text performance figures; a wrong series assignment is worse than a skipped point."""

SI_PROMPT_HEAD = """The input is the SUPPORTING INFORMATION of the paper (not the main article). Extract the catalyst-performance entries reported in it, following all rules below. Prefix every location with 'SI' (for example 'SI Table S1', 'SI Figure S4b'); page numbers refer to the '=== PAGE n ===' markers of the SI text and images. Characterisation data, literature-comparison tables and DFT results are out of scope. Use the catalyst names listed under 'Catalyst names used for this paper' when the same catalyst appears.

"""

PERF_WORDS = ("conversion", "selectivity", "sty", "space time", "space-time", "yield", "formation rate", "productivity",
              "activity", "tof", "catalytic performance")


def main_pass_names(doi: str) -> list[str]:
    raw = RAW_DIRS["main"] / f"{slug(doi)}.json"
    if not raw.exists():
        return []
    recs = json.loads(raw.read_text(encoding="utf-8")).get("records", [])
    return sorted({r["catalyst_name"] for r in recs})


def figure_pages(doi: str) -> list[int]:
    """Pages of the main text whose text holds a figure caption ('Fig. 3', 'Figure 3.')."""
    import re
    js = json.loads((TEXT_DIR / f"{slug(doi)}.json").read_text(encoding="utf-8"))
    cap = re.compile(r"(^|\n)\s*(Fig\.|Figure|FIGURE|Fig)\s*\d+[a-z]?[\.:|\s]", re.M)
    return [p["page"] for p in js["pages"] if cap.search(p["text"] or "")]


def hi_res_image(doi: str, page: int) -> Path:
    """Render one main-text page at 2.2x for the figure pass (cached in text/img_hi/)."""
    import pypdfium2 as pdfium
    out = TEXT_DIR / "img_hi" / f"{slug(doi)}_p{page}.jpg"
    if not out.exists():
        out.parent.mkdir(exist_ok=True)
        man = {r["doi"]: r["file"] for r in json.loads((HERE / "fetch_manifest.json").read_text(encoding="utf-8"))
               if r.get("file")}
        doc = pdfium.PdfDocument(str(HERE / "pdf" / man[doi]))
        doc[page - 1].render(scale=2.2).to_pil().convert("RGB").save(out, quality=88)
    return out


SI_FIG_HEAD = """The input is the SUPPORTING INFORMATION of the paper. Apply the figure rules below to the SI figures: digitise every catalytic-performance data point of the SI figures shown (prefix every location with 'SI', e.g. 'SI Figure S4a'). Values printed in SI tables were taken by another pass; report only plotted points.

"""


def si_figure_pages(doi: str) -> list[int]:
    """SI pages that carry a figure caption about catalytic performance."""
    import re
    js_path = TEXT_SI_DIR / f"{slug(doi)}.json"
    if not js_path.exists():
        return []
    cap = re.compile(r"(Fig(ure)?\.?\s*S\s?\d+)", re.I)
    perf = re.compile(r"(conversion|selectivity|space[ -]time|STY|yield|formation rate|productivity|catalytic performance|catalytic activity|effect of (?:the )?(?:pressure|temperature|GHSV|space velocity|H2/CO2))", re.I)
    out = []
    for p in json.loads(js_path.read_text(encoding="utf-8"))["pages"]:
        t = p["text"] or ""
        for m in cap.finditer(t):
            if perf.search(t[m.start():m.start() + 400]):
                out.append(p["page"])
                break
    return out


def si_hi_res_image(doi: str, page: int) -> Path:
    import pypdfium2 as pdfium
    out = TEXT_SI_DIR / "img_hi" / f"{slug(doi)}_p{page}.jpg"
    if not out.exists():
        out.parent.mkdir(exist_ok=True)
        js = json.loads((TEXT_SI_DIR / f"{slug(doi)}.json").read_text(encoding="utf-8"))
        pg = next(p for p in js["pages"] if p["page"] == page)
        doc = pdfium.PdfDocument(str(HERE / "si" / pg["file"]))
        doc[pg["file_page"] - 1].render(scale=2.2).to_pil().convert("RGB").save(out, quality=88)
    return out


def si_pages(doi: str) -> list[int]:
    js_path = TEXT_SI_DIR / f"{slug(doi)}.json"
    if not js_path.exists():
        return []
    js = json.loads(js_path.read_text(encoding="utf-8"))
    out = []
    for p in js["pages"]:
        t = (p["text"] or "").lower()
        if any(w in t for w in PERF_WORDS) or len(t.strip()) < 200:   # figure-only pages carry little text
            out.append(p["page"])
    return out


def build_messages_pass(doi: str, pass_: str) -> tuple[list, int, int]:
    s = slug(doi)
    names = main_pass_names(doi)
    name_line = "Catalyst names used for this paper: " + ("; ".join(names) if names else "(none yet)")
    if pass_ == "figures":
        text = (TEXT_DIR / f"{s}.txt").read_text(encoding="utf-8")
        pages = figure_pages(doi)
        content = [{"type": "text", "text": f"DOI: {doi}\n{name_line}\n\nFULL TEXT WITH PAGE MARKERS (for captions and conditions):\n\n{text}"}]
        for n in pages:
            b64 = base64.b64encode(hi_res_image(doi, n).read_bytes()).decode("ascii")
            content.append({"type": "text", "text": f"Page image {n}:"})
            content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}", "detail": "high"}})
        content.append({"type": "text", "text": "Digitise all main-text performance figures now, following the system rules."})
        system = FIGURE_PROMPT
        est = len(text) // 3 + len(pages) * 1600
    elif pass_ == "si_figures":
        text = (TEXT_SI_DIR / f"{s}.txt").read_text(encoding="utf-8")
        pages = si_figure_pages(doi)
        content = [{"type": "text", "text": f"DOI: {doi}\n{name_line}\n\nSUPPORTING INFORMATION TEXT WITH PAGE MARKERS (for captions and conditions):\n\n{text}"}]
        for n in pages:
            b64 = base64.b64encode(si_hi_res_image(doi, n).read_bytes()).decode("ascii")
            content.append({"type": "text", "text": f"SI page image {n}:"})
            content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}", "detail": "high"}})
        content.append({"type": "text", "text": "Digitise all SI performance figures now, following the system rules."})
        system = SI_FIG_HEAD + FIGURE_PROMPT
        est = len(text) // 3 + len(pages) * 1600
    else:  # si
        text = (TEXT_SI_DIR / f"{s}.txt").read_text(encoding="utf-8")
        pages = si_pages(doi)
        content = [{"type": "text", "text": f"DOI: {doi}\n{name_line}\n\nSUPPORTING INFORMATION TEXT WITH PAGE MARKERS:\n\n{text}"}]
        for n in pages:
            img = TEXT_SI_DIR / "img" / f"{s}_p{n}.jpg"
            b64 = base64.b64encode(img.read_bytes()).decode("ascii")
            content.append({"type": "text", "text": f"SI page image {n}:"})
            content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}", "detail": "high"}})
        content.append({"type": "text", "text": "Extract all SI records now, following the system rules."})
        system = SI_PROMPT_HEAD + SYSTEM_PROMPT
        est = len(text) // 3 + len(pages) * 1100
    return [{"role": "system", "content": system}, {"role": "user", "content": content}], len(pages), est


def used_tokens_pass(pass_: str) -> int:
    if not USAGE_CSV.exists():
        return 0
    with USAGE_CSV.open(encoding="utf-8") as f:
        return sum(int(r["total_tokens"] or 0) for r in csv.DictReader(f) if (r.get("pass") or "main") == pass_)


def slug(doi: str) -> str:
    import re
    return re.sub(r"[^a-z0-9]+", "_", doi.lower()).strip("_")


def used_tokens() -> int:
    if not USAGE_CSV.exists():
        return 0
    with USAGE_CSV.open(encoding="utf-8") as f:
        return sum(int(r["total_tokens"] or 0) for r in csv.DictReader(f))


def log_usage(row: dict) -> None:
    OUT_DIR.mkdir(exist_ok=True)
    if USAGE_CSV.exists():
        with USAGE_CSV.open(encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        if rows and "pass" not in rows[0]:
            with USAGE_CSV.open("w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=USAGE_FIELDS)
                w.writeheader()
                for r in rows:
                    r["pass"] = "main"
                    w.writerow(r)
    new = not USAGE_CSV.exists()
    with USAGE_CSV.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=USAGE_FIELDS)
        if new:
            w.writeheader()
        w.writerow(row)


def build_messages(doi: str, use_images: bool) -> tuple[list, int, int]:
    s = slug(doi)
    text = (TEXT_DIR / f"{s}.txt").read_text(encoding="utf-8")
    content = [{"type": "text", "text": f"DOI: {doi}\n\nFULL TEXT WITH PAGE MARKERS:\n\n{text}"}]
    n_img = 0
    if use_images:
        imgs = sorted((TEXT_DIR / "img").glob(f"{s}_p*.jpg"), key=lambda p: int(p.stem.rsplit("_p", 1)[1]))
        for p in imgs:
            n = int(p.stem.rsplit("_p", 1)[1])
            b64 = base64.b64encode(p.read_bytes()).decode("ascii")
            content.append({"type": "text", "text": f"Page image {n}:"})
            content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}", "detail": "high"}})
            n_img += 1
    content.append({"type": "text", "text": "Extract all records now, following the system rules."})
    est = len(text) // 3 + n_img * 1100
    return [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": content}], n_img, est


def extract_one(client, doi: str, model: str, effort: str, use_images: bool, max_out: int,
                pass_: str = "main") -> dict:
    if pass_ == "main":
        messages, n_img, _ = build_messages(doi, use_images)
    else:
        messages, n_img, _ = build_messages_pass(doi, pass_)
    t0 = time.time()
    if getattr(client, "_route", None):
        return extract_one_responses(client, doi, model, effort, messages, n_img, t0)
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        response_format={"type": "json_schema", "json_schema": {"name": "meoh_catalyst_records", "strict": True, "schema": SCHEMA}},
        reasoning_effort=effort,
        max_completion_tokens=max_out,
    )
    dt = time.time() - t0
    u = resp.usage
    choice = resp.choices[0]
    try:
        data = json.loads(choice.message.content or "{}")
    except json.JSONDecodeError:
        data = {"doi": doi, "title": "", "records": [], "extraction_notes": "UNPARSEABLE OUTPUT"}
    usage = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "doi": doi, "model": resp.model, "reasoning_effort": effort, "images": n_img,
        "prompt_tokens": u.prompt_tokens,
        "cached_tokens": getattr(getattr(u, "prompt_tokens_details", None), "cached_tokens", 0) or 0,
        "completion_tokens": u.completion_tokens,
        "reasoning_tokens": getattr(getattr(u, "completion_tokens_details", None), "reasoning_tokens", 0) or 0,
        "total_tokens": u.total_tokens,
        "finish_reason": choice.finish_reason,
        "n_records": len(data.get("records", [])),
        "seconds": round(dt, 1),
    }
    data["_meta"] = {k: usage[k] for k in ("model", "reasoning_effort", "images", "prompt_tokens", "completion_tokens",
                                            "reasoning_tokens", "total_tokens", "finish_reason", "seconds", "timestamp")}
    return data, usage


def extract_one_responses(client, doi, model, effort, messages, n_img, t0):
    """Router routes (API-YES, then the advisor key): streamed Responses calls with store=false (the API-YES
    chat-completions route drops images and the JSON schema), so the output is assembled from the streamed
    text deltas."""
    system, user = messages[0]["content"], messages[1]["content"]
    content = []
    for part in user:
        if part["type"] == "text":
            content.append({"type": "input_text", "text": part["text"]})
        else:
            content.append({"type": "input_image", "image_url": part["image_url"]["url"],
                            "detail": part["image_url"].get("detail", "high")})
    stream = client.responses.create(
        model=model, instructions=system, input=[{"role": "user", "content": content}],
        text={"format": {"type": "json_schema", "name": "meoh_catalyst_records", "strict": True, "schema": SCHEMA}},
        reasoning={"effort": effort}, store=False, stream=True)
    pieces, final = [], None
    for ev in stream:
        if ev.type == "response.output_text.delta":
            pieces.append(ev.delta)
        elif ev.type in ("response.completed", "response.incomplete"):
            final = ev.response
    dt = time.time() - t0
    text = "".join(pieces)
    try:
        data = json.loads(text or "{}")
    except json.JSONDecodeError:
        data = {"doi": doi, "title": "", "records": [], "extraction_notes": "UNPARSEABLE OUTPUT"}
    u = final.usage
    usage = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "doi": doi, "model": final.model, "reasoning_effort": effort, "images": n_img,
        "prompt_tokens": u.input_tokens,
        "cached_tokens": getattr(u.input_tokens_details, "cached_tokens", 0) or 0,
        "completion_tokens": u.output_tokens,
        "reasoning_tokens": getattr(u.output_tokens_details, "reasoning_tokens", 0) or 0,
        "total_tokens": u.total_tokens,
        "finish_reason": final.status,
        "n_records": len(data.get("records", [])),
        "seconds": round(dt, 1),
    }
    data["_meta"] = {k: usage[k] for k in ("model", "reasoning_effort", "images", "prompt_tokens", "completion_tokens",
                                            "reasoning_tokens", "total_tokens", "finish_reason", "seconds", "timestamp")}
    data["_meta"]["route"] = f"{client._route} responses"
    return data, usage


from llm_route import Router  # noqa: E402  (API-YES first, then the advisor key)
from paper_set import load_paper_set  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--doi", action="append", help="limit to these DOIs (repeatable)")
    ap.add_argument("--model", default="gpt-5.5")
    ap.add_argument("--effort", default="medium", choices=["minimal", "low", "medium", "high", "xhigh"])
    ap.add_argument("--no-images", action="store_true")
    ap.add_argument("--max-papers", type=int, default=30)
    ap.add_argument("--token-cap", type=int, default=6_000_000)
    ap.add_argument("--pass", dest="pass_", default="main", choices=["main", "figures", "si", "si_figures"])
    ap.add_argument("--pass-cap", type=int, default=1_500_000, help="token limit for this pass (figures/si)")
    ap.add_argument("--max-out", type=int, default=100_000)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--api-yes", action="store_true",
                    help="route calls through the local API-YES gateway, then the advisor key once API-YES is used up")
    args = ap.parse_args()

    manifest = json.loads((HERE / "fetch_manifest.json").read_text(encoding="utf-8"))
    in_set = load_paper_set()
    dois = [r["doi"] for r in manifest if r["status"] in ("ok", "skip") and r["file"] and r["doi"].lower() in in_set]
    if args.pass_ == "si":
        dois = [d for d in dois if (TEXT_SI_DIR / f"{slug(d)}.txt").exists()]
    if args.pass_ == "si_figures":
        dois = [d for d in dois if si_figure_pages(d)]
    if args.doi:
        wanted = {d.lower() for d in args.doi}
        dois = [d for d in dois if d in wanted]
    if len(dois) > args.max_papers:
        sys.exit(f"{len(dois)} papers exceed --max-papers {args.max_papers}")

    import openai
    router = None
    if args.api_yes:
        router = Router(args.model)
    else:
        sys.path.insert(0, HARNESS_AGENT)
        from llm_client import resolve_api_key
        client = openai.OpenAI(api_key=resolve_api_key(), timeout=1800)

    raw_dir = RAW_DIRS[args.pass_]
    raw_dir.mkdir(parents=True, exist_ok=True)
    for doi in dois:
        out_path = raw_dir / f"{slug(doi)}.json"
        if out_path.exists() and not args.force:
            print(f"skip {doi} (exists)")
            continue
        if args.pass_ == "main":
            _, n_img, est = build_messages(doi, not args.no_images)
        else:
            _, n_img, est = build_messages_pass(doi, args.pass_)
        spent = used_tokens()
        if spent + est + 30_000 > args.token_cap:
            print(f"STOP: token cap {args.token_cap:,} would be exceeded (spent {spent:,}, next ~{est + 30_000:,})")
            break
        if args.pass_ != "main" and used_tokens_pass(args.pass_) + est + 30_000 > args.pass_cap:
            print(f"STOP: {args.pass_} pass cap {args.pass_cap:,} would be exceeded "
                  f"(pass spent {used_tokens_pass(args.pass_):,}, next ~{est + 30_000:,})")
            break
        print(f"extract {doi}  (~{est:,} prompt tokens est., {n_img} images, spent so far {spent:,})", flush=True)
        try:
            if router is not None:
                data, usage = router.call(lambda c: extract_one(c, doi, args.model, args.effort, not args.no_images,
                                                                 args.max_out, args.pass_))
            else:
                data, usage = extract_one(client, doi, args.model, args.effort, not args.no_images, args.max_out,
                                          args.pass_)
        except Exception as e:  # log and continue with the next paper
            print(f"  ERROR {type(e).__name__}: {str(e)[:300]}")
            continue
        usage["cumulative_total_tokens"] = spent + usage["total_tokens"]
        usage["pass"] = args.pass_
        data.setdefault("_meta", {})["pass"] = args.pass_
        log_usage(usage)
        if data.get("extraction_notes") == "UNPARSEABLE OUTPUT":
            print(f"  UNPARSEABLE output not saved ({usage['total_tokens']:,} tokens); rerun retries this paper")
            continue
        out_path.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"  {usage['n_records']} records, {usage['total_tokens']:,} tokens "
              f"(prompt {usage['prompt_tokens']:,}, out {usage['completion_tokens']:,}, reasoning {usage['reasoning_tokens']:,}), "
              f"{usage['seconds']} s, finish={usage['finish_reason']}", flush=True)


if __name__ == "__main__":
    main()
