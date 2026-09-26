"""DISCOVER-V2-STOP driver (2026-09-26). Preregistration: ../Catalyst-Essay/docs/DISCOVER_STOPPING_TEST_2026-09-26.md Part B.

Inherits from the frozen V1 protocol, byte-for-byte and by import (never copied): task, 11-action schema + STOP, cost model,
environment, base system prompt, scorer, ledger, retry/nudge/unaffordable rules and the trace schema. Nothing frozen is edited.
What changes (the protocol delta, per arm):

  S-hard     the environment ends the episode at the first executed action after which S1 ^ S2 ^ S3 holds.
  S-gate     once S1 ^ S2 ^ S3 holds ("gate armed"), a PAID action is executed only if it is flip-capable:
               - CHECK_MODEL_VALIDITY (any scope);
               - BUILD_PROCESS_WINDOW / OPTIMIZE_PROCESS(m) only while an edge flag is pending: the optimum of the winner or of the
                 atomic-best candidate, or the parity state of their last BACKWARD, lies on an edge of its window that is not a bound
                 of the full domain (m must be one of those two candidates and be re-optimised in a different window);
               - BACKWARD [atomic_best, winner] only after such a re-optimisation (stale parity), TEST_REACHABILITY(atomic_best) only
                 after a new BACKWARD (stale reachability).
             Every other paid action (RUN_MC, TEST_LEVER, repeat windows on validated optima, ...) is rejected: 0 CU, turn consumed,
             reason returned. Three consecutive rejections end the episode (why_stop = gate_rejection_limit). Free actions are never gated.
             S3' = S3 ^ no pending edge flag ^ parity and reachability not stale is reported to the model as may_stop.
  S-anytime  prompt addendum only (minimum-spend scoping first, widen only on an edge flag); no gate, no forced stop.

All arms: final_answer takes the LAST matching BACKWARD and the LAST classified TEST_REACHABILITY for the (atomic_best, winner) pair
(V1 takes the first). The V1 first-record answer is stored alongside as answer_v1_first_record. Scored by the unchanged DISCOVER_SCORER_V1.

Usage (harness root):
  python discover/v2_stop_runner.py prereg
  python discover/v2_stop_runner.py smoke  --arms hard,gate,anytime --budgets 75
  python discover/v2_stop_runner.py run    --arms gate --budgets 75,225,5000 --runs 20 --start-run 0
"""
from __future__ import annotations
import argparse, hashlib, json, os, sys, time, traceback
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "agent"))
from discover.env import DiscoverEnv, BudgetExceeded
from discover.policies import admissible_actions
from discover.run import compact_state, confidence, final_answer, COST_MODEL
from discover.llm_policy import tool_definitions
from discover.formal_e import coerce, call_model, RETRIES, NUDGES, MAX_TURNS, MAX_UNAFFORDABLE   # frozen driver pieces, imported
from llm_client import resolve_api_key

ARMS = ("hard", "gate", "anytime")
MAX_GATE_REJECTS = 3
OUT = ROOT / "DISCOVER_V2_STOP"
PROMPT = (ROOT / "DISCOVER_PROMPT_V1.md").read_text(encoding="utf-8")
ADDENDA = json.loads((ROOT / "DISCOVER_V2_STOP_PROMPT_ADDENDA.json").read_text(encoding="utf-8"))
FROZEN = json.loads((ROOT / "DISCOVER_FROZEN_V1.json").read_text(encoding="utf-8"))
sha = lambda p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
GATED_ALWAYS_OK = {"CHECK_MODEL_VALIDITY"}


def final_answer_v2(env) -> dict:
    """V1 answer with the last (not first) matching BACKWARD / classified reachability for the pair."""
    w, feas = env.current_winner(); ranking = sorted(feas, key=feas.get)
    atomic_best = max(env.activity, key=env.activity.get) if env.activity else None
    bw = next((b for b in reversed(env.backward) if w and b["pair"] == [atomic_best, w]), None)
    rc = next((r for r in reversed(env.reachability) if atomic_best and r["metal"] == atomic_best and "classification" in r), None)
    return {"industrial_winner": w, "feasible_ranking_of_optimized_candidates": ranking, "optimized_costs_USD_t": feas, "infeasible_candidates": [m for m, r in env.optimized.items() if not r["feasible"]],
            "atomic_best": atomic_best, "atomic_best_differs_from_winner": (atomic_best is not None and w is not None and atomic_best != w),
            "parity_multiplier_atomic_best_vs_winner": (bw or {}).get("multiplier"), "reachability_classification": (rc or {}).get("classification"),
            "max_scaling_gain_used": (rc or {}).get("max_gain_across_process_states", (rc or {}).get("max_gain_on_descriptor_manifold_at_reference"))}


