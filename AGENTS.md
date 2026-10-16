# Instructions for Codex and repository editing agents

This repository contains a scientific manuscript, frozen computational benchmarks and historical experimental records. Before editing manuscript-facing files, read [docs/MANUSCRIPT_EDITORIAL_LOCKS.md](docs/MANUSCRIPT_EDITORIAL_LOCKS.md), particularly **LOCK-06** on the methanol second cohort. Also use the latest [docs/MANUSCRIPT_MAIN_TEXT.md](docs/MANUSCRIPT_MAIN_TEXT.md) and source result tables rather than old README numbers.

## Mandatory methanol manuscript presentation (author direction, 2026-10-16)

- **Unified-paper framing:** Discuss the field-scale CO₂-to-methanol analysis as **81 within-paper comparison groups from 50 publications**, processed and rescored consistently. The headline outcome is **50/81 (61.7%)** STY-leader vs model-economic-leader differences, with **42/81** exceeding 5% modeled cost regret.
- **Do not present this as "two times", "two experiments", "first cohort vs second cohort", successive extractions or repeated 28/40 vs 22/41 headline counts** in Abstract, Results, Discussion, the main figures/captions, paper title, or author-facing executive summaries. Describe the pooled sample and its process-constraint, selectivity, purge and recycle mechanisms.
- Avoid organizing the paper's main narrative around internal `P1`/`P2`/`PASS`/`FAIL` tags. Do not claim an overall independent prospective validation passed; do not overstate relative selectivity performance or industrial model validation.
- **Preserve factual methods/provenance:** the papers did enter through distinct collection windows; Methods/SI should give sufficient inclusion and extraction detail to reproduce the combined corpus and keep the original experiment's historical result accessible. Never state that all 81 were gathered as one original preregistered batch.
- **Preserve the completed negative pre-specified outcome.** The source registration/report remains unchanged in `analysis/validation_meoh_prospective_2026_10_13/`: the 22/41 S6 rate (53.7%) narrowly missed its originally pre-specified lower interval limit (54.1%); the 28/41 selectivity-rule-vs-chance test passed. Explain this concisely in Methods/SI or accessible scientific support, not as a headline banner. Pooled totals do not retroactively amend the registered criterion.
- Optional SI-figure extraction was partially curtailed by a token cap, while the primary printed-value dataset was fully scored; never imply the latter was incomplete due to compute limits.
- An editorial instruction to unify the story changes **presentation**, not source records, outcomes, or provenance. See **LOCK-06** for the complete policy.

## Editing workflow

- Change only the files needed for the requested task. Never silently mutate frozen scientific data, benchmark scoring or historical validation records.
- For new scientific results, keep source-to-claim traceability, demonstrate numerical anchors in CI and maintain qualification between model-conditioned results, cross-validation and independent industrial observations.
- Editing prose to improve clarity is allowed; changing facts or concealing a known contradictory outcome is not. When there is a difference between a reader-facing summary and historical experimental acceptance criteria, retain both at their appropriate evidential levels.
