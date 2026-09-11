# Current project status

Snapshot date: **2026-09-10**

## Research state

**RESEARCH FROZEN FOR DRAFTING.** The current scientific and Agent evidence package is complete for manuscript integration. Do not add new large API batches, budget points, model tiers, reaction cases or agent-policy variants solely to improve the story.

The cross-reaction numerical exception opened by the second-pass audit is closed as **qualitative-only**: the historical MeOH-CH4 / NH3-TOF normalized-leverage ratio **273–410 (midpoint ~328)** remains excluded because the original pre-audit NH3 TOF economic-leverage implementation has not been established. The pathway-level comparison remains valid; no replacement ratio is introduced.

The NH3-FINAL-1.1 provenance transfer is now complete. The original source-harness closure and F1-F6 assets are vendored under `provenance/nh3_final_1_1/source_harness/`. Cross-platform CI reports **`PROVENANCE_VALIDATED_READY_FOR_LOCK`** with **13/13 canonical anchors**, **6/6 evidence classes**, **6/6 figure mappings**, **28/28 manifest files present**, and **0 hash mismatches**. F1-F6 are therefore **LOCKED** to the canonical FINAL-1.1 SVG assets. No scientific model was rerun during this closure.

Primary freeze record: `docs/RESEARCH_FREEZE_2026-09-10.md`.  
NH3 provenance pointer: `docs/NH3_FINAL_1_1_PROVENANCE_POINTER.md`.  
NH3 figure-lock record: `docs/NH3_FINAL_1_1_FIGURE_LOCK_2026-09-10.md`.

## Canonical naming

The authoritative naming registry is `docs/VERSION_REGISTRY.md`; the machine-readable copy is `data/version_registry.json`.

Current labels:

- scientific model: **NH3-FINAL-1.1**;
- methanol case: **MEOH-D01-v3**;
- canonical rank-preservation control: **Au/TiO2-RP V1.1**;
- latest supporting rank-preservation robustness: **Au/TiO2-RP V1.3**;
- Agent umbrella: **Decision-aware Agent Harness**;
- supporting Agent benchmarks: **DRIFT v2** and **TRANSFER v1**;
- formal frozen Agent benchmark: **DISCOVER V1**;
- completed confirmatory boundary extension: **DISCOVER-BOUNDARY-C1**;
- **DISCOVER V2** is reserved for a future protocol redesign and is not a completed current benchmark.

Version numbers are family-specific. A higher number in one family does not supersede another family, and a supporting extension does not automatically replace the canonical evidence source.

## Canonical ammonia model

- Canonical version: **NH3-FINAL-1.1**
- Promotion status: approved and frozen on 2026-09-05
- Archived historical version: NH3-FINAL-1.0
- Canonical run identifier: `outputs/nh3_final_20260905T134204Z`

### Frozen ammonia ground truth

- Atomic activity ranking: **Ru > Os > Fe**
- Optimized economic ranking: **Fe > Ru > Os**
- Fe cost: **15.292 USD/t NH3**
- Ru cost: **22.031 USD/t NH3**
- Os cost: **25.832 USD/t NH3**
- Ru/Fe ratio: **1.441**
- Top-3 Spearman rho: **-0.50**
- Top-3 Kendall tau: **-0.33**
- Full 15-metal raw Spearman rho: **0.929**
- Fe feasibility: **0.799**
- Fe Top-1 survival: **0.282**
- Fe Top-3 actionable: **0.940**
- Ru activity-only break-even: **201.22x**
- Scaling headroom: **1.090x at 673 K; 2.525x maximum over the process-state library**
- Strict-scaling lowest Ru cost: **21.398 USD/t NH3 at E_N = -1.215 eV**

NH3-FINAL-1.1 removes the earlier pressure-grid boundary artefact by extending the pressure grid to 10-1000 bar and adding pressure-dependent equipment CAPEX. Representative optima are approximately **425 C / 180 bar / 30 C separator** for Fe and **450 C / 425 bar / 25 C** for Ru; Os has a broad shallow high-pressure minimum.

