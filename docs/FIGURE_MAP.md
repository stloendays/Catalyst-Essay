# Figure map — canonical manuscript snapshot

Snapshot date: **2026-09-07**  
Scientific basis: **NH3-FINAL-1.1** for ammonia headline values.

This page preserves a compact **nine-figure** main-text architecture. The Au/TiO2 rank-preservation control is integrated into **Figure 9B** as the counterpoint to the ammonia and methanol inversion cases rather than added as a tenth standalone figure.

The purpose of each figure is a scientific claim, not simply a visualization of available data.

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

## Figure 7 — CO2-to-MeOH catalyst-state ranking inversion and recycle economics

**Question:** Can an intrinsic catalyst-state ranking be reshaped after explicit recycle/separation economics, and where does the reversal occur?

**Content**
- Rebuilt upstream-to-economic rank-flow panel from `MeOH_F03_UpstreamToEconomicRanking_D01v3.png`.
- Four Re/TiO2 catalyst–temperature states at the D01 v3 literature points.
- Left: upstream **STY per g Re** ranking.
- Right: **NPC at 2% purge** ranking.
- Pair with the archived explicit-loop / cost-across-state view if space permits.

**Canonical headline**
- Upstream per-Re order: **1% Re 250 C > 1% Re 200 C > 5% Re 200 C > 5% Re 250 C**.
- Economic order: **5% Re 200 C > 1% Re 200 C > 1% Re 250 C > 5% Re 250 C**.
- NPC: **943 / 967 / 975 / 1258 EUR/t** in economic-rank order.
- Spearman rho = **0.20**.
- Kendall tau = **0.00**.
- Pairwise inversions = **3 of 6**.
- Upstream per-Re winner **1% Re / 250 C** falls to economic rank **#3**.

**Writing boundary**
- These are **catalyst–temperature states**, not four independently reoptimized catalyst identities.
- The top-rank reversal is specific to the **Re-normalized intrinsic metric**. Using yield or STY per g catalyst preserves the same rho/tau and 3/6 pairwise inversion count but the upstream winner then coincides with the economic winner.
- Re purchase price is excluded from the NPC by design.

**Claim supported:** explicit downstream propagation can reshape a methanol catalyst-state ranking, and the decision-frontier reversal depends jointly on the upstream screening metric and selectivity-sensitive recycle economics.

Current asset: [`../figures/meoh/MeOH_F03_UpstreamToEconomicRanking_D01v3.png`](../figures/meoh/MeOH_F03_UpstreamToEconomicRanking_D01v3.png).

---

## Figure 8 — Methane accumulation, purge and economic leverage

**Question:** Which catalyst property controls the economically important pathway behind the methanol ranking reshuffle?

**Content**
- CH4 formation / suppression versus accumulation and purge burden.
- Compare local leverage with STY and single-pass conversion.
- Use the 5 wt% Re / 250 C state to show that the highest conversion can still coincide with the highest NPC when methane selectivity is poor.

**Canonical benchmark**
- STY leverage = **0.00289**.
- Single-pass conversion leverage = **0.05883**.
- CH4-suppression leverage = **0.37579**.
- 5 wt% Re / 250 C: **X_CO2 = 0.40**, **S_CH4 = 0.25**, **NPC = 1258 EUR/t**.

**Claim supported:** in the current methanol regime, selectivity-driven methane suppression has much stronger economic leverage than production-rate improvement alone and provides the mechanistic pathway for the observed rank reshuffling.

---

## Figure 9 — When catalyst rankings invert and when they survive

**Question:** Is ranking inversion an inevitable consequence of multiscale propagation, or does it depend on the topology of catalyst-to-process coupling and on the upstream screening objective?

### Figure 9A — Cross-reaction catalyst-economic leverage

**Content**
- Put NH3 TOF and MeOH STY / conversion / CH4 suppression on a common cost-denominator basis.
- Compare normalized leverage magnitudes and the downstream pathways they activate.

**Canonical headline**
- MeOH CH4-suppression / NH3 TOF normalized leverage ratio = **273–410**.
- Midpoint = approximately **328**.

**Claim supported:** economic leverage is **reaction- and process-pathway dependent**.

### Figure 9B — Au/TiO2 rank-preservation control

**Content**
- Reuse / adapt the existing mirror rank-flow figure `RP1_AuTiO2_rank_preservation_V1_1.svg`.
- Left: literature-calibrated intrinsic mass-activity ranking across **2, 3, 4, 5 and 6 nm** Au particles.
- Right: required catalyst-burden ranking at the common fixed process condition.
- Show the same candidate order on both sides and annotate the fixed-condition / monotonic-mapping nature of the control.

**Canonical headline**
- Activity rank = burden rank = **2 > 3 > 4 > 5 > 6 nm**.
- Spearman rho = **1.000**.
- Kendall tau = **1.000**.
- Pairwise inversions = **0**.
- Full ranking preserved in **10,000 / 10,000** predefined literature-envelope draws.
- Literature-calibrated 6 nm / 2 nm required-catalyst ratio = **8.064x**.

**Writing boundary**
- This is a **rank-preservation control**, not a full industrial TEA.
- Do not assign unsupported absolute process economics to the Au/TiO2 system.
- Its scientific role is to show that the implementation does not manufacture inversion when the downstream mapping is monotonic.

**Combined Figure 9 claim:** multiscale propagation does not have one universal effect on catalyst rankings. NH3 shows a decision-frontier inversion after candidate-specific process/economic reoptimization; MeOH shows a catalyst-state ranking reshuffle through a selectivity–recycle pathway whose top-rank reversal depends on Re-normalized intrinsic screening; Au/TiO2 preserves the full ranking under a monotonic fixed-condition mapping.

Current control asset: [`../figures/rank_preservation_control/RP1_AuTiO2_rank_preservation_V1_1.svg`](../figures/rank_preservation_control/RP1_AuTiO2_rank_preservation_V1_1.svg).

---

## Working main-text allocation

The restored MeOH before/after ranking evidence makes **F7** a main-text result rather than a supporting-only process figure. A compact main narrative can now be built around **F1, F2, F5, F6, F7, F8 and F9**. Figures **F3 and F4** remain the strongest candidates for Extended Data / Supporting Information if the main-text figure count must be reduced.

Within F9, the preferred structure remains:

```text
F9A  pathway-specific economic leverage across NH3 and MeOH
F9B  Au/TiO2 rank-preservation counterexample
```

The manuscript closes with a three-regime distinction:

```text
NH3: candidate-specific process/economic coupling -> decision-frontier inversion
MeOH: intrinsic per-Re ranking + selectivity/recycle coupling -> catalyst-state reshuffle / top-rank inversion
Au/TiO2: monotonic fixed-condition mapping -> ranking preserved
```

This allocation is a working editorial recommendation, not a frozen scientific result.

## Version note

Older values such as Fe/Ru/Os = 10.199/17.592/21.321 USD/t, Fe feasibility = 73.6%, full-15 rho = 0.911 and Ru break-even = 2171.56x belong to **NH3-FINAL-1.0** and should not be used as current headline values.
