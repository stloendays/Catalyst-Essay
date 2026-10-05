# Methanol recycle–economics model for arbitrary catalysts, applied to the 21 Re/TiO₂ entries of Gothe et al. 2025 Table 4

Date: 2026-10-05. Model: `data/meoh/meoh_general_model.py`. Scripts: `validate_general_model.py` and
`run_table4_candidates.py` in this folder. Interpreter: `D:\Research\CatalystForge\.venv\Scripts\python.exe`.

```
python analysis/meoh_general_model_2026_10_05/validate_general_model.py   # gates + reference loop + 4 Re states
python analysis/meoh_general_model_2026_10_05/run_table4_candidates.py    # 21 Table 4 entries
```

## 1. Method

The model imports every constant, the process anchor (Processes 2022, 10, 1535) and the cost structure from the
canonical engine `data/meoh/meoh_d01_model.py`. That includes the recycle-flow calibration, the equipment split
and exponents, the H₂/CO₂/electricity prices, the 145 t/h plant and the NPC equation. Nothing there is re-fitted.
The model generalizes the catalyst and operating inputs and the treatment of CO.

**Catalyst inputs.** Each catalyst is described by:

- single-pass CO₂ conversion X;
- carbon selectivities S_MeOH, S_CO and S_CH₄, which must sum to 1;
- reaction temperature T and pressure P;
- reactor-inlet H₂/CO₂ ratio. The lab feed is the reactor inlet, as in the canonical model;
- productivity, either as STY per g metal plus metal wt% or as STY per g catalyst. Catalyst mass = production / STY;
- optionally, catalyst price (EUR/kg) and lifetime (y). These add a replacement term, catalyst mass × price / lifetime, to direct OPEX. The term is off by default, so the canonical objective is unchanged.

**Compression.** Fresh CO₂ is compressed from 1 bar, fresh H₂ from 30 bar and the recycle from P − 1.5 bar, all up
to the stated P. The engine's isothermal-equivalent formula and η = 0.80 apply. An entry with P below the 30 bar H₂
delivery pressure has zero H₂ compression work.

**Loop balance with CO recycle.** All flows are per mol of net methanol, with purge fraction p. The unknown is the
reactor-inlet CO₂ flow a. In one pass:

- CO₂ gives MeOH (X S_MeOH a), CO (X S_CO a) and CH₄ (X S_CH₄ a);
- recycled CO is converted with per-pass fraction x_CO by the net reaction CO + 2 H₂ → CH₃OH.

At steady state the reactor-inlet CO is co_in = (1−p) X S_CO a / (p + x_CO(1−p)). The net-methanol condition,
a [X S_MeOH + x_CO (1−p) X S_CO / (p + x_CO(1−p))] = 1, is linear in a, so the balance is solved exactly. The rest
of the loop follows from these flows:

- H₂ demand: 3 per MeOH from CO₂, 4 per CH₄, 1 per CO formed and 2 per MeOH from CO;
- water: 1 per MeOH from CO₂, 2 per CH₄, 1 per CO formed and 0 per MeOH from CO;
- CH₄ and the N₂ carried in with the H₂ impurity accumulate and leave only through the purge.

The water-gas-shift route, CO + H₂O → CO₂ + H₂ followed by CO₂ + 3 H₂ → CH₃OH + H₂O, has the same net
stoichiometry. H₂ demand and water make therefore do not depend on which route the catalyst uses. C, H and O close
to < 1e-13 mol per mol MeOH in 2,000 random states. With x_CO = 0 the balance is the canonical one (§2.1).

**x_CO rule.** The x_CO limits are set by the reactor-outlet thermodynamics at the stated T and P. The equilibrium
constants are the anchor's own (Table 1 of Processes 2022: K_CO₂-hyd, K_RWGS, with K_CO-hyd = K_CO₂-hyd / K_RWGS).
Fugacities come from Peng–Robinson with k_ij = 0 and the effective H₂ acentric factor −0.05 used by the anchor.
These thermodynamics give an equilibrium CO₂ conversion of 30.7% for the anchor's published reactor feed at 70 bar
and 247.5 °C; the anchor reports 30.4%. Ideal-gas activities would give 28.0%.

