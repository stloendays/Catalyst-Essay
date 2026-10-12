# Ru catalyst-metal financing: documented practice, documented rates, and Ru vs Fe at those rates (2026-10-12)

**Status: unfrozen, exploratory.** No frozen output, manuscript text, figure or existing analysis folder is changed.
The calculation reuses the merged PR #57 owned-metal cash flow and the PR #61 supplier-lease algebra unchanged.
Sources are in `EVIDENCE.md` (S01–S25).

## Numbers first

KAAP-type loop (90 bar, −20 °C separation), 8 wt % Ru/C, 490 kg/m³, 95.55 % gross Ru recovery, 10-year Ru life,
25-year project. USD per t NH₃; gap = Ru − Fe (negative: Ru cheaper).

- **Owned** (PR #57): the operator buys each Ru charge; Ru and Fe metal cash flows are discounted at the stated
  rate; reactor and process costs stay at the frozen 12 %/25 y. Parity below **0.56 %/y**.
- **Lease** (PR #61, `lease_unsecured`): the supplier keeps title; the operator pays the stated rate × Ru value
  each year and settles the fine-metal shortfall at each return; all operator cash flows at 12 %. Parity below
  **0.92 %/y**.

| Rate and its documented basis | %/y | Owned: Ru / Fe (gap) | vs 0.56 | Lease: Ru / Fe (gap) | vs 0.92 |
|---|---:|---|---|---|---|
| Pt market-implied 1-month lease rate before credit spread, normal pre-2020 range −0.2 to 0 (S11) | 0.00 | 18.84 / 19.09 (**−0.25**) | below | 18.52 / 19.14 (**−0.62**) | below |
| Pt market-implied lease rate, 2021 average (S12) | 0.80 | 19.19 / 19.09 (+0.10) | above | 19.09 / 19.14 (**−0.05**) | below |
| Industrial all-in, minimum of 32 PBF catalyst-metal leases 2013–22 (S01–S03) | 1.35 | 19.43 / 19.09 (+0.34) | above | 19.33 / 19.14 (+0.19) | above |
| Industrial all-in, median of the 32 PBF leases | 2.10 | 19.75 / 19.09 (+0.66) | above | 19.66 / 19.14 (+0.52) | above |
| Industrial all-in, maximum of the 32 PBF leases | 5.10 | 20.59 / 19.11 (+1.48) | above | 20.57 / 19.14 (+1.43) | above |
| Frozen plant rate (PR #57 baseline, not a market rate) | 12.00 | 21.79 / 19.14 (+2.64) | above | 21.79 / 19.14 (+2.64) | above |

1. **Every all-in rate an industrial user is documented to have paid for catalyst metal lies above both parity
   thresholds.** Over the 32 PBF platinum and palladium catalyst leases of 2013–2022 (1.35–5.10 %/y, median
   2.10 %), Fe stays cheaper by 0.34–1.48 USD/t if Ru is owned and 0.19–1.43 USD/t if it is leased. Against the
   12 % basis (+2.64 USD/t) the documented financing cost removes 44–87 % (owned) or 46–93 % (lease) of the gap,
   but does not close it.
2. **Ru reaches Fe only at market-implied Pt lease rates before any credit spread:** 0 % (the normal pre-2020
   level) under both structures, and the 2021 average of 0.8 % under the lease structure only (by 0.05 USD/t).
   No disclosed industrial contract was written at those levels: in 2019, when implied Pt rates were near 0 %
   (S10, S11), PBF's new contracts carried 1.35–1.80 % (S02).
3. **No Ru rate exists to apply.** No Ru lease rate, Ru forward curve or Ru lease contract was found; Ru is outside
   the LPPM standards (S16). Every rate above is documented for Pt or Pd (or Au); applying it to Ru is an analogy.
4. **KAAP:** no public source describes how a KAAP converter's Ru charge is sold, leased or financed. One KAAP
   operator, Point Lisas Nitrogen, carried 2.0 MUSD of Ru it owned in inventories at end-2008 (S21, S22).

### Other documented levels (all above both thresholds)

| Rate | %/y | Kind | Owned gap | Lease gap |
|---|---:|---|---:|---:|
| Umicore gold lease-in 2025, cost over proceeds (S25; derived, Au) | 1.22–1.95 | derived | +0.28 to +0.59 | +0.13 to +0.45 |
| Pd 1-month average about 2001–02 (S14) | 1.45 | quoted | +0.38 | +0.23 |
| LyondellBasell short-term debt, 94 % precious-metal financings, end-2017 (S05) | 1.80 | derived | +0.53 | +0.39 |
| Evonik cost-tool default interest on owned metal stock (S17) | 2.00 | quoted default | +0.61 | +0.47 |
| Pt implied 1-month, Apr–Jul 2020 average (S11) | 3.0 | quoted | +1.04 | +0.92 |
| Pd 1-week, March 2018 (S15) | 6.0 | quoted | +1.64 | +1.59 |
| PBF reset fee / proceeds, Delaware City 2010–11 (S01) | 6.16 | derived | +1.66 | +1.61 |
| Pt implied 1-month, peak 16 Apr 2020 (S11) | 6.7 | quoted | +1.75 | +1.71 |
| Pt 1-month average about 2000–02 (S14) | 9.0 | quoted | +2.14 | +2.11 |
| Pt implied 1-month / 3-month, May 2022 (S12) | >10 / >12 | quoted | +2.31 / +2.64 | +2.29 / +2.64 |
| Pt lease cost, July 2025 (S13) | ≈30 | quoted | +5.67 | +5.82 |

### Parity thresholds by recovery (flagship bed)

| Gross Ru recovery | Owned | Lease, unsecured | Lease, 25 % refundable collateral | Lease, 95 % refining yield + 500 USD/kg + 0.5-y delay |
|---:|---:|---:|---:|---:|
| 90 % | none (Ru > Fe at 0 %) | 0.58 % | none | 0.30 % |
| 93.05 % | 0.25 % | 0.77 % | none | 0.47 % |
| 95.55 % | 0.56 % | 0.92 % | none | 0.61 % |

Lease variants are those of PR #61. With 25 % collateral posted at the 12 % opportunity cost, Ru stays 0.92 USD/t
above Fe even at zero rent.

### Robustness over the KAAP bed grid

27 cells (5/8/10 wt % Ru, 430/490/550 kg/m³, 90/93.05/95.55 % recovery), `kaap_grid_headline_rates.csv`:

| Rate | Owned: cells with Ru ≤ Fe | Owned gap range | Lease: cells with Ru ≤ Fe | Lease gap range |
|---|---:|---|---:|---|
| 0 % | 16/27 | −0.40 to +0.21 | 27/27 | −0.77 to −0.11 |
| 0.8 % | 0/27 | +0.05 to +0.53 | 10/27 | −0.11 to +0.25 |
| 1.35 % (PBF min) | 0/27 | +0.28 to +0.76 | 0/27 | +0.14 to +0.49 |
| 2.10 % (PBF median) | 0/27 | +0.60 to +1.07 | 0/27 | +0.47 to +0.82 |
| 5.10 % (PBF max) | 0/27 | +1.46 to +1.64 | 0/27 | +1.40 to +1.55 |

## Evidence summary

Full table with quotes, URLs, dates and limits: `EVIDENCE.md`.

**Documented practice.**
- Refiners sell their Pt and Pd catalyst metal to banks and lease it back for 8 months to 3 years, accounted as debt
  with payments in interest expense and repurchase at market value (PBF, every refinery, 2010–2023: S01–S03; HF
  Sinclair, terms of one year or less, 2022–2025: S04).
- A petrochemical producer leases the precious metals used in its processes (LyondellBasell: S05).
- Catalyst suppliers offer PGM leases and consignments for catalyst production, use and recycling, and pool
  accounts (BASF group/Metivo: S06). Heraeus trades Ru, runs metal accounts, refines Ru-on-carbon catalysts and
  lends metal while a new catalyst is made (S07, S08). Johnson Matthey leases from banks for under 12 months and
  processes customer-owned metal (S09).
- Industrial uses hold the largest share of leased Pt; when lease rates spiked in 2025, users moved to ownership
  (WPIC: S10). Refiners keep catalyst Pt in pool accounts and lose 3–5 wt % per cycle in metal settlements (S20).
- Ownership is equally documented: nitric-acid producers carry gauze metal as inventory (S23, S24); a KAAP plant
  carried Ru in inventory (S21).

**Documented rate levels.**
- All-in industrial: 32 fixed PBF rates, 1.35–5.10 %/y, median 2.10 % (2013–2022, Pt and Pd).
- Market-implied Pt lease rates before credit spread: −0.2 to 0 % before 2020, near 0 % for much of the 2010s;
  0.8 % average in 2021; spikes to about 7 % (2020), over 10–12 % (2022) and nearly 30 % (2025). Pt 9 % and Pd
  1.45 % averages around 2000–2002. Pd 6 % (1-week, 2018).
- Ru: none published. Rh: no rate series found.

**Treatment of metal inventory in economics conventions.**
- US tax treats recoverable precious metal in a manufacturing process, with a refiner's platinum catalyst as the
  example, as non-depreciable; only the unrecoverable share depreciates (S18).
- Accounts carry owned catalyst metal as inventory (S21, S23, S24) or, after a sale-leaseback, as a financing
  liability whose cost is interest (S01, S04, S05, S09).
- A supplier's costing tool charges interest (default 2 %/y) on the user's own metal stock (S17).
- A public TEA guideline has no precious-metal rule: working capital zero, all overnight capital depreciated
  (NETL: S19). The frozen model follows this generic convention: Ru is charged like equipment, at the 12 % capital
  recovery factor with replacement every 10 years.
- Textbooks (Peters–Timmerhaus–West, Towler–Sinnott, Turton et al.) were not accessible in this session.

## Model inference (not in the sources)

- Reading a documented lease rate as the owned-metal financing rate of PR #57 assumes metal-denominated
  (price-hedged) financing, the reading PR #57 gives its 0–12 % sweep. The lease structure of PR #61 uses the rate
  directly as rent.
- Practice treats recoverable catalyst metal as a financed stock carrying a metal financing rate, documented at
  1.35–5.10 %/y for Pt and Pd, rather than as equipment carrying the 12 % hurdle. On that basis the KAAP-loop Ru–Fe
  gap is +0.19 to +1.48 USD/t NH₃ (1–8 % of Fe's 19.1 USD/t), not +2.64.
- Parity needs a rate of 0–0.9 %/y, which matches only the market lease rate a bullion bank charges before the
  lessee's credit spread. The 2019 PBF contracts suggest that spread was about 1.3–1.8 points.
- A Ru lessor has no forward market to hedge against, so a Ru rate below the Pt/Pd industrial range would need a
  specific counterparty (for example the catalyst licensor or supplier) to provide it. This is the open commercial
  question. A written quote would settle it.

## Method and regression checks

- `run_documented_rates.py` imports `lifecycle_cashflow.py` from `analysis/nh3_ru_net_recovery_boundary_2026_10_12/`
  (main) and `supplier_metal_contracts_pr61.py`. The latter is a byte-identical copy of
  `supplier_metal_contracts.py` from branch `nh3-ru-commercial-terms-2026-10-12` at `acefeed` (git blob
  `c2f24bb9`), checked by `test_documented_rates.py`.
- Checks that must pass before any output is written:
  - all 378 rows of PR #57 `lifecycle_finance_sensitivity.csv` are reproduced within 1e-9 USD/t;
  - the PR #57 flagship is reproduced (Ru 21.786 vs Fe 19.142 USD/t at 12 %), as is its owned hurdle
    (0.5604191 %/y);
  - the PR #61 unsecured-lease parity is reproduced as 0.9246 %/y;
  - the lease Fe reference equals PR #57's 12 % Fe.
- Lease rent equal to the 12 % plant rate gives exactly the owned-12 % result (21.786 USD/t), as it should.
- The 14,136-state frozen response cache, the frozen prices, the 12 % plant rate, the 25-year life and the 10-year
  catalyst life are asserted, not changed.

## Files

| File | Content |
|---|---|
| `EVIDENCE.md` | Source table S01–S25 (claim, quote ≤15 words, URL, date, what it supports and does not), searches that found nothing |
| `pbf_catalyst_lease_contracts.csv` | 32 PBF catalyst lease/financing contracts with rate, metal, term and SEC URL |
| `documented_rates.csv` | Every rate evaluated, with kind (quoted, derived, computed), metal, tenor and source ID |
| `run_documented_rates.py` | Calculation and regression checks |
| `flagship_documented_rates.csv` | Ru, Fe and gap at each rate, owned and three lease variants |
| `parity_thresholds_by_recovery.csv` | Parity rate per structure at 90/93.05/95.55 % recovery |
| `kaap_grid_headline_rates.csv` | 27-cell KAAP grid at 0, 0.8, 1.35, 2.10, 5.10 % |
| `summary.json` | Headline numbers, regressions, grid counts |
| `supplier_metal_contracts_pr61.py` | Vendored PR #61 module (unchanged) |
| `test_documented_rates.py` | Harness-free checks of the tables, vendored module and threshold classification |

## Reproduction

```bash
python -m unittest discover -s analysis/nh3_ru_metal_financing_evidence_2026_10_12 -p 'test_*.py' -v
python analysis/nh3_actual_ru_params_2026_10_07/build_harness_root.py /tmp/nh3_harness --workers 4
NH3_HARNESS=/tmp/nh3_harness python analysis/nh3_ru_metal_financing_evidence_2026_10_12/run_documented_rates.py
```

The committed outputs were produced against the local NH₃ harness with its pinned 14,136-state response cache
(about 12 s).
