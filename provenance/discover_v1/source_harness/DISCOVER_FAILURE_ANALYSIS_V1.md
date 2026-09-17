# DISCOVER formal V1 — failure analysis (policy E, gpt-5.5-2026-04-23; 70 runs; all runs kept and scored as-is)

Classification rule (fixed before the runs): infrastructure failures may be retried by the fixed rule and are counted; agent/scientific failures
are never retried and enter the score unchanged.

## A. Infrastructure
| type | count | handling |
|---|---|---|
| API error / timeout / rate limit | 0 retries in 70 runs | (fixed rule: ≤ 5 retries with backoff) |
| unparseable tool-argument JSON | 0 | (fixed rule: re-request) |
| driver exception | 0 | — |
| turn without a tool call | 26/70 runs, exactly one turn each | reminder message ("call one tool or STOP"), no cost, counted as `malformed_turns`; the model had written its reasoning JSON first and called the tool on the next turn |

## B. Agent / scientific (entered the scores unchanged)
| id | failure | where | effect on score | notes |
|---|---|---|---|---|
| F1 | **Window-relative parity multiplier**: BACKWARD executed inside a restricted process window (e.g. 20–300 bar "screen", or T/Tsep-restricted windows), so the re-optimized parity multiplier is not the full-domain value | anonymous 200 CU run 1 (12.67× vs 201.22×, rel. error 0.94); named 200 CU runs 0, 2, 3 (157.3×, rel. error 0.22) | break-even relative error (scored); reachability class still correct (both values ≫ 2.5×); full decision counted correct | only at 200 CU, where the full window (111 CU) is unaffordable; the agent's shortcut is exactly what makes 200-CU completion possible |
| F2 | **Stop with an unresolved candidate**: agent stopped while the environment's S2 was false (candidate_05 = Os not optimized, not screened) | anonymous 200 CU runs 2, 3, 4 (11 CU left; 2 of 3 stop texts claimed S1–S3 satisfied, one acknowledged the unaffordable optimization) | not penalized by the frozen scorer beyond the recorded `S1S2S3` flags; outcome correct (Os is third in truth) | an unjustified stop claim; a scorer V2 could weight unresolved risk |
| F3 | **Over-optimization at large budgets**: all 15 candidates optimized before stopping although 12 were screenable as dominated | anonymous 8/15 runs at ≥ 800 CU; named similar | unnecessary-CU fraction 0.29–0.43 (D: 0.10); stopping efficiency 0.55–0.56 | decision unaffected; the agent treats spare budget as licence to "confirm", contrary to the prompt's stopping guidance |
| F4 | Post-decision MC / breakdown / validity calls after S1–S3 were satisfied | most runs at ≥ 500 CU | small CU (mostly 0-cost bookkeeping; MC 17–164 CU) | cheap, partly legitimate confidence checks |
| F5 | Lever tests almost never used (1/70) | — | none | the prompt does not require levers; noted for the paper's lever discussion |
| F6 | Named-task ordering by prior: Fe optimized first, BACKWARD as early as 43 CU | named runs | none on correctness; earlier winner | evidence that names change allocation order, not outcomes |

Not observed in any run: wrong winner, wrong pair decision, wrong reachability class, wrong backward pair, invalid action, unaffordable-action
loop, max-turn exhaustion, disagreement between the agent's stated winner and the environment-derived winner (70/70 agree).

## C. Reading
The only scientific errors are the 200-CU window-relative parity values (F1) and the unresolved-candidate stops (F2); both arise from the
agent trading completeness for cost when the full-domain window is unaffordable, and neither changed a decision. At generous budgets the
failure mode flips to over-spending (F3/F4). These are the two regimes the cross-model evaluation should watch.
