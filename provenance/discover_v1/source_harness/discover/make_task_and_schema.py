"""E1/E3: write DISCOVER_ACTION_SCHEMA_V1.json (frozen action space + trace step schema) and DISCOVER_TASK_V1.json (the exact agent-visible task).
Nothing here reads a results.json. The candidate list comes from the environment (alphabetical) with descriptor and price only."""
import json, sys
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
from discover.env import DiscoverEnv, LEVERS, VALIDITY_SCOPES
COST = json.loads((ROOT / "DISCOVER_COST_MODEL_V1.json").read_text(encoding="utf-8"))
env = DiscoverEnv(cost_model=COST); insp = env.INSPECT_CANDIDATES()

ACTIONS = {
    "INSPECT_CANDIDATES": {"args": {}, "returns": "candidate ids (alphabetical), descriptor value and source, metal price, admissible process domain", "cost": COST["actions"]["INSPECT_CANDIDATES"]},
    "COMPUTE_ACTIVITY": {"args": {"metals": "list of candidate ids"}, "returns": "log10 turnover frequency of each requested candidate at the fixed atomic reference condition", "cost": COST["actions"]["COMPUTE_ACTIVITY"]},
    "READ_PROPERTY_UNCERTAINTY": {"args": {"metals": "list of candidate ids"}, "returns": "declared descriptor uncertainty distribution per requested candidate", "cost": COST["actions"]["READ_PROPERTY_UNCERTAINTY"]},
    "BUILD_PROCESS_WINDOW": {"args": {"bounds": "optional {T_C: [values], P_bar: [min, max], Tsep_C: [min, max]} inside the admissible domain; empty = whole domain", "name": "optional window id (use 'full' for the whole domain)"},
                             "returns": "window id, number of self-consistent reactor/recycle/separation states, ranges", "cost": COST["actions"]["BUILD_PROCESS_WINDOW"]},
    "OPTIMIZE_PROCESS": {"args": {"metal": "candidate id", "window": "window id"}, "returns": "lowest-cost feasible state of that candidate in the window (cost, T, P, Tsep, bed volume) or infeasibility with the minimum bed volume", "cost": COST["actions"]["OPTIMIZE_PROCESS"]},
    "READ_COST_BREAKDOWN": {"args": {"metal": "optimized candidate id"}, "returns": "cost pools at that candidate's optimized state", "cost": COST["actions"]["READ_COST_BREAKDOWN"]},
    "RUN_MC": {"args": {"metals": "list of optimized candidate ids", "draws": "100 | 300 | 1000", "window": "window id"}, "returns": "per-candidate feasibility probability and cost quantiles under descriptor uncertainty; among the requested set, P(lowest cost) and pairwise P(lower cost)", "cost": COST["actions"]["RUN_MC"]},
    "TEST_LEVER": {"args": {"lever": f"one of {[v[0] for v in LEVERS.values()]}", "value": "perturbed value inside the plausible range", "metals": "optimized candidate ids", "window": "window id"}, "returns": "re-optimized cost of each requested candidate under the perturbed parameter", "cost": COST["actions"]["TEST_LEVER"],
                   "levers": {v[0]: {"description": v[1], "plausible_range": v[2]} for v in LEVERS.values()}},
    "BACKWARD": {"args": {"pair": "[candidate A, candidate B] (both optimized, B feasible)", "property": "'activity'", "window": "window id"}, "returns": "intrinsic-activity multiplier of A at which its re-optimized cost equals B's optimized cost, and the state at parity", "cost": COST["actions"]["BACKWARD"]},
    "TEST_REACHABILITY": {"args": {"metal": "candidate id", "property": "'activity'", "scope": "'reference' | 'window'", "required_multiplier": "optional multiplier to classify"}, "returns": "largest activity gain obtainable along the frozen descriptor scaling manifold (reference condition; optionally across the window's process states); if a required multiplier is given, classification reachable / marginal / unreachable", "cost": COST["actions"]["TEST_REACHABILITY"]},
    "CHECK_MODEL_VALIDITY": {"args": {"scope": f"one of {list(VALIDITY_SCOPES)}", "candidate": "for dominance", "reference": "for dominance", "window": "window id"}, "returns": "validity flags: optimum on a window edge; bed-cap slack / infeasibility; bed volumes below the vessel-correlation floor; exact state-level dominance of a candidate by a reference", "cost": COST["actions"]["CHECK_MODEL_VALIDITY"]},
}
FORBIDDEN = ["RUN_CANONICAL", "READ_FINAL_RANKING", "READ_GROUND_TRUTH", "FULL_REPORT", "any action returning the 15-candidate ranking, Monte Carlo, backward design and reachability together"]
TRACE_STEP = {"required": ["step", "policy", "state_before", "known_evidence", "candidate_actions", "chosen_action", "action_cost", "reason_for_choice", "expected_decision_value", "result", "state_after", "remaining_budget", "current_winner", "current_confidence", "unresolved_questions", "stop_or_continue"],
              "final": ["why_stop", "remaining_budget", "unresolved_decision_risk", "answer", "ledger"]}
