# Figure 3 joint-region panel specification — 2026-09-29

Status: **READY FOR NEXT COMPOSITE REDRAW**. This note does not claim that the current Fig3.svg/pdf/png already contains the panel.

## Scientific message

Keep the existing activity-only panels unchanged, then add one compact panel showing that the backward-design answer becomes a **property region** once activity, lifetime and Ru recovery are allowed to move together.

## Plot

- x axis: Ru activity multiplier alpha, 1.0 to 2.524565.
- y axis: minimum Ru recovery required for Fe cost parity, 97–100%.
- curves: catalyst lifetime 10 y, 15 y, 20 y.
- vertical references:
  - 1.089901x = scaling-consistent gain at 673 K;
  - 2.524565x = maximum scaling-consistent gain over frozen process states.
- horizontal references: 98% and 99% recovery.
- highlighted certified point:
  - alpha = 2.524565x
  - life = 20 y
  - recovery = 98%
  - effective Ru price = 538.525 USD/kg
  - process state = 425 C / 185 bar / 30 C
  - Ru cost = 15.2571 USD/t NH3
  - Fe cost = 15.2917 USD/t NH3
  - margin = -0.0346 USD/t

## Evidence logic

The panel uses the certified inner-region calculation in:
- `analysis/fe_bridge_backward_2026_09_29/build_certified_inner_surface.py`
- `analysis/fe_bridge_backward_2026_09_29/activity_lifecycle_certified_boundary.csv`
- `analysis/fe_bridge_backward_2026_09_29/activity_lifecycle_certified_keypoint.json`

The calculation reuses the 53 distinct process states already present in the fully reoptimized Ru price sweep. For each state, bed volume scales as V/alpha and the FINAL-1.1 reactor/vessel terms are recomputed exactly. Because only a subset of the full 14,136 states is searched, the resulting feasible region is conservative: a point declared feasible is guaranteed feasible under the full model.

## Caption sentence

"Combining catalyst properties changes the reachability conclusion: although activity alone requires 201.22x, the certified inner region reaches Fe parity at the edge of the existing design envelope; 2.524565x activity with 20 y lifetime and 98% Ru recovery gives 15.257 USD t^-1 NH3 at an existing 425 C / 185 bar / 30 C process state."

## Full-state confirmation

`run_exact_joint_surface.py` is ready for the original frozen harness machine. It reuses the cached response surface and performs no DFT. Its purpose is to expand the conservative inner region to the exact 14,136-state parity boundary before final figure lock.
