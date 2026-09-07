# Figure map — canonical manuscript snapshot

Snapshot date: **2026-09-07**  
Scientific basis: **NH3-FINAL-1.1** for ammonia headline values.

This page preserves the original nine-figure logic but updates the ammonia values to the current canonical model. The purpose of each figure is a scientific claim, not simply a visualization of available data.

## Figure 1 — NH3 atomic vs economic ranking

**Question:** Does an atomic activity ranking survive industrial economic propagation?

**Content**
- 15-metal intrinsic activity ranking versus optimized catalyst-dependent economic ranking.
- Highlight Ru, Os and Fe.

**Canonical headline**
- Atomic top-3: **Ru > Os > Fe**.
- Economic top-3: **Fe > Ru > Os**.
- Fe / Ru / Os reduced catalyst-dependent costs: **15.292 / 22.031 / 25.832 USD/t NH3**.

**Claim supported:** the candidate ordering can invert after multiscale propagation even when the full candidate set remains globally correlated.

---

## Figure 2 — Rolling Top-K rank correlation

**Question:** Why can a globally high rank correlation still produce the wrong decision among the candidates that matter?

**Content**
- Spearman rho as a function of the number K of highest-activity candidates retained.
- Optionally pair with Kendall tau at the decision frontier.

**Canonical headline**
- Top-3 Spearman rho = **-0.50**.
- Top-3 Kendall tau = **-0.33**.
- Full 15-metal raw Spearman rho = **0.929**.

**Claim supported:** the inversion is concentrated at the **decision frontier**, not distributed uniformly across the full screen.

---

## Figure 3 — NH3 uncertainty and decision stability

**Question:** How does descriptor uncertainty propagate into engineering feasibility and ranking stability?

**Content**
- 1,000-draw Monte Carlo propagation.
- Fe feasibility under the 90 m3 bed-volume criterion.
- Top-1 survival and Top-3 actionable probability.

**Canonical headline**
- Fe feasibility = **79.9%**.
- Fe Top-1 survival = **28.2%**.
- Fe Top-3 actionable = **94.0%**.

**Interpretation:** the uncertainty is dominated by the strong-binding tail of the descriptor distribution; it should not be read as a probability that Fe is intrinsically “industrially unusable.”

---

## Figure 4 — Fe / Ru / Os operating envelopes

**Question:** After pressure-dependent equipment CAPEX is included, where do the catalysts actually prefer to operate?

**Content**
- Pressure-dependent cost envelope.
- Re-optimize reactor temperature and separator temperature at each pressure.
- Show the broadness of the optimum rather than only the argmin.

**Canonical headline**
- Fe optimum: approximately **425 C / 180 bar / 30 C**.
- Ru optimum: approximately **450 C / 425 bar / 25 C** and is now an interior point.
- Os: **broad shallow high-pressure minimum**; do not over-interpret a single point value.

**Claim supported:** process reoptimization and pressure CAPEX change the preferred operating regime without removing the ranking inversion.

---

## Figure 5 — Ru backward-design activity sweep

**Question:** How much activity improvement would Ru need to reach Fe cost parity after full process reoptimization?

**Content**
- Ru activity multiplier on the x-axis.
- Reoptimized Ru cost on the y-axis.
- Fe parity line and the crossing point.

**Canonical headline**
- Activity-only break-even target = **201.22x** (write approximately **201-fold** in prose).
- Break-even operating point: approximately **425 C / 190 bar / 30 C**.

**Claim supported:** economic parity can be translated into a quantitative catalyst-property target.

---

## Figure 6 — Scaling-manifold reachability

**Question:** Is the 201-fold Ru activity target physically reachable along the current scaling-consistent design path?

**Content**
- Descriptor/scaling manifold mapped to achievable activity.
- Compare reachable activity headroom with the backward-design target.
- Show the strict-scaling Ru minimum cost relative to Fe.

