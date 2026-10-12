"""Extended Data figures 1-8, 183 mm wide, drawn from the panel tables of ed_data.py.

    pur_bridge_env/python render_extended_data.py          -> EDFig{N}_{slug}.{svg,pdf,png}
    pur_bridge_env/python render_extended_data.py 3 5      -> only ED Figs 3 and 5
"""
import os
import re
import sys

import numpy as np
from matplotlib.patches import Patch
from matplotlib.ticker import NullFormatter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "composite"))
import ed_data as E  # noqa: E402
from style import DARK_B, DARK_G, FE, INK, OS, OTHER, PALE_B, PALE_G, RED, RU, TINT_B, Page, boxed  # noqa: E402

# Numbered in the order the manuscript first cites them (2026-10-07 restructure); the panel functions keep the
# names of the first numbering (ed2 = bimetallic, ed4 = measured NH3, ed5 = actual Ru, ed6 = benchmark, ed7 = pruning).
SLUGS = {1: "extraction_accuracy", 2: "bound_pruning", 3: "methanol_robustness", 4: "meoh_plant_benchmark",
         5: "nh3_measured_catalysts", 6: "bimetallic_surfaces", 7: "ru_actual_mc", 8: "meoh_purge_inlet"}
METAL_COL = {"Ru": RU, "Fe": FE, "Co": OTHER, "Ni": PALE_G}


def pct_axis(ax, top=1.0):
    ax.set_ylim(0, top)
    t = [x for x in (0, 0.25, 0.5, 0.75, 1.0) if x <= top + 1e-9]
    ax.set_yticks(t)
    ax.set_yticklabels(["%d" % round(100 * x) for x in t])


# ---------------------------------------------------------------------------------------------- ED Fig. 1
def ed1():
    d = E.edfig1()
    a, b = d["a"][0], d["b"][0]
    pg = Page(183.0, 62.0)
    ax = pg.ax(14, 13, 98, 40)
    srcs = list(dict.fromkeys(a.source_label))
    fields = [("X_CO2", "X$_{CO_2}$", RU), ("S_MeOH", "S$_{MeOH}$", FE), ("STY", "STY", PALE_B)]
    w = 0.26
    for i, s in enumerate(srcs):
        for k, (f, lab, col) in enumerate(fields):
            r = a[(a.source_label == s) & (a.field == f)].iloc[0]
            x = i + (k - 1) * w
            ax.bar(x, r.acc_strict, w * 0.92, color=col, ec=INK, lw=0.35)
            ax.text(x, r.acc_strict + 0.025, "%d/%d" % (r.n_correct_strict, r.n_extracted), ha="center",
                    va="bottom", fontsize=5.0, rotation=90)
    for f, lab, col in fields:
        ax.bar(0, 0, color=col, ec=INK, lw=0.35, label=lab)
    ax.legend(loc="upper right", fontsize=5.6, ncol=3, handlelength=0.9, columnspacing=0.8, borderaxespad=0.2)
    ax.set_xticks(range(len(srcs)))
    ax.set_xticklabels(srcs, fontsize=6.0)
    ax.set_ylim(0, 1.35)
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels(["0", "25", "50", "75", "100"])
    ax.set_ylabel("strict accuracy (%)")
    ax.set_xlabel("where the value is printed")
    boxed(ax)
    pg.letter("a", 2, 59)
    pg.title("Field accuracy by source", 14, 59)
    bx = pg.ax(130, 13, 48, 40)
    for i, r in b.iterrows():
        col = RU if r.reference_set == "all" else PALE_B
        bx.bar(i, r.recall, 0.6, color=col, ec=INK, lw=0.4)
        bx.text(i, r.recall + 0.02, "%d/%d" % (r.matched, r.curated), ha="center", va="bottom", fontsize=5.4)
    bx.set_xticks(range(len(b)))
    bx.set_xticklabels(b.reference_set, fontsize=6.0)
    bx.set_ylim(0, 1.15)
    bx.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    bx.set_yticklabels(["0", "25", "50", "75", "100"])
    bx.set_ylabel("recall of curated entries (%)")
    bx.set_xlabel("reference set")
    boxed(bx)
    pg.letter("b", 120, 59)
    pg.title("Entry recall", 130, 59)
    return pg


# ---------------------------------------------------------------------------------------------- ED Fig. 2
def ed2():
    d, fe = E.edfig2()
    pg = Page(183.0, 64.0)
    titles = {"a": "Transition metals only", "b": "+ group 3–5 elements", "c": "+ sp metals"}
    new_dom = {"a": None, "b": "contains_group3to5", "c": "contains_sp_metal"}
    allc = d["c"][0]
    ylo, yhi = 0.55 * allc.cost_USD_t.min(), 1.6 * allc.cost_USD_t.max()
    xlo, xhi = allc.logTOF_673K.min() - 0.3, allc.logTOF_673K.max() + 0.3
    for k, p in enumerate("abc"):
        t = d[p][0]
        ax = pg.ax(14 + k * 58, 12, 48, 40)
        old = t[t.domain != new_dom[p]] if new_dom[p] else t.iloc[0:0]
        new = t[t.domain == new_dom[p]] if new_dom[p] else t
        if p == "a":
            fam, rest = new[new.family_3d_group6], new[~new.family_3d_group6]
            ax.scatter(rest.logTOF_673K, rest.cost_USD_t, s=5, c=OTHER, ec=INK, lw=0.25, zorder=2,
                       label="other (%d)" % len(rest))
            ax.scatter(fam.logTOF_673K, fam.cost_USD_t, s=9, c=FE, ec=INK, lw=0.25, zorder=3,
                       label="cheap 3d + Cr/Mo/W (%d)" % len(fam))
        else:
            ax.scatter(old.logTOF_673K, old.cost_USD_t, s=4, c=OTHER, ec=INK, lw=0.2, zorder=2,
                       label="previous layers (%d)" % len(old))
            ax.scatter(new.logTOF_673K, new.cost_USD_t, s=7, c=RU, ec=INK, lw=0.25, zorder=3,
                       label="added (%d)" % len(new))
        # the Fe benchmark goes into the legend (upper right is empty); a label on the line sat on the cheap surfaces
        ax.axhline(fe, color=DARK_G, lw=0.7, ls="--", zorder=1,
                   label="Fe %.2f (%d surfaces below)" % (fe, int(t.below_Fe.sum())))
        ax.set_yscale("log")
        ax.set_ylim(ylo, yhi)
        ax.set_xlim(xlo, xhi)
        ax.yaxis.set_minor_formatter(NullFormatter())
        ax.set_xlabel("log$_{10}$ TOF at 673 K (s$^{-1}$)")
        if k == 0:
            ax.set_ylabel("plant cost (USD t$^{-1}$ NH$_3$)")
        ax.legend(loc="upper right", fontsize=5.0, handletextpad=0.2, borderaxespad=0.3, labelspacing=0.3)
        boxed(ax)
        pg.letter(p, 2 + k * 58, 61)
        pg.title("%s: %d surfaces" % (titles[p], len(t)), 14 + k * 58, 61)
    return pg


