"""NH3-FINAL-1.1 pressure-dependent CAPEX: unit checks and the 1.0 bit-identity guarantee."""
import math, json, sys
from pathlib import Path
import numpy as np, yaml, pytest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harness_core import NH3Harness

PC = yaml.safe_load((ROOT / "configs/nh3_final_1.1_candidate.yaml").read_text(encoding="utf-8"))["economics"]["pressure_capex"]


def _harness(cfg_rel, pmax):
    cfg = yaml.safe_load((ROOT / cfg_rel).read_text(encoding="utf-8"))
    cfg["process"]["pressure_bar"]["stop"] = pmax  # small library for speed
    return NH3Harness(cfg, ROOT)


def test_turton_vessel_reference_values():
    K = PC["vessel"]["K"]
    v = float(NH3Harness.turton_cp0(K, 20.0, 0.3, 520.0, 0.6))
    assert abs(v - 10 ** (3.4974 + 0.4485 * math.log10(20) + 0.1074 * math.log10(20) ** 2)) < 1e-6
    assert 1.7e4 < v < 1.9e4  # ~1.83e4 USD (2001 basis) for a 20 m3 vertical vessel
    # power-law extrapolation beyond A_max, and monotonicity inside the range
    assert float(NH3Harness.turton_cp0(K, 1040.0, 0.3, 520.0, 0.6)) == pytest.approx(float(NH3Harness.turton_cp0(K, 520.0, 0.3, 520.0, 0.6)) * 2 ** 0.6)
    vals = [float(NH3Harness.turton_cp0(K, a, 0.3, 520.0, 0.6)) for a in (0.3, 1, 10, 100, 520)]
    assert all(b > a for a, b in zip(vals, vals[1:]))


def test_compressor_unit_splitting():
    K = PC["compressor"]["K"]
    c3000 = float(NH3Harness.turton_cp0(K, 3000.0, 450.0, 3000.0, 0.67))
    assert 5e5 < c3000 < 7e5  # ~5.9e5 USD (2001) for a 3 MW centrifugal machine
    h = _harness("configs/nh3_final_1.1_candidate.yaml", pmax=40)
    assert h.PCAPEX_ENABLED
    elec_3MW = 3000.0 * 24.0 / h.PLANT_TPD / 1000.0 * h.ELECTRICITY  # USD/t that corresponds to 3000 kW at design capacity
    assert h.compressor_capex_USD_t(2 * elec_3MW) == pytest.approx(2 * h.compressor_capex_USD_t(elec_3MW))
    assert h.compressor_capex_USD_t(0.0) == 0.0


def test_pressure_factor_behaviour():
    h = _harness("configs/nh3_final_1.1_candidate.yaml", pmax=300)
    V = np.full(h.NSTATE, 0.05)  # tiny vessel -> costed at the 0.3 m3 floor
    prem = h.vessel_pressure_premium(V)
    assert np.all(prem >= 0.0)
    pmin = h.state_P.min()  # the lowest pressure that yields a valid process state
    assert prem[h.state_P == pmin].max() <= prem[h.state_P == 300.0].min()  # grows with pressure
    big = h.vessel_pressure_premium(np.full(h.NSTATE, 86.6))
    assert np.all(big >= prem)  # and with vessel size
    p150 = big[h.state_P == 150.0][0]
    assert 2.0 < p150 < 8.0  # pre-registered order of magnitude: 86.6 m3 at 150 bar ~ 4 USD/t


def test_canonical_1_0_is_bit_identical():
    """With no pressure_capex block (archived NH3-FINAL-1.0 manifest) the deterministic block must equal the 1.0 run to all digits."""
    cfg = yaml.safe_load((ROOT / "configs/nh3_final_1.0_archived.yaml").read_text(encoding="utf-8"))
    h = NH3Harness(cfg, ROOT); assert not h.PCAPEX_ENABLED
    d = h.deterministic()
    # Bit-identity reference: the last PRE-PATCH canonical run on this Windows machine (same numpy/MSVC build).
    # The Linux-built frozen run 20260903T092000Z differs from any Windows run by ~1e-14 in libm rounding, so it is
    # compared at the manifest gate tolerance (1e-8) instead.
    win = json.loads((ROOT / "outputs/nh3_final_20260904T072819Z/results.json").read_text(encoding="utf-8"))["deterministic"]
    lin = json.loads((ROOT / "outputs/nh3_final_20260903T092000Z/results.json").read_text(encoding="utf-8"))["deterministic"]
    for m in d["metals"]:
        assert d["metals"][m]["unconstrained"]["total_cost"] == win["metals"][m]["unconstrained"]["total_cost"]
        assert abs(d["metals"][m]["unconstrained"]["total_cost"] - lin["metals"][m]["unconstrained"]["total_cost"]) <= 1e-8 * max(1.0, lin["metals"][m]["unconstrained"]["total_cost"])
        if win["metals"][m]["feasible"]:
            assert d["metals"][m]["feasible"]["total_cost"] == win["metals"][m]["feasible"]["total_cost"]
            assert d["metals"][m]["feasible"]["breakdown"]["vessel_pressure_premium"] == 0.0
            assert d["metals"][m]["feasible"]["breakdown"]["compressor_capex"] == 0.0
    assert d["raw_global_spearman"] == win["raw_global_spearman"]
    assert d["rolling"][0]["rho_raw"] == win["rolling"][0]["rho_raw"]
