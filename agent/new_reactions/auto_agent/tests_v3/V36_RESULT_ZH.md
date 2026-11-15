12 个离线测试脚本通过，0 个失败；V3.6 新增 6/6 组验收通过。模块登记 16 项，A13 冻结 29 个文件。未执行 API/LLM 调用，未推送。

`t7` 只读副本参考工厂回放：

| V3.6 检查 | 结果 |
|---|---|
| 模块来源覆盖 | 9 个有非零能耗、冷却或投资的单元缺少 computed_by，BLOCK |
| 已登记验证覆盖率 | 外购能耗 0%，冷却负荷 0%，投资 0%；统计来源声明，不判定原数值全部错误 |
| 反应器 → 流程 | 缺 inlet_kmol_per_t，BLOCK |
| 流程 → TEA | 缺 utilities.primary_efficiency，BLOCK |
| 排序策略 | 缺 basis.ranking_strategy，BLOCK |
| 工作流 | 缺初始工作流计划，finish 拒绝 |
| 原运行保护 | 29 个原文件 SHA-256 前后一致；计算在临时副本执行 |

继承的 V3.5 规则继续指出 t7 的 9 条投资指数问题、16 条设计声明问题和 2 类备选方案记录问题。该回放只检查参考工厂，没有重新抽取、归一化或在线运行候选催化剂。

文件行数（总行数）：

| 文件（相对 auto_agent） | 行数 |
|---|---:|
| `build_mode.py` | 1133 |
| `runner.py` | 808 |
| `lean_chem.py` | 275 |
| `design_opt.py` | 255 |
| `registry.py` | 284 |
| `interfaces.py` | 133 |
| `workflow.py` | 134 |
| `tests_v3/validate_v35.py` | 164 |
| `tests_v3/validate_v36.py` | 302 |
| `tests_v3/run_v36_acceptance.py` | 43 |
| `docs/V36_HYBRID_HARNESS.md` | 120 |
| `docs/TRAIN_TEST_SPLIT.md` | 124 |
| `holdout/make_prereg_a13.py` | 27 |
| `holdout/PREREG_V31_A13.json` | 39 |
| `tests_v3/v36_test_results.json` | 102 |
| `tests_v3/v36_t7_replay.json` | 379 |
| `tests_v3/V36_RESULT_ZH.md` | 47 |

提交哈希：**未生成**。当前分支仍为 `analysis/v34-lean-chem-2026-11-15`，HEAD 仍是 `5af3ca048809a46fb5e73e16dfde6c36fe2279d2`。提交时创建 `D:/论文-AI4S/Catalyst-Essay/.git/worktrees/wt-v34/index.lock` 被操作系统拒绝；该目录对当前沙箱主体有显式 Deny Write。没有现存锁；当前会话禁止提权，未修改 ACL、未绕过权限，也未更新分支引用。

完整补丁：`C:\Users\ASUS\AppData\Local\Temp\v36-delivery\v36-hybrid-workflow.patch`。提交信息：`C:\Users\ASUS\AppData\Local\Temp\v36-delivery\commit-message.txt`，末尾已包含用户指定的 `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`。补丁包含本报告及本次实现的全部文件。

完成内容：模块登记和适用域检查、逐记录来源覆盖、绑定源码哈希的实验模块验证、四类类型化接口、报告警告核对、不可覆盖的工作流修订和只追加事件、整数枚举与连续优化分离、候选配置和排序策略、工具菜单与摘要、A13 预注册冻结、离线测试及 t7 回放。既有 holdout JSON、prices、evaluate_builds、evaluation、paper、figures、unitops 和 physics_gate 均未发生最终内容变更。

未完成：本地 Git 提交（权限阻断）。三次在线开发集运行不在本次离线任务范围内，遵守本次禁止 API/LLM 的要求而未启动。per_catalyst 按设计明确拒绝，未实现该策略。

复核证据：`v36_test_results.json` 保存全部脚本退出码及 stdout/stderr；`v36_t7_replay.json` 保存逐项失败和原文件哈希；`holdout/PREREG_V31_A13.json` 的 29 项冻结哈希全部复核相符。
