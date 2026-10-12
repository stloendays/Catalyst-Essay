# 甲醇金标准100项：Google Drive 原论文/SI 独立再审（2026-10-12）

## 核验范围与判定
基于用户Google Drive上传的10篇原始论文主文及与抽样字段有关的SI，重新逐条核对100项字段。所有原始PDF下载到本次会话环境，并对文件SHA256固化。Excel原始「核对表」的人工判定N–R列没有写入AI结论。

| 证据类别 | 项数 | 解释 |
|---|---:|---|
| 直接印刷/单位等价 | 91 | 原始表格/正文/图注直接给出数值；允许标准单位转换 |
| 组成或比值推导 | 6 | 数值由组成比或倒序比推得；并非该字段原样印刷 |
| 原文值对但定位错误 | 1 | 数值出现在正文，但不是原Excel声称的Table2 |
| 上界符号需恢复 | 1 | 原文给的是小于号上界，不是等号实测值 |
| 术语/计量口径需注明 | 1 | 原论文列名Rate或Yield，而采集字段STY printed |
| **合计** | **100** | 在所取文献证据中，未发现直接相互矛盾的抽取数值；这不意味着100个原始字段都是严格直接印刷数值。 |

## 可以立即修改的九处（按严格直接印刷口径）
- #45: Dang 2020 H2/CO2 = 73/24 = 3.0416667，原文印的是 H2/CO2/N2 = 73/24/3。
- #79: Chen 2019 H2/CO2 = 66/22 = 3，原文印的是 H2/CO2/N2 = 66/22/12。
- #85、#90: Ruiz Esquius 2020 H2/CO2 = 60/20 = 3，原文印的是20% CO2、20% N2、60% H2。
- #95、#96: Ota 2012 Table 2原文给CO2:H2=1:3，H2/CO2=3为倒置表达，数值等价。
- #40: Frei 2019 的9.7% CO2 conversion 在Fig.6邻近正文，**不是Table 2**，Table 2没有CO2 conversion列。
- #93: Ota 2012主文实验方法写 methane selectivity **less than 0.1%**；CSV原始qualifier为`<`，Excel不显示。该上限不是Table 2中PdZnAl的独立等号实测。必须恢复`<`字段并更正出处。
- #99: Ota Table 2为 **MeOH rate=0.3 µmol/(gcat·min)**；数值相符，字段`STY (printed)`需标注原始量纲与源列名。

此外，#17 Meng 2021 的0.4% CH4在SI Table S2中确为印刷数值；Gao 2015的Table6、Rui 2017的SI S1/S2、Chen 2019的SI S1、Ruiz Esquius 2020的SI S2–S4均可直接核对。

## 其他源文件审计注意
- Malik 2018 主文Table6 p8给0.5Ca5P5ZC XCO2=7.7%，正文评价段给7.6%；这是原文内部差异，**不是本次100项抽样的对应转换率字段**。
- Bansode 2013 SI的压力水平是0.4、3、10、36 MPa；不能写作等数字bar。此次100条中的Bansode字段没有压力，因此**100项通过并未排除外部数据集中压力单位错误**。
- Frei 2019 500 h稳定性序列初始选择性75%和Table2的78%对应不同报道语境，不能把两者强制合并。
- 基于旧脚本的分层抽样：10篇论文×每篇10值。100/100仍属于冻结S5的310条有效比较候选，但并非重新按310条抽样。条件字段重复，样本不满足简单独立伯努利。

## 签署与发表口径
这是**AI辅助原文复核**；未伪造独立人类验证或人工签名。论文中可报告“我们对100个原始文献字段做了来源逐项审计，抽取数值未发现直接矛盾，但标出了六个推导比值、一个限定上界、一个原文定位错误和一个计量标签问题”，不得直接写成“100/100原文直接印刷正确”或“数据库总体准确率100%”。

