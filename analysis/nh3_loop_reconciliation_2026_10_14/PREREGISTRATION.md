# NH3 loop reconciliation — preregistration (2026-10-14)

Committed before any result of this folder is computed. Every quantity listed here is reported whatever its direction.
Any change of a grid, rule or reported quantity after the first result is computed goes into a dated, labelled
addendum at the end of this file; nothing above the addendum line is edited after commit.

## Scope and fixed inputs

- Base: `main` at `bee539d`. Nothing under `docs/`, `data/`, `provenance/`, `figures/`, `source_data/` or any existing
  `analysis/*` folder is edited. Upstream code is imported read-only:
  - canonical model: `provenance/nh3_final_1_2/source_harness/harness_core.py`, manifest
    `configs/nh3_final_1_2.yaml` (loaded through `analysis/nh3_model.py`, `NH3_MODEL=1.2`);
  - measured-kinetics swap on canonical states: `analysis/nh3_staged_converter_2026_10_12/kinetics_swap.py`;
  - closed loop: `analysis/nh3_si_closed_loop_v1/` (via `analysis/nh3_kinetic_cost_coupling_v1/coupling.py`),
    economics `analysis/nh3_kinetic_cost_coupling_v1/economics.py`, rate laws
    `analysis/nh3_kinetic_cost_coupling_v1/kinetic_bridge.py`;
  - #93 / #94 studies: `analysis/nh3_kinetic_cost_coupling_v1/run_study.py`,
    `analysis/nh3_fe_first_domain_v1/source_domains.py`, rerun unchanged.
  Git blob hashes of every imported file are written to `outputs/provenance.json`.
- Frozen NH3-FINAL-1.2 numbers (Fe 11.516 / Ru 16.633 / Os 19.747 USD/t; 32/64 benchmark) are not changed. Every variant
  below is a labelled sensitivity.
