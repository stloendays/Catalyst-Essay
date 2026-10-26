"""Advanced chart types in the house style (matplotlib + numpy + scipy only; no seaborn here).

Ideas taken from the hiplot.cn catalogue (ggstatsplot, raincloud, corrplot, ComplexHeatmap, UpSet,
Taylor diagram, ternary, forest, ridge, parallel coordinates, waterfall...) and rebuilt for this
machine's figures: Arial, ticks in, one red per panel, live text, points shown rather than hidden.
Each function draws into axes you already placed with `style.Page`, so layout stays in millimetres.
The chart-to-claim map is `references/advanced-charts.md`; `advanced_gallery.py` builds every one.

    import advanced as A
    A.raincloud(ax, [a, b, c], ["ZFP", "SZ3", "SPERR"], highlight=1)
    A.stats_line(ax, A.compare(a, b))            # "Welch t(21.4) = 3.10, p = 0.005, g = 1.21 [0.43, 2.06]"
    A.forest(ax, names, est, lo, hi, null=0, pooled=(m, l, h))
    m = A.corr_triangle(ax, R, names); A.cbar(pg.ax(...), m, "Pearson r")

Big point clouds are drawn `rasterized=True` so the SVG stays small; axes, ticks and text stay vector.
"""
import numpy as np
from matplotlib.collections import LineCollection
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, Polygon, Rectangle
from matplotlib.ticker import FuncFormatter
from scipy import stats

import style as _S

# Project style.py copies diverge in naming (QSQ calls the blue BLUE, AI4S calls it RU); take what exists.
INK, MID, GRID, LINE, OTHER, RED = (_S.INK, _S.MID, _S.GRID, _S.LINE, _S.OTHER, _S.RED)
DARK_B = getattr(_S, "DARK_B", "#5A6480")
DARK_G = getattr(_S, "DARK_G", "#5E7A52")
PALE_B = getattr(_S, "PALE_B", "#C6CCDC")
RU = getattr(_S, "RU", getattr(_S, "BLUE", "#7789B7"))

# Signed quantities: warm = increase / positive, cool = decrease / negative (QSQ convention).
POS, NEG = "#D8894E", "#4F86B0"
# Diverging, colourblind-safe (no red/green pair), white at the null. State the null in the caption.
DIVERGE = LinearSegmentedColormap.from_list(
    "house_div", ["#2F4B7C", "#4F86B0", "#A9C4DC", "#F7F7F7", "#EFC2A0", "#D8894E", "#9C4A1E"])
# Sequential, single hue, light -> dark. Never a rainbow for ordered data.
SEQ = LinearSegmentedColormap.from_list("house_seq", ["#F4F5F8", "#C6CCDC", "#7789B7", "#4A5680", "#232A45"])
SEQ_G = LinearSegmentedColormap.from_list("house_seq_g", ["#F4F6F2", "#CBD7C3", "#89AA7B", "#5E7A52", "#2F3F28"])

ANNOT = 5.6          # in-panel annotation size, pt
SMALL = 5.3          # the floor; nothing smaller


def _fmt_minus(s):
    return s.replace("-", "−")


def _clean(ax, left=True, bottom=True):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.spines["left"].set_visible(left)
    ax.spines["bottom"].set_visible(bottom)
    ax.tick_params(which="both", top=False, right=False, left=left, bottom=bottom)


def _colors(n, colors, highlight):
    if colors is None:
        colors = [OTHER] * n if highlight is not None else [RU] * n
    colors = list(colors)
    if highlight is not None:
        for h in np.atleast_1d(highlight):
            colors[int(h)] = RED
    return colors


def _dark(c, f=0.62):
    from matplotlib.colors import to_rgb
    r, g, b = to_rgb(c)
    return (r * f, g * f, b * f)


# --------------------------------------------------------------------------- statistics

