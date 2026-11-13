"""Amendment A4 (2026-11-13 18:30), before any NH3-decomposition or blind-test result was evaluated.

Observed: in nh3dec_b6 (turn 261) run_python reached its 900 s limit, but subprocess.run killed only the bash wrapper; the
interpreter it started kept the output pipe open and the call returned only after 42 min, when the operator ended the two
orphaned processes by PID (the tool then returned "[timeout]" as designed). nh3dec_b4 (started under A2, no tool deadline)
spent about 3 h inside one fixed tool after turn 287 and was stopped by the operator at turn 288 of 300; it is invalid and is
replaced by nh3dec_b7. Change for builds started from now on: run_python ends the whole process tree on timeout (runner.run_tree).
Nothing the agent is told, no gate, price, holdout, target, tolerance or agreement rule changes.
Also recorded (advisor, 2026-11-13): PDH and CO2 methanation are development reactions (their results shaped the rules) and
are not validation; validation is NH3 decomposition plus the NH3 and methanol blind tests (docs/TRAIN_TEST_SPLIT.md).
"""
import hashlib
import json
from datetime import datetime
from pathlib import Path

H = Path(__file__).resolve().parent
A = H.parent
files = ["runner.py", "build_mode.py", "physics_gate.py", "basis_gate.py", "atomic_layer.py", "mkm_solver.py", "prices.json",
         "evaluate_builds.py", "audit_holdout.py", "blind_eval.py"]
doc = {"id": "V3.1-A4", "written": datetime.now().isoformat(timespec="seconds"), "amends": "PREREG_V31_A3.json",
       "change": __doc__.strip(),
       "split": {"development": ["pdh", "ch4", "etoh (tool-chain trial)"], "test": ["nh3dec", "nh3 (blind)", "meoh (blind)"]},
       "invalid_so_far": {"nh3dec_b1": "stopped by the operator at turn 137 (hung in a fixed tool)", "nh3dec_b2": "turn limit (140)",
                          "nh3dec_b3": "turn limit (140) in report",
                          "nh3dec_b4": "stopped by the operator at turn 288/300 after about 3 h inside one fixed tool (A2 code)",
                          "nh3_b1..b3 (first start)": "stopped before A2, not evaluated"},
       "replacements": {"nh3dec_b2": "nh3dec_b4 -> nh3dec_b7", "nh3dec_b3": "nh3dec_b5", "nh3dec_b1": "nh3dec_b6"},
       "operator_interventions": {"nh3dec_b6 turn 261": "ended two orphaned interpreter processes (by PID) of a run_python call 42 min past its 900 s limit"},
       "frozen_sha256": {f: hashlib.sha256((A / f).read_bytes()).hexdigest() for f in files}}
(H / "PREREG_V31_A4.json").write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")
print("written PREREG_V31_A4.json")
