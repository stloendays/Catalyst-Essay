# 甲醇金标准100项：原始文献独立核验与尚缺证据（2026-10-12）

## 核验范围与边界

已对照原始抽样工作簿的100个字段，以及GitHub冻结S5分支的40组/310条有效候选；100/100抽样记录的DOI+entry+catalyst三键均仍属于冻结版。该结果验证**样本仍在当前总体中**，不代表旧100值是按新总体随机重抽的。

以公开原文（主文、表格和SI）独立核查，原文无从取得时保留不可核状态。所有结论均为**AI协助的文献核验意见**，不是由第三方人类审核员签署的100项人工金标准。原始Excel表「核对表」N–R五列保持未改；「AI预填核验草稿_待复签」与「逐项原文核验」单列可确认的证据。

## 100项状态统计

| 证据状态 | 项数 | 含义 |
|---|---:|---|
| 01 数值相符 / 引文修订 | 42 | 存在原始具体行、正文数字或等价单位换算 |
| 02 数值可溯源但经推算 | 3 | 原文提供组成但抽取字段为推算值 |
| 03 限值或非直印，原文映射待核 | 2 | 限定符、直接印刷资格或来源关联仍有问题 |
| 04 仅条件或二手佐证 | 11 | 仅有文献背景条件或二手证据 |
| 05 未取得指定原始表行 | 42 | 关键原文/表格行未取得 |

“原文相符”是对提取值的证据一致性判断；未进行论文-领域总体准确率估计，也没有将未确认项按正确处理。

## 逐论文覆盖统计

| 论文 | 01 可核 | 02 推算 | 03 异常 | 04 背景 | 05 待核 |
|---|---:|---:|---:|---:|---:|
| Malik 2018 | 0 | 0 | 0 | 1 | 9 |
| Meng 2021 | 3 | 0 | 1 | 3 | 3 |
| Bansode 2013 | 10 | 0 | 0 | 0 | 0 |
| Frei 2019 | 10 | 0 | 0 | 0 | 0 |
| Dang 2020 | 9 | 1 | 0 | 0 | 0 |
| Gao 2015 | 0 | 0 | 0 | 3 | 7 |
| Rui 2017 | 0 | 0 | 0 | 4 | 6 |
| Energy Technol 2018 | 0 | 0 | 0 | 0 | 10 |
| Ruiz Esquius 2020 | 1 | 2 | 0 | 0 | 7 |
| Ota 2012 | 9 | 0 | 1 | 0 | 0 |

## 已取得的原文事实

Bansode 2013: RSC原始4页ESI中Table S1/S2/S3对应10项抽样值，温度K与压力MPa、MeOH yield mg/(gcat h)要分开报告。原SI：https://www.rsc.org/suppdata/cy/c2/c2cy20604h/c2cy20604h.pdf

Meng 2021：主文明确0.30 gMeOH/(gcat h)以及图注12,000/24,000 mL/(gcat h)工况；部分SI Table S2载体数据仍缺，且图2A的0.4% CH₄并未印出精确柱值。DOI: https://doi.org/10.1126/sciadv.abi6012

Frei 2019：500 h 稳定性段落为75%→78%选择性、9.7%→9.2%转化率，测试553K、5MPa；#40的9.7%不在Table2（Table2没有CO₂ conversion列），应引Fig6附近正文。https://www.nature.com/articles/s41467-019-11349-9

Dang 2020：Fig5文字明确15.4% CO₂转化率（360°C），初始选择性71%、44h后85%；标准进料H₂:CO₂:N₂=73:24:3，#45的3.041666…是73/24推算，不能标为该小数原文直印。DOI: https://doi.org/10.1126/sciadv.aaz2060

Gao 2015：RSC公布了8页原SI，但其仅含FigS1–S10，没有抽样指定的主文Table6；需单独取得主文Table6。原SI: https://www.rsc.org/suppdata/c5/cy/c5cy00372e/c5cy00372e1.pdf

Rui 2017：摘要层面是300°C、5MPa、转化率>20%、甲醇选择性>70%、最高STY0.89，但本样本逐行在SI TableS1/S2，不能用摘要替代。DOI: https://doi.org/10.1016/j.apcatb.2017.06.069

