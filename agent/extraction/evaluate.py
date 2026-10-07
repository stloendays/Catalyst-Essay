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
    """Element symbols named in the texts. A symbol must not run on into a lowercase letter ('Carbon' is not Ca,
    'Nickel' is not Ni), and a symbol followed by a zero amount in a catalyst code ('CHT-Y0': Y fraction 0) is
    absent."""
    found = set()
    for t in texts:
        if not isinstance(t, str):
            continue
        for m in re.finditer(r"([A-Z][a-z]?)(?![a-z])(0(?:\.0*)?(?![\d.]))?", t):
            if m.group(1) in ELEMENTS and not m.group(2):
                found.add(m.group(1))
    return frozenset(found)


SUVARNA_COMP = ("elements", "loading", "active_elements", "element_loading")


def suvarna_composition(name: str):
    """Composition of a Suvarna row from its constructed name '<family> <wt> wt% /<support> ... +<promoter> <wt> wt%':
    all elements, the family metal loading, the active elements (family metal(s) and promoters with a loading > 0;
    a promoter at 0 wt% is absent) and the wt% of each active element."""
    fam, load = re.match(r"(\S+)\s+([\d.eE+-]+) wt%", name).groups()
    fam_el = set(FAMILY_ELEMENTS.get(fam, elements_in(fam)))
    loads = {el: float(load) for el in fam_el}
    for p, pl in re.findall(r"\+(\S+)\s+([\d.eE+-]+) wt%", name):
        if float(pl) > 0:
            for el in elements_in(p):
                loads[el] = float(pl)
    supports = elements_in(*re.findall(r"/(\S+)", name))
    return frozenset(set(loads) | supports), float(load), frozenset(loads), loads


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
        comp.append(" ".join(parts))
    out["catalyst_name"] = comp
    for col, vals in zip(SUVARNA_COMP, zip(*(suvarna_composition(n) for n in comp))):
        out[col] = list(vals)
    # The Suvarna set lists some bimetallic catalysts twice, once under each family (e.g. Cu-In/CeO2 as a Cu row
    # and as an In2O3 row with the same conditions and STY); one copy is kept.
    out["_key"] = [(r.doi, r.temperature_k, r.pressure_bar, r.pH2_pCO2_ratio, r.GHSV_nlph_gcat, round(r.STY_g_per_gcath, 9),
                    r.elements) for r in out.itertuples()]
    out = out.drop_duplicates("_key").drop(columns="_key")
    out["cur_id"] = ["S%d" % i for i in out.index]
    out.index = out.cur_id
    return out


# ---------------------------------------------------------------- matching ------------------------------------------
# Pairs are formed on the paper, the catalyst identity (name rules; for Suvarna the composition) and the test
# conditions only. No value that is scored afterwards (X, S, STY) and no presence or absence of such a value enters a
# pairing. Among the admissible pairs a one-to-one assignment minimises the condition (and composition) cost; ties are
# broken by the extraction pass (main text before SI before plots) and then by document order, never by a scored
# value. A pair is ambiguous when its curated row has another admissible extracted partner, or its extracted entry
# another admissible curated row, at the same cost (identical name and conditions within AMB_EPS): the matcher has no
# information to choose. Ambiguous pairs count for recall and are excluded from field accuracy.
BIG = 1e6
AMB_EPS = 0.1          # cost units: 0.3 K, 0.5 % in P, 1 % in H2/CO2 or GHSV
PASS_RANK = {"main": 0, "si": 1, "figures": 2, "si_figures": 3}


