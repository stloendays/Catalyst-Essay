# DISCOVER-V2-STOP results (2026-09-26 11:01Z; 180 runs; frozen scorer V1)

| arm | CU | n | full | winner | reach | parity | median spent | median armed-at | paid after arm | median / max post-arm CU | rejections | S3' at stop | FP S3' | narrow | stop modes | C1 full / median spent / parity |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|---|---|
| anytime | 75 | 20 | 20 | 20 | 20 | 15 | 73.5 | 70.5 | 8 | 0.0 / 31.0 | 0 | 11 | 0 | 20 | {"self_stop": 20} | 20/20 / 70.0 / 9 |
| anytime | 225 | 20 | 20 | 20 | 20 | 18 | 158 | 152 | 2 | 0.0 / 114.0 | 0 | 20 | 0 | 16 | {"self_stop": 20} | 20/20 / 218.0 / 20 |
| anytime | 5000 | 20 | 20 | 20 | 20 | 20 | 216 | 216 | 0 | 0.0 / 0.0 | 0 | 20 | 0 | 4 | {"self_stop": 20} | 20/20 / 714.0 / 20 |
| gate | 75 | 20 | 19 | 20 | 19 | 9 | 72.5 | 71.5 | 5 | 0.0 / 26.0 | 0 | 4 | 0 | 20 | {"self_stop": 20} | 20/20 / 70.0 / 9 |
| gate | 225 | 20 | 20 | 20 | 20 | 19 | 218 | 218 | 0 | 0.0 / 0.0 | 0 | 18 | 0 | 3 | {"self_stop": 20} | 20/20 / 218.0 / 20 |
| gate | 5000 | 20 | 20 | 20 | 20 | 20 | 419 | 419 | 0 | 0.0 / 0.0 | 1 | 20 | 0 | 0 | {"self_stop": 20} | 20/20 / 714.0 / 20 |
| hard | 75 | 20 | 19 | 20 | 19 | 11 | 71 | 71 | 0 | 0.0 / 0.0 | 0 | 4 | 0 | 20 | {"forced_stop": 20} | 20/20 / 70.0 / 9 |
| hard | 225 | 20 | 20 | 20 | 20 | 20 | 218 | 218 | 0 | 0.0 / 0.0 | 0 | 20 | 0 | 0 | {"forced_stop": 20} | 20/20 / 218.0 / 20 |
| hard | 5000 | 20 | 20 | 20 | 20 | 20 | 566 | 566 | 0 | 0.0 / 0.0 | 0 | 20 | 0 | 0 | {"forced_stop": 20} | 20/20 / 714.0 / 20 |

## Preregistered gates

- completion_>=19/20_every_cell: **True**
- post_rule_median_0_hard_75: **True**
- post_rule_median_0_hard_5000: **True**
- post_rule_median_0_gate_75: **True**
- post_rule_median_0_gate_5000: **True**
- S3prime_false_positive_0: **True**
- allowance_invariance_anytime_|225-75|<=25: **False**
