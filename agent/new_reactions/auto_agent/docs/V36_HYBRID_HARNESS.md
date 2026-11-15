# V3.6 混合式基础 harness：调工具，但有边界

2026-11-15。结合两份方案：GPT 的 V3.5 五层流程（Notion，2026-11-15 截图）和本分支已实现的 V3.4/V3.5（`docs/V34_LEAN_CHEM.md`、`docs/V35_DESIGN_OPT.md`）。老师的要求：允许 AI 调工具，但不是完全自由，也不是完全固定。

## 1 两份方案各自的长处

| 来源 | 保留的内容 |
|---|---|
| GPT V3.5 | 五层结构（证据 → 决策 → 自主建模 → 确定性执行与独立验证 → 决策反馈）；跨尺度接口契约（DFT→MKM→反应器→流程→TEA），每个接口给 PASS / WARNING / BLOCK；模块登记（已验证模块只读，实验模块走沙箱 → 验证 → 晋升）；动态工作流图和带版本的重规划；AI 做离散选择、程序做连续优化；贯穿各层的治理（分阶段工具、事件日志、哈希、费用账本、留出隔离） |
| 本分支 V3.3.1–V3.5 | 固定单元库和核算账（冷却、分离、投资依据）；物理门控；读文件缓存、摘要、批量工具、分阶段工具菜单；model.py 改动即检查；设计变量 + 确定性优化（optimize_design）；分离方案比较；留出拦截（规范化拼写、检查所有工具参数）；额度路由与费用上限 |
| 本分支实测的问题 | AI 每次手写 400 多行 model.py，错误每次不同（COP 10、错用系数、重复放大、NameError、拍定设计参数）。门控只能事后堵 |

结合的要点：**AI 不再手写整个工厂模型。** AI 写的是一份带类型的流程说明，数值由固定核心和登记工具算出；确实缺工具时，AI 可以写新模块，但要过沙箱验证。

## 2 三级工具

| 级别 | 内容 | AI 能做什么 | 不能做什么 |
|---|---|---|---|
| **T0 固定核心** | 流程求解器（序贯模块法，循环用 Wegstein 收敛）；物性（`thermo`/`chemicals`，理想气体与 Peng-Robinson）；单元库 UO（压缩、换热、冷却公用工程、加热炉、反应器、闪蒸、膜/PSA、精馏简捷法、循环与吹扫）；设备投资关联式（Turton/Seider，CEPCI 换算）；物理门控、核算账、留出拦截 | 每次都被调用；AI 只能填参数 | 修改、绕过 |
| **T1 登记工具** | 文献检索、下载、OCR、抽取；MKM 求解器；Cantera（平衡、动力学）；IDAES/Pyomo 单元模型（用于严格校核）；`optimize_design`；敏感性分析 | 自主决定何时调用、调哪个；每个工具有输入格式、单位、适用范围 | 越出适用范围时结果带 WARNING；不能改工具本身 |
| **T2 沙箱模块** | AI 新写的单元模型或关联式（登记库里没有的） | 声明输入输出和单位，写进沙箱 | 不过守恒测试、参考算例和门控就不能用；能用时结果标"实验模块"并带 WARNING；晋升到 T1 要人工批准并跨运行复测 |

这就是"不是完全自由，也不是完全固定"：T0 定死，T1 自主选用，T2 允许创造但要验证。

## 3 AI 交出的东西

| 文件 | 内容 | 谁来算数 |
|---|---|---|
| `basis.json` | 界区、产能、进料与产品状态，各附证据 | AI 写，`basis_gate` 查 |
| `flowsheet_spec.json`（替代手写 model.py） | 单元从 UO 目录里选；物流连接；设计变量及上下限；产品规格；每个参数的来源编号；分离、反应器的备选方案 | T0 求解器 |
| `kinetics.json` | 速率式从登记形式里选（幂律、LHHW、MKM），参数由固定工具拟合 | T1 拟合工具 |
| `sources.csv`、`decisions.jsonl` | 每个数的来源，每个选择的备选和理由 | 门控与 Critic 审查 |
| `modules/*.py`（可选） | T2 沙箱模块 | 沙箱测试 |

## 4 跨尺度接口契约（沿用 GPT 方案，判定统一为 PASS / WARNING / BLOCK）