def condition_cost(e, c, p_missing_ok=False):
    """Gate and cost on the test conditions: |dT| <= 3 K, |dP|/P <= 5 %, H2/CO2 and mass GHSV within 10 % when both
    present (GHSV on the total-feed or the inert-free basis). Returns None when a gate fails."""
    if pd.isna(e.T_K) or pd.isna(c.temperature_k) or abs(e.T_K - c.temperature_k) > 3:
        return None
    if pd.isna(e.P_bar):
        if not p_missing_ok:
            return None
        cost = 1.0
    elif pd.isna(c.pressure_bar) or abs(e.P_bar - c.pressure_bar) > 0.05 * c.pressure_bar:
        return None
    else:
        cost = abs(e.P_bar - c.pressure_bar) / c.pressure_bar / 0.05
    cost += abs(e.T_K - c.temperature_k) / 3
    if pd.notna(e.H2_CO2) and pd.notna(c.pH2_pCO2_ratio):
        d = abs(e.H2_CO2 - c.pH2_pCO2_ratio) / c.pH2_pCO2_ratio
        if d > 0.10:
            return None
        cost += d / 0.10
    if pd.notna(e.GHSV_NL_gcat_h) and pd.notna(c.GHSV_nlph_gcat):
        d = min(abs(g - c.GHSV_nlph_gcat) / c.GHSV_nlph_gcat
                for g in (e.GHSV_NL_gcat_h, e.get("GHSV_inert_free_NL_gcat_h")) if pd.notna(g))
        if d > 0.10:
            return None
        cost += d / 0.10
    return cost


def assign(ex: pd.DataFrame, cur: pd.DataFrame, pair_cost) -> list[tuple]:
    """One-to-one assignment on pair_cost(e, c) (None = not admissible). Returns (ex_id, cur_id, ambiguous)."""
    if ex.empty or cur.empty:
        return []
    C = np.full((len(ex), len(cur)), BIG)
    for i, (_, e) in enumerate(ex.iterrows()):
        for j, (_, c) in enumerate(cur.iterrows()):
            v = pair_cost(e, c)
            if v is not None:
                C[i, j] = v
    # tie-breaks: extraction pass (0.05 per rank) and document order (1e-6 x distance of the relative positions)
    rank = np.array([PASS_RANK.get(p, 0) for p in (ex["pass"] if "pass" in ex else ["main"] * len(ex))], dtype=float)
    pos_e = np.arange(len(ex)) / max(len(ex) - 1, 1)
    pos_c = np.arange(len(cur)) / max(len(cur) - 1, 1)
    T = 0.05 * rank[:, None] + 1e-6 * np.abs(pos_e[:, None] - pos_c[None, :])
    rows, cols = linear_sum_assignment(np.where(C < BIG, C + T, BIG))
    out = []
    for r, c in zip(rows, cols):
        if C[r, c] >= BIG:
            continue
        col_riv = (C[:, c] < BIG) & (np.abs(C[:, c] - C[r, c]) <= AMB_EPS)
        row_riv = (C[r, :] < BIG) & (np.abs(C[r, :] - C[r, c]) <= AMB_EPS)
        out.append((ex.index[r], cur.index[c], bool(col_riv.sum() > 1 or row_riv.sum() > 1)))
    return out


def extracted_active_elements(e) -> frozenset:
    """Active metals and promoters as the extraction states them (empty when it states neither)."""
    return elements_in(e.active_metals, e.promoters)


def match_doi_suvarna(ex: pd.DataFrame, cur: pd.DataFrame) -> list[tuple]:
    """Suvarna rows have no names. Gates: the conditions (an extracted record without a pressure can still pair:
    Ni-In-Al/SiO2 states 'ambient pressure' once and the extraction left P empty; P then scores as missing), and the
    active/promoter elements when both sides state them: every active or promoter element of one side must appear
    in the other side's composition (no Pt row for a Pd catalyst, no promoted row for the bare oxide). Cost: the
    condition cost + 3 x (element-set difference) + the relative loading difference when both sides give the
    loading of the same single active element (otherwise no loading term)."""
    els = {i: elements_in(e.catalyst_name, e.composition, e.support, e.promoters, e.active_metals)
           for i, e in ex.iterrows()}
    act = {i: extracted_active_elements(e) for i, e in ex.iterrows()}

    def cost(e, c):
        v = condition_cost(e, c, p_missing_ok=True)
        if v is None:
            return None
        e_el, e_act = els[e.name], act[e.name]
        if e_act and not (e_act <= c.elements and c.active_elements <= e_el):
            return None
        v += 3 * len(e_el ^ c.elements)
        if pd.notna(e.metal_wt_pct) and len(e_act) == 1 and next(iter(e_act)) in c.element_loading:
            ref = c.element_loading[next(iter(e_act))]
            if ref > 0:
                v += min(1.0, abs(e.metal_wt_pct - ref) / ref)
        return v

    return assign(ex, cur, cost)


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
                    for col, v in zip(SUVARNA_COMP, suvarna_composition(e.value)):
                        adj.at[idx, col] = v
            continue
        for idx in adj[m].index:
            old = adj.at[idx, e.field]
            new = old * float(e.value) if e.action == "multiply" else float(e.value)
            adj.at[idx, e.field] = new
            log.append({"cur_id": idx, "doi": e.doi, "catalyst_name": adj.at[idx, "catalyst_name"],
                        "field": e.field, "themecat": old, "pdf": new, "evidence": e.evidence})
    return adj, pd.DataFrame(log)


