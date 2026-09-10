#!/usr/bin/env python3
"""Synchronize manuscript-facing documentation after F8/F9A GitHub Actions closure.

This script changes documentation only. It does not run or alter any scientific model.
Every section replacement is marker-bounded and fails if the expected markers are absent.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_section(rel: str, start: str, end: str, new_body: str) -> None:
    p = ROOT / rel
    text = p.read_text(encoding="utf-8")
    i = text.find(start)
    if i < 0:
        raise SystemExit(f"start marker not found in {rel}: {start}")
    j = text.find(end, i + len(start))
    if j < 0:
        raise SystemExit(f"end marker not found in {rel}: {end}")
    replacement = new_body.rstrip() + "\n\n"
    p.write_text(text[:i] + replacement + text[j:], encoding="utf-8")


def replace_once(rel: str, old: str, new: str) -> None:
    p = ROOT / rel
    text = p.read_text(encoding="utf-8")
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"expected exactly one match in {rel}, found {n}: {old}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


replace_section(
    "README.md",
    "## Cross-reaction economic leverage — quantitative ratio on hold",
    "## Au/TiO2-RP — rank-preservation family",
    """## Cross-reaction pathway comparison — qualitative-only after provenance audit

The qualitative mechanism comparison remains part of the current paper:

```text
NH3  : activity -> catalyst inventory / reactor demand
MeOH : selectivity -> feed loss / purge / recycle
```

The previously quoted normalized ratio **273–410** (midpoint approximately **328**) is an archived pre-NH3-FINAL-1.1 result and is **not a current manuscript value**. GitHub Actions run **34449914480** searched the full repository history with audit-generated files excluded from provenance proof and found **no pre-audit code-level implementation** that establishes the original NH3 TOF/activity perturbation, finite-difference definition, economic reoptimization and raw reduced-cost leverage. The current repository also does not contain `configs/nh3_final.yaml` or `outputs/nh3_final_20260905T134204Z`.

F9A is therefore classified **METRIC_EQUIVALENCE_NOT_ESTABLISHED / QUALITATIVE-ONLY**. No replacement ratio is inferred by cost rescaling or by defining a new proxy metric. A quantitative F9A may be reopened only if the original metric implementation and frozen FINAL-1.1 source harness are later imported with provenance.

See [`docs/CROSS_REACTION_LEVERAGE_PROVENANCE_POINTER.md`](docs/CROSS_REACTION_LEVERAGE_PROVENANCE_POINTER.md) and [`artifacts/f9a_ci/CROSS_REACTION_FINAL1_1_CI_ATTEMPT.md`](artifacts/f9a_ci/CROSS_REACTION_FINAL1_1_CI_ATTEMPT.md).""",
)

replace_section(
    "STATUS.md",
    "## Cross-reaction leverage status",
    "## Rank-preservation family — Au/TiO2-RP",
    """## Cross-reaction leverage status

The pathway-level comparison remains valid:

- NH3: **activity -> inventory / reactor-demand**;
- MeOH: **selectivity -> feed-loss / purge / recycle**.

The historical **273–410 (~328 midpoint)** ratio is not a current FINAL-1.1 claim. GitHub Actions run **34449914480** closed the repository-level revalidation attempt as **METRIC_EQUIVALENCE_NOT_ESTABLISHED**: no pre-audit implementation of the historical NH3 TOF economic-leverage metric could be recovered from this repository, and the frozen FINAL-1.1 config/output tree required to rerun that exact metric is not present here.

Figure 9A is therefore **qualitative-only** in the current manuscript. Do not rescale the old ratio or substitute a newly defined cross-reaction metric merely to restore a number.""",
)

replace_section(
    "docs/RESULTS_AT_A_GLANCE.md",
    "## Cross-reaction leverage — quantitative value on hold",
    "## Rank-preservation control",
    """## Cross-reaction pathway comparison — qualitative-only

The current supported cross-reaction statement is mechanistic:

```text
NH3   : activity -> catalyst inventory / reactor demand
MeOH  : selectivity -> feed loss / purge / recycle
```

The MeOH CH4-suppression leverage **0.3757939** remains directly traceable. The historical denominator-aligned MeOH/NH3 ratio **273–410** (midpoint ~**328**) is retained only as an archived pre-FINAL-1.1 result. GitHub Actions run **34449914480** returned **METRIC_EQUIVALENCE_NOT_ESTABLISHED** because the exact historical NH3 TOF economic-leverage implementation and the frozen FINAL-1.1 source harness are not retained in this repository.

Accordingly, no current quantitative cross-reaction ratio is reported. The paper retains the reaction-specific pathway contrast and does not manufacture a replacement metric.""",
)

replace_section(
    "docs/MANUSCRIPT_SKELETON.md",
    "### 3.5 Cross-reaction comparison reveals pathway-specific economic leverage",
    "### 3.6 A literature-calibrated control shows that multiscale propagation does not intrinsically invert rankings",
    """### 3.5 Cross-reaction comparison reveals pathway-specific propagation mechanisms

