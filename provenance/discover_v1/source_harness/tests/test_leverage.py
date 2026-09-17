import glob, json, math, sys
from pathlib import Path
import yaml
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "agent"))
from leverage import elasticity, pairwise_leverage, ratio_closure, abs_gap_closure, score_sweep, lever_info, log_variable

# NH3-FINAL-1.0 LEGACY regression of the scoring functions against the archived 1.0 run and its sens_* sweeps (immutable outputs).
BASE = json.loads((ROOT / "outputs/nh3_final_20260903T092000Z/results.json").read_text(encoding="utf-8"))
COST0 = {m: BASE["deterministic"]["metals"][m]["feasible"]["total_cost"] for m in ("Fe", "Ru", "Os")}


def test_common_multiplicative_factor_is_non_discriminatory():
    for k in (0.3, 0.5, 2.0, 7.0):
        assert abs(pairwise_leverage(COST0["Ru"] * k, COST0["Fe"] * k, COST0["Ru"], COST0["Fe"], 2.0, 1.0)) < 1e-12
        assert abs(ratio_closure(COST0["Ru"] * k, COST0["Fe"] * k, COST0["Ru"], COST0["Fe"])) < 1e-12
        # legacy metric is NOT invariant: it reports (1-k) "closure" for a pure rescaling
        assert abs(abs_gap_closure(COST0["Ru"] * k, COST0["Fe"] * k, COST0["Ru"], COST0["Fe"]) - (1 - k)) < 1e-12


def test_parity_gives_closure_one():
    assert abs(ratio_closure(10.0, 10.0, COST0["Ru"], COST0["Fe"]) - 1.0) < 1e-12


def test_elasticity_sign_and_value():
    assert abs(elasticity(2.0, 1.0, 2.0, 1.0) - 1.0) < 1e-12
    assert abs(elasticity(0.5, 1.0, 2.0, 1.0) + 1.0) < 1e-12
    assert elasticity(1.0, 1.0, 1.0, 1.0) is None  # no displacement


def _sweep_rows(pattern, key):
    rows = []
    for d in sorted(glob.glob(str(ROOT / "outputs" / pattern))):
        r = json.loads((Path(d) / "results.json").read_text(encoding="utf-8"))
        man = yaml.safe_load((Path(d) / "manifest_resolved.yaml").read_text(encoding="utf-8"))
        v = man
        for part in key.split("."): v = v[part]
        rows.append({"value": v, "costs_USD_t": {m: r["deterministic"]["metals"][m]["feasible"]["total_cost"] for m in ("Fe", "Ru", "Os")}})
    return rows


def test_reproduces_audit_table_from_existing_sweeps():
    """Numbers from NEXT_STAGE_AUDIT_2026-09-04.md Q5 (recomputed 2026-09-04)."""
    rec = score_sweep("economics.metal_recovery_fraction", 0.0, COST0, _sweep_rows("sens_metal_recovery_*", "economics.metal_recovery_fraction"))
    by = {round(r["value"], 2): r for r in rec["rows"]}
    assert abs(by[0.9]["ratio_closure"] - 0.42) < 0.01 and abs(by[0.99]["ratio_closure"] - 0.70) < 0.01
    assert 0.08 < by[0.9]["L_rel"] < 0.11 and by[0.9]["L_rel"] > 0  # loss fraction up -> Ru disadvantage widens
    assert rec["summary"]["discriminatory"] is True and rec["lever_class"] == "catalyst_specific"
    el = score_sweep("economics.electricity_USD_MWh", 50.0, COST0, _sweep_rows("sens_electricity_*", "economics.electricity_USD_MWh"))
    for r in el["rows"]:
        assert abs(r["L_rel"]) < 0.08                       # near-zero discriminatory
        assert r["L_abs"]["Fe"] > 0.85 and r["L_abs"]["Ru"] > 0.85   # large absolute
    assert el["summary"]["discriminatory"] is False and el["lever_class"] == "common_mode_external"
    r20 = next(r for r in el["rows"] if abs(r["value"] - 20) < 1e-9)
    assert r20["abs_gap_closure"] > 0.5 and r20["ratio_closure"] < 0   # the v0.4 failure mode, reproduced and corrected
    bed = score_sweep("engineering.max_catalyst_bed_m3", 90.0, COST0, _sweep_rows("sens_bedvol_*", "engineering.max_catalyst_bed_m3"))
    for r in bed["rows"]: assert abs(r["L_rel"]) < 1e-9 and abs(r["ratio_closure"]) < 1e-9


