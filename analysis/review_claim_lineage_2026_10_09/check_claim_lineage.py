"""Advisory cross-document claim-evidence gate for S5 printed-only paper.

Read-only: regenerate a review ledger from versioned scientific inputs; never
modify manuscript/figures/analysis. --publication-gate fails on unresolved
manuscript blockers; plain run succeeds if source-data invariants hold.
"""
from __future__ import annotations
import argparse
import csv
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def csv_rows(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def json_file(path):
    return json.loads(path.read_text(encoding="utf-8"))


def catalyst(s):
    return re.sub(r"\s+", "", s.split(" [", 1)[0]).lower().replace("–", "-").replace("−", "-")


def has_temperature_series(values, tol=0.05):
    return len(values) >= 2 and max(values) - min(values) > tol


def compute_evidence(root=ROOT):
    base = root / "analysis/verify_2026_10_08"
    steps = csv_rows(base / "decomposition_steps.csv")
    s5 = next(r for r in steps if r["mode"] == "printed" and r["step"] == "S5")
    me = json_file(base / "conversion_sensitivity_summary.json")
    lab, adjusted = me["thermo|printed|lab"], me["thermo|printed|cost_f0.95"]
    nh = json_file(base / "nh3_printed_summary.json")["printed"]
    kinds = csv_rows(base / "reversal_kinds.csv")
    kind_lab = next(r for r in kinds if r["base"] == "thermo" and r["mode"] == "printed" and
                    r["conversion"] == "laboratory conversion")
    kind_adj = next(r for r in kinds if r["base"] == "thermo" and r["mode"] == "printed" and
                    r["conversion"].startswith("conversion raised"))
    pts = csv_rows(base / "conversion_sensitivity_points.csv")
    groups = defaultdict(list)
    for p in pts:
        if p["base"] == "thermo" and p["mode"] == "printed":
            groups[p["group"]].append(p)
    n_mat = n_temp = n_groups = 0
    for ps in groups.values():
        if len(ps) < 2:
            continue
        n_groups += 1
        cs = defaultdict(list)
        for p in ps:
            cs[catalyst(p["catalyst"])].append(float(p["T_C"]))
        n_mat += int(len(cs) >= 2)
        n_temp += int(any(has_temperature_series(ts) for ts in cs.values()))
    accuracies = {(r["source_type"], r["field"]): r for r in csv_rows(
        root / "agent/extraction/eval/field_accuracy_by_source.csv")}
    alloy = json_file(root / "analysis/nh3_alloy_extension_2026_10_05/summary.json")
    bench = json_file(root / "analysis/meoh_plant_benchmark_2026_10_06/sensitivity_summary.json")
    evidence = {
        "treatment": "S5_CO_recycle_thermodynamics__printed_only__UNFROZEN",
        "methanol": {
            "groups": int(s5["groups"]), "papers": int(lab["papers"]),
            "mismatches": int(s5["mismatch"]), "gt5pct": int(s5["gt5pct"]),
            "candidate_corpus": int(s5["candidates"]),
            "crosscheck_lab": int(lab["mismatch"]),
            "adjustable_mismatches": int(adjusted["mismatch"]),
            "adjustable_gt5pct": int(adjusted["gt5pct"]),
            "multi_catalyst_groups": n_mat, "temperature_series_groups_strict": n_temp,
            "temperature_series_groups_legacy": int(kind_lab["temperature_series_groups"]),
            "different_catalyst_lab": int(kind_lab["other_catalyst"]),
            "different_catalyst_adjustable": int(kind_adj["other_catalyst"]),
            "same_catalyst_temperature_lab": int(kind_lab["other_temperature"]),
            "same_catalyst_temperature_adjustable": int(kind_adj["other_temperature"]),
            "old_benchmark_baseline": "{}/{}".format(
                bench["variants"]["baseline"]["top1_mismatch_groups"],
                bench["variants"]["baseline"]["groups"]),
        },
        "ammonia": {
            "groups": int(nh["groups"]), "papers": int(nh["papers"]),
            "mismatches": int(nh["top1_mismatch_groups"]),
            "gt5pct": int(nh["mismatch_regret_gt5pct"]),
            "cluster_ci95": nh["bootstrap_papers"]["mismatch_fraction_ci95"],
        },
        "extraction": {
            "SI_meoh_selectivity": [int(accuracies["SI","S_MeOH"][v]) for v in
                                    ("n_correct_strict","n_extracted")],
            "SI_STY": [int(accuracies["SI","STY"][v]) for v in
                        ("n_correct_strict","n_extracted")],
        },
        "alloy": {
            "transition_below_Fe": alloy["extended_transition_metals_only"]["below_Fe"],
            "full_below_Fe": alloy["extended_with_usgs_prices"]["below_Fe"],
            "restricted_family_result": alloy["extended_excluding_sp_and_group3to5"][
                "below_Fe_either_route_all_3d_plus_group6"],
        },
    }
    m = evidence["methanol"]
    errors = []
    def check(test, why):
        if not test:
            errors.append(why)
    check(n_groups == m["groups"], "S5 selected comparison-group population mismatch")
    check(int(lab["groups"]) == m["groups"], "Main methanol denominator mismatch")
    check(m["mismatches"] == m["crosscheck_lab"], "S5 and conversion-fixed leaderboard counts differ")
    check(int(lab["gt5pct"]) == m["gt5pct"], "S5 and conversion-fixed cost-regret counts differ")
    check(m["multi_catalyst_groups"] == int(kind_lab["multi_catalyst_groups"]),
          "Multi-material eligible groups differ")
    check(m["different_catalyst_lab"] + m["same_catalyst_temperature_lab"] == m["mismatches"],
          "Laboratory mismatch classification count does not close")
    check(m["different_catalyst_adjustable"] +
          m["same_catalyst_temperature_adjustable"] == m["adjustable_mismatches"],
          "Adjustable mismatch classification count does not close")
    check(m["temperature_series_groups_strict"] <= m["temperature_series_groups_legacy"],
          "Temperature unique series exceeds legacy row-based series")
    return evidence, errors


DOCS = (
    "docs/MANUSCRIPT_MAIN_TEXT.md", "docs/MAIN_FIGURE_CAPTIONS.md",
    "docs/SUPPLEMENTARY_INFORMATION.md", "docs/SI_TABLES.md",
    "figures/extended_data/ED_CAPTIONS.md",
)


def inspect_docs(root, evidence):
    files = {p: (root/p).read_text(encoding="utf-8").splitlines()
             for p in DOCS if (root/p).is_file()}
    issues = []
    def flag(rule, severity, path, needle, claim, action):
        for line_no, content in enumerate(files.get(path, []), 1):
            if re.search(needle, content, flags=re.I):
                issues.append(dict(rule=rule, severity=severity, path=path,
                                   line=line_no, excerpt=content[:240],
                                   claim=claim, required_action=action))
                break
    m, n = evidence["methanol"], evidence["ammonia"]
    main, captions, note, tables, ext = DOCS
    for doc in (main, captions, note):
        flag("ME_OH_PRIMARY", "BLOCKER", doc,
             r"(33\s+(?:of\s+)?83|33/83|40%\s+of\s+methanol|\b83\s+comparisons)",
             f"Current S5 printed: {m['mismatches']}/{m['groups']} across {m['papers']} papers.",
             "Regenerate narrative, paper-cluster CI, Fig. 2 and source data.")
        flag("NH3_PRIMARY", "BLOCKER", doc,
             r"(44\s+(?:of\s+)?124|44/124|35%\s+of\s+ammonia|\b124\s+comparisons)",
             f"Printed ammonia: {n['mismatches']}/{n['groups']}.",
             "Use printed-only ammonia cohort and its own bootstrap.")
    flag("ME_OH_OLD_CI", "BLOCKER", main, r"24\s*[–-]\s*55%",
         "An 83-group bootstrap cannot quantify uncertainty for the selected 40 groups.",
         "Resample independent papers within the selected comparison cohort.")
    flag("NH3_OLD_CI", "BLOCKER", main, r"18\s*[–-]\s*52%",
         "An 124-group bootstrap does not describe the 33-group printed-only cohort.",
         "Use the printed ammonia source bootstrap, not the old CI.")
    flag("EXTRACTION_OVERCLAIM", "BLOCKER", main,
         r"transcribes printed values exactly|remaining errors are plot readings|exact transcription of printed values",
         f"Printed SI MeOH selectivity {evidence['extraction']['SI_meoh_selectivity']} "
         f"and STY {evidence['extraction']['SI_STY']} are not 100% correct.",
         "Use source-specific accuracy counts; do not claim all printed values were exact.")
    flag("ALLOY_DOMAIN", "BLOCKER", main,
         r"Among transition.metal alloys, only cheap|only cheap 3d.{0,16}group.6",
         f"The unrestricted transition-metal subset has {evidence['alloy']['transition_below_Fe']} "
         "below Fe; the 3d/group-6 claim needs a restricted family.",
         "Write the chemical-domain exclusion explicitly, including in the abstract.")
    flag("METHANOL_METHOD", "BLOCKER", main,
         r"space.time.yield leader is not the plant.cost leader in 33",
         "Group includes comparison of different catalysts and of one catalyst at different temperatures.",
         f"Report {m['different_catalyst_lab']}/{m['multi_catalyst_groups']} catalyst "
         f"and {m['same_catalyst_temperature_lab']}/{m['temperature_series_groups_strict']} temperature.")
    flag("AGENT_BOUND_NAME", "WARNING", captions, r"descriptor.only lower bound decides",
         "NH3 uses descriptor-only bound, whereas MeOH uses purge-wise process cost bound.",
         "Describe the scientific bound of each branch independently.")
    flag("ED2_OLD", "BLOCKER", ext, r"906 methanol literature candidates in 83",
         "Pruning results based on all entries; selected S5 has a different feasible/costed set.",
         "Rerun bound soundness and pruning counts under the frozen source protocol.")
    flag("ED3_OLD", "BLOCKER", ext, r"share of the 83 published",
         "Measurement-noise and bootstrap results describe the old all-entry population.",
         "Regenerate all ED Fig. 3 panels on the selected cohort.")
    flag("ED4_OLD", "BLOCKER", ext, r"number of the 83 comparisons",
         "Plant cost sensitivities based on an old 83-group optimization protocol.",
         "Rerun all plant variants under S5 printed; keep economic cost boundary explicit.")
    flag("SI5F_SOURCE_MISMATCH", "BLOCKER", tables,
         r"baseline reproduces the frozen headline \(54/82",
         "SI Table 5f shows 54/82 while its cited sensitivity source has "
         + m["old_benchmark_baseline"] + " and the selected S5 result is "
         + f"{m['mismatches']}/{m['groups']}.",
         "Regenerate all SI 5f variants from current source, not by text substitution.")
    flag("SI5F_BODY_MISMATCH", "BLOCKER", tables, r"\|\s*frozen model\s*\|\s*54/82",
         "SI baseline comes from a different model treatment.",
         "Rebuild the table and its figure from the same canonical source.")
    if not re.search(r"other catalyst|same catalyst", "\n".join(files.get(main, [])), flags=re.I):
        issues.append(dict(rule="MATERIAL_OPERATION_CONFLATION", severity="BLOCKER",
                           path=main, line=0, excerpt="",
                           claim="No explicit distinction between catalyst and temperature comparisons.",
                           required_action="Separate material identity and operating temperature conclusions."))
    return issues


def markdown(e, issues):
    m, nh3 = e["methanol"], e["ammonia"]
    lines = [
        "# Scientific claim lineage check",
        "",
        "This is a PROVISIONAL evidence review, not permission to publish or merge.",
        "",
        f"- S5 printed MeOH fixed: {m['mismatches']}/{m['groups']} (>5%: {m['gt5pct']}).",
        f"- S5 printed MeOH adjustable: {m['adjustable_mismatches']}/{m['groups']} (>5%: {m['adjustable_gt5pct']}).",
        f"- Material changes: {m['different_catalyst_lab']}/{m['multi_catalyst_groups']} fixed; "
        f"{m['different_catalyst_adjustable']}/{m['multi_catalyst_groups']} adjustable.",
        f"- True same-material temperature series: {m['temperature_series_groups_strict']} "
        f"(legacy row-based: {m['temperature_series_groups_legacy']}).",
        f"- Same-material temperature mismatch: {m['same_catalyst_temperature_lab']} fixed, "
        f"{m['same_catalyst_temperature_adjustable']} adjustable.",
        f"- NH3 printed: {nh3['mismatches']}/{nh3['groups']}, "
        f"cluster CI {nh3['cluster_ci95'][0]:.1%}–{nh3['cluster_ci95'][1]:.1%}.",
        "",
        "## Issues blocking manuscript consistency",
        "",
        "| Severity | Rule | Location | Required work |",
        "|---|---|---|---|",
    ]
    for r in issues:
        lines.append("| {} | {} | {}:{} | {} |".format(
            r["severity"], r["rule"], r["path"], r["line"],
            r["required_action"].replace("|", "/")))
    lines.append("")
    lines.append("Do not copy new percentages into old figures or sensitivity tables. "
                 "Recompute their actual input cohort, uncertainties and source-data exports first.")
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--publication-gate", action="store_true")
    args = ap.parse_args()
    evidence, errors = compute_evidence(args.root)
    issues = inspect_docs(args.root, evidence)
    blocked = sum(x["severity"] == "BLOCKER" for x in issues)
    data = dict(status="BLOCKED" if blocked else "REVIEW_READY",
                source_invariants="FAIL" if errors else "PASS",
                blocking_claims=blocked, issues=issues,
                source_errors=errors, evidence=evidence)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir/"claim_lineage.json").write_text(
        json.dumps(data, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    (args.out_dir/"CLAIM_LINEAGE_REVIEW.md").write_text(markdown(evidence, issues), encoding="utf-8")
    print(json.dumps({k:data[k] for k in ("status","source_invariants",
                                         "blocking_claims","source_errors")},
                     ensure_ascii=False, indent=2))
    if errors:
        return 2
    return int(args.publication_gate and blocked > 0)


if __name__ == "__main__":
    raise SystemExit(main())