### NH3 provenance closure

The original FINAL-1.1 source record is now vendored and content-addressed. The imported bundle includes:

- `configs/nh3_final.yaml` and the archived comparison config;
- `outputs/nh3_final_20260905T134204Z/closure/`;
- `PRESSURE_CAPEX_INDEPENDENT_AUDIT_2026-09-05.md`;
- `NH3_FINAL_1_1_PRESSURE_CAPEX_REPORT_2026-09-05.md`;
- `audits/audit_pressure_capex_handcalc_2026-09-05.py`;
- `PROMOTE_NH3_FINAL_1_1_CHECKLIST.md`;
- `NH3_FINAL_1_1_CONSISTENCY_CLOSURE.md`;
- paired SVG + PNG assets for F1-F6 from the canonical run;
- `SOURCE_MANIFEST.json` with source SHA-256 values and explicit `FIGURE_ASSET_MAP.json`.

A first Linux checkout revealed that Git line-ending normalization had changed 18 text-like files. The repository now pins `provenance/nh3_final_1_1/source_harness/** -text` in `.gitattributes`. A deterministic CI repair rewrote a file only when a pure LF-to-CRLF or CRLF-to-LF transform reproduced the original source-manifest SHA-256 exactly. The final Linux validation reports **0 hash mismatches**. This was a byte-transport correction only; all canonical scientific anchors were unchanged and no scientific calculation was executed.

F1-F6 are locked in `docs/NH3_FINAL_1_1_FIGURE_LOCK_2026-09-10.md` and `data/figure_lock_registry_2026-09-10.csv`.

## Current NH3 lever ordering

Current 1.1 reach values:

- Metal recovery: **0.69**
- Catalyst lifetime: **0.16**
- Electricity: **0.12 at 20 USD/MWh**, weakly discriminatory / absolute-only
- Pressure upper bound: no longer a valid lever because Ru and Os are interior to the grid
- Bed-cap increase: inactive under the current Fe optimum

Current ordering: **recovery >> lifetime >> other tested levers**.

## Canonical methanol case — MEOH-D01-v3

The current MeOH evidence uses four Re/TiO2 catalyst-temperature states and an explicit recycle/separation loop at 2% purge.

Using STY per g Re as the upstream intrinsic-productivity metric:

- upstream order: **1 wt% 250 C > 1 wt% 200 C > 5 wt% 200 C > 5 wt% 250 C**;
- economic order: **5 wt% 200 C > 1 wt% 200 C > 1 wt% 250 C > 5 wt% 250 C**;
- NPC: **943 / 967 / 975 / 1258 EUR/t** in economic-rank order;
- Spearman rho: **0.20**;
- Kendall tau: **0**;
- pairwise inversions: **3/6**;
- upstream winner falls from **#1 to #3**.

The mechanistic interpretation is a **selectivity-recycle pathway**: methane suppression is the strongest tested local economic lever, with STY / conversion / CH4-suppression leverage = **0.00289 / 0.05883 / 0.37579**.

## Cross-reaction leverage status

The pathway-level comparison remains valid:

- NH3: **activity -> inventory / reactor-demand**;
- MeOH: **selectivity -> feed-loss / purge / recycle**.

The historical **273–410 (~328 midpoint)** ratio is not a current FINAL-1.1 claim. GitHub Actions run **34449914480** closed the repository-level revalidation attempt as **METRIC_EQUIVALENCE_NOT_ESTABLISHED** because the original pre-audit implementation of the historical NH3 TOF economic-leverage metric could not be established. The FINAL-1.1 source-harness provenance is now present, but that does not retroactively establish the missing historical metric definition.

Figure 9A is therefore **qualitative-only** in the current manuscript. Do not rescale the old ratio or substitute a newly defined cross-reaction metric merely to restore a number.

## Rank-preservation family — Au/TiO2-RP

### Au/TiO2-RP V1.1 — canonical control

