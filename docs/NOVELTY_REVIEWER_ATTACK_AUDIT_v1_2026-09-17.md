# Reviewer-attack novelty audit v1 — 2026-09-17

Purpose: stress-test the three manuscript contributions against the closest prior art before stronger novelty language is used in the main text. This is a literature-positioning audit, not a change to any scientific result.

## Executive conclusion

The manuscript retains a defensible contribution, but broad priority claims should be avoided. Three adjacent ideas are already established in the literature: catalyst rankings can depend on reactor/test context; catalyst descriptors can be optimized jointly with reaction/process models; and scientific experimentation or simulation can be allocated adaptively under resource constraints. The manuscript is strongest when it claims a specific integration of these ideas around an **industrial catalyst decision** rather than claiming to originate any one of them.

The safest high-level contribution is:

> We quantify whether an atomistic candidate ranking remains decision-faithful after candidate-specific process and economic propagation, translate any resulting industrial gap into a catalyst-property target and test its physical reachability, and then evaluate whether a tool-using agent can recover that same decision under a finite scientific-compute budget.

This wording leaves the prior art intact while preserving the manuscript's actual scope.

---

## Contribution 1 — Decision-frontier ranking fidelity

### Reviewer attack

> "Catalyst rankings changing with reactor conditions is not new. FCC testing literature already showed that different laboratory reactors can give erroneous or context-dependent catalyst rankings. Ammonia catalyst descriptors have also been connected to reactor conditions for decades."

### Closest prior art

**Wallenstein, Haas & Harding, Applied Catalysis A 203, 23–36 (2000), DOI 10.1016/S0926-860X(00)00467-1.** The paper explicitly reports that small-scale FCC test configurations can yield erroneous catalyst rankings relative to more representative reactor tests.

**Jacobsen et al., Journal of Catalysis 205, 382–387 (2002), DOI 10.1006/jcat.2001.3442.** The "optimal catalyst curves" work connected first-principles ammonia descriptors with temperature, pressure, synthesis-gas composition, reactor design and catalyst selection, showing that the optimum nitrogen-binding energy depends on reaction conditions.

**Rangarajan, Maravelias & Mavrikakis, J. Phys. Chem. C 121, 25847–25863 (2017), DOI 10.1021/acs.jpcc.7b08089.** This work formulated mechanistic modelling and catalyst design as constrained optimization problems and explicitly treated heterogeneous-catalyst design within a microkinetic framework.

**Wang & Hu, Phil. Trans. R. Soc. A 374, 20150078 (2016), DOI 10.1098/rsta.2015.0078.** This paper framed rational catalyst design as an optimization problem.

### What therefore cannot be claimed

- Do not claim that this is the first demonstration that catalyst ranking can depend on reactor or process conditions.
- Do not claim that this is the first connection between DFT-scale catalyst properties and reactor/process design.
- Do not claim that candidate-specific operating-condition optimization is itself novel.

### What remains distinctive and supported

The present work asks a narrower comparative question: whether a **discrete atomistic candidate ranking** survives an end-to-end catalyst-to-process-to-economic mapping when each candidate is allowed its own process optimum. It then evaluates **frontier-local rank fidelity** separately from full-set correlation. In NH3, the key result is not merely that operating conditions affect catalyst performance, but that a globally correlated 15-metal screen can still select a different winner at the industrial decision frontier.

The cross-reaction structure strengthens this point. NH3 and MeOH exhibit ranking changes through different downstream coupling pathways, while the Au/TiO2 control shows preservation under a common monotonic mapping. The supported conceptual object is therefore **candidate-to-process coupling topology**, not "multiscale complexity" in general.

### Safe manuscript formulation

> Previous work established that catalyst optima and even laboratory catalyst rankings can depend on reaction and reactor context. Here we quantify a different failure mode: an atomistic ranking can remain globally informative yet lose fidelity among the candidates that define the industrial economic decision.

---

## Contribution 2 — Economic backward target plus physical reachability

### Reviewer attack

> "Inverse catalyst design and integrated molecular/process design already exist. Translating a process objective into a molecular or catalyst target is established."

