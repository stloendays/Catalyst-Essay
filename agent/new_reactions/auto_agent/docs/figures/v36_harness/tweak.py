"""Hand adjustments of a finished matplotlib figure, kept as data and re-applied on every render.

Call `apply(fig, here, stem)` just before saving (Page.save does). It reads `<stem>.tweaks.json` next to the figure,
applies the adjustments, tags every adjustable artist with an SVG id, and writes `<stem>.tweak_keys.json`: the ids,
what each one is, its colours, the figure palette and how to re-render the figure (script, arguments, interpreter),
so the browser editor (tools/figure_tweak.py) can find and rebuild any figure that went through here.

Keys are built from the axes (position in mm), the kind and, for text, the string; they are taken after a layout
draw and before anything changes, so they stay valid after an adjustment.

Adjustable, per kind (lengths in mm; size, scale and lw are factors; colours are hex):
    figure      background, colors {old: new} over the whole figure; frame, tickdir, grid for every chart and
                textbox ("none": no border on boxed texts, and a white box left without a border goes too) for every
                text, unless the item sets its own
    axes        dx_mm, dy_mm, dw_mm, dh_mm (top-left fixed), background, background_alpha, lw (frame and ticks),
                colors, visible;
                frame ("full", "open": the two axis sides only, "none"), tickdir ("in", "out", "inout"),
                grid ("none", "x", "y", "both"), refs [{axis, v, color, ls, lw, label}] reference lines,
                and Origin's axis dialog, applied before the figure is keyed so the editor sees the new ticks:
                xlim/ylim [lo, hi], xscale/yscale ("linear", "log"), xstep/ystep (major tick spacing),
                xminor/yminor (minor ticks on or off);
                the plotted data, applied first (the keys file lists each chart's series under "series"):
                data {sid: {x, y, err} or {z}} replaces the values of a series the script drew (sid "bars/0",
                "line/2", "scatter/0", "errorbar/0", "image/0"), and series [{id, type ("bar", "line", "scatter",
                "area"), x, y, err, label, color, dodge, band, marker, legend}] adds series, keyed
                "<axes>/series/<id>/<part>"; added bars with dodge stand beside the script's bars
    text        texts, annotation labels, titles, letters: dx_mm, dy_mm, size, text, weight, style, rotation (deg),
                ha (left/center/right), colors, alpha, visible, border (false: a boxed text keeps its fill only)
                (an annotation's leader line keeps its data end and follows the label)
    axislabel   axis titles: as text
    ticks       the tick or category labels of one axis: dx_mm (y) / dy_mm (x), size, weight, rotation,
                rename {old: new}, colors, visible
    legend      dx_mm, dy_mm, size, weight, rename, colors, visible, frame (true/false), loc ("upper right" ...)
    added       "fig/added/<id>": {"add": {...}} plus the usual settings: an item the author inserted in the editor,
                in mm from the figure's bottom-left corner. add.type is
                  text     x_mm, y_mm (baseline-left), text, size_pt, color
                  arrow    x0_mm, y0_mm, x1_mm, y1_mm, head ("-|>", "->", "<|-|>", "-"), head_size, lw, ls, color
                  line     as arrow, head "-"
                  bracket  x0_mm, x1_mm, y_mm (the bar), h_mm (the legs), text ("*", "n.s." ...), size_pt, lw, color
                  box      x_mm, y_mm (bottom-left), w_mm, h_mm, radius_mm, fill, lw, ls, color
                  chart    x_mm, y_mm, w_mm, h_mm, script (a chart template's drawing script beside the figure,
                           which draws into that box); its charts are keyed "<insert key>/ax<n>/..."
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

import matplotlib
import numpy as np
from matplotlib.axis import Axis
from matplotlib.collections import Collection, LineCollection, PathCollection, PolyCollection
from matplotlib.container import BarContainer, ErrorbarContainer
from matplotlib.colors import LinearSegmentedColormap, to_hex, to_rgba
from matplotlib.figure import Figure
from matplotlib.legend import Legend
from matplotlib.lines import Line2D
from matplotlib.markers import MarkerStyle
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Patch
from matplotlib.text import Annotation, Text
from matplotlib.ticker import (AutoMinorLocator, FixedLocator, Formatter, FuncFormatter, LogLocator, MultipleLocator,
                               NullFormatter, NullLocator)
from matplotlib.transforms import Affine2D, Bbox, ScaledTranslation, blended_transform_factory

TWEAK_VERSION = "1.7"                                # onboarding replaces an older copy in a project
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

def _subfigs(fig):
    """The figure's subfigures (fig.subfigures), nested ones included, with a key prefix each: fig/sub0, fig/sub0/1..."""
    out = []

    def walk(f, prefix):
        for i, sf in enumerate(getattr(f, "subfigs", None) or []):
            out.append((sf, "%s%d" % (prefix, i)))
            walk(sf, "%s%d/" % (prefix, i))
    walk(fig, "fig/sub")
    return out


def _fig_texts(fig):
    """Texts placed on the figure and on its subfigures (suptitles, panel letters, notes)."""
    return list(fig.texts) + [t for sf, _ in _subfigs(fig) for t in sf.texts]


def _axkeys(fig):
    W, H = fig.get_size_inches() / MM
    seen, out = Counter(), {}
    for ax in fig.axes:
        if getattr(ax, "_tw_inset", None):            # a chart inserted in the editor: keyed by its insert
            out[ax] = ax._tw_inset
            continue
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


def _bar_name(p):
    """A bar's layer name: its category (and its series' label when the chart has several), e.g. 'Fe' or 'catalyst A · Fe'."""
    ax = getattr(p, "axes", None)
    if ax is None:
        return ""
    bcs = [c for c in ax.containers if isinstance(c, BarContainer) and c.patches]
    for c in bcs:
        if p in c.patches:
            horiz = getattr(c, "orientation", None) == "horizontal"
            mid = p.get_y() + p.get_height() / 2 if horiz else p.get_x() + p.get_width() / 2
            cat = _axis_value(ax.yaxis if horiz else ax.xaxis, mid, near=True)
            cat = cat if isinstance(cat, str) else ""
            lab = c.get_label() if len(bcs) > 1 and not str(c.get_label()).startswith("_") else ""
            return " · ".join(x for x in (lab, cat) if x)
    return ""


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
    for sf, sk in _subfigs(fig):                       # subfigures: their own titles, texts and legends
        texts_of(sk, sf.texts, "text")
        legends_of(sk, sf.legends)
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
        own = lambda a: not hasattr(a, "_tw_key")  # noqa: E731  (series added in the editor are keyed below)
        for i, c in enumerate(x for x in ax.collections if isinstance(x, PathCollection) and len(x.get_offsets())
                              and own(x)):
            items.append(dict(key="%s/scatter/%d" % (ak, i), kind="scatter", artist=c))
        for i, c in enumerate(x for x in ax.collections if not isinstance(x, PathCollection) and own(x)):
            items.append(dict(key="%s/collection/%d" % (ak, i), kind="collection", artist=c))
        for i, ln in enumerate(x for x in ax.lines if own(x)):
            items.append(dict(key="%s/line/%d" % (ak, i), kind="line", artist=ln))
        for a in list(ax.collections) + list(ax.lines):
            if hasattr(a, "_tw_kind"):
                items.append(dict(key=a._tw_key, kind=a._tw_kind, artist=a, added_series=True))
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
        if it["key"].startswith("fig/text/") or it["key"].startswith("fig/sub") and "/text/" in it["key"]:
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


def _draw_chart(fig, key, v, here):
    """A chart inserted in the editor: its own drawing script (a chart template, written beside the figure by the
    editor) draws into the box add.x_mm, y_mm, w_mm, h_mm (mm from the figure's bottom-left corner)."""
    a = v["add"]
    src = os.path.join(here, a["script"])
    before = set(fig.axes)
    box = (a["x_mm"] + v.get("dx_mm", 0.0), a["y_mm"] + v.get("dy_mm", 0.0), a["w_mm"], a["h_mm"])
    ns = dict(__file__=src, __name__="tw_chart", FIG=fig, BOX=box)
    try:
        exec(compile(open(src, encoding="utf-8").read(), src, "exec"), ns)
    except (Exception, SystemExit) as e:              # noqa: BLE001 -- one bad insert must not stop the figure
        print("tweaks: inserted chart %s not drawn: %s" % (key, e))
    for j, ax in enumerate(x for x in fig.axes if x not in before):
        ax._tw_inset = "%s/ax%d" % (key, j)
    if not hasattr(fig, "_tw_charts"):
        fig._tw_charts = set()
    fig._tw_charts.add(key)