| Treatment | x_CO | Meaning |
|---|---|---|
| inert | 0 | Canonical treatment. CO leaves only with the purge. This is the lower limit: a catalyst with no WGS or CO-hydrogenation activity. |
| **recycled, central** | **x_RWGS** | The smallest per-pass CO conversion that keeps the reactor outlet at or below reverse-water-gas-shift equilibrium (Q_RWGS ≤ K_RWGS). It is 0 when the inert loop already satisfies this. |
| recycled, high | max(x_RWGS, x_MeOH) | x_MeOH is the largest conversion that CO + 2 H₂ ⇌ CH₃OH equilibrium allows at the outlet, capped at 1. This is the thermodynamic upper limit. |
| recycled, equal-X (sensitivity) | X clipped into [x_RWGS, high] | Recycled CO is converted by the same fraction per pass as CO₂. |

The central rule is taken from the anchor loop itself, for three reasons:

1. The anchor's kinetic model forms and consumes CO only through (R)WGS (Processes 2022, Eqs. 8–9).
2. The anchor's published reactor outlet sits at RWGS equilibrium: Q/K = 1.02. The outlet composition was reconstructed from the Figure 6 feed and the outlet CO (1.76%), N₂ (5.65%), MeOH (7.4%) and H₂O (7.2%).
3. Applied to the anchor inputs, the rule reproduces the anchor's loop CO level (§2.2).

The inert treatment, by contrast, leaves the outlet beyond RWGS equilibrium whenever CO formed per pass accumulates.
This happens for the anchor (Q/K = 1.12), for the three canonical Re states with S_CO > 0 (Q/K = 1.35–4.66) and
for T4-19 and T4-21 (Q/K = 2.7 and 5.8).

## 2. Validation (`validation_summary.json`)

### 2.1 Canonical reproduction (x_CO = 0, 100 bar, H₂/CO₂ = 4, STY per g Re)

Inputs: the four Re/TiO₂ states of workbook sheet `Candidate_Inputs` (Table 3 inputs).

| Gate | Max abs. deviation |
|---|---:|
| NPC vs workbook `Explicit_Loop_2pct` (stored) | 3.9e-13 EUR/t |
| stored columns Y–AG (compression, catalyst t, EC, sep. EC, FCI, ACC, direct, indirect, NPC) | 4.5e-13 |
| all economics vs engine `meoh_d01_model.candidate_economics` | 2.9e-11 |
| NPC vs `meoh_candidate_ranking_D01v3.csv` after its 2-dp rounding | 0 (943.30 / 961.51 / 966.96 / 1258.17) |
| economic ranks vs ranking file | identical |
| purge sweep, 4 × 396 points, NPC vs workbook `Purge_Sweep` | 4.5e-13 EUR/t |
| purge sweep, all 7 stored columns | ≤ 8.7e-11 (recycle kmol/h) |
| purge sweep vs `meoh_purge_robustness_D01v3.csv` (2 dp), economic orders, inversions, Spearman | 0; all identical |
| loop balance with x_CO = 0 vs engine, 2,000 random states | 5.7e-14 |

All gates pass. The script exits non-zero if any gate fails.

### 2.2 Reference loop (Processes 2022: X 0.285, S_MeOH 0.995, S_CO 0.005, H₂/CO₂ 3, 70 bar, 2% purge, 247.5 °C)

