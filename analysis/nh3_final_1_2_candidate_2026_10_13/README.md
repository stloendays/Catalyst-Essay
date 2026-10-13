# NH3-FINAL-1.2 candidate | author review required

This branch is **not** NH3-FINAL-1.2 adoption. It builds on draft PR #75 and
imports the exact independent thermochemistry files from PR #72. No original
manuscript, figure, workbook, frozen traces or NH3-FINAL-1.1 methods are edited.

## Model matrix
| Scenario | Gas equilibrium and MKM reference | Rate law | Candidate cohort | Claim |
|---|---|---|---|---|
| Original | frozen | original descriptor MKM | 15 metals | baseline regression |
| NIST | NIST Shomate Gibbs referencing | original descriptor MKM | 15 metals | thermo sensitivity |
| GB descriptor | Gillespie-Beattie Gibbs referencing | original descriptor MKM | 15 metals | thermo sensitivity |
| GB measured | GB/ Newton-Cooper rate-law convention | Dyson-Simon Fe and Rossetti Ru/C | Fe/Ru only | kinetic + economics robustness |

The measured-pair rates and gas-equilibrium references are not
interchangeable without equilibrium-consistent refitting. PR #75's extra
'frozen process states + measured kinetics' variants are **stress tests**,
not publication-grade physical kinetic/thermodynamic closure.

## Reproduction
The new GitHub Actions workflow `.github/workflows/nh3-final-1-2-audit.yml`
executes two independent optimization jobs in parallel and reconciles their
JSON outputs in a third job. It checks the Wang/S1 hash, baseline pure metal
regression, all 15 atomistic and economic rankings, Fe/Ru reported gap,
all eight measured Fe/Ru kinetics sensitivity scenarios, recovery and
financing sign, and absence of changes to frozen code or manuscript.

It uploads the machine-readable thermo, pair-kinetics and combined CSV/MD
comparison as separate 90-day artifacts. The combined report explicitly
flags uncertainty, model limits and publication gates.

## What is NOT automatically established
- Exact 15-metal economic ranks under measured kinetic laws: only Fe and
  Ru have experimentally parameterized rates in the present PR.
- An experimentally validated and internally refitted DFT/MKM reference:
  NIST and GB descriptor variants shift a single gas chemical potential.
- A calibrated axial plant, pressure drop, heat transfer or supported-bed
  finance from the same reactor design.
- Rebuilt scaling-restricted headroom, uncertainty ensembles, alloy screens
  and main manuscript figures under one approved model.
- Permission to describe the 201.2x parity as robust across kinetic models.

## Promotion decision
Only after author and supervisor source/physics checks should a separate
NH3-FINAL-1.2 publication branch rebuild all dependencies in order:
kinetic-thermodynamic reference -> 15-metal cost and feasible states ->
backward scaling reachability -> Ru/C and DCF -> uncertainty -> alloys ->
main manuscript / figure / source data / SI. Keep these audit outputs
isolated until those steps pass.
