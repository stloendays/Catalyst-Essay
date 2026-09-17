"""Policy E — LLM decision-aware agent (interface only; NOT executed in PHASE E development).

The LLM sees: DISCOVER_PROMPT_V1.md (system), DISCOVER_TASK_V1.json with the budget filled in, the action schema as tool definitions,
and after each action the JSON returned by the environment plus the public state and stopping status. It never sees a results.json,
the manifest, or any file. Model name via CEL_AGENT_MODEL (development: gpt-5-mini; formal: 3 tiers x 5 independent runs, later).
Prompt, tools, cost model and scorer are frozen (DISCOVER_*_V1) before the first formal run; failures are recorded, not tuned away."""
from __future__ import annotations
import json, os, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
from discover.policies import Policy, admissible_actions

SCHEMA = json.loads((ROOT / "DISCOVER_ACTION_SCHEMA_V1.json").read_text(encoding="utf-8")) if (ROOT / "DISCOVER_ACTION_SCHEMA_V1.json").exists() else {}


def tool_definitions() -> list[dict]:
    """OpenAI-style tool definitions built from the frozen action schema (names + free-form args + cost)."""
    tools = []
    for name, spec in SCHEMA.get("actions", {}).items():
        tools.append({"type": "function", "function": {"name": name, "description": f"{spec['returns']} Cost: {json.dumps(spec['cost'].get('base_CU'))} base + {json.dumps(spec['cost'].get('per_unit_CU'))} per unit.",
                                                        "parameters": {"type": "object", "properties": {k: {"type": "string", "description": v} for k, v in spec["args"].items()}, "additionalProperties": True}}})
    tools.append({"type": "function", "function": {"name": "STOP", "description": "Stop and report the final answer (only when the stopping rule allows it).", "parameters": {"type": "object", "properties": {"final_answer": {"type": "object"}, "why_stop": {"type": "string"}, "unresolved_decision_risk": {"type": "object"}}}}})
    return tools


class LLMPolicy(Policy):
    name = "E_llm_agent"
    def __init__(self, seed: int = 0, model: str | None = None):
        super().__init__(seed); self.model = model or os.environ.get("CEL_AGENT_MODEL", "gpt-5-mini"); self.messages = None
    def choose(self, env, acts, status):
        raise NotImplementedError("Policy E is not executed in PHASE E development. Formal runs require: frozen DISCOVER_PROMPT_V1 / TOOLS_V1 / COST_MODEL_V1 / SCORER_V1, "
                                  "an API key in .env, and the human's go after protocol review. The tool loop mirrors agent/run_agent.py: system prompt = DISCOVER_PROMPT_V1.md, "
                                  "user = DISCOVER_TASK_V1.json with compute_budget_CU set, tools = tool_definitions(); each tool call is executed by the environment and its JSON plus "
                                  "public_state()/stopping_status() are returned; the trace step is written by discover/run.py in the same schema as policies A-D.")
