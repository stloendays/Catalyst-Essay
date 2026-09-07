"""Cross-model stability analysis of DISCOVER V1 (PHASE E-2, 2026-09-06).

  python discover/cross_model_analysis.py

Inputs (all read-only):
  DISCOVER_FORMAL_RUNS_V1/traces/<variant>/  frozen A–D baselines + the formal gpt-5.5-2026-04-23 policy-E traces (V1, untouched)
  DISCOVER_CROSS_MODEL_V1/<model>/traces/<variant>/  policy-E traces of the additional model tiers (same driver discover/formal_e.py, same frozen protocol)
Every number comes from the frozen scorer DISCOVER_SCORER_V1.score_trace; the allocation-path extractor of discover/formal_analysis.py is reused.
Outputs: CROSS_MODEL_SCORES_V1.csv, CROSS_MODEL_FAILURE_MATRIX_V1.csv, DISCOVER_CROSS_MODEL_V1/scores/*.json, DISCOVER_CROSS_MODEL_V1/figures/X1–X6.
Nothing in DISCOVER_FORMAL_RUNS_V1 or any frozen file is written."""
from __future__ import annotations
import csv, glob, json, statistics, sys
from collections import defaultdict
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
import DISCOVER_SCORER_V1 as S
from discover.formal_analysis import allocation_paths, mean

V1 = ROOT / "DISCOVER_FORMAL_RUNS_V1"; XM = ROOT / "DISCOVER_CROSS_MODEL_V1"
MODELS = [("gpt-5.4-nano-2026-03-17", "weak", XM / "gpt-5.4-nano"), ("gpt-5.4-mini-2026-03-17", "medium", XM / "gpt-5.4-mini"), ("gpt-5.5-2026-04-23", "strong", V1)]
BUDGETS = [200, 250, 300, 500, 800, 1200, 2000]; BE_TOL = 0.01
FAILURE_MODES = [  # (id, class, description)
    ("wrong_winner", "decision_correctness", "industrial winner != Fe"),
    ("wrong_pair", "decision_correctness", "pair decision wrong or Ru/Fe not both optimized"),
    ("wrong_or_missing_reachability", "decision_correctness", "reachability class != unreachable (incl. not classified)"),
    ("llm_env_winner_disagree", "decision_correctness", "agent's stated winner != environment-derived winner"),
    ("no_backward", "decision_correctness", "BACKWARD never executed"),
    ("parity_window_relative", "quantitative_fidelity", "break-even reported but rel. error > 1 % (restricted-window parity, F1)"),
    ("parity_not_reported", "quantitative_fidelity", "no parity multiplier in the final answer"),
    ("unresolved_candidate_stop", "stopping_efficiency", "agent STOP while environment S2 false (F2)"),
    ("all_15_optimized", "stopping_efficiency", "every candidate optimized before stopping (F3)"),
    ("over_confirmation", "stopping_efficiency", "unnecessary-CU fraction > 0.25 (F3/F4)"),
    ("post_decision_spend_gt_100CU", "stopping_efficiency", "> 100 CU spent after the winner was stable (F4)"),
    ("lever_used", "interpretability", "TEST_LEVER called (F5, not a failure)"),
    ("prior_ordered_fe_first", "allocation_path", "first OPTIMIZE_PROCESS target = Fe (F6, named prior)"),
    ("non_canonical_order", "allocation_path", "activity->optimize->backward->reachability order not followed"),
    ("narrow_window_used", "allocation_path", "at least one non-full process window built (adaptive scope)"),
    ("not_agent_stop", "protocol", "run ended by budget_exhausted / max_turns / malformed limit instead of STOP"),
    ("action_errors", "protocol", ">= 1 invalid / unaffordable action"),
    ("malformed_turns", "protocol", ">= 1 turn without a tool call"),
    ("infra_retries", "protocol", ">= 1 infrastructure retry"),
]


