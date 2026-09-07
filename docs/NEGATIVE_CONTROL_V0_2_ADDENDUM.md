# NEGATIVE CONTROL V0.2 — addendum to the V0.1 pre-registration (2026-09-07)

Status of V0.1: frozen and executed as registered (`NEGATIVE_CONTROL_V0_1_FROZEN.json`); its results are kept.

## Why a V0.2 exists
After freezing V0.1 and before reading any economic output, the atomic activity ranking at the reference condition
(450 °C, 10 bar, 1500 ppmv N2O, 3 % O2) was compared with the experimental metal order for direct N2O decomposition
(Rh > Ir ≈ Ru > Pd > Pt > Ni > Cu > Ag > Au; Kapteijn et al. 1996 and later summaries). V0.1 places the volcano peak at
Pd / Cu / Pt and ranks Rh sixth, below Ag (Spearman vs experimental order −0.10): the linear mean-field O–O repulsion of
1.0 eV/ML leaves Rh/Ir/Ru fully O-covered under 3 % O2. A scan over eps ∈ {1.0, 1.5, 2.0, 2.5, 3.0} eV/ML and four BEP slopes
showed that eps = 1.5 eV/ML with the V0.1 BEP (a1 = 0.30, b1 = 1.60) is the only setting that reproduces the experimental
order at the top (Rh ≈ Ir first; Pd > Pt; Ag, Au last; Spearman 0.75) without unpoisoning the early transition metals
(eps ≥ 2 pushes W / Mo / Re / Fe to the top, which contradicts their bulk oxidation).

## What changes
`configs/n2o_negcontrol_v0_2.yaml` = V0.1 manifest with `kinetics.lateral_interaction.eps_eV_per_ML: 1.0 -> 1.5` and
`model_version: N2O-NEGCTRL-0.2`. Descriptor values, BEP parameters, prefactors, grids, engineering and economic constants,
uncertainty model and the six rank-preservation criteria are byte-identical to V0.1.

## What does not change
The hypothesis, the criteria and the pass rule of the V0.1 pre-registration. Both versions are run and reported side by side;
V0.2 is the version whose atomic ranking is literature-consistent and is therefore the one proposed for the manuscript, with
V0.1 kept as the record of the first parameterization.
