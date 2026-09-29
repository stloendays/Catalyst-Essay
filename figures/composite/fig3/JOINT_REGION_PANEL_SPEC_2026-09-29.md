# Figure 3 joint backward-target panel specification — 2026-09-29

Status: **TARGET PANEL READY; STRICT-SCALING REACHABILITY PANEL PENDING**. This note does not claim that the current `Fig3.svg/pdf/png` already contains either panel.

## Scientific message

Keep the existing activity-only backward and scaling panels unchanged. Add a compact panel that shows how allowing catalyst lifetime and Ru recovery to improve changes the **economic target region**. Keep physical reachability as a separate panel/question.

## Panel c — direct-activity/lifecycle backward target

Plot:

- x axis: direct Ru activity multiplier, alpha;
- y axis: Ru recovery required for Fe parity;
- curves: catalyst lifetime 10 y, 15 y and 20 y;
- highlight the 99% recovery targets:
  - 10 y: alpha <= **2.41794x**
  - 15 y: alpha <= **1.74213x**
  - 20 y: alpha <= **1.40129x**
- additional point: 20 y + 98% recovery -> alpha <= **2.41794x**.

Use the wording **"required direct activity target"**, not "reachable activity". The 53-state calculation is conservative because it searches only process states already visited in the fully reoptimized Ru price sweep; full 14,136-state reoptimization can only reduce the activity multiplier required for parity.

### Reference lines

The existing **1.0899x at 673 K** and **2.524565x maximum over all process states** may be shown only as reference markers. The latter is explicitly labelled **state-specific maximum**, not a uniform activity multiplier.

## Panel d — strict-scaling x lifecycle reachability

Do not infer this panel from Panel c. It must come from the exact cached-response calculation:

- script: `analysis/fe_bridge_backward_2026_09_29/run_exact_scaling_lifecycle_surface.py`;
- no new DFT;
- reuse the frozen 14,136-state response cache;
- vary Ru `E_N` on the strict-scaling grid;
- propagate `P_eff = P_Ru (1-r) (10 y/L)`;
- reoptimize the full process for every point;
- baseline regression gate: recover **21.397873 USD/t at E_N = -1.215 eV** under canonical Ru economics.

Until that exact run is completed, label Panel d **PENDING** and do not state that the tested lifecycle region intersects the strict scaling manifold.

## Evidence

Direct target panel:
- `analysis/fe_bridge_backward_2026_09_29/build_certified_inner_surface.py`
- `analysis/fe_bridge_backward_2026_09_29/activity_lifecycle_target_keypoints.csv`
- `analysis/fe_bridge_backward_2026_09_29/activity_lifecycle_certified_boundary.csv`

Strict reachability panel:
- `analysis/fe_bridge_backward_2026_09_29/run_exact_scaling_lifecycle_surface.py`
- output files are intentionally absent until the frozen-harness run passes its baseline gate

## Caption wording for Panel c

"Joint backward design reduces the economic activity target when lifecycle properties improve. At 99% Ru recovery, the conservative upper bound on the direct activity multiplier required for Fe parity falls from 2.418x at 10 y catalyst life to 1.742x at 15 y and 1.401x at 20 y. These values define the required property region; strict scaling-manifold reachability is evaluated separately."

## Figure-lock rule

Do not rebuild/freeze the publication Fig. 3 with a joint-reachability conclusion until the exact strict-scaling x lifecycle cached-response run has completed successfully.
