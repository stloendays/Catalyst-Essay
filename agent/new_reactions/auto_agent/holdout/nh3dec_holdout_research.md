# 氨分解（NH3 cracking, 2 NH3 -> N2 + 3 H2）留出验证集调研

写于 2026-11-13。只读调研：普通网页检索和下载，付费全文用 nus-fetch（没有用 nus-library MCP）。数字都从原文 PDF 抽出的文本里读出，页码见各条。
换算常数：NH3 17.031、H2 2.016 g/mol；LHV：NH3 18.6 GJ/t，H2 119.96 GJ/t；电折一次能源按 0.38（与 ch4 相同）。
化学计量下限：NH3 进料 5.632 t/t H2。若反应热也由 NH3 燃烧供给（25 °C，ΔH 45.9 kJ/mol），总耗量下限约 6.45 t/t。
汇率与价格指数：2015 年平均 1.1095 USD/EUR；CEPCI 2015 = 556.8，2019 = 607.5。

## 0. 推荐的留出集（先看这里）

手工模型 `configs/nh3dec_ours.json` 的依据是 HS420（Ecuity/Engie/STFC 2020）。留出集**不使用** HS420，也不使用与它同一 ENGIE 设计谱系的论文（理由见 1.4）。

| # | 量（门槛定义） | 推荐值 | 来源与位置 | 容差 | 能否干净设门槛 |
|---|---|---|---|---|---|
| T1 | NH3 总耗 t/t H2（进料加燃料折 NH3：boundary_in:NH3 + 燃料 GJ/18.6） | **7.28** | Mehr 2026 p.4209 §3.3.2："1000 MTPD NH3 corresponds to approximately 137 MTPD H2"；表 7 p.4205 给出 5726 kg/h。p.4207 §3.2.2：满负荷时 PSA 尾气足够供炉，不另烧 NH3 | ±5 % | **干净**：不受燃料来源的记账方式影响 |
| T2 | 燃烧炉热负荷（LHV，不管烧的是什么）加电力折一次能源，GJ/t H2 | **45.6** | 尾气中 H2 39.6 t/d 与 NH3 漏量合计约 35.0 GJ/t。这是由 PSA 回收率 81 %（表 6 p.4204）和"尾气足够"（p.4207）推出的上限。电耗 1.12 kWh/kg（摘要；p.4210），折 10.6 GJ/t | ±35 % | 中等：炉负荷是推算的上限；论文内电耗有矛盾，见 E |
| T3 | 装置投资 USD /（年产 1 t H2） | **4,030**（2015 USD，按 8000 h/a 年产 118.3 kt 计） | Ishimoto 2020 AAM 表 8 p.13–14：cracking 的 TPC 为 430 M€，规模 "120 t-NH3/h"。表 6 p.12：规模指数 0.67，含欧洲大陆地点系数 1.19。图 6 p.10：H2 收率 17.6/142.8 | −30 / +50 % | 可以，但文献离散度很大，见 E |
| T4（原子层） | 预测的最优 N 结合能减去 Ru(0001) 的值，eV（正值表示比 Ru 结合得强） | **−0.33** | Hansgen 2010 正文与图 1："peak … at a nitrogen binding energy of 134 kcal mol⁻¹"；表 1 中 Ru 为 141.6 kcal/mol。差值 −7.6 kcal/mol | ±0.2 eV | 可以，要求 agent 也以 Ru(0001) 为参照，见 B |

T3 的规模曲线（只用 Ishimoto 的 0.67 指数推出，不是独立的数据点），单位 [t/y, USD2015/(t/y)]：[[29600, 6370], [59200, 5070], [118300, 4030]]。换成 2019 USD 乘以 1.091。

和手工模型对比（事实陈述，按其配置推算）：
- T1：5.63 + 51.4/18.6 = **8.39**，比 7.28 高 15 %，**不在 ±5 % 内**。
- T2：51.4 + 50 kWh/t NH3 × 5.63 / 0.38 / 1000 × 3.6 ≈ **54.1**，高 19 %，在容差内。
- T3：7,045 USD2019/(t/y)，规模 66.7 kt/y。留出曲线插值到 66.7 kt 为 4,872 USD2015，即 5,316 USD2019。手工值高 **32.5 %**，在 +50 % 内。

## A. 装置层（工业最优）

