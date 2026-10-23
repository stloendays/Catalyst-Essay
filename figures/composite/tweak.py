"""Hand adjustments of a finished matplotlib figure, kept as data and re-applied on every render.

Every text, annotation, legend and marker collection gets a stable key (its axes position in mm, its kind and, for
text, its string). `apply(fig, here, stem)` is called just before saving: it reads `<stem>.tweaks.json` next to the
figure, moves texts, annotation labels and legends by (dx_mm, dy_mm) and scales marker areas by `scale`, tags each
artist with an SVG id, and writes `<stem>.tweak_keys.json` (id -> key) for the browser editor
(tools/figure_tweak.py). Data markers are only resized, never moved: their positions are the data.

    {"ax@41,70,43,36/text/21/63": {"dx_mm": 1.2, "dy_mm": 0.0},
     "ax@41,70,43,36/scatter/3": {"scale": 1.3}}
"""
import hashlib
import json
import os
from collections import Counter

from matplotlib.collections import PathCollection
from matplotlib.legend import Legend
from matplotlib.text import Annotation, Text
from matplotlib.transforms import ScaledTranslation

MM = 1 / 25.4


def _axkey(fig, ax):
    x0, y0, w, h = ax.get_position().bounds
    W, H = fig.get_size_inches() / MM
    return "ax@%.0f,%.0f,%.0f,%.0f" % (x0 * W, y0 * H, w * W, h * H)


def _artists(fig):
    """(key, kind, artist) for every adjustable artist, in a deterministic order."""
    out = []
    groups = [("fig", fig.texts, fig.legends, [])]
    for ax in fig.axes:
        texts = [t for t in ax.texts if t.get_visible()] + [c for c in ax.get_children()
                                                           if isinstance(c, Annotation) and c not in ax.texts]
        texts += [lab for lab in (ax.xaxis.label, ax.yaxis.label) if lab.get_visible()]
        legs = [ax.legend_] if ax.legend_ is not None else []
        groups.append((_axkey(fig, ax), texts, legs, [c for c in ax.collections if isinstance(c, PathCollection)]))
    for owner, texts, legs, colls in groups:
        seen = Counter()
        for t in texts:
            s = t.get_text()
            if not s.strip():
                continue
            seen[s] += 1
            out.append(("%s/text/%s%s" % (owner, s, "" if seen[s] == 1 else "#%d" % seen[s]), "text", t))
        for i, lg in enumerate(legs):
            out.append(("%s/legend/%d" % (owner, i), "legend", lg))
        for i, c in enumerate(colls):
            if len(c.get_offsets()):
                out.append(("%s/scatter/%d" % (owner, i), "scatter", c))
    return out


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
        return x + renderer.points_to_pixels(dx * 72 * MM), y + renderer.points_to_pixels(dy * 72 * MM)
    lg._findoffset = find
    lg._legend_box.set_offset(find)          # the legend box holds the bound method taken at creation


def apply(fig, here, stem):
    path = os.path.join(here, stem + ".tweaks.json")
    tweaks = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}
    keys, used = {}, set()
    for key, kind, a in _artists(fig):
        gid = "tw_" + hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]
        a.set_gid(gid)
        keys[gid] = dict(key=key, kind=kind)
        tw = tweaks.get(key)
        if not tw:
            continue
        used.add(key)
        dx, dy = tw.get("dx_mm", 0.0), tw.get("dy_mm", 0.0)
        if kind == "text" and (dx or dy):
            _shift_text(fig, a, dx, dy)
        elif kind == "legend" and (dx or dy):
            _shift_legend(a, dx, dy)
        elif kind == "scatter" and tw.get("scale", 1.0) != 1.0:
            a.set_sizes(a.get_sizes() * tw["scale"])
    json.dump(keys, open(os.path.join(here, stem + ".tweak_keys.json"), "w", encoding="utf-8"), indent=0,
              ensure_ascii=False)
    stale = sorted(set(tweaks) - used)
    if stale:
        print("tweaks: %d entr%s match no artist any more: %s" % (len(stale), "y" if len(stale) == 1 else "ies",
                                                                  "; ".join(stale)))
    if used:
        print("tweaks: applied %d hand adjustment%s from %s.tweaks.json" % (len(used), "" if len(used) == 1 else "s",
                                                                            stem))
