"""After the manual download: per reaction, which DOIs of downloads/<rxn>_dois.txt have a PDF whose own text carries
the DOI (nus-fetch manifest), which are still missing, and which files are in pdf/<rxn>/ without a listed DOI.
Writes downloads/<rxn>_status.csv and prints a short table."""
import csv
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main(rxns):
    for rx in rxns:
        want = [l.strip().lower() for l in (HERE / "downloads" / f"{rx}_dois.txt").read_text(encoding="utf-8").splitlines() if l.strip()]
        man = HERE / "pdf" / rx / "manifest.csv"
        got = {}
        if man.exists():
            for r in csv.DictReader(open(man, encoding="utf-8-sig")):
                got[r["doi"].lower()] = r                      # last row per DOI wins (assist rows come after fetch rows)
        rows = []
        for d in want:
            r = got.get(d, {})
            f = HERE / "pdf" / rx / r.get("file", "") if r.get("file") else None
            ok = r.get("status") in ("ok", "skip") and f is not None and f.exists()
            rows.append(dict(doi=d, status="ok" if ok else (r.get("status") or "not tried"), file=r.get("file", ""),
                             pages=r.get("pages", ""), doi_in_pdf=r.get("doi_in_pdf", ""), route=r.get("route", ""),
                             note=(r.get("note") or "")[:80]))
        with open(HERE / "downloads" / f"{rx}_status.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, list(rows[0]))
            w.writeheader()
            w.writerows(rows)
        (HERE / "downloads" / f"{rx}_missing.txt").write_text("\n".join(r["doi"] for r in rows if r["status"] != "ok") + "\n",
                                                             encoding="utf-8")
        n_ok = sum(r["status"] == "ok" for r in rows)
        unchecked = sum(r["status"] == "ok" and str(r["doi_in_pdf"]).lower() not in ("true", "1") for r in rows)
        print(f"{rx}: {n_ok}/{len(rows)} downloaded" + (f" ({unchecked} without the DOI printed in the PDF - check those)" if unchecked else ""))
        for r in rows:
            if r["status"] != "ok":
                print(f"   missing  {r['doi']}  [{r['status']}] {r['note']}")


if __name__ == "__main__":
    main(sys.argv[1:] or ["nh3dec", "rwgs", "etoh"])
