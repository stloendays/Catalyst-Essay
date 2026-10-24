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

## 待定决定（收尾时按此执行，用户可推翻）
- **D 的写法**：描述符口径 12/44 保留为主数（整个氨模型都在描述符框架里，且实测方程覆盖不了实验点：237 条中 167 条在所有实测方程的拟合范围外）。
  正文把"描述符动力学不够"一句限定为 Fe 与 Ru/C 在工厂压力下的比较（两条实测方程都在拟合范围内），并说明文献比较为何用描述符；
  实测方程口径（4/25；各变体 2–6 组）与机理（单点标定的外推、文献熔铁参比只有商业活性的 0.5–6 %）放 SI 新 Note。
  摘要中氨计数是否保留，取决于正文压缩后是否还有空间；倾向保留并在正文给出口径。

## 需要用户的事项（不阻塞）
- Keestra, Rouwenhorst & Brilman 2025（CEJ 10.1016/j.cej.2025.168541，CC BY，Ru 通用动力学模型）：ScienceDirect 与 UTwente 均有人机验证，需用户用 nus-fetch 菜单 7/8 手动下载。到手后可作为 D 的第三条 Ru 方程，并核实正文"多数实验速率在实测方程拟合范围外"一句。

## 进度日志
- 2026-10-22 20:10 建分支与回溯标签；Keestra Ru 论文下载受人机验证阻挡（待用户手动），Cholewa 2024 已下载。
- 2026-10-22 22:00 D 完成：`analysis/nh3_field_measured_kinetics_2026_10_22`（README 有全部数字）。Cholewa 2024 式 (12) 按原文参数复现不了自身 Fig. 5b（1.21 vs >1.8），主选 Ru 方程改为 Rossetti（Addendum 1）。描述符 12/44 → 实测方程 4/25；98/237 条外推后放不进 90 m³ 床。标签 rollback/AD-D-done。
- 2026-10-22 20:30 A+B 完成：`analysis/nh3_final_1_3_2026_10_22`。BASF 表 VLE 过留出检验（−6.2 %、−3.3 %），多级压缩仍低 38–46 %（门槛未过，不拟合）→ 1.3 作结构性稳健性检查，1.2 仍为主模型。结论全部保持（Fe<Ru<Os，差 5.17；Ru/C 盈亏 3.24/4.84 %/y 仍高于 2.10 % 参考利率）。标签 rollback/AD-AB-done。
- 2026-10-22 20:40 正文/SI 第一轮：Note 4 加"动力学口径"段（D），Note 7 加 1.3 段与两行表，Methods 加两句检查；新文献 61（Appl 氨 1 表 5）、67（Cholewa 2024）并重排编号；审计加 D 与 1.3 锁，352/0；正文 3,493 词，SI 9,993。C 的加料口径重算仍在跑（`analysis/meoh_catalyst_level_co_rule_2026_10_22/run.log`）。
- 2026-10-22 21:00 核对：SI「熔铁参比只有商业活性 0.5–6 %」一句只对 450–459 °C、1 MPa 的三条成立，已改为分温度表述（300–340 °C 为 27–126 %）并加审计锁；正文氨口径句改为可由本仓库数据核实的说法。C 加料口径用 6 个进程重跑 high/equal_X/family。
- 2026-10-22 21:40 C 完成：`analysis/meoh_catalyst_level_co_rule_2026_10_22`。加料口径 central 21/63（正文）、equal_X 27、high 28、Cu 家族 26；实验室转化率 26/31/28/28。正文所用规则给出最小计数。标签 rollback/AD-C-done。
- 2026-10-22 21:55 收尾：正文 3,496 词、摘要 141、SI 9,986；审计 357/0；Word/PDF `work/build_2026-10-22_AD`（正文 46 页、SI 67 页，改动页已渲染目检）。草稿 PR #120（base = manuscript/nce-compact-2026-10-21）。A–D 全部完成；E（选择性–转化率包络）不在本轮范围。
- 2026-10-23 用户决定：D 只留在仓库（`analysis/nh3_field_measured_kinetics_2026_10_22`），不进论文。已从正文（Results 一句、Methods 一句）、SI Note 4、审计中移除；Cholewa 文献随之删除，Kitano 改回 67。A、B、C 保留。审计 352/0，正文 3,473 词，SI 9,784；Word/PDF `work/build_2026-10-23_ABC`（46 + 66 页，改动页已目检）。
- 2026-10-23 11:30 E 完成：`analysis/meoh_selectivity_conversion_2026_10_23`。同一催化剂多空速数据 23 组/9 篇，21 组甲醇选择性随转化率下降（中位斜率 −0.93）。加料口径下让选择性随转化率变化：趋向平衡分配 23/63，中位斜率 18，四分位 22/20；>5% 为 8–10；恒定选择性 21/63 复现。正文加半句，SI Note 3 加两句，审计 355/0。
- 2026-10-23 Data/Code availability 两节写入（Methods 之后、参考文献之前），指向公开仓库 catalyst-rankings-process-economics；版本写作 v2.0、Zenodo DOI 留占位。审计加 2 项，357/0。参考文献 67 篇（正文 56、仅 Methods 10、仅图注 1），NCE 指南为"建议不超过 50"，未删减。
- 待办：公开仓库仍停在 v1.1（10-12），缺 ED 9–10 Source Data 及之后的全部分析；投稿前需发布 v2.0 并取得 Zenodo DOI，再替换占位。
- 2026-10-23 PR #120 合入 manuscript/nce-compact-2026-10-21（c7d88c2）；合并前修了两项早已存在的 CI 失败（Word 构建缺 latex2mathml；Fig. 3 渲染清单在 10-21 换色后未重算哈希）。审计 357/0。
- 2026-10-23 全部图（主图 6 + ED 10）整合为一个 PPTX：work/figures_pptx_2026-10-23/Figures_NCE_2026-10-23.pptx，一图一页、1:1 尺寸，按 SVG 里的分图字母把每个分图切成独立透明底图片放回原位，可单独拖动（脚本 tools/make_figures_pptx.py）。
- 2026-10-23 Fig. 1a、Fig. 3a 可编辑 PPTX：work/editable_panels_2026-10-23/（tools/svg_panel_to_pptx.py 由 SVG 转换，文字为文本框、线框为自由形状、结构渲染为图片）。
- 2026-10-23 14:00 按用户 PPT 批注改图（d88f0f3；回溯标签 rollback/pre-figure-edits-2026-10-23）。Fig. 1a、Fig. 3a 改为用户新流程图（figures/composite/fig1/Fig1a.pptx、fig4/Fig3a.pptx，600 dpi 导出后放回原位）；Fig. 1f、3e 加两条排名轴、3e 文字外移；3c 组标题居中、表底加线；Fig. 2a 原子渲染图层盖住放大线；2b、2c 点线加粗，2c 图例左侧加竖线；2d–f 点重画、标注移出数据区。Fig. 2a 计数 90 = 50 + 40、52 = 30 + 22 核对无误。图注不变；审计 357/0。Word/PDF work/build_2026-10-23_figs（47 页，图页已目检）；图集 PPTX 已按新图重生成（用户改过的旧版存为 *_before-markup.pptx，另有 work/user_edits_2026-10-23_1326 快照）。
- 2026-10-23 Fig. 2b 改为横向森林图（d9bb421）：左侧类别与计数一列，横轴为百分比，图例移到标题下一行；数值与图注不变，审计 357/0。稿件 work/build_2026-10-23_figs/Manuscript_NCE_2026-10-23_fig2b.pdf；图集 PPTX 已重生成。
- 2026-10-23 拖动调图工具：tools/figure_tweak.py（双击 tools/figure_tweak.cmd 输入正文图号 1–6）。浏览器里拖文字、箭头标注、图例、坐标轴标题，滚轮改点的大小（点的位置是数据，不能拖）；保存后写入各图文件夹的 <stem>.tweaks.json，并自动重跑作图脚本。figures/composite/tweak.py 在每次出图前读取并套用这些调整，同时给每个对象打上固定 SVG 编号（<stem>.tweak_keys.json）。没有调整文件时 PNG 与之前逐字节相同（Fig 1–6 已验证）。调研过 pylustrator（Qt 窗口、按序号写回代码、GPL）、FigureFirst（只管 Inkscape 里的坐标轴布局）、SVG-Edit（改 SVG 但回不到脚本），都不能把调整稳定写回脚本，因此自建。
- 2026-10-23 调图工具扩展（用户要求）：可整块移动/缩放图表（分图字母和标题不跟着动）、刻度/类别标签整列移动与逐项改字、所有文字改字与改字号、图例改字与字号；右侧按类型勾选可选中的部分，数值框精确输入；页面内切换正文 Fig. 1–6 与 Extended Data Fig. 1–10。无调整文件时 PNG 与提交版逐像素一致（正文 6 张逐字节一致，ED 10 张像素差 0）。
- 2026-10-23 编辑器第三版（用户要求，仿 BioRender）：左侧图层树（按分图分组，可显隐）、右侧属性面板；改颜色（单个对象按“旧色→新色”替换，保留颜色编码；全图配色一键替换）、线宽、透明度、粗体/斜体、图表与画布背景；箭头标注的引线在拖动标签时实时跟随、出图后一端仍钉在数据点；工作区改为白底。tweak_keys.json 记录重跑命令，编辑器自动发现 figures/ 下所有图。figure-studio 技能已同步（assets/tweak.py、figure_tweak.py/.html，Page.save 接入，SKILL.md 新增“图必须可编辑”规则），以后生成的图自动接入。用户在 Fig. 2 保存的 9 处调整已保留并提交。
- 2026-10-24 编辑器 v4（用户要求）：修复多行文字改成一行时预览残留第二行的错误，加“合为一行”；文字/刻度/图例加粗，文字左中右对齐、旋转（±90° 一键），居中于所在图表；图表边框线宽单独可调（不影响数据线）、图表内部背景色与不透明度；插入新文字（存为 fig/added/<id>）；多选（Shift）后对齐/等距分布、批量字号与加粗；拖动时吸附参考线（Alt 关闭）；重叠检查；出图日志提示失效调整。用户正在编辑的 Fig. 1–3 调整文件未改动、未提交。
- 2026-10-24 编辑器 v5（用户要求）：插入箭头/线/引线、显著性括号（* ** *** n.s.）、圆角框，均可拖动、拖端点、改色、改线宽线型、箭头样式；格式刷（字号、粗细、颜色、线宽）；全稿一致性检查（分图字母、标题、坐标轴标题、刻度、图例，按字号与粗细找出与主流不同的项，可一键统一并重出相关图）；界面按论文配色改为白底深色字、清晰分隔线、14 px 字号。保留另一会话加入的多 root（QoI 补充图）。当前检查结果：分图字母 70 处一致；标题 6、坐标轴标题 1、刻度 15、图例 14 处不一致（未改，待用户决定）。
- 2026-10-24 按用户要求统一全稿字号：标题 7 pt（6 处）、坐标轴标题 7 pt（1 处）、刻度/类别 6.5 pt（15 处）、图例 5.3 pt（14 处），共 36 处，涉及 15 张图（写入各图 tweaks.json 的 size）。ED Fig. 3e 类别标签变大后相邻两项相接，改为三行排列（文字不变）。复查：上述四类全部一致（标题类剩 1 处仅粗细不同：Fig. 3d 副标题常规体）。审计 357/0；稿件 work/build_2026-10-24_fonts（47 页）。用户正在改的 Fig. 1、4、6 文件夹未提交。
- 2026-10-24 内部预审四条 + 两处图（用户：结果不利就不做）。
  - 3 三床 Ru/C 上限 500/530 °C（analysis/nh3_staged_ru_tmax_2026_10_24）：全 Ru/C 在 1.37 / 3.10 %/y 以下最优，Fe 在前到 6.00 %/y，6 %/y 以下 Ru 在前始终贵 0.06–0.25 USD/t，从不最优 → 正文、SI Note 7、Methods 写入，SI 原句"因 460 °C 上限"删去；审计加锁。
  - 1 氨 12/44 压力限制在实测压力附近（analysis/nh3_field_pressure_window_2026_10_24）：可比组 44 → 4–30，比例 20–30 %，不支持"保守数" → 只留仓库。
  - 2 甲醇 63 组（analysis/meoh_catalyst_level_robustness_2026_10_24）：加料口径重测平均 21.2（17–26），>5 % 的 10 组 8 组 ≥90 % 保持；工厂首选更选择性 17/21、>5 % 的 10/10 → 正文替换 42/50、40/50（81 口径移到 SI）。C3 惰性稀释写进速率（analysis/meoh_catalyst_level_c3_dilution_2026_10_24）：8→9–10/63、16→15–16/63，不利 → 只留仓库。
  - 4 "16 倍"口径：第 8 节改为"体相、无回收需 16 倍；负载并回收已比熔铁便宜"。
  - Fig. 1h 标题补 "#3"（用户 Fig1.tweaks.json 一处文字，未提交）；Fig. 2b "laboratory X" → "laboratory conversion"（两行）。
  - 正文 3,500 词内、SI 10,000 词内；审计 361/0；稿件 work/build_2026-10-24_review（47 + 67 页，改动页已目检）。