### Closest prior art

**Bardow, Steur & Gross, Ind. Eng. Chem. Res. 49, 2834–2840 (2010), DOI 10.1021/ie901281w.** Continuous-molecular targeting optimizes idealized molecular parameters together with process variables and then maps the resulting target back to real molecules.

**Rangarajan et al. (2017)** and **Wang & Hu (2016)** optimize catalyst descriptors/properties inside mechanistic catalyst-design formulations.

More recent inverse-design work, including generative catalyst design, further establishes that "inverse design" alone is not a novelty claim that should be used here.

### What therefore cannot be claimed

- Do not call backward design itself unprecedented.
- Do not claim to be the first framework to invert a process objective into a molecular/material target.
- Do not claim that optimizing a descriptor subject to kinetic constraints is new.

### What remains distinctive and supported

The manuscript defines the backward target by an explicit **industrial parity condition between discrete catalyst candidates**, with full downstream reoptimization at each imposed catalyst-property multiplier. It then subjects that economically required target to a separate **scaling-consistent reachability test**. The scientific result is the gap between what economics demands and what the current catalyst-property manifold can supply.

For the NH3 case, the paper therefore supports a precise statement: approximately 201-fold Ru activity is required to reach the Fe economic reference under the frozen process model, whereas the maximum scaling-consistent activity headroom is 2.525-fold. The novelty is in coupling an industrial candidate-level parity target to an explicit physical/scaling reachability check, not in inverse design as a general concept.

### Safe manuscript formulation

> Integrated material/process design has previously translated process objectives into idealized material targets. Here the backward target is instead defined by candidate-level industrial parity and is immediately tested against the scaling-consistent catalyst manifold, separating an economically useful target from a physically reachable one.

---

## Contribution 3 — Decision-aware scientific compute

### Reviewer attack

> "Adaptive experiment selection, Bayesian optimization and tool-using scientific agents already allocate resources. Cost-aware scientific-agent benchmarks now explicitly account for simulation cost, and decision-focused active learning has been proposed for process scale-up."

### Closest prior art

The established background includes active learning, Bayesian reaction optimization, self-driving laboratories, ChemCrow, Coscientist and tool-using agent frameworks already cited in the manuscript.

**Cao et al., SimulCost, ICML 2026 / arXiv:2603.20253.** SimulCost evaluates LLM agents on physics-simulation parameter tuning while explicitly accounting for computational tool cost. Its results also show that higher task success does not imply superior compute efficiency relative to traditional search.

**Srinivas, Ray & Nakouzi, "Decision-Focused Active Learning for Scale-Aware Critical-Materials Recovery," arXiv:2609.09413 (2026 preprint).** This recent work explicitly frames experiment selection by downstream decision value / expected reduction in Bayes risk for scale-up decisions.

These works mean that neither "cost-aware scientific agents" nor "decision-focused adaptive science" is a safe priority claim.

### What therefore cannot be claimed

- Do not claim the first cost-aware scientific-agent benchmark.
- Do not claim the first decision-focused allocation of scientific resources.
- Do not claim that LLM adaptation is generally more compute-efficient than deterministic search.
- Do not equate task completion with efficiency.

### What remains distinctive and supported

DISCOVER evaluates a different object: a tool-using language model acts as the policy over a **frozen deterministic multiscale catalyst decision chain**, and the endpoint is not generic task success but a specific industrial decision consisting of winner, decision-pair ordering and reachability classification.

Four features remain unusually specific:

1. **Decision and quantitative convergence are scored separately.** Complete W+P+R decision recovery can occur before recovery of the canonical backward parity multiplier.
2. **The operating envelope is measured against a deterministic scientific policy.** The 206-CU fixed-policy threshold provides a concrete reference rather than an unconstrained agent-only benchmark.
3. **Mechanism is traceable.** Below the threshold, the strong model uses scoped/narrow process windows; the mechanism disappears once the budget can afford full-domain evaluation.
4. **The non-binding control prevents an efficiency overclaim.** At 5,000 CU, the same strong policy reaches the same decision but continues spending substantially after the decision is stable, so the supported claim is constraint-enabled decision recovery, not intrinsic compute frugality.

