# Scientific claim contract — reviewer handoff, not manuscript prose

This is a **reviewer-facing evidence map**, not a replacement for the
author-written paper. All field analyses below are the 2026-10-08
**author-selected but not yet frozen** treatment. Maintain the causal hierarchy:

**measured/DFT property → operating constraints → process state → economic
objective → ranking choice → physically attainable material target.**

## 1. Atomic/descriptor ranking: ammonia only

**Claim:** In the 15-metal benchmark, intrinsic Ru > Os > Fe becomes Fe > Ru
> Os in the catalyst-dependent plant-cost objective.

**Quantitative basis:** 14,136 process states separately optimized per metal;
Fe/Ru/Os = 15.292/22.031/25.832 USD/t NH3. These are **catalyst-dependent
costs**, not a claim that complete ammonia plants cost 15–26 USD/t.

**Evidence:** provenance/nh3_final_1_1 and manuscript Figure 1, Figure 3.

**Prohibited leap:** A field-level ammonia *rate per g catalyst* or a methanol
*STY per g catalyst* is not equivalent to this DFT-derived atomic descriptor.

## 2. Benchmark Ru versus promoted, supported Ru are different systems

**Claim:** Pure benchmark Ru in the fused-iron bed formulation remains more
costly over the stated economic uncertainty range. A supported/promoted Ru/C
catalyst, with independently supported exposed-metal fraction, metal loading,
bed density and recovery, can approach Fe cost under a KAAP-type low-pressure
loop.

**Quantitative basis:** Fe optimum 15.292 USD/t versus benchmark Ru 22.031;
for actual Ru/C at 8 wt%, 430–550 kg/m3 and 90–97% recovery, the high-pressure
main loop gives 15.627–16.012 vs Fe-main 15.292; KAAP loop gives
18.492–19.079 vs Fe within KAAP 19.069. These are **two different Fe
denominators**. At the specified 8 wt% grid, KAAP has 3/4 corners below
its own Fe benchmark.

**Evidence:** figures/composite/fig2/fig2_ru_actual_cost_points.csv;
fig2_ru_bed_sensitivity.csv; analysis/nh3_actual_ru_params_2026_10_07;
read-only referee PR #45.

**Prohibited leap:** Do not interpret the pure-Ru 5000/5000 economic
draw result as disproving promoted Ru/C parity. Do not compare Ru-KAAP
against Fe-main optimum without explicitly saying the process loops differ.

## 3. Backward target and physical reachability are different tests

**Claim:** The 201.22-fold *direct activity multiplier* needed for baseline
Ru economic parity is inaccessible along the stated strict scaling relation
(2.525-fold maximum among process states). Laboratory promotion or support
changes may alter the admissible physics/dispersion and are not tests of
strict-manifold reachability.

**Evidence:** Figure 4 and analysis/fe_bridge_backward_2026_09_29;
strict descriptor/scaling and lifecycle analyses.

**Prohibited leap:** A promotion that produces 75-fold activity, in a
different catalyst and normalization, is not evidence that the baseline
201-fold economic parity has been realized under the same reactor conditions.
A physically inaccessible target in the strict descriptor space is compatible
with a lower target in the promoted, supported/recovered catalyst space.

## 4. Literature rankings: distinguish material from operating point

**Claim:** In the selected printed primary cohort, methanol has 15/40
laboratory-STY versus plant-cost winner differences (7 have >5% regret)
and ammonia has 7/33 rate-versus-cost differences (4 have >5% regret).

For methanol, lab conversion gives 10 *different material* winner pairs
among 32 multi-catalyst groups and five *same material, different temperature*
winner pairs among **22** strict temperature-series groups. Of the 10 material
winner pairs, **six share T and four change T**. If catalyst inventory is
adjustable, total mismatches are 14/40 (>5% in three), material winner pairs
are five (three same T, two joint material+T), and same-material temperature
winner pairs nine. Same-T winner pair does not certify the entire comparison
group is isothermal.

**Evidence:** analysis/verify_2026_10_08/decomposition_steps.csv,
nh3_printed_summary.json, conversion_sensitivity_summary.json;
read-only referee PR #43 and #47.

