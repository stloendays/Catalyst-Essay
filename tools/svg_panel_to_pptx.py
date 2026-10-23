"""One panel of a matplotlib composite SVG as an editable PowerPoint slide: text as text boxes (with sub- and
superscripts), lines, outlines, arrows and filled shapes as freeforms, embedded renders as pictures, in the SVG's own
z-order and at 1:1 scale.

The panel is the set of SVG primitives whose bounding-box centre lies below and to the right of the panel's letter
(style.letter: bold 9-px single character), and not below and to the right of a later letter (the rule of
tools/make_figures_pptx.py). Curves are flattened to short line segments.

    python tools/svg_panel_to_pptx.py <figure.svg> <panel letter> <out.pptx>
"""
import base64
import io
import math
import re
import sys
from pathlib import Path

import numpy as np
from lxml import etree
from PIL import Image, ImageFont
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.dml import MSO_LINE_DASH_STYLE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Pt

SVG = "{http://www.w3.org/2000/svg}"
XLINK = "{http://www.w3.org/1999/xlink}href"
EMU_PT = 12700
MARGIN = 3.0                     # pt around the panel on the slide
FONT_DIR = Path("C:/Windows/Fonts")


# ---------------------------------------------------------------- geometry
def mat_mul(a, b):
    return [a[0] * b[0] + a[2] * b[1], a[1] * b[0] + a[3] * b[1], a[0] * b[2] + a[2] * b[3],
            a[1] * b[2] + a[3] * b[3], a[0] * b[4] + a[2] * b[5] + a[4], a[1] * b[4] + a[3] * b[5] + a[5]]


def parse_transform(s):
    m = [1, 0, 0, 1, 0, 0]
    for name, args in re.findall(r"(\w+)\(([^)]*)\)", s or ""):
        v = [float(x) for x in re.split(r"[\s,]+", args.strip()) if x]
        if name == "translate":
            t = [1, 0, 0, 1, v[0], v[1] if len(v) > 1 else 0]
        elif name == "scale":
            t = [v[0], 0, 0, v[1] if len(v) > 1 else v[0], 0, 0]
        elif name == "rotate":
            a = math.radians(v[0])
            c, s_ = math.cos(a), math.sin(a)
            t = [c, s_, -s_, c, 0, 0]
            if len(v) == 3:
                t = mat_mul(mat_mul([1, 0, 0, 1, v[1], v[2]], t), [1, 0, 0, 1, -v[1], -v[2]])
        elif name == "matrix":
            t = v
        else:
            continue
        m = mat_mul(m, t)
    return m


def apply(m, x, y):
    return m[0] * x + m[2] * y + m[4], m[1] * x + m[3] * y + m[5]


def path_polys(d, m, steps=10):
    """List of (points, closed) sub-paths, curves flattened."""
    toks = re.findall(r"[MLCQZz]|-?[\d.]+(?:e-?\d+)?", d)
    polys, cur, i, pos, start = [], [], 0, (0.0, 0.0), (0.0, 0.0)
    num = lambda k: float(toks[k])  # noqa: E731
    while i < len(toks):
        c = toks[i]
        if c == "M":
            if cur:
                polys.append((cur, False))
            pos = (num(i + 1), num(i + 2)); start = pos; cur = [pos]; i += 3
        elif c == "L":
            pos = (num(i + 1), num(i + 2)); cur.append(pos); i += 3
        elif c == "C":
            p0, p1, p2, p3 = pos, (num(i + 1), num(i + 2)), (num(i + 3), num(i + 4)), (num(i + 5), num(i + 6))
            for t in np.linspace(0, 1, steps + 1)[1:]:
                cur.append(tuple((1 - t) ** 3 * np.array(p0) + 3 * (1 - t) ** 2 * t * np.array(p1)
                                 + 3 * (1 - t) * t ** 2 * np.array(p2) + t ** 3 * np.array(p3)))
            pos = p3; i += 7
        elif c == "Q":
            p0, p1, p2 = pos, (num(i + 1), num(i + 2)), (num(i + 3), num(i + 4))
            for t in np.linspace(0, 1, steps + 1)[1:]:
                cur.append(tuple((1 - t) ** 2 * np.array(p0) + 2 * (1 - t) * t * np.array(p1) + t ** 2 * np.array(p2)))
            pos = p2; i += 5
        elif c in "Zz":
            if cur:
                polys.append((cur, True))
            cur = []; pos = start; i += 1
        else:
            i += 1
    if cur:
        polys.append((cur, False))
    return [([apply(m, x, y) for x, y in pts], closed) for pts, closed in polys if len(pts) >= 2]


