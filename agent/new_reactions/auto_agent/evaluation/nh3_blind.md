# NH3 blind evaluation

Loader: 237/237; rejected 0.

| Hand convention | Changed/groups | >5% | Paper bootstrap 95% CI |
|---|---:|---:|---|
| printed | 12/44 | 8 | [0.13636363636363635, 0.41304347826086957] |

Unit conversion and ranking rules: see blind_eval.py module docstring.
The raised-conversion hand comparison retains its own frozen scenario. AI inputs are the same measured records.
NH3 hand costs are reduced catalyst-dependent costs; feed cost is outside that boundary.

## nh3_b1

Costed 237/237; scored records 237.
AI ranking: {"groups": 44, "papers": 31, "changed": 11, "gt5pct": 11, "fraction": 0.25, "ci95": [0.08691026827012026, 0.4], "bootstrap": {"draws": 2000, "seed": 20261006, "unit": "paper"}}

| Reference quantity | Hand | AI | Relative gap |
|---|---|---|---|
| cost_usd_per_t | 11.515783597179267 | 714.4771178632146 | 61.043291438562825 |
| parts.feed | 0.0 | 556.2301158511779 | None |
| shares.feed | 0.0 | 0.7785135478021944 | None |
| parts.energy | 7.598967948092639 | 62.74101546600043 | 7.256517976463973 |
| shares.energy | 0.6598741530670972 | 0.08781389060245885 | -0.8669232759090508 |
| parts.capital | 3.7915922812770635 | 90.96669755534671 | 22.99168760959388 |
| shares.capital | 0.3292517829360561 | 0.12731925947103898 | -0.6133073044109663 |
| parts.catalyst | 0.12522336780956467 | 4.539288990689574 | 35.24953608972382 |
| shares.catalyst | 0.010874063996846685 | 0.006353302124307657 | -0.41573802341516297 |
| parts.other | 0.0 | 0.0 | None |
| shares.other | 0.0 | 0.0 | None |
| operating.T_K | 698.15 | 700.0 | 0.002649860345198096 |
| operating.P_bar | 105.0 | 150.0 | 0.4285714285714286 |
| operating.per_pass_conversion | 0.17205887115595606 | 0.34392795119701525 | 0.9988969408341355 |
| balances.capacity_t_per_y | 346750.0 | 330000.0 | -0.048305695746214905 |
| balances.energy_GJ_per_t | 0.54712569226267 | 7.058364239925048 | 11.900809338224956 |
| basis.battery_limit | Reduced catalyst-dependent NH3 cost. NH3-FINAL-1.1 adds the pressure-attributable converter-shell cost and the compressor bare-module CAPEX; loop heat exchangers, separator vessel and piping remain outside the boundary (declared omission; direction: further penalizes high pressure). Purchased feed costs excluded. | Pure hydrogen and nitrogen at the plant boundary through synthesis-loop compression, heat recovery, catalytic conversion, ammonia condensation/separation, recycle and purge, to pressurized liquid ammonia product; upstream H2 production and air separation are excluded but feed consumption is charged. | None |
| basis.capacity_t_per_y | 346750.0 | 330000 | -0.048305695746214905 |
| basis.feeds.H2.P_bar | 30 | 1.0 | -0.9666666666666667 |
| basis.feeds.H2.T_K | 298.15 | 298.15 | 0.0 |
| basis.feeds.H2.purity_mol_frac | 1 | 1.0 | 0.0 |
| basis.feeds.H2O.P_bar | None | 3.0 | None |
| basis.feeds.H2O.T_K | None | 298.15 | None |
| basis.feeds.H2O.purity_mol_frac | None | 1.0 | None |
| basis.feeds.N2.P_bar | 30 | 1.0 | -0.9666666666666667 |
| basis.feeds.N2.T_K | 298.15 | 298.15 | 0.0 |
| basis.feeds.N2.purity_mol_frac | 1 | 1.0 | 0.0 |
| basis.operating_hours_per_y | 8322.0 | 8000 | -0.03869262196587364 |
| basis.product.NH3.P_bar | 105.0 | 20.0 | -0.8095238095238095 |
| basis.product.NH3.T_K | 303.15 | None | None |
| basis.product.NH3.purity_mol_frac | None | 1.0 | None |
| basis.product.NH3.state | condensed at separator | None | None |
| basis.purchased_preheat_reason | None | None | None |
| basis.utilities.ambient_temperature | None | 298.15 | None |
| basis.utilities.cooling_water_return_temperature | None | 308.15 | None |
| basis.utilities.cooling_water_supply_temperature | None | 298.15 | None |
| basis.utilities.electricity_primary_energy_factor | None | 2.5 | None |

### Group comparison: printed

Compared 44; verdict agreement 35; pooled cost Spearman 0.12446318271799924.

| Group | Complete | Hand changed | AI changed | Verdict agrees | Hand gap | AI gap | Plant leader agrees | Within-group cost Spearman |
|---|---|---|---|---|---:|---:|---|---:|
| 10.1002/aenm.201801772 / 400 C / 0.1 MPa / H2/N2 3 / 6.6e+04 mL/g/h | True | True | True | True | 0.3726866579010617 | 0.2006965212206835 | True | 0.9999999999999999 |
| 10.1002/aenm.201801772 / 400 C / 5 MPa / H2/N2 3 / 6.6e+04 mL/g/h | True | True | True | True | 0.13764479669840068 | 0.12756501824566535 | True | 0.4230769230769231 |
| 10.1002/anie.201712398 / 300 C / 0.9 MPa / H2/N2 3 / 3.6e+04 mL/g/h | True | True | True | True | 0.22051247667258944 | 0.9175678517081478 | False | 0.9642857142857145 |
| 10.1002/anie.201907171 / 400 C / 1 MPa / H2/N2 3 / SV not given | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1002/anie.201907171 / 459 C / 1 MPa / H2/N2 3 / SV not given | True | True | True | True | 0.2521433032419236 | 0.21860997010510808 | True | 0.5 |
| 10.1002/anie.201907171 / 459 C / 5 MPa / H2/N2 3 / SV not given | True | False | True | False | 0.0 | 0.14485741482916326 | False | -0.6000000000000001 |
| 10.1002/asia.201900618 / 400 C / 3 MPa / H2/N2 3 / 2.4e+04 mL/g/h | True | False | True | False | 0.0 | 0.17303434418269137 | False | -0.9999999999999999 |
| 10.1002/asia.201900618 / 450 C / 3 MPa / H2/N2 3 / 2.4e+04 mL/g/h | True | True | True | True | 0.011003879980802544 | 0.08359159856502107 | True | 0.39999999999999997 |
| 10.1007/s10562-019-02674-1 / 450 C / 3 MPa / H2/N2 3 / 2.4e+04 mL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1021/acs.chemmater.9b03099 / 375 C / 0.1 MPa / H2/N2 3 / 1.8e+04 mL/g/h | True | True | False | False | 0.023580082421838622 | 0.0 | False | -0.5 |
| 10.1021/acs.iecr.8b02126 / 400 C / 1 MPa / H2/N2 3 / 6e+04 mL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1021/acs.iecr.9b01610 / 400 C / 1 MPa / H2/N2 3 / 6e+04 mL/g/h | True | False | False | True | 0.0 | 0.0 | True | 1.0 |
| 10.1021/acs.jpcc.7b07268 / 340 C / 0.1 MPa / H2/N2 3 / 3.6e+04 mL/g/h | True | True | False | False | 0.05394087067900166 | 0.0 | False | -0.9999999999999999 |
| 10.1021/acscatal.1c02887 / 350 C / 1 MPa / H2/N2 3 / 7.2e+04 mL/g/h | True | False | False | True | 0.0 | 0.0 | True | 1.0 |
| 10.1021/acscatal.1c02887 / 400 C / 6 MPa / H2/N2 3 / 7.2e+04 mL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1021/acscatal.7b00284 / 300 C / 1 MPa / H2/N2 3 / 6e+04 mL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1021/acscatal.8b02839 / 340 C / 0.1 MPa / H2/N2 3 / 3.6e+04 mL/g/h | True | False | False | True | 0.0 | 0.0 | True | 1.0 |
| 10.1021/acscatal.8b03554 / 400 C / 1 MPa / H2/N2 3 / 1.8e+04 mL/g/h | True | False | False | True | 0.0 | 0.0 | True | 1.0 |
| 10.1021/acscatal.8b03554 / 400 C / 1 MPa / H2/N2 3 / 6e+04 mL/g/h | True | False | False | True | 0.0 | 0.0 | True | 1.0 |
| 10.1021/acscatal.8b03650 / 340 C / 0.1 MPa / H2/N2 3 / 1.8e+04 mL/g/h | True | False | False | True | 0.0 | 0.0 | True | 1.0 |
| 10.1021/acscatal.8b03743 / 340 C / 0.1 MPa / H2/N2 3 / 3.6e+04 mL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1021/acssuschemeng.8b04683 / 400 C / 1 MPa / H2/N2 3 / 7.2e+04 mL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1021/cs401044a / 340 C / 0.1 MPa / H2/N2 3 / 1.8e+04 mL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1021/jacs.0c06624 / 400 C / 0.9 MPa / H2/N2 3 / 3.6e+04 mL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1021/jacs.7b08891 / 400 C / 5.1 MPa / H2/N2 3 / 6.6e+04 mL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1021/jacs.9b10726 / 400 C / 0.9 MPa / H2/N2 3 / 3.6e+04 mL/g/h | True | True | False | False | 0.2873732745288964 | 0.0 | False | 0.5 |
| 10.1038/nchem.1476 / 320 C / 0.1 MPa / H2/N2 3 / 1.8e+04 mL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.4285714285714286 |
| 10.1038/nchem.1476 / 400 C / 0.1 MPa / H2/N2 3 / 1.8e+04 mL/g/h | True | False | True | False | 0.0 | 0.2947112627297104 | False | 0.8999999999999998 |
| 10.1038/nchem.1476 / 400 C / 1 MPa / H2/N2 3 / 1.8e+04 mL/g/h | True | False | True | False | 0.0 | 0.49638619681055696 | False | -0.14285714285714288 |
| 10.1038/s41467-020-15868-8 / 300 C / 0.1 MPa / H2/N2 3 / 3.6e+04 mL/g/h | True | True | True | True | 0.11814062966870109 | 0.8902089936637938 | True | 0.8928571428571429 |
| 10.1038/s41467-020-15868-8 / 340 C / 0.1 MPa / H2/N2 3 / 3.6e+04 mL/g/h | True | True | True | True | 0.28264737930732764 | 0.31843349353845896 | True | 0.8571428571428572 |
| 10.1038/s41586-020-2464-9 / 340 C / 0.1 MPa / H2/N2 3 / 3.6e+04 mL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1039/c6cy02089e / 380 C / 1 MPa / H2/N2 3 / 1.8e+04 mL/g/h | True | False | False | True | 0.0 | 0.0 | True | 1.0 |
| 10.1039/c6cy02089e / 380 C / 3 MPa / H2/N2 3 / SV not given | True | False | False | True | 0.0 | 0.0 | True | 1.0 |
| 10.1039/c6cy02089e / 400 C / 1 MPa / H2/N2 3 / 1.8e+04 mL/g/h | True | True | False | False | 0.02438687018126262 | 0.0 | False | 0.8787878787878788 |
| 10.1039/c6cy02089e / 400 C / 3 MPa / H2/N2 3 / 1.8e+04 mL/g/h | True | False | False | True | 0.0 | 0.0 | True | 1.0 |
| 10.1039/c6sc00767h / 300 C / 0.1 MPa / H2/N2 3 / 3.6e+04 mL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.6 |
| 10.1039/c6sc00767h / 340 C / 0.1 MPa / H2/N2 3 / 3.6e+04 mL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.8999999999999998 |
| 10.1039/c6sc02382g / 390 C / 0.9 MPa / H2/N2 3 / 1.8e+04 mL/g/h | True | False | False | True | 0.0 | 0.0 | True | 1.0 |
| 10.1039/c7sc05343f / 350 C / 1 MPa / H2/N2 3 / 7.2e+04 mL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.6904761904761906 |
| 10.1039/c8qi01244j / 425 C / 1 MPa / H2/N2 3 / SV not given | True | False | False | True | 0.0 | 0.0 | True | 1.0 |
| 10.1039/c9cc07385j / 400 C / 1 MPa / H2/N2 3 / 3.6e+04 mL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1039/c9ra03097b / 400 C / 10 MPa / H2/N2 3 / SV not given | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1039/d0ta05238h / 450 C / 1 MPa / H2/N2 3 / 1.6e+04 mL/g/h | True | True | False | False | 0.015008780423757972 | 0.0 | False | 0.7 |

### Bottlenecks

```json
{
  "largest_cost_item": "feed",
  "hand_largest_cost_item": "energy",
  "controlling_property": "activity",
  "hand_controlling_property": "not available",
  "attribution_share": {
    "selectivity": 0.0,
    "activity": 0.947,
    "temperature": 0.008,
    "stability": 0.0,
    "metal": 0.045
  },
  "cheapest_record": "nh3:0042",
  "cheapest_catalyst": "Co@BaO/MgO-700red",
  "hand_cheapest_record": "nh3:0231",
  "hand_cheapest_catalyst": "commercial Fe catalyst",
  "cheapest_common_record": "nh3:0042",
  "cheapest_common_catalyst": "Co@BaO/MgO-700red",
  "hand_cheapest_common_record": "nh3:0231",
  "hand_cheapest_common_catalyst": "commercial Fe catalyst"
}
```

### Difference diagnosis and uncertainty

