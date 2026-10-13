# NH₃ frontier provenance: committed sources for the kinetics-swap and staged-converter frontier numbers (2026-10-13)

Exploratory analysis. Gives committed outputs for numbers so far computed only in an independent check. It imports the
merged PR #75 code (`analysis/nh3_staged_converter_2026_10_12/`: `kinetics_swap.py`, `converter.py`, `kinetics.py`,
`run_staged.py`) unchanged. No manuscript text, figure, frozen output or existing analysis folder is changed.

**Reproduction gate.** `frontier_swap.py` first re-runs the committed headline variant (NH3-FINAL-1.1 states, plug flow,
measured rates) with `kinetics_swap.evaluate()` and stops unless it matches `kinetics_swap.json`. The match: Fe 15.58 USD/t
at 425 °C/170 bar; benchmark Ru 28.07 at 325 bar; parity multiple 24.6×; supported Ru/C − Fe −1.36/+1.12 globally and
−1.07/+1.86 in the KAAP-type loop at 0/12 %/y. All matched to 1e-5. `staged_window.py` first re-optimises the committed KAAP-type
cash-flow optima at 0 and 12 %/y (`arrangements.csv`). All 8 match within 5e-7 USD/t (`staged_window.json`,
`committed_check`).

Conventions are those of PR #75: supported Ru/C at 8 wt% Ru, 490 kg m⁻³ and 95.55 % recovery, Ru 53,852.5 USD/kg. Metal is
charged by the owned-metal 25-year cash flow at financing rate i, with Fe on the same convention. The KAAP-type loop is
90 bar with a −20 °C separator. Costs are in USD per tonne NH₃.

## Numbers and their output files

### 1. Break-even Ru inventory financing rate (supported Ru/C = Fe) — `frontier_swap.json` → `1_breakeven_financing_rate`

| Recovery | Global optimum | KAAP-type loop |
|---|---|---|
| 95.55 % (headline) | **3.35 %/y** (both 15.61 USD/t; Ru/C at 165 bar, Fe at 170 bar) | **2.34 %/y** (19.38) |
| 90 % | **2.75 %/y** | **1.71 %/y** |

The 95.55 % values match the independent check (3.35 and 2.34 %/y).

### 2. Supported Ru/C optimum pressure — `frontier_swap.json` → `2_RuC_optimum_pressure`

- 0 %/y: **145 bar** (400 °C). It stays at 145 bar for each one-at-a-time variation: bed density 430/550 kg m⁻³,
  recovery 90 %, Ru price ×0.7/×1.3. Over all 18 combinations it ranges from 145 to 165 bar; 165 bar (425 °C) occurs
  only at r 90 % with Ru ×1.3.
- 12 %/y: **190 bar**. One-at-a-time the range is 190–195 bar (195 only at Ru ×1.3); over all combinations it is also
  190–195 bar.
- The KAAP-type loop is fixed at 90 bar.

### 3. Ru-price parity, benchmark formulation — `frontier_swap.json` → `3_Ru_price_parity_benchmark`

- With measured kinetics, the benchmark Ru reaches parity with Fe (15.58) at **2,089 USD/kg Ru** (425 °C, 165 bar,
  1.23 m³ bed).
- The same price sweep on the frozen descriptor kinetics gives 163.763 USD/kg. This reproduces the manuscript's
  163.76.
- The benchmark Ru best cost restricted to 100–200 bar is **29.08** (450 °C, 200 bar, 25 °C separator), +1.01 above its
  325-bar optimum.

### 4. Parity activity multiple — `frontier_swap.json` → `4_parity_multiple`

| Dispersion ratio u | 5.5 | 11 (headline) | 22 | 50 |
|---|---|---|---|---|
| Multiple | 12.3× | **24.6×** | 49.3× | 112.0× |

The multiple is exactly proportional to u, because Ru mass and bed volume both scale as u/α.

| Converter pressure premium | ×0 | ×0.5 | ×1 | ×2 |
|---|---|---|---|---|
| Fe optimum (USD/t) | 13.71 | 14.93 | 15.58 | 16.39 |
| Multiple | **166.5×** | 45.4× | 24.6× | 11.0× |

### 5. Robustness of the 0 %/y and 12 %/y signs — `frontier_swap_robustness.csv`, `frontier_swap.json` → `5_robustness`

There are 16 cases: the base case plus 15 variations, as listed below.

- Fe catalyst price ×0.5/×2
- Ru/C bed density 430/550 kg m⁻³
- Recovery 90 %
- Ru price ×0.7/×1.3
- Catalyst life 5/15 y
- Effectiveness factor 0.5 for Fe, or for Ru/C
- Converter premium ×0/×0.5/×2
- Inlet-rate sizing instead of plug flow

| | Global | KAAP-type loop |
|---|---|---|
| Fe ahead at 12 %/y | **16 / 16**, smallest gap +0.18 (Fe effectiveness 0.5) | **16 / 16**, smallest +0.73 (Fe effectiveness 0.5) |
| Ru/C ahead at 0 %/y | **16 / 16**, smallest lead −0.18 (converter premium ×0) | **15 / 16**; exception inlet-rate sizing, +0.07 (next: premium ×0, −0.01) |

Break-even rates across the cases are 0.09–10.6 %/y globally and 0.02–6.2 %/y in the KAAP-type loop. The low ends
come from converter premium ×0 and the high ends from Fe effectiveness 0.5. Inlet-rate sizing has no KAAP break-even
because Ru/C is already dearer at 0 %/y. Source: CSV columns `breakeven_*`.