def style_of(el, inherited=None):
    st = dict(inherited or {})
    for part in (el.get("style") or "").split(";"):
        if ":" in part:
            k, v = part.split(":", 1)
            st[k.strip()] = v.strip()
    for k in ("fill", "stroke", "stroke-width", "opacity", "fill-opacity", "stroke-opacity", "stroke-dasharray"):
        if el.get(k) is not None:
            st[k] = el.get(k)
    return st


def colour(v):
    if not v or v == "none":
        return None
    v = v.strip()
    if v.startswith("#") and len(v) == 7:
        return RGBColor.from_string(v[1:].upper())
    if v.startswith("#") and len(v) == 4:
        return RGBColor.from_string("".join(ch * 2 for ch in v[1:]).upper())
    named = {"black": "000000", "white": "FFFFFF", "red": "FF0000", "blue": "0000FF", "green": "008000"}
    return RGBColor.from_string(named.get(v, "000000"))


# ---------------------------------------------------------------- collect primitives
def collect(root):
    defs = {el.get("id"): el for el in root.iter(SVG + "path") if el.get("id")}
    prims = []

    def walk(el, m, inh):
        if not isinstance(el.tag, str):              # comments and processing instructions
            return
        tag = el.tag.replace(SVG, "")
        if tag in ("defs", "clipPath", "metadata", "style"):
            return
        m2 = mat_mul(m, parse_transform(el.get("transform"))) if el.get("transform") else m
        st = style_of(el, inh) if tag == "g" else inh
        if tag == "path":
            prims.append(("path", path_polys(el.get("d", ""), m2), style_of(el, inh), el))
        elif tag == "use":
            ref = defs.get((el.get(XLINK) or "")[1:])
            if ref is not None:
                mu = mat_mul(m2, [1, 0, 0, 1, float(el.get("x", 0)), float(el.get("y", 0))])
                prims.append(("path", path_polys(ref.get("d", ""), mu), style_of(el, style_of(ref, inh)), el))
        elif tag == "text":
            prims.append(("text", m2, style_of(el, inh), el))
            return
        elif tag == "image":
            prims.append(("image", m2, None, el))
        for ch in el:
            if tag != "text":
                walk(ch, m2, st)

    walk(root, [1, 0, 0, 1, 0, 0], {})
    return prims


def text_runs(el, st):
    """[(text, size, weight, italic, colour, dx, dy)] in the text's own coordinates."""
    runs = []
    if len(el) == 0:
        runs.append((el.text or "", st, float(el.get("x", 0)), float(el.get("y", 0))))
    else:
        if (el.text or "").strip():
            runs.append((el.text, st, 0.0, 0.0))
        for ts in el:
            if ts.tag == SVG + "tspan":
                runs.append((ts.text or "", style_of(ts, st), float(ts.get("x", 0)), float(ts.get("y", 0))))
    runs.sort(key=lambda r: r[2])                     # mathtext writes sub/superscript spans after the base text
    out = []
    for txt, s, dx, dy in runs:
        size = float(re.match(r"[\d.]+", s.get("font-size", "7")).group())
        out.append((txt.replace("\u00a0", " "), size, "700" in s.get("font-weight", "") or "bold" in s.get("font-weight", ""),
                    "italic" in s.get("font-style", ""), s.get("fill", "#000000"), dx, dy, s.get("text-anchor", "start")))
    return out


_FONTS = {}


def text_width(txt, size, bold, italic):
    name = {(False, False): "arial.ttf", (True, False): "arialbd.ttf", (False, True): "ariali.ttf",
            (True, True): "arialbi.ttf"}[(bold, italic)]
    key = (name, size)
    if key not in _FONTS:
        _FONTS[key] = ImageFont.truetype(str(FONT_DIR / name), size=max(1, round(size * 40)))
    return _FONTS[key].getlength(txt) / 40.0


