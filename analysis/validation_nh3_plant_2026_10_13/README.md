# The latest NH3 plant model against industrial ammonia plants — 2026-10-13

Question: does the latest ammonia plant model behave like a real ammonia synthesis loop, and does its optimum land
where industry builds plants? Latest model = NH3-FINAL-1.1 process states with the measured fused-Fe (Dyson & Simon
1968) and Ru/C (Rossetti 2006) rate laws, plug-flow sizing (`analysis/nh3_staged_converter_2026_10_12/`, imported
unchanged; headline Fe optimum 15.58 USD/t at 425 °C, 170 bar, 30 °C). This is the ammonia counterpart of
`analysis/meoh_plant_benchmark_2026_10_06/`.

The 64 comparisons, their tolerances and the industrial windows were committed in `PREREGISTRATION.md` (commit
`b11133c`) before any comparison was run. None was changed afterwards.

**Verdict: 14 of 64 pre-registered comparisons pass.**

| Table | What is compared | Pass |
|---|---|---:|
| A | NH3-FINAL-1.1 loop state at each plant's own P, T, separator temperature and capacity (13 loop records) | 1/28 |
| E | compressor power (3 plants) | 1/3 |
| B | converter model with measured kinetics: the plant's own converter (forward, inverse), minimum-volume duty, cost-optimal designs, KAAP layout | 5/20 |
| C | revealed design: Fe optimum vs industrial Fe-loop windows; where Ru/C enters vs industrial Ru deployment | 7/12 |
| V | separator vapour NH3 vs the BASF saturation table | 0/1 |
| **all** | | **14/64** |

Secondary column, not counted: PR #77 (`analysis/nh3-final-1-2-candidate-20261013`, commit `ab9c294`, Gillespie–Beattie
standard Gibbs energy with Newton–Cooper reaction fugacities in the loop equilibrium, 50–300 bar) passes **24 of the 38**
comparisons it changes. Converter-level and staged results are identical in both columns.

**Model-upgrade re-score, NH3-FINAL-1.2: 32 of 64** (same 64 comparisons, tolerances and windows; the registered
NH3-FINAL-1.1 verdict above stays 14/64). NH3-FINAL-1.2 (`provenance/nh3_final_1_2/`) takes the NH3 formation free
energy from the Gillespie–Beattie equilibrium constant and closes the loop equilibrium on Newton–Cooper fugacities, so its
process states replace the NH3-FINAL-1.1 states in every row that uses them (Tables A and E, C01–C07, C11, C12). Details,
flips and the rerun command: [`nh3_1_2/README.md`](nh3_1_2/README.md).

| Table | NH3-FINAL-1.1 (registered) | NH3-FINAL-1.2 | PR #77 column |
|---|---:|---:|---:|
| A | 1/28 | **18/28** | 17/26 |
| E | 1/3 | **0/3** | 0/3 |
| B | 5/20 | **5/20** | – |
| C | 7/12 | **9/12** | 7/9 |
| V | 0/1 | **0/1** | – |
| **all** | **14/64** | **32/64** | 24/38 |

Within 50–300 bar the NH3-FINAL-1.2 values equal the PR #77 column to every printed digit (same Gillespie–Beattie and
Newton–Cooper loop closure). NH3-FINAL-1.2 also covers the 314-bar record (A26, A27), which PR #77 does not.