def test_recovery_and_lifetime_are_same_family_but_scored_separately():
    rec = score_sweep("economics.metal_recovery_fraction", 0.0, COST0, _sweep_rows("sens_metal_recovery_*", "economics.metal_recovery_fraction"))
    life = score_sweep("economics.catalyst_life_y", 10.0, COST0, _sweep_rows("sens_lifetime_*", "economics.catalyst_life_y"))
    assert rec["lever_family"] == life["lever_family"] == "catalyst_lifecycle_economics"
    assert rec["key"] != life["key"] and "family_L_rel" not in rec["summary"]
    # metal_cost ∝ (1-rec)/life: same |L_rel| magnitude, opposite sign in their own log-variables
    r05 = next(r for r in rec["rows"] if abs(r["value"] - 0.5) < 1e-9); l20 = next(r for r in life["rows"] if abs(r["value"] - 20) < 1e-9)
    assert r05["L_rel"] > 0 and l20["L_rel"] < 0 and abs(abs(r05["L_rel"]) - abs(l20["L_rel"])) < 1e-6


def test_log_variable_mapping():
    assert abs(log_variable("economics.metal_recovery_fraction", 0.9) - 0.1) < 1e-12 and lever_info("economics.metal_recovery_fraction")["xt"] == "metal_loss_fraction"
    assert lever_info("uncertainty.seed")["cls"] == "out_of_scope" and lever_info("process.pressure_bar.stop")["cls"] == "operating_window"
    assert lever_info("nonexistent.key")["cls"] == "unknown"


def test_sign_audit_closing_direction_and_reach():
    """Sign audit 2026-09-04: L_rel is w.r.t. x~; for recovery x~ = loss fraction (not monotone with the manifest value)."""
    rec = score_sweep("economics.metal_recovery_fraction", 0.0, COST0, _sweep_rows("sens_metal_recovery_*", "economics.metal_recovery_fraction"))
    assert rec["x_tilde_monotone_with_manifest"] is False
    assert rec["summary"]["L_rel_mean"] > 0 and rec["summary"]["closing_direction"] == "increase economics.metal_recovery_fraction"
    life = score_sweep("economics.catalyst_life_y", 10.0, COST0, _sweep_rows("sens_lifetime_*", "economics.catalyst_life_y"))
    assert life["summary"]["L_rel_mean"] < 0 and life["summary"]["closing_direction"] == "increase economics.catalyst_life_y"
    # reach = closure at the plausible bound; sweep value and log-linear estimate must agree to a few points
    assert rec["summary"]["reach_bound"] == 0.95 and abs(rec["summary"]["reach_estimate"] - 0.515) < 0.02
    assert life["summary"]["reach_bound"] == 20.0 and abs(life["summary"]["reach_from_sweep"] - 0.116) < 0.01
    # reach is a separate quantity from |L_rel|: pressure bound has the larger slope but the smaller reach
    press = score_sweep("process.pressure_bar.stop", 300.0, COST0, _sweep_rows("sens_pressure_stop_*", "process.pressure_bar.stop"))
    assert abs(press["summary"]["L_rel_mean"]) > abs(rec["summary"]["L_rel_mean"]) and press["summary"]["reach"] < life["summary"]["reach"] < rec["summary"]["reach"]
    assert press["summary"]["reach_bound"] == 350.0
    el = score_sweep("economics.electricity_USD_MWh", 50.0, COST0, _sweep_rows("sens_electricity_*", "economics.electricity_USD_MWh"))
    assert el["summary"]["discriminatory"] is False and (el["summary"]["reach"] or 0) < 0.05
