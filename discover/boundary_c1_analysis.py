"""
DISCOVER-BOUNDARY-C1 analysis: per-run table, per-budget summary with Wilson CIs, Delta P_full vs D, efficiency
(CU_to_full, spent CU), historical V1 points as a separate series, figures A-D. Reads traces only; frozen scorer used
unchanged for all V1 metrics; boundary_c1_metrics for CU_to_full. Bootstrap seed fixed (20260908).
Usage: python discover/boundary_c1_analysis.py [--repo <Catalyst-Essay root>]  (writes data/ + figures/ into harness DISCOVER_BOUNDARY_C1/ and, if --repo, copies there)
"""
from __future__ import annotations
import argparse, csv, glob, hashlib, json, math, platform, shutil, sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
from scipy import stats
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "discover"))
import DISCOVER_SCORER_V1 as S
from boundary_c1_metrics import cu_to_full, validate_against_frozen
OUT = ROOT / "DISCOVER_BOUNDARY_C1"; DATA = OUT / "data"; FIG = OUT / "figures"; DATA.mkdir(exist_ok=True); FIG.mkdir(exist_ok=True)
BUDGETS = [150, 175, 200, 225, 250]
TIER = {"gpt-5.4-nano-2026-03-17": "nano", "gpt-5.4-mini-2026-03-17": "mini", "gpt-5.5-2026-04-23": "strong"}
RNG = np.random.default_rng(20260908)


def wilson(k, n, z=1.959963984540054):
    if n == 0: return (float("nan"), float("nan"))
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def score_run(p: Path, family: str) -> dict:
    t = json.loads(p.read_text(encoding="utf-8")); sc = S.score_trace(p); c = cu_to_full(p)
    meta = t.get("metadata", {}); lm = t.get("llm_meta", {})
    return {"family": family, "trace_dir": str(p.parent.relative_to(ROOT)), "model": t.get("model_requested", "D_fixed_voi" if t["policy"] == "D_fixed_voi" else None), "response_model": meta.get("response_model"),
            "policy": t["policy"], "variant": t.get("task_variant"), "budget_CU": t["budget_CU"], "run_index": t.get("run_index", t.get("seed")), "started_utc": t.get("started_utc"), "finished_utc": meta.get("finished_utc"),
            "steps": sc["steps"], "spent_CU": sc["spent_CU"], "winner": sc["winner"], "winner_correct": int(sc["winner_correct"]), "pair_decision_correct": int(sc["pair_decision_correct"]), "reachability_correct": int(sc["reachability_correct"]),
            "full_decision_correct": int(sc["full_decision_correct"]), "CU_to_first_correct_winner": sc["CU_to_first_correct_winner"], "CU_to_stable_correct_winner": sc["CU_to_stable_correct_winner"], "CU_to_full_decision": c["CU_to_full_decision"],
            "unnecessary_CU_fraction": sc["unnecessary_CU_fraction"], "decision_regret_USD_t": sc["decision_regret_USD_t"], "break_even_estimate": sc["break_even_estimate"], "break_even_rel_error": sc["break_even_rel_error"],
            "action_errors": sc["action_errors"], "infra_retries": lm.get("infra_retries"), "malformed_turns": lm.get("malformed_turns"), "tokens_prompt": (lm.get("tokens") or {}).get("prompt"), "tokens_completion": (lm.get("tokens") or {}).get("completion"),
            "why_stop": sc["why_stop"], "narrow_window_built": int(any(s.get("chosen_action") == "BUILD_PROCESS_WINDOW" and (s.get("chosen_args") or {}).get("bounds") for s in t["steps"]))}