```json
{
  "rules": "deterministic evidence comparison; categories are evidence, not causal proof",
  "largest_reference_gaps": [
    {
      "field": "cost_usd_per_t",
      "hand": 11.515783597179267,
      "ai": 714.4771178632146,
      "relative_gap": 61.043291438562825,
      "categories": [
        "boundary",
        "structure",
        "parameters"
      ],
      "rule": "basis mismatch -> boundary; cost/energy/capital -> unit structure and matched parameters; no automatic causal attribution"
    },
    {
      "field": "parts.catalyst",
      "hand": 0.12522336780956467,
      "ai": 4.539288990689574,
      "relative_gap": 35.24953608972382,
      "categories": [
        "structure",
        "parameters"
      ],
      "rule": "basis mismatch -> boundary; cost/energy/capital -> unit structure and matched parameters; no automatic causal attribution"
    },
    {
      "field": "parts.capital",
      "hand": 3.7915922812770635,
      "ai": 90.96669755534671,
      "relative_gap": 22.99168760959388,
      "categories": [
        "structure",
        "parameters"
      ],
      "rule": "basis mismatch -> boundary; cost/energy/capital -> unit structure and matched parameters; no automatic causal attribution"
    },
    {
      "field": "balances.energy_GJ_per_t",
      "hand": 0.54712569226267,
      "ai": 7.058364239925048,
      "relative_gap": 11.900809338224956,
      "categories": [
        "structure",
        "parameters"
      ],
      "rule": "basis mismatch -> boundary; cost/energy/capital -> unit structure and matched parameters; no automatic causal attribution"
    },
    {
      "field": "parts.energy",
      "hand": 7.598967948092639,
      "ai": 62.74101546600043,
      "relative_gap": 7.256517976463973,
      "categories": [
        "structure",
        "parameters"
      ],
      "rule": "basis mismatch -> boundary; cost/energy/capital -> unit structure and matched parameters; no automatic causal attribution"
    },
    {
      "field": "operating.per_pass_conversion",
      "hand": 0.17205887115595606,
      "ai": 0.34392795119701525,
      "relative_gap": 0.9988969408341355,
      "categories": [
        "structure",
        "parameters"
      ],
      "rule": "basis mismatch -> boundary; cost/energy/capital -> unit structure and matched parameters; no automatic causal attribution"
    },
    {
      "field": "basis.feeds.H2.P_bar",
      "hand": 30,
      "ai": 1.0,
      "relative_gap": -0.9666666666666667,
      "categories": [
        "boundary"
      ],
      "rule": "basis mismatch -> boundary; cost/energy/capital -> unit structure and matched parameters; no automatic causal attribution"
    },
    {
      "field": "basis.feeds.N2.P_bar",
      "hand": 30,
      "ai": 1.0,
      "relative_gap": -0.9666666666666667,
      "categories": [
        "boundary"
      ],
      "rule": "basis mismatch -> boundary; cost/energy/capital -> unit structure and matched parameters; no automatic causal attribution"
    },
    {
      "field": "shares.energy",
      "hand": 0.6598741530670972,
      "ai": 0.08781389060245885,
      "relative_gap": -0.8669232759090508,
      "categories": [
        "structure",
        "parameters"
      ],
      "rule": "basis mismatch -> boundary; cost/energy/capital -> unit structure and matched parameters; no automatic causal attribution"
    },
    {
      "field": "basis.product.NH3.P_bar",
      "hand": 105.0,
      "ai": 20.0,
      "relative_gap": -0.8095238095238095,
      "categories": [
        "boundary"
      ],
      "rule": "basis mismatch -> boundary; cost/energy/capital -> unit structure and matched parameters; no automatic causal attribution"
    },
    {
      "field": "shares.capital",
      "hand": 0.3292517829360561,
      "ai": 0.12731925947103898,
      "relative_gap": -0.6133073044109663,
      "categories": [
        "structure",
        "parameters"
      ],
      "rule": "basis mismatch -> boundary; cost/energy/capital -> unit structure and matched parameters; no automatic causal attribution"
    },
    {
      "field": "operating.P_bar",
      "hand": 105.0,
      "ai": 150.0,
      "relative_gap": 0.4285714285714286,
      "categories": [
        "structure",
        "parameters"
      ],
      "rule": "basis mismatch -> boundary; cost/energy/capital -> unit structure and matched parameters; no automatic causal attribution"
    }
  ],
  "largest_ranking_gaps": {
    "printed": [
      {
        "group": "10.1002/anie.201712398 | 300 C | 0.9 MPa | H2/N2 3 | 3.6e+04 mL/g/h",
        "hand_leader": "Industrial Fe catalyst",
        "ai_leader": "Co(8%)/Ba-Ca(NH2)2",
        "hand_gap": 0.22051247667258944,
        "ai_gap": 0.9175678517081478,
        "categories": [
          "structure",
          "parameters",
          "data",
          "boundary"
        ]
      },
      {
        "group": "10.1038/nchem.1476 | 400 C | 1 MPa | H2/N2 3 | 1.8e+04 mL/g/h",
        "hand_leader": "Ru-Cs/MgO",
        "ai_leader": "Ru/C12A7:e−",
        "hand_gap": 0.0,
        "ai_gap": 0.49638619681055696,
        "categories": [
          "structure",
          "parameters",
          "data",
          "boundary"
        ]
      },
      {
        "group": "10.1038/nchem.1476 | 400 C | 0.1 MPa | H2/N2 3 | 1.8e+04 mL/g/h",
        "hand_leader": "Ru-Ba/AC",
        "ai_leader": "Ru/C12A7:e−",
        "hand_gap": 0.0,
        "ai_gap": 0.2947112627297104,
        "categories": [
          "structure",
          "parameters",
          "data",
          "boundary"
        ]
      },
      {
        "group": "10.1021/jacs.9b10726 | 400 C | 0.9 MPa | H2/N2 3 | 3.6e+04 mL/g/h",
        "hand_leader": "Fe(1.2 wt %)/BaCeO3−xNyHz",
        "ai_leader": "Co(4.7 wt %)/BaCeO3−xNyHz",
        "hand_gap": 0.2873732745288964,
        "ai_gap": 0.0,
        "categories": [
          "structure",
          "parameters",
          "data",
          "boundary"
        ]
      },
      {
        "group": "10.1002/asia.201900618 | 400 C | 3 MPa | H2/N2 3 | 2.4e+04 mL/g/h",
        "hand_leader": "3.5% Ru/BaCeO3-a",
        "ai_leader": "4% Cs-1.25%Ru/BaCeO3-a",
        "hand_gap": 0.0,
        "ai_gap": 0.17303434418269137,
        "categories": [
          "structure",
          "parameters",
          "data",
          "boundary"
        ]
      },
      {
        "group": "10.1002/anie.201907171 | 459 C | 5 MPa | H2/N2 3 | SV not given",
        "hand_leader": "Ru-Li/MgO",
        "ai_leader": "Ba-Fe/AC",
        "hand_gap": 0.0,
        "ai_gap": 0.14485741482916326,
        "categories": [
          "structure",
          "parameters",
          "data",
          "boundary"
        ]
      },
      {
        "group": "10.1021/acs.jpcc.7b07268 | 340 C | 0.1 MPa | H2/N2 3 | 3.6e+04 mL/g/h",
        "hand_leader": "Ru/CaNH",
        "ai_leader": "Ru/Ca2NH",
        "hand_gap": 0.05394087067900166,
        "ai_gap": 0.0,
        "categories": [
          "structure",
          "parameters",
          "data",
          "boundary"
        ]
      },
      {
        "group": "10.1039/c6cy02089e | 400 C | 1 MPa | H2/N2 3 | 1.8e+04 mL/g/h",
        "hand_leader": "2K–Ru/r-CeO2",
        "ai_leader": "2Cs–Ru/r-CeO2",
        "hand_gap": 0.02438687018126262,
        "ai_gap": 0.0,
        "categories": [
          "structure",
          "parameters",
          "data",
          "boundary"
        ]
      },
      {
        "group": "10.1021/acs.chemmater.9b03099 | 375 C | 0.1 MPa | H2/N2 3 | 1.8e+04 mL/g/h",
        "hand_leader": "Ru SAs/S-1",
        "ai_leader": "Ba-Ru SAs/S-1",
        "hand_gap": 0.023580082421838622,
        "ai_gap": 0.0,
        "categories": [
          "structure",
          "parameters",
          "data",
          "boundary"
        ]
      },
      {
        "group": "10.1039/d0ta05238h | 450 C | 1 MPa | H2/N2 3 | 1.6e+04 mL/g/h",
        "hand_leader": "Magnetite based industrial Fe catalyst",
        "ai_leader": "80% Fe–20% Ce0.8Sm0.2O2−δ",
        "hand_gap": 0.015008780423757972,
        "ai_gap": 0.0,
        "categories": [
          "structure",
          "parameters",
          "data",
          "boundary"
        ]
      }
    ]
  },
  "ranking_disagreements": {
    "printed": 9
  },
  "findings": [
    {
      "category": "boundary",
      "evidence": "hand NH3 excludes purchased feeds; AI has positive feed cost",
      "impact": "total costs have different boundaries"
    },
    {
      "category": "boundary",
      "evidence": {
        "field": "feeds.N2.P_bar",
        "hand": 30,
        "ai": 1.0
      },
      "impact": "different plant design basis"
    },
    {
      "category": "boundary",
      "evidence": {
        "field": "feeds.H2.P_bar",
        "hand": 30,
        "ai": 1.0
      },
      "impact": "different plant design basis"
    },
    {
      "category": "boundary",
      "evidence": {
        "field": "product.NH3.P_bar",
        "hand": 105.0,
        "ai": 20.0
      },
      "impact": "different plant design basis"
    },
    {
      "category": "boundary",
      "evidence": {
        "field": "battery_limit",
        "hand": "Reduced catalyst-dependent NH3 cost. NH3-FINAL-1.1 adds the pressure-attributable converter-shell cost and the compressor bare-module CAPEX; loop heat exchangers, separator vessel and piping remain outside the boundary (declared omission; direction: further penalizes high pressure). Purchased feed costs excluded.",
        "ai": "Pure hydrogen and nitrogen at the plant boundary through synthesis-loop compression, heat recovery, catalytic conversion, ammonia condensation/separation, recycle and purge, to pressurized liquid ammonia product; upstream H2 production and air separation are excluded but feed consumption is charged."
      },
      "impact": "different plant design basis"
    },
    {
      "category": "boundary",
      "evidence": {
        "field": "operating_hours_per_y",
        "hand": 8322.0,
        "ai": 8000
      },
      "impact": "different plant design basis"
    },
    {
      "category": "boundary",
      "evidence": {
        "field": "capacity_t_per_y",
        "hand": 346750.0,
        "ai": 330000
      },
      "impact": "different plant design basis"
    },
    {
      "category": "structure",
      "evidence": {
        "hand_units": [
          "reactor",
          "fresh compression",
          "recycle compression",
          "refrigeration",
          "compressor capex"
        ],
        "ai_units": [
          {
            "name": "makeup_compressor",
            "type": "compressor"
          },
          {
            "name": "feed_mixer",
            "type": "other"
          },
          {
            "name": "feed_effluent_exchanger",
            "type": "heat_exchanger"
          },
          {
            "name": "ammonia_converter",
            "type": "reactor"
          },
          {
            "name": "waste_heat_boiler",
            "type": "heat_exchanger"
          },
          {
            "name": "ammonia_condenser",
            "type": "knockout"
          },
          {
            "name": "ammonia_separator",
            "type": "separation"
          },
          {
            "name": "purge_splitter",
            "type": "other"
          },
          {
            "name": "recycle_compressor",
            "type": "compressor"
          },
          {
            "name": "product_letdown_storage",
            "type": "other"
          },
          {
            "name": "utilities_offsites",
            "type": "offsites"
          }
        ],
        "ai_checklist": {
          "feed_preparation": {
            "included": [
              "makeup_compressor",
              "feed_mixer",
              "feed_effluent_exchanger"
            ]
          },
          "reactor_heat_supply_or_removal": {
            "included": [
              "ammonia_converter",
              "waste_heat_boiler",
              "feed_effluent_exchanger"
            ]
          },
          "catalyst_regeneration": {
            "excluded": "The synthesis catalysts are modeled as periodically replaced rather than regenerated in situ because the screened papers do not establish an industrial regeneration cycle."
          },
          "product_compression": {
            "excluded": "Ammonia leaves the high-pressure loop as condensed liquid above the specified 20 bar product boundary pressure, so letdown rather than product compression is required."
          },
          "separation_and_purification": {
            "included": [
              "ammonia_condenser",
              "ammonia_separator",
              "product_letdown_storage"
            ]
          },
          "recycle": {
            "included": [
              "purge_splitter",
              "recycle_compressor",
              "feed_mixer"
            ]
          },
          "heat_recovery": {
            "included": [
              "waste_heat_boiler",
              "feed_effluent_exchanger"
            ]
          },
          "utilities_and_offsites": {
            "included": [
              "utilities_offsites"
            ]
          }
        },
        "missing_hand_unit_types": [],
        "extra_ai_unit_types": [
          "heat_exchanger",
          "knockout",
          "offsites",
          "other",
          "separation"
        ],
        "ai_recycle_declaration": {
          "included": [
            "purge_splitter",
            "recycle_compressor",
            "feed_mixer"
          ]
        },
        "hand_kinetics": "NH3 descriptor microkinetics and 0.8 equilibrium approach"
      },
      "impact": "unit types are a screening comparison, not proof of causal impact; NH3 separator vessel is outside the reduced CAPEX boundary; checklist exclusions retained verbatim"
    },
    {
      "category": "parameters",
      "evidence": {
        "gaps_gt20pct": [],
        "unmatched_hand_parameters": [
          "calibration_factor",
          "catalyst_life_y",
          "compressor_efficiency",
          "discount_rate",
          "electricity_USD_MWh",
          "metal_recovery_fraction",
          "plant_life_y",
          "reactor_exponent",
          "reactor_fixed_USD",
          "reactor_reference_m3",
          "reactor_variable_USD"
        ],
        "hand_parameters": {
          "discount_rate": 0.12,
          "plant_life_y": 25,
          "electricity_USD_MWh": 50.0,
          "compressor_efficiency": 0.75,
          "catalyst_life_y": 10.0,
          "metal_recovery_fraction": 0.0,
          "reactor_fixed_USD": 66800.0,
          "reactor_variable_USD": 268000.0,
          "reactor_reference_m3": 20.0,
          "reactor_exponent": 0.52,
          "calibration_factor": 74351.60773111923
        },
        "ai_parameters": {
          "NH3_condensation_duty_GJ_per_t": 1.37,
          "base_capacity_t_per_y": 330000.0,
          "base_reactor_catalyst_volume_m3": 100.0,
          "basis.capacity_t_per_y": 330000.0,
          "basis.feeds.H2.P_bar": 1.0,
          "basis.feeds.H2.T_K": 298.15,
          "basis.feeds.H2.purity_mol_frac": 1.0,
          "basis.feeds.H2O.P_bar": 3.0,
          "basis.feeds.H2O.T_K": 298.15,
          "basis.feeds.H2O.purity_mol_frac": 1.0,
          "basis.feeds.N2.P_bar": 1.0,
          "basis.feeds.N2.T_K": 298.15,
          "basis.feeds.N2.purity_mol_frac": 1.0,
          "basis.operating_hours_per_y": 8000.0,
          "basis.product.NH3.P_bar": 20.0,
          "basis.product.NH3.purity_mol_frac": 1.0,
          "basis.utilities.ambient_temperature": 298.15,
          "basis.utilities.cooling_water_return_temperature": 308.15,
          "basis.utilities.cooling_water_supply_temperature": 298.15,
          "basis.utilities.electricity_primary_energy_factor": 2.5,
          "capex.ammonia_condenser": 18000000.0,
          "capex.ammonia_converter": 25000000.0,
          "capex.ammonia_separator": 8000000.0,
          "capex.feed_effluent_exchanger": 15000000.0,
          "capex.feed_mixer": 1000000.0,
          "capex.makeup_compressor": 20000000.0,
          "capex.product_letdown_storage": 15000000.0,
          "capex.purge_splitter": 500000.0,
          "capex.recycle_compressor": 12000000.0,
          "capex.utilities_offsites": 25000000.0,
          "capex.waste_heat_boiler": 12000000.0,
          "capex_scale_exponent": 0.6,
          "catalyst_bulk_density_kg_per_m3": 1000.0,
          "compressor_installed_usd_per_kW": 2000.0,
          "condenser_COP": 3.0,
          "condenser_temperature_K": 248.15,
          "default_catalyst_life_y": 3.0,
          "equilibrium_deltaH_J_per_mol_rxn": -92220.0,
          "equilibrium_deltaS_J_per_molK_rxn": -209.3,
          "feed_effluent_exchanger_effectiveness": 0.8,
          "gas_sensible_heat_kJ_per_kmol_K": 31.0,
          "loop_pressure_drop_bar": 5.0,
          "makeup_compressor_efficiency": 0.75,
          "minimum_rate_kg_per_kg_h": 1e-06,
          "nitrogen_electricity_kWh_per_kg": 0.2,
          "offsites_electric_GJ_per_t": 0.02,
          "pressure_capex_exponent": 0.25,
          "price.capital_recovery_factor": 0.0944,
          "price.catalyst_support_and_manufacturing": 20.0,
          "price.electricity": 80.0,
          "price.fixed_om_fraction_of_capex": 0.04,
          "price.hydrogen": 3.0,
          "price.metal_Al": 3.9683,
          "price.metal_B": 1.0,
          "price.metal_Ba": 0.3569000679809653,
          "price.metal_Ca": 0.3637940925436203,
          "price.metal_Ce": 2.1005306603773586,
          "price.metal_Co": 56.28401553583051,
          "price.metal_Cu": 13.889122517655,
          "price.metal_Fe": 8.0,
          "price.metal_K": 1.4455393066229791,
          "price.metal_La": 1.1728,
          "price.metal_Mg": 2.5,
          "price.metal_Mn": 0.45,
          "price.metal_Mo": 91.22728409215301,
          "price.metal_Ni": 16.9094555095895,
          "price.metal_Ru": 53852.5,
          "price.metal_Si": 2.866006,
          "price.metal_W": 149.97,
          "price.metal_Y": 40.0,
          "price.metal_Zr": 22.0,
          "purge_fraction": 0.01,
          "reaction_heat_GJ_per_t_NH3": 2.708,
          "recycle_compressor_efficiency": 0.78,
          "reference_P_bar": 150.0,
          "reference_T_K": 700.0,
          "reference_X": 0.15,
          "reference_r": 0.5,
          "reference_t_cycle_h": 24000.0,
          "separation_electric_GJ_per_t_at_reference": 0.15,
          "separator_NH3_recovery": 1.0,
          "unknown_Co_loading_fraction": 0.4,
          "unknown_Fe_loading_fraction": 0.8,
          "unknown_Mo_loading_fraction": 0.2,
          "unknown_Ru_loading_fraction": 0.05,
          "waste_heat_recovery_fraction": 0.7
        },
        "price_table_rows": [
          {
            "parameter": "price.hydrogen",
            "value": "3.0",
            "unit": "USD/kg",
            "source": "prices.json:hydrogen",
            "location": "prices.hydrogen",
            "type": "price_table",
            "low": "1.5",
            "high": "7.0"
          },
          {
            "parameter": "price.electricity",
            "value": "80.0",
            "unit": "USD/MWh",
            "source": "prices.json:electricity",
            "location": "prices.electricity",
            "type": "price_table",
            "low": "40.0",
            "high": "150.0"
          },
          {
            "parameter": "price.catalyst_support_and_manufacturing",
            "value": "20.0",
            "unit": "USD/kg",
            "source": "prices.json:catalyst_support_and_manufacturing",
            "location": "prices.catalyst_support_and_manufacturing",
            "type": "price_table",
            "low": "5.0",
            "high": "100.0"
          },
          {
            "parameter": "price.metal_Ru",
            "value": "53852.5",
            "unit": "USD/kg",
            "source": "prices.json:metal_Ru",
            "location": "prices.metal_Ru",
            "type": "price_table",
            "low": "26926.25",
            "high": "107705.0"
          },
          {
            "parameter": "price.metal_Fe",
            "value": "8.0",
            "unit": "USD/kg",
            "source": "prices.json:metal_Fe",
            "location": "prices.metal_Fe",
            "type": "price_table",
            "low": "4.0",
            "high": "16.0"
          },
          {
            "parameter": "price.metal_Co",
            "value": "56.28401553583051",
            "unit": "USD/kg",
            "source": "prices.json:metal_Co",
            "location": "prices.metal_Co",
            "type": "price_table",
            "low": "28.142007767915256",
            "high": "112.56803107166103"
          },
          {
            "parameter": "price.metal_Mo",
            "value": "91.22728409215301",
            "unit": "USD/kg",
            "source": "prices.json:metal_Mo",
            "location": "prices.metal_Mo",
            "type": "price_table",
            "low": "45.61364204607651",
            "high": "182.45456818430603"
          },
          {
            "parameter": "price.metal_Ni",
            "value": "16.9094555095895",
            "unit": "USD/kg",
            "source": "prices.json:metal_Ni",
            "location": "prices.metal_Ni",
            "type": "price_table",
            "low": "8.45472775479475",
            "high": "33.818911019179"
          },
          {
            "parameter": "price.metal_W",
            "value": "149.97",
            "unit": "USD/kg",
            "source": "prices.json:metal_W",
            "location": "prices.metal_W",
            "type": "price_table",
            "low": "74.985",
            "high": "299.94"
          },
          {
            "parameter": "price.metal_Cu",
            "value": "13.889122517655",
            "unit": "USD/kg",
            "source": "prices.json:metal_Cu",
            "location": "prices.metal_Cu",
            "type": "price_table",
            "low": "6.9445612588275",
            "high": "27.77824503531"
          },
          {
            "parameter": "price.metal_Al",
            "value": "3.9683",
            "unit": "USD/kg",
            "source": "prices.json:metal_Al",
            "location": "prices.metal_Al",
            "type": "price_table",
            "low": "1.98415",
            "high": "7.9366"
          },
          {
            "parameter": "price.metal_La",
            "value": "1.1728",
            "unit": "USD/kg",
            "source": "prices.json:metal_La",
            "location": "prices.metal_La",
            "type": "price_table",
            "low": "0.5864",
            "high": "2.3456"
          },
          {
            "parameter": "price.metal_Mn",
            "value": "0.45",
            "unit": "USD/kg",
            "source": "prices.json:metal_Mn",
            "location": "prices.metal_Mn",
            "type": "price_table",
            "low": "0.225",
            "high": "0.9"
          },
          {
            "parameter": "price.metal_Y",
            "value": "40.0",
            "unit": "USD/kg",
            "source": "prices.json:metal_Y",
            "location": "prices.metal_Y",
            "type": "price_table",
            "low": "20.0",
            "high": "80.0"
          },
          {
            "parameter": "price.metal_Zr",
            "value": "22.0",
            "unit": "USD/kg",
            "source": "prices.json:metal_Zr",
            "location": "prices.metal_Zr",
            "type": "price_table",
            "low": "11.0",
            "high": "44.0"
          },
          {
            "parameter": "price.metal_Ce",
            "value": "2.1005306603773586",
            "unit": "USD/kg",
            "source": "prices.json:metal_Ce",
            "location": "prices.metal_Ce",
            "type": "price_table",
            "low": "1.0502653301886793",
            "high": "4.201061320754717"
          },
          {
            "parameter": "price.metal_Si",
            "value": "2.866006",
            "unit": "USD/kg",
            "source": "prices.json:metal_Si",
            "location": "prices.metal_Si",
            "type": "price_table",
            "low": "1.433003",
            "high": "5.732012"
          },
          {
            "parameter": "price.metal_Mg",
            "value": "2.5",
            "unit": "USD/kg",
            "source": "prices.json:metal_Mg",
            "location": "prices.metal_Mg",
            "type": "price_table",
            "low": "1.25",
            "high": "5.0"
          },
          {
            "parameter": "price.metal_Ca",
            "value": "0.3637940925436203",
            "unit": "USD/kg",
            "source": "prices.json:metal_Ca",
            "location": "prices.metal_Ca",
            "type": "price_table",
            "low": "0.18189704627181014",
            "high": "0.7275881850872405"
          },
          {
            "parameter": "price.metal_K",
            "value": "1.4455393066229791",
            "unit": "USD/kg",
            "source": "prices.json:metal_K",
            "location": "prices.metal_K",
            "type": "price_table",
            "low": "0.7227696533114896",
            "high": "2.8910786132459583"
          },
          {
            "parameter": "price.metal_Ba",
            "value": "0.3569000679809653",
            "unit": "USD/kg",
            "source": "prices.json:metal_Ba",
            "location": "prices.metal_Ba",
            "type": "price_table",
            "low": "0.17845003399048265",
            "high": "0.7138001359619306"
          },
          {
            "parameter": "price.metal_B",
            "value": "1.0",
            "unit": "USD/kg",
            "source": "prices.json:metal_B",
            "location": "prices.metal_B",
            "type": "price_table",
            "low": "0.5",
            "high": "2.0"
          },
          {
            "parameter": "price.capital_recovery_factor",
            "value": "0.0944",
            "unit": "1/y",
            "source": "prices.json:capital_recovery_factor",
            "location": "prices.capital_recovery_factor",
            "type": "price_table",
            "low": "0.08",
            "high": "0.13"
          },
          {
            "parameter": "price.fixed_om_fraction_of_capex",
            "value": "0.04",
            "unit": "1/y",
            "source": "prices.json:fixed_om_fraction_of_capex",
            "location": "prices.fixed_om_fraction_of_capex",
            "type": "price_table",
            "low": "0.02",
            "high": "0.06"
          }
        ]
      },
      "impact": "price-table values fixed by construction; only identical parameter names compared numerically; unmatched values remain unresolved"
    },
    {
      "category": "data",
      "evidence": {
        "rejected": [],
        "converted": 237,
        "total": 237,
        "missing_loading_records": 0
      },
      "impact": "unknown composition loading and inherited outlet/density assumptions may affect catalyst inventory and ranking"
    },
    {
      "category": "numerics",
      "evidence": "all converted record costs finite, positive and parts close; deterministic repeat checked",
      "impact": "does not verify the optimiser reaches a global minimum"
    }
  ],
  "uncertainty": {
    "hand": {
      "draws": 1000,
      "seed": 20260816,
      "Fe_sigma_eV": 0.2271258177356984,
      "other_uniform_half_width_eV": 0.15
    },
    "ai_assumptions": [
      {
        "parameter": "basis.capacity_t_per_y",
        "value": "330000",
        "unit": "",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "100000",
        "high": "1000000"
      },
      {
        "parameter": "basis.operating_hours_per_y",
        "value": "8000",
        "unit": "",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "7200",
        "high": "8400"
      },
      {
        "parameter": "basis.feeds.N2.T_K",
        "value": "298.15",
        "unit": "",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "288.15",
        "high": "313.15"
      },
      {
        "parameter": "basis.feeds.N2.P_bar",
        "value": "1.0",
        "unit": "",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "1.0",
        "high": "30.0"
      },
      {
        "parameter": "basis.feeds.N2.purity_mol_frac",
        "value": "1.0",
        "unit": "",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.995",
        "high": "1.0"
      },
      {
        "parameter": "basis.feeds.H2.T_K",
        "value": "298.15",
        "unit": "",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "288.15",
        "high": "313.15"
      },
      {
        "parameter": "basis.feeds.H2.P_bar",
        "value": "1.0",
        "unit": "",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "1.0",
        "high": "30.0"
      },
      {
        "parameter": "basis.feeds.H2.purity_mol_frac",
        "value": "1.0",
        "unit": "",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.995",
        "high": "1.0"
      },
      {
        "parameter": "basis.feeds.H2O.T_K",
        "value": "298.15",
        "unit": "",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "288.15",
        "high": "303.15"
      },
      {
        "parameter": "basis.feeds.H2O.P_bar",
        "value": "3.0",
        "unit": "",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "2.0",
        "high": "6.0"
      },
      {
        "parameter": "basis.feeds.H2O.purity_mol_frac",
        "value": "1.0",
        "unit": "",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.99",
        "high": "1.0"
      },
      {
        "parameter": "basis.product.NH3.P_bar",
        "value": "20.0",
        "unit": "",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "10.0",
        "high": "30.0"
      },
      {
        "parameter": "basis.product.NH3.purity_mol_frac",
        "value": "1.0",
        "unit": "",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.995",
        "high": "1.0"
      },
      {
        "parameter": "basis.utilities.ambient_temperature",
        "value": "298.15",
        "unit": "K",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "288.15",
        "high": "308.15"
      },
      {
        "parameter": "basis.utilities.cooling_water_supply_temperature",
        "value": "298.15",
        "unit": "K",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "288.15",
        "high": "303.15"
      },
      {
        "parameter": "basis.utilities.cooling_water_return_temperature",
        "value": "308.15",
        "unit": "K",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "303.15",
        "high": "318.15"
      },
      {
        "parameter": "basis.utilities.electricity_primary_energy_factor",
        "value": "2.5",
        "unit": "GJ_primary/GJ_electric",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "1.5",
        "high": "3.2"
      },
      {
        "parameter": "reference_X",
        "value": "0.15",
        "unit": "fraction",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.08",
        "high": "0.25"
      },
      {
        "parameter": "reference_r",
        "value": "0.5",
        "unit": "kg NH3/kgcat/h",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.05",
        "high": "2.0"
      },
      {
        "parameter": "reference_t_cycle_h",
        "value": "24000",
        "unit": "h to 10% loss",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "8000",
        "high": "80000"
      },
      {
        "parameter": "recycle_compressor_efficiency",
        "value": "0.78",
        "unit": "fraction",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.65",
        "high": "0.88"
      },
      {
        "parameter": "loop_pressure_drop_bar",
        "value": "5.0",
        "unit": "bar",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "2.0",
        "high": "12.0"
      },
      {
        "parameter": "feed_effluent_exchanger_effectiveness",
        "value": "0.8",
        "unit": "fraction",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.65",
        "high": "0.92"
      },
      {
        "parameter": "waste_heat_recovery_fraction",
        "value": "0.7",
        "unit": "fraction",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.4",
        "high": "0.9"
      },
      {
        "parameter": "separator_NH3_recovery",
        "value": "1.0",
        "unit": "fraction",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.98",
        "high": "1.0"
      },
      {
        "parameter": "purge_fraction",
        "value": "0.01",
        "unit": "fraction",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.002",
        "high": "0.05"
      },
      {
        "parameter": "condenser_temperature_K",
        "value": "248.15",
        "unit": "K",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "233.15",
        "high": "273.15"
      },
      {
        "parameter": "condenser_COP",
        "value": "3.0",
        "unit": "GJ cooling/GJ electric",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "1.5",
        "high": "5.0"
      },
      {
        "parameter": "NH3_condensation_duty_GJ_per_t",
        "value": "1.37",
        "unit": "GJ/t NH3",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "1.1",
        "high": "1.6"
      },
      {
        "parameter": "gas_sensible_heat_kJ_per_kmol_K",
        "value": "31.0",
        "unit": "kJ/kmol/K",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "28.0",
        "high": "38.0"
      },
      {
        "parameter": "separation_electric_GJ_per_t_at_reference",
        "value": "0.15",
        "unit": "GJ electric/t NH3",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.05",
        "high": "0.40"
      },
      {
        "parameter": "offsites_electric_GJ_per_t",
        "value": "0.02",
        "unit": "GJ electric/t NH3",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.005",
        "high": "0.08"
      },
      {
        "parameter": "nitrogen_electricity_kWh_per_kg",
        "value": "0.2",
        "unit": "kWh/kg N2",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.1",
        "high": "0.4"
      },
      {
        "parameter": "catalyst_bulk_density_kg_per_m3",
        "value": "1000.0",
        "unit": "kg/m3",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "600",
        "high": "1800"
      },
      {
        "parameter": "default_catalyst_life_y",
        "value": "3.0",
        "unit": "y",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "1.0",
        "high": "8.0"
      },
      {
        "parameter": "minimum_rate_kg_per_kg_h",
        "value": "1e-06",
        "unit": "kg/kg/h",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "1e-07",
        "high": "0.0001"
      },
      {
        "parameter": "unknown_Ru_loading_fraction",
        "value": "0.05",
        "unit": "kg/kg catalyst",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.01",
        "high": "0.15"
      },
      {
        "parameter": "unknown_Fe_loading_fraction",
        "value": "0.8",
        "unit": "kg/kg catalyst",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.3",
        "high": "0.95"
      },
      {
        "parameter": "unknown_Co_loading_fraction",
        "value": "0.4",
        "unit": "kg/kg catalyst",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.1",
        "high": "0.7"
      },
      {
        "parameter": "unknown_Mo_loading_fraction",
        "value": "0.2",
        "unit": "kg/kg catalyst",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.05",
        "high": "0.5"
      },
      {
        "parameter": "capex_scale_exponent",
        "value": "0.6",
        "unit": "dimensionless",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.5",
        "high": "0.8"
      },
      {
        "parameter": "pressure_capex_exponent",
        "value": "0.25",
        "unit": "dimensionless",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.15",
        "high": "0.5"
      },
      {
        "parameter": "base_capacity_t_per_y",
        "value": "330000.0",
        "unit": "t/y",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "100000",
        "high": "1000000"
      },
      {
        "parameter": "capex.makeup_compressor",
        "value": "20000000.0",
        "unit": "USD",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "8000000",
        "high": "60000000"
      },
      {
        "parameter": "capex.feed_mixer",
        "value": "1000000.0",
        "unit": "USD",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "300000",
        "high": "3000000"
      },
      {
        "parameter": "capex.feed_effluent_exchanger",
        "value": "15000000.0",
        "unit": "USD",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "5000000",
        "high": "40000000"
      },
      {
        "parameter": "capex.ammonia_converter",
        "value": "25000000.0",
        "unit": "USD",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "10000000",
        "high": "70000000"
      },
      {
        "parameter": "capex.waste_heat_boiler",
        "value": "12000000.0",
        "unit": "USD",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "4000000",
        "high": "35000000"
      },
      {
        "parameter": "capex.ammonia_condenser",
        "value": "18000000.0",
        "unit": "USD",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "7000000",
        "high": "50000000"
      },
      {
        "parameter": "capex.ammonia_separator",
        "value": "8000000.0",
        "unit": "USD",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "3000000",
        "high": "25000000"
      },
      {
        "parameter": "capex.purge_splitter",
        "value": "500000.0",
        "unit": "USD",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "100000",
        "high": "2000000"
      },
      {
        "parameter": "capex.recycle_compressor",
        "value": "12000000.0",
        "unit": "USD",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "4000000",
        "high": "40000000"
      },
      {
        "parameter": "capex.product_letdown_storage",
        "value": "15000000.0",
        "unit": "USD",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "5000000",
        "high": "50000000"
      },
      {
        "parameter": "capex.utilities_offsites",
        "value": "25000000.0",
        "unit": "USD",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "10000000",
        "high": "80000000"
      },
      {
        "parameter": "equilibrium_deltaH_J_per_mol_rxn",
        "value": "-92220.0",
        "unit": "J/mol reaction",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "-95000",
        "high": "-90000"
      },
      {
        "parameter": "equilibrium_deltaS_J_per_molK_rxn",
        "value": "-209.3",
        "unit": "J/mol/K reaction",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "-215",
        "high": "-195"
      },
      {
        "parameter": "base_reactor_catalyst_volume_m3",
        "value": "100.0",
        "unit": "m3",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "30.0",
        "high": "500.0"
      },
      {
        "parameter": "compressor_installed_usd_per_kW",
        "value": "2000.0",
        "unit": "USD/kW",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "700.0",
        "high": "5000.0"
      }
    ]
  }
}
```
## nh3_b2