# ---------------------------------------------------------------------------------------------- ED Fig. 3
def ed3():
    d = E.edfig3()
    a, b, c, dd = (d[k][0] for k in "abcd")
    ng = a.attrs["groups"]
    pg = Page(183.0, 182.0)
    up = 62.0                     # panels a-d sit above panel e
    # a bootstrap
    ax = pg.ax(14, 70 + up, 70, 40)
    ax.bar(a.bin_low_fraction, a.resamples, width=a.bin_high_fraction - a.bin_low_fraction, align="edge",
           color=PALE_B, ec=INK, lw=0.3)
    lo, hi = a.attrs["ci"]
    for v in (lo, hi):
        ax.axvline(v, color=INK, lw=0.6, ls="--")
    ax.axvline(a.attrs["point"], color=RED, lw=0.9)
    top = a.resamples.max() * 1.22
    ax.set_ylim(0, top)
    ax.text(a.attrs["point"] - 0.008, top * 0.97, "observed %d/%d\n(%.1f %%)" % (
        round(a.attrs["point"] * ng), ng, 100 * a.attrs["point"]), color=RED, fontsize=5.4, va="top", ha="right")
    ax.text(hi + 0.008, top * 0.75, "95 %% CI\n%.1f–%.1f %%" % (100 * lo, 100 * hi), fontsize=5.4,
            va="top")
    # x range from the populated bins (a 10 % margin), so the histogram fills the panel
    occ = a[a.resamples > 0]
    x0, x1 = max(0.0, float(occ.bin_low_fraction.min()) - 0.05), min(1.0, float(occ.bin_high_fraction.max()) + 0.05)
    ax.set_xlim(x0, x1)
    ticks = [t / 10 for t in range(0, 11) if x0 <= t / 10 <= x1]
    ax.set_xticks(ticks)
    ax.set_xticklabels(["%d" % round(100 * t) for t in ticks])
    ax.set_xlabel("comparisons whose STY leader is not the plant-cost leader (%)")
    ax.set_ylabel("bootstrap resamples")
    boxed(ax)
    pg.letter("a", 2, 117 + up)
    pg.title("Paper-cluster bootstrap, %s resamples of the papers" % format(a.attrs["n"], ","), 14, 117 + up)
    # b regret threshold
    bx = pg.ax(108, 70 + up, 70, 40)
    th = b.threshold.to_numpy()
    xs = np.where(th == 0, 0.0003, th)
    bx.plot(xs * 100, b.groups, color=RU, lw=0.9, marker="o", ms=2.6, mec=INK, mew=0.3)
    for x, g, p in zip(xs, b.groups, b.papers):
        bx.text(x * 100 * 1.08, g + 0.8, "%d (%d)" % (g, p), fontsize=5.0, va="bottom")
    bx.set_xscale("log")
    bx.set_xlim(0.02, 20)
    bx.set_xticks([0.03, 0.1, 0.5, 1, 2, 5, 10])
    bx.set_xticklabels(["0", "0.1", "0.5", "1", "2", "5", "10"])
    bx.xaxis.set_minor_formatter(NullFormatter())
    btop = int(5 * np.ceil(1.3 * float(b.groups.max()) / 5))
    bx.set_ylim(0, btop)
    bx.set_yticks(range(0, btop + 1, 5))          # counts: integer ticks
    bx.set_xlabel("regret at least (%)")
    bx.set_ylabel("mismatched comparisons")
    bx.text(0.97, 0.95, "labels: comparisons (papers)", transform=bx.transAxes, fontsize=5.0, ha="right", va="top")
    boxed(bx)
    pg.letter("b", 96, 117 + up)
    pg.title("Size of the disagreements", 108, 117 + up)
    # c noise scenarios
    cx = pg.ax(14, 12 + up, 70, 40)
    y = np.arange(len(c))[::-1]
    cx.errorbar(c.mismatch_groups_mean, y + 0.13, xerr=[c.mismatch_groups_mean - c.mismatch_groups_q025,
                                                        c.mismatch_groups_q975 - c.mismatch_groups_mean],
                fmt="o", ms=3, color=RU, mec=INK, mew=0.3, elinewidth=0.7, capsize=1.5, label="mismatched comparisons")
    cx.errorbar(c.noise_floor_mean, y - 0.13, xerr=[c.noise_floor_mean - c.noise_floor_q025,
                                                    c.noise_floor_q975 - c.noise_floor_mean],
                fmt="s", ms=2.6, color=OTHER, mec=INK, mew=0.3, elinewidth=0.7, capsize=1.5,
                label="noise floor (STY leader changes)")
    cx.axvline(c.attrs["observed"], color=RED, lw=0.8, ls="--")
    cx.text(c.attrs["observed"] + 0.8, -0.75, "observed %d" % c.attrs["observed"], color=RED, fontsize=5.2,
            va="center", ha="left")
    cx.set_yticks(y)
    short = {"meas_k1": "error ×1", "meas_k2": "error ×2", "meas_k4": "error ×4",
             "meas_k1_plus_extraction": "×1 + plot\nreadings"}
    cx.set_yticklabels([short[k] for k in c.scenario], fontsize=5.6)
    cx.set_ylim(-1.05, len(c) + 0.75)
    cx.set_xlim(0, max(ng, 10 * np.ceil(1.15 * float(c.mismatch_groups_q975.max()) / 10)))
    cx.set_xlabel("comparisons (of %d), mean and\n95 %% range over %s draws" % (ng, format(c.attrs["draws"], ",")))
    cx.legend(loc="upper right", fontsize=5.0, borderaxespad=0.3, handletextpad=0.3)
    boxed(cx)
    pg.letter("c", 2, 59 + up)
    pg.title("Measurement resampling" if "meas_k1_plus_extraction" not in set(c.scenario)
             else "Measurement and plot-reading resampling", 14, 59 + up)
    # d per-group persistence
    dx = pg.ax(108, 12 + up, 70, 40)
    xg = np.arange(len(dd)) + 1
    dx.bar(xg, dd.p_mismatch_meas_k1, 0.75, color=[RU if p >= 0.9 else PALE_B for p in dd.p_mismatch_meas_k1],
           ec=INK, lw=0.25, label="error ×1")
    if "p_mismatch_meas_k1_plus_extraction" in dd:
        dx.scatter(xg, dd.p_mismatch_meas_k1_plus_extraction, s=5, marker="_", c=INK, lw=0.7, zorder=3,
                   label="×1 + plot-reading errors")
    dx.axhline(0.9, color=INK, lw=0.5, ls=":")
    nrob = int((dd.p_mismatch_meas_k1 >= 0.9).sum())
    dx.text(len(dd) + 0.4, 1.02, "%d of %d stay in ≥ 90 %% of draws" % (nrob, len(dd)), fontsize=5.2, ha="right",
            va="bottom")
    dx.set_xlim(0.3, len(dd) + 0.7)
    pct_axis(dx, 1.3)
    dx.set_xlabel("observed mismatched comparison (sorted)")
    dx.set_ylabel("draws still mismatched (%)")
    dx.legend(loc="upper left", fontsize=5.0, borderaxespad=0.3, handletextpad=0.3, ncol=2)
    boxed(dx)
    pg.letter("d", 96, 59 + up)
    pg.title("Persistence of each observed disagreement", 108, 59 + up)
    # e limit on the reactor-inlet non-H2/CO2 fraction
    e = d["e"][0]
    ex = pg.ax(14, 12, 164, 40)
    fin = e[np.isfinite(e.limit)]
    xmax = 0.36
    lit = e.attrs.get("literature")
    if lit:
        ex.axvspan(lit[0] * 100, lit[1] * 100, color=PALE_G, alpha=0.45, lw=0, zorder=0)
        ex.text((lit[0] + lit[1]) * 50, 0.97, "published CO$_2$-to-methanol\nreactor inlets (%d designs)" % lit[2],
                fontsize=5.0, ha="center", va="top", color=DARK_G)
    ex.plot(fin.limit * 100, fin.share, color=RU, lw=0.9, marker="o", ms=2.6, mec=INK, mew=0.3,
            label="all comparisons")
    ex.plot(fin.limit * 100, fin.iso_share, color=FE, lw=0.9, marker="s", ms=2.4, mec=INK, mew=0.3,
            label="isothermal catalyst comparisons")
    nl = e[~np.isfinite(e.limit)].iloc[0]
    ex.scatter([xmax * 100], [nl.share], s=10, c=RU, ec=INK, lw=0.3, zorder=3, clip_on=False)
    ex.scatter([xmax * 100], [nl.iso_share], s=9, c=FE, marker="s", ec=INK, lw=0.3, zorder=3, clip_on=False)
    ref = e.attrs["reference"]
    r = e[np.isclose(e.limit, ref)].iloc[0]
    ex.axvline(ref * 100, color=RED, lw=0.7, ls="--")
    ex.text(ref * 100 + 0.4, 0.06, "workbook limit %.2f %% (sensitivity): %d/%d (%.0f %%); isothermal %d/%d (%.0f %%)" % (
        100 * ref, r.mismatched, r.groups, 100 * r.share, r.iso_mismatched, r.iso_groups, 100 * r.iso_share),
        color=RED, fontsize=5.2, va="bottom")
    ex.set_xlim(0, xmax * 100 + 1.5)
    ex.set_xticks([0, 5, 10, 15, 20, 25, 30, xmax * 100])
    ex.set_xticklabels(["0", "5", "10", "15", "20", "25", "30", "no limit"])
    pct_axis(ex, 1.0)
    ex.set_xlabel("limit on the reactor-inlet content of species other than H$_2$ and CO$_2$ (mol%)")
    ex.set_ylabel("STY leader \u2260 plant-cost leader (%)")
    ex.legend(loc="upper right", fontsize=5.0, borderaxespad=0.3, handletextpad=0.3)
    boxed(ex)
    pg.letter("e", 2, 59)
    pg.title("Inlet-composition limit of the loop", 14, 59)
    return pg


