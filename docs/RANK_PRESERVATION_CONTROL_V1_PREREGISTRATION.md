# Rank-Preservation Control V1 — Preregistration

Status: **frozen design before downstream ranking calculation**  
Reaction: `CO + 1/2 O2 -> CO2`  
Catalyst family: **Au/TiO2 particle-size states**

## Scientific question

When the catalyst-controlled variable maps approximately monotonically into required catalyst inventory and reactor burden, does the multiscale framework preserve the upstream catalytic ranking rather than create an artificial inversion?

## Hypothesis

For a fixed-condition Au/TiO2 CO-oxidation benchmark, smaller Au particles in the frozen 2–6 nm interval have higher literature-anchored intrinsic activity. Because all candidates share the same active element, support, pricing basis, feed condition and process topology, higher productivity should require less catalyst inventory and lower catalyst-dependent economic burden.

The preregistered expectation is therefore **rank preservation**.

## Candidate states

The candidate set is frozen as:

- `AuTiO2_d2` — 2 nm
- `AuTiO2_d3` — 3 nm
- `AuTiO2_d4` — 4 nm
- `AuTiO2_d5` — 5 nm
- `AuTiO2_d6` — 6 nm

No candidate may be removed or added after downstream results are generated.

## Upstream metric

Nominal intrinsic activity proxy:

`TOF_rel(d) = (d / 2)^(-1.7)`

The value is dimensionless and normalized to the 2 nm state. It is derived from the primary literature trend and is not an invented absolute TOF.

For catalyst-mass demand, a spherical-particle dispersion factor is used:

`dispersion_rel(d) = (d / 2)^(-1)`

so that relative mass-specific productivity is:

`q_mass_rel(d) = TOF_rel(d) * dispersion_rel(d)`

The exact dispersion prefactor cancels because only relative inventory and ranking are evaluated.

## Fixed process boundary

The control is intentionally a fixed-condition benchmark rather than a candidate-specific process optimization.

Frozen assumptions:

- temperature: externally fixed at the common literature anchor condition;
- pressure: externally fixed and identical for all candidates;
- feed composition: identical for all candidates;
- treatment duty / conversion target: identical for all candidates;
- no recycle-loop redesign;
- no candidate-dependent separation topology;
- no candidate-dependent heating or compression severity;
- same Au unit-price basis for every candidate;
- same TiO2 support-price basis for every candidate;
- same catalyst lifetime and recovery assumptions for every candidate.

This fixed boundary is part of the control definition. It must not be relaxed after results are observed.

## Downstream mapping

Required relative catalyst inventory:

`M_rel = 1 / q_mass_rel`

The catalyst-dependent economic index is:

`C_rel = C_common + a*M_rel + b*M_rel^gamma`

with:

- `a > 0` representing catalyst/support inventory and replacement burden;
- `b > 0` representing reactor/washcoat/volume burden;
- `0 < gamma <= 1` allowing sublinear equipment scaling;
- `C_common >= 0` representing common process cost that does not affect ranking.

No negative coefficient or candidate-specific price multiplier is allowed.

## Uncertainty propagation

Primary uncertainty is the common-series activity exponent:

`n ~ Normal(1.7, 0.2)` truncated to `n > 0`.

Additional structural uncertainty in the dispersion exponent is allowed as:

`m ~ Uniform(0.8, 1.2)`

with `dispersion_rel ~ d^(-m)`.

Economic coefficients are sampled only from positive ranges. These uncertainties test robustness without introducing a new competing pathway that is absent from the control hypothesis.

Secondary diagnostics may evaluate the independently reported alternative slopes near `0.9 +/- 0.2` and `1.8`, but they must not alter the nominal preregistered result.

## Preregistered criteria

The control is considered rank-preserving only if all of the following hold under the nominal model:

- **C1 — Winner preservation:** highest intrinsic-activity state is also the lowest catalyst-dependent economic-burden state.
- **C2 — Full-set Spearman:** `rho >= 0.95` between activity rank and inverse economic-burden rank.
- **C3 — Kendall:** `tau >= 0.90`.
- **C4 — Pairwise inversions:** zero pairwise inversions across the five candidates.
- **C5 — Top-3 preservation:** exact Top-3 membership and order are preserved.
- **C6 — Uncertainty robustness:** at least 95% of preregistered Monte Carlo draws preserve the complete rank.

## Failure rule

If any criterion fails, the result is reported as a failed rank-preservation control. The catalyst set, activity relation, process boundary, cost equation or thresholds must not be modified to recover the expected result.

## Outputs

The frozen runner must produce:

- upstream relative activity and mass-specific productivity table;
- downstream relative inventory and economic-burden table;
- Spearman rho and Kendall tau;
- pairwise inversion count;
- Top-3 preservation result;
- Monte Carlo full-rank preservation probability;
- sensitivity result for the two independent literature slope regimes;
- a compact machine-readable CSV and Markdown report.

No absolute USD/t result will be reported from this control unless a separately validated application-scale process model is added in a future version.
