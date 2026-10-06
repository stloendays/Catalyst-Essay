"""Score the extracted records against TheMeCat v1 and the manual Gothe 2025 Table 4.

Usage:
    python evaluate.py      (after normalize.py)

Inputs
    out/records_normalized.csv                 extraction output on the model basis
    TheMeCat_v1.csv                            human-curated reference (Toldy et al., Sci. Data 2026)
    table4_gothe2025.csv                       manual transcription of Gothe et al. 2025 Table 4
    eval/themecat_errata.csv                   TheMeCat values shown wrong by the PDF (verified by hand)
    eval/unmatched_review.csv                  hand verdicts on extracted entries with no TheMeCat partner
    eval/name_aliases.json                     catalyst-name aliases (per DOI) used by the matcher

Matching rule (documented in README):
    same DOI; catalyst names equal after normalisation (case, spaces, punctuation,
    dashes removed), or the shorter name's word tokens are a prefix of the longer
    name's tokens, or keys one edit apart with identical digit sequences, or
    listed in name_aliases.json; |dT| <= 3 K; |dP|/P <= 5 %;
    H2/CO2 within 10 % when both present; GHSV within 10 % when both are on a
    mass basis. Among the candidate pairs that pass, a one-to-one assignment
    (Hungarian) minimises |dT|/3 + |dP|/P/0.05 + |dX| + |dS| (pp), so performance
    values only break ties between entries at identical conditions.
Matching uses TheMeCat values after the errata are applied ("adjudicated").
Field accuracy is reported against both the raw and the adjudicated TheMeCat values.
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment

HERE = Path(__file__).resolve().parent
EVAL = HERE / "eval"
THEMECAT = Path(r"D:\论文-AI4S\work\advisor_2026-10-05\task3\data\TheMeCat_v1.csv")
GOTHE = Path(r"D:\论文-AI4S\work\advisor_2026-10-05\task4\table4_gothe2025.csv")
GOTHE_DOI = "10.1021/acscatal.5c05984"
SUVARNA = Path(r"D:\论文-AI4S\work\advisor_2026-10-05\task3\data\Suvarna2022_curated_1234.xlsx")
from paper_set import load_paper_set  # noqa: E402
REF = load_paper_set()  # DOI -> reference set (gothe, themecat, suvarna, review)

# field: (extracted column, TheMeCat column, kind, strict tol, loose tol); kind abs = pp / K, rel = fraction
FIELDS = {
    "T": ("T_K", "temperature_k", "abs", 1.0, 3.0),
    "P": ("P_bar", "pressure_bar", "rel", 0.01, 0.05),
    "H2/CO2": ("H2_CO2", "pH2_pCO2_ratio", "abs", 0.05, 0.15),  # TheMeCat stores 1 decimal
    "GHSV": ("GHSV_NL_gcat_h", "GHSV_nlph_gcat", "rel", 0.01, 0.05),
    "X_CO2": ("X_CO2_pct", "CO2_conversion", "abs", 0.5, 2.0),
    "S_MeOH": ("S_MeOH_pct", "selectivity_CH3OH", "abs", 0.5, 2.0),
    "STY": ("STY_g_gcat_h", "STY_g_per_gcath", "rel", 0.01, 0.05),
}


def norm_doi(s: str) -> str:
    return re.sub(r"^(https?://)?(dx\.)?doi\.org/", "", str(s).strip()).lower()


def name_key(s: str) -> str:
    s = unicodedata.normalize("NFKC", str(s)).lower()
    s = s.replace("–", "-").replace("—", "-")
    return re.sub(r"[\s.\-_(),/:;%]+", "", s)


def edit_distance(a: str, b: str) -> int:
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def name_tokens(s: str) -> list[str]:
    s = unicodedata.normalize("NFKC", str(s)).lower().replace("–", "-").replace("—", "-")
    return [t for t in re.split(r"[^0-9a-z]+", s) if t]


def names_match(a: str, b: str, aliases: dict, allow_fuzzy: bool = True) -> bool:
    ka, kb = name_key(a), name_key(b)
    if ka == kb:
        return True
    # word-level prefix: 'Cat-4.5' ~ 'Cat-4.5 H-In2O3/Al2O3/Al-fiber', but not 'Cu/ZrO2(I)' ~ 'Cu/ZrO2(II)'
    # and not 'Ir1Pd1-In2O3' ~ '2Ir1Pd1-In2O3'
    ta, tb = name_tokens(a), name_tokens(b)
    short, long_ = sorted((ta, tb), key=len)
    if allow_fuzzy and short and len("".join(short)) >= 4 and long_[:len(short)] == short:
        return True
    # spelling slips only: one edit apart on keys of >= 6 characters with identical digits
    # ('13% ZnO-ZrO2' must not match '10% ZnO-ZrO2', 'Ir1Pd1-In2O3(CP-CP)' must not match 'Ir1Pd1-In2O3(PM)')
    if allow_fuzzy and min(len(ka), len(kb)) >= 6 and re.findall(r"\d+", ka) == re.findall(r"\d+", kb) and edit_distance(ka, kb) <= 1:
        return True
    for pair in aliases:
        if {name_key(pair[0]), name_key(pair[1])} == {ka, kb}:
            return True
    return False


def within(a, b, kind, tol) -> bool:
    if kind == "abs":
        return abs(a - b) <= tol + 1e-9
    return abs(a - b) <= tol * max(abs(b), 1e-12) + 1e-12


def load_themecat(dois: set[str]) -> pd.DataFrame:
    t = pd.read_csv(THEMECAT)
    t = t[t.doi_link.notna()].copy()
    t["doi"] = t.doi_link.map(norm_doi)
    t = t[t.doi.isin(dois)].copy()
    t["cur_id"] = t.index
    return t


# ---------------------------------------------------------------- Suvarna et al. 2022 (batch 4)
# The Suvarna set has no catalyst names and no conversion or selectivity. Each row gives the composition
# (family, metal loading, supports, promoters with loadings), T, P, H2/CO2, GHSV (cm3 h-1 gcat-1) and STY
# (mg MeOH h-1 gcat-1). Rows are mapped onto the TheMeCat columns; the composition becomes an element set that the
# matcher compares with the elements named in the extracted catalyst name, composition, support and promoters.
ELEMENTS = ("Cu", "Zn", "Zr", "Al", "In", "Pd", "Pt", "Ni", "Co", "Ce", "Ti", "Si", "Ga", "Mg", "Ir", "Ru", "Ag", "Au",
            "Re", "Y", "La", "Mn", "K", "Ba", "Cs", "Sn", "Fe", "Cr", "Mo", "Ca", "Rh", "Na", "Sm", "Nd", "Gd", "Hf")
FAMILY_ELEMENTS = {"Cu": {"Cu"}, "In2O3": {"In"}, "Pd": {"Pd"}, "ZnO-ZrO2": {"Zn", "Zr"}}


def elements_in(*texts) -> frozenset:
    found = set()
    for t in texts:
        if not isinstance(t, str):
            continue
        for sym in re.findall(r"[A-Z][a-z]?", t):
            if sym in ELEMENTS:
                found.add(sym)
    return frozenset(found)


def load_suvarna(dois: set[str]) -> pd.DataFrame:
    d = pd.read_excel(SUVARNA, sheet_name="Curated Data")
    d.columns = [c.strip() for c in d.columns]
    d["doi"] = (d["Reference DOI"].astype(str).str.replace(r"^\s*doi:\s*", "", regex=True, case=False)
                .map(norm_doi))
    d = d[d.doi.isin(dois)].copy()
    out = pd.DataFrame({
        "doi": d.doi,
        "temperature_k": d["Temperature [K]"].astype(float),
        "pressure_bar": d["Pressure [Mpa]"].astype(float) * 10,
        "pH2_pCO2_ratio": d["H2/CO2 [-]"].astype(float),
        "GHSV_nlph_gcat": d["GHSV [cm3 h-1 gcat-1]"].astype(float) / 1000,
        "STY_g_per_gcath": d["STY [mgMeOH h-1 gcat-1]"].astype(float) / 1000,
        "CO2_conversion": np.nan, "selectivity_CH3OH": np.nan,
    })
    comp = []
    for _, r in d.iterrows():
        fam = str(r["Family"]).strip()
        parts = [f"{fam} {r['Metal Loading [wt.%]']:g} wt%"]
        for k in ("Support 1", "Name of Support2", "Name of Support 3"):
            if str(r[k]) not in ("0", "nan"):
                parts.append(f"/{r[k]}")
        for k, lk in (("Promoter 1", "Promoter 1 loading [wt.%]"), ("Promoter 2", "Promoter 2 loading [wt.%]")):
            if str(r[k]) not in ("0", "nan"):
                parts.append(f"+{r[k]} {r[lk]:g} wt%")
        name = " ".join(parts)
        els = set(FAMILY_ELEMENTS.get(fam, elements_in(fam)))
        els |= elements_in(*(str(r[k]) for k in ("Support 1", "Name of Support2", "Name of Support 3",
                                                 "Promoter 1", "Promoter 2")))
        comp.append((name, frozenset(els), float(r["Metal Loading [wt.%]"])))
    out["catalyst_name"] = [c[0] for c in comp]
    out["elements"] = [c[1] for c in comp]
    out["loading"] = [c[2] for c in comp]
    # The Suvarna set lists some bimetallic catalysts twice, once under each family (e.g. Cu-In/CeO2 as a Cu row
    # and as an In2O3 row with the same conditions and STY); one copy is kept.
    out["_key"] = [(r.doi, r.temperature_k, r.pressure_bar, r.pH2_pCO2_ratio, r.GHSV_nlph_gcat, round(r.STY_g_per_gcath, 9),
                    r.elements) for r in out.itertuples()]
    out = out.drop_duplicates("_key").drop(columns="_key")
    out["cur_id"] = ["S%d" % i for i in out.index]
    out.index = out.cur_id
    return out


def match_doi_suvarna(ex: pd.DataFrame, cur: pd.DataFrame) -> list[tuple[int, str]]:
    """Conditions as hard gates (|dT| <= 3 K, |dP|/P <= 5 %, H2/CO2 and mass GHSV within 10 % when both present);
    among the pairs that pass, a one-to-one assignment minimising 3 x (element-set difference) + the relative
    loading difference (capped at 1, only when the extracted record states it) + |ln STY ratio| (tie-break,
    capped at 2). Composition dominates; STY only separates entries of identical composition and conditions."""
    if ex.empty or cur.empty:
        return []
    BIG = 1e6
    C = np.full((len(ex), len(cur)), BIG)
    for i, (_, e) in enumerate(ex.iterrows()):
        e_el = elements_in(e.catalyst_name, e.composition, e.support, e.promoters, e.active_metals)
        for j, (_, c) in enumerate(cur.iterrows()):
            if pd.isna(e.T_K) or abs(e.T_K - c.temperature_k) > 3:
                continue
            # an extracted record without a pressure can still pair (Ni-In-Al/SiO2 states 'ambient pressure' once
            # and the extraction left P empty); P then scores as missing
            if pd.notna(e.P_bar) and abs(e.P_bar - c.pressure_bar) > 0.05 * c.pressure_bar:
                continue
            if pd.notna(e.H2_CO2) and pd.notna(c.pH2_pCO2_ratio) and abs(e.H2_CO2 - c.pH2_pCO2_ratio) > 0.10 * c.pH2_pCO2_ratio:
                continue
            if pd.notna(e.GHSV_NL_gcat_h) and pd.notna(c.GHSV_nlph_gcat) and not any(
                    pd.notna(g) and abs(g - c.GHSV_nlph_gcat) <= 0.10 * c.GHSV_nlph_gcat
                    for g in (e.GHSV_NL_gcat_h, e.get("GHSV_inert_free_NL_gcat_h"))):
                continue
            cost = abs(e.T_K - c.temperature_k) / 3
            cost += abs(e.P_bar - c.pressure_bar) / c.pressure_bar / 0.05 if pd.notna(e.P_bar) else 1
            cost += 3 * len(e_el ^ c.elements)
            if pd.notna(e.metal_wt_pct) and c.loading > 0:
                cost += min(1.0, abs(e.metal_wt_pct - c.loading) / c.loading)
            if pd.notna(e.STY_g_gcat_h) and e.STY_g_gcat_h > 0 and c.STY_g_per_gcath > 0:
                cost += min(2.0, abs(np.log(e.STY_g_gcat_h / c.STY_g_per_gcath)))
            else:
                cost += 2
            cost += 0.05 * {"main": 0, "si": 1, "figures": 2, "si_figures": 3}.get(e.get("pass", "main"), 0)
            C[i, j] = cost
    rows, cols = linear_sum_assignment(C)
    return [(ex.index[r], cur.index[c]) for r, c in zip(rows, cols) if C[r, c] < BIG]


def apply_errata(t: pd.DataFrame, errata: str | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return adjudicated copy and a log of every changed cell."""
    adj = t.copy()
    log = []
    path = EVAL / ("themecat_errata.csv" if errata is None else errata)
    if not path.exists():
        return adj, pd.DataFrame()
    er = pd.read_csv(path)
    for _, e in er.iterrows():
        m = adj.doi == e.doi.lower()
        if isinstance(e.selector, str) and e.selector.strip():
            m &= adj.eval(e.selector)
        if e.action == "drop":  # row contradicted by the PDF and not repairable: excluded from the adjudicated set
            for idx in adj[m].index:
                log.append({"cur_id": idx, "doi": e.doi, "catalyst_name": adj.at[idx, "catalyst_name"],
                            "field": "(row dropped)", "themecat": None, "pdf": None, "evidence": e.evidence})
            adj = adj[~m]
            continue
        if e.action == "rename":  # row carries another catalyst's data; value = the catalyst name the PDF gives
            for idx in adj[m].index:
                log.append({"cur_id": idx, "doi": e.doi, "catalyst_name": adj.at[idx, "catalyst_name"],
                            "field": "catalyst_name", "themecat": adj.at[idx, "catalyst_name"], "pdf": e.value,
                            "evidence": e.evidence})
                adj.at[idx, "catalyst_name"] = e.value
                if "elements" in adj.columns:  # Suvarna rows: the composition the matcher uses follows the new name
                    adj.at[idx, "elements"] = elements_in(e.value)
                    adj.at[idx, "loading"] = float(re.search(r"([\d.]+) wt%", e.value).group(1))
            continue
        for idx in adj[m].index:
            old = adj.at[idx, e.field]
            new = old * float(e.value) if e.action == "multiply" else float(e.value)
            adj.at[idx, e.field] = new
            log.append({"cur_id": idx, "doi": e.doi, "catalyst_name": adj.at[idx, "catalyst_name"],
                        "field": e.field, "themecat": old, "pdf": new, "evidence": e.evidence})
    return adj, pd.DataFrame(log)


