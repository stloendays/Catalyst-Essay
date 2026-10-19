"""Assert the headline numbers quoted in RESULTS.md against results/summary.json (CI gate)."""
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
s = json.loads((HERE / "results" / "summary.json").read_text())

EXPECT = {
    ("central", "parity_scale_mw"): (0.5952444122, 1e-8),
    ("central", "cost_Ru_0p1MW"): (19.69435115, 1e-6),
    ("central", "cost_Ni_0p1MW"): (42.40889800, 1e-6),
    ("central", "cost_Ru_100MW"): (8.473475035, 1e-6),
    ("central", "cost_Ni_100MW"): (3.236964773, 1e-6),
    ("central", "Pi"): (5.181220345, 1e-6),
    ("central", "phi_proc_0p1MW"): (9.131805686, 1e-6),
    ("central", "phi_proc_100MW"): (0.03763215129, 1e-8),
    ("boundary", "parity_scale_source_2019_price_life5"): (0.8262525988, 1e-8),
    ("monte_carlo", "parity_scale_median_mw"): (0.8576836897, 1e-8),
}
P_EXPECT = {"0.1": 0.983, "0.3": 0.8322, "1": 0.4405, "3": 0.1571, "10": 0.0291, "30": 0.0054, "100": 0.0005}

bad = []
for (sec, key), (val, tol) in EXPECT.items():
    got = s[sec][key]
    if not math.isclose(got, val, rel_tol=0, abs_tol=tol):
        bad.append(f"{sec}.{key}: got {got!r}, expected {val!r}")
for k, v in P_EXPECT.items():
    got = s["monte_carlo"]["p_ru_cheaper_by_scale"][k]
    if abs(got - v) > 1e-12:
        bad.append(f"P(Ru<Ni) at {k} MW: got {got}, expected {v}")
if s["central"]["ranking_0p1MW"] != "Ru>Ni" or s["central"]["ranking_100MW"] != "Ni>Ru":
    bad.append("central rankings changed")
if s["boundary"]["max_log10_diff_full_vs_leverage"] > 1e-6:
    bad.append("H3 leverage bookkeeping check failed")
if not all(s["hypotheses"].values()):
    bad.append(f"hypothesis flags changed: {s['hypotheses']}")
if bad:
    print("HEADLINE MISMATCH\n" + "\n".join(bad)); sys.exit(1)
print("All headline numbers in RESULTS.md reproduce.")
