"""Extended Data Figs 8 (Au/TiO2 conditional rank preservation) and 9 (Sabatier Ru vs Ni), added 2026-10-21 on the
supervisor's guidance of 2026-10-20 (Au/TiO2 to Extended Data as a conditional result; the external methanation case
with its criterion fixed before the calculation).

Every number is read from the committed analysis outputs and asserted against their summaries:
    artifacts/au_tio2_decision_boundary_v2/   (controls/au_tio2_decision_boundary_v2/, CI au-tio2-decision-boundary-v2)
    analysis/sabatier_ru_ni_2026_10_19/results/ (run_model.py --check, CI sabatier-ru-ni-boundary)
"""
import json
import os

import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.ticker import NullFormatter

from style import DARK_B, DARK_G, FE, INK, MID, PALE_B, RED, RU, Page, boxed  # noqa: F401

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
AU = "artifacts/au_tio2_decision_boundary_v2/"
SAB = "analysis/sabatier_ru_ni_2026_10_19/results/"
SIZES = (2, 3, 4, 5, 6)


def _csv(rel):
    return pd.read_csv(os.path.join(REPO, rel))


def _json(rel):
    with open(os.path.join(REPO, rel), encoding="utf-8") as fh:
        return json.load(fh)


# ------------------------------------------------------------------------------------------------- data
def au_data():
    s = _json(AU + "summary.json")
    burden = s["point_estimate_order_nominal"]["burden_vs_best"] if "burden_vs_best" in s.get(
        "point_estimate_order_nominal", {}) else None
    if burden is None:
        burden = _find(s, "burden_vs_best")
    mc = _csv(AU + "mc_v2_per_candidate.csv")
    prim = mc[mc.primary.astype(str) == "True"].iloc[0]
    assert abs(prim.sigma_ln - 0.25) < 1e-12
    assert (round(prim.full_preservation, 4), round(prim.winner_2nm_probability, 4)) == (0.7770, 0.9941)
    mp = _csv(AU + "l2_boundary_map_q_vs_nm.csv")
    comb = _csv(AU + "l2_l3_combined_273_293K_moderate.csv").sort_values("q")
    q0 = comb[comb.q == 0].iloc[0]
    assert (round(q0.full_preservation_fraction, 4), round(q0.mean_spearman_rho, 5)) == (0.9216, 0.99214)
    thr = _csv(AU + "l2_adjacent_flip_thresholds.csv")
    assert np.allclose(thr.q_star_pair, 1.9)
    return dict(burden=burden, mc=mc, prim=prim, map=mp, comb=comb, thr=thr, summary=s)


def _find(o, key):
    if isinstance(o, dict):
        if key in o:
            return o[key]
        for v in o.values():
            r = _find(v, key)
            if r is not None:
                return r
    return None


def sab_data():
    s = _json(SAB + "summary.json")
    cs = _csv(SAB + "central_sweep.csv")
    mc = _csv(SAB + "mc_summary.csv")
    lev = _csv(SAB + "leverage_decomposition.csv")
    p = mc.set_index("scale_mw").p_ru_cheaper
    assert (round(p.loc[0.1], 3), round(p.loc[100], 4)) == (0.983, 0.0005)
    return dict(summary=s, central=cs, mc=mc, lev=lev)


