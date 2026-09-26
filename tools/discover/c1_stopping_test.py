"""
DISCOVER stopping test (read-only replay, 2026-09-26).

Question: the agent already chooses *what* to compute next; does it know *when it has computed enough*?

The frozen environment exposes a machine-checkable stopping rule on the public state only
(env.stopping_status: S1 winner identified, S2 no unresolved candidate, S3 reachability classified if needed).
Every trace step records `stopping_status_before`, i.e. the rule evaluated on the state the agent saw before
choosing that step's action. So for each run we can ask, without calling any model:

  S123_CU          ledger-true cumulative spend at the first moment the public rule S1 ^ S2 ^ S3 was satisfied
                   (the agent could have emitted STOP there instead of acting)
  correct_at_S123  whether the frozen scorer's full decision (winner ^ pair ^ reachability), replayed on the
                   state at that moment, was already correct
  decision_stable  ledger-true decision-stable CU (ground-truth based; the agent cannot see it)
  final_CU         spent_CU at the agent's own stop
  post_S123_CU     final_CU - S123_CU : compute spent after the public rule already allowed a stop
  post_S123_steps  actions taken after the rule was satisfied, by action type and CU

and evaluate the counterfactual policy "STOP at first S1^S2^S3" per cell: how many runs would still be scored
full-decision-correct, and at what spend.

Nothing frozen is modified. The scorer, the traces and the stopping rule are read only.

Usage (harness root):
  python discover/c1_stopping_test.py
  python discover/c1_stopping_test.py --glob "DISCOVER_BOUNDARY_C1/runs/gpt-5.5-2026-04-23/traces/anonymous/*"
"""
from __future__ import annotations
import argparse, csv, glob, json, statistics as st, sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "discover"))
import DISCOVER_SCORER_V1 as S                      # frozen; read-only
from boundary_c1_metrics import _replay_answers, _full  # frozen extension metric, read-only

OUT = ROOT / "DISCOVER_BOUNDARY_C1" / "data"
TIER = {"gpt-5.5-2026-04-23": "strong", "gpt-5.4-mini-2026-03-17": "mini", "gpt-5.4-nano-2026-03-17": "nano",
        "gpt-5.4-mini": "mini", "gpt-5.4-nano": "nano"}
DEFAULT_GLOBS = [
    ("C1", "DISCOVER_BOUNDARY_C1/runs/*/traces/anonymous/*"),
    ("C1-E2", "DISCOVER_BOUNDARY_C1/e2/traces/anonymous/*"),
    ("C1-D", "DISCOVER_BOUNDARY_C1/D_reference/traces/anonymous/*"),
    ("V1", "DISCOVER_FORMAL_RUNS_V1/traces/anonymous/*"),
    ("V1", "DISCOVER_FORMAL_RUNS_V1/traces/named/*"),
    ("V1-XM", "DISCOVER_CROSS_MODEL_V1/*/traces/anonymous/*"),
    ("V1-XM", "DISCOVER_CROSS_MODEL_V1/*/traces/named/*"),
]


def _load(path: Path):
    t = json.loads(path.read_text(encoding="utf-8"))
    mp = path.parent / "identity_mapping.json"
    m = json.loads(mp.read_text(encoding="utf-8"))["public_to_real"] if mp.exists() else {}
    return t, m


def stop_mode(why: str) -> str:
    w = str(why)
    for k, v in (("agent STOP", "self_stop"), ("max_turns", "turn_cap"), ("budget_exhausted", "budget_exhausted"),
                 ("malformed_action_limit", "malformed"), ("infrastructure_failure", "infra"),
                 ("no affordable admissible action", "policy_exhausted")):
        if w.startswith(k):
            return v
    return "other"


