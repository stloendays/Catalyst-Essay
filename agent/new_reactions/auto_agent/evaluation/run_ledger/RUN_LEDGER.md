# AI 建模运行账本（原始数据）

由 `run_ledger.py` 从各运行目录的 `ledger.json`、`stage_ledger.csv`、`records.csv` 自动生成；逐行明细见 `RUN_LEDGER.csv`，分阶段明细见 `RUN_STAGES.csv`。费用按 gpt-5.5 公开标价折算（输入 token 含重复发送的历史上下文）。

## 按反应和用途汇总

| 用途 | 反应 | 运行次数 | 有效 | 无效 | 运行中 | 总 token（百万） | 折算费用（USD） | 总时长（小时） |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| development | CO2 甲烷化 | 4 | 4 | 0 | 0 | 9.3 | 63 | 3.9 |
| development | 乙醇脱水（试跑） | 1 | 1 | 0 | 0 | 1.3 | 9 | 0.5 |
| development | 丙烷脱氢 | 7 | 6 | 1 | 0 | 9.2 | 69 | 2.9 |
| smoke | 氨分解 | 1 | 0 | 1 | 0 | 0.0 | 0 | 0.0 |
| test | CO2 制甲醇（盲测） | 3 | 3 | 0 | 0 | 15.5 | 90 | 2.5 |
| test | NH3 合成（盲测） | 6 | 3 | 3 | 0 | 43.5 | 252 | 5.1 |
| test | 氨分解 | 6 | 1 | 4 | 1 | 96.4 | 521 | 15.0 |
| 合计 | | 28 | | | | 175.3 | 1,005 | 29.8 |

## 逐次运行