# ---- line styles, markers and colour maps --------------------------------------------------------------------------

LINESTYLES = {"-": "solid", "--": "dashed", ":": "dotted", "-.": "dashdot", "none": "None"}


def _ls_name(ls):
    """matplotlib's linestyle (a name, a symbol or an (offset, dashes) tuple) as one of '-', '--', ':', '-.', 'none'."""
    if isinstance(ls, tuple):
        return "--" if ls[1] else "-"
    s = str(ls)
    return {"solid": "-", "dashed": "--", "dotted": ":", "dashdot": "-.", "None": "none", " ": "none", "": "none"}.get(s, s)


def _style_line(a, tw):
    """ls ('-', '--', ':', '-.', 'none'), dash [on, off] in pt, marker, ms (pt), mew (pt), mfc ('none' for hollow)."""
    widths = [a.get_linewidth()] if isinstance(a, Line2D) else list(np.atleast_1d(a.get_linewidth()))
    if ("ls" in tw or "dash" in tw) and max(widths or [0]) > 0:   # a stroke of width 0 (a band's edge) has no dashes
        ls = tw.get("ls", "--" if "dash" in tw else "-")
        if ls == "--" and tw.get("dash"):
            lw = widths[0] if widths else 1.0
            on, off = tw["dash"]
            scale = lw if matplotlib.rcParams["lines.scale_dashes"] and lw > 0 else 1.0   # dashes scale with lw
            a.set_linestyle((0, (on / scale, off / scale)))
        else:
            a.set_linestyle(LINESTYLES.get(ls, ls))
    if isinstance(a, Line2D):
        if "marker" in tw:
            a.set_marker(tw["marker"] if tw["marker"] != "none" else "None")
        if "ms" in tw:
            a.set_markersize(tw["ms"])
        if "mew" in tw:
            a.set_markeredgewidth(tw["mew"])
        if "mfc" in tw:
            a.set_markerfacecolor(tw["mfc"])
    elif isinstance(a, PathCollection) and tw.get("marker") and tw["marker"] != "none":
        ms = MarkerStyle(tw["marker"])
        a.set_paths([ms.get_path().transformed(ms.get_transform())])


def _paper_cmaps():
    """Colour maps from the project's palette (white -> Ru blue, white -> Fe green, blue -> white -> red)."""
    pal = _style_palette()
    blue, green, red = pal.get("RU", "#5677b5"), pal.get("FE", "#6e9f60"), pal.get("RED", "#d9474f")
    dark_b, dark_g = pal.get("DARK_B", "#304c86"), pal.get("DARK_G", "#467238")
    return {"paper_blue": LinearSegmentedColormap.from_list("paper_blue", ["#ffffff", blue, dark_b]),
            "paper_green": LinearSegmentedColormap.from_list("paper_green", ["#ffffff", green, dark_g]),
            "paper_red": LinearSegmentedColormap.from_list("paper_red", ["#ffffff", red]),
            "paper_div": LinearSegmentedColormap.from_list("paper_div", [dark_b, "#ffffff", red])}


CMAP_CHOICES = ["paper_blue", "paper_green", "paper_red", "paper_div", "viridis", "cividis", "magma", "plasma",
                "Blues", "Greens", "Reds", "Oranges", "Purples", "Greys", "YlGnBu", "YlOrRd", "RdBu_r", "coolwarm",
                "PuOr_r", "BrBG"]


def _get_cmap(name):
    rev = name.endswith("_r") and name[:-2] in _paper_cmaps()
    base = name[:-2] if rev else name
    cm = _paper_cmaps().get(base) or matplotlib.colormaps[base]
    return cm.reversed() if rev else cm


def _style_cmap(a, tw):
    cb = getattr(a, "colorbar", None)
    keep = None
    if cb is not None and tw.get("clim"):            # the colorbar keeps its own tick values and wording
        locs = [float(v) for v in cb.locator()]
        labs = cb.formatter.format_ticks(locs) if hasattr(cb.formatter, "format_ticks") else [str(v) for v in locs]
        keep = (locs, dict(zip((round(v, 12) for v in locs), labs)))
    if tw.get("cmap"):
        a.set_cmap(_get_cmap(tw["cmap"]))
    if tw.get("clim"):
        a.set_clim(*tw["clim"])
    if keep:
        locs, lab = keep
        cb.locator = FixedLocator(locs)
        cb.formatter = FuncFormatter(lambda v, pos, _l=lab: _l.get(round(float(v), 12), "%g" % v))


def _cmap_samples():
    """Eleven colours of each colour map on offer, for the editor's swatches."""
    out = {}
    for n in CMAP_CHOICES:
        cm = _get_cmap(n)
        out[n] = [to_hex(cm(i / 10)) for i in range(11)]
    return out


def _is_mapped(a):
    """Coloured through a colour map (a heat map, contour or colour-coded scatter), not an RGB picture."""
    if not (hasattr(a, "get_array") and hasattr(a, "get_cmap")) or a.get_array() is None:
        return False
    if getattr(getattr(a, "axes", None), "_colorbar", None) is not None:
        return False                                   # a colorbar's own swatch follows its mappable
    return a.get_array().ndim <= 2 and not (a.get_array().ndim == 2 and a.__class__.__name__ == "AxesImage"
                                            and False) and not (a.get_array().ndim == 3)


def _follow_colorbars(fig, tweaks, axkeys):
    """A colorbar's axes moves with the chart it belongs to, unless it was moved itself."""
    key_of = {ax: k for ax, k in axkeys.items()}
    W, H = fig.get_size_inches() / MM
    for cax in fig.axes:
        cb = getattr(cax, "_colorbar", None)
        parent = getattr(getattr(cb, "mappable", None), "axes", None)
        if cb is None or parent is None or parent not in key_of or cax not in key_of:
            continue
        own = tweaks.get(key_of[cax] + "/axes") or {}
        if own.get("dx_mm") or own.get("dy_mm"):
            continue
        p = tweaks.get(key_of[parent] + "/axes") or {}
        dx, dy = p.get("dx_mm", 0.0), p.get("dy_mm", 0.0)
        if cb.orientation == "vertical":
            dx += p.get("dw_mm", 0.0)                  # a colorbar to the right follows the chart's right edge
        else:
            dy -= p.get("dh_mm", 0.0)                  # one below follows its bottom edge
        if dx or dy:
            x0, y0, w, h = cax.get_position(original=True).bounds
            cax.set_position(Bbox.from_bounds(x0 + dx / W, y0 + dy / H, w, h))


# ---- frames, axes and reference lines (Origin's layer and axis dialogs) --------------------------------------------

STRUCT = ("xlim", "ylim", "xscale", "yscale", "xstep", "ystep", "xminor", "yminor")


def _is_chart(ax):
    return ax.axison and set(ax.spines.keys()) >= {"left", "right", "top", "bottom"} \
        and getattr(ax, "_colorbar", None) is None


def _label_sides(ax):
    """(x side, y side) that carry the tick labels: 'bottom'/'top', 'left'/'right'."""
    def side(axis, one, two):
        ticks = axis.get_major_ticks()
        if ticks and ticks[0].label2.get_visible() and not ticks[0].label1.get_visible():
            return two
        return one
    return side(ax.xaxis, "bottom", "top"), side(ax.yaxis, "left", "right")


def _frame_of(ax):
    vis = [ax.spines[s].get_visible() for s in ("left", "right", "top", "bottom")]
    return "full" if all(vis) else "none" if not any(vis) else "open"