Literature-calibrated fixed-condition result:

- activity order: **2 > 3 > 4 > 5 > 6 nm**
- downstream catalyst-burden order: **2 > 3 > 4 > 5 > 6 nm**
- Spearman rho: **1.000**
- Kendall tau: **1.000**
- pairwise inversions: **0**
- 10,000/10,000 predefined literature-envelope draws preserve the full ranking
- 6 nm / 2 nm required-catalyst ratio: **8.064x**

This remains the manuscript-level canonical counterfactual because it is literature calibrated and physically interpretable.

### Au/TiO2-RP V1.3 — latest supporting robustness

V1.3 relaxes the perfectly fixed operating point while keeping common chemistry and process topology.

Moderate stress:

- **273.15-293.15 K**: exact preservation **92.16%**, mean rho **0.99214**, rho >= 0.9 in **99.98%** of draws;
- **273.15-313.15 K**: exact preservation **72.62%**, mean rho **0.96802**, rho >= 0.9 in **97.56%** of draws.

V1.3 is the latest robustness extension but does **not** replace V1.1 as the canonical control because its process penalties remain generic monotone penalties rather than a fully literature-derived plant TEA.

## Decision-aware Agent Harness

The Agent system is organized as:

```text
Layer A — deterministic multiscale harness
Layer B — decision layer
```

The decision layer evaluates current evidence, identifies decision-sensitive uncertainties or catalyst levers, selects admissible scientific actions, updates ranking/feasibility/reachability evidence and decides whether to stop, continue or redirect computation.

### Supporting benchmark families

- **DRIFT v2** — completed model/interface drift-diagnosis benchmark.
- **TRANSFER v1** — completed reaction-transfer benchmark covering transfer classification, minimum-sufficient-model selection, lever identification and next-calculation scoring.

These support the broader Agent-Harness description but are not the formal quantitative Agent benchmark used for the manuscript claim.

### DISCOVER V1 — frozen canonical Agent benchmark

DISCOVER V1 remains the formal closed-book, budgeted decision-allocation benchmark. It exposes 11 fine-grained actions and uses `1 CU = 1000 MKM state solves` as the scientific-compute budget.

Original cross-model evaluation:

- weak: `gpt-5.4-nano-2026-03-17`
- medium: `gpt-5.4-mini-2026-03-17`
- strong: `gpt-5.5-2026-04-23`
- budgets: **200, 250, 300, 500, 800, 1200, 2000 CU**
- anonymous complete decision: **6/35 / 15/35 / 35/35**
- tier trend: **Z = 6.95**
- pre-registered E-vs-D Go criterion: **not met**

The original supported conclusion is retained: a strong model can execute and exploit decision-aware allocation, but adaptive Agent superiority over fixed-VOI D is capability-dependent rather than universal.

### DISCOVER-BOUNDARY-C1 — completed confirmatory extension

C1 uses the **unchanged frozen DISCOVER V1 protocol** and sharpens the location and interpretation of the strong-tier adaptive effect.

Deterministic fixed-VOI policy D reaches the complete decision at **206 CU**.

| tier / policy | 175 CU | 225 CU |
|---|---:|---:|
| strong E | **19/20** | **20/20** |
| mini E | **0/20** | **6/20** |
| nano E | **0/20** | **0/20** |
| fixed-VOI D | incomplete | complete |

Mechanistic evidence:

- strong narrow-window construction at 175 CU: **20/20**;
- mini at 175 CU: **4/20**;
- nano at 175 CU: **0/20**;
- above the D threshold, strong E reaches the complete decision at about **218-221 CU** versus D at **206 CU**.

Therefore the manuscript-level C1 claim is a **budget-localized, model-tier-dependent decision-completion advantage**, not a universal raw-compute saving. Policy advantage, model capability and compute efficiency must be reported separately.

Phase B completed **80/80 formal runs** (mini 175/225 CU x20 each; nano 175/225 CU x20 each), with **0 smoke runs, 0 infrastructure retries and 0 driver exceptions**. Frozen hashes were **15/15 PASS before and after**.