**Prohibited leap:** 15/40 is not an atomic-to-economic ranking inversion
frequency. 10/32 is not the estimated probability that *changing only the
catalyst* changes an optimum. The 6/4 partition is descriptive. Do not use
the 83-group or 124-group historical bootstrap CI in selected cohorts.

## 5. Methanol source-imputation and sensitivity limitations

The main extraction filter requires printed CO2 conversion and MeOH
selectivity, but unreported CO/CH4 fractions may be closed using the carbon
balance. The source-provenance audit identifies 206/348 S5 printed-corpus
candidates with one or more missing CO/CH4 printed components, including
a winner of 13/15 lab-conversion disagreements. Those records are **not**
evidence that the ranking is erroneous, but the imputed-product sensitivity
must be disclosed.

Increasing catalyst inventory follows a calibrated hypothetical
X(m) trend while product selectivity is held fixed. It is a model
counterfactual, not an experimentally observed independent temperature
optimization or independently calibrated commercial kinetic law.

**Evidence:** meoh_candidates.py / meoh_general_model.py; referee PR #44;
analysis/verify_2026_10_08/meoh_conversion_sensitivity.py.

## 6. Cost-model validity: avoid a total-cost camouflage

A reproduction of the reference methanol break-even sale price to −2.4%
(706.108 vs 723.6 EUR/t) does not independently validate the
catalyst-dependent portion of the cost model. At reference H2 price,
the common three-H2-per-MeOH stoichiometric commodity floor alone is
583.212 EUR/t (82.6% of the harmonized model total). After a diagnostic
subtraction, the model/reference remaining costs are
122.896/140.388 EUR/t (−12.46%). These residuals are not a new
catalyst-only LCoM or an error metric certified for material comparisons.
The like-for-like cost uses *reference* fixed O&M, not the separately
reported model fixed O&M. Compressor-only work and net utilities are
different boundaries.

**Evidence:** analysis/meoh_plant_benchmark_2026_10_06,
ED Fig. 4, referee PR #46.

## 7. Deterministic physics versus extraction/model choices

**Claim:** ACSA makes the multiscale chain reusable and covers additional
published candidates; it does not introduce an additional independent
reaction kinetic model in each paper. Descriptor/plant-cost lower bounds,
hard cost constraints, candidate grouping and scorer remain deterministic,
while extraction and workflow selection involve model decisions.

**Accuracy facts:** 717/741 curated methanol records recovered is
*record recall*, not numeric transcription accuracy. Printed SI MeOH
selectivity is strictly correct in 123/128 values, and printed SI STY
in 116/121; main-text table results differ by field. Never write that
every printed value is exactly correct.

**Evidence:** agent/extraction/eval/field_accuracy_by_source.csv;
analysis/verify_2026_10_08/REPORT_zh.md; supervisor feedback on model
credit assignment and scientific decisions.

## 8. Selection and null-model logic

The Au/TiO2 CO oxidation particle-size case is the monotonic control:
it establishes that the framework does not inevitably invert a ranking
when the catalyst property affects only the mass requirement through a
common monotonic mapping. It does not prove that all monotonic activity
models will preserve an economic rank under arbitrary price, lifetime,
operating-condition or separation changes.

**Evidence:** Figure 6 and data/rank_preservation_control_v1_1.csv.

## Release/freeze acceptance gate

Require author approval of every extracted-paper gold-standard entry,
source-resolved data repairs, consistently regenerated selected cohort
scores, regenerated 28-paper DOI bootstrap, corrected Fig. 2 and ED Figs
2–4, verified Fe same-loop comparator and an SI 5f genuinely computed
using S5 printed sensitivity.

Run the independent review:

    python analysis/review_claim_lineage_2026_10_09/check_claim_lineage.py --out-dir /tmp/review --publication-gate

The numeric/claim gate may report PASS only after these sources have been
truly regenerated. A passing Python test is not a scientific freeze,
acceptance of the manuscript wording, or evidence of manual paper checking.