def _set_frame(ax, mode):
    """full: four sides; open: only the sides that carry tick labels (a twin axis keeps its own side);
    none: no spines (tick marks stay)."""
    if not _is_chart(ax) or mode not in ("full", "open", "none"):
        return
    xs, ys = _label_sides(ax)
    keep = {xs, ys}
    for s, sp in ax.spines.items():
        if mode == "full":
            sp.set_visible(True)
        elif mode == "none" or s not in keep:
            sp.set_visible(False)
    if mode != "full":
        off = {s: False for s in ("top", "bottom", "left", "right") if s not in keep}
        ax.tick_params(which="both", **off)


def _tickdir_of(ax):
    t = ax.xaxis.get_major_ticks()
    return getattr(t[0], "_tickdir", "out") if t else "out"


def _grid_of(ax):
    on = [any(g.get_visible() for g in a.get_gridlines()) for a in (ax.xaxis, ax.yaxis)]
    return {(False, False): "none", (True, False): "x", (False, True): "y", (True, True): "both"}[tuple(on)]


def _set_grid(ax, mode):
    style = {}
    for a in (ax.xaxis, ax.yaxis):                     # keep the script's grid style when there is one
        g = [x for x in a.get_gridlines() if x.get_visible()]
        if g:
            style = dict(color=g[0].get_color(), linewidth=g[0].get_linewidth(), linestyle=g[0].get_linestyle())
            break
    style = style or dict(color="#e2e2e2", linewidth=0.4)
    ax.grid(False, axis="both", which="both")
    if mode in ("x", "both"):
        ax.grid(True, axis="x", which="major", **style)
    if mode in ("y", "both"):
        ax.grid(True, axis="y", which="major", **style)
    ax.set_axisbelow(True)


def _axis_structure(ax, tw):
    """Range, scale, major spacing and minor ticks, like Origin's axis dialog."""
    for n in "xy":
        axis = getattr(ax, n + "axis")
        sc = tw.get(n + "scale")
        if sc in ("linear", "log") and sc != getattr(ax, "get_%sscale" % n)():
            getattr(ax, "set_%sscale" % n)(sc)
        lim = tw.get(n + "lim")
        if isinstance(lim, (list, tuple)) and len(lim) == 2 and lim[0] != lim[1]:
            getattr(ax, "set_%slim" % n)(float(lim[0]), float(lim[1]))
        linear = getattr(ax, "get_%sscale" % n)() == "linear"
        step = tw.get(n + "step")
        if step and linear:
            lo, hi = sorted(getattr(ax, "get_%slim" % n)())
            if (hi - lo) / float(step) <= 200:
                axis.set_major_locator(MultipleLocator(float(step)))
        if n + "minor" in tw:
            if tw[n + "minor"]:
                axis.set_minor_locator(AutoMinorLocator() if linear else LogLocator(base=10, subs=(2, 3, 4, 5, 6, 7, 8, 9)))
                axis.set_minor_formatter(NullFormatter())
            else:
                axis.set_minor_locator(NullLocator())


def _add_refs(ax, refs):
    """Reference lines at data values (Origin's 'Add reference line'); the view keeps its limits."""
    xl, yl = ax.get_xlim(), ax.get_ylim()
    for r in refs or []:
        try:
            v = float(r["v"])
        except (KeyError, TypeError, ValueError):
            continue
        kw = dict(color=r.get("color", "#d9474f"), lw=r.get("lw", 0.6), zorder=1.6,
                  linestyle=LINESTYLES.get(r.get("ls", "--"), r.get("ls", "--")))
        if r.get("axis", "y") == "y":
            ax.axhline(v, **kw)
            if r.get("label"):
                ax.text(0.99, v, r["label"], transform=blended_transform_factory(ax.transAxes, ax.transData),
                        ha="right", va="bottom", fontsize=r.get("size_pt", 5.6), color=kw["color"], zorder=7)
        else:
            ax.axvline(v, **kw)
            if r.get("label"):
                ax.text(v, 0.99, r["label"], transform=blended_transform_factory(ax.transData, ax.transAxes),
                        ha="right", va="top", rotation=90, fontsize=r.get("size_pt", 5.6), color=kw["color"], zorder=7)
    ax.set_xlim(xl)
    ax.set_ylim(yl)


# ---- the plotted data: read, replaced, and series added in the editor (FigureTweak 1.3) ----------------------------

DATA_ROWS = 2000                                     # longer series are listed but not offered for editing
DATA_CELLS = 30000                                   # values written per figure; later series are listed only


def _num(v):
    try:
        f = float(v)
    except (TypeError, ValueError):
        return str(v)
    return None if f != f else float("%.6g" % f)


def _categories(axis):
    """{position: name} of a categorical axis, else None."""
    m = getattr(getattr(axis, "units", None), "_mapping", None)
    return {v: k for k, v in m.items()} if isinstance(m, dict) and m else None


def _names(axis):
    """{position: name}: the categories of a categorical axis, or the text tick labels the script set."""
    cats = _categories(axis)
    if cats:
        return {float(k): v for k, v in cats.items()}
    try:
        pairs = zip(axis.get_majorticklocs(), [t.get_text() for t in axis.get_majorticklabels()])
    except Exception:                                  # noqa: BLE001 -- an axis without ticks
        return None
    out = {float(loc): t for loc, t in pairs if t.strip() and isinstance(_num(t.replace("−", "-")), str)}
    return out or None


def _axis_value(axis, v, near=False):
    """A position on the axis as the editor shows it: the category or tick name at it (near: the nearest one within
    half a step, for bars beside each other), else the number."""
    names = _names(axis)
    try:
        f = float(v)
    except (TypeError, ValueError):
        return str(v)
    if names:
        locs = sorted(names)
        k = min(locs, key=lambda x: abs(x - f))
        step = min(np.diff(locs)) if len(locs) > 1 else 1.0
        if abs(k - f) < (0.5 * step if near else 1e-6 * max(1.0, abs(f))):
            return names[k]
    return _num(f)


def _positions(axis, vals):
    """Values typed in the editor (numbers or category names) as positions on the axis."""
    rev = {v: k for k, v in (_names(axis) or {}).items()}
    cat = _categories(axis) is not None
    out = []
    for v in vals:
        s = str(v).strip()
        if s in rev:
            out.append(rev[s])
            continue
        try:
            out.append(float(s.replace("−", "-")))
        except ValueError:
            if not cat:
                raise ValueError("%r is neither a number nor a category of this axis" % s)
            axis.update_units(np.array([s]))
            out.append(float(np.atleast_1d(axis.convert_units(s))[0]))
    return np.asarray(out, dtype=float)


def _floats(vals):
    return np.asarray([np.nan if str(v).strip() in ("", "None") else float(v) for v in vals], dtype=float)


def _script_series(ax):
    """The data series the script drew on ax, as (sid, kind, artist or container), in a stable order."""
    out = []
    ebs = [c for c in ax.containers if isinstance(c, ErrorbarContainer)]
    skip = {id(c[0]) for c in ebs if c[0] is not None} | {id(x) for c in ebs for x in (c[1] or ())}
    for i, c in enumerate(x for x in ax.containers if isinstance(x, BarContainer)):
        if c.patches:
            out.append(("bars/%d" % i, "bars", c))
    for i, c in enumerate(ebs):
        if _eb_xy(c)[0] is not None:
            out.append(("errorbar/%d" % i, "errorbar", c))
    for i, ln in enumerate(ax.lines):
        if hasattr(ln, "_tw_key") or id(ln) in skip or ln.get_transform() is not ax.transData:
            continue
        if len(ln.get_xdata()) < 2 and str(ln.get_marker()) in ("None", "", " "):
            continue
        out.append(("line/%d" % i, "line", ln))
    for i, c in enumerate(x for x in ax.collections if isinstance(x, PathCollection) and len(x.get_offsets())):
        if not hasattr(c, "_tw_key") and c.get_offset_transform() is ax.transData:
            out.append(("scatter/%d" % i, "scatter", c))
    for i, im in enumerate(ax.images):
        a = im.get_array()
        if a is not None and a.ndim == 2 and a.size <= 3600:
            out.append(("image/%d" % i, "image", im))
    return out


