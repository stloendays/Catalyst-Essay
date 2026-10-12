"""Read-only audit of the Pérez-Fortes plant benchmark's accounting boundary.

Questions:
1. Does the plotted 'like-for-like' total actually sum the displayed model
   subcomponents, or substitute the reference plant's fixed O&M?
2. How much of the apparent total-cost agreement is a stoichiometric H2
   commodity baseline shared by every CO2-to-methanol process?
3. Which independent process comparisons (carbon efficiency, recycle ratio,
   compression and capital) still differ from the reference plant?

Never changes the cost model, the paper or a scientific result. It reads only
committed CSV/JSON/source constants and writes separate review artifacts.
"""
from __future__ import annotations

import argparse
import ast
import csv
import json
import math
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BENCH = REPO / "analysis" / "meoh_plant_benchmark_2026_10_06"
MODEL_PATH = REPO / "data" / "meoh" / "meoh_d01_model.py"


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def unique(seq: list, label: str):
    if len(seq) != 1:
        raise ValueError(f"Expected exactly one {label}; found {len(seq)}")
    return seq[0]


def weight_constants(model_path: Path) -> dict[str, float]:
    """Read the actual model's chemical molecular weights without importing it."""
    module = ast.parse(model_path.read_text(encoding="utf-8"))
    for stmt in module.body:
        if isinstance(stmt, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "MW" for t in stmt.targets
        ):
            mw = ast.literal_eval(stmt.value)
            return {k: float(v) for k, v in mw.items()}
    raise ValueError("Molecular-weight table MW missing from model")


def benchmark_cost_rows(cost_rows: list[dict]) -> dict[str, dict]:
    b3 = [r for r in cost_rows if r["case"].startswith("B3 Perez-Fortes")]
    if not b3:
        raise ValueError("No B3 Pérez-Fortes rows")
    by_term: dict[str, dict] = {}
    for row in b3:
        if row["term"] in by_term:
            raise ValueError(f"Duplicate Pérez-Fortes component {row['term']}")
        by_term[row["term"]] = row
    needed = (
        "H2",
        "electricity + utilities",
        "catalyst replacement",
        "capital (annuity at 8 %, 20 y)",
        "fixed O&M",
        "residual direct + 10 % of NPC (anchor convention)",
        "TOTAL, like-for-like (feed + power + catalyst + capital + reference FCP)",
        "TOTAL, anchor convention",
    )
    for key in needed:
        if key not in by_term:
            raise ValueError(f"Required B3 term absent: {key}")
    return by_term


def ref_values(records: list[dict], reference: str = "PEREZFORTES16") -> dict[str, float]:
    out = {}
    for row in records:
        if row["ref_id"] != reference:
            continue
        quantity = row["quantity"]
        if quantity in out:
            raise ValueError(f"Duplicate reference quantity: {quantity}")
        if row["value"]:
            try:
                out[quantity] = float(row["value"])
            except ValueError:
                pass
    return out


def plant_pf(plant_rows: list[dict]) -> dict[str, float]:
    if not plant_rows:
        raise ValueError("Missing plant comparison rows")
    match = [h for h in plant_rows[0].keys() if h.startswith("M7 at Perez-Fortes")]
    col = unique(match, "PF plant column")
    result = {}
    for r in plant_rows:
        try:
            result[r["metric"]] = float(r[col])
        except (ValueError, TypeError):
            continue
    return result


