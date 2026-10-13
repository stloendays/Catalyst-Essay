"""The latest NH3 plant model, imported unchanged, and its evaluation at an arbitrary plant operating point.

Latest model = NH3-FINAL-1.1 process states with the measured Fe (Dyson & Simon 1968) and Ru/C (Rossetti et al. 2006)
rate laws and plug-flow sizing, as implemented in analysis/nh3_staged_converter_2026_10_12/ (kinetics.py,
kinetics_swap.py, converter.py, parameters.yaml). Nothing in that folder or in provenance/ is edited; this module only
imports it.

Two model levels are used:

  state model      NH3-FINAL-1.1 loop state at (T, P, T_sep): H2/N2 = 3, no inerts, per-pass conversion 0.8 of the
                   loop equilibrium at T, recycle NH3 = separator vapour p_sat(T_sep)/P, compression from 30 bar
                   (isothermal, eta 0.75) and across the 3-bar recycle rise, Carnot/2 refrigeration; Fe bed volume by
                   isothermal plug flow with the Dyson-Simon rate (kinetics_swap.amount, 'plug').
  converter model  converter.py: 2-4 adiabatic beds in series with interbed cooling, inerts, fused Fe or Ru/C per bed,
                   bed inlet temperatures and extents optimised for cost inside the same loop accounting.

Secondary column: PR #77 (branch analysis/nh3-final-1-2-candidate-20261013), Gillespie-Beattie standard Gibbs energy
with Newton-Cooper reaction fugacities in the loop equilibrium (gb_fugacity_pair.GBFugacityReaction), 50-300 bar.
Its module is read from the branch with `git show` into a temporary directory and imported; nothing is checked out.

Model version (analysis/nh3_model.py, environment variable NH3_MODEL):
  1.1 (default)  the pre-registered model above, unchanged: NH3-FINAL-1.1 states from provenance/discover_v1 and
                 provenance/nh3_final_1_1 (kinetics_swap.build).
  1.2            NH3-FINAL-1.2 states (Gillespie-Beattie NH3 formation free energy and Newton-Cooper fugacities in the
                 loop equilibrium; provenance/nh3_final_1_2/source_harness, harness built by nh3_model.harness()). The
                 measured rate laws, plug-flow sizing and every converter-level function are the same code. The
                 converter model (converter.py) already closes its equilibrium on Gillespie-Beattie Ka with
                 Newton-Cooper activities, and the 1.2 manifest has the 1.1 economics, plant, process and engineering
                 blocks (asserted in assert_same_accounting), so converter-level results are the same in both versions.
"""
from __future__ import annotations

import copy
import importlib
import importlib.util
import math
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
STAGED = REPO / "analysis" / "nh3_staged_converter_2026_10_12"
sys.path.insert(0, str(STAGED))

import converter as C  # noqa: E402
import kinetics as K  # noqa: E402
import kinetics_swap as S  # noqa: E402


def _version_switch():
    """analysis/nh3_model.py under its own module name (this file is also called nh3_model)."""
    name = "nh3_model_version_switch"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, REPO / "analysis" / "nh3_model.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


NM = _version_switch()
VERSION, LABEL = NM.VERSION, NM.LABEL
hc = S.hc
if VERSION == "1.1":
    FROZEN = S.FROZEN                               # Fe 15.2917, Ru 22.0306 (NH3-FINAL-1.1)
    FROZEN_OPTIMA = dict(Fe=(425.0, 180.0, 30.0), Ru=(450.0, 425.0, 25.0))
    MEASURED_FE = dict(cost=15.578802, T_C=425.0, P_bar=170.0, Tsep_C=30.0, V_m3=25.59425)   # staged-converter README
