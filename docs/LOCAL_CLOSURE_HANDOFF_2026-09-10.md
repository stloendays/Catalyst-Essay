# Local closure handoff — 2026-09-10

This is the remaining **local-compute** work package after research freeze and C1 integration. It is intentionally narrow.

## Do first — F9A FINAL-1.1 revalidation

Read and execute:

`docs/F9A_FINAL_1_1_REVALIDATION_TASK.md`

Key constraints:

- deterministic calculation only;
- no OpenAI/Claude API calls are required for the science calculation;
- use the frozen local NH3 source harness and `configs/nh3_final.yaml` = NH3-FINAL-1.1;
- identify the exact historical TOF-economic-leverage definition before computing;
- do not infer a new ratio by scaling 273–410 with the change in Fe cost;
- keep denominator fractions fixed at 2%, 2.5%, 3%;
- keep MeOH CH4-suppression leverage fixed at 0.3757939247335326;
- if exact historical metric equivalence cannot be established, stop with `METRIC_EQUIVALENCE_NOT_ESTABLISHED` and keep F9A qualitative-only.

After completion, copy the revalidation bundle into this repository and update:

- `docs/CROSS_REACTION_LEVERAGE_PROVENANCE_POINTER.md`;
- `docs/RESULTS_AT_A_GLANCE.md`;
- `docs/MANUSCRIPT_SKELETON.md` §3.5;
- `docs/FIGURE_MAP.md` F9A;
- `data/canonical_results_2026-09-06.csv`;
- `data/claim_evidence_registry_2026-09-10.csv`;
- `data/figure_lock_registry_2026-09-10.csv`;
- `figures/README.md`.

Do not touch other frozen scientific/Agent results.

## In parallel — render Figure 8 locally

The Figure 8 scientific design is already frozen. Run from the `Catalyst-Essay` repository root:

```bash
Rscript figures/meoh/render_F08_selectivity_recycle.R .
```

Expected outputs:

```text
figures/meoh/F08_MeOH_selectivity_recycle_D01v3.svg
figures/meoh/F08_MeOH_selectivity_recycle_D01v3.pdf
figures/meoh/F08_MeOH_selectivity_recycle_D01v3.png
```

The R script validates:

- exactly 396 purge levels;
- 0.5–40% purge envelope;
- frozen leverage values at 5 wt% Re / 250 C.

After render, generate SHA-256 hashes for the two CSV inputs, R script and three outputs. Visually inspect the SVG/PDF/PNG for clipping, unreadable labels or rendering differences only. **Do not change data, metric, candidate definition or 2% canonical point to improve appearance.** Pure layout/font-size adjustments are permitted if the numeric content and panel meaning remain unchanged.

If the render passes, update the figure registry from `DESIGN_FROZEN_RENDER_PENDING` to `LOCKED`, recording the actual Git blob SHA(s).

## NH3 provenance import after F9A

Once the local source harness is open, also locate the current FINAL-1.1 evidence bundle around:

`outputs/nh3_final_20260905T134204Z`

and its `closure/` subdirectory. Do **not** recompute F1–F6 merely to create new files if the existing canonical outputs are intact. Prefer copying/content-addressing the already frozen outputs and figure-generating data/code with SHA-256 provenance.

Required target: enough direct evidence to move F1–F6 from `HOLD` to lockable without relying only on summary documents.

## Completion report

Return:

1. F9A classification (`PASS_REVALIDATED`, `METRIC_EQUIVALENCE_NOT_ESTABLISHED`, or `FINAL1_1_CALCULATION_FAILED`);
2. if PASS, all three FINAL-1.1 NH3 normalized leverage values and MeOH/NH3 ratios at 2%, 2.5%, 3%;
3. F8 SVG/PDF/PNG render status and SHA-256;
4. FINAL-1.1 NH3 provenance files found/copied for F1–F6;
5. Git commit hash(es);
6. any blocker that affects scientific correctness rather than appearance.

Do not start any new Agent/API benchmark, new reaction case, new model tier or exploratory parameter sweep.