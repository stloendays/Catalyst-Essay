#!/usr/bin/env python3
"""Unfrozen Re/TiO2 lab-STY normalization and net-metal-replacement price scan.

Recompute process optima over m and purge for every candidate in the SAME
reported Re/TiO2, 100 bar, H2/CO2=4, 10 NL/(gcat h) group. Treat the original
maximum STY as fixed, separately for per-total-catalyst and per-Re bases.
The paper's per-g-Re value is converted by the printed metal wt%.

Hypothetical price EUR/kg_Re, recovery fraction and replacement life test
ONLY the existing G.economics annual cat-replacement term, which is additive.
They omit initial precious-metal asset financing, support and manufacture cost,
market price validation, deactivation, and secondary metal recovery OPEX.
No manuscript or frozen S5 figure is changed.

This is a FORMULATION comparison (1wt vs 5wt Re/TiO2), not a cross-element
catalyst comparison. No single STY normalization is a universal answer.
"""
from __future__ import annotations

import argparse
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "analysis/meoh_engineering_envelope_2026_10_12"))
sys.path.insert(0, str(ROOT / "analysis/meoh_engineering_review_2026_10_12"))
import run_engineering_envelopes as E  # noqa: E402
import audit_fixed_sty_leader as F  # noqa: E402

J = E.J
M = E.M
G = E.G
DOI = "10.1021/acscatal.5c05984"
GROUP_SUFFIX = "100 bar | H2/CO2 4 | 10 NL/g/h"
MATCHED_ENTRIES = ("Table 4 row 3", "Table 4 row 11")
PRICE_PER_KG_RE_EUR = (0., 500., 2000., 10000., 50000.)
LIFE_YEARS = (1., 5.)
RECOVERY_FRACTIONS = (0., 0.9)
INLETS = tuple(J.INLET_NAMES)
CAP_NAMES = ("uncapped", "anchor_1x", "anchor_2x", "anchor_4x", "inventory_2x")
MAX_M = (10., 25.)
COMPARISONS = ("all9_per_gcat", "all9_per_gRe",
               "matched200_per_gcat", "matched200_per_gRe")
BASELINE = (ROOT / "analysis/meoh_engineering_envelope_2026_10_12"
            / "results/engineering_candidate_optima.csv")
RAW_SOURCE = ROOT / "agent/extraction/out/records_normalized.csv"


def load_group():
    f = J.candidates()
    f = f.loc[(f.doi == DOI) & f.group.str.endswith(GROUP_SUFFIX)].copy()
    if len(f) != 9 or f.group.nunique() != 1:
        raise AssertionError("Expected nine source-normalized Re/TiO2 Table 4 entries in one group")
    source = pd.read_csv(RAW_SOURCE)
    source = source.loc[source.doi == DOI]
    fractions = []
    for r in f.itertuples(index=False):
        rows = source.loc[source.entry_label == r.entry]
        if len(rows) != 1:
            raise AssertionError(f"Missing or nonunique Re source entry {r.entry}")
        orig = rows.iloc[0]
        if orig.sty_basis != "per_g_metal":
            raise AssertionError(f"Expected per-g-Re printed STY: {r.entry}")
        wt = float(orig.metal_wt_pct)
        if wt not in (1., 5.):
            raise AssertionError(f"Unexpected Re wt fraction: {wt}")
        total_sty = float(orig.STY_g_gcat_h)
        metal_sty = float(orig.STY_g_gmetal_h)
        if not np.isclose(total_sty, metal_sty * wt / 100., atol=1e-7, rtol=1e-7):
            raise AssertionError(f"STY metal-catalyst conversion mismatch: {r.entry}")
        if not np.isclose(r.STY, total_sty, atol=1e-7, rtol=1e-7):
            raise AssertionError(f"Printed STY normalizer has drifted: {r.entry}")
        fractions.append(wt / 100.)
    f["re_mass_fraction"] = fractions
    f["STY_per_g_Re"] = f.STY / f.re_mass_fraction
    pair = f[f.entry.isin(MATCHED_ENTRIES)].copy()
    if len(pair) != 2 or not np.allclose(pair.T_C.to_numpy(), 200.):
        raise AssertionError("The 200 C matched, 500 C pre-reduced pair drifted")
    if not np.allclose(pair.P_bar.to_numpy(), 100.):
        raise AssertionError("The matched pair changed reaction pressure")
    if {int(round(x * 100)) for x in pair.re_mass_fraction} != {1, 5}:
        raise AssertionError("Matched Re loading pair no longer matches paper")
    return f


