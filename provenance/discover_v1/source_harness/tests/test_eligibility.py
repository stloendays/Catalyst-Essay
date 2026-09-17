import json, sys
from pathlib import Path
import yaml
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "agent"))
from eligibility import test_lever_eligibility as elig, bed_cap_slack

# NH3-FINAL-1.0 LEGACY facts (archived run + archived manifest, both immutable). 1.1 facts are in test_eligibility_1_1.py.
RES = json.loads((ROOT / "outputs/nh3_final_20260903T092000Z/results.json").read_text(encoding="utf-8"))
MAN = yaml.safe_load((ROOT / "configs/nh3_final_1.0_archived.yaml").read_text(encoding="utf-8"))


def test_bed_cap_direction_aware():
    up = elig("engineering.max_catalyst_bed_m3", "increase", RES, MAN)
    assert up["status"] == "inactive_constraint" and up["slack"]["Fe"]["slack_m3"] > 3 and not up["slack"]["Fe"]["cap_active"]
    down = elig("engineering.max_catalyst_bed_m3", "decrease", RES, MAN)
    assert down["status"] == "eligible" and abs(down["activation_threshold_m3"] - 86.64) < 0.01


def test_electricity_is_common_mode():
    r = elig("economics.electricity_USD_MWh", "decrease", RES, MAN)
    assert r["status"] == "common_mode_external" and "absolute_leverage" in r["allowed"]


def test_uncertainty_and_version_out_of_scope():
    assert elig("uncertainty.seed", "increase", RES, MAN)["status"] == "out_of_scope"
    assert elig("project.model_version", "increase", RES, MAN)["status"] == "out_of_scope"
    assert elig("economics.calibration_factor", "increase", RES, MAN)["status"] == "out_of_scope"


def test_operating_window_uses_grid_edge():
    # Ru optimum is at T=450 (upper) and P=300 (upper): extending the upper bound is eligible
    assert elig("process.pressure_bar.stop", "increase", RES, MAN)["status"] == "eligible"
    # no pair metal at the lower pressure bound (10 bar): extending it downward is inactive
    assert elig("process.pressure_bar.start", "decrease", RES, MAN)["status"] == "inactive_constraint"
    assert elig("process.pressure_bar.step", "increase", RES, MAN)["status"] == "out_of_scope"


def test_catalyst_specific_eligible_and_unknown():
    assert elig("economics.metal_recovery_fraction", "increase", RES, MAN)["status"] == "eligible"
    assert elig("economics.catalyst_life_y", "increase", RES, MAN)["lever_family"] == "catalyst_lifecycle_economics"
    assert elig("no.such.key", "increase", RES, MAN)["status"] == "unknown"
    assert elig("economics.catalyst_life_y", "sideways", RES, MAN)["status"] == "unknown"
