"""Independent read-only audit of methanol winner classifications.

Uses committed verification candidate and group tables. Does not mutate source
data, run the reactor model, or declare frozen results. Repeated observations at
a single temperature are not a temperature series. A catalyst switch occurring
at a different temperature is a *joint* change, not proof of a catalyst-only
mechanism.

Usage:
  python field_comparison_audit.py --out-dir /tmp/meoh-audit
  python field_comparison_audit.py --out-dir /tmp/meoh-audit --strict
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

DEFAULT_DIR = Path(__file__).resolve().parents[1] / "verify_2026_10_08"
MAIN_COST_COLS = ("lab", "cost_f0.95")
T_TOL_C = 0.05


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def canonical_catalyst(label: str) -> str:
    """Mirror the existing name-normalisation convention for parity."""
    base = str(label).split(" [", 1)[0].lower()
    return re.sub(r"\s+", "", base).replace("\u2013", "-").replace("\u2212", "-")


def distinct_t(values: list[float], tol: float = T_TOL_C) -> list[float]:
    result: list[float] = []
    for val in sorted(values):
        if not result or abs(val - result[-1]) > tol:
            result.append(val)
    return result


def bool_field(v: str) -> bool:
    if v.lower() in ("true", "1"):
        return True
    if v.lower() in ("false", "0"):
        return False
    raise ValueError(f"Unknown boolean CSV value: {v!r}")


def leader_temperature(points: list[dict[str, str]], label: str) -> tuple[float | None, str]:
    temperatures = distinct_t([float(p["T_C"]) for p in points if p["catalyst"] == label])
    if len(temperatures) == 1:
        return temperatures[0], "unique"
    if not temperatures:
        return None, "missing"
    return None, "ambiguous"


def audit(points: list[dict[str, str]], groups: list[dict[str, str]],
          *, base: str = "thermo", mode: str = "printed",
          cost_cols: tuple[str, ...] = MAIN_COST_COLS, t_tol: float = T_TOL_C
          ) -> tuple[dict, list[dict]]:
    # Keep original identities and rows. Never deduplicate verification inputs.
    by_group: dict[str, list[dict[str, str]]] = defaultdict(list)
    for p in points:
        if p["base"] == base and p["mode"] == mode:
            by_group[p["group"]].append(p)

    eligible = {name: p for name, p in by_group.items() if len(p) >= 2}
    summaries: dict[str, dict] = {}
    details: list[dict] = []
    for cost_col in cost_cols:
        outcomes = [r for r in groups if r["base"] == base and r["mode"] == mode
                    and r["cost_col"] == cost_col]
        outcome_groups = {r["group"] for r in outcomes}
        errors: list[str] = []
        missing_groups = set(eligible) - outcome_groups
        extra_groups = outcome_groups - set(eligible)
        if missing_groups or extra_groups:
            errors.append(f"Group mismatch: missing={len(missing_groups)}, extra={len(extra_groups)}")

        types = Counter()
        shape_counts = Counter()
        material_mismatch = temp_mismatch = material_gt5 = temp_gt5 = 0
        for r in outcomes:
            p = eligible.get(r["group"], [])
            by_catalyst: dict[str, list[float]] = defaultdict(list)
            for x in p:
                by_catalyst[canonical_catalyst(x["catalyst"])].append(float(x["T_C"]))
            multi_cat = len(by_catalyst) >= 2
            temp_series = any(len(distinct_t(v, t_tol)) >= 2 for v in by_catalyst.values())
            old_rule_series = any(len(v) >= 2 for v in by_catalyst.values())
            shape_counts["multi_catalyst"] += int(multi_cat)
            shape_counts["temperature_series_strict"] += int(temp_series)
            shape_counts["temperature_series_row_count"] += int(old_rule_series)

            mismatch = bool_field(r["mismatch"])
            sty_t, sty_status = leader_temperature(p, r["sty_leader"])
            cost_t, cost_status = leader_temperature(p, r["cost_leader"])
            same_material = canonical_catalyst(r["sty_leader"]) == canonical_catalyst(r["cost_leader"])
            if not mismatch:
                kind = "no_winner_change"
            elif sty_status != "unique" or cost_status != "unique":
                kind = "unresolved_leader_temperature"
                errors.append(f"Cannot resolve winner temperature in {r['group']}")
            elif same_material and abs(sty_t - cost_t) > t_tol:
                kind = "same_catalyst_different_temperature"
            elif same_material:
                kind = "same_catalyst_same_temperature_different_record"
            elif abs(sty_t - cost_t) > t_tol:
                kind = "different_catalyst_and_temperature"
            else:
                kind = "different_catalyst_same_temperature"
            types[kind] += 1
            regret = float(r["regret"])
            if not math.isfinite(regret) or regret < -1e-10:
                errors.append(f"Invalid regret in group {r['group']}: {r['regret']}")
            if mismatch and kind.startswith("different_catalyst_"):
                material_mismatch += 1
                material_gt5 += int(regret > 0.05)
                if not multi_cat:
                    errors.append(f"Different-catalyst winner without multi-catalyst group: {r['group']}")
            if mismatch and kind == "same_catalyst_different_temperature":
                temp_mismatch += 1
                temp_gt5 += int(regret > 0.05)
                if not temp_series:
                    errors.append(f"Temperature winner without temperature series: {r['group']}")
            details.append({
                "base": base, "mode": mode, "cost_col": cost_col, "group": r["group"],
                "doi": r.get("doi", ""), "n_points": len(p), "n_catalysts": len(by_catalyst),
                "multi_catalyst": multi_cat, "temp_series_strict": temp_series,
                "temp_series_row_count": old_rule_series,
                "temperature_false_positive": old_rule_series and not temp_series,
                "mismatch": mismatch, "regret": regret,
                "sty_leader": r["sty_leader"], "cost_leader": r["cost_leader"],
                "sty_T_C": sty_t, "cost_T_C": cost_t, "classification": kind,
            })
        summaries[cost_col] = {
            "groups": len(outcomes), "multi_catalyst_groups": shape_counts["multi_catalyst"],
            "temperature_series_groups_strict": shape_counts["temperature_series_strict"],
            "temperature_series_groups_row_count": shape_counts["temperature_series_row_count"],
            "total_winner_changes": sum(v for k, v in types.items() if k != "no_winner_change"),
            "catalyst_changes": material_mismatch, "catalyst_changes_gt5pct": material_gt5,
            "same_catalyst_temperature_changes": temp_mismatch, "temperature_changes_gt5pct": temp_gt5,
            "categories": dict(sorted(types.items())), "errors": errors,
        }
    return {"base": base, "mode": mode, "temperature_tolerance_C": t_tol,
            "scenarios": summaries, "status": "INDEPENDENT_QA_NOT_FROZEN"}, details


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--points", type=Path,
                    default=DEFAULT_DIR / "conversion_sensitivity_points.csv")
    ap.add_argument("--groups", type=Path,
                    default=DEFAULT_DIR / "conversion_sensitivity_groups.csv")
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--base", default="thermo", choices=("orig", "thermo"))
    ap.add_argument("--mode", default="printed", choices=("printed", "all"))
    ap.add_argument("--strict", action="store_true",
                    help="Exit nonzero for any unresolved winner or invalid group")
    args = ap.parse_args()
    result, details = audit(read_csv(args.points), read_csv(args.groups),
                            base=args.base, mode=args.mode)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "audit_summary.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n",
                                                     encoding="utf-8")
    with (args.out_dir / "audit_groups.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(details[0]) if details else ["group"])
        writer.writeheader()
        writer.writerows(details)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if args.strict and any(d["errors"] for d in result["scenarios"].values()):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
