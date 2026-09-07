"""Purge-invariance of the MeOH D01 v3 rank result: per purge level (0.5-40 %), economic order vs upstream STY-per-gRe order."""
import csv, json, sys
from itertools import combinations
from pathlib import Path
import openpyxl
from scipy.stats import spearmanr, kendalltau
WB = Path(sys.argv[1]); OUT = Path(sys.argv[2]); OUT.mkdir(parents=True, exist_ok=True)
wb = openpyxl.load_workbook(WB, data_only=True)
rows = [r for r in wb["Purge_Sweep"].iter_rows(min_row=4, values_only=True) if r[0] and isinstance(r[1], (int, float))]
cands = list(dict.fromkeys(r[0] for r in rows))
sty = {"1 wt% Re | 200 C": 55, "5 wt% Re | 200 C": 18, "1 wt% Re | 250 C": 65, "5 wt% Re | 250 C": 16}
up = {n: i + 1 for i, n in enumerate(sorted(cands, key=lambda n: -sty[n]))}
purges = sorted(set(round(r[1], 4) for r in rows))
out = []
for p in purges:
    sel = {n: [r[2] for r in rows if r[0] == n and abs(r[1] - p) < 1e-9] for n in cands}
    if not all(sel.values()): continue
    npc = {n: sel[n][0] for n in cands}; e = sorted(cands, key=lambda n: npc[n]); er = {n: i + 1 for i, n in enumerate(e)}
    a = [up[n] for n in cands]; b = [er[n] for n in cands]
    inv = sum(1 for x, y in combinations(cands, 2) if (up[x] - up[y]) * (er[x] - er[y]) < 0)
    out.append({"purge": p, "economic_order": " > ".join(e), "economic_winner": e[0], "rank_of_upstream_winner_1wtRe_250C": er["1 wt% Re | 250 C"], "rank_of_5wtRe_250C": er["5 wt% Re | 250 C"],
                "spearman": round(float(spearmanr(a, b).statistic), 3), "kendall": round(float(kendalltau(a, b).statistic), 3), "pairwise_inversions": inv, **{f"NPC_{n}": round(npc[n], 2) for n in cands}})
with open(OUT / "meoh_purge_robustness_D01v3.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
summ = {"purge_levels": len(out), "purge_min": out[0]["purge"], "purge_max": out[-1]["purge"],
        "upstream_winner_ever_economic_winner": any(o["economic_winner"] == "1 wt% Re | 250 C" for o in out),
        "highest_conversion_state_5wtRe_250C_ever_economic_winner": any(o["economic_winner"] == "5 wt% Re | 250 C" for o in out),
        "max_spearman": max(o["spearman"] for o in out), "min_pairwise_inversions": min(o["pairwise_inversions"] for o in out),
        "economic_winner_by_purge": {"1 wt% Re | 200 C": [o["purge"] for o in out if o["economic_winner"] == "1 wt% Re | 200 C"][:1] + [o["purge"] for o in out if o["economic_winner"] == "1 wt% Re | 200 C"][-1:],
                                     "5 wt% Re | 200 C": [o["purge"] for o in out if o["economic_winner"] == "5 wt% Re | 200 C"][:1] + [o["purge"] for o in out if o["economic_winner"] == "5 wt% Re | 200 C"][-1:]},
        "per_candidate_purge_optimum": {n: {"purge": min((r for r in rows if r[0] == n), key=lambda r: r[2])[1], "NPC": round(min(r[2] for r in rows if r[0] == n), 2)} for n in cands},
        "note": "per-candidate NPC minimum sits at the 0.5 % lower bound of the sweep for every state (boundary optimum); 2 % purge remains the source-anchored canonical comparison"}
(OUT / "meoh_purge_robustness_D01v3_summary.json").write_text(json.dumps(summ, indent=1), encoding="utf-8"); print(json.dumps(summ, indent=1))
