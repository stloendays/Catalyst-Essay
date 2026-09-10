# Claim-to-evidence audit — 2026-09-10

Audit baseline: branch `experiment/discover-boundary-c1`, research state **FROZEN FOR DRAFTING**.

Purpose: verify that every manuscript-level numerical or mechanistic claim can be traced to the current canonical evidence before figures and prose are locked. This audit does not rerun scientific calculations and does not promote historical values.

## Status definitions

- **A — TRACEABLE:** manuscript claim is supported by a machine-readable result and its generating / analysis code or frozen run evidence is available in this repository.
- **B — CONSISTENT, PROVENANCE INCOMPLETE:** the claim agrees with the current canonical snapshot and manuscript summaries, but the underlying current raw run or generating script is not present in this repository. The claim is not contradicted, but its figure should not be frozen until the provenance pointer is closed.
- **C — STALE DOCUMENTATION:** the underlying result is traceable, but a manuscript-facing document still reports an earlier evidence state or omits a completed extension.
- **HOLD — NOT READY TO LOCK:** required figure asset, direct source data, or provenance chain is missing.

## 1. Abstract-level claims

| Claim | Current value / interpretation | Primary evidence | Status | Audit decision |
|---|---|---|---|---|
| NH3 atomic and economic rankings diverge at the decision frontier | Ru > Os > Fe -> Fe > Ru > Os; Top-3 rho = -0.50 | `data/canonical_results_2026-09-06.csv`; `docs/RESULTS_AT_A_GLANCE.md` | **B** | Numerically consistent. Current NH3-FINAL-1.1 raw output / generator is not vendored here. |
| CO2-to-MeOH undergoes a second catalyst-state ranking reshuffle | per-Re winner 1% Re/250 C falls to economic #3; rho = 0.20, tau = 0, 3/6 inversions | `data/meoh/meoh_candidate_ranking_D01v3.csv`; frozen D01 v3 workbook; `make_meoh_ranking_figure.py` | **A** | Keep. |
| Ranking inversion is conditional rather than inevitable | Au/TiO2 V1.1: rho = 1, tau = 1, 0 inversions, 10,000/10,000 full preservation | `data/rank_preservation_control_v1_1.csv`; `controls/au_tio2_rank_preservation_v1_1.py`; V1.1 report | **A** | Keep as canonical counterfactual control. |
| Rank preservation survives moderate semi-open freedom | primary moderate: exact 92.16%, mean rho 0.99214; wider sensitivity: 72.62%, rho 0.96802 | `data/rank_preservation_semiopen_v1_3_summary.csv`; V1.3 script/report | **A** | Supporting robustness only. |
| Ru activity-only parity target lies outside the current scaling-consistent manifold | 201.22x required vs 1.090x at 673 K / 2.525x process-library maximum | `data/canonical_results_2026-09-06.csv` | **B** | Numerically consistent; close direct NH3 run/script provenance before locking F5/F6. |
| NH3 and MeOH follow different economic-leverage pathways | NH3 activity -> inventory/reactor demand; MeOH selectivity -> feed loss/purge/recycle | NH3 canonical snapshot + MeOH direct loop outputs | **B/A mixed** | MeOH pathway is directly traceable; NH3 pathway decomposition needs a direct FINAL-1.1 source pointer. |
| The AI layer allocates finite scientific compute to downstream decision resolution | DISCOVER V1 cross-tier result plus C1 boundary extension | frozen V1 hashes/scores; C1 run summaries/traces | **A** | Keep, but manuscript §3.7 must be updated to include C1. |
| Atomistic uncertainty may be amplified or attenuated before the industrial decision | qualitative multiscale interpretation | NH3 MC headline values are present; no direct layer-by-layer amplification metric is vendored here | **B** | Use bounded wording unless the underlying sensitivity/propagation output is linked. |

## 2. Results-section audit

### 3.1 NH3 ranking inversion

**Claims checked**

- atomic top-3 = **Ru > Os > Fe**;
- optimized economic top-3 = **Fe > Ru > Os**;
- Fe / Ru / Os reduced catalyst-dependent costs = **15.292 / 22.031 / 25.832 USD/t NH3**;
- Top-3 Spearman rho = **-0.50**;
- Top-3 Kendall tau = **-0.33**;
- full-15 raw Spearman rho = **0.929**.

All values agree between `docs/MANUSCRIPT_SKELETON.md`, `docs/FIGURE_MAP.md`, `docs/RESULTS_AT_A_GLANCE.md`, and `data/canonical_results_2026-09-06.csv`.

**Status: B — consistent, provenance incomplete.** The essay repository contains the compact canonical snapshot but not the current NH3-FINAL-1.1 raw output tree or the generator that produced these values. `data/README.md` explicitly states that the compact snapshots do not replace the frozen computational harness or raw model outputs.

### 3.2 NH3 process reoptimization and uncertainty

Checked values:

