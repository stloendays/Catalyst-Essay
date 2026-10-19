### C1, first order at the upstream leader's optimum (primary)

| Set | n | inverted | TP | FN | FP | TN | accuracy | always-preserve | sensitivity | specificity |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Au nominal | 4 | 0 | 0 | 0 | 0 | 4 | 1.000 | 1.000 | – | 1.000 |
| NH3 | 3 | 2 | 2 | 0 | 0 | 1 | 1.000 | 0.333 | 1.000 | 1.000 |
| MeOH S5 | 40 | 15 | 14 | 1 | 3 | 22 | 0.900 | 0.625 | 0.933 | 0.880 |
| MeOH S6 | 40 | 28 | 13 | 15 | 0 | 12 | 0.625 | 0.300 | 0.464 | 1.000 |
| Re/TiO2 | 6 | 2 | 2 | 0 | 0 | 4 | 1.000 | 0.667 | 1.000 | 1.000 |
| pooled (Au + NH3 + MeOH S5 + Re) | 53 | 19 | 18 | 1 | 3 | 31 | 0.925 | 0.642 | 0.947 | 0.912 |
| pooled (Au + NH3 + MeOH S6 + Re) | 53 | 32 | 17 | 15 | 0 | 21 | 0.717 | 0.396 | 0.531 | 1.000 |
| Au draws | 40,000 | 0 | – | – | – | – | 1.000 | – | – | – |

### C2, fixed-design Shapley (secondary)

| Set | n | inverted | TP | FN | FP | TN | accuracy | always-preserve | sensitivity | specificity |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Au nominal | 4 | 0 | 0 | 0 | 0 | 4 | 1.000 | 1.000 | – | 1.000 |
| NH3 | 3 | 2 | 2 | 0 | 0 | 1 | 1.000 | 0.333 | 1.000 | 1.000 |
| MeOH S5 | 40 | 15 | 15 | 0 | 0 | 25 | 1.000 | 0.625 | 1.000 | 1.000 |
| MeOH S6 | 40 | 28 | 7 | 21 | 0 | 12 | 0.475 | 0.300 | 0.250 | 1.000 |
| Re/TiO2 | 6 | 2 | 2 | 0 | 0 | 4 | 1.000 | 0.667 | 1.000 | 1.000 |
| pooled (Au + NH3 + MeOH S5 + Re) | 53 | 19 | 19 | 0 | 0 | 34 | 1.000 | 0.642 | 1.000 | 1.000 |
| pooled (Au + NH3 + MeOH S6 + Re) | 53 | 32 | 11 | 21 | 0 | 21 | 0.604 | 0.396 | 0.344 | 1.000 |
| Au draws | 40,000 | 0 | – | – | – | – | 1.000 | – | – | – |

### Methanol, paper-cluster bootstrap of accuracy (10,000 resamples of the 28 papers)

| Set | accuracy | 95 % CI |
|---|---:|---|
| MeOH S5 C1 | 0.900 | 0.774–0.980 |
| MeOH S5 C2 | 1.000 | 1.000–1.000 |
| MeOH S5 all pairs C1 | 0.882 | 0.847–0.960 |
| MeOH S6 C1 | 0.625 | 0.447–0.766 |
| MeOH S6 C2 | 0.475 | 0.289–0.617 |
| MeOH S6 all pairs C1 | 0.679 | 0.604–0.764 |

### Methanol, every STY-ordered within-group pair, C1 (secondary set)

| Scenario | pairs | inverted | TP | FN | FP | TN | accuracy | always-preserve |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| S5 | 1976 | 304 | 263 | 41 | 193 | 1479 | 0.882 | 0.846 |
| S6 | 1976 | 707 | 214 | 493 | 142 | 1127 | 0.679 | 0.642 |

### Regret explained (inverted cases)

| System | inverted | carrying property (cases) | carrying share of regret, median | upstream share, median | pathway-pool share of regret | C1 reproduced share | Spearman, C1 vs actual ln(C_j/C_i) |
|---|---:|---|---:|---:|---:|---:|---:|
| NH3 | 2 | metal price / loading (2) | 2.28 | -1.28 | 0.13 | 1.17 | 1.000 |
| MeOH S5 | 15 | single-pass conversion (8), selectivity CH4 (3), temperature / operating window (3), selectivity CO (1) | 1.53 | -0.18 | 1.11 | 1.75 | 0.783 |
| MeOH S6 | 28 | selectivity CO (17), single-pass conversion (6), selectivity CH4 (3), temperature / operating window (2) | 1.38 | -0.03 | 1.01 | 0.37 | 0.436 |
| Re/TiO2 | 2 | single-pass conversion (2) | 1.91 | -0.26 | 0.92 | 1.46 | 1.000 |

