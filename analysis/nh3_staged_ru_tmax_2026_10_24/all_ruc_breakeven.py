"""Financing rate at which an all-Ru/C converter matches an all-Fe converter, in the 9 MPa three-bed adiabatic
converter at each Ru/C temperature limit, against the KAAP-type loop of Fig. 5a (2026-10-24).

Fig. 5a (KAAP-type loop, isothermal plug-flow states) puts the Ru/C - Fe break-even at 4.57 %/y, whereas in Fig. 5b
the all-Ru/C converter crosses all-Fe near 2.5 %/y. Both use the same loop (90 bar, -20 C separator, 8 % inerts) and
rate laws; the staged beds are adiabatic and each Ru/C bed must leave at or below its temperature limit. Reading the
committed cost curves at the three limits shows whether that limit accounts for the difference. Linear interpolation
between grid points (0.05 %/y steps).

    D:\\Research\\CatalystForge\\.venv\\Scripts\\python.exe -X utf8 all_ruc_breakeven.py   # all_ruc_breakeven.json
"""
import csv
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CURVES = ROOT / "analysis/nh3_keestra_consolidation_2026_10_20/financing_curves.csv"


def crossing(points):
    """First rate (%/y) where the difference turns from negative to non-negative."""
    prev = None
    for rate, diff in points:
        if prev is not None and prev[1] < 0 <= diff:
            return prev[0] + (rate - prev[0]) * (-prev[1]) / (diff - prev[1])
        prev = (rate, diff)
    return None


def main():
    rows = list(csv.DictReader(CURVES.open(encoding="utf-8")))
    pct = lambda x: float(x["financing_rate_pct"])  # noqa: E731
    out = {
        "KAAP_type_loop_RuC_vs_Fe_pct": crossing([(pct(x), float(x["KAAP_RuC_minus_Fe"])) for x in rows]),
        "staged_all_RuC_vs_all_Fe_pct": {
            "460": crossing([(pct(x), float(x["staged_all_RuC"]) - float(x["staged_all_Fe"])) for x in rows])},
        "sources": {"460": str(CURVES.relative_to(ROOT)).replace("\\", "/")},
    }
    for t in ("500", "530"):
        path = HERE / f"tmax{t}_window.csv"
        w = list(csv.DictReader(path.open(encoding="utf-8")))
        out["staged_all_RuC_vs_all_Fe_pct"][t] = crossing(
            [(100 * float(x["fin_rate"]), float(x["cost_RRR"]) - float(x["cost_FFF"])) for x in w])
        out["sources"][t] = str(path.relative_to(ROOT)).replace("\\", "/")
    (HERE / "all_ruc_breakeven.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
