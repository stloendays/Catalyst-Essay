"""Extended Data figures 1-7, 183 mm wide, drawn from the panel tables of ed_data.py.

    pur_bridge_env/python render_extended_data.py          -> EDFig{N}_{slug}.{svg,pdf,png}
    pur_bridge_env/python render_extended_data.py 3 5      -> only ED Figs 3 and 5
"""
import os
import re
import sys

import numpy as np
from matplotlib.ticker import NullFormatter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "composite"))
import ed_data as E  # noqa: E402
from style import DARK_B, DARK_G, FE, INK, OTHER, PALE_B, PALE_G, RED, RU, Page, boxed  # noqa: E402

# Numbered in the order the manuscript first cites them (2026-10-07 restructure); the panel functions keep the
# names of the first numbering (ed2 = bimetallic, ed4 = measured NH3, ed5 = actual Ru, ed6 = benchmark, ed7 = pruning).
SLUGS = {1: "extraction_accuracy", 2: "bound_pruning", 3: "methanol_robustness", 4: "meoh_plant_benchmark",
         5: "nh3_measured_catalysts", 6: "bimetallic_surfaces", 7: "ru_actual_mc"}
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
        ax.axhline(fe, color=DARK_G, lw=0.7, ls="--", zorder=1)
        ax.text(xhi - 0.1, fe * 0.9, "Fe %.2f; %d below" % (fe, int(t.below_Fe.sum())), fontsize=5.2,
                color=DARK_G, va="top", ha="right")
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
    pg = Page(183.0, 174.0)
    up = 54.0                     # panels a-d sit above panel e
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
    ax.set_xlim(0.05, 0.95)
    ax.set_xticks([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9])
    ax.set_xticklabels(["10", "20", "30", "40", "50", "60", "70", "80", "90"])
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
    bx.set_ylim(0, max(40, 1.25 * float(b.groups.max())))
    bx.set_xlabel("regret at least (%)")
    bx.set_ylabel("mismatched comparisons")
    bx.text(0.97, 0.95, "labels: comparisons (papers)", transform=bx.transAxes, fontsize=5.0, ha="right", va="top")
    boxed(bx)
    pg.letter("b", 96, 117 + up)
    pg.title("Size of the disagreements", 108, 117 + up)
    # c noise scenarios
    cx = pg.ax(40, 12 + up, 46, 40)
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
    cx.set_yticklabels(c.label, fontsize=5.6)
    cx.set_ylim(-1.05, len(c) + 0.75)
    cx.set_xlim(0, max(80, 10 * np.ceil(1.15 * float(c.mismatch_groups_q975.max()) / 10)))
    cx.set_xlabel("comparisons (of %d), mean and\n95 %% range over %s draws" % (ng, format(c.attrs["draws"], ",")))
    cx.legend(loc="upper right", fontsize=5.0, borderaxespad=0.3, handletextpad=0.3)
    boxed(cx)
    pg.letter("c", 2, 59 + up)
    pg.title("Measurement and plot-reading resampling", 14, 59 + up)
    # d per-group persistence
    dx = pg.ax(108, 12 + up, 70, 40)
    xg = np.arange(len(dd)) + 1
    dx.bar(xg, dd.p_mismatch_meas_k1, 0.75, color=[RU if p >= 0.9 else PALE_B for p in dd.p_mismatch_meas_k1],
           ec=INK, lw=0.25, label="error ×1")
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
    ex = pg.ax(14, 12, 112, 40)
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
    ex.text(xmax * 100 - 0.6, nl.share + 0.05, "no limit", fontsize=5.0, ha="right")
    ref = e.attrs["reference"]
    r = e[np.isclose(e.limit, ref)].iloc[0]
    ex.axvline(ref * 100, color=RED, lw=0.7, ls="--")
    ex.text(ref * 100 + 0.4, 0.06, "reference loop %.2f %%: %d/%d (%.0f %%); isothermal %d/%d (%.0f %%)" % (
        100 * ref, r.mismatched, r.groups, 100 * r.share, r.iso_mismatched, r.iso_groups, 100 * r.iso_share),
        color=RED, fontsize=5.2, va="bottom")
    ex.set_xlim(0, xmax * 100 + 1)
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
    ax = pg.ax(62, 66, 116, 36)
    y = np.arange(len(a))[::-1]
    cols = [OTHER, PALE_B, RU, FE, FE]
    ax.barh(y, a.P_Fe_cheaper, 0.6, color=cols, ec=INK, lw=0.4)
    for yi, p, med in zip(y, a.P_Fe_cheaper, a.median_Ru_minus_Fe_USD_t):
        ax.text(p + 0.01, yi, ("%.3f   (median Ru − Fe %+.2f USD t$^{-1}$)" % (p, med)).replace("-", "−"),
                va="center", fontsize=5.4)
    ax.set_yticks(y)
    ax.set_yticklabels(a.treatment, fontsize=5.8)
    ax.set_xlim(0, 1.6)
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_xlabel("P(Fe cheaper), %s draws" % format(int(a.draws.iloc[0]), ","))
    ax.axvline(0.5, color=INK, lw=0.4, ls=":")
    boxed(ax)
    pg.letter("a", 2, 109)
    pg.title("Fe against the Ru catalyst", 14, 109)
    specs = [("b", b, "u", "dispersion ratio u = D$_{Ru}$ / f$_{Fe}$", True),
             ("c", c, "r", "Ru recovery r (%)", False),
             ("d", dd, "Ru_wt_pct", "Ru content of the bed (wt%)", False)]
    for k, (p, t, key, xl, logx) in enumerate(specs):
        bx = pg.ax(14 + k * 58, 12, 46, 36)
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
        pg.letter(p, 2 + k * 58, 55)
    pg.title("Where the Ru catalyst wins", 14, 55)
    return pg