def match_doi(ex: pd.DataFrame, cur: pd.DataFrame, aliases: dict) -> list[tuple]:
    """TheMeCat: name rules and the condition gates; cost = condition cost (see assign for ties and ambiguity)."""
    # The prefix and one-edit rules are used only for names that have no exact or alias partner in the
    # other set, so 'Ir1Pd1-In2O3(PM)' is never paired with 'Ir1Pd1-In2O3(GM)', nor 'In2O3' with
    # 'In2O3/HZSM-5', when the exact partners exist.
    ex_names, cur_names = set(ex.catalyst_name), set(cur.catalyst_name)
    ex_strong = {a for a in ex_names if any(names_match(a, b, aliases, False) for b in cur_names)}
    cur_strong = {b for b in cur_names if any(names_match(a, b, aliases, False) for a in ex_names)}

    def cost(e, c):
        fuzzy_ok = e.catalyst_name not in ex_strong and c.catalyst_name not in cur_strong
        if not names_match(e.catalyst_name, c.catalyst_name, aliases, fuzzy_ok):
            return None
        return condition_cost(e, c)

    return assign(ex, cur, cost)


def _batch_of() -> dict:
    """DOI -> first18 (the TheMeCat papers of the first rounds), batch4 (Suvarna + Lam 2018), batch5 (TheMeCat
    papers downloaded by hand)."""
    b5 = {l.split("#")[0].strip().lower() for l in (HERE / "manual_download_dois_batch5.txt").read_text(encoding="utf-8").splitlines()}
    out = {}
    for doi, ref in REF.items():
        if ref == "themecat":
            out[doi] = "batch5" if doi in b5 else "first18"
        elif ref in ("suvarna", "review"):
            out[doi] = "batch4"
    return out


BATCH = _batch_of()
SAMPLES = {"batch4": EVAL / "batch4_unmatched_sample.csv", "batch5": EVAL / "batch5_unmatched_sample.csv"}


