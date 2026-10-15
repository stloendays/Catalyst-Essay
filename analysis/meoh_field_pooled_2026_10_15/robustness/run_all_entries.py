"""Plot-read cohort on the combined set: every entry of both extractions, plot readings included, scored in the
inert-limited loop (S6, cost_recycled_opt_inlet) and without the limit (S5, cost_recycled_opt).

First set: analysis/meoh_literature_inversion_2026_10_05/literature_candidates_all_entries.csv (frozen; 54 of 82 and
35 of 83). Second set: build_candidates(load_new_records(corrected=True), printed_only=False), costed by
field_set.second_all_entries() with the first set's plant_costs call (validation_meoh_prospective_2026_10_13/score.py
scores the same cohort: 47 of 78 and 23 of 78). Scored with the frozen code: meoh_candidates.aggregate, bootstrap
(10,000 paper resamples, seed 20261006) and mismatch_kinds.classify.

    MEOH_FIELD_SET=combined python run_all_entries.py   -> all_entries/summary.json, all_entries/groups.csv
"""
import json
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import field_set as FS  # noqa: E402

if not FS.COMBINED:
    raise SystemExit("run with MEOH_FIELD_SET=combined")
sys.path.insert(0, str(FS.INV))
from meoh_candidates import aggregate, bootstrap  # noqa: E402
from mismatch_kinds import classify  # noqa: E402

OUT = FS.out_dir("all_entries", HERE)
SCEN = {"S6": "cost_recycled_opt_inlet", "S5": "cost_recycled_opt"}
ANCHORS = {"first": {"S6": (54, 82), "S5": (35, 83)}, "second": {"S6": (47, 78), "S5": (23, 78)}}


def counts(gm):
    m = gm[gm.top1_mismatch]
    return dict(groups=int(len(gm)), papers=int(gm.doi.nunique()), disagreements=int(len(m)),
                gt5pct=int((m.regret > 0.05).sum()), papers_with_disagreement=int(m.doi.nunique()))


def main():
    c = FS.candidates_all_entries()
    out, tabs = {}, []
    for name, col in SCEN.items():
        gm, s = aggregate(c, col)
        gm, kinds = classify(c, gm, col)
        res = dict(combined=counts(gm), entries=s["entries"], candidates_infeasible=s["candidates_infeasible"],
                   groups_lost_to_infeasibility=s["groups_lost_to_infeasibility"],
                   pairwise_inversions=s["pairwise_inversions"], bootstrap=bootstrap(gm),
                   other_catalyst=kinds["other_catalyst"], other_temperature=kinds["other_temperature"])
        batch = c.groupby("group").batch.first()
        for b in ("first", "second"):
            res[b] = counts(gm[gm.group.map(batch) == b])
            got = (res[b]["disagreements"], res[b]["groups"])
            assert got == ANCHORS[b][name], (b, name, got, ANCHORS[b][name])
        out[name] = res
        tabs.append(gm.assign(scenario=name, batch=gm.group.map(batch)))
        print(name, res["combined"], "first", res["first"], "second", res["second"])
    out["rows"] = {b: int((c.batch == b).sum()) for b in ("first", "second")}
    pd.concat(tabs).to_csv(OUT / "groups.csv", index=False, float_format="%.6g")
    (OUT / "summary.json").write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
