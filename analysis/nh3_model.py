"""NH3 model selection shared by the ammonia analyses.

    NH3_MODEL=1.1   NH3-FINAL-1.1, the frozen model (default)
    NH3_MODEL=1.2   NH3-FINAL-1.2: NH3 formation free energy from the Gillespie-Beattie equilibrium constant and
                    Newton-Cooper fugacity coefficients, used alike in the loop equilibrium and in the microkinetic gas
                    activities; F_CAL recalibrated on the 1.1 definition (provenance/nh3_final_1_2/source_harness)

Harness roots (each holds harness_core.py, inputs/, outputs/<run>/manifest_resolved.yaml and results.json, and a local
cache/ with the response surface, which is never committed):
    1.1   $NH3_HARNESS       default D:/论文-AI4S/Catalyst_Economic_Leverage_Automation_Harness_v0.1
    1.2   $NH3_HARNESS_1_2   default <repo>/provenance/nh3_final_1_2/source_harness

The 1.2 harness_core.py is a superset of the 1.1 file: with no `thermo` block in the manifest it is bit-identical to 1.1.

Usage in an analysis script:
    sys.path.insert(0, str(REPO / "analysis")); import nh3_model as NM
    hc = NM.core(); h = NM.harness(); A = NM.anchors(); OUT = NM.out_dir(HERE)
"""
from __future__ import annotations

import importlib.util
import json
import os
from functools import lru_cache
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
VERSION = os.environ.get("NH3_MODEL", "1.1")
if VERSION not in ("1.1", "1.2"):
    raise ValueError(f"NH3_MODEL must be 1.1 or 1.2, not {VERSION!r}")
RUNS = {"1.1": "nh3_final_20260905T134204Z", "1.2": "nh3_final_1_2_20261013"}
LABEL = {"1.1": "NH3-FINAL-1.1", "1.2": "NH3-FINAL-1.2"}[VERSION]


def root() -> Path:
    if VERSION == "1.1":
        return Path(os.environ.get("NH3_HARNESS", r"D:/论文-AI4S/Catalyst_Economic_Leverage_Automation_Harness_v0.1"))
    return Path(os.environ.get("NH3_HARNESS_1_2", str(REPO / "provenance" / "nh3_final_1_2" / "source_harness")))


def run_dir() -> Path:
    return root() / "outputs" / RUNS[VERSION]


@lru_cache(maxsize=None)
def core():
    """harness_core of the selected version (the 1.2 file for 1.2, the root's own file for 1.1)."""
    path = root() / "harness_core.py"
    spec = importlib.util.spec_from_file_location("harness_core", path)
    mod = importlib.util.module_from_spec(spec)
    import sys
    sys.modules.setdefault("harness_core", mod)
    spec.loader.exec_module(mod)
    return mod


def cfg() -> dict:
    return yaml.safe_load((run_dir() / "manifest_resolved.yaml").read_text(encoding="utf-8"))


def harness():
    return core().NH3Harness(cfg(), root())


@lru_cache(maxsize=None)
def anchors() -> dict:
    """Headline values of the canonical run of the selected version, read from its results.json."""
    res = json.loads((run_dir() / "results.json").read_text(encoding="utf-8"))
    d, bk = res["deterministic"], res["backward_reachability"] or {}
    out = dict(version=VERSION, label=LABEL, run=RUNS[VERSION], NSTATE=d["process_state_count"],
               F_CAL=float(cfg()["economics"]["calibration_factor"]),
               alpha=bk.get("Ru_activity_break_even_multiplier"))
    for m in ("Fe", "Ru", "Os"):
        f = d["metals"][m]["feasible"]
        out[m] = f["total_cost"]
        out[m + "_optimum"] = (f["T_C"], f["P_bar"], f["Tsep_C"])
    return out


def out_dir(folder) -> Path:
    """Where an analysis writes: the folder itself for 1.1 (existing files), folder/nh3_1_2 for 1.2."""
    p = Path(folder) if VERSION == "1.1" else Path(folder) / "nh3_1_2"
    p.mkdir(parents=True, exist_ok=True)
    return p
