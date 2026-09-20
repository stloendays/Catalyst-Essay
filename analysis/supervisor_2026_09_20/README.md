# Supervisor-requested analyses — 2026-09-20

This directory contains the targeted analyses requested after the 2026-09-20 supervisor review. Existing NH3-FINAL-1.1, MEOH-D01-v3 and DISCOVER-BOUNDARY-C1 provenance is preserved; these files record the new counterfactual, uncertainty and oracle calculations.

## 1. NH3 Ru-price equalization

The frozen NH3-FINAL-1.1 baseline was reproduced before the counterfactual:

- Fe = **15.291705 USD/t NH3**, 425 C / 180 bar / Tsep 30 C.
- Ru = **22.030595 USD/t NH3**, 450 C / 425 bar / Tsep 25 C.
- reproduction error against the frozen result: < 1.5e-14 USD/t for both metals; optimum states match exactly.

Counterfactual: set the Ru metal price from 53,852.5 USD/kg to the Fe value, **8 USD/kg**, with every other parameter unchanged, and reoptimize Ru over the full **14,136-state** process library.

Result:

- Ru = **14.712130 USD/t NH3**
- optimum = **425 C / 170 bar / Tsep 30 C**
- Ru - Fe = **-0.579575 USD/t NH3**

Therefore the baseline Fe-over-Ru inversion **does not survive metal-price equalization**. The manuscript must not retain the claim that the inversion is independent of the direct Ru price premium. The counterfactual also shows a process-mediated response: once Ru is cheap, its optimum shifts from 425 bar to 170 bar, so the effect of metal price is amplified through reoptimization rather than being only the direct metal-inventory line item.

Files: `nh3_ru_price_equalization.json`, `nh3_cost_decomposition.csv`, `nh3_cost_decomposition.svg`.

## 2. Where the canonical 6.739 USD/t gap comes from

Canonical Ru - Fe = **+6.738890 USD/t NH3**.

Largest positive contributions:

- fresh-feed compression electricity: **+4.631668**
- metal inventory: **+1.763013**
- compressor CAPEX: **+1.180730**
- refrigeration: **+0.629119**

Offsets:

- vessel pressure premium: **-0.733129**
- recycle compression electricity: **-0.646840**
- reactor-volume base: **-0.085671**

The line-item decomposition alone does not establish causality because equalizing the metal price changes the Ru optimum. The full reoptimized counterfactual above is the causal diagnostic.

## 3. Fig. 3 metric reconciliation

The teacher's “Fe about 68% first” and the repository's 28.2% refer to different metrics.

From the frozen 1,000-draw NH3 descriptor Monte Carlo:

- Fe is the **economic winner in 681/1000 draws = 68.1%**.
- Ru is the economic winner in 319/1000.
- `top1_survival = 28.2%` means **atomic Top-1 equals economic Top-1**; it is not P(Fe is economic Top-1).

Use **68.1%** when discussing Fe's Top-1 economic probability under descriptor uncertainty.

## 4. Joint NH3 cost-parameter Monte Carlo

The protocol was frozen before outcomes in `docs/SUPERVISOR_COST_MC_PREREG_2026-09-20.md`.

Primary settings:

- N = **5,000**, seed = **20260920**
- Fe and Ru metal-price multipliers independently log-uniform over [0.5, 2.0]
- shared CAPEX multiplier uniform over [0.8, 1.2]
- shared electricity price uniform over [20, 100] USD/MWh
- shared catalyst lifetime uniform over [5, 20] y
- full per-draw Fe/Ru process reoptimization
- alpha* recomputed against each draw's reoptimized Fe target

Full 14,136-state direct-cost verification:

- **P(C_Fe < C_Ru) = 5000/5000 = 1.000**
- minimum observed Ru - Fe margin = **2.382 USD/t NH3**
- no draw has Ru <= Fe at alpha = 1

alpha* distribution:

- p05 = **70.78x**
- median = **174.27x**
- p95 = **462.00x**
- mean = **205.81x**

Thus the cost-side uncertainty tested here broadens the activity parity requirement substantially but does not change the Fe-over-Ru decision inside the preregistered parameter envelope.

File: `nh3_cost_mc_summary.json`; `cost_mc_summary.svg` visualizes alpha* and the MeOH rank matrix.

## 5. MeOH four-candidate rank probability

MEOH-D01-v3 excludes Re purchase/replacement from its canonical NPC boundary. Therefore two matrices are reported rather than silently changing the model.

### Canonical D01 boundary

CAPEX and electricity are propagated through the candidate-specific equipment and compression terms. Metal-price and lifetime draws are sampled but are structurally inactive because catalyst purchase/replacement is absent from D01.

All **5,000/5,000** draws retain:

**5 wt% Re / 200 C > 1 wt% Re / 200 C > 1 wt% Re / 250 C > 5 wt% Re / 250 C**.

### Explicit active-Re replacement extension

A separately labelled extension adds only active-Re replacement using the D01 STY-derived Re inventory. It uses the frozen project Re price 5,757.64 USD/kg, converted to 5,012.6 EUR/kg at USD/EUR = 0.8706 on 2026-09-20; lifetime and price multipliers follow the same joint-MC priors.

The ranking remains identical in **5,000/5,000** draws.

This extension does **not** replace the canonical D01 model.

Sources for the D01 economic anchor: https://doi.org/10.3390/pr10081535 and the frozen repository D01 workbook/provenance.

File: `meoh_rank_probability_matrix.csv`.

## 6. Agent oracle minimum CU

Two lower bounds are retained to avoid an artificially favourable scorer-only comparison.

### Scored full-decision oracle: 7 CU

Shortest legal chain that makes the frozen scorer's full decision correct (winner + decision pair + reachability), allowing the oracle to select only decision-relevant candidates.

### Protocol-complete S1-S3 oracle: 22 CU

This additionally requires the environment's scientific stopping criteria:

- nonempty 3-state decision window: 1 CU
- activity for all 15 candidates: 15 CU
- process optimization of the minimum unresolved set Fe/Ru/Os: 3 CU
- BACKWARD: 1 CU
- reference reachability: 2 CU
- total = **22 CU**

The same 3-state window reproduces the canonical Fe cost and alpha* = 201.223442987840x, relative error 2.88e-13.

Use the **22-CU protocol-complete oracle** as the manuscript-facing normalization:

- 75-CU strong allowance = **3.41x oracle**
- 75-CU cell median decision-stable spend 52.5 CU = **2.39x oracle**
- fixed-policy completion threshold 206 CU = **9.36x oracle**
- non-binding median decision-stable spend 566 CU = **25.73x oracle**

The separate 7-CU value should remain labelled as the scorer-theoretic floor.

File: `agent_oracle_min_cu.json`.

## Manuscript consequence

The central NH3 mechanism sentence changes. The supported statement is now:

> The Fe-Ru economic inversion is generated by the coupling of metal cost with process reoptimization. Equalizing the Ru and Fe metal prices reverses the economic order, while the preregistered joint cost-parameter Monte Carlo leaves Fe lower-cost in all 5,000 sampled draws around the canonical price regime.

This keeps the process pathway mechanistically explicit without claiming that process penalties are sufficient to overcome an equalized Ru price.
