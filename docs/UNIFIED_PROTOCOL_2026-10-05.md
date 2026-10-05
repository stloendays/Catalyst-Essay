# One protocol across the three systems (2026-10-05)

Every system is taken through the same five steps: upstream ranking → per-candidate process treatment → cost →
counterfactual → backward design, followed by uncertainty. This page records what each system does at each step and,
where a step cannot take the same form, why.

| step | Ammonia (15 metals) | Methanol (4 Re/TiO₂ states) | Au/TiO₂ control (5 sizes) |
|---|---|---|---|
| 1 upstream ranking | DFT descriptor E_N → microkinetic TOF at 673 K | measured STY per g Re (Gothe et al. 2025, Table 3) | literature size–activity relation (Janssens 2006 anchor, Overbury 2006 exponent) |
| 2 per-candidate process | T, P and T_sep reoptimized over 14,136 states | purge reoptimized per state (0.5–40 %, 396 levels); T and P at the measured points | common fixed condition; semi-open extension reoptimizes T and O₂/CO per size |
| 3 cost | catalyst-dependent cost, seven pools (USD/t NH₃) | net production cost, near-full plant (EUR/t MeOH) | required catalyst burden (∝ catalyst mass) |
| 4 counterfactual | Ru priced as Fe → Ru 14.712 < Fe 15.292: order reverses | CH₄ selectivity removed → ρ −0.80; conversion equalized → ρ +0.80 | none: the order is preserved, so there is no inversion to explain |
| 5 backward design | activity alone: α* = 201× vs 2.525× reachable; actual catalyst cost: Ru/C + recovery within 0.19–0.38 USD/t (Fig. 2d) | STY alone: unreachable at any value; conversion 0.23 → 0.281 or 100 % MeOH selectivity reaches parity | the 6 nm state needs 8.064× its activity to match 2 nm, equal to the activity ratio |
| uncertainty | 1,000 descriptor draws; 5,000 joint cost draws | 5,000 draws of each state's own measurement uncertainty | 10,000 literature-envelope draws; semi-open extension |

## Where the steps differ, and why

- **Upstream data.** Ammonia starts from DFT energetics for every metal; methanol and Au start from measured or
  literature-calibrated activities. The protocol is the same from step 2 on; the upstream layer is whatever the
  reaction's catalyst literature provides.
- **Process degrees of freedom.** Methanol has no temperature–pressure kinetic model for these catalysts, so only the
  loop variable (purge) is reoptimized per state; ammonia reoptimizes T, P and T_sep because its kinetics are
  descriptor-based. Each reoptimizes every degree of freedom its model exposes.
- **Au/TiO₂ is a control.** Under a common monotonic mapping the burden is the inverse of activity, so rank
  preservation and the 8.064× backward target follow from the mapping itself. The control demonstrates that the
  framework does not create inversions by construction; its 10,000/10,000 result is a property of the mapping and is
  reported as a control, not as evidence about Au catalysts. The semi-open extension, which lets each size take its
  own operating point, is where the control can change order (92.16 % exact preservation, moderate freedom, 273–293 K).
- **Counterfactual form.** Each counterfactual removes the candidate difference that drives that system's cost
  pathway: metal price in ammonia, selectivity or conversion in methanol.

## Sources

`docs/SOURCE_OF_TRUTH_2026-09-29.md`, `figures/composite/fig2/fig2_ru_actual_cost_points.csv`,
`analysis/meoh_counterfactual_backward_2026_10_05/`, `analysis/meoh_measurement_mc_2026_10_05/`,
`data/meoh/meoh_purge_robustness_D01v3_summary.json`, `controls/au_tio2_rank_preservation_v1_1_config.json`.