### A.1 主源：Mehr, Scheffknecht, Zohourian, Reinmöller, Maier（Univ. Stuttgart/EnBW）
"Design, Simulation, and Techno-Economic Evaluation of a High-Capacity Ammonia Cracking Facility for Pipeline-Grade Hydrogen Production"，*Energy Sci. Eng.* 14 (2026) 4197–4212，DOI **10.1002/ese3.70618**，CC BY 开放获取，2026-07 接收。

| 量 | 值 | 位置 |
|---|---|---|
| 规模 | 1000 t/d NH3 进，137.4 t/d H2 出（5726 kg/h） | 摘要；表 7 p.4205；§3.3.2 p.4209 |
| NH3 t/t H2 | 7.28，全部为进料；满负荷不另烧 NH3（50 % 负荷时另需 192 kg/h NH3） | p.4207 §3.2.2 |
| 收率 / 效率 | 0.78 kg H2 / kg 进料 NH3 中的 H2；"overall thermal efficiency to approximately 88%"（核算：137.4×119.96/(1000×18.6) = 88.6 %） | p.4204 §3.1.2；表 9 p.4209 |
| 反应器 | 火管式 Ni/Al2O3，Temkin–Pyzhev 动力学，Ea 95.6 kJ/mol；进口 480 °C，出口 760 °C；正文写 17.5 bar（表 6 写 21 bar）；转化率 98.6 %（表 6 为 99.7 %） | p.4204 |
| 纯化 | 两床四步 PSA，99.96 mol %，回收率 81 % | 表 6 p.4204 |
| 产品 | 管输压力 104 bar（表 1 p.4199；§3.1.3 写 115 bar） | — |
| 电耗 | 满负荷 1.12 kWh/kg，50 % 负荷 1.32 kWh/kg；§3.1.4 p.4205 另写 7.54 kWh/kg | p.4210 |
| 投资 | 642.7 M€（含 2 × 27 kt 冷冻储罐和压缩），LCOH 8.36 €/kg | p.4210 |

投资数**不用**：表 9 列的 385–900 €/(kg/d) 与 642.7 M€ 对应的约 4,680 €/(kg/d) 对不上；表 10 中 CAPEX 2.73 €/kg 和正文 1.4 €/kg 也互相矛盾。

### A.2 投资与交叉核对：Ishimoto, Voldsund, Nekså, Roussanaly, Berstad, Gardarsdottir（IAE/SINTEF）
"Large-scale production and transport of hydrogen from Norway to Europe and Japan…"，*IJHE* 45 (2020) 32865–32883，DOI **10.1016/j.ijhydene.2020.09.017**。
公开的接收稿（CC BY-NC-ND）：https://hdl.handle.net/11250/2764352 （转到 nva.sikt.no）。
裂解部分按 WE-NET Subtask 3（J-Power 1996）设计，设在鹿特丹接收站。

- 图 6 p.10：NH3 142.8 t/h → 裂解（99.9 %）→ PSA（回收 75 %）→ 外送 H2 17.6 t/h。即 **8.11 t NH3/t H2**。燃料为尾气中的 6.3 t/h H2 再加 1.4 t/h 产品 H2，不烧 NH3。由此炉负荷 **52.6 GJ/t**，总 H2 回收率 69.5 %（表 5 p.9–10）。
- 表 5：电耗 400 kWh/t NH3，即 3.25 MWh/t H2，折一次能源 30.7 GJ/t（原文没说是否含压缩）。
- 表 8 p.13–14：规模 120 t-NH3/h，TPC **430 M€**（基准年 2015，表 6 标题）；外送 128 kt H2/y（p.5）。
- 原文没有给出操作温度、压力和催化剂。

### A.3 交叉核对
- **Fluor 为鹿特丹港所做预可研的执行摘要**（2023，公开）：https://www.portofrotterdam.com/sites/default/files/2023-05/large-scale-industrial-ammonia-cracking-plant.pdf 。
  p.2："1 million tons of hydrogen per year (equivalent to ~3000 ton/day…)"，"approximate consumption of 20,000 tons of ammonia"，合约 **6.67 t/t**。
  p.3：7 家许可商均可做到 99.9 mol %、50 barg，TRL 6–9。燃料全部无碳。p.4：80–90 % 的 H2 成本来自 NH3。没有给出投资数。
