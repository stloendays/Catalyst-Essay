"""Measurement-uncertainty Monte Carlo for the four Re/TiO2 methanol states (replacement for Fig. 4d).

Each catalyst state's own CO2 conversion and MeOH / CH4 selectivities are sampled independently from that
state's measured distribution (Gothe et al., ACS Catal. 2025, Table 3; uncertainty basis from
derive_uncertainty_basis.py), and the full MEOH-D01-v3 recycle / purge / separation plant model
(meoh_d01_model.py, reproduces the frozen costs to < 1e-12 EUR/t) is re-solved per draw with every cost parameter
held at its canonical value (2 % purge, 100 bar, Processes 2022 prices).

Per state and draw (scale k multiplies every uncertainty width; k = 1 is the primary case):
  X_CO2  ~ Normal(X0, k * sigma_X), sigma_X^2 = (0.5 pt)^2 / 3 + (r_X * X0)^2      (rounding + cross-detector)
  S_MeOH ~ reporting interval: v + k * U(-0.5, 0.5) pt
  S_CH4  ~ v + k * U(-0.5, 0.5) pt for a reported integer; U(0, k * 1 pt) for a reported "<1"
  then a sum-conserving MeOH -> CH4 transfer delta ~ Normal(0, k * sigma_delta) pt, truncated so S_CH4 >= 0
  S_CO-like = 1 - S_MeOH - S_CH4 (D01 closure convention); if S_MeOH + S_CH4 > 1, both are rescaled to sum to 1
  STY    = STY0 * (X * S_MeOH) / (X0 * S_MeOH0)  (STY is X * S_MeOH * F_CO2 / m_Re at fixed GHSV)
r_X and sigma_delta come from the paper's own data (derive_uncertainty_basis.py; the paper reports no error bars).
Common random numbers: the same N(0,1) / U(-0.5,0.5) variates are used at every k and for both input sets.

Inputs: Table 3 of Gothe et al. for the four states, identical to the workbook Candidate_Inputs (asserted
against data/meoh/meoh_candidate_ranking_D01v3.csv before sampling).

Outputs (this folder): mc_summary.json, mc_rank_probability_matrix.csv, mc_pairwise_inversion.csv,
mc_scale_sweep.csv, mc_draws_canonical_k1.csv, fig4d_measurement_mc.png/.pdf/.svg,
fig_measurement_mc_sensitivity.png.
"""
from __future__ import annotations

import csv
import itertools
import json
import os
import sys

import numpy as np
from scipy.stats import norm

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(REPO, "data", "meoh"))
import meoh_d01_model as M  # noqa: E402
from derive_uncertainty_basis import basis  # noqa: E402

N = 5000
SEED = 20261005
SCALES = (0.5, 1.0, 2.0)
SWEEP = np.round(np.arange(0.0, 4.01, 0.25), 2)
KEYS = ["1wtRe_200C", "5wtRe_200C", "1wtRe_250C", "5wtRe_250C"]
LABEL = {"1wtRe_200C": "1 wt%, 200 °C", "5wtRe_200C": "5 wt%, 200 °C",
         "1wtRe_250C": "1 wt%, 250 °C", "5wtRe_250C": "5 wt%, 250 °C"}

# reported Table 3 entries (percent strings)
REPORTED = {
    "canonical": {
        "1wtRe_200C": dict(X="19", SMeOH="99", SCH4="<1"),
        "5wtRe_200C": dict(X="33", SMeOH="97", SCH4="3"),
        "1wtRe_250C": dict(X="23", SMeOH="97", SCH4="1"),
        "5wtRe_250C": dict(X="40", SMeOH="74", SCH4="25"),
    },
}
SETS = ("canonical",)

UB = basis()
R_X = UB["adopted"]["r_X_relative_sd"]
SIG_D = UB["adopted"]["sigma_delta_pct"]


def central_inputs(set_name):
    """Point inputs of the set (D01 convention: '<1' CH4 central 0, CO-like closes)."""
    out = {}
    for k in KEYS:
        rep = REPORTED[set_name][k]
        x = float(rep["X"]) / 100
        sm = float(rep["SMeOH"]) / 100
        sc = 0.0 if rep["SCH4"].startswith("<") else float(rep["SCH4"]) / 100
        f = M.FROZEN[k]
        out[k] = dict(X=x, SMeOH=sm, SCH4=sc, SCO=1 - sm - sc, STY=f["STY"], Re_wt=f["Re_wt"])
    return out


