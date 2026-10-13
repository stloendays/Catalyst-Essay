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
           f"operating points of the printed-value primary from {rel(INV / 'literature_candidates.csv')}. Lam 2018 has no curated reference and was "
           f"scored by PDF review only. SI column: number of SI files retrieved.")
    hdr = ["First author", "Year", "Journal", "DOI", "Reference set", "Curated entries", "Extracted entries",
           "Matched entries", "SI obtained", "Candidate operating points (printed values)"]
    return block(1, "The 50 CO₂-to-methanol papers of the extraction set", cap, hdr, rows)


# ---- Supplementary Table 2: ammonia field set ----------------------------------------------------------------
def table2(cr):
    ps = paper_set(NF / "paper_set.txt")
    fm, sm = manifest(NF / "fetch_manifest.json"), manifest(NF / "si_manifest.json")
    cand = pd.read_csv(FIELD / "candidates.csv")
    gm = pd.read_csv(FIELD / "group_metrics_printed.csv")          # frozen primary: printed values only
    prim = pd.read_csv(FIELD / "candidates_printed.csv")
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
    sp = json.loads((FIELD / "summary_printed.json").read_text(encoding="utf-8"))
    assert (tot["rec"], tot["prim"], tot["grp"], tot["mis"]) == (
        s["records_in"], sp["entries"]["printed"], sp["primary"]["groups"], sp["primary"]["top1_mismatch_groups"])
    rows.append(["**Total**", "", "", f"**{len(ps)} papers**", "", "", f"**{num(tot['rec'])}**",
                 f"**{num(tot['prim'])}**", "", f"**{tot['grp']}**", f"**{tot['mis']}**"])
    cap = (f"First author and year from {rel(NF / 'fetch_manifest.json')}, journal from Crossref; Humphreys 2021 "
           f"reference number from {rel(NF / 'paper_set.txt')}; SI files from {rel(NF / 'si_manifest.json')}; "
           f"extracted catalyst entries from {rel(FIELD / 'candidates.csv')}; printed-value primary entries (one per "
           f"catalyst and comparison) and their metals from {rel(FIELD / 'candidates_printed.csv')}; comparison groups "
           f"and groups whose highest-rate catalyst is not the lowest-plant-cost catalyst (primary leaderboard: rate "
           f"per g catalyst, no metal recovery) from {rel(FIELD / 'group_metrics_printed.csv')}; totals checked "
           f"against {rel(FIELD / 'summary.json')} and {rel(FIELD / 'summary_printed.json')}.")
    hdr = ["First author", "Year", "Journal", "DOI", "Humphreys 2021", "SI obtained", "Catalyst entries",
           "Printed-value entries", "Metals (printed)", "Comparison groups", "Groups with a different winner"]
    return block(2, "The 30 primary ammonia-synthesis papers", cap, hdr, rows)


