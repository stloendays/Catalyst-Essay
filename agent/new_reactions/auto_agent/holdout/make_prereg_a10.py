"""Amendment A10 (2026-11-14), build mode V3.3.1-engineering-ledger and unit library UO-1.1, for builds started from now on.
Found in the engineering audit of the development build ch4_v33_t3 (CO2 methanation; docs/TRAIN_TEST_SPLIT.md section 6;
evaluation/ch4_v33_test/V331_ENGINEERING_AUDIT.md). Generic, written per unit type; no holdout, target, tolerance or price
change. (1) unitops: cooling_utility (pump/fan or refrigeration electricity from first principles), separator_energy
(compression only for outlets that must be raised in pressure; letdown exergy drives the separation), plant_cost_share,
energy_ledger, capex_ledger. (2) physics gate ledger checks for V3.3.1 builds: boundary_role, cooling_medium and cooling
electricity limits, separation energy_method and source feed pressure, capex_basis (cost year, installed, no second
installation factor, plant-level shares within share and summing to <= 1, source plant cost/capacity/exponent). (3) all
versions: separation outlets given with pressures count their letdown exergy against the mixing minimum. (4) check_model
writes energy_ledger.csv and capex_ledger.csv; evaluate_builds records both ledgers (no score change).
"""
import hashlib
import json
from datetime import datetime
from pathlib import Path

H = Path(__file__).resolve().parent
A = H.parent
files = ["runner.py", "build_mode.py", "physics_gate.py", "basis_gate.py", "unitops.py", "atomic_layer.py", "mkm_solver.py",
         "prices.json", "evaluate_builds.py", "audit_holdout.py", "blind_eval.py", "../chain.py", "../normalize.py",
         "../../extraction/llm_route.py", "tests_v3/validate_v331.py"]
doc = {"id": "V3.1-A10", "written": datetime.now().isoformat(timespec="seconds"), "amends": "PREREG_V31_A9.json",
       "build_mode_version": "V3.3.1-engineering-ledger", "unit_library": "UO-1.1", "change": __doc__.strip(),
       "frozen_sha256": {f: hashlib.sha256((A / f).read_bytes()).hexdigest() for f in files}}
(H / "PREREG_V31_A10.json").write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")
print("written PREREG_V31_A10.json")
