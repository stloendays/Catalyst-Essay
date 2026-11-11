# Supervisor guidance — 2026-11-11

**Paper:** *Laboratory catalyst leaders are often not the plant-level optimum* (Nature Chemical Engineering target).

**Record status:** This document preserves the supervisor's latest guidance and separates it from the analysis below. The transcript is retained as supplied by the author, including speech-recognition wording. This is a guidance/plan record, not evidence that the proposed autonomous runs or validations have already passed.

## 1. Executive summary

Do not freeze the paper's final identity, title, narrative emphasis or contribution ordering at this stage. The existing NCE paper and its question provide the working context and continuity point, but the immediate priority is to define the next research tasks and connect them to prior models, data, code and benchmark cases. The paper may change its emphasis once the new results are available.

The supervisor has made the AI role explicit: **AI is one of the core contributions of the research work and should take over the complete research pipeline**, not merely extract numerical information from papers. How this capability is ultimately positioned in the paper is left open until the results are available.

The scaling axis must also change. The main scaling experiment should be the **number of distinct reactions**, not simply the number of papers for one reaction. Extending one reaction from dozens to hundreds of papers mostly increases evidence volume; extending to 10+ different reactions can reveal which reaction classes are sensitive to catalyst ranking and which are dominated by feedstock, energy, separation or other process costs.

The immediate sequence is:

1. Run PDH and CO₂ methanation as complete AI-led, end-to-end cases.
2. Compare each AI-built model with published TEA / industrial references.
3. Blind-test the AI on the previously hand-built ammonia and methanol cases.
4. Record cost, time, tokens, human effort and every human intervention at each stage.
5. Only after the first two reactions and internal validation are credible, scale to 10+ reactions.

## 2. Supervisor's original transcript

> 我先把定位给定下来啊，就是以我前上面说的为准，就是说咱们AI是要作为core contribution之一，就是它在接管整个pipeline。然后，化工那条主线就是说要保留，就是说实验室到工厂排名会不会变，为什么会变，这个还是有，而且这个可能是一个个也是另外一个重点，可能是排第一的一个点，OK, 然后，AI scaling up这个点呢，我觉得规模应该要放在反应的数量上，而不是论文的数量。能理我理解我的意思吧，这个应该很好理解啊，就是你同一个反应，你多抽几百几百篇结论，其实还是那个结论没有什么意义，知道吧？但是，你扩到十几二十几个反应，那就能回答一个新的问题。哪类反应你的催化剂的排名对工厂的成本是最要紧的啊，然后哪类根本无所谓啊，以及为什么那这个其实就是人工做不出来的啊，这才是我们AI的价值。所以就是你好好回味一下我这个我我我我定的这个frame frame好吧。然后，想先问你两个问题。第一，就是你这里做的这个实验PDH和甲烷化的这个工厂模型是怎么来的？是你自己搭的呢，还是AI搭的好吧？回答这个问题。第二个问题是，现在整个流程里面，哪些步骤还是人工在做啊？你列一下给我好吧？列出来。因为我觉得真正的难点不在于抽数据啊，就是你现在把AI就完全就当做一个数信息抽取器，这个太难了，这个AI根本就没有用在我们这里面，在我看来是没有用的。我用AI搜数据放在非AI时代，放在以前也可以做这个事情啊。所以所以我觉得真正难点不在输出数据，而是在建模这一步，知道吧，所以，如果说模型还是你手搭的，那就还是AI收数据，人建模，跟这个就跟跟没用AI就没什么本质区别。这个能理解吧，对吧？所以下一步就是说，你先拿这两个反应做一个完整的闭环的一个pala抽取建模，然后算这个成本，再到分析，你全部让AI来做，你负责只做这个局局部的这个监理啊，或者叫inspect。然后AI建出来的这个模型啊，要跟这个反应已经发表的那些TA，你要让他去对啊，去对一下看对不对得上啊。另外呢，就是这个还是我之前一直说的这个代表性的这个氨和甲醇那几个，我们手工做的几个case，其实呢，你正好可以当做一个验证集，你让AI从零见一面，看能不能得出一样的结论是吧。如果能那就是那就说明我们的AI的这个pipeline，这个automation pipeline就是好是吧，就是这不就是最有力的说服的证据吗？上面你给我的这个数据就是说，每篇0.52美刀，19篇是吧，9.5分钟，然后人工每天100分钟。嗯，这个数字OK，好吧。然后后面建模也每每一步的建模也都提供这些数字好吧，我知道是AI写的也要也要要提供一下。然后我们把这些代价和效率都记录下来，对这些数据可能会有用。后面我们会嗯会写到论文里面，就是哪些是AI自己做的，以及人工介入几次都报出来。这样我们就可以算成本嘛，以及这个劳动嘛，就AI节省了多少劳动，这个数量以及花了多少成本啊。如果你的Palo跑通了之后，然后我们再扩到10个以上的反应，好吧，扩到10个以上的反应。跑不通的话，我们再商量。然后，你你而且，你要想在这个过程中，你要思考就是把思路和你觉得难的地方写一个简单的方案，再你再发给我啊。所以是这么安排的。

