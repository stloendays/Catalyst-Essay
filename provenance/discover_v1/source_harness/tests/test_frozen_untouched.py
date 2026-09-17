"""Canary: the canonical NH3 manifest (NH3-FINAL-1.1 since 2026-09-05), the archived NH3-FINAL-1.0 manifest and run, the frozen
drift benchmark v1 files and the harness core must not change. Hashes are pinned in tests/frozen_hashes.json."""
import hashlib, json
from pathlib import Path
import yaml
ROOT = Path(__file__).resolve().parents[1]
PINS = json.loads((ROOT / "tests/frozen_hashes.json").read_text(encoding="utf-8"))


def sha(p): return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


def test_frozen_files_unchanged():
    for rel, h in PINS["files"].items():
        assert sha(rel) == h, f"{rel} changed"


def test_canonical_results_match_manifest_frozen_block():
    cfg = yaml.safe_load((ROOT / "configs/nh3_final.yaml").read_text(encoding="utf-8")); fr = cfg["frozen_regression"]
    r = json.loads((ROOT / PINS["canonical_run"] / "results.json").read_text(encoding="utf-8"))
    det = r["deterministic"]; tol = cfg["gates"]["headline_abs_tolerance"]
    assert det["process_state_count"] == fr["process_state_count"]
    for m in ("Fe", "Ru", "Os"):
        assert abs(det["metals"][m]["feasible"]["total_cost"] - fr[f"{m}_cost_USD_t"]) <= tol
    assert abs(r["monte_carlo"]["Fe_feasibility_probability"] - fr["Fe_feasibility_probability"]) <= cfg["gates"]["feasibility_abs_tolerance"]
    assert abs(r["backward_reachability"]["Ru_activity_break_even_multiplier"] - fr["Ru_activity_break_even_multiplier"]) <= max(tol, 1e-6 * fr["Ru_activity_break_even_multiplier"])
