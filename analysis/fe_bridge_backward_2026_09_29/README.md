# Fe bridge, backward-region and inversion-layer audit — 2026-09-29

This audit adds three targeted checks without changing any frozen NH3-FINAL-1.1 model or headline value.

## 1. Fe terrace-to-step bridge

The uploaded Wang-2021/S1 activity workbook contains step-site energetics for 14 metals but no Fe step-site row. The existing model therefore maps the raw S1 Fe terrace descriptor to the step descriptor using the same 14-metal terrace-to-step linear relation used by the activity workbook.

Global 14-metal fit:

- step E_N = 1.15474364 × terrace E_N − 0.17005543 eV
- R² = 0.981813
- Fe terrace E_N = −1.0583 eV
- Fe predicted step E_N = −1.39212062 eV
- residual standard error = 0.22712582 eV
- 14-fold LOO MAE = 0.20317 eV
- 14-fold LOO RMSE = 0.27706 eV
- conservative 95% new-observation prediction interval = [−1.91666, −0.86758] eV

The residual standard error is numerically identical to the frozen `Fe_sigma_eV = 0.2271258177356984` in NH3-FINAL-1.1. The existing descriptor Monte Carlo therefore already propagates the bridge-scale uncertainty through the process/economic decision.

A physically motivated strong-binding sensitivity check uses only the metals with terrace E_N <= −0.5 eV (Mo, Os, Re, Ru, W), i.e. the descriptor branch containing Fe. It is not used to replace the canonical global bridge.

- Fe predicted step E_N = −1.41800696 eV
- LOO RMSE = 0.05295 eV
- 95% prediction interval = [−1.57947, −1.25654] eV

The existing 1D activity volcano gives the strong-binding-side Fe descriptor values at which Fe would match Ru and Os activity as −1.21531 and −1.23222 eV, respectively. The branch-local 95% interval stays on the lower-activity side of both thresholds.

Prediction-interval propagation through the frozen 1D volcano gives:

- global new-observation model: P(Ru > Os > Fe) = 0.873
- strong-binding sensitivity: P(Ru > Os > Fe) = 0.987

Interpretation: keep the Fe bridge validation in Methods/SI rather than the headline narrative. No new DFT is required for this audit.

## 2. Backward design as a lifecycle feasible region

The fully reoptimized Ru metal-price sweep gives the Fe/Ru parity price

- P* = 163.7633 USD kg^-1 Ru

At fixed intrinsic Ru activity, Ru-specific recovery and lifetime enter the metal-replacement cost through the same multiplicative factor as price. Holding Fe at its baseline definition, the parity condition can therefore be reparameterized exactly as

```
P_Ru (1 - r) (10 y / L) <= P*
```

with canonical P_Ru = 53,852.5 USD kg^-1.

Consequences:

- 10 y lifetime -> required recovery = 99.6959%
- 20 y lifetime -> required recovery = 99.3918%
- 99% recovery -> required lifetime = 32.88 y
- 98% recovery -> required lifetime = 65.77 y

The prespecified lifecycle envelope used by the lever audit (5–20 y life; 0.99 as optimistic recovery bound) therefore does not reach Fe parity at the current Ru activity. This adds a genuine two-property feasible region to the backward-design result without rerunning DFT.

### Joint direct-activity/lifecycle target region

Allowing activity and lifecycle variables to move together changes the **required backward target**, but target determination and physical reachability must remain separate. The audit reuses the 53 distinct process states that already appear in the fully reoptimized Ru metal-price sweep. For each frozen state, a direct, state-independent Ru activity multiplier rescales required bed volume as V(alpha)=V(1)/alpha; lifetime and recovery map exactly to the effective Ru metal price; and the reactor-volume and vessel-pressure terms are recomputed from the frozen FINAL-1.1 cost correlations.

Because this search minimizes over only a subset of the full 14,136-state library, it gives a conservative upper bound on the direct activity multiplier required for parity. The subset reproduces both independent one-dimensional parity anchors:

- alpha = 1 -> effective Ru parity price = **163.7633 USD kg^-1**;
- alpha = 201.223 -> parity returns to the canonical Ru price **53,852.5 USD kg^-1**.

Representative backward targets are:

- **10 y life + 99% recovery:** direct activity multiplier <= **2.41794x**;
- **15 y life + 99% recovery:** <= **1.74213x**;
- **20 y life + 99% recovery:** <= **1.40129x**;
- **20 y life + 98% recovery:** <= **2.41794x**.

These results are the useful P1 extension: the original 201.22x single-property target collapses into a much smaller **activity-lifetime-recovery target region** once lifecycle properties are allowed to improve simultaneously.

### Exact strict-scaling × lifecycle reachability closure

The physical-reachability test is now closed without new DFT. The strict-scaling calculation was evaluated over all **14,136** FINAL-1.1 process states using the same Wang/S1-derived kinetic model and the canonical **0.005 eV** descriptor grid. The canonical regression gate is reproduced exactly: the activity-only strict-scaling minimum remains **21.397873 USD t^-1 NH3 at E_N = -1.215 eV**.