# ---------------------------------------------------------------------------------------------- ED Fig. 4
def ed4():
    t = E.edfig4()["a"][0]
    fe, ov = t.attrs["fe"], t.attrs["overall"]
    pg = Page(183.0, 80.0)
    ax = pg.ax(16, 12, 104, 60)
    for m in ("Ru", "Fe", "Co", "Ni"):
        s = t[t.metal == m]
        ax.scatter(s.rate_umol_per_g_metal_h / 1000.0, s.cost_USD_t, s=11, c=METAL_COL[m], ec=INK, lw=0.3, zorder=2,
                   label="%s (%d)" % (m, len(s)))
    ax.axhline(fe, color=DARK_G, lw=0.7, ls="--", zorder=1)
    ax.text(0.012, fe - 0.15, "Fe benchmark %.2f" % fe, color=DARK_G, fontsize=5.4, va="top")
    for name, col, dx_, dy in ((ov["rate_leader"], RED, 6, 10), (ov["plant_leader"], DARK_B, -8, -7)):
        r = t[t.catalyst == name].iloc[0]
        x, y = r.rate_umol_per_g_metal_h / 1000.0, r.cost_USD_t
        ax.scatter([x], [y], s=34, facecolor="none", ec=col, lw=0.9, zorder=3)
        ax.annotate("%s, %.2f" % (name, y), (x, y), xytext=(dx_, dy), textcoords="offset points", fontsize=5.4,
                    color=col, va="center", ha="left" if dx_ > 0 else "right")
    ax.set_xscale("log")
    ax.set_xlabel("laboratory rate (mmol g$_{metal}^{-1}$ h$^{-1}$)")
    ax.set_ylabel("plant cost (USD t$^{-1}$ NH$_3$)")
    ax.set_ylim(13, t.cost_USD_t.max() + 1.5)
    ax.legend(loc="upper right", fontsize=5.4, handletextpad=0.2, borderaxespad=0.4)
    boxed(ax)
    pg.letter("a", 2, 78)
    pg.title("%d measured catalysts (Humphreys et al. 2021 review), no metal recovery" % len(t), 16, 78)
    bx = pg.ax(138, 12, 40, 60)
    order = ["Ru", "Fe", "Co", "Ni"]
    for i, m in enumerate(order):
        s = t[t.metal == m].cost_USD_t.to_numpy()
        jit = (np.arange(len(s)) % 7 - 3) * 0.05
        bx.scatter(i + jit, s, s=6, c=METAL_COL[m], ec=INK, lw=0.25, zorder=2)
        bx.plot([i - 0.3, i + 0.3], [s.min()] * 2, color=INK, lw=0.7)
        bx.text(i, s.min() - 0.35, "%.2f" % s.min(), ha="center", va="top", fontsize=5.0)
    bx.axhline(fe, color=DARK_G, lw=0.7, ls="--", zorder=1)
    bx.set_xticks(range(len(order)))
    bx.set_xticklabels(order)
    bx.set_xlim(-0.6, 3.6)
    bx.set_ylim(ax.get_ylim())
    bx.set_ylabel("plant cost (USD t$^{-1}$ NH$_3$)")
    boxed(bx)
    pg.letter("b", 126, 78)
    pg.title("Lowest cost per metal", 138, 78)
    return pg


# ---------------------------------------------------------------------------------------------- ED Fig. 5
def ed5():
    d = E.edfig5()
    a, b, c, dd = (d[k][0] for k in "abcd")
    pg = Page(183.0, 112.0)
    # a across the full width (14-178 mm); treatment above each bar on the left, P and the median gap above it on
    # the right, so the axis spans exactly 0-1
    ax = pg.ax(14, 64, 164, 38)
    n = len(a)
    y = np.arange(n)[::-1].astype(float)
    cols = [OTHER, PALE_B, RU, FE, FE]
    ax.barh(y - 0.1, a.P_Fe_cheaper, 0.42, color=cols, ec=INK, lw=0.4)
    for yi, lab, pf, med in zip(y, a.treatment, a.P_Fe_cheaper, a.median_Ru_minus_Fe_USD_t):
        ax.text(0.004, yi + 0.17, lab, fontsize=5.6, ha="left", va="bottom")
        ax.text(0.996, yi + 0.17, "P(Fe cheaper) %.3f; median Ru %s Fe %s USD t$^{-1}$" % (
            pf, "−", ("%+.2f" % med).replace("-", "−")), fontsize=5.4, ha="right", va="bottom")
    ax.set_yticks([])
    ax.set_ylim(-0.45, n - 0.4)
    ax.set_xlim(-0.012, 1.012)
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_xlabel("P(Fe cheaper), %s draws" % format(int(a.draws.iloc[0]), ","))
    ax.axvline(0.5, color=INK, lw=0.4, ls=":")
    boxed(ax)
    pg.letter("a", 2, 109)
    pg.title("Fe against the Ru catalyst", 14, 109)
    specs = [("b", b, "u", "dispersion ratio u = D$_{Ru}$ / f$_{Fe}$", True),
             ("c", c, "r", "Ru recovery r (%)", False),
             ("d", dd, "Ru_wt_pct", "Ru content of the Ru/C bed (wt%)", False)]
    for k, (p, t, key, xl, logx) in enumerate(specs):
        bx = pg.ax(14 + k * (164 + 11) / 3, 12, (164 - 2 * 11) / 3, 36)   # three equal panels, 14-178 mm
        lo, hi = t[key + "_low"].to_numpy(), t[key + "_high"].to_numpy()
        mid = np.sqrt(lo * hi) if logx else (lo + hi) / 2
        scale = 100 if key == "r" else 1
        if key == "Ru_wt_pct":
            xs = np.arange(len(t))
            bx.bar(xs - 0.18, t.P_Ru_wins_A_bed, 0.36, color=RU, ec=INK, lw=0.35, label="A_bed")
            bx.bar(xs + 0.18, t.P_Ru_wins_A, 0.36, color=PALE_B, ec=INK, lw=0.35, label="A")
            bx.set_xticks(xs)
            bx.set_xticklabels(["%g–%g\nn = %d" % (l, h, n) for l, h, n in zip(lo, hi, t.draws)], fontsize=5.4)
        else:
            bx.plot(mid * scale, t.P_Ru_wins_A_bed, color=RU, lw=0.9, marker="o", ms=2.6, mec=INK, mew=0.3,
                    label="A_bed")
            bx.plot(mid * scale, t.P_Ru_wins_A, color=PALE_B, lw=0.9, marker="s", ms=2.4, mec=INK, mew=0.3,
                    label="A")
            if logx:
                bx.set_xscale("log")
                bx.set_xticks([11, 20, 30, 50])
                bx.set_xticklabels(["11", "20", "30", "50"])
                bx.xaxis.set_minor_formatter(NullFormatter())
        pct_axis(bx, 1.12)
        bx.set_xlabel(xl)
        if k == 0:
            bx.set_ylabel("P(Ru cheaper) (%)")
        bx.legend(loc="upper left", fontsize=5.0, borderaxespad=0.3, handletextpad=0.3, ncol=2, columnspacing=0.8)
        boxed(bx)
        pg.letter(p, 2 + k * (164 + 11) / 3, 55)
    pg.title("Where the Ru catalyst wins", 14, 55)
    return pg


