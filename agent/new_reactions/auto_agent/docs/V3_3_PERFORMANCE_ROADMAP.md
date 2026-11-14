# V3.3 性能提升计划：工程边界、确定性验证与自主流程优化

**日期：** 2026-11-14  
**状态：** 计划提案；不是已实现功能，也不是已通过的验证结论。  
**关联：** PR #122；`V3_FIVE_LAYER_DESIGN.md`；`evaluation/ch4_v31_test/CH4_HARNESS_TEST.md`

## 0. 目标与原则

目标不是单纯减少 token 或让 benchmark 数字更接近参考值，而是提升系统在真实工业问题上的四种能力：

1. **Engineering accuracy**：物料、能量、设备尺寸、CAPEX/OPEX 的物理和工程准确性。
2. **Decision quality**：Agent 能否根据证据选择机理、反应器、流程拓扑和模型边界。
3. **Robustness**：不同独立运行是否得到可复现、可解释的结果。
4. **Execution efficiency**：每个有效模型所需的 wall time、token、API 成本和人工介入。

优先级为：工程准确性与决策质量 > 鲁棒性 > 执行效率。不能用更少调用换取错误模型，也不能通过修改参考值、容差或未披露假设来“修到通过”。

**当前判断：先做 V3.3 的工程核算审计和重复性验证，再决定是否进入 V3.4。现在不应先增加新的 Agent、训练技巧或复杂 orchestration。**

## 1. V3.3 当前基线（来自仓库记录）

来源：`evaluation/ch4_v31_test/CH4_HARNESS_TEST.md`、`evaluation/ch4_v33_test/ch4_builds.json`。

| 指标 | V3.3 当前结果 | 参考值 | 当前判断 |
|---|---:|---:|---|
| H2 单耗 | 0.51285 t/t CH4 | 0.505，±5% | 通过 |
| CO2 单耗 | 2.79889 t/t CH4 | 2.785，±5% | 通过 |
| 外购能耗 | 7.15009 GJ/t | 3.84，±35% | 不通过 |
| 单位投资 | 1,410.19 USD/(t/y) | 684.20，−30%/+50% | 不通过 |

V3.3 的工业参考工况已改为 21 bar、有循环、尾气单独排出；H2 和 CO2 单耗回到容差范围。运行记录为 211 轮、151 min、6.66 M 建模输入 token、缓存命中 74%，按 gpt-5.5 标价折算约 USD 41。记录显示 `check_model` 通过、留出审查无命中、生成的 `model.py` 调用了 `unitops.py`。

当前模型报告的能耗贡献为 CO2 压缩 2.0、SNG 精制分离 3.1、出口冷却 1.8 GJ/t。**这些是待审计的模型归因，不应直接视为已确认的根因。**

重要限制：每个版本目前只有一次完整运行。测试记录明确指出，V2 的三次建模能耗曾分别为 5.3、18.0、15.9 GJ/t。因此，单次运行不足以证明版本间性能差异；V3.3 甲烷化结果目前应作为开发诊断，不作为独立、前瞻性的外部验证结论。

## 2. 第一优先级：先统一参考工厂的系统边界

当前最值得优先检查的不是立即修改某个能耗公式，而是确认模型和参考工厂是否在比较同一个系统边界。

根据当前测试文档引用的 D5.9：

- 3.84 GJ/t 的能耗目标由甲烷化电耗 0.29 kWh/m3 SNG 换算：约 1.46 GJe/t，再按电力一次能源效率 0.38 换算为约 3.84 GJ/t。
- 该参考边界说明 CO2 supply 和 grid injection 在边界之外。
- 684.20 USD/(t/y) 的 CAPEX 目标来自 Falkenhagen 甲烷化单元成本，文档标注为 **methanation unit only**。

这提示了一个可能影响结论的边界错配：当前 V3.3 flowsheet 计入 CO2 压缩、SNG 精制和冷却等单元，而参考能耗和 CAPEX 指标可能只覆盖甲烷化单元或不同的电力/设备范围。必须回到 D5.9 原文逐项映射，不能仅凭摘要判断。