### Attribution by property class (exact D): mean phi as % of C_i [mean signed share of sum |phi|]

Negative favours j (the plant-cost competitor). Cases where a class is not a player count as 0.

| System / scenario / outcome | n | upstream metric | metal price / loading | temperature / operating window | single-pass conversion | selectivity CO | selectivity CH4 | selectivity CO+CH4 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Au / nominal / preserved | 4 | +70.7 [+1.00] | 0 | 0 | 0 | 0 | 0 | 0 |
| MeOH / S5 / preserved | 25 | +0.647 [+0.21] | 0 | -0.18 [-0.01] | +20.1 [+0.57] | +6.53 [-0.06] | +0.603 [+0.04] | 0 |
| MeOH / S5 / inverted | 15 | +1.49 [+0.12] | 0 | +25.9 [-0.09] | -61.8 [-0.27] | +24.8 [-0.02] | -0.683 [-0.12] | -0.155 [-0.01] |
| MeOH / S6 / preserved | 12 | +0.69 [+0.05] | 0 | +0.0282 [+0.00] | +15.4 [+0.52] | +215 [+0.24] | +3.69 [+0.11] | 0 |
| MeOH / S6 / inverted | 28 | +0.637 [+0.03] | 0 | +82.7 [-0.09] | -400 [+0.02] | +13.3 [-0.37] | +12 [-0.09] | +266 [+0.03] |
| NH3 / frozen / preserved | 1 | +0.953 [+0.06] | +15.6 [+0.90] | +0.693 [+0.04] | 0 | 0 | 0 | 0 |
| NH3 / frozen / inverted | 2 | +46.2 [+0.33] | -83.4 [-0.59] | +1.46 [-0.01] | 0 | 0 | 0 | 0 |
| Re / D01 v3, 2 % purge / preserved | 4 | +0.341 [+0.01] | -0.372 [-0.01] | 0 | -2.96 [+0.06] | -0.123 [-0.03] | +26.8 [+0.57] | 0 |
| Re / D01 v3, 2 % purge / inverted | 2 | +0.545 [+0.06] | -0.709 [-0.08] | 0 | -4.22 [-0.46] | -0.721 [-0.08] | +2.93 [+0.32] | 0 |

### Small systems, per case (phi_D in cost units; U_L + O_L in ln J)

| Case | C_i | C_j | actual | phi_D by property | U_L + O_L | C1 | C2 |
|---|---:|---:|---|---|---:|---|---|
| Au 2-3 nm | 19.505 | 42.143 | preserved | U +22.64 | +0.7704 | preserved | preserved |
| Au 3-4 nm | 42.143 | 72.797 | preserved | U +30.65 | +0.5466 | preserved | preserved |
| Au 4-5 nm | 72.797 | 111.23 | preserved | U +38.44 | +0.4240 | preserved | preserved |
| Au 5-6 nm | 111.23 | 157.28 | preserved | U +46.05 | +0.3464 | preserved | preserved |
| NH3 Ru-Os | 22.031 | 25.832 | preserved | U +0.2099; W +0.1527; M +3.439 | +0.1484 | preserved | preserved |
| NH3 Ru-Fe | 22.031 | 15.292 | inverted | U +7.986; W -2.093; M -12.63 | -0.5344 | inverted | inverted |
| NH3 Os-Fe | 25.832 | 15.292 | inverted | U +14.51; W +3.206; M -28.26 | -0.5664 | inverted | inverted |
| Re 1wtRe_250C vs 1wtRe_200C | 961.51 | 966.96 | preserved | U +0.7248; X +20.74; CO -4.668; CH4 -11.34 | +0.0038 | preserved | preserved |
| Re 1wtRe_250C vs 5wtRe_200C | 961.51 | 943.3 | inverted | U +5.508; L -6.728; X -30.47; CO -9.283; CH4 +22.77 | -0.0248 | inverted | inverted |
| Re 1wtRe_250C vs 5wtRe_250C | 961.51 | 1258.2 | preserved | U +6.259; L -7.064; X -48.69; CO -7.492; CH4 +353.6 | +0.2224 | preserved | preserved |
| Re 1wtRe_200C vs 5wtRe_200C | 966.96 | 943.3 | inverted | U +5.008; L -6.952; X -50.96; CO -4.612; CH4 +33.86 | -0.0394 | inverted | inverted |
| Re 1wtRe_200C vs 5wtRe_250C | 966.96 | 1258.2 | preserved | U +5.759; L -7.289; X -71.93; CH4 +364.7 | +0.1983 | preserved | preserved |
| Re 5wtRe_200C vs 5wtRe_250C | 943.3 | 1258.2 | preserved | U +0.4141; X -14.04; CO +7.304; CH4 +321.2 | +0.2548 | preserved | preserved |
