"""Figure 6 trajectory tables, read from committed DISCOVER-BOUNDARY-C1 traces.

  fig6_trajectories.csv   the action sequence, CU cost and window size of three chains that reach
                          the complete decision: the protocol-complete oracle (22 CU,
                          analysis/supervisor_2026_09_20/agent_oracle_min_cu.json), one strong-tier
                          run at the 150-CU allowance, and fixed policy D at the 225-CU allowance.

Each chain is checked against the ledger summaries (data/discover_boundary_c1_runs.csv and
data/discover_boundary_c1_D_reference.csv) before anything is written.
"""
import csv
import hashlib
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
AGENT = ("data/discover_boundary_c1/runs/gpt-5.5-2026-04-23/traces/anonymous/"
         "E_llm_agent_anonymous_B150_r1_c1_20260909T124030Z")
DREF = "data/discover_boundary_c1/D_reference/traces/anonymous/D_fixed_voi_anon_B225_s0_c1_20260908T102449Z"
ORACLE = "analysis/supervisor_2026_09_20/agent_oracle_min_cu.json"


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def chain(trace_dir, label):
    tdir = os.path.join(REPO, trace_dir)
    t = json.load(open(os.path.join(tdir, "trace.json"), encoding="utf-8"))
    idmap = json.load(open(os.path.join(tdir, "identity_mapping.json"), encoding="utf-8"))["public_to_real"]
    rows, cum = [], 0.0
    for st in t["steps"]:
        cost = float(st.get("action_cost") or 0.0)
        res = st.get("result") if isinstance(st.get("result"), dict) else {}
        cum += cost
        win = st.get("current_winner")
        rows.append({"chain": label, "step": st["step"], "action": st["chosen_action"], "cost_CU": cost,
                     "cum_CU": cum, "window_states": res.get("n_states", ""),
                     "winner": idmap.get(win, "") if win else ""})
    return rows, t, sha(os.path.join(tdir, "trace.json"))


runs = {r["trace_dir"].replace("\\", "/").split("/")[-1]: r
        for r in csv.DictReader(open(os.path.join(REPO, "data/discover_boundary_c1_runs.csv"), encoding="utf-8"))}
dref = {r["trace_dir"].replace("\\", "/").split("/")[-1]: r
        for r in csv.DictReader(open(os.path.join(REPO, "data/discover_boundary_c1_D_reference.csv"), encoding="utf-8"))}

agent, ta, sha_a = chain(AGENT, "agent_strong_B150")
ra = runs[os.path.basename(AGENT)]
assert float(ra["spent_CU"]) == agent[-1]["cum_CU"] == 102.0
assert float(ra["CU_to_full_decision"]) == 102.0 and float(ra["CU_to_stable_correct_winner"]) == 65.0
assert ra["full_decision_correct"] == "1" and ra["narrow_window_built"] == "1"
first_fe = next(r["cum_CU"] for r in agent if r["winner"] == "Fe")
assert first_fe == 65.0, first_fe

dpol, td, sha_d = chain(DREF, "fixed_policy_D_B225")
rd = dref[os.path.basename(DREF)]
assert float(rd["spent_CU"]) == dpol[-1]["cum_CU"] == 214.0 and float(rd["CU_to_full_decision"]) == 206.0

orc = json.load(open(os.path.join(REPO, ORACLE), encoding="utf-8"))["protocol_complete_S1_S3_oracle"]
assert orc["minimum_CU"] == 22
oracle, cum = [], 0.0
steps = [("BUILD_PROCESS_WINDOW", orc["costs"]["BUILD_PROCESS_WINDOW"], 3),
         ("COMPUTE_ACTIVITY", orc["costs"]["COMPUTE_ACTIVITY_all_15"], ""),
         ("OPTIMIZE_PROCESS", orc["costs"]["OPTIMIZE_Fe_Ru_Os"], ""),
         ("BACKWARD", orc["costs"]["BACKWARD_Ru_vs_Fe"], ""),
         ("TEST_REACHABILITY", orc["costs"]["TEST_REACHABILITY_reference"], "")]
for i, (a, c, n) in enumerate(steps, 1):
    cum += c
    oracle.append({"chain": "oracle_protocol_complete", "step": i, "action": a, "cost_CU": float(c), "cum_CU": cum,
                   "window_states": n, "winner": "Fe" if a == "OPTIMIZE_PROCESS" else ""})
assert cum == 22.0

with open(os.path.join(HERE, "fig6_trajectories.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(agent[0]), lineterminator="\n")
    w.writeheader()
    for r in oracle + agent + dpol:
        w.writerow(r)
print("oracle 22 CU; agent %d steps, 102 CU (trace sha256 %s); D %d steps, 214 CU, decision at 206 (sha256 %s)"
      % (len(agent), sha_a[:12], len(dpol), sha_d[:12]))