def s123(status: dict) -> bool:
    return bool(status["S1_winner_identified"] and status["S2_no_unresolved_candidate"] and status["S3_reachability_classified_if_needed"])


def edge_flags(env) -> dict:
    """Optimum-on-window-edge flags for the winner, the atomic-best candidate and the parity state of their last BACKWARD.
    An edge that coincides with a bound of the full admissible domain is a physical bound, not a window artefact, and is not flagged."""
    dom = env.domain; Tlo, Thi = min(dom["T_C"]), max(dom["T_C"]); Plo, Phi = dom["P_bar"]["min"], dom["P_bar"]["max"]; Slo, Shi = dom["Tsep_C"]["min"], dom["Tsep_C"]["max"]
    w, _ = env.current_winner(); ab = max(env.activity, key=env.activity.get) if len(env.activity) == len(env.candidates) else None
    def on_edge(T, P, S, win):
        wv = env.windows[win]
        t = (T in (min(wv["T_values"]), max(wv["T_values"]))) and T not in (Tlo, Thi)
        p = (P in tuple(wv["P_range"])) and P not in (Plo, Phi)
        s = (S in tuple(wv["Tsep_range"])) and S not in (Slo, Shi)
        return {"T": t, "P": p, "Tsep": s, "any": bool(t or p or s), "window": win}
    out = {}
    for m in {x for x in (w, ab) if x}:
        r = env.optimized.get(m)
        if r and r["feasible"]: out[m] = on_edge(r["T_C"], r["P_bar"], r["Tsep_C"], r["window"])
    if w and ab and ab != w:
        bw = next((b for b in reversed(env.backward) if b["pair"] == [ab, w]), None)
        if bw and bw.get("state_at_parity"):
            st = bw["state_at_parity"]; out["parity_state"] = on_edge(st["T_C"], st["P_bar"], st["Tsep_C"], bw["window"])
    return out


def gate_decision(env, name: str, args: dict, cost: float, g: dict) -> tuple[bool, str]:
    """(admissible, reason) for a PAID action while the gate is armed."""
    if cost <= 0: return True, "free action"
    if name in GATED_ALWAYS_OK: return True, "validity check"
    w, _ = env.current_winner(); ab = max(env.activity, key=env.activity.get) if len(env.activity) == len(env.candidates) else None
    pending = [k for k, v in g["edge_flags"].items() if v["any"]]
    if name == "BUILD_PROCESS_WINDOW":
        return (True, f"edge flag pending on {pending}") if pending else (False, "no optimum of the winner / atomic-best candidate / parity state lies on a window edge; a new window cannot change the decision")
    if name == "OPTIMIZE_PROCESS":
        m = args.get("metal")
        if m not in (w, ab): return False, f"{m} is neither the current winner nor the atomic-best candidate; re-optimising it cannot change the decision"
        need = m in pending or (m == ab and "parity_state" in pending)
        if not need: return False, f"the optimum of {m} is not on a window edge; re-optimisation cannot change the decision"
        if args.get("window", "full") == env.optimized.get(m, {}).get("window"): return False, f"{m} is already optimised in window {args.get('window', 'full')}"
        return True, f"edge flag pending on {m}"
    if name == "BACKWARD":
        if list(args.get("pair") or []) != [ab, w]: return False, f"only the pair [{ab}, {w}] is decision-relevant"
        return (True, "parity stale after re-optimisation") if g["backward_stale"] else (False, "parity for this pair is up to date; a repeat BACKWARD cannot change the decision")
    if name == "TEST_REACHABILITY":
        if args.get("metal") != ab: return False, f"only {ab} is decision-relevant"
        return (True, "reachability stale after new BACKWARD") if g["reachability_stale"] else (False, "reachability is up to date; a repeat test cannot change the decision")
    return False, f"{name} cannot change winner, decision pair or reachability under the stopping rule; the gate rejects it"


