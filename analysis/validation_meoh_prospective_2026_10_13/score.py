"""Score the prospective batch with the latest methanol model and compare with the committed predictions
(PREREGISTRATION.md sections 2, 5 and 6).

1. Regression: the frozen records (agent/extraction/out/records_normalized.csv) through build_candidates and
   plant_costs, exactly as run_literature_inversion.py does; S5 must give 15/40 and S6 28/40, else stop.
2. New batch (corrected records = primary; uncorrected and all-entries cohorts = sensitivities): build_candidates,
   plant_costs for every unique operating point (<= 8 workers), group_table for S6 and S5.
3. Blind predictions: the committed blind_predictions.csv / blind_rankings.csv are read back; the prediction of each
   group is the first entry of the committed ranking that is feasible in the scenario. It must equal the rule
   choice recomputed here (check), and its correctness is scored against the plant-cost leader.
4. Pass rules P1, P2 per scenario, secondary statistics, predictive interval, near-infeasibility split.

    python score.py   -> results.json, scored_groups.csv, new_candidates_costed.csv
"""
from __future__ import annotations

import json
import os
import sys
import time
from multiprocessing import Pool

import numpy as np
import pandas as pd

from pv_common import (BOOT_N, FROZEN_CANDIDATES, HERE, NEW_SEED, REPO, RULE_FOR, SCEN, G, bootstrap, group_table,
                       load_new_records, paper_boot)
from meoh_candidates import ROW_KEYS, build_candidates, plant_costs_star, read_records

WORKERS = min(8, int(os.environ.get("PV_WORKERS", "6")))
FROZEN_RECORDS = REPO / "agent" / "extraction" / "out" / "records_normalized.csv"
INTERVALS = {"S6": (0.5405405405405406, 0.8275862068965517), "S5": (0.15151515151515152, 0.5714285714285714)}


def cost(cands: list[pd.DataFrame]) -> list[pd.DataFrame]:
    keys = sorted({tuple(float(r[k]) for k in ROW_KEYS) for c in cands for r in c[ROW_KEYS].to_dict("records")})
    with Pool(WORKERS) as pool:
        res = pool.map(plant_costs_star, [(dict(zip(ROW_KEYS, k)), None) for k in keys], chunksize=2)
    table = dict(zip(keys, res))
    out = []
    for c in cands:
        costs = pd.DataFrame([table[tuple(float(r[k]) for k in ROW_KEYS)] for r in c[ROW_KEYS].to_dict("records")],
                             index=c.index)
        out.append(pd.concat([c, costs], axis=1))
    return out


def regression():
    c = build_candidates(read_records(FROZEN_RECORDS), printed_only=True)
    (c,) = cost([c])
    got = {s: group_table(c, s) for s in SCEN}
    res = {s: f"{int(t.mismatch.sum())}/{len(t)}" for s, t in got.items()}
    frozen = pd.read_csv(FROZEN_CANDIDATES)
    maxrel = max(float(np.nanmax(np.abs(c[col].to_numpy(float) - frozen.set_index(["group", "catalyst"])
                                        .loc[list(zip(c.group, c.catalyst)), col].to_numpy(float))
                                 / frozen[col].abs().max())) for col in SCEN.values())
    ok = res == {"S6": "28/40", "S5": "15/40"}
    print(f"regression: {res}, max rel. cost difference vs frozen candidates {maxrel:.2e}", flush=True)
    if not ok:
        raise SystemExit("regression failed: the frozen result is not reproduced")
    return dict(result=res, max_rel_cost_diff_vs_frozen=maxrel)


def committed_prediction(scen, grp, feasible: set, ranks: pd.DataFrame):
    r = ranks[(ranks.scenario == scen) & (ranks.group == grp)].sort_values("rank", kind="stable")
    r = r[r.catalyst.isin(feasible)]
    if r.empty:
        return []
    top = r["rank"].iloc[0]
    return list(r[r["rank"] == top].catalyst)


def predictive_interval(frozen_t: pd.DataFrame, n_papers: int, seed=NEW_SEED, n=BOOT_N):
    per = frozen_t.groupby("doi").mismatch.agg(["sum", "count"])
    s, c = per["sum"].to_numpy(float), per["count"].to_numpy(float)
    idx = np.random.default_rng(seed).integers(0, len(per), size=(n, n_papers))
    v = s[idx].sum(1) / c[idx].sum(1)
    return [float(x) for x in np.percentile(v, [2.5, 97.5])]


