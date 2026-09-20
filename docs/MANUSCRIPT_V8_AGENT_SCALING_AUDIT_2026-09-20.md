# Manuscript v8 Agent-scaling framing audit — 2026-09-20

Canonical draft: `docs/MANUSCRIPT_MAIN_TEXT_v8_2026-09-20.md`  
Figure map: `docs/FIGURE_MAP.md`  
Caption set: `docs/MAIN_FIGURE_CAPTIONS_v4_2026-09-20.md`

## Framing change from v7

V7 correctly separated the Agent from the source of the physical ranking and mechanism, but described it too narrowly as an **operational extension**. V8 preserves the same evidence boundary while elevating the Agent to the **workflow-automation and scaling layer** of the paper.

The resulting architecture has three linked contributions:

1. **Scientific decision geometry** — ranking fidelity, catalyst-to-process coupling and causal boundaries.
2. **Backward design** — economic parity targets and physical reachability.
3. **Scalable execution** — Agent orchestration that repeatedly executes the deterministic decision workflow under finite compute.

## Supported Agent claim

The frozen benchmark supports the following measured result:

- deterministic fixed-policy completion: **206 CU**;
- strong lowest tested stable complete-decision allowance: **75 CU**;
- median decision-stable spend at 75 CU: **52.5 CU**;
- protocol-complete oracle: **22 CU**;
- non-binding median decision-stable / final spend: **566 / 714 CU**;
- non-binding median post-stability overrun: **148 CU**;
- non-binding canonical narrow-window use: **0/20**.

The benchmark therefore establishes a capability- and budget-dependent decision-allocation envelope.

## Workflow-scaling interpretation

The scaling contribution comes from architecture rather than from assigning scientific truth to the language model:

`reaction-specific deterministic tools -> shared decision objects -> Agent action selection -> repeated decision execution`.

Reaction-specific modules retain the physics, kinetics, process equations and economic definitions. The Agent operates on common decision objects such as ranking, feasibility, parity and reachability. This separation makes the workflow reusable across repeated candidate-screening instances and provides the implementation pattern for batch deployment as additional reaction-specific modules are connected.

The manuscript does **not** claim that cross-reaction Agent transfer has already been experimentally benchmarked. The current quantitative Agent benchmark remains the frozen NH3 decision environment; cross-reaction scalability is an architectural capability of the modular workflow.

## Main-text changes

- Abstract: Agent now appears as the layer that turns one-off multiscale analysis into a repeatedly executable workflow.
- Introduction: adds the methodological question of how the bidirectional framework can be executed repeatedly rather than manually rebuilt.
- Results §3.6: renamed to **“A decision-aware agent turns the framework into a reusable execution workflow.”**
- Discussion: Agent is described as the scaling layer of the framework, with batch screening as the downstream workflow implication.
- Methods: renamed to **“Decision-aware workflow automation and agent benchmark.”**
- Figure 6: reframed from an operational add-on to reusable scientific-workflow orchestration.

## Evidence boundary retained

V8 still attributes:
- catalyst ranking and physical mechanism to deterministic scientific models;
- economic boundaries to the frozen process/economic calculations;
- compute allocation and action sequencing to the Agent.

Thus the Agent contribution is strengthened without transferring unsupported physical credit from the scientific tools to the language model.
