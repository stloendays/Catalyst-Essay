"""Second, wider OpenAlex pass for the sample extension: every open-access article with the reaction in the title,
2010-2026, up to 600 per reaction, minus the papers already fetched. Writes candidates2_<rxn>.csv."""
import csv, json, sys, time, urllib.parse, urllib.request
TITLES = {"pdh": "propane dehydrogenation", "ch4": "methanation"}
def inv(ab):
    return " ".join(w for _, w in sorted((p, w) for w, ps in (ab or {}).items() for p in ps))
for rx in sys.argv[1:] or ["pdh", "ch4"]:
    res = []
    for page in (1, 2, 3):
        url = ("https://api.openalex.org/works?filter=title.search:" + urllib.parse.quote(TITLES[rx]) +
               ",is_oa:true,type:article,from_publication_date:2010-01-01,has_doi:true"
               f"&sort=cited_by_count:desc&per-page=200&page={page}")
        for attempt in range(3):
            try:
                d = json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "catalyst-essay-pipeline"}), timeout=90)); break
            except Exception as e:
                print("retry", page, e); time.sleep(5)
        res += d["results"]
        if len(d["results"]) < 200: break
    used = {x["doi"] for x in json.load(open(f"fetch_{rx}.json", encoding="utf-8"))}
    rows = []
    for w in res:
        doi = (w.get("doi") or "").replace("https://doi.org/", "")
        if doi in used: continue
        loc = w.get("best_oa_location") or {}
        rows.append(dict(doi=doi, year=w.get("publication_year"), title=w.get("title"),
                         venue=(loc.get("source") or {}).get("display_name"), cites=w.get("cited_by_count"),
                         oa_pdf_url=loc.get("pdf_url"), abstract=inv(w.get("abstract_inverted_index"))[:1500]))
    with open(f"candidates2_{rx}.csv", "w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, list(rows[0])); wr.writeheader(); wr.writerows(rows)
    print(rx, len(rows), "new candidates;", sum(r["doi"].startswith("10.1016") for r in rows), "Elsevier")
