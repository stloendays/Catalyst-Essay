# Methanol catalyst-level count under the recycled-CO rules (item C, 2026-10-22)

Protocol: `PREREGISTRATION.md`. Script: `run_co_rule_catalyst.py` (`MEOH_FIELD_SET=combined`, `INV_WORKERS=6`; the
laboratory part takes seconds, each conversion-raised rule ~12 min). Outputs: `summary.json`, `groups_raised_<rule>.csv`,
`raised_<rule>.csv` (per-point cost with more catalyst loaded), `raised_points.csv`.

Gates: central at 6.86 % from `entry_costs.csv` equals `cost_recycled_opt_inlet` (3.4e-10) and gives 26/63 (19 > 5 %);
the frozen conversion-raised column gives 21/63 (10 > 5 %); `raised()` reproduces the frozen cost_f0.95 to print precision
on a test set. 233 of the 699 pooled entries are Cu-based (rule `Cu(?![a-z])` on the catalyst name).

## Result (6.86 % inlet limit, 63 comparisons with ≥ 2 catalysts, 46 papers)

| x_CO rule | laboratory conversion | > 5 % | 95 % CI | more catalyst loaded (f = 0.95) | > 5 % | 95 % CI | strict identity, loaded |
|---|---:|---:|---|---:|---:|---|---:|
| central (manuscript) | **26** | 19 | 29–53 % | **21** | 10 | 22–46 % | 18/52 |
| equal_X | 31 | 19 | 35–61 % | 27 | 14 | 31–55 % | 21/52 |
| high (CO-hydrogenation equilibrium) | 28 | 15 | 29–58 % | 28 | 11 | 32–56 % | 21/52 |
| family (Cu-based high, others central) | 28 | 17 | 29–58 % | 26 | 9 | 29–53 % | 20/52 |

Laboratory conversion across limits (central / equal_X / high / family): none 16/14/14/16; 5 % 28/33/32/28 (of 62);
8 % 25/25/28/27; 10 % 23/23/24/22; 15 % 22/17/18/21.

## Reading

The manuscript's rule, the lower end of the thermodynamic window, gives the smallest catalyst-level count of the four rules,
with more catalyst loaded and at laboratory conversion.
