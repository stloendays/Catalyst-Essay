"""Reproduction anchors of the inlet-definition analysis and the 83 -> 40 ledger (run by the meoh-inlet-definition
workflow after both scripts).

  frozen definition = the frozen columns (run_inlet_definition.py stops otherwise) and the frozen field result:
      S5 15/40, 6.86 % 28/40, lim4 28/40, lim10 24/40, lim30 16/40
  ledger: 83 groups / 909 entries / 44 papers -> 40 / 310 / 28; all entries S5 35/83, 6.86 % 54/82; grouping identical

With --committed DIR (a copy of the committed outputs taken before the rerun), the regenerated definition_scan.csv,
stability_5_15.csv, group_ledger.csv and both JSON summaries must equal the committed ones (integers exactly, floats
to 1e-9 relative).
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from common import ANCHORS  # noqa: E402

CSVS = ("definition_scan.csv", "stability_5_15.csv", "group_ledger.csv")
JSONS = ("summary.json", "ledger_summary.json")


def same_frame(a, b):
    if list(a.columns) != list(b.columns) or len(a) != len(b):
        return False
    for c in a.columns:
        x, y = a[c], b[c]
        if pd.api.types.is_float_dtype(x) or pd.api.types.is_float_dtype(y):
            if not np.allclose(x.astype(float), y.astype(float), rtol=1e-9, atol=0, equal_nan=True):
                return False
        elif not (x.fillna("").astype(str) == y.fillna("").astype(str)).all():
            return False
    return True


def same_json(a, b, path=""):
    if isinstance(a, dict):
        return isinstance(b, dict) and a.keys() == b.keys() and all(
            same_json(a[k], b[k], f"{path}.{k}") for k in a if k != "runtime_s")
    if isinstance(a, list):
        return isinstance(b, list) and len(a) == len(b) and all(same_json(x, y, path) for x, y in zip(a, b))
    if isinstance(a, float) or isinstance(b, float):
        return bool(np.isclose(float(a), float(b), rtol=1e-9, atol=1e-15, equal_nan=True))
    return a == b


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--committed", type=Path)
    args = ap.parse_args()
    fails = []
    scan = pd.read_csv(HERE / "definition_scan.csv", dtype={"limit_pct": str})
    for L, (dl, g) in ANCHORS.items():
        r = scan[(scan.definition == "frozen") & (scan.limit_pct == L)].iloc[0]
        ok = (r.different_leader, r.groups) == (dl, g)
        print(f"frozen {L:>5}: {r.different_leader}/{r.groups} (expected {dl}/{g}) {'ok' if ok else 'FAIL'}")
        fails += [] if ok else [f"anchor {L}"]
    s = json.loads((HERE / "summary.json").read_text())
    if not s["reproduction"]["max_relative_difference"] <= 1e-6:
        fails.append("frozen-column reproduction")
    led = json.loads((HERE / "ledger_summary.json").read_text())
    expect = {("all_entries", "groups"): 83, ("all_entries", "entries"): 909, ("all_entries", "papers"): 44,
              ("printed_primary", "groups"): 40, ("printed_primary", "entries"): 310,
              ("printed_primary", "papers"): 28}
    for (a, b), v in expect.items():
        if led[a][b] != v:
            fails.append(f"ledger {a}.{b} = {led[a][b]} != {v}")
    r5, r6 = led["all_entries_result"]["S5"], led["all_entries_result"]["S6_6_86pct"]
    if (r5["different_leader"], r5["groups"], r6["different_leader"], r6["groups"]) != (35, 83, 54, 82):
        fails.append("all-entries result")
    if not led["grouping_checks"]["identical"]:
        fails.append("grouping rule")
    print(f"ledger 83 -> {led['printed_primary']['groups']}; all entries S5 {r5['different_leader']}/{r5['groups']}, "
          f"6.86 % {r6['different_leader']}/{r6['groups']}")
    if args.committed:
        for f in CSVS:
            if not same_frame(pd.read_csv(HERE / f), pd.read_csv(args.committed / f)):
                fails.append(f"{f} differs from the committed file")
        for f in JSONS:
            if not same_json(json.loads((HERE / f).read_text()), json.loads((args.committed / f).read_text())):
                fails.append(f"{f} differs from the committed file")
        print("regenerated outputs equal the committed ones" if not fails else "")
    if fails:
        raise SystemExit("FAIL: " + "; ".join(fails))
    print("all anchors ok")


if __name__ == "__main__":
    main()
