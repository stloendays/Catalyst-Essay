"""Methanol disagreements split by kind, with their denominators (author decision 2026-10-08: report separately).

A comparison group (one paper, pressure, H2/CO2 and space velocity) can hold several catalysts, one catalyst at several
temperatures, or both. A group whose space-time-yield leader is not the plant-cost leader is

  other catalyst   the two leaders are different catalysts (name before the location bracket, whitespace and dash
                   variants ignored); denominator: groups with at least two catalysts
  other temperature  the two leaders are the same catalyst at different temperatures; denominator: groups in which
                   at least one catalyst appears at two or more temperatures

Input: conversion_sensitivity_points.csv / conversion_sensitivity_groups.csv of meoh_conversion_sensitivity.py.
Output: reversal_kinds.csv (base treatment x data mode x conversion treatment) and reversal_kinds_groups.csv.
"""
import re
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
CONV = {"lab": "laboratory conversion", "cost_f0.95": "conversion raised with catalyst inventory (<= 0.95 X_eq)"}


def cat_name(s):
    return re.sub(r"\s+", "", str(s).split(" [")[0]).lower().replace("–", "-").replace("−", "-")


def main():
    pts = pd.read_csv(HERE / "conversion_sensitivity_points.csv")
    grp = pd.read_csv(HERE / "conversion_sensitivity_groups.csv")
    rows, per = [], []
    for (base, mode), p in pts.groupby(["base", "mode"]):
        p = p.assign(cat=p.catalyst.map(cat_name))
        n = p.groupby("group").size()
        p = p[p.group.isin(n[n >= 2].index)]
        shape = p.groupby("group").agg(n_catalysts=("cat", "nunique"))
        shape["temperature_series"] = p.groupby(["group", "cat"]).size().groupby("group").max() >= 2
        for col, label in CONV.items():
            g = grp[(grp.base == base) & (grp["mode"] == mode) & (grp.cost_col == col)].merge(
                shape, left_on="group", right_index=True, validate="one_to_one")
            g["kind"] = ["other catalyst" if cat_name(a) != cat_name(b) else "other temperature"
                         for a, b in zip(g.sty_leader, g.cost_leader)]
            g.loc[~g.mismatch, "kind"] = ""
            m = g[g.mismatch]
            oc, ot = m[m.kind == "other catalyst"], m[m.kind == "other temperature"]
            rows.append(dict(
                base=base, mode=mode, conversion=label, groups=len(g),
                multi_catalyst_groups=int((g.n_catalysts >= 2).sum()),
                temperature_series_groups=int(g.temperature_series.sum()),
                leader_differs=len(m), leader_differs_regret_gt5pct=int((m.regret > 0.05).sum()),
                other_catalyst=len(oc), other_catalyst_regret_gt5pct=int((oc.regret > 0.05).sum()),
                other_catalyst_regret_gt10pct=int((oc.regret > 0.10).sum()),
                other_catalyst_papers=int(oc.doi.nunique()),
                other_temperature=len(ot), other_temperature_regret_gt5pct=int((ot.regret > 0.05).sum()),
                other_temperature_regret_gt10pct=int((ot.regret > 0.10).sum()),
                other_temperature_papers=int(ot.doi.nunique()),
                max_regret_other_catalyst=float(oc.regret.max()) if len(oc) else 0.0,
                max_regret_other_temperature=float(ot.regret.max()) if len(ot) else 0.0))
            per.append(g.assign(base=base, mode=mode, conversion=label)[
                ["base", "mode", "conversion", "group", "doi", "n_catalysts", "temperature_series", "mismatch",
                 "kind", "regret", "sty_leader", "cost_leader"]])
    out = pd.DataFrame(rows)
    out.to_csv(HERE / "reversal_kinds.csv", index=False, float_format="%.4g")
    pd.concat(per).to_csv(HERE / "reversal_kinds_groups.csv", index=False, float_format="%.6g")
    pd.set_option("display.width", 250)
    print(out.drop(columns=["max_regret_other_catalyst", "max_regret_other_temperature"]).to_string(index=False))


if __name__ == "__main__":
    main()
