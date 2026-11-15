# V3.5 确定性设计优化

V3.5 继承 V3.4 的缓存、摘要、模型骨架、阶段菜单和既有物理门控。自由设计参数写入 sources.csv：type=design，给出 value、low、high、unit、note，并由模型 PARAMS 在调用时读取。压力、温度、回收率、吹扫或分流类 assumption 必须在 note 用至少 40 字符说明工艺固定原因。

model_checks 后调用 optimize_design。工具在独立子进程中以参考成本为目标，用有界 L-BFGS-B 和当前值及逐变量 low/mid/high 的确定性起点搜索；总计最多 40 次实际候选评估。每点运行带 basis、ledger=True、design=True 的物理检查，失败点不参与最优值选择。输出 design_opt.json：初始值、最优值、成本、能耗、投资、评估数、失败点、触界变量；无可行点时明确报告。此为预算内找到的可行最优候选。工具不编辑输入；代理采用结果后编辑 sources.csv 并重跑 check_model，或记录不采用的原因。摘要展示变量和上次优化；工具返回压缩摘要，完整结果保留在文件中。

separation 决策至少比较两项：name、由 unitops 算出的 energy_GJ_per_t、capex_usd、chosen，恰有一项 chosen=true。reactor 提供备选列表时执行同样检查；新决策替代同主题旧决策。门控验证这些数值字段，计算依据由代理的脚本及决策证据保留。

仅 V3.5 新增：整厂投资份额的 scale_exponent 应在 [0.5,0.95]，超出须有 measured/published 的 exponent_evidence，并复用 basis_gate.evidence 验证来源；产品压缩机出口不得超过 basis.product[物种].P_bar 的 102%。多产品可用单元 product_species 指定对应产品。提示建议无来源时用 0.6–0.9。

离线测试：tests_v3/validate_v35.py，含实际子进程优化、解析最优值、边界、物理失败点、check_model、证据及只读 t7 回放。开发记录 t7 原始 basis 明确为 40 bar，产品压缩机也是 40 bar，故不触发超压检查；另用 20 bar 基准负例验证拒绝。没有改写原运行或科学数据。
