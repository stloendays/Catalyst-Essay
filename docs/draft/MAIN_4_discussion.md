<!-- MAIN TEXT - Discussion 4.1-4.5. Drafted 2026-09-16 against MANUSCRIPT_SKELETON_v4_2026-09-14.md.
Section 4.6 is FROZEN in the skeleton and is not reproduced here; 4.5 hands off to it and does not anticipate its
content. Every number below is taken from a named source file; the claim-to-source list accompanies this draft.
Agent numbers are governed by docs/AGENT_METRIC_DEFINITIONS_SOURCE_OF_TRUTH_2026-09-13.md. -->

## 4. Discussion

### 4.1 Screening objectives should be defined at the level of downstream economic leverage

A catalyst property is valuable only insofar as it moves a cost pool that the industrial objective actually contains,
so high intrinsic sensitivity is not equivalent to high economic leverage. In ammonia synthesis the catalyst-dependent
cost at the optimum is not dominated by the catalyst. The entire metal-inventory pool is **0.070 USD/t** of Fe's
**15.292 USD/t** and **1.833** of Ru's **22.031**, while fresh compression electricity alone accounts for **9.660** and
**14.291** and compressor CAPEX for a further **3.875** and **5.055**. What separates the two candidates economically is
therefore how their activity translates into operating severity and equipment duty, not the price of the active metal.
The same asymmetry orders the non-activity design levers: raising metal recovery to its **0.95** bound closes **0.685**
of the baseline Fe/Ru cost-ratio gap and extending catalyst life to **20 y** closes **0.161**, whereas relaxing the upper
pressure bound closes **0.000**, because the Ru and Os optima are interior points at **425 bar** on the 10-1000 bar grid.
A screen that ranks an intrinsic property without asking which pool that property enters cannot distinguish a lever from
a non-lever.

The methanol case adds a sharper point: the objective function of the screen itself decides which candidate is
mis-ranked. All three admissible upstream metrics return the same frontier statistics — Spearman rho = **0.20**, Kendall
tau = **0.00**, **3 of 6** pairwise inversions — so the reshuffle is not an artefact of normalization. But STY per g Re
places **1 wt% Re / 250 C** first, and that state lands at economic rank **#3** with **974.99 EUR/t** against the
winner's **943.30 EUR/t**, while single-pass yield X*S and STY per g catalyst both place **5 wt% Re / 200 C** first,
where it coincides with the economic winner. The choice between a per-active-metal and a per-catalyst-mass denominator
carries no thermodynamic content, yet it determines whether the top pick of the screen survives propagation. Local
leverage at the **5 wt% Re / 250 C** benchmark makes the cost of that choice explicit: **0.00289** for STY, **0.05883**
for single-pass conversion and **0.37579** for CH4 suppression. The quantity the intrinsic screen maximizes has the
weakest economic leverage of the three tested.

The practical consequence is that a screening objective should be reported together with the cost pool it is intended to
move, and that sensitivity to the screening metric should be reported alongside the ranking itself, not treated as a
normalization detail.

### 4.2 The relevant uncertainty is decision sensitivity, not atomistic uncertainty alone

One descriptor distribution supports several different decisions with very different stability. The same 1,000-draw
propagation gives Fe an engineering feasibility of **79.9%**, a Top-1 survival probability of **28.2%** and a Top-3
actionable probability of **94.0%** (**98.5%** conditional). The winner transitions show why: the atomic winner moves to
Fe in **29.5%** (Ru) and **27.4%** (Os) of draws, stays at Ru in **17.0%**, moves Os to Ru in **14.9%**, and Fe is the
atomic and economic winner in only **11.2%**. The question "which single metal wins" is not resolved by the current
descriptor uncertainty; the question "is Fe inside the actionable shortlist" is. The two questions set different
uncertainty-reduction targets, and only the feasibility boundary has one that can be stated as a descriptor precision.

Inverting the feasibility statistic makes the target concrete rather than rhetorical. At the frozen descriptor
uncertainty **sigma_Fe = 0.227 eV** and the frozen **90 m3** bed-volume criterion, Fe feasibility is **0.799** by the
frozen Monte Carlo routine and **0.8120** on the analytic descriptor-interval scale, a **1.3 pp** difference against the
**1.26 pp** binomial standard error at n = 1,000. Reaching a **0.95** feasibility target requires either reducing the
descriptor uncertainty to **0.122 eV** at the frozen bed cap, or relaxing the bed cap to **6,479.6 m3** at the frozen
uncertainty — and the second route is not an engineering option, since the Fe optimum uses a **17.1 m3** bed. The
decision-relevant uncertainty-reduction target is therefore a specific descriptor precision, not a general instruction to
improve the energetics. These inverted quantities are also model-version specific: under NH3-FINAL-1.0, with a baseline
feasibility of **73.6%**, the same inversion returned **0.0874 eV** and **50,293 m3**, both now superseded.

