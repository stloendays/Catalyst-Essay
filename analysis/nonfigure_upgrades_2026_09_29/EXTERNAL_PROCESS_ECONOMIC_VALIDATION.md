# Independent process/economic validation — 2026-09-30

This note compares the manuscript's **qualitative process/economic mechanism** with external ammonia-process literature. It does not calibrate the reduced NH3 objective to plant-wide LCOA.

## Independent literature anchors

| Question | External evidence | Relation to current result | Validation status |
|---|---|---|---|
| Is the Fe optimum in a realistic industrial window? | Conventional Fe Haber-Bosch is commonly reported around 400–500 C and roughly 130–300 bar, depending on plant and review. | FINAL-1.1 Fe optimum = **425 C / 180 bar**. | **Plausibility PASS** |
| Can Ru enable lower-pressure operation? | Reviews and KAAP literature describe promoted Ru catalysts as enabling lower-pressure synthesis than conventional Fe systems. | Our **pure-metal reduced model** is not calibrated to commercial promoted Ru and therefore does not use its canonical Ru optimum as an external validation target. | **Scope-consistent, not a calibration target** |
| Is high Ru activity sufficient for lower cost? | Yoshida, Ogawa & Ishihara (Cleaner Chemical Engineering, 2024) find that high-activity Ru catalysts can reduce reactant-gas compression, while ammonia-separation refrigeration and expensive Ru can offset that gain; catalyst lifetime and recycling become important economic variables. | This independently supports our central mechanism that **catalyst activity, separation/compression and lifecycle economics must be propagated together** rather than evaluated by activity alone. | **Mechanism-level external support** |
| Does pressure remain an important process variable after catalyst improvement? | Low-pressure vs high-pressure Haber-Bosch TEA studies report that pressure changes compression/energy requirements and can alter overall economics, while the net result depends on the complete process configuration. | FINAL-1.1 identifies loop pressure as a major reoptimization variable and shows that changing Ru price changes the preferred pressure regime. | **Process-coupling support** |
| Are Ru price, availability and lifetime recognized industrial constraints? | Recent Ru-catalyst reviews emphasize Ru scarcity/high price and the importance of lowering Ru loading, extending lifetime or recycling. | Our first inversion occurs when catalyst demand is monetized through metal price/replacement economics; backward design identifies lifetime/recovery as high-leverage co-targets. | **Mechanism-level external support** |
| Are the manuscript's 15–26 USD/t values comparable with total ammonia production cost? | Plant-wide TEA includes upstream H2/N2 production, utilities, storage and broader balance-of-plant costs; reported total ammonia costs are hundreds of USD/t in many modern studies. | The manuscript explicitly labels the NH3 number as a **reduced catalyst-dependent cost objective** and does not compare it with total LCOA. | **Scope lock required** |

## Most important independent match

Yoshida et al. (2024) is especially useful because its conclusion is structurally independent but mechanistically aligned with this manuscript. Their Aspen-based process analysis reports that lowering pressure with high-activity Ru catalysts reduces gas-pressurization electricity, but additional refrigeration/separation demand and expensive Ru can offset the benefit; catalyst lifetime and Ru recycling then become economically important.

That is the same *type* of multiscale coupling exposed here, even though the process model, catalyst set and objective are different:

```text
intrinsic catalyst advantage
    -> changed process operating regime
    -> compression / separation trade-off
    -> catalyst inventory and lifecycle economics
    -> final industrial decision
```

This supports the **mechanism**, not the numerical cost values.

## Reader-facing wording rule

Preferred manuscript wording:

> Independent ammonia-process studies reach the same qualitative conclusion: the benefit of a more active Ru catalyst depends on the coupled response of compression, ammonia separation and catalyst lifecycle economics, so lower-pressure activity does not guarantee a lower process-level cost.

Do not write that the external studies "validate our cost model" or "reproduce our Fe > Ru result"; they use different catalyst formulations, process boundaries and plant assumptions.

## Literature

- Yoshida, M., Ogawa, T. & Ishihara, K. N. *Economic limitation of recent heterogeneous catalysts for ammonia synthesis*. Cleaner Chemical Engineering **10**, 100119 (2024). doi:10.1016/j.clce.2024.100119.
- Shin, B.-J. *et al.* *Comparative 3E (Energy, Economic, and Environment) study of gray, blue, and green ammonia: low-pressure Ru-based and high-pressure Fe-based Haber-Bosch processes*. International Journal of Hydrogen Energy **148**, 150090 (2025). doi:10.1016/j.ijhydene.2025.150090.
- Chen, H.-Y. *et al.* *Promotion effects in ammonia synthesis over ruthenium catalysts: A review*. EnergyChem **6**, 100140 (2024). doi:10.1016/j.enchem.2024.100140.
