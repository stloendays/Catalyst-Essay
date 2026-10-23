"""Hand adjustments of a finished matplotlib figure, kept as data and re-applied on every render.

Call `apply(fig, here, stem)` just before saving (Page.save does). It reads `<stem>.tweaks.json` next to the figure,
applies the adjustments, tags every adjustable artist with an SVG id, and writes `<stem>.tweak_keys.json`: the ids,
what each one is, its colours, the figure palette and how to re-render the figure (script, arguments, interpreter),
so the browser editor (tools/figure_tweak.py) can find and rebuild any figure that went through here.

Keys are built from the axes (position in mm), the kind and, for text, the string; they are taken after a layout
draw and before anything changes, so they stay valid after an adjustment.

Adjustable, per kind (lengths in mm; size, scale and lw are factors; colours are hex):
    figure      background, colors {old: new} over the whole figure
    axes        dx_mm, dy_mm, dw_mm, dh_mm (top-left fixed), background, background_alpha, lw (frame and ticks),
                colors, visible
    text        texts, annotation labels, titles, letters: dx_mm, dy_mm, size, text, weight, style, rotation (deg),
                ha (left/center/right), colors, alpha, visible
                (an annotation's leader line keeps its data end and follows the label)
    axislabel   axis titles: as text
    ticks       the tick or category labels of one axis: dx_mm (y) / dy_mm (x), size, weight, rotation,
                rename {old: new}, colors, visible
    legend      dx_mm, dy_mm, size, weight, rename, colors, visible
    added       "fig/added/<id>": {"add": {...}} plus the usual settings: an item the author inserted in the editor,
                in mm from the figure's bottom-left corner. add.type is
                  text     x_mm, y_mm (baseline-left), text, size_pt, color
                  arrow    x0_mm, y0_mm, x1_mm, y1_mm, head ("-|>", "->", "<|-|>", "-"), head_size, lw, ls, color
                  line     as arrow, head "-"
                  bracket  x0_mm, x1_mm, y_mm (the bar), h_mm (the legs), text ("*", "n.s." ...), size_pt, lw, color
                  box      x_mm, y_mm (bottom-left), w_mm, h_mm, radius_mm, fill, lw, ls, color
    scatter     scale (marker area), lw, alpha, colors, visible; positions are data and never move
    line        lw, alpha, colors, visible
    patch       bars, boxes, shapes: lw, alpha, colors, visible
    collection  error bars, bands and other collections: lw, alpha, colors, visible
    image       visible
"""
import hashlib
import json
import os
import sys
from collections import Counter

from matplotlib.axis import Axis
from matplotlib.collections import Collection, PathCollection
from matplotlib.colors import to_hex, to_rgba
from matplotlib.figure import Figure
from matplotlib.legend import Legend
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Patch
from matplotlib.text import Annotation, Text
from matplotlib.ticker import Formatter
from matplotlib.transforms import Affine2D, Bbox, ScaledTranslation

MM = 1 / 25.4
PT_PER_MM = 72 * MM


# ---- colours -------------------------------------------------------------------------------------------------------

def _hex(c):
    try:
        r = to_rgba(c)
    except (ValueError, TypeError):
        return None
    return None if r[3] == 0 else to_hex(r, keep_alpha=False).lower()


def _swap(c, m):
    h = _hex(c)
    return to_rgba(m[h], to_rgba(c)[3]) if h in m else c


def _swap_rows(arr, m):
    if arr is None or len(arr) == 0:
        return arr
    out = arr.copy()
    for i, row in enumerate(arr):
        out[i] = _swap(tuple(row), m)
    return out


def _walk(a):
    """The artist and everything drawn as part of it, for recolouring and colour listing."""
    if isinstance(a, Figure):
        yield a.patch
        for x in list(a.texts) + list(a.legends) + list(a.axes) + list(a.artists):
            yield from _walk(x)
    elif hasattr(a, "get_children") and not isinstance(a, (Text, Line2D, Patch, Collection)):
        if isinstance(a, Axis):
            ticks = a.get_major_ticks() + a.get_minor_ticks()
            kids = [a.label] + [p for t in ticks for p in (t.tick1line, t.tick2line, t.label1, t.label2)]
        elif isinstance(a, Legend):
            kids = list(a.get_texts()) + list(a.legend_handles) + [a.get_frame()]
        else:
            kids = a.get_children()
        for k in kids:
            if k is not None:
                yield from _walk(k)
    else:
        yield a
        if isinstance(a, Text) and a.get_bbox_patch() is not None:
            yield a.get_bbox_patch()
        if isinstance(a, Annotation) and a.arrow_patch is not None:
            yield a.arrow_patch