The converse case is equally important. Parametric uncertainty that is large in provenance terms can be irrelevant to
the decision. The **10-25%** perturbation set over CEPCI, CRF, compressor and vessel correlations leaves the
ranking, the inversion, the feasibility result and the reachability verdict fixed; a **-25%** compressor-CAPEX
diagnostic moves the activity-only break-even only from **201.2234x** to **200.4x** and changes nothing else. The
unverified pressure basis of the inherited reactor-volume proxy can at most affect **0.115 USD/t** for Fe and
**0.030 USD/t** for Ru, **0.8%** and **0.1%** of their costs. An input whose provenance is weak is not thereby
decision-relevant, and an input that is well characterised is not thereby decision-irrelevant.

Finally, which constraint is decision-active is itself a property of the current model rather than a fixed feature of the
system. Once pressure-dependent equipment CAPEX is included, the **90 m3** feasibility gate no longer changes the
winner: the raw Top-1 probability equals the feasible Top-1 probability at **0.282** in every draw, against **0.185** and
**0.248** in NH3-FINAL-1.0, because the pressure premium already penalises oversized beds. Decision sensitivity must
therefore be recomputed on the current model, not inherited with the descriptor.

### 4.3 Backward design changes the interpretation of catalyst targets

The forward question "can this catalyst be made more active" has no stopping rule, because any improvement can be
declared progress. The backward question has one. Reoptimizing the full ammonia process while scaling Ru activity places
cost parity with Fe at an activity-only requirement of **201.22x**, at an operating point of approximately
**425 C / 190 bar / 30 C**. That number is falsifiable against a supply side computed in the same framework: the
scaling-consistent activity headroom is **1.0899x** at the 673 K reference condition and **2.5246x** at most over the
frozen **14,136-state** process-state library. The gap is not marginal, and the conclusion does not depend on where
inside the process library the comparison is made. The strict-scaling route confirms it directly: the lowest Ru cost
reachable along the scaling manifold is **21.398 USD/t NH3** at **E_N = -1.215 eV**, still above Fe's
**15.292 USD/t NH3**.

The verdict is considerably more robust than the target. Between NH3-FINAL-1.0 and NH3-FINAL-1.1 the break-even
requirement fell from **2171.5598x** to **201.2234x**, a **90.7%** reduction driven by the extended pressure grid and the
pressure-dependent CAPEX term, while the maximum headroom moved only from **2.4329x** to **2.5246x**. The reachability
verdict was unchanged in both regimes. This is the property that makes backward design useful as a decision instrument:
the object that must be reported is the ratio of requirement to headroom, and a large revision to the requirement alone
does not necessarily reopen the question.

What backward design licenses is correspondingly narrow. The result is an activity-only infeasibility signal under the
current process model, its operating constraints and the scaling-consistent design path, not an experimental prediction
that no ammonia catalyst can reach Fe parity. Read that way, it redirects rather than closes the search. Among the levers
tested on the canonical run, metal recovery reaches **0.685** of the cost-ratio gap at its **0.95** bound and a cost-ratio closure of **0.911**
at **0.99**; catalyst lifetime reaches **0.161** at **20 y**; bed-cap relaxation is inactive, since the Fe bed leaves
**72.94 m3** of slack against the **90 m3** cap and the constraint only becomes active once the cap falls below
**17.06 m3**; and the upper pressure bound has ceased to be a lever at all, because the 1.0 sensitivity to it
recorded in the archived FINAL-1.0 model measured a grid truncation rather than a design freedom. A backward-design target is therefore best read as a statement about
which channel is closed, evaluated on the same cost metric that closed it.

### 4.4 Reaction transfer requires pathway transfer, not only model transfer

A new reaction should not inherit the ammonia mechanism by analogy, because the two cases separate their candidates
through different cost pools. In ammonia the separation runs through catalyst inventory, reactor demand and process
severity, and the inventory pool itself is small: **0.070 USD/t** of Fe's **15.292 USD/t**. In methanol the separation
runs through the recycle loop. The state with the highest single-pass conversion, **5 wt% Re / 250 C** at
**X_CO2 = 0.40**, carries the highest cost at **1258.17 EUR/t**, because **S_CH4 = 0.25** raises the non-H2/CO2 loop
fraction to **0.5208** and the H2 feed cost to **886.24 EUR/t**, against **645.24 EUR/t** for the economic winner, with
recycle flow at **145,648 kmol/h** against **67,467.4 kmol/h** and compression at **29.91** against
**22.13 EUR/t**. An analysis that transplanted the ammonia pathway would have read the highest conversion as the
strongest candidate and ranked the most expensive state first.

The protocol has to transfer as well, and the degree of freedom that is reoptimized is part of the physical claim. The
ammonia case reoptimizes temperature, pressure and separator temperature per catalyst identity across the
**14,136-state** admissible domain, because a kinetic model supports that reoptimization. The methanol case has no T/P
kinetic model — the four candidates are catalyst-temperature states measured at literature points — so the loop variable
is reoptimized instead, across **396** purge levels from **0.5%** to **40%**. The methanol conclusion survives that
substitution: Spearman rho never exceeds **0.40**, at least **2 of 6** pairs invert at every purge level, the intrinsic
per-Re winner is never the economic winner, and every per-candidate optimum sits at the **0.5%** lower bound
(**895 / 907 / 918 / 1233 EUR/t** for 1 wt% Re / 200 C, 5 wt% Re / 200 C, 1 wt% Re / 250 C and 5 wt% Re / 250 C), a
boundary optimum that leaves the **2%** source-anchored point as the canonical comparison. Importing the ammonia
reoptimization protocol unchanged would have swept a variable the methanol evidence does not contain, and omitting the
loop sweep would have left the single available process freedom untested.

