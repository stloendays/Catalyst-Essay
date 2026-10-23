"""All main and Extended Data figures in one PPTX: one figure per slide, each panel a separate picture at its
original position (1:1 scale, 600 dpi crops), so panels can be moved individually.

Panels are found from the panel letters of the figure's SVG (style.letter: bold 9-pt single characters, kept as
<text>): every ink pixel of the 600-dpi render goes to the panel whose letter lies above and to the left of it (the
lowest such letter row, then the rightmost letter), with a small tolerance. Each panel is saved as an RGBA crop that is
transparent outside its own pixels, so crops never duplicate content when moved. A preview PNG per figure colours the
panels.

    python make_figures_pptx.py <repo>  -> Figures_NCE_2026-10-23.pptx, crops/, previews/
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from pptx import Presentation
from pptx.util import Mm, Pt

REPO = Path(sys.argv[1])
HERE = Path(__file__).resolve().parent
DPI = 600.0
PX_MM = DPI / 25.4
GUTTER_MM = 1.6            # white band that separates two pieces
MIN_PIECE_MM2 = 60.0        # smaller pieces are merged into their nearest neighbour
SLIDE_W, SLIDE_H = 210.0, 215.0
ORIGIN = (13.5, 22.0)       # figure top-left on the slide, mm

FIGS = [("Figure 1", "composite/fig1/Fig1.png"), ("Figure 2", "composite/fig_field/FigField.png"),
        ("Figure 3", "composite/fig4/Fig4.png"), ("Figure 4", "composite/fig2/Fig2.png"),
        ("Figure 5", "composite/fig_frontier/FigFrontier.png"), ("Figure 6", "composite/fig3/Fig3.png")]
FIGS += [(f"Extended Data Fig. {n}", p) for n, p in sorted(
    ((int(f.name.split("EDFig")[1].split("_")[0]), f"extended_data/{f.name}")
     for f in (REPO / "figures/extended_data").glob("EDFig*.png")))]


def ink(a):
    return a < 250


def letters(svg):
    """(char, x_pt, top_pt) of the panel letters, from the SVG (bold 9-px single-character <text>)."""
    import re
    t = svg.read_text(encoding="utf-8")
    vb = [float(v) for v in re.search(r'viewBox="([^"]+)"', t).group(1).split()]
    out = []
    for m in re.finditer(r'<text style="([^"]*)" x="([\d.]+)" y="([\d.]+)"[^>]*>([a-z])</text>', t):
        st = m.group(1)
        if "font-weight: 700" in st and "font-size: 9px" in st:
            out.append((m.group(4), float(m.group(2)), float(m.group(3)) - 9.0))
    return out, vb


def assign(mask, lets, vb, shape):
    """Panel index per ink pixel (-1 for background)."""
    H, W = shape
    sx, sy = W / vb[2], H / vb[3]
    tol = 4.0
    ys, xs = np.mgrid[0:H, 0:W]
    best = np.full(shape, -1, dtype=int)
    score = np.full(shape, -np.inf)
    for k, (_, x, top) in enumerate(lets):
        ok = (ys >= (top - tol) * sy) & (xs >= (x - tol) * sx)
        sc = top * 1e4 + x
        upd = ok & (sc > score)
        best[upd] = k
        score[upd] = sc
    # pixels above or left of every letter go to the nearest letter
    rest = best < 0
    if rest.any() and lets:
        d = np.stack([((ys - top * sy) ** 2 + (xs - x * sx) ** 2) for _, x, top in lets])
        best[rest] = np.argmin(d, axis=0)[rest]
    best[~mask] = -1
    return best


def main():
    crops, prev = HERE / "crops", HERE / "previews"
    crops.mkdir(exist_ok=True); prev.mkdir(exist_ok=True)
    prs = Presentation()
    prs.slide_width, prs.slide_height = Mm(SLIDE_W), Mm(SLIDE_H)
    blank = prs.slide_layouts[6]
    report = []
    for title, rel in FIGS:
        im = Image.open(REPO / "figures" / rel).convert("RGB")
        a = np.asarray(im)
        mask = ink(a.min(axis=2))
        lets, vb = letters((REPO / "figures" / rel).with_suffix(".svg"))
        lab = assign(mask, lets, vb, mask.shape) if lets else np.where(mask, 0, -1)
        names = [c for c, _, _ in lets] or ["whole"]
        slide = prs.slides.add_slide(blank)
        tb = slide.shapes.add_textbox(Mm(ORIGIN[0]), Mm(6), Mm(SLIDE_W - 2 * ORIGIN[0]), Mm(10))
        p = tb.text_frame.paragraphs[0]; p.text = f"{title}  ({rel.split('/')[-1]})"
        p.runs[0].font.size, p.runs[0].font.bold = Pt(14), True
        fr = slide.shapes.add_shape(1, Mm(ORIGIN[0]), Mm(ORIGIN[1]), Mm(a.shape[1] / PX_MM), Mm(a.shape[0] / PX_MM))
        fr.fill.background(); fr.line.color.rgb = __import__("pptx.dml.color", fromlist=["RGBColor"]).RGBColor(0xC8, 0xC8, 0xC8)
        fr.line.width = Pt(0.5); fr.name = "original figure frame (183 mm)"
        stem = title.replace(" ", "_").replace(".", "")
        rgba = np.dstack([a, np.full(mask.shape, 255, np.uint8)])
        colours = np.array([(230, 75, 53), (77, 187, 213), (0, 160, 135), (60, 84, 136), (243, 155, 127),
                            (132, 145, 180), (145, 209, 194), (220, 0, 0), (126, 97, 72), (176, 156, 133)])
        prevw = np.full(a.shape, 255, np.uint8)
        for k, name in enumerate(names):
            sel = lab == k
            if not sel.any():
                continue
            yy, xx = np.where(sel)
            y0, y1, x0, x1 = yy.min(), yy.max() + 1, xx.min(), xx.max() + 1
            piece = rgba[y0:y1, x0:x1].copy()
            piece[..., 3] = np.where(sel[y0:y1, x0:x1], 255, 0)
            f = crops / f"{stem}_{name}.png"
            Image.fromarray(piece, "RGBA").save(f, dpi=(DPI, DPI))
            pic = slide.shapes.add_picture(str(f), Mm(ORIGIN[0] + x0 / PX_MM), Mm(ORIGIN[1] + y0 / PX_MM),
                                           Mm((x1 - x0) / PX_MM), Mm((y1 - y0) / PX_MM))
            pic.name = f"{title} panel {name}"
            prevw[sel] = colours[k % len(colours)]
        Image.fromarray(prevw).resize((a.shape[1] // 4, a.shape[0] // 4)).save(prev / f"{stem}.png")
        report.append(f"{title}: panels {' '.join(names)}")
        continue
        report.append(f"{title}: {len(boxes)} pieces")
    out = HERE / "Figures_NCE_2026-10-23.pptx"
    prs.save(out)
    print("\n".join(report)); print("wrote", out)


if __name__ == "__main__":
    main()
