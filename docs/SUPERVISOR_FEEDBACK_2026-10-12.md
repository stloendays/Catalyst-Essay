# Supervisor feedback — 2026-10-12

**Status: IN PROGRESS.** The analyses run on separate branches; the manuscript, figures and frozen results (`freeze/field-2026-10-12`) are unchanged until these items close.
- Fallback point before the industrial-parameter qualifiers: tag `fallback/pre-industrial-params-2026-10-12` (272664d).

The supervisor answered three questions:
- Which methanol loop should be the primary?
- Should the KAAP comparison become a staged Fe/Ru converter?
- Should the new "the laboratory metric that matches the plant depends on the loop" analysis be added?

## 1. Methanol: the inert-limited loop becomes the primary

**Decision.** The primary methanol loop limits the reactor-inlet non-H₂/CO₂ fraction (S6-type). The stated reason must be physical, not rhetorical:
- real loops limit inert accumulation;
- the model fixes the per-pass conversion at the laboratory value, so a loop without an inert limit implicitly assumes that diluting the feed does not slow the reaction.

**Requirements**

1. Report both treatments, e.g. "38–70% depending on how the loop handles inerts", each with its count of disagreements above 5% regret (7 at S5, 22 at 6.86%). Never report the upper value alone.
2. 6.86% is one plant's value (Campos et al. 2022). Scan 5–15% and report whether the result is stable.
3. State which species the limit counts.
   - In `data/meoh/meoh_general_model.py` (`loop_balance`), the limited fraction is (CH₄ + CO + N₂) / reactor inlet. The published 6.86% counts the same species (CO 1.5%, N₂ 4.9%).
   - CO still reacts in every pass, bounded by RWGS and CO-hydrogenation equilibrium; it only counts toward the cap.
   - Report the alternative that limits true inerts only (N₂ + CH₄), so the treatment of CO cannot contradict the CO recycle.
4. Explain the group count. 83 groups = all entries including plot readings (909 entries, 44 papers; kept as a sensitivity: 35/83 at S5, 54/82 at 6.86%). 40 groups = printed values only (310 entries, 28 papers), under the 2026-10-08 rule. The grouping rule is identical; groups with fewer than two printed entries drop out. Give the per-group ledger in the SI.

**Work**

| Item | Where | Status |
|---|---|---|
| Disagreement vs inlet limit (4–30%, S5, S6), paper-cluster bootstrap, near-infeasibility split, pre-registered laboratory-rule test | draft PR #69 | done, CI passing, under independent verification |
| S6 with conversion raised by catalyst inventory (23/40; 16 above 5% from 12 papers) | draft PR #67 | done, under verification; rerun if the true-inert definition is adopted |
| True-inert (N₂ + CH₄) limit definition, 5–15% stability for both definitions, 83 → 40 ledger | branch `analysis/meoh-inlet-definition-2026-10-12` (cloud run) | running |

## 2. Ammonia Fe–Ru: replace the frontier pair's kinetics before any staged converter

**Decision.** Do not build the staged (hybrid) converter yet.
- The descriptor microkinetics give Ru the wrong apparent orders (H₂ +2.5, NH₃ −2.0; PR #64).
- Measured Ru is inhibited by H₂, which is why industry uses it at low pressure and downstream.
- The model's Ru has no such inhibition and runs to 425 bar.
- With reversed kinetics a staged converter can only give a wrong answer.

**Requirements**

1. Replace the kinetics of the Fe–Ru pair only with literature rate laws that carry H₂ inhibition: promoted Ru/C (e.g. Rossetti et al., Ind. Eng. Chem. Res. 2006, 45, 4150) and a measured fused-Fe rate law.
2. Rerun the full plant optimization and report:
   - whether Ru's optimal pressure falls from 425 bar to about 100–200 bar;
   - whether the parity condition and the 201-fold activity multiple change.
3. This matches the paper's logic: high-fidelity models are spent only on the two candidates at the decision frontier.
4. Add the staged converter only if the new kinetics make its benefit appear.

**Work.** Branch `analysis/nh3-staged-converter-2026-10-12`, redirected to the kinetics swap first. Running.

## 3. Ru inventory financing: report both accounting conventions

Report both conventions wherever the KAAP comparison appears:
- not charging the Ru inventory for financing gives parity;
- financing it at the 12% equipment rate makes Ru about 2.6 US dollars per tonne more expensive (21.79 vs 19.14).

Documented industrial catalyst-metal lease rates (draft PR #70) can be given as a supplementary reference:
- refinery Pt/Pd catalyst leases run 1.35–5.10% per year;
- at those rates Ru stays 0.19–1.48 US dollars per tonne above Fe in that loop.

## 4. Framework: three tiers in Fig. 1a

**Decision.** Organize the paper around three tiers: the atomic optimum, the laboratory optimum and the industrial optimum. Show them in Fig. 1a, and mark the segment each case measures:

| Case | Segment measured |
|---|---|
| Ammonia | atomic → industrial |
| CO₂-to-methanol | published laboratory → industrial |
| Au/TiO₂ | laboratory → catalyst requirement |

The three cases use three approaches that together cover the chain.

**Work.** Branch `figure/fig1a-three-tier-2026-10-12`: redesign, render and two independent reviews. Running.

## 5. Author decision (same day)

The Adaptive Catalyst Screening Agent goes to Methods and Discussion. It is not a central scientific question; this follows the review of PR #65.

## Writing rules for the revision

- Write "locate and explain the decision boundary", not "predict it". The pre-registered leverage test (draft PR #71) is mixed: property-driven inversions are anticipated by a first-order cost attribution; constraint-driven inversions appear only after re-optimization.
- Quote counts, not maxima, for the inlet-limited loop; some regrets there reflect near-infeasibility.