def bbox_of(p):
    kind = p[0]
    if kind == "path":
        pts = [q for poly, _ in p[1] for q in poly]
        if not pts:
            return None
        xs, ys = zip(*pts)
        return min(xs), min(ys), max(xs), max(ys)
    if kind == "image":
        el, m = p[3], p[1]
        x, y, w, h = (float(el.get(k, 0)) for k in ("x", "y", "width", "height"))
        c = [apply(m, *q) for q in ((x, y), (x + w, y), (x, y + h), (x + w, y + h))]
        xs, ys = zip(*c)
        return min(xs), min(ys), max(xs), max(ys)
    runs = text_runs(p[3], p[2])
    if not runs:
        return None
    x0, y0 = apply(p[1], runs[0][5], runs[0][6])
    w = sum(text_width(r[0], r[1], r[2], r[3]) for r in runs)
    size = max(r[1] for r in runs)
    anchor = runs[0][7]
    xl = x0 - (w / 2 if anchor == "middle" else w if anchor == "end" else 0)
    return xl, y0 - 0.8 * size, xl + w, y0 + 0.25 * size


# ---------------------------------------------------------------- panel selection
def letters(root):
    out = []
    for el in root.iter(SVG + "text"):
        st = el.get("style") or ""
        if "font-weight: 700" in st and "font-size: 9px" in st and len(el) == 0 and re.fullmatch(r"[a-z]", el.text or ""):
            out.append((el.text, float(el.get("x")), float(el.get("y")) - 9.0))
    return out


def owner(cx, cy, lets, tol=4.0):
    best, score = None, -1e18
    for ch, x, top in lets:
        if cy >= top - tol and cx >= x - tol and top * 1e4 + x > score:
            best, score = ch, top * 1e4 + x
    return best


# ---------------------------------------------------------------- write
def dash_of(st):
    d = st.get("stroke-dasharray")
    if not d or d == "none":
        return None
    v = [float(x) for x in re.split(r"[\s,]+", d.strip()) if x]
    lw = float(st.get("stroke-width", 1))
    on = v[0] / max(lw, 1e-6)
    return MSO_LINE_DASH_STYLE.ROUND_DOT if on < 1.5 else (MSO_LINE_DASH_STYLE.DASH if on < 4 else MSO_LINE_DASH_STYLE.LONG_DASH)


def set_alpha(fill_or_line_xml, alpha):
    for clr in fill_or_line_xml.iter(qn("a:srgbClr")):
        a = clr.makeelement(qn("a:alpha"), {"val": str(int(alpha * 100000))})
        clr.append(a)


def add_path(slide, polys, st, ox, oy, name):
    fill = colour(st.get("fill", "#000000"))
    stroke = colour(st.get("stroke"))
    if fill is None and stroke is None:
        return
    for pts, closed in polys:
        pts = [((x - ox) * EMU_PT, (y - oy) * EMU_PT) for x, y in pts]
        fb = slide.shapes.build_freeform(pts[0][0], pts[0][1], scale=1.0)
        fb.add_line_segments(pts[1:], close=closed)
        sh = fb.convert_to_shape()
        sh.name = name
        if fill is not None and (closed or len(pts) > 2):
            sh.fill.solid(); sh.fill.fore_color.rgb = fill
            op = float(st.get("fill-opacity", 1)) * float(st.get("opacity", 1))
            if op < 0.999:
                set_alpha(sh.fill._xPr, op)
        else:
            sh.fill.background()
        if stroke is not None:
            sh.line.color.rgb = stroke
            sh.line.width = Pt(float(st.get("stroke-width", 1)))
            ds = dash_of(st)
            if ds is not None:
                sh.line.dash_style = ds
            op = float(st.get("stroke-opacity", 1)) * float(st.get("opacity", 1))
            if op < 0.999:
                set_alpha(sh.line._get_or_add_ln(), op)
        else:
            sh.line.fill.background()
        sh.shadow.inherit = False


def add_image(slide, el, m, ox, oy, tmp):
    href = el.get(XLINK) or ""
    raw = base64.b64decode(href.split(",", 1)[1])
    im = Image.open(io.BytesIO(raw))
    if m[3] < 0:                                   # matplotlib writes images flipped with scale(1 -1)
        im = im.transpose(Image.FLIP_TOP_BOTTOM)
    x0, y0, x1, y1 = bbox_of(("image", m, None, el))
    f = tmp / f"img_{abs(hash(href)) % 10 ** 8}.png"
    im.save(f)
    pic = slide.shapes.add_picture(str(f), Emu(int((x0 - ox) * EMU_PT)), Emu(int((y0 - oy) * EMU_PT)),
                                   Emu(int((x1 - x0) * EMU_PT)), Emu(int((y1 - y0) * EMU_PT)))
    pic.name = "render"


