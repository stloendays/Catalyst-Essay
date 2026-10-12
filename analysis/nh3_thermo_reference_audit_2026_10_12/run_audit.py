"""CLOUD-ONLY, UNFROZEN NH3 thermochemical-reference robustness audit.

The frozen model is loaded by import; no frozen source file, state cache, figure,
result or manuscript is modified. Full optimization is RECOMPUTED when changing
NH3 standard formation Gibbs energy. BOTH the equilibrium loop and the MKM
NH3 adsorption chemical potential see the same substitution.

Usage: python analysis/nh3_thermo_reference_audit_2026_10_12/run_audit.py
Output: RESULT_DIR/summary.json, thermo_reference.csv, catalyst_costs.csv.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import multiprocessing as mp
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
import yaml
from scipy.optimize import brentq

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))
from thermo_ref import (KB_EV, equilibrium_y_nh3, full_kp, gform_gb_ev,
                        gform_nist_ev, reference_summary)

SOURCE = REPO / "provenance" / "discover_v1" / "source_harness"
RUN_NAME = "nh3_final_20260905T134204Z"
FROZEN = SOURCE / "outputs" / RUN_NAME
WORKBOOK = REPO / "provenance" / "nh3_final_1_1" / "source_harness" / "inputs" / "ammonia_activity_volcano_s1_v1.xlsx"
SHA256 = "fc259c5311744cccb82a7bc80ba4529f9bd34c61ed7933890dac70f016dce9ba"
RUN_RESULTS = json.loads((FROZEN / "results.json").read_text(encoding="utf-8"))
CFG = yaml.safe_load((FROZEN / "manifest_resolved.yaml").read_text(encoding="utf-8"))
sys.path.insert(0, str(SOURCE))
import harness_core as hc

_WORKER_H = None
_BENCH = {"Fe": 15.291704676621144,
          "Ru": 22.03059478781101,
          "Os": 25.83179725613286}


def original_gform(ctx, T, original) -> float:
    gg = original(ctx, T)
    return gg["NH3"] - 0.5*gg["N2"] - 1.5*gg["H2"]


def patch_gas_formation(original, model):
    """Reference only NH3 gas chemical potential, not adsorbate DFT energies.

    KineticContext.gas_G is used BOTH for the process reaction equilibrium
    in self_consistent_process_state() and for NH3 adsorption in Condition().
    Patching one of them alone would violate the frozen thermodynamic linkage.
    """
    if model == "NIST":
        fn = gform_nist_ev
    elif model == "GB":
        fn = gform_gb_ev
    else:
        raise ValueError(f"Unknown thermodynamic reference {model}")

    def gas_g(self, T):
        gg = original(self, T)
        old = gg["NH3"] - 0.5*gg["N2"] - 1.5*gg["H2"]
        gg["NH3"] += fn(T) - old
        return gg

    return gas_g


def _one_metal(metal):
    """Runs in Linux forked worker with identical pinned frozen harness code."""
    h = _WORKER_H
    log_vec = h.frozen_state_logtof(hc.EN0_CANON[metal])
    if not np.isfinite(log_vec).all():
        raise AssertionError(f"{metal}: nonfinite TOF surface")

    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        cost, volume, metal_charge, reactor_charge = h.cost_arrays(
            metal, log_vec, recovery=0.0)
    good = np.isfinite(cost) & np.isfinite(volume)
    can = good & (volume <= h.V_CAP)
    if not np.any(good):
        raise AssertionError(f"{metal}: no finite cost states")

    jraw = int(np.argmin(np.where(good, cost, np.inf)))
    feasible = None
    if np.any(can):
        j = int(np.argmin(np.where(can, cost, np.inf)))
        feasible = {
            "cost_USD_t": float(cost[j]),
            "volume_m3": float(volume[j]),
            "state_index": j,
            "T_C": float(h.state_T[j]),
            "P_bar": float(h.state_P[j]),
            "Tsep_C": float(h.state_Tsep[j]),
            "logTOF": float(log_vec[j]),
            "metal_cost_USD_t": float(metal_charge[j]),
            "reactor_cost_USD_t": float(reactor_charge[j]),
            "process_cost_USD_t": float(h.state_process_cost[j]),
        }
    d = {
        "metal": metal,
        "intrinsic_logTOF_673K": float(
            h.base_condition.logtof(hc.EN0_CANON[metal])),
        "raw_cost_USD_t": float(cost[jraw]),
        "raw_T_C": float(h.state_T[jraw]),
        "raw_P_bar": float(h.state_P[jraw]),
        "raw_Tsep_C": float(h.state_Tsep[jraw]),
        "feasible": feasible,
        "finite_states": int(np.count_nonzero(good)),
        "bed_feasible_states": int(np.count_nonzero(can)),
    }
    return metal, d, log_vec if metal == "Ru" else None


def cost_for_alpha(h, ru_logvec, alpha):
    total, V, _, _ = h.cost_arrays(
        "Ru", ru_logvec, recovery=0.0, alpha=alpha)
    mask = (V <= h.V_CAP) & np.isfinite(total)
    return float(np.min(total[mask])) if np.any(mask) else float("inf")


def activity_to_parity(h, ru_logvec, fe_cost):
    if fe_cost is None or not math.isfinite(fe_cost):
        return None
    if cost_for_alpha(h, ru_logvec, 1.0) <= fe_cost:
        return 1.0
    f = lambda a: cost_for_alpha(h, ru_logvec, 10.0**a) - fe_cost
    if f(12.0) > 0:
        return None
    return float(10.0**brentq(f, 0.0, 12.0, xtol=1e-10))


def _prepare_root():
    if hashlib.sha256(WORKBOOK.read_bytes()).hexdigest() != SHA256:
        raise AssertionError("Wang S1 workbook hash not pinned")
    root = Path(tempfile.mkdtemp(prefix="nh3_thermo_reference_"))
    (root / "inputs").mkdir(parents=True, exist_ok=True)
    shutil.copyfile(WORKBOOK, root / "inputs" / WORKBOOK.name)
    return root


def _metal_run(h, nworkers):
    global _WORKER_H
    _WORKER_H = h
    if sys.platform != "linux":
        raise RuntimeError("The cloud audit requires Linux fork semantics")
    metals = list(hc.ACTIVITY_ORDER_CANON)
    start = time.monotonic()
    with mp.get_context("fork").Pool(processes=nworkers) as pool:
        records = list(pool.imap_unordered(_one_metal, metals, chunksize=1))
    _WORKER_H = None
    data = {metal: d for metal, d, _ in records}
    ru_logvec = next(ru for metal, _, ru in records if metal == "Ru")
    print(f"  computed {len(data)} metals in {time.monotonic()-start:.1f} s", flush=True)
    return data, ru_logvec


def _compare_to_frozen(h, metals, alpha):
    if h.NSTATE != 14136:
        raise AssertionError(f"Frozen state count drift: {h.NSTATE} != 14136")
    if h.METAL_RECOVERY != 0.0:
        raise AssertionError("Baseline must not force optional Ru recovery")
    for m, benchmark in _BENCH.items():
        got = metals[m]["feasible"]
        if got is None or abs(got["cost_USD_t"]-benchmark) > 2e-7:
            raise AssertionError(f"Frozen {m} cost drift: {got}, expected {benchmark}")
    if abs(alpha-201.2234429878984) > 0.03:
        raise AssertionError(f"Frozen Ru activity break-even drift: {alpha}")
    expected_activity = RUN_RESULTS["deterministic"]["activity_order"]
    actual_activity = sorted(metals, key=lambda m: metals[m]["intrinsic_logTOF_673K"], reverse=True)
    if actual_activity != expected_activity:
        raise AssertionError(f"Frozen atomic ordering drift: {actual_activity}")
    print("  PASS: 14,136 states, all 15 atomic ranks, 3 frozen costs, 201.223x break-even", flush=True)


def _one_reference(mode, root, nworkers, original):
    t0 = time.monotonic()
    target = {"frozen": None, "NIST": gform_nist_ev, "GB": gform_gb_ev}[mode]
    hc.KineticContext.gas_G = original if mode == "frozen" else patch_gas_formation(original, mode)
    try:
        h = hc.NH3Harness(CFG, root)
        if int(h.NSTATE) < 1000:
            raise AssertionError("Less than 1000 thermodynamically feasible process states")
        form = {
            str(T): original_gform(h.ctx, T, hc.KineticContext.gas_G)
            for T in (623.15, 673.0, 698.15, 723.15)
        }
        for temp, value in form.items():
            if target and abs(value-target(float(temp))) > 1e-11:
                raise AssertionError(f"{mode} Gibbs-gas shift incorrect at {temp}: {value}")
        data, ru_logvec = _metal_run(h, nworkers)
        order = sorted(data, key=lambda m: data[m]["intrinsic_logTOF_673K"], reverse=True)
        feasible_order = sorted((m for m in data if data[m]["feasible"] is not None),
                                key=lambda m: data[m]["feasible"]["cost_USD_t"])
        raw_order = sorted(data, key=lambda m: data[m]["raw_cost_USD_t"])
        fe = data["Fe"]["feasible"]
        ru = data["Ru"]["feasible"]
        os_ = data["Os"]["feasible"]
        fe_cost = fe["cost_USD_t"] if fe else None
        alpha = activity_to_parity(h, ru_logvec, fe_cost)

        if mode == "frozen":
            _compare_to_frozen(h, data, alpha)
        b = {
            "mode": mode,
            "status": "exploratory_model_conditioned",
            "number_process_states": h.NSTATE,
            "original_search_grid_combinations": (
                len(h.T_GRID_C)*len(h.P_GRID_BAR)*len(h.TSEP_GRID_C)),
            "gas_formation_eV_per_NH3_by_T_K": form,
            "ideal_90bar_425C_yNH3": equilibrium_y_nh3(698.15, 90.0, form["698.15"]),
            "intrinsic_order": order,
            "raw_economic_order": raw_order,
            "feasible_economic_order": feasible_order,
            "Fe_cost_USD_t": fe_cost,
            "Ru_cost_USD_t": ru["cost_USD_t"] if ru else None,
            "Os_cost_USD_t": os_["cost_USD_t"] if os_ else None,
            "Ru_minus_Fe_USD_t": (
                ru["cost_USD_t"] - fe_cost if fe and ru else None),
            "Fe_minus_Ru_USD_t": (
                fe_cost - ru["cost_USD_t"] if fe and ru else None),
            "Ru_activity_parity_multiplier": alpha,
            "Fe_Ru_Os_order_matches_frozen": (
                feasible_order[:3] == ["Fe", "Ru", "Os"]),
            "model_inversion_Ru_Os_Fe_to_Fe_Ru_Os": (
                order[:3] == ["Ru", "Os", "Fe"] and
                feasible_order[:3] == ["Fe", "Ru", "Os"]),
            "metals": data,
            "elapsed_seconds": round(time.monotonic() - t0, 1),
        }
        print(json.dumps({k: b[k] for k in (
            "mode", "number_process_states", "intrinsic_order",
            "feasible_economic_order", "Fe_cost_USD_t", "Ru_cost_USD_t",
            "Os_cost_USD_t", "Ru_minus_Fe_USD_t", "Ru_activity_parity_multiplier",
            "ideal_90bar_425C_yNH3", "elapsed_seconds")}, indent=2), flush=True)
        return b
    finally:
        hc.KineticContext.gas_G = original


def _csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--out", default=os.environ.get(
        "NH3_THERMO_OUT", str(HERE / "results")))
    args = ap.parse_args()
    if not 1 <= args.workers <= 8:
        ap.error("workers must be between 1 and 8")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    if CFG["project"]["model_version"] != "NH3-FINAL-1.1":
        raise AssertionError("Unknown frozen model version")
    original = hc.KineticContext.gas_G
    root = _prepare_root()
    modes = {}
    try:
        for mode in ("frozen", "NIST", "GB"):
            modes[mode] = _one_reference(mode, root, args.workers, original)
        thermo = []
        for tc in (350.0, 375.0, 400.0, 425.0, 450.0):
            T = tc+273.15
            for mode in ("frozen", "NIST", "GB"):
                val = modes[mode]["gas_formation_eV_per_NH3_by_T_K"].get(str(T))
                if val is None:
                    # Interpolate no thermodynamics: compute frozen gas directly.
                    val = original_gform(
                        _dummy_ctx, T, original) if False else (
                            gform_nist_ev(T) if mode == "NIST" else
                            gform_gb_ev(T) if mode == "GB" else None)
                thermo.append({
                    "mode": mode,
                    "T_C": tc,
                    "gform_eV_per_NH3": val if val is not None else "",
                    "Kp_full": full_kp(val, T) if val is not None else "",
                    "ideal_yNH3_90bar": equilibrium_y_nh3(T, 90.0, val) if val is not None else "",
                })
        _csv(out / "thermo_reference.csv", thermo)
        rows = []
        for mode, r in modes.items():
            for metal, d in r["metals"].items():
                f = d["feasible"]
                rows.append({
                    "mode": mode, "metal": metal,
                    "intrinsic_logTOF": d["intrinsic_logTOF_673K"],
                    "raw_cost_USD_t": d["raw_cost_USD_t"],
                    "feasible_cost_USD_t": f["cost_USD_t"] if f else "",
                    "bed_m3": f["volume_m3"] if f else "",
                    "T_C": f["T_C"] if f else "",
                    "P_bar": f["P_bar"] if f else "",
                    "Tsep_C": f["Tsep_C"] if f else "",
                    "states_economically_feasible": d["bed_feasible_states"],
                })
        _csv(out / "catalyst_costs.csv", rows)
        ref = reference_summary()
        report = {
            "status": "UNFROZEN thermochemical reference audit; no canonical correction",
            "workbook_sha256": SHA256,
            "frozen_results_json": str(FROZEN.relative_to(REPO) / "results.json"),
            "frozen_model_version": CFG["project"]["model_version"],
            "scenarios": {
                "frozen": "unchanged original gas Gibbs standard state",
                "NIST": "change only NH3 gas absolute G to match Shomate formation free energy",
                "GB": "change only NH3 gas absolute G to match Gillespie-Beattie K",
            },
            "recomputed": "process equilibrium, inlet partial pressures, all 15 metal MKM rate surfaces and cost optima; Ru inverse activity multiplier",
            "recovery_fraction": 0.0,
            "independent_90bar_425C_reference": ref,
            "results": modes,
            "cautions": [
                "ideal-gas equilibrium at high pressure, not a calibrated fugacity EOS",
                "NH3 gas-formation re-referencing is a sensitivity, not a complete DFT/TS/MKM re-fit",
                "current process map is algebraic approach-to-equilibrium, not an axial/thermal reactor",
                "energy, equipment/cost and catalytic descriptors are held frozen",
                "cannot establish real industrial Fe/Ru-C bed or KAAP commercial economics",
                "model-comparison outcome is not author approval to change frozen outputs or manuscript",
            ],
        }
        (out / "summary.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
            encoding="utf-8")
        print("WROTE", out / "summary.json", flush=True)
    finally:
        hc.KineticContext.gas_G = original
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    main()
