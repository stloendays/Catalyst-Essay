"""The methanol field result when a paper's leaderboard is taken on the basis the paper itself ranks by.

The frozen primary ranks every paper by space-time yield per gram of catalyst. One paper of the scored cohort, Gothe et
al. 2025 (10.1021/acscatal.5c05984, Re/TiO2 at 1 and 5 wt% Re), reports and ranks space-time yield per gram of Re. This
script rescores the frozen S5 and S6 costs with that paper's leaderboard per gram of Re (STY per g catalyst / Re mass
fraction) and every other paper unchanged. Plant costs are the frozen ones (literature_candidates.csv); nothing is
re-optimized.

Output: metal_basis_summary.json (NH3_MODEL=1.1, the default) or nh3_1_2/metal_basis_summary.json (NH3_MODEL=1.2).
The methanol rescoring does not use the ammonia model, so both files carry the same numbers; the switch only keeps
the per-model output layout of the ammonia analyses (analysis/nh3_model.py).
"""
import json
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
INV = REPO / "analysis" / "meoh_literature_inversion_2026_10_05"
sys.path.insert(0, str(REPO / "data" / "meoh"))
sys.path.insert(0, str(INV))
sys.path.append(str(REPO / "analysis"))
import meoh_candidates as M  # noqa: E402
from mismatch_kinds import classify  # noqa: E402
import nh3_model as NM  # noqa: E402

DOI = "10.1021/acscatal.5c05984"
COLS = {"S5": "cost_recycled_opt", "S6": "cost_recycled_opt_inlet"}


def score(frame, col, up):
    gm, s = M.aggregate(frame, col, up_col=up)
    gm, kinds = classify(frame, gm, col)
    m = gm[gm.top1_mismatch]
    return gm, dict(groups=s["groups"], different_winner=s["top1_mismatch_groups"],
                    gt5pct=int((m.regret > 0.05).sum()), other_catalyst=kinds["other_catalyst"],
                    other_temperature=kinds["other_temperature"])


def main():
    c = pd.read_csv(INV / "literature_candidates.csv")
    wt = c.catalyst.str.extract(r"(\d+(?:\.\d+)?)\s*wt\s*%")[0].astype(float) / 100.0
    sel = c.doi.eq(DOI)
    assert wt[sel].notna().all()
    c["STY_paper_basis"] = c.STY.where(~sel, c.STY / wt)
    out = {"paper": DOI, "entries": int(sel.sum())}
    for tag, col in COLS.items():
        g0, s0 = score(c, col, "STY")
        g1, s1 = score(c, col, "STY_paper_basis")
        groups = sorted(set(g0.group[g0.doi == DOI]))
        out[tag] = {"per_g_catalyst": s0, "paper_basis": s1,
                    "groups_of_paper": {k: {"winner_per_g_catalyst": g0.set_index("group").at[k, "upstream_winner"],
                                            "regret_per_g_catalyst": float(g0.set_index("group").at[k, "regret"]),
                                            "winner_per_g_Re": g1.set_index("group").at[k, "upstream_winner"],
                                            "regret_per_g_Re": float(g1.set_index("group").at[k, "regret"]),
                                            "plant_winner": g1.set_index("group").at[k, "economic_winner"]}
                                        for k in groups}}
    (NM.out_dir(HERE) / "metal_basis_summary.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    for tag in COLS:
        a, b = out[tag]["per_g_catalyst"], out[tag]["paper_basis"]
        print(tag, f"{a['different_winner']}/{a['groups']} -> {b['different_winner']}/{b['groups']}; other catalyst "
                   f"{a['other_catalyst']['groups']}/{a['other_catalyst']['of']} (>5% {a['other_catalyst']['gt5pct']}) -> "
                   f"{b['other_catalyst']['groups']}/{b['other_catalyst']['of']} (>5% {b['other_catalyst']['gt5pct']}); "
                   f"other temperature {a['other_temperature']['groups']}/{a['other_temperature']['of']} "
                   f"(>5% {a['other_temperature']['gt5pct']}) -> {b['other_temperature']['groups']}/"
                   f"{b['other_temperature']['of']} (>5% {b['other_temperature']['gt5pct']})")


if __name__ == "__main__":
    main()
