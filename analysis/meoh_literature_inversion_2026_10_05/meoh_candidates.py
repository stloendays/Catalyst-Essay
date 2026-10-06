"""Candidate construction from extracted methanol records, and the Gothe Table 4 self-check.

Shared by run_literature_inversion.py and the ACSA self-check gate (agent/selfcheck_gate.py), so both run the
same code path.
"""
import math
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "data" / "meoh"))
import meoh_general_model as G  # noqa: E402

RECORDS = REPO / "agent" / "extraction" / "out" / "records_normalized.csv"
TABLE4 = REPO / "analysis" / "meoh_general_model_2026_10_05" / "table4_candidate_results.csv"
GOTHE_DOI = "10.1021/acscatal.5c05984"
VM, MW_MEOH = 22.414, 32.042
RHO_DEFAULT, RHO_RANGE = 1.0, (0.5, 2.0)
REQUIRED = ["X_CO2_pct", "S_MeOH_pct", "P_bar", "H2_CO2", "T_K"]


def pct(v, q):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return None
    return 0.0 if str(q).strip() == "<" else float(v) / 100.0


def closure(r):
    sm = pct(r.S_MeOH_pct, r.S_MeOH_q)
    sco = pct(r.S_CO_pct, r.S_CO_q)
    sch4 = pct(r.S_CH4_pct, r.S_CH4_q)
    if sch4 is None:
        sch4 = max(0.0, 1.0 - sm - sco) if sco is not None else 0.0
    reported_sum = sm + (sco or 0.0) + sch4
    sm, sco_c, sch4 = G.close_selectivity(sm, None, min(sch4, 1.0 - sm))
    return sm, sco_c, sch4, reported_sum


def vol_ghsv(raw):
    s = str(raw).replace("−", "-").lower()
    if "h-1" not in s and "h−1" not in s:
        return None
    try:
        return float(s.split("h")[0].replace(",", "").strip())
    except ValueError:
        return None


def candidate_row(r):
    """One extracted record -> one candidate operating point, or None if it has no conversion or methanol."""
    X = float(r.X_CO2_pct) / 100.0
    sm, sco, sch4, rep = closure(r)
    if X <= 0 or sm <= 0:
        return None
    inert = 0.0 if pd.isna(r.inert_frac) else float(r.inert_frac)
    y_co2 = (1.0 - inert) / (1.0 + float(r.H2_CO2))
    sty_print = float(r.STY_g_gcat_h) if pd.notna(r.STY_g_gcat_h) and pd.notna(r.STY_q) else None
    sty_mass = (float(r.GHSV_NL_gcat_h) * y_co2 * X * sm / VM * MW_MEOH) if pd.notna(r.GHSV_NL_gcat_h) else None
    gv = vol_ghsv(r.GHSV_raw) if pd.isna(r.GHSV_NL_gcat_h) else None
    sty_vol = (gv / (RHO_DEFAULT * 1000.0) * y_co2 * X * sm / VM * MW_MEOH) if gv else None
    gkey = (f"{float(r.GHSV_NL_gcat_h):.3g} NL/g/h" if pd.notna(r.GHSV_NL_gcat_h)
            else (f"{gv:g} h-1" if gv else str(r.GHSV_raw)))
    plot_read = "~" in (str(r.X_CO2_q), str(r.S_MeOH_q))
    return dict(doi=r.doi, entry=r.entry_label, catalyst=f"{r.catalyst_name} [{r.entry_label}]", T_C=float(r.T_K) - 273.15,
                P_bar=float(r.P_bar), h2_co2=float(r.H2_CO2), ghsv_key=gkey, X=X, SMeOH=sm, SCO=sco,
                SCH4=sch4, reported_S_sum=rep, other_products=rep < 0.95, plot_read=plot_read,
                sty_print=sty_print, sty_mass=sty_mass, sty_vol=sty_vol, gv=gv, y_co2=y_co2,
                source=r.data_source_type, location=r.primary_location)


def gothe_selfcheck(got: pd.DataFrame) -> pd.DataFrame:
    """Run the extracted Gothe et al. 2025 Table 4 candidates through the methanol model and compare with the
    frozen Table 4 costs (inert and recycled CO, 2 % purge)."""
    t4 = pd.read_csv(TABLE4)
    got = got.copy()
    got["row"] = got.entry.str.extract(r"row (\d+)").astype(float)
    check = []
    for r in got.itertuples():
        ref = t4.iloc[int(r.row) - 1]
        for tag, xco in (("inert", "inert"), ("rec", "recycled_central")):
            # every input from the Agent's extraction (STY printed per g Re, converted with the extracted loading)
            c = G.cost(dict(X=r.X, SMeOH=r.SMeOH, SCH4=r.SCH4, SCO=r.SCO), STY_per_g_cat=r.sty_print,
                       P_bar=r.P_bar, h2_co2=r.h2_co2, T_C=r.T_C, x_co=xco, purge=0.02)["cost_eur_t"]
            check.append(dict(id=ref.id, canonical_state=ref.canonical_state if isinstance(ref.canonical_state, str) else "",
                              treatment=tag, frozen=float(ref[f"{tag}_NPC_2pct"]), agent=float(c),
                              abs_diff=abs(float(c) - float(ref[f"{tag}_NPC_2pct"]))))
    return pd.DataFrame(check)


def gothe_candidates(records: pd.DataFrame = None) -> pd.DataFrame:
    d = pd.read_csv(RECORDS) if records is None else records
    d = d[d.doi == GOTHE_DOI].dropna(subset=REQUIRED)
    return pd.DataFrame([c for c in (candidate_row(r) for _, r in d.iterrows()) if c is not None])
