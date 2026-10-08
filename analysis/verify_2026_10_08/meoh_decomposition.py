"""Step-by-step decomposition of the methanol field result between the original treatment on main (33/83) and the
physically constrained treatment of 2026-10-07 (54/82, branch meoh-physical-lock-2026-10-07 at LOCK).

Each step adds one change to the previous one and recounts the comparisons whose space-time-yield leader is not the
plant-cost leader:

  S0  main: records, group basis and model of main
  S1  + extraction records normalized with the unit-parsing fixes of LOCK (agent/extraction/normalize.py)
  S2  + group productivity basis of LOCK (printed STY also checked against the volumetric-GHSV reference)
  S3  + one measurement printed in several places counted once
  S4  + recycled-CO rule of LOCK: x_CO = min(x_RWGS, x_MeOH) (never beyond CO-hydrogenation equilibrium)
  S5  + single-pass conversion capped where the loop outlet reaches CO2-hydrogenation equilibrium
  S6  + purge restricted to reactor-inlet non-H2/CO2 <= 6.86 % (the workbook purge_diagnostic limit)

S4-S6 reproduce LOCK's variants recycled_opt_uncapped (36/83), recycled_opt_unconstrained (35/83) and its primary
(54/82). Every step is also evaluated on printed values only (mode "printed"): an entry enters only when its CO2
conversion, methanol selectivity and every reported CO/CH4 selectivity are printed numbers (qualifier =, < or <=, and
not taken from a plot by the figure passes), and a printed STY is used as the group basis only when it is itself
printed; otherwise the group falls back to the STY derived from the printed conversion, selectivity and space
velocity. Outputs: decomposition_steps.csv, decomposition_groups.csv (per group, step and mode),
decomposition.json, cost_cache.csv (every evaluated operating point and its four plant costs).
"""
import importlib.util
import json
import subprocess
import sys
import tempfile
from io import StringIO
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
LOCK = "86dcd76218e2fd5218d6da74e8f6092c0f1c2f3c"
sys.path.insert(0, str(REPO / "data" / "meoh"))
sys.path.insert(0, str(REPO / "analysis" / "meoh_literature_inversion_2026_10_05"))
import meoh_general_model as G  # noqa: E402
import meoh_candidates as MC  # noqa: E402


def git_show(path):
    return subprocess.run(["git", "-C", str(REPO), "show", f"{LOCK}:{path}"], capture_output=True, check=True,
                          text=True, encoding="utf-8").stdout


