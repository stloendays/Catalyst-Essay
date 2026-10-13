# Staged Fe → Ru/C converter: feasibility with the frozen NH₃ model

Question: industrial KAAP converters put fused iron in the first bed and promoted Ru/C downstream (Tripodi et al. 2018,
doi:10.1016/j.jiec.2018.05.027; RSC Sustain. Energy Fuels 2024, doi:10.1039/D4SE00254G). Can the frozen NH3-FINAL-1.1
model represent that arrangement and does it place Ru downstream? Diagnostic only; no frozen value or manuscript number
changes.

## Result

1. **The frozen kinetics can be integrated along the bed** (`Condition.logtof` accepts any T, p_N₂, p_H₂, p_NH₃), so a
   staged converter is computable. The frozen harness itself sizes each bed from the inlet rate.
2. **They place Ru upstream, not downstream.** The Ru/Fe rate ratio falls from 22 at the inlet to 4.3 at the outlet of the
   KAAP loop (90 bar, −20 °C separator, 425 °C). The cheapest staging puts Ru first for 18.5% of the NH₃ made per pass,
   then Fe (19.058 against 19.069 US dollars per tonne for Fe alone); Fe first, Ru last never beats Fe alone. Same pattern
   at 150 and 200 bar.
3. **Why:** the apparent orders of the frozen microkinetics at 90 bar, 400–425 °C, 2% NH₃ are Fe N₂ −0.3 to −0.4,
   H₂ +2.3, NH₃ −0.4 to −0.5, and Ru N₂ +1.0, H₂ +2.5 to +2.6, NH₃ −2.0 to −2.1. Measured promoted Ru has a negative H₂
   order and a weak NH₃ order, fused Fe a strong NH₃ inhibition (Temkin–Pyzhev, NH₃ order about −1). The single-descriptor
   scaling model makes Ru the NH₃-inhibited metal, the reverse of experiment, so it cannot reproduce the reason Ru sits
   downstream.
4. **Plug-flow sizing moves the KAAP comparison.** Integrated over the bed, Ru needs 9.3 times its inlet-rate mass at
   425 °C, Fe 2.5 times. Pure Ru/C (8 wt%, 490 kg m⁻³, 95.55% recovery, u = 11) then costs 19.85 against 19.07 for Fe in
   the KAAP loop, where the inlet-rate sizing of the paper gives 18.67–19.08 on its own bed.
5. **Equilibrium offset in the plant loop.** The model's NH₃ formation free energy is 6.2–6.3 kJ mol⁻¹ (0.064 eV) above
   the Gillespie–Beattie value at 400–450 °C, as the Methods state for the laboratory mapping; in the plant states it
   puts the 90-bar equilibrium NH₃ fraction at 7.5% against 17.6% at 425 °C. It applies to every metal.

## Consequence for the work item

A staged-converter result cannot come from the frozen descriptor kinetics: it would need measured rate expressions for
fused Fe and promoted Ru/C (e.g. Temkin–Pyzhev for Fe; the Ru kinetics of Tripodi et al. 2018 or the 2024 RSC study),
which is a new model rather than an extension of the frozen one. Points 4 and 5 bear on the KAAP parity statement and on
the absolute loop costs; neither changes the main-loop Fe optimum or the direction Fe ahead of Ru.

    NH3_HARNESS=<harness root> python analysis/verify_2026_10_12_hybrid_bed/hybrid_bed_feasibility.py
