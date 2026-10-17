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

## 2026-10-13 extension: physical-closure risk and falsification QA

The measured-kinetics job now reruns `audit_domain.py`, with an eight-variant
fit-support table in `source_domain.csv` and `source_domain.json`, and an
interpretation in `SOURCE_DOMAIN.md`. Reconcile consumes that report, displays
its key findings in the Actions job summary, and archives all artifacts.

**Source-range issue:** Rossetti 2006 Ru/C kinetics were fitted on 50-100 bar
data and the original **3.2 wt%** Ru/C formulation. The present supported
8 wt% Ru/C cost assumes unchanged activity per kg Ru. The 0% financing
supported optimum is outside 50-100 bar in **6/8** kinetics variants; at
12%/year all **8/8** optima exceed the fit. The optimal measured Fe case may
also fall below its cited 150-300 atm fit reference. The pressure-window
cost comparison is descriptive of the loss-only recovery basis, and cannot
be transferred automatically to the 25-year DCF cases.

**Thermodynamic convention issue:** At 425 C / 90 bar, GB ideal-gas
equilibrium predicts yNH3=0.1764, but the same GB standard equilibrium using
Newton-Cooper fugacity coefficients yields yNH3=0.1887 (**+1.22 percentage
points**). At 145 bar this gap is **+2.29 pp**, and at 325 bar **+5.66 pp**.
PR #75's plant-state gas standard reference and its measured kinetic rate
are thus not a fully nonideal-gas-closed optimization, despite using the
same GB standard equilibrium constant. These are warnings, not an
independently corrected reactor/industrial estimate.

**Numerical versus scientific tests:** The revised `reconcile.py` verifies
frozen costs, the entire 15-metal numeric order against metal records,
inversion flags against computed rankings, cashflow cost-gap arithmetic,
and fit-domain source anchors. It does NOT require that the new science
preserve the old sign. `test_reconcile.py` explicitly generates a
counterfactual reversal of the NIST result: coherent changed rankings must
PASS; a stale reversal flag or an incorrect DCF cost gap must FAIL. That
counterfactual is a software test, not a new scientific result.

The Actions guard compares frozen manuscript/source/data files to
`origin/main` as well as the clean working tree, avoiding the mistaken
assumption that `git diff` alone catches committed changes in a PR.

**Current decision:** Continue to leave PR #77 as Draft. The model is
numerically reproducible but physically unresolved for EOS/kinetic closure,
pressure fitting and reactor/bed validity. The most important next
scientific task is a source-consistent fugacity/loop-state reformulation
and independent pressure-domain/held-out validation before any canonical
NH3-FINAL-1.2 or manuscript change.
