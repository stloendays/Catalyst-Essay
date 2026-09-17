import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "agent"))
from voi import rank, boundary_proximity, priority


def test_kill_test_uncertain_but_irrelevant_ranks_below_decisive():
    """Property A: huge uncertainty, zero economic leverage. Property B: modest uncertainty, decides Top-1. B must win."""
    items = [{"name": "A_huge_sigma_no_leverage", "sigma": 0.6, "scale": 1.0, "L_rel": 0.0, "eligibility": "out_of_scope", "cost": "low"},
             {"name": "B_modest_sigma_decisive", "sigma": 0.03, "scale": 0.3, "L_rel": 0.10, "eligibility": "eligible", "cost": "medium"}]
    r = rank(items, 10.30, 10.20)
    assert r["top"] == "B_modest_sigma_decisive" and r["ranked"][-1]["priority"] == 0.0


def test_boundary_proximity_and_cost():
    assert abs(boundary_proximity(10.0, 10.0) - 1.0) < 1e-12
    assert boundary_proximity(17.59, 10.20) < 0.01            # far from parity: little decision value
    p_low = priority({"name": "x", "sigma": 0.1, "scale": 1.0, "L_rel": 0.1, "cost": "low"}, 10.0, 10.0)
    p_high = priority({"name": "x", "sigma": 0.1, "scale": 1.0, "L_rel": 0.1, "cost": "high"}, 10.0, 10.0)
    assert p_low["priority"] == 10 * p_high["priority"]


def test_common_mode_gets_zero_leverage_prior():
    p = priority({"name": "electricity", "sigma": 0.5, "scale": 1.0, "eligibility": "common_mode_external", "cost": "low"}, 10.0, 10.0)
    assert p["priority"] == 0.0 and p["g_source"] == "eligibility:common_mode_external"
