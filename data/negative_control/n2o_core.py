"""
NEGATIVE CONTROL V0.1 - N2O decomposition rank-preservation chain (model N2O-NEGCTRL-0.1).

Chain: dE_O -> BEP barriers -> two-step steady-state MKM with O2 inhibition and mean-field O-O repulsion -> atomic ranking at
one reference condition -> isothermal PFR at fixed conversion -> metal mass / bed volume -> per-candidate (T, D) optimization ->
cost pools (USD per t N2O destroyed) -> feasible economic ranking -> rank-preservation metrics.

Everything scientific is read from configs/n2o_negcontrol_v0_1.yaml (frozen). Prices / molar masses are imported from
harness_core (read-only). Nothing here reads configs/nh3_final.yaml.
"""
from __future__ import annotations
import math
from itertools import combinations
from pathlib import Path
from typing import Any
import numpy as np
from scipy.optimize import brentq
from scipy.stats import spearmanr, kendalltau

import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harness_core import PRICE, MW  # noqa: E402  (read-only constants, NH3-FINAL-1.1 price basis)

K_B_EV = 8.617333262145e-5
N_A = 6.02214076e23
R = 8.314462618
MW_N2O = 0.0440128
NM3_MOL = 1.0 / 0.022414  # mol per Nm3 (0 C, 1 atm)


class N2OKinetics:
    def __init__(self, cfg: dict):
        k = cfg["kinetics"]
        self.a1 = float(k["R1_BEP"]["a1"]); self.b1 = float(k["R1_BEP"]["b1"]); self.nu1 = float(k["R1_BEP"]["prefactor_s-1_bar-1"])
        self.nu2 = float(k["R2_desorption"]["prefactor_s-1"]); self.dS = float(k["R2_desorption"]["adsorption_entropy_loss_eV_per_K"])
        self.eps = float(k["lateral_interaction"]["eps_eV_per_ML"])

    def _rates(self, dEO: float, T: float, pO2: float, theta_O: float):
        kT = K_B_EV * T
        eff = dEO + self.eps * theta_O
        Ea1 = max(0.0, self.a1 * dEO + self.b1)
        k1 = self.nu1 * math.exp(-Ea1 / kT)                       # s-1 bar-1
        Ea2 = max(0.0, -eff) + 0.30
        k2 = self.nu2 * math.exp(-Ea2 / kT)                       # s-1
        KO = math.exp(-(eff + T * self.dS) / kT)                  # per-O adsorption equilibrium constant (bar^-1/2 scale)
        return k1, k2, KO

    def solve(self, dEO: float, T: float, pN2O: float, pO2: float) -> dict:
        """Steady state: r1 = k1 pN2O theta_* = 2 r2_net, r2_net = k2 (theta_O^2 - KO^2 pO2 theta_*^2)."""
        def f(theta_O):
            k1, k2, KO = self._rates(dEO, T, pO2, theta_O)
            ts = 1.0 - theta_O
            return k1 * pN2O * ts - 2.0 * k2 * (theta_O ** 2 - KO ** 2 * pO2 * ts ** 2)
        lo, hi = 1e-12, 1.0 - 1e-12
        flo, fhi = f(lo), f(hi)
        if flo <= 0.0:      # no consumption even at empty surface (numerically) -> take lo
            th = lo
        elif fhi >= 0.0:    # surface fully covered
            th = hi
        else:
            th = brentq(f, lo, hi, xtol=1e-14, rtol=1e-12, maxiter=300)
        k1, k2, KO = self._rates(dEO, T, pO2, th)
        tof = k1 * pN2O * (1.0 - th)
        return {"theta_O": th, "TOF": tof, "k1": k1, "k2": k2, "Ea1": max(0.0, self.a1 * dEO + self.b1), "Ea2": max(0.0, -(dEO + self.eps * th)) + 0.30}


