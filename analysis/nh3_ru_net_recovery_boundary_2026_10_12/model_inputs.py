"""Selected NH3 model (NH3_MODEL=1.1 | 1.2), its frozen response surface (read-only) and its golden references.

Both run scripts of this folder use the same loader. The cached response surface of the selected harness root is
read directly and checked against the manifest; it is never rebuilt (NH3Harness.build_or_load_response would rebuild
a missing or mismatched cache, which is not acceptable for a frozen model). In the cached case the array is the same
one build_or_load_response returns.

    NH3_MODEL=1.1  NH3_HARNESS=<1.1 root>      outputs in this folder (the committed NH3-FINAL-1.1 files)
    NH3_MODEL=1.2  NH3_HARNESS_1_2=<1.2 root>  outputs in nh3_1_2/

Golden references of the selected model come from figures/composite/fig2 (1.1) and figures/composite/fig2/nh3_1_2
(1.2), written by fig2_ru_actual_cost.py with the same own-bed arithmetic (effective price p (1 - r) / u, bed factor
ACTIVE_FRACTION * BED_DENSITY / (u w rho), KAAP loop = 90 bar, -20 C separator).
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "analysis"))
import nh3_model as NM  # noqa: E402

FIG2 = REPO / "figures" / "composite" / "fig2"
# fig2_ru_bed_sensitivity.csv key -> (loop, physical recovery) of the own-bed rows
BED_KEYS = {"supp_rec90": ("main", 0.90), "supp_rec_hi": ("main", 0.9555),
            "kaap90": ("KAAP", 0.90), "kaap_hi": ("KAAP", 0.9555)}


def harness():
    """(harness_core module, NH3Harness, anchors of the selected canonical run)."""
    return NM.core(), NM.harness(), NM.anchors()


def frozen_response(h, anchors):
    if h.NSTATE != anchors["NSTATE"]:
        raise RuntimeError(f"{NM.LABEL}: harness has {h.NSTATE} process states, canonical run {anchors['NSTATE']}")
    cp = h.response_cache_path()
    if not cp.exists():
        raise RuntimeError(f"Frozen cached response surface unavailable ({cp}): do not rebuild implicitly")
    z = np.load(cp)
    response, egrid = z["response"], z["EGRID"]
    if response.shape != (h.NSTATE, len(h.EGRID)) or not np.allclose(egrid, h.EGRID):
        raise RuntimeError(f"Cached response surface {cp.name} does not match the manifest: do not rebuild implicitly")
    return response


def fig2_bed_sensitivity_path() -> Path:
    return (FIG2 if NM.VERSION == "1.1" else FIG2 / "nh3_1_2") / "fig2_ru_bed_sensitivity.csv"


def fig2_own_bed():
    """Own-bed Ru/C costs and the Fe reference of each loop for the selected model, from Fig. 2's bed table.

    Returns ({(loop, recovery, w_Ru, rho): cost}, {"main": Fe optimum, "KAAP": Fe in the KAAP loop}, path).
    """
    path = fig2_bed_sensitivity_path()
    costs, fe = {}, {}
    with path.open(encoding="utf-8", newline="") as fh:
        for x in csv.DictReader(fh):
            if x["key"] not in BED_KEYS:
                continue
            loop, r = BED_KEYS[x["key"]]
            costs[(loop, r, float(x["w_Ru"]), float(x["rho_bed_kg_m3"]))] = float(x["cost"])
            ref = float(x["Fe_reference_cost"])
            if fe.setdefault(loop, ref) != ref:
                raise AssertionError(f"{path}: two Fe references for the {loop} loop")
    if set(fe) != {"main", "KAAP"}:
        raise AssertionError(f"{path}: Fe reference missing for {set(('main', 'KAAP')) - set(fe)}")
    return costs, fe, path
