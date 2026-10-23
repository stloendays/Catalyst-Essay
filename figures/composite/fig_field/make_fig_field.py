"""Figure 2 — laboratory leaderboards against plant-cost leaderboards, methanol and ammonia.

Composite, 183 mm wide.
  a  ACSA workflow (schematic, as Fig. 6a of the earlier numbering)
  b  methanol, leader changes by leaderboard metric in the inert-limited loop (primary; frozen column
     cost_recycled_opt_inlet: reactor-inlet CH4 + CO + N2 <= 6.86 %), and by STY without the limit (frozen column
     cost_recycled_opt), scored with the frozen code meoh_candidates.aggregate on
     analysis/meoh_literature_inversion_2026_10_05/literature_candidates.csv and checked against summary.json and
     analysis/meoh_s6_robustness_2026_10_13/results.json; paper-cluster bootstrap CIs on STY:
     analysis/meoh_s6_robustness_2026_10_13/stats_s6/summary.json and analysis/meoh_main_result_stats_2026_10_06/
     summary.json
  c  ammonia (NH3-FINAL-1.2), leader changes by rate basis and plant treatment, and what the winners differ by:
     analysis/nh3_field_2026_10_06/nh3_1_2/summary_printed.json, group_metrics_printed.csv, candidates.csv
  d  methanol group, Re/TiO2 at 100 bar: analysis/meoh_literature_inversion_2026_10_05/literature_candidates.csv
     (cost_recycled_opt_inlet filled, cost_recycled_opt open)
  e  methanol group, InNi3C0.5 on m-, t-, a-ZrO2 and SiO2 at 4 MPa (Meng et al. 2021, 24 NL/g/h): same file
  f  ammonia group, BaTiO3-xHx supports at 5 MPa: analysis/nh3_field_2026_10_06/nh3_1_2/candidates_printed.csv

    pur_bridge_env/python make_fig_field.py            -> FigField.{svg,pdf,png}
"""
import csv
import json
import os
import sys
from collections import Counter

import numpy as np
import pandas as pd
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Patch
from matplotlib import patheffects as pe
from matplotlib.ticker import FuncFormatter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from style import (AMB_D, AMB_L, AMB_P, DARK_B, DARK_G, FE, INK, MID, OS, OTHER, PALE_B, RED, RU, TINT_B,  # noqa: E402
                   TINT_G, Page, boxed, scripts_at_least)
import layout  # noqa: E402
import track  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
INV = "analysis/meoh_literature_inversion_2026_10_05/"
S6R = "analysis/meoh_s6_robustness_2026_10_13/"
sys.path.insert(0, os.path.join(REPO, "data", "meoh"))
sys.path.insert(0, os.path.join(REPO, INV))
from meoh_candidates import aggregate  # noqa: E402  (frozen scoring code)

S6, S5 = "cost_recycled_opt_inlet", "cost_recycled_opt"     # inert-limited loop (primary), loop without the limit


def read_csv(rel):
    return list(csv.DictReader(open(os.path.join(REPO, rel), encoding="utf-8")))


def read_json(rel):
    return json.load(open(os.path.join(REPO, rel), encoding="utf-8"))


