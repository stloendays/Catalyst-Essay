# Open-weights cross-model validation — execution plan (deferred, 2026-09-26)

**Status: planned, not started (user decision 2026-09-26 to defer).** Nothing here has been run. The plan is
written so that it can be executed without re-deriving anything: every command, file, gate and decision rule is
fixed now; the only inputs still open are the GPU host name and the model that passes admission.

Purpose. DISCOVER V1 and DISCOVER-V2-STOP were run on one vendor's three tiers (gpt-5.4-nano, gpt-5.4-mini,
gpt-5.5). The manuscript's Agent claim is "model-tier dependent". An open-weights model on the **unchanged** V1
protocol tests whether the strong-tier regime is reproducible outside that vendor (H-transfer) or whether the
result is capability-tiered across vendors (H-tier). Either outcome is publishable; the plan is written so neither
can be produced by tuning.

---

## 1. What stays frozen

| item | state |
|---|---|
| task, prompt, 11 actions + STOP, cost model, environment, scorer, ledger, stopping rule | DISCOVER V1 frozen files, hashes in `DISCOVER_FROZEN_V1.json` (15) |
| driver | `discover/formal_e.py` (frozen policy-E driver, byte-identical to the V1 formal run) unchanged; it takes `--model` and honours `OPENAI_BASE_URL`. Orchestration (hash check, admission, cell order, analysis) in `tools/discover/open_weights_runner.py` |
| variant | anonymous (closed-book); named only as the secondary prior-leak probe, as in V1 |
| sampling | API defaults, as for the closed tiers; the vLLM server is started with the model's default generation config and **no** temperature/top-p override |
| scoring | `DISCOVER_SCORER_V1.score_trace`; statistics via `discover/cross_model_stats.py` (Wilson, Fisher, Cochran-Armitage) |
| stopping test | `discover/c1_stopping_test.py` applies unchanged (traces carry `stopping_status_before`) |

No file under the frozen list is edited. A hash check is run before the smoke test and after the last formal run
(`python discover/boundary_c1_runner.py hashcheck --label openweights_{before,after}`).

## 2. Infrastructure (verify, do not assume)

