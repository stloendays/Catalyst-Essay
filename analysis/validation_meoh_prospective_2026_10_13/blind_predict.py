"""Blind per-group predictions (PREREGISTRATION.md section 6), made before the plant model sees any new entry.

From the corrected records: meoh_candidates.build_candidates (printed-value cohort, frozen groups and STY basis) only;
no plant_costs call. For every comparison group with at least two entries:
  S6 rule (R2): the entry with the highest methanol selectivity, ties to the higher STY (run_rules.choice_set);
  S5 rule (R1): the STY leader.
The full ranking of each group's entries under each rule is written too: if a predicted entry turns out infeasible in
a scenario (no cost), the next entry of the committed ranking is the prediction (frozen convention: an infeasible
entry leaves the group).

    python blind_predict.py  -> blind_predictions.csv, blind_rankings.csv, blind_candidates.csv
"""
from __future__ import annotations

import pandas as pd

from meoh_candidates import build_candidates
from pv_common import HERE, RULES, choice_set, load_new_records

RULE_OF = {"S6": "S", "S5": "STY"}


def ranking(g: pd.DataFrame, rule: str) -> pd.DataFrame:
    """Entries ordered by the rule's score, ties (relative 1e-9) by the higher STY; rank 1 = the choice set."""
    s = RULES[rule](g).astype(float)
    best = s.max()
    key = s.where(~(s >= best - 1e-9 * abs(best)), best)       # the frozen tie tolerance at the top
    o = g.assign(_score=s, _key=key).sort_values(["_key", "STY"], ascending=[False, False])
    cs = choice_set(g, s)
    o["rank"] = range(1, len(o) + 1)
    o.loc[o.index.isin(cs.index), "rank"] = 1
    return o


def main():
    cand = build_candidates(load_new_records(corrected=True), printed_only=True)
    n = cand.groupby("group").size()
    cand = cand[cand.group.isin(n[n >= 2].index)].copy()
    cand["entry_id"] = cand.doi + " || " + cand.catalyst
    preds, ranks = [], []
    for grp, g in cand.groupby("group"):
        for scen, rule in RULE_OF.items():
            o = ranking(g, rule)
            top = o[o["rank"] == 1]
            preds.append(dict(group=grp, doi=g.doi.iloc[0], n_entries=len(g), scenario=scen, rule=rule,
                              predicted_plant_leader=" | ".join(top.catalyst), n_tied=len(top),
                              predicted_SMeOH=float(top.SMeOH.iloc[0]), predicted_STY=float(top.STY.iloc[0]),
                              sty_leader=" | ".join(choice_set(g, g.STY).catalyst)))
            for r in o.itertuples():
                ranks.append(dict(group=grp, scenario=scen, rule=rule, rank=r.rank, catalyst=r.catalyst,
                                  SMeOH=r.SMeOH, STY=r.STY, X=r.X, T_C=r.T_C))
    p = pd.DataFrame(preds)
    p["predicted_disagreement"] = p.predicted_plant_leader != p.sty_leader
    p.to_csv(HERE / "blind_predictions.csv", index=False, float_format="%.6g")
    pd.DataFrame(ranks).to_csv(HERE / "blind_rankings.csv", index=False, float_format="%.6g")
    cand.to_csv(HERE / "blind_candidates.csv", index=False, float_format="%.12g")
    s6 = p[p.scenario == "S6"]
    print(f"{s6.group.nunique()} groups in {s6.doi.nunique()} papers; S6 rule predicts a disagreement in "
          f"{int(s6.predicted_disagreement.sum())} of them")


if __name__ == "__main__":
    main()
