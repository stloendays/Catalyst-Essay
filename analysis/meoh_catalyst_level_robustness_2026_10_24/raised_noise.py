"""Methanol catalyst-level count with more catalyst loaded (the headline 21/63) under re-measurement noise.

Error model, draws and seed are those of the frozen statistics script
(analysis/meoh_main_result_stats_2026_10_06/run_main_result_stats.py: R.draws, meas_k1, 2,000 draws, stream
[SEED, 0]), here drawn over the 566 entries of the 63 catalyst-level groups. Each perturbed entry is costed as in
analysis/verify_2026_10_12_s6_conversion/run_s6_conversion.evaluate for f = 0.95: the laboratory point and every
state with more catalyst up to 0.95 of the feed equilibrium conversion, inlet limit 6.86 %, cheapest admissible
state. Costs of the draws come from the frozen script's additive per-dimension piecewise-linear response surface
(ln X, MeOH -> CH4 transfer, ln STY; the MeOH -> CO transfer is zero in meas_k1), on a coarser grid than the
laboratory-conversion run because the raised-conversion cost is smooth in conversion; a draw outside the grid, or in an
interval that touches an infeasible grid point, is run exactly. Exact replicates check the surface.

Gates: the unperturbed cost of every entry equals its committed cost_f0.95; the catalyst-level count is 21 of 63.

    set MEOH_FIELD_SET=combined
    python raised_noise.py [--workers 6]     -> raised_grid.csv (resumable), raised_exact.csv, summary_noise_raised.json,
                                                groups_noise_raised.csv
"""
import argparse
import csv
import json
import math
import os
import sys
import time
from multiprocessing import Pool
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MEOH_FIELD_SET", "combined")

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

HERE = Path(__file__).resolve().parent
AN = HERE.parent
sys.path.insert(0, str(AN / "meoh_main_result_stats_2026_10_06"))
sys.path.insert(0, str(AN / "verify_2026_10_12_s6_conversion"))
sys.path.insert(0, str(AN / "meoh_catalyst_level_2026_10_19"))
import run_main_result_stats as R  # noqa: E402
import run_s6_conversion as S  # noqa: E402
import run_catalyst_level as CL  # noqa: E402

G, RC = S.G, S.RC
F = 0.95
KEYS = ("X", "SMeOH", "SCH4", "SCO", "STY", "P_bar", "h2_co2", "T_C", "y_co2")
GRID = {"u": [-0.25, -0.1, -0.03, 0.03, 0.1, 0.25],     # noise sd 0.052 in each of ln X and ln STY
        "v": [-0.25, 0.25],
        "d4": [-0.04, -0.008, 0.008, 0.04]}                # sd 0.0085
DIMS = ("u", "d4", "v")
N_VALID = 2
GRID_CSV, EXACT_CSV = HERE / "raised_grid.csv", HERE / "raised_exact.csv"


def raised_cost(e, pert):
    """cost_f0.95 of the perturbed entry (run_s6_conversion.evaluate, f = 0.95 only)."""
    c, sty0 = R.perturbed(e, **pert)
    if c["SMeOH"] <= 1e-6 or c["SCH4"] < -1e-12 or c["SCO"] < -1e-12:
        return float("nan")
    c["SCH4"], c["SCO"] = max(c["SCH4"], 0.0), max(c["SCO"], 0.0)
    X0, P, h2, T = c["X"], e["P_bar"], e["h2_co2"], e["T_C"]
    kw = dict(P_bar=P, h2_co2=h2, T_C=T, **RC.KW_RULE)
    cands = []
    try:
        s = G.purge_sweep(c, STY_per_g_cat=sty0, **kw)
        lab_cost = np.asarray(s["cost_eur_t"], dtype=float)
        ok = G.eligible_purges(s)
        if ok.any():
            cands.append(float(np.min(lab_cost[ok])))
    except ValueError:
        pass
    xeq, _ = RC.x_eq_feed(h2, e["y_co2"], T, P)
    u0 = X0 / xeq
    if u0 < 0.99:
        us = np.unique(np.concatenate([np.linspace(u0, 0.99, RC.U_GRID + 1)[1:],
                                       [f for f in (0.90, 0.95, 0.99) if f > u0]]))
        us = us[us <= F + 1e-12]
        ms = np.log(1.0 - us) / np.log(1.0 - u0)
        us, ms = us[ms > 1.0], ms[ms > 1.0]
        Xs = us * xeq
        stys = sty0 * Xs / (X0 * ms)
        try:        # every state at once, broadcast over the purge grid (as run_conversion_sensitivity.evaluate)
            r = G.cost(dict(c, X=Xs[:, None]), purge=G.PURGES[None, :], STY_per_g_cat=stys[:, None], **kw)
            res = [r]
        except ValueError:      # some state infeasible: one by one, as run_s6_conversion.evaluate
            res = []
            for X, sty in zip(Xs, stys):
                try:
                    res.append(G.cost(dict(c, X=X), purge=G.PURGES, STY_per_g_cat=sty, **kw))
                except ValueError:
                    continue
        for r in res:
            cost = np.asarray(r["cost_eur_t"], dtype=float)
            ok = ((np.asarray(r["co2_hyd_approach"], dtype=float) <= 1.0 + RC.EQ_TOL)
                  & (np.asarray(r["nonreactive_fraction"], dtype=float) <= G.NONREACTIVE_MAX) & np.isfinite(cost))
            if ok.any():
                cands.append(float(np.min(cost[ok])))
    return min(cands) if cands else float("nan")