- Price bases of the closed loop (decision-relevant cost = loop cost minus the common stoichiometric-feed floor, as in
  #93/#94; equipment annualised at 12%/y over 25 y; catalyst life 10 y; Ru 53,852.5 USD/kg; Fe catalyst 8 USD/kg;
  Ru/C support 8 USD/kg; 1500 t/d recovered NH3; 90 m³ bed cap):
  - **B94**: H₂ 3 USD/kg, N₂ 0.06, CH₄ 0.20, Ar 0, metal finance 12%/y, Ru recovery 90%.
  - **B93**: H₂ 2 USD/kg, N₂ 0.10, CH₄ 0.20, Ar 0, metal finance 12%/y, Ru recovery 95.55%.
  - Feasibility rules in T2–T5 for both bases: bed (or total converter) volume ≤ 90 m³, reactor-inlet inerts ≤ 15 mol%
    (the #94 rule), outlet below hot equilibrium, positive rate on the whole bed path. Numerically unresolved cold states
    are retained as UNRESOLVED and never counted as infeasible or as a win.
- Closed-loop Ru/C is the measured 3.2 wt% promoted Ru/C at 590 kg/m³ (closed-loop formulation, unchanged). Canonical
  supported Ru/C is 8 wt% at 490 kg/m³ with the measured activity per kg Ru (manuscript formulation, unchanged).

## T1. Canonical recycle-rise sensitivity

- Model: canonical NH3-FINAL-1.2 deterministic 15-metal optimisation (`NH3Harness.deterministic`, descriptor kinetics,
  14,510-state grid), with `process.recycle_pressure_rise_bar` = **3.0 (replay control), 6.0, 9.2**. Only the recycle
  compression electricity and its compressor CAPEX change; the process-state set must stay identical (asserted).
- All 15 metals. MC draws and scaling reachability are not rerun (not part of T1).
- Replay gate: at 3.0 bar Fe / Ru / Os costs and optima equal `results.json` to 1e-9 USD/t and the Ru parity multiple
  equals 114.667125 to 1e-6; if the gate fails, T1 is reported as failed.
- Reported for each rise: every metal's feasible cost, optimum T / P / Tsep, bed volume (or "no feasible state"),
  unconstrained cost; feasible economic ranking; Spearman of the 15-metal censored economic ranks against the frozen
  censored ranks and of the raw (unconstrained) economic ranks against the frozen raw ranks; the canonical
  activity-vs-economics raw and censored Spearman; Ru − Fe; Ru − Os; Ru parity activity multiple (brentq on the Ru
  activity multiplier, as `backward_and_reachability`).

## T2. Matched-pressure Fe vs Ru/C in the closed loop

- Pressures: **90, 100, 120, 140 bar** (Fe below 151 bar = 149 atm is outside the Dyson–Simon fit: every Fe row is
  labelled `engineering_TP_extrapolation`; Ru/C above 100 bar likewise).
- Grid at each pressure (union of the #93 and #94 grids): hot T ∈ {400, 425, 445, 450} °C;
  per-pass N₂ conversion X ∈ {0.08, 0.10, 0.12, 0.14, 0.20, 0.225, 0.25, 0.275, 0.35}; cold flash T2 ∈ {−20, −10, 0, 10} °C;
  purge ∈ {0.0075, 0.01, 0.015, 0.03}. 144 cold states per pressure; cold-loop pressure drop 9.2 bar as in #93/#94.
  Each catalyst picks its own T, X, T2, purge (isothermal inverse-PFR bed, as #93/#94).
- Reported per pressure and per basis (B94, B93): decision cost of Fe and Ru/C with their T, X, T2, purge, bed, inlet
  inerts and NH₃; Ru − Fe; term decomposition of Ru − Fe: excess feed split into purge-gas loss, dissolved-gas loss,
  NH₃ lost in purge and identity residual; utilities; catalyst inventory; reactor capital; compressor capital; hot duty
  (0 by basis). Ru/C metal-finance crossover rate on [0, 12%]/y (equipment fixed at 12%, both catalysts reoptimised at
  every rate on the same pressure): scan at 0.25%-points, then brentq to 1e-6; all sign changes reported; otherwise the
  winner over the whole interval. Counts of feasible, inert-capped and unresolved candidates.

## T3. Model bridge

- Points: (a) manuscript measured-kinetics optima on canonical 1.2 states (plug flow, measured rates, 25-y cash flow,
  r 95.55%): Fe 450 °C / 140 bar / 30 °C and supported Ru/C at its 0%/y optimum (~105 bar) and 12%/y optimum; recomputed
  with `kinetics_swap.evaluate` (gate: Fe 14.925644 USD/t, Ru/C − Fe −3.4634 at 0%/y and +1.452 at 12%/y, to 1e-3).
  (b) #94 closed-loop source-window optima (gate: Fe 41.634, Ru 82.636 USD/t to 1e-3); (c) #93 closed-loop optima at
  220 bar (gate: Fe 47.245, Ru 49.484 to 1e-3). Gates failing → reported, bridge still computed on recomputed values.
- Canonical side at any point: the canonical 1.2 self-consistent state at that T, P and Tsep (closed-loop cold T2 used as
  Tsep), measured-kinetics plug sizing, manuscript Ru/C formulation and cash-flow accounting; recycle rise 3.0 bar
  (native) and 9.2 bar.
- Closed-loop side at a manuscript point: T and P fixed to the manuscript value, X, T2, purge reoptimised on the T2 grid
  (cold states also computed at 105 and 150 bar for this purpose), basis B94 (and B93).
- Common cost categories (both models): catalyst inventory, reactor capital, loop utilities (compression +
  refrigeration electricity), compressor capital. Closed-loop-only: excess feed (purge-gas loss, dissolved-gas loss, NH₃
  in purge, residual) and hot duty. Real-gas VLE separation is not a separate cost term in either model; it is reported
  as a diagnostic (reactor-inlet NH₃ and inerts of each point in each model).
- Reported: Ru − Fe by category for every point × model; a pre-ordered waterfall from the manuscript +1.45 to the #94
  +41.0: S0 canonical pair (a) [r 95.55%, 12%] → S1 canonical pair (b) → S2 canonical pair (b) r 90% → S3 canonical
  pair (b) r 90%, recycle rise 9.2 bar → S4 closed loop pair (b) B94; plus the closed loop at pair (a) (S5, B94) so that
  the model effect and the pair (pressure-separation) effect are reported in both orders; each step split by category.
  Statement of the categories that explain the gap.

## T4. KAAP-type staged converter in the closed loop at 90 bar

- The manuscript converter (`converter.py`) is tied to its own loop (H₂/N₂ = 3, inerts split, Raoult separator); it is
  not reused. Labelled **simplified series-PFR**: three adiabatic beds in series with indirect interbed cooling back to
  one common inlet temperature T_in ∈ [350 °C, T_max(bed 1) − 1], same rate laws as the closed loop
  (`kinetic_bridge.rate_m3`: Fe KM1, 3.2 wt% Ru/C at 590 kg/m³), ideal-gas Shomate enthalpies from `kinetic_bridge`,
  isobaric; T_max Fe 530 °C, Ru/C 460 °C; every bed path below hot equilibrium. Bed extents set by two split fractions;
  total extent and feed from the closed-loop cold state (inverse design, as #93).
- Loop states: the 144 cold states of the T2 grid at 90 bar. Patterns: FFF (all-Fe), RRR (all-Ru/C), FFR and FRR
  (Fe-first staged), RFF and RRF (Ru/C-first, checked only).
- Optimisation: per (state, pattern, rate) coarse grid on (T_in step 10 °C, f1, f2 ∈ {0.2, 0.35, 0.5, 0.65, 0.8}) then
  Nelder–Mead; direct optimisation at Ru finance 0, 1, …, 12%/y under B94; the optimised designs form a library whose
  lower envelope gives the boundaries (bisection, 0.01%-point) and the B93 decisions (labelled envelope-derived).
- Reported: for each integer rate 0–12%/y (B94) the cost of all-Fe, all-Ru/C, best Fe-first, best Ru/C-first and the
  winning configuration with its Ru/C volume share; the rate boundaries between winning configurations under B94 and
  B93. Reference: isothermal single-bed all-Fe / all-Ru/C at 90 bar from T2.

## T5. Industrial plausibility check

- Sources in the repository only (`docs/RU_ACTUAL_CATALYST_COST_2026-10-05.md`): KAAP energy saving ≈ 1.17 GJ/t versus Fe
  loops (Humphreys 2021); ZA-5 loop recycle compression 21.5 kWh/t at 10 MPa and 17.5 at 30 MPa, refrigeration 22.6 and
  13.4 kWh/t (Humphreys 2021 citing Liu 2013). No cost difference is given numerically in the repository (KAAP "lower loop
  CAPEX" is qualitative) → no cost comparison.
- Reported: closed-loop recycle-compression kWh/t, refrigeration kWh/t and total loop electricity (GJ/t) of the B94
  optima: all-Fe and staged at 90 bar (T4), Fe and Ru/C at 100 and 140 bar (T2), Fe at 160–220 bar (#93 grid);
  difference (best conventional all-Fe at 140–220 bar) − (KAAP-type 90 bar optimum) in GJ/t against +1.17 GJ/t (sign and
  ratio only); 90–100 bar values against the 10-MPa ZA-5 values and 140–220 bar values against the 10–30 MPa range.

## Outputs

`outputs/`: `t1_*.csv/json`, `t2_*.csv/json`, `t3_*.csv/json`, `t4_*.csv/json`, `t5_*.json`, `cold_states.json`,
`provenance.json`, `summary.json`, and `REPORT.md` in this folder. CI: `.github/workflows/nh3-loop-reconciliation.yml`
reruns everything, runs `pytest`, and fails if a recomputed reported cost differs from the committed one by more than
0.01 USD/t (T1: 1e-9), a crossover or boundary rate by more than 0.05 %-point, or a winner changes; the CI outputs are
uploaded as artifacts.

---
Addenda (dated, labelled) below this line.
