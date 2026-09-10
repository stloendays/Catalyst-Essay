"""
DISCOVER-BOUNDARY-C1 Phase B analysis: capability gating at 175 / 225 CU (mini, nano) against the strong Phase A results.
Reads traces only (frozen scorer + boundary_c1_metrics); writes data/discover_boundary_c1_phase_b_{runs,summary,tokens}.csv,
_metadata.json and figures P1-P4. No protocol element is touched. Bootstrap/permutation seed 20260910.
Usage: python discover/boundary_c1_phase_b_analysis.py [--repo <Catalyst-Essay root>]
"""
from __future__ import annotations
import argparse, csv, glob, hashlib, json, math, platform, shutil, sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
from scipy import stats
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "discover"))
import DISCOVER_SCORER_V1 as S
from boundary_c1_metrics import cu_to_full, validate_against_frozen
from boundary_c1_analysis import score_run, wilson, TIER
OUT = ROOT / "DISCOVER_BOUNDARY_C1"; DATA = OUT / "data"; FIG = OUT / "figures"
MODELS = ["gpt-5.4-nano-2026-03-17", "gpt-5.4-mini-2026-03-17", "gpt-5.5-2026-04-23"]
COL = {"gpt-5.4-nano-2026-03-17": "#d62728", "gpt-5.4-mini-2026-03-17": "#ff7f0e", "gpt-5.5-2026-04-23": "#1f77b4"}
PB_BUDGETS = [175, 225]; D_THRESHOLD = 206


def taxonomy(t: dict, sc: dict) -> str:
    """Where a non-full run failed (first failing component in decision order), plus the proximate cause."""
    if sc["full_decision_correct"]: return "full"
    steps = t["steps"]; why = str(sc["why_stop"])
    ran_backward = any(s.get("chosen_action") == "BACKWARD" and isinstance(s.get("result"), dict) and "error" not in s["result"] for s in steps)
    ran_reach = any(s.get("chosen_action") == "TEST_REACHABILITY" and isinstance(s.get("result"), dict) and "classification" in s["result"] for s in steps)
    if not sc["winner_correct"]:
        return "no_winner" if sc["winner"] is None else "wrong_winner"
    if not sc["pair_decision_correct"]: return "pair_unresolved (decision pair not both optimized / wrong order)"
    if not sc["reachability_correct"]:
        if not ran_backward: return "reachability_missing: BACKWARD never executed" + (" [budget_exhausted]" if "budget_exhausted" in why or "Budget exhausted" in why else " [agent STOP]")
        if not ran_reach: return "reachability_missing: TEST_REACHABILITY never classified" + (" [budget_exhausted]" if "budget_exhausted" in why or "Budget exhausted" in why else " [agent STOP]")
        return "reachability_wrong: classified but not 'unreachable' (wrong pair / self-parity multiplier)"
    return "other"


def error_kinds(t: dict) -> Counter:
    c = Counter()
    for s in t["steps"]:
        r = s.get("result")
        if isinstance(r, dict) and "error" in r:
            e = str(r["error"]); a = s.get("chosen_action")
            kind = "unaffordable (BudgetExceeded)" if "BudgetExceeded" in e else ("invalid/undeclared argument" if "InvalidArguments" in e or "unexpected keyword" in e or "TypeError" in e else ("precondition (e.g. BACKWARD before optimization)" if "ValueError" in e else "unknown action" if "Unknown" in e else "other"))
            c[f"{a}: {kind}"] += 1
    return c


