"""Shared set-up for the Keestra consolidation scripts: paths, the Keestra Fe law on every Fe code path, and the gate.

Fe = Keestra et al. (2025) Model 3, Topsoe KM1R (1964) activity factor b_cat = 0.350, source K_f, fitted 1-324 bar
(analysis/nh3_fe_inrange_kinetics_2026_10_19/keestra_fe.py, imported unchanged). Ru/C = Rossetti 2006, fitted 50-100 bar.

Three Fe code paths exist in the repository; each is redirected here without editing the upstream file:
  cost model      kinetics_swap.rate_fe_m3 (plug-flow amounts per process state; read at call time)
  converter.py    catalyst_props(): 'Fe_Keestra_<cat>' keys as in staged_inrange.py, and (switch) the default 'Fe'
  PR loop (#93)   kinetic_bridge.rate_m3('Fe', ...) and its Fe bed density (see pr_loop_check.py)
Bed density 2,500 kg/m3 (keestra_fe.BED_DENSITY), as in the in-range folder.

gate() reproduces the canonical in-range anchors of analysis/nh3_fe_inrange_kinetics_2026_10_19/results.json on the
fitted_range.py / frontier_swap.py code path to 1e-6 relative and returns the objects for reuse.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np

assert os.environ.get("NH3_MODEL") == "1.2", "run with NH3_MODEL=1.2"
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
AN = REPO / "analysis"
INRANGE = AN / "nh3_fe_inrange_kinetics_2026_10_19"
STAGED = AN / "nh3_staged_converter_2026_10_12"
for p in (AN / "nh3_fitted_range_2026_10_19", INRANGE, STAGED):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import keestra_fe as KF  # noqa: E402
import kinetics as K  # noqa: E402
import converter as C  # noqa: E402

FE_CAT = "KM1R_1964"
FE_KEY = f"Fe_Keestra_{FE_CAT}"
FE_P = (1.0, 324.0)                 # Keestra fitted pressure range, bar
RU_P = (50.0, 100.0)                # Rossetti fitted pressure range, bar
TOL_P = 1e-6
REL = 1e-6                          # relative tolerance of the anchors


def rate_fe_m3(T, P, yN, yH, yA):
    """Keestra KM1R-1964 rate per m3 of bed (mol NH3 m^-3 s^-1), signature of kinetics_swap.rate_fe_m3."""
    return KF.rate(T, P, yN, yH, yA, catalyst=FE_CAT, eq="source", per="m3")


# --- converter.py: register the Keestra keys (as staged_inrange.py) and optionally the default 'Fe' ------------------
for _cat in KF.BCAT:
    K.RATE[f"Fe_Keestra_{_cat}"] = (lambda c: (lambda T, P, a, b, y: KF.rate(T, P, a, b, y, catalyst=c)))(_cat)
_ORIG_PROPS = C.catalyst_props
DEFAULT_FE_IS_KEESTRA = {"on": False}


def _props(cat, econ):
    key = econ.fe_kinetics
    if cat != "Ru" and key == "Fe" and DEFAULT_FE_IS_KEESTRA["on"]:
        key = FE_KEY
    if cat != "Ru" and key.startswith("Fe_Keestra_"):
        rate, act = K.RATE[key], econ.fe_activity
        return (lambda T, P, a, b, y: act * rate(T, P, a, b, y)), KF.BED_DENSITY
    return _ORIG_PROPS(cat, econ)


C.catalyst_props = _props


def converter_default_fe_keestra(on=True):
    """Every converter.py call that asks for the default Fe law ('Fe', Dyson-Simon) gets Keestra KM1R-1964."""
    DEFAULT_FE_IS_KEESTRA["on"] = bool(on)


# --- gate ---------------------------------------------------------------------------------------------------------

def inrange_masks(P):
    return ((P >= FE_P[0] - TOL_P) & (P <= FE_P[1] + TOL_P), (P >= RU_P[0] - TOL_P) & (P <= RU_P[1] + TOL_P))


def canonical_anchors():
    d = json.loads((INRANGE / "results.json").read_text(encoding="utf-8"))["Fe_Keestra"]["Keestra KM1R-1964, source Kf"]
    return {"Fe_benchmark": d["a"]["Fe"]["cost"], "Fe_benchmark_P": d["a"]["Fe"]["P_bar"],
            "Ru_bulk_benchmark": d["a"]["Ru"]["cost"], "Ru_bulk_benchmark_P": d["a"]["Ru"]["P_bar"],
            "RuC_minus_Fe_0": d["b_0"]["gap"], "RuC_minus_Fe_12": d["b_12"]["gap"], "breakeven": d["b_breakeven"]["rate"],
            "KAAP_RuC_minus_Fe_0": d["c_0_KAAP"]["gap"], "KAAP_RuC_minus_Fe_12": d["c_12_KAAP"]["gap"],
            "KAAP_breakeven": d["c_breakeven_KAAP"]["rate"]}


def check(name, got, ref, rel=REL):
    """Assert 1e-6 relative at the source's six-decimal precision, plus its rounding interval.

    results.json rounds rates (not percent rates) to 6 decimals. Its financing
    roots cannot support a 1e-6 relative test of unrounded internal values.
    Do not hide that precision limit behind an unexplained absolute tolerance.
    """
    assert abs(round(float(got),6)-ref) <= rel*abs(ref), (name,got,ref)
    assert abs(got-ref) <= max(rel*abs(ref),5.00001e-7), (name,got,ref)


def gate(log=print):
    """Canonical in-range anchors on the fitted_range.py path with Keestra Fe; returns (FR, KS, h, st, M, mfe, mru, kaap)."""
    import fitted_range as FR
    KS = FR.KS
    ref = canonical_anchors()
    ds_rate = KS.rate_fe_m3
    KS.rate_fe_m3 = rate_fe_m3
    try:
        h = KS.build(False)
        st = KS.state_arrays(h)
        M = FR.Variant(h, st, "plug", "source", None)
    finally:
        KS.rate_fe_m3 = ds_rate
    mfe, mru = inrange_masks(h.state_P)
    kaap = (h.state_P == 90.0) & (h.state_Tsep == -20.0)
    a = FR.pair(M, M.fe_bench(), M.rub(), mfe, mru)
    got = {"Fe_benchmark": a["Fe"]["cost"], "Fe_benchmark_P": a["Fe"]["P_bar"], "Ru_bulk_benchmark": a["Ru"]["cost"],
           "Ru_bulk_benchmark_P": a["Ru"]["P_bar"],
           "RuC_minus_Fe_0": FR.pair(M, M.fe_cf(0.0), M.ruc_cf(0.0), mfe, mru)["gap"],
           "RuC_minus_Fe_12": FR.pair(M, M.fe_cf(0.12), M.ruc_cf(0.12), mfe, mru)["gap"],
           "breakeven": FR.breakeven_fin(M, mfe, mru)["rate"],
           "KAAP_RuC_minus_Fe_0": FR.pair(M, M.fe_cf(0.0), M.ruc_cf(0.0), mfe & kaap, mru & kaap)["gap"],
           "KAAP_RuC_minus_Fe_12": FR.pair(M, M.fe_cf(0.12), M.ruc_cf(0.12), mfe & kaap, mru & kaap)["gap"],
           "KAAP_breakeven": FR.breakeven_fin(M, mfe & kaap, mru & kaap)["rate"]}
    for k in ref:
        check(k, got[k], ref[k])
    log("canonical in-range anchors reproduced (1e-6 relative at source 6-decimal precision; unrounded roots checked against rounding intervals): " + ", ".join(f"{k} {got[k]:.9g}" for k in ref))
    dump('canonical_anchor_checks.json',{k:dict(reference=ref[k],computed=got[k],raw_relative_error=abs(got[k]-ref[k])/abs(ref[k]),source_precision_relative_pass=abs(round(got[k],6)-ref[k])<=REL*abs(ref[k])) for k in ref},12)
    return FR, KS, h, st, M, mfe, mru, kaap, got


class Tee:
    """Mirror stdout into a *_stdout.txt file."""

    def __init__(self, path):
        self.f = open(path, "w", encoding="utf-8")
        self.o = sys.stdout

    def write(self, s):
        self.o.write(s)
        self.f.write(s)

    def flush(self):
        self.o.flush()
        self.f.flush()


def tee(name):
    sys.stdout = Tee(HERE / f"{name}_stdout.txt")


def clean(o, nd=6):
    import math
    if isinstance(o, (float, np.floating)):
        o = float(o)
        return round(o, nd) if math.isfinite(o) else str(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (bool, np.bool_)):
        return bool(o)
    if isinstance(o, dict):
        return {str(k): clean(v, nd) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v, nd) for v in o]
    return o


def dump(name, obj, nd=6):
    (HERE / name).write_text(json.dumps(clean(obj, nd), indent=1) + "\n", encoding="utf-8")
