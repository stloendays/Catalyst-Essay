# Methanol leaderboard per gram of Re under NH3-FINAL-1.2

    set NH3_MODEL=1.2
    D:\Research\CatalystForge\.venv\Scripts\python.exe -X utf8 analysis\verify_2026_10_12_metal_basis\metal_basis.py

`metal_basis.py` rescores the frozen methanol S5 and S6 plant costs (`analysis/meoh_literature_inversion_2026_10_05/
literature_candidates.csv`) with Gothe et al. 2025 (10.1021/acscatal.5c05984) ranked per gram of Re. No ammonia model,
harness, response surface or ammonia anchor enters the calculation, so `nh3_1_2/metal_basis_summary.json` is
byte-identical to the 1.1 file `../metal_basis_summary.json` (SHA-256
`937c3bd3ed5c77fc80e16620b6df017c293ad696055ee0adad470c43debfdf41`, both written on 2026-10-13).

| Quantity (methanol literature cohort, 40 groups) | NH3-FINAL-1.1 | NH3-FINAL-1.2 |
|---|---:|---:|
| S5, per g catalyst: different winner / >5 % regret | 15 of 40 / 7 | 15 of 40 / 7 |
| S5, per g catalyst: other catalyst / other temperature | 10 of 32 / 5 of 22 | 10 of 32 / 5 of 22 |
| S5, Gothe ranked per g Re: other catalyst / other temperature (manuscript) | 9 of 32 / 6 of 22 | 9 of 32 / 6 of 22 |
| S5, Gothe 10 NL g⁻¹ h⁻¹ group regret, per g catalyst → per g Re | 1.75 % → 0.52 % | 1.75 % → 0.52 % |
| S6, per g catalyst: different winner / >5 % regret | 28 of 40 / 22 | 28 of 40 / 22 |
| S6, per g catalyst: other catalyst / other temperature | 16 of 32 / 12 of 22 | 16 of 32 / 12 of 22 |
| S6, Gothe ranked per g Re: other catalyst / other temperature | 15 of 32 / 13 of 22 | 15 of 32 / 13 of 22 |
| S6, Gothe 10 NL g⁻¹ h⁻¹ group regret, per g catalyst → per g Re | 8.18 % → 6.61 % | 8.18 % → 6.61 % |
