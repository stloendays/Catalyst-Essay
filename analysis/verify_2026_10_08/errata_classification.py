"""Classify every correction made to the reference datasets, so that only definite errors are reported as errata.

Inputs: agent/extraction/eval/errata_applied.csv (TheMeCat and Suvarna 2022, cell level, with the evidence text of
the rule that changed the cell) and agent/nh3_supported/out/primary_errata.csv (Humphreys 2021 review, cell level).

Unit of counting: one error = one rule (TheMeCat / Suvarna: the same paper, field and evidence text; Humphreys: one
review row and the fields one finding changes together). Cells are reported alongside.

Proposed classes (a person confirms every row against the paper before any count is published):
  E-unit        unit or order of magnitude (MPa stored as bar, x10 space velocity, x100 selectivity)
  E-assignment  value attached to the wrong catalyst, series or condition (swapped series, wrong temperature step,
                wrong catalyst label, row that belongs to another material or paper)
  E-value       printed value differs from the dataset value by more than 2 % for another reason
  C-convention  dataset derives the value (STY from X x S x F) where the paper prints its own number; a difference of
                definition, not a transcription error
  C-derived     follows from another error of the same entry (e.g. an STY computed from a wrong selectivity)
  N-minor       difference of 2 % or less (reading or rounding); not counted as an erratum
Output: errata_classification.csv (one row per cell), errata_rules.csv (one row per error), errata_summary.json.
"""
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]

CONV = re.compile(r"computes? it from X|computed from X|matches X x S x F|X x S x F\)|recomput|recalcul", re.I)
DERIVED = re.compile(r"carries into it|follows from|inherits", re.I)
UNIT = re.compile(r"as bar\b|stores [\d.]+ MPa|\b10x\b|\b100x\b|order of magnitude|per g Cu|per-g-metal", re.I)
ASSIGN = re.compile(r"swap|lists? .* under|vice versa|belong|labels? it|is pristine|Ru-free|one temperature step|"
                    r"not tested|wrong catalyst|moved to the right|instead of|reduction flow|volumetric flow", re.I)


def classify(field, rel, ev):
    ev = str(ev)
    if "Ru-free" in ev or "no Ru" in ev or "without Ru" in ev:
        return "E-assignment"
    if field in ("(row dropped)", "(row)"):
        return "E-assignment"
    if DERIVED.search(ev):
        return "C-derived"
    if CONV.search(ev):
        return "C-convention"
    if field == "catalyst_name":
        return "E-assignment"
    if rel is not None and not np.isnan(rel) and rel <= 0.02:
        return "N-minor"
    if UNIT.search(ev):
        return "E-unit"
    if ASSIGN.search(ev):
        return "E-assignment"
    return "E-value"


def main():
    a = pd.read_csv(REPO / "agent" / "extraction" / "eval" / "errata_applied.csv")
    old, new = pd.to_numeric(a.themecat, errors="coerce"), pd.to_numeric(a.pdf, errors="coerce")
    a["rel_diff"] = (new - old).abs() / pd.concat([new.abs(), old.abs()], axis=1).max(axis=1)
    a["dataset"] = a.ref.map({"themecat": "TheMeCat", "suvarna": "Suvarna 2022"})
    a = a.rename(columns={"themecat": "dataset_value", "pdf": "paper_value", "evidence": "evidence"})
    a["rule"] = a.dataset + " | " + a.doi + " | " + a.field + " | " + a.evidence.astype(str)

    h = pd.read_csv(REPO / "agent" / "nh3_supported" / "out" / "primary_errata.csv")
    # a row the review assigns to Ru that the paper measured without Ru is one error, whatever fields it touches
    ru_free = set(h.loc[h.paper_value.astype(str).str.contains("Ru-free"), "row"].astype(str)
                  + "@" + h.loc[h.paper_value.astype(str).str.contains("Ru-free"), "page"].astype(str))
    h_key = h.row.astype(str) + "@" + h.page.astype(str)
    hv, hn = pd.to_numeric(h.review_value, errors="coerce"), pd.to_numeric(h.paper_value, errors="coerce")
    h = pd.DataFrame(dict(dataset="Humphreys 2021 review", doi="", catalyst_name="", field=h.field,
                          dataset_value=h.review_value, paper_value=h.paper_value, evidence=h.paper_locator,
                          rel_diff=(hn - hv).abs() / pd.concat([hn.abs(), hv.abs()], axis=1).max(axis=1),
                          rule="Humphreys | p" + h.page.astype(str) + " row " + h.row.astype(str)
                          + np.where(h_key.isin(ru_free), " | Ru-free row", " | " + h.field)))
    cells = pd.concat([a[["dataset", "doi", "catalyst_name", "field", "dataset_value", "paper_value", "rel_diff",
                          "evidence", "rule"]], h], ignore_index=True)
    cells["proposed_class"] = [classify(f, r, e) for f, r, e in zip(cells.field, cells.rel_diff, cells.evidence)]
    cells["human_check"] = ""
    cells.to_csv(HERE / "errata_classification.csv", index=False, encoding="utf-8-sig", float_format="%.6g")

    rules = (cells.groupby("rule").agg(dataset=("dataset", "first"), doi=("doi", "first"), field=("field", "first"),
                                       cells=("field", "size"), proposed_class=("proposed_class",
                                                                                lambda s: s.mode().iloc[0]),
                                       classes=("proposed_class", lambda s: ";".join(sorted(set(s)))),
                                       max_rel_diff=("rel_diff", "max"), evidence=("evidence", "first"))
             .reset_index())
    rules.to_csv(HERE / "errata_rules.csv", index=False, encoding="utf-8-sig", float_format="%.6g")
    errors = rules[rules.proposed_class.str.startswith("E")]
    summary = dict(
        cells=int(len(cells)), rules=int(len(rules)),
        cells_by_dataset=cells.dataset.value_counts().to_dict(),
        rules_by_dataset=rules.dataset.value_counts().to_dict(),
        rules_by_class=rules.proposed_class.value_counts().to_dict(),
        cells_by_class=cells.proposed_class.value_counts().to_dict(),
        errors_by_dataset=dict(rules=errors.dataset.value_counts().to_dict(),
                               cells=errors.groupby("dataset").cells.sum().to_dict(),
                               papers=errors[errors.doi != ""].groupby("dataset").doi.nunique().to_dict()),
    )
    (HERE / "errata_summary.json").write_text(json.dumps(summary, indent=1, default=int) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1, default=int, ensure_ascii=False))


if __name__ == "__main__":
    main()