def score_dir(root: Path, model_id: str | None) -> list[dict]:
    rows = []
    for p in sorted(glob.glob(str(root / "traces" / "*" / "*" / "trace.json"))):
        t = json.loads(Path(p).read_text(encoding="utf-8"))
        if "_smoke" in p: continue
        r = S.score_trace(Path(p)); meta = t.get("metadata") or {}; lm = t.get("llm_meta") or {}
        r["model"] = meta.get("response_model") or ("baseline" if r["policy"] != "E_llm_agent" else model_id)
        if r["policy"] == "E_llm_agent" and model_id and r["model"] != model_id: continue  # ignore foreign-model traces in a model root
        r["tokens_prompt"] = lm.get("tokens", {}).get("prompt"); r["tokens_completion"] = lm.get("tokens", {}).get("completion")
        r["infra_retries"] = lm.get("infra_retries"); r["malformed_turns"] = lm.get("malformed_turns"); r["steps_n"] = len(t["steps"])
        rows.append(r)
    return rows


def aggregate(rows: list[dict]) -> list[dict]:
    g = defaultdict(list)
    for r in rows: g[(r["model"], r["policy"], r["variant"], r["budget_CU"])].append(r)
    out = []
    for (mdl, p, v, b), rs in sorted(g.items()):
        n = len(rs); be = [r["break_even_rel_error"] for r in rs if r["break_even_rel_error"] is not None]
        out.append({"model": mdl, "policy": p, "variant": v, "budget_CU": int(b), "n": n,
                    "P_winner_correct": sum(r["winner_correct"] for r in rs) / n, "P_pair_correct": sum(bool(r["pair_decision_correct"]) for r in rs) / n,
                    "P_reachability_correct": sum(bool(r["reachability_correct"]) for r in rs) / n, "P_full_decision_correct": sum(r["full_decision_correct"] for r in rs) / n,
                    "n_break_even_reported": len(be), "mean_break_even_rel_error": mean(be), "median_break_even_rel_error": (statistics.median(be) if be else None), "n_break_even_exact": sum(1 for x in be if x <= BE_TOL),
                    "mean_spent_CU": mean([r["spent_CU"] for r in rs]), "mean_CU_to_first_correct": mean([r["CU_to_first_correct_winner"] for r in rs]), "n_first_correct": sum(r["CU_to_first_correct_winner"] is not None for r in rs),
                    "mean_CU_to_stable_correct": mean([r["CU_to_stable_correct_winner"] for r in rs]), "n_stable_correct": sum(r["CU_to_stable_correct_winner"] is not None for r in rs),
                    "mean_unnecessary_CU_fraction": mean([r["unnecessary_CU_fraction"] for r in rs]), "mean_regret_USD_t": mean([min(r["decision_regret_USD_t"], 1e3) for r in rs]),
                    "mean_stopping_efficiency": mean([r["stopping_efficiency"] for r in rs]), "mean_action_errors": mean([r["action_errors"] for r in rs]),
                    "mean_steps": mean([r["steps_n"] for r in rs]), "mean_tokens": mean([(r["tokens_prompt"] or 0) + (r["tokens_completion"] or 0) for r in rs if r.get("tokens_prompt") is not None])})
    return out


def classify(r: dict, ap: dict, trace: dict) -> dict:
    steps = trace["steps"]; seq = [s["chosen_action"] for s in steps]
    ans = trace["final"]["answer"]; fin = trace["final"]
    first_opt = next((s for s in steps if s["chosen_action"] == "OPTIMIZE_PROCESS" and isinstance(s.get("result"), dict) and "error" not in s["result"]), None)
    m = {}
    mp = Path(ROOT / r["trace"]).parent / "identity_mapping.json"
    if mp.exists(): m = json.loads(mp.read_text(encoding="utf-8"))["public_to_real"]
    fo_metal = None
    if first_opt:
        a = first_opt.get("chosen_args") or {}; x = a.get("metal") or ((a.get("metals") or [None])[0]); fo_metal = m.get(x, x)
    windows = ap.get("windows_built") or []
    narrow = any((w[1] or 0) < 14136 for w in windows if isinstance(w, (list, tuple)) and len(w) > 1)
    return {"wrong_winner": not r["winner_correct"], "wrong_pair": not bool(r["pair_decision_correct"]), "wrong_or_missing_reachability": not bool(r["reachability_correct"]),
            "llm_env_winner_disagree": ap.get("llm_env_winner_agree") is False, "no_backward": "BACKWARD" not in seq,
            "parity_window_relative": (r["break_even_rel_error"] is not None and r["break_even_rel_error"] > BE_TOL), "parity_not_reported": r["break_even_rel_error"] is None,
            "unresolved_candidate_stop": (str(fin["why_stop"]).startswith("agent STOP") and not fin["stopping_status"]["S2_no_unresolved_candidate"]),
            "all_15_optimized": len(ans.get("optimized_costs_USD_t") or {}) >= 15, "over_confirmation": (r["unnecessary_CU_fraction"] or 0) > 0.25,
            "post_decision_spend_gt_100CU": (r["CU_after_stable_winner"] or 0) > 100, "lever_used": "TEST_LEVER" in seq, "prior_ordered_fe_first": fo_metal == "Fe",
            "non_canonical_order": not ap.get("canonical_order", False), "narrow_window_used": narrow, "not_agent_stop": not str(fin["why_stop"]).startswith("agent STOP"),
            "action_errors": (r["action_errors"] or 0) > 0, "malformed_turns": (r["malformed_turns"] or 0) > 0, "infra_retries": (r["infra_retries"] or 0) > 0}


