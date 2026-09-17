# DISCOVER — formal single-model evaluation V1 (PHASE E, 2026-09-06)

Protocol: `DISCOVER_FROZEN_V1.json` (verified hashes; nothing in the frozen list was modified). Ground truth: canonical NH3-FINAL-1.1 run
`outputs/nh3_final_20260905T134204Z`, read only by `DISCOVER_SCORER_V1.py`. Driver for policy E: `discover/formal_e.py` (new file; sha in
`DISCOVER_FORMAL_RUNS_V1/metadata/formal_metadata.json`). Analysis: `discover/formal_analysis.py`. No post-result change to prompt, task,
schema, cost model, environment, stopping rule, policies A–D, scorer or D's constants.

## 1. Formal model and run configuration
| item | value |
|---|---|
| model requested / response model | `gpt-5.5-2026-04-23` / `gpt-5.5-2026-04-23` (every run) |
| API | OpenAI chat.completions, function tools (11 frozen actions + STOP), tool_choice auto; openai-python 3.7.0 |
| temperature / reasoning | API defaults (not set) |
| runs | 5 independent runs × 7 budgets {200, 250, 300, 500, 800, 1200, 2000} CU × 2 variants = 70 runs; no API seed control → "independent runs" |
| baselines | frozen A (20 trajectories per budget and variant), B, C, D traces copied from `discover_runs/*_v1_*`; not re-run |
| tokens | 4.41 M prompt + 0.68 M completion in total; mean 63 k + 9.8 k per run |
| failures | 0 infrastructure retries, 0 driver exceptions, 0 action errors; 26/70 runs had one turn without a tool call (reminder, cost 0); all 70 ended by the agent's own STOP |
| timestamps / provenance | `metadata/formal_metadata.json`; per-run `metadata` block in each trace; harness root is not a git repository (hash provenance) |

## 2. PRIMARY result — anonymous task (candidate_01…15; scorer-only identity mapping)
Policy E (LLM) per budget, n = 5 each; A: n = 20; B/C/D: deterministic, n = 1.

| budget CU | E full decision (winner ∧ pair ∧ reachability) | E break-even rel. error (mean) | E CU spent (mean) | E CU→stable correct winner (mean) | E unnecessary-CU fraction | D full / spent | B full / spent | C full / spent | A P(full) / P(winner) |
|---|---|---|---|---|---|---|---|---|---|
| 200 | **5/5** | 0.187 (one run 0.937, four 0.000) | 182 | 115 | 0.02 | 0 / 193 (winner only) | 0 / 184 (wrong winner) | 0 / 172 (winner only) | 0.00 / 0.15 |
| 250 | 5/5 | 0.000 | 218 | 167 | 0.13 | 1 / 247 | 1 / 219 | 0 / 230 | 0.00 / 0.15 |
| 300 | 5/5 | 0.000 | 248 | 155 | 0.12 | 1 / 281 | 1 / 269 | 1 / 293 | 0.00 / 0.20 |
| 500 | 5/5 | 0.000 | 268 | 161 | 0.11 | 1 / 281 | 1 / 369 | 0 / 500 | 0.05 / 0.70 |
| 800 | 5/5 | 0.000 | 496 | 364 | 0.39 | 1 / 281 | 1 / 369 | 1 / 798 | 0.20 / 0.85 |
| 1200 | 5/5 | 0.000 | 699 | 364 | 0.29 | 1 / 281 | 1 / 369 | 1 / 1059 | 0.65 / 0.95 |
| 2000 | 5/5 | 0.000 | 791 | 364 | 0.29 | 1 / 281 | 1 / 369 | 1 / 1059 | 0.85 / 0.95 |

Other primary metrics for E (anonymous, all 35 runs): winner correct 35/35; pair decision correct 35/35; reachability class correct 35/35
("unreachable"); decision regret 0 in every run; stopping efficiency 0.55–0.76 (best 0.76 at 250 CU); the LLM's own stated winner agreed with
the environment-derived winner in 35/35 runs. Full tables: `DISCOVER_POLICY_COMPARISON_V1.csv`, `DISCOVER_BUDGET_CURVES_V1.csv`; figures
`DISCOVER_FORMAL_RUNS_V1/anonymous/E1…E4_*_anonymous.png`.

## 3. SECONDARY — named task (metal symbols; studies the pretrained prior, not a closed-book claim)
E: full decision 5/5 at every budget; break-even rel. error 0.131 at 200 CU (three runs 0.218, window-relative), 0.000 elsewhere; CU spent
164/218/248/334/641/690/761; CU→stable 73/155/155/155/248/248/225; unnecessary fraction 0.03/0.13/0.12/0.15/0.43/0.43/0.32. A/B/C/D as in the
frozen baselines (`DISCOVER_FORMAL_RUNS_V1/named/`).

## 4. Allocation-path analysis of the 70 E traces (post hoc; `scores/allocation_paths.json`)
- Canonical order activity screen → process optimization → BACKWARD → TEST_REACHABILITY appeared in **35/35 anonymous and 35/35 named** runs
  (not required by the prompt). Stages used: MC 17/35 (anon) and 20/35 (named); model-validity checks 32/35 and 34/35; lever tests 1/35 and 0/35.