- **Balasubramanian, Haque, Bhargava, Parthasarathy**（RMIT/CSIRO），*IJHE* 166 (2025) 150904，DOI **10.1016/j.ijhydene.2025.150904**，CC BY（figshare 29938448）。
  规模 57 t/d H2，进料 323 t/d NH3（5.67 t/t，炉子烧天然气），1 % Ru/Al2O3，450 °C，PSA 回收 85 %，产品压缩到 880 bar。
  加热炉 16 MW（表 8），合 24.3 GJ/t。总能耗 8.5 MWh/t。PSA 方案投资 49.95 MUSD（2024 USD），合 **2,504 USD/(t/y)**。

### A.4 查过但不用
- **Makhloufi & Kezibri**，*IJHE* 46 (2021) 34777，DOI 10.1016/j.ijhydene.2021.07.188（ENGIE CRIGEN）：200 t/d，250 bar，热效率 68.5 %，深冷纯化。
  与 HS420（Engie 是合作方，同为 200 t/d、深冷纯化）是同一设计谱系，**与手工模型重叠**。全文受 Elsevier 人机验证所限，没能取得。
- **Richard 等**，*IJHE* 71 (2024) 571，DOI 10.1016/j.ijhydene.2024.05.308（ENGIE/TU/e）：FTR 方案的热效率同为 68.5 %，炉内热流分布沿用 Makhloufi，深冷纯化，为燃机供氢。属同一谱系，不用。
- Devkota 等 *Appl. Energy* 358 (2024) 122605、Restelli 等 *IJHE* 52 (2024) 532、Wen 等 *Appl. Energy* 390 (2025) 125871：nus-fetch 显示需手动下载，Polimi 和 EPFL 仓库也拦截了脚本。没有核数，不用。
- IRENA 2022《Global hydrogen trade Part II》：通用目录，agent 很可能会用。其约 1,700 USD/kW（约 200 t/d）的数与 HS420 量级一致，不作留出。

## B. 原子层（原子最优）

- **描述符**：Hansgen 用 N 原子化学吸附热 Q_N(0)，单位 kcal/mol，相对气相 N 原子；DFT 为 PW91、(111)/(0001) 平台、外推到零覆盖度。
  表 1：Pd 110.1，Pt 107.4，Ir 117.3，Ni 122.3，Rh 125.4，Co 125.4，**Ru 141.6**，Re 152.0，Mo 154.3。
- **条件**：850 K；固定床长 0.5 cm、直径 0.32 cm，70 sccm（p.6 Methods）。进料组成正文没有写。
- **最优位置**：134 kcal/mol，比 Ru(0001) 弱 7.6 kcal/mol，即 **0.33 eV**。
  Q_N 低于 125 时，速控步是 NH2 脱 H；高于此值时转为 N 的复合脱附。
- **接近顶点的表面**：Fe-Pt-Pt 134.1、Ni-Pt-Pt 130.7（表 2），Ru 略偏强结合一侧。TPD 实验中 Ni-Pt-Pt 的起始分解温度低于 Ru(0001)。
- **随条件移动**：Boisen 2005（DOI 10.1016/j.jcat.2004.12.013）由 Simonsen 2012 转述（公开稿 p.2）："99% NH3" 时峰在 Ru 与 Ni 之间；NH3/H2 降低时峰移向 Fe（强结合一侧）。所以合成的最优催化剂（如 Co-Mo）不是分解的最优催化剂。
  Boisen 原文受 Elsevier 拦截，没能读到原文里的具体数值。
- **门槛建议**：
  - T4：在 850 K、以纯 NH3 为主的进料下，agent 预测的最优值相对 Ru(0001) 为 −0.33 ± 0.2 eV（偏弱结合一侧）。
  - 方向性附加条件：NH3/H2 降低或转化率升高时，最优点移向强结合一侧。
- **必须屏蔽**：Hansgen 2010 *Nat. Chem.* 2, 484（10.1038/nchem.626）；Boisen 2005；Hansgen 2011 *J. Chem. Phys.* 134, 184701（10.1063/1.3589260，同一模型）；Guo & Vlachos 2015 *Nat. Commun.* 6, 8619（10.1038/ncomms9619，预防性屏蔽）。
- **不屏蔽**（agent 自建描述符模型的正当依据）：
  - Abild-Pedersen 2007 PRL 99, 016105（10.1103/PhysRevLett.99.016105），标度关系；
  - Logadottir 2001 *J. Catal.* 197, 229（10.1006/jcat.2000.3087），N2 的 BEP 关系与合成火山；
  - Wang 2011 PCCP 13, 20760（10.1039/c1cp20547a），N–H 断键的过渡态标度；
  - Dahl 1999 PRL 83, 1814（10.1103/PhysRevLett.83.1814），Ru 台阶位；
  - Jacobsen 2001 JACS 123, 8404（10.1021/ja010963d），周期表插值、Co-Mo；
  - Medford 2015 *J. Catal.* 328, 36（10.1016/j.jcat.2014.12.033）；
  - Hellman 2009 *Surf. Sci.* 603, 1731（10.1016/j.susc.2008.10.059），Ru 上合成与分解的第一性原理动力学。没读到全文，若其中含跨金属的分解火山，需改为屏蔽。