# ---------------------------------------------------------------------------------------------- ED Fig. 6
def ed6():
    d = E.edfig6()
    a, b, c, dd = (d[k][0] for k in "abcd")
    pg = Page(183.0, 128.0)
    # a: Perez-Fortes terms
    ax = pg.ax(48, 74, 50, 44)
    short = ["H$_2$", "power + utilities", "catalyst replacement", "capital (8 %, 20 y)", "fixed O&M",
             "residual + 10 % of NPC", "break-even price, like-for-like", "total, anchor convention"]
    y = np.arange(len(a))[::-1]
    ax.barh(y + 0.19, a.model, 0.36, color=RU, ec=INK, lw=0.35, label="model")
    ax.barh(y - 0.19, a.reference, 0.36, color=PALE_B, ec=INK, lw=0.35, label="Pérez-Fortes 2016")
    for yi, m, r in zip(y, a.model, a.reference):
        ax.text(max(m, r) + 12, yi, "%.0f / %.0f" % (m, r), va="center", fontsize=5.0)
    ax.set_yticks(y)
    ax.set_yticklabels(short, fontsize=5.6)
    ax.set_xlim(0, 1080)
    ax.set_xlabel("EUR t$^{-1}$ MeOH")
    ax.legend(loc="lower right", fontsize=5.0, borderaxespad=0.3, bbox_to_anchor=(1.0, 0.28))
    boxed(ax)
    pg.letter("a", 2, 125)
    pg.title("Pérez-Fortes plant at its own assumptions", 14, 125)
    # b: parity across studies
    bx = pg.ax(118, 74, 60, 44)
    lim = (200, 1100)
    bx.fill_between(lim, [lim[0] * 0.95, lim[1] * 0.95], [lim[0] * 1.05, lim[1] * 1.05], color=PALE_G, lw=0,
                    zorder=0)
    bx.plot(lim, lim, color=INK, lw=0.5, zorder=1)
    for _, r in b.iterrows():
        col = RED if r.study.startswith("Perez") else (FE if r.study.startswith("Campos") else PALE_B)
        bx.scatter(r.reference_eur_t, r.model_eur_t, s=14, c=col, ec=INK, lw=0.35, zorder=3)
    pf = b[b.study.str.startswith("Perez")].iloc[0]
    bx.annotate(("Pérez-Fortes %+.1f %%" % pf.deviation_pct).replace("-", "−"), (pf.reference_eur_t, pf.model_eur_t), xytext=(-8, 14),
                textcoords="offset points", fontsize=5.2, color=RED, ha="right",
                arrowprops=dict(arrowstyle="-", color=RED, lw=0.5))
    bx.set_xlim(lim)
    bx.set_ylim(lim)
    bx.set_xlabel("reference cost (EUR t$^{-1}$)")
    bx.set_ylabel("model cost (EUR t$^{-1}$)")
    bx.text(0.04, 0.95, "%d cases, %d studies\nband: ±5 %%\ngreen: Campos (anchor)" % (
        len(b), b.study.str.split(",| ").str[0].nunique()), transform=bx.transAxes, fontsize=5.0, va="top")
    boxed(bx)
    pg.letter("b", 108, 125)
    pg.title("Like-for-like cost, each study's own inputs", 118, 125)
    # c: PF plant metrics
    cx = pg.ax(48, 12, 50, 44)
    y = np.arange(len(c))[::-1]
    cx.barh(y, c.ratio, 0.55, color=[RED if abs(v - 1) > 0.1 else PALE_B for v in c.ratio], ec=INK, lw=0.35)
    cx.axvline(1.0, color=INK, lw=0.6)
    for yi, r in zip(y, c.itertuples()):
        cx.text(1.27, yi, "%.3g / %.3g" % (r.model, r.reference), va="center", fontsize=5.0)
    cx.set_yticks(y)
    cx.set_yticklabels(c.metric, fontsize=5.6)
    cx.set_xlim(0.5, 1.65)
    cx.set_xticks([0.5, 0.75, 1.0, 1.25])
    cx.set_xlabel("model / Pérez-Fortes")
    cx.text(0.99, 1.01, "model / ref.", transform=cx.transAxes, fontsize=5.0, ha="right", va="bottom")
    boxed(cx)
    pg.letter("c", 2, 63)
    pg.title("Loop metrics at the Pérez-Fortes point", 14, 63)
    # d: headline across variants
    dx = pg.ax(118, 12, 60, 44)
    assert (dd.key.to_numpy() == np.arange(1, len(dd) + 1)).all()
    xs = np.arange(len(dd))
    colors = [RED if v == "baseline" else (FE if v.startswith("catalyst_repl_95") else PALE_B) for v in dd.variant]
    dx.bar(xs, dd.mismatch_groups, 0.7, color=colors, ec=INK, lw=0.3)
    base = int(dd[dd.variant == "baseline"].mismatch_groups.iloc[0])
    dx.axhline(base, color=RED, lw=0.5, ls="--")
    dx.set_xticks(xs)
    dx.set_xticklabels([str(k) for k in dd.key], fontsize=5.0)
    ngr = int(dd.groups.max())
    dx.set_ylim(0, ngr)
    dx.set_ylabel("comparisons with a different winner (of %d)" % ngr)
    dx.set_xlabel("plant-model variant (key in Source Data)")
    dx.text(0.03, 0.97, "red: model as used (%d)\ngreen: catalyst 95.24 EUR kg$^{-1}$, 1/4/6 y" % base,
            transform=dx.transAxes, fontsize=5.0, va="top", bbox=dict(fc="white", ec="none", pad=1.0))
    for x, v in zip(xs, dd.mismatch_groups):
        dx.text(x, v + 0.5, str(v), ha="center", va="bottom", fontsize=5.0, rotation=90)
    boxed(dx)
    pg.letter("d", 108, 63)
    pg.title("Headline under %d plant-model variants" % len(dd), 118, 63)
    return pg


