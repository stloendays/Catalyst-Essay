"""ACSA code path for supported-Au CO-oxidation candidates (Au/TiO2 particle-size control).

The agent's batch chain for this reaction system. It takes catalyst inputs (as extracted from the source papers, or
the hand-built inputs) plus the fixed protocol, and returns per-candidate mass activity, required catalyst mass,
burden, the rank metrics, the literature-envelope Monte Carlo and the semi-open operating-window stress test.

Catalyst inputs (what the extraction agent reads from the papers):
  reference: average_diameter_nm, au_loading_mass_fraction, dispersion_fraction,
             stabilized_activity_umol_CO_gcat_s, catalyst_mass_mg, reaction_flow_Nml_min,
             feed_CO_mole_fraction, reaction_temperature_K                     (Janssens et al. 2006)
  size_activity: tof_exponent (TOF ~ d^-n for the series closest to the anchor loading), tof_exponent_sigma
                                                                               (Overbury et al. 2006)
Protocol (fixed, not extracted): candidate diameters, dispersion-geometry exponent, molar volume, Monte Carlo
ranges, seeds and draw counts; read from the frozen control configuration.

The frozen hand-built results are data/rank_preservation_control_v1_1.csv (nominal table), the 10,000-draw
literature envelope of controls/au_tio2_rank_preservation_v1_1.py and data/rank_preservation_semiopen_v1_3_summary.csv
(semi-open windows). self_check() compares this code path against them.
"""
from __future__ import annotations

import csv
import importlib.util
import json
import math
import random
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CONTROL_CONFIG = REPO / "controls" / "au_tio2_rank_preservation_v1_1_config.json"
FROZEN_TABLE = REPO / "data" / "rank_preservation_control_v1_1.csv"
FROZEN_SEMIOPEN = REPO / "data" / "rank_preservation_semiopen_v1_3_summary.csv"
SEMIOPEN_SCRIPT = REPO / "data" / "rank_preservation_semiopen_v1_3.py"
FROZEN_ENVELOPE_FULL = 1.0          # controls/.../RANK_PRESERVATION_CONTROL_V1_1_REPORT.md: 10,000/10,000 preserved

REFERENCE_KEYS = ("average_diameter_nm", "au_loading_mass_fraction", "dispersion_fraction",
                  "stabilized_activity_umol_CO_gcat_s", "catalyst_mass_mg", "reaction_flow_Nml_min",
                  "feed_CO_mole_fraction", "reaction_temperature_K")


def protocol() -> dict:
    cfg = json.loads(CONTROL_CONFIG.read_text(encoding="utf-8"))
    return {
        "diameters_nm": cfg["candidate_diameters_nm"],
        "dispersion_exponent": cfg["geometry"]["dispersion_exponent_nominal"],
        "molar_volume_L_mol": cfg["reactor_model"]["normal_molar_volume_L_mol"],
        "mc": cfg["uncertainty"],
    }


def handbuilt_inputs() -> dict:
    """The inputs the hand-built control used, taken from the frozen configuration."""
    cfg = json.loads(CONTROL_CONFIG.read_text(encoding="utf-8"))
    ref = cfg["literature_reference"]
    rel = cfg["size_activity_relation"]
    return {"reference": {k: ref[k] for k in REFERENCE_KEYS},
            "size_activity": {"tof_exponent": rel["nominal_tof_exponent"],
                              "tof_exponent_sigma": rel["tof_exponent_sigma"]}}


# ------------------------------------------------------------------ forward chain --------------------------------
def candidate(inp: dict, prot: dict, d_nm: float, n_tof: float, m_disp: float) -> dict:
    ref = inp["reference"]
    d_ref, disp_ref = ref["average_diameter_nm"], ref["dispersion_fraction"]
    dispersion = min(1.0, disp_ref * (d_ref / d_nm) ** m_disp)
    mass_activity = ref["stabilized_activity_umol_CO_gcat_s"] * (d_nm / d_ref) ** (-n_tof) * dispersion / disp_ref

    # Pseudo-first-order plug flow at the reference experiment's flow; the target conversion is the one the
    # reference rate, catalyst mass and flow imply.
    flow = ref["reaction_flow_Nml_min"] * 1e-3 / prot["molar_volume_L_mol"] / 60.0          # mol/s
    y_co = ref["feed_CO_mole_fraction"]
    theta_ref = ref["stabilized_activity_umol_CO_gcat_s"] * 1e-6 / y_co * ref["catalyst_mass_mg"] / 1000.0 / flow
    x_target = 1.0 - math.exp(-theta_ref)
    mass_g = -math.log(1.0 - x_target) * flow / (mass_activity * 1e-6 / y_co)
    return {"diameter_nm": d_nm, "mass_activity_umol_CO_gcat_s": mass_activity,
            "required_catalyst_mass_mg": mass_g * 1000.0,
            "required_Au_mass_mg": mass_g * 1000.0 * ref["au_loading_mass_fraction"],
            "target_conversion": x_target}


def _ranks(values, reverse=False):
    order = sorted(range(len(values)), key=lambda i: values[i], reverse=reverse)
    out = [0] * len(values)
    for r, i in enumerate(order, 1):
        out[i] = r
    return out


