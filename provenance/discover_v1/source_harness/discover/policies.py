"""DISCOVER policies A–D (deterministic, no LLM) and the common admissible-action enumerator.

Every policy sees only env.public_state(), the admissible action list with quoted costs, and the stopping status.
A  Random              : uniform random admissible action (seeded); stops when the environment says it may stop.
B  Activity-first      : complete the atomic ranking, then extend process calculations in descending atomic-activity order.
C  Uncertainty-first   : resolve the largest descriptor uncertainty first (optimize + max-draw MC), ignoring downstream leverage.
D  Fixed VOI heuristic : frozen deterministic decision-value score u*g*b/cost (voi.py logic); never calls an LLM.
All four use the same action space, cost model, budget and stopping constraints (S1-S4)."""
from __future__ import annotations
import math, random

LEVER_PROBES = [("metal_recovery_fraction", 0.9), ("catalyst_life_y", 20.0), ("electricity_USD_MWh", 20.0), ("max_catalyst_bed_m3", 30.0)]
MC_DRAWS = (100, 300, 1000)


def admissible_actions(env) -> list[dict]:
    """Enumerate admissible actions with quoted costs (generic; policies filter/score)."""
    st = env; acts = []
    if not env.windows: acts.append({"action": "BUILD_PROCESS_WINDOW", "args": {"bounds": {}, "name": "full"}})
    missing = [m for m in env.candidates if m not in env.activity]
    if missing: acts.append({"action": "COMPUTE_ACTIVITY", "args": {"metals": missing}})
    miss_u = [m for m in env.candidates if m not in env.uncertainty_read]
    if miss_u: acts.append({"action": "READ_PROPERTY_UNCERTAINTY", "args": {"metals": miss_u}})
    if env.windows:
        for m in env.candidates:
            if m not in env.optimized: acts.append({"action": "OPTIMIZE_PROCESS", "args": {"metal": m, "window": "full"}})
        feas = [m for m, r in env.optimized.items() if r["feasible"]]
        for m in feas:
            for d in MC_DRAWS: acts.append({"action": "RUN_MC", "args": {"metals": [m], "draws": d, "window": "full"}})
        w, _ = env.current_winner()
        if w:
            for m in feas:
                if m != w and env.activity.get(m, -1e9) > env.activity.get(w, -1e9) and not any(b["pair"] == [m, w] for b in env.backward):
                    acts.append({"action": "BACKWARD", "args": {"pair": [m, w], "property": "activity", "window": "full"}})
            for b in env.backward:
                m = b["pair"][0]
                if b.get("multiplier") and not any(r["metal"] == m and "classification" in r for r in env.reachability):
                    acts.append({"action": "TEST_REACHABILITY", "args": {"metal": m, "property": "activity", "scope": "window", "required_multiplier": b["multiplier"]}})
            for lever, val in LEVER_PROBES:
                if not any(l["lever"] == lever and abs(l["value"] - val) < 1e-9 for l in env.levers): acts.append({"action": "TEST_LEVER", "args": {"lever": lever, "value": val, "metals": feas, "window": "full"}})
            if len(feas) >= 2 and not any(len(x["metals"]) >= 2 for x in env.mc): acts.append({"action": "RUN_MC", "args": {"metals": sorted(feas), "draws": 300, "window": "full"}})
        if env.optimized and not any(v.get("scope") == "window_edges" for v in env.validity): acts.append({"action": "CHECK_MODEL_VALIDITY", "args": {"scope": "window_edges"}})
    for a in acts: a["cost_CU"] = env.quote(a["action"], a["args"])
    return [a for a in acts if a["cost_CU"] <= env.budget + 1e-9]


class Policy:
    name = "base"
    def __init__(self, seed: int = 0): self.rng = random.Random(seed); self.seed = seed
    def choose(self, env, acts: list[dict], status: dict) -> tuple[dict | None, str, float | None]:
        raise NotImplementedError
    def edv_threshold(self): return 0.0