| Treatment | x_CO | NPC (MEUR/y) | NPC (EUR/t) | Recycle (kmol/h) | CO in / out (mol%) | Net CO sel. per pass | RWGS Q/K at outlet |
|---|---:|---:|---:|---:|---|---:|---:|
| inert | 0 | 1071.683 | 923.86 | 54,290 | 1.63 / 1.91 | 0.50% | 1.12 |
| **recycled, central** | 0.00246 | **1071.428** | **923.64** | **54,125** | **1.45 / 1.71** | 0.45% | 1.00 |
| recycled, high = equal-X | 0.00587 | 1071.154 | 923.41 | 53,947 | 1.27 / 1.49 | 0.39% | 0.87 |
| x_CO = X = 0.285, unclipped | 0.285 | 1069.479 | 921.96 | 52,865 | 0.11 / 0.13 | 0.03% | 0.07 |
| published | – | 1071.8 | 920 | 54,290 | 1.50 / 1.76 | 0.5% | 1.02 |

- Moving from inert to recycled-central lowers the reference NPC by 0.26 MEUR/y (−0.024%, −0.22 EUR/t) and the recycle by 165 kmol/h (−0.30%). The anchor calibration is kept as the engine defines it. The reference plant itself moves by only 0.22 EUR/t under the central treatment.
- The central treatment matches the published reactor CO within 0.05 mol% at both inlet and outlet. The inert treatment overshoots by 0.13–0.15 mol%. Both treatments carry the anchor's 0.5% as a loop-level selectivity, i.e. the net CO make at the loop's own CO level.
- Recycling CO at x_CO = X would treat the anchor's 0.5% as a gross, CO-free-feed selectivity. That drives the loop CO down to 0.1%, 14 times below the published value. The anchor's CO selectivity is therefore a loop value. Lab selectivities, measured with CO-free feed, are the gross values that the recycled treatment converts into loop behaviour.
- Other anchor checks under the central treatment:
  - reactor-inlet N₂: 5.25%, published 5.0%;
  - outlet MeOH / H₂O: 7.63 / 7.66%, published 7.4 / 7.2%;
  - overall CO₂-to-methanol efficiency: 94.8%, published 94.3%;
  - reactor-inlet H₂ / CO₂: 70.0 / 23.3%, published 71.3 / 21.9%. The canonical model applies H₂/CO₂ = 3 at the reactor inlet, whereas the anchor's 3:1 is a fresh-feed ratio.

### 2.3 The four Re/TiO₂ states with CO recycled (`canonical_states_co_treatments.csv`)

NPC at 2% purge, EUR/t:

| State | S_CO | inert | recycled central (x_CO) | recycled high (x_CO) | equal-X |
|---|---:|---:|---:|---:|---:|
| 5 wt% Re, 200 °C | 0.00 | 943.30 | 943.30 (0) | 943.30 (0) | 943.30 |
| 1 wt% Re, 250 °C | 0.02 | 961.51 | 957.68 (0.014) | 952.98 (0.248) | 953.03 |
| 1 wt% Re, 200 °C | 0.01 | 966.96 | 965.76 (0.007) | 962.46 (1.000) | 962.81 |
| 5 wt% Re, 250 °C | 0.01 | 1258.17 | 1250.33 (0.075) | 1250.33 (0.075) | 1250.33 |

- The economic order is unchanged at 2% purge in every treatment: 5%-200 < 1%-250 < 1%-200 < 5%-250.
- Rank agreement with STY per g Re is unchanged in every treatment: ρ = 0.40, τ = 0.33, 2/6 pairs inverted. The STY winner (1%-250) stays economic #2.
- Normalized regret falls from 1.930% (inert) to 1.525% (central) and to 1.03% at the high limit. The 1%-250 state is the most CO-selective state, so recycling CO helps it most.
- At each state's own optimum purge (0.5%, lower bound of the grid, in every treatment), the order is 1%-200 < 1%-250 < 5%-200 < 5%-250 in all treatments. Agreement is ρ = 0.80 with 1/6 pairs inverted. Regret is 0.97% (inert), 0.52% (central) and 0.49% (high).

## 3. The 21 Table 4 entries

### 3.1 Inputs and conditions (`table4_gothe2025.csv`, `table4_inputs_closed.csv`)

