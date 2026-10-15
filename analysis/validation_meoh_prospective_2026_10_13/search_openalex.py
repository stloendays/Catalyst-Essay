"""The pre-registered OpenAlex search (PREREGISTRATION.md section 5).

One query, run once; the ranked result is saved as search_results.csv and is the fixed screening order. Rerunning
the script writes search_results_rerun.csv and never overwrites the committed list.

    python search_openalex.py            # first run: search_results.csv + search_query.json
"""
import csv
import json
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
UA = {"User-Agent": "Catalyst-Essay prospective-holdout"}

QUERY = {
    "endpoint": "https://api.openalex.org/works",
    "search": "CO2 hydrogenation methanol catalyst",
    "filter": ("from_publication_date:2025-11-05,to_publication_date:2026-10-13,"
               "type:article,language:en"),
    "sort": "relevance_score:desc",
    "per_page": 200,
    "max_results": 800,
    "select": "id,doi,title,publication_date,primary_location,relevance_score,type,abstract_inverted_index",
}


def get(params):
    url = QUERY["endpoint"] + "?" + urllib.parse.urlencode(params)
    for k in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                return json.load(r)
        except OSError:
            time.sleep(3 * (k + 1))
    raise SystemExit("OpenAlex not reachable")


def abstract(inv):
    if not inv:
        return ""
    pos = {}
    for w, idx in inv.items():
        for i in idx:
            pos[i] = w
    return " ".join(pos[i] for i in sorted(pos))


def main():
    out = HERE / ("search_results.csv" if not (HERE / "search_results.csv").exists() else "search_results_rerun.csv")
    rows, cursor, total = [], "*", None
    while cursor and len(rows) < QUERY["max_results"]:
        js = get({"search": QUERY["search"], "filter": QUERY["filter"], "sort": QUERY["sort"],
                  "per-page": QUERY["per_page"], "cursor": cursor, "select": QUERY["select"]})
        total = js["meta"]["count"]
        for w in js["results"]:
            src = ((w.get("primary_location") or {}).get("source") or {})
            rows.append(dict(rank=len(rows) + 1, doi=(w.get("doi") or "").replace("https://doi.org/", "").lower(),
                             publication_date=w.get("publication_date", ""), relevance_score=w.get("relevance_score"),
                             journal=src.get("display_name") or "", title=(w.get("title") or "").replace("\n", " "),
                             openalex_id=w.get("id", ""), abstract=abstract(w.get("abstract_inverted_index"))[:3000]))
        cursor = js["meta"].get("next_cursor")
        if not js["results"]:
            break
    rows = rows[:QUERY["max_results"]]
    # abstracts are publisher text: kept in a git-ignored file for the title/abstract screen only
    with (HERE / "search_abstracts_local.csv").open("w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=["rank", "doi", "abstract"])
        wr.writeheader()
        wr.writerows({k: r[k] for k in ("rank", "doi", "abstract")} for r in rows)
    with out.open("w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=[k for k in rows[0] if k != "abstract"])
        wr.writeheader()
        wr.writerows({k: v for k, v in r.items() if k != "abstract"} for r in rows)
    if out.name == "search_results.csv":
        meta = dict(QUERY, run_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"), total_matches=total,
                    saved=len(rows))
        (HERE / "search_query.json").write_text(json.dumps(meta, indent=1) + "\n", encoding="utf-8")
    print(f"{total} matches; saved {len(rows)} to {out.name}")


if __name__ == "__main__":
    sys.exit(main())