def _eb_xy(c):
    """x and y of an errorbar container: its data line, or the middles of its bars when drawn with fmt="none"."""
    if c[0] is not None:
        return (np.asarray(c[0].get_xdata(orig=False), dtype=float),     # converted: category names are positions
                np.asarray(c[0].get_ydata(orig=False), dtype=float))
    for lc in c[2] or ():
        segs = lc.get_segments()
        if segs and all(len(q) == 2 and abs(q[0][0] - q[1][0]) < 1e-12 for q in segs):
            return np.array([q[0][0] for q in segs]), np.array([(q[0][1] + q[1][1]) / 2 for q in segs])
    return None, None


def _yerr_of(c):
    """Half-lengths of an errorbar container's vertical bars, or None."""
    for lc in c[2] or ():
        segs = lc.get_segments()
        if segs and all(len(s) == 2 and abs(s[0][0] - s[1][0]) < 1e-12 for s in segs):
            return [abs(s[1][1] - s[0][1]) / 2 for s in segs]
    return None


def _series_table(ax, kind, a):
    """What the editor's data table shows: columns, rows, which columns may change, and whether rows are fixed."""
    if kind == "bars":
        horiz = getattr(a, "orientation", None) == "horizontal"
        rows = [[_axis_value(ax.yaxis, r.get_y() + r.get_height() / 2, True), _num(r.get_width())] if horiz else
                [_axis_value(ax.xaxis, r.get_x() + r.get_width() / 2, True), _num(r.get_height())] for r in a.patches]
        return dict(cols=["x", "y"], rows=rows, edit=[1], fixed=True, horizontal=horiz, name=_name(a))
    if kind == "errorbar":
        x, y = _eb_xy(a)
        e = _yerr_of(a)
        rows = [[_axis_value(ax.xaxis, x[i], True), _num(y[i])] + ([_num(e[i])] if e and len(e) == len(x) else [])
                for i in range(len(x))]
        return dict(cols=["x", "y"] + (["err"] if e and len(e) == len(x) else []), rows=rows, edit=[1, 2],
                    fixed=True, name=_name(a) or (_name(a[0]) if a[0] is not None else ""))
    if kind == "line":
        x, y = a.get_xdata(orig=True), a.get_ydata(orig=True)
        rows = [[_num(x[i]) if not isinstance(x[i], str) else x[i], _num(y[i])] for i in range(len(x))]
        return dict(cols=["x", "y"], rows=rows, edit=[0, 1], fixed=False, name=_name(a))
    if kind == "scatter":
        rows = [[_axis_value(ax.xaxis, p[0]), _axis_value(ax.yaxis, p[1])] for p in a.get_offsets()]
        return dict(cols=["x", "y"], rows=rows, edit=[0, 1], fixed=False, name=_name(a))
    z = np.asarray(a.get_array(), dtype=float)
    return dict(cols=["c%d" % (j + 1) for j in range(z.shape[1])], rows=[[_num(v) for v in r] for r in z],
                edit=list(range(z.shape[1])), fixed=True, matrix=True, name=_name(a))


def _set_series(ax, kind, a, d):
    """Replace the plotted values of one series with those typed in the editor."""
    if kind == "bars":
        horiz = getattr(a, "orientation", None) == "horizontal"
        for r, v in zip(a.patches, _floats(d.get("y") or [])):
            if v == v:
                (r.set_width if horiz else r.set_height)(v)
    elif kind == "errorbar":
        x, y = _eb_xy(a)
        y = y.copy()
        e = _floats(d["err"])[:len(y)] if d.get("err") else _yerr_of(a)
        if d.get("y"):
            new = _floats(d["y"])[:len(y)]
            y[:len(new)] = new
        if a[0] is not None:
            a[0].set_ydata(y)
        if e is not None:
            e = np.resize(np.asarray(e, dtype=float), len(y))
            xn = np.asarray(x, dtype=float)
            for lc in a[2] or ():
                lc.set_segments([[(xi, yi - ei), (xi, yi + ei)] for xi, yi, ei in zip(xn, y, e)])
            caps = list(a[1] or ())
            if len(caps) == 2:
                caps[0].set_data(xn, y - e)
                caps[1].set_data(xn, y + e)
    elif kind == "line":
        x, y = d.get("x"), d.get("y")
        x = a.get_xdata(orig=True) if x is None else x
        y = a.get_ydata(orig=True) if y is None else y
        n = min(len(x), len(y))
        try:
            xs = _floats(x[:n])
        except (TypeError, ValueError):
            xs = [str(v) for v in x[:n]]
        a.set_data(xs, _floats(y[:n]))
    elif kind == "scatter":
        old = a.get_offsets()
        x = d.get("x") if d.get("x") is not None else [_axis_value(ax.xaxis, p[0]) for p in old]
        y = d.get("y") if d.get("y") is not None else [_axis_value(ax.yaxis, p[1]) for p in old]
        n = min(len(x), len(y))
        a.set_offsets(np.column_stack([_positions(ax.xaxis, x[:n]), _positions(ax.yaxis, y[:n])]))
        if len(a.get_sizes()) > 1 and len(a.get_sizes()) != n:
            a.set_sizes(np.resize(a.get_sizes(), n))
        if a.get_array() is not None and len(a.get_array()) != n:
            a.set_array(np.resize(a.get_array(), n))
        for get, put in ((a.get_facecolors, a.set_facecolor), (a.get_edgecolors, a.set_edgecolor)):
            c = get()
            if len(c) > 1 and len(c) != n:
                put(np.resize(c, (n, 4)))
    elif kind == "image" and d.get("z"):
        z = np.array([_floats(r) for r in d["z"]], dtype=float)
        if z.shape == a.get_array().shape:
            a.set_data(z)


def _bar_horizontal(ax):
    bcs = [c for c in ax.containers if isinstance(c, BarContainer) and c.patches]
    return bool(bcs) and all(getattr(c, "orientation", None) == "horizontal" for c in bcs)


def _bar_slots(ax, added):
    """(width, offset) of each added bar series. Bars set to stand beside the others ('dodge') share the width of
    the script's bar group, and the script's bars move aside to make room."""
    out, h = {}, _bar_horizontal(ax)
    P = (lambda r: r.get_y()) if h else (lambda r: r.get_x())  # noqa: E731  (position and width along the
    S = (lambda r: r.get_height()) if h else (lambda r: r.get_width())  # noqa: E731  category axis)
    dodge = [s for s in added if s.get("type") == "bar" and s.get("dodge", True)]
    rects = [r for c in ax.containers if isinstance(c, BarContainer) and (getattr(c, "orientation", None) == "horizontal")
             == h for r in c.patches]
    w0, s0 = (S(rects[0]), 0) if rects else (None, 0)
    if rects:                                         # bars side by side form a group; its slots are the offsets
        cen = sorted(P(r) + S(r) / 2 for r in rects)
        groups, cur = [], [cen[0]]
        for c in cen[1:]:
            if c - cur[-1] < 1.3 * w0:
                cur.append(c)
            else:
                groups.append(cur)
                cur = [c]
        groups.append(cur)
        anchor = {}
        for g in groups:
            mid = (min(g) + max(g)) / 2
            for c in g:
                anchor[round(c, 9)] = mid
        offs = sorted({round(c - anchor[round(c, 9)], 6) for c in cen})
        s0 = len(offs)
    for s in added:
        if s.get("type") != "bar":
            continue
        x = _positions(ax.yaxis if h else ax.xaxis, s.get("x") or [])
        step = np.min(np.diff(np.unique(x))) if len(np.unique(x)) > 1 else 1.0
        out[id(s)] = (float(s.get("width") or w0 or 0.8 * step), 0.0)
    if not dodge:
        return out
    group = (w0 * s0) if rects else out[id(dodge[0])][0]
    total = s0 + len(dodge)
    w = group / total
    moved = {}
    for r in rects:                                   # the script's bars move to their new slots
        c = P(r) + S(r) / 2
        a = anchor[round(c, 9)]
        slot = offs.index(round(c - a, 6))
        new = a + (slot - (total - 1) / 2) * w
        moved[round(c, 9)] = new
        (r.set_y if h else r.set_x)(new - w / 2)
        (r.set_height if h else r.set_width)(w)
    old = np.array(list(moved))

    def follow(v):                                    # an x at the centre of a moved bar moves with it
        if not len(old):
            return v
        i = int(np.argmin(np.abs(old - v)))
        return moved[old[i]] if abs(old[i] - v) < 0.02 * w0 else v
    for c in ax.containers:                           # and the script's error bars with them
        if isinstance(c, ErrorbarContainer) and moved and not h and _eb_xy(c)[0] is not None:
            x = _eb_xy(c)[0]
            nx = np.array([follow(v) for v in x])
            if np.allclose(x, nx):
                continue
            if c[0] is not None:
                c[0].set_xdata(nx)
            for cap in c[1] or ():
                cap.set_xdata([follow(v) for v in cap.get_xdata()])
            for lc in c[2] or ():
                lc.set_segments([[(follow(p[0]), p[1]) for p in s] for s in lc.get_segments()])
    for k, s in enumerate(dodge):
        out[id(s)] = (w, (s0 + k - (total - 1) / 2) * w)
    return out


