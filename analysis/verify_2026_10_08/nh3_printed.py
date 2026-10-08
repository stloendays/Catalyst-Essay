"""Ammonia field result on printed values only.

Reads the committed candidates of analysis/nh3_field_2026_10_06 (costs unchanged), rebuilds the primary set of that
run (primary status, a plant cost, one entry per catalyst and measurement per group) and checks that it reproduces
the committed 44/124. Then it keeps only the entries whose values that enter the mapping are printed:

  rate per g catalyst   qualifier '=' and not taken from a plot (rate_src not plot / SI-plot)
  reaction temperature  qualifier '=' (a temperature read off a plot axis is not printed)
  outlet NH3            printed in the same sense when the entry uses it (y_source 'printed outlet'); entries whose
                        outlet comes from rate / WHSV or the set median use only the printed rate and space velocity

Groups are those of the committed run; a group is scored when at least two printed entries remain.
Outputs: nh3_printed_summary.json, nh3_printed_groups.csv.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
FIELD = REPO / "analysis" / "nh3_field_2026_10_06"
sys.path.insert(0, str(FIELD))
_argv, sys.argv = sys.argv, sys.argv[:1]
import run_field_chain as F  # noqa: E402
sys.argv = _argv

PLOT_SRC = ("plot", "SI-plot")


def main():
    c = pd.read_csv(FIELD / "candidates.csv", keep_default_na=False, na_values=[""])
    prim = c[c.status.str.startswith("primary") & c.cost_USD_t.notna() & c.duplicate_in_group.isna()].copy()
    _, ref = F.aggregate(prim, label="primary (rebuilt from candidates.csv)")
    committed = json.loads((FIELD / "summary.json").read_text(encoding="utf-8"))["primary"]
    assert (ref["groups"], ref["top1_mismatch_groups"]) == (committed["groups"], committed["top1_mismatch_groups"]), \
        (ref["groups"], ref["top1_mismatch_groups"])

    rec = pd.read_csv(REPO / "agent" / "nh3_field" / "out" / "records_normalized.csv", keep_default_na=False,
                      na_values=[""])
    q = rec[["doi", "entry_label", "T_q", "outlet_q", "outlet_src"]].rename(columns={"entry_label": "entry"})
    q = q.drop_duplicates(["doi", "entry"])
    p = prim.merge(q, on=["doi", "entry"], how="left", validate="many_to_one")
    rate_ok = (p.rate_q == "=") & ~p.rate_src.isin(PLOT_SRC)
    t_ok = p.T_q == "="
    uses_outlet = p.y_source == "printed outlet"
    outlet_ok = ~uses_outlet | ((p.outlet_q == "=") & ~p.outlet_src.isin(PLOT_SRC))
    p["printed"] = rate_ok & t_ok & outlet_ok
    p.index = prim.index

    gm_all, s_all = F.aggregate(prim, label="primary", boot=True)
    loose = prim[prim.apply(F._rank, axis=1) != 1]
    _, s_loose = F.aggregate(loose, label="rate not plot-read (committed variant)", boot=True)
    gm_pr, s_pr = F.aggregate(p[p.printed], label="printed rate, temperature and outlet", boot=True)
    for gm in (gm_all, gm_pr):
        gm["gt5pct"] = gm.top1_mismatch & (gm.regret > 0.05)
        gm["gt10pct"] = gm.top1_mismatch & (gm.regret > 0.10)
    out = {}
    for name, s, gm in (("primary", s_all, gm_all), ("rate_not_plot_read", s_loose, None),
                        ("printed", s_pr, gm_pr)):
        keep = {k: s.get(k) for k in ("variant", "groups", "papers", "entries", "top1_mismatch_groups",
                                      "top1_mismatch_fraction", "papers_with_mismatch", "regret_median_mismatched",
                                      "regret_max", "bootstrap_papers")}
        if gm is not None:
            keep["mismatch_regret_gt5pct"] = int(gm.gt5pct.sum())
            keep["mismatch_regret_gt10pct"] = int(gm.gt10pct.sum())
        out[name] = keep
    out["entries"] = dict(primary=int(len(p)), printed=int(p.printed.sum()), rate_printed=int(rate_ok.sum()),
                          T_printed=int(t_ok.sum()), outlet_used=int(uses_outlet.sum()),
                          outlet_used_printed=int((uses_outlet & outlet_ok).sum()))
    (HERE / "nh3_printed_summary.json").write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8")
    gm_pr.to_csv(HERE / "nh3_printed_groups.csv", index=False, float_format="%.6g")
    print(json.dumps(out, indent=1, default=float))


if __name__ == "__main__":
    main()
