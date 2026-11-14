# CO2 甲烷化（Sabatier, CO2 + 4 H2 -> CH4 + 2 H2O）留出验证集调研

写于 2026-11-12。只用了普通网页检索和下载（没有用 nus-library MCP）。这里的数都是从原文 PDF 抽出的文本里读出来的，页码按 PDF 页脚标注。
换算常数：CH4 16.043、H2 2.016、CO2 44.01 g/mol；STP（0 °C）下 22.414 m³/kmol，即 1 t CH4 = 1397 m³(STP)；
HHV：CH4 55.50 MJ/kg（15.42 kWh/kg），H2 141.8 MJ/kg（39.39 kWh/kg）。
电折一次能源按 0.38，与 PDH 各次构建里 agent 用的系数一致；2017 年平均汇率 1.1297 USD/EUR。
化学计量下限：H2 0.5026 t/t，CO2 2.743 t/t。

## 0. 推荐的留出集（先看这里）

| 量 | 推荐值 | 来源与位置 | 容差 | 性质 |
|---|---|---|---|---|
| H2 进料 t/t CH4 | **0.505** | STORE&GO D5.9 表 4-1（p.35，实测 708 kW H2 → 549 kW SNG，HHV），表 5-2（p.68，设计 6450 kW H2 / 5 MW SNG）两处一致 | ±5 % | 实测 + 设计 |
| CO2 进料 t/t CH4 | **2.785** | D5.9 表 5-2（p.68）："CO2 Volume flow at full load 460 … m³/h"，对 5 MW SNG 计（324.3 kg CH4/h） | ±5 % | 设计；Audi Werlte 的 2.8 t/t（新闻稿给的整数）可作佐证 |
| 外购能量 GJ/t（一次能源） | **3.84** | D5.9 表 5-2（p.69）甲烷化单元电耗 0.29 kWh/m³ SNG；p.70 原文 "an electrical demand of 25 kW/MW was assumed"。0.29×1397 = 405 kWh/t = 1.46 GJe/t，除以 0.38 | ±35 % | 设计（5 MW 放大工况）。实测值作上限参考、不设门槛，见下 |
| 装置投资 USD /（年产 1 t） | **784**（2017 USD） | D5.9 p.63："specific CAPEX of a 50 MW SNG output is further decreased to 360 €/kW"。360 €/kW × 50 MW = 18.0 M€；按 8000 h/a 年产 25.95 kt；乘 1.1297 USD/EUR | −30 / +50 %（AACE class 4） | 估算（Aspen 加附加系数法，厂别专属） |

不设门槛、只报告的参考值：
- **实测能耗上限**：Falkenhagen 实测甲烷化电耗 0.8 kWh/m³ SNG（D5.9 表 4-2 p.39；表 4-1 是 41 kW / 35.6 kg CH4/h = 1.15 kWh/kg），合 4.0–4.1 GJe/t，**一次能源 10.6–10.9 GJ/t**。Solothurn 实测 1.0 kWh/m³（表 4-6 p.47），合 13.2 GJ/t。两台都是 MW 以下的示范装置，进料从近常压压到 14 bar，还有电伴热。
- 算上并网压缩（63 bar，0.10 kWh/m³，表 5-2）后是 0.39 kWh/m³，合 5.16 GJ/t，仍在 +35 % 以内。
- CO2 捕集电耗（Falkenhagen 原计划的胺吸收，1.0 kWh/m³ SNG，表 4-2/5-2）**不应计入**：模型把 CO2 当作外购进料。
- **投资随规模的变化**：D5.9 优化后的 Falkenhagen 设计在 5 MW 时 720 €/kW（年产 2.59 kt，1567 USD/(t/y)），10 MW 时约 475 €/kW（原文说比 5 MW "reduced by about 34 %"，年产 5.19 kt，约 1035 USD/(t/y)），50 MW 时 360 €/kW（784 USD/(t/y)）。Solothurn 优化设计在 50 MW 时 380 €/kW，合 827 USD/(t/y)。
  agent 选的产能不在 15–60 kt/y 范围内时，建议在这三点之间按 log-log 插值到 agent 的产能再比较。10→50 MW 隐含的规模指数约为 0.83。
