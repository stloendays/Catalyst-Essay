# NH3 Fe–Ru Catalyst Metal Lifecycle DCF Audit (2026-10-12)

**Status:** Derived, exploratory, independent of frozen NH3-FINAL-1.1. PR [#57](https://github.com/stloendays/Catalyst-Essay/pull/57) remains a draft.

## Cloud provenance and verification

- Code commit a066d8878884ff6e6a138c7b1c13e2035686e456 on branch nh3-ru-net-recovery-boundary-2026-10-12.
- [GitHub Actions run 38243242863](https://github.com/stloendays/Catalyst-Essay/actions/runs/38243242863): both boundary and verify checks PASS.
- Pinned frozen response: 14,136 process states and unchanged Wang/S1 workbook hash.
- Unit tests: **12/12 PASS**. Independent legacy-equivalence cross-checks: **24/24 PASS** at 1e-9 USD/t using the appropriate 20-year/10-year, 0% cash-flow limit.
- Both derived DCF datasets and summary reproduced byte-for-byte. Artifact ID 11743547856, SHA256 7f0ef289e92de134ee3abc27e94681691513b4345d5187dadfcd01f1850db241. Archive also contains the financing figure and previously established Fe–Ru parity figure.

## Scientific question and explicit accounting

Frozen plant economics use a 12% discount rate and 25-year capital life for equipment, yet annualize metal purchase minus recovery without an inventory carrying charge. To test sensitivity to this convention, the new extension explicitly discounts fresh-catalyst purchases at 0, 10 and 20 years and spent-catalyst refining/sale at 10, 20 and 25 years (for ten-year catalyst life). The final partially used catalyst is assumed collected and monetized on plant decommissioning, which is **optimistic for Ru**. The same dated metal-cost convention is applied independently to Fe (zero metal recycling credit) and Ru. All original reactor, compression, energy and frozen kinetic calculations remain unchanged.

For initial active-metal inventory M, purchased at price P, physical spent-metal recovery r, refining yield y, payout as a fraction f of metal spot price, recycling fee c per kg of collected metal, financing/discount rate i and sale delay tau, the present cost is:

    PV = sum[ M*P / (1+i)^purchase_time ]
       + sum[ M*r*c / (1+i)^collection_time ]
       - sum[ M*r*y*f*P / (1+i)^(collection_time+tau) ].

Annual metal cost = PV × CRF(i,25) / annual ammonia production. This is an optional derived financial layer, not a revision of canonical Ru-price data.

## Numerically verified KAAP-type low-pressure comparison

Same modeled pressure and separator for both catalysts: 90 bar, −20 °C; Ru/C 8 wt%, bulk bed density 490 kg m−3, exposure u=11, gross Ru recovery 95.55%, Ru life 10 years. Metal-specific rate changes; reactor financing remains at the frozen 12%.

| Accounting scenario | Fe USD/t | Ru USD/t | Ru−Fe USD/t |
| --- | ---: | ---: | ---: |
| 25-year / zero metal carrying / 100% sale and refining | 19.087 | 18.839 | **−0.248** |
| 25-year / 12% metal discount / 100% sale and refining | **19.142** | **21.786** | **+2.644** |
| 12% / 95% refining yield / 95% market payout / $500/kg collected / 0.5-year sale delay | 19.142 | 21.949 | +2.808 |
| 12% / 85% refining yield / 90% market payout / $1,500/kg collected / 1-year delay | 19.142 | 22.145 | +3.004 |

**Conditional financing hurdle:** in this flagship geometry, with 95.55% physical recovery, ideal downstream refining/sale, no handling fee or payment delay, the Ru/Fe same-loop parity rate is **0.5604% per year**. Above this threshold Ru is more expensive under the modeled ownership and inventory-financing convention. Under zero metal financing, the 25-year model still requires **95.286% price realization per recovered unit**. At the frozen 12% financial rate no sale fraction between 0 and 100% reaches Fe parity.

## Grid stress-test classification

648 lifecycle comparisons = 4 scenarios × 2 loop masks × 3 Ru loadings × 3 bed densities × 3 physical recoveries × 3 Ru lives. The separate metal rate sweep has 378 scenarios.

| Scenario | Main loop Ru cheaper | KAAP mask Ru cheaper |
| --- | ---: | ---: |
| Zero metal-specific carrying, ideal refining and sale | 0/81 | **49/81** |
| 12% metal-specific rate, ideal refining and sale | **0/81** | **0/81** |
| 12%, mild refining and payment losses | 0/81 | 0/81 |
| 12%, strong refining and payment losses | 0/81 | 0/81 |

These are counts of **prespecified deterministic parameter cells, not frequencies or statistical probabilities**. The main-loop Fe comparator is globally optimized in the frozen state library; KAAP Ru and Fe are compared inside the identical low-pressure and separator mask.

## Reconciliation with earlier Ru recovery result

The earlier effective recovery credit q* = 0.896599 and its 93.84% realization threshold remain correct **under the original straight-line ten-year replacement accounting**. They cannot be used as the financing-adjusted 25-year break-even threshold.

The newer 25-year DCF sensitivity demonstrates that recovery and catalyst turnover financing are tightly coupled. It does **not** prove commercial Ru catalyst is uneconomic: Ru procurement may involve loans, leasing, consignment or guaranteed metal-return credit, none of which have yet been verified or modeled from actual industrial contract terms.

## Physical and literature limitations

1. Patent Ru recovery up to 95.55% refers to promoted spent Ru/C recovery as a Ru salt, not a verified buyback yield of saleable Ru metal. The refining yields, payouts, fees and settlement delays in the DCF are explicitly **hypothetical stresses**, not measurements or supplier quotations.
2. Fe satisfying a 90-bar KAAP model mask does not confirm it can replace the Ru beds in an actual KAAP converter. Isothermal finite-grid feasibility is only a first modeling check.
3. Ru/Fe results cover catalyst-responsive cost contributions rather than full ammonia production costs; gas feed, tax and metal-price paths are outside the extension.
4. Final partially used Ru bed was recovered optimistically; equipment decommissioning and resale cash flows require validation.
5. No original frozen model, SI table, official figure, abstract or manuscript conclusion was replaced.

## Before manuscript adoption

Obtain real Ru supply/lease terms, recycling contract and metal-return settlement dates; independently check the chemistry of converting recovered salts into saleable metal; assess end-of-project metal residual value and genuine engineering feasibility of Fe in the low-pressure loop. Treat all current DCF values as model-conditioned sensitivity results. Reproduce from GitHub Actions workflow nh3-ru-net-recovery-boundary.yml (PR #57).
