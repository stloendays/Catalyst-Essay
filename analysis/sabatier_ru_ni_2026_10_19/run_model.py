"""Run the pre-registered Sabatier Ru vs Ni sweeps, boundary solve, leverage decomposition and Monte Carlo.

Usage:  python analysis/sabatier_ru_ni_2026_10_19/run_model.py [--check]

Writes results/*.csv, results/summary.json and FROZEN_HASHES.json.  With --check, recomputes everything
and asserts the committed hashes and the headline numbers in results/summary.json are reproduced.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import sabatier_model as M  # noqa: E402

RESULTS = HERE / "results"
SEED = 20261019
N_MC = 10_000
SCALES_MW = np.round(np.logspace(-1, 2, 61), 10)
RU_MULTS = np.round(np.logspace(-1, 1, 41), 10)
LIVES_Y = np.arange(1, 11, dtype=float)
MC_SCALES = [0.1, 0.3, 1.0, 3.0, 10.0, 30.0, 100.0]
SOURCE_RU_PRICE_MULT = 8233.0 * M.EUR_TO_USD / M.PRICE_USD_KG["Ru"]   # source Table 6 Ru price vs frozen price
FLOAT_FMT = "%.10g"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sig(o):
    """Round every finite float in a JSON-able structure to FLOAT_FMT significant digits."""
    if isinstance(o, float):
        return float(FLOAT_FMT % o) if o == o and abs(o) != float("inf") else o
    if isinstance(o, dict):
        return {k: _sig(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_sig(v) for v in o]
    return o


def write_csv(df: pd.DataFrame, name: str) -> Path:
    path = RESULTS / name
    df.to_csv(path, index=False, float_format=FLOAT_FMT, lineterminator="\n")
    return path


def central_sweep() -> pd.DataFrame:
    c = M.cost_chain(SCALES_MW)
    df = pd.DataFrame({k: np.broadcast_to(v, SCALES_MW.shape) for k, v in c.items()})
    df["ranking"] = np.where(df["ru_cheaper"], "Ru>Ni", "Ni>Ru")
    return df


def price_scale_grid() -> pd.DataFrame:
    rows = []
    for mult in RU_MULTS:
        c = M.cost_chain(SCALES_MW, ru_price_mult=float(mult))
        for i, S in enumerate(SCALES_MW):
            rows.append(dict(ru_price_mult=float(mult), scale_mw=float(S),
                             cost_Ru_usd_mwh=float(c["cost_Ru_usd_mwh"][i]), cost_Ni_usd_mwh=float(c["cost_Ni_usd_mwh"][i]),
                             ranking="Ru>Ni" if c["ru_cheaper"][i] else "Ni>Ru",
                             Pi=float(c["Pi"]), phi_proc=float(c["phi_proc"][i]), leverage_margin=float(c["leverage_margin"][i])))
    return pd.DataFrame(rows)


def boundary_curve() -> pd.DataFrame:
    rows = []
    for L in LIVES_Y:
        for mult in RU_MULTS:
            S_full, st = M.parity_scale_mw(ru_price_mult=float(mult), life_y=float(L))
            S_lev, st2 = M.parity_scale_from_leverage(ru_price_mult=float(mult), life_y=float(L))
            rows.append(dict(life_y=float(L), ru_price_mult=float(mult), ru_price_usd_kg=float(mult) * M.PRICE_USD_KG["Ru"],
                             parity_scale_mw=S_full, status=st, parity_scale_mw_leverage=S_lev, status_leverage=st2,
                             log10_diff=(abs(math.log10(S_full) - math.log10(S_lev)) if st == "root" and st2 == "root" else math.nan)))
    return pd.DataFrame(rows)


def leverage_decomposition() -> pd.DataFrame:
    c = M.cost_chain(SCALES_MW)
    return pd.DataFrame(dict(scale_mw=SCALES_MW, r_V=np.full_like(SCALES_MW, M.CENTRAL.r_V), Pi=np.full_like(SCALES_MW, float(c["Pi"])),
                             phi_proc=c["phi_proc"], leverage_lhs=c["leverage_lhs"], leverage_margin=c["leverage_margin"],
                             inventory_term_ratio_A_Ni_over_A_Ru=c["A_Ni_usd_y"] / c["A_Ru_usd_y"],
                             reactor_term_ratio_R_Ni_over_R_Ru=c["R_Ni_usd_y"] / c["R_Ru_usd_y"],
                             ru_cheaper=c["ru_cheaper"]))


def scenarios() -> pd.DataFrame:
    """Named deterministic scenarios (all pre-registered brackets, plus the source's own 2019 Ru price)."""
    spec = {
        "central": {},
        "metal_only_basis": dict(basis_u=0.0),
        "commercial_basis": dict(basis_u=1.0),
        "source_2019_ru_price": dict(ru_price_mult=SOURCE_RU_PRICE_MULT),
        "source_2019_ru_price_metal_only": dict(ru_price_mult=SOURCE_RU_PRICE_MULT, basis_u=0.0),
        "ru_recovery_0p9": dict(ru_recovery=0.9),
        "life_2y": dict(life_y=2.0),
        "life_10y": dict(life_y=10.0),
        "kappa_0p5": dict(kappa=0.5),
        "kappa_3": dict(kappa=3.0),
        "r_V_1p5": dict(r_V=1.5),
        "r_V_2p5": dict(r_V=2.5),
        "r_V_isothermal_kref_3p46e_4_0p28": dict(r_V=0.28),
        "r_V_isothermal_kref_3p46e_5_2p77": dict(r_V=2.77),
        "ghsv_1500": dict(ghsv_h=1500.0),
        "ghsv_6000": dict(ghsv_h=6000.0),
        "ru_price_x0p1": dict(ru_price_mult=0.1),
        "ru_price_x10": dict(ru_price_mult=10.0),
    }
    rows = []
    for name, over in spec.items():
        S_star, st = M.parity_scale_mw(**over)
        c01 = M.cost_chain(0.1, **over)
        c100 = M.cost_chain(100.0, **over)
        rows.append(dict(scenario=name, overrides=json.dumps(over, sort_keys=True), parity_scale_mw=S_star, status=st,
                         cost_Ru_0p1MW=float(c01["cost_Ru_usd_mwh"]), cost_Ni_0p1MW=float(c01["cost_Ni_usd_mwh"]),
                         ranking_0p1MW="Ru>Ni" if c01["ru_cheaper"] else "Ni>Ru",
                         cost_Ru_100MW=float(c100["cost_Ru_usd_mwh"]), cost_Ni_100MW=float(c100["cost_Ni_usd_mwh"]),
                         ranking_100MW="Ru>Ni" if c100["ru_cheaper"] else "Ni>Ru", Pi=float(c01["Pi"])))
    return pd.DataFrame(rows)


def monte_carlo() -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(SEED)
    n = N_MC
    draws = dict(
        r_V=rng.uniform(1.5, 2.5, n),
        ghsv_h=np.exp(rng.uniform(math.log(1500.0), math.log(6000.0), n)),
        rho_bulk_kg_m3=rng.uniform(1200.0, 1800.0, n),
        ru_price_mult=np.exp(rng.uniform(math.log(0.5), math.log(2.0), n)),
        ni_price_mult=np.exp(rng.uniform(math.log(0.5), math.log(2.0), n)),
        life_y=rng.uniform(2.0, 10.0, n),
        ru_recovery=rng.uniform(0.0, 0.9, n),
        basis_u=rng.uniform(0.0, 1.0, n),
        kappa=rng.uniform(0.5, 3.0, n),
        capex_mult=rng.uniform(0.8, 1.2, n),
    )
    summary, per_draw = [], {"draw": np.arange(n)}
    per_draw.update(draws)
    for S in MC_SCALES:
        c = M.cost_chain(S, **draws)
        d = c["diff_ru_minus_ni_usd_mwh"]
        per_draw[f"diff_ru_minus_ni_{S:g}MW"] = d
        summary.append(dict(scale_mw=S, n=n, n_ru_cheaper=int(np.sum(d < 0)), p_ru_cheaper=float(np.mean(d < 0)),
                            diff_median=float(np.median(d)), diff_p05=float(np.percentile(d, 5)), diff_p95=float(np.percentile(d, 95)),
                            cost_Ru_median=float(np.median(c["cost_Ru_usd_mwh"])), cost_Ni_median=float(np.median(c["cost_Ni_usd_mwh"]))))
    # per-draw parity scale by vectorised bisection in log10 S over [0.1, 100]
    lo = np.full(n, -1.0); hi = np.full(n, 2.0)
    f = lambda logS: np.asarray(M.cost_chain(10.0 ** logS, **draws)["diff_ru_minus_ni_usd_mwh"])
    flo, fhi = f(lo), f(hi)
    status = np.where((flo < 0) & (fhi < 0), "ru_cheaper_everywhere", np.where((flo > 0) & (fhi > 0), "ni_cheaper_everywhere", "root"))
    for _ in range(60):
        mid = 0.5 * (lo + hi); fm = f(mid)
        same = (fm < 0) == (flo < 0)
        lo = np.where(same, mid, lo); flo = np.where(same, fm, flo)
        hi = np.where(same, hi, mid)
    S_star = np.where(status == "root", 10.0 ** (0.5 * (lo + hi)), np.nan)
    per_draw["parity_scale_mw"] = S_star
    per_draw["parity_status"] = status
    return pd.DataFrame(summary), pd.DataFrame(per_draw)


def kinetic_crosscheck() -> pd.DataFrame:
    rows = []
    for T in (250.0, 300.0, 350.0, 400.0):
        for P in (1.0, 10.0):
            for X in (0.7, 0.9):
                rows.append(M.kinetic_volume_ratio(T, P, X))
    return pd.DataFrame(rows)


def main(check: bool) -> int:
    RESULTS.mkdir(exist_ok=True)
    sweep = central_sweep(); grid = price_scale_grid(); bnd = boundary_curve(); lev = leverage_decomposition()
    scen = scenarios(); mc_sum, mc_draws = monte_carlo(); kin = kinetic_crosscheck()

    S_star, st = M.parity_scale_mw()
    c01 = M.cost_chain(0.1); c100 = M.cost_chain(100.0)
    p_small = float(mc_sum.loc[mc_sum.scale_mw == 0.1, "p_ru_cheaper"].iloc[0])
    p_large = float(mc_sum.loc[mc_sum.scale_mw == 100.0, "p_ru_cheaper"].iloc[0])
    h3_ok = bnd["log10_diff"].dropna()
    summary = dict(
        seed=SEED, n_mc=N_MC, central_params=asdict(M.CENTRAL),
        frozen_prices_usd_kg=M.PRICE_USD_KG, source_2019_ru_price_mult=SOURCE_RU_PRICE_MULT,
        central=dict(parity_scale_mw=S_star, status=st,
                     cost_Ru_0p1MW=float(c01["cost_Ru_usd_mwh"]), cost_Ni_0p1MW=float(c01["cost_Ni_usd_mwh"]),
                     cost_Ru_100MW=float(c100["cost_Ru_usd_mwh"]), cost_Ni_100MW=float(c100["cost_Ni_usd_mwh"]),
                     Pi=float(c01["Pi"]), r_V=M.CENTRAL.r_V, phi_proc_0p1MW=float(c01["phi_proc"]), phi_proc_100MW=float(c100["phi_proc"]),
                     ranking_0p1MW="Ru>Ni" if c01["ru_cheaper"] else "Ni>Ru", ranking_100MW="Ru>Ni" if c100["ru_cheaper"] else "Ni>Ru"),
        boundary=dict(n_points=int(len(bnd)), n_root=int((bnd.status == "root").sum()),
                      n_ru_everywhere=int((bnd.status == "ru_cheaper_everywhere").sum()), n_ni_everywhere=int((bnd.status == "ni_cheaper_everywhere").sum()),
                      parity_scale_central_life5_price1=S_star,
                      parity_scale_source_2019_price_life5=float(scen.loc[scen.scenario == "source_2019_ru_price", "parity_scale_mw"].iloc[0]),
                      max_log10_diff_full_vs_leverage=float(h3_ok.max()) if len(h3_ok) else None),
        monte_carlo=dict(p_ru_cheaper_by_scale={f"{r.scale_mw:g}": r.p_ru_cheaper for r in mc_sum.itertuples()},
                         parity_status_counts=mc_draws["parity_status"].value_counts().to_dict(),
                         parity_scale_median_mw=float(np.nanmedian(mc_draws["parity_scale_mw"])),
                         parity_scale_p05_mw=float(np.nanpercentile(mc_draws["parity_scale_mw"], 5)),
                         parity_scale_p95_mw=float(np.nanpercentile(mc_draws["parity_scale_mw"], 95))),
        kinetic_crosscheck=dict(
            ratio_Ni_over_Ru_300C_10bar_X0p9_kref_3p46e_4=float(kin.loc[(kin.T_C == 300) & (kin.P_bar == 10) & (kin.X_target == 0.9), "ratio_Ni_over_Ru_kref_3p46e_4"].iloc[0]),
            ratio_Ni_over_Ru_300C_10bar_X0p9_kref_3p46e_5=float(kin.loc[(kin.T_C == 300) & (kin.P_bar == 10) & (kin.X_target == 0.9), "ratio_Ni_over_Ru_kref_3p46e_5"].iloc[0]),
            source_reported_ratio_X0p9=3.11),
        hypotheses=dict(
            H1_small_scale_ru_preserved=bool(c01["ru_cheaper"]) and p_small >= 0.5,
            H2_boundary_exists_in_range=(st == "root"),
            H3_leverage_locates_boundary=bool(len(h3_ok)) and float(h3_ok.max()) < 1e-6,
        ),
    )

    paths = [write_csv(sweep, "central_sweep.csv"), write_csv(grid, "price_scale_grid.csv"), write_csv(bnd, "boundary_curve.csv"),
             write_csv(lev, "leverage_decomposition.csv"), write_csv(scen, "scenarios.csv"), write_csv(mc_sum, "mc_summary.csv"),
             write_csv(mc_draws, "mc_draws.csv"), write_csv(kin, "kinetic_crosscheck.csv")]
    # floats at the CSV precision (FLOAT_FMT): the full-precision repr differs in the last bit across platforms;
    # bytes are written with LF on every OS so that FROZEN_HASHES.json holds on Linux CI and Windows alike
    sp = RESULTS / "summary.json"; sp.write_bytes((json.dumps(_sig(summary), indent=2, sort_keys=True) + "\n").encode())
    paths.append(sp)
    hashes = {p.relative_to(HERE).as_posix(): sha256(p) for p in paths}

    hp = HERE / "FROZEN_HASHES.json"
    if check:
        frozen = json.loads(hp.read_text())
        bad = {k: (v, frozen.get(k)) for k, v in hashes.items() if frozen.get(k) != v}
        if bad:
            print("HASH MISMATCH:", json.dumps(bad, indent=1)); return 1
        print("All", len(hashes), "result files reproduce their frozen SHA-256.")
    else:
        hp.write_bytes((json.dumps(hashes, indent=2, sort_keys=True) + "\n").encode())
    print(json.dumps(summary["central"], indent=1)); print(json.dumps(summary["monte_carlo"]["p_ru_cheaper_by_scale"])); print(summary["hypotheses"])
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--check", action="store_true")
    sys.exit(main(ap.parse_args().check))