def _add_series(ax, ak, s, slot):
    """Draw one series added in the editor; returns the artists that belong in the legend."""
    typ, sid = s.get("type", "line"), str(s.get("id", "s"))
    n = min(len(s.get("x") or []), len(s.get("y") or []))
    h = typ == "bar" and _bar_horizontal(ax)          # bars added to a horizontal bar chart lie down too
    x, y = _positions(ax.yaxis if h else ax.xaxis, (s.get("x") or [])[:n]), _floats((s.get("y") or [])[:n])
    err = _floats(s["err"][:n]) if s.get("err") else None
    col, lab = s.get("color") or "#5677b5", s.get("label") or ""
    alpha = s.get("alpha", 1.0)
    parts, ex = [], x
    if typ == "bar":
        w, off = slot or (0.8, 0.0)
        ex = x + off
        verts = [[(xi - w / 2, 0), (xi - w / 2, yi), (xi + w / 2, yi), (xi + w / 2, 0)] for xi, yi in zip(ex, y)]
        if h:
            verts = [[(q[1], q[0]) for q in v] for v in verts]
        pc = PolyCollection(verts, facecolors=col, edgecolors=s.get("edge") or "none", linewidths=0.6, alpha=alpha,
                            label=lab, zorder=2)
        ax.add_collection(pc, autolim=True)
        parts.append(("bar", "collection", pc))
    elif typ == "area":
        o = np.argsort(x)
        pc = ax.fill_between(x[o], 0, y[o], color=col, alpha=s.get("alpha", 0.35), lw=0, label=lab, zorder=1.5)
        parts.append(("area", "collection", pc))
    elif typ == "scatter":
        sc = ax.scatter(x, y, s=s.get("size", 14), color=col, marker=s.get("marker") or "o", edgecolors="#1b1b1b",
                        linewidths=0.4, alpha=alpha, label=lab, zorder=3)
        parts.append(("points", "scatter", sc))
    else:
        o = np.argsort(x) if s.get("sort", True) else np.arange(n)
        if err is not None and s.get("band"):
            band = ax.fill_between(x[o], (y - err)[o], (y + err)[o], color=col, alpha=0.18, lw=0, zorder=1.5)
            parts.append(("band", "collection", band))
            err = None
        ln, = ax.plot(x[o], y[o], color=col, lw=s.get("lw", 1.2), alpha=alpha, marker=s.get("marker") or None,
                      ms=s.get("ms", 3.2), mec="#1b1b1b", mew=0.4, ls=s.get("ls", "-"), label=lab, zorder=3)
        parts.append(("line", "line", ln))
    if err is not None and typ != "area":
        if typ == "bar":
            cap = slot[0] * 0.18 if slot else 0.1
        else:
            cap = 0.15 * (np.min(np.diff(np.unique(x))) if len(np.unique(x)) > 1 else 1.0)
        segs = []
        for xi, yi, ei in zip(ex, y, err):
            if ei == ei and ei > 0:
                seg = [[(xi, yi - ei), (xi, yi + ei)], [(xi - cap, yi - ei), (xi + cap, yi - ei)],
                       [(xi - cap, yi + ei), (xi + cap, yi + ei)]]
                segs += [[(q[1], q[0]) for q in v] for v in seg] if h else seg
        lc = LineCollection(segs, colors="#1b1b1b", linewidths=0.6, zorder=4)
        ax.add_collection(lc, autolim=False)
        parts.append(("err", "collection", lc))
    for nm, kind, a in parts:
        a._tw_key = "%s/series/%s/%s" % (ak, sid, nm)
        a._tw_kind = kind
    return [a for nm, _, a in parts if lab and nm in ("bar", "area", "points", "line")] if s.get("legend", True) else []


def _rescale(ax):
    """Fit the view to the data again, on the axes the script left to autoscale."""
    if not (ax.get_autoscalex_on() or ax.get_autoscaley_on()):
        return
    ax.relim()
    for c in ax.collections:                          # relim leaves collections out
        if isinstance(c, PathCollection) and c.get_offset_transform() is ax.transData and len(c.get_offsets()):
            ax.update_datalim(c.get_offsets())
        elif isinstance(c, PolyCollection) and c.get_transform() is ax.transData:
            for p in c.get_paths():
                if len(p.vertices):
                    ax.update_datalim(p.vertices)
    ax.autoscale_view()


def _legend_with(ax, handles):
    """The chart's legend with the added series appended (a new one if the script drew none)."""
    lg = ax.get_legend()
    if lg is None:
        ax.legend(handles=handles)
        return
    old = list(getattr(lg, "legend_handles", None) or getattr(lg, "legendHandles", []))
    labels = [t.get_text() for t in lg.get_texts()]
    kw = dict(loc=lg._loc, frameon=lg.get_frame_on(), title=lg.get_title().get_text() or None)
    if getattr(lg, "_bbox_to_anchor", None) is not None:
        kw["bbox_to_anchor"] = lg._bbox_to_anchor
    if lg.get_texts():
        kw["fontsize"] = lg.get_texts()[0].get_fontsize()
    try:
        ax.legend(old + handles, labels + [h.get_label() for h in handles], ncols=getattr(lg, "_ncols", 1), **kw)
    except TypeError:                                  # matplotlib before 3.6
        ax.legend(old + handles, labels + [h.get_label() for h in handles], ncol=getattr(lg, "_ncols", 1), **kw)


def _data_layer(ax, ak, tw):
    """tw['data'] {sid: {x, y, err, z}} replaces plotted values; tw['series'] [{id, type, x, y, err, ...}] adds
    series (type bar, line, scatter, area)."""
    found = {sid: (kind, a) for sid, kind, a in _script_series(ax)}
    for sid, d in (tw.get("data") or {}).items():
        if sid in found and isinstance(d, dict):
            try:
                _set_series(ax, found[sid][0], found[sid][1], d)
            except (TypeError, ValueError, IndexError) as e:
                print("tweaks: data of %s %s not applied: %s" % (ak, sid, e))
    added = [s for s in tw.get("series") or [] if isinstance(s, dict)]
    slots = _bar_slots(ax, added)
    handles = []
    for s in added:
        try:
            handles += _add_series(ax, ak, s, slots.get(id(s)))
        except (TypeError, ValueError, IndexError) as e:
            print("tweaks: series %s of %s not drawn: %s" % (s.get("id"), ak, e))
    _rescale(ax)
    if handles:
        _legend_with(ax, handles)


def _border_of(t):
    p = t.get_bbox_patch() if isinstance(t, Text) else None
    return bool(p is not None and p.get_visible() and p.get_linewidth() > 0 and to_rgba(p.get_edgecolor())[3] > 0)


def _set_border(t, on):
    p = t.get_bbox_patch() if isinstance(t, Text) else None
    if p is not None and not on:
        p.set_edgecolor("none")
        p.set_linewidth(0)


