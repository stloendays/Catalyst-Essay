# Scientific naming convention

Snapshot: **2026-09-23**

Reader-facing documents use stable scientific names rather than development-version labels.

## Active scientific names

| Scientific family | Reader-facing name |
|---|---|
| Ammonia model | **Ammonia process–economics model** |
| Methanol model | **Methanol recycle–economics model** |
| Rank-preservation control | **Au/TiO₂ rank-preservation control** |
| Rank-preservation robustness | **Au/TiO₂ semi-open robustness extension** |
| Agent architecture | **Adaptive Catalyst Screening Agent (ACSA)** |
| Agent compute-budget extension | **ACSA budget-boundary study** |

## Active manuscript entry points

- Main text: `docs/MANUSCRIPT_MAIN_TEXT.md`
- Main-figure captions: `docs/MAIN_FIGURE_CAPTIONS.md`
- Figure architecture: `docs/FIGURE_MAP.md`

## Naming rule

Reader-facing material must not display internal development identifiers, numbered architecture labels, or explicit old-name → new-name mapping tables. Use the scientific-function names above directly, as if they were the only manuscript-facing names.

Historical identifiers may remain inside provenance directories, frozen manifests, implementation filenames and Git history when required for traceability, but they should not be surfaced in the manuscript, captions, README, STATUS, supervisor-facing summaries, figure maps, Data/Code Availability text or other reader-facing documentation.

Do not introduce new reader-facing names based on development chronology. If a scientifically distinct extension is added, name it by function, such as **semi-open robustness extension** or **budget-boundary study**.


## Superseded-work rule

When a later validated analysis or scientific treatment replaces an earlier stage, use the later work directly and do not mention the older stage in reader-facing material. Older artifacts remain archival/provenance material only. Development history is surfaced only when it is necessary to interpret the current science or when the author explicitly requests it.