def collect():
    rows = []
    for p in glob.glob(str(OUT / "runs" / "*" / "traces" / "anonymous" / "*" / "trace.json")):
        r = score_run(Path(p), "C1"); t = json.loads(Path(p).read_text(encoding="utf-8")); sc = S.score_trace(Path(p))
        r["failure_taxonomy"] = taxonomy(t, sc); r["error_kinds"] = json.dumps(error_kinds(t)); r["n_api_requests"] = len(t.get("llm_meta", {}).get("response_models", []))
        r["ran_backward"] = int(any(s.get("chosen_action") == "BACKWARD" and isinstance(s.get("result"), dict) and "error" not in s["result"] for s in t["steps"]))
        r["ran_reachability"] = int(any(s.get("chosen_action") == "TEST_REACHABILITY" and isinstance(s.get("result"), dict) and "classification" in s["result"] for s in t["steps"]))
        r["phase"] = "B" if r["model"] in MODELS[:2] else "A"; rows.append(r)
    dref = {}
    for p in list(glob.glob(str(OUT / "D_reference" / "traces" / "anonymous" / "*" / "trace.json"))) + list(glob.glob(str(ROOT / "DISCOVER_FORMAL_RUNS_V1" / "traces" / "anonymous" / "D_fixed_voi_anon_B2[05]0_*" / "trace.json"))):
        r = score_run(Path(p), "D"); dref[int(r["budget_CU"])] = r
    return rows, dref


def summarise(rows, dref):
    out = []
    for m in MODELS:
        for b in sorted({int(r["budget_CU"]) for r in rows if r["model"] == m}):
            rs = [r for r in rows if r["model"] == m and int(r["budget_CU"]) == b]; n = len(rs); k = sum(r["full_decision_correct"] for r in rs); lo, hi = wilson(k, n); d = dref.get(b)
            cf = np.array([r["CU_to_full_decision"] for r in rs if r["CU_to_full_decision"] is not None], float)
            tp = [r["tokens_prompt"] or 0 for r in rs]; tc = [r["tokens_completion"] or 0 for r in rs]
            tax = Counter(r["failure_taxonomy"] for r in rs if r["failure_taxonomy"] != "full")
            ek = Counter()
            for r in rs: ek.update(json.loads(r["error_kinds"]))
            out.append({"model": m, "tier": TIER[m], "budget_CU": b, "n": n, "k_full": k, "P_full": k / n, "CI_lo": lo, "CI_hi": hi, "P_full_D": d["full_decision_correct"] if d else None, "delta_P_full": k / n - (d["full_decision_correct"] if d else 0),
                        "k_winner": sum(r["winner_correct"] for r in rs), "k_pair": sum(r["pair_decision_correct"] for r in rs), "k_reach": sum(r["reachability_correct"] for r in rs), "k_ran_backward": sum(r["ran_backward"] for r in rs), "k_ran_reachability": sum(r["ran_reachability"] for r in rs),
                        "k_break_even_exact": sum(1 for r in rs if r["break_even_rel_error"] is not None and r["break_even_rel_error"] < 1e-6), "n_narrow_window": sum(r["narrow_window_built"] for r in rs),
                        "action_errors_total": sum(r["action_errors"] for r in rs), "runs_with_errors": sum(1 for r in rs if r["action_errors"]), "infra_retries_total": sum(r["infra_retries"] or 0 for r in rs), "driver_exceptions": 0,
                        "CU_to_full_median": float(np.median(cf)) if len(cf) else None, "CU_to_full_IQR": (f"{np.percentile(cf, 25):.0f}-{np.percentile(cf, 75):.0f}" if len(cf) else None), "CU_to_full_range": (f"{cf.min():.0f}-{cf.max():.0f}" if len(cf) else None), "n_CU_to_full": int(len(cf)),
                        "mean_spent_CU": float(np.mean([r["spent_CU"] for r in rs])), "median_spent_CU": float(np.median([r["spent_CU"] for r in rs])), "mean_unnecessary_CU_fraction": float(np.mean([r["unnecessary_CU_fraction"] for r in rs if r["unnecessary_CU_fraction"] is not None])) if any(r["unnecessary_CU_fraction"] is not None for r in rs) else None,
                        "n_api_requests": sum(r["n_api_requests"] for r in rs), "prompt_tokens": sum(tp), "completion_tokens": sum(tc), "mean_tokens_per_run": float(np.mean([a + b_ for a, b_ in zip(tp, tc)])), "median_tokens_per_run": float(np.median([a + b_ for a, b_ in zip(tp, tc)])),
                        "cached_tokens": "not recorded by the frozen driver (usage.prompt_tokens_details not stored)", "D_CU_to_full": d["CU_to_full_decision"] if d else None,
                        "failure_taxonomy": json.dumps(dict(tax)), "error_kinds": json.dumps(dict(ek)), "why_stop_kinds": json.dumps(dict(Counter(str(r["why_stop"]).split(":")[0][:40] for r in rs)))})
    return out


