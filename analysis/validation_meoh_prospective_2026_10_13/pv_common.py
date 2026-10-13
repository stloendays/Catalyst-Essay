"""Shared definitions of the prospective methanol hold-out test (PREREGISTRATION.md).

Everything is imported from the frozen code, unchanged:
  analysis/meoh_literature_inversion_2026_10_05/meoh_candidates.py   candidates, plant costs, aggregate, bootstrap
  analysis/meoh_literature_inversion_2026_10_05/mismatch_kinds.py    kinds of disagreement
  analysis/meoh_constraint_boundary_2026_10_12/run_rules.py          the pre-registered laboratory rules (RULES,
                                                                    choice_set: ties broken by the higher STY)
  data/meoh/meoh_general_model.py                                    the plant model (S6 limit = G.NONREACTIVE_MAX)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
INV = REPO / "analysis" / "meoh_literature_inversion_2026_10_05"
CB = REPO / "analysis" / "meoh_constraint_boundary_2026_10_12"
for _p in (REPO / "data" / "meoh", INV, CB, REPO / "agent"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import meoh_general_model as G  # noqa: E402
from meoh_candidates import aggregate, bootstrap, catalyst_key  # noqa: E402,F401
from mismatch_kinds import classify  # noqa: E402
from run_rules import RULES, choice_set  # noqa: E402

FROZEN_CANDIDATES = INV / "literature_candidates.csv"
SCEN = {"S6": "cost_recycled_opt_inlet",   # primary (supervisor 2026-10-12): reactor-inlet CH4+CO+N2 <= 6.86 %
        "S5": "cost_recycled_opt"}          # frozen primary of 2026-10-12, reported alongside
RULE_FOR = {"S6": "S", "S5": "STY"}         # the rule the pre-registered out-of-paper selection chose in every fold
BOOT_N, BOOT_SEED = 10_000, 20261006       # frozen bootstrap (meoh_candidates.bootstrap)
NEW_SEED = 20261013                        # resamples of the new batch (PREREGISTRATION.md section 4)


NEW_RECORDS = HERE / "out" / "records_normalized.csv"
CORRECTIONS = HERE / "corrections.csv"


def _isnum(s) -> bool:
    try:
        float(s)
        return True
    except (TypeError, ValueError):
        return False


def load_new_records(corrected: bool = True, log: list | None = None) -> pd.DataFrame:
    """The new batch's normalized records (frozen read_records convention); with corrected=True the PDF-check
    corrections (corrections.csv: doi, entry_label, field, extracted, corrected, source, note) replace single fields,
    each of which must match exactly one record."""
    from meoh_candidates import read_records
    rec = read_records(NEW_RECORDS)
    if not corrected or not CORRECTIONS.exists():
        return rec
    cor = pd.read_csv(CORRECTIONS, keep_default_na=False, na_values=[""], dtype=str)
    rec = rec.copy()
    for r in cor.to_dict("records"):
        m = (rec.doi == r["doi"]) & (rec.entry_label == r["entry_label"])
        if m.sum() != 1:
            raise SystemExit(f"correction does not match exactly one record: {r}")
        new = r["corrected"]
        old = rec.loc[m, r["field"]].iloc[0]
        rec[r["field"]] = rec[r["field"]].astype(object)
        rec.loc[m, r["field"]] = (float(new) if _isnum(new) else new) if new not in ("", None) else np.nan
        if log is not None:
            log.append(dict(doi=r["doi"], entry_label=r["entry_label"], field=r["field"], before=old, after=new))
    for c in set(cor["field"]):      # restore the numeric dtype of a corrected numeric column
        if rec[c].dtype == object:
            conv = pd.to_numeric(rec[c], errors="coerce")
            if conv.notna().sum() == rec[c].notna().sum():
                rec[c] = conv
    return rec


def group_table(cand: pd.DataFrame, scen: str) -> pd.DataFrame:
    """One row per scored group (frozen convention: entries with a finite cost in the scenario's column; groups with
    at least two of them). Leaders as meoh_candidates.group_metrics scores them (a tied STY lead counts as the
    cheapest tied entry); the pre-registered rule's choice set (run_rules.choice_set); chance = 1 / n; and the
    laboratory differences between the plant-cost leader and the STY leader."""
    col = SCEN[scen]
    gm, _ = aggregate(cand, col)
    gm, _ = classify(cand, gm, col)
    f = cand[np.isfinite(cand[col].astype(float))]
    rows = []
    for r in gm.itertuples():
        g = f[f.group == r.group]
        tied = g[g.STY >= g.STY.max() - 1e-12]
        lab = tied[col].idxmin()
        plant = g[col].idxmin()
        cp = float(g.at[plant, col])
        out = dict(group=r.group, doi=r.doi, n=len(g), mismatch=bool(r.top1_mismatch), regret=float(r.regret),
                   kind=r.kind, chance=1.0 / len(g), lab_leader=g.at[lab, "catalyst"],
                   plant_leader=g.at[plant, "catalyst"])
        for name in ("STY", "S"):
            cs = choice_set(g, RULES[name](g))
            out[f"{name}_correct"] = bool(plant in cs.index)
            out[f"{name}_regret"] = float(((cs[col] - cp) / cp).min())
            out[f"{name}_choice"] = " | ".join(cs.catalyst)
        out["rule_correct"] = out[f"{RULE_FOR[scen]}_correct"]
        out["sty_leader_is_most_selective"] = bool(lab in choice_set(g, RULES["S"](g)).index)
        out["plant_more_selective"] = bool(g.at[plant, "SMeOH"] > g.at[lab, "SMeOH"])
        out["plant_less_co"] = bool(g.at[plant, "SCO"] < g.at[lab, "SCO"])
        out["plant_higher_x"] = bool(g.at[plant, "X"] > g.at[lab, "X"])
        out["plant_cooler"] = bool(g.at[plant, "T_C"] < g.at[lab, "T_C"])
        rows.append(out)
    return pd.DataFrame(rows)


def paper_boot(t: pd.DataFrame, stats: dict, n=BOOT_N, seed=BOOT_SEED) -> dict:
    """Paper-cluster bootstrap (papers resampled with replacement, every group of a drawn paper enters).
    stats: name -> (numerator column or callable on t, denominator mask column or None). Returns
    {name: {value, ci95}} for ratio statistics sum(num) / count(den)."""
    papers = sorted(t.doi.unique())
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(papers), size=(n, len(papers)))
    out = {}
    for name, (num, den) in stats.items():
        x = t[num] if isinstance(num, str) else num(t)
        m = pd.Series(True, index=t.index) if den is None else t[den]
        per_num = (x.astype(float) * m).groupby(t.doi).sum().reindex(papers).to_numpy()
        per_den = m.astype(float).groupby(t.doi).sum().reindex(papers).to_numpy()
        S, C = per_num[idx].sum(1), per_den[idx].sum(1)
        with np.errstate(invalid="ignore", divide="ignore"):
            v = S / C
        v = v[np.isfinite(v)]
        val = float(per_num.sum() / per_den.sum()) if per_den.sum() else float("nan")
        lo, hi = (np.percentile(v, [2.5, 97.5]) if len(v) else (np.nan, np.nan))
        out[name] = dict(value=val, numerator=float(per_num.sum()), denominator=float(per_den.sum()),
                         ci95=[float(lo), float(hi)], valid_resamples=int(len(v)))
    return out
