"""Paired DOI-cluster bootstrap for *selected* S5 printed-only MeOH cases.

Unlike the obsolete all-entry 83-group CI, this resamples the 28 independent
papers of the author's selected 40-group cohort. Each sampled paper carries
all its eligible within-paper comparison groups. Lab and catalyst-inventory
scenarios resample the *same* DOI draws to preserve pairing.

Diagnostic until author confirmation; not a preregistered significance test.
"""
from __future__ import annotations
import argparse
import csv
import json
import math
import random
from collections import defaultdict
from pathlib import Path

VERIFY = Path(__file__).resolve().parents[1] / "verify_2026_10_08"
CONDITIONS = ("lab", "cost_f0.95")


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def percentile(a, q):
    b = sorted(a)
    if not b:
        raise ValueError("Percentile of empty sample")
    t = (len(b)-1)*q
    k = math.floor(t)
    return b[k] if k == len(b)-1 else b[k] + (t-k)*(b[k+1]-b[k])


def paired_ci(records, *, seed=20261009, draws=10000):
    if draws < 100:
        raise ValueError("At least 100 resamples required")
    by_condition = {}
    for cond in CONDITIONS:
        rows = [r for r in records if r["base"] == "thermo" and
                r["mode"] == "printed" and r["cost_col"] == cond]
        mp = {}
        for r in rows:
            k = (r["doi"], r["group"])
            if k in mp:
                raise ValueError(f"Repeated case {k} in {cond}")
            if r["mismatch"].lower() not in ("true", "false"):
                raise ValueError(f"Bad mismatch marker {r['mismatch']}")
            mp[k] = (r["mismatch"].lower() == "true", float(r["regret"]))
        by_condition[cond] = mp
    one, two = by_condition[CONDITIONS[0]], by_condition[CONDITIONS[1]]
    if not one or set(one) != set(two):
        raise ValueError("Before/after group IDs or DOIs are not identical")
    groups_by_doi = defaultdict(list)
    for doi, group in one:
        groups_by_doi[doi].append((doi, group))
    dois = sorted(groups_by_doi)
    n_papers = len(dois)
    obs = {}
    for cond, mp in by_condition.items():
        obs[cond] = dict(
            groups=len(mp), papers=n_papers,
            mismatches=sum(int(v[0]) for v in mp.values()),
            mismatches_gt5pct=sum(int(v[0] and v[1] > 0.05) for v in mp.values()),
        )
        obs[cond]["fraction"] = obs[cond]["mismatches"]/obs[cond]["groups"]
    observed_diff = obs["cost_f0.95"]["fraction"]-obs["lab"]["fraction"]
    rng = random.Random(seed)
    samples = {c: [] for c in CONDITIONS}
    diffs = []
    n_group_draws = []
    for _ in range(draws):
        chosen = rng.choices(dois, k=n_papers)
        keys = [k for doi in chosen for k in groups_by_doi[doi]]
        den = len(keys)
        if den == 0:
            raise ValueError("Bootstrap draw contains no groups")
        n_group_draws.append(den)
        for c, mp in by_condition.items():
            samples[c].append(sum(int(mp[k][0]) for k in keys)/den)
        diffs.append(samples["cost_f0.95"][-1]-samples["lab"][-1])
    return dict(
        status="DIAGNOSTIC_S5_PRINTED_NOT_FROZEN",
        protocol="DOI-cluster resampling, retain all comparison groups in each sampled DOI",
        seed=seed, draws=draws,
        observed=obs,
        cluster_ci95={c: [percentile(v,0.025),percentile(v,0.975)]
                      for c,v in samples.items()},
        paired_difference=dict(
            definition="adjustable mismatch fraction minus laboratory mismatch fraction",
            observed=observed_diff,
            cluster_ci95=[percentile(diffs,0.025),percentile(diffs,0.975)],
            paired_on="same DOI bootstrap draws and matched comparison groups",
        ),
        bootstrap_group_count_range=[min(n_group_draws),max(n_group_draws)],
        caveats=[
            "A paper may contribute multiple correlated comparisons; papers, not groups, are resampling units.",
            "Selection into the printed-only cohort is observational; neither group fraction is causal.",
            "Intervals describe this published-article sample; they do not validate the plant-cost model.",
            "Not preregistered, and not proof of a difference in the two model scenarios.",
        ],
    )


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--groups", type=Path, default=VERIFY/"conversion_sensitivity_groups.csv")
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--seed", type=int, default=20261009)
    ap.add_argument("--draws", type=int, default=10000)
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args()
    result = paired_ci(read_csv(args.groups), seed=args.seed, draws=args.draws)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir/"selected_meoh_paper_cluster_bootstrap.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.strict and not (
        result["observed"]["lab"]["groups"] == 40 and
        result["observed"]["lab"]["mismatches"] == 15 and
        result["observed"]["cost_f0.95"]["mismatches"] == 14 and
        result["observed"]["lab"]["papers"] == 28
    ):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
