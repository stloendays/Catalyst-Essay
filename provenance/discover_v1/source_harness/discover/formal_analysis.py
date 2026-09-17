"""Formal single-model analysis (PHASE E). Uses ONLY the frozen scorer (DISCOVER_SCORER_V1.score_trace) for every number.

  python discover/formal_analysis.py --root DISCOVER_FORMAL_RUNS_V1 [--copy-baselines]

Steps: (1) optionally copy the frozen A–D v1 traces (discover_runs/*_v1_*) into <root>/traces/<variant>/ so the formal set is self-contained;
(2) score every trace; (3) DISCOVER_POLICY_COMPARISON_V1.csv, DISCOVER_BUDGET_CURVES_V1.csv; (4) figures E1–E4 (anonymous = main, named = supplementary);
(5) allocation-path and failure extraction for policy E traces -> <root>/scores/allocation_paths.json + failure_table.csv."""
from __future__ import annotations
import argparse, csv, glob, json, shutil, statistics, sys
from collections import defaultdict
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
import DISCOVER_SCORER_V1 as S
COMPETITIVE = set(S.GT["feasible_order"])  # scorer-only: candidates that are feasible in the ground truth (everything else is obviously non-competitive)


def copy_baselines(root: Path):
    for p in glob.glob(str(ROOT / "discover_runs" / "*_v1_*")):
        src = Path(p); variant = "anonymous" if "_anon_" in src.name else "named"; dst = root / "traces" / variant / src.name
        if not dst.exists(): shutil.copytree(src, dst)


def score_all(root: Path) -> list[dict]:
    rows = []
    for p in sorted(glob.glob(str(root / "traces" / "*" / "*" / "trace.json"))):
        r = S.score_trace(Path(p)); t = json.loads(Path(p).read_text(encoding="utf-8"))
        r["tokens_prompt"] = (t.get("llm_meta") or {}).get("tokens", {}).get("prompt"); r["tokens_completion"] = (t.get("llm_meta") or {}).get("tokens", {}).get("completion")
        r["response_model"] = (t.get("metadata") or {}).get("response_model"); r["infra_retries"] = (t.get("llm_meta") or {}).get("infra_retries"); r["malformed_turns"] = (t.get("llm_meta") or {}).get("malformed_turns")
        rows.append(r)
    return rows


def mean(xs):
    xs = [x for x in xs if isinstance(x, (int, float)) and x == x and abs(x) != float("inf")]
    return (sum(xs) / len(xs)) if xs else None


def aggregate(rows: list[dict]) -> list[dict]:
    g = defaultdict(list)
    for r in rows: g[(r["policy"], r["variant"], r["budget_CU"])].append(r)
    out = []
    for (p, v, b), rs in sorted(g.items()):
        n = len(rs); out.append({"policy": p, "variant": v, "budget_CU": b, "n": n,
                                 "P_winner_correct": sum(r["winner_correct"] for r in rs) / n, "P_pair_correct": sum(bool(r["pair_decision_correct"]) for r in rs) / n,
                                 "P_reachability_correct": sum(bool(r["reachability_correct"]) for r in rs) / n, "P_full_decision_correct": sum(r["full_decision_correct"] for r in rs) / n,
                                 "mean_break_even_rel_error": mean([r["break_even_rel_error"] for r in rs]), "n_break_even_reported": sum(r["break_even_rel_error"] is not None for r in rs),
                                 "mean_spent_CU": mean([r["spent_CU"] for r in rs]), "mean_CU_to_first_correct": mean([r["CU_to_first_correct_winner"] for r in rs]), "n_first_correct": sum(r["CU_to_first_correct_winner"] is not None for r in rs),
                                 "mean_CU_to_stable_correct": mean([r["CU_to_stable_correct_winner"] for r in rs]), "n_stable_correct": sum(r["CU_to_stable_correct_winner"] is not None for r in rs),
                                 "mean_unnecessary_CU_fraction": mean([r["unnecessary_CU_fraction"] for r in rs]), "mean_regret_USD_t": mean([min(r["decision_regret_USD_t"], 1e3) for r in rs]),
                                 "mean_stopping_efficiency": mean([r["stopping_efficiency"] for r in rs]), "mean_action_errors": mean([r["action_errors"] for r in rs]),
                                 "mean_tokens": mean([(r["tokens_prompt"] or 0) + (r["tokens_completion"] or 0) for r in rs if r["tokens_prompt"] is not None])})
    return out


