# UO-2.0 单元库与 IDAES 复核

新增 **25 个计算方法 + 1 个 T1 复核工具**，共 42 个注册能力。通过 `from unitops import ...` 使用，旧函数保留原签名和行为；`describe_module` 提供输入、输出、来源和适用域。

默认物料基准为 **kmol/t 产品**、热量 **GJ/t**、温度 **K**、压力 **bar 绝压**。PFR/CSTR 的流量与速率明确采用 **kmol/h、kmol/(m³·h)**，结果为 GJ/h；换热面积和夹点使用 **kW**。将小时或功率基准接入产品账本时，调用方必须按自己的生产率换算。所有结果含 `computed_by`、`applicability` 和基础账本字段；工艺热负荷与实际购买能源分开，需组合 `fired_heater`、`cooling_utility` 等供能模块。

| 方法 | 算法与来源 | 适用域 | 离线验证 |
|---|---|---|---|
| `cp_mix`, `enthalpy_stream` | 复用 gate 的 NIST Shomate/常 Cp 数据 | 理想气体，沿用原温度范围 | Ar Cp、N₂ 焓升 |
| `antoine_psat`, `vapor_pressure` | NIST SRD69 Antoine；CO₂ 液相 Lee–Kesler | 表内温度；拒绝固相及外推 | 水/甲醇蒸气压、5 种正常沸点、CO₂ 293 K |
| `flash_pt` | Rachford–Rice、Raoult；永久气体不溶或调用方给定 Henry H=p/x | 推荐 ≤10 bar；极性混合液默认标出非理想风险 | 三组分 RR β=0.690730、两相守恒、单相极限 |
| `dew_point`, `water_knockout` | 露点方程；闪蒸 + CRC 潜热 + 冷却公用工程 | 与闪蒸相同；常潜热为初估 | 水露点、冷凝量/负荷 |
| `equilibrium_reactor` | 多反应受限 Gibbs 最小化，NIST H/S | 独立、元素守恒反应；理想气体；高压有标记 | 氨平衡、双反应化学势残差 |
| `adiabatic_temperature_rise`, `staged_cooled_reactor` | Fogler，第 11 章，积分焓平衡；平衡/指定转化 + 温升上限 | 放热绝热床、床间回冷；需可括根的温度区间 | Tad=527.242 K、分床温升和冷却 |
| `pfr_isothermal`, `cstr` | Fogler，第 4 章，SciPy ODE/稳态余额 | 调用方提供速率律、固定温压和容积 | 一级反应解析解 |
| `catalyst_inventory`, `ergun_pressure_drop` | 生产率/速率/平均活性；Ergun 1952 | 活性为周期平均值；均匀球形填料近似 | 1000 kg、24.84375 Pa |
| `membrane_two_component` | Baker，第 3 章，完全混合膜及压差驱动力 | 二元；指定膜级分率；不估面积；校验正向通量 | 有限压比二次方程、守恒 |
| `psa_energy` | 压缩机和 `separator_energy` 组合 | 回收率由调用方给定；计进料压缩、产品升压和尾气抽真空 | 0.5 bar 抽至 1 bar 手算 |
| `absorber_kremser`, `stripper_heat` | Seader，第 7 章；Kremser 与显热/解吸/汽化热 | 稀溶质、恒 L/G、线性平衡；不含真实溶剂模型 | A=2、3 级；0.33 GJ/t |
| `distillation_fug` | Seader，第 9 章；Fenske–Underwood–Gilliland/Eduljee | 饱和液体进料 q=1、恒相对挥发度、全凝器；排除中间关键组分/共沸 | Nmin=ln361/ln2.5、Rmin=1.10、负荷 |
| `heat_exchanger` | 逆流 LMTD，Smith | 正端温差，U 为输入；不含壳程修正系数 | LMTD=89.628 K、等端温差 |
| `problem_table` | Linnhoff 1982 温度平移热级联 | 恒 CP 显热流；拒绝等温潜热流 | 四流例 QH=0、QC=79 kW；仅冷流负对照 |
| `steam_generation` | IAPWS-IF97 饱和表，分段线性 | 1–40 bar，饱和水制饱和汽；不含给水预热 | 10 bar 潜热 2014.4 kJ/kg |
| `turton_cost` | Turton 第 5 版附录 A，购置费对数二次式 + 裸模块因子 | 压缩机/泵/固定管板换热器/立卧容器/反应器壳体/填料及板式塔/炉；表内尺寸 | 9 类设备表格手算；例 7.13 压力/材质因子；实际资本 gate |
| `cepci`, `lang_factor_total` | Chemical Engineering 年均 CEPCI；Peters–Timmerhaus Lang 法 | 指数仅列已给年份；Lang 输入必须为共同年份购置费 | 816/397 升级、12000 USD |
| `idaes_check` | IDAES Modular Ideal/FTPx、真实 ipopt 求解 | 参考工厂显式状态；见下文 | 7 组协议/求解测试、8 项数值对比 |