# ---------------------------------------------------------------------------------------------- ED Fig. 6
def ed6():
    d = E.edfig6()
    a, b, c, dd = (d[k][0] for k in "abcd")
    # grid shared by the Extended Data figures: left column axes 14-84 mm, right column 108-178 mm; category labels
    # sit above their bars so that the bar panels align with the scatter panels instead of being pushed right
    pg = Page(183.0, 132.0)
    # a: Perez-Fortes terms: the stoichiometric feed (the same for every catalyst) and the catalyst-sensitive terms;
    # the two large rows are drawn at 1/10 so that the sensitive terms (tens of EUR/t) stay readable
    ax = pg.ax(14, 72, 70, 50)
    n = len(a)
    base = np.arange(n)[::-1].astype(float)
    big = a.term.str.startswith(("stoichiometric", "total")).to_numpy()
    scale = np.where(big, 0.1, 1.0)
    ax.barh(base + 0.02, a.model * scale, 0.24, color=RU, ec=INK, lw=0.35, label="model")
    ax.barh(base - 0.24, a.reference * scale, 0.24, color=PALE_B, ec=INK, lw=0.35, label="Pérez-Fortes 2016")
    short = {"stoichiometric": "stoichiometric H$_2$ + CO$_2$ (bars ×0.1)",
             "H$_2$ and CO$_2$ above": "feed above stoichiometry",
             "electricity": "electricity (model: compressors; ref.: net utilities)",
             "catalyst replacement": "catalyst replacement", "capital": "capital (8 %, 20 y)",
             "fixed O&M": "fixed O&M: ref. value on both sides (model's own %.1f)" % a.attrs["model_own_fixed_om"],
             "catalyst-sensitive": "catalyst-sensitive subtotal",
             "total": "total; ref. = NPV = 0 break-even price (bars ×0.1)"}
    for yb, t, m, r, sc, dev, cat in zip(base, a.term, a.model, a.reference, scale, a.deviation_pct, a.category):
        lab = next(v for k, v in short.items() if t.startswith(k))
        ax.text(2.0, yb + 0.17, lab, fontsize=5.2, ha="left", va="bottom",
                fontweight="bold" if cat in ("subtotal", "total") else "normal")
        ax.text(max(m, r) * sc + 2, yb - 0.11, ("%.1f / %.1f (%+.0f %%)" % (m, r, dev)).replace("-", "−"),
                va="center", fontsize=5.0)
        if cat == "subtotal":
            ax.axhline(yb + 0.62, color=INK, lw=0.4)
    ax.set_yticks([])
    ax.set_ylim(-0.5, n - 0.25)
    ax.set_xlim(0, 175)
    ax.set_xlabel("EUR t$^{-1}$ MeOH")
    ax.legend(loc="upper right", fontsize=5.0, borderaxespad=0.3, handlelength=1.2)
    boxed(ax)
    pg.letter("a", 2, 129)
    pg.title("Pérez-Fortes plant at its own assumptions", 14, 129)
    # b: parity across studies
    bx = pg.ax(108, 72, 70, 50)
    lim = (200, 1100)
    bx.fill_between(lim, [lim[0] * 0.95, lim[1] * 0.95], [lim[0] * 1.05, lim[1] * 1.05], color=PALE_G, lw=0,
                    zorder=0)
    bx.plot(lim, lim, color=INK, lw=0.5, zorder=1)
    for _, r in b.iterrows():
        col = RED if r.study.startswith("Perez") else (FE if r.study.startswith("Campos") else PALE_B)
        bx.scatter(r.reference_eur_t, r.model_eur_t, s=14, c=col, ec=INK, lw=0.35, zorder=3)
    pf = b[b.study.str.startswith("Perez")].iloc[0]
    bx.annotate(("Pérez-Fortes %+.1f %%" % pf.deviation_pct).replace("-", "−"), (pf.reference_eur_t, pf.model_eur_t),
                xytext=(-8, 14), textcoords="offset points", fontsize=5.2, color=RED, ha="right",
                arrowprops=dict(arrowstyle="-", color=RED, lw=0.5))
    bx.set_xlim(lim)
    bx.set_ylim(lim)
    bx.set_xlabel("reference cost (EUR t$^{-1}$)")
    bx.set_ylabel("model cost (EUR t$^{-1}$)")
    bx.text(0.04, 0.95, "%d cases, %d studies\nband: ±5 %%\ngreen: Campos (anchor)" % (
        len(b), b.study.str.split(",| ").str[0].nunique()), transform=bx.transAxes, fontsize=5.0, va="top")
    boxed(bx)
    pg.letter("b", 96, 129)
    pg.title("Like-for-like cost, each study's own inputs", 108, 129)
    # c: PF plant metrics, model / reference as a deviation from 1
    cx = pg.ax(14, 12, 70, 44)
    m = len(c)
    yc = np.arange(m)[::-1].astype(float)
    cols = [RED if abs(v - 1) > 0.1 else PALE_B for v in c.ratio]
    cx.barh(yc - 0.1, c.ratio - 1.0, 0.44, left=1.0, color=cols, ec=INK, lw=0.35)
    cx.axvline(1.0, color=INK, lw=0.6)
    for yi, r in zip(yc, c.itertuples()):
        cx.text(0.615, yi + 0.16, r.metric, fontsize=5.2, ha="left", va="bottom")
        cx.text(max(1.0, r.ratio) + 0.02, yi - 0.1, ("%.3g / %.3g (×%.2f)" % (r.model, r.reference, r.ratio)),
                va="center", fontsize=5.0)
    cx.set_yticks([])
    cx.set_ylim(-0.5, m - 0.38)
    cx.set_xlim(0.6, 1.5)
    cx.set_xticks([0.6, 0.8, 1.0, 1.2, 1.4])
    cx.set_xlabel("model / Pérez-Fortes (red: more than 10 % apart)")
    boxed(cx)
    pg.letter("c", 2, 63)
    pg.title("Loop metrics at the Pérez-Fortes point", 14, 63)
    # d: headline across variants
    dx = pg.ax(108, 12, 70, 44)
    assert (dd.key.to_numpy() == np.arange(1, len(dd) + 1)).all()
    xs = np.arange(len(dd))
    colors = [RED if v == "baseline" else (RU if v.startswith("pf_aligned") else
                                            (FE if v.startswith("catalyst_repl_95") else PALE_B)) for v in dd.variant]
    dx.bar(xs, dd.mismatch_groups, 0.7, color=colors, ec=INK, lw=0.3)
    base_n = int(dd[dd.variant == "baseline"].mismatch_groups.iloc[0])
    dx.axhline(base_n, color=RED, lw=0.5, ls="--")
    dx.set_xticks(xs)
    dx.set_xticklabels([str(k) for k in dd.key], fontsize=5.0)
    dx.set_xlim(-0.6, len(dd) - 0.4)
    ngr = int(dd.groups.max())
    top = 5 * np.ceil(1.45 * dd.mismatch_groups.max() / 5)
    dx.set_ylim(0, top)
    dx.set_ylabel("comparisons with a different winner (of %d)" % ngr)
    dx.set_xlabel("plant-model variant (key in Source Data)")
    dx.text(0.02, 0.97, "red: model as used (%d); green: catalyst 95.24 EUR kg$^{-1}$, 1/4/6 y\n"
            "dark: recycle, compression, capital set to Pérez-Fortes" % base_n,
            transform=dx.transAxes, fontsize=5.0, va="top")
    for x, v in zip(xs, dd.mismatch_groups):
        dx.text(x, v + 0.3, str(v), ha="center", va="bottom", fontsize=5.0)
    boxed(dx)
    pg.letter("d", 96, 63)
    pg.title("Headline under %d plant-model variants" % len(dd), 108, 63)
    return pg


