"""Figure 3 — backward design separates economic targets from physical reachability.

Four-panel composite, 183 x 122 mm.

a  Activity-only backward target after full process reoptimization.
b  Activity-only reachability on the strict E_N scaling manifold.
c  Joint direct-activity / lifetime / recovery economic target region.
d  Exact strict-scaling x lifecycle reachability boundary over all 14,136 process states.

Every numerical value is read from pinned NH3-FINAL-1.1 provenance or audited
2026-09-29 derived outputs. No scientific calculation is performed here.

    python make_fig3.py  -> Fig3.{svg,pdf,png}
"""
import csv
import json
import os
import sys

import numpy as np
from matplotlib.ticker import FixedLocator, LogLocator, MultipleLocator, NullFormatter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from style import (DARK_B, DARK_G, FE, GRID, INK, MID, OS, RED, RU,  # noqa: E402
                   TINT_B, TINT_G, boxed, fmt_minus, Page)

REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
RUN = os.path.join(
    REPO,
    "provenance/nh3_final_1_1/source_harness/outputs/nh3_final_20260905T134204Z",
)
CL = os.path.join(RUN, "closure")
SUP = os.path.join(REPO, "analysis", "supervisor_2026_09_20")
BWD = os.path.join(REPO, "analysis", "fe_bridge_backward_2026_09_29")


def read_csv(path):
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


sweep = read_csv(os.path.join(CL, "breakeven_sweep.csv"))
scal = read_csv(os.path.join(CL, "scaling_reachability.csv"))
results = json.load(open(os.path.join(RUN, "results.json"), encoding="utf-8"))
bk = results["backward_reachability"]
mc = json.load(open(os.path.join(SUP, "nh3_cost_mc_summary.json"), encoding="utf-8"))["alpha_star"]
direct_boundary = read_csv(os.path.join(BWD, "activity_lifecycle_certified_boundary.csv"))
direct_keys = read_csv(os.path.join(BWD, "activity_lifecycle_target_keypoints.csv"))
strict_boundary = read_csv(os.path.join(BWD, "scaling_lifecycle_exact_global_boundary.csv"))
strict_keys = read_csv(os.path.join(BWD, "scaling_lifecycle_exact_keypoints.csv"))
strict_summary = json.load(open(os.path.join(BWD, "scaling_lifecycle_exact_summary.json"), encoding="utf-8"))

A_STAR = float(bk["Ru_activity_break_even_multiplier"])
G673 = float(bk["Ru_scaling_max_gain_673K"])
GALL = float(bk["Ru_scaling_max_gain_all_states"])
BEST_C = float(bk["Ru_best_scaling_cost_USD_t"])
BEST_E = float(bk["Ru_best_scaling_EN_eV"])
FE_COST = float(results["deterministic"]["metals"]["Fe"]["feasible"]["total_cost"])
RU_COST = float(results["deterministic"]["metals"]["Ru"]["feasible"]["total_cost"])
P05, P50, P95 = float(mc["p05"]), float(mc["p50"]), float(mc["p95"])
QCRIT = float(strict_summary["critical_lifecycle_factor_q_per_y"])

assert abs(A_STAR - 201.2234429878984) < 1e-9
assert abs(GALL - 2.5245651130943445) < 1e-12
assert abs(BEST_C - 21.397872966049547) < 1e-8
assert abs(BEST_E - (-1.215)) < 1e-12
assert strict_summary["tested_lifecycle_envelope"]["intersects_strict_scaling_manifold"] is False
assert abs(QCRIT - 0.00044068345398945024) < 1e-12

pg = Page(183.0, 122.0)

# --------------------------------------------------------------------------------------
# a — activity-only backward target
# --------------------------------------------------------------------------------------
pg.letter("a", 2.0, 119.5)
pg.title("Activity-only economic target", 12.0, 116.5)
a = pg.ax(13.0, 85.0, 74.0, 24.0)
boxed(a)
lit = pg.ax(13.0, 70.0, 74.0, 13.0, sharex=a)   # measured gains over a reference Ru catalyst
boxed(lit)

alpha = np.array([float(r["alpha"]) for r in sweep])
ru_cost = np.array([float(r["Ru_cost"]) for r in sweep])

a.axvspan(1.0, GALL, color=TINT_G, lw=0, zorder=0)
a.axvspan(P05, P95, color="#F8DADA", lw=0, zorder=0)
a.axhline(FE_COST, color=FE, lw=1.0, ls=(0, (3, 1.8)), zorder=2)
a.plot(alpha, ru_cost, color=RU, lw=1.25, zorder=3)
a.axvline(A_STAR, color=RED, lw=0.9, ls=(0, (3, 1.8)), zorder=2)

