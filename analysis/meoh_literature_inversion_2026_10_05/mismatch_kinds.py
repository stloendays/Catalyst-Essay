"""What the methanol disagreements differ by (primary treatment), from literature_candidates.csv.

A disagreement is a comparison group whose STY leader is not its plant-cost leader. It is 'same catalyst' when the two
entries carry the same catalyst name (the bracketed source locator removed), i.e. the paper's own catalyst at another
temperature, and 'different catalyst' otherwise. Also reported: how the plant-cost leader differs from the STY leader
(methanol selectivity, CO selectivity, temperature, conversion, chosen purge).

Output: mismatch_kinds.json (this folder).
"""
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent


def base(name):
    return re.sub(r"\s*\[.*$", "", str(name)).strip()


def main():
    c = pd.read_csv(HERE / "literature_candidates.csv")
    c = c[np.isfinite(c.cost_recycled_opt)]
    kinds = {"same catalyst": [], "different catalyst": []}
    diffs = []
    multi = 0
    for _, d in c.groupby("group"):
        if len(d) < 2:
            continue
        multi += d.catalyst.map(base).nunique() >= 2
        up, ec = d.loc[d.STY.idxmax()], d.loc[d.cost_recycled_opt.idxmin()]
        if d.STY.max() - ec.STY <= 1e-12:          # the plant-cost leader shares the top STY
            continue
        reg = (up.cost_recycled_opt - ec.cost_recycled_opt) / ec.cost_recycled_opt
        kinds["same catalyst" if base(up.catalyst) == base(ec.catalyst) else "different catalyst"].append(
            (up.doi, reg))
        diffs.append(dict(dS=ec.SMeOH - up.SMeOH, dCO=ec.SCO - up.SCO, dT=ec.T_C - up.T_C, dX=ec.X - up.X,
                          S_up=up.SMeOH, S_ec=ec.SMeOH, purge_up=up.purge_recycled_opt, purge_ec=ec.purge_recycled_opt))
    r = pd.DataFrame(diffs)
    out = {k: dict(groups=len(v), papers=len({d for d, _ in v}), regret_median=float(np.median([x for _, x in v])))
           for k, v in kinds.items()}
    out["groups_with_two_or_more_catalysts"] = int(multi)
    out["disagreements"] = len(r)
    out["plant_leader_more_selective"] = int((r.dS > 0).sum())
    out["plant_leader_less_CO"] = int((r.dCO < 0).sum())
    out["plant_leader_cooler"] = int((r.dT < 0).sum())
    out["plant_leader_higher_conversion"] = int((r.dX > 0).sum())
    out["median"] = {k: float(r[k].median()) for k in ("dT", "S_up", "S_ec", "purge_up", "purge_ec")}
    (HERE / "mismatch_kinds.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
