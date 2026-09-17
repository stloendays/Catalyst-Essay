"""DISCOVER_SCORER_V1 — the ONLY component that reads the frozen ground truth. Scores trace.json files written by discover/run.py.

  python DISCOVER_SCORER_V1.py score [discover_runs/<pattern>]   -> discover_runs/SCORES_V1.json + SCORES_V1.md (+ curves png)

Ground truth is read from the pinned canonical run (tests/frozen_hashes.json -> canonical_run) and never written anywhere the agent reads.
Metrics (E7): industrial winner accuracy; full feasible-ranking quality (Kendall tau over optimized feasible candidates + coverage);
pair decision correctness (true winner vs true atomic-best); parity/reachability classification accuracy; break-even relative error;
CU consumed; CU to first correct winner; CU to stable correct winner; decision-relevant CU fraction; unnecessary CU fraction; decision regret
(USD/t); stopping efficiency. Curves: budget -> P(correct decision), budget -> regret."""
from __future__ import annotations
import glob, json, math, sys
from pathlib import Path
from collections import defaultdict
ROOT = Path(__file__).resolve().parent
PINS = json.loads((ROOT / "tests/frozen_hashes.json").read_text(encoding="utf-8"))
GT_RES = json.loads((ROOT / PINS["canonical_run"] / "results.json").read_text(encoding="utf-8"))
_det = GT_RES["deterministic"]; _bk = GT_RES["backward_reachability"]
GT = {"winner": _det["feasible_economic_order"][0], "feasible_order": _det["feasible_economic_order"], "feasible_costs": {m: _det["metals"][m]["feasible"]["total_cost"] for m in _det["feasible_economic_order"]},
      "atomic_best": _det["activity_order"][0], "atomic_order": _det["activity_order"], "break_even": _bk["Ru_activity_break_even_multiplier"], "headroom": _bk["Ru_scaling_max_gain_all_states"],
      "reachability": "unreachable", "raw_costs": {m: _det["metals"][m]["unconstrained"]["total_cost"] for m in _det["activity_order"]}}
DECISION_PAIR = (GT["atomic_best"], GT["winner"])   # scorer-internal; never exposed
TAU_STABLE = 1.5  # a winner is "stable" once it never changes again within the trace


def kendall(a: list, b: list) -> float | None:
    """Kendall tau between two rankings of the same items (a, b lists ordered best-first)."""
    items = [x for x in a if x in b]
    if len(items) < 2: return None
    ra = {x: i for i, x in enumerate(a)}; rb = {x: i for i, x in enumerate(b)}; c = d = 0
    for i in range(len(items)):
        for j in range(i + 1, items.__len__()):
            s = (ra[items[i]] - ra[items[j]]) * (rb[items[i]] - rb[items[j]]); c += s > 0; d += s < 0
    return (c - d) / (c + d) if (c + d) else None


def relevant(step: dict) -> bool:
    """Decision-relevant calculation: touches the true decision pair or produces mandatory pre-decision information."""
    a, args = step.get("chosen_action"), step.get("chosen_args") or {}
    if a in ("BUILD_PROCESS_WINDOW", "COMPUTE_ACTIVITY", "READ_PROPERTY_UNCERTAINTY", "INSPECT_CANDIDATES", "CHECK_MODEL_VALIDITY"): return True
    metals = set(args.get("metals") or []) | ({args["metal"]} if "metal" in args else set()) | set(args.get("pair") or [])
    return bool(metals & set(DECISION_PAIR))


def _demap(obj, m: dict):
    """Map public candidate ids back to real metals (anonymous variant); identity for the named variant."""
    if isinstance(obj, dict): return {(m.get(k, k) if isinstance(k, str) else k): _demap(v, m) for k, v in obj.items()}
    if isinstance(obj, list): return [_demap(v, m) for v in obj]
    if isinstance(obj, str): return m.get(obj, obj)
    return obj


