"""Eligibility facts on the canonical NH3-FINAL-1.1 run (promoted 2026-09-05)."""
import json, sys
from pathlib import Path
import yaml
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "agent"))
from eligibility import test_lever_eligibility as elig

PINS = json.loads((ROOT / "tests/frozen_hashes.json").read_text(encoding="utf-8"))
RES = json.loads((ROOT / PINS["canonical_run"] / "results.json").read_text(encoding="utf-8"))
MAN = yaml.safe_load((ROOT / "configs/nh3_final.yaml").read_text(encoding="utf-8"))


def test_pressure_upper_bound_is_inactive_in_1_1():
    # Ru (425 bar) and Fe (180 bar) are interior on the 10-1000 bar grid: extending the upper bound cannot move them
    r = elig("process.pressure_bar.stop", "increase", RES, MAN)
    assert r["status"] == "inactive_constraint" and all(e is None for e in r["on_edge"].values())


def test_bed_cap_slack_large_in_1_1():
    up = elig("engineering.max_catalyst_bed_m3", "increase", RES, MAN)
    assert up["status"] == "inactive_constraint" and up["slack"]["Fe"]["slack_m3"] > 70
    down = elig("engineering.max_catalyst_bed_m3", "decrease", RES, MAN)
    assert down["status"] == "eligible" and abs(down["activation_threshold_m3"] - 17.06) < 0.01


def test_catalyst_levers_still_eligible():
    assert elig("economics.metal_recovery_fraction", "increase", RES, MAN)["status"] == "eligible"
    assert elig("economics.electricity_USD_MWh", "decrease", RES, MAN)["status"] == "common_mode_external"
