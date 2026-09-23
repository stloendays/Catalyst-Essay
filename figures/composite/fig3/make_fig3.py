"""Figure 3 — backward design separates the activity economics requires from the activity the material can reach.

Composite, 183 mm wide. Every value comes from pinned NH3-FINAL-1.1 provenance or the
preregistered joint cost Monte Carlo:
  closure/breakeven_sweep.csv, closure/scaling_reachability.csv, closure/headline_1_1.json,
  results.json (direct DFT diagnostic), analysis/supervisor_2026_09_20/nh3_cost_mc_{histogram.csv,summary.json}
Step-site renders are reused from ../fig1/renders.

    pur_bridge_env/python make_fig3.py            -> Fig3.{svg,pdf,png}
"""
import csv
import json
import math
import os
import sys

import numpy as np
from matplotlib.patches import FancyBboxPatch
from matplotlib.ticker import FixedLocator, LogLocator, MultipleLocator, NullFormatter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from style import (DARK_B, DARK_G, FE, INK, MID, PAPER, RED, RU, TINT_B, TINT_G,  # noqa: E402
                   Page, boxed, crop_rgba, fmt_minus)

REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
RUN = os.path.join(REPO, "provenance/nh3_final_1_1/source_harness/outputs/nh3_final_20260905T134204Z")
CL = os.path.join(RUN, "closure")
SUP = os.path.join(REPO, "analysis", "supervisor_2026_09_20")
RENDERS = os.path.join(HERE, "..", "fig1", "renders")
KT_673 = 8.617333262e-5 * 673.0                         # eV


def read_csv(path):
    return list(csv.DictReader(open(path, encoding="utf-8")))


sweep = read_csv(os.path.join(CL, "breakeven_sweep.csv"))
scal = read_csv(os.path.join(CL, "scaling_reachability.csv"))
bk = json.load(open(os.path.join(CL, "headline_1_1.json"), encoding="utf-8"))["backward"]
direct = json.load(open(os.path.join(RUN, "results.json"), encoding="utf-8"))["backward_reachability"]["direct_DFT_diagnostic_gain"]
mc = json.load(open(os.path.join(SUP, "nh3_cost_mc_summary.json"), encoding="utf-8"))["alpha_star"]
hist = [r for r in read_csv(os.path.join(SUP, "nh3_cost_mc_histogram.csv")) if r["alpha_count"]]
metals = {r["metal"]: r for r in read_csv(os.path.join(HERE, "..", "fig1", "fig1_metals.csv"))}

A_STAR = bk["Ru_activity_break_even_multiplier"]
G673, GALL = bk["Ru_scaling_max_gain_673K"], bk["Ru_scaling_max_gain_all_states"]
FE_COST = bk["Fe_cost_at_parity"]
BEST_C, BEST_E = bk["Ru_best_scaling_cost_USD_t"], bk["Ru_best_scaling_EN_eV"]
P05, P50, P95 = mc["p05"], mc["p50"], mc["p95"]
assert abs(A_STAR - 201.2234429878984) < 1e-9 and abs(GALL - 2.5245651130943445) < 1e-12
assert abs(P05 - 70.78151661985564) < 1e-9 and sum(int(r["alpha_count"]) for r in hist) == 5000
EN_RU = float(metals["Ru"]["E_N_eV"])

pg = Page(183.0, 122.0)

# ---- a: the backward-design question -------------------------------------------------
pg.letter("a", 2.0, 120.0)
a = pg.canvas(4.0, 66.0, 108.0, 52.0)
a.text(1.5, 50.0, "Backward design", fontsize=7, fontweight="bold", va="top")
yc = 31.0
ru = crop_rgba(os.path.join(RENDERS, "Ru_211_N.png"))
fe = crop_rgba(os.path.join(RENDERS, "Fe_211_N.png"))
for img, xc, name, sub in ((ru, 12.5, "Ru step site", r"$E_\mathrm{N}$ = %s eV" % fmt_minus("%.2f" % EN_RU)),
                           (fe, 95.5, "Fe optimum", "%.3f USD t$^{-1}$" % FE_COST)):
    h = 16.5
    w = h * img.shape[1] / img.shape[0]
    a.imshow(img, extent=(xc - w / 2, xc + w / 2, yc - h / 2, yc + h / 2), zorder=3)
    a.text(xc, yc - h / 2 - 1.4, name, ha="center", va="top", fontsize=6.3, fontweight="bold")
    a.text(xc, yc - h / 2 - 4.4, sub, ha="center", va="top", fontsize=5.8)
