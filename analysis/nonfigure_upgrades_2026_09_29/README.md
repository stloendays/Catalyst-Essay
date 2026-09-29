# Non-figure scientific upgrades — 2026-09-29

This directory closes four manuscript issues without changing any frozen scientific source or main-figure layout.

## 1. Decision regret

Rank correlation says whether orders differ; **decision regret** says what the wrong screening choice costs.

Define, within each reaction-specific downstream objective,

```
R = (J_upstream-winner - J_downstream-winner) / J_downstream-winner
```

where lower downstream objective is better.

Canonical values:

- NH3: choosing Ru from intrinsic activity instead of Fe from catalyst-dependent economics gives **R = 44.07%**.
  Under the preregistered 5,000-draw cost-side Monte Carlo, **R stays positive in 5,000/5,000 draws** and its p05 / median / p95 are **30.48% / 40.89% / 54.25%**. The original Fe/Ru cost-gap and cost quantiles are reproduced exactly by `reproduce_nh3_cost_mc.py`.
- MeOH: choosing 1 wt% Re / 250 C from STY per g Re instead of 5 wt% Re / 200 C from NPC gives **R = 3.36%**.
- Au/TiO2: the upstream and downstream winners coincide, so **R = 0**.

These dimensionless regrets are comparable as *decision consequences* but do not make absolute NH3 and MeOH costs comparable.

A complementary pairwise transfer index is defined as `chi_AB = ln(J_A/J_B) / ln(s_A/s_B)` for a higher-is-better upstream metric `s` and lower-is-better downstream objective `J`. For `s_A > s_B`, **chi < 0** preserves the upstream direction and **chi > 0** identifies a pairwise inversion. Canonical values are **+0.0853** for Ru vs Fe in NH3, **+0.0257** for the MeOH STY winner vs NPC winner, and approximately **-1.00** for 2 nm vs 6 nm Au/TiO2. The magnitude is not promoted as universal across reactions; the sign is the transferable diagnostic.

## 2. Correlated descriptor-error sensitivity

The frozen NH3 descriptor MC uses Fe normal uncertainty and uniform ±0.15 eV uncertainty for the other metals, sampled independently. A supporting Gaussian-copula sensitivity preserves those marginals while varying a positive latent pairwise correlation.

At rho=0, the 100,000-draw audit reproduces the frozen atomistic-winner frequencies closely (audit: Ru 45.98%, Os 43.32%, Fe 10.71%; frozen 1,000 draws: 46.5%, 42.3%, 11.2%). At rho=0.9, the corresponding values become 39.72%, 38.61%, and 21.68%; the exact Ru > Os > Fe order occurs in 36.29% of draws versus 40.40% at rho=0.

This is **not** promoted as a new downstream probability. It shows that the independent descriptor-error model is a modeling choice, and that correlation does not necessarily cancel on a nonlinear volcano.

A separate common additive descriptor-bias sweep gives the same message more directly. The canonical top-three order is preserved only approximately over

```
-0.0573 eV < common delta E_N < +0.1030 eV.
```

A negative common shift first swaps Ru and Os; a positive shift of about +0.11 eV lets Fe overtake Ru. Common-mode energetic bias can therefore change ordering because it moves all candidates relative to the volcano peak.

## 3. Validation and model-form scope

See `MODEL_VALIDATION_MATRIX.md`. The key distinction is:

- external literature supports the **descriptor/volcano structure**, Wang/S1 reference conditions, and the plausibility of Fe operation near 425 C / 180 bar;
- internal audits support the **decision sign** against pressure-CAPEX perturbations;
- the NH3 numerical cost values remain a **reduced catalyst-dependent economic objective**, not a total ammonia production cost.

## 4. Agent stopping efficiency

The 20 non-binding 5000-CU strong-model runs all eventually self-stop, but the retrospective stable-decision audit shows:

- median decision-stable spend = **566 CU**;
- median final spend = **714 CU**;
- median post-stability overrun = **148 CU**;
- **14/20** runs spend additional CU after hindsight stability;
- across all 20 runs, **8207 / 17535 = 46.8%** of final compute occurs after the point from which the full decision remains correct to the end.

This does **not** mean 46.8% is automatically recoverable online: `decision_stable_CU` is a hindsight definition. The manuscript should use it as evidence that the present policy lacks a reliable *operational* stopping detector under non-binding budgets. A future protocol can enforce an environment-level S1–S3 completion guard, but that would be a new policy and must not be retrofitted into the frozen benchmark.

## Scientific consequence

The strengthened narrative is:

1. global rank correlation is supplemented by **decision regret**;
2. uncertainty reporting distinguishes marginal uncertainty from **error dependence/model bias**;
3. model credibility is separated into external trend validation, industrial plausibility and internal robustness;
4. Agent results distinguish **decision stabilization** from **self-stopping efficiency**.