def hedges_g(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    na, nb = len(a), len(b)
    sp = np.sqrt(((na - 1) * a.var(ddof=1) + (nb - 1) * b.var(ddof=1)) / (na + nb - 2))
    d = (b.mean() - a.mean()) / sp
    return d * (1 - 3 / (4 * (na + nb) - 9))


def compare(a, b, test="welch", n_boot=4000, seed=0, paired=False):
    """Two-group comparison with an effect size and its bootstrap 95 % CI (ggbetweenstats-style).

    test: "welch" (Welch t), "mw" (Mann-Whitney U), or paired=True for a paired t-test.
    The effect size is Hedges' g of b relative to a (paired: mean difference / s.d. of differences).
    """
    a, b = np.asarray(a, float), np.asarray(b, float)
    rng = np.random.default_rng(seed)
    if paired:
        d = b - a
        t = stats.ttest_rel(b, a)
        g = d.mean() / d.std(ddof=1)
        boots = [(lambda x: x.mean() / x.std(ddof=1))(rng.choice(d, len(d))) for _ in range(n_boot)]
        name, stat, df = "paired t", t.statistic, len(d) - 1
    elif test == "mw":
        u = stats.mannwhitneyu(b, a, alternative="two-sided")
        t, name, stat, df = u, "Mann–Whitney U", u.statistic, None
        g = hedges_g(a, b)
        boots = [hedges_g(rng.choice(a, len(a)), rng.choice(b, len(b))) for _ in range(n_boot)]
    else:
        t = stats.ttest_ind(b, a, equal_var=False)
        va, vb = a.var(ddof=1) / len(a), b.var(ddof=1) / len(b)
        df = (va + vb) ** 2 / (va ** 2 / (len(a) - 1) + vb ** 2 / (len(b) - 1))
        name, stat = "Welch t", t.statistic
        g = hedges_g(a, b)
        boots = [hedges_g(rng.choice(a, len(a)), rng.choice(b, len(b))) for _ in range(n_boot)]
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return dict(test=name, stat=float(stat), df=df, p=float(t.pvalue), g=float(g), lo=float(lo),
                hi=float(hi), n=(len(a), len(b)))


def p_text(p):
    if p < 1e-4:
        return "p < 10$^{-4}$"
    if p < 0.001:
        return "p = %.1e" % p
    return "p = %.3f" % p if p < 0.1 else "p = %.2f" % p


def stats_line(ax, res, x=0.0, y=1.02, size=ANNOT, two_lines=True, **kw):
    """Statistics above the panel: test, statistic, p; then effect size with 95 % CI and n."""
    df = "(%.1f)" % res["df"] if res.get("df") is not None else ""
    sep = "\n" if two_lines else ", "
    s = "%s%s = %.2f, %s%s$\\mathit{g}$ = %.2f [%.2f, %.2f], $\\mathit{n}$ = %d/%d" % (
        res["test"], df, res["stat"], p_text(res["p"]), sep, res["g"], res["lo"], res["hi"], *res["n"])
    return ax.text(x, y, _fmt_minus(s), transform=ax.transAxes, fontsize=size, ha="left", va="bottom",
                   color=INK, **kw)


def bracket(ax, p1, p2, level, text, orient="v", tip=None, size=ANNOT, color=INK):
    """Significance bracket between group positions p1 and p2 at value `level`."""
    if tip is None:
        lo, hi = ax.get_ylim() if orient == "v" else ax.get_xlim()
        tip = 0.02 * (hi - lo)
    xs = [p1, p1, p2, p2]
    ys = [level - tip, level, level, level - tip]
    if orient == "v":
        ax.plot(xs, ys, color=color, lw=0.5, clip_on=False)
        ax.text((p1 + p2) / 2, level + 0.4 * tip, text, ha="center", va="bottom", fontsize=size, color=color)
    else:
        ax.plot(ys, xs, color=color, lw=0.5, clip_on=False)
        ax.text(level + 0.4 * tip, (p1 + p2) / 2, text, ha="left", va="center", fontsize=size, color=color,
                rotation=-90)


# --------------------------------------------------------------------------- distributions

def swarm(values, d_val, d_off, max_off=None):
    """Deterministic beeswarm offsets: points closer than d_val in value are pushed apart by d_off steps.

    Offsets alternate +/-, smallest first, so a symmetric column grows around the centre. Never sort-fan:
    spreading sorted values across the width draws a trend along an axis that means nothing.
    """
    v = np.asarray(values, float)
    order = np.argsort(v)
    off = np.zeros(len(v))
    placed = []
    for i in order:
        near = [(v[j], off[j]) for j in placed if abs(v[j] - v[i]) < d_val]
        k = 0
        while True:
            cand = (k + 1) // 2 * (1 if k % 2 else -1) * d_off if k else 0.0
            if all(((vv - v[i]) / d_val) ** 2 + ((oo - cand) / d_off) ** 2 >= 0.999 for vv, oo in near):
                break
            k += 1
        if max_off is not None:
            cand = float(np.clip(cand, -max_off, max_off))
        off[i] = cand
        placed.append(i)
    return off


def _kde(x, grid, bw=None):
    x = np.asarray(x, float)
    if len(x) < 2 or np.ptp(x) == 0:
        return np.zeros_like(grid)
    return stats.gaussian_kde(x, bw_method=bw)(grid)


def raincloud(ax, data, labels, colors=None, highlight=None, orient="h", cloud=0.42, box_w=0.07,
              rain=0.26, point_size=5.0, bw=None, value_label=None, show_mean=False, positions=None,
              point_alpha=1.0, swarm_d=0.018, bounds=(-np.inf, np.inf)):
    """Half-violin (cloud) + slim box + every point (rain). Groups at integer positions.
    `bounds` clips each cloud to a physical range (e.g. log10(1 - R^2) <= 0); the KDE tail must not
    draw values the quantity cannot take.

    orient "h": groups on y, top to bottom in list order; "v": groups on x, left to right.
    The box shows median and IQR, whiskers to 1.5 IQR. Points use a deterministic swarm.
    """
    n = len(data)
    colors = _colors(n, colors, highlight)
    allv = np.concatenate([np.asarray(d, float) for d in data])
    span = np.ptp(allv) or 1.0
    grid = np.linspace(allv.min() - 0.08 * span, allv.max() + 0.08 * span, 300)
    if positions is not None:
        pos = np.asarray(positions, float)
    else:
        pos = np.arange(n)[::-1] if orient == "h" else np.arange(n)

    def xy(p, v):
        return (v, p) if orient == "h" else (p, v)

    for d, p, c in zip(data, pos, colors):
        d = np.asarray(d, float)
        dens = _kde(d, grid, bw)
        dens = dens / (dens.max() or 1) * cloud
        lo, hi = np.percentile(d, [0.5, 99.5])
        keep = (grid >= max(lo - 0.05 * span, bounds[0])) & (grid <= min(hi + 0.05 * span, bounds[1]))
        g, h = grid[keep], dens[keep]
        pv = np.r_[g, g[::-1]]
        pp = np.r_[p + box_w * 0.9 + h, np.full(len(g), p + box_w * 0.9)]
        X, Y = xy(pp, pv)
        ax.fill(X, Y, color=c, alpha=0.55, lw=0, zorder=2)
        ax.plot(*xy(p + box_w * 0.9 + h, g), color=_dark(c, 0.8), lw=0.5, zorder=3)
        q1, med, q3 = np.percentile(d, [25, 50, 75])
        iqr = q3 - q1
        wl, wh = d[d >= q1 - 1.5 * iqr].min(), d[d <= q3 + 1.5 * iqr].max()
        ax.plot(*xy([p, p], [wl, q1]), color=INK, lw=0.5, zorder=3)
        ax.plot(*xy([p, p], [q3, wh]), color=INK, lw=0.5, zorder=3)
        bx, by = xy(p - box_w / 2, q1)
        bw_, bh = (iqr, box_w) if orient == "h" else (box_w, iqr)
        ax.add_patch(Rectangle((bx, by), bw_, bh, fc="white", ec=INK, lw=0.5, zorder=4))
        ax.plot(*xy([p - box_w / 2, p + box_w / 2], [med, med]), color=INK, lw=0.9, zorder=5,
                solid_capstyle="butt")
        if show_mean:
            ax.plot(*xy(p, d.mean()), marker="D", ms=2.2, mfc="white", mec=INK, mew=0.5, zorder=6)
        off = swarm(d, d_val=swarm_d * span, d_off=0.035, max_off=rain / 2)
        base = p - box_w * 0.9 - rain / 2
        X, Y = xy(base + off, d)
        ax.scatter(X, Y, s=point_size, color=c, edgecolor=_dark(c), lw=0.3, zorder=4, alpha=point_alpha)
    if orient == "h":
        ax.set_yticks(pos)
        ax.set_yticklabels(labels)
        ax.set_ylim(pos.min() - box_w - rain - 0.12, pos.max() + box_w + cloud + 0.08)
        ax.tick_params(axis="y", length=0)
        if value_label:
            ax.set_xlabel(value_label)
        _clean(ax, left=False)
    else:
        ax.set_xticks(pos)
        ax.set_xticklabels(labels)
        ax.set_xlim(pos.min() - box_w - rain - 0.12, pos.max() + box_w + cloud + 0.08)
        ax.tick_params(axis="x", length=0)
        if value_label:
            ax.set_ylabel(value_label)
        _clean(ax, bottom=False)
    return pos


def violin_box_points(ax, data, labels, colors=None, highlight=None, width=0.7, point_size=5.0,
                      value_label=None, bw=None, show_mean=True, fmt_mean="%.2f"):
    """ggbetweenstats-style: full violin, slim box, every point, mean marked (value under the tick)."""
    n = len(data)
    colors = _colors(n, colors, highlight)
    allv = np.concatenate([np.asarray(d, float) for d in data])
    span = np.ptp(allv) or 1.0
    grid = np.linspace(allv.min() - 0.1 * span, allv.max() + 0.1 * span, 300)
    for p, (d, c) in enumerate(zip(data, colors)):
        d = np.asarray(d, float)
        dens = _kde(d, grid, bw)
        dens = dens / (dens.max() or 1) * width / 2
        keep = dens > 0.01 * width
        g, h = grid[keep], dens[keep]
        ax.fill(np.r_[p - h, (p + h)[::-1]], np.r_[g, g[::-1]], color=c, alpha=0.28, lw=0, zorder=1)
        ax.plot(p - h, g, color=_dark(c, 0.8), lw=0.4, zorder=2)
        ax.plot(p + h, g, color=_dark(c, 0.8), lw=0.4, zorder=2)
        q1, med, q3 = np.percentile(d, [25, 50, 75])
        ax.add_patch(Rectangle((p - 0.05, q1), 0.1, q3 - q1, fc="white", ec=INK, lw=0.5, zorder=3))
        ax.plot([p - 0.05, p + 0.05], [med, med], color=INK, lw=0.9, zorder=4, solid_capstyle="butt")
        off = swarm(d, d_val=0.02 * span, d_off=0.045, max_off=width * 0.42)
        ax.scatter(p + off, d, s=point_size, color=c, edgecolor=_dark(c), lw=0.3, zorder=5)
        if show_mean:
            ax.plot(p, d.mean(), marker="o", ms=3.4, mfc=INK, mec="white", mew=0.5, zorder=6)
    ax.set_xticks(range(n))
    ax.set_xticklabels(["%s\n$\\mathit{n}$ = %d" % (l, len(d))
                        + (("\n$\\hat{\\mu}$ = " + fmt_mean) % np.mean(d) if show_mean else "")
                        for l, d in zip(labels, data)])
    ax.set_xlim(-0.6, n - 0.4)
    ax.tick_params(axis="x", length=0)
    if value_label:
        ax.set_ylabel(value_label)
    _clean(ax, bottom=False)


def ridgeline(ax, data, labels, colors=None, highlight=None, overlap=1.7, bw=None, value_label=None,
              show_median=True, fill_alpha=0.75):
    """Stacked KDEs sharing one value axis; top of list drawn at the top. For >4 distributions."""
    n = len(data)
    colors = _colors(n, colors if colors is not None else [PALE_B] * n, highlight)
    allv = np.concatenate([np.asarray(d, float) for d in data])
    span = np.ptp(allv) or 1.0
    grid = np.linspace(allv.min() - 0.1 * span, allv.max() + 0.1 * span, 400)
    dens = [_kde(d, grid, bw) for d in data]
    top = max(d.max() for d in dens) or 1.0
    for i, (d, dn, c) in enumerate(zip(data, dens, colors)):
        base = n - 1 - i
        h = dn / top * overlap
        z = 10 + i * 2
        ax.fill_between(grid, base, base + h, color=c, alpha=fill_alpha, lw=0, zorder=z)
        ax.plot(grid, base + h, color=_dark(c, 0.7) if c != RED else RED, lw=0.6, zorder=z + 1)
        ax.plot(grid, np.full_like(grid, base), color=LINE, lw=0.4, zorder=z + 1)
        if show_median:
            m = np.median(d)
            hm = np.interp(m, grid, h)
            ax.plot([m, m], [base, base + hm], color=INK, lw=0.6, zorder=z + 1)
    ax.set_yticks(np.arange(n)[::-1])
    ax.set_yticklabels(labels)
    ax.tick_params(axis="y", length=0)
    ax.set_ylim(-0.15, n - 1 + overlap + 0.1)
    ax.set_xlim(grid[0], grid[-1])
    if value_label:
        ax.set_xlabel(value_label)
    _clean(ax, left=False)


def mirror(ax, a, b, labels=("positive", "negative"), bins=30, colors=(DARK_B, OTHER), threshold=None,
           value_label=None, density=True):
    """Two distributions back to back on one value axis (e.g. relevant vs. irrelevant scores).

    `threshold` draws the one red decision line. Counts are shown as magnitudes on both sides.
    """
    a, b = np.asarray(a, float), np.asarray(b, float)
    edges = np.histogram_bin_edges(np.r_[a, b], bins=bins)
    ha, _ = np.histogram(a, edges, density=density)
    hb, _ = np.histogram(b, edges, density=density)
    w = np.diff(edges)
    ax.bar(edges[:-1], ha, w, align="edge", color=colors[0], alpha=0.8, lw=0)
    ax.bar(edges[:-1], -hb, w, align="edge", color=colors[1], alpha=0.9, lw=0)
    ax.axhline(0, color=INK, lw=0.5)
    m = max(ha.max(), hb.max()) * 1.15
    ax.set_ylim(-m, m)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: "%g" % abs(round(v, 6))))
    ax.text(0.04, 0.97, labels[0], transform=ax.transAxes, ha="left", va="top", fontsize=ANNOT,
            color=colors[0] if colors[0] != OTHER else INK, fontweight="bold")
    ax.text(0.04, 0.03, labels[1], transform=ax.transAxes, ha="left", va="bottom", fontsize=ANNOT,
            color=INK, fontweight="bold")
    if threshold is not None:
        ax.axvline(threshold, color=RED, lw=0.8, ls=(0, (3, 2)))
    ax.set_ylabel("density" if density else "count")
    if value_label:
        ax.set_xlabel(value_label)
    _clean(ax)


