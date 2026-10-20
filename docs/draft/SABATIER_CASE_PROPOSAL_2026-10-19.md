<!-- DRAFT PROPOSAL, not manuscript text. Drafted 2026-10-19 from analysis/sabatier_ru_ni_2026_10_19/RESULTS.md.
Nothing here edits docs/MANUSCRIPT_MAIN_TEXT.md or docs/SUPPLEMENTARY_INFORMATION.md. Every number is taken from
results/summary.json and results/*.csv of that analysis directory and is asserted in CI. -->

# Proposal: an external Sabatier Ru vs Ni case under the three-tier framing

## What the case adds

The manuscript's three cases each occupy one segment of the atomic → laboratory → industrial chain (Fig. 1a):
ammonia from the atomic to the industrial optimum (price channel active, ranking inverts), methanol from the laboratory
to the industrial optimum (selectivity channel active, ranking inverts) and Au/TiO₂ from the laboratory optimum to the
catalyst requirement (no channel, ranking preserved). All three are computed in-house. The Sabatier case is different in
two ways that strengthen the argument rather than repeat it:

1. **It is external.** Moioli & Züttel (*Sustainable Energy Fuels* 2020, 4, 1396) built their own reactor model, found
   that Ru/Al₂O₃ reaches 99.5 % conversion in one stage while Ni/Al₂O₃ needs 1.89× the catalyst volume plus an
   intermediate water-condensation stage, costed the Ru bed at ≈2.5× the Ni bed, and concluded that Ru is the reference
   catalyst for small-scale SNG while a Ni system suits large scale. None of that used this paper's harness.
2. **It is the ammonia decision structure with the opposite outcome.** Expensive, more active Ru against cheap, less active
   Ni; the catalyst price penalty per kilogram (Π = 5.2) exceeds the inventory advantage (r_V = 1.89), exactly as in ammonia
   where Ru is 607× more active and 6,732× more expensive. On inventory alone Ni wins at every scale, as Fe does. Ru keeps its
   rank at small scale only because the cheap metal forces a second reactive stage with condensation, and that
   process-topology penalty has a fixed-cost component that does not shrink with throughput. The decision therefore
   depends on scale, and the boundary is an explicit inequality:

       Ru cheaper  ⇔  r_V · (1 + φ_proc(S)) > Π

   with φ_proc the Ni process penalty per unit of Ni catalyst cost (9.1 at 0.1 MW, 0.04 at 100 MW).

This gives the paper a fourth observed outcome: **rank preserved while the price channel is active**, because a second,
opposing downstream channel (process topology) is also opened — and preserved only below a plant scale that the
inequality locates.

## Headline numbers (central parameters; 10,000-draw Monte Carlo, seed 20261019)

- Parity scale S\* = 0.60 MW SNG (≈ 75 Nm³ h⁻¹ CH₄); Monte Carlo median 0.86 MW, 5–95 % 0.18–7.0 MW.
- P(Ru cheaper) = 0.983 at 0.1 MW, 0.44 at 1 MW, 0.029 at 10 MW, 0.0005 at 100 MW.
- Every deterministic scenario (Ru price ×0.1–×10, life 2–10 y, three catalyst-cost bases, κ 0.5–3, r_V 1.5–2.5, the
  source's own 2019 Ru price) gives Ru at 0.1 MW and Ni at 100 MW; the boundary moves over 0.14–37.6 MW.
- The full-model and leverage-inequality boundaries coincide exactly (bookkeeping identity, 382 points).

## Where it would sit

**Recommended: Discussion, one paragraph, plus a Supplementary Note.** The case is a literature-level cost chain, not a
full TEA, and it is external; it belongs where the paper generalizes (Discussion, the paragraph that currently reads
"A catalyst ranking carries over from one optimum to the next only to the extent that the upstream advantage reaches the
plant objective…"), with the model, ledger and Monte Carlo in a Supplementary Note after Note 9. It should not join Fig. 6
as a fourth in-house panel, because its activity input is the source's volume ratio rather than a rate law run through the
harness, and the three-tier bars of Fig. 1a would have to show it as laboratory-model → industrial-optimum with an
external model.

Under the supervisor's three-tier framing the case runs from the **laboratory optimum** (Ru > Ni by light-off and
single-stage conversion, as the source measures and simulates) to the **industrial optimum**, and the industrial optimum
is *scale-indexed*: Ru below ~1 MW, Ni above. That is the first case in the paper where the industrial optimum is not a
single catalyst but a boundary in plant scale, which is the point worth making in Discussion.

## Draft Discussion paragraph (proposed insertion after the "penalty differs at each step" sentence in Discussion)

> The same inequality can be read from an independent study. For CO₂ methanation, Moioli and Züttel[ref] compared
> 0.5 wt% Ru/Al₂O₃ with Ni/Al₂O₃ in their own reactor model: Ru reaches 99.5 % conversion in one stage, Ni needs
> 1.9 times the catalyst volume and an intermediate water-condensation stage, and the Ru bed costs about 2.5 times the Ni
> bed. Taking their volume ratio and catalyst-cost bases through the inventory → reactor → replacement chain of this work,
> with the same metal prices as the ammonia case, the inventory term favours Ni at every scale, as it favours Fe in
> ammonia; Ru is the least-cost catalyst only where the second Ni stage, whose capital does not shrink with throughput,
> outweighs the Ru price, below 0.6 MW of SNG at the central parameters (Monte Carlo median 0.9 MW, 5–95 % 0.2–7 MW;
> Supplementary Note 10). The laboratory ranking is therefore preserved at the scale the source recommends for Ru and
> inverted at the scale it recommends for Ni, and the boundary between them is the point at which the process-topology
> penalty of the cheap metal equals its price advantage.

## Proposed Supplementary Note 10 outline

1. Source statements used, with table locations (SOURCE_LEDGER.csv).
2. Cost chain and the leverage identity; what is and is not costed (RESULTS.md "What is modelled").
3. Table: central decomposition by scale (r_V, Π, φ_proc, winner).
4. Table: boundary scale against Ru price and catalyst life.
5. Monte Carlo P(Ru < Ni) by scale; parameter brackets and which were not sourced.
6. Kinetic cross-check and the Koschany rate-constant ambiguity (3.46 × 10⁻⁵ vs 10⁻⁴).
7. Limitations: no feed, compression, heat-integration or hybrid-bed terms; literature-level, not a TEA.

## Decisions needed from the author

- Whether an external, literature-level case is admissible alongside the three in-house cases, and if so whether it
  enters Discussion only, Discussion + SI, or also Fig. 1a as a fourth bar.
- Whether the catalyst-cost basis for the headline should be the precursor basis (central here; S\* = 0.6 MW) or the
  commercial-catalyst basis (S\* = 0.2 MW); the source reports both.
- Whether to state the boundary in MW SNG or in Nm³ h⁻¹ CH₄ (power-to-gas literature uses both).