# ---------------------------------------------------------------------------------------------- ED Fig. 7
def ed7():
    d, fe = E.edfig7()
    a, b, c = (d[k][0] for k in "abc")
    pg = Page(183.0, 120.0)
    # shared grid: left column axes 14-84 mm, right column 108-178 mm; panel c spans 14-178 mm
    ax = pg.ax(14, 70, 70, 40)
    ev = a.evaluated_recycled_opt
    for m, col, lab, z in ((~ev, OTHER, "excluded by the bound (%d)" % (~ev).sum(), 2),
                           (ev, RU, "evaluated in full (%d)" % ev.sum(), 3)):
        ax.scatter(a.cost_recycled_opt[m], a.bound[m], s=4, c=col, ec=INK, lw=0.2, zorder=z, label=lab)
    lim = (min(a.bound.min(), a.cost_recycled_opt.min()) * 0.95,
           max(a.bound.max(), a.cost_recycled_opt.max()) * 1.05)
    ax.plot(lim, lim, color=INK, lw=0.5)
    ax.set_xlim(lim)
    ax.set_ylim(lim)
    ax.set_xscale("log")
    ax.set_yscale("log")
    for axis in (ax.xaxis, ax.yaxis):
        axis.set_minor_formatter(NullFormatter())
    ax.set_xticks([1000, 10000, 100000])
    ax.set_xticklabels(["10$^3$", "10$^4$", "10$^5$"])
    ax.set_yticks([1000, 10000, 100000])
    ax.set_yticklabels(["10$^3$", "10$^4$", "10$^5$"])
    ax.set_xlabel("full plant cost, recycled CO (EUR t$^{-1}$)")
    ax.set_ylabel("lower bound (EUR t$^{-1}$)")
    ax.legend(loc="upper left", fontsize=5.0, borderaxespad=0.3, handletextpad=0.2)
    boxed(ax)
    pg.letter("a", 2, 117)
    pg.title("Methanol: %d literature candidates, %d groups" % (len(a), a.group.nunique()), 14, 117)
    bx = pg.ax(108, 70, 70, 40)
    fb = b[b.feasible]
    for m, col, lab, z in ((fb.pruned, OTHER, "excluded by the bound (%d)" % fb.pruned.sum(), 2),
                           (~fb.pruned, RU, "optimized in full (%d)" % (~fb.pruned).sum(), 3)):
        bx.scatter(fb.cost_USD_t[m], fb.lower_bound_USD_t[m], s=4, c=col, ec=INK, lw=0.2, zorder=z, label=lab)
    lim = (8, 2e4)
    bx.plot(lim, lim, color=INK, lw=0.5)
    bx.axhline(fe, color=DARK_G, lw=0.6, ls="--")
    bx.axvline(fe, color=DARK_G, lw=0.6, ls="--")
    bx.text(fe * 1.1, 3000, "Fe %.2f" % fe, color=DARK_G, fontsize=5.2, va="top")
    bx.set_xscale("log")
    bx.set_yscale("log")
    bx.set_xlim(lim)
    bx.set_ylim(lim)
    bx.set_xlabel("full plant cost (USD t$^{-1}$ NH$_3$)")
    bx.set_ylabel("lower bound (USD t$^{-1}$)")
    bx.legend(loc="lower right", fontsize=5.0, borderaxespad=0.3, handletextpad=0.2)
    n_pure = int(sum(len(E._els(x)) == 1 for x in fb.surface))
    # above the diagonal is empty by construction (bound <= cost): the note goes there, right of the Fe line
    bx.text(0.17, 0.96, "%d surfaces inside the bed cap shown\n(%d bimetallic, %d pure metal; of %s costed)"
            % (len(fb), len(fb) - n_pure, n_pure, format(len(b), ",")), transform=bx.transAxes, fontsize=5.0,
            va="top", ha="left")
    boxed(bx)
    pg.letter("b", 96, 117)
    pg.title("Ammonia alloy and metal surfaces", 108, 117)
    # c: share of the candidates evaluated in full; labels above the bars, counts inside the segments, so the
    # axes span exactly the data range (0-100 %) and the full width of panels a and b
    cx = pg.ax(14, 10, 164, 34)
    nc = len(c)
    yc = np.arange(nc)[::-1].astype(float)
    full = (c.full_evaluations / c.candidates).to_numpy()
    cx.barh(yc - 0.1, full, 0.42, color=RU, ec=INK, lw=0.35)
    cx.barh(yc - 0.1, 1.0 - full, 0.42, left=full, color=PALE_B, ec=INK, lw=0.35)
    for yi, r, f in zip(yc, c.itertuples(), full):
        cx.text(0.004, yi + 0.17, "%s, %s candidates" % (r.system, format(int(r.candidates), ",")), fontsize=5.6,
                ha="left", va="bottom")
        cx.text(f / 2, yi - 0.1, "%s evaluated in full" % format(int(r.full_evaluations), ","), fontsize=5.2,
                ha="center", va="center", color="white")
        cx.text(f + (1 - f) / 2, yi - 0.1, "%s excluded by the bound (%.1f %%)" % (
            format(int(r.excluded_by_bound), ","), 100 * r.excluded_by_bound / r.candidates), fontsize=5.2,
            ha="center", va="center", color=INK)
    cx.set_yticks([])
    cx.set_ylim(-0.45, nc - 0.4)
    cx.set_xlim(-0.012, 1.012)            # a hairline of air between the 0 and 100 % bar ends and the frame
    cx.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
    cx.set_xticklabels(["0", "25", "50", "75", "100"])
    cx.set_xlabel("share of candidates (%)")
    boxed(cx)
    pg.letter("c", 2, 51)
    pg.title("Full optimizations saved by the lower bound; plant-cost leaders or sub-Fe surfaces excluded: %d"
             % int(c.leader_missed.sum()), 14, 51)
    return pg


# ---------------------------------------------------------------------------------------------- ED Fig. 8
TREAT_COL = {"canonical": RU, "extended": PALE_B, "limit_published_max": PALE_G, "limit_anchor": FE,
             "limit_published_min": DARK_G}
TREAT_TICK = {"canonical": "S5\n0.5–40 %", "extended": "S5\nfrom 10$^{-4}$ %", "limit_published_max": "inlet\n≤ %.2f %%",
              "limit_anchor": "inlet\n≤ %.2f %%", "limit_published_min": "inlet\n≤ %.2f %%"}


def _purge_axis(ax):
    ax.set_xscale("log")
    ax.set_xlim(1e-4, 40)
    ax.set_xticks([1e-4, 1e-3, 1e-2, 0.1, 0.5, 2, 10, 40])
    ax.set_xticklabels(["10$^{-4}$", "10$^{-3}$", "0.01", "0.1", "0.5", "2", "10", "40"])
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.set_xlabel("purge (% of the loop gas)")


def _strip(ax, c, col, keys, rng):
    for x, k in enumerate(keys):
        v = c.loc[c.key == k, col].to_numpy(float)
        v = v[np.isfinite(v)]
        ax.scatter(x + rng.uniform(-0.28, 0.28, len(v)), v, s=1.6, c=TREAT_COL[k], ec=INK, lw=0.12, zorder=2)
        med = float(np.median(v))
        ax.plot([x - 0.36, x + 0.36], [med, med], color=INK, lw=0.9, zorder=3)
    ax.set_xlim(-0.6, len(keys) - 0.4)
    ax.set_yscale("log")