def collect() -> tuple[list[dict], dict]:
    rows = []
    for p in glob.glob(str(OUT / "runs" / "*" / "traces" / "anonymous" / "*" / "trace.json")): rows.append(score_run(Path(p), "C1"))
    for p in glob.glob(str(OUT / "smoke" / "*" / "traces" / "anonymous" / "*" / "trace.json")): rows.append(score_run(Path(p), "smoke"))
    for p in glob.glob(str(ROOT / "DISCOVER_FORMAL_RUNS_V1" / "traces" / "anonymous" / "E_llm_agent_anonymous_B2[05]0_*" / "trace.json")): r = score_run(Path(p), "V1_historical"); r["model"] = "gpt-5.5-2026-04-23"; rows.append(r)
    for p in glob.glob(str(ROOT / "DISCOVER_CROSS_MODEL_V1" / "*" / "traces" / "anonymous" / "E_llm_agent_anonymous_B2[05]0_*" / "trace.json")): rows.append(score_run(Path(p), "V1_historical"))
    dref = {}
    for p in list(glob.glob(str(OUT / "D_reference" / "traces" / "anonymous" / "*" / "trace.json"))) + list(glob.glob(str(ROOT / "DISCOVER_FORMAL_RUNS_V1" / "traces" / "anonymous" / "D_fixed_voi_anon_B2[05]0_*" / "trace.json"))):
        r = score_run(Path(p), "D_reference" if "BOUNDARY" in p else "D_frozen_V1"); dref[int(r["budget_CU"])] = r
    return rows, dref


def summarise(rows, dref, family="C1"):
    out = []
    for model in sorted({r["model"] for r in rows if r["family"] == family}):
        for b in BUDGETS:
            rs = [r for r in rows if r["family"] == family and r["model"] == model and int(r["budget_CU"]) == b]
            if not rs: continue
            clean = [r for r in rs if (r["infra_retries"] or 0) == 0]
            n = len(rs); k = sum(r["full_decision_correct"] for r in rs); lo, hi = wilson(k, n); d = dref.get(b)
            pd_ = d["full_decision_correct"] if d else float("nan")
            cf = [r["CU_to_full_decision"] for r in rs if r["CU_to_full_decision"] is not None]
            both = bool(d and d["full_decision_correct"] == 1)
            rec = {"model": model, "tier": TIER.get(model, model), "family": family, "budget_CU": b, "n": n, "k_full": k, "P_full_E": k / n, "CI_lo": lo, "CI_hi": hi, "P_full_D": pd_, "delta_P_full": k / n - pd_, "delta_CI_lo": lo - pd_, "delta_CI_hi": hi - pd_,
                   "k_winner": sum(r["winner_correct"] for r in rs), "k_pair": sum(r["pair_decision_correct"] for r in rs), "k_reach": sum(r["reachability_correct"] for r in rs),
                   "mean_spent_CU": float(np.mean([r["spent_CU"] for r in rs])), "median_spent_CU": float(np.median([r["spent_CU"] for r in rs])),
                   "mean_CU_to_full": float(np.mean(cf)) if cf else None, "median_CU_to_full": float(np.median(cf)) if cf else None, "n_CU_to_full": len(cf),
                   "mean_CU_to_stable": float(np.mean([r["CU_to_stable_correct_winner"] for r in rs if r["CU_to_stable_correct_winner"] is not None])) if any(r["CU_to_stable_correct_winner"] is not None for r in rs) else None,
                   "mean_unnecessary_CU_fraction": float(np.mean([r["unnecessary_CU_fraction"] for r in rs if r["unnecessary_CU_fraction"] is not None])),
                   "mean_action_errors": float(np.mean([r["action_errors"] for r in rs])), "mean_regret_USD_t": float(np.mean([min(r["decision_regret_USD_t"], 1e3) for r in rs])),
                   "n_break_even_exact": sum(1 for r in rs if r["break_even_rel_error"] is not None and r["break_even_rel_error"] < 1e-6), "n_narrow_window": sum(r["narrow_window_built"] for r in rs),
                   "n_infra_retry_runs": sum(1 for r in rs if (r["infra_retries"] or 0) > 0), "k_full_clean": sum(r["full_decision_correct"] for r in clean), "n_clean": len(clean),
                   "D_spent_CU": d["spent_CU"] if d else None, "D_CU_to_full": d["CU_to_full_decision"] if d else None, "D_CU_to_stable": d["CU_to_stable_correct_winner"] if d else None,
                   "both_full_correct_regime": both,
                   "delta_CU_full_D_minus_E_mean": (d["CU_to_full_decision"] - float(np.mean(cf))) if (both and cf and d["CU_to_full_decision"] is not None) else None,
                   "relative_CU_full_saving": ((d["CU_to_full_decision"] - float(np.mean(cf))) / d["CU_to_full_decision"]) if (both and cf and d["CU_to_full_decision"]) else None,
                   "relative_total_CU_saving": ((d["spent_CU"] - float(np.mean([r["spent_CU"] for r in rs]))) / d["spent_CU"]) if d else None,
                   "comparison_label": "same-quality efficiency" if both else "decision-completion advantage (D incomplete)"}
            if both and cf and d["CU_to_full_decision"] is not None:
                bs = np.array([d["CU_to_full_decision"] - RNG.choice(cf, len(cf)).mean() for _ in range(10000)]); rec["delta_CU_full_boot_lo"], rec["delta_CU_full_boot_hi"] = float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))
            out.append(rec)
    return out


