"""
DISCOVER-BOUNDARY-C1 per-cell decision-component counts (2026-09-16).

Emits, for every scored cell, how many runs recovered each component of the complete decision and how many reached each
stage of the decision chain. These counts are produced by the frozen scorer and by direct trace inspection; they are the
inputs Extended Data Fig. 1 needs and they are not otherwise available as a committed CSV.

Read-only replay: no model is called, no frozen file is modified, no scientific value is recomputed.

Usage (from harness root):
  python discover/c1_decision_components.py
"""
from __future__ import annotations
import csv, glob, json, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "discover"))
import DISCOVER_SCORER_V1 as S

OUT = ROOT / "DISCOVER_BOUNDARY_C1" / "data"
TIER = {"gpt-5.5-2026-04-23": "strong", "gpt-5.4-mini-2026-03-17": "mini", "gpt-5.4-nano-2026-03-17": "nano"}
GLOBS = [
    "DISCOVER_BOUNDARY_C1/runs/*/traces/anonymous/*",
    "DISCOVER_BOUNDARY_C1/e2/traces/anonymous/*",
]


def ran(steps, action, key=None) -> bool:
    for s in steps:
        if s.get("chosen_action") != action:
            continue
        r = s.get("result")
        if isinstance(r, dict) and "error" not in r and (key is None or key in r):
            return True
    return False


def main() -> int:
    cells: dict[tuple, list[dict]] = {}
    for pat in GLOBS:
        for p in glob.glob(str(ROOT / pat / "trace.json")):
            path = Path(p)
            t = json.loads(path.read_text(encoding="utf-8"))
            if str(t["final"]["why_stop"]).startswith("infrastructure_failure"):
                continue
            sc = S.score_trace(path)
            model = t["metadata"]["model_requested"]
            key = (TIER.get(model, model), "E2" if t["policy"].startswith("E2_") else "E", int(float(t["budget_CU"])))
            steps = t["steps"]
            cells.setdefault(key, []).append({
                "winner": int(sc["winner_correct"]),
                "pair": int(sc["pair_decision_correct"]),
                "reach": int(sc["reachability_correct"]),
                "full": int(sc["full_decision_correct"]),
                "built_window": int(ran(steps, "BUILD_PROCESS_WINDOW", "n_states")),
                "ran_backward": int(ran(steps, "BACKWARD", "multiplier")),
                "ran_reachability": int(ran(steps, "TEST_REACHABILITY", "classification")),
                "malformed_turns": int(t.get("llm_meta", {}).get("malformed_turns", 0) or 0),
                "validation_rejections": int(t.get("llm_meta", {}).get("validation_rejections", 0) or 0),
            })

    rows = []
    order = {"strong": 0, "mini": 1, "nano": 2}
    for (tier, arm, b), rs in sorted(cells.items(), key=lambda kv: (order[kv[0][0]], kv[0][2], kv[0][1])):
        n = len(rs)
        rows.append({
            "tier": tier, "arm": arm, "budget_CU": b, "n": n,
            "k_winner": sum(r["winner"] for r in rs),
            "k_pair": sum(r["pair"] for r in rs),
            "k_reachability": sum(r["reach"] for r in rs),
            "k_complete_decision": sum(r["full"] for r in rs),
            "k_built_window": sum(r["built_window"] for r in rs),
            "k_ran_BACKWARD": sum(r["ran_backward"] for r in rs),
            "k_ran_TEST_REACHABILITY": sum(r["ran_reachability"] for r in rs),
            "no_tool_call_turns": sum(r["malformed_turns"] for r in rs),
            "validation_rejections": sum(r["validation_rejections"] for r in rs),
        })

    OUT.mkdir(parents=True, exist_ok=True)
    f = OUT / "discover_boundary_c1_decision_components.csv"
    with f.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    (OUT / "discover_boundary_c1_decision_components_metadata.json").write_text(json.dumps({
        "schema": "discover-boundary-c1-decision-components-v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "cells": len(rows),
        "note": "k_* are run counts out of n. Chain-stage counts require the action to have succeeded and, for "
                "TEST_REACHABILITY, to have returned a classification.",
        "scientific_recomputation": False,
    }, indent=2), encoding="utf-8")

    print(f"{'tier':7s} {'arm':>3s} {'budget':>7s} {'n':>3s} {'win':>4s} {'pair':>5s} {'reach':>6s} {'full':>5s} "
          f"{'window':>7s} {'BACKW':>6s} {'REACH':>6s}")
    for r in rows:
        print(f"{r['tier']:7s} {r['arm']:>3s} {r['budget_CU']:7d} {r['n']:3d} {r['k_winner']:4d} {r['k_pair']:5d} "
              f"{r['k_reachability']:6d} {r['k_complete_decision']:5d} {r['k_built_window']:7d} "
              f"{r['k_ran_BACKWARD']:6d} {r['k_ran_TEST_REACHABILITY']:6d}")
    print("wrote", f.name)
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main())