The two reaction cases resolve different catalyst-to-process pathways. In NH3, activity changes propagate primarily through catalyst inventory, reactor demand and process severity. In CO2-to-methanol, selectivity—particularly methane formation—changes feed loss, gas accumulation, purge, recycle and compression burden.

A previously reported denominator-aligned MeOH CH4-suppression / NH3 TOF leverage ratio of **273–410** (midpoint ~**328**) is not used as a current result. The repository-level provenance audit and GitHub Actions revalidation attempt could not establish the exact historical NH3 TOF-economic-leverage metric from pre-audit code, and the frozen FINAL-1.1 source harness required to rerun that exact definition is not retained in this repository. The result is therefore classified **METRIC_EQUIVALENCE_NOT_ESTABLISHED** rather than replaced by a newly constructed ratio.

The manuscript-level conclusion is consequently bounded to the directly supported mechanism: catalyst ranking changes are reaction- and process-pathway dependent. NH3 demonstrates an activity–inventory / reactor-demand route; MeOH demonstrates a selectivity–recycle route. The choice of upstream screening objective can further change which candidate is mis-ranked at the decision frontier.

Primary figure: F9A as a **qualitative pathway panel only**; no current cross-reaction numerical ratio.""",
)

replace_section(
    "docs/FIGURE_MAP.md",
    "### Figure 9A — Cross-reaction catalyst-economic leverage",
    "### Figure 9B — Au/TiO2 rank-preservation control",
    """### Figure 9A — Cross-reaction catalyst-to-process pathways

**Current status: QUALITATIVE-ONLY / METRIC_EQUIVALENCE_NOT_ESTABLISHED.**

The previous denominator-aligned MeOH CH4-suppression / NH3 TOF normalized-leverage ratio of **273–410** (midpoint ~**328**) belongs to the archived pre-NH3-FINAL-1.1 normalization and is not a current figure headline. GitHub Actions run **34449914480** did not recover a pre-audit code-level implementation sufficient to prove the exact historical NH3 TOF economic-leverage definition, and the frozen FINAL-1.1 source harness needed for an exact rerun is not present in this repository.

**Content**
- NH3: activity -> catalyst inventory / reactor demand / process severity.
- MeOH: selectivity -> feed loss / gas accumulation / purge / recycle / compression.
- No cross-reaction numerical ratio is plotted unless the original metric implementation and frozen FINAL-1.1 harness are later recovered.

**Claim supported:** the dominant catalyst-to-economic propagation mechanism is **reaction- and process-pathway dependent**. Figure 9A is a mechanism/topology comparison, not a quantitative leverage-ratio panel.""",
)

replace_once(
    "docs/FIGURE_MAP.md",
    "**Status:** scientific design frozen; vector/raster render pending. Rendering must not change the metric or canonical 2% comparison.",
    "**Status:** **LOCKED.** The frozen R renderer was executed by GitHub Actions and verified SVG/PDF/PNG outputs plus a SHA-256 manifest. Rendering did not change the metric or canonical 2% comparison.",
)
replace_once(
    "docs/FIGURE_MAP.md",
    "F9A  pathway-specific economic leverage across NH3 and MeOH — quantitative ratio pending FINAL-1.1 revalidation",
    "F9A  qualitative catalyst-to-process pathway comparison across NH3 and MeOH; no current cross-reaction leverage ratio",
)
replace_once(
    "docs/FIGURE_MAP.md",
    "The historical cross-reaction **273–410 (~328)** ratio is also treated as pre-FINAL-1.1 until explicitly revalidated.",
    "The historical cross-reaction **273–410 (~328)** ratio remains archived pre-FINAL-1.1 evidence and is excluded from the current manuscript because metric equivalence could not be established from the retained source history.",
)

replace_once(
    "figures/README.md",
    "`REVALIDATION_REQUIRED_AFTER_NH3_FINAL_1.1` means the prior numerical result is traceable to the archived NH3-FINAL-1.0 regime and must not be used as a current FINAL-1.1 manuscript value until the same calculation is repeated under the frozen 1.1 harness.",
    "`METRIC_EQUIVALENCE_NOT_ESTABLISHED` means the archived numerical result cannot be promoted because the exact historical metric implementation is not recoverable from the retained repository evidence; the current manuscript must remain qualitative for that comparison.",
)
replace_once(
    "figures/README.md",
    "| F8 | Methane accumulation / purge / selectivity leverage | **DESIGN FROZEN; RENDER PENDING** — the final Panel A+B scientific specification is frozen in `docs/F8_METHANOL_FIGURE_LOCK_SPEC.md`; final editable/vector plus raster rendering remains. Current GitHub-hosted workflow attempts failed before any job step was assigned/executed, so this is an infrastructure/render blocker rather than a scientific-data failure. |",
    "| F8 | Methane accumulation / purge / selectivity leverage | **LOCKED** — GitHub Actions run 34449914480 rendered and verified `F08_MeOH_selectivity_recycle_D01v3.svg/.pdf/.png`; SHA-256 manifest is `F08_RENDER_SHA256.txt` and the canonical SVG blob is pinned in the figure registry. |",
)
replace_once(
    "figures/README.md",
    "| F9A | Cross-reaction catalyst-economic leverage | **REVALIDATION REQUIRED AFTER NH3-FINAL-1.1** — legacy 273–410 (~328 midpoint) lineage predates FINAL-1.1 and is held out of the current manuscript until the frozen 1.1 TOF economic leverage is recalculated with the same definition |",
    "| F9A | Cross-reaction catalyst-to-process pathways | **QUALITATIVE-ONLY / METRIC_EQUIVALENCE_NOT_ESTABLISHED** — legacy 273–410 (~328 midpoint) is archived pre-FINAL-1.1 evidence and is excluded from the current manuscript; no substitute ratio is introduced |",
)
replace_section(
    "figures/README.md",
    "### Figure 8 frozen design",
    "## Cross-reaction Figure 9A",
    """### Figure 8 locked render

