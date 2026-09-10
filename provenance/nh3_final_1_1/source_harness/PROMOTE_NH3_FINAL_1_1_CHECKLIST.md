# PROMOTE NH3-FINAL-1.1 — promotion diff / checklist (PHASE B, 2026-09-05)

Status: **prepared, NOT applied.** Canonical is still NH3-FINAL-1.0. PHASE A audit = PASS (`PRESSURE_CAPEX_INDEPENDENT_AUDIT_2026-09-05.md`).

## 1. Reproducibility confirmations

| check | result |
|---|---|
| 1.0 with `pressure_capex` absent, after the patch | deterministic block bit-identical to the pre-patch Windows run `outputs/nh3_final_20260904T072819Z` (all 15 metals, both cost blocks, ρ values); ≤ 1e-8 relative to the Linux-built frozen run `nh3_final_20260903T092000Z` (libm rounding, 1e-14); canonical smoke gate PASS `outputs/nh3_final_20260905T113652Z`; `tests/test_pressure_capex.py::test_canonical_1_0_is_bit_identical` pins this; 27/27 tests pass |
| 1.1 enabled, two independent full runs (`nh3_final_1_1_20260905T113727Z`, `nh3_final_1_1_20260905T_repro`) | deterministic identical: True; monte_carlo identical: True; backward identical: True; response cache sha identical: True; second run gated against the filled `frozen_regression` → **PASS** |
| independent arithmetic | every cost pool of the Fe and Ru optima reproduced to 6 decimals without the harness (audit §1–3) |

## 2. Files that change at promotion (diff)

| file | now | after promotion | action |
|---|---|---|---|
| `configs/nh3_final.yaml` | NH3-FINAL-1.0, sha `cdda440057bda938…` | content of `configs/nh3_final_1.1_candidate.yaml` with `run_label: nh3_final` (non-frozen key; keeps run-dir naming and `_canonical_baseline` glob) | copy 1.0 to `_backup/<ts>/` **and** `configs/nh3_final_1.0_archived.yaml`; then overwrite |
| `configs/nh3_final_1.1_candidate.yaml` | candidate, sha `278a74d5c6b04369…`, `frozen_regression` filled from run 113727Z | unchanged (kept as the promotion source) | none |
| `harness_core.py`, `run_all.py`, `agent/commands.py::COST_BREAKDOWN` | already 1.1-capable; 1.0 path bit-identical | unchanged | none |
| `tests/frozen_hashes.json` | pins `configs/nh3_final.yaml` = `cdda440057bda938…`, `outputs/nh3_final_20260903T092000Z/results.json`, `…/manifest_resolved.yaml` | pin the new canonical manifest sha, the archived 1.0 sha, and the **new canonical full run** (`results.json`, `manifest_resolved.yaml`) | update after the canonical run, with a dated note and previous hashes |
| `tests/test_manifest.py` | asserts model_version == NH3-FINAL-1.0 | NH3-FINAL-1.1 + `pressure_capex.enabled` + pressure stop 1000 | edit |
| `tests/test_pressure_capex.py` | 1.0 bit-identity test reads `configs/nh3_final.yaml` | read `configs/nh3_final_1.0_archived.yaml` | edit |
| `tests/test_eligibility.py` | reads 1.0 run; asserts Ru on the P = 300 grid edge (`test_operating_window_uses_grid_edge`) | on 1.1 Ru is interior (425 bar): the upper-bound lever is `inactive_constraint`; bed slack Fe 90 − 17.06 = 72.9 m³ (no longer near-binding) | rewrite the two assertions from 1.1 facts (PHASE C item 13) |
| `tests/test_leverage.py` | reads 1.0 run + `outputs/sens_*` (1.0 sweeps) | keep as 1.0-legacy regression (paths to archived run) **or** regenerate from 1.1 sweeps in PHASE C | decide in PHASE C |
| `CURRENT_STATE.md` | 1.0 headline lines | 1.1 headline lines (table below) | edit with backup |
| `agent/commands.py` `frozen_principles` | "model_version NH3-FINAL-1.0", "P 10-300 bar" | "NH3-FINAL-1.1", "P 10-1000 bar", "pressure CAPEX on" | edit (this string is shown to the agent in DIAGNOSE_DRIFT) |
| `agent/run_agent.py` SYSTEM prompt, `--scripted strategy` (2171.56), `agent/diagnose.py`, `agent/strategy.py`, `agent/extrapolate.py` prompt text | name NH3-FINAL-1.0 | NH3-FINAL-1.1; scripted multiplier read from the run instead of a literal | edit; prompts otherwise frozen |
| `agent/reaction_case.py` (`build_nh3` default run) and `cases/reaction_cases/nh3_final_1.0.json` | anchor from 1.0 | new anchor `cases/reaction_cases/nh3_final_1.1.json` from the new canonical run; 1.0 anchor kept | regenerate (PHASE C item 16) |
| `benchmark/drift_v2/make_v2.py` `CANON_RUN`, `benchmark/cases.json`, `benchmark/ground_truth.json`, `benchmark/drift_v2/{cases,ground_truth}.json` | derived from the 1.0 manifest/run | regenerate on 1.1 (new case dirs; old v1/v2 scores become 1.0-legacy and are not comparable) | PHASE C item 14 |
| `benchmark/extrapolation_v1/cases/x_case_*.json`, `FROZEN_EXTRAPOLATION_V1.json` | contain 1.0 costs (10.199/17.592/21.321) and "3636 states" | regenerate from the 1.1 anchor via `make_x1.py`; frozen hash list must be re-frozen as extrapolation v1.1 — **no prompt change** | PHASE C; human decision because it resets the frozen benchmark |
| `cache/` | 3636-state cache (1.0) + `cache\response_fc259c5311744ccc_-2.6_3.4_0.005_14136.npz` sha `5c551c84f8668850…` (1.1, 14136 × 1201) | both kept; 1.1 cache is the one reused by canonical full runs | none |
| `scenarios_registry.json` | 15 entries; all `configs/scenarios/*.yaml` except `s11_*` are 1.0-derived | entries kept as history; new scenarios will be copies of the 1.1 canonical | none (append-only) |
| `outputs/LATEST.txt` | points to the last run | will point to the canonical 1.1 full run | automatic |
| Notion 04 / 07 / 12 / 18 / 19, GIST | 1.0 numbers with 2026-09-05 caveat callouts | rewrite in PHASE D | after PHASE C |

