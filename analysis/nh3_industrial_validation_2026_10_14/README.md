# NH3-FINAL-1.2 industrial failure triage (2026-10-14)

**Scope:** read-only verification and falsification triage of the pre-registered industrial benchmark in `analysis/validation_nh3_plant_2026_10_13/`. This is **not** a corrected industrial simulator, a new pass threshold or a license to label a model 'validated'.

## Baseline
Original preregistration: NH3-FINAL-1.1, **14/64** passes. On the upgraded thermodynamic basis NH3-FINAL-1.2, **32/64** passes: state 18/28; compression 0/3; converters 5/20; industrial-design outcomes 9/12; separator 0/1. All 64 metric IDs, source rows, original windows and rules remain fixed.

## Audit contract
- Pin the Git blob bytes of the preregistration, the reference ledger (1,589 values), the benchmark cases, all metrics/windows, the recorded 1.2 metric table and its summary. Changed evidence fails loudly.
- Independently score all 64 outcomes from the unchanged registered rules, compare outcomes and per-table statistics; validate all source IDs and disallow web-summary facts in scored metrics.
- Preserve all 32 failures and assign one *provisional diagnostic family* each, with source/equipment inputs needed to discriminate mechanism from non-equivalent comparator.
- Produce `triage_64.csv`, `summary.json` and `REPORT.md` as Actions artifacts. CI pass is evidence integrity and reproducibility, NOT industrial physics validity.
- No ad-hoc refitting and no changes to `provenance/`, `docs/`, `data/` or the original benchmark.
- The supplemental E01 27-versus-30-bar suction-pressure ratio bound uses an explicit ideal-isothermal hypothetical, not a replacement compressor prediction.

## Running
GitHub Actions workflow: `.github/workflows/nh3-industrial-validation-triage.yml`.
Push or PR executes the independent forensic audit (Python standard library only). For complete NH3 model re-execution, select **Run workflow** on the branch and set `full_recompute=true`. That optional job runs the original NH3-FINAL-1.2 harness and compares every recomputed row against the preserved snapshot. Full source-model recomputation is not inferred from the faster score-only audit.

## Scientific priorities indicated by the failures
1. **Plant separator/VLE:** all five literature inlet NH3 cases fail, as does the NH3 saturation-table comparison; source-specific mixed-gas separator validation is required.
2. **Compression/hydraulics:** all three power checks fail. Need matched suction/discharge basis, efficiencies, auxiliary inclusion and sourced pressure loss. Do not replace fixed 3 bar by arbitrary fitted losses.
3. **Measured-bed heat transfer:** four source-conditioned outlet bed temperature comparisons fail even though two outlet NH3 and inverse required-volume checks pass. This is direct evidence of profile mismatch, not proof of a specific rate-law error.
4. **Plant design constraints:** nine unconstrained cost-optimal bed comparisons fail; the model optimizes a different engineering contract from installed hardware. Need coupled reactor/hydraulics/heat exchange/equipment costs for comparable predictions.
5. **KAAP economics:** financed Ru selection, staged inventory split and NH3 outlet have distinct comparisons and source contracts. Do not equate an assumed 12% metal-finance decision with published lower lease rates.

## Interpretation gate
Never infer that the 32/64 benchmark proves absolute industrial plant-cost accuracy. Scientifically defensible ranking, backward design and sensitivity results remain conditional on the model. Industrial validation only advances if source-matched physical predictions improve under **separately preregistered inputs and unchanged, prospective acceptance rules**.


## Source-grounded separator/VLE follow-up

`diagnose_separator_vle.py` is a **noncanonical read-only physical sensitivity**, not an engineering calibration.
It reconstructs Ullmann/BASF Table 5 from 28 source-fact rows for N₂:H₂ = 1:3, at seven temperatures (−30 to 30 °C)
and four pressures (10, 15, 20, 30 MPa), pins the original NH3-FINAL-1.2 comparison, and evaluates:

- Why `p_sat(T)/P` cannot be repaired over the industrial pressure range by a single multiplier, even at one temperature.
- Piecewise bilinear interpolation **strictly inside** the printed table (no extrapolation, no regression).
- Five reactor-inlet **vapor proxies** versus reported plant inlets. Vapor after the separator is not identical
  to a mixed reactor inlet; these proxy values are never rescored as plant validation.
- A gated one-factor *counterfactual*: temporarily substitute the tabulated separator vapor into the original
  NH3-FINAL-1.2 loop state solver, preserve equilibrium, catalyst and economic equations exactly, rerun each
  inlet case through its full loop balance and measured-Fe plug-flow sizing, then restore the source function.

The Actions job `separator-vle` generates `saturation_28.csv`, `plant_inlet_proxy_5.csv`,
`conditional_model_inlet_5.csv`, `REPORT.md` and `summary.json`. Missing source composition and
equipment details, inert dilution, fugacity/activity consistency and high-pressure mixture VLE must be
reviewed before any such correction could be proposed for a new model version. **All registered scores
remain exactly 32/64, including five failed inlet-NH3 comparisons and V01.**
