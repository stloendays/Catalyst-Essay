"""DOIs -> PDFs through the local nus-fetch tool (NUS EZproxy, then OA).

Usage:
    python fetch_papers.py -f candidates_round1.txt [-o pdf]

Runs `nus_fetch.py fetch -f <file> -o <dir> --headless --json`, then reads
`<dir>/last_run.json` and writes `fetch_manifest.json` next to this script
(DOI, status, file name, pages, doi_in_pdf, note). PDFs stay in the
git-ignored `pdf/` folder. Rows with status `manual` (publisher bot check)
are reported and never automated.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
NUS_FETCH_DIR = Path(r"D:\Tools\nus-fetch")
NUS_FETCH_PY = NUS_FETCH_DIR / ".venv" / "Scripts" / "python.exe"


def run_fetch(doi_file: Path, out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = [str(NUS_FETCH_PY), "nus_fetch.py", "fetch", "-f", str(doi_file),
           "-o", str(out_dir), "--headless", "--json"]
    proc = subprocess.run(cmd, cwd=NUS_FETCH_DIR, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    sys.stderr.write(proc.stderr[-4000:])
    return json.loads((out_dir / "last_run.json").read_text(encoding="utf-8"))


def update_manifest(summary: dict, manifest_path: Path) -> list[dict]:
    rows = {}
    if manifest_path.exists():
        rows = {r["doi"].lower(): r for r in json.loads(manifest_path.read_text(encoding="utf-8"))}
    items = summary.get("results") or summary.get("items") or summary.get("rows") or []
    for it in items:
        doi = str(it.get("doi", "")).lower()
        if not doi:
            continue
        prev = rows.get(doi, {})
        status = it.get("status")
        # a later "skip" means the file from an earlier ok run is still present
        if status == "skip" and prev.get("status") == "ok":
            continue
        rows[doi] = {
            "doi": doi,
            "status": status,
            "file": Path(it["file"]).name if it.get("file") else None,
            "pages": it.get("pages"),
            "doi_in_pdf": it.get("doi_in_pdf"),
            "title_overlap": it.get("title_overlap"),
            "route": it.get("route"),
            "note": it.get("note"),
        }
    out = sorted(rows.values(), key=lambda r: r["doi"])
    manifest_path.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("-f", "--file")
    ap.add_argument("-o", "--out", default=str(HERE / "pdf"))
    ap.add_argument("--from-csv", action="store_true",
                    help="rebuild fetch_manifest.json from <out>/manifest.csv (nus-fetch's own log) without fetching")
    args = ap.parse_args()
    if args.from_csv:
        import csv
        items = [dict(r, doi_in_pdf=r.get("doi_in_pdf") == "True") for r in
                 csv.DictReader((Path(args.out) / "manifest.csv").open(encoding="utf-8-sig"))]
        summary = {"results": items}
    else:
        summary = run_fetch(Path(args.file).resolve(), Path(args.out).resolve())
    rows = update_manifest(summary, HERE / "fetch_manifest.json")
    for r in rows:
        print(f'{r["status"]:7s} {r["doi"]:40s} pages={r["pages"]} doi_in_pdf={r["doi_in_pdf"]} {r["file"]}')
    manual = [r["doi"] for r in rows if r["status"] == "manual"]
    if manual:
        print("MANUAL (publisher bot check, not automated):", ", ".join(manual))


if __name__ == "__main__":
    main()