def add_text(slide, el, m, st, ox, oy):
    runs = [r for r in text_runs(el, st) if r[0] != ""]
    if not runs:
        return
    # restore word spaces that the SVG expresses only as a gap between span positions
    fixed = [runs[0]]
    for r in runs[1:]:
        prev = fixed[-1]
        end = prev[5] + text_width(prev[0], prev[1], prev[2], prev[3])
        if r[5] - end > 0.2 * r[1] and not r[0].startswith(" ") and not prev[0].endswith(" "):
            r = (" " + r[0],) + r[1:]
        fixed.append(r)
    runs = fixed
    angle = -math.degrees(math.atan2(m[1], m[0]))
    base_dy = runs[0][6]
    size = max(r[1] for r in runs)
    widths = [text_width(r[0], r[1], r[2], r[3]) for r in runs]
    w = sum(widths)
    anchor = runs[0][7]
    # baseline start point in figure coordinates (unrotated layout, then the box is rotated about its centre)
    bx, by = apply(m, runs[0][5], base_dy)
    left = -(w / 2 if anchor == "middle" else w if anchor == "end" else 0)
    asc = 0.905 * size
    hbox = 1.2 * size
    # centre of the text box in the text's own frame, then mapped
    cx_l, cy_l = left + w / 2, -asc + hbox / 2
    ca, sa = m[0] / math.hypot(m[0], m[1]), m[1] / math.hypot(m[0], m[1])
    cx = bx + ca * cx_l - sa * cy_l
    cy = by + sa * cx_l + ca * cy_l
    wpad = w * 1.04 + 1.0
    tb = slide.shapes.add_textbox(Emu(int((cx - wpad / 2 - ox) * EMU_PT)), Emu(int((cy - hbox / 2 - oy) * EMU_PT)),
                                  Emu(int(wpad * EMU_PT)), Emu(int(hbox * EMU_PT)))
    tb.name = "text: " + "".join(r[0] for r in runs)[:30]
    tf = tb.text_frame
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.word_wrap = False
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = {"middle": PP_ALIGN.CENTER, "end": PP_ALIGN.RIGHT}.get(anchor, PP_ALIGN.LEFT)
    for txt, sz, bold, ital, fill, dx, dy, _ in runs:
        r = p.add_run()
        r.text = txt
        f = r.font
        f.size, f.bold, f.italic, f.name = Pt(sz), bold, ital, "Arial"
        c = colour(fill)
        if c is not None:
            f.color.rgb = c
        shift = dy - base_dy
        if abs(shift) > 0.3:
            r._r.get_or_add_rPr().set("baseline", str(int(-shift / size * 100000)))
    if abs(angle) > 0.5:
        tb.rotation = -angle


def main():
    svg, panel, out = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3])
    root = etree.parse(str(svg)).getroot()
    lets = letters(root)
    prims = collect(root)
    keep = []
    for p in prims:
        b = bbox_of(p)
        if b is None:
            continue
        if p[0] == "path":
            st = p[2]
            area = (b[2] - b[0]) * (b[3] - b[1])
            if (st.get("fill", "").lower() in ("#ffffff", "white") and colour(st.get("stroke")) is None
                    and area > 20000):
                continue                               # figure or axes background
        cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
        if owner(cx, cy, lets) == panel:
            keep.append((p, b))
    xs0 = min(b[0] for _, b in keep) - MARGIN
    ys0 = min(b[1] for _, b in keep) - MARGIN
    xs1 = max(b[2] for _, b in keep) + MARGIN
    ys1 = max(b[3] for _, b in keep) + MARGIN
    prs = Presentation()
    prs.slide_width, prs.slide_height = Emu(int((xs1 - xs0) * EMU_PT)), Emu(int((ys1 - ys0) * EMU_PT))
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    tmp = out.parent / (out.stem + "_assets")
    tmp.mkdir(exist_ok=True)
    counts = {}
    for p, _ in keep:
        kind = p[0]
        counts[kind] = counts.get(kind, 0) + 1
        if kind == "path":
            add_path(slide, p[1], p[2], xs0, ys0, p[3].getparent().get("id") or "shape")
        elif kind == "image":
            add_image(slide, p[3], p[1], xs0, ys0, tmp)
        else:
            add_text(slide, p[3], p[1], p[2], xs0, ys0)
    prs.save(out)
    print(f"{svg.name} panel {panel}: {counts}, {(xs1 - xs0) / 72 * 25.4:.1f} x {(ys1 - ys0) / 72 * 25.4:.1f} mm -> {out}")


if __name__ == "__main__":
    main()
