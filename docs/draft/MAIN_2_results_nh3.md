<!-- MAIN TEXT — Results 3.1-3.3 (ammonia). Drafted 2026-09-16.
All values are NH3-FINAL-1.1, canonical run outputs/nh3_final_20260905T134204Z, unless a FINAL-1.0 value is
explicitly labelled historical. Headings and argument structure follow MANUSCRIPT_SKELETON_v4_2026-09-14.md;
sections 3.7 and 4.6 of that file are frozen and are only cross-referenced here. -->

### 3.1 Atomic and economic rankings diverge in ammonia synthesis

At the atomic reference condition (673 K; pN2 24.5 bar, pH2 74.25 bar, pNH3 1.0 bar) the 15-metal microkinetic screen
orders the candidates Ru > Os > Fe, with log10 TOF values of -3.4512, -3.4953 and -5.3100. Propagating each metal
independently through catalyst productivity, inventory, reactor sizing and pressure-resolved economics — reoptimizing
reactor temperature, pressure and separator temperature per candidate over the 14,136-state process grid — reverses the
head of that list. The feasible economic order is Fe > Ru > Os, at **15.292**, **22.031** and **25.832 USD per tonne
NH3**. Fe is 6.739 USD/t cheaper than Ru, a cost ratio of 1.441.

The reversal is produced by the operating point each catalyst is driven to, not by the catalyst price alone. The Fe
optimum sits at 180 bar and pays 9.660 USD/t for fresh-feed compression and 3.875 USD/t of compressor bare-module
CAPEX, while Ru and Os are both driven to 425 bar and pay 14.291 USD/t and 5.055 / 5.050 USD/t for the same two pools.
Fe carries the larger vessel — a 17.06 m3 bed against 0.066 m3 for Ru and 0.029 m3 for Os — and therefore the larger
converter-shell pressure premium, 0.807 USD/t against 0.074 USD/t for both noble metals; that penalty is far smaller
than the compression saving it buys. Metal inventory runs the other way, 0.070 USD/t for Fe against 1.833 for Ru and
2.159 for Os, and Os additionally pays 4.120 USD/t of refrigeration electricity at its 0 C separator against 0.629 for
Ru and zero for Fe. The dominant channel is therefore activity to inventory to reactor demand to process
severity, with the intrinsically weaker metal winning because it can be operated in a cheaper part of the plant.

The inversion does not generalise to the full screen. Across all 15 metals the raw Spearman correlation between atomic
activity rank and economic rank is **0.929** (Kendall tau 0.829; 0.684 on the censored ranking), whereas restricted to
the top three candidates it is **-0.50** (Kendall tau -0.33). The rolling Top-K statistic localises the failure
precisely: rho is -0.500 at K = 3, +0.400 at K = 4, 0.700 at K = 5, 0.786 at K = 7, 0.818 at K = 11, 0.890 at K = 13
and 0.929 at K = 15. K = 3 is the only window with a negative correlation. A screen that is globally faithful can
therefore be wrong exactly where the decision is made, and a global rank statistic will not reveal it.

Primary figures: F1, F2 (both LOCKED to the canonical FINAL-1.1 assets).

### 3.2 Process reoptimization and uncertainty determine the actionable region

Extending the pressure grid to 10-1000 bar and adding pressure-dependent equipment CAPEX removes the boundary artefact
of the archived FINAL-1.0 model, in which the Ru and Os optima were pinned to the 300-bar grid edge. In FINAL-1.1 no
feasible optimum lies on a grid bound. Fe optimises at **425 C / 180 bar / 30 C** separator with a 17.06 m3 bed, having
moved from 400 C / 150 bar with an 86.6 m3 bed in FINAL-1.0: under a pressure-resolved shell cost the optimizer avoids
the large vessel rather than paying for it. Ru optimises at **450 C / 425 bar / 25 C**, now an interior point. Os has a
broad, shallow high-pressure minimum: its numerical argmin is 450 C / 425 bar / 0 C, the 360-430 bar band lies
within 0.1 USD/t of that argmin and the 220-430 bar band within 0.5 USD/t, and two of eight handbook-constant perturbations move the argmin to
approximately 220 bar. The Os operating pressure should not be quoted more precisely than the valley allows.

Propagating descriptor uncertainty over 1,000 draws (seed 20260816; Fe sigma 0.2271 eV, other metals uniform with
0.15 eV half-width) against the 90 m3 catalyst-bed criterion gives feasibility probabilities of 100% for Ru and Os,
**79.9%** for Fe, 24.5% for Rh and 7.6% for Ir, with every remaining metal at zero. The feasible set contains three
metals in 63.2% of draws, four in 21.4%, two in 13.4% and five in 2.0%, a mean of 3.12 candidates. The draws in which
Fe is infeasible are the strong-binding tail of its descriptor distribution, and should not be read as a probability
that Fe is industrially unusable.