def v2_status(env, arm: str, g: dict, status: dict) -> dict:
    ef = edge_flags(env); g["edge_flags"] = ef
    pending = [k for k, v in ef.items() if v["any"]]
    s3p = s123(status) and not pending and not g["backward_stale"] and not g["reachability_stale"]
    out = {"arm": arm, "S123": s123(status), "edge_flags": ef, "S3prime_validated_stop": s3p}
    if arm == "gate":
        adm = []
        if pending: adm += ["BUILD_PROCESS_WINDOW", f"OPTIMIZE_PROCESS({', '.join(pending)})"]
        if g["backward_stale"]: adm.append("BACKWARD")
        if g["reachability_stale"]: adm.append("TEST_REACHABILITY")
        out.update({"gate_armed": g["armed"], "admissible_paid_actions_while_armed": adm + ["CHECK_MODEL_VALIDITY"], "may_stop": bool(g["armed"]), "consecutive_rejections": g["rejects"]})
    return out


def run_one(arm: str, budget: float, run_idx: int, model: str, out_root: Path, params: dict, tag: str = "") -> Path:
    assert arm in ARMS
    variant = "anonymous"; env = DiscoverEnv(cost_model=COST_MODEL, budget=budget, seed=run_idx, anonymous=True)
    task = json.loads((ROOT / "DISCOVER_TASK_V1_ANON.json").read_text(encoding="utf-8")); task["compute_budget_CU"] = budget
    tools = tool_definitions(); prompt = PROMPT + "\n\n" + ADDENDA[arm]
    from openai import OpenAI; import openai as _oa
    client = OpenAI(api_key=resolve_api_key(), base_url=os.environ.get("OPENAI_BASE_URL") or None, timeout=180.0)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"); policy = f"E_v2stop_{arm}"
    rd = out_root / arm / "traces" / variant / f"{policy}_{variant}_B{int(budget)}_r{run_idx}{('_' + tag) if tag else ''}_{ts}"; rd.mkdir(parents=True, exist_ok=True)
    (rd / "identity_mapping.json").write_text(json.dumps(env.identity_mapping(), indent=2), encoding="utf-8")
    messages = [{"role": "system", "content": prompt}, {"role": "user", "content": "TASK:\n" + json.dumps(task, indent=1) + f"\n\nYour compute budget is {budget:.0f} CU. Begin."}]
    trace = {"schema": "DISCOVER_TRACE_V1", "protocol": "DISCOVER-V2-STOP", "arm": arm, "policy": policy, "task_variant": variant, "budget_CU": budget, "seed": run_idx, "run_index": run_idx,
             "cost_model": COST_MODEL["version"], "started_utc": ts, "model_requested": model, "sampling": params, "steps": [],
             "llm_meta": {"response_models": [], "infra_retries": 0, "malformed_turns": 0, "gate_rejections": 0, "tokens": {"prompt": 0, "completion": 0}, "sdk": _oa.__version__}}
    g = {"armed": False, "armed_at_CU": None, "armed_at_step": None, "edge_flags": {}, "backward_stale": False, "reachability_stale": False, "rejects": 0}
    why = None; llm_final = None; unaff = 0; nudges = 0; step = 0; resp_model = None
    for turn in range(1, MAX_TURNS + 1):
        try: msg, usage, resp_model, retries = call_model(client, model, messages, tools, params)
        except RuntimeError as e: why = f"infrastructure_failure: {e}"; break
        trace["llm_meta"]["infra_retries"] += retries; trace["llm_meta"]["response_models"].append(resp_model)
        if usage: trace["llm_meta"]["tokens"]["prompt"] += usage.prompt_tokens; trace["llm_meta"]["tokens"]["completion"] += usage.completion_tokens
        content = msg.content or ""; calls = msg.tool_calls or []
        messages.append({"role": "assistant", "content": content or None, "tool_calls": [{"id": c.id, "type": "function", "function": {"name": c.function.name, "arguments": c.function.arguments}} for c in calls]} if calls else {"role": "assistant", "content": content})
        try: parsed = json.loads(content) if content.strip().startswith("{") else None
        except Exception: parsed = None
        if not calls:
            trace["llm_meta"]["malformed_turns"] += 1; nudges += 1
            if nudges > NUDGES: why = "malformed_action_limit (no tool call after reminders)"; break
            messages.append({"role": "user", "content": "No action was called. Call exactly one tool (an allowed action) or STOP with your final answer."}); continue
        nudges = 0
        for c in calls:
            name = c.function.name
            try: args = json.loads(c.function.arguments or "{}")
            except Exception:
                trace["llm_meta"]["infra_retries"] += 1; messages.append({"role": "tool", "tool_call_id": c.id, "content": json.dumps({"error": "tool arguments were not valid JSON; repeat the call"})}); continue
            args = coerce(name, args); acts = admissible_actions(env); status = env.stopping_status(min_action_cost=min((a["cost_CU"] for a in acts), default=0.0))
            before = compact_state(env); known = {"activity": sorted(env.activity), "optimized": sorted(env.optimized), "mc": len(env.mc), "backward": len(env.backward), "reachability": len(env.reachability)}
            rec = {"step": step + 1, "policy": policy, "state_before": before, "known_evidence": known, "candidate_actions": [{k: a[k] for k in a if k in ("action", "args", "cost_CU")} for a in acts],
                   "llm_candidate_actions": (parsed or {}).get("candidate_actions") if isinstance(parsed, dict) else None, "stopping_status_before": status,
                   "reason_for_choice": (parsed or {}).get("reason") if isinstance(parsed, dict) else (content[:2000] or None), "expected_decision_value": (parsed or {}).get("expected_decision_value") if isinstance(parsed, dict) else None,
                   "llm_state_before": (parsed or {}).get("state_before") if isinstance(parsed, dict) else None, "gate_before": {"armed": g["armed"], "backward_stale": g["backward_stale"], "reachability_stale": g["reachability_stale"], "edge_flags": g["edge_flags"]}}
            if name == "STOP":
                step += 1; llm_final = args
                rec.update({"chosen_action": "STOP", "chosen_args": args, "action_cost": 0, "result": None, "state_after": before, "remaining_budget": env.budget, "current_winner": status["current_winner"],
                            "current_confidence": confidence(env, status["current_winner"]) if status["current_winner"] else None, "unresolved_questions": {"unresolved_candidates": status["unresolved_candidates"], "S3": status["S3_note"]}, "stop_or_continue": "stop"})
                trace["steps"].append(rec); why = f"agent STOP: {str(args.get('why_stop', ''))[:300]}"; break
            step += 1; err = None; result = None; cost = 0.0; gated = None
            try:
                if not hasattr(env, name) or name.startswith("_"): raise ValueError(f"unknown action {name}; allowed: {[t['function']['name'] for t in tools]}")
                cost = env.quote(name, args)
                if arm == "gate" and g["armed"]:
                    ok, reason = gate_decision(env, name, args, cost, g); gated = {"admissible": ok, "reason": reason}
                    if not ok: raise PermissionError(f"GateRejected: {reason}")
                result = getattr(env, name)(**args)
                if arm == "gate" and g["armed"]:
                    if name == "OPTIMIZE_PROCESS": g["backward_stale"] = True
                    if name == "BACKWARD": g["backward_stale"] = False; g["reachability_stale"] = True
                    if name == "TEST_REACHABILITY" and "classification" in (result or {}): g["reachability_stale"] = False
            except BudgetExceeded as e: err = f"BudgetExceeded: {e}"; unaff += 1; cost = 0.0
            except PermissionError as e: err = str(e); cost = 0.0; g["rejects"] += 1; trace["llm_meta"]["gate_rejections"] += 1
            except TypeError as e: err = f"InvalidArguments: {e}"; cost = 0.0
            except Exception as e: err = f"{type(e).__name__}: {e}"; cost = 0.0
            if err is None: unaff = 0; g["rejects"] = 0
            after = compact_state(env); status2 = env.stopping_status()
            if s123(status2) and not g["armed"]: g["armed"] = True; g["armed_at_CU"] = env.budget0 - env.budget; g["armed_at_step"] = step
            elif not s123(status2) and g["armed"]: g["armed"] = False
            v2 = v2_status(env, arm, g, status2)
            rec.update({"chosen_action": name, "chosen_args": args, "action_cost": cost if err is None else 0, "result": result if err is None else {"error": err}, "state_after": after, "remaining_budget": env.budget,
                        "current_winner": status2["current_winner"], "current_confidence": confidence(env, status2["current_winner"]) if status2["current_winner"] else None,
                        "unresolved_questions": {"unresolved_candidates": status2["unresolved_candidates"], "S3": status2["S3_note"]}, "stop_or_continue": "continue", "gate": gated, "v2_status_after": v2})
            trace["steps"].append(rec)
            payload = (result if err is None else {"error": err}); payload = dict(payload) if isinstance(payload, dict) else {"result": payload}
            payload["_remaining_CU"] = env.budget; payload["_stopping_status"] = {k: status2[k] for k in ("S1_winner_identified", "S2_no_unresolved_candidate", "unresolved_candidates", "S3_reachability_classified_if_needed", "S3_note", "may_stop")}
            payload["_v2"] = v2
            messages.append({"role": "tool", "tool_call_id": c.id, "content": json.dumps(payload, default=str)})
            if unaff >= MAX_UNAFFORDABLE: why = "budget_exhausted (3 consecutive unaffordable actions)"; break
            if arm == "hard" and err is None and s123(status2): rec["stop_or_continue"] = "env_forced_stop"; why = "env_forced_stop: S1^S2^S3 satisfied (S-hard)"; break
            if arm == "gate" and g["rejects"] >= MAX_GATE_REJECTS: why = f"gate_rejection_limit ({MAX_GATE_REJECTS} consecutive rejected paid actions after S1^S2^S3)"; break
        if why: break
    else:
        why = f"max_turns {MAX_TURNS} reached"
    st = env.stopping_status(); v2 = v2_status(env, arm, g, st)
    trace["final"] = {"why_stop": why, "remaining_budget": env.budget, "spent_CU": env.budget0 - env.budget, "stopping_status": st, "v2_status": v2,
                      "gate": {"armed_at_CU": g["armed_at_CU"], "armed_at_step": g["armed_at_step"], "rejections": trace["llm_meta"]["gate_rejections"]},
                      "unresolved_decision_risk": {"unresolved_candidates": st["unresolved_candidates"], "S3": st["S3_note"], "S1": st["S1_winner_identified"], "S2": st["S2_no_unresolved_candidate"], "S3_ok": st["S3_reachability_classified_if_needed"]},
                      "answer": final_answer_v2(env), "answer_v1_first_record": final_answer(env), "llm_final_answer": llm_final, "ledger": env.ledger}
    trace["metadata"] = {"protocol": "DISCOVER-V2-STOP", "arm": arm, "model_requested": model, "response_model": resp_model, "sampling": params, "reasoning": "API default (not set)", "temperature": "API default (not set)", "tool_choice": "auto",
                         "tools": [t["function"]["name"] for t in tools], "base_prompt_sha256": sha("DISCOVER_PROMPT_V1.md"), "addenda_sha256": sha("DISCOVER_V2_STOP_PROMPT_ADDENDA.json"), "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
                         "task_file": "DISCOVER_TASK_V1_ANON.json", "frozen_sha256": sha("DISCOVER_FROZEN_V1.json"), "driver_sha256": sha("discover/v2_stop_runner.py"), "frozen_driver_sha256": sha("discover/formal_e.py"),
                         "final_answer_rule": "last matching BACKWARD / last classified TEST_REACHABILITY for (atomic_best, winner); V1 first-record answer stored as answer_v1_first_record",
                         "git": "harness root is not a git repository; provenance = DISCOVER_FROZEN_V1.json hashes + PREREG_V2_STOP.json", "finished_utc": datetime.now(timezone.utc).isoformat()}
    (rd / "trace.json").write_text(json.dumps(trace, indent=2, default=str), encoding="utf-8"); (rd / "messages.json").write_text(json.dumps(messages, indent=1, default=str), encoding="utf-8"); env.close()
    return rd