## 3. Regression targets that become canonical (exact values from `configs/nh3_final_1.1_candidate.yaml`, confirmed by two runs)

| key | 1.0 | 1.1 |
|---|---|---|
| `process_state_count` | 3636 | 14136 |
| `raw_global_spearman` | 0.9107142857142855 | 0.9285714285714284 |
| `censored_global_spearman` | 0.684172319121686 | 0.684172319121686 |
| `top3_spearman` | -0.5 | -0.5 |
| `feasible_metals` | ['Fe', 'Ru', 'Os'] | ['Fe', 'Ru', 'Os'] |
| `Fe_cost_USD_t` | 10.19865904708462 | 15.291704676621144 |
| `Fe_optimum` | {'T_C': 400.0, 'P_bar': 150.0, 'Tsep_C': 30.0} | {'T_C': 425.0, 'P_bar': 180.0, 'Tsep_C': 30.0} |
| `Ru_cost_USD_t` | 17.59239838038635 | 22.03059478781101 |
| `Ru_optimum` | {'T_C': 450.0, 'P_bar': 300.0, 'Tsep_C': 10.0} | {'T_C': 450.0, 'P_bar': 425.0, 'Tsep_C': 25.0} |
| `Os_cost_USD_t` | 21.32057789728162 | 25.83179725613286 |
| `Os_optimum` | {'T_C': 450.0, 'P_bar': 300.0, 'Tsep_C': -15.0} | {'T_C': 450.0, 'P_bar': 425.0, 'Tsep_C': 0.0} |
| `Fe_feasibility_probability` | 0.736 | 0.799 |
| `Ru_activity_break_even_multiplier` | 2171.559771717808 | 201.2234429878984 |
| `Ru_scaling_max_gain_673K` | 1.089901226752712 | 1.0899012267527077 |
| `Ru_scaling_max_gain_all_states` | 2.432864708218596 | 2.5245651130943445 |
| `Ru_best_scaling_cost_USD_t` | 17.1940362123231 | 21.397872966049547 |

## 4. Procedure on approval (each step reversible; nothing below has been executed)

1. `_backup/<ts>/configs/nh3_final.yaml`; `cp configs/nh3_final.yaml configs/nh3_final_1.0_archived.yaml`.
2. Write the candidate content to `configs/nh3_final.yaml` with `run_label: nh3_final`; `project.model_version` stays `NH3-FINAL-1.1`.
3. `python run_all.py --config configs/nh3_final.yaml --mode full` (no `--scenario`) → must PASS its own gate; this run becomes the pinned canonical run.
4. Re-pin `tests/frozen_hashes.json` (manifest, archived 1.0, new run files) with a dated note; edit `test_manifest.py`, `test_pressure_capex.py`, `test_eligibility.py`; run the suite.
5. Update agent strings (`frozen_principles`, SYSTEM prompt names, scripted multiplier) — text only, no behavioural change.
6. Then PHASE C closure (items 1–16) on the single canonical 1.1 model; only after that PHASE D manuscript numbers.

## 5. Verdict

**可以 promotion** — technically ready: the 1.0 path is bit-preserved, the 1.1 result is bit-reproducible, the audit passed, and every dependent artefact is enumerated above with its action. Two consequences need the human's explicit acceptance before step 1: (a) drift benchmarks v1/v2 and extrapolation v1 must be regenerated on 1.1, so their published scores restart (old scores stay as 1.0-legacy records); (b) the manuscript headline numbers change (Fe 10.199 → 15.292, Ru 17.592 → 22.031, Os 21.321 → 25.832 USD/t; Ru break-even 2171.56× → 201.22×; Fe feasibility 0.736 → 0.799), while ranking, Top-3 ρ, and reachability verdict do not.
