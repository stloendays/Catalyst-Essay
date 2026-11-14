"""V3.3.1 engineering-ledger checks (2026-11-14).

1. unitops UO-1.1 against hand calculations (cooling utilities, pressure-driven separation, plant-cost shares).
2. Replay on the archived development build ch4_v33_t3 (CO2 methanation, V3.3): the ledger checks must reject the two
   energy errors found in its audit (cooling duty bought at COP 10; a biogas-upgrading factor measured with feed compression
   applied to a 20 bar loop gas) and its reactor capital (a plant-level cost share rescaled with the recycle flow), and accept
   the same plant once those lines are computed with UO-1.1.
3. Report the diagnostic purchased energy of the repaired reference plant (an audit number, not a build result).
"""
import copy
import importlib.util
import json
import math
import shutil
import sys
import tempfile
from pathlib import Path

A = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(A))
import unitops as u  # noqa: E402
from physics_gate import R, check_physics  # noqa: E402

# ---------------- 1. hand calculations
# cooling water, 1 GJ rejected, 10 K range: 23 900 kg water; pump 23.9 m3 x 3 bar / 0.75 = 9.56 MJ;
# tower fan: 23 900 kg air / 1.18 kg/m3 x 200 Pa / 0.6 = 6.75 MJ; total 16.3 MJ (1.63 %, COP 61)
c = u.cooling_utility(1.0, 313.15)
water = 1e9 / (4184 * 10)
hand = (water / 1000 * 3e5 / .75 + water / 1.18 * 200 / .6) / 1e9
assert c["cooling_medium"] == "cooling_water" and abs(c["electricity_GJ_per_t"] - hand) < 1e-12 and 55 < c["cop"] < 65, c
print(f"cooling water: {c['electricity_GJ_per_t']*100:.2f} % of duty (hand {hand*100:.2f} %), COP {c['cop']:.0f}: PASS")
a = u.cooling_utility(1.0, 320.0, "air")
hand = 1e9 / (1006 * 15) / 1.18 * 200 / .6 / 1e9
assert abs(a["electricity_GJ_per_t"] - hand) < 1e-12
print(f"air cooler: {a['electricity_GJ_per_t']*100:.2f} % of duty: PASS")
r = u.cooling_utility(1.0, 263.15)          # -10 C: Carnot 258.15/50 = 5.16, x 0.5 = 2.58, plus condenser cooling water
assert r["cooling_medium"] == "refrigeration" and 2.3 < r["cop"] < 2.58, r
try:
    u.cooling_utility(1.0, 300.0, "cooling_water")
    raise AssertionError("cooling water below ambient + approach accepted")
except ValueError:
    pass
print(f"refrigeration at -10 C: COP {r['cop']:.2f} (Carnot x 0.5 = 2.58 before condenser pumps); cooling water below 308 K refused: PASS")
s = u.separator_energy(20.0, [dict(kmol_per_t=60.0, P_out_bar=20.0), dict(kmol_per_t=5.0, P_out_bar=1.2)])
assert s["power_GJ_per_t"] == 0 and abs(s["letdown_exergy_GJ_per_t"] - 5e3 * R * 298.15 * math.log(20 / 1.2) / 1e9) < 1e-12
s2 = u.separator_energy(20.0, [dict(kmol_per_t=60.0, P_out_bar=20.0), dict(kmol_per_t=5.0, P_out_bar=1.2, P_required_bar=20.0)])
assert abs(s2["power_GJ_per_t"] - u.compressor(5.0, 313.15, 1.2, 20.0)["power_GJ_per_t"]) < 1e-12
v = u.separator_energy(5.0, [dict(kmol_per_t=2.0, P_out_bar=0.2, P_required_bar=1.01325)])
assert v["power_GJ_per_t"] > 0
print("separator energy: passive letdown 0, recompression = compressor(), vacuum pumping counted: PASS")
cs = u.plant_cost_share(1e8, .28, cost_year=2020, size_basis="kW CH4")
assert abs(cs["capex_usd"] - 2.8e7) < 1e-6 and cs["capex_basis"]["installed"] is True
print("plant cost share: PASS")