class N2OHarness:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.metals = list(cfg["candidate_set"]["metals"])
        self.dEO = {m: float(cfg["descriptor"]["values_eV"][m]) for m in self.metals}
        self.kin = N2OKinetics(cfg)
        tg = cfg["tail_gas"]; pr = cfg["process"]; en = cfg["engineering"]; ec = cfg["economics"]
        self.P = float(tg["pressure_bar"]); self.yN2O = float(tg["yN2O_in"]); self.yO2 = float(tg["yO2"])
        self.flow_Nm3_h = float(tg["flow_Nm3_h"]); self.T_avail = float(tg["available_temperature_C"]) + 273.15
        self.cp = float(tg["cp_J_mol_K"]); self.Mgas = float(tg["gas_molar_mass_kg_mol"]); self.mu = float(tg["viscosity_Pa_s"])
        self.X = float(tg["conversion_target"])
        t = pr["temperature_C"]; self.T_grid_C = np.round(np.arange(float(t["start"]), float(t["stop"]) + 1e-9, float(t["step"])), 3)
        self.D_grid = [float(d) for d in pr["bed_diameter_m"]]
        self.loading = float(en["metal_loading_wt_fraction"]); self.disp = float(en["dispersion"]); self.rho_bed = float(en["bed_bulk_density_kg_m3"])
        self.dp = float(en["pellet_diameter_m"]); self.void = float(en["bed_void_fraction"]); self.V_cap = float(en["max_catalyst_bed_m3"]); self.dP_cap = float(en["max_pressure_drop_bar"])
        self.i = float(ec["discount_rate"]); self.life = int(ec["plant_life_y"]); self.cat_life = float(ec["catalyst_life_y"]); self.recovery = float(ec["metal_recovery_fraction"])
        self.cf = float(ec["capacity_factor"]); self.fuel = float(ec["fuel_USD_GJ"]); self.hrec = float(ec["heat_recovery_fraction"]); self.elec = float(ec["electricity_USD_MWh"]); self.eta_exp = float(ec["expander_efficiency"])
        self.r_fixed = float(ec["reactor_fixed_USD"]); self.r_var = float(ec["reactor_variable_USD"]); self.r_ref = float(ec["reactor_reference_m3"]); self.r_exp = float(ec["reactor_exponent"])
        pc = ec["pressure_capex"]; v = pc["vessel"]
        self.pc_ratio = float(pc["cost_index_current"]) / float(pc["cost_index_base"]); self.vK = [float(x) for x in v["K"]]; self.vAmin = float(v["A_min_m3"]); self.vAmax = float(v["A_max_m3"]); self.vExp = float(v["extrapolation_exponent"])
        self.vB2 = float(v["B2"]); self.vFm = float(v["Fm"]); self.vLD = float(v["L_over_D"]); self.vS = float(v["allowable_stress_x_weld_eff_bar"]); self.vCA = float(v["corrosion_allowance_m"]); self.vTmin = float(v["min_thickness_m"])
        # derived plant quantities
        self.crf = self.i * (1 + self.i) ** self.life / ((1 + self.i) ** self.life - 1)
        self.mol_s = self.flow_Nm3_h * NM3_MOL / 3600.0                       # total tail gas mol/s
        self.F_N2O = self.mol_s * self.yN2O                                   # mol/s N2O in
        self.sec_y = 365.0 * 86400.0 * self.cf
        self.t_N2O_y = self.F_N2O * self.X * MW_N2O * self.sec_y / 1000.0     # t N2O destroyed per year
        self.pN2O = self.P * self.yN2O; self.pO2 = self.P * self.yO2
        ar = cfg["atomic_reference"]; self.T_ref = float(ar["temperature_C"]) + 273.15
        self.pN2O_ref = float(ar["pressure_bar"]) * float(ar["yN2O"]); self.pO2_ref = float(ar["pressure_bar"]) * float(ar["yO2"])

    # ---------- kinetics / atomic ----------
    def tof(self, dEO: float, T: float) -> float:
        return self.kin.solve(dEO, T, self.pN2O, self.pO2)["TOF"]

    def atomic_logtof(self, dEO: float) -> float:
        return math.log10(max(self.kin.solve(dEO, self.T_ref, self.pN2O_ref, self.pO2_ref)["TOF"], 1e-300))

    # ---------- reactor / inventory ----------
    def sites_required(self, tof_inlet: float) -> float:
        """Isothermal PFR, rate first order in pN2O (dilute; theta_* set by pO2 which is ~constant): sites = F ln(1/(1-X)) / TOF_inlet."""
        return self.F_N2O * math.log(1.0 / (1.0 - self.X)) / tof_inlet

    def inventory(self, metal: str, sites_mol: float):
        mass = sites_mol * MW[metal] / 1000.0 / self.disp   # kg metal (harness_core.MW is g/mol)
        V = mass / self.loading / self.rho_bed              # m3 bed
        return mass, V

    def pressure_drop_bar(self, V: float, D: float, T: float) -> float:
        L = V / (math.pi * D * D / 4.0)
        rho = self.P * 1e5 * self.Mgas / (R * T)
        Q = self.mol_s * R * T / (self.P * 1e5)             # m3/s actual
        u = Q / (math.pi * D * D / 4.0)
        e = self.void
        dPdL = 150.0 * self.mu * u * (1 - e) ** 2 / (e ** 3 * self.dp ** 2) + 1.75 * rho * u * u * (1 - e) / (e ** 3 * self.dp)
        return dPdL * L / 1e5

    # ---------- cost pools (USD per t N2O destroyed) ----------
    def turton_cp0(self, A):
        Ac = min(max(A, self.vAmin), self.vAmax)
        K1, K2, K3 = self.vK; l = math.log10(Ac)
        cp = 10 ** (K1 + K2 * l + K3 * l * l)
        if A > self.vAmax: cp *= (A / self.vAmax) ** self.vExp
        return cp

    def vessel_pressure_premium(self, V: float) -> float:
        D = (4.0 * V / (math.pi * self.vLD)) ** (1.0 / 3.0)
        Pg = self.P - 1.0
        t = (Pg + 1.0) * D / (2.0 * (self.vS - 0.6 * (Pg + 1.0))) + self.vCA
        Fp = max(t / self.vTmin, 1.0)
        return self.turton_cp0(V) * self.vB2 * self.vFm * (Fp - 1.0) * self.pc_ratio * self.crf / self.t_N2O_y

    def pools(self, metal: str, T: float, D: float, alpha: float = 1.0, tof_value: float | None = None) -> dict | None:
        tofv = (self.tof(self.dEO[metal], T) if tof_value is None else tof_value) * alpha
        if tofv <= 0: return None
        sites = self.sites_required(tofv); mass, V = self.inventory(metal, sites)
        dP = self.pressure_drop_bar(V, D, T)
        metal_cost = mass * PRICE[metal] * (1.0 - self.recovery) / self.cat_life / self.t_N2O_y
        reactor_base = (self.r_fixed + self.r_var * (V / self.r_ref) ** self.r_exp) * self.crf / self.t_N2O_y
        vessel = self.vessel_pressure_premium(V)
        dT = max(0.0, T - self.T_avail)
        heat = self.mol_s * self.cp * dT * (1.0 - self.hrec) * self.sec_y / 1e9 * self.fuel / self.t_N2O_y
        # expander work lost: isothermal expansion work of the tail gas over dP at T, at expander efficiency
        W = self.mol_s * R * T * math.log(self.P / max(self.P - dP, 1e-6)) * self.eta_exp     # W
        pdrop = W * self.sec_y / 3.6e9 * self.elec / self.t_N2O_y
        total = metal_cost + reactor_base + vessel + heat + pdrop
        return dict(T_C=T - 273.15, D_m=D, TOF=tofv, sites_mol=sites, metal_kg=mass, V_m3=V, dP_bar=dP, L_m=V / (math.pi * D * D / 4),
                    metal_cost=metal_cost, reactor_base=reactor_base, vessel_pressure_premium=vessel, heating=heat, pressure_drop=pdrop, total=total,
                    feasible=bool(V <= self.V_cap and dP <= self.dP_cap))

    def optimize(self, metal: str, alpha: float = 1.0, dEO_override: float | None = None) -> dict:
        saved = self.dEO[metal]
        if dEO_override is not None: self.dEO[metal] = dEO_override
        try:
            best_u = None; best_f = None; envelope = []
            for TC in self.T_grid_C:
                T = float(TC) + 273.15; row_best = None; tof_T = self.tof(self.dEO[metal], T)
                for D in self.D_grid:
                    p = self.pools(metal, T, D, alpha, tof_value=tof_T)
                    if p is None: continue
                    if best_u is None or p["total"] < best_u["total"]: best_u = p
                    if p["feasible"] and (best_f is None or p["total"] < best_f["total"]): best_f = p
                    if p["feasible"] and (row_best is None or p["total"] < row_best["total"]): row_best = p
                envelope.append({"T_C": float(TC), "total": row_best["total"] if row_best else None, "V_m3": row_best["V_m3"] if row_best else None})
            return {"unconstrained": best_u, "feasible": best_f, "envelope": envelope}
        finally:
            self.dEO[metal] = saved

    # ---------- ranking metrics ----------
    @staticmethod
    def rank_metrics(atomic_order: list[str], econ_cost: dict[str, float | None], universe: list[str]) -> dict:
        """econ_cost: metal -> feasible cost or None (censored). Censored metals share the mean of the remaining ranks."""
        feas = [m for m in universe if econ_cost.get(m) is not None]
        eorder = sorted(feas, key=lambda m: econ_cost[m])
        erank = {m: i + 1 for i, m in enumerate(eorder)}
        n, nf = len(universe), len(feas)
        tie = (nf + 1 + n) / 2.0 if nf < n else None
        arank = {m: i + 1 for i, m in enumerate(atomic_order)}
        a = [arank[m] for m in universe]; e = [erank.get(m, tie) for m in universe]
        out = {"economic_order_feasible": eorder, "n_feasible": nf}
        out["full_spearman"] = float(spearmanr(a, e).statistic) if len(set(e)) > 1 else float("nan")
        out["full_kendall"] = float(kendalltau(a, e).statistic) if len(set(e)) > 1 else float("nan")
        for K in (3, 5):
            sub = atomic_order[:K]; ar = {m: i + 1 for i, m in enumerate(sub)}
            fs = [m for m in sub if m in erank]; fo = sorted(fs, key=lambda m: erank[m]); fr = {m: i + 1 for i, m in enumerate(fo)}
            tk = (len(fs) + 1 + K) / 2.0 if len(fs) < K else None
            ee = [fr.get(m, tk) for m in sub]; aa = [ar[m] for m in sub]
            out[f"top{K}_spearman"] = float(spearmanr(aa, ee).statistic) if len(set(ee)) > 1 else float("nan")
            out[f"top{K}_kendall"] = float(kendalltau(aa, ee).statistic) if len(set(ee)) > 1 else float("nan")
        out["atomic_winner"] = atomic_order[0]; out["economic_winner"] = eorder[0] if eorder else None
        out["atomic_winner_is_economic_winner"] = bool(eorder and eorder[0] == atomic_order[0])
        # pairwise inversions among feasible candidates
        inv = 0; pairs = 0; inv_list = []
        for x, y in combinations(feas, 2):
            pairs += 1
            if (arank[x] - arank[y]) * (erank[x] - erank[y]) < 0:
                inv += 1; inv_list.append((x, y))
        out["pairwise_inversions_feasible"] = inv; out["pairs_feasible"] = pairs
        out["pairwise_inversion_fraction"] = inv / pairs if pairs else float("nan"); out["inverted_pairs"] = inv_list
        # rolling top-K (raw over feasible-censored)
        rolling = []
        for K in range(3, n + 1):
            sub = atomic_order[:K]; ar = {m: i + 1 for i, m in enumerate(sub)}
            fs = [m for m in sub if m in erank]; fo = sorted(fs, key=lambda m: erank[m]); fr = {m: i + 1 for i, m in enumerate(fo)}
            tk = (len(fs) + 1 + K) / 2.0 if len(fs) < K else None
            ee = [fr.get(m, tk) for m in sub]; aa = [ar[m] for m in sub]
            rolling.append({"K": K, "rho": float(spearmanr(aa, ee).statistic) if len(set(ee)) > 1 else float("nan"), "n_feasible": len(fs)})
        out["rolling"] = rolling
        return out

    def deterministic(self) -> dict:
        act = {m: self.atomic_logtof(self.dEO[m]) for m in self.metals}
        atomic_order = sorted(self.metals, key=lambda m: act[m], reverse=True)
        det = {}
        for m in self.metals:
            o = self.optimize(m)
            ref = self.kin.solve(self.dEO[m], self.T_ref, self.pN2O_ref, self.pO2_ref)
            det[m] = {"dEO": self.dEO[m], "activity_logTOF": act[m], "theta_O_ref": ref["theta_O"], "Ea1_eV": ref["Ea1"], "Ea2_eV_ref": ref["Ea2"], **o}
        feas_cost = {m: (det[m]["feasible"]["total"] if det[m]["feasible"] else None) for m in self.metals}
        raw_cost = {m: det[m]["unconstrained"]["total"] for m in self.metals}
        metrics_feas = self.rank_metrics(atomic_order, feas_cost, self.metals)
        metrics_raw = self.rank_metrics(atomic_order, raw_cost, self.metals)
        return {"activity_order": atomic_order, "metals": det, "metrics_feasible_censored": metrics_feas, "metrics_raw_unconstrained": metrics_raw}

    def leverage(self, metal: str, alphas=(0.5, 1.0, 2.0)) -> dict:
        """Activity leverage: re-optimized cost at TOF x alpha; elasticity d ln C / d ln alpha around 1."""
        out = {}
        for a in alphas:
            o = self.optimize(metal, alpha=a)["feasible"]
            out[str(a)] = None if o is None else {"total": o["total"], "T_C": o["T_C"], "V_m3": o["V_m3"], "metal_cost": o["metal_cost"], "heating": o["heating"]}
        c05, c1, c2 = (out["0.5"] or {}).get("total"), (out["1.0"] or {}).get("total"), (out["2.0"] or {}).get("total")
        el = None
        if c05 and c2: el = (math.log(c2) - math.log(c05)) / (math.log(2.0) - math.log(0.5))
        out["elasticity_dlnC_dlnTOF"] = el
        return out

    def monte_carlo(self, atomic_order_det: list[str]) -> dict:
        u = self.cfg["uncertainty"]; n = int(u["draws"]); rng = np.random.default_rng(int(u["seed"])); hw = float(u["descriptor_uniform_half_width_eV"])
        crit = self.cfg["rank_preservation_criteria"]
        c1 = c2 = c_all = 0; top3_rhos = []; econ_win = {}; atom_win = {}; base = dict(self.dEO)
        for d in range(n):
            draw = {m: base[m] + rng.uniform(-hw, hw) for m in self.metals}
            act = {m: self.atomic_logtof(draw[m]) for m in self.metals}
            ao = sorted(self.metals, key=lambda m: act[m], reverse=True)
            cost = {}
            for m in self.metals:
                o = self.optimize(m, dEO_override=draw[m])["feasible"]; cost[m] = o["total"] if o else None
            mt = self.rank_metrics(ao, cost, self.metals)
            ok1 = mt["atomic_winner_is_economic_winner"]; ok2 = (not math.isnan(mt["top3_spearman"])) and mt["top3_spearman"] >= float(crit["C2_top3_spearman_min"])
            c1 += ok1; c2 += ok2
            allok = ok1 and ok2 and mt["top5_spearman"] >= float(crit["C3_top5_spearman_min"]) and mt["full_spearman"] >= float(crit["C4_full_set_spearman_min"]) \
                and mt["pairwise_inversion_fraction"] <= float(crit["C5_pairwise_inversion_fraction_max"]) and mt["full_kendall"] >= float(crit["C6_kendall_tau_full_min"])
            c_all += bool(allok); top3_rhos.append(mt["top3_spearman"])
            econ_win[mt["economic_winner"]] = econ_win.get(mt["economic_winner"], 0) + 1; atom_win[ao[0]] = atom_win.get(ao[0], 0) + 1
        return {"draws": n, "seed": int(u["seed"]), "half_width_eV": hw, "P_C1_winner_preserved": c1 / n, "P_C2_top3_rho_ge_0.5": c2 / n, "P_all_criteria": c_all / n,
                "top3_rho_mean": float(np.nanmean(top3_rhos)), "top3_rho_p10_p90": [float(np.nanpercentile(top3_rhos, 10)), float(np.nanpercentile(top3_rhos, 90))],
                "economic_winner_counts": econ_win, "atomic_winner_counts": atom_win, "top3_rho_draws": [float(x) for x in top3_rhos]}


def nh3_reference_metrics(results_json: Path) -> dict:
    """Recompute the same six metrics for NH3-FINAL-1.1 from its results.json (read-only)."""
    import json
    r = json.loads(results_json.read_text(encoding="utf-8"))["deterministic"]
    ao = r["activity_order"]; universe = ao
    feas = {m: (r["metals"][m]["feasible"]["total_cost"] if r["metals"][m]["feasible"] else None) for m in universe}
    raw = {m: r["metals"][m]["unconstrained"]["total_cost"] for m in universe}
    return {"feasible_censored": N2OHarness.rank_metrics(ao, feas, universe), "raw_unconstrained": N2OHarness.rank_metrics(ao, raw, universe),
            "cost_pools_Fe_Ru_Os": {m: r["metals"][m]["feasible"]["breakdown"] for m in ("Fe", "Ru", "Os")}}
