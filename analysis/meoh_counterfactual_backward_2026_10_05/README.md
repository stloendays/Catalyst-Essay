# Methanol — counterfactual and backward design (2026-10-05)

The two steps of the common protocol (upstream ranking → per-candidate process → cost → counterfactual → backward
design) that the ammonia case already has, applied to the four Re/TiO₂ states with the methanol recycle-economics
model (`data/meoh/meoh_d01_model.py`, Table 3 inputs, canonical 2 % purge and cost parameters).

    python meoh_counterfactual_backward.py   -> counterfactual_ranks.csv, backward_targets.csv, summary.json

## Counterfactuals

| case | economic order | ρ vs STY per g Re | τ |
|---|---|---:|---:|
| canonical (Table 3) | 5%-200 > 1%-250 > 1%-200 > 5%-250 | +0.40 | +0.33 |
| CH₄ selectivity removed (moved to MeOH) | 5%-250 > 5%-200 > 1%-250 > 1%-200 | −0.60 | −0.33 |
| conversion equalized (X = 0.2875) | 1%-200 > 1%-250 > 5%-200 > 5%-250 | +1.00 | +1.00 |
| CH₄ removed and conversion equalized | 5%-200 > 1%-200 > 5%-250 > 1%-250 | 0.00 | 0.00 |

STY follows every change of conversion or selectivity (STY ∝ X·S_MeOH at fixed feed, as in the measurement Monte
Carlo; 2026-10-07). With STY held fixed the three rows read −0.80, +0.80 and −0.80.

- Removing the selectivity difference makes the highest-conversion state (5 wt% Re, 250 °C) the economic optimum:
  CH₄ selectivity is what keeps it last.
- Equalizing conversion makes the economic order the STY order (ρ +1.00): the conversion difference is what lifts the
  5 wt% Re states above the per-Re STY winner.
- With both removed, the economic order is unrelated to STY per g Re (ρ 0.00).

## Backward design for the STY winner (1 wt% Re, 250 °C → parity with 5 wt% Re, 200 °C at 943.30 EUR/t)

| property changed alone | current | required for parity |
|---|---:|---|
| STY per g Re (multiplier) | 65 | unreachable: unlimited STY gives 954.64 EUR/t |
| single-pass CO₂ conversion | 0.23 | 0.2785 (the same study measures 0.19–0.40 on these catalysts) |
| CH₄ selectivity → 0 | 0.01 | not sufficient alone (950.14 EUR/t) |
| CO-like selectivity → 0 | 0.02 | not sufficient alone (952.21 EUR/t) |
| methanol selectivity → 100 % | 0.97 | sufficient (941.15 EUR/t) |
| CH₄ → 0 and CO-like reduced | 0.02 | CO-like ≤ 0.49 % |

With STY scaled by X·S (2026-10-07); with STY held fixed the targets were 0.281, 950.18, 952.29, 941.27 and 0.46 %.

Productivity per gram of Re cannot close the gap at any value, whereas a conversion gain inside the measured range of
the same catalyst family, or complete methanol selectivity, does. This is the methanol analogue of the ammonia result
that intrinsic activity cannot reach parity while metal economy can.
