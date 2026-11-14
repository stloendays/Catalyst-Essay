"""Amendment A11 (2026-11-15), build mode V3.4-lean-chem: fewer agent turns, no modelling, gate, price, holdout, target or
tolerance change. Motivated by the turn audit of the development build ch4_v33_t3 (211 turns: read_file 114, of which 77
rereads of unchanged files; resolve_debt 28 and respond_critique 18 in single calls; set_stage 39; three NameErrors from
text patches costing 10 turns; 11 of 18 critique issues about wording or format). Changes: read cache, workspace_digest,
batched debt/critique tools, model skeleton generated from the flowsheet, stage-scoped tool menus, grouped check_model
diagnosis with fix hints, opt-in extraction cache (--reuse-extraction), soft stage turn budgets, model.py import check
after every change, engineering-only critic, set_stage only on change. Details: docs/V34_LEAN_CHEM.md.
"""
import hashlib
import json
from datetime import datetime
from pathlib import Path

H = Path(__file__).resolve().parent
A = H.parent
files = ["runner.py", "build_mode.py", "physics_gate.py", "basis_gate.py", "unitops.py", "atomic_layer.py", "mkm_solver.py",
         "prices.json", "evaluate_builds.py", "audit_holdout.py", "blind_eval.py", "../chain.py", "../normalize.py",
         "../../extraction/llm_route.py", "tests_v3/validate_v331.py", "tests_v3/validate_v34.py", "lean_chem.py"]
doc = {"id": "V3.1-A11", "written": datetime.now().isoformat(timespec="seconds"), "amends": "PREREG_V31_A10.json",
       "build_mode_version": "V3.4-lean-chem", "unit_library": "UO-1.1", "change": __doc__.strip(),
       "frozen_sha256": {f: hashlib.sha256((A / f).read_bytes()).hexdigest() for f in files}}
(H / "PREREG_V31_A11.json").write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")
print("written PREREG_V31_A11.json")