class RandomPolicy(Policy):
    name = "A_random"
    def choose(self, env, acts, status):
        if status["may_stop"] and status["S1_winner_identified"] and status["S2_no_unresolved_candidate"] and status["S3_reachability_classified_if_needed"]:
            return None, "S1-S3 satisfied", None
        if not acts: return None, "no affordable admissible action", None
        a = self.rng.choice(acts); return a, "uniform random choice among admissible actions", None


def _phase0(env, acts):
    """Cheap mandatory information every non-random policy takes first: window, activities, uncertainties."""
    for name in ("BUILD_PROCESS_WINDOW", "COMPUTE_ACTIVITY", "READ_PROPERTY_UNCERTAINTY"):
        a = next((x for x in acts if x["action"] == name), None)
        if a: return a
    return None


class ActivityFirstPolicy(Policy):
    name = "B_activity_first"
    def choose(self, env, acts, status):
        a = _phase0(env, acts)
        if a: return a, "phase 0: complete the atomic activity / descriptor picture before any process calculation", None
        order = sorted(env.candidates, key=lambda m: -env.activity.get(m, -1e9))          # descending atomic activity
        for m in order:                                                                    # extend process calculations by atomic rank
            o = next((x for x in acts if x["action"] == "OPTIMIZE_PROCESS" and x["args"]["metal"] == m), None)
            if o and (not status["S2_no_unresolved_candidate"] or m in status["unresolved_candidates"]): return o, f"optimize next candidate in atomic-activity order ({m})", None
        if not status["S3_reachability_classified_if_needed"]:
            b = next((x for x in acts if x["action"] == "BACKWARD"), None) or next((x for x in acts if x["action"] == "TEST_REACHABILITY"), None)
            if b: return b, "atomic-best differs from industrial winner: run backward/reachability", None
        for m in order:                                                                    # refine uncertainty in atomic order, 300 draws
            if m in env.optimized and env.optimized[m]["feasible"] and not any(x["metals"] == [m] for x in env.mc):
                o = next((x for x in acts if x["action"] == "RUN_MC" and x["args"]["metals"] == [m] and x["args"]["draws"] == 300), None)
                if o: return o, f"refine descriptor uncertainty of {m} (atomic order)", None
        return None, "atomic-order queue exhausted; S1-S3 " + ("satisfied" if status["may_stop"] else "NOT satisfied (budget limits)"), None


class UncertaintyFirstPolicy(Policy):
    name = "C_uncertainty_first"
    def _sigma(self, env, m):
        u = env.uncertainty_read.get(m) or {}
        return u.get("sigma_eV") or (u.get("half_width_eV", 0.0) / math.sqrt(3.0))
    def choose(self, env, acts, status):
        a = _phase0(env, acts)
        if a: return a, "phase 0: window, activities, uncertainties", None
        # largest descriptor sigma first; ties broken by public physical data (descriptor value, then price), never by the candidate label,
        # so the policy is label-invariant and the named / anonymous variants are isomorphic (2026-09-06: the first draft used the label as
        # tie-break, which made C's trajectory depend on the naming; recorded in DISCOVER_V1_FINAL_CHECKS.md)
        order = sorted(env.candidates, key=lambda m: (-self._sigma(env, m), env._EN0[m], env._price[m]))
        for m in order:
            o = next((x for x in acts if x["action"] == "OPTIMIZE_PROCESS" and x["args"]["metal"] == m), None)
            if o: return o, f"largest unresolved descriptor uncertainty: optimize {m} (sigma {self._sigma(env, m):.3f} eV)", None
            if env.optimized.get(m, {}).get("feasible") and not any(x["metals"] == [m] for x in env.mc):
                o = next((x for x in acts if x["action"] == "RUN_MC" and x["args"]["metals"] == [m] and x["args"]["draws"] == 1000), None) or \
                    next((x for x in acts if x["action"] == "RUN_MC" and x["args"]["metals"] == [m]), None)
                if o: return o, f"propagate the largest uncertainty with maximum draws ({m})", None
        if not status["S3_reachability_classified_if_needed"]:
            b = next((x for x in acts if x["action"] in ("BACKWARD", "TEST_REACHABILITY")), None)
            if b: return b, "uncertainty queue exhausted; backward/reachability still required by S3", None
        return None, "uncertainty queue exhausted", None


