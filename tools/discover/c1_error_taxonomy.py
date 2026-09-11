"""
DISCOVER-BOUNDARY-C1 error taxonomy and canonical narrow-window rule (2026-09-11 teacher request items 5 and 6).

Reads the existing frozen C1 traces only. No protocol file is touched, no model is called, no scientific value is recomputed.

Item 5 — every 0-CU action error is assigned to exactly one of three mechanisms:
  interface  : the model could not express a legal call (undeclared/wrong-typed argument, unknown action, no tool call at all)
  budget     : the call was legal but unaffordable at the remaining budget (BudgetExceeded)
  sequencing : the call was legal and affordable but violated an evidence precondition, split into
               premature_BACKWARD / premature_OPTIMIZE / premature_other
Item 6 — the narrow-window flag is fixed. The previous C1 flag counted any BUILD_PROCESS_WINDOW carrying a `bounds`
argument, which also counts bounds that select the whole admissible domain. The canonical rule requires the window to be
strictly smaller than the full state set AND to be used by a later successful scoped action.

Usage (from harness root):
  python discover/c1_error_taxonomy.py
"""
from __future__ import annotations
import csv, glob, json, sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "DISCOVER_BOUNDARY_C1"
DATA = OUT / "data"
TIER = {"gpt-5.5-2026-04-23": "strong", "gpt-5.4-mini-2026-03-17": "mini", "gpt-5.4-nano-2026-03-17": "nano"}
SCOPED_ACTIONS = ("OPTIMIZE_PROCESS", "RUN_MC", "TEST_LEVER", "BACKWARD", "CHECK_MODEL_VALIDITY")
FULL_STATES_EXPECTED = 14136


def classify_error(action: str, err: str) -> tuple[str, str]:
    """(mechanism, detail) for one 0-CU action error."""
    if "BudgetExceeded" in err:
        return "budget", f"unaffordable_{action}"
    if "InvalidArguments" in err or "unexpected keyword" in err or err.startswith("TypeError"):
        return "interface", f"undeclared_argument_{action}"
    if "unknown action" in err:
        return "interface", "unknown_action"
    if err.startswith("ValueError"):
        if action == "BACKWARD":
            return "sequencing", "premature_BACKWARD"
        if action == "OPTIMIZE_PROCESS":
            return "sequencing", "premature_OPTIMIZE"
        return "sequencing", f"premature_other_{action}"
    return "interface", f"other_{action}"


def window_analysis(steps: list[dict]) -> dict:
    """Canonical narrow-window determination for one run."""
    built: dict[str, int] = {}
    narrow_ids: set[str] = set()
    full_n = 0
    bounds_flag = False
    for s in steps:
        if s.get("chosen_action") != "BUILD_PROCESS_WINDOW":
            continue
        if (s.get("chosen_args") or {}).get("bounds"):
            bounds_flag = True
        r = s.get("result")
        if not isinstance(r, dict) or "error" in r or "window" not in r:
            continue
        wid, n = str(r["window"]), int(r["n_states"])
        built[wid] = n
        full_n = max(full_n, n)
    total = max(full_n, FULL_STATES_EXPECTED)
    narrow_ids = {w for w, n in built.items() if n < total}
    used = set()
    for s in steps:
        if s.get("chosen_action") not in SCOPED_ACTIONS:
            continue
        r = s.get("result")
        if not isinstance(r, dict) or "error" in r:
            continue
        w = (s.get("chosen_args") or {}).get("window") or (r.get("window") if isinstance(r, dict) else None)
        if w in narrow_ids:
            used.add(str(w))
    return {
        "windows_built": len(built),
        "narrow_windows_built": len(narrow_ids),
        "min_window_states": min(built.values()) if built else None,
        "full_window_states": total,
        "narrow_window_used": int(bool(used)),
        "narrow_window_canonical": int(bool(narrow_ids) and bool(used)),
        "narrow_window_bounds_flag_legacy": int(bounds_flag),
    }


def analyse_run(path: Path) -> dict:
    t = json.loads(path.read_text(encoding="utf-8"))
    steps = t["steps"]
    model = t["metadata"]["model_requested"]
    mech = Counter()
    detail = Counter()
    for s in steps:
        r = s.get("result")
        if isinstance(r, dict) and "error" in r:
            m, d = classify_error(str(s.get("chosen_action")), str(r["error"]))
            mech[m] += 1
            detail[d] += 1
    # A turn with no tool call is an interface failure but not a 0-CU action error; it is counted separately so that
    # the action-error totals stay byte-comparable with the frozen Phase A/B summaries.
    malformed = int(t.get("llm_meta", {}).get("malformed_turns", 0) or 0)
    if malformed:
        detail["no_tool_call"] += malformed
    row = {
        "run_dir": path.parent.name,
        "model": model,
        "tier": TIER.get(model, model),
        "budget_CU": int(float(t["budget_CU"])),
        "run_index": t.get("run_index"),
        "spent_CU": float(t["final"]["spent_CU"]),
        "why_stop": str(t["final"]["why_stop"])[:120],
        "action_errors": sum(mech.values()),
        "interface_failures_incl_no_tool_call": mech["interface"] + malformed,
        "err_interface": mech["interface"],
        "err_budget": mech["budget"],
        "err_sequencing": mech["sequencing"],
        "premature_BACKWARD": detail["premature_BACKWARD"],
        "premature_OPTIMIZE": detail["premature_OPTIMIZE"],
        "malformed_turns": malformed,
        "detail": json.dumps(dict(detail)),
    }
    row.update(window_analysis(steps))
    return row