def evaluate(cand: pd.DataFrame, label: str, ranks: pd.DataFrame | None, frozen_cand: pd.DataFrame) -> tuple[dict, list]:
    out, tabs = {"label": label}, []
    for scen, col in SCEN.items():
        t = group_table(cand, scen)
        if t.empty:
            out[scen] = dict(groups=0)
            continue
        f = cand[np.isfinite(cand[col].astype(float))]
        if ranks is not None:               # committed blind prediction, re-checked against the rule
            pred, agree = [], []
            for r in t.itertuples():
                g = f[f.group == r.group]
                p = committed_prediction(scen, r.group, set(g.catalyst), ranks)
                pred.append(" | ".join(p))
                agree.append(set(p) == set(getattr(r, f"{RULE_FOR[scen]}_choice").split(" | ")))
            t["blind_prediction"] = pred
            t["blind_equals_rule"] = agree
            t["blind_correct"] = [r.plant_leader in p.split(" | ") for r, p in zip(t.itertuples(), pred)]
        t["_not_most_selective"] = ~t.sty_leader_is_most_selective
        if scen == "S6":                    # near-infeasibility split (PR #69 rule)
            lab_cost_ratio = []
            for r in t.itertuples():
                e = f[(f.group == r.group) & (f.catalyst == r.lab_leader)].iloc[0]
                lab_cost_ratio.append(float(e[col]) / float(e["cost_recycled_opt"]))
            t["near_infeasible"] = t.mismatch & ((t.regret > 1) | (np.array(lab_cost_ratio) > 2))
        stats = paper_boot(t, {
            "disagreement_rate": ("mismatch", None),
            "rule_accuracy": ("rule_correct", None),
            "chance_accuracy": ("chance", None),
            "rule_minus_chance": (lambda d: d.rule_correct.astype(float) - d.chance, None),
            "sty_accuracy": ("STY_correct", None),
            "rule_minus_sty": (lambda d: d.rule_correct.astype(float) - d.STY_correct.astype(float), None),
            "share_plant_more_selective": ("plant_more_selective", "mismatch"),
            "share_plant_less_co": ("plant_less_co", "mismatch"),
            "share_plant_higher_x": ("plant_higher_x", "mismatch"),
            "share_plant_cooler": ("plant_cooler", "mismatch"),
            "disagreement_rate_sty_leader_most_selective": ("mismatch", "sty_leader_is_most_selective"),
            "disagreement_rate_sty_leader_not_most_selective": ("mismatch", "_not_most_selective"),
        }, seed=NEW_SEED)
        lo, hi = INTERVALS[scen]
        rate = stats["disagreement_rate"]["value"]
        p1 = bool(lo <= rate <= hi)
        p2 = bool(stats["rule_minus_chance"]["ci95"][0] > 0)
        frozen_t = group_table(frozen_cand, scen)
        o = dict(groups=len(t), papers=int(t.doi.nunique()), entries=int(t.n.sum()),
                 disagreements=int(t.mismatch.sum()), disagreements_gt5pct=int((t.mismatch & (t.regret > 0.05)).sum()),
                 papers_with_disagreement=int(t[t.mismatch].doi.nunique()),
                 median_regret_of_disagreements=float(t.loc[t.mismatch, "regret"].median()) if t.mismatch.any() else 0.0,
                 kinds=t[t.mismatch].kind.value_counts().to_dict(),
                 rule=RULE_FOR[scen], rule_correct=int(t.rule_correct.sum()),
                 frozen_bootstrap_of_new=bootstrap(t.rename(columns={"mismatch": "top1_mismatch"}), seed=NEW_SEED),
                 stats=stats, predicted_interval=[lo, hi],
                 predictive_interval_for_batch_size=predictive_interval(frozen_t, int(t.doi.nunique())),
                 P1_rate_inside_interval=p1, P2_rule_above_chance=p2, PASS=bool(p1 and p2),
                 M1_borne_out=bool(stats["disagreement_rate_sty_leader_not_most_selective"]["value"]
                                   > stats["disagreement_rate_sty_leader_most_selective"]["value"])
                 if t.sty_leader_is_most_selective.any() and (~t.sty_leader_is_most_selective).any() else None,
                 share_more_selective_above_half=bool(stats["share_plant_more_selective"]["value"] > 0.5)
                 if t.mismatch.any() else None,
                 share_higher_x_above_half=bool(stats["share_plant_higher_x"]["value"] > 0.5) if t.mismatch.any() else None)
        if ranks is not None:
            o["blind_predictions_equal_rule"] = int(t.blind_equals_rule.sum())
            o["blind_correct"] = int(t.blind_correct.sum())
        if scen == "S6":
            o["near_infeasible_disagreements"] = int(t.near_infeasible.sum())
            o["near_infeasible_gt5pct"] = int((t.near_infeasible & (t.regret > 0.05)).sum())
        out[scen] = o
        tabs.append(t.drop(columns=["_not_most_selective"]).assign(scenario=scen, cohort=label))
    return out, tabs


def main():
    t0 = time.time()
    res = {"regression": regression()}
    frozen_cand = pd.read_csv(FROZEN_CANDIDATES)
    ranks = pd.read_csv(HERE / "blind_rankings.csv")
    corr_log = []
    rec = load_new_records(corrected=True, log=corr_log)
    rec_u = load_new_records(corrected=False)
    cands = {"primary (printed, corrected)": build_candidates(rec, printed_only=True),
             "printed, uncorrected": build_candidates(rec_u, printed_only=True),
             "all entries, corrected": build_candidates(rec, printed_only=False)}
    costed = dict(zip(cands, cost(list(cands.values()))))
    tabs = []
    for label, c in costed.items():
        r, t = evaluate(c, label, ranks if label.startswith("primary") else None, frozen_cand)
        res[label] = r
        tabs += t
    res["corrections_applied"] = corr_log
    res["model"] = dict(file="data/meoh/meoh_general_model.py", S6_limit=float(G.NONREACTIVE_MAX))
    res["runtime_s"] = round(time.time() - t0, 1)
    pd.concat(tabs).to_csv(HERE / "scored_groups.csv", index=False, float_format="%.6g")
    costed["primary (printed, corrected)"].to_csv(HERE / "new_candidates_costed.csv", index=False, float_format="%.12g")
    (HERE / "results.json").write_text(json.dumps(res, indent=1, default=float) + "\n", encoding="utf-8")
    for label in cands:
        for scen in SCEN:
            o = res[label][scen]
            if not o.get("groups"):
                print(label, scen, "no groups")
                continue
            s = o["stats"]
            print(f"{label:30s} {scen}: {o['disagreements']}/{o['groups']} groups ({o['papers']} papers), "
                  f"CI {s['disagreement_rate']['ci95']}, rule {o['rule_correct']}/{o['groups']}, "
                  f"rule-chance CI {s['rule_minus_chance']['ci95']}, P1 {o['P1_rate_inside_interval']}, "
                  f"P2 {o['P2_rule_above_chance']}")


if __name__ == "__main__":
    sys.exit(main())
