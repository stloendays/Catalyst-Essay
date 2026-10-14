# NH3-STREAM-V0: source-matched ammonia loop accounting

**Project status:** observation-constrained, non-calibrated *material balance and stream-boundary audit*. It is **not** a complete new process simulator, a ranking model, or an improvement to the original 64-case validation score. No original manuscript or NH3-FINAL-1.2 files are modified.

## Full five-component industrial steady-state reconstruction (preferred analysis)

The source-matched **NH3-STREAM-V0.2** method uses the full *printed* industrial
Krupp-Uhde Figure 57 from Appl, *Ammonia, 2. Production Processes* (2011),
doi:10.1002/14356007.o02_o11, p. 211, comprising **12 numbered streams**,
their molar flow, temperature, pressure and **N2/H2/CH4/Ar/NH3** mole percentages.
Every row is pinned in `figure57_streams.csv`; its overlapping numbers are
also independently cross-checked against the existing frozen literature ledger.

`species_reconstruct.py` applies the reaction stoichiometry and component-flow
conservation to **nine steady-state control volumes**, reporting **45 species
residuals**. It reproduces, using direct component-flow differences:

- **1499.36 t/d** NH3 generation from converter stream 1 -> 4 compared with
  **1500.24 t/d** recorded NH3 liquid product in stream 8: **-0.059%**.
  The prior total-flow/equilibrium-stoichiometry method gives 1499.61 t/d;
  their **0.26 t/d** difference follows from independently rounded printed values.
- First separator stream 5 NH3 **8.502 mol%** reconstructed from all five
  species of stream 4 minus separated liquid stream 7, versus **8.51 mol%** source.
- The largest absolute species residual among 9 boundaries is **0.0489% of
  the feed flow to the corresponding unit/control volume**. This is a source
  internal balance test, not a new engineering accuracy claim.
- Source liquid stream 7 is **3060 kmol/h at 98.55 mol% NH3**, and stream 8
  **3678 kmol/h at 99.82 mol% NH3**. The printed **51.36 and 62.51 t/h**
  are close to the directly calculated *NH3-component* liquid mass rates;
  they should not be interpreted as unqualified pure-stream total masses.
- Both separate source gas temperatures/pressures are now directly read
  from the **full printed gas rows**: gas 5 **21 C, 180.2 bar** and gas 6
  **0 C, 178.8 bar**. BASF 1:3 N2/H2 source table interpolation at these
  conditions gives **8.108%** versus 8.51% source and **4.097%** versus 4.18%
  source. The real mixture contains inerts; these data are not a validated
  five-component EOS.
- The source stream 6 -> 1 pressure difference is **9.2 bar**.
  Neither fresh-gas compression nor staged recycle compressor performance
  can be inferred solely from that two-point pressure difference.

Source-based **steady-state process reconstruction** is the appropriate term
for this calculation. Inputs are printed industrial streams, the outputs are
conservation-implied cross-stream quantities, and catalyst kinetics, true
multi-component VLE, heat exchanger duty, equipment efficiency and plant cost
are **not fitted or independently predicted**. It therefore does not supersede
the NH3-FINAL-1.2 32/64 industrial benchmark.

The earlier `source_matched.py` is retained as the simpler NH3-only
projection for reproducibility of the first feasibility audit.
Its pure-NH3-liquid approximation must not be conflated with the preferred
five-species calculation.

Run:
`python analysis/nh3_source_matched_loop_v0/species_reconstruct.py --out-dir artifacts/nh3-source-matched/species`

Primary artifacts: `species/REPORT.md`, `species/component_balance_9.csv`,
`species/component_residuals_45.csv`, `species/species_summary.json`.

---

## Scope and evidence hierarchy

The frozen industrial ledger lives at `analysis/validation_nh3_plant_2026_10_13/reference_values.csv`. The new solver enforces source blob hashes, loads every numeric input from its original row ID, and distinguishes source observations from calculations and conditional routing assumptions.

| Case | Source | Resolution | Independence |
|---|---|---|---|
| TOP140 | Dybkjaer 1995 Table 6.1 | Converter inlet/outlet flow, NH3/inerts, plant capacity | Same publication/table as TOP220 |
| TOP220 | Dybkjaer 1995 Table 6.1 | Same as TOP140 | NOT a separate source study |
| UHDE188 | Appl 2011 Ullmann Part 2, Figure 57 | Stream 1 and 4, separator gas 5/6, liquids 7/8, makeup 10/12, H2 recovery 11, fuel 9 | One independently described industrial flowsheet |