i1 = int(np.argmin(np.abs(alpha - 1.0)))
a.plot(1.0, ru_cost[i1], "o", ms=3.6, mfc=RU, mec=INK, mew=0.5, zorder=5)
a.plot(A_STAR, FE_COST, "o", ms=4.0, mfc=RED, mec=INK, mew=0.5, zorder=6)

a.text(1.22, ru_cost[i1] + 0.25, "current Ru\n%.2f" % RU_COST,
       fontsize=5.8, color=DARK_B, va="bottom", ha="left")
a.text(A_STAR * 1.08, FE_COST + 0.35, r"$\alpha^*$ = %.1f×" % A_STAR,
       fontsize=6.2, color=RED, fontweight="bold", va="bottom", ha="left")
a.text(1.05, 15.6, "strict-scaling\nheadroom ≤ %.3f×" % GALL,
       fontsize=5.3, color=DARK_G, fontweight="bold", va="bottom", ha="left")
a.text(P05 / 1.12, 22.9, "economic uncertainty\np05–p95: %.1f×–%.0f×" % (P05, P95),
       fontsize=5.5, color=RED, ha="right", va="top")
a.text(4.0, FE_COST - 0.12, "Fe %.3f USD t$^{-1}$" % FE_COST, fontsize=5.4, color=DARK_G, ha="left", va="top")

a.set_xscale("log")
a.set_xlim(0.3, 800)
a.set_ylim(14.4, 23.2)
a.xaxis.set_major_locator(LogLocator(base=10, numticks=5))
a.xaxis.set_minor_locator(LogLocator(base=10, subs=np.arange(2, 10), numticks=20))
a.xaxis.set_minor_formatter(NullFormatter())
a.yaxis.set_major_locator(FixedLocator([15, 19, 23]))
a.yaxis.set_minor_locator(MultipleLocator(1.0))
a.set_ylabel("Ru cost\n(USD t$^{-1}$ NH$_3$)")
a.tick_params(axis="x", labelbottom=False)

# literature: measured activity gains of promoted, support-modified and confined Ru over a reference Ru catalyst,
# on the same multiplier axis (analysis/promoted_ru_literature_2026_10_05/fig3_literature_points.csv)
LIT = read_csv(os.path.join(REPO, "analysis", "promoted_ru_literature_2026_10_05", "fig3_literature_points.csv"))
ROW = {"promoter": 2, "support": 1, "confinement": 0}
lit.axvspan(1.0, GALL, color=TINT_G, lw=0, zorder=0)
lit.axvspan(P05, P95, color="#F8DADA", lw=0, zorder=0)
lit.axvline(1.0, color=MID, lw=0.5, ls=(0, (2, 1.5)), zorder=1)
for r in LIT:
    y, lo, hi = ROW[r["row"]], float(r["factor_low"]), float(r["factor_high"])
    if r["id"] == "P04":          # Cs-Ru/MgO: plot the 350 C lower bound (>134x) just below the promoter row
        y, lo = y - 0.42, hi
    tof = r["basis"] == "TOF"
    col = RED if r["row"] == "promoter" else (DARK_B if r["row"] == "support" else MID)
    if hi > lo:
        lit.plot([lo, hi], [y, y], color=col, lw=1.6, solid_capstyle="round", zorder=3)
    for v in {lo, hi}:
        lit.plot(v, y, "o" if tof else "s", ms=3.0, mfc=col if tof else "white", mec=col, mew=0.8, zorder=4)
    if r["lower_bound"] == "1":
        lit.annotate("", (hi * 1.9, y), xytext=(hi * 1.05, y),
                     arrowprops=dict(arrowstyle="-|>", lw=0.6, color=col, mutation_scale=4.5), zorder=4)
LBL = [  # label, x, y, ha, va
    ("Cs–Ru/YSZ", 10.0, 2.32, "center", "bottom"), ("Cs-, Ba–Ru/C", 57.0, 2.0, "right", "center"),
    ("Ba–Ru/BN, 5 MPa", 112.0, 2.32, "left", "bottom"), ("Cs–Ru/MgO", 270.0, 1.58, "left", "center"),
    ("electride, hydride", 7.4, 1.0, "right", "center"), ("Ba–Ca(NH$_2$)$_2$*", 33.5, 1.32, "center", "bottom"),
    ("Ru inside CNT", 0.56, 0.0, "left", "center"),
]
for text, x, y, ha, va in LBL:
    lit.text(x, y, text, fontsize=4.9, ha=ha, va=va, color=INK)
lit.set_ylim(-0.6, 3.05)
lit.set_yticks([2, 1, 0])
lit.set_yticklabels(["promoters", "supports", "confinement"], fontsize=5.4)
lit.tick_params(axis="y", length=0)
lit.set_xlabel(r"Ru activity multiplier $\alpha$ (literature: measured gain over reference Ru)")