def _job(args):
    tag, e, pert = args
    return tag, raised_cost(e, pert)


def run_jobs(jobs, path, workers, fields):
    """Compute jobs (tag, entry, pert) not yet in path; append rows as they finish (resumable)."""
    done = set()
    if path.exists():
        done = set(pd.read_csv(path).tag)
    todo = [j for j in jobs if j[0] not in done]
    print(f"{path.name}: {len(jobs) - len(todo)} cached, {len(todo)} to run", flush=True)
    if todo:
        new = not path.exists()
        t0 = time.time()
        with path.open("a", newline="", encoding="utf-8") as fh, Pool(workers) as pool:
            w = csv.writer(fh)
            if new:
                w.writerow(["tag", "cost"])
            for i, (tag, cost) in enumerate(pool.imap_unordered(_job, todo, chunksize=2)):
                w.writerow([tag, repr(cost)])
                fh.flush()
                if i % 200 == 0:
                    print(f"  {i + 1}/{len(todo)}  {time.time() - t0:.0f} s", flush=True)
    t = pd.read_csv(path)
    return dict(zip(t.tag, t.cost.astype(float)))


def load():
    p = pd.read_csv(CL.CONV)
    p = p[p["mode"] == "printed"]
    pool = pd.read_csv(CL.POOLED / "pooled_candidates.csv")
    key = ["group", "catalyst", "T_C", "STY"]
    p = p.merge(pool[key + ["sty_basis"]], on=key, how="left", validate="one_to_one")
    f = CL.identities(CL.scored(p, "cost_f0.95"))
    n = f.groupby("group").cat_primary.nunique()
    f = f[f.group.isin(n[n >= 2].index)].reset_index(drop=True)
    f["sty_printed_basis"] = f.sty_basis.fillna("").str.startswith("printed STY")
    f["plot_read"] = False
    return f