def calculate(
    cost_rows: list[dict],
    refs: dict[str, float],
    pf_summary: dict[str, float],
    pf_like_for_like_summary: float,
    plant: dict[str, float],
    mw: dict[str, float],
    *,
    table_tolerance: float = 0.15,
) -> tuple[dict, list[dict]]:
    cost = benchmark_cost_rows(cost_rows)
    errors: list[str] = []
    def check(name: str, observed: float, expected: float, tol: float = table_tolerance) -> None:
        if not (math.isfinite(observed) and math.isfinite(expected) and
                math.isclose(observed, expected, rel_tol=0.0, abs_tol=tol)):
            errors.append(f"{name}: observed {observed:.8g}, expected {expected:.8g}, tolerance {tol:g}")

    fixed_ref = refs["FCP_eur_t"]
    price_h2 = refs["H2_price"]
    price_co2 = refs["CO2_price"]
    vcp = refs["VCP_eur_t"]
    breakeven = refs["breakeven_MeOH_price_eur_t"]
    prod_no_cap = refs["production_cost_no_capital_eur_t"]
    exact_model_harmonized = (
        pf_summary["h2_eur_t"] + pf_summary["co2_eur_t"] +
        pf_summary["elec_eur_t"] + pf_summary["cat_eur_t"] +
        pf_summary["acc_eur_t"] + fixed_ref
    )
    displayed_model_sum = sum(float(cost[label]["model"]) for label in (
        "H2", "electricity + utilities", "catalyst replacement",
        "capital (annuity at 8 %, 20 y)", "fixed O&M"))
    displayed_ref_sum = sum(float(cost[label]["reference"]) for label in (
        "H2", "electricity + utilities", "catalyst replacement",
        "capital (annuity at 8 %, 20 y)", "fixed O&M"))
    anchor_model = float(cost["TOTAL, anchor convention"]["model"])
    reported_like = float(cost["TOTAL, like-for-like (feed + power + catalyst + capital + reference FCP)"]["model"])
    check("like-for-like summation", exact_model_harmonized, reported_like)
    check("summary matches like-for-like CSV", exact_model_harmonized, pf_like_for_like_summary, tol=0.04)
    check("reference fixed O&M sourced from published number",
          float(cost["fixed O&M"]["reference"]), fixed_ref, tol=0.03)
    check("cost-table H2 vs high-precision model", float(cost["H2"]["model"]),
          pf_summary["h2_eur_t"])
    check("cost-table capital vs high-precision model",
          float(cost["capital (annuity at 8 %, 20 y)"]["model"]), pf_summary["acc_eur_t"])
    check("breakeven reference", float(cost["TOTAL, anchor convention"]["reference"]),
          breakeven)
    check("breakeven reference like-for-like",
          float(cost["TOTAL, like-for-like (feed + power + catalyst + capital + reference FCP)"]["reference"]),
          breakeven)
    check("published total cost = VCP + FCP", vcp + fixed_ref, prod_no_cap, tol=0.04)
    check("published capital annuity derived", breakeven - prod_no_cap,
          float(cost["capital (annuity at 8 %, 20 y)"]["reference"]), tol=0.03)
    # References reconstructed from a rounded raw-materials allocation need
    # not close exactly: the H2 charge is *derived* from 95.9% of the 283 M€
    # variable production cost, not an independently printed H2 cost.
    check("displayed reference components (approximate)",
          displayed_ref_sum, breakeven, tol=1.0)
    # A quoted compressor-only consumption is not like-for-like with the
    # Pérez-Fortes net 'utilities' line (which includes energy recovery).
    model_h2_t = pf_summary["h2_eur_t"] / price_h2
    check("model H2 specific consumption vs table A",
          model_h2_t, plant["H2 consumption (t/t MeOH)"], tol=0.001)
    check("published H2 use vs documented reference", refs["H2_t_per_t"],
          0.199, tol=1e-8)
    check("model carbon efficiency vs table A", pf_summary["carbon_efficiency"],
          plant["Carbon efficiency (MeOH C / fresh CO2)"], tol=0.001)
    check("model CO2 feed vs table A", pf_summary["co2_t_per_t"],
          plant["CO2 consumption (t/t MeOH)"], tol=0.001)

    h2_stoich = 3.0 * mw["H2"] / mw["MeOH"]
    co2_stoich = mw["CO2"] / mw["MeOH"]
    h2_floor_cost = h2_stoich * price_h2
    co2_floor_cost = co2_stoich * price_co2
    commodity_floor = h2_floor_cost + co2_floor_cost
    model_nonfloor = exact_model_harmonized - commodity_floor
    ref_nonfloor = breakeven - commodity_floor
    check("physically allowable stoichiometric floor",
          float(h2_stoich <= model_h2_t), 1.0, tol=0)
    if ref_nonfloor <= 0 or model_nonfloor <= 0:
        errors.append("Non-positive non-stoichiometric cost residual")

    cost_metrics = {
        "source": "PEREZFORTES16, paper's own prices and capacity",
        "model_like_for_like_EUR_t": exact_model_harmonized,
        "reference_breakeven_EUR_t": breakeven,
        "like_for_like_difference_EUR_t": exact_model_harmonized-breakeven,
        "relative_total_difference_pct": 100*(exact_model_harmonized-breakeven)/breakeven,
        "model_displayed_own_OandM_sum_EUR_t": displayed_model_sum,
        "model_actual_fixed_OandM_EUR_t": float(cost["fixed O&M"]["model"]),
        "reference_fixed_OandM_used_EUR_t": fixed_ref,
        "own_OandM_vs_reference_gap_EUR_t": float(cost["fixed O&M"]["model"])-fixed_ref,
        "reference_costs_reconstructed_from_rounded_components_EUR_t": displayed_ref_sum,
        "model_anchor_convention_EUR_t": anchor_model,
        "model_anchor_minus_like_for_like_EUR_t": anchor_model-exact_model_harmonized,
        "H2_stoichiometric_floor_t_per_tMeOH": h2_stoich,
        "CO2_stoichiometric_floor_t_per_tMeOH": co2_stoich,
        "H2_stoichiometric_cost_floor_EUR_t": h2_floor_cost,
        "CO2_stoichiometric_cost_floor_EUR_t": co2_floor_cost,
        "commodity_stoichiometric_cost_floor_EUR_t": commodity_floor,
        "floor_share_model_total_pct": 100*commodity_floor/exact_model_harmonized,
        "floor_share_reference_total_pct": 100*commodity_floor/breakeven,
        "model_excess_H2_EUR_t": pf_summary["h2_eur_t"]-h2_floor_cost,
        "reference_excess_H2_from_derived_cost_EUR_t": float(cost["H2"]["reference"])-h2_floor_cost,
        "model_nonfloor_residual_EUR_t": model_nonfloor,
        "reference_nonfloor_residual_EUR_t": ref_nonfloor,
        "relative_nonfloor_residual_difference_pct": 100*(model_nonfloor-ref_nonfloor)/ref_nonfloor,
    }
    plant_checks = {
        "modeled_carbon_efficiency": plant["Carbon efficiency (MeOH C / fresh CO2)"],
        "reference_carbon_efficiency": refs["carbon_efficiency"],
        "carbon_efficiency_difference_pp":
            100*(plant["Carbon efficiency (MeOH C / fresh CO2)"]-refs["carbon_efficiency"]),
        "model_recycle_to_fresh_mol_ratio": plant["Recycle ratio (recycle / fresh feed, mol)"],
        "reference_recycle_ratio_approx": refs["recycle_ratio"],
        "model_compressor_only_MWh_t": plant["Electricity, compression (MWh/t)"],
        "reference_compressor_only_MWh_t": refs["electricity_compressors_MWh_t"],
        "reference_net_electricity_MWh_t": refs["electricity_net_MWh_t"],
        "compression_ratio_model_to_ref": (
            plant["Electricity, compression (MWh/t)"] /
            refs["electricity_compressors_MWh_t"]),
        "capital_model_EUR_t": float(cost["capital (annuity at 8 %, 20 y)"]["model"]),
        "capital_reference_EUR_t": float(cost["capital (annuity at 8 %, 20 y)"]["reference"]),
        "reference_H2_spend_basis": "derived: 95.9% of reported VCP allocated to raw materials",
        "energy_comparison_caveat": "model compressor electricity and reference utility net are not identical boundaries",
    }
    review = [
        dict(category="minimum_stoichiometric_commodity", item="H2 for three H2 per MeOH",
             model_EUR_t=h2_floor_cost, reference_EUR_t=h2_floor_cost,
             basis="exact stoichiometry times the same study-specific H2 price"),
        dict(category="process_dependent", item="H2 expenditure above stoichiometric floor",
             model_EUR_t=pf_summary["h2_eur_t"]-h2_floor_cost,
             reference_EUR_t=float(cost["H2"]["reference"])-h2_floor_cost,
             basis="includes purge, selectivity and product-recovery effects"),
        dict(category="process_dependent", item="CO2 expenditure above stoichiometric floor",
             model_EUR_t=pf_summary["co2_eur_t"]-co2_floor_cost,
             reference_EUR_t=0.0,
             basis="CO2 price is zero in the Pérez-Fortes base case"),
        dict(category="process_and_equipment", item="electricity and utilities",
             model_EUR_t=float(cost["electricity + utilities"]["model"]),
             reference_EUR_t=float(cost["electricity + utilities"]["reference"]),
             basis="boundary mismatch: model compressor-only; reference net utilities"),
        dict(category="catalyst_inventory", item="catalyst replacement",
             model_EUR_t=float(cost["catalyst replacement"]["model"]),
             reference_EUR_t=float(cost["catalyst replacement"]["reference"]),
             basis="reference catalyst inventory and replacement frequency fixed at this point"),
        dict(category="capital_mixed", item="capital annuity",
             model_EUR_t=float(cost["capital (annuity at 8 %, 20 y)"]["model"]),
             reference_EUR_t=float(cost["capital (annuity at 8 %, 20 y)"]["reference"]),
             basis="mixes process equipment, financing and materials factors"),
        dict(category="accounting", item="fixed O&M on published basis",
             model_EUR_t=fixed_ref, reference_EUR_t=fixed_ref,
             basis="reference fixed O&M substituted on model side to harmonize accounting"),
    ]
    return {
        "status": "INDEPENDENT_QA_NOT_FROZEN",
        "cost_comparison": cost_metrics,
        "process_metric_comparison": plant_checks,
        "warnings": [
            "Stoichiometric-baseline subtraction is a diagnostic ratio, not a validated catalyst-sensitive production-cost model.",
            "A common-mode hydrogen floor does not imply the entire hydrogen charge is catalyst independent.",
            "Reference H2 expenditure comes from an allocated VCP percentage, not a separately measured H2 cost.",
            "Like-for-like substitutes the *reference* FCP into the model; table displays model FCP too.",
            "S5 printed-only cohort economics and 2026-10-06 benchmark sensitivity use different screening protocols.",
            "This check does not re-solve plants, change headline reversals or correct any manuscript.",
        ],
        "errors": errors,
    }, review


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-dir", type=Path, default=BENCH)
    p.add_argument("--model-path", type=Path, default=MODEL_PATH)
    p.add_argument("--out-dir", type=Path, required=True)
    p.add_argument("--strict", action="store_true")
    args = p.parse_args()
    s = args.source_dir
    report, terms = calculate(
        rows(s / "reconciliation_cost.csv"),
        ref_values(rows(s / "reference_values.csv")),
        json.loads((s/"summary.json").read_text(encoding="utf-8"))["perez_fortes_primary"],
        float(json.loads((s/"summary.json").read_text(encoding="utf-8"))[
            "perez_fortes_like_for_like_eur_t"]),
        plant_pf(rows(s/"reconciliation_plant.csv")),
        weight_constants(args.model_path),
    )
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir/"pf_benchmark_audit.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    with (args.out_dir/"pf_cost_boundary_terms.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(terms[0]))
        writer.writeheader()
        writer.writerows(terms)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return int(args.strict and bool(report["errors"]))


if __name__ == "__main__":
    raise SystemExit(main())
