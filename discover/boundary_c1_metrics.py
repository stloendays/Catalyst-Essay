"""
DISCOVER-BOUNDARY-C1 extension metric: CU_to_full_decision (post-hoc, read-only; the frozen scorer is NOT modified).

For every step of a trace we replay the frozen `final_answer` logic (discover/run.py) from the step-level record:
  winner            = step["current_winner"]                     (env.current_winner()[0])
  feasible costs    = step["state_after"]["feasible_costs"]      (env.current_winner()[1])
  activity          = accumulated COMPUTE_ACTIVITY results        (env.activity)
  backward          = accumulated BACKWARD results                (env.backward)
  reachability      = accumulated TEST_REACHABILITY results       (env.reachability)
and evaluate the frozen scorer's three correctness tests (winner / pair / reachability) after de-anonymizing with the
scorer-only identity mapping. CU_to_full_decision = cumulative CU after the first step k such that full(j) is True for
every j >= k up to STOP. Validation (validate_against_frozen): replayed answer at the last step == frozen final.answer, and
CU_to_full is non-null iff DISCOVER_SCORER_V1.score_trace(...)["full_decision_correct"].
"""
from __future__ import annotations
import glob, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
import DISCOVER_SCORER_V1 as S  # frozen; read-only use of GT / DECISION_PAIR / _demap


def _replay_answers(t: dict) -> list[dict]:
    """Return the frozen-style answer dict after each step (public IDs, not yet de-anonymized)."""
    activity: dict = {}; backward: list = []; reach: list = []; out = []
    for s in t["steps"]:
        act = s.get("chosen_action"); res = s.get("result"); args = s.get("chosen_args") or {}
        if isinstance(res, dict) and "error" not in res:
            if act == "COMPUTE_ACTIVITY":
                for k, v in (res.get("log10_TOF_at_reference") or {}).items(): activity[k] = float(v)
            elif act == "BACKWARD" and "pair" in res: backward.append(res)
            elif act == "TEST_REACHABILITY" and "metal" in res: reach.append(res)   # env appends every record; final_answer keeps only those with a classification
        w = s.get("current_winner"); feas = (s.get("state_after") or {}).get("feasible_costs") or {}
        atomic_best = max(activity, key=activity.get) if activity else None
        bw = next((b for b in backward if w and b.get("pair") == [atomic_best, w]), None)
        rc = next((r for r in reach if atomic_best and r.get("metal") == atomic_best and "classification" in r), None)
        out.append({"industrial_winner": w, "optimized_costs_USD_t": dict(feas), "atomic_best": atomic_best,
                    "parity_multiplier_atomic_best_vs_winner": (bw or {}).get("multiplier"), "reachability_classification": (rc or {}).get("classification"),
                    "cum_CU": None})
    cum = 0.0
    for s, a in zip(t["steps"], out):
        cum += s.get("action_cost") or 0; a["cum_CU"] = cum
    return out


def _full(ans: dict) -> bool:
    w = ans["industrial_winner"]; costs = ans["optimized_costs_USD_t"]
    winner_ok = w == S.GT["winner"]
    pair_ok = (S.DECISION_PAIR[0] in costs and S.DECISION_PAIR[1] in costs and costs[S.DECISION_PAIR[1]] < costs[S.DECISION_PAIR[0]])
    reach_ok = ans.get("reachability_classification") == S.GT["reachability"]
    return bool(winner_ok and pair_ok and reach_ok)


def cu_to_full(path: Path) -> dict:
    t = json.loads(path.read_text(encoding="utf-8")); mp = path.parent / "identity_mapping.json"
    m = json.loads(mp.read_text(encoding="utf-8"))["public_to_real"] if mp.exists() else {}
    if m: t = S._demap(t, m)
    answers = _replay_answers(t)
    flags = [_full(a) for a in answers]
    # first k such that all later flags are True
    k = None
    for i in range(len(flags)):
        if all(flags[i:]): k = i; break
    return {"CU_to_full_decision": answers[k]["cum_CU"] if k is not None else None, "full_at_end": bool(flags and flags[-1]), "n_steps": len(flags),
            "first_full_step": (k + 1) if k is not None else None, "replayed_final": answers[-1] if answers else None}


def validate_against_frozen(patterns=("DISCOVER_FORMAL_RUNS_V1/traces/*/*/trace.json", "DISCOVER_CROSS_MODEL_V1/*/traces/*/*/trace.json")) -> dict:
    n = 0; bad_answer = []; bad_flag = []; by_policy = {}
    for pat in patterns:
        for p in sorted(glob.glob(str(ROOT / pat))):
            p = Path(p); t = json.loads(p.read_text(encoding="utf-8"))
            if t["policy"] not in ("E_llm_agent", "D_fixed_voi"): continue
            n += 1; sc = S.score_trace(p); r = cu_to_full(p)
            fin = t["final"]["answer"]; mp = p.parent / "identity_mapping.json"
            m = json.loads(mp.read_text(encoding="utf-8"))["public_to_real"] if mp.exists() else {}
            fin_d = S._demap(fin, m) if m else fin
            rf = r["replayed_final"]
            same = (rf["industrial_winner"] == fin_d["industrial_winner"] and rf["optimized_costs_USD_t"] == fin_d["optimized_costs_USD_t"]
                    and rf["atomic_best"] == fin_d["atomic_best"] and rf["reachability_classification"] == fin_d.get("reachability_classification")
                    and rf["parity_multiplier_atomic_best_vs_winner"] == fin_d.get("parity_multiplier_atomic_best_vs_winner"))
            if not same: bad_answer.append(str(p.relative_to(ROOT)))
            if (r["CU_to_full_decision"] is not None) != bool(sc["full_decision_correct"]): bad_flag.append(str(p.relative_to(ROOT)))
            by_policy.setdefault(t["policy"], 0); by_policy[t["policy"]] += 1
    return {"n_traces": n, "by_policy": by_policy, "answer_mismatches": bad_answer, "flag_mismatches": bad_flag, "gate": "PASS" if not bad_answer and not bad_flag else "FAIL"}


if __name__ == "__main__":
    print(json.dumps(validate_against_frozen(), indent=1))