1. **Host.** The 8 × RTX 3090 node (192 GB). Record hostname, driver and CUDA version in the run metadata.
2. **Server.** vLLM ≥ 0.10 with OpenAI-compatible tool calling:
   ```bash
   vllm serve <MODEL> --tensor-parallel-size 4 --max-model-len 65536 \
     --enable-auto-tool-choice --tool-call-parser <parser> --served-model-name <MODEL> --port 8000
   ```
   `--tool-call-parser` is `hermes` for Qwen3, `openai` for gpt-oss (check the vLLM version's parser table). Two
   models can be served on the two 4-GPU halves at once.
3. **Context length.** C1 strong runs reach 100–260 k prompt tokens per run because the whole tool history is
   resent every turn; per-turn context reaches ~20–30 k tokens. `--max-model-len 65536` is the minimum; a
   model whose native context is shorter fails admission on that ground alone.
4. **Client side.** On the driver host:
   ```bash
   export OPENAI_BASE_URL=http://<host>:8000/v1
   export OPENAI_API_KEY=local-placeholder      # the driver requires a non-empty key; vLLM ignores it
   ```
   The harness `cache/` (212 MB response surfaces) must be present on the driver host; the driver, not the GPU node,
   runs the scientific environment.
5. **Green check before anything else:** `python -m pytest tests/test_frozen_untouched.py -q`.

## 3. Model selection rule (fixed now, applied in order)

Candidate list, in priority order, all Apache-2.0 / permissive, native function calling, fits 4 × 3090 or 8 × 3090:

| rank | model | serving | why |
|---|---|---|---|
| 1 | **Qwen3-32B** (dense) | bf16, TP = 4 (~65 GB) | strongest dense open model that fits one half of the node; thinking mode **off** for the primary cells (`chat_template_kwargs: enable_thinking=false`), on as a secondary arm if budget allows |
| 2 | **gpt-oss-120b** | MXFP4, TP = 4 (~65 GB) | second vendor lineage; reasoning effort left at the server default |
| 3 | Qwen3-235B-A22B | FP8 / AWQ, TP = 8 | only if 1 and 2 both pass admission and the node is free |

**Admission test (per model, before any formal run).** 3 runs at 225 CU, anonymous, tag `admit`:

- pass: 0 malformed tool calls, 0 undeclared-argument errors, 0 `no tool call` turns across the 3 runs, and
  every run ends by `agent STOP` or `budget_exhausted` (not `malformed_action_limit`);
- fail: the model is recorded with its error counts in `DISCOVER_OPEN_WEIGHTS/ADMISSION.md` and the next candidate is
  tried. A failed model is **not** retried with a different prompt, parser or sampling; interface hardening is a
  DISCOVER V2 change and out of scope here.

The first model to pass is the primary open tier. The admission traces are kept but excluded from all statistics.

## 4. Cells, sample size, order

| step | cell | n | why |
|---|---|---|---|
| 1 | 225 CU | 20 | the C1 boundary cell where mini reaches 6/20 and strong 20/20 |
| 2 | 175 CU | 20 | the cell below the 206-CU fixed-policy threshold where mini/nano are 0/20 |
| 3 | 75 CU | 20 | the lowest stable strong-tier cell (narrow-window regime) |
| 4 | 5,000 CU (non-binding) | 20 | **only if** step 1 completes ≥ 19/20; otherwise skipped and recorded |
| 5 | S-gate arm of DISCOVER-V2-STOP at 75 and 5,000 CU | 20 + 20 | **only if** steps 1–3 place the model in the strong regime (≥ 19/20 at 75 CU) |

Total 60–120 runs per admitted model. Runs are executed in the order above and never re-run; a run that ends in
`infrastructure_failure` (server down, timeout after the driver's 5 retries) is quarantined and replaced by the
next run index, as in C1.

Commands (harness root, after `hashcheck --label openweights_before`):

```bash
python discover/formal_e.py --variant anonymous --model <MODEL> --budgets 225 --runs 20 --out DISCOVER_OPEN_WEIGHTS/<MODEL>/runs --tag ow
python discover/formal_e.py --variant anonymous --model <MODEL> --budgets 175 --runs 20 --out DISCOVER_OPEN_WEIGHTS/<MODEL>/runs --tag ow
python discover/formal_e.py --variant anonymous --model <MODEL> --budgets 75  --runs 20 --out DISCOVER_OPEN_WEIGHTS/<MODEL>/runs --tag ow
# conditional
python discover/formal_e.py --variant anonymous --model <MODEL> --budgets 5000 --runs 20 --out DISCOVER_OPEN_WEIGHTS/<MODEL>/runs --tag owuncapped
python discover/v2_stop_runner.py run --arms gate --budgets 75,5000 --runs 20 --model <MODEL> --tag owgate
```

Wall time: C1 strong runs took 70–250 s each against the vendor API; a 32B model on 4 × 3090 at 20–30 k context
will be slower per turn. Budget one node-day per 60 runs and run the two halves in parallel.

## 5. Endpoints and preregistered readouts

All computed by existing scripts, none hand-entered:

| endpoint | script | comparison |
|---|---|---|
| P(full), P(win), P(pair), P(reach) with Wilson 95% CI per cell; Fisher exact against the strong, mini and nano cells at the same budget | `discover/cross_model_stats.py` | closed tiers |
| canonical narrow-window use (window < 14,136 states, used in a later scoped action) | `discover/c1_error_taxonomy.py` | strong 20/20 at 75, 0/20 at 225 |
| rule-reach rate, correct-at-rule, post-rule spend | `discover/c1_stopping_test.py` | strong 189/212, 188/189 |
| tool-interface error count per run | `discover/c1_error_taxonomy.py` | nano/mini 69–86% of runs, strong 0 |
| decision-stable and final spend (ledger-true) | `discover/c1_overrun_analysis.py` | strong 52.5 / 70 at 75 CU |

Preregistered hypotheses (both informative):

- **H-transfer**: ≥ 19/20 complete at 225 CU **and** ≥ 19/20 at 75 CU with narrow-window use ≥ 15/20 → the
  strong-tier decision-recovery regime is reproduced by an open model; the manuscript can say "not vendor-specific".
- **H-tier**: < 19/20 at 225 CU, or ≥ 19/20 at 225 but < 15/20 at 75 CU → the open model sits in or between the
  closed weaker tiers; report its failure layer (¬S2 unresolved / ¬S3 reachability / interface) with the same
  taxonomy, and the manuscript keeps "model-tier dependent" with a second vendor as evidence.
- Anything in between is reported as measured; no cell is re-run to move it.

## 6. Deliverables (repository)

| file | content |
|---|---|
| `docs/OPEN_WEIGHTS_CROSS_MODEL_RESULTS_<date>.md` | results in the format of `CROSS_MODEL_DISCOVER_V1.md` §2–§5 |
| `data/discover_open_weights/` | per-run and per-cell CSVs from the five scripts above; traces (`trace.json`, `messages.json`, `identity_mapping.json`) |
| `provenance/discover_open_weights/` | hash checks before/after, server launch line, vLLM version, model revision hash, admission record, batch logs |
| Extended Data | one panel added to ED4 (final spend and completion for the open model beside the closed tiers) via `render_ED4_v2stop.py`, manifest updated |
| manuscript | one sentence in the Agent Results paragraph and one in Methods, registered in `tools/check_manuscript_numbers.py` |

## 7. Stop conditions

- No candidate passes admission → record all three admission results, write the results file with §3 only, and
  report to the user; do not relax the admission test.
- The GPU node is unavailable for more than the planned window → nothing partial is analysed; cells are complete
  units of 20.
- Any frozen-hash mismatch at `openweights_after` → the batch is void and repeated after the cause is found.