def _colors_of(a):
    out = []
    for x in _walk(a):
        if isinstance(x, Text):
            cs = [x.get_color()] if x.get_text().strip() else []
        elif isinstance(x, Line2D):
            cs = [x.get_color(), x.get_markerfacecolor(), x.get_markeredgecolor()] if x.get_marker() not in (
                None, "None", "", " ") else [x.get_color()]
        elif isinstance(x, Patch):
            cs = [x.get_facecolor(), x.get_edgecolor()]
        elif isinstance(x, Collection):
            cs = [tuple(r) for r in x.get_facecolors()] + [tuple(r) for r in x.get_edgecolors()]
        else:
            cs = []
        out += [h for h in map(_hex, cs) if h]
    return out


def _recolor(a, m):
    for x in _walk(a):
        if isinstance(x, Text):
            x.set_color(_swap(x.get_color(), m))
        elif isinstance(x, Line2D):
            x.set_color(_swap(x.get_color(), m))
            x.set_markerfacecolor(_swap(x.get_markerfacecolor(), m))
            x.set_markeredgecolor(_swap(x.get_markeredgecolor(), m))
        elif isinstance(x, Patch):
            x.set_facecolor(_swap(x.get_facecolor(), m))
            x.set_edgecolor(_swap(x.get_edgecolor(), m))
        elif isinstance(x, Collection):
            fc, ec = x.get_facecolors(), x.get_edgecolors()
            if len(fc):
                x.set_facecolor(_swap_rows(fc, m))
            if len(ec):
                x.set_edgecolor(_swap_rows(ec, m))


def _scale_lw(a, f):
    for x in _walk(a):
        if isinstance(x, (Line2D, Patch)):
            x.set_linewidth(x.get_linewidth() * f)
        elif isinstance(x, Collection):
            x.set_linewidths(x.get_linewidths() * f)


# ---- what can be adjusted ------------------------------------------------------------------------------------------

def _axkeys(fig):
    W, H = fig.get_size_inches() / MM
    seen, out = Counter(), {}
    for ax in fig.axes:
        x0, y0, w, h = ax.get_position(original=True).bounds
        k = "ax@%.0f,%.0f,%.0f,%.0f" % (x0 * W, y0 * H, w * W, h * H)
        seen[k] += 1
        out[ax] = k if seen[k] == 1 else "%s#%d" % (k, seen[k])      # twin axes share a position
    return out


def _panel_letters(fig, axkeys):
    """For each axes, the nearest single-letter figure text above-left of it (the panel letter), if any."""
    W, H = fig.get_size_inches() / MM
    letters = [(t.get_text(), t.get_position()) for t in fig.texts
               if len(t.get_text().strip()) == 1 and t.get_text().strip().isalpha()]
    out = {}
    for ax in axkeys:
        x0, y0, w, h = ax.get_position(original=True).bounds
        top, left = (y0 + h) * H, x0 * W
        best = None
        for s, (x, y) in letters:
            x, y = x * W, y * H
            if x <= left + 8 and y >= top - 8:
                d = (left - x) ** 2 + (y - top) ** 2
                if best is None or d < best[0]:
                    best = (d, s)
        if best:
            out[ax] = best[1]
    return out


def _drawn_tick_labels(axis):
    try:
        ticks = axis._update_ticks()                       # the ticks inside the view, as drawn
    except Exception:
        ticks = axis.get_major_ticks()
    out = []
    for t in ticks:
        for lab, side in ((t.label1, 1), (t.label2, 2)):
            if lab.get_visible() and lab.get_text().strip():
                out.append((lab, side))
    return out


def _name(a):
    lab = a.get_label() if hasattr(a, "get_label") else ""
    return lab if lab and not lab.startswith("_") else ""


