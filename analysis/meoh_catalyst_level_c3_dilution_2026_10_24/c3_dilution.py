"""C3: methanol loop without the hard inlet limit, with inert dilution written into the catalyst rate.

The headline counts (21/63 with more catalyst loaded, 26/63 at laboratory conversion) hold the reactor inlet to at most
6.86 % CO + CH4 + N2; without that limit the counts are 8/63 and 16/63 (meoh_catalyst_level_2026_10_19/run_no_limit.py).
In the unlimited loop the cost model keeps each catalyst's laboratory STY however much the recycle dilutes the
reactants, so the purge can be cut until the inlet carries a median 8.8 % CO. Here the limit is dropped and the dilution
is charged to the rate instead:

    STY_plant(purge) = STY_lab * [(1 - phi(purge)) / rho_lab]^n

phi is the reactor-inlet non-H2/CO2 fraction of the loop at that purge (meoh_general_model, nonreactive_fraction),
rho_lab the reactant fraction of the laboratory feed, y_CO2 (1 + H2/CO2) (the same feed that sets the equilibrium
conversion in run_conversion_sensitivity.x_eq_feed); both at the same total pressure and H2/CO2 ratio, so the ratio is
the change in the H2 and CO2 partial pressures, and n is the sum of the apparent H2 and CO2 orders. The purge is then
chosen by cost alone, over every level of the conversion-capped sweep (the unlimited loop, S5), and the more-catalyst
treatment raises conversion exactly as run_conversion_sensitivity.evaluate (f = 0.95) with the diluted STY at each
state and purge. n = 0 is the unlimited loop and must reproduce cost_recycled_opt and cost_f0.95 of
robustness/conversion_s5 (gate), and the counts 16/63 and 8/63.

    set MEOH_FIELD_SET=combined
    python c3_dilution.py [--workers 4]     -> c3_points.csv, summary.json
"""
import argparse
import json
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
sys.path.insert(0, str(AN / "meoh_literature_inversion_2026_10_05"))
sys.path.insert(0, str(AN / "meoh_catalyst_level_2026_10_19"))
import run_conversion_sensitivity as RC  # noqa: E402
import run_catalyst_level as CL  # noqa: E402

G = RC.G
NS = (0.0, 0.5, 1.0, 1.5, 2.0)
F = 0.95
SRC = CL.POOLED / "robustness" / "conversion_s5" / "conversion_sensitivity_points.csv"
KEYS = ("X", "SMeOH", "SCH4", "SCO", "STY", "P_bar", "h2_co2", "T_C", "y_co2")


def entry_costs(e):
    """{n: (lab cost, raised cost f = 0.95)} for one entry."""
    c = dict(X=e["X"], SMeOH=e["SMeOH"], SCH4=e["SCH4"], SCO=e["SCO"])
    sty0, X0 = e["STY"], e["X"]
    kw = dict(P_bar=e["P_bar"], h2_co2=e["h2_co2"], T_C=e["T_C"])
    rho = min(1.0, e["y_co2"] * (1.0 + e["h2_co2"]))
    s = G.purge_sweep(c, STY_per_g_cat=sty0, **RC.KW_RULE, **kw)
    phi = np.asarray(s["nonreactive_fraction"], dtype=float)
    lab = {}
    for n in NS:
        fac = ((1.0 - phi) / rho) ** n
        if n == 0.0:
            cost = np.asarray(s["cost_eur_t"], dtype=float)
        else:
            r = G.cost(dict(c, X=s["X_eff"]), purge=G.PURGES, x_co=s["x_co"], STY_per_g_cat=sty0 * fac, **kw)
            cost = np.asarray(r["cost_eur_t"], dtype=float)
        lab[n] = float(np.nanmin(cost))

    xeq, _ = RC.x_eq_feed(e["h2_co2"], e["y_co2"], e["T_C"], e["P_bar"])
    u0 = X0 / xeq
    states = []
    if u0 < 0.99:
        us = np.unique(np.concatenate([np.linspace(u0, 0.99, RC.U_GRID + 1)[1:],
                                       [f for f in (0.90, 0.95, 0.99) if f > u0]]))
        us = us[us <= F + 1e-12]
        ms = np.log(1.0 - us) / np.log(1.0 - u0)
        states = [(u, m) for u, m in zip(us, ms) if m > 1.0]
    raised = {n: [lab[n]] for n in NS}
    if states:
        us, ms = np.array([u for u, _ in states]), np.array([m for _, m in states])
        Xs = us * xeq
        stys = sty0 * Xs / (X0 * ms)
        blocks = []
        try:
            r = G.cost(dict(c, X=Xs[:, None]), purge=G.PURGES[None, :], STY_per_g_cat=stys[:, None],
                       **RC.KW_RULE, **kw)
            blocks.append((Xs[:, None], stys[:, None], r))
        except ValueError:
            for X, sty in zip(Xs, stys):
                try:
                    blocks.append((X, sty, G.cost(dict(c, X=X), purge=G.PURGES, STY_per_g_cat=sty, **RC.KW_RULE, **kw)))
                except ValueError:
                    continue
        for X, sty, r in blocks:
            ok = np.asarray(r["co2_hyd_approach"], dtype=float) <= 1.0 + RC.EQ_TOL
            ph = np.asarray(r["nonreactive_fraction"], dtype=float)
            for n in NS:
                if n == 0.0:
                    cost = np.asarray(r["cost_eur_t"], dtype=float)
                else:
                    rr = G.cost(dict(c, X=X), purge=G.PURGES, x_co=r["x_co"], STY_per_g_cat=sty * ((1.0 - ph) / rho) ** n,
                                **kw)
                    cost = np.asarray(rr["cost_eur_t"], dtype=float)
                m = np.where(ok & np.isfinite(cost), cost, np.inf)
                raised[n].append(float(m.min()))
    return {n: (lab[n], min(v for v in raised[n] if np.isfinite(v))) for n in NS}


