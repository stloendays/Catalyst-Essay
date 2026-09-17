# SI Section 6. Protocol execution, boundary-targeted sampling and reproducibility record

Scope: the DISCOVER-BOUNDARY-C1 Agent line. Results §3.7 and Discussion §4.6 are cross-referenced rather than restated here.

## 6.1 Boundary-targeted weak-tier evaluation

After the strong-tier extension localized the deterministic fixed-VOI completion threshold at 206 CU, the weak-tier transfer arm was evaluated at two deliberately discriminative budgets that straddle that threshold: 175 CU below it and 225 CU above it. The 175-CU cell tests whether the below-threshold decision-recovery regime transfers to weaker models; the 225-CU cell is the control region in which the deterministic policy completes.

| model | 175 CU | 225 CU |
|---|---:|---:|
| `gpt-5.4-mini-2026-03-17` | 20 formal | 20 formal |
| `gpt-5.4-nano-2026-03-17` | 20 formal | 20 formal |

The evaluation reused the identical frozen task and anonymous mapping, prompt, 11 tools plus STOP interface, CU cost model, policy-E semantics, deterministic D reference, scorer, definition of `full_decision_correct`, stopping rule, API retry policy and NH3-FINAL-1.1 ground truth. No prompt tuning or tool-contract redesign was introduced in this arm. Because the same frozen driver, scorer and interface had already been exercised by the completed strong-model extension, no additional smoke calls were used for this targeted transfer test.

Phase-B integrity counts are therefore simple: **80 formal runs**, frozen-hash checks **15/15 PASS before and after**, **0 infrastructure retries** and **0 driver exceptions**. The two cells are interpreted only as boundary-straddling capability-transfer measurements; no weak-tier response is inferred for unmeasured budgets.

## 6.2 Infrastructure-isolated 75-CU replication

The first 75-CU strong-tier batch was interrupted by API quota exhaustion after three complete traces and one partial trace; subsequent requests returned HTTP 429 `insufficient_quota`. The interruption was isolated from the scientific sample rather than mixed into it.

| run index | steps | spent CU | disposition |
|---|---:|---:|---|
| 0 | 23 | 75.0 | complete; retained as superseded partial-batch provenance |
| 1 | 12 | 52.0 | complete; retained as superseded partial-batch provenance |
| 2 | 13 | 73.0 | complete; retained as superseded partial-batch provenance |
| 3 | 11 | 51.0 | quota-truncated; quarantined |
| 4–19 (16 runs) | 0 | 0.0 | zero-step infrastructure traces; quarantined |

No reported result was derived from this interrupted batch. All traces were preserved verbatim: the 17 infrastructure-affected traces are listed in `data/discover_boundary_c1_quarantine_2026-09-11.json`, and the three completed partial-batch traces are recorded in `data/discover_boundary_c1_superseded_B75_2026-09-11.json`. The reported 75-CU cell was then generated as one complete r0–r19 batch after quota restoration, preventing cross-batch pooling.

Across the subsequent 2026-09-11/12 extension series, **118/118 formal runs completed**, with **0 infrastructure retries**, **0 driver exceptions**, frozen hashes **15/15 PASS** before and after every batch, and the `discover/formal_e.py` SHA-256 unchanged. Independent tags (`c1low`, `c1uncapped`, `c1mini300`, `c1mini400`) keep every extension cell separable in downstream analysis.

## 6.3 Canonical compute accounting and diagnostic normalization

The harness records two distinct compute quantities for scoped optimization. `env.quote()` is a pre-execution request estimate, whereas the environment ledger records the actual charge after reusing states that were already computed. When an optimization window overlaps previously evaluated states, the quote can exceed the ledger charge. The manuscript therefore uses the **ledger-true decision-stable CU** as the canonical compute metric and retains the quote-based field only as a diagnostic view.

Across all 317 scored runs, 32 contain a non-zero quote-minus-ledger difference. The per-cell median difference is 0 CU in every cell except strong 175 CU, where it is 2 CU; the largest single-run difference is 58 CU. This distinction affects compute-accounting summaries only. Completion rate, winner and pair decisions, break-even values, reachability verdicts, narrow-window classification and error counts are independent of the quote field.

Window allocation is likewise reported under one canonical operational definition: a narrow window must be **strictly smaller than the full 14,136-state admissible domain and must be used by a later successful scoped action**. Under this definition, strong-tier narrow-window allocation is concentrated below the deterministic 206-CU threshold (20/20 at 50–175 CU, 1/8 at 200 CU, 0/20 at 225 CU and 0/9 at 250 CU), while neither mini nor nano uses a qualifying narrow window at 175 CU (0/20 each). This definition ties the mechanism to compute that actually participates in the decision chain rather than to the presence of a syntactic bounds argument.

For window-size summaries, the reporting code uses the conventional sample median (`statistics.median`), including the average of the two central observations for even `n`. The regenerated diagnostic tables and manuscript prose therefore share one statistical convention.

Together, these checks make the Agent result content-addressable at three levels: the scientific protocol is hash-pinned, infrastructure interruptions are separated from scored samples, and every manuscript compute quantity is tied to the environment ledger rather than to a request-time estimate.
