"""T4: KAAP-type staged converter in the closed loop at 90 bar (simplified series-PFR, labelled).

Direct optimisation at Ru finance 0..12 %/y (integer) for bases B94 and B93 and every pattern. States are visited in
ascending order of their converter-independent loop cost; a state is optimised for an (economics, pattern) only if its
loop cost is below the best total already found for that (economics, pattern) — exact pruning, since the converter terms
(inventory, reactor) are nonnegative. Boundaries between winning configurations come from the lower envelope of all
optimised designs re-costed on a 0.01 %-point grid (labelled envelope-derived).
"""
from __future__ import annotations

import math
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, replace

import numpy as np

import closed_loop as CL
import staged as S

P = 90.0
RATES = tuple(range(13))


def econs():
    return [(f"{b}|{r}", replace(base, metal_rate=r / 100.0)) for b, base in CL.BASES.items() for r in RATES]


def _pattern_job(args):
    pattern, states = args
    ec = econs()
    loops = {lab: {sid: S.loop_terms(d["record"], P, 400.0, e)["loop"] for sid, d in states.items()} for lab, e in ec}
    order = sorted(states, key=lambda sid: loops["B94|12"][sid])
    best = {lab: math.inf for lab, _ in ec}
    designs, visited = [], 0
    for sid in order:
        need = [(lab, e) for lab, e in ec if loops[lab][sid] < best[lab]]
        if not need:
            continue
        visited += 1
        for d in S.optimise_state(states[sid], pattern, need, P):
            designs.append(d)
            best[d["econ"]] = min(best[d["econ"]], d["decision_USD_t"])
    return pattern, designs, visited


def run(states, workers=4, log=print):
    at = {sid: d for sid, d in states.items() if d["P_bar"] == P and d.get("record")
          and d["record"]["inlet_inerts_pct"] <= CL.MAX_INERT_PCT + 1e-10}
    n_unres = sum(1 for d in states.values() if d["P_bar"] == P and not d.get("record"))
    n_inert = sum(1 for d in states.values() if d["P_bar"] == P and d.get("record")
                  and d["record"]["inlet_inerts_pct"] > CL.MAX_INERT_PCT + 1e-10)
    with ProcessPoolExecutor(max_workers=min(workers, len(S.PATTERNS))) as ex:
        res = list(ex.map(_pattern_job, [(p, at) for p in S.PATTERNS]))
    library = [d for _, ds, _ in res for d in ds]
    visited = {p: v for p, _, v in res}
    log(f"T4: {len(at)} eligible cold states (unresolved {n_unres}, inert-capped {n_inert}); library {len(library)}; visited {visited}")
    # direct per-rate table
    rate_rows = []
    for bname in CL.BASES:
        for r in RATES:
            lab = f"{bname}|{r}"
            cand = [d for d in library if d["econ"] == lab]
            per_pat = {}
            for d in cand:
                if d["pattern"] not in per_pat or d["decision_USD_t"] < per_pat[d["pattern"]]["decision_USD_t"]:
                    per_pat[d["pattern"]] = d
            cls = {}
            for p, d in per_pat.items():
                c = S.CLASS[p]
                if c not in cls or d["decision_USD_t"] < cls[c]["decision_USD_t"]:
                    cls[c] = d
            win = min(per_pat.values(), key=lambda d: d["decision_USD_t"]) if per_pat else None
            row = {"basis": bname, "Ru_finance_pct": r}
            for c in ("all-Fe", "Fe-first", "all-Ru/C", "Ru/C-first"):
                d = cls.get(c)
                row[c + " USD_t"] = None if d is None else d["decision_USD_t"]
                row[c + " pattern"] = None if d is None else d["pattern"]
                row[c + " Ru_share"] = None if d is None else d["Ru_volume_share"]
            if win is not None:
                eff = "all-Fe" if win["Ru_volume_share"] < 1e-6 else "all-Ru/C" if win["Ru_volume_share"] > 1 - 1e-6 else S.CLASS[win["pattern"]]
                row.update({"winner_class": S.CLASS[win["pattern"]], "winner_pattern": win["pattern"],
                            "winner_effective": eff, "winner_USD_t": win["decision_USD_t"],
                            "winner_Ru_share": win["Ru_volume_share"], "winner_V_tot": win["V_tot"],
                            "winner_state": win["state_id"], "winner_T_in_C": win["T_in_C"],
                            "winner_bed_T_out_C": ";".join(f"{b['catalyst']}:{b['T_out_C']:.1f}" for b in win["beds"]),
                            "staged_minus_allFe": None if ("Fe-first" not in cls or "all-Fe" not in cls)
                            else cls["Fe-first"]["decision_USD_t"] - cls["all-Fe"]["decision_USD_t"]})
            else:
                row["winner_class"] = "NO_FEASIBLE_DESIGN"
            rate_rows.append(row)
            log(f"T4 {bname} {r:2d}%: " + ", ".join(f"{c} {row[c + ' USD_t'] and round(row[c + ' USD_t'], 3)}"
                                                    for c in ("all-Fe", "Fe-first", "all-Ru/C", "Ru/C-first"))
                + f" -> {row.get('winner_pattern')} ({row.get('winner_effective')}, Ru share {row.get('winner_Ru_share') and round(row['winner_Ru_share'], 3)})")
    # envelope-derived boundaries on a fine grid
    loops = {b: {sid: S.loop_terms(at[sid]["record"], P, 400.0, base) for sid in {d["state_id"] for d in library}}
             for b, base in CL.BASES.items()}
    boundaries = {}
    for bname, base in CL.BASES.items():
        grid = np.round(np.arange(0.0, 12.0 + 1e-9, 0.01), 2)
        winners = []
        for r in grid:
            e = replace(base, metal_rate=r / 100.0)
            env = S.envelope(library, loops[bname], P, e)
            if not env:
                winners.append(None)
                continue
            c, (tot, d) = min(env.items(), key=lambda kv: kv[1][0])
            eff = "all-Fe" if d["Ru_volume_share"] < 1e-6 else "all-Ru/C" if d["Ru_volume_share"] > 1 - 1e-6 else c
            winners.append(eff)
        segs, start = [], 0
        for k in range(1, len(grid) + 1):
            if k == len(grid) or winners[k] != winners[start]:
                segs.append({"winner": winners[start], "from_pct": float(grid[start]), "to_pct": float(grid[k - 1])})
                start = k
        boundaries[bname] = segs
        log(f"T4 envelope {bname}: " + "; ".join(f"{s['winner']} {s['from_pct']:.2f}-{s['to_pct']:.2f}%" for s in segs))
    lib_rows = [{k: v for k, v in d.items() if k != "beds"} | {"beds": ";".join(
        f"{b['catalyst']}:{b['T_in_C']:.1f}->{b['T_out_C']:.1f}C,{b['volume_m3']:.3f}m3,{b['extent_fraction']:.4f}" for b in d["beds"])}
        for d in library]
    out = {"P_bar": P, "label": "simplified series-PFR: 3 adiabatic beds, interbed cooling to one common inlet T",
           "patterns": list(S.PATTERNS), "T_max_C": S.TMAX_C, "T_min_C": S.TMIN_C, "gauss_legendre_nodes": S.NGL,
           "bases": {k: asdict(v) for k, v in CL.BASES.items()},
           "eligible_cold_states": len(at), "unresolved_cold_states": n_unres, "inert_capped_cold_states": n_inert,
           "visited_states_per_pattern": visited, "library_size": len(library),
           "per_rate": rate_rows, "envelope_boundaries": boundaries}
    return out, rate_rows, lib_rows
