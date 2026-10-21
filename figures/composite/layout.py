"""House legend boxes, and a check that nothing in the figure overlaps.

A legend frame is allowed and often better than direct labels once a panel
carries more than four or five series. What is not allowed is a legend sitting
on the data or on another label, so `audit` measures it instead of trusting the
eye: it draws the figure, collects every text and legend bounding box, and
reports any pair that genuinely intersects.

Call `audit(pg.fig)` right before `pg.save(...)`. It prints what it found and
returns the list, so a build can be made to fail on a regression.
"""
import itertools

from matplotlib.text import Text

INK, MID, LINE = "#1B1B1B", "#6B6F76", "#D6D6D6"

# Ticks and their axis label are laid out by matplotlib and are allowed to sit
# close; only real collisions between things we placed are interesting.
MIN_FRAC = 0.18            # ignore an intersection smaller than this share of
                           # the smaller box -- antialiasing and descenders touch


def legend(ax, handles=None, labels=None, loc="lower right", ncol=1,
           fontsize=5.4, title=None, frame=True, **kw):
    """A legend in the house style: hairline frame, white fill, tight padding."""
    kw.setdefault("handlelength", 1.5)
    kw.setdefault("handletextpad", 0.45)
    kw.setdefault("labelspacing", 0.32)
    kw.setdefault("columnspacing", 0.9)
    kw.setdefault("borderpad", 0.42)
    kw.setdefault("borderaxespad", 0.5)
    lg = (ax.legend(handles, labels, loc=loc, ncol=ncol, fontsize=fontsize, **kw)
          if handles is not None else
          ax.legend(loc=loc, ncol=ncol, fontsize=fontsize, **kw))
    fr = lg.get_frame()
    fr.set_linewidth(0.5 if frame else 0.0)
    fr.set_edgecolor(LINE if frame else "none")
    fr.set_facecolor("white")
    fr.set_alpha(1.0 if frame else 0.0)
    lg.set_zorder(6)
    if title:
        lg.set_title(title, prop=dict(size=fontsize, weight="bold"))
        lg.get_title().set_color(INK)
    for t in lg.get_texts():
        t.set_color(INK)
    return lg


def _drawn_ticklabels(axis):
    """Tick labels that are actually drawn: inside the view interval.

    get_ticklabels() also returns labels for tick locations beyond the limits,
    which matplotlib never renders; auditing them reports collisions with text
    that is not there (a phantom "1.6" on an axis that stops at 1.52).
    """
    lo, hi = sorted(axis.get_view_interval())
    tol = 1e-9 * max(abs(hi - lo), 1e-12)
    out = []
    for tick in axis.get_major_ticks():
        loc = tick.get_loc()
        if loc is None or not (lo - tol <= loc <= hi + tol):
            continue
        for lab in (tick.label1, tick.label2):
            if lab.get_visible():
                out.append(lab)
    return out


def _all_axes(fig):
    """Every Axes, including secondary axes, which live in child_axes."""
    seen, out = set(), []
    stack = list(fig.axes)
    while stack:
        ax = stack.pop(0)
        if id(ax) in seen:
            continue
        seen.add(id(ax))
        out.append(ax)
        stack.extend(getattr(ax, "child_axes", []))
    return out


def _boxes(fig):
    """(name, kind, owner, bbox) for every visible piece of text in the figure.

    Axis labels, titles and tick labels are included. An earlier version
    collected only placed text and legends, and missed a note sitting squarely
    on a neighbouring panel's y-axis label.
    """
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    out = []

    def add(t, kind, owner):
        if t is None or not t.get_visible() or not t.get_text().strip():
            return
        out.append(("%s:%s" % (kind, _short(t)), kind, owner,
                    t.get_window_extent(r)))

    for ax in _all_axes(fig):
        o = id(ax)
        for t in ax.texts:
            add(t, "text", o)
        for t in (ax.title, getattr(ax, "_left_title", None),
                  getattr(ax, "_right_title", None)):
            add(t, "title", o)
        # An axis switched off (every Page.canvas) still owns tick-label
        # objects, and they report visible; they are never drawn.
        if not ax.axison:
            lg = ax.get_legend()
            if lg is not None and lg.get_visible():
                out.append(("legend", "legend", o, lg.get_window_extent(r)))
            continue
        add(ax.xaxis.label, "axlabel", o)
        add(ax.yaxis.label, "axlabel", o)
        for axis in (ax.xaxis, ax.yaxis):
            for t in _drawn_ticklabels(axis):
                add(t, "tick", o)
        lg = ax.get_legend()
        if lg is not None and lg.get_visible():
            out.append(("legend", "legend", o, lg.get_window_extent(r)))
    for t in fig.texts:
        if isinstance(t, Text):
            add(t, "figtext", "fig")
    return out


# Pairs matplotlib lays out itself, within one Axes, are its business.
_MANAGED = {"tick", "axlabel"}


def _short(t, n=28):
    s = " ".join(t.get_text().split())
    return s if len(s) <= n else s[:n - 1] + "…"


def audit(fig, min_frac=MIN_FRAC, verbose=True):
    """Report text/legend boxes that intersect. Returns a list of collisions."""
    boxes = _boxes(fig)
    hits = []
    for (na, ka, oa, ba), (nb, kb, ob, bb) in itertools.combinations(boxes, 2):
        if oa == ob and ka in _MANAGED and kb in _MANAGED:
            continue
        x0, x1 = max(ba.x0, bb.x0), min(ba.x1, bb.x1)
        y0, y1 = max(ba.y0, bb.y0), min(ba.y1, bb.y1)
        if x1 <= x0 or y1 <= y0:
            continue
        inter = (x1 - x0) * (y1 - y0)
        smaller = min(ba.width * ba.height, bb.width * bb.height)
        if smaller <= 0:
            continue
        frac = inter / smaller
        if frac >= min_frac:
            hits.append((frac, na, nb))
    hits.sort(reverse=True)
    if verbose:
        if hits:
            print("  OVERLAP  %d pair(s):" % len(hits))
            for frac, na, nb in hits:
                print("    %3.0f%%  %-34s  x  %s" % (100 * frac, na, nb))
        else:
            print("  overlap audit clean (%d boxes)" % len(boxes))
    return hits
