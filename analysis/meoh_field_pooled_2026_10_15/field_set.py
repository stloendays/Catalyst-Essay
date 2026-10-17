"""Which methanol candidate set a robustness script runs on: MEOH_FIELD_SET=first (default) or combined.

  first     the 40 comparison groups of the first extraction, exactly as committed:
              analysis/meoh_literature_inversion_2026_10_05/literature_candidates.csv (printed cohort, 351 rows)
              analysis/meoh_literature_inversion_2026_10_05/literature_candidates_all_entries.csv (plot readings too)
              agent/extraction/out/records_normalized.csv (records)
            and every script writes to its own committed output folder.
  combined  the first set plus the 41 groups of the second extraction (22 papers, 2025-11-05 to 2026-10-13):
              analysis/validation_meoh_prospective_2026_10_13/new_candidates_costed.csv (printed cohort, 348 rows,
              PDF-checked records, costed by the frozen meoh_candidates.plant_costs)
              all entries: build_candidates(load_new_records(corrected=True), printed_only=False), costed here with
              the same plant_costs call as the first set's all-entries table (cached in robustness/all_entries/)
              records: the frozen records followed by the corrected second-extraction records
            and every script writes to analysis/meoh_field_pooled_2026_10_15/robustness/<analysis>/.

The combined tables keep the first set's rows first and in their committed order (column `batch` = first / second),
so a script's first-set part, grid and cache keys are those of the committed run. A second-set column the first set
does not have is dropped; a first-set column the second set does not have is NaN there.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
INV = REPO / "analysis" / "meoh_literature_inversion_2026_10_05"
PV = REPO / "analysis" / "validation_meoh_prospective_2026_10_13"
ROBUSTNESS = HERE / "robustness"

FIRST_CANDIDATES = INV / "literature_candidates.csv"
FIRST_ALL_ENTRIES = INV / "literature_candidates_all_entries.csv"
SECOND_CANDIDATES = PV / "new_candidates_costed.csv"
SECOND_ALL_ENTRIES = ROBUSTNESS / "all_entries" / "second_all_entries_costed.csv"

SET = os.environ.get("MEOH_FIELD_SET", "first").strip().lower()
if SET not in ("first", "combined"):
    raise SystemExit(f"MEOH_FIELD_SET must be 'first' or 'combined', not {SET!r}")
COMBINED = SET == "combined"
WORKERS = int(os.environ.get("PV_WORKERS", "2"))       # plant-model processes for the second set's all-entries table


def out_dir(analysis: str, default: Path) -> Path:
    """The committed folder for the first set; robustness/<analysis>/ for the combined set."""
    if not COMBINED:
        return default
    d = ROBUSTNESS / analysis
    d.mkdir(parents=True, exist_ok=True)
    return d


def _pool(first: pd.DataFrame, second: pd.DataFrame) -> pd.DataFrame:
    assert not set(first.doi) & set(second.doi), "a paper appears in both extractions"
    assert not set(first.group) & set(second.group), "a group id appears in both extractions"
    second = second[[c for c in first.columns if c in second.columns]]
    out = pd.concat([first.assign(batch="first"), second.assign(batch="second")], ignore_index=True)
    for c in ("other_products", "plot_read", "printed", "sty_printed", "ch4_printed", "co_printed"):
        if c in out:
            out[c] = out[c].astype(str).str.lower().isin(["true", "1"])
    return out


def candidates() -> pd.DataFrame:
    """Printed-value candidate table (the field result's primary cohort)."""
    first = pd.read_csv(FIRST_CANDIDATES)
    if not COMBINED:
        return first
    return _pool(first, pd.read_csv(SECOND_CANDIDATES))


def candidates_all_entries() -> pd.DataFrame:
    """Every entry, plot readings included (the plot-read cohort)."""
    first = pd.read_csv(FIRST_ALL_ENTRIES)
    if not COMBINED:
        return first
    return _pool(first, second_all_entries())


def _pv():
    """pv_common of the second extraction. Its rule module imports a sibling module named `common`; a caller that
    already imported another analysis folder's `common` (e.g. analysis/meoh_inlet_definition_2026_10_12) would shadow
    it, so that entry is set aside while pv_common loads and restored afterwards."""
    if "pv_common" in sys.modules:
        return sys.modules["pv_common"]
    if str(PV) not in sys.path:
        sys.path.insert(0, str(PV))
    held = sys.modules.pop("common", None)
    try:
        import pv_common  # noqa: E402  (puts data/meoh and the inversion folder on sys.path)
    finally:
        if held is not None:
            sys.modules["common"] = held
    return pv_common


def records() -> pd.DataFrame:
    """Extracted records the candidates are built from (catalyst names and compositions)."""
    if str(INV) not in sys.path:
        sys.path.insert(0, str(INV))
    from meoh_candidates import read_records
    first = read_records()
    if not COMBINED:
        return first
    return pd.concat([first, _pv().load_new_records(corrected=True)], ignore_index=True)


def second_all_entries() -> pd.DataFrame:
    """The second extraction's all-entries table, costed once with the first set's call
    (meoh_candidates.plant_costs(row, RHO_SCALES), as run_literature_inversion.py) and cached."""
    if SECOND_ALL_ENTRIES.exists():
        return pd.read_csv(SECOND_ALL_ENTRIES)
    from multiprocessing import Pool
    pv = _pv()
    from meoh_candidates import RHO_SCALES, ROW_KEYS, build_candidates, plant_costs_star
    cand = build_candidates(pv.load_new_records(corrected=True), printed_only=False)
    keys = sorted({tuple(float(r[k]) for k in ROW_KEYS) for r in cand[ROW_KEYS].to_dict("records")})
    with Pool(WORKERS) as pool:
        res = pool.map(plant_costs_star, [(dict(zip(ROW_KEYS, k)), RHO_SCALES) for k in keys], chunksize=2)
    table = dict(zip(keys, res))
    costs = pd.DataFrame([table[tuple(float(r[k]) for k in ROW_KEYS)] for r in cand[ROW_KEYS].to_dict("records")],
                         index=cand.index)
    out = pd.concat([cand, costs], axis=1)
    SECOND_ALL_ENTRIES.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(SECOND_ALL_ENTRIES, index=False, float_format="%.12g")
    return pd.read_csv(SECOND_ALL_ENTRIES)


def first_part(frame: pd.DataFrame) -> pd.DataFrame:
    """The first-extraction rows of a (possibly combined) table, for the reproduction anchors."""
    return frame[frame.batch == "first"] if "batch" in frame else frame
