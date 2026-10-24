# Ammonia within-paper count with each catalyst's plant pressure held near its measured pressure (2026-10-24)

Question (internal review, item 1): the descriptor kinetics behind the 12/44 count give Ru an apparent H₂ order of +2.4
against +0.3 measured, and the plant optimum ranges over 10–1,000 bar. If that bias favours Ru, restricting each catalyst
to pressures near the one its rate was measured at should raise the count, and 12/44 would be conservative.

    set NH3_MODEL=1.2
    D:\Research\CatalystForge\.venv\Scripts\python.exe -X utf8 pressure_window.py   # summary.json, ~2 min

Method: the frozen effective descriptor and residual activity of every primary entry
(`nh3_field_expansion_2026_10_12/nh3_1_2/runs/pooled_vf_screen/candidates_printed.csv`), the same harness cost call
(`run_supported_chain.plant_cost`), with the states limited to P ≤ max(10 bar, k × P_lab). 10 bar is the lowest state
of the process library; laboratory pressures are 1–150 bar (median 10). Gate: unrestricted, every entry reproduces its
frozen cost (max relative deviation 6.3 × 10⁻⁵, from E_eff stored to 5 figures) and the count is 12/44.

| Plant pressure | groups | leader differs | > 5 % | CI 95 % | entries without a feasible state (of 237) |
|---|---:|---:|---:|---|---:|
| 10–1,000 bar (manuscript) | 44 | 12 | 8 | 14–42 % | 0 |
| ≤ max(10 bar, 1 × P_lab) | 4 | 1 | 1 | 0–75 % | 218 |
| ≤ max(10 bar, 2 × P_lab) | 10 | 3 | 3 | 0–67 % | 190 |
| ≤ max(10 bar, 5 × P_lab) | 28 | 7 | 3 | 8–46 % | 94 |
| ≤ max(10 bar, 10 × P_lab) | 30 | 6 | 4 | 7–35 % | 84 |

Same groups, unrestricted count: 1, 2, 6 and 7 of the 4, 10, 28 and 30 groups.

Reading: near their laboratory pressures most catalysts cannot make the plant's output within the 90 m³ bed limit,
so the comparison set collapses. On the groups that remain the fraction (20–30 %) is that of the unrestricted count
(27 %); the restriction neither raises the count nor shows a Ru bias in it. The test does not support calling 12/44
conservative, and the manuscript is unchanged (author decision 2026-10-24: unfavourable results stay in the
repository).
