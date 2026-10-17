"""Leverage criterion: when does an upstream advantage survive the frozen plant models? (PROTOCOL.md, 2026-10-12)

    python analysis/leverage_criterion_2026_10_12/run_leverage_criterion.py        # LEV_WORKERS (default 4)

For each pre-registered pair (i = better upstream metric, j = its plant-cost competitor) of the four systems
(Au/TiO2 control, NH3 top three, methanol field groups under S5 and S6, Re/TiO2 four states) the cost difference
C_j - C_i is decomposed over the properties in which i and j differ, three ways (PROTOCOL.md section 4):

  D  exact Shapley values with the plant re-optimized for every hybrid (attribution; its sign rule is an identity)
  F  Shapley values with the operating point frozen at i's optimum (criterion C2)
  L  first-order terms eps_k * Delta z_k at i's optimum (criterion C1, primary)

and scored against the frozen outcome. Reproduction gates (PROTOCOL.md section 7) abort the run on failure.

Outputs (this folder): cases.csv, properties.csv, pools.csv, meoh_pairwise.csv, run_record.json; then
score_leverage_criterion.py writes summary.json and results_tables.md. About 11 min on 6 workers.
"""
from __future__ import annotations

import ast
import hashlib
import json
import math
import os
import random
import shutil
import sys
import tempfile
import time
from itertools import combinations
from math import factorial
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "data" / "meoh"))
import meoh_d01_model as M  # noqa: E402
import meoh_general_model as G  # noqa: E402

WORKERS = int(os.environ.get("LEV_WORKERS", "4"))
REL_TIE = 1e-9            # actual outcome: |C_j - C_i| <= REL_TIE * max -> tie -> preserved
TOL_RULE = 1e-12          # criterion: |U + O| <= TOL_RULE (relative for D and F) -> preserved
EPS_LN = 0.005            # ln coordinates: x (1 +/- 0.005)
EPS_LOGTOF = 0.005        # log10 TOF: +/- 0.005 decade
EPS_S = 0.001             # selectivities: +/- 0.001 absolute
EPS_T = 0.5               # temperature: +/- 0.5 K

CLASS = {"U": "upstream metric", "X": "single-pass conversion", "CO": "selectivity CO", "CH4": "selectivity CH4",
         "S": "selectivity CO+CH4", "T": "temperature / operating window", "W": "temperature / operating window",
         "M": "metal price / loading", "L": "metal price / loading"}
NAME = {"Au": {"U": "mass activity"},
        "NH3": {"U": "intrinsic activity (log10 TOF, 673 K)", "W": "operating window (state TOF profile)",
                "M": "metal price and molar mass"},
        "MeOH": {"U": "STY per g catalyst", "X": "CO2 conversion", "CO": "S_CO", "CH4": "S_CH4", "S": "S_CO and S_CH4",
                 "T": "reaction temperature"},
        "Re": {"U": "STY per g Re", "L": "Re loading", "X": "CO2 conversion", "CO": "S_CO", "CH4": "S_CH4"}}

NH3_POOLS = ["metal", "reactor_base", "vessel_premium", "fresh_comp", "recycle_comp", "refrigeration",
             "compressor_capex"]
NH3_PATHWAY = {"metal", "reactor_base", "vessel_premium"}
MEOH_POOLS = ["reactor_modules", "h2_feed", "co2_feed", "compression_electricity", "compressor_capital",
              "loop_equipment", "purge_handling", "fixed"]
