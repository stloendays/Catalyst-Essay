# Figure 3 — composite

Backward design now separates four logically distinct operations: the activity-only economic target, activity-only physical reachability, the joint activity/lifecycle economic target region, and the exact strict-scaling lifecycle reachability test.

183 × 122 mm, four panels: `Fig3.{svg,pdf,png}`.

| Panel | Content | Source |
|---|---|---|
| a | Full-process Ru cost versus direct activity multiplier; baseline `alpha*=201.22x`; cost-side uncertainty p05–p95 = 70.78–462.00x; strict-scaling headroom shown only as a reference band | FINAL-1.1 `breakeven_sweep.csv`, 5,000-draw cost MC |
| b | Lowest feasible Ru cost along the strict `E_N` scaling line; minimum 21.397873 USD/t at `E_N=-1.215 eV`, still above Fe 15.291705 USD/t | FINAL-1.1 `scaling_reachability.csv` |
| c | Conservative direct-activity / lifetime / recovery target curves. At 99% recovery: <=2.41794x (10 y), <=1.74213x (15 y), <=1.40129x (20 y) | `activity_lifecycle_certified_boundary.csv`, `activity_lifecycle_target_keypoints.csv` |
| d | Exact strict-scaling lifecycle boundary over all 14,136 process states. Tested box `L<=20 y, recovery<=99%` misses parity by 0.07078 USD/t at its best corner; parity requires 99.1186% recovery at 20 y or 22.69 y at 99% recovery | `scaling_lifecycle_exact_global_boundary.csv`, `scaling_lifecycle_exact_summary.json` |

## Scientific reading order

```text
activity-only target
        ->
activity-only reachability
        ->
joint economic target region
        ->
strict-scaling joint reachability
```

The important distinction is **target versus reachability**. Panel c reports the catalyst-property combinations economics asks for; Panel d independently tests whether the strict scaling-constrained materials space reaches those requirements.

The value **2.524565x** remains a state-specific maximum activity gain and is never treated as a uniform multiplier in the joint reachability calculation.

## Build

```bash
python figures/composite/fig3/make_fig3.py
```

The script asserts the canonical activity-only and strict-scaling anchors before rendering.
