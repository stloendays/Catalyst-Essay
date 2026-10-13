"""Item 6: each catalyst priced from its own composition, under S5 (frozen) and S6 (inlet-limited).

Imports analysis/meoh_catalyst_cost_2026_10_06/run_catalyst_cost_inversion.py unchanged (candidate rebuild, composition
prices catalyst_prices.build, VARIANTS, charges_for, aggregate, bootstrap) and swaps only the purge levels the minimum is
taken over:

  S5  every level of the conversion-capped sweep (the frozen _one, called as is)
  S6  the eligible levels of the same sweep (meoh_general_model.eligible_purges: equilibrium feasible and reactor-inlet
      CH4 + CO + N2 <= 6.86 %); the catalyst charge does not change the loop, so the eligible set is that of the
      sweep without it

Checks: the catalyst term off reproduces the frozen cost column of each treatment and its group count (S5 15/40,
S6 28/40); the S5 primary (composition price, 3-year life) reproduces the frozen 16/40 and candidate_costs.csv.
Writes catalyst_cost.json (this folder).
"""
import json
import os
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
CCDIR = REPO / "analysis" / "meoh_catalyst_cost_2026_10_06"
sys.path.insert(0, str(CCDIR))
import run_catalyst_cost_inversion as CC  # noqa: E402

G = CC.G
WORKERS = int(os.environ.get("CATCOST_WORKERS", "4"))
FROZEN_COL = {"S5": "cost_recycled_opt", "S6": "cost_recycled_opt_inlet"}


def _one_s6(args):
    """CC._one with the minimum taken over the eligible purge levels (S6)."""
    row, charges = args
    c = (row["X"], row["SMeOH"], row["SCH4"], row["SCO"])
    kw = dict(STY_per_g_cat=row["STY"], P_bar=row["P_bar"], h2_co2=row["h2_co2"], T_C=row["T_C"])
    base = G.purge_sweep(dict(X=c[0], SMeOH=c[1], SCH4=c[2], SCO=c[3]), x_co="recycled_central", **kw)
    ok = G.eligible_purges(base)                      # the only change from CC._one
    c = (base["X_eff"],) + c[1:]
    out = {}
    for name, (price, life) in charges.items():
        extra = {} if price is None else dict(cat_price_eur_kg=price, cat_life_y=life)
        e = G.economics(*c, purge=G.PURGES, x_co=base["x_co"], **kw, **extra)
        if not ok.any():
            out[name] = (np.nan, np.nan, np.nan, float(e["catalyst_t"]))
            continue
        j = int(np.argmin(np.where(ok, e["cost_eur_t"], np.inf)))
        out[name] = (float(e["cost_eur_t"][j]), float(G.PURGES[j]), float(e["cat_repl_eur_t"]),
                     float(e["catalyst_t"]))
    return out


def main():
    cand = CC.build_candidates()
    frozen = pd.read_csv(CC.INV / "literature_candidates.csv")
    key = ["group", "entry"]
    b = frozen.set_index(key).sort_index()
    assert len(cand) == len(b) and (cand.set_index(key).sort_index().index == b.index).all()
    prices = CC.CP.build(cand)
    rows = cand[CC.ROW_KEYS].to_dict("records")
    args = list(zip(rows, CC.charges_for(prices)))
    out = {}
    fz = pd.read_csv(CCDIR / "candidate_costs.csv").set_index(key).sort_index()
    for treat, fn in (("S5", CC._one), ("S6", _one_s6)):
        with Pool(WORKERS) as pool:
            res = pool.map(fn, args, chunksize=4)
        f = cand.copy()
        for name in CC.VARIANTS:
            f[f"cost_{name}"] = [r[name][0] for r in res]
        a = f.set_index(key).sort_index()
        ref = b[FROZEN_COL[treat]]
        assert (np.isnan(a.cost_off) == np.isnan(ref)).all()
        dev_off = float(np.nanmax(np.abs(a.cost_off / ref - 1)))
        assert dev_off < 1e-9, (treat, dev_off)
        summ = {}
        for name in CC.VARIANTS:
            gm, s = CC.aggregate(f, f"cost_{name}", label=name)
            m = gm[gm.top1_mismatch]
            summ[name] = dict(groups=s["groups"], disagreements=s["top1_mismatch_groups"],
                              papers_with_disagreement=s["papers_with_mismatch"], gt5pct=int((m.regret > 0.05).sum()),
                              median_regret_disagreements=s["regret_median_mismatched"],
                              pairwise_inversions=s["pairwise_inversions"])
            if name == CC.PRIMARY:
                summ[name]["bootstrap"] = CC.bootstrap(gm)
                gm_off, _ = CC.aggregate(f, "cost_off")
                g, g0 = gm.set_index("group"), gm_off.set_index("group")
                summ[name]["groups_flipped_vs_off"] = int((g.top1_mismatch != g0.loc[g.index, "top1_mismatch"]).sum())
        if treat == "S5":
            dev = float(np.nanmax(np.abs(a[f"cost_{CC.PRIMARY}"] / fz[f"cost_{CC.PRIMARY}"] - 1)))
            assert dev < 1e-5, dev                    # candidate_costs.csv is written with 6 significant digits
            assert summ[CC.PRIMARY]["disagreements"] == 16 and summ["off"]["disagreements"] == 15, summ
        else:
            assert summ["off"]["disagreements"] == 28, summ["off"]
        out[treat] = dict(max_rel_diff_off_vs_frozen_column=dev_off, variants=summ)
        print(treat, {k: (v["disagreements"], v["groups"], v["gt5pct"]) for k, v in summ.items()}, flush=True)
    (HERE / "catalyst_cost.json").write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
