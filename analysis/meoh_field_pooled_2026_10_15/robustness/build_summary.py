"""Collect every robustness number of the methanol field result on the combined 81-group set, each next to its
first-set anchor (the committed first-set output), into summary.json and results_table.md (this folder).

Inputs: the combined-set outputs in the subfolders of this folder (written by the scripts run with
MEOH_FIELD_SET=combined, see README.md) and the committed first-set outputs. For every deterministic analysis the
first-set groups of the combined run must equal the committed first-set counts; the re-measurement Monte Carlo draws
one random stream over all 632 (S6) / 632 (S5) entries, so its first-set anchor is the committed first-set run (the
default-mode rerun reproduces it) and the first-set groups of the combined run are reported alongside.

Two numbers are derived here with the committed method:
  - the paper-bootstrap interval of the excess over the unlimited loop along the limit scan
    (analysis/meoh_constraint_boundary_2026_10_12/run_boundary.bootstrap_all: 10,000 resamples of the S5 papers, seed
    20261006, the same resamples for every limit), applied to the inlet-definition group tables; on the committed
    first-set tables it reproduces boundary_summary.json exactly (checked below);
  - the near-infeasible / ordinary split of the S6 disagreements (regret > 1 or the paper leader's S6 cost > 2x its S5
    cost; run_pooled.near_infeasible) crossed with the groups kept in >= 90 % of re-measurements.

    python build_summary.py      -> summary.json, results_table.md
"""
import csv
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

os.environ["MEOH_FIELD_SET"] = "combined"
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import field_set as FS  # noqa: E402

A = FS.REPO / "analysis"
ROB1 = A / "meoh_s6_robustness_2026_10_13"
INL1 = A / "meoh_inlet_definition_2026_10_12"
BOOT_N, BOOT_SEED = 10_000, 20261006
LIMITS = ["4", "5", "6", "6.86", "8", "10", "12", "15", "20", "25", "30"]
FAILS = []