A useful reduction makes the joint sweep exact and inexpensive. At a fixed process state, changing E_N changes cost only through TOF -> required active metal -> catalyst-bed volume. Metal replacement cost, the reactor-volume term and the vessel-pressure term all increase monotonically with required active metal / volume, while the process-state compression and refrigeration terms are independent of E_N. Therefore, for every process state and every lifetime/recovery choice, the cost-minimizing E_N is simply that state's TOF-maximizing E_N on the strict-scaling grid. The audit first finds that statewise descriptor optimum and then takes the lower cost envelope over all 14,136 states.

The resulting lifecycle variable is

```
q = (1 - recovery) / catalyst_lifetime
```

and the strict-scaling parity boundary is

- q* = **4.40683454e-4 y^-1**;
- equivalent Ru effective price at the 10-year basis = **237.319 USD kg^-1**;
- parity occurs at **E_N = -1.230 eV**, **425 C / 190 bar / 30 C**, with a **4.298 m3** bed.

Within the prespecified lifecycle envelope (**life <= 20 y; recovery <= 0.99**), the best corner is 20 y + 99% recovery. Its strict-scaling optimum is **15.36249 USD t^-1 NH3**, still **0.07078 USD t^-1** above Fe (**0.46%**). Thus the tested lifecycle box **does not intersect** the strict E_N scaling manifold.

The boundary lies only slightly outside that box:

- **20 y lifetime -> 99.1186% recovery** is required for parity;
- **99% recovery -> 22.69 y lifetime** is required;
- **10 y -> 99.5593% recovery**;
- **15 y -> 99.3390% recovery**.

This is the key P1 result. The direct backward target region moves very close to physical reachability when lifecycle properties improve simultaneously, but under the prespecified 5–20 y / <=99% recovery envelope the strict-scaling manifold still misses Fe parity. The conclusion is therefore neither "activity can never work" nor "the combined target is reachable": **activity alone is far outside reach; joint lifecycle improvement nearly closes the gap, but the tested material-property envelope remains just short of the industrial target.**

Machine-readable outputs are `scaling_lifecycle_exact_summary.json`, `scaling_lifecycle_exact_keypoints.csv` and `scaling_lifecycle_exact_global_boundary.csv`. The fast reproducible calculation is `run_statewise_strict_scaling_lifecycle.py`; `run_exact_scaling_lifecycle_surface.py` is retained as the brute-force cached-response implementation of the same scientific test.

## 3. First layer at which the NH3 ranking inverts

The causal localization is now supported by two complementary tests.

First, a **common-reference layer diagnostic** keeps the 673 K atomistic activity condition fixed and converts activity into the same plant-throughput active-metal normalization used by the FINAL-1.1 cost model. The activity order and catalyst-demand order agree:

```
activity                         Ru > Os > Fe
required active-metal burden     Ru < Os < Fe   (lower is better)
```

The normalized active-metal demands are **2,161.5 kg Ru, 4,503.5 kg Os and 86,279 kg Fe**. Thus the catalyst-demand layer itself does not invert the activity ranking.

The first explicit flip appears when this demand is monetized using the canonical metal prices and the frozen 10-y catalyst lifetime, before adding any reactor, compression, refrigeration or equipment term:

```
annualized replacement cost:
Fe 0.199 < Ru 33.570 < Os 185.270 USD/t NH3
```

Second, the independent **equal-price full-process ablation** removes the Ru-Fe price disparity and reoptimizes all 14,136 process states. Ru then remains less costly than Fe (**14.712 vs 15.292 USD/t**). Therefore process reoptimization by itself is not sufficient to produce the Fe-over-Ru order.

Together these checks identify the trigger more tightly:

```
intrinsic activity
    -> catalyst demand                      (order preserved)
    -> actual-price lifecycle monetization  (FIRST FLIP)
    -> process reoptimization               (gap amplified)
```

The canonical Ru - Fe gap is then widened mainly by fresh compression (**+4.632 USD/t**), compressor CAPEX (**+1.181**) and refrigeration (**+0.629**) on top of the metal-inventory contribution (**+1.763**), while vessel pressure, recycle compression and reactor-base terms partly offset the difference.

The common-reference diagnostic is intentionally a **layer-localization calculation**, not a replacement for the final process model. Its role is to show that the order change exists before downstream process costs are introduced; the equal-price full-process calculation independently confirms the causal role of metal-price-weighted inventory.

## Source hierarchy

No new source of truth is introduced. Current manuscript numbers remain pinned to:

- `data/manuscript_headline_results_2026-09-20.csv`
- `data/claim_evidence_registry_2026-09-10.csv`
- frozen NH3-FINAL-1.1 provenance under `provenance/nh3_final_1_1/`

This directory is an audit/derived-analysis layer only.


## Reproducibility gate

GitHub Actions workflow `.github/workflows/backward-joint-region-audit.yml` recomputes the direct-alpha boundary, representative target keypoints and conditional diagnostic JSON from the pinned Ru price-sweep states. Run **36516350623** passed on 2026-09-29 after the target/reachability separation and byte-stable output fix.

This CI gate validates the **backward target calculation**. The strict-scaling × lifecycle closure is now recorded separately in `scaling_lifecycle_exact_summary.json` and reproduced by `run_statewise_strict_scaling_lifecycle.py`, which uses all 14,136 FINAL-1.1 process states and the canonical 0.005-eV scaling grid without new DFT. The brute-force cached-response script is retained as an independent implementation for cross-checking.

