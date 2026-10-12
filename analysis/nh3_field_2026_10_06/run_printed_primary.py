"""Frozen ammonia field result: printed values only (author decision 2026-10-08), with the variants Fig. 2c uses.

Reads candidates.csv of run_field_chain.py (plant costs unchanged), rebuilds its primary set (primary status, a plant
cost, one entry per catalyst and measurement per group) and checks that it reproduces the committed all-entries result
(summary.json, primary). The frozen primary keeps only the entries whose values that enter the mapping are printed
(the definition of analysis/verify_2026_10_08/nh3_printed.py):

  rate per g catalyst   qualifier '=' and not taken from a plot (rate_src not plot / SI-plot)
  reaction temperature  qualifier '=' (a temperature read off a plot axis is not printed)
  outlet NH3            printed in the same sense when the entry uses it (y_source 'printed outlet'); entries whose
                        outlet comes from rate / WHSV or the set median use only the printed rate and space velocity

Groups are those of the all-entries run; a group is scored when at least two printed entries remain. Variants on the
printed set: leaderboard per g catalyst and per g metal, 90 % Ru recovery, bed density 500 / 2,500 kg m-3, commercial
fused-Fe references removed, measured at >= 5 MPa, without the paper with the most groups; and the all-entries result
(plot readings included) as the sensitivity.

Outputs (this folder): summary_printed.json, group_metrics_printed.csv.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))
_argv, sys.argv = sys.argv, sys.argv[:1]
import run_field_chain as F  # noqa: E402
sys.argv = _argv

PLOT_SRC = ("plot", "SI-plot")


def regret_bins(gm):
    m = gm[gm.top1_mismatch]
    return {f"gt{int(t * 100)}pct": dict(groups=int((m.regret > t).sum()), papers=int(m[m.regret > t].doi.nunique()))
            for t in (0.01, 0.05, 0.10)}


def main():
    c = pd.read_csv(HERE / "candidates.csv", keep_default_na=False, na_values=[""])
    prim = c[c.status.str.startswith("primary") & c.cost_USD_t.notna() & c.duplicate_in_group.isna()].copy()
    prim["rate_per_gmetal"] = prim.rate_umol_gcat_h / (np.where(prim.fused, 71.51, prim.metal_wt_pct) / 100.0)
    gm_all, s_all = F.aggregate(prim, label="all entries, plot readings included", boot=True)
    committed = json.loads((HERE / "summary.json").read_text(encoding="utf-8"))["primary"]
    assert (s_all["groups"], s_all["top1_mismatch_groups"]) == (committed["groups"], committed["top1_mismatch_groups"])

    rec = pd.read_csv(REPO / "agent" / "nh3_field" / "out" / "records_normalized.csv", keep_default_na=False,
                      na_values=[""])
    q = rec[["doi", "entry_label", "T_q", "outlet_q", "outlet_src"]].rename(columns={"entry_label": "entry"})
    p = prim.merge(q.drop_duplicates(["doi", "entry"]), on=["doi", "entry"], how="left", validate="many_to_one")
    p.index = prim.index
    rate_ok = (p.rate_q == "=") & ~p.rate_src.isin(PLOT_SRC)
    t_ok = p.T_q == "="
    uses_outlet = p.y_source == "printed outlet"
    outlet_ok = ~uses_outlet | ((p.outlet_q == "=") & ~p.outlet_src.isin(PLOT_SRC))
    p["printed"] = rate_ok & t_ok & outlet_ok
    pr = p[p.printed].copy()

    gm, primary = F.aggregate(pr, label="primary: printed rate, temperature and outlet; paper's own rate basis, "
                                        "plant cost without metal recovery", boot=True)
    primary["regret_bins"] = regret_bins(gm)
    variants = {
        "per_g_catalyst_leaderboard": F.aggregate(pr, up_col="rate_umol_gcat_h", label="rate per g catalyst",
                                                  boot=True)[1],
        "per_g_metal_leaderboard": F.aggregate(pr, up_col="rate_per_gmetal", label="rate per g metal", boot=True)[1],
        "Ru_recovery_90pct": F.aggregate(pr.assign(cost_rec=pr.cost_recovery90.fillna(pr.cost_USD_t)),
                                         cost_col="cost_rec", label="90 % Ru recovery", boot=True)[1],
        "bed_density_500": F.aggregate(pr.assign(c5=pr.cost_bed500.where(~pr.fused, pr.cost_USD_t)), cost_col="c5",
                                       label="bed density 500 kg/m3")[1],
        "bed_density_2500": F.aggregate(pr.assign(c25=pr.cost_bed2500.where(~pr.fused, pr.cost_USD_t)),
                                        cost_col="c25", label="bed density 2,500 kg/m3")[1],
        "without_fused_Fe_references": F.aggregate(pr[~pr.fused], label="commercial fused-Fe references removed",
                                                   boot=True)[1],
        "P_ge_5MPa": F.aggregate(pr[pr.P_MPa >= 5.0], label="measured at >= 5 MPa", boot=True)[1],
        "all_entries": s_all,
    }
    variants["all_entries"]["regret_bins"] = regret_bins(gm_all)
    big = gm.groupby("doi").size().idxmax()
    variants["without_paper_with_most_groups"] = F.aggregate(pr[pr.doi != big], label=f"without {big}")[1]
    entries = dict(all_entries=int(len(p)), printed=int(p.printed.sum()), rate_printed=int(rate_ok.sum()),
                   T_printed=int(t_ok.sum()), outlet_used=int(uses_outlet.sum()),
                   outlet_used_printed=int((uses_outlet & outlet_ok).sum()))
    out = dict(treatment="printed values only", entries=entries, primary=primary, variants=variants)
    (HERE / "summary_printed.json").write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8")
    gm.to_csv(HERE / "group_metrics_printed.csv", index=False, float_format="%.6g")
    print(json.dumps(out, indent=1, default=float))
    print(f"\nprimary {primary['top1_mismatch_groups']}/{primary['groups']} groups ({primary['papers_with_mismatch']}"
          f"/{primary['papers']} papers), regret > 5 %: {primary['regret_bins']['gt5pct']['groups']}")


if __name__ == "__main__":
    main()
