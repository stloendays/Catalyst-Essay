# Figure 3 joint backward-design panel specification — 2026-09-29

Status: **TARGET REGION + STRICT-SCALING REACHABILITY CLOSED; COMPOSITE REBUILD PENDING**.

The current committed `Fig3.svg/pdf/png` is still the five-panel pre-extension figure. This specification defines the next publication-facing rebuild and must not be read as a claim that the raster has already been replaced.

## Scientific message

Figure 3 should now make the backward-design logic explicit as two separate operations:

```
economic target inversion
        ->
required catalyst-property region
        ->
strict scaling-manifold reachability
```

The activity-only result remains important, but the new result is that joint lifecycle improvement moves the target close to the strict scaling manifold without quite entering the prespecified property box.

## Panel a — activity-only backward target

Keep the established result:

- canonical direct Ru activity multiplier for Fe parity: **201.22x**;
- cost-MC p05 / median / p95: **70.78x / 174.27x / 462.00x**.

This remains the single-property reference.

## Panel b — activity-only physical reachability

Keep the strict-scaling reference:

- 673 K scaling gain: **1.090x**;
- largest state-specific scaling gain in the frozen process library: **2.525x**;
- strict-scaling minimum Ru cost: **21.397873 USD/t NH3 at E_N = -1.215 eV**.

The **2.525x** quantity is explicitly labelled a **state-specific maximum**, not a uniform activity multiplier.

## Panel c — joint direct-activity / lifetime / recovery target region

Plot:

- x axis: direct Ru activity multiplier, alpha;
- y axis: Ru recovery required for Fe parity;
- curves: catalyst lifetime 10 y, 15 y and 20 y.

Highlight the conservative 53-state target upper bounds:

- **10 y + 99% recovery -> alpha_req <= 2.41794x**;
- **15 y + 99% -> <= 1.74213x**;
- **20 y + 99% -> <= 1.40129x**;
- **20 y + 98% -> <= 2.41794x**.

Use the wording **required direct activity target**, not reachable activity.

## Panel d — exact strict-scaling x lifecycle reachability

This panel is now closed using all **14,136** FINAL-1.1 process states and the canonical **0.005-eV E_N grid**, without new DFT.

Primary quantity:

```
q = (1 - recovery) / catalyst_lifetime
q* = 4.40683454e-4 y^-1
```

Exact boundary and nearest tested point:

- equivalent 10-y effective Ru price at parity: **237.319 USD/kg**;
- parity descriptor/state: **E_N = -1.230 eV**, **425 C / 190 bar / 30 C**, **4.298 m3** bed;
- prespecified box: **life <= 20 y; recovery <= 99%**;
- closest tested corner: **20 y + 99% recovery**;
- strict-scaling cost there: **15.36249 USD/t NH3**;
- miss versus Fe: **+0.07078 USD/t (+0.46%)**;
- parity at 20 y requires **99.1186% recovery**;
- equivalently, 99% recovery requires **22.69 y lifetime**.

Recommended plot:

- x axis: catalyst lifetime (y);
- y axis: Ru recovery required for Fe parity (%);
- solid line: exact strict-scaling parity boundary;
- dashed reference lines: 20 y and 99% recovery;
- mark the tested-box corner (20 y, 99%) and the boundary point (20 y, 99.1186%).

The scientific conclusion is: **the tested lifecycle box does not intersect the strict scaling manifold, but misses it only narrowly.**

## Evidence

Direct target:
- `analysis/fe_bridge_backward_2026_09_29/activity_lifecycle_target_keypoints.csv`
- `analysis/fe_bridge_backward_2026_09_29/build_certified_inner_surface.py`

Strict reachability:
- `analysis/fe_bridge_backward_2026_09_29/scaling_lifecycle_exact_summary.json`
- `analysis/fe_bridge_backward_2026_09_29/scaling_lifecycle_exact_keypoints.csv`
- `analysis/fe_bridge_backward_2026_09_29/scaling_lifecycle_exact_global_boundary.csv`
- `analysis/fe_bridge_backward_2026_09_29/run_statewise_strict_scaling_lifecycle.py`

## Proposed caption wording

**c,** Joint backward design reduces the economic activity target when lifecycle properties improve. At 99% Ru recovery, the conservative upper bound on the direct activity multiplier required for Fe parity falls from 2.418x at 10 y catalyst life to 1.742x at 15 y and 1.401x at 20 y.

**d,** Exact strict-scaling × lifecycle reachability over all 14,136 process states. The tested box (life <= 20 y, Ru recovery <= 99%) remains outside parity: its closest corner, 20 y and 99% recovery, gives 15.362 US dollars per tonne, 0.071 above Fe. The parity boundary lies just outside the box at 99.1186% recovery for a 20-y lifetime, or 22.69 y lifetime at 99% recovery.

## Figure-lock rule

The new scientific result is promoted and CI-gated. The remaining task is **render production**: rebuild `Fig3.svg/pdf/png` from Panels a-d and only then update the publication caption to describe those exact rendered panels.
