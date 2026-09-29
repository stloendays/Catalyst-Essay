# Model validation and scope matrix — 2026-09-29

This note separates **validation**, **plausibility checks**, and **declared model scope**. It does not treat agreement with a literature trend as validation of absolute production cost.

| Layer | External/internal anchor | Current model result | Status | What is supported | What is not supported |
|---|---|---|---|---|---|
| Descriptor / volcano concept | Nørskov et al., J. Catal. 197 (2001) 229–231, DOI 10.1006/jcat.2000.3087 | N adsorption descriptor produces a volcano-shaped activity relation | qualitative external validation | use of N binding / BEP-type scaling as an activity descriptor | absolute TOF calibration |
| Step-site dataset and conditions | Wang & Abild-Pedersen, PNAS 118 (2021) e2106527118, DOI 10.1073/pnas.2106527118 | source workbook is derived from Dataset S1; atomic reference is 673 K, pN2=24.5 bar, pH2=74.25 bar, pNH3=1 bar | source-level match | same literature dataset family, step-site scaling logic and reference conditions | exact reproduction of the authors' CatMAP / absolute rates |
| Leading transition metals | Wang 2021 and prior volcano literature place Ru/Os/Fe near the high-activity region | reduced MKM gives Ru > Os > Fe | ranking-level consistency | headline intrinsic top-three is literature-consistent | universal ranking for promoted/support-dependent catalysts |
| Industrial Fe operating envelope | reviews describe conventional Fe Haber–Bosch near 400–500 C and roughly 150–300 bar | Fe optimum 425 C / 180 bar | plausibility PASS | Fe optimum lies inside a realistic industrial window | calibration of conversion, heat integration or full loop design |
| Ru industrial interpretation | reviews describe promoted Ru as more active and capable of lower-temperature/lower-pressure operation, while high Ru cost limits adoption | pure-metal reduced model gives Ru optimum 450 C / 425 bar at canonical Ru price, shifting to 425 C / 170 bar when Ru price is equalized to Fe | model-specific / causal diagnostic | the optimum responds strongly to inventory economics and reoptimization | the canonical pure-Ru optimum is not presented as a prediction of a commercial promoted-Ru process |
| Cost boundary | FINAL-1.1 explicitly includes catalyst inventory, reactor proxy, pressure-vessel premium, compression/refrigeration electricity and compressor CAPEX; other plant-wide pools are outside scope | Fe/Ru/Os = 15.292/22.031/25.832 USD/t NH3 | internally audited reduced objective | candidate-dependent economic ranking inside the declared boundary | total levelized ammonia production cost |
| Engineering cost model form | FINAL-1.1 closure perturbations: compressor capacity convention, CEPCI/CRF/vessel sensitivities | ranking, inversion and reachability verdict remain unchanged under the recorded 10–25% perturbations | internal robustness PASS | decision sign is not driven by one pressure-CAPEX convention | model discrepancy is not eliminated |
| Backward reachability | canonical strict-scaling anchor reproduced before lifecycle extension | 21.397873 USD/t at E_N=-1.215 eV; tested lifecycle box remains 0.07078 USD/t above Fe at its best corner | regression + reachability PASS | backward target and strict-scaling reachability are numerically separated | physical realizability beyond the chosen scaling family |

## Literature anchors used here

1. J. K. Nørskov et al., *The Brønsted–Evans–Polanyi Relation and the Volcano Plot for Ammonia Synthesis over Transition Metal Catalysts*, Journal of Catalysis 197 (2001) 229–231. DOI: **10.1006/jcat.2000.3087**.
2. Tao Wang and Frank Abild-Pedersen, *Achieving industrial ammonia synthesis rates at near-ambient conditions through modified scaling relations on a confined dual site*, PNAS 118 (2021) e2106527118. DOI: **10.1073/pnas.2106527118**.
3. *Facilitating green ammonia manufacture under milder conditions: what do heterogeneous catalyst formulations have to offer?*, Chemical Science (2022). DOI: **10.1039/D1SC04734E**.

## Manuscript wording lock

Use **"catalyst-dependent cost objective"**, **"reduced process–economics boundary"**, or equivalent where numerical NH3 costs are quoted. Do not describe the 15–26 USD/t values as total ammonia production cost.

The correct validation claim is: **the atomistic trend and Fe operating point are externally plausible, while the numerical cost ranking and backward target are internally audited within a deliberately reduced catalyst-dependent process–economics model.**
