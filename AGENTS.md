# Instructions for Codex and repository editing agents

This repository contains a scientific manuscript, frozen computational benchmarks and historical experimental records. Before editing manuscript-facing files, read [docs/MANUSCRIPT_EDITORIAL_LOCKS.md](docs/MANUSCRIPT_EDITORIAL_LOCKS.md), Also use the latest [docs/MANUSCRIPT_MAIN_TEXT.md](docs/MANUSCRIPT_MAIN_TEXT.md) and source result tables rather than old README numbers.

## Methanol manuscript presentation (LOCK-06, archived 2026-10-19)

The former mandatory methanol presentation rules (LOCK-06) were archived by author decision on 2026-10-19 and are no
longer enforced. Their text is kept under "Archived locks" in
[docs/MANUSCRIPT_EDITORIAL_LOCKS.md](docs/MANUSCRIPT_EDITORIAL_LOCKS.md); the prospective-test records stay unchanged in
`analysis/validation_meoh_prospective_2026_10_13/`.

## Editing workflow

- Change only the files needed for the requested task. Never silently mutate frozen scientific data, benchmark scoring or historical validation records.
- For new scientific results, keep source-to-claim traceability, demonstrate numerical anchors in CI and maintain qualification between model-conditioned results, cross-validation and independent industrial observations.
- Editing prose to improve clarity is allowed; changing facts or concealing a known contradictory outcome is not. When there is a difference between a reader-facing summary and historical experimental acceptance criteria, retain both at their appropriate evidential levels.
