# F10 — main-text Agent figure spec, and Extended Data / SI allocation (2026-09-13)

Scientific design specification for the **main-text three-panel Agent figure**, plus the allocation of the remaining
Agent evidence to Extended Data and SI. Written against the frozen §3.7 / §4.6 in
`MANUSCRIPT_SKELETON_v3_2026-09-13.md`. Every number must come from
`data/agent_figure_panel_data_2026-09-13.csv`, built by `tools/discover/build_agent_figure_data.py` from the frozen
analysis CSVs; no value is hand-entered into the renderer. Metric definitions are fixed by
`AGENT_METRIC_DEFINITIONS_SOURCE_OF_TRUTH_2026-09-13.md`.

## 0. Status change this figure implies

The 2026-09-10 research-freeze record decided that the C1 Agent figures would remain *supporting / Extended Data*
evidence and that **no tenth main scientific figure** would be created. That decision is **superseded here**: the Agent
line now carries a three-part result (envelope interior, upper cost boundary, capability boundary) that the main text
states in full, so it needs a main-text figure. F10 is therefore added to the main set, and the existing C1 panels
(`figA`–`figD`, `figP1`–`figP4`) drop to Extended Data / SI roles as allocated in §3.

F10 is **not** locked by this document. It is locked only after render, caption fixing and a SHA-256 manifest, following
the F8 precedent.

## 1. One-sentence message

**Adaptive compute allocation has a capability-bounded operating envelope**: it recovers the complete decision far below
the fixed policy's threshold, it costs more than the fixed policy once the constraint is lifted, and it does not transfer
to weaker model tiers.

Each panel carries exactly one of those three clauses. No panel repeats another's claim.

## 2. Panel specification

Toolchain: **matplotlib**, consistent with the existing C1 panels (`figA`–`figP4`). R is reserved for F8.
Layout: one row, three panels, shared visual grammar, panel letters **a / b / c**.
Export: SVG (canonical), PDF, PNG at 600 dpi, plus `F10_RENDER_SHA256.txt`.

### Panel a — the envelope interior and the capability boundary

*Claim: the strong tier completes the decision from 75 CU upward, far below D's 206 CU; the weaker tiers do not, at any
budget tested.*

- x: budget (CU), log scale, 50 → 400 plus a broken-axis inset or offset marker for the non-binding 5000-CU allowance.
- y: P(complete decision), 0 → 1.
- series: strong E (50–250 CU + non-binding cell), mini E (175–400 CU), nano E (175, 225 CU). Wilson 95% intervals as
  error bars on every point — `ci_lo` / `ci_hi` columns.
- reference lines: **vertical** at D's completion threshold **206 CU**, labelled `fixed-policy completion threshold`;
  **vertical** at **75 CU**, labelled `lowest stable strong threshold`.
- annotation: the 50 CU strong point (13/20) marked as the **affordability floor**, with a short note that winner and
  decision pair remain 20/20 there and only reachability fails.
- The mini E2 interface arm is **not** drawn here — it coincides exactly with mini E at 175 CU (both 0/20) and would be
  visually degenerate. It goes to Extended Data (§3).

### Panel b — the allocation mechanism

*Claim: narrow-window allocation is used only below the threshold and only by the strong tier.*

- x: budget (CU), same scale and reference lines as panel a.
- y (left): fraction of runs using canonical narrow-window allocation, 0 → 1, strong tier — 20/20 at 50–175 CU, 1/8 at
  200 CU, 0/20 at 225 CU, 0/9 at 250 CU, 0/20 at the non-binding allowance.
- y (right): median smallest window built, in states, out of 14,136 — 1,950 at 125 CU, 1,262 at 150 CU, 1,122 at 175 CU.
  Plot only the budgets for which this is recorded; do not interpolate.
- overlay: mini and nano at 0/20, to make the tier specificity visible in the same panel.
- The canonical rule must appear in the caption in one clause: *window strictly smaller than the full 14,136-state
  domain **and** used by a later successful scoped action*.

### Panel c — the upper cost boundary

*Claim: the agent stops near its decision-stable point only while the budget binds; released, it spends 3.5× the fixed
policy for the same audited decision.*