lit = read_json(INV + "summary.json")
stats = read_json("analysis/meoh_main_result_stats_2026_10_06/summary.json")      # bootstrap, loop without limit
stats6 = read_json(S6R + "stats_s6/summary.json")                                  # bootstrap, inert-limited loop
s6res = read_json(S6R + "results.json")
cand = pd.read_csv(os.path.join(REPO, INV, "literature_candidates.csv"))
# panel b since 2026-10-15: both extractions (40 + 41 groups), analysis/meoh_field_pooled_2026_10_15
POOL = "analysis/meoh_field_pooled_2026_10_15/"
pool = read_json(POOL + "summary.json")
pcand = pd.read_csv(os.path.join(REPO, POOL, "pooled_candidates.csv"))
# ammonia since 2026-10-17: both extractions pooled (33 + 11 groups; the canonical pooled run of
# analysis/nh3_field_expansion_2026_10_12, report_numbers.py "pooled_vf"); model NH3-FINAL-1.2
NH3F = "analysis/nh3_field_expansion_2026_10_12/nh3_1_2/runs/pooled_vf_screen/"
nh3_run = read_json(NH3F + "summary.json")
nh3 = read_json(NH3F + "summary_printed.json")                                   # primary: printed values
nh3_groups = read_csv(NH3F + "group_metrics_printed.csv")
nh3_cand = read_csv(NH3F + "candidates.csv")
nh3_pcand = read_csv(NH3F + "candidates_printed.csv")
assert nh3_run["model"]["label"] == "NH3-FINAL-1.2" and nh3_run["model"]["process_states"] == 14510
assert lit["selfcheck"]["max_abs_diff_eur_t"] < 1e-12
assert stats["point_estimate"]["groups"] == lit["primary"]["top1_mismatch_groups"]
assert stats["groups"] == lit["primary"]["groups"]
assert stats6["point_estimate"]["groups"] == lit["variants"]["inlet_limit_6.86pct"]["top1_mismatch_groups"]
assert np.allclose(stats6["cluster_bootstrap"]["fraction_ci95"], lit["variants"]["inlet_limit_6.86pct"]["bootstrap"]["ci95"])
assert read_json("analysis/nh3_field_2026_10_06/nh3_1_2/summary.json")["selfcheck_supported_chain"]["pass_"]   # the chain self-check of the first extraction

# (group, panel title, by-product whose selectivity sets the marker area)
MEOH_GROUPS = [("10.1021/acscatal.5c05984 | 100 bar | H2/CO2 4 | 10 NL/g/h", "Re/TiO$_2$, 100 bar", "SCH4", "CH$_4$"),
               ("10.1126/sciadv.abi6012 | 40 bar | H2/CO2 3 | 24 NL/g/h", "InNi$_3$C$_{0.5}$ on four supports, 4 MPa",
                "SCO", "CO")]
NH3_GROUP = ("10.1002/aenm.201801772 | 400 C | 5 MPa | H2/N2 3 | 6.6e+04 mL/g/h",
             "Ru, Fe, Co on BaTiO$_{3-x}$H$_x$, 5 MPa")


def meoh_leaderboards():
    """Panel b: comparisons whose paper leader is not the plant-cost leader, by paper leaderboard, in the inert-limited
    loop, and by STY without the limit; scored with the frozen meoh_candidates.aggregate (X*S as in
    run_literature_inversion.py) and checked against the frozen summaries."""
    c = pcand.assign(XS=pcand.X * pcand.SMeOH)
    rows = []
    for key, label, col, up in (("STY", "STY", S6, "STY"), ("XS", "X·S", S6, "XS"), ("X", "X", S6, "X"),
                                ("SMeOH", "S$_{MeOH}$", S6, "SMeOH"), ("STY_no_limit", "STY", S5, "STY")):
        gm, s_ = aggregate(c, col, up_col=up)
        m = gm[gm.top1_mismatch]
        rows.append(dict(key=key, label=label, loop="inert-limited (primary)" if col == S6 else "no inlet limit",
                         cost_column=col, leaderboard=up, groups=s_["groups"], papers=s_["papers"],
                         mismatch_groups=s_["top1_mismatch_groups"], fraction=s_["top1_mismatch_fraction"],
                         regret_gt5pct=int((m.regret > 0.05).sum()), papers_with_mismatch=s_["papers_with_mismatch"],
                         regret_median_mismatched=s_["regret_median_mismatched"]))
    t = pd.DataFrame(rows).set_index("key")
    q6, q5 = pool["S6"], pool["S5"]
    assert (t.loc["STY", "mismatch_groups"], t.loc["STY", "regret_gt5pct"]) == (
        q6["primary"]["disagreements"], q6["primary"]["gt5pct"])
    assert (t.loc["STY_no_limit", "mismatch_groups"], t.loc["STY_no_limit", "regret_gt5pct"]) == (
        q5["primary"]["disagreements"], q5["primary"]["gt5pct"])
    for k, r in (("X", "leaderboard_X"), ("SMeOH", "leaderboard_SMeOH"), ("XS", "leaderboard_XS")):
        assert (t.loc[k, "mismatch_groups"], t.loc[k, "regret_gt5pct"]) == (q6[r]["disagreements"], q6[r]["gt5pct"])
    ci = {"STY": q6["primary"]["bootstrap_frozen_inversion"]["ci95"],
          "STY_no_limit": q5["primary"]["bootstrap_frozen_inversion"]["ci95"]}
    t["CI95_low"] = [ci[k][0] if k in ci else np.nan for k in t.index]
    t["CI95_high"] = [ci[k][1] if k in ci else np.nan for k in t.index]
    return t


