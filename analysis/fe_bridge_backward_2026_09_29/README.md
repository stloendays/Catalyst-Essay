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

### Reachability caution

The target region above is **not yet evidence that the same property combinations are physically reachable along the strict E_N scaling manifold**. The published 2.524565x value is the maximum scaling-derived activity gain found at any one process state. Because the scaling-derived gain is process-state dependent, that maximum cannot be treated as a uniform activity multiplier and applied to a different cost-optimal state.

Accordingly, the earlier conditional calculation at direct alpha = 2.524565 is retained only as a diagnostic cost-space comparison and is not promoted as a manuscript reachability claim.

The correct next test is an exact strict-scaling x lifecycle sweep:

1. vary Ru E_N along the frozen scaling grid;
2. obtain the state-resolved logTOF vector from the existing cached response surface;
3. apply lifecycle economics through P_eff = P_Ru (1-r) (10 y/L);
4. fully reoptimize all 14,136 process states;
5. test whether any point with L <= 20 y and r <= 0.99 reaches C_Ru <= C_Fe.

`run_exact_scaling_lifecycle_surface.py` now implements this test for the original frozen harness machine. It explicitly refuses to rebuild the response cache and performs no new DFT. The baseline regression gate requires it to reproduce the canonical strict-scaling minimum **21.397873 USD/t at E_N = -1.215 eV** before any joint reachability result is accepted.

The direct-target audit remains reproducible through `build_certified_inner_surface.py`, and `run_exact_joint_surface.py` is retained as the full-state direct-alpha counterpart.

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