def source_basis():
    f = load_group()
    pair = f[f.entry.isin(MATCHED_ENTRIES)]
    d = {r.entry: r for r in pair.itertuples(index=False)}
    assert np.isclose(d[MATCHED_ENTRIES[0]].STY, 0.55)
    assert np.isclose(d[MATCHED_ENTRIES[1]].STY, 0.90)
    assert np.isclose(d[MATCHED_ENTRIES[0]].STY_per_g_Re, 55.)
    assert np.isclose(d[MATCHED_ENTRIES[1]].STY_per_g_Re, 18.)
    return {
        "original_source_doi": DOI,
        "units": {"per_g_total_catalyst": "g MeOH / (g total catalyst h)",
                  "per_g_re": "g MeOH / (g metallic Re h)"},
        "matched_200C": {
            "one_wt_per_total": 0.55, "five_wt_per_total": 0.90,
            "one_wt_per_re": 55., "five_wt_per_re": 18.,
            "per_total_lab_winner": "5 wt % Re/TiO2",
            "per_metal_lab_winner": "1 wt % Re/TiO2",
            "same_pressure_bar": 100., "same_temperature_C": 200.,
            "same_pre_reduction_C": 500.,
        },
        "full_group": {
            "candidates": len(f),
            "per_total_STY_leader": str(f.loc[f.STY.idxmax(), "catalyst"]),
            "per_Re_STY_leader": str(f.loc[f.STY_per_g_Re.idxmax(), "catalyst"]),
            "note": "The group spans different reaction T/pre-reductions; only the two-source-entry matched pair tests equal T and pre-reduction directly.",
        },
    }


def replacement_cost_eur_t(catalyst_t, re_fraction, price_eur_kg_Re, life_y, unrecovered):
    """Exact incremental NPC from original G.economics(cat_price_eur_kg,...).

    net EUR/kg total catalyst = (wt Re) * metal EUR/kg * (1 - recovery).
    Annual replacement EUR = total catalyst t * 1000 * net EUR/kg / life.
    NPC gross-up / 0.90 matches the unmodified economic model.
    """
    if not (0 <= unrecovered <= 1):
        raise ValueError("The unrecovered fraction must lie in [0,1]")
    if life_y <= 0 or price_eur_kg_Re < 0:
        raise ValueError("Life must be positive and price nonnegative")
    return (np.asarray(catalyst_t, dtype=float) * 1000. * float(re_fraction) *
            float(price_eur_kg_Re) * float(unrecovered) /
            (float(life_y) * float(M.PROD_TPY) * 0.90))


def validate_additivity(f):
    """Cross-check the analytic replacement formula against model-priced G.cost."""
    r = f.loc[f.entry == MATCHED_ENTRIES[0]].iloc[0]
    c = dict(X=float(r.X), SMeOH=float(r.SMeOH), SCO=float(r.SCO),
             SCH4=float(r.SCH4), STY=float(r.STY))
    args = dict(purge=0.02, x_co="recycled_central", P_bar=float(r.P_bar),
                h2_co2=float(r.h2_co2), T_C=float(r.T_C),
                STY_per_g_cat=float(r.STY))
    base = G.cost(c, **args)
    price = 2000.
    life = 5.
    recovery = 0.90
    priced = G.cost(c, **args, cat_price_eur_kg=price * (1-recovery) *
                    float(r.re_mass_fraction), cat_life_y=life)
    actual = float(priced["cost_eur_t"]) - float(base["cost_eur_t"])
    predicted = float(replacement_cost_eur_t(
        base["catalyst_t"], float(r.re_mass_fraction), price, life, 1-recovery))
    if not np.isclose(actual, predicted, atol=1e-9, rtol=1e-8):
        raise AssertionError(f"Replacement penalty failed exact model crosscheck: {actual} versus {predicted}")
    return {"tested_price_eur_kg_Re": price, "tested_life_y": life,
            "tested_Re_recovery": recovery, "penalty_model_EUR_t": actual}