**Transcript note:** This is the user-supplied speech transcript. Homophones and possible ASR errors have not been silently corrected.

## 3. Interpretation for the research work (paper framing remains open)

### 3.1 Keep continuity with prior work; leave the paper framing open

*Laboratory catalyst leaders are often not the plant-level optimum* is the current project context and a useful entry point to the prior work, not a fixed commitment to the final title or manuscript emphasis. The paper may change its focus, contribution ordering or narrative after the next experiments. At this stage, do not decide the final paper framing; prioritize a coherent sequence of research tasks that reuses and tests the existing work.

The inherited scientific questions that the next tasks can build on include:

- Does the laboratory ranking predict the economically preferred catalyst at the plant level?
- If it does not, where does the ranking change along the multiscale chain?
- Which catalyst properties actually control plant cost, and which are attenuated by feedstock cost, equilibrium, recycle, separation, equipment or operating constraints?
- Do these relationships differ across reaction types and process pathways?

The supervisor wants AI to be a core contribution of the research work by taking over the full pipeline. The eventual paper-level framing and relative emphasis remain open; decide those after the end-to-end experiments, external validation and blind tests produce evidence.

### 3.2 Scaling by reactions, not papers

The new scaling question is not “how many papers can the system read for one reaction?” but “what patterns emerge when the same research pipeline is applied to many distinct reactions?”

Candidate examples already in the project include PDH, CO₂ methanation, ammonia synthesis and methanol synthesis. Additional reactions should be selected based on evidence availability and process diversity, not to force a desired outcome.

Cross-reaction questions include:

- In which reactions is plant cost highly sensitive to catalyst activity or selectivity?
- In which reactions do feedstock or hydrogen costs dominate, making catalyst ranking relatively unimportant?
- When do stability, regeneration, surface coverage, equilibrium, recycle or separation control the economic ranking?
- Why does the same laboratory metric have different industrial consequences in different reactions?

**Methodological recommendation:** compare laboratory and plant rankings within each reaction. Across reactions, compare rank-change statistics and cost-driver/catalyst-to-process coupling patterns. Do not rank different products directly by their absolute USD/t values without a justified common basis.

### 3.3 AI must make scientific modeling decisions

The insufficient workflow is:

Literature search → PDF reading → data extraction → hand-built reaction-specific plant model.

The required AI-led workflow is:

1. Search and screen evidence; explain inclusion/exclusion decisions.
2. Infer plausible reaction mechanisms and select a model with evidence and rationale.
3. Select kinetic expressions, relevant elementary steps and assumptions.
4. Choose reactor representation and operating variables, e.g. isothermal/adiabatic treatment and transport constraints.
5. Decide whether recycle, separation, compression, heat management, regeneration and catalyst replacement must be represented.
6. Source parameters, record units and provenance, and distinguish measured values from assumptions and uncertainty ranges.
7. Build an executable reaction-specific model.
8. Run deterministic solvers for balances, optimization and costing.
9. Analyze rankings, cost attribution, sensitivity and backward design.
10. Validate against published TEA and independent benchmark cases.

The LLM does not need to perform numerical integration or optimization itself. Fixed Python solvers, property databases and numerical tools can remain. The essential requirement is that the **reaction-specific model structure, model selection, parameter choices and modeling rationale are not pre-decided by a human and merely handed to the AI**.

## 4. Answers to the supervisor's two diagnostic questions

### 4.1 Who built the current PDH and methanation plant models?

The current main analysis chain is primarily a **pre-designed deterministic engineering model**, not a model independently constructed from scratch by AI during the reported analysis.

Relevant files in PR #122 include:

