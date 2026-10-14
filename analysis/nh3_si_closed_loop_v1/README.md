# NH3-SI-LOOP-v1: an operable engineering loop from the supplied SI

This implementation shifts the effort from reproducing an entire publication
or attaining an arbitrary historical score to a **physically coherent,
callable process calculation**:

`SI S27 coefficients -> PR phase equilibrium -> two cold separators -> purge/makeup/recycle fixed point -> pressure work and cold duty -> conditional utility tradeoffs`.

## Source versus engineering choices

The user supplied the 34-page Supporting Information of Mace and Vrabec,
*High-Pressure Fluid-Phase Equilibria and Henry's Constants of Supercritical
Gases in Ammonia*, DOI **10.1021/acs.jced.3c00327**. Equation and coefficients
are directly taken from Section 4, Table S27, page S-33. The uploaded file's
SHA256 is recorded in `si_parameters.json`; the copyrighted PDF is not
republished in the repository.

`k_ij(T) = a0 + a1*T + a2*T^2`, **T in kelvin**. PR coefficients are used in PR;
PC-SAFT coefficients are stored separately as source information, not inserted
into the wrong EOS. S27 contains Ar/H2/N2/O2--NH3, **not CH4--NH3**. O2 is not
present in this ammonia-synthesis loop. The missing methane pair is nominally
zero, with independent engineering scenarios -0.1, +0.1 and +0.2. The other
six dry-gas pairs are zero assumptions. These scenarios are neither literature
coefficients nor statistical confidence bounds. Full validity bounds of the
S27 regressions are not supplied on S-33; cold-section use is an engineering
transfer, not a declaration of a validated whole-temperature EOS.

Pure-fluid critical values and acentric factors retain the prior PR experiment
inputs. The standard PR mixing, fugacity and residual-enthalpy equations are
implemented directly; the enthalpy derivative includes **d(k_ij)/dT**.
Reference formulation: [IDAES cubic EOS documentation](https://idaes-pse.readthedocs.io/en/2.0.0/explanations/components/property_package/general/eos/cubic.html).
Fixed ideal-gas Cp values are explicit cold-section approximations, not
parameters reported in the uploaded SI. They affect approximate cold duty,
not mass closure or vapor/liquid equilibrium.

## Scope of the working plant scenario

The explicitly chosen loop is:

1. Specified single-pass N2 conversion in a stoichiometric reactor.
2. First flash at 21 C, 180.2 bar.
3. Purge from the first-separator vapor.
4. Mix the remaining gas with delivered make-up stream 12.
5. Second flash at 0 C, 178.8 bar.
6. Compress the gas to the reactor inlet and close the recycle fixed point.

The independent source-first-separator test uses only upstream stream 4 and
separator T/P; source vapor 5 and liquid 7 are read after predicting the split.
Source data live in the upstream `nh3_source_matched_loop_v0/figure57_streams.csv`.

The main-loop make-up boundary is delivered stream12, including the upstream
hydrogen recovery represented in the source. The upstream recovery itself is
outside this control volume. The chosen simplified topology is not asserted
to be the exact complete source piping arrangement.

Nominal assumptions: N2 single-pass conversion **0.275**, purge **0.03**,
isothermal-equivalent compressor efficiency **0.75**, refrigeration COP **2.5**,
electricity **50 USD/MWh**. Conversion is a reactor specification, **not new
Fe/Ru/Os kinetics**. SI cold-section correlations are not applied at reactor
temperatures. Compressor work and second-stage refrigeration enter a **partial
utility objective**, excluding feed costs, first-stage cooler utility, hot
reactor thermal duty, equipment CAPEX and catalyst inventory. Therefore its
USD/t is not total ammonia cost or the paper's catalyst-dependent cost.

## Useful results from this implementation

At the same first-separator feed, SI PR predicts vapor NH3 **9.792 mol%** versus
**11.623 mol%** with zero interactions and **8.510 mol%** in the industrial
source. Liquid NH3 improves from **95.468%** to **97.105%** (source **98.550%**).
These are full two-phase flash comparisons, not pure-NH3-liquid saturation
proxy results from the previous screening experiment.

The nominal closed loop computes **1484.37 t/d** liquid NH3, **4.942 mol%**
NH3 in the reactor feed and **9.364 mol%** inlet CH4+Ar. The loop has a relative
component residual of about **4.54e-12** and phase log-fugacity error below
**1e-9**. It does not force the source's 1500.24 t/d product value.

There are **34 completed scenarios, zero failed cases**: two EOS reference
cases; a 3x3x3 grid over second-stage temperature, specified conversion and
purge; three missing-methane-pair assumptions; two recycle pressure-rise
variants. All outcomes and any future failures are retained in the output.
Changing cold-stage temperature, purge and pressure loss propagates through
circulation, NH3 recovery, H2 loss and utility consumption.

## Interfaces and execution

- `State(T_K, P_Pa, methane_k=0, mode='si2024').flash(z)`:
  normalized phase compositions, vapor fraction, equilibrium residual, and
  Gibbs comparison to the single-phase state.
- `solve(Settings(...))`: steady-state component flows, pressure-work scenarios,
  approximate second-stage cold duty, utility objective and operating scope.
- `run_research.py --out-dir ...`: all 34 cases plus a readable report.

Requirements: Python 3.12+, NumPy 2.3.5, SciPy 1.17.0.

```sh
python -m unittest discover -s analysis/nh3_si_closed_loop_v1 -p 'test_*.py' -v
python analysis/nh3_si_closed_loop_v1/run_research.py --out-dir artifacts/nh3-si-loop
```

The implementation checks positive flow, species closure, fugacity equality,
Gibbs improvement and multi-start local tangent-plane stability of converged
splits. Single-phase second-stage cases are supported, including zero liquid
flow in cold-duty accounting. Local stability checks are not a mathematical
proof of global phase stability.

The previous 24/28 accuracy screen is preserved in its original experiment;
it is not rewritten to claim a pass. It is also not used to veto clearly
labelled engineering exploration of this new working loop. Canonical
NH3-FINAL-1.2 results, the external 32/64 benchmark and manuscript headline
Fe/Ru/Os rankings remain unchanged. The next integration is candidate-specific
kinetics and catalyst/equipment cost, using this already operable loop rather
than another standalone audit exercise.