def figures(agg: list[dict], rows: list[dict], root: Path):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    fig_dir = root / "figures"; fig_dir.mkdir(exist_ok=True); pols = ["A_random", "B_activity_first", "C_uncertainty_first", "D_fixed_voi", "E_llm_agent"]
    col = {"A_random": "#1f77b4", "B_activity_first": "#ff7f0e", "C_uncertainty_first": "#2ca02c", "D_fixed_voi": "#7f7f7f", "E_llm_agent": "#d62728"}
    for variant in ("anonymous", "named"):
        for key, ylabel, name in (("P_full_decision_correct", "P(complete correct industrial decision)", "E1_budget_vs_P_full_decision"), ("mean_regret_USD_t", "decision regret (USD/t, ∞ capped at 1000)", "E2_budget_vs_regret"), ("P_reachability_correct", "reachability-classification accuracy", "E3_budget_vs_reachability_accuracy")):
            fig, ax = plt.subplots(figsize=(8, 5))
            for p in pols:
                pts = sorted([(a["budget_CU"], a[key]) for a in agg if a["policy"] == p and a["variant"] == variant and a[key] is not None])
                if pts: ax.plot([x for x, _ in pts], [y for _, y in pts], "-o", color=col[p], label=p, lw=2.2 if p in ("D_fixed_voi", "E_llm_agent") else 1.4)
            ax.set_xlabel("compute budget (CU)"); ax.set_ylabel(ylabel); ax.grid(alpha=0.3); ax.legend(fontsize=9)
            if key != "mean_regret_USD_t": ax.set_ylim(-0.05, 1.05)
            else: ax.set_yscale("symlog", linthresh=1.0)
            ax.set_title(f"{name.split('_')[0]}: {variant} task ({'PRIMARY' if variant == 'anonymous' else 'secondary'})", fontsize=12); fig.tight_layout(); fig.savefig(fig_dir / f"{name}_{variant}.png", dpi=170); plt.close(fig)
        # E4: distribution of CU to stable correct decision per policy (all budgets pooled; None -> not reached)
        fig, ax = plt.subplots(figsize=(8, 5)); data = []; labels = []
        for p in pols:
            xs = [r["CU_to_stable_correct_winner"] for r in rows if r["policy"] == p and r["variant"] == variant and r["full_decision_correct"] and r["CU_to_stable_correct_winner"] is not None]
            nr = sum(1 for r in rows if r["policy"] == p and r["variant"] == variant)
            if xs: data.append(xs); labels.append(f"{p}\n(n={len(xs)}/{nr} complete)")
        if data:
            ax.boxplot(data, showmeans=True); ax.set_xticks(range(1, len(labels) + 1)); ax.set_xticklabels(labels); ax.set_ylabel("CU to stable correct winner (runs with complete correct decision)"); ax.grid(alpha=0.3, axis="y")
            ax.set_title(f"E4: distribution of CU to stable correct decision — {variant} task", fontsize=12); plt.setp(ax.get_xticklabels(), fontsize=8)
        fig.tight_layout(); fig.savefig(fig_dir / f"E4_CU_to_stable_decision_{variant}.png", dpi=170); plt.close(fig)


