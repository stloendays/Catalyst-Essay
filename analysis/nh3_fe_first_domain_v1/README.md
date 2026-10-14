# NH3-FE-FIRST-DOMAIN-v1 — experimentally reported kinetic-pressure constraints

This **source-pressure-conditional** extension of the NH3-SI closed-loop /
Fe–Ru kinetic/economic study investigates a very specific review risk:
the higher-pressure Ru/C optimum in the earlier engineering atlas was an
extrapolation of a **50–100 bar** source-fitted rate expression.

**The Fe Dyson–Simon KM1 source rate is reported at 149–309 atm
(150.974–313.094 bar). The promoted 3.2 wt% Ru/C Rossetti formulation is
reported at 50–100 bar. They have zero common source-fitting pressure range.**
The source hot-T ranges do overlap (370–460 °C).

## What is calculated

Source [PR #93](https://github.com/stloendays/Catalyst-Essay/pull/93)
measured-rate bed integrals, [PR #92](https://github.com/stloendays/Catalyst-Essay/pull/92)
five-component SI-S27 cold recycle, and the same declared inventory/equipment
economic formulas are used. Each catalyst is reoptimized **only inside its own
reported pressure fit interval**, with independent process pressure and common
1500 t/d *actual recovered NH3*, 90 m³ bed cap, 15% reactor-inlet inerts cap,
25-year project and 12% equipment/metal reference annualization.

Economic scenario prices in this experiment are **H2 3 USD/kg, N2 0.06
USD/kg, Ru recovery 90%**, in order to check the independent local decision
atlas on its declared basis. These are **not market quotations** and differ
from the canonical PR #93 default H2 2 / N2 0.10 / recovery 95.55%.
Every scenario explicitly reoptimizes Fe and Ru under the *same price and
feasibility rules*, and the Ru-favorable branches are retained if present.

The baseline PR #93 32-state grid is independently rerun from source. The
predeclared extension samples Fe at 235/285 bar and Ru/C at 95/100 bar, with
hot/cold temperatures, purge and per-pass conversion varied for both source
pressure regions. No Ru temperature, metal price, or interaction coefficient
is fitted to make Fe win. Numerical unresolved points remain unresolved;
failing pressure or equilibrium constraints are never counted as wins.

## Scientific hierarchy and legitimate claims

**Level A, canonical paper:** NH3-FINAL-1.2 Fe 11.516 < Ru 16.633 < Os
19.747 USD/t (original catalyst-dependent economic objective), despite
Ru > Os > Fe descriptor activity. Frozen results and 32/64 industrial
benchmark remain unchanged.

**Level B, new source-rate fitted pressure-domain study:** Fe and promoted
Ru/C are two distinct *technology options*, each at its own allowed process
pressure. A lower Fe manufacturing-proxy cost is a source-window-constrained
**technology selection**, NOT evidence that Fe has better intrinsic kinetics
at a common measured experimental pressure: those pressure domains do not
overlap. Source T/P adherence alone does not validate other mixture and
industrial constraints, including the low-temperature PR SI temperature
correlation domain.

**Level C, broad 235-bar Ru conditional engineering study:** PFR and SI
process model extrapolate the promoted Ru/C kinetics well above 100 bar.
Cost proximity or finance-boundary results here are conditional and should
appear in SI/Discussion as mechanism tests, never promoted to an
experimentally pressure-validated Fe/Ru ranking.

## Independent local atlas and precision

A separate already computed 1,264-design atlas was extended with source-domain
Ru/C 50–100 bar searches and adaptive bounded optimization. The independent
local result is in the companion downloadable archive; source-window grid
minima and source-window local candidates both prefer Fe, but numerical
values may differ from this GH CI implementation because their process
adapters and cost boundaries are not byte-identical. Never silently
substitute one absolute cost into the other's table.

This PR's CI is the independent, fully source-pinned implementation on top of
PR #93. Its own numerical results, cost bridge and **all 45** finance /
recovery / H2 economic variations are regenerated in GitHub Actions. CI PASS
means reproducible computations and correct evidence provenance, not an
externally validated industrial process simulation.

## Next experiment after pressure-domain audit

The strongest external scientific lift is matched kinetic data in an
**overlapping P/T window** for Fe and Ru formulations. Cholewa et al.
*Sustainable Energy & Fuels* (2024), DOI 10.1039/D4SE00254G, reports matched
Fe and **Ru/CeO2**, not promoted Ru/C, at 10–80 bar. Only a
formulation-labelled new experiment/data model can use those measurements;
the catalysts must never be silently relabelled as interchangeable.

## Running this branch

```bash
python -m unittest discover -s analysis/nh3_fe_first_domain_v1 -p 'test_*.py' -v
python analysis/nh3_kinetic_cost_coupling_v1/run_study.py --out-dir artifacts/nh3-domain/base
python analysis/nh3_kinetic_cost_coupling_v1/run_study.py --out-dir artifacts/nh3-domain/base --retry-unresolved
python analysis/nh3_fe_first_domain_v1/source_domains.py --baseline-dir artifacts/nh3-domain/base --out-dir artifacts/nh3-domain/pressure-window
```

Actions: `.github/workflows/nh3-fe-first-source-domains.yml`.
Output: machine-readable complete scenario and failure ledger, updated model
source applicability report, candidate grid and cost bridge. Run is deliberately
separate from all frozen/merged figure and manuscript validations.