- Fe optimum ~ **425 C / 180 bar / 30 C**;
- Ru optimum ~ **450 C / 425 bar / 25 C**;
- Os = **broad shallow high-pressure minimum**;
- Fe feasibility = **79.9%**;
- Fe Top-1 survival = **28.2%**;
- Fe Top-3 actionable = **94.0%**.

These agree across the current manuscript-facing files and `data/canonical_results_2026-09-06.csv`.

**Status: B.** Direct FINAL-1.1 process-state / Monte Carlo provenance is missing from this repository. Historical NH3-FINAL-1.0 workbooks must not be used to fill this gap because they contain superseded values.

### 3.3 Ru backward design and scaling reachability

Checked values:

- Ru activity-only break-even = **201.22x**;
- scaling-consistent headroom = **1.090x at 673 K** and **2.525x maximum** over the process-state library;
- strict-scaling minimum Ru cost = **21.398 USD/t NH3** at **E_N = -1.215 eV**;
- break-even operating point used by the figure map = approximately **425 C / 190 bar / 30 C**.

The first three are present in `data/canonical_results_2026-09-06.csv`; the break-even operating point is present in the manuscript/figure map but is not represented in that compact CSV.

**Status: B / HOLD for F5-F6.** The numerical story is internally consistent, but the direct FINAL-1.1 backward-sweep and scaling-manifold outputs must be linked or imported before these figures are frozen.

### 3.4 CO2-to-MeOH ranking reshuffle

Direct file `data/meoh/meoh_candidate_ranking_D01v3.csv` reproduces the manuscript numbers:

- STY per g Re = **65 / 55 / 18 / 16** for 1%-250 / 1%-200 / 5%-200 / 5%-250;
- NPC at 2% purge = **943.30 / 966.96 / 974.99 / 1258.17 EUR/t** in economic order;
- upstream per-Re winner falls from **#1 to #3**;
- rho = **0.20**, tau = **0.00**, **3/6** pairwise inversions;
- 5%-250 C: X_CO2 = **0.40**, S_CH4 = **0.25**, NPC = **1258.17 EUR/t**;
- local leverage at 5%-250 C = STY **0.0028943**, conversion **0.0588278**, CH4 suppression **0.3757939**.

The purge robustness summary independently records **396** levels from **0.5% to 40%**, maximum rho **0.40**, minimum **2/6** inversions, and all candidate-specific NPC minima at the **0.5%** lower bound.

**Status: A — traceable.** Frozen workbook, extracted CSV, provenance JSON, purge-analysis code and ranking-figure generator are all present.

### 3.5 Cross-reaction leverage

Current headline:

- MeOH CH4-suppression / NH3 TOF normalized leverage ratio = **273-410**;
- midpoint ~ **328**.

The values are present in `data/canonical_results_2026-09-06.csv` and manuscript summaries.

**Status: B / HOLD for F9A.** No dedicated cross-reaction source-data file, calculation script, or provenance record is present in the current data tree. A compact result snapshot alone is insufficient to freeze the final plotted values.

### 3.6 Au/TiO2 rank-preservation control

V1.1 is directly reproduced by `controls/au_tio2_rank_preservation_v1_1.py` and `data/rank_preservation_control_v1_1.csv`:

- activity and catalyst-burden order = **2 > 3 > 4 > 5 > 6 nm**;
- rho = **1.000**;
- tau = **1.000**;
- pairwise inversions = **0**;
- full order preserved in **10,000/10,000** literature-envelope draws;
- 6 nm / 2 nm required-catalyst ratio = **8.064x**.

V1.3 direct summary also reproduces the stated moderate-stress robustness values.

**Status: A — traceable.** The V1.1 SVG can be treated as the canonical visual source. V1.3 remains supporting evidence, not a replacement for V1.1.

### 3.7 Decision-aware computation allocation

The current `MANUSCRIPT_SKELETON.md` reports the frozen DISCOVER V1 cross-model result:

- anonymous full decision = nano **6/35**, mini **15/35**, strong **35/35**;
- pooled tier trend Z = **6.95**;
- original universal E > D Go criterion not met.

These remain valid DISCOVER V1 results. However, the manuscript section is now **stale** because it does not integrate the completed `DISCOVER-BOUNDARY-C1` confirmatory extension.

C1 direct evidence shows:

- fixed-VOI D complete-decision threshold = **206 CU**;
- strong E: **19/20 at 175 CU**, **20/20 at 225 CU**;
- mini E: **0/20 at 175 CU**, **6/20 at 225 CU**;
- nano E: **0/20 at both 175 and 225 CU**;
- narrow-window use at 175 CU: strong **20/20**, mini **4/20**, nano **0/20**;
- at 225 CU, strong E median CU_to_full = **218 CU** versus D = **206 CU**, so the result is not a universal raw-compute saving;
- Phase B: **80/80 formal traces**, **0 smoke**, **0 infrastructure retries**, **0 driver exceptions**, frozen hashes **15/15 PASS** before and after.

**Status: A for evidence; C for manuscript integration.** The correct post-C1 claim is a **model-tier-dependent, budget-localized decision-recovery advantage below the fixed policy's completion threshold**, not universal adaptive superiority or universal compute saving.

