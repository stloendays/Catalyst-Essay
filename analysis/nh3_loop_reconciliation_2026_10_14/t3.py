"""T3: model bridge between the manuscript's canonical measured-kinetics comparison and the closed loop (#93/#94)."""
from __future__ import annotations

import canonical as CAN
import closed_loop as CL
import cold_worker
import kinetic_bridge as KB

COMMON = ("inventory", "reactor", "utilities", "compressor_capital")
CL_ONLY = ("excess_feed", "hot_duty")
FEED_SPLIT = ("purge_gas_loss", "dissolved_gas_loss", "NH3_in_purge", "feed_residual")
ALL = COMMON + CL_ONLY + FEED_SPLIT


def delta(ru, fe):
    d = {k: ru[k] - fe[k] for k in ALL}
    d["total"] = ru["total_USD_t"] - fe["total_USD_t"]
    d["sum_check"] = sum(d[k] for k in COMMON + CL_ONLY) - d["total"]
    assert abs(d["sum_check"]) < 1e-8, d
    return d


def closed_design(cat, T, P, X, T2, purge, base):
    """Recompute one closed-loop design (cold state + isothermal bed) and price it on a basis."""
    rec = cold_worker.job((P, X, T2, purge, CL.TARGET_TPD))
    sid = CL.RS.grid_key(P, X, T2, purge)
    states = {sid: {"state_id": sid, "P_bar": P, "X": X, "T2_C": T2, "purge": purge, "record": rec}}
    rows = [r for r in CL.size_candidates(states, temps=(T,)) if r["catalyst"] == cat]
    assert len(rows) == 1 and rows[0].get("feasible"), rows
    return CL.describe((rows[0], CL.price(rows[0], rec, base)), states)


def closed_at(states, cat, T, P, base):
    """Closed-loop optimum at fixed T and P (X, T2, purge reoptimised on the grid)."""
    at = {k: v for k, v in states.items() if v["P_bar"] == P}
    rows = CL.size_candidates(at, temps=(T,))
    return CL.describe(CL.best(rows, at, base, cat), at)