def prereg() -> dict:
    mism = [f for f, h in FROZEN["sha256"].items() if sha(f) != h]
    rec = {"protocol": "DISCOVER-V2-STOP", "utc": datetime.now(timezone.utc).isoformat(), "frozen_v1_hashcheck": "PASS" if not mism else f"FAIL {mism}",
           "arms": list(ARMS), "cells_CU": [75, 225, 5000], "runs_per_cell": 20, "variant": "anonymous", "model": "gpt-5.5-2026-04-23", "sampling": "API defaults",
           "gates": {"completion": ">= 19/20 per cell and arm (frozen scorer)", "post_rule_spend": "median 0 CU in S-hard and S-gate at 75 and 5000 CU",
                     "false_positive_S3prime": "0/60 across S-gate cells", "allowance_invariance": "S-anytime median final spend at 225 CU within 25 CU of the 75-CU median", "parity_recovery": "reported, not gated"},
           "protocol_delta": {"final_answer_rule": "last matching record (V1: first)", "hard": "env-forced stop at first S1^S2^S3", "gate": f"flip-capability gate on paid actions after S1^S2^S3; {MAX_GATE_REJECTS} consecutive rejections end the run", "anytime": "prompt addendum only"},
           "sha256": {"driver": sha("discover/v2_stop_runner.py"), "addenda": sha("DISCOVER_V2_STOP_PROMPT_ADDENDA.json"), "base_prompt": sha("DISCOVER_PROMPT_V1.md"), "frozen": sha("DISCOVER_FROZEN_V1.json"), "formal_e": sha("discover/formal_e.py"), "env": sha("discover/env.py"), "scorer": sha("DISCOVER_SCORER_V1.py")},
           "addenda": ADDENDA}
    OUT.mkdir(parents=True, exist_ok=True); p = OUT / "PREREG_V2_STOP.json"
    if p.exists(): p = OUT / f"PREREG_V2_STOP_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    p.write_text(json.dumps(rec, indent=2), encoding="utf-8"); print(json.dumps({k: v for k, v in rec.items() if k != "addenda"}, indent=1)); print("->", p); return rec


