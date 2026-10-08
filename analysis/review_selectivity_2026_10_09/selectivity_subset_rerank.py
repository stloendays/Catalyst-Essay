"""Printed-component-completeness sensitivity using existing methanol costs.

This is a read-only stratification of precomputed S5+printed candidate costs.
It never recalculates thermodynamics, selects a new plant model, or modifies the
canonical paper leaderboard. Output comparisons have *different denominators*
and are intended for reviewer/author QA only.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

from selectivity_source_audit import (
    VERIFY, audit, number, read_csv, read_pinned_records,
)

STY_TOL = 1e-12
COST_VARIANTS = ("lab", "cost_f0.95")


def source_key(row: dict) -> tuple[str, str, str, str, str]:
    return (
        row["doi"], row["entry"], row["group"], row["catalyst"], str(row["T_C"])
    )


def strict_components(source: dict) -> bool:
    if not (source["has_printed_CO"] and source["has_printed_CH4"]):
        return False
    if source["qualifier_CO"] != "=" or source["qualifier_CH4"] != "=":
        return False
    if source["CO_closed_vs_reported_delta_pp"] == "":
        return False
    if abs(float(source["CO_closed_vs_reported_delta_pp"])) > 1.0 + 1e-8:
        return False
    rch4 = source["reported_CH4_pct"]
    if rch4 == "":
        return False
    return abs(float(source["modeled_CH4_pct"]) - float(rch4)) <= 1.0 + 1e-8


def top1(points: list[dict], cost_col: str) -> dict | None:
    """Same tie semantics as S5's source top1: any tied-STY leader is valid."""
    f = [p for p in points if math.isfinite(float(p[cost_col])) and
         math.isfinite(float(p["STY"]))]
    if len(f) < 2:
        return None
    stymax = max(float(p["STY"]) for p in f)
    up = [p for p in f if float(p["STY"]) >= stymax - STY_TOL]
    econ = min(f, key=lambda p: float(p[cost_col]))
    c_best = float(econ[cost_col])
    if c_best <= 0:
        raise ValueError("Invalid nonpositive cost in group")
    upstream_best_cost = min(float(p[cost_col]) for p in up)
    regret = (upstream_best_cost - c_best) / c_best
    mismatch = econ not in up
    return {
        "group": f[0]["group"], "doi": f[0]["doi"],
        "n_points": len(f), "mismatch": mismatch, "regret": regret,
        "sty_leader": up[0]["catalyst"], "economic_leader": econ["catalyst"],
    }


def compare(points: list[dict], groups: list[dict], originals: list[dict],
            base: str = "thermo", mode: str = "printed") -> tuple[dict, list[dict]]:
    provenance, sources, _ = audit(points, groups, originals, base, mode)
    by_key: dict[tuple, dict] = {}
    for s in sources:
        key = source_key(s)
        if key in by_key:
            raise ValueError(f"Duplicate candidate source identity: {key!r}")
        by_key[key] = s
    selected = [p for p in points if p.get("base") == base and p.get("mode") == mode]
    enriched = []
    for point in selected:
        key = source_key(point)
        if key not in by_key:
            raise ValueError(f"Missing provenance for candidate {key}")
        source = by_key[key]
        enriched.append((point, source))
    cohorts = (
        "full_printed_X_MeOH",
        "CO_CH4_both_printed",
        "CO_CH4_exact_and_closed_within_1pp",
    )
    buckets: dict[str, dict[str, list[dict]]] = {
        name: defaultdict(list) for name in cohorts
    }
    for point, source in enriched:
        buckets[cohorts[0]][point["group"]].append(point)
        if source["has_printed_CO"] and source["has_printed_CH4"]:
            buckets[cohorts[1]][point["group"]].append(point)
        if strict_components(source):
            buckets[cohorts[2]][point["group"]].append(point)

    summary = {
        "status": "SENSITIVITY_ONLY_NOT_FROZEN",
        "base": base, "mode": mode,
        "provenance_candidate_count": provenance["candidates"]["candidates"],
        "cohorts": {},
        "errors": [],
    }
    per_group = []
    main_group_lookup = {
        (g["group"], g["cost_col"]): g for g in groups
        if g.get("base") == base and g.get("mode") == mode and
        g["cost_col"] in COST_VARIANTS
    }
    for cohort in cohorts:
        for cost_col in COST_VARIANTS:
            tallies = Counter()
            valid_dois = set()
            retained_mismatch_dois = set()
            for group, states in sorted(buckets[cohort].items()):
                r = top1(states, cost_col)
                if r is None:
                    continue
                tallies["groups"] += 1
                tallies["candidates_in_eligible_groups"] += r["n_points"]
                tallies["mismatches"] += int(r["mismatch"])
                tallies["mismatches_gt5pct"] += int(r["mismatch"] and r["regret"] > 0.05)
                valid_dois.add(r["doi"])
                if r["mismatch"]:
                    retained_mismatch_dois.add(r["doi"])
                if cohort == cohorts[0]:
                    prior = main_group_lookup.get((group, cost_col))
                    if prior is None:
                        summary["errors"].append(f"Missing full leaderboard {group} {cost_col}")
                    else:
                        baseline_mismatch = prior["mismatch"].lower() == "true"
                        if baseline_mismatch != r["mismatch"]:
                            summary["errors"].append(
                                f"Recomputed full mismatch disagrees {group} {cost_col}")
                        if abs(float(prior["regret"]) - r["regret"]) > 1e-5:
                            summary["errors"].append(
                                f"Recomputed full regret disagrees {group} {cost_col}")
                per_group.append(dict(
                    cohort=cohort, cost_col=cost_col, **r,
                ))
            summary["cohorts"][cohort + "|" + cost_col] = dict(
                tallies,
                papers=len(valid_dois),
                papers_with_mismatch=len(retained_mismatch_dois),
            )
    return summary, per_group


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--points", type=Path, default=VERIFY / "conversion_sensitivity_points.csv")
    parser.add_argument("--groups", type=Path, default=VERIFY / "conversion_sensitivity_groups.csv")
    parser.add_argument("--records", type=Path, default=None)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--base", choices=("orig", "thermo"), default="thermo")
    parser.add_argument("--mode", choices=("all", "printed"), default="printed")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    originals = read_csv(args.records) if args.records else read_pinned_records()
    summary, details = compare(
        read_csv(args.points), read_csv(args.groups), originals,
        base=args.base, mode=args.mode
    )
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "subset_rank_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if details:
        with (args.out_dir / "subset_rank_groups.csv").open(
            "w", newline="", encoding="utf-8"
        ) as handle:
            writer = csv.DictWriter(handle, fieldnames=list(details[0]))
            writer.writeheader()
            writer.writerows(details)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return int(bool(summary["errors"]) and args.strict)


if __name__ == "__main__":
    raise SystemExit(main())
