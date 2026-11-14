# V3.4-lean-chem（2026-11-15）

目标是减少重复读取、工具往返和建模起草成本，保留 V3.3.1 的科学检查。新建 build 默认写入 `V3.4-lean-chem`；已有工作区仍按 `build_version.json` 使用旧行为。以下均为通用工具和按单元类型的工程脚手架，不新增反应专用知识。

开发依据：只读取 `D:\agent_runs\ch4_v33_t3\trace.jsonl`、`stage_ledger.csv` 与 `ledger.json`。共 **211 轮、40.95 USD**；费用为原账本的 gpt-5.5 标价等价。read_file 114 次、run_python 54 次、set_stage 39 次、resolve_debt 28 次、respond_critique 18 次、check_model 12 次。feedback 10.642 USD、model_code 6.045 USD、extraction 阶段 5.651 USD。下面的改动没有进行新的付费运行，不能据此声称已经节省了多少费用。

| 改动 | 实现与开发依据 |
|---|---|
| 1 读取缓存 | 同路径、同读取区间、内容 SHA256 未变且先前输出仍可见时，仅返回首次读取轮数和 SHA；`force=true` 重读。不同区间继续返回内容；旧输出被遮蔽、截断或阶段重置移除后重读内容。对应 114 次 read_file。 |
| 2 workspace_digest | 确定性汇总 basis、单元及边界角色、最后检查失败、两张账前几行、未决欠账和审查意见、阶段笔记；各部分有长度上限，提示词指定用其恢复上下文。对应 114 次读取及 39 次阶段切换。 |
| 3 批量处理 | resolve_debts、respond_critiques 按顺序调用原单项处理器，返回单项结果数组；拒绝规则与状态写入保持原样。对应 28 次欠账处理、18 次审查回复及 feedback 10.642 USD。 |
| 4 流程骨架 | submit_flowsheet 通过后生成可导入的 model_skeleton.py；每单元一个函数，按类型调用 unitops，checklist 映射边界角色，预填能耗/投资字段，数值和来源保留 TODO/None。骨架可编辑或忽略，再提交会重新生成。对应 54 次 run_python、model_code 6.045 USD。 |
| 5 分阶段工具 | 始终保留读写、切阶段、finish、digest；文献阶段只开放文献操作，参数/机理和流程阶段可查来源，模型阶段不传搜索 schema，反馈和分析各有其工具。按请求时的阶段选择菜单。对应 211 轮及 39 次阶段切换。 |
| 6 检查诊断 | 不改门控；V3.4 将相同失败去除记录标签后按检查分组，只展示一次并附记录计数和通用修复提示，完整结果保存在 model_check.json。对应 12 次 check_model。 |
| 7 可选抽取缓存 | `runner.py ... --reuse-extraction` 才启用；默认关闭。缓存位于 `D:\agent_runs\_extraction_cache\`，键包含 PDF SHA256、渲染后的抽取提示（含 schema、OCR 和所选图片散列）SHA256、抽取模型。命中直接写 extracted、记录 extraction_cache_hit，当前账本增量为零；缺 PDF 时走原抽取。启用后延迟抽取路由探测，避免命中前探测费用。对应每 build 约 6 USD 的 extraction 阶段及重复文献抽取。 |
| 8 阶段软预算 | 文献含机理 40、流程 15、参数 25、模型含检查/原子模型 40、反馈 20、分析含报告 25 轮；同组阶段往返累计，达到预算只提醒一次收尾，不强停。对应 211 轮、feedback 10.642 USD、model_code 6.045 USD。 |

离线验收：`tests_v3/validate_v34.py` 覆盖上述八项；其余七个指定回归脚本照常运行。玩具工作区 digest 按 `len/4` 计为 202 token。门控阈值、basis 检查、价格、留出目标、评估评分与论文图件未修改。

## 主会话补充（依据 agy 对 ch4_v33_t3 轨迹的审计）

- model.py 每次改动（write_file 或补丁脚本）后，框架自动导入并运行 reference()，报错立即返回。V3.3 有 3 次 NameError 链，耗了 10 轮才由 check_model 发现。
- Critic 只报会改变数字的工程问题（衡算、热力学、各类负荷、公用工程、投资依据、界区）。V3.3 的 18 条意见里有 11 条是措辞和格式问题。
- 提示词要求只在阶段变化时调用 set_stage（V3.3 有 8 次原地重复），改 model.py 时整段重写函数，不要按变量名做子串替换。
- 修正：启动时照常探测抽取路由；Codex 原实现里开缓存时跳过探测，缓存未命中会无路由可用。
- 冻结：`holdout/PREREG_V31_A11.json`。