Integrity note: the original C1 preregistration specified a broader five-budget Phase B and smoke runs. The executed two-budget/no-smoke Phase B was selected for cost control **before the first Phase B API call** but is nonetheless a design deviation from the original preregistration. It is recorded transparently as a post-run audit in `docs/DISCOVER_BOUNDARY_C1_ADDENDUM_A2.md` and must not be presented as the original preregistered design.

DISCOVER V1 remains frozen. Any change to its pinned task, prompt, action schema, cost model, scorer, stopping rule or policy-D constants defines **DISCOVER V2**. C1 is confirmatory sampling on V1, not V2.

## Figure / manuscript integration status

Current main-text evidence state:

- **F1-F6** — LOCKED to the canonical NH3-FINAL-1.1 SVG assets after full provenance validation.
- **F7** — LOCKED current MeOH upstream-to-economic ranking asset.
- **F8** — LOCKED; GitHub Actions run 34449914480 rendered and verified the frozen R source to SVG/PDF/PNG, with SHA-256 manifest stored in `figures/meoh/F08_RENDER_SHA256.txt`.
- **F9B** — LOCKED canonical Au/TiO2 V1.1 SVG.
- **F9A** — qualitative-only after `METRIC_EQUIVALENCE_NOT_ESTABLISHED`; the historical 273–410 ratio remains archived and is excluded from the current manuscript.

`docs/MANUSCRIPT_SKELETON.md` contains the C1 boundary result directly in Results §3.7, Discussion §4.6 and Methods item 13. The current F9A text is qualitative at pathway level.

## Next work package

All non-Agent scientific evidence and main figure sources remain frozen. Remaining work is manuscript production:

1. assemble final figure captions and main/Extended Data allocation;
2. finish Methods and Supporting Information around the locked evidence;
3. complete reproducibility/readme packaging and the final claim-to-figure audit;
4. produce the formal manuscript draft and submission package.

## 2026-09-11 Agent-line directed extension (supervisor request)

The research freeze now carries a **narrow, directed exception for the Agent line only**. Every NH3, MeOH, Au/TiO2 and
figure result stays frozen; no scientific model is rerun. Seven items were requested. Three are closed from the existing
frozen traces with no new compute, and are recorded in `docs/DISCOVER_BOUNDARY_C1_ADDENDUM_A3_2026-09-11.md`:

- the **canonical narrow-window rule** is fixed (window strictly smaller than the 14,136-state domain *and* used by a
  later scoped action). This corrects mini at 175 CU from 4/20 to **0/20** and strong at 225 CU from 3/20 to **0/20**,
  and shows narrow-window allocation is used only below the fixed-policy threshold and only by the strong tier;
- **175 vs 225 CU consistency**: the reachability verdict and both scaling-headroom values are identical at the two
  budgets (Ru `unreachable` 20/20; 1.0899 / 2.5246), while the canonical break-even 201.223443 is recovered 15/20 at
  175 CU against 20/20 at 225 CU, with all five deviations traced to discrete window-scope artefacts;
- the **error taxonomy** splits every 0-CU action error into interface / budget / sequencing. The 133 errors are the
  mini tier total; nano is budget-blind (81% unaffordable requests), mini is interface- and ordering-limited, and the
  single strong 175 CU failure is a probe-before-target ordering failure.

Results §3.7 of `docs/MANUSCRIPT_SKELETON.md` now states the claim as **complete decision recovery below the
fixed-policy compute threshold**. A universal compute saving is not claimed anywhere.

Two further items were then executed as 53 formal runs (0 infrastructure retries, 0 driver exceptions, frozen hashes
15/15 PASS before the batch) and are recorded in `docs/DISCOVER_BOUNDARY_C1_ADDENDUM_A4_2026-09-11.md`:

