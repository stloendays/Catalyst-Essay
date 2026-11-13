"""Amendment A3 (2026-11-13 13:10), before any V3.1 build output was evaluated.

Observed: nh3dec_b1 stopped making progress at turn 137 inside a fixed tool that executes the agent's own atomic.py/model.py
(30 min at full CPU, no output). Change for builds started from now on: fixed tools that execute agent code (check_model,
check_atomic, run_analysis, run_three_optima, run_sensitivity, assess_assumptions, check_records, submit_flowsheet) get a
900 s deadline; on timeout the agent receives an error asking it to make its code faster. nh3dec_b1 was stopped by the
operator (it was at turn 137 of 140 and would have ended at the turn limit) and is replaced; nh3dec_b3 ended at the 140-turn
limit in the report stage and is replaced (nh3dec_b5). nh3dec_b4 and nh3dec_b5 started under A2 and keep running unchanged.
Decisions confirmed by the user on 2026-11-13 ("我觉得可以，你就这样做吧"): the fixed price table as generic infrastructure;
NH3-decomposition mass tolerance +-12 %; CO2 methanation used only as the basis for the V3 changes, validation carried by NH3
decomposition and the two blind tests.
"""
import hashlib
import json
from datetime import datetime
from pathlib import Path

H = Path(__file__).resolve().parent
A = H.parent
files = ["runner.py", "build_mode.py", "physics_gate.py", "basis_gate.py", "atomic_layer.py", "mkm_solver.py", "prices.json",
         "evaluate_builds.py", "audit_holdout.py", "blind_eval.py"]
doc = {"id": "V3.1-A3", "written": datetime.now().isoformat(timespec="seconds"), "amends": "PREREG_V31_A2.json",
       "change": __doc__.strip(), "tool_timeout_s": 900,
       "invalid_so_far": {"nh3dec_b1": "stopped by the operator at turn 137 (hung in a fixed tool)", "nh3dec_b2": "turn limit (140)",
                          "nh3dec_b3": "turn limit (140) in report", "nh3_b1..b3 (first start)": "stopped before A2, not evaluated"},
       "replacements": {"nh3dec_b2": "nh3dec_b4", "nh3dec_b3": "nh3dec_b5", "nh3dec_b1": "nh3dec_b6"},
       "frozen_sha256": {f: hashlib.sha256((A / f).read_bytes()).hexdigest() for f in files}}
(H / "PREREG_V31_A3.json").write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")
print("written PREREG_V31_A3.json")
