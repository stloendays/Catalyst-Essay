# Ru/C net-recovery economic decision boundary (2026-10-12)

**NH3-FINAL-1.2:** the three scripts take `NH3_MODEL=1.1|1.2` (`analysis/nh3_model.py`; default 1.1, which writes the
committed files here). 1.2 outputs and the 1.1 → 1.2 table are in `nh3_1_2/` (see `nh3_1_2/README.md`).

**Status: derived, exploratory analysis.** No modification to the frozen NH3-FINAL-1.1, Wang/S1 source workbook, original 15-metal ranking or official figures. The GitHub Actions workflow runs the calculation on a fresh Linux runner and publishes machine-readable CSV artifacts.

## Question

When does a supported, promoted Ru/C ammonia catalyst equal Fe in **the same loop**, after allowing for partial monetary realization of recovered Ru and its actual supported-bed volume?

The original frozen cost accounting credits recovered Ru metal at its purchase price. We retain that formula but replace its recovery input with a **net credit fraction** `q = f_recovered × eta_net_value`, where `eta_net_value` is a *scenario* (0.8, 0.9, 1.0), not a measured plant recovery-cost coefficient. Its interpretation is a compact sensitivity for refining, salvage discounts and lag. Do not claim that these are measured cash flows or that a uniform adjustment accounts for replacement logistics, finite catalyst age or discounting rigorously. A fully dated discounted-cash-flow cost is still needed for final industrial inference.

The analysis uses physically promoted spent Ru/C recovery scenarios 90%, 91.1%, 93.05%, 94.6%, 95.55%, with 0% and 80% counterfactuals; 8 wt% commercial Ru loading (5–10% sensitivity) and density 430–550 kg/m3 (490 midpoint). Comparison is separately to Fe's unconstrained optimum 15.2917046766 USD/t and Fe in the **same KAAP mask** (90 bar and -20 C) 19.0686886119 USD/t. The KAAP mask is a process-model proxy: Fe performance within this mask does not validate a commercial Fe retrofit of a Ru-promoted KAAP converter.

## Outputs

- `cost_surface.csv`: independently reoptimized Ru across its permitted frozen states for every loop × loading × density × recovery × net-value realization; sign of Ru minus Fe **within the same loop**; also reports whether it beats Fe's global best.
- `parity_boundary.csv`: exact-to-grid binary search for the smallest `q` yielding `C_Ru <= C_Fe`. Convert to required *physical* recovery by `r*=q*/eta`, mark unreachable when r*>1, and additionally mark whether it lies below the promoted Ru/C 95.55% source upper bound.
- `summary.json`: frozen reference values, cell counts, applicability limitations and cross-check count.
- `test_boundary_math.py`: independent arithmetic and sign/threshold regressions.

The existing `promoted_recovery_check.csv` is a numerical golden reference. At `eta=1`, r=0.90 and 0.9555, loading = 5/8/10%, density = 430/550, both loops, all **24 matching cells must agree within 1e-9 USD/t**, or the cloud job fails. The frozen 15-metal and process-state inputs are never modified or regenerated.

## Reproduction

```bash
pip install numpy scipy pandas openpyxl pyyaml
python -m unittest discover -s analysis/nh3_ru_net_recovery_boundary_2026_10_12 -p 'test_*.py' -v
python analysis/nh3_actual_ru_params_2026_10_07/build_harness_root.py /tmp/nh3_harness --workers 4
NH3_HARNESS=/tmp/nh3_harness python analysis/nh3_ru_net_recovery_boundary_2026_10_12/run_boundary.py
```

Cloud workflow: `.github/workflows/nh3-ru-net-recovery-boundary.yml` (PR or manual dispatch), with downloadable CSV/JSON artifact.

## Claims and blockers