### Safe manuscript formulation

> Resource-aware agent evaluation and decision-focused adaptive experimentation are emerging independently. DISCOVER addresses a complementary question: whether a tool-using model can allocate a fixed scientific-compute budget across a deterministic multiscale decision chain so that the industrial decision converges before every intermediate quantitative target does, and under which model/budget regimes that behavior appears.

---

## Strongest integrated contribution

The manuscript is more defensible as an integrated decision framework than as three independent novelty claims. The sequence is:

```text
atomistic candidate ranking
-> candidate-specific process/economic propagation
-> decision-frontier preservation or reshaping
-> economic parity target
-> scaling-consistent reachability
-> unresolved decision evidence
-> finite scientific-compute allocation
```

No reviewed source identified in this audit combines this full chain as the primary scientific object. That does not justify a blanket "first" claim; it does justify presenting the paper as a **decision-centered synthesis** that links screening fidelity, backward reachability and scientific-compute allocation around the same industrial outcome.

---

## Reviewer questions the manuscript should already answer

### "Is ranking inversion itself new?"

No broad priority claim is needed. Ranking sensitivity to reactor/test context is known. The paper quantifies atomistic-to-economic **decision-frontier fidelity** and shows that the same multiscale implementation can preserve or reshape rankings depending on downstream coupling.

### "Why is this more than Jacobsen's optimal catalyst curves?"

Jacobsen et al. identify the descriptor value associated with maximum ammonia activity under different reaction conditions. The present work compares **discrete candidates after candidate-specific process/economic optimization**, measures whether their ordering survives, and then asks what property shift would be required to overturn the resulting industrial decision.

### "Why is backward design more than inverse design?"

The target is not an arbitrary desired property or unconstrained optimum. It is the catalyst-property change required for one real candidate to reach the economic reference of another, followed by an explicit reachability test on the frozen scaling manifold.

### "Why is the Agent section more than active learning or Bayesian optimization?"

The agent is not choosing new experimental points to optimize an unknown response surface. It chooses among heterogeneous scientific actions in a known deterministic tool environment, and is scored on recovery of a structured industrial decision under a finite action-cost budget.

### "Is the agent more efficient?"

Not in general. The non-binding control shows that it can spend more than the fixed policy once the constraint is removed. The supported result is budget-localized decision recovery below the fixed-policy threshold for the strong tier.

---

## Priority wording to avoid across Abstract, Introduction and cover letter

Avoid:

- "for the first time, catalyst rankings are shown to invert after process propagation"
- "first framework linking DFT and industrial catalyst selection"
- "first inverse design from process economics to catalyst properties"
- "first decision-aware scientific agent"
- "agent reduces compute relative to deterministic methods"
- "universal ranking inversion"

Prefer:

- "decision-frontier ranking fidelity"
- "candidate-specific multiscale economic propagation"
- "candidate-level parity target and scaling-consistent reachability"
- "pathway-specific catalyst-to-process coupling"
- "capability- and budget-bounded decision recovery"
- "decision convergence can precede quantitative-target convergence"

---

## Literature added by this audit

- Wallenstein, D., Haas, A. & Harding, R. H. Latest developments in microactivity testing: influence of operational parameters on the performance of FCC catalysts. *Applied Catalysis A: General* **203**, 23–36 (2000). DOI: 10.1016/S0926-860X(00)00467-1.
- Wang, Z. & Hu, P. Towards rational catalyst design: a general optimization framework. *Philosophical Transactions of the Royal Society A* **374**, 20150078 (2016). DOI: 10.1098/rsta.2015.0078.
- Cao, Y. *et al.* SimulCost: A Cost-Aware Benchmark and Toolkit for Automating Physics Simulations with LLMs. *International Conference on Machine Learning* (2026); arXiv:2603.20253.
- Srinivas, N., Ray, D. & Nakouzi, E. Decision-Focused Active Learning for Scale-Aware Critical-Materials Recovery. arXiv:2609.09413 (2026 preprint).