| 运行 | 反应 | 用途 | 建模版本 | 结论 | 模型 / 路由 | 轮数 | 输入 token | 输出 token | 审查 token | 折算 USD | 时长 min | 论文 / 记录 / 催化剂 | 主要元素（记录数） |
|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---|---|
| ch4_db | CO2 甲烷化 | development | db/lean/full mode | valid | gpt-5.6-sol / api-yes | 28 | 1,045,995 | 24,769 | 0 | 6.0 | 10.3 |  |  |
| ch4_b1 | CO2 甲烷化 | development | V2-flowsheet | valid | gpt-5.5 / api-yes-xiexiu | 65 | 2,860,373 | 242,115 | 0 | 21.6 | 75.4 | 15 / 339 / 64 | Ni:253 Co:60 Mn:47 Ru:46 Ce:28 Cu:14 Al:13 S:11 La:5 C:4 |
| ch4_b2 | CO2 甲烷化 | development | V2-flowsheet | valid | gpt-5.5 / api-yes-xiexiu | 62 | 2,527,628 | 171,421 | 0 | 17.8 | 77.1 | 15 / 213 / 66 | Ni:174 Fe:25 Mg:18 Ru:15 Co:13 Ce:6 Cu:1 Zn:1 Mn:1 |
| ch4_b3 | CO2 甲烷化 | development | V2-flowsheet | valid | gpt-5.5 / api-yes-xiexiu | 52 | 2,243,199 | 212,440 | 0 | 17.6 | 68.2 | 16 / 280 / 62 | Ni:204 Ru:78 Mn:39 Fe:26 S:13 Ce:10 La:5 Ci:4 G:4 C:1 |
| trial_etoh | 乙醇脱水（试跑） | development | db/lean/full mode | valid | gpt-5.6-sol / api-yes | 40 | 1,145,404 | 110,119 | 0 | 9.0 | 28.4 | 4 / 108 / 19 | Al:42 Zr:12 La:6 |
| pdh_db | 丙烷脱氢 | development | db/lean/full mode | valid | gpt-5.6-sol / api-yes | 21 | 764,056 | 24,884 | 0 | 4.6 | 9.8 |  |  |
| lean_trial_pdh | 丙烷脱氢 | development | db/lean/full mode | valid | gpt-5.5 / advisor-openai | 7 | 141,961 | 36,748 | 0 | 1.8 | 6.0 | 6 / 38 / 23 | Zn:24 Pt:14 Mn:6 Mg:5 Ti:4 Cu:4 La:2 Y:2 Ce:2 Ga:1 |
| pdh_build1 | 丙烷脱氢 | development | V1 | invalid: status finished, model_check passed=False | gpt-5.5 / api-yes-xiexiu | 36 | 1,405,869 | 207,935 | 0 | 13.3 | 24.2 | 19 / 270 / 166 | Zn:119 Pt:101 Ga:71 Co:17 Ti:15 K:13 Fe:11 P:11 Mg:10 Vi:10 |
| pdh_b1 | 丙烷脱氢 | development | V1 | valid | gpt-5.5 / api-yes-xiexiu | 38 | 1,454,646 | 199,342 | 0 | 13.2 | 39.0 | 19 / 260 / 141 | Zn:118 Pt:111 Ga:57 Mg:25 Co:18 Ti:16 K:14 Sn:14 P:11 Fe:10 |
| pdh_b2 | 丙烷脱氢 | development | V1 | valid | gpt-5.5 / api-yes-xiexiu | 38 | 1,284,100 | 135,007 | 0 | 10.5 | 17.7 | 13 / 155 / 104 | Zn:73 Pt:38 Ga:18 In:18 Ti:15 Fe:14 P:14 Mg:10 Sn:10 Mn:6 |
| pdh_b3 | 丙烷脱氢 | development | V1 | valid | gpt-5.5 / api-yes-xiexiu | 49 | 1,758,354 | 146,387 | 0 | 13.2 | 32.2 | 18 / 155 / 87 | Pt:67 Zn:47 Ga:29 Fe:17 Co:13 Cu:13 Sn:8 Al:8 In:7 K:5 |
| pdh_v2_d1 | 丙烷脱氢 | development | V2-flowsheet | valid | gpt-5.5 / api-yes-xiexiu | 44 | 1,515,533 | 163,629 | 0 | 12.5 | 42.8 | 15 / 179 / 98 | Zn:99 Pt:84 Sn:24 In:17 Ti:14 Mg:13 Fe:11 P:11 Ca:7 Mn:6 |
| smoke_v3_nh3dec | 氨分解 | smoke | V3-five-layer | invalid: harness smoke test (4 turns), no model | gpt-5.6-sol / api-yes-personal | 4 | 44,731 | 3,399 | 0 | 0.3 | 1.4 |  |  |
| meoh_b1 | CO2 制甲醇（盲测） | test | V3.1-five-layer | valid | gpt-5.6-sol / api-yes-xiexiu | 89 | 4,824,857 | 210,108 | 23,660 | 30.4 | 65.5 | 16 / 281 / 128 | Cu:99 Zn:77 In:74 Pd:49 Ni:46 Co:44 Sn:22 Ru:16 Ce:14 Cr:12 |
| meoh_b2 | CO2 制甲醇（盲测） | test | V3.1-five-layer | valid | gpt-5.6-sol / api-yes-xiexiu | 86 | 5,553,354 | 134,528 | 26,253 | 31.8 | 44.2 | 14 / 104 / 62 | Zn:60 Cu:54 Zr:27 Pd:23 Pt:9 In:4 Ru:2 Re:1 Co:1 Au:1 |
| meoh_b3 | CO2 制甲醇（盲测） | test | V3.1-five-layer | valid | gpt-5.6-sol / api-yes-xiexiu | 84 | 4,555,551 | 166,359 | 23,416 | 27.8 | 39.2 | 15 / 200 / 98 | Cu:59 Co:54 Pd:52 In:31 Zn:16 Ru:15 Pt:13 Zr:12 Ni:8 Mo:8 |
| nh3_b1_stopped_140turns | NH3 合成（盲测） | test | V3.1-five-layer | invalid: stopped during extraction before A2 (started with 140 turns); not evaluated | gpt-5.6-sol / api-yes-xiexiu | 29 | 1,085,381 | 193,110 | 0 | 11.2 | 25.6 | 15 / 344 / 117 | Ru:215 Ba:45 Fe:39 Ni:33 Ce:31 Co:29 Mo:12 Cs:11 U:9 Re:6 |
| nh3_b2_stopped_140turns | NH3 合成（盲测） | test | V3.1-five-layer | invalid: stopped during extraction before A2 (started with 140 turns); not evaluated | gpt-5.6-sol / api-yes-xiexiu | 35 | 1,483,479 | 188,384 | 0 | 13.1 | 20.9 | 18 / 303 / 87 | Ru:112 Fe:79 Co:63 Ni:41 Ba:41 Cs:30 Ce:14 K:14 Mo:14 Na:9 |
| nh3_b3_stopped_140turns | NH3 合成（盲测） | test | V3.1-five-layer | invalid: stopped during extraction before A2 (started with 140 turns); not evaluated | gpt-5.6-sol / api-yes-xiexiu | 12 | 516,696 | 159,341 | 0 | 7.4 | 17.5 | 15 / 283 / 98 | Ru:102 Co:88 Ba:68 Si:50 Fe:46 Ni:39 La:37 Ce:18 Cs:13 Ca:11 |
| nh3_b1 | NH3 合成（盲测） | test | V3.1-five-layer | valid | gpt-5.6-sol / api-yes-xiexiu | 181 | 12,336,807 | 299,877 | 24,229 | 70.7 | 72.6 | 14 / 445 / 85 | Ru:233 Fe:124 Cs:75 Co:54 Ce:53 Ba:49 Ks:22 K:22 Al:18 Ca:18 |
| nh3_b2 | NH3 合成（盲测） | test | V3.1-five-layer | valid | gpt-5.6-sol / api-yes-xiexiu | 140 | 8,211,652 | 289,974 | 27,981 | 49.8 | 59.9 | 17 / 449 / 123 | Ru:244 Fe:79 Co:55 Ba:44 La:42 Cs:33 Nd:32 Ce:20 Sc:17 K:14 |
| nh3_b3 | NH3 合成（盲测） | test | V3.1-five-layer | valid | gpt-5.6-sol / api-yes-xiexiu | 218 | 18,426,801 | 267,796 | 24,168 | 100.2 | 112.2 | 14 / 306 / 75 | Ru:149 Fe:59 Ba:52 K:44 Co:33 Ni:31 Cs:28 Nd:28 Sc:17 Y:2 |
| nh3dec_b1 | 氨分解 | test | V3.1-five-layer | invalid: stopped by the operator at turn 137/140, hung in a fixed tool (before A3) | gpt-5.6-sol / api-yes-xiexiu | 138 | 9,793,217 | 282,586 | 23,933 | 57.4 | 85.0 | 12 / 476 / 90 | Co:187 Ru:128 Ni:124 K:74 Li:50 Ce:36 Ba:15 Yp:7 Fe:7 La:6 |
| nh3dec_b2 | 氨分解 | test | V3.1-five-layer | invalid: turn limit 140 in atomic_model | gpt-5.6-sol / api-yes-xiexiu | 140 | 10,822,336 | 307,190 | 24,799 | 63.3 | 75.1 | 12 / 530 / 73 | Co:247 Ru:137 K:105 Li:66 Ni:53 Ba:17 Fe:15 Na:15 Y:7 Mg:1 |
| nh3dec_b3 | 氨分解 | test | V3.1-five-layer | invalid: turn limit 140 in report | gpt-5.6-sol / api-yes-xiexiu | 140 | 11,890,900 | 233,820 | 0 | 66.5 | 86.9 | 11 / 382 / 47 | Co:152 Ni:109 Ru:60 Li:50 Fe:15 La:6 Ce:1 Ba:1 Pd:1 |
| nh3dec_b4 | 氨分解 | test | V3.1-five-layer | invalid: stopped by the operator at turn 288/300 after about 3 h inside one fixed tool (A2 code, no tool deadline) | gpt-5.6-sol / api-yes-xiexiu | 288 | 24,877,980 | 265,778 | 27,502 | 132.4 | 164.4 | 9 / 332 / 86 | Co:164 Ru:142 K:62 Ce:58 Ba:23 Ni:21 Mo:5 Fe:4 La:4 Li:3 |
| nh3dec_b5 | 氨分解 | test | V3.1-five-layer | valid | gpt-5.6-sol / api-yes-xiexiu | 219 | 15,909,180 | 268,935 | 43,694 | 87.6 | 195.3 | 12 / 356 / 116 | Ru:192 Co:132 K:110 Ni:84 Ce:26 Cs:20 La:11 Ga:10 Ba:5 Mo:5 |
| nh3dec_b6 | 氨分解 | test | V3.1-five-layer | running | gpt-5.6-sol / api-yes-xiexiu | 272 | 21,381,005 | 228,809 | 24,771 | 113.8 | 292.0 | 11 / 248 / 82 | Co:78 Ru:75 K:66 Li:52 Ni:47 Ba:24 Pd:21 Fe:13 Mo:13 Ce:12 |
