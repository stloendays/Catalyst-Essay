"""Flat content thumbnails for the workflow row of Fig. 2a: each shows what a stage produces, in the plot palette.

Drawn on a millimetre canvas; (x, y) is the lower-left corner of a w x h tile.
"""
import numpy as np
from matplotlib.patches import FancyArrowPatch, Polygon, Rectangle

LW = 0.4


def _check(ax, x, y, s, color, lw=0.9):
    ax.plot([x - 0.5 * s, x - 0.15 * s, x + 0.55 * s], [y, y - 0.4 * s, y + 0.45 * s], color=color, lw=lw,
            solid_capstyle="round", solid_joinstyle="round", zorder=6)


def papers(ax, x, y, w, h, ink, line, accent, accent2):
    """Two pages: a paper with a figure, and its Supporting Information behind it."""
    pw, ph = 0.62 * w, 0.78 * h
    for k, (dx, dy, tag) in enumerate(((0.34 * w, 0.17 * h, "SI"), (0.06 * w, 0.06 * h, None))):
        x0, y0 = x + dx, y + dy
        f = 0.16 * pw
        ax.add_patch(Polygon([(x0, y0), (x0 + pw, y0), (x0 + pw, y0 + ph - f), (x0 + pw - f, y0 + ph),
                              (x0, y0 + ph)], closed=True, fc="white", ec=ink, lw=LW, zorder=4 + 2 * k))
        if tag:
            ax.text(x0 + pw - 0.12 * pw, y0 + 0.1 * ph, tag, fontsize=4.2, fontweight="bold", ha="right",
                    va="bottom", color=ink, zorder=5)
        for i in range(3):
            yy = y0 + ph * (0.86 - 0.09 * i)
            ax.plot([x0 + 0.12 * pw, x0 + (0.7 if i < 2 else 0.5) * pw], [yy, yy], color=line, lw=0.5,
                    zorder=5 + 2 * k)
        if not tag:                                   # a small figure on the paper
            bx, by, bw, bh = x0 + 0.14 * pw, y0 + 0.12 * ph, 0.72 * pw, 0.42 * ph
            ax.add_patch(Rectangle((bx, by), bw, bh, fc="none", ec=line, lw=0.35, zorder=7))
            for j, (hh, c) in enumerate(((0.45, accent), (0.8, accent2), (0.6, accent), (0.3, accent2))):
                ax.add_patch(Rectangle((bx + bw * (0.1 + 0.21 * j), by), bw * 0.14, bh * hh, fc=c, ec="none",
                                       zorder=7))


def table(ax, x, y, w, h, ink, line, accent):
    """An extracted table with one value highlighted and its source tag."""
    tw, th = 0.9 * w, 0.56 * h
    x0, y0 = x + 0.05 * w, y + 0.36 * h
    ax.add_patch(Rectangle((x0, y0), tw, th, fc="white", ec=ink, lw=LW, zorder=4))
    ax.add_patch(Rectangle((x0, y0 + th * 0.78), tw, th * 0.22, fc=line, ec="none", zorder=4.1))
    for i in (1, 2):
        ax.plot([x0 + tw * i / 3] * 2, [y0, y0 + th], color=ink, lw=0.3, zorder=5)
    for j in (1, 2, 3):
        ax.plot([x0, x0 + tw], [y0 + th * 0.78 * j / 4 + th * (0.22 if False else 0)] * 2, color=ink, lw=0.25,
                zorder=5)
    cx0, cy0 = x0 + tw / 3, y0 + th * 0.78 * 1 / 4
    ax.add_patch(Rectangle((cx0, cy0), tw / 3, th * 0.78 / 4, fc=accent, ec=ink, lw=0.4, zorder=5.5))
    tx, ty = x + 0.5 * w, y + 0.12 * h
    ax.plot([cx0 + tw / 6, tx], [cy0, ty + 0.07 * h], color=ink, lw=0.35, zorder=5)
    ax.text(tx, ty, "Table 2, p. 5", fontsize=3.8, ha="center", va="center", color=ink, zorder=6,
            bbox=dict(boxstyle="round,pad=0.25,rounding_size=0.6", fc="white", ec=ink, lw=0.35))


def selfcheck(ax, x, y, w, h, ink, ok):
    """Frozen versus reproduced result for the three hand-built systems, each ticked."""
    rows = ["NH$_3$", "MeOH", "Au/TiO$_2$"]
    ax.text(x + 0.52 * w, y + 0.93 * h, "frozen = rerun", fontsize=3.9, ha="center", va="center", color=ink)
    for i, lab in enumerate(rows):
        yy = y + h * (0.70 - 0.24 * i)
        ax.text(x + 0.05 * w, yy, lab, fontsize=4.4, ha="left", va="center", color=ink)
        ax.plot([x + 0.55 * w, x + 0.72 * w], [yy, yy], color=ink, lw=0.3, ls=(0, (1, 1)))
        _check(ax, x + 0.85 * w, yy, 0.12 * w, ok)


