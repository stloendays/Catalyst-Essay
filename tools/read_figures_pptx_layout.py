"""Read panel positions back from an edited figures PPTX (made by tools/make_figures_pptx.py) and report, per figure and
panel, how far each panel moved or was rescaled relative to the original layout, in millimetres of the 183-mm figure.

    python tools/read_figures_pptx_layout.py <edited.pptx> [<original.pptx>]  -> prints a table, writes <edited>_layout.csv

Without an original, the reference is the generator's own placement (ORIGIN offset), so an untouched file reports zero.
Each row: figure, panel, x_mm, y_mm, w_mm, h_mm (figure coordinates, top-left origin), dx, dy, scale_w, scale_h.
"""
import csv
import sys
from pathlib import Path

from pptx import Presentation

EMU_MM = 36000.0
ORIGIN = (13.5, 22.0)            # must match make_figures_pptx.py


def panels(path):
    out = {}
    for slide in Presentation(path).slides:
        for sh in slide.shapes:
            if " panel " in (sh.name or ""):
                fig, pan = sh.name.split(" panel ")
                out[(fig, pan)] = (sh.left / EMU_MM - ORIGIN[0], sh.top / EMU_MM - ORIGIN[1],
                                   sh.width / EMU_MM, sh.height / EMU_MM)
    return out


def main():
    edited = Path(sys.argv[1])
    new = panels(edited)
    ref = panels(Path(sys.argv[2])) if len(sys.argv) > 2 else None
    rows = []
    for key, (x, y, w, h) in new.items():
        if ref is not None and key in ref:
            x0, y0, w0, h0 = ref[key]
        else:
            x0, y0, w0, h0 = x, y, w, h
        rows.append(dict(figure=key[0], panel=key[1], x_mm=round(x, 2), y_mm=round(y, 2), w_mm=round(w, 2),
                         h_mm=round(h, 2), dx_mm=round(x - x0, 2), dy_mm=round(y - y0, 2),
                         scale_w=round(w / w0, 4), scale_h=round(h / h0, 4)))
    out = edited.with_name(edited.stem + "_layout.csv")
    with out.open("w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0]))
        wr.writeheader()
        wr.writerows(rows)
    moved = [r for r in rows if abs(r["dx_mm"]) > 0.05 or abs(r["dy_mm"]) > 0.05
             or abs(r["scale_w"] - 1) > 1e-3 or abs(r["scale_h"] - 1) > 1e-3]
    print(f"{len(rows)} panels, {len(moved)} moved or rescaled -> {out}")
    for r in moved:
        print(f"  {r['figure']:24s} {r['panel']}: dx {r['dx_mm']:+.1f} mm, dy {r['dy_mm']:+.1f} mm, "
              f"scale {r['scale_w']:.3f} x {r['scale_h']:.3f}")


if __name__ == "__main__":
    main()
