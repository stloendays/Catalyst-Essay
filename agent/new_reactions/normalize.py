"""Normalise the raw LLM records (raw/<rxn>/*.json) into one table per reaction (data/<rxn>_records.csv):
SI units, fractions, catalyst composition by element, and the plant-model inputs. Unit handling only; the
extracted values themselves are not changed. Derived quantities (productivity from flow x conversion x selectivity,
first-order deactivation constant from initial/final conversion) are computed here and flagged."""
from __future__ import annotations

import csv
import json
import math
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MW = {"C3H8": 44.097, "C3H6": 42.081, "CH4": 16.043, "CO2": 44.010, "H2": 2.016}
OXIDE_METAL = {"WO3": ("W", 183.84 / 231.84), "Cr2O3": ("Cr", 103.99 / 151.99), "Ga2O3": ("Ga", 139.44 / 187.44),
               "V2O5": ("V", 101.88 / 181.88), "ZnO": ("Zn", 65.38 / 81.38), "In2O3": ("In", 229.64 / 277.64),
               "CoO": ("Co", 58.93 / 74.93), "Co3O4": ("Co", 176.80 / 240.80), "NiO": ("Ni", 58.69 / 74.69),
               "Fe2O3": ("Fe", 111.69 / 159.69), "MoO3": ("Mo", 95.95 / 143.95), "CeO2": ("Ce", 140.12 / 172.12),
               "ZrO2": ("Zr", 91.22 / 123.22), "MnO2": ("Mn", 54.94 / 86.94), "La2O3": ("La", 277.81 / 325.81)}
RHO_BED_KG_L = 1.0   # bed density for volume-based GHSV (assumption; varied 0.5-1.5 in the sensitivity)
SUPPORT_WORDS = ("SiO2", "Al2O3", "TiO2", "ZrO2", "CeO2", "MgO", "SBA", "MCM", "zeolite", "ZSM", "Beta", "carbon",
                 "C", "USY", "Y2O3", "MgAl", "hydrotalcite", "siloxene", "foam")


def num(d):
    return None if not d or d.get("value") is None else float(d["value"])


def temp_K(d):
    v = num(d)
    if v is None:
        return None
    u = (d.get("unit") or "").replace(" ", "")
    return v if u.upper().startswith("K") or (v > 450 and "C" not in u) else v + 273.15


def pres_bar(d):
    v, u = num(d), (d.get("unit") or "").lower() if d else ""
    if "atmospher" in u or "ambient" in u:
        return 1.01325
    if v is None:
        return None
    m = re.search(r"10\s*\^?\s*([-+]?\d+)", u)
    if m and ("×" in u or "x" in u):
        v *= 10 ** int(m.group(1))
        u = u[m.end():]
    for k, f in (("mpa", 10), ("kpa", 0.01), ("atm", 1.01325), ("psi", 0.0689476), ("bar", 1), ("pa", 1e-5)):
        if k in u:
            return v * f
    return v


def frac(d):
    v = num(d)
    return None if v is None else (v / 100 if (d.get("unit") or "%").strip().startswith("%") or v > 1 else v)


def hours(d):
    v = num(d)
    if v is None:
        return None
    u = (d.get("unit") or "h").lower()
    return v / 60 if u.startswith("min") else v * 24 if u.startswith("d") else v


def mass_g(d):
    v = num(d)
    if v is None:
        return None
    u = (d.get("unit") or "g").lower()
    return v / 1000 if u.startswith("mg") else v * 1000 if u.startswith("kg") else v


def flow_ml_min(d):
    v = num(d)
    if v is None:
        return None
    u = (d.get("unit") or "").lower().replace(" ", "")
    if "l" in u and "ml" not in u:
        v *= 1000
    if "/s" in u or "s-1" in u or "s^-1" in u:
        v *= 60
    if "/h" in u or "h-1" in u:
        v /= 60
    return v


SPECIES = {"c3h8": "C3H8", "propane": "C3H8", "h2": "H2", "co2": "CO2", "n2": "N2", "he": "He", "ar": "Ar",
           "c3h6": "C3H6", "ch4": "CH4", "co": "CO"}


def feed_fraction(text, species):
    """Mole fraction of `species` from a feed string like 'C3H8:H2:He = 3.9:5.0:40' or '20% C3H8/N2'."""
    if not text:
        return None
    t = text.replace("₂", "2").replace("₃", "3").replace("₈", "8").replace("₄", "4")
    m = re.search(r"([A-Za-z][A-Za-z0-9]*(?:\s*[:/]\s*[A-Za-z][A-Za-z0-9]*)+)[^\d]{0,40}?"
                  r"([\d.]+(?:\s*[:/]\s*[\d.]+)+)", t)
    if m:
        names = [SPECIES.get(s.strip().lower()) for s in re.split(r"[:/]", m.group(1))]
        vals = [float(v) for v in re.split(r"[:/]", m.group(2))]
        if len(names) == len(vals) and species in names and all(names):
            return vals[names.index(species)] / sum(vals)
    m = re.search(r"([\d.]+)\s*(?:vol\.?\s*%|%|mol\s*%)\s*" + species, t, re.I)
    if m:
        return float(m.group(1)) / 100
    if re.fullmatch(r"\s*(pure\s+)?" + species + r"\s*", t, re.I):
        return 1.0
    return None


