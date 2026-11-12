"""Single-site mean-field steady-state MKM; energies eV, pressures bar, TOF /site/s.

Spec: species={adsorbate: site_count}, gases={formula: partial_pressure}, T_K,
descriptor, steps=[{name, stoich:{species: signed_nu}, Ea:{a,b}, dE:{a,b},
prefactor:optional}], overall={gas: signed_nu}. Vacancy is '*'; each step must
conserve sites. Gas free-energy corrections are standard-state eV per molecule,
supplied as gas_corrections={gas: number}, and added stoichiometrically to dE.
Ea and dE can alternatively be numbers. dE is the uncorrected standard reaction
energy. Backward constants use the SAME prefactor and transition state, exactly
enforcing kf/kr=exp(-dG/kT). Caller must supply thermodynamically consistent cycles.
DRC lowers each shared transition-state energy, preserving its equilibrium constant.
"""
import copy
import math
import numpy as np
from scipy.optimize import root
from scipy.integrate import solve_ivp
from scipy.special import softmax

KB = 8.617333262145e-5
H_EV_S = 4.135667696e-15


def linear(value, descriptor):
    return float(value.get("a", 0)) + float(value.get("b", 0))*descriptor if isinstance(value, dict) else float(value)


def solve(spec, drc=True):
    names = list(spec["species"])
    sites = np.array([float(spec["species"][s]) for s in names])
    if not len(names) or np.any(sites <= 0):
        raise ValueError("positive adsorbate site counts required")
    gases = {k: float(v) for k, v in spec["gases"].items()}
    if any(v < 0 or not math.isfinite(v) for v in gases.values()):
        raise ValueError("invalid partial pressure")
    t, d = float(spec["T_K"]), float(spec.get("descriptor", 0))
    if t <= 0:
        raise ValueError("positive temperature required")
    kt = KB*t
    steps = spec["steps"]
    nu = np.array([[float(step["stoich"].get(s, 0)) for step in steps] for s in names])
    logs = []
    for step in steps:
        st = step["stoich"]
        if set(st) - set(names) - set(gases) - {"*"}:
            raise ValueError("unknown species in step")
        if abs(sum(st.get(s, 0)*n for s, n in zip(names, sites)) + st.get("*", 0)) > 1e-10:
            raise ValueError("elementary step violates site balance")
        dg = linear(step["dE"], d) + sum(st.get(s, 0)*float(v) for s, v in spec.get("gas_corrections", {}).items())
        ea = linear(step["Ea"], d)
        pref = float(step.get("prefactor", kt/H_EV_S))
        if pref <= 0 or not all(math.isfinite(v) for v in (dg, ea, pref)):
            raise ValueError("invalid kinetic parameters")
        # One common TS above both minima; no independent reverse barrier clipping.
        ea = max(ea, dg, 0.)
        logs.append((math.log(pref)-ea/kt, math.log(pref)-(ea-dg)/kt))
    logs = np.array(logs)
    scale = math.exp(float(np.clip(logs.max(), -600, 600)))

    def decode(z):
        fractions = softmax(np.r_[0., z])
        return fractions[1:]/sites, fractions[0]

    def rates(theta, vacancy, gross=False):
        activities = dict(gases, **dict(zip(names, theta)))
        activities["*"] = vacancy
        result, turnover = [], []
        for (lf, lr), step in zip(logs, steps):
            for s, v in step["stoich"].items():
                la = math.log(max(float(activities[s]), 1e-300))
                if v < 0:
                    lf += -v*la
                else:
                    lr += v*la
            # expm1 prevents cancellation near equilibrium.
            a, b = np.clip([lf, lr], -745, 700)
            result.append(math.exp(a)*(-math.expm1(b-a)) if a >= b else math.exp(b)*math.expm1(a-b))
            turnover.append(math.exp(a)+math.exp(b))
        return (np.array(result), np.array(turnover)) if gross else np.array(result)

    def residual(z):
        theta, vacancy = decode(z)
        rr, turnover = rates(theta, vacancy, gross=True)
        return (nu @ rr) / np.maximum(abs(nu) @ turnover, scale*1e-100)

    solution = None
    for initial in (np.zeros(len(names)), np.full(len(names), -8.), np.full(len(names), 8.)):
        candidate = root(residual, initial, method="hybr")
        if np.linalg.norm(residual(candidate.x), np.inf) < 1e-10:
            theta, vacancy = decode(candidate.x)
            # A saturated numerical boundary must not masquerade as an interior root.
            if vacancy > 1e-14 and np.all(theta > 1e-14):
                solution = candidate.x
                break
    method = "root"
    if solution is None:
        method = "BDF+root"
        # Integrate log(theta_i / vacancy) with a common rate scaling.
        def rhs(_, z):
            theta, vacancy = decode(z)
            dt = nu @ rates(theta, vacancy) / scale
            return dt / np.maximum(theta, 1e-100) + np.dot(sites, dt)/max(vacancy, 1e-100)
        z = np.full(len(names), -2.)
        for horizon in (1e2, 1e4, 1e6):
            result = solve_ivp(rhs, (0, horizon), z, method="BDF", rtol=1e-8, atol=1e-10)
            z = result.y[:, -1]
            candidate = root(residual, z)
            if np.linalg.norm(residual(candidate.x), np.inf) < 1e-10:
                solution = candidate.x
                break
        if solution is None:
            raise RuntimeError("MKM did not reach steady state")
    theta, vacancy = decode(solution)
    rr = rates(theta, vacancy)
    overall = spec["overall"]
    fluxes = {g: sum(step["stoich"].get(g, 0)*r for step, r in zip(steps, rr)) for g in overall}
    ratios = [fluxes[g]/v for g, v in overall.items() if v]
    tof = float(np.mean(ratios))
    if not np.allclose(ratios, tof, rtol=1e-6, atol=scale*1e-9):
        raise ValueError("gas fluxes do not match named overall stoichiometry")
    result = dict(coverages=dict(zip(names, map(float, theta)), **{"*": float(vacancy)}),
                  net_rates={s.get("name", str(i)): float(r) for i, (s, r) in enumerate(zip(steps, rr))},
                  TOF=tof, method=method, residual=float(np.linalg.norm(residual(solution), np.inf)),
                  log_kf_over_kr=[float(a-b) for a, b in logs], degree_of_rate_control=[])
    if drc and abs(tof) > 1e-200:
        delta = 1e-4
        for i in range(len(steps)):
            trial = copy.deepcopy(spec)
            trial["steps"][i]["Ea"] = linear(steps[i]["Ea"], d) - delta*kt
            changed = solve(trial, drc=False)["TOF"]
            result["degree_of_rate_control"].append((math.log(abs(changed))-math.log(abs(tof)))/delta if changed*tof > 0 else None)
    return result