## 3. Figure-by-figure lock audit

| Figure | Evidence audit | Asset audit | Lock state | Required action |
|---|---|---|---|---|
| **F1 NH3 atomic vs economic ranking** | Values consistent; current raw FINAL-1.1 run not vendored | No manuscript-ready F1 asset in `figures/` | **HOLD** | Import/link FINAL-1.1 source and regenerate/import F1 with provenance. |
| **F2 rolling Top-K correlation** | rho/tau consistent in canonical snapshot | No F2 asset | **HOLD** | Same NH3 provenance closure + figure source. |
| **F3 NH3 uncertainty** | 79.9 / 28.2 / 94.0 consistent | No F3 asset | **HOLD** | Link/import FINAL-1.1 MC output + figure source. |
| **F4 operating envelopes** | Fe/Ru/Os operating claims consistent | No F4 asset | **HOLD** | Link/import pressure-envelope data + figure source. |
| **F5 Ru backward sweep** | 201.22x consistent | No F5 asset | **HOLD** | Link/import activity-sweep output + generator. |
| **F6 scaling reachability** | 1.090 / 2.525 / 21.398 consistent | No F6 asset | **HOLD** | Link/import scaling-manifold output + generator. |
| **F7 MeOH rank reconstruction** | Direct workbook/CSV/script provenance present | `MeOH_F03_UpstreamToEconomicRanking_D01v3.png` present | **LOCKABLE** | Final visual/QC and, ideally, vector export. |
| **F8 MeOH selectivity-recycle pathway** | Direct candidate and purge data present | MeOH F01/F02 PNG sources present | **LOCKABLE WITH ASSET QC** | Verify which panel(s) constitute manuscript F8 and archive editable/vector source if available. |
| **F9A cross-reaction leverage** | Headline values only in compact snapshot | No dedicated F9A source asset identified | **HOLD** | Add source-data CSV + derivation script/provenance and render final panel. |
| **F9B Au/TiO2 preservation** | Direct CSV + code + literature-calibrated report | `RP1_AuTiO2_rank_preservation_V1_1.svg` present | **LOCKABLE** | Keep V1.1 as canonical; V1.3 only as small robustness annotation/SI. |

The current repository therefore does **not** yet support declaring all nine manuscript figures frozen. The scientific conclusions checked above are not contradicted; the limiting issue is provenance/asset closure, concentrated in NH3 and cross-reaction figures.

## 4. Documentation inconsistencies found

1. `docs/MANUSCRIPT_SKELETON.md` §3.7 and Methods item 13 stop at DISCOVER V1 and must incorporate C1.
2. `docs/RESULTS_AT_A_GLANCE.md` stops at the original DISCOVER V1 result and must add the C1 boundary result.
3. `data/README.md` Agent evidence hierarchy stops at DISCOVER V1 and must add C1 summaries/traces/addenda.
4. `figures/README.md` still labels F1-F9 as image-pending even though MeOH and Au/TiO2 assets are present; its F9 description also predates the current F9A/F9B combined architecture.
5. `figures/README.md` contains a stale N2O negative-control section although no such directory exists in the current figure tree and that line is not part of the frozen manuscript architecture.

These are documentation/provenance issues, not evidence of a scientific-model bug.

## 5. Required provenance closure before final figure freeze

### NH3-FINAL-1.1

Add a repository-level provenance record that points unambiguously to the frozen source for:

- canonical run ID `outputs/nh3_final_20260905T134204Z`;
- exact model/driver commit or immutable file hashes;
- process-state library and pressure-CAPEX output;
- 15-metal ranking table;
- 1,000-draw Monte Carlo output and seed;
- Ru backward activity sweep and parity crossing;
- scaling-manifold reachability output;
- source-data files/scripts used to render F1-F6.

If those raw outputs live in another repository or archive, a content-addressed pointer with hashes is sufficient; they do not have to be duplicated blindly.

### Cross-reaction leverage

Create a dedicated source-data/provenance bundle for the **273 / 328 / 410** normalized-leverage result. It should expose the NH3 and MeOH denominator definitions, the input values used in the normalization, the calculation, and the figure-generating source for F9A.

## 6. Current audit decision

**No scientific recalculation is triggered by this first pass.** I found no numerical contradiction among the current canonical manuscript-facing sources for NH3, MeOH, Au/TiO2 or DISCOVER C1.

The next work is therefore provenance closure and documentation repair, not new model runs:

1. close NH3-FINAL-1.1 raw provenance;
2. close the cross-reaction leverage derivation;
3. update manuscript §3.7 / Methods / Results-at-a-glance to C1;
4. correct `figures/README.md` and remove stale figure metadata;
5. lock F7/F8/F9B first;
6. only then lock F1-F6/F9A once their direct source chains are available.

A new scientific run should be opened only if provenance recovery exposes an actual inconsistency in a canonical value, algorithm or frozen assumption.
