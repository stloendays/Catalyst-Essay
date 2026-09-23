"""Figure 6 — decision-aware agents make the multiscale decision framework repeatedly executable.

Composite, 183 mm wide.
  fig6_trajectories.csv                              fig6_data.py (committed traces + oracle JSON)
  data/agent_figure_panel_data_2026-09-13.csv        recovery, narrow-window use, stable and final spend
  analysis/supervisor_2026_09_20/agent_*.csv         window sizes, 22-CU oracle normalization
  data/discover_boundary_c1_error_taxonomy_summary.csv   action errors by layer
  provenance/discover_v1/source_harness/DISCOVER_COST_MODEL_V1.json   CU prices in panel a

    pur_bridge_env/python make_fig6.py            -> Fig6.{svg,pdf,png}
"""
import csv
import json
import os
import sys

import numpy as np
from matplotlib.patches import FancyBboxPatch, Rectangle
from matplotlib.ticker import FixedLocator, LogLocator, MultipleLocator, NullFormatter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from style import (DARK_B, DARK_G, FE, INK, LINE, MID, OS, PALE_B, PALE_G, PAPER, RED, RU, TINT_B,  # noqa: E402
                   TINT_G, Page, boxed)

REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))


def read_csv(path):
    return list(csv.DictReader(open(path, encoding="utf-8")))


traj = read_csv(os.path.join(HERE, "fig6_trajectories.csv"))
panel = read_csv(os.path.join(REPO, "data/agent_figure_panel_data_2026-09-13.csv"))
win = {int(r["budget_CU"]): float(r["median_smallest_window_states"])
       for r in read_csv(os.path.join(REPO, "analysis/supervisor_2026_09_20/agent_window_summary.csv"))}
orc = {r["metric"]: float(r["value"]) for r in read_csv(os.path.join(REPO, "analysis/supervisor_2026_09_20/agent_oracle_summary.csv"))}
tax = read_csv(os.path.join(REPO, "data/discover_boundary_c1_error_taxonomy_summary.csv"))
cm = json.load(open(os.path.join(REPO, "provenance/discover_v1/source_harness/DISCOVER_COST_MODEL_V1.json"),
                    encoding="utf-8"))["actions"]
assert orc["protocol_oracle_CU"] == 22.0 and orc["D_threshold_CU"] == 206.0
assert abs(cm["BUILD_PROCESS_WINDOW"]["per_unit_CU"]["states"] - 0.00782) < 1e-12
assert cm["OPTIMIZE_PROCESS"]["per_unit_CU"]["states"] == 0.002

STRONG, MINI, NANO = "#56679A", "#89AA7B", "#B3B8C0"
ACT = {"BUILD_PROCESS_WINDOW": ("window build", "#7789B7"), "COMPUTE_ACTIVITY": ("activity screen", "#C6CCDC"),
       "OPTIMIZE_PROCESS": ("optimization", "#ACBF9F"), "RUN_MC": ("Monte Carlo, levers", "#D6D6D6"),
       "TEST_LEVER": ("Monte Carlo, levers", "#D6D6D6"), "BACKWARD": ("backward design", RED),
       "TEST_REACHABILITY": ("reachability", "#5E7A52")}
pg = Page(183.0, 168.0)

# ---- a: the agent and its environment ----------------------------------------------------------------
pg.letter("a", 2.0, 166.0)
a = pg.canvas(4.0, 112.0, 100.0, 52.0)
a.text(1.5, 50.0, "Decision-aware agent on a frozen environment", fontsize=7, fontweight="bold", va="top")


def box(x, y, w, h, fc="white", ec=INK, lw=0.7, r=1.4):
    a.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=%.1f" % r, fc=fc, ec=ec, lw=lw,
                               zorder=2))


