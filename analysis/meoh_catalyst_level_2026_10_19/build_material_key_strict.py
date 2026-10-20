"""Outcome-blind catalyst-identity annotation for the strict rule (RULES.md section 1).

Reads from the frozen candidate table only the identity columns (group, doi, catalyst, catalyst_key, T_C) and,
as a boolean finite-mask, the cost column that defines which entries are in the comparison; no cost value, STY,
ranking, leader or regret is read or used. Each (group, catalyst_key) with >= 2 distinct keys in its group is
annotated with composition, loading, support and synthesis from the sample name, the locator text, the extraction
records (agent/extraction/out/raw*, analysis/validation_meoh_prospective_2026_10_13/out/raw*) and the papers.

Strict rule: samples of one composition (elements and ratios, promoters/dopants included), loading and support
(identity and crystal phase as the authors report it) that differ only in synthesis share material_key_strict.

Output: material_key_strict.csv (one row per in-scope (group, catalyst_key)).
"""
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "meoh_field_pooled_2026_10_15" / "pooled_candidates.csv"
OUT = HERE / "material_key_strict.csv"

# ---------------------------------------------------------------------------------------------------------------
# Annotation per (doi, catalyst_key): composition, loading, support, synthesis, evidence.
# ---------------------------------------------------------------------------------------------------------------
X = "raw extraction record"
A = {}


def add(doi, key, comp, load, sup, syn, ev=X):
    A[(doi, key)] = (comp, load, sup, syn, ev)


d = "10.1002/anie.201600943"
add(d, "in2o3", "In2O3", "bulk", "none (bulk oxide)", "calcination of In(OH)3, 573 K")
add(d, "cu-zno-al2o3", "Cu-ZnO-Al2O3 (ratio n.r.)", "n.r.", "Al2O3", "hydroxycarbonate coprecipitation")

d = "10.1002/cctc.202000974"
add(d, "pd/tio2", "Pd", "5 wt% Pd", "TiO2", "CVI, air 500 C")
add(d, "pd/zno", "Pd", "5 wt% Pd", "ZnO", "CVI, air 500 C")
add(d, "pdzn/tio2", "Pd-Zn (Pd:Zn 1:5)", "5 wt% Pd", "TiO2", "CVI, air 500 C")
add(d, "pd/zntio3", "Pd", "5 wt% Pd", "ZnTiO3", "CVI, air 500 C")
add(d, "pdzn/zntio3", "Pd-Zn (Pd:Zn 1:5)", "5 wt% Pd", "ZnTiO3", "CVI, air 500 C")
add(d, "physicalmixtureofpd/znoandtio2", "Pd/ZnO + TiO2 (physical mixture)", "5 wt% Pd on ZnO", "ZnO + TiO2",
    "physical mixing of Pd/ZnO with TiO2")
add(d, "zno", "ZnO", "-", "none (bare support)", "pelleted support")
add(d, "tio2", "TiO2", "-", "none (bare support)", "pelleted support")
add(d, "zntio3", "ZnTiO3", "-", "none (bare support)", "pelleted support")

d = "10.1002/ente.201800747"
for k, w, u in [("cat-1.5", "9.8", "1.5"), ("cat-3.0", "12.3", "3.0"), ("cat-4.5", "16.4", "4.5"),
                ("cat-6.0", "6.2", "6.0")]:
    add(d, k, "hexagonal In2O3", f"{w} wt% In2O3", "Al2O3/Al-fiber", f"solvothermal, urea/In {u}, calc. 400 C",
        X + " (In2O3 content per sample, SI)")
add(d, "in2o3-iwi/al2o3/al-fiber", "cubic In2O3", "14.6 wt% In2O3", "Al2O3/Al-fiber", "incipient wetness impregnation")
add(d, "h-in2o3/al2o3", "hexagonal In2O3", "n.r. (urea/In 4.5)", "Al2O3 (no Al-fiber)", "solvothermal, urea/In 4.5")

d = "10.1016/j.apcata.2018.04.036"
add(d, "0.5ca5p5zc", "Pd-Zn-Ca", "5 wt% Pd, 5 wt% Zn, 0.5 wt% Ca", "CeO2", "citric-acid chelating, calc. 500 C")
add(d, "5p5zc", "Pd-Zn", "5 wt% Pd, 5 wt% Zn", "CeO2", "citric-acid chelating, calc. 500 C")
add(d, "5pc", "Pd", "5 wt% Pd", "CeO2", "citric-acid chelating, calc. 500 C")

d = "10.1016/j.apcatb.2017.06.069"
add(d, "pd-i/in2o3", "Pd", "0.97 wt% Pd", "In2O3", "incipient wetness impregnation, calc. 350 C")
add(d, "in2o3", "In2O3", "bulk", "none (bulk oxide)", "precipitation")