else:
    _A = NM.anchors()                               # canonical 1.2 run, results.json
    FROZEN = dict(Fe=_A["Fe"], Ru=_A["Ru"], NSTATE=_A["NSTATE"])
    FROZEN_OPTIMA = dict(Fe=tuple(_A["Fe_optimum"]), Ru=tuple(_A["Ru_optimum"]))
    # Re-derived on the 1.1 definition (measured Dyson-Simon Fe rate, plug flow, source rates, no F_CAL) on the 1.2
    # states; recorded from the first 1.2 run of run_benchmark.py (nh3_1_2/summary.json) as the 1.2 regression anchor.
    MEASURED_FE = dict(cost=14.925644, T_C=450.0, P_bar=140.0, Tsep_C=30.0, V_m3=56.30022)
PR77_BRANCH = "origin/analysis/nh3-final-1-2-candidate-20261013"
PR77_FILE = "analysis/nh3_final_1_2_candidate_2026_10_13/gb_fugacity_pair.py"


# --- anchors ------------------------------------------------------------------------------------------------------

def build_frozen():
    """Process-state harness of the selected version (1.1: kinetics_swap.build, unchanged; 1.2: nh3_model.harness)."""
    if VERSION == "1.1":
        return S.build(False)
    assert_same_accounting()
    h = NM.harness()
    assert (h.NH3_REFERENCE, h.FUGACITY_IN_LOOP, h.FUGACITY_IN_MKM) == ("gillespie_beattie", True, True), "not 1.2"
    assert h.NSTATE == FROZEN["NSTATE"], h.NSTATE
    return h


def build_v11():
    """The NH3-FINAL-1.1 harness (for the uncounted Gillespie-Beattie ideal-gas diagnostic, which patches it)."""
    return S.build(False)


def assert_same_accounting():
    """The 1.2 manifest differs from the 1.1 manifest used by converter.py and kinetics_swap.py only in project labels,
    the thermodynamic basis, the descriptor calibration factor F_CAL (unused by the measured rate laws), the frozen
    regression anchors and the worker count. Every block the measured-kinetics costs read is identical."""
    a, b = S.CFG, NM.cfg()
    skip_top = {"project", "thermo", "frozen_regression", "numerics", "gates"}
    for k in sorted((set(a) | set(b)) - skip_top):
        if k == "economics":
            ea = {kk: v for kk, v in a[k].items() if kk not in ("calibration_factor", "calibration_note")}
            eb = {kk: v for kk, v in b[k].items() if kk not in ("calibration_factor", "calibration_note")}
            assert ea == eb, "economics differ between the 1.1 and 1.2 manifests"
        else:
            assert a.get(k) == b.get(k), f"manifest block {k!r} differs between 1.1 and 1.2"
    assert a["numerics"]["descriptor_grid_eV"] == b["numerics"]["descriptor_grid_eV"]
    assert a["gates"] == b["gates"]


def _frozen_reference(h):
    """Descriptor-kinetics optima of the selected version (kinetics_swap.frozen_reference for 1.1, which asserts the
    1.1 anchors itself; the same computation on the 1.2 harness otherwise)."""
    if VERSION == "1.1":
        return S.frozen_reference(h)
    out = {}
    for m in ("Fe", "Ru"):
        tot, V, _, _ = h.cost_arrays(m, h.frozen_state_logtof(h.EN0[m]))
        out[m] = S.best(h, np.where(V <= h.V_CAP, tot, np.inf), V)
    return out