fw = dict(arrowstyle="-|>", lw=0.9, color=INK, mutation_scale=6.5, shrinkA=0, shrinkB=0)
a.annotate("", xy=(33.0, yc), xytext=(23.5, yc), arrowprops=fw)
a.text(28.2, yc + 1.2, r"× $\alpha$", ha="center", va="bottom", fontsize=6.5, fontweight="bold")
a.text(28.2, yc - 1.2, "activity", ha="center", va="top", fontsize=5.5, color=MID)
a.add_patch(FancyBboxPatch((33.5, yc - 7.0), 25.0, 14.0, boxstyle="round,pad=0,rounding_size=1.6",
                           fc=PAPER, ec=INK, lw=0.7, zorder=2))
a.text(46.0, yc + 3.9, "Process", ha="center", va="center", fontsize=6.4, fontweight="bold")
a.text(46.0, yc - 0.6, r"$T$, $P$, $T_\mathrm{sep}$ reoptimized", ha="center", va="center", fontsize=5.8)
a.text(46.0, yc - 4.2, "14,136 states, bed ≤ 90 m$^3$", ha="center", va="center", fontsize=5.5, color=MID)
a.annotate("", xy=(67.5, yc), xytext=(58.5, yc), arrowprops=fw)
a.text(73.5, yc, r"$C_\mathrm{Ru}(\alpha)$", ha="center", va="center", fontsize=7.0)
a.text(81.2, yc, "=", ha="center", va="center", fontsize=8.5)
# return path
ret = dict(arrowstyle="-|>", lw=0.9, color=RED, mutation_scale=7, shrinkA=0, shrinkB=0, linestyle=(0, (3, 2)))
yb = 7.0
a.plot([95.5, 95.5], [yb, yc - 16.0], color=RED, lw=0.9, ls=(0, (3, 2)))
a.annotate("", xy=(12.5, yb), xytext=(95.5, yb), arrowprops=ret)
a.plot([12.5, 12.5], [yb, yc - 16.0], color=RED, lw=0.9, ls=(0, (3, 2)))
a.text(54.0, yb + 1.3, r"parity needs $\alpha^*$ = %.0f×" % A_STAR, ha="center", va="bottom", fontsize=6.5,
       fontweight="bold", color=RED)
a.text(54.0, yb - 1.3, "the scaling line delivers at most %.2f×" % GALL, ha="center", va="top", fontsize=6.2,
       color=DARK_G, fontweight="bold")

# ---- b: required versus reachable on one activity axis ---------------------------------------
pg.letter("b", 114.0, 120.0)
b = pg.ax(118.0, 74.0, 63.0, 30.0)
for s in ("left", "right", "top"):
    b.spines[s].set_visible(False)
b.set_xscale("log")
b.set_xlim(0.6, 2500)
b.set_ylim(0, 1.0)
b.set_yticks([])
b.axvspan(1.0, GALL, color=TINT_G, lw=0, zorder=0)
al = np.array([float(r["alpha_left"]) for r in hist])
ar = np.array([float(r["alpha_right"]) for r in hist])
ac = np.array([float(r["alpha_count"]) for r in hist])
b.bar(al, 0.62 * ac / ac.max(), width=ar - al, align="edge", color="#F4C4C4", ec="white", lw=0.3, zorder=2)
for v, lab_, style in ((P05, "p05 %.1f" % P05, (0, (2, 1.5))), (P95, "p95 %.0f" % P95, (0, (2, 1.5)))):
    b.plot([v, v], [0, 0.72], color=RED, lw=0.6, ls=style, zorder=3)
    b.text(v, 0.745, lab_, ha="center", va="bottom", fontsize=5.5, color=RED)