d = "10.1016/j.cattod.2019.05.040"
add(d, "0.5ca5p5zzr-imp", "Pd-Zn-Ca", "5 wt% Pd, 5 wt% Zn, 0.5 wt% Ca", "ZrO2", "impregnation, calc. 500 C")
add(d, "5p5zzr-imp", "Pd-Zn", "5 wt% Pd, 5 wt% Zn", "ZrO2", "impregnation, calc. 500 C")

d = "10.1016/j.cattod.2020.05.049"
for k, s in [("pd-cu/tio2-c", "TiO2-C"), ("pd-cu/ti0.8ce0.2o2", "Ti0.8Ce0.2O2"), ("pd-cu/ti0.2ce0.8o2", "Ti0.2Ce0.8O2"),
             ("pd-cu/ceo2-c", "CeO2-C"), ("pd-cu/ti0.8zr0.2o2", "Ti0.8Zr0.2O2"), ("pd-cu/ti0.5zr0.5o2", "Ti0.5Zr0.5O2"),
             ("pd-cu/ti0.3zr0.7o2", "Ti0.3Zr0.7O2"), ("pd-cu/ti0.2zr0.8o2", "Ti0.2Zr0.8O2"),
             ("pd-cu/ti0.1zr0.9o2", "Ti0.1Zr0.9O2"), ("pd-cu/zro2-c", "ZrO2-C")]:
    add(d, k, "Pd-Cu, Pd/(Pd+Cu) = 0.25", "series loading (same for all)", s,
        "co-impregnation; support by urea precipitation, 723 K")

d = "10.1016/j.fuel.2023.127927"
for k, ca in [("pzc", "0"), ("0.3ca-pzc", "0.3"), ("0.5ca-pzc", "0.5"), ("0.7ca-pzc", "0.7"), ("1.0ca-pzc", "1.0")]:
    add(d, k, "Pd-Zn (1:1)" + ("" if ca == "0" else "-Ca"), f"8.1 wt% Pd, 5 wt% Zn, {ca} wt% Ca", "CeO2",
        "sol-gel chelation, calc. 500 C")

d = "10.1016/j.fuel.2024.131111"
for x, y in [(300, 425), (350, 425), (450, 425), (500, 425), (400, 375), (400, 400), (400, 450), (400, 475),
             (400, 500)]:
    sup = "Fe3O4" if (x, y) != (400, 500) else "Fe3O4 partly over-reduced to Fe/FeCx (paper Sec. 3.3.1)"
    add(d, f"5inni3c0.5/fe3o4-{x}/{y}", "InNi3C0.5 (In/Ni 1/3)", "5 wt% In", sup,
        f"coprecipitation; calcination {x} C / carburization {y} C",
        X + "; paper Sec. 3.3.1 / Fig. 4 (Fe3O4 kept pure phase except 400/500)")
add(d, "5%inni3c0.5/sio2", "InNi3C0.5 (In/Ni 1/3)", "5 wt% In", "SiO2", "calcination 400 C / carburization 425 C")
add(d, "fe3o4", "Fe3O4", "-", "none (bare support)", "calcination 400 C / carburization 425 C")

d = "10.1016/j.jcat.2012.05.020"
add(d, "pdznal", "Pd:Zn:Al 1.0:69.5:29.5 (PdZn)", "1.46 wt% Pd", "ZnO/AlOx (HT-derived)", "hydrotalcite coprecipitation")
add(d, "pdmgga", "Pd:Mg:Ga 1.0:64.5:34.5 (Pd2Ga)", "1.81 wt% Pd", "MgO/MgGa2O4 (HT-derived)",
    "hydrotalcite coprecipitation")
add(d, "pdmgal", "Pd:Mg:Al 1.3:69.1:29.6", "3.13 wt% Pd", "MgAlOx (HT-derived)", "hydrotalcite coprecipitation")

d = "10.1016/j.jcat.2016.03.017"
ev = X + "; paper Tables 4-6 (all Pd/ZnO on the same ZnO)"
add(d, "1%pd,si", "Pd", "1 wt% Pd", "ZnO", "sol immobilisation", ev)
add(d, "1%pd,im", "Pd", "1 wt% Pd", "ZnO", "impregnation", ev)
add(d, "5%pd,si", "Pd", "5 wt% Pd", "ZnO", "sol immobilisation", ev)
add(d, "5%pd,im", "Pd", "5 wt% Pd", "ZnO", "impregnation", ev)
add(d, "5%pd/znosi", "Pd", "5 wt% Pd", "ZnO", "sol immobilisation, calcination pretreatment (Table 5)", ev)
add(d, "5%pd/znoim", "Pd", "5 wt% Pd", "ZnO", "impregnation, heat-treatment variant (Table 6)", ev)

d = "10.1016/j.jcou.2016.11.015"
for k, w in [("cza-1", "9.94"), ("cza-2", "22.76"), ("cza-3", "33.61"), ("cza-4", "44.50"), ("cza-5", "55.3")]:
    add(d, k, "Cu-ZnO, Cu/Zn ~2.3", f"Cu+ZnO {w} wt%", "Al2O3", "ammonia deposition-precipitation, calc. 623 K")