Ruiz Esquius 2020：Cardiff大学版本的主文Table1明确Pd/TiO₂ 225°C，进料60%H₂/20%CO₂/20%N₂；#85/#90的H₂/CO₂=3是60/20推算。多项样本对应补充Table S2/S3/S4，目前尚未拿到。原文：https://orca.cardiff.ac.uk/id/eprint/135088/13/cctc.202000974%20FINAL.pdf

Ota 2012：上轮核到Table2多项性能，但本轮复取作者接受稿受阻；#93必须连同“<”限定符而非仅0.1%审查；Table2没有直接印CH₄选择性，不能直接按correct结案。DOI: https://doi.org/10.1016/j.jcat.2012.05.020

## 完成全部100项尚需的原始文件

以下文件是现有GitHub下载清单记录的可复核目标；清单中status=ok只表示用户工作目录曾成功下载，不代表该文件已随GitHub入库；当前远程电脑离线：

- **Malik 2018**：主文Table6页面或整篇可读PDF。资源：https://ars.els-cdn.com/content/image/1-s2.0-S0926860X18302084-mmc1.docx。备注：SI是mmc1.docx；当前目标数据多数在主文Table6。
- **Meng 2021**：sciadv.abi6012_sm.pdf（SI Table S2、S7）。资源：https://www.science.org/doi/suppl/10.1126/sciadv.abi6012/suppl_file/sciadv.abi6012_sm.pdf。备注：主文原始PDF已核；图2的数值仅有部分直接印刷。
- **Gao 2015**：需主文Table 6（不是ESI）。资源：https://www.rsc.org/suppdata/c5/cy/c5cy00372e/c5cy00372e1.pdf。备注：8页ESI已找到，但只有FigS1–S10，不含Table6。
- **Rui 2017**：10_1016_j_apcatb_2017_06_069__mmc1.docx（SI S1/S2）。资源：https://ars.els-cdn.com/content/image/1-s2.0-S0926337317306197-mmc1.docx。备注：目前仅能佐证摘要中T=300C、P=5MPa。
- **Energy Technol 2018**：ente201800747-sup-0001-SuppData-S1.pdf。资源：https://onlinelibrary.wiley.com/action/downloadSupplement?doi=10.1002%2Fente.201800747&file=ente201800747-sup-0001-SuppData-S1.pdf。备注：主要需要SI Table S1。
- **Ruiz Esquius 2020**：cctc202000974-sup-0001-misc_information.pdf。资源：https://chemistry-europe.onlinelibrary.wiley.com/action/downloadSupplement?doi=10.1002%2Fcctc.202000974&file=cctc202000974-sup-0001-misc_information.pdf。备注：主文Table1已核；SI Tables S2–S4待核。
- **Ota 2012**：作者接受稿Table2上轮已核；本轮下载需恢复。资源：https://iris.unito.it/retrieve/handle/2318/122839/18808/COST_OA.pdf。备注：#93原论文Table2没有CH4选择性列，需独立确认上界依据。

## 准确率的统计限制

本抽样每篇固定10个数、先抽论文再抽字段，字段类别与论文内重复条件不均衡。100项中55项为性能数据、45项工况数据；任何未加权的correct/100只描述本次选中的样本，不宜直接等价于甲醇全库逐值准确率。建议完成逐项作者复签后，分性能/工况和按paper cluster报告误差与区间；另对重要排序反转论文增加定向全量审计。

## 来源追踪

- 原抽样表/脚本：https://github.com/stloendays/Catalyst-Essay/blob/freeze-s5-printed-2026-10-12/analysis/verify_2026_10_08/gold_standard_sample.py
- 抽样CSV与 #93 qualifier: https://github.com/stloendays/Catalyst-Essay/blob/freeze-s5-printed-2026-10-12/analysis/verify_2026_10_08/gold_standard_sample.csv
- 冻结版甲醇结果：https://github.com/stloendays/Catalyst-Essay/blob/freeze-s5-printed-2026-10-12/analysis/meoh_literature_inversion_2026_10_05/summary.json
- 本次整理的10篇论文文献工作区：https://app.undermind.ai/projects/7f59cd3c-1c28-48c1-b897-bab4fbcbd522

> 结案标准：提供缺失Table/SI原文并逐行比对；对于所有无法确认的原始值继续标记“未核”。本轮并未声称全部100项正确或已经完成人类人工金标准审核。