def states_for_candidate(row):
    """One expensive kinetic/loop calculation per (m,p), reused across all prices."""
    x0 = float(row.X)
    xeq, roots = J.feed_eq(float(row.h2_co2), float(row.y_co2),
                           float(row.T_C), float(row.P_bar))
    if x0 >= xeq * (1 - 1e-10):
        states = [(1., x0)]
    else:
        q = x0 / xeq
        states = [(float(m), float(x0 if m == 1 else xeq *
                  (1 - (1-q) ** m))) for m in E.LOADING_GRID]
    blocks = []
    for m, x in states:
        if not 0 < x < 1:
            continue
        sty = float(row.STY) * x / (x0*m)
        c = dict(X=x, SMeOH=float(row.SMeOH), SCH4=float(row.SCH4),
                 SCO=float(row.SCO), STY=sty, P_bar=float(row.P_bar),
                 h2_co2=float(row.h2_co2), T_C=float(row.T_C))
        with np.errstate(all="ignore"), warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            e = E.evaluate_grid(c)
        e["m"] = np.full(len(J.GRID), m)
        e["purge"] = J.GRID.copy()
        blocks.append(e)
    if not blocks:
        raise AssertionError(f"No states tested for row {row.row_id}")
    return {k: np.concatenate([b[k] for b in blocks]) for k in blocks[0]}


def possible_optima(row, e):
    results = []
    for max_m in MAX_M:
        allowed_m = e["m"] <= max_m + 1e-10
        for inlet in INLETS:
            for cap in CAP_NAMES:
                valid = allowed_m & E.feasible_mask(e, J.LIMITS[inlet], E.CAPS[cap])
                for metal_price in PRICE_PER_KG_RE_EUR:
                    for life_y in LIFE_YEARS:
                        for recovery in RECOVERY_FRACTIONS:
                            key = dict(row_id=int(row.row_id), group=str(row.group),
                                       doi=str(row.doi), entry=str(row.entry),
                                       catalyst=str(row.catalyst),
                                       T_C=float(row.T_C),
                                       re_mass_fraction=float(row.re_mass_fraction),
                                       max_m=int(max_m), inlet=inlet, cap=cap,
                                       price_eur_kg_Re=metal_price, life_y=life_y,
                                       re_recovery_fraction=recovery)
                            if not valid.any():
                                results.append(dict(key, feasible=False, cost=np.nan,
                                                    base_cost=np.nan, metal_replacement_eur_t=np.nan,
                                                    catalyst_t=np.nan, chosen_m=np.nan,
                                                    chosen_purge=np.nan))
                                continue
                            replacement = replacement_cost_eur_t(
                                e["catalyst_t"], row.re_mass_fraction, metal_price,
                                life_y, 1-recovery)
                            priced = e["cost_eur_t"] + replacement
                            j = int(np.argmin(np.where(valid, priced, np.inf)))
                            if not np.isfinite(priced[j]):
                                raise AssertionError("Invalid priced optimum")
                            results.append(dict(key, feasible=True, cost=float(priced[j]),
                                                base_cost=float(e["cost_eur_t"][j]),
                                                metal_replacement_eur_t=float(replacement[j]),
                                                catalyst_t=float(e["catalyst_t"][j]),
                                                chosen_m=float(e["m"][j]),
                                                chosen_purge=float(e["purge"][j])))
    return results


