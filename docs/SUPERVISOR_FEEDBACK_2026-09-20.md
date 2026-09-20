# Supervisor feedback — 2026-09-20

**Status: ANALYSES COMPLETED 2026-09-20; figure/manuscript integration pending.** The frozen families remain the provenance baseline. Results are stored under `analysis/supervisor_2026_09_20/`; no existing provenance was deleted or overwritten.

## 1. NH3: isolate direct Ru metal-price effects and explain the 6.739 USD/t gap

### Required counterfactual

Run the canonical NH3 model again with **Ru metal price set equal to the Fe metal price**, with every other model input, constraint, costing convention and optimizer unchanged. The process must be reoptimized for Ru under the counterfactual rather than evaluated at the old Ru operating point.

Interpretation is binary at the claim level:

- If Fe still has the lower optimized cost, the inversion survives removal of the direct Ru-vs-Fe metal-price difference. The manuscript can then support the statement that direct metal purchase price is not sufficient to explain the inversion, and that catalyst/process-demand terms are sufficient within the current model.
- If Ru becomes cheaper than Fe, the current mechanism wording must change. In that case the inversion cannot be presented as process-driven independently of the Ru price premium.

Until this run is complete, do **not** use the sentence “not metal price alone” as an established result.

### NH3 cost decomposition

The current canonical costs are Fe = **15.292 USD/t NH3** and Ru = **22.031 USD/t NH3**, so the current gap is **6.739 USD/t NH3**.

Add a Fe-vs-Ru cost decomposition, visually analogous to the component breakdown used for Fig. 7C. Use the cost categories already implemented in the NH3 model; do not invent new accounting categories for the plot. The decomposition must close exactly to the model totals and show which components generate the 6.739 USD/t difference.

Report both:

1. the canonical baseline decomposition; and
2. the Ru-price-equalized counterfactual decomposition after full reoptimization.

## 2. Joint cost-parameter Monte Carlo

The existing uncertainty result is not enough for the new question because the supervisor specifically wants **cost-side uncertainty**.

Jointly vary:

- metal price;
- CAPEX coefficient;
- electricity price;
- catalyst lifetime.

Keep the distributions, bounds, dependence assumptions, random seed and draw count fixed before reading the outcomes. Reoptimize the relevant economic/process decision for each draw when the sampled cost parameters can move the optimum.

Required outputs:

1. **P(Fe economically preferred to Ru)**, reported unambiguously as `P(C_Fe < C_Ru)`;
2. the distribution of **alpha*** under the current canonical definition of alpha*;
3. for the four MeOH candidates, a **candidate-by-rank probability matrix** (rank 1-4 probabilities for each candidate), with Top-1 probability called out explicitly.

### Figure 3 metric reconciliation

The supervisor referred to “Fe only 68% first” in Fig. 3d, while the current active repository reports Fe Top-1 survival = **28.2%**. Treat this as a metric/version reconciliation checkpoint, not as a new result. Identify which quantity/figure version the 68% refers to before changing F3 or writing the new cost-MC interpretation.

## 3. Agent: separate the non-binding failure mode and add an oracle CU baseline

The non-binding strong-tier result should be described with the full decomposition:

- median decision-stable spend = **566 CU**;
- median final spend = **714 CU**;
- median post-decision-stability overrun = **148 CU**;
- canonical narrow-window use under the non-binding allowance = **0/20**.

The important mechanism is not only that the agent continues for 148 CU after the decision is stable. The larger effect is that once budget pressure disappears, it no longer compresses the process search into a narrow window, so the decision itself stabilizes much later. F10b already contains the key observation: non-binding narrow-window rate is zero.

Recommended wording:

> Under a binding budget, the strong policy compresses the decision chain through scoped process windows. When the allowance becomes non-binding, narrow-window allocation disappears (0/20), the median complete-decision stabilization point shifts to 566 CU, and a further median 148 CU is spent before self-stop, yielding 714 CU median final spend.

### Oracle minimum CU

Compute a deterministic **oracle minimum CU**: the shortest admissible tool chain that can produce the frozen complete decision under the existing 11-action interface and the ledger-true cost model.

