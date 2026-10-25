# Exploratory ranking preservation and NH3 staged-catalyst decision phase atlas

**Date:** 2026-10-19  
**State:** tested exploratory branch; **NOT incorporated into the main manuscript**.  
**Source:** the already-committed NH3-FINAL-1.2 supported Ru/C / Fe-first staged-converter design-library costs, **not** the descriptor-only NH3 15-metal main screen.  
**Cloud audit:** [Actions #39215399826](https://github.com/stloendays/Catalyst-Essay/actions/runs/39215399826) — all 13 tests green, 4,100/4,100 source cells scored, source Git blobs exact, figures produced and uploaded.  
**Artifact:** [phase atlas (PNG/SVG + four CSVs + JSON + report + logs)](https://github.com/stloendays/Catalyst-Essay/actions/runs/39215399826/artifacts/12169620748). GitHub login may be required to download.

## I. Mathematical result: conditional order-preservation proposition

The mathematically exact statement is in [THEORY.md](THEORY.md). If catalyst A's feasible operation set **contains** B's and its downstream cost is no worse **at every B-feasible operation**, separately minimizing each catalyst's cost cannot reverse A's economic order. That is a **sufficient optimization-dominance proposition**, not a universal materials law or an original deep mathematical theorem: knowing only A's higher TOF/STY does *not* establish the premises.

We give explicit counterexamples showing (i) higher intrinsic activity can lose on price; (ii) even pointwise A dominance on the **common intersection** of feasible sets cannot prevent a B win if B has another cheap policy unavailable to A; (iii) Fe/Ru pure-parity does not force either pure material to be chosen when a Fe-first mixed-bed design is cheaper. We also prove a uniform-error decision-margin certificate but **have not calibrated a plant-model error bound**.

A second formal property is useful: for fixed financing, recovery and a fixed feasible design library whose cost is affine and nondecreasing in Ru purchase price, each catalyst-policy envelope is the minimum of finitely many nonnegative-slope lines, hence **concave, piecewise affine and nondecreasing in price**. Binary Fe-vs-Ru cost difference cannot reverse sign more than once when raising Ru price. This does **not** hold for arbitrary changes in financing, pressures or model validity.

## II. Model economic decision phases: observed source-grid outcomes

Fixed dimensions: **two simultaneous P/Tsep masks**, (90 bar, -20 °C separator) and (150 bar, -5 °C separator); 90.00% and 95.55% assumed gross Ru recovery; 41 Ru purchase-price points USD $2,000–200,000 per kg; 25 metal financing points 0–12%/yr. Total 2×2×41×25 = **4,100 exact precomputed cells**.

Patterns: FFF (all Fe), FFR (Fe–Fe–Ru/C), FRR (Fe–Ru/C–Ru/C), RRR (all supported promoted Ru/C). The finance/recovery comparison is within **one fixed process mask** at a time, not a comparison of real industrial plants. Each economic winner is the lowest of the original source's three *envelopes*: all Fe, the best of FFR/FRR, all Ru/C. The source also records WHICH staged pattern wins. The two individual mixed-pattern costs are not both printed per scenario, so all economic-margin analyses below concern the three-family comparison.

| Process mask | Ru recovery | FFF | FFR | FRR | RRR | Staged strictly cheaper than both pure |
|---|---:|---:|---:|---:|---:|---:|
| 90 bar / −20 °C | 90.00% | 261 | 64 | 279 | 421 | 343 / 1,025 (33.5%) |
| 90 bar / −20 °C | 95.55% | 241 | 61 | 272 | 451 | 333 / 1,025 (32.5%) |
| 150 bar / −5 °C | 90.00% | 325 | 67 | 434 | 199 | 501 / 1,025 (48.9%) |
| 150 bar / −5 °C | 95.55% | 305 | 60 | 431 | 229 | 491 / 1,025 (47.9%) |
| **Total** |  | **1,132** | **252** | **1,416** | **1,300** | **1,668 / 4,100 (40.7%)** |

**High-impact theoretical observation:** 97 of the 100 fixed-mask/recovery/financing price sweeps contained a sampled interval bracketing the **binary** pure-Ru-versus-Fe cost sign change; at BOTH price-grid endpoints of all 97 such brackets, the mixed configuration was the cheapest candidate. This demonstrates the incompleteness of reporting only the Fe/Ru binary crossing in this **model library**. It does *not* certify a mixed optimum at the exact continuous binary root or in actual installations.

### Nominal Ru-price slice: $53,852.5/kg, gross recovery 95.55%

**90 bar/-20 °C** (25 independent source rows):

| Model winner | Source financing samples |
|---|---|
| All Ru/C (RRR) | 0–0.5%/yr |
| Fe–Ru/C–Ru/C (FRR) | 1.0–4.5%/yr |
| Fe–Fe–Ru/C (FFR) | 5.0–6.5%/yr |
| All Fe (FFF) | 7.0–12.0%/yr |

Category transitions are bracketed by **0.5–1.0%**, **4.5–5.0%**, **6.5–7.0%**; intervals denote discrete adjacent samples, NOT exactly identified continuous thresholds.

**150 bar/-5 °C** (same nominal price and recovery): FRR → FFR in **3.0–3.5%/yr**; FFR → all Fe in **4.5–5.0%/yr**. Here all-Ru/C does not win at the nominal sampled price.

### How economically substantial are the staged wins?

For a cell where the staged envelope strictly beats both pure alternatives, calculate the modeled regret from refusing a mixed bed as \(\min(C_{\mathrm{FFF}},C_{\mathrm{RRR}})/C_{\mathrm{staged}}-1\).

- At 90 bar/-20 °C, median penalty is **0.53–0.55%** and the largest across the two recovery panels **~1.54%**.
- At 150 bar/-5 °C, median penalty is **0.36%** and the largest **~1.09%**.
- Across all 4,100 cells, **355** have the first-versus-second *family* cost margin <**$0.01/t**, and **3,351** have a family margin <**$0.10/t** (~81.7%). The latter are **not** automatically robust policy choices under a plausible real model discrepancy. These are source *grid* counts, not a confidence level.
- Raising assumed recovery from 90% to 95.55% changes the four-way winning pattern at **73/1,025** matched 90-bar cells and **75/1,025** matched 150-bar cells, with mean modeled optimized-cost decrease **$0.0453/t** and **$0.0194/t** respectively.

These numerical results are most useful for motivating **quantitative decision margins** rather than claiming large economic savings or that Fe-first designs are always preferable.

## III. Essential credibility boundaries

1. **Non-overlapping original kinetics-fit pressure ranges.** Dyson–Simon Fe: about **151–313 bar**; promoted Ru/C Rossetti: **50–100 bar**. The Fe calculation in the 90-bar mask and the Ru/C calculation in the 150-bar mask extrapolate beyond their fitted ranges. The phase diagram does not validate same-pressure Fe/Ru cost ranking experimentally.
2. **Two process masks change pressure AND separator temperature together**; no isolated pressure effect follows. Commercial metal financing/buyback terms are not verified for Ru by this study.
3. **Finite previously optimized design library**, not a new global continuous optimum, full plant flowsheet closure or pressure-domain-calibrated rate law. Every conclusion remains model-conditional.
4. **Close-cost distinctions are fragile** without error bars. A small region of near-ties should be shown as uncertainty or decision indifference in any eventual main-paper adaptation, not as sharp industrial borders. We currently report observed margins but have NOT estimated realistic error bounds.
5. **Do not change main paper.** No original numerical evidence, old experiments, agent, manuscript text, SI, figures or frozen model has been edited. This branch is for independent scientific review.

## IV. Files and how to repeat

- PROTOCOL.md — scope and acceptance criteria committed BEFORE analysis code.
- THEORY.md — formal propositions, proofs, counterexamples, applicability limits.
- atlas.py — standard-library source SHA auditing, source-cost classification, choice-boundary reporting and Matplotlib 2×2 categorical atlas.
- test_theory.py — 13 tests including exhaustive finite-state preservation checks, counterexamples and source ledger validation.
- .github/workflows/rank-preservation-phase-2026-10-19.yml — reruns with Python 3.12, source hash checking and read-only manuscript firewall. **Artifacts include** figure PNG/SVG, data CSV, JSON summary, REPORT.md and logs.

Run from repository root:

    python -m pip install matplotlib
    python -m unittest discover -s analysis/rank_preservation_phase_2026_10_19 -p "test_*.py" -v
    python analysis/rank_preservation_phase_2026_10_19/atlas.py --out /tmp/nh3_decision_atlas

**Next scientifically useful gate:** test model-form sensitivity before any paper promotion (candidate kinetic domains, actual separator and compressor boundary uncertainties, bounded price/cost margins). The result is exploratory, and those uncertainties may be larger than the calculated mixed-bed savings.
