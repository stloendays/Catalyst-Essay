"""OpenAlex search for open-access experimental catalyst papers of one reaction.
Writes candidates_<rxn>.csv: doi, year, title, venue, cites, oa_pdf_url, license, abstract."""
import csv, json, sys, urllib.parse, urllib.request
rxn, query = sys.argv[1], sys.argv[2]
n = int(sys.argv[3]) if len(sys.argv) > 3 else 60
def inv(ab):
    if not ab: return ""
    pos = sorted((p, w) for w, ps in ab.items() for p in ps)
    return " ".join(w for _, w in pos)
url = ("https://api.openalex.org/works?search=" + urllib.parse.quote(query) +
       "&filter=title.search:" + urllib.parse.quote(sys.argv[4] if len(sys.argv) > 4 else query) + ",is_oa:true,type:article,publication_year:2012-2025,has_doi:true&sort=cited_by_count:desc&per-page=%d" % n)
req = urllib.request.Request(url, headers={"User-Agent": "catalyst-essay-pipeline"})
data = json.load(urllib.request.urlopen(req, timeout=60))
rows = []
for w in data["results"]:
    loc = w.get("best_oa_location") or {}
    rows.append(dict(doi=(w.get("doi") or "").replace("https://doi.org/", ""), year=w.get("publication_year"),
                     title=w.get("title"), venue=((loc.get("source") or {}).get("display_name")),
                     cites=w.get("cited_by_count"), oa_pdf_url=loc.get("pdf_url"), license=loc.get("license"),
                     abstract=inv(w.get("abstract_inverted_index"))[:1500]))
with open(f"candidates_{rxn}.csv", "w", newline="", encoding="utf-8") as f:
    wr = csv.DictWriter(f, list(rows[0])); wr.writeheader(); wr.writerows(rows)
print(len(rows), "candidates;", sum(1 for r in rows if r["oa_pdf_url"]), "with OA pdf url")
for r in rows: print(r["year"], r["cites"], (r["venue"] or "")[:28], "|", (r["title"] or "")[:110], "|", "PDF" if r["oa_pdf_url"] else "-")
