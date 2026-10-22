# Proposed replacement text — Au/TiO2 section (§3.6) and the Au sentence of the Abstract

Date: 2026-10-19. Draft for the author; the manuscript (`docs/MANUSCRIPT_MAIN_TEXT.md`) is not edited here.
Numbers: `docs/AU_TIO2_DECISION_BOUNDARY_V2_RESULT.md` (CI-asserted), `data/rank_preservation_control_v1_1.csv`,
`data/rank_preservation_semiopen_v1_3_summary.csv`. Framing follows the 2026-10-12 three-tier table (Au/TiO2
measures "laboratory → catalyst requirement") and the writing rule "locate and explain the decision boundary", not
"predict it". Reader-facing text uses scientific names only (LOCK-02/03); the internal labels V1.1/V2.0/V1.3 appear
in this file only as pointers for the author and must not be carried into the manuscript.

---

## A. Abstract — current and proposed Au sentence

**Current (last sentence of the Abstract):**

> Leaders change where a catalyst property alters a downstream operating requirement and are kept where it maps monotonically onto catalyst requirement.

**Proposed:**

> Leaders change where a catalyst property alters a downstream operating requirement; where candidates share one metal, one loading and one product, as 2–6 nm Au/TiO₂ particles do in CO oxidation, the only channel that can invert the ranking is catalyst lifetime, and the inversion boundary is located where the lifetime gain of the larger particle exceeds its activity penalty.

(Alternative, shorter: "…and are kept where no downstream channel differentiates the candidates by more than their activity ratio, as for 2–6 nm Au/TiO₂ in CO oxidation, whose only inverting channel, catalyst lifetime, we locate.")

---

## B. §3.6 — current and proposed

**Current heading and paragraph:**

> ### A monotonic catalyst-to-process mapping preserves the ranking
>
> Process evaluation does not change every ranking. In Au/TiO₂ CO oxidation, with the rate anchor of Janssens et al.[24] and the particle-size dependence of Overbury et al.,[25] candidates differ only in particle size from 2 to 6 nm under one operating condition and process model. Intrinsic activity and required catalyst mass preserve the order 2 > 3 > 4 > 5 > 6 nm in all 10,000 parameter samples drawn from the literature ranges (Fig. 6b–d), and in 92.2% when candidate-specific kinetic and operating variations are introduced over 273–293 K (Fig. 6e).

**Proposed heading and paragraphs:**

