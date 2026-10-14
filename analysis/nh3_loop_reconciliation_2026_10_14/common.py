"""Shared paths, read-only imports of upstream modules, JSON/CSV helpers and provenance hashes.

Nothing upstream is patched or copied: every model function used here is imported from its existing file.
NH3_MODEL is forced to 1.2 (the canonical NH3-FINAL-1.2 run) before `analysis/nh3_model.py` is imported.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import subprocess
import sys
from pathlib import Path

import numpy as np

if os.environ.get("NH3_MODEL", "1.2") != "1.2":
    raise RuntimeError("This analysis runs on NH3-FINAL-1.2 only (NH3_MODEL=1.2)")
os.environ["NH3_MODEL"] = "1.2"

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ANALYSIS = REPO / "analysis"
STAGED = ANALYSIS / "nh3_staged_converter_2026_10_12"
RECOVERY = ANALYSIS / "nh3_ru_net_recovery_boundary_2026_10_12"
COUPLING = ANALYSIS / "nh3_kinetic_cost_coupling_v1"
CLOSED = ANALYSIS / "nh3_si_closed_loop_v1"
FE_FIRST = ANALYSIS / "nh3_fe_first_domain_v1"
CANON = REPO / "provenance" / "nh3_final_1_2" / "source_harness"
OUT = Path(os.environ.get("NH3_RECON_OUT", str(HERE / "outputs")))
WORK = Path(os.environ.get("NH3_RECON_WORK", str(HERE / "work")))

for p in (FE_FIRST, CLOSED, COUPLING, RECOVERY, STAGED, ANALYSIS):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

# Upstream files this analysis imports (blob hashes go to outputs/provenance.json).
UPSTREAM = [
    "provenance/nh3_final_1_2/source_harness/harness_core.py",
    "provenance/nh3_final_1_2/source_harness/configs/nh3_final_1_2.yaml",
    "provenance/nh3_final_1_2/source_harness/outputs/nh3_final_1_2_20261013/manifest_resolved.yaml",
    "provenance/nh3_final_1_2/source_harness/outputs/nh3_final_1_2_20261013/results.json",
    "provenance/nh3_final_1_2/source_harness/inputs/ammonia_activity_volcano_s1_v1.xlsx",
    "analysis/nh3_model.py",
    "analysis/nh3_staged_converter_2026_10_12/kinetics_swap.py",
    "analysis/nh3_staged_converter_2026_10_12/kinetics.py",
    "analysis/nh3_staged_converter_2026_10_12/parameters.yaml",
    "analysis/nh3_staged_converter_2026_10_12/nh3_1_2/kinetics_swap.json",
    "analysis/nh3_ru_net_recovery_boundary_2026_10_12/lifecycle_cashflow.py",
    "analysis/nh3_si_closed_loop_v1/model.py",
    "analysis/nh3_si_closed_loop_v1/loop.py",
    "analysis/nh3_si_closed_loop_v1/si_parameters.json",
    "analysis/nh3_source_matched_loop_v0/figure57_streams.csv",
    "analysis/nh3_kinetic_cost_coupling_v1/coupling.py",
    "analysis/nh3_kinetic_cost_coupling_v1/economics.py",
    "analysis/nh3_kinetic_cost_coupling_v1/kinetic_bridge.py",
    "analysis/nh3_kinetic_cost_coupling_v1/run_study.py",
    "analysis/nh3_kinetic_cost_coupling_v1/cold_worker.py",
    "analysis/nh3_fe_first_domain_v1/source_domains.py",
    "docs/RU_ACTUAL_CATALYST_COST_2026-10-05.md",
]


def blob_hash(rel: str) -> str:
    """Git blob hash of the committed file (HEAD); falls back to hashing the worktree bytes."""
    try:
        out = subprocess.run(["git", "rev-parse", f"HEAD:{rel}"], cwd=REPO, capture_output=True, text=True, timeout=30)
        if out.returncode == 0:
            return out.stdout.strip()
    except Exception:
        pass
    data = (REPO / rel).read_bytes()
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def provenance() -> dict:
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True, text=True).stdout.strip()
    return {"repo_head": head, "python": sys.version, "numpy": np.__version__,
            "scipy": __import__("scipy").__version__,
            "upstream_blob_sha1": {rel: blob_hash(rel) for rel in UPSTREAM}}


def native(v):
    if isinstance(v, np.generic):
        return v.item()
    if isinstance(v, np.ndarray):
        return v.tolist()
    raise TypeError(type(v).__name__)


def clean(o, nd=9):
    if isinstance(o, (float, np.floating)):
        o = float(o)
        return round(o, nd) if math.isfinite(o) else None
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, np.bool_):
        return bool(o)
    if isinstance(o, dict):
        return {str(k): clean(v, nd) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v, nd) for v in o]
    if isinstance(o, np.ndarray):
        return [clean(v, nd) for v in o.tolist()]
    return o


def dump(path: Path, obj, nd=9):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(clean(obj, nd), indent=1, allow_nan=False) + "\n", encoding="utf-8")


def load(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_csv(path: Path, rows, nd=9):
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [clean(r, nd) for r in rows]
    keys = list(dict.fromkeys(k for r in rows for k, v in r.items() if not isinstance(v, (dict, list))))
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in keys})
