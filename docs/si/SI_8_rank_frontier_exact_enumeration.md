# SI Section 8. Exact enumeration of small decision-frontier rank spaces

## 8.1 Purpose

The NH3 and CO2-to-methanol decision frontiers contain only three and four ranked candidates, respectively. Spearman rho and Kendall tau are therefore used in the manuscript as compact **descriptive measures of rank rearrangement**, not as population-level significance tests. To make the discreteness of these small rank spaces explicit, the complete permutation space is enumerated exactly.

The executable source is `tools/rank_frontier_exact.py`. It uses only the Python standard library and contains frozen assertions for the canonical NH3 and MeOH rank statistics.

## 8.2 NH3 Top-3 decision frontier

The upstream activity order is

```text
Ru > Os > Fe
```

and the optimized economic order is

```text
Fe > Ru > Os
```

For the same three candidates, the downstream rank vector in upstream order is `(2, 3, 1)`. This gives:

- Spearman rho = **-0.50**
- Kendall tau = **-0.3333**
- pairwise inversions = **2 of 3**
- inverted pairs = **Ru vs Fe** and **Os vs Fe**
- preferred-candidate identity change = **Ru -> Fe**

Because `n = 3`, there are only `3! = 6` possible downstream permutations. Their Spearman-rho distribution is:

```text
rho =  1.0 : 1 permutation
rho =  0.5 : 2 permutations
rho = -0.5 : 2 permutations
rho = -1.0 : 1 permutation
```

The exact two-sided permutation probability for `|rho| >= 0.50` is therefore **6/6 = 1.000**. The exact two-sided Kendall probability is also **1.000**. These values are not used to argue that the frontier is statistically negatively correlated. The scientific result is the observed decision-level change: **2/3 pairwise orders invert and the preferred candidate changes from Ru to Fe**, even though the full 15-metal ranking remains strongly correlated overall (`rho = 0.929`).

This is the distinction used in the manuscript:

```text
global rank agreement != decision-frontier consistency
```

## 8.3 CO2-to-methanol four-state frontier

At the canonical 2% purge point, using STY per g Re as the upstream screening metric, the upstream order is

```text
1 wt% Re / 250 C
> 1 wt% Re / 200 C
> 5 wt% Re / 200 C
> 5 wt% Re / 250 C
```

and the economic order is

```text
5 wt% Re / 200 C
> 1 wt% Re / 200 C
> 1 wt% Re / 250 C
> 5 wt% Re / 250 C
```

For the same four states, the downstream rank vector in upstream order is `(3, 2, 1, 4)`. This gives:

- Spearman rho = **0.20**
- Kendall tau = **0.00**
- pairwise inversions = **3 of 6**
- upstream per-Re winner moves from rank **#1 to #3** economically
- economic winner = **5 wt% Re / 200 C**

Because `n = 4`, the complete downstream rank space contains only `4! = 24` permutations. Exact enumeration gives the following Spearman-rho distribution:

```text
rho =  1.0 : 1 permutation
rho =  0.8 : 3 permutations
rho =  0.6 : 1 permutation
rho =  0.4 : 4 permutations
rho =  0.2 : 2 permutations
rho =  0.0 : 2 permutations
rho = -0.2 : 2 permutations
rho = -0.4 : 4 permutations
rho = -0.6 : 1 permutation
rho = -0.8 : 3 permutations
rho = -1.0 : 1 permutation
```

The exact two-sided permutation probability for `|rho| >= 0.20` is **22/24 = 0.9167**. With observed `tau = 0`, the corresponding exact two-sided Kendall probability is **1.000**. Again, these probabilities are included to document the finite rank space, not to support a population-level significance claim.

The manuscript-level evidence is therefore the directly observed rearrangement: **3/6 pairwise orders invert**, the upstream per-Re winner falls to economic rank #3, and the preferred state under the economic objective is different.

## 8.4 Reporting convention

For NH3 and MeOH, the manuscript should report rank statistics in the following hierarchy:

1. **decision identity** — whether the preferred candidate changes;
2. **pairwise inversion structure** — how many candidate pairs change order;
3. **Spearman rho / Kendall tau** — compact descriptive summaries of the rearrangement.

No small-n frontier claim should be phrased as a statistically significant population correlation result. Exact permutation enumeration is retained in the SI as an audit of the finite rank space.

Run:

```bash
python tools/rank_frontier_exact.py --check
python tools/rank_frontier_exact.py
```

The first command fails if any frozen canonical rank statistic changes.