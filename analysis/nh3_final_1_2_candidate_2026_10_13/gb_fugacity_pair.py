"""Exploratory reaction-equilibrium closure for the measured Fe/Ru pair.

Compare GB ideal-gas loop states with GB+Newton-Cooper reaction fugacity
closure over the SAME 50-300 bar process-pressure grid. Measured Ru/C and
Fe rate laws are unchanged, as are compression, separator, capital, and
metal-ownership accounting. This is NOT a fully nonideal EOS plant model.

The parent frozen NH3 harness is never patched on disk.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import brentq

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "analysis" / "nh3_staged_converter_2026_10_12"))
import kinetics as K  # noqa: E402
import kinetics_swap as S  # noqa: E402

P_LO, P_HI = 50.0, 300.0

class SharedPressureWindow(S.hc.NH3Harness):
    """Same fixed pressure mask for old and new equilibrium physics."""
    def _init_controls(self):
        super()._init_controls()
        self.P_GRID_BAR = np.asarray([p for p in self.P_GRID_BAR if P_LO <= p <= P_HI], dtype=float)
        assert 90.0 in self.P_GRID_BAR and 145.0 in self.P_GRID_BAR
        assert len(self.P_GRID_BAR) > 30

class GBFugacityReaction(SharedPressureWindow):
    """Nonideal reaction equilibrium with Newton-Cooper fugacities.

    This overrides the equilibrium extent only. N2/H2/NH3 partial-pressure
    formation for MKM remains ideal; those descriptor rates are not used
    for the *measured Fe/Ru* branch evaluated here.
    """
    def self_consistent_process_state(self, C, P, Tsep):
        self._current_T_K = C + 273.15
        return super().self_consistent_process_state(C, P, Tsep)

    def equilibrium_extent(self, Kp, P, nN, nH, nA):
        T = self._current_T_K
        phiN, phiH, phiA = map(float, K.fugacity_coefficients(T, P / K.BAR_PER_ATM))
        if not all(math.isfinite(x) and x > 0 for x in (phiN, phiH, phiA)):
            raise ArithmeticError(f"nonphysical fugacity coefficients at {T} K, {P} bar")
        def Q(xi):
            nn, hh, aa = nN-xi, nH-3.0*xi, nA+2.0*xi
            tot = nn+hh+aa
            fN, fH, fA = nn/tot*P*phiN, hh/tot*P*phiH, aa/tot*P*phiA
            return fA*fA / (fN*fH**3)
        hi = min(nN, nH/3.0)*(1.0-1e-10)
        if Q(0.0) >= Kp:
            return 0.0
        return brentq(lambda z: Q(z)-Kp, 0.0, hi, xtol=1e-12, rtol=1e-10, maxiter=100)

def _create(cls):
    return cls(S.CFG, S.ROOT)

def _clear_profile(d):
    d.pop("_profile", None)
    return S._clean(d)

def run():
    # The GB formation standard matches the published Ka in the rate law.
    original = S.hc.KineticContext.gas_G
    S.hc.KineticContext.gas_G = S._corrected_gas_G
    try:
        ideal = _create(SharedPressureWindow)
        nonideal = _create(GBFugacityReaction)
    finally:
        S.hc.KineticContext.gas_G = original
    # The self_consistent_process_state is a method in both objects, so
    # the thermochemical monkeypatch must be installed DURING construction.
    # Measured pair kinetics only uses K.rate_* thereafter.
    assert ideal.NSTATE > 1000 and nonideal.NSTATE > 1000

    # Independent stoichiometric check at 90 bar / 425 C, 1:3 N2/H2.
    T, P = 698.15, 90.0
    kp = math.exp(-2*S.gb_dG(T)/(S.hc.K_B_EV*T))
    nonideal._current_T_K = T
    extent = nonideal.equilibrium_extent(kp, P, 1.0, 3.0, 0.0)
    ycalc = 2*extent / (4.0-2*extent)
    ysource = float(K.equilibrium_y_nh3(T, P, fugacity=True))
    if abs(ycalc-ysource) > 1e-9:
        raise AssertionError(f"Reaction fugacity closure mismatch: {ycalc} vs {ysource}")

    results = {}
    for name, h in (("GB_ideal_loop", ideal), ("GB_NC_reaction_equilibrium", nonideal)):
        r = S.evaluate(h, S.state_arrays(h), "plug", "source", fcal_target=1.0)
        results[name] = _clear_profile(r)
        print(name, "states", h.NSTATE, "Fe", r["Fe"]["cost"],
              "Ru benchmark", r["Ru_benchmark"]["cost"],
              "alpha", r["Ru_activity_multiple_for_parity"], flush=True)
    a, b = results["GB_ideal_loop"], results["GB_NC_reaction_equilibrium"]
    rows = {}
    for key in ("Fe", "Ru_benchmark"):
        rows[key] = {
            "ideal": a[key],
            "NC_equilibrium": b[key],
            "delta_cost_USD_t": b[key]["cost"]-a[key]["cost"],
        }
    for key in ("cashflow 0% r 0.9555", "cashflow 12% r 0.9555"):
        x, y = a["Ru_C_supported"][key], b["Ru_C_supported"][key]
        rows["supported_"+key] = {
            "ideal_Ru_minus_Fe_global": x["Ru_minus_Fe_global"],
            "NC_Ru_minus_Fe_global": y["Ru_minus_Fe_global"],
            "ideal_Ru_minus_Fe_KAAP": x["Ru_minus_Fe_KAAP"],
            "NC_Ru_minus_Fe_KAAP": y["Ru_minus_Fe_KAAP"],
        }
    report = {
        "status": "UNFROZEN controlled fugacity reaction-equilibrium sensitivity",
        "pressure_range_bar": [P_LO, P_HI],
        "states_ideal": ideal.NSTATE,
        "states_NC": nonideal.NSTATE,
        "independent_gb_equilibrium_check_90bar_425C": {
            "NC_from_extent": ycalc, "NC_from_published_Ka": ysource},
        "rows": rows,
        "full_results": results,
        "limitations": [
            "Single gas standard Gibbs (GB) now used in ideal and nonideal reaction equilibrium; Ru/C and Fe rates use Newton-Cooper activities",
            "Separators, compressors, heat management and axial temperature profiles are NOT separately recalibrated with nonideal fugacity",
            "Nonideal coefficients are Newton-Cooper correlations, not a validated mixture EOS",
            "Ru/C fitted pressure interval is 50-100 bar; joint 50-300 bar grid still contains extrapolated rates, and 8 wt% Ru/C productivity remains hypothesized",
            "Results are not canonical NH3-FINAL-1.2 and cannot change existing manuscript without source review",
        ],
    }
    return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out", type=Path, required=True)
    args=p.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    d=run()
    (args.out/"gb_nc_pair.json").write_text(json.dumps(d, indent=2, allow_nan=False)+"\n", encoding="utf-8")
    lines=[
        "# GB ideal-vs-fugacity reactor-equilibrium sensitivity",
        "",
        "**UNFROZEN; same 50-300 bar pressure envelope, published Fe/Ru/C measured rate laws, unchanged modelled loop equipment and finance.**",
        "",
        "| Quantity | GB ideal loop | GB + Newton-Cooper reaction equilibrium |",
        "|---|---:|---:|",
        f'| Fe minimum (USD/t) | {d["rows"]["Fe"]["ideal"]["cost"]:.3f} | {d["rows"]["Fe"]["NC_equilibrium"]["cost"]:.3f} |',
        f'| Benchmark Ru minimum (USD/t) | {d["rows"]["Ru_benchmark"]["ideal"]["cost"]:.3f} | {d["rows"]["Ru_benchmark"]["NC_equilibrium"]["cost"]:.3f} |',
    ]
    for key in ("cashflow 0% r 0.9555", "cashflow 12% r 0.9555"):
        row=d["rows"]["supported_"+key]
        lines.append(f'| Supported Ru/C vs Fe, {key} (USD/t) | {row["ideal_Ru_minus_Fe_global"]:+.3f} | {row["NC_Ru_minus_Fe_global"]:+.3f} |')
    lines += [
        "",
        f'State counts: ideal {d["states_ideal"]}; fugacity-closed reaction {d["states_NC"]}.',
        "A different count is a genuine thermodynamic feasibility result, not a forced regression match.",
        "",
        "**Limit:** Nonideal reactor reaction-equilibrium closure does not make this a fully nonideal industrial plant. Bed hydraulics, kinetics fit boundaries, interbed heat exchange and ownership conventions require separate validation.",
        "",
    ]
    (args.out/"GB_NC_PAIR.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))

if __name__ == "__main__":
    main()