- First visible atomic/economic mismatch (own leader ≠ own highest activity, all 15 activities known): median 155 CU (anonymous min 29 CU, named
  min 34 CU — reached by optimizing the leading candidate inside a cheap screening window before the full domain). First BACKWARD: typically
  214 CU, minimum 88 CU (anonymous) / 43 CU (named). After the mismatch became visible, 67 % (anon) / 58 % (named) of the remaining spend went
  to the decision pair.
- Budget on obviously non-competitive candidates (feasible-in-truth set is only Fe/Ru/Os): mean 11 % (anon) / 16 % (named), max 62 % — the
  maximum comes from runs at ≥ 800 CU that optimized all 15 candidates (8/15 anonymous runs at ≥ 800 CU) before stopping.
- Adaptive window use: at 200 CU the agent built narrow screening windows (e.g. 50–300 bar, 1,343 states = 11 CU) instead of the 111-CU full
  domain, which is why it completed the decision below the 215-CU full-window floor; the cost of that shortcut is a window-relative parity
  multiplier in 1/5 anonymous and 3/5 named runs at 200 CU (still classified unreachable).

## 5. Answers
**Q1 — Decision-aware allocation vs random / activity-first / uncertainty-first.** Yes, with one honest qualification. Random needs ≈ 2,000 CU for
85 % complete decisions and 500 CU for a 70 % winner; uncertainty-first (largest σ first) reaches the complete decision only at 300 and ≥ 800 CU
and wastes 40–60 % of its budget; the fixed decision-aware policy D completes the decision from 250 CU with 10 % unnecessary compute. Against
activity-first the margin is modest: B also completes from 250 CU (219 CU spent) but finds the winner 58 CU later (213 vs 155), fails at 200 CU
(stops on the most active candidate), and wastes about twice the compute of D (0.21 vs 0.10). B and D are close on this reaction; the claim is
"decision-aware allocation is at least as good as activity-first and clearly better than random and uncertainty-first", not more.

**Q2 — LLM agent vs fixed VOI policy.** Equal decision quality (both 100 % at ≥ 250 CU). E adds value only in the budget-scarce regime: at 200 CU
it completes the decision 5/5 where D cannot (D's fixed full-domain window alone costs 111 CU), by sizing windows adaptively and reaching the
winner at 29–52 CU. At 250–500 CU E and D are indistinguishable (E 218–268 CU, D 247–281; CU→stable 155–167 vs 155). At ≥ 800 CU E is
*less* economical: it spends 496–791 CU (D 281) and its unnecessary fraction rises to 0.29–0.39 (D 0.10) because it continues to optimize
non-competitive candidates and run MC after the decision is stable. Pre-registered Agent-specific Go: met on "fewer CU to a stable correct
decision" only at 200 CU (5/5), and on "correct use of model-validity checks" (32–34/35 runs vs D's single check); not met on unnecessary
compute at high budgets. Reported as such.

**Q3 — Anonymous recovery of mismatch → backward → reachability.** Yes: 35/35 anonymous runs identified candidate_13 (= Fe) as the industrial
choice, candidate_04 (= Ru) as the most active, computed the parity multiplier (exact 201.22× in 34/35; 12.7× window-relative in one run) and
classified it unreachable against the 2.52× manifold headroom, in the canonical order, without any name-based prior (the zero-tool prior probe
on the same task got 0/5 on each of these).

**Q4 — Compute for a correct industrial decision.** Full-domain floor 215 CU (window 111 + activities 15 + three optimizations 87 + backward 1
+ reachability 4 with exact parity). Observed: E 147 CU (anonymous, narrow windows, exact parity) and 103 CU (named); D 247 CU (250-budget) /
281 CU (self-stop); B 219 CU; C 293 CU; random median ≈ 375 CU among the 25 % of trajectories that complete at all.

**Q5 — Named vs anonymous.** Decision quality identical (5/5 everywhere). The prior changes *ordering and timing*, not outcomes: with names the
agent optimizes Fe first (CU→first winner 73 vs 115 at 200 CU; first BACKWARD as early as 43 CU vs 88) and runs MC slightly more often; it
also produced three window-relative parity errors at 200 CU (vs one anonymous). The zero-tool probe shows the named prior alone recovers the
textbook picture (atomic-best Ru 4/5, unreachable 4/5) while the anonymous prior recovers only the winner (price prior) and nothing of the
inversion — so the anonymous tool-driven result, not the prior, is the evidence for the closed-book claim.

## 6. Caveats (recorded, not adjusted)
Single model, single tier; B ≈ D on this reaction; E's over-spending at large budgets; four window-relative break-even values at 200 CU; three
anonymous 200-CU runs stopped with one candidate (Os) unresolved by the environment's S2 while the agent's stop text claimed S1–S3 (see
`DISCOVER_FAILURE_ANALYSIS_V1.md`). Cross-model tiers and the negative-control reaction are not started.