# ------------------------------------------------------------------------------------------------- ED Fig. 8
def ed_au():
    d = au_data()
    pg = Page(183.0, 112.0)
    # a: catalyst requirement against size (nominal exponents)
    a = pg.ax(14, 62, 36, 38)
    b_ = np.asarray(d["burden"], float)
    assert np.allclose(b_, [1, 2.161, 3.732, 5.703, 8.064], atol=6e-4), b_
    a.plot(SIZES, b_, "-o", color=RU, ms=3, lw=0.8, mec=INK, mew=0.3)
    for x, y in zip(SIZES, b_):
        a.text(x, y * 1.12, "%.2f" % y if y > 1 else "1", ha="center", va="bottom", fontsize=5.3)
    a.set_yscale("log")
    a.set_ylim(0.8, 14)
    a.set_yticks([1, 2, 5, 10])
    a.set_yticklabels(["1", "2", "5", "10"])
    a.yaxis.set_minor_formatter(NullFormatter())
    a.set_xticks(SIZES)
    a.set_xlabel("Au particle diameter (nm)")
    a.set_ylabel("catalyst required (rel. to 2 nm)")
    boxed(a)
    pg.letter("a", 2, 108)

    # b: per-candidate scatter: full order and 2 nm leader against sigma
    b = pg.ax(62, 62, 36, 38)
    mc = d["mc"].sort_values("sigma_ln")
    b.plot(mc.sigma_ln, mc.full_preservation, "-o", color=RU, ms=3, lw=0.8, mec=INK, mew=0.3, label="full order")
    b.plot(mc.sigma_ln, mc.winner_2nm_probability, "-s", color=FE, ms=3, lw=0.8, mec=INK, mew=0.3,
           label="2 nm leader")
    b.axvline(0.25, color=INK, lw=0.4, ls=(0, (1.5, 1.5)))
    b.text(0.265, 1.0, "σ = 0.25", fontsize=5.3, va="top")
    b.set_ylim(0, 1.05)
    b.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    b.set_yticklabels(["0", "25", "50", "75", "100"])
    b.set_xlabel("per-size activity scatter σ (ln units)")
    b.set_ylabel("draws kept (%)")
    b.legend(frameon=False, fontsize=5.3, loc="lower left", bbox_to_anchor=(0.0, 0.0), handlelength=1.6)
    boxed(b)
    pg.letter("b", 50, 108)

    # c: lambda x (n + m) map of P(2 nm leader)
    c = pg.ax(112, 62, 40, 38)
    mp = d["map"]
    qs, nms = np.sort(mp.q.unique()), np.sort(mp.n_plus_m.unique())
    Z = mp.pivot(index="n_plus_m", columns="q", values="p_winner_2nm").loc[nms, qs].values
    cmap = LinearSegmentedColormap.from_list("w2b", ["#FFFFFF", RU])
    im = c.pcolormesh(_edges(qs), _edges(nms), Z, cmap=cmap, vmin=0, vmax=1, shading="flat")
    lo, hi = min(qs.min(), nms.min()), max(qs.max(), nms.max())
    c.plot([lo, hi], [lo, hi], color=INK, lw=0.6, ls=(0, (2, 1.5)))
    c.set_xlim(_edges(qs)[[0, -1]])
    c.set_ylim(_edges(nms)[[0, -1]])
    c.set_xlabel("life exponent λ (life ~ d$^{λ}$)")
    c.set_ylabel("requirement exponent n + m")
    c.text(0.03, 0.97, "dashed: λ = n + m", transform=c.transAxes, fontsize=5.3, va="top")
    cb = pg.fig.add_axes([153.5 / pg.W, 62 / pg.H, 2.2 / pg.W, 38 / pg.H])
    pg.fig.colorbar(im, cax=cb, ticks=[0, 0.5, 1])
    cb.set_yticklabels(["0", "50", "100"], fontsize=5.3)
    cb.set_ylabel("P(2 nm leader) (%)", fontsize=5.3, labelpad=1)
    boxed(c)
    pg.letter("c", 100, 108)

    # d: combined lifetime + operating freedom, 273-293 K
    e = pg.ax(14, 10, 70, 36)
    cm = d["comb"]
    e.plot(cm.q, cm.full_preservation_fraction, "-o", color=RU, ms=3, lw=0.8, mec=INK, mew=0.3, label="full order")
    e.plot(cm.q, cm.winner_2nm_probability, "-s", color=FE, ms=3, lw=0.8, mec=INK, mew=0.3, label="2 nm leader")
    e.plot(cm.q, cm.fully_inverted_fraction, "-^", color=INK, mfc="white", ms=3, lw=0.8, mew=0.5,
           label="order fully inverted")
    e.axvline(1.9, color=INK, lw=0.4, ls=(0, (1.5, 1.5)))
    e.text(1.85, 0.78, "λ = n + m\n= 1.9", fontsize=5.3, ha="right")
    e.axvspan(-0.6, 0.0, color=PALE_B, alpha=0.35, lw=0)
    e.text(-0.3, 1.04, "carbonate\nloss, λ ≈ 0", fontsize=5.3, ha="center", va="bottom")
    e.set_xlim(-0.6, 3.1)
    e.set_ylim(0, 1.2)
    e.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    e.set_yticklabels(["0", "25", "50", "75", "100"])
    e.set_xlabel("life exponent λ")
    e.set_ylabel("draws (%)")
    e.legend(frameon=False, fontsize=5.3, loc="center left", bbox_to_anchor=(1.01, 0.5), handlelength=1.6)
    boxed(e)
    pg.letter("d", 2, 50)
    return pg


