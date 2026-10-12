# Packed-bed pressure-drop validation layer: source-gated Ergun model

**STATUS: Implementation and numerical unit tests, NOT independently validated packed-bed feasibility.**

The upstream methanol TEA `meoh_general_model` assumes a **fixed 1.5 bar** recycle-loop pressure loss even as reactor size and gas throughput change. This can understate the compressor and vessel impact of a highly recycled/large bed. The Ergun equation provides a transparent first-pass screen when independent physical design inputs are available.

## Equation and units

The model uses the standard packed-bed Ergun form:

```
-dP/dz = [150 mu (1-eps)^2/(eps^3 (phi dp)^2)] u
       + [1.75 rho (1-eps)/(eps^3 phi dp)] u^2
```

Here `u` is **superficial actual gas velocity** in m/s through the free bed cross-sectional area (not interstitial velocity), `mu` is Pa s, `rho` is kg/m³, `dp` is m, `phi` is particle sphericity and `eps` is bed voidage. Gas pressure input is bar, converted internally to Pa. Total gas molar flow is kmol/h divided evenly among explicitly supplied parallel beds.

For **isothermal gas, constant mean molecular weight, viscosity and Z** (but compressible with pressure), `u ~ 1/P`, `rho ~ P`, and the integration yields

```
Pout^2 = Pin^2 - 2 * Pin * (Ergun_dPdz_at_inlet) * L .
```

This is more appropriate at non-negligible pressure losses than simply multiplying the inlet-pressure gradient by the bed length. If `Pout^2<=0`, the simple isothermal model has no positive outlet pressure: stop rather than invent a feasible bed.

The supported source-input fields are bed geometry (n, length, cross-section), catalyst particle size and sphericity, void fraction, bulk packing density, gas T/P, actual inlet flow, viscosity, mixture MW, compressibility Z and an independently specified allowable pressure drop and catalyst loading. **Any null input blocks the physical validation**.

Catalyst capacity is checked separately as `n * (pi D²/4) * L * bulk_density`. Avoid using this to claim industrial throughput without measured conditions. The model does not use a 'typical' pellet size or generic gas viscosity as evidence.

## Connection to source methanol TEA

`ergun_screen.recost_recycle_from_dP(original_G.cost_state, P, deltaP)` transparently replaces ONLY the energy usage and installed cost term of the recycle compressor. The exact previous `G.cost` is recovered when `deltaP=1.5 bar`; this is a CI regression test.

The replacement has **major known limitations**: outlet fugacities, CO2/CO equilibrium, reaction extent, hot/cold pressure profile and reactor hydraulics are not coupled back to the new pressure. Therefore, this is a **one-way marginal compressor-cost diagnostic**, not a new final jointly optimized TEA ranking. Do not report resulting numerical ranking changes unless independent reactor geometry/gas conditions have been sourced and full reactor-pressure coupling has been added.

## Original data availability

- Campos et al. (2022), `Processes` **10** 1535, DOI: [10.3390/pr10081535](https://doi.org/10.3390/pr10081535), specifies a one-step plant with six parallel reactor modules and a 2% purge in its detailed flowsheet.
- The **six-module** count is known; source-independent physical bed length, cross section, pellet size, porosity, actual gas thermophysical properties and vessel allowable pressure drop are NOT demonstrated in the existing printed methanol literature comparison dataset.
- The existing 1.5-bar model value is a **fixed process modelling assumption**, not an independent measurement or acceptable vessel design threshold.
- Blank requirements are in `bed_input_requirements.json`. No physical feasibility status is claimed until these fields are measured or traceably supplied.

## Commands

```bash
pip install -r requirements.txt
python -m unittest discover -s analysis/meoh_hydraulic_2026_10_12/tests -v
python analysis/meoh_hydraulic_2026_10_12/ergun_screen.py \
  --input analysis/meoh_hydraulic_2026_10_12/bed_input_requirements.json \
  --output analysis/meoh_hydraulic_2026_10_12/results/bed_input_audit.json
```

This gives a **BLOCKED** result listing the physical inputs still missing. This is deliberate: filling hypothetical dimensions just to obtain plausible-looking industrial pressure-drop numbers would not strengthen the paper.

With independently sourced complete inputs, add `--require-complete` and replace the JSON input path with a versioned validated geometry file, then inspect separate hydraulic and catalyst bed capacity decisions. Sources should identify catalyst pellets (lab powder vs formed plant pellets) and real module geometry.

## Research next steps

1. Collect geometry, particle size/shape, porosity/bulk density, gas viscosity/MW/Z and a verified allowable reactor deltaP for **each candidate** (cannot silently transfer the same powder/pellet parameters to unrelated formulations).
2. Validate Ergun-predicted pressure loss against at least one reported/reference reactor under measured flow.
3. Couple variable pressure through reactor kinetics/thermodynamics and recalculate true `argmin_(m,p)` under the hydraulic mask before making any industrial-scale ranking claim.
4. Keep the published methanol and ammonia frozen results unchanged in the meantime.

**This is an auditable calculation tool and engineering evidence gate, not claimed successful physical scale-up validation.**
