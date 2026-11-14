"""Phase 0 (2026-11-14): freeze the V3.3 harness files and the ch4_v33_t3 run inputs before the V3.3.1 engineering-ledger
changes, so V3.1/V3.2/V3.3 results stay attributable to the exact code that produced them. Hash record only."""
import hashlib
import json
from datetime import datetime
from pathlib import Path

H = Path(__file__).resolve().parent
A = H.parent
RUN = Path("D:/agent_runs/ch4_v33_t3")
files = ["runner.py", "build_mode.py", "physics_gate.py", "basis_gate.py", "unitops.py", "atomic_layer.py", "mkm_solver.py",
         "prices.json", "evaluate_builds.py", "audit_holdout.py", "../chain.py", "../normalize.py", "../../extraction/llm_route.py"]
run_files = ["model.py", "flowsheet.json", "basis.json", "sources.csv", "build_version.json", "unitops.py", "physics_gate.py"]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
doc = {"id": "V3.3-baseline", "written": datetime.now().isoformat(timespec="seconds"),
       "harness_sha256": {f: sha(A / f) for f in files},
       "run": "ch4_v33_t3", "run_sha256": {f: sha(RUN / f) for f in run_files if (RUN / f).exists()}}
(H / "FREEZE_V33_BASELINE.json").write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")
print("written FREEZE_V33_BASELINE.json")