def match_doi(ex: pd.DataFrame, cur: pd.DataFrame, aliases: dict) -> list[tuple[int, int]]:
    if ex.empty or cur.empty:
        return []
    BIG = 1e6
    C = np.full((len(ex), len(cur)), BIG)
    # The prefix and one-edit rules are used only for names that have no exact or alias partner in the
    # other set, so 'Ir1Pd1-In2O3(PM)' is never paired with 'Ir1Pd1-In2O3(GM)', nor 'In2O3' with
    # 'In2O3/HZSM-5', when the exact partners exist.
    ex_names, cur_names = set(ex.catalyst_name), set(cur.catalyst_name)
    ex_strong = {a for a in ex_names if any(names_match(a, b, aliases, False) for b in cur_names)}
    cur_strong = {b for b in cur_names if any(names_match(a, b, aliases, False) for a in ex_names)}
    for i, (_, e) in enumerate(ex.iterrows()):
        for j, (_, c) in enumerate(cur.iterrows()):
            fuzzy_ok = e.catalyst_name not in ex_strong and c.catalyst_name not in cur_strong
            if not names_match(e.catalyst_name, c.catalyst_name, aliases, fuzzy_ok):
                continue
            if pd.isna(e.T_K) or pd.isna(c.temperature_k) or abs(e.T_K - c.temperature_k) > 3:
                continue
            if pd.isna(e.P_bar) or pd.isna(c.pressure_bar) or abs(e.P_bar - c.pressure_bar) > 0.05 * c.pressure_bar:
                continue
            if pd.notna(e.H2_CO2) and pd.notna(c.pH2_pCO2_ratio) and abs(e.H2_CO2 - c.pH2_pCO2_ratio) > 0.10 * c.pH2_pCO2_ratio:
                continue
            if pd.notna(e.GHSV_NL_gcat_h) and pd.notna(c.GHSV_nlph_gcat) and not any(
                    pd.notna(g) and abs(g - c.GHSV_nlph_gcat) <= 0.10 * c.GHSV_nlph_gcat
                    for g in (e.GHSV_NL_gcat_h, e.get("GHSV_inert_free_NL_gcat_h"))):
                continue
            cost = abs(e.T_K - c.temperature_k) / 3 + abs(e.P_bar - c.pressure_bar) / c.pressure_bar / 0.05
            # tie-break only: prefer the main extraction, then SI, then plot passes (0.05 per rank)
            cost += 0.05 * {"main": 0, "si": 1, "figures": 2, "si_figures": 3}.get(e.get("pass", "main"), 0)
            for a, b in (("X_CO2_pct", "CO2_conversion"), ("S_MeOH_pct", "selectivity_CH3OH")):
                if pd.notna(e[a]) and pd.notna(c[b]):
                    cost += abs(e[a] - c[b])
                else:
                    cost += 5  # unknown performance: weaker evidence for this pairing
            C[i, j] = cost
    rows, cols = linear_sum_assignment(C)
    return [(ex.index[r], cur.index[c]) for r, c in zip(rows, cols) if C[r, c] < BIG]


