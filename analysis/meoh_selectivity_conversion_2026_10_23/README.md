# Methanol: selectivity that moves with conversion when catalyst is loaded (item E, 2026-10-23)

Protocol: `PREREGISTRATION.md`. Script: `run_selectivity_conversion.py` (`MEOH_FIELD_SET=combined`, `INV_WORKERS=6`,
~55 min). Outputs: `summary.json`, `groups_<model>.csv`, `raised_points.csv`, `s_eq.csv`, `slopes.csv`.

Gates: the constant model reproduces the frozen cost_f0.95 of every point (5.0e-10) and 21/63 (10 > 5 %); the equilibrium
conversion of the split solver equals the frozen X_eq for every feed; every equilibrium split lies in [0, 1].

Evidence on the direction (`slopes.csv`): 23 sets in 9 papers measured one catalyst at several space velocities; methanol
selectivity falls with conversion in 21 (dS_MeOH/dX quartiles −2.65, −0.93, −0.065).

## Result (63 comparisons with ≥ 2 catalysts, more catalyst loaded to ≤ 0.95 X_eq, 6.86 % inlet limit)

| Selectivity in a raised state | Laboratory leader ≠ plant leader | > 5 % | 95 % CI |
|---|---:|---:|---|
| constant (manuscript) | **21** | 10 | 22–46 % |
| methanol/CO split moving to the equilibrium split | 23 | 9 | 23–52 % |
| median slope (−0.93) | 18 | 9 | 18–40 % |
| lower-quartile slope (−2.65) | 22 | 8 | 23–48 % |
| upper-quartile slope (−0.065) | 20 | 10 | 20–44 % |

The count stays at 18–23 of 63 (8–10 above 5 %). At laboratory conversion, where no extrapolation is made, it is 26 of 63.
