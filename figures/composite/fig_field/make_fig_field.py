"""Figure 2 — published laboratory leaderboards against plant-cost leaderboards, methanol and ammonia.

Composite, 183 mm wide.
  a  ACSA workflow (schematic, as Fig. 6a of the earlier numbering)
  b  methanol, leader changes by leaderboard metric: analysis/meoh_literature_inversion_2026_10_05/summary.json,
     paper-cluster bootstrap CI on STY: analysis/meoh_main_result_stats_2026_10_06/summary.json
  c  ammonia, leader changes by rate basis and plant treatment, and what the winners differ by:
     analysis/nh3_field_2026_10_06/summary.json, group_metrics.csv, candidates.csv
  d  methanol group, Re/TiO2 at 100 bar: analysis/meoh_literature_inversion_2026_10_05/literature_candidates.csv
  e  methanol group, Cu/Al2O3 (K, Ba) at 10 MPa: same file
  f  ammonia group, BaTiO3-xHx supports at 5 MPa: analysis/nh3_field_2026_10_06/candidates.csv

    pur_bridge_env/python make_fig_field.py            -> FigField.{svg,pdf,png}
"""
import csv
import json
import os
import sys
from collections import Counter

import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from matplotlib.ticker import FuncFormatter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from style import DARK_G, FE, INK, MID, OTHER, PALE_B, RED, RU, TINT_B, TINT_G, Page, boxed  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))


def read_csv(rel):
    return list(csv.DictReader(open(os.path.join(REPO, rel), encoding="utf-8")))


def read_json(rel):
    return json.load(open(os.path.join(REPO, rel), encoding="utf-8"))


lit = read_json("analysis/meoh_literature_inversion_2026_10_05/summary.json")
stats = read_json("analysis/meoh_main_result_stats_2026_10_06/summary.json")
cand = read_csv("analysis/meoh_literature_inversion_2026_10_05/literature_candidates.csv")
nh3 = read_json("analysis/nh3_field_2026_10_06/summary.json")
nh3_groups = read_csv("analysis/nh3_field_2026_10_06/group_metrics.csv")
nh3_cand = read_csv("analysis/nh3_field_2026_10_06/candidates.csv")
assert lit["selfcheck"]["max_abs_diff_eur_t"] < 1e-12
assert stats["point_estimate"]["groups"] == lit["primary"]["top1_mismatch_groups"]
assert stats["groups"] == lit["primary"]["groups"]
assert nh3["selfcheck_supported_chain"]["pass_"]

MEOH_GROUPS = [("10.1021/acscatal.5c05984 | 100 bar | H2/CO2 4 | 10 NL/g/h", "Re/TiO$_2$, 100 bar"),
               ("10.1039/c2cy20604h | 100 bar | H2/CO2 3.8 | 10.6 NL/g/h", "Cu/Al$_2$O$_3$ (K, Ba), 10 MPa")]
NH3_GROUP = ("10.1002/aenm.201801772 | 400 C | 5 MPa | H2/N2 3 | 6.6e+04 mL/g/h",
             "Ru, Fe, Co on BaTiO$_{3-x}$H$_x$, 5 MPa")


def pct(x):
    return "%.1f" % (100 * x) if x < 0.01 else "%.0f" % (100 * x)


def nh3_kind_counts():
    """Mismatched groups by mechanism; for 'different metal', how many the same-support Fe catalyst wins."""
    metal = {(r["group"], r["catalyst"]): r["metal"] for r in nh3_cand if r["group"]}
    kinds = nh3["primary"]["mismatch_kinds"]
    assert sum(v["groups"] for v in kinds.values()) == nh3["primary"]["top1_mismatch_groups"]
    dm = [g for g in nh3_groups if g["mismatch_kind"] == "different metal"]
    fe_wins = sum(metal[(g["group"], g["plant_winner"])] == "Fe" for g in dm)
    assert len(dm) == kinds["different metal"]["groups"]
    return kinds, fe_wins


def nh3_example():
    rows = [r for r in nh3_cand if r["group"] == NH3_GROUP[0]]
    g = next(r for r in nh3_groups if r["group"] == NH3_GROUP[0])
    assert len(rows) == int(g["n"])
    return rows, g


