# External process/economic validation and top-journal benchmark — 2026-09-30

This note distinguishes **external support for model structure** from **validation of numerical predictions**. It does not replace the frozen NH3-FINAL-1.1 source of truth.

## 1. Independent ammonia process/economic comparators

### Smith, Hill & Torrente-Murciano, Energy & Environmental Science 2020
DOI: 10.1039/C9EE02873K

Reported process facts relevant to the present model:
- conventional promoted-Fe Haber–Bosch operation is above 400 °C and around 150 bar;
- ammonia separation, recycle and feed/recycle compression are strongly pressure-coupled;
- lowering synthesis pressure with more active Ru catalysts does not automatically lower system cost when condensation remains the separation method because low single-pass conversion can increase recycle/compression burden.

**Supports:** the present treatment of pressure, recycle, compression and separation as catalyst-dependent downstream variables; plausibility of the Fe optimum at 425 °C / 180 bar.

**Does not support:** the present pure-Ru optimum at 450 °C / 425 bar, or the exact Fe/Ru cost difference.

### Yoshida et al., International Journal of Hydrogen Energy 2021
DOI: 10.1016/j.ijhydene.2020.12.081

Aspen Plus loops with explicit Fe and Ru/C kinetics were compared from 0.1 to 500 t NH3/day. Their reported preferred configurations change with scale:
- Fe at 150 bar is least costly at their largest studied scale;
- Ru/C at 50 bar is favored around 100 t/day;
- Ru/C at 100 bar is favored at still smaller scale;
- catalyst price is not the dominant loop cost at every scale.

**Supports:** catalyst identity and economics cannot be separated from process scale/configuration; Fe-versus-Ru ordering is not universal.

**Does not support:** direct numerical comparison to the present 1000 t/day reduced catalyst-dependent objective, because scale, supported-catalyst kinetics, flowsheet and cost boundary differ.

### Skubic et al., Journal of Catalysis 2024
DOI: 10.1016/j.jcat.2023.115217

The review identifies multiscale linkage—from atomistic energetics and microkinetics to reactor/process models—as an important unresolved modelling challenge in ammonia catalysis.

**Supports:** the manuscript's problem statement and modular multiscale framing.

**Does not validate:** any specific ranking, cost, parity target or Agent result.

## 2. Top-journal rhetorical benchmark

### Van Allsburg et al., Nature Catalysis 2022
DOI: 10.1038/s41929-022-00759-6

CatCost is not a scientific analogue of the present ammonia model, but its **evidence architecture** is useful:
1. identify an early-stage screening quantity that is routinely ignored or misused;
2. quantify the missing economic layer;
3. show how scale and catalyst lifetime change the apparent ranking;
4. normalize the result to the downstream product/decision rather than catalyst price alone;
5. end with a concrete catalyst-selection implication.

The present manuscript should emulate that rhetorical sequence without copying wording:

```
atomistic ranking
    -> downstream process/economic propagation
    -> decision consequence (regret)
    -> causal localization of the inversion
    -> backward target
    -> physical reachability
```

This is stronger than presenting the work as a long multiscale workflow.

## 3. Reader-facing wording lock

Use:
- **"the external literature supports the catalyst–process coupling structure"**
- **"the Fe operating point lies within the conventional industrial range"**
- **"published Fe/Ru comparisons show that the preferred catalyst changes with scale and process configuration"**

Do not write:
- "the literature validates our Ru optimum";
- "Fe is universally more economic than Ru";
- "the reduced 15–26 USD/t objective is the total cost of ammonia";
- "agreement with one process paper validates the full multiscale model".

## 4. Current interpretation

The strongest externally defensible claim is:

> Published ammonia-process studies independently show that catalyst identity can change the preferred pressure, recycle/separation burden and economic optimum. The present work extends that principle from selected Fe/Ru process comparisons to a candidate-ranking question and explicitly localizes where an atomistic ranking first changes.

