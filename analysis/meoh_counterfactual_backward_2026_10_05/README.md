# Methanol — counterfactual and backward design (2026-10-05)

The two steps of the common protocol (upstream ranking → per-candidate process → cost → counterfactual → backward
design) that the ammonia case already has, applied to the four Re/TiO₂ states with the methanol recycle-economics
model (`data/meoh/meoh_d01_model.py`, Table 3 inputs, canonical 2 % purge and cost parameters).

    python meoh_counterfactual_backward.py   -> counterfactual_ranks.csv, backward_targets.csv, summary.json

## Counterfactuals

| case | economic order | ρ vs STY per g Re | τ |
|---|---|---:|---:|
| canonical (Table 3) | 5%-200 > 1%-250 > 1%-200 > 5%-250 | +0.40 | +0.33 |
| CH₄ selectivity removed (moved to MeOH) | 5%-250 > 5%-200 > 1%-250 > 1%-200 | −0.80 | −0.67 |
| conversion equalized (X = 0.2875) | 1%-200 > 1%-250 > 5%-200 > 5%-250 | +0.80 | +0.67 |
| CH₄ removed and conversion equalized | 5%-200 > 5%-250 > 1%-200 > 1%-250 | −0.80 | −0.67 |

- Removing the selectivity difference makes the highest-conversion state (5 wt% Re, 250 °C) the economic optimum:
  CH₄ selectivity is what keeps it last.
- Equalizing conversion brings the economic order close to the STY order (ρ +0.80): the conversion difference is what
  lifts the 5 wt% Re states above the per-Re STY winner.
- With both removed, the remaining spread follows catalyst mass per tonne of product (STY per g catalyst) and CO-like
  selectivity, not STY per g Re.

## Backward design for the STY winner (1 wt% Re, 250 °C → parity with 5 wt% Re, 200 °C at 943.30 EUR/t)

| property changed alone | current | required for parity |
|---|---:|---|
| STY per g Re (multiplier) | 65 | unreachable: unlimited STY gives 954.64 EUR/t |
| single-pass CO₂ conversion | 0.23 | 0.281 (the same study measures 0.19–0.40 on these catalysts) |
| CH₄ selectivity → 0 | 0.01 | not sufficient alone (950.18 EUR/t) |
| CO-like selectivity → 0 | 0.02 | not sufficient alone (952.29 EUR/t) |
| methanol selectivity → 100 % | 0.97 | sufficient (941.27 EUR/t) |
| CH₄ → 0 and CO-like reduced | 0.02 | CO-like ≤ 0.46 % |

Productivity per gram of Re cannot close the gap at any value, whereas a conversion gain inside the measured range of
the same catalyst family, or complete methanol selectivity, does. This is the methanol analogue of the ammonia result
that intrinsic activity cannot reach parity while metal economy can.