- **独立佐证（不同团队）**：Electrochaea BioCat 最终报告给出 50 MWe 生物甲烷化装置的甲烷化部分投资 63.54 MDKK（p.24 Figure 1.8）。按 200–240 Nm³ H2/MWh 算，年产 14–17 kt CH4，合 **560–700 USD/(t/y)**（约 2017 年价），与 784 相差约 −10 至 −30 %。

和手工参考模型对比（事实陈述）：`configs/ch4_ours.json` 里 capex 22.43 MUSD / 50 kt/y = **449 USD/(t/y)**，依据是 Götz 2016 的 175 €/kW。它比上面的 784 低 43 %，落在 −30 % 门槛之外。
即使按 D5.9 隐含的 0.83 指数把 50 MW 放大到 96 MW（约 702 USD/(t/y)），差距仍是 −36 %。如果留出集按本文采用，手工模型的投资这一项通不过。

## 1. 候选来源逐一说明

### 1.1 STORE&GO D5.9（首选，四个量都能读出）

- **引用**：Mörs F., Schlautmann R. *et al.* (DVGW-EBI/KIT), "D5.9 Final report on evaluation of technologies and processes", STORE&GO（EU H2020 grant 691797），第 2.0 版，2020-05-15，92 页。
- **URL（已确认可打开，HTTP 200）**：https://www.storeandgo.info/fileadmin/downloads/deliverables_2020/20200713-STOREandGO_D5.9_DVGW_Final_report_on_evaluation_of_technologies_and_processes.pdf
- **DOI**：无。
- **同一套数据的期刊版（也要屏蔽）**：Schlautmann R., Böhm H., Zauner A., Mörs F., Tichler R., Graf F., Kolb T., "Renewable Power-to-Gas: A Technical and Economic Evaluation of Three Demo Sites Within the STORE&GO Project", *Chem. Ing. Tech.* 93 (2021) 568–579，DOI **10.1002/cite.202000187**（经 Crossref 核对；doi.org 跳转到 Wiley，出版商对脚本返回 403）。KIT 开放获取镜像：https://publikationen.bibliothek.kit.edu/1000130144
- **装置**：Falkenhagen（德国），蜂窝式催化甲烷化 + 精制反应器，14 bar，最大 210 m³/h H2，约 1 MWel；SNG 0.58 MW（HHV）。Solothurn（瑞士），生物甲烷化，0.325 MW SNG。Troia（意大利），毫通道反应器 + 直接空气捕集 + LNG，0.112 MW。
- **数值与位置**：

| 量 | 值 | 位置 / 原文（<15 词） | 性质 |
|---|---|---|---|
| H2 t/t（FH 实测） | 0.505 | 表 4-1 p.35："PtG plant H2 input 708 715 kW"；SNG 549 kW | 实测，95 % 负荷，2019-04-17 运行 1 h |
| H2 t/t（5 MW 设计，FH/SO/TR） | 0.505 / 0.512 / 0.514 | 表 5-2 p.68："H2 output at full load for 5MW SNG output 6450 6540 6560 kW" | 设计 |
| CO2 t/t（5 MW 设计） | 2.785 | 表 5-2 p.68：460 m³/h CO2 | 设计 |
| CO2（FH 实测） | 不能用 | p.33：H2/CO2 实测 4.4，原文称 "most probably a measurement error"；表 2-1 的累计值包含火炬燃烧，同样不能用 | — |
| 甲烷化电耗（FH 实测） | 0.8 kWh/m³ SNG（41 kW） | 表 4-2 p.39："Energy demand 1.0 22.4 0.8 0.1 kWh/m³"（依次为 CO2 源 / 电解 / 甲烷化 / 注入）；表 4-1 p.35 | 实测 |
| 甲烷化电耗（5 MW 设计） | 0.29 kWh/m³（25 kW/MW） | 表 5-2 p.69 与 p.70 | 设计假设 |
| 可外供热（不抵扣） | 1.7 kWh/m³（实测，184 °C），优化后 2.1 + 0.9 kWh/m³ | 表 4-2 p.39 | 实测 / 估计 |
| 投资：FH 示范装置 | 3740 €/kW × 0.58 MW = 2.17 M€（年产约 301 t，合 7207 €/(t/y)） | p.61："the total specific CAPEX is 3740 €/kW" | DVGW 成本工具估算，不是实际结算价 |
| 投资：FH 按原设计放大到 5 MW | 1430 €/kW（3113 USD/(t/y)） | p.61 | 估算 |
| 投资：FH 优化设计 5 / 10 / 50 MW | 720 / 约 475 / 360 €/kW | p.63、表 1-2 p.7、表 5-1 p.67 | 估算 |
| 投资：SO 示范 / 5 MW / 优化 5 / 10 / 50 MW | 4320 / 940 / 870 / 590 / 380 €/kW | p.62、p.64 | 估算 |
| 投资：TR 示范 / 5 MW / 10 MW | 5400 / 1090 / 790 €/kW | p.62、p.64 | 估算 |
| 全链投资（含电解等） | 3100 €/kW（FH，5 MW） | 表 5-1 p.67 | 文献加估算 |

