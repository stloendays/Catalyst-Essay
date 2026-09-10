# Manuscript integration checklist — 2026-09-10

Research generation is frozen. The remaining work is an evidence-integration and submission-preparation workflow, not an open-ended experiment program.

## 1. Claim-to-evidence audit

For every quantitative statement in the Abstract, Results, Discussion and figure captions, record the canonical source file, script, run identifier and figure/table panel. Resolve any mismatch before prose polishing.

Priority claims:

- NH3 atomic-to-economic top-3 inversion and full-15 versus Top-3 rank statistics;
- NH3 uncertainty / feasibility values;
- Ru activity-only parity and scaling-consistent headroom;
- MEOH-D01-v3 upstream/economic rankings, purge robustness and pathway interpretation;
- Au/TiO2-RP V1.1 canonical preservation and V1.3 supporting robustness;
- DISCOVER V1 original cross-model result;
- DISCOVER-BOUNDARY-C1 175/225-CU boundary result, Wilson intervals, narrow-window usage, CU_to_full and failure taxonomy.

## 2. Agent wording audit

Keep three quantities separate:

1. **policy advantage** — whether adaptive E completes a decision that fixed D does not at the same budget;
2. **model capability** — whether a model tier can execute the frozen decision policy and scientific interface correctly;
3. **raw compute efficiency** — CU required to reach the same complete decision.

Do not use C1 to claim universal compute saving. Do not claim weak-tier behavior outside the Phase B 175/225-CU cells. Do not describe the reduced Phase B as the original five-budget preregistered design.

## 3. Figure locking

Freeze a single manuscript source for every main and supporting panel. No hand-edited numerical values. Rerender from the retained source data/scripts where possible. Check that panel labels, units, rank direction, cost denominator and canonical model labels match the text.

C1 figures in `figures/discover_boundary_c1/` should be considered for the Agent Results/Extended Data package; use the manuscript story, not figure availability, to decide main-text placement.

## 4. Methods / SI

Document:

- frozen scientific-model boundaries and canonical versions;
- candidate-specific versus fixed-state process optimization choices;
- uncertainty propagation and seeds;
- backward-design and reachability definitions;
- rank-preservation-control evidence boundary;
- DISCOVER V1 task, actions, CU definition, scorer and stopping rule;
- C1 preregistration, A1 and A2 deviations, Wilson intervals and failure taxonomy;
- raw trace retention, token accounting and frozen-hash checks.

## 5. Reproducibility package

Before submission:

- verify all retained scripts run from a clean environment;
- verify no secrets or local-only paths are committed;
- verify canonical data paths exist;
- verify all frozen hashes;
- produce a concise reproduction entry point for each main figure/table;
- tag the manuscript-data freeze only after the audit is complete.

## 6. Reopen criteria

New computation is warranted only if the audit reveals a substantive correctness or reproducibility problem. Narrative preference alone is not a reason to reopen the research phase.
