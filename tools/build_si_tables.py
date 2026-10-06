"""Write docs/SI_TABLES.md, the data tables of the Supplementary Information.

Every number is read from the repository files named in each table's caption; nothing is typed by hand. Journal
names (and author spellings with accents or spaces) come from Crossref, cached in docs/SI_TABLES_crossref.json so
that the build is reproducible offline; `--refresh` fetches the cache again.

    CatalystForge/.venv/python tools/build_si_tables.py [--refresh]
"""
import ast
import html
import json
import math
import re
import sys
import time
import unicodedata
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/SI_TABLES.md"
CACHE = ROOT / "docs/SI_TABLES_crossref.json"

EX = ROOT / "agent/extraction"
NF = ROOT / "agent/nh3_field"
INV = ROOT / "analysis/meoh_literature_inversion_2026_10_05"
FIELD = ROOT / "analysis/nh3_field_2026_10_06"
BENCH = ROOT / "analysis/meoh_plant_benchmark_2026_10_06"
ALLOY = ROOT / "analysis/nh3_alloy_extension_2026_10_05"
BRIDGE = ROOT / "analysis/fe_bridge_backward_2026_09_29"
SUPP = ROOT / "agent/nh3_supported"


def rel(p):
    return "`" + Path(p).relative_to(ROOT).as_posix() + "`"


# ---- formatting ---------------------------------------------------------------------------------------------
class Raw(str):
    """Cell text written here with intended markup (*italic*, _{subscript}); not escaped."""


def cell(x):
    """Markdown-safe cell text: single line, no pipes, literal asterisks and underscores escaped (a whole **bold**
    cell and Raw text keep their markup); None or NaN prints as an en dash, an empty string stays empty."""
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "–"
    if isinstance(x, Raw):
        return str(x)
    s = " ".join(str(x).split())
    if len(s) > 4 and s.startswith("**") and s.endswith("**"):
        return "**" + cell(s[2:-2]) + "**"
    return s.replace("|", "/").replace("*", "\\*").replace("_", "\\_")


def num(x, nd=None):
    """Number as printed in a table: thousands separator, minus sign, `nd` decimals or 4 significant digits."""
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "–"
    x = float(x)
    if nd is not None:
        s = f"{x:,.{nd}f}"
    elif x == int(x) and abs(x) < 1e7:
        s = f"{int(x):,}"
    elif abs(x) >= 1000:
        s = f"{x:,.0f}"
    else:
        s = f"{x:.4g}"
        if "e" in s:
            s = f"{x:.2e}"
    return s.replace("-", "−")


def pct(x, nd=1):
    return num(100 * x, nd) + " %"


