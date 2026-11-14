"""Offline checks of unitops.py against textbook / NIST values."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import unitops as u  # noqa: E402

# NIST: N2 H(1000 K) - H(298.15 K) = 21.46 kJ/mol
q = u.sensible_heat({"N2": 1.0}, 298.15, 1000.0)
assert abs(q * 1e3 - 21.46) < 0.1, q
print(f"N2 298->1000 K: {q*1e3:.2f} kJ/mol (NIST 21.46): PASS")
# compression of 1 kmol H2 from 1 to 30 bar: between isothermal minimum and the gate's 2.5x bound
c = u.compressor(1.0, 298.15, 1.0, 30.0)
w = u.isothermal_work(1.0, 298.15, 1.0, 30.0)
assert w < c["power_GJ_per_t"] < 2.5 * w and c["stages"] == 3, (c, w)
print(f"H2 1->30 bar: {c['power_GJ_per_t']/2.016*1e3:.2f} MJ/kg H2, {c['stages']} stages, {c['power_GJ_per_t']/w:.2f}x isothermal: PASS")
assert u.compressor(1.0, 300, 30, 30)["power_GJ_per_t"] == 0
# recycle without purge converts everything; with purge the loss closes the balance
r = u.recycle_loop(0.25, 0.0)
assert abs(r["overall_conversion"] - 1) < 1e-12 and abs(r["recycle_ratio"] - 3) < 1e-12
r = u.recycle_loop(0.25, 0.1)
assert abs(r["overall_conversion"] + r["purge_loss_fraction"] - 1) < 1e-12
print(f"recycle X=0.25 purge 10 %: overall {r['overall_conversion']:.3f}, recycle ratio {r['recycle_ratio']:.2f}: PASS")
# heating values and fired heater with internal fuel first
assert abs(u.stream_lhv({"H2": 1.0, "N2": 5.0}) - 2.016 * 120 / 1e3) < 1e-9
f = u.fired_heater(10.0, internal_fuel_available_GJ_per_t=8.0, efficiency=0.8)
assert abs(f["purchased_energy_GJ_per_t"] - 4.5) < 1e-12 and f["internal_fuel_GJ_per_t"] == 8.0
print("stream LHV and fired heater burning internal fuel first: PASS")
p, t = u.split({"H2": 3.0, "N2": 1.0}, 0.85, ["H2"])
assert abs(p["H2"] - 2.55) < 1e-12 and abs(t["H2"] - 0.45) < 1e-12 and t["N2"] == 1.0
print("ideal split: PASS")
dh = u.reaction_heat({"N2": -1, "H2": -3, "NH3": 2}, 1.0, 298.15) * 1e3
assert abs(dh + 91.88) < 0.5, dh
print(f"reaction heat N2+3H2->2NH3 at 298 K: {dh:.1f} kJ/mol (NIST -91.9): PASS")
assert abs(u.latent_heat("H2O", 1.0) * 1e3 - 40.65) < 1e-9
assert abs(u.scaled_capex(100, 1, 2) - 100 * 2 ** 0.6) < 1e-9
print("unitops: ALL PASS")