def tokens_by_model(rows):
    out = []
    for m in MODELS:
        rs = [r for r in rows if r["model"] == m]
        if not rs: continue
        tp = [r["tokens_prompt"] or 0 for r in rs]; tc = [r["tokens_completion"] or 0 for r in rs]
        out.append({"model": m, "tier": TIER[m], "phase": "A" if m == MODELS[2] else "B", "formal_runs": len(rs), "api_requests": sum(r["n_api_requests"] for r in rs), "prompt_tokens": sum(tp), "completion_tokens": sum(tc),
                    "cached_tokens": "not recorded", "mean_tokens_per_run": float(np.mean([a + b for a, b in zip(tp, tc)])), "median_tokens_per_run": float(np.median([a + b for a, b in zip(tp, tc)])), "infra_retries": sum(r["infra_retries"] or 0 for r in rs)})
    return out


def figures(summary, rows, dref):
    plt.rcParams.update({"font.size": 13, "axes.labelsize": 14, "axes.titlesize": 13, "legend.fontsize": 11})
    # P1: P_full vs CU, all tiers; strong at its Phase A budgets, weak at 175/225; D threshold
    fig, ax = plt.subplots(figsize=(10, 6))
    for m in MODELS:
        s = [r for r in summary if r["model"] == m]
        if not s: continue
        ax.errorbar([r["budget_CU"] for r in s], [r["P_full"] for r in s], yerr=[[max(0, r["P_full"] - r["CI_lo"]) for r in s], [max(0, r["CI_hi"] - r["P_full"]) for r in s]], marker="o", ms=10, lw=2 if m == MODELS[2] else 0, ls="-" if m == MODELS[2] else "none", capsize=5, color=COL[m], mec="black", label=f"E, {TIER[m]} (n = " + "/".join(str(r["n"]) for r in s) + ")")
    ax.axvline(D_THRESHOLD, color="black", ls="--", lw=1.5); ax.text(D_THRESHOLD + 1.5, 0.08, "D completes\nat 206 CU", fontsize=10)
    bs = sorted(dref); ax.step(bs, [dref[b]["full_decision_correct"] for b in bs], where="mid", color="black", lw=1.2, ls=":", label="D fixed-VOI (deterministic)")
    ax.set_xticks([150, 175, 200, 225, 250]); ax.set_ylim(-0.05, 1.08); ax.set_xlabel("scientific-compute budget (CU)"); ax.set_ylabel("P(full decision correct), Wilson 95 % CI")
    ax.set_title("P1  Full-decision probability vs budget by model tier (weak tiers measured at 175 and 225 CU only)"); ax.grid(color="#dddddd"); ax.legend(loc="center right")
    fig.tight_layout(); fig.savefig(FIG / "figP1_pfull_vs_CU_cross_model.png", dpi=170); plt.close(fig)
    # P2 / P3: decomposition at 175 and 225
    for b, name, title in [(175, "figP2_175CU_recovery.png", "P2  175 CU: below D's completion threshold — which components each tier recovers"), (225, "figP3_225CU_control.png", "P3  225 CU: control region where D completes — which components each tier recovers")]:
        fig, ax = plt.subplots(figsize=(10, 5.8)); comps = [("k_winner", "winner"), ("k_pair", "pair"), ("k_ran_backward", "BACKWARD run"), ("k_reach", "reachability"), ("k_full", "FULL")]
        x = np.arange(len(comps)); w = 0.26
        for i, m in enumerate(MODELS):
            s = next((r for r in summary if r["model"] == m and r["budget_CU"] == b), None)
            if not s: continue
            vals = [s[k] / s["n"] for k, _ in comps]; ax.bar(x + (i - 1) * w, vals, w, color=COL[m], edgecolor="black", label=f"{TIER[m]} (n = {s['n']})")
            for xi, v, (k, _) in zip(x + (i - 1) * w, vals, comps): ax.text(xi, v + 0.02, f"{s[k]}", ha="center", fontsize=10)
        ax.axhline(dref[b]["full_decision_correct"] if b in dref else 0, color="black", ls="--", lw=1.2, label=f"D fixed-VOI full = {dref[b]['full_decision_correct'] if b in dref else 0}")
        ax.set_xticks(x); ax.set_xticklabels([c for _, c in comps]); ax.set_ylim(0, 1.15); ax.set_ylabel("fraction of runs"); ax.set_title(title); ax.legend(loc="lower left"); ax.grid(axis="y", color="#dddddd")
        fig.tight_layout(); fig.savefig(FIG / name, dpi=170); plt.close(fig)
    # P4: CU_to_full distributions + failure taxonomy counts
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    ax = axes[0]; rng = np.random.default_rng(20260910)
    for i, m in enumerate(MODELS):
        for j, b in enumerate(PB_BUDGETS):
            v = [r["CU_to_full_decision"] for r in rows if r["model"] == m and int(r["budget_CU"]) == b and r["CU_to_full_decision"] is not None]
            xc = b + (i - 1) * 8
            if v:
                ax.plot(xc + rng.uniform(-2.5, 2.5, len(v)), v, "o", ms=6, color=COL[m], mec="black", alpha=0.8, label=TIER[m] if j == 0 else None); ax.plot([xc - 3, xc + 3], [np.median(v), np.median(v)], color="black", lw=2)
            else: ax.text(xc, 45, f"{TIER[m]}:\n0 full", ha="center", fontsize=9, color=COL[m])
    if 225 in dref: ax.plot(225, dref[225]["CU_to_full_decision"], "D", ms=11, color="black", label="D CU_to_full (225 CU)")
    ax.set_ylim(30, 235)
    for b in PB_BUDGETS: ax.plot([b - 14, b + 14], [b, b], ":", color="gray")
    ax.set_xticks(PB_BUDGETS); ax.set_xlabel("budget (CU); tiers offset for visibility"); ax.set_ylabel("CU_to_full_decision (full runs only; bar = median)"); ax.set_title("P4a  CU at which the complete decision is reached and kept"); ax.grid(color="#dddddd"); ax.legend(loc="lower right")
    ax = axes[1]; labels = []; mat = []
    tax_all = sorted({t for r in rows if r["model"] in MODELS[:2] or int(r["budget_CU"]) in PB_BUDGETS for t in [r["failure_taxonomy"]] if t != "full"})
    for m in MODELS:
        for b in PB_BUDGETS:
            rs = [r for r in rows if r["model"] == m and int(r["budget_CU"]) == b]
            if not rs: continue
            labels.append(f"{TIER[m]}\n{b} CU"); mat.append([sum(1 for r in rs if r["failure_taxonomy"] == t) for t in tax_all])
    mat = np.array(mat).T if mat else np.zeros((0, 0)); bottom = np.zeros(len(labels)); cm = plt.get_cmap("tab10")
    for i, t in enumerate(tax_all):
        ax.bar(np.arange(len(labels)), mat[i], bottom=bottom, color=cm(i % 10), edgecolor="black", label=t[:60]); bottom += mat[i]
    ax.set_xticks(np.arange(len(labels))); ax.set_xticklabels(labels); ax.set_ylabel("non-full runs"); ax.set_title("P4b  failure taxonomy of non-full runs (first failing component)"); ax.legend(fontsize=8, loc="upper right"); ax.grid(axis="y", color="#dddddd")
    fig.tight_layout(); fig.savefig(FIG / "figP4_cu_to_full_and_failure_taxonomy.png", dpi=170); plt.close(fig)