def _items(fig):
    items = [dict(key="fig/figure", kind="figure", artist=fig)]
    for key, (shape, parts) in getattr(fig, "_tw_added", {}).items():
        if shape == "text":
            items.append(dict(key=key, kind="text", artist=parts[0], added=True))
        else:
            items.append(dict(key=key, kind="shape", artist=parts[0], parts=parts, shape=shape, added=True))

    def texts_of(owner, texts, kind):
        seen = Counter()
        for t in texts:
            s = t.get_text()
            if not s.strip() or not t.get_visible() or hasattr(t, "_tw_key"):
                continue
            seen[s] += 1
            items.append(dict(key="%s/text/%s%s" % (owner, s, "" if seen[s] == 1 else "#%d" % seen[s]), kind=kind,
                              artist=t))

    def legends_of(owner, legs):
        for i, lg in enumerate(legs):
            items.append(dict(key="%s/legend/%d" % (owner, i), kind="legend", artist=lg,
                              members=[t for t in lg.get_texts() if t.get_text().strip()]))

    texts_of("fig", fig.texts, "text")
    legends_of("fig", fig.legends)
    axk = _axkeys(fig)
    panels = _panel_letters(fig, axk)
    for ax, ak in axk.items():
        items.append(dict(key=ak + "/axes", kind="axes", artist=ax, panel=panels.get(ax, "")))
        texts_of(ak, ax.texts, "text")
        texts_of(ak, [ax.xaxis.label, ax.yaxis.label], "axislabel")
        for name, axis in (("x", ax.xaxis), ("y", ax.yaxis)):
            labs = _drawn_tick_labels(axis) if axis.get_visible() and ax.axison else []
            if labs:
                items.append(dict(key="%s/%sticks" % (ak, name), kind="ticks", artist=axis, axis=name,
                                  side=labs[0][1], members=[lab for lab, _ in labs]))
        legends_of(ak, [ax.legend_] if ax.legend_ is not None else [])
        for i, c in enumerate(x for x in ax.collections if isinstance(x, PathCollection) and len(x.get_offsets())):
            items.append(dict(key="%s/scatter/%d" % (ak, i), kind="scatter", artist=c))
        for i, c in enumerate(x for x in ax.collections if not isinstance(x, PathCollection)):
            items.append(dict(key="%s/collection/%d" % (ak, i), kind="collection", artist=c))
        for i, ln in enumerate(ax.lines):
            items.append(dict(key="%s/line/%d" % (ak, i), kind="line", artist=ln))
        for i, p in enumerate(ax.patches):
            items.append(dict(key="%s/patch/%d" % (ak, i), kind="patch", artist=p))
        for i, im in enumerate(ax.images):
            items.append(dict(key="%s/image/%d" % (ak, i), kind="image", artist=im))
    return items


def _gid(key):
    return "tw_" + hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]


def _font_of(it):
    """The text whose font stands for the item (the first label of a tick column or legend)."""
    k = it["kind"]
    if k in ("text", "axislabel"):
        return it["artist"]
    if k in ("ticks", "legend") and it.get("members"):
        return it["members"][0]
    if k == "shape" and it["shape"] == "bracket":
        return it["parts"][1]
    return None


def _weight(w):
    if isinstance(w, (int, float)):
        return "bold" if w >= 600 else "normal"
    return "bold" if str(w).lower() in ("bold", "heavy", "extra bold", "black", "semibold", "demibold", "demi") \
        else "normal"


def _role(it):
    """What a text is, for the cross-figure consistency check."""
    if it.get("added"):
        return "added"
    if it["kind"] == "text":
        if it["key"].startswith("fig/"):
            s = it["artist"].get_text().strip()
            return "letter" if len(s) == 1 and s.isalpha() else "title"
        return "text"
    return it["kind"]                                  # axislabel, ticks, legend


# ---- texts and shapes inserted in the editor -----------------------------------------------------------------------

def _mm_transform(fig):
    """Millimetres from the figure's bottom-left corner."""
    return Affine2D().scale(MM) + fig.dpi_scale_trans


