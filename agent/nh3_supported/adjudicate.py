"""Reconcile the two extraction passes, check every number against the page text, apply the manual adjudication,
and write out/records.csv for analysis/nh3_supported_2026_10_06/run_supported_chain.py.

Per page, rows of pass a and pass b are paired in printed order (row counts must match; a mismatch is listed).
For each numeric field: agree = both passes give the same value; in_text = the value appears in the pdfplumber/pdfium
text of that page (thin spaces and thousands separators removed). Fields where the passes disagree or a value is not
found in the text are written to out/review.csv; out/manual_adjudication.csv (page, row, field, value, basis) holds
the decision taken from the page image and overrides pass a.

Primary-source errata: out/primary_errata.csv (page, row, field, review_value, paper_value, paper_locator, source)
is applied after the manual adjudication. It holds the review misprints found by checking the cited papers (PR #27,
agent/nh3_field/eval/humphreys_adjudication.csv); the paper value supersedes the review value, paper_value "none"
empties the field, and records.csv names every correction in the column `erratum`. The review value in the errata
file must equal the adjudicated value, so the layer cannot drift silently from the extraction.

Normalization (recorded per row): metal content from the content column, or from a leading "x%" in the catalyst name
for Table 1 (flagged); rate printed in umol g-1 h-1, or mL h-1 g-1 converted with 22,414 mL mol-1, or derived from
the printed outlet NH3 fraction and WHSV (flagged); fused-iron rows (Fe3O4, Fe1-xO, wustite) take the benchmark
metal content.
"""
import csv
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
TEXT = HERE / "text" / "humphreys2021.txt"
VM_ML = 22414.0
FIELDS = ["metal_content_wt_pct", "metal_content_wt_pct_max", "temperature_C", "temperature_C_max", "pressure_MPa",
          "pressure_MPa_max", "whsv_mL_g_h", "whsv_mL_g_h_max", "outlet_nh3_vol_pct", "rate_value", "rate_value_max"]
TEXT_FIELDS = ["catalyst_as_printed", "reference_number", "rate_unit"]
FUSED = re.compile(r"^(Fe3O4|Fe1−xO|Fe1-xO|ZBRW|.*w[uü]stite)", re.I)


def pages_text():
    parts = re.split(r"=== PAGE (\d+) ===", TEXT.read_text(encoding="utf-8"))
    return {int(p): re.sub(r"(?<=\d)[\s  ,](?=\d{3}\b)", "", t) for p, t in zip(parts[1::2], parts[2::2])}


def num_forms(v):
    if v is None:
        return []
    out = {f"{v:g}", f"{v:.1f}", f"{v:.2f}", f"{int(v)}" if float(v).is_integer() else f"{v:g}"}
    return [s for s in out if s]


def in_text(v, text):
    return any(re.search(rf"(?<![\d.]){re.escape(s)}(?![\d])", text) for s in num_forms(v))


def load(pass_):
    d = {}
    for f in sorted((OUT / f"pass_{pass_}").glob("p*.json")):
        j = json.loads(f.read_text(encoding="utf-8"))
        d[int(f.stem[1:])] = j["rows"]
    return d