| 接口 | 传递的量 | BLOCK 的例子 | WARNING 的例子 |
|---|---|---|---|
| DFT → MKM | 能量参考、位点、覆盖度 | 参考态不一致 | 描述符超出拟合范围 |
| MKM → 反应器 | TOF、产率随 T、P、组成 | 单位不对、违反平衡 | 外推出实验温度范围 |
| 反应器 → 流程 | 物流、热负荷、压力 | 元素不守恒 | 单程转化接近平衡上限 |
| 流程 → TEA | 界区、能耗、设备规模 | 界区和成本依据不一致 | 投资指数缺少文献依据 |

BLOCK 时停止向下游传递，回到对应层修改；WARNING 时继续，并把不确定性带进报告和敏感性分析。

## 5 一次运行怎么走

1. **证据层**：检索、筛选、下载 OCR、抽取；留出拦截全程生效。
2. **决策层**：确定机理、动力学形式、反应器和流程拓扑，每项至少两个备选并给出计算值；写出 `workflow.json`（本次运行要走的步骤）。
3. **建模层**：写 `basis.json`、`flowsheet_spec.json`、`kinetics.json`；缺工具时才写 T2 模块。
4. **确定性执行与验证层**：T0 求解 → 接口契约 → 物理门控 → `optimize_design`（AI 选拓扑，程序优化连续变量）→ 敏感性分析 → 独立 Critic（只报工程问题）→ 参考工厂用 IDAES 严格校核一次 → 留出 TEA 评估（评估侧，AI 看不到）。
5. **反馈层**：失败按类别归档；证据债和假设复查；重新规划时开一个新的工作流版本，旧的运行全部保留；人工检查后出报告（成本、排序、遗憾值、敏感性、反向设计）。

贯穿全程：分阶段工具菜单、事件日志、哈希冻结、token/时间/费用/人工干预账本、留出隔离、额度路由（个人额度优先，老师 key 有上限）。

## 6 预期能减少哪些错误（以已有运行为例）

| 已出现的错误 | 在 V3.6 下 |
|---|---|
| 冷却按 COP 10 计电、套用常压分离系数 | T0 单元直接计算，AI 不填这类系数 |
| 投资份额被循环流量重复放大、规模指数取 1 | 投资由关联式按设备规模计算，或按门控规则缩放 |
| model.py 里的 NameError | 不再手写 model.py |
| 渗透压、产品压力拍定 | 声明为设计变量，交给 `optimize_design` |
| 每次运行建出不同结构的模型 | 单元从同一目录里选，运行之间可以比较 |

## 7 实施顺序（还没有开始）

| 步骤 | 内容 | 执行 |
|---|---|---|
| P0 | 冻结当前 V3.5（4add3611），作为对照 | 主会话 |
| P1 | T0 求解器与 `flowsheet_spec` 格式；把 unitops、核算账和门控并入；用 ch4_v34_t7 的流程作回放算例 | Codex |
| P2 | T1 适配器：`thermo`/`chemicals` 物性、Cantera、IDAES 校核（只用于参考工厂） | Codex，主会话验收 |
| P3 | T2 沙箱与晋升流程；接口契约的 PASS / WARNING / BLOCK | Codex |
| P4 | 甲烷化（开发集）3 次独立运行，与 V3.4 t7 对比；通过后再上检验集 | 后台运行，监控总台 |

所有规则按单元类型和接口来写，不写入任何具体反应的知识；留出值、容差、价格表不变。

参考：CRAFTS（arXiv 2608.01369，IDAES）；From Text to Simulation（arXiv 2601.06776，Aspen Plus）；Sketch2Simulation（arXiv 2603.24629，HYSYS）；Liang 等（arXiv 2601.11650，模拟器保证物理定律）。

## 8 对照 GPT 的 V3.5 预案后的修订（2026-11-15，以本节为准）

GPT 预案：`docs/V3_5_PROGRESSIVE_WORKFLOW_CONSTRUCTION.md`（分支 `docs/v35-progressive-workflow-2026-11-15`）。

**我理解偏了的一处：** 第 3 节把手写的 model.py 换成 JSON 流程说明，由一个新写的固定求解器来算。GPT 的方案不重写求解器，也不禁止 AI 写代码：model.py 保留，但只做"组合层"，通用计算一律调用已登记的模块，新方程走实验模块。这更符合老师"不完全自由、也不完全固定"的要求，改动也小，所以采用 GPT 的做法，第 3 节的 `flowsheet_spec.json` 和新求解器暂不做。

