"""Measurement-uncertainty basis for the Re/TiO2 states of Gothe et al., ACS Catal. 2025, 15, 19111.

The paper and its SI report no error bars, standard deviations, repeat runs or carbon balance for the catalytic
data (Table 3 / Table 4 give single integer values; Methods: GC values after 1 h on stream were used). The
uncertainty used in the measurement Monte Carlo is therefore built from the paper's own numbers:

1. Reporting resolution (per catalyst, per quantity): integers in %, so a reported v means [v-0.5, v+0.5];
   "<1" means [0, 1).
2. Cross-detector consistency (21 Table-4 rows): STY (MeOH by GC-MS) must equal
   X_CO2 * S_MeOH * F_CO2 * M_MeOH / m_Re (CO2 by GC-TCD), with F_CO2 from GHSV, 290 mg catalyst and the
   CO2:H2 ratio. The log residual scatter beyond what integer rounding explains is a relative measurement error
   r_X, assigned entirely to CO2 conversion (the difference measurement F_in - F_out).
3. Carbon closure (21 rows): Eq. 3 normalises each selectivity by CO2 consumed, so the reported selectivities
   are not forced to sum to 100 %. Their sum scatter compared with what rounding of three entries explains
   bounds any extra selectivity error that does not conserve the sum.
4. Selectivity transfer (MeOH <-> CH4, sum-conserving, invisible to closure): the 11 Table-4 runs of one catalyst
   (5 wt% Re, 500 C prereduction, 200 C) at different GHSV, pressure and CO2:H2 give S_MeOH = 96-99 %. Their SD,
   which also contains genuine condition effects, is an upper bound on run-to-run selectivity noise; the part
   beyond integer rounding is sigma_delta, applied as a MeOH -> CH4 transfer.

Writes uncertainty_basis.json.
"""
import csv
import json
import os

import numpy as np
from scipy.optimize import minimize

HERE = os.path.dirname(os.path.abspath(__file__))
MW_MEOH = 32.04186
VM_STP = 22414.0      # mL/mol, GHSV taken at 0 C / 1 atm; a common scale error is absorbed by the fitted mean
CAT_G = 0.290


def _val(s):
    return (0.5, 1.0 / 12.0, True) if s.startswith("<") else (float(s), 1.0 / 12.0, False)


def basis():
    rows = list(csv.DictReader(open(os.path.join(HERE, "table4_gothe2025.csv"), encoding="utf-8")))
    res, var_round, closure, closure_var = [], [], [], []
    for r in rows:
        a, b = map(float, r["CO2_H2"].split(":"))
        f_co2 = float(r["GHSV_1e3_mL_gcat_h"]) * 1e3 * CAT_G * a / (a + b) / VM_STP
        m_re = CAT_G * float(r["Re_wt"]) / 100.0
        x, s, sty = float(r["X_CO2_pct"]), float(r["S_MeOH_pct"]), float(r["STY_gMeOH_gRe_h"])
        res.append(np.log(sty / (x / 100 * s / 100 * f_co2 * MW_MEOH / m_re)))
        var_round.append(((0.5 / sty) ** 2 + (0.5 / x) ** 2 + (0.5 / s) ** 2) / 3.0)
        parts = [_val(r[k]) for k in ("S_MeOH_pct", "S_CO_pct", "S_CH4_pct")]
        closure.append(sum(p[0] for p in parts))
        closure_var.append(sum(p[1] for p in parts))
    res, var_round = np.array(res), np.array(var_round)

    def nll(p, idx):
        mu, ln_r = p
        v = var_round[idx] + np.exp(2 * ln_r)
        return 0.5 * np.sum(np.log(v) + (res[idx] - mu) ** 2 / v)

    def fit(idx):
        o = minimize(nll, x0=[0.0, np.log(0.03)], args=(idx,), method="Nelder-Mead",
                     options=dict(xatol=1e-8, fatol=1e-10, maxiter=4000))
        return float(o.x[0]), float(np.exp(o.x[1]))

    series = [float(r["S_MeOH_pct"]) for r in rows if r["Re_wt"] == "5" and r["T_prered_C"] == "500"
              and r["T_rxn_C"] == "200"]
    sd_series = float(np.std(series, ddof=1))
    sigma_delta = float(np.sqrt(max(sd_series ** 2 - 1.0 / 12.0, 0.0)))
    all_idx = np.arange(len(res))
    mu_all, r_all = fit(all_idx)
    z = (res - mu_all) / np.sqrt(var_round + r_all ** 2)
    out_idx = int(np.argmax(np.abs(z)))
    keep = all_idx[all_idx != out_idx]
    mu_k, r_k = fit(keep)
    four = [2, 3, 9, 10]   # the four D01 states (500 C prereduction, 10k GHSV)
    closure = np.array(closure)
    excess_closure_var = float(np.var(closure - 100.0, ddof=0) - np.mean(closure_var))
    return {
        "source": "Gothe et al., ACS Catal. 2025, 15, 19111-19126, Table 4 (21 rows; Table 3 rows are a subset)",
        "n_rows": len(res),
        "log_residual_STY_vs_X_S_flow": [float(v) for v in res],
        "log_residual_sd_raw": float(np.std(res, ddof=1)),
        "log_residual_sd_four_D01_states": float(np.std(res[four], ddof=1)),
        "rounding_only_rms_sd": float(np.sqrt(np.mean(var_round))),
        "mle_all_rows": {"mean_log_ratio": mu_all, "r_excess_relative_sd": r_all},
        "largest_outlier_row_index": out_idx,
        "largest_outlier_row": rows[out_idx],
        "mle_without_outlier": {"mean_log_ratio": mu_k, "r_excess_relative_sd": r_k},
        "carbon_closure_sum_pct": {"mean": float(closure.mean()), "sd": float(closure.std(ddof=1)),
                                   "min": float(closure.min()), "max": float(closure.max()),
                                   "rounding_expected_sd": float(np.sqrt(np.mean(closure_var))),
                                   "excess_variance_pct2": excess_closure_var},
        "selectivity_series_5wtRe_500_200": {"S_MeOH_pct": series, "sd_pct": sd_series,
                                             "sigma_delta_pct_excess_over_rounding": sigma_delta},
        "adopted": {
            "r_X_relative_sd": r_all,
            "sigma_delta_pct": sigma_delta,
            "note": "r_X = MLE excess cross-detector scatter over all 21 rows (outlier kept, conservative); "
                    "carbon closure shows no sum-changing selectivity error beyond rounding (excess variance <= 0); "
                    "sum-conserving MeOH<->CH4 transfer noise sigma_delta from the 11-run single-catalyst series "
                    "(upper bound: includes real GHSV/P/ratio effects)",
        },
    }


if __name__ == "__main__":
    b = basis()
    json.dump(b, open(os.path.join(HERE, "uncertainty_basis.json"), "w", encoding="utf-8"), indent=1)
    print(json.dumps({k: b[k] for k in ("log_residual_sd_raw", "log_residual_sd_four_D01_states",
                                        "rounding_only_rms_sd", "mle_all_rows", "mle_without_outlier",
                                        "carbon_closure_sum_pct", "largest_outlier_row",
                                        "selectivity_series_5wtRe_500_200")}, indent=1))
