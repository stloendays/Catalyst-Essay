"""Download the Supporting Information (SI) of the ammonia field papers into the git-ignored si/ folder (copied from
agent/extraction/fetch_si.py; a browser error on one paper is recorded as fail and retried on the next run).

Usage (run with the nus-fetch interpreter, which has playwright):
    D:\\Tools\\nus-fetch\\.venv\\Scripts\\python.exe fetch_si.py [--doi DOI ...] [--no-browser]

Routes, in order:
1. Public routes without a browser. Elsevier SI sits on the public CDN
   ars.els-cdn.com/content/image/1-s2.0-<PII>-mmc<k>.<ext> (PII from Crossref).
2. Publisher landing page through the NUS EZproxy, using the nus-fetch module and its browser
   profile (imported, not modified; cookies are not written back). The script collects the
   page's SI links (ACS /doi/suppl/, Science /doi/suppl/, Wiley /action/downloadSupplement,
   RSC suppdata, Nature/Springer ESM files *_MOESM<k>_ESM.*) and downloads them with the same browser
   context.
A publisher bot check (Cloudflare, ScienceDirect challenge) is never automated: the paper is
marked `manual` in si_manifest.json for the user to download by hand.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

import requests

HERE = Path(__file__).resolve().parent
SI_DIR = HERE / "si"
MANIFEST = HERE / "si_manifest.json"
NUS_FETCH_DIR = Path(r"D:\Tools\nus-fetch")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/129.0 Safari/537.36"}
EXTS = ("pdf", "docx", "doc", "xlsx", "xls")
SI_LINK = re.compile(r"(/doi/suppl/|downloadSupplement|/suppdata/|suppl_file|article-supplement/|_si_\d+|_sm\.pdf|_esi|"
                     r"static-content[.-]springer[.-]com/esm/|MOESM\d+_ESM)", re.I)


def slug(doi: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", doi.lower()).strip("_")


def kind(b: bytes) -> str | None:
    if b[:5] == b"%PDF-":
        return "pdf"
    if b[:2] == b"PK":
        return "zip"   # docx / xlsx (Office Open XML)
    if b[:8] == b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1":
        return "ole"   # legacy .doc / .xls
    return None


def elsevier_pii(doi: str) -> str | None:
    m = requests.get(f"https://api.crossref.org/works/{doi}", timeout=30).json()["message"]
    pii = [a for a in m.get("alternative-id", []) if re.fullmatch(r"S[0-9X]{16}", a)]
    return pii[0] if pii else None


def fetch_elsevier(doi: str) -> list[dict]:
    pii = elsevier_pii(doi)
    files = []
    if not pii:
        return files
    for k in range(1, 7):
        for ext in EXTS:
            url = f"https://ars.els-cdn.com/content/image/1-s2.0-{pii}-mmc{k}.{ext}"
            try:
                r = requests.get(url, headers=UA, timeout=60)
            except requests.RequestException:
                continue
            if r.status_code == 200 and kind(r.content) and not any(f["bytes"] == len(r.content) for f in files):
                name = f"{slug(doi)}__mmc{k}.{ext}"
                (SI_DIR / name).write_bytes(r.content)
                files.append({"file": name, "url": url, "bytes": len(r.content)})
    return files


def fetch_via_browser(br, nf, doi: str) -> tuple[str, list[dict], str]:
    landing = br.goto(f"{nf.PROXY}/login?url=https://doi.org/{doi}")
    if nf.is_auth(landing):
        return "fail", [], "EZproxy session not logged in"
    if br.bot_check():
        return "manual", [], f"publisher bot check on {nf.original_host(landing)}"
    host = nf.original_host(landing)
    links = set()
    try:
        hrefs = br.page.eval_on_selector_all("a[href]", "els => els.map(e => e.href)")
    except Exception:
        hrefs = []
    for h in hrefs:
        if SI_LINK.search(h) and not re.search(r"(citation|ris|bibtex|\.ris$)", h, re.I):
            links.add(h.split("#")[0])
    # ACS lists the files on /doi/suppl/<doi>; open that page when the landing page only links to it
    if host.endswith("pubs.acs.org") and not any(("suppl_file" in h or "article-supplement" in h) for h in links):
        br.goto(nf.to_proxy(f"https://pubs.acs.org/doi/suppl/{doi}"))
        if br.bot_check():
            return "manual", [], "ACS supporting-information page shows a bot check"
        hrefs = br.page.eval_on_selector_all("a[href]", "els => els.map(e => e.href)")
        links |= {h.split("#")[0] for h in hrefs if ("suppl_file" in h or "article-supplement" in h)}
    files = []
    for i, url in enumerate(sorted(links)):
        if not re.search(r"(suppl_file|downloadSupplement|suppdata|article-supplement/|\.pdf|\.docx?)", url, re.I):
            continue
        try:
            r = br.ctx.request.get(url, headers={"Referer": landing}, timeout=120000, max_redirects=10)
            body = r.body()
        except Exception:
            continue
        k = kind(body)
        if not k:
            if body and re.search(rb"just a moment|challenge|captcha", body[:4000], re.I):
                return "manual", files, f"bot check when downloading {nf.original_host(url)}"
            continue
        m = re.search(r"\.(pdf|docx|doc|xlsx|xls)(?:$|[?&])", url, re.I)
        ext = m.group(1).lower() if m else {"pdf": "pdf", "zip": "docx", "ole": "doc"}[k]
        if any(f["bytes"] == len(body) for f in files):
            continue
        name = f"{slug(doi)}__si{len(files) + 1}.{ext}"
        (SI_DIR / name).write_bytes(body)
        files.append({"file": name, "url": nf.original_host(url) + "/" + url.split("/", 3)[-1][:160], "bytes": len(body)})
    status = "ok" if files else "none"
    return status, files, "" if files else f"no SI link found on {host}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--doi", action="append")
    ap.add_argument("--no-browser", action="store_true")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    SI_DIR.mkdir(exist_ok=True)
    manifest = {r["doi"]: r for r in json.loads(MANIFEST.read_text(encoding="utf-8"))} if MANIFEST.exists() else {}
    papers = [r["doi"] for r in json.loads((HERE / "fetch_manifest.json").read_text(encoding="utf-8"))
              if r.get("status") in ("ok", "skip") and r.get("file")]
    if args.doi:
        papers = [d for d in papers if d in {x.lower() for x in args.doi}]
    todo = [d for d in papers if args.force or manifest.get(d, {}).get("status") not in ("ok", "none_public")]

    br = nf = None
    try:
        for doi in todo:
            row = {"doi": doi, "status": "none", "files": [], "route": "", "note": ""}
            if doi.startswith("10.1016/"):
                row["files"] = fetch_elsevier(doi)
                row["route"] = "public ars.els-cdn.com"
                row["status"] = "ok" if row["files"] else "none_public"
                if not row["files"]:
                    row["note"] = "no mmc file on the public CDN (the article may have no SI)"
            elif not args.no_browser:
                if br is None:
                    sys.path.insert(0, str(NUS_FETCH_DIR))
                    import nus_fetch as nf  # noqa: E402  (imported, not modified)
                    br = nf.Browser(headless=True)
                row["route"] = "EZproxy browser (nus-fetch profile)"
                try:
                    row["status"], row["files"], row["note"] = fetch_via_browser(br, nf, doi)
                except Exception as e:  # browser/network error on one paper: record it, rerun retries it
                    row["status"], row["note"] = "fail", f"{type(e).__name__}: {str(e)[:120]}"
            print(f"{row['status']:12s} {doi:32s} {len(row['files'])} file(s) {row['note']}", flush=True)
            manifest[doi] = row
            MANIFEST.write_text(json.dumps(sorted(manifest.values(), key=lambda r: r["doi"]), indent=1), encoding="utf-8")
            time.sleep(1)
    finally:
        if br is not None:  # close without writing cookies back to the nus-fetch state file
            try:
                br.ctx.close()
            finally:
                br.pw.stop()


if __name__ == "__main__":
    main()
