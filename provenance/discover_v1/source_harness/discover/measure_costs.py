"""E2: measure the real Layer-A workload of every DISCOVER action once (MKM state evaluations + wall time), then freeze the integer
compute-unit table in DISCOVER_COST_MODEL_V1.json. Unit definition: 1 CU = the wall time of 1,000 MKM state evaluations on this machine
(measured), so evaluation-based actions map exactly and vectorized actions (MC, backward, lever) map by measured wall time."""
import json, math, statistics, sys, time
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
from discover.env import DiscoverEnv

def timed(fn, *a, **k):
    t0 = time.perf_counter(); r = fn(*a, **k); return r, time.perf_counter() - t0

env = DiscoverEnv(count_evals=True); h = env._h
# --- unit: 1,000 MKM state evaluations
c = h.process_states[0]["condition"]; e = env._EN0["Fe"]
_, t = timed(lambda: [c.logtof(e) for _ in range(2000)]); ms_per_1000_evals = 1000 * t / 2; unit_s = ms_per_1000_evals / 1000
print(f"1,000 MKM evaluations = {ms_per_1000_evals:.1f} ms -> 1 CU")
meas = {}
def rec(name, res, evals, wall, size=None): meas[name] = {"evals": evals, "wall_s": wall, "size": size}; print(f"{name:26s} evals {evals:>8} wall {wall:8.3f} s  size {size}")

e0 = env._evals; _, w = timed(env.INSPECT_CANDIDATES); rec("INSPECT_CANDIDATES", None, env._evals - e0, w)
e0 = env._evals; _, w = timed(env.COMPUTE_ACTIVITY, env.candidates); rec("COMPUTE_ACTIVITY(15)", None, env._evals - e0, w, 15)
e0 = env._evals; _, w = timed(env.READ_PROPERTY_UNCERTAINTY, env.candidates); rec("READ_PROPERTY_UNCERTAINTY", None, env._evals - e0, w)
# process library construction cost (state fixed points) measured on a fresh harness init
t0 = time.perf_counter(); _ = DiscoverEnv(); init_s = time.perf_counter() - t0; rec("HARNESS_INIT(full library)", None, 0, init_s, h.NSTATE)
e0 = env._evals; _, w = timed(env.BUILD_PROCESS_WINDOW, {}, "full"); rec("BUILD_PROCESS_WINDOW(full)", None, env._evals - e0, w, h.NSTATE)
e0 = env._evals; _, w = timed(env.OPTIMIZE_PROCESS, "Fe", "full"); rec("OPTIMIZE_PROCESS(1 metal, full)", None, env._evals - e0, w, h.NSTATE)
e0 = env._evals; _, w = timed(env.OPTIMIZE_PROCESS, "Ru", "full"); rec("OPTIMIZE_PROCESS(Ru)", None, env._evals - e0, w, h.NSTATE)
e0 = env._evals; _, w = timed(env.READ_COST_BREAKDOWN, "Fe"); rec("READ_COST_BREAKDOWN", None, env._evals - e0, w)
e0 = env._evals; _, w = timed(env.RUN_MC, ["Fe", "Ru"], 100, "full"); rec("RUN_MC(2 metals x 100)", None, env._evals - e0, w, 200)
e0 = env._evals; _, w = timed(env.TEST_LEVER, "metal_recovery_fraction", 0.9, ["Fe", "Ru"], "full"); rec("TEST_LEVER(2 metals)", None, env._evals - e0, w, 2)
e0 = env._evals; _, w = timed(env.BACKWARD, ["Ru", "Fe"], "activity", "full"); rec("BACKWARD(pair)", None, env._evals - e0, w)
e0 = env._evals; _, w = timed(env.TEST_REACHABILITY, "Ru", "activity", "reference"); rec("TEST_REACHABILITY(reference)", None, env._evals - e0, w)
e0 = env._evals; _, w = timed(env.TEST_REACHABILITY, "Ru", "activity", "window", 200.0); rec("TEST_REACHABILITY(window)", None, env._evals - e0, w)
e0 = env._evals; _, w = timed(env.CHECK_MODEL_VALIDITY, "window_edges"); rec("CHECK_MODEL_VALIDITY(edges)", None, env._evals - e0, w)
e0 = env._evals; _, w = timed(env.CHECK_MODEL_VALIDITY, "dominance", "Co", "Fe", "full"); rec("CHECK_MODEL_VALIDITY(dominance, new metal)", None, env._evals - e0, w)
env.close()

