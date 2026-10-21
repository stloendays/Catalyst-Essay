"""Source-type ledger of the 100 sampled extracted methanol values (supervisor item P2, 2026-10-20).

Input: the row-level source evidence of the 100-value sample (10 papers x 10 values, seed 20261008),
analysis/verify_2026_10_08/gold_standard_human_review_2026_10_12/methanol_gold_standard_100_source_evidence.csv.
Each value is assigned one source type, by where the paper gives it:

  printed, table          a table cell of the main text or the Supporting Information
  printed, text/caption   a sentence of the text, a figure or table caption, or a table footnote
  derived                 calculated from printed numbers (H2/CO2 from a printed feed composition)
  plot-read               read off a plotted curve or bar (none in this sample)

A value is correct when its number and qualifier agree with the paper and it is attached to an entry for which the
paper reports it under the metric it names. The sample has two errors:
  #40 (Frei et al. 2019): the CO2 conversion of 9.7% is printed in the text on the 500 h stability test (Fig. 6), but
      the extraction attached it to the Table 2 entry, and Table 2 has no conversion column. Its effect on the
      comparisons is computed below from the costed candidates; the catalyst-level counts are unaffected because both
      records belong to one catalyst.
  #99 (Ota et al. 2012): Table 2 prints a methanol formation rate, 0.3 umol per gram of catalyst per minute, and the
      extraction recorded it as a printed STY without the paper's metric name. The value converts to the STY the model
      uses (checked below), so no comparison changes.

Plot-read values do not occur in the sample, so their accuracy is taken from the comparison with the curated datasets
(agent/extraction/eval/field_accuracy_by_source.csv, strict tolerance), with its own denominators.

    python build_ledger.py  -> ledger_100.csv, summary.json
"""
import json
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
EVIDENCE = (REPO / "analysis/verify_2026_10_08/gold_standard_human_review_2026_10_12"
            / "methanol_gold_standard_100_source_evidence.csv")
BY_SOURCE = REPO / "agent/extraction/eval/field_accuracy_by_source.csv"
POOLED = REPO / "analysis/meoh_field_pooled_2026_10_15/pooled_candidates.csv"

ERRORS = {40: "conversion printed for the 500 h stability test (text, Fig. 6) attached to the Table 2 entry; "
              "Table 2 has no conversion column",
          99: "methanol formation rate printed in µmol per gram of catalyst per minute recorded as a printed STY "
              "without the paper's metric name; the value converts to the same STY"}
NOTES = {93: "upper bound '<0.1%' kept as extracted (qualifier '<'); printed in the methods text"}
M_MEOH = 32.04                       # g/mol
TEXT_MARKS = ("caption", "footnote", "reaction conditions", "text", "prose", "paragraph", "activity testing")
TYPES = ["printed, table", "printed, text/caption", "derived", "plot-read"]


def source_type(r):
    if r.source_evidence_class == "组成或比值推导":
        return "derived"
    loc = str(r.precise_table_figure_location).lower()
    if any(m in loc for m in TEXT_MARKS) or not loc.startswith("table"):
        return "printed, text/caption"
    return "printed, table"


def frei_effect():
    """Verdicts of the Frei 2019 48 NL/g/h group with and without the erroneous Table 2 record."""
    sys.path.insert(0, str(REPO / "analysis/meoh_s6_robustness_2026_10_13"))
    import run_frozen_columns  # noqa: E402,F401  (puts the frozen methanol modules on sys.path)
    from meoh_candidates import aggregate  # noqa: E402
    c = pd.read_csv(POOLED)
    grp = "10.1038/s41467-019-11349-9 | 50 bar | H2/CO2 4 | 48 NL/g/h"
    bad = c[(c.group == grp) & c.entry.str.startswith("Table 2 Pd–In2O3 CP")].index
    assert len(bad) == 1
    out = {}
    for name, col in (("inlet_limited", "cost_recycled_opt_inlet"), ("no_limit", "cost_recycled_opt")):
        res = {}
        for label, d in (("as_extracted", c), ("corrected", c.drop(index=bad))):
            gm, s = aggregate(d, col)
            g = gm[gm.group == grp].iloc[0]
            res[label] = dict(disagreements=int(s["top1_mismatch_groups"]), groups=int(s["groups"]),
                              gt5pct=int((gm[gm.top1_mismatch].regret > 0.05).sum()),
                              group_disagrees=bool(g.top1_mismatch), group_regret=round(float(g.regret), 4))
        out[name] = res
    return out


def ota_effect():
    """#99: the printed rate (umol per g catalyst per min) converts to the STY (g per g catalyst per h) of the model."""
    c = pd.read_csv(POOLED)
    r = c[(c.doi == "10.1016/j.jcat.2012.05.020") & (c.entry == "Table 2, PdMgAl")]
    assert len(r) == 1
    sty = 0.3e-6 * M_MEOH * 60
    assert abs(r.STY.item() - sty) < 1e-6, (r.STY.item(), sty)
    return dict(printed_rate_umol_per_g_min=0.3, sty_g_per_g_h=round(sty, 6), model_sty=round(float(r.STY.item()), 6),
                comparisons_changed=0)


def main():
    d = pd.read_csv(EVIDENCE)
    assert len(d) == 100 and d.numeric_comparison.eq("MATCH").all()
    d["location"] = d.source_file_key.str.endswith("-SI").map({True: "Supporting Information", False: "main text"})
    d["source_type"] = d.apply(source_type, axis=1)
    d["correct"] = ~d.id.isin(ERRORS)
    d["note"] = d.id.map({**ERRORS, **NOTES}).fillna("")
    led = d[["id", "doi", "catalyst", "experimental_entry", "field", "extracted_value", "unit", "source_qualifier",
             "location", "source_type", "precise_table_figure_location", "pdf_page", "correct", "note"]]
    led.to_csv(HERE / "ledger_100.csv", index=False, encoding="utf-8")

    by_type = {t: dict(n=int((d.source_type == t).sum()), correct=int(d[d.source_type == t].correct.sum()))
               for t in TYPES}
    by_type_loc = {f"{t} | {loc}": dict(n=int(len(g)), correct=int(g.correct.sum()))
                   for (t, loc), g in d.groupby(["source_type", "location"])}
    acc = pd.read_csv(BY_SOURCE)
    plot = {f"{r.source_type} | {r.field}": dict(n=int(r.n_extracted), correct=int(r.n_correct_strict))
            for r in acc.itertuples() if r.source_type in ("plot", "SI-plot") and r.field in ("X_CO2", "S_MeOH", "STY")}
    pooled = {k: dict(n=sum(v["n"] for kk, v in plot.items() if kk.endswith(k)),
                      correct=sum(v["correct"] for kk, v in plot.items() if kk.endswith(k)))
              for k in ("X_CO2", "S_MeOH", "STY")}
    summary = dict(values=100, papers=int(d.doi.nunique()), correct=int(d.correct.sum()),
                   errors=[dict(id=int(i), doi=d.loc[d.id == i, "doi"].item(), note=n) for i, n in ERRORS.items()],
                   by_source_type=by_type, by_source_type_and_location=by_type_loc,
                   plot_read_vs_curated=dict(by_source=plot, pooled=pooled),
                   error_effect_frei_2019=frei_effect(), error_effect_ota_2012=ota_effect())
    (HERE / "summary.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("correct", "by_source_type", "error_effect_frei_2019")}, indent=1,
                     ensure_ascii=False))
    print(json.dumps(summary["plot_read_vs_curated"]["pooled"]))


if __name__ == "__main__":
    main()
