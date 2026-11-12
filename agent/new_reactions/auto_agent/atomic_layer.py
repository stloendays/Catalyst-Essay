"""Reaction-independent validation and atom -> lab -> plant analysis.

All descriptor/scaling/site inputs come from the run's atomic.py. No hidden
reference is imported here. logtof is log10 forward flux; net_tof is signed.
"""
import importlib.util
import json
import math
import sys
import time
from itertools import combinations
import numpy as np
from scipy.optimize import brentq

try:
    from .physics_gate import check_physics, species_thermo, R
except ImportError:
    from physics_gate import check_physics, species_thermo, R


def load_atomic(ws):
    spec = importlib.util.spec_from_file_location(f"atomic_{time.time_ns()}", ws / "atomic.py")
    m = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(ws))
    try:
        exec(compile((ws / "atomic.py").read_text(encoding="utf-8"), str(ws / "atomic.py"), "exec"), m.__dict__)
    finally:
        sys.path.pop(0)
    return m


def descriptor_grid(a):
    bounds = a.ATOMIC.get("descriptor_range")
    if bounds is None:
        bounds = [min(x["value"] for x in a.DESCRIPTORS.values()), max(x["value"] for x in a.DESCRIPTORS.values())]
    lo, hi = map(float, bounds)
    if not math.isfinite(lo+hi) or lo >= hi:
        raise ValueError("invalid descriptor range")
    return np.linspace(lo, hi, 201)


def conditions(ref):
    r = ref["physics"]["reactor"]
    return dict(T_K=r["T_K"], p_bar={s: y*r["P_bar"] for s, y in r["feed_mol_frac"].items()})


def optimum(a, grid, cond):
    vals = np.array([a.logtof(float(d), cond["T_K"], cond["p_bar"]) for d in grid], dtype=float)
    if not np.all(np.isfinite(vals)):
        raise ValueError("nonfinite atomic logtof")
    j = int(vals.argmax())
    return dict(D=float(grid[j]), logtof=float(vals[j]), grid_index=j, conditions=cond), vals