- **agent/new_reactions/plant_models.py** — PDH and CO₂ methanation cost equations and plant calculations.
- **agent/new_reactions/params_process.json** — plant scale, operating conditions, feed prices, CAPEX and catalyst assumptions.
- **agent/new_reactions/build_params.py** — parameter assembly.
- **agent/new_reactions/analyze.py** — cost calculation, ranking, attribution, sensitivity and backward design.

The PDH case uses an Oleflex-type reference plant; the methanation case uses a staged adiabatic plant. The existing models include a first-order approach-to-equilibrium approximation to transfer laboratory activity to plant conditions, as well as catalyst productivity/inventory and process-cost terms.

Humans had already defined the main model structure and engineering assumptions. Claude Code / AI assisted with implementation, data processing and analysis. Therefore the current main-chain results must not be described as fully AI-built models.

PR #122 also contains exploratory autonomous-agent paths:

- A full mode starting from a reaction description, in which the agent can source parameters and write normalization, plant-model and analysis code.
- A masked-database mode, in which the agent receives already-extracted records and works under a reveal budget. This is not a complete literature-to-plant pipeline.

These are useful starting points, but they do not yet establish that the requested end-to-end autonomous modeling system is robust and validated. As inspected on 2026-11-11, PR #122 is open and marked draft; its branch is **analysis/ai-pipeline-new-reactions-2026-11-10**.

### 4.2 Which current steps still involve human-designed logic?

| Stage | Current state | Required change |
|---|---|---|
| Research question / reaction scope | Human-defined | Keep scope explicit and logged |
| Literature search / screening | Automated search and AI screening exist | Agent should explain criteria and exclusions |
| PDF download / OCR | Tool-automated, with access failures | Log failures, missing SI and manual recovery |
| Data extraction | LLM extraction plus fixed normalization/self-check code | Preserve evidence locations and physical checks |
| Mechanism / kinetic-model selection | Mainly predefined in the current main chain | Agent must choose and justify |
| Reactor / flowsheet structure | Mainly predefined in the current main chain | Agent must choose from evidence and process requirements |
| Plant parameters / assumptions | Human-configured and source-curated | Agent should source, parameterize and mark uncertainty |
| Cost-model code | Existing deterministic model is predefined | Agent builds the reaction-specific model; deterministic code executes it |
| Ranking / attribution / sensitivity | Mostly fixed analysis code | Agent should choose the analysis and explain results |
| External validation / scientific review | Human Inspect required | Log every check, correction and rejection |

Automation is not equivalent to AI decision-making. AI-generated code is not, by itself, evidence that a model is physically or industrially correct.

## 5. Required validation design

### 5.1 External validation: PDH and CO₂ methanation

For each reaction, compare the AI-built model against published TEA or a traceable industrial case. Compare more than the final USD/t value:

- System boundary, plant capacity and annual operating hours.
- Material and energy balances.
- Reactor type, temperature, pressure and conversion.
- Recycle, separation, compression and heat-management assumptions.
- Feedstock, energy, CAPEX, OPEX and catalyst cost.
- Final product cost and the breakdown of major cost contributors.

When results differ, identify whether the cause is model structure, parameter choice, system boundary or source convention. Do not tune assumptions after seeing the answer merely to force agreement.

### 5.2 Internal blind validation: ammonia and methanol

The previously hand-built ammonia and methanol cases should become internal benchmark sets.

Recommended protocol:

1. Freeze the hand-built models, parameters, outputs and version hashes as reference answers.
2. Do not expose their code, configuration, reports or final rankings to the agent.
3. Give the agent only the reaction name, research objective and normally available public evidence.
4. Let it independently rebuild the models and complete the cost analysis.
5. Evaluate the outputs against the frozen references: costs, operating conditions, cost breakdowns, laboratory/plant rankings and bottleneck conclusions.

Reproducing the key conclusions without answer leakage would be strong evidence for the automation pipeline. Differences must be diagnosed, not hidden by reporting only whether the final ranking happens to match.

## 6. Cost, time, tokens and human-labor accounting

The supervisor wants every stage to report its resource cost and efficiency. Record at least:

| Field | Required record |
|---|---|
| Stage | Search, screening, OCR, extraction, mechanism selection, model building, parameter sourcing, simulation, validation, analysis, report |
| AI action | The decision or operation actually performed by AI |
| Tools / deterministic code | Tool, solver, script and version |
| Input / output tokens | Separately recorded |
| API cost | USD cost using the actual model price |
| Wall time | Actual stage duration |
| Human time | Active human minutes |
| Human interventions | Number of interventions |
| Intervention type | Review, correction, missing-data recovery, model change, rerun or rejection |
| Output / evidence | Files, model version, source locations and validation result |
| Quality | TEA deviation, physical checks, ranking agreement and unresolved issues |