### 必须形成的边界映射表

| 项目 | 当前模型是否计入 | 参考值是否计入 | 下一步 |
|---|---|---|---|
| CO2 进料压缩（1 → 21 bar） | 是，当前归因约 2.0 GJ/t | CO2 supply 标注为边界外，具体压缩界点待核实 | 对照 D5.9 电池界区/进料状态 |
| SNG 精制与尾气处理 | 是，当前归因约 3.1 GJ/t | 需要从 D5.9 流程图和电耗口径确认 | 核实产品规格、回收率、设备范围 |
| 出口冷却 | 当前报告约 1.8 GJ/t | 参考值是否包含冷却公用工程需核实 | 区分热负荷和购入能源 |
| 甲烷化反应器及其热管理 | 是 | 甲烷化单元目标应覆盖的核心部分 | 对齐设备及能耗定义 |
| 产品并网压缩/注入 | 需要确认 | grid injection 标注为边界外 | 两边统一排除或另列 |

在边界核对完成前，不得直接删除 CO2 压缩、分离或冷却项，也不得将当前 7.15 GJ/t 直接归因为模型公式错误。应同时保留“参考边界内”与“扩展全流程边界”两套可追溯结果（若来源允许）。

## 3. 能量账本：把热负荷、轴功和外购能源分开

为每个单元操作生成独立 Energy Ledger，至少包含：

- 单元名称、入口/出口物流、流量、压力、温度；
- duty 类型：反应热、显热、潜热、压缩轴功、冷却负荷、制冷负荷；
- final energy / purchased electricity / purchased fuel / internal fuel；
- 一次能源换算因子及来源；
- 热回收量、内部燃料利用量；
- 最终计入 benchmark 边界的外购能源；
- 手算交叉验证和不确定性范围。

### 三个优先审计点

1. **CO2 压缩：** 核对入口状态、出口压力、级数、级间冷却、等熵效率和一次能源换算。当前 2.0 GJ/t 是一次能源口径的模型归因；要分别报告 shaft work、购电量和 primary energy。若参考边界不含 CO2 supply，必须先解决边界再比较。
2. **SNG 精制：** 核实采用的分离技术、产品纯度、CH4 回收率、尾气组成和循环方式。当前 `unitops.split()` 是理想组分分割函数，本身不计算 PSA/膜分离的压缩、真空、再生或分离能耗；这些必须由独立、可追溯的分离模型补足，不能把理想 split 当成完整分离设备模型。
3. **出口冷却：** 1.8 GJ/t 若代表热量移除负荷，不等于 1.8 GJ/t 外购能源。应按冷却水、冷却塔或冷冻机方案，计算泵/风机电耗或 COP 对应的购电量；冷却 duty 单独保留，不直接计入 purchased energy。

同时检查热回收与内部燃料是否重复抵扣或重复计入。当前 `unitops.heat_recovery()` 是基于 approach fraction 的简化热回收估算，不等同于完整 pinch analysis；其适用范围和参数应显式记录。

## 4. CAPEX 账本：先对齐设备范围，再审计成本相关式

当前 1,410.19 USD/(t/y) 高于 684.20 的参考值，但参考文档将目标标为 methanation unit only。若当前模型汇总了整个 flowsheet 的压缩、分离、冷却和其他设备，直接比较两者并不能证明模型投资高估。

每个设备必须单独输出 CAPEX Ledger：

- equipment type / duty / size / capacity basis；
- bare equipment cost 或 installed cost；
- installation factor、pressure factor、material factor；
- cost index、币种和基准年份；
- capacity scaling exponent 和来源；
- 设备是否已包含在其他 package cost；
- 是否计入电气、仪表、土建、工程费和 contingency；
- 对应参考工厂是否在同一设备边界内。

重点审计：压缩机和循环压缩机是否重复；循环流量是否错误应用到新鲜进料设备；bare cost 是否再次乘安装系数；pressure factor / CEPCI 是否重复应用；年产能、capacity factor 和 USD/(t/y) 单位是否一致。

