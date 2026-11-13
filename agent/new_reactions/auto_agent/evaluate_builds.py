"""Evaluation side (never visible to the agent): compare the independent AI-built models of one reaction with
(1) the held-out published TEA / plant data (holdout/<rxn>.json "targets", preregistered tolerances),
(2) each other on a common record set (the PR #122 usable records of this reaction, converted to the contract input),
(3) the hand-built reference model (plant_framework + configs/<rxn>_ours.json) on the same records.
Writes evaluation/<rxn>_builds.json and prints the preregistered verdicts.
Usage: python evaluate_builds.py <rxn> <run_dir> [<run_dir> ...]
"""
import importlib.util
import csv
import json
import math
import statistics as st
import sys
import time
from itertools import combinations
from pathlib import Path

from scipy.stats import spearmanr
import numpy as np

HERE = Path(__file__).resolve().parent
NR = HERE.parent
sys.path.insert(0, str(NR))
import analyze as an  # noqa: E402
import plant_framework as fw  # noqa: E402


def load_model(run):
    spec = importlib.util.spec_from_file_location(f"m{time.time_ns()}", Path(run) / "model.py")
    m = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(Path(run)))
    prior = sys.modules.pop("atomic", None)
    try:
        if (Path(run) / "atomic.py").exists():
            from atomic_layer import load_atomic
            sys.modules["atomic"] = load_atomic(Path(run))
        exec(compile((Path(run)/"model.py").read_text(encoding="utf-8"), str(Path(run)/"model.py"), "exec"), m.__dict__)
    finally:
        sys.path.pop(0)
        sys.modules.pop("atomic", None)
        if prior is not None:
            sys.modules["atomic"] = prior
    return m


def common_records(rx, runs=None):
    out = []
    try:
        loaded = an.load(rx)
    except (FileNotFoundError, KeyError):
        if not runs:
            raise
        sets = []
        for run in runs:
            mapped = {}
            with (Path(run) / "records.csv").open(encoding="utf-8") as fh:
                for r in csv.DictReader(fh):
                    if str(r.get("usable", "True")).lower() not in ("true", "1"):
                        continue
                    key = (r["paper"], "".join(r["catalyst"].lower().split()), round(float(r["T_K"])))
                    def num(k, fallback=None):
                        v = r.get(k, fallback)
                        return None if v in (None, "", "None") else float(v)
                    mapped[key] = dict(key="|".join(map(str, key)), paper=r["paper"], idx=int(r.get("idx", 0)),
                        catalyst=r["catalyst"], T_K=num("T_K"), P_bar=num("P_bar"), X=num("X"), S=num("S"),
                        r=num("r", r.get("r_kg_kg_h")), y_key=num("y_key"), y_cofeed=num("y_h2", r.get("y_cofeed")),
                        t_cycle_h=num("t_cycle_h"), components=json.loads(r.get("elements", r.get("components", "[]"))))
            sets.append(mapped)
        shared = set.intersection(*(set(x) for x in sets))
        return [sets[0][k] for k in sorted(shared)]
    for r in loaded:
        out.append(dict(key=f"{r['paper']}#{r['idx']}", catalyst=r["catalyst"], T_K=r["T_K"], P_bar=r["P_bar"], X=r["X"], S=r["S"],
                        r=r["r_kg_kg_h"], y_key=r["y_key"], y_cofeed=r["y_h2"], t_cycle_h=r["t_cycle_h"],
                        components=[[c["element"], c["wt_pct"]] for c in r["components"]], rec=r["rec"]))
    return out


def within(v, target, tol):
    lo, hi = (target * (1 + tol[0]), target * (1 + tol[1])) if isinstance(tol, list) else (target * (1 - tol), target * (1 + tol))
    return lo <= v <= hi


def scaled_target(target, capacity):
    """Log-log interpolation; end slopes extrapolate within 0.5x--2x end values."""
    if "scale_curve" not in target:
        return target["value"]
    points = sorted((float(c), float(v)) for c, v in target["scale_curve"])
    if (len(points) < 2 or any(not math.isfinite(x) or x <= 0 for pt in points for x in pt)
            or any(a[0] == b[0] for a, b in zip(points, points[1:]))):
        raise ValueError("scale_curve requires at least two distinct positive capacities and positive finite values")
    if capacity is None or not math.isfinite(capacity) or capacity <= 0:
        raise ValueError("scale_curve requires positive finite balances.capacity_t_per_y")
    i = next((i for i in range(len(points)-1) if capacity <= points[i+1][0]), len(points)-2)
    (c0, v0), (c1, v1) = points[i:i+2]
    log_value = math.log(v0) + math.log(capacity/c0) * math.log(v1/v0) / math.log(c1/c0)
    if capacity < points[0][0] or capacity > points[-1][0]:
        end = points[0][1] if capacity < points[0][0] else points[-1][1]
        log_value = min(math.log(2*end), max(math.log(.5*end), log_value))
    return math.exp(log_value)


