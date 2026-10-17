# Joint methanol field robustness, 2026-10-12 (unfrozen)

## Scope

Independent exploratory work in PR #55. This folder does not modify S5, ammonia 7/33, source data, figures, the manuscript, or freeze/field-2026-10-12.

- audit_inversion_robustness.py: reproduce source-aligned S5, extended purge, published-inlet and loading-only comparisons. An intersection of separately computed sensitivities is not a joint loading/purge result.
- joint_inventory_purge.py: jointly minimize the original cost objective over catalyst loading multiplier m and purge p, separately for each measured experimental point. Compare experimental STY and joint-optimized cost leaders.
- .github/workflows/field-robustness-audit.yml: regression tests, two-entry smoke, 4 parallel full shards, joint rankings, regret and paper-cluster confidence intervals, artifacts and branch-only output commits.

## Model

For laboratory conversion X0 and space-time yield STY0, use the *one-point calibrated surrogate*:

    X(m) = X_eq (1 - (1 - X0/X_eq)**m)
    STY(m) = STY0 * X(m) / (X0*m)

The feed equilibrium X_eq is solved using the existing multi-start CO2-hydrogenation + RWGS root-finding routine. Laboratory points at/above this feed equilibrium retain only m=1, not an unphysical extrapolation.

At each candidate's fixed measured temperature, pressure, selectivity and H2/CO2, the original loop and plant cost are recalculated over m and purge. Selected conditions must pass CO2-hydrogenation outlet equilibrium. Additional reactor-inlet fractions of species other than H2/CO2 are upper-bounded at 4.92%, 6.86% and 10.249% in three separate sensitivity scenarios derived from published plant flowsheets; these are **reference design envelopes, not universal limits**. The unconstrained case is diagnostic only.

The catalyst-loading grid is [0.25, 0.5, 0.75, 1, 1.25, 1.5, 2, 3, 5, 10]. Purge is extended logarithmically below 0.5% and retains the original upper grid to 40%. Minima are grid minima. Inventory costs are calculated within the original reactor module model; an optional anchor-inventory upper bound can be given via --max-inventory-multiple. The standard CI leaves this optional cap unset.

**Important:** Original S5 may equilibrium-cap conversion while leaving printed STY unchanged. The new joint model uses the surrogate to rescale STY together with conversion and independently filters equilibrium-feasible states, so its cost must not be characterized as an exact S5 rerun. It is a controlled counterfactual, not independently validated reactor kinetics.

## Known limitations

Fixed CO and CH4 selectivities may be inaccurate under changed residence time. The current plant model does not supply a full reactor heat/mass transfer or pressure-drop feasibility constraint and carries uncertainties in CO/RWGS conversions. Some published data omit CO or CH4 selectivity. Published inlet compositions are illustrative. Sample size, shared papers, and surrogate structural uncertainty must be reported separately.

## Reproduce

    pip install -r requirements.txt
    python -m unittest discover -s analysis/field_robustness_2026_10_12/tests -v
    python analysis/field_robustness_2026_10_12/audit_inversion_robustness.py --check-frozen
    for i in 0 1 2 3; do
      python analysis/field_robustness_2026_10_12/joint_inventory_purge.py shard --index "$i" --count 4 --out "/tmp/joint_shards/shard_$i.csv"
    done
    python analysis/field_robustness_2026_10_12/joint_inventory_purge.py aggregate --input-dir /tmp/joint_shards --output /tmp/joint_report

## Acceptance

Require 310 unique input entries; stable source-aligned comparison identifiers; every reported optimum satisfies its scenario constraint; full reporting of infeasible candidates, above-feed-equilibrium cases, group types and paper-bootstrap CIs. Report with and without Bansode 2013. Manuscript should remain frozen until new scientific claims are independently validated.