def _make_added(fig, key, v):
    """Draw one inserted item. Text moves through dx_mm/dy_mm like any text; a shape's offset is added to its
    coordinates (the editor stores a dragged shape's new coordinates, alignment tools may add an offset)."""
    a, T = v["add"], _mm_transform(fig)
    W, H = fig.get_size_inches() / MM
    typ = a.get("type", "text")
    col, lw, ls = a.get("color", "#1b1b1b"), a.get("lw", 0.8), a.get("ls", "-")
    ox, oy = (0.0, 0.0) if typ == "text" else (v.get("dx_mm", 0.0), v.get("dy_mm", 0.0))
    if typ == "text":
        parts = [fig.text(a.get("x_mm", W / 2), a.get("y_mm", H / 2), a.get("text", ""), transform=T,
                          fontsize=a.get("size_pt", 7), color=col, ha="left", va="baseline")]
    elif typ in ("arrow", "line"):
        parts = [FancyArrowPatch((a["x0_mm"] + ox, a["y0_mm"] + oy), (a["x1_mm"] + ox, a["y1_mm"] + oy), transform=T,
                                 arrowstyle=a.get("head", "-|>" if typ == "arrow" else "-"),
                                 mutation_scale=a.get("head_size", 6), lw=lw, color=col, linestyle=ls,
                                 shrinkA=0, shrinkB=0, capstyle="butt", joinstyle="miter")]
    elif typ == "box":
        r = a.get("radius_mm", 1.0)
        parts = [FancyBboxPatch((a["x_mm"] + ox, a["y_mm"] + oy), a["w_mm"], a["h_mm"], transform=T,
                                boxstyle=("round,pad=0,rounding_size=%g" % r) if r > 0 else "square,pad=0",
                                lw=lw, edgecolor=col, facecolor=a.get("fill", "none"), linestyle=ls)]
    elif typ == "bracket":
        x0, x1, y, h = a["x0_mm"] + ox, a["x1_mm"] + ox, a["y_mm"] + oy, a.get("h_mm", 1.5)
        parts = [Line2D([x0, x0, x1, x1], [y - h, y, y, y - h], transform=T, lw=lw, color=col, linestyle=ls,
                        solid_joinstyle="miter", solid_capstyle="butt"),
                 Text((x0 + x1) / 2, y + a.get("gap_mm", 0.3), a.get("text", "*"), transform=T, ha="center",
                      va="bottom", fontsize=a.get("size_pt", 7), color=col)]
    else:
        return
    for p in parts:
        if p not in fig.texts:
            fig.add_artist(p)
        p._tw_key = key
    if not hasattr(fig, "_tw_added"):
        fig._tw_added = {}
    fig._tw_added[key] = (typ, parts)


# ---- applying one adjustment ---------------------------------------------------------------------------------------

def _shift_text(fig, t, dx, dy):
    off = ScaledTranslation(dx * MM, dy * MM, fig.dpi_scale_trans)
    orig = t.set_transform
    t.set_transform = lambda tr, _o=orig, _off=off: _o(tr + _off)     # Annotation resets it on every draw
    if not isinstance(t, Annotation):
        orig(t.get_transform() + off)


def _shift_legend(lg, dx, dy):
    orig = lg._findoffset

    def find(width, height, xdescent, ydescent, renderer, _o=orig):
        x, y = _o(width, height, xdescent, ydescent, renderer)
        return x + renderer.points_to_pixels(dx * PT_PER_MM), y + renderer.points_to_pixels(dy * PT_PER_MM)
    lg._findoffset = find
    lg._legend_box.set_offset(find)          # the legend box holds the bound method taken at creation


class _Renamed(Formatter):
    """Wraps an axis formatter and replaces chosen label strings."""

    def __init__(self, inner, rename):
        self.inner, self.rename = inner, rename

    def set_axis(self, axis):
        self.inner.set_axis(axis)
        super().set_axis(axis)

    def set_locs(self, locs):
        self.inner.set_locs(locs)

    def __call__(self, x, pos=None):
        s = self.inner(x, pos)
        return self.rename.get(s, s)

    def format_ticks(self, values):
        return [self.rename.get(s, s) for s in self.inner.format_ticks(values)]

    def get_offset(self):
        return self.inner.get_offset()