d = "10.1016/j.jes.2023.05.010"
ev = X + "; paper Sec. 2.1 (all cubic In2O3; Au 1.01-1.03 wt% by ICP-MS)"
for m, w, s in [("hm", "1.03", "solvothermal hollow microspheres"), ("np", "1.01", "hydrothermal nanoparticles"),
                ("ns", "1.02", "precipitation nanosheets")]:
    add(d, f"au/in2o3-{m}", "Au", f"{w} wt% Au", "cubic In2O3", f"deposition-precipitation on In2O3-{m.upper()} ({s})", ev)
    add(d, f"in2o3-{m}", "In2O3", "bulk", "none (bulk cubic In2O3)", f"In2O3-{m.upper()} ({s})", ev)

d = "10.1021/acs.iecr.7b01464"
for r in (200, 300, 400):
    add(d, f"cza{r}", "Cu:Zn:Al 58:25:17", "Cu:Zn:Al 58:25:17", "Al2O3 (component)",
        f"mechanical-force solid-state ion exchange, ball milling {r} rpm, calc. 320 C")

d = "10.1021/acscatal.0c05628"
for w in ("1", "5", "10"):
    add(d, f"ir/in2o3-{w}", "Ir", f"{w} wt% Ir", "In2O3", "incipient wetness impregnation, calc. 450 C")
add(d, "pristinein2o3", "In2O3", "bulk", "none (bulk oxide)", "precipitation, calc. 350 C")

d = "10.1021/acscatal.1c03170"
for m in ("ni", "pd", "cu", "co"):
    add(d, f"{m}-in2o3", f"{m.capitalize()}-promoted In2O3", f"5 wt% {m.capitalize()}", "none (bulk In2O3)",
        "one-step flame spray pyrolysis")

d = "10.1021/acscatal.5c05984"
add(d, "1wt%re/tio2", "Re", "1 wt% Re", "TiO2 (P25)", "wet impregnation (Re2O7)")
add(d, "5wt%re/tio2", "Re", "5 wt% Re", "TiO2 (P25)", "wet impregnation (Re2O7)")

d = "10.1021/acscatal.9b01869"
for w in ("0.1", "0.25", "0.5", "1", "2.5", "5", "10"):
    add(d, f"in{w}/zro2", "In oxide", f"{w} wt% In", "m-ZrO2", "impregnation, calc. 600 C")
add(d, "bulkin2o3(in2o3-b)", "In2O3", "bulk", "none (commercial bulk In2O3)", "commercial")

d = "10.1021/acscatal.9b03305"
for k, n, m in [("1in2o3-99zro2", 1, "1.0"), ("5in2o3-95zro2", 5, "3.6"), ("25in2o3-75zro2", 25, "26.8"),
                ("50in2o3-50zro2", 50, "51.8"), ("75in2o3-25zro2", 75, "76.3"), ("95in2o3-5zro2", 95, "96.4"),
                ("99in2o3-1zro2", 99, "98.5")]:
    add(d, k, "In2O3-ZrO2 mixed oxide", f"{n} mol% In nominal ({m} measured)", "ZrO2 (coprecipitated)",
        "coprecipitation, calc. 773 K")
add(d, "100in2o3-0zro2", "In2O3", "bulk", "none (bulk oxide)", "coprecipitation, calc. 773 K")
for k, s in [("in2o3/m-zro2", "m-ZrO2"), ("in2o3/t-zro2", "t-ZrO2"), ("in2o3/al2o3", "Al2O3"), ("in2o3/ceo2", "CeO2")]:
    add(d, k, "In2O3", "5 wt% In2O3", s, "wet impregnation, calc. 773 K")

d = "10.1021/cs500979c"
ev = X + "; paper Table 1 (t-ZrO2 fraction) and title (ZrO2 structure is the studied variable)"
for k, cu, t, s in [("cu/zro2(i)", 15, 7, "impregnation of ZrO2(A), calc. 623 K"),
                    ("cu/zro2(ii)", 10, 33, "impregnation of ZrO2(B), calc. 623 K"),
                    ("cu/zro2(iii)", 10, 71, "citric-acid complexation, calc. 623 K"),
                    ("cu/zro2(iv)", 10, 100, "citric-acid complexation, calc. 773 K"),
                    ("cu/zro2(v)", 10, 15, "NaOH precipitation, calc. 623 K")]:
    add(d, k, "Cu", f"{cu} atom% Cu", f"ZrO2, t-ZrO2 {t}% / m-ZrO2 {100 - t}%", s, ev)
add(d, "zro2", "ZrO2", "-", "none (bare support)", "n.r.")

d = "10.1038/s41467-019-11349-9"
ev = X + "; paper Fig. 6 = extended test of the best Pd-In2O3 CP catalyst (0.75 wt% nominal Pd)"
add(d, "pd-in2o3cp", "Pd-promoted In2O3", "0.75 wt% Pd (nominal)", "none (In2O3 matrix)",
    "coprecipitation, calc. 573 K", ev)
