# Methanol screen: compute saved by a closed-form cost bound — 2026-10-06

`run_meoh_pruning.py` writes `candidate_bounds.csv`, `group_pruning.csv` and `summary.json`.

The full evaluation of one literature candidate (`analysis/meoh_literature_inversion_2026_10_05`) is the recycle-loop
cost on the 396-level purge grid with the recycled-CO conversion solved at each level against the RWGS and
CO-hydrogenation equilibria; the minimum over purge is the plant cost. That takes about 0.9 s per candidate on this
machine. The lower bound evaluates the same plant economics on lower-bound loop flows at each purge level, valid for
any recycled-CO per-pass conversion between 0 and 1 (so for the inert treatment and every recycled-CO rule), with no
equilibrium solve: about 0.3 ms. The inequalities are listed in the script docstring. When the methanol selectivity
is 100 %, the bound equals the exact cost.

Agent rule per comparison group: evaluate the paper's leader in full (its cost gives the regret), then the other
candidates in increasing bound order, stopping when the next bound exceeds the best full cost found.

| | Recycled CO (primary) | Inert CO |
|---|---:|---:|
| candidates in the 36 scored groups | 413 | 413 |
| bound below the full cost | 413/413 | 413/413 |
| full evaluations needed | 89 | 248 |
| excluded before full optimization | 324 (78.5 %) | 165 (40.0 %) |
| plant-cost leader missed | 0/36 | 0/36 |
| median bound gap | 22.1 EUR/t | 247.8 EUR/t |

With the bound itself counted, the primary treatment needs 21.6 % of the compute of evaluating every candidate in full.
The inert treatment gains less because the bound is taken at the most favourable recycled-CO conversion (all
recycled CO converted), whereas with inert CO the CO builds up in the loop and the CO2 feed per pass is higher.

The full costs compared against are those of `literature_candidates.csv` (stored to six significant digits; the check
uses that precision). The script calls the ACSA self-check gate first.
