"""Ammonia within-paper comparisons with Fe and Ru extrapolated on measured rate laws (PREREGISTRATION.md).

Fe: Keestra et al. 2025 Model 3 (keestra_fe.py), states 1-324 bar. Ru: Rossetti et al. 2006 (kinetics.rate_ru_rossetti),
states 50-100 bar; variant Cholewa et al. 2024 eqn (12) as printed (Ru/CeO2), states 11-81 bar (Addendum 1). Co and Ni keep their frozen
descriptor cost. Each Fe or Ru entry carries one activity factor that reproduces its printed rate per kg catalyst at its
laboratory T, P, H2/N2 = 3 and NH3 fraction min(y_out/2, y_eq/2), the composition convention of the frozen mapping.
Catalyst amount per process state by isothermal plug flow; cost = metal (no recovery) + reactor + process, V <= 90 m3
(kinetics_swap.amount / costs). Because the activity factor only scales the rate, the amount per state is computed once
per law and divided by each entry's factor.

    set NH3_MODEL=1.2
    D:\\Research\\CatalystForge\\.venv\\Scripts\\python.exe -X utf8 measured_field.py
        -> summary.json, candidates_measured.csv, group_metrics_<variant>.csv, gates.json
"""
from __future__ import annotations

import json
import math
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

assert os.environ.get("NH3_MODEL") == "1.2", "run with NH3_MODEL=1.2"
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
AN = REPO / "analysis"
for p in (AN, AN / "nh3_staged_converter_2026_10_12", AN / "nh3_fe_inrange_kinetics_2026_10_19",
          AN / "nh3_field_2026_10_06"):
    sys.path.insert(0, str(p))

import nh3_model as NM  # noqa: E402
import kinetics as K  # noqa: E402
import kinetics_swap as KS  # noqa: E402
import keestra_fe as KF  # noqa: E402
_argv, sys.argv = sys.argv, sys.argv[:1]
import run_field_chain as F  # noqa: E402
sys.argv = _argv

hc = NM.core()
SRC = AN / "nh3_field_expansion_2026_10_12" / "nh3_1_2" / "runs" / "pooled_vf_screen" / "candidates_printed.csv"
R_J = 8.31446261815324
BAR_PER_ATM = 1.01325
FUSED_W, FUSED_RHO, SUP_RHO = 0.7151, 2500.0, 1000.0
UMOL_GCAT_H = 1e-6 / 1e-3 / 3600.0          # umol g-1 h-1 -> mol kg-1 s-1

# Cholewa et al. 2024, Sustain. Energy Fuels 8, 2245, eqn (12) and Table 3 (Ru/CeO2)
CH = dict(k0=3.49e8, EA=1.06e5, dH2=-8.71e4, dS2=-80.1, f2=0.116, dH3=-1.184e4, dS3=-143.0, f3=0.414, alpha=0.25)

LAWS = {   # name: (metal, fitted P bar, fitted T C)
    "Fe_Keestra": ("Fe", (1.0, 324.0), (251.0, 550.0)),
    "Ru_Cholewa": ("Ru", (11.0, 81.0), (350.0, 450.0)),
    "Ru_Rossetti": ("Ru", (50.0, 100.0), (370.0, 460.0)),
}


def fugacities_bar(T, P_bar, yN, yH, yA):
    aN, aH, aA = K.activities(T, P_bar, yN, yH, yA)
    return aN * BAR_PER_ATM, aH * BAR_PER_ATM, aA * BAR_PER_ATM


def rate_ru_cholewa(T, P_bar, yN, yH, yA):
    """mol NH3 per kg catalyst per s (Ru/CeO2 of the source)."""
    T = np.asarray(T, dtype=float)
    fN, fH, fA = fugacities_bar(T, P_bar, yN, yH, yA)
    Keq = KF.Kf_GB(T)                                         # 1/2 N2 + 3/2 H2 = NH3, bar^-1
    k2 = CH["k0"] * np.exp(-CH["EA"] / (R_J * T))
    K2 = np.exp(-CH["dH2"] / (R_J * T) + CH["dS2"] / R_J)
    K3 = np.exp(-CH["dH3"] / (R_J * T) + CH["dS3"] / R_J)
    a = CH["alpha"]
    num = np.sqrt(fN) * Keq * (fH ** 1.5 / fA) ** a - (fA / fH ** 1.5) ** (1.0 - a)
    return k2 * num / (1.0 + K2 * fH ** (1.5 * CH["f2"]) + K3 * fA ** CH["f3"])


