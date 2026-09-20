# Figure 10 — caption (2026-09-20 oracle update)

Asset: `F10_agent_capability_bounded_envelope.svg` (canonical), `.pdf`, `.png` (600 dpi).  
Data: `data/agent_figure_panel_data_2026-09-13.csv`, `analysis/supervisor_2026_09_20/agent_window_summary.csv` and `analysis/supervisor_2026_09_20/agent_oracle_summary.csv`.  
Renderer: `render_F10_agent_envelope.R` (current manuscript renderer; the older Python renderer is retained for provenance). Manifest will be regenerated after the R asset is rendered.  
Metric definitions: `docs/AGENT_METRIC_DEFINITIONS_SOURCE_OF_TRUTH_2026-09-13.md`.

## Caption

**Figure 10 | Adaptive compute allocation has a capability-bounded operating envelope.** All panels use the frozen DISCOVER V1 environment and the DISCOVER-BOUNDARY-C1 budget series. Unless noted, each cell contains *n* = 20 independent runs; the strong-tier 200-CU and 250-CU cells contain *n* = 8 and *n* = 9, respectively. The deterministic fixed-VOI policy D reaches the complete decision at 206 CU (dashed grey line). A complete decision requires the economic winner, decision pair and reachability verdict. In every panel the non-binding 5000-CU allowance is drawn on a separate axis with a dashed spine because it is a control condition rather than a point on the budget continuum.

**a**, Probability of complete-decision recovery against compute budget for the three model tiers, with Wilson 95% confidence intervals. From 75 to 250 CU, the strong tier completes every run at 75, 125, 150, 200, 225 and 250 CU, and completes 19/20 runs at 100 and 175 CU; the 200- and 250-CU cells are 8/8 and 9/9. The 75-CU point (dotted blue line) is the lowest tested stable complete-decision budget, 36% of policy D's 206-CU threshold. A deterministic oracle analysis gives a **22-CU protocol-complete S1-S3 minimum**, so the 75-CU allowance is 3.41× this scientifically complete lower bound; a separate **7-CU scorer-only floor** is retained as a diagnostic and is not used for manuscript normalization. At 50 CU an affordability floor binds and completion falls to 13/20, although the winner and decision pair remain correct in 20/20 runs and only the reachability component limits full completion. Neither weaker tier enters the strong-tier regime at the tested boundary budgets.

**b**, The allocation mechanism. Left axis, the fraction of runs using canonical narrow-window allocation, counted only when a run builds a process window strictly smaller than the full 14,136-state admissible domain and completes at least one scoped action against that window. The strong tier uses this mechanism in 20/20 runs from 50 through 175 CU, 1/8 at 200 CU, 0/20 at 225 CU, 0/9 at 250 CU and 0/20 under the non-binding allowance; neither weaker tier uses it in the measured cells. Right axis, the median smallest window built, plotted as unconnected points because the series is non-monotone; it ranges from 633 to 1,950 states (4.5–14% of the full domain) in the narrowed regime.

**c**, The upper cost boundary. Median decision-stable CU (the cumulative spend from which the complete decision remains correct to the end, computed from the environment ledger) is shown against median final spend; the connector gives the median post-stability overrun. The **22-CU protocol-complete oracle** is shown as the irreducible scientific reference. At the strong 75-CU cell, median decision-stable spend is 52.5 CU, or 2.39× oracle; policy D's 206-CU threshold is 9.36× oracle. Where the budget binds, the agent stops close to its decision-stable point. Under the non-binding allowance, canonical narrow-window use is 0/20 and median decision stability shifts to 566 CU, or 25.73× oracle, before a further median 148 CU is spent; median final spend is 714 CU. Thus the non-binding failure mode begins with loss of search compression, not only with post-stability overspending. The agent still completes 20/20 runs and stops on its own rule, with no run reaching the 60-turn cap. The mean per-run post-stability share is 33% and the median per-run share is 31%. The open marker at 3,021 CU denotes the single most extreme run rather than a summary statistic. A per-run audit confirms that the scientific decision is unchanged: 20/20 runs recover the canonical Ru→Fe parity multiplier 201.2234429878984 and classify Ru as unreachable at the frozen 2.5246 scaling headroom, with the multiplier numerically identical to the frozen reference within floating-point round-off (relative difference 9.89 × 10⁻¹⁶). All CU summaries are unweighted medians over runs unless otherwise stated.

## Wording constraints retained

- use **non-binding 5000-CU allowance**, not “unlimited budget”;
- report interface and compute interventions separately;
- use **numerically identical within floating-point round-off**, not “bit-exact”;
- do not attribute 1.0899 headroom to the non-binding cell;
- do not describe the Agent result as universal or intrinsic compute saving;
- identify single-run extrema as single runs rather than summary statistics;
- use **22-CU protocol-complete oracle** for manuscript normalization; keep 7 CU labelled as the scorer-only floor.
