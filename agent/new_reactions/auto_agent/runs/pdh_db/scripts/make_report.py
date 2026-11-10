import pandas as pd, json, math
R=pd.read_csv('analysis_record_costs.csv');rank=pd.read_csv('analysis_rankings.csv');att=pd.read_csv('analysis_attribution.csv');back=pd.read_csv('analysis_backward.csv');sens=pd.read_csv('analysis_sensitivity.csv');S=json.load(open('analysis_summary.json'))
D=pd.read_csv('db/visible.csv')[['rec_id','catalyst','T_C']]
R=R.merge(D,on='rec_id',suffixes=('','_name'))
# catalyst name got overwritten in prior result by catalyst-cost field, use catalyst_name
costtbl=R[['rec_id','paper','catalyst_name','selectivity','stability_revealed','total','x','inventory_t','feed','energy','capital','catalyst','regeneration']].copy()
for c in ['selectivity','total','x','inventory_t','feed','energy','capital','catalyst','regeneration']:costtbl[c]=costtbl[c].map(lambda x:f'{x:.3f}' if c in ['selectivity','x'] else f'{x:.1f}')
costtbl.columns=['Record','Paper','Catalyst','S','stability measured?','cost $/t','opt. X','inventory t','feed','energy','capital','catalyst','regen']
ct=costtbl.to_markdown(index=False)
rt=rank[rank.metric.isin(['conversion','product_productivity'])].copy();rt['regret_usd_t']=rt.regret_usd_t.map(lambda x:f'{x:,.1f}');rt.columns=['Paper','Lab metric','Lab leader','Plant choice','Agree?','Disagreement type','Regret $/t'];rtt=rt.to_markdown(index=False)
# backward only above reference
b=back[back.base_cost>S['reference']['total']].copy();b['base_cost']=b.base_cost.map(lambda x:f'{x:.1f}');b['selectivity_needed']=b.selectivity_needed.map(lambda x:'not sufficient' if pd.isna(x) else f'{100*x:.2f}%');b['activity_multiplier_needed']=b.activity_multiplier_needed.map(lambda x:'not sufficient' if pd.isna(x) else f'{x:.2f}x');b['metal_price_multiplier_needed']=b.metal_price_multiplier_needed.map(lambda x:'not sufficient' if pd.isna(x) else f'{x:.2f}x');b.columns=['Record','Base $/t','S needed alone','Activity needed alone','Metal-price factor alone'];bt=b.to_markdown(index=False)
st=sens[['scenario','winner','winner_cost','margin','reference_cost']].copy();st[['winner_cost','margin','reference_cost']]=st[['winner_cost','margin','reference_cost']].round(1);stt=st.to_markdown(index=False)
text=f'''# Industrial screening of literature catalysts for non-oxidative propane dehydrogenation

**Reaction:** C3H8 → C3H6 + H2  
**Analysis date:** 10 November 2026  
**Database:** 59 catalyst × condition records from six coded papers (P01–P06).

## Executive answer

- **Industrial bottleneck:** the cost is carried primarily by **propane feed and carbon selectivity to propylene**, not precious-metal price or coke-cycle stability. In the reference plant, fresh propane is **$441.2/t propylene**, 59.9% of the net modeled cost; annualised capital is $261.3/t and energy is $74.6/t. Across the 27 costable records, selectivity is the largest one-at-a-time cost-gap term for **22/27**, activity for 4/27, and temperature/equilibrium for 1/27. Metal price and modeled regeneration are never the largest term.
- **Plant choice from the measured literature set:** **PDH-015, PtGa/SiO2 at 600 °C**, at **$658.2/t propylene** in the central case, versus **$736.7/t** for the industrial reference. Its measured selectivity is 99.1%; the optimized per-pass conversion is 45.4%; modeled inventory is 10.6 t. Its disclosed stability is weak—10% activity loss in 8.13 h—so this is a cost-screen winner, **not a claim of plant readiness**. PDH-017 is only $1.8/t behind.
- **Do paper rankings agree?** Using the two metrics named in the question (conversion and propylene productivity), the lab leader agrees with the cheapest plant choice in **8/12 comparisons (66.7%)**. There are 4 disagreements: **3 switch to another catalyst, 0 are the same catalyst at another temperature, and 1 is the same catalyst under another same-temperature condition**. Mean regret is $1,693.8/t, median $921.6/t, but this is dominated by P01's very low selectivities; the two non-P01 regrets are only $1.8 and $6.9/t.
- **Main uncertainty:** selectivity remained masked for 32/59 records, so those records cannot be responsibly costed or ruled out. Long-term irreversible lifetime is unavailable for every literature catalyst; short time-on-stream deactivation was treated as a regeneration-cycle indicator only.

## 1. Reveal strategy and budget

All **35/35** reveal units were used.

1. Revealed selectivity for 27 records: both visible-metric leaders and plausible plant contenders in every paper, with denser coverage of P02, P05 and P06 where activity/selectivity looked industrially relevant.
2. Revealed stability for eight decision-critical records: PDH-003, 015, 017, 018, 020, 027, 033 and 059. Six had numeric tests; PDH-003 and PDH-033 had no reported stability values.
3. This allocation ensured that every paper's conversion leader and product-productivity leader was costable. It did not reveal all lower-ranked records because selectivity, rather than another stability datum, was needed first to compute propane consumption.

**Treatment of masked fields:**
- Masked selectivity: no point estimate and no plant cost; these 32 records are reported as uncostable.
- Masked/no numeric stability: assumed 24 h to 10% activity loss, with 5–100 h sensitivity. This affects regeneration and online fraction, not irreversible catalyst lifetime.
- Unknown Pt loading in P06: 0.3 wt% central, 0.1–1.0 wt% sensitivity. Known 3 wt% Pt in P02/P05 was used as printed.

## 2. Plant model

### 2.1 Reference plant and costing equations

A 750,000 t/y polymer-grade-propylene plant operating 8,500 h/y was used, close to Enterprise's 1.65 billion lb/y PDH scale. The industrial material benchmark is 1.12 t propane/t propylene, corresponding to an effective molar selectivity/yield of about 93.6% after recovery losses.

For each literature record, the lab conversion was **not** imposed on the plant. A first-order approach-to-equilibrium PFR model was fitted to the measured lab conversion and converted-propane rate:

`W/F = -(Xeq/k) ln(1 - X/Xeq)`

Equilibrium is represented by `Kp(600 °C)=0.299` and a 124.3 kJ/mol van't Hoff slope. Lab dilution and reported H2 were included in the equilibrium calculation; the plant reactor feed was modeled as propane after product/H2 separation. The plant then optimized per-pass conversion from 5% to 95% of equilibrium. Increasing conversion reduces recycle but increases catalyst inventory near equilibrium.

Fresh propane consumption is `1.048/S` t/t propylene. Circulation-sensitive capital and energy scale with reactor feed per tonne product. Total installed capital is split 25% fixed, 60% circulation/separation and 15% reactor; variable blocks scale to the 0.60 power. Annual capital charge is 10% capital recovery plus 4% fixed O&M.

Catalyst inventory follows modeled plant productivity. Catalyst annual cost includes $20/kg fabrication/support, element values, three-year replacement, 90% Pt recovery and financing of retained Pt. Regeneration uses the disclosed time to 10% activity loss, a 1 h regeneration, and $0.05/kg-catalyst-cycle. These are explicit assumptions, not claims about a commercial regeneration design.

### 2.2 Parameter and source table

| Parameter | Central value | Range / status | Source or rationale |
|---|---:|---:|---|
| Capacity | 750,000 t/y | 650–800 kt/y | Enterprise PDH plants report 1.65 billion lb/y PGP capacity (~748 kt/y): Enterprise 2023 10-K / PDH2 disclosure, https://www.sec.gov/Archives/edgar/data/1061219/000106121924000006/epd-20231231.htm |
| Total installed capital | $1.40 bn | $1.0–2.0 bn | US EPA statement-of-basis records an estimated $1.4 bn for the Enterprise PDH unit: https://archive.epa.gov/region6/6pd/air/pd-r/ghg/web/pdf/enterprise-propane-sob03072014.pdf |
| Propane use, reference | 1.12 t/t propylene | industrial benchmark | Clariant CATOFIN material cites below 1.12 t/t; used as an effective yield benchmark: https://www.clariant.com/en/Business-Units/Catalysts/Petrochemical-and-Refining-Catalysts/CATOFIN-and-CATADIENE |
| Propane price | $394/t | $300–500/t | Constructed planning value (~$0.755/gal at 4.23 lb/gal) within EIA Mont Belvieu series; not a contracted plant price: https://www.eia.gov/dnav/pet/hist/LeafHandler.ashx?n=PET&s=EER_EPLLPA_PF4_Y35MB_DPG&f=M |
| Natural gas | $4.96/GJ | $3.5–8/GJ | Planning value based on EIA U.S. industrial-gas series: https://www.eia.gov/dnav/ng/ng_pri_sum_dcu_nus_m.htm |
| Industrial electricity | $0.0862/kWh | $0.06–0.12 | EIA industrial retail-price data: https://www.eia.gov/electricity/monthly/ |
| Thermal demand | 13.3 GJ/t propylene | 8–18 | **Assumption**, calibrated from 11.84 GJ/t propane process-energy figures and 1.12 t/t propane. Electricity is separately 100 kWh/t (75–300 sensitivity conceptually). |
| Hydrogen credit | $1.15/kg recovered H2; 90% recovery | $0.5–1.74/kg | **Discounted assumption** versus DOE natural-gas-reforming production-cost estimates; avoids crediting full merchant price: https://www.energy.gov/eere/fuelcells/hydrogen-production-natural-gas-reforming |
| Operating time | 8,500 h/y | 8,000–8,760 | **Assumption**, world-scale continuous plant with outages. |
| Annualisation | 10% CRF + 4% fixed O&M | 8–14% + 3–6% | **Assumption**. |
| Reference catalyst annual expense | $5.42m/y | $2–15m/y | **Assumption/calibration** from a reported £4.17m/y catalyst-replacement line converted at $1.30/£; not used to rank literature records. |
| Pt | $30,500/kg | $20,000–50,000 | Planning value near $950/oz; range anchored to USGS platinum-group-metal statistics: https://pubs.usgs.gov/periodicals/mcs2026/ |
| Ga / Co / base metals | $400/kg Ga; $30/kg Co; Fe $0.15, P $4, Zn $3, Pb $2.2, Sn $30, K $1 per kg | broad commodity ranges | Planning assumptions anchored to USGS 2026 commodity summaries; catalyst-grade procurement may be higher: https://pubs.usgs.gov/periodicals/mcs2026/ |
| Reaction enthalpy | 124.3 kJ/mol | 120–128 | Thermochemical value consistent with NIST gas-phase formation enthalpies: https://webbook.nist.gov/chemistry/ |
| Catalyst life / Pt recovery | 3 y / 90% | 1–5 y / 80–98% | **Assumption**; irreversible lifetime was not supplied by the papers. |
| Regeneration | 1 h, $0.05/kg-cycle | 0.5–2 h; $0.01–0.20 | **Assumption**; used only as an order-of-magnitude cyclic-deactivation penalty. |

### 2.3 Reference check

The reference model gives **$736.7/t propylene**: feed $441.2, energy $74.6, capital/fixed O&M $261.3, catalyst $7.2, regeneration $2.0, and H2 credit −$49.6. Feed is 59.9% of net cost. This is consistent in order of magnitude with open PDH techno-economic studies and with the common finding that propane feed contributes roughly 60% of cost. It is a screening model, not a bankable estimate; regional propane/propylene contracts and the financing structure can move the answer materially.

## 3a. Plant cost of costable records

All values are USD per tonne propylene unless otherwise labeled. “Catalyst” and “regen” columns are annual catalyst and regeneration contributions. Costs for the 32 unrevealed-selectivity records are deliberately left unknown.

{ct}

**Lowest five:** PDH-015 $658.2/t; PDH-017 $660.0/t; PDH-016 $666.5/t; PDH-059 $671.2/t; PDH-036 $672.9/t. The winner's margin over PDH-017 is only $1.8/t, so those two are economically tied at this model's precision.

## 3b. Paper ranking versus plant ranking

{rtt}

Denominator: six same-paper/same-pressure/same-feed groups × two requested lab metrics = **12 comparisons**. Agreement is 8/12. If converted-reactant rate is added as a third metric, agreement is 12/18 and disagreement 6/18; the qualitative conclusion is unchanged.

The very large P01 regrets are real consequences of the disclosed selectivities in the database: its conversion leader PDH-009 has only 12% selectivity and its rate/productivity leader PDH-003 has 20%, whereas the plant-cost winner within P01, PDH-010, has 77%. Ranking on conversion or converted-propane rate therefore rewards propane destruction.

## 3c. Bottleneck and attribution

### Reference cost breakdown

| Item | $/t propylene | Share of net cost |
|---|---:|---:|
| Fresh propane | 441.2 | 59.9% |
| Annualised capital + fixed O&M | 261.3 | 35.5% |
| Energy | 74.6 | 10.1% |
| Catalyst | 7.2 | 1.0% |
| Regeneration | 2.0 | 0.3% |
| H2 credit | −49.6 | −6.7% |
| **Net** | **736.7** | **100%** |

### One-at-a-time levers at the reference

- +1 percentage point selectivity: **−$4.66/t**.
- 2× activity: **−$17.95/t**, mainly by shrinking the modeled reactor block and inventory.
- 10× coke-cycle stability: **−$1.80/t** under the central regeneration assumptions.
- +$10/t propane: **+$11.20/t propylene**.

Thus, at a mature reference catalyst, a large activity doubling has more value than one selectivity point, but **feedstock price and selectivity carry the total cost**. Across the literature gaps, selectivity is dominant in 22/27 records; activity is dominant in four low-rate records; temperature/equilibrium is dominant in one. Metal cost does not dominate any record.

The full one-at-a-time attribution for every costed record is saved in `analysis_attribution.csv`. Important examples:

- PDH-009 gap to reference: +$5,538/t; setting only selectivity to the reference removes $5,163/t.
- PDH-003: +$2,444/t; selectivity term $2,333/t.
- PDH-010: +$608/t; selectivity term $193/t and 2× activity saves $181/t.
- PDH-018: +$63/t; it is already more selective than reference, but 2× activity saves $47.7/t and 10× stability saves $37.0/t.
- PDH-015: −$78.5/t versus reference; its selectivity advantage is worth $32.5/t and its high activity/compact reactor supplies the rest.

## 3d. Backward design

Records already below the reference need no improvement in this deterministic screen. For records above the reference, the one-at-a-time requirement is:

{bt}

Interpretation:
- PDH-018 can reach the reference with about **2.73× activity**; selectivity alone cannot do it because it is already 96% selective and remains burdened by rate/stability/capital.
- PDH-026 can reach with **98.27% selectivity** or **3.11× activity**.
- PDH-042 can reach with **90.55% selectivity** or **2.91× activity**.
- PDH-044 can reach with **91.27% selectivity** or **1.60× activity**.
- The low-selectivity P01 records cannot reach the reference by changing only selectivity, only activity up to 10,000×, or eliminating metal cost; they need simultaneous gains and/or a different process configuration.
- Catalyst metal price alone does not rescue any above-reference catalyst, confirming that metal purchase is not the industrial bottleneck under recovery.

## 3e. Sensitivity

{stt}

PDH-015 remains the winner in all listed one-at-a-time scenarios, but its margin over PDH-017 is only $1.3–2.4/t. The **identity of the top pair is robust; their order is not practically significant**. Propane price moves the reference cost by over $220/t across the tested range, much more than catalyst-metal or regeneration assumptions. The P06 Pt-loading sensitivity does not affect the winner because PDH-015 has a reported 3 wt% Pt loading; it does affect P06 catalyst costs, but not enough to change the top five.

## 4. What the masked data cannot support

1. **No global winner across all 59 records:** 32 selectivities remain masked. Any one of them could combine high selectivity with adequate activity and beat PDH-015.
2. **No bankable lifetime claim:** time-on-stream tests describe short deactivation and often coke accumulation, not multi-year mechanical/chemical life through thousands of regenerations.
3. **No scale-up guarantee:** heat transfer, pellet diffusion, pressure drop, impurities, propylene separation and regenerability are not represented by powder-scale rates.
4. **No firm P06 metal bill:** Pt wt% is missing. The 0.1–1 wt% sensitivity did not change the central winner, but it prevents a precise inventory value for P06.
5. **No by-product credit beyond H2:** methane/ethane/coke were assigned zero credit. Fuel-gas use could modestly lower cost, but low selectivity would still be strongly penalized because propylene yield is lost.

## 5. Decision

**Screening decision:** choose **PDH-015** if forced to choose from the revealed literature data, with PDH-017 as an economically indistinguishable backup and PDH-059 as the most credible long-duration candidate because it reports ~100 h to 10% loss over a 336 h test. Before a plant decision, require cyclic regeneration testing, impurity tolerance, shaped-pellet productivity and at least thousands of hours of cumulative operation. A risk-adjusted owner could rationally retain the commercial reference until those data exist.

**Bottleneck decision:** PDH economics are feedstock/selectivity-led. Research should prioritize propylene selectivity and retained yield under cyclic operation; activity matters when it is low enough to enlarge reactor/catalyst inventory, while precious-metal price is secondary after recovery.

## 6. Reproducibility and files

- `scripts/pdh_analysis.py` — equilibrium/kinetic fit, optimization, costing, attribution, backward design and sensitivity.
- `analysis_record_costs.csv` — all 27 costable records.
- `analysis_rankings.csv` — groupwise lab-versus-plant ranking.
- `analysis_attribution.csv` — record-level one-at-a-time attribution.
- `analysis_backward.csv` — backward-design requirements.
- `analysis_sensitivity.csv` — one-at-a-time scenarios.
- `db/visible.csv`, `db/revealed.csv` — source database views.

## 7. Run time and cost

From `ledger.json` read near completion: **7.5 wall-minutes** and **$3.04 USD-equivalent model cost** at that read. Final file-writing overhead occurred after the read, so these are slightly conservative.
'''
open('report.md','w',encoding='utf-8').write(text)
print('wrote',len(text),'chars; cost rows',len(costtbl))