def base_variates(rng):
    return {k: dict(zX=rng.standard_normal(N), uM=rng.uniform(-0.5, 0.5, N), uC=rng.uniform(-0.5, 0.5, N),
                    zD=rng.standard_normal(N)) for k in KEYS}


def sample(set_name, var, k):
    cen = central_inputs(set_name)
    draws = {}
    for key in KEYS:
        rep, v, c = REPORTED[set_name][key], var[key], cen[key]
        x0 = float(rep["X"])
        sig_x = np.sqrt(0.5 ** 2 / 3 + (R_X * x0) ** 2)
        X = (x0 + k * sig_x * v["zX"]) / 100
        sm = (float(rep["SMeOH"]) + k * v["uM"]) / 100
        if rep["SCH4"].startswith("<"):
            sc = k * (v["uC"] + 0.5) / 100
        else:
            sc = (float(rep["SCH4"]) + k * v["uC"]) / 100
        sc = np.maximum(sc, 0.0)
        sd = k * SIG_D / 100
        if sd > 0:   # MeOH <-> CH4 transfer, sum conserved; Normal truncated so that S_CH4 >= 0 (inverse CDF, CRN kept)
            p_lo = norm.cdf(-sc / sd)
            delta = sd * norm.ppf(p_lo + norm.cdf(v["zD"]) * (1.0 - p_lo))
            sm = sm - delta
            sc = np.maximum(sc + delta, 0.0)
        tot = sm + sc
        over = tot > 1.0
        sm = np.where(over, sm / tot, sm)
        sc = np.where(over, sc / tot, sc)
        sco = np.maximum(1.0 - sm - sc, 0.0)
        sm = 1.0 - sc - sco                       # exact closure to machine precision
        assert np.all((X > 0.01) & (X < 0.99)) and np.all(sm > 0) and np.all(sc >= 0) and np.all(sco >= 0)
        sty = c["STY"] * (X * sm) / (c["X"] * c["SMeOH"])
        cost = M.candidate_economics(X, sm, sc, sco, sty, c["Re_wt"])["cost_eur_t"]
        draws[key] = dict(X=X, SMeOH=sm, SCH4=sc, SCO=sco, STY=sty, cost=np.asarray(cost))
    return draws


def ranks_from(values, ascending=True):
    """values: (N, 4) array -> integer ranks 1..4 per row."""
    order = np.argsort(values if ascending else -values, axis=1, kind="stable")
    r = np.empty_like(order)
    r[np.arange(values.shape[0])[:, None], order] = np.arange(1, 5)
    return r