def analyse(path: Path, family: str) -> dict | None:
    t, m = _load(path)
    why = str(t["final"]["why_stop"])
    if why.startswith("infrastructure_failure"):
        return None
    td = S._demap(t, m) if m else t
    steps = td["steps"]
    if not steps:
        return None
    b0 = float(td["budget_CU"])
    spent_at = [b0 - float(s["remaining_budget"]) for s in steps]          # ledger-true spend after step j
    answers = _replay_answers(td)
    flags = [_full(a) for a in answers]                                    # full decision correct after step j

    # decision-stable (ground truth, ledger-true)
    stable = None
    if flags and flags[-1]:
        k = len(flags) - 1
        while k > 0 and flags[k - 1]:
            k -= 1
        stable = spent_at[k]

    # first moment the public rule S1^S2^S3 held (evaluated before step i, i.e. after step i-1)
    s123_idx = None; maystop_idx = None
    for i, s in enumerate(steps):
        ss = s.get("stopping_status_before") or {}
        if maystop_idx is None and ss.get("may_stop"):
            maystop_idx = i
        if ss.get("S1_winner_identified") and ss.get("S2_no_unresolved_candidate") and ss.get("S3_reachability_classified_if_needed"):
            s123_idx = i; break
    # the status recorded at the final STOP step also counts (the agent stopped exactly when the rule first held);
    # a run that ends without a STOP step (budget_exhausted / turn cap) can satisfy the rule only after its last action,
    # which is recorded in final.stopping_status -> treat as reached at the final spend with zero post-rule spend
    fs = (td.get("final") or {}).get("stopping_status") or {}
    if s123_idx is None and fs.get("S1_winner_identified") and fs.get("S2_no_unresolved_candidate") and fs.get("S3_reachability_classified_if_needed"):
        s123_idx = len(steps)
    s123_cu = None; correct_at = None; post_cu = None; post_steps = None; post_actions = Counter(); post_cu_by = Counter(); post_edv = []
    if s123_idx is not None:
        s123_cu = spent_at[s123_idx - 1] if s123_idx > 0 else 0.0
        correct_at = bool(flags[s123_idx - 1]) if s123_idx > 0 else False
        tail = [s for s in steps[s123_idx:] if s.get("chosen_action") != "STOP"]
        post_steps = len(tail)
        for s in tail:
            a = s.get("chosen_action") or "?"
            c = float(s.get("action_cost") or 0)
            post_actions[a] += 1; post_cu_by[a] += c
            e = s.get("expected_decision_value")
            if isinstance(e, (int, float)):
                post_edv.append(float(e))
        post_cu = spent_at[-1] - s123_cu
    pre_edv = [float(s["expected_decision_value"]) for s in steps[: (s123_idx if s123_idx is not None else len(steps))]
               if isinstance(s.get("expected_decision_value"), (int, float))]

    sc = S.score_trace(path)
    model = (td.get("metadata") or {}).get("model_requested") or td.get("model_requested") or td["policy"]
    return {
        "family": family, "run_dir": path.parent.name, "policy": td["policy"], "variant": td.get("task_variant"),
        "model": model, "tier": TIER.get(model, model if td["policy"].startswith("E") else td["policy"]),
        "budget_CU": b0, "run_index": td.get("run_index"), "steps": len(steps), "stop_mode": stop_mode(why),
        "full_decision_correct": int(sc["full_decision_correct"]),
        "decision_stable_CU": stable,
        "S123_reached": int(s123_idx is not None),
        "S123_CU": s123_cu,
        "correct_at_S123": (int(correct_at) if correct_at is not None else None),
        "stable_minus_S123": ((stable - s123_cu) if (stable is not None and s123_cu is not None) else None),
        "final_CU": spent_at[-1],
        "post_S123_CU": post_cu, "post_S123_steps": post_steps,
        "post_S123_actions": json.dumps(dict(post_actions), sort_keys=True) if post_steps is not None else None,
        "post_S123_CU_by_action": json.dumps(dict(post_cu_by), sort_keys=True) if post_steps is not None else None,
        "post_S123_paid_steps": (sum(1 for a, c in post_cu_by.items() if c > 0) if post_steps is not None else None),
        "edv_pre_S123_median": (st.median(pre_edv) if pre_edv else None),
        "edv_post_S123_median": (st.median(post_edv) if post_edv else None),
        "edv_post_S123_max": (max(post_edv) if post_edv else None),
        "overrun_CU_vs_stable": ((spent_at[-1] - stable) if stable is not None else None),
    }


def _med(xs):
    xs = [x for x in xs if x is not None]
    return st.median(xs) if xs else None