def _apply(fig, it, tw):
    kind, a = it["kind"], it["artist"]
    if kind == "shape":                                # geometry and base style live in tw["add"]
        m = {k.lower(): v for k, v in (tw.get("colors") or {}).items()}
        for p in it["parts"]:
            if m:
                _recolor(p, m)
            if tw.get("lw", 1.0) != 1.0:
                _scale_lw(p, tw["lw"])
            if "alpha" in tw:
                p.set_alpha(tw["alpha"])
            if isinstance(p, Text):
                if tw.get("size", 1.0) != 1.0:
                    p.set_fontsize(p.get_fontsize() * tw["size"])
                if tw.get("weight"):
                    p.set_fontweight(tw["weight"])
            if tw.get("visible") is False:
                p.set_visible(False)
        return
    dx, dy, size = tw.get("dx_mm", 0.0), tw.get("dy_mm", 0.0), tw.get("size", 1.0)
    W, H = fig.get_size_inches() / MM
    if tw.get("colors"):
        m = {k.lower(): v for k, v in tw["colors"].items()}
        if kind == "ticks":
            for lab in it["members"]:
                _recolor(lab, m)
            a.axes.tick_params(axis=it["axis"], which="both",
                               **{k: m[_hex(v)] for k, v in (("labelcolor", it["members"][0].get_color()),)
                                  if _hex(v) in m})
        elif kind != "figure":
            _recolor(a, m)
    if tw.get("lw", 1.0) != 1.0:
        if kind == "axes":                                 # the frame: spines and tick marks, not the data
            for sp in a.spines.values():
                sp.set_linewidth(sp.get_linewidth() * tw["lw"])
            for nm, axis in (("x", a.xaxis), ("y", a.yaxis)):
                ticks = axis.get_major_ticks()
                if ticks:
                    a.tick_params(axis=nm, which="major", width=ticks[0].tick1line.get_markeredgewidth() * tw["lw"])
                mt = axis.get_minor_ticks()
                if mt:
                    a.tick_params(axis=nm, which="minor", width=mt[0].tick1line.get_markeredgewidth() * tw["lw"])
        else:
            _scale_lw(a, tw["lw"])
    if "alpha" in tw and kind in ("text", "axislabel", "scatter", "line", "patch", "collection", "image"):
        a.set_alpha(tw["alpha"])
    if kind == "figure":
        if tw.get("background"):
            fig.patch.set_facecolor(tw["background"])
    elif kind == "axes":
        x0, y0, w, h = a.get_position(original=True).bounds
        dw, dh = tw.get("dw_mm", 0.0), tw.get("dh_mm", 0.0)
        if dx or dy or dw or dh:
            a.set_position(Bbox.from_bounds(x0 + dx / W, y0 + (dy - dh) / H, w + dw / W, h + dh / H))
        if tw.get("background") or "background_alpha" in tw:
            a.set_facecolor(to_rgba(tw.get("background") or a.patch.get_facecolor(), tw.get("background_alpha")))
    elif kind in ("text", "axislabel"):
        if "text" in tw:
            a.set_text(tw["text"])
        if size != 1.0:
            a.set_fontsize(a.get_fontsize() * size)
        if tw.get("weight"):
            a.set_fontweight(tw["weight"])
        if tw.get("style"):
            a.set_fontstyle(tw["style"])
        if "rotation" in tw:
            a.set_rotation(tw["rotation"])
        if tw.get("ha"):
            a.set_horizontalalignment(tw["ha"])
            a.set_multialignment(tw["ha"])
        if dx or dy:
            _shift_text(fig, a, dx, dy)
    elif kind == "ticks":
        axis, ax = a, a.axes
        if tw.get("rename"):
            axis.set_major_formatter(_Renamed(axis.get_major_formatter(), dict(tw["rename"])))
        kw = {}
        d = (dx if it["axis"] == "y" else dy) * PT_PER_MM
        if d:
            sign = -1 if it["side"] == 1 else 1           # left/bottom labels move out as the column moves out
            kw["pad"] = axis.get_major_ticks()[0].get_pad() + sign * d
        if size != 1.0:
            kw["labelsize"] = it["members"][0].get_fontsize() * size
        if "rotation" in tw:
            kw["labelrotation"] = tw["rotation"]
        if tw.get("weight"):
            for t in axis.get_major_ticks():
                t.label1.set_fontweight(tw["weight"])
                t.label2.set_fontweight(tw["weight"])
        if tw.get("visible") is False:
            kw.update(label1On=False, label2On=False)
        if kw:
            ax.tick_params(axis=it["axis"], which="major", **kw)
        return
    elif kind == "legend":
        for t in a.get_texts():
            if tw.get("rename") and t.get_text() in tw["rename"]:
                t.set_text(tw["rename"][t.get_text()])
            if size != 1.0:
                t.set_fontsize(t.get_fontsize() * size)
            if tw.get("weight"):
                t.set_fontweight(tw["weight"])
        if dx or dy:
            _shift_legend(a, dx, dy)
    elif kind == "scatter" and tw.get("scale", 1.0) != 1.0:
        a.set_sizes(a.get_sizes() * tw["scale"])
    if tw.get("visible") is False and kind != "figure":
        a.set_visible(False)


# ---- entry point ---------------------------------------------------------------------------------------------------

def _style_palette():
    """Named hex colours of the project's style module, if one is loaded (shown as swatches in the editor)."""
    mod = sys.modules.get("style")
    out = {}
    for k, v in (vars(mod).items() if mod else []):
        if k.isupper() and isinstance(v, str) and v.startswith("#") and len(v) in (7, 9):
            out[k] = v.lower()[:7]
    return out


