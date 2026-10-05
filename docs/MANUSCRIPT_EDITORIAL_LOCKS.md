# Manuscript editorial locks

Snapshot: **2026-09-23**

These are author-level editorial decisions for the current manuscript. They should be preserved in future manuscript polishing unless the author explicitly reopens the specific item.

## LOCK-01 — Agent manuscript role

Revised 2026-10-05 on the supervisor's direction. The manuscript-level role of the Agent is **the automation engine that scales the multiscale analysis to the candidates that publications and databases provide**.

Required interpretation:

- Reaction-specific kinetic, process and economic tools remain responsible for the scientific calculations; the Agent adds no scientific model.
- The Agent does three things: it extracts catalytic data from publications and Supporting Information with the location of every value; it takes every candidate through the full chain, with cheap bounds deciding where the expensive calculations are spent; and it must reproduce the frozen hand-built cases before it scores new candidates.
- The evidence for the Agent is extraction accuracy against a curated reference, the self-check against the hand-built cases, and the computation saved relative to full enumeration.
- The main result the Agent enables is the share of published catalyst comparisons whose leader changes after process and economic evaluation.
- The compute-budget study (budget curves, stopping behaviour, model tiers) belongs to the separate methods paper and is not part of this manuscript; its figure is kept in `figures/acsa_budget_boundary/`.
- Do not use sophisticated agent architecture as a selling point; the contribution is scale.

This lock remains active unless the author explicitly asks to reconsider the Agent's manuscript-level role.

## LOCK-02 — Reader-facing semantic names

Reader-facing manuscript, figure, README and supervisor-facing documents should use the semantic names defined in `docs/SCIENTIFIC_NAMING.md`. Development-version labels remain only where provenance or implementation traceability requires them.

Do not create new reader-facing `V1.x`-style names unless the author explicitly asks for versioned nomenclature.


## LOCK-03 — No legacy-name mapping in reader-facing documents

Do not display internal development identifiers or explicit legacy-name → scientific-name mappings in reader-facing material.

- Use the scientific name directly.
- Do not write constructions of the form `internal label → scientific label`.
- Do not add a “historical provenance key” column to README, STATUS, manuscript-facing tables or naming guides.
- Historical identifiers may remain only where they are operationally necessary for provenance, frozen manifests, implementation paths or Git history.
- If a reader-facing document needs to point to provenance, link to the provenance location without reproducing the internal development identifier in the prose.

This lock remains active unless the author explicitly asks to expose historical identifiers.


## LOCK-04 — Superseded work stays out of the active narrative

Once a later validated analysis, figure, model treatment or manuscript interpretation supersedes an earlier development stage, the later work becomes the sole reader-facing basis.

- Do not mention an older stage simply because it exists in the repository.
- Do not compare the current result with obsolete intermediate results unless the historical comparison changes the scientific interpretation or the author explicitly requests it.
- Do not carry superseded values, figures, model variants, partial analyses or development-stage conclusions forward as secondary support after a later analysis has replaced them.
- Keep obsolete material only in provenance, archive records and Git history when traceability is required.
- README, STATUS, supervisor-facing summaries, captions, SI prose and manuscript text should describe the current scientific state directly, without phrases such as “legacy”, “previous version”, “earlier version”, “superseded result” or similar development-history commentary.
- If later work merely refines an earlier result, cite and discuss the refined result directly unless the refinement history is scientifically necessary.

This lock remains active unless the author explicitly asks to discuss development history.

## LOCK-05 — MeOH uncertainty wording and evidence hierarchy

Reader-facing text must not foreground the MeOH uncertainty analysis as being “assumption-aware”, “assumption-derived”, or otherwise frame the result around the word *assumption*.

Required treatment:

- In Results, Discussion, figures and supervisor-facing summaries, call the analysis **performance-input uncertainty propagation**, **published-data-resolution uncertainty**, or an equivalently neutral scientific description.
- Keep the source basis precise but secondary: the catalytic-performance quantities propagated in the MeOH model do not come with directly reported replicate standard deviations in the source paper, so the performance-input uncertainty scale is constructed from the information carried by the published catalytic data (integer reporting resolution, censored “<1%” entries, and table-internal consistency of the reported performance relationships).
- State that source/boundary information once in Methods or Supporting Information. Do not make it the headline interpretation of the result.
- Do not call the constructed scale an experimentally reported SD, SEM or replicate error unless the source explicitly supplies such a statistic.
- Keep two uncertainty questions separate: (i) **performance-input uncertainty**, which can move the candidate ranking and is the primary MeOH ranking-robustness test; and (ii) **economic-parameter robustness**, which is supporting evidence only. The 2026-09-20 cost-side matrix (5,000/5,000 invariant order) was computed before the Table 3 correction and must be rerun on the corrected inputs before it is cited.
- The reader-facing MeOH rank-probability result is the committed performance-input Monte Carlo (`analysis/meoh_measurement_mc_2026_10_05/`, 5,000 draws, seed 20261005): economic winner first in 4,559/5,000 (91.2%), 5 wt% Re / 250 °C last in 5,000/5,000, ranks 2 and 3 exchanged in 1,054/5,000 (21.1%). The earlier ~97.0% / ~47.8% figures came from the uncorrected inputs and are not cited.

This lock remains active unless the author explicitly reopens the MeOH uncertainty framing.
