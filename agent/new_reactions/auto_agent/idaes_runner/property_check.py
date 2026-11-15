"""Runs in the IDAES env: compare the harness thermo table (physics_gate) with the independent `chemicals`/`thermo`
database for every species in THERMO. Prints JSON {species: {dH_rel, Hf_diff_kJ}}."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from physics_gate import THERMO, species_thermo  # noqa: E402
from thermo import Chemical  # noqa: E402

NAMES = {"H2": "hydrogen", "CH4": "methane", "C2H6": "ethane", "C2H4": "ethylene", "C3H8": "propane", "C3H6": "propylene",
         "CO": "carbon monoxide", "CO2": "carbon dioxide", "H2O": "water", "NH3": "ammonia", "N2": "nitrogen", "O2": "oxygen",
         "C2H5OH": "ethanol", "CH3OH": "methanol", "Ar": "argon"}
out = {}
for s in THERMO:
    c, T = Chemical(NAMES[s]), 700.0
    ref = c.HeatCapacityGas.T_dependent_property_integral(298.15, T) / 1000
    ours = (species_thermo(s, T)[0] - species_thermo(s, 298.15)[0]) / 1000
    hf = (Chemical(NAMES[s], T=298.15).Hfgm or 0) / 1000
    out[s] = dict(dH_harness=ours, dH_chemicals=ref, dH_rel=(ours - ref) / ref, Hf_diff_kJ=THERMO[s][0] - hf)
print(json.dumps(out))
