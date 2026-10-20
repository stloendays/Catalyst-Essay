# Strict catalyst identity (`material_key_strict.csv`): notes (2026-10-19)

Built by `build_material_key_strict.py`, without reference to any leader, cost or regret. From
`pooled_candidates.csv` only `group, doi, catalyst, catalyst_key, T_C` were read, plus `cost_recycled_opt_inlet` as
a finite/non-finite mask to fix the scope. Identity comes from the sample names, the locator text, the extraction
records (`agent/extraction/out/raw*`, `analysis/validation_meoh_prospective_2026_10_13/out/raw*`) and the paper and SI
texts.

Scope: 64 groups with at least two distinct `catalyst_key` among costed entries; 286 (group, catalyst_key) rows.

Rule applied (RULES.md §1, strict). Samples that share composition (elements and ratios, promoters and dopants
included), loading and support (identity and crystal phase as the authors report it) share a key, even when they
differ in route, precursor or precipitant, calcination or carburization temperature, or morphology. A changed additive
identity counts as a composition or support difference. Examples: graphite, activated carbon and CNT in
`cza-0.1gc/ac/cnt`, porous PDVB in `czam-ldh+p-pdvb`, and BN vs CNT. Measured loadings that differ also keep samples
apart: `cat-1.5…6.0` are 9.8/12.3/16.4/6.2 wt% In2O3, and `cza-1…5` are Cu+ZnO 9.9–55.3 wt%.

## Synthesis-only sets (19 group-level sets in 18 groups; 12 groups collapse to one strict catalyst)

