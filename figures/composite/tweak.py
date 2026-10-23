"""Hand adjustments of a finished matplotlib figure, kept as data and re-applied on every render.

Every adjustable artist gets a stable key built from its axes (position in mm), its kind and, for text, its string.
`apply(fig, here, stem)` is called just before saving: it reads `<stem>.tweaks.json` next to the figure, applies the
adjustments, tags each artist with an SVG id and writes `<stem>.tweak_keys.json` (id -> key, kind) for the browser
editor (tools/figure_tweak.py). Keys are taken before anything moves, so they stay valid after an adjustment.

Kinds and what can be adjusted (lengths in mm, "size" and "scale" are factors):
    axes        a whole chart: dx_mm, dy_mm (move), dw_mm, dh_mm (resize, top-left corner fixed)
    text        texts, annotation labels, titles, panel letters: dx_mm, dy_mm, size, text
    axislabel   axis titles: dx_mm, dy_mm, size, text
    ticks       the tick or category labels of one axis: dx_mm (y) or dy_mm (x) moves the column, size,
                rename {old: new}
    legend      dx_mm, dy_mm, size, rename {old: new}
    scatter     marker set: scale (area); marker positions are data and never move

    {"ax@41,70,43,36/axes": {"dx_mm": 2.0},
     "ax@41,70,43,36/yticks": {"dx_mm": -1.0, "rename": {"STY": "space-time yield"}},
     "ax@41,70,43,36/text/21/63": {"dx_mm": 1.2, "size": 1.1}}
"""
import hashlib
import json
import os
from collections import Counter

from matplotlib.collections import PathCollection
from matplotlib.text import Annotation
from matplotlib.ticker import Formatter
from matplotlib.transforms import Bbox, ScaledTranslation

MM = 1 / 25.4
PT_PER_MM = 72 * MM


def _axkeys(fig):
    W, H = fig.get_size_inches() / MM
    seen, out = Counter(), {}
    for ax in fig.axes:
        x0, y0, w, h = ax.get_position(original=True).bounds
        k = "ax@%.0f,%.0f,%.0f,%.0f" % (x0 * W, y0 * H, w * W, h * H)
        seen[k] += 1
        out[ax] = k if seen[k] == 1 else "%s#%d" % (k, seen[k])      # twin axes share a position
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


def _items(fig):
    """One dict per adjustable item: key, kind, artist, and for ticks and legends their member texts."""
    items = []

    def texts_of(owner, texts, kind):
        seen = Counter()
        for t in texts:
            s = t.get_text()
            if not s.strip() or not t.get_visible():
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
    for ax, ak in _axkeys(fig).items():
        items.append(dict(key=ak + "/axes", kind="axes", artist=ax))
        texts_of(ak, ax.texts, "text")
        texts_of(ak, [ax.xaxis.label, ax.yaxis.label], "axislabel")
        for name, axis in (("x", ax.xaxis), ("y", ax.yaxis)):
            labs = _drawn_tick_labels(axis) if axis.get_visible() and ax.axison else []
            if labs:
                items.append(dict(key="%s/%sticks" % (ak, name), kind="ticks", artist=axis, axis=name,
                                  side=labs[0][1], members=[lab for lab, _ in labs]))
        legends_of(ak, [ax.legend_] if ax.legend_ is not None else [])
        for i, c in enumerate(x for x in ax.collections if isinstance(x, PathCollection)):
            if len(c.get_offsets()):
                items.append(dict(key="%s/scatter/%d" % (ak, i), kind="scatter", artist=c))
    return items


def _gid(key):
    return "tw_" + hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]


# ---- adjustments ---------------------------------------------------------------------------------------------------

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
    dx, dy, size = tw.get("dx_mm", 0.0), tw.get("dy_mm", 0.0), tw.get("size", 1.0)
    W, H = fig.get_size_inches() / MM
    if kind == "axes":
        x0, y0, w, h = a.get_position(original=True).bounds
        dw, dh = tw.get("dw_mm", 0.0), tw.get("dh_mm", 0.0)
        a.set_position(Bbox.from_bounds(x0 + dx / W, y0 + (dy - dh) / H, w + dw / W, h + dh / H))
    elif kind in ("text", "axislabel"):
        if "text" in tw:
            a.set_text(tw["text"])
        if size != 1.0:
            a.set_fontsize(a.get_fontsize() * size)
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
        if kw:
            ax.tick_params(axis=it["axis"], which="major", **kw)
    elif kind == "legend":
        for t in a.get_texts():
            if tw.get("rename") and t.get_text() in tw["rename"]:
                t.set_text(tw["rename"][t.get_text()])
            if size != 1.0:
                t.set_fontsize(t.get_fontsize() * size)
        if dx or dy:
            _shift_legend(a, dx, dy)
    elif kind == "scatter" and tw.get("scale", 1.0) != 1.0:
        a.set_sizes(a.get_sizes() * tw["scale"])


def apply(fig, here, stem):
    path = os.path.join(here, stem + ".tweaks.json")
    tweaks = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}
    fig.canvas.draw()                              # lays out ticks and legends so they can be keyed and tagged
    items = _items(fig)
    keys = {}
    for it in items:                               # tag everything before anything changes
        gid = _gid(it["key"])
        it["artist"].set_gid(gid)
        rec = dict(key=it["key"], kind=it["kind"])
        if it["kind"] in ("ticks", "legend"):
            rec.update({k: it[k] for k in ("axis", "side") if k in it})
            for j, m in enumerate(it.get("members", [])):
                mid = "%s_%d" % (gid, j)
                m.set_gid(mid)
                keys[mid] = dict(key=it["key"], kind=it["kind"], member=m.get_text(), group=gid,
                                 **{k: it[k] for k in ("axis", "side") if k in it})
        keys[gid] = rec
    used = set()
    for it in items:
        tw = tweaks.get(it["key"])
        if tw:
            used.add(it["key"])
            _apply(fig, it, tw)
    json.dump(keys, open(os.path.join(here, stem + ".tweak_keys.json"), "w", encoding="utf-8"), indent=0,
              ensure_ascii=False)
    stale = sorted(set(tweaks) - used)
    if stale:
        print("tweaks: %d entr%s match no artist any more: %s" % (len(stale), "y" if len(stale) == 1 else "ies",
                                                                  "; ".join(stale)))
    if used:
        print("tweaks: applied %d hand adjustment%s from %s.tweaks.json" % (len(used), "" if len(used) == 1 else "s",
                                                                            stem))
