"""Policy E2 driver — frozen DISCOVER protocol with a budget-aware, type-validated tool interface (2026-09-11 item 3).

E2 is a declared interface arm, not a new protocol. Everything scientific is imported from the frozen layer:
  system prompt  = DISCOVER_PROMPT_V1.md (verbatim, unchanged)
  task           = DISCOVER_TASK_V1{,_ANON}.json with compute_budget_CU filled in memory (unchanged)
  environment    = discover.env.DiscoverEnv (frozen), cost model DISCOVER_COST_MODEL_V1.json (frozen)
  scoring        = DISCOVER_SCORER_V1.py (frozen), applied to the same trace schema
  argument coercion = discover.formal_e.coerce (the identical frozen function, applied first)

Exactly two declared deltas versus policy E, both in discover/llm_policy_v2.py:
  1. typed tool parameters + pre-execution validation (undeclared key, wrong type, bad enum, missing required field)
     are reported as named 0-CU action errors instead of surfacing as a Python TypeError inside the environment;
  2. an explicit `_budget` block (starting/spent/remaining CU, cheapest affordable action, quoted cost of every
     admissible action) is returned with every tool result.

Traces are written with policy "E2_llm_agent_budget_aware" so that no analysis can pool them with frozen policy-E runs.

Usage (from harness root):
  python discover/formal_e2.py --variant anonymous --model gpt-5.4-mini-2026-03-17 --budgets 175 --runs 20 --out DISCOVER_BOUNDARY_C1/e2 --tag c1e2
"""
from __future__ import annotations
import argparse, hashlib, json, os, sys, time, traceback
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "agent"))
from discover.env import DiscoverEnv, BudgetExceeded
from discover.policies import admissible_actions
from discover.run import compact_state, confidence, final_answer, COST_MODEL
from discover.formal_e import RETRIES, NUDGES, MAX_TURNS, MAX_UNAFFORDABLE, PROMPT, call_model, coerce
from discover.llm_policy_v2 import tool_definitions, validate, budget_block
from llm_client import resolve_api_key

POLICY = "E2_llm_agent_budget_aware"
sha = lambda p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


