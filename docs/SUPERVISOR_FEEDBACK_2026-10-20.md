# Supervisor feedback — 2026-10-20

**Source:** supervisor's Chinese voice-message transcript supplied by the author on 2026-10-20. Homophones are normalized here as Fe (铁), Ru (钌), and KAAP; uncertain spoken numbers remain explicitly qualified.

**Status:** guidance recorded; several manuscript decisions adopted; numerical reconciliation, source verification, and integration into the manuscript are **not yet completed by this document**. No frozen model, experimental record, figure, or manuscript result is changed here.

**Related records:** [2026-10-19 supervisor feedback in Notion](https://app.notion.com/p/3fec0ee7c03e81188207e2bba95c5ae5); [2026-10-19 analyses merged as PR #115](https://github.com/stloendays/Catalyst-Essay/pull/115); [Au/TiO2 PR #113](https://github.com/stloendays/Catalyst-Essay/pull/113); [Sabatier PR #112](https://github.com/stloendays/Catalyst-Essay/pull/112).

## A. Accepted scientific/story decisions

### A1. NH3 staged Fe/Ru converter: promote the independently emerging industrial arrangement

The strongest staged-converter result is **Fe upstream, supported Ru/C downstream**, selected by the optimization rather than imposed as an ordering constraint. Placing Ru/C upstream is never optimal in the **tested** configuration/financing domain. The qualitative agreement with the reported KAAP-type industrial arrangement is an important external plausibility check and merits a **dedicated main-text Results panel**. It is not by itself an independent quantitative plant validation; cite the real plant configuration and preserve the model's pressure, bed, and financing boundaries.

Cross-check against the merged updated-in-range kinetic analysis: in the 9 MPa staged study Fe-first is optimal over an approximately **0–5.46%/yr** financing-rate window (from PR #115), and Ru-first is never optimal in the evaluated choices. The supervisor's central point is **emergent alignment with industrial practice**, not a forced prior.

### A2. Methanol: conversion-flexible *catalyst change* is the headline

The main-text isolated results panel should use the case allowing **candidate-specific conversion improvement by adding catalyst up to the documented equilibrium-relative bound**, because each candidate should be evaluated at its most appropriate permitted process condition:

- **21/63 catalyst comparisons (33.3%)** select a different catalyst from the laboratory STY leader; **10/63 (15.9%)** have a cost gap exceeding 5% (equivalently, 10 of the 21 changes). These are the preferred main result, with the exact denominator and definition.
- **26/63 (41.3%)** with laboratory conversion held fixed, **19/63** above a 5% cost gap, is the companion fixed-conversion treatment. Together the 21–26/63 rates describe a **model-scenario range (~33–41%)**, not a statistical confidence interval. A separate paper-cluster uncertainty interval must not be conflated with this range.
- Do **not** return to the initial ~66% point-level headline: that count also includes changes of operating temperature or other operating state rather than necessarily changing catalyst identity. The 50/81 point-level analysis, if retained, is an explicitly secondary comparison with a different unit of analysis.
- The pre-registered catalyst-identity rule from [RULES.md](../analysis/meoh_catalyst_level_2026_10_19/RULES.md) remains unchanged. The [2026-10-19 analysis](../analysis/meoh_catalyst_level_2026_10_19/README.md) reports 21/63 and 26/63; re-run the main-text/figure audit after adopting the new presentation.

### A3. Temperature-only result: separate the engineering observation

When only the operating temperature changes, report an operating-point finding, **not a catalyst ranking inversion**. In the committed 2026-10-19 analysis, 112 catalysts had at least two measured temperatures, 82 changed best operating temperature, and 75 of these 82 chose a lower plant-cost temperature; the **median decrease is 50 °C for the lower-temperature cases**. Do not generalize that median to all catalysts without checking the cohort definition.

### A4. NH3 value proposition and language

Center the NH3 Results on **industrial cost/financing parity, kinetic mechanism, and the emergent Fe→Ru bed order**; the intrinsic-activity/economic-ranking inversion remains context, not the sole headline. Use **plant-level optimum** to mean a model-predicted minimum under a stated process/economic boundary; define this once in Methods and write the supported conclusion plainly. Do not use conditional industrial claims as universal plant facts.

## B. Scientific evidence and provenance gates — must close before draft

### B1. Remove mixed generations of NH3 kinetics and results (P0)

The supervisor explicitly identified old kinetic outputs still present in ammonia prose, including a Ru optimum near **425 bar** and an old activity-improvement multiple of order **~200x** (the speech transcription also contains an ambiguous “188”). These should **not** be repeated as current numbers without a direct code/data audit.

Action: establish a single audited Fe and Ru/C kinetic/model provenance for manuscript use (the merged comparison uses **Keestra 2025 Model 3 with Topsoe KM1R calibration for Fe**, and **Rossetti 2006 for promoted Ru/C**, with both evaluated inside the experimentally fitted pressure ranges for the KAAP-type check). Recompute/trace every downstream NH3 claim: optimal pressure, temperature, catalyst mass/bed, break-even metal price, activity multiple, economic difference, staged window, and confidence/sensitivity tests. Sweep **Abstract, Methods, Results, Discussion, figure panels/captions, Tables, Extended Data, SI and Source Data** for mixed-generation values. Maintain frozen historical outputs and record replacements with source references. Only freeze the new ammonia claim set after the audit passes.

### B2. Financing/lease rate: choose and justify ONE main baseline (P0)

The Ru/C–Fe ordering depends strongly on the annual financing/lease rate. The supervisor referred to a crossover of roughly **6–6.5%/yr** and noted that Ru/C can be cheaper below a threshold while Fe is cheaper at **12%/yr**. Do not publish 6.5% as a universal threshold: current analyses imply different crossovers for different comparisons:

- **4.57%/yr**: KAAP-type 90-bar fixed-loop Fe versus Ru/C comparison after in-range Fe kinetics.
- **5.46%/yr**: upper financing boundary for the **Fe-first → Ru/C-second** staged-converter optimum in the tested 9 MPa model.
- Approximately **6.5%/yr**: separately optimized Fe/Ru/C pressure-in-range comparison.

Choose a reference annual rate with an explicit source from catalyst-metal leasing/industrial reports or a properly identified cost-of-capital methodology; explain **why that financial convention applies to the specified catalyst ownership and recovery contract**. Show a single **cost difference (Ru/C minus Fe) versus rate** curve, with the matching break-even intersection, nominal point, and sensitivity to other rates; keep **0% and 12%** as transparent comparison cases. Do not transfer one threshold to another process configuration.

### B3. Audit the 100 extracted numerical values by source type (P0)

The supervisor requested an actual double check: are the **100 values** each matched against the original paper/SI, and were any **read from figures**? The 2026-10-19 project record currently describes **91 printed or unit-converted values, 6 reconstructed from feed composition, and 3 numerically matching entries requiring locator/qualifier/metric-label corrections**. This **does not establish 100 directly printed values or independent manual verification**.

Create a per-value ledger with paper/DOI, source page and locator, quantity, value, units, source type (**printed table/text, derived, plot-digitized**), derivation (if relevant), verifier and verification mode (**human vs AI-assisted**), agreement status, and correction. Report **printed, derived, and plot-read categories separately with their own denominators and accuracies**, including the hold-out printed-value check **39/40** in its own cohort. Never pool table transcription with graphic extraction or call AI-assisted checking an independently signed human audit. Verify from primary material before making a manuscript claim about accuracy.

### B4. Au/TiO2: conditional preservation in Extended Data; support lifetime exponent q (P1)

Use the newer Au/TiO2 decision-boundary analysis as a **conditional rank-preservation** result, not a constructed inevitability from identical exponent draws; place it in **Extended Data** rather than creating an artificial main-text symmetry. The lifetime-size exponent **q**, including any threshold such as q* ≈ 1.9, must have either a scientifically defensible literature anchor for its physical interpretation or be explicitly labeled a **model parameter/theoretical threshold, not an empirically measured exponent**. Preserve the distinction between powder low-temperature experiments and model-surface ripening examples. [Draft PR #113](https://github.com/stloendays/Catalyst-Essay/pull/113) is still subject to scientific and author review; recording this guidance **does not merge it**.

### B5. Sabatier/methanation: prediction-before-run or post-hoc explanation? (P0 for placement)

Audit the timestamp/commit chronology of the leverage **criterion, predicted ranking/scale boundary, preregistration, numerical run, and interpretation** in [PR #112](https://github.com/stloendays/Catalyst-Essay/pull/112):

- **Criterion/prediction frozen before running the calculation** → may be presented as a prospective/independent validation in the main text, if the evidence really supports this sequence.
- **Criterion found or tuned only after the calculation** → Discussion-level explanatory example, **not** independent prediction.

No chronology conclusion is assumed from the existence of preregistration alone. The supervisor also explicitly rejected manufacturing a 50/50 number of preservation versus inversion cases: report the **actual observed counts**, even when asymmetric.

## C. Manuscript and figure implementation checklist

- [ ] **P0:** Consolidate the ammonia kinetic generation; rerun source-to-number audit and freeze a single active claim set.
- [ ] **P0:** Make staged Fe-upstream/Ru/C-downstream industrial correspondence an independent main-text Results panel, with tested-domain boundaries and an industrial-layout reference.
- [ ] **P0:** Refocus the methanol headline and Figure 2 result panel on conversion-flexible **21/63**, **10/63 >5%**, with fixed-conversion **26/63** as its bounded comparison; reconcile captions, abstract, Methods, Results, Discussion and SI.
- [ ] **P0:** Retain the catalyst-level identity definition, isolate temperature-only re-optimization and accurately describe the **50 °C** median subset.
- [ ] **P0:** Select a literature-grounded financing baseline, build and label the rate crossover/sensitivity plot, and distinguish the **4.57/5.46/~6.5%** economic questions.
- [ ] **P0:** Complete a 100-row extraction provenance audit; publish source-type-specific error rates and human/AI verification status.
- [ ] **P0:** Establish temporal order of Sabatier criterion versus simulation; only then decide Main Results versus Discussion.
- [ ] **P1:** Move Au/TiO2 to Extended Data and justify/qualify the lifetime exponent q; avoid circular preservation evidence.
- [ ] **P1:** Use natural, assertive scientific English where supported; retain uncertainties that matter, avoid generic defensive “might/may” padding.
- [ ] **P0:** Revise **Methods and Results throughout**, align figures/tables/SI/Source Data, produce a coherent **end-of-October manuscript draft** for the supervisor; supervisor will then seek feedback from external professors.

## D. Delivery plan (planning targets, not claims of completion)

- **20–23 Oct:** reconcile all main statistics, kinetic provenance and exact definitions; identify finance citation and extraction-audit ledger.
- **24–27 Oct:** regenerate/inspect updated panels and sensitivity analyses; update Methods, Results, Extended Data and SI together.
- **28–31 Oct 2026:** full scientific number audit; complete the consolidated draft (Word/PDF if applicable) and transmit to the supervisor **by the end of October**. The previously discussed **28 October** date can serve as an internal draft target, not a confirmed promise from this record.
- **After supervisor review:** seek external professors' assessment of the consolidated manuscript; do not start a new case merely to balance preservation and inversion counts.

## E. Provenance and cautions

- **Direct supervisor decisions:** staged Fe-first finding in main text; conversion-flexible 21/63 main; fixed 26/63 as a range endpoint; 50 °C operating-point observation; NH3 kinetics-wide recomputation; financing-baseline justification; extraction-source-type split; Au in Extended Data; Sabatier prediction-order gate; no forced case balance; end-of-month draft.
- **Pre-existing computed results:** quantities attributed to [merged PR #115](https://github.com/stloendays/Catalyst-Essay/pull/115) and its analysis files are **not newly computed in this feedback note**.
- **Not yet established:** whether each of 100 values has a truly independent manual signoff; the proportion, if any, read from figures; which finance rate the author will adopt as canonical; Sabatier temporal independence; an empirical literature measurement of q; an audited fully updated NH3 manuscript.
- **No silent updates** to canonical frozen protocols, figures, manuscript numbers, or PR #112/#113 are authorized by this note alone.

**Transcription ambiguities:** “聊/辽/梁” is interpreted as **钌 (Ru)**; “KKAP” as **KAAP**; the spoken “188” has unclear referent and requires source inspection, not normalization into an invented statistic.
