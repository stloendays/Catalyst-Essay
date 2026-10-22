# Methanol catalyst-level count under the recycled-CO rules — preregistration (2026-10-22)

Committed before any count of this folder is made; every count below is reported whatever its direction.

## Question

The manuscript's methanol headline is catalyst-level: 21 of 63 comparisons with more catalyst loaded (conversion raised
to 0.95 X_eq) and 26 of 63 at laboratory conversion, inlet CO + CH₄ + N₂ ≤ 6.86 %, recycled CO converted per pass at the
lower end of its thermodynamic window (`x_co = recycled_central`). The point-level result was tested against the other
two rules (`analysis/meoh_field_pooled_2026_10_15/robustness/co_conversion_bound`); the catalyst-level count was not.

## Rules

| Tag | x_CO | Source |
|---|---|---|
| central | lower end of the window (frozen) | `meoh_general_model.resolve_x_co('recycled_central')` |
| equal_X | x_CO = X, clipped into the window | `'recycled_equal_X'` |
| high | CO-hydrogenation equilibrium (upper end) | `'recycled_high'` |
| family | high for Cu-based catalysts, central otherwise | fixed here: a catalyst is Cu-based when its name contains the element symbol Cu (regex `Cu(?![a-z])`); Cu/ZnO-type catalysts convert CO readily, In₂O₃- and ZrO₂-type oxides much less |

## Counts

- Laboratory conversion: entry costs `cost_<rule>_<limit>` of `robustness/co_conversion_bound/entry_costs.csv`
  (limits none, 5, 6.86, 8, 10, 15 %), catalyst identity and leaders exactly as
  `analysis/meoh_catalyst_level_2026_10_19/run_catalyst_level.py` (`identities`, `catalyst_table`, `compare`, `brief`,
  imported unchanged), primary and strict identity.
- More catalyst loaded (f = 0.95), 6.86 % limit: `analysis/verify_2026_10_12_s6_conversion/run_s6_conversion.evaluate`
  with `run_conversion_sensitivity.KW_RULE['x_co']` set to the rule; same states, purge grid, admission test.

Reported for each: comparisons with ≥ 2 catalysts, leader is another catalyst, > 5 %, papers, paper-bootstrap CI.

## Gates

1. central at 6.86 % from `entry_costs.csv` equals `cost_recycled_opt_inlet` and reproduces 26/63 (19 > 5 %).
2. The conversion-raised run under central reproduces 21/63 (10 > 5 %).