def analyse(set_name, draws):
    cen = central_inputs(set_name)
    c0 = {k: float(M.cost(cen[k])["cost_eur_t"]) for k in KEYS}
    econ_order = sorted(KEYS, key=lambda k: c0[k])
    up_order = sorted(KEYS, key=lambda k: -cen[k]["STY"])
    C = np.column_stack([draws[k]["cost"] for k in KEYS])
    S = np.column_stack([draws[k]["STY"] for k in KEYS])
    er, ur = ranks_from(C), ranks_from(S, ascending=False)
    rank_p = {k: [float(np.mean(er[:, i] == j)) for j in range(1, 5)] for i, k in enumerate(KEYS)}
    pair = {}
    for a, b in itertools.combinations(econ_order, 2):           # a cheaper than b at the centre
        ia, ib = KEYS.index(a), KEYS.index(b)
        pair["%s vs %s" % (a, b)] = float(np.mean(C[:, ia] > C[:, ib]))
    up_fixed = np.array([up_order.index(k) + 1 for k in KEYS])
    rho = 1.0 - 6.0 * np.sum((ur - er) ** 2, axis=1) / (4 * (4 ** 2 - 1))     # no ties (continuous draws)
    winner = econ_order[0]
    second, third = econ_order[1], econ_order[2]
    d23 = C[:, KEYS.index(third)] - C[:, KEYS.index(second)]
    res = {
        "central_cost_EUR_t": c0,
        "central_economic_order": econ_order,
        "upstream_order_STY_per_gRe": up_order,
        "rank_probability": rank_p,
        "pairwise_inversion_probability": pair,
        "P_full_central_order_retained": float(np.mean(np.all(er == np.array([econ_order.index(k) + 1 for k in KEYS]), axis=1))),
        "P_winner_stays_first": float(np.mean(er[:, KEYS.index(winner)] == 1)),
        "winner": winner,
        "second_vs_third": {"second": second, "third": third,
                            "P_inverted": pair["%s vs %s" % (second, third)],
                            "central_gap_EUR_t": c0[third] - c0[second],
                            "gap_draw_mean": float(d23.mean()), "gap_draw_sd": float(d23.std(ddof=1)),
                            "gap_draw_p05_p95": [float(np.percentile(d23, 5)), float(np.percentile(d23, 95))]},
        "P_economic_order_equals_frozen_upstream_order": float(np.mean(np.all(er == up_fixed, axis=1))),
        "P_economic_order_equals_same_draw_upstream_order": float(np.mean(np.all(er == ur, axis=1))),
        "P_upstream_winner_1wtRe_250C_economic_first": float(np.mean(er[:, KEYS.index("1wtRe_250C")] == 1)),
        "P_same_draw_upstream_winner_economic_first": float(np.mean(er[np.arange(N), np.argmax(S, axis=1)] == 1)),
        "P_upstream_order_itself_changes": float(np.mean(np.any(ur != up_fixed, axis=1))),
        "spearman_rho_upstream_vs_economic": {"mean": float(rho.mean()), "max": float(rho.max()),
                                              "P_rho_eq_1": float(np.mean(rho > 0.999)),
                                              "values_freq": {"%.1f" % v: float(np.mean(np.isclose(rho, v)))
                                                              for v in np.unique(np.round(rho, 1))}},
        "cost_quantiles_EUR_t": {k: {"mean": float(C[:, i].mean()), "sd": float(C[:, i].std(ddof=1)),
                                     "p05": float(np.percentile(C[:, i], 5)), "p50": float(np.median(C[:, i])),
                                     "p95": float(np.percentile(C[:, i], 95))} for i, k in enumerate(KEYS)},
    }
    return res, C, er


def check_inputs():
    import csv as _csv
    frozen = {r["candidate"]: float(r["NPC_EUR_t_2pct_purge"])
              for r in _csv.DictReader(open(os.path.join(REPO, "data", "meoh", "meoh_candidate_ranking_D01v3.csv"),
                                            encoding="utf-8"))}
    cen = central_inputs("canonical")
    for k in KEYS:
        c = float(M.cost(cen[k])["cost_eur_t"])
        assert abs(c - frozen[M.FROZEN[k]["name"]]) < 0.006, (k, c)