- **口径**：CAPEX_Meth 只含甲烷化单元，不含电解、CO2 处理和注入（p.61）。币种为欧元，按 2017 年平均汇率换算并作了通胀调整（p.29："using the average exchange rate of 2017"）。
  附加系数见表 3-1 p.30：contingency 取 0，auxiliary services 取 0，outside lines 取 0（假定建在已有厂区内），所以数值偏向 ISBL 下限。投资按 SNG 的 HHV 计。产能按 8000 h/a 算（p.31 情景设定、p.71）。
- **适合留出的理由**：针对具体装置，有实测；四个量都在同一份文件里，有页码可查。它是项目交付物，不在综述常引的文献里，但 agent 搜 "STORE&GO" 可能找到，所以必须按域名屏蔽。

### 1.2 Electrochaea P2G-BioCat 最终报告（投资的独立佐证；生物法）

- **引用**：Electrochaea.dk ApS *et al.*, "Power-to-Gas via Biological Catalysis (P2G-Biocat) – Final report", ForskEL project 2014-1-12164（Energinet/ForskEL），约 2017 年。
- **URL（已确认可打开，200）**：https://energiforskning.dk/sites/energiforskning.dk/files/slutrapporter/12164_final_report_p2g_biocat.pdf ；无 DOI。
- **数值**：
  - Avedøre 1 MW 示范的实际项目总花费为 60,005,811 DKK（p.13，含研发）。
  - 投资估算表 Figure 1.8（p.24）："Methanation DKK 10.90 DKK 28.10 DKK 36.82 DKK 63.54"，对应 1/10/20/50 MWe。这是基于 BioCat 设计的报价估算。
  - 运行窗口：H2:CO2 = 4.02–4.2（p.16）。
  - 辅助电耗：只说 "3% to 5%" 的电用于照明、待机等辅助设备（p.22），没有按甲烷化单独给出。
- **能用的**：50 MWe 甲烷化部分 560–700 USD/(t/y)，用作投资佐证。
- **不能用的**：进料比和能耗没有可直接读出的稳态数。另外这是生物法，而 agent 建的是催化固定床。

### 1.3 Audi e-gas Werlte（ETOGAS/MAN，6.3 MWel）

- 新闻稿口径："about 1,000 metric tons of e-gas … bind some 2,800 metric tons of CO2"，即 **CO2 2.8 t/t**（设计值，取了整），例如 https://www.pv-magazine.com/2013/06/27/audi-opens-6-mw-power-to-gas-facility_100011859 。
- 投资只有二手数据库的 "budget 20 million euros"（https://database.co2value.eu/projects/7），而且包含电解，不能拆出甲烷化部分。
- 结论：只适合作 CO2 进料的佐证，不适合作留出主源。

### 1.4 查过但不适合的

