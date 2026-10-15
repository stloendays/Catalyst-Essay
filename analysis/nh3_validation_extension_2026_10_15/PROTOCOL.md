# Prospective-analysis protocol | NH3 source VLE predictive checks and industrial scope gates

**Committed before implementation/results for this source-based follow-up (2026-10-15).** Do NOT modify any preregistered original 64-metric NH3 industrial benchmark, its acceptance bands, source ledger, baseline source models, or manuscript. Models below are fitted only to source literature saturation measurements and evaluated out of temperature/pressure strata; their success is not automatically industrial process or Fe/Ru economic validation.

## P1: Cross-validated predictive ability on independent BASF/Ullmann NH3 vapor data

Data are the independently image-verified Ullmann/BASF ammonia equilibrium vapor concentrations above liquid NH3 with 1:3 N2:H2 gas at 7 temperatures (-30,-20,-10,0,10,20,30 C), 4 pressures (10,15,20,30 MPa), as locked by 'analysis/nh3_industrial_validation_2026_10_14/diagnose_separator_vle.py' (28 original literature entries). The original model's saturation baseline is 'psat_nh3_bar(T_C)/P_bar'. It contains no adjustable parameter. The mixed N2/H2 vapor comparator is not the same as an industrial loop with CH4/Ar/inerts, multiple separators and makeup mixing. Source table is NOT a new industrial plant dataset.

Predeclared three models on mol fraction y:
- M0: original ideal-gas baseline y0=p_sat(T)/P, no fit, fixed.
- M1: one-parameter effective pressure correction y=y0 * exp(k * X), where X=(P_bar-p_sat_bar)*100000 / (R*(T_C+273.15)), R=8.314462618 J/mol/K. Constrain k>=0 and <=1e-3 m3/mol. Fit least-squares on z=ln(y_source/y0), no intercept, equally weighted source table rows. This is an EFFECTIVE pressure parameter, not measured liquid molar volume or a validated gas fugacity coefficient.
- M2: two-parameter log ratio z=a + k X, with k>=0 and <=1e-3; least-squares fits a and k on training only. a captures unmodeled fugacity/composition, not a measured thermodynamic property. Neither regression uses catalyst, industrial process, 64-case scoring or an empirical plant target.
- Deterministic blocked validation: 7 leave-one-T-out folds, training 24 and holdout four pressure points; 4 leave-one-P-out folds, training 21 and holdout seven temperatures. Every one of 28 source points appears exactly once in each validation. Boundary folds are extrapolations relative to training support, still within the original total source domain, not new apparatus conditions.
- Metrics per fold and overall: mean and median absolute log(yhat/y_source), mean absolute relative error |yhat/y_source-1|, fraction within original comparator ±20% of source, log-bias, max absolute relative error; absolute pointwise predictions and training coefficients; both equal source-entry weighting. No 28-point in-sample result is to be mislabeled external holdout; the source is externally published relative to the canonical surrogate but validation splitting is internal to that single 28-point reference.
- One-parameter is deemed predictively better than M0 only if heldout mean absolute log-error is strictly lower on BOTH T and P blocking. Two-param results reported regardless of signs; if bias correction helps, it does not establish a causal EOS law.
- Source gates: 28 unique (T,P) points, original source string and Git-blob pins unchanged; canonical Antoine baseline reproduced at each grid row (<1e-5 source-percent absolute), M0 log ratio consistent with original source model; all predictions positive and finite and <100% mole fraction. No high-pressure EOS refit to registered 64 industrial outcomes.
- No value of fitting these 28 records can silently change original 32/64 industrial score. No "1/5 industrial inlet pass" counterfactual re-scoring here; that earlier no-fit source-vapor substitution remains a separate PR.

## P2: Compressor and kinetic applicability gate

Industrial original model/preregistered source: 'analysis/validation_nh3_plant_2026_10_13/nh3_1_2/results_metrics.csv', source pin checked by original audit_industrial.py. E01 and E02 measure fresh+recycle compressor MW, E03 is recycle-only MW; all three failed their predeclared rel:0.30 acceptance. The calculation here is purely algebraic and does NOT reinterpret unlike equipment boundaries.

- For each E case compute source/model power ratio, missing MW, and interval of hypothetical multiplicative factor c that would pass the original ±30% criterion for that case: [(1-0.30)*source/model, (1+0.30)*source/model].
- Intersect all three intervals, and separately E01/E02 (comparable combined machinery) only; report whether one shared coefficient can pass, but explicitly note that E03 has a DIFFERENT equipment boundary and invalidates inference that a real global compressor efficiency exists.
- E01 "generous" fresh suction 27 vs model 30 bar / discharge 151bar is reused from original pinned independent audit; do not fit arbitrary compressor factors to source.
- Measured-source kinetics: Fe Dyson-Simon source 149–309 atm (convert to bar *1.01325); promoted Ru/C Rossetti source 50–100 bar. Pressure ranges disjoint; do not claim a matched-pressure common-domain benchmark. A descriptor-driven result is neither measured Fe nor promoted Ru/C kinetic validity.
- Existing 'analysis/nh3_loop_reconciliation_2026_10_14/outputs/t3_points.csv' grouped by pair/model_basis and catalyst (Fe,Ru); test pair completeness, number of pairs, and pressure validity for each named source at its own pressure. Report how many pair observations are both within their OWN respective domains (which is not common-pressure kinetic validation). A cost sign switch between two model bases is an uncertainty flag, not a validated design ranking.
- Original registered A/B/C/E/V 18/28,5/20,9/12,0/3,0/1 and 32/64 overall must remain unchanged. New work is NOT a direct solution of the full plant's heat/mass/pressure balance.

## Execution and reporting

New branch, one folder 'analysis/nh3_validation_extension_2026_10_15' and one read-only Actions workflow. Two independently runnable stdlib scripts, deterministic synthetic unit tests, output CSV/JSON/Markdown, CI source pins, no secrets and no changes to frozen files. If any modeled pass criterion is not met, record negative evidence, never retune after running. PR remains draft awaiting scientific review.