MEOH_PATHWAY = set(MEOH_POOLS) - {"reactor_modules", "fixed"}
AU_POOLS = ["catalyst_mass"]
POOL_CLASS = {"metal": "catalyst inventory", "reactor_base": "reactor", "vessel_premium": "reactor",
              "fresh_comp": "compression & refrigeration", "recycle_comp": "compression & refrigeration",
              "refrigeration": "compression & refrigeration", "compressor_capex": "compression & refrigeration",
              "reactor_modules": "catalyst / reactor modules", "h2_feed": "H2 feed", "co2_feed": "CO2 feed",
              "compression_electricity": "recycle & compression", "compressor_capital": "recycle & compression",
              "loop_equipment": "recycle & compression", "purge_handling": "purge handling", "fixed": "fixed",
              "catalyst_mass": "catalyst mass"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(ok, msg):
    if not ok:
        raise SystemExit("GATE FAILED: " + msg)


# ================================================================ Shapley and criteria ===========================
def coalitions(players):
    return [frozenset(S) for r in range(len(players) + 1) for S in combinations(players, r)]


def shapley(players, v):
    """Exact Shapley values; v maps frozenset -> float or numpy array (pool vectors)."""
    n = len(players)
    out = {}
    for k in players:
        rest = [p for p in players if p != k]
        tot = 0.0
        for r in range(len(rest) + 1):
            w = factorial(r) * factorial(n - r - 1) / factorial(n)
            for S in combinations(rest, r):
                S = frozenset(S)
                tot = tot + w * (v[S | {k}] - v[S])
        out[k] = tot
    return out


def predict(U, O, scale=1.0):
    return bool(U + O < -TOL_RULE * scale)


def actual_inverted(ci, cj):
    return bool(cj < ci and abs(cj - ci) > REL_TIE * max(abs(ci), abs(cj)))


def fd_ln(f, x, eps=EPS_LN):
    """d ln f / d ln x, central difference x (1 +/- eps)."""
    return (math.log(f(x * (1 + eps))) - math.log(f(x * (1 - eps)))) / (math.log(1 + eps) - math.log(1 - eps))


def fd_lin(f, x, h, lower=None):
    """d ln f / d x, central difference +/- h, forward where x - h < lower."""
    if lower is not None and x - h < lower:
        return (math.log(f(x + h)) - math.log(f(x))) / h
    return (math.log(f(x + h)) - math.log(f(x - h))) / (2 * h)


# ================================================================ Au/TiO2 control ================================
def au_setup():
    path = REPO / "controls" / "au_tio2_rank_preservation_v1_1.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "candidate_state")
    cfg = json.loads((REPO / "controls" / "au_tio2_rank_preservation_v1_1_config.json").read_text(encoding="utf-8"))
    ns = {"CFG": cfg, "math": math}
    exec(compile(ast.Module(body=[fn], type_ignores=[]), str(path), "exec"), ns)  # the frozen function, unchanged
    return cfg, ns["candidate_state"]


def au_mass_mg(cfg, a):
    """Required catalyst mass (mg) for mass activity a (umol gcat^-1 s^-1): the reactor lines of candidate_state."""
    ref = cfg["literature_reference"]
    flow = ref["reaction_flow_Nml_min"] * 1e-3 / cfg["reactor_model"]["normal_molar_volume_L_mol"] / 60.0
    y = ref["feed_CO_mole_fraction"]
    theta = ref["stabilized_activity_umol_CO_gcat_s"] * 1e-6 / y * (ref["catalyst_mass_mg"] / 1000.0) / flow
    x = 1.0 - math.exp(-theta)
    return -math.log(1.0 - x) * flow / (a * 1e-6 / y) * 1000.0


def au_case(cfg, di, dj, ai, aj, Ji, Jj, case_id):
    Jh = au_mass_mg(cfg, aj)
    phi = Jh - Ji
    eps = fd_ln(lambda a: au_mass_mg(cfg, a), ai)
    t = eps * math.log(aj / ai)
    return dict(case=dict(system="Au", scenario="nominal", case_id=case_id, i=f"{di:g} nm", j=f"{dj:g} nm",
                          C_i=Ji, C_j=Jj, unit="mg catalyst", players="U"),
                props={"U": dict(phi_D=phi, phi_F=phi, t_L=t, dz=math.log(aj / ai), eps=eps)},
                pools_D={"U": np.array([phi])}, pools_i=np.array([Ji]), pools_j=np.array([Jj]), pool_names=AU_POOLS)


def run_au():
    cfg, candidate_state = au_setup()
    n_nom = cfg["size_activity_relation"]["nominal_tof_exponent"]
    m_nom = cfg["geometry"]["dispersion_exponent_nominal"]
    ds = cfg["candidate_diameters_nm"]
    rows = [candidate_state(d, n_nom, m_nom) for d in ds]
    for r in rows:
        J = au_mass_mg(cfg, r["mass_activity_umol_CO_gcat_s"])
        require(abs(J - r["required_catalyst_mass_mg"]) <= 1e-12 * J, "Au required mass reproduction")
    cases = []
    for k in range(len(ds) - 1):
        a, b = rows[k], rows[k + 1]
        if a["mass_activity_umol_CO_gcat_s"] < b["mass_activity_umol_CO_gcat_s"]:
            a, b = b, a
        cases.append(au_case(cfg, a["diameter_nm"], b["diameter_nm"], a["mass_activity_umol_CO_gcat_s"],
                             b["mass_activity_umol_CO_gcat_s"], a["required_catalyst_mass_mg"],
                             b["required_catalyst_mass_mg"], f"Au {a['diameter_nm']:g}-{b['diameter_nm']:g} nm"))
    # the frozen 10,000 draws (same RNG sequence as the control)
    unc = cfg["uncertainty"]
    rng = random.Random(unc["seed"])
    tally = dict(cases=0, actual_inverted=0, L_pred_inverted=0, F_pred_inverted=0, L_correct=0, F_correct=0,
                 full_rank_preserved_draws=0)
    for _ in range(unc["draws"]):
        n = rng.uniform(unc["tof_exponent_min"], unc["tof_exponent_max"])
        m = rng.uniform(unc["dispersion_exponent_min"], unc["dispersion_exponent_max"])
        rr = [candidate_state(d, n, m) for d in ds]
        act = [r["mass_activity_umol_CO_gcat_s"] for r in rr]
        bur = [r["required_catalyst_mass_mg"] for r in rr]
        tally["full_rank_preserved_draws"] += int(sorted(range(5), key=lambda q: -act[q]) == sorted(range(5), key=lambda q: bur[q]))
        for k in range(4):
            p, q = (k, k + 1) if act[k] >= act[k + 1] else (k + 1, k)
            inv = actual_inverted(bur[p], bur[q])
            eps = fd_ln(lambda a: au_mass_mg(cfg, a), act[p])
            pl = predict(eps * math.log(act[q] / act[p]), 0.0)
            pf = predict(au_mass_mg(cfg, act[q]) - bur[p], 0.0, max(bur[p], bur[q]))
            tally["cases"] += 1
            tally["actual_inverted"] += inv
            tally["L_pred_inverted"] += pl
            tally["F_pred_inverted"] += pf
            tally["L_correct"] += int(pl == inv)
            tally["F_correct"] += int(pf == inv)
    require(tally["full_rank_preserved_draws"] == unc["draws"], "Au draws: full-rank preservation in every draw")
    return cases, tally


# ================================================================ NH3 ============================================
def nh3_setup():
    sys.path.insert(0, str(REPO / "analysis" / "nh3_actual_ru_params_2026_10_07"))
    import build_harness_root as B
    import yaml
    require(sha256(B.WORKBOOK) == B.WORKBOOK_SHA256, "NH3 workbook SHA-256")
    root = Path(tempfile.mkdtemp(prefix="nh3_leverage_"))
    (root / "inputs").mkdir()
    shutil.copy2(B.CORE / "harness_core.py", root / "harness_core.py")
    shutil.copy2(B.WORKBOOK, root / "inputs" / B.WORKBOOK.name)
    run = root / "outputs" / B.RUN_NAME
    run.mkdir(parents=True)
    for f in ("manifest_resolved.yaml", "results.json"):
        shutil.copy2(B.CORE / "outputs" / B.RUN_NAME / f, run / f)
    sys.path.insert(0, str(root))
    import harness_core as hc
    H = hc.NH3Harness(yaml.safe_load((run / "manifest_resolved.yaml").read_text(encoding="utf-8")), root)
    require(H.NSTATE == 14136, "NH3 process states")
    results = json.loads((run / "results.json").read_text(encoding="utf-8"))
    return H, hc, results, root


def nh3_eval(H, L, price, mw):
    """cost_arrays with price and molar mass as inputs (same arithmetic), plus the seven pools per state."""
    active = H.nh3_mol_s * mw / H.F_CAL * np.power(10.0, -L)
    V = active / H.ACTIVE_FRACTION / H.BED_DENSITY
    metal = active * price * (1.0 - H.METAL_RECOVERY) / H.CATALYST_LIFE_Y / H.annual_output_t
    base = (H.REACTOR_FIXED + H.REACTOR_VAR * np.power(V / H.REACTOR_REF, H.REACTOR_EXP)) * H.crf / H.annual_output_t
    reactor = base + H.vessel_pressure_premium(V)
    total = metal + reactor + H.state_process_cost
    pools = np.vstack([metal, base, reactor - base, H.state_fresh, H.state_reccomp, H.state_refrig, H.state_compcapex])
    return total, V, pools


def nh3_opt(H, total, V):
    ok = V <= H.V_CAP
    if ok.any():
        return int(np.argmin(np.where(ok, total, np.inf))), False
    return int(np.argmin(total)), True


def run_nh3():
    H, hc, results, root = nh3_setup()
    metals = ["Ru", "Os", "Fe"]
    d = {}
    for m in metals:
        a = float(H.base_condition.logtof(hc.EN0_CANON[m]))
        L = H.frozen_state_logtof(hc.EN0_CANON[m])
        total, V, pools = nh3_eval(H, L, hc.PRICE[m], hc.MW[m])
        ref_total = H.cost_arrays(m, L)[0]
        require(np.array_equal(total, ref_total), f"NH3 {m}: cost function identical to cost_arrays")
        idx, fb = nh3_opt(H, total, V)
        frozen = results["deterministic"]["metals"][m]
        require(abs(total[idx] - frozen["feasible"]["total_cost"]) <= 1e-9, f"NH3 {m} cost vs results.json")
        require(abs(a - frozen["activity_logTOF"]) <= 1e-12, f"NH3 {m} activity vs results.json")
        require(abs(pools[:, idx].sum() - total[idx]) <= 1e-9 * total[idx], f"NH3 {m} pools sum")
        d[m] = dict(a=a, L=L, w=L - a, price=hc.PRICE[m], mw=hc.MW[m], C=float(total[idx]), idx=idx)
    gates = {m: d[m]["C"] for m in metals}
    cases = []
    fallbacks = 0
    for mi, mj in (("Ru", "Os"), ("Ru", "Fe"), ("Os", "Fe")):
        i, j = (d[mi], d[mj]) if d[mi]["a"] >= d[mj]["a"] else (d[mj], d[mi])
        ni, nj = (mi, mj) if i is d[mi] else (mj, mi)
        players = ["U", "W", "M"]
        sstar = i["idx"]
        vD, vF, pD = {}, {}, {}
        for S in coalitions(players):
            if ("U" in S) == ("W" in S):
                L = j["L"] if "U" in S else i["L"]
            else:
                L = (j["a"] if "U" in S else i["a"]) + (j["w"] if "W" in S else i["w"])
            src = j if "M" in S else i
            total, V, pools = nh3_eval(H, L, src["price"], src["mw"])
            idx, fb = nh3_opt(H, total, V)
            fallbacks += fb
            vD[S], vF[S], pD[S] = float(total[idx]), float(total[sstar]), pools[:, idx]
        require(abs(vD[frozenset()] - i["C"]) <= 1e-12 * i["C"] and abs(vD[frozenset(players)] - j["C"]) <= 1e-12 * j["C"],
                "NH3 coalition end points")
        phiD, phiF, poolD = shapley(players, vD), shapley(players, vF), shapley(players, pD)

        # first order at i's state s*
        def J(dL=0.0, price=None, mw=None):
            t, _, _ = nh3_eval(H, i["L"] + dL, i["price"] if price is None else price, i["mw"] if mw is None else mw)
            return float(t[sstar])
        eL = (math.log(J(EPS_LOGTOF)) - math.log(J(-EPS_LOGTOF))) / (2 * EPS_LOGTOF)
        ep = fd_ln(lambda p: J(price=p), i["price"])
        em = fd_ln(lambda w: J(mw=w), i["mw"])
        dA, dW = j["a"] - i["a"], float(j["w"][sstar] - i["w"][sstar])
        tL = {"U": eL * dA, "W": eL * dW, "M": ep * math.log(j["price"] / i["price"]) + em * math.log(j["mw"] / i["mw"])}
        dz = {"U": dA, "W": dW, "M": math.log(j["price"] / i["price"])}
        eps = {"U": eL, "W": eL, "M": ep}
        props = {k: dict(phi_D=phiD[k], phi_F=phiF[k], t_L=tL[k], dz=dz[k], eps=eps[k]) for k in players}
        st = lambda q: f"{H.state_T[q]:g} C, {H.state_P[q]:g} bar, Tsep {H.state_Tsep[q]:g} C"  # noqa: E731
        cases.append(dict(case=dict(system="NH3", scenario="frozen", case_id=f"NH3 {ni}-{nj}", i=ni, j=nj, C_i=i["C"],
                                    C_j=j["C"], unit="USD/t NH3", players="U W M", operating_point_i=st(sstar),
                                    operating_point_j=st(j["idx"]), eps_M_molar_mass=em),
                          props=props, pools_D=poolD, pools_i=pD[frozenset()], pools_j=pD[frozenset(players)],
                          pool_names=NH3_POOLS))
    shutil.rmtree(root, ignore_errors=True)
    return cases, dict(costs=gates, hybrids_without_feasible_state=int(fallbacks))


# ================================================================ methanol (field and Re/TiO2) ===================
COEF_EC = M.LF * (M.CRF + M.IR / 9.0 + 0.081) / 0.90 * 1e6 / M.PROD_TPY      # EUR/t per MEUR of equipment cost
FIXED_EUR_T = (M.COMMON_DIRECT_MEUR_Y + 2.2125 * M.SOURCE_OL_MEUR_Y) / 0.90 * 1e6 / M.PROD_TPY


def meoh_pools(e):
    """Exact pool split (EUR/t) of an `economics` / `candidate_economics` result (arrays)."""
    ec = e["ec"]
    cat = np.asarray(e.get("cat_repl_eur_t", 0.0)) / 0.90
    return np.vstack(np.broadcast_arrays(
        COEF_EC * ec["Reactor modules"] + cat,
        np.asarray(e["h2_eur_t"]) / 0.90, np.asarray(e["co2_eur_t"]) / 0.90, np.asarray(e["elec_eur_t"]) / 0.90,
        COEF_EC * (ec["Carbon dioxide compressor"] + ec["Hydrogen compressor"] + ec["Recycle/reflux compressor"]),
        COEF_EC * (ec["Reactor preheaters"] + ec["Heat exchangers"] + ec["Flash drums"] + ec["Distillation column"]
                   + ec["Pump"]),
        COEF_EC * (ec["Furnace & blower"] + ec["Turbine & generator"]),
        np.full(np.shape(e["cost_eur_t"]), FIXED_EUR_T)))


def meoh_hybrid(i, j, S):
    """Hybrid candidate: properties in S from j, the rest from i (players U, X, CO, CH4, S, T)."""
    h = {}
    h["STY"] = j["STY"] if "U" in S else i["STY"]
    h["X"] = j["X"] if "X" in S else i["X"]
    h["SCO"] = j["SCO"] if ("CO" in S or "S" in S) else i["SCO"]
    h["SCH4"] = j["SCH4"] if ("CH4" in S or "S" in S) else i["SCH4"]
    h["T_C"] = j["T_C"] if "T" in S else i["T_C"]
    h["P_bar"], h["h2_co2"] = i["P_bar"], i["h2_co2"]
    return h


def meoh_sweep(h, purges=None):
    sm = 1.0 - h["SCO"] - h["SCH4"]
    if sm <= 0:
        raise ValueError("S_MeOH <= 0")
    c = dict(X=h["X"], SMeOH=sm, SCH4=h["SCH4"], SCO=h["SCO"])
    return c, G.purge_sweep(c, purges=purges, STY_per_g_cat=h["STY"], x_co="recycled_central", P_bar=h["P_bar"],
                            h2_co2=h["h2_co2"], T_C=h["T_C"])


def purge_index(p):
    k = int(np.argmin(np.abs(G.PURGES - p)))
    if abs(G.PURGES[k] - p) > 1e-12:
        raise ValueError(f"purge {p} not on the grid")
    return k


def meoh_coalition_task(args):
    """One hybrid: optimum under S5 and S6 and the cost at i's S5 and S6 purge levels, with pools at each."""
    key, S, h, p5_i, p6_i = args
    try:
        c, s = meoh_sweep(h)
    except ValueError as exc:
        return key, S, dict(error=str(exc))
    cost = np.asarray(s["cost_eur_t"], dtype=float)
    ok = G.eligible_purges(s)
    fin = np.isfinite(cost)
    lv = {"S5": int(np.argmin(np.where(fin, cost, np.inf))) if fin.any() else None,
          "S6": int(np.argmin(np.where(ok, cost, np.inf))) if ok.any() else None,
          "F5": purge_index(p5_i), "F6": purge_index(p6_i)}
    names = [k for k, v in lv.items() if v is not None]
    idx = np.array([lv[k] for k in names])
    e = G.economics(np.asarray(s["X_eff"])[idx], c["SMeOH"], c["SCH4"], c["SCO"], STY_per_g_cat=h["STY"],
                    P_bar=h["P_bar"], h2_co2=h["h2_co2"], purge=G.PURGES[idx], x_co="recycled_central", T_C=h["T_C"])
    pools = meoh_pools(e)
    out = {}
    for n, k in enumerate(names):
        cs, ce = float(cost[lv[k]]), float(np.asarray(e["cost_eur_t"])[n])
        if abs(cs - ce) > 1e-9 * cs or abs(pools[:, n].sum() - cs) > 1e-9 * cs:
            return key, S, dict(error=f"pool re-evaluation mismatch at {k}: {cs} vs {ce}")
        out[k] = dict(cost=cs, purge=float(G.PURGES[lv[k]]), pools=pools[:, n])
    out["S6_none_eligible"] = lv["S6"] is None
    return key, S, out


def meoh_eps_task(args):
    """First-order elasticities of ln J at one entry's purge level (operating point frozen)."""
    key, h, p = args
    pp = np.array([p])

    def J(**kw):
        return float(np.asarray(meoh_sweep(dict(h, **kw), purges=pp)[1]["cost_eur_t"])[0])
    J0 = J()
    eps = {"U": fd_ln(lambda v: J(STY=v), h["STY"]), "X": fd_ln(lambda v: J(X=v), h["X"]),
           "CO": fd_lin(lambda v: J(SCO=v), h["SCO"], EPS_S, lower=0.0),
           "CH4": fd_lin(lambda v: J(SCH4=v), h["SCH4"], EPS_S, lower=0.0),
           "T": fd_lin(lambda v: J(T_C=v), h["T_C"], EPS_T)}
    return key, dict(J0=J0, eps=eps)


def meoh_dz(i, j):
    return {"U": math.log(j["STY"] / i["STY"]), "X": math.log(j["X"] / i["X"]), "CO": j["SCO"] - i["SCO"],
            "CH4": j["SCH4"] - i["SCH4"], "T": j["T_C"] - i["T_C"]}


def meoh_players(i, j):
    return [k for k, a, b in (("U", i["STY"], j["STY"]), ("X", i["X"], j["X"]), ("CO", i["SCO"], j["SCO"]),
                               ("CH4", i["SCH4"], j["SCH4"]), ("T", i["T_C"], j["T_C"])) if abs(a - b) > 1e-12]


def run_meoh(pool):
    cand = pd.read_csv(REPO / "analysis" / "meoh_literature_inversion_2026_10_05" / "literature_candidates.csv")
    n = cand.groupby("group").size()
    cand = cand[cand.group.isin(n[n >= 2].index)].reset_index(drop=True)
    require(cand.group.nunique() == 40 and len(cand) == 310 and cand.doi.nunique() == 28, "methanol cohort 40/310/28")
    require(cand.groupby("group").P_bar.nunique().max() == 1 and cand.groupby("group").h2_co2.nunique().max() == 1,
            "methanol: P and H2/CO2 equal within groups")
    kinds = {}
    for sc, f in (("S5", "group_metrics.csv"), ("S6", "group_metrics_inlet_limit.csv")):
        gm = pd.read_csv(REPO / "analysis" / "meoh_literature_inversion_2026_10_05" / f)
        kinds[sc] = dict(zip(gm.group, gm.get("kind", pd.Series([""] * len(gm))).fillna("")))
    SC = {"S5": ("cost_recycled_opt", "purge_recycled_opt"), "S6": ("cost_recycled_opt_inlet", "purge_recycled_opt_inlet")}
    ent = {r: dict(STY=float(x.STY), X=float(x.X), SCO=float(x.SCO), SCH4=float(x.SCH4), T_C=float(x.T_C),
                   P_bar=float(x.P_bar), h2_co2=float(x.h2_co2)) for r, x in cand.iterrows()}

    # ---- pre-registered pairs: i = cheapest of the group's top-STY entries, j = cheapest other entry
    pairs = {}
    for sc, (ccol, _) in SC.items():
        for g, d in cand.groupby("group"):
            top = d.STY.max()
            win = d[d.STY >= top - 1e-12]
            i = int(win[ccol].idxmin())
            j = int(d.drop(win.index)[ccol].idxmin())
            pairs[(sc, g)] = (i, j)
    inv_counts = {sc: sum(actual_inverted(cand.at[i, SC[sc][0]], cand.at[j, SC[sc][0]])
                          for (s, g), (i, j) in pairs.items() if s == sc) for sc in SC}
    require(inv_counts == {"S5": 15, "S6": 28}, f"methanol leader mismatches {inv_counts} != 15 / 28")

    # ---- elasticities at every entry's own purge (S5 and S6): primary cases and the all-pairs set
    tasks = [((r, sc), ent[r], float(cand.at[r, SC[sc][1]])) for r in ent for sc in SC]
    eps = dict(pool.map(meoh_eps_task, tasks, chunksize=4))
    for (r, sc), e in eps.items():
        require(abs(e["J0"] - cand.at[r, SC[sc][0]]) <= 1e-6, f"methanol entry {r} {sc}: cost at own purge")

    # ---- coalitions (exact and fixed design), one set per unique (i, j) and player set
    def coalition_tasks(pair_players):
        out = []
        for (i, j), players in pair_players.items():
            for S in coalitions(players):
                out.append(((i, j, tuple(players)), S, meoh_hybrid(ent[i], ent[j], S),
                            float(cand.at[i, SC["S5"][1]]), float(cand.at[i, SC["S6"][1]])))
        return out
    full = {(i, j): meoh_players(ent[i], ent[j]) for (i, j) in set(pairs.values())}
    res = {}
    for key, S, r in pool.map(meoh_coalition_task, coalition_tasks(full), chunksize=2):
        res.setdefault(key, {})[S] = r

    def usable(key, sc):
        rs = res.get(key, {})
        return bool(rs) and not any("error" in r or (sc == "S6" and r["S6_none_eligible"]) for r in rs.values())
    merged = {}
    for (sc, g), (i, j) in pairs.items():
        pl = full[(i, j)]
        if not usable((i, j, tuple(pl)), sc) and "CO" in pl and "CH4" in pl:
            merged[(i, j)] = [p for p in pl if p not in ("CO", "CH4", "T")] + ["S"] + (["T"] if "T" in pl else [])
    if merged:
        for key, S, r in pool.map(meoh_coalition_task, coalition_tasks(merged), chunksize=2):
            res.setdefault(key, {})[S] = r

    cases, undefined = [], []
    for (sc, g), (i, j) in sorted(pairs.items()):
        ccol, pcol = SC[sc]
        Ci, Cj = float(cand.at[i, ccol]), float(cand.at[j, ccol])
        key = (i, j, tuple(full[(i, j)]))
        fb = False
        if not usable(key, sc) and (i, j) in merged:
            key, fb = (i, j, tuple(merged[(i, j)])), True
        players = list(key[2])
        e_i = eps[(i, sc)]["eps"]
        dz = meoh_dz(ent[i], ent[j])
        tL = {k: (e_i[k] * dz[k] if k != "S" else e_i["CO"] * dz["CO"] + e_i["CH4"] * dz["CH4"]) for k in players}
        base = dict(system="MeOH", scenario=sc, case_id=f"MeOH {sc} | {g}", group=g, doi=cand.at[i, "doi"],
                    i=cand.at[i, "catalyst"], j=cand.at[j, "catalyst"], C_i=Ci, C_j=Cj, unit="EUR/t MeOH",
                    players=" ".join(players), merged_selectivity=fb, kind=kinds[sc].get(g, ""),
                    T_i=ent[i]["T_C"], T_j=ent[j]["T_C"], purge_i=float(cand.at[i, pcol]),
                    purge_j=float(cand.at[j, pcol]))
        if not usable(key, sc):
            undefined.append(base["case_id"])
            props = {k: dict(phi_D=np.nan, phi_F=np.nan, t_L=tL[k], dz=dz.get(k, np.nan), eps=e_i.get(k, np.nan))
                     for k in players}
            cases.append(dict(case=dict(base, decomposition_defined=False), props=props, pools_D=None, pools_i=None,
                              pools_j=None, pool_names=MEOH_POOLS))
            continue
        rs = res[key]
        F = "F5" if sc == "S5" else "F6"
        vD = {S: r[sc]["cost"] for S, r in rs.items()}
        vF = {S: r[F]["cost"] for S, r in rs.items()}
        pD = {S: r[sc]["pools"] for S, r in rs.items()}
        e0, e1 = frozenset(), frozenset(players)
        require(abs(vD[e0] - Ci) <= 1e-6 and abs(vD[e1] - Cj) <= 1e-6, f"methanol {sc} {g}: coalition end points")
        require(abs(vF[e0] - Ci) <= 1e-6, f"methanol {sc} {g}: fixed-design origin")
        phiD, phiF, poolD = shapley(players, vD), shapley(players, vF), shapley(players, pD)
        props = {k: dict(phi_D=phiD[k], phi_F=phiF[k], t_L=tL[k], dz=dz.get(k, np.nan),
                         eps=e_i.get(k, np.nan)) for k in players}
        cases.append(dict(case=dict(base, decomposition_defined=True, purge_j_hybrid_check=rs[e1][sc]["purge"]),
                          props=props, pools_D=poolD, pools_i=pD[e0], pools_j=pD[e1], pool_names=MEOH_POOLS))

    # ---- secondary: every STY-ordered within-group pair, criterion C1 only
    prs = []
    for sc, (ccol, _) in SC.items():
        for g, d in cand.groupby("group"):
            for a, b in combinations(d.index, 2):
                sa, sb = cand.at[a, "STY"], cand.at[b, "STY"]
                if abs(sa - sb) <= 1e-9 * max(abs(sa), abs(sb)):
                    continue
                if sa < sb:
                    a, b = b, a
                dz = meoh_dz(ent[a], ent[b])
                e_a = eps[(a, sc)]["eps"]
                t = {k: e_a[k] * dz[k] for k in dz}
                U, O = t["U"], sum(v for k, v in t.items() if k != "U")
                inv = actual_inverted(cand.at[a, ccol], cand.at[b, ccol])
                prs.append(dict(scenario=sc, group=g, doi=cand.at[a, "doi"], i=cand.at[a, "catalyst"],
                                j=cand.at[b, "catalyst"], C_i=cand.at[a, ccol], C_j=cand.at[b, ccol],
                                actual_inverted=inv, U_L=U, O_L=O, pred_L=predict(U, O), **{f"t_{k}": v for k, v in t.items()}))
    prs = pd.DataFrame(prs)
    frozen_inv = {}
    for sc, f in (("S5", "group_metrics.csv"), ("S6", "group_metrics_inlet_limit.csv")):
        gm = pd.read_csv(REPO / "analysis" / "meoh_literature_inversion_2026_10_05" / f)
        frozen_inv[sc] = int(gm.inversions.sum())
    got = {sc: int(prs[prs.scenario == sc].actual_inverted.sum()) for sc in SC}
    require(got == frozen_inv, f"methanol pairwise inversions {got} != frozen {frozen_inv}")
    return cases, prs, dict(leader_mismatches=inv_counts, pairwise_inversions=frozen_inv,
                            merged_selectivity_cases=int(sum(c["case"].get("merged_selectivity", False) for c in cases)),
                            undefined_cases=undefined, unique_pairs=len(full))


def re_case(a, b, ka, kb):
    """Re/TiO2 D01 v3 canonical (inert CO, 2 % purge): players U (STY/gRe), L (loading), X, CO, CH4."""
    def ev(h):
        e = M.candidate_economics(h["X"], 1.0 - h["SCO"] - h["SCH4"], h["SCH4"], h["SCO"], h["STY"], h["Re_wt"])
        return float(e["cost_eur_t"]), meoh_pools(e)[:, 0] if np.ndim(e["cost_eur_t"]) == 0 else None

    def hyb(S):
        return dict(STY=(b if "U" in S else a)["STY"], Re_wt=(b if "L" in S else a)["Re_wt"],
                    X=(b if "X" in S else a)["X"], SCO=(b if "CO" in S else a)["SCO"],
                    SCH4=(b if "CH4" in S else a)["SCH4"])
    players = [k for k, x, y in (("U", a["STY"], b["STY"]), ("L", a["Re_wt"], b["Re_wt"]), ("X", a["X"], b["X"]),
                                 ("CO", a["SCO"], b["SCO"]), ("CH4", a["SCH4"], b["SCH4"])) if abs(x - y) > 1e-12]
    v, p = {}, {}
    for S in coalitions(players):
        v[S], p[S] = ev(hyb(S))
    phi, pphi = shapley(players, v), shapley(players, p)

    def J(**kw):
        return ev(dict(hyb(frozenset()), **kw))[0]
    eps = {"U": fd_ln(lambda x: J(STY=x), a["STY"]), "L": fd_ln(lambda x: J(Re_wt=x), a["Re_wt"]),
           "X": fd_ln(lambda x: J(X=x), a["X"]), "CO": fd_lin(lambda x: J(SCO=x), a["SCO"], EPS_S, lower=0.0),
           "CH4": fd_lin(lambda x: J(SCH4=x), a["SCH4"], EPS_S, lower=0.0)}
    dz = {"U": math.log(b["STY"] / a["STY"]), "L": math.log(b["Re_wt"] / a["Re_wt"]), "X": math.log(b["X"] / a["X"]),
          "CO": b["SCO"] - a["SCO"], "CH4": b["SCH4"] - a["SCH4"]}
    props = {k: dict(phi_D=phi[k], phi_F=phi[k], t_L=eps[k] * dz[k], dz=dz[k], eps=eps[k]) for k in players}
    e0, e1 = frozenset(), frozenset(players)
    return dict(case=dict(system="Re", scenario="D01 v3, 2 % purge", case_id=f"Re {ka} vs {kb}", i=ka, j=kb,
                          C_i=v[e0], C_j=v[e1], unit="EUR/t MeOH", players=" ".join(players)),
                props=props, pools_D=pphi, pools_i=p[e0], pools_j=p[e1], pool_names=MEOH_POOLS)


def run_re():
    F = M.FROZEN
    expect = {"5wtRe_200C": 943.30, "1wtRe_250C": 961.51, "1wtRe_200C": 966.96, "5wtRe_250C": 1258.17}
    for k, c in F.items():
        cc = float(M.cost(c)["cost_eur_t"])
        require(round(cc, 2) == expect[k], f"Re/TiO2 {k}: {cc:.4f} vs {expect[k]}")
        h = dict(STY=c["STY"], Re_wt=c["Re_wt"], X=c["X"], SCO=c["SCO"], SCH4=c["SCH4"])
        e = M.candidate_economics(h["X"], 1.0 - h["SCO"] - h["SCH4"], h["SCH4"], h["SCO"], h["STY"], h["Re_wt"])
        require(abs(float(e["cost_eur_t"]) - cc) <= 1e-9 * cc, f"Re/TiO2 {k}: closure-based selectivity")
    keys = sorted(F, key=lambda k: -F[k]["STY"])
    cases = []
    for a, b in combinations(keys, 2):
        ha = dict(STY=F[a]["STY"], Re_wt=F[a]["Re_wt"], X=F[a]["X"], SCO=F[a]["SCO"], SCH4=F[a]["SCH4"])
        hb = dict(STY=F[b]["STY"], Re_wt=F[b]["Re_wt"], X=F[b]["X"], SCO=F[b]["SCO"], SCH4=F[b]["SCH4"])
        cases.append(re_case(ha, hb, a, b))
    return cases, {k: round(float(M.cost(c)["cost_eur_t"]), 2) for k, c in F.items()}


# ================================================================ scoring ========================================
def finish_case(c):
    """Criteria, outcome and regret attribution for one case record."""
    k = c["case"]
    props = c["props"]
    Ci, Cj = k["C_i"], k["C_j"]
    k["actual_inverted"] = actual_inverted(Ci, Cj)
    k["regret_rel"] = (Ci - Cj) / Cj if k["actual_inverted"] else 0.0
    k["dlnC_actual"] = math.log(Cj / Ci)
    for t, col, scale in (("L", "t_L", 1.0), ("F", "phi_F", max(Ci, Cj)), ("D", "phi_D", max(Ci, Cj))):
        U = props["U"][col]
        O = sum(v[col] for p, v in props.items() if p != "U")
        k[f"U_{t}"], k[f"O_{t}"] = U, O
        k[f"pred_{t}"] = predict(U, O, scale) if np.isfinite(U + O) else None
        k[f"correct_{t}"] = (k[f"pred_{t}"] == k["actual_inverted"]) if k[f"pred_{t}"] is not None else None
    if c["pools_D"] is not None:
        k["D_efficiency_error_rel"] = abs(k["U_D"] + k["O_D"] - (Cj - Ci)) / max(Ci, Cj)
        require(k["D_efficiency_error_rel"] <= 1e-9, f"{k['case_id']}: Shapley efficiency")
        require(abs(c["pools_i"].sum() - Ci) <= 1e-9 * Ci and abs(c["pools_j"].sum() - Cj) <= 1e-9 * Cj,
                f"{k['case_id']}: pools sum")
    k["R_hat_L"] = Ci * (1.0 - math.exp(k["U_L"] + k["O_L"]))      # first-order predicted C_i - C_j
    if k["actual_inverted"] and c["pools_D"] is not None:
        R = Ci - Cj
        others = {p: v["phi_D"] for p, v in props.items() if p != "U"}
        ks = min(others, key=others.get)
        k["carrying_property"] = ks
        k["carrying_class"] = CLASS[ks]
        k["carrying_share_of_regret"] = -others[ks] / R
        k["upstream_share_of_regret"] = -props["U"]["phi_D"] / R
        names = c["pool_names"]
        dpool = c["pools_i"] - c["pools_j"]
        path = NH3_PATHWAY if k["system"] == "NH3" else (MEOH_PATHWAY if k["system"] in ("MeOH", "Re") else set())
        k["pathway_pool_share_of_regret"] = float(sum(dpool[n] for n, p in enumerate(names) if p in path) / R)
        cp = -np.asarray(c["pools_D"][ks]) / R
        k["carrying_property_pool_split"] = "; ".join(f"{names[n]} {cp[n]:+.3f}" for n in np.argsort(-np.abs(cp))[:4])
        k["regret_pool_split"] = "; ".join(f"{names[n]} {dpool[n] / R:+.3f}" for n in np.argsort(-np.abs(dpool))[:4])
    return c


def main():
    t0 = time.time()
    au_cases, au_draws = run_au()
    nh3_cases, nh3_info = run_nh3()
    re_cases, re_costs = run_re()
    with Pool(WORKERS) as pool:
        me_cases, prs, me_info = run_meoh(pool)
    allc = [finish_case(c) for c in au_cases + nh3_cases + me_cases + re_cases]

    cases = pd.DataFrame([c["case"] for c in allc])
    prop_rows, pool_rows = [], []
    for c in allc:
        k = c["case"]
        sysname = k["system"]
        tot = sum(abs(v["phi_D"]) for v in c["props"].values())
        for p, v in c["props"].items():
            prop_rows.append(dict(case_id=k["case_id"], system=sysname, scenario=k["scenario"], property=p,
                                  property_name=NAME[sysname].get(p, p), property_class=CLASS[p],
                                  actual_inverted=k["actual_inverted"], C_i=k["C_i"],
                                  phi_D=v["phi_D"], phi_F=v["phi_F"], t_L=v["t_L"], delta_z=v["dz"], eps_at_i=v["eps"],
                                  phi_D_pct_of_Ci=100 * v["phi_D"] / k["C_i"],
                                  phi_D_share_of_abs_total=v["phi_D"] / tot if tot > 0 else np.nan))
        if c["pools_D"] is not None:
            for p, arr in c["pools_D"].items():
                for n, name in enumerate(c["pool_names"]):
                    pool_rows.append(dict(case_id=k["case_id"], system=sysname, scenario=k["scenario"], property=p,
                                          pool=name, pool_class=POOL_CLASS[name], phi_D=float(np.asarray(arr)[n])))
            for n, name in enumerate(c["pool_names"]):
                pool_rows.append(dict(case_id=k["case_id"], system=sysname, scenario=k["scenario"],
                                      property="(C_j - C_i)", pool=name, pool_class=POOL_CLASS[name],
                                      phi_D=float(c["pools_j"][n] - c["pools_i"][n])))
    order = ["system", "scenario", "case_id", "group", "doi", "kind", "i", "j", "unit", "C_i", "C_j", "actual_inverted",
             "regret_rel", "dlnC_actual", "players", "U_L", "O_L", "pred_L", "correct_L", "U_F", "O_F", "pred_F",
             "correct_F", "U_D", "O_D", "pred_D", "correct_D", "R_hat_L", "carrying_property", "carrying_class",
             "carrying_share_of_regret", "upstream_share_of_regret", "pathway_pool_share_of_regret",
             "carrying_property_pool_split", "regret_pool_split"]
    cols = [c for c in order if c in cases.columns] + [c for c in cases.columns if c not in order]
    cases[cols].to_csv(HERE / "cases.csv", index=False, float_format="%.12g")
    pd.DataFrame(prop_rows).to_csv(HERE / "properties.csv", index=False, float_format="%.12g")
    pd.DataFrame(pool_rows).to_csv(HERE / "pools.csv", index=False, float_format="%.12g")
    prs.to_csv(HERE / "meoh_pairwise.csv", index=False, float_format="%.12g")
    record = dict(au_draws=au_draws,
                  gates=dict(au_draws_full_rank_preserved=au_draws["full_rank_preserved_draws"], nh3=nh3_info,
                             re_costs=re_costs, meoh=me_info),
                  runtime_s=round(time.time() - t0, 1), workers=WORKERS)
    (HERE / "run_record.json").write_text(json.dumps(record, indent=1, default=float) + "\n", encoding="utf-8")
    print(f"computation done in {time.time() - t0:.0f} s")
    sys.path.insert(0, str(HERE))
    import score_leverage_criterion
    score_leverage_criterion.main()


if __name__ == "__main__":
    main()