- Claim only *model-conditioned* Fe/Ru decision boundaries. A locally preferred KAAP Ru does not imply globally cheapest Ru plant: a same-loop comparison and separately optimized full-plant selection answer different questions.
- The 95.55% source is a promoted Ru/C laboratory recovery example reported as recovered Ru salt, not independently verified commercial metal buyback yield. The full possible 97.61% is unpromoted Ru/C and must not be the headline promoted upper bound.
- Realizing a salvage credit requires evidence for refining cost, fractions reaching saleable metal, refining purity, catalysts' physical lifespan, site exposure/dispersion and industrial plant compatibility.
- Continuous pressure optimization beyond the frozen 14,136-state library and feasibility of an Fe catalyst in a KAAP-style low-pressure loop are not established here.
- **Do not edit manuscript numbers or re-freeze the main results on the basis of this exploratory overlay.** Confirm CI and expert/primary literature inputs first.


## Finite 25-year metal cash-flow audit (additive extension, same PR)

The frozen plant assumptions are **12% discount rate**, **25-year plant life**, and **10-year nominal catalyst replacement life**. Frozen metal costs previously used a straight-line purchase-minus-recovery charge, even though reactor/compressor fixed assets carry a 12%-discount capital-recovery factor. This extension addresses that **accounting mismatch**, and is not a revision of the canonical numbers.

For a metal inventory of M kg purchased at price P USD/kg, with collector return r, refining yield y, monetary sale payout f, per-collected-kg processing fee c and resale delay tau, the 25-year metal present cost is:

    PV = sum_k [M P / (1+i)^(purchase_k)]
       + sum_j [M r c / (1+i)^(retirement_j)]
       - sum_j [M r y f P / (1+i)^(retirement_j+tau)]

The equivalent annual metal cost is CRF(i,25) × PV, divided by annual tonnes NH3. Fe is **recalculated on exactly the same metal-financing convention** with its baseline 0% recovery, 10-year replacement life and same process feasibility mask. Plant OPEX, reactor/pressure CAPEX and the 14,136-state process physics are unchanged. The metal-finance-rate sweep 0–12% is a counterfactual to show what cheaper metal leasing could change; it does **not** adjust the reactor financing rate, which remains frozen at 12%.

- Case grid: physical gross Ru recovery 90%, 93.05% and 95.55%; Ru life 5/10/15 years; Ru loading 5/8/10 wt%; bed densities 430/490/550 kg/m3; main and KAAP masks; ideal zero-interest, ideal 12%-interest, mild process losses, strong process losses. These produce 648 lifecycle cases.
- Financing sensitivity: 0, 0.5, 1, 2, 4, 8 and 12% metal financing over the 18 loop/bed choices, each at three recovery fractions, Ru life 10 years: 378 more cases.
- Scenario process penalties: 95% refining yield/95% market-price sale/500 USD per collected kilogram/0.5-year delay (mild); 85%/90%/1,500 USD per kg/one-year delay (strong). **These numbers are hypothetical stresses, not supplier quotes or primary industrial yield measurements.** Ru recovery as a salt must not be equated to saleable metallic Ru.
- Financial assumption: replacement at t=0, L, 2L ... strictly before project closure and attempted recovered-metal resale on replacement and at project year 25. Crediting the final partly used catalyst at closure is **optimistic**; the model omits ownership/lease contract restrictions, market price paths, taxes, end-of-project dismantling costs and catalyst-volume lifetime deterioration.
- Regression: the 20-year/10-year, zero-financing, full-terminal-recovery algebra **must reproduce the earlier 24 benchmark rows within 10^-9 USD/t** for each loop and own-bed corner. Actual results retain the 25-year cash-flow horizon, which need not reproduce the frozen straight-line figure numbers.

New cloud outputs: lifecycle_dcf_report.json, lifecycle_cost_scenarios.csv, lifecycle_finance_sensitivity.csv, lifecycle_legacy_regression.csv, lifecycle_financing_break_even.png. The finite-project result is a **model-conditioned financial sensitivity**; any claim about bankable Ru leasing or industrial Ru-metal refining requires commercial primary evidence.

Run from a clean CI checkout after the frozen response cache is constructed:

    NH3_HARNESS=/tmp/nh3_harness python analysis/nh3_ru_net_recovery_boundary_2026_10_12/run_lifecycle_cashflow.py

**Editorial gate:** Do not replace the canonical ranking or same-loop Figure 3 values until a domain expert validates the Ru metal inventory financing contract, final recovery yield, and genuine feasibility of Fe in the KAAP loop.


