# NH3-FINAL-1.1 source-harness import handoff

## Purpose

Close the only remaining repository-provenance gap for main scientific Figures F1-F6 by importing the **already-completed** NH3-FINAL-1.1 source evidence. Do not rerun, retune or reconstruct the science.

GitHub-side validation infrastructure is already installed. The current expected state before the local source copy is `PENDING_SOURCE_IMPORT`.

## Find the original source root

On the Windows machine that contains the original AI4S project, locate the canonical consistency-closure file:

```powershell
Get-ChildItem -Path 'D:\论文-AI4S' -Recurse -File -Filter 'NH3_FINAL_1_1_CONSISTENCY_CLOSURE.md' -ErrorAction SilentlyContinue |
  Select-Object -ExpandProperty FullName
```

The **source root** is the project directory under which all of the following resolve at the recorded relative paths:

```text
configs/nh3_final.yaml
outputs/nh3_final_20260905T134204Z/closure/
PRESSURE_CAPEX_INDEPENDENT_AUDIT_2026-09-05.md
audits/audit_pressure_capex_handcalc_2026-09-05.py
PROMOTE_NH3_FINAL_1_1_CHECKLIST.md
NH3_FINAL_1_1_CONSISTENCY_CLOSURE.md
figures/
```

Do not select a directory that only contains a manuscript/GIST copy.

## Import into Catalyst-Essay

From a current local checkout of `stloendays/Catalyst-Essay`:

```powershell
git switch main
git pull origin main
python tools/prepare_nh3_final_1_1_bundle.py --source-root '<SOURCE_ROOT>' --clean
python ci/validate_nh3_final_1_1_provenance.py
Get-Content artifacts/nh3_final_1_1_provenance/status.txt
```

The importer is read-only with respect to `<SOURCE_ROOT>`. It content-addresses copied evidence with SHA-256 and creates `FIGURE_ASSET_MAP.json` for explicit F1-F6 source assets.

## If figure mapping is ambiguous

Open:

```text
provenance/nh3_final_1_1/source_harness/FIGURE_ASSET_MAP.json
```

Resolve only against the original FINAL-1.1 `figures/` directory. A valid mapping points each F1-F6 entry to the exact copied source asset. Do not map any FINAL-1.0 figure.

## Push the bundle

Only after the local validator reports no hash/integrity failure:

```powershell
git add provenance/nh3_final_1_1/source_harness
git status
git commit -m 'Import content-addressed NH3-FINAL-1.1 provenance bundle'
git push origin main
```

The push automatically triggers `.github/workflows/nh3-final-1-1-provenance-closure.yml`.

## Acceptance condition

The repository is ready to lock F1-F6 only when CI reports:

```text
PROVENANCE_VALIDATED_READY_FOR_LOCK
```

Any other state remains diagnostic. In particular:

- `PENDING_SOURCE_IMPORT`: source evidence still missing;
- `HASH_MISMATCH`: copied content disagrees with its import manifest;
- `CANONICAL_EVIDENCE_INCOMPLETE`: imported closure does not expose all frozen FINAL-1.1 anchors;
- `SOURCE_DATA_CLASS_INCOMPLETE`: one or more F1-F6 source-data families are absent;
- `FIGURE_MAPPING_INCOMPLETE`: source figures exist but F1-F6 mapping is not yet unambiguous.

No status authorizes replacing missing FINAL-1.1 files with old FINAL-1.0 workbooks.
