测试：8 通过 / 0 失败（既有回归 7/7，新增 V3.4 功能组 8/8）。
玩具工作区 workspace_digest：202.00 token（len/4），目标 <2500。

| 文件（仓库相对路径） | 新增行 | 删除行 |
|---|---:|---:|
| agent/new_reactions/auto_agent/build_mode.py | 40 | 2 |
| agent/new_reactions/auto_agent/docs/TRAIN_TEST_SPLIT.md | 1 | 0 |
| agent/new_reactions/auto_agent/docs/V34_LEAN_CHEM.md | 18 | 0 |
| agent/new_reactions/auto_agent/lean_chem.py | 247 | 0 |
| agent/new_reactions/auto_agent/runner.py | 26 | 9 |
| agent/new_reactions/auto_agent/tests_v3/v34_regression_results.json | 50 | 0 |
| agent/new_reactions/auto_agent/tests_v3/validate_v34.py | 214 | 0 |
| agent/new_reactions/auto_agent/tests_v3/V34_RESULT.md | 43 | 0 |

提交哈希：未生成。Git add 创建 `D:/论文-AI4S/Catalyst-Essay/.git/worktrees/wt-v34/index.lock` 时返回 Permission denied，尚未暂存，当前权限不能完成本地提交；未推送。
分支：analysis/v34-lean-chem-2026-11-15。

待提交信息：
```text
Implement V3.4 lean chemical-engineering build scaffolding

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
```

八项实现均已完成：读取缓存（含 force、读取区间、内容变化、遮蔽/重置/截断重读）；有长度上限的确定性摘要；批量欠账与审查回复；按流程单元生成可导入骨架；阶段工具菜单；按检查合并失败与计数/提示；默认关闭的抽取缓存；按阶段组累计且只提醒一次的软预算。

离线测试脚本：
- tests_v3/validate_unitops.py：PASS（exit_code=0）
- tests_v3/validate_v3.py：PASS（exit_code=0）
- tests_v3/validate_v33.py：PASS（exit_code=0）
- tests_v3/validate_v331.py：PASS（exit_code=0）
- tests_v3/validate_evaluation.py：PASS（exit_code=0）
- tests_v3/validate_blind.py：PASS（exit_code=0）
- physics_gate_validate.py：PASS（exit_code=0）
- tests_v3/validate_v34.py：PASS（exit_code=0）

检查证据：新增测试含实际 b_check_model 的 41 条重复失败归并、旧版输出格式保持，以及批量抽取入口缓存命中前后 token 账本相同、缓存失效键。抽取网络路径使用本地桩替换；全部验证未调用 API/LLM。runner --help 已确认 --reuse-extraction，git diff --check 通过。

开发基线（本次只读核实）：211 轮、40.95 USD；read_file 114、run_python 54、set_stage 39、resolve_debt 28、respond_critique 18、check_model 12 次；feedback 10.642、model_code 6.045、extraction 阶段 5.651 USD。尚未运行新的付费 build，也未声称实测降本。

变更边界：上表之外没有仓库变更；physics_gate.py、basis_gate.py、holdout、prices.json、evaluate_builds.py、evaluation、paper、figures 保持原内容。TRAIN_TEST_SPLIT.md 位于 auto_agent/docs/，第 6 节只新增一行。

未完成：仅本地 Git 提交（文件系统拒绝 index.lock 写入）。
