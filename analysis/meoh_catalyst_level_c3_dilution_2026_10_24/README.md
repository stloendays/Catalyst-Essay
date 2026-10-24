# C3: methanol loop without the inlet limit, inert dilution charged to the rate (2026-10-24)

Question (internal review, item 2 / work item C3 of 2026-10-22): without the 6.86 % inlet limit the catalyst-level
counts fall to 8/63 (more catalyst loaded) and 16/63 (laboratory conversion). Does a loop without a hard limit, in which
the inert gases the recycle accumulates dilute the reactants and so lower the catalyst rate, recover the limited counts?

    set MEOH_FIELD_SET=combined
    D:\Research\CatalystForge\.venv\Scripts\python.exe -X utf8 c3_dilution.py --workers 3    # summary.json, ~25 min

Rate: STY_plant(purge) = STY_lab × [(1 − φ(purge)) / ρ_lab]ⁿ, φ the reactor-inlet CO + CH₄ + N₂ fraction at that purge,
ρ_lab = y_CO₂ (1 + H₂/CO₂) the reactant fraction of the laboratory feed, n the total apparent H₂ + CO₂ order (0.5–2).
Purge chosen by cost over the whole conversion-capped sweep; more catalyst loaded as in
`run_conversion_sensitivity.evaluate` (f = 0.95). Gate: n = 0 reproduces the committed unlimited-loop costs (max relative
deviation 4.9 × 10⁻¹⁰) and 16/63, 8/63.

| n | laboratory conversion | > 5 % | more catalyst loaded | > 5 % |
|---|---:|---:|---:|---:|
| 0 (unlimited loop) | 16/63 | 5 | 8/63 | 0 |
| 0.5 | 16/63 | 5 | 9/63 | 0 |
| 1 | 16/63 | 5 | 10/63 | 0 |
| 1.5 | 15/63 | 5 | 9/63 | 0 |
| 2 | 15/63 | 5 | 9/63 | 0 |

Reading: the catalyst inventory is a small part of the methanol production cost, so a slower catalyst in a diluted loop
costs little and the optimizer still lets CO accumulate. Charging dilution to the rate does not recover the counts of
the limited loop; the limit stands in for what this rate term does not capture (the loop design the cost model was
anchored on, and the industrial practice of purging to 4.4–9.8 % inerts). Not used in the manuscript (author decision
2026-10-24: unfavourable results stay in the repository).
