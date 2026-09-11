"""
DISCOVER-BOUNDARY-C1: decision-stable CU vs final-used CU (2026-09-11 teacher request item 2b).

Read-only replay of existing traces. No model is called, no frozen file is touched. For every run it reports

  decision_stable_CU  = ledger-true cumulative CU after the first step from which the full decision stays correct to
                        the end. The step-level `action_cost` field in a trace is the pre-execution `env.quote()` and
                        OVERSTATES the real charge for OPTIMIZE_PROCESS (quote counts every state in the window; the
                        environment charges only states not yet computed for that metal). The authoritative per-step
                        cumulative spend is therefore `budget_CU - step["remaining_budget"]`, which always reconciles
                        with the environment ledger and with spent_CU. The frozen metric
                        discover/boundary_c1_metrics.cu_to_full sums `action_cost` and is reported alongside as
                        decision_stable_CU_quoted so the difference stays visible.
  final_used_CU       = spent_CU at stop
  overrun_CU          = final_used_CU - decision_stable_CU  (compute spent after the decision was already complete)
  overrun_fraction    = overrun_CU / final_used_CU
  stop_mode           = self_stop (agent STOP) | turn_cap | budget_exhausted | malformed | infra

A run that never reaches the full decision has no decision_stable_CU and is reported separately; it is never counted as
zero overrun.

Usage (from harness root):
  python discover/c1_overrun_analysis.py                       # every C1 cell
  python discover/c1_overrun_analysis.py --glob "DISCOVER_BOUNDARY_C1/uncapped/traces/anonymous/*"
"""
from __future__ import annotations
import argparse, csv, glob, json, statistics as st, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "discover"))
import DISCOVER_SCORER_V1 as S
from boundary_c1_metrics import cu_to_full, _replay_answers, _full

OUT = ROOT / "DISCOVER_BOUNDARY_C1"
DATA = OUT / "data"
TIER = {"gpt-5.5-2026-04-23": "strong", "gpt-5.4-mini-2026-03-17": "mini", "gpt-5.4-nano-2026-03-17": "nano"}
DEFAULT_GLOBS = [
    "DISCOVER_BOUNDARY_C1/runs/*/traces/anonymous/*",
    "DISCOVER_BOUNDARY_C1/e2/traces/anonymous/*",
    "DISCOVER_BOUNDARY_C1/uncapped/traces/anonymous/*",
]


def _stable_from_ledger(path: Path) -> float | None:
    """Ledger-true decision-stable CU.

    Same replay as the frozen metric, but the cumulative spend at step j is taken from the environment state
    (`budget_CU - remaining_budget`) instead of from the quote-based `action_cost` field.
    """
    t = json.loads(path.read_text(encoding="utf-8"))
    mp = path.parent / "identity_mapping.json"
    m = json.loads(mp.read_text(encoding="utf-8"))["public_to_real"] if mp.exists() else {}
    if m:
        t = S._demap(t, m)
    steps = t["steps"]
    if not steps:
        return None
    answers = _replay_answers(t)
    flags = [_full(a) for a in answers]
    if not flags or not flags[-1]:
        return None
    k = len(flags) - 1
    while k > 0 and flags[k - 1]:
        k -= 1
    b0 = float(t["budget_CU"])
    return b0 - float(steps[k]["remaining_budget"])


def stop_mode(why: str) -> str:
    w = str(why)
    if w.startswith("agent STOP"):
        return "self_stop"
    if w.startswith("max_turns"):
        return "turn_cap"
    if w.startswith("budget_exhausted"):
        return "budget_exhausted"
    if w.startswith("malformed_action_limit"):
        return "malformed"
    if w.startswith("infrastructure_failure"):
        return "infra"
    return "other"