def leaders(sty, cost, gid, cat, ng):
    sty = np.where(np.isnan(cost), np.nan, sty)
    n = sty.shape[0]
    ch = np.zeros((n, ng), dtype=bool)
    for g in range(ng):
        idx = np.where(gid == g)[0]
        s, c = sty[:, idx], cost[:, idx]
        ok = ~np.isnan(c)
        ncat = np.array([len(set(cat[idx][ok[r]])) for r in range(n)])
        ls = idx[np.argmax(np.where(ok, s, -np.inf), axis=1)]
        lc = idx[np.argmin(np.where(ok, c, np.inf), axis=1)]
        ch[:, g] = (cat[ls] != cat[lc]) & (ncat >= 2)
    return ch


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()
    t0 = time.time()
    f = load()
    ents = [{k: float(getattr(r, k)) for k in KEYS} for r in f.itertuples()]
    gid, ng = R.group_index(f)
    cat = f.cat_primary.to_numpy()
    assert (len(f), ng) == (566, 63), (len(f), ng)

    # grid (f0 + per-dimension points inside the physical range)
    jobs = []
    for i, e in enumerate(ents):
        jobs.append((f"{i}|f0|0", e, {}))
        for k in DIMS:
            for x in GRID[k]:
                if k == "d4" and not (-e["SCH4"] - 1e-12 <= x <= 0.9 * e["SMeOH"]):
                    continue
                jobs.append((f"{i}|{k}|{x:g}", e, {k: x}))
            if k == "d4" and 1e-9 < e["SCH4"] < 0.04:
                jobs.append((f"{i}|d4|{-e['SCH4']:.12g}", e, {"d4": -e["SCH4"]}))
    grid = run_jobs(jobs, GRID_CSV, a.workers, None)
    f0 = np.array([grid[f"{i}|f0|0"] for i in range(len(ents))])
    dev = np.nanmax(np.abs(f0 - f["cost_f0.95"].to_numpy()) / f["cost_f0.95"].to_numpy())
    assert dev < 1e-8 and np.isfinite(f0).all(), ("f0 gate", dev)
    ch0 = leaders(f.STY.to_numpy()[None, :], f0[None, :], gid, cat, ng)[0]
    assert int(ch0.sum()) == 21, int(ch0.sum())

    tab = {}
    for tag, cost in grid.items():
        i, k, x = tag.split("|")
        if k != "f0":
            tab.setdefault((int(i), k), []).append((float(x), cost))
    for key, pts in tab.items():
        pts.append((0.0, f0[key[0]]))
        pts.sort()
        xa = np.array([p[0] for p in pts])
        ya = np.array([p[1] for p in pts])
        tab[key] = (xa, ya)

    # draws: frozen error model and stream
    srng = np.random.default_rng([R.SEED, 0])
    P, sty = R.draws(f, srng, R.N_MC, k_meas=1.0)
    cost = np.repeat(f0[None, :], R.N_MC, axis=0)
    outside = np.zeros_like(cost, dtype=bool)
    for (i, k), (xa, ya) in tab.items():
        x = P[k][:, i]
        ok = np.isfinite(ya)
        cost[:, i] += np.interp(x, xa[ok], ya[ok]) - f0[i]
        bad = np.interp(x, xa, (~ok).astype(float)) > 0
        outside[:, i] |= (x < xa[0] - 1e-12) | (x > xa[-1] + 1e-12) | bad
    for i in range(len(ents)):          # an entry without a grid in a dimension (e.g. no admissible d4 point)
        for k in DIMS:
            if (i, k) not in tab:
                outside[:, i] |= np.abs(P[k][:, i]) > 1e-12
    rr, ee = np.where(outside)
    print(f"draws outside the grid: {len(rr)}", flush=True)
    xjobs = [(f"draw|{r}|{e}", ents[e], {k: float(P[k][r, e]) for k in DIMS}) for r, e in zip(rr, ee)]
    for r in range(N_VALID):
        xjobs += [(f"valid|{r}|{e}", ents[e], {k: float(P[k][r, e]) for k in DIMS}) for e in range(len(ents))]
    ex = run_jobs(xjobs, EXACT_CSV, a.workers, None)
    for r, e in zip(rr, ee):
        cost[r, e] = ex[f"draw|{r}|{e}"]

    ch = leaders(sty, cost, gid, cat, ng)
    valid = []
    for r in range(N_VALID):
        exr = np.array([ex[f"valid|{r}|{e}"] for e in range(len(ents))])
        che = leaders(sty[r:r + 1], exr[None, :], gid, cat, ng)[0]
        rel = np.abs(cost[r] - exr) / exr
        valid.append(dict(replicate=r, surface_changed=int(ch[r].sum()), exact_changed=int(che.sum()),
                          groups_different_verdict=int((ch[r] != che).sum()),
                          cost_rel_err_median=float(np.nanmedian(rel)), cost_rel_err_max=float(np.nanmax(rel))))
    p = ch.mean(axis=0)
    n_ch = ch.sum(axis=1)
    groups = pd.factorize(f.group)[1]
    doi = f.groupby(gid).doi.first().to_numpy()
    gap = CL.compare(CL.catalyst_table(f, "cat_primary", "cost_f0.95")).set_index("group").gap
    out = dict(basis="more catalyst loaded (f = 0.95), inlet limit 6.86 %, meas_k1 (2,000 draws)",
               entries=len(f), groups=int(ng), observed_changed=int(ch0.sum()),
               observed_kept_ge90=int(((p >= 0.9) & ch0).sum()), observed_kept_ge50=int(((p >= 0.5) & ch0).sum()),
               observed_gt5pct=int(sum(gap[g] > 0.05 for g, c0 in zip(groups, ch0) if c0)),
               observed_gt5pct_kept_ge90=int(sum((gap[g] > 0.05) and pp >= 0.9 for g, c0, pp in zip(groups, ch0, p) if c0)),
               unchanged_flipped_ge50=int(((p >= 0.5) & ~ch0).sum()),
               changed_per_draw_mean=float(n_ch.mean()),
               changed_per_draw_q025_q975=[float(np.quantile(n_ch, 0.025)), float(np.quantile(n_ch, 0.975))],
               grid_runs=len(jobs), exact_draw_runs=int(len(rr)), validation=valid,
               f0_max_rel_dev=float(dev), runtime_s=round(time.time() - t0))
    pd.DataFrame(dict(group=groups, doi=doi, observed_changed=ch0, p_changed=p)).to_csv(
        HERE / "groups_noise_raised.csv", index=False, float_format="%.6g")
    (HERE / "summary_noise_raised.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