| ID | Case | Metric | Model | Industrial | Rule | Source | Result | PR #77 | NH3-FINAL-1.2 |
|---|---|---|---:|---|---|---|---|---|---|
| A01 | Topsøe 140 bar | inlet NH3 (mol%) | 2.27 | 4.10 | rel:0.20 | Dybkjaer 1995 p. 226 | **fail** | 1.87 fail | 1.87 fail |
| A02 | Topsøe 140 bar | outlet NH3 (mol%) | 7.45 | 17.1 | rel:0.15 | Dybkjaer 1995 p. 226 | **fail** | 16.9 pass | 16.9 pass |
| A03 | Topsøe 140 bar | inlet flow (Nm³/h) | 1,137,652 | 500,000 | rel:0.25 | Dybkjaer 1995 p. 226 | **fail** | 425,248 pass | 425,248 pass |
| A04 | Topsøe 220 bar | inlet NH3 (mol%) | 1.34 | 3.80 | rel:0.20 | Dybkjaer 1995 p. 226 | **fail** | 1.04 fail | 1.04 fail |
| A05 | Topsøe 220 bar | outlet NH3 (mol%) | 10.2 | 19.9 | rel:0.15 | Dybkjaer 1995 p. 226 | **fail** | 22.5 pass | 22.5 pass |
| A06 | Topsøe 220 bar | inlet flow (Nm³/h) | 679,158 | 407,000 | rel:0.25 | Dybkjaer 1995 p. 226 | **fail** | 312,556 pass | 312,556 pass |
| A07 | Krupp-Uhde 188 bar | inlet NH3 (mol%) | 1.96 | 4.18 | rel:0.20 | Appl 2011 A2 p. 211 | **fail** | 1.55 fail | 1.55 fail |
| A08 | Krupp-Uhde 188 bar | outlet NH3 (mol%) | 9.25 | 19.7 | rel:0.15 | Appl 2011 A2 p. 211 | **fail** | 20.5 pass | 20.5 pass |
| A09 | Krupp-Uhde 188 bar | inlet flow (Nm³/h) | 1,232,756 | 635,302 | rel:0.25 | Appl 2011 A2 p. 211 | **fail** | 522,044 pass | 522,044 pass |
| A10 | Krupp-Uhde 188 bar | feed / make-up (mol/mol) | 7.49 | 3.52 | rel:0.25 | Appl 2011 A2 p. 211 | **fail** | 3.17 pass | 3.17 pass |
| A11 | Topsøe S-250 137 bar | net NH3 (mol%) | 5.03 | 16.5 | rel:0.15 | Liu 2013 p. 738 | **fail** | 14.8 pass | 14.8 pass |
| A12 | Uhde 160 bar | net NH3 (mol%) | 6.34 | 19.3 | rel:0.15 | Liu 2013 p. 740 | **fail** | 17.5 pass | 17.5 pass |
| A13 | PFI Kavala (Casale) 266 bar | outlet NH3 (mol%) | 9.97 | 19.0 | rel:0.15 | Orphanides 2006 p. 6 | **fail** | 22.1 fail | 22.1 fail |
| A14 | Kellogg 150 bar | inlet NH3 (mol%) | 0.891 | 2.00 | rel:0.20 | Hooper 1991 p. 269 | **fail** | 0.727 fail | 0.727 fail |
| A15 | Kellogg 150 bar | outlet NH3 (mol%) | 7.55 | 10.0–12.0 | rel:0.15 | Hooper 1991 p. 270 | **fail** | 17.5 fail | 17.5 fail |
| A16 | Braun 150 bar | inlet NH3 (mol%) | 2.71 | 4.00 | rel:0.20 | Liu 2013 p. 738 | **fail** | 2.20 fail | 2.20 fail |
| A17 | Braun 150 bar | outlet NH3 (mol%) | 7.96 | 21.0 | rel:0.15 | Liu 2013 p. 738 | **fail** | 17.9 pass | 17.9 pass |
| A18 | Braun 150 bar | net NH3 (mol%) | 5.25 | 17.0 | rel:0.15 | Liu 2013 p. 736 | **fail** | 15.7 pass | 15.7 pass |
| A19 | Braun 150 bar | space velocity (h⁻¹) | 91,235 | 7600 | factor:2 | Liu 2013 p. 736 | **fail** | 11,938 pass | 11,938 pass |
| A20 | Kellogg 140 bar | net NH3 (mol%) | 6.13 | 10.0 | rel:0.15 | Liu 2013 p. 736 | **fail** | 15.8 fail | 15.8 fail |
| A21 | Kellogg 140 bar | space velocity (h⁻¹) | 92,714 | 10,000 | factor:2 | Liu 2013 p. 736 | **fail** | 12,486 pass | 12,486 pass |
| A22 | Topsøe 260 bar | net NH3 (mol%) | 10.2 | 10.0–12.5 | rel:0.15 | Liu 2013 p. 736 | pass | 23.9 fail | 23.9 fail |
| A23 | Topsøe 260 bar | space velocity (h⁻¹) | 101,883 | 12,000 | factor:2 | Liu 2013 p. 736 | **fail** | 16,579 pass | 16,579 pass |
| A24 | ICI AMV 100 bar | net NH3 (mol%) | 3.09 | 13.0 | rel:0.15 | Liu 2013 p. 736 | **fail** | 11.1 pass | 11.1 pass |
| A25 | ICI AMV 100 bar | space velocity (h⁻¹) | 99,049 | 8000 | factor:2 | Liu 2013 p. 736 | **fail** | 10,534 pass | 10,534 pass |
| A26 | small/medium 314 bar | net NH3 (mol%) | 11.8 | 8.00–10.0 | rel:0.15 | Liu 2013 p. 736 | **fail** | – – | 26.8 fail |
| A27 | small/medium 314 bar | space velocity (h⁻¹) | 109,657 | 30,000 | factor:2 | Liu 2013 p. 736 | **fail** | – – | 18,857 pass |
| A28 | Casale 250 bar | Fe bed (m³) | 6.00 | 30.0 | factor:2 | US 4,372,920 col. 4, Ex. 1 | **fail** | 17.9 pass | 17.9 pass |
| E01 | 1000 t/d loop 151 bar | syngas + recycle compression (MW) | 8.01 | 13.0 | rel:0.30 | Liu 2013 p. 749 | **fail** | 7.50 fail | 7.50 fail |
| E02 | Uhde 2000 t/d 195 bar | syngas + recycle compression (MW) | 17.6 | 26.6 | rel:0.30 | Lippmann & Frisse 2004 p. 11 | **fail** | 17.1 fail | 17.1 fail |
| E03 | S-200 126 bar | recycle compression (MW) | 1.12 | 1.44 | rel:0.30 | Liu 2013 p. 779 | pass | 0.325 fail | 0.325 fail |
| B01 | S-200 126 bar, forward | bed-1 outlet (°C) | 457 | 489 | abs:15 | Liu 2013 p. 779 | **fail** | – – | 457 fail |
| B02 | S-200 126 bar, forward | bed-2 outlet (°C) | 463 | 446 | abs:15 | Liu 2013 p. 779 | **fail** | – – | 463 fail |
| B03 | S-200 126 bar, forward | outlet NH3 (mol%) | 13.2 | 14.3 | rel:0.15 | Liu 2013 p. 779 | pass | – – | 13.2 pass |
| B04 | S-200 126 bar, inverse | catalyst for printed ΔT (m³) | 76.4 | 65.3 | factor:2 | Liu 2013 p. 779 | pass | – – | 76.4 pass |
| B05 | S-200 134 bar, forward | bed-1 outlet (°C) | 454 | 490 | abs:15 | Liu 2013 p. 779 | **fail** | – – | 454 fail |
| B06 | S-200 134 bar, forward | bed-2 outlet (°C) | 463 | 444 | abs:15 | Liu 2013 p. 779 | **fail** | – – | 463 fail |
| B07 | S-200 134 bar, forward | outlet NH3 (mol%) | 13.7 | 14.9 | rel:0.15 | Liu 2013 p. 779 | pass | – – | 13.7 pass |
| B08 | S-200 134 bar, inverse | catalyst for printed ΔT (m³) | 77.6 | 65.3 | factor:2 | Liu 2013 p. 779 | pass | – – | 77.6 pass |
| B09 | Topsøe 220 vs 140 bar | catalyst volume 220/140 bar | 0.512 | 0.600 | rel:0.25 | Dybkjaer 1995 p. 226 | pass | – – | 0.512 pass |
| B10 | Topsøe 140 bar, cost-optimal | outlet NH3 (mol%) | 9.80 | 17.1 | rel:0.15 | Dybkjaer 1995 p. 226 | **fail** | – – | 9.80 fail |
| B11 | Topsøe 140 bar, cost-optimal | bed-1 inlet (°C) | 478 | 340–420 | window | W_BED1_FE (industrial_windows.csv) | **fail** | – – | 478 fail |
| B12 | Topsøe 140 bar, cost-optimal | catalyst (m³ per t/d) | 0.014 | 0.030–0.090 | window | W_VOL_FE (industrial_windows.csv) | **fail** | – – | 0.0145 fail |
| B13 | Topsøe 220 bar, cost-optimal | outlet NH3 (mol%) | 10.1 | 19.9 | rel:0.15 | Dybkjaer 1995 p. 226 | **fail** | – – | 10.1 fail |
| B14 | Topsøe 220 bar, cost-optimal | bed-1 inlet (°C) | 470 | 340–420 | window | W_BED1_FE (industrial_windows.csv) | **fail** | – – | 470 fail |
| B15 | Topsøe 220 bar, cost-optimal | catalyst (m³ per t/d) | 0.005 | 0.030–0.090 | window | W_VOL_FE (industrial_windows.csv) | **fail** | – – | 0.00535 fail |
| B16 | Krupp-Uhde 188 bar, cost-optimal | outlet NH3 (mol%) | 10.1 | 19.7 | rel:0.15 | Appl 2011 A2 p. 211 | **fail** | – – | 10.1 fail |
| B17 | Krupp-Uhde 188 bar, cost-optimal | bed-1 inlet (°C) | 474 | 340–420 | window | W_BED1_FE (industrial_windows.csv) | **fail** | – – | 474 fail |
| B18 | Krupp-Uhde 188 bar, cost-optimal | catalyst (m³ per t/d) | 0.008 | 0.030–0.090 | window | W_VOL_FE (industrial_windows.csv) | **fail** | – – | 0.00799 fail |
| B19 | KAAP 89 bar, Fe + 3 Ru/C | Fe share of catalyst volume | 0.155 | 0.350–0.650 | range | Liu 2013 p. 748 | **fail** | – – | 0.155 fail |
| B20 | KAAP 89 bar, Fe + 3 Ru/C | outlet NH3 (mol%) | 12.7 | 21.0–21.7 | rel:0.15 | Le Blanc & Knez 1996 p. 89; Liu 2013 ch.6 p. 504; Liu 2013 p. 748 | **fail** | – – | 12.7 fail |
| C01 | Fe optimum | pressure (bar) | 170 | 78.5–343 | window | W_P_FE (industrial_windows.csv) | pass | 140 pass | 140 pass |
| C02 | Fe optimum | pressure (bar) | 170 | 155–190 | window | W_P_FE_WORLDSCALE (industrial_windows.csv) | pass | 140 fail | 140 fail |
| C03 | Fe optimum | temperature (°C) | 425 | 350–540 | window | W_T_FE (industrial_windows.csv) | pass | 450 pass | 450 pass |
| C04 | Fe optimum | separator (°C) | 30.0 | -25.0–7.50 | window | W_TSEP_FE (industrial_windows.csv) | **fail** | 30.0 fail | 30.0 fail |
| C05 | Fe optimum | catalyst (m³ per t/d) | 0.026 | 0.030–0.090 | window | W_VOL_FE (industrial_windows.csv) | **fail** | 0.056 pass | 0.0563 pass |
| C06 | Fe optimum | outlet NH3 (mol%) | 11.3 | 10.0–21.0 | window | W_OUT_FE (industrial_windows.csv) | pass | 17.9 pass | 17.9 pass |
| C07 | Fe optimum | space velocity (h⁻¹) | 46,460 | 7600–35,000 | window | W_SV_FE (industrial_windows.csv) | **fail** | 10,240 pass | 10,240 pass |
| C08 | staged optima (44) | Ru/C upstream of Fe in any staged optimum | no | no | equals:False | Le Blanc & Knez 1996 p. 90; Liu 2013 p. 748; Le Blanc & Knez 1996 p. 84; Appl 2011 A3 p. 242 | pass | – – | no pass |
| C09 | KAAP-type loop | Ru/C in 90-bar optimum at 12 %/y | no | yes | equals:True | Le Blanc & Knez 1996 p. 89; Le Blanc & Knez 1996 p. 90; Liu 2013 p. 747 | **fail** | – – | no fail |
| C10 | 60–200 bar sweep | ρ(P, Ru financing boundary) | -0.976 | < -0.5 | below:-0.5 | Le Blanc & Knez 1996 p. 89 | pass | – – | -0.976 pass |
| C11 | Ru/C optimum, 0 %/y | pressure (bar) | 145 | 89.2–138 | window | W_P_RU (industrial_windows.csv) | **fail** | 105 pass | 105 pass |
| C12 | global, 12 %/y | supported Ru/C − Fe at 12 %/y (USD/t) | 1.12 | > 0 | above:0 | Liu 2013 ch.6 p. 492 | pass | 1.45 pass | 1.45 pass |
| V01 | 10–30 MPa, −30…30 °C | separator vapour NH3, model/table | 0.602 | 0.800–1.20 | range | Appl 2011 A1 Table 5 p. 113 | **fail** | – – | 0.602 fail |

