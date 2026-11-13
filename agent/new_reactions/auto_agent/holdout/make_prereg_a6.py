"""Amendment A6 (2026-11-13 19:10), before any NH3-decomposition TEA or atomic result was evaluated.

Observed (holdout audit, run with the frozen audit_holdout.py and unchanged leak rule): every NH3-decomposition build b1-b6
has hits. Two held-out works (10.1007/s11244-016-0653-4, 10.1038/ncomms9619, added to the blocking list in V3.1) appeared
with title and abstract in the literature-search results; their download was blocked, but the abstracts reached the agent.
In addition nh3dec_b5 opened the held-out TEA paper (10.1002/ese3.70618) through web search at turn 62, and nh3dec_b4
opened the held-out cracking-plant study. Under the preregistered rule all six are invalid (b5 was the only one that had
finished). The blind builds nh3_b1..b3 and meoh_b1..b3 have no hits.
Changes for builds started from now on: (1) the literature search drops held-out works from its results (they never reach
the agent or candidates.csv); (2) a build whose web search opens or queries a held-out DOI or URL fragment is stopped at
once and recorded as invalid (holdout leak), instead of spending its remaining turns; it is replaced. The audit, the
leak rule, targets, tolerances and the agent's instructions are unchanged. Replacements: nh3dec_b7, b8, b9.
"""
import hashlib
import json
from datetime import datetime
from pathlib import Path

H = Path(__file__).resolve().parent
A = H.parent
files = ["runner.py", "build_mode.py", "physics_gate.py", "basis_gate.py", "atomic_layer.py", "mkm_solver.py", "prices.json",
         "evaluate_builds.py", "audit_holdout.py", "blind_eval.py"]
doc = {"id": "V3.1-A6", "written": datetime.now().isoformat(timespec="seconds"), "amends": "PREREG_V31_A5.json",
       "change": __doc__.strip(),
       "invalid_so_far": {"nh3dec_b1": "hung in a fixed tool; holdout abstracts in search results",
                          "nh3dec_b2": "turn limit (140); holdout abstracts in search results",
                          "nh3dec_b3": "turn limit (140); holdout abstracts in search results",
                          "nh3dec_b4": "stopped after about 3 h in one tool; opened the held-out cracking-plant study",
                          "nh3dec_b5": "holdout leak: opened the held-out TEA paper (turn 62); holdout abstracts in search results",
                          "nh3dec_b6": "harness crash at finish; holdout abstracts in search results",
                          "nh3_b1..b3 (first start)": "stopped before A2, not evaluated"},
       "valid_blind_builds_audited_clean": ["nh3_b1", "nh3_b2", "nh3_b3", "meoh_b1", "meoh_b2", "meoh_b3"],
       "replacements": ["nh3dec_b7", "nh3dec_b8", "nh3dec_b9"],
       "frozen_sha256": {f: hashlib.sha256((A / f).read_bytes()).hexdigest() for f in files}}
(H / "PREREG_V31_A6.json").write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")
print("written PREREG_V31_A6.json")
