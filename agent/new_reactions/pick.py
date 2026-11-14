import csv, sys, json
rxn = sys.argv[1]; keys = [k.lower() for k in sys.argv[2:]]
rows = list(csv.DictReader(open(f"candidates_{rxn}.csv", encoding="utf-8")))
out = []
for k in keys:
    m = [r for r in rows if k in (r["title"] or "").lower() and r["oa_pdf_url"]]
    if not m: print("NO MATCH", k); continue
    out.append(m[0]); print(m[0]["doi"], "|", m[0]["title"][:90], "|", m[0]["oa_pdf_url"][:80])
json.dump(out, open(f"selected_{rxn}.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
