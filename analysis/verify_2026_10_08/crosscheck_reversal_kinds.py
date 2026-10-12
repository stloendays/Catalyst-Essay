"""Cross-check reversal_kinds.csv against the independent classifier analysis/review_2026_10_09/field_comparison_audit.py.

The two scripts were written separately; every denominator and every count by kind must agree for both base
treatments, both data modes and both conversion treatments. Exits 1 on any difference.
"""
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "review_2026_10_09"))
import field_comparison_audit as A  # noqa: E402

CONV = {"lab": "laboratory conversion", "cost_f0.95": "conversion raised with catalyst inventory (<= 0.95 X_eq)"}
CAT = {"different_catalyst_same_temperature": "cat_sameT", "different_catalyst_and_temperature": "cat_and_T",
       "same_catalyst_different_temperature": "T", "same_catalyst_same_temperature_different_record": "same_record"}


def main():
    mine = pd.read_csv(HERE / "reversal_kinds.csv")
    points = A.read_csv(HERE / "conversion_sensitivity_points.csv")
    groups = A.read_csv(HERE / "conversion_sensitivity_groups.csv")
    bad = []
    for base in ("orig", "thermo"):
        for mode in ("printed", "all"):
            result, _ = A.audit(points, groups, base=base, mode=mode)
            for col, label in CONV.items():
                ind = result["scenarios"][col]
                row = mine[(mine.base == base) & (mine["mode"] == mode) & (mine.conversion == label)].iloc[0]
                pairs = [("multi_catalyst_groups", ind["multi_catalyst_groups"], row.multi_catalyst_groups),
                         ("temperature_series_groups", ind["temperature_series_groups_strict"],
                          row.temperature_series_groups),
                         ("leader_differs", ind["total_winner_changes"], row.leader_differs),
                         ("other_catalyst_gt5pct", ind["catalyst_changes_gt5pct"], row.other_catalyst_gt5pct),
                         ("T_gt5pct", ind["temperature_changes_gt5pct"], row.T_gt5pct)]
                pairs += [(tag, ind["categories"].get(k, 0), row[tag]) for k, tag in CAT.items()]
                for name, a, b in pairs:
                    if int(a) != int(b):
                        bad.append(f"{base}/{mode}/{col}/{name}: independent {a}, reversal_kinds {b}")
                if ind["errors"]:
                    bad.append(f"{base}/{mode}/{col}: independent classifier errors {ind['errors'][:3]}")
            print(f"{base}/{mode}: checked")
    if bad:
        print("\n".join(bad))
        sys.exit(1)
    print("reversal_kinds.csv agrees with the independent classifier in all 8 settings.")


if __name__ == "__main__":
    main()