Decision stability separates sharply from winner stability. Fe Top-1 survival is **28.2%**, while the Top-3 actionable
probability is **94.0%** and the Top-3 conditional probability is **98.5%**; the mean Monte-Carlo rank correlation is
0.941 raw and 0.694 censored. Winner transitions from the atomic to the feasible economic ranking are Ru to Fe in
29.5% of draws, Os to Fe in 27.4%, Ru to Ru in 17.0%, Os to Ru in 14.9% and Fe to Fe in 11.2%. The raw Top-1 frequency
before the feasibility gate is 0.282, identical to Top-1 survival after it, so in FINAL-1.1 the bed-volume gate no
longer selects the winner — the pressure premium already penalises oversized beds — whereas in FINAL-1.0 the two
figures differed (0.185 raw against 0.248). Uncertainty is therefore not amplified monotonically along the chain: the
same descriptor spread that leaves the identity of the single best metal genuinely uncertain still leaves the
three-metal shortlist actionable in 94% of draws.

Inverting the feasibility model quantifies what would have to change to make the single-candidate decision on Fe
actionable. Reaching 95% Fe feasibility at the frozen 90 m3 cap requires the descriptor uncertainty to fall from
0.2271 eV to **0.1223 eV**; holding sigma frozen instead, the bed cap would have to rise to **6,479.6 m3**. Both are
recomputed on FINAL-1.1 and supersede the FINAL-1.0 values of 0.0874 eV and 50,293 m3. The analytic baseline used for
the inversion, 0.8120, sits 1.3 percentage points above the frozen 1,000-draw value of 0.7990, a gap of about one
binomial standard error at n = 1,000 (1.26 percentage points), so the inverted values are reported on the analytic
scale. The eight registered perturbations of the handbook constants (CEPCI ±10%, discount rate 8% and 15%, compressor
CAPEX ±20%, vessel premium ±20%) leave Fe feasibility at 0.799 and the Top-3 correlation at -0.50 in every case, and no
perturbation returns an optimum to a grid edge.

Primary and supporting figures: F3, F4.

### 3.3 Backward design places the Ru activity target outside the current scaling manifold

Inverting the chain asks what catalyst-property improvement the economic objective would require. Reoptimizing the full
ammonia process at each level of a Ru activity multiplier, Ru reaches Fe cost parity at a break-even multiplier of
**201.2234429878984**, approximately 201-fold relative to baseline Ru. Parity occurs at 425 C / 190 bar / 30 C with a
0.027 m3 Ru bed, against an Fe cost of 15.292 USD/t. This is the same canonical multiplier that the frozen agent
benchmark in section 3.7 audits.

The scaling-consistent supply of activity is far smaller. Along the strict scaling and BEP path, the maximum attainable
Ru activity gain is **1.0899x** at the 673 K reference condition and **2.5246x** taken as the maximum over the frozen
14,136-state process-state library. The required-to-reachable ratio is therefore approximately **79.7x**. Following the
scaling manifold to its best point does not close the gap in cost either: the strict-scaling Ru minimum is
**21.398 USD/t at E_N = -1.215 eV**, still above Fe at 15.292 USD/t. The activity-only route is unreachable.

The verdict survives the largest structural change made to the economic model. In FINAL-1.0 the break-even requirement
was 2171.56x; adding the pressure-dependent CAPEX and widening the pressure grid moved it to 201.22x, a 90.7%
reduction — close to an order of magnitude — because parity now sits against an Fe cost of 15.292 USD/t rather than the
historical 10.199 USD/t, and the Ru floor of compression plus compressor CAPEX at a Fe-like pressure lies near it. The
reachable headroom barely moved over the same change: 1.0899x at 673 K in both versions, and 2.4329x to 2.5246x across
states. A requirement that falls by a factor of ten against a supply that rises by 3.8% leaves the classification
untouched. The eight-perturbation set keeps the break-even inside 151.0-283.9x, a factor-1.9 spread with no
order-of-magnitude change, holds the all-state headroom at 2.525x in every case, and preserves the unreachable verdict;
the separate -25% compressor-CAPEX diagnostic gives 200.4x.

The result should be read as an activity-only infeasibility signal under the current process model, operating
constraints and scaling-consistent design path, not as an experimental target for Ru. It also redirects the design
question. Within FINAL-1.1 the largest catalyst-specific non-activity lever is metal recovery, whose reach is 0.685 at
the 0.95 bound, followed by catalyst lifetime at 0.161 at the 20-year bound, while the bed cap and the pressure upper
bound are inactive constraints in the current regime.

Primary figures: F5, F6.