The source is Gothe et al., ACS Catal. 15, 19111 (2025), Table 4: Re/TiO₂ at 1 and 5 wt%, prereduction at 250 or
500 °C, reaction at 150–250 °C, P 20–100 bar, CO₂:H₂ 1:1–1:4 and GHSV 10–40 × 10³ mL g_cat⁻¹ h⁻¹. The
transcription was checked against the table image.

**Selectivity closure.** '<1' is read as 0. S_MeOH and S_CH₄ are taken as reported, and CO(-like) = 1 − S_MeOH − S_CH₄, the workbook convention. No residual is negative. Two entries whose reported values sum to 101% (T4-08: 89/1/11; T4-20: 98/1/2) close to S_CO = 0.

**Operating point per entry.** Each entry is costed at its own P, which sets the plant loop pressure, and at its own reactor-inlet H₂/CO₂.

**Entries whose conditions differ.** Entries that are not at the canonical operating point (100 bar, CO₂:H₂ 1:4) are flagged in the `Flags` column:

- pressure differs: T4-15 to T4-18 (80, 60, 40 and 20 bar);
- feed ratio differs: T4-19 to T4-21 (1:3, 1:2, 1:1).

The other 14 entries share 100 bar and 1:4. Rank metrics are reported both for all 21 entries and for those 14.

GHSV (10–40k) and prereduction temperature (250 °C entries) are listed as further flags. They change the measured performance but are not plant inputs. The model does not represent the lower condensation efficiency of a 20–40 bar loop.

The four canonical states are T4-03, T4-04, T4-10 and T4-11. Under the inert treatment they reproduce the canonical NPC exactly; the script asserts this.

### 3.2 Per-entry results (`table4_candidate_results.csv`)

NPC is in EUR/t. "opt" means the entry's own cost-optimal purge on the 0.5–40% grid. That optimum is at 0.5% for every entry except T4-07 (0.6%). Ranks: 1 = highest upstream metric or lowest cost.

