"""Extraction agent for the experimental ammonia-synthesis catalysts tabulated in Humphreys, Lan & Tao,
Adv. Energy Sustain. Res. 2, 2000043 (2021), doi:10.1002/aesr.202000043, Tables 1-6.

One gpt-5.5 call per table page (API-YES first, advisor key once API-YES is used up; agent/extraction/llm_route.py),
strict JSON schema, input = the page text (pypdfium2 + pdfplumber) and a 2.2x page image. Two independent passes
(--pass a / --pass b, same prompt); adjudicate.py compares them with each other and with the numbers printed in the
page text, and every disagreement is checked against the page image.

    python extract_tables.py --pass a
    python extract_tables.py --pass b

The prompt contains only the review pages. Keys are never printed, logged or stored.
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
sys.path.insert(0, str(HERE.parent / "extraction"))
from llm_route import Router  # noqa: E402

PDF = HERE / "pdf" / "humphreys2021.pdf"
TEXT = HERE / "text"
OUT = HERE / "out"
DOI = "10.1002/aesr.202000043"
TABLE_PAGES = (6, 10, 11, 13, 16, 17, 19)
HI_RES = 2.2

NUM = {"type": ["number", "null"]}
S = {"type": "string"}
S_N = {"type": ["string", "null"]}


def obj(props):
    return {"type": "object", "additionalProperties": False, "required": list(props), "properties": props}


ROW = obj({
    "table": S, "catalyst_as_printed": S,
    "active_metals": {"type": "array", "items": S},
    "metal_content_as_printed": S_N, "metal_content_wt_pct": NUM,
    "metal_content_wt_pct_max": NUM,
    "support": S_N, "promoters_as_printed": S_N,
    "temperature_C": NUM, "temperature_C_max": NUM,
    "pressure_MPa": NUM, "pressure_MPa_max": NUM,
    "whsv_as_printed": S_N, "whsv_mL_g_h": NUM, "whsv_mL_g_h_max": NUM,
    "outlet_nh3_vol_pct": NUM,
    "rate_as_printed": S_N, "rate_value": NUM, "rate_value_max": NUM, "rate_unit": S_N,
    "reference_number": S_N,
    "notes": S})
SCHEMA = obj({"page": {"type": "integer"}, "column_headers_as_printed": {"type": "array", "items": S},
              "rows": {"type": "array", "items": ROW}, "page_notes": S})

SYSTEM = """You transcribe the catalyst tables of one page of a review on ammonia-synthesis catalysts.
Return one JSON object following the schema, with one entry in rows for every table row on this page, in the printed
order, including rows that continue a table from the previous page. Do not add rows from the running text.

Rules:
- Copy each cell as printed into the *_as_printed fields. Fill the numeric fields with the number as printed, in the
  unit of the column header (temperature in deg C, pressure in MPa, space velocity in mL g-1 h-1, NH3 outlet in v/v %).
  A range such as "0.4-1.0" or "18 000-36 000" gives the lower value in the field and the upper value in *_max.
- metal_content_wt_pct: only when the cell gives the metal content in wt%. Ratios (Cs/Ru = 1), at% or mmol g-1 stay
  in metal_content_as_printed with the numeric field null. "-" or an empty cell is null.
- active_metals: the catalytic metals named in the catalyst (e.g. ["Ru"], ["Co"], ["Fe"], ["Co", "Mo"]); promoters
  (Ba, Cs, K, La, Ce ...) and supports are not active metals.
- rate_value: the NH3 synthesis rate as printed and rate_unit the unit of its column header, e.g. "umol g-1 h-1" or
  "mL h-1 g-1"; if a row gives the rate in another unit inside the cell, record that unit.
- reference_number: the number in the Ref. column.
- Never compute or convert values. Put anything unusual (footnotes, "after 20 h", per g of metal) in notes."""


def slug_page(p):
    return f"p{p:02d}"


def page_text(page: int) -> str:
    txt = (TEXT / "humphreys2021.txt").read_text(encoding="utf-8")
    parts = re.split(r"=== PAGE (\d+) ===", txt)
    return dict(zip(map(int, parts[1::2]), parts[2::2]))[page]


def page_image(page: int) -> Path:
    out = TEXT / "img_hi" / f"humphreys2021_p{page}.jpg"
    if not out.exists():
        import pypdfium2 as pdfium
        out.parent.mkdir(parents=True, exist_ok=True)
        pdfium.PdfDocument(str(PDF))[page - 1].render(scale=HI_RES).to_pil().convert("RGB").save(out, quality=90)
    return out


def extract_page(router: Router, page: int, model: str, effort: str) -> tuple[dict, dict]:
    content = [{"type": "input_text", "text": f"Review DOI: {DOI}. PDF page {page}.\n\nPAGE TEXT:\n{page_text(page)}"},
               {"type": "input_text", "text": "Page image:"},
               {"type": "input_image", "detail": "high",
                "image_url": "data:image/jpeg;base64," + base64.b64encode(page_image(page).read_bytes()).decode("ascii")},
               {"type": "input_text", "text": "Transcribe every table row on this page now, following the system rules."}]

    def call(client):
        stream = client.responses.create(
            model=model, instructions=SYSTEM, input=[{"role": "user", "content": content}],
            text={"format": {"type": "json_schema", "name": "nh3_catalyst_table_rows", "strict": True, "schema": SCHEMA}},
            reasoning={"effort": effort}, store=False, stream=True)
        pieces, final = [], None
        for ev in stream:
            if ev.type == "response.output_text.delta":
                pieces.append(ev.delta)
            elif ev.type in ("response.completed", "response.incomplete"):
                final = ev.response
        return "".join(pieces), final, client._route

    t0 = time.time()
    text, final, route = router.call(call)
    data = json.loads(text)
    u = final.usage
    usage = {"timestamp": datetime.now().isoformat(timespec="seconds"), "page": page, "route": route,
             "model": final.model, "effort": effort, "prompt_tokens": u.input_tokens,
             "completion_tokens": u.output_tokens, "total_tokens": u.total_tokens, "status": final.status,
             "rows": len(data["rows"]), "seconds": round(time.time() - t0, 1)}
    return data, usage


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pass", dest="pass_", choices=["a", "b"], required=True)
    ap.add_argument("--model", default="gpt-5.5")
    ap.add_argument("--effort", default="medium")
    ap.add_argument("--page", type=int, action="append")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    out = OUT / f"pass_{a.pass_}"
    out.mkdir(parents=True, exist_ok=True)
    router = None
    usage_csv = OUT / "token_usage.csv"
    for page in a.page or TABLE_PAGES:
        path = out / f"{slug_page(page)}.json"
        if path.exists() and not a.force:
            print(f"skip page {page}")
            continue
        router = router or Router(a.model)
        data, usage = extract_page(router, page, a.model, a.effort)
        usage["pass"] = a.pass_
        path.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
        new = not usage_csv.exists()
        with usage_csv.open("a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(usage))
            if new:
                w.writeheader()
            w.writerow(usage)
        print(f"page {page}: {usage['rows']} rows, {usage['total_tokens']:,} tokens, {usage['seconds']} s ({usage['route']})",
              flush=True)


if __name__ == "__main__":
    main()
