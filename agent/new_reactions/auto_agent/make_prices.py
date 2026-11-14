"""Writes prices.json: the fixed price table every AI build cites (user 2026-11-13: one price table; the AI cites prices,
it may not set them). Basis: US Gulf Coast, 2024 USD unless stated; low/high are the sensitivity ranges used by
run_sensitivity. Values follow public sources; where the hand-built configs used the same public figure it is reused
(the hand models themselves stay hidden).
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
metals = json.loads((HERE.parent / "configs" / "metal_prices.json").read_text(encoding="utf-8"))
metal_src = metals.pop("_source")

P = {
    "natural_gas": dict(value=2.5, unit="USD/GJ", low=2.0, high=12.0,
                        source="PetroLogistics Catofin plant gas cost 2.60 USD/MMBtu (SEC 424B4, 2012); Henry Hub 2024 average 2.19 USD/MMBtu (EIA)",
                        note="high end covers European hub prices"),
    "electricity": dict(value=80.0, unit="USD/MWh", low=40.0, high=150.0,
                        source="industrial power assumption used across the NCE chains; EIA 2024 US industrial average about 80 USD/MWh"),
    "hydrogen": dict(value=3.0, unit="USD/kg", low=1.5, high=7.0,
                     source="Becker, Penev & Braun, J. Energy Resour. Technol. 2019 anchor 3 USD/kg; grey about 2, electrolytic 5-7 (DOE Pathways to Commercial Liftoff: Clean Hydrogen, 2024)"),
    "carbon_dioxide": dict(value=100.0, unit="USD/t", low=20.0, high=200.0,
                           source="104 USD/t CO2 captured, Enterprise Products EPA GHG permit application 2012, rounded"),
    "propane": dict(value=408.0, unit="USD/t", low=300.0, high=700.0,
                    source="EIA Mont Belvieu propane spot 2024, 0.778 USD/gal at 4.2 lb/gal"),
    "ammonia": dict(value=445.0, unit="USD/t", low=300.0, high=900.0,
                    source="Tampa CFR ammonia, March 2024 contract settlement (trade press summary)"),
    "ethanol": dict(value=716.1, unit="USD/t", low=500.0, high=1000.0,
                    source="Haro et al. 2013, Table 9 (Brazilian hydrated ethanol)"),
    "catalyst_support_and_manufacturing": dict(value=20.0, unit="USD/kg", low=5.0, high=100.0,
                                               source="NCE chain assumption for support plus manufacturing per kg of finished catalyst, excluding active metals"),
}
for el, v in metals.items():
    P[f"metal_{el}"] = dict(value=float(v), unit="USD/kg", low=0.5 * float(v), high=2.0 * float(v),
                            source=metal_src + " (per kg contained element)")
P.update({
    "capital_recovery_factor": dict(value=0.0944, unit="1/y", low=0.08, high=0.13,
                                    source="7 %/y over 20 y (Enterprise Products PDH, EPA GHG permit application 2012); range 5-12 %/y"),
    "fixed_om_fraction_of_capex": dict(value=0.04, unit="1/y", low=0.02, high=0.06, source="NCE chain assumption, 4 %/y of installed capital"),
})
out = {"basis": "US Gulf Coast, 2024 USD; the agent must cite these and may not set prices", "prices": P}
(HERE / "prices.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
print(f"written prices.json with {len(P)} prices")