def assert_prior_unpriced(candidate_results):
    prior = pd.read_csv(BASELINE)
    baseline = candidate_results[(candidate_results.price_eur_kg_Re == 0.) &
                                 (candidate_results.life_y == 1.) &
                                 (candidate_results.re_recovery_fraction == 0.)]
    merged = baseline.merge(prior, on=["row_id", "max_m", "inlet", "cap"],
                            how="left", validate="one_to_one",
                            suffixes=("_now", "_original"), indicator=True)
    if (merged._merge != "both").any() or len(merged) != len(baseline):
        raise AssertionError("Original equipment scan candidate identity drifted")
    same = np.isclose(merged.cost_now, merged.cost_original,
                      rtol=2e-8, atol=2e-5, equal_nan=True)
    if not same.all():
        bad = merged.loc[~same, ["row_id", "max_m", "inlet", "cap"]]
        raise AssertionError(f"Zero-price rerun does not reproduce PR #56: {bad.head().to_dict('records')}")
    return len(merged)


def summarize(f, candidate_results):
    metadata = source_basis()
    classifiers = {
        "all9_per_gcat": f,
        "all9_per_gRe": f.assign(STY=f.STY_per_g_Re),
        "matched200_per_gcat": f[f.entry.isin(MATCHED_ENTRIES)],
        "matched200_per_gRe": f[f.entry.isin(MATCHED_ENTRIES)].assign(
            STY=lambda x: x.STY_per_g_Re),
    }
    keys = ["max_m", "inlet", "cap", "price_eur_kg_Re", "life_y", "re_recovery_fraction"]
    rows = []
    for values, batch in candidate_results.groupby(keys, dropna=False, sort=True):
        case = dict(zip(keys, values))
        prices = batch.set_index("row_id").cost
        for basis, cohort in classifiers.items():
            r = F.classify_group(cohort, prices)
            eligible = r["status"] == "original_sty_leader_feasible"
            rows.append(dict(case, comparator=basis, group=r["group"],
                             independent_papers=1, original_entries=len(cohort),
                             feasible_entries=r["candidates_feasible"],
                             original_lab_leader=r["original_STY_leader"],
                             lab_leader_STY=float(r["original_STY_max"]),
                             selected_economic_leader=r["economic_winner"],
                             status=r["status"], material_gt5=r["material_gt5"],
                             economic_reversal=r["mismatch"],
                             regret=r["regret"], kind=r["kind"],
                             sameT_other_formulation_gt5=r["sameT_other_catalyst_gt5"],
                             source_lab_leader_is_feasible=eligible))
    reported = pd.DataFrame(rows)
    baseline = reported[
        (reported.max_m == 10) & (reported.inlet == "inlet_6p86") &
        (reported.cap == "uncapped") &
        (reported.price_eur_kg_Re == 0) & (reported.life_y == 1) &
        (reported.re_recovery_fraction == 0)]
    def one(which):
        o = baseline.loc[baseline.comparator == which]
        if len(o) != 1:
            raise AssertionError("Missing zero-price baseline comparator " + which)
        return o.iloc[0]
    if (not one("matched200_per_gcat").sameT_other_formulation_gt5 or
        one("matched200_per_gRe").economic_reversal or
        one("all9_per_gRe").kind != "other temperature"):
        raise AssertionError("Observed source-STY denominator change did not reproduce the expected economic interpretation")
    canonical = {}
    for label in COMPARISONS:
        val = one(label)
        canonical[label] = dict(
            laboratory_leader=str(val.original_lab_leader),
            economic_leader=str(val.selected_economic_leader),
            mismatch=bool(val.economic_reversal),
            kind=str(val.kind), regret=float(val.regret),
            status=str(val.status))
    price_robust = {}
    for max_m in MAX_M:
        for cap in CAP_NAMES:
            for basis in COMPARISONS:
                x = reported.loc[(reported.max_m == max_m) &
                                 (reported.cap == cap) &
                                 (reported.comparator == basis) &
                                 (reported.inlet.isin(INLETS))]
                # each price/lifetime/recovery hypothesis must survive all three inlet designs
                groups = x.groupby(["price_eur_kg_Re", "life_y",
                                    "re_recovery_fraction"], dropna=False)
                pass_case = {str((float(p),float(l),float(r))):
                    bool(len(g) == 3 and g.sameT_other_formulation_gt5.all())
                    for (p,l,r),g in groups}
                price_robust[f"m{int(max_m)}__{cap}__{basis}"] = {
                    "hypotheses_tested": len(pass_case),
                    "sameT_material_3inlet_survives": sum(pass_case.values()),
                    "hypothesis_labels_surviving": [k for k,v in pass_case.items() if v],
                    "not_surviving": [k for k,v in pass_case.items() if not v],
                }
    info = {
        "scope": "Single source paper and its NINE Re/TiO2 experimental points; no all-field claim.",
        "source": metadata,
        "candidate_rows": len(f), "original_group_count": 1,
        "price_scenarios": {
            "EUR_kg_Re": PRICE_PER_KG_RE_EUR,
            "lifetime_y": LIFE_YEARS,
            "recovery": RECOVERY_FRACTIONS,
            "price_is_market_observation": False,
        },
        "cost_model": {
            "existing_code_function": "meoh_general_model.economics(..., cat_price_eur_kg, cat_life_y)",
            "incremental_replacement_EUR_per_t": "catalyst_t * 1000 * (wt_Re/100) * (EUR_kg_Re) * (1-recovery) / (life_y * plant_tpy * 0.90)",
            "metal_outlay_initial_capital_annualization_included": False,
            "support_precursor_manufacturing_and_recovery_OPEX_included": False,
            "reason": "Respect original model's optional additive catalyst-replacement cost; no invented real-world spot price or financial asset valuation.",
        },
        "zero_price_6p86_no_cap_m10": canonical,
        "three_inlet_hypothesis_robustness": price_robust,
        "source_quality": [
            "200 C comparison aligns pre-reduction at 500 C but uses different metal loading.",
            "Other entries in the nine-point group vary temperature or pre-reduction temperature.",
            "Original paper's <1% reported selectivities are censored values; extracted closure treats some as zero.",
            "Priced Re scenarios are hypotheses only and exclude initial metal-financing and selective deactivation effects.",
            "One source paper cannot provide independent cross-paper replication.",
        ],
    }
    return reported, info


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, default=HERE / "results")
    args = p.parse_args()
    f = load_group()
    additive = validate_additivity(f)
    batches = []
    for row in f.itertuples(index=False):
        e = states_for_candidate(row)
        batches.extend(possible_optima(row, e))
        print(f"Completed source Re/TiO2 row={row.row_id} {row.entry}", flush=True)
    candidates = pd.DataFrame(batches)
    covered = assert_prior_unpriced(candidates)
    summary_rows, summary = summarize(f, candidates)
    summary["regression"] = {
        "zero_price_optima_matched_prior_full_engineering_scan": covered,
        "additive_price_formula_matches_original_TEA": additive,
    }
    args.output.mkdir(parents=True, exist_ok=True)
    candidates.to_csv(args.output / "re_candidate_price_optima.csv",
                      index=False, float_format="%.12g")
    summary_rows.to_csv(args.output / "re_lab_normalization_decisions.csv",
                        index=False, float_format="%.12g")
    (args.output / "re_normalization_price_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "source_basis": summary["source"]["matched_200C"],
        "baseline": summary["zero_price_6p86_no_cap_m10"],
        "scenario_count": len(summary_rows),
        "priced_candidate_optima": len(candidates),
        "prior_baseline_checks": covered,
        "source_comparison_scope": summary["scope"],
    }, indent=2))


if __name__ == "__main__":
    main()
