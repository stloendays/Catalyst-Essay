"""Convert extracted records (out/raw/*.json) to the methanol-model basis.

Usage:
    python normalize.py          -> out/records_normalized.csv

Model basis
    T_K            K            (°C + 273.15)
    P_bar          bar          (MPa x 10, atm x 1.01325, kPa / 100, psi x 0.0689476)
    H2_CO2         molar ratio
    X_CO2_pct, S_MeOH_pct, S_CO_pct, S_CH4_pct    % (a fraction <= 1 with unit 'fraction' is x100)
    GHSV_NL_gcat_h NL (g cat)-1 h-1, only for mass-based GHSV/WHSV; volume-based
                   GHSV (h-1) needs a bed density and is left in GHSV_raw
    cat_mass_g     g
    STY_g_gcat_h   g MeOH (g cat)-1 h-1   (sty_basis per_g_catalyst)
    STY_g_gmetal_h g MeOH (g metal)-1 h-1 (sty_basis per_g_metal)
                   A basis written in the unit (kg_cat, g_Re ...) overrides an extracted
                   sty_basis of 'other'/'unspecified'. A per-metal STY is also expressed per g
                   catalyst (x metal wt% / 100) when the record states the metal loading;
                   STY_gcat_from_metal marks these.
    metal_wt_pct   sum of components with role active_metal whose loading unit is wt%
Each converted value keeps its qualifier (=, <, ~ ...) in a *_q column; raw
value+unit strings are kept so every conversion can be audited.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
RAW_DIR = HERE / "out" / "raw"
M_MEOH = 32.042  # g/mol


def _clean(u: str | None) -> str:
    if u is None:
        return ""
    s = u.strip()
    for a, b in (("−", "-"), ("–", "-"), ("⁻¹", "-1"), ("⁻", "-"), ("¹", "1"), ("·", " "), ("⋅", " "),
                 ("μ", "u"), ("µ", "u"), ("℃", "°C"), ("^", ""), ("·", " ")):
        s = s.replace(a, b)
    return s


def temp_K(v, u):
    if v is None:
        return None
    s = _clean(u).lower().replace(" ", "")
    if s in ("k", "kelvin"):
        return v
    if s in ("°c", "oc", "c", "degc", "deg.c", "celsius", "ºc"):
        return round(v + 273.15, 2)
    return None


def press_bar(v, u):
    if v is None:
        return None
    s = _clean(u).lower().replace(" ", "")
    f = {"bar": 1, "bara": 1, "barg": 1, "mpa": 10, "atm": 1.01325, "kpa": 0.01, "psi": 0.0689476, "psig": 0.0689476}.get(s)
    return None if f is None else round(v * f, 6)


def pct(v, u):
    if v is None:
        return None
    s = _clean(u).lower()
    if s in ("", "%", "percent", "mol%", "c-mol%", "mol %", "% c"):
        return v
    if s in ("fraction", "-"):
        return v * 100
    return v


# --- composite units (GHSV, STY) -------------------------------------------------
_PREFIX = {"": 1.0, "k": 1e3, "m": 1e-3, "u": 1e-6, "n": 1e-9}
_TOKEN = re.compile(
    r"(?P<pre>[kmun]?)(?P<base>mol|ml|nml|nl|l|g|hours|hour|hr|h|min|s|cm3)"
    r"(?P<label>[_ ]?(?:cat|catalyst|meoh|ch3oh|methanol|metal|cu|in|in2o3|pd|re|zn|ir|pt|au|ni|co))?"
    r"(?P<exp>-?\d)?$")


def _parse(unit: str):
    """Return list of (prefix, base, label, exponent). None if a token is not understood."""
    s = _clean(unit).lower()
    s = s.replace("gcat", "g_cat").replace("kgcat", "kg_cat")
    s = re.sub(r"\bnml", "ml", s)            # normal mL / L: same number, STP basis
    s = re.sub(r"\bnl(?=[\s/_-]|$)", "l", s)
    num, *dens = s.split("/")
    parts = [(num, 1)] + [(d, -1) for d in dens]
    out = []
    for part, sign in parts:
        part = part.replace("(", " ").replace(")", " ").replace("*", " ")
        # glue labels written after a space: 'g ch3oh' -> 'g_ch3oh'
        part = re.sub(r"\b(k?g|m?mol|umol)\s+(ch3oh|meoh|methanol|cat|catalyst|metal)\b", r"\1_\2", part)
        part = re.sub(r"\b(k?g)\s?(re|cu|pd|in|zn|ir|pt|au)\b(?=\s|-|$)", r"\1_\2", part)
        for tok in part.split():
            m = _TOKEN.match(tok)
            if not m:
                return None
            exp = int(m.group("exp")) if m.group("exp") else 1
            base = m.group("base")
            pre = m.group("pre")
            if base in ("nml", "nl"):
                pre, base = ("m" if base == "nml" else ""), ("ml" if base == "nml" else "l")
            if base == "ml":
                pre, base = "m", "l"
            if base == "cm3":
                pre, base = "m", "l"
            if base in ("hr", "hour", "hours"):
                base = "h"
            if base == "min" or base == "mol" or base == "l" or base == "g" or base == "h" or base == "s":
                pass
            out.append((pre, base, (m.group("label") or "").strip("_ "), exp * sign))
    return out


def _time_factor(tokens):
    f = 1.0
    for pre, base, _, e in tokens:
        if base == "h":
            f *= 1.0 ** e
        elif base == "min":
            f *= (1 / 60) ** e
        elif base == "s":
            f *= (1 / 3600) ** e
    return f  # multiply a 'per <time>' value by this to get 'per h'


def ghsv_NL_gcat_h(v, u, basis):
    """mL g-1 h-1, L g-1 h-1, L kg-1 h-1, mL g-1 min-1 ... -> NL g-1 h-1."""
    if v is None or basis != "per_mass_catalyst":
        return None
    t = _parse(u or "")
    if not t:
        return None
    vol = [x for x in t if x[1] == "l" and x[3] == 1]
    mass = [x for x in t if x[1] == "g" and x[3] == -1]
    tim = [x for x in t if x[1] in ("h", "min", "s") and x[3] == -1]
    if len(vol) != 1 or len(mass) != 1 or len(tim) != 1:
        return None
    val = v * _PREFIX[vol[0][0]] / _PREFIX[mass[0][0]]
    # per min -> per h: x60 ; per s -> x3600
    val *= {"h": 1, "min": 60, "s": 3600}[tim[0][1]]
    return val


def sty_g_g_h(v, u):
    """Methanol amount per catalyst/metal mass per time -> g MeOH g-1 h-1."""
    if v is None:
        return None
    t = _parse(u or "")
    if not t:
        return None
    amt = [x for x in t if x[1] in ("g", "mol") and x[3] == 1]
    mass = [x for x in t if x[1] == "g" and x[3] == -1]
    tim = [x for x in t if x[1] in ("h", "min", "s") and x[3] == -1]
    if len(amt) != 1 or len(mass) != 1 or len(tim) != 1:
        return None
    pre, base, _, _ = amt[0]
    grams = v * _PREFIX[pre] * (M_MEOH if base == "mol" else 1.0)
    grams /= _PREFIX[mass[0][0]]
    grams *= {"h": 1, "min": 60, "s": 3600}[tim[0][1]]
    return grams


def flow_NL_h(v, u):
    """mL min-1, NmL min-1, cm3 min-1, sccm, L h-1 ... -> NL h-1 (flows are taken as reported at STP)."""
    if v is None:
        return None
    s = _clean(u).lower().strip()
    if s in ("sccm", "ml/min (stp)"):
        return v * 60 / 1000
    t = _parse(s)
    if not t:
        return None
    vol = [x for x in t if x[1] == "l" and x[3] == 1]
    tim = [x for x in t if x[1] in ("h", "min", "s") and x[3] == -1]
    if len(vol) != 1 or len(tim) != 1 or len(t) != 2:
        return None
    return v * _PREFIX[vol[0][0]] * {"h": 1, "min": 60, "s": 3600}[tim[0][1]]


def mass_g(v, u):
    if v is None:
        return None
    s = _clean(u).lower().replace(" ", "")
    return {"g": v, "mg": v / 1000, "kg": v * 1000}.get(s)


def ratio(v, u):
    return v


_METAL_LABELS = {"metal", "cu", "in", "pd", "re", "zn", "ir", "pt", "au", "ni", "co"}


def sty_basis_from_unit(unit):
    """Basis written into the unit itself (g_cat / kg_cat -> catalyst, g_Re / g_metal -> metal), else None."""
    t = _parse(unit or "")
    if not t:
        return None
    mass = [x for x in t if x[1] == "g" and x[3] == -1]
    if len(mass) != 1 or not mass[0][2]:
        return None
    lab = mass[0][2]
    if lab in ("cat", "catalyst"):
        return "per_g_catalyst"
    if lab in _METAL_LABELS:
        return "per_g_metal"
    return None


def metal_wt(components):
    vals = [c["loading"]["value"] for c in components
            if c["role"] == "active_metal" and c["loading"]["value"] is not None
            and re.fullmatch(r"\s*wt\s?%\s*", c["loading"]["unit"] or "")]
    return sum(vals) if vals else None


def normalize_record(doi: str, r: dict) -> dict:
    def q(k):
        return r[k]["qualifier"]

    def raw(k):
        n = r[k]
        return None if n["value"] is None else f"{n['value']} {n['unit'] or ''}".strip()

    sty_raw = sty_g_g_h(r["methanol_sty"]["value"], r["methanol_sty"]["unit"])
    # An explicit basis in the unit (mmol kgcat-1 h-1, g gRe-1 h-1) overrides an 'other'/'unspecified' label.
    basis = r["sty_basis"]
    unit_basis = sty_basis_from_unit(r["methanol_sty"]["unit"])
    if basis in ("other", "unspecified") and unit_basis:
        basis = unit_basis
    m_wt = metal_wt(r["components"])
    sty_cat = sty_raw if basis == "per_g_catalyst" else None
    sty_metal = sty_raw if basis == "per_g_metal" else None
    # per g metal -> per g catalyst with the stated metal loading (wt%); marked as derived
    sty_cat_derived = False
    if sty_cat is None and sty_metal is not None and m_wt:
        sty_cat = sty_metal * m_wt / 100
        sty_cat_derived = True
    row = {
        "doi": doi,
        "entry_label": r["entry_label"],
        "catalyst_name": r["catalyst_name"],
        "composition": r["composition"],
        "support": r["support"],
        "promoters": ";".join(r["promoters"]),
        "preparation": r["preparation"],
        "active_metals": ";".join(c["component"] for c in r["components"] if c["role"] == "active_metal"),
        "metal_wt_pct": m_wt,
        "T_K": temp_K(r["temperature"]["value"], r["temperature"]["unit"]),
        "P_bar": press_bar(r["pressure"]["value"], r["pressure"]["unit"]),
        "H2_CO2": ratio(r["h2_co2_ratio"]["value"], r["h2_co2_ratio"]["unit"]),
        "feed": r["feed_composition"],
        "GHSV_NL_gcat_h": ghsv_NL_gcat_h(r["ghsv"]["value"], r["ghsv"]["unit"], r["ghsv_basis"]),
        "GHSV_raw": raw("ghsv"),
        "ghsv_basis": r["ghsv_basis"],
        "cat_mass_g": mass_g(r["catalyst_mass"]["value"], r["catalyst_mass"]["unit"]),
        "TOS_raw": raw("time_on_stream"),
        "X_CO2_pct": pct(r["co2_conversion"]["value"], r["co2_conversion"]["unit"]),
        "X_CO2_q": q("co2_conversion"),
        "S_MeOH_pct": pct(r["selectivity_ch3oh"]["value"], r["selectivity_ch3oh"]["unit"]),
        "S_MeOH_q": q("selectivity_ch3oh"),
        "S_CO_pct": pct(r["selectivity_co"]["value"], r["selectivity_co"]["unit"]),
        "S_CO_q": q("selectivity_co"),
        "S_CH4_pct": pct(r["selectivity_ch4"]["value"], r["selectivity_ch4"]["unit"]),
        "S_CH4_q": q("selectivity_ch4"),
        "selectivity_basis": r["selectivity_basis"],
        "STY_g_gcat_h": sty_cat,
        "STY_g_gmetal_h": sty_metal,
        "STY_gcat_from_metal": sty_cat_derived,
        "STY_raw": raw("methanol_sty"),
        "sty_basis": basis,
        "sty_basis_extracted": r["sty_basis"],
        "STY_q": q("methanol_sty"),
        "data_source_type": r["data_source_type"],
        "primary_location": r["primary_location"],
        "primary_page": r["primary_page"],
        "notes": r["notes"],
    }
    flags = []
    if r["temperature"]["value"] is not None and row["T_K"] is None:
        flags.append("T_unit")
    if r["pressure"]["value"] is not None and row["P_bar"] is None:
        flags.append("P_unit")
    if r["methanol_sty"]["value"] is not None and sty_raw is None:
        flags.append("STY_unit")
    if r["ghsv"]["value"] is not None and r["ghsv_basis"] == "per_mass_catalyst" and row["GHSV_NL_gcat_h"] is None:
        flags.append("GHSV_unit")
    # GHSV from total flow / catalyst mass when the paper gives no mass-based GHSV (schema v2 field)
    tf = r.get("total_flow") or {}
    row["flow_NL_h"] = flow_NL_h(tf.get("value"), tf.get("unit"))
    row["ghsv_derived"] = False
    if row["GHSV_NL_gcat_h"] is None and row["flow_NL_h"] and row["cat_mass_g"]:
        row["GHSV_NL_gcat_h"] = row["flow_NL_h"] / row["cat_mass_g"]
        row["ghsv_derived"] = True
    row["flags"] = ";".join(flags)
    return row


def main() -> None:
    rows = []
    for f in sorted(RAW_DIR.glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        doi = d.get("doi") or f.stem
        for r in d["records"]:
            rows.append(normalize_record(doi.lower(), r))
    df = pd.DataFrame(rows)
    df.to_csv(HERE / "out" / "records_normalized.csv", index=False, encoding="utf-8")
    print(f"{len(df)} records from {df.doi.nunique()} papers -> out/records_normalized.csv")
    bad = df["flags"].astype(bool)
    if bad.any():
        print(df[bad][["doi", "entry_label", "flags", "STY_raw", "GHSV_raw"]].to_string())


if __name__ == "__main__":
    main()
