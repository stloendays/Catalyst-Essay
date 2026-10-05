# Promoted, support-modified and confined Ru: measured activity gains (Fig. 3a strip)

`promoted_confined_ru_enhancement.csv` — 35 data points from 25 sources: catalyst, reference catalyst measured in the
same study, enhancement factor, metric (turnover frequency per surface site, or rate per mass), site-counting method,
temperature, pressure, H₂:N₂, DOI, table/figure location, a short quote and the verification level (full text read
for all plotted points). `fig3_literature_points.csv` — the nine points drawn in Fig. 3a. PDFs were retrieved through
the NUS library and are not redistributed.

## Reading the factors against the model

The model's α multiplies the turnover frequency of an unpromoted Ru step site. A factor for promoted versus
unpromoted Ru on the same support is therefore like-for-like; a factor measured against an already promoted reference
(Cs–Ru/MgO) is a lower bound relative to unpromoted Ru.

| class | strongest like-for-like factor | basis | conditions | source |
|---|---:|---|---|---|
| alkaline-earth promoter | Ba–Ru/C 75× | TOF per surface Ru | 300 °C, 0.3 MPa | Siporin et al., Catal. Lett. 93, 61 (2004), 10.1023/B:CATL.0000016950.09677.4d |
| alkaline-earth promoter | Ba–Ru/BN >100× | per g at equal Ru | 400 °C, 5 MPa | Hansen et al., Science 294, 1508 (2001), 10.1126/science.1064399 |
| alkali promoter | Cs–Ru/C 65× | TOF per surface Ru | 300 °C, 0.3 MPa | Siporin et al. (2004) |
| alkali promoter | Cs–Ru/MgO >134× (350 °C) | per g at matched Ru | 0.1 MPa | Larichev et al., J. Phys. Chem. C (2007), 10.1021/jp066970b |
| alkali promoter | Cs–Ru/YSZ ~10× | per g Ru | 450 °C, ≤ 1.1 MPa | ACS Sustain. Chem. Eng. (2019), 10.1021/acssuschemeng.9b04929 |
| electride support | Ru/C12A7:e⁻ 9.8× | TOF (CO count) | 400 °C, 1 MPa | Kitano et al., Nat. Chem. 4, 934 (2012), 10.1038/nchem.1476 |
| oxyhydride support | Ru/BaTiO₂.₅H₀.₅ 8.4× | TOF | 400 °C, 5 MPa | Tang et al., Adv. Energy Mater. (2018), 10.1002/aenm.201801772 |
| amide support | Ru/Ba–Ca(NH₂)₂ ≥ 33.5× vs Cs–Ru/MgO | TOF (STEM count) | 300 °C, 0.9 MPa | Kitano et al., Angew. Chem. Int. Ed. (2018), 10.1002/anie.201712398 |
| confinement | Ru inside CNT 0.5× | TOF | 400 °C, 1–4 MPa | Chem. Eur. J. (2010), 10.1002/chem.200902371 |

- Alkali and alkaline-earth promotion is the only measured strategy that reaches the 70.78–462× parity band against an
  unpromoted reference; electride, hydride and amide supports give about 10–34× (more against Cs–Ru/MgO); confinement
  inside carbon nanotubes lowers activity.
- Factors at 250–300 °C are larger than at 400–450 °C because the unpromoted reference is hydrogen-poisoned at low
  temperature; the 5 MPa Ba–Ru/BN result shows the promoter effect persists at elevated pressure.
- Points whose large factors come from site counting or a weak reference (H₂-counted amide 197×, CO-counted Ba-covered
  surfaces, acidic Al₂O₃ references, terrace references) are in the CSV but are not plotted as intrinsic gains.
- Commercial Ru catalysts (KAAP) are Ba/Cs/K-promoted Ru on graphitic carbon. The Fig. 2d actual-cost calculation
  credits only dispersion and recovery, not the promoter gain.