Costed 237/237; scored records 237.
AI ranking: {"groups": 44, "papers": 31, "changed": 11, "gt5pct": 0, "fraction": 0.25, "ci95": [0.08691026827012026, 0.4], "bootstrap": {"draws": 2000, "seed": 20261006, "unit": "paper"}}

| Reference quantity | Hand | AI | Relative gap |
|---|---|---|---|
| cost_usd_per_t | 11.515783597179267 | 618.8814095765105 | 52.742014544985224 |
| parts.feed | 0.0 | 563.5624058543963 | None |
| shares.feed | 0.0 | 0.9106145331462323 | None |
| parts.energy | 7.598967948092639 | 26.990603992608015 | 2.551877594033375 |
| shares.energy | 0.6598741530670972 | 0.043611915909830296 | -0.9339087374355822 |
| parts.capital | 3.7915922812770635 | 21.944207275442736 | 4.787596779274908 |
| shares.capital | 0.3292517829360561 | 0.03545785498785424 | -0.8923077813834026 |
| parts.catalyst | 0.12522336780956467 | 6.384192454063411 | 49.98243695036432 |
| shares.catalyst | 0.010874063996846685 | 0.01031569595608309 | -0.05134860719281342 |
| parts.other | 0.0 | 0.0 | None |
| shares.other | 0.0 | 0.0 | None |
| operating.T_K | 698.15 | 725.0 | 0.03845878392895519 |
| operating.P_bar | 105.0 | 250.0 | 1.380952380952381 |
| operating.per_pass_conversion | 0.17205887115595606 | 0.3818669251173074 | 1.2193968991646993 |
| balances.capacity_t_per_y | 346750.0 | 1000000.0 | 1.883922134102379 |
| balances.energy_GJ_per_t | 0.54712569226267 | 3.0364429491684017 | 4.549808740677148 |
| basis.battery_limit | Reduced catalyst-dependent NH3 cost. NH3-FINAL-1.1 adds the pressure-attributable converter-shell cost and the compressor bare-module CAPEX; loop heat exchangers, separator vessel and piping remain outside the boundary (declared omission; direction: further penalizes high pressure). Purchased feed costs excluded. | Purchased purified H2 and N2 at the synthesis-plant gate through pressurization, stoichiometric mixing, heat recovery/preheat, catalytic synthesis, cooling/condensation, gas recycle and purge, liquid-ammonia product handling, and synthesis-loop utilities/offsites; upstream H2 and N2 manufacture and downstream ammonia distribution are excluded. | None |
| basis.capacity_t_per_y | 346750.0 | 1000000 | 1.883922134102379 |
| basis.feeds.H2.P_bar | 30 | 30.0 | 0.0 |
| basis.feeds.H2.T_K | 298.15 | 298.15 | 0.0 |
| basis.feeds.H2.purity_mol_frac | 1 | 0.999 | -0.0010000000000000009 |
| basis.feeds.N2.P_bar | 30 | 30.0 | 0.0 |
| basis.feeds.N2.T_K | 298.15 | 298.15 | 0.0 |
| basis.feeds.N2.purity_mol_frac | 1 | 0.999 | -0.0010000000000000009 |
| basis.operating_hours_per_y | 8322.0 | 8000 | -0.03869262196587364 |
| basis.product.NH3.P_bar | 105.0 | 20.0 | -0.8095238095238095 |
| basis.product.NH3.T_K | 303.15 | None | None |
| basis.product.NH3.purity_mol_frac | None | 0.995 | None |
| basis.product.NH3.state | condensed at separator | None | None |
| basis.purchased_preheat_reason | None | None | None |
| basis.utilities.cooling_water_return_temperature | None | 308.15 | None |
| basis.utilities.cooling_water_supply_temperature | None | 298.15 | None |
| basis.utilities.electric_motor_efficiency | None | 0.95 | None |

### Group comparison: printed

Compared 44; verdict agreement 35; pooled cost Spearman 0.538384013211745.

| Group | Complete | Hand changed | AI changed | Verdict agrees | Hand gap | AI gap | Plant leader agrees | Within-group cost Spearman |
|---|---|---|---|---|---:|---:|---|---:|
| 10.1002/aenm.201801772 / 400 C / 0.1 MPa / H2/N2 3 / 6.6e+04 mL/g/h | True | True | True | True | 0.3726866579010617 | 0.013691435208098124 | True | 0.9999999999999999 |
| 10.1002/aenm.201801772 / 400 C / 5 MPa / H2/N2 3 / 6.6e+04 mL/g/h | True | True | True | True | 0.13764479669840068 | 0.030839861750248776 | True | 0.39010989010989006 |
| 10.1002/anie.201712398 / 300 C / 0.9 MPa / H2/N2 3 / 3.6e+04 mL/g/h | True | True | True | True | 0.22051247667258944 | 0.04495978991689187 | False | 0.9642857142857145 |
| 10.1002/anie.201907171 / 400 C / 1 MPa / H2/N2 3 / SV not given | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1002/anie.201907171 / 459 C / 1 MPa / H2/N2 3 / SV not given | True | True | True | True | 0.2521433032419236 | 0.022638639714072317 | True | 0.5 |
| 10.1002/anie.201907171 / 459 C / 5 MPa / H2/N2 3 / SV not given | True | False | True | False | 0.0 | 0.03459351387274823 | False | -0.6000000000000001 |
| 10.1002/asia.201900618 / 400 C / 3 MPa / H2/N2 3 / 2.4e+04 mL/g/h | True | False | True | False | 0.0 | 0.020037263068883204 | False | -0.9999999999999999 |
| 10.1002/asia.201900618 / 450 C / 3 MPa / H2/N2 3 / 2.4e+04 mL/g/h | True | True | True | True | 0.011003879980802544 | 0.010503277854618798 | True | 0.39999999999999997 |
| 10.1007/s10562-019-02674-1 / 450 C / 3 MPa / H2/N2 3 / 2.4e+04 mL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1021/acs.chemmater.9b03099 / 375 C / 0.1 MPa / H2/N2 3 / 1.8e+04 mL/g/h | True | True | False | False | 0.023580082421838622 | 0.0 | False | -0.5 |
| 10.1021/acs.iecr.8b02126 / 400 C / 1 MPa / H2/N2 3 / 6e+04 mL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1021/acs.iecr.9b01610 / 400 C / 1 MPa / H2/N2 3 / 6e+04 mL/g/h | True | False | False | True | 0.0 | 0.0 | True | 1.0 |
| 10.1021/acs.jpcc.7b07268 / 340 C / 0.1 MPa / H2/N2 3 / 3.6e+04 mL/g/h | True | True | False | False | 0.05394087067900166 | 0.0 | False | -0.9999999999999999 |
| 10.1021/acscatal.1c02887 / 350 C / 1 MPa / H2/N2 3 / 7.2e+04 mL/g/h | True | False | False | True | 0.0 | 0.0 | True | 1.0 |
| 10.1021/acscatal.1c02887 / 400 C / 6 MPa / H2/N2 3 / 7.2e+04 mL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1021/acscatal.7b00284 / 300 C / 1 MPa / H2/N2 3 / 6e+04 mL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1021/acscatal.8b02839 / 340 C / 0.1 MPa / H2/N2 3 / 3.6e+04 mL/g/h | True | False | False | True | 0.0 | 0.0 | True | 1.0 |
| 10.1021/acscatal.8b03554 / 400 C / 1 MPa / H2/N2 3 / 1.8e+04 mL/g/h | True | False | False | True | 0.0 | 0.0 | True | 1.0 |
| 10.1021/acscatal.8b03554 / 400 C / 1 MPa / H2/N2 3 / 6e+04 mL/g/h | True | False | False | True | 0.0 | 0.0 | True | 1.0 |
| 10.1021/acscatal.8b03650 / 340 C / 0.1 MPa / H2/N2 3 / 1.8e+04 mL/g/h | True | False | False | True | 0.0 | 0.0 | True | 1.0 |
| 10.1021/acscatal.8b03743 / 340 C / 0.1 MPa / H2/N2 3 / 3.6e+04 mL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1021/acssuschemeng.8b04683 / 400 C / 1 MPa / H2/N2 3 / 7.2e+04 mL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1021/cs401044a / 340 C / 0.1 MPa / H2/N2 3 / 1.8e+04 mL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1021/jacs.0c06624 / 400 C / 0.9 MPa / H2/N2 3 / 3.6e+04 mL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1021/jacs.7b08891 / 400 C / 5.1 MPa / H2/N2 3 / 6.6e+04 mL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1021/jacs.9b10726 / 400 C / 0.9 MPa / H2/N2 3 / 3.6e+04 mL/g/h | True | True | False | False | 0.2873732745288964 | 0.0 | False | 0.5 |
| 10.1038/nchem.1476 / 320 C / 0.1 MPa / H2/N2 3 / 1.8e+04 mL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.4285714285714286 |
| 10.1038/nchem.1476 / 400 C / 0.1 MPa / H2/N2 3 / 1.8e+04 mL/g/h | True | False | True | False | 0.0 | 0.008110108834466612 | False | 0.8999999999999998 |
| 10.1038/nchem.1476 / 400 C / 1 MPa / H2/N2 3 / 1.8e+04 mL/g/h | True | False | True | False | 0.0 | 0.02533255787608435 | False | -0.14285714285714288 |
| 10.1038/s41467-020-15868-8 / 300 C / 0.1 MPa / H2/N2 3 / 3.6e+04 mL/g/h | True | True | True | True | 0.11814062966870109 | 0.02037805017939842 | True | 0.8928571428571429 |
| 10.1038/s41467-020-15868-8 / 340 C / 0.1 MPa / H2/N2 3 / 3.6e+04 mL/g/h | True | True | True | True | 0.28264737930732764 | 0.013809846021491934 | True | 0.9285714285714287 |
| 10.1038/s41586-020-2464-9 / 340 C / 0.1 MPa / H2/N2 3 / 3.6e+04 mL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1039/c6cy02089e / 380 C / 1 MPa / H2/N2 3 / 1.8e+04 mL/g/h | True | False | False | True | 0.0 | 0.0 | True | 1.0 |
| 10.1039/c6cy02089e / 380 C / 3 MPa / H2/N2 3 / SV not given | True | False | False | True | 0.0 | 0.0 | True | 1.0 |
| 10.1039/c6cy02089e / 400 C / 1 MPa / H2/N2 3 / 1.8e+04 mL/g/h | True | True | False | False | 0.02438687018126262 | 0.0 | False | 0.8787878787878788 |
| 10.1039/c6cy02089e / 400 C / 3 MPa / H2/N2 3 / 1.8e+04 mL/g/h | True | False | False | True | 0.0 | 0.0 | True | 1.0 |
| 10.1039/c6sc00767h / 300 C / 0.1 MPa / H2/N2 3 / 3.6e+04 mL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.6 |
| 10.1039/c6sc00767h / 340 C / 0.1 MPa / H2/N2 3 / 3.6e+04 mL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.8999999999999998 |
| 10.1039/c6sc02382g / 390 C / 0.9 MPa / H2/N2 3 / 1.8e+04 mL/g/h | True | False | False | True | 0.0 | 0.0 | True | 1.0 |
| 10.1039/c7sc05343f / 350 C / 1 MPa / H2/N2 3 / 7.2e+04 mL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.6904761904761906 |
| 10.1039/c8qi01244j / 425 C / 1 MPa / H2/N2 3 / SV not given | True | False | False | True | 0.0 | 0.0 | True | 1.0 |
| 10.1039/c9cc07385j / 400 C / 1 MPa / H2/N2 3 / 3.6e+04 mL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1039/c9ra03097b / 400 C / 10 MPa / H2/N2 3 / SV not given | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1039/d0ta05238h / 450 C / 1 MPa / H2/N2 3 / 1.6e+04 mL/g/h | True | True | False | False | 0.015008780423757972 | 0.0 | False | 0.7 |

### Bottlenecks

```json
{
  "largest_cost_item": "feed",
  "hand_largest_cost_item": "energy",
  "controlling_property": "metal",
  "hand_controlling_property": "not available",
  "attribution_share": {
    "selectivity": 0.0,
    "activity": 0.055,
    "temperature": 0.042,
    "stability": 0.001,
    "metal": 0.902
  },
  "cheapest_record": "nh3:0232",
  "cheapest_catalyst": "commercial Fe catalyst",
  "hand_cheapest_record": "nh3:0231",
  "hand_cheapest_catalyst": "commercial Fe catalyst",
  "cheapest_common_record": "nh3:0232",
  "cheapest_common_catalyst": "commercial Fe catalyst",
  "hand_cheapest_common_record": "nh3:0231",
  "hand_cheapest_common_catalyst": "commercial Fe catalyst"
}
```

### Difference diagnosis and uncertainty