def _edges(v):
    v = np.asarray(v, float)
    m = (v[1:] + v[:-1]) / 2
    return np.concatenate([[v[0] - (m[0] - v[0])], m, [v[-1] + (v[-1] - m[-1])]])


# ------------------------------------------------------------------------------------------------- ED Fig. 9
def ed_sab():
    d = sab_data()
    cs, mc, lev = d["central"], d["mc"], d["lev"]
    pg = Page(183.0, 62.0)
    # a: Ru - Ni catalyst-dependent cost against scale, central and Monte Carlo 5-95 %
    a = pg.ax(14, 12, 44, 40)
    a.plot(cs.scale_mw, cs.diff_ru_minus_ni_usd_mwh, color=RU, lw=0.9, label="central")
    a.errorbar(mc.scale_mw, mc.diff_median, yerr=[mc.diff_median - mc.diff_p05, mc.diff_p95 - mc.diff_median],
               fmt="o", ms=2.6, color=INK, mfc="white", mew=0.5, elinewidth=0.5, capsize=1.5,
               label="Monte Carlo median, 5–95 %")
    a.axhline(0, color=INK, lw=0.4)
    s_star = _parity(cs)
    a.axvline(s_star, color=INK, lw=0.4, ls=(0, (1.5, 1.5)))
    a.text(s_star * 1.12, -14, "%.2f MW" % s_star, fontsize=5.3, ha="left")
    a.set_xscale("log")
    a.set_ylim(-45, 12)
    a.set_xlabel("plant scale (MW SNG)")
    a.set_ylabel("Ru − Ni (USD MWh$^{-1}$)")
    a.legend(frameon=False, fontsize=5.3, loc="lower right", bbox_to_anchor=(1.0, 0.18))
    boxed(a)
    pg.letter("a", 2, 58)

    # b: P(Ru cheaper)
    b = pg.ax(74, 12, 40, 40)
    b.plot(mc.scale_mw, mc.p_ru_cheaper, "-o", color=RU, ms=3, lw=0.8, mec=INK, mew=0.3)
    for x, y in zip(mc.scale_mw, mc.p_ru_cheaper):
        b.text(x, y + 0.04, ("%.1f" % (100 * y)) if y >= 0.01 else ("%.2f" % (100 * y)), ha="center", fontsize=5.3)
    b.set_xscale("log")
    b.set_ylim(0, 1.12)
    b.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    b.set_yticklabels(["0", "25", "50", "75", "100"])
    b.set_xlabel("plant scale (MW SNG)")
    b.set_ylabel("P(Ru cheaper) (%)")
    boxed(b)
    pg.letter("b", 62, 58)

    # c: leverage decomposition r_V (1 + phi_proc) against Pi
    c = pg.ax(132, 12, 46, 40)
    c.plot(lev.scale_mw, lev.leverage_lhs, color=RU, lw=0.9, label="$r_V(1+φ_{proc})$")
    c.axhline(lev.Pi.iloc[0], color=RED, lw=0.8, label="Π = %.2f" % lev.Pi.iloc[0])
    c.axhline(lev.r_V.iloc[0], color=FE, lw=0.8, ls=(0, (2, 1.5)), label="$r_V$ = %.2f (inventory only)" % lev.r_V.iloc[0])
    c.axvline(s_star, color=INK, lw=0.4, ls=(0, (1.5, 1.5)))
    c.set_xscale("log")
    c.set_yscale("log")
    c.set_ylim(1, 30)
    c.set_yticks([1, 2, 5, 10, 20])
    c.set_yticklabels(["1", "2", "5", "10", "20"])
    c.yaxis.set_minor_formatter(NullFormatter())
    c.set_xlabel("plant scale (MW SNG)")
    c.set_ylabel("leverage ratio")
    c.legend(frameon=False, fontsize=5.3, loc="upper right")
    boxed(c)
    pg.letter("c", 120, 58)
    return pg