def ed8():
    d = E.edfig8()
    a, b, c, dd, e, f = (d[k][0] for k in "abcdef")
    keys = list(e.key)
    lim = {"limit_published_min": b.attrs["published"][0], "limit_anchor": b.attrs["anchor"],
           "limit_published_max": b.attrs["published"][1]}
    ticks = [TREAT_TICK[k] % (100 * lim[k]) if k in lim else TREAT_TICK[k] for k in keys]
    floor = 100 * a.attrs["purge_floor"]
    opt = c[c.key == "extended"]
    pg = Page(183.0, 178.0)
    # a cost along the purge grid, relative to the cost at the lowest level of the canonical grid
    ax = pg.ax(14, 128, 70, 40)
    ax.axvspan(floor, 40, color=TINT_B, lw=0, zorder=0)
    for _, g in a.groupby("i"):
        ax.plot(g.purge * 100, g.cost_rel_0p5pct, color=RU, lw=0.25, alpha=0.2, zorder=1)
    med = a.groupby("purge").cost_rel_0p5pct.median()
    ax.plot(med.index * 100, med.values, color=INK, lw=1.0, zorder=3, label="median of %d entries" % a.i.nunique())
    ax.scatter(opt.purge * 100, opt.cost_rel_0p5pct, s=2.0, c=DARK_B, lw=0, zorder=4, label="optimum, extended grid")
    ax.axvline(floor, color=RED, lw=0.7, ls="--", zorder=4)
    _purge_axis(ax)
    ax.set_yscale("log")
    ax.set_ylim(0.05, 5)
    ax.set_yticks([0.05, 0.1, 0.2, 0.5, 1, 2, 5])
    ax.set_yticklabels(["0.05", "0.1", "0.2", "0.5", "1", "2", "5"])
    ax.yaxis.set_minor_formatter(NullFormatter())
    ax.set_ylabel("cost / cost at %.1f %% purge" % floor)
    below = int((opt.purge < a.attrs["purge_floor"] - 1e-12).sum())
    ax.text(floor * 1.15, 0.062, "S5 grid\n(0.5–40 %)", color=RED, fontsize=5.0, va="bottom")
    ax.text(0.03, 0.04, "optimum below %.1f %%: %d of %d entries\nmedian optimum %.3f %% purge" % (
        floor, below, len(opt), 100 * float(np.median(opt.purge))), transform=ax.transAxes, fontsize=5.0,
        va="bottom")
    ax.legend(loc="upper left", fontsize=5.0, borderaxespad=0.3, handlelength=1.4, markerscale=2.5)
    boxed(ax)
    pg.letter("a", 2, 175)
    pg.title("Cost along the purge grid, every scored entry", 14, 175)
    # b reactor-inlet content of species other than H2 and CO2
    bx = pg.ax(108, 128, 70, 40)
    lo, hi, nlit = b.attrs["published"]
    bx.axhspan(100 * lo, 100 * hi, color=PALE_G, alpha=0.6, lw=0, zorder=0)
    for _, g in b.groupby("i"):
        bx.plot(g.purge * 100, g.nonreactive * 100, color=RU, lw=0.25, alpha=0.2, zorder=1)
    mb = b.groupby("purge").nonreactive.median()
    bx.plot(mb.index * 100, mb.values * 100, color=INK, lw=1.0, zorder=3)
    bx.scatter(opt.purge * 100, opt.nonreactive * 100, s=2.0, c=DARK_B, lw=0, zorder=4)
    bx.axvline(floor, color=RED, lw=0.7, ls="--", zorder=4)
    bx.axhline(100 * b.attrs["anchor"], color=DARK_G, lw=0.6, ls="--", zorder=2)
    _purge_axis(bx)
    bx.set_ylim(0, 100)
    bx.set_ylabel("reactor inlet, not H$_2$ or CO$_2$ (mol%)")
    # just above the band at the lowest purges, where the curves sit near 100 % and the optima do not reach
    bx.text(1.3e-4, 100 * hi + 0.8, "shaded: %d published\nloop designs, %.2f–%.2f %%\ndashed: anchor loop %.2f %%" % (
        nlit, 100 * lo, 100 * hi, 100 * b.attrs["anchor"]), fontsize=5.0, ha="left", va="bottom", color=DARK_G)
    boxed(bx)
    pg.letter("b", 96, 175)
    pg.title("Reactor-inlet content other than H$_2$ and CO$_2$", 108, 175)
    # c optimal purge per treatment
    rng = np.random.default_rng(8)
    cx = pg.ax(14, 70, 70, 40)
    _strip(cx, c.assign(purge=c.purge * 100), "purge", keys, rng)
    cx.axhline(floor, color=RED, lw=0.6, ls="--", zorder=1)
    cx.set_ylim(1e-4, 40)
    cx.set_yticks([1e-4, 1e-3, 1e-2, 0.1, 0.5, 2, 10, 40])
    cx.set_yticklabels(["10$^{-4}$", "10$^{-3}$", "0.01", "0.1", "0.5", "2", "10", "40"])
    cx.yaxis.set_minor_formatter(NullFormatter())
    cx.set_xticks(range(len(keys)))
    cx.set_xticklabels(ticks, fontsize=5.4)
    cx.set_ylabel("optimal purge (%)")
    boxed(cx)
    pg.letter("c", 2, 117)
    pg.title("Optimal purge (bars: median)", 14, 117)
    # d recycle ratio at the optimum
    dx = pg.ax(108, 70, 70, 40)
    _strip(dx, dd, "recycle_ratio", keys, rng)
    ar = dd.attrs["anchor_recycle_ratio"]
    dx.axhline(ar, color=DARK_G, lw=0.6, ls="--", zorder=1)
    dx.text(-0.5, ar * 0.85, "anchor loop %.2f" % ar, color=DARK_G, fontsize=5.0, ha="left", va="top")
    dx.set_ylim(0.5, 1e4)
    dx.set_yticks([1, 10, 100, 1000, 10000])
    dx.set_yticklabels(["1", "10", "100", "1,000", "10,000"])
    dx.yaxis.set_minor_formatter(NullFormatter())
    dx.set_xticks(range(len(keys)))
    dx.set_xticklabels(ticks, fontsize=5.4)
    dx.set_ylabel("recycle / fresh make-up (molar)")
    boxed(dx)
    pg.letter("d", 96, 117)
    pg.title("Recycle ratio at the optimum (bars: median)", 108, 117)
    # e comparisons with a different winner
    ex = pg.ax(14, 12, 70, 40)
    y = np.arange(len(e))[::-1].astype(float)
    ng = int(e.groups.max())
    ex.barh(y - 0.12, e.different_winner, 0.4, color=[TREAT_COL[k] for k in e.key], ec=INK, lw=0.35)
    ex.barh(y - 0.12, e.regret_gt5pct, 0.4, color="none", ec=INK, lw=0.35, hatch="//////")
    for yi, r in zip(y, e.itertuples()):
        ex.text(0.3, yi + 0.13, r.treatment, fontsize=5.0, ha="left", va="bottom")
        ex.text(r.different_winner + 0.6, yi - 0.12, "%d / %d (%d > 5 %%)" % (r.different_winner, r.groups,
                                                                            r.regret_gt5pct),
                fontsize=5.0, va="center")
    ex.set_yticks([])
    ex.set_ylim(-0.55, len(e) - 0.3)
    ex.set_xlim(0, ng)
    ex.set_xticks(range(0, ng + 1, 10))
    ex.set_xlabel("comparisons, STY leader ≠ plant-cost leader (of %d)" % ng)
    boxed(ex)
    pg.letter("e", 2, 59)
    pg.title("Comparisons with a different winner (hatched: regret > 5 %)", 14, 59)
    # f mean inlet CO, CH4, N2 at the optimum
    fx = pg.ax(108, 12, 70, 40)
    fx.axvspan(100 * lo, 100 * hi, color=PALE_G, alpha=0.6, lw=0, zorder=0)
    left = np.zeros(len(f))
    for sp, colr in (("CO", OS), ("CH4", OTHER), ("N2", PALE_B)):
        fx.barh(y - 0.12, 100 * f[sp], 0.4, left=left, color=colr, ec=INK, lw=0.35, zorder=2,
                label={"CO": "CO", "CH4": "CH$_4$", "N2": "N$_2$"}[sp])
        left += 100 * f[sp].to_numpy()
    for yi, r in zip(y, f.itertuples()):
        fx.text(0.4, yi + 0.13, r.treatment, fontsize=5.0, ha="left", va="bottom")
        fx.text(100 * r.nonreactive + 0.8, yi - 0.12, "%.1f %%" % (100 * r.nonreactive), fontsize=5.0, va="center")
    fx.set_yticks([])
    fx.set_ylim(-0.55, len(f) - 0.3)
    fx.set_xlim(0, 50)
    fx.set_xlabel("reactor inlet (mol%, mean over the scored entries)")
    h, lab = fx.get_legend_handles_labels()
    h.append(Patch(color=PALE_G, alpha=0.6, lw=0))
    lab.append("published designs")
    fx.legend(h, lab, loc="lower right", fontsize=5.0, borderaxespad=0.3, handlelength=1.2, ncol=2)
    boxed(fx)
    pg.letter("f", 96, 59)
    pg.title("Reactor-inlet CO, CH$_4$ and N$_2$ at the optimum", 108, 59)
    return pg


FIGS = {1: ed1, 2: ed7, 3: ed3, 4: ed6, 5: ed4, 6: ed2, 7: ed5, 8: ed8}


# ---------------------------------------------------------------------------------------------- captions
def _p(x, d=1):
    return ("%%.%df" % d) % (100 * x)