def figures(agg: list[dict], rows: list[dict], fm: list[dict]):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt; import numpy as np; from matplotlib.ticker import NullFormatter, NullLocator
    fd = XM / "figures"; fd.mkdir(exist_ok=True)
    col = {"gpt-5.4-nano-2026-03-17": "#1f77b4", "gpt-5.4-mini-2026-03-17": "#ff7f0e", "gpt-5.5-2026-04-23": "#d62728", "D_fixed_voi": "#7f7f7f", "B_activity_first": "#2ca02c"}
    tier = {m: t for m, t, _ in MODELS}
    def series(key, variant, model=None, policy="E_llm_agent"):
        pts = sorted([(a["budget_CU"], a[key]) for a in agg if a["policy"] == policy and a["variant"] == variant and (model is None or a["model"] == model) and a[key] is not None])
        return [x for x, _ in pts], [y for _, y in pts]
    panels = [("P_full_decision_correct", "P(complete correct industrial decision)", "X1_full_decision", (-0.05, 1.05)), ("P_reachability_correct", "reachability-classification accuracy", "X2_reachability", (-0.05, 1.05)),
              ("mean_break_even_rel_error", "break-even relative error (mean of reported)", "X3_break_even_error", None), ("mean_CU_to_stable_correct", "CU to stable correct winner (mean)", "X4_CU_to_stable", None),
              ("mean_unnecessary_CU_fraction", "unnecessary-CU fraction (mean)", "X5_unnecessary_CU", (-0.02, 0.8)), ("mean_regret_USD_t", "decision regret (USD/t, ∞ capped 1000)", "X6_regret", None)]
    for variant in ("anonymous", "named"):
        fig, axes = plt.subplots(2, 3, figsize=(16, 9))
        for ax, (key, ylabel, name, ylim) in zip(axes.flat, panels):
            for mdl, t, _ in MODELS:
                x, y = series(key, variant, mdl); ax.plot(x, y, "-o", color=col[mdl], lw=2.2, label=f"E {mdl} ({t})")
            for pol in ("D_fixed_voi", "B_activity_first"):
                x, y = series(key, variant, None, pol); ax.plot(x, y, "--s", color=col[pol], lw=1.3, ms=4, label=pol)
            ax.set_xlabel("compute budget (CU)"); ax.set_ylabel(ylabel); ax.grid(alpha=0.3); ax.set_xscale("log"); ax.set_xticks(BUDGETS); ax.set_xticklabels([str(b) for b in BUDGETS]); ax.xaxis.set_minor_locator(NullLocator())
            if ylim: ax.set_ylim(*ylim)
            if key == "mean_regret_USD_t": ax.set_yscale("symlog", linthresh=1.0); ax.set_ylim(-0.1, 1500)
            ax.set_title(name.replace("_", " "), fontsize=11)
        axes.flat[0].legend(fontsize=8, loc="lower right"); fig.suptitle(f"DISCOVER V1 cross-model curves — {variant} task ({'PRIMARY' if variant == 'anonymous' else 'secondary'}); policy E, n = 5 per budget", fontsize=13)
        fig.tight_layout(); fig.savefig(fd / f"X_cross_model_curves_{variant}.png", dpi=170); plt.close(fig)
        for key, ylabel, name, ylim in panels:
            fig, ax = plt.subplots(figsize=(7.5, 4.8))
            for mdl, t, _ in MODELS:
                x, y = series(key, variant, mdl); ax.plot(x, y, "-o", color=col[mdl], lw=2.2, label=f"E {mdl} ({t})")
            for pol in ("D_fixed_voi", "B_activity_first"):
                x, y = series(key, variant, None, pol); ax.plot(x, y, "--s", color=col[pol], lw=1.3, ms=4, label=pol)
            ax.set_xlabel("compute budget (CU)"); ax.set_ylabel(ylabel); ax.grid(alpha=0.3); ax.set_xscale("log"); ax.set_xticks(BUDGETS); ax.set_xticklabels([str(b) for b in BUDGETS]); ax.xaxis.set_minor_locator(NullLocator()); ax.legend(fontsize=8)
            if ylim: ax.set_ylim(*ylim)
            if key == "mean_regret_USD_t": ax.set_yscale("symlog", linthresh=1.0); ax.set_ylim(-0.1, 1500)
            ax.set_title(f"{name}: {variant}", fontsize=11); fig.tight_layout(); fig.savefig(fd / f"{name}_{variant}.png", dpi=170); plt.close(fig)
    # X7 failure-mode matrix heatmap: rows = failure modes, columns = model x variant, value = fraction of the 35 runs
    ids = [f[0] for f in FAILURE_MODES]; cols = [(m, v) for m, _, _ in MODELS for v in ("anonymous", "named")]
    M = np.zeros((len(ids), len(cols)))
    for j, (mdl, v) in enumerate(cols):
        rs = [f for f in fm if f["model"] == mdl and f["variant"] == v]
        for i, fid in enumerate(ids): M[i, j] = (sum(f[fid] for f in rs) / len(rs)) if rs else np.nan
    fig, ax = plt.subplots(figsize=(10, 9)); im = ax.imshow(M, cmap="Reds", vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(len(cols))); ax.set_xticklabels([f"{tier[m]}\n{m}\n{v}" for m, v in cols], fontsize=7); ax.set_yticks(range(len(ids))); ax.set_yticklabels([f"[{f[1][:4]}] {f[0]}" for f in FAILURE_MODES], fontsize=8)
    for i in range(len(ids)):
        for j in range(len(cols)):
            if not np.isnan(M[i, j]): ax.text(j, i, f"{M[i, j]:.2f}", ha="center", va="center", fontsize=7, color="white" if M[i, j] > 0.6 else "black")
    fig.colorbar(im, ax=ax, label="fraction of the 35 policy-E runs (7 budgets × 5)"); ax.set_title("X7: failure-mode matrix across model tiers (DISCOVER V1, frozen protocol)", fontsize=11)
    fig.tight_layout(); fig.savefig(fd / "X7_failure_mode_matrix.png", dpi=170); plt.close(fig)
    # X8 per-budget failure-mode matrix for the anonymous task (key modes only)
    key_modes = ["wrong_winner", "wrong_pair", "wrong_or_missing_reachability", "parity_window_relative", "parity_not_reported", "unresolved_candidate_stop", "over_confirmation", "all_15_optimized", "not_agent_stop", "action_errors"]
    fig, axes = plt.subplots(1, 3, figsize=(17, 5.5), sharey=True)
    for ax, (mdl, t, _) in zip(axes, MODELS):
        Mb = np.zeros((len(key_modes), len(BUDGETS)))
        for j, b in enumerate(BUDGETS):
            rs = [f for f in fm if f["model"] == mdl and f["variant"] == "anonymous" and int(f["budget_CU"]) == b]
            for i, fid in enumerate(key_modes): Mb[i, j] = (sum(f[fid] for f in rs) / len(rs)) if rs else np.nan
        im = ax.imshow(Mb, cmap="Reds", vmin=0, vmax=1, aspect="auto"); ax.set_xticks(range(len(BUDGETS))); ax.set_xticklabels(BUDGETS); ax.set_yticks(range(len(key_modes))); ax.set_yticklabels(key_modes, fontsize=8)
        for i in range(len(key_modes)):
            for j in range(len(BUDGETS)):
                if not np.isnan(Mb[i, j]): ax.text(j, i, f"{Mb[i, j]:.1f}", ha="center", va="center", fontsize=7, color="white" if Mb[i, j] > 0.6 else "black")
        ax.set_title(f"{t}: {mdl}", fontsize=10); ax.set_xlabel("budget (CU)")
    fig.suptitle("X8: failure modes by budget — anonymous task (fraction of 5 runs)", fontsize=12); fig.tight_layout(); fig.savefig(fd / "X8_failure_by_budget_anonymous.png", dpi=170); plt.close(fig)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    (XM / "scores").mkdir(parents=True, exist_ok=True)
    rows = []; paths = {}
    for mdl, tier, root in MODELS:
        rows += [r for r in score_dir(root, mdl) if r["policy"] == "E_llm_agent"]
        for ap in allocation_paths(root):
            key = str(Path(ap["trace"]))
            paths[key] = ap
    rows += [r for r in score_dir(V1, None) if r["policy"] != "E_llm_agent"]  # frozen A–D baselines, reused, not re-run
    agg = aggregate(rows)
    (XM / "scores" / "per_trace_scores.json").write_text(json.dumps(rows, indent=2, default=str), encoding="utf-8")
    with (ROOT / "CROSS_MODEL_SCORES_V1.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(agg[0])); w.writeheader(); w.writerows(agg)
    # failure matrix per E trace + aggregated per model/variant(/budget)
    fm = []
    for r in rows:
        if r["policy"] != "E_llm_agent": continue
        ap = paths.get(str(Path(r["trace"])), {}); t = json.loads((ROOT / r["trace"]).read_text(encoding="utf-8"))
        c = classify(r, ap, t); c.update({"model": r["model"], "variant": r["variant"], "budget_CU": int(r["budget_CU"]), "run": r["seed"], "trace": r["trace"], "spent_CU": r["spent_CU"], "break_even_estimate": r["break_even_estimate"],
                                          "break_even_rel_error": r["break_even_rel_error"], "unnecessary_CU_fraction": r["unnecessary_CU_fraction"], "CU_after_stable_winner": r["CU_after_stable_winner"], "why_stop": str(r["why_stop"])[:160],
                                          "windows_built": json.dumps(ap.get("windows_built")), "sequence": " ".join(ap.get("sequence") or [])})
        fm.append(c)
    (XM / "scores" / "failure_per_trace.json").write_text(json.dumps(fm, indent=2, default=str), encoding="utf-8")
    ids = [f[0] for f in FAILURE_MODES]; cls = {f[0]: f[1] for f in FAILURE_MODES}; desc = {f[0]: f[2] for f in FAILURE_MODES}
    with (ROOT / "CROSS_MODEL_FAILURE_MATRIX_V1.csv").open("w", newline="", encoding="utf-8") as f:
        keys = ["failure_mode", "class", "description", "model", "tier", "variant", "budget_CU", "n_runs", "n_failed", "fraction"]; w = csv.DictWriter(f, fieldnames=keys); w.writeheader()
        for fid in ids:
            for mdl, tier, _ in MODELS:
                for v in ("anonymous", "named"):
                    for b in ["all"] + BUDGETS:
                        rs = [x for x in fm if x["model"] == mdl and x["variant"] == v and (b == "all" or x["budget_CU"] == b)]
                        if rs: w.writerow({"failure_mode": fid, "class": cls[fid], "description": desc[fid], "model": mdl, "tier": tier, "variant": v, "budget_CU": b, "n_runs": len(rs), "n_failed": sum(x[fid] for x in rs), "fraction": sum(x[fid] for x in rs) / len(rs)})
    with (XM / "scores" / "failure_per_trace.csv").open("w", newline="", encoding="utf-8") as f:
        keys = ["model", "variant", "budget_CU", "run", "spent_CU"] + ids + ["break_even_estimate", "break_even_rel_error", "unnecessary_CU_fraction", "CU_after_stable_winner", "why_stop", "windows_built", "sequence", "trace"]
        w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); w.writerows([{k: x.get(k) for k in keys} for x in fm])
    figures(agg, rows, fm)
    nE = sum(1 for r in rows if r["policy"] == "E_llm_agent"); print(f"scored {len(rows)} traces ({nE} policy-E across {len(MODELS)} models); wrote CROSS_MODEL_SCORES_V1.csv, CROSS_MODEL_FAILURE_MATRIX_V1.csv, figures -> {XM / 'figures'}")
