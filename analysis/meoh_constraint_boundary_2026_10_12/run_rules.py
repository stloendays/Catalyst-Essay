"""Task B, as fixed in PROTOCOL_B.md (committed before this file): can a laboratory-only rule pick the plant-cost leader?

Nine laboratory-only rules (R1 STY ... R9 lowest temperature), scored in 12 scenarios (S5, S6, lim4-lim30) on the 40
frozen comparison groups; leave-one-paper-out selection of a rule (primary: training accuracy; secondary: training mean
regret) against the STY baseline, with exact McNemar tests and paper-cluster bootstrap intervals that re-run the
selection in every resample; and the loop-aware rules LA1 (STY when the loop is unconstrained, selectivity when it is
inert-limited) and LA2 (selectivity only where the limit binds on the STY leader) against every single rule, pooled
over the 12 scenarios.

Outputs: rules_by_scenario.csv, rules_fixed.csv, rules_lopo_folds.csv, rules_group_choices.csv, rules_summary.json.
"""
import json
import math
import time

import numpy as np
import pandas as pd
from scipy.stats import binomtest

from common import BY_NAME, HERE, load_candidates, leaders

SCENARIOS_B = ["S5", "S6"] + [f"lim{L}" for L in (4, 5, 6, 8, 10, 12, 15, 20, 25, 30)]
RULES = {                       # name -> score to maximise (laboratory columns only)
    "STY": lambda g: g.STY,
    "S": lambda g: g.SMeOH,
    "STY*S": lambda g: g.STY * g.SMeOH,
    "STY*S^2": lambda g: g.STY * g.SMeOH ** 2,
    "STY*S^4": lambda g: g.STY * g.SMeOH ** 4,
    "STY*S^8": lambda g: g.STY * g.SMeOH ** 8,
    "X*S": lambda g: g.X * g.SMeOH,
    "lowCH4": lambda g: -g.SCH4,
    "lowT": lambda g: -g.T_C,
}
RNAMES = list(RULES)
B_N, B_SEED = 10_000, 20261012
EXPECTED_STY_CORRECT = {"S5": 25, "S6": 12, "lim4": 12, "lim5": 14, "lim6": 13, "lim8": 13, "lim10": 16, "lim12": 16,
                        "lim15": 22, "lim20": 21, "lim25": 23, "lim30": 24}   # 40 minus the Task A counts


def choice_set(g, score):
    """Entries at the rule's best score (relative 1e-9), ties broken by the higher STY; entries still tied form the
    choice set."""
    s = score.astype(float)
    best = s.max()
    tied = g[s >= best - 1e-9 * abs(best)]
    return tied[tied.STY >= tied.STY.max() - 1e-12]


def score_groups(cand, scen):
    """Per group and rule: chosen entries, correct and regret (frozen convention) and the expected-value
    sensitivity, in the 40 groups of the scenario (finite-cost entries only)."""
    col = BY_NAME[scen]["col"]
    lt, _, _ = leaders(cand, col)
    f = cand[np.isfinite(cand[col].astype(float))]
    rows = []
    for r in lt.itertuples():
        g = f[f.group == r.group]
        cp = r.c_plant
        for name, fn in RULES.items():
            cs = choice_set(g, fn(g))
            reg = (cs[col] - cp) / cp
            hit = r.plant_idx in cs.index
            rows.append(dict(scenario=scen, group=r.group, doi=r.doi, rule=name, chosen=" | ".join(cs.catalyst),
                             n_choice=len(cs), correct=bool(hit), regret=float(reg.min()),
                             correct_ev=(1.0 / len(cs)) if hit else 0.0, regret_ev=float(reg.mean()),
                             plant_leader=cand.at[r.plant_idx, "catalyst"],
                             sty_leader_inlet_S5=float(cand.loc[choice_set(g, g.STY).index,
                                                                "nonreactive_at_opt_recycled"].max())))
    return pd.DataFrame(rows), lt


