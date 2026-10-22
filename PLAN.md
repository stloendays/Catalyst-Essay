# PLAN — 审稿意见 A–D 修复与稿件回到顶刊水平（2026-10-22 起）

主线：把内部预审的四个模型问题（A 分离器 VLE、B 压缩功、C 循环 CO、D 氨文献动力学）修掉，
数字冻结后把正文与 SI 更新到同样流畅的 NCE 稿。进度看 Claude 任务列表；本文件记录决定、回溯点和结果。

## 回溯点（出意外时从这里恢复）

| 标签 / 分支 | 指向 | 含义 |
|---|---|---|
| `rollback/pre-AD-2026-10-22` | 728af84 | A–D 开始前的 NCE 稿（Ru/C 主线、读者落点已在）。正文/SI/审计全过 345/0。 |
| 分支 `revision/a-d-2026-10-22`（worktree `D:\论文-AI4S\wt-ad22`） | 本工作线 | 所有 A–D 改动只在这里；`manuscript/nce-compact-2026-10-21` 不动。 |
| `rollback/AD-D-done` 等 | 每项完成时打 | 每项分析冻结后打一个标签，正文改动前再打一个 `rollback/AD-pre-text`。 |

规则：
- NH3-FINAL-1.2、MEOH 冻结输出、`provenance/` 一律不改；新模型叫 NH3-FINAL-1.3，由 `NH3_MODEL=1.3` 选择。
- 每项先写 `PREREGISTRATION.md`（判据、报告量；结果不论方向都报）并提交，再跑。
- 正文只在全部数字冻结后改；改完审计 0 失败、Word/PDF 渲染目检，才推送。
- 本机只剩约 3.5 GB 空闲内存：并行 ≤ 2 进程；长任务用后台运行并在本文件记日志路径。
- 额度用尽：停在一个已提交的状态，在下面「进度日志」写清下一步；恢复后从日志继续。

## 工作项

### D 氨文献比较改用实测速率方程（最高优先）
- 现状：`analysis/nh3_field_expansion_2026_10_12/nh3_1_2/runs/pooled_vf_screen`，44 组 / 237 条（Ru 183、Co 29、Fe 19、Ni 6），
  实验压力中位 1 MPa（0.1–15 MPa）。12 个反转中 8 个跨金属（3 不同金属、5 熔铁参比）。映射在
  `analysis/nh3_supported_2026_10_06/run_supported_chain.py`（实测速率 → 有效描述符 → 14,510 态）。
- 速率方程：
  - Fe：Keestra 2025 Model 3（1–324 bar），已实现 `analysis/nh3_fe_inrange_kinetics_2026_10_19/keestra_fe.py`；
    每个 Fe 条目单点拟合 b_cat（熔铁参比按商业熔铁）。
  - Ru：主选 Cholewa et al. 2024（Sustain. Energy Fuels 8, 2245，CC BY，Ru/CeO₂ 扩展 Temkin 式 (12)，10–80 bar，
    350–450 °C；PDF 已在 `literature/ru_kinetics_2026-10-22/`）；敏感性 Rossetti 2006（50–100 bar，正文 Ru/C 所用）。
    待补：Keestra, Rouwenhorst & Brilman 2025 "Universal kinetic model … ruthenium-based catalysts"
    (CEJ, 10.1016/j.cej.2025.168541，CC BY)——ScienceDirect 与 UTwente 均有人机验证，需用户手动下载（nus-fetch 菜单 7/8）。
  - Co、Ni：无实测方程，保持描述符口径；含 Co/Ni 的组另报"剔除 Co/Ni 条目"的变体。
- 做法：每条目在实验条件下单点标定活性因子（精确复现实测速率）；工厂端只在该方程拟合压力范围内优化；
  实验压力在拟合范围外的条目单独标记并报"剔除后"的计数。
- 报告：描述符口径 vs 实测方程口径的反转数 / >5% 数 / bootstrap CI；按类别（同金属、跨金属、熔铁参比）拆分。
- 输出：`analysis/nh3_field_measured_kinetics_2026_10_22/`。

### C 甲醇 63 组 × 循环 CO 规则
- 在 `analysis/meoh_catalyst_level_2026_10_19` 的代码路径上加 x_CO ∈ {central, equal_X, high}，覆盖加料/实验室转化率、
  无上限与 4/5/6.86/8/10% 上限；再加家族规则（Cu 基 high，氧化物 central；规则先冻结）。
- 已有基础：`analysis/meoh_co_conversion_bound_2026_10_13`（40 组：28/29/27）。
- 输出：`analysis/meoh_catalyst_level_co_rule_2026_10_22/`。

### A+B NH3-FINAL-1.3：分离器 VLE、惰性气体与弛放、压缩功
- 现状：`provenance/nh3_final_1_2/source_harness/harness_core.py:418–436`：`ysep = psat/P`（纯液氨理想 Raoult），
  回路无惰性气体；新鲜气 298 K 等温功 ÷ 0.75（30 bar 起），循环固定 3 bar。对标：入口 NH₃ −63%、分离器气相 −40%、
  压缩功 −36 至 −77%。`analysis/nh3_pr_vle_compression_v0`：PR（k_ij=0 或 Binous 2022）2/28、6/28，偏高，未过门槛。
- 做法：
  1. VLE：γ–φ（液相 H₂、N₂ 亨利常数 Mace & Vrabec 2024；气相 PR）或经典实测关联式；
     门槛沿用 v0 预设：BASF Table 5 ≥ 24/28 在 ±20%，Uhde gas5/gas6 均过；这些点只检验不拟合。
  2. 回路惰性气体（CH₄+Ar，新鲜气含量取出处值）+ 以入口惰性上限决定的弛放。
  3. 压缩：多级多变、级间冷却 40 °C、PR 压缩因子、循环压降 9.2 bar（Krupp–Uhde 出处）；门槛 E01–E03 ±30%，不拟合。
- 1.3 作为新 run 落在新 harness 副本（`provenance/nh3_final_1_3/`），`analysis/nh3_model.py` 增加 1.3 选择；1.2 原样保留。
- 连锁重跑：15 金属确定性 + MC + 反向设计、64 项对标与扰动、Ru/C 实测方程与融资盈亏点、KAAP、三床转化器、合金、D 的文献比较。

### 收尾：正文与 SI
- 新数字进正文与 SI、Source Data、审计脚本（`tools/audit_live_manuscript_truth.py`）；1.2 数字作为旧版保留在 provenance。
- 行文按当前 NCE 稿的标准恢复：正文 ≤ 3,500 词、摘要 ≤ 150、Ru/C 主线、读者落点；SI 增加 D、C、A+B 的 Note/表。
- 构建 Word/PDF（`tools/build_manuscript_docx.py`、`tools/build_si_docx.py`），渲染目检；开草稿 PR。

## 进度日志
- 2026-10-22 20:10 建分支与回溯标签；Keestra Ru 论文下载受人机验证阻挡（待用户手动），Cholewa 2024 已下载。