def _parity(cs):
    """Central parity scale from summary.json (solved on the full model by run_model.py); the sweep must bracket it."""
    v = float(_json(SAB + "summary.json")["central"]["parity_scale_mw"])
    x, y = cs.scale_mw.values, cs.diff_ru_minus_ni_usd_mwh.values
    i = int(np.where((y[:-1] < 0) & (y[1:] >= 0))[0][0])
    assert x[i] <= v <= x[i + 1], (v, x[i], x[i + 1])
    return v


# ------------------------------------------------------------------------------------------------- captions
def captions():
    d = au_data()
    p, cm, s = d["prim"], d["comb"].set_index("q"), d["summary"]
    mc = d["mc"].set_index("sigma_ln")
    au = ["## Extended Data Fig. 8 | Rank preservation in the Au/TiO$_2$ control and the catalyst-life channel", "",
          "2–6 nm Au on TiO$_2$ under one operating condition and process model (rate anchor of Janssens et al., size "
          "dependence of Overbury et al.). **a**, Catalyst required for the same conversion relative to 2 nm particles "
          "at the nominal size exponents (n = 0.9, m = 1.0): %s. A common Au price and loading leave every cost "
          "ratio equal to this ratio. **b**, Each particle size given an independent log-normal activity scatter σ "
          "on top of the shared exponents (10,000 draws per σ): full order kept in %s %% and 2 nm leader in %s %% at "
          "σ = 0.25 (dashed); %s %% and %s %% at σ = 0.50. **c**, Probability that 2 nm particles remain the least-cost "
          "catalyst when catalyst life scales as d$^{λ}$ (σ = 0.25, 2,000 draws per cell); the order is kept below the "
          "dashed line λ = n + m and inverted above it. **d**, Catalyst life combined with candidate-specific kinetic "
          "and operating variation over 273–293 K (10,000 draws per λ): full order kept in %s %% at λ = 0, %s %% at "
          "λ = 1.0 and %s %% at λ = 1.9; 2 nm leader in %s %%, %s %% and %s %%; order fully inverted in %s %% at λ = 3. "
          "Shaded: the powder Au/TiO$_2$ window at 273–313 K, where activity loss is carbonate accumulation without "
          "particle growth (λ ≈ 0); Ostwald ripening kinetics, where they control life, give λ = 3–4. λ is a model parameter; no "
          "lifetime–size exponent has been measured for Au/TiO$_2$. Source: `%s` (mc_v2_per_candidate.csv, "
          "l2_boundary_map_q_vs_nm.csv, l2_l3_combined_273_293K_moderate.csv)." % (
              ", ".join("%g nm %.2f" % (x, y) for x, y in zip(SIZES, d["burden"])),
              _pc(p.full_preservation), _pc(p.winner_2nm_probability), _pc(mc.loc[0.5, "full_preservation"]),
              _pc(mc.loc[0.5, "winner_2nm_probability"]),
              _pc(cm.loc[0.0, "full_preservation_fraction"]), _pc(cm.loc[1.0, "full_preservation_fraction"]),
              _pc(cm.loc[1.9, "full_preservation_fraction"]), _pc(cm.loc[0.0, "winner_2nm_probability"]),
              _pc(cm.loc[1.0, "winner_2nm_probability"]), _pc(cm.loc[1.9, "winner_2nm_probability"]),
              _pc(cm.loc[3.0, "fully_inverted_fraction"]), AU), ""]
    sd = sab_data()
    mcs, lev, cs = sd["mc"].set_index("scale_mw"), sd["lev"], sd["central"]
    sb = ["## Extended Data Fig. 9 | Ru against Ni in CO$_2$ methanation, from an independent reactor study", "",
          "Moioli and Züttel's 0.5 wt%% Ru/Al$_2$O$_3$ (one stage, 99.5 %% conversion) and Ni/Al$_2$O$_3$ (%.2f times "
          "the catalyst volume, two stages with intermediate water condensation) taken through the inventory, reactor "
          "and replacement chain of this work with the metal prices of the ammonia case; catalyst-dependent cost per "
          "MWh of SNG (LHV). **a**, Ru − Ni cost against plant scale at the central parameters (line; parity at %.2f MW) "
          "and the Monte Carlo median with 5–95 %% range (10,000 draws). **b**, Probability that Ru is cheaper: %s. "
          "**c**, The criterion fixed before the calculation: Ru is cheaper when r$_V$(1 + φ$_{proc}$) > Π, with "
          "r$_V$ = %.2f the Ni-to-Ru catalyst volume ratio, Π = %.2f the Ru-to-Ni catalyst price ratio per kilogram and "
          "φ$_{proc}$ the cost of the second Ni stage per unit of Ni catalyst cost (%.2f at 0.1 MW, %.3f at 100 MW). "
          "Source: `%s` (central_sweep.csv, mc_summary.csv, leverage_decomposition.csv)." % (
              lev.r_V.iloc[0], _parity(cs),
              ", ".join("%g MW %s %%" % (k, ("%.1f" % (100 * v)) if v >= 0.01 else "%.2f" % (100 * v))
                        for k, v in mcs.p_ru_cheaper.items()),
              lev.r_V.iloc[0], lev.Pi.iloc[0], lev.set_index("scale_mw").phi_proc.iloc[0],
              lev.set_index("scale_mw").phi_proc.iloc[-1], SAB), ""]
    return au + sb