# ---------------- 2. replay on ch4_v33_t3
RUN = Path("D:/agent_runs/ch4_v33_t3")
if not RUN.exists():
    print("ch4_v33_t3 not on this machine: replay skipped")
    sys.exit(0)
with tempfile.TemporaryDirectory() as tmp:
    for f in ("model.py", "unitops.py", "physics_gate.py"):
        shutil.copyfile(RUN / f, Path(tmp) / f)      # the build's own frozen library copies
    sys.path.insert(0, tmp)
    for name in ("unitops", "physics_gate"):
        sys.modules.pop(name, None)
    spec = importlib.util.spec_from_file_location("v33_model", Path(tmp) / "model.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    ref = m.reference()
    sys.path.remove(tmp)
    for name in ("unitops", "physics_gate"):
        sys.modules.pop(name, None)
flow = json.loads((RUN / "flowsheet.json").read_text(encoding="utf-8"))
basis = json.loads((RUN / "basis.json").read_text(encoding="utf-8"))
assert abs(ref["balances"]["energy_GJ_per_t"] - 7.150088939635745) < 1e-9
assert check_physics(m, ref, flow, basis) == [], "the archived build passed the V3.3 gate"
fails = check_physics(m, ref, flow, basis, ledger=True)
joined = "\n".join(fails)
assert "effluent cooler cooling" in joined and "without cooling_medium" in joined, joined
assert "SNG polishing separator separation" in joined and "without energy_method" in joined, joined
print(f"replay ch4_v33_t3: V3.3 gate passes, V3.3.1 ledger checks reject it ({len(fails)} failures): PASS")

# the same lines as the build declared them, now with the fields V3.3.1 asks for: still rejected
units = {x["name"]: x for x in ref["physics"]["units"]}
eff = m.PARAMS["basis.utilities.electricity_primary_efficiency"]
declared = copy.deepcopy(ref)
du = {x["name"]: x for x in declared["physics"]["units"]}
du["effluent cooler"]["cooling_medium"] = "cooling_water"
du["SNG polishing separator"].update(energy_method="published_factor", source_feed_P_bar=1.0)   # biogas upgrading feed
du["SNG polishing separator"]["feed"]["P_bar"] = du["SNG polishing separator"]["P_in_bar"]
fails = "\n".join(check_physics(m, declared, flow, basis, ledger=True))
assert "cooling_utility: purchased energy" in fails and "separation_pressure" in fails, fails
print("declared COP 10 cooling and 0.22 kWh/Nm3 factor from an atmospheric source at 20 bar: rejected: PASS")

# repaired with UO-1.1 (diagnostic): cooling from cooling_utility, separator from stream pressures (membrane retentate loses
# 2 bar and is recompressed to the 20 bar product spec; tail gas let down to 1.2 bar without recompression, as the build
# declared; letdown of the tail alone gives less exergy than the separation's minimum work, which the gate enforces), and
# capital as fixed shares of the build's own plant-level cost
plant = m.PARAMS["capital.total_usd_per_kW_CH4"] * (u.stream_lhv({"CH4": 1000 / 16.043}) * 57120 / 8000 / .0036)
roles = {"CO2 feed compressor": "feed_conditioning", "feed mixer": "feed_conditioning", "feed-effluent exchanger": "heat_integration",
         "staged cooled fixed-bed reactor": "reaction", "reaction heat steam generator": "heat_integration",
         "effluent cooler": "separation", "water knockout and dryer": "separation", "recycle splitter": "recycle",
         "recycle compressor": "recycle", "SNG polishing separator": "separation", "tail-gas handling": "offsites",
         "condensate handling": "offsites"}
fixed = copy.deepcopy(ref)
fu = {x["name"]: x for x in fixed["physics"]["units"]}
cool = u.cooling_utility(fu["effluent cooler"]["cooling_duty_GJ_per_t"], 313.15, "cooling_water", primary_efficiency=eff)
fu["effluent cooler"].update(cool)
sep = fu["SNG polishing separator"]
sep["feed"]["P_bar"] = sep["P_in_bar"]
outs = sep["outlets"]
outs[0]["P_bar"], outs[1]["P_bar"] = sep["P_in_bar"] - 2.0, 1.2
se = u.separator_energy(sep["P_in_bar"], [dict(kmol_per_t=outs[0]["kmol_per_t"], P_out_bar=sep["P_in_bar"] - 2.0,
                                               P_required_bar=m.PARAMS["basis.product.CH4.P_bar"]),
                                          dict(kmol_per_t=outs[1]["kmol_per_t"], P_out_bar=1.2)], primary_efficiency=eff)
sep.update(se)
original_reactor = fu["staged cooled fixed-bed reactor"]["capex_usd"]
share = m.PARAMS["capital.share.staged_cooled_fixed_bed_methanation_reactor"]
for name, x in fu.items():
    x["boundary_role"] = roles[name]
    if x["type"] == "compressor":
        x["capex_basis"] = dict(method="power_based", size_basis="shaft kW", cost_year=2024, installed=True)
    else:
        key = m._SHARE_KEYS[name]
        x.update(u.plant_cost_share(plant, m.PARAMS[key], cost_year=2020, size_basis="kW CH4 LHV", source_cost_usd=plant,
                                    source_capacity=57120.0, scale_exponent=0.6))   # the build's implicit source size
fixed["balances"]["energy_GJ_per_t"] = sum(x["purchased_energy_GJ_per_t"] for x in fu.values())
fixed["balances"]["capex_usd"] = sum(x["capex_usd"] for x in fu.values())
bad = copy.deepcopy(fixed)
bad_r = {x["name"]: x for x in bad["physics"]["units"]}["staged cooled fixed-bed reactor"]
bad_r["capex_usd"] = original_reactor
bad["balances"]["capex_usd"] += original_reactor - share * plant
fails = "\n".join(check_physics(m, bad, flow, basis, ledger=True))
assert "capital_double_count" in fails, fails
print(f"reactor capital rescaled with the recycle flow ({original_reactor/1e6:.1f} M vs share {share} x {plant/1e6:.1f} M): rejected: PASS")
nosrc = copy.deepcopy(fixed)
for x in nosrc["physics"]["units"]:
    x.get("capex_basis", {}).pop("source_capacity", None)
assert "capital_scaling" in " | ".join(check_physics(m, nosrc, flow, basis, ledger=True))
print("plant-level cost share without the source plant's capacity: rejected: PASS")
fails = check_physics(m, fixed, flow, basis, ledger=True)
assert fails == [], fails
e_old, e_new = ref["balances"]["energy_GJ_per_t"], fixed["balances"]["energy_GJ_per_t"]
print(f"repaired with UO-1.1: all checks pass; diagnostic purchased energy {e_old:.2f} -> {e_new:.2f} GJ/t primary "
      f"(cooler {units['effluent cooler']['purchased_energy_GJ_per_t']:.2f} -> {cool['purchased_energy_GJ_per_t']:.2f}, "
      f"separator {units['SNG polishing separator']['purchased_energy_GJ_per_t']:.2f} -> {se['purchased_energy_GJ_per_t']:.2f}); "
      f"capital {ref['balances']['capex_usd']/57120:.0f} -> {fixed['balances']['capex_usd']/57120:.0f} USD/(t/y)")
rows = u.energy_ledger(fixed["physics"]["units"])
assert abs(sum(x["purchased_energy_GJ_per_t"] for x in rows) - e_new) < 1e-12
print("V3.3.1: ALL PASS")