def classify(summary, model="gpt-5.5-2026-04-23"):
    s = {r["budget_CU"]: r for r in summary if r["model"] == model and r["family"] == "C1"}
    if 200 not in s: return {"class": "NOT RUN"}
    k200 = s[200]["k_full"]; lo200 = s[200]["CI_lo"]
    # pre-registered substantive threshold: k >= 14/20, stated in the preregistration as equivalent to a Wilson lower bound >= 0.48;
    # after addendum A1 the 200-CU cell has n < 20, so the lower-bound form is the only evaluable form (reported as reduced-n)
    replicated = lo200 >= 0.48
    pos = [b for b in BUDGETS if b in s and s[b]["delta_P_full"] > 0]
    adjacent = any(BUDGETS[i] in pos and BUDGETS[i + 1] in pos for i in range(len(BUDGETS) - 1))
    if not replicated: cls = "NO ADAPTIVE REGION"
    elif adjacent and pos != [200]: cls = "COHERENT LOCAL REGION"
    elif pos == [200] or (len(pos) == 1): cls = "ISOLATED SPIKE"
    else: cls = "REPLICATED-200 (non-adjacent positives)"
    return {"class": cls, "k200": k200, "n200": s[200]["n"], "wilson_lo_200": lo200, "threshold_form": "Wilson lower bound >= 0.48 (pre-registered equivalent of 14/20)", "positive_budgets": pos, "adjacent_positive": adjacent, "delta": {b: s[b]["delta_P_full"] for b in BUDGETS if b in s}}


