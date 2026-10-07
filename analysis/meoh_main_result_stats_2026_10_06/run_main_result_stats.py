"""How firm is the headline methanol result (paper STY leader != plant-cost leader in 33 of 83 comparisons)?

Input: analysis/meoh_literature_inversion_2026_10_05/literature_candidates.csv (the 906 entries in the 83 comparison
groups with at least two entries) and group_metrics.csv. The plant model, candidate construction and group
definitions are those of run_literature_inversion.py and are not changed.

A. Sampling uncertainty. The 83 groups come from 44 papers, and groups of one paper are not independent. A
   paper-cluster bootstrap (10,000 resamples of papers with replacement) gives the 95 % interval of the share of
   groups whose STY leader is not the plant-cost leader; the paper-weighted share is bootstrapped the same way.
B. Size of the disagreement. Share of groups whose STY leader is not the plant-cost leader AND costs more than the
   plant-cost leader by at least t (regret threshold curve, t = 0-10 %).
C. Measurement noise. Every entry is re-measured with the error model derived from the paper's own data for the
   hand-built methanol case (analysis/meoh_measurement_mc_2026_10_05/uncertainty_basis.json):
   relative CO2-conversion error r_X = 5.21 % (log-normal), sum-conserving MeOH -> CH4 selectivity transfer
   sigma = 0.847 percentage points, and, where the paper prints its STY, an independent relative STY error r_X
   (cross-detector scatter). Where STY is derived from the space velocity it follows the perturbed X * S_MeOH.
   Both leaderboards are rebuilt from the same perturbed entry, so a noisy STY moves cost and STY together. Noise
   scales k = 1, 2, 4 are run.
   Re-measurement null: the same noise applied twice; the share of groups whose STY leader changes between two
   independent re-measurements is the disagreement that measurement reproducibility alone produces.
D. Extraction error. For entries whose conversion or selectivity was read from a plot, the agent's measured plot
   reading errors (agent/extraction/eval/field_scores.csv, adjudicated truth, plot and SI-plot values) are
   resampled and removed: ln(X) error, methanol-selectivity error as a MeOH <-> CO transfer (the closure residual),
   and the STY error where the group prints STY. Combined with measurement noise k = 1.

Plant cost of a perturbed entry: recycled CO (central RWGS rule), entry-optimal purge, at the entry's own T, P and
H2/CO2 -- the primary treatment. Each entry gets an additive per-dimension response surface from exact model runs
on a grid in each perturbation coordinate (ln X, MeOH->CH4, MeOH->CO, ln STY); draws outside the grid are run
exactly. The surface is validated against exact runs of complete replicates (validation.csv).

Outputs (this folder): grid_costs.csv, validation.csv, group_noise_probabilities.csv, regret_threshold_curve.csv,
summary.json.

Every exact model run is stored in exact_cache.csv.gz under a key built from the entry state and the perturbation, so
a run is never repeated and the work can be split across machines (.github/workflows/methanol-stats.yml):
  STATS_MODE=enumerate      list the runs still missing from the cache into STATS_JOBS_OUT and stop; first the
                            response-surface grid, then (once the grid is cached) every draw outside the grid and the
                            validation replicates. The draws do not depend on exact results, only on the completed grid.
  compute JOBS SHARD N OUT  run jobs[SHARD::N] and write key,cost to OUT
  merge PART...             add part files to the cache
  (no mode)                 the full analysis; runs still missing are computed locally.
"""
import json
import os
import pickle
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

SRC = Path(__file__).resolve().parent
REPO = SRC.parents[1]
HERE = SRC / "_smoke" if os.environ.get("STATS_SMOKE") == "1" else SRC
HERE.mkdir(exist_ok=True)
INV = REPO / "analysis" / "meoh_literature_inversion_2026_10_05"
sys.path.insert(0, str(REPO / "data" / "meoh"))
import meoh_general_model as G  # noqa: E402

BASIS = json.loads((REPO / "analysis" / "meoh_measurement_mc_2026_10_05" / "uncertainty_basis.json")
                   .read_text(encoding="utf-8"))["adopted"]
R_X = float(BASIS["r_X_relative_sd"])                 # 0.0521
SIG_D = float(BASIS["sigma_delta_pct"]) / 100.0       # 0.00847
SEED = 20261006
N_BOOT = 10_000
N_MC = 2_000
N_VALID = 5                                           # exact replicates per validated scenario
WORKERS = int(os.environ.get("STATS_WORKERS", "8"))   # each worker commits ~0.8 GB; 24 exhausted the 15 GB machine
SMOKE = os.environ.get("STATS_SMOKE") == "1"          # 4 groups, few draws, separate output folder
if SMOKE:
    N_BOOT, N_MC, N_VALID = 200, 50, 1