**Canonical headline**
- Activity headroom at 673 K: **1.090x**.
- Maximum headroom over the process-state library: **2.525x**.
- Strict-scaling lowest Ru cost: **21.398 USD/t NH3** at **E_N = -1.215 eV**.
- Activity-only route: **unreachable** under the frozen model.

**Claim supported:** backward design distinguishes an economically useful target from a target that the current catalyst-property manifold cannot supply.

---

## Figure 7 — CO2-to-MeOH recycle / separation economics

**Question:** How do catalyst properties enter the recycle and separation layers rather than only changing intrinsic reaction rate?

**Content**
- Fresh H2 / CO2 demand.
- Recycle flow and purge.
- Product separation and compression burden.
- Cost response across catalyst states.

**Claim supported:** catalyst changes can alter the process architecture and downstream cost pools.

---

## Figure 8 — Methane accumulation, purge and economic leverage

**Question:** Which catalyst property controls the economically important pathway in the methanol loop?

**Content**
- CH4 formation / suppression versus accumulation and purge burden.
- Compare local leverage with STY and single-pass conversion.

**Canonical benchmark**
- STY leverage = **0.00289**.
- Single-pass conversion leverage = **0.05883**.
- CH4-suppression leverage = **0.37579**.

**Claim supported:** in the current methanol regime, selectivity-driven methane suppression has much stronger economic leverage than production-rate improvement alone.

---

## Figure 9 — Cross-reaction catalyst-economic leverage

**Question:** Is there one universal catalyst property that controls economic ranking across reactions?

**Content**
- Put NH3 TOF and MeOH STY / conversion / CH4 suppression on a common cost-denominator basis.
- Compare normalized leverage magnitudes and the pathways they activate.

**Canonical headline**
- MeOH CH4-suppression / NH3 TOF normalized leverage ratio = **273–410**.
- Midpoint = approximately **328**.

**Claim supported:** economic leverage is **reaction- and process-pathway dependent**.

---

## Rank-preservation control figure — Au/TiO2 CO oxidation V1.1

**Question:** Does the multiscale implementation preserve an upstream ranking when the downstream mapping is fixed and physically monotonic?

**Content**
- Mirror rank-flow figure for the 2–6 nm Au/TiO2 particle-size series.
- Left: literature-calibrated intrinsic mass-activity order.
- Right: required catalyst / catalyst-burden order at the same fixed reaction condition.
- Straight rank-flow lines rather than the crossing lines expected for an inversion figure.

**Headline**
- Activity order: **2 > 3 > 4 > 5 > 6 nm**.
- Downstream burden order: **2 > 3 > 4 > 5 > 6 nm**.
- Spearman rho = **1.000**.
- Kendall tau = **1.000**.
- Pairwise inversions = **0**.
- 10,000/10,000 predefined literature-envelope draws preserve the full order.
- Literature calibration contracts the 6 nm / 2 nm required-mass ratio from **19.42x to 8.064x (-58.5%)** without changing the ranking.

**Claim supported:** the framework does not intrinsically destroy catalyst rankings; a rank can remain intact when the catalyst-to-process mapping is monotonic and does not activate a competing downstream penalty.

Current vector asset: [`../figures/rank_preservation_control/RP1_AuTiO2_rank_preservation_V1_1.svg`](../figures/rank_preservation_control/RP1_AuTiO2_rank_preservation_V1_1.svg).

---

## Working main-text allocation

A compact main narrative can be built around **F1, F2, F5, F6, F8 and F9**. Figures **F3, F4 and F7** are strong candidates for Extended Data / Supporting Information unless the uncertainty and process-reoptimization story is given more main-text space.

The Au/TiO2 rank-preservation control is currently best treated as a **compact companion to F1 or an Extended Data control**, rather than forcing a tenth full main-text figure.

This allocation is a working editorial recommendation, not a frozen scientific result.

## Version note

Older values such as Fe/Ru/Os = 10.199/17.592/21.321 USD/t, Fe feasibility = 73.6%, full-15 rho = 0.911 and Ru break-even = 2171.56x belong to **NH3-FINAL-1.0** and should not be used as current headline values.