- **HELMETH D4.2**（https://task33.ieabioenergy.com/wp-content/uploads/sites/33/2022/06/HELMETH_DELIVERABLE_4.2_R1.0_2.pdf）：SOEC + 甲烷化，10 kW 级，PtG 效率 75.4–76.1 %，没有投资数，规模太小。
- **INPEX/大阪燃气 长冈 400 Nm³-CO2/h**（NEDO 成果报告会 2026 o-04，https://www.nedo.go.jp/content/800060336.pdf）：海报上没有能耗和投资数。
- **Jupiter 1000**（GRTgaz，25 Nm³/h CO2、22 Nm³/h CH4，见 https://atee.fr/system/files/2022-06/presentation%20CEA%20ATEE%20methanation%202022.pdf）：没有公开的单元能耗和投资。
- **Becker 2011 硕士论文**（Colorado School of Mines，50 MW SNG）：原链接已经 404。
- **Becker, Penev & Braun, J. Energy Resour. Technol. 141 (2019) 021901**，DOI 10.1115/1.4041381：手工模型引用过它的 H2 价格，agent 也容易搜到，不宜作留出。
- **Frontiers in Chemistry 2024 Nepal SNG**，DOI 10.3389/fchem.2024.1347255：表 4 的币值换算自相矛盾，CO2 进料在各节之间不一致，质量差，不用。
- **DGC 2019 "Biogas, Biomethane and Electro-methane cost comparison"**（https://dgc.dk/media/g1bn0xut/electrolyser-and-methanisation-economics_final-1.pdf）：基于文献综合，5 MW SNG 甲烷化 37.4 / 31.3 MDKK（表 4-6），属于通用估算。
- **丹麦能源署 Technology Data – Renewable fuels**（https://ens.dk/technologydata）：通用目录，agent 很可能会用到，不作留出。
- **Böhm, Zauner, Rosenfeld, Tichler, Applied Energy 264 (2020) 114780**，DOI 10.1016/j.apenergy.2020.114780："Projecting cost development for future large-scale power-to-gas implementations by scaling effects"。与 STORE&GO 是同一个联合体，可能复用 D5.9 的投资数。没有逐项核对，**预防性屏蔽**。

### 1.5 通用综述（agent 很可能会找到，不适合作留出）

- **Götz M. *et al.***, "Renewable Power-to-Gas: A technological and economic review", *Renew. Energy* 85 (2016) 1371–1390，DOI 10.1016/j.renene.2015.07.066。甲烷化投资约为 130 €/kW_SNG（110 MW）到 400 €/kW（5 MW），手工模型取 175 €/kW。
- **Thema M., Bauer F., Sterner M.**, "Power-to-Gas: Electrolysis and methanation status review", *RSER* 112 (2019) 775–787，DOI 10.1016/j.rser.2019.06.030。按年份平均的安装成本数据库；摘要预计到 2050 年电解和甲烷化都会降到 500 €/kWel 以下。同组另一篇给出的文献区间是 190–1500 €/kW_SNG。
- **Gorre J., Ortloff F., van Leeuwen C.**, "Production costs for synthetic methane in 2030 and 2050 of an optimized Power-to-Gas plant with intermediate hydrogen storage", *Appl. Energy* 253 (2019) 113594，DOI 10.1016/j.apenergy.2019.113594。2030/2050 年的通用成本假设。
- 这三篇的 DOI 都通过 doi.org 解析到了 Elsevier。

## 2. 屏蔽清单与抄数检测

**dois**：
- 10.1002/cite.202000187
- 10.1016/j.apenergy.2020.114780

**url_fragments**（请按大小写不敏感匹配）：
- `storeandgo`（覆盖 storeandgo.info 域名和 "STOREandGO_D5.9" 文件名）
- `cordis.europa.eu/project/id/691797`
- `cite.202000187`
- `publikationen.bibliothek.kit.edu/1000130144`
- `s0306261920302920`（Böhm 2020 的 PII）
- `12164_final_report_p2g_biocat`
- `energiforskning.dk/sites/energiforskning.dk/files/slutrapporter/12164`
- `database.co2value.eu/projects/7`
- `stloendays`
- `catalyst-essay`

