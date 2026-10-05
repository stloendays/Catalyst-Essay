# Figure 3 backward-design panel specification — 2026-09-29

Status: **CLOSED AND PROMOTED**.

## Scientific message

The figure must distinguish what economics **requires** from what the scaling-constrained catalyst space can **reach**.

### Panel a — activity-only economic target

Show fully reoptimized Ru cost against a direct activity multiplier.

Canonical anchors:
- Ru activity-only parity: **201.223x**;
- cost-MC target distribution: **70.78x / 174.27x / 462.00x** at p05 / median / p95;
- Fe reference cost: **15.2917 USD/t NH3**.

### Panel b — activity-only physical reachability

Show the strict `E_N` scaling line independently.

Canonical anchors:
- strict-scaling minimum Ru cost: **21.397873 USD/t**;
- descriptor at minimum: **E_N = -1.215 eV**;
- 673 K scaling headroom: **1.0899x**;
- state-specific maximum headroom: **2.524565x**.

Conclusion: activity alone remains outside reach.

### Panel c — joint direct-activity/lifecycle backward target

Plot:
- x: direct Ru activity multiplier;
- y: recovery required for Fe parity;
- curves: 10, 15, 20 y catalyst lifetime.

At **99% recovery**:
- 10 y: **alpha <= 2.41794x**;
- 15 y: **alpha <= 1.74213x**;
- 20 y: **alpha <= 1.40129x**.

These are conservative economic targets from the 53-state subset. They are **not** reachability results.

### Panel d — strict-scaling × lifecycle reachability

Use the exact 14,136-state closure:
- canonical regression gate: **21.397873 USD/t at E_N=-1.215 eV**;
- critical factor: **q*=(1-r)/L = 4.40683454e-4 y^-1**;
- strict-scaling parity state: **E_N=-1.230 eV; 425 C / 190 bar / 30 C; V=4.298 m3**;
- tested box: **L<=20 y, recovery<=99%**;
- best tested corner: **20 y + 99%**, cost **15.36249 USD/t**, margin **+0.07078 USD/t** versus Fe;
- exact boundary: **99.1186% recovery at 20 y**, or **22.69 y lifetime at 99% recovery**.

Conclusion: the joint target approaches but does not enter the prespecified strict-scaling property box.

## Figure-lock rule

The publication figure may now be rebuilt and frozen from:
- `activity_lifecycle_certified_boundary.csv`
- `activity_lifecycle_target_keypoints.csv`
- `scaling_lifecycle_exact_global_boundary.csv`
- `scaling_lifecycle_exact_keypoints.csv`
- `scaling_lifecycle_exact_summary.json`

Do not reintroduce the earlier interpretation that the 2.524565x state-specific maximum is a uniform activity multiplier.