GRID_LN = np.array([-2.5, -1.5, -1.0, -0.7, -0.35, -0.15, -0.05, 0.05, 0.15, 0.35, 0.7, 1.0, 1.5])
GRID_D = np.array([-0.15, -0.1, -0.06, -0.025, -0.008, 0.008, 0.025, 0.06, 0.1, 0.15])
DIMS = ("u", "d4", "dc", "v")                         # ln X, MeOH->CH4, MeOH->CO, ln STY


# ---------------------------------------------------------------- exact model --------------------------------
def perturbed(e, u=0.0, d4=0.0, dc=0.0, v=0.0):
    X = min(e["X"] * np.exp(u), 0.99)
    sm = e["SMeOH"] - d4 - dc
    return dict(X=X, SMeOH=sm, SCH4=e["SCH4"] + d4, SCO=e["SCO"] + dc), e["STY"] * np.exp(v)


def exact_cost(args):
    e, pert = args
    c, sty = perturbed(e, **pert)
    if c["SMeOH"] <= 1e-6 or c["SCH4"] < -1e-12 or c["SCO"] < -1e-12:
        return np.nan
    c["SCH4"], c["SCO"] = max(c["SCH4"], 0.0), max(c["SCO"], 0.0)
    try:
        sweep = G.purge_sweep(c, STY_per_g_cat=sty, P_bar=e["P_bar"], h2_co2=e["h2_co2"], T_C=e["T_C"],
                              x_co="recycled_central")["cost_eur_t"]
    except ValueError:      # perturbed state outside the model's feasible loop (e.g. H2 inlet ratio insufficient)
        return np.nan
    return float(np.nanmin(sweep))


CACHE_FILE = HERE / "exact_cache.csv.gz"
MODE = os.environ.get("STATS_MODE", "run")
_CACHE = None
_PENDING = {}


class NeedJobs(Exception):
    """Raised in enumerate mode when the response-surface grid is incomplete."""


def job_key(job):
    """Entry state and perturbation, each float written exactly (17 significant digits)."""
    e, pert = job
    state = "|".join("%.17g" % e[k] for k in ("X", "SMeOH", "SCH4", "SCO", "STY", "P_bar", "h2_co2", "T_C"))
    return state + "#" + "|".join("%s=%.17g" % (k, pert[k]) for k in DIMS if pert.get(k, 0.0) != 0.0)


def exact_cache():
    global _CACHE
    if _CACHE is None:
        _CACHE = {}
        if CACHE_FILE.exists():
            t = pd.read_csv(CACHE_FILE, dtype={"key": str, "cost": float})
            _CACHE = dict(zip(t.key, t.cost))
    return _CACHE


def save_cache():
    t = pd.DataFrame(sorted(exact_cache().items()), columns=["key", "cost"])
    t.to_csv(CACHE_FILE, index=False, float_format="%.17g", compression={"method": "gzip", "mtime": 0})


def _compute(jobs):
    if not jobs:
        return np.array([])
    with Pool(WORKERS) as pool:
        return np.array(pool.map(exact_cost, jobs, chunksize=4))


def run_exact(jobs):
    cache = exact_cache()
    keys = [job_key(j) for j in jobs]
    miss = {}
    for k, j in zip(keys, jobs):
        if k not in cache and k not in miss:
            miss[k] = j
    if miss:
        if MODE == "enumerate":
            _PENDING.update(miss)
        else:
            ks = list(miss)
            cache.update(zip(ks, _compute([miss[k] for k in ks])))
            save_cache()
    return np.array([cache.get(k, np.nan) for k in keys], dtype=float)


def write_pending(stage):
    out = Path(os.environ.get("STATS_JOBS_OUT", str(HERE / "pending_jobs.pkl")))
    with open(out, "wb") as f:
        pickle.dump(dict(stage=stage, jobs=list(_PENDING.items())), f)
    print(json.dumps(dict(stage=stage, pending=len(_PENDING), jobs_file=str(out))), flush=True)