QUAL = {"X_CO2": "X_CO2_q", "S_MeOH": "S_MeOH_q", "STY": "STY_q"}
SRC_COL = {"X_CO2": "X_CO2_src", "S_MeOH": "S_MeOH_src", "STY": "STY_src", "GHSV": "GHSV_src"}


def field_source(e, f) -> str:
    """Source of one value: table, text, mixed, plot or SI (per field after the pass merge)."""
    v = e.get(SRC_COL.get(f, ""), None)
    if isinstance(v, str) and v:
        return v
    if e.get("pass") == "si_figures":
        return "SI-plot"
    if e.get("pass") == "si":
        return "SI"
    if e.get("pass") == "figures" or e.data_source_type == "figure":
        return "plot"
    return e.data_source_type


def field_scores(pairs, ex, cur_raw, cur_adj):
    out = []
    for ei, ci in pairs:
        e = ex.loc[ei]
        for f, (ecol, ccol, kind, st, lo) in FIELDS.items():
            for truth_name, cur in (("raw", cur_raw), ("adjudicated", cur_adj)):
                tv = cur.at[ci, ccol]
                if pd.isna(tv):
                    continue
                ev = e[ecol]
                if f == "GHSV" and pd.isna(ev) and pd.notna(e.GHSV_raw):
                    status_s = status_l = "not_comparable_basis"
                elif pd.isna(ev):
                    status_s = status_l = "missing"
                else:
                    cands = [ev]
                    if f == "GHSV" and pd.notna(e.get("GHSV_inert_free_NL_gcat_h")):
                        # curated GHSV is computed on the total feed or on reactants only; either counts
                        cands.append(e["GHSV_inert_free_NL_gcat_h"])
                        ev = min(cands, key=lambda g: abs(g - tv))
                    qual = e.get(QUAL.get(f, ""), "=")
                    if qual in (">", ">=") and tv >= ev - 1e-9:      # printed as a bound, e.g. '>20 %'
                        status_s = status_l = "correct"
                    elif qual in ("<", "<=") and tv <= ev + 1e-9:
                        status_s = status_l = "correct"
                    else:
                        status_s = "correct" if within(ev, tv, kind, st) else "wrong"
                        status_l = "correct" if within(ev, tv, kind, lo) else "wrong"
                out.append({"doi": e.doi, "ex_id": ei, "cur_id": ci, "catalyst": e.catalyst_name, "field": f,
                            "truth": truth_name, "extracted": ev, "curated": tv,
                            "source_type": field_source(e, f), "strict": status_s, "loose": status_l})
    return pd.DataFrame(out)