# --------------------------------------------------------------------------------------
# b — activity-only strict-scaling reachability
# --------------------------------------------------------------------------------------
pg.letter("b", 93.0, 119.5)
pg.title("Activity-only physical reachability", 103.0, 116.5)
b = pg.ax(105.0, 70.0, 69.0, 39.0)
boxed(b)

cE = np.array([float(r["E_N_eV"]) for r in scal if r["Ru_min_feasible_cost"]])
cC = np.array([float(r["Ru_min_feasible_cost"]) for r in scal if r["Ru_min_feasible_cost"]])
b.axhline(FE_COST, color=FE, lw=1.0, ls=(0, (3, 1.8)), zorder=2)
b.plot(cE, cC, color=RU, lw=1.25, zorder=3)
b.fill_between(cE, FE_COST, cC, where=cC >= FE_COST, color="#F8DADA", alpha=0.7, zorder=0)

ib = int(np.argmin(cC))
b.plot(cE[ib], cC[ib], "o", ms=4.0, mfc=RU, mec=INK, mew=0.5, zorder=5)
b.annotate(
    "best %.3f\nat %s eV" % (cC[ib], fmt_minus("%.3f" % cE[ib])),
    xy=(cE[ib], cC[ib]), xytext=(-1.51, 23.7),
    fontsize=5.8, va="top", ha="left",
    arrowprops=dict(arrowstyle="-", lw=0.5, color=MID, shrinkA=1, shrinkB=2),
)
b.text(0.97, 0.91, "still +%.3f USD t$^{-1}$ above Fe" % (BEST_C - FE_COST),
       transform=b.transAxes, fontsize=5.6, color=RED, ha="right", va="top",
       fontweight="bold")
b.text(0.97, 0.78, "673 K headroom %.3f×\nstate-specific max %.3f×" % (G673, GALL),
       transform=b.transAxes, fontsize=5.4, color=DARK_G, ha="right", va="top")
b.text(0.97, 0.08, "Fe %.3f" % FE_COST, transform=b.transAxes,
       fontsize=5.6, color=DARK_G, ha="right", va="bottom")

b.set_xlim(-1.62, -0.62)
b.set_ylim(14.4, 28.0)
b.xaxis.set_major_locator(FixedLocator([-1.5, -1.25, -1.0, -0.75]))
b.set_xticklabels([fmt_minus(x) for x in ("-1.5", "-1.25", "-1.0", "-0.75")])
b.xaxis.set_minor_locator(MultipleLocator(0.05))
b.yaxis.set_major_locator(FixedLocator([15, 18, 21, 24, 27]))
b.yaxis.set_minor_locator(MultipleLocator(1))
b.set_xlabel(r"Ru descriptor $E_\mathrm{N}$ on strict scaling line (eV)")
b.set_ylabel(r"Lowest Ru cost (USD t$^{-1}$ NH$_3$)")

# --------------------------------------------------------------------------------------
# c — joint direct activity / lifecycle target
# --------------------------------------------------------------------------------------
pg.letter("c", 2.0, 62.0)
pg.title("Joint economic target region", 12.0, 59.0)
c = pg.ax(13.0, 13.0, 74.0, 39.0)
boxed(c)

da = np.array([float(r["alpha"]) for r in direct_boundary])
m = da <= 3.000001
da = da[m]
curves = {
    10: np.array([100.0 * float(r["required_recovery_at_10y"]) for r in direct_boundary])[m],
    15: np.array([100.0 * float(r["required_recovery_at_15y"]) for r in direct_boundary])[m],
    20: np.array([100.0 * float(r["required_recovery_at_20y"]) for r in direct_boundary])[m],
}
line_style = {
    10: (RU, "-", "10 y"),
    15: (OS, "-", "15 y"),
    20: (DARK_G, "-", "20 y"),
}
for life in (10, 15, 20):
    col, ls, lab = line_style[life]
    c.plot(da, curves[life], color=col, lw=1.15, ls=ls, label=lab)

c.axhline(99.0, color=MID, lw=0.8, ls=(0, (3, 1.8)))
for r in direct_keys:
    life = int(float(r["catalyst_life_y"]))
    rec = float(r["Ru_recovery_fraction"])
    if abs(rec - 0.99) > 1e-12:
        continue
    aa = float(r["certified_upper_bound_required_direct_activity_multiplier"])
    col = line_style[life][0]
    c.plot(aa, 99.0, "o", ms=3.8, mfc=col, mec=INK, mew=0.45, zorder=5)
    c.text(aa, 98.82, "%.3f×" % aa, fontsize=5.2, color=col,
           ha="center", va="top")

