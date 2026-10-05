"""PDF -> page-tagged text, tables and page images.

Running text comes from pypdfium2 (it follows the content stream, so
two-column layouts stay in reading order; pdfplumber interleaves the columns
line by line). Tables come from pdfplumber `extract_tables()`. Each page is
also rendered to `text/img/<slug>_p<n>.jpg` so the extraction model can read
tables whose cells pdfplumber misses and values plotted in figures.

Usage:
    python pdf_to_text.py            # all PDFs listed as ok in fetch_manifest.json

For each DOI writes `text/<slug>.json`:
    {"doi", "file", "pages": [{"page": n, "text": str, "tables": [[[cell]]]}]}
and `text/<slug>.txt`, the LLM input: every page opens with a
`=== PAGE n ===` marker and every pdfplumber table is appended after the page
text as a pipe-delimited block (`--- pdfplumber table p{n}.{k} ---`).
Page numbers are 1-based positions in the PDF file. `--si` converts the Supporting Information in si/
into text_si/ the same way (see convert_si). The text folder is
git-ignored (it is derived from the publisher PDF).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pdfplumber
import pypdfium2 as pdfium

HERE = Path(__file__).resolve().parent
PDF_DIR = HERE / "pdf"
TEXT_DIR = HERE / "text"


def slug(doi: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", doi.lower()).strip("_")


def clean_cell(c) -> str:
    return "" if c is None else re.sub(r"\s+", " ", str(c)).strip()


NL = chr(10)
IMG_SCALE = 1.5  # 612 pt page -> 918 px wide


def convert(pdf_path: Path, img_prefix: Path) -> list[dict]:
    pages = []
    doc = pdfium.PdfDocument(str(pdf_path))
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            pp = doc[i - 1]
            text = pp.get_textpage().get_text_range().replace("\ufffe", "-").replace("\r", "")
            if not text.strip():
                text = page.extract_text(x_tolerance=1.5, y_tolerance=3) or ""
            pp.render(scale=IMG_SCALE).to_pil().convert("RGB").save(f"{img_prefix}_p{i}.jpg", quality=85)
            tables = []
            try:
                for t in page.extract_tables():
                    rows = [[clean_cell(c) for c in row] for row in t if row]
                    rows = [r for r in rows if any(r)]
                    if len(rows) >= 2:
                        tables.append(rows)
            except Exception:  # malformed page geometry; keep the text
                pass
            pages.append({"page": i, "text": text, "tables": tables})
    return pages


def render_txt(pages: list[dict]) -> str:
    out = []
    for p in pages:
        out.append(f"=== PAGE {p['page']} ===")
        out.append(p["text"])
        for k, t in enumerate(p["tables"], start=1):
            out.append(f"--- pdfplumber table p{p['page']}.{k} ---")
            out.extend(" | ".join(r) for r in t)
    return "\n".join(out)


def convert_si() -> None:
    """SI mode: si/<slug>__*.pdf (Word SI already exported by si_docx2pdf.ps1) -> text_si/<slug>.txt and
    text_si/img/<slug>_p<n>.jpg. Pages are numbered continuously across the SI files of a paper and each
    page marker names its file, e.g. '=== PAGE 3 (SI file 10_1021_x__si1.pdf, page 3) ==='."""
    out_dir = HERE / "text_si"
    (out_dir / "img").mkdir(parents=True, exist_ok=True)
    si_dir = HERE / "si"
    by_paper: dict[str, list[Path]] = {}
    for f in sorted(si_dir.glob("*__*.pdf")):
        by_paper.setdefault(f.name.split("__")[0], []).append(f)
    for s, files in by_paper.items():
        pages, n = [], 0
        for f in files:
            tmp = out_dir / "img" / f"_tmp_{s}"
            for pg in convert(f, tmp):
                n += 1
                Path(f"{tmp}_p{pg['page']}.jpg").replace(out_dir / "img" / f"{s}_p{n}.jpg")
                pg["file"], pg["file_page"], pg["page"] = f.name, pg["page"], n
                pages.append(pg)
        out = []
        for p in pages:
            out.append(f"=== PAGE {p['page']} (SI file {p['file']}, page {p['file_page']}) ===")
            out.append(p["text"])
            for k, t in enumerate(p["tables"], start=1):
                out.append(f"--- pdfplumber table p{p['page']}.{k} ---")
                out.extend(" | ".join(r) for r in t)
        txt = NL.join(out)
        (out_dir / f"{s}.txt").write_text(txt, encoding="utf-8")
        (out_dir / f"{s}.json").write_text(json.dumps({"slug": s, "files": [f.name for f in files], "pages": pages},
                                                      ensure_ascii=False), encoding="utf-8")
        print(f"SI {s:36s} files={len(files)} pages={len(pages):3d} chars={len(txt)}")


def main() -> None:
    import sys
    if "--si" in sys.argv:
        convert_si()
        return
    TEXT_DIR.mkdir(exist_ok=True)
    manifest = json.loads((HERE / "fetch_manifest.json").read_text(encoding="utf-8"))
    for row in manifest:
        if row["status"] not in ("ok", "skip") or not row["file"]:
            continue
        pdf_path = PDF_DIR / row["file"]
        if not pdf_path.exists():
            print("missing", pdf_path)
            continue
        s = slug(row["doi"])
        (TEXT_DIR / "img").mkdir(exist_ok=True)
        pages = convert(pdf_path, TEXT_DIR / "img" / s)
        (TEXT_DIR / f"{s}.json").write_text(json.dumps(
            {"doi": row["doi"], "file": row["file"], "pages": pages}, ensure_ascii=False), encoding="utf-8")
        txt = render_txt(pages)
        (TEXT_DIR / f"{s}.txt").write_text(txt, encoding="utf-8")
        print(f"{row['doi']:40s} pages={len(pages):3d} tables={sum(len(p['tables']) for p in pages):3d} chars={len(txt)}")


if __name__ == "__main__":
    main()
