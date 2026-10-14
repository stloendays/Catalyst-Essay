"""T2: matched-pressure Fe vs Ru/C in the closed loop (90, 100, 120, 140 bar), bases B94 and B93."""
from __future__ import annotations

from dataclasses import asdict

import closed_loop as CL


def run(states, log=print):
    rows = CL.size_candidates(states)
    out = {"pressures_bar": list(CL.T2_PRESSURES), "grid": CL.GRID, "bases": {k: asdict(v) for k, v in CL.BASES.items()},
           "per_pressure": []}
    opt_rows, term_rows, cross_rows = [], [], []
    for P in CL.T2_PRESSURES:
        at = [r for r in rows if r["P_bar"] == P]
        n_cold = sum(1 for d in states.values() if d["P_bar"] == P)
        n_unres = sum(1 for d in states.values() if d["P_bar"] == P and not d.get("record"))
        counts = {"cold_states": n_cold, "cold_unresolved": n_unres,
                  "unresolved_ids": sorted(d["state_id"] for d in states.values() if d["P_bar"] == P and not d.get("record"))}
        for cat in ("Fe", "Ru"):
            sub = [r for r in at if r["catalyst"] == cat]
            counts[cat] = {"sized": len(sub), "hot_feasible": sum(bool(r.get("feasible")) for r in sub),
                           "above_90m3": sum(bool(r.get("feasible")) and r["bed_m3"] > 90.0 for r in sub),
                           "inert_capped": sum(bool(r.get("feasible")) and r["bed_m3"] <= 90.0 and not r["passes_inert_bound"] for r in sub),
                           "eligible": sum(r["eligible"] for r in sub)}
        entry = {"P_bar": P, "counts": counts, "bases": {}}
        for bname, base in CL.BASES.items():
            fe = CL.describe(CL.best(at, states, base, "Fe"), states)
            ru = CL.describe(CL.best(at, states, base, "Ru"), states)
            gap = None if fe is None or ru is None else ru["decision_USD_t"] - fe["decision_USD_t"]
            terms = None if gap is None else CL.gap_terms(ru, fe)
            if terms is not None:
                assert abs(sum(terms[k] for k in ("excess_feed", "utilities", "inventory", "reactor",
                                                  "compressor_capital", "hot_duty")) - gap) < 1e-8
            cx = CL.crossover(at, states, base)
            entry["bases"][bname] = {"Fe": fe, "Ru": ru, "Ru_minus_Fe": gap, "terms_Ru_minus_Fe": terms,
                                     "crossover": cx}
            for cat, d in (("Fe", fe), ("Ru/C", ru)):
                opt_rows.append({"P_bar": P, "basis": bname, "catalyst": cat, **({} if d is None else
                                 {k: v for k, v in d.items() if k not in ("model", "catalyst")}),
                                 "feasible": d is not None})
            term_rows.append({"P_bar": P, "basis": bname, "Ru_minus_Fe": gap, **(terms or {})})
            cross_rows.append({"P_bar": P, "basis": bname, "verdict": cx["verdict"],
                               "crossover_rates": ";".join(f"{x:.6f}" for x in cx["roots"]),
                               "Ru_minus_Fe_at_0pct": cx["gap_at_0"], "Ru_minus_Fe_at_12pct": cx["gap_at_12pct"]})
            log(f"T2 {P:.0f} bar {bname}: Fe {fe and round(fe['decision_USD_t'], 3)} Ru {ru and round(ru['decision_USD_t'], 3)}"
                f" gap {gap and round(gap, 3)} crossover {cx['verdict']} {[round(x, 5) for x in cx['roots']]}")
        out["per_pressure"].append(entry)
    return out, rows, opt_rows, term_rows, cross_rows