def precision_report(ex, matched_ex, ent, verdict_of) -> dict:
    """Precision over all extracted entries, and the share of unmatched entries that are correct."""
    tot = ent.set_index("doi")
    out = {}
    r = tot.loc["TOTAL first 18 TheMeCat papers"]
    out["first18"] = dict(
        extracted=int(r.extracted), matched=int(r.matched), unmatched=int(r.unmatched_extracted),
        unmatched_correct=int(r.unmatched_reviewed_correct), unmatched_duplicate=int(r.unmatched_reviewed_duplicate),
        unmatched_wrong=int(r.unmatched_reviewed_wrong), unmatched_unreviewed=int(r.unmatched_unreviewed),
        share_of_unmatched_correct=round(r.unmatched_reviewed_correct / r.unmatched_extracted, 4),
        share_of_reviewed_unmatched_correct=round(r.unmatched_reviewed_correct / max(
            r.unmatched_extracted - r.unmatched_unreviewed, 1), 4),
        precision_all_extracted=round((r.matched + r.unmatched_reviewed_correct) / r.extracted, 4))
    # sampled batches: re-check each sampled entry's status under the current matching
    key_ex = {(d, l): i for i, d, l in zip(ex.index, ex.doi, ex.entry_label)}
    strata, changed = {}, []
    for b, path in SAMPLES.items():
        s = pd.read_csv(path)
        s["doi"] = s.doi.str.lower()
        s["ok"] = s.verdict.astype(str).str.lower().str.startswith("correct")
        s["now_matched"] = [key_ex.get((d, l)) in matched_ex for d, l in zip(s.doi, s.entry_label)]
        s["found"] = [(d, l) in key_ex for d, l in zip(s.doi, s.entry_label)]
        changed += [dict(batch=b, doi=x.doi, entry_label=x.entry_label, verdict=x.verdict,
                         status="matched now" if x.now_matched else "not in extraction") for x in s.itertuples()
                    if x.now_matched or not x.found]
        keep = s[~s.now_matched & s.found]
        rb = tot.loc["TOTAL batch 4 (Suvarna + Lam 2018)" if b == "batch4" else "TOTAL batch 5 (TheMeCat by hand)"]
        p = float(keep.ok.mean())
        strata[b] = dict(extracted=int(rb.extracted), matched=int(rb.matched), unmatched=int(rb.unmatched_extracted),
                         sample=int(len(s)), sample_still_unmatched=int(len(keep)), sample_correct=int(keep.ok.sum()),
                         share_correct=round(p, 4),
                         precision_all_extracted=round((rb.matched + rb.unmatched_extracted * p) / rb.extracted, 4))
    U = sum(v["unmatched"] for v in strata.values())
    w = {b: v["unmatched"] / U for b, v in strata.items()}
    pw = sum(w[b] * v["share_correct"] for b, v in strata.items())
    se = np.sqrt(sum(w[b] ** 2 * v["share_correct"] * (1 - v["share_correct"]) / v["sample_still_unmatched"]
                     for b, v in strata.items()))
    E = sum(v["extracted"] for v in strata.values())
    M_ = sum(v["matched"] for v in strata.values())
    out["added31"] = dict(
        strata=strata, pooled_sample=f"{sum(v['sample_correct'] for v in strata.values())}/"
                                    f"{sum(v['sample_still_unmatched'] for v in strata.values())}",
        share_of_unmatched_correct_weighted=round(pw, 4), share_ci95_weighted=[round(pw - 1.96 * se, 4),
                                                                               round(pw + 1.96 * se, 4)],
        extracted=E, matched=M_, unmatched=U, precision_all_extracted=round((M_ + U * pw) / E, 4),
        sampled_entries_changed_status=changed)
    return out


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
    for ei, ci, amb in pairs:
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
                            "truth": truth_name, "extracted": ev, "curated": tv, "ambiguous": amb,
                            "source_type": field_source(e, f), "strict": status_s, "loose": status_l})
    return pd.DataFrame(out)


