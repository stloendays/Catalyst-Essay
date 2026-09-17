# SI Section 7. Complete run inventory and integrity record

Scope: the DISCOVER-BOUNDARY-C1 Agent line. Results §3.7 and Discussion §4.6 are frozen and are cross-referenced, not
restated, here.

Every DISCOVER-BOUNDARY-C1 result in the manuscript derives from the scored runs listed below. The inventory is built
directly from `data/discover_boundary_c1_error_taxonomy_summary.csv` and
`data/discover_boundary_c1_decision_components.csv`, which key the same **17 cells** and agree on every cell definition
`(tier, arm, budget_CU, n)` (the two files order the mini cells differently), giving **317 scored runs** in total. Three
model tiers were sampled — `gpt-5.5-2026-04-23` (strong), `gpt-5.4-mini-2026-03-17` (mini) and
`gpt-5.4-nano-2026-03-17` (nano) — under the frozen policy E and, in one cell, the declared-interface arm E2.

## 7.1 Scored cells

Complete decisions are `k_complete_decision` from the decision-components file; action errors and the count of runs
carrying at least one action error are from the error-taxonomy file. Action errors are counted per event, so a single
run can contribute several.

| Tier | Model | Arm | Budget (CU) | n | Complete decisions | Action errors | Runs with ≥1 action error |
|---|---|---|---|---|---|---|---|
| strong | gpt-5.5-2026-04-23 | E | 50 | 20 | 13/20 | 3 | 3 |
| strong | gpt-5.5-2026-04-23 | E | 75 | 20 | 20/20 | 2 | 2 |
| strong | gpt-5.5-2026-04-23 | E | 100 | 20 | 19/20 | 4 | 4 |
| strong | gpt-5.5-2026-04-23 | E | 125 | 20 | 20/20 | 2 | 2 |
| strong | gpt-5.5-2026-04-23 | E | 150 | 20 | 20/20 | 4 | 4 |
| strong | gpt-5.5-2026-04-23 | E | 175 | 20 | 19/20 | 10 | 9 |
| strong | gpt-5.5-2026-04-23 | E | 200 | 8 | 8/8 | 1 | 1 |
| strong | gpt-5.5-2026-04-23 | E | 225 | 20 | 20/20 | 0 | 0 |
| strong | gpt-5.5-2026-04-23 | E | 250 | 9 | 9/9 | 0 | 0 |
| strong | gpt-5.5-2026-04-23 | E | 5000 (non-binding allowance) | 20 | 20/20 | 1 | 1 |
| mini | gpt-5.4-mini-2026-03-17 | E | 175 | 20 | 0/20 | 72 | 19 |
| mini | gpt-5.4-mini-2026-03-17 | E | 225 | 20 | 6/20 | 61 | 20 |
| mini | gpt-5.4-mini-2026-03-17 | E | 300 | 20 | 4/20 | 71 | 17 |
| mini | gpt-5.4-mini-2026-03-17 | E | 400 | 20 | 7/20 | 49 | 19 |
| mini | gpt-5.4-mini-2026-03-17 | E2 | 175 | 20 | 0/20 | 122 | 20 |
| nano | gpt-5.4-nano-2026-03-17 | E | 175 | 20 | 0/20 | 50 | 20 |
| nano | gpt-5.4-nano-2026-03-17 | E | 225 | 20 | 0/20 | 59 | 20 |
| **Total** | — | — | — | **317** | — | **511** | **161** |

Each new cell is independently tagged and keyed separately in the analysis (`c1low`, `c1uncapped`, `c1mini300` and
`c1mini400` for the 2026-09-11 batches), so no new cell is pooled with an existing E or E2 cell.

| Tier / arm | Cells | Scored runs |
|---|---|---|
| strong / E | 10 | 177 |
| mini / E | 4 | 80 |
| mini / E2 | 1 | 20 |
| nano / E | 2 | 40 |
| All | 17 | 317 |

The two mini interventions occupy different rows and must be read separately. The E2 interface arm is a single cell at
175 CU with **0/20** complete decisions; the added-compute cells are E cells at 225, 300 and 400 CU with **6/20**,
**4/20** and **7/20**. Two reduced-n cells exist, 200 CU (n = 8) and 250 CU (n = 9), both produced by the
cost-motivated stop recorded in addendum A1, which was taken before any C1 result had been scored or inspected.

## 7.2 Integrity record

`data/discover_frozen_v1_hashes.json` lists **15** frozen files, under the rule that any change to a listed file
defines DISCOVER V2. Every recorded check returns **15/15 PASS with zero mismatches, before and after every batch**:
the C1 metadata records checks labelled `before`, `before_smoke2` and `after`, the Phase B metadata records
`before_phaseB` and `after_phaseB`, and addendum A5 records the same result for each 2026-09-11 batch. The driver
`discover/formal_e.py` carries SHA-256 `d4451c424dbfac5f7a6176038864f35cc6326ac04ae5efcb91f14574f8aeee93` in every one
of those checks and is unchanged throughout; the runner (`2f6103aa…`) and the extension metrics module (`3f8f4e59…`)
are likewise unchanged.

Execution was clean. Phase B completed **80/80 formal runs with 0 smoke runs, 0 infrastructure retries and 0 driver
exceptions**; the 2026-09-11 extension completed **118/118 formal runs with 0 infrastructure retries and 0 driver
exceptions**. Across all 17 cells there are **0 validation rejections**, and `k_built_window` equals n in all 17 cells,
so all 317 runs built at least one process window.

**No scored run was discarded, and no trace was deleted.** Two exclusions are recorded, neither of which removes a
scored run. Three directories interrupted mid-run without a `trace.json` (strong 150, 200 and 250 CU) are listed as
interrupted in the C1 and Phase B metadata and excluded from all counts. One 75 CU batch was aborted by API credit
exhaustion (HTTP 429); its **17** traces were quarantined — 16 with 0 steps and 0 CU spent, one truncated mid-run — and
preserved verbatim outside the scored path so that no analysis can pool them into a 75 CU cell, and the 3 valid runs
from that batch were superseded by a complete n = 20 re-run so that the cell never mixes two batches.

The execution environment recorded with the C1 and Phase B batches is Windows-11-10.0.26200-SP0 with Python 3.12.14,
numpy 2.3.5, scipy 1.18.0, matplotlib 3.11.0 and openai 3.7.0.

Primary evidence: `data/discover_boundary_c1_error_taxonomy_summary.csv`,
`data/discover_boundary_c1_decision_components.csv`, `data/discover_frozen_v1_hashes.json`,
`data/discover_boundary_c1_metadata.json`, `data/discover_boundary_c1_phase_b_metadata.json`,
`data/discover_boundary_c1_quarantine_2026-09-11.json`, `data/discover_boundary_c1_superseded_B75_2026-09-11.json`.
Batch-level records: `docs/DISCOVER_BOUNDARY_C1_ADDENDUM_A1.md`, `docs/DISCOVER_BOUNDARY_C1_ADDENDUM_A2.md`,
`docs/DISCOVER_BOUNDARY_C1_ADDENDUM_A5_2026-09-11.md`. Metric definitions are governed by
`docs/AGENT_METRIC_DEFINITIONS_SOURCE_OF_TRUTH_2026-09-13.md`; the corresponding main-text statements are
`MANUSCRIPT_SKELETON_v4_2026-09-14.md` §3.7 and §4.6, which are frozen and are cross-referenced here without change.
