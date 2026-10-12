"""Shared definitions for the inlet-limit definition analysis (run_inlet_definition.py) and the 83 -> 40 group ledger
(run_group_ledger.py).

Everything starts from the frozen candidate tables of analysis/meoh_literature_inversion_2026_10_05 and is scored with
that folder's own code (meoh_candidates.aggregate, mismatch_kinds.classify). Nothing is re-extracted.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
INV = REPO / "analysis" / "meoh_literature_inversion_2026_10_05"
for _p in (REPO / "data" / "meoh", INV):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import meoh_general_model as G  # noqa: E402
from meoh_candidates import aggregate, catalyst_key  # noqa: E402,F401
from mismatch_kinds import classify  # noqa: E402,F401

CANDIDATES = INV / "literature_candidates.csv"                  # printed cohort (frozen primary)
CANDIDATES_ALL = INV / "literature_candidates_all_entries.csv"   # every entry, plot readings included
BANSODE = "10.1039/c2cy20604h"
S6_LIMIT = float(G.NONREACTIVE_MAX)                              # 6.8625 %, the cost model's anchor loop
LIMITS_PCT = (4, 5, 6, "6.86", 8, 10, 12, 15, 20, 25, 30)          # plus "none" (S5)
STABILITY_PCT = (5, 6, "6.86", 8, 10, 12, 15)
BOOT_N, BOOT_SEED = 10_000, 20261012
NEAR_REGRET, NEAR_COST_RATIO = 1.0, 2.0                          # draft PR #69 near-infeasibility split

# Which reactor-inlet species the limit counts.
#   frozen      CH4 + CO + N2 (meoh_general_model.loop_balance `nonreactive_fraction`): the frozen S6 / lim<L> columns
#   true_inert  CH4 + N2 only; CO is excluded because the loop converts recycled CO per pass (x_co='recycled_central')
DEFINITIONS = {"frozen": "CH4 + CO + N2 (frozen)", "true_inert": "CH4 + N2 (true inerts; CO excluded)"}

# frozen columns of literature_candidates.csv that the frozen definition must reproduce
FROZEN_COLUMNS = {"none": "cost_recycled_opt", "6.86": "cost_recycled_opt_inlet",
                  **{str(L): f"cost_recycled_opt_lim{L}" for L in (4, 5, 6, 8, 10, 12, 15, 20, 25, 30)}}

# the frozen reproduction anchors (summary.json limit_sweep / variants of the 2026-10-05 folder)
ANCHORS = {"none": (15, 40), "6.86": (28, 40), "4": (28, 40), "10": (24, 40), "30": (16, 40)}


def limit_value(L):
    """Limit label -> fraction; '6.86' is the anchor loop's exact value G.NONREACTIVE_MAX; 'none' -> None."""
    if L == "none":
        return None
    return S6_LIMIT if str(L) == "6.86" else float(L) / 100.0