def _job(args):
    i, e = args
    try:
        return i, entry_costs(e)
    except Exception as exc:  # noqa: BLE001
        return i, repr(exc)


def counts(f, col):
    g = CL.compare(CL.catalyst_table(CL.identities(CL.scored(f, col)), "cat_primary", col))
    b = CL.brief(g)
    return dict(changed=b["changed"], groups=b["groups_2plus_catalysts"], gt5pct=b["gt5pct"], ci95=b["ci95"]), g


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    t0 = time.time()
    p = pd.read_csv(SRC)
    p = p[p["mode"] == "printed"].reset_index(drop=True).assign(sty_basis="")
    jobs = [(i, {k: float(getattr(r, k)) for k in KEYS}) for i, r in enumerate(p.itertuples())]
    with Pool(a.workers) as pool:
        res = dict(pool.imap_unordered(_job, jobs, chunksize=2))
    errs = {i: v for i, v in res.items() if isinstance(v, str)}
    assert not errs, list(errs.items())[:5]
    for n in NS:
        p[f"lab_n{n:g}"] = [res[i][n][0] for i in range(len(p))]
        p[f"raised_n{n:g}"] = [res[i][n][1] for i in range(len(p))]
    d_lab = np.nanmax(np.abs(p.lab_n0 - p.cost_recycled_opt) / p.cost_recycled_opt)
    d_rai = np.nanmax(np.abs(p.raised_n0 - p["cost_f0.95"]) / p["cost_f0.95"])
    assert d_lab < 1e-8 and d_rai < 1e-8, ("n = 0 gate", d_lab, d_rai)
    out = dict(gate=dict(lab_max_rel_dev=float(d_lab), raised_max_rel_dev=float(d_rai)), variants={})
    for n in NS:
        cl, _ = counts(p, f"lab_n{n:g}")
        cr, _ = counts(p, f"raised_n{n:g}")
        out["variants"][f"n = {n:g}"] = {"laboratory conversion": cl, "more catalyst loaded (f = 0.95)": cr}
        print(f"n = {n:g}: lab {cl['changed']}/{cl['groups']} (>5% {cl['gt5pct']}), raised {cr['changed']}/{cr['groups']} "
              f"(>5% {cr['gt5pct']})", flush=True)
    v0 = out["variants"]["n = 0"]
    assert (v0["laboratory conversion"]["changed"], v0["more catalyst loaded (f = 0.95)"]["changed"]) == (16, 8), v0
    out["runtime_s"] = round(time.time() - t0)
    p.to_csv(HERE / "c3_points.csv", index=False, float_format="%.10g")
    (HERE / "summary.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