b.plot([A_STAR, A_STAR], [0, 0.84], color=RED, lw=1.2, zorder=4)
b.text(A_STAR, 0.86, r"$\alpha^*$ = %.1f" % A_STAR, ha="center", va="bottom", fontsize=6.3, color=RED,
       fontweight="bold")
reach = [(G673, "scaling line,\n673 K"), (direct, "direct DFT\ncheck"), (GALL, "any process\nstate")]
ym = 0.15
for i, (v, lab_) in enumerate(reach):
    b.plot(v, ym, "o", ms=3.4, mfc=FE, mec=INK, mew=0.5, zorder=5)
    b.text(v, ym + 0.1 + 0.24 * i, lab_ + "  %.2f×" % v, ha="center", va="bottom", fontsize=5.4, linespacing=1.0,
           color=INK)
    b.plot([v, v], [ym + 0.02, ym + 0.09 + 0.24 * i], color=MID, lw=0.4, zorder=4)
b.annotate("", xy=(P05, ym), xytext=(GALL, ym),
           arrowprops=dict(arrowstyle="<->", lw=0.6, color=INK, mutation_scale=5, shrinkA=1, shrinkB=1))
b.text(math.sqrt(GALL * P05), ym + 0.03, "%.0f×" % (P05 / GALL), ha="center", va="bottom", fontsize=6.0,
       fontweight="bold")
b.text(0.64, 0.02, "reachable", fontsize=5.6, color=DARK_G, va="bottom", ha="left", fontweight="bold",
       transform=b.get_xaxis_transform())
b.text(0.995, 0.64, "required,\n5,000 cost\ndraws", transform=b.transAxes, fontsize=5.6, color=RED,
       ha="right", va="top", linespacing=1.1)
b.xaxis.set_major_locator(LogLocator(base=10, numticks=6))
b.xaxis.set_minor_locator(LogLocator(base=10, subs=np.arange(2, 10), numticks=12))
b.xaxis.set_minor_formatter(NullFormatter())
b.set_xlabel(r"Ru activity multiplier $\alpha$")
top = b.secondary_xaxis("top", functions=(lambda x: KT_673 * np.log(np.maximum(x, 1e-9)),
                                          lambda e: np.exp(e / KT_673)))
top.set_xscale("linear")
top.set_xticks([0.0, 0.1, 0.2, 0.3, 0.4])
top.xaxis.set_minor_locator(MultipleLocator(0.05))
top.set_xlabel(r"$k_\mathrm{B}T\,\ln\alpha$ at 673 K (eV)", labelpad=2.5)
top.tick_params(axis="x", which="both", direction="in")

# ---- c: Ru break-even sweep and the process state it moves through ------------------------------
RY0 = 12.0
pg.letter("c", 2.0, 57.0)
c1 = pg.ax(14.0, RY0 + 14.0, 46.0, 24.0)
c2 = pg.ax(14.0, RY0, 46.0, 12.5, sharex=c1)
boxed(c1)
boxed(c2)
al_ = np.array([float(r["alpha"]) for r in sweep])
cost = np.array([float(r["Ru_cost"]) for r in sweep])
Pst = np.array([float(r["P_bar"]) for r in sweep])
Tst = np.array([float(r["T_C"]) for r in sweep])
for ax_ in (c1, c2):
    ax_.axvspan(1.0, GALL, color=TINT_G, lw=0, zorder=0)
    ax_.axvspan(P05, P95, color="#F8DADA", lw=0, zorder=0)
    ax_.axvline(A_STAR, color=RED, lw=0.7, ls=(0, (3, 1.6)), zorder=1)
c1.axhline(FE_COST, color=FE, lw=0.9, ls=(0, (3, 1.6)), zorder=2)
c1.text(8e5, FE_COST + 0.35, "Fe %.2f" % FE_COST, fontsize=5.8, color=DARK_G, ha="right", va="bottom",
        fontweight="bold")
