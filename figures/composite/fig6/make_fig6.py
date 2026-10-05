"""Figure 6 — the agent scales the analysis to published and computed catalysts.

Composite, 183 mm wide.
  a  ACSA workflow (schematic)
  b  extraction accuracy by source: agent/extraction/eval/field_accuracy_by_source.csv
  c  bimetallic surfaces, transition-metal layer: analysis/nh3_alloy_extension_2026_10_05/alloy_chain_results.csv
  d  published methanol comparisons, leader changes by leaderboard: analysis/meoh_literature_inversion_2026_10_05/summary.json
  e  two comparison groups, STY against plant cost: analysis/meoh_literature_inversion_2026_10_05/literature_candidates.csv

    pur_bridge_env/python make_fig6.py            -> Fig6.{svg,pdf,png}
"""
import csv
import json
import os
import re
import sys

import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from matplotlib.ticker import NullFormatter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from style import DARK_G, FE, INK, MID, OTHER, PALE_B, PALE_G, RED, RU, TINT_B, TINT_G, Page, boxed  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
FE_COST = 15.291704676621144


def read_csv(rel):
    return list(csv.DictReader(open(os.path.join(REPO, rel), encoding="utf-8")))


acc = {(r["source_type"], r["field"]): r for r in read_csv("agent/extraction/eval/field_accuracy_by_source.csv")}
alloy = read_csv("analysis/nh3_alloy_extension_2026_10_05/alloy_chain_results.csv")
lit = json.load(open(os.path.join(REPO, "analysis/meoh_literature_inversion_2026_10_05/summary.json"), encoding="utf-8"))
cand = read_csv("analysis/meoh_literature_inversion_2026_10_05/literature_candidates.csv")
assert all(-7.6 < float(r["logTOF_673K"]) and float(r["cost_USD_t"]) < 15000 for r in alloy
           if r["domain"] == "transition_metal" and r["feasible"] == "True")
assert lit["selfcheck"]["max_abs_diff_eur_t"] < 1e-12

pg = Page(183.0, 128.0)

# ---- a: workflow ------------------------------------------------------------------------------------------
a = pg.canvas(4, 98, 176, 22)
boxes = [
    (16, "Publications + SI", "databases", "white"),
    (51, "Extract", "value · unit · table/figure · page", TINT_B),
    (88, "Self-check", "reproduce the frozen cases", TINT_G),
    (127, "Full chain", "kinetics → process opt. → cost\nbound first, full optimization if needed", TINT_B),
    (162, "Leaderboards", "upstream vs plant cost", "white"),
]
for x, t, sub, fc in boxes:
    w = {"Full chain": 36, "Leaderboards": 26}.get(t, 30)
    a.add_patch(FancyBboxPatch((x - w / 2, 5), w, 15, boxstyle="round,pad=0,rounding_size=1.4", fc=fc, ec=INK, lw=0.55))
    a.text(x, 15.8, t, ha="center", va="center", fontsize=6.4, fontweight="bold")
    a.text(x, 10.0, sub, ha="center", va="center", fontsize=5.2, color=MID, linespacing=1.15)
for x0, x1 in ((31.2, 35.8), (66.2, 72.8), (103.2, 108.8), (145.2, 148.8)):
    a.add_patch(FancyArrowPatch((x0, 12.5), (x1, 12.5), arrowstyle="-|>", mutation_scale=6, lw=0.6, color=INK))
a.text(88, 1.8, "scientific models unchanged; the agent supplies scale", ha="center", va="center", fontsize=5.3, color=MID)
pg.letter("a", 2, 123)

# ---- b: extraction accuracy -------------------------------------------------------------------------------
b = pg.ax(13, 50, 46, 36)
sources = [("table", "main-text\ntables"), ("SI", "SI\nprinted"), ("plot", "main-text\nplots"), ("SI-plot", "SI\nplots")]
fields = [("X_CO2", "X$_{CO_2}$", RU), ("S_MeOH", "S$_{MeOH}$", FE), ("STY", "STY", PALE_B)]
wbar = 0.26
for i, (s, _) in enumerate(sources):
    for k, (f, lab, col) in enumerate(fields):
        r = acc.get((s, f))
        if not r or not r["acc_strict"]:
            continue
        v = float(r["acc_strict"])
        n = int(r["n_extracted"])
        x = i + (k - 1) * wbar
        b.bar(x, v, wbar * 0.92, color=col, ec=INK, lw=0.35)
        b.text(x, v + 0.025, f"{round(v * n)}/{n}", ha="center", va="bottom", fontsize=4.1, rotation=90)