def cmd_compute(jobs_file, shard, nshards, out):
    with open(jobs_file, "rb") as f:
        jobs = pickle.load(f)["jobs"][int(shard)::int(nshards)]
    costs = _compute([j for _, j in jobs])
    pd.DataFrame(dict(key=[k for k, _ in jobs], cost=costs)).to_csv(out, index=False, float_format="%.17g")
    print(json.dumps(dict(shard=int(shard), nshards=int(nshards), jobs=len(jobs))), flush=True)


def cmd_merge(parts):
    cache = exact_cache()
    n0 = len(cache)
    for p in parts:
        t = pd.read_csv(p, dtype={"key": str, "cost": float})
        cache.update(zip(t.key, t.cost))
    save_cache()
    print(json.dumps(dict(cache_before=n0, cache_after=len(cache), parts=len(parts))), flush=True)


# ---------------------------------------------------------------- data ---------------------------------------
def load():
    c = pd.read_csv(INV / "literature_candidates.csv")
    n = c.groupby("group").size()
    c = c[c.group.isin(n[n >= 2].index)].reset_index(drop=True)
    if SMOKE:
        c = c[c.group.isin(c.group.unique()[:4])].reset_index(drop=True)
    c["printed"] = c.sty_basis.str.startswith("printed STY")
    gm = pd.read_csv(INV / "group_metrics.csv")
    return c, gm


def entry_dicts(c):
    keys = ["X", "SMeOH", "SCH4", "SCO", "STY", "P_bar", "h2_co2", "T_C"]
    return [{k: float(getattr(r, k)) for k in keys} for r in c.itertuples()]


def grid_points(e):
    """Per-entry grid in each coordinate, inside the physically allowed range."""
    pts = {"u": list(GRID_LN), "v": list(GRID_LN)}
    pts["d4"] = [d for d in GRID_D if -e["SCH4"] - 1e-12 <= d <= e["SMeOH"] * 0.9]
    pts["dc"] = [d for d in GRID_D if -e["SCO"] - 1e-12 <= d <= e["SMeOH"] * 0.9]
    if e["SCH4"] > 1e-9 and e["SCH4"] < 0.06:
        pts["d4"].append(-e["SCH4"])
    if e["SCO"] > 1e-9 and e["SCO"] < 0.06:
        pts["dc"].append(-e["SCO"])
    return {k: sorted(set(round(float(x), 12) for x in v)) for k, v in pts.items()}


# ---------------------------------------------------------------- response surface ---------------------------
class Surface:
    """Additive per-dimension piecewise-linear response: cost = f0 + sum_k [f_k(x_k) - f0]."""

    def __init__(self, c, ents, grid_csv):
        self.c, self.ents = c, ents
        # grid points already computed are reused; only missing ones are run
        g = pd.read_csv(grid_csv) if grid_csv.exists() else pd.DataFrame(columns=["entry", "dim", "x", "cost"])
        have = {(int(r.entry), r.dim, round(float(r.x), 12)) for r in g.itertuples()}
        jobs, meta = [], []
        for i, e in enumerate(ents):
            if (i, "f0", 0.0) not in have:
                jobs.append((e, {}))
                meta.append((i, "f0", 0.0))
            for k, xs in grid_points(e).items():
                for x in xs:
                    if (i, k, round(float(x), 12)) not in have:
                        jobs.append((e, {k: x}))
                        meta.append((i, k, x))
        if jobs:
            new = pd.DataFrame(meta, columns=["entry", "dim", "x"])
            new["cost"] = run_exact(jobs)
            if MODE == "enumerate" and _PENDING:
                raise NeedJobs("grid")
            g = pd.concat([g, new], ignore_index=True)
            g.to_csv(grid_csv, index=False, float_format="%.10g")
        self.f0 = g[g.dim == "f0"].set_index("entry").cost.reindex(range(len(ents))).to_numpy()
        self.tab = {}
        for (i, k), s in g[g.dim != "f0"].groupby(["entry", "dim"]):
            s = s.dropna(subset=["cost"])
            xs = np.r_[s.x.to_numpy(), 0.0]
            ys = np.r_[s.cost.to_numpy(), self.f0[i]]
            o = np.argsort(xs)
            self.tab[(i, k)] = (xs[o], ys[o])

    def cost(self, P):
        """P: dict dim -> array (n_rep, n_entry). Returns surface costs and a mask of draws outside the grid."""
        out = np.repeat(self.f0[None, :], next(iter(P.values())).shape[0], axis=0).astype(float)
        outside = np.zeros_like(out, dtype=bool)
        for k, arr in P.items():
            for i in range(arr.shape[1]):
                xs, ys = self.tab.get((i, k), (np.array([0.0]), np.array([self.f0[i]])))
                x = arr[:, i]
                out[:, i] += np.interp(x, xs, ys) - self.f0[i]
                outside[:, i] |= (x < xs[0] - 1e-12) | (x > xs[-1] + 1e-12)
        return out, outside