## C. 实验室层（描述符与实验速率的联系）

1. Ganley, Thomas, Seebauer, Masel, *Catal. Lett.* 96 (2004) 117，DOI 10.1023/B:CATL.0000030108.50691.d4：13 种金属负载于 Al2O3，580 °C 测 TOF，活性顺序 Ru > Ni > Rh > Co > Ir > Fe > Pt > Cr > Pd > Cu（二手转述）。Hansgen 图 1 把它与 Q_N 画在一起。**这是描述符与实验 TOF 之间的主要联系，建议保留给 agent 用。**
2. Yin 等, *Catal. Today* 93–95 (2004) 27，DOI 10.1016/j.cattod.2004.05.011：Ru/CNT 及 K 促进。综述见 Yin 等, *Appl. Catal. A* 277 (2004) 1，DOI 10.1016/j.apcata.2004.09.020。
3. Karim 等, *JACS* 131 (2009) 12230，DOI 10.1021/ja902587k：Ru/γ-Al2O3 粒径、形貌与 TOF 的关系（B5 位）。
4. Zhang, Xu, Li, *Appl. Catal. A* 296 (2005) 257，DOI 10.1016/j.apcata.2005.08.046：Ni 的结构敏感性与 La 促进。
5. Podila 等, *Catal. Sci. Technol.* 6 (2016) 1496，DOI 10.1039/C5CY00871A：Mo2N、Co3Mo3N。
6. Simonsen 等, *Appl. Catal. A* 447–448 (2012) 22，DOI 10.1016/j.apcata.2012.08.045：Ni-Fe 合金在两种气氛下测 TOF，并与 Ru 对比。它定性转述了峰位随条件的移动，有泄露风险，但不给数值，建议不屏蔽。

## D. 屏蔽清单（ch4.json 格式）

**dois**：10.1002/ese3.70618；10.1016/j.ijhydene.2020.09.017；10.1016/j.ijhydene.2025.150904；10.1038/nchem.626；10.1016/j.jcat.2004.12.013；10.1063/1.3589260；10.1038/ncomms9619

**url_fragments**（大小写不敏感）：`ese3.70618`、`11250/2764352`、`isimoto2020lsp`、`0198cc827bb1-0fe4540b-4d31-4949-845d-f470cc190c8e`、`day1_1140_ishimoto`、`s0360319925039047`、`figshare.com/articles/journal_contribution/techno-economic_comparison_of_ammonia_cracking`、`29938448`、`large-scale-industrial-ammonia-cracking-plant`、`nchem.626`、`jcat.2004.12.013`、`ncomms9619`、`osti.gov/pages/servlets/purl/1239294`、`stloendays`、`catalyst-essay`

**keyword_sets**（每组内的词同时出现才算命中，小写）：
1. `["1000 mtpd", "137 mtpd"]`
2. `["0.78 kg h2", "ammonia"]`
3. `["642.7", "ammonia"]`
4. `["8.36", "pipeline-grade"]`
5. `["142.8", "nh3", "cracking"]`
6. `["400 kwh/t-nh3", "cracking"]`
7. `["we-net", "nh3 cracking"]`
8. `["20,000 tons of ammonia", "1 million tons of hydrogen"]`
9. `["fluor", "ammonia cracking", "pre-feasibility"]`
10. `["49.95", "psa", "ammonia"]`
11. `["134 kcal", "nitrogen"]`
12. `["ni-pt-pt", "ammonia"]`
13. `["heat of nitrogen chemisorption", "volcano", "ammonia decomposition"]`
14. `["optimal ammonia synthesis catalyst is not the optimal ammonia decomposition catalyst"]`

这些词组都不会命中一般的裂解文献（如 "Ru > Ni"、"PSA recovery"、"ammonia cracking cost"）。

## E. 风险与公平性

