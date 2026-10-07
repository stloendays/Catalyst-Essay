"""Experimental ammonia catalysts (Humphreys et al. 2021, Tables 1-6) through the frozen ammonia chain.

Input: agent/nh3_supported/out/records.csv, the adjudicated agent extraction (one row per table row).

Mapping a real catalyst onto the model (effective descriptor). The model turns a per-site TOF into metal inventory
with one calibration (fused Fe, 65 m3 for 1,000 t/d): rate per g of metal = F_CAL x TOF(E_N) / MW. For a catalyst of
model metal M with metal content w and measured rate R (per g catalyst) at its laboratory T and P, the effective
descriptor E_eff is the E_N on M's side of the volcano (the side of M's frozen descriptor at that condition) at which
w x F_CAL x TOF(E_eff) / MW_M = R. A rate above the volcano top at that condition places the catalyst at the top with
the remaining factor alpha_res > 1. The catalyst then enters the 14,136-state library as a surface with descriptor
E_eff (and alpha_res), molar mass and price of M: a catalyst as active as a given descriptor is treated as behaving
like it under plant conditions. A constant multiplier on M's own TOF vector, alpha = R / (w F_CAL TOF_M / MW_M), is
reported as a sensitivity. Fused-Fe rows test the calibration (alpha near 1).

Laboratory condition: H2/N2 = 3; outlet NH3 from the printed value or from rate and WHSV, y = n / (F0 - n) (n NH3 made,
F0 inlet flow; the reaction removes one mole of gas per mole of NH3). The frozen model's NH3 formation free energy lies
0.064-0.065 eV per NH3 above experiment (573-773 K), so the laboratory NH3 fraction is entered at the same approach to
equilibrium: y_model = (y_out / 2) x y_eq,model / y_eq,exp, with y_eq,exp from the Gillespie-Beattie equilibrium
constant. Rows with y_out >= 0.9 y_eq,exp are flagged: their rate is limited by equilibrium.

Plant cost: the frozen 14,136-state library, the metal's TOF vector times alpha, the catalyst's own metal content as
the active fraction of the bed (bed density 1,000 kg m-3 for supported catalysts, 500 and 2,500 tested; fused Fe
keeps the benchmark 71.51 wt% and 2,500 kg m-3), metal price only, no metal recovery (90 % tested for precious
metals), cost minimized over all states inside the 90 m3 bed limit. Fe, benchmark: 15.29 USD/t.

Primary set: one model metal (Fe, Ru, Co, Ni, Mo, ...), metal content known, measured at 300-500 C under steady
thermal operation (rows flagged chemical looping, electric field, microwave or plasma are reported separately),
outlet NH3 below 90 % of equilibrium.

Leaderboards. Paper leaderboard: rate per g catalyst, as tabulated. Plant leaderboard: plant cost. Compared within
each source reference at one T and P (the comparison that paper makes) and across the whole primary set.

Outputs: supported_candidates.csv, group_metrics.csv, summary.json.

    CatalystForge/.venv/python run_supported_chain.py [harness_root]
"""
import csv
import json
import math
import os
import sys
from pathlib import Path

import numpy as np
import yaml
from scipy.stats import spearmanr

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
HARNESS = Path(sys.argv[1] if len(sys.argv) > 1 else
               os.environ.get("NH3_HARNESS", r"D:/论文-AI4S/Catalyst_Economic_Leverage_Automation_Harness_v0.1"))
sys.path.insert(0, str(HARNESS))
import harness_core as hc  # noqa: E402

sys.path.insert(0, str(REPO / "agent"))
from selfcheck_gate import require  # noqa: E402

RECORDS = REPO / "agent" / "nh3_supported" / "out" / "records.csv"
RUN = HARNESS / "outputs" / "nh3_final_20260905T134204Z"
H2_N2 = 3.0
VM_ML = 22414.0
T_PRIMARY = (300.0, 500.0)
NONSTEADY = ("looping", "electric", "microwave", "plasma")
BED_SUPPORTED, BED_SENS = 1000.0, (500.0, 2500.0)
PRECIOUS = {"Ru", "Os", "Rh", "Ir", "Pd", "Pt", "Re", "Au", "Ag"}


def load_harness():
    h = hc.NH3Harness(yaml.safe_load((RUN / "manifest_resolved.yaml").read_text(encoding="utf-8")), HARNESS)
    response, _cp, cached = h.build_or_load_response()
    if not cached:
        raise SystemExit("response surface is not cached; refusing to rebuild a frozen asset")
    return h, response


