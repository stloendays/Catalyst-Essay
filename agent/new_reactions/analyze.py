"""Same analysis as the NH3 / methanol chains, applied to the new reactions.

1. Plant cost of every usable record (plant_models.py) and of the industrial reference catalyst.
2. Paper ranking vs plant-cost ranking inside each comparison group (same paper, same pressure and feed):
   is the catalyst/condition that the lab metric puts first also the cheapest in the plant? Regret of the lab choice.
   A disagreement is classed 'catalyst' (different catalyst) or 'temperature' (same catalyst, other T).
3. Bottleneck: cost split into parts; one-at-a-time attribution of each record's cost gap to the reference
   (selectivity, per-pass conversion, productivity, stability, catalyst metal) -> which catalyst property carries
   the plant cost; elasticities at the reference point.
4. Backward design: the property value a lab catalyst would need to reach the reference cost.
Writes results/<rxn>_*.csv and results/<rxn>_summary.json.
"""
from __future__ import annotations

import copy
import csv
import json
import math
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

from scipy.optimize import brentq

import plant_models as pm

HERE = Path(__file__).resolve().parent
OUT = HERE / "results"
OUT.mkdir(exist_ok=True)


def load(rxn):
    rows = list(csv.DictReader(open(HERE / "data" / f"{rxn}_records.csv", encoding="utf-8")))
    out = []
    for r in rows:
        f = {k: (float(r[k]) if r[k] not in ("", "None") else None)
             for k in ("T_K", "P_bar", "y_key", "y_h2", "X", "S", "r_kg_kg_h", "t_cycle_h", "kd_h")}
        if not (f["T_K"] and f["X"] and f["S"] and f["r_kg_kg_h"]) or f["X"] <= 0 or f["S"] <= 0:
            continue
        if f["S"] > 1.0 or f["X"] > 1.0:
            continue
        comps = [dict(element=e, wt_pct=w) for e, w in json.loads(r["elements"])]
        out.append(dict(r, **f, components=comps, rec=dict(T_K=f["T_K"], X=f["X"], S=f["S"], r=f["r_kg_kg_h"],
                                                            components=comps, t_cycle_h=f["t_cycle_h"],
                                                            P_bar=f["P_bar"], y_key=f["y_key"], y_h2=f["y_h2"])))
    return out


def cost(rxn, rec, detail=False, prm=None):
    return (pm.pdh_cost if rxn == "pdh" else pm.ch4_cost)(rec, prm=prm, detail=detail)


def reference(rxn):
    return pm.reference_record(rxn)


def groups(rows):
    g = defaultdict(list)
    for r in rows:
        key = (r["paper"], round(r["P_bar"], 1), round(r["y_key"] or 0, 2))
        g[key].append(r)
    return {k: v for k, v in g.items() if len({(x["catalyst"], round(x["T_K"])) for x in v}) >= 2}


def lab_metrics(rxn):
    # the metrics papers rank on: activity (productivity) and conversion; selectivity as a third
    return {"productivity": lambda r: r["r_kg_kg_h"], "conversion": lambda r: r["X"], "selectivity": lambda r: r["S"]}


def attribution(rxn, rec, ref):
    """Swap one property at a time from the reference to the record's value; cost change of each swap."""
    base = cost(rxn, ref)
    out = {}
    props = {"selectivity": ("S",), "activity": ("X", "r", "xeq_lab"), "temperature": ("T_K",),
             "metal": ("components",)}
    if rxn == "pdh":
        props["stability"] = ("t_cycle_h",)
    for name, keys in props.items():
        x = copy.deepcopy(ref)
        for k in keys:
            if k == "t_cycle_h" and rec.get(k) is None:
                continue
            if k == "xeq_lab":
                x[k] = pm.lab_xeq(rxn, rec)
                continue
            x[k] = rec[k]
        out[name] = cost(rxn, x) - base
    return out


