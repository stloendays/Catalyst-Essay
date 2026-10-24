"""Methanol catalyst-level count (63 groups with at least two catalysts) under re-measurement noise, and the
selectivity of the plant leader, at laboratory conversion and with more catalyst loaded.

The main text quotes two robustness figures that were computed on the 81 point-level comparisons: 42 of the 50
disagreements persist in >= 90 % of 2,000 re-measurements, and the plant leader is the more selective catalyst in 40
of the 50. Here both are redone on the catalyst-level unit of the headline (RULES.md of meoh_catalyst_level_2026_10_19).

Re-measurement (laboratory conversion, inlet limit 6.86 %): the frozen draws of
analysis/meoh_field_pooled_2026_10_15/robustness/stats_s6 (meas_k1, 2,000 draws, seed and stream of the frozen script),
costed from the committed response surface and exact cache, i.e. the same per-entry costs that gave 42/50. In each draw
every catalyst takes its highest-STY and its lowest-cost point; an entry with no feasible cost leaves both leaderboards
(frozen rule). Gate: the point-level count of these draws reproduces 42 of 50.

    set MEOH_FIELD_SET=combined
    python catalyst_level_noise.py     -> summary_noise_lab.json, groups_noise_lab.csv
"""
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

os.environ.setdefault("MEOH_FIELD_SET", "combined")
os.environ.setdefault("STATS_WORKERS", "2")
HERE = Path(__file__).resolve().parent
AN = HERE.parent
sys.argv = [sys.argv[0], "s6"]
sys.path.insert(0, str(AN / "meoh_s6_robustness_2026_10_13"))
sys.path.insert(0, str(AN / "meoh_catalyst_level_2026_10_19"))
import run_stats_wrapper as W  # noqa: E402
import run_catalyst_level as CL  # noqa: E402

R = W.R
R.exact_cost, R._compute, R.load = W.exact_cost_s6, W._compute_s6, W.load_s6


def cat_ids(c):
    return CL.identities(c.copy())["cat_primary"].to_numpy()


def catalyst_leaders(sty, cost, gid, cat, groups2):
    """Per draw and group (with >= 2 catalysts): catalyst of the STY leader and of the cost leader; None if empty."""
    sty = np.where(np.isnan(cost), np.nan, sty)
    n = sty.shape[0]
    changed = np.zeros((n, len(groups2)), dtype=bool)
    valid = np.zeros((n, len(groups2)), dtype=bool)
    for j, g in enumerate(groups2):
        idx = np.where(gid == g)[0]
        s, c = sty[:, idx], cost[:, idx]
        ok = ~np.isnan(c)
        # a group with fewer than two feasible catalysts in a draw is no comparison in that draw
        cats = cat[idx]
        ncat = np.array([len(set(cats[ok[r]])) for r in range(n)])
        ls = idx[np.argmax(np.where(ok, s, -np.inf), axis=1)]
        lc = idx[np.argmin(np.where(ok, c, np.inf), axis=1)]
        valid[:, j] = ncat >= 2
        changed[:, j] = (cat[ls] != cat[lc]) & valid[:, j]
    return changed, valid


def main():
    c, gm = R.load()
    ents = R.entry_dicts(c)
    gid, ng = R.group_index(c)
    cat = cat_ids(c)
    groups = pd.Series(pd.factorize(c.group)[1])
    ncat = pd.Series(cat).groupby(gid).nunique()
    groups2 = np.array([g for g in range(ng) if ncat[g] >= 2])
    doi = c.groupby(gid).doi.first().to_numpy()

    surf = R.Surface(c, ents, R.HERE / "grid_costs.csv")
    lx, ds, ls, _ = R.extraction_pools()
    srng = np.random.default_rng([R.SEED, 0])                       # meas_k1 stream of the frozen script
    P, sty = R.draws(c, srng, R.N_MC, pools=(lx, ds, ls), k_meas=1.0)
    cost, outside = surf.cost(P)
    rr, ee = np.where(outside)
    n_before = len(R.exact_cache())
    if len(rr):
        jobs = [(ents[e], {k: float(P[k][r, e]) for k in R.DIMS}) for r, e in zip(rr, ee)]
        cost[rr, ee] = R.run_exact(jobs)
    new_runs = len(R.exact_cache()) - n_before

    # gate: point level, 42 of the 50 observed disagreements kept in >= 90 % of draws
    sty0, cost0 = c.STY.to_numpy()[None, :], c.cost_recycled_opt.to_numpy()[None, :]
    _, _, mm0, _ = R.mismatch_stats(sty0, cost0, gid, ng)
    _, _, mm, _ = R.mismatch_stats(sty, cost, gid, ng)
    kept_pt = int(((mm.mean(axis=0) >= 0.9) & mm0[0]).sum())
    assert (int(mm0.sum()), kept_pt) == (50, 42), (int(mm0.sum()), kept_pt)

    ch0, v0 = catalyst_leaders(sty0, cost0, gid, cat, groups2)
    ch0 = ch0[0]
    assert (len(groups2), int(ch0.sum())) == (63, 26), (len(groups2), int(ch0.sum()))
    ch, val = catalyst_leaders(sty, cost, gid, cat, groups2)
    p = ch.mean(axis=0)
    n_ch = ch.sum(axis=1)
    out = dict(
        basis="laboratory conversion, inlet limit 6.86 %, meas_k1 (2,000 draws)",
        gate_point_level=dict(observed=int(mm0.sum()), kept_ge90=kept_pt),
        exact_runs_outside_grid=int(len(rr)), new_exact_runs=int(new_runs),
        groups=int(len(groups2)), observed_changed=int(ch0.sum()),
        observed_kept_ge90=int(((p >= 0.9) & ch0).sum()), observed_kept_ge50=int(((p >= 0.5) & ch0).sum()),
        unchanged_flipped_ge50=int(((p >= 0.5) & ~ch0).sum()),
        changed_per_draw_mean=float(n_ch.mean()),
        changed_per_draw_q025_q975=[float(np.quantile(n_ch, 0.025)), float(np.quantile(n_ch, 0.975))],
        groups_without_comparison_some_draw=int((~val).any(axis=0).sum()))
    pd.DataFrame(dict(group=groups[groups2].to_numpy(), doi=doi[groups2], observed_changed=ch0,
                      p_changed=p)).to_csv(HERE / "groups_noise_lab.csv", index=False, float_format="%.6g")
    (HERE / "summary_noise_lab.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