def reproduce_anchors(h=None, tol_frozen=1e-9, tol_measured=1e-5):
    """Frozen descriptor-kinetics Fe / Ru optima of the selected version (1.1: 15.29 / 22.03; 1.2: 11.52 / 16.63, from
    the canonical results.json) and the measured-kinetics Fe optimum (plug, source), asserted."""
    h = h or build_frozen()
    fr = _frozen_reference(h)
    assert abs(fr["Fe"]["cost"] - FROZEN["Fe"]) < tol_frozen and abs(fr["Ru"]["cost"] - FROZEN["Ru"]) < tol_frozen
    for m in ("Fe", "Ru"):
        assert (fr[m]["T_C"], fr[m]["P_bar"], fr[m]["Tsep_C"]) == FROZEN_OPTIMA[m], fr[m]
    _, V0, _, _ = h.cost_arrays("Fe", h.frozen_state_logtof(hc.EN0_CANON["Fe"]))
    j0 = next(i for i in range(h.NSTATE) if (h.state_T[i], h.state_P[i], h.state_Tsep[i]) == S.CAL_STATE)
    r = S.evaluate(h, S.state_arrays(h), "plug", "source", float(V0[j0]))
    fe = r["Fe"]
    assert abs(fe["cost"] - MEASURED_FE["cost"]) < tol_measured, fe
    assert (fe["T_C"], fe["P_bar"], fe["Tsep_C"]) == (MEASURED_FE["T_C"], MEASURED_FE["P_bar"], MEASURED_FE["Tsep_C"]), fe
    return dict(frozen_Fe=fr["Fe"], frozen_Ru=fr["Ru"], measured=r)


# --- state model at an arbitrary point ----------------------------------------------------------------------------

def _state_dict(h, s, tpd):
    """Loop metrics of one NH3-FINAL-1.1 state dict s (basis: 1 mol NH3 made per pass), scaled to tpd."""
    X, ysep = s["X"], s["ysep"]
    ratio = ysep / (1.0 - ysep)
    nA = ratio * 2.0 * (1.0 - X) / X                 # NH3 recycled per mol NH3 made
    tot_in = 2.0 / X + nA
    tot_out = tot_in - 1.0
    y_in, y_out = nA / tot_in, (nA + 1.0) / tot_out
    fresh = 2.0                                      # mol N2 + H2 make-up per mol NH3 (no inerts in NH3-FINAL-1.1)
    el = h.ELECTRICITY
    return dict(
        T_C=s["T_C"], P_bar=s["P_bar"], Tsep_C=s["Tsep_C"], X_N2_per_pass=X, X_over_Xeq=X / s["Xeq"],
        inlet_NH3_molpct=100 * y_in, outlet_NH3_molpct=100 * y_out, delta_NH3_molpct=100 * (y_out - y_in),
        recycle_to_makeup=s["recycle_total"] / fresh, inlet_to_makeup=tot_in / fresh,
        inlet_Nm3_h=s["inlet_Nm3_h"] * tpd / h.PLANT_TPD,
        inlet_Nm3_h_per_tpd=s["inlet_Nm3_h"] / h.PLANT_TPD,
        fresh_comp_MWh_t=s["fresh_comp"] / el, recycle_comp_MWh_t=s["recycle_comp"] / el,
        refrigeration_MWh_t=s["refrigeration"] / el,
        loop_power_MWh_t=(s["fresh_comp"] + s["recycle_comp"] + s["refrigeration"]) / el,
        process_cost_USD_t=s["process_cost"])


def fe_bed_m3(h, s, tpd, sizing="plug"):
    """Dyson-Simon fused-Fe bed (m3) for state s at capacity tpd: isothermal plug flow, inlet -> outlet."""
    X, ysep = s["X"], s["ysep"]
    ratio = ysep / (1.0 - ysep)
    nA = ratio * 2.0 * (1.0 - X) / X
    tot = 2.0 / X + nA
    st = dict(T=np.array([s["T_C"] + 273.15]), P=np.array([s["P_bar"]]), yN=np.array([(0.5 / X) / tot]),
              yH=np.array([(1.5 / X) / tot]), yA=np.array([max(nA / tot, 1e-12)]), xi_out=np.array([0.5 / tot]),
              F_in=np.array([h.nh3_mol_s * tot]), X=np.array([X]))
    return float(S.amount(st, S.rate_fe_m3, h, sizing)[0]) * tpd / h.PLANT_TPD