Appl 2011 Table 16 reprints the Dybkjaer operating data. The program verifies their source-row equality and **does not count these reprints as independent validation samples**.

## Conserved chemistry without any kinetic/activity model

For `N2 + 3H2 -> 2NH3`, the total gas flow decreases by one mole per new mole NH3. At source-reported converter inlet and outlet:
`A_new = F_in*(y_NH3,out - y_NH3,in)/(1+y_NH3,out)`.
This remains valid with inert gas if there is no unreported gas addition/removal inside the selected converter boundary. It is a source **internal-consistency identity**, not a prediction of catalyst rate or industrial design.

The Uhde stage-1 liquid balance assumes R0014 stream 7 is pure NH3. R0002 product stream 8 is annotated as 99.82 mol% NH3, but its unknown impurity molecular weights prevent exact conversion of a **total-liquid mass** into ammonia moles. Estimated closure percentages should therefore be viewed as **approximate**.

## Source-matched temperature and pressure boundaries

The old benchmark used a surrogate `T_REF=448 C` for the Uhde overall-state comparison. The source Figure 57 has distinct stream/b ed temperatures: stream1 enters vessel at **295 C**, first catalytic bed at **390 C**, third bed at **401 C**, and stream4 is cooled to **336 C** *after* the downstream waste-heat boiler. Do **not** identify any of these as a single reactor isothermal temperature.

- Stream 5, NH3 8.51%, T 21 C (R0014). For the VLE comparison the pressure **180.2 bar** is inferred from same-vessel liquid stream 7; it is not a separate measured gas-5 pressure row.
- Stream 6, NH3 4.18%, T 0 C, P **178.8 bar** (R0015 source annotation). Stream 1 also has NH3 4.18%; their exact makeup/flash/recovery order is not fully specified in numeric ledger notes.
- Source stream6 -> stream1 pressure difference **9.2 bar**, versus 3.0 bar in the canonical simplified loop. The script reports an *ideal-gas reversible-isothermal cold-stream lower bound* only, never a whole-plant compressor prediction.
- BASF Table 5 (1:3 N2:H2 saturated vapor) provides independently recorded gas-mixture equilibrium reference, but the Uhde reactor feed contains **11.09 mol% CH4+Ar**. The agreement at two separator stages does not validate a 5-component EOS.

## Topology counterexample

When source stream 6 y_NH3 = stream 1 y_NH3 = 4.18% and combined NH3-free make-up stream 12 contributes 8,041 kmol/h, the hypothesis that **all** stream 12 enters the converter **after** a final gas already at 4.18% NH3 necessarily predicts a lower-than-observed feed concentration. Thus that simplistic topology is inconsistent with its own assumptions. It does not establish the real injection point; another stage, purge, mixing and hydrogen-recovery arrangement can be present.

The source-internal gas/liquid and product flows show a close overall balance only after accounting for stream 9 fuel, recovered-H2 stream 11 and stream 10 make-up; the paths and partial NH3 recovery remain uncertain. No pressure drop or separator-efficiency parameter is adjusted to close residuals.

## Run via GitHub Actions

Workflow: `.github/workflows/nh3-source-matched-loop.yml`. It uses **only Python 3.12 standard library**, plus pre-existing pinned audit utilities. On push/PR it runs retrospective unit tests and writes:

- `REPORT.md`: evidence-tiered scientific account and two-stage separator comparison
- `converter_source_3.csv`: three converter boundary mass balances and source dependency labels
- `uhde_stream_closure.json`: source pressure/temperature/product/recovery and topology diagnostics
- `summary.json`: machine-readable aggregate with explicit status `NOT_INDUSTRIAL_SIMULATOR`

Local:
`python analysis/nh3_source_matched_loop_v0/source_matched.py --out-dir artifacts/nh3-source-matched`
`python -m unittest discover -s analysis/nh3_source_matched_loop_v0 -p 'test_*.py' -v`

## Next acceptance gate

Before any updated NH3-FINAL physics, Fe/Ru/Os re-optimization or revised manuscript headline: (1) independently inspect the source **Figure 57** piping and stage pressure/makeup points, (2) map each measured gas/liquid stream with species/mass and energy accounting, (3) externally evaluate high-pressure NH3/H2/N2/CH4/Ar separator VLE without selecting equations on validation targets, (4) measure held-out physical states across a second complete flowsheet, (5) then re-evaluate process/economic ranks. No claim of hold-out performance from retrospective consistency checks. See [issue #88](https://github.com/stloendays/Catalyst-Essay/issues/88) and upstream [audit PR #87](https://github.com/stloendays/Catalyst-Essay/pull/87).