def j(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def frac(a, b):
    return f"{a}/{b}"


def check(name, first_in_combined, committed):
    ok = first_in_combined == committed
    if not ok:
        FAILS.append(f"{name}: first-set part {first_in_combined} != committed {committed}")
    return ok


CAND = FS.candidates()
FIRST_GROUPS = set(FS.first_part(CAND).group)


# ------------------------------------------------------------------------------------------ 1. re-measurement ------
def noise():
    out = {}
    for t, anchor in (("s6", (28, 40, 24)), ("s5", (15, 40, 11))):
        c1, c = j(ROB1 / f"stats_{t}" / "summary.json"), j(HERE / f"stats_{t}" / "summary.json")
        g = pd.read_csv(HERE / f"stats_{t}" / "group_noise_probabilities.csv")
        v = pd.read_csv(HERE / f"stats_{t}" / "validation.csv")
        v1 = pd.read_csv(ROB1 / f"stats_{t}" / "validation.csv")
        gf = g[g.group.isin(FIRST_GROUPS)]

        def block(s, val, ng):
            n = s["noise"]
            k1 = n["meas_k1"]
            return dict(
                disagreements=frac(s["point_estimate"]["groups"], s["groups"]),
                kept_ge90pct={k: frac(n[f"meas_{k}"]["observed_mismatches_kept_in_ge_90pct"], s["point_estimate"]["groups"])
                              for k in ("k1", "k2", "k4")},
                disagreement_count_mean_and_95pct={k: [round(n[f"meas_{k}"]["mismatch_groups_mean"], 3),
                                                      n[f"meas_{k}"]["mismatch_groups_q025_q975"]]
                                                  for k in ("k1", "k2", "k4")},
                noise_only_sty_leader_changes=dict(mean=round(k1["sty_leader_differs_from_reported_mean"], 3),
                                                   range95=k1["sty_leader_differs_from_reported_q025_q975"]),
                exact_runs_outside_grid={k: n[f"meas_{k}"]["exact_runs_outside_grid"] for k in ("k1", "k2", "k4")},
                validation=dict(all=frac(s["validation"]["verdict_disagreements_total"], s["validation"]["verdicts_compared"]),
                                k1=frac(int(val[val.scenario == "meas_k1"].groups_with_different_verdict.sum()),
                                        int((val.scenario == "meas_k1").sum()) * ng),
                                cost_rel_err_p99_max=s["validation"]["cost_rel_err_p99_max"]),
                bootstrap_ci95=s["cluster_bootstrap"]["fraction_ci95"])
        first = block(c1, v1, c1["groups"])
        comb = block(c, v, c["groups"])
        got = (c1["point_estimate"]["groups"], c1["groups"], c1["noise"]["meas_k1"]["observed_mismatches_kept_in_ge_90pct"])
        ok = check(f"noise {t} committed first set", got, anchor)
        obs = gf.observed_mismatch.astype(str) == "True"
        comb["first_set_groups_in_combined_run"] = dict(
            disagreements=frac(int(obs.sum()), len(gf)),
            kept_ge90pct={k: int((obs & (gf[f"p_mismatch_meas_{k}"] >= 0.9)).sum()) for k in ("k1", "k2", "k4")})
        ok &= check(f"noise {t} first-set point estimate in combined", (int(obs.sum()), len(gf)), anchor[:2])
        out[t.upper()] = dict(first_set=first, first_set_anchor_reproduced=ok, combined=comb)
    return out


# ------------------------------------------------------------------------------------------ 2. inlet limit ---------
def boundary_excess(groups):
    """run_boundary.bootstrap_all on the inlet-definition group tables (frozen definition)."""
    t = {L: groups[(groups.definition == "frozen") & (groups.limit == L)] for L in ["none"] + LIMITS}
    papers = sorted(t["none"].doi.unique())
    rng = np.random.default_rng(BOOT_SEED)
    idx = rng.integers(0, len(papers), size=(BOOT_N, len(papers)))
    w = np.zeros((BOOT_N, len(papers)))
    np.add.at(w, (np.repeat(np.arange(BOOT_N), len(papers)), idx.ravel()), 1.0)
    fr = {}
    for L, d in t.items():
        g = d.assign(gt5=d.mismatch & (d.regret > 0.05)).groupby("doi")
        n = g.size().reindex(papers).to_numpy(float)
        fr[L] = dict(different_leader=(w @ g.mismatch.sum().reindex(papers).to_numpy(float)) / (w @ n),
                     gt5pct=(w @ g.gt5.sum().reindex(papers).to_numpy(float)) / (w @ n))
    out = {L: {k: [float(x) for x in np.percentile(fr[L][k] - fr["none"][k], [2.5, 97.5])]
               for k in ("different_leader", "gt5pct")} for L in LIMITS}

    def above_until(k):
        up = None
        for L in LIMITS:
            if out[L][k][0] <= 0:
                break
            up = L
        return up
    gone = next(L for L in LIMITS if all(out[L][k][0] <= 0 for k in ("different_leader", "gt5pct")))
    return dict(excess_above_zero_up_to_pct=dict(different_leader=above_until("different_leader"),
                                                 gt5pct=above_until("gt5pct")), vanishes_at_pct=gone,
                ci95_of_excess=out)


def inlet_block(folder):
    scan = pd.read_csv(folder / "definition_scan.csv", dtype={"limit_pct": str})
    groups = pd.read_csv(folder / "scan_groups.csv", dtype={"limit": str})
    ec = pd.read_csv(folder / "entry_costs.csv")

    def row(d, L):
        return scan[(scan.definition == d) & (scan.limit_pct == L)].iloc[0]
    s5_groups = set(groups[(groups.definition == "frozen") & (groups.limit == "none")].group)
    co = ec[ec.group.isin(s5_groups)].co_frozen_none
    band = [int(row("frozen", L).different_leader) for L in ("5", "6", "6.86", "8", "10")]
    ti = [int(row("true_inert", L).different_leader) for L in LIMITS]
    return dict(
        sweep={L: dict(disagreements=frac(int(row("frozen", L).different_leader), int(row("frozen", L).groups)),
                       gt5pct=int(row("frozen", L).gt5pct)) for L in ["none"] + LIMITS},
        band_5_10pct=f"{min(band)}-{max(band)} of {int(row('frozen', '6.86').groups)}",
        at_12pct=frac(int(row("frozen", "12").different_leader), int(row("frozen", "12").groups)),
        at_15pct=frac(int(row("frozen", "15").different_leader), int(row("frozen", "15").groups)),
        co_excluded_6_86=dict(disagreements=frac(int(row("true_inert", "6.86").different_leader),
                                                 int(row("true_inert", "6.86").groups)),
                              gt5pct=int(row("true_inert", "6.86").gt5pct)),
        co_excluded_all_limits=f"{min(ti)}-{max(ti)}",
        inlet_co_without_limit=dict(entries=int(len(co)), median=float(co.median()), p10=float(co.quantile(0.1)),
                                    p90=float(co.quantile(0.9))),
        co_fraction_of_limited_quantity_median_6_86=float(row("frozen", "6.86").co_fraction_of_nonreactive_median),
        purge_median=dict(none=float(row("frozen", "none").purge_median), s6=float(row("frozen", "6.86").purge_median)),
        excess_over_unlimited=boundary_excess(groups)), groups


def inlet():
    first, g1 = inlet_block(INL1)
    comb, g = inlet_block(HERE / "inlet_definition")
    # the reimplemented excess bootstrap reproduces the committed constraint-boundary analysis on the first set
    bnd = j(A / "meoh_constraint_boundary_2026_10_12" / "boundary_summary.json")["scenarios"]
    name = {L: ("S6" if L == "6.86" else f"lim{L}") for L in LIMITS}
    ex = first["excess_over_unlimited"]["ci95_of_excess"]
    dev = max(abs(ex[L][k][i] - bnd[name[L]]["bootstrap"][f"{k}_minus_S5"]["ci95"][i])
              for L in LIMITS for k in ("different_leader", "gt5pct") for i in (0, 1))
    if dev > 1e-12:
        FAILS.append(f"excess bootstrap does not reproduce boundary_summary.json ({dev})")
    gf = g[g.group.isin(FIRST_GROUPS)]
    fic = {f"{d}|{L}": frac(int(x.mismatch.sum()), len(x)) for (d, L), x in gf.groupby(["definition", "limit"])}
    com = {f"{d}|{L}": frac(int(x.mismatch.sum()), len(x)) for (d, L), x in g1.groupby(["definition", "limit"])}
    ok = check("inlet first-set groups", fic, com)
    return dict(first_set=first, first_set_anchor_reproduced=ok, combined=comb,
                excess_bootstrap_reproduces_committed_first_set_max_abs_diff=dev)


# ------------------------------------------------------------------------------------------ 3. CO to equilibrium ---
def co_bound():
    s1, s = j(A / "meoh_co_conversion_bound_2026_10_13" / "summary.json"), j(HERE / "co_conversion_bound" / "summary.json")

    def b(x):
        r = x["results"]
        return {f"{rule}|{L}": dict(disagreements=frac(r[rule][L]["disagreements"], r[rule][L]["groups"]),
                                    gt5pct=r[rule][L]["gt5pct"], gt5pct_papers=r[rule][L]["gt5pct_papers"],
                                    median_inlet_co=r[rule][L]["median_inlet_co_share_at_optimum"])
                for rule in ("central", "high") for L in ("none", "6.86")}
    first = b(s1)
    fic = s["frozen_anchors"]["first_set"]
    ok = all(check(f"co_bound {k}", fic[k][:2], [int(x) for x in first[k]["disagreements"].split("/")])
             for k in ("central|none", "central|6.86", "high|6.86"))
    return dict(first_set=first, first_set_anchor_reproduced=ok, combined=b(s), first_set_in_combined=fic)


# ------------------------------------------------------------------------------------------ 4. catalyst inventory --
def conversion():
    out = {}
    for t, f1, f in (("S6", A / "verify_2026_10_12_s6_conversion" / "s6_conversion_summary.json",
                      HERE / "conversion_s6" / "s6_conversion_summary.json"),
                     ("S5", A / "meoh_literature_inversion_2026_10_05" / "conversion_sensitivity_summary.json",
                      HERE / "conversion_s5" / "conversion_sensitivity_summary.json")):
        c1, c = j(f1), j(f)

        def b(x):
            r = {}
            for k in ("printed|lab", "printed|cost_f0.95", "printed|cost_f0.9", "printed|cost_f0.99",
                      "printed|cost_two_sided", "all|lab", "all|cost_f0.95"):
                v = x["scenarios"][k]
                r[k] = dict(disagreements=frac(v["top1_mismatch_groups"], v["groups"]), gt5pct=v["gt5pct"],
                            gt5pct_papers=v["gt5pct_papers"],
                            other_catalyst_sameT_gt5pct=v.get("gt5pct_by_kind", {}).get(
                                "other catalyst, same temperature"))
            return r
        first = b(c1)
        fic = (c.get("first_set") or c.get("meta", {}).get("first_set"))
        ok = all(check(f"conversion {t} {k}", f"{fic[k]['disagreements']}/{fic[k]['groups']}", first[k]["disagreements"])
                 for k in first)
        out[t] = dict(first_set=first, first_set_anchor_reproduced=ok, combined=b(c))
    return out


# ------------------------------------------------------------------------------------------ 5. composition price ---
def catalyst():
    c1, c = j(ROB1 / "catalyst_cost.json"), j(HERE / "catalyst_cost" / "catalyst_cost.json")
    out = {}
    for t in ("S6", "S5"):
        def b(x):
            return {k: dict(disagreements=frac(v["disagreements"], v["groups"]), gt5pct=v["gt5pct"])
                    for k, v in x[t]["variants"].items()}
        first = b(c1)
        fic = c[t]["first_set"]
        ok = all(check(f"catalyst {t} {k}", frac(fic[k]["disagreements"], fic[k]["groups"]), first[k]["disagreements"])
                 for k in first)
        out[t] = dict(first_set=first, first_set_anchor_reproduced=ok, combined=b(c))
    return out


# ------------------------------------------------------------------------------------------ 6. selectivity split ---
def split():
    c1, c = j(ROB1 / "selectivity_split.json"), j(HERE / "selectivity_split" / "selectivity_split.json")
    out = {}
    for t in ("S6", "S5"):
        def b(x):
            return {v: dict(disagreements=frac(x[t][v]["disagreements"], x[t][v]["groups"]), gt5pct=x[t][v]["gt5pct"])
                    for v in ("convention", "low", "high")}
        first, comb = b(c1), b(c)
        fic = c["first_set"][t]
        ok = all(check(f"split {t} {v}", frac(fic[v]["disagreements"], fic[v]["groups"]), first[v]["disagreements"])
                 for v in first)
        lo = [int(comb[v]["disagreements"].split("/")[0]) for v in ("low", "high")]
        lo1 = [int(first[v]["disagreements"].split("/")[0]) for v in ("low", "high")]
        out[t] = dict(first_set=dict(first, bounds=f"{min(lo1)}-{max(lo1)}"), first_set_anchor_reproduced=ok,
                      combined=dict(comb, bounds=f"{min(lo)}-{max(lo)}"))
    return out


# ------------------------------------------------------------------------------------------ 7. plot-read cohort ----
def all_entries():
    led = j(INL1 / "ledger_summary.json")["all_entries_result"]
    s = j(HERE / "all_entries" / "summary.json")
    out = {}
    for t, k in (("S6", "S6_6_86pct"), ("S5", "S5")):
        first = dict(disagreements=frac(led[k]["different_leader"], led[k]["groups"]), gt5pct=led[k]["gt5pct"])
        fic = dict(disagreements=frac(s[t]["first"]["disagreements"], s[t]["first"]["groups"]),
                   gt5pct=s[t]["first"]["gt5pct"])
        ok = check(f"all entries {t}", fic, first)
        out[t] = dict(first_set=first, first_set_anchor_reproduced=ok,
                      combined=dict(disagreements=frac(s[t]["combined"]["disagreements"], s[t]["combined"]["groups"]),
                                    gt5pct=s[t]["combined"]["gt5pct"], papers=s[t]["combined"]["papers"],
                                    bootstrap_ci95=s[t]["bootstrap"]["ci95"]),
                      second_set=dict(disagreements=frac(s[t]["second"]["disagreements"], s[t]["second"]["groups"])))
    return out


# ------------------------------------------------------------------------------------------ 8. pruning ------------
def pruning():
    p1, p = j(A / "meoh_pruning_2026_10_06" / "summary.json"), j(HERE / "pruning" / "summary.json")

    def b(x):
        r = x["pruning"]["recycled_opt"]
        return dict(spared=frac(r["excluded"], r["full"]), excluded_fraction=r["excluded_fraction"],
                    compute_share=x["compute_fraction_recycled_opt"], leaders_missed=r["leader_missed"],
                    inert_spared=frac(x["pruning"]["inert_opt"]["excluded"], x["pruning"]["inert_opt"]["full"]),
                    timing_s=x["timing_s"])
    first = b(p1)
    f = p["first_set"]
    fic = dict(spared=frac(f["recycled_opt"]["excluded"], f["recycled_opt"]["full"]),
               leaders_missed=f["recycled_opt"]["leader_missed"],
               compute_share_with_this_runs_timing=f["compute_fraction_recycled_opt"])
    ok = check("pruning", (fic["spared"], fic["leaders_missed"]), (first["spared"], first["leaders_missed"]))
    return dict(first_set=first, first_set_anchor_reproduced=ok, combined=b(p), first_set_in_combined=fic,
                treatment="S5 recycled CO (cost_recycled_opt) and inert CO, as the committed analysis")


# ------------------------------------------------------------------------------------------ 9. plant variants -----
def plant():
    s1, s = j(A / "meoh_plant_benchmark_2026_10_06" / "sensitivity_summary.json"), j(HERE / "plant_variants" / "sensitivity_summary.json")
    loop = [k for k in s1["variants"] if not k.startswith(("catalyst", "combined", "baseline"))]

    def rng(v, tag=""):
        x = [v[f"{k}{tag}"]["top1_mismatch_groups"] for k in loop]
        return f"{min(x)}-{max(x)} of {v[f'baseline{tag}']['groups']}"
    fs = s["first_set"]
    first_s6 = [fs[f"{k}|S6"]["disagreements"] for k in loop]
    ok = check("plant variants S5", {k: fs[k]["disagreements"] for k in s1["variants"]},
               {k: v["top1_mismatch_groups"] for k, v in s1["variants"].items()})
    per = {k: dict(S5=frac(s["variants"][k]["top1_mismatch_groups"], s["variants"][k]["groups"]),
                   S6=frac(s["variants"][f"{k}|S6"]["top1_mismatch_groups"], s["variants"][f"{k}|S6"]["groups"]))
           for k in s1["variants"]}
    return dict(variants_in_range=loop, first_set=dict(S5=rng(s1["variants"]),
                                                       S6_from_combined_run=f"{min(first_s6)}-{max(first_s6)} of 40"),
                first_set_anchor_reproduced=ok,
                combined=dict(S5=rng(s["variants"]), S6=rng(s["variants"], "|S6")), per_variant_combined=per)


# ------------------------------------------------------------------------------------------ 10. Note 3 extras ------
def purge_boundary():
    b1 = j(A / "meoh_literature_inversion_2026_10_05" / "purge_boundary_summary.json")
    b = j(HERE / "purge_boundary" / "purge_boundary_summary.json")

    def blk(x, gm_file):
        bb, xo = x["boundary"], x["boundary"]["at_extended_optimum"]
        gm = pd.read_csv(gm_file)
        m = gm[gm.top1_mismatch]
        return dict(below_0p5pct=frac(bb["extended_optimum_below_0p5pct"], x["entries"]),
                    purge_median=xo["purge"]["median"], nonreactive_median=xo["inlet_mol_frac"]["nonreactive"]["median"],
                    recycle_ratio_median=xo["recycle_ratio"]["median"],
                    disagreements=frac(int(len(m)), int(len(gm))), gt5pct=int((m.regret > 0.05).sum()))
    first = blk(b1, A / "meoh_literature_inversion_2026_10_05" / "group_metrics_purge_extended.csv")
    fic = b["first_set"]
    ok = check("purge boundary", (fic["below_0p5pct"], f"{fic['disagreements']}/{fic['groups']}", fic["gt5pct"]),
               (int(first["below_0p5pct"].split("/")[0]), first["disagreements"], first["gt5pct"]))
    return dict(first_set=first, first_set_anchor_reproduced=ok,
                combined=blk(b, HERE / "purge_boundary" / "group_metrics_purge_extended.csv"), first_set_in_combined=fic)


def near_infeasible_robust():
    """Ordinary / near-infeasible S6 disagreements (run_pooled.near_infeasible) and those kept in >= 90 % of
    re-measurements at the reported noise."""
    c = pd.read_csv(FS.HERE / "pooled_candidates.csv")
    gm = pd.read_csv(FS.HERE / "groups_S6.csv")
    g = pd.read_csv(HERE / "stats_s6" / "group_noise_probabilities.csv")
    robust = set(g[(g.observed_mismatch.astype(str) == "True") & (g.p_mismatch_meas_k1 >= 0.9)].group)
    rows = []
    for r in gm[gm.top1_mismatch].itertuples():
        e = c[c.group == r.group]
        lab = e[e.catalyst == r.upstream_winner].sort_values("cost_recycled_opt_inlet").iloc[0]
        near = (r.regret > 1.0) or (lab.cost_recycled_opt_inlet / lab.cost_recycled_opt > 2.0)
        rows.append(dict(group=r.group, near=near, gt5=r.regret > 0.05, robust=r.group in robust,
                         in_first=r.group in FIRST_GROUPS))
    d = pd.DataFrame(rows)
    o = d[~d.near]
    out = dict(disagreements=int(len(d)), near_infeasible=int(d.near.sum()), ordinary=int(len(o)),
               ordinary_gt5pct=int(o.gt5.sum()), ordinary_robust_to_remeasurement=int(o.robust.sum()),
               robust_to_remeasurement=int(d.robust.sum()))
    o1 = o[o.in_first]
    rob1 = j(ROB1 / "results.json")["noise_robust_S6_k1_ordinary"]
    s6g = pd.read_csv(ROB1 / "s6_groups.csv")
    s6g = s6g[s6g.mismatch.astype(str) == "True"]
    first = dict(near_infeasible=int((s6g.cls == "near-infeasible").sum()), ordinary=int((s6g.cls == "ordinary").sum()),
                 ordinary_gt5pct=int(((s6g.cls == "ordinary") & (s6g.regret > 0.05)).sum()),
                 ordinary_robust_to_remeasurement=rob1["ordinary"])
    first_comb = dict(near_infeasible=int(d[d.in_first].near.sum()), ordinary=int(len(o1)),
                      ordinary_gt5pct=int(o1.gt5.sum()), ordinary_robust_in_combined_run=int(o1.robust.sum()))
    ok = check("near-infeasible split first set", (first_comb["near_infeasible"], first_comb["ordinary"],
                                                   first_comb["ordinary_gt5pct"]),
               (first["near_infeasible"], first["ordinary"], first["ordinary_gt5pct"]))
    return dict(first_set=first, first_set_anchor_reproduced=ok, combined=out, first_set_in_combined=first_comb)


def note3_sources():
    """Supplementary Note 3 statements with a first-set-only source, and where the combined value is."""
    return [
        dict(statement="re-measurement: kept in >= 90 %, noise-only STY-leader changes, twice the noise",
             first_set_source="analysis/meoh_s6_robustness_2026_10_13/stats_s6|stats_s5", combined="1_noise"),
        dict(statement="inlet-limit sweep 4-30 %, > 5 % counts, CO-excluded limit 15-19 (18 at 6.86 %, 8 > 5 %)",
             first_set_source="analysis/meoh_inlet_definition_2026_10_12/definition_scan.csv", combined="2_inlet"),
        dict(statement="excess over the unlimited loop above zero up to 12 % / 10 %, vanishes at 15 %",
             first_set_source="analysis/meoh_constraint_boundary_2026_10_12/boundary_summary.json",
             combined="2_inlet.combined.excess_over_unlimited"),
        dict(statement="inlet CO without the limit, median 7.1 % (10th-90th 0.5-22 %); CO > 80 % of the limited quantity;"
                       " median purge 0.5 % -> 2.6 %",
             first_set_source="analysis/meoh_inlet_definition_2026_10_12/entry_costs.csv, definition_scan.csv",
             combined="2_inlet.combined.inlet_co_without_limit / co_fraction_of_limited_quantity_median_6_86 / purge_median"),
        dict(statement="with plot-read entries the inert-limited loop scores 82 of 83 groups; 54 of 82, 35 of 83",
             first_set_source="analysis/meoh_inlet_definition_2026_10_12/ledger_summary.json", combined="7_all_entries"),
        dict(statement="recycled CO converted up to CO-hydrogenation equilibrium: 14 / 27 of 40, 0.9 % inlet CO",
             first_set_source="analysis/meoh_co_conversion_bound_2026_10_13/summary.json", combined="3_co_bound"),
        dict(statement="near-infeasible 11 of 28; ordinary 17 (12 > 5 %, 13 robust to re-measurement)",
             first_set_source="analysis/meoh_s6_robustness_2026_10_13/results.json, s6_groups.csv",
             combined="10_near_infeasible_robust"),
        dict(statement="unreported CO / CH4 split at either bound 26-29 of 40",
             first_set_source="analysis/meoh_s6_robustness_2026_10_13/selectivity_split.json", combined="6_split"),
        dict(statement="composition-priced catalysts 25 of 40, 22 > 5 %",
             first_set_source="analysis/meoh_s6_robustness_2026_10_13/catalyst_cost.json", combined="5_catalyst"),
        dict(statement="catalyst inventory: 23 of 40, 16 > 5 % from 12 papers, other catalyst same T > 5 % in 5 from 4 "
                       "papers; 14 of 40, 3 > 5 % without the limit",
             first_set_source="analysis/verify_2026_10_12_s6_conversion, meoh_literature_inversion_2026_10_05/"
                              "conversion_sensitivity_summary.json", combined="4_conversion"),
        dict(statement="purge grid extended to 1e-4 %: optimum below 0.5 % for 309 of 310 entries (median 0.048 %), "
                       "40 % non-H2/CO2, recycle ratio 44, 14 of 40 (2 > 5 %)",
             first_set_source="analysis/meoh_literature_inversion_2026_10_05/purge_boundary_summary.json",
             combined="10_purge_boundary"),
        dict(statement="plant terms at reference values: 14-16 of 40 (main text, Methods)",
             first_set_source="analysis/meoh_plant_benchmark_2026_10_06/sensitivity_summary.json",
             combined="9_plant_variants"),
        dict(statement="pruning by the lower bound: 199 of 310 spared, 36 % compute (Extended Data Fig. 2)",
             first_set_source="analysis/meoh_pruning_2026_10_06/summary.json", combined="8_pruning"),
        dict(statement="response-surface validation in Methods (7 of 600 S6, 1 of 600 S5)",
             first_set_source="analysis/meoh_s6_robustness_2026_10_13/stats_s6|stats_s5/validation.csv",
             combined="1_noise.*.combined.validation"),
        dict(statement="the 83 -> 40 group ledger (Supplementary Table 6) and the ledger's grouping checks",
             first_set_source="analysis/meoh_inlet_definition_2026_10_12/run_group_ledger.py",
             combined="not recomputed: a ledger of the first extraction's extraction and grouping decisions"),
        dict(statement="hand-built Re/TiO2 noise model (r_X 5.21 %, sigma 0.847 pp) and the counterfactual backward design",
             first_set_source="analysis/meoh_measurement_mc_2026_10_05, meoh_counterfactual_backward_2026_10_05",
             combined="not field-set analyses (Re/TiO2 states); the noise model is an input of 1_noise"),
    ]


def table(r):
    """results_table.md: analysis | first set (anchor reproduced) | combined S6 | combined S5."""
    yn = lambda ok: "yes" if ok else "NO"  # noqa: E731
    n6, n5 = r["1_noise"]["S6"], r["1_noise"]["S5"]

    def nz(b):
        k = b["kept_ge90pct"]
        sl = b["noise_only_sty_leader_changes"]
        w = b["disagreement_count_mean_and_95pct"]
        return (f"{b['disagreements']}; kept in >= 90 %: {k['k1']} (2x {k['k2']}, 4x {k['k4']}); noise-only STY-leader "
                f"changes {sl['mean']:.1f} ({sl['range95'][0]:.0f}-{sl['range95'][1]:.0f}); disagreement count 1x/2x/4x "
                + ", ".join(f"{w[k][0]:.1f} [{w[k][1][0]:.0f}-{w[k][1][1]:.0f}]" for k in ("k1", "k2", "k4"))
                + f"; validation {b['validation']['all']} ({b['validation']['k1']} at 1x)")
    rows = [("1 Re-measurement Monte Carlo", f"S6 {nz(n6['first_set'])}<br>S5 {nz(n5['first_set'])}",
             n6["first_set_anchor_reproduced"] and n5["first_set_anchor_reproduced"], nz(n6["combined"]),
             nz(n5["combined"]))]
    i1, i = r["2_inlet"]["first_set"], r["2_inlet"]["combined"]

    def inl(x):
        sw = ", ".join(f"{L}: {x['sweep'][L]['disagreements'].split('/')[0]} ({x['sweep'][L]['gt5pct']})" for L in LIMITS)
        ex = x["excess_over_unlimited"]
        co = x["inlet_co_without_limit"]
        return (f"limits 4-30 % (> 5 %): {sw}; 5-10 % band {x['band_5_10pct']}; 12 % {x['at_12pct']}; 15 % "
                f"{x['at_15pct']}; CH4+N2 only at 6.86 %: {x['co_excluded_6_86']['disagreements']} "
                f"({x['co_excluded_6_86']['gt5pct']} > 5 %), all limits {x['co_excluded_all_limits']}; excess over "
                f"unlimited > 0 up to {ex['excess_above_zero_up_to_pct']['different_leader']} % (all) / "
                f"{ex['excess_above_zero_up_to_pct']['gt5pct']} % (> 5 %), gone at {ex['vanishes_at_pct']} %; inlet CO "
                f"without limit median {100 * co['median']:.1f} % (p10 {100 * co['p10']:.1f}, p90 {100 * co['p90']:.0f} %); "
                f"CO share of limited quantity {100 * x['co_fraction_of_limited_quantity_median_6_86']:.0f} %; median "
                f"purge {100 * x['purge_median']['none']:.2f} -> {100 * x['purge_median']['s6']:.2f} %")
    rows.append(("2 Inlet-limit sweep and CO definitions", inl(i1), r["2_inlet"]["first_set_anchor_reproduced"],
                 inl(i), f"no limit {i['sweep']['none']['disagreements']} ({i['sweep']['none']['gt5pct']} > 5 %)"))
    c1, c = r["3_co_bound"]["first_set"], r["3_co_bound"]["combined"]
    cb = lambda x, L: (f"{x[f'high|{L}']['disagreements']} ({x[f'high|{L}']['gt5pct']} > 5 %, "  # noqa: E731
                       f"{x[f'high|{L}']['gt5pct_papers']} papers; median inlet CO "
                       f"{100 * x[f'high|{L}']['median_inlet_co']:.2f} %)")
    rows.append(("3 Recycled CO to CO-hydrogenation equilibrium", f"S6 {cb(c1, '6.86')}; S5 {cb(c1, 'none')}",
                 r["3_co_bound"]["first_set_anchor_reproduced"], cb(c, "6.86"), cb(c, "none")))
    v6, v5 = r["4_conversion"]["S6"], r["4_conversion"]["S5"]
    def cv(x):
        p = x["printed|cost_f0.95"]
        k = p["other_catalyst_sameT_gt5pct"] or dict(groups=0, papers=0)
        return (f"{p['disagreements']} ({p['gt5pct']} > 5 % from {p['gt5pct_papers']} papers; other catalyst at the "
                f"same T > 5 %: {k['groups']} from {k['papers']} papers)")
    rows.append(("4 Catalyst inventory (conversion towards equilibrium)",
                 f"S6 {cv(v6['first_set'])}; S5 {cv(v5['first_set'])}",
                 v6["first_set_anchor_reproduced"] and v5["first_set_anchor_reproduced"], cv(v6["combined"]),
                 cv(v5["combined"])))
    k6, k5 = r["5_catalyst"]["S6"], r["5_catalyst"]["S5"]
    kc = lambda x: f"{x['composition_3y']['disagreements']} ({x['composition_3y']['gt5pct']} > 5 %)"  # noqa: E731
    rows.append(("5 Composition-priced catalysts (3 y)", f"S6 {kc(k6['first_set'])}; S5 {kc(k5['first_set'])}",
                 k6["first_set_anchor_reproduced"] and k5["first_set_anchor_reproduced"], kc(k6["combined"]),
                 kc(k5["combined"])))
    s6, s5 = r["6_split"]["S6"], r["6_split"]["S5"]
    sp = lambda x: (f"{x['bounds']} (low {x['low']['disagreements']}, high {x['high']['disagreements']})")  # noqa: E731
    rows.append(("6 Unreported CO / CH4 at either bound", f"S6 {sp(s6['first_set'])}; S5 {sp(s5['first_set'])}",
                 s6["first_set_anchor_reproduced"] and s5["first_set_anchor_reproduced"], sp(s6["combined"]),
                 sp(s5["combined"])))
    a6, a5 = r["7_all_entries"]["S6"], r["7_all_entries"]["S5"]
    ae = lambda x: f"{x['disagreements']} ({x['gt5pct']} > 5 %)"  # noqa: E731
    rows.append(("7 Plot-read cohort (all entries)", f"S6 {ae(a6['first_set'])}; S5 {ae(a5['first_set'])}",
                 a6["first_set_anchor_reproduced"] and a5["first_set_anchor_reproduced"], ae(a6["combined"]),
                 ae(a5["combined"])))
    p1, p = r["8_pruning"]["first_set"], r["8_pruning"]["combined"]
    pr = lambda x: (f"{x['spared']} spared, compute {100 * x['compute_share']:.0f} %, leaders missed "  # noqa: E731
                    f"{x['leaders_missed']}")
    rows.append(("8 Pruning by the lower bound (S5 recycled CO)", pr(p1), r["8_pruning"]["first_set_anchor_reproduced"],
                 "-", pr(p)))
    pv = r["9_plant_variants"]
    rows.append(("9 Plant-term variants (loop dP, recycle, compression, capital, prices)",
                 f"S5 {pv['first_set']['S5']}; S6 {pv['first_set']['S6_from_combined_run']}",
                 pv["first_set_anchor_reproduced"], pv["combined"]["S6"], pv["combined"]["S5"]))
    b1, b = r["10_purge_boundary"]["first_set"], r["10_purge_boundary"]["combined"]
    pb = lambda x: (f"optimum < 0.5 % for {x['below_0p5pct']} (median {100 * x['purge_median']:.3f} %, "  # noqa: E731
                    f"{100 * x['nonreactive_median']:.0f} % non-H2/CO2, recycle ratio {x['recycle_ratio_median']:.0f}); "
                    f"{x['disagreements']} ({x['gt5pct']} > 5 %)")
    rows.append(("10 S5 purge grid extended to 1e-4 %", pb(b1), r["10_purge_boundary"]["first_set_anchor_reproduced"],
                 "-", pb(b)))
    ni1, ni = r["10_near_infeasible_robust"]["first_set"], r["10_near_infeasible_robust"]["combined"]
    rows.append(("10 Near-infeasible split x re-measurement (S6)",
                 f"near-infeasible {ni1['near_infeasible']}, ordinary {ni1['ordinary']} ({ni1['ordinary_gt5pct']} > 5 %, "
                 f"{ni1['ordinary_robust_to_remeasurement']} robust)",
                 r["10_near_infeasible_robust"]["first_set_anchor_reproduced"],
                 f"near-infeasible {ni['near_infeasible']}, ordinary {ni['ordinary']} ({ni['ordinary_gt5pct']} > 5 %, "
                 f"{ni['ordinary_robust_to_remeasurement']} robust); robust overall {ni['robust_to_remeasurement']} of "
                 f"{ni['disagreements']}", "-"))
    out = ["| analysis | first set (40 groups) | anchor reproduced | combined 81, S6 | combined 81, S5 |",
           "|---|---|---|---|---|"]
    out += [f"| {a} | {f} | {yn(ok)} | {x} | {y} |" for a, f, ok, x, y in rows]
    return "\n".join(out) + "\n"


def main():
    res = {"1_noise": noise(), "2_inlet": inlet(), "3_co_bound": co_bound(), "4_conversion": conversion(),
           "5_catalyst": catalyst(), "6_split": split(), "7_all_entries": all_entries(), "8_pruning": pruning(),
           "9_plant_variants": plant(), "10_purge_boundary": purge_boundary(),
           "10_near_infeasible_robust": near_infeasible_robust(), "10_note3_sources": note3_sources()}
    res["checks_failed"] = FAILS
    (HERE / "summary.json").write_text(json.dumps(res, indent=1, default=float) + "\n", encoding="utf-8")
    (HERE / "results_table.md").write_text(table(res), encoding="utf-8")
    print(json.dumps(FAILS or "all first-set anchors reproduced", indent=1))
    if FAILS:
        sys.exit(1)


if __name__ == "__main__":
    main()