```json
{
  "rules": "deterministic evidence comparison; categories are evidence, not causal proof",
  "largest_reference_gaps": [
    {
      "field": "cost_usd_per_t",
      "hand": 11.515783597179267,
      "ai": 618.8814095765105,
      "relative_gap": 52.742014544985224,
      "categories": [
        "boundary",
        "structure",
        "parameters"
      ],
      "rule": "basis mismatch -> boundary; cost/energy/capital -> unit structure and matched parameters; no automatic causal attribution"
    },
    {
      "field": "parts.catalyst",
      "hand": 0.12522336780956467,
      "ai": 6.384192454063411,
      "relative_gap": 49.98243695036432,
      "categories": [
        "structure",
        "parameters"
      ],
      "rule": "basis mismatch -> boundary; cost/energy/capital -> unit structure and matched parameters; no automatic causal attribution"
    },
    {
      "field": "parts.capital",
      "hand": 3.7915922812770635,
      "ai": 21.944207275442736,
      "relative_gap": 4.787596779274908,
      "categories": [
        "structure",
        "parameters"
      ],
      "rule": "basis mismatch -> boundary; cost/energy/capital -> unit structure and matched parameters; no automatic causal attribution"
    },
    {
      "field": "balances.energy_GJ_per_t",
      "hand": 0.54712569226267,
      "ai": 3.0364429491684017,
      "relative_gap": 4.549808740677148,
      "categories": [
        "structure",
        "parameters"
      ],
      "rule": "basis mismatch -> boundary; cost/energy/capital -> unit structure and matched parameters; no automatic causal attribution"
    },
    {
      "field": "parts.energy",
      "hand": 7.598967948092639,
      "ai": 26.990603992608015,
      "relative_gap": 2.551877594033375,
      "categories": [
        "structure",
        "parameters"
      ],
      "rule": "basis mismatch -> boundary; cost/energy/capital -> unit structure and matched parameters; no automatic causal attribution"
    },
    {
      "field": "balances.capacity_t_per_y",
      "hand": 346750.0,
      "ai": 1000000.0,
      "relative_gap": 1.883922134102379,
      "categories": [
        "structure",
        "parameters"
      ],
      "rule": "basis mismatch -> boundary; cost/energy/capital -> unit structure and matched parameters; no automatic causal attribution"
    },
    {
      "field": "basis.capacity_t_per_y",
      "hand": 346750.0,
      "ai": 1000000,
      "relative_gap": 1.883922134102379,
      "categories": [
        "boundary"
      ],
      "rule": "basis mismatch -> boundary; cost/energy/capital -> unit structure and matched parameters; no automatic causal attribution"
    },
    {
      "field": "operating.P_bar",
      "hand": 105.0,
      "ai": 250.0,
      "relative_gap": 1.380952380952381,
      "categories": [
        "structure",
        "parameters"
      ],
      "rule": "basis mismatch -> boundary; cost/energy/capital -> unit structure and matched parameters; no automatic causal attribution"
    },
    {
      "field": "operating.per_pass_conversion",
      "hand": 0.17205887115595606,
      "ai": 0.3818669251173074,
      "relative_gap": 1.2193968991646993,
      "categories": [
        "structure",
        "parameters"
      ],
      "rule": "basis mismatch -> boundary; cost/energy/capital -> unit structure and matched parameters; no automatic causal attribution"
    },
    {
      "field": "shares.energy",
      "hand": 0.6598741530670972,
      "ai": 0.043611915909830296,
      "relative_gap": -0.9339087374355822,
      "categories": [
        "structure",
        "parameters"
      ],
      "rule": "basis mismatch -> boundary; cost/energy/capital -> unit structure and matched parameters; no automatic causal attribution"
    },
    {
      "field": "shares.capital",
      "hand": 0.3292517829360561,
      "ai": 0.03545785498785424,
      "relative_gap": -0.8923077813834026,
      "categories": [
        "structure",
        "parameters"
      ],
      "rule": "basis mismatch -> boundary; cost/energy/capital -> unit structure and matched parameters; no automatic causal attribution"
    },
    {
      "field": "basis.product.NH3.P_bar",
      "hand": 105.0,
      "ai": 20.0,
      "relative_gap": -0.8095238095238095,
      "categories": [
        "boundary"
      ],
      "rule": "basis mismatch -> boundary; cost/energy/capital -> unit structure and matched parameters; no automatic causal attribution"
    }
  ],
  "largest_ranking_gaps": {
    "printed": [
      {
        "group": "10.1021/jacs.9b10726 | 400 C | 0.9 MPa | H2/N2 3 | 3.6e+04 mL/g/h",
        "hand_leader": "Fe(1.2 wt %)/BaCeO3−xNyHz",
        "ai_leader": "Co(4.7 wt %)/BaCeO3−xNyHz",
        "hand_gap": 0.2873732745288964,
        "ai_gap": 0.0,
        "categories": [
          "structure",
          "parameters",
          "data",
          "boundary"
        ]
      },
      {
        "group": "10.1002/anie.201712398 | 300 C | 0.9 MPa | H2/N2 3 | 3.6e+04 mL/g/h",
        "hand_leader": "Industrial Fe catalyst",
        "ai_leader": "Co(8%)/Ba-Ca(NH2)2",
        "hand_gap": 0.22051247667258944,
        "ai_gap": 0.04495978991689187,
        "categories": [
          "structure",
          "parameters",
          "data",
          "boundary"
        ]
      },
      {
        "group": "10.1021/acs.jpcc.7b07268 | 340 C | 0.1 MPa | H2/N2 3 | 3.6e+04 mL/g/h",
        "hand_leader": "Ru/CaNH",
        "ai_leader": "Ru/Ca2NH",
        "hand_gap": 0.05394087067900166,
        "ai_gap": 0.0,
        "categories": [
          "structure",
          "parameters",
          "data",
          "boundary"
        ]
      },
      {
        "group": "10.1002/anie.201907171 | 459 C | 5 MPa | H2/N2 3 | SV not given",
        "hand_leader": "Ru-Li/MgO",
        "ai_leader": "Ba-Fe/AC",
        "hand_gap": 0.0,
        "ai_gap": 0.03459351387274823,
        "categories": [
          "structure",
          "parameters",
          "data",
          "boundary"
        ]
      },
      {
        "group": "10.1038/nchem.1476 | 400 C | 1 MPa | H2/N2 3 | 1.8e+04 mL/g/h",
        "hand_leader": "Ru-Cs/MgO",
        "ai_leader": "Ru/C12A7:e−",
        "hand_gap": 0.0,
        "ai_gap": 0.02533255787608435,
        "categories": [
          "structure",
          "parameters",
          "data",
          "boundary"
        ]
      },
      {
        "group": "10.1039/c6cy02089e | 400 C | 1 MPa | H2/N2 3 | 1.8e+04 mL/g/h",
        "hand_leader": "2K–Ru/r-CeO2",
        "ai_leader": "2Cs–Ru/r-CeO2",
        "hand_gap": 0.02438687018126262,
        "ai_gap": 0.0,
        "categories": [
          "structure",
          "parameters",
          "data",
          "boundary"
        ]
      },
      {
        "group": "10.1021/acs.chemmater.9b03099 | 375 C | 0.1 MPa | H2/N2 3 | 1.8e+04 mL/g/h",
        "hand_leader": "Ru SAs/S-1",
        "ai_leader": "Ba-Ru SAs/S-1",
        "hand_gap": 0.023580082421838622,
        "ai_gap": 0.0,
        "categories": [
          "structure",
          "parameters",
          "data",
          "boundary"
        ]
      },
      {
        "group": "10.1002/asia.201900618 | 400 C | 3 MPa | H2/N2 3 | 2.4e+04 mL/g/h",
        "hand_leader": "3.5% Ru/BaCeO3-a",
        "ai_leader": "4% Cs-1.25%Ru/BaCeO3-a",
        "hand_gap": 0.0,
        "ai_gap": 0.020037263068883204,
        "categories": [
          "structure",
          "parameters",
          "data",
          "boundary"
        ]
      },
      {
        "group": "10.1039/d0ta05238h | 450 C | 1 MPa | H2/N2 3 | 1.6e+04 mL/g/h",
        "hand_leader": "Magnetite based industrial Fe catalyst",
        "ai_leader": "80% Fe–20% Ce0.8Sm0.2O2−δ",
        "hand_gap": 0.015008780423757972,
        "ai_gap": 0.0,
        "categories": [
          "structure",
          "parameters",
          "data",
          "boundary"
        ]
      },
      {
        "group": "10.1038/nchem.1476 | 400 C | 0.1 MPa | H2/N2 3 | 1.8e+04 mL/g/h",
        "hand_leader": "Ru-Ba/AC",
        "ai_leader": "Ru/C12A7:e−",
        "hand_gap": 0.0,
        "ai_gap": 0.008110108834466612,
        "categories": [
          "structure",
          "parameters",
          "data",
          "boundary"
        ]
      }
    ]
  },
  "ranking_disagreements": {
    "printed": 9
  },
  "findings": [
    {
      "category": "boundary",
      "evidence": "hand NH3 excludes purchased feeds; AI has positive feed cost",
      "impact": "total costs have different boundaries"
    },
    {
      "category": "boundary",
      "evidence": {
        "field": "feeds.N2.purity_mol_frac",
        "hand": 1,
        "ai": 0.999
      },
      "impact": "different plant design basis"
    },
    {
      "category": "boundary",
      "evidence": {
        "field": "product.NH3.P_bar",
        "hand": 105.0,
        "ai": 20.0
      },
      "impact": "different plant design basis"
    },
    {
      "category": "boundary",
      "evidence": {
        "field": "battery_limit",
        "hand": "Reduced catalyst-dependent NH3 cost. NH3-FINAL-1.1 adds the pressure-attributable converter-shell cost and the compressor bare-module CAPEX; loop heat exchangers, separator vessel and piping remain outside the boundary (declared omission; direction: further penalizes high pressure). Purchased feed costs excluded.",
        "ai": "Purchased purified H2 and N2 at the synthesis-plant gate through pressurization, stoichiometric mixing, heat recovery/preheat, catalytic synthesis, cooling/condensation, gas recycle and purge, liquid-ammonia product handling, and synthesis-loop utilities/offsites; upstream H2 and N2 manufacture and downstream ammonia distribution are excluded."
      },
      "impact": "different plant design basis"
    },
    {
      "category": "boundary",
      "evidence": {
        "field": "operating_hours_per_y",
        "hand": 8322.0,
        "ai": 8000
      },
      "impact": "different plant design basis"
    },
    {
      "category": "boundary",
      "evidence": {
        "field": "feeds.H2.purity_mol_frac",
        "hand": 1,
        "ai": 0.999
      },
      "impact": "different plant design basis"
    },
    {
      "category": "boundary",
      "evidence": {
        "field": "capacity_t_per_y",
        "hand": 346750.0,
        "ai": 1000000
      },
      "impact": "different plant design basis"
    },
    {
      "category": "structure",
      "evidence": {
        "hand_units": [
          "reactor",
          "fresh compression",
          "recycle compression",
          "refrigeration",
          "compressor capex"
        ],
        "ai_units": [
          {
            "name": "hydrogen_feed_compressor",
            "type": "compressor"
          },
          {
            "name": "nitrogen_feed_compressor",
            "type": "compressor"
          },
          {
            "name": "synthesis_gas_mixer",
            "type": "other"
          },
          {
            "name": "feed_effluent_exchanger",
            "type": "heat_exchanger"
          },
          {
            "name": "ammonia_converter",
            "type": "reactor"
          },
          {
            "name": "waste_heat_boiler",
            "type": "heat_exchanger"
          },
          {
            "name": "final_product_cooler",
            "type": "heat_exchanger"
          },
          {
            "name": "ammonia_knockout",
            "type": "knockout"
          },
          {
            "name": "purge_splitter",
            "type": "other"
          },
          {
            "name": "recycle_compressor",
            "type": "compressor"
          },
          {
            "name": "product_and_offsites",
            "type": "offsites"
          }
        ],
        "ai_checklist": {
          "feed_preparation": {
            "included": [
              "hydrogen_feed_compressor",
              "nitrogen_feed_compressor",
              "synthesis_gas_mixer",
              "feed_effluent_exchanger"
            ]
          },
          "reactor_heat_supply_or_removal": {
            "included": [
              "ammonia_converter",
              "waste_heat_boiler"
            ]
          },
          "catalyst_regeneration": {
            "excluded": "Ammonia-synthesis catalysts are replaced during planned turnarounds; no continuous in-situ regeneration unit is justified inside this battery limit."
          },
          "product_compression": {
            "excluded": "Condensed ammonia leaves at adequate pressure and is let down to the specified 20 bar product state, so no product compressor is required."
          },
          "separation_and_purification": {
            "included": [
              "final_product_cooler",
              "ammonia_knockout",
              "purge_splitter"
            ]
          },
          "recycle": {
            "included": [
              "purge_splitter",
              "recycle_compressor",
              "synthesis_gas_mixer"
            ]
          },
          "heat_recovery": {
            "included": [
              "waste_heat_boiler",
              "feed_effluent_exchanger"
            ]
          },
          "utilities_and_offsites": {
            "included": [
              "product_and_offsites"
            ]
          }
        },
        "missing_hand_unit_types": [],
        "extra_ai_unit_types": [
          "heat_exchanger",
          "knockout",
          "offsites",
          "other"
        ],
        "ai_recycle_declaration": {
          "included": [
            "purge_splitter",
            "recycle_compressor",
            "synthesis_gas_mixer"
          ]
        },
        "hand_kinetics": "NH3 descriptor microkinetics and 0.8 equilibrium approach"
      },
      "impact": "unit types are a screening comparison, not proof of causal impact; NH3 separator vessel is outside the reduced CAPEX boundary; checklist exclusions retained verbatim"
    },
    {
      "category": "parameters",
      "evidence": {
        "gaps_gt20pct": [],
        "unmatched_hand_parameters": [
          "calibration_factor",
          "catalyst_life_y",
          "compressor_efficiency",
          "discount_rate",
          "electricity_USD_MWh",
          "metal_recovery_fraction",
          "plant_life_y",
          "reactor_exponent",
          "reactor_fixed_USD",
          "reactor_reference_m3",
          "reactor_variable_USD"
        ],
        "hand_parameters": {
          "discount_rate": 0.12,
          "plant_life_y": 25,
          "electricity_USD_MWh": 50.0,
          "compressor_efficiency": 0.75,
          "catalyst_life_y": 10.0,
          "metal_recovery_fraction": 0.0,
          "reactor_fixed_USD": 66800.0,
          "reactor_variable_USD": 268000.0,
          "reactor_reference_m3": 20.0,
          "reactor_exponent": 0.52,
          "calibration_factor": 74351.60773111923
        },
        "ai_parameters": {
          "basis.capacity_t_per_y": 1000000.0,
          "basis.operating_hours_per_y": 8000.0,
          "basis.feeds.H2.T_K": 298.15,
          "basis.feeds.H2.P_bar": 30.0,
          "basis.feeds.H2.purity_mol_frac": 0.999,
          "basis.feeds.N2.T_K": 298.15,
          "basis.feeds.N2.P_bar": 30.0,
          "basis.feeds.N2.purity_mol_frac": 0.999,
          "basis.product.NH3.P_bar": 20.0,
          "basis.product.NH3.purity_mol_frac": 0.995,
          "basis.utilities.cooling_water_supply_temperature": 298.15,
          "basis.utilities.cooling_water_return_temperature": 308.15,
          "basis.utilities.electric_motor_efficiency": 0.95,
          "kinetic.activation_energy_J_per_mol": 100000.0,
          "kinetic.pressure_order_total": 1.0,
          "kinetic.max_rate_scale": 1000.0,
          "operation.loop_pressure_min_bar": 80.0,
          "operation.loop_pressure_max_bar": 250.0,
          "operation.pressure_grid_points": 8.0,
          "operation.conversion_grid_points": 32.0,
          "operation.min_conversion": 0.02,
          "operation.equilibrium_fraction_limit": 0.95,
          "operation.purge_fraction": 0.02,
          "operation.nh3_condensation_recovery": 0.995,
          "compressor.isentropic_efficiency": 0.75,
          "compressor.gamma_h2": 1.4,
          "compressor.gamma_n2": 1.4,
          "compressor.gamma_loop": 1.35,
          "compressor.recycle_pressure_ratio": 1.05,
          "energy.electricity_primary_factor": 2.5,
          "heat.reaction_enthalpy_J_per_mol_NH3": -46110.0,
          "heat.feed_effluent_recovery_fraction": 0.75,
          "heat.waste_heat_recovery_fraction": 0.7,
          "heat.cooling_electricity_GJ_per_GJ_removed": 0.015,
          "heat.sensible_cooling_GJ_per_t": 0.35,
          "catalyst.default_cycle_h": 24000.0,
          "catalyst.activity_loss_fraction_at_cycle": 0.1,
          "catalyst.reference_inventory_kg": 2000000.0,
          "catalyst.reference_rate_kg_per_kg_h": 0.12,
          "capital.scale_exponent": 0.65,
          "capital.pressure_exponent": 0.25,
          "capital.reference_capacity_t_per_y": 1000000.0,
          "capital.reference_pressure_bar": 150.0,
          "capital.hydrogen_feed_compressor_usd": 25000000.0,
          "capital.nitrogen_feed_compressor_usd": 18000000.0,
          "capital.synthesis_gas_mixer_usd": 1000000.0,
          "capital.feed_effluent_exchanger_usd": 12000000.0,
          "capital.ammonia_converter_usd": 45000000.0,
          "capital.waste_heat_boiler_usd": 18000000.0,
          "capital.final_product_cooler_usd": 15000000.0,
          "capital.ammonia_knockout_usd": 6000000.0,
          "capital.purge_splitter_usd": 500000.0,
          "capital.recycle_compressor_usd": 7500000.0,
          "capital.product_and_offsites_usd": 38000000.0,
          "capital.reactor_activity_scale_exponent": 0.6,
          "capital.reactor_min_scale": 0.35,
          "capital.offsites_capacity_exponent": 0.6,
          "operation.reference_T_K": 700.0,
          "operation.reference_P_bar": 150.0,
          "operation.reference_X": 0.15,
          "operation.reference_selectivity": 1.0,
          "operation.reference_y_N2": 0.25,
          "operation.reference_y_H2": 0.75,
          "price.natural_gas": 2.5,
          "price.electricity": 80.0,
          "price.hydrogen": 3.0,
          "price.carbon_dioxide": 100.0,
          "price.propane": 408.0,
          "price.ammonia": 445.0,
          "price.ethanol": 716.1,
          "price.catalyst_support_and_manufacturing": 20.0,
          "price.metal_Ru": 53852.5,
          "price.metal_Os": 142650.0,
          "price.metal_Fe": 8.0,
          "price.metal_Rh": 265243.65919095,
          "price.metal_Ir": 252383.36056351,
          "price.metal_Co": 56.28401553583051,
          "price.metal_Re": 5757.64,
          "price.metal_Mo": 91.22728409215301,
          "price.metal_Ni": 16.9094555095895,
          "price.metal_W": 149.97,
          "price.metal_Pd": 40670.694409279,
          "price.metal_Pt": 51508.71107755406,
          "price.metal_Cu": 13.889122517655,
          "price.metal_Ag": 1823.590345370992,
          "price.metal_Au": 128732.2322756058,
          "price.metal_Al": 3.9683,
          "price.metal_Bi": 44.092,
          "price.metal_Cd": 3.9,
          "price.metal_Cr": 13.007,
          "price.metal_Ga": 580.0,
          "price.metal_Hf": 3800.0,
          "price.metal_Hg": 50.0,
          "price.metal_In": 370.0,
          "price.metal_La": 1.1728,
          "price.metal_Mn": 0.45,
          "price.metal_Nb": 40.0,
          "price.metal_Pb": 2.3369,
          "price.metal_Sc": 5200.0,
          "price.metal_Sn": 35.274,
          "price.metal_Ta": 219.78,
          "price.metal_Ti": 12.0,
          "price.metal_Tl": 9300.0,
          "price.metal_V": 19.756,
          "price.metal_Y": 40.0,
          "price.metal_Zn": 3.2849,
          "price.metal_Zr": 22.0,
          "price.metal_Ce": 2.1005306603773586,
          "price.metal_Si": 2.866006,
          "price.metal_Mg": 2.5,
          "price.metal_Ca": 0.3637940925436203,
          "price.metal_K": 1.4455393066229791,
          "price.metal_Ba": 0.3569000679809653,
          "price.metal_B": 1.0,
          "price.capital_recovery_factor": 0.0944,
          "price.fixed_om_fraction_of_capex": 0.04,
          "feed.nitrogen_embodied_electricity_kWh_per_kg": 0.2,
          "heat.reaction_entropy_J_per_mol_reaction_K": -210.1,
          "heat.delta_cp_J_per_mol_NH3_K": -16.0
        },
        "price_table_rows": [
          {
            "parameter": "price.natural_gas",
            "value": "2.5",
            "unit": "USD/GJ",
            "source": "prices.json:natural_gas",
            "location": "PetroLogistics Catofin plant gas cost 2.60 USD/MMBtu (SEC 424B4, 2012); Henry Hub 2024 average 2.19 USD/MMBtu (EIA)",
            "type": "price_table",
            "low": "2.0",
            "high": "12.0"
          },
          {
            "parameter": "price.electricity",
            "value": "80.0",
            "unit": "USD/MWh",
            "source": "prices.json:electricity",
            "location": "industrial power assumption used across the NCE chains; EIA 2024 US industrial average about 80 USD/MWh",
            "type": "price_table",
            "low": "40.0",
            "high": "150.0"
          },
          {
            "parameter": "price.hydrogen",
            "value": "3.0",
            "unit": "USD/kg",
            "source": "prices.json:hydrogen",
            "location": "Becker, Penev & Braun, J. Energy Resour. Technol. 2019 anchor 3 USD/kg; grey about 2, electrolytic 5-7 (DOE Pathways to Commercial Liftoff: Clean Hydrogen, 2024)",
            "type": "price_table",
            "low": "1.5",
            "high": "7.0"
          },
          {
            "parameter": "price.carbon_dioxide",
            "value": "100.0",
            "unit": "USD/t",
            "source": "prices.json:carbon_dioxide",
            "location": "104 USD/t CO2 captured, Enterprise Products EPA GHG permit application 2012, rounded",
            "type": "price_table",
            "low": "20.0",
            "high": "200.0"
          },
          {
            "parameter": "price.propane",
            "value": "408.0",
            "unit": "USD/t",
            "source": "prices.json:propane",
            "location": "EIA Mont Belvieu propane spot 2024, 0.778 USD/gal at 4.2 lb/gal",
            "type": "price_table",
            "low": "300.0",
            "high": "700.0"
          },
          {
            "parameter": "price.ammonia",
            "value": "445.0",
            "unit": "USD/t",
            "source": "prices.json:ammonia",
            "location": "Tampa CFR ammonia, March 2024 contract settlement (trade press summary)",
            "type": "price_table",
            "low": "300.0",
            "high": "900.0"
          },
          {
            "parameter": "price.ethanol",
            "value": "716.1",
            "unit": "USD/t",
            "source": "prices.json:ethanol",
            "location": "Haro et al. 2013, Table 9 (Brazilian hydrated ethanol)",
            "type": "price_table",
            "low": "500.0",
            "high": "1000.0"
          },
          {
            "parameter": "price.catalyst_support_and_manufacturing",
            "value": "20.0",
            "unit": "USD/kg",
            "source": "prices.json:catalyst_support_and_manufacturing",
            "location": "NCE chain assumption for support plus manufacturing per kg of finished catalyst, excluding active metals",
            "type": "price_table",
            "low": "5.0",
            "high": "100.0"
          },
          {
            "parameter": "price.metal_Ru",
            "value": "53852.5",
            "unit": "USD/kg",
            "source": "prices.json:metal_Ru",
            "location": "frozen NH3 harness prices (Ru, Os, Fe, Rh, Ir, Co, Re, Mo, Ni, W, Pd, Pt, Cu, Ag, Au) + USGS Mineral Commodity Summaries 2026 per kg contained element; see analysis/meoh_catalyst_cost_2026_10_06/catalyst_prices.py (per kg contained element)",
            "type": "price_table",
            "low": "26926.25",
            "high": "107705.0"
          },
          {
            "parameter": "price.metal_Os",
            "value": "142650.0",
            "unit": "USD/kg",
            "source": "prices.json:metal_Os",
            "location": "frozen NH3 harness prices (Ru, Os, Fe, Rh, Ir, Co, Re, Mo, Ni, W, Pd, Pt, Cu, Ag, Au) + USGS Mineral Commodity Summaries 2026 per kg contained element; see analysis/meoh_catalyst_cost_2026_10_06/catalyst_prices.py (per kg contained element)",
            "type": "price_table",
            "low": "71325.0",
            "high": "285300.0"
          },
          {
            "parameter": "price.metal_Fe",
            "value": "8.0",
            "unit": "USD/kg",
            "source": "prices.json:metal_Fe",
            "location": "frozen NH3 harness prices (Ru, Os, Fe, Rh, Ir, Co, Re, Mo, Ni, W, Pd, Pt, Cu, Ag, Au) + USGS Mineral Commodity Summaries 2026 per kg contained element; see analysis/meoh_catalyst_cost_2026_10_06/catalyst_prices.py (per kg contained element)",
            "type": "price_table",
            "low": "4.0",
            "high": "16.0"
          },
          {
            "parameter": "price.metal_Rh",
            "value": "265243.65919095",
            "unit": "USD/kg",
            "source": "prices.json:metal_Rh",
            "location": "frozen NH3 harness prices (Ru, Os, Fe, Rh, Ir, Co, Re, Mo, Ni, W, Pd, Pt, Cu, Ag, Au) + USGS Mineral Commodity Summaries 2026 per kg contained element; see analysis/meoh_catalyst_cost_2026_10_06/catalyst_prices.py (per kg contained element)",
            "type": "price_table",
            "low": "132621.829595475",
            "high": "530487.3183819"
          },
          {
            "parameter": "price.metal_Ir",
            "value": "252383.36056351",
            "unit": "USD/kg",
            "source": "prices.json:metal_Ir",
            "location": "frozen NH3 harness prices (Ru, Os, Fe, Rh, Ir, Co, Re, Mo, Ni, W, Pd, Pt, Cu, Ag, Au) + USGS Mineral Commodity Summaries 2026 per kg contained element; see analysis/meoh_catalyst_cost_2026_10_06/catalyst_prices.py (per kg contained element)",
            "type": "price_table",
            "low": "126191.680281755",
            "high": "504766.72112702"
          },
          {
            "parameter": "price.metal_Co",
            "value": "56.28401553583051",
            "unit": "USD/kg",
            "source": "prices.json:metal_Co",
            "location": "frozen NH3 harness prices (Ru, Os, Fe, Rh, Ir, Co, Re, Mo, Ni, W, Pd, Pt, Cu, Ag, Au) + USGS Mineral Commodity Summaries 2026 per kg contained element; see analysis/meoh_catalyst_cost_2026_10_06/catalyst_prices.py (per kg contained element)",
            "type": "price_table",
            "low": "28.142007767915256",
            "high": "112.56803107166103"
          },
          {
            "parameter": "price.metal_Re",
            "value": "5757.64",
            "unit": "USD/kg",
            "source": "prices.json:metal_Re",
            "location": "frozen NH3 harness prices (Ru, Os, Fe, Rh, Ir, Co, Re, Mo, Ni, W, Pd, Pt, Cu, Ag, Au) + USGS Mineral Commodity Summaries 2026 per kg contained element; see analysis/meoh_catalyst_cost_2026_10_06/catalyst_prices.py (per kg contained element)",
            "type": "price_table",
            "low": "2878.82",
            "high": "11515.28"
          },
          {
            "parameter": "price.metal_Mo",
            "value": "91.22728409215301",
            "unit": "USD/kg",
            "source": "prices.json:metal_Mo",
            "location": "frozen NH3 harness prices (Ru, Os, Fe, Rh, Ir, Co, Re, Mo, Ni, W, Pd, Pt, Cu, Ag, Au) + USGS Mineral Commodity Summaries 2026 per kg contained element; see analysis/meoh_catalyst_cost_2026_10_06/catalyst_prices.py (per kg contained element)",
            "type": "price_table",
            "low": "45.61364204607651",
            "high": "182.45456818430603"
          },
          {
            "parameter": "price.metal_Ni",
            "value": "16.9094555095895",
            "unit": "USD/kg",
            "source": "prices.json:metal_Ni",
            "location": "frozen NH3 harness prices (Ru, Os, Fe, Rh, Ir, Co, Re, Mo, Ni, W, Pd, Pt, Cu, Ag, Au) + USGS Mineral Commodity Summaries 2026 per kg contained element; see analysis/meoh_catalyst_cost_2026_10_06/catalyst_prices.py (per kg contained element)",
            "type": "price_table",
            "low": "8.45472775479475",
            "high": "33.818911019179"
          },
          {
            "parameter": "price.metal_W",
            "value": "149.97",
            "unit": "USD/kg",
            "source": "prices.json:metal_W",
            "location": "frozen NH3 harness prices (Ru, Os, Fe, Rh, Ir, Co, Re, Mo, Ni, W, Pd, Pt, Cu, Ag, Au) + USGS Mineral Commodity Summaries 2026 per kg contained element; see analysis/meoh_catalyst_cost_2026_10_06/catalyst_prices.py (per kg contained element)",
            "type": "price_table",
            "low": "74.985",
            "high": "299.94"
          },
          {
            "parameter": "price.metal_Pd",
            "value": "40670.694409279",
            "unit": "USD/kg",
            "source": "prices.json:metal_Pd",
            "location": "frozen NH3 harness prices (Ru, Os, Fe, Rh, Ir, Co, Re, Mo, Ni, W, Pd, Pt, Cu, Ag, Au) + USGS Mineral Commodity Summaries 2026 per kg contained element; see analysis/meoh_catalyst_cost_2026_10_06/catalyst_prices.py (per kg contained element)",
            "type": "price_table",
            "low": "20335.3472046395",
            "high": "81341.388818558"
          },
          {
            "parameter": "price.metal_Pt",
            "value": "51508.71107755406",
            "unit": "USD/kg",
            "source": "prices.json:metal_Pt",
            "location": "frozen NH3 harness prices (Ru, Os, Fe, Rh, Ir, Co, Re, Mo, Ni, W, Pd, Pt, Cu, Ag, Au) + USGS Mineral Commodity Summaries 2026 per kg contained element; see analysis/meoh_catalyst_cost_2026_10_06/catalyst_prices.py (per kg contained element)",
            "type": "price_table",
            "low": "25754.35553877703",
            "high": "103017.42215510811"
          },
          {
            "parameter": "price.metal_Cu",
            "value": "13.889122517655",
            "unit": "USD/kg",
            "source": "prices.json:metal_Cu",
            "location": "frozen NH3 harness prices (Ru, Os, Fe, Rh, Ir, Co, Re, Mo, Ni, W, Pd, Pt, Cu, Ag, Au) + USGS Mineral Commodity Summaries 2026 per kg contained element; see analysis/meoh_catalyst_cost_2026_10_06/catalyst_prices.py (per kg contained element)",
            "type": "price_table",
            "low": "6.9445612588275",
            "high": "27.77824503531"
          },
          {
            "parameter": "price.metal_Ag",
            "value": "1823.590345370992",
            "unit": "USD/kg",
            "source": "prices.json:metal_Ag",
            "location": "frozen NH3 harness prices (Ru, Os, Fe, Rh, Ir, Co, Re, Mo, Ni, W, Pd, Pt, Cu, Ag, Au) + USGS Mineral Commodity Summaries 2026 per kg contained element; see analysis/meoh_catalyst_cost_2026_10_06/catalyst_prices.py (per kg contained element)",
            "type": "price_table",
            "low": "911.795172685496",
            "high": "3647.180690741984"
          },
          {
            "parameter": "price.metal_Au",
            "value": "128732.2322756058",
            "unit": "USD/kg",
            "source": "prices.json:metal_Au",
            "location": "frozen NH3 harness prices (Ru, Os, Fe, Rh, Ir, Co, Re, Mo, Ni, W, Pd, Pt, Cu, Ag, Au) + USGS Mineral Commodity Summaries 2026 per kg contained element; see analysis/meoh_catalyst_cost_2026_10_06/catalyst_prices.py (per kg contained element)",
            "type": "price_table",
            "low": "64366.1161378029",
            "high": "257464.4645512116"
          },
          {
            "parameter": "price.metal_Al",
            "value": "3.9683",
            "unit": "USD/kg",
            "source": "prices.json:metal_Al",
            "location": "frozen NH3 harness prices (Ru, Os, Fe, Rh, Ir, Co, Re, Mo, Ni, W, Pd, Pt, Cu, Ag, Au) + USGS Mineral Commodity Summaries 2026 per kg contained element; see analysis/meoh_catalyst_cost_2026_10_06/catalyst_prices.py (per kg contained element)",
            "type": "price_table",
            "low": "1.98415",
            "high": "7.9366"
          },
          {
            "parameter": "price.metal_Bi",
            "value": "44.092",
            "unit": "USD/kg",
            "source": "prices.json:metal_Bi",
            "location": "frozen NH3 harness prices (Ru, Os, Fe, Rh, Ir, Co, Re, Mo, Ni, W, Pd, Pt, Cu, Ag, Au) + USGS Mineral Commodity Summaries 2026 per kg contained element; see analysis/meoh_catalyst_cost_2026_10_06/catalyst_prices.py (per kg contained element)",
            "type": "price_table",
            "low": "22.046",
            "high": "88.184"
          },
          {
            "parameter": "price.metal_Cd",
            "value": "3.9",
            "unit": "USD/kg",
            "source": "prices.json:metal_Cd",
            "location": "frozen NH3 harness prices (Ru, Os, Fe, Rh, Ir, Co, Re, Mo, Ni, W, Pd, Pt, Cu, Ag, Au) + USGS Mineral Commodity Summaries 2026 per kg contained element; see analysis/meoh_catalyst_cost_2026_10_06/catalyst_prices.py (per kg contained element)",
            "type": "price_table",
            "low": "1.95",
            "high": "7.8"
          },
          {
            "parameter": "price.metal_Cr",
            "value": "13.007",
            "unit": "USD/kg",
            "source": "prices.json:metal_Cr",
            "location": "frozen NH3 harness prices (Ru, Os, Fe, Rh, Ir, Co, Re, Mo, Ni, W, Pd, Pt, Cu, Ag, Au) + USGS Mineral Commodity Summaries 2026 per kg contained element; see analysis/meoh_catalyst_cost_2026_10_06/catalyst_prices.py (per kg contained element)",
            "type": "price_table",
            "low": "6.5035",
            "high": "26.014"
          },
          {
            "parameter": "price.metal_Ga",
            "value": "580.0",
            "unit": "USD/kg",
            "source": "prices.json:metal_Ga",
            "location": "frozen NH3 harness prices (Ru, Os, Fe, Rh, Ir, Co, Re, Mo, Ni, W, Pd, Pt, Cu, Ag, Au) + USGS Mineral Commodity Summaries 2026 per kg contained element; see analysis/meoh_catalyst_cost_2026_10_06/catalyst_prices.py (per kg contained element)",
            "type": "price_table",
            "low": "290.0",
            "high": "1160.0"
          },
          {
            "parameter": "price.metal_Hf",
            "value": "3800.0",
            "unit": "USD/kg",
            "source": "prices.json:metal_Hf",
            "location": "frozen NH3 harness prices (Ru, Os, Fe, Rh, Ir, Co, Re, Mo, Ni, W, Pd, Pt, Cu, Ag, Au) + USGS Mineral Commodity Summaries 2026 per kg contained element; see analysis/meoh_catalyst_cost_2026_10_06/catalyst_prices.py (per kg contained element)",
            "type": "price_table",
            "low": "1900.0",
            "high": "7600.0"
          },
          {
            "parameter": "price.metal_Hg",
            "value": "50.0",
            "unit": "USD/kg",
            "source": "prices.json:metal_Hg",
            "location": "frozen NH3 harness prices (Ru, Os, Fe, Rh, Ir, Co, Re, Mo, Ni, W, Pd, Pt, Cu, Ag, Au) + USGS Mineral Commodity Summaries 2026 per kg contained element; see analysis/meoh_catalyst_cost_2026_10_06/catalyst_prices.py (per kg contained element)",
            "type": "price_table",
            "low": "25.0",
            "high": "100.0"
          },
          {
            "parameter": "price.metal_In",
            "value": "370.0",
            "unit": "USD/kg",
            "source": "prices.json:metal_In",
            "location": "frozen NH3 harness prices (Ru, Os, Fe, Rh, Ir, Co, Re, Mo, Ni, W, Pd, Pt, Cu, Ag, Au) + USGS Mineral Commodity Summaries 2026 per kg contained element; see analysis/meoh_catalyst_cost_2026_10_06/catalyst_prices.py (per kg contained element)",
            "type": "price_table",
            "low": "185.0",
            "high": "740.0"
          },
          {
            "parameter": "price.metal_La",
            "value": "1.1728",
            "unit": "USD/kg",
            "source": "prices.json:metal_La",
            "location": "frozen NH3 harness prices (Ru, Os, Fe, Rh, Ir, Co, Re, Mo, Ni, W, Pd, Pt, Cu, Ag, Au) + USGS Mineral Commodity Summaries 2026 per kg contained element; see analysis/meoh_catalyst_cost_2026_10_06/catalyst_prices.py (per kg contained element)",
            "type": "price_table",
            "low": "0.5864",
            "high": "2.3456"
          },
          {
            "parameter": "price.metal_Mn",
            "value": "0.45",
            "unit": "USD/kg",
            "source": "prices.json:metal_Mn",
            "location": "frozen NH3 harness prices (Ru, Os, Fe, Rh, Ir, Co, Re, Mo, Ni, W, Pd, Pt, Cu, Ag, Au) + USGS Mineral Commodity Summaries 2026 per kg contained element; see analysis/meoh_catalyst_cost_2026_10_06/catalyst_prices.py (per kg contained element)",
            "type": "price_table",
            "low": "0.225",
            "high": "0.9"
          },
          {
            "parameter": "price.metal_Nb",
            "value": "40.0",
            "unit": "USD/kg",
            "source": "prices.json:metal_Nb",
            "location": "frozen NH3 harness prices (Ru, Os, Fe, Rh, Ir, Co, Re, Mo, Ni, W, Pd, Pt, Cu, Ag, Au) + USGS Mineral Commodity Summaries 2026 per kg contained element; see analysis/meoh_catalyst_cost_2026_10_06/catalyst_prices.py (per kg contained element)",
            "type": "price_table",
            "low": "20.0",
            "high": "80.0"
          },
          {
            "parameter": "price.metal_Pb",
            "value": "2.3369",
            "unit": "USD/kg",
            "source": "prices.json:metal_Pb",
            "location": "frozen NH3 harness prices (Ru, Os, Fe, Rh, Ir, Co, Re, Mo, Ni, W, Pd, Pt, Cu, Ag, Au) + USGS Mineral Commodity Summaries 2026 per kg contained element; see analysis/meoh_catalyst_cost_2026_10_06/catalyst_prices.py (per kg contained element)",
            "type": "price_table",
            "low": "1.16845",
            "high": "4.6738"
          },
          {
            "parameter": "price.metal_Sc",
            "value": "5200.0",
            "unit": "USD/kg",
            "source": "prices.json:metal_Sc",
            "location": "frozen NH3 harness prices (Ru, Os, Fe, Rh, Ir, Co, Re, Mo, Ni, W, Pd, Pt, Cu, Ag, Au) + USGS Mineral Commodity Summaries 2026 per kg contained element; see analysis/meoh_catalyst_cost_2026_10_06/catalyst_prices.py (per kg contained element)",
            "type": "price_table",
            "low": "2600.0",
            "high": "10400.0"
          },
          {
            "parameter": "price.metal_Sn",
            "value": "35.274",
            "unit": "USD/kg",
            "source": "prices.json:metal_Sn",
            "location": "frozen NH3 harness prices (Ru, Os, Fe, Rh, Ir, Co, Re, Mo, Ni, W, Pd, Pt, Cu, Ag, Au) + USGS Mineral Commodity Summaries 2026 per kg contained element; see analysis/meoh_catalyst_cost_2026_10_06/catalyst_prices.py (per kg contained element)",
            "type": "price_table",
            "low": "17.637",
            "high": "70.548"
          },
          {
            "parameter": "price.metal_Ta",
            "value": "219.78",
            "unit": "USD/kg",
            "source": "prices.json:metal_Ta",
            "location": "frozen NH3 harness prices (Ru, Os, Fe, Rh, Ir, Co, Re, Mo, Ni, W, Pd, Pt, Cu, Ag, Au) + USGS Mineral Commodity Summaries 2026 per kg contained element; see analysis/meoh_catalyst_cost_2026_10_06/catalyst_prices.py (per kg contained element)",
            "type": "price_table",
            "low": "109.89",
            "high": "439.56"
          },
          {
            "parameter": "price.metal_Ti",
            "value": "12.0",
            "unit": "USD/kg",
            "source": "prices.json:metal_Ti",
            "location": "frozen NH3 harness prices (Ru, Os, Fe, Rh, Ir, Co, Re, Mo, Ni, W, Pd, Pt, Cu, Ag, Au) + USGS Mineral Commodity Summaries 2026 per kg contained element; see analysis/meoh_catalyst_cost_2026_10_06/catalyst_prices.py (per kg contained element)",
            "type": "price_table",
            "low": "6.0",
            "high": "24.0"
          },
          {
            "parameter": "price.metal_Tl",
            "value": "9300.0",
            "unit": "USD/kg",
            "source": "prices.json:metal_Tl",
            "location": "frozen NH3 harness prices (Ru, Os, Fe, Rh, Ir, Co, Re, Mo, Ni, W, Pd, Pt, Cu, Ag, Au) + USGS Mineral Commodity Summaries 2026 per kg contained element; see analysis/meoh_catalyst_cost_2026_10_06/catalyst_prices.py (per kg contained element)",
            "type": "price_table",
            "low": "4650.0",
            "high": "18600.0"
          },
          {
            "parameter": "price.metal_V",
            "value": "19.756",
            "unit": "USD/kg",
            "source": "prices.json:metal_V",
            "location": "frozen NH3 harness prices (Ru, Os, Fe, Rh, Ir, Co, Re, Mo, Ni, W, Pd, Pt, Cu, Ag, Au) + USGS Mineral Commodity Summaries 2026 per kg contained element; see analysis/meoh_catalyst_cost_2026_10_06/catalyst_prices.py (per kg contained element)",
            "type": "price_table",
            "low": "9.878",
            "high": "39.512"
          },
          {
            "parameter": "price.metal_Y",
            "value": "40.0",
            "unit": "USD/kg",
            "source": "prices.json:metal_Y",
            "location": "frozen NH3 harness prices (Ru, Os, Fe, Rh, Ir, Co, Re, Mo, Ni, W, Pd, Pt, Cu, Ag, Au) + USGS Mineral Commodity Summaries 2026 per kg contained element; see analysis/meoh_catalyst_cost_2026_10_06/catalyst_prices.py (per kg contained element)",
            "type": "price_table",
            "low": "20.0",
            "high": "80.0"
          },
          {
            "parameter": "price.metal_Zn",
            "value": "3.2849",
            "unit": "USD/kg",
            "source": "prices.json:metal_Zn",
            "location": "frozen NH3 harness prices (Ru, Os, Fe, Rh, Ir, Co, Re, Mo, Ni, W, Pd, Pt, Cu, Ag, Au) + USGS Mineral Commodity Summaries 2026 per kg contained element; see analysis/meoh_catalyst_cost_2026_10_06/catalyst_prices.py (per kg contained element)",
            "type": "price_table",
            "low": "1.64245",
            "high": "6.5698"
          },
          {
            "parameter": "price.metal_Zr",
            "value": "22.0",
            "unit": "USD/kg",
            "source": "prices.json:metal_Zr",
            "location": "frozen NH3 harness prices (Ru, Os, Fe, Rh, Ir, Co, Re, Mo, Ni, W, Pd, Pt, Cu, Ag, Au) + USGS Mineral Commodity Summaries 2026 per kg contained element; see analysis/meoh_catalyst_cost_2026_10_06/catalyst_prices.py (per kg contained element)",
            "type": "price_table",
            "low": "11.0",
            "high": "44.0"
          },
          {
            "parameter": "price.metal_Ce",
            "value": "2.1005306603773586",
            "unit": "USD/kg",
            "source": "prices.json:metal_Ce",
            "location": "frozen NH3 harness prices (Ru, Os, Fe, Rh, Ir, Co, Re, Mo, Ni, W, Pd, Pt, Cu, Ag, Au) + USGS Mineral Commodity Summaries 2026 per kg contained element; see analysis/meoh_catalyst_cost_2026_10_06/catalyst_prices.py (per kg contained element)",
            "type": "price_table",
            "low": "1.0502653301886793",
            "high": "4.201061320754717"
          },
          {
            "parameter": "price.metal_Si",
            "value": "2.866006",
            "unit": "USD/kg",
            "source": "prices.json:metal_Si",
            "location": "frozen NH3 harness prices (Ru, Os, Fe, Rh, Ir, Co, Re, Mo, Ni, W, Pd, Pt, Cu, Ag, Au) + USGS Mineral Commodity Summaries 2026 per kg contained element; see analysis/meoh_catalyst_cost_2026_10_06/catalyst_prices.py (per kg contained element)",
            "type": "price_table",
            "low": "1.433003",
            "high": "5.732012"
          },
          {
            "parameter": "price.metal_Mg",
            "value": "2.5",
            "unit": "USD/kg",
            "source": "prices.json:metal_Mg",
            "location": "frozen NH3 harness prices (Ru, Os, Fe, Rh, Ir, Co, Re, Mo, Ni, W, Pd, Pt, Cu, Ag, Au) + USGS Mineral Commodity Summaries 2026 per kg contained element; see analysis/meoh_catalyst_cost_2026_10_06/catalyst_prices.py (per kg contained element)",
            "type": "price_table",
            "low": "1.25",
            "high": "5.0"
          },
          {
            "parameter": "price.metal_Ca",
            "value": "0.3637940925436203",
            "unit": "USD/kg",
            "source": "prices.json:metal_Ca",
            "location": "frozen NH3 harness prices (Ru, Os, Fe, Rh, Ir, Co, Re, Mo, Ni, W, Pd, Pt, Cu, Ag, Au) + USGS Mineral Commodity Summaries 2026 per kg contained element; see analysis/meoh_catalyst_cost_2026_10_06/catalyst_prices.py (per kg contained element)",
            "type": "price_table",
            "low": "0.18189704627181014",
            "high": "0.7275881850872405"
          },
          {
            "parameter": "price.metal_K",
            "value": "1.4455393066229791",
            "unit": "USD/kg",
            "source": "prices.json:metal_K",
            "location": "frozen NH3 harness prices (Ru, Os, Fe, Rh, Ir, Co, Re, Mo, Ni, W, Pd, Pt, Cu, Ag, Au) + USGS Mineral Commodity Summaries 2026 per kg contained element; see analysis/meoh_catalyst_cost_2026_10_06/catalyst_prices.py (per kg contained element)",
            "type": "price_table",
            "low": "0.7227696533114896",
            "high": "2.8910786132459583"
          },
          {
            "parameter": "price.metal_Ba",
            "value": "0.3569000679809653",
            "unit": "USD/kg",
            "source": "prices.json:metal_Ba",
            "location": "frozen NH3 harness prices (Ru, Os, Fe, Rh, Ir, Co, Re, Mo, Ni, W, Pd, Pt, Cu, Ag, Au) + USGS Mineral Commodity Summaries 2026 per kg contained element; see analysis/meoh_catalyst_cost_2026_10_06/catalyst_prices.py (per kg contained element)",
            "type": "price_table",
            "low": "0.17845003399048265",
            "high": "0.7138001359619306"
          },
          {
            "parameter": "price.metal_B",
            "value": "1.0",
            "unit": "USD/kg",
            "source": "prices.json:metal_B",
            "location": "frozen NH3 harness prices (Ru, Os, Fe, Rh, Ir, Co, Re, Mo, Ni, W, Pd, Pt, Cu, Ag, Au) + USGS Mineral Commodity Summaries 2026 per kg contained element; see analysis/meoh_catalyst_cost_2026_10_06/catalyst_prices.py (per kg contained element)",
            "type": "price_table",
            "low": "0.5",
            "high": "2.0"
          },
          {
            "parameter": "price.capital_recovery_factor",
            "value": "0.0944",
            "unit": "1/y",
            "source": "prices.json:capital_recovery_factor",
            "location": "7 %/y over 20 y (Enterprise Products PDH, EPA GHG permit application 2012); range 5-12 %/y",
            "type": "price_table",
            "low": "0.08",
            "high": "0.13"
          },
          {
            "parameter": "price.fixed_om_fraction_of_capex",
            "value": "0.04",
            "unit": "1/y",
            "source": "prices.json:fixed_om_fraction_of_capex",
            "location": "NCE chain assumption, 4 %/y of installed capital",
            "type": "price_table",
            "low": "0.02",
            "high": "0.06"
          }
        ]
      },
      "impact": "price-table values fixed by construction; only identical parameter names compared numerically; unmatched values remain unresolved"
    },
    {
      "category": "data",
      "evidence": {
        "rejected": [],
        "converted": 237,
        "total": 237,
        "missing_loading_records": 0
      },
      "impact": "unknown composition loading and inherited outlet/density assumptions may affect catalyst inventory and ranking"
    },
    {
      "category": "numerics",
      "evidence": "all converted record costs finite, positive and parts close; deterministic repeat checked",
      "impact": "does not verify the optimiser reaches a global minimum"
    }
  ],
  "uncertainty": {
    "hand": {
      "draws": 1000,
      "seed": 20260816,
      "Fe_sigma_eV": 0.2271258177356984,
      "other_uniform_half_width_eV": 0.15
    },
    "ai_assumptions": [
      {
        "parameter": "basis.capacity_t_per_y",
        "value": "1000000",
        "unit": "t/y",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "200000",
        "high": "1500000"
      },
      {
        "parameter": "basis.operating_hours_per_y",
        "value": "8000",
        "unit": "h/y",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "7200",
        "high": "8400"
      },
      {
        "parameter": "basis.feeds.H2.T_K",
        "value": "298.15",
        "unit": "K",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "288.15",
        "high": "313.15"
      },
      {
        "parameter": "basis.feeds.H2.P_bar",
        "value": "30.0",
        "unit": "bar",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "20.0",
        "high": "40.0"
      },
      {
        "parameter": "basis.feeds.H2.purity_mol_frac",
        "value": "0.999",
        "unit": "fraction",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.995",
        "high": "0.9999"
      },
      {
        "parameter": "basis.feeds.N2.T_K",
        "value": "298.15",
        "unit": "K",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "288.15",
        "high": "313.15"
      },
      {
        "parameter": "basis.feeds.N2.P_bar",
        "value": "30.0",
        "unit": "bar",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "20.0",
        "high": "40.0"
      },
      {
        "parameter": "basis.feeds.N2.purity_mol_frac",
        "value": "0.999",
        "unit": "fraction",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.995",
        "high": "0.9999"
      },
      {
        "parameter": "basis.product.NH3.P_bar",
        "value": "20.0",
        "unit": "bar",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "10.0",
        "high": "30.0"
      },
      {
        "parameter": "basis.product.NH3.purity_mol_frac",
        "value": "0.995",
        "unit": "fraction",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.99",
        "high": "0.999"
      },
      {
        "parameter": "basis.utilities.cooling_water_supply_temperature",
        "value": "298.15",
        "unit": "K",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "288.15",
        "high": "303.15"
      },
      {
        "parameter": "basis.utilities.cooling_water_return_temperature",
        "value": "308.15",
        "unit": "K",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "303.15",
        "high": "318.15"
      },
      {
        "parameter": "basis.utilities.electric_motor_efficiency",
        "value": "0.95",
        "unit": "fraction",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.9",
        "high": "0.98"
      },
      {
        "parameter": "kinetic.activation_energy_J_per_mol",
        "value": "100000",
        "unit": "J/mol",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "60000",
        "high": "160000"
      },
      {
        "parameter": "kinetic.pressure_order_total",
        "value": "1.0",
        "unit": "dimensionless",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.5",
        "high": "1.5"
      },
      {
        "parameter": "kinetic.max_rate_scale",
        "value": "1000",
        "unit": "dimensionless",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "100",
        "high": "10000"
      },
      {
        "parameter": "operation.loop_pressure_min_bar",
        "value": "80",
        "unit": "bar",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "50",
        "high": "100"
      },
      {
        "parameter": "operation.pressure_grid_points",
        "value": "8",
        "unit": "count",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "5",
        "high": "12"
      },
      {
        "parameter": "operation.conversion_grid_points",
        "value": "32",
        "unit": "count",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "20",
        "high": "60"
      },
      {
        "parameter": "operation.min_conversion",
        "value": "0.02",
        "unit": "fraction",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.01",
        "high": "0.05"
      },
      {
        "parameter": "operation.equilibrium_fraction_limit",
        "value": "0.95",
        "unit": "fraction",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.85",
        "high": "0.99"
      },
      {
        "parameter": "operation.purge_fraction",
        "value": "0.02",
        "unit": "fraction",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.005",
        "high": "0.05"
      },
      {
        "parameter": "operation.nh3_condensation_recovery",
        "value": "0.995",
        "unit": "fraction",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.98",
        "high": "0.9995"
      },
      {
        "parameter": "compressor.gamma_h2",
        "value": "1.4",
        "unit": "dimensionless",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "1.35",
        "high": "1.42"
      },
      {
        "parameter": "compressor.gamma_n2",
        "value": "1.4",
        "unit": "dimensionless",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "1.35",
        "high": "1.42"
      },
      {
        "parameter": "compressor.gamma_loop",
        "value": "1.35",
        "unit": "dimensionless",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "1.25",
        "high": "1.4"
      },
      {
        "parameter": "compressor.recycle_pressure_ratio",
        "value": "1.05",
        "unit": "ratio",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "1.02",
        "high": "1.12"
      },
      {
        "parameter": "energy.electricity_primary_factor",
        "value": "2.5",
        "unit": "GJ_primary/GJ_electric",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "2.0",
        "high": "3.0"
      },
      {
        "parameter": "heat.reaction_enthalpy_J_per_mol_NH3",
        "value": "-46110",
        "unit": "J/mol NH3",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "-47000",
        "high": "-45000"
      },
      {
        "parameter": "heat.feed_effluent_recovery_fraction",
        "value": "0.75",
        "unit": "fraction",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.55",
        "high": "0.9"
      },
      {
        "parameter": "heat.waste_heat_recovery_fraction",
        "value": "0.7",
        "unit": "fraction",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.5",
        "high": "0.85"
      },
      {
        "parameter": "heat.cooling_electricity_GJ_per_GJ_removed",
        "value": "0.015",
        "unit": "GJ electric/GJ heat",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.005",
        "high": "0.04"
      },
      {
        "parameter": "heat.sensible_cooling_GJ_per_t",
        "value": "0.35",
        "unit": "GJ/t NH3",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.15",
        "high": "0.7"
      },
      {
        "parameter": "catalyst.default_cycle_h",
        "value": "24000",
        "unit": "h",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "8000",
        "high": "60000"
      },
      {
        "parameter": "catalyst.activity_loss_fraction_at_cycle",
        "value": "0.1",
        "unit": "fraction",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.05",
        "high": "0.25"
      },
      {
        "parameter": "catalyst.reference_inventory_kg",
        "value": "2000000",
        "unit": "kg",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "500000",
        "high": "5000000"
      },
      {
        "parameter": "catalyst.reference_rate_kg_per_kg_h",
        "value": "0.12",
        "unit": "kg/kg/h",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.03",
        "high": "0.5"
      },
      {
        "parameter": "capital.scale_exponent",
        "value": "0.65",
        "unit": "dimensionless",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.55",
        "high": "0.75"
      },
      {
        "parameter": "capital.pressure_exponent",
        "value": "0.25",
        "unit": "dimensionless",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.15",
        "high": "0.4"
      },
      {
        "parameter": "capital.reference_capacity_t_per_y",
        "value": "1000000",
        "unit": "t/y",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "500000",
        "high": "1500000"
      },
      {
        "parameter": "capital.reference_pressure_bar",
        "value": "150",
        "unit": "bar",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "100",
        "high": "200"
      },
      {
        "parameter": "capital.hydrogen_feed_compressor_usd",
        "value": "25000000",
        "unit": "USD",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "12000000",
        "high": "50000000"
      },
      {
        "parameter": "capital.nitrogen_feed_compressor_usd",
        "value": "18000000",
        "unit": "USD",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "8000000",
        "high": "35000000"
      },
      {
        "parameter": "capital.synthesis_gas_mixer_usd",
        "value": "1000000",
        "unit": "USD",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "300000",
        "high": "3000000"
      },
      {
        "parameter": "capital.feed_effluent_exchanger_usd",
        "value": "12000000",
        "unit": "USD",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "6000000",
        "high": "25000000"
      },
      {
        "parameter": "capital.ammonia_converter_usd",
        "value": "45000000",
        "unit": "USD",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "20000000",
        "high": "90000000"
      },
      {
        "parameter": "capital.waste_heat_boiler_usd",
        "value": "18000000",
        "unit": "USD",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "8000000",
        "high": "35000000"
      },
      {
        "parameter": "capital.final_product_cooler_usd",
        "value": "15000000",
        "unit": "USD",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "7000000",
        "high": "30000000"
      },
      {
        "parameter": "capital.ammonia_knockout_usd",
        "value": "6000000",
        "unit": "USD",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "2500000",
        "high": "12000000"
      },
      {
        "parameter": "capital.purge_splitter_usd",
        "value": "500000",
        "unit": "USD",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "150000",
        "high": "1500000"
      },
      {
        "parameter": "capital.recycle_compressor_usd",
        "value": "7500000",
        "unit": "USD",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "3500000",
        "high": "18000000"
      },
      {
        "parameter": "capital.product_and_offsites_usd",
        "value": "38000000",
        "unit": "USD",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "18000000",
        "high": "75000000"
      },
      {
        "parameter": "capital.reactor_activity_scale_exponent",
        "value": "0.6",
        "unit": "dimensionless",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.45",
        "high": "0.75"
      },
      {
        "parameter": "capital.reactor_min_scale",
        "value": "0.35",
        "unit": "fraction",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.2",
        "high": "0.6"
      },
      {
        "parameter": "capital.offsites_capacity_exponent",
        "value": "0.6",
        "unit": "dimensionless",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.5",
        "high": "0.7"
      },
      {
        "parameter": "operation.reference_T_K",
        "value": "700",
        "unit": "K",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "650",
        "high": "750"
      },
      {
        "parameter": "operation.reference_P_bar",
        "value": "150",
        "unit": "bar",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "100",
        "high": "220"
      },
      {
        "parameter": "operation.reference_X",
        "value": "0.15",
        "unit": "fraction",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.08",
        "high": "0.25"
      },
      {
        "parameter": "operation.reference_selectivity",
        "value": "1.0",
        "unit": "fraction",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.99",
        "high": "1.0"
      },
      {
        "parameter": "operation.reference_y_N2",
        "value": "0.25",
        "unit": "fraction",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.24",
        "high": "0.26"
      },
      {
        "parameter": "operation.reference_y_H2",
        "value": "0.75",
        "unit": "fraction",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.74",
        "high": "0.76"
      },
      {
        "parameter": "feed.nitrogen_embodied_electricity_kWh_per_kg",
        "value": "0.20",
        "unit": "kWh/kg",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "0.10",
        "high": "0.40"
      },
      {
        "parameter": "heat.reaction_entropy_J_per_mol_reaction_K",
        "value": "-210.1",
        "unit": "J/mol reaction/K",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "-220",
        "high": "-198"
      },
      {
        "parameter": "heat.delta_cp_J_per_mol_NH3_K",
        "value": "-16.0",
        "unit": "J/mol NH3/K",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "-22",
        "high": "-10"
      }
    ]
  }
}
```
## nh3_b3