arrow = dict(arrowstyle="-|>", lw=0.8, color=INK, mutation_scale=6, shrinkA=0, shrinkB=0)
# policy
box(1.0, 10.0, 20.0, 32.0, fc=TINT_B)
a.text(11.0, 40.2, "Language-model\npolicy", ha="center", va="top", fontsize=6.3, fontweight="bold", linespacing=1.05)
for i, (t, c) in enumerate((("strong", STRONG), ("mini", MINI), ("nano", NANO))):
    a.add_patch(FancyBboxPatch((3.5, 29.0 - i * 3.6), 15.0, 2.8, boxstyle="round,pad=0,rounding_size=1.0",
                               fc=c, ec="none", zorder=3))
    a.text(11.0, 30.4 - i * 3.6, t, ha="center", va="center", fontsize=5.8, color="white" if i < 2 else INK,
           fontweight="bold", zorder=4)
a.text(11.0, 20.0, "chooses actions,\nnever computes\nphysics", ha="center", va="top", fontsize=5.4, color=MID,
       linespacing=1.1)
# interface
a.annotate("", xy=(25.8, 31.0), xytext=(21.2, 31.0), arrowprops=arrow)
box(26.0, 8.0, 35.0, 36.0)
a.text(43.5, 42.0, "Typed actions, priced in CU", ha="center", va="top", fontsize=6.3, fontweight="bold")
items = [(ACT["BUILD_PROCESS_WINDOW"][0], "%.4f/state" % cm["BUILD_PROCESS_WINDOW"]["per_unit_CU"]["states"],
          ACT["BUILD_PROCESS_WINDOW"][1]),
         (ACT["COMPUTE_ACTIVITY"][0], "1/candidate", ACT["COMPUTE_ACTIVITY"][1]),
         (ACT["OPTIMIZE_PROCESS"][0], "%.3f/state" % cm["OPTIMIZE_PROCESS"]["per_unit_CU"]["states"],
          ACT["OPTIMIZE_PROCESS"][1]),
         ("MC, lever tests", "%.2f/draw/metal" % cm["RUN_MC"]["per_unit_CU"]["draws_x_metals"], ACT["RUN_MC"][1]),
         (ACT["BACKWARD"][0], "1", ACT["BACKWARD"][1]),
         (ACT["TEST_REACHABILITY"][0], "2–4", ACT["TEST_REACHABILITY"][1]),
         ("inspect, read", "0", "white")]
for i, (name, price, col) in enumerate(items):
    y = 37.2 - i * 4.1
    a.add_patch(Rectangle((27.8, y - 1.1), 2.2, 2.2, fc=col, ec=INK, lw=0.4, zorder=3))
    a.text(30.9, y, name, va="center", fontsize=5.5)
    a.text(59.6, y, price, va="center", ha="right", fontsize=5.2, color=MID)
a.text(43.5, 9.3, "full domain: 14,136 states", ha="center", va="bottom", fontsize=5.4, color=MID)
# tools
a.annotate("", xy=(65.8, 31.0), xytext=(61.2, 31.0), arrowprops=arrow)
box(66.0, 17.0, 33.0, 27.0, fc=PAPER)
a.text(82.5, 42.0, "Deterministic tools", ha="center", va="top", fontsize=6.3, fontweight="bold")
a.text(82.5, 38.4, "frozen NH$_3$-FINAL-1.1", ha="center", va="top", fontsize=5.4, color=MID)
tools = [("S1", "atomic activity"), ("S2", "process and cost"), ("S3", "backward, reachability")]
for i, (s_, t) in enumerate(tools):
    y = 31.5 - i * 5.0
    a.add_patch(FancyBboxPatch((67.8, y - 1.7), 5.2, 3.4, boxstyle="round,pad=0,rounding_size=0.8", fc="white",
                               ec=INK, lw=0.5, zorder=3))
    a.text(70.4, y, s_, ha="center", va="center", fontsize=5.8, fontweight="bold", zorder=4)
    a.text(74.2, y, t, va="center", fontsize=5.6)
# ledger and scorer
a.annotate("", xy=(82.5, 12.6), xytext=(82.5, 17.0), arrowprops=arrow)
box(66.0, 2.0, 33.0, 10.4, fc=TINT_G)
a.text(82.5, 9.6, "Ledger and scorer", ha="center", va="center", fontsize=6.2, fontweight="bold")
a.text(82.5, 5.2, "winner + decision pair\n+ reachability = complete", ha="center", va="center", fontsize=5.4,
       linespacing=1.1)
