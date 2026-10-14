# NH3-FINAL-1.2 industrial-validation decision record

**2026-10-14.** Read-only audit and source-conditioned mechanistic falsification.
**Status: reproducible source-model benchmark; industrial closure NOT established.**
All numbers in this file are from the registered comparison and Actions artifacts, not new industrial plant measurements.

## What was reproduced

- NH3-FINAL-1.1 preregistered baseline **14/64**; NH3-FINAL-1.2 upgrade **32/64**. Breakdown: loop states A **18/28**, compressor E **0/3**, converter B **5/20**, revealed engineering design C **9/12**, separator V **0/1**.
- [Full 1.2 single-process model replay](https://github.com/stloendays/Catalyst-Essay/actions/runs/38516578920): 64/64 verdicts unchanged; max absolute raw metric discrepancy **7.99999998e-6** (metric-specific units). Registered rules, source rows, optima anchors and scientific score totals preserved; changing run-duration metadata was ignored **only after** pinning the original summary separately.
- No original process, kinetic, equipment, literature, provenance, manuscript or score files have been edited. CI acceptance certifies **software replay integrity**, not plant accuracy.

## Mechanistic diagnostics, with different evidential statuses

| Question | Evidence | Result | Interpretation |
|---|---|---|---|
| Is source gas-liquid NH3 equal to ideal `p_sat/P`? | Ullmann/BASF Table 5, 28 sourced entries, 10-30 MPa, -30 to +30 C | Original model/source ratio **0.423-0.762**, falling with pressure in every temperature slice | Model separator approximation is systemically biased **against that measured 1:3 N2/H2 gas-mixture comparator** |
| Does source-based separator vapor alone recover industrial reactor inlets? | Change only separator input in unchanged 1.2 loop; five independently reported inlet NH3 concentrations | Five improve, **1/5** within original +/-20% inlet diagnostic band | Correcting this input does not close whole-loop mismatch; conditional sensitivity, never a revised baseline |
| What separator vapor would the existing loop require to hit the five measured reactor inlets? | Inverse solution of *unmodified* source loop closure at five published operating points | TOP140 **5.314% (1.32x BASF)**; TOP220 **5.562% (1.79x)**; UHDE188 **5.821% (1.47x)**; KELLOGG150 **2.733% (1.61x)**; BRAUN150 **5.279% (1.10x)** | Fitted-to-target **requirements**, not source-independent predictions or credible VLE predictions |
| Can literature flows and stoichiometry alone support the single-separator inlet level? | Source matched inlet NH3, inlet flow, and nominal NH3 design output; NH3-free fresh gas | Best-case inlet bounds **3.143% / 2.275% / 2.941%** for TOP140 / TOP220 / UHDE188 versus printed **4.10% / 3.80% / 4.18%** | **Conditional source-flowsheet mismatch**. Do NOT allege real mass-conservation failure: BASF table gas and plant gas differ; multi-stage separation, purge, inerts, and flow measurement boundaries remain incompletely mapped |
| Is the S-200 measured Fe converter discrepancy a uniform rate scaling? | Source-conditioned two-bed forward/inverse calculations, two operating points | For target heat rise, required/installed volume first bed **1.634 and 1.638**, second bed **0.983 and 1.006** | A uniform multiplicative activity adjustment cannot match both bed targets under these fixed-source trajectory assumptions |
| Can E01 compressor discrepancy be explained by 27 versus 30 bar fresh suction alone? | Extreme ideal-isothermal pressure-ratio correction applied generously to all modeled combined power | Model **7.500 MW**, bound **7.989 MW**, source **13.0 MW** | Approx. **38.5% of published duty** remains outside even this generous correction; equipment scope/efficiency/staging/hydraulics unresolved |

Detailed machine-readable evidence: [full replay](https://github.com/stloendays/Catalyst-Essay/actions/runs/38516578920/artifacts/11872094767), [VLE/inverse diagnostic](https://github.com/stloendays/Catalyst-Essay/actions/runs/38518037794), [source-only flow bounds](https://github.com/stloendays/Catalyst-Essay/actions/runs/38518512364/artifacts/11873225265), and [industrial-physics follow-up issue #88](https://github.com/stloendays/Catalyst-Essay/issues/88).

## Scientific decision

**Do not promote an alternative VLE input or inverse-target value to NH3-FINAL-1.2.** These tests expose a model-comparator mismatch; they do not identify a unique correction. The manuscript's Fe/Ru/Os economics, reachable scaling envelope and backward-design claims remain **conditional on the explicitly defined process model**, not independently calibrated predictions for full industrial ammonia synthesis hardware.

These discrepancies appear *before* any catalyst or metal-cost optimisation. Therefore, an improved engineering validation should first match **complete plant process topology and measured feed/stream boundaries** before recomputing catalysts under a modified model.

## Next preregistered engineering closure

1. For at least two same-source flowsheets (e.g. Dybkjaer Topsoe 140/220 bar and Appl's Uhde 188 bar), record the **exact named stream** of each flow, NH3 concentration, inerts, bypass/makeup, separator number and pressure/temperature. State normal-volume and throughput bases explicitly, independent of any economic optimiser.
2. Replace the *candidate* mixture-separator calculation with a thermodynamically valid high-pressure H2/N2/NH3/Ar/CH4 vapor-liquid description, then verify it against held-out tabulated VLE and in-domain measured separator outlets. Do not extrapolate the 28-point 1:3 table.
3. Match compression duties with actual suction/discharge and interstage conditions, equipment/auxiliary scope and a physically sourced pressure-loss model. Do not arbitrarily increase the canonical 3-bar recycle drop.
4. Check both beds of the measured S-200 plant jointly with source gas, catalyst geometry/effectiveness and heat transfer. Do not independently fit one scale factor per bed.
5. Then freeze a new *separately named* engineering candidate and reassess absolute prediction error, feasible design spaces, Fe/Ru/Os cost ordering, ranking robustness and backward-design reachability on original and held-out cases. Report failing cases and unchanged original benchmark scores.

**Review gate:** PR #87 remains draft; merge of auditing code is separate from acceptance of industrial predictive validity. The original main manuscript is not to be updated with conditional sensitivity scores.