def summarize_fields(fs: pd.DataFrame, by=("truth", "field")) -> pd.DataFrame:
    """Field accuracy on the unambiguous pairs (n_curated ... n_not_comparable); n_ambiguous counts the curated
    values of ambiguous pairs, which are not scored."""
    rows = []
    for key, g in fs.groupby(list(by)):
        amb = g[g.ambiguous]
        g = g[~g.ambiguous]
        n = len(g)
        rec = dict(zip(by, key if isinstance(key, tuple) else (key,)))
        cmp_s = g[g.strict.isin(["correct", "wrong"])]
        rec.update({
            "n_curated": n,
            "n_extracted": len(cmp_s),
            "n_correct_strict": int((cmp_s.strict == "correct").sum()),
            "coverage": round(len(cmp_s) / n, 3) if n else None,
            "acc_strict": round((cmp_s.strict == "correct").mean(), 3) if len(cmp_s) else None,
            "acc_loose": round((cmp_s.loose == "correct").mean(), 3) if len(cmp_s) else None,
            "n_missing": int((g.strict == "missing").sum()),
            "n_not_comparable": int((g.strict == "not_comparable_basis").sum()),
            "n_ambiguous": len(amb),
            "n_ambiguous_compared": int(amb.strict.isin(["correct", "wrong"]).sum()),
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
    ambiguous_pairs = sum(1 for p in pairs if p[2])

    fs = field_scores(pairs, ex, cur_raw, cur_adj)
    fs["ref"] = fs.doi.map(REF)
    fsum = summarize_fields(fs)
    fsum_src = summarize_fields(fs[fs.truth == "adjudicated"], by=("source_type", "field"))
    fsum_ref = summarize_fields(fs[fs.truth == "adjudicated"], by=("ref", "field"))

    # entry-level recall / precision
    # First 18 TheMeCat papers: every unmatched extracted entry has a hand verdict in unmatched_review.csv (entries
    # that became unmatched after the review count as unreviewed). The 31 papers added later (batch 4: Suvarna and
    # Lam 2018; batch 5: TheMeCat by hand) were checked in random samples of their unmatched entries; precision there
    # is estimated stratum by stratum. A duplicate of a matched entry is not a correct additional entry.
    review = pd.read_csv(EVAL / "unmatched_review.csv") if (EVAL / "unmatched_review.csv").exists() else pd.DataFrame(columns=["doi", "entry_label", "verdict"])
    review["doi"] = review.doi.str.lower()
    verdict_of = {(r.doi, r.entry_label): str(r.verdict) for r in review.itertuples()}
    ent = []
    for doi in sorted(dois):
        e = ex[ex.doi == doi]
        c = cur_adj[cur_adj.doi == doi]
        um = e[~e.index.isin(matched_ex)]
        v = [verdict_of.get((doi, lbl)) for lbl in um.entry_label]
        correct = sum(1 for x in v if x and x.startswith("correct") and x != "correct_duplicate")
        dup = sum(1 for x in v if x == "correct_duplicate")
        wrong = sum(1 for x in v if x and x.startswith("wrong"))
        ent.append({"doi": doi, "ref": REF[doi], "batch": BATCH.get(doi, ""), "curated": len(c), "extracted": len(e),
                    "matched": int(e.index.isin(matched_ex).sum()),
                    "matched_ambiguous": sum(1 for p in pairs if p[2] and p[0] in e.index),
                    "matched_with_X_and_S": int((e.index.isin(matched_ex) & e.X_CO2_pct.notna() & e.S_MeOH_pct.notna()).sum()),
                    "recall": round(e.index.isin(matched_ex).sum() / len(c), 3) if len(c) else None,
                    "unmatched_extracted": len(um), "unmatched_reviewed_correct": correct,
                    "unmatched_reviewed_duplicate": dup, "unmatched_reviewed_wrong": wrong,
                    "unmatched_unreviewed": len(um) - correct - dup - wrong,
                    "precision_matched_only": round(e.index.isin(matched_ex).sum() / len(e), 3) if len(e) else None})
    ent = pd.DataFrame(ent)
    num = ["curated", "extracted", "matched", "matched_ambiguous", "matched_with_X_and_S", "unmatched_extracted",
           "unmatched_reviewed_correct", "unmatched_reviewed_duplicate", "unmatched_reviewed_wrong", "unmatched_unreviewed"]
    totals = []
    for label, part in (("TOTAL themecat", ent[ent.ref == "themecat"]), ("TOTAL suvarna", ent[ent.ref == "suvarna"]),
                        ("TOTAL review", ent[ent.ref == "review"]),
                        ("TOTAL first 18 TheMeCat papers", ent[ent.batch == "first18"]),
                        ("TOTAL batch 4 (Suvarna + Lam 2018)", ent[ent.batch == "batch4"]),
                        ("TOTAL batch 5 (TheMeCat by hand)", ent[ent.batch == "batch5"]),
                        ("TOTAL 31 added papers", ent[ent.batch.isin(["batch4", "batch5"])]), ("TOTAL", ent)):
        if part.empty:
            continue
        tot = part[num].sum()
        totals.append({"doi": label, **tot.to_dict(),
                       "recall": round(tot.matched / tot.curated, 3) if tot.curated else None,
                       "precision_matched_only": round(tot.matched / tot.extracted, 3)})
    ent = pd.concat([ent, pd.DataFrame(totals)])
    precision = precision_report(ex, matched_ex, ent, verdict_of)

    # unmatched lists for the hand review
    um_all = ex[(~ex.index.isin(matched_ex)) & (ex.doi != GOTHE_DOI)][
        ["doi", "entry_label", "catalyst_name", "T_K", "P_bar", "X_CO2_pct", "S_MeOH_pct", "S_CO_pct", "data_source_type", "primary_location", "primary_page"]]
    um_cur = cur_adj[~cur_adj.index.isin(matched_cur)][["doi", "catalyst_name", "temperature_k", "pressure_bar", "CO2_conversion", "selectivity_CH3OH", "STY_g_per_gcath"]]

    gres, gsum = gothe_eval(ex)

    EVAL.mkdir(exist_ok=True)
    pd.DataFrame([{"ex_id": a, "cur_id": b, "doi": ex.at[a, "doi"], "ex_catalyst": ex.at[a, "catalyst_name"],
                   "cur_catalyst": cur_adj.at[b, "catalyst_name"], "T_ex": ex.at[a, "T_K"], "T_cur": cur_adj.at[b, "temperature_k"],
                   "P_ex": ex.at[a, "P_bar"], "P_cur_adj": cur_adj.at[b, "pressure_bar"], "ambiguous": amb}
                  for a, b, amb in pairs]).to_csv(EVAL / "matches.csv", index=False)
    fs.to_csv(EVAL / "field_scores.csv", index=False)
    fsum.to_csv(EVAL / "field_accuracy.csv", index=False)
    fsum_src.to_csv(EVAL / "field_accuracy_by_source.csv", index=False)
    fsum_ref.to_csv(EVAL / "field_accuracy_by_reference.csv", index=False)
    ent.to_csv(EVAL / "entry_metrics.csv", index=False)
    um_all.to_csv(EVAL / "unmatched_extracted.csv", index=False)
    um_cur.to_csv(EVAL / "unmatched_curated.csv", index=False)
    errata_log.to_csv(EVAL / "errata_applied.csv", index=False)
    gres.to_csv(EVAL / "gothe_table4_scores.csv", index=False)
    f = errata_log.field.astype(str)
    errata = {"log_rows": len(errata_log), "rows_dropped": int((f == "(row dropped)").sum()),
              "rows_renamed": int((f == "catalyst_name").sum()),
              "cells_set_to_missing": int(((f != "(row dropped)") & (f != "catalyst_name") & errata_log.pdf.isna()).sum()),
              "cells_corrected": int(((f != "(row dropped)") & (f != "catalyst_name") & errata_log.pdf.notna()).sum()),
              "by_reference": {k: {"cells": int((g.field != "(row dropped)").sum()),
                                   "rows_dropped": int((g.field == "(row dropped)").sum())}
                               for k, g in errata_log.groupby("ref")}}
    summary = {"matching": {"pairs": len(pairs), "ambiguous_pairs": ambiguous_pairs, "amb_eps": AMB_EPS},
               "field_accuracy": fsum.to_dict("records"), "entry_metrics": ent.to_dict("records"),
               "precision": precision, "gothe": gsum, "errata": errata}
    (EVAL / "summary.json").write_text(json.dumps(summary, indent=1, default=str), encoding="utf-8")

    pd.set_option("display.width", 220)
    print("FIELD ACCURACY\n", fsum.to_string(index=False))
    print("\nBY SOURCE TYPE (adjudicated)\n", fsum_src.to_string(index=False))
    print("\nBY REFERENCE SET (adjudicated)\n", fsum_ref.to_string(index=False))
    print("\nENTRIES\n", ent.to_string(index=False))
    print("\nGOTHE", gsum)
    print("\nMATCHING", summary["matching"])
    print("\nPRECISION", json.dumps(precision, indent=1, default=str))
    print("\nERRATA", errata)


if __name__ == "__main__":
    main()