def y_from_Kp(h, Kp, P_bar):
    xi = h.equilibrium_extent(Kp, P_bar, 1.0, H2_N2, 0.0)
    return 2.0 * xi / (1.0 + H2_N2 - 2.0 * xi)


def y_eq_model(h, T_K, P_bar):
    gg = h.ctx.gas_G(T_K)
    return y_from_Kp(h, math.exp(-2.0 * (gg["NH3"] - 0.5 * gg["N2"] - 1.5 * gg["H2"]) / (hc.K_B_EV * T_K)), P_bar)


def y_eq_exp(h, T_K, P_bar):
    """Gillespie & Beattie (1930) Ka for 1/2 N2 + 3/2 H2 = NH3 (atm^-1), ideal gas; Kp for the harness in bar^-2."""
    log_ka = -2.691122 * math.log10(T_K) - 5.519265e-5 * T_K + 1.848863e-7 * T_K ** 2 + 2001.6 / T_K + 2.6899
    return y_from_Kp(h, (10.0 ** log_ka / 1.01325) ** 2, P_bar)


def lab_condition(h, T_K, P_bar, y_nh3):
    p_free = P_bar * (1.0 - y_nh3)
    return h.ctx.condition(T_K, p_free / (1 + H2_N2), p_free * H2_N2 / (1 + H2_N2), P_bar * y_nh3)


def effective_descriptor(h, cond, metal, log_rate_target):
    """E_N on the metal's side of the volcano at `cond` whose model rate per g metal (log10 mol g-1 s-1) equals the
    target; returns (E_eff, log10 alpha_res), alpha_res > 1 only above the volcano top."""
    from scipy.optimize import brentq
    lmw = math.log10(h.F_CAL / hc.MW[metal] / 1000.0)
    grid = h.EGRID
    lt = np.array([cond.logtof(float(e)) for e in grid]) + lmw
    k = int(np.argmax(lt))
    if log_rate_target >= lt[k]:
        return float(grid[k]), float(log_rate_target - lt[k])
    left = hc.EN0_CANON[metal] <= grid[k]
    lo, hi = (0, k) if left else (k, len(grid) - 1)
    seg = lt[lo:hi + 1]
    if log_rate_target <= seg.min():
        j = lo + int(np.argmin(seg))
        return float(grid[j]), float(log_rate_target - lt[j])
    cross = np.where(np.diff(np.sign(seg - log_rate_target)))[0]
    j = lo + (int(cross[-1]) if left else int(cross[0]))
    f = lambda e: cond.logtof(e) + lmw - log_rate_target  # noqa: E731
    return float(brentq(f, float(grid[j]), float(grid[j + 1]), xtol=1e-6)), 0.0


def plant_cost(h, response, metal, alpha, w, bed_density, recovery=None, E=None):
    af, bd = h.ACTIVE_FRACTION, h.BED_DENSITY
    h.ACTIVE_FRACTION, h.BED_DENSITY = w, bed_density
    try:
        logvec = h.interp_state_vector(response, hc.EN0_CANON[metal] if E is None else E)
        return h.eval_scenario(metal, logvec, alpha=alpha, recovery=recovery)
    except RuntimeError:
        return None
    finally:
        h.ACTIVE_FRACTION, h.BED_DENSITY = af, bd


def fnum(x):
    return None if x in ("", None) else float(x)


def y_out_from_rate(R, whsv):
    """Outlet NH3 mole fraction from the rate (umol g-1 h-1) and the inlet space velocity (mL g-1 h-1, STP):
    n / (F0 - n), since N2 + 3 H2 -> 2 NH3 removes one mole of gas per mole of NH3 formed."""
    n = R * 1e-6 * VM_ML
    return n / (whsv - n)