def analyse(path: Path) -> dict | None:
    t = json.loads(path.read_text(encoding="utf-8"))
    why = str(t["final"]["why_stop"])
    if why.startswith("infrastructure_failure"):
        return None
    sc = S.score_trace(path)
    stable_quoted = cu_to_full(path)["CU_to_full_decision"]
    stable = _stable_from_ledger(path)
    spent = float(sc["spent_CU"])
    model = t["metadata"]["model_requested"]
    row = {
        "run_dir": path.parent.name,
        "arm": "E2" if t["policy"].startswith("E2_") else "E",
        "model": model,
        "tier": TIER.get(model, model),
        "budget_CU": float(t["budget_CU"]),
        "run_index": t.get("run_index"),
        "steps": len(t["steps"]),
        "full_decision_correct": int(sc["full_decision_correct"]),
        "decision_stable_CU": stable,
        "decision_stable_CU_quoted": stable_quoted,
        "quote_inflation_CU": (stable_quoted - stable) if (stable is not None and stable_quoted is not None) else None,
        "final_used_CU": spent,
        "overrun_CU": (spent - stable) if stable is not None else None,
        "overrun_fraction": ((spent - stable) / spent) if (stable is not None and spent) else None,
        "stop_mode": stop_mode(why),
        "budget_remaining_at_stop": float(t["final"]["remaining_budget"]),
        "why_stop": why[:160],
    }
    return row


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--glob", action="append", default=None, help="trace directory glob (repeatable)")
    ap.add_argument("--out", default="discover_boundary_c1_overrun")
    a = ap.parse_args()
    pats = a.glob or DEFAULT_GLOBS
    paths = sorted({Path(p) for pat in pats for p in glob.glob(str(ROOT / pat / "trace.json"))})
    rows = [r for r in (analyse(p) for p in paths) if r]
    if not rows:
        raise SystemExit("no usable traces matched")

    DATA.mkdir(parents=True, exist_ok=True)
    run_csv = DATA / f"{a.out}_runs.csv"
    with run_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    cells: dict[tuple, list[dict]] = {}
    for r in rows:
        cells.setdefault((r["tier"], r["arm"], r["budget_CU"]), []).append(r)

    summary = []
    print(f"{'tier':7s} {'arm':>3s} {'budget':>7s} {'n':>3s} {'full':>5s} {'stable_med':>10s} {'used_med':>9s} {'overrun_med':>11s} {'overrun%':>9s}  stop modes")
    for (tier, arm, b), rs in sorted(cells.items(), key=lambda kv: ({"strong": 0, "mini": 1, "nano": 2}[kv[0][0]], kv[0][2], kv[0][1])):
        ov = [r["overrun_CU"] for r in rs if r["overrun_CU"] is not None]
        stab = [r["decision_stable_CU"] for r in rs if r["decision_stable_CU"] is not None]
        used = [r["final_used_CU"] for r in rs]
        frac = [r["overrun_fraction"] for r in rs if r["overrun_fraction"] is not None]
        modes: dict[str, int] = {}
        for r in rs:
            modes[r["stop_mode"]] = modes.get(r["stop_mode"], 0) + 1
        rec = {
            "tier": tier, "arm": arm, "budget_CU": b, "n": len(rs),
            "k_full": sum(r["full_decision_correct"] for r in rs),
            "decision_stable_CU_median": st.median(stab) if stab else None,
            "quote_inflation_CU_max": max((r["quote_inflation_CU"] for r in rs if r["quote_inflation_CU"] is not None), default=None),
            "decision_stable_CU_range": f"{min(stab):.0f}-{max(stab):.0f}" if stab else None,
            "final_used_CU_median": st.median(used),
            "final_used_CU_range": f"{min(used):.0f}-{max(used):.0f}",
            "overrun_CU_median": st.median(ov) if ov else None,
            "overrun_CU_range": f"{min(ov):.0f}-{max(ov):.0f}" if ov else None,
            "overrun_fraction_mean": (sum(frac) / len(frac)) if frac else None,
            "stop_modes": json.dumps(modes),
        }
        summary.append(rec)
        print(f"{tier:7s} {arm:>3s} {b:7.0f} {len(rs):3d} {rec['k_full']:5d} "
              f"{(rec['decision_stable_CU_median'] if rec['decision_stable_CU_median'] is not None else float('nan')):10.0f} "
              f"{rec['final_used_CU_median']:9.0f} "
              f"{(rec['overrun_CU_median'] if rec['overrun_CU_median'] is not None else float('nan')):11.0f} "
              f"{(100 * rec['overrun_fraction_mean'] if rec['overrun_fraction_mean'] is not None else float('nan')):8.1f}%  {json.dumps(modes)}")

    sum_csv = DATA / f"{a.out}_summary.csv"
    with sum_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(summary[0].keys()))
        w.writeheader()
        w.writerows(summary)
    (DATA / f"{a.out}_metadata.json").write_text(json.dumps({
        "schema": "discover-boundary-c1-overrun-v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "definitions": {
            "decision_stable_CU": "cumulative CU after the first step from which the replayed full decision stays correct to the end (frozen replay, discover/boundary_c1_metrics.cu_to_full)",
            "final_used_CU": "spent_CU at stop",
            "overrun_CU": "final_used_CU - decision_stable_CU; compute spent after the decision was already complete",
            "stop_mode": "self_stop (agent STOP) | turn_cap (MAX_TURNS) | budget_exhausted | malformed | infra",
        },
        "runs_analysed": len(rows),
        "infrastructure_failed_traces_excluded": True,
        "scientific_recomputation": False,
    }, indent=2), encoding="utf-8")
    print("\nwrote", run_csv.name, sum_csv.name)
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main())
