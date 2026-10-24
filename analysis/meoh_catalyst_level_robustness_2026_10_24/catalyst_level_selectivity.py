"""How the plant leader differs from the laboratory (STY) leader in the catalyst-level disagreements of the 63 methanol
groups, at laboratory conversion (26/63) and with more catalyst loaded (21/63).

Same comparison as meoh_literature_inversion_2026_10_05/mismatch_kinds.leader_differences (which gives 40 of 50 on the
81 point-level comparisons), on the catalyst-level unit of RULES.md: the laboratory leader is represented by its
highest-STY point, the plant leader by its lowest-cost point.

    python catalyst_level_selectivity.py      -> selectivity.json, selectivity_groups.csv
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
AN = HERE.parent
sys.path.insert(0, str(AN / "meoh_catalyst_level_2026_10_19"))
import run_catalyst_level as CL  # noqa: E402


def differences(f, cost, ident="cat_primary"):
    ct = CL.catalyst_table(f, ident, cost)
    gm = CL.compare(ct)
    rows = []
    for r in gm[gm.changed].itertuples():
        g = f[f.group == r.group]
        lab_cats = r.lab_leader.split(" | ")
        lab = g[g[ident].isin(lab_cats)]
        up = lab.loc[lab.STY.idxmax()]
        pl = g[g[ident] == r.plant_leader]
        ec = pl.loc[pl[cost].idxmin()]
        rows.append(dict(group=r.group, doi=r.doi, gap=r.gap, lab_leader=r.lab_leader, plant_leader=r.plant_leader,
                         S_lab=up.SMeOH, S_plant=ec.SMeOH, dS=ec.SMeOH - up.SMeOH, dCO=ec.SCO - up.SCO,
                         dX=ec.X - up.X, dT=ec.T_C - up.T_C))
    d = pd.DataFrame(rows)
    return gm, d, dict(groups=len(gm), disagreements=len(d), plant_leader_more_selective=int((d.dS > 0).sum()),
                       plant_leader_less_CO=int((d.dCO < 0).sum()),
                       plant_leader_higher_conversion=int((d.dX > 0).sum()), plant_leader_cooler=int((d.dT < 0).sum()),
                       more_selective_among_gap_gt5pct=f"{int(((d.dS > 0) & (d.gap > 0.05)).sum())}/{int((d.gap > 0.05).sum())}",
                       median_S_lab=float(d.S_lab.median()), median_S_plant=float(d.S_plant.median()))


def main():
    c = pd.read_csv(CL.POOLED / "pooled_candidates.csv")
    f = CL.identities(CL.scored(c, CL.COST))
    _, d_lab, s_lab = differences(f, CL.COST)
    p = pd.read_csv(CL.CONV)
    p = p[p["mode"] == "printed"].assign(sty_basis="")
    fp = CL.identities(CL.scored(p, "cost_f0.95"))
    _, d_raised, s_raised = differences(fp, "cost_f0.95")
    assert (s_lab["groups"], s_lab["disagreements"], s_raised["groups"], s_raised["disagreements"]) == (63, 26, 63, 21)
    out = {"laboratory conversion (26/63)": s_lab, "more catalyst loaded, f = 0.95 (21/63)": s_raised}
    (HERE / "selectivity.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    pd.concat([d_lab.assign(basis="laboratory"), d_raised.assign(basis="raised")]).to_csv(
        HERE / "selectivity_groups.csv", index=False, float_format="%.6g")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
