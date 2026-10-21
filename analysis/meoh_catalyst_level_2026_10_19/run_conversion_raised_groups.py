"""Per-group table of the catalyst-level comparison with conversion raised toward equilibrium (cost_f0.95), the
manuscript's primary methanol count since 2026-10-20 (supervisor: each candidate at its own best permitted condition).

Uses the functions of run_catalyst_level.py unchanged and asserts the committed summary.json counts before writing.

    python run_conversion_raised_groups.py  -> groups_catalyst_level_conversion_raised.csv (+ stdout)
"""
import json

import pandas as pd

import run_catalyst_level as R

COL = "cost_f0.95"
RE_DOI = "10.1021/acscatal.5c"   # Gothe et al. 2025, Re/TiO2; the paper ranks its catalysts per gram of Re


def main():
    s = json.loads((R.HERE / "summary.json").read_text(encoding="utf-8"))["conversion_raised"][COL]["cat_primary"]
    c = pd.read_csv(R.POOLED / "pooled_candidates.csv")
    p = pd.read_csv(R.CONV)
    p = p[p["mode"] == "printed"].assign(sty_basis="")
    assert len(p) == len(c)
    fp = R.identities(R.scored(p, COL))
    gm = R.compare(R.catalyst_table(fp, "cat_primary", COL))
    b = R.brief(gm)
    for k in ("groups_2plus_catalysts", "changed", "gt5pct", "gt10pct", "papers_changed"):
        assert b[k] == s[k], (k, b[k], s[k])
    gm.to_csv(R.HERE / "groups_catalyst_level_conversion_raised.csv", index=False, float_format="%.6g")
    re = gm[gm.doi.str.startswith(RE_DOI)]
    print(f"conversion raised: {b['changed']}/{b['groups_2plus_catalysts']} changed, >5% {b['gt5pct']}, "
          f">10% {b['gt10pct']}, papers {b['papers_changed']}, CI {b['ci95']}")
    print("Re/TiO2 group(s):")
    print(re.to_string(index=False))


if __name__ == "__main__":
    main()
