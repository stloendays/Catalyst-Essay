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

## LOCK-06 — Methanol second cohort as a follow-up literature–computational experiment (2026-10-16)

**Author-directed editorial decision, made after the second-cohort outcomes were known.** This lock changes how the finished paper organizes and interprets its evidence; it is not a retrospective amendment of the original pre-registered experiment. This instruction applies to Codex, AI writing agents, manuscript revisions, figure captions, SI summaries, and supervisor-facing reports.

### Required reader-facing framing

- Treat the later methanol literature cohort as an **independently assembled follow-up literature–computational replication experiment** that applies the same data-extraction, within-paper grouping, catalyst-specific process optimization, and economic scoring workflow. It is **not** a new laboratory experiment, nor independent measurement of industrial catalyst operating economics.
- Assess its scientific contribution from the **observed data and mechanism**, not from an earlier binary P1/P2 label as an acceptance gate for whether to include this cohort in the paper. The paper's headline evidence is the combined **50/81** STY-versus-model-cost leader disagreements (61.7%, 42 with >5% regret) together with the disjoint-cohort counts **28/40** and **22/41**. Frame the difference between cohorts as observed heterogeneity, not proof of a fixed universal 70% inversion frequency.
- Emphasize the repeated downstream mechanism, including the second cohort's **28/41** selectivity-rule matches to the model-cost leader and **21/22** inversion cases whose plant-cost leader has higher selectivity and lower CO. Describe the rule's demonstrated improvement over the **specified chance baseline**, but do **not** assert statistically proven superiority to the STY baseline where the paired uncertainty interval includes zero.
- In the Abstract, Results, figures, and public-facing overview, **do not organize the scientific story around the internal labels `P1`, `P2`, `PASS`, `FAIL` or call the second cohort a wholesale failed experiment**. Report the underlying observations, economic regret, mechanisms, model-conditional scope and robustness. Internal success/failure labels need not be manuscript headings or figure annotations.
- Manuscript wording should distinguish **model-derived plant-cost leader** from actual observed industrial catalyst adoption. Do not imply that two independent literature cohorts are two independent industrial field trials.

### Evidence transparency and non-retroactivity (mandatory)

- The original prospective pre-registration is historical provenance and **remains unchanged**: `analysis/validation_meoh_prospective_2026_10_13/PREREGISTRATION.md`, `DEVIATIONS.md`, `REPORT.md`, `results.json`, blind predictions, corrections, and commit-order evidence. Do not delete, rewrite, conceal or relabel a pre-specified result so it appears to have passed.
- In the Methods or Supporting Information, preserve a concise, accessible account that the **originally specified S6 rate-interval criterion was narrowly unmet**: observed **22/41 = 53.7%** versus pre-specified lower bound **54.1%**; the separately specified selectivity rule beat its chance baseline (**28/41**). The detailed original binary assessment remains available in the unchanged analysis report. This disclosure can be expressed in normal scientific prose instead of foregrounding the labels in the main narrative.
- The token-limit interruption affects the optional `si_figures` extraction (**24/40 completed**). The primary 41 printed-value comparisons were completed and scored. **Do not attribute the primary original criterion miss to incomplete computing** without specific evidence.
- Do not retrospectively claim that the original prospective validation passed, discard a completed pre-registered endpoint, select only passing sensitivity sets, or silently replace the originally registered decision threshold. If writing a post-hoc pooled/exploratory interpretation, identify it as such where relevant.
- The combined 81 comparisons and manuscript narrative may be emphasized as the current scientific synthesis **without reopening, refitting, or changing any frozen underlying experiment**, its saved numerical results, or original decision criteria.

**Operational rule:** Future agents and editors should follow this lock as the *current manuscript presentation instruction* while keeping the original registered test and its actual result auditable. A new evaluation standard requires a genuinely new, clearly labeled study; it cannot be retroactively assigned to the earlier experiment.
