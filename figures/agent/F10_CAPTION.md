# Figure 10 — caption (final text)

Asset: `F10_agent_capability_bounded_envelope.svg` (canonical), `.pdf`, `.png` (600 dpi).
Data: `data/agent_figure_panel_data_2026-09-13.csv` and `data/discover_boundary_c1_error_taxonomy_summary.csv`.
Renderer: `render_F10_agent_envelope.py`. Manifest: `F10_RENDER_SHA256.txt`.
Metric definitions: `docs/AGENT_METRIC_DEFINITIONS_SOURCE_OF_TRUTH_2026-09-13.md`.

---

## Caption

**Figure 10 | Adaptive compute allocation has a capability-bounded operating envelope.**
All panels use the frozen DISCOVER V1 environment and the DISCOVER-BOUNDARY-C1 budget series; *n* = 20 independent runs
per cell unless noted (200 CU, *n* = 8; 250 CU, *n* = 9). The deterministic fixed-VOI policy D reaches the complete
decision at 206 CU (dashed grey line). A complete decision requires the economic winner, the decision pair and the
reachability verdict. In every panel the non-binding 5000-CU allowance is drawn on a separate axis with a dashed spine,
because it is a control condition rather than a point on the budget continuum.
**a**, Probability of complete decision recovery against compute budget for the three model tiers, with Wilson 95%
confidence intervals. The strong tier completes 19–20 of 20 runs at every budget from 75 to 250 CU; 75 CU (dotted blue
line) is the lowest stable threshold, 36% of policy D's. At 50 CU an affordability floor binds and completion falls to
13/20, although the winner and the decision pair are still recovered in 20/20 runs and only the reachability
classification fails. Neither weaker tier enters the strong regime at any budget tested.
**b**, The allocation mechanism. Left axis, the fraction of runs using narrow-window allocation, counted only when a run
builds a process window strictly smaller than the full 14,136-state admissible domain **and** completes at least one
scoped action against that window. The strong tier uses it in 20/20 runs from 50 to 175 CU and abandons it once the
budget covers full enumeration (1/8 at 200 CU; 0/20 at 225 CU; 0/9 at 250 CU; 0/20 under the non-binding allowance);
neither weaker tier uses it at any budget. Right axis, the median smallest window built, plotted as unconnected points
because the series is non-monotone with a maximum at 125 CU; it ranges over 633–1,950 states, 4.5–14% of the domain,
against no narrowing at all from 200 CU upward.
**c**, The upper cost boundary. Median decision-stable CU (the cumulative spend from which the full decision stays
correct to the end, computed from the environment ledger) against median final spend, with the shaded connector giving
the median post-stability overrun. Where the budget binds, the agent stops within 13–18% of its decision-stable point,
and at 225 CU essentially exactly there. Released to the non-binding allowance it still completes 20/20 and still stops
on its own rule, with no run reaching the 60-turn cap, but median final spend rises to 714 CU, 3.5× policy D's
threshold, and a median 148 CU is consumed after the decision is already complete (mean per-run post-stability share
33%, median per-run share 31%). The open marker is the single most extreme run at 3,021 CU, not a summary statistic.
A per-run audit of that cell confirms the decision itself is unchanged: 20/20 runs recover the canonical Ru→Fe parity
multiplier 201.2234429878984 and classify Ru as unreachable at the frozen 2.5246 scaling headroom, the multipliers being
numerically identical to the frozen reference within floating-point round-off (relative difference 9.89 × 10⁻¹⁶).
All CU figures are unweighted medians over the runs in each cell.

---

## Compliance with the spec's wording constraints

| constraint | satisfied by |
|---|---|
| non-binding 5000-CU allowance, never "unlimited budget" | used verbatim in the lead-in and in **c** |
| the two interventions reported separately | the interface arm is not in this figure; **a** shows the compute sweep only, and no combined "0/20" claim is made |
| "numerically identical within floating-point round-off", never "bit-exact" | stated in **c** with the 9.89 × 10⁻¹⁶ relative difference |
| 1.0899 not attributed to the non-binding cell | only 2.5246 is cited, which is the value that cell actually returns |
| 218 CU must name its cell | the number is not used in the caption; **c** cites only 714 CU and 148 CU, both from the non-binding cell |
| no universal or intrinsic compute saving | **c** states the 3.5× reversal explicitly |
| aggregation named | final sentence: unweighted medians; the 33% share is labelled a mean of per-run ratios |
| single-run extrema marked as such | the 3,021 CU open marker is called "not a summary statistic" |
