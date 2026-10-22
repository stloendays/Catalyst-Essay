"""NH3-FINAL-1.3 harness: the NH3-FINAL-1.2 harness with sourced separator VLE and compression (PREREGISTRATION.md).

Only `self_consistent_process_state` changes. Separator vapour NH3 = E(T_sep, P) p_sat(T_sep) / P with ln E
interpolated in the measured BASF table (Appl 2011, Ullmann's, Table 5); fresh gas compressed from 30 bar in
equal-ratio polytropic stages (ratio <= 2.2) with intercooling to 40 C; recycle compressed across the 9.2-bar loop
pressure drop of the Krupp-Uhde flowsheet; eta_p 0.78, kappa 1.40.

    import harness13 as H13
    h = H13.build()                    # 1.3 harness, F_CAL recalibrated on the 1.2 definition
"""
from __future__ import annotations

import csv
import math
import os
import re
import sys
from pathlib import Path

import numpy as np

os.environ.setdefault("NH3_MODEL", "1.2")
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "analysis"))
import nh3_model as NM  # noqa: E402

hc = NM.core()
REF = REPO / "analysis" / "validation_nh3_plant_2026_10_13" / "reference_values.csv"
T_IC = 313.15                 # intercooler / circulator suction temperature, K
ETA_P = 0.78
KAPPA = 1.40
R_STAGE_MAX = 2.2
DP_RECYCLE_13 = 9.2           # bar, Krupp-Uhde 1,500 t/d flowsheet (Appl 2011)
CAL_STATE = (400.0, 80.0, -35.0)


def basf_table():
    """{(T_C, P_MPa): y_NH3 mol%} from the registered reference ledger (APPL11_A1 Table 5)."""
    out = {}
    for r in csv.DictReader(REF.open(encoding="utf-8")):
        if r["ref_id"] != "APPL11_A1" or r["table_or_figure"] != "Table 5":
            continue
        if "NH3 concentration at saturation" not in r["record"]:
            continue
        m = re.search(r"at t\s*=\s*(-?\d+)\s*C,\s*p\s*=\s*(\d+)\s*MPa", r["printed_value_and_unit"])
        if m:
            out[int(m.group(1)), int(m.group(2))] = float(r["value"])
    return out


def psat_bar(T_C):
    T = T_C + 273.15
    a, b, c = (3.18757, 506.713, -80.78) if T < 239.6 else (4.86886, 1113.928, -10.409)
    return 10.0 ** (a - b / (T + c))


TAB = basf_table()
TS = sorted({t for t, _ in TAB})
PS = sorted({p for _, p in TAB})
assert len(TAB) == len(TS) * len(PS) == 64, len(TAB)
LNE = np.array([[math.log(TAB[t, p] / (100.0 * psat_bar(t) / (10.0 * p))) for p in PS] for t in TS])  # [T, P]


def enhancement(T_C, P_bar):
    """E = y_measured / (p_sat / P), bilinear in (T, P) on ln E; ln E -> 0 linearly as P -> 0 below 5 MPa;
    temperatures below -30 C take the -30 C row, above 40 C the 40 C row."""
    t = min(max(T_C, TS[0]), TS[-1])
    pm = P_bar / 10.0
    i = max(0, min(len(TS) - 2, int(np.searchsorted(TS, t) - 1)))
    ft = (t - TS[i]) / (TS[i + 1] - TS[i])
    row = (1 - ft) * LNE[i] + ft * LNE[i + 1]
    if pm <= PS[0]:
        return math.exp(row[0] * pm / PS[0])
    pm = min(pm, PS[-1])
    j = max(0, min(len(PS) - 2, int(np.searchsorted(PS, pm) - 1)))
    fp = (pm - PS[j]) / (PS[j + 1] - PS[j])
    return math.exp((1 - fp) * row[j] + fp * row[j + 1])


def y_sep(T_C, P_bar):
    return enhancement(T_C, P_bar) * psat_bar(T_C) / P_bar


