# Figure 6 — composite

Decision-aware agents make the multiscale decision framework repeatedly executable.
183 × 168 mm, seven panels: `Fig6.{svg,pdf,png}`.

| Panel | Content | Source |
|---|---|---|
| a | the agent: a language-model policy (strong, mini, nano tiers) chooses typed actions priced in compute units; deterministic S1–S3 tools on frozen NH3-FINAL-1.1 do all physics and economics; a ledger and scorer define the complete decision | `provenance/discover_v1/source_harness/DISCOVER_COST_MODEL_V1.json` (CU prices) |
| b | three chains to the same complete decision: the 22-CU protocol oracle, one strong-tier run at the 150-CU allowance (102 CU; Fe found at 65 CU; windows of 1,302 and 1,784 states), and fixed policy D (full 14,136-state window at 111 CU; decision at 206 CU, 214 CU spent) | `fig6_trajectories.csv` from `fig6_data.py` |
| c | complete-decision recovery against allowance for the three tiers, Wilson 95 % band for the strong tier; non-binding 5,000 CU: 20/20 | `data/agent_figure_panel_data_2026-09-13.csv` |
| d | runs using a narrow window and the median smallest window built; non-binding: 0/20 | same, `analysis/supervisor_2026_09_20/agent_window_summary.csv` |
| e | median decision-stable and final spend against allowance, with the 22-CU oracle and D's 206 CU; non-binding 566 and 714 CU | `data/agent_figure_panel_data_2026-09-13.csv` |
| f | spend in units of the 22-CU protocol oracle: 2.39×, 3.41×, 9.36×, 25.73× | `analysis/supervisor_2026_09_20/agent_oracle_summary.csv` |
| g | action errors and empty turns by layer at 175 CU, 20 runs per cell, including the mini tier's typed-interface arm | `data/discover_boundary_c1_error_taxonomy_summary.csv` |

## Trajectories

`fig6_data.py` reads two committed traces and the oracle record and checks each against the ledger
summaries before writing `fig6_trajectories.csv`:

- strong tier, `data/discover_boundary_c1/runs/gpt-5.5-2026-04-23/traces/anonymous/E_llm_agent_anonymous_B150_r1_c1_20260909T124030Z` — 31 steps, 102 CU spent, stable correct winner at 65 CU and complete decision at 102 CU, as in `data/discover_boundary_c1_runs.csv`;
- fixed policy D, `data/discover_boundary_c1/D_reference/traces/anonymous/D_fixed_voi_anon_B225_s0_c1_20260908T102449Z` — 214 CU spent, complete decision at 206 CU, as in `data/discover_boundary_c1_D_reference.csv`;
- protocol-complete oracle, `analysis/supervisor_2026_09_20/agent_oracle_min_cu.json` — 22 CU.

The strong-tier run is one of the 20 runs in its cell, chosen because its trace is in the repository
and it builds a narrow window; panels c–f carry the cell statistics.

## Build

```
pur_bridge_env/python   fig6_data.py      # traces -> fig6_trajectories.csv
pur_bridge_env/python   make_fig6.py      # -> Fig6.svg / .pdf / .png
```
