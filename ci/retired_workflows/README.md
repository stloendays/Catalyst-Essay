# Retired workflows

Workflow files moved here no longer run (GitHub only runs files under `.github/workflows/`). They are kept with
their history so a past run can still be read against the file that produced it.

| File | Retired | Why |
|---|---|---|
| `post-closure-doc-sync.yml` | 2026-10-07 | It rewrote marked sections of `README.md`, `STATUS.md` and the v6 manuscript skeleton after the September closures and pushed them to `main`. The README section it looks for (`## Cross-reaction economic leverage — quantitative ratio on hold`) was removed when the README was rewritten, so every run since 2026-09-10 failed at "start marker not found"; the documents it synchronised are superseded by `docs/MANUSCRIPT_MAIN_TEXT.md`, `docs/SUPPLEMENTARY_INFORMATION.md` and `STATUS.md`. Its checks of the live text are done by `tools/audit_live_manuscript_truth.py` (workflow `manuscript-number-audit.yml`). |
