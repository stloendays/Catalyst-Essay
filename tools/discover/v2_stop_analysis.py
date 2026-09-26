"""DISCOVER-V2-STOP analysis (read-only). Scores every V2-STOP trace with the unchanged DISCOVER_SCORER_V1 and evaluates the
preregistered gates (PREREG_V2_STOP.json). Also reports, per run, the S1^S2^S3 arming point, post-arm spend by action, gate
rejections, S3' status at stop and parity recovery, and compares each cell with the matching frozen C1 cell (policy E, V1 protocol).

  python discover/v2_stop_analysis.py            # -> DISCOVER_V2_STOP/data/v2_stop_{runs,cells}.csv + v2_stop_summary.md
"""
from __future__ import annotations
import csv, glob, json, statistics as st, sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "discover"))
import DISCOVER_SCORER_V1 as S
OUT = ROOT / "DISCOVER_V2_STOP"; DATA = OUT / "data"
C1_GLOB = "DISCOVER_BOUNDARY_C1/runs/gpt-5.5-2026-04-23/traces/anonymous/*/trace.json"


def med(xs):
    xs = [x for x in xs if x is not None]; return st.median(xs) if xs else None


def analyse(p: Path) -> dict | None:
    t = json.loads(p.read_text(encoding="utf-8")); why = str(t["final"]["why_stop"])
    if why.startswith("infrastructure_failure"): return None
    sc = S.score_trace(p.resolve()); b0 = float(t["budget_CU"]); steps = t["steps"]
    armed = t["final"]["gate"]["armed_at_CU"]; spent = float(t["final"]["spent_CU"])
    post = Counter(); post_steps = 0
    if armed is not None:
        k = t["final"]["gate"]["armed_at_step"]
        for s in steps[k:]:
            if s["chosen_action"] == "STOP": continue
            post_steps += 1; post[s["chosen_action"]] += float(s.get("action_cost") or 0)
    v2f = t["final"].get("v2_status") or {}
    fa = t["final"]["answer"]; fa1 = t["final"].get("answer_v1_first_record") or {}
    return {"arm": t["arm"], "budget_CU": b0, "run_index": t["run_index"], "steps": len(steps), "why_stop": why[:60],
            "stop_mode": ("self_stop" if why.startswith("agent STOP") else "forced_stop" if why.startswith("env_forced") else "gate_limit" if why.startswith("gate_rejection") else "budget_exhausted" if why.startswith("budget") else "other"),
            "full_decision_correct": int(sc["full_decision_correct"]), "winner_correct": int(sc["winner_correct"]), "pair_correct": int(sc["pair_decision_correct"]), "reach_correct": int(sc["reachability_correct"]),
            "break_even_rel_error": sc["break_even_rel_error"], "parity_canonical": int(sc["break_even_rel_error"] is not None and sc["break_even_rel_error"] < 1e-6),
            "spent_CU": spent, "armed_at_CU": armed, "post_arm_CU": (spent - armed) if armed is not None else None, "post_arm_steps": post_steps if armed is not None else None,
            "post_arm_CU_by_action": json.dumps({k: v for k, v in post.items() if v > 0}, sort_keys=True) if armed is not None else None,
            "gate_rejections": t["final"]["gate"]["rejections"], "S3prime_at_stop": int(bool(v2f.get("S3prime_validated_stop"))), "S123_at_stop": int(bool(v2f.get("S123"))),
            "edge_pending_at_stop": json.dumps([k for k, v in (v2f.get("edge_flags") or {}).items() if v.get("any")]),
            "answer_changed_by_last_record_rule": int(fa.get("reachability_classification") != fa1.get("reachability_classification") or fa.get("parity_multiplier_atomic_best_vs_winner") != fa1.get("parity_multiplier_atomic_best_vs_winner")),
            "narrow_window": int(any(s["chosen_action"] == "BUILD_PROCESS_WINDOW" and isinstance(s.get("result"), dict) and "error" not in s["result"] and s["result"].get("n_states", 14136) < 14136 for s in steps)),
            "tokens_prompt": t["llm_meta"]["tokens"]["prompt"], "tokens_completion": t["llm_meta"]["tokens"]["completion"], "run_dir": p.parent.name}


def c1_reference() -> dict:
    ref = {}
    for p in glob.glob(str(ROOT / C1_GLOB)):
        p = Path(p); t = json.loads(p.read_text(encoding="utf-8"))
        if str(t["final"]["why_stop"]).startswith("infrastructure_failure"): continue
        sc = S.score_trace(p.resolve()); ref.setdefault(float(t["budget_CU"]), []).append((int(sc["full_decision_correct"]), float(sc["spent_CU"]), int(sc["break_even_rel_error"] is not None and sc["break_even_rel_error"] < 1e-6)))
    return {b: {"n": len(v), "full": sum(x[0] for x in v), "median_spent": med([x[1] for x in v]), "parity": sum(x[2] for x in v)} for b, v in ref.items()}