Sources are given as printed page; every value, its PDF page, table or figure and a verbatim snippet are in
`reference_values.csv` (row ids in `results_metrics.csv`). Window members are in `industrial_windows.csv`.

**Answers**

- **Loop states (Table A) fail because of the loop equilibrium, not the kinetics.** At the plants' conditions the
  NH3-FINAL-1.1 equilibrium per-pass N2 conversion is 0.12 / 0.21 / 0.17 (Topsøe 140 bar / Topsøe 220 bar /
  Krupp-Uhde 188 bar, 448 °C). The Gillespie–Beattie value is 0.30 / 0.40 / 0.36, and with Newton–Cooper fugacities it
  is 0.33 / 0.44 / 0.40.
  - With 0.8 of the NH3-FINAL-1.1 value, outlet and net NH3 are 38–76 % low in 11 of 13 comparisons, converter flows
    are 67–128 % high and space velocities are 3.7–12 × the plants'.
  - With PR #77's loop closure, 24 of its 38 comparisons pass: outlet and net NH3 within 15 % in 8 of 12, flows and
    feed/make-up within 25 % in 4 of 4, space velocity within ×2 in 4 of 4, the Casale bed within ×2.
- **Separator vapour is 40 % low in both columns.** The model's recycle NH3 is p_sat(T_sep)/P. That is 0.60 × (median;
  0.42–0.76) the BASF saturation table over 10–30 MPa, −30 to +30 °C. Converter inlet NH3 is therefore 32–65 % below all
  five plants that print it (A01, A04, A07, A14, A16; 45–73 % under PR #77).
- **The measured Fe kinetics reproduce a real converter.** Liu's S-200 converter (1000 t/d, 18.8 + 46.5 m³ of
  1.5–3 mm magnetite):
  - Run at its printed inlet gas and bed inlet temperatures, the model gives outlet NH3 13.2 / 13.7 % against 14.31 /
    14.94 % (−7.7 / −8.0 %).
  - The printed bed temperature rises need 76.4 / 77.6 m³ against the 65.3 m³ installed (×1.17 / ×1.19).
  - The split is wrong: bed 1 is too slow at its 360–365 °C inlet (outlet −32 / −36 K; 30.7 m³ needed against 18.8),
    and bed 2 is right (45.7 m³ against 46.5).
  - The minimum-volume converter for Topsøe's printed duties needs 37.3 m³ at 220 bar and 72.9 m³ at 140 bar. That
    ratio of 0.51 compares with Topsøe's 0.60 (−15 %, pass).