b.set_xticks(range(len(sources)))
b.set_xticklabels([l for _, l in sources], fontsize=5.4)
b.set_ylim(0, 1.32)
b.set_yticks([0, 0.5, 1.0])
b.set_ylabel("strict accuracy")
for k, (f, lab, col) in enumerate(fields):
    b.bar(0, 0, color=col, ec=INK, lw=0.35, label=lab)
b.legend(loc="upper right", fontsize=5.2, ncol=3, handlelength=0.9, columnspacing=0.8, borderaxespad=0.1)
boxed(b)
pg.letter("b", 2, 91)
pg.title("Extraction from 20 papers (recall 96%)", 13, 91)

# ---- c: bimetallic surfaces -------------------------------------------------------------------------------
c = pg.ax(74, 50, 52, 36)
CHEAP_3D, GROUP6 = {"Fe", "Co", "Ni", "Cu"}, {"Cr", "Mo", "W"}


def els(name):
    return set(re.findall(r"[A-Z][a-z]?", name))


tm = [r for r in alloy if r["domain"] == "transition_metal" and r["feasible"] == "True"]
fam = [r for r in tm if len(els(r["surface"])) == 2 and len(els(r["surface"]) & CHEAP_3D) == 1
       and len(els(r["surface"]) & GROUP6) == 1]
rest = [r for r in tm if r not in fam]
for grp, col, sz, z in ((rest, OTHER, 5, 2), (fam, FE, 9, 3)):
    c.scatter([float(r["logTOF_673K"]) for r in grp], [float(r["cost_USD_t"]) for r in grp], s=sz, c=col,
              ec=INK, lw=0.25, zorder=z)
c.axhline(FE_COST, color=DARK_G, lw=0.7, ls="--", zorder=1)
c.text(-7.5, FE_COST * 1.12, "Fe %.2f" % FE_COST, fontsize=5.2, color=DARK_G, va="bottom")
below = sorted([r for r in tm if float(r["cost_USD_t"]) < FE_COST], key=lambda r: float(r["cost_USD_t"]))
c.text(-5.6, 5.8, "%d below Fe, all cheap 3d + Cr/Mo/W" % len(below), fontsize=5.0, color=DARK_G, va="bottom")
top = max(tm, key=lambda r: float(r["logTOF_673K"]))
c.scatter([float(top["logTOF_673K"])], [float(top["cost_USD_t"])], s=16, facecolor="none", ec=RED, lw=0.8, zorder=4)
c.annotate("%s: most active,\neconomic rank 43" % top["surface"], (float(top["logTOF_673K"]), float(top["cost_USD_t"])),
           xytext=(-6, 60), textcoords="offset points", fontsize=5.0, color=RED, ha="right",
           arrowprops=dict(arrowstyle="-", color=RED, lw=0.5))
c.set_yscale("log")
c.set_ylim(5, 15000)
c.set_xlim(-7.6, -3.1)
c.yaxis.set_minor_formatter(NullFormatter())
c.set_yticks([15, 100, 1000, 10000])
c.set_yticklabels(["15", "100", "10$^3$", "10$^4$"])
c.set_xlabel("log$_{10}$ TOF at 673 K (s$^{-1}$)")
c.set_ylabel("cost (USD t$^{-1}$ NH$_3$)")
c.scatter([], [], s=9, c=FE, ec=INK, lw=0.25, label="cheap 3d + Cr/Mo/W")
c.scatter([], [], s=5, c=OTHER, ec=INK, lw=0.25, label="other")
c.legend(loc="upper center", fontsize=5.0, handletextpad=0.2, borderaxespad=0.2)
boxed(c)
pg.letter("c", 64, 91)
pg.title("%d transition-metal surfaces in the bed limit" % len(tm), 74, 91)

