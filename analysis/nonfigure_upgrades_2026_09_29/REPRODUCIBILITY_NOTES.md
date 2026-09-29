# Reproducibility notes for the non-figure upgrade — 2026-09-29

## Closed items

- Baseline normalized decision regret is derived directly from committed canonical objective values.
- The NH3 2026-09-20 cost-side Monte Carlo is now **exactly reconstructable at draw level** from the frozen seed, priors, FINAL-1.1 harness equations and the committed compact kinetic-input extract.
- The reconstruction reproduces the already promoted cost summary exactly:
  - minimum Ru-Fe gap = **2.3823780549 USD/t**;
  - gap p05 / median / p95 = **3.4884175202 / 7.1104234939 / 11.3792273746 USD/t**;
  - Fe and Ru cost quantiles match `nh3_cost_mc_summary.json` to machine precision.
- The reconstructed normalized regret distribution is:
  - **P(R > 0) = 1.000**;
  - p05 / median / p95 = **0.304794 / 0.408891 / 0.542538**;
  - min / max = **0.253477 / 0.645383**.
- Descriptor-correlation and common-bias sensitivities are independently reproducible from the frozen marginal assumptions and the committed 673 K volcano.

## Files

- `nh3_cost_mc_repro_inputs.json` — deterministic minimal kinetic input extracted from the frozen Wang/S1 workbook, pinned by workbook SHA256.
- `reproduce_nh3_cost_mc.py` — reconstructs all 5,000 draws and writes the draw-level CSV.
- `nh3_cost_mc_regret_summary.json` — promoted regret statistics and the expected draw-table SHA256.
- `.github/workflows/nh3-cost-mc-reconstruction.yml` — CI gate that reruns the reconstruction and uploads the draw table as an artifact.

The binary activity workbook itself remains outside Git, but the reconstruction no longer depends on its presence: the committed extract contains exactly the kinetic quantities used by the frozen harness for this calculation and is pinned to source-workbook SHA256 `fc259c5311744cccb82a7bc80ba4529f9bd34c61ed7933890dac70f016dce9ba`.