def _set_legend_loc(lg, loc):
    if hasattr(lg, "set_loc"):
        lg.set_loc(loc)
    elif loc in Legend.codes:
        lg._loc = Legend.codes[loc]


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
    if kind in ("line", "patch", "collection", "scatter"):
        _style_line(a, tw)
    if kind in ("image", "collection", "scatter") and ("cmap" in tw or "clim" in tw):
        _style_cmap(a, tw)
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
        if tw.get("frame"):
            _set_frame(a, tw["frame"])
        if tw.get("tickdir") in ("in", "out", "inout"):
            a.tick_params(axis="both", which="both", direction=tw["tickdir"])
        if tw.get("grid") in ("none", "x", "y", "both"):
            _set_grid(a, tw["grid"])
        if tw.get("refs"):
            _add_refs(a, tw["refs"])
    elif kind in ("text", "axislabel"):
        if tw.get("border") is False:
            _set_border(a, False)
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
        if tw.get("weight") or tw.get("style"):
            for t in axis.get_major_ticks():
                for lab in (t.label1, t.label2):
                    if tw.get("weight"):
                        lab.set_fontweight(tw["weight"])
                    if tw.get("style"):
                        lab.set_fontstyle(tw["style"])
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
            if tw.get("style"):
                t.set_fontstyle(tw["style"])
        if "frame" in tw:
            a.set_frame_on(bool(tw["frame"]))
        if tw.get("loc"):
            _set_legend_loc(a, tw["loc"])
        if dx or dy:
            _shift_legend(a, dx, dy)
    elif kind == "scatter" and tw.get("scale", 1.0) != 1.0:
        a.set_sizes(a.get_sizes() * tw["scale"])
    if tw.get("visible") is False and kind != "figure":
        a.set_visible(False)


# ---- entry point ---------------------------------------------------------------------------------------------------

def _safely(fig, what, fn, *args):
    """One step of applying the edits or keying the figure. A step that fails is reported (render log and the keys
    file's meta.problems) and skipped; it never stops the figure. Scripts written by hand or by an agent draw things
    this module has not met, and one odd artist or one stale edit must not cost the whole render."""
    try:
        return fn(*args)
    except Exception as e:                             # noqa: BLE001
        msg = "%s (%s: %s)" % (what, type(e).__name__, str(e).splitlines()[0][:200] if str(e) else "")
        fig.__dict__.setdefault("_tw_problems", []).append(msg)
        print("tweaks: skipped %s" % msg)
        return None


def _freeze_layout(fig):
    """A figure laid out by constrained or tight layout gets that layout once, from the script's own drawing, and
    keeps it. Without this the layout runs again on every draw: an edit that changes a tick label moves the charts,
    their keys (positions in mm) change, and the edits no longer find them; charts dragged in the editor would also
    snap back when the figure is saved."""
    eng = fig.get_layout_engine() if hasattr(fig, "get_layout_engine") else None
    if eng is not None and type(eng).__name__ != "PlaceHolderLayoutEngine":
        fig.canvas.draw()
        fig.set_layout_engine("none")
    elif not hasattr(fig, "get_layout_engine") and (fig.get_constrained_layout() or fig.get_tight_layout()):
        fig.canvas.draw()                              # matplotlib before 3.6
        fig.set_constrained_layout(False)
        fig.set_tight_layout(False)


def _main_script():
    """The script that drew the figure: __main__'s file (also right under runpy or a wrapper), else argv[0]."""
    f = getattr(sys.modules.get("__main__"), "__file__", None) or (sys.argv[0] if sys.argv else "")
    return os.path.abspath(f) if f and f != "-c" else ""


def _style_palette():
    """Named hex colours of the project's style module, if one is loaded (shown as swatches in the editor)."""
    mod = sys.modules.get("style")
    out = {}
    for k, v in (vars(mod).items() if mod else []):
        if k.isupper() and isinstance(v, str) and v.startswith("#") and len(v) in (7, 9):
            out[k] = v.lower()[:7]
    return out


def _near_white(c):
    from matplotlib.colors import to_rgba
    r, g, b, a = to_rgba(c)
    return a > 0 and min(r, g, b) >= 0.9


def _house_defaults(fig):
    """House defaults, applied before the figure is keyed so the editor records them as the base style (user,
    2026-10-26): legend text is bold, and text carries no masking background (no white stroke halo, no white or
    near-white box without an edge). Boxes with an edge are drawn labels and stay. A weight or a box set in
    tweaks.json still wins, because the tweaks are applied afterwards."""
    from matplotlib import patheffects as pe
    legends = [ax.get_legend() for ax in fig.axes if ax.get_legend() is not None] + list(fig.legends) + [
        lg for sf, _ in _subfigs(fig) for lg in sf.legends]
    for lg in legends:
        for t in lg.get_texts():
            t.set_fontweight("bold")
        if lg.get_title() is not None and lg.get_title().get_text():
            lg.get_title().set_fontweight("bold")
    for t in _fig_texts(fig) + [t for ax in fig.axes for t in ax.texts]:
        effects = t.get_path_effects() or []
        keep = [e for e in effects
                if not (isinstance(e, pe.withStroke) and _near_white(e._gc.get("foreground", "black")))]
        if len(keep) != len(effects):
            t.set_path_effects(keep)
        _drop_masking_box(t)


def _drop_masking_box(t):
    """Remove a white or near-white box without a visible edge: it only masks what lies behind the text."""
    bp = t.get_bbox_patch() if isinstance(t, Text) else None
    if bp is not None and _near_white(bp.get_facecolor()) and (
            bp.get_linewidth() == 0 or bp.get_edgecolor()[3] == 0):
        t.set_bbox(None)


