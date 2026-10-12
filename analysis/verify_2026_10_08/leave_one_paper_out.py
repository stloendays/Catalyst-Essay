"""Leave-one-paper-out check of the methanol field result: the comparisons of one paper are removed at a time.

Bansode 2013 (10.1039/c2cy20604h) alone gives 8 of the 40 comparisons, so the field result is also reported without
it. Read from the committed group metrics of the frozen primary (S5, printed values) and of its treatments; nothing is
re-optimized.

Output: leave_one_paper_out.csv (one row per treatment and removed paper), leave_one_paper_out_summary.json.
"""
import json
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
INV = HERE.parents[1] / "analysis" / "meoh_literature_inversion_2026_10_05"
TREATMENTS = {
    "S5 primary": "group_metrics.csv",
    "S6 inlet limit 6.86 %": "group_metrics_inlet_limit.csv",
    "purge grid extended": "group_metrics_purge_extended.csv",
    "inlet limit of the anchor loop, extended grid": "group_metrics_purge_anchor.csv",
}
LARGEST = "10.1039/c2cy20604h"


def stats(g):
    m = g[g.top1_mismatch]
    return dict(groups=len(g), mismatches=int(len(m)), share=len(m) / len(g) if len(g) else float("nan"),
                gap_over_5pct=int((m.regret > 0.05).sum()), papers=int(g.doi.nunique()),
                papers_with_mismatch=int(m.doi.nunique()), median_regret=float(m.regret.median()) if len(m) else 0.0,
                max_regret=float(m.regret.max()) if len(m) else 0.0)


def main():
    rows, summary = [], {}
    for name, f in TREATMENTS.items():
        g = pd.read_csv(INV / f)
        g["top1_mismatch"] = g.top1_mismatch.astype(str).eq("True")
        rows.append(dict(treatment=name, removed="none", removed_groups=0, **stats(g)))
        for doi, k in g.groupby("doi").size().items():
            rows.append(dict(treatment=name, removed=doi, removed_groups=int(k), **stats(g[g.doi != doi])))
        t = pd.DataFrame([r for r in rows if r["treatment"] == name and r["removed"] != "none"])
        summary[name] = dict(all=stats(g), without_largest_paper=stats(g[g.doi != LARGEST]),
                             loo_mismatch_range=[int(t.mismatches.min()), int(t.mismatches.max())],
                             loo_share_range=[float(t.share.min()), float(t.share.max())])
    pd.DataFrame(rows).to_csv(HERE / "leave_one_paper_out.csv", index=False, encoding="utf-8-sig", float_format="%.6g")
    summary["largest_paper"] = LARGEST
    (HERE / "leave_one_paper_out_summary.json").write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8")
    for name in TREATMENTS:
        a, w = summary[name]["all"], summary[name]["without_largest_paper"]
        print(f"{name}: {a['mismatches']}/{a['groups']} (>5 % {a['gap_over_5pct']}); without Bansode 2013 "
              f"{w['mismatches']}/{w['groups']} (>5 % {w['gap_over_5pct']}, {w['papers_with_mismatch']} of "
              f"{w['papers']} papers); leave-one-out range {summary[name]['loo_mismatch_range']}")


if __name__ == "__main__":
    main()