def evaluate_targets(ref, targets, run=None):
    """Read held-out quantities from the reference output, including boundary feeds."""
    if not targets:
        return {}
    b = ref["balances"]
    tea = {}
    for name, t in targets.items():
        quantity = t["quantity"]
        if quantity == "atomic_optimum_D":
            got = None
            if run:
                if "conditions" in t:
                    from atomic_layer import load_atomic, descriptor_grid, optimum
                    a = load_atomic(Path(run))
                    got = optimum(a, descriptor_grid(a), t["conditions"])[0]["D"]
                elif (Path(run) / "three_optima.json").exists():
                    got = json.loads((Path(run) / "three_optima.json").read_text(encoding="utf-8"))["atomic_optimum"]["D"]
        elif quantity == "atomic_opt_weaker_than_ref_eV":
            got = None
            if run and "conditions" in t:
                from atomic_layer import load_atomic, descriptor_grid, optimum
                a = load_atomic(Path(run))
                d_opt = optimum(a, descriptor_grid(a), t["conditions"])[0]["D"]
                d_ref = a.DESCRIPTORS.get(t["ref_metal"], {}).get("value")
                sign = {"more_negative": 1.0, "more_positive": -1.0}.get(a.ATOMIC.get("stronger_binding"))
                if d_ref is not None and sign is not None:
                    got = sign * (float(d_opt) - float(d_ref))
        elif quantity == "nh3_equiv_t_per_t":   # key feed + purchased furnace fuel as key-feed LHV equivalent
            units = ref.get("physics", {}).get("units", [])
            feed = ref.get("physics", {}).get("boundary", {}).get("in_t_per_t", {}).get(t.get("species", "NH3"))
            got = None if feed is None else feed + sum(u.get("purchased_energy_GJ_per_t", 0) for u in units
                                                      if u.get("type") == "furnace") / t.get("fuel_lhv_GJ_per_t", 18.6)
        elif quantity == "fired_plus_power_GJ_per_t":
            units = ref.get("physics", {}).get("units", [])
            got = (b.get("energy_GJ_per_t") or 0) + sum(u.get("internal_fuel_GJ_per_t", 0) for u in units)
        elif quantity.startswith("boundary_in:"):
            got = ref.get("physics", {}).get("boundary", {}).get("in_t_per_t", {}).get(quantity.split(":", 1)[1])
        else:
            got = {"feed_t_per_t": b.get("key_feed_t_per_t"), "energy_GJ_per_t": b.get("energy_GJ_per_t"),
                   "capex_usd_per_t_y": (b.get("capex_usd") or 0) / max(b.get("capacity_t_per_y") or 1, 1),
                   "feed_share": ref["parts"].get("feed", 0) / ref["cost_usd_per_t"],
                   "capital_share": ref["parts"].get("capital", 0) / ref["cost_usd_per_t"],
                   "total_cost": ref["cost_usd_per_t"]}.get(quantity)
        value = scaled_target(t, b.get("capacity_t_per_y"))
        tea[name] = dict(model=got, target=value, tol=t.get("tol"),
                         within=False if got is None else abs(got-value) <= t["tol_abs"] if "tol_abs" in t else within(got, value, t["tol"]), source=t["source"])
        if "tol_abs" in t:
            tea[name]["tol_abs"] = t["tol_abs"]
        if got is None:
            tea[name]["reason"] = "not reported"
        if "scale_curve" in t:
            tea[name]["scaled_target"] = value
            tea[name]["scale_curve"] = t["scale_curve"]
    return tea