**结合后的规则：**
1. **模块登记：** 现有 unitops、mkm_solver、design_opt 逐个登记（输入输出、单位、假设、适用范围、对应测试）。split 标为只算物料平衡，heat_recovery 标为简化估算，mkm_solver 标为单位点平均场。
2. **组合规则（本节新增，GPT 预案里没有的可执行检查）：** 每个有能耗、冷却负荷或投资的单元都要写明 `computed_by`，即由哪个登记模块或实验模块算出。没写就阻断；超出模块适用范围给警告。check_model 报告由已验证模块算出的能耗和投资占比。这样"优先用已验证模块"就不只是提示词里的一句话。
3. **实验模块：** AI 在运行目录写 `modules/<name>.py`，附自己的测试；框架再加通用检查（有限值、单位、能耗非负、重复结果一致）。没通过的阻断，通过的可以用但带警告；不自动晋升，晋升要人工批准。
4. **接口契约：** 反应器→流程、流程→TEA 两个接口在每次构建时都检查；MKM→反应器、DFT→MKM 两个接口在用到原子层时检查。判定为通过、警告、阻断。阻断时 check_model 不通过；警告必须写进报告。
5. **渐进式工作流：** 在现有阶段之上加 `workflow/rev_<n>.json` 和只追加的 `workflow_events.jsonl`。证据、界区、流程图、模型检查、接口检查、独立审查、报告是必经节点，不能跳过；其他节点可以增加、替换或跳过，但要写明理由。每次修改生成新版本，旧版本保留。
6. **离散变量和连续变量分开（采纳 GPT 对 design_opt 的意见）：** 拓扑方案由 AI 列出备选并用模块算出结果；整数变量（如压缩级数）逐个枚举；连续变量交给 optimize_design。basis 里要声明排序策略：统一设计（shared design），或参考工厂重建（reference reconstruction）。按催化剂分别优化（per-catalyst）暂未实现，选了就阻断。
7. **IDAES：** 暂不接入。等模块登记和接口契约稳定后，再作为参考工厂的独立校核工具登记进来。

**版本命名（采纳 GPT 的意见）：** 建模框架实现版本记为 `V3.6-hybrid-workflow`；路线图里程碑和模块版本（UO-1.1 等）分开记录。

**测试安排：** GPT 建议先跑基线 3 次。V3.4 已有一次有效运行（t7），按用户要求直接用 V3.6 在甲烷化（开发集）上跑 3 次，与 t7 对比。


## 9 V3.6-hybrid-workflow 实施（2026-11-15）

实现保持 STAGES、unitops、既有物理阈值、价格、留出目标和评分不变。只有 build_version 以 V3.6 开头时启用新检查；V3.6 同时继承 V3.4 的精简工具和 V3.5 的设计检查。model.py 保留为组合层。

