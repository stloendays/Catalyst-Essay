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

### Joint activity-lifecycle region: certified non-DFT inner approximation

Allowing activity and lifecycle properties to improve together changes the reachability conclusion. To avoid assuming that the two levers are separable after process optimization, the audit reuses the 53 distinct process states that already appear in the fully reoptimized Ru metal-price sweep. For each frozen state, a direct Ru activity multiplier rescales required bed volume exactly as V(alpha)=V(1)/alpha; lifetime and recovery map exactly to the effective Ru metal price; and the reactor-volume and vessel-pressure terms are recomputed from the frozen FINAL-1.1 cost correlations. Minimizing over this state subset gives an upper bound on the true fully reoptimized Ru cost. Therefore every point classified as feasible by this audit is guaranteed feasible in the full 14,136-state model; the method can only miss additional feasible points.

The subset reproduces both independent parity anchors to numerical tolerance:

- alpha = 1: effective Ru parity price = **163.7633 USD kg^-1**;
- alpha = 201.223: parity returns to the canonical Ru price **53,852.5 USD kg^-1**.

At the maximum scaling-consistent activity gain already present in the frozen model, alpha = **2.524565**, the certified effective-price parity boundary rises to **566.964 USD kg^-1**. This implies a recovery requirement of **98.947% at 10 y**, **98.421% at 15 y**, and **97.894% at 20 y**.

Most importantly, the explicit joint point alpha = **2.524565x**, catalyst lifetime = **20 y**, Ru recovery = **98.0%**, effective Ru price = **538.525 USD kg^-1** is already feasible without any new process state: the existing **425 C / 185 bar / 30 C** state gives **15.2571 USD t^-1 NH3**, **0.0346 USD t^-1 below Fe**. Because this is a direct feasible-state evaluation, full reoptimization can only preserve or improve that result.

This refines the backward-design conclusion: **activity alone is unreachable, and lifecycle improvement alone misses parity inside the prespecified range, but the combined activity-lifetime-recovery design region does intersect parity near the upper edge of the existing property envelope.** The reproducible audit is implemented in build_certified_inner_surface.py; run_exact_joint_surface.py is prepared for the original harness machine to map the complete 14,136-state boundary without new DFT.

## 3. First layer at which the NH3 ranking inverts

The intermediate order localizes the causal trigger:

1. **Atomic/MKM activity:** Ru > Os > Fe.
2. **Catalyst demand:** Ru > Os > Fe remains preserved; minimum bed burden still favors Ru/Os over Fe.
3. **Full process with Ru price set equal to Fe:** Ru = 14.712 USD t^-1, Fe = 15.292 USD t^-1. Fe still does not win after full reoptimization.
4. **Catalyst inventory monetized at canonical metal prices:** Fe < Ru < Os. This is the first explicit top-three flip.
5. **Full canonical process and economics:** Fe < Ru < Os; reoptimization amplifies the initial flip.

Thus the causal trigger is the **catalyst-inventory -> lifecycle-economics interface**, where required inventory is weighted by the actual metal-price disparity. The high Ru price then changes the preferred operating regime, and fresh compression, compressor CAPEX and refrigeration widen the final Ru–Fe gap.

Canonical Ru − Fe cost-gap contributions (USD t^-1 NH3):

- metal inventory +1.763013
- fresh-feed compression +4.631668
- compressor CAPEX +1.180730
- refrigeration +0.629119
- reactor base −0.085671
- vessel pressure premium −0.733129
- recycle compression −0.646840
- total +6.738890

## Source hierarchy

No new source of truth is introduced. Current manuscript numbers remain pinned to:

- `data/manuscript_headline_results_2026-09-20.csv`
- `data/claim_evidence_registry_2026-09-10.csv`
- frozen NH3-FINAL-1.1 provenance under `provenance/nh3_final_1_1/`

This directory is an audit/derived-analysis layer only.


## Reproducibility gate

GitHub Actions workflow `.github/workflows/backward-joint-region-audit.yml` recomputes the certified inner-region CSV/JSON from the pinned price-sweep states and fails if the committed outputs drift.