Costed 237/237; scored records 237.
AI ranking: {"groups": 44, "papers": 31, "changed": 10, "gt5pct": 1, "fraction": 0.22727272727272727, "ci95": [0.07317073170731707, 0.375], "bootstrap": {"draws": 2000, "seed": 20261006, "unit": "paper"}}

| Reference quantity | Hand | AI | Relative gap |
|---|---|---|---|
| cost_usd_per_t | 11.515783597179267 | 657.9355795350514 | 56.133374727205656 |
| parts.feed | 0.0 | 532.675709001233 | None |
| shares.feed | 0.0 | 0.8096168159467273 | None |
| parts.energy | 7.598967948092639 | 41.53018751064137 | 4.465240516123713 |
| shares.energy | 0.6598741530670972 | 0.06312196634811852 | -0.904342417331051 |
| parts.capital | 3.7915922812770635 | 79.21701735900989 | 19.89281006034975 |
| shares.capital | 0.3292517829360561 | 0.12040239169766562 | -0.6343151413669066 |
| parts.catalyst | 0.12522336780956467 | 4.512665664167083 | 35.0369293934802 |
| shares.catalyst | 0.010874063996846685 | 0.006858826007488583 | -0.3692490673700707 |
| parts.other | 0.0 | 0.0 | None |
| shares.other | 0.0 | 0.0 | None |
| operating.T_K | 698.15 | 773.15 | 0.10742677075127127 |
| operating.P_bar | 105.0 | 250.0 | 1.380952380952381 |
| operating.per_pass_conversion | 0.17205887115595606 | 0.15 | -0.12820536952123585 |
| balances.capacity_t_per_y | 346750.0 | 600000.0 | 0.7303532804614274 |
| balances.energy_GJ_per_t | 0.54712569226267 | 4.672146094947153 | 7.5394383064433 |
| basis.battery_limit | Reduced catalyst-dependent NH3 cost. NH3-FINAL-1.1 adds the pressure-attributable converter-shell cost and the compressor bare-module CAPEX; loop heat exchangers, separator vessel and piping remain outside the boundary (declared omission; direction: further penalizes high pressure). Purchased feed costs excluded. | Purified gaseous H2 and N2 at the synthesis-loop battery limit through compression, mixing, heat recovery, trim heating, catalytic conversion, NH3 condensation/separation, recycle, purge handling and product letdown; upstream H2 production, air separation, ammonia storage and export are excluded. | None |
| basis.capacity_t_per_y | 346750.0 | 600000 | 0.7303532804614274 |
| basis.feeds.H2.P_bar | 30 | 30.0 | 0.0 |
| basis.feeds.H2.T_K | 298.15 | 298.15 | 0.0 |
| basis.feeds.H2.purity_mol_frac | 1 | 1.0 | 0.0 |
| basis.feeds.N2.P_bar | 30 | 30.0 | 0.0 |
| basis.feeds.N2.T_K | 298.15 | 298.15 | 0.0 |
| basis.feeds.N2.purity_mol_frac | 1 | 1.0 | 0.0 |
| basis.operating_hours_per_y | 8322.0 | 8000 | -0.03869262196587364 |
| basis.product.NH3.P_bar | 105.0 | 20.0 | -0.8095238095238095 |
| basis.product.NH3.T_K | 303.15 | None | None |
| basis.product.NH3.purity_mol_frac | None | 1.0 | None |
| basis.product.NH3.state | condensed at separator | None | None |
| basis.purchased_preheat_reason | None | None | None |
| basis.utilities.cooling_water_return_T | None | 308.15 | None |
| basis.utilities.cooling_water_supply_T | None | 298.15 | None |
| basis.utilities.electricity_primary_energy_factor | None | 2.5 | None |
| basis.utilities.refrigeration_COP | None | 4.0 | None |

