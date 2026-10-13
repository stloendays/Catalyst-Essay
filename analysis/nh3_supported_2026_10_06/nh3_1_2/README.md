# Measured ammonia catalysts through NH3-FINAL-1.2 — 2026-10-13

The Humphreys 2021 chain of the parent folder (`run_supported_chain.py`, same inputs `agent/nh3_supported/out/records.csv`)
run on NH3-FINAL-1.2 (`provenance/nh3_final_1_2/README.md`, run `nh3_final_1_2_20261013`): Gillespie–Beattie NH₃
formation free energy, Newton–Cooper fugacities in the loop and the microkinetics, F_CAL 74,351.6, 14,510 process states.
Same file names as the 1.1 outputs one level up.

    set NH3_MODEL=1.2
    set NH3_HARNESS_1_2=D:\论文-AI4S\wt-nh3-12\provenance\nh3_final_1_2\source_harness   (holds cache/ with the 1.2 surface)
    D:\Research\CatalystForge\.venv\Scripts\python.exe -X utf8 analysis\nh3_supported_2026_10_06\run_supported_chain.py

With `NH3_MODEL=1.1` (default) the same script rewrites the parent folder's three files byte for byte (git diff empty).
The script refuses to run if the selected run's response surface is not in `cache/` (it never rebuilds one), and before
scoring any catalyst it checks that its pure-metal path reproduces all 15 metal costs of the selected run's
`results.json` (|diff| < 1e-9 USD/t; passes for 1.1 and 1.2).

## Key numbers, NH3-FINAL-1.1 → NH3-FINAL-1.2

Primary set, no metal recovery, supported bed 1,000 kg m⁻³ (fused Fe: 71.51 wt%, 2,500 kg m⁻³), against the run's own Fe
benchmark.

| Quantity | 1.1 | 1.2 |
|---|---:|---:|
| Fe benchmark (USD/t) | 15.29 | **11.52** |
| rows / enter the chain / primary / flagged | 161 / 83 / 73 / 10 | 161 / 83 / 73 / 10 |
| primary per metal (Ru, Fe, Co, Ni) | 54, 9, 5, 5 | 54, 9, 5, 5 |
| fused-iron calibration α (Fe₁₋ₓO, Fe₃O₄; ref. 157, 430 °C, 3 MPa) | 0.65, 0.46 | **0.77, 0.54** |
| best fused Fe (Fe₁₋ₓO), USD/t | 15.51 | **11.74** |
| catalysts below Fe without recovery | 0 | **2**: Ru/Cs/Ba/CCHT 11.01, 20% Fe–BaH₂ 11.19 |
| lowest Ru (Ru/Cs/Ba/CCHT), USD/t; ratio to Fe | 15.32; 1.002 | **11.01; 0.956** |
| lowest Fe-based / Co / Ni, USD/t | 15.51 (Fe₁₋ₓO) / 18.28 / 20.41 | **11.19 (20% Fe–BaH₂)** / 13.10 / 14.32 |
| highest-rate catalyst Ru/AC-G: cost, regret over the plant leader | 17.22, 12.4% | **13.76, 24.9%** |
| Spearman ρ, rate vs plant cost (73) | 0.156 | **0.071** |
| single-source comparisons where rate leader ≠ plant leader | 3 of 9 | 3 of 9 |
| same-support Fe/Ru regrets (ref. 81 BaTiO₃₋ₓHₓ; ref. 82 BaCeO₃₋ₓHᵧN_z) | 15.2%; 12.6% | **17.8%; 12.9%** |
| ref. 164 Ru/BaZr₀.₉Y₀.₁O₃ vs Ru/BaZrO₃ regret | 6.8% | **11.7%** |
| Ru below Fe with 90% recovery | 3 of 54 (Ru/Cs/Ba/CCHT 14.42, Ru/Ba–Ca(NH₂)₂, Ru/Ca(NH₂)₂) | **4 of 54** (the same three + Ru/BaO–CaH₂; Ru/Cs/Ba/CCHT 9.92) |
| median Ru α (per g Ru, against the benchmark) | 0.226 | 0.247 |
| ≥ 5 MPa (15 catalysts): lowest Fe / Ru / Co, USD/t; below Fe | 16.70 / 17.22 / 23.73; none | 12.92 / 13.76 / 17.61; none |
| bed 500 kg m⁻³: below Fe | none | Ru/Cs/Ba/CCHT |
| bed 2,500 kg m⁻³: below Fe | 20% Fe–BaH₂ | 10% Fe/C, 20% Fe–BaH₂, Ru/Cs/Ba/CCHT |
| constant multiplier on the metal's own TOF: below Fe | 9 | 10 (adds 3.4 wt% Co–N–C) |
| median outlet NH₃ for the 20 catalysts without outlet or WHSV | 0.429% | 0.429% |
| process states searched | 14,136 | 14,510 |