资本输出统一含 `capex_basis={method:'size_based', cost_year, installed:true, installation_factor:1, size_basis, source}`。`turton_cost` 是设备裸模块安装费；`lang_factor_total` 是另一条从购置费估总安装投资的路径，两者不能重复套用。塔内件必须给出来源明确的 2001 年购置费与**独立**裸模块因子，不可沿用塔壳的压力/材质因子。反应器壳体不自动包含催化剂、搅拌或复杂内件。特殊材质、压缩机/炉的非基础压力修正、表外尺寸明确拒绝。

IDAES 支持 `Compressor/PressureChanger`、`Heater`、`Flash`、`Mixer/Separator`、`StoichiometricReactor`、`EquilibriumReactor` 和 `GibbsReactor`。`idaes_adapter.run({'units': [...]})` 在临时目录写 JSON，独立子进程限时 300 s；输入单元至少指定 `name,type,feed,T_in_K,P_in_bar`，加热/闪蒸/反应器指定 `T_out_K`，压缩指定 `P_out_bar`。平衡与计量反应器另给 `nu_list`，计量反应器另给 `extents_kmol_per_t`。显式 `inlet_from` 可引用前一个单元的总出口物料；默认各单元为独立参考快照，不推断拓扑。Flash 使用理想液体、常潜热，不是高压/非理想液相 EOS。

`idaes_check(model)` 或 `idaes_check(reference_out)` 映射 `physics.units` 的显式入口组成/状态；可用单元的 `idaes_case` 补充求解规格。缺状态或无对应模型的单元列入 `skipped`。逐项列出功、热负荷和组分出口相对差异，**>5% 为 WARNING**。工具在 V3.6 及后续版本模型阶段可用，写 `idaes_check.json`，提示要求在报告解释超差；不进入优化内循环、不改变得分。

本机优先使用 `D:\Tools\idaes-env\Scripts\python.exe`，设置 `IDAES_DATA` 与 ipopt PATH。若迁移的 venv 启动器仍指向不可用基础 Python，则用同主次版本的可用基础解释器，以 `-I -S` 启动子进程，仅加入**既有 IDAES 环境**包目录；结果标记启动方式。没有修改或安装环境。可通过 `IDAES_PYTHON/IDAES_BIN/IDAES_DATA` 指定其他现有环境。

验证：`tests_v3/validate_uo2.py`（17 组）、`tests_v3/validate_idaes.py`（缺环境/求解器明确 skip，计算错误 fail）、`tests_v3/run_uo2_regression.py`（含全部指定旧回归，最多 2 个工作子进程）。机器可读结果为 `uo2_idaes_results.json` 和 `uo2_regression_results.json`。

物性来源：[NIST WebBook](https://webbook.nist.gov/chemistry/)；CO₂ 液相 Lee & Kesler, AIChE J. 21 (1975), 510–527；成本来源 Turton 等 *Analysis, Synthesis, and Design of Chemical Processes*, 第 5 版附录 A、例 7.10–7.13；[Chemical Engineering CEPCI](https://www.chemengonline.com/pci-home)；[IDAES 官方文档](https://idaes-pse.readthedocs.io/en/stable/reference_guides/model_libraries/generic/index.html)。成本测试以表格手算为主，并未声称九类设备均已逐项复现书中独立 worked example。

## 物性数据修正（2026-11-15，独立物性交叉核对发现）

IDAES 复算用的是本库自己的 NIST 物性表，只能核对方程和求解，核对不了数据本身。所以另加了一项核对：把物性表和独立的 `chemicals`/`thermo` 数据库逐个物种比较（298→700 K 气相焓变差 ≤ 2 %，生成焓差 ≤ 1.5 kJ/mol），见 `tests_v3/validate_idaes.py` 的 `test_independent_properties`。

这项核对发现了一个固定库里的错误：NIST 没有甲醇、乙醇、乙烷、丙烷、丙烯的气相 Shomate 系数，原来的代码对这 5 个物种用 298 K 的恒定 Cp，700 K 时焓变偏低 26–33 %。已按 `chemicals` 的理想气体 Cp（TRC/Poling 数据）拟合 298–1000 K 的 Shomate 系数补上，拟合误差 ≤ 0.5 %。修正后 15 个物种里最大偏差是乙烯 1.2 %（NIST 自己的数据）。

影响范围：此前的 PDH 和甲醇建模没有调用这张物性表算能耗（模型代码里没有引用），只在物理门控的反应热检查里用到；甲烷化涉及的物种（CH4、CO2、H2、H2O、CO）不受影响。
