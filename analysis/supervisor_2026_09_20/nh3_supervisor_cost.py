"""NH3 supervisor cost analyses of 2026-09-20 on the selected ammonia model.

Produces, for the model chosen by NH3_MODEL (analysis/nh3_model.py):
    nh3_ru_price_equalization.json   Ru metal price set to the Fe price (8 USD/kg), Ru re-optimized over the full library
    nh3_cost_decomposition.csv       Fe / Ru canonical cost pools, Ru - Fe, and the equal-price Ru pools
    nh3_cost_mc_summary.json         preregistered joint cost-parameter Monte Carlo (docs/SUPERVISOR_COST_MC_PREREG_2026-09-20.md)
    nh3_cost_mc_histogram.csv        histogram table of Ru - Fe and alpha* read by figures/nh3/render_F03_uncertainty_cost_mc.R
    f3_panel_summary.csv             F03 panel metrics (descriptor MC of the canonical closure + the cost MC above)
    nh3_cost_mc_draws.csv            draw-level table (prereg output 4); written for 1.2 and with --out only

    NH3_MODEL=1.1 (default)  recompute and compare with the committed files of this folder; the frozen files are never
                             overwritten. Writes nh3_v11_reproduction_check.json here (and the files to --out if given).
    NH3_MODEL=1.2            write everything to nh3_1_2/ plus nh3_1_2/README.md (1.1 -> 1.2 table).

Definitions (identical for both models):
    cost(draw) = metal + CAPEX_mult * (reactor base + vessel pressure premium + compressor CAPEX)
                 + (electricity / canonical electricity) * (fresh + recycle compression + refrigeration),
    minimized over the full process-state library subject to the bed cap (V <= 90 m3);
    metal price multipliers log-uniform [0.5, 2] (Fe and Ru independent), CAPEX U(0.8, 1.2), electricity U(20, 100)
    USD/MWh, catalyst life U(5, 20) y, shared within a draw; N = 5,000, seed 20260920, sampled as whole vectors in that
    order; alpha* = Ru activity multiplier at which the re-optimized Ru cost equals the same draw's re-optimized Fe cost,
    solved as in the harness (brentq on log10 alpha over [-6, 12], xtol 1e-11, infeasible -> 1e100).
alpha* is solved on the Ru states not dominated in (1/TOF, P, electricity duty, compressor CAPEX), which cannot change the
minimum; every 25th draw from draw 25 (199 draws) is re-solved on the full library as a check.

Response surfaces are read from <harness root>/cache and never rebuilt (set NH3_HARNESS / NH3_HARNESS_1_2).

    python -X utf8 analysis/supervisor_2026_09_20/nh3_supervisor_cost.py            # NH3_MODEL=1.1 check
    NH3_MODEL=1.2 python -X utf8 analysis/supervisor_2026_09_20/nh3_supervisor_cost.py
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import brentq

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "analysis"))
import nh3_model as NM  # noqa: E402

N_DRAWS = 5000
SEED = 20260920
CHECK_DRAWS = list(range(25, N_DRAWS, 25))  # 199 draws re-solved on the full library
POOLS = [("metal_inventory", "metal_cost"), ("reactor_base", "reactor_base"),
         ("vessel_pressure_premium", "vessel_pressure_premium"), ("fresh_compression_electricity", "fresh_comp"),
         ("recycle_compression_electricity", "recycle_comp"), ("refrigeration_electricity", "refrigeration"),
         ("compressor_CAPEX", "compressor_capex")]


# ----------------------------------------------------------------------------------------------------------------------
# model
# ----------------------------------------------------------------------------------------------------------------------
def load_model():
    h = NM.harness()
    HC = NM.core()
    cp = h.response_cache_path()
    if not cp.exists():
        sys.exit(f"STOP: response surface {cp} not found. It is never rebuilt here; set "
                 f"{'NH3_HARNESS' if NM.VERSION == '1.1' else 'NH3_HARNESS_1_2'} to the harness root that holds it.")
    z = np.load(cp)
    resp, eg = z["response"], z["EGRID"]
    if resp.shape != (h.NSTATE, len(h.EGRID)) or not np.allclose(eg, h.EGRID):
        sys.exit(f"STOP: response surface {cp} does not match the library ({resp.shape} vs {h.NSTATE} states).")
    vec = {m: h.interp_state_vector(resp, h.EN0[m]) for m in ("Fe", "Ru")}
    return h, HC, vec, cp


class CostModel:
    def __init__(self, h, HC, vec):
        self.h, self.HC, self.vec = h, HC, vec
        self.opex = h.state_fresh + h.state_reccomp + h.state_refrig

    def evaluate(self, metal, *, price=None, life_y=None, alpha=1.0, capex_multiplier=1.0, electricity=None):
        """Re-optimized cost of one metal over the full library, with its cost pools at the optimum."""
        h, HC = self.h, self.HC
        price = HC.PRICE[metal] if price is None else price
        life_y = h.CATALYST_LIFE_Y if life_y is None else life_y
        electricity = h.ELECTRICITY if electricity is None else electricity
        _, V, metal_cost, reactor = h.cost_arrays(metal, self.vec[metal], price=price, life_y=life_y, alpha=alpha)
        s = float(electricity) / h.ELECTRICITY
        total = metal_cost + capex_multiplier * (reactor + h.state_compcapex) + self.opex * s
        ok = V <= h.V_CAP
        if not np.any(ok):
            return None
        i = int(np.argmin(np.where(ok, total, np.inf)))
        vi = float(V[i])
        base = float((h.REACTOR_FIXED + h.REACTOR_VAR * (vi / h.REACTOR_REF) ** h.REACTOR_EXP) * h.crf / h.annual_output_t)
        bd = {"metal_cost": float(metal_cost[i]), "reactor_base": base * capex_multiplier,
              "vessel_pressure_premium": (float(reactor[i]) - base) * capex_multiplier,
              "fresh_comp": float(h.state_fresh[i]) * s, "recycle_comp": float(h.state_reccomp[i]) * s,
              "refrigeration": float(h.state_refrig[i]) * s, "compressor_capex": float(h.state_compcapex[i]) * capex_multiplier}
        return {"total_cost": float(total[i]), "V_m3": vi, "T_C": float(h.state_T[i]), "P_bar": float(h.state_P[i]),
                "Tsep_C": float(h.state_Tsep[i]), "state_index": i, "breakdown": bd}

    def ru_total_fn(self, sel):
        """Minimum Ru cost over the states `sel` (same arithmetic as harness cost_arrays + the evaluate() total)."""
        h, HC = self.h, self.HC
        lt, P, op, cc = self.vec["Ru"][sel], h.state_P[sel], self.opex[sel], h.state_compcapex[sel]
        k0 = h.nh3_mol_s * HC.MW["Ru"] / h.F_CAL * np.power(10.0, -lt)
        denom = 2.0 * (h.PC_V_SE - 0.6 * P)

        def f(price, life_y, alpha, cap, elec):
            active = k0 / alpha
            V = active / h.ACTIVE_FRACTION / h.BED_DENSITY
            metal = active * price * (1.0 - h.METAL_RECOVERY) / life_y / h.annual_output_t
            vpp = np.zeros_like(V)
            if h.PCAPEX_ENABLED:
                Vd = np.maximum(V, h.PC_V_AMIN)
                D = np.power(4.0 * Vd / (math.pi * h.PC_V_LD), 1.0 / 3.0)
                t = np.where(denom > 0.0, P * D / np.where(denom > 0.0, denom, 1.0) + h.PC_V_CA, np.inf)
                Fp = np.maximum(t / h.PC_V_TMIN, 1.0)
                cp0 = h.turton_cp0(h.PC_VK, Vd, h.PC_V_AMIN, h.PC_V_AMAX, h.PC_V_NEXP)
                vpp = cp0 * h.PC_V_B2 * h.PC_V_FM * (Fp - 1.0) * h.PC_INDEX_RATIO * h.crf / h.annual_output_t
            reactor = (h.REACTOR_FIXED + h.REACTOR_VAR * np.power(V / h.REACTOR_REF, h.REACTOR_EXP)) * h.crf / h.annual_output_t + vpp
            total = metal + cap * (reactor + cc) + op * (elec / h.ELECTRICITY)
            ok = V <= h.V_CAP
            return float(np.min(np.where(ok, total, np.inf))) if np.any(ok) else math.inf
        return f

    def ru_nondominated(self):
        """Ru states not dominated in (1/TOF, P, electricity duty, compressor CAPEX). Every cost pool is nondecreasing in
        each of these, so a dominated state can never be cheaper than the state dominating it."""
        h = self.h
        k, P, op, cc = -self.vec["Ru"], h.state_P, self.opex, h.state_compcapex
        keep = np.ones(h.NSTATE, bool)
        for i in range(h.NSTATE):
            le = (k <= k[i]) & (P <= P[i]) & (op <= op[i]) & (cc <= cc[i])
            lt = (k < k[i]) | (P < P[i]) | (op < op[i]) | (cc < cc[i])
            keep[i] = not np.any(le & lt)
        return np.where(keep)[0]


def solve_alpha(f, target, ru_price, life, cap, elec):
    def gap(loga):
        v = f(ru_price, life, 10.0 ** loga, cap, elec)
        return (v if math.isfinite(v) else 1e100) - target
    return float(10.0 ** brentq(gap, -6.0, 12.0, xtol=1e-11))


# ----------------------------------------------------------------------------------------------------------------------
# analyses
# ----------------------------------------------------------------------------------------------------------------------
def price_equalization(cm, A, nstate, extra):
    HC = cm.HC
    fe, ru = cm.evaluate("Fe"), cm.evaluate("Ru")
    rq = cm.evaluate("Ru", price=HC.PRICE["Fe"])
    out = {"schema": "nh3-ru-price-equalization-v1", "date": extra.get("date", "2026-09-20")}
    out.update({k: v for k, v in extra.items() if k != "date"})
    out["baseline_reproduction"] = {
        "Fe_cost_abs_error_USD_t": abs(fe["total_cost"] - A["Fe"]),
        "Ru_cost_abs_error_USD_t": abs(ru["total_cost"] - A["Ru"]),
        "Fe_optimum_match": (fe["T_C"], fe["P_bar"], fe["Tsep_C"]) == tuple(A["Fe_optimum"]),
        "Ru_optimum_match": (ru["T_C"], ru["P_bar"], ru["Tsep_C"]) == tuple(A["Ru_optimum"])}
    st = lambda e: {"T_C": e["T_C"], "P_bar": e["P_bar"], "Tsep_C": e["Tsep_C"], "V_m3": e["V_m3"]}
    out["Fe_canonical"] = {"total_cost_USD_t": fe["total_cost"], **st(fe)}
    out["Ru_canonical"] = {"price_USD_kg": HC.PRICE["Ru"], "total_cost_USD_t": ru["total_cost"], **st(ru)}
    out["Ru_price_equalized_to_Fe"] = {"price_USD_kg": HC.PRICE["Fe"], "total_cost_USD_t": rq["total_cost"], **st(rq),
                                       "breakdown_USD_t": rq["breakdown"]}
    out["Ru_minus_Fe_USD_t"] = rq["total_cost"] - fe["total_cost"]
    out["economic_order_after_equalization"] = "Ru < Fe" if rq["total_cost"] < fe["total_cost"] else "Fe <= Ru"
    out["process_state_count"] = nstate
    return out, fe, ru, rq


def decomposition_rows(fe, ru, rq):
    rows = [["cost_pool", "Fe_canonical_USD_t", "Ru_canonical_USD_t", "Ru_minus_Fe_USD_t", "Ru_equal_price_reoptimized_USD_t"]]
    for pool, key in POOLS:
        a, b, c = fe["breakdown"][key], ru["breakdown"][key], rq["breakdown"][key]
        rows.append([pool, a, b, b - a, c])
    tf = sum(fe["breakdown"][k] for _, k in POOLS)
    tr = sum(ru["breakdown"][k] for _, k in POOLS)
    tq = sum(rq["breakdown"][k] for _, k in POOLS)
    rows.append(["TOTAL", tf, tr, tr - tf, tq])
    return rows


def cost_mc(cm, log=print):
    h, HC = cm.h, cm.HC
    rng = np.random.default_rng(SEED)
    lo, hi = math.log(0.5), math.log(2.0)
    fe_pm = np.exp(rng.uniform(lo, hi, N_DRAWS))
    ru_pm = np.exp(rng.uniform(lo, hi, N_DRAWS))
    cap = rng.uniform(0.8, 1.2, N_DRAWS)
    elec = rng.uniform(20.0, 100.0, N_DRAWS)
    life = rng.uniform(5.0, 20.0, N_DRAWS)
    sub = cm.ru_nondominated()
    f_sub, f_full = cm.ru_total_fn(sub), cm.ru_total_fn(np.arange(h.NSTATE))
    log(f"  alpha*: {len(sub)} non-dominated Ru states of {h.NSTATE}")
    rows = []
    for d in range(N_DRAWS):
        fe_d = cm.evaluate("Fe", price=HC.PRICE["Fe"] * fe_pm[d], life_y=life[d], capex_multiplier=cap[d], electricity=elec[d])
        ru_d = cm.evaluate("Ru", price=HC.PRICE["Ru"] * ru_pm[d], life_y=life[d], capex_multiplier=cap[d], electricity=elec[d])
        alpha = solve_alpha(f_sub, fe_d["total_cost"], HC.PRICE["Ru"] * ru_pm[d], life[d], cap[d], elec[d])
        rows.append({"draw": d, "Fe_price_multiplier": float(fe_pm[d]), "Ru_price_multiplier": float(ru_pm[d]),
                     "capex_multiplier": float(cap[d]), "electricity_USD_MWh": float(elec[d]), "catalyst_life_y": float(life[d]),
                     "Fe_cost_USD_t": fe_d["total_cost"], "Ru_cost_USD_t": ru_d["total_cost"],
                     "Ru_minus_Fe_USD_t": ru_d["total_cost"] - fe_d["total_cost"], "alpha_star": alpha,
                     "Fe_T_C": fe_d["T_C"], "Fe_P_bar": fe_d["P_bar"], "Fe_Tsep_C": fe_d["Tsep_C"],
                     "Ru_T_C": ru_d["T_C"], "Ru_P_bar": ru_d["P_bar"], "Ru_Tsep_C": ru_d["Tsep_C"]})
        if (d + 1) % 1000 == 0:
            log(f"  cost MC draws {d + 1}/{N_DRAWS}")
    err = 0.0
    for d in CHECK_DRAWS:
        r = rows[d]
        a_full = solve_alpha(f_full, r["Fe_cost_USD_t"], HC.PRICE["Ru"] * r["Ru_price_multiplier"], r["catalyst_life_y"],
                             r["capex_multiplier"], r["electricity_USD_MWh"])
        err = max(err, abs(a_full - r["alpha_star"]) / r["alpha_star"])
    return rows, {"n_checked": len(CHECK_DRAWS), "max_alpha_relative_error": err}


def cost_mc_summary(rows, check, extra):
    fe = np.array([r["Fe_cost_USD_t"] for r in rows]); ru = np.array([r["Ru_cost_USD_t"] for r in rows])
    g = ru - fe; a = np.array([r["alpha_star"] for r in rows])
    q = lambda x, ps: {k: float(np.quantile(x, p)) for k, p in ps}
    p3 = [("p05", .05), ("p50", .5), ("p95", .95)]
    out = {"schema": "supervisor-cost-mc-v1", "date": extra.get("date", "2026-09-20")}
    out.update({k: v for k, v in extra.items() if k != "date"})
    out.update({
        "draws": len(rows), "seed": SEED, "preregistration": "docs/SUPERVISOR_COST_MC_PREREG_2026-09-20.md",
        "priors": {"Fe_price_multiplier": "log-uniform[0.5,2.0]", "Ru_price_multiplier": "log-uniform[0.5,2.0]",
                   "CAPEX_multiplier": "uniform[0.8,1.2], common within draw",
                   "electricity_USD_MWh": "uniform[20,100], common within draw",
                   "catalyst_lifetime_y": "uniform[5,20], common within draw"},
        # key name kept from the 1.1 schema so downstream readers work unchanged; the library size is process_state_count
        "full_14136_state_direct_cost_verification": {
            "P_C_Fe_lt_C_Ru": float(np.mean(fe < ru)), "count_Fe_lt_Ru": int(np.sum(fe < ru)),
            "count_Ru_le_Fe": int(np.sum(ru <= fe)), "minimum_Ru_minus_Fe_USD_t": float(np.min(g)),
            "Ru_minus_Fe_USD_t_quantiles": q(g, p3)},
        "Fe_cost_USD_t_quantiles": q(fe, p3), "Ru_cost_USD_t_quantiles": q(ru, p3),
        "alpha_star": {**q(a, [("p05", .05), ("p10", .10), ("p25", .25), ("p50", .5), ("p75", .75), ("p90", .90), ("p95", .95)]),
                       "mean": float(np.mean(a)), "min": float(np.min(a)), "max": float(np.max(a))},
        "P_Ru_le_Fe_at_alpha_1": float(np.mean(ru <= fe)),
        "alpha_subset_validation_against_full_library": check})
    return out


def histogram_rows(rows):
    g = np.array([r["Ru_minus_Fe_USD_t"] for r in rows]); a = np.array([r["alpha_star"] for r in rows])
    de = np.linspace(g.min(), g.max(), 31); dc, _ = np.histogram(g, bins=de)
    ae = np.geomspace(a.min() * 0.95, a.max() * 1.03, 30); ac, _ = np.histogram(a, bins=ae)
    out = [["delta_left", "delta_right", "delta_count", "alpha_left", "alpha_right", "alpha_count"]]
    for i in range(max(len(dc), len(ac))):
        d = [float(de[i]), float(de[i + 1]), int(dc[i])] if i < len(dc) else ["", "", ""]
        x = [float(ae[i]), float(ae[i + 1]), int(ac[i])] if i < len(ac) else ["", "", ""]
        out.append(d + x)
    return out


def f3_rows(rows, A):
    res = json.loads((NM.run_dir() / "results.json").read_text(encoding="utf-8"))["monte_carlo"]
    with (NM.run_dir() / "closure" / "mc_draws.csv").open(encoding="utf-8") as fh:
        draws = list(csv.DictReader(fh))
    fe_top1 = sum(r["economic_winner"] == "Fe" for r in draws) / len(draws)
    g = np.array([r["Ru_minus_Fe_USD_t"] for r in rows]); a = np.array([r["alpha_star"] for r in rows])
    fe = np.array([r["Fe_cost_USD_t"] for r in rows]); ru = np.array([r["Ru_cost_USD_t"] for r in rows])
    return [["metric", "value", "unit"],
            ["Fe_feasible_descriptor_MC", res["Fe_feasibility_probability"], "fraction"],
            ["Fe_economic_top1_descriptor_MC", fe_top1, "fraction"],
            ["top1_survival_descriptor_MC", res["top1_survival"], "fraction"],
            ["Fe_top3_actionable_descriptor_MC", round(res["top3_actionable"], 12), "fraction"],
            ["P_C_Fe_lt_C_Ru_cost_MC", float(np.mean(fe < ru)), "fraction"],
            ["min_Ru_minus_Fe_cost_MC", float(np.min(g)), "USD/t NH3"],
            ["median_Ru_minus_Fe_cost_MC", float(np.median(g)), "USD/t NH3"],
            ["alpha_star_p05", float(np.quantile(a, .05)), "fold"],
            ["alpha_star_median", float(np.quantile(a, .5)), "fold"],
            ["alpha_star_p95", float(np.quantile(a, .95)), "fold"],
            ["alpha_star_canonical", A["alpha"], "fold"]]


# ----------------------------------------------------------------------------------------------------------------------
# serialisation and comparison
# ----------------------------------------------------------------------------------------------------------------------
def csv_text(rows):
    buf = io.StringIO()
    csv.writer(buf, lineterminator="\n").writerows(rows)
    return buf.getvalue()


def json_text(obj):
    return json.dumps(obj, indent=2)


def _num(s):
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def compare_tree(a, b, path="", out=None):
    """Max relative difference of numeric leaves; non-numeric leaves and structure must be equal."""
    out = out if out is not None else {"max_rel": 0.0, "where": None, "mismatch": []}
    if isinstance(a, dict) and isinstance(b, dict):
        if set(a) != set(b):
            out["mismatch"].append(f"{path}: keys {sorted(set(a) ^ set(b))}")
        for k in set(a) & set(b):
            compare_tree(a[k], b[k], f"{path}/{k}", out)
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            out["mismatch"].append(f"{path}: length {len(a)} vs {len(b)}")
        for i, (x, y) in enumerate(zip(a, b)):
            compare_tree(x, y, f"{path}[{i}]", out)
    elif isinstance(a, bool) or isinstance(b, bool) or _num(a) is None or _num(b) is None:
        if a != b:
            out["mismatch"].append(f"{path}: {a!r} vs {b!r}")
    else:
        x, y = _num(a), _num(b)
        if (isinstance(a, int) and not isinstance(a, bool)) and (isinstance(b, int) and not isinstance(b, bool)) and x != y:
            out["mismatch"].append(f"{path}: {a} vs {b}")
        r = 0.0 if x == y else abs(x - y) / max(abs(x), abs(y))
        if r > out["max_rel"]:
            out["max_rel"], out["where"] = r, path
    return out


def csv_cells(text):
    rows = list(csv.reader(io.StringIO(text)))
    return [[(int(c) if c.lstrip("-").isdigit() else c) for c in r] for r in rows]


def build_all(log=print):
    h, HC, vec, cache = load_model()
    A = NM.anchors()
    cm = CostModel(h, HC, vec)
    log(f"{NM.LABEL}: {h.NSTATE} states; response {cache}")
    extra = {} if NM.VERSION == "1.1" else {"date": "2026-10-13", "model": NM.LABEL, "run": NM.RUNS[NM.VERSION]}
    eq, fe, ru, rq = price_equalization(cm, A, h.NSTATE, extra)
    res = json.loads((NM.run_dir() / "results.json").read_text(encoding="utf-8"))["deterministic"]["metals"]
    pools_match_results_json = (fe["breakdown"] == res["Fe"]["feasible"]["breakdown"]
                                and ru["breakdown"] == res["Ru"]["feasible"]["breakdown"])
    rows, check = cost_mc(cm, log)
    files = {
        "nh3_ru_price_equalization.json": json_text(eq),
        "nh3_cost_decomposition.csv": csv_text(decomposition_rows(fe, ru, rq)),
        "nh3_cost_mc_summary.json": json_text(cost_mc_summary(rows, check, extra)),
        "nh3_cost_mc_histogram.csv": csv_text(histogram_rows(rows)),
        "f3_panel_summary.csv": csv_text(f3_rows(rows, A)),
    }
    draws = csv_text([list(rows[0])] + [list(r.values()) for r in rows])
    return files, draws, dict(A=A, fe=fe, ru=ru, rq=rq, nstate=h.NSTATE, pools_match_results_json=pools_match_results_json)


def compare_with_committed(files):
    rep = {}
    for name, text in files.items():
        committed = (HERE / name).read_text(encoding="utf-8")
        note = None
        if name.endswith(".json"):
            new, old = json.loads(text), json.loads(committed)
            if "baseline_reproduction" in new:
                # error of the producing run against results.json, not a result: reported side by side
                ks = ("Fe_cost_abs_error_USD_t", "Ru_cost_abs_error_USD_t")
                note = {"committed": {k: old["baseline_reproduction"].pop(k) for k in ks},
                        "recomputed": {k: new["baseline_reproduction"].pop(k) for k in ks}}
            c = compare_tree(new, old)
        else:
            c = compare_tree(csv_cells(text), csv_cells(committed))
        rep[name] = {"byte_identical": text == committed, "max_relative_difference": c["max_rel"], "at": c["where"],
                     "non_numeric_or_integer_mismatches": c["mismatch"]}
        if note:
            rep[name]["baseline_reproduction_errors"] = note
    return rep


# ----------------------------------------------------------------------------------------------------------------------
def readme_1_2(files, info):
    old = {n: (HERE / n).read_text(encoding="utf-8") for n in files}
    eq0, eq1 = json.loads(old["nh3_ru_price_equalization.json"]), json.loads(files["nh3_ru_price_equalization.json"])
    mc0, mc1 = json.loads(old["nh3_cost_mc_summary.json"]), json.loads(files["nh3_cost_mc_summary.json"])
    d0 = {r[0]: r for r in csv.reader(io.StringIO(old["nh3_cost_decomposition.csv"]))}
    d1 = {r[0]: r for r in csv.reader(io.StringIO(files["nh3_cost_decomposition.csv"]))}
    f0 = {r[0]: r[1] for r in csv.reader(io.StringIO(old["f3_panel_summary.csv"]))}
    f1 = {r[0]: r[1] for r in csv.reader(io.StringIO(files["f3_panel_summary.csv"]))}
    st = lambda e: f"{e['T_C']:.0f} °C, {e['P_bar']:.0f} bar, {e['Tsep_C']:.0f} °C"
    usd = lambda x: f"{float(x):.4f}"
    k0, k1 = mc0["full_14136_state_direct_cost_verification"], mc1["full_14136_state_direct_cost_verification"]
    t = [
        ("Process states", f"{eq0['process_state_count']:,}", f"{eq1['process_state_count']:,}", ""),
        ("Fe canonical cost / optimum", f"{usd(eq0['Fe_canonical']['total_cost_USD_t'])} / {st(eq0['Fe_canonical'])}",
         f"{usd(eq1['Fe_canonical']['total_cost_USD_t'])} / {st(eq1['Fe_canonical'])}", "USD t⁻¹"),
        ("Ru canonical cost / optimum", f"{usd(eq0['Ru_canonical']['total_cost_USD_t'])} / {st(eq0['Ru_canonical'])}",
         f"{usd(eq1['Ru_canonical']['total_cost_USD_t'])} / {st(eq1['Ru_canonical'])}", "USD t⁻¹"),
        ("Ru − Fe, canonical", usd(d0["TOTAL"][3]), usd(d1["TOTAL"][3]), "USD t⁻¹"),
    ]
    for pool, _ in POOLS:
        t.append((f"  Ru − Fe: {pool}", usd(d0[pool][3]), usd(d1[pool][3]), "USD t⁻¹"))
    t += [
        ("Ru at Fe metal price (8 USD/kg), re-optimized", f"{usd(eq0['Ru_price_equalized_to_Fe']['total_cost_USD_t'])} / {st(eq0['Ru_price_equalized_to_Fe'])}",
         f"{usd(eq1['Ru_price_equalized_to_Fe']['total_cost_USD_t'])} / {st(eq1['Ru_price_equalized_to_Fe'])}", "USD t⁻¹"),
        ("Ru(equal price) − Fe", usd(eq0["Ru_minus_Fe_USD_t"]), usd(eq1["Ru_minus_Fe_USD_t"]), "USD t⁻¹"),
        ("Economic order after equalization", eq0["economic_order_after_equalization"], eq1["economic_order_after_equalization"], ""),
        ("Cost MC: P(C_Fe < C_Ru)", f"{k0['count_Fe_lt_Ru']:,}/{mc0['draws']:,} = {k0['P_C_Fe_lt_C_Ru']:.3f}",
         f"{k1['count_Fe_lt_Ru']:,}/{mc1['draws']:,} = {k1['P_C_Fe_lt_C_Ru']:.3f}", ""),
        ("Cost MC: minimum Ru − Fe", f"{k0['minimum_Ru_minus_Fe_USD_t']:.3f}", f"{k1['minimum_Ru_minus_Fe_USD_t']:.3f}", "USD t⁻¹"),
        ("Cost MC: Ru − Fe p05 / median / p95",
         " / ".join(f"{k0['Ru_minus_Fe_USD_t_quantiles'][p]:.3f}" for p in ("p05", "p50", "p95")),
         " / ".join(f"{k1['Ru_minus_Fe_USD_t_quantiles'][p]:.3f}" for p in ("p05", "p50", "p95")), "USD t⁻¹"),
        ("Cost MC: Fe cost p05 / median / p95", " / ".join(f"{mc0['Fe_cost_USD_t_quantiles'][p]:.3f}" for p in ("p05", "p50", "p95")),
         " / ".join(f"{mc1['Fe_cost_USD_t_quantiles'][p]:.3f}" for p in ("p05", "p50", "p95")), "USD t⁻¹"),
        ("Cost MC: Ru cost p05 / median / p95", " / ".join(f"{mc0['Ru_cost_USD_t_quantiles'][p]:.3f}" for p in ("p05", "p50", "p95")),
         " / ".join(f"{mc1['Ru_cost_USD_t_quantiles'][p]:.3f}" for p in ("p05", "p50", "p95")), "USD t⁻¹"),
        ("Cost MC: alpha* p05 / median / p95", " / ".join(f"{mc0['alpha_star'][p]:.2f}×" for p in ("p05", "p50", "p95")),
         " / ".join(f"{mc1['alpha_star'][p]:.2f}×" for p in ("p05", "p50", "p95")), ""),
        ("Cost MC: alpha* mean / min / max", " / ".join(f"{mc0['alpha_star'][p]:.2f}×" for p in ("mean", "min", "max")),
         " / ".join(f"{mc1['alpha_star'][p]:.2f}×" for p in ("mean", "min", "max")), ""),
        ("Cost MC: P(Ru ≤ Fe at alpha = 1)", f"{mc0['P_Ru_le_Fe_at_alpha_1']:.3f}", f"{mc1['P_Ru_le_Fe_at_alpha_1']:.3f}", ""),
        ("alpha* canonical (results.json)", f"{float(f0['alpha_star_canonical']):.2f}×", f"{float(f1['alpha_star_canonical']):.2f}×", ""),
        ("Descriptor MC: Fe feasible", f"{float(f0['Fe_feasible_descriptor_MC']):.3f}", f"{float(f1['Fe_feasible_descriptor_MC']):.3f}", "1,000 draws"),
        ("Descriptor MC: Fe economic Top-1", f"{float(f0['Fe_economic_top1_descriptor_MC']):.3f}", f"{float(f1['Fe_economic_top1_descriptor_MC']):.3f}", "1,000 draws"),
        ("Descriptor MC: atomic Top-1 = economic Top-1", f"{float(f0['top1_survival_descriptor_MC']):.3f}", f"{float(f1['top1_survival_descriptor_MC']):.3f}", "1,000 draws"),
        ("Descriptor MC: Fe Top-3 actionable", f"{float(f0['Fe_top3_actionable_descriptor_MC']):.3f}", f"{float(f1['Fe_top3_actionable_descriptor_MC']):.3f}", "1,000 draws"),
    ]
    lines = [
        "# Supervisor NH3 cost analyses on NH3-FINAL-1.2",
        "",
        "Same definitions as the NH3-FINAL-1.1 files one folder up (`../README.md` sections 1, 2 and 4,",
        "`docs/SUPERVISOR_COST_MC_PREREG_2026-09-20.md`), run on NH3-FINAL-1.2 (Gillespie–Beattie NH₃ formation free energy,",
        f"Newton–Cooper fugacities in the loop and the microkinetics, F_CAL {info['A']['F_CAL']:,.1f}; canonical run "
        f"`{info['A']['run']}`).",
        "Nothing is re-chosen: the counterfactual is still Ru at the Fe metal price (8 USD/kg) with Ru re-optimized over the",
        "full library; the cost MC keeps the prior, N = 5,000 and seed 20260920 and re-optimizes Fe and Ru over the 1.2",
        "library in every draw; alpha* is solved against each draw's re-optimized Fe cost.",
        "",
        "    set NH3_MODEL=1.2",
        r"    set NH3_HARNESS_1_2=D:\论文-AI4S\wt-nh3-12\provenance\nh3_final_1_2\source_harness",
        "    python -X utf8 analysis/supervisor_2026_09_20/nh3_supervisor_cost.py",
        "",
        "With `NH3_MODEL=1.1` the same script recomputes the frozen files and compares them",
        "(`../nh3_v11_reproduction_check.json`); it never overwrites them.",
        "",
        "| Quantity | NH3-FINAL-1.1 | **NH3-FINAL-1.2** | Unit |",
        "|---|---:|---:|---|",
    ]
    lines += [f"| {a} | {b} | **{c}** | {d} |" for a, b, c, d in t]
    lines += [
        "",
        "Files (same names and schema as the 1.1 files):",
        "",
        "- `nh3_ru_price_equalization.json`, `nh3_cost_decomposition.csv` — canonical pools and the equal-price counterfactual.",
        "- `nh3_cost_mc_summary.json`, `nh3_cost_mc_histogram.csv` — joint cost MC. The key",
        "  `full_14136_state_direct_cost_verification` keeps its 1.1 name so readers work unchanged; the library here has",
        f"  {info['nstate']:,} states (`process_state_count`).",
        "- `f3_panel_summary.csv` — the metric table `figures/nh3/render_F03_uncertainty_cost_mc.R` reads (descriptor MC",
        "  values from the 1.2 closure `mc_detail` / `mc_draws.csv`, cost MC values from this run).",
        "- `nh3_cost_mc_draws.csv` — the draw-level table (prereg output 4; sampled parameters, re-optimized costs, alpha*,",
        "  optimum states).",
        "",
        "Checks in this run against the 1.2 `results.json`: |Fe cost error| = "
        f"{eq1['baseline_reproduction']['Fe_cost_abs_error_USD_t']:.1e}, |Ru cost error| = "
        f"{eq1['baseline_reproduction']['Ru_cost_abs_error_USD_t']:.1e} USD t⁻¹; optimum states match: "
        f"{eq1['baseline_reproduction']['Fe_optimum_match'] and eq1['baseline_reproduction']['Ru_optimum_match']};",
        f"canonical cost pools equal its `breakdown` blocks: {info['pools_match_results_json']}. alpha* on the non-dominated",
        f"Ru states vs the full library, {mc1['alpha_subset_validation_against_full_library']['n_checked']} draws: max "
        f"relative error {mc1['alpha_subset_validation_against_full_library']['max_alpha_relative_error']:.1e}.",
        "",
        "## F03 renderer",
        "",
        "`figures/nh3/render_F03_uncertainty_cost_mc.R` reads `f3_panel_summary.csv` (all 11 metrics),",
        "`nh3_cost_mc_histogram.csv` (both histograms) and the MeOH `../meoh_rank_probability_matrix.csv` (unchanged by the",
        "NH3 model), with paths fixed to the 1.1 folder. It stops unless Fe economic Top-1 = 0.681, Top-1 survival = 0.282",
        "and P(C_Fe < C_Ru) = 1, and types \"68.1%\", \"28.2%\" and \"5,000/5,000\" into the panel text; on 1.2 the first two",
        f"are {float(f1['Fe_economic_top1_descriptor_MC']):.3f} and {float(f1['top1_survival_descriptor_MC']):.3f}. "
        "It does not read the price-equalization JSON, the decomposition CSV or the cost MC summary JSON.",
        "",
    ]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", help="also write the recomputed files (and the draw table) to this directory")
    args = ap.parse_args()
    files, draws, info = build_all()
    if NM.VERSION == "1.1":
        rep = compare_with_committed(files)
        import platform
        import scipy
        rep_all = {"model": NM.LABEL, "run": NM.RUNS["1.1"], "harness_root": str(NM.root()),
                   "environment": {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__,
                                   "platform": platform.system()},
                   "canonical_pools_equal_results_json_breakdown": info["pools_match_results_json"],
                   "note": "The committed files were written by a run (script not committed) whose own baseline check differs "
                           "from results.json by {:.1e} / {:.1e} USD/t (Fe / Ru); this script gives {:.1e} / {:.1e} USD/t, "
                           "so the files are compared numerically, not byte for byte. Non-numeric fields, integer counts, "
                           "states and histogram counts identical: {}.".format(
                               *rep["nh3_ru_price_equalization.json"]["baseline_reproduction_errors"]["committed"].values(),
                               *rep["nh3_ru_price_equalization.json"]["baseline_reproduction_errors"]["recomputed"].values(),
                               all(not r["non_numeric_or_integer_mismatches"] for r in rep.values())),
                   "files": rep}
        (HERE / "nh3_v11_reproduction_check.json").write_text(json.dumps(rep_all, indent=2, ensure_ascii=False) + "\n",
                                                               encoding="utf-8", newline="\n")
        for n, r in rep.items():
            print(f"  {n}: byte-identical {r['byte_identical']}, max rel diff {r['max_relative_difference']:.2e} at {r['at']}, "
                  f"mismatches {r['non_numeric_or_integer_mismatches']}")
    if args.out or NM.VERSION == "1.2":
        out = Path(args.out) if args.out else NM.out_dir(HERE)
        out.mkdir(parents=True, exist_ok=True)
        for n, text in files.items():
            (out / n).write_text(text, encoding="utf-8", newline="")
        (out / "nh3_cost_mc_draws.csv").write_text(draws, encoding="utf-8", newline="")
        if NM.VERSION == "1.2" and not args.out:
            (out / "README.md").write_text(readme_1_2(files, info), encoding="utf-8", newline="\n")
        print(f"  wrote {out}")


if __name__ == "__main__":
    main()