## Supplier-owned Ru/C metal, leasing, consignment and buyback (new PR, 2026-10-12)

The project rate is FIXED at 12% for all operator cash flows and unchanged Fe/Ru process optimization. Operator-owned Ru metal and Fe metal follow their dated 25-year purchase-and-salvage DCF. In hypothetical supplier-owned leasing/consignment, the customer does NOT pay the Ru metal principal upfront; instead it pays annual rent or per-loading service fees, optional refundable collateral, fine-Ru metal loss make-up at collection, and separate processing costs. **Metal principal cannot appear as both purchase and lease cost.** Customer-owned metal in a refinery **pool account is NOT treated as supplier-owned** merely because it is recorded in the provider's ledger.

- Annual lease rates: 0, 0.5, 1, 2, 4, 8, 12% of frozen Ru spot value.
- Consignment service fee per loading: 0, 0.5, 1, 2, 4% of Ru value.
- Security deposit: either 0 or 25% of Ru value, refunded at year 25 (hypothetical).
- Physical recovery: 90, 93.05, 95.55%; Ru/C loading 5/8/10 wt%, bed density 430/490/550 kg/m³; nominal metal life 10 years, fixed project life 25.
- Refining stress: either perfect refining or an assumed 95% metallization yield, $500/kg gross collected Ru processing fee and a half-year metal-loss bill settlement delay. Delayed loss billing benefits the operator under DCF, and is therefore only a scenario, not an assumption about actual supplier practice.
- Owned/guaranteed buyback: modeled as the original owner DCF with future sale payout fractions of 80, 90, 95 or 100% of certified fine Ru, not a confirmed commercial repurchase agreement.
- All fee percentages, collateral provisions, fine-metal make-up liability, payment timing and buyback guarantees are **model inputs, not verified contract quotes**. Public documents establish available PGM trading mechanisms, not their Ru-ammonia process applicability or rates. See the source audit in docs/NH3_RU_COMMERCIAL_TERMS_SOURCE_AUDIT_2026-10-12.md.

New workflow calls run_contract_structures.py after 25-year owned DCF, checks baseline identity, solves critical lease-rate thresholds and regenerates all 1,890 contract case rows and 162 thresholds with byte-for-byte repeatability. Figures and machine-readable outputs are available as Actions artifacts:

- contract_terms_report.json
- contract_cost_surface.csv
- contract_parity_thresholds.csv
- contract_structure_parity.png

**Use this to test the importance of contractual metal ownership; never claim a market-available KAAP Ru metal lease at any of the modeled rates.**


## Fe feasibility and hybrid-reactor model-domain gate (additive, PR #61)

The same 90-bar / -20C Fe vs Ru comparison is a **single-metal whole-bed process-state counterfactual**. It does not simulate a KAAP multibed converter with Fe upstream and Ru downstream. Peer-reviewed literature (Tripodi et al. 2018, DOI 10.1016/j.jiec.2018.05.027; RSC 2024 DOI 10.1039/D4SE00254G) explicitly describes Fe+Ru multibed arrangements and gas-composition differences.

The new read-only run_kaap_feasibility_audit.py records nominal Fe cost, feasible volume and temperature against the frozen 90 m3 catalyst-bed limit. It then probes an **unmeasured, hypothetical** Fe effective-TOF alpha factor 0.10–3 and a hypothetical assumed-bed-cap factor 0.5–1.5, while preserving the complete fixed 14,136-state Fe response, finances and validated Ru contract costs. Its cost-parity solver refuses to mistake the onset of geometric feasibility for genuine Fe/Ru cost equality. Its machine-readable report blocks any claim of validated industrial KAAP Fe replacement or modeled serial Fe–Ru beds.

See docs/NH3_KAAP_FE_MIXED_BED_FEASIBILITY_GATE_2026-10-12.md. Outputs: kaap_fe_volume_alpha_sweep.csv, kaap_fe_contract_contingency.csv, kaap_fe_effectiveness_parity.csv, kaap_feasibility_gate_report.json and kaap_fe_model_feasibility_gate.png. Do not replace canonical manuscript figures or claims.