# ---- Supplementary Table 5: methanol plant benchmark ---------------------------------------------------------
KNOBS = {"cat_term": lambda v: f"catalyst {num(v[0])} €/kg replaced every {num(v[1])} y",
         "loop_dp": lambda v: f"loop ΔP {num(v)} bar", "h2_price": lambda v: f"H₂ {num(v)} €/t",
         "co2_price": lambda v: f"CO₂ {num(v)} €/t", "elec_price": lambda v: f"electricity {num(v)} €/MWh",
         "recycle_mult": lambda v: f"recycle-driven costs ×{num(v)}",
         "capex_mult": lambda v: f"capital ×{num(v)}",
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
    out.append(block("5a", "Sources of the methanol plant benchmark",
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
    out.append(block("5b", "Plant metrics of the model loop at each reference operating point",
                     f"Model values from {rel(BENCH / 'reconciliation_plant.csv')} (recycled CO, central RWGS rule). "
                     f"Columns: {legend}. " + "".join(x + ". " for x in same) +
                     "Reference values for each metric are in Supplementary Table 5c.",
                     ["Metric"] + short, rows))

    rows = [[r.metric, r.references.replace(" | ", "; ")] for r in rp.itertuples(index=False)]
    out.append(block("5c", "Reference values for the plant metrics of Supplementary Table 5b",
                     f"From the `references` column of {rel(BENCH / 'reconciliation_plant.csv')}; each value is traced "
                     f"to its source locator in {rel(BENCH / 'reference_values.csv')}. An asterisk marks a pilot-plant "
                     f"value tabulated by Dieterich 2020.", ["Metric", "Reference values"], rows))

    rows, last = [], None
    for r in rc.itertuples(index=False):
        dev = "–" if not math.isfinite(r.deviation_pct) else num(r.deviation_pct, 1) + " %"
        rows.append(["" if r.case == last else r.case, r.term, num(r.model), num(r.reference), dev, r.ref_basis,
                     r.attribution])
        last = r.case
    out.append(block("5d", "Cost at each study's own prices, scale and finance",
                     f"From {rel(BENCH / 'reconciliation_cost.csv')} (€/t methanol unless stated). Like-for-like: "
                     f"feed, compression electricity, catalyst replacement and capital annuity at the study's own rate, "
                     f"plus the study's own fixed O&M; for Pérez-Fortes 2016 the reference is its NPV = 0 break-even "
                     f"methanol price (production cost plus capital recovery), not a production cost. Anchor "
                     f"convention: the model's full net production cost. "
                     f"Like-for-like totals: Pérez-Fortes 2016 {num(s['perez_fortes_like_for_like_eur_t'], 1)} €/t, "
                     f"Szima 2018 {num(s['szima_like_for_like_eur_t'], 1)} €/t ({rel(BENCH / 'summary.json')}).",
                     ["Case", "Term", "Model", "Reference", "Deviation", "Reference basis", "Attribution"], rows))

    rows = []
    for c in s["capex_scale"]:
        rows.append([c["reference"], num(c["capacity_t_a"]), num(c["model_FCI_MEUR"], 1),
                     num(c["model_FCI_eur_per_tpa"], 0), num(c["reference_eur_per_tpa"], 0), c["reference_basis"],
                     num(c["ratio_model_FCI_to_reference"], 2)])
    out.append(block("5e", "Specific fixed capital of the model against published plants",
                     f"From `capex_scale` in {rel(BENCH / 'summary.json')}; the model is run at each study's own "
                     f"capacity and cost year.",
                     ["Reference", "Capacity (t/a)", "Model FCI (M€)", "Model FCI (€ per t/a)",
                      "Reference (€ per t/a)", "Reference basis", "Model / reference"], rows))

    rows = []
    sens = json.loads((BENCH / "sensitivity_summary.json").read_text(encoding="utf-8"))
    for v in sens["variants"].values():
        knobs = "; ".join(KNOBS[k](x) for k, x in v["knobs"].items()) or "frozen model"
        rows.append([knobs, f"{v['top1_mismatch_groups']}/{v['groups']}", num(v["papers_with_mismatch"]),
                     v["pairwise_inversions"], num(100 * v["regret_median_mismatched"], 1) + " %",
                     num(v["groups_flipped_vs_baseline"]), num(v["groups_economic_winner_changed"])])
    chk = sens["check"]
    out.append(block("5f", "Headline comparison rerun with primary-source plant terms",
                     f"From {rel(BENCH / 'sensitivity_summary.json')}: groups whose STY leader is not the "
                     f"plant-cost leader, papers affected, pairwise orderings inverted, median regret of the "
                     f"mismatched groups, groups whose mismatch flag changes and groups whose plant-cost winner "
                     f"changes. The baseline reproduces the frozen headline ({chk['frozen_top1']}, "
                     f"{chk['frozen_inversions']} inversions; maximum relative cost difference "
                     f"{num(chk['max_rel_diff_vs_frozen_costs'])}).",
                     ["Plant terms changed", "Different winner", "Papers", "Inversions",
                      "Median regret", "Flags changed", "Winners changed"], rows))
    return "\n".join(out)


# ---- Supplementary Table 3: bimetallic surface layers --------------------------------------------------------
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
    return block(3, "Bimetallic surface layers of the ammonia screen", cap, hdr, rows)


# ---- Supplementary Table 4: Fe terrace-to-step bridge ---------------------------------------------------------
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
           f"Supplementary Table 4b are recomputed from these rows.")
    out = [block("4a", "Leave-one-out validation of the Fe terrace-to-step bridge", cap,
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
    cap = (f"Ordinary least squares on Supplementary Table 4a. The global 14-metal fit is the relation used for Fe in "
           f"the model; its residual standard error is the Fe descriptor uncertainty of the descriptor Monte Carlo "
           f"analysis. The strong-binding branch (terrace *E*_{{N}} ≤ −0.5 eV: {names}) is a sensitivity check and is "
           f"not used in the model. Prediction interval: Student t with n − 2 degrees of freedom.")
    out.append(block("4b", "Statistics of the Fe terrace-to-step bridge", cap,
                     ["Statistic", "Global fit (14 metals)", "Strong-binding branch"], rows))
    return "\n".join(out)


# ---- Supplementary Table 6: the 83 -> 40 methanol comparison groups ------------------------------------------
# One row per comparison group of the all-entries cohort (plot readings included), from the ledger of
# analysis/meoh_inlet_definition_2026_10_12/run_group_ledger.py; the printed-value verdicts of the 40 kept groups come
# from the frozen group metrics of the primary analysis (inert-limited loop S6 and unlimited loop S5).
LEDGER = ROOT / "analysis/meoh_inlet_definition_2026_10_12"
LEDGER_STATUS = {"paper without printed values": "dropped: no printed values in the paper",
                 "fewer than 2 printed entries": "dropped: fewer than two printed entries"}


def _verdict(differs, regret):
    if differs is None or (isinstance(differs, float) and math.isnan(differs)):
        return "–"
    return f"yes ({pct(float(regret))})" if bool(differs) else "no"


def table_ledger(cr, fm):
    led = pd.read_csv(LEDGER / "group_ledger.csv")
    s = json.loads((LEDGER / "ledger_summary.json").read_text(encoding="utf-8"))
    g5 = pd.read_csv(INV / "group_metrics.csv").set_index("group")
    g6 = pd.read_csv(INV / "group_metrics_inlet_limit.csv").set_index("group")
    kept = led[led.scored_in_printed_primary.astype(bool)]
    assert led.group.is_unique and set(kept.group) == set(g5.index) == set(g6.index)
    assert led.reason_not_scored.fillna("kept").isin(["kept", *LEDGER_STATUS]).all()
    assert (kept.printed_S5_different_leader.astype(bool) == g5.loc[kept.group, "top1_mismatch"].values).all()
    rows, tot = [], dict(p6=0, p5=0, a6=0, a6n=0, a5=0)
    for r in led.itertuples(index=False):
        author, year, _ = bib(r.doi, fm, cr)
        status = "kept" if r.scored_in_printed_primary else LEDGER_STATUS[r.reason_not_scored]
        cond = r.group.split(" | ", 1)[1].replace(" | ", ", ").replace("H2/CO2", "H₂/CO₂")
        if r.scored_in_printed_primary:
            p6 = _verdict(g6.at[r.group, "top1_mismatch"], g6.at[r.group, "regret"])
            p5 = _verdict(g5.at[r.group, "top1_mismatch"], g5.at[r.group, "regret"])
            tot["p6"] += bool(g6.at[r.group, "top1_mismatch"]); tot["p5"] += bool(g5.at[r.group, "top1_mismatch"])
        else:
            p6 = p5 = "–"
        a6 = _verdict(r.all_entries_S6_different_leader, r.all_entries_S6_regret)
        a5 = _verdict(r.all_entries_S5_different_leader, r.all_entries_S5_regret)
        tot["a6"] += a6.startswith("yes"); tot["a6n"] += a6 != "–"; tot["a5"] += a5.startswith("yes")
        rows.append([f"{author} {year}", r.doi, cond, f"{num(r.entries)} / {num(r.printed_entries)}", status,
                     p6, p5, a6, a5])
    order = sorted(range(len(rows)), key=lambda i: (rows[i][0].lower(), rows[i][1], led.P_bar.iloc[i],
                                                    led.h2_co2.iloc[i], rows[i][2]))
    rows = [rows[i] for i in order]
    ae, pp, gr = s["all_entries"], s["printed_primary"], s["groups_dropped_by_reason"]
    res, split = s["all_entries_result"], s["all_entries_result_split"]
    assert (len(led), led.doi.nunique(), int(led.entries.sum())) == (ae["groups"], ae["papers"], ae["entries"])
    assert (len(kept), kept.doi.nunique(), int(kept.printed_entries.sum())) == (pp["groups"], pp["papers"], pp["entries"])
    assert all(int((led.reason_not_scored == k).sum()) == gr[k] for k in LEDGER_STATUS) and gr["other"] == 0
    assert (tot["a5"], len(led)) == (res["S5"]["different_leader"], res["S5"]["groups"])
    assert (tot["a6"], tot["a6n"]) == (res["S6_6_86pct"]["different_leader"], res["S6_6_86pct"]["groups"])
    assert tot["p5"] == split["S5"]["printed_primary"]["different_leader"]
    assert tot["p6"] == int(g6.top1_mismatch.sum()) and tot["p5"] == int(g5.top1_mismatch.sum())
    rows.append(["**Total**", f"**{ae['papers']} papers**", f"**{ae['groups']} groups**",
                 f"**{num(ae['entries'])} / {num(int(led.printed_entries.sum()))}**",
                 f"**{len(kept)} kept; {gr['paper without printed values']} + {gr['fewer than 2 printed entries']} "
                 f"dropped**", f"**{tot['p6']} of {len(kept)}**", f"**{tot['p5']} of {len(kept)}**",
                 f"**{tot['a6']} of {tot['a6n']}**", f"**{tot['a5']} of {len(led)}**"])
    pr = s["papers_dropped_by_reason"]
    cap = (f"One row per comparison group of the all-entries cohort (entries of one paper at the same pressure, H₂/CO₂ "
           f"ratio and space velocity, plot readings included), from {rel(LEDGER / 'group_ledger.csv')}; counts checked "
           f"against {rel(LEDGER / 'ledger_summary.json')}. Entries: all entries of the group / entries with printed "
           f"conversion and selectivities. The same grouping rule applied to printed values alone keeps "
           f"{pp['groups']} groups ({num(pp['entries'])} entries, {pp['papers']} papers); "
           f"{gr['paper without printed values']} groups come from {pr['paper without printed values']} papers without "
           f"printed values and {gr['fewer than 2 printed entries']} have fewer than two printed entries "
           f"({s['groups_dropped_by_printed_entries']['0']} with none, {s['groups_dropped_by_printed_entries']['1']} with "
           f"one). Verdict columns: whether the space-time-yield leader of the group is not its plant-cost leader, with "
           f"the regret where it is not; inlet limit, CO, methane and N₂ at most 6.86% of the reactor inlet (primary); "
           f"no limit, the loop without it. Printed values: the primary analysis, from "
           f"{rel(INV / 'group_metrics_inlet_limit.csv')} and {rel(INV / 'group_metrics.csv')}. All entries: the "
           f"sensitivity with plot readings, from the ledger; under the inlet limit one group keeps fewer than two "
           f"entries that can meet the limit (–).")
    hdr = ["Paper", "DOI", "Comparison group", "Entries (all / printed)", "Status",
           "Printed values, inlet limit", "Printed values, no limit", "All entries, inlet limit", "All entries, no limit"]
    return block(6, f"The {ae['groups']} methanol comparison groups and the {pp['groups']} of the primary analysis",
                 cap, hdr, rows)


# ---- Supplementary Table 7: errata of the curated reference data ---------------------------------------------
# Read from the final adjudication (analysis/verify_2026_10_08/errata_adjudication.py): one root cause = one
# mechanism in one source paper; STY values a dataset derives from a confirmed input error count with that root.
ADJ = ROOT / "analysis/verify_2026_10_08/errata_adjudication.csv"
SET_NAME = {"TheMeCat": "TheMeCat v1", "Suvarna 2022": "Suvarna 2022", "Humphreys 2021 review": "Humphreys 2021"}


def table7(cr, fms):
    r = pd.read_csv(ADJ)
    r["paper_doi"] = r.source_doi.fillna(r.doi)
    hum_ref = r.evidence.str.extract(r"^(ref\. \d+)")[0]

    def paper(doi):
        for fm in fms:
            if doi.lower() in fm:
                a, y, j = bib(doi, fm, cr)
                return f"{a} {y}, {j}"
        raise KeyError(doi)

    counted = r[r.final_class.isin(["ERR", "DER"])]
    rows = []
    for (ds, doi), g in counted.groupby(["dataset", "paper_doi"], sort=False):
        err, der = g[g.final_class == "ERR"], g[g.final_class == "DER"]
        cells = int(err[err.unit_of_count == "value cells"].cells.sum())
        recs = int(err[err.unit_of_count == "records"].cells.sum())
        name = SET_NAME[ds] + (f" ({hum_ref[g.index[0]]})" if ds.startswith("Humphreys") else "")
        rows.append([name, paper(doi), doi, num(g.root_id.nunique()), num(len(err)),
                     f"{cells}" + (f" (+ {recs} rows)" if recs else ""), num(int(der.cells.sum())) if len(der) else "–",
                     "; ".join(dict.fromkeys(g.drop_duplicates("root_id").root_cause_en)) + "."])
    rows.sort(key=lambda x: (x[0].split(" (")[0], x[1]))
    e = counted[counted.final_class == "ERR"]
    tot = (f"{counted.root_id.nunique()} root causes, {len(e)} error rules, "
           f"{int(e[e.unit_of_count == 'value cells'].cells.sum())} value cells and "
           f"{int(e[e.unit_of_count == 'records'].cells.sum())} rows; "
           f"{int(counted[counted.final_class == 'DER'].cells.sum())} further STY cells derived from them")
    cap = (f"One row per source paper with a confirmed error. A root cause is one mechanism in one source paper; "
           f"error rules group the cells of one paper, field and cause; rows are records of conditions the paper did not "
           f"test. TheMeCat stores STY as yield × GHSV × CO₂ fraction × 32.04/24.05 rather than the printed value, so a "
           f"derived STY is counted only with the input error it inherits (last column). Per-cell old value, printed "
           f"value, dataset row and locator: {rel(ROOT / 'analysis/verify_2026_10_08/errata_cells_audit.csv')}; rules "
           f"and classes: {rel(ADJ)}. Total: {tot}.")
    out = [block("7a", "Errors in the curated reference data confirmed against the papers", cap,
                 ["Reference set", "Paper", "DOI", "Root causes", "Error rules", "Cells", "Derived STY cells",
                  "Nature of the error"], rows)]

    rest = r[r.final_class.isin(["CONV", "MINOR"])]
    rows = []
    for (ds, doi), g in rest.groupby(["dataset", "paper_doi"], sort=False):
        conv, minor = g[g.final_class == "CONV"], g[g.final_class == "MINOR"]
        rows.append([SET_NAME[ds], paper(doi), doi, num(int(conv.cells.sum())) if len(conv) else "–",
                     num(int(minor.cells.sum())) if len(minor) else "–"])
    rows.sort(key=lambda x: (x[0], x[1]))
    cap = (f"Differences between curated and printed values that are not errors of the curated data. Definition: the "
           f"paper's printed STY differs from the STY that TheMeCat derives from yield and GHSV, or the paper prints STY "
           f"on bases it does not reconcile (10.1021/acsami.1c05586). Minor: at most 2 % and at most one unit "
           f"of the last printed digit. Total: definition {int(rest[rest.final_class == 'CONV'].cells.sum())} cells, "
           f"minor {int(rest[rest.final_class == 'MINOR'].cells.sum())} cells. The printed values are used for scoring "
           f"in both cases.")
    out.append(block("7b", "Differences of definition and minor differences, not counted as errors", cap,
                     ["Reference set", "Paper", "DOI", "Definition (cells)", "Minor (cells)"], rows))
    return "\n".join(out)


# ---- main ---------------------------------------------------------------------------------------------------
def main():
    refresh = "--refresh" in sys.argv
    fm_ex, fm_nf = manifest(EX / "fetch_manifest.json"), manifest(NF / "fetch_manifest.json")
    dois = [d for d, _ in paper_set(EX / "paper_set.txt")] + [d for d, _ in paper_set(NF / "paper_set.txt")]
    cr = crossref(dois, refresh)
    parts = ["# Supplementary Tables", "",
             "<!-- Generated by tools/build_si_tables.py from the repository files named in each caption; do not edit "
             "by hand. -->", "",
             table1(cr), table2(cr), table4(), table5(), table3(), table_ledger(cr, fm_ex),
             table7(cr, (fm_ex, fm_nf))]
    OUT.write_text("\n".join(parts), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")
    for n in dict.fromkeys(NOTES):
        print("  note:", n)


if __name__ == "__main__":
    main()
