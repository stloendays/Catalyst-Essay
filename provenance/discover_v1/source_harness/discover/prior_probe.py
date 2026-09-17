"""Zero-tool prior-only probe (light enhancement, 2026-09-06): ask the model to answer the DISCOVER task WITHOUT any action, from prior
knowledge only, on the anonymous task (and the named task for comparison). Quantifies how much of the decision a model can produce
from priors alone. Uses the frozen DISCOVER_PROMPT_V1 + a zero-tool instruction; N independent samples; scored with the scorer-only mapping.

  python discover/prior_probe.py --n 5 [--model gpt-5-mini] [--dry-run]
"""
from __future__ import annotations
import argparse, json, sys
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "agent")); sys.path.insert(0, str(ROOT))
from llm_client import call_json, DEFAULT_MODEL

SCHEMA = {"type": "object", "additionalProperties": False,
          "properties": {"industrial_winner": {"type": "string"}, "top3_lowest_cost": {"type": "array", "items": {"type": "string"}},
                         "highest_activity_candidate": {"type": "string"}, "parity_multiplier_guess": {"type": "number"},
                         "reachability_guess": {"type": "string", "enum": ["reachable", "marginal", "unreachable", "unknown"]},
                         "confidence_winner": {"type": "number"}, "reasoning": {"type": "string"}},
          "required": ["industrial_winner", "top3_lowest_cost", "highest_activity_candidate", "parity_multiplier_guess", "reachability_guess", "confidence_winner", "reasoning"]}
ZERO_TOOL = ("\n\nZERO-TOOL PROBE: in this probe you cannot execute any action. Answer the task from prior knowledge and the task data alone: name the "
             "industrial winner, the three lowest-cost candidates in order, the highest-activity candidate, your guess of the intrinsic-activity multiplier "
             "the highest-activity candidate would need for cost parity with the winner, and whether that is reachable on a single-descriptor scaling manifold. "
             "Give a confidence in [0,1] for the winner. Do not ask for tools; answer now.")


def probe(task_file: str, n: int, model: str, dry_run: bool) -> list[dict]:
    system = (ROOT / "DISCOVER_PROMPT_V1.md").read_text(encoding="utf-8") + ZERO_TOOL
    task = json.loads((ROOT / task_file).read_text(encoding="utf-8")); task = dict(task); task["compute_budget_CU"] = 0; task["allowed_actions"] = []
    user = "TASK (no actions available in this probe):\n" + json.dumps(task, indent=1)
    outs = []
    for i in range(n):
        r = call_json(system, user, SCHEMA, "discover_prior_probe", model=model, dry_run=dry_run); r["sample"] = i; outs.append(r)
        if dry_run: break
    return outs


def score(outs: list[dict], mapping: dict | None) -> dict:
    """Scored with the scorer-only ground truth (winner / atomic-best / reachability / break-even) after de-anonymization."""
    sys.path.insert(0, str(ROOT)); import importlib; S = importlib.import_module("DISCOVER_SCORER_V1")
    m = (mapping or {}).get("public_to_real", {}); rows = []
    for o in outs:
        if o.get("_dry_run"): continue
        w = m.get(o["industrial_winner"], o["industrial_winner"]); ab = m.get(o["highest_activity_candidate"], o["highest_activity_candidate"]); top3 = [m.get(x, x) for x in o["top3_lowest_cost"]]
        be = o["parity_multiplier_guess"]
        rows.append({"sample": o["sample"], "winner_public": o["industrial_winner"], "winner_real": w, "winner_correct": w == S.GT["winner"], "atomic_best_real": ab, "atomic_best_correct": ab == S.GT["atomic_best"],
                     "top3_real": top3, "top3_match": top3[:3] == S.GT["feasible_order"][:3], "reachability_guess": o["reachability_guess"], "reachability_correct": o["reachability_guess"] == S.GT["reachability"],
                     "parity_guess": be, "parity_log10_error": (abs(__import__("math").log10(max(be, 1e-9)) - __import__("math").log10(S.GT["break_even"]))) if be else None,
                     "confidence_winner": o["confidence_winner"], "usage": o.get("_usage"), "reasoning": o["reasoning"][:400]})
    n = len(rows) or 1
    return {"n": len(rows), "P_winner_correct": sum(r["winner_correct"] for r in rows) / n, "P_atomic_best_correct": sum(r["atomic_best_correct"] for r in rows) / n,
            "P_top3_exact": sum(r["top3_match"] for r in rows) / n, "P_reachability_correct": sum(r["reachability_correct"] for r in rows) / n,
            "mean_parity_log10_error": (sum(r["parity_log10_error"] for r in rows if r["parity_log10_error"] is not None) / n), "rows": rows}


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(); ap.add_argument("--n", type=int, default=5); ap.add_argument("--model", default=DEFAULT_MODEL); ap.add_argument("--dry-run", action="store_true"); a = ap.parse_args()
    out = {"probe": "DISCOVER_PRIOR_PROBE_V1", "model": a.model, "n": a.n, "utc": datetime.now(timezone.utc).isoformat(), "variants": {}}
    mapping = json.loads((ROOT / "discover/IDENTITY_MAPPING_SCORER_ONLY.json").read_text(encoding="utf-8"))
    for variant, tf, mp in (("anonymous", "DISCOVER_TASK_V1_ANON.json", mapping), ("named", "DISCOVER_TASK_V1.json", None)):
        outs = probe(tf, a.n, a.model, a.dry_run); sc = score(outs, mp); out["variants"][variant] = {"raw": outs, "score": sc}
        print(f"{variant:10s}: n={sc['n']} winner {sc['P_winner_correct']:.2f} atomic-best {sc['P_atomic_best_correct']:.2f} top3 {sc['P_top3_exact']:.2f} reach {sc['P_reachability_correct']:.2f} parity log10 err {sc['mean_parity_log10_error']:.2f}")
        for r in sc["rows"]: print(f"   s{r['sample']}: {r['winner_public']}->{r['winner_real']} conf {r['confidence_winner']:.2f} | atomic {r['atomic_best_real']} | reach {r['reachability_guess']} | parity {r['parity_guess']}")
    (ROOT / "discover_runs").mkdir(exist_ok=True); p = ROOT / "discover_runs" / f"PRIOR_PROBE_{a.model.replace('/', '_')}_{out['utc'][:10]}.json"
    p.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8"); print("wrote", p)
