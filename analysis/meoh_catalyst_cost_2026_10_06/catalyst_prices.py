"""Catalyst purchase price (EUR/kg) of every literature methanol candidate, from its own extracted composition.

price = sum_i w_i * p_i  +  base
  w_i   mass fraction of element i in the catalyst (metal basis; O, C, H, N carry no price)
  p_i   element price, EUR/kg contained element (ELEMENT_PRICES below; USD -> EUR at the ECB 2025 annual average)
  base  manufacturing / support base cost, calibrated so that commercial Cu/ZnO/Al2O3 (CuO/ZnO/Al2O3 = 60/30/10 wt%)
        costs the anchor's 18.1 EUR/kg (Campos 2022). Variant: the Perez-Fortes 2016 value 95.24 EUR/kg.

Composition comes from the extracted fields of agent/extraction/out/records_normalized.csv (composition,
active_metals, metal_wt_pct, support, promoters, catalyst_name). The rules, one per paper where the paper's notation
needs it, are in PAPER_RULES; every rule is listed with its source text in the README. A catalyst whose composition
cannot be parsed gets the CZA price and the flag "unparsed".

Run as a script: writes element_prices.csv and catalyst_prices.csv (one row per candidate of the literature inversion).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
INV = REPO / "analysis" / "meoh_literature_inversion_2026_10_05"
sys.path.insert(0, str(INV))
from meoh_candidates import read_records  # noqa: E402

USD_PER_EUR_2025 = 1.1299831372549   # ECB reference rate, annual average 2025 (EXR.A.USD.EUR.SP00.A)
CZA_ANCHOR_EUR_KG = 18.1             # anchor (Campos 2022) Cu/ZnO/Al2O3 price, as in the plant benchmark
PEREZ_FORTES_EUR_KG = 95.24          # Perez-Fortes 2016, AE p727; JRC EUR 27629 p37
CZA_COMMERCIAL = {"CuO": 0.60, "ZnO": 0.30, "Al2O3": 0.10}
PRECIOUS = {"Pd", "Pt", "Ir", "Au", "Ag", "Re", "Ru", "Rh", "Os"}
HARNESS_CORE = Path(r"D:/论文-AI4S/Catalyst_Economic_Leverage_Automation_Harness_v0.1/harness_core.py")

# ------------------------------------------------------------------------------------------- element prices ------
# (USD per kg contained element, basis, source, locator). "frozen" = the frozen NH3 model price set
# (harness_core.PRICE, used for every metal of the paper's ammonia results); MCS 2026 = USGS Mineral Commodity
# Summaries 2026, 2025 estimated annual average (first-page salient-statistics table of each chapter).
ELEMENT_PRICES = {
    "Cu": (13.889122517655, "metal", "frozen", "harness_core.PRICE['Cu']"),
    "Pd": (40670.694409279, "metal", "frozen", "harness_core.PRICE['Pd']"),
    "Pt": (51508.71107755406, "metal", "frozen", "harness_core.PRICE['Pt']"),
    "Au": (128732.2322756058, "metal", "frozen", "harness_core.PRICE['Au']"),
    "Ir": (252383.36056351, "metal", "frozen", "harness_core.PRICE['Ir']"),
    "Re": (5757.64, "metal", "frozen", "harness_core.PRICE['Re']"),
    "Ni": (16.9094555095895, "metal", "frozen", "harness_core.PRICE['Ni']"),
    "Co": (56.28401553583051, "metal", "frozen", "harness_core.PRICE['Co']"),
    "Fe": (8.0, "metal", "frozen", "harness_core.PRICE['Fe']"),
    "Ag": (1823.590345370992, "metal", "frozen", "harness_core.PRICE['Ag']"),
    "Ru": (53852.5, "metal", "frozen", "harness_core.PRICE['Ru']"),
    "Rh": (265243.65919095, "metal", "frozen", "harness_core.PRICE['Rh']"),
    # already in the repo: analysis/nh3_alloy_extension_2026_10_05/element_prices_usgs_mcs2026.csv
    "In": (370.0, "metal", "MCS 2026 indium", "Price, annual average, U.S. warehouse, 370 $/kg"),
    "Ga": (580.0, "metal", "MCS 2026 gallium", "Price, average unit value of imports, 580 $/kg"),
    "Zn": (3.2849, "metal", "MCS 2026 zinc", "Price, average, North American, 149 c/lb x 2.20462/100"),
    "Zr": (22.0, "metal (sponge)", "MCS 2026 zirconium-hafnium", "Zirconium, sponge, ex-works China, 22 $/kg; "
           "MCS gives no zirconia price, so ZrO2 is priced at its contained Zr"),
    "Y": (40.0, "metal", "MCS 2026 yttrium", "Yttrium metal, min 99.9 %, 40 $/kg"),
    "La": (1.1728, "oxide (contained La)", "MCS 2026 rare earths", "Lanthanum oxide 99.5 %, 1.00 $/kg La2O3 / 0.85268"),
    "Cd": (3.90, "metal", "MCS 2026 cadmium", "Price, metal, annual average, 3.90 $/kg"),
    # added here (MCS 2026 chapters downloaded from pubs.usgs.gov/periodicals/mcs2026/, page 1 price table)
    "Ce": (1.71 / 0.81408, "oxide (contained Ce)", "MCS 2026 rare earths",
           "Cerium oxide, 99.5 % min, 1.71 $/kg CeO2 / 0.81408 (Ce mass fraction of CeO2)"),
    "Al": (590.0 / 1000.0 / 0.52925, "oxide (contained Al)", "MCS 2026 bauxite and alumina",
           "Alumina, average unit value of imports f.a.s., 590 $/t Al2O3 / 0.52925 (Al mass fraction)"),
    "Ti": (3200.0 / 1000.0 / 0.59934, "oxide (contained Ti)", "MCS 2026 titanium and titanium dioxide",
           "TiO2 pigment, 3,200 $/t / 0.59934 (Ti mass fraction)"),
    "Si": (130.0 * 2.20462 / 100.0, "metal", "MCS 2026 silicon", "Silicon metal, 130 c/lb x 2.20462/100"),
    "Mg": (2500.0 / 1000.0, "metal", "MCS 2026 magnesium metal", "European free market, 2,500 $/t"),
    "Ca": (260.0 / 1000.0 / 0.71469, "oxide (contained Ca)", "MCS 2026 lime",
           "Quicklime, average value at plant, 260 $/t CaO / 0.71469"),
    "K": (1200.0 / 1000.0 / 0.83014, "K2O equivalent", "MCS 2026 potash",
          "Potash, all products f.o.b. mine, 1,200 $/t K2O / 0.83014"),
    "Ba": (210.0 / 1000.0 / 0.58840, "barite (contained Ba)", "MCS 2026 barite",
           "Barite, ground, ex-works, 210 $/t BaSO4 / 0.58840"),
}
NO_PRICE = {"O", "C", "H", "N"}       # carbon supports and templates (CNTs, bamboo powder) carry no price

AW = {"H": 1.008, "C": 12.011, "N": 14.007, "O": 15.999, "Mg": 24.305, "Al": 26.982, "Si": 28.085, "K": 39.098,
      "Ca": 40.078, "Ti": 47.867, "Fe": 55.845, "Co": 58.933, "Ni": 58.693, "Cu": 63.546, "Zn": 65.38, "Ga": 69.723,
      "Y": 88.906, "Zr": 91.224, "Ru": 101.07, "Rh": 102.906, "Pd": 106.42, "Ag": 107.868, "Cd": 112.414,
      "In": 114.818, "Ba": 137.327, "La": 138.905, "Ce": 140.116, "Re": 186.207, "Ir": 192.217, "Pt": 195.084,
      "Au": 196.967, "Os": 190.23}
# oxide a dopant is present as when its loading is given on a metal basis (only used to size the support remainder)
DOPANT_OXIDE = {"In": "In2O3", "Zn": "ZnO", "Y": "Y2O3", "La": "La2O3", "Ca": "CaO", "K": "K2O", "Ba": "BaO",
                "Ga": "Ga2O3", "Mg": "MgO", "Al": "Al2O3", "Ce": "CeO2", "Zr": "ZrO2", "Ti": "TiO2", "Cd": "CdO"}


def formula(f: str) -> dict:
    """'Ce0.4Zr0.6O2' -> {'Ce': 0.4, 'Zr': 0.6, 'O': 2.0}."""
    out = {}
    for el, n in re.findall(r"([A-Z][a-z]?)(\d*\.?\d*)", f):
        out[el] = out.get(el, 0.0) + (float(n) if n else 1.0)
    return out


def mw(f: str) -> float:
    return sum(AW[e] * n for e, n in formula(f).items())


def el_frac(f: str) -> dict:
    m = mw(f)
    return {e: AW[e] * n / m for e, n in formula(f).items()}


def elements(components: dict) -> dict:
    """{formula: mass fraction} -> {element: mass fraction of the catalyst}."""
    out = {}
    for f, w in components.items():
        for e, x in el_frac(f).items():
            out[e] = out.get(e, 0.0) + w * x
    return out


def eur_kg(el: str) -> float:
    return ELEMENT_PRICES[el][0] / USD_PER_EUR_2025


def metal_value(els: dict, only=None) -> float:
    """Value of the contained elements, EUR per kg catalyst."""
    v = 0.0
    for e, w in els.items():
        if e in NO_PRICE or (only is not None and e not in only):
            continue
        v += w * eur_kg(e)
    return v


BASE_EUR_KG = CZA_ANCHOR_EUR_KG - metal_value(elements(CZA_COMMERCIAL))
BASE_PF_EUR_KG = PEREZ_FORTES_EUR_KG - metal_value(elements(CZA_COMMERCIAL))


# ------------------------------------------------------------------------------------------- composition --------
def cation_mix(parts: dict) -> dict:
    """Molar cation ratios {oxide formula per cation: moles} -> mass fractions."""
    m = {f: n * mw(f) for f, n in parts.items()}
    s = sum(m.values())
    return {f: v / s for f, v in m.items()}


def loaded(metal: dict, support, oxides: dict = None) -> dict:
    """Loadings (wt%) on a support. metal: {element: wt% metal basis}; oxides: {oxide: wt%}. Precious metals, Cu,
    Ni and Co count as metal, other dopants as their oxide, when the support remainder is sized. support: a formula
    or a {formula: mass fraction} dict (normalised)."""
    comp = {}
    for el, w in metal.items():
        if el in PRECIOUS or el in ("Cu", "Ni", "Co"):
            comp[el] = comp.get(el, 0.0) + w / 100.0
        else:
            ox = DOPANT_OXIDE[el]
            comp[ox] = comp.get(ox, 0.0) + w / 100.0 / el_frac(ox)[el]
    for ox, w in (oxides or {}).items():
        comp[ox] = comp.get(ox, 0.0) + w / 100.0
    rest = 1.0 - sum(comp.values())
    if rest < -1e-9:
        raise ValueError(f"loadings exceed 100 %: {comp}")
    sup = {support: 1.0} if isinstance(support, str) else support
    s = sum(sup.values())
    for f, x in sup.items():
        comp[f] = comp.get(f, 0.0) + rest * x / s
    return comp


SUPPORTS = {  # extracted support / name token -> formula (or mixture); C = carbon, no price
    "In2O3": "In2O3", "ZrO2": "ZrO2", "CeO2": "CeO2", "TiO2": "TiO2", "ZnO": "ZnO", "Al2O3": "Al2O3",
    "SiO2": "SiO2", "Fe3O4": "Fe3O4", "ZnTiO3": "ZnTiO3", "ZnAl2O4": "ZnAl2O4", "NiO": "NiO", "MgO": "MgO",
}


def support_formula(s: str):
    s = str(s)
    s = re.sub(r"\s*\(.*?\)", "", s)
    s = re.sub(r"^(?:m|t|a|γ|c|h)[-–]", "", s)
    s = re.sub(r"[-–](?:C|R|O|NS|NP|HM|\d)$", "", s)
    if re.fullmatch(r"(?:[A-Z][a-z]?\d*\.?\d*)+", s) and s in SUPPORTS:
        return SUPPORTS[s]
    if re.fullmatch(r"(?:Ti|Ce|Zr)\d?\.?\d*(?:Ti|Ce|Zr)\d?\.?\d*O2", s):     # Ti0.8Ce0.2O2, Ce0.4Zr0.6O2
        f = formula(s)
        return cation_mix({f"{e}O2": n for e, n in f.items() if e != "O"})
    return None


NUM = r"(\d+(?:\.\d+)?)"
MEASURED = re.compile(r"ICP|XRF|measured|actual|real|content", re.I)


def generic_loadings(text: str) -> dict:
    """Metal-basis wt% loadings written as '5 wt% Pd', 'Pd = 0.44 wt%', 'Pd loading of 2.50 wt.%', 'WIn = 10.1%',
    'content of Cu = 10.7%', 'Measured In content = 11.9 wt%'."""
    el = r"(Pd|Pt|Ir|Au|Ag|Re|Ru|Rh|Cu|Ni|Co|In|Zn|Ca|K|Ba|Y|La|Ga|Al|Ce|Zr)"
    out = {}
    pats = [rf"{NUM}\s*wt\.?\s*%\s*{el}\b", rf"\b{el}\s*=\s*{NUM}\s*wt", rf"\bW{el}\s*=\s*{NUM}\s*%",
            rf"\b{el}\s+(?:loading|content)\s*(?:of|=|was fixed at|after reduction =)?\s*{NUM}\s*(?:wt|%)",
            rf"content of {el}\s*=\s*{NUM}\s*%", rf"\b{el}\s*:\s*{NUM}\s*wt"]
    for i, p in enumerate(pats):
        for m in re.finditer(p, text):
            a, b = m.groups()
            e, v = (b, a) if i == 0 else (a, b)
            out.setdefault(e, float(v))
    return out


def oxide_loadings(text: str) -> dict:
    out = {}
    for p in (rf"{NUM}\s*wt\.?\s*%\s*(In2O3|CuO|NiO)\b", rf"\b(In2O3|NiO)\s+(?:content|loading)\s*(?:=|of)?\s*{NUM}\s*wt",
              rf"measured (In2O3) content {NUM}\s*wt"):
        for m in re.finditer(p, text):
            a, b = m.groups()
            ox, v = (b, a) if a[0].isdigit() else (a, b)
            out[ox] = float(v)
    return out


# ---------------------------------------------------------------------- paper rules (name: extracted record) ---
def r_anie2024(name, texts, rec):
    """Ir/Pd single-atom pairs on In2O3: 'Ir1Pd1' = 0.44 wt% Ir + 0.25 wt% Pd (composition field, Ir/Pd molar 0.97);
    a leading factor scales both ('0.5Ir1Pd1' = 0.35 wt%, as the record states), 'IrxPdy' scales each metal."""
    m = re.match(r"(\d*\.?\d*)((?:Ir|Pd)\d+)((?:Ir|Pd)\d+)?-In2O3", name)
    if not m:
        return None
    f = float(m.group(1)) if m.group(1) else 1.0
    load = {}
    for tok in (m.group(2), m.group(3)):
        if tok:
            e, n = tok[:2], float(tok[2:])
            load[e] = load.get(e, 0.0) + f * n * {"Ir": 0.44, "Pd": 0.25}[e]
    return loaded(load, "In2O3"), "Ir1 = 0.44 wt% Ir, Pd1 = 0.25 wt% Pd (composition field), scaled by the name"


def r_cctc2020(name, texts, rec):
    """Pd 5 wt%; PdZn: Pd:Zn = 1:5 molar on the support; the physical mixture is taken as 1:1 by mass."""
    if name in ("ZnO", "TiO2", "ZnTiO3"):
        return {name: 1.0}, "bare support"
    if name.startswith("physical mixture"):
        return ({**{k: 0.5 * v for k, v in loaded({"Pd": 5}, "ZnO").items()}, "TiO2": 0.5},
                "Pd/ZnO (5 wt% Pd) + TiO2, 1:1 by mass assumed (ratio not extracted)", "assumed")
    sup = name.split("/")[1]
    load = {"Pd": 5.0}
    if name.startswith("PdZn"):
        load["Zn"] = 5.0 * 5 * AW["Zn"] / AW["Pd"]
    return loaded(load, SUPPORTS[sup]), "5 wt% Pd; Zn from Pd:Zn = 1:5 molar"


ENTE_IN2O3 = {"Cat-1.5": 9.8, "Cat-3.0": 12.3, "Cat-4.5": 16.4, "Cat-6.0": 6.2, "In2O3-IWI/Al2O3/Al-fiber": 14.6}


def r_ente2018(name, texts, rec):
    """In2O3 content per catalyst (composition field); remainder Al2O3/Al-fiber priced as Al2O3."""
    if name in ENTE_IN2O3:
        return loaded({}, "Al2O3", {"In2O3": ENTE_IN2O3[name]}), "In2O3 content (wt%) from composition field"
    if name == "H-In2O3/Al2O3":
        return (loaded({}, "Al2O3", {"In2O3": 16.4}), "same synthesis as Cat-4.5 (urea/In 4.5); 16.4 wt% In2O3 assumed",
                "assumed")
    return None


def r_capd_zn(name, texts, rec):
    """'0.5Ca5P5ZC' / '5P5ZZr-IMP' / '5PC': wt% Ca, Pd (P), Zn (Z) on CeO2 (C) or ZrO2 (Zr)."""
    m = re.match(r"(?:(\d*\.?\d*)Ca)?(?:(\d*\.?\d*)P)(?:(\d*\.?\d*)Z)?(C|Zr)\b", name)
    if not m:
        return None
    ca, pd_, zn, s = m.groups()
    load = {"Pd": float(pd_)}
    if ca:
        load["Ca"] = float(ca)
    if zn:
        load["Zn"] = float(zn)
    return loaded(load, "CeO2" if s == "C" else "ZrO2"), "name code: wt% Ca, Pd (P), Zn (Z); C = CeO2, Zr = ZrO2"


def r_apcatb2019(name, texts, rec):
    """Pd 2.50 wt%; Pd/ZnO-xAl: x wt% Al in the Zn-Al mixed oxide; ZnO/Al2O3 taken as 1:1 by mass."""
    m = re.match(r"Pd/ZnO-(\d+\.?\d*)Al", name)
    if m:
        a = float(m.group(1)) / 100.0
        al2o3 = a / el_frac("Al2O3")["Al"]
        return loaded({"Pd": 2.5}, {"ZnO": 1 - al2o3, "Al2O3": al2o3}), "2.5 wt% Pd; Al wt% of the Zn-Al oxide from the name"
    sup = {"Pd/ZnO": "ZnO", "Pd/ZnAl2O4": "ZnAl2O4", "Pd/Al2O3": "Al2O3"}.get(name)
    if sup:
        return loaded({"Pd": 2.5}, sup), "2.5 wt% Pd"
    if name == "Pd/ZnO/Al2O3":
        return loaded({"Pd": 2.5}, {"ZnO": 0.5, "Al2O3": 0.5}), "2.5 wt% Pd; ZnO:Al2O3 1:1 by mass assumed", "assumed"
    return None


def r_cattod2020(name, texts, rec):
    """Pd-Cu, Pd/(Pd+Cu) = 0.25 atomic, but the total metal loading is not reported in the paper (it refers to its
    ref. 27): unparsed."""
    return None


def r_cej2022(name, texts, rec):
    """In2O3:HZSM-5 = 2:1 by mass; the zeolite is priced as SiO2 (Si/Al not extracted)."""
    return {"In2O3": 2 / 3, "SiO2": 1 / 3}, "In2O3:HZSM-5 = 2:1 (mass); HZSM-5 priced as SiO2", "assumed"


def r_cej2024(name, texts, rec):
    """Pd-Pt on In2O3: 1 wt% total (the stated composition; metal_wt_pct is filled for only some records of the
    same catalyst), split by the Pd/Pt atomic ratio."""
    tot = 1.0
    if name.startswith("Pd-Pt"):
        m = re.search(r"\((\d):(\d)\)", name)
        a, b = (int(m.group(1)), int(m.group(2))) if m else (1, 1)
        mp, mt = a * AW["Pd"], b * AW["Pt"]
        return loaded({"Pd": tot * mp / (mp + mt), "Pt": tot * mt / (mp + mt)}, "In2O3"), \
            "1 wt% total split by Pd/Pt atomic ratio"
    el = name[:2]
    return loaded({el: tot}, "In2O3"), "1 wt% metal"


def r_fuel2023b(name, texts, rec):
    """y% Zn-CdZrOx: y = Zn wt% (metal basis); Cd:Zr molar = 1.264:9.76 from the recipe (0.39 g Cd(NO3)2.4H2O,
    4.19 g Zr(NO3)4.5H2O; paper section 2.1)."""
    m = re.match(r"(\d+\.?\d*)% Zn-CdZrOx", name)
    if not m:
        return None
    cdzr = cation_mix({"CdO": 1.264, "ZrO2": 9.76})
    return loaded({"Zn": float(m.group(1))}, cdzr), "y = Zn wt%; Cd:Zr = 0.1295 molar from the recipe"


def r_fuel2024(name, texts, rec):
    """xInNi3C0.5/Fe3O4: In x wt%, Ni:In = 3 molar (composition field); C neglected. Fe3O4 bare."""
    if name == "Fe3O4":
        return {"Fe3O4": 1.0}, "bare support"
    m = re.match(r"(\d+\.?\d*)%?InNi3C0\.5/(Fe3O4|SiO2)", name)
    if not m:
        return None
    x = float(m.group(1))
    return loaded({"In": x, "Ni": 3 * x * AW["Ni"] / AW["In"]}, m.group(2)), "In wt% from the name; Ni:In = 3 molar"


def r_jcat2012(name, texts, rec):
    """Measured cation ratios (Pd:Mg:Ga etc.) as oxides, scaled to the measured Pd content; CuZnAl = reference CZA."""
    if name == "CuZnAl":
        return dict(CZA_COMMERCIAL), "reference Cu/ZnO/Al2O3: commercial CZA composition", "cza_reference"
    ratios = {"PdMgGa": {"Pd": 1.0, "MgO": 64.5, "GaO1.5": 34.5}, "PdZnAl": {"Pd": 1.0, "ZnO": 69.5, "AlO1.5": 29.5},
              "PdMgAl": {"Pd": 1.3, "MgO": 69.1, "AlO1.5": 29.6}}.get(name)
    pdw = {"PdMgGa": 1.81, "PdZnAl": 1.46, "PdMgAl": 3.13}.get(name)
    if not ratios:
        return None
    mix = cation_mix(ratios)
    rest = {k: v for k, v in mix.items() if k != "Pd"}
    return loaded({"Pd": pdw}, rest), "measured cation ratio as oxides, measured Pd wt%"


def r_jcou2016(name, texts, rec):
    """CZA-n: Cu + ZnO = T wt%, Cu/Zn molar r (5 lacks r: mean 2.34 of the series), rest Al2O3."""
    t = " ".join(texts)
    T = re.search(r"Cu \+ ZnO = (\d+\.?\d*)", t)
    r = re.search(r"Cu/Zn = (\d+\.?\d*)", t)
    if not T:
        return None
    T = float(T.group(1)) / 100.0
    r = float(r.group(1)) if r else 2.3425
    cu = T * r * AW["Cu"] / (r * AW["Cu"] + mw("ZnO"))
    return {"Cu": cu, "ZnO": T - cu, "Al2O3": 1 - T}, "Cu + ZnO wt% and Cu/Zn molar (composition field); rest Al2O3"


def r_jcou2022(name, texts, rec):
    """Co3O4-In2O3 by Co:In molar (name XY, default 7:3); the bamboo-powder template burns off at 450 C (paper,
    Preparation of catalysts), so no support; 1.04 wt% K on CoIn-N."""
    if name.startswith("In-BP"):
        return {"In2O3": 1.0}, "In2O3 (Co:In = 0:10)"
    if name.startswith("Co-BP"):
        return {"Co3O4": 1.0}, "Co3O4"
    m = re.search(r"CoIn-(\d)(\d)", name)
    co, in_ = (int(m.group(1)), int(m.group(2))) if m else (7, 3)
    mix = cation_mix({"CoO1.3333333": co, "InO1.5": in_})
    if name.startswith("1.04 wt% K"):
        return loaded({"K": 1.04}, mix), "1.04 wt% K on Co:In = 7:3 oxides"
    return mix, f"Co:In = {co}:{in_} molar as Co3O4 + In2O3; template burnt off"


def r_mcat2020(name, texts, rec):
    m = re.match(r"(\d+)-CuO", name)
    return loaded({}, support_formula("Ce0.4Zr0.6O2"), {"CuO": float(m.group(1))}), "x wt% CuO on Ce0.4Zr0.6O2"


def r_iecr2017(name, texts, rec):
    return cation_mix({"CuO": 58, "ZnO": 25, "AlO1.5": 17}), "Cu:Zn:Al = 58:25:17 molar as oxides"


def r_acsaem2021(name, texts, rec):
    """ZnZr: Zn/(Zn+Zr) = 4.40/(4.40+29.5) = 13 % molar from the recipe (1.31 g Zn(NO3)2.6H2O, 12.68 g
    Zr(NO3)4.5H2O); Pd 0.1 wt% unless the name gives it."""
    znzr = cation_mix({"ZnO": 4.40, "ZrO2": 29.54})
    if name == "ZnZr":
        return znzr, "ZnO-ZrO2, Zn/(Zn+Zr) = 13 % molar from the recipe"
    m = re.search(r"(\d+\.?\d*)\s*% ?(?:CP-)?Pd", name)
    w = float(m.group(1)) if m else 0.1
    return loaded({"Pd": w}, znzr), "Pd wt% (name, else 0.1 wt%) on ZnZr"


def r_acsami2021(name, texts, rec):
    """yIn-xCu/CeO2 (paper: x = Cu wt%, y = In wt%)."""
    m = re.match(r"(?:(\d+\.?\d*)In-)?(\d+\.?\d*)Cu/CeO2", name)
    if m:
        load = {"Cu": float(m.group(2))}
        if m.group(1):
            load["In"] = float(m.group(1))
        return loaded(load, "CeO2"), "name: y wt% In, x wt% Cu (paper's notation)"
    if name == "In2O3":
        return {"In2O3": 1.0}, "bulk"
    if name == "Cu/In2O3":
        return loaded({"Cu": 4.8}, "In2O3"), "Cu loading not printed; 4.8 wt% as the Cu/CeO2 reference assumed", "assumed"
    if name == "In2O3/CeO2":
        return loaded({"In": 0.92}, "CeO2"), "In loading not printed; 0.92 wt% assumed", "assumed"
    return None


def r_acscatal2021(name, texts, rec):
    """NiO(x)-In2O3: x wt% NiO; M-In2O3: 5 wt% M (metal basis)."""
    if name in ("In2O3", "NiO"):
        return {name: 1.0}, "bulk"
    m = re.match(r"NiO\((\d+)\)", name)
    if m:
        return loaded({}, "In2O3", {"NiO": float(m.group(1))}), "x wt% NiO in In2O3"
    m = re.match(r"(Ni|Pd|Cu|Co)-In2O3", name)
    if m:
        return loaded({m.group(1): 5.0}, "In2O3"), "5 wt% M promoted In2O3"
    return None


def r_9b03305(name, texts, rec):
    """xIn2O3-yZrO2 by measured In mol % of cations; In2O3/support 'measured In2O3 content' wt%."""
    t = " ".join(texts)
    m = re.search(r"measured In content (\d+\.?\d*) mol", t)
    if m:
        x = float(m.group(1))
        return cation_mix({"InO1.5": x, "ZrO2": 100 - x}), "measured In mol % of cations, as InO1.5 + ZrO2"
    m = re.search(r"measured In2O3 content (\d+\.?\d*)", t)
    if m:
        sup = support_formula(rec.support)
        return loaded({}, sup, {"In2O3": float(m.group(1))}), "measured In2O3 wt%"
    return None


def r_cs500979c(name, texts, rec):
    """Cu/ZrO2: 10 (or 15) atom % Cu of cations, Cu metallic."""
    if name == "ZrO2":
        return {"ZrO2": 1.0}, "bulk"
    t = " ".join(texts)
    m = re.search(r"(\d+) atom % of Cu", t)
    x = float(m.group(1)) / 100.0
    return cation_mix({"Cu": x, "ZrO2": 1 - x}), "atom % Cu of cations, Cu metal + ZrO2"


def r_c2cy(name, texts, rec):
    """Cu/Al2O3 = 18/82 wt%; Cu-M: 5 wt% M + 95 wt% Cu/Al2O3."""
    base = {"Cu": 0.18, "Al2O3": 0.82}
    m = re.match(r"Cu[–-](Ba|K)/Al2O3", name)
    if m:
        ox = DOPANT_OXIDE[m.group(1)]
        c = {k: 0.95 * v for k, v in base.items()}
        c[ox] = 0.05 / el_frac(ox)[m.group(1)]
        s = sum(c.values())
        return {k: v / s for k, v in c.items()}, "5 wt% Ba or K on 95 wt% Cu/Al2O3 (18/82)"
    return base, "Cu/Al2O3 = 18/82 wt%"


def r_c5cy(name, texts, rec):
    """Cu:Zn:(Al+Y) = 2:1:1 molar, Y/(Al+Y) from the name, as oxides."""
    y = float(re.search(r"Y(\d*\.?\d+)", name).group(1))
    return cation_mix({"CuO": 2, "ZnO": 1, "AlO1.5": 1 - y, "YO1.5": y}), "Cu:Zn:(Al+Y) = 2:1:1 molar, oxides"


def r_c5ra(name, texts, rec):
    t = " ".join(texts)
    cu = float(re.search(r"actual Cu (\d+\.?\d*)", t).group(1))
    zr = float(re.search(r"ZrO2 (\d+\.?\d*) wt", t).group(1))
    return {"Cu": cu / 100, "ZrO2": zr / 100, "C": 1 - (cu + zr) / 100}, \
        "actual Cu and ZrO2 wt%; rest CNTs (carbon, no price)", "carbon"


def r_c6ra(name, texts, rec):
    cu = float(rec.metal_wt_pct)
    return {"Cu": cu / 100, "ZrO2": 1 - cu / 100}, "Cu wt% (metal_wt_pct); rest ZrO2"


def r_sciadv2017(name, texts, rec):
    """x% ZnO-ZrO2: Zn/(Zn+Zr) = x % molar."""
    if name in ("ZnO", "ZrO2"):
        return {name: 1.0}, "bulk"
    x = float(re.match(r"(\d+)%", name).group(1))
    return cation_mix({"ZnO": x, "ZrO2": 100 - x}), "Zn/(Zn+Zr) molar as ZnO + ZrO2"


INNI = {"In": AW["In"], "Ni": 3 * AW["Ni"], "C": 0.5 * AW["C"]}


def r_sciadv2021(name, texts, rec):
    """InNi3C0.5 on supports: measured In and Ni wt% where given, else the InNi3C0.5 loading (42.8 wt% for the
    ZrO2/SiO2 series, 11.4 wt% on Fe3O4); ZnO, CeO2, TiO2 supports take the 42.8 wt% of the series (assumed)."""
    if name in ("m-ZrO2", "t-ZrO2", "a-ZrO2", "SiO2"):
        return {support_formula(name): 1.0}, "bare support"
    if name == "CuZnAl":
        return dict(CZA_COMMERCIAL), "reference Cu/ZnO/Al2O3: commercial CZA composition", "cza_reference"
    sup = support_formula(name.split("/")[1])
    t = " ".join(texts)
    m = re.search(r"real In content (\d+\.?\d*) wt%, Ni content (\d+\.?\d*) wt%", t)
    if m:
        return loaded({"In": float(m.group(1)), "Ni": float(m.group(2))}, sup), "measured In and Ni wt%"
    m = re.search(r"(\d+\.?\d*) wt ?% InNi3C0\.5|InNi3C0\.5 loading = (\d+\.?\d*)", t)
    flag = ()
    if m:
        L = float(m.group(1) or m.group(2))
    else:
        L, flag = 42.8, ("assumed",)
    s = sum(INNI.values())
    return (loaded({"In": L * INNI["In"] / s, "Ni": L * INNI["Ni"] / s}, sup),
            f"InNi3C0.5 loading {L} wt% split by stoichiometry", *flag)


PAPER_RULES = {
    "10.1002/anie.202401168": r_anie2024, "10.1002/cctc.202000974": r_cctc2020, "10.1002/ente.201800747": r_ente2018,
    "10.1016/j.apcata.2018.04.036": r_capd_zn, "10.1016/j.cattod.2019.05.040": r_capd_zn,
    "10.1016/j.apcatb.2019.118367": r_apcatb2019, "10.1016/j.cattod.2020.05.049": r_cattod2020,
    "10.1016/j.cej.2022.135090": r_cej2022, "10.1016/j.cej.2024.149370": r_cej2024,
    "10.1016/j.fuel.2023.128376": r_fuel2023b, "10.1016/j.fuel.2024.131111": r_fuel2024,
    "10.1016/j.jcat.2012.05.020": r_jcat2012, "10.1016/j.jcou.2016.11.015": r_jcou2016,
    "10.1016/j.jcou.2022.102209": r_jcou2022, "10.1016/j.mcat.2020.111105": r_mcat2020,
    "10.1021/acs.iecr.7b01464": r_iecr2017, "10.1021/acsaem.1c01502": r_acsaem2021,
    "10.1021/acsami.1c05586": r_acsami2021, "10.1021/acscatal.1c03170": r_acscatal2021,
    "10.1021/acscatal.9b03305": r_9b03305, "10.1021/cs500979c": r_cs500979c, "10.1039/c2cy20604h": r_c2cy,
    "10.1039/c5cy00372e": r_c5cy, "10.1039/c5ra04774a": r_c5ra, "10.1039/c6ra28305e": r_c6ra,
    "10.1126/sciadv.1701290": r_sciadv2017, "10.1126/sciadv.abi6012": r_sciadv2021,
}


def r_generic(name, texts, rec):
    """Bulk oxide names, the commercial-CZA reference, and 'loading on support' records: metal-basis loadings from
    the composition text (measured values preferred), else metal_wt_pct with active_metals, else a loading in the
    name ('Cu(15)ZnO', 'In13/ZrO2', 'Ir/In2O3-10', '2Pd/CeO2'); oxide loadings ('2.5 wt% In2O3', 'NiO loading');
    the remainder is the support (support field, else the name)."""
    bare = re.sub(r"\s*\(.*?\)|^(?:bulk|Pristine|High-purity)\s+|^[hc][-–]|-(?:R|S|P|L|NS|NP|HM)$", "", name).strip()
    if bare in ("In2O3", "ZrO2", "TiO2", "ZnO", "Fe3O4", "NiO", "SiO2") or name.lower().startswith("bulk in2o3"):
        return {"In2O3" if "In2O3" in bare or "In2O3" in name else bare: 1.0}, "bulk oxide"
    if re.fullmatch(r"(Cu-ZnO-Al2O3|CuZnAl|CZA)", name):
        return dict(CZA_COMMERCIAL), "reference Cu/ZnO/Al2O3: commercial CZA composition", "cza_reference"
    sup = support_formula(rec.support) if pd.notna(rec.support) else None
    if sup is None:
        m = re.search(r"/([A-Za-z0-9.]+)", name)
        sup = support_formula(m.group(1)) if m else None
    if sup is None and (re.search(r"In2O3", name) or any("promoted In2O3" in t for t in texts)):
        sup = "In2O3"
    if sup is None:
        return None
    def read(ts):
        load, ox = {}, {}
        for t in ts:
            for k, v in generic_loadings(t).items():
                load.setdefault(k, v)
            for k, v in oxide_loadings(t).items():
                ox.setdefault(k, v)
        return load, ox

    # the record's own composition text first: a paper may reuse one name for a loading series ("CP" = 0.25-10 wt%
    # Pd in Snider 2019). Records of the same name fill a missing text, and supply a measured value only when every
    # nominal value under that name equals the record's own.
    own = [rec.own_text] if rec.own_text else []
    sibs = [t for t in texts if t not in own]
    meas = [t for t in sibs if MEASURED.search(t)]
    o_load, o_ox = read(own)
    m_load, m_ox = read(meas)
    if o_load or o_ox:
        nominal = [read([t]) for t in sibs if t not in meas]
        same = all(n == (o_load, o_ox) for n in nominal if n[0] or n[1])
        if own and not MEASURED.search(own[0]) and (m_load or m_ox) and same and set(m_load) == set(o_load):
            return loaded(m_load, sup, m_ox), "loading from composition text (measured, same-name record)"
        return loaded(o_load, sup, o_ox), "loading from composition text" + (" (measured)" if MEASURED.search(own[0]) else "")
    for ts, tag in ((meas, " (measured, same-name record)"), (sibs, " (same-name record)")):
        load, ox = read(ts)
        if load or ox:
            return loaded(load, sup, ox), "loading from composition text" + tag
    if pd.notna(rec.metal_wt_pct) and pd.notna(rec.active_metals) and ";" not in str(rec.active_metals):
        return loaded({rec.active_metals: float(rec.metal_wt_pct)}, sup), "metal_wt_pct of active_metals"
    for p, rule in ((r"^(Cu)\((\d+\.?\d*)\)", "name Cu(x)"), (r"^(In)(\d+\.?\d*)/", "name Inx/"),
                    (r"^(Ir)/In2O3-(\d+)", "name Ir/In2O3-x"), (r"^(\d+\.?\d*)(Pd|Pt|Cu|Ni)", "name xM")):
        m = re.match(p, name)
        if m:
            a, b = m.groups()
            el, v = (b, a) if a[0].isdigit() else (a, b)
            return loaded({el: float(v)}, sup), rule
    return None


def parse(name, texts, rec):
    """-> (components, rule, flag) or (None, reason, 'unparsed')."""
    rule = PAPER_RULES.get(rec.doi, r_generic)
    try:
        out = rule(name, texts, rec)
        if out is None and rule is not r_generic and rec.doi != "10.1016/j.cattod.2020.05.049":
            out = r_generic(name, texts, rec)
    except (ValueError, AttributeError, KeyError, TypeError) as e:
        return None, f"parse error: {e}", "unparsed"
    if out is None:
        doc = (rule.__doc__ or "").split("\n")[0] if rule is r_cattod2020 else "composition not parseable"
        return None, doc, "unparsed"
    comp, why = out[0], out[1]
    flag = out[2] if len(out) > 2 else ""
    return comp, why, flag


def price_table(comp) -> dict:
    els = elements(comp)
    mv = metal_value(els)
    return dict(elements={k: v for k, v in els.items() if k not in NO_PRICE and v > 1e-9},
                metal_value_eur_kg=mv, precious_value_eur_kg=metal_value(els, PRECIOUS),
                price_eur_kg=mv + BASE_EUR_KG, price_pf_base_eur_kg=mv + BASE_PF_EUR_KG)


def build(cand: pd.DataFrame) -> pd.DataFrame:
    rec = read_records()
    texts = {}
    for r in rec.itertuples():
        bits = [str(x) for x in (r.composition,) if pd.notna(x)]
        texts.setdefault((r.doi, r.catalyst_name), []).extend(bits)
    cza = price_table(CZA_COMMERCIAL)
    rows = []
    recs = rec.set_index(["doi", "entry_label"]).sort_index()
    for c in cand.itertuples():
        r = recs.loc[(c.doi, c.entry)]
        if isinstance(r, pd.DataFrame):
            r = r.iloc[0]
        r = pd.Series(r).copy()
        r["doi"] = c.doi
        r["own_text"] = str(r.composition) if pd.notna(r.composition) else ""
        name = str(r.catalyst_name)
        tx = list(dict.fromkeys(texts.get((c.doi, name), [])))
        rr = type("R", (), r.to_dict())
        comp, why, flag = parse(name, tx, rr)
        p = price_table(comp) if comp is not None else cza
        rows.append(dict(group=c.group, doi=c.doi, entry=c.entry, catalyst_name=name,
                         composition_field=r.composition, active_metals=r.active_metals,
                         metal_wt_pct=r.metal_wt_pct, support_field=r.support, promoters=r.promoters,
                         parsed_components=";".join(f"{k}={v:.4f}" for k, v in comp.items()) if comp else "",
                         element_wt_pct=";".join(f"{k}={100 * v:.3f}" for k, v in sorted(p["elements"].items(),
                                                                                         key=lambda kv: -kv[1])),
                         metal_value_eur_kg=p["metal_value_eur_kg"], precious_value_eur_kg=p["precious_value_eur_kg"],
                         price_eur_kg=p["price_eur_kg"], price_pf_base_eur_kg=p["price_pf_base_eur_kg"],
                         rule=why, flag=flag))
    return pd.DataFrame(rows)


def element_table() -> pd.DataFrame:
    rows = [dict(element=e, price_USD_per_kg=v[0], price_EUR_per_kg=v[0] / USD_PER_EUR_2025, basis=v[1], source=v[2],
                 locator=v[3]) for e, v in ELEMENT_PRICES.items()]
    return pd.DataFrame(rows)


def check_frozen_prices():
    """The frozen NH3 price set is read back from harness_core.py when it is present."""
    if not HARNESS_CORE.exists():
        return "harness_core.py not found; constants used as stored"
    src = HARNESS_CORE.read_text(encoding="utf-8")
    block = src[src.index("PRICE = {"):src.index("}", src.index("PRICE = {"))]
    frozen = {k: float(v) for k, v in re.findall(r"'([A-Z][a-z]?)':\s*([\d.]+)", block)}
    for e, v in ELEMENT_PRICES.items():
        if v[2] == "frozen":
            assert abs(frozen[e] - v[0]) < 1e-9 * v[0], (e, frozen[e], v[0])
    return "frozen prices equal harness_core.PRICE"


if __name__ == "__main__":
    print(check_frozen_prices())
    cand = pd.read_csv(INV / "literature_candidates.csv")
    out = build(cand)
    element_table().to_csv(HERE / "element_prices.csv", index=False, float_format="%.6g")
    out.to_csv(HERE / "catalyst_prices.csv", index=False, float_format="%.6g")
    print(f"base {BASE_EUR_KG:.4f} EUR/kg (PF {BASE_PF_EUR_KG:.4f}); CZA check "
          f"{price_table(CZA_COMMERCIAL)['price_eur_kg']:.4f}")
    print(out.flag.replace("", "ok").value_counts())
    print(out.price_eur_kg.describe())