def rate_fe_keestra(T, P_bar, yN, yH, yA):
    return KF.rate(T, P_bar, yN, yH, yA, catalyst="KM1R_1964", eq="source", per="kg")


def rate_ru_rossetti(T, P_bar, yN, yH, yA):
    return K.rate_ru_rossetti(T, P_bar, yN, yH, yA)


RATE = {"Fe_Keestra": rate_fe_keestra, "Ru_Cholewa": rate_ru_cholewa, "Ru_Rossetti": rate_ru_rossetti}


def lab_rate(law, T_C, P_bar, y):
    T = T_C + 273.15
    return float(RATE[law](np.array([T]), np.array([P_bar]), np.array([(1 - y) / 4]), np.array([3 * (1 - y) / 4]),
                           np.array([y]))[0])


def gates(h, st, c):
    g = {}
    gm, s = F.aggregate(c, label="frozen descriptor", boot=False)
    g["1_frozen_12_of_44"] = dict(groups=s["groups"], mismatch=s["top1_mismatch_groups"],
                                  ok=(s["groups"], s["top1_mismatch_groups"]) == (44, 12))
    V = KS.amount(st, lambda T, P, a, b, y: KF.rate(T, P, a, b, y, catalyst="KM1R_1964", eq="source", per="m3"), h, "plug")
    tot, _ = KS.costs(h, V, V * FUSED_W * FUSED_RHO, hc.PRICE["Fe"], 1.0)
    fe = float(np.min(np.where(h.state_P <= 324.0 + 1e-6, tot, np.inf)))
    g["2_keestra_fe_benchmark"] = dict(value=fe, target=15.307473, ok=abs(fe / 15.307473 - 1) < 1e-6)
    T = 673.15
    y_eq = F.SC.y_eq_exp_fugacity(h, T, 75.0)
    r_eq = lab_rate("Ru_Rossetti", 400.0, 75.0, y_eq)
    r_mid = lab_rate("Ru_Rossetti", 400.0, 75.0, 0.5 * y_eq)
    g["3_rossetti_zero_at_equilibrium"] = dict(rel=abs(r_eq / r_mid), ok=abs(r_eq / r_mid) < 1e-3)
    yA = 0.002
    r15 = float(rate_ru_cholewa(T, 45.0, (1 - yA) / 2.5, 1.5 * (1 - yA) / 2.5, yA))
    r30 = float(rate_ru_cholewa(T, 45.0, (1 - yA) / 4.0, 3.0 * (1 - yA) / 4.0, yA))
    g["cholewa_as_printed_H2N2_ratio_info"] = dict(ratio_15_over_30=r15 / r30, source_fig5b="> 1.8", ok=True)
    return g