def _pc(x):
    return "%.1f" % (100 * float(x))


# ------------------------------------------------------------------------------------------------- ED Fig. 7
# Replaces the descriptor-kinetics Monte Carlo of the actual Ru catalyst (supervisor, 2026-10-20: one kinetic
# generation for the Ru/C - Fe comparison): the 16 robustness cases with measured rate laws, each in its fitted range.
INR = "analysis/nh3_fe_inrange_kinetics_2026_10_19/"
LEASES = (1.35, 2.10, 5.10)


def frontier_data():
    t = _csv(INR + "robustness.csv")
    b = t.set_index("case").loc["base"]
    assert (round(b.gap_0_global, 2), round(b.gap_12_global, 2), round(100 * b.breakeven_global, 2)) == (-3.83, 2.13, 6.49)
    assert (round(b.gap_0_KAAP, 2), round(b.gap_12_KAAP, 2), round(100 * b.breakeven_KAAP, 2)) == (-1.21, 1.95, 4.57)
    return t


def ed_frontier():
    t = frontier_data()
    n = len(t)
    pg = Page(183.0, 92.0)
    yy = np.arange(n)[::-1]
    a = pg.ax(48, 10, 60, 72)
    a.axvline(0, color=INK, lw=0.5)
    for col, mk, fc, lab in (("gap_0_global", "o", RU, "own optima, 0 %/y"), ("gap_12_global", "o", "white", "own optima, 12 %/y"),
                             ("gap_0_KAAP", "D", DARK_B, "KAAP-type, 0 %/y"), ("gap_12_KAAP", "D", "white", "KAAP-type, 12 %/y")):
        v = t[col].astype(float).values
        ok = np.isfinite(v)
        off = -0.15 if "global" in col else 0.15
        a.plot(v[ok], yy[ok] + off, mk, ms=3.0, mfc=fc, mec=RU if "global" in col else DARK_B, mew=0.7, ls="none",
               label=lab)
    a.set_yticks(yy)
    a.set_yticklabels(t.case.str.replace("x", "×", regex=False).str.replace("kg/m3", "kg m$^{-3}$", regex=False), fontsize=5.6)
    a.set_ylim(-0.8, n - 0.2)
    a.set_xlim(-8, 7.5)
    a.set_xlabel("Ru/C $-$ Fe (USD t$^{-1}$ NH$_3$)")
    a.text(-7.7, n - 0.6, "Ru/C cheaper", fontsize=5.3, color=DARK_B, va="center")
    a.text(7.2, n - 0.6, "Fe cheaper", fontsize=5.3, color=DARK_G, ha="right", va="center")
    a.legend(frameon=False, fontsize=5.0, loc="upper right", bbox_to_anchor=(1.0, 0.50), handlelength=0.6, handletextpad=0.3, borderaxespad=0.2)
    boxed(a)
    pg.letter("a", 2, 88)

    b = pg.ax(124, 10, 54, 72)
    b.axvspan(LEASES[0], LEASES[2], color=PALE_B, alpha=0.45, lw=0)
    b.axvline(LEASES[1], color=RED, lw=0.7)
    for col, mk, fc, lab, off in (("breakeven_global", "o", RU, "own optima", -0.15),
                                  ("breakeven_KAAP", "D", DARK_B, "KAAP-type loop", 0.15)):
        v = 100 * pd.to_numeric(t[col], errors="coerce").values
        ok = np.isfinite(v)
        b.plot(v[ok], yy[ok] + off, mk, ms=3.0, mfc=fc, mec=INK, mew=0.4, ls="none", label=lab)
        for yv, case in zip(yy[~ok], t.case.values[~ok]):
            note = "no Fe bed within 90 m$^3$" if case.startswith("Fe effectiveness") else "Ru/C never cheaper"
            b.text(0.2, yv + off, note, fontsize=4.8, va="center", color=DARK_B)
    b.set_yticks(yy)
    b.set_yticklabels([])
    b.set_ylim(-0.8, n - 0.2)
    b.set_xlim(0, 16.5)
    b.set_xlabel("break-even Ru financing rate (% per year)")
    b.text(LEASES[1] + 0.25, n - 0.6, "reference 2.10", fontsize=5.0, color=RED, va="center")
    b.legend(frameon=False, fontsize=5.0, loc="lower right", handletextpad=0.3, borderaxespad=0.2)
    boxed(b)
    pg.letter("b", 112, 88)
    return pg


