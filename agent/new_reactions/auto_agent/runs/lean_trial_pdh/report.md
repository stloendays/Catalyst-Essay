# non-oxidative propane dehydrogenation: autonomous run 2026-11-11 01:17

Plant model: plant_framework 1.1, pdh_ours.json (SHA-256 335c22019089eb39).

## Papers

candidates found 25, screened 25, included 17; downloaded 6; processed 6; with usable records 6; replaced/dropped 0.


## Data

records 38, usable 31 from 6 papers; printed values found in the paper 169/169 (1.0); plot readings 60. Every record keeps its page and table/figure location in records.csv.

## Plant cost (NCE metrics)

reference plant (Pt-Sn/Al2O3 (Oleflex-type)): 772.29 USD/t; parts {'raw_C3H8': 491.43, 'credits': -32.77, 'energy': np.float64(84.49), 'capital': np.float64(224.6), 'catalyst': np.float64(4.5), 'regeneration': np.float64(0.04)}; largest raw_C3H8.
cheapest literature record: {'paper': '10_1039_d2sc03723h', 'catalyst': '0.1Pt7CuSiO3-680R', 'T_C': 580, 'cost': np.float64(861.53)}; records below the reference 0 of 31.

| lab metric | groups | leader is not the cheapest | other catalyst | same catalyst, other T | regret > 1 % | max regret % |
|---|---:|---:|---:|---:|---:|---:|
| productivity | 5 | 3 | 3 | 0 | 3 | 5.58 |
| conversion | 5 | 4 | 3 | 1 | 3 | 5.58 |
| selectivity | 5 | 1 | 0 | 1 | 0 | 0.6 |

attribution of the cost gap to the reference: {'selectivity': np.float64(0.141), 'activity': np.float64(0.016), 'temperature': np.float64(0.694), 'metal': np.float64(0.018), 'stability': np.float64(0.131)}
cost change at the reference: {'+1 pt selectivity': np.float64(-5.732), 'activity x2': np.float64(-2.268), 'stability x10': np.float64(-0.206), 'C3H8 price -1 %': np.float64(-4.914)}
backward design: 0 records can reach the reference cost by selectivity alone; 3 records measured below half the plant per-pass conversion.

## Sensitivity


## Run

wall 6.0 min; agent decisions 25476 tokens; extraction 148743 tokens over 6 papers (24790 per paper).

## Decision

Use the PtCu single-atom alloy catalyst 0.1Pt7CuSiO3-680R at about 580 °C: in the fixed plant model it gives the lowest propylene cost among the usable literature records. Its advantage comes mainly from operating-temperature economics with sufficiently high conversion/selectivity, while selectivity-only ranking changes have little cost impact.
