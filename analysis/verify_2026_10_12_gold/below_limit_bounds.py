"""Gold-standard review of 2026-10-12: does any correction change the frozen methanol result (S5) or its inlet-limit
sensitivity (S6)?

The review (AI-assisted re-check of the 100 sampled values against the papers and SI, accepted by the author as the
working basis) found no extracted value in conflict with the papers. Its corrections are locators (Frei 2019 9.7 %),
derived quantities that are numerically right (Dang 2020 H2/CO2 = 3.0417 from the feed composition), metric names,
and one qualifier: Ota 2012 prints the CH4 selectivity of PdZnAl as "<0.1 %", an upper bound. The frozen closure
(meoh_candidates.pct) sets every "<" selectivity to zero. This script tests the other end of that bound for every
"<"-qualified CO or CH4 selectivity in the extracted records (not only Ota 2012): the selectivity is set to its printed
bound, the selectivities are re-closed exactly as in the frozen code, the changed candidates are re-costed with the
frozen plant_costs, and the 40 groups are scored again for S5 (cost_recycled_opt) and S6 (cost_recycled_opt_inlet).
Unchanged candidates keep their frozen costs; the script first re-costs a few unchanged candidates and asserts that
they reproduce the frozen values.

Outputs (this folder): below_limit_candidates.csv (every changed candidate, frozen and bound costs),
below_limit_groups.csv (group verdicts, frozen and bound, S5 and S6), below_limit_summary.json.
"""
import json
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
INV = REPO / "analysis" / "meoh_literature_inversion_2026_10_05"
sys.path.insert(0, str(REPO / "data" / "meoh"))
sys.path.insert(0, str(INV))
import meoh_candidates as M  # noqa: E402
from mismatch_kinds import classify  # noqa: E402

COLS = {"S5": "cost_recycled_opt", "S6": "cost_recycled_opt_inlet"}
KEY = ["doi", "catalyst", "T_C", "P_bar", "ghsv_key"]


def pct_upper(v, q):
    """As meoh_candidates.pct, but a '<' value is taken at its printed bound instead of zero."""
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return None
    return float(v) / 100.0


def candidates(upper):
    orig = M.pct
    M.pct = pct_upper if upper else orig
    try:
        return M.build_candidates(M.read_records(), printed_only=True)
    finally:
        M.pct = orig


def costs(frame):
    rows = [dict(zip(M.ROW_KEYS, (float(r[k]) for k in M.ROW_KEYS))) for r in frame[M.ROW_KEYS].to_dict("records")]
    with Pool(4) as pool:
        res = pool.map(M.plant_costs_star, [(r, None) for r in rows])
    return pd.DataFrame(res, index=frame.index)


def score(frame, col):
    gm, s = M.aggregate(frame, col)
    gm, kinds = classify(frame, gm, col)
    m = gm[gm.top1_mismatch]
    s["gt5pct"] = int((m.regret > 0.05).sum())
    s["kinds"] = kinds
    return gm.set_index("group"), s


def main():
    frozen = pd.read_csv(INV / "literature_candidates.csv")
    base, bound = candidates(False), candidates(True)
    assert len(base) == len(bound) == len(frozen)
    # the frozen file is written in another row order: align it on the candidate key
    for f in (base, frozen):
        f["_k"] = (f.doi.astype(str) + "|" + f.catalyst.astype(str) + "|" + f.T_C.astype(float).round(2).astype(str)
                   + "|" + f.P_bar.astype(float).round(2).astype(str) + "|" + f.ghsv_key.astype(str))
    assert frozen._k.is_unique and base._k.is_unique
    frozen = frozen.set_index("_k").loc[base._k].reset_index()
    for k in ("SCO", "SCH4", "SMeOH", "X", "STY"):
        assert np.allclose(base[k].astype(float), frozen[k].astype(float), equal_nan=True), k
    changed = ~(np.isclose(base.SCO, bound.SCO) & np.isclose(base.SCH4, bound.SCH4))
    print(f"candidates with a '<' selectivity in the scored cohort: {int(changed.sum())} of {len(base)}")

    # the frozen costs, and a reproduction check on unchanged candidates
    for c in COLS.values():
        base[c] = frozen[c].values
    probe = base[~changed].head(4)
    rep = costs(probe)
    for c in COLS.values():
        assert np.allclose(rep[c], probe[c], rtol=1e-9, equal_nan=True), c
    bound_c = costs(bound[changed])
    for c in COLS.values():
        bound[c] = base[c]
        bound.loc[changed, c] = bound_c[c]

    out = {"changed_candidates": int(changed.sum()), "papers": sorted(base.loc[changed, "doi"].unique())}
    groups = []
    for tag, col in COLS.items():
        gb, sb = score(base, col)
        gu, su = score(bound, col)
        out[tag] = {"frozen": {k: sb[k] for k in ("groups", "top1_mismatch_groups", "papers_with_mismatch", "gt5pct")}
                    | {"other_catalyst": sb["kinds"]["other_catalyst"], "other_temperature": sb["kinds"]["other_temperature"]},
                    "upper_bound": {k: su[k] for k in ("groups", "top1_mismatch_groups", "papers_with_mismatch", "gt5pct")}
                    | {"other_catalyst": su["kinds"]["other_catalyst"], "other_temperature": su["kinds"]["other_temperature"]}}
        j = gb[["top1_mismatch", "regret", "economic_winner"]].join(
            gu[["top1_mismatch", "regret", "economic_winner"]], lsuffix="_frozen", rsuffix="_bound")
        j["treatment"] = tag
        j["verdict_changed"] = j.top1_mismatch_frozen != j.top1_mismatch_bound
        j["winner_changed"] = j.economic_winner_frozen != j.economic_winner_bound
        j["touched"] = j.index.isin(base.loc[changed, "group"])
        groups.append(j.reset_index())
        out[tag]["groups_touched"] = int(j.touched.sum())
        out[tag]["verdicts_changed"] = j.index[j.verdict_changed].tolist()
        out[tag]["plant_winner_changed"] = j.index[j.winner_changed].tolist()
    g = pd.concat(groups, ignore_index=True)
    g.to_csv(HERE / "below_limit_groups.csv", index=False, encoding="utf-8-sig", float_format="%.6g")

    d = base.loc[changed, KEY + ["group", "SMeOH", "SCO", "SCH4"]].copy()
    for k in ("SCO", "SCH4"):
        d[f"{k}_bound"] = bound.loc[changed, k]
    for tag, col in COLS.items():
        d[f"{tag}_frozen"] = base.loc[changed, col]
        d[f"{tag}_bound"] = bound.loc[changed, col]
        d[f"{tag}_rel_change"] = d[f"{tag}_bound"] / d[f"{tag}_frozen"] - 1
    d.to_csv(HERE / "below_limit_candidates.csv", index=False, encoding="utf-8-sig", float_format="%.6g")
    for tag in COLS:
        r = d[f"{tag}_rel_change"].abs()
        out[tag]["max_abs_cost_change"] = float(r.max()) if len(r) else 0.0
    (HERE / "below_limit_summary.json").write_text(json.dumps(out, indent=1, default=str) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    main()
