"""Compose the two cleaned Origin panel SVGs into one vector figure.

Each panel is cropped to its ink bounding box (measured on its own rasterised
PNG, then mapped into the SVG's user units), scaled to a common height and
nested inside a parent <svg> that carries the physical size. Element ids are
prefixed per panel so Origin's clip/mask ids cannot collide.

    python compose_svg.py F08_panel_a.svg F08_panel_a.png \
                          F08_panel_b.svg F08_panel_b.png  out.svg  [width_mm]
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from png_compose import png_read  # noqa: E402

import numpy as np  # noqa: E402

PAD_PX = 12          # same padding png_compose uses around the ink box
GAP = 0.05           # gap between panels, fraction of panel height
MARGIN = 0.03        # outer margin, fraction of panel height


def ink_box(png_path, thresh=245):
    img = png_read(png_path)
    mask = (img < thresh).any(axis=2)
    rows = np.where(mask.any(axis=1))[0]
    cols = np.where(mask.any(axis=0))[0]
    h, w = mask.shape
    top, bottom = max(0, rows[0] - PAD_PX), min(h, rows[-1] + 1 + PAD_PX)
    left, right = max(0, cols[0] - PAD_PX), min(w, cols[-1] + 1 + PAD_PX)
    return left, top, right, bottom, w, h


def panel(svg_path, png_path, prefix, namespaces):
    src = open(svg_path, encoding="utf-8").read()
    root = re.search(r"<svg\b[^>]*>", src)
    # Origin writes olab:* metadata attributes; their namespace has to survive the
    # nesting or the composite is not well-formed XML.
    for name, uri in re.findall(r'xmlns:(\w+)="([^"]+)"', root.group(0)):
        namespaces[name] = uri
    vb = [float(v) for v in re.split(r"[,\s]+", re.search(r'viewBox="([^"]+)"', root.group(0)).group(1).strip())]
    body = src[root.end():src.rfind("</svg>")]

    # Origin clips the plot area with a <mask> holding one opaque white rectangle.
    # PDF writers rasterise masked content, which flattens every curve into a bitmap;
    # a clipPath with the same rectangle is geometrically identical and stays vector.
    # Convert only that exact shape, so a real luminance mask is never rewritten.
    def mask_to_clip(m):
        inner = m.group(2).strip()
        if re.fullmatch(r'<rect\b[^>]*fill="white"[^>]*/>', inner):
            return '<clipPath id="%s">%s</clipPath>' % (m.group(1), inner.replace(' fill="white"', ""))
        print("warning: %s: mask %s is not a plain white rectangle; left as a mask" % (svg_path, m.group(1)))
        return m.group(0)
    body, n_masks = re.subn(r'<mask id="([^"]+)">(.*?)</mask>', mask_to_clip, body, flags=re.S)
    for mid in re.findall(r'<clipPath id="([^"]+)">', body):
        body = body.replace('mask="url(#%s)"' % mid, 'clip-path="url(#%s)"' % mid)

    # Keep ids unique across the two panels.
    body = re.sub(r'\bid="([^"]+)"', lambda m: 'id="%s%s"' % (prefix, m.group(1)), body)
    body = re.sub(r'url\(#([^)]+)\)', lambda m: "url(#%s%s)" % (prefix, m.group(1)), body)
    body = re.sub(r'(xlink:href|href)="#([^"]+)"', lambda m: '%s="#%s%s"' % (m.group(1), prefix, m.group(2)), body)

    left, top, right, bottom, pw, ph = ink_box(png_path)
    sx, sy = vb[2] / pw, vb[3] / ph           # PNG px -> SVG user units
    crop = (vb[0] + left * sx, vb[1] + top * sy, (right - left) * sx, (bottom - top) * sy)
    return body, crop, (right - left), (bottom - top)


def main():
    a_svg, a_png, b_svg, b_png, out = sys.argv[1:6]
    width_mm = float(sys.argv[6]) if len(sys.argv) > 6 else 183.0

    namespaces = {"xlink": "http://www.w3.org/1999/xlink"}
    a_body, a_crop, aw, ah = panel(a_svg, a_png, "pa_", namespaces)
    b_body, b_crop, bw, bh = panel(b_svg, b_png, "pb_", namespaces)
    ns_decl = " ".join('xmlns:%s="%s"' % kv for kv in sorted(namespaces.items()))

    H = float(max(ah, bh))
    aw_s, bw_s = aw * H / ah, bw * H / bh
    gap, margin = GAP * H, MARGIN * H
    W = aw_s + gap + bw_s + 2 * margin
    Ht = H + 2 * margin
    height_mm = width_mm * Ht / W

    def nested(x, w, crop, body):
        return ('<svg x="%.3f" y="%.3f" width="%.3f" height="%.3f" viewBox="%.3f %.3f %.3f %.3f" '
                'preserveAspectRatio="xMidYMid meet" overflow="hidden">%s</svg>'
                % (x, margin, w, H, crop[0], crop[1], crop[2], crop[3], body))

    doc = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<svg xmlns="http://www.w3.org/2000/svg" %s '
           'width="%.2fmm" height="%.2fmm" viewBox="0 0 %.3f %.3f">\n'
           '<rect x="0" y="0" width="%.3f" height="%.3f" fill="#FFFFFF"/>\n%s\n%s\n</svg>\n'
           % (ns_decl, width_mm, height_mm, W, Ht, W, Ht,
              nested(margin, aw_s, a_crop, a_body),
              nested(margin + aw_s + gap, bw_s, b_crop, b_body)))
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(doc)
    print("composed %s: %.1f x %.1f mm (viewBox %.0f x %.0f), panel widths %.0f%% / %.0f%%"
          % (out, width_mm, height_mm, W, Ht, 100 * aw_s / W, 100 * bw_s / W))


if __name__ == "__main__":
    main()