The Figure 8 scientific composition remains the frozen specification in [`../docs/F8_METHANOL_FIGURE_LOCK_SPEC.md`](../docs/F8_METHANOL_FIGURE_LOCK_SPEC.md):

- **Panel A:** NPC versus purge across the four literature catalyst–temperature states, with 2% marked as the canonical source point;
- **Panel B:** dot/lollipop comparison of local economic leverage for STY, single-pass conversion and CH4 suppression at 5 wt% Re / 250 C.

GitHub Actions run **34449914480** rendered and verified:

- `F08_MeOH_selectivity_recycle_D01v3.svg`
- `F08_MeOH_selectivity_recycle_D01v3.pdf`
- `F08_MeOH_selectivity_recycle_D01v3.png`
- `F08_RENDER_SHA256.txt`

The render passed the frozen 396-level purge-envelope and leverage-value checks. No scientific calculation or metric selection was changed during rendering.""",
)
replace_section(
    "figures/README.md",
    "## Cross-reaction Figure 9A",
    "## Rank-preservation control (`rank_preservation_control/`)",
    """## Cross-reaction Figure 9A

The archived **273–410** ratio is not lockable as a current FINAL-1.1 result. GitHub Actions run **34449914480** searched full repository history under a conservative provenance rule and classified the result **METRIC_EQUIVALENCE_NOT_ESTABLISHED**: no pre-audit implementation of the historical NH3 TOF economic-leverage metric was recovered, while the frozen FINAL-1.1 config/output tree is not present in this repository.

F9A is therefore a **qualitative catalyst-to-process pathway panel** in the current manuscript. It may contrast NH3 activity–inventory/reactor-demand coupling with MeOH selectivity–feed-loss/purge/recycle coupling, but it must not plot 273–410 as current or substitute a newly defined cross-reaction ratio.

See [`../docs/CROSS_REACTION_LEVERAGE_PROVENANCE_POINTER.md`](../docs/CROSS_REACTION_LEVERAGE_PROVENANCE_POINTER.md) and [`../artifacts/f9a_ci/CROSS_REACTION_FINAL1_1_CI_ATTEMPT.md`](../artifacts/f9a_ci/CROSS_REACTION_FINAL1_1_CI_ATTEMPT.md).""",
)

replace_section(
    "docs/RESEARCH_FREEZE_2026-09-10.md",
    "## Figure-lock state at freeze",
    "## Freeze rule",
    """## Figure-lock state after deterministic closure

- **F7:** locked current MeOH ranking asset.
- **F8:** **LOCKED**; GitHub Actions run **34449914480** generated and verified SVG/PDF/PNG plus SHA-256 manifest from the frozen R renderer and D01 v3 data.
- **F9B:** locked canonical Au/TiO2 V1.1 SVG.
- **F1–F6:** numerical results frozen, but direct FINAL-1.1 raw provenance/assets still require repository closure before final figure lock.
- **F9A:** **QUALITATIVE-ONLY / METRIC_EQUIVALENCE_NOT_ESTABLISHED**. The historical 273–410 (~328) ratio is excluded from current manuscript claims because the retained repository does not establish the exact historical NH3 TOF leverage metric or contain the frozen FINAL-1.1 source harness required for an exact rerun.""",
)
replace_once(
    "docs/RESEARCH_FREEZE_2026-09-10.md",
    "The current F9A exception satisfies the incorrect-data-lineage criterion but is restricted to **repeating the exact historical leverage calculation under the already frozen NH3-FINAL-1.1 model**. It does not authorize model redesign or exploratory parameter changes.\n\nThe next work package is manuscript integration: targeted F9A closure, NH3 provenance import/content-addressing, figure locking, Methods/SI completion, and final reproducibility documentation.",
    "The repository-level F9A exception is now closed as **METRIC_EQUIVALENCE_NOT_ESTABLISHED**. A quantitative F9A may be reopened only if the original historical metric implementation and the frozen NH3-FINAL-1.1 source harness are recovered with provenance; it does not authorize model redesign, cost rescaling or exploratory parameter changes.\n\nThe remaining work package is manuscript production: NH3 provenance import/content-addressing for F1–F6, final figure/caption assembly, Methods/SI completion, and reproducibility documentation.",
)

print("Post-closure documentation sync complete.")
