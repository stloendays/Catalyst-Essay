# Paper leaderboards versus plant-cost leaderboards (ammonia synthesis) — 2026-10-06, 30-paper set

`run_field_chain.py` takes the extraction agent's output for 30 primary papers (`agent/nh3_field/out/records_normalized.csv`,
used as extracted) through the frozen ammonia chain and compares, within each paper, the paper's own leaderboard with
the plant-cost leaderboard. It is the ammonia analogue of `analysis/meoh_literature_inversion_2026_10_05/`; the paper
set, extraction and accuracy are in `agent/nh3_field/README.md`.

- **Mapping:** unchanged from `analysis/nh3_supported_2026_10_06/run_supported_chain.py`, whose functions are
  imported. A catalyst of one model metal with a known metal content and a rate per g catalyst at its laboratory T, P
  and NH₃ fraction is inverted into an effective descriptor on its metal's side of the volcano (residual factor above
  the volcano top) and goes through the frozen 14,136-state library with its own metal content (bed density
  1,000 kg m⁻³; the commercial fused or wüstite iron catalyst used as a reference, 71.51 wt% and 2,500 kg m⁻³ — a
  composite made from it, such as "80% magnetite based industrial Fe catalyst–20% Ce₀.₈Sm₀.₂O₂₋δ", keeps its own metal
  content and the supported-bed density). The laboratory NH₃ fraction is the printed outlet, else n / (F₀ − n) from the
  rate n and the inlet space velocity F₀, else the median of the set (0.31 %), entered at the same approach to equilibrium
  (Gillespie–Beattie). An entry without a space velocity takes the single one its paper reports at the same T, P and
  H₂/N₂ (a condition stated once for a figure or table).
- **Primary set:** 300–500 °C, steady thermal operation, outlet below 90 % of equilibrium, H₂/N₂ = 3, feasible within
  the 90 m³ bed limit.
- **Candidates:** 1,176 extracted entries; 945 enter the chain, 231 do not (164 without a metal content, 87 without a
  rate per g catalyst, 46 without a single model metal — bimetallic, nitride or metal-free —, 25 without T or P; an
  entry can have several reasons). 742 primary entries with a plant cost, 65 primary entries infeasible within the bed
  limit, 138 flagged. After one entry per catalyst (name, preparation and metal content) and comparison (94 removed)
  and one entry per measurement (25 removed, below), 623 entries from 29 papers.
- **Comparison groups:** entries of one paper at the same T, P, H₂/N₂ and space velocity, i.e. the comparison the
  paper itself makes. Pressures within 0.102 MPa and 6 % are one setting (a gauge and an absolute value of the same run,
  e.g. 2.0 and 2.1 MPa). **124 groups with at least two entries, 539 entries, 28 papers.**
- **One entry per measurement:** within a group, entries with the same metal, metal content and rate (3 significant
  figures) are one measurement printed twice — read from the text and from an SI figure (2.5%Ru/CeO₂–NR, –MS, –CS),
  printed under two names ("80 wt% Fe–20 wt% SDC" and "80 wt% Fe–20 wt% Ce₀.₈Sm₀.₂O₂₋δ", up to four times), or two
  catalysts the chain cannot tell apart (same metal, content and rate, hence the same cost). The printed value is kept
  (main text > SI > plot reading, then the longest time on stream). 25 entries in 18 groups of 9 papers are removed
  (`candidates.csv`, column `duplicate_in_group`); no group winner changes through this step.
- **Paper leaderboard:** the rate per g catalyst. The script uses the rate per g metal only for a group in which the
  paper prints every rate per g metal; no such group exists, so all 124 groups rank per g catalyst (`summary.json`,
  `primary.paper_basis_groups`; Fan 2017 prints per g Fe, but its groups include the industrial catalyst printed per
  g catalyst). The per-g-metal leaderboard is a variant.
- **Plant leaderboard:** plant cost (USD/t NH₃), metal price only, no metal recovery; variant with 90 % Ru recovery.
  Fe benchmark 15.29 USD/t.

## Self-check (Humphreys chain through this code path)