# ---------------------------------------------------------------- perturbation draws -------------------------
def draws(c, rng, n, k_meas=1.0, extraction=False, pools=None):
    m = len(c)
    S, SCH4, SCO = c.SMeOH.to_numpy(), c.SCH4.to_numpy(), c.SCO.to_numpy()
    u = rng.normal(0.0, k_meas * R_X, (n, m))
    d4 = rng.normal(0.0, k_meas * SIG_D, (n, m))
    v_print = rng.normal(0.0, k_meas * R_X, (n, m))
    dc = np.zeros((n, m))
    if extraction:
        pr = c.plot_read.to_numpy()
        printed = c.printed.to_numpy()
        lx, ds, ls = pools
        u += np.where(pr, -rng.choice(lx, (n, m)), 0.0)
        dc += np.where(pr, rng.choice(ds, (n, m)), 0.0)
        v_print += np.where(pr & printed, -rng.choice(ls, (n, m)), 0.0)
    d4 = np.clip(d4, -SCH4, 0.9 * S)
    dc = np.clip(dc, -SCO, 0.9 * S - d4)
    s_new = S - d4 - dc
    v_der = u + np.log(s_new / S)
    v = np.where(c.printed.to_numpy(), v_print, v_der)
    sty = c.STY.to_numpy() * np.exp(v)
    return dict(u=u, d4=d4, dc=dc, v=v), sty


def extraction_pools():
    f = pd.read_csv(REPO / "agent" / "extraction" / "eval" / "field_scores.csv")
    f = f[(f.truth == "adjudicated") & f.source_type.isin(["plot", "SI-plot"])].dropna(subset=["extracted", "curated"])
    x = f[(f.field == "X_CO2") & (f.curated > 0) & (f.extracted > 0)]
    s = f[f.field == "S_MeOH"]
    t = f[(f.field == "STY") & (f.curated > 0) & (f.extracted > 0)]
    lx = np.log(x.extracted / x.curated).to_numpy()
    ds = ((s.extracted - s.curated) / 100.0).to_numpy()
    ls = np.log(t.extracted / t.curated).to_numpy()
    return lx, ds, ls, dict(n_X=len(lx), n_S=len(ds), n_STY=len(ls))


# ---------------------------------------------------------------- leaderboards -------------------------------
def group_index(c):
    gid = pd.factorize(c.group)[0]
    return gid, int(gid.max()) + 1


def winners(values, gid, ng, highest):
    """Index of the leader of every group for each replicate row (ties: first entry)."""
    n = values.shape[0]
    out = np.empty((n, ng), dtype=int)
    for g in range(ng):
        idx = np.where(gid == g)[0]
        sub = values[:, idx]
        j = np.nanargmax(sub, axis=1) if highest else np.nanargmin(sub, axis=1)
        out[:, g] = idx[j]
    return out


def mismatch_stats(sty, cost, gid, ng):
    # an entry whose perturbed state is infeasible in the plant model leaves both leaderboards of that draw
    sty = np.where(np.isnan(cost), np.nan, sty)
    ws = winners(sty, gid, ng, True)
    wc = winners(cost, gid, ng, False)
    rows = np.arange(sty.shape[0])[:, None]
    c_up = cost[rows, ws]
    c_best = cost[rows, wc]
    regret = (c_up - c_best) / c_best
    return ws, wc, ws != wc, regret