The limit of what can currently be asserted is explicit. No quantitative cross-reaction leverage comparison is available:
the denominator-aligned MeOH CH4-suppression / NH3 TOF normalized-leverage ratio is classified
**METRIC_EQUIVALENCE_NOT_ESTABLISHED**, and the repository-level revalidation in GitHub Actions run **34449914480**
recovered **0** pre-audit code-level implementations of the historical NH3 denominator. The FINAL-1.1 source-harness
provenance vendored into the repository after that run does not retroactively establish the missing metric definition.
The archived **273-410** range and its **~328** midpoint belong to the pre-FINAL-1.1 normalization and are not rescaled
into a current value. What is established, and what transfer claims should be restricted to, is the pathway level:
ammonia propagates activity through catalyst inventory, reactor demand and process severity, whereas methanol propagates
selectivity through feed loss, gas accumulation, purge, recycle and compression burden. Until metric equivalence is
re-established, the correct question when moving to a third reaction is which catalyst property controls which
downstream cost pool in that process architecture, answered from that architecture rather than by rescaling a ratio.

### 4.5 Ranking inversion is conditional, not an intrinsic consequence of adding more model layers

The Au/TiO2 control supplies the counterfactual needed to interpret the two inversion cases. Under the canonical
fixed-condition mapping, the literature-calibrated mass-activity ranking and the downstream required-catalyst-burden
ranking are the same order, **2 > 3 > 4 > 5 > 6 nm**, with Spearman rho = **1.000**, Kendall tau = **1.000**, **0**
pairwise inversions, and the complete order preserved in **10,000 / 10,000** predefined literature-envelope draws. The
implementation that inverts the ammonia decision frontier (Top-3 rho = **-0.50**, tau = **-0.33**, against a full
15-metal raw rho of **0.929**) and reshuffles the methanol states (rho = **0.20**, tau = **0.00**, **3 of 6** inversions)
leaves this ranking exactly intact. Passing through more model layers is therefore not the operative cause.

Neither is the magnitude of the downstream spread. Replacing the original arbitrary burden coefficients with the
literature calibration lowered the nominal TOF size exponent from **1.70** to **0.90** and compressed the 6 nm / 2 nm
required-catalyst ratio from **19.42x** to **8.064x**, a **58.5%** reduction in the downstream spread, without changing a
single pairwise comparison. A downstream layer that is large but monotone in the upstream property cannot invert an
ordering, while a layer that is small but differently ordered across candidates can.

Preservation is also not an artefact of holding the operating point perfectly fixed. In the semi-open V1.3 extension each
particle-size state independently selects its temperature and O2/CO ratio inside a literature-constrained low-temperature
envelope, with candidate-specific perturbations to the activity prefactor and the apparent activation energy. Under
moderate stress in the primary **273.15-293.15 K** window the exact full order survives in **92.16%** of 10,000 draws,
the mean Spearman rho is **0.99214**, **99.98%** of draws retain rho >= 0.9, and the mean number of pairwise inversions
per draw is **0.0786**. In the wider **273.15-313.15 K** sensitivity window exact preservation falls to **72.62%** with
mean rho **0.96802**, **97.56%** of draws above rho = 0.9 and **0.3012** mean inversions. The reshuffling that does occur
appears first among neighbouring, lower-ranked states rather than as a reversal at the decision frontier. These bounds
should be read with the control's scope: V1.1 is a rank-preservation control and not a full industrial TEA, the V1.3
process penalties are generic monotone penalties rather than a literature-derived plant cost model, and no absolute
process economics are assigned to the Au/TiO2 system.

Taken together, the three cases sharpen the central claim. The relevant object is not multiscale complexity in the
abstract but the coupling topology between catalyst properties, screening objectives and downstream decision variables.
Substantial inversion appears only when candidate-specific downstream coupling is large enough, and differently enough
ordered, to overcome the upstream separation. Au/TiO2 fails that condition by construction, holding chemistry, support,
feed and topology common so that only a monotone size-activity relation propagates. Ammonia meets it through
candidate-specific process and economic reoptimization, and methanol meets it through selectivity-driven recycle
economics, with its top-rank reversal additionally conditional on the upstream normalization.

Because the condition is a property of the coupling rather than of model depth, it cannot be settled by adding layers; it
has to be evaluated for the particular chain, and that evaluation is what consumes scientific compute. Which parts of the
chain must actually be computed before the industrial decision is determined, and under what budget, is the question the
frozen DISCOVER benchmark poses.
