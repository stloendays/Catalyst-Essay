"""Amendment A9 (2026-11-14), harness structure for runs started from now on; first exercised on CO2 methanation, a
development reaction (docs/TRAIN_TEST_SPLIT.md), so no test-set result is involved.

Changes (generic; no modelling instruction, gate, price, holdout, target or tolerance changes):
(1) context: observation masking with batched eviction - only the last 10 tool outputs stay in full, older outputs and long
tool arguments are masked in batches of 20 calls, so the resent prefix stays identical between batches and the provider's
prompt cache can be reused (references: SWE-agent history processors; Lindenbauer et al. 2025, arXiv 2508.21433;
OpenHands condensers). A2 kept 60 calls, A8 30, both re-cut the prefix every turn.
(2) routing: LLM_ROUTES restricts calls to the listed API-YES credentials (user: test on the personal account quota only);
LLM_WAIT_ON_LIMIT=1 waits for a usage-limit reset (at most 6 h) instead of failing the run.
"""
import hashlib
import json
from datetime import datetime
from pathlib import Path

H = Path(__file__).resolve().parent
A = H.parent
files = ["runner.py", "build_mode.py", "physics_gate.py", "basis_gate.py", "atomic_layer.py", "mkm_solver.py", "prices.json",
         "evaluate_builds.py", "audit_holdout.py", "blind_eval.py", "../chain.py", "../normalize.py", "../../extraction/llm_route.py"]
doc = {"id": "V3.1-A9", "written": datetime.now().isoformat(timespec="seconds"), "amends": "PREREG_V31_A8.json",
       "change": __doc__.strip(), "history_keep_full_tool_outputs": 10, "mask_batch": 20,
       "frozen_sha256": {f: hashlib.sha256((A / f).read_bytes()).hexdigest() for f in files}}
(H / "PREREG_V31_A9.json").write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")
print("written PREREG_V31_A9.json")