def summarize_fields(fs: pd.DataFrame, by=("truth", "field")) -> pd.DataFrame:
    rows = []
    for key, g in fs.groupby(list(by)):
        n = len(g)
        rec = dict(zip(by, key if isinstance(key, tuple) else (key,)))
        cmp_s = g[g.strict.isin(["correct", "wrong"])]
        rec.update({
            "n_curated": n,
            "n_extracted": len(cmp_s),
            "coverage": round(len(cmp_s) / n, 3) if n else None,
            "acc_strict": round((cmp_s.strict == "correct").mean(), 3) if len(cmp_s) else None,
            "acc_loose": round((cmp_s.loose == "correct").mean(), 3) if len(cmp_s) else None,
            "n_missing": int((g.strict == "missing").sum()),
            "n_not_comparable": int((g.strict == "not_comparable_basis").sum()),
        })
        rows.append(rec)
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- Gothe Table 4
def _lt(s):
    s = str(s).strip()
    return (float(s[1:]), "<") if s.startswith("<") else (float(s), "=")


def gothe_eval(ex: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    g = pd.read_csv(GOTHE)
    e = ex[ex.doi == GOTHE_DOI].copy()

    def prered(r):
        txt = " ".join(str(r[k]) for k in ("catalyst_name", "preparation", "notes") if pd.notna(r[k]))
        m = re.search(r"pre-?reduc\w*.{0,40}?(\d{3})\s*°\s*C", txt, re.I) or re.search(r"(\d{3})\s*°C", txt)
        return float(m.group(1)) if m else np.nan

    e["T_prered"] = e.apply(prered, axis=1)
    rows, used = [], set()
    for gi, t in g.iterrows():
        ratio = float(t.CO2_H2.split(":")[1]) / float(t.CO2_H2.split(":")[0])
        cand = e[(e.metal_wt_pct == t.Re_wt) & (e.T_prered == t.T_prered_C) & ((e.T_K - 273.15 - t.T_rxn_C).abs() < 1)
                 & ((e.P_bar - t.P_bar).abs() < 0.5) & ((e.H2_CO2 - ratio).abs() < 0.05)
                 & ((e.GHSV_NL_gcat_h - t.GHSV_1e3_mL_gcat_h).abs() < 0.5)]
        cand = cand[~cand.index.isin(used)]
        if cand.empty:
            rows.append({"gothe_row": gi + 1, "matched": False})
            continue
        r = cand.iloc[0]
        used.add(cand.index[0])
        rec = {"gothe_row": gi + 1, "matched": True, "ex_id": cand.index[0]}
        for f, col, tcol in (("X_CO2", "X_CO2_pct", "X_CO2_pct"), ("S_MeOH", "S_MeOH_pct", "S_MeOH_pct"),
                             ("S_CO", "S_CO_pct", "S_CO_pct"), ("S_CH4", "S_CH4_pct", "S_CH4_pct"),
                             ("STY_per_gRe", "STY_g_gmetal_h", "STY_gMeOH_gRe_h")):
            tv, tq = _lt(t[tcol])
            ev = r[col]
            eq = r.get(col.replace("_pct", "_q").replace("STY_g_gmetal_h", "STY_q"), "=")
            eq = "=" if pd.isna(eq) else eq
            ok = pd.notna(ev) and abs(ev - tv) <= 0.5 + 1e-9 and (tq == eq or (tq == "=" and eq == "="))
            rec[f] = "correct" if ok else ("missing" if pd.isna(ev) else "wrong")
            rec[f + "_extracted"] = f"{'' if eq == '=' else eq}{ev}"
            rec[f + "_manual"] = t[tcol]
        rows.append(rec)
    res = pd.DataFrame(rows)
    summ = {"rows": len(g), "matched": int(res.matched.sum()), "extracted_entries": len(e)}
    for f in ("X_CO2", "S_MeOH", "S_CO", "S_CH4", "STY_per_gRe"):
        if f in res:
            summ[f] = f"{int((res[f] == 'correct').sum())}/{int(res.matched.sum())}"
    return res, summ


def main() -> None:
    ex = pd.read_csv(HERE / "out" / "records_normalized.csv", keep_default_na=False, na_values=[""])  # catalyst "NA"
    ex["doi"] = ex.doi.str.lower()
    aliases_all = json.loads((EVAL / "name_aliases.json").read_text(encoding="utf-8")) if (EVAL / "name_aliases.json").exists() else {}
    ex = ex[ex.doi.isin(REF)]
    dois = set(ex.doi) - {GOTHE_DOI}
    tm_raw = load_themecat({d for d in dois if REF[d] == "themecat"})
    tm_raw["ref"] = "themecat"
    tm_adj, tm_log = apply_errata(tm_raw)
    sv_raw = load_suvarna({d for d in dois if REF[d] == "suvarna"})
    sv_raw["ref"] = "suvarna"
    sv_adj, sv_log = apply_errata(sv_raw, "suvarna_errata.csv")
    cur_raw = pd.concat([tm_raw, sv_raw])
    cur_adj = pd.concat([tm_adj, sv_adj])
    errata_log = pd.concat([tm_log.assign(ref="themecat"), sv_log.assign(ref="suvarna")])

    pairs = []
    for doi in sorted(dois):
        if REF[doi] == "suvarna":
            pairs += match_doi_suvarna(ex[ex.doi == doi], sv_adj[sv_adj.doi == doi])
        else:
            pairs += match_doi(ex[ex.doi == doi], cur_adj[cur_adj.doi == doi], aliases_all.get(doi, []))
    matched_ex = {p[0] for p in pairs}
    matched_cur = {p[1] for p in pairs}

    fs = field_scores(pairs, ex, cur_raw, cur_adj)
    fs["ref"] = fs.doi.map(REF)
    fsum = summarize_fields(fs)
    fsum_src = summarize_fields(fs[fs.truth == "adjudicated"], by=("source_type", "field"))
    fsum_ref = summarize_fields(fs[fs.truth == "adjudicated"], by=("ref", "field"))

    # entry-level recall / precision
    review = pd.read_csv(EVAL / "unmatched_review.csv") if (EVAL / "unmatched_review.csv").exists() else pd.DataFrame(columns=["doi", "entry_label", "verdict"])
    ent = []
    for doi in sorted(dois):
        e = ex[ex.doi == doi]
        c = cur_adj[cur_adj.doi == doi]
        um = e[~e.index.isin(matched_ex)]
        rv = review[review.doi.str.lower() == doi]
        verified = sum(1 for lbl in um.entry_label if (rv[rv.entry_label == lbl].verdict.astype(str).str.startswith("correct")).any())
        ent.append({"doi": doi, "ref": REF[doi], "curated": len(c), "extracted": len(e),
                    "matched": int(e.index.isin(matched_ex).sum()),
                    "matched_with_X_and_S": int((e.index.isin(matched_ex) & e.X_CO2_pct.notna() & e.S_MeOH_pct.notna()).sum()),
                    "recall": round(e.index.isin(matched_ex).sum() / len(c), 3) if len(c) else None,
                    "unmatched_extracted": len(um), "unmatched_verified_correct": verified,
                    "precision_matched_only": round(e.index.isin(matched_ex).sum() / len(e), 3) if len(e) else None,
                    "precision_with_review": round((e.index.isin(matched_ex).sum() + verified) / len(e), 3) if len(e) else None})
    ent = pd.DataFrame(ent)
    num = ["curated", "extracted", "matched", "matched_with_X_and_S", "unmatched_extracted", "unmatched_verified_correct"]
    totals = []
    for label, part in (("TOTAL themecat", ent[ent.ref == "themecat"]), ("TOTAL suvarna", ent[ent.ref == "suvarna"]),
                        ("TOTAL review", ent[ent.ref == "review"]), ("TOTAL", ent)):
        if part.empty:
            continue
        tot = part[num].sum()
        totals.append({"doi": label, **tot.to_dict(),
                       "recall": round(tot.matched / tot.curated, 3) if tot.curated else None,
                       "precision_matched_only": round(tot.matched / tot.extracted, 3),
                       "precision_with_review": round((tot.matched + tot.unmatched_verified_correct) / tot.extracted, 3)})
    ent = pd.concat([ent, pd.DataFrame(totals)])

    # unmatched lists for the hand review
    um_all = ex[(~ex.index.isin(matched_ex)) & (ex.doi != GOTHE_DOI)][
        ["doi", "entry_label", "catalyst_name", "T_K", "P_bar", "X_CO2_pct", "S_MeOH_pct", "S_CO_pct", "data_source_type", "primary_location", "primary_page"]]
    um_cur = cur_adj[~cur_adj.index.isin(matched_cur)][["doi", "catalyst_name", "temperature_k", "pressure_bar", "CO2_conversion", "selectivity_CH3OH", "STY_g_per_gcath"]]

    gres, gsum = gothe_eval(ex)

    EVAL.mkdir(exist_ok=True)
    pd.DataFrame([{"ex_id": a, "cur_id": b, "doi": ex.at[a, "doi"], "ex_catalyst": ex.at[a, "catalyst_name"],
                   "cur_catalyst": cur_adj.at[b, "catalyst_name"], "T_ex": ex.at[a, "T_K"], "T_cur": cur_adj.at[b, "temperature_k"],
                   "P_ex": ex.at[a, "P_bar"], "P_cur_adj": cur_adj.at[b, "pressure_bar"]} for a, b in pairs]).to_csv(EVAL / "matches.csv", index=False)
    fs.to_csv(EVAL / "field_scores.csv", index=False)
    fsum.to_csv(EVAL / "field_accuracy.csv", index=False)
    fsum_src.to_csv(EVAL / "field_accuracy_by_source.csv", index=False)
    fsum_ref.to_csv(EVAL / "field_accuracy_by_reference.csv", index=False)
    ent.to_csv(EVAL / "entry_metrics.csv", index=False)
    um_all.to_csv(EVAL / "unmatched_extracted.csv", index=False)
    um_cur.to_csv(EVAL / "unmatched_curated.csv", index=False)
    errata_log.to_csv(EVAL / "errata_applied.csv", index=False)
    gres.to_csv(EVAL / "gothe_table4_scores.csv", index=False)
    summary = {"field_accuracy": fsum.to_dict("records"), "entry_metrics": ent.to_dict("records"), "gothe": gsum,
               "n_errata_cells": len(errata_log)}
    (EVAL / "summary.json").write_text(json.dumps(summary, indent=1, default=str), encoding="utf-8")

    pd.set_option("display.width", 220)
    print("FIELD ACCURACY\n", fsum.to_string(index=False))
    print("\nBY SOURCE TYPE (adjudicated)\n", fsum_src.to_string(index=False))
    print("\nBY REFERENCE SET (adjudicated)\n", fsum_ref.to_string(index=False))
    print("\nENTRIES\n", ent.to_string(index=False))
    print("\nGOTHE", gsum)
    print(f"\nerrata cells applied: {len(errata_log)}")


if __name__ == "__main__":
    main()
