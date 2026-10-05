"""LLM extraction of CO2-to-methanol catalyst performance entries into schema.json.

Usage:
    python extract_records.py                    # every ok paper in fetch_manifest.json
    python extract_records.py --doi 10.1021/cs500979c --force

Input per paper: text/<slug>.txt (pypdfium2 text + pdfplumber tables, page
markers) and the rendered page images text/img/<slug>_p<n>.jpg. One API call
per paper, strict JSON-schema output, raw result in out/raw/<slug>.json.
Every call is logged to out/token_usage.csv. Hard caps: --max-papers
(default 15) and --token-cap (default 3,000,000 total tokens, counted from the
log, so the cap holds across reruns). Nothing from the evaluation datasets is
read here; the prompt contains only the paper itself.

The API key is resolved by the harness resolver and handed straight to the
client; it is never printed, logged or stored.
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
USAGE_CSV = OUT_DIR / "token_usage.csv"
SCHEMA = json.loads((HERE / "schema.json").read_text(encoding="utf-8"))
HARNESS_AGENT = r"D:\论文-AI4S\Catalyst_Economic_Leverage_Automation_Harness_v0.1\agent"

USAGE_FIELDS = ["timestamp", "doi", "model", "reasoning_effort", "images", "prompt_tokens", "cached_tokens",
                "completion_tokens", "reasoning_tokens", "total_tokens", "cumulative_total_tokens",
                "finish_reason", "n_records", "seconds"]

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


def extract_one(client, doi: str, model: str, effort: str, use_images: bool, max_out: int) -> dict:
    messages, n_img, _ = build_messages(doi, use_images)
    t0 = time.time()
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


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--doi", action="append", help="limit to these DOIs (repeatable)")
    ap.add_argument("--model", default="gpt-5.5")
    ap.add_argument("--effort", default="medium", choices=["minimal", "low", "medium", "high", "xhigh"])
    ap.add_argument("--no-images", action="store_true")
    ap.add_argument("--max-papers", type=int, default=15)
    ap.add_argument("--token-cap", type=int, default=3_000_000)
    ap.add_argument("--max-out", type=int, default=100_000)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    manifest = json.loads((HERE / "fetch_manifest.json").read_text(encoding="utf-8"))
    dois = [r["doi"] for r in manifest if r["status"] in ("ok", "skip") and r["file"]]
    if args.doi:
        wanted = {d.lower() for d in args.doi}
        dois = [d for d in dois if d in wanted]
    if len(dois) > args.max_papers:
        sys.exit(f"{len(dois)} papers exceed --max-papers {args.max_papers}")

    sys.path.insert(0, HARNESS_AGENT)
    from llm_client import resolve_api_key
    import openai
    client = openai.OpenAI(api_key=resolve_api_key(), timeout=1800)

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for doi in dois:
        out_path = RAW_DIR / f"{slug(doi)}.json"
        if out_path.exists() and not args.force:
            print(f"skip {doi} (exists)")
            continue
        _, n_img, est = build_messages(doi, not args.no_images)
        spent = used_tokens()
        if spent + est + 30_000 > args.token_cap:
            print(f"STOP: token cap {args.token_cap:,} would be exceeded (spent {spent:,}, next ~{est + 30_000:,})")
            break
        print(f"extract {doi}  (~{est:,} prompt tokens est., {n_img} images, spent so far {spent:,})", flush=True)
        try:
            data, usage = extract_one(client, doi, args.model, args.effort, not args.no_images, args.max_out)
        except Exception as e:  # log and continue with the next paper
            print(f"  ERROR {type(e).__name__}: {str(e)[:300]}")
            continue
        usage["cumulative_total_tokens"] = spent + usage["total_tokens"]
        log_usage(usage)
        out_path.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"  {usage['n_records']} records, {usage['total_tokens']:,} tokens "
              f"(prompt {usage['prompt_tokens']:,}, out {usage['completion_tokens']:,}, reasoning {usage['reasoning_tokens']:,}), "
              f"{usage['seconds']} s, finish={usage['finish_reason']}", flush=True)


if __name__ == "__main__":
    main()
