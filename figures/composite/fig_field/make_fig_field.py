"""Figure 2 — published laboratory leaderboards against plant-cost leaderboards, methanol and ammonia.

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
from PIL import Image
import pandas as pd
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from matplotlib.ticker import FuncFormatter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from matplotlib.patches import Polygon, Rectangle  # noqa: E402
import glyphs  # noqa: E402
from style import (DARK_B, DARK_G, FE, INK, MID, OTHER, PALE_B, RED, RU, TINT_B, TINT_G, Page, boxed,  # noqa: E402
                   crop_rgba, scripts_at_least)

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


if __name__ == "__main__":
    pg = Page(183.0, 189.0)

    # ---- a: literature -> ACSA -> multiscale chain -> leaderboards (U-shaped flow) --------------------------------
    # flat thumbnails: glyphs.py; atomistic renders: build_atoms.py (OVITO); pellet, bed and loop: single generated
    # images with transparent background (assets/pellet.png, bed.png, loop.png)
    a = pg.canvas(5, 122, 176, 64)
    AS = os.path.join(HERE, "assets")
    SOFT = (0.62, 0.72, 0.88, 0.55)                     # broad translucent flow arrows

    def place(name, cx, cy, h, z=2):
        im_ = Image.open(os.path.join(AS, name + ".png")).convert("RGBA")
        im_ = im_.crop(im_.getbbox())
        img = np.asarray(im_) / 255.0
        w = h * img.shape[1] / img.shape[0]
        ext = [cx - w / 2, cx + w / 2, cy - h / 2, cy + h / 2]
        a.imshow(img, extent=ext, zorder=z, interpolation="lanczos")
        return ext

    def flow(p0, p1, rad=0.0, lw=7.0):
        a.add_patch(FancyArrowPatch(p0, p1, connectionstyle="arc3,rad=%.2f" % rad, arrowstyle="simple,head_width=1.6,"
                                    "head_length=1.2,tail_width=0.75", mutation_scale=lw, fc=SOFT, ec="none",
                                    zorder=0.6))

    def tile(x, y, w, h, fc):
        a.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=1.2", fc=fc, ec="none",
                                   zorder=1.1))
        return (x + 0.7, y + 0.7, w - 1.4, h - 1.4)

    ty, th_ = 45.0, 18.0
    # literature
    a.add_patch(FancyBboxPatch((0, ty), 31, th_, boxstyle="round,pad=0,rounding_size=1.6", fc="white", ec="#9AA0AA",
                               lw=0.55, zorder=1))
    glyphs.papers(a, *tile(1.3, ty + 1.3, 11.5, th_ - 2.6, TINT_B), INK, PALE_B, RU, FE)
    a.text(14.5, ty + th_ - 3.6, "Literature", fontsize=6.3, fontweight="bold", va="center")
    a.text(14.5, ty + 6.2, "papers + SI:\n90 methanol,\n52 ammonia", fontsize=5.0, va="center", linespacing=1.2)
    # ACSA with its three steps; the language model is used for extraction only
    ax0, ax1 = 37.0, 133.0
    a.add_patch(FancyBboxPatch((ax0, ty - 1.0), ax1 - ax0, th_ + 2.0, boxstyle="round,pad=0,rounding_size=2.0",
                               fc=TINT_B, ec="#9AA0AA", lw=0.55, zorder=0.9))
    a.text(ax0 + 1.8, ty + th_ - 0.6, "ACSA", fontsize=6.6, fontweight="bold", va="top", ha="left", color=DARK_B)
    steps = [("Extract", "value, unit, page", "language model", RU, "table"),
             ("Self-check", "hand-built cases\nreproduced first", "code", DARK_G, "selfcheck"),
             ("Bound", "full optimization\nonly where needed", "code", DARK_G, "bound")]
    cw, cg = 28.0, 2.6
    for k, (tt, sub, who, wc, g) in enumerate(steps):
        cx0 = ax0 + 8.6 + k * (cw + cg)
        a.add_patch(FancyBboxPatch((cx0, ty + 0.8), cw, th_ - 3.6, boxstyle="round,pad=0,rounding_size=1.2",
                                   fc="white", ec="none", zorder=1))
        tl = tile(cx0 + 0.8, ty + 1.6, 11.0, th_ - 5.2, TINT_G if k else TINT_B)
        if g == "table":
            glyphs.table(a, *tl, INK, PALE_B, "#E3C16F")
        elif g == "selfcheck":
            glyphs.selfcheck(a, *tl, INK, DARK_G)
        else:
            glyphs.bound(a, *tl, INK, "white", FE)
        a.text(cx0 + 13.0, ty + th_ - 5.6, tt, fontsize=6.0, fontweight="bold", va="center")
        a.text(cx0 + 13.0, ty + 6.0, sub, fontsize=4.9, va="center", linespacing=1.15)
        a.text(cx0 + cw - 0.8, ty + th_ - 3.4, who, fontsize=4.2, va="center", ha="right", color="white",
               bbox=dict(boxstyle="round,pad=0.22,rounding_size=0.7", fc=wc, ec="none"), zorder=6)
        if k < 2:
            a.add_patch(FancyArrowPatch((cx0 + cw + 0.2, ty + th_ / 2 - 0.9), (cx0 + cw + cg - 0.2, ty + th_ / 2 - 0.9),
                                        arrowstyle="-|>", mutation_scale=5, lw=0.6, color=INK, zorder=3))
    # leaderboards (output)
    a.add_patch(FancyBboxPatch((139, ty), 37, th_, boxstyle="round,pad=0,rounding_size=1.6", fc="white",
                               ec="#9AA0AA", lw=0.55, zorder=1))
    glyphs.bump(a, *tile(140.3, ty + 1.3, 11.5, th_ - 2.6, TINT_G), INK, PALE_B, RED, DARK_G)
    a.text(153.5, ty + th_ - 3.6, "Leaderboards", fontsize=6.3, fontweight="bold", va="center")
    a.text(153.5, ty + 6.2, "laboratory leader\nvs plant-cost\nleader (b, c)", fontsize=5.0, va="center",
           linespacing=1.2)
    # broad flow arrows (U-shaped): literature -> ACSA -> chain -> leaderboards
    flow((31.2, ty + th_ / 2), (36.8, ty + th_ / 2))
    flow((ax0 + 6.0, ty - 1.2), (12.0, 36.4), rad=-0.22)
    flow((168.0, 36.6), (160.0, ty - 0.2), rad=-0.25)
    a.text(30.0, 40.6, "every candidate", fontsize=5.0, style="italic", ha="center", va="center", color=DARK_B)
    a.text(151.0, 40.6, "plant cost", fontsize=5.0, style="italic", ha="center", va="center", color=DARK_B)
    # bottom band: the unchanged multiscale chain (soft vertical gradient, as in multiscale-catalysis schematics)
    band = FancyBboxPatch((0, 0), 176, 36.0, boxstyle="round,pad=0,rounding_size=1.8", fc="none", ec="#9AA0AA",
                          lw=0.55, zorder=0.3)
    a.add_patch(band)
    grad = np.linspace(0.93, 1.0, 64)[:, None, None] * np.ones((64, 2, 3))
    gi = a.imshow(grad, extent=[0, 176, 0, 36.0], aspect="auto", zorder=0.2, origin="lower")
    gi.set_clip_path(band)
    boxes = {}
    for key, cx, h in (("surface", 15, 12.5), ("nanoparticle", 42, 12.5), ("pellet", 67, 10.5), ("bed", 90, 19.0),
                       ("loop", 127, 19.0)):
        boxes[key] = place(key, cx, 19.5, h)
    for k1, k2, fx, fy in (("surface", "nanoparticle", 0.45, 0.80), ("nanoparticle", "pellet", 0.40, 0.55),
                           ("pellet", "bed", 0.45, 0.62)):
        e1, e2 = boxes[k1], boxes[k2]
        sx, sy = e2[0] + fx * (e2[1] - e2[0]), e2[2] + fy * (e2[3] - e2[2])
        r = 0.9
        a.add_patch(Rectangle((sx - r, sy - r), 2 * r, 2 * r, fc="none", ec=INK, lw=0.5, zorder=3))
        fx0 = e1[1] - 1.2
        a.add_patch(Polygon([(fx0, e1[3] - 1.2), (sx - r, sy + r), (sx - r, sy - r), (fx0, e1[2] + 1.2)],
                            closed=True, fc=(0.47, 0.54, 0.72, 0.10), ec=(0.3, 0.32, 0.36, 0.45), lw=0.3, zorder=1))
    # what passes between the model layers (labelled arrows)
    for x1, x2, lab in ((101.0, 113.5, "catalyst mass,\nbed volume"), (141.0, 151.0, "duties,\nflows")):
        a.add_patch(FancyArrowPatch((x1, 19.5), (x2, 19.5), arrowstyle="-|>", mutation_scale=7, lw=0.9, color=INK,
                                    zorder=3))
        a.text((x1 + x2) / 2, 23.2, lab, fontsize=4.8, ha="center", va="center", linespacing=1.1)
    # catalyst-dependent cost: flat stacked bars in the colours of the cost pools
    bx0, by0 = 156.5, 12.5
    a.plot([bx0 - 2.0, bx0 - 2.0, bx0 + 14.0], [by0 + 15.0, by0, by0], color=INK, lw=0.5, zorder=3)
    for xb_, parts in ((bx0, ((4.0, RU), (2.5, FE), (1.5, "#E3C16F"))),
                       (bx0 + 6.8, ((7.0, RU), (3.8, FE), (2.4, "#E3C16F")))):
        yy = by0
        for hh, c in parts:
            a.add_patch(Rectangle((xb_, yy), 4.6, hh, fc=c, ec=INK, lw=0.35, zorder=3))
            yy += hh
    a.text(bx0 + 2.3, by0 - 1.4, "cat. 1", fontsize=4.6, ha="center", va="center")
    a.text(bx0 + 9.1, by0 - 1.4, "cat. 2", fontsize=4.6, ha="center", va="center")
    # labels in white boxes and scale bars, after the multiscale-catalysis convention
    for lab, x in (("active site", 15), ("supported particle", 42), ("catalyst pellet", 67), ("loaded bed", 90),
                   ("synthesis loop", 127), ("cost per tonne", 162)):
        a.text(x, 32.6, lab, ha="center", va="center", fontsize=5.5, zorder=6,
               bbox=dict(boxstyle="round,pad=0.3,rounding_size=0.9", fc="white", ec="#C9CDD3", lw=0.4))
    for txt, x in (("1 nm", 15), ("10 nm", 42), ("5 mm", 67), ("1 m", 90), ("10 m", 127)):
        a.plot([x - 3.0, x + 3.0], [9.3, 8.5], color="#3A3D42", lw=1.6, solid_capstyle="butt", zorder=3)
        a.text(x, 6.9, "~" + txt, ha="center", va="center", fontsize=5.3, fontweight="bold")
    for x1, x2, txt, col in ((3, 100, "kinetics: descriptor turnover or measured rate law", RU),
                             (102, 148, "process optimization: T, P, separator, purge", FE),
                             (150, 173, "catalyst-dependent cost", "#C9A54A")):
        a.add_patch(FancyBboxPatch((x1, 1.2), x2 - x1, 3.4, boxstyle="round,pad=0,rounding_size=1.0", fc=col,
                                   ec="none", alpha=0.32, zorder=1))
        a.text((x1 + x2) / 2, 2.9, txt, ha="center", va="center", fontsize=5.0, zorder=2)
    pg.letter("a", 2, 187)

    # ---- b: methanol leaderboards, inert-limited loop (primary) and STY without the limit ------------------------
    # first bar since 2026-10-20: catalyst against catalyst, each at its best measured point (identity rules committed
    # before the count, analysis/meoh_catalyst_level_2026_10_19); the other bars count every operating point
    b = pg.ax(14, 70, 46, 38)
    lb = meoh_leaderboards()
    kc = read_json("analysis/meoh_catalyst_level_2026_10_19/summary.json")
    assert kc["point_level_total"]["changed"] == pool["S6"]["primary"]["disagreements"]
    kc = kc["cat_primary"]["comparison"]
    cat = pd.DataFrame([dict(label="STY\ncat.", groups=kc["groups_2plus_catalysts"], mismatch_groups=kc["changed"],
                             fraction=kc["changed"] / kc["groups_2plus_catalysts"], regret_gt5pct=kc["gt5pct"],
                             CI95_low=kc["ci95"][0], CI95_high=kc["ci95"][1])], index=["STY_catalyst"])
    assert abs(cat.fraction.iloc[0] - kc["fraction"]) < 1e-12
    lb = pd.concat([cat, lb.assign(label=lb.label.where(lb.index != "STY", "STY\npoints"))])
    xb = {"STY_catalyst": 0.0, "STY": 1.0, "XS": 2.0, "X": 3.0, "SMeOH": 4.0, "STY_no_limit": 5.55}
    fill = {"STY_catalyst": RU, "STY": PALE_B, "XS": PALE_B, "X": PALE_B, "SMeOH": PALE_B, "STY_no_limit": "white"}
    for k, r in lb.iterrows():
        x = xb[k]
        b.bar(x, r.fraction, 0.62, color=fill[k], ec=INK, lw=0.4, zorder=2)
        b.bar(x, r.regret_gt5pct / r.groups, 0.62, color="none", ec=INK, lw=0.4, hatch="//////", zorder=2.5)
        top = r.fraction
        if np.isfinite(r.CI95_low):
            b.errorbar([x], [r.fraction], yerr=[[r.fraction - r.CI95_low], [r.CI95_high - r.fraction]], fmt="none",
                       ecolor=INK, elinewidth=0.6, capsize=1.8, capthick=0.6, zorder=3)
            top = r.CI95_high
        b.text(x, top + 0.03, "%d/%d" % (r.mismatch_groups, r.groups), ha="center", va="bottom", fontsize=5.3)
    b.axvline(4.775, color=INK, lw=0.4, ls=(0, (1.5, 1.5)), zorder=1)
    b.text(2.0, 0.985, "inert-limited loop", ha="center", va="top", fontsize=5.3)
    b.text(xb["STY_no_limit"], 0.985, "no limit", ha="center", va="top", fontsize=5.3)
    pg.fig.text(14 / pg.W, 113.4 / pg.H, "error bars: 95 % CI; hatched: cost gap > 5 %", fontsize=5.3, va="top",
                ha="left")
    b.set_xticks([xb[k] for k in lb.index])
    b.set_xticklabels(list(lb.label), fontsize=5.6)
    b.set_ylim(0, 1.0)
    b.set_xlim(-0.55, 6.1)
    b.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    b.set_yticklabels(["0", "25", "50", "75", "100"])
    b.set_ylabel("leader changes (% of comparisons)")
    b.set_xlabel("paper leaderboard")
    boxed(b)
    pg.letter("b", 2, 117)
    pg.title("Methanol: %d comparisons, %d papers" % (lb.loc["STY", "groups"], lb.loc["STY", "papers"]), 14, 117)

    # ---- c: ammonia leaderboards ------------------------------------------------------------------------------
    c1 = pg.ax(74, 70, 34, 38)
    pr, nv = nh3["primary"], nh3["variants"]
    ncases = [("rate per\ng cat.", pr, RU), ("rate per\ng metal", nv["per_g_metal_leaderboard"], PALE_B),
              ("per g cat.,\n90 % Ru rec.", nv["Ru_recovery_90pct"], PALE_B)]
    for i, (lab, x, col) in enumerate(ncases):
        f = x["top1_mismatch_fraction"]
        l, h = x["bootstrap_papers"]["mismatch_fraction_ci95"]
        c1.bar(i, f, 0.62, color=col, ec=INK, lw=0.4, zorder=2)
        if "regret_bins" in x:
            c1.bar(i, x["regret_bins"]["gt5pct"]["groups"] / x["groups"], 0.62, color="none", ec=INK, lw=0.4,
                   hatch="//////", zorder=2.5)
        c1.errorbar([i], [f], yerr=[[f - l], [h - f]], fmt="none", ecolor=INK, elinewidth=0.6, capsize=1.8,
                    capthick=0.6, zorder=3)
        c1.text(i, h + 0.035, "%d/%d" % (x["top1_mismatch_groups"], x["groups"]), ha="center", va="bottom",
                fontsize=5.3)
    c1.set_xticks(range(len(ncases)))
    c1.set_xticklabels([l for l, _, _ in ncases], fontsize=5.3)
    c1.set_xlim(-0.55, 2.55)
    c1.set_ylim(0, 1.0)
    c1.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    c1.set_yticklabels(["0", "25", "50", "75", "100"])
    c1.set_ylabel("leader changes (% of comparisons)")
    c1.text(0.04, 0.97, "bars: 95 % CI\nhatched: cost gap > 5 %", transform=c1.transAxes, fontsize=5.3, va="top",
            color=INK)
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
        c2.text(0.35, y + 0.25, lab % v["groups"] if "%d" in lab else lab, fontsize=5.3, va="bottom", ha="left",
                linespacing=1.05)
        c2.text(v["groups"] + 0.4, y, "%d (%d paper%s); regret %s %%" % (
            v["groups"], v["papers"], "" if v["papers"] == 1 else "s", pct(v["regret_median"])),
            fontsize=5.3, va="center", ha="left")
    c2.set_ylim(-0.4, len(korder) - 0.05 + 0.55)
    c2.set_xlim(0, nmax * 1.95)
    c2.set_yticks([])
    c2.set_xlabel("mismatched comparisons (of %d)" % pr["top1_mismatch_groups"])
    boxed(c2)
    c2.text(0.99, 0.985, "regret: median cost penalty of\nbuilding the paper's leader", transform=c2.transAxes,
            fontsize=5.3, ha="right", va="top")
    pg.letter("c", 64, 117)
    pg.title("Ammonia: %d comparisons, %d papers" % (pr["groups"], pr["papers"]), 74, 117)

    # ---- d, e: methanol groups in the inert-limited loop (filled) and without the limit (open) ------------------
    for k, (g, title, byp, byp_tex) in enumerate(MEOH_GROUPS):
        t = meoh_group(g, byp)
        e = pg.ax(14 + k * 59, 11, 45, 40)
        sty, cost, cost5 = t.STY.to_numpy(), t[S6].to_numpy(), t[S5].to_numpy()
        purge = t.purge_recycled_opt_inlet.to_numpy()
        size = 8 + 160 * t[byp].to_numpy()
        for x, y0, y1 in zip(sty, cost5, cost):
            e.plot([x, x], [y0, y1], color=MID, lw=0.35, zorder=1)
        e.scatter(sty, cost5, s=size, facecolor="white", ec=MID, lw=0.4, zorder=1.5)
        e.scatter(sty, cost, s=size, c=PALE_B, ec=INK, lw=0.35, zorder=2)
        iu, ie = int(np.argmax(sty)), int(np.argmin(cost))
        assert t.STY_leader[iu] and t.plant_cost_leader[ie] and iu != ie
        e.scatter([sty[iu]], [cost[iu]], s=size[iu] + 28, facecolor="none", ec=RED, lw=0.9, zorder=3)
        e.scatter([sty[ie]], [cost[ie]], s=size[ie] + 28, facecolor="none", ec=DARK_G, lw=0.9, zorder=3)
        names = [support_name(c) if k == 1 else "" for c in t.catalyst]
        xr = sty.max() - sty.min()
        for i, nm in enumerate(names):
            if nm:
                right = sty[i] > sty.min() + 0.5 * xr
                e.annotate(nm, (sty[i], cost[i]), xytext=(-5 if right or i == ie else 5, 0),
                           textcoords="offset points", fontsize=5.3, ha="right" if right or i == ie else "left",
                           va="center")
        e.set_xlabel("STY (g$_{MeOH}$ g$_{cat}^{-1}$ h$^{-1}$)")
        e.set_ylabel("net cost (EUR t$^{-1}$)")
        allc = np.concatenate([cost, cost5])
        plain = FuncFormatter(lambda v, _: "{:,.0f}".format(v))
        if allc.max() / allc.min() > 2:
            # log axis: a few entries cost several times the leaders and would flatten them on a linear axis
            e.set_yscale("log")
            e.set_ylim(allc.min() / 1.25, allc.max() * 4.2)
            e.yaxis.set_minor_formatter(FuncFormatter(lambda v, _: "{:,.0f}".format(v) if str(int(round(v)))[0] in "25"
                                                      else ""))
        else:
            span = allc.max() - allc.min()
            e.set_ylim(allc.min() - 0.12 * span, allc.max() + 0.95 * span)
        e.yaxis.set_major_formatter(plain)
        e.set_xlim(sty.min() - 0.2 * xr, sty.max() + 0.1 * xr)
        e.text(0.03, 0.96, title, transform=e.transAxes, fontsize=5.6, va="top", fontweight="bold")
        key = ["marker area: %s selectivity" % byp_tex, "filled: inert-limited loop; open: no limit"]
        for j, line in enumerate(key):
            e.text(0.03, 0.86 - 0.075 * j, line, transform=e.transAxes, fontsize=5.3, va="top")
        for j, (i, lab, col) in enumerate(((iu, "STY leader", RED), (ie, "plant-cost leader", DARK_G))):
            e.text(0.03, 0.86 - 0.075 * (len(key) + j), "%s%s: %.1f %% purge" % (
                lab, (", " + names[i]) if names[i] else "", 100 * purge[i]), transform=e.transAxes, fontsize=5.3,
                va="top", color=col)
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
                 (rate[iu], cost[iu]), xytext=(-2, 7), textcoords="offset points", fontsize=5.3, color=RED,
                 ha="right")
    fax.annotate("plant-cost leader\nFe, 1 wt%% (regret %.0f %%)" % (100 * float(gm["regret"])), (rate[ie], cost[ie]),
                 xytext=(7, -1), textcoords="offset points", fontsize=5.3, color=DARK_G, ha="left", va="center")
    assert rows[ie]["metal"] == "Fe" and float(rows[ie]["metal_wt_pct"]) == 1.0
    fax.set_xlabel("rate (mmol g$_{cat}^{-1}$ h$^{-1}$)")
    fax.set_ylabel("plant cost (USD t$^{-1}$ NH$_3$)")
    fax.set_xlim(-2.5, 55)
    fax.set_ylim(11.5, 34.5)
    fax.legend(loc="upper right", fontsize=5.3, handletextpad=0.1, borderaxespad=0.3, labelspacing=0.3)
    fax.text(0.03, 0.96, NH3_GROUP[1], transform=fax.transAxes, fontsize=5.6, va="top", fontweight="bold")
    boxed(fax)
    pg.letter("f", 121, 57)

    with scripts_at_least(5.3):          # sub- and superscripts at >= 5.3 pt
        pg.save(HERE, "FigField")
