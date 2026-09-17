<!-- MAIN TEXT DRAFT - Results 3.4-3.6. Written 2026-09-16 against MANUSCRIPT_SKELETON_v4_2026-09-14.md.
Sections 3.7 and 4.6 are frozen and are not touched here. Figure 9A is quantitatively on HOLD
(METRIC_EQUIVALENCE_NOT_ESTABLISHED); section 3.5 is therefore written at pathway level with no cross-reaction ratio. -->

### 3.4 Methanol catalyst-state rankings invert through a selectivity-recycle pathway

The CO2-to-methanol case tests a second propagation channel on four Re/TiO2 catalyst-temperature states taken from a
single controlled study (Gothe et al., ACS Catal. 2025, Table 3; 100 bar, CO2/H2 = 1:4, 500 °C prereduction) and passed
through one explicit recycle and separation loop anchored to a published plant model (Processes 2022, 10, 1535;
calibration error -0.01 %). All four states are evaluated at the same 2 % purge. Using space-time yield per gram of Re as
the upstream intrinsic-productivity metric, the states rank 1 wt% Re / 250 °C first at 65 g MeOH per g Re per hour,
1 wt% Re / 200 °C second at 55, 5 wt% Re / 200 °C third at 18 and 5 wt% Re / 250 °C fourth at 16. After propagation to a
near-full-plant net production cost, the order becomes 5 wt% Re / 200 °C at 943 EUR/t, 1 wt% Re / 200 °C at 967 EUR/t,
1 wt% Re / 250 °C at 975 EUR/t and 5 wt% Re / 250 °C at 1258 EUR/t. The intrinsic per-Re winner therefore falls from
first to third while the third-ranked state becomes the economic winner; across the four states Spearman rho = 0.20,
Kendall tau = 0.00, and 3 of 6 pairwise comparisons invert.

The reshuffle follows selectivity rather than productivity. The state with the highest single-pass conversion,
5 wt% Re / 250 °C at X_CO2 = 0.40, is also the most expensive, because its methanol selectivity falls to 0.74 and its
methane selectivity rises to 0.25. Methane is not cleared efficiently from the loop: at that state the non-H2/CO2 loop
fraction reaches 0.52, of which 0.47 is methane, against 0.13 at 5 wt% Re / 200 °C, and the accumulating inert stream
forces the recycle flow from 67,467 to 145,648 kmol/h. The cost consequences are distributed rather than local: hydrogen
feed cost rises from 645 to 886 EUR/t as H2 is consumed by methanation instead of methanol, the compression term rises
from 22.13 to 29.91 EUR/t, and the equipment-cost term rises from 65.13 to 82.43 MEUR. Local leverage evaluated at that
benchmark state confirms which catalyst property controls the chain: 0.00289 for space-time yield, 0.05883 for
single-pass conversion and 0.37579 for methane suppression, so suppressing methane is about 6.39 times as effective as
raising conversion and about 129.84 times as effective as raising production rate alone. This is a coupled
selectivity-recycle penalty, not a single-variable monotonic cost term applied to a rate.

The reshuffle is a property of the propagation, not of the screening metric, but the identity of the mis-ranked candidate
is not. Under all three admissible upstream metrics — space-time yield per gram of Re, single-pass methanol yield X·S,
and space-time yield per gram of catalyst — the global statistics are identical at rho = 0.20, tau = 0.00 and 3 of 6
pairs inverted. What changes is the top rank: the Re-normalized intrinsic metric places 1 wt% Re / 250 °C first, and that
state falls to economic rank three, whereas the yield and per-catalyst metrics place 5 wt% Re / 200 °C first, where it
coincides with the economic winner. The screening objective decides which candidate is mis-ranked at the decision
frontier, not whether the frontier is reshuffled.

The result also survives the one process degree of freedom the source loop exposes. The workbook sweeps the purge
fraction from 0.5 % to 40 % for every state across 396 levels. Over that entire sweep the intrinsic per-Re winner is
never the economic winner, the highest-conversion state is never the economic winner, Spearman rho never exceeds 0.40,
and at least 2 of 6 pairs invert at every level. Re-optimizing purge separately for each candidate — the methanol
analogue of the candidate-specific reoptimization used for ammonia — gives 1 wt% Re / 200 °C > 5 wt% Re / 200 °C >
1 wt% Re / 250 °C > 5 wt% Re / 250 °C at 895.25, 907.43, 917.63 and 1232.57 EUR/t, with rho = 0.40, tau = 0.333 and 2 of
6 inversions. Every per-candidate optimum sits at the 0.5 % lower bound of the sweep and is therefore a boundary optimum,
so the 2 % source-anchored point remains the canonical comparison and the sweep is reported as robustness.