add(d, "cp", "Pd-promoted In2O3", "0.75 wt% Pd (nominal)", "none (In2O3 matrix)",
    "coprecipitation, calc. 573 K (same sample, Fig. 6 stability test)", ev)

d = "10.1039/c2cy20604h"
add(d, "cu/al2o3", "Cu", "18 wt% Cu", "Al2O3", "incipient wetness impregnation, calc. 673 K")
add(d, "cu-k/al2o3", "Cu-K", "18 wt% Cu (parent), 5 wt% K", "Al2O3", "K2CO3 impregnation of Cu/Al2O3")
add(d, "cu-ba/al2o3", "Cu-Ba", "18 wt% Cu (parent), 5 wt% Ba", "Al2O3", "Ba acetate impregnation of Cu/Al2O3")

d = "10.1039/c5cy00372e"
for y in ("0", "0.05", "0.1", "0.2", "0.5"):
    add(d, f"cht-y{y}", "Cu:Zn:(Al+Y) 2:1:1" + ("" if y == "0" else "-Y"), f"Y/(Al+Y) = {y}", "Al2O3 (HT-derived)",
        "hydrotalcite coprecipitation, calc. 773 K")

d = "10.1039/c6ra28305e"
ev = X + "; paper Fig. 1 XRD / Raman (350,450 C amorphous ZrO2; 550 C t-ZrO2; 650 C t+m-ZrO2)"
for c, ph in [(350, "amorphous ZrO2"), (450, "amorphous ZrO2"), (550, "t-ZrO2"), (650, "t-ZrO2 + m-ZrO2")]:
    add(d, f"cz-{c}", "(CuO)0.5(ZrO2)0.5", "~31.5 wt% Cu", ph, f"coprecipitation, calcination {c} C", ev)

d = "10.1039/d0gc01597k"
add(d, "pt/in2o3", "Pt", "1.07 wt% Pt", "In2O3", "deposition-precipitation, calc. 450 C")
add(d, "in2o3", "In2O3", "bulk", "none (bulk oxide)", "precipitation, calc. 450 C")

d = "10.1126/sciadv.abi6012"
for k, s in [("inni3c0.5/m-zro2", "m-ZrO2"), ("inni3c0.5/t-zro2", "t-ZrO2"), ("inni3c0.5/a-zro2", "a-ZrO2"),
             ("inni3c0.5/sio2", "SiO2")]:
    add(d, k, "InNi3C0.5", "42.8 wt% InNi3C0.5", s, "impregnation, calc. 350 C, carburization 600 C")
for k, s in [("inni3c0.5/zno", "ZnO"), ("inni3c0.5/ceo2", "CeO2"), ("inni3c0.5/tio2", "TiO2")]:
    add(d, k, "InNi3C0.5", "n.r. (series loading)", s, "impregnation, carburization 600 C")
add(d, "inni3c0.5/fe3o4", "InNi3C0.5", "11.4 wt% InNi3C0.5", "Fe3O4", "carburization of In2O3-NiO/Fe2O3")
add(d, "cuznal", "Cu-Zn-Al", "n.r.", "Al2O3", "coprecipitation (ref. 20)")
for k, s in [("m-zro2", "m-ZrO2"), ("t-zro2", "t-ZrO2"), ("a-zro2", "a-ZrO2"), ("sio2", "SiO2")]:
    add(d, k, s, "-", "none (bare support)", "n.r.")

d = "10.1002/cbh2.70072"
for k, s in [("cu/znga", "ZnGa2O4"), ("cu/zncr", "ZnCr2O4"), ("cu/znal", "ZnAl2O4")]:
    add(d, k, "Cu", "5 wt% Cu", s, "ultrasonic impregnation on spinel, calc. 350 C")

d = "10.1007/s11426-026-3904-1"
add(d, "cuznal", "Cu:Zn:Al 6:2.7:1", "Cu:Zn:Al 6:2.7:1", "Al oxide (component)", "controlled coprecipitation")
add(d, "cuznzr", "Cu:Zn:Zr 6:2.7:1", "Cu:Zn:Zr 6:2.7:1", "Zr oxide (component)", "controlled coprecipitation")

d = "10.1021/acs.energyfuels.6c02662"
add(d, "czam-ldh", "Cu:Zn:Al:Mg 3:1:1:0.02", "-", "LDH-derived Al oxide", "LDH coprecipitation, calc. 500 C")
add(d, "czam-ldh+p-pdvb", "Cu:Zn:Al:Mg 3:1:1:0.02 + porous PDVB", "PDVB/CZAM-LDH = 0.25 (mass)",
    "LDH-derived Al oxide", "physical mixing with solvothermal p-PDVB")