- **Cost-optimal designs leave industrial practice.** At the plants' own loop conditions the cost-optimal all-Fe
  converter starts every bed at 467–493 °C (industry 340–420 °C at bed 1). It stops at 9.8–10.1 % outlet NH3 (plants
  17.1–19.9 %) and holds 0.005–0.014 m³ per t/d (plants 0.030–0.090).
  - The cost function prices per-pass conversion almost at zero: 3-bar recycle pressure rise (plants 5–20 bar), no
    recycle-flow equipment, and syngas compression 34–38 % below the plant compressors (E01, E02).
  - The KAAP layout at 89 bar (Fe bed 1, Ru/C beds 2–4) puts 15 % of the catalyst volume in the Fe bed against about
    half in the Trinidad KAAP converters, and reaches 12.7 % NH3 against 21–21.7 %.
- **Revealed design (a), Fe.**
  - Passes: the unconstrained Fe optimum (170 bar, 425 °C) lies inside the industrial Fe-loop window (78.5–343 bar,
    36 loops), the world-scale window (155–190 bar) and the catalyst window (350–540 °C). Its outlet NH3, 11.3 %, is
    inside 10–21 %.
  - Fails: its 30 °C separator is outside the industrial −25 to 7.5 °C (no refrigeration). Its 0.026 m³ per t/d is
    below 0.030, and its space velocity of 46,000 h⁻¹ is above 35,000.
  - Under PR #77 the optimum moves to 140 bar and 450 °C. That is still inside the Fe-loop window but below the
    world-scale 155 bar. Its 56.3 m³ (0.056 per t/d) and 10,240 h⁻¹ are industrial.
