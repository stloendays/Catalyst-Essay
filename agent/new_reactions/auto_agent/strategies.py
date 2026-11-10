"""Agent strategies used by runner.py --full:

Planner-Executor: one planning call (high reasoning effort, no tools) writes plan.json - ordered steps with done
  criteria, targets and the risks to watch - before the executor loop starts; the executor marks progress with the
  cheap update_plan tool and may revise a step.
Critic (independent verifier): when the executor calls finish, a separate call with no tools and no access to the
  executor's reasoning checks report.md claim by claim against the run's own outputs (summary_main.json,
  sensitivity.csv, records/verify, config sources). Major issues go back to the executor (at most two rounds); the run
  ends only when the critic passes or the rounds are used up, and the verdicts are kept in critic.json.
"""
from __future__ import annotations

import json
from pathlib import Path

PLAN_SCHEMA = {"type": "object", "additionalProperties": False, "required": ["targets", "steps", "risks"],
               "properties": {
                   "targets": {"type": "string"},
                   "steps": {"type": "array", "items": {"type": "object", "additionalProperties": False,
                             "required": ["id", "goal", "tools", "done_when"],
                             "properties": {"id": {"type": "integer"}, "goal": {"type": "string"},
                                            "tools": {"type": "array", "items": {"type": "string"}},
                                            "done_when": {"type": "string"}}}},
                   "risks": {"type": "array", "items": {"type": "string"}}}}

CRITIC_SCHEMA = {"type": "object", "additionalProperties": False, "required": ["verdict", "issues"],
                 "properties": {
                     "verdict": {"type": "string", "enum": ["pass", "revise"]},
                     "issues": {"type": "array", "items": {"type": "object", "additionalProperties": False,
                                "required": ["severity", "claim", "problem", "evidence"],
                                "properties": {"severity": {"type": "string", "enum": ["major", "minor"]},
                                               "claim": {"type": "string"}, "problem": {"type": "string"},
                                               "evidence": {"type": "string"}}}}}}

UPDATE_PLAN_TOOL = {"type": "function", "name": "update_plan", "strict": True,
                    "description": "Mark a plan step done/blocked/revised with a one-line note (keeps plan.json current).",
                    "parameters": {"type": "object", "additionalProperties": False, "required": ["step_id", "status", "note"],
                                   "properties": {"step_id": {"type": "integer"},
                                                  "status": {"type": "string", "enum": ["done", "in_progress", "blocked", "revised"]},
                                                  "note": {"type": "string"}}}}

PLANNER = """You plan an autonomous research run. Read the task and the tool list, then write the plan the executor will follow: ordered steps (each with the tools it uses and a concrete done-when criterion with numbers), the targets (papers, records), and the risks to watch (e.g. OpenAlex title stemming, papers without usable data, unit errors, unsourced plant parameters, equilibrium limits). Keep it short and specific to this reaction."""

CRITIC = """You are an independent reviewer of an automated research report. You see the report and the raw outputs of the run it is based on. Check every number and claim in the report against those outputs: counts and denominators, costs and shares, rankings and regrets, the bottleneck statement, the chosen catalyst, the sensitivity, the parameter sources (a number presented as sourced must have a source entry), and whether the conclusions go beyond what the data support. Report each problem with the claim, what is wrong and the evidence from the outputs. 'major' = a wrong number, an unsupported conclusion or a missing required section; 'minor' = wording. verdict 'pass' only if there is no major issue."""


def make_plan(run, instructions, tools):
    names = [t.get("name", t["type"]) for t in tools]
    _, text, final = run.respond([{"role": "user", "content": f"Task given to the executor:\n{instructions}\n\nReaction: {run.reaction}\nTools: {names}"}],
                                 PLANNER, None, effort="high", schema=PLAN_SCHEMA)
    run.tok["agent_in"] += final.usage.input_tokens
    run.tok["agent_out"] += final.usage.output_tokens
    run.tok["agent_calls"] += 1
    plan = json.loads(text)
    for s in plan["steps"]:
        s["status"] = "pending"
        s["notes"] = []
    (run.ws / "plan.json").write_text(json.dumps(plan, indent=1, ensure_ascii=False), encoding="utf-8")
    run.log({"plan": plan})
    return plan


def update_plan(run, step_id, status, note):
    p = run.ws / "plan.json"
    plan = json.loads(p.read_text(encoding="utf-8"))
    for s in plan["steps"]:
        if s["id"] == step_id:
            s["status"] = status
            s["notes"].append(note[:300])
    p.write_text(json.dumps(plan, indent=1, ensure_ascii=False), encoding="utf-8")
    left = [s["id"] for s in plan["steps"] if s["status"] != "done"]
    return json.dumps(dict(ok=True, steps_not_done=left))


def _read(p, n=20000):
    return p.read_text(encoding="utf-8", errors="replace")[:n] if p.exists() else "(missing)"


def critique(run, round_no):
    ws = run.ws
    parts = [f"=== report.md ===\n{_read(ws / 'report.md', 30000)}",
             f"=== summary_main.json ===\n{_read(ws / 'summary_main.json')}",
             f"=== sensitivity.csv ===\n{_read(ws / 'sensitivity.csv', 8000)}",
             f"=== ledger.json ===\n{_read(ws / 'ledger.json', 3000)}"]
    cfg = ws / "config.json"
    if cfg.exists():
        c = json.loads(cfg.read_text(encoding="utf-8"))
        parts.append("=== config sources and uncertain ===\n" + json.dumps(dict(sources=c.get("sources"), uncertain=c.get("uncertain"),
                                                                              reference=c.get("reference")), ensure_ascii=False)[:12000])
    for extra in ("chain_result.json", "candidates_summary.json"):
        if (ws / extra).exists():
            parts.append(f"=== {extra} ===\n{_read(ws / extra, 12000)}")
    _, text, final = run.respond([{"role": "user", "content": "\n\n".join(parts)}], CRITIC, None, effort="high", schema=CRITIC_SCHEMA)
    run.tok["agent_in"] += final.usage.input_tokens
    run.tok["agent_out"] += final.usage.output_tokens
    run.tok["agent_calls"] += 1
    res = json.loads(text)
    p = ws / "critic.json"
    hist = json.loads(p.read_text(encoding="utf-8")) if p.exists() else []
    hist.append(dict(round=round_no, **res))
    p.write_text(json.dumps(hist, indent=1, ensure_ascii=False), encoding="utf-8")
    run.log({"critic_round": round_no, "verdict": res["verdict"], "n_major": sum(i["severity"] == "major" for i in res["issues"])})
    return res