Every catalyst of the Humphreys 2021 chain (83 rows after the PR #28 errata) is run through this script's mapping
function with that chain's inputs. Costs (primary, constant-α transfer, bed 500 and 2,500 kg m⁻³, 90 % recovery), E_eff
and α reproduce `analysis/nh3_supported_2026_10_06/supported_candidates.csv` exactly: 548 values, maximum relative
difference 0
(`selfcheck_supported.csv`). The script also calls the ACSA gate (`agent/selfcheck_gate.py` `require()`) first.

## Result

| Leaderboard / plant treatment | Groups with a different winner | Papers affected | Regret if the paper's winner is built (median of mismatched / max) | Pairwise orderings inverted | Spearman (median over groups of ≥ 3) |
|---|---|---|---|---|---|
| **Rate per g catalyst, no metal recovery (primary)** | **44 / 124 (35.5 %)** | **13 / 28** | **11.3 % / 76 %** | **231 / 1356 (17 %)** | **0.90** |
| Rate per g catalyst, 90 % Ru recovery | 43 / 124 (35 %) | 14 / 28 | 6.2 % / 88 % | 210 / 1356 (15 %) | 0.90 |
| Rate per g metal | 54 / 124 (44 %) | 18 / 28 | 10.2 % / 127 % | 390 / 1356 (29 %) | 0.60 |
| Commercial fused-Fe references removed | 27 / 115 (23 %) | 10 / 28 | 4.5 % / 62 % | 189 / 1256 (15 %) | 1.00 |

- **Paper-cluster bootstrap** (10,000 resamples of the 28 papers, seed 20261006): 95 % CI of the share of groups with
  a different winner **18–52 %** (primary); 28–59 % per g metal; 19–51 % with Ru recovery; 11–38 % without the fused-Fe
  references.
- Weighting each paper equally, 23.5 % of a paper's comparison groups pick a different winner (CI 13–36 %).
- Six of the 44 mismatched groups are near-ties (regret below 1 %); 38 / 124 differ by at least 1 %.

Robustness of the primary result:

| Variant | Different winner | Papers |
|---|---|---|
| Printed values only (no plot readings) | 7 / 34 (21 %, CI 7–35 %) | 6 / 23 |
| Bed density 500 kg m⁻³ | 41 / 119 (34 %) | 13 / 28 |
| Bed density 2,500 kg m⁻³ | 41 / 124 (33 %) | 11 / 28 |
| Outlet NH₃ known (printed or rate / WHSV) | 38 / 103 (37 %) | 10 / 25 |
| Constant multiplier on the metal's own TOF instead of E_eff | 37 / 124 (30 %) | 9 / 28 |
| Without Kitano 2018 (the paper with the most groups, 12) | 32 / 112 (29 %) | 12 / 27 |
| Measured at ≥ 5 MPa | 1 / 19 (5 %) | 1 / 8 |
| Groups pooled over T (the methanol grouping: one paper, P, H₂/N₂, space velocity) | 40 / 64 (63 %) | 23 / 29 |

## Why the winners differ

The 44 mismatched groups (`group_metrics.csv`, `mismatch_kind`; `same_support_family` compares the host cations of
the two supports, O, N, H and stoichiometry ignored):

| Mechanism | Groups | Papers | Regret median / max |
|---|---:|---:|---|
| Commercial fused-Fe reference beats the paper's new catalyst | 17 | 3 | 28.7 % / 76.5 % |
| A different metal beats the paper's Ru or Co catalyst | 14 | 3 | 17.1 % / 62.1 % |
| — of which Fe on the same support (Tang 2018 BaTiO₃₋ₓHₓ, 6; Kitano 2019 BaCeO₃₋ₓNᵧH_z, 6) | 12 | 2 | 17.1 % / 31.5 % |
| — of which Ru/MgO beats Co/C12A7:e⁻ (Inoue 2019) | 2 | 1 | 34.7 % / 62.1 % |
| Same metal and metal content, different support or promoter | 11 | 5 | 2.3 % / 5.9 % |
| Same metal, different metal content | 2 | 2 | 0.5 % / 1.0 % |

**1. Metal inventory: Fe beats Ru and Co on the same support.** The paper ranks by rate per g catalyst; the plant pays
for the metal inventory, and Ru costs 53,852 USD/kg against 8 USD/kg for Fe.
- Tang et al. 2018 (BaTiO₃₋ₓHₓ supports, 400 °C, 66,000 mL g⁻¹ h⁻¹): at 5 MPa the paper's leader Ru/BaTiO₂.₅H₀.₅
  (2.5 wt% Ru, 50 mmol g⁻¹ h⁻¹) costs 24.45 USD/t; Fe/BaTiO₂.₃₅H₀.₆₅ (1 wt% Fe, 14 mmol g⁻¹ h⁻¹) costs 19.94 USD/t
  (regret 23 %). Fe wins at every pressure the paper tests (0.1–5 MPa; regret 17–31 %).
- Kitano et al. 2019 (BaCeO₃₋ₓNᵧH_z, 0.9 MPa): Fe (1.2 wt%) has the lowest plant cost at all six temperatures; at
  400 °C Ru (4.5 wt%, 29.5 mmol g⁻¹ h⁻¹, 21.11 USD/t) leads the paper and Fe (6.8 mmol g⁻¹ h⁻¹, 18.92 USD/t) the
  plant (regret 12 %); at 320, 360 and 380 °C, where the extracted entries are Co and Fe only, Co (4.7 wt%) leads the
  paper (regret 6–20 %).
- Inoue et al. 2019, 400 °C, 0.1 MPa: Co/C12A7:e⁻ leads the paper (1.8 mmol g⁻¹ h⁻¹) but its Co sits far on the
  weak-binding side (E_eff −0.70 eV) and costs 35.17 USD/t; Ru/MgO (6 wt%, 1.6 mmol g⁻¹ h⁻¹) costs 21.69 (regret 62 %).
- With 90 % Ru recovery the Ru penalty shrinks (median regret 6.2 %), but the share of groups with a different winner
  stays at 35 %.

**2. The commercial fused-Fe reference.** Four papers test their catalysts against an industrial fused-iron catalyst
in the same run; in three it wins the plant ranking (17 groups; 18 before the composite of Ref. d0ta05238h was taken
out of the reference class, see Corrections). The reference carries 71.5 wt% Fe in a 2,500 kg m⁻³ bed at 8 USD/kg; it loses the paper's ranking
and wins the plant's.
- Kitano et al. 2018 (Fig. 1, 0.9 MPa): at 360 °C Ru/Ba-Ca(NH₂)₂ (10 wt% Ru) makes 60.4 mmol g⁻¹ h⁻¹ against
  10.5 for the wüstite reference; the plant costs are 15.88 and 14.22 USD/t (regret 12 %). At 0.1 MPa the paper's
  leader Cs-Ru/MgO costs 22–25 USD/t against 14.2 for the reference (regret 55–76 %).
- Sato et al. 2021 (400 °C, 2 MPa): Co@BaO/MgO-700red (20 wt% Co, 61 mmol g⁻¹ h⁻¹, 18.90 USD/t) against the
  commercial fused Fe (14.2 mmol g⁻¹ h⁻¹, 14.69 USD/t), regret 29 %; 16 % at 4 MPa.
- Without these references 23 % of the groups still pick a different winner.

**3. Same metal and metal content: the descriptor that wins at 0.1–1 MPa is not the plant's.** The laboratory rate
places each catalyst on its metal's volcano at the laboratory condition. For 5 wt% Ru the plant cost is lowest at
E ≈ −1.20 eV (21.73 USD/t) and rises to 24.67 USD/t at −1.00 eV, while the volcano top at the laboratory condition
sits at −0.99 eV (0.1 MPa, 340 °C), −1.07 eV (1 MPa, 400 °C) and −1.11 eV (5 MPa, 400 °C). A catalyst that
outperforms its neighbour at 0.1–1 MPa is mapped closer to the low-pressure optimum and further from the plant's.
- Ma et al. 2017 (Ru/CeO₂, 4 wt% Ru, 400 °C, 1 MPa): 2Cs–Ru/r-CeO₂ leads (14.3 mmol g⁻¹ h⁻¹, E_eff −1.06 eV,
  22.80 USD/t); 2Cs–Ru/MgO (10.5 mmol g⁻¹ h⁻¹, −1.20 eV) costs 21.83 (regret 4.5 %).
- Sato et al. 2017 (Ru/Pr₂O₃, 0.9 MPa, 370 °C): Ru/Pr₂O₃ (9.9 mmol g⁻¹ h⁻¹, 22.23 USD/t) against Ru/CeO₂
  (4.4, 21.73), regret 2.3 %.
- The regrets stay small (median 2.3 %, max 6 %), and the effect vanishes at plant pressure: of the 19 groups measured
  at ≥ 5 MPa, where the laboratory volcano top approaches the plant optimum, one picks a different winner (the Tang
  Fe-versus-Ru group).

The two leaderboards agree on most pairs (Spearman median 0.90; 83 % of the pairwise orderings kept). What separates
them is the winner: the paper rewards the highest rate per g catalyst, the plant the cheapest metal inventory at its
own pressure.

## Corrections, 2026-10-07 (review findings A3, A7, A8 and the outlet fraction)

- **A3, fused-iron reference.** The reference pattern matched "industrial" in "80% magnetite based industrial Fe
  catalyst–20% Ce₀.₈Sm₀.₂O₂₋δ" (Ref. 10.1039/d0ta05238h), and the script then replaced its 80 wt% by the fused-iron
  71.51 wt% at 2,500 kg m⁻³. Only the commercial fused or wüstite iron catalyst used as a reference is now the reference;
  a name that states a composition (a percentage, a support after "/", an added component) or an entry with a support
  is a new catalyst with its own metal content and the supported-bed density (`run_field_chain.py`, `COMPOSITE`). In
  the 450 °C, 3 MPa group the composite was the plant leader at 17.06 USD/t; mapped like its 80 wt% Fe siblings it
  costs 19.89 USD/t, above the paper's leader (80 wt% Fe–20 wt% Ce₀.₈Sm₀.₂O₂₋δ, 18.04), which is now also the plant's
  leader: that mismatch disappears.
- **A7, one entry per measurement** (above): 25 entries removed in 18 groups.
- **A8, leaderboard basis** (above): per g catalyst in all 124 groups; the per-g-metal rule applies to no group.
- **Outlet fraction** n / (F₀ − n) instead of n / F₀ (shared with the supported chain); median |Δcost| 0.0006 USD/t;
  one entry (Ru/Ba-Ca(NH₂)₂ in Kitano 2018) now sits above 90 % of equilibrium and is flagged.

| Quantity | Before | After |
|---|---:|---:|
| primary entries with a cost / flagged | 743 / 137 | 742 / 138 |
| entries after one entry per catalyst (and per measurement) | 649 | 623 |
| groups / entries / papers | 124 / 565 / 28 | 124 / **539** / 28 |
| groups with a different winner | 45 (36.3 %) | **44 (35.5 %)** |
| 95 % CI (paper bootstrap) | 19–53 % | **18–52 %** |
| papers with a mismatch | 13 / 28 | 13 / 28 |
| regret, median of mismatched / max | 11.2 % / 76.6 % | 11.3 % / 76.5 % |
| mismatched groups with regret ≥ 1 % | 39 | 38 |
| paper-weighted share (CI) | 24.0 % (13–36 %) | 23.5 % (13–36 %) |
| pairwise orderings inverted | 262 / 1551 (16.9 %) | 231 / 1356 (17.0 %) |
| Spearman, median over groups of ≥ 3 | 0.90 (91 groups) | 0.90 (90 groups) |
| kinds: fused reference / different metal / same metal and content / different content | 18 / 14 / 11 / 2 | **17** / 14 / 11 / 2 |
| different metal: Fe on the same support / Ru beats Co | — | 12 (2 papers) / 2 (1 paper) |
| 90 % Ru recovery | 43 / 124 (CI 19–51 %), 14 papers | 43 / 124 (CI 19–51 %), 14 papers |
| per g metal | 55 / 124 (CI 29–60 %), 18 papers | 54 / 124 (CI 28–59 %), 18 papers |
| fused references removed | 28 / 115 (CI 12–38 %), 11 papers | 27 / 115 (CI 11–38 %), 10 papers |
| printed values only | 7 / 35 | 7 / 34 |
| primary entries below Fe | 30 | 29 |

## Files

- `run_field_chain.py`: the chain, self-check, groups, metrics, variants, bootstrap.
- `candidates.csv`: every extracted entry with its inputs, mapping (E_eff, α_res, α), costs, status and group.
- `group_metrics.csv`: per group n, winners, mismatch kind, regret, inversions, Spearman.
- `selfcheck_supported.csv`: the Humphreys-chain reproduction.
- `summary.json`: all numbers above.

Run: `D:\Research\CatalystForge\.venv\Scripts\python.exe run_field_chain.py` (about 3 min on one core; `--workers N`
parallelises the mapping when the machine has memory to spare — each worker loads the 130 MB response surface).