d = "10.1021/acs.iecr.6c02654"
add(d, "zno/cu", "Zn/Cu 14:86", "Zn/Cu 14:86", "none (inverse oxide/Cu)", "oxalic-acid coprecipitation")
add(d, "gaox/cu", "Ga/Cu 14:86", "Ga/Cu 14:86", "none (inverse oxide/Cu)", "oxalic-acid coprecipitation")
add(d, "zro2/cu", "Zr/Cu 14:86", "Zr/Cu 14:86", "none (inverse oxide/Cu)",
    "oxalic-acid coprecipitation on malachite-derived CuO, calc. 450 C")
add(d, "alkali-treatedcatalyst", "CuOx (no promoter oxide)", "-", "none", "alkali-treated malachite, calc. 550 C")

d = "10.1021/acs.iecr.6c02734"
add(d, "pd/zro2", "Pd", "Pd n.r.; 0 In2O3 ALD cycles", "ZrO2 (from UiO-66)", "Pd on UiO-66, calc. 500 C")
for n, pdl in [(1, "n.r."), (5, "n.r."), (10, "3.31 wt% Pd"), (15, "1.51 wt% Pd")]:
    add(d, f"pd/{n}in2o3/zro2", "Pd-In2O3", f"{pdl}; {n} In2O3 ALD cycles", "ZrO2 (from UiO-66)",
        "In2O3 ALD on UiO-66, Pd loading, calc. 500 C")
add(d, "10in2o3/zro2", "In2O3", "10 In2O3 ALD cycles", "ZrO2 (from UiO-66)", "In2O3 ALD on UiO-66, calc. 500 C")
add(d, "10in2o3/sio2", "In2O3", "10 In2O3 ALD cycles", "SiO2", "In2O3 ALD on SiO2, calc. 500 C")
add(d, "pd/10in2o3/sio2", "Pd-In2O3", "Pd n.r.; 10 In2O3 ALD cycles", "SiO2", "In2O3 ALD on SiO2, Pd loading")

d = "10.1021/acs.iecr.6c02971"
add(d, "cza-n2", "Cu-ZnO-Al2O3 (no additive)", "-", "Al2O3", "urea hydrolysis, wet grinding, N2 350 C")
for k, a, r in [("cza-0.1gc", "graphite", "0.1"), ("cza-0.1ac", "activated carbon", "0.1"),
                ("cza-0.1cnt", "carbon nanotubes", "0.1"), ("cza-0.05ac", "activated carbon", "0.05"),
                ("cza-0.2ac", "activated carbon", "0.2"), ("cza-0.3ac", "activated carbon", "0.3"),
                ("cza-0.1sio2", "SiO2", "0.1")]:
    add(d, k, f"Cu-ZnO-Al2O3 + {a}", f"{a}/CZA = {r} (mass)", "Al2O3",
        "wet grinding with additive, N2 350 C")

d = "10.1021/acscatal.6c01275"
add(d, "11zno/tio2", "ZnO", "11 at% Zn", "TiO2", "wet impregnation, calc. 350 C")
add(d, "0.6reox11zno/tio2", "ReOx-ZnO", "0.6 at% Re, 11 at% Zn", "TiO2", "wet impregnation, calc. 350 C")

d = "10.1021/acscatal.6c01304"
add(d, "h-zro2@cu1.3znal1.6-ldh", "Cu:Zn:Al 1.3:1:1.6 on ZrO2 (ZrO2/LDH 42:58)", "~22 wt% Cu", "hollow ZrO2",
    "LDH coprecipitation on h-ZrO2@AlOOH")
add(d, "cu1.3znal-ldh", "Cu:Zn:Al 1.3:1:1", "~35 wt% Cu", "none (LDH-derived oxide)", "LDH coprecipitation")
add(d, "commercialmethanolsynthesiscatalyst", "Cu/ZnO/Al2O3 (commercial)", "n.r.", "Al2O3", "commercial")

d = "10.1021/acscatal.6c02907"
ev = "paper Cu/ZnO Synthesis + Experimental: all Cu:Zn 70:30; XPS Na 1s shows no residual Na"
for k, s in [("cuzn-nh4hco3", "NH4HCO3 precipitant, 0.5 mL/min"), ("cuzn-naoh-0.25", "NaOH precipitant, 0.25 mL/min"),
             ("cuzn-naoh-0.5", "NaOH precipitant, 0.5 mL/min"), ("cuzn-naoh-1.0", "NaOH precipitant, 1.0 mL/min"),
             ("cuzn-nh4oh-0.25", "NH4OH precipitant, 0.25 mL/min")]:
    add(d, k, "Cu:Zn 70:30 (molar)", "Cu:Zn 70:30", "ZnO (component)", f"coprecipitation, {s}, calc. 360 C", ev)

d = "10.1021/acscatal.6c03987"
add(d, "cu", "Cu", "~10 wt% Cu", "Mg-Al oxide (HT-derived, Mg/Al 4)", "hydrotalcite coprecipitation, calc. 550 C")
for k, m, w in [("cuzn1.5", "Zn", "1.5"), ("cula1.5", "La", "1.5"), ("cuin1.5", "In", "1.5"), ("cuga1.5", "Ga", "1.5"),
                ("cuga2.5", "Ga", "2.5")]:
    add(d, k, f"Cu-{m}", f"~10 wt% Cu, {w} wt% {m}", "Mg-Al oxide (HT-derived, Mg/Al 4)",
        "hydrotalcite coprecipitation, calc. 550 C")