# ---------------------------------------------------------------------------------------------- ED Fig. 7
def ed7():
    d, fe = E.edfig7()
    a, b, c = (d[k][0] for k in "abc")
    pg = Page(183.0, 120.0)
    ax = pg.ax(14, 70, 60, 40)
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
    bx.text(0.97, 0.2, "%d surfaces inside the bed cap shown (of %d costed)" % (len(fb), len(b)),
            transform=bx.transAxes, fontsize=5.0, va="bottom", ha="right")
    boxed(bx)
    pg.letter("b", 96, 117)
    pg.title("Ammonia bimetallic surfaces", 108, 117)
    cx = pg.ax(62, 12, 116, 36)
    y = np.arange(len(c))[::-1]
    cx.barh(y, c.full_evaluations / c.candidates, 0.55, color=RU, ec=INK, lw=0.35, label="evaluated in full")
    cx.barh(y, c.excluded_by_bound / c.candidates, 0.55, left=c.full_evaluations / c.candidates, color=PALE_B,
            ec=INK, lw=0.35, label="excluded by the bound")
    for yi, r in zip(y, c.itertuples()):
        cx.text(1.02, yi, "%d / %d evaluated; %d excluded (%.1f %%); leaders missed %d" % (
            r.full_evaluations, r.candidates, r.excluded_by_bound, 100 * r.excluded_by_bound / r.candidates,
            r.leader_missed), va="center", fontsize=5.2)
    cx.set_yticks(y)
    cx.set_yticklabels(c.system, fontsize=5.8)
    cx.set_xlim(0, 1.9)
    cx.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
    cx.set_xticklabels(["0", "25", "50", "75", "100"])
    cx.set_xlabel("share of candidates (%)")
    cx.legend(loc="lower right", fontsize=5.0, borderaxespad=0.2, bbox_to_anchor=(1.0, 1.0), ncol=2)
    boxed(cx)
    pg.letter("c", 2, 57)
    pg.title("Full optimizations saved", 14, 57)
    return pg


