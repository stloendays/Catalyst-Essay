# NH3-FINAL-1.1 provenance pointer

Recorded: **2026-09-10** during the manuscript claim-to-evidence audit.

## Scope

This file records the known immutable/source paths for the canonical **NH3-FINAL-1.1** result. It is a provenance pointer, not a copy of the raw computational package.

The source-harness record in the project knowledge base states that NH3-FINAL-1.1 was manually promoted to canonical on **2026-09-05** after an independent pressure-CAPEX audit and a consistency closure. All current NH3 ground-truth quantities were recomputed from the same canonical run.

## Canonical source run

- canonical run: `outputs/nh3_final_20260905T134204Z`
- consistency-closure directory: `outputs/nh3_final_20260905T134204Z/closure/`
- canonical config after promotion: `configs/nh3_final.yaml`
- archived predecessor config: `configs/nh3_final_1.0_archived.yaml`

The closure directory is recorded as containing the current:

- rolling Spearman/Kendall outputs;
- 1,000-draw Monte Carlo results;
- Ru activity break-even scan;
- scaling-reachability outputs;
- Layer-B lever outputs.

## Promotion / audit records in the source harness

- `PRESSURE_CAPEX_INDEPENDENT_AUDIT_2026-09-05.md`
- `audits/audit_pressure_capex_handcalc_2026-09-05.py`
- full-mode perturbation runs: `outputs/s11_*`
- `PROMOTE_NH3_FINAL_1_1_CHECKLIST.md`
- `NH3_FINAL_1_1_CONSISTENCY_CLOSURE.md`

The project record states that the independent audit reproduced the Fe/Ru cost pools to 1e-6, that the 1.1 full-mode run was repeated independently with identical values, and that 31 tests passed at promotion. Those source files/tests are not currently vendored in `Catalyst-Essay`, so this statement remains a pointer to the source harness rather than a locally executable verification.

## Figure provenance in the source harness

The project record states that **F1-F6 were redrawn from the NH3-FINAL-1.1 consistency closure into the source harness `figures/` directory**. Those current F1-F6 assets are not present in the `Catalyst-Essay/figures/` tree as of this audit.

Therefore:

- current NH3 manuscript numbers may continue to use `data/canonical_results_2026-09-06.csv` as the compact canonical snapshot;
- F1-F6 remain **HOLD** for final figure locking until the source-harness figure/data files are imported or content-addressed;
- NH3-FINAL-1.0 workbooks must not be substituted for the missing 1.1 provenance.

## Current canonical values mapped by this pointer

- atomic top-3: **Ru > Os > Fe**
- economic top-3: **Fe > Ru > Os**
- Fe/Ru/Os reduced catalyst-dependent cost: **15.292 / 22.031 / 25.832 USD/t NH3**
- Top-3 Spearman rho / Kendall tau: **-0.50 / -0.33**
- full-15 raw Spearman rho: **0.929**
- Fe feasibility / Top-1 survival / Top-3 actionable: **0.799 / 0.282 / 0.940**
- Ru activity-only break-even: **201.22x**
- break-even operating point: **425 C / 190 bar / 30 C**
- scaling-consistent activity headroom: **1.090x at 673 K / 2.525x maximum**
- strict-scaling lowest Ru cost: **21.398 USD/t at E_N = -1.215 eV**

## Transfer closure required for figure lock

To convert this pointer into repository-complete provenance, import or content-address the following from the source harness:

1. canonical-run summary/manifest with hashes;
2. F1-F6 source-data tables;
3. F1-F6 generation scripts or editable figure sources;
4. the final rendered vector/raster assets;
5. the relevant closure metadata for MC, backward sweep and scaling reachability.

No new scientific calculation is required if these recovered files match the canonical values above. A rerun is warranted only if the recovered source disagrees with the frozen canonical snapshot or fails integrity checks.

## Automated repository closure installed 2026-09-10

The repository now contains a deterministic import/validation path:

- landing zone and contract: `provenance/nh3_final_1_1/README.md`;
- source-machine importer: `tools/prepare_nh3_final_1_1_bundle.py`;
- CI validator: `ci/validate_nh3_final_1_1_provenance.py`;
- workflow: `.github/workflows/nh3-final-1-1-provenance-closure.yml`;
- local handoff: `docs/NH3_FINAL_1_1_IMPORT_HANDOFF.md`.

The first GitHub Actions validation, run **34451643681**, completed successfully as infrastructure and returned **`PENDING_SOURCE_IMPORT`**. This is the expected state because the original FINAL-1.1 config, canonical closure directory, audit files and F1-F6 source assets are not yet present in this repository. The workflow performed no scientific calculation.

Once the original source harness is copied into the landing zone, the same workflow verifies SHA-256 integrity, canonical FINAL-1.1 anchors, F1-F6 source-data families and explicit F1-F6 asset mapping. Only `PROVENANCE_VALIDATED_READY_FOR_LOCK` permits the figure registry to advance from HOLD.
