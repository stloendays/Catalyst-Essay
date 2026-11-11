"""Evaluation side (never visible to the agent): compare the independent AI-built models of one reaction with
(1) the held-out published TEA / plant data (holdout/<rxn>.json "targets", preregistered tolerances),
(2) each other on a common record set (the PR #122 usable records of this reaction, converted to the contract input),
(3) the hand-built reference model (plant_framework + configs/<rxn>_ours.json) on the same records.
Writes evaluation/<rxn>_builds.json and prints the preregistered verdicts.
Usage: python evaluate_builds.py <rxn> <run_dir> [<run_dir> ...]
"""
import importlib.util
import json
import math
import statistics as st
import sys
import time
from itertools import combinations
from pathlib import Path

from scipy.stats import spearmanr

HERE = Path(__file__).resolve().parent
NR = HERE.parent
sys.path.insert(0, str(NR))
import analyze as an  # noqa: E402
import plant_framework as fw  # noqa: E402


def load_model(run):
    spec = importlib.util.spec_from_file_location(f"m{time.time_ns()}", Path(run) / "model.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def common_records(rx):
    out = []
    for r in an.load(rx):
        out.append(dict(key=f"{r['paper']}#{r['idx']}", catalyst=r["catalyst"], T_K=r["T_K"], P_bar=r["P_bar"], X=r["X"], S=r["S"],
                        r=r["r_kg_kg_h"], y_key=r["y_key"], y_cofeed=r["y_h2"], t_cycle_h=r["t_cycle_h"],
                        components=[[c["element"], c["wt_pct"]] for c in r["components"]], rec=r["rec"]))
    return out


def within(v, target, tol):
    lo, hi = (target * (1 + tol[0]), target * (1 + tol[1])) if isinstance(tol, list) else (target * (1 - tol), target * (1 + tol))
    return lo <= v <= hi


def main(rx, runs):
    hold = json.loads((HERE / "holdout" / f"{rx}.json").read_text(encoding="utf-8"))
    recs = common_records(rx)
    cfg = fw.load(rx, "ours")
    hand = {x["key"]: fw.cost(cfg, dict(x["rec"], xeq_lab=fw.lab_xeq(cfg, x["rec"]))) for x in recs}
    builds = {}
    for run in runs:
        m = load_model(run)
        ref = m.reference()
        costs = {}
        for x in recs:
            try:
                costs[x["key"]] = m.plant_cost({k: v for k, v in x.items() if k not in ("key", "rec")})["cost_usd_per_t"]
            except Exception:  # noqa: BLE001
                costs[x["key"]] = math.nan
        an_path = Path(run) / "analysis.json"
        a = json.loads(an_path.read_text(encoding="utf-8")) if an_path.exists() else {}
        ok = {k: v for k, v in costs.items() if math.isfinite(v)}
        cheapest = min(ok, key=ok.get) if ok else None
        b = ref["balances"]
        tea = {}
        for name, t in hold.get("targets", {}).items():
            got = {"feed_t_per_t": b.get("key_feed_t_per_t"), "energy_GJ_per_t": b.get("energy_GJ_per_t"),
                   "capex_usd_per_t_y": (b.get("capex_usd") or 0) / max(b.get("capacity_t_per_y") or 1, 1),
                   "feed_share": ref["parts"].get("feed", 0) / ref["cost_usd_per_t"],
                   "capital_share": ref["parts"].get("capital", 0) / ref["cost_usd_per_t"],
                   "total_cost": ref["cost_usd_per_t"]}.get(t["quantity"])
            tea[name] = dict(model=got, target=t["value"], tol=t["tol"], within=None if got is None else within(got, t["value"], t["tol"]),
                             source=t["source"])
        n_in = sum(1 for v in tea.values() if v["within"])
        far = [k for k, v in tea.items() if v["model"] is not None and not within(v["model"], v["target"], [x * 2 for x in v["tol"]] if isinstance(v["tol"], list) else v["tol"] * 2)]
        builds[str(run)] = dict(reference_cost=ref["cost_usd_per_t"], parts=ref["parts"], largest=max(ref["parts"], key=ref["parts"].get),
                                cheapest_common=cheapest, cheapest_catalyst=next((x["catalyst"] for x in recs if x["key"] == cheapest), None),
                                n_costed=len(ok), top_attribution=max(a.get("attribution_share", {"?": 0}), key=a.get("attribution_share", {"?": 0}).get),
                                spearman_vs_hand=spearmanr([ok[k] for k in ok], [hand[k] for k in ok]).statistic if len(ok) > 2 else None,
                                tea=tea, tea_within=n_in, tea_n=len(tea), tea_far=far,
                                tea_pass=(n_in >= hold["pass_rule"]["min_within"] and not far) if tea else None,
                                # pass_rule text: pass = all within; partial = two within and none beyond twice the tolerance
                                tea_verdict=(None if not tea else "pass" if n_in == len(tea) else
                                             "partial" if n_in == len(tea) - 1 and not far else "fail"),
                                attribution_share=a.get("attribution_share"),
                                costs=costs)
    keys = list(builds)
    pair = {}
    for a_, b_ in combinations(keys, 2):
        k = [x for x in builds[a_]["costs"] if math.isfinite(builds[a_]["costs"][x]) and math.isfinite(builds[b_]["costs"][x])]
        pair[f"{Path(a_).name} vs {Path(b_).name}"] = spearmanr([builds[a_]["costs"][x] for x in k], [builds[b_]["costs"][x] for x in k]).statistic
    refs = [builds[k]["reference_cost"] for k in keys]

    def verdict(vals):
        c = {v: vals.count(v) for v in vals}
        top = max(c.values())
        return "robust (all agree)" if top == len(vals) else ("majority" if top > len(vals) / 2 else "model-dependent")
    concl = {
        "largest cost item": verdict([builds[k]["largest"] for k in keys]),
        "controlling catalyst property": verdict([builds[k]["top_attribution"] for k in keys]),
        "cheapest catalyst (common records)": verdict([builds[k]["cheapest_catalyst"] for k in keys]),
        "reference cost spread max/min-1": round(max(refs) / min(refs) - 1, 3) if refs else None,
        "pairwise Spearman (common records)": {k: round(v, 3) for k, v in pair.items()},
    }
    median_build = sorted(keys, key=lambda k: builds[k]["reference_cost"])[len(keys) // 2]
    out = dict(rxn=rx, builds={k: {kk: vv for kk, vv in v.items() if kk != "costs"} for k, v in builds.items()},
               agreement=concl, primary_build_median_reference=median_build, holdout_pass_rule=hold["pass_rule"])
    (HERE / "evaluation").mkdir(exist_ok=True)
    (HERE / "evaluation" / f"{rx}_builds.json").write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")
    print(json.dumps(out, indent=1, default=str)[:6000])


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
