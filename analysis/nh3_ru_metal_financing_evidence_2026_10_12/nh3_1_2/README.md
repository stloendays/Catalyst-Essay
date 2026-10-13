# Ru metal financing at documented rates on NH3-FINAL-1.2

The four files here are the NH3-FINAL-1.2 counterparts of the files one level up (same names and columns, except the
two classification columns, whose names carry the parity threshold of the model: `owned_vs_12p33_threshold`,
`lease_vs_12p31_threshold`; 1.1: `owned_vs_0p56_threshold`, `lease_vs_0p92_threshold`). `summary.json` has an extra
`model` block. The documented rates (`documented_rates.csv`, `pbf_catalyst_lease_contracts.csv`) and `EVIDENCE.md`
are data and unchanged.

```
set NH3_MODEL=1.2
set NH3_HARNESS_1_2=D:\论文-AI4S\wt-nh3-12\provenance\nh3_final_1_2\source_harness
D:\Research\CatalystForge\.venv\Scripts\python.exe analysis\nh3_ru_metal_financing_evidence_2026_10_12\run_documented_rates.py
```

It reads `analysis/nh3_ru_net_recovery_boundary_2026_10_12/nh3_1_2/` (PR #57 on 1.2, branch `port/nh3-1-2-dcf`),
so run that folder's `run_boundary.py` and `run_lifecycle_cashflow.py` with `NH3_MODEL=1.2` first. About 15 s.

## Checks

- The cached 1.2 response surface is read directly (never rebuilt); the Fe and Ru feasible optima of `results.json`
  (11.515783597179267 / 16.632749358902807 USD/t) are reproduced to 1e-9.
- All 378 rows of PR #57 `nh3_1_2/lifecycle_finance_sensitivity.csv` are reproduced within 1e-9 USD/t, the 12 %
  flagship (Ru 16.987 vs Fe 16.999 USD/t), and PR #57's 1.2 financing hurdle 12.3329 %/y to 1e-9.
- PR #61 has no 1.2 run, so its 0.92 %/y lease anchor is checked under 1.1 only. Under both models the lease at a rent
  equal to the 12 % plant rate reproduces the owned case at 12 % to 1e-9, and the lease Fe reference equals PR #57's
  12 % Fe.
- With `NH3_MODEL=1.1` the script rewrites the three committed CSVs byte for byte and `summary.json` identically
  after CRLF → LF (`Path.write_text` on Windows; the committed bytes are LF).
- `test_documented_rates.py` checks both summaries (1.1: 0.5604 / 0.92 %/y; 1.2: 12.3329 / 12.31 %/y) against PR
  #57's hurdle of the same model and the below/above classification of every headline rate.

## Re-derived definition (rule 4)

The parity rate keeps its 1.1 definition (the rate at which Ru − Fe = 0 for the flagship bed, owned: metal cash flows
of Ru and Fe at that rate; lease: rent at that rate, operator cash flows at 12 %) and the same bisection on
[0, 12 %] (owned) and [0, 15 %] (lease). Under 1.2 Ru stays at or below Fe at 12 % owned for 93.05 % and 95.55 %
recovery. The partial port's `bisect` returned the bracket end (12 %) as the threshold there; it now moves the bracket
up by its own width until the gap changes sign and bisects there, and raises an error if no sign change occurs below
100 %/y. Under 1.1 no call reaches that branch, so the 1.1 outputs are unchanged.

## Key numbers, NH3-FINAL-1.1 → NH3-FINAL-1.2

Flagship: KAAP-type loop (90 bar, −20 °C), 8 wt % Ru/C, 490 kg/m³, 95.55 % gross recovery, 10-y Ru life, 25-y project;
gap = Ru − Fe in USD/t NH₃ (negative: Ru cheaper).

| Quantity | NH3-FINAL-1.1 | NH3-FINAL-1.2 |
|---|---|---|
| Owned parity rate (flagship) | 0.5604 %/y | 12.3329 %/y |
| Lease (unsecured) parity rent (flagship) | 0.9246 %/y | 12.3140 %/y |
| Owned parity rate at 90 / 93.05 / 95.55 % recovery | none (Ru > Fe at 0 %) / 0.254 / 0.560 %/y | 11.969 / 12.171 / 12.333 %/y |
| Lease unsecured parity rent at 90 / 93.05 / 95.55 % | 0.582 / 0.770 / 0.925 %/y | 11.971 / 12.160 / 12.314 %/y |
| Lease with 25 % collateral at 90 / 93.05 / 95.55 % | none / none / none | 8.971 / 9.160 / 9.314 %/y |
| Lease with refining loss at 90 / 93.05 / 95.55 % | 0.302 / 0.469 / 0.606 %/y | 11.691 / 11.858 / 11.995 %/y |
| Fe in the KAAP loop, 12 % (lease reference) | 19.142 USD/t | 16.999 USD/t |
| Owned at 0 % (Pt implied pre-2020): Ru / Fe (gap) | 18.84 / 19.09 (−0.25) | 16.38 / 16.98 (−0.61) |
| Owned at 0.8 % (Pt 2021 avg) | 19.19 / 19.09 (+0.10) | 16.46 / 16.99 (−0.53) |
| Owned at 1.35 / 2.10 / 5.10 % (PBF min / median / max): gap | +0.34 / +0.66 / +1.48 | −0.48 / −0.41 / −0.26 |
| Lease at 0 / 0.8 %: gap | −0.62 / −0.05 | −0.68 / −0.56 |
| Lease at 1.35 / 2.10 / 5.10 % (PBF): gap | +0.19 / +0.52 / +1.43 | −0.51 / −0.44 / −0.27 |
| Owned / lease at the 12 % plant rate: gap | +2.64 / +2.64 | −0.012 / −0.012 |
| Documented rates (19 levels, 0–30 %/y) below the owned / lease threshold | 1 / 2 (0 % owned; 0 and 0.8 % lease) | 18 / 18 (all but the 30 % Pt lease of July 2025) |
| PBF 32 contracts, 1.35–5.10 %/y, relative to the thresholds | all above both | all below both, by 7.2–10.98 points (owned) |
| KAAP grid, 27 cells, Ru ≤ Fe owned at 0 / 0.8 / 1.35 / 2.10 / 5.10 % | 16 / 0 / 0 / 0 / 0 | 27 / 27 / 27 / 27 / 27 |
| same, lease | 27 / 10 / 0 / 0 / 0 | 27 / 27 / 27 / 27 / 27 |
| KAAP grid gap range, owned at PBF min / median / max | +0.28…+0.76 / +0.60…+1.07 / +1.46…+1.64 | −0.49…−0.39 / −0.43…−0.33 / −0.27…−0.22 |
| KAAP grid gap range, lease at PBF min / median / max | +0.14…+0.49 / +0.47…+0.82 / +1.40…+1.55 | −0.53…−0.45 / −0.46…−0.38 / −0.28…−0.24 |

Under 1.1 every documented industrial all-in rate (PBF 1.35–5.10 %/y) lies above both parity thresholds and Fe stays
cheaper by 0.34–1.48 USD/t (owned) or 0.19–1.43 USD/t (leased). Under 1.2 the same rates lie 7–11 points below both
thresholds and Ru/C is cheaper than Fe in the KAAP loop by 0.26–0.48 USD/t (owned) or 0.27–0.51 USD/t (leased); only
the ≈30 % Pt lease cost of July 2025 lies above them (+0.28 / +0.32 USD/t).