def apply(fig, here, stem, rerun_args=None):
    """Apply <stem>.tweaks.json to `fig` and write <stem>.tweak_keys.json. `rerun_args` are the command-line
    arguments that re-render only this figure (default: those of the current run)."""
    path = os.path.join(here, stem + ".tweaks.json")
    tweaks = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}
    for k, v in sorted(tweaks.items()):            # texts and shapes inserted in the editor
        if k.startswith("fig/added/") and isinstance(v, dict) and v.get("add"):
            _make_added(fig, k, v)
    fig.canvas.draw()                              # lays out ticks and legends so they can be keyed and tagged
    renderer = fig.canvas.get_renderer()
    H_pt = fig.get_size_inches()[1] * 72
    to_svg = 72.0 / fig.dpi
    items = _items(fig)
    ids, palette = {}, Counter()
    for it in items:                               # tag everything before anything changes
        a, gid = it["artist"], _gid(it["key"])
        rec = dict(key=it["key"], kind=it["kind"])
        if it.get("added"):
            rec["added"] = True
        if isinstance(a, Text):
            rec.update(rotation=round(a.get_rotation(), 2), ha=a.get_horizontalalignment())
        font = _font_of(it)
        if font:                                   # base font, for the format painter and the consistency check
            rec.update(fontsize=round(font.get_fontsize(), 2), weight=_weight(font.get_fontweight()),
                       role=_role(it))
        if it["kind"] == "shape":
            rec["shape"] = it["shape"]
            for j, p in enumerate(it["parts"][1:]):
                p.set_gid("%s_p%d" % (gid, j))
            rec["parts"] = ["%s_p%d" % (gid, j) for j in range(len(it["parts"]) - 1)]
        if it["kind"] == "figure":
            a.patch.set_gid(gid)
            rec["background"] = _hex(a.patch.get_facecolor()) or "#ffffff"
        else:
            a.set_gid(gid)
        if it["kind"] == "axes":
            a.patch.set_gid(gid + "_bg")
            rec.update(panel=it["panel"], background=_hex(a.patch.get_facecolor()) or "none")
        if it["kind"] in ("ticks", "legend"):
            rec.update({k: it[k] for k in ("axis", "side") if k in it})
            for j, m in enumerate(it.get("members", [])):
                mid = "%s_%d" % (gid, j)
                m.set_gid(mid)
                ids[mid] = dict(key=it["key"], kind=it["kind"], member=m.get_text(), group=gid,
                                **{k: it[k] for k in ("axis", "side") if k in it})
        if isinstance(a, Annotation) and a.arrow_patch is not None:
            a.arrow_patch.set_gid(gid + "_arrow")
            px, py = a._get_position_xy(renderer)          # the annotated point, which the leader keeps
            rec["arrow"] = [px * to_svg, H_pt - py * to_svg]
        name = _name(a) if it["kind"] not in ("figure", "axes", "ticks") else ""
        if name:
            rec["name"] = name
        cols = _colors_of(a) if it["kind"] != "figure" else []
        if cols:
            rec["colors"] = sorted(set(cols), key=cols.index)
        if it["kind"] == "figure":
            palette.update(_colors_of(fig))
        ids[gid] = rec
    used = set()
    for it in items:                               # element-level first, then the figure-wide colour swap
        tw = tweaks.get(it["key"])
        if tw:
            used.add(it["key"])
            _apply(fig, it, tw)
    gm = (tweaks.get("fig/figure") or {}).get("colors")
    if gm:
        _recolor(fig, {k.lower(): v for k, v in gm.items()})
    meta = dict(stem=stem, script=os.path.abspath(sys.argv[0]),
                args=[str(x) for x in (sys.argv[1:] if rerun_args is None else rerun_args)],
                python=sys.executable, cwd=os.getcwd(), size_mm=[round(v / MM, 2) for v in fig.get_size_inches()],
                palette=[c for c, _ in palette.most_common()], style_palette=_style_palette())
    json.dump(dict(meta=meta, ids=ids), open(os.path.join(here, stem + ".tweak_keys.json"), "w", encoding="utf-8"),
              indent=0, ensure_ascii=False)
    stale = sorted(set(tweaks) - used)
    if stale:
        print("tweaks: %d entr%s match no artist any more: %s" % (len(stale), "y" if len(stale) == 1 else "ies",
                                                                  "; ".join(stale)))
    if used:
        print("tweaks: applied %d hand adjustment%s from %s.tweaks.json" % (len(used), "" if len(used) == 1 else "s",
                                                                            stem))