def check_atomic(h):
    failures = []
    try:
        a, m = load_atomic(h.ws), h._load_model()
        grid = descriptor_grid(a)
        ref = m.reference()
        cond = conditions(ref)
        if a.ATOMIC["overall"] != m.REACTION["nu"]:
            failures.append("overall reaction differs from plant model")
        for field in ("descriptor", "overall", "sources", "site_assumptions", "stronger_binding"):
            if not a.ATOMIC.get(field):
                failures.append("atomic contract missing " + field)
        if a.ATOMIC.get("stronger_binding") not in (None, "more_negative", "more_positive"):
            failures.append("stronger_binding must be 'more_negative' or 'more_positive'")
        for metal, entry in a.DESCRIPTORS.items():
            if not entry.get("source") or not entry.get("location") or not math.isfinite(float(entry["value"])):
                failures.append("descriptor provenance: " + metal)
        peak, _ = optimum(a, grid, cond)
        if a.ATOMIC.get("lab_conditions"):
            optimum(a, grid, a.ATOMIC["lab_conditions"])
        if peak["grid_index"] in (0, len(grid)-1) and not a.ATOMIC.get("no_volcano_reason", "").strip():
            failures.append("volcano: endpoint optimum needs no_volcano_reason")
        # Change a product activity to construct two compositions with dG/RT = +/- 2.
        nu = a.ATOMIC["overall"]
        t = cond["T_K"]
        dg0 = sum(v*(lambda hs: hs[0]-t*hs[1])(species_thermo(s, t)) for s, v in nu.items())
        p = {s: max(cond["p_bar"].get(s, 0), 1e-8) for s in nu}
        sp = next(s for s, v in nu.items() if v > 0)
        other = sum(v*math.log(p[s]) for s, v in nu.items() if s != sp)
        for sign in (-1, 1):
            logp = (sign*2-dg0/(R*t)-other)/nu[sp]
            if abs(logp) > 650:
                raise ValueError("equilibrium test pressure out of representable range")
            trial = dict(p, **{sp: math.exp(logp)})
            for d in (grid[0], peak["D"], grid[-1]):
                rate = float(a.net_tof(float(d), t, trial))
                lt = float(a.logtof(float(d), t, trial))
                if not math.isfinite(rate) or sign*rate >= 0:
                    failures.append("thermodynamic_direction: signed net_tof inconsistent with gas dG")
                if sign > 0 and lt > -290:
                    failures.append("thermodynamic_direction: positive forward flux beyond equilibrium")
        flow = json.loads((h.ws / "flowsheet.json").read_text(encoding="utf-8"))
        for d in (grid[0], peak["D"], grid[-1]):
            rec = a.record_from_descriptor(float(d))
            for field in ("T_K", "P_bar", "X", "S", "r", "y_key", "y_cofeed", "t_cycle_h", "components", "catalyst"):
                if field not in rec:
                    raise ValueError("record_from_descriptor missing " + field)
            if not math.isfinite(float(rec["r"])) or rec["r"] <= 0:
                raise ValueError("descriptor record invalid rate")
            if not math.isclose(float(a.rate_from_descriptor(float(d), rec)), rec["r"], rel_tol=1e-6):
                failures.append("atomic/plant activity mapping inconsistent")
            failures += ["plant_link: " + x for x in check_physics(m, m.plant_cost(rec), flow, basis=h._basis() if h._is_v3() else None)]
    except Exception as exc:
        failures.append(f"atomic: {type(exc).__name__}: {exc}")
    result = dict(passed=not failures, failures=failures, input_fingerprint=h._fingerprint())
    (h.ws / "atomic_check.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def effective_descriptor(a, grid, rec, metal):
    # Use EACH record's laboratory conditions and its own loading/site mapping.
    rates = np.array([float(a.rate_from_descriptor(float(d), rec)) for d in grid])
    if np.any(~np.isfinite(rates)) or np.any(rates <= 0):
        raise ValueError("laboratory mapping needs finite positive rate_from_descriptor")
    j = int(rates.argmax())
    target = float(rec["r"])
    left = a.DESCRIPTORS[metal]["value"] <= grid[j]
    lo, hi = (0, j) if left else (j, len(grid)-1)
    residual, status = 1., "matched"
    if target >= rates[j]:
        d, residual, status = grid[j], target/rates[j], "above_volcano" if target > rates[j] else "matched"
    else:
        crossings = [k for k in range(lo, hi) if (rates[k]-target)*(rates[k+1]-target) <= 0]
        if crossings:
            k = crossings[-1] if left else crossings[0]
            d = brentq(lambda x: a.rate_from_descriptor(x, rec)-target, grid[k], grid[k+1])
        else:
            k = lo + int(np.argmin(abs(rates[lo:hi+1]-target)))
            d, residual, status = grid[k], target/rates[k], "outside_declared_range"
    return dict(D_eff=float(d), residual_multiplier=float(residual), status=status, metal=metal,
                paper=rec.get("paper"), idx=rec.get("idx"), catalyst=rec["catalyst"])


def main_metal(a, rec):
    candidates = [(el, float(w or 0)) for el, w in rec["components"] if el in a.DESCRIPTORS]
    return max(candidates, key=lambda x: x[1])[0] if candidates else None


def three_optima(h):
    if not (h.ws / "analysis.json").exists():
        raise ValueError("run_analysis first")
    checked = json.loads((h.ws / "atomic_check.json").read_text(encoding="utf-8"))
    if not checked.get("passed") or checked.get("input_fingerprint") != h._fingerprint():
        raise ValueError("pass check_atomic on current inputs first")
    a, m = load_atomic(h.ws), h._load_model()
    ref = m.reference()
    grid = descriptor_grid(a)
    cond = conditions(ref)
    peak, vals = optimum(a, grid, cond)
    recs = h._records()
    if not recs:
        raise ValueError("no usable records")
    costs = [float(m.plant_cost(r)["cost_usd_per_t"]) for r in recs]
    def label(i):
        r = recs[i]
        return dict(paper=r["paper"], idx=r["idx"], catalyst=r["catalyst"], r=r["r"], cost=costs[i])
    per_paper = {}
    for i, r in enumerate(recs):
        if r["paper"] not in per_paper or r["r"] > recs[per_paper[r["paper"]]]["r"]:
            per_paper[r["paper"]] = i
    by_metal = {}
    for metal, entry in a.DESCRIPTORS.items():
        price = entry["metal_price_usd_per_kg"]
        cc = [float(m.plant_cost(a.record_from_descriptor(float(d), price))["cost_usd_per_t"]) for d in grid]
        j = int(np.argmin(cc))
        by_metal[metal] = dict(D=float(grid[j]), cost=cc[j], metal_price_usd_per_kg=price)
    mapping, excluded = [], []
    rankings = []
    for i, r in enumerate(recs):
        metal = main_metal(a, r)
        if metal is None:
            excluded.append(dict(paper=r["paper"], idx=r["idx"], reason="main metal absent from DESCRIPTORS"))
            continue
        mapping.append(effective_descriptor(a, grid, r, metal))
        # Intrinsic atomic rank uses literature metal descriptor; measured lab rank uses actual r.
        rankings.append((a.logtof(a.DESCRIPTORS[metal]["value"], cond["T_K"], cond["p_bar"]), r["r"], -costs[i]))
    disagreements = {}
    for i, j in combinations(range(3), 2):
        pairs = [(x, y) for x, y in combinations(rankings, 2) if x[i] != y[i] and x[j] != y[j]]
        disagreements[f"{('atomic','lab','industrial')[i]}_vs_{('atomic','lab','industrial')[j]}"] = dict(
            disagreements=sum((x[i]-y[i])*(x[j]-y[j]) < 0 for x, y in pairs), denominator=len(pairs),
            total_pairs=len(rankings)*(len(rankings)-1)//2, ties_excluded=len(rankings)*(len(rankings)-1)//2-len(pairs))
    refmetal = a.ATOMIC["reference_metal"]
    price = a.ATOMIC.get("reference_metal_price_usd_per_kg", a.DESCRIPTORS[refmetal]["metal_price_usd_per_kg"])
    cc = np.array([m.plant_cost(a.record_from_descriptor(float(d), price))["cost_usd_per_t"] for d in grid])
    backwards = {}
    for fraction in (.9, .95):
        target = ref["cost_usd_per_t"]*fraction
        indices = np.flatnonzero(cc <= target)
        segments = np.split(indices, np.where(np.diff(indices) > 1)[0]+1) if len(indices) else []
        backwards[str(fraction)] = dict(target_cost=target, descriptor_windows=[[float(grid[s[0]]), float(grid[s[-1]])] for s in segments] if segments else "not reachable")
    eff = effective_descriptor(a, grid, ref["record"], refmetal)
    counterfactuals = [a.record_from_descriptor(d, price) for d in (eff["D_eff"], peak["D"])]
    for rec in counterfactuals:
        rec["r"] *= eff["residual_multiplier"]
    before, after = [m.plant_cost(rec)["cost_usd_per_t"] for rec in counterfactuals]
    result = dict(input_fingerprint=h._fingerprint(), descriptor_range=[float(grid[0]), float(grid[-1])], grid_points=len(grid),
                  atomic_optimum=peak, laboratory_optimum=label(max(range(len(recs)), key=lambda i: recs[i]["r"])),
                  laboratory_best_per_paper={p: label(i) for p, i in per_paper.items()},
                  industrial_optimum=dict(measured=label(int(np.argmin(costs))), descriptor_by_metal=by_metal),
                  lab_to_descriptor=mapping, mapping_exclusions=excluded, backward_design=backwards,
                  pairwise_disagreement=disagreements, n_usable=len(recs), n_mapped=len(mapping),
                  atom_to_plant_attribution=dict(reference_D_eff=eff["D_eff"], atomic_D=peak["D"], cost_before=before,
                      cost_after=after, cost_change=after-before, residual_multiplier=eff["residual_multiplier"],
                      basis="descriptor-only counterfactual at reference metal price, retaining reference residual multiplier"))
    if a.ATOMIC.get("lab_conditions"):
        result["atomic_optimum_lab"] = optimum(a, grid, a.ATOMIC["lab_conditions"])[0]
    (h.ws / "three_optima.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    path = h.ws / "analysis.json"
    analysis = json.loads(path.read_text(encoding="utf-8"))
    analysis["atom_to_plant_attribution"] = result["atom_to_plant_attribution"]
    path.write_text(json.dumps(analysis, indent=2), encoding="utf-8")
    return result