- **strong 125 and 150 CU at n = 20 each: 20/20 complete decisions at both budgets.** The completion floor is therefore
  below the tested range and is not yet located; at 125 CU the median run completes after 80 CU, 39% of D's 206 CU. The
  canonical break-even target has a separate, higher floor: 20/20 at 225 CU, 15/20 at 175 CU, 11/20 at 150 and 125 CU;
- **the E2 interface arm is a negative result.** Typed tool parameters plus an explicit remaining-budget block removed
  the mini interface failure mode entirely (undeclared-argument errors 18 → 0, no-tool-call turns 16 → 4) and raised
  correct winner identification from 14/20 to 19/20, but complete decisions stayed 0/20. mini ran `BACKWARD` in 0/20
  runs under both interfaces, so the barrier is chain ordering under a binding budget, not interface expressiveness.

A further 98 formal runs then closed three more items (frozen hashes 15/15 PASS before and after every batch, 0
infrastructure retries, 0 driver exceptions), recorded in `docs/DISCOVER_BOUNDARY_C1_ADDENDUM_A5_2026-09-11.md`:

- **the completion floor is now located. strong 75 CU is 20/20** (median 52 CU to the complete decision, 25% of D's
  206 CU), completion stays at 19–20/20 across 75–250 CU, and at **50 CU it finally breaks to 13/20** (P = 0.65). The
  **lowest stable completion threshold is 75 CU**. The 50 CU failures are affordability failures on the closing step,
  not reasoning failures: winner and decision pair are still 20/20, and six of seven incomplete runs ran `BACKWARD`
  then could not afford the 2–4 CU reachability classification. The hard floor lies between roughly 35 and 50 CU;
- **uncapped condition (20 runs at a 5000 CU allowance that never binds): the agent is efficient only because the
  budget binds.** All 20 complete the decision and all 20 stop on their own rule, but median spend is 714 CU — 3.5× D's
  threshold, worst run 3021 CU — and the decision-stable point moves from 218 CU to 566 CU, with a median 148 CU (33%
  of spend) consumed after the decision is already complete. This directly contradicts any universal compute saving;
- **mini saturation sweep: a plateau, not a trend.** Completion is 0/20, 6/20, 4/20, 7/20 at 175, 225, 300, 400 CU with
  overlapping intervals, and the number of runs that execute `BACKWARD` at all is pinned at exactly 7/20 at 225, 300
  and 400 CU. The compute at which mini would match strong-175 does not exist in the tested range. With the negative
  E2 interface result, two independent interventions — more compute and a better interface — both fail to move mini.

**Metric correction.** The trace's per-step `action_cost` is the pre-execution `env.quote()` and overstates the real
charge for `OPTIMIZE_PROCESS`, so the frozen `cu_to_full` metric that sums it is inflated in 31 of 297 runs (per-cell
median inflation 0 CU, single-run maximum 58 CU). Two published medians change: strong 175 CU from 140 to **124 CU**
and strong 150 CU from 106 to **102 CU**. No completion rate, break-even value, reachability verdict, narrow-window
count or error count is affected. `discover/boundary_c1_metrics.py` was not modified; the ledger-true value is computed
in `tools/discover/c1_overrun_analysis.py`, which reports the quoted value and the inflation alongside it.

All seven supervisor items are now closed except the open-source strong-tier control, which stays deferred to the
reproducibility-package stage.

## Version policy

- Use **NH3-FINAL-1.1** for all current NH3 manuscript numbers.
- Use **MEOH-D01-v3** for the current MeOH case.
- Use **Au/TiO2-RP V1.1** as canonical rank-preservation evidence and **V1.3** only as supporting robustness.
- Use **DISCOVER V1** as the frozen formal Agent benchmark and **DISCOVER-BOUNDARY-C1** as its completed confirmatory boundary extension.
- Use **DRIFT v2** and **TRANSFER v1** only with their family names.
- Do not describe **DISCOVER V2** as completed unless a new protocol is explicitly frozen and evaluated.
- Frozen filenames and hash-pinned protocol files are not renamed.