Existing extraction baseline:

- 19 papers in the current PDH / methanation run.
- 438 extracted records; 314 usable for the plant models.
- Approximately USD 0.52 per paper.
- Approximately 36,000 tokens per paper.
- Approximately 9.5 minutes for the final parallel extraction pass.
- Existing manual single-extraction-plus-verification benchmark: 107 minutes per study (the supervisor referred to roughly 100 minutes; the exact task definition should be standardized).

The existing ledger records search, download, OCR, extraction and a combined downstream stage. However, normalization, self-check, plant models, analysis and sensitivity are grouped together; model code was written during the OCR/extraction window. The ledger therefore does not yet isolate the AI cost of model selection, parameter research, model construction, debugging and TEA validation. Nor does it yet provide a complete human-Inspect count and labor ledger.

The manual baseline must use the same task scope and quality standard as the AI run. The extraction baseline must not be applied to all modeling work without a separate measurement.

## 7. Existing plan that now needs revision

**agent/new_reactions/PLAN_AI_CHAIN.md** still describes an older setup in which the agent mainly chooses papers, masked cells, stopping points and catalyst conditions while plant models and cost formulas remain fixed.

That is inconsistent with the 2026-11-11 guidance. The revised plan should state:

- AI selects and builds reaction-specific models.
- Generic solvers, property libraries and execution tools may be reused.
- The agent must not be limited to filling parameters into a prewritten reaction-specific plant model.
- Published TEA comparison and internal blind validation are mandatory.
- Scaling is measured primarily by distinct reactions.
- Each stage records AI/human responsibility, time, tokens, API cost and quality.

This guidance record does not itself change any frozen scientific model, manuscript number or PR #122 result.

## 8. Open technical questions

1. **Boundary of autonomous modeling:** Which generic property databases, thermodynamic libraries, solvers and engineering templates may the agent use? Which reaction-specific decisions must be made by the agent?
2. **TEA acceptance criteria:** What tolerances apply to total cost, balances, operating conditions and cost breakdown? How should different published system boundaries be reconciled?
3. **Model-quality gates:** Which physical constraints, dimensional checks, limiting cases and numerical-stability checks must pass before a model can rank catalysts?
4. **Blind-test leakage:** How will we guarantee that the agent cannot access the ammonia/methanol hand-built code, parameters or results?
5. **Human-labor baseline:** How will manual end-to-end modeling time be measured under the same scope and quality requirements?
6. **Reaction selection:** How will the 10+ reactions be chosen to represent process diversity and evidence availability, rather than to favor easy or inversion-rich examples?
7. **Cross-reaction metrics:** How should rank-change magnitude and cost-driver patterns be compared without directly ranking different products by incomparable USD/t values?

## 9. Immediate execution order

- [ ] Freeze the AI-autonomous task definition and input boundary for PDH and CO₂ methanation.
- [ ] Preserve the existing hand-built plant models separately as references; do not expose them to the agent.
- [ ] Design the agent workflow for model selection, model construction, parameter sourcing, code generation, execution, validation and reporting.
- [ ] Add stage-level time, token, API-cost, human-labor and intervention logging.
- [ ] Complete PDH, then CO₂ methanation; compare each with published TEA.
- [ ] Freeze the ammonia and methanol hand-built cases and conduct blind AI reconstruction.
- [ ] Decide whether to expand to 10+ reactions based on model quality and blind-validation results.
- [ ] Send the supervisor a concise plan focused on the difficult model interfaces, validation criteria and likely failure modes.

## 10. References

- NCE manuscript page in Notion: [2026-10-26 manuscript record](https://app.notion.com/p/405c0ee7c03e81d3876df7061eefd39).
- GitHub repository: [stloendays/Catalyst-Essay](https://github.com/stloendays/Catalyst-Essay).
- Current exploratory implementation: [PR #122 — PDH and CO₂ methanation](https://github.com/stloendays/Catalyst-Essay/pull/122).
- This record: docs/SUPERVISOR_FEEDBACK_2026-11-11.md.

**Status:** This document records supervisor guidance and a proposed work plan. The PDH/methanation autonomous runs, TEA validation, ammonia/methanol blind tests and 10+ reaction extension remain to be executed.