def poly_work_J_mol(p_in, p_out, stages=None):
    """Polytropic compression work per mol, equal-ratio stages with intercooling to T_IC."""
    if p_out <= p_in:
        return 0.0
    n = stages or max(1, math.ceil(math.log(p_out / p_in) / math.log(R_STAGE_MAX)))
    r = (p_out / p_in) ** (1.0 / n)
    e = (KAPPA - 1.0) / (KAPPA * ETA_P)
    return n * hc.R * T_IC / e * (r ** e - 1.0)


class NH3Harness13(hc.NH3Harness):
    def self_consistent_process_state(self, C, P, Tsep):
        T = C + 273.15
        if psat_bar(Tsep) >= P:
            return None
        ysep = y_sep(Tsep, P)
        if ysep > self.RECYCLE_NH3_CAP or ysep >= 1.0:
            return None
        gg = self.ctx.gas_G(T); Gform = gg['NH3'] - 0.5 * gg['N2'] - 1.5 * gg['H2']
        Kp = math.exp(-2.0 * Gform / (hc.K_B_EV * T)); ratio = ysep / (1.0 - ysep)
        phi = hc.newton_cooper_phi(T, P) if self.FUGACITY_IN_LOOP else None

        def fixed_point(X):
            nN = 0.5 / X; nH = 1.5 / X; nA = ratio * 2.0 * (1.0 - X) / X
            xi_eq = self.equilibrium_extent(Kp, P, nN, nH, nA, phi); return X - self.APPROACH_EQ * (xi_eq / nN)
        lo, hi = 1e-6, 0.999
        if fixed_point(lo) >= 0.0 or fixed_point(hi) <= 0.0:
            return None
        X = hc.brentq(fixed_point, lo, hi, xtol=1e-10, rtol=1e-9, maxiter=100); Xeq = X / self.APPROACH_EQ
        reactive_recycle = 2.0 * (1.0 - X) / X; nh3_recycle = ratio * reactive_recycle; recycle_total = reactive_recycle + nh3_recycle
        reactive_in = 2.0 / X; total_in = reactive_in + nh3_recycle
        yN = (0.5 / X) / total_in; yH = (1.5 / X) / total_in; yA = nh3_recycle / total_in
        cond = self.ctx.condition(T, P * yN, P * yH, max(P * yA, 1e-12))
        if P <= DP_RECYCLE_13:
            return None
        to_usd = self.n_per_t / 3.6e9 * self.ELECTRICITY
        fresh = 2.0 * poly_work_J_mol(self.FRESH_FEED_PRESSURE_BAR, P) * to_usd
        recycle_comp = recycle_total * poly_work_J_mol(P - DP_RECYCLE_13, P, stages=1) * to_usd
        refrig = self.refriger_cost(Tsep); inlet_Nm3_h = self.nh3_mol_s * total_in * 0.022414 * 3600.0
        comp_capex = self.compressor_capex_USD_t(fresh) + self.compressor_capex_USD_t(recycle_comp)
        return dict(T_C=float(C), P_bar=float(P), Tsep_C=float(Tsep), X=float(X), Xeq=float(Xeq), ysep=float(ysep),
                    recycle_total=float(recycle_total), inlet_Nm3_h=float(inlet_Nm3_h), fresh_comp=float(fresh),
                    recycle_comp=float(recycle_comp), refrigeration=float(refrig), compressor_capex=float(comp_capex),
                    process_cost=float(fresh + recycle_comp + refrig + comp_capex), condition=cond)


def state_logtof(h, EN):
    return h.direct_state_logtof(EN)


def build(recalibrate=True):
    h12 = NM.harness()
    h = NH3Harness13(NM.cfg(), NM.root())
    if recalibrate:
        j12 = next(i for i in range(h12.NSTATE) if (h12.state_T[i], h12.state_P[i], h12.state_Tsep[i]) == CAL_STATE)
        j13 = next(i for i in range(h.NSTATE) if (h.state_T[i], h.state_P[i], h.state_Tsep[i]) == CAL_STATE)
        l12 = h12.process_states[j12]["condition"].logtof(hc.EN0_CANON["Fe"])
        l13 = h.process_states[j13]["condition"].logtof(hc.EN0_CANON["Fe"])
        h.F_CAL = h12.F_CAL * 10.0 ** (l12 - l13)
    return h