def matrices(d, papers):
    """Per-paper sums: correct counts C, regret sums R (papers x rules), groups per paper n."""
    C = d.pivot_table(index="doi", columns="rule", values="correct", aggfunc="sum").reindex(index=papers, columns=RNAMES)
    R = d.pivot_table(index="doi", columns="rule", values="regret", aggfunc="sum").reindex(index=papers, columns=RNAMES)
    n = d[d.rule == "STY"].groupby("doi").size().reindex(papers)
    return C.to_numpy(float), R.to_numpy(float), n.to_numpy(float)


def select(train_c, train_r, primary=True):
    """Index of the rule chosen on a training set (arrays over rules). The denominators are the same for every rule,
    so counts and regret sums compare as accuracies and mean regrets. primary: highest accuracy, then lowest mean
    regret, then rule order; secondary: lowest mean regret, then highest accuracy, then rule order."""
    keys = [((-train_c[k], round(train_r[k], 9), k) if primary else (round(train_r[k], 9), -train_c[k], k))
            for k in range(len(RNAMES))]
    return min(keys)[2]


def lopo(d, papers, primary=True):
    C, R, n = matrices(d, papers)
    out = []
    for p in range(len(papers)):
        k = select(C.sum(0) - C[p], R.sum(0) - R[p], primary)
        out.append(dict(doi=papers[p], rule=RNAMES[k], groups=int(n[p]), correct=int(C[p, k]), regret_sum=float(R[p, k])))
    return pd.DataFrame(out)


def lopo_bootstrap(C, R, n, w, primary=True):
    """Out-of-paper accuracy and mean regret of the selection in every resample (rows of w = paper multiplicities);
    a fold leaves out every copy of its paper; the training sums are weighted by the multiplicities."""
    Ct, Rt = w @ C, w @ R                                     # draws x rules
    trc = Ct[:, None, :] - w[:, :, None] * C[None, :, :]      # draws x folds x rules
    trr = Rt[:, None, :] - w[:, :, None] * R[None, :, :]
    trr = np.round(trr, 9)
    if primary:
        best = trc == trc.max(axis=2, keepdims=True)
        rr = np.where(best, trr, np.inf)
        best &= rr == rr.min(axis=2, keepdims=True)
    else:
        best = trr == trr.min(axis=2, keepdims=True)
        cc = np.where(best, trc, -np.inf)
        best &= cc == cc.max(axis=2, keepdims=True)
    k = np.argmax(best, axis=2)                               # first rule in order among the remaining ties
    held_c = np.take_along_axis(np.broadcast_to(C, (w.shape[0],) + C.shape), k[:, :, None], 2)[:, :, 0]
    held_r = np.take_along_axis(np.broadcast_to(R, (w.shape[0],) + R.shape), k[:, :, None], 2)[:, :, 0]
    N = w @ n
    return (w * held_c).sum(1) / N, (w * held_r).sum(1) / N


def ci(v):
    lo, hi = np.percentile(v, [2.5, 97.5])
    return [float(lo), float(hi)]


def mcnemar(a, b):
    """Exact two-sided McNemar test of paired correct/incorrect vectors a (selection) and b (baseline)."""
    a, b = np.asarray(a, bool), np.asarray(b, bool)
    n10, n01 = int((a & ~b).sum()), int((~a & b).sum())
    p = 1.0 if n10 + n01 == 0 else float(binomtest(n10, n10 + n01, 0.5).pvalue)
    return dict(selection_only=n10, baseline_only=n01, p_two_sided=p)


