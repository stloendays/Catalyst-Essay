# Instructions for Codex and repository editing agents

This repository contains a scientific manuscript, frozen computational benchmarks and historical experimental records. Before editing manuscript-facing files, read [docs/MANUSCRIPT_EDITORIAL_LOCKS.md](docs/MANUSCRIPT_EDITORIAL_LOCKS.md), particularly **LOCK-06** on the methanol second cohort. Also use the latest [docs/MANUSCRIPT_MAIN_TEXT.md](docs/MANUSCRIPT_MAIN_TEXT.md) and source result tables rather than old README numbers.

## Mandatory methanol manuscript framing (author direction, 2026-10-16)

- Present the second independent literature-cohort analysis as a **follow-up literature–computational replication experiment** and the complete 81-group set as the manuscript synthesis. The earlier pre-registered P1/P2 binary labels are **not** the manuscript's headline success criterion and must not drive Abstract/Results/figure-caption organization.
- Use the actually computed cohort results: 28/40 first-cohort and 22/41 second-cohort STY-to-model-cost leader differences; 50/81 overall, including 42/81 economically consequential (>5% regret) disagreements. Interpret changes in prevalence across cohorts directly. Do not recast source-cost optimization as measured industrial adoption.
- Preserve the complete **historical** pre-registration, predictions, evaluation and deviations in `analysis/validation_meoh_prospective_2026_10_13/`. The originally specified S6 rate-interval criterion was narrowly missed (22/41 = 53.7%, lower bound 54.1%); the separately defined rule-versus-chance criterion passed (28/41). Disclose these accurately in Methods/SI or a clearly accessible supporting report, without requiring conspicuous P1/P2 labels in the main narrative.
- Do not claim the missed original criterion was caused by the compute/token limit: only the optional SI-figure extraction was interrupted, whereas the principal printed-value cohort was scored. Do not replace the original endpoint after seeing the results or claim the original pre-registered validation fully passed.
- An editorial change made after observing outcomes must be described as **a new framing choice**, not a modification of the previously fixed experimental plan. Preserve all source provenance, numerical tables, accepted/rejected cases and reproducibility links.

## Editing workflow

- Change only the files needed for the requested task. Never silently mutate frozen scientific data, benchmark scoring or historical validation records.
- For new scientific results, keep source-to-claim traceability, demonstrate numerical anchors in CI and maintain qualification between model-conditioned results, cross-validation and independent industrial observations.
- Editing prose to improve clarity is allowed; changing facts or concealing a known contradictory outcome is not. When there is a difference between a reader-facing summary and historical experimental acceptance criteria, retain both at their appropriate evidential levels.
