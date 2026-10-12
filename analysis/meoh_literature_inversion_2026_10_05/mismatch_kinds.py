"""What the methanol disagreements differ by, with their denominators (author decision 2026-10-08: report the kinds
separately).

A comparison group (one paper, pressure, H2/CO2 and space velocity) can hold several catalysts, one catalyst at several
temperatures, or both. Catalyst identity is meoh_candidates.catalyst_key (the name before the location bracket,
whitespace and dash variants ignored); two temperatures are distinct when they differ by more than T_TOL_C. A group
whose space-time-yield leader is not its plant-cost leader is one of

  other catalyst, same temperature     the leaders are different catalysts tested at the same temperature
  other catalyst and temperature       different catalysts at different temperatures (a joint change)
  other temperature                    the same catalyst at two different temperatures
  same catalyst, same temperature      two records of one catalyst at one temperature (e.g. a stability run)

Denominators: groups with at least two catalysts (the two other-catalyst kinds) and groups in which at least one
catalyst was tested at two or more distinct temperatures (other temperature). Each kind is also counted with a cost
gap (regret) above 5 % and 10 %. The same classification as analysis/verify_2026_10_08/reversal_kinds.py, which the
independent check analysis/review_2026_10_09/field_comparison_audit.py reproduces.

Also reported: how the plant-cost leader differs from the STY leader (methanol and CO selectivity, temperature,
conversion, chosen purge). Output of main(): mismatch_kinds.json (this folder), from literature_candidates.csv (the
frozen primary).
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from meoh_candidates import catalyst_key

HERE = Path(__file__).resolve().parent
T_TOL_C = 0.05
KINDS = ("other catalyst, same temperature", "other catalyst and temperature", "other temperature",
         "same catalyst, same temperature")
TAGS = ("cat_sameT", "cat_and_T", "T", "same_record")


def n_distinct(temps, tol=T_TOL_C):
    out = []
    for t in sorted(temps):
        if not out or t - out[-1] > tol:
            out.append(t)
    return len(out)


def _leader_T(g, label):
    t = g.loc[g.catalyst == label, "T_C"]
    if n_distinct(t.tolist()) != 1:
        raise ValueError(f"leader {label!r} has no unique temperature")
    return float(t.iloc[0])


def kind(g, sty_leader, cost_leader):
    same_cat = catalyst_key(sty_leader) == catalyst_key(cost_leader)
    same_T = abs(_leader_T(g, sty_leader) - _leader_T(g, cost_leader)) <= T_TOL_C
    if same_cat:
        return KINDS[3] if same_T else KINDS[2]
    return KINDS[0] if same_T else KINDS[1]


def classify(cand, gm, cost_col):
    """Per-group kind (empty where the leaders agree) and the summary with denominators.

    cand: the candidates the group metrics gm (meoh_candidates.aggregate) were computed from; only entries with a
    finite cost in cost_col are in a leaderboard."""
    f = cand[np.isfinite(cand[cost_col].astype(float))]
    by_group = dict(tuple(f.groupby("group")))
    gm = gm.copy()
    gm["n_catalysts"] = [by_group[g].catalyst.map(catalyst_key).nunique() for g in gm.group]
    gm["temperature_series"] = [
        bool(by_group[g].assign(k=by_group[g].catalyst.map(catalyst_key)).groupby("k").T_C
             .agg(lambda t: n_distinct(t.tolist()) >= 2).any()) for g in gm.group]
    gm["kind"] = [kind(by_group[g], a, b) if m else ""
                  for g, a, b, m in zip(gm.group, gm.upstream_winner, gm.economic_winner, gm.top1_mismatch)]
    m = gm[gm.top1_mismatch]
    out = dict(groups=len(gm), multi_catalyst_groups=int((gm.n_catalysts >= 2).sum()),
               temperature_series_groups=int(gm.temperature_series.sum()),
               leader_differs=len(m), leader_differs_gt5pct=int((m.regret > 0.05).sum()),
               leader_differs_gt10pct=int((m.regret > 0.10).sum()))
    for k, tag in zip(KINDS, TAGS):
        x = m[m.kind == k]
        out[tag] = dict(kind=k, groups=len(x), gt5pct=int((x.regret > 0.05).sum()),
                        gt10pct=int((x.regret > 0.10).sum()), papers=int(x.doi.nunique()),
                        regret_max=float(x.regret.max()) if len(x) else 0.0)
    oc = m[m.kind.isin(KINDS[:2])]
    out["other_catalyst"] = dict(groups=len(oc), of=out["multi_catalyst_groups"], gt5pct=int((oc.regret > 0.05).sum()),
                                 gt10pct=int((oc.regret > 0.10).sum()), papers=int(oc.doi.nunique()))
    ot = m[m.kind == KINDS[2]]
    out["other_temperature"] = dict(groups=len(ot), of=out["temperature_series_groups"],
                                    gt5pct=int((ot.regret > 0.05).sum()), gt10pct=int((ot.regret > 0.10).sum()),
                                    papers=int(ot.doi.nunique()))
    return gm, out


def leader_differences(cand, gm, cost_col, purge_col):
    """How the plant-cost leader differs from the STY leader in the groups where they differ."""
    f = cand.drop_duplicates(["group", "catalyst"]).set_index(["group", "catalyst"])
    rows = []
    for r in gm[gm.top1_mismatch].itertuples():
        up, ec = f.loc[(r.group, r.upstream_winner)], f.loc[(r.group, r.economic_winner)]
        rows.append(dict(dS=ec.SMeOH - up.SMeOH, dCO=ec.SCO - up.SCO, dT=ec.T_C - up.T_C, dX=ec.X - up.X,
                         S_up=up.SMeOH, S_ec=ec.SMeOH, purge_up=up[purge_col], purge_ec=ec[purge_col]))
    d = pd.DataFrame(rows)
    if d.empty:
        return {}
    return dict(disagreements=len(d), plant_leader_more_selective=int((d.dS > 0).sum()),
                plant_leader_less_CO=int((d.dCO < 0).sum()), plant_leader_cooler=int((d.dT < 0).sum()),
                plant_leader_higher_conversion=int((d.dX > 0).sum()),
                median={k: float(d[k].median()) for k in ("dT", "S_up", "S_ec", "purge_up", "purge_ec")})


def main():
    from meoh_candidates import aggregate
    c = pd.read_csv(HERE / "literature_candidates.csv")
    gm, _ = aggregate(c, "cost_recycled_opt")
    gm, out = classify(c, gm, "cost_recycled_opt")
    out["leader_differences"] = leader_differences(c, gm, "cost_recycled_opt", "purge_recycled_opt")
    (HERE / "mismatch_kinds.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