def load_lock_model():
    tmp = Path(tempfile.mkdtemp(prefix="meoh_lock_"))
    (tmp / "meoh_general_model_lock.py").write_text(git_show("data/meoh/meoh_general_model.py"), encoding="utf-8")
    spec = importlib.util.spec_from_file_location("meoh_general_model_lock", tmp / "meoh_general_model_lock.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


GL = None


def _init():
    global GL
    GL = load_lock_model()


PRINTED_SPREAD_MAX = 3.0


def basis_main(g):
    if g.sty_print.notna().all():
        ratio = g.sty_print / g.sty_mass
        if g.sty_mass.notna().all() and (ratio.min() <= 0 or ratio.max() / ratio.min() > PRINTED_SPREAD_MAX):
            return "STY from mass GHSV (printed STY inconsistent with X*S*F)", g.sty_mass
        return "printed STY", g.sty_print
    if g.sty_mass.notna().all():
        return "STY from mass GHSV", g.sty_mass
    if g.sty_vol.notna().all():
        return "STY from volumetric GHSV (assumed density)", g.sty_vol
    if g.sty_print.notna().any():
        return "printed STY (partial)", g.sty_print
    return None, None


def basis_lock(g):
    if g.sty_mass.notna().all():
        ref, ref_label = g.sty_mass, "STY from mass GHSV"
    elif g.sty_vol.notna().all():
        ref, ref_label = g.sty_vol, "STY from volumetric GHSV (assumed density)"
    else:
        ref, ref_label = None, None
    if g.sty_print.notna().all():
        if ref is not None:
            ratio = g.sty_print / ref
            if ratio.min() <= 0 or ratio.max() / ratio.min() > PRINTED_SPREAD_MAX:
                return ref_label + " (printed STY inconsistent with X*S*F)", ref
        return "printed STY", g.sty_print
    if ref is not None:
        return ref_label, ref
    if g.sty_print.notna().any():
        return "printed STY (partial)", g.sty_print
    return None, None


PRINTED_Q = ("=", "<", "<=")
PLOT_SRC = ("plot", "SI-plot")


def _printed(r, field):
    v, q, src = getattr(r, f"{field}_pct" if field != "STY" else "STY_g_gcat_h"), getattr(r, f"{field}_q"),         getattr(r, f"{field}_src")
    if pd.isna(v):
        return None                       # not reported
    return (q in PRINTED_Q) and (src not in PLOT_SRC)


def candidate(r, printed_only):
    c = MC.candidate_row(r)
    if c is None or not printed_only:
        return c
    perf = [_printed(r, f) for f in ("X_CO2", "S_MeOH", "S_CO", "S_CH4")]
    if not (perf[0] and perf[1]) or any(p is False for p in perf[2:]):
        return None
    if c["sty_print"] is not None and not _printed(r, "STY"):
        c["sty_print"] = None
    return c


def build(records, basis_fn, dedup, printed_only=False):
    d = records.dropna(subset=MC.REQUIRED).copy()
    cand = pd.DataFrame([c for c in (candidate(r, printed_only) for r in d.itertuples(index=False))
                         if c is not None])
    cand["group"] = (cand.doi + " | " + cand.P_bar.map("{:g} bar".format) + " | H2/CO2 "
                     + cand.h2_co2.map("{:.3g}".format) + " | " + cand.ghsv_key)
    parts = []
    for _, g in cand.groupby("group"):
        b, sty = basis_fn(g)
        g = g.copy()
        g["sty_basis"], g["STY"] = b, sty
        parts.append(g)
    cand = pd.concat([p for p in parts if p.STY.notna().any()]).dropna(subset=["STY"])
    cand = cand[cand.STY > 0]
    if dedup:
        cand = cand[~cand.duplicated(["group", "T_C", "X", "SMeOH", "SCH4", "SCO", "STY"], keep="first")]
    return cand.reset_index(drop=True)


KEYS = ["X", "SMeOH", "SCH4", "SCO", "STY", "P_bar", "h2_co2", "T_C"]


def costs_one(key):
    X, sm, sch4, sco, sty, P, h2, T = key
    c = dict(X=X, SMeOH=sm, SCH4=sch4, SCO=sco)
    kw = dict(STY_per_g_cat=sty, P_bar=P, h2_co2=h2, T_C=T, x_co="recycled_central")
    main = float(np.nanmin(np.asarray(G.purge_sweep(c, **kw)["cost_eur_t"], dtype=float)))
    su = GL.purge_sweep(c, cap_conversion=False, **kw)
    cu = np.asarray(su["cost_eur_t"], dtype=float)
    s = GL.purge_sweep(c, **kw)
    cc = np.asarray(s["cost_eur_t"], dtype=float)
    ok = GL.eligible_purges(s)
    return dict(main=main, lock_uncapped=float(np.nanmin(cu)), lock_capped=float(np.nanmin(cc)),
                lock_capped_limited=float(np.min(np.where(ok, cc, np.inf))) if ok.any() else np.nan)


def top1(frame, cost_col):
    f = frame[np.isfinite(frame[cost_col].astype(float))]
    rows = []
    for key, g in f.groupby("group"):
        if len(g) < 2:
            continue
        up_best = g.STY.max()
        up = set(g.index[g.STY >= up_best - 1e-12])
        econ = g[cost_col].idxmin()
        c_best, c_up = g[cost_col].min(), g.loc[list(up), cost_col].min()
        rows.append(dict(group=key, doi=g.doi.iloc[0], n=len(g), mismatch=econ not in up,
                         regret=(c_up - c_best) / c_best, sty_leader=g.loc[sorted(up)[0], "catalyst"],
                         cost_leader=g.at[econ, "catalyst"]))
    return pd.DataFrame(rows)


def main():
    rec_main = MC.read_records()
    rec_lock = pd.read_csv(StringIO(git_show("agent/extraction/out/records_normalized.csv")),
                           keep_default_na=False, na_values=[""])
    sets = {}
    for mode, po in (("all", False), ("printed", True)):
        sets[("S0", mode)] = build(rec_main, basis_main, False, po)
        sets[("S1", mode)] = build(rec_lock, basis_main, False, po)
        sets[("S2", mode)] = build(rec_lock, basis_lock, False, po)
        sets[("S3", mode)] = build(rec_lock, basis_lock, True, po)
    keys = sorted({tuple(float(v) for v in r) for s in sets.values() for r in s[KEYS].itertuples(index=False)})
    with Pool(4, initializer=_init) as pool:
        res = pool.map(costs_one, keys, chunksize=8)
    table = dict(zip(keys, res))
    pd.DataFrame([dict(zip(KEYS, k), **v) for k, v in table.items()]).to_csv(HERE / "cost_cache.csv", index=False,
                                                                           float_format="%.12g")

    def attach(frame, which):
        f = frame.copy()
        f["cost"] = [table[tuple(float(v) for v in r)][which] for r in f[KEYS].itertuples(index=False)]
        return f

    steps = [("S0", "S0", "main", "main: original treatment"),
             ("S1", "S1", "main", "+ unit-parsing fixes in the extraction normalization"),
             ("S2", "S2", "main", "+ printed STY checked against the volumetric-GHSV reference"),
             ("S3", "S3", "main", "+ repeated prints of one measurement counted once"),
             ("S4", "S3", "lock_uncapped", "+ recycled CO limited by CO-hydrogenation equilibrium"),
             ("S5", "S3", "lock_capped", "+ conversion capped at loop CO2-hydrogenation equilibrium"),
             ("S6", "S3", "lock_capped_limited", "+ purge limited to inlet non-H2/CO2 <= 6.86 %")]
    out, per = [], []
    for mode in ("all", "printed"):
      prev = None
      for name, cset, which, label in steps:
        f = attach(sets[(cset, mode)], which)
        gm = top1(f, "cost")
        mism = set(gm.loc[gm.mismatch, "group"])
        row = dict(mode=mode, step=name, change=label, records=len(rec_main if name == "S0" else rec_lock), candidates=len(f),
                   infeasible=int((~np.isfinite(f.cost)).sum()), groups=len(gm), mismatch=int(gm.mismatch.sum()),
                   fraction=round(float(gm.mismatch.mean()), 4), papers_with_mismatch=int(gm[gm.mismatch].doi.nunique()),
                   gt5pct=int((gm.mismatch & (gm.regret > 0.05)).sum()),
                   gt10pct=int((gm.mismatch & (gm.regret > 0.10)).sum()),
                   regret_max=round(float(gm.regret.max()), 4))
        if prev is not None:
            row["new_mismatch"] = len(mism - prev[0])
            row["lost_mismatch"] = len(prev[0] - mism)
            row["groups_added"] = len(set(gm.group) - prev[1])
            row["groups_removed"] = len(prev[1] - set(gm.group))
        out.append(row)
        gm["step"], gm["mode"] = name, mode
        per.append(gm)
        prev = (mism, set(gm.group))
    steps_df = pd.DataFrame(out)
    steps_df.to_csv(HERE / "decomposition_steps.csv", index=False)
    pd.concat(per).to_csv(HERE / "decomposition_groups.csv", index=False, float_format="%.6g")
    (HERE / "decomposition.json").write_text(json.dumps(dict(lock_commit=LOCK, steps=out), indent=1) + "\n",
                                             encoding="utf-8")
    pd.set_option("display.width", 250)
    print(steps_df.to_string(index=False))


if __name__ == "__main__":
    main()