add(d, "cu-ga2o3", "Cu-Ga (gamma-Ga2O3 nanoparticles)", "~10 wt% Cu; Ga n.r. ('comparable metal loadings')",
    "Mg-Al oxide (HT-derived)", "colloidal gamma-Ga2O3 deposited on calcined Cu-HT, calc. 550 C",
    X + "; SI Sec. 1.1.2 (Ga loading of the reference not reported)")

d = "10.1021/acscatal.6c04842"
add(d, "gazr/90cu", "Cu-Ga-Zr (Ga:Zr 1:3)", "90 at% Cu", "none (inverse oxide/Cu)", "coprecipitation, calc. 400 C")
add(d, "znzr/90cu", "Cu-Zn-Zr (Zn:Zr 1:3)", "90 at% Cu", "none (inverse oxide/Cu)", "coprecipitation, calc. 400 C")

d = "10.1021/acscatal.6c05217"
add(d, "cu@uio-36aa-pse", "Cu", "n.r.", "UiO-66 (36AA, PSE-repaired)", "ethanol impregnation, N2 calcination")
add(d, "cu/zro2", "Cu", "n.r.", "ZrO2", "conventional Cu/ZrO2")

d = "10.1021/acscatal.6c06647"
add(d, "zno", "ZnO", "-", "none", "n.r.")
add(d, "znso4-derivedresidues", "ZnSO4-derived residue", "-", "none", "n.r.")
add(d, "physicalmixturesofzns+mos2", "ZnS + MoS2 (physical mixture)", "n.r.", "MoS2", "physical mixing")
add(d, "impregnatedzn/mos2", "Zn on MoS2", "n.r.", "MoS2", "impregnation")

d = "10.1021/acscatal.6c06714"
add(d, "in2o3-r", "In2O3", "bulk", "none (bulk oxide)", "precipitation, calc. 300 C")
add(d, "pd/in2o3-r", "Pd", "1 wt% Pd", "In2O3", "incipient wetness impregnation, calc. 400 C")
add(d, "cnt+in2o3-r", "In2O3 + CNT (1:1 mass)", "-", "CNT (physical mixture)", "physical grinding")
add(d, "pd/cnt+in2o3-r", "Pd/CNT + In2O3 (1:1 mass)", "1 wt% Pd on CNT (~0.5 wt% overall)", "CNT (physical mixture)",
    "Pd/CNT by IWI, physical grinding with In2O3")

d = "10.1021/acscatal.6c06780"
add(d, "cza", "Cu/ZnO/Al2O3 (commercial)", "-", "Al2O3", "commercial, calc. 773 K")
add(d, "cza-2zr", "Cu/ZnO/Al2O3-Zr", "Zr/Cu = 2 mol%", "Al2O3", "IWI of Zr on commercial CZA")
add(d, "cza-8zr", "Cu/ZnO/Al2O3-Zr", "Zr/Cu = 8 mol%", "Al2O3", "IWI of Zr on commercial CZA")
add(d, "ca", "Cu/Al2O3", "-", "Al2O3", "coprecipitation, calc. 773 K")
add(d, "ca-2zr", "Cu/Al2O3-Zr", "Zr/Cu = 2 mol%", "Al2O3", "IWI of Zr on CA")

d = "10.1021/acssuschemeng.6c05638"
add(d, "cza", "Cu-Zn-Al", "n.r.", "Al oxide (component)", "n.r.")
add(d, "czc-oa", "Zn:Cu:Ce 1:2:1", "Zn:Cu:Ce 1:2:1", "Ce oxide (component)", "oxalic-acid precipitation, calc. 450 C")

d = "10.1038/s41467-025-65929-z"
ev = X + "; SI Synthesis of PFCP series and of LDH-NiInCAl (both RNi/In 2.5, oxide support 45 wt%)"
for k, s in [("pfcp-niincce", "CeO2"), ("pfcp-niincsi", "SiO2"), ("pfcp-niincmg", "MgO"), ("pfcp-niinczr", "ZrO2"),
             ("pfcp-niincmn", "MnOx")]:
    add(d, k, "Ni-In carbide, Ni/In 2.5", "support 45 wt%", s, "parallel-flow coprecipitation, carburization 500 C", ev)
add(d, "pfcp-niincal", "Ni-In carbide, Ni/In 2.5", "support 45 wt%", "Al2O3",
    "parallel-flow coprecipitation, carburization 500 C", ev)
add(d, "ldh-niincal", "Ni-In carbide, Ni/In 2.5", "support 45 wt%", "Al2O3 (LDH-derived)",
    "LDH coprecipitation, carburization", ev)
