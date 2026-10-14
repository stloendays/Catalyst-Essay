# Figure 3 — composite

Backward design now separates four logically distinct operations: the activity-only economic target, activity-only physical reachability, the joint activity/lifecycle economic target region, and the exact strict-scaling lifecycle reachability test.

183 × 122 mm, four panels: `Fig3.{svg,pdf,png}`.

Render status: **rebuilt on 2026-10-14 on NH3-FINAL-1.2 (canonical run `nh3_final_1_2_20261013`, `nh3_1_2/` analysis outputs); render manifest `../FIG3_RENDER_SHA256.txt` current**.

| Panel | Content | Source |
|---|---|---|
| a | Full-process Ru cost versus direct activity multiplier; baseline `alpha*=114.67x`; cost-side uncertainty p05–p95 = 43.52–262.28x; strict-scaling headroom shown only as a reference band. Bottom strip: measured activity gains of promoted, support-modified and confined Ru over a reference Ru catalyst on the same axis | FINAL-1.2 `breakeven_sweep.csv`, 5,000-draw cost MC (`analysis/supervisor_2026_09_20/nh3_1_2/`), `analysis/promoted_ru_literature_2026_10_05/nh3_1_2/fig3_literature_points.csv` |
| b | Lowest feasible Ru cost along the strict `E_N` scaling line; minimum 16.454819 USD/t at `E_N=-1.180 eV`, still 4.939 above Fe 11.515784 USD/t | FINAL-1.2 `scaling_reachability.csv` |
| c | Conservative direct-activity / lifetime / recovery target curves. At 99% recovery: <=1.29065x (10 y), <=0.90397x (15 y), <=0.71009x (20 y); left of alpha = 1 no activity gain is needed | `nh3_1_2/activity_lifecycle_certified_boundary.csv`, `nh3_1_2/activity_lifecycle_target_keypoints.csv` |
| d | Exact strict-scaling lifecycle boundary over all 14,510 process states. Tested box `L<=20 y, recovery<=99%` reaches parity: its best corner is 0.3167 USD/t (2.75%) below Fe; parity requires 98.3498% recovery at 20 y or 12.12 y at 99% recovery | `nh3_1_2/scaling_lifecycle_exact_global_boundary.csv`, `nh3_1_2/scaling_lifecycle_exact_summary.json` |

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

The value **1.575275x** remains a state-specific maximum activity gain and is never treated as a uniform multiplier in the joint reachability calculation.

## Build

```bash
python figures/composite/fig3/make_fig3.py
```

The script asserts the canonical activity-only and strict-scaling anchors before rendering.