## 关键源文件及SHA256
| DOI对应主/补充材料 | Drive链接 | SHA256 |
|---|---|---|
| Malik-main | [原文PDF](https://drive.google.com/file/d/1--kU_GkfzNu3dB71N5o_RA6ri2lVgEcj/view) | `58e4e1e6d1ae981bc27217fd90ac31d34660d313ce095820052e13d7c065e1ab` |
| Meng-main | [原文PDF](https://drive.google.com/file/d/1R7gbS2sdMmPWvqKsrC6fKUXSedvwZfwe/view) | `c227d1c10d8ff9c77df8e7a2b1466afeb6e2aa272c436fcb2db7e55e2e5bbb37` |
| Meng-SI | [原文PDF](https://drive.google.com/file/d/1w4nbo1f-SQjZ1_mP63Uc7HuFbekYMUyA/view) | `ebff6b65cec05a24ea067333c5cb805b9dcc83408f1205ac2781c578bde9b866` |
| Bansode-main | [原文PDF](https://drive.google.com/file/d/1mHfxFIRroGBoD_rc-z2M0IDdER6fIXCu/view) | `054321b0b5a4205745554b74263095b1d7e7da947bf51c24b395fc1c8b8e66f4` |
| Bansode-SI | [原文PDF](https://drive.google.com/file/d/1vAP6iNS7sXYNV2z9__QqhMEJt5o0Rllo/view) | `9a45c3d5c0555001a60b3b6485b3a9799500a57079fc266f8cdf0562ad5ebcf0` |
| Frei-main | [原文PDF](https://drive.google.com/file/d/1SpUJIHvYqa2nrDV6DeXCxRVpO02YyOJ1/view) | `ee86dd4c833be2702f5e825c66a6dd3b1cc8c609bd9cc441ee955a26b3cd5330` |
| Dang-main | [原文PDF](https://drive.google.com/file/d/1JtMfT_rmaSxPBxw9ruJKSfhUJnyYMn_-/view) | `3d5da02d49915def0108f56f6123b1ca1800e65b600dd725e62976e16d76c001` |
| Gao-main | [原文PDF](https://drive.google.com/file/d/1GvzHIPGbmfYxz-tsqbDLSeqcKO2SJdg_/view) | `e614d670a66fff90bbd3335c090e5ea6684d3878219e2f4ef82fb3a6dbde0f17` |
| Rui-main | [原文PDF](https://drive.google.com/file/d/1DEiVdM2jAEkQfVRPNXrNGIaDkYmHYJJI/view) | `364513a2b867a26d104e502c3ae8503d3a7c38aef5a592fccffa29cc937baf43` |
| Rui-SI | [原文PDF](https://drive.google.com/file/d/1AIgTxerbhuj424LzfNw0_t3wwBf0Iu3I/view) | `11f8f70b20cde4f9240f45948ebd9defe54bc22db1b4f40da0efd9ac323c52dc` |
| Chen-main | [原文PDF](https://drive.google.com/file/d/1KWB194YdzohFxLovrjrNmdHyvch8n70q/view) | `84885c9b5347bdf321cfb342c5d3b171245f051b72f0cdec173551fb81b08b41` |
| Chen-SI | [原文PDF](https://drive.google.com/file/d/1BfPoG96bC3lh69paQTz4qlQDV83XHTdg/view) | `28de9ff027971d177773816fc9cc1e8a9e15485eb853b79fddb0085b349fd148` |
| Ruiz-main | [原文PDF](https://drive.google.com/file/d/1KbcBNcn6Fu7BYiqMz1i33vxyVC5fyj1R/view) | `940fa897226c94da235dcd577a399b06494f3c01b4aeaf87b2e2524c7c6c75d9` |
| Ruiz-SI | [原文PDF](https://drive.google.com/file/d/1UGQFZ9fnewpti0zvdYyWSXMRrpTxP5qR/view) | `4f24221d4806514e846c73139d2d2628e34fae727a401b9b85e1451ff27d812a` |
| Ota-main | [原文PDF](https://drive.google.com/file/d/1GyR6wSTnSFGhsz4xd2mT6pW_gvLdq-ZD/view) | `f4e6a0fb755e2b61dc77aed734014bc754e90c277a5e47b9e1767a0aaeffc16b` |

## 产物
- Excel: `甲醇金标准100项_GoogleDrive原文再审核_2026-10-12.xlsx` （原始核对表保留不变，新表包含100条原始数字、变换公式、匹配结果、精确页码和原件SHA256）