c.text(0.03, 0.08, "curves = conservative direct-activity targets\n(not physical reachability)",
       transform=c.transAxes, fontsize=5.3, color=MID, ha="left", va="bottom")
c.text(0.97, 0.92, "99% recovery", transform=c.transAxes,
       fontsize=5.4, color=MID, ha="right", va="top")
c.legend(loc="lower left", bbox_to_anchor=(0.02, 0.28), fontsize=5.5, handlelength=2.2)

c.set_xlim(0.95, 3.02)
c.set_ylim(97.4, 100.02)
c.xaxis.set_major_locator(FixedLocator([1.0, 1.5, 2.0, 2.5, 3.0]))
c.xaxis.set_minor_locator(MultipleLocator(0.1))
c.yaxis.set_major_locator(FixedLocator([98, 99, 100]))
c.yaxis.set_minor_locator(MultipleLocator(0.2))
c.set_xlabel(r"Direct Ru activity multiplier $\alpha$")
c.set_ylabel("Ru recovery required for Fe parity (%)")

# --------------------------------------------------------------------------------------
# d — exact strict-scaling x lifecycle reachability
# --------------------------------------------------------------------------------------
pg.letter("d", 93.0, 62.0)
pg.title("Strict-scaling joint reachability", 103.0, 59.0)
d = pg.ax(105.0, 13.0, 69.0, 39.0)
boxed(d)

life = np.array([float(r["life_y"]) for r in strict_boundary])
req = np.array([float(r["required_recovery_percent"]) for r in strict_boundary])

# Region above boundary reaches parity under strict scaling; tested box is life<=20, recovery<=99%.
d.fill_between(life, req, 100.2, color=TINT_B, alpha=0.8, zorder=0)
d.fill_between([5, 20], [97.4, 97.4], [99.0, 99.0], color=TINT_G, alpha=0.9, zorder=0)
d.plot(life, req, color=RU, lw=1.35, zorder=3, label="Fe-parity boundary")
d.axhline(99.0, color=MID, lw=0.75, ls=(0, (3, 1.8)))
d.axvline(20.0, color=MID, lw=0.75, ls=(0, (3, 1.8)))

corner = strict_summary["tested_lifecycle_envelope"]["best_corner"]
corner_cost = float(corner["best_strict_scaling_cost_USD_t"])
corner_margin = float(corner["margin_vs_Fe_USD_t"])
boundary20 = float(strict_summary["boundary_examples"]["required_recovery_at_20y"]) * 100.0
life99 = float(strict_summary["boundary_examples"]["required_life_at_99pct_recovery_y"])

d.plot(20.0, 99.0, "o", ms=4.0, mfc=FE, mec=INK, mew=0.5, zorder=5)
d.plot(20.0, boundary20, "o", ms=4.0, mfc=RU, mec=INK, mew=0.5, zorder=5)
d.plot(life99, 99.0, "o", ms=3.7, mfc=RU, mec=INK, mew=0.5, zorder=5)

d.annotate(
    "tested corner\n20 y + 99%%\n+%.3f USD t$^{-1}$" % corner_margin,
    xy=(20.0, 99.0), xytext=(26.2, 99.55),
    fontsize=5.4, va="top", ha="left",
    arrowprops=dict(arrowstyle="-", lw=0.5, color=MID, shrinkA=1, shrinkB=2),
)
d.annotate(
    "parity at 20 y:\n%.4f%%" % boundary20,
    xy=(20.0, boundary20), xytext=(7.0, 99.70),
    fontsize=5.4, va="top", ha="left", color=DARK_B,
    arrowprops=dict(arrowstyle="-", lw=0.5, color=MID, shrinkA=1, shrinkB=2),
)
d.text(0.97, 0.10, r"$q^*=(1-r)/L=4.4068\times10^{-4}$ y$^{-1}$",
       transform=d.transAxes, fontsize=5.3, ha="right", va="bottom")
d.text(0.03, 0.08, "tested box", transform=d.transAxes,
       fontsize=5.3, color=DARK_G, fontweight="bold", ha="left", va="bottom")
d.text(0.97, 0.92, "strict-scaling parity region", transform=d.transAxes,
       fontsize=5.3, color=DARK_B, fontweight="bold", ha="right", va="top")

d.set_xlim(5, 50)
d.set_ylim(97.4, 100.05)
d.xaxis.set_major_locator(FixedLocator([10, 20, 30, 40, 50]))
d.xaxis.set_minor_locator(MultipleLocator(5))
d.yaxis.set_major_locator(FixedLocator([98, 99, 100]))
d.yaxis.set_minor_locator(MultipleLocator(0.2))
d.set_xlabel("Catalyst lifetime (y)")
d.set_ylabel("Ru recovery required for Fe parity (%)")

pg.save(HERE, "Fig3")