a.annotate("", xy=(11.0, 10.0), xytext=(65.8, 5.0),
           arrowprops=dict(arrowstyle="-|>", lw=0.7, color=MID, mutation_scale=5, shrinkA=0, shrinkB=0,
                           connectionstyle="angle,angleA=180,angleB=90,rad=0", linestyle=(0, (2.5, 1.5))))
a.text(40.0, 4.4, "results and remaining CU return to the policy", fontsize=5.4, color=MID, ha="center", va="top")

# ---- b: where the compute goes ---------------------------------------------------------------------------
pg.letter("b", 106.0, 166.0)
pg.title("Three chains to the same complete decision", 110.5, 166.4)
b = pg.ax(131.0, 127.0, 44.0, 29.0)
chains = [("oracle_protocol_complete", "Protocol oracle", None),
          ("agent_strong_B150", "Strong agent,\n150-CU allowance", 102.0),
          ("fixed_policy_D_B225", "Fixed policy D", 206.0)]
for i, (key, lab_, done) in enumerate(chains):
    y = 2 - i
    rows = [r for r in traj if r["chain"] == key]
    x0 = 0.0
    for r in rows:
        c_ = float(r["cost_CU"])
        if c_ <= 0 or r["action"] not in ACT:
            continue
        b.barh(y, c_, left=x0, height=0.56, color=ACT[r["action"]][1], ec="white", lw=0.35, zorder=3)
        if r["action"] == "BUILD_PROCESS_WINDOW" and r["window_states"]:
            n = format(int(float(r["window_states"])), ",")
            if c_ > 40:
                b.text(x0 + c_ / 2, y, n + " states", ha="center", va="center", fontsize=5.4, color="white",
                       fontweight="bold", zorder=4)
            else:
                b.text(x0 + c_ / 2, y + 0.34, n, ha="center", va="bottom", fontsize=5.2, zorder=4)
        x0 += c_
    b.text(x0 + 2.5, y, "%d CU" % x0, va="center", fontsize=5.8, fontweight="bold")
    if done and done < x0:
        b.plot([done, done], [y - 0.36, y + 0.36], color=INK, lw=0.9, zorder=5)
        b.text(done, y + 0.38, "decision %d" % done, ha="center", va="bottom", fontsize=5.2)
    b.text(-3.0, y, lab_, ha="right", va="center", fontsize=5.8, linespacing=1.0)
b.plot([65, 65], [0.66, 1.34], color=INK, lw=0.6, ls=(0, (1.5, 1)), zorder=5)
b.text(65, 0.62, "Fe found at 65", ha="center", va="top", fontsize=5.2)
b.set_xlim(0, 232)
b.set_ylim(-0.5, 2.75)
b.set_yticks([])
for s_ in ("left", "right", "top"):
    b.spines[s_].set_visible(False)
b.xaxis.set_major_locator(FixedLocator([0, 50, 100, 150, 200]))
b.xaxis.set_minor_locator(MultipleLocator(10))
b.set_xlabel("Compute spent (CU)")
b.text(232, 2.72, "numbers: window size, states", fontsize=5.2, color=MID, va="top", ha="right")
seen = []
for act_, (name, col) in ACT.items():
    if name not in seen:
        seen.append(name)
