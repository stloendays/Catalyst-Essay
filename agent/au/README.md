# ACSA: supported-Au CO-oxidation chain and self-check

The third hand-built case (Au/TiO₂ particle-size control) taken through the agent, as ammonia and methanol already are.

| File | What it does |
|---|---|
| `au_chain.py` | The agent's chain for supported-Au candidates: anchor rate → size-scaled mass activity → required catalyst mass at the reference conversion (pseudo-first-order plug flow) → burden, rank metrics, the 10,000-draw literature envelope and the semi-open operating windows. `self_check(inputs)` compares against the frozen hand-built results: `data/rank_preservation_control_v1_1.csv` (20 cells at their stored precision), the envelope (10,000/10,000 preserved) and `data/rank_preservation_semiopen_v1_3_summary.csv` (6 windows). |
| `extract_au_params.py` | Extraction agent (gpt-5.5 through API-YES, strict JSON schema, prompt contains only the paper) for the catalyst inputs: Janssens et al. 2006 (doi:10.1016/j.jcat.2006.03.008) for the absolute-rate anchor, Overbury et al. 2006 (doi:10.1016/j.jcat.2006.04.018) for the TOF–size exponent. Units are normalized and the protocol's selection rules pick the anchor sample (the Au/TiO₂ sample with a reported rate) and the size series (Au loading closest to the anchor loading). Writes `out/inputs_extracted.json`, `out/inputs_vs_handbuilt.csv`, `out/selfcheck_au_extracted.json`. |
| `dois_au.txt` | The two source DOIs. PDFs go to `pdf/` (git-ignored; ScienceDirect needs `nus_fetch.py manual` / `collect`). |

Protocol constants (candidate diameters 2–6 nm, dispersion-geometry exponent, molar volume, Monte Carlo ranges and seeds)
are not extracted; they are read from `controls/au_tio2_rank_preservation_v1_1_config.json`.

Dispersion enters the chain only as a ratio to the anchor dispersion, so output reproduction cannot detect a wrong
dispersion value. The gate therefore also requires every extracted input to equal the hand-built value. Perturbing the
TOF exponent to 0.92, the anchor rate to 8.9 µmol g⁻¹ s⁻¹ or the catalyst mass to 21.5 mg fails the output check
(19, 5 and 10 of 20 cells).

## Gate

`agent/selfcheck_gate.py` runs the three self-checks (ammonia pure metals, methanol Gothe Table 4, Au/TiO₂ hand-built
and extracted) and writes `agent/selfcheck_report.json`. `run_alloy_chain.py`, `run_alloy_backward.py`, `run_literature_inversion.py` and `run_meoh_pruning.py` call
`require()` first, so no new candidate is scored unless all three pass.

## Result (2026-10-06)

gpt-5.5 through API-YES, one call per paper (Janssens: 3 samples, 20.0k tokens, 39 s; Overbury: 12 samples and 2
size series, 36.1k tokens, 148 s). The selection rules pick the Au/TiO₂ sample of Janssens and the 4.5 wt% series of
Overbury (TOF ∝ d^−0.9±0.2).

| Input | Extracted | Hand-built |
|---|---:|---:|
| average Au diameter | 2.10 nm | 2.10 nm |
| Au loading | **4.41 wt%** (p. 2, Experimental) | 4.40 wt% (p. 4, Table 1) |
| dispersion | 38 % | 38 % |
| stabilized rate | 8.8 µmol g⁻¹ s⁻¹ | 8.8 |
| catalyst mass / flow | 21.4 mg / 214.4 Nml min⁻¹ | same |
| CO fraction / temperature | 1 % / 273.15 K | same |
| TOF size exponent ± | 0.9 ± 0.2 | 0.9 ± 0.2 |

The paper prints the Au/TiO₂ loading twice with different values (and 4.08 vs 4.10 wt% for Au/MgAl₂O₄). The gate
accepts a differing input only when `out/source_discrepancies.json` locates both printed values in the paper, and
then accepts output differences only in the column that depends on that input alone: the required Au mass, 0.2 %
higher, equal to the frozen catalyst mass × 4.41 wt%. Catalyst masses, burdens, order, ρ = τ = 1, the 10,000/10,000
envelope and all six semi-open windows reproduce exactly. Gate: PASS for NH3, MeOH and Au/TiO₂
(`agent/selfcheck_report.json`).