> ### Where no channel differentiates the candidates, the ranking is kept, and the one channel that can invert it has a located boundary
>
> Process evaluation does not change every ranking, and the Au/TiO₂ CO-oxidation case shows why. With the rate anchor of Janssens et al.[24] and the particle-size dependence of Overbury et al.,[25] 2–6 nm Au particles on one support differ only in size; mass activity falls as d^−1.9 at the nominal exponents, so the 6 nm particles require 8.1 times the catalyst mass of the 2 nm particles at a fixed conversion duty. Under this fixed-condition mapping the order 2 > 3 > 4 > 5 > 6 nm is kept in every parameter sample, but that result is a property of the mapping, not of the catalyst: any positive size exponent applied to all sizes at once is monotone, and the Au price, the Au loading and the support cost are common to all sizes, so the price channel that reverses the ammonia ranking is identically absent here. The fixed-condition calculation therefore serves as the implementation control (Fig. 6b–d), and the evidence about the system comes from three further tests.
>
> First, when each size carries its own activity uncertainty (a lognormal factor with σ = 0.25 in ln units, bounded by the exponent uncertainty of the size series,[25] on top of the shared exponent ranges), the full order survives in 77.7% of 10,000 samples and the 2 nm leader in 99.4%; the inversions that do occur sit in the 5/4 nm (7.7%) and 6/5 nm (11.1%) pairs, where the activity gaps are smallest. Second, allowing each size its own temperature and O₂/CO ratio within the literature ranges keeps the full order in 92.2% of samples over 273–293 K and 72.6% over 273–313 K (Fig. 6e). Third, catalyst lifetime is the one channel that can differentiate the sizes. With annualized catalyst cost equal to required mass divided by lifetime, adjacent pairs exchange order when the larger particle's lifetime exceeds the smaller one's by the mass ratio (2.16, 1.73, 1.53 and 1.41 for the 3/2, 4/3, 5/4 and 6/5 nm pairs), and for a power-law lifetime τ ∝ d^q the whole ranking reverses at q* = n + m = 1.9, the size exponent of the mass activity. The decision boundary is therefore the line q = n + m in the (q, n + m) plane (Supplementary Fig. X), and the per-size uncertainty widens it into a band: with operating freedom and lifetime acting together over 273–293 K, the 2 nm leader is kept in 97.6% of samples at q = 1, 61.6% at q = 1.5 and 5.2% at q = 1.9.
>
> The literature places the measured regime on the kept side of this boundary with a stated condition window. In powder Au/TiO₂ at 273–313 K and atmospheric pressure, activity loss proceeds by carbonate and bicarbonate accumulation on the support and at the particle perimeter, is reversible by thermal or hydrogen regeneration, and occurs without particle growth;[refs: Saavedra 2013, Azar 2006, Clark 2007] no size dependence of this loss has been resolved, so the lifetime between regenerations is to first order size-independent (q ≈ 0) and the 2 nm leader is kept. Where Ostwald ripening of the smallest particles is active, as observed on model Au/TiO₂(110) under CO/O₂ at room temperature and at 300–410 K,[refs: Lai 2000, Yang et al.] and as the size-dependent metal chemical potential predicts for sub-3 nm Au,[refs: Campbell 2002, Parker 2007] ripening kinetics give q between 3 and 4, above the boundary, and the larger particles become the economic choice. The Au/TiO₂ case thus measures the step from the laboratory optimum to the catalyst requirement (Fig. 1a): the ranking is kept because every channel other than lifetime has a ratio of one, and the lifetime boundary is located, not assumed.

**Consequential edits elsewhere (for the author; not made here):**

- §3.7 ("These cases reveal three distinct observed outcomes…"): replace "an upstream advantage is preserved in the Au/TiO₂ control" with "an upstream advantage is preserved in Au/TiO₂, where no differentiating channel is present below the located lifetime boundary"; the χ ≈ −1.00 sentence should say that χ = −1 is the fixed-condition value and is a property of the mapping.
- Discussion paragraph "The penalty differs at each step…": change "from the laboratory optimum to the catalyst requirement in Au/TiO₂ there is none, and the ranking is kept" to "…in Au/TiO₂ the only candidate penalty is lifetime, which lies below its inversion threshold in the measured low-temperature window, and the ranking is kept".
- Methods, "Au/TiO₂ rank-preservation control": add two sentences describing the per-size uncertainty propagation (σ, seed, draws) and the lifetime channel (annualized cost = required mass / lifetime; τ ∝ d^q; boundary q = n + m), pointing to the Supplementary note.
- Fig. 6c caption: "ρ = τ = 1.000, with the complete order preserved in 10,000/10,000 parameter samples" is true but should be labelled as the fixed-condition implementation control; the Supplementary figure carries the (q, n + m) map.
- Reference list: add Saavedra et al. 2013 (10.1016/j.jcat.2013.06.021), Azar et al. 2006 (10.1016/j.jcat.2006.02.012), Clark et al. 2007 (10.1016/j.cattod.2006.10.008), Campbell et al. 2002 (10.1126/science.1075094), Parker and Campbell 2007 (10.1007/s11244-007-0274-z), Lai and Goodman 2000 (J. Mol. Catal. A 162, 33; DOI to be verified) and the Yang et al. Au/TiO₂ ripening study (bibliographic entry to be verified from Niu et al., Nanoscale 2018, ref. 28).

**What this proposal states plainly:** the fixed-condition preservation is by construction; the evidential content
now comes from the per-size uncertainty propagation, the lifetime boundary and the operating-freedom test. The
claim is the location and explanation of the boundary, not a prediction of the industrial choice.