def meoh_group(g, byp):
    """Panels d, e: the entries of one comparison group with both loops' costs and purges."""
    cols = ["entry", "catalyst", "T_C", "X", "SMeOH", "SCO", "SCH4", "STY", S6, "purge_recycled_opt_inlet", S5,
            "purge_recycled_opt"]
    t = cand[cand.group == g][cols].copy().reset_index(drop=True)
    assert len(t) >= 2, g
    t["STY_leader"] = t.STY == t.STY.max()
    t["plant_cost_leader"] = t[S6] == t[S6].min()
    t["plant_cost_leader_no_limit"] = t[S5] == t[S5].min()
    t.attrs["byproduct"] = byp
    return t


def support_name(catalyst):
    """'InNi3C0.5/m-ZrO2 [Fig. 2B, ...]' -> 'm-ZrO$_2$'."""
    sup = catalyst.split(" [")[0].split("/")[-1]
    return sup.replace("O2", "O$_2$")


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
    g = next(r for r in nh3_groups if r["group"] == NH3_GROUP[0])
    rows = [r for r in nh3_pcand if r["group"] == NH3_GROUP[0]]
    assert len(rows) == int(g["n"]), (len(rows), g["n"])
    return rows, g


SCAN = read_json("analysis/meoh_catalyst_level_2026_10_19/summary_raised_limit_scan.json")
NOLIM = read_json("analysis/meoh_catalyst_level_2026_10_19/summary_no_limit.json")
INDUSTRIAL = ("5", "6.86", "8", "10")          # inlet limits inside the 4.4-9.8 % of industrial loop designs


def draw_track(pg):
    """Panel a: literature -> ACSA -> multiscale cost chain -> leaderboards (editable source Fig2a.pptx)."""
    import matplotlib.image as mpimg
    img = mpimg.imread(os.path.join(HERE, "Fig2a_from_pptx.png"))
    ink = (img[..., :3].min(-1) < 0.97)
    r, c = np.where(ink.any(1))[0], np.where(ink.any(0))[0]
    img = img[r[0]:r[-1] + 1, c[0]:c[-1] + 1]
    h, w = img.shape[:2]
    W_ = 174.0
    H_ = W_ * h / w
    ax = pg.ax(5, 184 - 1 - H_, W_, H_)
    ax.imshow(img, interpolation="lanczos")
    ax.axis("off")
    pg.letter("a", 2, 182)


def dot(ax, x, y, lo=None, hi=None, fc=RU, ec=INK, s=42, z=4):
    if lo is not None:
        ax.plot([x, x], [lo, hi], color=INK, lw=1.0, zorder=z - 1, solid_capstyle="butt")
    ax.scatter([x], [y], s=s, facecolor=fc, edgecolor=ec, lw=0.8, zorder=z)


HALO = [pe.withStroke(linewidth=2.2, foreground="white")]     # keeps labels legible where they cross data