def main():
    require()          # ACSA scores new candidates only after reproducing all three hand-built cases
    h, response = load_harness()
    fe_cost = float(json.loads((RUN / "results.json").read_text(encoding="utf-8"))["deterministic"]["metals"]["Fe"]
                    ["feasible"]["total_cost"])
    rows, seen = [], {}
    for r in csv.DictReader(RECORDS.open(encoding="utf-8")):
        key = (r["T_C"], r["P_MPa"], r["rate_umol_g_h"], r["ref"])
        if r["rate_umol_g_h"] and key in seen:   # rows repeated across tables (Tables 2 and 3) with the name retyped
            seen[key]["notes"] = (seen[key]["notes"] + f"; also printed as {r['id']}").strip("; ")
            continue
        seen[key] = r
        rows.append(r)
    y_known = []
    for r in rows:
        R, whsv, out = fnum(r["rate_umol_g_h"]), fnum(r["whsv_mL_g_h"]), fnum(r["outlet_nh3_vol_pct"])
        r["_y_out"] = out / 100.0 if out is not None else (y_out_from_rate(R, whsv) if R and whsv else None)
        r["_y_source"] = "printed outlet" if out is not None else ("rate / WHSV" if r["_y_out"] is not None else "")
        if r["_y_out"] is not None:
            y_known.append(r["_y_out"])
    y_default = float(np.median(y_known))

    out = []
    for r in rows:
        metals = [m for m in r["active_metals"].split(";") if m]
        rec = {k: r[k] for k in ("id", "table", "page", "catalyst", "active_metals", "metal_wt_pct", "T_C", "P_MPa",
                                 "whsv_mL_g_h", "outlet_nh3_vol_pct", "rate_umol_g_h", "ref", "notes")}
        rec["erratum"] = r.get("erratum", "")
        rec.update(status="", E_eff_eV="", log10_alpha_res="", alpha="", y_out="", y_source=r["_y_source"], y_eq_exp="",
                   cost_USD_t="", cost_alpha_transfer="", cost_bed500="", cost_bed2500="", cost_recovery90="",
                   T_opt_C="", P_opt_bar="", V_m3="")
        R, w, T_C, P_MPa = fnum(r["rate_umol_g_h"]), fnum(r["metal_wt_pct"]), fnum(r["T_C"]), fnum(r["P_MPa"])
        fused = r.get("fused_fe", "") == "True"
        reasons = []
        if len(metals) != 1 or metals[0] not in hc.EN0_CANON:
            reasons.append("not a single model metal")
        if R is None or R <= 0 or r["rate_unit_ok"] != "True":
            reasons.append("no rate per g catalyst")
        if w is None and not fused:
            reasons.append("metal content not given")
        if T_C is None or P_MPa is None:
            reasons.append("no T or P")
        if reasons:
            rec["status"] = "outside: " + "; ".join(reasons)
            out.append(rec)
            continue
        metal = metals[0]
        w = 0.7151 if fused else w / 100.0
        T_K, P_bar = T_C + 273.15, P_MPa * 10.0
        y_out = r["_y_out"] if r["_y_out"] is not None else y_default
        y_eq = y_eq_exp(h, T_K, P_bar)
        y_lab = min(0.5 * y_out, 0.5 * y_eq) * y_eq_model(h, T_K, P_bar) / y_eq
        cond = lab_condition(h, T_K, P_bar, y_lab)
        log_target = math.log10(R * 1e-6 / 3600.0 / w)                     # mol NH3 / (g metal s)
        alpha = 10.0 ** log_target / (h.F_CAL * 10.0 ** cond.logtof(hc.EN0_CANON[metal]) / hc.MW[metal] / 1000.0)
        E_eff, la_res = effective_descriptor(h, cond, metal, log_target)
        flags = []
        if any(k in (r["catalyst"] + " " + r["notes"]).lower() for k in NONSTEADY):
            flags.append("non-steady or non-thermal")
        if not (T_PRIMARY[0] <= T_C <= T_PRIMARY[1]):
            flags.append("T outside 300-500 C")
        if y_out >= 0.9 * y_eq:
            flags.append("outlet near equilibrium")
        if r["_y_out"] is None:
            flags.append("outlet NH3 assumed (median)")
        bed = 2500.0 if fused else BED_SUPPORTED
        a_res = 10.0 ** la_res
        best = plant_cost(h, response, metal, a_res, w, bed, E=E_eff)
        rec.update(E_eff_eV=E_eff, log10_alpha_res=la_res, alpha=alpha, y_out=y_out, y_eq_exp=y_eq)
        if best is not None:
            rec.update(cost_USD_t=best["total_cost"], T_opt_C=best["T_C"], P_opt_bar=best["P_bar"], V_m3=best["V_m3"])
        s = plant_cost(h, response, metal, alpha, w, bed)
        rec["cost_alpha_transfer"] = "" if s is None else s["total_cost"]
        if not fused:
            for bd, key in zip(BED_SENS, ("cost_bed500", "cost_bed2500")):
                s = plant_cost(h, response, metal, a_res, w, bd, E=E_eff)
                rec[key] = "" if s is None else s["total_cost"]
        if metal in PRECIOUS:
            s = plant_cost(h, response, metal, a_res, w, bed, recovery=0.9, E=E_eff)
            rec["cost_recovery90"] = "" if s is None else s["total_cost"]
        primary = not flags or flags == ["outlet NH3 assumed (median)"]
        rec["status"] = ("primary" if primary else "flagged") + ("" if not flags else ": " + "; ".join(flags))
        if best is None:
            rec["status"] += "; infeasible within bed limit"
        out.append(rec)

    prim = [o for o in out if o["status"].startswith("primary") and o["cost_USD_t"] != ""]
    groups = {}
    for o in prim:
        groups.setdefault((o["ref"], o["T_C"], o["P_MPa"]), []).append(o)
    gm = []
    for (ref, T, P), g in sorted(groups.items()):
        if len(g) < 2:
            continue
        up = max(g, key=lambda o: float(o["rate_umol_g_h"]))
        eco = min(g, key=lambda o: o["cost_USD_t"])
        rho = spearmanr([-float(o["rate_umol_g_h"]) for o in g], [o["cost_USD_t"] for o in g]).correlation
        gm.append(dict(ref=ref, T_C=T, P_MPa=P, n=len(g), rate_leader=up["catalyst"], plant_leader=eco["catalyst"],
                       same=up["id"] == eco["id"], regret=up["cost_USD_t"] / eco["cost_USD_t"] - 1.0, spearman=rho))
    fused_ids = {r["id"] for r in rows if r.get("fused_fe") == "True"}
    fused = [o for o in out if o["alpha"] != "" and o["id"] in fused_ids]
    by_metal = {}
    for o in prim:
        by_metal.setdefault(o["active_metals"], []).append(o)
    up_all = max(prim, key=lambda o: float(o["rate_umol_g_h"]))
    eco_all = min(prim, key=lambda o: o["cost_USD_t"])
    summary = dict(
        rows=len(out), primary=len(prim), flagged=sum(o["status"].startswith("flagged") for o in out),
        outside=sum(o["status"].startswith("outside") for o in out), y_default_median=y_default,
        Fe_benchmark_USD_t=fe_cost,
        per_metal={m: dict(n=len(g), below_Fe=sum(o["cost_USD_t"] < fe_cost for o in g),
                           alpha_median=float(np.median([o["alpha"] for o in g])),
                           E_eff_median=float(np.median([o["E_eff_eV"] for o in g])),
                           E_frozen=hc.EN0_CANON.get(m),
                           cost_min=min(o["cost_USD_t"] for o in g), best=min(g, key=lambda o: o["cost_USD_t"])["catalyst"])
                   for m, g in sorted(by_metal.items())},
        overall=dict(rate_leader=up_all["catalyst"], rate_leader_cost=up_all["cost_USD_t"], plant_leader=eco_all["catalyst"],
                     plant_leader_cost=eco_all["cost_USD_t"], regret=up_all["cost_USD_t"] / eco_all["cost_USD_t"] - 1.0,
                     spearman_rate_vs_cost=spearmanr([-float(o["rate_umol_g_h"]) for o in prim],
                                                     [o["cost_USD_t"] for o in prim]).correlation),
        groups=dict(n=len(gm), leader_differs=sum(not g["same"] for g in gm)),
        fused_fe_alpha=[(o["catalyst"], o["alpha"]) for o in fused],
    )

    def below(col, sub):
        vals = [o for o in sub if o[col] not in ("", None)]
        return dict(n=len(vals), below_Fe=sorted(o["catalyst"] for o in vals if float(o[col]) < fe_cost))

    hp = [o for o in prim if float(o["P_MPa"]) >= 5.0]
    ru = [o for o in prim if o["active_metals"] == "Ru"]
    summary["sensitivity"] = dict(
        alpha_transfer=below("cost_alpha_transfer", prim),
        bed_500=below("cost_bed500", prim), bed_2500=below("cost_bed2500", prim),
        Ru_recovery90=below("cost_recovery90", ru),
        P_ge_5MPa=dict(n=len(hp), per_metal={m: dict(n=sum(o["active_metals"] == m for o in hp),
                                                     cost_min=min((o["cost_USD_t"] for o in hp if o["active_metals"] == m),
                                                                  default=None))
                                             for m in sorted({o["active_metals"] for o in hp})},
                       below_Fe=sorted(o["catalyst"] for o in hp if o["cost_USD_t"] < fe_cost)),
        outlet_assumed=sum("outlet NH3 assumed" in o["status"] for o in prim),
    )
    reasons = {}
    for o in out:
        if o["status"].startswith("outside"):
            for x in o["status"][len("outside: "):].split("; "):
                reasons[x] = reasons.get(x, 0) + 1
    summary["outside_reasons"] = reasons
    fields = list(out[0])
    with (HERE / "supported_candidates.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(out)
    if gm:
        with (HERE / "group_metrics.csv").open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(gm[0]))
            w.writeheader()
            w.writerows(gm)
    (HERE / "summary.json").write_text(json.dumps(summary, indent=1, default=float) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1, default=float))


if __name__ == "__main__":
    main()
