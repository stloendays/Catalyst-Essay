# Current project status

Snapshot date: **2026-09-07**

## Canonical scientific model

- Canonical ammonia version: **NH3-FINAL-1.1**
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
- Strict scaling lowest Ru cost: **21.398 USD/t NH3 at E_N = -1.215 eV**

## Current mechanistic interpretation

NH3-FINAL-1.1 removes the earlier 300-bar boundary artefact by extending the pressure grid to 10-1000 bar and adding pressure-dependent equipment CAPEX. The headline inversion and reachability conclusions survive, while the numerical cost gap narrows.

Fe now avoids a large-vessel penalty by moving to a smaller bed and an optimized point near **425 C / 180 bar / 30 C separator temperature**. Ru moves to an interior optimum near **450 C / 425 bar / 25 C**, while Os shows a broad shallow high-pressure minimum rather than a meaningful single operating point.

## Levers on the current canonical model

Current 1.1 reach values:

- Metal recovery: **0.69**
- Catalyst lifetime: **0.16**
- Electricity: **0.12 at 20 USD/MWh**, treated as weakly discriminatory / absolute-only
- Pressure upper bound: no longer a valid lever because Ru and Os are interior to the grid
- Bed-cap increase: inactive under the current Fe optimum

Current ordering: **recovery >> lifetime >> other tested levers**.

## DISCOVER benchmark status

The closed-book DISCOVER environment is frozen around 11 fine-grained actions:

1. INSPECT_CANDIDATES
2. COMPUTE_ACTIVITY
3. READ_PROPERTY_UNCERTAINTY
4. BUILD_PROCESS_WINDOW
5. OPTIMIZE_PROCESS
6. READ_COST_BREAKDOWN
7. RUN_MC
8. TEST_LEVER
9. BACKWARD
10. TEST_REACHABILITY
11. CHECK_MODEL_VALIDITY

The cost model defines **1 CU = 1000 MKM state solves**. The formal single-model benchmark contains anonymous and named variants and uses a frozen scorer.

Latest recorded formal run:

- 70 policy-E runs = 5 seeds x 7 budgets x anonymous/named
- 392 traces including frozen A-D baselines
- 0 infrastructure retries
- 0 action errors
- anonymous variant: complete correct decision 35/35, including 200 CU
- exact break-even recovered 34/35
- policy E and fixed-VOI D are effectively tied from 250-500 CU

## DISCOVER cross-model stability (completed 2026-09-06, statistics 2026-09-07)

- Tiers: gpt-5.4-nano-2026-03-17 (weak), gpt-5.4-mini-2026-03-17 (medium), gpt-5.5-2026-04-23 (strong; V1 traces reused).
- 140 new policy-E traces (70 per new model), all present and scored; frozen hashes PASS before and after; 0 retries, 0 driver exceptions.
- Anonymous pooled P(full decision): **6/35 / 15/35 / 35/35**; tier trend Z = 6.95.
- Weak-tier failure is the reachability step (P(reach) = P(full)); winner accuracy is not tier-discriminating (nano vs mini p = 0.73).
- Unnecessary-CU fraction 0.46 / 0.30 / 0.19; tool-interface errors 2.1 / 2.2 / 0 per run.
- Pre-registered agent-specific Go (E beats D, ≥ 4/5 runs, ≥ 2 tiers): **not met** — recorded as a negative result.
- Reports: `docs/CROSS_MODEL_DISCOVER_V1.md`, `docs/CROSS_MODEL_STATS_V1.md`; figures `figures/discover_cross_model/`.

## Next validation layer

The project plan currently points to:

1. a negative-reaction control where atomic ranking should largely survive economic propagation (not started);
2. continued manuscript integration using NH3-FINAL-1.1 only;
3. any protocol change (scorer weighting of unresolved risk, tool-argument schema hardening) is DISCOVER V2 and must not overwrite V1.

Historical NH3-FINAL-1.0 values such as Fe/Ru/Os = 10.199/17.592/21.321 USD/t, Fe feasibility = 73.6%, and Ru break-even = 2171.56x should not be used as current headline numbers.
