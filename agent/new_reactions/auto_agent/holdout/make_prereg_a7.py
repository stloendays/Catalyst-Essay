"""Amendment A7 (2026-11-14), written AFTER the NH3-decomposition evaluation of nh3dec_b7, b9, b10. It changes no reported
verdict; it fixes two defects of the fixed record-normalisation code (chain.normalise, shared with PR #122) for runs started
from now on.

Found while diagnosing an empty common record set: (1) a space velocity written 'cm3 gcat-1 h-1' matched no volume test and
was read as a mass WHSV, so the derived rate was about 1000 times too high (51 records of nh3dec_b7, paper
10.1002/cctc.202200688, up to 3444 kg/kg/h); the > 50 kg/kg/h unit gate covered printed rates only. (2) A rate derived from
space velocity x conversion x selectivity used moles of key reactant times the product molar mass, without the product/key
stoichiometric ratio (1.5 for 2 NH3 -> N2 + 3 H2, 2 for N2 + 3 H2 -> 2 NH3 with N2 as key; 1 for PDH, CO2 methanation,
CO2-to-methanol and ethanol dehydration, which are therefore unchanged). Changes: normalize.sv_unit maps cm3/cm^3/cc/sccm to
ml and dm3/nl to l; derived rates get the same 50 kg/kg/h unit gate; the ratio comes from the reaction equation given to the
run (build_mode.parse_equation). Effect on the reported NH3-decomposition and NH3 blind builds: their own derived lab rates
are low by the stoichiometric ratio (and nh3dec_b7 has the 51 inflated records); the blind-test scoring uses the paper's
frozen record set and is unaffected; the TEA quantities come from each build's reference plant.
"""
import hashlib
import json
from datetime import datetime
from pathlib import Path

H = Path(__file__).resolve().parent
A = H.parent
files = ["runner.py", "build_mode.py", "physics_gate.py", "basis_gate.py", "atomic_layer.py", "mkm_solver.py", "prices.json",
         "evaluate_builds.py", "audit_holdout.py", "blind_eval.py", "../chain.py", "../normalize.py"]
doc = {"id": "V3.1-A7", "written": datetime.now().isoformat(timespec="seconds"), "amends": "PREREG_V31_A6.json",
       "written_after_results": True, "change": __doc__.strip(),
       "frozen_sha256": {f: hashlib.sha256((A / f).read_bytes()).hexdigest() for f in files}}
(H / "PREREG_V31_A7.json").write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")
print("written PREREG_V31_A7.json")
