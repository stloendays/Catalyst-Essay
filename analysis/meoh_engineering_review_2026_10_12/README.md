# Decision-accounting audit: hold the original laboratory champion fixed

**Unfrozen post-analysis of engineering-envelope results.** Read-only. This adds no optimization, edits no data, and does not change the frozen methanol S5 or the published version of PR #55.

## Why this is necessary

The existing `meoh_candidates.aggregate()` intentionally filters candidate designs with nonfinite TEA cost, then reselects the highest-STY laboratory leader among the remaining feasible candidates. This is a valid **ranking among the feasible subset**. It is not automatically equivalent to asking whether **the laboratory leader from the original published comparison** remains competitive at industrial scale.

When a physical envelope excludes the originally top-STY catalyst, comparing the two best of the remaining candidates can create a new inversion. Calling it an inversion of the original experimental ranking would shift the scientific estimand.

## Fixed-original-champion taxonomy

Every one of the original 40 groups is classified into exactly one category for each combination of loading upper bound, published inlet design envelope, and source-scaled equipment caps:

| Category | Interpretation | Contributes to economic inversion denominator? |
|---|---|---|
| **Original top-STY leader feasible** | At least two candidates can be built, including at least one of the original top-STY entries. Assess raw-STY-champion vs cheapest feasible candidate and regret. | **Yes** |
| **Original top-STY leader infeasible** | At least two candidates remain, but *all* original STY champions are infeasible. | **No** — the source champion cannot be compared |
| **One feasible candidate** | Only one candidate in the original group satisfies constraints. | **No**, ranking is impossible |
| **No feasible candidate** | All candidates fail the process envelope. | **No** |

For tied original STY maximum entries, use the cheapest *feasible* tied original winner; if none remains, the group is "original top-STY leader infeasible". A material reversal requires (1) original winner feasible, (2) another feasible catalyst with lower process/TEA cost, (3) regret >5%, and (4) for same-temperature cross-catalyst claims, distinct catalyst identities at identical experimental temperature. In addition, report paper-cluster bootstrap only on the eligible group subset.

The baseline `m=10, uncapped equipment` scenario MUST reproduce PR #55 group mismatch/regret counts, which guards against accidentally changing the original approach. The new 56-case screen never mutates the base PR #56 optimization or the source-data records.

## Interpretation

- Report **both** ranking-among-feasible-subset and fixed-original-STY-leader results with explicit denominators.
- If a constraint eliminates the original champion, record a **feasibility finding**, not a "ranking agrees" or "ranking inverts" finding.
- The process-anchored equipment ratios are **illustrative**, not physically established bed size or pressure-drop limits. The fixed 1.5-bar loop pressure drop is not a hydraulic model.
- Independently verify original papers' STY basis, CO/CH4 selectivity and inert dilution. The source consistency audit is separate at `analysis/meoh_survivor_source_2026_10_12/`.
- This is a post-hoc analysis. The paper should not present the three-envelope intersection as a registered, independently replicated experiment.

## Reproduce

```bash
pip install -r requirements.txt
python -m unittest discover -s analysis/meoh_engineering_review_2026_10_12/tests -v
python analysis/meoh_engineering_review_2026_10_12/audit_fixed_sty_leader.py
python analysis/meoh_survivor_source_2026_10_12/audit_survivor_sources.py
```

Results are written to `analysis/meoh_engineering_review_2026_10_12/results/` and `analysis/meoh_survivor_source_2026_10_12/results/` respectively.