若找不到全流程 CAPEX 参考值，应把“甲烷化单元 CAPEX 对照”和“全流程模型 CAPEX”分开报告，不能通过删减模型设备让数字表面吻合。

## 5. 现有代码资产与针对性补强

当前代码已经具备不少 V3.3 能力，不应重复造轮子：

| 现有资产 | 已有能力 | 需要补强的地方 |
|---|---|---|
| `unitops.py` | compressor、pump、sensible/latent heat、fired heater、heat recovery、recycle/purge、split、CAPEX scaling | 每个函数做独立手算测试；明确适用范围；分离模型补充真实能耗/成本 |
| `physics_gate.py` | 独立 ideal-gas 物理检查、压缩功和设备边界检查 | 审计一次/终端能源口径、冷却 duty、分离能源和 CAPEX 设备范围 |
| `basis_gate.py` / `basis.json` | 设计基准和进料边界检查 | 确保 benchmark 边界、流程边界、模型边界完全一致 |
| `build_mode.py` | flowsheet 先行、model contract、阶段交接、假设敏感性、Critic | 保留现有决策流程；用真实运行 trace 评估哪些反馈动作有效 |
| `validate_v33.py` | 单元库只读、milestone handoff、每个 milestone 只重置一次 | 增加工程账本和单元操作回归测试 |

`build_mode.py` 已包含独立 Critic 模型路由、artifact-only 输入、critic token 记账和 critique 收尾检查；因此当前不把“再增加一个 Critic”列为优先任务。下一步应验证 Critic 是否能稳定发现真实的边界、分离和设备成本错误，而不是只确认它被调用。

另需统一版本元数据：Build Mode 标记为 `V3.3-process-design`，而当前 `unitops.py` 文件头写有 V4；应明确区分 harness 版本与通用单元库版本，避免运行记录产生歧义。

## 6. 执行效率：先分析账本，不盲目压缩调用

V3.3 的 211 轮、151 min、约 USD 41 是当前观察值；缓存命中 74%。上下文重置修复已进入代码，并由 `validate_v33.py` 检查 milestone 只在首次进入时重置、handoff 携带 notes/decisions/gate status。该问题先视为已修复，下一次运行只验证实际效果，不重复开发同一机制。

后续效率优化依赖 `stage_ledger.csv`、`ledger.json`、`trace.jsonl`：

- 统计各阶段 token、调用次数、wall time、缓存命中、API 成本；
- 区分有效模型决策、代码调试、重复读取、重复计算和无效循环；
- 统计每个有效模型的成本，而不只统计总轮数；
- 记录人工 Inspect、补证据、纠错和否决次数。

建议采用有上限的纠错循环：每次 gate/critic 返回具体问题；Agent 提交有依据的修订；再次验证；若仍失败则保留失败原因并升级人工 Inspect，不无限重复。不得为了降低 token 删除必要的科学判断。

## 7. 分阶段路线

### Phase 0 — Freeze the baseline（不改模型）

- [ ] 冻结当前 V3.3 prompt、代码、unitops、physics gate、flowsheet、basis、sources 和运行输入的 hash。
- [ ] 保存 V3.1/V3.2/V3.3 历史结果，不覆盖旧数据。
- [ ] 从 D5.9 原文建立能耗和 CAPEX 的系统边界映射表。
- [ ] 明确 final energy、purchased energy 和 primary energy 的换算口径。

### Phase 1 — V3.3.1 Engineering Audit（最高优先级）

- [ ] 输出逐单元 Energy Ledger 和 CAPEX Ledger。
- [ ] 对 CO2 压缩、SNG 精制、冷却分别做手算。
- [ ] 核实参考工厂的设备边界和公用工程边界。
- [ ] 检查 recycle flow、热回收、内部燃料和设备成本是否重复计入。
- [ ] 只修正已被证据确认的模型错误；不改参考值和容差。
- [ ] 为每项修正增加 regression test。

### Phase 2 — V3.3.2 Reproducibility（工程审计通过后）

