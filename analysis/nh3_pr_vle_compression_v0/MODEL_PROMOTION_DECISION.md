# NH3-PHYSICS-V0 research decision | 2026-10-14

**Status: computational implementation reproducible; physical-model promotion blocked.** Original NH3-FINAL-1.2, Fe/Ru/Os economic ranking and all 32/64 original industrial verdicts are unchanged. Current branch is a *research comparison*, not a validated replacement industrial plant model.

## Independent high-pressure VLE evidence

The independent reference is the frozen BASF/Ullmann Table 5 (NH3 saturation in a H2:N2 = 3:1 mixture, 28 T/P points, −30 to +30 °C, 10/15/20/30 MPa). The 20% tolerance and requirement of ≥24/28 passing rows **plus both held-out Uhde separator gas NH3 concentrations passing** were set **before** testing the two models. This is a provisional exploratory physical adequacy gate, distinct from the old 64-case benchmark.

| EOS hypothesis | Fixed binary interactions | BASF rows within ±20% | BASF mean absolute relative error | Uhde gas5 prediction vs 8.51% | Uhde gas6 prediction vs 4.18% | Promotion |
|---|---|---:|---:|---:|---:|---|
| Original ideal saturated-gas p_sat/P | N/A | not rescored | 40.6% | — | — | frozen only |
| Peng–Robinson 1976, pure-liquid saturation | All ten k_ij = 0 | **2/28** | **44.2%** | **12.254%** (+44.0%) | **6.373%** (+52.5%) | **FAIL** |
| PR78 with external Aspen-HYSYS Table 8 (Binous & Bellagi 2022) | k_N2–NH3=+0.222; k_N2–H2=−0.036; other pairs 0 where unsourced | **6/28** | **31.9%** | **11.435%** (+34.4%) | **5.871%** (+40.5%) | **FAIL** |

Model 2 improves prediction without tuning on any BASF/plant target, yet still fails both stages. The 2022 PR parameters were published for *reactor* Haber equilibrium conditions; their transfer to cold industrial NH3 condensation is not established. CH4/Ar BIPs remain unprovided by that source.

Sources:
- [Peng & Robinson 1976, PR EOS](https://doi.org/10.1021/i160057a011)
- [CoolProp pure-component critical property data](https://coolprop.org/fluid_properties/fluids/Ammonia.html) and H2/N2/CH4/Ar analogs
- [Binous & Bellagi 2022, PR binary interaction parameters, Table 8](https://doi.org/10.1002/eng2.12506)
- [Ullmann / Appl 2011 industrial plant Figure 57](https://doi.org/10.1002/14356007.o02_o11)

**Model-form restriction:** Both saturation rows treat the liquid as *pure NH3* and neglect dissolved gases. They do **not** implement a full five-component phase-equilibrium model. The numerical fluxes are source-conditioned, not independent full-loop output predictions.

## Complete source-first-separator TP flash (additional diagnostic)

PR with all binary parameters zero can solve a two-phase φ–φ fixed-pressure/temperature flash with **only observed upstream stream4 composition**. At 21 °C and 180.2 bar, it returns vapor NH3 **11.623 mol%** (literature gas5 **8.510 mol%**), liquid NH3 **95.468 mol%** (literature liquid7 **98.550 mol%**), and vapor molar fraction **0.9040** (source stream5 / stream4 **0.8760**). The calculation is numerical two-phase fugacity convergence but **does not include global thermodynamic phase-stability analysis** and does not pass the source split check. This is a direct prediction comparison, distinct from the stage saturation proxy.

## Source-boundary compression work

From reported Figure57 pressures, temperatures, compositions and flows, the sum of three specified **isothermal reversible** integration paths (raw make-up 10→12, recovered H2 11→12, cold recycle 6→1) is **11.044 MW** with PR compressibility versus **10.794 MW** ideal-gas reference. These figures are physically meaningful *thermodynamic reference-work calculations*, not a measured compressor shaft duty: they omit mechanical efficiency, actual stage and cooling temperatures, equipment pressure losses and plant configuration. The 13 MW E01 comparator concerns **a different facility**; no comparison or calibration is claimed.

## Five-component high-fidelity Helmholtz EOS library check

The independent [Neumann et al. 2020](https://doi.org/10.1016/j.fluid.2020.112496) paper develops mixture Helmholtz energy EOSs for NH3 with N2/H2/CH4/Ar/CO. However, in a fresh GitHub Actions **CoolProp 7.2.0** environment, only **4 of the 10** requisite binary pairs for the full Figure57 N2/H2/CH4/Ar/NH3 stream expose complete reducing coefficients. A fully specified five-fluid equation-of-state calculation was **not** attempted with fabricated defaults. Pair presence alone would not establish the correct 2020 formulation or industrial validity.

The high-priority independent transfer source is [Mace & Vrabec 2024](https://doi.org/10.1021/acs.jced.3c00327): NH3–Ar/CH4/H2/N2/O2 high-pressure gas-liquid VLE, and published PR/PC-SAFT temperature-dependent binary interaction functions in its Supporting Information. The full **numerical SI functions have not yet been source-verified or imported**. No guessed or back-inferred parameters from the 28 BASF or Figure57 outputs are acceptable.

## Blocking next work

1. Obtain and **verify the published 2024 SI** PR/PC-SAFT temperature-dependent binary parameters, exact component source, equation convention, original estimation dataset, and valid T/P domain. Confirm the SI did not use BASF Table5 or Uhde Figure57; if it did, obtain a different independent holdout.
2. Implement thermodynamically stable full multicomponent flash (liquid dissolution of light gases, fugacity consistency and global phase stability), and compare *source-predicted* gas5/liquid7 compositions and phase fractions, then downstream cooling with matched source topology.
3. Use a second fully specified, **independent** industrial flowsheet to validate stage pressures, coolant/refrigeration duty, compressor stage work (sourced isentropic efficiencies and stage map), bed hydraulics/Ergun inputs, and loop mixing under published design conditions. Never infer absolute plant physical accuracy from near-perfect printed-flow internal conservation.
4. Freeze a **separately versioned** engineering model, predeclare accuracy rules and source-held-out inputs, and only then reoptimize **all Fe/Ru/Os** under identical physical constraints. Compare original and new industrial cost ordering, regret, feasibility and Ru backward-design reachability. Do not overwrite any 1.2 archive/hash.

## Verified GitHub Actions

- [Zero-k PR, published-k PR and 16 math/source tests PASS](https://github.com/stloendays/Catalyst-Essay/actions/runs/38527866908)
- [CoolProp 7.2.0 pair coverage, 4/10 without invented fallbacks](https://github.com/stloendays/Catalyst-Essay/actions/runs/38527712408)
- [Baseline source-stream reconstruction and 21 tests](https://github.com/stloendays/Catalyst-Essay/actions/runs/38522624086)

**Interpretation:** GH Actions PASS = numerically reproducible. Science gate FAIL = must not use the attempted EOS for manuscript headline or catalyst ranking. Both are explicitly reported.