# --------------------------------------------------------------------------- comparisons

def forest(ax, labels, est, lo, hi, null=0.0, weights=None, pooled=None, pooled_label="Pooled",
           highlight=None, value_label=None, fmt="%.2f", text_x=1.03, header=None, numbers=True,
           ms_range=(2.2, 3.0)):
    """Effect sizes with CIs, one row each, null line, optional pooled diamond and a numeric column.

    The numeric column is drawn outside the axes at `text_x` (axes fraction); leave room for it.
    """
    n = len(labels)
    y = np.arange(n)[::-1] + (1.3 if pooled is not None else 0)
    est, lo, hi = map(lambda v: np.asarray(v, float), (est, lo, hi))
    w = np.ones(n) if weights is None else np.asarray(weights, float)
    ms = ms_range[0] + ms_range[1] * np.sqrt(w / w.max())
    cols = _colors(n, [DARK_B] * n, highlight)
    ax.axvline(null, color=MID, lw=0.5, ls=(0, (3, 2)), zorder=1)
    for yi, e, l, h, m, c in zip(y, est, lo, hi, ms, cols):
        ax.plot([l, h], [yi, yi], color=c, lw=0.8, zorder=2, solid_capstyle="butt")
        ax.plot(e, yi, marker="s", ms=m, color=c, mec="white", mew=0.3, zorder=3)
        if numbers:
            ax.text(text_x, yi, _fmt_minus((fmt + " [" + fmt + ", " + fmt + "]") % (e, l, h)),
                    transform=ax.get_yaxis_transform(), fontsize=ANNOT, va="center", ha="left", color=INK)
    ticks, labs = list(y), list(labels)
    if pooled is not None:
        pm, pl, ph = pooled
        ax.axhline(0.65, color=LINE, lw=0.5)
        ax.add_patch(Polygon([[pl, 0], [pm, 0.28], [ph, 0], [pm, -0.28]], closed=True, fc=INK, ec=INK,
                             lw=0.4, zorder=3))
        if numbers:
            ax.text(text_x, 0, _fmt_minus((fmt + " [" + fmt + ", " + fmt + "]") % (pm, pl, ph)),
                    transform=ax.get_yaxis_transform(), fontsize=ANNOT, va="center", ha="left", color=INK,
                    fontweight="bold")
        ticks.append(0)
        labs.append(pooled_label)
    ax.set_yticks(ticks)
    ax.set_yticklabels(labs)
    if pooled is not None:
        ax.get_yticklabels()[-1].set_fontweight("bold")
    ax.tick_params(axis="y", length=0)
    ax.set_ylim(-0.7 if pooled is not None else -0.7, y.max() + 0.7)
    if header and numbers:
        ax.text(text_x, y.max() + 0.75, header, transform=ax.get_yaxis_transform(), fontsize=ANNOT,
                ha="left", va="bottom", color=INK, fontweight="bold")
    if value_label:
        ax.set_xlabel(value_label)
    _clean(ax, left=False)


def dumbbell(ax, labels, a, b, label_a="before", label_b="after", sort=True, highlight=None,
             value_label=None, legend_loc="above"):
    """Paired change per item on one value axis: hollow = a, filled = b, segment = the change.

    Use instead of a slopegraph: the change sits on the value axis, so nothing implies a continuum
    between two conditions. Sorted by b - a unless sort=False.
    """
    a, b = np.asarray(a, float), np.asarray(b, float)
    idx = np.argsort(b - a) if sort else np.arange(len(a))[::-1]
    labels = [labels[i] for i in idx]
    a, b = a[idx], b[idx]
    hl = None
    if highlight is not None:
        hl = int(np.where(idx == highlight)[0][0])
    y = np.arange(len(a))
    for i in y:
        c = RED if i == hl else (POS if b[i] > a[i] else NEG)
        ax.plot([a[i], b[i]], [i, i], color=c, lw=1.4, alpha=0.55 if i != hl else 0.9, zorder=1,
                solid_capstyle="round")
        ax.plot(a[i], i, "o", ms=3.3, mfc="white", mec=INK, mew=0.6, zorder=3)
        ax.plot(b[i], i, "o", ms=3.3, mfc=RED if i == hl else INK, mec="white", mew=0.4, zorder=3)
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.tick_params(axis="y", length=0)
    ax.set_ylim(-0.7, len(a) - 0.3)
    ax.grid(axis="y", color=GRID, lw=0.4, zorder=0)
    if value_label:
        ax.set_xlabel(value_label)
    _clean(ax, left=False)
    import layout as L
    hs = [Line2D([], [], ls="none", marker="o", ms=3.3, mfc="white", mec=INK, mew=0.6),
          Line2D([], [], ls="none", marker="o", ms=3.3, mfc=INK, mec="white", mew=0.4)]
    if legend_loc == "above":      # never on the data: a sorted dumbbell fills every corner
        return L.legend(ax, hs, [label_a, label_b], loc="lower left", bbox_to_anchor=(0.0, 1.0), ncol=2,
                        frame=False, borderaxespad=0.1)
    return L.legend(ax, hs, [label_a, label_b], loc=legend_loc)


def waterfall(ax, labels, deltas, start=None, start_label="Start", total_label="Total", fmt="%+.2f",
              value_label=None, width=0.62, highlight=None):
    """Additive decomposition: floating bars for each contribution, then the total.

    Positive contributions warm, negative cool; `highlight` (index into deltas) turns one red.
    """
    deltas = np.asarray(deltas, float)
    x, level = 0, 0.0
    names = []
    if start is not None:
        ax.bar(x, start, width, color=OTHER, lw=0)
        ax.text(x, start, (fmt.replace("+", "")) % start, ha="center", va="bottom", fontsize=SMALL)
        level = start
        names.append(start_label)
        x += 1
    for i, d in enumerate(deltas):
        c = RED if i == highlight else (POS if d > 0 else NEG)
        ax.bar(x, d, width, bottom=level, color=c, lw=0)
        ax.plot([x - 1 + width / 2, x - width / 2], [level, level], color=MID, lw=0.4, zorder=0) if x else None
        top = level + max(d, 0)
        ax.text(x, top, _fmt_minus(fmt % d), ha="center", va="bottom", fontsize=SMALL)
        level += d
        names.append(labels[i])
        x += 1
    ax.plot([x - 1 + width / 2, x - width / 2], [level, level], color=MID, lw=0.4, zorder=0)
    ax.bar(x, level, width, color=DARK_B, lw=0)
    ax.text(x, max(level, 0), _fmt_minus((fmt.replace("+", "")) % level), ha="center", va="bottom",
            fontsize=SMALL, fontweight="bold")
    names.append(total_label)
    ax.axhline(0, color=INK, lw=0.5)
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, rotation=35, ha="right", rotation_mode="anchor")
    ax.tick_params(axis="x", length=0)
    if value_label:
        ax.set_ylabel(value_label)
    _clean(ax)


# --------------------------------------------------------------------------- matrices

def corr_triangle(ax, R, labels, cmap=DIVERGE, vmin=-1, vmax=1, p=None, alpha=0.05, show_numbers=True):
    """corrplot 'mixed': circles in the lower triangle (area ~ |r|, colour = r), numbers in the upper,
    variable names on the diagonal. `p` (same shape) greys out non-significant circles with a cross.
    Returns a ScalarMappable for `cbar`.
    """
    R = np.asarray(R, float)
    k = len(labels)
    norm = Normalize(vmin, vmax)
    for i in range(k):
        for j in range(k):
            x, y = j, k - 1 - i
            if i == j:
                ax.text(x, y, labels[i], ha="center", va="center", fontsize=ANNOT, fontweight="bold", color=INK)
                continue
            ax.add_patch(Rectangle((x - 0.5, y - 0.5), 1, 1, fc="none", ec=GRID, lw=0.4))
            r = R[i, j]
            ns = p is not None and p[i, j] >= alpha
            if i > j:
                ax.add_patch(Circle((x, y), 0.46 * np.sqrt(abs(r)), fc=cmap(norm(r)),
                                    ec="none", alpha=0.35 if ns else 1.0))
                if ns:
                    ax.plot([x - 0.18, x + 0.18], [y - 0.18, y + 0.18], color=MID, lw=0.4)
                    ax.plot([x - 0.18, x + 0.18], [y + 0.18, y - 0.18], color=MID, lw=0.4)
            elif show_numbers:
                ax.text(x, y, _fmt_minus("%.2f" % r), ha="center", va="center", fontsize=SMALL,
                        color=INK if not ns else MID, fontweight="bold" if abs(r) >= 0.5 and not ns else "normal")
    ax.set_xlim(-0.5, k - 0.5)
    ax.set_ylim(-0.5, k - 0.5)
    ax.set_aspect("equal")
    ax.axis("off")
    from matplotlib.cm import ScalarMappable
    return ScalarMappable(norm=norm, cmap=cmap)


