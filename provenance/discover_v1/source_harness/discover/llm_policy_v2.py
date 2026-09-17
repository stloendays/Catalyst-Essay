"""Policy E2 interface layer — typed tool parameters + explicit remaining-budget display (2026-09-11 teacher request item 3).

This is a NEW, non-frozen interface arm. It does not modify any frozen file: `DISCOVER_PROMPT_V1.md`,
`DISCOVER_ACTION_SCHEMA_V1.json`, `DISCOVER_COST_MODEL_V1.json`, `discover/env.py`, `discover/llm_policy.py` and
`DISCOVER_SCORER_V1.py` are read verbatim. Policy E and E2 therefore differ in exactly two declared respects:

1. tool-parameter validation — frozen E declares every argument as a bare `string` with `additionalProperties: true`,
   so a wrong-typed or invented argument only fails inside the environment as a Python TypeError. E2 declares the real
   JSON types (arrays, numbers, enums), marks the required fields, forbids undeclared keys, and pre-validates each call.
   A violation is still a recorded 0-CU action error — it is never silently repaired — but the error message names the
   offending field, its expected type and the allowed keys.
2. remaining-budget display — frozen E returns `_remaining_CU` inside each tool result. E2 additionally returns a
   `_budget` block: the starting budget, spent and remaining CU, the cheapest affordable action, and the quoted cost of
   every admissible action at the current state, so the model does not have to infer affordability from the cost model.

Action semantics, costs, environment behaviour, stopping rule and scoring are unchanged. The enum values used below are
taken verbatim from the frozen action schema's own argument descriptions; no candidate identity, no result and no
ground-truth information is added.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SCHEMA = json.loads((ROOT / "DISCOVER_ACTION_SCHEMA_V1.json").read_text(encoding="utf-8"))
LEVER_NAMES = ["metal_recovery_fraction", "catalyst_life_y", "electricity_USD_MWh", "max_catalyst_bed_m3"]
VALIDITY_SCOPES = ["window_edges", "bed_cap", "vessel_floor", "dominance"]

# Typed parameter spec per action: name -> (json schema fragment, required?)
_STR = {"type": "string"}
_ID_LIST = {"type": "array", "items": {"type": "string"}, "minItems": 1}
TYPES: dict[str, dict[str, tuple[dict, bool]]] = {
    "INSPECT_CANDIDATES": {},
    "COMPUTE_ACTIVITY": {"metals": (_ID_LIST, True)},
    "READ_PROPERTY_UNCERTAINTY": {"metals": (_ID_LIST, True)},
    "BUILD_PROCESS_WINDOW": {
        "bounds": ({"type": "object", "properties": {"T_C": {"type": "array", "items": {"type": "number"}},
                                                     "P_bar": {"type": "array", "items": {"type": "number"}, "minItems": 2, "maxItems": 2},
                                                     "Tsep_C": {"type": "array", "items": {"type": "number"}, "minItems": 2, "maxItems": 2}},
                    "additionalProperties": False}, False),
        "name": (_STR, False),
    },
    "OPTIMIZE_PROCESS": {"metal": (_STR, True), "window": (_STR, False)},
    "READ_COST_BREAKDOWN": {"metal": (_STR, True)},
    "RUN_MC": {"metals": (_ID_LIST, True), "draws": ({"type": "integer", "enum": [100, 300, 1000]}, False), "window": (_STR, False)},
    "TEST_LEVER": {"lever": ({"type": "string", "enum": LEVER_NAMES}, True), "value": ({"type": "number"}, True), "metals": (_ID_LIST, True), "window": (_STR, False)},
    "BACKWARD": {"pair": ({"type": "array", "items": {"type": "string"}, "minItems": 2, "maxItems": 2}, True),
                 "property": ({"type": "string", "enum": ["activity"]}, False), "window": (_STR, False)},
    "TEST_REACHABILITY": {"metal": (_STR, True), "property": ({"type": "string", "enum": ["activity"]}, False),
                          "scope": ({"type": "string", "enum": ["reference", "window"]}, False), "required_multiplier": ({"type": "number"}, False)},
    "CHECK_MODEL_VALIDITY": {"scope": ({"type": "string", "enum": VALIDITY_SCOPES}, True), "candidate": (_STR, False), "reference": (_STR, False), "window": (_STR, False)},
}


def tool_definitions() -> list[dict]:
    """Typed OpenAI tool definitions built from the frozen action schema (descriptions and costs verbatim)."""
    tools = []
    for name, spec in SCHEMA.get("actions", {}).items():
        types = TYPES[name]
        props = {}
        for arg, desc in spec["args"].items():
            frag, _ = types.get(arg, (_STR, False))
            props[arg] = {**frag, "description": desc}
        required = [a for a, (_, req) in types.items() if req and a in spec["args"]]
        tools.append({"type": "function", "function": {
            "name": name,
            "description": f"{spec['returns']} Cost: {json.dumps(spec['cost'].get('base_CU'))} base + {json.dumps(spec['cost'].get('per_unit_CU'))} per unit.",
            "parameters": {"type": "object", "properties": props, "required": required, "additionalProperties": False},
        }})
    tools.append({"type": "function", "function": {
        "name": "STOP",
        "description": "Stop and report the final answer (only when the stopping rule allows it).",
        "parameters": {"type": "object", "properties": {"final_answer": {"type": "object"}, "why_stop": {"type": "string"}, "unresolved_decision_risk": {"type": "object"}}, "additionalProperties": True},
    }})
    return tools


def validate(name: str, args: dict) -> str | None:
    """Pre-execution parameter validation. Returns None when the call is well-formed, else a corrective message."""
    if name == "STOP":
        return None
    types = TYPES.get(name)
    if types is None:
        return f"unknown action {name}; allowed: {sorted(TYPES) + ['STOP']}"
    allowed = set(SCHEMA["actions"][name]["args"])
    extra = [k for k in (args or {}) if k not in allowed]
    if extra:
        return f"undeclared argument(s) {extra} for {name}; allowed arguments: {sorted(allowed) or 'none'}"
    for arg, (frag, req) in types.items():
        if arg not in (args or {}):
            if req:
                return f"missing required argument '{arg}' for {name}; allowed arguments: {sorted(allowed)}"
            continue
        v = args[arg]
        t = frag.get("type")
        if t == "array":
            if not isinstance(v, list):
                return f"argument '{arg}' of {name} must be a JSON array, got {type(v).__name__}"
            if len(v) < frag.get("minItems", 0) or ("maxItems" in frag and len(v) > frag["maxItems"]):
                return f"argument '{arg}' of {name} must have between {frag.get('minItems', 0)} and {frag.get('maxItems', 'any')} items, got {len(v)}"
        elif t == "object":
            if not isinstance(v, dict):
                return f"argument '{arg}' of {name} must be a JSON object, got {type(v).__name__}"
            bad = [k for k in v if k not in (frag.get("properties") or {})]
            if bad:
                return f"argument '{arg}' of {name} has unknown key(s) {bad}; allowed keys: {sorted(frag.get('properties') or {})}"
        elif t == "integer":
            if isinstance(v, bool) or not isinstance(v, int):
                return f"argument '{arg}' of {name} must be an integer, got {type(v).__name__}"
        elif t == "number":
            if isinstance(v, bool) or not isinstance(v, (int, float)):
                return f"argument '{arg}' of {name} must be a number, got {type(v).__name__}"
        elif t == "string" and not isinstance(v, str):
            return f"argument '{arg}' of {name} must be a string, got {type(v).__name__}"
        if "enum" in frag and v not in frag["enum"]:
            return f"argument '{arg}' of {name} must be one of {frag['enum']}, got {v!r}"
    return None


def budget_block(env, admissible: list[dict]) -> dict:
    """Explicit remaining-budget display appended to every tool result."""
    costs = sorted(({"action": a["action"], "cost_CU": a["cost_CU"]} for a in admissible), key=lambda x: x["cost_CU"])
    return {
        "budget_CU": env.budget0,
        "spent_CU": env.budget0 - env.budget,
        "remaining_CU": env.budget,
        "cheapest_affordable_action_CU": costs[0]["cost_CU"] if costs else None,
        "affordable_actions_now": costs,
        "note": "an action whose quoted cost exceeds remaining_CU is refused and costs 0 CU but consumes a turn",
    }