def main():
    A, B, T = load("a"), load("b"), pages_text()
    manual = {}
    mpath = OUT / "manual_adjudication.csv"
    if mpath.exists():
        for m in csv.DictReader(mpath.open(encoding="utf-8")):
            manual[(int(m["page"]), int(m["row"]), m["field"])] = m
    errata = {}
    epath = OUT / "primary_errata.csv"
    if epath.exists():
        for e in csv.DictReader(epath.open(encoding="utf-8")):
            errata.setdefault((int(e["page"]), int(e["row"])), []).append(e)
    review, records, stats = [], [], dict(rows=0, numeric_fields=0, agree=0, in_text=0, manual=0, count_mismatch_pages=[],
                                          errata_fields=0, errata_rows=0)
    for page in sorted(A):
        ra, rb = A[page], B.get(page, [])
        if len(ra) != len(rb):
            stats["count_mismatch_pages"].append((page, len(ra), len(rb)))
        for i, a in enumerate(ra):
            b = rb[i] if i < len(rb) else None
            row = dict(a)
            for f in FIELDS:
                va, vb = a[f], (b[f] if b else None)
                if va is None and vb is None:
                    continue
                stats["numeric_fields"] += 1
                agree = va == vb
                found = in_text(va, T[page]) if va is not None else False
                stats["agree"] += agree
                stats["in_text"] += found
                if (page, i, f) in manual:
                    m = manual[(page, i, f)]
                    row[f] = None if m["value"] in ("", "null") else float(m["value"])
                    stats["manual"] += 1
                elif not agree or (va is not None and not found):
                    review.append(dict(page=page, row=i, catalyst=a["catalyst_as_printed"], field=f, pass_a=va, pass_b=vb,
                                       a_in_text=found))
            for f in TEXT_FIELDS:
                if b and a[f] != b[f] and (page, i, f) not in manual:
                    review.append(dict(page=page, row=i, catalyst=a["catalyst_as_printed"], field=f, pass_a=a[f],
                                       pass_b=b[f], a_in_text=""))
                if (page, i, f) in manual:
                    row[f] = manual[(page, i, f)]["value"]
            notes = apply_errata(row, errata.get((page, i), []))
            stats["errata_fields"] += len(notes)
            stats["errata_rows"] += bool(notes)
            rec = normalize(page, i, row)
            rec["erratum"] = "; ".join(notes)
            records.append(rec)
            stats["rows"] += 1
    with (OUT / "review.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["page", "row", "catalyst", "field", "pass_a", "pass_b", "a_in_text"])
        w.writeheader()
        w.writerows(review)
    with (OUT / "records.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(records[0]))
        w.writeheader()
        w.writerows(records)
    stats["review_items"] = len(review)
    (OUT / "adjudication_summary.json").write_text(json.dumps(stats, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(stats, indent=1))


def apply_errata(row, items):
    """Replace review values by the primary-paper values; returns one note per corrected field."""
    notes = []
    for e in items:
        f, old, new = e["field"], row[e["field"]], e["paper_value"]
        if f in FIELDS:
            same = old is not None and float(old) == float(e["review_value"])
        else:
            same = (";".join(old) if isinstance(old, list) else old) == e["review_value"]
        if not same:
            raise SystemExit(f"erratum p{e['page']} r{e['row']} {f}: review_value {e['review_value']!r}, record {old!r}")
        if f == "active_metals":
            row[f] = [] if new == "none" else new.split(";")
        elif f in FIELDS:
            row[f] = None if new == "none" else float(new)
        else:
            row[f] = new
        notes.append(f"{f} {e['review_value']} -> {new} ({e['source']}: {e['paper_locator']})")
    return notes


def normalize(page, i, r):
    name = r["catalyst_as_printed"]
    flags = []
    w = r["metal_content_wt_pct"]
    if r["metal_content_wt_pct_max"] is not None:
        flags.append("metal content range, lower value used")
    if w is not None and r["metal_content_as_printed"] and name.strip().startswith(r["metal_content_as_printed"].strip()):
        flags.append("metal content from catalyst name")
    fused = bool(FUSED.match(name.strip()))
    unit = (r["rate_unit"] or "").replace("μ", "u").replace("µ", "u").replace("−", "-").replace(" ", "")
    rate, src = None, ""
    if r["rate_value"] is not None:
        if unit.startswith("umolg-1h-1"):
            rate, src = r["rate_value"], "printed (umol g-1 h-1)"
        elif unit.startswith("mLh-1g-1") or unit.startswith("mlh-1g-1"):
            rate, src = r["rate_value"] / VM_ML * 1e6, "printed (mL h-1 g-1), converted"
    if rate is None and r["outlet_nh3_vol_pct"] is not None and r["whsv_mL_g_h"] is not None:
        rate, src = r["outlet_nh3_vol_pct"] / 100.0 * r["whsv_mL_g_h"] / VM_ML * 1e6, "derived from outlet NH3 and WHSV"
    if r["rate_value_max"] is not None or r["temperature_C_max"] is not None or r["pressure_MPa_max"] is not None:
        flags.append("range in table, lower value used")
    return dict(id=f"T{r['table'].split()[-1] if r['table'] else '?'}-p{page}-r{i}", table=r["table"], page=page,
                catalyst=name, active_metals=";".join(r["active_metals"]), metal_wt_pct="" if w is None else w,
                fused_fe=fused, T_C=r["temperature_C"] if r["temperature_C"] is not None else "",
                P_MPa=r["pressure_MPa"] if r["pressure_MPa"] is not None else "",
                whsv_mL_g_h="" if r["whsv_mL_g_h"] is None else r["whsv_mL_g_h"],
                outlet_nh3_vol_pct="" if r["outlet_nh3_vol_pct"] is None else r["outlet_nh3_vol_pct"],
                rate_umol_g_h="" if rate is None else rate, rate_unit_ok=rate is not None, rate_source=src,
                promoters=r["promoters_as_printed"] or "", support=r["support"] or "", ref=r["reference_number"] or "",
                notes="; ".join([r["notes"]] + flags).strip("; "))


if __name__ == "__main__":
    main()
