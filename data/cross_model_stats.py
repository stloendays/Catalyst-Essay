"""
Cross-model statistical analysis (DISCOVER V1, PHASE E-2 continuation, 2026-09-07).

Reads ONLY DISCOVER_CROSS_MODEL_V1/scores/per_trace_scores.json (frozen-scorer output, unchanged) and writes
CROSS_MODEL_STATS_V1.csv + CROSS_MODEL_STATS_V1.md. No frozen file is touched; no trace is re-scored or re-run.

Tests: Wilson 95 % CI (per cell n=5, pooled n=35, budget strata), two-sided Fisher exact for tier pairs, Cochran-Armitage trend
across tiers (nano<mini<5.5) and across budgets within a tier, logistic regression (nano vs mini only: gpt-5.5 is 70/70 -> separation),
Mann-Whitney U + fixed-seed bootstrap means for continuous metrics, and the pre-registered "Agent-specific Go" (E vs D, >=4/5 runs at
the same budget in >=2 tiers). n=5 per cell: the smallest two-cell difference Fisher can call at alpha=0.05 is 5/5 vs <=1/5.
"""
from __future__ import annotations
import csv, json, math
from collections import defaultdict
from pathlib import Path
import numpy as np
from scipy import stats, optimize

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "DISCOVER_CROSS_MODEL_V1" / "scores" / "per_trace_scores.json"
TIERS = ["gpt-5.4-nano-2026-03-17", "gpt-5.4-mini-2026-03-17", "gpt-5.5-2026-04-23"]
SHORT = {TIERS[0]: "nano", TIERS[1]: "mini", TIERS[2]: "5.5"}
BUDGETS = [200, 250, 300, 500, 800, 1200, 2000]
BIN = [("full_decision_correct", "P(full)"), ("winner_correct", "P(win)"), ("pair_decision_correct", "P(pair)"), ("reachability_correct", "P(reach)")]
CONT = ["unnecessary_CU_fraction", "CU_to_stable_correct_winner", "spent_CU", "action_errors", "decision_regret_USD_t", "break_even_rel_error"]
RNG = np.random.default_rng(20260907)
rows_out: list[dict] = []
PAIRS = [(0, 1), (1, 2), (0, 2)]


def wilson(k, n, z=1.959964):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def ca_trend(ks, ns, scores):
    """Cochran-Armitage trend test; returns (Z, two-sided p)."""
    ks, ns, s = np.array(ks, float), np.array(ns, float), np.array(scores, float)
    N = ns.sum()
    R = ks.sum()
    if R == 0 or R == N:
        return (float("nan"), float("nan"))
    pbar = R / N
    sbar = (s * ns).sum() / N
    T = (ks * (s - sbar)).sum()
    V = pbar * (1 - pbar) * (ns * (s - sbar) ** 2).sum()
    Z = T / math.sqrt(V)
    return (Z, 2 * stats.norm.sf(abs(Z)))


def logit_fit(X, y):
    """Plain MLE logistic regression with Wald SE from the observed Hessian (statsmodels not installed)."""
    X = np.asarray(X, float)
    y = np.asarray(y, float)

    def nll(b):
        z = X @ b
        return float(np.sum(np.logaddexp(0, z) - y * z))

    def grad(b):
        p = 1 / (1 + np.exp(-(X @ b)))
        return X.T @ (p - y)

    r = optimize.minimize(nll, np.zeros(X.shape[1]), jac=grad, method="BFGS")
    p = 1 / (1 + np.exp(-(X @ r.x)))
    W = p * (1 - p)
    H = (X * W[:, None]).T @ X
    se = np.sqrt(np.diag(np.linalg.inv(H)))
    z = r.x / se
    return r.x, se, 2 * stats.norm.sf(abs(z)), -r.fun


def add(section, **kv):
    rows_out.append({"section": section, **kv})


def fmt(x, nd=3):
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "-"
    return f"{x:.{nd}f}" if isinstance(x, float) else str(x)


