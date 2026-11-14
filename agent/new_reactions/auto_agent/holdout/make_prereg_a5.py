"""Amendment A5 (2026-11-13 18:45), before any NH3-decomposition or blind-test result was evaluated.

Observed: nh3dec_b6 wrote its own evidence_debt.json with write_file at turn 206 (an empty debt list, never produced by
assess_assumptions); at finish (turn ~290) the finish check raised KeyError on the missing input_fingerprint and the runner
exited. The build is invalid (harness crash) and is replaced by nh3dec_b8. Changes for builds started from now on:
(1) gate outputs (model_check.json, evidence_debt.json, critique.json, sensitivity.json, analysis.json, atomic_check.json,
three_optima.json) are written only by their fixed tools; a change to them through write_file or run_python is undone and
the agent is told to call the tool; (2) a malformed or unreadable gate output at finish is returned to the agent as a
NOT FINISHED error instead of ending the run. Nothing the agent is told about modelling, no gate criterion, price, holdout,
target, tolerance or agreement rule changes.
"""
import hashlib
import json
from datetime import datetime
from pathlib import Path

H = Path(__file__).resolve().parent
A = H.parent
files = ["runner.py", "build_mode.py", "physics_gate.py", "basis_gate.py", "atomic_layer.py", "mkm_solver.py", "prices.json",
         "evaluate_builds.py", "audit_holdout.py", "blind_eval.py"]
doc = {"id": "V3.1-A5", "written": datetime.now().isoformat(timespec="seconds"), "amends": "PREREG_V31_A4.json",
       "change": __doc__.strip(),
       "invalid_so_far": {"nh3dec_b1": "stopped by the operator at turn 137 (hung in a fixed tool)", "nh3dec_b2": "turn limit (140)",
                          "nh3dec_b3": "turn limit (140) in report",
                          "nh3dec_b4": "stopped by the operator at turn 288/300 after about 3 h inside one fixed tool (A2 code)",
                          "nh3dec_b6": "harness crash at finish (KeyError on an agent-written evidence_debt.json)",
                          "nh3_b1..b3 (first start)": "stopped before A2, not evaluated"},
       "replacements": {"nh3dec_b2": "nh3dec_b4 -> nh3dec_b7", "nh3dec_b3": "nh3dec_b5", "nh3dec_b1": "nh3dec_b6 -> nh3dec_b8"},
       "frozen_sha256": {f: hashlib.sha256((A / f).read_bytes()).hexdigest() for f in files}}
(H / "PREREG_V31_A5.json").write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")
print("written PREREG_V31_A5.json")
