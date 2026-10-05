"""Generalized methanol recycle-economics model applied to the 21 Re/TiO2 entries of Gothe et al. 2025, Table 4.

Inputs: table4_gothe2025.csv (this folder; transcribed from Gothe et al., ACS Catal. 15, 19111 (2025), Table 4:
Re wt%, prereduction T, reaction T, P, CO2:H2, STY per g Re, S_MeOH/S_CO/S_CH4 in %, X_CO2 in %, GHSV).
Selectivity closure follows the workbook convention: '<1' -> 0; S_MeOH and S_CH4 as reported; CO(-like) = 1 -
S_MeOH - S_CH4. Each entry is evaluated at its own P (plant loop pressure) and reactor-inlet H2/CO2, with catalyst
mass from STY per g Re and the Re loading.

For every entry and each CO treatment (inert; recycled, central rule; plus the recycled range high / equal-X):
net production cost at the canonical 2 % purge and at the entry's own cost-optimal purge (0.5-40 %, 0.1 % grid).
Upstream rankings: STY per g Re, STY per g catalyst, single-pass yield X * S_MeOH. Rank agreement: Spearman,
Kendall tau-b, pairwise inversions, normalized decision regret = (C[upstream winner] - C[economic winner]) /
C[economic winner]. Computed for all 21 entries and for the 14 entries at the canonical operating point
(100 bar, CO2:H2 = 1:4).

Outputs (this folder): table4_inputs_closed.csv, table4_candidate_results.csv, table4_rank_metrics.csv,
table4_summary.json.
"""
import csv
import json
import sys
from itertools import combinations
from pathlib import Path

import numpy as np
from scipy.stats import kendalltau, rankdata, spearmanr

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "data" / "meoh"))
import meoh_general_model as G  # noqa: E402

TREATMENTS = ["inert", "recycled_central", "recycled_high", "recycled_equal_X"]
PRIMARY = ["inert", "recycled_central"]
LABEL = {"inert": "inert CO", "recycled_central": "recycled CO (central)", "recycled_high": "recycled CO (high)",
         "recycled_equal_X": "recycled CO (equal-X)"}
CANONICAL = {(1, 500, 200, 100, 4, 10): "1 wt% Re | 200 C", (1, 500, 250, 100, 4, 10): "1 wt% Re | 250 C",
             (5, 500, 200, 100, 4, 10): "5 wt% Re | 200 C", (5, 500, 250, 100, 4, 10): "5 wt% Re | 250 C"}

# ---------------------------------------------------------------- inputs ---------------------------------------
cands = []
for i, r in enumerate(csv.DictReader(open(HERE / "table4_gothe2025.csv", encoding="utf-8"))):
    co2, h2 = (float(v) for v in r["CO2_H2"].split(":"))
    ratio = h2 / co2
    smeoh_r, sco_r, sch4_r = (G.parse_pct(r[k]) for k in ("S_MeOH_pct", "S_CO_pct", "S_CH4_pct"))
    smeoh, sco, sch4 = G.close_selectivity(smeoh_r, sco_r, sch4_r)
    wt, tred, trx, P, ghsv = (float(r[k]) for k in ("Re_wt", "T_prered_C", "T_rxn_C", "P_bar", "GHSV_1e3_mL_gcat_h"))
    flags = []
    if P != 100:
        flags.append("P %g bar" % P)
    if ratio != 4:
        flags.append("CO2:H2 %s" % r["CO2_H2"])
    if ghsv != 10:
        flags.append("GHSV %gk" % ghsv)
    if tred != 500:
        flags.append("prereduction %g C" % tred)
    key = (int(wt), int(tred), int(trx), int(P), int(ratio), int(ghsv))
    cands.append(dict(
        id="T4-%02d" % (i + 1),
        label="%g wt%% Re | red %g C | %g C | %g bar | %s | GHSV %gk" % (wt, tred, trx, P, r["CO2_H2"], ghsv),
        metal_wt=wt, T_prered_C=tred, T_C=trx, P_bar=P, h2_co2=ratio, CO2_H2=r["CO2_H2"], GHSV_k=ghsv,
        STY_per_g_metal=float(r["STY_gMeOH_gRe_h"]), X=float(r["X_CO2_pct"]) / 100.0,
        SMeOH=smeoh, SCO=sco, SCH4=sch4,
        S_reported="%s/%s/%s" % (r["S_MeOH_pct"], r["S_CO_pct"], r["S_CH4_pct"]),
        canonical_state=CANONICAL.get(key, ""),
        same_operating_point=(P == 100 and ratio == 4),
        flags="; ".join(flags) if flags else ""))
for c in cands:
    c["STY_per_g_cat"] = c["STY_per_g_metal"] * c["metal_wt"] / 100.0
    c["yield_XS"] = c["X"] * c["SMeOH"]

with open(HERE / "table4_inputs_closed.csv", "w", newline="", encoding="utf-8") as f:
    keys = ["id", "label", "metal_wt", "T_prered_C", "T_C", "P_bar", "CO2_H2", "h2_co2", "GHSV_k",
            "STY_per_g_metal", "STY_per_g_cat", "X", "S_reported", "SMeOH", "SCO", "SCH4", "yield_XS",
            "canonical_state", "same_operating_point", "flags"]
    w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
    w.writeheader()
    w.writerows(cands)

