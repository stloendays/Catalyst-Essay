"""ACSA self-check gate: the agent may score new candidates only after it reproduces all three hand-built cases.

  ammonia   every pure metal's canonical deterministic cost through the batch chain of the alloy extension
            (frozen NH3-FINAL-1.1 run; needs the local harness and its cached response surface);
  methanol  the agent-extracted Gothe et al. 2025 Table 4 entries through the general methanol model, against the
            frozen Table 4 costs (21 entries, inert and recycled CO), including the four hand-built states;
  Au/TiO2   the hand-built inputs and, once extracted, the agent-extracted inputs through agent/au/au_chain.py,
            against the frozen nominal table, the 10,000-draw literature envelope and the semi-open windows.

    python agent/selfcheck_gate.py [--skip-semiopen]

Writes agent/selfcheck_report.json and exits non-zero unless every system passes. Batch runners call require().
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
REPORT = REPO / "agent" / "selfcheck_report.json"
HARNESS = Path(os.environ.get("NH3_HARNESS", r"D:/论文-AI4S/Catalyst_Economic_Leverage_Automation_Harness_v0.1"))
NH3_RUN = "outputs/nh3_final_20260905T134204Z"
TOL_NH3_USD_T = 1e-9
TOL_MEOH_EUR_T = 1e-9


def check_nh3() -> dict:
    import yaml
    sys.path.insert(0, str(HARNESS))
    import harness_core as hc
    run = HARNESS / NH3_RUN
    h = hc.NH3Harness(yaml.safe_load((run / "manifest_resolved.yaml").read_text(encoding="utf-8")), HARNESS)
    response, _cp, cached = h.build_or_load_response()
    if not cached:
        return {"system": "NH3", "pass": False, "error": "response surface not cached; a frozen asset is not rebuilt"}
    canon = json.loads((run / "results.json").read_text(encoding="utf-8"))["deterministic"]["metals"]
    rows = []
    for m, rec in canon.items():
        name = "candidate::" + m + "_check"          # same naming as the alloy batch chain
        hc.MW[name], hc.PRICE[name] = hc.MW[m], hc.PRICE[m]
        try:
            got = h.eval_scenario(name, h.interp_state_vector(response, hc.EN0_CANON[m]))
        except RuntimeError:
            got = None
        finally:
            hc.MW.pop(name, None)
            hc.PRICE.pop(name, None)
        want = None if rec.get("feasible") is None else float(rec["feasible"]["total_cost"])
        chain = None if got is None else float(got["total_cost"])
        ok = (chain is None and want is None) or (None not in (chain, want) and abs(chain - want) < TOL_NH3_USD_T)
        rows.append({"metal": m, "frozen": want, "chain": chain, "match": ok})
    return {"system": "NH3", "metals": len(rows), "mismatches": [r for r in rows if not r["match"]],
            "Fe": next(r["chain"] for r in rows if r["metal"] == "Fe"),
            "Ru": next(r["chain"] for r in rows if r["metal"] == "Ru"),
            "pass": len(rows) == 15 and all(r["match"] for r in rows)}


def check_meoh() -> dict:
    sys.path.insert(0, str(REPO / "analysis" / "meoh_literature_inversion_2026_10_05"))
    import meoh_candidates as M
    check = M.gothe_selfcheck(M.gothe_candidates())
    canon = check[(check.canonical_state != "") & (check.treatment == "inert")]
    return {"system": "MeOH", "entries": int(check.id.nunique()), "comparisons": int(len(check)),
            "max_abs_diff_eur_t": float(check.abs_diff.max()),
            "canonical_states": {r.canonical_state: round(r.agent, 2) for r in canon.itertuples()},
            "pass": check.id.nunique() == 21 and len(canon) == 4 and float(check.abs_diff.max()) < TOL_MEOH_EUR_T}


def check_au(semiopen: bool) -> dict:
    sys.path.insert(0, str(REPO / "agent" / "au"))
    import au_chain
    out = {"system": "Au/TiO2", "handbuilt": au_chain.self_check(au_chain.handbuilt_inputs(), "hand-built", semiopen)}
    extracted = REPO / "agent" / "au" / "out" / "inputs_extracted.json"
    if extracted.exists():
        inp = json.loads(extracted.read_text(encoding="utf-8"))["inputs"]
        # Dispersion cancels in the chain (only its ratio enters), so output reproduction cannot see it: every
        # extracted input must also equal the hand-built value.
        hand = au_chain.handbuilt_inputs()
        diffs = [f"{g}.{k}" for g in hand for k in hand[g]
                 if inp[g].get(k) is None or abs(inp[g][k] - hand[g][k]) > 1e-9 * max(1.0, abs(hand[g][k]))]
        inp = {"reference": inp["reference"], "size_activity": {"tof_exponent": inp["size_activity"]["tof_exponent"]}}
        res = au_chain.self_check(inp, "extracted (agent)", semiopen)
        # A differing input passes only as a discrepancy inside the source: the paper prints both values
        # (agent/au/out/source_discrepancies.json, pages located in the PDF text). Output cells may then differ only
        # in the column that depends on that input alone: the Au mass, which must equal the frozen catalyst mass
        # times the extracted loading.
        disc_path = REPO / "agent" / "au" / "out" / "source_discrepancies.json"
        disc = {d["field"]: d for d in json.loads(disc_path.read_text(encoding="utf-8"))} if disc_path.exists() else {}
        documented = [f for f in diffs if f in disc and disc[f]["pages_extracted_value"] and disc[f]["pages_hand_built_value"]]
        res["input_fields_differing"] = diffs
        res["source_discrepancies"] = [disc[f] for f in documented]
        res["checks"]["inputs_equal_handbuilt_or_both_printed_in_source"] = set(diffs) == set(documented)
        if res["nominal_mismatches"] and set(diffs) <= {"reference.au_loading_mass_fraction"}:
            import csv
            frozen = {float(r["diameter_nm"]): r for r in csv.DictReader(au_chain.FROZEN_TABLE.open(encoding="utf-8"))}
            load = inp["reference"]["au_loading_mass_fraction"]
            explained = all(m["field"] == "required_Au_mass_mg" and
                            abs(m["chain"] - float(frozen[m["diameter_nm"]]["required_catalyst_mass_mg"]) * load) < 6e-4
                            for m in res["nominal_mismatches"])
            res["checks"]["nominal_table_cells_match"] = explained
            res["nominal_mismatches_explained_by_loading"] = explained
        res["pass"] = all(res["checks"].values())
        out["extracted"] = res
    else:
        out["extracted"] = {"pass": False, "error": "no agent-extracted Au inputs yet (agent/au/out/inputs_extracted.json)"}
    out["pass"] = out["handbuilt"]["pass"] and out["extracted"]["pass"]
    return out


def run(semiopen: bool = True) -> dict:
    res = {"timestamp": datetime.now().isoformat(timespec="seconds"),
           "systems": [check_nh3(), check_meoh(), check_au(semiopen)]}
    res["pass"] = all(s["pass"] for s in res["systems"])
    REPORT.write_text(json.dumps(res, indent=1, default=float) + "\n", encoding="utf-8")
    return res


def require(semiopen: bool = True) -> None:
    """Called by batch runners before any new candidate is scored."""
    res = run(semiopen)
    if not res["pass"]:
        failed = [s["system"] for s in res["systems"] if not s["pass"]]
        raise SystemExit(f"ACSA self-check gate failed for {failed}; see {REPORT}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-semiopen", action="store_true")
    a = ap.parse_args()
    r = run(not a.skip_semiopen)
    for s in r["systems"]:
        print(f"{s['system']:8s} {'PASS' if s['pass'] else 'FAIL'}")
    print("GATE", "PASS" if r["pass"] else "FAIL")
    sys.exit(0 if r["pass"] else 1)
