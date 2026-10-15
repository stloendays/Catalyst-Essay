"""POST HOC (not pre-registered): the frozen 40 groups pooled with the new batch's primary groups.

PREREGISTRATION.md section 2(c) scores the new batch on its own; this pooled reading was asked for after the result
was known (2026-10-15) and is reported as post hoc next to the registered verdict, never in place of it.
Frozen groups: group_table on the frozen candidates (as score.py's evaluate does); new groups: scored_groups.csv,
cohort "primary (printed, corrected)". Same paper-cluster bootstrap (pv_common.paper_boot, seed BOOT_SEED).

    python pooled_posthoc.py  -> pooled_posthoc.json
"""
from __future__ import annotations

import json

import pandas as pd

from pv_common import FROZEN_CANDIDATES, HERE, SCEN, group_table, paper_boot

new = pd.read_csv(HERE / "scored_groups.csv")
new = new[new.cohort == "primary (printed, corrected)"]
frozen_cand = pd.read_csv(FROZEN_CANDIDATES)
out = {"note": "POST HOC: pooling is not part of the pre-registration (section 2(c): the new batch is scored on its own)"}
for scen in SCEN:
    f = group_table(frozen_cand, scen).assign(batch="frozen")
    n = new[new.scenario == scen].assign(batch="new")
    assert not set(f.doi) & set(n.doi), "a paper appears in both batches"
    t = pd.concat([f, n], ignore_index=True)
    t["mismatch"] = t["mismatch"].astype(bool)
    t["rule_correct"] = t["rule_correct"].astype(bool)
    t["rule_minus_chance"] = t["rule_correct"].astype(float) - t["chance"].astype(float)
    st = paper_boot(t, {"disagreement_rate": ("mismatch", None), "rule_accuracy": ("rule_correct", None),
                        "chance_accuracy": ("chance", None), "rule_minus_chance": ("rule_minus_chance", None)})
    out[scen] = {"groups": int(len(t)), "papers": int(t.doi.nunique()),
                 "by_batch": {b: {"groups": int(len(g)), "papers": int(g.doi.nunique()),
                                  "disagreements": int(g.mismatch.sum()), "rule_correct": int(g.rule_correct.sum())}
                              for b, g in t.groupby("batch")},
                 "disagreements": int(t.mismatch.sum()),
                 "disagreements_gt5pct": int((t.mismatch & (t.regret > 0.05)).sum()),
                 "stats": st}
    s = st["disagreement_rate"]
    print(f"{scen}: pooled {int(t.mismatch.sum())}/{len(t)} = {100 * s['value']:.1f}% "
          f"(CI {100 * s['ci95'][0]:.1f}-{100 * s['ci95'][1]:.1f}%), rule {int(t.rule_correct.sum())}/{len(t)}, "
          f"rule-chance CI {[round(100 * x, 1) for x in st['rule_minus_chance']['ci95']]} pp; {out[scen]['by_batch']}")
(HERE / "pooled_posthoc.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
