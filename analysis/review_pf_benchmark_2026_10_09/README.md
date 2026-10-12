# Independent process-and-economic benchmark audit

**Status:** independent QA, not a frozen paper statistic. Source files in
\`analysis/meoh_plant_benchmark_2026_10_06\` are **not** the current selected
S5+printed-only comparison cohort. This directory does not replace that
cohort's frozen calculations, alter the plant model, or edit the manuscript.

## Scientific interpretation

The Pérez-Fortes et al. (2016) reference has a 723.6 EUR/t NPV-zero **sale-price
threshold**, including capital recovery; it is not the production cost before
capital charges.

At that reference's own H2, CO2, catalyst and finance assumptions, the
existing "like-for-like" model total is approximately 706 EUR/t. This cost
definition uses the **reference plant's fixed O&M** (24.57 EUR/t) on the
model side. The component table also shows the model's **own fixed O&M**
(33.64 EUR/t). Adding the latter to the model's other components is a
different accounting treatment and must not be presented as the 706 EUR/t
break-even comparison.

The shared stoichiometric feed needed for each tonne of methanol from CO2 is:

- H2: \`3 * MW_H2 / MW_MeOH\` tonnes;
- CO2: \`MW_CO2 / MW_MeOH\` tonnes.

Its purchased-commodity expense at the **reference's** prices is the
same physical baseline for any 100%-yield methanol process. Subtracting it
from both reported totals reveals how sensitive a headline percentage
agreement is to the large common feed term. **This subtraction is a
diagnostic, not an alternative plant-cost model and does not isolate pure
catalyst effects**.

The *excess* H2 and CO2 consumption above stoichiometry remains sensitive
to carbon selectivity, side reactions, product losses, purge and recycle.
It is false to label the **entire** hydrogen bill "catalyst independent".

Carbon efficiency, recycle-to-fresh ratio, compressor-only electricity,
capital annuity and catalyst replacement are reported separately. The
reference's electricity *net* of recovery and the model's compressor-only
electricity have different boundary definitions and must be labeled.

## Run independently

~~~bash
python -m unittest discover -s analysis/review_pf_benchmark_2026_10_09/tests -v
python analysis/review_pf_benchmark_2026_10_09/pf_benchmark_audit.py \
  --out-dir /tmp/meoh_pf_benchmark_qa --strict
~~~

No third-party Python dependencies, and no process optimization is rerun.
The audit reads:

- \`reconciliation_cost.csv\`: model and reference cost rows;
- \`reference_values.csv\`: primary-source facts and source locators;
- \`reconciliation_plant.csv\`: original operating-point metrics;
- \`summary.json\`: higher-precision model costs;
- \`data/meoh/meoh_d01_model.py\`: model molecular weights via static AST
  literal parsing, without importing the model.

It emits \`pf_benchmark_audit.json\` and \`pf_cost_boundary_terms.csv\`.
GitHub Actions runs regression tests, the entire committed benchmark,
and uploads those tables as ephemeral reviewer artifacts.

## Human and Claude review queue

Before Extended Data Fig. 4 is finalized:

1. Draw the *stoichiometric feed baseline* separately from *excess feed
   consumption*. Do not infer universal catalyst independence from similar
   absolute H2 expenditure.
2. Use one fixed O&M definition per displayed total, and label the
   like-for-like substitution explicitly.
3. Clearly distinguish compressor gross power from net utilities.
4. Report discrepancies in recycle ratio, carbon efficiency and capital
   as separate checks; a 2.4% agreement in the total benchmark is not a
   validation of the catalyst-dependent ranking terms.
5. Re-run the formal sensitivity/figure generation **on the author's
   selected S5+printed-only cohort**, after source and gold-standard
   checks, before allowing any old 33/83 plots to appear in the paper.

Do not make any automatic correction to references, manuscripts or
experimental gold standards from an independent computed diagnostic.