def figures(rows, summary, dref):
    plt.rcParams.update({"font.size": 13, "axes.labelsize": 14, "axes.titlesize": 14, "legend.fontsize": 11})
    models = [m for m in ["gpt-5.4-nano-2026-03-17", "gpt-5.4-mini-2026-03-17", "gpt-5.5-2026-04-23"] if any(r["model"] == m and r["family"] == "C1" for r in rows)]
    col = {"gpt-5.4-nano-2026-03-17": "#d62728", "gpt-5.4-mini-2026-03-17": "#ff7f0e", "gpt-5.5-2026-04-23": "#1f77b4"}
    # Figure A: Delta P_full vs CU
    fig, ax = plt.subplots(figsize=(10, 6))
    for m in models:
        s = [r for r in summary if r["model"] == m and r["family"] == "C1"]; x = [r["budget_CU"] for r in s]; y = [r["delta_P_full"] for r in s]
        ax.errorbar(x, y, yerr=[[max(0.0, r["delta_P_full"] - r["delta_CI_lo"]) for r in s], [max(0.0, r["delta_CI_hi"] - r["delta_P_full"]) for r in s]], marker="o", ms=9, lw=2.2, capsize=5, color=col[m], mec="black", label=f"{TIER[m]} — C1 confirmatory (n = " + "/".join(str(r["n"]) for r in s) + " at " + "/".join(str(r["budget_CU"]) for r in s) + " CU)")
        hist = [r for r in summary if r["model"] == m and r["family"] == "V1_historical"]
        if hist: ax.plot([r["budget_CU"] for r in hist], [r["delta_P_full"] for r in hist], "s", ms=9, color=col[m], alpha=0.35, mec="black", label=f"{TIER[m]} — frozen V1 historical (n = 5), not pooled")
    ax.axhline(0, color="black", lw=1); ax.set_xticks(BUDGETS); ax.set_xlabel("scientific-compute budget (CU)"); ax.set_ylabel("ΔP_full = P_full(E) − P_full(D)"); ax.set_ylim(-1.05, 1.15)
    for b in BUDGETS:
        d = dref.get(b); ax.text(b, -1.0, f"D: {'full' if d and d['full_decision_correct'] else 'incomplete'}", ha="center", fontsize=10)
    ax.set_title("A  ΔP_full = P_full(E) − P_full(D) vs budget (D deterministic; CI = Wilson interval of E shifted by P_full(D))", fontsize=12)
    ax.grid(color="#dddddd"); ax.legend(loc="upper right"); fig.tight_layout(); fig.savefig(FIG / "figA_delta_pfull_vs_CU.png", dpi=170); plt.close(fig)
    # Figure B: strong efficiency
    s = [r for r in summary if r["model"] == "gpt-5.5-2026-04-23" and r["family"] == "C1"]
    fig, ax = plt.subplots(figsize=(10, 6))
    vals = [100 * r["relative_CU_full_saving"] for r in s if r["both_full_correct_regime"] and r["relative_CU_full_saving"] is not None]
    lims = [100 * r["delta_CU_full_boot_lo"] / r["D_CU_to_full"] for r in s if r.get("delta_CU_full_boot_lo") is not None] + [100 * r["delta_CU_full_boot_hi"] / r["D_CU_to_full"] for r in s if r.get("delta_CU_full_boot_hi") is not None]
    ymin = min([0.0] + vals + lims) - 6; ymax = max([0.0] + vals + lims) + 12; ax.set_ylim(ymin, ymax)
    for r in s:
        if r["both_full_correct_regime"] and r["relative_CU_full_saving"] is not None:
            lo, hi = r.get("delta_CU_full_boot_lo"), r.get("delta_CU_full_boot_hi"); yv = 100 * r["relative_CU_full_saving"]
            err = [[max(0.0, yv - 100 * lo / r["D_CU_to_full"])], [max(0.0, 100 * hi / r["D_CU_to_full"] - yv)]] if lo is not None else None
            ax.errorbar([r["budget_CU"]], [yv], yerr=err, marker="o", ms=11, color="#1f77b4", mec="black", capsize=5, lw=2)
            ax.text(r["budget_CU"], (hi * 100 / r["D_CU_to_full"] if hi is not None else yv) + 1.5 + (2.5 if r["budget_CU"] == 250 else 0), f"D {r['D_CU_to_full']:.0f} → E {r['mean_CU_to_full']:.0f} CU (n = {r['n_CU_to_full']})", ha="center", fontsize=10)
        else:
            ax.plot([r["budget_CU"]], [0], marker="x", ms=12, color="#888888", mew=2)
            ax.text(r["budget_CU"], ymax - 1, "D incomplete:\ndecision-completion\nadvantage, not efficiency", ha="center", va="top", fontsize=9, color="#555555")
    ax.axhline(0, color="black", lw=1); ax.set_xticks(BUDGETS); ax.set_xlabel("scientific-compute budget (CU)"); ax.set_ylabel("relative CU_to_full saving of E vs D (%)")
    ax.set_title("B  Strong model, same-quality regime only: relative CU_to_full saving of E vs D (positive = E earlier; bootstrap 95 % CI)", fontsize=11); ax.grid(color="#dddddd")
    fig.tight_layout(); fig.savefig(FIG / "figB_strong_efficiency.png", dpi=170); plt.close(fig)
    # Figure C: P_full vs CU with Wilson
    fig, ax = plt.subplots(figsize=(10, 6))
    for m in models:
        s = [r for r in summary if r["model"] == m and r["family"] == "C1"]
        ax.errorbar([r["budget_CU"] for r in s], [r["P_full_E"] for r in s], yerr=[[max(0.0, r["P_full_E"] - r["CI_lo"]) for r in s], [max(0.0, r["CI_hi"] - r["P_full_E"]) for r in s]], marker="o", ms=9, lw=2, capsize=5, color=col[m], mec="black", label=f"E, {TIER[m]} (C1, n = 20)")
    ax.step([b for b in BUDGETS if b in dref], [dref[b]["full_decision_correct"] for b in BUDGETS if b in dref], where="mid", color="black", lw=2, ls="--", label="D fixed-VOI (deterministic)")
    ax.set_xticks(BUDGETS); ax.set_ylim(-0.05, 1.08); ax.set_xlabel("scientific-compute budget (CU)"); ax.set_ylabel("P(full decision correct)"); ax.set_title("C  supporting: P_full vs budget (Wilson 95 % CI)"); ax.grid(color="#dddddd"); ax.legend(loc="lower right")
    fig.tight_layout(); fig.savefig(FIG / "figC_pfull_vs_CU.png", dpi=170); plt.close(fig)
    # Figure D: CU_to_full distributions (strong)
    fig, ax = plt.subplots(figsize=(10, 6))
    for i, b in enumerate(BUDGETS):
        v = [r["CU_to_full_decision"] for r in rows if r["family"] == "C1" and r["model"] == "gpt-5.5-2026-04-23" and int(r["budget_CU"]) == b and r["CU_to_full_decision"] is not None]
        if v:
            xs = b + RNG.uniform(-6, 6, len(v)); ax.plot(xs, v, "o", ms=7, color="#1f77b4", mec="black", alpha=0.8)
            ax.plot([b - 9, b + 9], [np.median(v), np.median(v)], color="black", lw=2)
        d = dref.get(b)
        if d and d["CU_to_full_decision"] is not None: ax.plot(b, d["CU_to_full_decision"], "D", ms=11, color="#d62728", mec="black", label="D fixed-VOI CU_to_full" if not ax.get_legend_handles_labels()[1] else None)
        ax.plot([b - 10, b + 10], [b, b], ":", color="gray", lw=1)
    ax.set_xticks(BUDGETS); ax.set_xlabel("scientific-compute budget (CU)"); ax.set_ylabel("CU_to_full_decision (E runs; bar = median)"); ax.set_title("D  strong model: CU_to_full_decision per run (bar = median; dotted = budget; red = D)", fontsize=13); ax.grid(color="#dddddd"); ax.legend(loc="upper left")
    fig.tight_layout(); fig.savefig(FIG / "figD_cu_to_full_distribution.png", dpi=170); plt.close(fig)