add(d, "niinczr", "Ni3InC0.5, Ni/In 3.0", "33 wt% Ni", "m-ZrO2", "ammonia carbonate coprecipitation, carburization 600 C",
    X + "; paper Methods (Ni 33 wt%, RNi/In 3.0)")

d = "10.1038/s41467-026-72876-w"
add(d, "in1.9sn0.1o3.05", "Sn-doped In2O3", "5.0 at% Sn", "none (bulk oxide)", "colloidal synthesis, calc. 650 C")
add(d, "in1.9zr0.1o3.05", "Zr-doped In2O3", "5.5 at% Zr", "none (bulk oxide)", "colloidal synthesis, calc. 650 C")
add(d, "nano-in2o3", "In2O3 (undoped)", "-", "none (bulk oxide)", "colloidal synthesis, calc. 400 C")

d = "10.1038/s41557-026-02104-x"
for k, c, s in [("ptmo6o24@nu1k", "PtMo6O24", "NU1K"), ("ptmo6o24/zro2", "PtMo6O24", "ZrO2"),
                ("pt@nu1k", "Pt nanoparticles", "NU1K"), ("ptv9o28@nu1k", "PtV9O28", "NU1K"),
                ("ptw6o24@nu1k", "PtW6O24", "NU1K"), ("ptmo6o24sc", "PtMo6O24 (unsupported)", "none"),
                ("ptmo6o24@nu901", "PtMo6O24", "NU901"), ("ptmo6o24@nu1008", "PtMo6O24", "NU1008"),
                ("ptmo6o24@hf-nu1k", "PtMo6O24", "Hf-NU1K"), ("znmo6o24@nu1k", "ZnMo6O24", "NU1K"),
                ("almo6o24@nu1k", "AlMo6O24", "NU1K")]:
    add(d, k, c, "n.r.", s, "encapsulation/impregnation")

d = "10.1038/s41565-026-02135-y"
ev = "paper 'Synthesis-dependent reducibility' section: all 2 wt% In2O3, predominantly monoclinic HfO2 (Ext. Data Fig. 3)"
for w in ("1", "2", "3", "5", "7", "10"):
    add(d, f"{w}inhfox", "In2O3-HfO2", f"{w} wt% In2O3", "HfO2 (m-dominant)", "flame spray pyrolysis",
        ev if w == "2" else X)
    add(d, f"{w}inzrox", "In2O3-ZrO2", f"{w} wt% In2O3", "ZrO2", "flame spray pyrolysis")
add(d, "in2o3/hfo2(fsp),wi", "In2O3-HfO2", "2 wt% In2O3", "HfO2 (m-dominant)", "wet impregnation of FSP HfO2", ev)
add(d, "in2o3/hfo2(p),wi", "In2O3-HfO2", "2 wt% In2O3", "HfO2 (m-dominant)", "wet impregnation of precipitated HfO2", ev)
add(d, "inhfox,cp", "In2O3-HfO2", "2 wt% In2O3", "HfO2 (m-dominant)", "coprecipitation, calc. 973 K", ev)

d = "10.1126/sciadv.aea7041"
ev = X + "; SI Table S5 / Fig. S4-S5 (all In2O3:CNT 1:2 by mass; differ in assembly route)"
add(d, "in2o3", "In2O3", "bulk", "none (bulk oxide)", "n.r.")
add(d, "cnt", "CNT", "-", "none", "n.r.")
add(d, "in2o3-bn(1:2)", "In2O3 + BN", "In2O3:BN = 1:2 (mass)", "BN", "In2O3-BN composite")
for r in ("3:1", "1:1", "1:4"):
    add(d, f"in2o3-cnt({r})", "In2O3 + CNT", f"In2O3:CNT = {r} (mass)", "CNT", "In2O3-CNT composite")
add(d, "in2o3-cnt(1:2)", "In2O3 + CNT", "In2O3:CNT = 1:2 (mass)", "CNT", "In2O3-CNT composite (standard route)", ev)
add(d, "in2o3@cnt-h(1:2)", "In2O3 + CNT", "In2O3:CNT = 1:2 (mass)", "CNT", "In2O3@CNT, route H", ev)
add(d, "in2o3@cnt-ui(1:2)", "In2O3 + CNT", "In2O3:CNT = 1:2 (mass)", "CNT", "In2O3@CNT, route UI", ev)

