#!/usr/bin/env python3
"""Assemble the tidy panel data for the main-text Agent figure (F10) from the frozen analysis CSVs.

Single source of truth for every plotted number: this script reads only
  data/discover_boundary_c1_overrun_summary.csv        (k_full, decision-stable CU, final-used CU, overrun)
  data/discover_boundary_c1_error_taxonomy_summary.csv (canonical narrow-window counts)
and writes data/agent_figure_panel_data_2026-09-13.csv. Nothing is recomputed from traces and nothing is hand-entered.

Metric definitions follow docs/AGENT_METRIC_DEFINITIONS_SOURCE_OF_TRUTH_2026-09-13.md:
  decision_stable_CU is the ledger-true full-decision stability quantity (#4), not any winner-only quantity.

Usage (from the repository root):
  python tools/discover/build_agent_figure_data.py
"""
from __future__ import annotations
import csv
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
OVERRUN = DATA / "discover_boundary_c1_overrun_summary.csv"
TAXONOMY = DATA / "discover_boundary_c1_error_taxonomy_summary.csv"
OUT = DATA / "agent_figure_panel_data_2026-09-13.csv"
D_THRESHOLD_CU = 206.0
UNCAPPED_ALLOWANCE_CU = 5000.0


def wilson(k: int, n: int, z: float = 1.959963984540054) -> tuple[float, float]:
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def load(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def num(v):
    if v in ("", None):
        return None
    return float(v)


def main() -> int:
    overrun = load(OVERRUN)
    taxonomy = load(TAXONOMY)
    nw = {(r["tier"], r["arm"], int(float(r["budget_CU"]))): int(r["narrow_window_canonical"]) for r in taxonomy}

    rows = []
    for r in overrun:
        tier, arm, b = r["tier"], r["arm"], int(float(r["budget_CU"]))
        n, k = int(r["n"]), int(r["k_full"])
        lo, hi = wilson(k, n)
        key = (tier, arm, b)
        rows.append({
            "tier": tier,
            "arm": arm,
            "budget_CU": b,
            "is_non_binding_allowance": int(b == UNCAPPED_ALLOWANCE_CU),
            "n": n,
            "k_complete_decision": k,
            "p_complete_decision": k / n,
            "ci_lo": lo,
            "ci_hi": hi,
            "narrow_window_canonical": nw.get(key),
            "narrow_window_fraction": (nw[key] / n) if key in nw else None,
            "decision_stable_CU_median": num(r["decision_stable_CU_median"]),
            "final_used_CU_median": num(r["final_used_CU_median"]),
            "overrun_CU_median": num(r["overrun_CU_median"]),
            "overrun_fraction_mean_per_run": num(r["overrun_fraction_mean"]),
            "final_used_CU_range": r["final_used_CU_range"],
            "decision_stable_CU_range": r["decision_stable_CU_range"],
            "final_over_D_threshold": (num(r["final_used_CU_median"]) / D_THRESHOLD_CU) if num(r["final_used_CU_median"]) else None,
            "stop_modes": r["stop_modes"],
        })

    order = {"strong": 0, "mini": 1, "nano": 2}
    rows.sort(key=lambda x: (order[x["tier"]], x["arm"], x["budget_CU"]))
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    print(f"wrote {OUT.relative_to(ROOT).as_posix()}  ({len(rows)} cells)")
    print(f"{'tier':7s} {'arm':>3s} {'budget':>7s} {'n':>3s} {'k':>3s} {'P':>5s} {'nw':>6s} {'stable':>7s} {'final':>7s} {'xD':>5s}")
    for r in rows:
        nwf = f"{r['narrow_window_canonical']}/{r['n']}" if r["narrow_window_canonical"] is not None else "-"
        st = f"{r['decision_stable_CU_median']:.0f}" if r["decision_stable_CU_median"] else "-"
        xd = f"{r['final_over_D_threshold']:.2f}" if r["final_over_D_threshold"] else "-"
        print(f"{r['tier']:7s} {r['arm']:>3s} {r['budget_CU']:7d} {r['n']:3d} {r['k_complete_decision']:3d} "
              f"{r['p_complete_decision']:5.2f} {nwf:>6s} {st:>7s} {r['final_used_CU_median']:7.0f} {xd:>5s}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