# ---- d: published methanol leaderboards --------------------------------------------------------------------
d = pg.ax(140, 50, 40, 36)
P0, V = lit["primary"], lit["variants"]
cases = [("STY", P0), ("X·S", V["leaderboard_X_times_S"]), ("X", V["leaderboard_X"]), ("S$_{MeOH}$", V["leaderboard_S_MeOH"])]
for i, (lab, x) in enumerate(cases):
    f = x["top1_mismatch_fraction"]
    col = RED if lab.startswith("S$") else (RU if lab == "STY" else PALE_B)
    d.bar(i, f, 0.62, color=col, ec=INK, lw=0.4)
    d.text(i, f + 0.02, "%d/%d" % (x["top1_mismatch_groups"], x["groups"]), ha="center", va="bottom", fontsize=5.0)
d.scatter([0], [V["inert_opt"]["top1_mismatch_fraction"]], marker="_", s=60, c=INK, lw=0.9, zorder=4)
d.text(0.38, V["inert_opt"]["top1_mismatch_fraction"], "inert CO", fontsize=4.8, va="center", color=MID)
d.set_xticks(range(len(cases)))
d.set_xticklabels([l for l, _ in cases], fontsize=5.6)
d.set_ylim(0, 1.0)
d.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
d.set_yticklabels(["0", "25", "50", "75", "100"])
d.set_ylabel("leader changes (% of comparisons)")
d.set_xlabel("paper leaderboard")
boxed(d)
pg.letter("d", 131, 91)
pg.title("%d comparisons, %d papers" % (P0["groups"], P0["papers"]), 140, 91)

# ---- e: two comparison groups -------------------------------------------------------------------------------
groups = [("10.1021/acscatal.5c05984 | 100 bar | H2/CO2 4 | 10 NL/g/h", "Re/TiO$_2$, 100 bar"),
          ("10.1039/c2cy20604h | 100 bar | H2/CO2 3.8 | 10.6 NL/g/h", "Cu/Al$_2$O$_3$ (K, Ba), 10 MPa")]
for k, (g, title) in enumerate(groups):
    rows = [r for r in cand if r["group"] == g]
    assert rows, g
    e = pg.ax(13 + k * 88, 9, 74, 30)
    sty = np.array([float(r["STY"]) for r in rows])
    cost = np.array([float(r["cost_recycled_opt"]) for r in rows])
    sch4 = np.array([float(r["SCH4"]) for r in rows])
    sc = e.scatter(sty, cost, s=10 + 120 * sch4, c=PALE_B, ec=INK, lw=0.35, zorder=2)
    iu, ie = int(np.argmax(sty)), int(np.argmin(cost))
    e.scatter([sty[iu]], [cost[iu]], s=40, facecolor="none", ec=RED, lw=0.9, zorder=3)
    e.scatter([sty[ie]], [cost[ie]], s=40, facecolor="none", ec=DARK_G, lw=0.9, zorder=3)
    e.annotate("STY leader", (sty[iu], cost[iu]), xytext=(-4, 9), textcoords="offset points", fontsize=5.0,
               color=RED, ha="right")
    left = sty[ie] < sty.min() + 0.25 * (sty.max() - sty.min())
    e.annotate("plant-cost leader", (sty[ie], cost[ie]), xytext=(6 if left else -4, 9), textcoords="offset points",
               fontsize=5.0, color=DARK_G, ha="left" if left else "right")
    e.set_xlabel("STY (g$_{MeOH}$ g$_{cat}^{-1}$ h$^{-1}$)")
    e.set_ylabel("net cost (EUR t$^{-1}$)")
    lo, hi = cost.min(), np.percentile(cost, 90)
    e.set_ylim(lo - 0.08 * (hi - lo), hi + 0.25 * (hi - lo))
    e.text(0.02, 0.95, title, transform=e.transAxes, fontsize=5.6, va="top", fontweight="bold")
    if k == 0:
        e.text(0.02, 0.83, "marker area scales with CH$_4$ selectivity", transform=e.transAxes, fontsize=5.0, va="top", color=MID)
    boxed(e)
pg.letter("e", 2, 44)

pg.save(HERE, "Fig6")
