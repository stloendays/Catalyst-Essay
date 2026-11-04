"""Cost-change attribution, upstream metric against the other properties (exact decomposition D).

    python analysis/leverage_criterion_2026_10_12/make_figure.py      # after run_leverage_criterion.py

a  phi_U (the cost change attributed to the upstream metric, % of C_i) against the cost advantage the other
   properties give j (-sum phi_k, % of C_i), every pre-registered case; filled markers inverted, open preserved.
   Above the diagonal the other properties outweigh the upstream metric (equivalent to C_j < C_i).
b  property-class composition of the attribution per system and outcome: mean of phi_k / sum_k |phi_k| (signed;
   right favours i, the upstream leader; left favours j).
Writes fig_attribution.{svg,pdf,png}. Uses the shared composite style (figures/composite/style.py, read only).
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "figures" / "composite"))
import style as S  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.ticker import FixedLocator, NullFormatter  # noqa: E402

cases = pd.read_csv(HERE / "cases.csv")
props = pd.read_csv(HERE / "properties.csv")
cases = cases[cases.U_D.notna()].copy()
cases["actual_inverted"] = cases.actual_inverted.astype(str) == "True"

SYS = [("Au", "nominal", "Au/TiO$_2$", "o", S.MID_G),
       ("NH3", "frozen", "NH$_3$", "s", S.DARK_B),
       ("MeOH", "S5", "MeOH S5", "^", S.FE),
       ("MeOH", "S6", "MeOH S6", "v", S.DARK_G),
       ("Re", "D01 v3, 2 % purge", "Re/TiO$_2$", "D", S.RU)]
CLASSES = [("upstream metric", "#5A6480"), ("metal price / loading", "#D8894E"),
           ("temperature / operating window", "#9DACCB"), ("single-pass conversion", "#B3B8C0"),
           ("selectivity CO", "#89AA7B"), ("selectivity CH4", "#5E7A52"), ("selectivity CO+CH4", "#CBD7C3")]

pg = S.Page(183.0, 95.0)

# ---- a: upstream attribution vs the other properties' advantage for j --------------------------------------------
a = pg.ax(16.0, 22.0, 62.0, 66.0)
S.boxed(a)
cases["x"] = 100.0 * cases.U_D / cases.C_i
cases["y"] = -100.0 * cases.O_D / cases.C_i
lin = 0.01
xlo, lo, hi = 3e-3, -1e4, 1e3
a.set_xscale("symlog", linthresh=lin, linscale=0.5)
a.set_yscale("symlog", linthresh=lin, linscale=0.5)
grid = np.concatenate([np.linspace(xlo, lin, 20), np.logspace(-2, 3, 300)])
a.fill_between(grid, grid, hi, color=S.TINT_B, lw=0, zorder=0)       # y > x: the other properties outweigh U
a.plot(grid, grid, color=S.INK, lw=0.6, zorder=1)
a.axhline(0, color=S.LINE, lw=0.5, zorder=0)
for s, sc, lab, mk, col in SYS:
    d = cases[(cases.system == s) & (cases.scenario == sc)]
    for inv, face in ((False, "white"), (True, col)):
        e = d[d.actual_inverted == inv]
        a.scatter(e.x, e.y, s=12, marker=mk, facecolor=face, edgecolor=col, lw=0.7, zorder=3)
a.set_xlim(xlo, hi)
a.set_ylim(lo, hi)
yt = [-1e4, -100, -1, 0, 1e-2, 1, 100]
fmt = {-1e4: "−10$^4$", -100: "−100", -1: "−1", 0: "0", 1e-2: "0.01", 1: "1", 100: "100"}
a.yaxis.set_major_locator(FixedLocator(yt))
a.set_yticklabels([fmt[t] for t in yt])
a.xaxis.set_major_locator(FixedLocator([1e-2, 1, 100]))
a.set_xticklabels(["0.01", "1", "100"])
a.xaxis.set_minor_formatter(NullFormatter())
a.yaxis.set_minor_formatter(NullFormatter())
a.set_xlabel("Upstream metric, $\\phi_U$ (% of $C_i$)")
a.set_ylabel("Other properties, advantage to $j$ (% of $C_i$)")
# upper-left corner above y = 100 is empty in every system (y <= 97 %), lower right below y = 0 holds no inverted case
a.text(4.5e-3, 330, "inverted: other properties\noutweigh the upstream metric", fontsize=6.0, va="center", ha="left")
a.text(6, -0.04, "preserved", fontsize=6.0, va="center", ha="left")
handles = [Line2D([], [], marker=mk, ls="", mfc=col, mec=col, ms=4.0) for _, _, _, mk, col in SYS]
handles += [Line2D([], [], marker="o", ls="", mfc="white", mec=S.INK, ms=4.0),
            Line2D([], [], marker="o", ls="", mfc=S.INK, mec=S.INK, ms=4.0)]
labels = [x[2] for x in SYS] + ["preserved", "inverted"]
pg.fig.legend(handles, labels, loc="lower left", bbox_to_anchor=(14.0 / 183.0, 0.005), ncol=4, fontsize=5.8,
              frameon=False, handletextpad=0.2, columnspacing=0.9, labelspacing=0.35)
pg.letter("a", 2.0, 94.0)
pg.title("Upstream metric against the other properties", 7.0, 94.0)

# ---- b: property-class composition ------------------------------------------------------------------------------
b = pg.ax(124.0, 22.0, 55.0, 66.0)
S.boxed(b)
pp = props[props.phi_D.notna() & props.case_id.isin(cases.case_id)]
rows = []
for s, sc, lab, _, _ in SYS:
    for inv in (False, True):
        ids = cases[(cases.system == s) & (cases.scenario == sc) & (cases.actual_inverted == inv)].case_id
        if not len(ids):
            continue
        d = pp[pp.case_id.isin(ids)]
        sh = d.groupby("property_class").phi_D_share_of_abs_total.sum() / len(ids)
        rows.append((f"{lab}, {'inverted' if inv else 'preserved'} ({len(ids)})", sh))
y = np.arange(len(rows))[::-1]
for yy, (name, sh) in zip(y, rows):
    pos, neg = 0.0, 0.0
    for cl, col in CLASSES:
        v = float(sh.get(cl, 0.0))
        left = pos if v >= 0 else neg
        b.barh(yy, v, left=left, height=0.62, color=col, ec=S.INK, lw=0.3, zorder=2)
        if v >= 0:
            pos += v
        else:
            neg += v
b.axvline(0, color=S.INK, lw=0.6, zorder=3)
b.set_yticks(y)
b.set_yticklabels([r[0] for r in rows], fontsize=6.0)
b.set_xlim(-1.0, 1.0)
b.set_ylim(-0.7, len(rows) - 0.3)
b.xaxis.set_major_locator(FixedLocator([-1, -0.5, 0, 0.5, 1]))
b.set_xticklabels(["−1", "−0.5", "0", "0.5", "1"])
b.set_xlabel("Signed share $\\phi_k$ / $\\Sigma|\\phi|$  (< 0 favours $j$)")
b.tick_params(axis="y", length=0)
b.text(-0.97, len(rows) - 0.55, "← favours $j$", fontsize=5.6, va="center", ha="left")
b.text(0.97, len(rows) - 0.55, "favours $i$ →", fontsize=5.6, va="center", ha="right")
pg.letter("b", 84.0, 94.0)
pg.title("Composition of the attribution by property class", 89.0, 94.0)
hand = [Line2D([], [], marker="s", ls="", mfc=c, mec=S.INK, mew=0.3, ms=4.3) for _, c in CLASSES]
pg.fig.legend(hand, [c for c, _ in CLASSES], loc="lower left", bbox_to_anchor=(86.0 / 183.0, 0.005), ncol=3,
              fontsize=5.8, frameon=False, handletextpad=0.2, columnspacing=0.9, labelspacing=0.35)
pg.save(str(HERE), "fig_attribution")
