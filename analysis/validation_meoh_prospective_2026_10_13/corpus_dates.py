"""Publication dates (OpenAlex) of the frozen methanol extraction corpus (agent/extraction/paper_set.txt).

Writes frozen_corpus_dates.csv; the latest date fixes the start of the prospective search window (PREREGISTRATION.md).
"""
import csv
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "agent" / "extraction"))
from paper_set import load_paper_set  # noqa: E402

UA = {"User-Agent": "Catalyst-Essay prospective-holdout"}


def work(doi):
    url = "https://api.openalex.org/works/doi:" + urllib.parse.quote(doi)
    for _ in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
                return json.load(r)
        except OSError:
            time.sleep(2)
    return None


def main():
    rows = []
    for doi, ref in load_paper_set().items():
        w = work(doi) or {}
        rows.append(dict(doi=doi, reference=ref, publication_date=w.get("publication_date", ""),
                         openalex_id=w.get("id", ""), title=(w.get("title") or "")[:160]))
    rows.sort(key=lambda r: r["publication_date"])
    with (HERE / "frozen_corpus_dates.csv").open("w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0]))
        wr.writeheader()
        wr.writerows(rows)
    for r in rows[-6:]:
        print(r["publication_date"], r["doi"], r["title"][:80])
    print("papers", len(rows), "missing dates", sum(1 for r in rows if not r["publication_date"]))


if __name__ == "__main__":
    main()