def run(states, up, log=print):
    h = CAN.build()
    ms = CAN.manuscript_optima(h)
    sup = ms["Ru_C_supported"]
    a12, a0 = sup["cashflow 12% r 0.9555"], sup["cashflow 0% r 0.9555"]
    gates = {"Fe_optimum_14.925644": abs(ms["Fe"]["cost"] - 14.925644) < 1e-3,
             "RuC_minus_Fe_0pct_-3.4634": abs(a0["Ru_minus_Fe_global"] + 3.4634) < 1e-3,
             "RuC_minus_Fe_12pct_+1.452": abs(a12["Ru_minus_Fe_global"] - 1.452) < 1e-3}
    pt = lambda d: (d["T_C"], d["P_bar"], d["Tsep_C"])
    pairs = {
        "a12_manuscript_12pct": {"Fe": pt(a12["Fe_global"]), "Ru": pt(a12["Ru_C_global"])},
        "a0_manuscript_0pct": {"Fe": pt(a0["Fe_global"]), "Ru": pt(a0["Ru_C_global"])},
    }
    u94, u93 = up["u94"]["nominal_selected"], up["u93"]["selected"]
    cl_pairs = {
        "b94_closed_source_windows": {c: (u94[c]["T_C"], u94[c]["P_bar"], u94[c]["X"], u94[c]["cold_T2_C"], u94[c]["purge"])
                                      for c in ("Fe", "Ru")},
        "c93_closed_220bar": {c: (u93[c]["T_C"], u93[c]["P_bar"], u93[c]["X_design"], u93[c]["T2_C"], u93[c]["purge"])
                              for c in ("Fe", "Ru")},
    }
    for name, d in cl_pairs.items():
        pairs[name] = {c: (v[0], v[1], v[3]) for c, v in d.items()}      # canonical Tsep = closed-loop cold T2
    econ = {"r0.9555_12pct_dp3": (0.9555, 0.12, 3.0), "r0.90_12pct_dp3": (0.90, 0.12, 3.0),
            "r0.90_12pct_dp9.2": (0.90, 0.12, 9.2), "r0.9555_0pct_dp3": (0.9555, 0.0, 3.0)}
    points, table = [], {}
    for name, pr in pairs.items():
        table[name] = {}
        for ename, (r, i, dp) in econ.items():
            fe = CAN.canonical_point_costs(h, pr["Fe"], "Fe", recovery=r, fin_rate=i, dp=dp)
            ru = CAN.canonical_point_costs(h, pr["Ru"], "Ru", recovery=r, fin_rate=i, dp=dp)
            table[name]["canonical " + ename] = {"Fe": fe, "Ru": ru, "delta": delta(ru, fe)}
        for bname, base in CL.BASES.items():
            if name in cl_pairs:
                fe = closed_design("Fe", *cl_pairs[name]["Fe"], base)
                ru = closed_design("Ru", *cl_pairs[name]["Ru"], base)
                how = "upstream design, repriced" if (name.startswith("b94") and bname == "B93") or \
                      (name.startswith("c93") and bname == "B94") else "upstream optimum"
            else:
                fe = closed_at(states, "Fe", pr["Fe"][0], pr["Fe"][1], base)
                ru = closed_at(states, "Ru", pr["Ru"][0], pr["Ru"][1], base)
                how = "T and P fixed to the canonical point; X, T2, purge reoptimised"
            if fe is None or ru is None:
                table[name]["closed " + bname] = {"Fe": fe, "Ru": ru, "delta": None, "how": how}
                continue
            table[name]["closed " + bname] = {"Fe": fe, "Ru": ru, "delta": delta(ru, fe), "how": how}
        for model, v in table[name].items():
            for cat in ("Fe", "Ru"):
                if v[cat] is not None:
                    points.append({"pair": name, "model_basis": model, "catalyst": cat,
                                   **{k: v[cat].get(k) for k in ("T_C", "P_bar", "Tsep_C", "X", "X_per_pass", "T2_C", "purge",
                                                                  "bed_m3", "total_USD_t", "inlet_NH3_pct", "inlet_inerts_pct")},
                                   **{k: v[cat][k] for k in ALL}})
        log(f"T3 {name}: " + ", ".join(f"{m} {v['delta']['total']:+.3f}" for m, v in table[name].items() if v["delta"]))
    # consistency: canonical point costs reproduce the kinetics_swap optima; closed designs reproduce upstream
    cons = {"canonical_a12_Fe": table["a12_manuscript_12pct"]["canonical r0.9555_12pct_dp3"]["Fe"]["total_USD_t"] - a12["Fe_global"]["cost"],
            "canonical_a12_Ru": table["a12_manuscript_12pct"]["canonical r0.9555_12pct_dp3"]["Ru"]["total_USD_t"] - a12["Ru_C_global"]["cost"],
            "canonical_a0_Ru": table["a0_manuscript_0pct"]["canonical r0.9555_0pct_dp3"]["Ru"]["total_USD_t"] - a0["Ru_C_global"]["cost"],
            "closed_b94_Fe": table["b94_closed_source_windows"]["closed B94"]["Fe"]["total_USD_t"] - u94["Fe"]["decision_USD_t"],
            "closed_b94_Ru": table["b94_closed_source_windows"]["closed B94"]["Ru"]["total_USD_t"] - u94["Ru"]["decision_USD_t"],
            "closed_c93_Fe": table["c93_closed_220bar"]["closed B93"]["Fe"]["total_USD_t"] - u93["Fe"]["decision_relevant_cost_USD_t"],
            "closed_c93_Ru": table["c93_closed_220bar"]["closed B93"]["Ru"]["total_USD_t"] - u93["Ru"]["decision_relevant_cost_USD_t"]}
    # waterfall from the manuscript +1.45 to the #94 +41.0
    S = {"S0 canonical pair a12, r 95.55%, 12%, rise 3 bar": table["a12_manuscript_12pct"]["canonical r0.9555_12pct_dp3"]["delta"],
         "S1 canonical pair b94": table["b94_closed_source_windows"]["canonical r0.9555_12pct_dp3"]["delta"],
         "S2 canonical pair b94, r 90%": table["b94_closed_source_windows"]["canonical r0.90_12pct_dp3"]["delta"],
         "S3 canonical pair b94, r 90%, rise 9.2 bar": table["b94_closed_source_windows"]["canonical r0.90_12pct_dp9.2"]["delta"],
         "S4 closed loop pair b94, B94": table["b94_closed_source_windows"]["closed B94"]["delta"],
         "S5 closed loop pair a12, B94": table["a12_manuscript_12pct"]["closed B94"]["delta"],
         "S0' canonical pair a12, r 90%, rise 9.2 bar": table["a12_manuscript_12pct"]["canonical r0.90_12pct_dp9.2"]["delta"]}
    names = list(S)
    wf = []
    keys = ("total",) + COMMON + CL_ONLY + FEED_SPLIT
    for a, b in zip(names[:4], names[1:5]):
        wf.append({"step": f"{a.split()[0]} -> {b.split()[0]}", "from": a, "to": b, **{k: S[b][k] - S[a][k] for k in keys}})
    if S[names[5]] is not None:
        s0, s0p, s3, s4, s5 = (S[names[i]] for i in (0, 6, 3, 4, 5))
        for lbl, x, y in (("order 1: econ+rise at pair a (S0 -> S0')", s0, s0p),
                          ("order 1: pair effect, canonical (S0' -> S3)", s0p, s3),
                          ("order 1: model effect at pair b (S3 -> S4)", s3, s4),
                          ("order 2: model effect at pair a (S0' -> S5)", s0p, s5),
                          ("order 2: pair effect, closed loop (S5 -> S4)", s5, s4)):
            wf.append({"step": lbl, "from": "", "to": "", **{k: y[k] - x[k] for k in keys}})
    total_gap = S[names[4]]["total"] - S[names[0]]["total"]
    contrib = {k: S[names[4]][k] - S[names[0]][k] for k in COMMON + CL_ONLY}
    ranked = sorted(contrib.items(), key=lambda kv: -abs(kv[1]))
    out = {"gates": gates, "consistency_abs_diff": cons, "pairs": pairs, "closed_pairs": cl_pairs, "table": table,
           "waterfall_levels": S, "gap_S4_minus_S0": total_gap, "gap_by_category": contrib,
           "categories_ranked_by_abs_contribution": ranked,
           "manuscript_recomputed": {"Fe_optimum": ms["Fe"], "a12": {k: a12[k] for k in ("Ru_C_global", "Fe_global", "Ru_minus_Fe_global")},
                                     "a0": {k: a0[k] for k in ("Ru_C_global", "Fe_global", "Ru_minus_Fe_global")}}}
    log(f"T3 gates {gates}; consistency {cons}; S4-S0 {total_gap:+.3f} {ranked}")
    return out, points, wf
