# Research freeze — 2026-09-10

## Status

The current manuscript evidence package is considered **research-complete for drafting**, with one narrowly defined data-lineage exception identified by the second-pass audit. No additional large API batch, budget sweep, model tier, reaction case or agent-policy variant is required for the present manuscript.

This freeze does not alter any previously frozen protocol or scientific model. It records the transition from experiment generation to manuscript integration.

### Targeted exception opened by the final audit

The historical cross-reaction MeOH-CH4 / NH3-TOF normalized-leverage ratio **273–410 (midpoint ~328)** is no longer treated as a current NH3-FINAL-1.1 manuscript result. Its source normalization predates FINAL-1.1 and explicitly uses the archived ~10.2 USD/t NH3 reduced-cost regime. Because FINAL-1.1 changed the NH3 pressure-CAPEX/economic closure, the audit requires one deterministic revalidation with the already frozen FINAL-1.1 harness and the exact historical TOF-leverage definition.

This is the **only scientific calculation reopened** under the freeze. It is specified in `F9A_FINAL_1_1_REVALIDATION_TASK.md`. If exact historical metric equivalence cannot be established, the correct outcome is to keep Figure 9A qualitative rather than invent a replacement metric or rescale the old ratio.

The qualitative cross-reaction pathway comparison remains valid:

- NH3: activity -> catalyst inventory / reactor demand;
- MeOH: selectivity -> feed loss / purge / recycle.

Audit addendum: `CLAIM_EVIDENCE_AUDIT_ADDENDUM_A1_2026-09-10.md`.

## Scientific evidence frozen for the manuscript

### NH3 — NH3-FINAL-1.1

- atomic activity top-3: **Ru > Os > Fe**;
- optimized economic top-3: **Fe > Ru > Os**;
- Fe / Ru / Os catalyst-dependent costs: **15.292 / 22.031 / 25.832 USD/t NH3**;
- Top-3 Spearman rho: **-0.50**; full-15 raw rho: **0.929**;
- Fe feasibility / Top-1 survival / Top-3 actionable: **79.9% / 28.2% / 94.0%**;
- Ru activity-only parity target: **201.22x**;
- scaling-consistent activity headroom: **1.090x at 673 K; 2.525x maximum**;
- strict-scaling lowest Ru cost: **21.398 USD/t NH3 at E_N = -1.215 eV**.

### CO2-to-MeOH — MEOH-D01-v3

- upstream per-Re rank: **1% Re 250 C > 1% Re 200 C > 5% Re 200 C > 5% Re 250 C**;
- economic rank: **5% Re 200 C > 1% Re 200 C > 1% Re 250 C > 5% Re 250 C**;
- NPC in economic-rank order: **943 / 967 / 975 / 1258 EUR/t**;
- Spearman rho **0.20**, Kendall tau **0**, pairwise inversions **3/6**;
- dominant interpretation: **selectivity-recycle pathway**.

### Rank-preservation control — Au/TiO2-RP

- canonical **V1.1**: activity and downstream burden preserve **2 > 3 > 4 > 5 > 6 nm**, rho = tau = **1.000**, **0** inversions, **10,000/10,000** predefined draws preserve the full ranking;
- supporting **V1.3**: moderate semi-open operation retains mean rho **0.99214** in 273.15-293.15 K and **0.96802** in 273.15-313.15 K, showing that preservation is not confined to one perfectly fixed operating point.

### Decision-aware Agent Harness

The original **DISCOVER V1** remains the frozen formal benchmark. The completed **DISCOVER-BOUNDARY-C1** extension sharpens its boundary interpretation without changing the frozen task, prompt, action schema, cost model, scorer, stopping rule or policy-D constants.

C1 boundary result:

| tier / policy | 175 CU | 225 CU |
|---|---:|---:|
| strong E | **19/20** | **20/20** |
| mini E | **0/20** | **6/20** |
| nano E | **0/20** | **0/20** |
| deterministic fixed-VOI D | incomplete | complete |

- D reaches a complete decision at **206 CU**.
- Strong E constructs a narrow process window in **20/20** runs at 175 CU, versus mini **4/20** and nano **0/20**.
- Above the D threshold, strong E does not provide a raw-compute saving: it reaches the full decision at about **218-221 CU** versus D at **206 CU**.
- Phase B completed **80/80 formal runs**, with **0 smoke**, **0 infrastructure retry**, **0 driver exception**, and frozen hashes **15/15 PASS before and after**.

Manuscript interpretation:

> Under the frozen benchmark protocol, adaptive decision recovery below the fixed policy's completion threshold is model-tier dependent. A sufficiently capable model can exploit a narrow, high-value computation path under a constrained budget, but this advantage does not transfer to the two tested weaker tiers and does not imply universal raw-compute savings.

Policy advantage, model capability and raw compute efficiency must remain separate quantities.

## Evidence-integrity notes

- Phase A reduction of the 150 / 200 / 250 CU strong cells is documented prospectively in `DISCOVER_BOUNDARY_C1_ADDENDUM_A1.md` relative to result inspection.
- The original C1 preregistration specified a broader Phase B and smoke runs. The executed Phase B was reduced before its first API call to 175 / 225 CU and no smoke. This deviation is transparently recorded post-run in `DISCOVER_BOUNDARY_C1_ADDENDUM_A2.md`; it must not be described as the original preregistered design.
- The 200-CU C1 strong estimate remains **8/8** new runs and is not pooled with the separate historical DISCOVER V1 5/5 sample for the confirmatory estimate.
- The first-pass claim audit found no contradiction among the promoted headline values; the second-pass temporal/lineage check identified the F9A cross-reaction ratio as the one genuine revalidation exception. See `CLAIM_EVIDENCE_AUDIT_ADDENDUM_A1_2026-09-10.md`.

## Figure-lock state after deterministic closure

- **F7:** locked current MeOH ranking asset.
- **F8:** **LOCKED**; GitHub Actions run **34449914480** generated and verified SVG/PDF/PNG plus SHA-256 manifest from the frozen R renderer and D01 v3 data.
- **F9B:** locked canonical Au/TiO2 V1.1 SVG.
- **F1–F6:** numerical results frozen, but direct FINAL-1.1 raw provenance/assets still require repository closure before final figure lock.
- **F9A:** **QUALITATIVE-ONLY / METRIC_EQUIVALENCE_NOT_ESTABLISHED**. The historical 273–410 (~328) ratio is excluded from current manuscript claims because the retained repository does not establish the exact historical NH3 TOF leverage metric or contain the frozen FINAL-1.1 source harness required for an exact rerun.

## Freeze rule

From this point, do not add new experimental cells solely to improve the narrative. New computation is justified only if the final audit reveals one of the following: a scorer/driver defect, a frozen-state mismatch, an unreproducible canonical number, an incorrect data lineage, or a manuscript claim not supported by the retained evidence.

The repository-level F9A exception is now closed as **METRIC_EQUIVALENCE_NOT_ESTABLISHED**. A quantitative F9A may be reopened only if the original historical metric implementation and the frozen NH3-FINAL-1.1 source harness are recovered with provenance; it does not authorize model redesign, cost rescaling or exploratory parameter changes.

The remaining work package is manuscript production: NH3 provenance import/content-addressing for F1–F6, final figure/caption assembly, Methods/SI completion, and reproducibility documentation.