for i, name in enumerate(seen):
    col = next(c for n, c in ACT.values() if n == name)
    xx = 112.0 + (i % 3) * 23.0
    yy = 115.6 - (i // 3) * 3.4
    pg.fig.patches.append(Rectangle((xx / pg.W, (yy - 0.9) / pg.H), 2.0 / pg.W, 1.8 / pg.H, fc=col, ec=INK, lw=0.3,
                                    transform=pg.fig.transFigure, figure=pg.fig))
    pg.fig.text((xx + 2.8) / pg.W, yy / pg.H, name, fontsize=5.4, va="center")

# ---- shared data for c-e ------------------------------------------------------------------------------------
strong = sorted([r for r in panel if r["tier"] == "strong" and r["arm"] == "E"], key=lambda r: float(r["budget_CU"]))
cont = [r for r in strong if r["is_non_binding_allowance"] == "0"]
nb = next(r for r in strong if r["is_non_binding_allowance"] == "1")
B = np.array([float(r["budget_CU"]) for r in cont])
RY, RH = 64.0, 34.0


def budget_axis(ax):
    ax.set_xscale("log")
    ax.set_xlim(40, 460)
    ax.xaxis.set_major_locator(FixedLocator([50, 75, 100, 150, 200, 300, 400]))
    ax.xaxis.set_minor_locator(FixedLocator([]))
    ax.set_xticklabels(["50", "75", "100", "150", "200", "300", "400"])
    ax.set_xlabel("Compute allowance (CU)")


def nb_axis(x, y, h, ylim, log=False):
    ax = pg.ax(x, y, 6.0, h)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.spines["left"].set_linestyle((0, (2, 1.5)))
    ax.set_xlim(0, 1)
    if log:
        ax.set_yscale("log")
    ax.set_ylim(*ylim)
    ax.set_yticks([])
    ax.yaxis.set_minor_locator(FixedLocator([]))
    ax.set_xticks([0.5])
    ax.set_xticklabels(["5,000"], fontsize=5.8)
    ax.tick_params(axis="x", length=0)
    return ax


# ---- c: complete-decision recovery --------------------------------------------------------------------------
pg.letter("c", 2.0, RY + RH + 7.0)
c = pg.ax(13.0, RY, 44.0, RH)
boxed(c)
for tier, col, mk in (("strong", STRONG, "o"), ("mini", MINI, "s"), ("nano", NANO, "^")):
    rr = sorted([r for r in panel if r["tier"] == tier and r["arm"] == "E" and r["is_non_binding_allowance"] == "0"],
                key=lambda r: float(r["budget_CU"]))
    bb = np.array([float(r["budget_CU"]) for r in rr])
    p = np.array([float(r["p_complete_decision"]) for r in rr])
    lo = np.array([float(r["ci_lo"]) for r in rr])
    hi = np.array([float(r["ci_hi"]) for r in rr])
    if tier == "strong":
        c.fill_between(bb, lo, hi, color=TINT_B, lw=0, zorder=1)
    c.plot(bb, p, color=col, lw=1.0, zorder=3)
    c.plot(bb, p, mk, ms=3.2, mfc=col, mec=INK, mew=0.4, zorder=4)
c.axvline(206, color=MID, lw=0.6, ls=(0, (3, 1.6)))
c.axvline(75, color=STRONG, lw=0.6, ls=(0, (1.2, 1.2)))
c.text(210, 0.47, "D 206", fontsize=5.4, color=MID, va="center")
c.text(77, 0.47, "75", fontsize=5.4, color=STRONG, va="center")
c.text(44, 1.06, "strong", fontsize=5.6, color=STRONG, fontweight="bold", va="center")
c.text(300, 0.13, "mini", fontsize=5.6, color="#5E7A52", fontweight="bold", va="center")
c.text(160, 0.0, "nano", fontsize=5.6, color=MID, fontweight="bold", va="center", ha="right")
budget_axis(c)
c.set_ylim(-0.12, 1.15)
c.yaxis.set_major_locator(FixedLocator([0, 0.5, 1.0]))
c.yaxis.set_minor_locator(MultipleLocator(0.1))
c.set_ylabel("P(complete decision)")
c.text(445, 0.74, "5,000 CU,\nnon-binding:\n%d/%d" % (int(nb["k_complete_decision"]), int(nb["n"])), fontsize=5.4,
       ha="right", va="top", color=INK, linespacing=1.1)

# ---- d: scoped search under binding budgets --------------------------------------------------------------------
pg.letter("d", 66.0, RY + RH + 7.0)
d = pg.ax(78.0, RY, 36.0, RH)
boxed(d)
frac = np.array([float(r["narrow_window_fraction"]) for r in cont])
d.plot(B, frac, color=STRONG, lw=1.0, zorder=3)
d.plot(B, frac, "o", ms=3.2, mfc=STRONG, mec=INK, mew=0.4, zorder=4)
d.axvline(206, color=MID, lw=0.6, ls=(0, (3, 1.6)))
budget_axis(d)
d.set_ylim(-0.08, 1.12)
d.yaxis.set_major_locator(FixedLocator([0, 0.5, 1.0]))
d.set_ylabel("Runs using a narrow window")
d2 = d.twinx()
ws = np.array([win[int(b_)] for b_ in B])
d2.plot(B, ws, "D", ms=2.8, mfc="white", mec=MID, mew=0.6, zorder=4)
d2.set_yscale("log")
d2.set_ylim(300, 40000)
d2.axhline(14136, color=MID, lw=0.5, ls=(0, (1.5, 1.2)))
d2.text(44, 16500, "full domain 14,136", fontsize=5.2, color=MID, va="bottom")
d2.yaxis.set_major_locator(FixedLocator([1000, 10000]))
d2.set_yticklabels(["10$^3$", "10$^4$"])
d2.yaxis.set_minor_formatter(NullFormatter())
d2.set_ylabel("Smallest window (states)", color=MID)
d2.tick_params(axis="y", colors=MID, which="both", direction="in")
d2.spines["right"].set_color(MID)
d.text(445, 0.62, "5,000 CU,\nnon-binding:\n%d/%d" % (int(nb["narrow_window_canonical"]), int(nb["n"])), fontsize=5.4,
       ha="right", va="top", color=INK, linespacing=1.1)

# ---- e: decision-stable and final spend -------------------------------------------------------------------------
pg.letter("e", 128.0, RY + RH + 7.0)
e = pg.ax(139.0, RY, 34.0, RH)
boxed(e)
st = np.array([float(r["decision_stable_CU_median"]) for r in cont])
fn = np.array([float(r["final_used_CU_median"]) for r in cont])
for x_, a_, b_ in zip(B, st, fn):
    e.plot([x_, x_], [a_, b_], color=PALE_B, lw=1.6, zorder=1)
e.plot(B, fn, color=INK, lw=0.9, zorder=2)
e.plot(B, fn, "v", ms=3.0, mfc=INK, mec=INK, zorder=3)
e.plot(B, st, color=STRONG, lw=0.9, zorder=2)
e.plot(B, st, "o", ms=3.0, mfc=STRONG, mec=INK, mew=0.4, zorder=3)
e.axhline(22, color=DARK_G, lw=0.8, zorder=1)
e.text(44, 24.5, "oracle 22", fontsize=5.4, color=DARK_G, va="bottom")
e.axhline(206, color=MID, lw=0.6, ls=(0, (3, 1.6)))
e.text(44, 218, "D 206", fontsize=5.4, color=MID, va="bottom")
budget_axis(e)
e.set_xlim(40, 300)
e.xaxis.set_major_locator(FixedLocator([50, 100, 200]))
e.set_xticklabels(["50", "100", "200"])
e.set_yscale("log")
e.set_ylim(15, 1200)
e.yaxis.set_major_locator(FixedLocator([20, 50, 100, 200, 500, 1000]))
e.set_yticklabels(["20", "50", "100", "200", "500", "1000"])
e.yaxis.set_minor_formatter(NullFormatter())
e.set_ylabel("CU spent (median)")
e.text(118, 62, "decision stable", fontsize=5.3, color=STRONG, va="top", ha="left")
e.text(80, 150, "final", fontsize=5.3, color=INK, va="center")
en = nb_axis(174.0, RY, RH, (15, 1200), log=True)
en.plot([0.5, 0.5], [float(nb["decision_stable_CU_median"]), float(nb["final_used_CU_median"])], color=PALE_B, lw=1.6)
en.plot(0.5, float(nb["final_used_CU_median"]), "v", ms=3.0, mfc=INK, mec=INK)
en.plot(0.5, float(nb["decision_stable_CU_median"]), "o", ms=3.0, mfc=STRONG, mec=INK, mew=0.4)
en.axhline(22, color=DARK_G, lw=0.8)
en.text(0.5, 780, "714", fontsize=5.2, ha="center", va="bottom")
en.text(0.5, 400, "566", fontsize=5.2, ha="center", va="top", color=STRONG)

# ---- f: spend in units of the protocol oracle ----------------------------------------------------------------
LY, LH = 12.0, 32.0
pg.letter("f", 2.0, LY + LH + 7.0)
f = pg.ax(40.0, LY, 44.0, LH)
boxed(f)
bars = [("75-CU cell, decision stable", orc["strong_75_stable_over_oracle"], STRONG),
        ("75-CU allowance", orc["strong_allowance_75_over_oracle"], "#9DACCB"),
        ("fixed policy D", orc["D_over_oracle"], NANO),
        ("non-binding, decision stable", orc["nonbinding_stable_over_oracle"], RED)]
for i, (name, v, col) in enumerate(bars):
    f.barh(i, v - 1.0, left=1.0, height=0.58, color=col, ec=INK, lw=0.45, zorder=3)
    f.text(v * 1.12, i, "%.2f×" % v, va="center", fontsize=5.8, fontweight="bold" if i in (0, 3) else "normal")
f.set_xscale("log")
f.set_xlim(1.0, 80)
f.set_ylim(3.6, -0.6)
f.set_yticks(range(4))
f.set_yticklabels([x[0] for x in bars], fontsize=5.8)
f.tick_params(axis="y", length=0)
f.xaxis.set_major_locator(FixedLocator([1, 3, 10, 30]))
f.set_xticklabels(["1", "3", "10", "30"])
f.xaxis.set_minor_locator(LogLocator(base=10, subs=np.arange(2, 10), numticks=10))
f.xaxis.set_minor_formatter(NullFormatter())
f.set_xlabel("Spend ÷ 22-CU protocol oracle")

# ---- g: where the tiers fail --------------------------------------------------------------------------------------
pg.letter("g", 96.0, LY + LH + 7.0)
g = pg.ax(125.0, LY, 50.0, LH)
boxed(g)
cells = [("strong, 175 CU", "strong", "E", "175"), ("mini, 175 CU", "mini", "E", "175"),
         ("mini, typed interface", "mini", "E2", "175"), ("nano, 175 CU", "nano", "E", "175")]
layers = [("interface", "interface", "#9DACCB"), ("budget", "budget", "#D6D6D6"),
          ("sequencing", "sequencing", RED), ("no tool call", "no_tool_call_turns", "#F0EEEF")]
for i, (lab_, tier, arm, bud) in enumerate(cells):
    r = next(x for x in tax if x["tier"] == tier and x["arm"] == arm and x["budget_CU"] == bud)
    x0 = 0.0
    for name, col_key, col in layers:
        v = float(r[col_key])
        if v > 0:
            g.barh(i, v, left=x0, height=0.58, color=col, ec=INK, lw=0.4, zorder=3)
            if v >= 9:
                g.text(x0 + v / 2, i, "%d" % v, ha="center", va="center", fontsize=5.2,
                       color="white" if col == RED else INK, zorder=4)
        x0 += v
    g.text(x0 + 2.0, i, "%d" % x0, va="center", fontsize=5.6, fontweight="bold")
g.set_yticks(range(len(cells)))
g.set_yticklabels([c_[0] for c_ in cells], fontsize=5.8)
g.tick_params(axis="y", length=0)
g.set_ylim(len(cells) - 0.4, -0.6)
g.set_xlim(0, 150)
g.xaxis.set_major_locator(FixedLocator([0, 50, 100, 150]))
g.xaxis.set_minor_locator(MultipleLocator(10))
g.set_xlabel("Errors and empty turns, 20 runs")
for i, (name, _, col) in enumerate(layers):
    xx = 125.0 + i * 13.0
    pg.fig.patches.append(Rectangle((xx / pg.W, (LY + LH + 2.2) / pg.H), 2.0 / pg.W, 1.8 / pg.H, fc=col, ec=INK,
                                    lw=0.3, transform=pg.fig.transFigure, figure=pg.fig))
    pg.fig.text((xx + 2.8) / pg.W, (LY + LH + 3.1) / pg.H, name, fontsize=5.4, va="center")

pg.save(HERE, "Fig6")