def main():
    c = pd.read_csv(SRC, keep_default_na=False, na_values=[""])
    c["fused"] = c.fused.astype(str).str.lower().isin(("true", "1"))
    h = KS.build(False)
    st = KS.state_arrays(h)
    G = gates(h, st, c)
    print(json.dumps(G, indent=1), flush=True)
    assert all(v["ok"] for v in G.values()), "gate failed"

    base = {law: KS.amount(st, RATE[law], h, "plug") for law in LAWS}      # kg catalyst per state at activity 1
    P, T = h.state_P, h.state_T
    in_fit = {law: (P >= LAWS[law][1][0] - 1e-6) & (P <= LAWS[law][1][1] + 1e-6)
              & (T >= LAWS[law][2][0] - 1e-6) & (T <= LAWS[law][2][1] + 1e-6) for law in LAWS}

    def entry_cost(r, law, restrict=True):
        y = min(0.5 * r.y_out, 0.5 * r.y_eq_exp)
        rl = lab_rate(law, r.T_C, r.P_MPa * 10.0, y)
        if not (rl > 0):
            return None, None, None
        A = r.rate_umol_gcat_h * UMOL_GCAT_H / rl
        assert abs(A * rl / (r.rate_umol_gcat_h * UMOL_GCAT_H) - 1) < 1e-9
        w, rho = (FUSED_W, FUSED_RHO) if r.fused else (r.metal_wt_pct / 100.0, SUP_RHO)
        M = base[law] / A
        tot, _ = KS.costs(h, M / rho, M * w, hc.PRICE[r.metal], 1.0)
        t = np.where(in_fit[law], tot, np.inf) if restrict else tot
        i = int(np.argmin(t))
        if not np.isfinite(t[i]):
            return None, A, None
        return float(t[i]), A, (float(T[i]), float(P[i]), float(h.state_Tsep[i]), float(M[i] / rho))

    rows = []
    for idx, r in c.iterrows():
        d = dict(idx=idx)
        lab_P, lab_T = r.P_MPa * 10.0, r.T_C
        for variant, law_of, restrict in (("primary", {"Fe": "Fe_Keestra", "Ru": "Ru_Rossetti"}, True),
                                          ("ru_cholewa", {"Fe": "Fe_Keestra", "Ru": "Ru_Cholewa"}, True),
                                          ("ru_unrestricted", {"Fe": "Fe_Keestra", "Ru": "Ru_Rossetti"}, False)):
            law = law_of.get(r.metal)
            if law is None:
                d[f"cost_{variant}"] = r.cost_USD_t
                continue
            cost, A, opt = entry_cost(r, law, restrict if r.metal == "Ru" else True)
            d[f"cost_{variant}"] = cost
            if variant == "primary":
                d.update(law=law, activity_factor=A, lab_in_fit=bool(LAWS[law][1][0] - 1e-6 <= lab_P <= LAWS[law][1][1] + 1e-6
                                                                     and LAWS[law][2][0] - 1e-6 <= lab_T <= LAWS[law][2][1] + 1e-6))
                if opt:
                    d.update(meas_T_opt_C=opt[0], meas_P_opt_bar=opt[1], meas_Tsep_opt_C=opt[2], meas_V_m3=opt[3])
        rows.append(d)
    m = pd.DataFrame(rows).set_index("idx")
    cm = c.join(m)
    cm["lab_in_fit"] = cm.lab_in_fit.astype("boolean").fillna(True)        # Co/Ni: descriptor, no fitted range

    def agg(frame, col, label):
        gm, s = F.aggregate(frame, cost_col=col, label=label, boot=True)
        if len(gm):
            mm = gm[gm.top1_mismatch]
            s["regret_gt5pct_groups"] = int((mm.regret > 0.05).sum())
        return gm, s

    out, gms = {}, {}
    fe_ru_only = cm.groupby("group").metal.transform(lambda s: set(s) <= {"Fe", "Ru"})
    spec = {
        "frozen_descriptor": (cm, "cost_USD_t"),
        "primary_measured": (cm, "cost_primary"),
        "a_ru_cholewa_as_printed": (cm, "cost_ru_cholewa"),
        "b_without_Co_Ni": (cm[cm.metal.isin(["Fe", "Ru"])], "cost_primary"),
        "c_lab_inside_fitted_range": (cm[cm.lab_in_fit], "cost_primary"),
        "d_ru_states_unrestricted": (cm, "cost_ru_unrestricted"),
        "e_groups_only_Fe_Ru": (cm[fe_ru_only], "cost_primary"),
        "frozen_descriptor_groups_only_Fe_Ru": (cm[fe_ru_only], "cost_USD_t"),
    }
    for k, (fr, col) in spec.items():
        gms[k], out[k] = agg(fr, col, k)
        gms[k].to_csv(HERE / f"group_metrics_{k}.csv", index=False, float_format="%.6g")
    # group-by-group comparison of the frozen and primary leaders
    a, b = gms["frozen_descriptor"].set_index("group"), gms["primary_measured"].set_index("group")
    j = a[["top1_mismatch", "mismatch_kind", "regret"]].join(b[["top1_mismatch", "mismatch_kind", "regret"]],
                                                             lsuffix="_frozen", rsuffix="_measured", how="outer")
    j.to_csv(HERE / "group_comparison.csv", float_format="%.6g")
    out["transitions"] = {f"{x}->{y}": int(((j.top1_mismatch_frozen == x) & (j.top1_mismatch_measured == y)).sum())
                          for x in (True, False) for y in (True, False)}
    out["entries"] = dict(total=int(len(cm)), by_law=cm.law.fillna("descriptor (Co/Ni)").value_counts().to_dict(),
                          lab_outside_fitted_range=int((~cm.lab_in_fit).sum()),
                          infeasible_primary=int(cm.cost_primary.isna().sum()))
    out["gates"] = G
    cm.to_csv(HERE / "candidates_measured.csv", index=False, float_format="%.6g")
    (HERE / "summary.json").write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8")
    for k in spec:
        s = out[k]
        ci = s.get("bootstrap_papers", {}).get("mismatch_fraction_ci95")
        print(f"{k:40s} {s.get('top1_mismatch_groups')}/{s.get('groups')}  >5%: {s.get('regret_gt5pct_groups')}  CI {ci}")
    print(out["transitions"], out["entries"])


if __name__ == "__main__":
    main()
