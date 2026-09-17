"""Write DISCOVER_FROZEN_V1.json: sha256 of every protocol artefact. After this file exists, none of the listed files may change without a V2."""
import hashlib, json, sys
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
FILES = ["DISCOVER_TASK_V1.json", "DISCOVER_TASK_V1_ANON.json", "DISCOVER_ACTION_SCHEMA_V1.json", "DISCOVER_COST_MODEL_V1.json", "DISCOVER_PROMPT_V1.md", "DISCOVER_SCORER_V1.py",
         "DISCOVER_PREREGISTRATION_V1.md", "discover/env.py", "discover/policies.py", "discover/run.py", "discover/llm_policy.py", "discover/prior_probe.py", "discover/IDENTITY_MAPPING_SCORER_ONLY.json",
         "discover/PROTOCOL_FORBIDDEN_ACTIONS.json", "tests/test_discover_oracle.py"]
pins = json.loads((ROOT / "tests/frozen_hashes.json").read_text(encoding="utf-8"))
out = {"version": "DISCOVER_FROZEN_V1", "frozen_utc": datetime.now(timezone.utc).isoformat(), "ground_truth_source": {"canonical_run": pins["canonical_run"], "results_sha256": pins["files"][pins["canonical_run"] + "/results.json"], "model_version": pins["canonical_model_version"]},
       "policy_D_constants": {"THETA": 0.05, "MC_DECAY_DRAWS": 50, "LAMBDA_price": 0.5, "boundary_scale": 0.15, "note": "frozen; no further tuning"},
       "anonymous_mapping_seed": 20260906, "budget_grid_CU": [200, 250, 300, 500, 800, 1200, 2000], "random_baseline_trajectories_per_budget": 20,
       "sha256": {f: hashlib.sha256((ROOT / f).read_bytes()).hexdigest() for f in FILES},
       "rule": "any change to a listed file = DISCOVER V2; formal policy-E runs must verify these hashes first; failures are recorded, never tuned away"}
(ROOT / "DISCOVER_FROZEN_V1.json").write_text(json.dumps(out, indent=2), encoding="utf-8"); print("wrote DISCOVER_FROZEN_V1.json with", len(FILES), "hashes")