def main(repo: Path | None):
    gate = validate_against_frozen(); assert gate["gate"] == "PASS", gate
    rows, dref = collect()
    rows.sort(key=lambda r: (r["family"], r["model"] or "", r["budget_CU"], r["run_index"] or 0))
    keys = list(rows[0].keys())
    with open(DATA / "discover_boundary_c1_runs.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); w.writerows(rows)
    summary = summarise(rows, dref, "C1") + summarise(rows, dref, "V1_historical")
    skeys = sorted({k for r in summary for k in r}, key=lambda k: (k not in ("model", "tier", "family", "budget_CU", "n", "k_full", "P_full_E", "CI_lo", "CI_hi", "P_full_D", "delta_P_full", "delta_CI_lo", "delta_CI_hi"), k))
    with open(DATA / "discover_boundary_c1_summary.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=skeys); w.writeheader(); w.writerows(summary)
    with open(DATA / "discover_boundary_c1_D_reference.csv", "w", newline="", encoding="utf-8") as f:
        dk = ["budget_CU", "family", "trace_dir", "full_decision_correct", "winner_correct", "pair_decision_correct", "reachability_correct", "spent_CU", "CU_to_stable_correct_winner", "CU_to_full_decision", "unnecessary_CU_fraction", "steps", "why_stop"]
        w = csv.DictWriter(f, fieldnames=dk, extrasaction="ignore"); w.writeheader(); [w.writerow(dref[b]) for b in sorted(dref)]
    cls = {m: classify(summary, m) for m in sorted({r["model"] for r in rows if r["family"] == "C1"})}
    # secondary stats: exact binomial at 200 (strong), logistic on budget
    sec = {}
    for m in cls:
        rs = [r for r in rows if r["family"] == "C1" and r["model"] == m]
        s200 = [r for r in rs if int(r["budget_CU"]) == 200]
        if s200: sec[m] = {"binom_200_p_vs_D0": float(stats.binomtest(sum(r["full_decision_correct"] for r in s200), len(s200), 0.0 + 1e-9, alternative="greater").pvalue) if dref.get(200, {}).get("full_decision_correct") == 0 else None}
        x = np.array([[1.0, (r["budget_CU"] - 200) / 25] for r in rs]); y = np.array([r["full_decision_correct"] for r in rs], float)
        if 0 < y.sum() < len(y):
            from scipy.optimize import minimize
            nll = lambda b: float(np.sum(np.logaddexp(0, x @ b) - y * (x @ b))); res = minimize(nll, np.zeros(2)); sec.setdefault(m, {})["logit_slope_per_25CU"] = float(res.x[1])
        else: sec.setdefault(m, {})["logit_slope_per_25CU"] = "separation (all equal)"
    figures(rows, summary, dref)
    interrupted = [str(Path(d).relative_to(ROOT)) for d in glob.glob(str(OUT / "runs" / "*" / "traces" / "anonymous" / "*")) if not (Path(d) / "trace.json").exists()]
    meta = {"family": "DISCOVER-BOUNDARY-C1", "generated_utc": datetime.now(timezone.utc).isoformat(), "validation_gate": gate, "classification": cls, "secondary_stats": sec,
            "interrupted_run_dirs_excluded": interrupted, "design_addendum": "A1 (2026-09-09): 150/200/250 stopped early by user for cost; 175/225 to 20; see docs/DISCOVER_BOUNDARY_C1_ADDENDUM_A1.md",
            "n_rows": {fam: sum(1 for r in rows if r["family"] == fam) for fam in {r["family"] for r in rows}}, "python": sys.version, "platform": platform.platform(),
            "packages": {p: __import__(p).__version__ for p in ("numpy", "scipy", "matplotlib", "openai")},
            "hashchecks": [json.loads(Path(p).read_text(encoding="utf-8")) for p in sorted(glob.glob(str(OUT / "metadata" / "hashcheck_*.json")))],
            "code_sha256": {f: hashlib.sha256((ROOT / f).read_bytes()).hexdigest() for f in ("discover/formal_e.py", "discover/boundary_c1_runner.py", "discover/boundary_c1_metrics.py", "discover/boundary_c1_analysis.py", "DISCOVER_SCORER_V1.py")}}
    (DATA / "discover_boundary_c1_metadata.json").write_text(json.dumps(meta, indent=1, default=str), encoding="utf-8")
    print(json.dumps({"classification": cls, "secondary": sec}, indent=1, default=str))
    for r in summary:
        if r["family"] == "C1": print(f"{r['tier']:6s} B={r['budget_CU']} k={r['k_full']}/{r['n']} P={r['P_full_E']:.2f} [{r['CI_lo']:.2f},{r['CI_hi']:.2f}] D={r['P_full_D']} dP={r['delta_P_full']:+.2f} spent={r['mean_spent_CU']:.0f} CUfull={r['mean_CU_to_full']} Dfull={r['D_CU_to_full']} unnec={r['mean_unnecessary_CU_fraction']:.2f} err={r['mean_action_errors']:.2f} nw={r['n_narrow_window']} retries={r['n_infra_retry_runs']}")
    if repo:
        (repo / "data").mkdir(exist_ok=True); (repo / "figures" / "discover_boundary_c1").mkdir(parents=True, exist_ok=True)
        for f in DATA.iterdir(): shutil.copy(f, repo / "data" / f.name)
        for f in FIG.iterdir(): shutil.copy(f, repo / "figures" / "discover_boundary_c1" / f.name)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--repo", default=None); a = ap.parse_args()
    main(Path(a.repo) if a.repo else None)
