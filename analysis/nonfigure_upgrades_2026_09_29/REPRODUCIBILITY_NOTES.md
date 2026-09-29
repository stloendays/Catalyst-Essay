# Reproducibility notes for the non-figure upgrade — 2026-09-29

## Closed

- Baseline normalized decision regret is derived directly from committed canonical objective values.
- The **sign** of decision regret under the existing uncertainty studies is supported by committed summary/rank-probability evidence:
  - NH3 economic-parameter MC: Fe lower than Ru in 5000/5000 draws.
  - MeOH economic-parameter MC: canonical economic order retained in 5000/5000 draws.
  - Au/TiO2 control: complete order retained in 10000/10000 draws.
- Descriptor-correlation and common-bias sensitivities are independently reproducible from frozen marginal assumptions and the committed 673 K volcano.

## Remaining provenance item before submission

The NH3 2026-09-20 cost-side Monte Carlo preregistration states that a complete draw-level table is retained, but the current repository snapshot contains only:

- `analysis/supervisor_2026_09_20/nh3_cost_mc_summary.json`
- `analysis/supervisor_2026_09_20/nh3_cost_mc_histogram.csv`

The per-draw cost table is not present in the current Git tree. Therefore this audit **does not invent** a median or 95% interval for normalized regret magnitude. The manuscript may report the already-supported sign probability `P(regret>0)=1.000` for the cost-side MC, but an uncertainty interval for regret magnitude should be added only after the original draw-level table is restored or the preregistered simulation is exactly regenerated.

This is a provenance-completeness issue, not a contradiction in the published summary values.
