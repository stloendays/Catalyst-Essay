"""Download the open-access PDF of each selected paper: try every OpenAlex location, keep the first real PDF whose
text contains the DOI or title words. Writes pdf/<rxn>/<slug>.pdf and fetch_<rxn>.json."""
import json, re, sys, time, urllib.request
from pathlib import Path
import pypdfium2 as pdfium
rxn = sys.argv[1]
sel = json.load(open(f"selected_{rxn}.json", encoding="utf-8"))
out = Path("pdf") / rxn; out.mkdir(parents=True, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36",
      "Accept": "application/pdf,*/*"}
def slug(d): return re.sub(r"[^A-Za-z0-9]+", "_", d)
def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r: return r.read()
res = []
for p in sel:
    doi = p["doi"]; dst = out / f"{slug(doi)}.pdf"
    if dst.exists():
        res.append(dict(doi=doi, title=p["title"], status="ok", url="cached", pages=None)); print("ok(cached)", doi); continue
    w = json.load(urllib.request.urlopen(urllib.request.Request(
        "https://api.openalex.org/works/doi:" + doi, headers={"User-Agent": "catalyst-essay-pipeline"}), timeout=60))
    urls = [l.get("pdf_url") for l in [w.get("best_oa_location") or {}] + (w.get("locations") or []) if l and l.get("pdf_url")]
    urls = list(dict.fromkeys(urls))
    status, used = "fail", None
    for u in urls:
        try:
            b = get(u)
        except Exception as e:
            continue
        if not b.startswith(b"%PDF"): continue
        dst.write_bytes(b)
        try:
            pdf = pdfium.PdfDocument(str(dst)); n = len(pdf)
            txt = " ".join(pdf[i].get_textpage().get_text_range() for i in range(min(2, n))).lower()
            pdf.close()
        except Exception:
            try: pdf.close()
            except Exception: pass
            dst.unlink(); continue
        words = [x for x in re.findall(r"[a-z]{5,}", (p["title"] or "").lower())][:6]
        hit = doi.lower() in txt or sum(x in txt for x in words) >= max(3, len(words) - 2)
        if hit:
            status, used = "ok", u; break
        dst.unlink()
    res.append(dict(doi=doi, title=p["title"], status=status, url=used, pages=n if status == "ok" else None))
    print(status, doi, used and used[:70])
json.dump(res, open(f"fetch_{rxn}.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(sum(r["status"] == "ok" for r in res), "/", len(res))
