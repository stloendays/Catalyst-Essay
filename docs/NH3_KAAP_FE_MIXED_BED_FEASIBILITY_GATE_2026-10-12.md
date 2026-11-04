# NH3 / KAAP hybrid-reactor domain audit: limits of all-Fe vs all-Ru low-pressure comparisons

**Status: UNFROZEN literature and feasibility gate.** No NH3-FINAL-1.1 kinetic model, source workbook, official figure or manuscript headline value is changed.

## Why the engineering scope gate matters

The existing NH3-FINAL-1.1 model selects Fe or Ru as the entire catalyst bed, independently. The low-pressure scenario is defined by a 90-bar reaction pressure and a −20 °C separator temperature, with remaining process states optimized inside that same mask. This is a **same operating-mask single-catalyst model comparison**. It does not simulate the full KAAP commercial converter.

Peer-reviewed process research explicitly investigates serial Fe-based catalyst upstream followed by Ru/C downstream, with intercooling. In a staged reactor, Fe consumes reactants and enriches ammonia, while downstream Ru experiences different NH3 and hydrogen partial pressures and temperatures. The number of beds differs across industrial descriptions, so the actual Fe/Ru loading split is not inferred or fixed in this audit.

## Sources and supported claims

1. Tripodi, A.; Compagnoni, M.; Bahadori, E.; Rossetti, I. “Process simulation of ammonia synthesis over optimized Ru/C catalyst and multibed Fe + Ru configurations,” Journal of Industrial and Engineering Chemistry 66 (2018) 176–186. DOI https://doi.org/10.1016/j.jiec.2018.05.027 . University of Milan record https://air.unimi.it/handle/2434/618294 . It explicitly describes Fe catalysts followed by Ru/C in a multibed intercooled loop. It does not validate substituting an entire real KAAP reactor by a pure Fe bed at constant throughput.
2. “Reaction kinetics for ammonia synthesis using ruthenium and iron based catalysts under low temperature and pressure conditions,” Sustainable Energy & Fuels (2024), DOI https://doi.org/10.1039/D4SE00254G . Describes the Fe ammonia-product inhibition contrast and industrial Ru in rear sections of a multistage Kellogg reactor.
3. Humphreys et al. “Development and Recent Progress on Ammonia Synthesis Catalysts for Haber–Bosch Process,” 2021, DOI https://doi.org/10.1002/aesr.202000043 . Supports approximate KAAP operating pressure of 9 MPa and Ru on graphite; does not establish KAAP Fe replacement feasibility.

## Quantities calculated here

Read-only 14,136-state Fe catalyst analysis: at 90 bar and -20 °C, identify the optimized Fe temperature, mass, model bed volume, feasible state count and 90-m3 bed-capacity margin. The benchmark uses frozen Fe adsorption descriptor, plant 1000 tpd, Fe metal 10-year life, 25-year project DCF and 12% discount.

Fe effective-TOF alpha counterfactual: alpha values 0.10, 0.15, 0.20, 0.25, 0.5, 0.75, 1, 1.25, 1.5, 2, 3, with Fe metal inventory and bed volume divided by alpha. Assumed maximum converter bed volume scales by 0.5, 0.75, 1, 1.25 or 1.5. These choices are intentionally **unmeasured stress tests**, not laboratory uncertainty bounds or claims about promoter effects. The fixed Fe descriptor and gas-phase chemistry are not refitted. Values as low as 0.10 are deliberately extreme stress probes to exercise the model bed-volume infeasibility classifier, not realistic Fe deactivation estimates.

For KAAP mask only, compare Fe under the same 12%-discount DCF with the PR #61 Ru contract options: purchased metal, zero/one/two percent annual supplier lease, a secured lease, and one/two percent per-loading consignment. Report the Fe activity multiplier required to reach cost parity where the root actually exists; otherwise distinguish a geometric feasibility onset, Fe already lower-cost, Ru lower-cost throughout the finite test range or a discontinuous process-state switch. Never infer chemical feasibility or industrial operation solely from model bed volume.

## Unresolved engineering validation

- No serial Fe + Ru plug-flow reactor with axial chemical-potential/partial-pressure evolution.
- No exothermic energy-balance and inter-bed heat exchange or pressure-drop model.
- No validation of Fe bed activity near 90 bar at matched H2/N2/NH3 feed, residence time and outlet conversion.
- No measured KAAP converter volume or verified Fe/Ru bed allocation and replacement schedules.
- No verified Ru metal leasing contract or price, recycling of salt to fine metal, Ru catalyst deactivation or supplier guarantee.
- No proof that the 90-m3 capacity cap is a real KAAP plant engineering limit.
- No justification for simply linearly mixing whole-bed Ru and Fe costs: serial reaction kinetics make that economically invalid.

## Scientific language gate

**Allowed:** “Under a 90-bar same-mask single-catalyst synthesis-loop surrogate, the Ru vs Fe catalyst-responsive cost ranking depends on financing and physical/economic feasibility assumptions.”

**Not allowed without a validated mixed-bed plant reactor model:** “A real KAAP all-Fe converter beats Ru at $X/t” or “the 0.925% rent threshold is a verified commercial KAAP lease criterion.”

The whole-bed Ru/Fe baseline, including all rent thresholds, remains an **unfrozen model counterfactual**. Primary industrial data and process/engineering validation are still required.

## Reproduction

GitHub Actions: .github/workflows/nh3-ru-net-recovery-boundary.yml. New script: analysis/nh3_ru_net_recovery_boundary_2026_10_12/run_kaap_feasibility_audit.py. New tests: test_kaap_feasibility_math.py. New outputs: kaap_fe_volume_alpha_sweep.csv, kaap_fe_contract_contingency.csv, kaap_fe_effectiveness_parity.csv, kaap_feasibility_gate_report.json and kaap_fe_model_feasibility_gate.png.

At alpha=1 and a 90-m3 Fe bed cap, the script must match the merged 25-year Fe DCF cost reference in both main and KAAP masks to 1e-9 USD/t. The machine-readable report must explicitly set serial_Fe_then_Ru_reactor_implemented=false, full_multibed_KAAP_process_economics_is_verified=false, and may_replace_frozen_manuscript_claims=false.