# ---------------------------------------------------------------------------------------------------------------
# Shared strict keys (synthesis-only sets) and flags.
# ---------------------------------------------------------------------------------------------------------------
SETS = {
    "10.1016/j.fuel.2024.131111": {"5In-InNi3C0.5/Fe3O4": [f"5inni3c0.5/fe3o4-{x}/{y}" for x, y in [
        (300, 425), (350, 425), (450, 425), (500, 425), (400, 375), (400, 400), (400, 450), (400, 475)]]},
    "10.1016/j.jcat.2016.03.017": {"1wt%Pd/ZnO": ["1%pd,si", "1%pd,im"],
                                   "5wt%Pd/ZnO": ["5%pd,si", "5%pd,im", "5%pd/znosi", "5%pd/znoim"]},
    "10.1016/j.jes.2023.05.010": {"1wt%Au/cubic-In2O3": ["au/in2o3-hm", "au/in2o3-np", "au/in2o3-ns"],
                                  "cubic-In2O3": ["in2o3-hm", "in2o3-np", "in2o3-ns"]},
    "10.1021/acs.iecr.7b01464": {"CuZnAl-58:25:17": ["cza200", "cza300", "cza400"]},
    "10.1038/s41467-019-11349-9": {"0.75Pd-In2O3": ["pd-in2o3cp", "cp"]},
    "10.1039/c6ra28305e": {"CuO-ZrO2-amorphous": ["cz-350", "cz-450"]},
    "10.1021/acscatal.6c02907": {"CuZn-70:30": ["cuzn-nh4hco3", "cuzn-naoh-0.25", "cuzn-naoh-0.5", "cuzn-naoh-1.0",
                                                "cuzn-nh4oh-0.25"]},
    "10.1038/s41467-025-65929-z": {"NiInC2.5/Al2O3-45": ["pfcp-niincal", "ldh-niincal"]},
    "10.1038/s41565-026-02135-y": {"2In2O3/m-HfO2": ["2inhfox", "in2o3/hfo2(fsp),wi", "in2o3/hfo2(p),wi",
                                                     "inhfox,cp"]},
    "10.1126/sciadv.aea7041": {"In2O3:CNT-1:2": ["in2o3-cnt(1:2)", "in2o3@cnt-h(1:2)", "in2o3@cnt-ui(1:2)"]},
}
# Kept distinct but flagged: the support phase (as the authors report it) changes with a synthesis variable
# only, or the loading needed to decide is not reported.
UNCERTAIN = {
    ("10.1039/c6ra28305e", "cz-550"), ("10.1039/c6ra28305e", "cz-650"),
    ("10.1021/cs500979c", "cu/zro2(ii)"), ("10.1021/cs500979c", "cu/zro2(iii)"),
    ("10.1021/cs500979c", "cu/zro2(iv)"), ("10.1021/cs500979c", "cu/zro2(v)"),
    ("10.1016/j.fuel.2024.131111", "5inni3c0.5/fe3o4-400/500"),
    ("10.1021/acscatal.6c03987", "cu-ga2o3"),
}


def main():
    ident = pd.read_csv(SRC, usecols=["group", "doi", "catalyst", "catalyst_key", "T_C"])
    finite = np.isfinite(pd.to_numeric(pd.read_csv(SRC, usecols=["cost_recycled_opt_inlet"]).iloc[:, 0],
                                       errors="coerce").to_numpy())
    ident = ident[finite]
    nkeys = ident.groupby("group")["catalyst_key"].nunique()
    scope = ident[ident["group"].isin(nkeys[nkeys >= 2].index)]
    pairs = scope.drop_duplicates(["group", "catalyst_key"])[["group", "doi", "catalyst_key"]]

    setkey = {(doi, k): lab for doi, sets in SETS.items() for lab, ks in sets.items() for k in ks}
    rows = []
    for g, doi, k in pairs.itertuples(index=False):
        if (doi, k) not in A:
            raise KeyError(f"no annotation for {doi} / {k}")
        comp, load, sup, syn, ev = A[(doi, k)]
        mk = "set:" + setkey[(doi, k)] if (doi, k) in setkey else k
        rows.append(dict(group=g, catalyst_key=k, composition=comp, loading=load, support=sup, synthesis=syn,
                         material_key_strict=mk, uncertain=int((doi, k) in UNCERTAIN), evidence=ev))
    out = pd.DataFrame(rows)
    shared = out.groupby(["group", "material_key_strict"])["catalyst_key"].transform("nunique") > 1
    out.insert(7, "synthesis_only_set", shared.astype(int))
    for (doi, k) in setkey:  # every listed set member must be in scope
        assert ((pairs["doi"] == doi) & (pairs["catalyst_key"] == k)).any(), (doi, k)
    out.to_csv(OUT, index=False, encoding="utf-8")

    n_groups = out["group"].nunique()
    strict_n = out.groupby("group")["material_key_strict"].nunique()
    sets = out[out["synthesis_only_set"] == 1].groupby(["group", "material_key_strict"])["catalyst_key"].apply(list)
    print(f"groups in scope: {n_groups}; (group, key) rows: {len(out)}")
    print(f"synthesis-only sets (group-level): {len(sets)} in {sets.index.get_level_values(0).nunique()} groups")
    for (g, mk), ks in sets.items():
        print(f"  {g} :: {mk} :: {ks}")
    print(f"groups collapsing to one strict catalyst: {(strict_n == 1).sum()}")
    for g in strict_n[strict_n == 1].index:
        print(f"  {g}")
    print(f"uncertain rows: {out['uncertain'].sum()}")


if __name__ == "__main__":
    main()