def state_point(h, T_C, P_bar, Tsep_C, tpd=1000.0):
    """NH3-FINAL-1.1 loop state at any (T, P, T_sep) (the grid is not required) plus the measured-Fe plug-flow bed."""
    s = h.self_consistent_process_state(float(T_C), float(P_bar), float(Tsep_C))
    if s is None:
        return None
    d = _state_dict(h, s, tpd)
    V = fe_bed_m3(h, s, tpd)
    d.update(capacity_tpd=tpd, Fe_bed_m3=V, Fe_bed_m3_per_tpd=V / tpd,
             GHSV_h=d["inlet_Nm3_h"] / V if V > 0 and math.isfinite(V) else math.nan)
    return d


# --- converter model -------------------------------------------------------------------------------------------------

def converter_design(pattern, P_bar, Tsep_C, inerts, tpd=1000.0, econ=None, seed=1, maxiter=80, popsize=10):
    """Cost-optimal adiabatic converter (bed inlet temperatures and extents) at the plant's loop conditions."""
    econ = econ or C.Econ(accounting="frozen", recovery=0.9555)
    loop = C.Loop(P_bar=float(P_bar), Tsep_C=float(Tsep_C), inerts=float(inerts), production_tpd=float(tpd))
    r = C.optimize(tuple(pattern), loop, econ, "adiabatic", seed=seed, maxiter=maxiter, popsize=popsize)
    return r


# --- PR #77 secondary column --------------------------------------------------------------------------------------

_PR77 = {}


def pr77_module():
    """Import gb_fugacity_pair.py from the PR #77 branch (read-only, via git show). None if the branch is absent."""
    if "mod" in _PR77:
        return _PR77["mod"]
    try:
        src = subprocess.run(["git", "-C", str(REPO), "show", f"{PR77_BRANCH}:{PR77_FILE}"], capture_output=True,
                             check=True).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        _PR77["mod"] = None
        return None
    d = Path(tempfile.mkdtemp(prefix="pr77_"))
    p = d / "pr77_gb_fugacity_pair.py"
    p.write_bytes(src)
    sys.path.insert(0, str(d))
    mod = importlib.import_module("pr77_gb_fugacity_pair")
    rev = subprocess.run(["git", "-C", str(REPO), "rev-parse", PR77_BRANCH], capture_output=True, text=True).stdout.strip()
    mod.__pr77_commit__ = rev
    _PR77["mod"] = mod
    return mod


class _GBGibbs:
    """Context manager: Gillespie-Beattie gas Gibbs energy in the harness (the PR #64 / PR #77 patch), restored after."""

    def __enter__(self):
        self.orig = hc.KineticContext.gas_G
        hc.KineticContext.gas_G = S._corrected_gas_G

    def __exit__(self, *a):
        hc.KineticContext.gas_G = self.orig


def build_pr77():
    """PR #77 harness: GB + Newton-Cooper reaction equilibrium, 50-300 bar (gb_fugacity_pair.GBFugacityReaction)."""
    mod = pr77_module()
    if mod is None:
        return None
    with _GBGibbs():
        h = mod.GBFugacityReaction(S.CFG, S.ROOT)
    h._pr77_commit = mod.__pr77_commit__
    return h


def state_point_pr77(h, T_C, P_bar, Tsep_C, tpd=1000.0):
    if h is None or not (50.0 <= P_bar <= 300.0):
        return None
    with _GBGibbs():
        return state_point(h, T_C, P_bar, Tsep_C, tpd)


def optimum(h, fcal_target=1.0):
    """Measured-kinetics optima (plug flow, source rates) on harness h: Fe, Ru benchmark and supported Ru/C."""
    return S.evaluate(h, S.state_arrays(h), "plug", "source", fcal_target)


def scaled_cfg(tpd):
    cfg = copy.deepcopy(S.CFG)
    cfg["plant"]["production_tpd"] = float(tpd)
    return cfg
