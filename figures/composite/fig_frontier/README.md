# Figure 5 — supported Ru/C against fused iron with measured rate laws

183 × 76 mm, four panels: `FigFrontier.{svg,pdf,png}`. Added 2026-10-21 on the supervisor's guidance of 2026-10-20 (one
Ru/C − Fe cost curve against the financing rate; the Fe-upstream / Ru/C-downstream bed order as its own panel). Fused
iron: Keestra et al. 2025 Model 3 with the Topsoe KM1R (1964) activity (1–324 bar); Ru/C: Rossetti et al. 2006
(50–100 bar); each catalyst optimized only inside its fitted range.

| Panel | Content | Source |
|---|---|---|
| a | Ru/C − Fe against the Ru financing rate, KAAP-type loop (90 bar, −20 °C) and each catalyst at its own optimum; break-evens 4.57 and 6.49 %/y; 32 disclosed catalyst-metal leases (1.35–5.10 %/y) and the reference rate 2.10 %/y (their median) | `analysis/nh3_keestra_consolidation_2026_10_20/financing_curves.csv`; `analysis/nh3_ru_metal_financing_evidence_2026_10_12/pbf_catalyst_lease_contracts.csv` |
| b | three-bed adiabatic converter at 9 MPa: best all-Fe, all-Ru/C, Ru/C-first and Fe-first designs; Fe first optimal 0–5.46 %/y | same `financing_curves.csv`; window from `analysis/nh3_fe_inrange_kinetics_2026_10_19/staged_KM1R_1964_summary.json` |
| c | least-cost converter at 2.10 %/y (FRR: 5.8, 1.2, 1.9 m³; Ru/C 35 % of volume; 17.95 vs 18.32 USD/t all-Fe) | `analysis/nh3_fe_inrange_kinetics_2026_10_19/staged_KM1R_1964_design_library.csv`, costed with `analysis/nh3_staged_converter_2026_10_12/boundary.charges` |
| d | Ru/C (8 wt%) : fused-iron rate per kg and per m³ at 90 bar, 400 °C against NH₃ (9 at 2 %, 62 at 14 % per kg) | `analysis/nh3_fe_inrange_kinetics_2026_10_19/validation.json` |

The renderer asserts the break-evens, the window, that no Ru/C-first design is optimal and that the re-costed design
equals the curve at 2.10 %/y. Build (`boundary.py` needs PyYAML, so the CatalystForge interpreter):

    set NH3_MODEL=1.2
    D:\Research\CatalystForge\.venv\Scripts\python.exe -X utf8 make_fig_frontier.py