def run(rxn):
    rows = load(rxn)
    ref = reference(rxn)
    c_ref, d_ref = cost(rxn, ref, detail=True)
    recs = []
    for r in rows:
        r["rec"]["xeq_lab"] = pm.lab_xeq(rxn, r["rec"])
        c, d = cost(rxn, r["rec"], detail=True)
        r.update(cost=c, Xp=d["Xp"], Xeq_plant=d["Xeq"], Xeq_lab=d["Xeq_lab"], r_plant=d["r_plant"],
                 **{"part_" + k: v for k, v in d["parts"].items()})
        r.update({"attr_" + k: v for k, v in attribution(rxn, r["rec"], ref).items()})
        recs.append(r)
    keys = [k for k in recs[0] if k not in ("rec", "components")]
    with open(OUT / f"{rxn}_costs.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, keys)
        w.writeheader()
        w.writerows({k: r[k] for k in keys} for r in recs)

    # 2. ranking within groups
    G = groups(recs)
    grows, summ = [], defaultdict(lambda: defaultdict(int))
    for key, members in G.items():
        best = min(members, key=lambda r: r["cost"])
        for mname, fn in lab_metrics(rxn).items():
            top = max(members, key=fn)
            differ = top is not best and abs(top["cost"] - best["cost"]) > 1e-9
            kind = "" if not differ else ("catalyst" if top["catalyst"] != best["catalyst"] else "temperature")
            regret = (top["cost"] - best["cost"]) / best["cost"]
            grows.append(dict(paper=key[0], P_bar=key[1], y_key=key[2], n=len(members), metric=mname,
                              lab_top=f"{top['catalyst']} @ {top['T_K'] - 273.15:.0f} C",
                              plant_best=f"{best['catalyst']} @ {best['T_K'] - 273.15:.0f} C",
                              differ=differ, kind=kind, regret=regret))
            s = summ[mname]
            s["groups"] += 1
            s["differ"] += differ
            s["differ_catalyst"] += kind == "catalyst"
            s["differ_temperature"] += kind == "temperature"
            s["regret_gt_1pct"] += differ and regret > 0.01
            s["regret_gt_5pct"] += differ and regret > 0.05
            s["max_regret_pct"] = max(s["max_regret_pct"], round(100 * regret, 2))
    if grows:
        with open(OUT / f"{rxn}_groups.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, list(grows[0]))
            w.writeheader()
            w.writerows(grows)

    # 3. bottleneck
    costs = sorted(r["cost"] for r in recs)
    attr = {k: [r["attr_" + k] for r in recs] for k in recs[0] if False}
    attr = {k[5:]: [r[k] for r in recs] for k in recs[0] if k.startswith("attr_")}
    gap = [r["cost"] - c_ref for r in recs]
    share = {}
    tot_abs = sum(sum(abs(v) for v in vals) for vals in attr.values())
    for k, vals in attr.items():
        share[k] = dict(median=st.median(vals), mean_abs=st.mean(abs(v) for v in vals),
                        share_of_abs_gap=sum(abs(v) for v in vals) / tot_abs if tot_abs else 0)
    elastic = {}
    for k, step in (("S", 0.01), ("X", 0.05), ("r", 0.10), ("t_cycle_h", 0.10)):
        if ref.get(k) is None:
            continue
        x = copy.deepcopy(ref)
        x[k] = ref[k] * (1 + step) if k != "S" else min(ref[k] + step, 1.0)
        elastic[k] = dict(step=step, cost_change=cost(rxn, x) - c_ref)
    # 4. backward design: selectivity needed to reach the reference cost at each record's own other properties
    need = []
    for r in recs:
        def f(S):
            x = dict(r["rec"], S=S)
            return cost(rxn, x) - c_ref
        try:
            s_need = brentq(f, 0.30, 1.0) if f(1.0) < 0 < f(0.30) else (None if f(1.0) > 0 else 0.30)
        except ValueError:
            s_need = None
        need.append(s_need)
    beat = sum(1 for r in recs if r["cost"] < c_ref)
    summary = dict(
        reaction=rxn, n_records_usable=len(recs), n_papers=len({r["paper"] for r in recs}),
        n_productivity_derived=sum(1 for r in recs if r["r_src"] == "derived"),
        reference=dict(cost=c_ref, parts=d_ref["parts"], Xp=d_ref["Xp"]),
        cost_quantiles=dict(min=costs[0], p25=costs[len(costs) // 4], median=st.median(costs), max=costs[-1]),
        n_below_reference=beat,
        ranking={k: dict(v) for k, v in summ.items()}, n_groups=len(G),
        attribution=share, elasticities_at_reference=elastic,
        selectivity_needed=dict(n_reachable=sum(1 for s in need if s), n_unreachable_even_S1=sum(1 for s in need if s is None)),
    )
    if rxn == "pdh":
        summary["records_X_below_half_plant_Xp"] = sum(1 for r in recs if r["X"] < 0.5 * r["Xp"])
    (OUT / f"{rxn}_summary.json").write_text(json.dumps(summary, indent=1, default=lambda o: float(o)), encoding="utf-8")
    print(json.dumps(summary, default=lambda v: round(float(v), 4))[:300])
    return summary


if __name__ == "__main__":
    for rxn in sys.argv[1:] or ["pdh", "ch4"]:
        run(rxn)