def summarise(rows: list[dict]) -> list[dict]:
    cells: dict[tuple, list[dict]] = {}
    for r in rows:
        cells.setdefault((r["family"], r["tier"], r["policy"], r["variant"], r["budget_CU"]), []).append(r)
    out = []
    for (fam, tier, pol, var, b), rs in sorted(cells.items(), key=lambda kv: (kv[0][0], kv[0][1], kv[0][2], kv[0][3] or "", kv[0][4])):
        n = len(rs)
        reached = [r for r in rs if r["S123_reached"]]
        post = [r["post_S123_CU"] for r in reached]
        out.append({
            "family": fam, "tier": tier, "policy": pol, "variant": var, "budget_CU": b, "n": n,
            "actual_full_correct": sum(r["full_decision_correct"] for r in rs),
            "S123_reached": len(reached),
            "stop_at_S123_full_correct": sum((r["correct_at_S123"] or 0) for r in reached),
            "S123_before_stable": sum(1 for r in reached if r["stable_minus_S123"] is not None and r["stable_minus_S123"] > 0),
            "S123_after_stable": sum(1 for r in reached if r["stable_minus_S123"] is not None and r["stable_minus_S123"] < 0),
            "S123_equal_stable": sum(1 for r in reached if r["stable_minus_S123"] == 0),
            "median_S123_CU": _med([r["S123_CU"] for r in reached]),
            "median_decision_stable_CU": _med([r["decision_stable_CU"] for r in rs]),
            "median_final_CU": _med([r["final_CU"] for r in rs]),
            "median_post_S123_CU": _med(post),
            "max_post_S123_CU": (max(post) if post else None),
            "runs_with_post_S123_paid_action": sum(1 for r in reached if (r["post_S123_paid_steps"] or 0) > 0),
            "runs_post_S123_zero_CU": sum(1 for r in reached if r["post_S123_CU"] == 0),
            "median_post_S123_steps": _med([r["post_S123_steps"] for r in reached]),
            "median_edv_pre_S123": _med([r["edv_pre_S123_median"] for r in reached]),
            "median_edv_post_S123": _med([r["edv_post_S123_median"] for r in reached]),
            "stop_modes": json.dumps(dict(Counter(r["stop_mode"] for r in rs)), sort_keys=True),
        })
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--glob", action="append", default=None)
    ap.add_argument("--out", default="discover_stopping_test")
    a = ap.parse_args()
    pats = [("custom", g) for g in a.glob] if a.glob else DEFAULT_GLOBS
    seen = set(); rows = []
    for fam, pat in pats:
        for p in sorted(glob.glob(str(ROOT / pat / "trace.json"))):
            p = Path(p)
            if p in seen:
                continue
            seen.add(p)
            r = analyse(p, fam)
            if r:
                rows.append(r)
    if not rows:
        raise SystemExit("no usable traces matched")
    OUT.mkdir(parents=True, exist_ok=True)
    run_csv = OUT / f"{a.out}_runs.csv"; cell_csv = OUT / f"{a.out}_cells.csv"
    with run_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    cells = summarise(rows)
    with cell_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(cells[0].keys())); w.writeheader(); w.writerows(cells)
    meta = {"generated_utc": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"), "n_runs": len(rows), "n_cells": len(cells),
            "globs": pats, "scorer": "DISCOVER_SCORER_V1 (frozen, read-only)", "note": "no model called; no frozen file modified"}
    (OUT / f"{a.out}_META.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    print(f"runs {len(rows)} -> {run_csv}\ncells {len(cells)} -> {cell_csv}")
    keys = ["family", "tier", "policy", "variant", "budget_CU", "n", "actual_full_correct", "S123_reached", "stop_at_S123_full_correct",
            "S123_before_stable", "median_S123_CU", "median_decision_stable_CU", "median_final_CU", "median_post_S123_CU", "max_post_S123_CU",
            "runs_with_post_S123_paid_action", "median_post_S123_steps", "median_edv_pre_S123", "median_edv_post_S123"]
    print("\t".join(keys))
    for c in cells:
        print("\t".join("" if c[k] is None else (f"{c[k]:g}" if isinstance(c[k], float) else str(c[k])) for k in keys))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
