# AI 建模运行账本（原始数据）

由 `run_ledger.py` 从各运行目录的 `ledger.json`、`stage_ledger.csv`、`records.csv` 自动生成；逐行明细见 `RUN_LEDGER.csv`，分阶段明细见 `RUN_STAGES.csv`。费用按 gpt-5.5 公开标价折算（输入 token 含重复发送的历史上下文）。

## 按反应和用途汇总

| 用途 | 反应 | 运行次数 | 有效 | 无效 | 运行中 | 总 token（百万） | 折算费用（USD） | 总时长（小时） |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| development | CO2 甲烷化 | 3 | 3 | 0 | 0 | 16.1 | 96 | 7.8 |
| 合计 | | 3 | | | | 16.1 | 96 | 7.8 |

## 逐次运行

| 运行 | 反应 | 用途 | 建模版本 | 结论 | 模型 / 路由 | 轮数 | 输入 token | 输出 token | 审查 token | 折算 USD | 时长 min | 论文 / 记录 / 催化剂 | 主要元素（记录数） |
|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---|---|
| ch4_v31_t1 | CO2 甲烷化 | development | V3.1-five-layer | valid | gpt-5.6-sol / api-yes-personal | 102 | 5,190,644 | 209,108 | 25,847 | 32.2 | 61.5 | 14 / 270 / 52 | Ni:244 Ru:51 Mn:29 Fe:27 Ce:22 Mg:2 Ca:2 No:1 |
| ch4_v32_t2 | CO2 甲烷化 | development | V3.2-five-layer | valid | gpt-5.6-sol / api-yes-personal | 74 | 3,185,351 | 214,490 | 21,767 | 22.4 | 254.4 | 14 / 300 / 79 | Ni:237 Ru:55 Fe:43 Mn:35 Mg:13 La:5 C:5 Co:1 Cu:1 Zn:1 |
| ch4_v33_t3 | CO2 甲烷化 | development | V3.3-process-design | valid | gpt-5.6-sol / api-yes-personal | 211 | 7,032,699 | 192,756 | 47,958 | 41.0 | 150.6 | 13 / 156 / 41 | Ni:135 Ce:42 Ru:25 Fe:24 Al:10 Mn:4 Ci:3 La:2 Co:1 Cu:1 |