def loop_aware(d, scen, variant):
    """LA1: R1 in S5, R2 in every limited scenario. LA2: R2 where the limit is below the inlet non-H2/CO2 fraction of
    the group's STY leader at its S5 optimum, otherwise R1; R1 in S5."""
    sty, sel = d[d.rule == "STY"].set_index("group"), d[d.rule == "S"].set_index("group")
    if scen == "S5":
        use_sel = pd.Series(False, index=sty.index)
    elif variant == "LA1":
        use_sel = pd.Series(True, index=sty.index)
    else:
        use_sel = BY_NAME[scen]["limit"] < sty.sty_leader_inlet_S5
    out = sty.copy()
    out.loc[use_sel, ["chosen", "n_choice", "correct", "regret", "correct_ev", "regret_ev"]] = \
        sel.loc[use_sel, ["chosen", "n_choice", "correct", "regret", "correct_ev", "regret_ev"]]
    out["rule"] = variant
    out["uses_selectivity"] = use_sel
    return out.reset_index()


def jsonable(o):
    if isinstance(o, dict):
        return {str(k): jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [jsonable(v) for v in o]
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, (np.floating, float)):
        return None if not math.isfinite(float(o)) else float(o)
    if isinstance(o, np.bool_):
        return bool(o)
    return o