if __name__ == "__main__":
    pg = Page(180.0, 184.0)
    draw_track(pg)

    # ---- b: methanol, between catalysts and over every operating point ------------------------------------------
    b = pg.ax(41, 70, 43, 36)          # horizontal forest layout: labels and counts to the left (2026-10-23)
    kj = read_json("analysis/meoh_catalyst_level_2026_10_19/summary.json")
    lb = meoh_leaderboards()
    assert kj["point_level_total"]["changed"] == pool["S6"]["primary"]["disagreements"]
    rows = []
    for key, lab, kc, nl, sk in (
            ("cat_raised", "more catalyst", kj["conversion_raised"]["cost_f0.95"]["cat_primary"],
             NOLIM["conversion_raised"]["cost_f0.95"]["cat_primary"], "conversion_raised"),
            ("cat_lab", "laboratory X", kj["cat_primary"]["comparison"], NOLIM["laboratory_conversion"]["cat_primary"],
             "laboratory_conversion")):
        scan = [SCAN[L][sk]["changed"] / SCAN[L][sk]["groups"] for L in INDUSTRIAL]
        assert SCAN["6.86"][sk]["changed"] == kc["changed"]
        rows.append((key, lab, kc["changed"], kc["groups_2plus_catalysts"], kc["ci95"], nl["changed"] / nl["groups_2plus_catalysts"],
                     (min(scan), max(scan))))
    assert (rows[0][2], rows[1][2]) == (21, 26)
    c5 = pcand.assign(XS=pcand.X * pcand.SMeOH)
    for key, lab, up in (("STY", "STY", "STY"), ("X", "conversion", "X"), ("SMeOH", "selectivity", "SMeOH")):
        r = lb.loc[key]
        _, s5 = aggregate(c5, S5, up_col=up)
        ci = (r.CI95_low, r.CI95_high) if np.isfinite(r.CI95_low) else None
        rows.append((key, lab, int(r.mismatch_groups), int(r.groups), ci, s5["top1_mismatch_fraction"], None))
    ys = [0, 1, 2.75, 3.75, 4.75]               # rows top to bottom; a header row above each group

    def fx(mm):                                  # figure millimetres -> axes fraction of b
        return (mm - 41) / 43
    for y, (key, lab, n, g, ci, f5, band) in zip(ys, rows):
        f = n / g
        cat = key.startswith("cat")
        if band:
            b.plot(band, [y, y], color=PALE_B, lw=8.0, solid_capstyle="round", zorder=1)
        b.plot([f5, f], [y, y], color=MID, lw=0.8, ls=(0, (1.5, 1.2)), zorder=1.5)
        b.scatter([f5], [y], s=30, facecolor="white", edgecolor=MID, lw=0.8, zorder=3)
        if ci:
            b.plot(ci, [y, y], color=INK, lw=1.0, zorder=3, solid_capstyle="butt")
        b.scatter([f], [y], s=42, facecolor=RU if cat else OS, edgecolor=INK, lw=0.8, zorder=4)
        yt = b.get_yaxis_transform()
        b.text(fx(15.5), y, lab, transform=yt, fontsize=5.8, va="center", ha="left", clip_on=False)
        b.text(fx(39.5), y, "%d/%d" % (n, g), transform=yt, fontsize=5.8, va="center", ha="right", clip_on=False)
    for y, t in ((-0.85, "between catalysts"), (1.9, "every operating point")):
        b.text(fx(14), y, t, transform=b.get_yaxis_transform(), fontsize=5.8, fontweight="bold", va="center",
               ha="left", clip_on=False)
    b.axhline(1.9 - 0.55, xmin=fx(14), xmax=1, color=INK, lw=0.4, clip_on=False, ls=(0, (1, 1.5)))
    b.set_ylim(5.35, -1.35)
    b.set_yticks([])
    b.set_xlim(0, 0.85)
    b.set_xticks([0, 0.2, 0.4, 0.6, 0.8])
    b.set_xticklabels(["0", "20", "40", "60", "80"])
    b.set_xlabel("STY leader ≠ plant choice (%)")
    b.grid(axis="x", color=TINT_B, lw=0.5, zorder=0)
    b.set_axisbelow(True)
    h = [b.scatter([], [], s=42, facecolor=RU, edgecolor=INK, lw=0.8),
         Patch(facecolor=PALE_B, edgecolor="none"),
         b.scatter([], [], s=30, facecolor="white", edgecolor=MID, lw=0.8)]
    pg.fig.legend(h, ["6.86% inlet limit", "5–10% limits", "no limit"], loc="lower left", ncol=3,
                  bbox_to_anchor=(13 / pg.W, 106.6 / pg.H), fontsize=5.6, handlelength=1.2, frameon=False,
                  columnspacing=1.4, handletextpad=0.4, borderaxespad=0)
    boxed(b)
    pg.letter("b", 2, 117)
    pg.title("Methanol, %d comparisons in %d papers" % (lb.loc["STY", "groups"], lb.loc["STY", "papers"]), 14, 117)

    # ---- c: ammonia, by rate basis, and what the 12 disagreements differ by -----------------------------------
    c1 = pg.ax(108, 70, 30, 38)
    pr, nv = nh3["primary"], nh3["variants"]
    ncases = [("per g\ncatalyst", pr, RU), ("per g\nmetal", nv["per_g_metal_leaderboard"], OS),
              ("90% Ru\nrecovery", nv["Ru_recovery_90pct"], OS)]
    for i, (lab, x, col) in enumerate(ncases):
        f = x["top1_mismatch_fraction"]
        l, h_ = x["bootstrap_papers"]["mismatch_fraction_ci95"]
        dot(c1, i, f, l, h_, fc=col)
        c1.text(i + 0.16, f, "%d/%d" % (x["top1_mismatch_groups"], x["groups"]), fontsize=5.8, va="center", ha="left",
                path_effects=HALO)
    c1.set_xticks(range(len(ncases)))
    c1.set_xticklabels([l for l, _, _ in ncases], fontsize=5.6)
    c1.set_xlim(-0.5, 2.7)
    c1.set_ylim(0, 0.85)
    c1.set_yticks([0, 0.2, 0.4, 0.6, 0.8])
    c1.set_yticklabels(["0", "20", "40", "60", "80"])
    c1.set_ylabel("rate leader ≠ plant choice (%)")
    boxed(c1)

    kinds, fe_wins = nh3_kind_counts()
    c2 = pg.canvas(144, 70, 36, 38)
    korder = [("fused-Fe reference vs supported catalyst", "commercial fused-Fe\nreference", DARK_G),
              ("different metal", "Fe on the same\nsupport", FE),
              ("same metal and metal content", "other support\nor promoter", RU),
              ("same metal, different metal content", "other metal\ncontent", OS)]
    assert fe_wins == kinds["different metal"]["groups"]
    mis = [g for g in nh3_groups if g["top1_mismatch"].lower() in ("true", "1")]
    assert len(mis) == pr["top1_mismatch_groups"] == 12
    cell, gap = 5.0, 1.1
    k = 0
    ytop = 33.5
    for j, (kname, lab, col) in enumerate(korder):
        gs = sorted((g for g in mis if g["mismatch_kind"] == kname), key=lambda g: -float(g["regret"]))
        assert len(gs) == kinds[kname]["groups"]
        y = ytop - j * 8.6
        for i, g in enumerate(gs):
            x0 = i * (cell + gap)
            c2.add_patch(FancyBboxPatch((x0, y - cell), cell, cell, boxstyle="round,pad=0,rounding_size=0.8", fc=col,
                                        ec="none"))
            if float(g["regret"]) > 0.05:
                c2.add_patch(Circle((x0 + cell / 2, y - cell / 2), 0.75, fc="white", ec="none"))
        c2.text(0, y + 0.6, lab.replace("\n", " "), fontsize=5.6, ha="left", va="bottom", color=INK)
    # vertical rule left of the key (author's mark-up, 2026-10-23)
    c2.plot([-1.25, -1.25], [2.2, 34.3], color=INK, lw=0.8, solid_capstyle="butt", clip_on=False)
    c2.add_patch(Circle((1.0, 0.9), 0.75, fc=INK, ec="none"))
    c2.text(2.4, 0.9, "cost gap > 5%", fontsize=5.4, va="center", ha="left")
    pg.letter("c", 96, 117)
    pg.title("Ammonia, %d comparisons in %d papers" % (pr["groups"], pr["papers"]), 108, 117)
    pg.fig.text(144 / pg.W, 109.5 / pg.H, "the %d disagreements" % pr["top1_mismatch_groups"], fontsize=6,
                fontweight="bold", va="bottom")

    # ---- d, e: two methanol comparisons ------------------------------------------------------------------------
    # Each entry: filled circle with the 6.86% inlet limit, open circle without it, joined by a light stem; marker
    # area scales with the by-product selectivity. Leaders are ringed; labels carry a white halo and sit in empty
    # space with a hairline leader, so no label covers a marker.
    for k, (g, title, byp, byp_tex) in enumerate(MEOH_GROUPS):
        t = meoh_group(g, byp)
        e = pg.ax(14 + k * 59, 11, 45, 40)
        sty, cost, cost5 = t.STY.to_numpy(), t[S6].to_numpy(), t[S5].to_numpy()
        size = 16 + 120 * t[byp].to_numpy()
        for x, y0, y1 in zip(sty, cost5, cost):
            e.plot([x, x], [y0, y1], color=AMB_D, lw=0.7, alpha=0.55, zorder=1, solid_capstyle="butt")
        e.scatter(sty, cost5, s=size, facecolor="white", ec=AMB_D, lw=0.7, zorder=1.5)
        e.scatter(sty, cost, s=size, c=AMB_P, ec="white", lw=0.7, zorder=2)
        e.scatter(sty, cost, s=size, facecolor="none", ec=AMB_D, lw=0.5, zorder=2.1)
        iu, ie = int(np.argmax(sty)), int(np.argmin(cost))
        assert t.STY_leader[iu] and t.plant_cost_leader[ie] and iu != ie
        for i_, col in ((iu, RED), (ie, DARK_G)):
            e.scatter([sty[i_]], [cost[i_]], s=size[i_] + 60, facecolor="none", ec=col, lw=1.1, zorder=3)
        names = [support_name(c) if k == 1 else "" for c in t.catalyst]
        xr = sty.max() - sty.min()
        lab_kw = dict(fontsize=5.6, fontweight="bold", path_effects=HALO, zorder=6)

        def leader(col):
            return dict(arrowstyle="-", lw=0.5, color=col, shrinkA=0.5, shrinkB=5)
        if k == 0:
            # d: the two leaders sit among other entries near 1,000 EUR/t; labels go to the empty upper right
            for i_, lab, col, xy in ((iu, "STY leader", RED, (0.97, 0.66)), (ie, "plant choice", DARK_G, (0.70, 0.45))):
                e.annotate(lab, (sty[i_], cost[i_]), xytext=xy, textcoords="axes fraction", ha="right", va="center",
                           color=col, arrowprops=leader(col), **lab_kw)
        else:
            # e: entries are named by support; the leaders carry their support in the leader label
            for i_, nm in enumerate(names):
                if nm and i_ not in (iu, ie):
                    e.annotate(nm, (sty[i_], cost[i_]), xytext=(6, 0), textcoords="offset points", fontsize=5.4,
                               ha="left", va="center", color=INK, path_effects=HALO, zorder=6)
            e.annotate("STY leader, " + names[iu], (sty[iu], cost[iu]), xytext=(0.97, 0.74), textcoords="axes fraction",
                       ha="right", va="center", color=RED, arrowprops=leader(RED), **lab_kw)
            e.annotate("plant choice,\n" + names[ie], (sty[ie], cost[ie]), xytext=(-10, 0), textcoords="offset points",
                       ha="right", va="center", color=DARK_G, linespacing=1.1, **lab_kw)
        e.set_xlabel("STY (g$_{MeOH}$ g$_{cat}^{-1}$ h$^{-1}$)")
        e.set_ylabel("net cost (EUR t$^{-1}$)")
        allc = np.concatenate([cost, cost5])
        plain = FuncFormatter(lambda v, _: "{:,.0f}".format(v))
        if allc.max() / allc.min() > 2:
            e.set_yscale("log")
            e.set_ylim(allc.min() / 1.25, allc.max() * 2.6)
            e.yaxis.set_minor_formatter(FuncFormatter(lambda v, _: "{:,.0f}".format(v) if str(int(round(v)))[0] in "25"
                                                      else ""))
        else:
            span = allc.max() - allc.min()
            e.set_ylim(allc.min() - 0.12 * span, allc.max() + 0.55 * span)
        e.yaxis.set_major_formatter(plain)
        e.set_xlim(sty.min() - (0.45 if k == 1 else 0.2) * xr, sty.max() + 0.16 * xr)   # e: room for the plant label
        e.text(0.04, 0.95, title, transform=e.transAxes, fontsize=6, va="top", fontweight="bold")
        boxed(e)
    pg.letter("d", 2, 57)
    pg.letter("e", 61, 57)

    # ---- f: one ammonia comparison -------------------------------------------------------------------------------
    rows_, gm = nh3_example()
    fax = pg.ax(132, 11, 48, 40)
    mcol = {"Ru": RU, "Fe": FE, "Co": OTHER}
    rate = np.array([float(r["paper_rate"]) for r in rows_]) / 1000.0
    cost = np.array([float(r["cost_USD_t"]) for r in rows_])
    met = [r["metal"] for r in rows_]
    for m in ("Ru", "Fe", "Co"):
        sel = [i for i, x in enumerate(met) if x == m]
        fax.scatter(rate[sel], cost[sel], s=34, c=mcol[m], ec="white", lw=0.7, zorder=2, label=m)
        fax.scatter(rate[sel], cost[sel], s=34, facecolor="none", ec=INK, lw=0.4, zorder=2.1)
    iu, ie = int(np.argmax(rate)), int(np.argmin(cost))
    assert rows_[iu]["catalyst"] == gm["paper_winner"] and abs(cost[ie] - float(gm["plant_winner_cost"])) < 1e-9
    assert rows_[ie]["metal"] == "Fe" and float(rows_[ie]["metal_wt_pct"]) == 1.0
    fax.scatter([rate[iu]], [cost[iu]], s=110, facecolor="none", ec=RED, lw=1.1, zorder=3)
    fax.scatter([rate[ie]], [cost[ie]], s=110, facecolor="none", ec=DARK_G, lw=1.1, zorder=3)
    fax.annotate("rate leader", (rate[iu], cost[iu]), xytext=(-4, 10), textcoords="offset points", fontsize=5.6,
                 color=RED, ha="right", fontweight="bold", path_effects=HALO, zorder=6)
    fax.annotate("plant choice", (rate[ie], cost[ie]), xytext=(9, -1), textcoords="offset points", fontsize=5.6,
                 color=DARK_G, ha="left", va="center", fontweight="bold", path_effects=HALO, zorder=6)
    fax.set_xlabel("rate (mmol g$_{cat}^{-1}$ h$^{-1}$)")
    fax.set_ylabel("plant cost (USD t$^{-1}$ NH$_3$)")
    fax.set_xlim(-2.5, 55)
    fax.set_ylim(11.5, 34.5)
    fax.legend(loc="center right", bbox_to_anchor=(1.0, 0.62), fontsize=5.6, handletextpad=0.1, borderaxespad=0.3,
               labelspacing=0.3)
    fax.text(0.04, 0.95, NH3_GROUP[1], transform=fax.transAxes, fontsize=6, va="top", fontweight="bold")
    boxed(fax)
    pg.letter("f", 121, 57)

    with scripts_at_least(5.3):
        layout.audit(pg.fig)
        pg.save(HERE, "FigField")