def main(repo):
    gate = validate_against_frozen(); assert gate["gate"] == "PASS", gate
    rows, dref = collect(); rows.sort(key=lambda r: (r["model"], r["budget_CU"], r["run_index"]))
    pb = [r for r in rows if r["phase"] == "B"]
    with open(DATA / "discover_boundary_c1_phase_b_runs.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(pb)
    summary = summarise(rows, dref)
    with open(DATA / "discover_boundary_c1_phase_b_summary.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(summary[0].keys())); w.writeheader(); w.writerows(summary)
    tok = tokens_by_model(rows)
    with open(DATA / "discover_boundary_c1_phase_b_tokens.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(tok[0].keys())); w.writeheader(); w.writerows(tok)
    # secondary: Fisher exact between tiers at each budget, and interaction via difference of differences
    sec = {}
    for b in PB_BUDGETS:
        cell = {m: next((r for r in summary if r["model"] == m and r["budget_CU"] == b), None) for m in MODELS}
        for i, j in [(0, 1), (1, 2), (0, 2)]:
            a, c = cell[MODELS[i]], cell[MODELS[j]]
            if a and c: sec[f"fisher_{TIER[MODELS[i]]}_vs_{TIER[MODELS[j]]}_{b}"] = float(stats.fisher_exact([[a["k_full"], a["n"] - a["k_full"]], [c["k_full"], c["n"] - c["k_full"]]])[1])
    for m in MODELS:
        a = next((r for r in summary if r["model"] == m and r["budget_CU"] == 175), None); c = next((r for r in summary if r["model"] == m and r["budget_CU"] == 225), None)
        if a and c: sec[f"budget_effect_{TIER[m]}_225_minus_175"] = c["P_full"] - a["P_full"]
    figures(summary, rows, dref)
    meta = {"family": "DISCOVER-BOUNDARY-C1 Phase B", "generated_utc": datetime.now(timezone.utc).isoformat(), "validation_gate": gate, "phase_b_runs": len(pb), "phase_b_by_cell": {f"{TIER[r['model']]}_{r['budget_CU']}": r["n"] for r in summary if r["model"] in MODELS[:2]},
            "secondary_stats": sec, "python": sys.version, "platform": platform.platform(), "packages": {p: __import__(p).__version__ for p in ("numpy", "scipy", "matplotlib", "openai")},
            "hashchecks": [json.loads(Path(p).read_text(encoding="utf-8")) for p in sorted(glob.glob(str(OUT / "metadata" / "hashcheck_*phaseB*.json")))],
            "interrupted_run_dirs_excluded": [str(Path(d).relative_to(ROOT)) for d in glob.glob(str(OUT / "runs" / "*" / "traces" / "anonymous" / "*")) if not (Path(d) / "trace.json").exists()],
            "code_sha256": {f: hashlib.sha256((ROOT / f).read_bytes()).hexdigest() for f in ("discover/formal_e.py", "discover/boundary_c1_runner.py", "discover/boundary_c1_metrics.py", "discover/boundary_c1_analysis.py", "discover/boundary_c1_phase_b_analysis.py", "DISCOVER_SCORER_V1.py")}}
    (DATA / "discover_boundary_c1_phase_b_metadata.json").write_text(json.dumps(meta, indent=1, default=str), encoding="utf-8")
    for r in summary: print(f"{r['tier']:6s} B={r['budget_CU']} full {r['k_full']}/{r['n']} [{r['CI_lo']:.2f},{r['CI_hi']:.2f}] win {r['k_winner']} pair {r['k_pair']} bw {r['k_ran_backward']} reach {r['k_reach']} BE {r['k_break_even_exact']} nw {r['n_narrow_window']} err {r['action_errors_total']} CUfull med {r['CU_to_full_median']} IQR {r['CU_to_full_IQR']} spent {r['mean_spent_CU']:.0f} req {r['n_api_requests']} tok {r['prompt_tokens']/1e6:.2f}M/{r['completion_tokens']/1e6:.2f}M | tax {r['failure_taxonomy']}")
    print(json.dumps(sec, indent=1))
    if repo:
        for f in DATA.glob("discover_boundary_c1_phase_b_*"): shutil.copy(f, repo / "data" / f.name)
        for f in FIG.glob("figP*.png"): shutil.copy(f, repo / "figures" / "discover_boundary_c1" / f.name)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--repo", default=None); a = ap.parse_args(); main(Path(a.repo) if a.repo else None)