# ---------------------------------------------------------------- economics ------------------------------------
model_args = dict.fromkeys(["X", "SMeOH", "SCH4", "SCO", "STY_per_g_metal", "metal_wt", "P_bar", "h2_co2", "T_C"])
res = {}
for c in cands:
    cc = {k: c[k] for k in model_args}
    for t in TREATMENTS:
        e = G.cost(cc, x_co=t)
        s = G.purge_sweep(cc, x_co=t)
        k = int(np.argmin(s["cost_eur_t"]))
        res[(c["id"], t)] = dict(
            npc=float(e["cost_eur_t"]), opt=float(s["cost_eur_t"][k]), opt_purge=float(G.PURGES[k]),
            x_co=float(e["x_co"]), x_co_opt=float(s["x_co"][k]), recycle=float(e["recycle_kmol_h"]),
            co_in=float(e["co_inlet_fraction"]), nonh2co2=float(e["nonreactive_fraction"]),
            rwgs=float(e["rwgs_approach"]), h2=float(e["h2_eur_t"]), elec=float(e["elec_eur_t"]),
            EC=float(e["EC_MEUR"]), cat_t=float(e["catalyst_t"]), carbon_eff=float(e["carbon_efficiency"]))
    print("%s %-55s inert %8.2f / %8.2f@%.3f   central %8.2f / %8.2f@%.3f  x %.4f  RWGS(inert) %.2f" % (
        c["id"], c["label"], res[(c["id"], "inert")]["npc"], res[(c["id"], "inert")]["opt"],
        res[(c["id"], "inert")]["opt_purge"], res[(c["id"], "recycled_central")]["npc"],
        res[(c["id"], "recycled_central")]["opt"], res[(c["id"], "recycled_central")]["opt_purge"],
        res[(c["id"], "recycled_central")]["x_co"], res[(c["id"], "inert")]["rwgs"]))

# the four canonical states must reproduce the canonical ranking file under the inert treatment
canon_csv = {r["candidate"]: float(r["NPC_EUR_t_2pct_purge"])
             for r in csv.DictReader(open(REPO / "data/meoh/meoh_candidate_ranking_D01v3.csv", encoding="utf-8"))}
for c in cands:
    if c["canonical_state"]:
        assert round(res[(c["id"], "inert")]["npc"], 2) == canon_csv[c["canonical_state"]], c["id"]

UPSTREAM = {"STY per g Re": "STY_per_g_metal", "STY per g catalyst": "STY_per_g_cat",
            "single-pass yield X*S_MeOH": "yield_XS"}


def ranks_desc(vals):
    return rankdata([-v for v in vals], method="min")


def rank_metrics(subset, metric_key, cost):
    ids = [c["id"] for c in subset]
    up_val = {c["id"]: c[metric_key] for c in subset}
    upr = dict(zip(ids, ranks_desc([up_val[i] for i in ids])))
    ecr = dict(zip(ids, rankdata([cost[i] for i in ids], method="min")))
    a, b = [up_val[i] for i in ids], [-cost[i] for i in ids]  # both "higher is better"
    inv = sum(1 for x, y in combinations(ids, 2) if (up_val[x] - up_val[y]) * (cost[y] - cost[x]) < 0)
    ties = sum(1 for x, y in combinations(ids, 2) if up_val[x] == up_val[y])
    upw = max(ids, key=lambda i: up_val[i])
    ecw = min(ids, key=lambda i: cost[i])
    return dict(n=len(ids), spearman=float(spearmanr(a, b).statistic), kendall_tau_b=float(kendalltau(a, b).statistic),
                pairwise_inversions=inv, pairs=len(ids) * (len(ids) - 1) // 2, upstream_tied_pairs=ties,
                upstream_winner=upw, economic_winner=ecw, upstream_winner_econ_rank=int(ecr[upw]),
                economic_winner_upstream_rank=int(upr[ecw]),
                cost_upstream_winner=cost[upw], cost_economic_winner=cost[ecw],
                normalized_regret=(cost[upw] - cost[ecw]) / cost[ecw])


sets = {"all 21 entries": cands, "14 entries at 100 bar, CO2:H2 1:4": [c for c in cands if c["same_operating_point"]]}
metrics_rows = []
for sname, subset in sets.items():
    for t in TREATMENTS:
        for basis, bkey in (("2 % purge", "npc"), ("own optimum purge", "opt")):
            cost = {c["id"]: res[(c["id"], t)][bkey] for c in subset}
            for mname, mkey in UPSTREAM.items():
                m = rank_metrics(subset, mkey, cost)
                metrics_rows.append(dict(set=sname, co_treatment=LABEL[t], purge_basis=basis, upstream_metric=mname, **m))
