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
and extracted) and writes `agent/selfcheck_report.json`. `run_alloy_chain.py` and `run_literature_inversion.py` call
`require()` first, so no new candidate is scored unless all three pass.
