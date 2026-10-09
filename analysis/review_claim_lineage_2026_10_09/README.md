# Cross-document scientific consistency gate (independent review)

This is a **read-only, provisional** evidence-lineage checker, created on an
independent review branch so local Claude can continue the paper/figure rebuild.
It does not change the model, manuscript, SI, figure source data or freeze tag.

## Author-approved science protocol

The author's selected methanol treatment is the thermodynamically consistent
S5 process model (unit/duplicate corrections, CO equilibrium and CO2 conversion
equilibrium); only literature *printed* values enter the primary field result.
The ammonia field result also uses its published printed observations. A
separate sensitivity lets methanol conversion rise with catalyst inventory.

The program reads these selection decisions from the verification branch's
committed tables; it does not infer authority from currently stale manuscript
prose. It classifies **substantial scientific coherence blockers**:

- old full/all-entry 33/83 and 44/124 field claims in paper/captions/SI
  versus S5 printed-only 15/40 and NH3 printed-only 7/33;
- SI 5f contains a 54/82 baseline despite referencing a benchmark table whose
  actual baseline is 33/83, neither representing the selected S5 cohort;
- invalid reuse of 83- and 124-comparison paper-cluster confidence intervals;
- reported material replacement versus same-material temperature changes, with
  *distinct measured temperatures* required for temperature-series eligibility;
- unqualified perfect transcription of printed fields despite measured SI
  extraction errors;
- alloy domain scope (the 3d/group-6 selection result requires exclusion
  of groups 3–5 and sp-element surfaces);
- NH3 descriptor-only vs MeOH purge-wise deterministic cost-bound attribution;
- stale population in Extended Data Figs 2–4.

## Run without touching the original paper

Run from the repository root:

~~~bash
python -m unittest discover -s analysis/review_claim_lineage_2026_10_09/tests -v
python analysis/review_claim_lineage_2026_10_09/check_claim_lineage.py \
  --out-dir /tmp/claim_lineage
python analysis/review_claim_lineage_2026_10_09/paired_paper_bootstrap.py \
  --out-dir /tmp/claim_lineage --strict
~~~

The default gate exits zero **only if source-data cross-checks succeed**;
it may (and currently should) emit manuscript blockers. The publication gate
has the opposite semantics:

~~~bash
python analysis/review_claim_lineage_2026_10_09/check_claim_lineage.py \
  --out-dir /tmp/claim_lineage --publication-gate
~~~

This should exit nonzero until the selected data are approved/frozen and all
dependent manuscript, figures and SI are regenerated.

## Matched bootstrap for the chosen paper population

The optional paired diagnostic draws **papers** (DOIs), with replacement,
not individual comparison groups. Every sampled paper brings its existing
groups into the draw. The same sampled DOI set is used for the two treatments,
ensuring the resulting change-in-rate interval is **paired**. The seed and
draw count are recorded (default 20261009, 10,000 draws). This is
**post-hoc diagnosis**, not a new preregistered significance test. It does
not establish that allowing catalyst loading causally changes chemistry.

The comparison ratio 10/32 describes *different catalyst winners*; 5/22
describes *same catalyst, different temperature winners*. These are different
eligibility populations. Material switches in which temperature also differs
cannot be called pure material effects. Source-input CH4/CO closure assumptions
are separately tested in PR #44 and must be retained as a limitation in the
author's interpretation.

## Review outputs

- claim_lineage.json (machine-readable source checks, issue severity and
  location, provisional selected cohort metadata)
- CLAIM_LINEAGE_REVIEW.md (human-readable handoff)
- selected_meoh_paper_cluster_bootstrap.json (observed proportions,
  paper-cluster percentile intervals and paired change interval)

No result generated here authorizes replacing manuscript percentages blindly.
Especially, an old 83-group plant-term sensitivity table must be **rerun**,
not relabelled 15/40. The selected S5 pruning proof must likewise be checked
before reusing the original 700/906 optimization count.

**For local Claude:** review these artifacts, fix the model-derived figures
in your own working branch after the scientific freeze, and keep manually
curated raw-data and original-paper gold-standard confirmation in the author's
workflow. Do not merge this stacked draft PR directly into main first.