# ---------------------------------------------------------------- main ---------------------------------------
def main():
    rng = np.random.default_rng(SEED)
    c, gm = load()
    ents = entry_dicts(c)
    gid, ng = group_index(c)
    groups = pd.Series(pd.factorize(c.group)[1])
    doi_of_group = c.groupby(gid).doi.first().to_numpy()

    try:
        surf = Surface(c, ents, HERE / "grid_costs.csv")
    except NeedJobs:
        write_pending("grid")
        return
    base_diff = np.nanmax(np.abs(surf.f0 - c.cost_recycled_opt.to_numpy()) / c.cost_recycled_opt.to_numpy())

    # point estimate, reproduced from the frozen candidate costs
    sty0 = c.STY.to_numpy()[None, :]
    cost0 = c.cost_recycled_opt.to_numpy()[None, :]
    _, _, mm0, reg0 = mismatch_stats(sty0, cost0, gid, ng)
    mm0, reg0 = mm0[0], reg0[0]
    if not SMOKE:
        assert int(mm0.sum()) == int(gm.top1_mismatch.sum()), "point estimate does not reproduce group_metrics.csv"

    # A. paper-cluster bootstrap
    papers = np.unique(doi_of_group)
    by_paper = {p: np.where(doi_of_group == p)[0] for p in papers}
    boot, boot_pw = np.empty(N_BOOT), np.empty(N_BOOT)
    for b in range(N_BOOT):
        pick = rng.choice(papers, len(papers), replace=True)
        idx = np.concatenate([by_paper[p] for p in pick])
        boot[b] = mm0[idx].mean()
        boot_pw[b] = np.mean([mm0[by_paper[p]].mean() for p in pick])
    paper_w = np.mean([mm0[by_paper[p]].mean() for p in papers])

    # B. regret threshold curve
    thresholds = [0.0, 0.001, 0.005, 0.01, 0.02, 0.05, 0.10]
    curve = []
    for t in thresholds:
        hit = mm0 & (reg0 >= t) if t > 0 else mm0
        curve.append(dict(threshold=t, groups=int(hit.sum()), fraction=float(hit.mean()),
                          papers=int(len(set(doi_of_group[hit])))))
    curve = pd.DataFrame(curve)

    # C/D. noise scenarios with the response surface
    lx, ds, ls, pool_n = extraction_pools()
    scenarios = {"meas_k1": dict(k_meas=1.0), "meas_k2": dict(k_meas=2.0), "meas_k4": dict(k_meas=4.0),
                 "meas_k1_plus_extraction": dict(k_meas=1.0, extraction=True)}
    results, per_group, valid_rows = {}, {}, []
    for si, (name, kw) in enumerate(scenarios.items()):
        cache = HERE / f"scenario_{name}.json"
        if cache.exists():                      # a scenario finished in an earlier run is not recomputed
            saved = json.loads(cache.read_text(encoding="utf-8"))
            results[name], per_group[name] = saved["result"], np.array(saved["p_mismatch"])
            valid_rows += saved["validation"]
            print(name, "(cached)", flush=True)
            continue
        srng = np.random.default_rng([SEED, si])  # per-scenario stream, reproducible on restart
        P, sty = draws(c, srng, N_MC, pools=(lx, ds, ls), **kw)
        cost, outside = surf.cost(P)
        # draws outside the grid are run exactly
        rr, ee = np.where(outside)
        if len(rr):
            jobs = [(ents[e], {k: float(P[k][r, e]) for k in DIMS}) for r, e in zip(rr, ee)]
            cost[rr, ee] = run_exact(jobs)
        if MODE == "enumerate":                 # list the validation replicates too; the statistics wait for the runs
            for r in range(N_VALID):
                run_exact([(ents[e], {k: float(P[k][r, e]) for k in DIMS}) for e in range(len(ents))])
            continue
        ws, wc, mm, reg = mismatch_stats(sty, cost, gid, ng)
        # re-measurement null: a second independent re-measurement of the same entries
        P2, sty2 = draws(c, srng, N_MC, pools=(lx, ds, ls), **kw)
        ws2 = winners(sty2, gid, ng, True)
        n_mm = mm.sum(axis=1)
        results[name] = dict(
            exact_runs_outside_grid=int(len(rr)),
            mismatch_groups_mean=float(n_mm.mean()),
            mismatch_groups_q025_q975=[float(np.quantile(n_mm, 0.025)), float(np.quantile(n_mm, 0.975))],
            mismatch_fraction_mean=float(mm.mean()),
            mismatch_with_regret_ge_1pct_mean=float((mm & (reg >= 0.01)).sum(axis=1).mean()),
            groups_mismatched_in_ge_90pct_of_draws=int((mm.mean(axis=0) >= 0.9).sum()),
            groups_mismatched_in_ge_50pct_of_draws=int((mm.mean(axis=0) >= 0.5).sum()),
            observed_mismatches_kept_in_ge_90pct=int(((mm.mean(axis=0) >= 0.9) & mm0).sum()),
            observed_matches_flipped_in_ge_50pct=int(((mm.mean(axis=0) >= 0.5) & ~mm0).sum()),
            null_sty_leader_changes_between_remeasurements_mean=float((ws != ws2).sum(axis=1).mean()),
            null_sty_leader_changes_q025_q975=[float(np.quantile((ws != ws2).sum(axis=1), 0.025)),
                                               float(np.quantile((ws != ws2).sum(axis=1), 0.975))],
            sty_leader_differs_from_reported_mean=float((ws != winners(sty0, gid, ng, True)).sum(axis=1).mean()),
            sty_leader_differs_from_reported_q025_q975=[
                float(np.quantile((ws != winners(sty0, gid, ng, True)).sum(axis=1), 0.025)),
                float(np.quantile((ws != winners(sty0, gid, ng, True)).sum(axis=1), 0.975))],
        )
        per_group[name] = mm.mean(axis=0)

        # validation: complete replicates run exactly with the same draws
        for r in range(N_VALID):
            jobs = [(ents[e], {k: float(P[k][r, e]) for k in DIMS}) for e in range(len(ents))]
            ex = run_exact(jobs)
            _, _, mm_ex, _ = mismatch_stats(sty[r:r + 1], ex[None, :], gid, ng)
            rel = np.abs(cost[r] - ex) / ex
            valid_rows.append(dict(scenario=name, replicate=r, surface_mismatch_groups=int(mm[r].sum()),
                                   exact_mismatch_groups=int(mm_ex.sum()),
                                   groups_with_different_verdict=int((mm[r] != mm_ex[0]).sum()),
                                   cost_rel_err_median=float(np.nanmedian(rel)),
                                   cost_rel_err_p99=float(np.nanquantile(rel, 0.99)),
                                   cost_rel_err_max=float(np.nanmax(rel))))
        cache.write_text(json.dumps(dict(result=results[name], p_mismatch=per_group[name].tolist(),
                                         validation=[v for v in valid_rows if v["scenario"] == name])),
                         encoding="utf-8")
        print(name, json.dumps(results[name]), flush=True)

    if MODE == "enumerate":
        write_pending("draws")
        return

    valid = pd.DataFrame(valid_rows)
    valid.to_csv(HERE / "validation.csv", index=False, float_format="%.6g")
    curve.to_csv(HERE / "regret_threshold_curve.csv", index=False, float_format="%.6g")
    pg = pd.DataFrame(dict(group=groups, doi=doi_of_group, observed_mismatch=mm0, observed_regret=reg0,
                           **{f"p_mismatch_{k}": v for k, v in per_group.items()}))
    pg.to_csv(HERE / "group_noise_probabilities.csv", index=False, float_format="%.6g")

    summary = dict(
        input=str(INV.relative_to(REPO)).replace("\\", "/"),
        groups=int(ng), papers=int(len(papers)), entries=int(len(c)),
        plot_read_entries=int(c.plot_read.sum()), printed_sty_entries=int(c.printed.sum()),
        surface_f0_max_rel_diff_vs_frozen=float(base_diff),
        point_estimate=dict(groups=int(mm0.sum()), fraction=float(mm0.mean()),
                            papers=int(len(set(doi_of_group[mm0]))), paper_weighted_fraction=float(paper_w)),
        cluster_bootstrap=dict(resamples=N_BOOT, unit="paper",
                               fraction_ci95=[float(np.quantile(boot, 0.025)), float(np.quantile(boot, 0.975))],
                               paper_weighted_ci95=[float(np.quantile(boot_pw, 0.025)),
                                                    float(np.quantile(boot_pw, 0.975))]),
        regret_threshold_curve=curve.to_dict(orient="records"),
        noise_model=dict(r_X=R_X, sigma_MeOH_to_CH4=SIG_D, source="analysis/meoh_measurement_mc_2026_10_05",
                         extraction_error_pools=pool_n, draws=N_MC, seed=SEED),
        noise=results,
        validation=dict(replicates_per_scenario=N_VALID,
                        verdict_disagreements_total=int(valid.groups_with_different_verdict.sum()),
                        verdicts_compared=int(len(valid) * ng),
                        cost_rel_err_max=float(valid.cost_rel_err_max.max()),
                        cost_rel_err_p99_max=float(valid.cost_rel_err_p99.max())),
    )
    (HERE / "summary.json").write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "compute":
        cmd_compute(*sys.argv[2:6])
    elif len(sys.argv) > 1 and sys.argv[1] == "merge":
        cmd_merge(sys.argv[2:])
    else:
        main()