def full_harness_decomposition(condition, grid, ts_shift_eV=None):
    """Seven-step mean-field MKM using the harness scaling energies (report only).

    The workbook supplies TS fits for N2 dissociation and all three N-H steps,
    but NO adsorption TS fits. Complete the three adsorption/desorption steps
    with a shared TS at max(reactant, product), kBT/h. This explicit barrierless
    closure is an assumption, not additional DFT evidence. All six adsorbates
    occupy one site. Solve log(theta_i/theta_*) plus log(overall extent/s).
    Each step is oriented toward decomposition and its positive net flux is
    constrained to the stoichiometric multiple of one common flux. Equations
    log(r_forward)=logaddexp(log(r_reverse),log(nu*J)) avoid subtracting large
    near-equilibrium gross rates. No fixed rate-determining step is imposed.
    """
    from scipy.optimize import least_squares
    from scipy.special import logsumexp
    names = ['NH3', 'NH2', 'NH', 'N', 'N2', 'H', '*']
    # forward reactants/products and multiplicity per 2NH3 -> N2+3H2 extent
    definitions = [({'NH3_g':1,'*':1},{'NH3':1},None,2),
                   ({'NH3':1,'*':1},{'NH2':1,'H':1},'NH2-H',2),
                   ({'NH2':1,'*':1},{'NH':1,'H':1},'NH-H',2),
                   ({'NH':1,'*':1},{'N':1,'H':1},'N-H',2),
                   ({'N':2},{'N2':1,'*':1},'N-N',1),
                   ({'N2':1},{'N2_g':1,'*':1},None,1),
                   ({'H':2},{'H2_g':1,'*':2},None,3)]
    gaslog = {'NH3_g':math.log(condition.pNH3), 'N2_g':math.log(condition.pN2), 'H2_g':math.log(condition.pH2)}
    driving = -2*condition.G_NH3_g_form+condition.kT*(gaslog['N2_g']+3*gaslog['H2_g']-2*gaslog['NH3_g'])
    if driving >= 0:
        raise ValueError('conditions do not support positive net decomposition')
    old_solution = None
    rows = []
    for descriptor in grid:
        g = {s:a*float(descriptor)+b for s,(a,b) in condition.g_linear.items()}
        g.update({'*':0.,'N2_g':0.,'H2_g':0.,'NH3_g':condition.G_NH3_g_form})
        constants=[]
        for step_index,(react,prod,ts,nu) in enumerate(definitions):
            er=sum(g[s]*v for s,v in react.items());ep=sum(g[s]*v for s,v in prod.items())
            top=max(er,ep,g[ts]) if ts else max(er,ep)
            top += (ts_shift_eV or {}).get(ts or f'adsorption_{step_index}', 0.)
            constants.append((math.log(condition.pref)-(top-er)/condition.kT,
                              math.log(condition.pref)-(top-ep)/condition.kT))
        def residual(z):
            ls=logsumexp(np.r_[z[:6],0.])
            logs=dict(zip(names,np.r_[z[:6],0.]-ls));logs.update(gaslog)
            result=[]
            for (react,prod,_,nu),(lf,lr) in zip(definitions,constants):
                forward=lf+sum(v*logs[s] for s,v in react.items())
                reverse=lr+sum(v*logs[s] for s,v in prod.items())
                result.append(forward-np.logaddexp(reverse,z[6]+math.log(nu)))
            return np.asarray(result)
        best=None
        # Continuation and two physically distinct surface seeds.
        for seed in ([old_solution] if old_solution is not None else []) + [np.r_[np.zeros(6),-15.],np.r_[np.full(6,-8.),-30.]]:
            fit=least_squares(residual,np.clip(seed,-690,690),bounds=(-700,700),
                              xtol=1e-12,ftol=1e-12,gtol=1e-12,max_nfev=800)
            err=float(np.linalg.norm(residual(fit.x),np.inf))
            if best is None or err<best[0]:
                best=(err,fit.x)
            if err<1e-8:
                break
        err,z=best
        if err>1e-7:
            raise RuntimeError(f'full MKM not converged at E_N={descriptor}: log-flux residual={err}')
        old_solution=z
        ls=logsumexp(np.r_[z[:6],0.])
        cover=dict(zip(names,map(float,np.exp(np.r_[z[:6],0.]-ls))))
        rows.append(dict(D=float(descriptor),TOF_extent_per_site_s=math.exp(float(z[6])),
                         log10_TOF=float(z[6]/math.log(10)),coverages=cover,log_flux_residual=err))
    return dict(method='full_mkm_barrierless_adsorption',argmax_D=rows[int(np.argmax([r['log10_TOF'] for r in rows]))]['D'],
                max_log_flux_residual=max(r['log_flux_residual'] for r in rows),curve=rows,
                adsorption_assumption='missing adsorption TS supplied by max(reactant,product), common kBT/h; not a uniquely specified full harness MKM')