def score_trace(path: Path) -> dict:
    t = json.loads(path.read_text(encoding="utf-8")); mp = path.parent / "identity_mapping.json"
    m = json.loads(mp.read_text(encoding="utf-8"))["public_to_real"] if mp.exists() else {}
    if m: t = _demap(t, m)   # scorer-only de-anonymization; the trace file itself stays anonymous
    steps = t["steps"]; fin = t["final"]; ans = fin["answer"]; B = t["budget_CU"]
    spent = fin["spent_CU"]; w = ans["industrial_winner"]
    winner_ok = w == GT["winner"]
    rank_tau = kendall(ans["feasible_ranking_of_optimized_candidates"], GT["feasible_order"]); coverage = len([m for m in ans["feasible_ranking_of_optimized_candidates"] if m in GT["feasible_order"]]) / len(GT["feasible_order"])
    costs = ans["optimized_costs_USD_t"]; pair_ok = (DECISION_PAIR[0] in costs and DECISION_PAIR[1] in costs and costs[DECISION_PAIR[1]] < costs[DECISION_PAIR[0]])
    reach_ok = ans.get("reachability_classification") == GT["reachability"]; be = ans.get("parity_multiplier_atomic_best_vs_winner")
    be_err = abs(be - GT["break_even"]) / GT["break_even"] if isinstance(be, (int, float)) else None
    # compute to first / stable correct winner
    cum = 0.0; first = None; stable = None; last_wrong_cum = 0.0
    for s in steps:
        cum += s.get("action_cost") or 0
        if s.get("current_winner") == GT["winner"]:
            if first is None: first = cum
        else: last_wrong_cum = cum
    if first is not None and steps and steps[-1].get("current_winner") == GT["winner"]: stable = max(first, last_wrong_cum + (0 if last_wrong_cum == 0 else 1e-9)); stable = first if last_wrong_cum < first else last_wrong_cum
    rel = sum((s.get("action_cost") or 0) for s in steps if relevant(s)); irr = spent - rel
    after_stable = (spent - stable) if stable is not None else None
    regret = (GT["feasible_costs"].get(w, math.inf) - GT["feasible_costs"][GT["winner"]]) if w else math.inf
    if w and w not in GT["feasible_costs"]: regret = GT["raw_costs"].get(w, math.inf) - GT["feasible_costs"][GT["winner"]]
    errors = sum(1 for s in steps if isinstance(s.get("result"), dict) and "error" in s["result"])
    return {"trace": str(path.relative_to(ROOT)), "policy": t["policy"], "variant": t.get("task_variant", "named"), "budget_CU": B, "seed": t["seed"], "steps": len(steps), "spent_CU": spent, "why_stop": fin["why_stop"],
            "S1S2S3": [fin["stopping_status"]["S1_winner_identified"], fin["stopping_status"]["S2_no_unresolved_candidate"], fin["stopping_status"]["S3_reachability_classified_if_needed"]],
            "winner": w, "winner_correct": winner_ok, "feasible_ranking_kendall_tau": rank_tau, "feasible_ranking_coverage": coverage, "pair_decision_correct": pair_ok,
            "reachability_classification": ans.get("reachability_classification"), "reachability_correct": reach_ok, "break_even_estimate": be, "break_even_rel_error": be_err,
            "CU_to_first_correct_winner": first, "CU_to_stable_correct_winner": stable, "decision_relevant_CU_fraction": (rel / spent) if spent else None, "unnecessary_CU_fraction": (irr / spent) if spent else None,
            "CU_after_stable_winner": after_stable, "stopping_efficiency": (stable / spent) if (stable and spent) else None, "decision_regret_USD_t": regret, "action_errors": errors,
            "full_decision_correct": bool(winner_ok and pair_ok and reach_ok)}