def main() -> int:
    paths = sorted(Path(p) for p in glob.glob(str(OUT / "runs" / "*" / "traces" / "anonymous" / "*" / "trace.json")))
    if not paths:
        raise SystemExit("no C1 traces found")
    rows = [analyse_run(p) for p in paths]

    by_cell: dict[tuple, list[dict]] = defaultdict(list)
    for r in rows:
        by_cell[(r["tier"], r["budget_CU"])].append(r)

    summary = []
    for (tier, b), rs in sorted(by_cell.items(), key=lambda kv: ({"strong": 0, "mini": 1, "nano": 2}[kv[0][0]], kv[0][1])):
        det = Counter()
        for r in rs:
            det.update(json.loads(r["detail"]))
        summary.append({
            "tier": tier, "budget_CU": b, "n": len(rs),
            "action_errors": sum(r["action_errors"] for r in rs),
            "interface": sum(r["err_interface"] for r in rs),
            "no_tool_call_turns": sum(r["malformed_turns"] for r in rs),
            "budget": sum(r["err_budget"] for r in rs),
            "sequencing": sum(r["err_sequencing"] for r in rs),
            "premature_BACKWARD": sum(r["premature_BACKWARD"] for r in rs),
            "premature_OPTIMIZE": sum(r["premature_OPTIMIZE"] for r in rs),
            "runs_with_errors": sum(1 for r in rs if r["action_errors"]),
            "narrow_window_canonical": sum(r["narrow_window_canonical"] for r in rs),
            "narrow_window_legacy_bounds_flag": sum(r["narrow_window_bounds_flag_legacy"] for r in rs),
            "min_window_states_median": sorted(x["min_window_states"] for x in rs if x["min_window_states"] is not None)[len([x for x in rs if x["min_window_states"] is not None]) // 2] if any(x["min_window_states"] is not None for x in rs) else None,
            "detail": json.dumps(dict(det.most_common())),
        })

    DATA.mkdir(parents=True, exist_ok=True)
    run_csv = DATA / "discover_boundary_c1_error_taxonomy_runs.csv"
    sum_csv = DATA / "discover_boundary_c1_error_taxonomy_summary.csv"
    with run_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    with sum_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(summary[0].keys()))
        w.writeheader()
        w.writerows(summary)

    meta = {
        "schema": "discover-boundary-c1-error-taxonomy-v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "traces_analysed": len(rows),
        "mechanisms": {
            "interface": "model could not express a legal call: undeclared or wrong-typed argument, unknown action, turn with no tool call",
            "budget": "legal call refused because its quoted cost exceeded the remaining budget (BudgetExceeded)",
            "sequencing": "legal, affordable call that violated an evidence precondition (premature BACKWARD / OPTIMIZE / other)",
        },
        "narrow_window_canonical_rule": (
            "a run uses narrow-window allocation iff it builds at least one process window with n_states strictly less than "
            f"the full admissible state set ({FULL_STATES_EXPECTED}) AND at least one later scoped action "
            f"({', '.join(SCOPED_ACTIONS)}) succeeds against that window"
        ),
        "narrow_window_legacy_rule": "any BUILD_PROCESS_WINDOW call carrying a non-empty bounds argument (counts full-domain bounds as narrow)",
        "scientific_recomputation": False,
    }
    (DATA / "discover_boundary_c1_error_taxonomy_metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print(f"{'tier':7s} {'B':>4s} {'n':>3s} {'act_err':>7s} {'iface':>6s} {'noTool':>6s} {'budg':>5s} {'seq':>4s} {'preBW':>6s} {'preOPT':>7s} {'nw_can':>7s} {'nw_legacy':>10s}")
    for r in summary:
        print(f"{r['tier']:7s} {r['budget_CU']:4d} {r['n']:3d} {r['action_errors']:7d} {r['interface']:6d} {r['no_tool_call_turns']:6d} {r['budget']:5d} {r['sequencing']:4d} {r['premature_BACKWARD']:6d} {r['premature_OPTIMIZE']:7d} {r['narrow_window_canonical']:7d} {r['narrow_window_legacy_bounds_flag']:10d}")
    tot = Counter()
    for r in summary:
        tot[r["tier"]] += r["action_errors"]
    print("\ntier totals:", dict(tot), "| all tiers:", sum(tot.values()))
    print("wrote", run_csv.name, sum_csv.name)
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main())