- **Revealed design (b), Ru/C.**
  - Bed position, pass: the model never places Ru/C upstream of Fe in any of 44 staged optima. Every built Ru loop
    has Ru downstream of magnetite.
  - Pressure ordering, pass: the financing rate below which Ru/C enters the optimum falls with loop pressure, from
    7.0 %/y at 60–75 bar to 2.9 %/y at 200 bar (ρ = −0.98).
  - Global optimum at 12 %/y, pass: the optimum is Fe, with supported Ru/C +1.12 USD/t dearer.
  - Fail: at the model's own 12 %/y rate and today's Ru price no Ru enters the 90-bar optimum. The boundary is
    6.7 %/y, yet the KAAP plants were built with Ru at about 90 bar.
  - Fail: where Ru/C beats Fe (0 %/y) its optimum is at 145 bar, outside the 89–138 bar of built Ru loops. PR #77 puts
    it at 105 bar (pass).

## 1. Reproduction gate

`test_reproduce.py` and the first step of `run_benchmark.py` assert, before any other run:

- NH3-FINAL-1.1 with descriptor kinetics: Fe 15.291705 USD/t (425 °C, 180 bar, 30 °C) and Ru 22.030595 (450 °C,
  425 bar, 25 °C), to 1e-9.
- Measured kinetics, plug flow: Fe 15.578802 USD/t at 425 °C, 170 bar, 30 °C, 25.594 m³, to 1e-5.
- The off-grid state function returns the grid state where both exist.