def run_one(variant: str, budget: float, run_idx: int, model: str, out_root: Path, params: dict, tag: str = "") -> Path:
    anonymous = variant == "anonymous"
    env = DiscoverEnv(cost_model=COST_MODEL, budget=budget, seed=run_idx, anonymous=anonymous)
    task = json.loads((ROOT / ("DISCOVER_TASK_V1_ANON.json" if anonymous else "DISCOVER_TASK_V1.json")).read_text(encoding="utf-8"))
    task["compute_budget_CU"] = budget
    tools = tool_definitions()
    from openai import OpenAI
    import openai as _oa
    client = OpenAI(api_key=resolve_api_key(), base_url=os.environ.get("OPENAI_BASE_URL") or None, timeout=180.0)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    rd = out_root / "traces" / variant / f"E2_llm_agent_{variant}_B{int(budget)}_r{run_idx}{('_' + tag) if tag else ''}_{ts}"
    rd.mkdir(parents=True, exist_ok=True)
    (rd / "identity_mapping.json").write_text(json.dumps(env.identity_mapping(), indent=2), encoding="utf-8")
    messages = [{"role": "system", "content": PROMPT},
                {"role": "user", "content": "TASK:\n" + json.dumps(task, indent=1) + f"\n\nYour compute budget is {budget:.0f} CU. Begin."}]
    trace = {"schema": "DISCOVER_TRACE_V1", "policy": POLICY, "task_variant": variant, "budget_CU": budget, "seed": run_idx, "run_index": run_idx,
             "cost_model": COST_MODEL["version"], "started_utc": ts, "model_requested": model, "sampling": params,
             "interface_variant": {"name": "E2_budget_aware_typed_tools", "typed_tool_parameters": True, "pre_execution_validation": True, "remaining_budget_block": True,
                                   "prompt_modified": False, "environment_modified": False, "cost_model_modified": False},
             "steps": [], "llm_meta": {"response_models": [], "infra_retries": 0, "malformed_turns": 0, "validation_rejections": 0, "tokens": {"prompt": 0, "completion": 0}, "sdk": _oa.__version__}}
    why = None; llm_final = None; unaff = 0; nudges = 0; step = 0; resp_model = None
    for turn in range(1, MAX_TURNS + 1):
        try:
            msg, usage, resp_model, retries = call_model(client, model, messages, tools, params)
        except RuntimeError as e:
            why = f"infrastructure_failure: {e}"; break
        trace["llm_meta"]["infra_retries"] += retries
        trace["llm_meta"]["response_models"].append(resp_model)
        if usage:
            trace["llm_meta"]["tokens"]["prompt"] += usage.prompt_tokens
            trace["llm_meta"]["tokens"]["completion"] += usage.completion_tokens
        content = msg.content or ""; calls = msg.tool_calls or []
        messages.append({"role": "assistant", "content": content or None,
                         "tool_calls": [{"id": c.id, "type": "function", "function": {"name": c.function.name, "arguments": c.function.arguments}} for c in calls]} if calls
                        else {"role": "assistant", "content": content})
        try:
            parsed = json.loads(content) if content.strip().startswith("{") else None
        except Exception:
            parsed = None
        if not calls:
            trace["llm_meta"]["malformed_turns"] += 1; nudges += 1
            if nudges > NUDGES:
                why = "malformed_action_limit (no tool call after reminders)"; break
            messages.append({"role": "user", "content": "No action was called. Call exactly one tool (an allowed action) or STOP with your final answer."}); continue
        nudges = 0
        for c in calls:
            name = c.function.name
            try:
                args = json.loads(c.function.arguments or "{}")
            except Exception:
                trace["llm_meta"]["infra_retries"] += 1
                messages.append({"role": "tool", "tool_call_id": c.id, "content": json.dumps({"error": "tool arguments were not valid JSON; repeat the call"})}); continue
            args = coerce(name, args)
            acts = admissible_actions(env)
            status = env.stopping_status(min_action_cost=min((a["cost_CU"] for a in acts), default=0.0))
            before = compact_state(env)
            known = {"activity": sorted(env.activity), "optimized": sorted(env.optimized), "mc": len(env.mc), "backward": len(env.backward), "reachability": len(env.reachability)}
            rec = {"step": step + 1, "policy": POLICY, "state_before": before, "known_evidence": known,
                   "candidate_actions": [{k: a[k] for k in a if k in ("action", "args", "cost_CU")} for a in acts],
                   "llm_candidate_actions": (parsed or {}).get("candidate_actions") if isinstance(parsed, dict) else None, "stopping_status_before": status,
                   "reason_for_choice": (parsed or {}).get("reason") if isinstance(parsed, dict) else (content[:2000] or None),
                   "expected_decision_value": (parsed or {}).get("expected_decision_value") if isinstance(parsed, dict) else None,
                   "llm_state_before": (parsed or {}).get("state_before") if isinstance(parsed, dict) else None}
            if name == "STOP":
                step += 1; llm_final = args
                rec.update({"chosen_action": "STOP", "chosen_args": args, "action_cost": 0, "result": None, "state_after": before, "remaining_budget": env.budget,
                            "current_winner": status["current_winner"], "current_confidence": confidence(env, status["current_winner"]) if status["current_winner"] else None,
                            "unresolved_questions": {"unresolved_candidates": status["unresolved_candidates"], "S3": status["S3_note"]}, "stop_or_continue": "stop"})
                trace["steps"].append(rec); why = f"agent STOP: {str(args.get('why_stop', ''))[:300]}"; break
            step += 1; err = None; result = None; cost = 0.0
            bad = validate(name, args)
            if bad is not None:
                err = f"InvalidArguments: {bad}"; trace["llm_meta"]["validation_rejections"] += 1
            else:
                try:
                    if not hasattr(env, name) or name.startswith("_"):
                        raise ValueError(f"unknown action {name}; allowed: {[t['function']['name'] for t in tools]}")
                    cost = env.quote(name, args); result = getattr(env, name)(**args)
                except BudgetExceeded as e:
                    err = f"BudgetExceeded: {e}"; unaff += 1; cost = 0.0
                except TypeError as e:
                    err = f"InvalidArguments: {e}"; cost = 0.0
                except Exception as e:
                    err = f"{type(e).__name__}: {e}"; cost = 0.0
            if err is None:
                unaff = 0
            after = compact_state(env); status2 = env.stopping_status()
            rec.update({"chosen_action": name, "chosen_args": args, "action_cost": cost if err is None else 0, "result": result if err is None else {"error": err},
                        "state_after": after, "remaining_budget": env.budget, "current_winner": status2["current_winner"],
                        "current_confidence": confidence(env, status2["current_winner"]) if status2["current_winner"] else None,
                        "unresolved_questions": {"unresolved_candidates": status2["unresolved_candidates"], "S3": status2["S3_note"]}, "stop_or_continue": "continue"})
            trace["steps"].append(rec)
            payload = (result if err is None else {"error": err})
            payload = dict(payload) if isinstance(payload, dict) else {"result": payload}
            payload["_remaining_CU"] = env.budget
            payload["_budget"] = budget_block(env, admissible_actions(env))
            payload["_stopping_status"] = {k: status2[k] for k in ("S1_winner_identified", "S2_no_unresolved_candidate", "unresolved_candidates", "S3_reachability_classified_if_needed", "S3_note", "may_stop")}
            messages.append({"role": "tool", "tool_call_id": c.id, "content": json.dumps(payload, default=str)})
            if unaff >= MAX_UNAFFORDABLE:
                why = "budget_exhausted (3 consecutive unaffordable actions)"; break
        if why:
            break
    else:
        why = f"max_turns {MAX_TURNS} reached"
    st = env.stopping_status()
    trace["final"] = {"why_stop": why, "remaining_budget": env.budget, "spent_CU": env.budget0 - env.budget, "stopping_status": st,
                      "unresolved_decision_risk": {"unresolved_candidates": st["unresolved_candidates"], "S3": st["S3_note"], "S1": st["S1_winner_identified"],
                                                   "S2": st["S2_no_unresolved_candidate"], "S3_ok": st["S3_reachability_classified_if_needed"]},
                      "answer": final_answer(env), "llm_final_answer": llm_final, "ledger": env.ledger}
    trace["metadata"] = {"model_requested": model, "response_model": resp_model, "sampling": params, "reasoning": "API default (not set)", "temperature": "API default (not set)",
                         "tool_choice": "auto", "tools": [t["function"]["name"] for t in tools], "prompt_sha256": sha("DISCOVER_PROMPT_V1.md"),
                         "task_file": "DISCOVER_TASK_V1_ANON.json" if anonymous else "DISCOVER_TASK_V1.json", "frozen_sha256": sha("DISCOVER_FROZEN_V1.json"),
                         "driver_sha256": sha("discover/formal_e2.py"), "interface_sha256": sha("discover/llm_policy_v2.py"), "frozen_driver_sha256": sha("discover/formal_e.py"),
                         "git": "harness root is not a git repository; provenance = DISCOVER_FROZEN_V1.json hashes", "finished_utc": datetime.now(timezone.utc).isoformat()}
    (rd / "trace.json").write_text(json.dumps(trace, indent=2, default=str), encoding="utf-8")
    (rd / "messages.json").write_text(json.dumps(messages, indent=1, default=str), encoding="utf-8")
    env.close()
    return rd


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", choices=["anonymous", "named"], default="anonymous")
    ap.add_argument("--budgets", default="175")
    ap.add_argument("--runs", type=int, default=20)
    ap.add_argument("--model", default="gpt-5.4-mini-2026-03-17")
    ap.add_argument("--out", default="DISCOVER_BOUNDARY_C1/e2")
    ap.add_argument("--tag", default="c1e2")
    ap.add_argument("--start-run", type=int, default=0)
    a = ap.parse_args()
    out_root = ROOT / a.out
    log = ROOT / "DISCOVER_BOUNDARY_C1" / "logs" / f"e2_{a.model}_B{a.budgets.replace(',', '-')}.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    params = {}
    with log.open("a", encoding="utf-8") as lf:
        for b in [float(x) for x in a.budgets.split(",")]:
            for r in range(a.start_run, a.start_run + a.runs):
                t0 = time.time()
                try:
                    rd = run_one(a.variant, b, r, a.model, out_root, params, a.tag)
                    t = json.loads((rd / "trace.json").read_text(encoding="utf-8"))
                    line = (f"{a.model} E2 B={b:.0f} r={r} -> winner {t['final']['answer']['industrial_winner']} spent {t['final']['spent_CU']:.0f} "
                            f"steps {len(t['steps'])} tokens {t['llm_meta']['tokens']} valrej {t['llm_meta']['validation_rejections']} "
                            f"retries {t['llm_meta']['infra_retries']} {time.time()-t0:.0f}s | {t['final']['why_stop'][:70]}")
                except Exception as e:
                    line = f"{a.model} E2 B={b:.0f} r={r} -> DRIVER EXCEPTION {e!r}\n{traceback.format_exc()}"
                print(line, flush=True); lf.write(line + "\n"); lf.flush()
