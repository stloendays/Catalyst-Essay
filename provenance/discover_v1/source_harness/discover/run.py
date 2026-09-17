"""DISCOVER runner: executes a policy under a budget, writes a trace in the E6 schema, records the final answer and the stopping record.

  python discover/run.py --policy A_random --budget 600 --seed 0 [--tag dev]
  python discover/run.py --all --budgets 300,500,800,1200,2000 --seeds 0,1,2   (deterministic development curves)
No LLM is called here; policy E lives in discover/llm_policy.py and is not part of this runner."""
from __future__ import annotations
import argparse, json, sys, traceback
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
from discover.env import DiscoverEnv, BudgetExceeded
from discover.policies import POLICIES, admissible_actions
COST_MODEL = json.loads((ROOT / "DISCOVER_COST_MODEL_V1.json").read_text(encoding="utf-8"))
OUT = ROOT / "discover_runs"


def compact_state(env):
    w, feas = env.current_winner()
    return {"remaining_CU": env.budget, "n_activity": len(env.activity), "n_optimized": len(env.optimized), "feasible_costs": feas, "current_lowest_cost_candidate": w,
            "n_mc": len(env.mc), "n_backward": len(env.backward), "n_reachability": len(env.reachability), "n_levers": len(env.levers)}


def confidence(env, w):
    """P(w has the lowest cost) from the latest multi-metal MC that contains w, else the latest single-metal feasibility of w, else None."""
    for x in reversed(env.mc):
        if w in x["metals"] and len(x["metals"]) >= 2: return {"P_lowest_cost_among_requested": x["P_lowest_cost_among_requested"][w], "basis": f"MC {x['draws']} draws over {x['metals']}"}
    for x in reversed(env.mc):
        if x["metals"] == [w]: return {"feasibility_probability": x["per_metal"][w]["feasibility_probability"], "basis": f"MC {x['draws']} draws on {w}"}
    return None


def final_answer(env):
    w, feas = env.current_winner(); ranking = sorted(feas, key=feas.get)
    atomic_best = max(env.activity, key=env.activity.get) if env.activity else None
    bw = next((b for b in env.backward if w and b["pair"] == [atomic_best, w]), None)
    rc = next((r for r in env.reachability if atomic_best and r["metal"] == atomic_best and "classification" in r), None)
    return {"industrial_winner": w, "feasible_ranking_of_optimized_candidates": ranking, "optimized_costs_USD_t": feas, "infeasible_candidates": [m for m, r in env.optimized.items() if not r["feasible"]],
            "atomic_best": atomic_best, "atomic_best_differs_from_winner": (atomic_best is not None and w is not None and atomic_best != w),
            "parity_multiplier_atomic_best_vs_winner": (bw or {}).get("multiplier"), "reachability_classification": (rc or {}).get("classification"),
            "max_scaling_gain_used": (rc or {}).get("max_gain_across_process_states", (rc or {}).get("max_gain_on_descriptor_manifold_at_reference"))}