def table(header, rows):
    out = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    out += ["| " + " | ".join(cell(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def block(n, title, caption, header, rows):
    return f"### Supplementary Table {n} | {title}\n\n{caption}\n\n{table(header, rows)}\n"


# ---- paper sets and Crossref metadata ------------------------------------------------------------------------
def paper_set(path):
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.split("#")[0].strip()
        if line:
            doi, tag = line.split()[:2]
            out.append((doi, tag))
    return out


def manifest(path):
    return {r["doi"].lower(): r for r in json.loads(path.read_text(encoding="utf-8")) if r.get("doi")}


def crossref(dois, refresh=False):
    cache = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() and not refresh else {}
    todo = [d for d in dois if d.lower() not in cache]
    for i, d in enumerate(todo):
        req = urllib.request.Request(f"https://api.crossref.org/works/{d}",
                                     headers={"User-Agent": "Catalyst-Essay SI table builder"})
        m = json.loads(urllib.request.urlopen(req, timeout=30).read())["message"]
        issued = (m.get("issued") or {}).get("date-parts", [[None]])[0][0]
        authors = m.get("author") or []
        cache[d.lower()] = dict(
            title=(m.get("title") or [""])[0],
            journal=(m.get("container-title") or [""])[0],
            journal_short=(m.get("short-container-title") or [""])[0],
            volume=m.get("volume", ""), page=m.get("page") or m.get("article-number", ""),
            year=issued, first_author=(authors[0].get("family") or authors[0].get("name", "")) if authors else "")
        if i < len(todo) - 1:
            time.sleep(0.3)
    if todo or refresh:
        CACHE.write_text(json.dumps(dict(sorted(cache.items())), indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return cache


def ascii_letters(s):
    s = unicodedata.normalize("NFKD", s)
    return re.sub(r"[^a-z]", "", s.encode("ascii", "ignore").decode().lower())


NOTES = []

# ISO 4 abbreviations of the journals in the two paper sets (Crossref's short titles are inconsistent)
ISO4 = {
    "ACS Applied Energy Materials": "ACS Appl. Energy Mater.", "ACS Applied Materials & Interfaces": "ACS Appl. Mater. Interfaces",
    "ACS Catalysis": "ACS Catal.", "ACS Omega": "ACS Omega", "ACS Sustainable Chemistry & Engineering": "ACS Sustain. Chem. Eng.",
    "Advanced Energy Materials": "Adv. Energy Mater.", "Advanced Materials": "Adv. Mater.",
    "Angewandte Chemie International Edition": "Angew. Chem. Int. Ed.", "Applied Catalysis A: General": "Appl. Catal. A",
    "Applied Catalysis B: Environmental": "Appl. Catal. B", "Catal. Sci. Technol.": "Catal. Sci. Technol.",
    "Catalysis Letters": "Catal. Lett.", "Catalysis Science & Technology": "Catal. Sci. Technol.",
    "Catalysis Today": "Catal. Today", "ChemCatChem": "ChemCatChem", "ChemPhysChem": "ChemPhysChem",
    "Chemical Communications": "Chem. Commun.", "Chemical Engineering Journal": "Chem. Eng. J.",
    "Chemical Science": "Chem. Sci.", "Chemistry An Asian Journal": "Chem. Asian J.", "ChemistrySelect": "ChemistrySelect",
    "Energy Technology": "Energy Technol.", "Fuel": "Fuel", "Green Chemistry": "Green Chem.",
    "Industrial & Engineering Chemistry Research": "Ind. Eng. Chem. Res.", "Inorganic Chemistry Frontiers": "Inorg. Chem. Front.",
    "Journal of CO2 Utilization": "J. CO2 Util.", "Journal of Catalysis": "J. Catal.",
    "Journal of Environmental Sciences": "J. Environ. Sci.", "Journal of Materials Chemistry A": "J. Mater. Chem. A",
    "Journal of the American Chemical Society": "J. Am. Chem. Soc.", "Molecular Catalysis": "Mol. Catal.",
    "Nature": "Nature", "Nature Chemistry": "Nat. Chem.", "Nature Communications": "Nat. Commun.",
    "RSC Advances": "RSC Adv.", "Science Advances": "Sci. Adv.",
}


def iso4(title):
    t = " ".join(html.unescape(title).split())
    t = re.sub(r"^Chemistry\W+An Asian Journal$", "Chemistry An Asian Journal", t)
    if t not in ISO4:
        NOTES.append(f"no ISO 4 abbreviation for {t!r}; full title used")
    return ISO4.get(t, t)


def bib(doi, fm, cr):
    """First author and year from the fetch-manifest file name, journal from Crossref."""
    name = fm[doi.lower()]["file"]
    author, year = name.split("_")[:2]
    meta = cr[doi.lower()]
    if ascii_letters(meta["first_author"]) == ascii_letters(author):
        author = meta["first_author"]          # keeps accents and spaces the file name drops
    else:
        NOTES.append(f"{doi}: file name author {author!r}, Crossref {meta['first_author']!r}")
    if str(meta["year"]) != year:
        NOTES.append(f"{doi}: file name year {year}, Crossref {meta['year']}")
    return author, int(year), iso4(meta["journal"])


# ---- Supplementary Table 1: methanol extraction set ----------------------------------------------------------
def table1(cr):
    ps = paper_set(EX / "paper_set.txt")
    fm, sm = manifest(EX / "fetch_manifest.json"), manifest(EX / "si_manifest.json")
    em = pd.read_csv(EX / "eval/entry_metrics.csv").set_index("doi")
    rec = pd.read_csv(EX / "out/records_normalized.csv").groupby("doi").size()
    gothe = pd.read_csv(EX / "eval/gothe_table4_scores.csv")
    cand = pd.read_csv(INV / "literature_candidates.csv").groupby("doi").size()
    label = {"gothe": "Gothe (Table 4)", "themecat": "TheMeCat", "suvarna": "Suvarna", "review": "PDF review"}
    rows, tot = [], dict(cur=0, ext=0, mat=0, si=0, cand=0)
    for doi, ref in ps:
        author, year, journal = bib(doi, fm, cr)
        if ref == "gothe":
            cur, ext, mat = len(gothe), int(rec.get(doi, 0)), int(gothe.matched.sum())
        else:
            e = em.loc[doi]
            cur, ext, mat = int(e.curated), int(e.extracted), int(e.matched)
        assert ext == int(rec.get(doi, 0)), doi
        si = sm[doi.lower()]
        nsi = len(si["files"]) if si["status"] == "ok" else 0
        nc = int(cand.get(doi, 0))
        tot["cur"] += cur; tot["ext"] += ext; tot["mat"] += mat; tot["si"] += nsi > 0; tot["cand"] += nc
        rows.append([author, year, journal, doi, label[ref], num(cur) if cur else "–", num(ext),
                     num(mat) if cur else "–", f"yes ({nsi})" if nsi else "no", num(nc) if nc else "–"])
    rows.append(["**Total**", "", "", f"**{len(ps)} papers**", "", f"**{num(tot['cur'])}**", f"**{num(tot['ext'])}**",
                 f"**{num(tot['mat'])}**", f"**{tot['si']}**", f"**{num(tot['cand'])}**"])
    assert tot["cand"] == pd.read_csv(INV / "literature_candidates.csv").shape[0]
    cap = (f"First author, year and journal from {rel(EX / 'fetch_manifest.json')} and Crossref; reference set from "
           f"{rel(EX / 'paper_set.txt')}; curated, extracted and matched entries from "
           f"{rel(EX / 'eval/entry_metrics.csv')} (Gothe 2025 Table 4: {rel(EX / 'eval/gothe_table4_scores.csv')} and "
           f"{rel(EX / 'out/records_normalized.csv')}); SI files from {rel(EX / 'si_manifest.json')}; candidate "
           f"operating points from {rel(INV / 'literature_candidates.csv')}. Lam 2018 has no curated reference and was "
           f"scored by PDF review only. SI column: number of SI files retrieved.")
    hdr = ["First author", "Year", "Journal", "DOI", "Reference set", "Curated entries", "Extracted entries",
           "Matched entries", "SI obtained", "Candidate operating points"]
    return block(1, "The 50 CO₂-to-methanol papers of the extraction set", cap, hdr, rows)


# ---- Supplementary Table 2: ammonia field set ----------------------------------------------------------------
def table2(cr):
    ps = paper_set(NF / "paper_set.txt")
    fm, sm = manifest(NF / "fetch_manifest.json"), manifest(NF / "si_manifest.json")
    cand = pd.read_csv(FIELD / "candidates.csv")
    gm = pd.read_csv(FIELD / "group_metrics.csv")
    prim = cand[cand.group.notna()]
    rows, tot = [], dict(rec=0, prim=0, grp=0, mis=0)
    for doi, tag in ps:
        author, year, journal = bib(doi, fm, cr)
        c, p, g = cand[cand.doi == doi], prim[prim.doi == doi], gm[gm.doi == doi]
        metals = ", ".join(sorted(p.metal.dropna().unique())) or "–"
        hum = "ref. " + tag.split(":")[1] if tag.startswith("humphreys:") else "–"
        nsi = len(sm[doi.lower()]["files"]) if sm[doi.lower()]["status"] == "ok" else 0
        mis = int(g.top1_mismatch.sum())
        tot["rec"] += len(c); tot["prim"] += len(p); tot["grp"] += len(g); tot["mis"] += mis
        rows.append([author, year, journal, doi, hum, f"yes ({nsi})" if nsi else "no", num(len(c)), num(len(p)),
                     metals, num(len(g)), num(mis)])
    s = json.loads((FIELD / "summary.json").read_text(encoding="utf-8"))
    assert (tot["rec"], tot["prim"], tot["grp"], tot["mis"]) == (
        s["records_in"], s["primary_entries_after_dedup"], s["primary"]["groups"], s["primary"]["top1_mismatch_groups"])
    rows.append(["**Total**", "", "", f"**{len(ps)} papers**", "", "", f"**{num(tot['rec'])}**",
                 f"**{num(tot['prim'])}**", "", f"**{tot['grp']}**", f"**{tot['mis']}**"])
    cap = (f"First author and year from {rel(NF / 'fetch_manifest.json')}, journal from Crossref; Humphreys 2021 "
           f"reference number from {rel(NF / 'paper_set.txt')}; SI files from {rel(NF / 'si_manifest.json')}; "
           f"extracted catalyst entries, primary entries (one per catalyst and comparison) and their metals from "
           f"{rel(FIELD / 'candidates.csv')}; comparison groups and groups whose highest-rate catalyst is not the "
           f"lowest-plant-cost catalyst (primary leaderboard: rate per g catalyst, no metal recovery) from "
           f"{rel(FIELD / 'group_metrics.csv')}; totals checked against {rel(FIELD / 'summary.json')}.")
    hdr = ["First author", "Year", "Journal", "DOI", "Humphreys 2021", "SI obtained", "Catalyst entries",
           "Primary entries", "Metals (primary)", "Comparison groups", "Groups with a different winner"]
    return block(2, "The 30 primary ammonia-synthesis papers", cap, hdr, rows)


# ---- Supplementary Table 3: methanol plant benchmark ---------------------------------------------------------
KNOBS = {"cat_term": lambda v: f"catalyst {num(v[0])} €/kg replaced every {num(v[1])} y",
         "loop_dp": lambda v: f"loop ΔP {num(v)} bar", "h2_price": lambda v: f"H₂ {num(v)} €/t",
         "co2_price": lambda v: f"CO₂ {num(v)} €/t", "elec_price": lambda v: f"electricity {num(v)} €/MWh",
         "recycle_mult": lambda v: f"recycle-driven costs ×{num(v)}",
         "ec_ref": lambda v: f"equipment split from Campos 2022 SI ({len(v)} items)"}


def table3():
    rv = pd.read_csv(BENCH / "reference_values.csv")
    rp = pd.read_csv(BENCH / "reconciliation_plant.csv")
    rc = pd.read_csv(BENCH / "reconciliation_cost.csv")
    s = json.loads((BENCH / "summary.json").read_text(encoding="utf-8"))
    out = []

    kinds = ["source_fact", "derived", "secondary", "figure_reading"]
    rows = []
    for rid, g in rv.groupby("ref_id", sort=False):
        k = g.kind.value_counts()
        rows.append([rid, max(g.reference, key=len), g.doi.iloc[0], num(len(g))] + [num(k.get(x, 0)) for x in kinds])
    k = rv.kind.value_counts()
    rows.append(["**Total**", "", "", f"**{num(len(rv))}**"] + [f"**{num(k.get(x, 0))}**" for x in kinds])
    out.append(block("3a", "Sources of the methanol plant benchmark",
                     f"One row per source of {rel(BENCH / 'reference_values.csv')}, which gives every value with its "
                     f"locator (page, table or figure) and the conversion applied. Printed: value printed in the "
                     f"source; derived: arithmetic on printed values; secondary: pilot-plant values tabulated by "
                     f"Dieterich 2020; figure: read off a figure.",
                     ["ID", "Source", "DOI", "Values", "Printed", "Derived", "Secondary", "Figure"], rows))

    cases = [c for c in rp.columns if c not in ("metric", "references")]
    short = [c.split(" ")[0] for c in cases]
    rows, same = [], []
    for _, r in rp.iterrows():
        vals = [str(v) for v in r[cases]]
        if len(set(vals)) == 1 and not re.fullmatch(r"-?[\d.e+-]+", vals[0]):
            same.append(f"{r['metric']}: {vals[0]} in every case")     # one text value for all cases
            continue
        rows.append([r["metric"]] + [num(float(v)) for v in vals])
    legend = "; ".join(f"{a}, {c[len(a):].strip()}" for a, c in zip(short, cases))
    out.append(block("3b", "Plant metrics of the model loop at each reference operating point",
                     f"Model values from {rel(BENCH / 'reconciliation_plant.csv')} (recycled CO, central RWGS rule). "
                     f"Columns: {legend}. " + "".join(x + ". " for x in same) +
                     "Reference values for each metric are in Supplementary Table 3c.",
                     ["Metric"] + short, rows))

    rows = [[r.metric, r.references.replace(" | ", "; ")] for r in rp.itertuples(index=False)]
    out.append(block("3c", "Reference values for the plant metrics of Supplementary Table 3b",
                     f"From the `references` column of {rel(BENCH / 'reconciliation_plant.csv')}; each value is traced "
                     f"to its source locator in {rel(BENCH / 'reference_values.csv')}. An asterisk marks a pilot-plant "
                     f"value tabulated by Dieterich 2020.", ["Metric", "Reference values"], rows))

    rows, last = [], None
    for r in rc.itertuples(index=False):
        dev = "–" if not math.isfinite(r.deviation_pct) else num(r.deviation_pct, 1) + " %"
        rows.append(["" if r.case == last else r.case, r.term, num(r.model), num(r.reference), dev, r.ref_basis,
                     r.attribution])
        last = r.case
    out.append(block("3d", "Cost at each study's own prices, scale and finance",
                     f"From {rel(BENCH / 'reconciliation_cost.csv')} (€/t methanol unless stated). Like-for-like: "
                     f"feed, compression electricity, catalyst replacement and capital annuity at the study's own rate, "
                     f"plus the study's own fixed O&M. Anchor convention: the model's full net production cost. "
                     f"Like-for-like totals: Pérez-Fortes 2016 {num(s['perez_fortes_like_for_like_eur_t'], 1)} €/t, "
                     f"Szima 2018 {num(s['szima_like_for_like_eur_t'], 1)} €/t ({rel(BENCH / 'summary.json')}).",
                     ["Case", "Term", "Model", "Reference", "Deviation", "Reference basis", "Attribution"], rows))

    rows = []
    for c in s["capex_scale"]:
        rows.append([c["reference"], num(c["capacity_t_a"]), num(c["model_FCI_MEUR"], 1),
                     num(c["model_FCI_eur_per_tpa"], 0), num(c["reference_eur_per_tpa"], 0), c["reference_basis"],
                     num(c["ratio_model_FCI_to_reference"], 2)])
    out.append(block("3e", "Specific fixed capital of the model against published plants",
                     f"From `capex_scale` in {rel(BENCH / 'summary.json')}; the model is run at each study's own "
                     f"capacity and cost year.",
                     ["Reference", "Capacity (t/a)", "Model FCI (M€)", "Model FCI (€ per t/a)",
                      "Reference (€ per t/a)", "Reference basis", "Model / reference"], rows))

    rows = []
    for v in s["sensitivity"].values():
        knobs = "; ".join(KNOBS[k](x) for k, x in v["knobs"].items()) or "frozen model"
        rows.append([knobs, v["top1"], num(v["papers"]), v["inversions"],
                     num(100 * v["regret_median_mismatched"], 1) + " %", num(v["groups_flipped"]),
                     num(v["economic_winner_changed"])])
    chk = s["sensitivity_check"]
    out.append(block("3f", "Headline comparison rerun with primary-source plant terms",
                     f"From `sensitivity` in {rel(BENCH / 'summary.json')}: groups whose STY leader is not the "
                     f"plant-cost leader, papers affected, pairwise orderings inverted, median regret of the "
                     f"mismatched groups, groups whose mismatch flag changes and groups whose plant-cost winner "
                     f"changes. The baseline reproduces the frozen headline ({chk['frozen_top1']}, "
                     f"{chk['frozen_inversions']} inversions; maximum relative cost difference "
                     f"{num(chk['max_rel_diff_vs_frozen_costs'])}).",
                     ["Plant terms changed", "Different winner", "Papers", "Inversions",
                      "Median regret", "Flags changed", "Winners changed"], rows))
    return "\n".join(out)


# ---- Supplementary Table 4: bimetallic surface layers --------------------------------------------------------
def table4():
    s = json.loads((ALLOY / "summary.json").read_text(encoding="utf-8"))
    layers = [("Frozen 15-metal prices only", s),
              ("Transition metals (no sp metal, no group 3–5 element)", s["extended_excluding_sp_and_group3to5"]),
              ("+ group 3–5 elements", s["extended_transition_metals_only"]),
              ("+ sp metals (all priced surfaces)", s["extended_with_usgs_prices"])]

    def names(lst):
        return ", ".join(x if isinstance(x, str) else f"{x[0]} {num(x[1], 2)}" for x in lst)

    rows = []
    for name, d in layers:
        assert d["below_Fe"] == len(d["below_Fe_surfaces"]) and d["below_Fe_anchored"] == len(d["below_Fe_anchored_surfaces"])
        assert d["pruning"]["pruned"] + d["pruning"]["full_optimizations_needed"] == d["costed"]
        rows.append([name, num(d["costed"]), num(d["feasible"]), num(d["route_anchored"]["feasible"]),
                     f"{d['below_Fe']}: {names(d['below_Fe_surfaces'])}",
                     f"{d['below_Fe_anchored']}: {names(d['below_Fe_anchored_surfaces'])}",
                     f"{num(d['pruning']['pruned'])} ({pct(d['pruning']['fraction_saved'])})",
                     num(len(d["pruning"]["false_prunes"]))])
    dc = s["domain_counts"]
    cal = s["calibration"]
    cap = (f"From {rel(ALLOY / 'summary.json')}. {num(s['surfaces_fetched'])} surfaces ({num(s['sites_fetched'])} N* "
           f"sites) were fetched; {num(s['not_costed_no_price'])} contain Tc, which has no market price, and are not "
           f"costed; the {num(s['extended_with_usgs_prices']['costed'])} costed surfaces are "
           f"{num(dc['transition_metal'])} transition-metal, {num(dc['contains_group3to5'])} with a group 3–5 element "
           f"and {num(dc['contains_sp_metal'])} with an sp metal. Layers are cumulative. Feasible: inside the 90 m³ bed "
           f"limit. Surfaces below Fe ({num(s['Fe_cost_USD_t'], 2)} USD/t NH₃) are listed in order of cost for the "
           f"global bridge (slope {num(cal['slope'], 3)}, R² {num(cal['r2'], 3)}, RMS {num(cal['rms_eV'], 2)} eV over "
           f"{len(cal['bridge_metals'])} pure metals) and with their cost (USD/t) for the element-anchored bridge. "
           f"Pruned: candidates ruled out by the descriptor-only lower bound before the full 14,136-state "
           f"optimization; false prunes: pruned candidates whose full optimization falls below Fe.")
    hdr = ["Layer", "Costed", "Feasible, global", "Feasible, anchored", "Below Fe, global bridge",
           "Below Fe, element-anchored bridge", "Pruned", "False prunes"]
    return block(4, "Bimetallic surface layers of the ammonia screen", cap, hdr, rows)


# ---- Supplementary Table 5: Fe terrace-to-step bridge ---------------------------------------------------------
def s1_terrace():
    src = (ALLOY / "run_alloy_chain.py").read_text(encoding="utf-8")
    node = next(n for n in ast.parse(src).body
                if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "S1_TERRACE")
    return ast.literal_eval(node.value)


def fit(x, y, x0):
    n = len(x)
    b, a = np.polyfit(x, y, 1)
    res = y - (a + b * x)
    se = math.sqrt((res ** 2).sum() / (n - 2))
    r2 = 1 - (res ** 2).sum() / ((y - y.mean()) ** 2).sum()
    loo = np.array([np.polyval(np.polyfit(np.delete(x, i), np.delete(y, i), 1), x[i]) for i in range(n)])
    err = y - loo
    pred = a + b * x0
    half = stats.t.ppf(0.975, n - 2) * se * math.sqrt(1 + 1 / n + (x0 - x.mean()) ** 2 / ((x - x.mean()) ** 2).sum())
    return dict(n=n, slope=b, intercept=a, r2=r2, se=se, loo=loo, mae=np.abs(err).mean(),
                rmse=math.sqrt((err ** 2).mean()), pred=pred, lo=pred - half, hi=pred + half)


def table5():
    d = pd.read_csv(BRIDGE / "fe_bridge_loo.csv")
    fe = s1_terrace()["Fe"]
    x, y = d.terrace_E_N_eV.to_numpy(), d.step_E_N_observed_eV.to_numpy()
    g = fit(x, y, fe)
    # the CSV keeps 4-decimal energies; its leave-one-out predictions come from the unrounded workbook values
    assert np.allclose(g["loo"], d.LOO_predicted_eV, atol=1e-4)
    err = d.error_obs_minus_pred_eV.to_numpy()
    g.update(mae=np.abs(err).mean(), rmse=math.sqrt((err ** 2).mean()))
    assert abs(g["se"] - 0.2271258177356984) < 1e-9          # the frozen Fe_sigma_eV of NH3-FINAL-1.1
    strong = (x <= -0.5)
    b = fit(x[strong], y[strong], fe)
    rows = [[r.metal, num(r.terrace_E_N_eV, 4), num(r.step_E_N_observed_eV, 4), num(r.LOO_predicted_eV, 4),
             num(r.error_obs_minus_pred_eV, 4)] for r in d.itertuples(index=False)]
    rows.append(["Fe", num(fe, 4), "not in S1", f"{num(g['pred'], 4)} (full fit)", "–"])
    cap = (f"Terrace and observed step-site N formation energies of the 14 metals with both values in Dataset S1, and "
           f"the step value predicted with that metal left out, from {rel(BRIDGE / 'fe_bridge_loo.csv')}; the Fe "
           f"terrace value is the Dataset S1 entry used by {rel(ALLOY / 'run_alloy_chain.py')}. Statistics in "
           f"Supplementary Table 5b are recomputed from these rows.")
    out = [block("5a", "Leave-one-out validation of the Fe terrace-to-step bridge", cap,
                 ["Metal", "Terrace *E*_{N} (eV)", "Step *E*_{N}, observed (eV)", "Step *E*_{N}, leave-one-out (eV)",
                  "Observed − predicted (eV)"], rows)]
    names = ", ".join(d.metal[strong])
    stat = [("Metals in the fit", lambda f: str(f["n"])),
            ("Slope", lambda f: num(f["slope"], 4)), ("Intercept (eV)", lambda f: num(f["intercept"], 4)),
            ("R²", lambda f: num(f["r2"], 4)), ("Residual standard error (eV)", lambda f: num(f["se"], 4)),
            ("Leave-one-out MAE (eV)", lambda f: num(f["mae"], 4)),
            ("Leave-one-out RMSE (eV)", lambda f: num(f["rmse"], 4)),
            (Raw("Fe step *E*_{N}, predicted (eV)"), lambda f: num(f["pred"], 4)),
            ("95 % prediction interval for Fe (eV)", lambda f: f"{num(f['lo'], 3)} to {num(f['hi'], 3)}")]
    rows = [[k, fn(g), fn(b)] for k, fn in stat]
    cap = (f"Ordinary least squares on Supplementary Table 5a. The global 14-metal fit is the relation used for Fe in "
           f"the model; its residual standard error is the Fe descriptor uncertainty of the descriptor Monte Carlo "
           f"analysis. The strong-binding branch (terrace *E*_{{N}} ≤ −0.5 eV: {names}) is a sensitivity check and is "
           f"not used in the model. Prediction interval: Student t with n − 2 degrees of freedom.")
    out.append(block("5b", "Statistics of the Fe terrace-to-step bridge", cap,
                     ["Statistic", "Global fit (14 metals)", "Strong-binding branch"], rows))
    return "\n".join(out)


# ---- Supplementary Table 6: errata of the curated reference data ---------------------------------------------
# Nature of each correction, summarised from the `evidence` column of the errata files (text only; the counts
# are read from the files).
NATURE = {
    "10.1039/c2cy20604h": "pressures in MPa stored as bar; STY set to the yields printed in the text",
    "10.1021/acs.iecr.7b01464": "CO selectivity stored as CO₂ conversion (Table 1)",
    "10.1002/anie.202401168": "conversion and selectivity set to the values printed in the text",
    "10.1002/cphc.202300530": "conversion curves of two catalysts swapped (Fig. 9a)",
    "10.1002/ente.201800747": "STY set to the printed SI Table S1 values",
    "10.1016/j.apcatb.2017.06.069": "STY set to the printed formation rates (Table 2)",
    "10.1016/j.cattod.2020.05.049": "STY recomputed from X × S × F replaced by the printed rates (Table 1)",
    "10.1016/j.cej.2022.135090": "methanol selectivity read on the wrong axis segment (Fig. 2b); STY derived from it",
    "10.1016/j.fuel.2022.125878": "conversion and selectivity set to the values printed in Section 3.3",
    "10.1016/j.fuel.2023.127927": "STY and conversion set to the printed Table 1 values",
    "10.1016/j.jcat.2012.05.020": "STY set to the printed rate (Table 2)",
    "10.1016/j.jcat.2016.03.017": "GHSV off by a factor of ten; STY set to the printed rates (Tables 4–6)",
    "10.1016/j.jcat.2020.01.014": "STY set to the printed value in the text",
    "10.1016/j.jcou.2016.11.015": "STY recomputed from X × S × F replaced by the printed yields (Table 4)",
    "10.1016/j.jes.2023.05.010": "STY set to the printed text and Fig. 6b values",
    "10.1021/acscatal.9b01869": "bulk In₂O₃ row listed as In/ZrO₂; STY set to SI Table S5 values",
    "10.1039/c6ra28305e": "STY set to the printed productivities; H₂/CO₂ ratio set to the printed feed",
    "10.1126/sciadv.1701290": "STY set to the printed SI Table S2 values",
    "10.1039/c4cy00848k": "pressure in bar stored as MPa; rates of one series shifted one temperature step",
    "10.1021/acsami.1c05586": "rows at temperatures not tested dropped; STY on an inconsistent basis not scored",
    "10.1021/acscatal.0c05628": "two STY values assigned to the wrong catalysts",
    "10.1021/acsomega.8b00211": "rate assigned to the Sn-free catalyst instead of the Sn-promoted one",
    "10.1021/jacs.7b08891": "Ru-free supports listed as Ru catalysts (name, active metal, metal content)",
    "10.1002/aenm.201801772": "Ru loading, space velocity and rate set to the printed values",
    "10.1021/acssuschemeng.7b02812": "reduction flow taken as the reaction space velocity",
    "10.1007/s10562-019-02674-1": "space velocity set to the printed WHSV",
    "10.1021/acscatal.7b00284": "space velocity off by a factor of ten",
    "10.1038/s41467-020-14287-z": "Co loading set to the ICP-AES value",
    "10.1021/acs.iecr.8b02126": "volumetric flow printed as a space velocity",
}


def table6(cr, fms):
    ap = pd.read_csv(EX / "eval/errata_applied.csv")
    rules = pd.concat([pd.read_csv(EX / "eval/themecat_errata.csv").assign(ref="themecat"),
                       pd.read_csv(EX / "eval/suvarna_errata.csv").assign(ref="suvarna")])
    hum = pd.read_csv(SUPP / "out/primary_errata.csv")
    hum["refno"] = hum.paper_locator.str.extract(r"ref\. (\d+)")[0].astype(int)
    refs = pd.read_csv(NF / "humphreys_refs.csv", comment="#").dropna().set_index("ref").doi
    hum["doi"] = hum.refno.map(refs)
    assert hum.doi.notna().all()

    def paper(doi):
        for fm in fms:
            if doi.lower() in fm:
                a, y, j = bib(doi, fm, cr)
                return f"{a} {y}, {j}"
        raise KeyError(doi)

    rows, tot = [], {}
    for ref, name in (("themecat", "TheMeCat v1"), ("suvarna", "Suvarna 2022")):
        a = ap[ap.ref == ref]
        for doi in rules[rules.ref == ref].doi.drop_duplicates():
            g = a[a.doi == doi]
            dropped = int((g.field == "(row dropped)").sum())
            cells = len(g) - dropped
            n = f"{cells}" + (f" (+ {dropped} rows dropped)" if dropped else "")
            rows.append([name, paper(doi), doi, num(int((rules.doi == doi).sum())), n, NATURE[doi]])
            tot[name] = tot.get(name, 0) + cells
    for doi, g in hum.groupby("doi", sort=False):
        nrow = len(g[["page", "row"]].drop_duplicates())
        rows.append([f"Humphreys 2021 (ref. {g.refno.iloc[0]}, {nrow} row{'s' * (nrow > 1)})", paper(doi), doi,
                     num(len(g)), num(len(g)), NATURE[doi]])
    tot["Humphreys 2021"] = len(hum)
    nrows = len(hum[["page", "row"]].drop_duplicates())
    cap = (f"One row per paper. TheMeCat and Suvarna: correction rules in {rel(EX / 'eval/themecat_errata.csv')} and "
           f"{rel(EX / 'eval/suvarna_errata.csv')} (page, table or figure locator in the `evidence` column), cells "
           f"changed in {rel(EX / 'eval/errata_applied.csv')}. Humphreys 2021: one row per corrected field in "
           f"{rel(SUPP / 'out/primary_errata.csv')} ({len(hum)} fields in {nrows} rows of the review tables), reference "
           f"number resolved with {rel(NF / 'humphreys_refs.csv')}. "
           f"Cells corrected: " + "; ".join(f"{k} {num(v)}" for k, v in tot.items()) + ".")
    return block(6, "Corrections to the curated reference data found against the papers", cap,
                 ["Reference set", "Paper", "DOI", "Correction rules", "Cells corrected", "Nature of the correction"], rows)


# ---- main ---------------------------------------------------------------------------------------------------
def main():
    refresh = "--refresh" in sys.argv
    fm_ex, fm_nf = manifest(EX / "fetch_manifest.json"), manifest(NF / "fetch_manifest.json")
    dois = [d for d, _ in paper_set(EX / "paper_set.txt")] + [d for d, _ in paper_set(NF / "paper_set.txt")]
    cr = crossref(dois, refresh)
    parts = ["# Supplementary Tables", "",
             "<!-- Generated by tools/build_si_tables.py from the repository files named in each caption; do not edit "
             "by hand. -->", "",
             table1(cr), table2(cr), table3(), table4(), table5(), table6(cr, (fm_ex, fm_nf))]
    OUT.write_text("\n".join(parts), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")
    for n in dict.fromkeys(NOTES):
        print("  note:", n)


if __name__ == "__main__":
    main()
