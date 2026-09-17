"""DISCOVER environment (PHASE E, 2026-09-06): closed-book, fine-grained scientific actions on the frozen NH3-FINAL-1.1 Layer A.

Design rules
- The environment loads the canonical manifest privately and never returns it. Nothing derived from `frozen_regression`,
  `atomic_reference.activity_order_expected`, the canonical run directory, the scenario registry or any results.json is exposed.
- Candidates are presented in alphabetical order (the harness' internal order is the atomic activity order and would leak).
- Every action returns only what that computation would give a working scientist; no aggregate "final answer" action exists.
- Every action is charged in compute units (CU) from the frozen cost model (DISCOVER_COST_MODEL_V1.json); the ledger is public.
- Stopping status is machine-checkable (S1–S4) and computed by the environment from the public state only.
"""
from __future__ import annotations
import json, math, time
from pathlib import Path
import numpy as np, yaml
from scipy.optimize import brentq

ROOT = Path(__file__).resolve().parents[1]
import sys; sys.path.insert(0, str(ROOT))
import harness_core as HC

LEVERS = {  # manifest key -> (public name, description, plausible range shown to the agent)
    "economics.metal_recovery_fraction": ("metal_recovery_fraction", "fraction of spent active metal recovered at replacement (0 = none)", [0.0, 0.95]),
    "economics.catalyst_life_y": ("catalyst_life_y", "catalyst service life before replacement, years", [5.0, 20.0]),
    "economics.electricity_USD_MWh": ("electricity_USD_MWh", "electricity price, USD/MWh (compression and refrigeration OPEX)", [20.0, 100.0]),
    "engineering.max_catalyst_bed_m3": ("max_catalyst_bed_m3", "maximum admissible catalyst bed volume, m3 (feasibility gate)", [15.0, 500.0]),
}
VALIDITY_SCOPES = ("window_edges", "bed_cap", "vessel_floor", "dominance")


class BudgetExceeded(Exception):
    pass


