"""Pair methanol groups before/after catalyst-inventory optimization.

No new plant calculations. This is a within-group classification transition
audit over the already existing S5+printed verification outputs. Avoids a
misleading interpretation of two unpaired proportions as causal mechanism.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

from field_comparison_audit import audit, read_csv

BASE = Path(__file__).resolve().parents[1] / "verify_2026_10_08"
BEFORE = "lab"
AFTER = "cost_f0.95"


def pair_rows(details: list[dict]) -> tuple[dict, list[dict]]:
    by_case: dict[tuple[str, str, str], dict] = {}
    for row in details:
        k = (row["base"], row["mode"], row["group"])
        entry = by_case.setdefault(k, {})
        cost_col = row["cost_col"]
        if cost_col in entry:
            raise ValueError(f"Repeated outcome {k} {cost_col}")
        entry[cost_col] = row

    transitions = Counter()
    rows = []
    errors = []
    for key, cases in sorted(by_case.items()):
        if BEFORE not in cases or AFTER not in cases:
            errors.append(f"Missing paired condition in {key}")
            continue
        a, b = cases[BEFORE], cases[AFTER]
        if a["doi"] != b["doi"]:
            errors.append(f"Paper identity changed for {key}")
        if a["sty_leader"] != b["sty_leader"]:
            errors.append(f"Upstream STY leader changed across conversion sensitivity: {key}")
        if a["n_catalysts"] != b["n_catalysts"] or a["temp_series_strict"] != b["temp_series_strict"]:
            errors.append(f"Group comparison eligibility changed unexpectedly: {key}")
        first, second = a["classification"], b["classification"]
        transitions[(first, second)] += 1
        def is_mismatch(x):
            return x["classification"] != "no_winner_change"
        rows.append({
            "doi": a["doi"], "group": a["group"],
            "lab_classification": first, "adjusted_classification": second,
            "lab_regret": a["regret"], "adjusted_regret": b["regret"],
            "lab_gt5pct": is_mismatch(a) and a["regret"] > 0.05,
            "adjusted_gt5pct": is_mismatch(b) and b["regret"] > 0.05,
            "lab_cost_leader": a["cost_leader"],
            "adjusted_cost_leader": b["cost_leader"],
            "same_economic_winner": a["cost_leader"] == b["cost_leader"],
            "new_mismatch": not is_mismatch(a) and is_mismatch(b),
            "lost_mismatch": is_mismatch(a) and not is_mismatch(b),
            "changed_disagreement_type": is_mismatch(a) and is_mismatch(b) and first != second,
            "lab_joint_catalyst_temperature_change": first == "different_catalyst_and_temperature",
            "adjusted_joint_catalyst_temperature_change": second == "different_catalyst_and_temperature",
        })

    c = Counter()
    papers: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for r in rows:
        c["groups"] += 1
        c["lab_mismatches"] += int(r["lab_classification"] != "no_winner_change")
        c["adjusted_mismatches"] += int(r["adjusted_classification"] != "no_winner_change")
        for k in ("new_mismatch", "lost_mismatch", "changed_disagreement_type",
                  "same_economic_winner", "lab_gt5pct", "adjusted_gt5pct"):
            c[k] += int(r[k])
        papers[r["doi"]]["lab_gt5pct"] += int(r["lab_gt5pct"])
        papers[r["doi"]]["adjusted_gt5pct"] += int(r["adjusted_gt5pct"])
        papers[r["doi"]]["lab_mismatches"] += int(r["lab_classification"] != "no_winner_change")
        papers[r["doi"]]["adjusted_mismatches"] += int(r["adjusted_classification"] != "no_winner_change")

    diag = {
        "status": "INDEPENDENT_REVIEW_NOT_FROZEN",
        "counts": dict(c),
        "transitions": [
            {"lab_classification": a, "adjusted_classification": b, "groups": count}
            for (a, b), count in sorted(transitions.items())
        ],
        "papers": [{"doi": d, **v} for d, v in sorted(papers.items())],
        "errors": errors,
        "scope": "same papers/groups, same STY leaders, existing cost tables only",
    }
    if c["lab_mismatches"] + c["new_mismatch"] - c["lost_mismatch"] != c["adjusted_mismatches"]:
        diag["errors"].append("Inconsistent mismatch transition identity")
    return diag, rows


def main() -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--points", type=Path, default=BASE / "conversion_sensitivity_points.csv")
    cli.add_argument("--groups", type=Path, default=BASE / "conversion_sensitivity_groups.csv")
    cli.add_argument("--out-dir", type=Path, required=True)
    cli.add_argument("--base", choices=("orig", "thermo"), default="thermo")
    cli.add_argument("--mode", choices=("all", "printed"), default="printed")
    cli.add_argument("--strict", action="store_true")
    args = cli.parse_args()
    _, details = audit(read_csv(args.points), read_csv(args.groups),
                       base=args.base, mode=args.mode)
    result, records = pair_rows(details)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "paired_transition_summary.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with (args.out_dir / "paired_transition_groups.csv").open("w", newline="", encoding="utf-8") as fh:
        if records:
            writer = csv.DictWriter(fh, fieldnames=list(records[0]))
            writer.writeheader()
            writer.writerows(records)
    print(json.dumps({k: result[k] for k in ("counts", "transitions", "errors")}, indent=2))
    return int(bool(result["errors"]) and args.strict)


if __name__ == "__main__":
    raise SystemExit(main())