Two boundaries are part of the design. The candidates are catalyst-temperature states measured at fixed temperature and
pressure, not four independently reoptimized catalyst identities; no T/P kinetic model exists for this system, so the
loop variable rather than the operating point is reoptimized per candidate. Rhenium purchase price is excluded from the
net production cost by design. The methanol case is consequently not a lower-fidelity repeat of the ammonia protocol but
the complementary test of a second channel: ammonia isolates activity to inventory to reactor demand and process
severity, methanol isolates selectivity to feed loss, gas accumulation, purge and recycle.

Primary figures: F7, F8.
Primary evidence: `docs/MEOH_RANKING_INVERSION.md`, `data/meoh/MeOH_D01_ExplicitRecycleSeparationEconomics_v3.0.xlsx`,
`data/meoh/meoh_candidate_ranking_D01v3.csv`, `data/meoh/meoh_purge_robustness_D01v3.csv` and the associated provenance
JSON.

### 3.5 Cross-reaction comparison reveals pathway-specific propagation mechanisms

The two reaction cases resolve different catalyst-to-process pathways, and the difference is visible in where the
catalyst-dependent cost actually sits. In ammonia, the catalyst acts through inventory, reactor demand and the operating
severity the process must adopt in order to use it. At the reoptimized optima the metal-inventory pool is 0.070 USD/t for
Fe and 1.833 USD/t for Ru, but the candidates separate far more strongly through the operating point those catalysts
drive the process to: Fe optimizes at approximately 425 °C and 180 bar with fresh-compression electricity of
9.660 USD/t, Ru at approximately 450 °C and 425 bar with 14.291 USD/t, and Os additionally carries 4.120 USD/t of
refrigeration against 0.000 for Fe. The catalyst-specific design levers act on the inventory pool rather than on that
operating point: on the canonical NH3-FINAL-1.1 run, metal recovery closes 0.685 of the Fe-Ru cost ratio and catalyst
lifetime 0.161, whereas the pressure-window and bed-volume constraints are inactive at the optima. Activity in ammonia is
therefore expressed economically as how much catalyst is needed and how severe a process is required to use it.

In CO2-to-methanol the dominant pathway differs in kind. The controlling property is selectivity, and it acts through the
loop rather than through the reactor: methane formation removes hydrogen from the product channel, accumulates as an
inert, and propagates into purge, recycle flow, compression duty and equipment burden, as quantified in section 3.4.
Nothing in the methanol case resembles the ammonia inventory-severity route, and nothing in the ammonia case resembles
the methanol loop-accumulation route.

The comparison is reported here at pathway level and without a cross-reaction numerical ratio. A denominator-aligned
methanol-to-ammonia leverage ratio appears in earlier project records, but it belongs to the archived
pre-NH3-FINAL-1.1 normalization: its ammonia baseline corresponds to the superseded FINAL-1.0 reduced cost rather than
the current Fe cost of 15.292 USD/t. A repository-level provenance audit and a GitHub Actions revalidation attempt
(run 34449914480) recovered 0 pre-audit code-level implementation candidates and 0 conservatively verified historical
metric implementations of the ammonia TOF economic-leverage definition, and the frozen FINAL-1.1 source harness required
to rerun that exact definition is not retained in this repository. The ratio is therefore classified
METRIC_EQUIVALENCE_NOT_ESTABLISHED and excluded from the current claim set, and no substitute is constructed either by
rescaling it or by defining a new proxy metric. The methanol leverage numerator remains directly traceable to the frozen
D01 v3 evidence; it is the ammonia denominator whose lineage cannot be established.

The manuscript-level conclusion is consequently bounded to what the two cases directly support: catalyst ranking changes
are reaction- and process-pathway dependent, ammonia demonstrating an activity-inventory / reactor-demand route and
methanol a selectivity-recycle route, with the choice of upstream screening objective further deciding which candidate is
mis-ranked at the decision frontier. A new reaction should not inherit either mechanism by analogy; the transferable
question is which catalyst property feeds which downstream cost pool in that process architecture.

Primary figure: F9A as a qualitative pathway panel only; no current cross-reaction numerical ratio.
Primary evidence: `docs/CROSS_REACTION_LEVERAGE_PROVENANCE_POINTER.md`, `artifacts/f9a_ci/f9a_ci_revalidation.json`,
`provenance/nh3_final_1_1/source_harness/NH3_FINAL_1_1_CONSISTENCY_CLOSURE.md`.

### 3.6 A literature-calibrated control shows that multiscale propagation does not intrinsically invert rankings

If adding model layers were by itself sufficient to reshuffle a ranking, the two inversion results above would be
artefacts of the implementation rather than findings about catalyst-to-process coupling. The falsification test is a
separate Au/TiO2 CO-oxidation control in which the downstream mapping is deliberately monotonic and no competing process
penalty is introduced. Candidate states differ only in Au particle size, from 2 to 6 nm, while active element, support,
feed composition, temperature, pressure, conversion duty and process topology are held common, so catalyst-dependent
burden can change only through the catalyst and Au inventory required to meet the same duty. Six preservation criteria
were fixed in advance: the highest-activity candidate must also be the lowest-burden candidate, Spearman rho >= 0.95,
Kendall tau >= 0.90, zero pairwise inversions, exact Top-3 ordering, and at least 95 % full-rank preservation under a
predefined uncertainty envelope.