| Paper | Groups | Shared key | Members | Evidence |
|---|---|---|---|---|
| 10.1021/acscatal.6c02907 | 8 (1, 2.5, 5, 10 bar; 20 bar at 7.5/15/22.2/30 NL/g/h) | CuZn-70:30 | `cuzn-nh4hco3`, `cuzn-naoh-0.25/0.5/1.0`, `cuzn-nh4oh-0.25` (those present in each group) | Paper "Cu/ZnO Synthesis" and Experimental: every sample has Cu:Zn 70:30 molar; X = precipitant, Y = addition rate. XPS Na 1s finds no residual Na. **All 8 groups collapse.** |
| 10.1021/acs.iecr.7b01464 | 1 | CuZnAl-58:25:17 | `cza200/300/400` | Same Cu:Zn:Al 58:25:17; only the ball-milling speed differs. **Collapses.** |
| 10.1016/j.jes.2023.05.010 | 1 (18 NL/g/h) | 1wt%Au/cubic-In2O3 | `au/in2o3-hm/np/ns` | Au 1.03/1.01/1.02 wt% (ICP-MS). All supports are cubic In2O3 (Sec. 2.1 XRD); only the morphology differs. **Collapses.** |
| 10.1016/j.jes.2023.05.010 | 1 (18000 h-1) | cubic-In2O3 | `in2o3-hm/np/ns` | As above. **Collapses.** |
| 10.1038/s41467-019-11349-9 | 1 | 0.75Pd-In2O3 | `pd-in2o3cp`, `cp` | Not a synthesis difference: `cp` ("Fig. 6 … Pd–In2O3 CP stability, start") is the same 0.75 wt% Pd–In2O3 CP sample under a shortened name. **Collapses.** |
| 10.1016/j.fuel.2024.131111 | 1 | 5In-InNi3C0.5/Fe3O4 | `5inni3c0.5/fe3o4-x/y` for 300/425, 350/425, 450/425, 500/425, 400/375, 400/400, 400/450, 400/475 | 5 wt% In, In/Ni 1/3, Fe3O4; only the calcination/carburization temperatures differ. Fe3O4 stays pure phase (Sec. 3.3.1, Fig. 4). 400/500 is kept separate (see below). |
| 10.1016/j.jcat.2016.03.017 | 1 | 1wt%Pd/ZnO | `1%pd,si`, `1%pd,im` | 1 wt% Pd/ZnO by sol immobilisation vs impregnation (Table 4). |
| 10.1016/j.jcat.2016.03.017 | same | 5wt%Pd/ZnO | `5%pd,si`, `5%pd,im`, `5%pd/znosi`, `5%pd/znoim` | 5 wt% Pd/ZnO; route (Table 4) and heat-treatment variants (Tables 5, 6). |
| 10.1039/c6ra28305e | 1 | CuO-ZrO2-amorphous | `cz-350`, `cz-450` | (CuO)0.5(ZrO2)0.5, ~31.5 wt% Cu; ZrO2 amorphous in both (Fig. 1 XRD, Raman). |
| 10.1038/s41467-025-65929-z | 1 (40 bar) | NiInC2.5/Al2O3-45 | `pfcp-niincal`, `ldh-niincal` | SI synthesis: both RNi/In = 2.5 with an Al2O3 support of 45 wt%; parallel-flow vs LDH coprecipitation. (The extraction record's "33 wt% Ni default" for LDH-NiInCAl is superseded by the SI.) |
| 10.1038/s41565-026-02135-y | 1 | 2In2O3/m-HfO2 | `2inhfox`, `in2o3/hfo2(fsp),wi`, `in2o3/hfo2(p),wi`, `inhfox,cp` | Section "Synthesis-dependent reducibility": all 2 wt% In2O3 on HfO2 that is predominantly monoclinic in every reference (Ext. Data Fig. 3). The authors present the set as a synthesis comparison. |
| 10.1126/sciadv.aea7041 | 1 | In2O3:CNT-1:2 | `in2o3-cnt(1:2)`, `in2o3@cnt-h(1:2)`, `in2o3@cnt-ui(1:2)` | SI Table S5 and Figs. S4–S5: all In2O3:CNT 1:2 by mass, assembled by different routes. The main-text methods are not in the local corpus (the fetched "main" PDF is the SI). The assembly route only affects synthesis, so the merge stands. |

## Uncertain cases (8 rows, kept distinct, `uncertain = 1`)

1. **Support phase changed by a synthesis variable only.** The rule lists both "support crystal phase" (item 3)
   and "calcination temperature" (item 4) for these samples. Each is kept distinct on the authors' reported
   support phase.
   - `cz-550` (t-ZrO2) and `cz-650` (t+m-ZrO2) vs the amorphous `cz-350/450` set (10.1039/c6ra28305e, Fig. 1).
     Treated as synthesis-only, this group would also collapse to one catalyst.
   - `cu/zro2(ii)–(v)` (10.1021/cs500979c): all 10 atom% Cu, with t-ZrO2 fractions of 33/71/100/15 %. The ZrO2
     polymorph is the variable the paper studies (title, Table 1). `cu/zro2(i)` differs in loading (15 atom%) and
     is not flagged. Treated as synthesis-only, (ii)–(v) would form one set; the group would keep (i), (ii–v) and
     bare ZrO2.
   - `5inni3c0.5/fe3o4-400/500` (10.1016/j.fuel.2024.131111): carburization at 500 °C over-reduces part of the
     Fe3O4 to Fe/FeCx (Sec. 3.3.1). Treated as synthesis-only, it would join the 5In-InNi3C0.5/Fe3O4 set.
2. **Loading not reported.** `cu-ga2o3` (10.1021/acscatal.6c03987, 14 bar group): colloidal γ-Ga2O3 deposited on
   Cu–Mg–Al HT with "comparable metal loadings". The Ga loading is not given (SI §1.1.2, Table S1 covers CuMe only),
   so a match with `cuga1.5` or `cuga2.5` cannot be decided.

## Other judgements recorded

- Different supports or support phases chosen by the authors stay distinct, for example m-, t- and a-ZrO2 in
  10.1126/sciadv.abi6012 and In2O3/m-ZrO2 vs t-ZrO2 in 10.1021/acscatal.9b03305.
- `5in2o3-95zro2` (coprecipitated, 3.6 mol% In measured) and `in2o3/m-zro2` (5 wt% In2O3, about 4.4 mol% In,
  impregnated on m-ZrO2) differ in loading and support phase, so they are distinct.
- `cat-4.5` (16.4 wt% hexagonal In2O3) and `in2o3-iwi/al2o3/al-fiber` (14.6 wt% cubic In2O3) differ in loading,
  so they are distinct.
- The scope filter gives 148 groups with at least one costed entry, of which 64 have two or more keys. This matches
  the expected 64.