def allocation_paths(root: Path) -> list[dict]:
    """Post-hoc allocation analysis of policy-E traces (scorer-only knowledge of which candidates are competitive)."""
    out = []
    for p in sorted(glob.glob(str(root / "traces" / "*" / "E_llm_agent_*" / "trace.json"))):
        t = json.loads(Path(p).read_text(encoding="utf-8")); mp = Path(p).parent / "identity_mapping.json"; m = json.loads(mp.read_text(encoding="utf-8"))["public_to_real"] if mp.exists() else {}
        steps = t["steps"]; seq = [s["chosen_action"] for s in steps]; spent = t["final"]["spent_CU"]
        def metals_of(s):
            a = s.get("chosen_args") or {}; ms = set(a.get("metals") or []) | ({a["metal"]} if a.get("metal") else set()) | set(a.get("pair") or []) | ({a["candidate"]} if a.get("candidate") else set())
            return {m.get(x, x) for x in ms}
        cu_noncomp = sum((s.get("action_cost") or 0) for s in steps if metals_of(s) and not (metals_of(s) & COMPETITIVE))
        cu_pair = sum((s.get("action_cost") or 0) for s in steps if metals_of(s) & set(S.DECISION_PAIR))
        first_mismatch = None; first_backward = None; first_reach = None; cum = 0.0; after_mismatch_pair = 0.0; after_mismatch_total = 0.0
        for s in steps:
            cum += s.get("action_cost") or 0
            st = s.get("state_after") or {}; w = st.get("current_lowest_cost_candidate"); act_known = s.get("known_evidence", {}).get("activity", [])
            # mismatch is visible to the agent when both a leader exists and the highest computed activity (among all 15) differs from it
            if first_mismatch is None and w and len(act_known) == 15:
                sa = s.get("stopping_status_before", {}).get("atomic_best") or None
                if sa and m.get(sa, sa) != m.get(w, w): first_mismatch = cum
            if first_backward is None and s["chosen_action"] == "BACKWARD": first_backward = cum
            if first_reach is None and s["chosen_action"] == "TEST_REACHABILITY": first_reach = cum
            if first_mismatch is not None and cum > first_mismatch:
                after_mismatch_total += s.get("action_cost") or 0
                if metals_of(s) & set(S.DECISION_PAIR): after_mismatch_pair += s.get("action_cost") or 0
        stages = {"activity_screen": "COMPUTE_ACTIVITY" in seq, "process_optimization": "OPTIMIZE_PROCESS" in seq, "uncertainty_mc": "RUN_MC" in seq, "backward": "BACKWARD" in seq, "reachability": "TEST_REACHABILITY" in seq, "validity_check": "CHECK_MODEL_VALIDITY" in seq, "lever_test": "TEST_LEVER" in seq, "stop_called": "STOP" in seq}
        order_ok = all(x in seq for x in ("COMPUTE_ACTIVITY", "OPTIMIZE_PROCESS", "BACKWARD", "TEST_REACHABILITY")) and seq.index("COMPUTE_ACTIVITY") < seq.index("OPTIMIZE_PROCESS") < seq.index("BACKWARD") < seq.index("TEST_REACHABILITY")
        ans = t["final"]["answer"]; lf = t["final"].get("llm_final_answer") or {}
        pub_ids = set(m) if m else {"Ag", "Au", "Co", "Cu", "Fe", "Ir", "Mo", "Ni", "Os", "Pd", "Pt", "Re", "Rh", "Ru", "W"}
        def first_id(obj, keys=("industrial_winner", "winner", "best_candidate", "industrial_candidate", "best_industrial_candidate", "recommended_candidate", "candidate", "id")):
            """First candidate id found under a winner-like key (recursive), else the first candidate id string anywhere in the payload."""
            if isinstance(obj, dict):
                for k in keys:
                    v = obj.get(k)
                    if isinstance(v, str) and v in pub_ids: return v
                    if isinstance(v, dict):
                        r = first_id(v, keys)
                        if r: return r
                for v in obj.values():
                    r = first_id(v, keys)
                    if r: return r
            if isinstance(obj, list):
                for v in obj:
                    r = first_id(v, keys)
                    if r: return r
            if isinstance(obj, str) and obj in pub_ids: return obj
            return None
        lf_w = first_id(lf)
        env_w_real = m.get(ans["industrial_winner"], ans["industrial_winner"]) if ans["industrial_winner"] else None
        stop_claim_vs_env = {"env_S2": t["final"]["stopping_status"]["S2_no_unresolved_candidate"], "env_S3": t["final"]["stopping_status"]["S3_reachability_classified_if_needed"],
                             "env_unresolved": [m.get(x, x) for x in t["final"]["stopping_status"]["unresolved_candidates"]], "llm_why_stop": str((lf or {}).get("why_stop", ""))[:200]}
        windows = [s["result"] for s in steps if s["chosen_action"] == "BUILD_PROCESS_WINDOW" and isinstance(s.get("result"), dict) and "error" not in s["result"]]
        bw = [s for s in steps if s["chosen_action"] == "BACKWARD" and isinstance(s.get("result"), dict) and "error" not in s["result"]]
        bw_windows = [s["result"].get("window") for s in bw]
        out.append({"trace": str(Path(p).relative_to(ROOT)), "variant": t["task_variant"], "budget_CU": t["budget_CU"], "run": t["seed"], "n_steps": len(steps), "sequence": seq, "stages": stages, "canonical_order": order_ok,
                    "spent_CU": spent, "CU_on_noncompetitive_candidates": cu_noncomp, "frac_noncompetitive": (cu_noncomp / spent) if spent else None, "CU_on_decision_pair": cu_pair,
                    "CU_at_first_visible_mismatch": first_mismatch, "CU_at_first_backward": first_backward, "CU_at_first_reachability": first_reach,
                    "pair_fraction_after_mismatch": (after_mismatch_pair / after_mismatch_total) if after_mismatch_total else None,
                    "env_winner": env_w_real, "llm_stated_winner": m.get(lf_w, lf_w) if lf_w else None, "llm_env_winner_agree": (m.get(lf_w, lf_w) == env_w_real) if lf_w else None,
                    "stop_claim_vs_env": stop_claim_vs_env, "windows_built": [(w.get("window"), w.get("n_states"), w.get("P_range")) for w in windows], "backward_windows": bw_windows,
                    "break_even_reported": ans.get("parity_multiplier_atomic_best_vs_winner"),
                    "why_stop": t["final"]["why_stop"], "infra_retries": t["llm_meta"]["infra_retries"], "malformed_turns": t["llm_meta"]["malformed_turns"], "action_errors": sum(1 for s in steps if isinstance(s.get("result"), dict) and "error" in s["result"]),
                    "tokens": t["llm_meta"]["tokens"], "response_model": t.get("metadata", {}).get("response_model")})
    return out


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(); ap.add_argument("--root", default="DISCOVER_FORMAL_RUNS_V1"); ap.add_argument("--copy-baselines", action="store_true"); a = ap.parse_args()
    root = ROOT / a.root; (root / "scores").mkdir(parents=True, exist_ok=True); (root / "metadata").mkdir(exist_ok=True)
    if a.copy_baselines: copy_baselines(root)
    rows = score_all(root); agg = aggregate(rows)
    (root / "scores" / "per_trace_scores.json").write_text(json.dumps(rows, indent=2, default=str), encoding="utf-8")
    with (ROOT / "DISCOVER_POLICY_COMPARISON_V1.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(agg[0])); w.writeheader(); w.writerows(agg)
    with (ROOT / "DISCOVER_BUDGET_CURVES_V1.csv").open("w", newline="", encoding="utf-8") as f:
        keys = ["policy", "variant", "budget_CU", "n", "P_full_decision_correct", "P_winner_correct", "P_pair_correct", "P_reachability_correct", "mean_regret_USD_t", "mean_spent_CU", "mean_CU_to_stable_correct"]
        w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); w.writerows([{k: r[k] for k in keys} for r in agg])
    figures(agg, rows, root); paths = allocation_paths(root)
    (root / "scores" / "allocation_paths.json").write_text(json.dumps(paths, indent=2, default=str), encoding="utf-8")
    if paths:
        with (root / "scores" / "failure_table.csv").open("w", newline="", encoding="utf-8") as f:
            keys = ["trace", "variant", "budget_CU", "run", "n_steps", "spent_CU", "env_winner", "llm_stated_winner", "llm_env_winner_agree", "why_stop", "infra_retries", "malformed_turns", "action_errors", "frac_noncompetitive", "CU_at_first_visible_mismatch", "CU_at_first_backward", "CU_at_first_reachability", "canonical_order"]
            w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); w.writerows([{k: p[k] for k in keys} for p in paths])
    print(f"scored {len(rows)} traces; {len(agg)} policy/variant/budget cells; {len(paths)} E traces analysed"); print("wrote DISCOVER_POLICY_COMPARISON_V1.csv, DISCOVER_BUDGET_CURVES_V1.csv, figures ->", root / "figures")