## 2. Industrial data (`reference_values.csv`)

1,589 values from 41 sources. Each has a printed page, PDF page, table or figure locator and a verbatim snippet of at
most 25 words.

| Kind | Rows | Meaning |
|---|---:|---|
| `source_fact` | 1,295 | printed number |
| `derived` | 170 | unit conversion or arithmetic on printed numbers, shown in `conversion` |
| `secondary` | 104 | a source reporting another party's plant; the primary is named in `note` |
| `figure_reading` | 11 | read off a plot |
| `web_summary` | 9 | read through a web summariser; used in no metric and no window |

Main sources:
- Ullmann's "Ammonia" 1–3 (Appl 2011), Appl 1999 and 1997 (IFA);
- Dybkjaer 1995 (Topsøe) in Nielsen;
- Hooper, Gramatica & Pernicone and Tennison in Jennings 1991;
- Liu 2013 (chapters 6 and 9), Kirk-Othmer, Rouwenhorst 2021, Brown 2014 (BP/KBR KAAP catalyst), Tripodi 2021;
- patents of Kellogg, Casale, Braun and KBR (US 3,721,532; 4,153,673; 4,230,669; 4,372,920; 4,482,523; 4,554,135;
  4,696,799; 4,755,362; 4,919,909; 6,171,570; 7,081,230);
