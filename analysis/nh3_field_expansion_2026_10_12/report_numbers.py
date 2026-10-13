"""Collect every number of REPORT.md from the run folders -> report_numbers.json (no new computation beyond counting).

Sets: round 1 (frozen, analysis/nh3_field_2026_10_06), batch 2 (runs/batch2_corrected; uncorrected runs/batch2),
pooled (runs/pooled), and the sensitivities runs/batch2_corrected_units, runs/pooled_units, runs/pooled_single_chain.
Cross-metal group: a scored group whose entries hold more than one metal (a fused-Fe reference counts as Fe).
"""
import json
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
SETS = {"round1": REPO / "analysis" / "nh3_field_2026_10_06", "batch2": HERE / "runs" / "batch2_corrected",
        "pooled": HERE / "runs" / "pooled", "batch2_uncorrected": HERE / "runs" / "batch2",
        "pooled_uncorrected": HERE / "runs" / "pooled_uncorrected",
        "batch2_units": HERE / "runs" / "batch2_corrected_units", "pooled_units": HERE / "runs" / "pooled_units",
        "pooled_single_chain": HERE / "runs" / "pooled_single_chain",
        # with Supporting Information (2026-10-13)
        "batch2_si": HERE / "runs" / "batch2_si_corrected", "pooled_si": HERE / "runs" / "pooled_si",
        "batch2_si_uncorrected": HERE / "runs" / "batch2_si", "pooled_si_uncorrected": HERE / "runs" / "pooled_si_uncorrected",
        "batch2_si_units": HERE / "runs" / "batch2_si_corrected_units", "pooled_si_units": HERE / "runs" / "pooled_si_units",
        "pooled_si_single_chain": HERE / "runs" / "pooled_si_single_chain"}
CHAIN_KEYS = ("records_in", "papers_with_records", "mapped", "primary_with_cost", "flagged", "outside", "outside_reasons",
              "y_default_median", "primary_entries_after_dedup", "papers_with_primary", "removed_as_duplicate",
              "fused_reference_entries_primary", "primary_below_Fe")
VARIANTS = ["per_g_catalyst_leaderboard", "per_g_metal_leaderboard", "Ru_recovery_90pct", "bed_density_500",
            "bed_density_2500", "without_fused_Fe_references", "P_ge_5MPa", "without_paper_with_most_groups",
            "all_entries"]


def brief(s):
    if not s.get("groups"):
        return dict(groups=0)
    b = s.get("bootstrap_papers", {})
    return dict(groups=s["groups"], papers=s["papers"], entries=s["entries"], mismatch=s["top1_mismatch_groups"],
                fraction=s["top1_mismatch_fraction"], papers_with_mismatch=s["papers_with_mismatch"],
                ci95=b.get("mismatch_fraction_ci95"), paper_weighted=s["paper_weighted_mismatch_fraction"],
                paper_weighted_ci95=b.get("paper_weighted_ci95"), regret_median_mismatched=s["regret_median_mismatched"],
                regret_max=s["regret_max"], regret_gt5pct=s.get("regret_bins", {}).get("gt5pct"),
                kinds={k: v["groups"] for k, v in s.get("mismatch_kinds", {}).items()})


def one(d: Path):
    sp = json.loads((d / "summary_printed.json").read_text(encoding="utf-8"))
    gm = pd.read_csv(d / "group_metrics_printed.csv")
    cross = gm[gm.metals.str.contains(";")]
    p = brief(sp["primary"])
    p.update(cross_metal_groups=int(len(cross)), cross_metal_papers=sorted(cross.doi.unique()),
             cross_metal_mismatch=int(cross.top1_mismatch.sum()),
             papers_with_disagreement=sorted(gm[gm.top1_mismatch].doi.unique()),
             scored_papers=sorted(gm.doi.unique()), printed_entries=sp["entries"])
    return dict(primary=p, variants={k: brief(sp["variants"][k]) for k in VARIANTS if k in sp["variants"]})


def main():
    out = {k: one(v) for k, v in SETS.items()}
    scr = pd.read_csv(HERE / "batch2_screening.csv")
    out["screening"] = dict(screened=int(len(scr)), included=int((scr.decision == "include").sum()),
                            excluded={r.doi: r.reason for r in scr[scr.decision == "exclude"].itertuples()})
    s2 = json.loads((SETS["batch2"] / "summary.json").read_text(encoding="utf-8"))
    out["batch2_chain"] = {k: s2[k] for k in CHAIN_KEYS}
    out["batch2_chain"]["all_entries_primary"] = brief(s2["primary"])
    s3 = json.loads((SETS["batch2_si"] / "summary.json").read_text(encoding="utf-8"))
    out["batch2_si_chain"] = {k: s3[k] for k in CHAIN_KEYS}
    out["batch2_si_chain"]["all_entries_primary"] = brief(s3["primary"])
    tok = pd.read_csv(REPO / "agent" / "nh3_field" / "out_batch2" / "token_usage.csv")
    g = tok.groupby("pass").agg(calls=("doi", "size"), prompt=("prompt_tokens", "sum"),
                                output=("completion_tokens", "sum"), reasoning=("reasoning_tokens", "sum"),
                                total=("total_tokens", "sum"), records=("n_records", "sum"))
    si_task = tok.timestamp >= "2026-10-13"
    out["tokens_si_task"] = dict(by_pass=tok[si_task].groupby("pass").agg(calls=("doi", "size"),
                                 total=("total_tokens", "sum"), records=("n_records", "sum")).to_dict("index"),
                                 total=int(tok[si_task].total_tokens.sum()), prompt=int(tok[si_task].prompt_tokens.sum()),
                                 output=int(tok[si_task].completion_tokens.sum()), route="api-yes only",
                                 cost_usd_at_5_30_per_M=round(tok[si_task].prompt_tokens.sum() / 1e6 * 5
                                                              + tok[si_task].completion_tokens.sum() / 1e6 * 30, 2))
    out["tokens"] = dict(by_pass=g.to_dict("index"), total=int(tok.total_tokens.sum()),
                         prompt=int(tok.prompt_tokens.sum()), output=int(tok.completion_tokens.sum()),
                         cost_usd_at_5_30_per_M=round(tok.prompt_tokens.sum() / 1e6 * 5 + tok.completion_tokens.sum() / 1e6 * 30, 2))
    chk = pd.read_csv(HERE / "batch2_pdf_check.csv")
    out["pdf_check"] = dict(n=int(len(chk)), verdicts=chk.verdict.value_counts().to_dict(),
                            by_field=chk.field.value_counts().to_dict())
    chk2 = pd.read_csv(HERE / "batch2_si_pdf_check.csv")
    out["si_pdf_check"] = dict(n=int(len(chk2)), verdicts=chk2.verdict.value_counts().to_dict(),
                               by_field=chk2.field.value_counts().to_dict())
    sim = json.loads((HERE / "batch2_si_manifest.json").read_text(encoding="utf-8"))
    out["si_fetch"] = dict(status={k: int(v) for k, v in pd.Series([r["status"] for r in sim]).value_counts().items()},
                           none=[r["doi"] for r in sim if r["status"] != "ok"])
    out["si_corrections"] = int(len(pd.read_csv(HERE / "batch2_si_corrections.csv")))
    out["corrections"] = int(len(pd.read_csv(HERE / "batch2_corrections.csv")))
    out["unit_completions"] = int(len(pd.read_csv(HERE / "batch2_unit_completions.csv")))
    (HERE / "report_numbers.json").write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8")
    print(json.dumps({k: out[k]["primary"] for k in SETS}, indent=1, default=float))


if __name__ == "__main__":
    main()
