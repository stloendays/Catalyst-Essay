# Manuscript v6 audit — 2026-09-20

Canonical draft: `docs/MANUSCRIPT_MAIN_TEXT_v6_2026-09-20.md`  
Caption set: `docs/MAIN_FIGURE_CAPTIONS_v2_2026-09-20.md`  
Headline data: `data/manuscript_headline_results_2026-09-20.csv`

## Scientific integration closed in v6

- NH3 ranking: Ru > Os > Fe -> Fe > Ru > Os.
- Descriptor uncertainty: Fe feasibility 79.9%; Fe economic Top-1 68.1%; atomic-to-economic Top-1 survival 28.2%; Top-3 actionable 94.0%.
- Ru equal-price counterfactual: reoptimized Ru = 14.712 USD/t NH3 at 425 C / 170 bar / 30 C, 0.580 USD/t below Fe.
- Canonical Ru-Fe gap decomposition integrated into the NH3 mechanism paragraph.
- Joint cost MC: P(C_Fe < C_Ru) = 5000/5000; alpha* p05 / median / p95 = 70.78x / 174.27x / 462.00x.
- Backward design: canonical alpha* = 201.22x versus 2.525x maximum scaling-consistent headroom.
- MeOH cost-MC rank preservation: 5000/5000 under canonical D01; active-Re replacement extension reported separately.
- Agent oracle: 7-CU scorer floor retained as diagnostic; 22-CU protocol-complete S1-S3 floor used for manuscript normalization.
- Non-binding Agent mechanism: narrow-window 0/20, 566 CU median decision stability, +148 CU median post-stability spend, 714 CU median final spend.

## Structural changes

The Results section now follows the current F1-F10 evidence chain:

1. decision-frontier inversion;
2. process reoptimization, uncertainty and Ru-price counterfactual;
3. backward design and reachability;
4. MeOH selectivity-recycle transfer;
5. cross-reaction coupling topology;
6. Au/TiO2 rank-preservation control;
7. decision-aware compute allocation.

The Discussion now treats the equal-price result as a causal boundary and distinguishes it from local robustness around the canonical economic regime. Agent efficiency is normalized to the 22-CU scientific oracle and the non-binding failure mode is attributed first to loss of search compression, then to post-stability overrun.

## Deterministic consistency checks

- Figure citations present: Fig. 1 through Fig. 10.
- Highest reference cited: 38.
- Working-reference entries: 38.
- No stale `remains top-ranked in 28.2%` wording.
- No `not metal price alone` wording.
- No TODO/FIXME/guardrail drafting language.
- Required 2026-09-20 headline numbers are present in the draft.
- F3 and F10 R renders and SHA-256 manifests exist on main.

## Top-journal structural benchmark

Morandi et al., *Nature Chemical Engineering* 3, 169-180 (2026) is retained as the closest recent structural benchmark for an end-to-end heterogeneous-catalysis framework. The useful architectural features adopted here are: a short problem-first Introduction, a framework section that does not displace the scientific results, application-driven Results subsections, and detailed implementation moved to Methods/SI rather than embedded in the main narrative.

## Remaining production work

1. visually inspect the final R-rendered F3 and F10 assets and re-lock them;
2. assign final SI figure/table numbers to the NH3 cost decomposition and MeOH active-Re replacement extension;
3. verify DOI/metadata for the complete working bibliography;
4. finalize Data Availability and Code Availability language against a frozen release/tag;
5. export v6 to DOCX/PDF only after the Markdown/caption/figure cross-audit closes.