**keyword_sets**（每组内所有词同时出现才算命中，小写）：
1. `["falkenhagen", "720 €/kw"]`
2. `["falkenhagen", "3740"]`
3. `["falkenhagen", "360 €/kw"]`
4. `["solothurn", "380 €/kw"]`
5. `["store&go", "methanation", "capex"]`
6. `["460 m³/h", "6450"]`
7. `["25 kw/mw", "methanation"]`
8. `["falkenhagen", "0.8 kwh/m³"]`
9. `["biocat", "63.54"]`
10. `["avedøre", "methanation", "dkk"]`

单靠数字很难判定抄袭，因为 0.505 和 2.785 几乎就是化学计量值。所以检测应主要靠投资和能耗这两组带厂名的关键词。

## 3. 可直接改写成 holdout/ch4.json 的草案

```json
{
 "rxn": "ch4",
 "sources": [
  {"name": "STORE&GO D5.9 Final report on evaluation of technologies and processes (DVGW, 2020)",
   "url": "https://www.storeandgo.info/fileadmin/downloads/deliverables_2020/20200713-STOREandGO_D5.9_DVGW_Final_report_on_evaluation_of_technologies_and_processes.pdf"},
  {"name": "Schlautmann et al., Chem. Ing. Tech. 93 (2021) 568 (same data)", "url": "https://doi.org/10.1002/cite.202000187"},
  {"name": "Electrochaea P2G-BioCat final report, ForskEL 2014-1-12164 (capex cross-check)",
   "url": "https://energiforskning.dk/sites/energiforskning.dk/files/slutrapporter/12164_final_report_p2g_biocat.pdf"}],
 "dois": ["10.1002/cite.202000187", "10.1016/j.apenergy.2020.114780"],
 "targets": {
  "H2 per t CH4": {"quantity": "h2_t_per_t", "value": 0.505, "tol": 0.05,
    "source": "D5.9 Table 4-1 (measured 708 kW H2 -> 549 kW SNG, HHV) and Table 5-2 (6450 kW H2 per 5 MW SNG)"},
  "CO2 per t CH4": {"quantity": "feed_t_per_t", "value": 2.785, "tol": 0.05,
    "source": "D5.9 Table 5-2: 460 m3(STP)/h CO2 per 5 MW SNG (HHV); Audi Werlte 2.8 t/t as support"},
  "purchased energy GJ per t": {"quantity": "energy_GJ_per_t", "value": 3.84, "tol": 0.35,
    "source": "D5.9 Table 5-2 / p.70: methanation electricity 0.29 kWh/m3 SNG (25 kW/MW) = 1.46 GJe/t, /0.38; CO2 capture and grid injection outside the boundary"},
  "installed capital per annual t": {"quantity": "capex_usd_per_t_y", "value": 784, "tol": [-0.30, 0.50],
    "source": "D5.9 p.63: optimized Falkenhagen design 360 EUR/kW at 50 MW SNG = 18.0 MEUR (2017), 25.95 kt/y at 8000 h, 1.1297 USD/EUR"}},
 "reported_not_gated": {
  "measured methanation electricity, demo scale": {"value": 10.6, "basis": "D5.9 Table 4-2: 0.8 kWh/m3 SNG at Falkenhagen (0.58 MW), /0.38; Solothurn 1.0 kWh/m3 -> 13.2"},
  "capex scale points USD2017/(t/y)": {"value": {"5 MW": 1567, "10 MW": 1035, "50 MW": 784}, "basis": "D5.9 p.63, Table 5-1"},
  "BioCat 50 MWe methanation capex USD/(t/y)": {"value": [560, 700], "basis": "BioCat final report Fig. 1.8: 63.54 MDKK"}}
}
```

注意：`feed_t_per_t` 在 build_mode 里对应 key_feed，手工配置的 key 是 CO2。H2 需要 evaluate_builds 另加一个字段，或者在 agent 契约里加 `h2_t_per_t`。