FIGS = {1: ed1, 2: ed7, 3: ed3, 4: ed6, 5: ed4, 6: ed2, 7: ed5}


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
    cc = c.set_index("scenario")
    bc = b.set_index("threshold")
    out += ["## Extended Data Fig. 3 | Robustness of the methanol leader changes", "",
            "**a**, Share of the 83 published comparisons whose STY leader is not the plant-cost leader, over %s "
            "paper-cluster bootstrap resamples of the 44 papers: observed %s %%, 95 %% CI %s–%s %%. **b**, Mismatched "
            "comparisons whose regret (cost penalty of building the STY leader) is at least the threshold: %d at 0, "
            "%d at 1 %% (%d papers), %d at 5 %%, %d at 10 %%. **c**, Mean and 95 %% range over %s draws of the number "
            "of mismatched comparisons when every entry is re-measured with the error the papers' own data imply (×1, "
            "×2, ×4) or with ×1 plus the agent's measured plot-reading errors (circles), against the noise floor, the "
            "number of comparisons whose reported STY leader changes under re-measurement alone (squares): ×1 %.1f "
            "(%d–%d) against a floor of %.1f (%d–%d); dashed, observed %d. **d**, Share of draws in which each observed "
            "mismatch persists (bars, ×1; ticks, ×1 plus plot-reading errors); %d of %d persist in at least 90 %% of "
            "draws at ×1 and %d with plot-reading errors added. Source: `%s`." % (
                format(a.attrs["n"], ","), _p(a.attrs["point"]), _p(a.attrs["ci"][0]), _p(a.attrs["ci"][1]),
                bc.loc[0.0, "groups"], bc.loc[0.01, "groups"], bc.loc[0.01, "papers"], bc.loc[0.05, "groups"],
                bc.loc[0.1, "groups"], format(c.attrs["draws"], ","),
                cc.loc["meas_k1", "mismatch_groups_mean"], cc.loc["meas_k1", "mismatch_groups_q025"],
                cc.loc["meas_k1", "mismatch_groups_q975"], cc.loc["meas_k1", "noise_floor_mean"],
                cc.loc["meas_k1", "noise_floor_q025"], cc.loc["meas_k1", "noise_floor_q975"], c.attrs["observed"],
                int((dd.p_mismatch_meas_k1 >= 0.9).sum()), len(dd),
                int((dd.p_mismatch_meas_k1_plus_extraction >= 0.9).sum()), E.STATS), ""]

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
            "A_bed: the Ru inventory divided by u and charged at (1 − r), in a bed of its own Ru content (drawn from "
            "the measured catalysts) and bed density; B and B0: one measured Ru "
            "catalyst per draw, with and without recovery. **b–d**, Probability that Ru is cheaper (A_bed, circles or "
            "dark bars; A, squares or light bars) by u (**b**), r (**c**) and the Ru content of the bed (**d**, n = "
            "draws per bin). Source: `%s`." % (
                format(int(a.draws.iloc[0]), ","),
                "; ".join("%s %.3f (%+.2f USD t$^{-1}$)" % (r.treatment.split(":")[0].split(" (")[0], r.P_Fe_cheaper,
                                                          r.median_Ru_minus_Fe_USD_t) for r in a.itertuples()),
                b.u_low.min(), b.u_high.max(), c.r_low.min(), c.r_high.max(), E.MC + "draws.csv, summary.json"), ""]

    d = E.edfig6()
    a, b, c, dd = (d[k][0] for k in "abcd")
    pf = b[b.study.str.startswith("Perez")].iloc[0]
    rest = b[~b.study.str.startswith("Campos")]
    base = int(dd[dd.variant == "baseline"].mismatch_groups.iloc[0])
    cat = dd[dd.variant.str.startswith("catalyst_repl_95")].set_index("variant").mismatch_groups
    out += ["## Extended Data Fig. 4 | The methanol plant model against published plants", "",
            "**a**, Cost terms of the Pérez-Fortes et al. (2016) plant run at its own point, prices, catalyst charge "
            "and finance (model / reference, EUR t$^{-1}$): break-even methanol price (production cost plus capital recovery) %.0f / %.0f (%+.1f %%); the anchor "
            "convention adds a catalyst-independent residual and 10 %% of the net production cost (%.0f EUR t$^{-1}$), "
            "common to every catalyst. **b**, Like-for-like cost against each study's reported production cost or break-even price at that study's "
            "own inputs (%d cases; band ±5 %%; green, the Campos anchor); deviations of the non-anchor cases %+.1f to "
            "%+.1f %%. **c**, Loop metrics at the Pérez-Fortes operating point, model / reference (%s). **d**, Number "
            "of the 83 comparisons whose STY leader is not the plant-cost leader under %d plant-model variants (keys in "
            "Source Data): model as used %d; catalyst replacement at 95.24 EUR kg$^{-1}$ every 6, 4 and 1 y gives %d, "
            "%d and %d. Source: `%s`." % (
                pf.model_eur_t, pf.reference_eur_t, pf.deviation_pct,
                a.set_index("term").loc["residual direct + 10 % of NPC (anchor convention)", "model"], len(b),
                rest.deviation_pct.min(), rest.deviation_pct.max(),
                "; ".join("%s %.2f" % (r.metric.replace("$_2$", "2"), r.ratio) for r in c.itertuples()), len(dd), base,
                cat["catalyst_repl_95.24EURkg_6y"], cat["catalyst_repl_95.24EURkg_4y"],
                cat["catalyst_repl_95.24EURkg_1y"], E.BENCH), ""]

    d, fe = E.edfig7()
    a, b, c = (d[k][0] for k in "abc")
    cr = c.set_index("system")
    out += ["## Extended Data Fig. 2 | Full optimizations saved by the closed-form lower bound", "",
            "**a**, Lower bound against the full plant cost (recycled CO) for the %d methanol literature candidates "
            "in %d comparison groups; every bound lies below its full cost. Agent rule per group: evaluate the paper's "
            "leader in full, then the others in increasing bound order until the next bound exceeds the best full "
            "cost; %d candidates are evaluated in full (blue), %d are excluded. **b**, The same for the %d ammonia "
            "bimetallic surfaces inside the bed cap (of %d costed); a surface is excluded when its bound exceeds the Fe "
            "benchmark (%.2f USD t$^{-1}$, dashed). **c**, Share of candidates evaluated in full: %s. No plant-cost "
            "leader and no surface below Fe is excluded. Source: `%s`, `%s`." % (
                len(a), a.group.nunique(), int(a.evaluated_recycled_opt.sum()), int((~a.evaluated_recycled_opt).sum()),
                int(b.feasible.sum()), len(b), fe,
                "; ".join("%s %d / %d (%s %% excluded)" % (s, r.full_evaluations, r.candidates,
                                                          _p(r.excluded_by_bound / r.candidates))
                          for s, r in cr.iterrows()), E.PRUNE + "candidate_bounds.csv", E.ALLOY), ""]
    assert int(cr.leader_missed.sum()) == 0
    assert (a.bound <= a.cost_recycled_opt * (1 + 5e-6)).all() and (a.bound <= a.cost_inert_opt * (1 + 5e-6)).all()
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