def qe_reverse_logtof(c, d):
    g = {s: aa*d+bb for s, (aa, bb) in c.g_linear.items()}
    exp = c._exp
    qn = exp(-g["N2"]/c.kT)*c.pN2
    qh = exp(-g["H"]/c.kT)*math.sqrt(c.pH2)
    qa = exp(-(g["NH3"]-c.G_NH3_g_form)/c.kT)*c.pNH3
    def ks(ts, rs, ps):
        top = max(g[ts], rs, ps)
        return c.pref*exp(-(top-rs)/c.kT), c.pref*exp(-(top-ps)/c.kT)
    f2, r2 = ks("N-N", g["N2"], 2*g["N"])
    f4, r4 = ks("N-H", g["N"]+g["H"], g["NH"])
    f5, r5 = ks("NH-H", g["NH"]+g["H"], g["NH2"])
    f6, r6 = ks("NH2-H", g["NH2"]+g["H"], g["NH3"])
    if qh <= 0:
        raise ValueError("reverse reduction requires positive H2 seed pressure")
    def ratios(j):
        z = (j+r6*qa)/(f6*qh)
        y = (j+r5*z)/(f5*qh)
        x = (j+r4*y)/(f4*qh)
        return x, y, z
    # Ratios are affine in j: find the first physically admissible lower bound.
    r0 = np.array(ratios(0))
    # Analytic affine slopes; subtracting ratios(1)-ratios(0)
    # loses all precision when equilibrium ratios are very large.
    az = 1/(f6*qh)
    ay = (1+r5*az)/(f5*qh)
    ax = (1+r4*ay)/(f4*qh)
    if 2*(f2*qn-r2*r0[0]**2) >= 0:
        return -300.
    # Solve for x=theta_N/theta_* rather than nearly cancelling
    # j at its positivity bound. 2*ax*r2*x^2+x-(b+2*ax*f2*qn)=0.
    const = r0[0]+2*ax*f2*qn
    coeff = 2*ax*r2
    x = 2*const/(1+math.sqrt(1+4*coeff*const))
    j = (x-r0[0])/ax if abs(x-r0[0])>1e-8*(x+r0[0]) else 2*(f2*qn-r2*x*x)
    # Recover downstream ratios by addition on the reverse branch.
    y = (f4*qh*x-j)/r4
    z = (f5*qh*y-j)/r5
    vacancy = 1/(1+qn+qh+qa+x+y+z)
    # synthesis j counts NH3; one decomposition extent consumes two NH3.
    return math.log10(max(-j*vacancy**2/2, 1e-300))


def hidden_atomic_reference(run, hold):
    """Report-only: signed reverse branch from harness internals, never agent-visible.

Condition.logtof clips negative synthesis rates to -300. It cannot be negated
to obtain decomposition. Solve the same quasi-equilibrium reduction on its
physical reverse branch with nonnegative intermediate ratios instead.
"""
    try:
        from atomic_layer import load_atomic, descriptor_grid
        root = NR.parents[1] / "provenance" / "nh3_final_1_2" / "source_harness"
        spec = importlib.util.spec_from_file_location("hidden_nh3_reference", root / "harness_core.py")
        hc = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = hc
        spec.loader.exec_module(hc)
        books = list(root.rglob("*.xlsx"))
        if not books:
            return dict(status="unavailable", reason="source_harness activity workbook absent; Condition.logtof clips negative synthesis flux, so it cannot directly give decomposition")
        src = hc.parse_activity_workbook(books[0])
        ctx = hc.KineticContext(src["fits"], src["median_freqs"], src["gasrec"], "gillespie_beattie", "ideal")
        a = load_atomic(Path(run))
        grid = descriptor_grid(a)
        import yaml
        cfg = yaml.safe_load((root / "configs" / "nh3_final_1_2.yaml").read_text(encoding="utf-8"))
        hg = cfg["numerics"]["descriptor_grid_eV"]
        lo, hi = max(float(grid[0]), float(hg["start"])), min(float(grid[-1]), float(hg["stop"]))
        if lo >= hi:
            raise ValueError("agent and harness descriptor ranges do not overlap")
        grid = np.linspace(lo, hi, 201)
        conds = [x["conditions"] for x in hold.get("targets", {}).values() if x.get("quantity") in ("atomic_optimum_D", "atomic_opt_weaker_than_ref_eV") and "conditions" in x]
        if not conds:
            conds = [json.loads((Path(run)/"three_optima.json").read_text(encoding="utf-8"))["atomic_optimum"]["conditions"]]
        conds = list({json.dumps(c, sort_keys=True):c for c in conds}.values())
        results = []
        for cond in conds:
            t, p = cond["T_K"], cond["p_bar"]
            c = ctx.condition(t, p.get("N2", 0), p.get("H2", 0), p.get("NH3", 0))
            vals = [qe_reverse_logtof(c, float(d)) for d in grid]
            av = [a.logtof(float(d), t, p) for d in grid]
            qe = dict(conditions=cond, argmax_D=float(grid[int(np.argmax(vals))]),
                spearman=float(spearmanr(av, vals).statistic), descriptor_range=[float(grid[0]), float(grid[-1])],
                method="qe_reverse", curve=[dict(D=float(d),log10_TOF=float(v)) for d,v in zip(grid,vals)])
            try:
                full = full_harness_decomposition(c, grid)
                full['spearman'] = float(spearmanr(av,[r['log10_TOF'] for r in full['curve']]).statistic)
            except Exception as exc:
                full = dict(status='unavailable', reason=f'{type(exc).__name__}: {exc}')
            # The adsorption TS are absent from the harness. A completed full MKM
            # is a sensitivity check, not sufficient evidence to replace QE.
            results.append(dict(conditions=cond,argmax_D=qe['argmax_D'],method='qe_reverse',
                                spearman=qe['spearman'],descriptor_range=qe['descriptor_range'],
                                qe_reverse=qe,full_mkm=full,
                                selection_reason='retain QE primary: full MKM requires unprovided adsorption kinetics; report both'))
        return dict(status="computed_report_only", results=results)
    except Exception as exc:
        return dict(status="unavailable", reason=f"{type(exc).__name__}: {exc}; no forward-clipped logtof used as decomposition proxy")


