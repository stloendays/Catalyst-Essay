"""OCR / layout parsing with Docling (github.com/docling-project/docling): every PDF in pdf/<rxn>/ ->
ocr/<rxn>/<stem>.md (reading-order text, TableFormer tables as Markdown, page markers) + figure crops
ocr/<rxn>/<stem>_figs/fig<k>_p<page>.png with their captions in <stem>_figs.json."""
import json, sys, time
from pathlib import Path
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode, AcceleratorOptions, AcceleratorDevice
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling_core.types.doc import PictureItem, TableItem
rxn = sys.argv[1]
import os
src = Path(os.environ.get("DOCLING_SRC", f"pdf/{rxn}")); dst = Path(os.environ.get("DOCLING_DST", f"ocr/{rxn}")); dst.mkdir(parents=True, exist_ok=True)
opt = PdfPipelineOptions(do_ocr=True, do_table_structure=True, generate_picture_images=True, images_scale=float(sys.argv[2]) if len(sys.argv) > 2 else 4.0)
opt.table_structure_options.mode = TableFormerMode.ACCURATE
opt.table_structure_options.do_cell_matching = True
opt.accelerator_options = AcceleratorOptions(device=AcceleratorDevice.CUDA, num_threads=4)
conv = DocumentConverter(format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=opt)})
log = []
for pdf in sorted(src.glob("*.pdf")):
    out_md = dst / (pdf.stem[:60] + ".md")
    if out_md.exists() and len(sys.argv) < 4: continue
    t0 = time.time()
    doc = conv.convert(str(pdf)).document
    parts, figs, ntab, k = [], [], 0, 0
    page = None
    figdir = dst / (pdf.stem[:60] + "_figs"); figdir.mkdir(exist_ok=True)
    for item, _lvl in doc.iterate_items():
        p = item.prov[0].page_no if getattr(item, "prov", None) else page
        if p != page:
            page = p; parts.append(f"\n=== PAGE {page} ===\n")
        if isinstance(item, TableItem):
            ntab += 1
            cap = item.caption_text(doc)
            parts.append(f"\n[TABLE {ntab}] {cap}\n" + item.export_to_markdown(doc) + "\n")
        elif isinstance(item, PictureItem):
            k += 1
            cap = item.caption_text(doc)
            img = item.get_image(doc)
            fn = figdir / f"fig{k}_p{page}.png"
            if img is not None: img.save(fn)
            figs.append(dict(file=fn.name, page=page, caption=cap))
            parts.append(f"\n[PICTURE {k}, page {page}] {cap}\n")
        elif hasattr(item, "text") and item.text:
            parts.append(item.text)
    out_md.write_text("\n".join(parts), encoding="utf-8")
    (dst / (pdf.stem[:60] + "_figs.json")).write_text(json.dumps(figs, indent=1, ensure_ascii=False), encoding="utf-8")
    log.append(dict(pdf=pdf.name, pages=doc.num_pages(), tables=ntab, pictures=k, seconds=round(time.time() - t0, 1)))
    print(log[-1], flush=True)
lp = dst / "ocr_log.json"
old = json.loads(lp.read_text()) if lp.exists() else []
lp.write_text(json.dumps(old + log, indent=1), encoding="utf-8")
