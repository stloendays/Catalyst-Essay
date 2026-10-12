"""Methanol disagreements split by kind, with their denominators (author decision 2026-10-08: report separately).

A comparison group (one paper, pressure, H2/CO2 and space velocity) can hold several catalysts, one catalyst at several
temperatures, or both. Catalyst identity is the name before the location bracket (whitespace and dash variants
ignored); two temperatures are distinct when they differ by more than T_TOL_C. A group whose space-time-yield leader
is not the plant-cost leader is one of

  other catalyst, same temperature     the leaders are different catalysts tested at the same temperature
  other catalyst and temperature       different catalysts at different temperatures (a joint change)
  other temperature                    the same catalyst at two different temperatures
  same catalyst, same temperature      two records of one catalyst at one temperature (e.g. a stability run)

Denominators: groups with at least two catalysts (for the two other-catalyst kinds) and groups in which at least one
catalyst was tested at two or more distinct temperatures (for other temperature). Repeated rows at one temperature
are not a temperature series (corrects the 2026-10-08 version, which counted rows; found by the independent check
analysis/review_2026_10_09/field_comparison_audit.py, whose counts this script must reproduce).

Input: conversion_sensitivity_points.csv / conversion_sensitivity_groups.csv of meoh_conversion_sensitivity.py.
Output: reversal_kinds.csv (base treatment x data mode x conversion treatment) and reversal_kinds_groups.csv.
"""
import re
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
CONV = {"lab": "laboratory conversion", "cost_f0.95": "conversion raised with catalyst inventory (<= 0.95 X_eq)"}
T_TOL_C = 0.05
KINDS = ("other catalyst, same temperature", "other catalyst and temperature", "other temperature",
         "same catalyst, same temperature")


def cat_name(s):
    return re.sub(r"\s+", "", str(s).split(" [")[0]).lower().replace("–", "-").replace("−", "-")


def n_distinct(temps, tol=T_TOL_C):
    out = []
    for t in sorted(temps):
        if not out or t - out[-1] > tol:
            out.append(t)
    return len(out)


def leader_T(points, label):
    """Temperature of the leader entry (the full catalyst label identifies one entry of the group)."""
    t = points.loc[points.catalyst == label, "T_C"]
    if n_distinct(t.tolist()) != 1:
        raise ValueError(f"leader {label!r} has no unique temperature")
    return float(t.iloc[0])


def kind(points, sty_leader, cost_leader):
    same_cat = cat_name(sty_leader) == cat_name(cost_leader)
    same_T = abs(leader_T(points, sty_leader) - leader_T(points, cost_leader)) <= T_TOL_C
    if same_cat:
        return KINDS[3] if same_T else KINDS[2]
    return KINDS[0] if same_T else KINDS[1]


def main():
    pts = pd.read_csv(HERE / "conversion_sensitivity_points.csv")
    grp = pd.read_csv(HERE / "conversion_sensitivity_groups.csv")
    rows, per = [], []
    for (base, mode), p in pts.groupby(["base", "mode"]):
        p = p.assign(cat=p.catalyst.map(cat_name))
        n = p.groupby("group").size()
        p = p[p.group.isin(n[n >= 2].index)]
        by_group = dict(tuple(p.groupby("group")))
        shape = p.groupby("group").agg(n_catalysts=("cat", "nunique"))
        shape["temperature_series"] = p.groupby(["group", "cat"]).T_C.agg(lambda t: n_distinct(t.tolist()) >= 2) \
            .groupby("group").any()
        for col, label in CONV.items():
            g = grp[(grp.base == base) & (grp["mode"] == mode) & (grp.cost_col == col)].merge(
                shape, left_on="group", right_index=True, validate="one_to_one")
            g["kind"] = [kind(by_group[gr], a, b) if m else ""
                         for gr, a, b, m in zip(g.group, g.sty_leader, g.cost_leader, g.mismatch)]
            m = g[g.mismatch]
            row = dict(base=base, mode=mode, conversion=label, groups=len(g),
                       multi_catalyst_groups=int((g.n_catalysts >= 2).sum()),
                       temperature_series_groups=int(g.temperature_series.sum()),
                       leader_differs=len(m), leader_differs_regret_gt5pct=int((m.regret > 0.05).sum()))
            for k, tag in zip(KINDS, ("cat_sameT", "cat_and_T", "T", "same_record")):
                x = m[m.kind == k]
                row[tag] = len(x)
                row[tag + "_gt5pct"] = int((x.regret > 0.05).sum())
                row[tag + "_gt10pct"] = int((x.regret > 0.10).sum())
                row[tag + "_papers"] = int(x.doi.nunique())
            oc = m[m.kind.isin(KINDS[:2])]
            row.update(other_catalyst=len(oc), other_catalyst_gt5pct=int((oc.regret > 0.05).sum()))
            rows.append(row)
            per.append(g.assign(base=base, mode=mode, conversion=label)[
                ["base", "mode", "conversion", "group", "doi", "n_catalysts", "temperature_series", "mismatch",
                 "kind", "regret", "sty_leader", "cost_leader"]])
    out = pd.DataFrame(rows)
    out.to_csv(HERE / "reversal_kinds.csv", index=False, float_format="%.4g")
    pd.concat(per).to_csv(HERE / "reversal_kinds_groups.csv", index=False, float_format="%.6g")
    pd.set_option("display.width", 250)
    show = ["base", "mode", "conversion", "groups", "multi_catalyst_groups", "temperature_series_groups",
            "leader_differs", "cat_sameT", "cat_and_T", "other_catalyst", "other_catalyst_gt5pct", "T", "T_gt5pct",
            "same_record"]
    print(out[show].to_string(index=False))


if __name__ == "__main__":
    main()
