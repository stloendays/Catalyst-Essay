"""Amendment A12 (2026-11-15), held-out guard and route policy, no modelling, gate, price, holdout, target or tolerance
change. ch4_v34_t4/t5 reached the held-out STORE&GO report: the guard matched only raw strings in web-search actions, so
'STORE&GO' passed and a held-out DOI the agent wrote into sources.csv was found only by the audit after the run. Now the
guard normalises spelling ('&' -> 'and', punctuation dropped), applies the holdout keyword sets, and checks web-search
actions, agent messages and every tool-call argument; a hit stops the build as invalid. ch4_v34_t6 died when the personal
quota ran out and the advisor key had no credits: a failing fallback now waits for the first route (its reset time, and
not before return_after_s) instead of failing. Route policy file D:/agent_runs/_route_policy.json (advisor cap 40 USD).
"""
import hashlib
import json
from datetime import datetime
from pathlib import Path

H = Path(__file__).resolve().parent
A = H.parent
files = ["runner.py", "build_mode.py", "physics_gate.py", "basis_gate.py", "unitops.py", "atomic_layer.py", "mkm_solver.py",
         "prices.json", "evaluate_builds.py", "audit_holdout.py", "blind_eval.py", "../chain.py", "../normalize.py",
         "../../extraction/llm_route.py", "tests_v3/validate_v331.py", "tests_v3/validate_v34.py", "lean_chem.py", "tests_v3/validate_holdout_guard.py", "tests_v3/validate_route_policy.py"]
doc = {"id": "V3.1-A12", "written": datetime.now().isoformat(timespec="seconds"), "amends": "PREREG_V31_A11.json",
       "build_mode_version": "V3.4-lean-chem", "unit_library": "UO-1.1", "change": __doc__.strip(),
       "frozen_sha256": {f: hashlib.sha256((A / f).read_bytes()).hexdigest() for f in files}}
(H / "PREREG_V31_A12.json").write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")
print("written PREREG_V31_A12.json")