if __name__ == "__main__":
    pg = Page(183.0, 150.0)

    # ---- a: workflow ------------------------------------------------------------------------------------------
    a = pg.canvas(4, 124, 176, 22)
    boxes = [
        (16, "Publications + SI", "databases", "white"),
        (51, "Extract", "value · unit · table/figure · page", TINT_B),
        (88, "Self-check", "reproduce the frozen cases", TINT_G),
        (127, "Full chain", "kinetics → process opt. → cost\nbound first, full optimization if needed", TINT_B),
        (162, "Leaderboards", "laboratory vs plant cost", "white"),
    ]
    for x, t, sub, fc in boxes:
        w = {"Full chain": 36, "Leaderboards": 26}.get(t, 30)
        a.add_patch(FancyBboxPatch((x - w / 2, 5), w, 15, boxstyle="round,pad=0,rounding_size=1.4", fc=fc, ec=INK,
                                   lw=0.55))
        a.text(x, 15.8, t, ha="center", va="center", fontsize=6.4, fontweight="bold")
        a.text(x, 10.0, sub, ha="center", va="center", fontsize=5.2, color=INK, linespacing=1.15)
    for x0, x1 in ((31.2, 35.8), (66.2, 72.8), (103.2, 108.8), (145.2, 148.8)):
        a.add_patch(FancyArrowPatch((x0, 12.5), (x1, 12.5), arrowstyle="-|>", mutation_scale=6, lw=0.6, color=INK))
    a.text(88, 1.8, "scientific models unchanged; the agent supplies scale", ha="center", va="center", fontsize=5.3,
           color=INK)
    pg.letter("a", 2, 148)

    # ---- b: methanol leaderboards -----------------------------------------------------------------------------
    b = pg.ax(14, 70, 40, 38)
    P0, V = lit["primary"], lit["variants"]
    cases = [("STY", P0), ("X·S", V["leaderboard_X_times_S"]), ("X", V["leaderboard_X"]),
             ("S$_{MeOH}$", V["leaderboard_S_MeOH"])]
    lo, hi = stats["cluster_bootstrap"]["fraction_ci95"]
    for i, (lab, x) in enumerate(cases):
        f = x["top1_mismatch_fraction"]
        col = RED if lab.startswith("S$") else (RU if lab == "STY" else PALE_B)
        b.bar(i, f, 0.62, color=col, ec=INK, lw=0.4, zorder=2)
        ytxt = (hi if i == 0 else f) + 0.035
        b.text(i, ytxt, "%d/%d" % (x["top1_mismatch_groups"], x["groups"]), ha="center", va="bottom", fontsize=5.0)
    b.errorbar([0], [P0["top1_mismatch_fraction"]], yerr=[[P0["top1_mismatch_fraction"] - lo],
                                                          [hi - P0["top1_mismatch_fraction"]]],
               fmt="none", ecolor=INK, elinewidth=0.6, capsize=1.8, capthick=0.6, zorder=3)
    b.scatter([0], [V["inert_opt"]["top1_mismatch_fraction"]], marker="_", s=60, c=INK, lw=0.9, zorder=4)
    b.text(0.97, 0.97, "bar on STY: 95 % CI\n(paper-cluster bootstrap);\ntick: recycled CO taken as inert",
           transform=b.transAxes, fontsize=5.0,
           ha="right", va="top", color=INK)
    b.set_xticks(range(len(cases)))
    b.set_xticklabels([l for l, _ in cases], fontsize=5.6)
    b.set_ylim(0, 1.0)
    b.set_xlim(-0.55, 3.55)
    b.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    b.set_yticklabels(["0", "25", "50", "75", "100"])
    b.set_ylabel("leader changes (% of comparisons)")
    b.set_xlabel("paper leaderboard")
    boxed(b)
    pg.letter("b", 2, 117)
    pg.title("Methanol: %d comparisons, %d papers" % (P0["groups"], P0["papers"]), 14, 117)

    # ---- c: ammonia leaderboards ------------------------------------------------------------------------------
    c1 = pg.ax(74, 70, 34, 38)
    pr, nv = nh3["primary"], nh3["variants"]
    ncases = [("rate per\ng cat.", pr, RU), ("rate per\ng metal", nv["per_g_metal_leaderboard"], PALE_B),
              ("per g cat.,\n90 % Ru rec.", nv["Ru_recovery_90pct"], PALE_B)]
    for i, (lab, x, col) in enumerate(ncases):
        f = x["top1_mismatch_fraction"]
        l, h = x["bootstrap_papers"]["mismatch_fraction_ci95"]
        c1.bar(i, f, 0.62, color=col, ec=INK, lw=0.4, zorder=2)
        c1.errorbar([i], [f], yerr=[[f - l], [h - f]], fmt="none", ecolor=INK, elinewidth=0.6, capsize=1.8,
                    capthick=0.6, zorder=3)
        c1.text(i, h + 0.035, "%d/%d" % (x["top1_mismatch_groups"], x["groups"]), ha="center", va="bottom",
                fontsize=5.0)
    c1.set_xticks(range(len(ncases)))
    c1.set_xticklabels([l for l, _, _ in ncases], fontsize=5.2)
    c1.set_xlim(-0.55, 2.55)
    c1.set_ylim(0, 1.0)
    c1.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    c1.set_yticklabels(["0", "25", "50", "75", "100"])
    c1.set_ylabel("leader changes (% of comparisons)")
    c1.text(0.04, 0.97, "bars: 95 % CI", transform=c1.transAxes, fontsize=5.0, va="top", color=INK)
    boxed(c1)

    kinds, fe_wins = nh3_kind_counts()
    c2 = pg.ax(124, 70, 56, 38)
    korder = [("fused-Fe reference vs supported catalyst", "commercial fused-Fe reference wins", FE),
              ("different metal", "different metal wins (Fe on the same\nsupport in %d of %%d)" % fe_wins, FE),
              ("same metal and metal content", "same metal and content,\nother support or promoter", PALE_B),
              ("same metal, different metal content", "same metal, other content", PALE_B)]
    nmax = max(kinds[k]["groups"] for k, _, _ in korder)
    for j, (k, lab, col) in enumerate(korder):
        v = kinds[k]
        y = len(korder) - 1 - j
        c2.barh(y, v["groups"], 0.42, color=col, ec=INK, lw=0.4)
        c2.text(0.35, y + 0.25, lab % v["groups"] if "%d" in lab else lab, fontsize=5.0, va="bottom", ha="left",
                linespacing=1.05)
        c2.text(v["groups"] + 0.4, y, "%d (%d paper%s); regret %s %%" % (
            v["groups"], v["papers"], "" if v["papers"] == 1 else "s", pct(v["regret_median"])),
            fontsize=5.0, va="center", ha="left")
    c2.set_ylim(-0.4, len(korder) - 0.05 + 0.55)
    c2.set_xlim(0, nmax * 1.75)
    c2.set_yticks([])
    c2.set_xlabel("mismatched comparisons (of %d)" % pr["top1_mismatch_groups"])
    boxed(c2)
    c2.text(0.99, 0.985, "regret: median cost penalty of\nbuilding the paper's leader", transform=c2.transAxes,
            fontsize=5.0, ha="right", va="top")
    pg.letter("c", 64, 117)
    pg.title("Ammonia: %d comparisons, %d papers" % (pr["groups"], pr["papers"]), 74, 117)

    # ---- d, e: methanol groups --------------------------------------------------------------------------------
    for k, (g, title) in enumerate(MEOH_GROUPS):
        rows = [r for r in cand if r["group"] == g]
        assert rows, g
        e = pg.ax(14 + k * 59, 11, 45, 40)
        sty = np.array([float(r["STY"]) for r in rows])
        cost = np.array([float(r["cost_recycled_opt"]) for r in rows])
        sch4 = np.array([float(r["SCH4"]) for r in rows])
        e.scatter(sty, cost, s=8 + 100 * sch4, c=PALE_B, ec=INK, lw=0.35, zorder=2)
        iu, ie = int(np.argmax(sty)), int(np.argmin(cost))
        e.scatter([sty[iu]], [cost[iu]], s=36, facecolor="none", ec=RED, lw=0.9, zorder=3)
        e.scatter([sty[ie]], [cost[ie]], s=36, facecolor="none", ec=DARK_G, lw=0.9, zorder=3)
        e.annotate("STY leader", (sty[iu], cost[iu]), xytext=(-2, 8), textcoords="offset points", fontsize=5.0,
                   color=RED, ha="right")
        left = sty[ie] < sty.min() + 0.25 * (sty.max() - sty.min())
        e.annotate("plant-cost\nleader", (sty[ie], cost[ie]), xytext=(6 if left else -4, 6),
                   textcoords="offset points", fontsize=5.0, color=DARK_G, ha="left" if left else "right")
        e.set_xlabel("STY (g$_{MeOH}$ g$_{cat}^{-1}$ h$^{-1}$)")
        e.set_ylabel("net cost (EUR t$^{-1}$)")
        # log axis: a few entries cost tens of times the leaders and would flatten them on a linear axis
        e.set_yscale("log")
        e.set_ylim(cost.min() / 1.25, cost.max() * 1.9)
        plain = FuncFormatter(lambda v, _: "{:,.0f}".format(v))
        e.yaxis.set_major_formatter(plain)
        e.yaxis.set_minor_formatter(FuncFormatter(lambda v, _: "{:,.0f}".format(v) if str(int(round(v)))[0] in "25" else ""))
        xr = sty.max() - sty.min()
        e.set_xlim(sty.min() - 0.08 * xr, sty.max() + 0.08 * xr)
        e.text(0.03, 0.96, title, transform=e.transAxes, fontsize=5.6, va="top", fontweight="bold")
        if k == 0:
            e.text(0.03, 0.86, "marker area: CH$_4$ selectivity", transform=e.transAxes, fontsize=5.0, va="top")
        boxed(e)
    pg.letter("d", 2, 57)
    pg.letter("e", 61, 57)

    # ---- f: ammonia group -------------------------------------------------------------------------------------
    rows, gm = nh3_example()
    fax = pg.ax(132, 11, 48, 40)
    mcol = {"Ru": RU, "Fe": FE, "Co": OTHER}
    rate = np.array([float(r["paper_rate"]) for r in rows]) / 1000.0
    cost = np.array([float(r["cost_USD_t"]) for r in rows])
    met = [r["metal"] for r in rows]
    for m in ("Ru", "Fe", "Co"):
        sel = [i for i, x in enumerate(met) if x == m]
        fax.scatter(rate[sel], cost[sel], s=14, c=mcol[m], ec=INK, lw=0.35, zorder=2, label=m)
    iu = int(np.argmax(rate))
    ie = int(np.argmin(cost))
    assert rows[iu]["catalyst"] == gm["paper_winner"] and abs(cost[ie] - float(gm["plant_winner_cost"])) < 1e-9
    fax.scatter([rate[iu]], [cost[iu]], s=40, facecolor="none", ec=RED, lw=0.9, zorder=3)
    fax.scatter([rate[ie]], [cost[ie]], s=40, facecolor="none", ec=DARK_G, lw=0.9, zorder=3)
    fax.annotate("rate leader\n%s, %s wt%%" % (rows[iu]["catalyst"].replace("BaTiO2.5H0.5", "BaTiO$_{2.5}$H$_{0.5}$"),
                                               rows[iu]["metal_wt_pct"].rstrip("0").rstrip(".")),
                 (rate[iu], cost[iu]), xytext=(-2, 7), textcoords="offset points", fontsize=5.0, color=RED,
                 ha="right")
    fax.annotate("plant-cost leader\nFe, 1 wt%% (regret %.0f %%)" % (100 * float(gm["regret"])), (rate[ie], cost[ie]),
                 xytext=(7, -1), textcoords="offset points", fontsize=5.0, color=DARK_G, ha="left", va="center")
    assert rows[ie]["metal"] == "Fe" and float(rows[ie]["metal_wt_pct"]) == 1.0
    fax.set_xlabel("rate (mmol g$_{cat}^{-1}$ h$^{-1}$)")
    fax.set_ylabel("plant cost (USD t$^{-1}$ NH$_3$)")
    fax.set_xlim(-2.5, 55)
    fax.set_ylim(14.5, 46)
    fax.legend(loc="upper right", fontsize=5.0, handletextpad=0.1, borderaxespad=0.3, labelspacing=0.3)
    fax.text(0.03, 0.96, NH3_GROUP[1], transform=fax.transAxes, fontsize=5.6, va="top", fontweight="bold")
    boxed(fax)
    pg.letter("f", 121, 57)

    pg.save(HERE, "FigField")
