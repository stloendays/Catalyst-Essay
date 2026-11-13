"""Amendment A2 (2026-11-13), written before any model output of the V3.1 builds was evaluated.

Observed: the V3.1 workflow (design basis, physics gate with upper bounds and zero-duty rule, evidence debt, critic, atomic layer,
deterministic sensitivity) needs more tool turns than V2: nh3dec_b2 reached the 140-turn limit in the atomic_model stage
(66 calls in model_checks), with about 10.6 M resent input tokens. Change, for every build from now on (replacement builds of
NH3 decomposition and all blind builds): max_turns 300, and a generic history compaction in runner.py (tool outputs and long
tool arguments older than the last 60 tool calls are cut to a short head; files and trace.jsonl keep the full text). A build
that ends at the turn limit is invalid and is replaced; every replacement is reported. Nothing in the agent's instructions,
tools, gates, price table, holdouts, targets, tolerances or agreement rules changes.
Also recorded: the API-YES credential GPT-personal reached its usage limit at about 12:00 (reset 16:03); calls fell back to
the credential 邪修gpt with the same model name, as the route order in llm_route.py prescribes.
"""
import hashlib
import json
from datetime import datetime
from pathlib import Path

H = Path(__file__).resolve().parent
A = H.parent
files = ["runner.py", "build_mode.py", "physics_gate.py", "basis_gate.py", "atomic_layer.py", "mkm_solver.py", "prices.json",
         "evaluate_builds.py", "audit_holdout.py", "blind_eval.py"]
doc = {"id": "V3.1-A2", "written": datetime.now().isoformat(timespec="seconds"),
       "amends": ["PREREG_AI_BUILD_NH3DEC.json", "PREREG_AI_BUILD_NH3DEC_A1.json", "PREREG_BLIND_NH3.json", "PREREG_BLIND_MEOH.json"],
       "change": __doc__.strip(), "max_turns": 300, "history_compaction_keep_last_tool_calls": 60,
       "invalid_so_far": {"nh3dec_b2": "turn limit (140) in atomic_model",
                          "nh3_b1, nh3_b2, nh3_b3": "stopped by the operator during extraction (started with 140 turns, before A2); not evaluated"},
       "frozen_sha256": {f: hashlib.sha256((A / f).read_bytes()).hexdigest() for f in files}}
(H / "PREREG_V31_A2.json").write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")
print("written PREREG_V31_A2.json")