def bubble_matrix(ax, S, C, rows, cols, cmap=DIVERGE, vmin=None, vmax=None, smax=60.0, s_ref=None,
                  highlight=None, xrot=35, norm=None):
    """Dot matrix: size encodes one quantity (S >= 0), colour another (C). Rows top-down.

    `highlight` = (i, j) outlines that one cell in red. NaN cells are left empty (no data there).
    `norm` (e.g. TwoSlopeNorm centred on a threshold) overrides vmin/vmax. Returns the scatter (a mappable).
    """
    S, C = np.asarray(S, float), np.asarray(C, float)
    nr, nc = S.shape
    s_ref = s_ref or np.nanmax(S)
    jj, ii = np.meshgrid(np.arange(nc), np.arange(nr))
    ok = (np.isfinite(S) & np.isfinite(C)).ravel()
    kw = dict(norm=norm) if norm is not None else dict(vmin=vmin, vmax=vmax)
    sc = ax.scatter(jj.ravel()[ok], (nr - 1 - ii).ravel()[ok], s=smax * S.ravel()[ok] / s_ref, c=C.ravel()[ok],
                    cmap=cmap, edgecolor=INK, lw=0.3, zorder=3, **kw)
    if highlight is not None:
        i, j = highlight
        ax.add_patch(Rectangle((j - 0.5, nr - 1 - i - 0.5), 1, 1, fc="none", ec=RED, lw=0.9, zorder=4))
    ax.set_xticks(range(nc))
    ax.set_xticklabels(cols, rotation=xrot, ha="right" if xrot else "center", rotation_mode="anchor")
    ax.set_yticks(range(nr))
    ax.set_yticklabels(rows[::-1])
    ax.set_xlim(-0.6, nc - 0.4)
    ax.set_ylim(-0.6, nr - 0.4)
    ax.set_xticks(np.arange(nc + 1) - 0.5, minor=True)
    ax.set_yticks(np.arange(nr + 1) - 0.5, minor=True)
    ax.grid(which="minor", color=GRID, lw=0.4, zorder=0)
    ax.tick_params(which="both", length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    return sc


def size_key(ax, values, s_ref, smax=60.0, fmt="%g", loc="upper left", title=None, **kw):
    """Legend for bubble sizes, matching bubble_matrix(smax, s_ref)."""
    import layout as L
    hs = [ax.scatter([], [], s=smax * v / s_ref, color="white", edgecolor=INK, lw=0.4) for v in values]
    return L.legend(ax, hs, [fmt % v for v in values], loc=loc, title=title, **kw)


def cbar(cax, mappable, label=None, orientation="vertical", ticks=None, size=6.0):
    """House colour bar in an axes you placed (e.g. pg.ax(x, y, 2.2, 20))."""
    cb = cax.figure.colorbar(mappable, cax=cax, orientation=orientation, ticks=ticks)
    cb.outline.set_linewidth(0.4)
    cb.ax.tick_params(labelsize=size, width=0.5, length=1.6, direction="in")
    if label:
        cb.set_label(label, fontsize=size)
    for t in (cb.ax.get_yticklabels() + cb.ax.get_xticklabels()):
        t.set_text(_fmt_minus(t.get_text()))
    return cb


def annot_heatmap(ax, M, rows, cols, fmt="%.1f", cmap=SEQ, vmin=None, vmax=None, highlight=None,
                  size=SMALL, gap=0.6):
    """Grid of values with the number in every cell (convergence scans, parameter sweeps).

    Text switches to white on dark cells. `highlight` = (i, j) outlines the chosen cell in red.
    Rows top-down. Returns the mesh (a mappable).
    """
    M = np.asarray(M, float)
    nr, nc = M.shape
    mesh = ax.pcolormesh(np.arange(nc + 1), np.arange(nr + 1), M[::-1], cmap=cmap, vmin=vmin, vmax=vmax,
                         edgecolors="white", linewidth=gap)
    norm = mesh.norm
    for i in range(nr):
        for j in range(nc):
            r, g, b, _ = cmap(norm(M[i, j]))
            dark = 0.299 * r + 0.587 * g + 0.114 * b < 0.5
            ax.text(j + 0.5, nr - i - 0.5, _fmt_minus(fmt % M[i, j]), ha="center", va="center", fontsize=size,
                    color="white" if dark else INK)
    if highlight is not None:
        i, j = highlight
        ax.add_patch(Rectangle((j + 0.04, nr - i - 1 + 0.04), 0.92, 0.92, fc="none", ec=RED, lw=1.0, zorder=5))
    ax.set_xticks(np.arange(nc) + 0.5)
    ax.set_xticklabels(cols)
    ax.set_yticks(np.arange(nr) + 0.5)
    ax.set_yticklabels(list(rows)[::-1])
    ax.tick_params(which="both", length=0)
    for sp in ax.spines.values():
        sp.set_visible(False)
    return mesh


def cluster_heatmap(pg, x, y, w, h, M, rows, cols, row_groups=None, group_colors=None, cmap=DIVERGE,
                    vmin=None, vmax=None, center=None, method="average", metric="euclidean",
                    dendro=7.0, bar=2.0, col_rot=45, label_w=14.0, label_h=9.0):
    """ComplexHeatmap-style: clustered matrix, row + column dendrograms, a categorical row bar.

    Everything in millimetres on `pg` (a style.Page). The box (x, y, w, h) includes dendrograms,
    the annotation bar and the tick labels. Returns dict(ax=heatmap axes, mesh=mappable, order=(ri, ci)).
    """
    from scipy.cluster import hierarchy as H
    M = np.asarray(M, float)
    lr = H.linkage(M, method=method, metric=metric)
    lc = H.linkage(M.T, method=method, metric=metric)
    dr = H.dendrogram(lr, no_plot=True)
    dc = H.dendrogram(lc, no_plot=True)
    ri, ci = dr["leaves"], dc["leaves"]
    has_bar = row_groups is not None
    hx = x + dendro + (bar + 0.8 if has_bar else 0)
    hw = w - (hx - x) - label_w
    hy = y + label_h
    hh = h - label_h - dendro
    ax = pg.ax(hx, hy, hw, hh)
    D = M[np.ix_(ri, ci)]
    if center is not None and vmin is None:
        m = np.nanmax(np.abs(D - center))
        vmin, vmax = center - m, center + m
    mesh = ax.pcolormesh(D[::-1], cmap=cmap, vmin=vmin, vmax=vmax, edgecolors="white", linewidth=0.25)
    ax.set_xticks(np.arange(len(ci)) + 0.5)
    ax.set_xticklabels([cols[i] for i in ci], rotation=col_rot, ha="right", rotation_mode="anchor")
    ax.set_yticks(np.arange(len(ri)) + 0.5)
    ax.set_yticklabels([rows[i] for i in ri][::-1])
    ax.yaxis.tick_right()
    ax.tick_params(which="both", length=0, pad=1.2, left=False, right=False)
    for s in ax.spines.values():
        s.set_visible(False)
    # dendrograms: scipy leaves sit at 5, 15, 25 ...; map to cell centres 0.5, 1.5 ...
    axr = pg.ax(x, hy, dendro, hh)
    for xs, ys in zip(dr["icoord"], dr["dcoord"]):
        axr.plot(ys, len(ri) - np.asarray(xs) / 10.0, color=INK, lw=0.45)
    axr.set_ylim(0, len(ri))
    axr.set_xlim(max(max(d) for d in dr["dcoord"]) * 1.02, 0)
    axr.axis("off")
    axc = pg.ax(hx, hy + hh, hw, dendro)
    for xs, ys in zip(dc["icoord"], dc["dcoord"]):
        axc.plot(np.asarray(xs) / 10.0, ys, color=INK, lw=0.45)
    axc.set_xlim(0, len(ci))
    axc.set_ylim(0, max(max(d) for d in dc["dcoord"]) * 1.02)
    axc.axis("off")
    if has_bar:
        axb = pg.ax(x + dendro + 0.4, hy, bar, hh)
        g = [row_groups[i] for i in ri][::-1]
        for k, gi in enumerate(g):
            axb.add_patch(Rectangle((0, k), 1, 1, fc=group_colors[gi], ec="white", lw=0.25))
        axb.set_xlim(0, 1)
        axb.set_ylim(0, len(ri))
        axb.axis("off")
    return dict(ax=ax, mesh=mesh, order=(ri, ci))


def upset(pg, x, y, w, h, sets, max_bars=12, highlight=None, bar_color=DARK_B, set_w=0.26,
          matrix_h=0.42, name_w=13.0):
    """UpSet plot for 3+ sets (use instead of a Venn beyond three): exclusive intersection sizes,
    membership matrix, set sizes. `sets` maps name -> iterable. `highlight` = tuple of set names.
    Returns dict of axes.
    """
    names = list(sets)
    S = {k: set(v) for k, v in sets.items()}
    universe = set().union(*S.values())
    combos = {}
    for e in universe:
        key = tuple(k for k in names if e in S[k])
        combos[key] = combos.get(key, 0) + 1
    items = sorted(combos.items(), key=lambda kv: (-kv[1], len(kv[0])))[:max_bars]
    k, m = len(names), len(items)
    mh = h * matrix_h
    left = w * set_w
    ax_bar = pg.ax(x + left + name_w, y + mh, w - left - name_w, h - mh)
    ax_mat = pg.ax(x + left + name_w, y, w - left - name_w, mh, sharex=ax_bar)
    ax_set = pg.ax(x, y, left, mh, sharey=ax_mat)
    cnt = [c for _, c in items]
    cols = [RED if highlight is not None and set(key) == set(highlight) else bar_color for key, _ in items]
    ax_bar.bar(range(m), cnt, 0.62, color=cols, lw=0)
    for i, c in enumerate(cnt):
        ax_bar.text(i, c, "%d" % c, ha="center", va="bottom", fontsize=SMALL)
    ax_bar.set_ylabel("intersection size")
    _clean(ax_bar, bottom=False)
    ax_bar.tick_params(axis="x", labelbottom=False)
    ax_bar.set_xlim(-0.6, m - 0.4)
    ax_bar.set_ylim(0, max(cnt) * 1.15)
    for r in range(k):
        if r % 2 == 0:
            ax_mat.axhspan(r - 0.5, r + 0.5, color="#F4F5F7", lw=0, zorder=0)
    for i, (key, _) in enumerate(items):
        ys = [k - 1 - names.index(n) for n in key]
        hl = cols[i] == RED
        ax_mat.scatter([i] * k, range(k), s=14, color=GRID, lw=0, zorder=1)
        ax_mat.scatter([i] * len(ys), ys, s=14, color=RED if hl else INK, lw=0, zorder=3)
        if len(ys) > 1:
            ax_mat.plot([i, i], [min(ys), max(ys)], color=RED if hl else INK, lw=1.0, zorder=2)
    ax_mat.set_ylim(-0.6, k - 0.4)
    ax_mat.axis("off")
    sizes = [len(S[n]) for n in names]
    ax_set.barh([k - 1 - i for i in range(k)], sizes, 0.55, color=OTHER, lw=0)
    ax_set.invert_xaxis()
    ax_set.set_xlabel("set size")
    ax_set.tick_params(axis="y", left=False, labelleft=False)
    for s in ("top", "left"):
        ax_set.spines[s].set_visible(False)
    ax_set.tick_params(which="both", top=False, left=False, right=False)
    for i, n in enumerate(names):
        pg.fig.text((x + left + name_w / 2) / pg.W, (y + mh * (k - 1 - i + 0.5 + 0.1) / (k + 0.2)) / pg.H, n,
                    ha="center", va="center", fontsize=ANNOT, color=INK)
    return dict(bar=ax_bar, matrix=ax_mat, sets=ax_set)


# --------------------------------------------------------------------------- model evaluation

def density_scatter(ax, x, y, logx=False, logy=False, method="auto", bins=90, cmap=SEQ, s=2.0, zorder=2,
                    floor=0.08, **kw):
    """Every point, coloured by local point density, densest drawn last.

    method "kde" (smooth; default up to 30 000 points) colours by a Gaussian KDE evaluated at each point,
    scaled to [0, 1]; "hist" (fast, for 10^5-10^6 points) by log10 of the count in its 2-D bin, which
    looks blocky at small n. Density is computed in log space on log axes. `floor` keeps the sparsest
    points off white. Rasterized, so the SVG stays small while text stays live.
    """
    x, y = np.asarray(x, float), np.asarray(y, float)
    u = np.log10(x) if logx else x
    v = np.log10(y) if logy else y
    if method == "auto":
        method = "kde" if len(x) <= 30000 else "hist"
    if method == "kde":
        uv = np.vstack([u, v])
        z = stats.gaussian_kde(uv)(uv)
        z = floor + (1 - floor) * z / z.max()
        vmax = 1.0
    else:
        H2, xe, ye = np.histogram2d(u, v, bins=bins)
        ix = np.clip(np.searchsorted(xe, u, side="right") - 1, 0, bins - 1)
        iy = np.clip(np.searchsorted(ye, v, side="right") - 1, 0, bins - 1)
        z = np.log10(H2[ix, iy])
        vmax = None
    o = np.argsort(z, kind="stable")
    return ax.scatter(x[o], y[o], c=z[o], s=s, cmap=cmap, lw=0, rasterized=True, zorder=zorder, vmin=0,
                      vmax=vmax, **kw)


def parity(ax, ref, pred, unit="", tol=None, density=True, cmap=SEQ, s=2.0, highlight=None,
           stats_loc=(0.04, 0.96), resid_inset=True, bins=80, lim=None):
    """Parity plot for many points: density-coloured scatter (rasterized), y = x, optional +/- tol band,
    MAE / RMSE / R^2 / N in the top-left, residual histogram inset in the empty bottom-right corner.
    `highlight` = boolean mask drawn in red on top (e.g. the outliers under discussion).
    """
    ref, pred = np.asarray(ref, float), np.asarray(pred, float)
    lo = min(ref.min(), pred.min()) if lim is None else lim[0]
    hi = max(ref.max(), pred.max()) if lim is None else lim[1]
    pad = 0.04 * (hi - lo)
    lo, hi = lo - pad, hi + pad
    if density:
        H2, xe, ye = np.histogram2d(ref, pred, bins=bins, range=[[lo, hi], [lo, hi]])
        ix = np.clip(np.searchsorted(xe, ref) - 1, 0, bins - 1)
        iy = np.clip(np.searchsorted(ye, pred) - 1, 0, bins - 1)
        z = H2[ix, iy]
        o = np.argsort(z)
        sc = ax.scatter(ref[o], pred[o], c=np.log10(z[o]), s=s, cmap=cmap, lw=0, rasterized=True, zorder=2,
                        vmin=0)
    else:
        sc = ax.scatter(ref, pred, s=s, color=RU, lw=0, rasterized=True, zorder=2)
    if highlight is not None:
        mk = np.asarray(highlight, bool)
        ax.scatter(ref[mk], pred[mk], s=s * 3, color=RED, lw=0, zorder=4)
    ax.plot([lo, hi], [lo, hi], color=INK, lw=0.6, zorder=3)
    if tol:
        ax.fill_between([lo, hi], [lo - tol, hi - tol], [lo + tol, hi + tol], color=GRID, lw=0, zorder=1)
    ax.set_xlim(lo, hi)
    ax.set_ylim(lo, hi)
    ax.set_aspect("equal")
    r = pred - ref
    mae, rmse = np.abs(r).mean(), np.sqrt((r ** 2).mean())
    r2 = 1 - (r ** 2).sum() / ((ref - ref.mean()) ** 2).sum()
    u = (" " + unit) if unit else ""
    ax.text(*stats_loc, _fmt_minus("MAE %.3g%s\nRMSE %.3g%s\n$\\mathit{R}^2$ %.3f\n$\\mathit{N}$ = %s"
                                   % (mae, u, rmse, u, r2, format(len(r), ","))),
            transform=ax.transAxes, ha="left", va="top", fontsize=SMALL, color=INK, linespacing=1.25)
    ins = None
    if resid_inset:
        ins = ax.inset_axes([0.60, 0.17, 0.36, 0.20])
        lim_r = np.percentile(np.abs(r), 99.5)
        ins.hist(r, bins=40, range=(-lim_r, lim_r), color=OTHER, lw=0)
        ins.axvline(0, color=INK, lw=0.4)
        ins.set_yticks([])
        ins.tick_params(axis="x", labelsize=SMALL, length=1.2, pad=1)
        ins.set_xlabel("residual" + ((" (%s)" % unit) if unit else ""), fontsize=SMALL, labelpad=1)
        for sp in ("top", "right", "left"):
            ins.spines[sp].set_visible(False)
        ins.patch.set_alpha(0)
        ins.xaxis.set_major_formatter(FuncFormatter(lambda v, _: _fmt_minus("%g" % round(v, 6))))
    return dict(mappable=sc, mae=mae, rmse=rmse, r2=r2, inset=ins)


def taylor(fig_or_pg, rect_mm, ref_std, models, highlight=None, normalize=True, smax=None, colors=None,
           rms_levels=None):
    """Taylor diagram (quarter circle): radius = s.d., angle = arccos(r), distance to REF = centred RMSE.

    `models` = list of (name, std, corr). Returns the polar axes. Place it with rect_mm on a Page.
    """
    pg = fig_or_pg
    x, y, w, h = rect_mm
    ax = pg.fig.add_axes([x / pg.W, y / pg.H, w / pg.W, h / pg.H], projection="polar")
    ax.set_thetamin(0)
    ax.set_thetamax(90)
    sref = 1.0 if normalize else ref_std
    stds = [m[1] / (ref_std if normalize else 1.0) for m in models]
    smax = smax or 1.25 * max(max(stds), sref)
    ax.set_ylim(0, smax)
    rt = np.array([0, 0.2, 0.4, 0.6, 0.8, 0.9, 0.95, 0.99, 1.0])
    ax.set_thetagrids(np.degrees(np.arccos(rt)), [("%g" % v) for v in rt], fontsize=SMALL)
    ax.tick_params(axis="x", pad=0.5)
    ax.tick_params(axis="y", labelsize=6.0)
    ax.grid(color=GRID, lw=0.4)
    ax.spines["polar"].set_linewidth(0.6)
    th, rr = np.meshgrid(np.linspace(0, np.pi / 2, 200), np.linspace(0, smax, 200))
    E = np.sqrt(rr ** 2 + sref ** 2 - 2 * rr * sref * np.cos(th))
    levels = rms_levels or list(np.round(np.array([0.25, 0.5, 0.75, 1.0]) * sref, 3))
    ax.contour(th, rr, E, levels=levels, colors=[MID], linewidths=0.45, linestyles="dashed")
    tt = np.radians(62)                    # label each centred-RMSE arc on one ray, outer root
    for lv in levels:
        disc = (sref * np.cos(tt)) ** 2 - (sref ** 2 - lv ** 2)
        if disc > 0:
            r0 = sref * np.cos(tt) + np.sqrt(disc)
            if r0 < smax * 0.97:
                ax.text(tt, r0, "%g" % lv, fontsize=SMALL - 0.3, color=MID, ha="center", va="center",
                        bbox=dict(fc="white", ec="none", pad=0.2), zorder=4)
    t = np.linspace(0, np.pi / 2, 100)
    ax.plot(t, np.full_like(t, sref), color=INK, lw=0.5, ls=(0, (1, 1.2)))
    ax.plot(0, sref, marker="*", ms=6, color=INK, clip_on=False, zorder=5)
    ax.text(0.03, sref * 1.02, "REF", fontsize=SMALL, ha="left", va="bottom", color=INK)
    n = len(models)
    cols = _colors(n, colors or [DARK_B] * n, highlight)
    for (name, _, r), s, c in zip(models, stds, cols):
        tt = np.arccos(np.clip(r, 0, 1))
        ax.plot(tt, s, "o", ms=3.6, color=c, mec="white", mew=0.4, zorder=6, clip_on=False)
        ax.annotate(name, (tt, s), xytext=(3, 2), textcoords="offset points", fontsize=SMALL, color=INK,
                    zorder=6)
    ax.set_xlabel("")
    ax.text(np.radians(45), smax * 1.2, "correlation", rotation=-45, ha="center", va="center",
            fontsize=6.3, color=INK)
    ax.text(0.5, -0.13, "normalized s.d." if normalize else "s.d.", transform=ax.transAxes, ha="center",
            va="top", fontsize=6.3, color=INK)
    return ax


def calibration(ax, nominal, observed, lo=None, hi=None, label=None, color=DARK_B, annotate=True):
    """Reliability / coverage calibration: observed vs nominal with y = x. Above = conservative."""
    nominal, observed = np.asarray(nominal, float), np.asarray(observed, float)
    ax.plot([0, 1], [0, 1], color=INK, lw=0.5, ls=(0, (3, 2)))
    if lo is not None:
        ax.fill_between(nominal, lo, hi, color=color, alpha=0.18, lw=0)
    ax.plot(nominal, observed, "-o", color=color, ms=2.6, lw=0.9, mec="white", mew=0.3, label=label)
    if annotate:
        ax.text(0.05, 0.93, "conservative", transform=ax.transAxes, fontsize=SMALL, color=INK, ha="left",
                va="top")
        ax.text(0.95, 0.07, "over-confident", transform=ax.transAxes, fontsize=SMALL, color=INK, ha="right",
                va="bottom")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_aspect("equal")
    _clean(ax)


def nondominated(x, y, minimize=(True, True)):
    """Boolean mask of the Pareto-optimal points."""
    X = np.asarray(x, float) * (1 if minimize[0] else -1)
    Y = np.asarray(y, float) * (1 if minimize[1] else -1)
    return np.array([not np.any((X <= X[i]) & (Y <= Y[i]) & ((X < X[i]) | (Y < Y[i]))) for i in range(len(X))])


def pareto(ax, x, y, minimize=(True, True), labels=None, highlight=None, xlabel=None, ylabel=None,
           front_color=DARK_B):
    """Multi-objective scatter with the non-dominated set joined by its attainment step line."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    X = x if minimize[0] else -x
    nd = nondominated(x, y, minimize)
    ax.scatter(x[~nd], y[~nd], s=7, color=OTHER, lw=0, zorder=2)
    o = np.argsort(X[nd])
    fx, fy = x[nd][o], y[nd][o]
    ax.step(fx, fy, where="post", color=front_color, lw=0.9, zorder=3)
    ax.scatter(fx, fy, s=12, color=front_color, edgecolor="white", lw=0.4, zorder=4)
    if highlight is not None:
        ax.scatter(x[highlight], y[highlight], s=22, color=RED, edgecolor="white", lw=0.5, zorder=5)
    if labels is not None:
        for i in np.where(nd)[0]:
            ax.annotate(labels[i], (x[i], y[i]), xytext=(3, 3), textcoords="offset points", fontsize=SMALL,
                        color=INK)
    if xlabel:
        ax.set_xlabel(xlabel)
    if ylabel:
        ax.set_ylabel(ylabel)
    _clean(ax)
    return nd


def parallel(ax, X, names, highlight=None, invert=None, color_by=None, cmap=SEQ, fmt="%.3g", lw=0.5,
             alpha=0.35):
    """Parallel coordinates for candidates with several objectives / descriptors.

    Each column min-max scaled to its own vertical axis; `invert[k]` flips an axis so "better" is up
    on every axis. Background lines grey (or coloured by `color_by`), `highlight` rows in red on top.
    """
    X = np.asarray(X, float)
    n, k = X.shape
    inv = np.zeros(k, bool) if invert is None else np.asarray(invert, bool)
    lo, hi = X.min(0), X.max(0)
    Z = (X - lo) / np.where(hi > lo, hi - lo, 1)
    Z[:, inv] = 1 - Z[:, inv]
    xs = np.arange(k)
    hl = set(np.atleast_1d(highlight).tolist()) if highlight is not None else set()
    segs = [np.column_stack([xs, Z[i]]) for i in range(n) if i not in hl]
    if color_by is not None:
        cb = np.asarray(color_by, float)[[i for i in range(n) if i not in hl]]
        lc = LineCollection(segs, cmap=cmap, array=cb, lw=lw, alpha=0.7, zorder=2)
    else:
        lc = LineCollection(segs, colors=OTHER, lw=lw, alpha=alpha, zorder=2)
    ax.add_collection(lc)
    for i in hl:
        ax.plot(xs, Z[i], color=RED, lw=1.2, zorder=4)
        ax.scatter(xs, Z[i], s=8, color=RED, zorder=5, lw=0)
    for j in xs:
        ax.plot([j, j], [0, 1], color=INK, lw=0.6, zorder=3)
        top, bot = (lo[j], hi[j]) if inv[j] else (hi[j], lo[j])
        ax.text(j, 1.03, _fmt_minus(fmt % top), ha="center", va="bottom", fontsize=SMALL, color=INK)
        ax.text(j, -0.03, _fmt_minus(fmt % bot), ha="center", va="top", fontsize=SMALL, color=INK)
        ax.text(j, 1.16, names[j] + (" (inv.)" if inv[j] else ""), ha="center", va="bottom", fontsize=6.0,
                color=INK, fontweight="bold")
    ax.set_xlim(-0.3, k - 0.7)
    ax.set_ylim(-0.12, 1.28)
    ax.axis("off")
    return lc


# --------------------------------------------------------------------------- catalysis / materials

class Ternary:
    """Ternary axes on an ordinary Axes. Components (a, b, c) sum to 1 (normalised on input).

    Corners: a top, b bottom-left, c bottom-right. Tick values: a on the left edge, b on the bottom
    edge, c on the right edge; grid lines parallel to the edge where that component is zero.
    """
    S3 = np.sqrt(3) / 2

    def __init__(self, ax, labels=("A", "B", "C"), step=0.2, grid=True, tick_fmt="%.1f", label_size=7.0):
        self.ax = ax
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_xlim(-0.12, 1.12)
        ax.set_ylim(-0.13, self.S3 + 0.1)
        ax.add_patch(Polygon([[0, 0], [1, 0], [0.5, self.S3]], closed=True, fc="none", ec=INK, lw=0.6, zorder=5))
        ticks = np.arange(step, 1.0, step)
        for t in ticks:
            if grid:
                for p, q in (self._line_a(t), self._line_b(t), self._line_c(t)):
                    ax.plot([p[0], q[0]], [p[1], q[1]], color=GRID, lw=0.4, zorder=1)
            pa = self.xy(t, 1 - t, 0)
            ax.text(pa[0] - 0.02, pa[1], tick_fmt % t, ha="right", va="center", fontsize=SMALL, color=INK)
            pb = self.xy(0, t, 1 - t)
            ax.text(pb[0], pb[1] - 0.025, tick_fmt % t, ha="center", va="top", fontsize=SMALL, color=INK,
                    rotation=60)
            pc = self.xy(1 - t, 0, t)
            ax.text(pc[0] + 0.02, pc[1], tick_fmt % t, ha="left", va="center", fontsize=SMALL, color=INK,
                    rotation=-60)
        ax.text(0.5, self.S3 + 0.035, labels[0], ha="center", va="bottom", fontsize=label_size,
                fontweight="bold", color=INK)
        ax.text(-0.03, -0.035, labels[1], ha="right", va="top", fontsize=label_size, fontweight="bold",
                color=INK)
        ax.text(1.03, -0.035, labels[2], ha="left", va="top", fontsize=label_size, fontweight="bold",
                color=INK)

    def xy(self, a, b, c):
        a, b, c = (np.asarray(v, float) for v in (a, b, c))
        s = a + b + c
        a, c = a / s, c / s
        return c + a / 2, a * self.S3

    def _line_a(self, t):
        return self.xy(t, 1 - t, 0), self.xy(t, 0, 1 - t)

    def _line_b(self, t):
        return self.xy(1 - t, t, 0), self.xy(0, t, 1 - t)

    def _line_c(self, t):
        return self.xy(1 - t, 0, t), self.xy(0, 1 - t, t)

    def scatter(self, a, b, c, **kw):
        kw.setdefault("zorder", 6)
        return self.ax.scatter(*self.xy(a, b, c), **kw)

    def contourf(self, a, b, c, v, levels=12, cmap=SEQ, lines=True, **kw):
        import matplotlib.tri as mtri
        X, Y = self.xy(a, b, c)
        tri = mtri.Triangulation(X, Y)
        m = self.ax.tricontourf(tri, v, levels=levels, cmap=cmap, zorder=0, **kw)
        if lines:
            self.ax.tricontour(tri, v, levels=m.levels, colors="white", linewidths=0.3, zorder=0.5)
        return m

    @staticmethod
    def lattice(n=40):
        pts = [(i / n, j / n, 1 - (i + j) / n) for i in range(n + 1) for j in range(n + 1 - i)]
        return [np.array(v) for v in zip(*pts)]


def energy_profile(ax, energies, states=None, x=None, color=DARK_B, label=None, ts=None, level_w=0.56,
                   fmt="%.2f", annotate=True, pds=False, ls="-", label_offset=0.0, text_size=SMALL):
    """Free-energy / reaction-energy diagram: a level per state, thin dashed connectors, optional TS humps.

    `ts` = {i: E_TS} draws a smooth barrier between state i and i+1 (labelled). `pds=True` marks the
    largest uphill step in red with its Delta G. The dashed connectors are the domain convention for
    consecutive elementary steps; they do not claim intermediate values. Call once per pathway.
    """
    E = np.asarray(energies, float)
    n = len(E)
    x = np.arange(n) if x is None else np.asarray(x, float)
    ts = ts or {}
    for i in range(n):
        ax.plot([x[i] - level_w / 2, x[i] + level_w / 2], [E[i], E[i]], color=color, lw=1.6, ls=ls,
                solid_capstyle="butt", zorder=3, label=label if i == 0 else None)
        if annotate:
            ax.text(x[i], E[i] + label_offset, _fmt_minus(fmt % E[i]), ha="center", va="bottom",
                    fontsize=text_size, color=_dark(color, 0.85) if color != OTHER else INK)
    for i in range(n - 1):
        x0, x1 = x[i] + level_w / 2, x[i + 1] - level_w / 2
        if i in ts:
            et = ts[i]
            t = np.linspace(0, 1, 60)
            # piecewise cosine: rises from E[i] to et, falls to E[i+1]; smooth at the top
            xm = (x0 + x1) / 2
            left = t <= 0.5
            u = np.where(left, t / 0.5, (t - 0.5) / 0.5)
            yy = np.where(left, E[i] + (et - E[i]) * (1 - np.cos(np.pi * u)) / 2,
                          et + (E[i + 1] - et) * (1 - np.cos(np.pi * u)) / 2)
            ax.plot(x0 + (x1 - x0) * t, yy, color=color, lw=0.8, ls=ls, zorder=2)
            if annotate:
                ax.text(xm, et + label_offset, _fmt_minus(fmt % et), ha="center", va="bottom", fontsize=text_size,
                        color=_dark(color, 0.85) if color != OTHER else INK, style="italic")
        else:
            ax.plot([x0, x1], [E[i], E[i + 1]], color=color, lw=0.6, ls=(0, (2, 1.6)), zorder=2)
    if pds:
        d = np.diff(E)
        k = int(np.argmax(d))
        xa = x[k + 1] + level_w / 2 + 0.06
        ax.annotate("", xy=(xa, E[k + 1]), xytext=(xa, E[k]),
                    arrowprops=dict(arrowstyle="<->", color=RED, lw=0.7, shrinkA=0, shrinkB=0))
        ax.plot([x[k] + level_w / 2, xa + 0.04], [E[k], E[k]], color=RED, lw=0.4, ls=(0, (1, 1)))
        ax.text(xa + 0.07, (E[k] + E[k + 1]) / 2, _fmt_minus("Δ$\\mathit{G}$ = %.2f" % d[k]),
                color=RED, fontsize=text_size, ha="left", va="center", zorder=7,
                bbox=dict(fc="white", ec="none", pad=0.5))
    if states is not None:
        ax.set_xticks(x)
        ax.set_xticklabels(states)
        ax.tick_params(axis="x", length=0)
    _clean(ax)


def map2d(ax, X, Y, Z, levels=14, cmap=SEQ, points=None, labels=None, highlight=None, lines=True,
          point_color="white"):
    """Filled contour map over two descriptors (a 2D activity volcano), optional points on top."""
    m = ax.contourf(X, Y, Z, levels=levels, cmap=cmap, zorder=0)
    if lines:
        ax.contour(X, Y, Z, levels=m.levels, colors="white", linewidths=0.3, zorder=1)
    if points is not None:
        px, py = points
        ax.scatter(px, py, s=10, color=point_color, edgecolor=INK, lw=0.5, zorder=4)
        if highlight is not None:
            ax.scatter(px[highlight], py[highlight], s=16, color=RED, edgecolor="white", lw=0.5, zorder=5)
        if labels is not None:
            for xx, yy, t in zip(px, py, labels):
                ax.annotate(t, (xx, yy), xytext=(3, 2), textcoords="offset points", fontsize=SMALL, color=INK,
                            zorder=6, bbox=dict(fc="white", ec="none", pad=0.3, alpha=0.75))
    return m


# --------------------------------------------------------------------------- spectra: zoom insets, stacks

def zoom_inset(pg, ax, xlim, ylim, rect_mm, ticks=False, box_color=RED, line_color=INK, lw_scale=1.25,
               copy_lines=True, include=None):
    """Magnify a key region of `ax` in a separate axes placed at `rect_mm` (x, y, w, h in page millimetres).

    The region gets a dashed box on the parent, and two dashed leader lines join it to the near edge of the inset,
    as in XANES/XPS figures where the shift sits in a small window. The parent's lines are copied into the inset
    (thicker by `lw_scale`) unless `copy_lines=False`; `include` limits the copy to lines with those labels, so
    reference curves that only cross the window stay out of the inset. Draw extra marks (labels, `shift_arrow`) on the returned
    axes. The inset is an ordinary page axes, so the figure editor can move and resize it.
    Returns the inset axes.
    """
    axin = pg.ax(*rect_mm)
    if copy_lines:
        for ln in ax.get_lines():
            x, y = (np.asarray(v, float) for v in ln.get_data())
            if len(np.atleast_1d(x)) < 3 or (include is not None and ln.get_label() not in include):
                continue
            # keep only the stretch inside the window (plus one point either side, so lines still reach the frame):
            # an SVG bounding box ignores clipping, and a full-length copy made the editor's selection box of the
            # inset cover half the figure
            inside = (x >= min(xlim)) & (x <= max(xlim)) & (y >= min(ylim)) & (y <= max(ylim))
            keep = inside | np.roll(inside, 1) | np.roll(inside, -1)
            if not keep.any():
                continue
            yk = np.where(keep, y, np.nan)
            axin.plot(x, yk, color=ln.get_color(), lw=ln.get_linewidth() * lw_scale, ls=ln.get_linestyle(),
                      zorder=ln.get_zorder(), solid_capstyle="round", label=ln.get_label())
    axin.set_xlim(*xlim)
    axin.set_ylim(*ylim)
    for s in axin.spines.values():
        s.set_linewidth(0.6)
        s.set_color(INK)
    if not ticks:
        axin.set_xticks([])
        axin.set_yticks([])
    ax.add_patch(Rectangle((xlim[0], ylim[0]), xlim[1] - xlim[0], ylim[1] - ylim[0], fill=False, ec=box_color,
                           lw=0.8, ls=(0, (3, 2)), zorder=8))
    pg.fig.add_artist(_ZoomLeaders(ax, axin, xlim, ylim, line_color))
    return axin


class _ZoomLeaders(Line2D):
    """The two dashed leaders from a zoom box to its inset. The corners are chosen when the figure is drawn, from
    where the inset is at that moment, so an inset moved or resized in the figure editor (tweaks.json) is joined
    from the side that faces it. A Line2D in display coordinates, so the editor lists it as one dashed line."""

    def __init__(self, ax, axin, xlim, ylim, color):
        from matplotlib.transforms import IdentityTransform
        super().__init__([], [], color=color, lw=0.6, ls=(0, (3, 2)), zorder=7, transform=IdentityTransform())
        self._zoom = (ax, axin, xlim, ylim)

    def _corners(self, renderer):
        ax, axin, (x0, x1), (y0, y1) = self._zoom
        box = ax.transData.transform([[x0, y0], [x1, y1]])
        bl, tr = box.min(axis=0), box.max(axis=0)
        ins = axin.get_window_extent(renderer)
        bx, by = (bl + tr) / 2
        ix, iy = (ins.x0 + ins.x1) / 2, (ins.y0 + ins.y1) / 2
        horizontal = (abs(ix - bx) / max(ins.width + tr[0] - bl[0], 1)
                      >= abs(iy - by) / max(ins.height + tr[1] - bl[1], 1))
        if horizontal:                       # inset beside the box: join the facing vertical edges
            xb = tr[0] if ix > bx else bl[0]
            xi = ins.x0 if ix > bx else ins.x1
            return [(xb, bl[1]), (xi, ins.y0)], [(xb, tr[1]), (xi, ins.y1)]
        yb = tr[1] if iy > by else bl[1]     # inset above or below: join the facing horizontal edges
        yi = ins.y0 if iy > by else ins.y1
        return [(bl[0], yb), (ins.x0, yi)], [(tr[0], yb), (ins.x1, yi)]

    def draw(self, renderer):
        a, b = self._corners(renderer)
        self.set_data([a[0][0], a[1][0], np.nan, b[0][0], b[1][0]], [a[0][1], a[1][1], np.nan, b[0][1], b[1][1]])
        super().draw(renderer)


def shift_arrow(ax, xy_from, xy_to, color=DARK_B, alpha=0.55, width=1.0, text=None, text_xy=None, size=ANNOT + 1.4,
                bold=True):
    """A wide, translucent block arrow for the direction of a change (an edge shift, a peak gain, a ratio rise),
    with an optional label. Coordinates are data coordinates of `ax`. One arrow per change; pair two arrows in
    opposite directions to show a reversible switch (gas A ↔ gas B)."""
    ax.annotate("", xy=xy_to, xytext=xy_from,
                arrowprops=dict(arrowstyle="simple,head_length=0.9,head_width=1.0,tail_width=0.45",
                                mutation_scale=11 * width, fc=color, ec="none", alpha=alpha, shrinkA=0, shrinkB=0),
                zorder=9)
    if text:
        tx, ty = text_xy if text_xy is not None else xy_from
        ax.text(tx, ty, text, fontsize=size, fontweight="bold" if bold else "normal", color=INK, ha="center",
                va="center", zorder=10)


def stacked(ax, x, ys, labels, offset=None, dx=0.0, colors=None, baselines=None, components=None, raw=None,
            notes=None, top_first=True, label_x=None, note_x=None, lw=1.1, comp_alpha=0.35, raw_size=2.2,
            label_size=ANNOT + 1.0, note_size=ANNOT + 0.6, invert_x=False, ylabel="Intensity (a.u.)",
            label_at="below"):
    """Offset stack of comparable curves (XPS, XRD, Raman, spectra across loadings or treatments).

    ys:          list of 1-D arrays on the common x (the fitted envelope or the measured curve).
    offset:      vertical step between traces (default 1.1 × the largest trace range).
    dx:          horizontal step per trace for an oblique (staggered, tilted) stack; 0 for a plain vertical stack.
    baselines:   per trace, an array or (y_left, y_right) for a sloped linear background, drawn as a thin line;
                 a sloped background is what makes an XPS stack read "tilted".
    components:  per trace, list of (y_component, colour) filled down to the baseline (fitted peaks).
    raw:         per trace, measured points drawn as small hollow markers under the fit.
    notes:       per trace, a short value printed under the right end ("Ce$^{3+}$ ratio = 0.09").
    label_at:    "below" (default): the name under the left end of its trace, in the gap above the next trace,
                 as in XPS stacks; "above": over the left end; "end": after the right end of the trace (oblique
                 stacks, leave room with xlim).
    The y axis carries no ticks (arbitrary units). With dx > 0 the upper traces move right, so the front (lowest)
    trace keeps the true x scale. Leave enough offset that the gap under each trace holds its name and note.
    Returns the vertical offsets used.
    """
    n = len(ys)
    colors = colors or [DARK_B] * n
    rng_ = max(float(np.nanmax(y) - np.nanmin(y)) for y in ys)
    step = 1.1 * rng_ if offset is None else offset
    order = list(range(n))
    levels = [(n - 1 - k) * step if top_first else k * step for k in order]
    x = np.asarray(x, float)
    lo_x, hi_x = (x.max(), x.min()) if invert_x else (x.min(), x.max())
    lx = label_x if label_x is not None else lo_x
    nx = note_x if note_x is not None else hi_x
    for k in order:
        off, sh = levels[k], dx * (n - 1 - k if top_first else k)   # upper traces move right
        xs = x + sh
        if baselines is not None and baselines[k] is not None:
            b = baselines[k]
            base = np.interp(x, [x.min(), x.max()], b) if len(b) == 2 and len(x) != 2 else np.asarray(b, float)
        else:
            base = np.zeros_like(x)
        if components is not None and components[k]:
            for yc, c in components[k]:
                ax.fill_between(xs, base + off, np.asarray(yc) + off, color=c, alpha=comp_alpha, lw=0, zorder=2)
                ax.plot(xs, np.asarray(yc) + off, color=c, lw=0.5, zorder=3)
        if baselines is not None and baselines[k] is not None:
            ax.plot(xs, base + off, color=MID, lw=0.6, zorder=3)
        if raw is not None and raw[k] is not None:
            ax.scatter(xs, np.asarray(raw[k]) + off, s=raw_size, facecolors="none", edgecolors=OTHER, lw=0.35,
                       zorder=4, rasterized=True)
        ax.plot(xs, np.asarray(ys[k]) + off, color=colors[k], lw=lw, zorder=5, label=labels[k])
        srt = np.argsort(x)
        y_at = float(np.interp(lx, x[srt], np.asarray(ys[k])[srt]))
        b_at = float(np.interp(lx, x[srt], base[srt]))
        # ha refers to the screen, so a label at the left end reads rightwards even on an inverted axis
        if label_at == "above":
            ax.text(lx + sh, off + max(y_at, b_at) + 0.12 * step, labels[k], fontsize=label_size,
                    fontweight="bold", color=INK, ha="left", va="bottom", zorder=6)
        elif label_at == "end":
            y_end = float(np.interp(nx, x[srt], np.asarray(ys[k])[srt]))
            ax.text(nx + sh + 0.015 * abs(x.max() - x.min()) * (-1 if invert_x else 1), off + y_end, labels[k],
                    fontsize=label_size, fontweight="bold", color=INK, ha="left", va="center", zorder=6)
        else:
            ax.text(lx + sh, off + min(y_at, b_at) - 0.05 * step, labels[k], fontsize=label_size,
                    fontweight="bold", color=INK, ha="left", va="top", zorder=6)
        if notes is not None and notes[k]:
            b_end = float(np.interp(nx, x[srt], base[srt]))
            ax.text(nx + sh, off + b_end - 0.05 * step, notes[k], fontsize=note_size, fontweight="bold", color=INK,
                    ha="right", va="top", zorder=6)
    if invert_x:
        ax.invert_xaxis()
    ax.set_yticks([])
    ax.set_ylabel(ylabel)
    return levels


def demo_stamp(pg, text="SYNTHETIC DEMO DATA — not a result", y_mm=None):
    """Loud label for demo figures. A demo composite was once mistaken for a manuscript figure."""
    y = 1.5 if y_mm is None else y_mm
    pg.fig.text((pg.W - 3) / pg.W, y / pg.H, text, ha="right", va="bottom", fontsize=6.5, color=RED,
                fontweight="bold")