class DiscoverEnv:
    def __init__(self, manifest: str = "configs/nh3_final.yaml", cost_model: dict | None = None, budget: float = math.inf, seed: int = 0, count_evals: bool = False,
                 anonymous: bool = False, mapping_seed: int = 20260906):
        self._cfg = yaml.safe_load((ROOT / manifest).read_text(encoding="utf-8"))
        self._h = HC.NH3Harness(self._cfg, ROOT)
        self._resp = None                                       # response surface (loaded lazily from the cache asset)
        self.cost_model = cost_model or {"actions": {}}
        self.budget0 = float(budget); self.budget = float(budget); self.seed = int(seed)
        self.count_evals = count_evals; self._evals = 0
        if count_evals:
            env = self; orig = HC.Condition.logtof
            def counted(cond, EN): env._evals += 1; return orig(cond, EN)
            HC.Condition.logtof = counted; self._orig_logtof = orig
        # Public candidate ids. Named variant: alphabetical metal symbols (no activity-order leak). Anonymous variant: candidate_01..15 assigned by a
        # seeded permutation; the mapping public -> real is held privately and released only to the runner for the scorer (identity_mapping()).
        real = sorted(self._h.activity_order); self.anonymous = bool(anonymous); self.mapping_seed = int(mapping_seed)
        if self.anonymous:
            import random as _r; perm = list(real); _r.Random(self.mapping_seed).shuffle(perm)
            self._real = {f"candidate_{i + 1:02d}": m for i, m in enumerate(perm)}
        else:
            self._real = {m: m for m in real}
        self.candidates = sorted(self._real)
        self._price = {p: HC.PRICE[self._real[p]] for p in self.candidates}
        self._EN0 = {p: self._h.EN0[self._real[p]] for p in self.candidates}
        unc = self._cfg["uncertainty"]
        self._unc = {p: ({"distribution": "normal", "sigma_eV": float(unc["Fe_sigma_eV"])} if self._real[p] == "Fe"
                         else {"distribution": "uniform", "half_width_eV": float(unc["other_uniform_half_width_eV"])}) for p in self.candidates}
        self._V_CAP = float(self._cfg["engineering"]["max_catalyst_bed_m3"])
        proc = self._cfg["process"]
        self.domain = {"T_C": [float(x) for x in proc["temperature_C"]], "P_bar": {"min": float(proc["pressure_bar"]["start"]), "max": float(proc["pressure_bar"]["stop"]), "step": float(proc["pressure_bar"]["step"])},
                       "Tsep_C": {"min": float(proc["separator_temperature_C"]["start"]), "max": float(proc["separator_temperature_C"]["stop"]), "step": float(proc["separator_temperature_C"]["step"])},
                       "max_catalyst_bed_m3": self._V_CAP, "cost_boundary": "reduced catalyst/process-dependent NH3 cost, USD per tonne: active-metal replacement, converter (volume proxy + pressure-dependent shell), compression and refrigeration electricity, compressor capital; plant 1000 t/d"}
        # public state
        self.activity: dict[str, float] = {}; self.uncertainty_read: dict[str, dict] = {}
        self.windows: dict[str, dict] = {}; self._wmask: dict[str, np.ndarray] = {}
        self.optimized: dict[str, dict] = {}; self._logvec: dict[str, np.ndarray] = {}
        self.mc: list[dict] = []; self.levers: list[dict] = []; self.backward: list[dict] = []; self.reachability: list[dict] = []; self.validity: list[dict] = []
        self.ledger: list[dict] = []; self.step = 0

    # ------------------------------------------------------------------ accounting
    def _cost(self, action: str, **size) -> float:
        spec = self.cost_model["actions"].get(action)
        if spec is None: return 0.0
        c = float(spec.get("base_CU", 0.0))
        for k, rate in (spec.get("per_unit_CU") or {}).items(): c += float(rate) * float(size.get(k, 0.0))
        return float(math.ceil(c))

    def _charge(self, action: str, args: dict, cost: float, t0: float, e0: int, out: dict):
        if cost > self.budget + 1e-9: raise BudgetExceeded(f"{action} costs {cost:.0f} CU, remaining {self.budget:.0f} CU")
        self.budget -= cost; self.step += 1
        self.ledger.append({"step": self.step, "action": action, "args": args, "cost_CU": cost, "wall_s": round(time.perf_counter() - t0, 4),
                            "layerA_state_evals": (self._evals - e0) if self.count_evals else None, "remaining_CU": self.budget})
        return out

    def quote(self, action: str, args: dict) -> float:
        """Cost of an action before executing it (public)."""
        a = args or {}
        if action == "COMPUTE_ACTIVITY": return self._cost(action, metals=len(a.get("metals") or []))
        if action == "BUILD_PROCESS_WINDOW": return self._cost(action, states=float(np.count_nonzero(self._mask_from_bounds(a.get("bounds") or {}))))
        if action == "OPTIMIZE_PROCESS": return self._cost(action, states=float(np.count_nonzero(self._wmask.get(a.get("window", "full"), np.ones(self._h.NSTATE, bool)))))
        if action == "RUN_MC": return self._cost(action, draws_x_metals=float(a.get("draws", 100)) * len(a.get("metals") or []))
        if action == "TEST_LEVER": return self._cost(action, metals=len(a.get("metals") or []))
        if action == "BACKWARD": return self._cost(action)
        if action == "TEST_REACHABILITY": return self._cost(action, window=1.0 if a.get("scope", "reference") == "window" else 0.0)
        if action == "CHECK_MODEL_VALIDITY": return self._cost(action, evals=1.0 if (a.get("scope") == "dominance" and a.get("candidate") not in self._logvec) else 0.0)
        return self._cost(action)

    # ------------------------------------------------------------------ actions
    def INSPECT_CANDIDATES(self) -> dict:
        t0 = time.perf_counter(); e0 = self._evals
        out = {"candidates": [{"id": m, "descriptor_E_N_eV": self._EN0[m], "descriptor_source": "frozen S1-derived single-descriptor table", "price_USD_kg": self._price[m]} for m in self.candidates],
               "process_domain": self.domain, "note": "activities, feasibility and costs are not known until computed"}
        return self._charge("INSPECT_CANDIDATES", {}, self._cost("INSPECT_CANDIDATES"), t0, e0, out)

    def COMPUTE_ACTIVITY(self, metals: list[str]) -> dict:
        t0 = time.perf_counter(); e0 = self._evals; metals = self._check_metals(metals); cost = self._cost("COMPUTE_ACTIVITY", metals=len(metals))
        if cost > self.budget + 1e-9: raise BudgetExceeded(f"COMPUTE_ACTIVITY costs {cost:.0f} CU, remaining {self.budget:.0f} CU")
        res = {}
        for m in metals:
            self.activity[m] = float(self._h.base_condition.logtof(self._EN0[m])); res[m] = self.activity[m]
        out = {"log10_TOF_at_reference": res, "reference_condition": f"T {self._cfg['atomic_reference']['temperature_K']} K, pN2 {self._cfg['atomic_reference']['pN2_bar']} / pH2 {self._cfg['atomic_reference']['pH2_bar']} / pNH3 {self._cfg['atomic_reference']['pNH3_bar']} bar"}
        return self._charge("COMPUTE_ACTIVITY", {"metals": metals}, cost, t0, e0, out)

    def READ_PROPERTY_UNCERTAINTY(self, metals: list[str]) -> dict:
        t0 = time.perf_counter(); e0 = self._evals; metals = self._check_metals(metals)
        for m in metals: self.uncertainty_read[m] = self._unc[m]
        return self._charge("READ_PROPERTY_UNCERTAINTY", {"metals": metals}, self._cost("READ_PROPERTY_UNCERTAINTY"), t0, e0, {"descriptor_uncertainty_E_N": {m: self._unc[m] for m in metals}})

    def _mask_from_bounds(self, b: dict) -> np.ndarray:
        h = self._h; m = np.ones(h.NSTATE, bool)
        if "T_C" in b: m &= np.isin(h.state_T, [float(x) for x in b["T_C"]])
        if "P_bar" in b: m &= (h.state_P >= float(b["P_bar"][0])) & (h.state_P <= float(b["P_bar"][1]))
        if "Tsep_C" in b: m &= (h.state_Tsep >= float(b["Tsep_C"][0])) & (h.state_Tsep <= float(b["Tsep_C"][1]))
        return m

    def BUILD_PROCESS_WINDOW(self, bounds: dict | None = None, name: str | None = None) -> dict:
        t0 = time.perf_counter(); e0 = self._evals; bounds = bounds or {}; mask = self._mask_from_bounds(bounds)
        n = int(np.count_nonzero(mask)); cost = self._cost("BUILD_PROCESS_WINDOW", states=n)
        if n == 0: raise ValueError("window contains no admissible process state")
        wid = name or f"W{len(self.windows) + 1}"; self._wmask[wid] = mask
        self.windows[wid] = {"bounds": bounds, "n_states": n, "P_range": [float(self._h.state_P[mask].min()), float(self._h.state_P[mask].max())],
                             "T_values": sorted(set(float(x) for x in self._h.state_T[mask])), "Tsep_range": [float(self._h.state_Tsep[mask].min()), float(self._h.state_Tsep[mask].max())]}
        return self._charge("BUILD_PROCESS_WINDOW", {"bounds": bounds, "name": wid}, cost, t0, e0, {"window": wid, **self.windows[wid]})

    def _window(self, window: str | None) -> tuple[str, np.ndarray]:
        if window is None or window == "full":
            if "full" not in self._wmask: raise ValueError("no process window built yet: call BUILD_PROCESS_WINDOW first (name it 'full' for the whole admissible domain)")
        if window not in self._wmask: raise ValueError(f"unknown window {window}; built: {list(self._wmask)}")
        return window, self._wmask[window]

    def _state_logvec(self, m: str, mask: np.ndarray) -> np.ndarray:
        """Layer-A state-level activity vector for metal m over the masked states (2 MKM evaluations per state, as in the frozen closure)."""
        if m in self._logvec and np.all(np.isfinite(self._logvec[m][mask])): return self._logvec[m]
        h = self._h; EN = self._EN0[m]; x = min(max(float(EN), float(h.EGRID[0])), float(h.EGRID[-1])); pos = (x - float(h.EGRID[0])) / float(h.EGRID[1] - h.EGRID[0]); j = int(math.floor(pos))
        e0, e1, f = (float(h.EGRID[-1]), float(h.EGRID[-1]), 0.0) if j >= len(h.EGRID) - 1 else (float(h.EGRID[j]), float(h.EGRID[j + 1]), pos - j)
        vec = self._logvec.get(m, np.full(h.NSTATE, np.nan))
        for i in np.where(mask & ~np.isfinite(vec))[0]:
            c = h.process_states[i]["condition"]; vec[i] = c.logtof(e0) if (f == 0.0 or e0 == e1) else c.logtof(e0) * (1 - f) + c.logtof(e1) * f
        self._logvec[m] = vec; return vec

    def OPTIMIZE_PROCESS(self, metal: str, window: str = "full") -> dict:
        t0 = time.perf_counter(); e0 = self._evals; (metal,) = self._check_metals([metal]); wid, mask = self._window(window)
        cost = self._cost("OPTIMIZE_PROCESS", states=int(np.count_nonzero(mask & ~np.isfinite(self._logvec.get(metal, np.full(self._h.NSTATE, np.nan))))))
        if cost > self.budget + 1e-9: raise BudgetExceeded(f"OPTIMIZE_PROCESS costs {cost:.0f} CU, remaining {self.budget:.0f} CU")
        vec = self._state_logvec(metal, mask); total, V, metal_cost, reactor = self._h.cost_arrays(self._real[metal], np.nan_to_num(vec, nan=-300.0))
        ok = mask & (V <= self._V_CAP); h = self._h
        if np.any(ok):
            i = int(np.argmin(np.where(ok, total, np.inf))); rec = {"feasible": True, "cost_USD_t": float(total[i]), "T_C": float(h.state_T[i]), "P_bar": float(h.state_P[i]), "Tsep_C": float(h.state_Tsep[i]), "bed_m3": float(V[i]), "state_index": i}
        else:
            i = int(np.argmin(np.where(mask, V, np.inf))); rec = {"feasible": False, "cost_USD_t": None, "min_bed_m3": float(V[i]), "bed_cap_m3": self._V_CAP, "note": "no state satisfies the bed-volume limit"}
        rec.update({"window": wid, "metal": metal}); self.optimized[metal] = rec
        return self._charge("OPTIMIZE_PROCESS", {"metal": metal, "window": wid}, cost, t0, e0, dict(rec))

    def READ_COST_BREAKDOWN(self, metal: str) -> dict:
        t0 = time.perf_counter(); e0 = self._evals; (metal,) = self._check_metals([metal]); r = self.optimized.get(metal)
        if not r or not r["feasible"]: raise ValueError(f"{metal} has no feasible optimized state yet")
        vec = self._logvec[metal]; total, V, mc, reactor = self._h.cost_arrays(self._real[metal], np.nan_to_num(vec, nan=-300.0)); i = r["state_index"]
        bd = self._h.cost_breakdown_at(self._real[metal], V, mc, reactor, i)
        return self._charge("READ_COST_BREAKDOWN", {"metal": metal}, self._cost("READ_COST_BREAKDOWN"), t0, e0, {"metal": metal, "total_USD_t": float(total[i]), "pools_USD_t": bd})

    def _response(self):
        if self._resp is None:
            resp, cp, cached = self._h.build_or_load_response()
            if not cached: raise RuntimeError("response-surface asset missing; the frozen cache must exist")
            self._resp = resp
        return self._resp

    def RUN_MC(self, metals: list[str], draws: int = 100, window: str = "full") -> dict:
        t0 = time.perf_counter(); e0 = self._evals; metals = self._check_metals(metals); wid, mask = self._window(window); draws = int(draws)
        cost = self._cost("RUN_MC", draws_x_metals=draws * len(metals))
        if cost > self.budget + 1e-9: raise BudgetExceeded(f"RUN_MC costs {cost:.0f} CU, remaining {self.budget:.0f} CU")
        resp = self._response(); h = self._h; rng = np.random.default_rng(self.seed * 100003 + self.step + 1)
        costs = np.full((draws, len(metals)), np.inf)
        for j, m in enumerate(metals):
            u = self._unc[m]; en = rng.normal(self._EN0[m], u["sigma_eV"], draws) if u["distribution"] == "normal" else rng.uniform(self._EN0[m] - u["half_width_eV"], self._EN0[m] + u["half_width_eV"], draws)
            for d in range(draws):
                logv = h.interp_state_vector(resp, en[d]); total, V, _, _ = h.cost_arrays(self._real[m], logv); ok = mask & (V <= self._V_CAP)
                if np.any(ok): costs[d, j] = float(np.min(np.where(ok, total, np.inf)))
        per = {}
        for j, m in enumerate(metals):
            c = costs[:, j]; fin = np.isfinite(c)
            per[m] = {"feasibility_probability": float(fin.mean()), "cost_quantiles_USD_t": ({"p10": float(np.quantile(c[fin], 0.1)), "p50": float(np.quantile(c[fin], 0.5)), "p90": float(np.quantile(c[fin], 0.9))} if fin.any() else None)}
        win = np.argmin(costs, axis=1); anyfin = np.isfinite(costs).any(axis=1)
        pwin = {m: float(np.mean((win == j) & anyfin)) for j, m in enumerate(metals)}
        pair = {f"{a}<{b}": float(np.mean(costs[:, i] < costs[:, k])) for i, a in enumerate(metals) for k, b in enumerate(metals) if i < k}
        rec = {"window": wid, "draws": draws, "metals": metals, "per_metal": per, "P_lowest_cost_among_requested": pwin, "P_pairwise_lower_cost": pair}
        self.mc.append(rec); return self._charge("RUN_MC", {"metals": metals, "draws": draws, "window": wid}, cost, t0, e0, dict(rec))

    def TEST_LEVER(self, lever: str, value: float, metals: list[str], window: str = "full") -> dict:
        t0 = time.perf_counter(); e0 = self._evals; metals = self._check_metals(metals); wid, mask = self._window(window)
        key = next((k for k, v in LEVERS.items() if v[0] == lever or k == lever), None)
        if key is None: raise ValueError(f"unknown lever {lever}; allowed: {[v[0] for v in LEVERS.values()]}")
        cost = self._cost("TEST_LEVER", metals=len(metals))
        if cost > self.budget + 1e-9: raise BudgetExceeded(f"TEST_LEVER costs {cost:.0f} CU, remaining {self.budget:.0f} CU")
        h = self._h; out = {}
        for m in metals:
            if m not in self._logvec: raise ValueError(f"{m} must be optimized before testing levers")
            vec = np.nan_to_num(self._logvec[m], nan=-300.0); cap = self._V_CAP
            if key == "economics.metal_recovery_fraction": total, V, _, _ = h.cost_arrays(self._real[m], vec, recovery=float(value))
            elif key == "economics.catalyst_life_y": total, V, _, _ = h.cost_arrays(self._real[m], vec, life_y=float(value))
            elif key == "economics.electricity_USD_MWh":
                total, V, mcst, reactor = h.cost_arrays(self._real[m], vec); scale = float(value) / h.ELECTRICITY
                total = mcst + reactor + (h.state_fresh + h.state_reccomp + h.state_refrig) * scale + h.state_compcapex
            else: total, V, _, _ = h.cost_arrays(self._real[m], vec); cap = float(value)
            ok = mask & (V <= cap)
            out[m] = ({"feasible": True, "cost_USD_t": float(total[int(np.argmin(np.where(ok, total, np.inf)))]), "P_bar": float(h.state_P[int(np.argmin(np.where(ok, total, np.inf)))])} if np.any(ok) else {"feasible": False, "cost_USD_t": None})
        rec = {"lever": LEVERS[key][0], "value": float(value), "window": wid, "costs": out, "baseline_costs": {m: self.optimized[m]["cost_USD_t"] for m in metals if m in self.optimized}}
        self.levers.append(rec); return self._charge("TEST_LEVER", {"lever": LEVERS[key][0], "value": float(value), "metals": metals, "window": wid}, cost, t0, e0, dict(rec))

    def BACKWARD(self, pair: list[str], property: str = "activity", window: str = "full") -> dict:
        t0 = time.perf_counter(); e0 = self._evals; a, b = self._check_metals(pair); wid, mask = self._window(window)
        if property != "activity": raise ValueError("only property='activity' (intrinsic-activity multiplier) is implemented")
        if a not in self._logvec or b not in self._logvec or not self.optimized.get(b, {}).get("feasible"): raise ValueError("both metals must be optimized in this window and the target must be feasible")
        cost = self._cost("BACKWARD")
        if cost > self.budget + 1e-9: raise BudgetExceeded(f"BACKWARD costs {cost:.0f} CU, remaining {self.budget:.0f} CU")
        h = self._h; va = np.nan_to_num(self._logvec[a], nan=-300.0); target = self.optimized[b]["cost_USD_t"]
        def best(alpha):
            total, V, _, _ = h.cost_arrays(self._real[a], va, alpha=alpha); ok = mask & (V <= self._V_CAP)
            if not np.any(ok): return None, None
            i = int(np.argmin(np.where(ok, total, np.inf))); return float(total[i]), i
        def gap(la):
            c, _ = best(10 ** la); return (c - target) if c is not None else 1e100
        if gap(0.0) <= 0: rec = {"pair": [a, b], "already_at_or_below_target": True, "multiplier": 1.0}
        elif gap(12.0) > 0: rec = {"pair": [a, b], "parity_not_reached_within": "1e12", "multiplier": None}
        else:
            la = brentq(gap, -6.0, 12.0, xtol=1e-9); c, i = best(10 ** la)
            rec = {"pair": [a, b], "multiplier": float(10 ** la), "parity_cost_USD_t": c, "state_at_parity": {"T_C": float(h.state_T[i]), "P_bar": float(h.state_P[i]), "Tsep_C": float(h.state_Tsep[i])}}
        rec.update({"property": "activity", "window": wid, "definition": f"intrinsic-activity multiplier of {a} at which its re-optimized cost equals the optimized cost of {b}"})
        self.backward.append(rec); return self._charge("BACKWARD", {"pair": [a, b], "property": property, "window": wid}, cost, t0, e0, dict(rec))

    def TEST_REACHABILITY(self, metal: str, property: str = "activity", scope: str = "reference", required_multiplier: float | None = None) -> dict:
        t0 = time.perf_counter(); e0 = self._evals; (metal,) = self._check_metals([metal])
        if property != "activity": raise ValueError("only property='activity' is implemented")
        cost = self._cost("TEST_REACHABILITY", window=1.0 if scope == "window" else 0.0)
        if cost > self.budget + 1e-9: raise BudgetExceeded(f"TEST_REACHABILITY costs {cost:.0f} CU, remaining {self.budget:.0f} CU")
        h = self._h; base = float(h.base_condition.logtof(self._EN0[metal]))
        curve = np.array([h.base_condition.logtof(float(e)) for e in h.EGRID]); gain_ref = float(10 ** (np.max(curve) - base)); e_at = float(h.EGRID[int(np.argmax(curve))])
        rec = {"metal": metal, "property": "activity", "scope": scope, "max_gain_on_descriptor_manifold_at_reference": gain_ref, "descriptor_at_max_eV": e_at,
               "definition": "largest intrinsic-activity multiplier obtainable by moving the single descriptor along the frozen scaling manifold"}
        if scope == "window":
            resp = self._response(); vec = h.interp_state_vector(resp, self._EN0[metal]); rec["max_gain_across_process_states"] = float(np.max(10 ** (np.max(resp, axis=1) - vec)))
        if required_multiplier is not None:
            g = rec.get("max_gain_across_process_states", gain_ref); rec["required_multiplier"] = float(required_multiplier)
            rec["classification"] = "reachable" if required_multiplier <= g else ("marginal" if required_multiplier <= 2 * g else "unreachable")
        self.reachability.append(rec); return self._charge("TEST_REACHABILITY", {"metal": metal, "property": property, "scope": scope, "required_multiplier": required_multiplier}, cost, t0, e0, dict(rec))

    def CHECK_MODEL_VALIDITY(self, scope: str, candidate: str | None = None, reference: str | None = None, window: str = "full") -> dict:
        t0 = time.perf_counter(); e0 = self._evals
        if scope not in VALIDITY_SCOPES: raise ValueError(f"scope must be one of {VALIDITY_SCOPES}")
        h = self._h; out = {"scope": scope}
        if scope == "window_edges":
            flags = {}
            for m, r in self.optimized.items():
                if not r["feasible"]: continue
                w = self.windows[r["window"]]; flags[m] = {"T_on_edge": r["T_C"] in (min(w["T_values"]), max(w["T_values"])), "P_on_edge": r["P_bar"] in tuple(w["P_range"]), "Tsep_on_edge": r["Tsep_C"] in tuple(w["Tsep_range"])}
            out["optimum_on_window_edge"] = flags; out["note"] = "an optimum on a window edge means the window, not the model, sets that variable"
        elif scope == "bed_cap":
            out["bed_cap_m3"] = self._V_CAP; out["slack_m3"] = {m: (self._V_CAP - r["bed_m3"]) for m, r in self.optimized.items() if r["feasible"]}; out["infeasible"] = [m for m, r in self.optimized.items() if not r["feasible"]]
        elif scope == "vessel_floor":
            floor = float(self._cfg["economics"]["pressure_capex"]["vessel"]["A_min_m3"]); out["vessel_correlation_floor_m3"] = floor
            out["below_floor"] = {m: r["bed_m3"] for m, r in self.optimized.items() if r["feasible"] and r["bed_m3"] < floor}; out["note"] = "vessels below the correlation floor are costed at the floor (declared clamp)"
        else:
            if not candidate or not reference: raise ValueError("dominance check needs candidate and reference")
            (candidate, reference) = self._check_metals([candidate, reference]); wid, mask = self._window(window)
            need = candidate not in self._logvec; cost = self._cost("CHECK_MODEL_VALIDITY", evals=1.0 if need else 0.0)
            if cost > self.budget + 1e-9: raise BudgetExceeded(f"CHECK_MODEL_VALIDITY costs {cost:.0f} CU, remaining {self.budget:.0f} CU")
            if reference not in self._logvec: raise ValueError("reference must be optimized first")
            vc = self._state_logvec(candidate, mask); vr = self._logvec[reference]
            tc, Vc, _, _ = h.cost_arrays(self._real[candidate], np.nan_to_num(vc, nan=-300.0)); tr, Vr, _, _ = h.cost_arrays(self._real[reference], np.nan_to_num(vr, nan=-300.0))
            okc = mask & (Vc <= self._V_CAP); dominated = (not np.any(okc)) or bool(np.all(tc[okc] >= tr[okc] - 1e-9))
            out.update({"candidate": candidate, "reference": reference, "window": wid, "dominated_at_every_admissible_state": dominated,
                        "note": "exact state-level check: candidate cost >= reference cost at every feasible state of the window"})
            self.validity.append(out); return self._charge("CHECK_MODEL_VALIDITY", {"scope": scope, "candidate": candidate, "reference": reference, "window": wid}, cost, t0, e0, dict(out))
        self.validity.append(out); return self._charge("CHECK_MODEL_VALIDITY", {"scope": scope}, self._cost("CHECK_MODEL_VALIDITY"), t0, e0, dict(out))

    # ------------------------------------------------------------------ helpers / public state
    def _check_metals(self, metals):
        metals = list(metals or [])
        bad = [m for m in metals if m not in self.candidates]
        if bad or not metals: raise ValueError(f"unknown or empty candidate list: {bad or metals}")
        return metals

    def current_winner(self):
        feas = {m: r["cost_USD_t"] for m, r in self.optimized.items() if r["feasible"]}
        return (min(feas, key=feas.get) if feas else None), feas

    def screened_dominated(self, m: str, winner: str) -> bool:
        """Declared screening rule (approximate, public): lower reference activity AND higher metal price than the current lowest-cost candidate."""
        return (m in self.activity and winner in self.activity and self.activity[m] <= self.activity[winner] and self._price[m] >= self._price[winner])

    def stopping_status(self, edv_max: float | None = None, edv_threshold: float = 0.0, min_action_cost: float = 0.0) -> dict:
        w, feas = self.current_winner()
        unresolved = [m for m in self.candidates if m not in self.optimized and not (w and self.screened_dominated(m, w))]
        s1 = w is not None; s2 = s1 and not unresolved
        atomic_best = max(self.activity, key=self.activity.get) if len(self.activity) == len(self.candidates) else None
        if atomic_best is None: s3 = False; s3_note = "atomic activities not computed for every candidate"
        elif w and atomic_best == w: s3 = True; s3_note = "highest-activity candidate equals the lowest-cost candidate"
        else:
            bw = [b for b in self.backward if b["pair"] == [atomic_best, w]]; rc = [r for r in self.reachability if r["metal"] == atomic_best and "classification" in r]
            s3 = bool(bw and rc); s3_note = f"backward {'done' if bw else 'missing'}, reachability {'classified' if rc else 'missing'} for {atomic_best} vs {w}" if w else "no winner"
        s4 = (edv_max is not None and edv_max < edv_threshold) or (self.budget < max(min_action_cost, 1e-9))
        return {"S1_winner_identified": s1, "S2_no_unresolved_candidate": s2, "unresolved_candidates": unresolved, "S3_reachability_classified_if_needed": s3, "S3_note": s3_note,
                "S4_edv_below_threshold_or_budget_exhausted": bool(s4), "may_stop": bool((s1 and s2 and s3) or self.budget < max(min_action_cost, 1e-9)),
                "current_winner": w, "atomic_best": atomic_best, "remaining_CU": self.budget}

    def public_state(self) -> dict:
        w, feas = self.current_winner()
        return {"remaining_CU": self.budget, "spent_CU": self.budget0 - self.budget, "steps": self.step,
                "activity_log10_TOF": dict(self.activity), "uncertainty_read": dict(self.uncertainty_read), "windows": dict(self.windows),
                "optimized": {m: {k: v for k, v in r.items() if k != "state_index"} for m, r in self.optimized.items()},
                "current_lowest_cost_candidate": w, "mc": list(self.mc), "levers": list(self.levers), "backward": list(self.backward), "reachability": list(self.reachability), "validity": list(self.validity)}

    def identity_mapping(self) -> dict:
        """public id -> real metal. SCORER-ONLY: the runner writes it next to the trace; it is never part of any action output or public state."""
        return {"variant": "anonymous" if self.anonymous else "named", "mapping_seed": self.mapping_seed, "public_to_real": dict(self._real)}

    def close(self):
        if self.count_evals: HC.Condition.logtof = self._orig_logtof