def feed_flows(text):
    """{'C3H8': 5.0, 'N2': 30.0} from 'C3H8 (5 mL/min) and N2 (30 mL/min)' or '4 ml/min propane'."""
    if not text:
        return {}
    out = {}
    for sp, v in re.findall(r"([A-Za-z][A-Za-z0-9]*)\s*\(\s*([\d.]+)\s*m[lL]\s*(?:/|\s)\s*min", text):
        if SPECIES.get(sp.lower()):
            out[SPECIES[sp.lower()]] = float(v)
    for v, sp in re.findall(r"([\d.]+)\s*m[lL]\s*(?:/|\s)\s*min(?:-1|−1)?\s+(?:of\s+)?([A-Za-z][A-Za-z0-9]*)", text):
        if SPECIES.get(sp.lower()):
            out.setdefault(SPECIES[sp.lower()], float(v))
    return out


R_MAX_PRINTED = 50.0   # kg product per kg catalyst per h; a printed rate above this is a unit error (self-check gate)


def elements(components):
    """[(element, wt% or None, role)] with oxides converted to metal content; bulk oxide (no support) = 100 %."""
    out = []
    has_support = any(c["role"] == "support" for c in components)
    for c in components:
        name = c["component"].replace("-x", "").replace("Ox", "O").strip()
        wt = c["loading_wt_pct"]
        if c["role"] == "support":
            continue
        base = re.sub(r"[^A-Za-z0-9]", "", name)
        if base in OXIDE_METAL:
            el, f = OXIDE_METAL[base]
            if wt is None and not has_support and len([x for x in components if x["role"] != "support"]) == 1:
                wt = 100.0
            out.append((el, None if wt is None else wt * f, c["role"]))
        else:
            m = re.match(r"([A-Z][a-z]?)", base)
            if m:
                out.append((m.group(1), wt, c["role"]))
    return out


def rate_kg_per_kg_h(d, basis, product, metal_wt):
    """Formation rate -> kg product per kg catalyst per h, or None when the unit cannot be converted."""
    v = num(d)
    if v is None:
        return None
    u = (d.get("unit") or "").lower().replace(" ", "").replace("μ", "µ").replace("·", "")
    if "m^-2" in u or "m-2" in u or "/m2" in u or "site" in u or "tof" in u or "s-1" == u or u in ("s^-1", "h-1"):
        return None
    mol = {"µmol": 1e-6, "umol": 1e-6, "mmol": 1e-3, "mol": 1}
    mass = {"mg": 1e-3, "kg": 1e3, "g": 1}
    q = None
    for k in ("µmol", "umol", "mmol", "mol"):
        if u.startswith(k):
            q = v * mol[k] * MW[product]        # g product
            break
    else:
        for k in ("mg", "kg", "g"):
            if u.startswith(k):
                q = v * mass[k]
                break
    if q is None:
        return None
    per_t = 1.0
    if "s" in re.split(r"[/]|g", u)[-1] or "s-1" in u or "s^-1" in u:
        per_t = 3600
    elif "min" in u:
        per_t = 60
    per_mass = 1e-3 if "kgcat" in u or "kg-1" in u or "/kg" in u else 1.0
    r = q * per_t * per_mass                    # g product per g (cat or metal) per h = kg/kg/h
    if basis == "per_g_metal":
        if not metal_wt:
            return None
        r *= metal_wt / 100
    elif basis not in ("per_g_catalyst", "unknown"):
        return None
    return r


