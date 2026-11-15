# V3.5-design-opt 结果

11 个测试脚本通过，0 个失败；V3.5 新测试 6/6 组通过。已知最优压力 5，优化得到 4.99999972，相对误差约 0.000006%，共 26 次评估（上限 40）。边界、触界变量、物理失败点排除、全不可行状态、输入不变、重复结果一致、39/40 字符边界均通过。

t7 原始回放：旧物理门控 0 项失败；V3.5 新物理门控 9 项失败（9 个单元的整厂投资指数均为 1.0，缺少指数来源）；16 个 assumption 参数缺少 design 标记或至少 40 字符的 note；2 项决策不合格（separation、reactor 的备选只有文字，缺少计算值和 chosen）。

t7 参考成本 2027.315431554476 USD/t，能耗 5.494499813917254 GJ/t，投资 124826388.8888889 USD。循环压缩机能耗账为 2.7452963041631153 GJ/t。

产品压缩检查：t7 原始 basis.product.CH4.P_bar=40 bar，产品压缩机出口也是 40 bar，因此实际回放没有超压失败。任务中“basis 更低”的预期与原文件不同。将独立负例的 basis 改为 20 bar 后，原压缩机被正确拒绝；原运行保持不变，并逐文件核对 SHA-256。

逐文件新增/删除行数（相对当前 HEAD；路径相对 auto_agent）：

| 文件 | 新增 | 删除 |
|---|---:|---:|
| `build_mode.py` | +19 | -3 |
| `docs/TRAIN_TEST_SPLIT.md` | +1 | -0 |
| `lean_chem.py` | +12 | -2 |
| `physics_gate.py` | +32 | -1 |
| `runner.py` | +6 | -3 |
| `tests_v3/validate_v3.py` | +1 | -0 |
| `tests_v3/validate_v34.py` | +1 | -1 |
| `design_opt.py` | +185 | -0 |
| `docs/V35_DESIGN_OPT.md` | +11 | -0 |
| `tests_v3/validate_v35.py` | +163 | -0 |
| `tests_v3/v35_existing_results.json` | +57 | -0 |
| `tests_v3/v35_t7_replay.json` | +48 | -0 |
| `tests_v3/V35_RESULT.md` | +43 | -0 |

提交哈希：未生成。git add 无法创建 `D:/论文-AI4S/Catalyst-Essay/.git/worktrees/wt-v34/index.lock`，报 Permission denied。已核对目录 ACL：当前沙箱身份有显式 Deny Write，且不存在遗留 index.lock。当前环境禁止提权；未改动权限或绕过限制。

待提交信息（末行符合任务要求）：

```text
Build V3.5 deterministic design optimisation and computed separation alternatives

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
```

实现包括 design 声明及 gate、独立子进程有界多起点优化、压缩结果、设计变量摘要、计算型方案决策、指数证据和产品压力检查、V3.5 通用提示及模型阶段工具。旧版物理检查和阈值未改。旧版回归固定到其原版本；模型导入检查用当前 Python 直接运行，避免依赖 bash。

测试使用 `D:/Research/CatalystForge/.venv/Scripts/python.exe`，PYTHONUTF8=1；无 API/LLM 调用。完整输出见 `v35_existing_results.json`；只读回放及来源哈希见 `v35_t7_replay.json`。

未完成：本地 Git 提交，原因是上述沙箱目录写入拒绝。没有推送。未实现 t7 模型重设计或新建在线构建（任务只要求回放）；实现没有修改 holdout、prices、评分逻辑、evaluation、paper、figures。现有未跟踪 `evaluation/ch4_v34_test/` 未加入提交范围。