def apply(fig, here, stem, rerun_args=None):
    """Apply <stem>.tweaks.json to `fig` and write <stem>.tweak_keys.json. `rerun_args` are the command-line
    arguments that re-render only this figure (default: those of the current run)."""
    path = os.path.join(here, stem + ".tweaks.json")
    fig._tw_problems = []
    tweaks = (_safely(fig, "reading %s.tweaks.json" % stem, lambda: json.load(open(path, encoding="utf-8")))
              if os.path.exists(path) else None) or {}
    if not isinstance(tweaks, dict):
        tweaks = {}
    _safely(fig, "fixing the layout", _freeze_layout, fig)
    for k, v in sorted(tweaks.items()):            # charts inserted in the editor, first: they are edited like the rest
        if k.startswith("fig/added/") and isinstance(v, dict) and (v.get("add") or {}).get("type") == "chart" \
                and v.get("visible", True) is not False:
            _safely(fig, k, _draw_chart, fig, k, v, here)
    for ax, ak in _axkeys(fig).items():            # plotted values replaced and series added in the editor
        tw = tweaks.get(ak + "/axes") or {}
        if isinstance(tw, dict) and (tw.get("data") or tw.get("series")):
            _safely(fig, ak + " data", _data_layer, ax, ak, tw)
    _safely(fig, "house defaults", _house_defaults, fig)   # bold legends, no masking text backgrounds
    for k, v in sorted(tweaks.items()):            # texts and shapes inserted in the editor
        if k.startswith("fig/added/") and isinstance(v, dict) and v.get("add") and v["add"].get("type") != "chart":
            _safely(fig, k, _make_added, fig, k, v)
    for ax, ak in _axkeys(fig).items():            # axis ranges, scales and ticks first: the keys see the new ticks
        tw = tweaks.get(ak + "/axes") or {}
        if isinstance(tw, dict) and any(k in tw for k in STRUCT):
            _safely(fig, ak + " axis", _axis_structure, ax, tw)
    fig.canvas.draw()                              # lays out ticks and legends so they can be keyed and tagged
    renderer = fig.canvas.get_renderer()
    H_pt = fig.get_size_inches()[1] * 72
    to_svg = 72.0 / fig.dpi
    items = _items(fig)
    axk = _axkeys(fig)
    ids, palette, budget = {}, Counter(), [0]

    def key_one(it):
        a, gid = it["artist"], _gid(it["key"])
        rec = dict(key=it["key"], kind=it["kind"])
        if it.get("added"):
            rec["added"] = True
        if isinstance(a, Text):
            rec.update(rotation=round(a.get_rotation(), 2), ha=a.get_horizontalalignment(), va=a.get_verticalalignment())
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
            if _is_chart(a):                       # what Origin's axis dialog shows
                for s, sp in a.spines.items():     # the editor previews a frame change on these
                    sp.set_gid("%s_sp_%s" % (gid, s))
                rec.update(frame=_frame_of(a), tickdir=_tickdir_of(a), grid=_grid_of(a), sides=list(_label_sides(a)),
                           xlim=[float(v) for v in a.get_xlim()], ylim=[float(v) for v in a.get_ylim()],
                           xscale=a.get_xscale(), yscale=a.get_yscale(),
                           xminor=len(a.xaxis.get_minorticklocs()) > 0, yminor=len(a.yaxis.get_minorticklocs()) > 0)
        if it["kind"] in ("text", "axislabel") and _border_of(a):
            rec["border"] = True
        if it["kind"] == "legend":
            rec.update(frame=bool(a.get_frame_on()))
        if it["kind"] in ("ticks", "legend"):
            rec.update({k: it[k] for k in ("axis", "side") if k in it})
            if it["kind"] == "ticks" and it.get("members"):   # the script's label rotation; the editor's field starts here
                rec["rotation"] = round(it["members"][0].get_rotation(), 2)
            for j, m in enumerate(it.get("members", [])):
                mid = "%s_%d" % (gid, j)
                m.set_gid(mid)
                ids[mid] = dict(key=it["key"], kind=it["kind"], member=m.get_text(), group=gid,
                                **{k: it[k] for k in ("axis", "side") if k in it})
        if isinstance(a, Annotation) and a.arrow_patch is not None:
            a.arrow_patch.set_gid(gid + "_arrow")
            px, py = a._get_position_xy(renderer)          # the annotated point, which the leader keeps
            rec["arrow"] = [px * to_svg, H_pt - py * to_svg]
        if isinstance(a, Line2D) and it["kind"] == "line":
            rec.update(ls=_ls_name(a.get_linestyle()), marker=str(a.get_marker()), ms=round(a.get_markersize(), 2),
                       lw_pt=round(a.get_linewidth(), 2))
        elif it["kind"] in ("patch", "collection", "scatter") and hasattr(a, "get_linestyle"):
            ls = a.get_linestyle()
            rec["ls"] = _ls_name(ls[0] if isinstance(ls, list) and ls else ls)
            rec["lw_pt"] = round(float(max(np.atleast_1d(a.get_linewidth()), default=0)), 2)
        if it["kind"] in ("image", "collection", "scatter") and _is_mapped(a):
            rec.update(cmap=a.get_cmap().name, clim=[float(v) for v in a.get_clim()])
        if it["kind"] == "axes":
            x0, y0, w, h = a.get_position(original=True).bounds
            Wm, Hm = fig.get_size_inches() / MM
            rec["rect_mm"] = [round(x0 * Wm, 2), round(y0 * Hm, 2), round(w * Wm, 2), round(h * Hm, 2)]
            if getattr(a, "_tw_inset", None):
                rec["inset"] = a._tw_inset.rsplit("/", 1)[0]
            if _is_chart(a):                       # gridlines, so the editor can preview switching them off
                for n, axis in (("x", a.xaxis), ("y", a.yaxis)):
                    for j, gl in enumerate(axis.get_gridlines()):
                        gl.set_gid("%s_g%s%d" % (gid, n, j))
        if it["kind"] == "axes" and getattr(a, "_colorbar", None) is None:
            series = []                            # the plotted data, for the editor's data table
            for sid, kind, art in _script_series(a):
                t = _series_table(a, kind, art)
                cells = sum(len(r) for r in t["rows"])
                if len(t["rows"]) > DATA_ROWS or budget[0] + cells > DATA_CELLS:
                    t = dict(name=t["name"], n=len(t["rows"]), rows=[], too_long=True)
                else:
                    budget[0] += cells
                series.append(dict(sid=sid, kind=kind, **t))
            if series:
                rec["series"] = series
            rec["xcat"] = _categories(a.xaxis) is not None
        if it.get("added_series"):
            rec["added_series"] = True
        if it["kind"] == "axes" and getattr(a, "_colorbar", None) is not None:
            parent = getattr(a._colorbar.mappable, "axes", None)
            if parent is not None and parent in axk:
                rec.update(colorbar_of=axk[parent] + "/axes", cb_orient=a._colorbar.orientation)
        name = _name(a) if it["kind"] not in ("figure", "axes", "ticks") else ""
        if not name and it["kind"] == "patch":
            name = _bar_name(a)
        if name:
            rec["name"] = name
        cols = _colors_of(a) if it["kind"] != "figure" else []
        if cols:
            rec["colors"] = sorted(set(cols), key=cols.index)
        if it["kind"] == "figure":
            palette.update(_colors_of(fig))
        ids[gid] = rec
        return rec

    for it in items:                               # tag everything before anything changes
        if _safely(fig, "keying " + it["key"], key_one, it) is None and _gid(it["key"]) not in ids:
            ids[_gid(it["key"])] = dict(key=it["key"], kind=it["kind"])
    used, failed = set(), set()
    for it in items:                               # element-level first, then the figure-wide colour swap
        tw = tweaks.get(it["key"])
        if tw and isinstance(tw, dict):
            used.add(it["key"])
            if _safely(fig, it["key"], lambda: _apply(fig, it, tw) or True) is None:
                failed.add(it["key"])
    _safely(fig, "colour bars", _follow_colorbars, fig, tweaks, axk)
    fw = tweaks.get("fig/figure") or {}            # figure-wide frame, tick direction and text borders
    fw = fw if isinstance(fw, dict) else {}

    def figure_wide(it):
        own = tweaks.get(it["key"]) or {}
        if it["kind"] == "axes":
            if fw.get("frame") and "frame" not in own:
                _set_frame(it["artist"], fw["frame"])
            if fw.get("tickdir") in ("in", "out", "inout") and "tickdir" not in own and _is_chart(it["artist"]):
                it["artist"].tick_params(axis="both", which="both", direction=fw["tickdir"])
            if fw.get("grid") in ("none", "x", "y", "both") and "grid" not in own and _is_chart(it["artist"]):
                _set_grid(it["artist"], fw["grid"])
        elif it["kind"] in ("text", "axislabel") and fw.get("textbox") == "none" and "border" not in own:
            _set_border(it["artist"], False)
            _drop_masking_box(it["artist"])        # a borderless white box is the masking background the defaults remove

    for it in items:
        if fw:
            _safely(fig, "fig/figure on " + it["key"], figure_wide, it)
    W_pt, H_pt2 = fig.get_size_inches() * 72

    def where(ax, rec):
        try:
            ax.apply_aspect()
        except Exception:                          # noqa: BLE001
            pass
        x0, y0, x1, y1 = ax.get_position().extents
        rec["box"] = [round(x0 * W_pt, 2), round((1 - y1) * H_pt2, 2), round(x1 * W_pt, 2), round((1 - y0) * H_pt2, 2)]
        rec.update(xlim=[float(v) for v in ax.get_xlim()], ylim=[float(v) for v in ax.get_ylim()],
                   xscale=ax.get_xscale(), yscale=ax.get_yscale())

    for ax, ak in axk.items():                     # where each chart ends up, for the editor's data reader
        rec = ids.get(_gid(ak + "/axes"))
        if rec is not None and "xlim" in rec:
            _safely(fig, ak + " position", where, ax, rec)
    gm = fw.get("colors")
    if gm:
        _safely(fig, "fig/figure colours", _recolor, fig, {k.lower(): v for k, v in gm.items()})
    meta = dict(stem=stem, script=_main_script(),
                args=[str(x) for x in (sys.argv[1:] if rerun_args is None else rerun_args)],
                python=sys.executable, cwd=os.getcwd(), tweak_version=TWEAK_VERSION, size_mm=[round(v / MM, 2) for v in fig.get_size_inches()],
                palette=[c for c, _ in palette.most_common()], style_palette=_style_palette(),
                cmaps=_cmap_samples() if any("cmap" in v for v in ids.values()) else {})
    if fig._tw_problems:                           # the editor lists these after a render
        meta["problems"] = fig._tw_problems
    rows = {}                                      # each data series on one line, the rest one item per line
    for rec in ids.values():
        for i, t in enumerate(rec.get("series", [])):
            tok = "@series%d@" % len(rows)
            rows[tok], rec["series"][i] = json.dumps(t, ensure_ascii=False, separators=(",", ":")), tok
    text = json.dumps(dict(meta=meta, ids=ids), indent=0, ensure_ascii=False)
    for tok, r in rows.items():
        text = text.replace('"%s"' % tok, r, 1)
    open(os.path.join(here, stem + ".tweak_keys.json"), "w", encoding="utf-8").write(text)
    used |= getattr(fig, "_tw_charts", set())
    used -= failed
    stale = sorted(set(tweaks) - used - failed)
    if stale:
        print("tweaks: %d entr%s match no artist any more: %s" % (len(stale), "y" if len(stale) == 1 else "ies",
                                                                  "; ".join(stale)))
    if used:
        print("tweaks: applied %d hand adjustment%s from %s.tweaks.json" % (len(used), "" if len(used) == 1 else "s",
                                                                            stem))


