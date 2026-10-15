"""The predictions of PREREGISTRATION.md, computed from the frozen field result only (no new paper is read).

Input: the frozen printed cohort analysis/meoh_literature_inversion_2026_10_05/literature_candidates.csv (40 groups,
28 papers), whose cost columns are the latest model's S5 and S6 costs. Output: prediction_frozen.json and
prediction_frozen_groups.csv. Anchors (frozen): S5 15/40 with CI 15.2-57.1 %, S6 28/40 with CI 54.1-82.8 %
(analysis/meoh_s6_robustness_2026_10_13, PR #79), rule accuracies S5/STY 25/40 and S6/S 23/40
(analysis/meoh_constraint_boundary_2026_10_12 rules_fixed.csv).
"""
import json

import pandas as pd

from pv_common import BOOT_N, BOOT_SEED, FROZEN_CANDIDATES, HERE, RULE_FOR, SCEN, bootstrap, group_table, paper_boot

ANCHORS = {"S5": dict(mismatch=15, ci=(0.152, 0.571), rule_correct=25),
           "S6": dict(mismatch=28, ci=(0.541, 0.828), rule_correct=23)}


def stats_for(t):
    return {
        "disagreement_rate": ("mismatch", None),
        "rule_accuracy": ("rule_correct", None),
        "sty_accuracy": ("STY_correct", None),
        "chance_accuracy": ("chance", None),
        "rule_minus_chance": (lambda d: d.rule_correct.astype(float) - d.chance, None),
        "rule_minus_sty": (lambda d: d.rule_correct.astype(float) - d.STY_correct.astype(float), None),
        "share_plant_more_selective": ("plant_more_selective", "mismatch"),
        "share_plant_less_co": ("plant_less_co", "mismatch"),
        "share_plant_higher_x": ("plant_higher_x", "mismatch"),
        "share_plant_cooler": ("plant_cooler", "mismatch"),
        "disagreement_rate_sty_leader_most_selective": ("mismatch", "sty_leader_is_most_selective"),
        "disagreement_rate_sty_leader_not_most_selective": ("mismatch", "_not_most_selective"),
    }


def main():
    cand = pd.read_csv(FROZEN_CANDIDATES)
    out, tabs = {}, []
    for scen in ("S6", "S5"):
        t = group_table(cand, scen)
        t["_not_most_selective"] = ~t.sty_leader_is_most_selective
        a = ANCHORS[scen]
        b = bootstrap(t.rename(columns={"mismatch": "top1_mismatch"}), n=BOOT_N, seed=BOOT_SEED)
        assert len(t) == 40 and t.doi.nunique() == 28, (scen, len(t))
        assert int(t.mismatch.sum()) == a["mismatch"], (scen, int(t.mismatch.sum()))
        assert abs(b["ci95"][0] - a["ci"][0]) < 1e-3 and abs(b["ci95"][1] - a["ci"][1]) < 1e-3, (scen, b["ci95"])
        assert int(t.rule_correct.sum()) == a["rule_correct"], (scen, int(t.rule_correct.sum()))
        s = paper_boot(t, stats_for(t))
        out[scen] = dict(cost_column=SCEN[scen], rule=RULE_FOR[scen], groups=len(t), papers=int(t.doi.nunique()),
                         disagreements=int(t.mismatch.sum()), disagreements_gt5pct=int((t.mismatch & (t.regret > 0.05)).sum()),
                         frozen_bootstrap=b, stats=s,
                         kinds=t[t.mismatch].kind.value_counts().to_dict())
        tabs.append(t.drop(columns=["_not_most_selective"]).assign(scenario=scen))
    pd.concat(tabs).to_csv(HERE / "prediction_frozen_groups.csv", index=False, float_format="%.6g")
    (HERE / "prediction_frozen.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    for scen, o in out.items():
        s = o["stats"]
        print(f"{scen}: {o['disagreements']}/{o['groups']} ({o['disagreements_gt5pct']} > 5 %), CI "
              f"{o['frozen_bootstrap']['ci95'][0]:.3f}-{o['frozen_bootstrap']['ci95'][1]:.3f}")
        for k, v in s.items():
            print(f"   {k:50s} {v['value']:.3f}  [{v['ci95'][0]:.3f}, {v['ci95'][1]:.3f}]  ({v['numerator']:.2f}/{v['denominator']:.0f})")


if __name__ == "__main__":
    main()