### Group comparison: printed

Compared 44; verdict agreement 36; pooled cost Spearman 0.6465218206534479.

| Group | Complete | Hand changed | AI changed | Verdict agrees | Hand gap | AI gap | Plant leader agrees | Within-group cost Spearman |
|---|---|---|---|---|---:|---:|---|---:|
| 10.1002/aenm.201801772 / 400 C / 0.1 MPa / H2/N2 3 / 6.6e+04 mL/g/h | True | True | True | True | 0.3726866579010617 | 0.10097972335433547 | True | 0.9999999999999999 |
| 10.1002/aenm.201801772 / 400 C / 5 MPa / H2/N2 3 / 6.6e+04 mL/g/h | True | True | True | True | 0.13764479669840068 | 0.00793116010497763 | True | 0.3186813186813187 |
| 10.1002/anie.201712398 / 300 C / 0.9 MPa / H2/N2 3 / 3.6e+04 mL/g/h | True | True | True | True | 0.22051247667258944 | 0.009184495284045857 | False | 0.9642857142857145 |
| 10.1002/anie.201907171 / 400 C / 1 MPa / H2/N2 3 / SV not given | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1002/anie.201907171 / 459 C / 1 MPa / H2/N2 3 / SV not given | True | True | True | True | 0.2521433032419236 | 0.002152247960005349 | True | 1.0 |
| 10.1002/anie.201907171 / 459 C / 5 MPa / H2/N2 3 / SV not given | True | False | False | True | 0.0 | 0.0 | True | 0.7999999999999999 |
| 10.1002/asia.201900618 / 400 C / 3 MPa / H2/N2 3 / 2.4e+04 mL/g/h | True | False | True | False | 0.0 | 0.011487178183182456 | False | -0.9999999999999999 |
| 10.1002/asia.201900618 / 450 C / 3 MPa / H2/N2 3 / 2.4e+04 mL/g/h | True | True | True | True | 0.011003879980802544 | 0.015077063032244986 | True | 0.39999999999999997 |
| 10.1007/s10562-019-02674-1 / 450 C / 3 MPa / H2/N2 3 / 2.4e+04 mL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1021/acs.chemmater.9b03099 / 375 C / 0.1 MPa / H2/N2 3 / 1.8e+04 mL/g/h | True | True | False | False | 0.023580082421838622 | 0.0 | False | -0.5 |
| 10.1021/acs.iecr.8b02126 / 400 C / 1 MPa / H2/N2 3 / 6e+04 mL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1021/acs.iecr.9b01610 / 400 C / 1 MPa / H2/N2 3 / 6e+04 mL/g/h | True | False | False | True | 0.0 | 0.0 | True | 1.0 |
| 10.1021/acs.jpcc.7b07268 / 340 C / 0.1 MPa / H2/N2 3 / 3.6e+04 mL/g/h | True | True | False | False | 0.05394087067900166 | 0.0 | False | -0.9999999999999999 |
| 10.1021/acscatal.1c02887 / 350 C / 1 MPa / H2/N2 3 / 7.2e+04 mL/g/h | True | False | False | True | 0.0 | 0.0 | True | 1.0 |
| 10.1021/acscatal.1c02887 / 400 C / 6 MPa / H2/N2 3 / 7.2e+04 mL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1021/acscatal.7b00284 / 300 C / 1 MPa / H2/N2 3 / 6e+04 mL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1021/acscatal.8b02839 / 340 C / 0.1 MPa / H2/N2 3 / 3.6e+04 mL/g/h | True | False | False | True | 0.0 | 0.0 | True | 1.0 |
| 10.1021/acscatal.8b03554 / 400 C / 1 MPa / H2/N2 3 / 1.8e+04 mL/g/h | True | False | False | True | 0.0 | 0.0 | True | 1.0 |
| 10.1021/acscatal.8b03554 / 400 C / 1 MPa / H2/N2 3 / 6e+04 mL/g/h | True | False | False | True | 0.0 | 0.0 | True | 1.0 |
| 10.1021/acscatal.8b03650 / 340 C / 0.1 MPa / H2/N2 3 / 1.8e+04 mL/g/h | True | False | False | True | 0.0 | 0.0 | True | 1.0 |
| 10.1021/acscatal.8b03743 / 340 C / 0.1 MPa / H2/N2 3 / 3.6e+04 mL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1021/acssuschemeng.8b04683 / 400 C / 1 MPa / H2/N2 3 / 7.2e+04 mL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1021/cs401044a / 340 C / 0.1 MPa / H2/N2 3 / 1.8e+04 mL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1021/jacs.0c06624 / 400 C / 0.9 MPa / H2/N2 3 / 3.6e+04 mL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1021/jacs.7b08891 / 400 C / 5.1 MPa / H2/N2 3 / 6.6e+04 mL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1021/jacs.9b10726 / 400 C / 0.9 MPa / H2/N2 3 / 3.6e+04 mL/g/h | True | True | False | False | 0.2873732745288964 | 0.0 | False | 0.5 |
| 10.1038/nchem.1476 / 320 C / 0.1 MPa / H2/N2 3 / 1.8e+04 mL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.4285714285714286 |
| 10.1038/nchem.1476 / 400 C / 0.1 MPa / H2/N2 3 / 1.8e+04 mL/g/h | True | False | True | False | 0.0 | 0.017551309777974256 | False | 0.7 |
| 10.1038/nchem.1476 / 400 C / 1 MPa / H2/N2 3 / 1.8e+04 mL/g/h | True | False | True | False | 0.0 | 0.01780043283014332 | False | 0.7500000000000002 |
| 10.1038/s41467-020-15868-8 / 300 C / 0.1 MPa / H2/N2 3 / 3.6e+04 mL/g/h | True | True | True | True | 0.11814062966870109 | 0.006304620453039922 | True | 0.8928571428571429 |
| 10.1038/s41467-020-15868-8 / 340 C / 0.1 MPa / H2/N2 3 / 3.6e+04 mL/g/h | True | True | True | True | 0.28264737930732764 | 0.006803631757411832 | True | 0.7619047619047621 |
| 10.1038/s41586-020-2464-9 / 340 C / 0.1 MPa / H2/N2 3 / 3.6e+04 mL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1039/c6cy02089e / 380 C / 1 MPa / H2/N2 3 / 1.8e+04 mL/g/h | True | False | False | True | 0.0 | 0.0 | True | 1.0 |
| 10.1039/c6cy02089e / 380 C / 3 MPa / H2/N2 3 / SV not given | True | False | False | True | 0.0 | 0.0 | True | 1.0 |
| 10.1039/c6cy02089e / 400 C / 1 MPa / H2/N2 3 / 1.8e+04 mL/g/h | True | True | False | False | 0.02438687018126262 | 0.0 | False | 0.8787878787878788 |
| 10.1039/c6cy02089e / 400 C / 3 MPa / H2/N2 3 / 1.8e+04 mL/g/h | True | False | False | True | 0.0 | 0.0 | True | 1.0 |
| 10.1039/c6sc00767h / 300 C / 0.1 MPa / H2/N2 3 / 3.6e+04 mL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.6 |
| 10.1039/c6sc00767h / 340 C / 0.1 MPa / H2/N2 3 / 3.6e+04 mL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.8999999999999998 |
| 10.1039/c6sc02382g / 390 C / 0.9 MPa / H2/N2 3 / 1.8e+04 mL/g/h | True | False | False | True | 0.0 | 0.0 | True | 1.0 |
| 10.1039/c7sc05343f / 350 C / 1 MPa / H2/N2 3 / 7.2e+04 mL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.6904761904761906 |
| 10.1039/c8qi01244j / 425 C / 1 MPa / H2/N2 3 / SV not given | True | False | False | True | 0.0 | 0.0 | True | 1.0 |
| 10.1039/c9cc07385j / 400 C / 1 MPa / H2/N2 3 / 3.6e+04 mL/g/h | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1039/c9ra03097b / 400 C / 10 MPa / H2/N2 3 / SV not given | True | False | False | True | 0.0 | 0.0 | True | 0.9999999999999999 |
| 10.1039/d0ta05238h / 450 C / 1 MPa / H2/N2 3 / 1.6e+04 mL/g/h | True | True | False | False | 0.015008780423757972 | 0.0 | False | 0.7 |

