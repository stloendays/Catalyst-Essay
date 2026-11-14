"""Self-check of the extraction, without a human gold standard: every value the model marked as printed
(qualifier '=') must appear as a number in the paper - in the Docling parse or in the PDF text layer (pypdfium2).
Plot readings ('~') cannot be checked this way and are counted separately. Writes results/verify_<rxn>.csv."""
import csv
import json
import re
import sys
from pathlib import Path

import pypdfium2 as pdfium

HERE = Path(__file__).resolve().parent
FIELDS = {"pdh": ["temperature", "propane_conversion", "propylene_selectivity", "propylene_yield", "propylene_rate",
                  "space_velocity", "stability_initial_conversion", "stability_final_conversion", "deactivation_constant"],
          "ch4": ["temperature", "co2_conversion", "ch4_selectivity", "co_selectivity", "ch4_yield", "ch4_rate",
                  "space_velocity", "stability_initial_conversion", "stability_final_conversion"]}


def numbers(text):
    t = text.replace("−", "-").replace("–", "-").replace(",", "")
    return {float(m) for m in re.findall(r"\d+(?:\.\d+)?(?:[eE][-+]?\d+)?", t)}


def pdf_for(rxn, stem):
    for p in (HERE / "pdf" / rxn).glob("*.pdf"):
        if p.stem[:60] == stem:
            return p


def run(rxn):
    out, tally = [], {"printed": 0, "found": 0, "plot": 0}
    for f in sorted((HERE / "raw" / rxn).glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        md = (HERE / "ocr" / rxn / (f.stem + ".md")).read_text(encoding="utf-8")
        pdf = pdfium.PdfDocument(str(pdf_for(rxn, f.stem)))
        raw = " ".join(pdf[i].get_textpage().get_text_range() for i in range(len(pdf)))
        pdf.close()
        pool = numbers(md) | numbers(raw)
        for r in d.get("records", []):
            for k in FIELDS[rxn]:
                v = r[k]
                if v["value"] is None:
                    continue
                if v["qualifier"] == "~":
                    tally["plot"] += 1
                    continue
                if v["qualifier"] not in ("=", "<", ">"):
                    continue
                x = abs(float(v["value"]))
                cands = {x, round(x, 6)}
                if x != 0:
                    e = int(f"{x:e}".split("e")[1])
                    cands |= {round(x / 10 ** e, 6), round(x * 1e3, 6), round(x / 1e3, 6), round(x * 100, 6), round(x / 100, 6),
                              round(x - 273.15, 2), round(x + 273.15, 2), round(x / 10 ** (e - 2), 6)}
                hit = any(abs(c - p) <= 1e-6 * max(1, abs(p)) for c in cands for p in pool)
                tally["printed"] += 1
                tally["found"] += hit
                out.append(dict(paper=f.stem, catalyst=r["catalyst_name"], field=k, value=v["value"], unit=v["unit"],
                                location=r["location"], found=hit))
    (HERE / "results").mkdir(exist_ok=True)
    with open(HERE / "results" / f"verify_{rxn}.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, list(out[0]))
        w.writeheader()
        w.writerows(out)
    print(rxn, tally, "traceable %.3f" % (tally["found"] / max(1, tally["printed"])))
    return tally


if __name__ == "__main__":
    for rxn in sys.argv[1:] or ["pdh", "ch4"]:
        run(rxn)
