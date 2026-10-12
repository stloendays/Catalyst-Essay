# Ru/C net-recovery economic decision boundary (2026-10-12)

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