c1.plot(al_, cost, color=RU, lw=1.2, zorder=3)
i1 = int(np.argmin(np.abs(al_ - 1.0)))
c1.plot(1.0, cost[i1], "o", ms=3.4, mfc=RU, mec=INK, mew=0.5, zorder=5)
c1.text(1.25, cost[i1] + 0.5, "Ru %.2f" % cost[i1], fontsize=5.8, va="bottom", color=DARK_B, fontweight="bold")
c1.plot(A_STAR, FE_COST, "o", ms=4.0, mfc=RED, mec=INK, mew=0.5, zorder=6)
c1.text(A_STAR * 1.5, FE_COST + 3.1, r"$\alpha^*$ = %.0f×" % A_STAR, fontsize=6.0, color=RED, fontweight="bold",
        va="bottom")
c1.set_xscale("log")
c1.set_xlim(0.1, 1e6)
c1.set_ylim(10.5, 28)
c1.yaxis.set_major_locator(FixedLocator([12, 16, 20, 24, 28]))
c1.yaxis.set_minor_locator(MultipleLocator(1))
c1.set_ylabel(r"Ru cost (USD t$^{-1}$)")
c1.tick_params(axis="x", labelbottom=False)
c2.step(al_, Pst, where="mid", color=INK, lw=0.8)
c2.set_ylim(60, 520)
c2.yaxis.set_major_locator(FixedLocator([200, 400]))
c2.set_ylabel("$P_\\mathrm{opt}$\n(bar)", labelpad=1.5)
c2.set_xscale("log")
c2.xaxis.set_major_locator(LogLocator(base=10, numticks=8))
c2.xaxis.set_minor_locator(LogLocator(base=10, subs=np.arange(2, 10), numticks=12))
c2.xaxis.set_minor_formatter(NullFormatter())
c2.set_xlabel(r"Ru activity multiplier $\alpha$")
# optimal temperature at the two ends of the sweep
assert Tst[0] == 450.0 and Tst[-1] == 350.0
c2.text(0.13, 385, "450 °C", ha="left", va="top", fontsize=5.4, color=MID)
c2.text(8e5, 125, "350 °C", ha="right", va="bottom", fontsize=5.4, color=MID)
bs = bk["break_even_state"]
c2.annotate("%d °C, %d bar,\nT$_\\mathrm{sep}$ %d °C" % (bs["T_C"], bs["P_bar"], bs["Tsep_C"]), (A_STAR, bs["P_bar"]),
            xytext=(1.3e3, 390), fontsize=5.4, color=RED, va="center", linespacing=1.05,
            arrowprops=dict(arrowstyle="-", lw=0.45, color=RED, shrinkA=0.5, shrinkB=1.5))

# ---- d: activity gain along the scaling line ------------------------------------------------------
pg.letter("d", 66.0, 57.0)
d = pg.ax(78.0, RY0, 44.0, 38.5)
boxed(d)
E = np.array([float(r["E_N_eV"]) for r in scal])
G = np.array([float(r["gain_673K"]) for r in scal])
d.axhspan(P05, P95, color="#F8DADA", lw=0, zorder=0)
d.axhline(A_STAR, color=RED, lw=0.9, zorder=2)
d.text(-1.58, A_STAR * 1.25, r"required: $\alpha^*$ = %.0f×" % A_STAR, fontsize=5.8, color=RED, va="bottom",
       fontweight="bold")
d.text(-1.58, P05 * 0.82, "cost draws p05–p95", fontsize=5.4, color=RED, va="top")
d.axhline(GALL, color=FE, lw=0.8, ls=(0, (3, 1.6)), zorder=2)
d.text(-0.72, GALL * 1.18, "any process state %.2f×" % GALL, fontsize=5.4, color=DARK_G, ha="right", va="bottom")
d.plot(E, G, color=INK, lw=1.0, zorder=3)
im = int(np.argmax(G))
d.plot(E[im], G[im], "o", ms=3.4, mfc=FE, mec=INK, mew=0.5, zorder=5)
d.annotate("peak %.2f×" % G[im], (E[im], G[im]), xytext=(-1.57, 0.35), fontsize=5.6,
           ha="left", va="center", arrowprops=dict(arrowstyle="-", lw=0.45, color=MID, shrinkA=0.5, shrinkB=1.5))