- 2026-10-24 修复编辑器预览错误（v5 引入）：预览时清空了 matplotlib 自带的 text-anchor 与粗细，右对齐/居中的文字在编辑器里错位、粗体显示成常规。真实出图一直正确，但用户在错误预览下为“对齐”所做的拖动（Fig. 2b 计数、2c 纵轴标题、2d–f 纵轴刻度列，Fig. 3c 三个表头）让真实图偏了。已按每段文字的实测宽度把这部分补偿量加回（刻度列直接归零），保留用户看到的位置与其余有意调整。修改前的调整文件备份在会话临时目录。
- 2026-10-24 ED Fig. 3 加分图 f（用户要求）：63 组催化剂口径的重测保持比例，加料与实验室转化率两种口径，>5 % 组加点；页面 183 × 244 mm，原 a–e 上移，tweaks 键随之迁移；图注（短/详）与 Source Data 更新；审计加锁 362/0。
- 2026-10-24 编辑器 v6（用户要求）：线型（实线/虚线/点线/点划线/无，虚线段长与间距）、线上标记（形状、大小、描边、空心）；热图/等高线/彩色散点的配色方案（含论文配色 4 种与常用 16 种，可反转）与色标范围，色条跟随所属图表移动并保留原刻度文字；叠加层模式：外部 SVG/PNG（Origin、R 等）上加文字、箭头、括号、框，导出 <stem>_annotated.svg/png(600 dpi)/pdf，原文件不改。以技能版编辑器为基础（含另一会话的同名图区分、无窗口运行），两份保持一致。
- 2026-10-24 晚 逻辑一致性复查：用户 15:13 后的图调整入稿；第 1 节标题、Ru/C 一节描述符句、0.204/4.09 状态、90/50 篇、Fig. 6a Cs–Ru/YSZ（文献 68）、ED Fig. 10 回路阴影口径（CO+CH₄+N₂ 4.40–9.85%）；Fig. 3 README 的 ρ 最大值改为 0.80。审计 363/0；稿件 work/build_2026-10-24_logic（48 + 67 页）。未提交。
- 2026-10-24 晚 参考文献 68 → 正文 57（删 Bruix 2019、Ramos 2025、Yoshida 2024、Zimmermann 2020、Smith 2020；Jadhav、Valden、Nestler 2022、Azar、Nishi、Mace–Vrabec 改为只在 SI 引用，留在文献池中排在正文之后）；renumber 工具与审计支持 SI-only 文献；ED Fig. 5 图注 ref. 31 → 26。Fig. 5b 图注与 SI Note 7 补全 Ru/C 与全 Fe 打平 2.46 %/y（500/530 °C：4.32/4.96，夹住 KAAP 型 4.57）。审计 368/0；稿件 work/build_2026-10-24_refs（46 + 67 页）。
