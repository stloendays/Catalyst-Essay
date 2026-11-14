"""Amendment A8 (2026-11-14), cost control for runs started from now on (user: "怎么这么贵？下次设个上限").

Observed: all runs so far used 237.8 M tokens, 1,343 USD at the gpt-5.5 list price; 83 % of it is agent input (the history
is resent every turn), and 51 % (683 USD) went to runs that ended invalid (turn limits, hung tools, harness crash, holdout
leaks). Changes: a hard per-build spend cap (default 60 USD, list-price equivalent, --max-usd); at 85 % of the cap the agent is
told to write its report and finish; a build that reaches the cap stops with status "budget limit" (invalid, replaced and
reported, like a turn limit). History compaction keeps the last 30 tool calls in full (was 60). Cached input tokens are now
recorded (agent_cached_in) where the gateway reports them. Modelling instructions, gates, prices, holdouts, targets and
tolerances are unchanged.
"""
import hashlib
import json
from datetime import datetime
from pathlib import Path

H = Path(__file__).resolve().parent
A = H.parent
files = ["runner.py", "build_mode.py", "physics_gate.py", "basis_gate.py", "atomic_layer.py", "mkm_solver.py", "prices.json",
         "evaluate_builds.py", "audit_holdout.py", "blind_eval.py", "../chain.py", "../normalize.py"]
doc = {"id": "V3.1-A8", "written": datetime.now().isoformat(timespec="seconds"), "amends": "PREREG_V31_A7.json",
       "change": __doc__.strip(), "max_usd_per_build": 60.0, "history_keep_last_tool_calls": 30,
       "frozen_sha256": {f: hashlib.sha256((A / f).read_bytes()).hexdigest() for f in files}}
(H / "PREREG_V31_A8.json").write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")
print("written PREREG_V31_A8.json")
