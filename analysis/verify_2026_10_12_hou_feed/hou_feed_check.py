"""Hou et al. 2024 (J. Environ. Sci. 140, 91-102, 10.1016/j.jes.2023.05.010): laboratory feed of the bare In2O3 controls.

Section 1.4 of the article tests both Au/In2O3 and bare In2O3 at H2:CO2:Ar = 4:1:1. The extraction recorded the bare In2O3
rows (SI Table S5: 3 printed entries; SI Fig. S4: 12 plot-read entries, all-entries cohort only) with no inert (laboratory
y_CO2 = 0.20); the correct value is 1/6, as already used for the Au/In2O3 rows. (The Au/In2O3 rows name the inert N2 instead of Ar; only the inert fraction enters
the model.)

Where the laboratory CO2 fraction enters: the space-velocity STY (not used here: all six Hou entries print their STY) and
the laboratory equilibrium conversion of the conversion-raised analysis (run_conversion_sensitivity.py). The frozen S5 and
S6 costs do not use it. This script recomputes the conversion-raised analysis for the corrected rows with the
frozen code, keeps every other row's frozen result, and compares the group counts with the frozen summary.

Output: hou_feed_check.json. Single process.
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
import run_conversion_sensitivity as RC  # noqa: E402
from meoh_candidates import ROW_KEYS, aggregate  # noqa: E402
from mismatch_kinds import classify  # noqa: E402

DOI = "10.1016/j.jes.2023.05.010"
Y_CO2 = 1.0 / 6.0
COLS = ["lab", "x_eq", "x_eq_roots", "u0",
        *[f"{p}_f{x:g}" for p in ("cost", "m", "u") for x in (RC.F_PRIMARY, *RC.F_VARIANTS)],
        "cost_two_sided", "m_two_sided", "u_two_sided"]


def key(vals):
    return tuple(f"{float(x):.6g}" for x in vals)


def main():
    pts = pd.read_csv(INV / "conversion_sensitivity_points.csv")
    frozen = json.loads((INV / "conversion_sensitivity_summary.json").read_text(encoding="utf-8"))["scenarios"]
    table = {key(r[k] for k in ROW_KEYS): {c: r[c] for c in COLS} for _, r in pts.drop_duplicates(ROW_KEYS).iterrows()}
    sets = {"printed": pd.read_csv(INV / "literature_candidates.csv"),
            "all": pd.read_csv(INV / "literature_candidates_all_entries.csv")}
    out = {"doi": DOI, "corrected_rows": [], "scenarios": {}}
    for f in sets.values():
        sel = f.doi.eq(DOI) & f.entry.str.match(r"SI (Table S5|Figure S4)")
        assert sel.sum() in (3, 15) and (f.loc[sel, "y_co2"].round(6) == 0.2).all()
        assert (f.loc[f.doi.eq(DOI) & ~sel, "y_co2"].round(6) == round(Y_CO2, 6)).all()
        for r in f[sel].itertuples(index=False):
            k = key(getattr(r, c) for c in ROW_KEYS)
            if any(x["key"] == k for x in out["corrected_rows"]):
                continue
            _, new = RC.evaluate((tuple(float(getattr(r, c)) for c in ROW_KEYS), Y_CO2))
            old = table[k]
            out["corrected_rows"].append(dict(key=k, catalyst=r.catalyst, y_co2_frozen=0.2, y_co2_corrected=Y_CO2,
                                              x_eq_frozen=float(old["x_eq"]), x_eq_corrected=float(new["x_eq"]),
                                              cost_f095_frozen=float(old["cost_f0.95"]),
                                              cost_f095_corrected=float(new["cost_f0.95"])))
            table[k] = {c: new[c] for c in COLS}
    changed = 0
    for mode, f in sets.items():
        f = f.copy()
        outs = [table[key(getattr(r, c) for c in ROW_KEYS)] for r in f.itertuples(index=False)]
        for c in COLS:
            f[c] = [o[c] for o in outs]
        for col, label in RC.COLS.items():
            gm, s = aggregate(f, col, label=label)
            gm, kinds = classify(f, gm, col)
            m = gm[gm.top1_mismatch]
            new = dict(different_winner=int(s["top1_mismatch_groups"]), gt5pct=int((m.regret > 0.05).sum()),
                       other_catalyst=int(kinds["other_catalyst"]["groups"]),
                       other_catalyst_gt5pct=int(kinds["other_catalyst"]["gt5pct"]))
            o = frozen[f"{mode}|{col}"]
            old = dict(different_winner=int(o["top1_mismatch_groups"]), gt5pct=int(o["gt5pct"]),
                       other_catalyst=int(o["kinds"]["other_catalyst"]["groups"]),
                       other_catalyst_gt5pct=int(o["kinds"]["other_catalyst"]["gt5pct"]))
            changed += new != old
            out["scenarios"][f"{mode}|{col}"] = dict(frozen=old, corrected=new)
            print(f"{mode:7s} {col:15s} {old} -> {new}{'' if new == old else '  CHANGED'}")
    out["scenarios_changed"] = changed
    (HERE / "hou_feed_check.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print("scenarios changed:", changed)


if __name__ == "__main__":
    main()
