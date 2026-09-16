"""Extended Data Table 1 source: the five CU-to-X quantities on the non-binding-allowance cell (2026-09-16).

Read-only replay. Emits one row per quantity with its definition and its median/range, so the table carries no
hand-entered number. See docs/AGENT_METRIC_DEFINITIONS_SOURCE_OF_TRUTH_2026-09-13.md section 1.
"""
from __future__ import annotations
import csv, glob, json, statistics as st, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "discover"))
import DISCOVER_SCORER_V1 as S
from boundary_c1_metrics import cu_to_full
from c1_overrun_analysis import _stable_from_ledger

CELL = "DISCOVER_BOUNDARY_C1/runs/gpt-5.5-2026-04-23/traces/anonymous/*B5000*c1uncapped*"
OUT = ROOT / "DISCOVER_BOUNDARY_C1" / "data" / "discover_boundary_c1_cu_quantities.csv"

DEFS = [
    ("1", "CU_to_first_correct_winner", "frozen DISCOVER_SCORER_V1",
     "first step where current_winner equals ground truth; winner only; no stability requirement"),
    ("2", "CU_to_stable_correct_winner", "frozen DISCOVER_SCORER_V1",
     "cumulative CU from which the winner stays correct to the end; winner only"),
    ("3", "CU_to_full_decision", "discover/boundary_c1_metrics.cu_to_full",
     "full decision stability; sums the quote-based per-step action_cost field"),
    ("4", "decision_stable_CU", "tools/discover/c1_overrun_analysis.py",
     "full decision stability; ledger-true, from budget_CU minus remaining_budget"),
    ("5", "CU_after_stable_winner", "frozen DISCOVER_SCORER_V1",
     "spent_CU minus quantity 2; spend after the WINNER stabilised, not after the full decision"),
]


def main() -> int:
    paths = sorted(Path(p) for p in glob.glob(str(ROOT / CELL / "trace.json")))
    vals = {k: [] for k, *_ in DEFS}
    for p in paths:
        sc = S.score_trace(p)
        vals["1"].append(sc["CU_to_first_correct_winner"])
        vals["2"].append(sc["CU_to_stable_correct_winner"])
        vals["3"].append(cu_to_full(p)["CU_to_full_decision"])
        vals["4"].append(_stable_from_ledger(p))
        vals["5"].append(sc["CU_after_stable_winner"])
    rows = []
    for k, name, src, desc in DEFS:
        v = [x for x in vals[k] if x is not None]
        rows.append({"quantity_id": k, "name": name, "source": src, "definition": desc,
                     "n": len(v), "median_CU": st.median(v), "min_CU": min(v), "max_CU": max(v)})
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    for r in rows:
        print(f"  #{r['quantity_id']} {r['name']:32s} median {r['median_CU']:7.0f}  range {r['min_CU']:.0f}-{r['max_CU']:.0f}")
    print("wrote", OUT.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