- x: budget (CU), same scale, including the non-binding allowance cell.
- y: CU, log scale. Two series per budget: **median decision-stable CU** (quantity #4) and **median final-used CU**
  (`spent_CU`), with a shaded band or vertical connector between them representing the median post-stability overrun.
- reference line: **horizontal** at **206 CU** (D's threshold), so the crossing at the non-binding cell is visible.
- annotation at the non-binding cell: `median 714 CU = 3.5x D`, and the per-run maximum **3,021 CU** marked as a single
  open symbol explicitly labelled as one run, not a summary statistic.
- The caption must state the aggregation: medians over 20 runs, unweighted, and that the overrun share quoted in the text
  (33%) is a **mean of per-run ratios**, not 148/714.

## 3. Extended Data and SI allocation

Everything that §3.7 no longer carries in the main text gets a fixed home. Reviewers will look for these.

| item | destination | source |
|---|---|---|
| **ED Fig. 1** — interface intervention (E2) at 175 CU: interface errors 18 → 0, no-tool-call 16 → 4, winner 14/20 → 19/20, complete decisions 0/20, `BACKWARD` 0/20, budget errors 36 → 51, premature `OPTIMIZE` 13 → 67 | Extended Data, paired bar / slope chart | A4 §2; `discover_boundary_c1_error_taxonomy_summary.csv` |
| **ED Fig. 2** — failure-mechanism taxonomy by tier: interface / budget / sequencing shares, nano 81% budget-blind versus mini 51/29/20 | Extended Data, stacked bars | A3 §3; taxonomy CSV |
| **ED Fig. 3** — per-run decision-stable versus final spend for the non-binding cell, showing the bimodal 218 CU / 566 CU split | Extended Data, strip or dumbbell plot | A6 §3; `discover_boundary_c1_uncapped_breakeven_audit.csv` |
| **ED Table 1** — the five CU-to-X quantities, their definitions and their uncapped-cell values (503 / 503 / 566 / 566 / 211) | Extended Data table | source-of-truth §1 |
| **SI §1** — the first-record scoring convention: scored break-even equals the first decision-pair `BACKWARD` in 100% of runs; capability versus scored recovery (any-`BACKWARD` 17/20 at 75 CU against scored 9/20) | SI text + table | A4 §1, A5 §1 |
| **SI §2** — the two strong ordering failures, run by run (175 CU r16 probe-before-target with no budget to re-classify; 100 CU r18 premature first `BACKWARD` never displaced) | SI text | A4 §1.1 |
| **SI §3** — the 50 CU affordability floor: 7 failures, 6 of which execute `BACKWARD` then cannot afford the 2–4 CU classification; arithmetic spine 35–50 CU | SI text | A5 §1 |
| **SI §4** — quote-based versus ledger-true CU: 31/297 runs affected, per-cell median inflation 0 CU, maximum 58 CU, two cell medians corrected (175 CU 140→124, 150 CU 106→102) | SI text + table | A5 §4; source-of-truth §4.2 |
| **SI §5** — break-even numerical agreement: relative difference 9.89 × 10⁻¹⁶, exactly 7.00 ULP, bitwise identical in 0/20 runs; wording constraint | SI text | source-of-truth §3.2 |
| **SI §6** — pre-registration deviations: cost-motivated reduced Phase B, no-smoke decision, both before the first Phase B API call; the aborted batch and its 17 quarantined zero-step traces | SI text | A5 §3.1; addendum A2 |
| **SI §7** — full run inventory: 317 scored C1 runs by cell, frozen hash checks 15/15 before and after every batch | SI table | taxonomy CSV; hashcheck records |

## 4. Wording constraints carried into every caption

- the control is a **non-binding 5000-CU allowance** — never "unlimited budget";
- the two interventions are reported **separately**: interface arm 0/20 at 175 CU; added compute 4–7/20 across
  225–400 CU. Never "both interventions were 0/20";
- the break-even agreement is **numerically identical within floating-point round-off** — never "bit-exact";
- **1.0899** is the reference-condition headroom and is **not** evidenced by the non-binding cell; only **2.5246**
  appears there. Any caption citing 1.0899 points to the 175 CU cell and the frozen NH3-FINAL-1.1 record;
- **218 CU** must name its cell: the 225 CU cell median, not the non-binding cell minimum;
- no claim of a universal or intrinsic compute saving.

## 5. Acceptance criteria before F10 can be marked LOCKED

1. every plotted value reproduces from `data/agent_figure_panel_data_2026-09-13.csv` with no manual entry;
2. panels a, b, c each state one distinct claim, with no repeated claim across panels;
3. all three reference markers present: 206 CU threshold, 75 CU lowest stable threshold, 14,136-state full domain;
4. Wilson intervals drawn on every proportion;
5. the non-binding cell is visually distinguished from the budget-constrained cells, not plotted as if 5000 CU were a
   point on the same continuum;
6. single-run extrema (3,021 CU) marked as single runs, never as summary statistics;
7. SVG / PDF / PNG exported and `F10_RENDER_SHA256.txt` written;
8. caption satisfies every constraint in §4.