### Bottlenecks

```json
{
  "largest_cost_item": "feed",
  "hand_largest_cost_item": "energy",
  "controlling_property": "metal",
  "hand_controlling_property": "not available",
  "attribution_share": {
    "selectivity": 0.0,
    "activity": 0.109,
    "temperature": 0.084,
    "stability": 0.0,
    "metal": 0.807
  },
  "cheapest_record": "nh3:0040",
  "cheapest_catalyst": "Co@BaO/MgO-700red",
  "hand_cheapest_record": "nh3:0231",
  "hand_cheapest_catalyst": "commercial Fe catalyst",
  "cheapest_common_record": "nh3:0040",
  "cheapest_common_catalyst": "Co@BaO/MgO-700red",
  "hand_cheapest_common_record": "nh3:0231",
  "hand_cheapest_common_catalyst": "commercial Fe catalyst"
}
```

### Difference diagnosis and uncertainty

```json
{
  "rules": "deterministic evidence comparison; categories are evidence, not causal proof",
  "largest_reference_gaps": [
    {
      "field": "cost_usd_per_t",
      "hand": 11.515783597179267,
      "ai": 657.9355795350514,
      "relative_gap": 56.133374727205656,
      "categories": [
        "boundary",
        "structure",
        "parameters"
      ],
      "rule": "basis mismatch -> boundary; cost/energy/capital -> unit structure and matched parameters; no automatic causal attribution"
    },
    {
      "field": "parts.catalyst",
      "hand": 0.12522336780956467,
      "ai": 4.512665664167083,
      "relative_gap": 35.0369293934802,
      "categories": [
        "structure",
        "parameters"
      ],
      "rule": "basis mismatch -> boundary; cost/energy/capital -> unit structure and matched parameters; no automatic causal attribution"
    },
    {
      "field": "parts.capital",
      "hand": 3.7915922812770635,
      "ai": 79.21701735900989,
      "relative_gap": 19.89281006034975,
      "categories": [
        "structure",
        "parameters"
      ],
      "rule": "basis mismatch -> boundary; cost/energy/capital -> unit structure and matched parameters; no automatic causal attribution"
    },
    {
      "field": "balances.energy_GJ_per_t",
      "hand": 0.54712569226267,
      "ai": 4.672146094947153,
      "relative_gap": 7.5394383064433,
      "categories": [
        "structure",
        "parameters"
      ],
      "rule": "basis mismatch -> boundary; cost/energy/capital -> unit structure and matched parameters; no automatic causal attribution"
    },
    {
      "field": "parts.energy",
      "hand": 7.598967948092639,
      "ai": 41.53018751064137,
      "relative_gap": 4.465240516123713,
      "categories": [
        "structure",
        "parameters"
      ],
      "rule": "basis mismatch -> boundary; cost/energy/capital -> unit structure and matched parameters; no automatic causal attribution"
    },
    {
      "field": "operating.P_bar",
      "hand": 105.0,
      "ai": 250.0,
      "relative_gap": 1.380952380952381,
      "categories": [
        "structure",
        "parameters"
      ],
      "rule": "basis mismatch -> boundary; cost/energy/capital -> unit structure and matched parameters; no automatic causal attribution"
    },
    {
      "field": "shares.energy",
      "hand": 0.6598741530670972,
      "ai": 0.06312196634811852,
      "relative_gap": -0.904342417331051,
      "categories": [
        "structure",
        "parameters"
      ],
      "rule": "basis mismatch -> boundary; cost/energy/capital -> unit structure and matched parameters; no automatic causal attribution"
    },
    {
      "field": "basis.product.NH3.P_bar",
      "hand": 105.0,
      "ai": 20.0,
      "relative_gap": -0.8095238095238095,
      "categories": [
        "boundary"
      ],
      "rule": "basis mismatch -> boundary; cost/energy/capital -> unit structure and matched parameters; no automatic causal attribution"
    },
    {
      "field": "balances.capacity_t_per_y",
      "hand": 346750.0,
      "ai": 600000.0,
      "relative_gap": 0.7303532804614274,
      "categories": [
        "structure",
        "parameters"
      ],
      "rule": "basis mismatch -> boundary; cost/energy/capital -> unit structure and matched parameters; no automatic causal attribution"
    },
    {
      "field": "basis.capacity_t_per_y",
      "hand": 346750.0,
      "ai": 600000,
      "relative_gap": 0.7303532804614274,
      "categories": [
        "boundary"
      ],
      "rule": "basis mismatch -> boundary; cost/energy/capital -> unit structure and matched parameters; no automatic causal attribution"
    },
    {
      "field": "shares.capital",
      "hand": 0.3292517829360561,
      "ai": 0.12040239169766562,
      "relative_gap": -0.6343151413669066,
      "categories": [
        "structure",
        "parameters"
      ],
      "rule": "basis mismatch -> boundary; cost/energy/capital -> unit structure and matched parameters; no automatic causal attribution"
    },
    {
      "field": "shares.catalyst",
      "hand": 0.010874063996846685,
      "ai": 0.006858826007488583,
      "relative_gap": -0.3692490673700707,
      "categories": [
        "structure",
        "parameters"
      ],
      "rule": "basis mismatch -> boundary; cost/energy/capital -> unit structure and matched parameters; no automatic causal attribution"
    }
  ],
  "largest_ranking_gaps": {
    "printed": [
      {
        "group": "10.1021/jacs.9b10726 | 400 C | 0.9 MPa | H2/N2 3 | 3.6e+04 mL/g/h",
        "hand_leader": "Fe(1.2 wt %)/BaCeO3−xNyHz",
        "ai_leader": "Co(4.7 wt %)/BaCeO3−xNyHz",
        "hand_gap": 0.2873732745288964,
        "ai_gap": 0.0,
        "categories": [
          "structure",
          "parameters",
          "data",
          "boundary"
        ]
      },
      {
        "group": "10.1002/anie.201712398 | 300 C | 0.9 MPa | H2/N2 3 | 3.6e+04 mL/g/h",
        "hand_leader": "Industrial Fe catalyst",
        "ai_leader": "Co(8%)/Ba-Ca(NH2)2",
        "hand_gap": 0.22051247667258944,
        "ai_gap": 0.009184495284045857,
        "categories": [
          "structure",
          "parameters",
          "data",
          "boundary"
        ]
      },
      {
        "group": "10.1021/acs.jpcc.7b07268 | 340 C | 0.1 MPa | H2/N2 3 | 3.6e+04 mL/g/h",
        "hand_leader": "Ru/CaNH",
        "ai_leader": "Ru/Ca2NH",
        "hand_gap": 0.05394087067900166,
        "ai_gap": 0.0,
        "categories": [
          "structure",
          "parameters",
          "data",
          "boundary"
        ]
      },
      {
        "group": "10.1039/c6cy02089e | 400 C | 1 MPa | H2/N2 3 | 1.8e+04 mL/g/h",
        "hand_leader": "2K–Ru/r-CeO2",
        "ai_leader": "2Cs–Ru/r-CeO2",
        "hand_gap": 0.02438687018126262,
        "ai_gap": 0.0,
        "categories": [
          "structure",
          "parameters",
          "data",
          "boundary"
        ]
      },
      {
        "group": "10.1021/acs.chemmater.9b03099 | 375 C | 0.1 MPa | H2/N2 3 | 1.8e+04 mL/g/h",
        "hand_leader": "Ru SAs/S-1",
        "ai_leader": "Ba-Ru SAs/S-1",
        "hand_gap": 0.023580082421838622,
        "ai_gap": 0.0,
        "categories": [
          "structure",
          "parameters",
          "data",
          "boundary"
        ]
      },
      {
        "group": "10.1038/nchem.1476 | 400 C | 1 MPa | H2/N2 3 | 1.8e+04 mL/g/h",
        "hand_leader": "Ru-Cs/MgO",
        "ai_leader": "Ru/C12A7:e−",
        "hand_gap": 0.0,
        "ai_gap": 0.01780043283014332,
        "categories": [
          "structure",
          "parameters",
          "data",
          "boundary"
        ]
      },
      {
        "group": "10.1038/nchem.1476 | 400 C | 0.1 MPa | H2/N2 3 | 1.8e+04 mL/g/h",
        "hand_leader": "Ru-Ba/AC",
        "ai_leader": "Ru/C12A7:e−",
        "hand_gap": 0.0,
        "ai_gap": 0.017551309777974256,
        "categories": [
          "structure",
          "parameters",
          "data",
          "boundary"
        ]
      },
      {
        "group": "10.1039/d0ta05238h | 450 C | 1 MPa | H2/N2 3 | 1.6e+04 mL/g/h",
        "hand_leader": "Magnetite based industrial Fe catalyst",
        "ai_leader": "80% Fe–20% Ce0.8Sm0.2O2−δ",
        "hand_gap": 0.015008780423757972,
        "ai_gap": 0.0,
        "categories": [
          "structure",
          "parameters",
          "data",
          "boundary"
        ]
      },
      {
        "group": "10.1002/asia.201900618 | 400 C | 3 MPa | H2/N2 3 | 2.4e+04 mL/g/h",
        "hand_leader": "3.5% Ru/BaCeO3-a",
        "ai_leader": "4% Cs-1.25%Ru/BaCeO3-a",
        "hand_gap": 0.0,
        "ai_gap": 0.011487178183182456,
        "categories": [
          "structure",
          "parameters",
          "data",
          "boundary"
        ]
      }
    ]
  },
  "ranking_disagreements": {
    "printed": 8
  },
  "findings": [
    {
      "category": "boundary",
      "evidence": "hand NH3 excludes purchased feeds; AI has positive feed cost",
      "impact": "total costs have different boundaries"
    },
    {
      "category": "boundary",
      "evidence": {
        "field": "product.NH3.P_bar",
        "hand": 105.0,
        "ai": 20.0
      },
      "impact": "different plant design basis"
    },
    {
      "category": "boundary",
      "evidence": {
        "field": "battery_limit",
        "hand": "Reduced catalyst-dependent NH3 cost. NH3-FINAL-1.1 adds the pressure-attributable converter-shell cost and the compressor bare-module CAPEX; loop heat exchangers, separator vessel and piping remain outside the boundary (declared omission; direction: further penalizes high pressure). Purchased feed costs excluded.",
        "ai": "Purified gaseous H2 and N2 at the synthesis-loop battery limit through compression, mixing, heat recovery, trim heating, catalytic conversion, NH3 condensation/separation, recycle, purge handling and product letdown; upstream H2 production, air separation, ammonia storage and export are excluded."
      },
      "impact": "different plant design basis"
    },
    {
      "category": "boundary",
      "evidence": {
        "field": "operating_hours_per_y",
        "hand": 8322.0,
        "ai": 8000
      },
      "impact": "different plant design basis"
    },
    {
      "category": "boundary",
      "evidence": {
        "field": "capacity_t_per_y",
        "hand": 346750.0,
        "ai": 600000
      },
      "impact": "different plant design basis"
    },
    {
      "category": "structure",
      "evidence": {
        "hand_units": [
          "reactor",
          "fresh compression",
          "recycle compression",
          "refrigeration",
          "compressor capex"
        ],
        "ai_units": [
          {
            "name": "H2 feed compressor",
            "type": "compressor"
          },
          {
            "name": "N2 feed compressor",
            "type": "compressor"
          },
          {
            "name": "makeup gas mixer",
            "type": "other"
          },
          {
            "name": "loop feed mixer",
            "type": "other"
          },
          {
            "name": "feed effluent heat exchanger",
            "type": "heat_exchanger"
          },
          {
            "name": "recovered-heat trim exchanger",
            "type": "heat_exchanger"
          },
          {
            "name": "ammonia synthesis reactor",
            "type": "reactor"
          },
          {
            "name": "interbed heat recovery exchanger",
            "type": "heat_exchanger"
          },
          {
            "name": "ammonia condenser separator",
            "type": "separation"
          },
          {
            "name": "purge splitter",
            "type": "other"
          },
          {
            "name": "recycle compressor",
            "type": "compressor"
          },
          {
            "name": "NH3 product letdown",
            "type": "other"
          },
          {
            "name": "purge handling and offsites",
            "type": "offsites"
          }
        ],
        "ai_checklist": {
          "feed_preparation": {
            "included": [
              "H2 feed compressor",
              "N2 feed compressor",
              "makeup gas mixer",
              "loop feed mixer",
              "feed effluent heat exchanger",
              "recovered-heat trim exchanger"
            ]
          },
          "reactor_heat_supply_or_removal": {
            "included": [
              "ammonia synthesis reactor",
              "interbed heat recovery exchanger",
              "feed effluent heat exchanger",
              "recovered-heat trim exchanger"
            ]
          },
          "catalyst_regeneration": {
            "excluded": "The compared ammonia catalysts are replaced at end of life rather than regenerated continuously; replacement and downtime are represented in catalyst cost and availability assumptions."
          },
          "product_compression": {
            "excluded": "Ammonia leaves the high-pressure separator above the specified 20 bar product pressure, so a letdown valve is required but no product compressor is thermodynamically necessary."
          },
          "separation_and_purification": {
            "included": [
              "ammonia condenser separator",
              "NH3 product letdown"
            ]
          },
          "recycle": {
            "included": [
              "purge splitter",
              "recycle compressor",
              "loop feed mixer"
            ]
          },
          "heat_recovery": {
            "included": [
              "interbed heat recovery exchanger",
              "feed effluent heat exchanger",
              "recovered-heat trim exchanger"
            ]
          },
          "utilities_and_offsites": {
            "included": [
              "purge handling and offsites",
              "recovered-heat trim exchanger",
              "ammonia condenser separator"
            ]
          }
        },
        "missing_hand_unit_types": [],
        "extra_ai_unit_types": [
          "heat_exchanger",
          "offsites",
          "other",
          "separation"
        ],
        "ai_recycle_declaration": {
          "included": [
            "purge splitter",
            "recycle compressor",
            "loop feed mixer"
          ]
        },
        "hand_kinetics": "NH3 descriptor microkinetics and 0.8 equilibrium approach"
      },
      "impact": "unit types are a screening comparison, not proof of causal impact; NH3 separator vessel is outside the reduced CAPEX boundary; checklist exclusions retained verbatim"
    },
    {
      "category": "parameters",
      "evidence": {
        "gaps_gt20pct": [],
        "unmatched_hand_parameters": [
          "calibration_factor",
          "catalyst_life_y",
          "compressor_efficiency",
          "discount_rate",
          "electricity_USD_MWh",
          "metal_recovery_fraction",
          "plant_life_y",
          "reactor_exponent",
          "reactor_fixed_USD",
          "reactor_reference_m3",
          "reactor_variable_USD"
        ],
        "hand_parameters": {
          "discount_rate": 0.12,
          "plant_life_y": 25,
          "electricity_USD_MWh": 50.0,
          "compressor_efficiency": 0.75,
          "catalyst_life_y": 10.0,
          "metal_recovery_fraction": 0.0,
          "reactor_fixed_USD": 66800.0,
          "reactor_variable_USD": 268000.0,
          "reactor_reference_m3": 20.0,
          "reactor_exponent": 0.52,
          "calibration_factor": 74351.60773111923
        },
        "ai_parameters": {
          "basis.capacity_t_per_y": 600000.0,
          "basis.operating_hours_per_y": 8000.0,
          "basis.feeds.H2.T_K": 298.15,
          "basis.feeds.H2.P_bar": 30.0,
          "basis.feeds.H2.purity_mol_frac": 1.0,
          "basis.feeds.N2.T_K": 298.15,
          "basis.feeds.N2.P_bar": 30.0,
          "basis.feeds.N2.purity_mol_frac": 1.0,
          "basis.product.NH3.P_bar": 20.0,
          "basis.product.NH3.purity_mol_frac": 1.0,
          "basis.utilities.cooling_water_supply_T": 298.15,
          "basis.utilities.cooling_water_return_T": 308.15,
          "basis.utilities.electricity_primary_energy_factor": 2.5,
          "basis.utilities.refrigeration_COP": 4.0,
          "prices.hydrogen": 3.0,
          "prices.electricity": 80.0,
          "prices.catalyst_support_and_manufacturing": 20.0,
          "prices.metal_Ru": 53852.5,
          "prices.metal_Fe": 8.0,
          "prices.metal_Co": 56.28401553583051,
          "prices.metal_K": 1.4455393066229791,
          "prices.capital_recovery_factor": 0.0944,
          "prices.fixed_om_fraction_of_capex": 0.04,
          "thermo.reaction_heat_J_per_mol_NH3": 46110.0,
          "thermo.reaction_entropy_J_per_molrxn_K": -198.9,
          "thermo.gas_cp_GJ_per_kmol_K": 3.1e-05,
          "thermo.nh3_condensation_GJ_per_t": 1.37,
          "compression.isentropic_efficiency": 0.75,
          "compression.recycle_pressure_drop_fraction": 0.03,
          "separation.nh3_recovery": 1.0,
          "separation.purge_fraction": 0.0,
          "heat_exchange.effectiveness": 0.75,
          "kinetics.apparent_Ea_J_per_mol": 80000.0,
          "kinetics.pressure_exponent": 0.7,
          "kinetics.composition_exponent": 1.0,
          "kinetics.minimum_rate_kgkg_h": 1e-08,
          "operation.T_min_K": 573.15,
          "operation.T_max_K": 773.15,
          "operation.P_min_bar": 80.0,
          "operation.P_max_bar": 250.0,
          "operation.X_min": 0.03,
          "operation.X_max": 0.15,
          "operation.equilibrium_margin": 0.97,
          "catalyst.default_life_h": 48000.0,
          "catalyst.bulk_density_kg_m3": 1100.0,
          "catalyst.inventory_design_factor": 1.25,
          "capital.scaling_exponent": 0.6,
          "capital.reference_capacity_tpy": 600000.0,
          "capital.H2_feed_compressor_usd": 28000000.0,
          "capital.N2_feed_compressor_usd": 18000000.0,
          "capital.makeup_gas_mixer_usd": 1000000.0,
          "capital.loop_feed_mixer_usd": 1000000.0,
          "capital.feed_effluent_heat_exchanger_usd": 22000000.0,
          "capital.electric_trim_heater_usd": 6000000.0,
          "capital.ammonia_synthesis_reactor_usd": 85000000.0,
          "capital.ammonia_condenser_separator_usd": 55000000.0,
          "capital.purge_splitter_usd": 500000.0,
          "capital.recycle_compressor_usd": 3500000.0,
          "capital.NH3_product_letdown_usd": 1500000.0,
          "capital.purge_handling_and_offsites_usd": 35000000.0,
          "capital.catalyst_volume_reference_m3": 250.0,
          "reference.T_K": 723.15,
          "reference.P_bar": 90.0,
          "reference.X": 0.005814,
          "reference.S": 1.0,
          "reference.r": 0.026502,
          "reference.y_key": 0.25,
          "reference.y_cofeed": 0.75,
          "thermo.R_J_per_mol_K": 8.314462618,
          "catalyst.default_metal_loading_wt_frac": 0.05,
          "capital.nominal_conversion": 0.15,
          "capital.nominal_pressure_bar": 150.0,
          "capital.minimum_scale_factor": 0.05,
          "thermo.reaction_heat_temperature_coefficient_J_per_molNH3_K": 15.4,
          "capital.interbed_heat_recovery_usd": 20000000.0
        },
        "price_table_rows": [
          {
            "parameter": "prices.hydrogen",
            "value": "3.0",
            "unit": "USD/kg",
            "source": "prices.json:hydrogen",
            "location": "Becker, Penev & Braun, J. Energy Resour. Technol. 2019 anchor 3 USD/kg; grey about 2, electrolytic 5-7 (DOE Pathways to Commercial Liftoff: Clean Hydrogen, 2024)",
            "type": "price_table",
            "low": "1.5",
            "high": "7.0"
          },
          {
            "parameter": "prices.electricity",
            "value": "80.0",
            "unit": "USD/MWh",
            "source": "prices.json:electricity",
            "location": "industrial power assumption used across the NCE chains; EIA 2024 US industrial average about 80 USD/MWh",
            "type": "price_table",
            "low": "40.0",
            "high": "150.0"
          },
          {
            "parameter": "prices.catalyst_support_and_manufacturing",
            "value": "20.0",
            "unit": "USD/kg",
            "source": "prices.json:catalyst_support_and_manufacturing",
            "location": "NCE chain assumption for support plus manufacturing per kg of finished catalyst, excluding active metals",
            "type": "price_table",
            "low": "5.0",
            "high": "100.0"
          },
          {
            "parameter": "prices.metal_Ru",
            "value": "53852.5",
            "unit": "USD/kg",
            "source": "prices.json:metal_Ru",
            "location": "frozen NH3 harness prices (Ru, Os, Fe, Rh, Ir, Co, Re, Mo, Ni, W, Pd, Pt, Cu, Ag, Au) + USGS Mineral Commodity Summaries 2026 per kg contained element; see analysis/meoh_catalyst_cost_2026_10_06/catalyst_prices.py (per kg contained element)",
            "type": "price_table",
            "low": "26926.25",
            "high": "107705.0"
          },
          {
            "parameter": "prices.metal_Fe",
            "value": "8.0",
            "unit": "USD/kg",
            "source": "prices.json:metal_Fe",
            "location": "frozen NH3 harness prices (Ru, Os, Fe, Rh, Ir, Co, Re, Mo, Ni, W, Pd, Pt, Cu, Ag, Au) + USGS Mineral Commodity Summaries 2026 per kg contained element; see analysis/meoh_catalyst_cost_2026_10_06/catalyst_prices.py (per kg contained element)",
            "type": "price_table",
            "low": "4.0",
            "high": "16.0"
          },
          {
            "parameter": "prices.metal_Co",
            "value": "56.28401553583051",
            "unit": "USD/kg",
            "source": "prices.json:metal_Co",
            "location": "frozen NH3 harness prices (Ru, Os, Fe, Rh, Ir, Co, Re, Mo, Ni, W, Pd, Pt, Cu, Ag, Au) + USGS Mineral Commodity Summaries 2026 per kg contained element; see analysis/meoh_catalyst_cost_2026_10_06/catalyst_prices.py (per kg contained element)",
            "type": "price_table",
            "low": "28.142007767915256",
            "high": "112.56803107166103"
          },
          {
            "parameter": "prices.metal_K",
            "value": "1.4455393066229791",
            "unit": "USD/kg",
            "source": "prices.json:metal_K",
            "location": "frozen NH3 harness prices (Ru, Os, Fe, Rh, Ir, Co, Re, Mo, Ni, W, Pd, Pt, Cu, Ag, Au) + USGS Mineral Commodity Summaries 2026 per kg contained element; see analysis/meoh_catalyst_cost_2026_10_06/catalyst_prices.py (per kg contained element)",
            "type": "price_table",
            "low": "0.7227696533114896",
            "high": "2.8910786132459583"
          },
          {
            "parameter": "prices.capital_recovery_factor",
            "value": "0.0944",
            "unit": "1/y",
            "source": "prices.json:capital_recovery_factor",
            "location": "7 %/y over 20 y (Enterprise Products PDH, EPA GHG permit application 2012); range 5-12 %/y",
            "type": "price_table",
            "low": "0.08",
            "high": "0.13"
          },
          {
            "parameter": "prices.fixed_om_fraction_of_capex",
            "value": "0.04",
            "unit": "1/y",
            "source": "prices.json:fixed_om_fraction_of_capex",
            "location": "NCE chain assumption, 4 %/y of installed capital",
            "type": "price_table",
            "low": "0.02",
            "high": "0.06"
          }
        ]
      },
      "impact": "price-table values fixed by construction; only identical parameter names compared numerically; unmatched values remain unresolved"
    },
    {
      "category": "data",
      "evidence": {
        "rejected": [],
        "converted": 237,
        "total": 237,
        "missing_loading_records": 0
      },
      "impact": "unknown composition loading and inherited outlet/density assumptions may affect catalyst inventory and ranking"
    },
    {
      "category": "numerics",
      "evidence": "all converted record costs finite, positive and parts close; deterministic repeat checked",
      "impact": "does not verify the optimiser reaches a global minimum"
    }
  ],
  "uncertainty": {
    "hand": {
      "draws": 1000,
      "seed": 20260816,
      "Fe_sigma_eV": 0.2271258177356984,
      "other_uniform_half_width_eV": 0.15
    },
    "ai_assumptions": [
      {
        "parameter": "basis.capacity_t_per_y",
        "value": "600000",
        "unit": "t/y",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "300000",
        "high": "1000000"
      },
      {
        "parameter": "basis.operating_hours_per_y",
        "value": "8000",
        "unit": "h/y",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "7500",
        "high": "8400"
      },
      {
        "parameter": "basis.feeds.H2.T_K",
        "value": "298.15",
        "unit": "K",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "288.15",
        "high": "313.15"
      },
      {
        "parameter": "basis.feeds.H2.P_bar",
        "value": "30.0",
        "unit": "bar",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "20.0",
        "high": "40.0"
      },
      {
        "parameter": "basis.feeds.H2.purity_mol_frac",
        "value": "1.0",
        "unit": "mol/mol",
        "source": "",
        "location": "Nominal impurity-free boundary; uncertainty permits trace impurity",
        "type": "assumption",
        "low": "0.999",
        "high": "1.0"
      },
      {
        "parameter": "basis.feeds.N2.T_K",
        "value": "298.15",
        "unit": "K",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "288.15",
        "high": "313.15"
      },
      {
        "parameter": "basis.feeds.N2.P_bar",
        "value": "30.0",
        "unit": "bar",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "20.0",
        "high": "40.0"
      },
      {
        "parameter": "basis.feeds.N2.purity_mol_frac",
        "value": "1.0",
        "unit": "mol/mol",
        "source": "",
        "location": "Nominal impurity-free boundary; uncertainty permits trace impurity",
        "type": "assumption",
        "low": "0.999",
        "high": "1.0"
      },
      {
        "parameter": "basis.product.NH3.P_bar",
        "value": "20.0",
        "unit": "bar",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "15.0",
        "high": "30.0"
      },
      {
        "parameter": "basis.product.NH3.purity_mol_frac",
        "value": "1.0",
        "unit": "mol/mol",
        "source": "",
        "location": "Pure-NH3 accounting basis; uncertainty includes commercial specification",
        "type": "assumption",
        "low": "0.998",
        "high": "1.0"
      },
      {
        "parameter": "basis.utilities.cooling_water_supply_T",
        "value": "298.15",
        "unit": "K",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "288.15",
        "high": "303.15"
      },
      {
        "parameter": "basis.utilities.cooling_water_return_T",
        "value": "308.15",
        "unit": "K",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "303.15",
        "high": "318.15"
      },
      {
        "parameter": "basis.utilities.electricity_primary_energy_factor",
        "value": "2.5",
        "unit": "GJ_primary/GJ_electric",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "1.0",
        "high": "3.0"
      },
      {
        "parameter": "basis.utilities.refrigeration_COP",
        "value": "4.0",
        "unit": "GJ_cooling/GJ_electric",
        "source": "",
        "location": "",
        "type": "assumption",
        "low": "2.5",
        "high": "6.0"
      },
      {
        "parameter": "thermo.gas_cp_GJ_per_kmol_K",
        "value": "3.1e-05",
        "unit": "GJ/kmol/K",
        "source": "https://webbook.nist.gov/cgi/cbook.cgi?ID=C7727379&Mask=1",
        "location": "NIST gas heat-capacity data near 300-800 K; rounded mixture-average engineering value",
        "type": "assumption",
        "low": "2.8e-05",
        "high": "3.6e-05"
      },
      {
        "parameter": "thermo.nh3_condensation_GJ_per_t",
        "value": "1.37",
        "unit": "GJ/t NH3",
        "source": "https://webbook.nist.gov/cgi/cbook.cgi?ID=C7664417&Mask=4",
        "location": "NIST phase-change enthalpy data, converted and rounded to product-mass basis",
        "type": "assumption",
        "low": "1.1",
        "high": "1.6"
      },
      {
        "parameter": "compression.recycle_pressure_drop_fraction",
        "value": "0.03",
        "unit": "fraction",
        "source": "",
        "location": "Synthesis-loop pressure loss across beds, exchangers and separator",
        "type": "assumption",
        "low": "0.01",
        "high": "0.08"
      },
      {
        "parameter": "separation.nh3_recovery",
        "value": "1.0",
        "unit": "fraction",
        "source": "",
        "location": "Nominal complete NH3 recovery for pure-product accounting; lower bound covers small unrecovered fraction",
        "type": "assumption",
        "low": "0.995",
        "high": "1.0"
      },
      {
        "parameter": "separation.purge_fraction",
        "value": "0.0",
        "unit": "fraction",
        "source": "https://www.linde-engineering.com/products-and-services/process-plants/hydrogen-and-synthesis-gas/gas-synthesis",
        "location": "Linde LAC description states inert-free synthesis gas avoids syngas purges and a purge-gas separation step",
        "type": "assumption",
        "low": "0.0",
        "high": "0.01"
      },
      {
        "parameter": "heat_exchange.effectiveness",
        "value": "0.75",
        "unit": "fraction",
        "source": "",
        "location": "Feed-effluent exchanger effectiveness",
        "type": "assumption",
        "low": "0.6",
        "high": "0.9"
      },
      {
        "parameter": "kinetics.apparent_Ea_J_per_mol",
        "value": "80000",
        "unit": "J/mol",
        "source": "",
        "location": "Cross-catalyst transfer parameter spanning reported apparent activation energies",
        "type": "assumption",
        "low": "40000",
        "high": "160000"
      },
      {
        "parameter": "kinetics.pressure_exponent",
        "value": "0.7",
        "unit": "dimensionless",
        "source": "",
        "location": "Aggregate pressure dependence used only to transfer each measured productivity",
        "type": "assumption",
        "low": "0.0",
        "high": "1.5"
      },
      {
        "parameter": "kinetics.composition_exponent",
        "value": "1.0",
        "unit": "dimensionless",
        "source": "",
        "location": "Stoichiometric-feed correction exponent around each laboratory anchor",
        "type": "assumption",
        "low": "0.0",
        "high": "2.0"
      },
      {
        "parameter": "kinetics.minimum_rate_kgkg_h",
        "value": "1e-08",
        "unit": "kg NH3/kg catalyst/h",
        "source": "",
        "location": "Numerical floor for catalyst inventory sizing",
        "type": "assumption",
        "low": "1e-10",
        "high": "1e-06"
      },
      {
        "parameter": "operation.T_min_K",
        "value": "573.15",
        "unit": "K",
        "source": "https://www.mdpi.com/2077-0375/15/10/308",
        "location": "Review discussion of industrial Fe catalyst synthesis-loop operation around 350-520 C",
        "type": "assumption",
        "low": "523.15",
        "high": "623.15"
      },
      {
        "parameter": "operation.T_max_K",
        "value": "773.15",
        "unit": "K",
        "source": "https://www.mdpi.com/2077-0375/15/10/308",
        "location": "Review discussion of industrial Fe catalyst synthesis-loop operation around 350-520 C",
        "type": "assumption",
        "low": "723.15",
        "high": "823.15"
      },
      {
        "parameter": "operation.P_min_bar",
        "value": "80.0",
        "unit": "bar",
        "source": "https://valmet.com/insights/articles/services/taking-the-heat/",
        "location": "Typical ammonia converter operation reported in the 100-200 bar range",
        "type": "assumption",
        "low": "50",
        "high": "120"
      },
      {
        "parameter": "operation.P_max_bar",
        "value": "250.0",
        "unit": "bar",
        "source": "https://valmet.com/insights/articles/services/taking-the-heat/",
        "location": "Typical ammonia converter operation reported in the 100-200 bar range",
        "type": "assumption",
        "low": "180",
        "high": "300"
      },
      {
        "parameter": "operation.X_min",
        "value": "0.03",
        "unit": "fraction",
        "source": "",
        "location": "Lower per-pass conversion bound to limit pathological recycle",
        "type": "assumption",
        "low": "0.01",
        "high": "0.08"
      },
      {
        "parameter": "operation.X_max",
        "value": "0.15",
        "unit": "fraction",
        "source": "10.1016/j.energy.2017.06.157",
        "location": "Industrial ammonia-loop configurations and converter operation support a conservative per-pass conversion range around the 15% nominal bound",
        "type": "assumption",
        "low": "0.10",
        "high": "0.20"
      },
      {
        "parameter": "operation.equilibrium_margin",
        "value": "0.97",
        "unit": "fraction",
        "source": "",
        "location": "Keep numerical optimum below equilibrium conversion",
        "type": "assumption",
        "low": "0.9",
        "high": "0.995"
      },
      {
        "parameter": "catalyst.bulk_density_kg_m3",
        "value": "1100",
        "unit": "kg/m3",
        "source": "",
        "location": "Representative packed catalyst bulk density for reactor-volume sizing",
        "type": "assumption",
        "low": "700",
        "high": "1600"
      },
      {
        "parameter": "catalyst.inventory_design_factor",
        "value": "1.25",
        "unit": "dimensionless",
        "source": "",
        "location": "Extra installed catalyst volume for maldistribution, aging and reserve activity",
        "type": "assumption",
        "low": "1.0",
        "high": "2.0"
      },
      {
        "parameter": "capital.scaling_exponent",
        "value": "0.6",
        "unit": "dimensionless",
        "source": "https://www.netl.doe.gov/projects/files/QGESSCostEstimationMethodologyforNETLAssessmentsforEnergyAnalysisPerspective_040419.pdf",
        "location": "NETL cost-estimation methodology discusses capacity-factor scaling for conceptual equipment estimates",
        "type": "assumption",
        "low": "0.5",
        "high": "0.75"
      },
      {
        "parameter": "capital.reference_capacity_tpy",
        "value": "600000",
        "unit": "t/y",
        "source": "https://www.mdpi.com/2077-0375/15/10/308",
        "location": "Industrial ammonia plant capacities discussed in the 1000-3000 t/day range; 600 kt/y reference is within that range",
        "type": "assumption",
        "low": "300000",
        "high": "1000000"
      },
      {
        "parameter": "capital.H2_feed_compressor_usd",
        "value": "28000000.0",
        "unit": "USD",
        "source": "",
        "location": "Installed cost allocation at the 600 kt/y reference basis; summed loop cost is constrained by literature-scale conceptual estimates",
        "type": "assumption",
        "low": "14000000.0",
        "high": "56000000.0"
      },
      {
        "parameter": "capital.N2_feed_compressor_usd",
        "value": "18000000.0",
        "unit": "USD",
        "source": "",
        "location": "Installed cost allocation at the 600 kt/y reference basis; summed loop cost is constrained by literature-scale conceptual estimates",
        "type": "assumption",
        "low": "9000000.0",
        "high": "36000000.0"
      },
      {
        "parameter": "capital.makeup_gas_mixer_usd",
        "value": "1000000.0",
        "unit": "USD",
        "source": "",
        "location": "Installed cost allocation at the 600 kt/y reference basis; summed loop cost is constrained by literature-scale conceptual estimates",
        "type": "assumption",
        "low": "500000.0",
        "high": "2000000.0"
      },
      {
        "parameter": "capital.loop_feed_mixer_usd",
        "value": "1000000.0",
        "unit": "USD",
        "source": "",
        "location": "Installed cost allocation at the 600 kt/y reference basis; summed loop cost is constrained by literature-scale conceptual estimates",
        "type": "assumption",
        "low": "500000.0",
        "high": "2000000.0"
      },
      {
        "parameter": "capital.feed_effluent_heat_exchanger_usd",
        "value": "22000000.0",
        "unit": "USD",
        "source": "",
        "location": "Installed cost allocation at the 600 kt/y reference basis; summed loop cost is constrained by literature-scale conceptual estimates",
        "type": "assumption",
        "low": "11000000.0",
        "high": "44000000.0"
      },
      {
        "parameter": "capital.electric_trim_heater_usd",
        "value": "6000000.0",
        "unit": "USD",
        "source": "",
        "location": "Installed cost allocation at the 600 kt/y reference basis; summed loop cost is constrained by literature-scale conceptual estimates",
        "type": "assumption",
        "low": "3000000.0",
        "high": "12000000.0"
      },
      {
        "parameter": "capital.ammonia_synthesis_reactor_usd",
        "value": "85000000.0",
        "unit": "USD",
        "source": "",
        "location": "Installed cost allocation at the 600 kt/y reference basis; summed loop cost is constrained by literature-scale conceptual estimates",
        "type": "assumption",
        "low": "42500000.0",
        "high": "170000000.0"
      },
      {
        "parameter": "capital.ammonia_condenser_separator_usd",
        "value": "55000000.0",
        "unit": "USD",
        "source": "",
        "location": "Installed cost allocation at the 600 kt/y reference basis; summed loop cost is constrained by literature-scale conceptual estimates",
        "type": "assumption",
        "low": "27500000.0",
        "high": "110000000.0"
      },
      {
        "parameter": "capital.purge_splitter_usd",
        "value": "500000.0",
        "unit": "USD",
        "source": "",
        "location": "Installed cost allocation at the 600 kt/y reference basis; summed loop cost is constrained by literature-scale conceptual estimates",
        "type": "assumption",
        "low": "250000.0",
        "high": "1000000.0"
      },
      {
        "parameter": "capital.recycle_compressor_usd",
        "value": "3500000.0",
        "unit": "USD",
        "source": "",
        "location": "Installed recycle pressure-loss compressor allocation at the reference basis",
        "type": "assumption",
        "low": "1500000.0",
        "high": "7000000.0"
      },
      {
        "parameter": "capital.NH3_product_letdown_usd",
        "value": "1500000.0",
        "unit": "USD",
        "source": "",
        "location": "Installed cost allocation at the 600 kt/y reference basis; summed loop cost is constrained by literature-scale conceptual estimates",
        "type": "assumption",
        "low": "750000.0",
        "high": "3000000.0"
      },
      {
        "parameter": "capital.purge_handling_and_offsites_usd",
        "value": "35000000.0",
        "unit": "USD",
        "source": "",
        "location": "Installed cost allocation at the 600 kt/y reference basis; summed loop cost is constrained by literature-scale conceptual estimates",
        "type": "assumption",
        "low": "17500000.0",
        "high": "70000000.0"
      },
      {
        "parameter": "capital.catalyst_volume_reference_m3",
        "value": "250.0",
        "unit": "m3",
        "source": "",
        "location": "Reference converter catalyst volume used to scale reactor installed cost when low activity requires larger inventory",
        "type": "assumption",
        "low": "100",
        "high": "600"
      },
      {
        "parameter": "catalyst.default_metal_loading_wt_frac",
        "value": "0.05",
        "unit": "kg metal/kg catalyst",
        "source": "",
        "location": "Fallback total active-metal loading where literature composition lacks weight percentages",
        "type": "assumption",
        "low": "0.01",
        "high": "0.2"
      },
      {
        "parameter": "capital.nominal_conversion",
        "value": "0.15",
        "unit": "fraction",
        "source": "",
        "location": "Nominal loop conversion for duty-ratio capital scaling",
        "type": "assumption",
        "low": "0.1",
        "high": "0.22"
      },
      {
        "parameter": "capital.nominal_pressure_bar",
        "value": "150.0",
        "unit": "bar",
        "source": "https://valmet.com/insights/articles/services/taking-the-heat/",
        "location": "Representative synthesis-loop pressure within the reported 100-200 bar range",
        "type": "assumption",
        "low": "100",
        "high": "200"
      },
      {
        "parameter": "capital.minimum_scale_factor",
        "value": "0.05",
        "unit": "dimensionless",
        "source": "",
        "location": "Lower bound preventing conceptual equipment costs from vanishing at low calculated duty",
        "type": "assumption",
        "low": "0.02",
        "high": "0.2"
      },
      {
        "parameter": "thermo.reaction_heat_temperature_coefficient_J_per_molNH3_K",
        "value": "15.4",
        "unit": "J/mol NH3/K",
        "source": "https://webbook.nist.gov/cgi/cbook.cgi?ID=C7664417&Mask=1",
        "location": "Effective temperature correction derived from NIST ideal-gas heat capacities over the synthesis range",
        "type": "assumption",
        "low": "10.0",
        "high": "22.0"
      },
      {
        "parameter": "capital.interbed_heat_recovery_usd",
        "value": "20000000.0",
        "unit": "USD",
        "source": "",
        "location": "Installed integrated interbed cooling and steam-generation allocation at the 600 kt/y basis",
        "type": "assumption",
        "low": "10000000.0",
        "high": "50000000.0"
      }
    ]
  }
}
```