def main():
    paths = sorted(Path(p) for p in glob.glob(str(OUT / "runs" / "*" / "traces" / "anonymous" / "*" / "trace.json")))
    rows = [r for r in (analyse(p) for p in paths) if r]
    if not rows: raise SystemExit("no V2-STOP traces yet")
    DATA.mkdir(parents=True, exist_ok=True)
    with (DATA / "v2_stop_runs.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    ref = c1_reference(); cells = []
    for (arm, b), rs in sorted({(r["arm"], r["budget_CU"]): [x for x in rows if x["arm"] == r["arm"] and x["budget_CU"] == r["budget_CU"]] for r in rows}.items()):
        n = len(rs); c1 = ref.get(b, {})
        cells.append({"arm": arm, "budget_CU": b, "n": n, "full_correct": sum(r["full_decision_correct"] for r in rs), "winner_correct": sum(r["winner_correct"] for r in rs), "reach_correct": sum(r["reach_correct"] for r in rs),
                      "parity_canonical": sum(r["parity_canonical"] for r in rs), "median_spent_CU": med([r["spent_CU"] for r in rs]), "median_armed_at_CU": med([r["armed_at_CU"] for r in rs]),
                      "armed_runs": sum(1 for r in rs if r["armed_at_CU"] is not None), "median_post_arm_CU": med([r["post_arm_CU"] for r in rs]), "max_post_arm_CU": max([r["post_arm_CU"] for r in rs if r["post_arm_CU"] is not None], default=None),
                      "runs_paid_after_arm": sum(1 for r in rs if (r["post_arm_CU"] or 0) > 0), "gate_rejections_total": sum(r["gate_rejections"] for r in rs), "S3prime_at_stop": sum(r["S3prime_at_stop"] for r in rs),
                      "false_positive_S3prime": sum(1 for r in rs if r["S3prime_at_stop"] and not r["full_decision_correct"]), "narrow_window_runs": sum(r["narrow_window"] for r in rs),
                      "answer_changed_by_last_record": sum(r["answer_changed_by_last_record_rule"] for r in rs), "stop_modes": json.dumps(dict(Counter(r["stop_mode"] for r in rs)), sort_keys=True),
                      "C1_n": c1.get("n"), "C1_full": c1.get("full"), "C1_median_spent_CU": c1.get("median_spent"), "C1_parity": c1.get("parity")})
    with (DATA / "v2_stop_cells.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(cells[0].keys())); w.writeheader(); w.writerows(cells)
    # preregistered gates
    g = {}
    g["completion_>=19/20_every_cell"] = all(c["full_correct"] >= 19 for c in cells if c["n"] >= 20) if any(c["n"] >= 20 for c in cells) else None
    for arm in ("hard", "gate"):
        for b in (75.0, 5000.0):
            c = next((c for c in cells if c["arm"] == arm and c["budget_CU"] == b), None)
            if c: g[f"post_rule_median_0_{arm}_{b:.0f}"] = (c["median_post_arm_CU"] == 0)
    gate_cells = [c for c in cells if c["arm"] == "gate"]
    g["S3prime_false_positive_0"] = (sum(c["false_positive_S3prime"] for c in gate_cells) == 0) if gate_cells else None
    a75 = next((c for c in cells if c["arm"] == "anytime" and c["budget_CU"] == 75.0), None); a225 = next((c for c in cells if c["arm"] == "anytime" and c["budget_CU"] == 225.0), None)
    g["allowance_invariance_anytime_|225-75|<=25"] = (abs(a225["median_spent_CU"] - a75["median_spent_CU"]) <= 25) if (a75 and a225) else None
    L = [f"# DISCOVER-V2-STOP results ({datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%MZ')}; {len(rows)} runs; frozen scorer V1)", "",
         "| arm | CU | n | full | winner | reach | parity | median spent | median armed-at | paid after arm | median / max post-arm CU | rejections | S3' at stop | FP S3' | narrow | stop modes | C1 full / median spent / parity |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|---|---|"]
    for c in cells:
        L.append(f"| {c['arm']} | {c['budget_CU']:.0f} | {c['n']} | {c['full_correct']} | {c['winner_correct']} | {c['reach_correct']} | {c['parity_canonical']} | {c['median_spent_CU']:g} | {c['median_armed_at_CU'] if c['median_armed_at_CU'] is None else f'{c['median_armed_at_CU']:g}'} | {c['runs_paid_after_arm']} | {c['median_post_arm_CU']} / {c['max_post_arm_CU']} | {c['gate_rejections_total']} | {c['S3prime_at_stop']} | {c['false_positive_S3prime']} | {c['narrow_window_runs']} | {c['stop_modes']} | {c['C1_full']}/{c['C1_n']} / {c['C1_median_spent_CU']} / {c['C1_parity']} |")
    L += ["", "## Preregistered gates", ""] + [f"- {k}: **{v}**" for k, v in g.items()]
    (DATA / "v2_stop_summary.md").write_text("\n".join(L) + "\n", encoding="utf-8"); print("\n".join(L))


if __name__ == "__main__":
    main()
