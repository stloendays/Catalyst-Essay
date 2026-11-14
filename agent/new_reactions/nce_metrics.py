"""NCE ranking metrics as one module, used for every reaction (new and calibration):

point level     per comparison group (>= 2 entries): the lab-metric leader(s) vs the cheapest plant entry;
                changed when the cheapest is not a lab leader; kind 'other catalyst' or 'same catalyst, other
                temperature'; regret = J(lab leader) / J(cheapest) - 1 (as analysis/meoh_literature_inversion_2026_10_05)
catalyst level  each catalyst at its best lab value and at its lowest plant cost first, then catalysts are compared
                within the group (groups with >= 2 catalysts), as analysis/meoh_catalyst_level_2026_10_19/run_catalyst_level.compare
bootstrap       95 % CI by resampling papers (10,000 draws, seed 20261006), as the NCE scripts.
calibrate()     reproduces the NCE headline numbers from the NCE candidate tables (methanol pooled, NH3 printed).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
SEED = 20261006


def point_level(df, group, catalyst, lab, cost, paper):
    out = []
    for g, x in df.groupby(group):
        if len(x) < 2:
            continue
        leaders = x[x[lab] >= x[lab].max() - 1e-12]
        best = x.loc[x[cost].idxmin()]
        changed = best.name not in set(leaders.index)
        lab_cost = leaders[cost].min()
        kind = "" if not changed else ("same catalyst, other temperature" if best[catalyst] in set(leaders[catalyst]) else "other catalyst")
        out.append(dict(group=g, paper=x[paper].iloc[0], n=len(x), changed=changed, kind=kind, regret=lab_cost / best[cost] - 1))
    return pd.DataFrame(out)


def catalyst_level(df, group, catalyst, lab, cost, paper):
    rows = []
    for (g, c), x in df.groupby([group, catalyst]):
        rows.append(dict(group=g, catalyst=c, paper=x[paper].iloc[0], lab_best=x[lab].max(), cost_best=x[cost].min()))
    ct = pd.DataFrame(rows)
    out = []
    for g, x in ct.groupby("group"):
        if len(x) < 2:
            continue
        lab_lead = x[x.lab_best >= x.lab_best.max() - 1e-12]
        plant = x.loc[x.cost_best.idxmin()]
        out.append(dict(group=g, paper=x.paper.iloc[0], catalysts=len(x), changed=plant.catalyst not in set(lab_lead.catalyst),
                        regret=lab_lead.cost_best.min() / plant.cost_best - 1))
    return pd.DataFrame(out)


def bootstrap(gm, n=10_000, seed=SEED):
    per = gm.groupby("paper").changed.agg(["sum", "count"])
    s, c = per["sum"].to_numpy(float), per["count"].to_numpy(float)
    idx = np.random.default_rng(seed).integers(0, len(per), size=(n, len(per)))
    lo, hi = np.percentile(s[idx].sum(1) / c[idx].sum(1), [2.5, 97.5])
    return [round(float(lo), 4), round(float(hi), 4)]


def summarise(gm):
    if gm.empty:
        return dict(groups=0)
    ch = gm[gm.changed]
    d = dict(groups=len(gm), papers=int(gm.paper.nunique()), changed=int(gm.changed.sum()),
             fraction=round(float(gm.changed.mean()), 4), ci95=bootstrap(gm), papers_changed=int(ch.paper.nunique()),
             gt1pct=int((ch.regret > 0.01).sum()), gt5pct=int((ch.regret > 0.05).sum()), gt10pct=int((ch.regret > 0.10).sum()),
             median_regret_changed=round(float(ch.regret.median()), 4) if len(ch) else 0.0)
    if "kind" in gm:
        d["kinds"] = {k: int(v) for k, v in ch.kind.value_counts().items()}
    return d


def metrics(df, group="group", catalyst="catalyst", lab="lab", cost="cost", paper="paper"):
    return dict(point_level=summarise(point_level(df, group, catalyst, lab, cost, paper)),
                catalyst_level=summarise(catalyst_level(df, group, catalyst, lab, cost, paper)))


def calibrate():
    """Reproduce the NCE headline numbers with this module from the frozen NCE candidate tables."""
    res = {}
    import sys
    sys.path.insert(0, str(REPO / "analysis" / "meoh_catalyst_level_2026_10_19"))
    import run_catalyst_level as rcl          # NCE catalyst identity rule and scored set, reused as is
    me = pd.read_csv(REPO / "analysis/meoh_field_pooled_2026_10_15/pooled_candidates.csv")
    nce = json.loads((REPO / "analysis/meoh_catalyst_level_2026_10_19/summary.json").read_text(encoding="utf-8"))
    me = rcl.identities(rcl.scored(me, rcl.COST))
    m = metrics(me, group="group", catalyst="cat_primary", lab="STY", cost=rcl.COST, paper="doi")
    res["methanol"] = dict(ours=m, nce_point=nce["point_level_total"], nce_catalyst=nce["cat_primary"]["comparison"])
    nh = pd.read_csv(REPO / "analysis/nh3_field_expansion_2026_10_12/nh3_1_2/runs/pooled_vf_screen/candidates_printed.csv")
    nce_nh = json.loads((REPO / "analysis/nh3_field_expansion_2026_10_12/nh3_1_2/runs/pooled_vf_screen/summary_printed.json").read_text(encoding="utf-8"))
    nh = nh[nh.group.notna() & nh.cost_USD_t.notna() & nh.paper_rate.notna()]
    if "duplicate_in_group" in nh:
        nh = nh[nh.duplicate_in_group.isna() | (nh.duplicate_in_group == False)]  # noqa: E712
    m = metrics(nh, group="group", catalyst="catalyst", lab="paper_rate", cost="cost_USD_t", paper="doi")
    p = nce_nh["primary"]
    res["ammonia"] = dict(ours=m, nce=dict(groups=p["groups"], papers=p["papers"], changed=p["top1_mismatch_groups"],
                                           papers_changed=p["papers_with_mismatch"]))
    return res


if __name__ == "__main__":
    print(json.dumps(calibrate(), indent=1, default=str))
