# Provenance QA of the methanol engineering-survivor papers (unfrozen)

This is a **numerical consistency check of curated source records**, not a claim of independent human inspection of every original article, supplementary table, or plot. It does not change the original data.

The checker reads the committed \`agent/extraction/out/records_normalized.csv\`, the completed joint m-p result and the completed engineering-envelope result. It records remaining source defects or unverified items as **explicit machine-readable flags**.

| DOI | Check against accessible main text | Outstanding issue |
| --- | --- | --- |
| 10.1021/acscatal.5c05984 | Re/TiO2, 1 vs 5 wt%, Table 4 rows 3 and 11: 55 and 18 g MeOH/gRe/h. Convert using 1 and 5 wt% to 0.55 and 0.90 g MeOH/gcat/h, respectively. Same 200 C, 100 bar, H2/CO2=4. | The paper's '<1%' selectivity entries are reporting limits, not exact zero. Reactor extrapolation unvalidated. |
| 10.1126/sciadv.abi6012 | InNi3C0.5/m-ZrO2 vs SiO2, Figure 2A 12 NL/gcat/h: X=11.2%, 2.5%, methanol selectivity 85.4%, 90%. Figure 2B 24 NL/gcat/h: printed STY 0.62 vs 0.18 g/gcat/h. 300 C, 40 bar, H2/CO2=3. | Fig. 2A STY is *reconstructed*, not separately printed. The CO/CH4 numerical split from original SI still needs independent source-page recheck. |
| 10.1016/j.jes.2023.05.010 | Curated SI Table S5: bare In2O3-NS 9.15% X, 44.08% methanol selectivity, 0.17 STY; In2O3-HM 5.43%, 53.23%, 0.12 STY, 300 C, 30 bar. | **Not independently verified against original SI.** CO/CH4 not reported. The paper's main article uses Ar or N2 dilution in another series but its bare-control SI record states only H2/CO2=4: whether those controls used 1/6 inert gas dilution remains unresolved. |

The audit also lists other DOIs that appear as material robust survivors **after** introducing equipment limits, which must not inherit provenance validation from these original three papers.

These are source checks and caveat tracking, not a substitute for kinetics/experimental data or vessel hydraulics.

Run from the repository root:

    python analysis/meoh_survivor_source_2026_10_12/audit_survivor_sources.py