def chain(ax, x, y, w, h, ink, c1, c2, c3):
    """Kinetics (volcano), process (loop), cost (bar): the three models every candidate passes through."""
    cy = [y + h * 0.80, y + h * 0.47, y + h * 0.13]
    gw, gh = 0.62 * w, 0.2 * h
    gx = x + 0.19 * w
    u = np.linspace(0, 1, 40)
    v = 1 - 1.6 * np.abs(u - 0.55) ** 1.1
    ax.plot(gx + gw * u, cy[0] - gh / 2 + gh * np.clip(v, 0, 1), color=c1, lw=0.8, zorder=5)
    ax.plot([gx, gx, gx + gw], [cy[0] + gh / 2, cy[0] - gh / 2, cy[0] - gh / 2], color=ink, lw=0.35, zorder=5)
    lx0, lx1 = gx + 0.08 * gw, gx + 0.92 * gw
    ax.add_patch(Rectangle((lx0, cy[1] - gh / 2), 0.16 * gw, gh, fc=c2, ec=ink, lw=0.35, zorder=5))
    ax.add_patch(Rectangle((lx1 - 0.14 * gw, cy[1] - gh * 0.35), 0.14 * gw, gh * 0.7, fc="white", ec=ink, lw=0.35,
                           zorder=5))
    ax.plot([lx0 + 0.08 * gw, lx0 + 0.08 * gw, lx1 - 0.07 * gw, lx1 - 0.07 * gw],
            [cy[1] + gh / 2, cy[1] + gh * 0.75, cy[1] + gh * 0.75, cy[1] + gh * 0.35], color=ink, lw=0.4, zorder=4)
    ax.plot([lx1 - 0.07 * gw, lx1 - 0.07 * gw, lx0 + 0.08 * gw, lx0 + 0.08 * gw],
            [cy[1] - gh * 0.35, cy[1] - gh * 0.75, cy[1] - gh * 0.75, cy[1] - gh / 2], color=ink, lw=0.4, zorder=4)
    yb = cy[2] - gh / 2
    for j, (f, c) in enumerate(((0.45, c1), (0.25, c2), (0.2, c3))):
        ax.add_patch(Rectangle((gx + 0.3 * gw, yb + gh * 1.2 * sum(q for q, _ in ((0.45, 0), (0.25, 0), (0.2, 0))[:j])),
                               0.4 * gw, gh * 1.2 * f, fc=c, ec=ink, lw=0.3, zorder=5))
    for k in range(2):
        ax.add_patch(FancyArrowPatch((x + 0.5 * w, cy[k] - gh * 0.62), (x + 0.5 * w, cy[k + 1] + gh * 0.95),
                                     arrowstyle="-|>", mutation_scale=3.5, lw=0.4, color=ink, zorder=5))


def bump(ax, x, y, w, h, ink, pale, lead, win):
    """Laboratory rank against plant-cost rank: the laboratory leader drops, another catalyst rises to first."""
    xl, xr = x + 0.22 * w, x + 0.82 * w
    ys = [y + h * (0.80 - 0.2 * i) for i in range(4)]
    perm = {0: 2, 1: 1, 2: 0, 3: 3}
    ax.text(xl, y + h * 0.97, "lab", fontsize=4.2, ha="center", va="center", color=ink)
    ax.text(xr, y + h * 0.97, "plant", fontsize=4.2, ha="center", va="center", color=ink)
    for i in range(4):
        j = perm[i]
        col = lead if i == 0 else (win if j == 0 else pale)
        ax.plot([xl, xr], [ys[i], ys[j]], color=col, lw=0.9 if col != pale else 0.6, zorder=4 + (col != pale))
        for xx, yy in ((xl, ys[i]), (xr, ys[j])):
            ax.add_patch(Rectangle((xx - 0.05 * w, yy - 0.035 * h), 0.1 * w, 0.07 * h, fc=col if col != pale else
                                   "white", ec=ink, lw=0.3, zorder=6))
    for k, yy in enumerate(ys):
        ax.text(x + 0.06 * w, yy, str(k + 1), fontsize=4.0, ha="center", va="center", color=ink)


def bound(ax, x, y, w, h, ink, pale, keep):
    """Candidates against a cost lower bound: only those whose bound beats the best cost found get the full run."""
    rng = np.random.default_rng(7)
    xs = x + w * (0.12 + 0.76 * rng.random(18))
    ys = y + h * (0.12 + 0.76 * rng.random(18))
    yl = y + 0.38 * h
    ax.plot([x + 0.05 * w, x + 0.95 * w], [yl, yl], color=ink, lw=0.5, ls=(0, (2, 1)), zorder=5)
    for xx, yy in zip(xs, ys):
        c = keep if yy < yl else pale
        ax.add_patch(Rectangle((xx - 0.035 * w, yy - 0.035 * h), 0.07 * w, 0.07 * h, fc=c, ec=ink, lw=0.25,
                               zorder=6))