# --- map to CU (integers); eval-based where evals dominate, wall-time based otherwise
cu = lambda wall: max(1, int(math.ceil(wall / unit_s)))
per_state_lib = init_s / h.NSTATE
model = {"version": "DISCOVER_COST_MODEL_V1", "frozen_utc": datetime.now(timezone.utc).isoformat(), "unit_definition": f"1 CU = wall time of 1,000 MKM state evaluations on the measurement machine ({ms_per_1000_evals:.1f} ms); evaluation-based actions charged by evaluation count, vectorized actions by measured wall time; all costs rounded up to integers",
         "measurement": {k: v for k, v in meas.items()} | {"ms_per_1000_evals": ms_per_1000_evals, "process_library_init_s": init_s, "n_states_full": h.NSTATE},
         "actions": {
             "INSPECT_CANDIDATES": {"base_CU": 0, "per_unit_CU": {}, "basis": "bookkeeping"},
             "COMPUTE_ACTIVITY": {"base_CU": 0, "per_unit_CU": {"metals": 1}, "basis": "1 MKM evaluation per metal at the reference condition; charged 1 CU per metal (minimum billable unit)"},
             "READ_PROPERTY_UNCERTAINTY": {"base_CU": 0, "per_unit_CU": {}, "basis": "bookkeeping"},
             "BUILD_PROCESS_WINDOW": {"base_CU": 0, "per_unit_CU": {"states": round(per_state_lib / unit_s, 5)}, "basis": f"self-consistent recycle fixed point per state: {1000*per_state_lib:.3f} ms/state measured over the full library"},
             "OPTIMIZE_PROCESS": {"base_CU": 0, "per_unit_CU": {"states": 2 / 1000}, "basis": "2 MKM evaluations per not-yet-evaluated state (descriptor bracketing as in the frozen closure) -> states*2/1000 CU"},
             "READ_COST_BREAKDOWN": {"base_CU": 0, "per_unit_CU": {}, "basis": "bookkeeping on an already optimized state"},
             "RUN_MC": {"base_CU": 0, "per_unit_CU": {"draws_x_metals": round(meas["RUN_MC(2 metals x 100)"]["wall_s"] / 200 / unit_s, 5)}, "basis": "per (draw x metal): interpolation on the response-surface asset + full-window cost minimization; wall time measured; the response-surface asset (14136 x 1201 evaluations) is a shared precomputed Layer-A asset, not charged"},
             "TEST_LEVER": {"base_CU": 0, "per_unit_CU": {"metals": max(1, cu(meas["TEST_LEVER(2 metals)"]["wall_s"] / 2))}, "basis": "re-optimization of an already evaluated metal under a perturbed economic/engineering parameter; wall time measured"},
             "BACKWARD": {"base_CU": cu(meas["BACKWARD(pair)"]["wall_s"]), "per_unit_CU": {}, "basis": "root search over the activity multiplier, each iteration a full-window re-optimization; wall time measured"},
             "TEST_REACHABILITY": {"base_CU": cu(meas["TEST_REACHABILITY(reference)"]["wall_s"]), "per_unit_CU": {"window": cu(meas["TEST_REACHABILITY(window)"]["wall_s"])}, "basis": "reference scope: 1201 MKM evaluations along the descriptor grid; window scope adds the state-wise maximum on the response-surface asset"},
             "CHECK_MODEL_VALIDITY": {"base_CU": 0, "per_unit_CU": {"evals": round(2 * h.NSTATE / 1000)}, "basis": "bookkeeping, except the exact dominance check on a not-yet-evaluated metal, which costs its state evaluation (2 per state)"}}}
(ROOT / "DISCOVER_COST_MODEL_V1.json").write_text(json.dumps(model, indent=2), encoding="utf-8")
print("\nwrote DISCOVER_COST_MODEL_V1.json"); print(json.dumps({k: v["per_unit_CU"] | {"base": v["base_CU"]} for k, v in model["actions"].items()}, indent=1))