def write_captions():
    """ED_CAPTIONS.md: every number below is read from the same panel tables the figures are drawn from."""
    out = ["# Extended Data figure captions", "",
           "Generated by `render_extended_data.py` from the panel tables of `ed_data.py`; numbers are read from the "
           "source files named in each caption. Source Data: `source_data/SourceData_EDFig{N}.xlsx`.", ""]

    d = E.edfig1()
    a, b = d["a"][0], d["b"][0]
    tot = b.set_index("reference_set")
    rng = lambda s: "%d–%d" % (s.min(), s.max())  # noqa: E731
    pl = a[a.source_type == "plot"].set_index("field")
    tb = a[a.source_type == "table"].set_index("field")
    out += ["## Extended Data Fig. 1 | Accuracy of the extraction agent on the methanol literature", "",
            "**a**, Strict accuracy of the extracted CO$_2$ conversion (X), methanol selectivity (S$_{MeOH}$) and "
            "space-time yield (STY) against the curated values, by where the value is printed (main-text tables, SI "
            "tables, main-text plots, SI plots); labels give correct / extracted values (n = %s per bar). Values printed "
            "in tables are reproduced at %s–%s %%; values read from plots at %s %% (X), %s %% (S$_{MeOH}$) and %s %% "
            "(STY) in the main text. **b**, Recall of curated entries per reference set: TheMeCat %d / %d, Suvarna "
            "%d / %d, all %d / %d (%s %%). Source: `%s` and `%s` (rows TOTAL)." % (
                rng(a.n_extracted), _p(a[a.source_type.isin(["table", "SI"])].acc_strict.min()),
                _p(a[a.source_type.isin(["table", "SI"])].acc_strict.max()),
                _p(pl.loc["X_CO2", "acc_strict"]), _p(pl.loc["S_MeOH", "acc_strict"]), _p(pl.loc["STY", "acc_strict"]),
                tot.loc["TheMeCat", "matched"], tot.loc["TheMeCat", "curated"], tot.loc["Suvarna", "matched"],
                tot.loc["Suvarna", "curated"], tot.loc["all", "matched"], tot.loc["all", "curated"],
                _p(tot.loc["all", "recall"]), E.EXTRACT_ACC, E.EXTRACT_ENT), ""]
    del tb

    d, fe = E.edfig2()
    n = {p: len(d[p][0]) for p in "abc"}
    nb = {p: int(d[p][0].below_Fe.sum()) for p in "abc"}
    fam = d["a"][0]
    out += ["## Extended Data Fig. 6 | Bimetallic surfaces through the ammonia chain, by element layer", "",
            "Plant cost (no metal recovery, cost optimum inside the 90 m$^3$ bed cap) against log$_{10}$ TOF at 673 K "
            "for the Mamun et al. (2019) bimetallic surfaces whose optimum fits the bed cap (global descriptor route). "
            "**a**, Transition metals only: %d surfaces, %d below the Fe benchmark (%.2f USD t$^{-1}$, dashed), all of "
            "them one cheap 3d metal (Fe, Co, Ni, Cu) with Cr, Mo or W (green, %d surfaces of that family). **b**, "
            "Adding surfaces with group 3–5 elements: %d surfaces, %d below Fe. **c**, Adding surfaces with sp metals: "
            "%d surfaces, %d below Fe. Surfaces with sp metals lie outside the transition-metal scaling relations of "
            "the activity model, and group 3–5 elements form stable bulk nitrides; both layers are shown separately. "
            "Source: `%s`." % (n["a"], nb["a"], fe, int(fam.family_3d_group6.sum()), n["b"], nb["b"], n["c"], nb["c"],
                                 E.ALLOY), ""]
    assert set(fam[fam.below_Fe].family_3d_group6) == {True}

    d = E.edfig3()
    a, b, c, dd = (d[k][0] for k in "abcd")
    e = d["e"][0]
    cc = c.set_index("scenario")
    bc = b.set_index("threshold")
    st = E.rjson(E.STATS + "summary.json")
    out += ["## Extended Data Fig. 3 | Robustness of the methanol leader changes", "",
            "**a**, Share of the %d published comparisons whose STY leader is not the "
            "plant-cost leader, over %s paper-cluster bootstrap resamples of the %d papers: "
            "observed %s %%, 95 %% CI %s–%s %%. **b**, Mismatched "
            "comparisons whose regret (cost penalty of building the STY leader) is at least the threshold: %d at 0, "
            "%d at 1 %% (%d papers), %d at 5 %%, %d at 10 %%. **c**, Mean and 95 %% range over %s draws of the number "
            "of mismatched comparisons when every entry is re-measured with the error the papers' own data imply (×1, "
            "×2, ×4; circles), against the noise floor, the number of comparisons whose reported STY leader changes "
            "under re-measurement alone (squares): ×1 %.1f (%d–%d) against a floor of %.1f (%d–%d); dashed, observed "
            "%d. **d**, Share of draws in which each observed mismatch persists at ×1; %d of %d persist in at least "
            "90 %% of draws. Source: `%s`." % (
                st["groups"], format(a.attrs["n"], ","), st["papers"], _p(a.attrs["point"]), _p(a.attrs["ci"][0]),
                _p(a.attrs["ci"][1]), bc.loc[0.0, "groups"], bc.loc[0.01, "groups"], bc.loc[0.01, "papers"], bc.loc[0.05, "groups"],
                bc.loc[0.1, "groups"], format(c.attrs["draws"], ","),
                cc.loc["meas_k1", "mismatch_groups_mean"], cc.loc["meas_k1", "mismatch_groups_q025"],
                cc.loc["meas_k1", "mismatch_groups_q975"], cc.loc["meas_k1", "noise_floor_mean"],
                cc.loc["meas_k1", "noise_floor_q025"], cc.loc["meas_k1", "noise_floor_q975"], c.attrs["observed"],
                int((dd.p_mismatch_meas_k1 >= 0.9).sum()), len(dd), E.STATS)]
    fin = e[np.isfinite(e.limit)]
    span = fin[(fin.limit >= 0.05 - 1e-9) & (fin.limit <= 0.10 + 1e-9)]
    nl = e[~np.isfinite(e.limit)].iloc[0]
    ref = e[np.isclose(e.limit, e.attrs["reference"])].iloc[0]
    lit = e.attrs.get("literature")
    out[-1] = out[-1].replace(" Source: `%s`." % E.STATS, "")
    out[-1] += (" **e**, Share of comparisons whose STY leader is not the plant-cost leader against the limit on the "
                "reactor-inlet content of species other than H$_2$ and CO$_2$ (all comparisons, circles; isothermal "
                "comparisons of at least two catalysts, squares; right edge, no limit). Dashed, the calibrated reference "
                "loop (%s %%): %d / %d (%s %%) and %d / %d (%s %%). Shaded, the reactor inlets of %d published "
                "CO$_2$-to-methanol loop designs (%.1f–%.1f %%). Between 5 %% and 10 %%: %s–%s %% and %s–%s %%; no limit: "
                "%s %% and %s %%. Source: `%s`; `%s` (summary.json limit_sweep, isothermal; inlet_inert_literature.csv)."
                % (_p(e.attrs["reference"], 2), ref.mismatched, ref.groups, _p(ref.share), ref.iso_mismatched,
                   ref.iso_groups, _p(ref.iso_share), lit[2], 100 * lit[0], 100 * lit[1],
                   _p(min(span.share.min(), ref.share)), _p(max(span.share.max(), ref.share)),
                   _p(min(span.iso_share.min(), ref.iso_share)), _p(max(span.iso_share.max(), ref.iso_share)),
                   _p(nl.share), _p(nl.iso_share), E.STATS, E.INV))
    out += [""]

    d = E.edfig4()
    t, bm = d["a"][0], d["b"][0].set_index("metal")
    ov = t.attrs["overall"]
    out += ["## Extended Data Fig. 5 | Measured ammonia catalysts through the plant chain", "",
            "**a**, Plant cost (no metal recovery) against the laboratory rate per gram of metal for the %d primary "
            "catalysts of the Humphreys et al. (2021) review (%s); dashed, Fe benchmark %.2f USD t$^{-1}$. The highest "
            "rate (%s, %.2f USD t$^{-1}$, red) and the plant-cost leader (%s, %.2f USD t$^{-1}$) differ; regret %s %%. "
            "**b**, Plant cost by metal; bars mark the lowest cost per metal (%s). Fused-iron catalysts carry 71.51 "
            "wt%% Fe. Source: `%s`." % (
                len(t), ", ".join("%d %s" % (bm.loc[m, "catalysts"], m) for m in bm.index), t.attrs["fe"],
                ov["rate_leader"], ov["rate_leader_cost"], ov["plant_leader"], ov["plant_leader_cost"],
                _p(ov["regret"]), ", ".join("%s %.2f" % (m, bm.loc[m, "lowest_cost_USD_t"]) for m in bm.index),
                E.SUP + "supported_candidates.csv"), ""]

    d = E.edfig5()
    a, b, c, dd = (d[k][0] for k in "abcd")
    out += ["## Extended Data Fig. 7 | Fe against the actual Ru catalyst", "",
            "**a**, Probability that Fe is cheaper than Ru over %s joint draws (price multipliers, CAPEX, electricity, "
            "catalyst life), with the median Ru − Fe cost: %s. A: dispersion ratio u = D$_{Ru}$/f$_{Fe}$ (log-uniform "
            "%g–%g) and Ru recovery r (%g–%g) lower the Ru price to p(1 − r)/u in the benchmark bed (the Fig. 3d reading); "
            "A_bed: the Ru inventory divided by u and charged at (1 − r), in the commercial Ru/C bed (Ru content "
            "%g–%g wt%%, bed density %g–%g kg m$^{-3}$); B and B0: one measured Ru "
            "catalyst per draw, with and without recovery. **b–d**, Probability that Ru is cheaper (A_bed, circles or "
            "dark bars; A, squares or light bars) by u (**b**), r (**c**) and the Ru content of the bed (**d**, n = "
            "draws per bin). Source: `%s`." % (
                format(int(a.draws.iloc[0]), ","),
                "; ".join("%s %.3f (%+.2f USD t$^{-1}$)" % (r.treatment.split(":")[0].split(" (")[0], r.P_Fe_cheaper,
                                                          r.median_Ru_minus_Fe_USD_t) for r in a.itertuples()),
                b.u_low.min(), b.u_high.max(), c.r_low.min(), c.r_high.max(), dd.Ru_wt_pct_low.min(),
                dd.Ru_wt_pct_high.max(), *E.rjson(E.MC + "summary.json")["ranges"]["bed_density_kg_m3"],
                E.MC + "draws.csv, summary.json"), ""]

    d = E.edfig6()
    a, b, c, dd = (d[k][0] for k in "abcd")
    pf = b[b.study.str.startswith("Perez")].iloc[0]
    rest = b[~b.study.str.startswith("Campos")]
    base = int(dd[dd.variant == "baseline"].mismatch_groups.iloc[0])
    cat = dd[dd.variant.str.startswith("catalyst_repl_95")].set_index("variant").mismatch_groups
    ta = a.set_index("category")
    sub, tot = ta.loc["subtotal"], ta.loc["total"]
    stoich = ta.loc["catalyst-independent"]
    sens = a[a.category == "catalyst-sensitive"]
    fom = ta.loc["accounting"]
    pf_aligned = dd[dd.variant == "pf_aligned_recycle_compression_capital"].mismatch_groups.iloc[0]
    out += ["## Extended Data Fig. 4 | The methanol plant model against published plants", "",
            "**a**, The Pérez-Fortes et al. (2016) plant run at its own operating point, prices, catalyst charge and "
            "finance, term by term (model / reference, EUR t$^{-1}$). The stoichiometric H$_2$ and CO$_2$ demand "
            "(%.1f / %.1f) does not depend on the catalyst. The catalyst-sensitive terms (feed above stoichiometry, "
            "electricity, catalyst replacement, capital) sum to %.1f / %.1f (%+.1f %%): feed %+.1f %%, electricity "
            "%+.1f %%, catalyst %+.1f %%, capital %+.1f %%. Fixed operation and maintenance is the reference value on "
            "both sides (%.2f). Total, against the reference break-even price (NPV = 0): %.1f / %.1f (%+.1f %%). "
            "**b**, Like-for-like cost against each study's reported production cost or break-even price at that "
            "study's own inputs (%d cases; band ±5 %%; green, the Campos anchor); deviations of the non-anchor cases "
            "%+.1f to %+.1f %%. **c**, Loop metrics at the Pérez-Fortes operating point, model / reference (%s; red, "
            "more than 10 %% apart). **d**, Number of the %d comparisons whose STY leader is not the plant-cost leader "
            "under %d plant-model variants (keys in Source Data): model as used %d; catalyst replacement at 95.24 "
            "EUR kg$^{-1}$ every 6, 4 and 1 y gives %d, %d and %d; recycle, compression and capital set to "
            "Pérez-Fortes gives %d. Source: `%s`." % (
                stoich.model, stoich.reference, sub.model, sub.reference, sub.deviation_pct,
                *sens.deviation_pct.iloc[:4], fom.model, tot.model, tot.reference, tot.deviation_pct, len(b),
                rest.deviation_pct.min(), rest.deviation_pct.max(),
                "; ".join("%s %.2f" % (r.metric.replace("$_2$", "2"), r.ratio) for r in c.itertuples()),
                E.rjson(E.STATS + "summary.json")["groups"], len(dd), base,
                cat["catalyst_repl_95.24EURkg_6y"], cat["catalyst_repl_95.24EURkg_4y"],
                cat["catalyst_repl_95.24EURkg_1y"], pf_aligned, E.BENCH), ""]

    d = E.edfig8()
    e8, f8 = d["e"][0].set_index("key"), d["f"][0].set_index("key")
    pb = E.rjson(E.INV + "purge_boundary_summary.json")
    bd, ext = pb["boundary"], pb["boundary"]["at_extended_optimum"]
    lim = pb["limits"]
    n_pub = d["b"][0].attrs["published"][2]
    row = lambda k: "%d / %d (%d with regret > 5 %%)" % (e8.loc[k, "different_winner"], e8.loc[k, "groups"],  # noqa: E731
                                                       e8.loc[k, "regret_gt5pct"])
    lab = [("canonical", "frozen grid"), ("extended", "extended grid"),
           ("limit_published_max", "≤ %.2f %%" % (100 * lim["published_max"])),
           ("limit_anchor", "≤ %.2f %%" % (100 * lim["anchor"])),
           ("limit_published_min", "≤ %.2f %%" % (100 * lim["published_min"]))]
    out += ["## Extended Data Fig. 8 | Purge boundary and inlet-constrained methanol loops", "",
            "**a**, Net production cost along the purge grid for each of the %d scored methanol entries (S5 model), "
            "relative to the cost at 0.5 %% purge, the floor of the frozen grid (0.5–40 %%, dashed); the grid is "
            "extended to 10$^{-4}$ %% (black, median; dots, optimum). The optimum lies below 0.5 %% for %d of %d "
            "entries (median optimum %.3f %% purge); at 0.5 %% the cost is a median %s %% above it. **b**, "
            "Reactor-inlet content of species other than H$_2$ and CO$_2$ along the same grid; shaded, the inlets of "
            "%d published CO$_2$-to-methanol loop designs (%.2f–%.2f %%); dashed, the anchor loop of the cost model "
            "(%s %%). **c**, Optimal purge and **d**, recycle ratio (recycle / fresh make-up, molar; dashed, anchor "
            "loop %.2f) for the frozen grid, the extended grid (median recycle ratio %.0f) and with the inlet content "
            "limited to %.2f, %.2f and %.2f %% on the extended grid (bars, median). **e**, Comparisons whose STY "
            "leader is not the plant-cost leader: %s. **f**, Reactor-inlet CO, CH$_4$ and N$_2$ at each optimum, "
            "mean over the scored entries (total: %s). Source: `%s` (purge_boundary_summary.json, "
            "purge_boundary_entries.csv, purge_boundary_curves.csv)." % (
                pb["entries"], bd["extended_optimum_below_0p5pct"], pb["entries"], 100 * ext["purge"]["median"],
                _p(bd["cost_at_0p5pct_above_extended_optimum"]["median"]), n_pub,
                100 * lim["published_min"], 100 * lim["published_max"], _p(lim["anchor"], 2),
                pb["anchor_loop"]["recycle_ratio"], ext["recycle_ratio"]["median"], 100 * lim["published_max"],
                100 * lim["anchor"], 100 * lim["published_min"],
                "; ".join("%s %s" % (t, row(k)) for k, t in lab),
                "; ".join("%s %s %%" % (t, _p(f8.loc[k, "nonreactive"])) for k, t in lab), E.INV), ""]

    d, fe = E.edfig7()
    a, b, c = (d[k][0] for k in "abc")
    cr = c.set_index("system")
    out += ["## Extended Data Fig. 2 | Full optimizations saved by the closed-form lower bound", "",
            "**a**, Lower bound against the full plant cost (recycled CO) for the %d methanol literature candidates "
            "in %d comparison groups; every bound lies below its full cost. Agent rule per group: evaluate the paper's "
            "leader in full, then the others in increasing bound order until the next bound exceeds the best full "
            "cost; %d candidates are evaluated in full (blue), %d are excluded. **b**, The same for the %d ammonia "
            "surfaces inside the bed cap (%d bimetallic, %d pure metals; of %d costed); a surface is excluded when its bound exceeds the Fe "
            "benchmark (%.2f USD t$^{-1}$, dashed). **c**, Share of candidates evaluated in full: %s. No plant-cost "
            "leader and no surface below Fe is excluded. Source: `%s`, `%s`." % (
                len(a), a.group.nunique(), int(a.evaluated_recycled_opt.sum()), int((~a.evaluated_recycled_opt).sum()),
                int(b.feasible.sum()), int((b.feasible & b.surface.str.count(r"[A-Z]").gt(1)).sum()),
                int((b.feasible & b.surface.str.count(r"[A-Z]").eq(1)).sum()), len(b), fe,
                "; ".join("%s %d / %d (%s %% excluded)" % (s, r.full_evaluations, r.candidates,
                                                          _p(r.excluded_by_bound / r.candidates))
                          for s, r in cr.iterrows()), E.PRUNE + "candidate_bounds.csv", E.ALLOY), ""]
    assert int(cr.leader_missed.sum()) == 0
    # infeasible candidates (NaN cost) are in no leaderboard; the bound must hold for every feasible one
    for col in ("cost_recycled_opt", "cost_inert_opt"):
        fin = np.isfinite(a[col])
        assert (a.bound[fin] <= a[col][fin] * (1 + 5e-6)).all(), col
    head, *blocks = "\n".join(out).split("\n## Extended Data Fig. ")
    blocks.sort(key=lambda b: int(b.split(" ", 1)[0]))
    text = re.sub(r"(?<=[\s(])-(?=\d)", "−", "\n## Extended Data Fig. ".join([head] + blocks))
    open(os.path.join(HERE, "ED_CAPTIONS.md"), "w", encoding="utf-8").write(text)
    print("wrote ED_CAPTIONS.md")

if __name__ == "__main__":
    which = [int(x) for x in sys.argv[1:]] or sorted(FIGS)
    for n in which:
        pg = FIGS[n]()
        pg.save(HERE, "EDFig%d_%s" % (n, SLUGS[n]))
    if not sys.argv[1:]:
        write_captions()