def frontier_caption():
    t = frontier_data().set_index("case")
    g, k = t.breakeven_global.astype(float), pd.to_numeric(t.breakeven_KAAP, errors="coerce")
    return ["## Extended Data Fig. 7 | Supported Ru/C against fused iron with measured rate laws: robustness", "",
            "Fused iron (Keestra et al. Model 3 with the Topsoe KM1R activity, fitted at 1–324 bar) and promoted Ru/C "
            "(Rossetti et al., 50–100 bar), each optimized only inside its fitted pressure range; Ru/C with its own bed "
            "(8 wt%% Ru, 490 kg m$^{-3}$) and 95.55 %% recovery, metal purchases and credits dated over the 25-year plant "
            "life. **a**, Ru/C − Fe at metal financing rates of 0 and 12 %% per year for the base case and 15 variants, at "
            "each catalyst's own optimum (circles) and in the KAAP-type loop at 90 bar and −20 °C (diamonds); base case "
            "%.2f / +%.2f and %.2f / +%.2f US dollars per tonne. A halved Fe effectiveness leaves no Fe bed within the "
            "90 m$^3$ limit in the KAAP-type loop. **b**, Financing rate at which the two catalysts cost the same: "
            "%.2f–%.2f %% per year at the own optima and %.2f–%.2f %% per year in the KAAP-type loop (base %.2f and %.2f); "
            "with inlet-rate sizing Ru/C is not cheaper in the KAAP-type loop at any rate. Shaded, the 32 disclosed "
            "catalyst-metal lease rates (1.35–5.10 %% per year); red, the reference rate 2.10 %% per year. Source: `%s` "
            "(robustness.csv, robustness_inrange.py)." % (
                t.loc["base", "gap_0_global"], t.loc["base", "gap_12_global"], t.loc["base", "gap_0_KAAP"],
                t.loc["base", "gap_12_KAAP"], 100 * g.min(), 100 * g.max(), 100 * k.min(), 100 * k.max(),
                100 * g["base"], 100 * k["base"], INR), ""]