# ---- checking a figure script ---------------------------------------------------------------------------------------

def _git_root(p):
    d = os.path.dirname(os.path.abspath(p)) if os.path.isfile(p) else os.path.abspath(p)
    while True:
        if os.path.exists(os.path.join(d, ".git")):
            return os.path.normcase(d)
        up = os.path.dirname(d)
        if up == d:
            return None
        d = up


def check(here, stem, rerun=False):
    """What stands between a figure and editing it in FigureTweak, with the fix for each finding. Returns the
    findings as (level, text): "error" (the editor cannot work on it), "warn" (some edits will not hold)."""
    import re
    import subprocess
    out, here = [], os.path.abspath(here)
    keys_p = os.path.join(here, stem + ".tweak_keys.json")
    if not os.path.exists(keys_p):
        return [("error", "%s.tweak_keys.json is missing: the script never reached tweak.apply(fig, HERE, %r). Call it "
                          "right before savefig (Page.save does), then render once." % (stem, stem))]
    keys = json.load(open(keys_p, encoding="utf-8"))
    meta, ids = keys.get("meta", {}), keys.get("ids", {})
    if str(meta.get("tweak_version", "0")) < TWEAK_VERSION:
        out.append(("warn", "rendered with tweak.py %s; this is %s. Copy this tweak.py next to the paper's style.py "
                            "(or onboard the folder again) and re-render." % (meta.get("tweak_version"), TWEAK_VERSION)))
    script = meta.get("script") or ""
    if not script or not os.path.isfile(script):
        out.append(("error", "the recorded script %r does not exist, so the editor cannot re-render. Run the figure "
                             "script as a file (python make_fig.py), not through -c, a notebook or exec." % script))
    elif (_git_root(script) != _git_root(keys_p) if _git_root(script) or _git_root(keys_p) else not (
            os.path.normcase(here).startswith(os.path.normcase(os.path.dirname(script)))
            or os.path.normcase(os.path.dirname(script)).startswith(os.path.normcase(here)))):
        out.append(("warn", "the keys file names a script in another folder or worktree (%s); it was copied. Render "
                            "this copy's own script once so the editor re-renders the right one." % script))
    for p in meta.get("problems") or []:
        out.append(("warn", "a step was skipped while rendering: %s" % p))
    texts = [r for r in ids.values() if r.get("kind") in ("text", "axislabel") and "member" not in r]
    svg_p = os.path.join(here, stem + ".svg")
    if os.path.exists(svg_p):
        svg = open(svg_p, encoding="utf-8", errors="replace").read()
        if texts and "<text" not in svg:
            out.append(("error", "the SVG holds no text elements: text was saved as glyph outlines, so no text can be "
                                 "edited. Set rcParams['svg.fonttype'] = 'none' before drawing."))
        m = re.search(r'<svg[^>]*\bwidth="([\d.]+)pt"[^>]*\bheight="([\d.]+)pt"', svg)
        if m and meta.get("size_mm"):
            w_mm, h_mm = float(m.group(1)) / 72 * 25.4, float(m.group(2)) / 72 * 25.4
            if abs(w_mm - meta["size_mm"][0]) > 1 or abs(h_mm - meta["size_mm"][1]) > 1:
                out.append(("error", "the SVG is %.0f x %.0f mm but the figure is %.0f x %.0f mm: it was cropped "
                                     "(savefig bbox_inches='tight' or pad_inches), so the editor's overlay lands in "
                                     "the wrong place. Save without bbox_inches; size the figure itself."
                            % (w_mm, h_mm, meta["size_mm"][0], meta["size_mm"][1])))
    else:
        out.append(("error", "%s.svg is missing: the editor shows the SVG. Save svg next to the png." % stem))
    if script and os.path.isfile(script):
        src = open(script, encoding="utf-8", errors="replace").read()
        if re.search(r"""bbox_inches\s*=\s*["']tight""", src) and not any("cropped" in t for _, t in out):
            out.append(("warn", "the script saves with bbox_inches='tight'; if the SVG gets cropped the editor's "
                                "overlay shifts. Size the figure instead."))
        if re.search(r"savefig\(.*facecolor\s*=\s*['\"]", src):
            out.append(("warn", "savefig(facecolor='...') overrides a background set in the editor; use "
                                "facecolor=fig.get_facecolor()."))
    unnamed = [t for r in ids.values() for t in r.get("series") or [] if isinstance(t, dict)
               and t.get("kind") in ("line", "scatter") and not t.get("name") and max(len(t.get("rows") or []),
                                                                                    t.get("n", 0)) >= 4]
    if len(unnamed) > 3:
        out.append(("warn", "%d lines/point sets have no label=, so the layer list shows them as 'line 3', "
                            "'scatter 0'. Give each series a label= (legend=False keeps it out of the legend)."
                    % len(unnamed)))
    dup = sorted({r["key"].rsplit("#", 1)[0] for r in texts if re.search(r"#\d+$", r["key"])
                  and isinstance(_num(r["key"].rsplit("#", 1)[0].split("/text/", 1)[-1].replace("−", "-")), str)})
    if dup:
        out.append(("warn", "the same string is drawn more than once (%s); those texts are told apart only by "
                            "drawing order, so reordering the script moves their edits. Prefer one text per string."
                    % ", ".join(k.split("/text/", 1)[-1] for k in dup[:5])))
    if rerun and script and os.path.isfile(script):
        import hashlib as _h

        def render():
            subprocess.run([meta.get("python") or sys.executable, script] + list(meta.get("args") or []),
                           cwd=meta.get("cwd") or os.path.dirname(script), capture_output=True)
            k = json.load(open(keys_p, encoding="utf-8"))
            png = os.path.join(here, stem + ".png")
            return ({r["key"] for r in k["ids"].values()},
                    _h.md5(open(png, "rb").read()).hexdigest() if os.path.exists(png) else None)
        (k1, h1), (k2, h2) = render(), render()
        if k1 != k2:
            out.append(("error", "two renders give different keys (%d differ, e.g. %s): the script is not "
                                 "deterministic (unseeded random data, set or dict order, timestamps in text), and "
                                 "edits will drift. Seed every generator (np.random.default_rng(0)) and keep text "
                                 "stable." % (len(k1 ^ k2), sorted(k1 ^ k2)[:3])))
        elif h1 != h2:
            out.append(("warn", "two renders give different PNGs with the same keys: something random is drawn. "
                                "Seed the generators so a re-render shows only the hand edits."))
    return out


def _main(argv):
    """python tweak.py --check FOLDER STEM [--rerun]: what keeps the figure from being edited in FigureTweak."""
    if len(argv) >= 3 and argv[0] == "--check":
        res = check(argv[1], argv[2], rerun="--rerun" in argv)
        for lvl, t in res:
            print("%-5s %s" % (lvl.upper(), t))
        print("OK    %s is ready for FigureTweak" % argv[2] if not res else
              "%d finding%s" % (len(res), "" if len(res) == 1 else "s"))
        return 1 if any(lvl == "error" for lvl, _ in res) else 0
    print(_main.__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