- IFA technical-conference papers on KAAP Kitimat and KAAP grassroots (Le Blanc & Knez 1996), Uhde dual pressure
  (Lippmann & Frisse 2004), PFI Kavala, IFFCO Kalol, KRIBHCO and SOUTHPETRO;
- the thyssenkrupp Uhde brochure, the KBR revamp list and the Johnson Matthey slides.

Every number from a table or figure was read from a rendered page image. Spot-checked against the page images for this
README: Dybkjaer Table 6.1, Appl A2 Fig. 57 and its text, Liu Tables 9.2 and 9.19, and Le Blanc & Knez Table 2.

Industrial records used (P, T_sep as printed; T is the printed final-bed outlet temperature, or T_REF = 448 °C):

| Case | Plant / design | P (bar) | T (°C) | T_sep (°C) | t/d |
|---|---|---:|---:|---:|---:|
| TOP140, TOP220 | Topsøe loops, Dybkjaer 1995 Table 6.1 | 140, 220 | 448 | −5 | 1000 |
| UHDE188 | Krupp-Uhde, Appl 2011 A2 Fig. 57 | 188 | 448 | 0 | 1500 |
| S250 | Topsøe S-250, Liu Fig. 9.3 | 137.3 | 448 (S-50 outlet) | −5 | 1000 |
| UHDE160 | Uhde two-converter loop, Liu Fig. 9.6 | 160 | 442 | 0 | 1000 |
| PFI266 | PFI Kavala, Casale 2-bed (Orphanides 2006) | 266 | 470 | 1.5 | 470 |
| KELLOGG150 | Kellogg single-train (Hooper 1991) | 150 | 448 | −25 | 1000 |
| BRAUN150, LIU_* | Braun, Kellogg, Topsøe, ICI AMV, Chinese small/medium (Liu Table 9.2) | 100–314 | 448 | −23 to 7.5 | 1000 |
| CASALE250 | US 4,372,920 Ex. 1 | 250 | 448 | −5 | 1000 |
| LIU93_151, UHDE2000, LIU919A | compressor powers | 151, 195, 126.4 | 448, 448, 446 | −5 | 1000, 2000, 956 |
| LIU919A/B | Liu Table 9.19, S-200 2-bed, A110 magnetite, inlet as printed (H2 62.9, N2 22.8, NH3 2.3, inerts 12 %) | 126.4, 134 | beds 365/390, 360/385 in | – | 956, 1001 |
| KAAP | KAAP grassroots, Le Blanc & Knez 1996 Table 2; Liu 2013 p. 747 | 89.2 | model | −20 (model) | 1850 |

## 3. Sensitivities and diagnostics (not counted)