The V1.1 control replaces the original arbitrary downstream coefficients with a literature-anchored physical mapping. The
absolute-rate anchor is a 2.10 nm Au/TiO2 catalyst with 4.40 wt% Au and 38 % measured dispersion, giving a stabilized
activity of 8.8 umol CO per gram of catalyst per second at 273.15 K and 1 atm in 1 % CO / 21 % O2 / 78 % Ar (Janssens et
al., J. Catal. 240 (2006) 108-113); the plug-flow relation reported in that source fixes the reference conversion at
11.14 %, which is derived from the experiment rather than chosen. The particle-size dependence is taken as TOF ~ d^-0.9
from the closest-loading 4.5 wt% series (Overbury et al., J. Catal. 241 (2006) 56-65), replacing the V1 nominal exponent
of 1.70. The recalibration is substantial and is reported explicitly: the effective mass-activity exponent falls from
2.70 to 1.90, and the 6 nm / 2 nm required-catalyst ratio falls from 19.42x in V1 to 8.064x in V1.1, a 58.5 %
compression of the predicted burden spread.

The ordering nonetheless does not change. Mass activity falls monotonically from 9.6548 to 1.1973 umol CO per gram of
catalyst per second between 2 and 6 nm, and the required catalyst mass rises monotonically from 19.505 to 157.284 mg, so
the activity ranking and the downstream catalyst-burden ranking are both 2 nm > 3 nm > 4 nm > 5 nm > 6 nm, with Spearman
rho = 1.000, Kendall tau = 1.000, zero pairwise inversions and the complete order preserved in 10,000 of 10,000
predefined literature-envelope draws. All six preregistered criteria pass. Because the burden spread was compressed by
more than half without disturbing the order, the preservation does not depend on the magnitude of the downstream
coefficients; it follows from an independently supported monotonic size-activity relation combined with a fixed process
condition and a common Au/TiO2 composition.

A supporting semi-open extension (V1.3) removes the perfectly fixed operating point while retaining the common chemistry
and topology. Each particle-size state independently searches reaction temperature and an O2/CO ratio between 1 and 21
inside a literature-constrained low-temperature envelope, with candidate-specific perturbations to the activity
prefactor and the apparent activation energy, so a weaker state can receive a favourable kinetic draw and a stronger
state an unfavourable one. Under moderate stress in the primary 273.15-293.15 K window, 10,000 draws preserve the exact
full ordering in 92.16 % of cases, with mean Spearman rho = 0.99214, 99.98 % of draws at rho >= 0.9 and a mean of 0.0786
pairwise inversions. In the wider 273.15-313.15 K sensitivity window, which extends beyond the 253-293 K range of the
activation-energy source, exact preservation falls to 72.62 % with mean rho = 0.96802 and 97.56 % of draws at rho >= 0.9.
The reshuffling that does occur is local, appearing first among neighbouring lower-ranked states rather than as a
reversal of the decision frontier.

The control therefore establishes a bounded but load-bearing negative result: the same multiscale implementation that
inverts the ammonia and methanol rankings preserves an upstream ranking exactly when the downstream mapping remains
monotonic and no competing process-severity or topology penalty is introduced, and it continues to preserve it strongly
once moderate candidate-specific kinetic and operating freedom is allowed. Ranking inversion is not an intrinsic
consequence of propagating through more model layers. V1.1 remains the canonical falsification control because the V1.3
process penalties are generic monotone penalties rather than a literature-derived plant cost model; neither is a full
industrial technoeconomic analysis, and no absolute process economics are assigned to the Au/TiO2 system.

Read together with sections 3.1-3.5, the three cases give a conditional rather than a universal statement. Multiscale
propagation preserves a catalyst ranking when the downstream mapping is monotonic, weakly reshapes it under moderate
downstream flexibility, and inverts or strongly reshapes it when catalyst properties and screening objectives couple
strongly enough to downstream process and economic pathways. The object that decides which of the three occurs is the
coupling topology between catalyst properties, screening objectives and downstream decision variables, not model
complexity in the abstract.

Primary figure: F9B.
Primary evidence: `docs/RANK_PRESERVATION_CONTROL_V1_1_LITERATURE_CALIBRATION.md`,
`data/rank_preservation_control_v1_1.csv`, `docs/RANK_PRESERVATION_CONTROL_V1_PREREGISTRATION.md`.
Supporting robustness evidence: `docs/RANK_PRESERVATION_CONTROL_V1_3_SEMIOPEN.md`,
`data/rank_preservation_semiopen_v1_3_summary.csv`.
