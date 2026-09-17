# Editorial figure architecture v1 — 2026-09-17

## Main-text target: six composite figures

The current evidence is stronger than a ten-figure linear sequence requires. For a high-impact general-science presentation, the main text should carry six composite figures, each organized around one scientific question. Existing panels and assets can be reused; this is an editorial regrouping, not a scientific reanalysis.

### Figure 1 | The industrial decision frontier can reverse an atomic catalyst ranking

**Question:** Does atomic ranking survive industrial propagation?

**Panels**
- a, 15-metal atomic activity ranking versus optimized catalyst-dependent economic ranking, highlighting Ru, Os and Fe.
- b, rolling Top-K Spearman correlation, with the Top-3 frontier and full-15 result marked.
- c, compact rank-flow inset for Ru, Os and Fe if space permits.

**Headline:** Ru > Os > Fe becomes Fe > Ru > Os; Top-3 rho = -0.50 while full-15 rho = 0.929.

**Role in the story:** establishes the central phenomenon and immediately distinguishes decision-frontier failure from global rank disorder.

### Figure 2 | Process reoptimization and uncertainty define the actionable region

**Question:** Which downstream constraints determine whether the frontier is stable?

**Panels**
- a, Fe/Ru/Os pressure-dependent optimized cost envelopes.
- b, operating optima / shallow-envelope representation.
- c, Fe uncertainty propagation with feasibility, Top-1 survival and Top-3 actionable frequency.

**Headline:** catalyst-specific process optima coexist with a stable economic ordering, while uncertainty is selectively amplified or absorbed by the process constraints.

**Role in the story:** shows that the inversion survives realistic process freedom and that atomistic uncertainty should be interpreted through decision sensitivity.

### Figure 3 | Backward design separates economic requirement from physical reachability

**Question:** What improvement would Ru need, and can the current catalyst manifold provide it?

**Panels**
- a, Ru activity multiplier versus reoptimized cost, with Fe parity crossing at approximately 201-fold.
- b, scaling-consistent activity headroom versus the required target.
- c, strict-scaling Ru minimum relative to Fe.

**Headline:** approximately 201-fold activity is required, compared with a maximum scaling-consistent headroom of 2.525-fold.

**Role in the story:** converts ranking inversion into a design target and then tests whether that target is physically reachable.

### Figure 4 | Methanol transfers the framework through a different process pathway

**Question:** Does ranking reshaping persist when the controlling catalyst-to-process pathway changes?

**Panels**
- a, Re/TiO2 upstream-to-economic rank flow at the canonical 2% purge.
- b, NPC versus purge fraction for all four catalyst-temperature states.
- c, local leverage comparison for STY, conversion and methane suppression.
- d, small inset showing the effect of alternative upstream screening metrics on the identity of the apparent winner.

**Headline:** the Re-normalized upstream winner falls from first to third after recycle/separation economics; methane suppression has the dominant local leverage in the benchmark state.

**Role in the story:** demonstrates transfer across reaction and process architecture while identifying selectivity-recycle coupling as the mechanism.

### Figure 5 | Coupling topology determines whether rankings invert or survive

**Question:** Is inversion an intrinsic consequence of multiscale propagation?

**Panels**
- a, compact mechanism map: NH3 activity -> inventory/reactor demand; MeOH selectivity -> loss/purge/recycle/compression.
- b, Au/TiO2 mirror rank flow showing exact preservation at the canonical condition.
- c, small robustness panel for the V1.3 semi-open extension.

**Headline:** strong candidate-specific downstream coupling can reshape the decision frontier, whereas a common monotonic mapping preserves the ranking and moderate operating freedom produces only limited local reshuffling.

**Role in the story:** provides the falsification control and elevates the paper from two case studies to a conditional principle.

### Figure 6 | Decision-aware scientific compute has a capability-bounded operating envelope

**Question:** When can adaptive allocation recover the industrial decision with less available compute than a fixed policy requires?

**Panels**
- a, complete-decision recovery versus CU for the three model tiers, with D = 206 CU, 75 CU and the 50-CU floor marked.
- b, canonical backward-target recovery versus CU, visually separating the 75-CU decision threshold from the 225-CU quantitative-target threshold.
- c, canonical narrow-window allocation frequency versus CU for the strong model and weaker-tier comparison at 175 CU.
- d, decision-stable CU versus final-used CU, with the non-binding 5,000-CU condition shown separately from the bounded-budget axis.

**Headline:** the strong model closes the complete decision at 75 CU, quantitative target recovery converges later at 225 CU, and the allocation advantage disappears when the budget ceases to bind.

**Role in the story:** closes the paper by linking decision-aware catalyst design to decision-aware allocation of scientific computation.

## Extended Data / Supporting Information allocation

Detailed Monte Carlo distributions, full operating surfaces, pairwise inversion matrices, alternative methanol screening metrics, the complete purge sweep, Au/TiO2 stress-level tables, named-versus-anonymous agent controls, low-budget error taxonomy, E2 interface results, mini saturation sweeps, quote-versus-ledger CU accounting and the full 5,000-CU trace audit belong in Extended Data or Supporting Information.

## Editorial rule

Each main figure should answer one question and have one sentence-level take-home message. Main-text panels should prioritize rank changes, physical mechanism and decision consequences. Provenance, audit structure, frozen hashes, implementation details and exhaustive robustness accounting remain essential evidence, but they should stay outside the visual foreground of the main narrative unless they change the scientific interpretation.
