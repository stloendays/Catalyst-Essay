"""Convert extracted ammonia-synthesis records (out/raw*/<slug>.json) to the ammonia-model basis and merge the passes.

Usage:
    python normalize.py          -> out/records_normalized.csv

Model basis (the inputs of analysis/nh3_supported_2026_10_06/run_supported_chain.py)
    T_C                 deg C        (K - 273.15)
    P_MPa               MPa          (bar / 10, atm x 0.101325, kPa / 1000; 'atmospheric' = 0.1 MPa as printed)
    H2_N2               molar ratio
    WHSV_mL_g_h         mL (g cat)-1 h-1, mass-based space velocity only, or total flow / catalyst mass
                        (WHSV_derived marks these); a volumetric GHSV (h-1) stays in SV_raw
    outlet_nh3_vol_pct  vol% (ppm / 1e4; a fraction <= 1 given with unit 'fraction' x 100)
    rate_umol_gcat_h    umol NH3 (g cat)-1 h-1   (rate_basis per_g_catalyst)
    rate_umol_gmetal_h  umol NH3 (g metal)-1 h-1 (rate_basis per_g_metal)
                        Amounts: mol, mmol, umol, nmol, or NH3 volume at STP (mL, L; 22,414 mL mol-1).
                        A basis written in the unit (gcat, gRu, gCo, g_metal ...) overrides an extracted rate_basis
                        of 'other'/'unspecified'. Per-metal and per-catalyst rates are converted into each other with
                        the stated metal loading (wt%): rate_cat_from_metal / rate_metal_from_cat mark these.
    metal_wt_pct        metal_loading when its unit is wt%; otherwise the sum of the wt% loadings of the components
                        with role active_metal
    TOF_s               s-1 (h-1 / 3600)
Passes: records of the main, SI and figure passes are merged per entry (same paper, same catalyst, T within 1.5 K,
P within 1 %, H2/N2 within 2 %, WHSV within 5 %, time on stream within 0.5 h when both are given). A printed main-text
value beats a printed SI value, which beats any plot reading; a lower-ranked pass only fills fields that are empty or
plot-read. `pass` gives the origin of an entry, `filled` the fields taken from another pass, <field>_src the source
of each value (table, text, mixed, plot, SI, SI-plot). Raw value+unit strings are kept so every conversion can be
audited, and a value whose unit was not understood is listed in `flags`, never silently dropped.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
from paper_set import load_paper_set  # noqa: E402
IN_SET = load_paper_set()
VM_ML = 22414.0          # mL (STP) per mol
METALS = {"ru", "fe", "co", "ni", "mo", "os", "re", "rh", "ir", "pd", "pt", "w", "cu", "ag", "au", "metal"}


def _clean(u: str | None) -> str:
    if u is None:
        return ""
    s = u.strip()
    for a, b in (("−", "-"), ("–", "-"), ("⁻¹", "-1"), ("⁻", "-"), ("¹", "1"), ("·", " "), ("⋅", " "),
                 ("μ", "u"), ("µ", "u"), ("℃", "°C"), ("^", ""), ("₃", "3"), ("NH3", "nh3")):
        s = s.replace(a, b)
    return s


def temp_C(v, u):
    if v is None:
        return None
    s = _clean(u).lower().replace(" ", "")
    if s in ("k", "kelvin"):
        return round(v - 273.15, 2)
    if s in ("°c", "oc", "c", "degc", "deg.c", "celsius", "ºc", "˚c"):
        return v
    return None


def press_MPa(v, u):
    """Absolute pressure in MPa; a gauge pressure ('MPa (gauge pressure)', 'barg', 'bar (gauge)') gets 0.101325 MPa
    added."""
    if v is None:
        return None
    s = _clean(u).lower().replace(" ", "")
    gauge = "gauge" in s or s in ("barg", "psig", "mpag")
    s = re.sub(r"\(?gauge(pressure)?\)?", "", s)
    f = {"mpa": 1, "bar": 0.1, "bara": 0.1, "barg": 0.1, "atm": 0.101325, "kpa": 0.001, "pa": 1e-6,
         "psi": 0.00689476, "psig": 0.00689476, "mpag": 1}.get(s)
    if f is None:
        return None
    return round(v * f + (0.101325 if gauge else 0.0), 6)


def outlet_pct(v, u):
    if v is None:
        return None
    s = _clean(u).lower().replace(" ", "")
    if s in ("", "%", "vol%", "vol.%", "mol%", "v/v%", "%(v/v)", "volume%", "percent", "%nh3", "vol%nh3"):
        return v
    if s in ("ppm", "ppmv", "vppm"):
        return v / 1e4
    if s in ("fraction", "-", "molefraction"):
        return v * 100
    return None


_PREFIX = {"": 1.0, "k": 1e3, "m": 1e-3, "u": 1e-6, "n": 1e-9}
_TOKEN = re.compile(r"(?P<pre>[kmun]?)(?P<base>mol|ml|l|g|hours|hour|hr|h|min|s|cm3)"
                    r"(?P<label>[_ ]?(?:cat|catalyst|nh3|ammonia|metal|ru|fe|co|ni|mo|os|re|rh|ir|pd|pt|w|cu))?"
                    r"(?P<exp>-?\d)?$")


def _parse(unit: str):
    """List of (prefix, base, label, exponent), or None when a token is not understood."""
    s = _clean(unit).lower()
    s = re.sub(r"\(?\b(stp|ntp)\b\)?", " ", s)
    s = s.replace("g-cat", "g_cat").replace("gcat", "g_cat").replace("kgcat", "kg_cat")
    s = re.sub(r"(?<=[a-z])\.(?=[a-z])", " ", s)
    s = re.sub(r"(?<=[a-z])\.(?=-|\d|\s|$|/|\))", "", s)
    s = re.sub(r"\bnml", "ml", s)
    s = re.sub(r"\bnl(?=[\s/_-]|$)", "l", s)
    num, *dens = s.split("/")
    out = []
    for part, sign in [(num, 1)] + [(d, -1) for d in dens]:
        part = part.replace("(", " ").replace(")", " ").replace("*", " ").replace("·", " ")
        part = re.sub(r"\b(k?g|[mun]?mol|m?l)\s+(nh3|ammonia|cat|catalyst|metal)\b", r"\1_\2", part)
        part = re.sub(r"\b(k?g)\s?(ru|fe|co|ni|mo|os|re|rh|ir|pd|pt|w|cu)\b(?=\s|-|$)", r"\1_\2", part)
        part = re.sub(r"\b(k?g)-?(ru|fe|co|ni|mo|os|re|rh|ir|pd|pt|w|cu|cat)(?=-\d)", r"\1_\2", part)
        for tok in part.split():
            m = _TOKEN.match(tok)
            if not m:
                return None
            exp = int(m.group("exp")) if m.group("exp") else 1
            pre, base = m.group("pre"), m.group("base")
            if base in ("ml", "cm3"):
                pre, base = "m", "l"
            if base in ("hr", "hour", "hours"):
                base = "h"
            out.append((pre, base, (m.group("label") or "").strip("_ "), exp * sign))
    return out


_TIME = {"h": 1.0, "min": 60.0, "s": 3600.0}


def rate_umol_g_h(v, u):
    """NH3 amount (mol or STP volume) per mass per time -> (umol g-1 h-1, mass label)."""
    if v is None:
        return None, None
    t = _parse(u or "")
    if not t:
        return None, None
    amt = [x for x in t if x[1] in ("mol", "l") and x[3] == 1]
    mass = [x for x in t if x[1] == "g" and x[3] == -1]
    tim = [x for x in t if x[1] in _TIME and x[3] == -1]
    if len(amt) == 1 and len(mass) == 1 and not tim and len(t) == 3 and t[-1][1] in _TIME and t[-1][3] == 1:
        tim = [(t[-1][0], t[-1][1], t[-1][2], -1)]   # 'umol g-1 h': the superscript -1 of the time unit was lost
    if len(amt) != 1 or len(mass) != 1 or len(tim) != 1 or len(t) != 3:
        return None, None
    pre, base, _, _ = amt[0]
    mol = v * _PREFIX[pre] * (1.0 if base == "mol" else 1000.0 / VM_ML)   # STP litres -> mol
    return mol * 1e6 / _PREFIX[mass[0][0]] * _TIME[tim[0][1]], mass[0][2]


def basis_from_label(label):
    if label in ("cat", "catalyst"):
        return "per_g_catalyst"
    if label in METALS:
        return "per_g_metal"
    return None


def whsv_mL_g_h(v, u, basis):
    if v is None or basis != "per_mass_catalyst":
        return None
    t = _parse(u or "")
    if not t:
        return None
    vol = [x for x in t if x[1] == "l" and x[3] == 1]
    mass = [x for x in t if x[1] == "g" and x[3] == -1]
    tim = [x for x in t if x[1] in _TIME and x[3] == -1]
    if len(vol) != 1 or len(mass) != 1 or len(tim) != 1:
        return None
    return v * _PREFIX[vol[0][0]] * 1000.0 / _PREFIX[mass[0][0]] * _TIME[tim[0][1]]


def flow_mL_h(v, u):
    if v is None:
        return None
    s = _clean(u).lower().strip()
    if s in ("sccm", "ml/min (stp)", "ml min-1 (stp)"):
        return v * 60
    t = _parse(s)
    if not t:
        return None
    vol = [x for x in t if x[1] == "l" and x[3] == 1]
    tim = [x for x in t if x[1] in _TIME and x[3] == -1]
    if len(vol) != 1 or len(tim) != 1 or len(t) != 2:
        return None
    return v * _PREFIX[vol[0][0]] * 1000.0 * _TIME[tim[0][1]]


def mass_g(v, u):
    if v is None:
        return None
    return {"g": v, "mg": v / 1000, "kg": v * 1000}.get(_clean(u).lower().replace(" ", ""))


def tof_s(v, u):
    if v is None:
        return None
    s = _clean(u).lower().replace(" ", "")
    m = re.match(r"10(-?\d+)(.*)", s)            # a power of ten left in the unit ('10-3 s-1')
    if m:
        v, s = v * 10.0 ** int(m.group(1)), m.group(2)
    s = re.sub(r"^(molecule|ru|co|fe|ni)?(site|atom)-1", "", s)
    if s in ("s-1", "1/s", "/s", "sec-1"):
        return v
    if s in ("h-1", "1/h", "/h", "hr-1"):
        return v / 3600
    if s in ("min-1", "1/min", "/min"):
        return v / 60
    return None


def is_wt(unit) -> bool:
    """wt% in any spelling; a bare '%' counts as wt% (papers write '1.25%Ru/BaCeO3' for a mass fraction of the
    catalyst). A ratio to the support ('% mass ratio Co metal to CNTs') is not the metal content of the catalyst."""
    return bool(re.fullmatch(r"\s*(wt\s?\.?\s?%|% ?\(?w/w\)?|mass\s?%|weight\s?%|wt\.%|%)(\s*nominal)?\s*", unit or "", re.I))


def metal_wt(r):
    ml = r["metal_loading"]
    if ml["value"] is not None and is_wt(ml["unit"]):
        return ml["value"]
    vals = [c["loading"]["value"] for c in r["components"]
            if c["role"] == "active_metal" and c["loading"]["value"] is not None and is_wt(c["loading"]["unit"])]
    return sum(vals) if vals else None


def normalize_record(doi: str, r: dict) -> dict:
    def raw(k):
        n = r[k]
        return None if n["value"] is None else f"{n['value']} {n['unit'] or ''}".strip()

    rate, label = rate_umol_g_h(r["rate"]["value"], r["rate"]["unit"])
    basis = r["rate_basis"]
    ub = basis_from_label(label)
    if ub and (basis in ("other", "unspecified") or ub != basis):
        basis = ub
    w = metal_wt(r)
    r_cat = rate if basis == "per_g_catalyst" else None
    r_met = rate if basis == "per_g_metal" else None
    cat_from_metal = metal_from_cat = False
    if r_cat is None and r_met is not None and w:
        r_cat, cat_from_metal = r_met * w / 100.0, True
    elif r_met is None and r_cat is not None and w:
        r_met, metal_from_cat = r_cat / (w / 100.0), True
    metals = (r["active_metal"] or "").replace(",", ";").replace("/", ";").replace(" ", "")
    row = {
        "doi": doi,
        "entry_label": r["entry_label"],
        "catalyst_name": r["catalyst_name"],
        "composition": r["composition"],
        "active_metals": ";".join(m for m in metals.split(";") if m),
        "metal_wt_pct": w,
        "metal_loading_raw": raw("metal_loading"),
        "support": r["support"],
        "promoters": ";".join(r["promoters"]),
        "preparation": r["preparation"],
        "T_C": temp_C(r["temperature"]["value"], r["temperature"]["unit"]),
        "T_q": r["temperature"]["qualifier"],
        "P_MPa": press_MPa(r["pressure"]["value"], r["pressure"]["unit"]),
        "H2_N2": r["h2_n2_ratio"]["value"],
        "feed": r["feed_composition"],
        "WHSV_mL_g_h": whsv_mL_g_h(r["space_velocity"]["value"], r["space_velocity"]["unit"], r["space_velocity_basis"]),
        "SV_raw": raw("space_velocity"),
        "sv_basis": r["space_velocity_basis"],
        "cat_mass_g": mass_g(r["catalyst_mass"]["value"], r["catalyst_mass"]["unit"]),
        "TOS_raw": raw("time_on_stream"),
        "outlet_nh3_vol_pct": outlet_pct(r["outlet_nh3"]["value"], r["outlet_nh3"]["unit"]),
        "outlet_raw": raw("outlet_nh3"),
        "outlet_q": r["outlet_nh3"]["qualifier"],
        "rate_umol_gcat_h": r_cat,
        "rate_umol_gmetal_h": r_met,
        "rate_cat_from_metal": cat_from_metal,
        "rate_metal_from_cat": metal_from_cat,
        "rate_raw": raw("rate"),
        "rate_basis": basis,
        "rate_basis_extracted": r["rate_basis"],
        "rate_q": r["rate"]["qualifier"],
        "TOF_s": tof_s(r["tof"]["value"], r["tof"]["unit"]),
        "TOF_raw": raw("tof"),
        "tof_basis": r["tof_basis"],
        "operation_mode": r["operation_mode"],
        "data_source_type": r["data_source_type"],
        "primary_location": r["primary_location"],
        "primary_page": r["primary_page"],
        "notes": r["notes"],
    }
    flags = []
    if r["temperature"]["value"] is not None and row["T_C"] is None:
        flags.append("T_unit")
    if r["pressure"]["value"] is not None and row["P_MPa"] is None:
        flags.append("P_unit")
    if r["rate"]["value"] is not None and rate is None and basis not in ("per_m2", "per_mL_catalyst", "per_mol_metal"):
        flags.append("rate_unit")
    if r["outlet_nh3"]["value"] is not None and row["outlet_nh3_vol_pct"] is None:
        flags.append("outlet_unit")
    if r["tof"]["value"] is not None and row["TOF_s"] is None:
        flags.append("TOF_unit")
    if r["space_velocity"]["value"] is not None and r["space_velocity_basis"] == "per_mass_catalyst" and row["WHSV_mL_g_h"] is None:
        flags.append("SV_unit")
    # physical range: a rate above 1 mol NH3 per g catalyst per h is a transcription error (unit or multiplier)
    if (row["rate_umol_gcat_h"] or 0) > 1e6:
        flags.append("rate_implausible")
        row["rate_umol_gcat_h"] = row["rate_umol_gmetal_h"] = None
    tf = r.get("total_flow") or {}
    row["flow_mL_h"] = flow_mL_h(tf.get("value"), tf.get("unit"))
    row["WHSV_derived"] = False
    if row["WHSV_mL_g_h"] is None and row["flow_mL_h"] and row["cat_mass_g"]:
        row["WHSV_mL_g_h"] = row["flow_mL_h"] / row["cat_mass_g"]
        row["WHSV_derived"] = True
    row["flags"] = ";".join(flags)
    return row


# ---------------------------------------------------------------- merging the passes
PASS_DIRS = {"main": HERE / "out" / "raw", "si": HERE / "out" / "raw_si", "figures": HERE / "out" / "raw_figures",
             "si_figures": HERE / "out" / "raw_si_figures"}
FIELD_GROUPS = {
    "rate": (["rate_umol_gcat_h", "rate_umol_gmetal_h", "rate_cat_from_metal", "rate_metal_from_cat", "rate_raw",
              "rate_basis", "rate_basis_extracted", "rate_q"], "rate_q"),
    "outlet": (["outlet_nh3_vol_pct", "outlet_raw", "outlet_q"], "outlet_q"),
    "TOF": (["TOF_s", "TOF_raw", "tof_basis"], None),
    "WHSV": (["WHSV_mL_g_h", "SV_raw", "sv_basis", "WHSV_derived", "flow_mL_h"], None),
    "H2_N2": (["H2_N2", "feed"], None),
    "cat_mass_g": (["cat_mass_g"], None),
    "metal_wt_pct": (["metal_wt_pct", "metal_loading_raw"], None),
}
SRC_FIELDS = ("rate", "outlet", "TOF", "WHSV")


def _key(name) -> str:
    return re.sub(r"[\s.\-_(),/:;%–—]+", "", str(name).lower())


def _tokens(name) -> list[str]:
    return [t for t in re.split(r"[^0-9a-z]+", str(name).lower().replace("–", "-")) if t]


def _same_catalyst(a, b) -> bool:
    if _key(a) == _key(b):
        return True
    ta, tb = _tokens(a), _tokens(b)
    short, long_ = sorted((ta, tb), key=len)
    ds, dl = re.findall(r"\d+", "".join(short)), re.findall(r"\d+", "".join(long_))
    return bool(short) and len("".join(short)) >= 4 and long_[:len(short)] == short and dl[:len(ds)] == ds


def _empty(v) -> bool:
    return v is None or (isinstance(v, float) and np.isnan(v))


def _close(a, b, rel):
    if _empty(a) or _empty(b):
        return None
    return abs(a - b) <= rel * max(abs(a), abs(b), 1e-12)


def _tos_h(raw):
    if _empty(raw):
        return None
    m = re.match(r"\s*([\d.]+)\s*([a-zA-Z]*)", str(raw))
    if not m:
        return None
    unit = m.group(2).lower()
    f = 1 / 60 if unit.startswith("min") else 1 / 3600 if unit in ("s", "sec") else 24 if unit.startswith("d") else 1
    try:
        return float(m.group(1)) * f
    except ValueError:
        return None


def _same_entry(r, m) -> bool:
    if r["doi"] != m["doi"] or not _same_catalyst(r["catalyst_name"], m["catalyst_name"]):
        return False
    if _empty(r["T_C"]) or _empty(m["T_C"]) or abs(r["T_C"] - m["T_C"]) > 1.5:
        return False
    for col, rel in (("P_MPa", 0.01), ("H2_N2", 0.02), ("WHSV_mL_g_h", 0.05)):
        if _close(r[col], m[col], rel) is False:
            return False
    ta, tb = _tos_h(r["TOS_raw"]), _tos_h(m["TOS_raw"])
    if ta is not None and tb is not None and abs(ta - tb) > max(0.5, 0.05 * max(ta, tb)):
        return False
    return True


def _rank(row, qual_col) -> int:
    plotted = (qual_col and row.get(qual_col) == "~") or row["data_source_type"] == "figure"
    if row["pass"] in ("figures", "si_figures") or plotted:
        return 1
    return 3 if row["pass"] == "main" else 2


def _src(row) -> str:
    if row["pass"] == "si_figures" or (row["pass"] == "si" and row["data_source_type"] == "figure"):
        return "SI-plot"
    if row["pass"] == "si":
        return "SI"
    if row["pass"] == "figures" or row["data_source_type"] == "figure":
        return "plot"
    return row["data_source_type"]


def merge_passes(rows_by_pass: dict[str, list[dict]]) -> list[dict]:
    merged: list[dict] = []
    for pass_ in ("main", "si", "figures", "si_figures"):
        for r in rows_by_pass.get(pass_, []):
            r = dict(r, **{"pass": pass_, "filled": ""})
            for f in SRC_FIELDS:
                r[f + "_src"] = _src(r) if not _empty(r[FIELD_GROUPS[f][0][0]]) else None
            target = next((m for m in merged if _same_entry(r, m)), None) if pass_ != "main" else None
            if target is None:
                merged.append(r)
                continue
            for f, (cols, qcol) in FIELD_GROUPS.items():
                if _empty(r[cols[0]]):
                    continue
                if _empty(target[cols[0]]) or _rank(r, qcol) > _rank(target, qcol):
                    for c in cols:
                        target[c] = r[c]
                    if f in SRC_FIELDS:
                        target[f + "_src"] = _src(r)
                    target["filled"] = ";".join(x for x in (target["filled"], f"{f}<-{pass_}") if x)
    return merged


def slug(doi: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", doi.lower()).strip("_")


def load_pass(pass_: str, slug_to_doi: dict) -> list[dict]:
    rows = []
    for f in sorted(PASS_DIRS[pass_].glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        doi = slug_to_doi.get(f.stem, (d.get("doi") or f.stem).lower())
        if doi.lower() not in IN_SET:
            continue
        for r in d["records"]:
            rows.append(normalize_record(doi.lower(), r))
    return rows


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--passes", default="main,si,figures,si_figures")
    args = ap.parse_args()
    slug_to_doi = {slug(d): d for d in IN_SET}
    passes = [x.strip() for x in args.passes.split(",") if x.strip()]
    by_pass = {p_: load_pass(p_, slug_to_doi) for p_ in passes}
    df = pd.DataFrame(merge_passes(by_pass))
    df.to_csv(HERE / "out" / "records_normalized.csv", index=False, encoding="utf-8")
    print(f"{len(df)} merged records from {df.doi.nunique()} papers; per-pass {({k: len(v) for k, v in by_pass.items()})}; "
          f"by origin {df['pass'].value_counts().to_dict()}; rows with filled fields {(df['filled'] != '').sum()}")
    bad = df["flags"].astype(bool)
    if bad.any():
        print(df[bad][["doi", "entry_label", "flags", "rate_raw", "SV_raw", "outlet_raw"]].to_string())


if __name__ == "__main__":
    main()