| Variant | Effect |
|---|---|
| T_REF −25 / +25 °C (27 state and machinery metrics) | 3/27 and 1/27 pass, against 1/27 at T_REF |
| Gillespie–Beattie ideal-gas loop equilibrium (PR #64 states), same harness | 12/31 of the state and machinery metrics pass. Outlet NH3 −9 to +1 % at Topsøe and Uhde; inlet NH3 still 43–71 % low |
| PR #77 (GB + Newton–Cooper) | 24/38 |
| Fe effectiveness 0.5 in the forward S-200 runs | outlet NH3 10.4 / 10.8 % (−27 / −28 %); full intrinsic activity is the better description of this 1.5–3 mm radial converter |

## 4. Judgement calls

- **T_REF = 448 °C.** This is the median of seven printed final-bed outlet temperatures. It is the reaction
  temperature for records that print none. Converter exit temperatures measured after an internal exchanger
  (280–420 °C in Liu Table 9.2) were excluded by rule before the run.
- **TSEP_REF = −5 °C.** This is the median of 14 printed final separator temperatures. It was used only for the Casale
  catalyst volume and the compressor-power cases, which print no separator temperature.
- **No inerts in the state model.** The NH3-FINAL-1.1 states carry none. Plants run with 8–12 %, which lowers their
  equilibrium. The PR #77 column passes the outlet-NH3 checks anyway.
- **Converter designs run at 1000 t/d.** `converter.py` prices per tonne on the NH3-FINAL-1.1 1000 t/d annual output, so
  designs run there and are compared per t/d. Outlet NH3, temperatures and volume shares are intensive.
- **KAAP layout.** The KAAP layout uses the staged analysis's KAAP-type assumptions, a −20 °C separator and 8 % inerts,
  because no KAAP source prints them.
- **"About half" Fe.** The phrase was pre-registered as a 0.35–0.65 volume share.
- **Staged checks C08–C10.** These read the committed staged-converter outputs (`arrangements.csv`,
  `sensitivities.csv`, `boundary_summary.json`), which that folder's workflow reproduces. The 44 optima are 18
  arrangement cases plus 26 sensitivity cases.
- **Liu Table 9.19.** It is Liu's simulation of an S-200-type converter with printed geometry. It is used as a licensor
  design, not as measured plant data. The same holds for Dybkjaer Table 6.1 ("typical operating parameters") and the
  Krupp-Uhde flowsheet.

## 5. Files and rerun

| File | Content |
|---|---|
| `PREREGISTRATION.md` | metrics, rules, windows (commit `b11133c`, before any comparison) |
| `reference_values.csv` | 1,589 industrial values with locators |
| `build_prereg_tables.py` | writes `benchmark_cases.csv`, `benchmark_metrics.csv`, `industrial_windows.csv` from row ids |
| `nh3_model.py`, `converter_sim.py` | the latest model imported unchanged; state at any operating point; converter forward / inverse / minimum volume; PR #77 import via `git show` |
| `run_benchmark.py` | everything above → `results_metrics.csv`, `results_cases.json`, `results_sensitivity.csv`, `summary.json`, `run_benchmark_stdout.txt` |
| `test_reproduce.py` | the reproduction gate |
| `nh3_1_2/` | NH3-FINAL-1.2 re-score (`NH3_MODEL=1.2`): the same output files plus `rescore_1_1_vs_1_2.csv`; see its README |

    pip install -r requirements.txt pyyaml
    cd analysis/validation_nh3_plant_2026_10_13
    python -m unittest test_reproduce -v          # ~20 s
    python build_prereg_tables.py                 # regenerates the pre-registered tables (identical output)
    python run_benchmark.py --workers 4           # ~4 min; at most 8 workers (--workers 1: no pool, ~9 min)
    NH3_MODEL=1.2 python -m unittest test_reproduce -v
    NH3_MODEL=1.2 python run_benchmark.py --workers 1   # NH3-FINAL-1.2 re-score -> nh3_1_2/

Interpreter used: `D:\Research\CatalystForge\.venv\Scripts\python.exe` (CPython 3.12.14, numpy 2.3.5, scipy 1.18.0).
The PR #77 column needs the branch `origin/analysis/nh3-final-1-2-candidate-20261013` fetched; without it the column is
skipped. No file outside this folder is changed. `NH3_MODEL` selects the model through `analysis/nh3_model.py`
(default 1.1, which reproduces the committed files above: `results_metrics.csv` and `results_sensitivity.csv` byte for
byte, `results_cases.json` and `summary.json` apart from their wall-clock `seconds` entries).