- [ ] 使用同一冻结输入、同一参考边界和同一评估规则，进行至少 3 次独立 V3.3 建模。
- [ ] 报告 median、IQR、pass rate 和每次运行的成本/时间/人工介入。
- [ ] 若要比较 V3.1/V3.2/V3.3，必须在相同输入协议和同一评估边界下重复；旧的单次结果只作为历史诊断，不作强版本优劣结论。
- [ ] 开发集与盲测集分离；模型改进不能继续使用同一留出结果调参后再宣称盲测通过。

### Phase 3 — V3.4 Autonomous Process Optimization（前两阶段达标后）

采用“离散流程决策 + 连续数值优化”的分工：

- **AI 外层：** 根据证据提出少量（建议 2–3 个）候选流程拓扑，说明 reactor、compression、separation、recycle、purge、heat recovery 的选择理由和备选方案。
- **确定性内层：** 对每个候选流程优化允许变化的连续变量，例如 T、P、per-pass conversion、recycle/purge ratio、压缩级数和热集成参数。
- **独立验证：** 对每个候选检查物料/能量守恒、热力学可行性、产品规格、设备边界和 CAPEX。
- **决策反馈：** 返回成本、能耗、约束违反、敏感性和 Pareto trade-off，由 Agent 解释并选择下一步，而不是让 LLM 反复猜数值参数。

这一步才是真正的 autonomous process design；不是让 Agent 多生成几张 flowsheet，也不是把数值优化器包装成新的 Agent。

### Phase 4 — V3.5 Decision-aware Resource Allocation（后续研究方向）

在工程模型和验证协议稳定后，再研究有限预算下“下一步最值得做什么”：

- 哪个证据缺口可能改变流程选择或经济排名；
- 哪项参数核验/实验/DFT 计算最可能降低决策不确定性；
- 哪些计算虽然降低模型误差，却不会改变最终决策；
- 何时应停止当前分支、继续搜索或请求人工 Inspect。

评价应面向 downstream decision / regret 的变化，而不是只看 surrogate error 或 token 数。

## 8. Benchmark 必须拆成两种任务

1. **Industrial Reconstruction：** 固定参考工厂的系统边界、设备范围、产品规格和操作条件，评价模型是否能重建已知工业流程。这里可以使用预先定义的能耗/CAPEX 容差。
2. **Autonomous Process Design：** 固定原料、产品规格、产量和安全/设备约束，允许 Agent 选择流程拓扑和优化操作条件。这里评价物理可行性、单位产品成本和 Pareto trade-off，不因设计优于参考流程而判错。

两类任务不能混用同一评分规则。Holdout TEA 必须对 Agent 隔离；开发集上的诊断性修正不能包装成独立盲测。

## 9. 成功标准

- 每个主要设备的能耗、能量类型、CAPEX 和边界归属可追溯。
- 冷却 duty 不被直接等同于外购能源；分离模型明确包含真实能耗和设备成本。
- 模型与参考值使用相同设备范围、系统边界、币种/年份和一次能源口径。
- 关键公式通过独立手算和单元测试；修改不破坏已通过的 H2/CO2 物料衡算。
- 至少 3 次独立运行报告 median/IQR/pass rate，不以单次结果宣称版本提升。
- 效率以 cost per valid model、wall time、tokens、human interventions 衡量，不单独优化轮数。
- 新流程优化结果满足全部硬约束，并提供可复现的候选方案比较。

## 10. 明确暂不做的事

- 不重写 V3.3 五层架构；先复用当前 Build Mode、unitops、physics gate、basis gate 和 Critic。
- 不先加多 Agent、fine-tuning 或新的 orchestration 技巧。
- 不因为能耗/CAPEX 超标就直接调低压缩功、删除冷却负荷或改变成本系数。
- 不改 reference value、容差或 holdout 数据来获得通过。
- 不把一次运行、`check_model` 通过或 Critic 完成等同于工程模型已被外部验证。

**近期唯一执行重点：V3.3.1 Engineering Audit。先回答“我们是否在比较同一个工厂边界、同一种能源和同一组设备”，再决定要改哪条公式。**