def main():
    t0 = time.time()
    cand = load_candidates()
    per_scen, papers = {}, None
    for scen in SCENARIOS_B:
        d, lt = score_groups(cand, scen)
        papers = sorted(lt.doi.unique()) if papers is None else papers
        if sorted(lt.doi.unique()) != papers or len(lt) != 40:
            raise AssertionError(f"{scen}: not the 40 groups of the 28 papers")
        sty_correct = int(d[d.rule == "STY"].correct.sum())
        if sty_correct != EXPECTED_STY_CORRECT[scen] or sty_correct != int((~lt.mismatch).sum()):
            raise AssertionError(f"{scen}: STY baseline {sty_correct} correct, expected {EXPECTED_STY_CORRECT[scen]}")
        per_scen[scen] = d

    rng = np.random.default_rng(B_SEED)
    idx = rng.integers(0, len(papers), size=(B_N, len(papers)))
    w = np.zeros((B_N, len(papers)))
    np.add.at(w, (np.repeat(np.arange(B_N), len(papers)), idx.ravel()), 1.0)

    rows, fixed_rows, fold_rows, choice_parts, scen_json = [], [], [], [], {}
    pooled = {k: dict(correct=0, regret=0.0, n=0) for k in RNAMES + ["LA1", "LA2"]}
    pooled_boot = {k: np.zeros(B_N) for k in RNAMES + ["LA1", "LA2"]}
    N_w = None
    for scen in SCENARIOS_B:
        d = per_scen[scen]
        C, R, n = matrices(d, papers)
        N_w = w @ n
        # fixed rules on all 40 groups
        fixed = {}
        for k, name in enumerate(RNAMES):
            x = d[d.rule == name]
            fixed[name] = dict(correct=int(x.correct.sum()), accuracy=float(x.correct.mean()),
                               mean_regret=float(x.regret.mean()), median_regret=float(x.regret.median()),
                               regret_gt5pct=int((x.regret > 0.05).sum()), accuracy_ev=float(x.correct_ev.mean()),
                               mean_regret_ev=float(x.regret_ev.mean()))
            fixed_rows.append(dict(scenario=scen, rule=name, **fixed[name]))
            pooled[name]["correct"] += fixed[name]["correct"]
            pooled[name]["regret"] += float(x.regret.sum())
            pooled[name]["n"] += len(x)
            pooled_boot[name] += w @ C[:, k]
        # leave one paper out
        res = {}
        base = d[d.rule == "STY"].set_index("doi")
        base_acc_b, base_reg_b = (w @ C[:, 0]) / N_w, (w @ R[:, 0]) / N_w
        for label, primary in (("primary", True), ("secondary", False)):
            folds = lopo(d, papers, primary)
            held = d.merge(folds[["doi", "rule"]], on=["doi", "rule"])          # held-out groups under the fold's rule
            held = held.set_index("group").loc[d[d.rule == "STY"].group]
            acc_b, reg_b = lopo_bootstrap(C, R, n, w, primary)
            # the vectorised selection with unit weights is the selection above
            a1, r1 = lopo_bootstrap(C, R, n, np.ones((1, len(papers))), primary)
            if abs(a1[0] - held.correct.mean()) > 1e-12 or abs(r1[0] - held.regret.mean()) > 1e-9:
                raise AssertionError(f"{scen} {label}: vectorised selection differs from the fold loop")
            sty_g = d[d.rule == "STY"].set_index("group").loc[held.index]
            res[label] = dict(correct=int(held.correct.sum()), accuracy=float(held.correct.mean()),
                              mean_regret=float(held.regret.mean()), median_regret=float(held.regret.median()),
                              regret_gt5pct=int((held.regret > 0.05).sum()), accuracy_ev=float(held.correct_ev.mean()),
                              rules_chosen=folds.rule.value_counts().to_dict(),
                              minus_sty_correct=int(held.correct.sum() - sty_g.correct.sum()),
                              minus_sty_mean_regret=float(held.regret.mean() - sty_g.regret.mean()),
                              mcnemar=mcnemar(held.correct.to_numpy(), sty_g.correct.to_numpy()),
                              bootstrap=dict(accuracy_ci95=ci(acc_b), mean_regret_ci95=ci(reg_b),
                                             accuracy_minus_sty_ci95=ci(acc_b - base_acc_b),
                                             mean_regret_minus_sty_ci95=ci(reg_b - base_reg_b)))
            for fr in folds.itertuples():
                fold_rows.append(dict(scenario=scen, selection=label, doi=fr.doi, rule=fr.rule, groups=fr.groups,
                                      correct=fr.correct))
            choice_parts.append(held.reset_index().assign(rule=f"LOPO_{label}")[d.columns])
        # loop-aware rules
        la = {}
        for v in ("LA1", "LA2"):
            x = loop_aware(d, scen, v)
            la[v] = dict(correct=int(x.correct.sum()), accuracy=float(x.correct.mean()),
                         mean_regret=float(x.regret.mean()), median_regret=float(x.regret.median()),
                         regret_gt5pct=int((x.regret > 0.05).sum()), groups_ranked_by_selectivity=int(x.uses_selectivity.sum()))
            pooled[v]["correct"] += la[v]["correct"]
            pooled[v]["regret"] += float(x.regret.sum())
            pooled[v]["n"] += len(x)
            pc = x.groupby("doi").correct.sum().reindex(papers).to_numpy(float)
            pooled_boot[v] += w @ pc
            choice_parts.append(x[d.columns])
        best_fixed = max(RNAMES, key=lambda r: (fixed[r]["correct"], -fixed[r]["mean_regret"]))
        scen_json[scen] = dict(sty_baseline=fixed["STY"], lopo=res, loop_aware=la, fixed_rules=fixed,
                               best_fixed_rule_post_hoc=dict(rule=best_fixed, **fixed[best_fixed]))
        lim = BY_NAME[scen]["limit"]
        rows.append(dict(scenario=scen, limit_pct=lim * 100 if lim else np.nan,
                         sty_correct=fixed["STY"]["correct"], sty_mean_regret=fixed["STY"]["mean_regret"],
                         lopo_correct=res["primary"]["correct"], lopo_mean_regret=res["primary"]["mean_regret"],
                         lopo_minus_sty=res["primary"]["minus_sty_correct"],
                         lopo_minus_sty_ci_lo=40 * res["primary"]["bootstrap"]["accuracy_minus_sty_ci95"][0],
                         lopo_minus_sty_ci_hi=40 * res["primary"]["bootstrap"]["accuracy_minus_sty_ci95"][1],
                         lopo_mcnemar_p=res["primary"]["mcnemar"]["p_two_sided"],
                         lopo_rules_chosen="; ".join(f"{k} {v}" for k, v in res["primary"]["rules_chosen"].items()),
                         lopo2_correct=res["secondary"]["correct"], lopo2_mean_regret=res["secondary"]["mean_regret"],
                         lopo2_rules_chosen="; ".join(f"{k} {v}" for k, v in res["secondary"]["rules_chosen"].items()),
                         la1_correct=la["LA1"]["correct"], la1_mean_regret=la["LA1"]["mean_regret"],
                         la2_correct=la["LA2"]["correct"], la2_mean_regret=la["LA2"]["mean_regret"],
                         best_fixed_rule_post_hoc=best_fixed, best_fixed_correct=fixed[best_fixed]["correct"],
                         **{f"{r}_correct": fixed[r]["correct"] for r in RNAMES},
                         **{f"{r}_mean_regret": fixed[r]["mean_regret"] for r in RNAMES}))

    # pooled over the 12 scenarios: LA1 / LA2 against every single rule
    tot = 12 * N_w
    pooled_out = {k: dict(correct=v["correct"], of=v["n"], accuracy=v["correct"] / v["n"],
                          mean_regret=v["regret"] / v["n"]) for k, v in pooled.items()}
    tests = {}
    for v in ("LA1", "LA2"):
        diffs = {r: dict(accuracy_difference=pooled_out[v]["accuracy"] - pooled_out[r]["accuracy"],
                         ci95=ci((pooled_boot[v] - pooled_boot[r]) / tot)) for r in RNAMES}
        beats = all(d_["accuracy_difference"] > 0 for d_ in diffs.values())
        clear = beats and all(d_["ci95"][0] > 0 for d_ in diffs.values())
        per = {s: dict(la=scen_json[s]["loop_aware"][v]["correct"],
                       best_single=scen_json[s]["best_fixed_rule_post_hoc"]["correct"],
                       best_single_rule=scen_json[s]["best_fixed_rule_post_hoc"]["rule"]) for s in SCENARIOS_B}
        tests[v] = dict(beats_every_single_rule=beats, clear=clear, differences=diffs,
                        scenarios_la_at_least_best_single=int(sum(p["la"] >= p["best_single"] for p in per.values())),
                        per_scenario=per)

    by_scen = pd.DataFrame(rows)
    by_scen.to_csv(HERE / "rules_by_scenario.csv", index=False, float_format="%.10g")
    pd.DataFrame(fixed_rows).to_csv(HERE / "rules_fixed.csv", index=False, float_format="%.10g")
    pd.DataFrame(fold_rows).to_csv(HERE / "rules_lopo_folds.csv", index=False)
    pd.concat(list(per_scen.values()) + choice_parts).to_csv(HERE / "rules_group_choices.csv", index=False,
                                                             float_format="%.10g")
    summary = dict(protocol="PROTOCOL_B.md", rules=RNAMES, scenarios=SCENARIOS_B, groups=40, papers=len(papers),
                   bootstrap=dict(resamples=B_N, seed=B_SEED), sty_baseline_anchor=EXPECTED_STY_CORRECT,
                   per_scenario=scen_json, pooled=pooled_out, loop_aware_test=tests, runtime_s=round(time.time() - t0, 1))
    (HERE / "rules_summary.json").write_text(json.dumps(jsonable(summary), indent=1) + "\n", encoding="utf-8")
    show = ["scenario", "sty_correct", "lopo_correct", "lopo_minus_sty", "lopo_minus_sty_ci_lo", "lopo_minus_sty_ci_hi",
            "lopo_mcnemar_p", "sty_mean_regret", "lopo_mean_regret", "lopo_rules_chosen", "lopo2_correct", "la1_correct",
            "la2_correct", "best_fixed_rule_post_hoc", "best_fixed_correct"]
    with pd.option_context("display.width", 260, "display.max_columns", 30, "display.max_colwidth", 40):
        print(by_scen[show].round(3).to_string(index=False))
        print(pd.DataFrame(fixed_rows).pivot(index="scenario", columns="rule", values="correct")
              .reindex(index=SCENARIOS_B, columns=RNAMES).to_string())
    print(json.dumps(jsonable(pooled_out), indent=0))
    print(json.dumps(jsonable({v: {k: tests[v][k] for k in ("beats_every_single_rule", "clear",
                                                             "scenarios_la_at_least_best_single")} for v in tests})))
    print(f"done in {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