def main(pattern: str = "discover_runs/*/trace.json"):
    rows = [score_trace(Path(p)) for p in sorted(glob.glob(str(ROOT / pattern)))]
    if not rows: print("no traces"); return
    out = ROOT / "discover_runs"; out.mkdir(exist_ok=True)
    (out / "SCORES_V1.json").write_text(json.dumps({"ground_truth_source": PINS["canonical_run"], "rows": rows}, indent=2, default=str), encoding="utf-8")
    # curves: per policy, per budget -> mean over seeds
    curve = defaultdict(lambda: defaultdict(list))
    for r in rows: curve[f"{r['policy']}[{r['variant']}]"][r["budget_CU"]].append(r)
    L = ["# DISCOVER scores (scorer V1; ground truth = pinned canonical run, hidden from policies)\n", "| policy | variant | budget | seed | winner | correct | pair | reach | BE rel err | spent | CU→first | CU→stable | relevant frac | unnecessary frac | regret | stop reason |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        f = lambda v, d=2: ("—" if v is None else (f"{v:.{d}f}" if isinstance(v, float) else str(v)))
        L.append(f"| {r['policy']} | {r['variant']} | {r['budget_CU']:.0f} | {r['seed']} | {r['winner']} | {r['winner_correct']} | {r['pair_decision_correct']} | {r['reachability_correct']} | {f(r['break_even_rel_error'], 3)} | {r['spent_CU']:.0f} | {f(r['CU_to_first_correct_winner'], 0)} | {f(r['CU_to_stable_correct_winner'], 0)} | {f(r['decision_relevant_CU_fraction'])} | {f(r['unnecessary_CU_fraction'])} | {f(r['decision_regret_USD_t'])} | {str(r['why_stop'])[:60]} |")
    L += ["", "## Curves: budget → P(full decision correct) and mean regret (mean over seeds)", "", "| policy | budget | n | P(winner correct) | P(full decision correct) | mean regret USD/t | mean spent |", "|---|---|---|---|---|---|---|"]
    curves = {}
    for p, byb in curve.items():
        for b, rs in sorted(byb.items()):
            pw = sum(r["winner_correct"] for r in rs) / len(rs); pf = sum(r["full_decision_correct"] for r in rs) / len(rs); rg = sum(min(r["decision_regret_USD_t"], 1e3) for r in rs) / len(rs); sp = sum(r["spent_CU"] for r in rs) / len(rs)
            curves.setdefault(p, []).append({"budget": b, "n": len(rs), "P_winner_correct": pw, "P_full_decision_correct": pf, "mean_regret": rg, "mean_spent": sp})
            L.append(f"| {p} | {b:.0f} | {len(rs)} | {pw:.2f} | {pf:.2f} | {rg:.2f} | {sp:.0f} |")
    (out / "SCORES_V1.md").write_text("\n".join(L) + "\n", encoding="utf-8"); (out / "CURVES_V1.json").write_text(json.dumps(curves, indent=2), encoding="utf-8")
    try:
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
        fig, ax = plt.subplots(1, 2, figsize=(12, 4.8))
        for p, cs in curves.items():
            ax[0].plot([c["budget"] for c in cs], [c["P_full_decision_correct"] for c in cs], "-o", label=p); ax[1].plot([c["budget"] for c in cs], [c["mean_regret"] for c in cs], "-o", label=p)
        ax[0].set_xlabel("compute budget (CU)"); ax[0].set_ylabel("P(full industrial decision correct)"); ax[0].set_ylim(-0.05, 1.05); ax[0].grid(alpha=0.3); ax[0].legend(fontsize=8)
        ax[1].set_xlabel("compute budget (CU)"); ax[1].set_ylabel("decision regret (USD/t)"); ax[1].grid(alpha=0.3); ax[1].legend(fontsize=8)
        fig.suptitle("DISCOVER development curves (deterministic policies; no LLM)"); fig.tight_layout(); fig.savefig(out / "CURVES_V1.png", dpi=160); plt.close(fig)
    except Exception as e: print("curve plot skipped:", e)
    print("\n".join(L)); print("\nwrote", out / "SCORES_V1.json", out / "SCORES_V1.md")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main(*(sys.argv[2:3] if len(sys.argv) > 2 else []))