The 1.1 column is the committed `../summary.json` (its Spearman ρ is 0.1560; the parent README's table still says 0.158
from before commit 7e96397; both round to 0.16). Over the 82 rows with a cost in both runs, costs move by −3.5 to
−12.4 USD/t and effective descriptors by at most 0.043 eV (median 0.004 eV); the statuses of all 161 rows are unchanged.

Statements of the 1.1 chain that no longer hold on 1.2:
- "No measured catalyst undercuts the fused-iron benchmark without metal recovery": two do. Ru/Cs/Ba/CCHT (327 °C,
  0.1 MPa, printed outlet 0.9%) has a laboratory rate 10^2.80 ≈ 640 times the model's volcano top at that condition
  (α_res, as in 1.1) and costs 11.01 USD/t at 425 °C, 105 bar (Fe: 11.52); 20% Fe–BaH₂ (350 °C, 0.1 MPa, outlet from
  rate and WHSV, on the volcano) costs 11.19. In 1.1 they were 0.2% and 1.6% above Fe.
- The plant leader is still Ru/Cs/Ba/CCHT and the rate leader still Ru/AC-G, but the regret doubles (12% → 25%) and
  rate and plant cost are less correlated (ρ 0.16 → 0.07).
- With 90% Ru recovery four Ru catalysts undercut Fe (three in 1.1).

## The 1.1-specific choice, re-derived

The chain enters the laboratory NH₃ fraction at the same approach to equilibrium as in the experiment,
y_model = (y_out / 2) · y_eq,model / y_eq,exp (both ideal-gas mole fractions; y_eq,exp from the Gillespie–Beattie
constant). In 1.1 the ratio corrects the model's 0.064–0.065 eV per NH₃ offset. In 1.2 the model's NH₃ formation free
energy is the Gillespie–Beattie value, and the same expression gives y_eq,model / y_eq,exp = 1 to rounding
(0.9999999999999982–1.0000000000000016 over the 83 rows), so the laboratory fraction enters unscaled and the model applies
its Newton–Cooper fugacity coefficients to the laboratory gas through `lab_condition` (`h.ctx.condition`), as it does for
every plant state. No code path changed for this: the 1.2 harness core does it (`KineticContext.gas_G`, `condition`).
The Methods sentence on the 0.064–0.065 eV offset therefore describes 1.1 only; on 1.2 there is no offset to correct.

The near-equilibrium screen (y_out ≥ 0.9 y_eq,exp, ideal-gas Gillespie–Beattie) is a property of the laboratory data
and keeps its 1.1 definition, so the primary set is the same 73 catalysts. Sensitivity (`summary.json`,
`nh3_model.screen_newton_cooper`): with the screen on the Newton–Cooper equilibrium, Ru/LaScSi (400 °C, 0.1 MPa,
y_out / y_eq 0.901 → 0.884, cost 17.42 USD/t, the only row of its source) joins: 74 primary, 55 Ru, Spearman ρ 0.070;
leaders, regrets, below-Fe sets and the nine single-source comparisons do not change.

Other inputs of the chain are the same in both runs and are read from the selected run: F_CAL, the state library, the
Fe benchmark, the benchmark active fraction (0.7151) and bed density (2,500 kg m⁻³) of fused Fe.