1. **T1 的设计离散度大于 ±5 %**。各来源分别为：Fluor 6.67（−8 %）、Mehr 7.28、Ishimoto 8.11（+11 %）、手工模型 8.39（+15 %）。差别来自 PSA 回收率（75–90 %）和热回收程度。
   ±5 % 相当于只认 Mehr 这一种设计。如要放宽，建议 ±12 %，即可覆盖 Fluor 和 Ishimoto。
2. **T1 与 T2 部分冗余**：在用尾气供热的设计里，炉负荷约等于（T1 × 0.1776 − 1）× 120。agent 若改用天然气供热，T1 会接近 5.63–5.7，同时 T2 上升。所以 T1 必须按"进料 + 燃料/18.6"计。evaluate_builds 需要新增这个派生量。
3. **Mehr 文内有矛盾**：压力 17.5 / 21 bar，电耗 1.12 / 7.54 kWh/kg，投资 642.7 M€ / 385–900 €/(kg/d)。这里只取能闭合的数：质量、88.6 % 效率、1.12 kWh/kg（与表 10 的电费 0.113–0.133 €/kg 一致）。
4. **投资离散约 6 倍**：Balasubramanian 2,504 USD2024、Ishimoto 4,030 USD2015、HS420 7,045 USD2019、Mehr 约 14,000 €（含储罐）。
   Ishimoto 的成本源自 1996 年的 WE-NET 设计，按指数缩放，且含 1.19 的地点系数。
   币种年份：EUR2015 按 1.1095 换算，没有按 CEPCI 升到当前年份；比较时手工模型的 2019 USD 应除以 1.091。
5. **口径**：Mehr 不含储罐之外的上游；Ishimoto 的 400 kWh/t NH3 可能包含压缩。T2 的电力部分按 Mehr 计（含压缩到 104 bar）。
6. **原子层**：Q_N 的绝对值随泛函相差 0.3–0.5 eV，所以门槛只认相对 Ru(0001) 的差值。Hansgen 的进料组成正文未写，"850 K、以 NH3 为主"是推断。
   综述（Lucentini 2021 IECR 10.1021/acs.iecr.1c00843、Bell 2016 Top. Catal. 10.1007/s11244-016-0653-4）复印了火山图，没有屏蔽，agent 可能从图上读出大致峰位。

## 草案 holdout/nh3dec.json（只列要点）

```json
{"rxn":"nh3dec",
 "targets":{
  "NH3 incl. fuel per t H2":{"quantity":"nh3_equiv_t_per_t","value":7.28,"tol":0.05,
    "source":"Mehr 2026 ESE 14:4209 s3.3.2 (1000 t/d NH3 -> 137.4 t/d H2), p.4207 PSA purge covers furnace at full load"},
  "fired duty + primary electricity GJ per t H2":{"quantity":"energy_GJ_per_t","value":45.6,"tol":0.35,
    "source":"Mehr 2026: purge LHV <=35.0 GJ/t (PSA 81 %, Table 6) + 1.12 kWh/kg (p.4210) /0.38"},
  "installed capital per annual t":{"quantity":"capex_usd_per_t_y","value":4030,"tol":[-0.3,0.5],
    "scale_curve":[[29600,6370],[59200,5070],[118300,4030]],
    "source":"Ishimoto 2020 IJHE AAM Table 8: 430 MEUR2015 for 120 t-NH3/h cracking+PSA, Fig.6 yield 0.1232, 8000 h, n=0.67 (Table 6), 1.1095 USD/EUR"},
  "atomic optimum dQ_N vs Ru(0001) eV":{"quantity":"descriptor_opt_minus_Ru_eV","value":-0.33,"tol_abs":0.2,
    "source":"Hansgen 2010 Nat Chem Fig.1/Table 1: 134 vs 141.6 kcal/mol at 850 K"}},
 "reported_not_gated":{
  "Fluor/PoR NH3 t/t":6.67,"Ishimoto NH3 t/t":8.11,"Ishimoto fired GJ/t":52.6,
  "Balasubramanian capex USD2024/(t/y) @20 kt/y":2504,"Mehr capex MEUR (incl. storage)":642.7,
  "hand-built: NH3 8.39 t/t, energy ~54.1 GJ/t, capex 7045 USD2019/(t/y)":null},
 "pass_rule":{"rule":"plant: pass = T1-T3 within tolerance; partial = two within and none beyond twice the tolerance. Atomic gate T4 reported separately."}}
```