def main():
    check_inputs()
    rng = np.random.default_rng(SEED)
    var = base_variates(rng)
    summary = {"N": N, "seed": SEED, "scales": list(SCALES),
               "uncertainty_basis": {"r_X_relative_sd": R_X,
                                     "r_X_without_outlier": UB["mle_without_outlier"]["r_excess_relative_sd"],
                                     "carbon_closure": UB["carbon_closure_sum_pct"],
                                     "sigma_delta_pct": SIG_D,
                                     "sigma_X_pt_at_k1": {k: float(np.sqrt(0.5 ** 2 / 3 + (R_X * float(REPORTED["canonical"][k]["X"])) ** 2))
                                                          for k in KEYS}},
               "reported_inputs": REPORTED, "sets": {}}
    mat_rows, pair_rows, sweep_rows = [], [], []
    keep = {}
    for set_name in SETS:
        summary["sets"][set_name] = {}
        for k in SCALES:
            d = sample(set_name, var, k)
            res, C, er = analyse(set_name, d)
            summary["sets"][set_name]["k=%g" % k] = res
            keep[(set_name, k)] = (res, C)
            for key in res["central_economic_order"]:
                mat_rows.append(dict(input_set=set_name, scale=k, state=key,
                                     **{"rank_%d" % (j + 1): res["rank_probability"][key][j] for j in range(4)}))
            for p, v in res["pairwise_inversion_probability"].items():
                pair_rows.append(dict(input_set=set_name, scale=k, pair_cheaper_vs_dearer_at_centre=p,
                                      P_inverted=v))
            if k == 1.0:
                with open(os.path.join(HERE, "mc_draws_%s_k1.csv" % set_name), "w", newline="", encoding="utf-8") as fh:
                    w = csv.writer(fh)
                    w.writerow(["draw"] + ["%s_%s" % (key, q) for key in KEYS for q in ("X", "SMeOH", "SCH4", "SCO", "STY", "NPC")])
                    for n in range(N):
                        w.writerow([n] + ["%.6g" % d[key][q][n] for key in KEYS for q in ("X", "SMeOH", "SCH4", "SCO", "STY", "cost")])
        for k in SWEEP:
            res, _, _ = analyse(set_name, sample(set_name, var, float(k)))
            sweep_rows.append(dict(input_set=set_name, scale=float(k), P_winner_first=res["P_winner_stays_first"],
                                   P_second_third_inverted=res["second_vs_third"]["P_inverted"],
                                   P_full_order_retained=res["P_full_central_order_retained"],
                                   P_upstream_winner_first=res["P_upstream_winner_1wtRe_250C_economic_first"],
                                   P_econ_eq_upstream=res["P_economic_order_equals_same_draw_upstream_order"]))
    for name, rows in (("mc_rank_probability_matrix.csv", mat_rows), ("mc_pairwise_inversion.csv", pair_rows),
                       ("mc_scale_sweep.csv", sweep_rows)):
        with open(os.path.join(HERE, name), "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
    json.dump(summary, open(os.path.join(HERE, "mc_summary.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    for set_name in SETS:
        r = summary["sets"][set_name]["k=1"]
        print("[%s] order %s  P(winner first)=%.4f  P(2v3 inverted)=%.4f  P(full order)=%.4f  P(econ=upstream)=%.4f"
              % (set_name, r["central_economic_order"], r["P_winner_stays_first"], r["second_vs_third"]["P_inverted"],
                 r["P_full_central_order_retained"], r["P_economic_order_equals_same_draw_upstream_order"]))
    make_figures(summary, keep)


# ------------------------------------------------------------------------------------------- figures --------
def make_figures(summary, keep):
    sys.path.insert(0, os.path.join(REPO, "figures", "composite"))
    from matplotlib.colors import LinearSegmentedColormap
    from matplotlib.patches import Rectangle
    from style import INK, LINE, MID, RED, Page, boxed  # noqa: E402
    COLOR = {"1wtRe_200C": "#ACBF9F", "5wtRe_200C": "#6E8E62", "1wtRe_250C": "#9DACCB", "5wtRe_250C": "#56679A"}
    cmap = LinearSegmentedColormap.from_list("rp", ["#FFFFFF", "#3E4452"])

    def fmt(p):
        if p == 0:
            return ""
        if p < 0.005:
            return "<0.01"
        if p > 0.995 and p < 1:
            return ">0.99"
        return "%.2f" % p

    def matrix(set_name, stem):
        res = summary["sets"][set_name]["k=1"]
        order = res["central_economic_order"]
        win = res["winner"]
        pg = Page(72.0, 44.0)
        lab = pg.ax(2.0, 8.0, 26.0, 25.0)
        lab.set_xlim(0, 1)
        lab.set_ylim(-0.6, 3.6)
        lab.axis("off")
        m = pg.ax(30.0, 8.0, 36.0, 25.0)
        m.set_xlim(-0.5, 3.5)
        m.set_ylim(-0.6, 3.6)
        m.axis("off")
        for i, key in enumerate(order):
            y = 3 - i
            lab.plot(0.06, y, "s", ms=4.2, mfc=COLOR[key], mec=INK, mew=0.4)
            lab.text(0.17, y, LABEL[key], va="center", fontsize=6.0,
                     fontweight="bold" if key == win else "normal", color=RED if key == win else INK)
            for j in range(4):
                p = res["rank_probability"][key][j]
                m.add_patch(Rectangle((j - 0.46, y - 0.4), 0.92, 0.8, fc=cmap(p), ec=LINE, lw=0.5))
                if p > 0:
                    m.text(j, y, fmt(p), ha="center", va="center", fontsize=5.3,
                           color="white" if p >= 0.6 else INK, fontweight="bold" if p >= 0.6 else "normal")
        for j in range(4):
            m.text(j, 3.72, "#%d" % (j + 1), ha="center", va="bottom", fontsize=5.7)
        lab.text(0.0, 4.3, "Catalyst state", fontsize=6.0, fontweight="bold", va="bottom")
        lab.text(0.0, 3.72, "in net-cost order", fontsize=5.4, color=MID, va="bottom")
        pg.fig.text(30.0 / pg.W, 40.6 / pg.H, "Rank probability", fontsize=6.3, fontweight="bold", va="bottom")
        pg.fig.text(30.0 / pg.W, 37.6 / pg.H, "5,000 measurement draws (X$_\\mathrm{CO_2}$, S per state)",
                    fontsize=5.4, color=MID, va="bottom")
        s23 = res["second_vs_third"]
        m.text(1.5, -0.8, "#1 kept in %d / 5,000\n#2 ↔ #3 swap in %d / 5,000" % (
            round(res["P_winner_stays_first"] * N), round(s23["P_inverted"] * N)),
            ha="center", va="top", fontsize=5.4, color=MID, linespacing=1.1)
        for ext in ("png", "pdf", "svg"):
            pg.fig.savefig(os.path.join(HERE, "%s.%s" % (stem, ext)), dpi=600, facecolor="white")

    matrix("canonical", "fig4d_measurement_mc")

    # sensitivity sheet: cost distributions at k = 1 and probabilities vs k
    import matplotlib.pyplot as plt
    sweep = list(csv.DictReader(open(os.path.join(HERE, "mc_scale_sweep.csv"), encoding="utf-8")))
    pg = Page(183.0, 62.0)
    for col, set_name in enumerate(SETS):
        res, C = keep[(set_name, 1.0)]
        ax = pg.ax(12.0 + col * 60.0, 10.0, 50.0, 44.0)
        boxed(ax)
        bins = np.arange(900, 1320, 3)
        for i, key in enumerate(KEYS):
            ax.hist(C[:, i], bins=bins, color=COLOR[key], alpha=0.35, ec="none")
            ax.hist(C[:, i], bins=bins, histtype="step", color=COLOR[key], lw=1.1, label=LABEL[key])
            ax.axvline(res["central_cost_EUR_t"][key], color=INK, lw=0.5, ls=(0, (2, 1.5)))
        ax.set_xlim(915, 1010)
        ax.set_ylim(0, 1000)
        ax.set_xlabel("Net cost (EUR t$^{-1}$), k = 1")
        ax.set_ylabel("Draws")
        ax.set_title("Table 3 inputs", fontsize=6.5, loc="left")
        if col == 0:
            ax.legend(fontsize=5.0, loc="upper left", ncol=2, handlelength=1.2, columnspacing=0.8)
        ins = ax.inset_axes([0.64, 0.50, 0.33, 0.24])
        ins.hist(C[:, KEYS.index("5wtRe_250C")], bins=40, color=COLOR["5wtRe_250C"], ec="none")
        ins.tick_params(labelsize=4.5, length=1.2)
        ins.set_yticks([])
        ins.set_title("5 wt%, 250 °C", fontsize=4.8, pad=1)
    ax = pg.ax(136.0, 10.0, 44.0, 44.0)
    boxed(ax)
    for set_name, ls in (("canonical", "-"),):
        rows = [r for r in sweep if r["input_set"] == set_name]
        kk = [float(r["scale"]) for r in rows]
        ax.plot(kk, [float(r["P_winner_first"]) for r in rows], color="#6E8E62", ls=ls, lw=1.0)
        ax.plot(kk, [float(r["P_second_third_inverted"]) for r in rows], color=RED, ls=ls, lw=1.0)
        ax.plot(kk, [float(r["P_upstream_winner_first"]) for r in rows], color="#56679A", ls=ls, lw=1.0)
    for k in SCALES:
        ax.axvline(k, color=MID, lw=0.4, ls=(0, (1, 1.5)))
    ax.text(3.95, 0.93, "#1 kept", color="#6E8E62", fontsize=5.4, ha="right", va="top")
    ax.text(3.95, 0.52, "#2 ↔ #3 swap", color=RED, fontsize=5.4, ha="right", va="bottom")
    ax.text(3.95, 0.04, "STY winner #1", color="#56679A", fontsize=5.4, ha="right", va="bottom")
    ax.set_xlim(0, 4)
    ax.set_ylim(-0.02, 1.02)
    ax.set_xlabel("Uncertainty scale k")
    ax.set_ylabel("Probability")
    pg.fig.savefig(os.path.join(HERE, "fig_measurement_mc_sensitivity.png"), dpi=300, facecolor="white")
    plt.close("all")


if __name__ == "__main__":
    main()