d.plot(EN_RU, 1.0, "o", ms=3.4, mfc=RU, mec=INK, mew=0.5, zorder=5)
d.annotate("Ru", (EN_RU, 1.0), xytext=(1, -6), textcoords="offset points", fontsize=5.8, fontweight="bold",
           va="top", ha="center")
d.set_yscale("log")
d.set_xlim(-1.6, -0.7)
d.set_ylim(1e-2, 5e3)
d.xaxis.set_major_locator(FixedLocator([-1.6, -1.4, -1.2, -1.0, -0.8]))
d.set_xticklabels([fmt_minus("%.1f" % v) for v in (-1.6, -1.4, -1.2, -1.0, -0.8)])
d.xaxis.set_minor_locator(MultipleLocator(0.05))
d.yaxis.set_major_locator(LogLocator(base=10, numticks=8))
d.yaxis.set_minor_locator(LogLocator(base=10, subs=np.arange(2, 10), numticks=12))
d.yaxis.set_minor_formatter(NullFormatter())
d.set_xlabel(r"Ru design descriptor $E_\mathrm{N}$ (eV)")
d.set_ylabel("Activity gain over current Ru (×)")

# ---- e: the best Ru cost the scaling line allows ---------------------------------------------------
pg.letter("e", 128.0, 57.0)
e = pg.ax(140.0, RY0, 41.0, 38.5)
boxed(e)
cE = np.array([float(r["E_N_eV"]) for r in scal if r["Ru_min_feasible_cost"]])
cC = np.array([float(r["Ru_min_feasible_cost"]) for r in scal if r["Ru_min_feasible_cost"]])
e.axhline(FE_COST, color=FE, lw=0.9, ls=(0, (3, 1.6)), zorder=2)
e.text(-0.62, FE_COST + 0.4, "Fe %.2f" % FE_COST, fontsize=5.8, color=DARK_G, ha="right", va="bottom",
       fontweight="bold")
e.fill_between([-1.7, -0.5], FE_COST, BEST_C, color="#F8DADA", lw=0, zorder=0)
e.plot(cE, cC, color=RU, lw=1.1, zorder=3)
e.plot(BEST_E, BEST_C, "o", ms=3.6, mfc=RU, mec=INK, mew=0.5, zorder=5)
e.annotate("best %.2f\nat %s eV" % (BEST_C, fmt_minus("%.3f" % BEST_E)), (BEST_E, BEST_C), xytext=(-1.52, 26.2),
           fontsize=5.6, va="center", linespacing=1.1,
           arrowprops=dict(arrowstyle="-", lw=0.45, color=MID, shrinkA=0.5, shrinkB=1.5))
e.text(-0.99, 0.5 * (FE_COST + BEST_C), "%.2f\nunclosed" % (BEST_C - FE_COST), fontsize=5.8, color=RED,
       fontweight="bold", ha="left", va="center", linespacing=1.1)
e.set_xlim(-1.6, -0.6)
e.set_ylim(12.0, 32.0)
e.xaxis.set_major_locator(FixedLocator([-1.5, -1.25, -1.0, -0.75]))
e.set_xticklabels([fmt_minus(v) for v in ("-1.5", "-1.25", "-1.0", "-0.75")])
e.xaxis.set_minor_locator(MultipleLocator(0.05))
e.yaxis.set_major_locator(FixedLocator([15, 20, 25, 30]))
e.yaxis.set_minor_locator(MultipleLocator(1))
e.set_xlabel(r"Ru $E_\mathrm{N}$ on the scaling line (eV)")
e.set_ylabel(r"Lowest Ru cost (USD t$^{-1}$)")

pg.save(HERE, "Fig3")