The oracle is a lower bound, not another LLM policy. It may use knowledge of the ground-truth shortest valid action path to choose actions, but it must obey the same action prerequisites and exact environment charges.

After it is computed, report at least:

- oracle minimum CU;
- strong 75-CU budget / oracle;
- strong median decision-stable spend at 75 CU / oracle;
- fixed-policy threshold 206 CU / oracle;
- non-binding median decision-stable 566 CU / oracle.

This makes “75 vs 206” interpretable relative to the irreducible decision cost rather than only as a pairwise policy comparison.

## Consequences for the current manuscript state

- **NH3 mechanism claim:** reopened until the Ru-price-equalization test is complete.
- **F3 uncertainty story:** reopened for joint cost-parameter MC and the 68% vs 28.2% metric reconciliation.
- **F10 Agent story:** frozen run data remain valid, but the interpretation/caption is reopened to add the 566 + 148 decomposition, the 0/20 non-binding narrow-window mechanism, and the oracle CU reference.
- **Versioning:** keep NH3-FINAL-1.1 and DISCOVER-BOUNDARY-C1 as the current baseline/provenance sources. Do not mint a replacement version until the requested analyses are complete and audited.


## Execution closure — 2026-09-20

All three requested points have now been calculated.

### 1. NH3 Ru-price counterfactual and cost decomposition

- Frozen baseline reproduced: Fe **15.291705 USD/t**, Ru **22.030595 USD/t**.
- Set Ru metal price to Fe = **8 USD/kg**, keep all other inputs unchanged, and reoptimize over all **14,136 states**.
- Equal-price Ru = **14.712130 USD/t** at **425 C / 170 bar / 30 C**.
- Ru - Fe = **-0.579575 USD/t**: the economic order flips to Ru < Fe.
- Therefore direct Ru-vs-Fe metal-price disparity is necessary for the baseline Fe-over-Ru inversion in the current model. The response is process-mediated because Ru also shifts from 450 C / 425 bar to 425 C / 170 bar.

The canonical **6.738890 USD/t** Ru-Fe gap is decomposed as: fresh-feed compression **+4.631668**, metal inventory **+1.763013**, compressor CAPEX **+1.180730**, refrigeration **+0.629119**, vessel pressure **-0.733129**, recycle compression **-0.646840**, reactor base **-0.085671 USD/t**.

### 2. F3 reconciliation and joint cost MC

- The teacher's **68%** is **P(Fe is the economic winner) = 681/1000 = 68.1%** in the frozen descriptor MC.
- The repository's **28.2%** is `top1_survival`, i.e. P(atomic Top-1 = economic Top-1). The values do not conflict.
- Preregistered joint cost MC: **5,000 draws, seed 20260920**.
- Full 14,136-state direct-cost verification: **P(C_Fe < C_Ru) = 5000/5000 = 1.000**; minimum observed Ru-Fe margin **2.382 USD/t**.
- alpha*: **p05 70.78x, median 174.27x, p95 462.00x**; no draw has Ru <= Fe at alpha = 1.
- MeOH four-candidate rank matrix: canonical D01 order is retained in **5000/5000** draws. A separately labelled active-Re replacement extension also retains the same order in **5000/5000** draws.

### 3. Agent oracle CU

Two lower bounds are retained so the result cannot be improved merely by exploiting scorer incompleteness:

- **7 CU**: literal scorer-complete floor (winner + decision pair + reachability).
- **22 CU**: protocol-complete S1-S3 minimum, including all-candidate activity screening and no unresolved candidate. This is the manuscript-facing oracle.

Relative to **22 CU**: strong 75-CU allowance = **3.41x**, median decision-stable spend at the 75-CU cell (52.5 CU) = **2.39x**, fixed-policy threshold 206 CU = **9.36x**, non-binding median decision-stable 566 CU = **25.73x**.

Machine-readable outputs and figures: `analysis/supervisor_2026_09_20/README.md`.

### Manuscript consequence

The previous phrase **“not metal price alone” should not be retained**. The supported statement is that the Fe-Ru inversion is generated by **metal cost coupled to process reoptimization**: price equalization reverses the order, whereas bounded joint cost uncertainty around the canonical regime leaves Fe lower-cost in all 5,000 draws.