def isnum(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def main():
    data = json.load(open(SRC, encoding="utf-8"))
    E = [r for r in data if r["policy"] == "E_llm_agent"]
    D = {(r["variant"], int(r["budget_CU"])): r for r in data if r["policy"] == "D_fixed_voi"}
    assert len(E) == 210 and len(D) == 14, (len(E), len(D))
    md = ["# DISCOVER V1 cross-model statistics (2026-09-07)", "",
          "Input: `DISCOVER_CROSS_MODEL_V1/scores/per_trace_scores.json` (frozen scorer V1, unchanged; 210 policy-E runs = 3 tiers x 7 budgets x 5 runs x "
          "{anonymous, named}; policy D = 7 budgets x 2 variants, deterministic). Script `discover/cross_model_stats.py`; table `CROSS_MODEL_STATS_V1.csv`. "
          "Frozen-hash check on 2026-09-07 before this analysis: 15/15 match; 140/140 new traces present, none missing or duplicated; no case was re-run.", ""]

    # ---------- 1. Wilson CIs ----------
    md += ["## 1. Binomial outcomes with Wilson 95 % CI", "",
           "Per-cell n = 5: the CI of an observed 5/5 is [0.57, 1.00] and of 0/5 is [0.00, 0.43]; per-cell differences smaller than 5/5 vs <= 1/5 are not "
           "resolvable (Fisher two-sided p = 0.048 for 5/5 vs 1/5, 0.008 for 5/5 vs 0/5). Inference therefore rests on the pooled 35-run and budget-stratum rows.", ""]
    for variant in ["anonymous", "named"]:
        md += [f"### {variant}", "", "| tier | stratum | n | " + " | ".join(lab + " [95 % CI]" for _, lab in BIN) + " |", "|---|---|---|" + "---|" * len(BIN)]
        for tier in TIERS:
            sub = [r for r in E if r["model"] == tier and r["variant"] == variant]
            strata = [("pooled", sub), ("<=300 CU", [r for r in sub if r["budget_CU"] <= 300]), (">=500 CU", [r for r in sub if r["budget_CU"] >= 500])] + \
                     [(f"{b} CU", [r for r in sub if int(r["budget_CU"]) == b]) for b in BUDGETS]
            for name, s in strata:
                cells = []
                for key, lab in BIN:
                    k = sum(bool(r[key]) for r in s)
                    n = len(s)
                    lo, hi = wilson(k, n)
                    cells.append(f"{k}/{n} = {k/n:.2f} [{lo:.2f}, {hi:.2f}]")
                    add("wilson", variant=variant, tier=SHORT[tier], stratum=name, metric=lab, k=k, n=n, p=k / n, ci_lo=lo, ci_hi=hi)
                md.append(f"| {SHORT[tier]} | {name} | {len(s)} | " + " | ".join(cells) + " |")
        md.append("")

    # ---------- 2. Fisher exact ----------
    md += ["## 2. Tier-pair comparisons (two-sided Fisher exact)", "",
           "| variant | stratum | metric | nano vs mini | mini vs 5.5 | nano vs 5.5 |", "|---|---|---|---|---|---|"]
    for variant in ["anonymous", "named"]:
        for sname, cond in [("pooled", lambda r: True), ("<=300 CU", lambda r: r["budget_CU"] <= 300), (">=500 CU", lambda r: r["budget_CU"] >= 500)]:
            for key, lab in BIN:
                cells = []
                for i, j in PAIRS:
                    a = [r for r in E if r["model"] == TIERS[i] and r["variant"] == variant and cond(r)]
                    b = [r for r in E if r["model"] == TIERS[j] and r["variant"] == variant and cond(r)]
                    ka, kb = sum(bool(r[key]) for r in a), sum(bool(r[key]) for r in b)
                    _, p = stats.fisher_exact([[ka, len(a) - ka], [kb, len(b) - kb]])
                    cells.append(f"{ka}/{len(a)} vs {kb}/{len(b)}, p = {p:.3g}")
                    add("fisher", variant=variant, stratum=sname, metric=lab, pair=f"{SHORT[TIERS[i]]} vs {SHORT[TIERS[j]]}", k1=ka, n1=len(a), k2=kb, n2=len(b), p=p)
                md.append(f"| {variant} | {sname} | {lab} | " + " | ".join(cells) + " |")
    md.append("")

    # ---------- 3. Trend tests ----------
    md += ["## 3. Trend tests (Cochran-Armitage)", "",
           "Across tiers (scores nano = 0, mini = 1, 5.5 = 2; pooled 35 per tier) and across budgets within a tier (score = rank of budget, 5 per budget).", "",
           "| variant | metric | tier trend Z (p) | budget trend nano Z (p) | budget trend mini Z (p) | budget trend 5.5 Z (p) |", "|---|---|---|---|---|---|"]
    for variant in ["anonymous", "named"]:
        for key, lab in BIN:
            ks = [sum(bool(r[key]) for r in E if r["model"] == t and r["variant"] == variant) for t in TIERS]
            Z, p = ca_trend(ks, [35] * 3, [0, 1, 2])
            add("trend_tier", variant=variant, metric=lab, Z=Z, p=p, counts=str(ks))
            cells = [f"{fmt(Z, 2)} ({fmt(p, 3)})"]
            for t in TIERS:
                kb = [sum(bool(r[key]) for r in E if r["model"] == t and r["variant"] == variant and int(r["budget_CU"]) == b) for b in BUDGETS]
                Zb, pb = ca_trend(kb, [5] * 7, list(range(7)))
                add("trend_budget", variant=variant, metric=lab, tier=SHORT[t], Z=Zb, p=pb, counts=str(kb))
                cells.append(f"{fmt(Zb, 2)} ({fmt(pb, 3)})")
            md.append(f"| {variant} | {lab} | " + " | ".join(cells) + " |")
    md += ["", "Z is undefined (-) when a tier is 35/35 or 0/35 (no variance)."]

    # ---------- 4. Logistic regression ----------
    md += ["", "## 4. Logistic regression, nano vs mini only (gpt-5.5 is 70/70 correct -> complete separation, excluded)", "",
           "Model: logit P(outcome) = b0 + b1[mini] + b2 log2(budget/200) + b3[named]; 140 runs. Wald SE from the observed information matrix.", "",
           "| outcome | mini vs nano OR [95 % CI] (p) | per budget doubling OR [95 % CI] (p) | named vs anonymous OR [95 % CI] (p) |", "|---|---|---|---|"]
    sub = [r for r in E if r["model"] in TIERS[:2]]
    X = np.array([[1.0, r["model"] == TIERS[1], math.log2(r["budget_CU"] / 200), r["variant"] == "named"] for r in sub], float)
    for key, lab in BIN:
        y = np.array([bool(r[key]) for r in sub], float)
        b, se, p, ll = logit_fit(X, y)
        cells = []
        for i, nm in [(1, "mini"), (2, "budget_doubling"), (3, "named")]:
            lo, hi = math.exp(b[i] - 1.96 * se[i]), math.exp(b[i] + 1.96 * se[i])
            cells.append(f"{math.exp(b[i]):.2f} [{lo:.2f}, {hi:.2f}] ({p[i]:.3g})")
            add("logit_nano_mini", metric=lab, term=nm, beta=b[i], se=se[i], OR=math.exp(b[i]), ci_lo=lo, ci_hi=hi, p=p[i])
        md.append(f"| {lab} | " + " | ".join(cells) + " |")

    # ---------- 5. Continuous metrics ----------
    md += ["", "## 5. Continuous metrics, anonymous task, pooled over budgets", "",
           "mean [bootstrap 95 % CI, 10 000 resamples, seed 20260907]; Mann-Whitney U two-sided p between tiers. "
           "CU-to-stable and break-even error exist only for some runs (n shown).", "",
           "| metric | nano | mini | 5.5 | p nano-mini | p mini-5.5 | p nano-5.5 |", "|---|---|---|---|---|---|---|"]
    for key in CONT:
        vals = {}
        for t in TIERS:
            v = [r[key] for r in E if r["model"] == t and r["variant"] == "anonymous" and isnum(r[key])]
            vals[t] = np.array(v, float)
        cells = []
        for t in TIERS:
            v = vals[t]
            if len(v) == 0:
                cells.append("-")
                continue
            bs = np.array([RNG.choice(v, len(v)).mean() for _ in range(10000)])
            lo, hi = np.percentile(bs, [2.5, 97.5])
            cells.append(f"{v.mean():.3g} [{lo:.3g}, {hi:.3g}] (n={len(v)})")
            add("continuous", metric=key, tier=SHORT[t], n=len(v), mean=v.mean(), median=float(np.median(v)), ci_lo=lo, ci_hi=hi)
        ps = []
        for i, j in PAIRS:
            a, b = vals[TIERS[i]], vals[TIERS[j]]
            if len(a) and len(b) and not (np.all(a == a[0]) and np.all(b == a[0])):
                p = stats.mannwhitneyu(a, b, alternative="two-sided").pvalue
            else:
                p = float("nan")
            ps.append(fmt(p, 3))
            add("mannwhitney", metric=key, pair=f"{SHORT[TIERS[i]]} vs {SHORT[TIERS[j]]}", p=p)
        md.append(f"| {key} | " + " | ".join(cells) + " | " + " | ".join(ps) + " |")

    # ---------- 6. Pre-registered Agent-specific Go ----------
    md += ["", "## 6. Pre-registered Agent-specific Go (E beats D; repeatable = >= 4 of 5 runs at the same budget, in >= 2 tiers)", "",
           "Anonymous task. D is deterministic (one trajectory per budget). Criteria per run: (a) CU to a stable correct winner lower than D; "
           "(b) regret lower than D: D's regret is 0 at every budget, so this criterion can only tie and is not counted; (c) unnecessary-CU fraction lower than D; "
           "(d) full decision correct where D is not (D fails only at 200 CU). Counts are runs out of 5.", "",
           "| budget | D: full / CU-stable / unnec. | " + " | ".join(f"{SHORT[t]}: (a) / (c) / (d)" for t in TIERS) + " |", "|---|---|" + "---|" * 3]
    win_tiers = defaultdict(set)
    for b in BUDGETS:
        d = D[("anonymous", b)]
        dcu = d["CU_to_stable_correct_winner"]
        dun = d["unnecessary_CU_fraction"]
        cells = [f"{int(bool(d['full_decision_correct']))} / {fmt(dcu, 0)} / {dun:.2f}"]
        for t in TIERS:
            runs = [r for r in E if r["model"] == t and r["variant"] == "anonymous" and int(r["budget_CU"]) == b]
            a = sum(1 for r in runs if isnum(r["CU_to_stable_correct_winner"]) and isnum(dcu) and r["CU_to_stable_correct_winner"] < dcu)
            c = sum(1 for r in runs if isnum(r["unnecessary_CU_fraction"]) and r["unnecessary_CU_fraction"] < dun)
            dd = sum(1 for r in runs if r["full_decision_correct"] and not d["full_decision_correct"])
            for crit, k in [("a", a), ("c", c), ("d", dd)]:
                if k >= 4:
                    win_tiers[(crit, b)].add(SHORT[t])
                add("prereg_go", budget=b, tier=SHORT[t], criterion=crit, wins_of_5=k, D_value={"a": dcu, "c": dun, "d": int(bool(d["full_decision_correct"]))}[crit])
            cells.append(f"{a} / {c} / {dd}")
        md.append(f"| {b} | " + " | ".join(cells) + " |")
    hits = {k: v for k, v in win_tiers.items() if len(v) >= 2}
    md += ["", "Repeatable (>= 4/5) cells: " + (", ".join(f"criterion ({c}) at {b} CU in {sorted(v)}" for (c, b), v in sorted(win_tiers.items())) or "none") + ".",
           "**Agent-specific Go met (>= 2 tiers): " + (", ".join(f"criterion ({c}) at {b} CU [{', '.join(sorted(v))}]" for (c, b), v in sorted(hits.items())) if hits else "NO cell") + ".**"]
    for (c, b), v in sorted(win_tiers.items()):
        add("prereg_go_summary", criterion=c, budget=b, tiers=";".join(sorted(v)), n_tiers=len(v), go=len(v) >= 2)

    # ---------- write ----------
    keys = []
    for r in rows_out:
        for k in r:
            if k not in keys:
                keys.append(k)
    with open(ROOT / "CROSS_MODEL_STATS_V1.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows_out)
    (ROOT / "CROSS_MODEL_STATS_V1.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()