def run_policy(policy_name: str, budget: float, seed: int = 0, tag: str = "", max_steps: int = 400, verbose: bool = False, anonymous: bool = False) -> Path:
    pol = POLICIES[policy_name](seed=seed); env = DiscoverEnv(cost_model=COST_MODEL, budget=budget, seed=seed, anonymous=anonymous)
    variant = "anon" if anonymous else "named"
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"); rd = OUT / f"{policy_name}_{variant}_B{int(budget)}_s{seed}{('_' + tag) if tag else ''}_{run_id}"; rd.mkdir(parents=True, exist_ok=True)
    (rd / "identity_mapping.json").write_text(json.dumps(env.identity_mapping(), indent=2), encoding="utf-8")   # scorer-only file; never fed back to a policy
    trace = {"schema": "DISCOVER_TRACE_V1", "policy": policy_name, "task_variant": "anonymous" if anonymous else "named", "budget_CU": budget, "seed": seed, "cost_model": COST_MODEL["version"], "started_utc": run_id, "steps": []}
    why = None; stop_status = None
    for step in range(1, max_steps + 1):
        acts = admissible_actions(env); status = env.stopping_status(min_action_cost=min((a["cost_CU"] for a in acts), default=0.0))
        before = compact_state(env); known = {"activity": sorted(env.activity), "optimized": sorted(env.optimized), "mc": len(env.mc), "backward": len(env.backward), "reachability": len(env.reachability)}
        try: choice, reason, edv = pol.choose(env, acts, status)
        except Exception as e: choice, reason, edv = None, f"policy error: {e!r}", None
        rec = {"step": step, "policy": policy_name, "state_before": before, "known_evidence": known, "candidate_actions": [{k: a[k] for k in a if k in ("action", "args", "cost_CU", "expected_decision_value")} for a in acts],
               "stopping_status_before": status}
        if choice is None:
            rec.update({"chosen_action": "STOP", "action_cost": 0, "reason_for_choice": reason, "expected_decision_value": edv, "result": None, "state_after": before, "remaining_budget": env.budget,
                        "current_winner": status["current_winner"], "current_confidence": confidence(env, status["current_winner"]) if status["current_winner"] else None,
                        "unresolved_questions": {"unresolved_candidates": status["unresolved_candidates"], "S3": status["S3_note"]}, "stop_or_continue": "stop"})
            trace["steps"].append(rec); why = reason; stop_status = status; break
        try:
            result = getattr(env, choice["action"])(**choice["args"]); err = None
        except BudgetExceeded as e: result = None; err = f"BudgetExceeded: {e}"
        except Exception as e: result = None; err = f"{type(e).__name__}: {e}"
        after = compact_state(env); status2 = env.stopping_status()
        rec.update({"chosen_action": choice["action"], "chosen_args": choice["args"], "action_cost": choice["cost_CU"] if err is None else 0, "reason_for_choice": reason, "expected_decision_value": edv,
                    "result": result if err is None else {"error": err}, "state_after": after, "remaining_budget": env.budget, "current_winner": status2["current_winner"],
                    "current_confidence": confidence(env, status2["current_winner"]) if status2["current_winner"] else None,
                    "unresolved_questions": {"unresolved_candidates": status2["unresolved_candidates"], "S3": status2["S3_note"]}, "stop_or_continue": "continue"})
        trace["steps"].append(rec)
        if verbose: print(f"[{step:3d}] {choice['action']:24s} cost {choice['cost_CU']:6.0f} rem {env.budget:8.0f} winner {status2['current_winner']} {('ERR ' + err) if err else ''}")
        if err and err.startswith("BudgetExceeded"): why = err; stop_status = status2; break
    else:
        why = f"max_steps {max_steps} reached"; stop_status = env.stopping_status()
    if stop_status is None: stop_status = env.stopping_status()
    trace["final"] = {"why_stop": why, "remaining_budget": env.budget, "spent_CU": env.budget0 - env.budget, "stopping_status": stop_status,
                      "unresolved_decision_risk": {"unresolved_candidates": stop_status["unresolved_candidates"], "S3": stop_status["S3_note"], "S1": stop_status["S1_winner_identified"], "S2": stop_status["S2_no_unresolved_candidate"], "S3_ok": stop_status["S3_reachability_classified_if_needed"]},
                      "answer": final_answer(env), "ledger": env.ledger}
    (rd / "trace.json").write_text(json.dumps(trace, indent=2, default=str), encoding="utf-8"); env.close()
    return rd


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(); ap.add_argument("--policy", default=None); ap.add_argument("--budget", type=float, default=600); ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--tag", default=""); ap.add_argument("--all", action="store_true"); ap.add_argument("--budgets", default="300,500,800,1200,2000"); ap.add_argument("--seeds", default="0"); ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--anon", action="store_true", help="anonymous task variant (candidate_01..15; identity mapping written for the scorer only)")
    ap.add_argument("--policies", default=",".join(POLICIES), help="comma-separated subset for --all")
    a = ap.parse_args()
    if a.all:
        pols = [p for p in a.policies.split(",") if p in POLICIES]
        for b in [float(x) for x in a.budgets.split(",")]:
            for s in [int(x) for x in a.seeds.split(",")]:
                for p in pols:
                    if p != "A_random" and s != int(a.seeds.split(",")[0]): continue      # deterministic policies: one run per budget
                    rd = run_policy(p, b, s, a.tag, verbose=a.verbose, anonymous=a.anon); t = json.loads((rd / "trace.json").read_text(encoding="utf-8"))
                    print(f"{p:22s} {'anon ' if a.anon else 'named'} B={b:6.0f} s={s} -> winner {t['final']['answer']['industrial_winner']} spent {t['final']['spent_CU']:.0f} steps {len(t['steps'])} stop: {t['final']['why_stop'][:70]}")
    else:
        rd = run_policy(a.policy, a.budget, a.seed, a.tag, verbose=True, anonymous=a.anon); print("trace:", rd / "trace.json")