STOPPING = {"S1": "a feasible optimized candidate exists (current lowest-cost candidate identified)",
            "S2": "no unresolved candidate: every candidate is optimized, or is screened as dominated by the current lowest-cost candidate (declared screening rule: lower reference activity AND higher metal price; exact state-level check available via CHECK_MODEL_VALIDITY dominance)",
            "S3": "if the highest-activity candidate differs from the lowest-cost candidate, BACKWARD(pair) and TEST_REACHABILITY(required multiplier) have been executed and a classification exists",
            "S4": "the best remaining expected decision value is below the policy's declared threshold, or the remaining budget cannot pay for any admissible action",
            "may_stop": "(S1 and S2 and S3) or budget exhausted; every stop records why_stop, remaining_budget and unresolved_decision_risk"}
schema = {"version": "DISCOVER_ACTION_SCHEMA_V1", "frozen_utc": datetime.now(timezone.utc).isoformat(), "actions": ACTIONS, "trace_step_schema": TRACE_STEP, "stopping_rule": STOPPING,
          "cost_model": COST["version"], "note": "action outputs contain only what that computation yields; no action returns another candidate's result or any precomputed answer"}
(ROOT / "DISCOVER_ACTION_SCHEMA_V1.json").write_text(json.dumps(schema, indent=2), encoding="utf-8")
# the forbidden-action list is protocol documentation, not part of the agent-visible surface
(ROOT / "discover" / "PROTOCOL_FORBIDDEN_ACTIONS.json").write_text(json.dumps({"forbidden_actions_not_in_agent_surface": FORBIDDEN}, indent=2), encoding="utf-8")

task = {"version": "DISCOVER_TASK_V1", "frozen_utc": datetime.now(timezone.utc).isoformat(),
        "industrial_objective": {"product": "NH3", "capacity_t_per_day": 1000, "objective": "minimize the canonical catalyst/process-dependent cost (USD per tonne NH3) under the admissible process domain and engineering constraints", "cost_boundary": env.domain["cost_boundary"]},
        "candidate_set": insp["candidates"],
        "engineering_constraints": {k: v for k, v in env.domain.items() if k != "cost_boundary"},
        "allowed_actions": list(ACTIONS.keys()), "action_schema": "DISCOVER_ACTION_SCHEMA_V1.json", "cost_model": "DISCOVER_COST_MODEL_V1.json",
        "compute_budget_CU": None,
        "requirement": ["return the best industrial candidate (lowest canonical cost, feasible) with the evidence that supports it",
                        "if the candidate with the highest atomic activity differs from the industrial choice, assess whether that candidate could reach cost parity through intrinsic-activity improvement alone, and classify the requirement as reachable, marginal or unreachable on the frozen descriptor scaling manifold",
                        "spend compute on the calculations whose outcome could change the industrial decision; stop when the decision is stable under the stopping rule",
                        "report for every step: state before, candidate actions, chosen action, reason, expected decision value, cost, evidence returned, updated belief, remaining budget; report why you stopped, remaining budget and unresolved decision risk"],
        "stopping_rule": STOPPING,
        "not_provided": "no candidate ranking, no cost, no feasibility, no parity multiplier and no reachability result is given in advance; all must be computed through the allowed actions"}
task["task_variant"] = "named"
(ROOT / "DISCOVER_TASK_V1.json").write_text(json.dumps(task, indent=2), encoding="utf-8")
# anonymous isomorphic variant: same objective, constraints, actions, requirement; candidate ids candidate_01..15 (seeded permutation held by the scorer)
env_a = DiscoverEnv(cost_model=COST, anonymous=True); insp_a = env_a.INSPECT_CANDIDATES()
task_a = dict(task); task_a["task_variant"] = "anonymous"; task_a["candidate_set"] = insp_a["candidates"]; task_a["version"] = "DISCOVER_TASK_V1_ANON"
task_a["not_provided"] = task["not_provided"] + "; candidate identities are anonymous labels"
(ROOT / "DISCOVER_TASK_V1_ANON.json").write_text(json.dumps(task_a, indent=2), encoding="utf-8")
(ROOT / "discover" / "IDENTITY_MAPPING_SCORER_ONLY.json").write_text(json.dumps(env_a.identity_mapping(), indent=2), encoding="utf-8")
print("wrote DISCOVER_ACTION_SCHEMA_V1.json, DISCOVER_TASK_V1.json, DISCOVER_TASK_V1_ANON.json; named candidates:", [c["id"] for c in insp["candidates"]], "| anon:", [c["id"] for c in insp_a["candidates"]][:3], "...")