def batch(arms: list[str], budgets: list[float], runs: int, start: int, tag: str, model: str, sub: str):
    (OUT / "logs").mkdir(parents=True, exist_ok=True); log = OUT / "logs" / f"{sub}_{'-'.join(arms)}_B{'-'.join(f'{b:.0f}' for b in budgets)}.log"
    with open(log, "a", encoding="utf-8") as lf:
        for arm in arms:
            for b in budgets:
                for r in range(start, start + runs):
                    t0 = time.time()
                    try:
                        rd = run_one(arm, float(b), r, model, OUT / sub, {}, tag); t = json.loads((rd / "trace.json").read_text(encoding="utf-8"))
                        line = (f"{arm:7s} B={b:.0f} r={r} -> winner {t['final']['answer']['industrial_winner']} reach {t['final']['answer']['reachability_classification']} spent {t['final']['spent_CU']:.0f} "
                                f"armed_at {t['final']['gate']['armed_at_CU']} rej {t['final']['gate']['rejections']} steps {len(t['steps'])} tokens {t['llm_meta']['tokens']} {time.time()-t0:.0f}s | {t['final']['why_stop'][:70]}")
                    except Exception as e:
                        line = f"{arm:7s} B={b:.0f} r={r} -> DRIVER EXCEPTION {e!r}\n{traceback.format_exc()}"
                    print(line, flush=True); lf.write(line + "\n"); lf.flush()


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(); ap.add_argument("cmd", choices=["prereg", "smoke", "run"])
    ap.add_argument("--arms", default="hard,gate,anytime"); ap.add_argument("--budgets", default="75,225,5000"); ap.add_argument("--runs", type=int, default=20); ap.add_argument("--start-run", type=int, default=0)
    ap.add_argument("--model", default="gpt-5.5-2026-04-23"); ap.add_argument("--tag", default="v2stop")
    a = ap.parse_args(); arms = [x for x in a.arms.split(",") if x]; budgets = [float(x) for x in a.budgets.split(",")]
    if a.cmd == "prereg": prereg()
    elif a.cmd == "smoke": batch(arms, budgets, 1, 99, "smoke", a.model, "smoke")
    else: batch(arms, budgets, a.runs, a.start_run, a.tag, a.model, "runs")