def rank_metrics(activity, burden) -> dict:
    ra, rb = _ranks(activity, reverse=True), _ranks(burden)
    n = len(ra)
    rho = 1.0 - 6.0 * sum((a - b) ** 2 for a, b in zip(ra, rb)) / (n * (n * n - 1))
    conc = disc = 0
    for i in range(n):
        for j in range(i + 1, n):
            s = (activity[i] - activity[j]) * (burden[j] - burden[i])
            conc += s > 0
            disc += s < 0
    return {"spearman": rho, "kendall": (conc - disc) / (conc + disc), "inversions": disc,
            "winner_preserved": ra.index(1) == rb.index(1)}


def nominal(inp: dict, prot: dict) -> list[dict]:
    rows = [candidate(inp, prot, d, inp["size_activity"]["tof_exponent"], prot["dispersion_exponent"])
            for d in prot["diameters_nm"]]
    best = min(r["required_catalyst_mass_mg"] for r in rows)
    for r in rows:
        r["procurement_burden_vs_best"] = r["required_catalyst_mass_mg"] / best
    return rows


def envelope(inp: dict, prot: dict) -> dict:
    """Literature envelope: TOF and dispersion exponents drawn over the protocol ranges."""
    mc = prot["mc"]
    rng = random.Random(mc["seed"])
    full, min_rho = 0, 1.0
    for _ in range(mc["draws"]):
        n = rng.uniform(mc["tof_exponent_min"], mc["tof_exponent_max"])
        m = rng.uniform(mc["dispersion_exponent_min"], mc["dispersion_exponent_max"])
        rows = [candidate(inp, prot, d, n, m) for d in prot["diameters_nm"]]
        met = rank_metrics([r["mass_activity_umol_CO_gcat_s"] for r in rows],
                           [r["required_catalyst_mass_mg"] for r in rows])
        full += met["inversions"] == 0
        min_rho = min(min_rho, met["spearman"])
    return {"draws": mc["draws"], "full_preservation": full / mc["draws"], "min_spearman": min_rho}


def semiopen(rows: list[dict]) -> list[dict]:
    """Semi-open operating-window stress test, fed with this chain's 273.15 K activities and masses at the
    precision the frozen table stores (the precision the frozen stress test was run from)."""
    spec = importlib.util.spec_from_file_location("semiopen_v1_3", SEMIOPEN_SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    import numpy as np
    mod.ACTIVITY_273 = np.array([round(r["mass_activity_umol_CO_gcat_s"], 4) for r in rows])
    mod.MASS_273_MG = np.array([round(r["required_catalyst_mass_mg"], 3) for r in rows])
    out = []
    for wname, w in mod.WINDOWS.items():
        for sname, s in mod.STRESS_LEVELS.items():
            out.append(mod.run_window(wname, w["tmax"], w["seed"], sname, **s))
    return out


# ------------------------------------------------------------------ self-check -----------------------------------
FROZEN_DECIMALS = {"mass_activity_umol_CO_gcat_s": 4, "required_catalyst_mass_mg": 3, "required_Au_mass_mg": 3,
                   "procurement_burden_vs_best": 3}


def self_check(inp: dict, label: str, run_semiopen: bool = True) -> dict:
    """Reproduce the frozen hand-built Au/TiO2 numbers from `inp` through this code path."""
    prot = protocol()
    rows = nominal(inp, prot)
    frozen = list(csv.DictReader(FROZEN_TABLE.open(encoding="utf-8")))
    cells, bad = 0, []
    for r, f in zip(rows, frozen):
        assert float(f["diameter_nm"]) == r["diameter_nm"]
        for k, dec in FROZEN_DECIMALS.items():
            cells += 1
            if f"{r[k]:.{dec}f}" != f[k]:
                bad.append({"diameter_nm": r["diameter_nm"], "field": k, "chain": round(r[k], dec + 2), "frozen": f[k]})
    met = rank_metrics([r["mass_activity_umol_CO_gcat_s"] for r in rows], [r["required_catalyst_mass_mg"] for r in rows])
    env = envelope(inp, prot)
    checks = {
        "nominal_table_cells_match": not bad,
        "order_2_3_4_5_6_nm": met["inversions"] == 0 and met["winner_preserved"],
        "spearman_kendall_1": met["spearman"] == 1.0 and met["kendall"] == 1.0,
        "envelope_10000_of_10000": env["draws"] == 10000 and env["full_preservation"] == FROZEN_ENVELOPE_FULL,
    }
    result = {"system": "Au/TiO2 CO oxidation", "inputs": label, "nominal_cells_compared": cells,
              "nominal_mismatches": bad, "rank_metrics": met, "envelope": env}
    if run_semiopen:
        frozen_s = {(f["window"], f["stress"]): f for f in csv.DictReader(FROZEN_SEMIOPEN.open(encoding="utf-8"))}
        s_bad = []
        for s in semiopen(rows):
            f = frozen_s[(s["window"], s["stress"])]
            for k in ("full_preservation_fraction", "mean_spearman_rho", "mean_pairwise_inversions"):
                dec = len(f[k].split(".")[1]) if "." in f[k] else 0
                if f"{s[k]:.{dec}f}" != f[k]:
                    s_bad.append({"window": s["window"], "stress": s["stress"], "field": k, "chain": s[k], "frozen": f[k]})
        checks["semiopen_windows_match"] = not s_bad
        result["semiopen_mismatches"] = s_bad
        result["semiopen_windows_compared"] = len(frozen_s)
    result["checks"] = checks
    result["pass"] = all(checks.values())
    return result


if __name__ == "__main__":
    print(json.dumps(self_check(handbuilt_inputs(), "hand-built"), indent=1))