**Decomposition of the 0 %/y global gap** (Ru/C 14.24 at 400 °C/145 bar vs Fe 15.60 at 425 °C/170 bar):

| Term | Ru/C − Fe |
|---|---|
| Process (compression energy, compressor CAPEX, refrigeration) | −0.90 |
| Converter (vessel proxy + pressure premium) | −0.74 |
| Metal | +0.28 |
| **Total** | **−1.36** |

### 6. Staged converter, KAAP-type loop (owned cash flow, 95.55 %) — `staged_window.json`, `staged_direct.csv`, `staged_scan.csv`

The window is the range of financing rates in which Fe-first, Ru/C-downstream staging is the optimum. Below it all-Ru/C
is optimal; above it all-Fe is. Each edge is found by direct global optimisation: differential evolution plus
Nelder–Mead for all four arrangements (FFF, FFR, FRR, RRR) at five rates spaced 0.25 %/y around the edge, then linear
interpolation between the two bracketing rates. A 0.5 %/y continuation scan is reported alongside; it agrees within
0.03 %/y.

| Case | Window (direct) | Scan |
|---|---|---|
| Base (Ru/C ≤ 460 °C, Fe ≤ 530 °C) | **0.82–6.70 %/y** | 0.82–6.71 |
| Ru/C cap 480 °C | **2.11–7.93** | 2.11–7.93 |
| Ru/C cap 500 °C | **3.96–8.10** | 3.95–8.12 |
| Both catalysts capped at 460 °C | **2.86–6.78** | 2.85–6.79 |
| Ru/C without H₂ inhibition (rescaled ×0.5716) | **0.67–5.43** | 0.67–5.43 |
| Recovery 90 % | **0.13–6.18** | 0.13–6.19 |
| Ru price ×0.7 | **1.42–10.11** | 1.42–10.12 |
| Ru price ×1.3 | **0.50–4.95** | 0.50–4.96 |

For the case without H₂ inhibition, K_H₂ is set to 0 and the rate is rescaled to the fitted Rossetti rate at 400 °C,
90 bar, 2 % NH₃, H₂/N₂ = 3.

**Ru/C share of catalyst volume across the base window** (direct optima): 56 % (FRR) at the lower edge, 48 % at
1.35 %/y, 39 % at 2.10 %/y, 30 % at 3 %/y and 22 % at 4 %/y. It then drops to FFR at 6.9 % at 5.10 %/y and 4.3 % at
6.46 %/y, just below the upper edge. In the other cases it falls from 28–56 % just above the lower edge to 4–5 % (FFR) just below the
upper edge. The exception is the 500 °C cap, where the optimum stays FRR, at 18 %, up to the edge.

**Savings over all-Fe, base case** (`staged_window.json` → `base_savings_vs_all_Fe`):

| Financing | Optimum | Cost | all-Fe | Saving |
|---|---|---|---|---|
| 1.35 %/y | FRR, Ru/C 48 % | 17.90 | 18.68 | **0.78** |
| 2.10 %/y | FRR, Ru/C 39 % | 18.09 | 18.68 | **0.60** |
| 5.10 %/y | FFR, Ru/C 6.9 % | 18.61 | 18.71 | **0.10** |

The direct edges supersede the design-library envelope of PR #75 (0.8–6.7 %/y), which they confirm.

## Files and rerun

| File | Content |
|---|---|
| `frontier_swap.py` | Items 1–5. Asserts the committed headline, then writes `frontier_swap.json` and `frontier_swap_robustness.csv` (about 10 s). |
| `staged_window.py` | Item 6: scan, direct edges and base-case points. Writes `staged_scan.csv`, `staged_direct.csv` and `staged_window.json` (about 72 min on 4 workers). |
| `check_outputs.py` | Compares a rerun with the committed outputs: swap within 1e-6, edges within 0.2 %/y, savings within 0.02 USD/t. |
| `nh3_1_2/` | NH3-FINAL-1.2 (`NH3_MODEL=1.2`): the same scripts and file names; key numbers 1.1 → 1.2 in `nh3_1_2/README.md`. |

    python3.12 -m venv /tmp/v && /tmp/v/bin/pip install -r requirements.txt pyyaml
    cd analysis/nh3_frontier_provenance_2026_10_13
    /tmp/v/bin/python frontier_swap.py
    /tmp/v/bin/python staged_window.py --workers 4

Workflow `.github/workflows/nh3-frontier-provenance.yml` reruns both scripts on a pull request touching this folder. It
compares the rerun with the committed outputs and checks that `provenance/`, the PR #75 folder, `docs/` and `figures/`
are untouched.

Notes:

- The PR #75 kinetics swap and the staged converter read the NH3-FINAL-1.1 manifest and workbook from `provenance/`
  directly. They compute the frozen Fe/Ru descriptor vectors with `frozen_state_logtof`, so no prebuilt harness response
  cache (`build_harness_root.py`) is needed; the PR #75 workflow does not build one either.
- Case switches act on the imported modules only inside this run. These switches are the Fe temperature cap
  (`converter.PAR['process']['T_max_Fe_C']`) and the Ru/C rate function (`kinetics.rate_ru_rossetti`). The source files
  are not edited.
- The supported Ru/C metal charge in the kinetics swap carries no support charge, as in PR #75. The staged converter
  adds an 8 USD/kg support charge, as in PR #75.
