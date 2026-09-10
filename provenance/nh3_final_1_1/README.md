# NH3-FINAL-1.1 repository provenance bundle

This directory is the landing zone for the already-completed **NH3-FINAL-1.1** source-harness evidence. It closes repository provenance for F1-F6; it does **not** authorize a new scientific run or any change to the frozen model.

## Canonical source anchor

The project record identifies the following immutable source state:

- canonical run: `outputs/nh3_final_20260905T134204Z`
- closure: `outputs/nh3_final_20260905T134204Z/closure/`
- config: `configs/nh3_final.yaml`
- archived predecessor: `configs/nh3_final_1.0_archived.yaml`
- audit: `PRESSURE_CAPEX_INDEPENDENT_AUDIT_2026-09-05.md`
- independent audit code: `audits/audit_pressure_capex_handcalc_2026-09-05.py`
- promotion checklist: `PROMOTE_NH3_FINAL_1_1_CHECKLIST.md`
- consistency closure: `NH3_FINAL_1_1_CONSISTENCY_CLOSURE.md`
- source-harness figures: `figures/` (F1-F6 were redrawn after FINAL-1.1 closure)

The authoritative project-side pointer is `docs/NH3_FINAL_1_1_PROVENANCE_POINTER.md`.

## Frozen headline values

The imported bundle must agree with the current manuscript snapshot; import is rejected if it contradicts these values:

- atomic top-3: `Ru > Os > Fe`
- economic top-3: `Fe > Ru > Os`
- Fe / Ru / Os cost: `15.292 / 22.031 / 25.832 USD/t NH3`
- Top-3 Spearman / Kendall: `-0.50 / -0.33`
- full-15 raw Spearman: `0.929`
- Fe feasibility / Top-1 survival / Top-3 actionable: `0.799 / 0.282 / 0.940`
- Ru activity-only break-even: `201.22x`
- scaling headroom: `1.090x at 673 K / 2.525x maximum`
- strict-scaling Ru minimum cost: `21.398 USD/t at E_N = -1.215 eV`

These are comparison anchors, not a substitute for the source files.

## Import layout

Run `tools/prepare_nh3_final_1_1_bundle.py` **on the machine that still has the original source harness**:

```bash
python tools/prepare_nh3_final_1_1_bundle.py --source-root <PATH_TO_SOURCE_HARNESS>
```

The helper copies only provenance-relevant material into:

```text
provenance/nh3_final_1_1/source_harness/
```

and writes:

- `SOURCE_MANIFEST.json` — SHA-256, byte size and source-relative path for every copied file;
- `FIGURE_ASSET_MAP.json` — F1-F6 source-asset mapping when uniquely recoverable;
- `IMPORT_REPORT.md` — copied/missing/skipped evidence and any ambiguous figure mapping.

The helper performs no model calculation and does not modify the source harness.

## CI decision

`.github/workflows/nh3-final-1-1-provenance-closure.yml` runs `ci/validate_nh3_final_1_1_provenance.py`.

Possible statuses:

- `PENDING_SOURCE_IMPORT` — source bundle is absent/incomplete;
- `HASH_MISMATCH` — a copied file no longer matches its import manifest;
- `CANONICAL_CONFLICT` — imported textual closure evidence conflicts with the frozen canonical anchors;
- `FIGURE_MAPPING_INCOMPLETE` — F1-F6 assets are present but cannot yet be mapped unambiguously;
- `PROVENANCE_VALIDATED_READY_FOR_LOCK` — required evidence, hashes, canonical anchors and F1-F6 asset mapping all pass.

Only the final state permits F1-F6 to be moved from `HOLD` to `LOCKED`. CI does not silently substitute NH3-FINAL-1.0 material and does not regenerate missing science.

## What must not be used

Do not use an NH3-FINAL-1.0 workbook or figure to fill a missing FINAL-1.1 slot. In particular, historical 10.199 / 17.592 / 21.321 USD/t, 73.6% Fe feasibility and 2171.56x Ru parity are not current figure evidence.
