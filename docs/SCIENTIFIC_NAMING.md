# Scientific naming convention

Snapshot: **2026-09-23**

Reader-facing documents use stable scientific names rather than development-version labels. Historical identifiers remain unchanged in provenance directories, code, frozen manifests and Git history so that existing results remain traceable.

## Active scientific names

| Scientific family | Reader-facing name | Historical provenance key |
|---|---|---|
| Ammonia model | **Ammonia process–economics model** | `NH3-FINAL-1.1` |
| Methanol model | **Methanol recycle–economics model** | `MEOH-D01-v3` |
| Rank-preservation control | **Au/TiO₂ rank-preservation control** | `Au/TiO2-RP V1.1` |
| Rank-preservation robustness | **Au/TiO₂ semi-open robustness extension** | `Au/TiO2-RP V1.3` |
| Agent architecture | **Adaptive Catalyst Screening Agent (ACSA)** | `DISCOVER V1` |
| Agent compute-budget extension | **ACSA budget-boundary study** | `DISCOVER-BOUNDARY-C1` |

## Active manuscript entry points

- Main text: `docs/MANUSCRIPT_MAIN_TEXT.md`
- Main-figure captions: `docs/MAIN_FIGURE_CAPTIONS.md`
- Figure architecture: `docs/FIGURE_MAP.md`

Versioned manuscript and caption files remain in the repository as revision history, but they are no longer the preferred reader-facing entry points.

## Naming rule

Do not introduce new reader-facing labels such as `V1.4`, `V1.5`, `v4`, `FINAL-1.2`, or similar development chronology. If a scientifically distinct extension is added, name it by function, for example `semi-open robustness extension`, `budget-boundary study`, or another descriptive scientific name. If a machine-readable internal identifier is required, keep it in provenance and map it here to the stable scientific name.

Historical files are not renamed or deleted solely to satisfy this convention because their paths are part of the provenance record.