def main(rx, runs, holdout_path=None, output_dir=None):
    hold = json.loads((Path(holdout_path) if holdout_path else HERE / "holdout" / f"{rx}.json").read_text(encoding="utf-8"))
    recs = common_records(rx, runs)
    try:
        cfg = fw.load(rx, "ours")
        hand = {x["key"]: fw.cost(cfg, dict(x["rec"], xeq_lab=fw.lab_xeq(cfg, x["rec"]))) for x in recs if "rec" in x}
    except (FileNotFoundError, KeyError):
        hand = {}
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
        allt = evaluate_targets(ref, hold.get("targets", {}), run)
        tea = {k: v for k, v in allt.items() if not hold["targets"][k].get("group")}
        grouped = {k: v for k, v in allt.items() if hold["targets"][k].get("group")}
        n_in = sum(1 for v in tea.values() if v["within"])
        far = [k for k, v in tea.items() if v["model"] is not None and
               (abs(v["model"]-v["target"]) > 2*v["tol_abs"] if "tol_abs" in v else
                not within(v["model"], v["target"], [x * 2 for x in v["tol"]] if isinstance(v["tol"], list) else v["tol"] * 2))]
        builds[str(run)] = dict(reference_cost=ref["cost_usd_per_t"], parts=ref["parts"], largest=max(ref["parts"], key=ref["parts"].get),
                                cheapest_common=cheapest, cheapest_catalyst=next((x["catalyst"] for x in recs if x["key"] == cheapest), None),
                                n_costed=len(ok), top_attribution=max(a.get("attribution_share", {"?": 0}), key=a.get("attribution_share", {"?": 0}).get),
                                spearman_vs_hand=spearmanr([ok[k] for k in ok if k in hand], [hand[k] for k in ok if k in hand]).statistic if len(set(ok) & set(hand)) > 2 else None,
                                tea=tea, tea_within=n_in, tea_n=len(tea), tea_far=far,
                                tea_pass=(n_in >= hold["pass_rule"]["min_within"] and not far) if tea else None,
                                # pass_rule text generalized: all within / all but one within, none beyond twice tolerance
                                tea_verdict=(None if not tea else "pass" if n_in == len(tea) else
                                             "partial" if n_in == len(tea) - 1 and not far else "fail"),
                                group_targets=grouped,
                                attribution_share=a.get("attribution_share"),
                                costs=costs)
        if hold.get("hidden_reference", {}).get("atomic") == "nh3_harness_decomposition":
            builds[str(run)]["hidden_atomic_reference"] = hidden_atomic_reference(run, hold)
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
    out["common_record_count"] = len(recs)
    dest = Path(output_dir) if output_dir else HERE / "evaluation"
    dest.mkdir(exist_ok=True, parents=True)
    (dest / f"{rx}_builds.json").write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")
    print(json.dumps(out, indent=1, default=str)[:6000])
    return out


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