- `registry.py` 登记 16 个可解析的模块（14 个 unitops、MKM、设计优化），提供版本、能力、输入输出单位、假设、单元字段谓词、对应既有测试和实现出处。split 只作物料分割，分离单元另须 energy_method；热回收标明简化估算；MKM 标明单位点平均场；优化标明局部有界搜索。
- `computed_by` 是单元来源声明，逐个检查 reference 和全部可用候选记录。任何非零外购能耗、冷却负荷或投资的单元缺少来源或使用未登记/未验证模块时阻断；适用域外记录 WARNING。覆盖率按实际能耗、冷却、投资分别加权；含实验来源的单元不计入已验证来源分子。该占比统计已声明且被登记识别的来源，并不替代物理检查或证明任意 glue code 的数据流。
- 实验模块使用 `modules/<name>.py`：`META.inputs`、`META.outputs` 为变量到单位的映射，`META.units` 覆盖所有输入输出名，另附 assumptions、applicability；暴露 `compute(**inputs)` 和 `tests()`。tests 执行自身断言，并返回含 conservation、limit、reference 三类的 `{kind, inputs}` 算例。框架对子进程输出检查有限值、单位键、能耗非负和重复确定性；20 s 超时；隔离工作目录、清理环境并通过 Python audit hooks 禁止网络、子进程和文件修改。它是离线实验执行隔离，不声称是运行任意敌对代码的 OS 安全边界。validation.json 绑定源码 SHA-256，源码变化即失效，通过后仍标实验模块，仅记录 promotion_candidate，不自动晋升。
- `interfaces.py` 使用类型化 Verdict，输出 PASS / WARNING / BLOCK。反应器合同要求 physics.reactor 的 `inlet_kmol_per_t` / `outlet_kmol_per_t`（物种到 kmol/t 的映射），检查元素、平衡上限、反应热符号和流程物流物种。流程到 TEA 要求 `basis.utilities.primary_efficiency`（带 value/unit/evidence 的数值叶）、balances 中来自 basis 的 capacity_t_per_y / operating_hours_per_y，以及产品 boundary stream 的 P_bar / mol_frac；投资须有 cost_year，成本指数缺少来源时警告。
- 使用原子层时，`atomic.ATOMIC` 另声明 `tof_unit`（s^-1、1/s 或 site^-1 s^-1）、site_density_evidence、dispersion_evidence、temperature_range_K、energy_reference_state、scaling_bep_source。缺少参考态/不兼容 TOF 单位阻断；位点证据、外推温区和标度来源缺失警告。原子层未启用且无 atomic.py 时不添加这两个合同。
- check_model 写 `interface_check.json` 和 `module_coverage.json`，保留逐记录结果、警告和输入指纹；任何 BLOCK 使模型检查失败。finish 检查当前指纹，并要求报告逐条包含警告原文。实验代码和 validation.json 纳入指纹。
- `workflow.py` 通过 plan_workflow(nodes) 和 revise_workflow(changes, reason) 保存 `workflow/rev_<n>.json`，只用独占创建，不覆盖历史；事件只追加到 workflow_events.jsonl。节点字段为 node_id/node_type/stage/depends_on/inputs/outputs/validation_policy/status/skip_reason；计算节点另声明 module_id/module_version 或 experimental。必经 node_type 为 evidence、basis、flowsheet、model_check、interface_check、independent_validation、report，分别唯一且不可移除/跳过。依赖无环，ready/running/validated 节点的依赖须先 validated；可选跳过理由至少 30 字符。revise 的 change 为 `{op: add, node_id, node}`、`{op: update, node_id, fields}` 或 `{op: remove, node_id, skip_reason}`；remove 保留跳过节点。finish 要求七个必经节点全为 validated，并保留原有物理、证据欠账与独立 critic 产物检查。节点状态由 Agent 通过工具更新，不取代实际检查结果。
- design_int 的整数上下界逐个枚举（最多 256 个组合，每组合最多 40 次连续评估）；design 仅交给连续优化。`optimize_design(candidate=null)` 使用默认构型；非空 candidate 须是 model.CANDIDATES 的键，其值映射固定配置 PARAMS。每个整数组合保存起点、失败点、边界命中和收敛状态；不修改 model.py / sources.csv。basis.ranking_strategy 必填 shared_design 或 reference_reconstruction；per_catalyst 明确阻断。任何局部结果均不构成全局最优证明。
- 新工具输出紧凑 JSON；workflow 工具各阶段可用，登记/验证工具在建模相关阶段可用。摘要显示最新工作流。runner 封存接口/覆盖产物、工作流修订和事件、实验验证记录；直接写入被撤销，新增伪造修订也被删除，写工具异常时仍恢复封存。

离线验收入口：`tests_v3/run_v36_acceptance.py`，顺序执行 11 个既有检查脚本及 validate_v36.py，无 API/LLM。validate_v35 的旧版夹具显式固定 V3.5，而不是跟随最新默认版本；回放直接编译读取原模型，不在原目录生成字节码。完整结果和 t7 只读副本回放分别位于 `tests_v3/v36_test_results.json`、`tests_v3/v36_t7_replay.json`。回放只测试参考工厂，不重新抽取或归一化原始记录。

A13 由 `holdout/make_prereg_a13.py` 生成，承接 A12 冻结列表并新增本次实现、测试和文档；不改写 A12 或任何既有留出 JSON。未启动开发集的三次在线运行，也未接入 IDAES。

离线验收结果：12 个脚本通过、0 个失败；V3.6 的 6 组验收全部通过。沙箱的失败测试、非有限数、负能耗、重复不确定性和缺失单位键均被拒绝；四类接口各有 PASS/WARNING/BLOCK 对照。

t7 只读副本回放：9 个非零单元缺少 computed_by；反应器到流程缺少 inlet_kmol_per_t，流程到 TEA 缺少 utilities.primary_efficiency，两类合同 BLOCK；另缺 ranking_strategy、工作流计划。已登记验证的能耗/冷却/投资份额均为 0%（来源声明覆盖统计，不是对原数值正确性的判定）。原运行文件 SHA-256 前后一致。V3.5 已有的投资指数、设计声明和备选方案问题仍由继承的规则保留。