class FixedVOIPolicy(Policy):
    """Frozen deterministic acquisition score. value = u * g * b / cost  (u: descriptor uncertainty of the target, g: downstream leverage proxy,
    b: closeness to the decision boundary), plus fixed values for the mandatory decision steps. No LLM."""
    name = "D_fixed_voi"
    THETA = 0.05        # stop when the best remaining value (per CU, x10 scale) falls below this; frozen before any formal run
    MC_DECAY_DRAWS = 50 # diminishing returns of repeated MC on the same candidate: decay = 1/(1 + done/50)^2
    LAMBDA = 0.5        # price weight in the cost surrogate (log10 USD/kg per log10 TOF unit)
    def edv_threshold(self): return self.THETA
    def _surrogate(self, env, m):   # lower is better: cheap proxy for the optimized cost rank before any process calculation
        return -env.activity.get(m, -1e9) + self.LAMBDA * math.log10(env._price[m])
    def score(self, env, a, status):
        act, args, cost = a["action"], a["args"], max(a["cost_CU"], 1.0); w, feas = env.current_winner()
        if act in ("BUILD_PROCESS_WINDOW", "COMPUTE_ACTIVITY", "READ_PROPERTY_UNCERTAINTY"): return 10.0
        if act == "OPTIMIZE_PROCESS":
            m = args["metal"]
            if w and env.screened_dominated(m, w): return 0.0005 / cost * 10
            s = {x: self._surrogate(env, x) for x in env.candidates if x not in env.optimized}; smin = min(s.values())
            return (1.0 * math.exp(-(s[m] - smin) / 1.0) + (0.5 if not w else 0.0)) / cost * 10
        if act == "BACKWARD": return 5.0 if not status["S3_reachability_classified_if_needed"] else 0.01
        if act == "TEST_REACHABILITY": return 5.0 if not status["S3_reachability_classified_if_needed"] else 0.01
        if act == "RUN_MC":
            metals, d = args["metals"], args["draws"]
            if not w: return 0.0
            val = 0.0
            for m in metals:
                u = (env.uncertainty_read.get(m) or {}); sig = u.get("sigma_eV") or u.get("half_width_eV", 0.1) / math.sqrt(3)
                cw = feas[w]; cm = feas.get(m, cw); b = math.exp(-abs(math.log(cm / cw)) / 0.15) if cm and cw else 0.0
                g = 1.0 if m == w else b
                done = sum(x["draws"] for x in env.mc if m in x["metals"]); u_rem = sig / 0.1 / (1.0 + done / self.MC_DECAY_DRAWS) ** 2
                val += u_rem * g * b
            return val / cost * 10 * (1.0 if len(metals) == 1 else 1.5)
        if act == "TEST_LEVER":
            if not w or len(feas) < 2: return 0.0
            return 0.05 / cost * 10
        if act == "CHECK_MODEL_VALIDITY": return 0.3 / cost * 10 if env.optimized else 0.0
        return 0.0
    def choose(self, env, acts, status):
        if not acts: return None, "no affordable admissible action", None
        scored = sorted(((self.score(env, a, status), a) for a in acts), key=lambda t: -t[0]); v, a = scored[0]
        a = dict(a); a["expected_decision_value"] = v
        for s, x in scored: x["expected_decision_value"] = s
        if status["S1_winner_identified"] and status["S2_no_unresolved_candidate"] and status["S3_reachability_classified_if_needed"] and v < self.THETA:
            return None, f"S1-S3 satisfied and best remaining value {v:.4f} < theta {self.THETA}", v
        return a, f"highest decision value per CU ({v:.4f}): {a['action']} {a['args']}", v


POLICIES = {p.name: p for p in (RandomPolicy, ActivityFirstPolicy, UncertaintyFirstPolicy, FixedVOIPolicy)}