## Across-build agreement

```json
{
  "reference_spread": 0.15446530919731227,
  "spread_within20pct": true,
  "pairwise_spearman": {
    "D:\\agent_runs\\nh3_b1 vs D:\\agent_runs\\nh3_b2": 0.19927595022518385,
    "D:\\agent_runs\\nh3_b1 vs D:\\agent_runs\\nh3_b3": 0.2378600867561633,
    "D:\\agent_runs\\nh3_b2 vs D:\\agent_runs\\nh3_b3": 0.8607358047661805
  },
  "pairwise_ge08": false,
  "quantitative_consistency": false,
  "common_successful_records": 237,
  "conclusions": {
    "largest_cost_item": {
      "status": "robust (all agree)",
      "values": {
        "D:\\agent_runs\\nh3_b1": "feed",
        "D:\\agent_runs\\nh3_b2": "feed",
        "D:\\agent_runs\\nh3_b3": "feed"
      }
    },
    "controlling_property": {
      "status": "majority",
      "values": {
        "D:\\agent_runs\\nh3_b1": "activity",
        "D:\\agent_runs\\nh3_b2": "metal",
        "D:\\agent_runs\\nh3_b3": "metal"
      }
    },
    "cheapest_common_catalyst": {
      "status": "majority",
      "values": {
        "D:\\agent_runs\\nh3_b1": "Co@BaO/MgO-700red",
        "D:\\agent_runs\\nh3_b2": "commercial Fe catalyst",
        "D:\\agent_runs\\nh3_b3": "Co@BaO/MgO-700red"
      }
    }
  }
}
```

Primary build (median reference cost): D:\agent_runs\nh3_b3

## Loader exclusions

[]