with open(HERE / "table4_rank_metrics.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(metrics_rows[0]))
    w.writeheader()
    w.writerows(metrics_rows)

# per-candidate table
rows = []
for sname_key in ("all",):
    for c in cands:
        row = {k: c[k] for k in ("id", "label", "canonical_state", "flags", "metal_wt", "T_C", "P_bar", "CO2_H2",
                                 "GHSV_k", "STY_per_g_metal", "STY_per_g_cat", "X", "SMeOH", "SCO", "SCH4",
                                 "yield_XS")}
        for mname, mkey in UPSTREAM.items():
            vals = [x[mkey] for x in cands]
            row["rank_" + mkey] = int(ranks_desc(vals)[cands.index(c)])
        for t in TREATMENTS:
            r_ = res[(c["id"], t)]
            pre = {"inert": "inert", "recycled_central": "rec", "recycled_high": "rec_high",
                   "recycled_equal_X": "rec_eqX"}[t]
            row["%s_x_CO" % pre] = r_["x_co"]
            row["%s_NPC_2pct" % pre] = r_["npc"]
            row["%s_NPC_opt" % pre] = r_["opt"]
            row["%s_opt_purge" % pre] = r_["opt_purge"]
            if t in PRIMARY:
                row["%s_recycle_kmol_h" % pre] = r_["recycle"]
                row["%s_reactor_in_CO_pct" % pre] = 100 * r_["co_in"]
                row["%s_nonH2CO2_fraction" % pre] = r_["nonh2co2"]
                row["%s_RWGS_Q_over_K" % pre] = r_["rwgs"]
        for t in PRIMARY:
            pre = "inert" if t == "inert" else "rec"
            for basis, bkey in (("2pct", "npc"), ("opt", "opt")):
                vals = [res[(x["id"], t)][bkey] for x in cands]
                row["%s_econ_rank_%s" % (pre, basis)] = int(rankdata(vals, method="min")[cands.index(c)])
        rows.append(row)
with open(HERE / "table4_candidate_results.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)

# ---------------------------------------------------------------- summary --------------------------------------
lab = {c["id"]: c["label"] for c in cands}


def pick(sname, t, basis, metric):
    for m in metrics_rows:
        if (m["set"], m["co_treatment"], m["purge_basis"], m["upstream_metric"]) == (sname, LABEL[t], basis, metric):
            return m


headline = {}
for sname in sets:
    for t in TREATMENTS:
        for basis in ("2 % purge", "own optimum purge"):
            key = "%s | %s | %s" % (sname, LABEL[t], basis)
            ms = {mn: pick(sname, t, basis, mn) for mn in UPSTREAM}
            any_m = next(iter(ms.values()))
            headline[key] = dict(
                economic_winner=any_m["economic_winner"] + " (" + lab[any_m["economic_winner"]] + ")",
                economic_winner_cost=any_m["cost_economic_winner"],
                per_metric={mn: dict(upstream_winner=m["upstream_winner"] + " (" + lab[m["upstream_winner"]] + ")",
                                     upstream_winner_cost=m["cost_upstream_winner"],
                                     upstream_winner_econ_rank=m["upstream_winner_econ_rank"],
                                     spearman=round(m["spearman"], 4), kendall_tau_b=round(m["kendall_tau_b"], 4),
                                     pairwise_inversions="%d/%d" % (m["pairwise_inversions"], m["pairs"]),
                                     normalized_regret_pct=round(100 * m["normalized_regret"], 4))
                            for mn, m in ms.items()})
co_effect = {c["id"]: dict(label=c["label"], S_CO=c["SCO"],
                           delta_central_2pct=res[(c["id"], "recycled_central")]["npc"] - res[(c["id"], "inert")]["npc"],
                           delta_high_2pct=res[(c["id"], "recycled_high")]["npc"] - res[(c["id"], "inert")]["npc"])
             for c in cands}
summary = dict(
    source="Gothe et al., ACS Catal. 15, 19111 (2025), Table 4 (21 Re/TiO2 entries)",
    closure="'<1' -> 0; S_MeOH, S_CH4 as reported; CO(-like) = 1 - S_MeOH - S_CH4",
    model="data/meoh/meoh_general_model.py (canonical cost parameters; P and H2/CO2 per entry; STY per g Re basis)",
    purge_grid="0.005-0.400 step 0.001 (396 levels)",
    headline=headline,
    co_recycle_effect_EUR_t=co_effect,
    max_abs_co_effect_central_2pct=max(abs(v["delta_central_2pct"]) for v in co_effect.values()),
    max_abs_co_effect_high_2pct=max(abs(v["delta_high_2pct"]) for v in co_effect.values()),
)
(HERE / "table4_summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")

for key, h in headline.items():
    if "equal-X" in key:
        continue
    print("\n" + key + ": economic winner " + h["economic_winner"] + " %.2f EUR/t" % h["economic_winner_cost"])
    for mn, m in h["per_metric"].items():
        print("   %-28s winner %s  econ rank #%d  rho %.3f tau %.3f inv %s regret %.3f%%" % (
            mn, m["upstream_winner"].split(" ")[0], m["upstream_winner_econ_rank"], m["spearman"],
            m["kendall_tau_b"], m["pairwise_inversions"], m["normalized_regret_pct"]))
