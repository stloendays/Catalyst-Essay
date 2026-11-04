# NH3 thermochemical-reference and economic-ranking audit (UNFROZEN)

**Status: independent scientific diagnostic, not an amendment to NH3-FINAL-1.1.**
The analysis runs on GitHub Actions. Do not merge it into canonical numbers or the manuscript without author/supervisor review.

## Question

Exploratory PR #64 and corrected PR #68 indicate a 90-bar, 425-C, stoichiometric-inlet equilibrium discrepancy:
approximately 7.53% NH3 from the frozen descriptor representation versus
17.64% from Gillespie-Beattie and 18.57% from NIST Shomate (ideal reference).
Does this difference alter the Fe/Ru/Os economic ranking or the direct Ru activity parity target?

## Reproducible scenarios

1. **Frozen**: exact unchanged NH3-FINAL-1.1 harness, manifest, workbook and gas-phase free energy.
2. **NIST**: re-reference ONLY standard NH3 gas chemical potential so that reaction Gibbs formation energy matches NIST 1-bar Shomate at each process temperature.
3. **GB**: re-reference ONLY NH3 gas chemical potential to match Gillespie-Beattie half-reaction K as documented in corrected PR #68.

The same gas Gibbs-energy function feeds BOTH the equilibrium process solver and the MKM condition object.
Changing only equilibrium Kp, or only the microkinetic NH3 adsorption term, would create a thermodynamic inconsistency.
All other gas species, adsorbate and transition-state energetic parameters, economics, metal prices, reactor options,
and original descriptor vectors remain unchanged. This one-degree-of-freedom shift is explicitly a **model-form sensitivity**,
not a completely re-fitted kinetic model or experimentally established industrial reference.

For each case the unchanged harness rebuilds the permitted temperature/pressure/separator states and re-evaluates
all 15 metals by exact two-column descriptor interpolation. The ORIGINAL frozen count must be 14,136; thermochemical
scenarios may change the number of thermodynamically eligible states, which is recorded rather than hidden.
All cost minima are optimized independently subject to the same 90 m3 bed cap.

**Frozen regressions:** pin SHA-256 of Wang S1; exactly 14,136 frozen states; all 15 baseline activity ranks;
Fe/Ru/Os economic costs within 2e-7 USD/t, and Ru direct-activity parity within 0.03 times the 201.223x baseline.
If the frozen regression fails, the sensitivity audit cannot be trusted. Modified modes are never forced to match.

## Outputs

The GitHub Actions job uploads a 90-day artifact containing:

- results/summary.json: scenario physics, all 15 metal costs, atomic/economic rankings, feasible states, optima,
  Fe–Ru gap and activity-parity target.
- results/catalyst_costs.csv: per-metal per-mode rankings and optimum states.
- results/thermo_reference.csv: original/NIST/GB ideal equilibrium checks at 350-450 C.
- results/audit_summary.md: machine-generated review table for the PR and Actions job summary.

The workflow starts automatically when the draft pull request is opened.
It may also be dispatched manually from GitHub Actions on this branch.
CI PASS checks numerical reproducibility only, not scientific publication readiness.

## Explicit limitations

- Zero recovered Ru in the baseline, and NO deferred metal-financing overlay. Recovery remains an OPTIONAL separate scenario.
- The independent 90-bar equilibria are ideal-gas references, not a calibrated mixture EOS.
- Gas-phase Gibbs re-referencing is NOT a full transition-state/MKM re-fit or measured catalyst-specific rate law.
- The process model is algebraic approach-to-equilibrium, not a validated axial nonisothermal plant converter.
- The published PR #68 Ru/CeO2 fitted kinetic law is NOT the industrial promoted Ru/C found in KAAP.
- A changed economic order requires a separately approved, end-to-end NH3-FINAL-1.2 reconstruction,
  including MC, strict scaling headroom, alloy screening and figures.
- A preserved order proves robustness only to the named one-parameter thermo perturbations,
  NOT to untested kinetic, hydraulic, financial or operating-condition changes.

## Reproduce in GitHub Actions

GitHub Actions -> NH3 thermochemical reference robustness (unfrozen) -> Run workflow.
No new private source downloads and no local compute environment are required.
