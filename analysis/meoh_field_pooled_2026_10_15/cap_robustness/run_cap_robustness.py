"""How much does the choice of the reactor-inlet limit matter for the catalyst a plant would pick?

For each of the 81 combined comparison groups and each operating point, the regret at an inlet limit c is
cost_c / min_group cost_c - 1 (frozen definition: CO + CH4 + N2 counted; costs from
robustness/inlet_definition/entry_costs.csv, the combined rerun of analysis/meoh_inlet_definition_2026_10_12).
The worst-case regret of a choice is its largest regret over the limits 5, 6, 6.86, 8 and 10 % (the band of the
published loop designs). Choices compared:
  S6 leader      the plant-cost leader at 6.86 % (the primary analysis)
  minimax        the operating point with the smallest worst-case regret (an oracle that knows every limit's cost)
  STY leader     the paper's space-time-yield leader (ties to the cheaper at 6.86 %)
  selectivity    the entry with the highest methanol selectivity (ties to the higher STY)
A limit at which no entry of a group is feasible is skipped for that group; an entry infeasible at a limit where
others are feasible has infinite regret there.

    python run_cap_robustness.py  -> summary.json, groups.csv
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
POOL = HERE.parent
CAPS = ["5", "6", "6.86", "8", "10"]
TOL = 0.05


def main():
    e = pd.read_csv(POOL / "robustness" / "inlet_definition" / "entry_costs.csv")
    scored = set(pd.read_csv(POOL / "groups_S6.csv").group)
    e = e[e.group.isin(scored)].copy()
    assert e.group.nunique() == 81, e.group.nunique()
    rows = []
    for g, d in e.groupby("group", sort=False):
        d = d.reset_index(drop=True)
        reg = {}
        for c in CAPS:
            col = d[f"cost_frozen_{c}"].astype(float)
            if not np.isfinite(col).any():
                continue
            reg[c] = (col / col[np.isfinite(col)].min() - 1).where(np.isfinite(col), np.inf)
        worst = pd.concat(reg, axis=1).max(axis=1)
        c686 = d["cost_frozen_6.86"].astype(float)
        s6 = int(c686.idxmin())
        sty_top = d[d.STY >= d.STY.max() - 1e-12]
        sty = int(c686.loc[sty_top.index].idxmin()) if np.isfinite(c686.loc[sty_top.index]).any() else int(sty_top.index[0])
        sel_top = d[d.SMeOH >= d.SMeOH.max() - 1e-12]
        sel = int(sel_top.STY.idxmax())
        mm = int(worst.idxmin())
        rows.append(dict(group=g, doi=d.doi[0], batch=d.batch[0], n=len(d), caps_scored=len(reg),
                         worst_minimax=worst[mm], worst_s6_leader=worst[s6], worst_sty_leader=worst[sty],
                         worst_selectivity=worst[sel], s6_is_minimax=bool(s6 == mm)))
    t = pd.DataFrame(rows)
    out = {"groups": len(t), "caps_pct": CAPS, "tolerance": TOL}
    for k in ("minimax", "s6_leader", "sty_leader", "selectivity"):
        w = t["worst_" + k]
        out[k] = dict(within_tolerance=int((w <= TOL).sum()), median_worst_regret=float(w.median()),
                      by_batch={b: int((g["worst_" + k] <= TOL).sum()) for b, g in t.groupby("batch")})
    out["s6_leader_is_minimax_choice"] = int(t.s6_is_minimax.sum())
    t.to_csv(HERE / "groups.csv", index=False, float_format="%.6g")
    (HERE / "summary.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