| ID | Entry | Flags | STY/gRe | STY/gcat | X·S | S_MeOH/CO/CH₄ | NPC inert 2% | NPC recycled 2% | x_CO (central, 2%) | NPC inert opt | NPC recycled opt | rank STY/gRe | econ rank 2% inert/rec | econ rank opt inert/rec |
|---|---|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| T4-01 | 1 wt%, red 250, 200 C, 100 bar, 1:4, 10k | prered. 250 | 15 | 0.15 | 0.056 | 0.80/0.00/0.20 | 1488.30 | 1488.30 | 0 | 1234.68 | 1234.68 | 16 | 20/20 | 19/19 |
| T4-02 | 1 wt%, red 250, 250 C, 100 bar, 1:4, 10k | prered. 250 | 28 | 0.28 | 0.097 | 0.46/0.01/0.53 | 2213.62 | 2213.32 | 0.0002 | 2108.27 | 2083.17 | 11 | 21/21 | 21/21 |
| T4-03 | 1 wt%, red 500, 200 C, 100 bar, 1:4, 10k (canonical) | – | 55 | 0.55 | 0.188 | 0.99/0.01/0.00 | 966.96 | 965.76 | 0.0072 | 895.25 | 891.80 | 3 | 9/9 | 6/4 |
| T4-04 | 1 wt%, red 500, 250 C, 100 bar, 1:4, 10k (canonical) | – | 65 | 0.65 | 0.223 | 0.97/0.02/0.01 | 961.51 | 957.68 | 0.0142 | 903.92 | 896.44 | 1 | 8/8 | 9/8 |
| T4-05 | 5 wt%, red 250, 150 C, 100 bar, 1:4, 10k | prered. 250 | 2 | 0.10 | 0.039 | 0.97/0.00/0.03 | 1445.37 | 1445.37 | 0 | 1062.21 | 1062.21 | 21 | 18/18 | 17/17 |
| T4-06 | 5 wt%, red 250, 200 C, 100 bar, 1:4, 10k | prered. 250 | 8 | 0.40 | 0.176 | 0.98/0.00/0.02 | 993.18 | 993.18 | 0 | 916.66 | 916.66 | 19 | 11/11 | 12/12 |
| T4-07 | 5 wt%, red 250, 250 C, 100 bar, 1:4, 10k | prered. 250 | 13 | 0.65 | 0.260 | 0.65/0.00/0.35 | 1462.41 | 1462.41 | 0 | 1436.48 | 1436.48 | 17 | 19/19 | 20/20 |
| T4-08 | 5 wt%, red 250, 250 C, 100 bar, 1:4, 20k | GHSV; prered. 250 | 30 | 1.50 | 0.258 | 0.89/0.00/0.11 | 1050.70 | 1050.70 | 0 | 1007.70 | 1007.70 | 10 | 14/14 | 16/16 |
| T4-09 | 5 wt%, red 250, 250 C, 100 bar, 1:4, 40k | GHSV; prered. 250 | 49 | 2.45 | 0.207 | 0.94/0.01/0.05 | 1004.74 | 1004.74 | 0 | 943.47 | 940.12 | 4 | 12/12 | 14/14 |
| T4-10 | 5 wt%, red 500, 250 C, 100 bar, 1:4, 10k (canonical) | – | 16 | 0.80 | 0.296 | 0.74/0.01/0.25 | 1258.17 | 1250.33 | 0.0748 | 1232.57 | 1223.30 | 14 | 16/16 | 18/18 |
| T4-11 | 5 wt%, red 500, 200 C, 100 bar, 1:4, 10k (canonical) | – | 18 | 0.90 | 0.320 | 0.97/0.00/0.03 | 943.30 | 943.30 | 0 | 907.43 | 907.43 | 13 | 7/7 | 11/11 |
| T4-12 | 5 wt%, red 500, 200 C, 100 bar, 1:4, 20k | GHSV | 37 | 1.85 | 0.323 | 0.98/0.00/0.02 | 930.11 | 930.11 | 0 | 894.12 | 894.12 | 6 | 2/2 | 4/6 |
| T4-13 | 5 wt%, red 500, 200 C, 100 bar, 1:4, 30k | GHSV | 48 | 2.40 | 0.277 | 0.99/0.00/0.01 | 930.96 | 930.96 | 0 | **886.18** | **886.18** | 5 | 3/3 | **1/1** |
| T4-14 | 5 wt%, red 500, 200 C, 100 bar, 1:4, 40k | GHSV | 59 | 2.95 | 0.257 | 0.99/0.00/0.01 | 936.84 | 936.84 | 0 | 887.68 | 887.68 | 2 | 6/6 | 2/3 |
| T4-15 | 5 wt%, red 500, 200 C, 80 bar, 1:4, 20k | **P 80**; GHSV | 20 | 1.00 | 0.168 | 0.99/0.00/0.01 | 980.09 | 980.09 | 0 | 899.18 | 899.18 | 12 | 10/10 | 7/9 |
| T4-16 | 5 wt%, red 500, 200 C, 60 bar, 1:4, 20k | **P 60**; GHSV | 16 | 0.80 | 0.137 | 0.98/0.01/0.01 | 1007.27 | 1007.27 | 0 | 906.79 | 903.91 | 14 | 13/13 | 10/10 |
| T4-17 | 5 wt%, red 500, 200 C, 40 bar, 1:4, 20k | **P 40**; GHSV | 9 | 0.45 | 0.078 | 0.98/0.01/0.01 | 1118.16 | 1118.16 | 0 | 936.50 | 936.50 | 18 | 15/15 | 13/13 |
| T4-18 | 5 wt%, red 500, 200 C, 20 bar, 1:4, 20k | **P 20**; GHSV | 6 | 0.30 | 0.049 | 0.98/0.01/0.01 | 1279.76 | 1279.76 | 0 | 987.83 | 987.83 | 20 | 17/17 | 15/15 |
| T4-19 | 5 wt%, red 500, 200 C, 100 bar, 1:3, 20k | **1:3**; GHSV | 32 | 1.60 | 0.216 | 0.98/0.01/0.01 | 935.42 | 932.65 | 0.0341 | 891.24 | 887.31 | 9 | 5/5 | 3/2 |
| T4-20 | 5 wt%, red 500, 200 C, 100 bar, 1:2, 20k | **1:2**; GHSV | 35 | 1.75 | 0.176 | 0.98/0.00/0.02 | 931.57 | 931.57 | 0 | 894.91 | 894.91 | 8 | 4/4 | 5/7 |
| T4-21 | 5 wt%, red 500, 200 C, 100 bar, 1:1, 20k | **1:1**; GHSV | 36 | 1.80 | 0.125 | 0.96/0.02/0.02 | **928.26** | **920.97** | 0.0983 | 900.50 | 891.94 | 7 | **1/1** | 8/5 |

