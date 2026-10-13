"""Shared loaders for the revealed-preference validation. Everything is read from the frozen candidate tables and
scored with the frozen code (meoh_candidates.aggregate); nothing frozen is written."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
INV = REPO / "analysis" / "meoh_literature_inversion_2026_10_05"
INLET = REPO / "analysis" / "meoh_inlet_definition_2026_10_12"
for _p in (REPO / "data" / "meoh", INV, HERE):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from meoh_candidates import aggregate  # noqa: E402,F401
from families import cu_based, family, scale_class, scale_class_alt  # noqa: E402,F401

COHORTS = {"printed": INV / "literature_candidates.csv", "extended": INV / "literature_candidates_all_entries.csv"}
TI_FILE = {c: HERE / f"costs_true_inert_{c}.csv" for c in COHORTS}
# scenario -> cost column (S6TI is added from costs_true_inert_<cohort>.csv)
SCENARIOS = {"S6": "cost_recycled_opt_inlet", "S5": "cost_recycled_opt", "S6TI": "cost_S6TI"}
PRIMARY = ("printed", "S6")
BOOT_N, BOOT_SEED = 10_000, 20261013
ANCHORS = {("printed", "S5"): (15, 40), ("printed", "S6"): (28, 40), ("printed", "S6TI"): (18, 40),
           ("extended", "S5"): (35, 83), ("extended", "S6"): (54, 82)}


def load(cohort: str) -> pd.DataFrame:
    """Frozen candidates of one cohort plus the S6-TI cost column, family and scale classes."""
    d = pd.read_csv(COHORTS[cohort])
    ti = pd.read_csv(TI_FILE[cohort])
    if len(ti) != len(d) or not (ti.entry.astype(str).to_numpy() == d.entry.astype(str).to_numpy()).all():
        raise SystemExit(f"STOP: {TI_FILE[cohort].name} is not row-aligned with the frozen {cohort} candidates")
    d["cost_S6TI"] = ti["cost_S6TI"].to_numpy(float)
    # classes only for entries of groups with >= 2 entries (the only ones aggregate() can score; as make_subsets.py)
    multi = d.group.map(d.groupby("group").size()) >= 2
    d["family"] = [family(c, doi) if m else "single_entry_group" for c, doi, m in zip(d.catalyst, d.doi, multi)]
    d["cu_based"] = d.family.map(cu_based)
    d["scale"] = [scale_class(c, doi) if m else "single_entry_group" for c, doi, m in zip(d.catalyst, d.doi, multi)]
    d["scale_alt"] = [scale_class_alt(c, doi) if m else "single_entry_group"
                      for c, doi, m in zip(d.catalyst, d.doi, multi)]
    return d


def scored(d: pd.DataFrame, cost_col: str):
    """aggregate() exactly as frozen, plus the entries of the scored groups that have a finite cost."""
    gm, s = aggregate(d, cost_col, up_col="STY")
    e = d[d.group.isin(gm.group) & np.isfinite(d[cost_col].astype(float))].copy()
    return gm, s, e