def run(rxn):
    rows = []
    for f in sorted((HERE / "raw" / rxn).glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        paper = f.stem
        for i, x in enumerate(d.get("records", [])):
            els = elements(x["components"])
            act = [e for e in els if e[2] in ("active_metal", "active_oxide")]
            metal_wt = sum(e[1] for e in act if e[1]) if act else None
            T = temp_K(x["temperature"])
            P = pres_bar(x["pressure"]) or 1.01325
            if rxn == "pdh":
                X, S = frac(x["propane_conversion"]), frac(x["propylene_selectivity"])
                Y = frac(x["propylene_yield"])
                if X is None and Y is not None and S:
                    X = Y / S
                if S is None and Y is not None and X:
                    S = Y / X
                rate_d, basis, prod, key, prodname = x["propylene_rate"], x["propylene_rate_basis"], "C3H6", "C3H8", "C3H6"
                y = frac(x["c3h8_fraction_pct"]) if num(x["c3h8_fraction_pct"]) else feed_fraction(x["feed_composition"], "C3H8")
            else:
                X, S = frac(x["co2_conversion"]), frac(x["ch4_selectivity"])
                if S is None and frac(x["co_selectivity"]) is not None:
                    S = 1 - frac(x["co_selectivity"])
                Y = frac(x["ch4_yield"])
                if X is None and Y is not None and S:
                    X = Y / S
                rate_d, basis, prod, key = x["ch4_rate"], x["ch4_rate_basis"], "CH4", "CO2"
                y = feed_fraction(x["feed_composition"], "CO2")
                if y is None and num(x["h2_co2_ratio"]):
                    y = 1 / (1 + num(x["h2_co2_ratio"]))
            ff = feed_flows(x["feed_composition"])
            if not y and ff.get(key) and len(ff) > 1:
                y = ff[key] / sum(ff.values())
            r = rate_kg_per_kg_h(rate_d, basis, prod, metal_wt)
            r = r if r else None
            r_src = "printed" if r is not None else None
            rejected = False
            if r is not None and r > R_MAX_PRINTED:
                r, r_src, rejected = None, None, True
            # productivity from feed flow x conversion x selectivity (flagged 'derived')
            if r is None and X and S and y:
                m = mass_g(x["catalyst_mass"])
                fl = flow_ml_min(x["total_flow"])
                if not fl and len(ff) > 1:
                    fl = sum(ff.values())
                sv, svu = num(x["space_velocity"]), (x["space_velocity"].get("unit") or "").lower()
                mol_key_per_g_h = None
                flag = "derived"
                if fl and m:
                    mol_key_per_g_h = fl * y * 60 / 22414 / m
                elif sv and ("ml" in svu or "l" in svu) and x["space_velocity_basis"] == "per_mass_catalyst":
                    mol_key_per_g_h = sv * (1000 if "ml" not in svu else 1) * y / 22414
                elif sv and x["space_velocity_basis"] == "per_mass_catalyst" and rxn == "pdh" and "h" in svu:
                    mol_key_per_g_h = sv / MW["C3H8"]                 # WHSV on propane mass
                elif sv and x["space_velocity_basis"] == "per_volume_catalyst" and "h" in svu and "g" not in svu:
                    mol_key_per_g_h = sv * y / 22.414 / RHO_BED_KG_L / 1000   # GHSV (L gas / L bed / h) -> per g
                    flag = "derived_rho"
                if mol_key_per_g_h:
                    r = mol_key_per_g_h * X * S * MW[prod]
                    r_src = flag + ("_after_unit_gate" if rejected else "")
            X0, Xf, tdur = frac(x["stability_initial_conversion"]), frac(x["stability_final_conversion"]), hours(x["stability_duration"])
            kd = t_cycle = None
            if X0 and Xf and tdur and 0 < Xf < 1 and 0 < X0 < 1:
                kd = max((math.log((1 - Xf) / Xf) - math.log((1 - X0) / X0)) / tdur, 1e-6)
                Xt = 0.9 * X0
                t_cycle = (math.log((1 - Xt) / Xt) - math.log((1 - X0) / X0)) / kd
            y_h2 = feed_fraction(x["feed_composition"], "H2")
            rows.append(dict(
                rxn=rxn, paper=paper, idx=i, label=x["entry_label"], catalyst=x["catalyst_name"],
                elements=json.dumps([[e[0], e[1]] for e in els]), T_K=T, P_bar=P, feed=x["feed_composition"],
                y_key=y, y_h2=y_h2, X=X, S=S, r_kg_kg_h=r, r_src=r_src, kd_h=kd, t_cycle_h=t_cycle, stab_dur_h=tdur,
                X0=X0, Xf=Xf, source=x["data_source_type"],
                qual_X=(x["propane_conversion"] if rxn == "pdh" else x["co2_conversion"])["qualifier"],
                location=x["location"], page=x["page"]))
    out = HERE / "data"
    out.mkdir(exist_ok=True)
    with open(out / f"{rxn}_records.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    usable = [r for r in rows if r["T_K"] and r["X"] and r["S"] and r["r_kg_kg_h"]]
    print(rxn, len(rows), "records;", len(usable), "with T, X, S and productivity;",
          sum(1 for r in usable if r["r_src"] == "derived"), "productivity derived;",
          sum(1 for r in rows if r["t_cycle_h"]), "with stability")
    return rows


if __name__ == "__main__":
    for rxn in sys.argv[1:] or ["pdh", "ch4"]:
        run(rxn)