The CO-recycle effect at 2% purge is −7.8 EUR/t at most under the central rule (T4-10; T4-21 −7.3; T4-04 −3.8)
and −25.2 EUR/t at the high limit (T4-02). The 11 entries whose closed S_CO is 0 are unaffected. So are four
more entries under the central rule at 2% purge (T4-09, T4-16 to T4-18), because their inert loops are already below
RWGS equilibrium. In this candidate
set CO is a minor by-product (S_CO ≤ 2%) and CH₄ carries most of the selectivity loss, so the treatment moves costs
by less than 1%. The generalized model exists for CO-selective catalyst families, which this set does not contain.

### 3.3 Upstream vs economic rankings (`table4_rank_metrics.csv`, `table4_summary.json`)

Regret = (C[upstream winner] − C[economic winner]) / C[economic winner]. Ties in an upstream metric are ranked
together and do not count as inversions. STY per g Re has 1 tied pair, STY per g catalyst has 2 and X·S_MeOH
has 1.

**All 21 entries**

| CO treatment, purge basis | Economic winner (EUR/t) | Upstream metric | Upstream winner (econ. rank) | Spearman ρ | Kendall τ_b | Inversions | Regret |
|---|---|---|---|---:|---:|---:|---:|
| inert, 2% | T4-21, 1:1 (928.26) | STY/gRe | T4-04 (#8) | 0.659 | 0.454 | 57/210 | 3.58% |
| | | STY/gcat | T4-14 (#6) | 0.760 | 0.584 | 43/210 | 0.92% |
| | | X·S_MeOH | T4-12 (#2) | 0.451 | 0.329 | 70/210 | 0.20% |
| **recycled central, 2%** | T4-21, 1:1 (920.97) | STY/gRe | T4-04 (#8) | 0.659 | 0.454 | 57/210 | 3.99% |
| | | STY/gcat | T4-14 (#6) | 0.760 | 0.584 | 43/210 | 1.72% |
| | | X·S_MeOH | T4-12 (#2) | 0.451 | 0.329 | 70/210 | 0.99% |
| inert, own optimum purge | T4-13 (886.18) | STY/gRe | T4-04 (#9) | 0.630 | 0.444 | 58/210 | 2.00% |
| | | STY/gcat | T4-14 (#2) | 0.678 | 0.517 | 50/210 | 0.17% |
| | | X·S_MeOH | T4-12 (#4) | 0.332 | 0.263 | 77/210 | 0.90% |
| **recycled central, own optimum purge** | T4-13 (886.18) | STY/gRe | T4-04 (#8) | 0.652 | 0.473 | 55/210 | 1.16% |
| | | STY/gcat | T4-14 (#3) | 0.643 | 0.488 | 53/210 | 0.17% |
| | | X·S_MeOH | T4-12 (#6) | 0.299 | 0.234 | 80/210 | 0.90% |

**14 entries at 100 bar, CO₂:H₂ 1:4**

| CO treatment, purge basis | Economic winner (EUR/t) | Upstream metric | Upstream winner (econ. rank) | Spearman ρ | Kendall τ_b | Inversions | Regret |
|---|---|---|---|---:|---:|---:|---:|
| inert, 2% | T4-12 (930.11) | STY/gRe | T4-04 (#5) | 0.582 | 0.385 | 28/91 | 3.38% |
| | | STY/gcat | T4-14 (#3) | 0.673 | 0.508 | 22/91 | 0.72% |
| | | X·S_MeOH | T4-12 (#1) | 0.591 | 0.429 | 26/91 | 0 |
| **recycled central, 2%** | T4-12 (930.11) | STY/gRe | T4-04 (#5) | 0.582 | 0.385 | 28/91 | 2.97% |
| | | STY/gcat | T4-14 (#3) | 0.673 | 0.508 | 22/91 | 0.72% |
| | | X·S_MeOH | T4-12 (#1) | 0.591 | 0.429 | 26/91 | 0 |
| inert, own optimum purge | T4-13 (886.18) | STY/gRe | T4-04 (#5) | 0.644 | 0.451 | 25/91 | 2.00% |
| | | STY/gcat | T4-14 (#2) | 0.605 | 0.442 | 25/91 | 0.17% |
| | | X·S_MeOH | T4-12 (#3) | 0.398 | 0.275 | 33/91 | 0.90% |
| **recycled central, own optimum purge** | T4-13 (886.18) | STY/gRe | T4-04 (#5) | 0.657 | 0.472 | 24/91 | 1.16% |
| | | STY/gcat | T4-14 (#2) | 0.579 | 0.420 | 26/91 | 0.17% |
| | | X·S_MeOH | T4-12 (#4) | 0.358 | 0.253 | 34/91 | 0.90% |

The recycled-high and equal-X rows are in `table4_rank_metrics.csv`.

**Upstream vs economic winner.**

- The STY-per-g-Re winner is T4-04 (1 wt% Re, 250 °C; 65 g g_Re⁻¹ h⁻¹). It is never the economic winner in either CO treatment or on either purge basis. Its economic rank is #8–#9 of 21 and #5 of 14.
- The economic winner is a 5 wt% Re, 200 °C state at higher space velocity:
  - at 2% purge: T4-12 among the 14 same-point entries, and T4-21 among all 21. T4-21 runs at CO₂:H₂ 1:1, a different operating point;
  - at the own-optimum purge: T4-13 in every treatment.

**Ranking robustness.**

- At 2% purge the CO treatment does not change any economic rank among the 21 entries. It changes only the cost gaps, and with them the regret. The STY-per-g-Re regret rises from 3.58% to 3.99%, because the economic winner T4-21 is itself CO-forming.
- At the own-optimum purge, recycling CO moves T4-03, T4-04, T4-19 and T4-21 up the ranking and lowers the STY-per-g-Re regret from 2.00% to 1.16%.

## 4. Files

| File | Content |
|---|---|
| `data/meoh/meoh_general_model.py` | generalized model (imports the canonical engine; engine file unchanged) |
| `validate_general_model.py` | reproduction gates, reference loop, four Re states |
| `validation_summary.json` | all gate values, reference-loop rows, four-state costs and rank metrics |
| `reference_loop_comparison.csv` | anchor loop under each CO treatment vs the published loop |
| `canonical_states_co_treatments.csv` | four Re states × four CO treatments (2% and optimum purge) |
| `table4_gothe2025.csv` | Table 4 transcription (input) |
| `table4_inputs_closed.csv` | closed selectivities, upstream metrics, condition flags |
| `run_table4_candidates.py` | 21-entry analysis |
| `table4_candidate_results.csv` | per-entry costs (four treatments, 2% and optimum purge), x_CO, loop state, ranks |
| `table4_rank_metrics.csv` | ρ, τ_b, inversions, tied pairs, winners, regret: 2 sets × 4 treatments × 2 purge bases × 3 metrics |
| `table4_summary.json` | headline winners and metrics; CO-recycle cost effect per entry |
