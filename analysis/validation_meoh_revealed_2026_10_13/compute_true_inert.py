"""S6-TI costs (reactor-inlet limit 6.8625 % on CH4 + N2 only) for both cohorts, with the unchanged code of
analysis/meoh_inlet_definition_2026_10_12/run_inlet_definition.py (sweep, pick, reproduce).

The same sweeps also re-derive every frozen cost column under the frozen CH4 + CO + N2 definition; the script stops
unless they reproduce the frozen columns (NaN pattern identical, 1e-6 relative). INLET_WORKERS processes (default 8,
the project limit). Outputs: costs_true_inert_printed.csv, costs_true_inert_extended.csv (entry, cost_S6TI,
purge_S6TI), true_inert_reproduction.json.
"""
import json
import os
import sys
import time

os.environ.setdefault("INLET_WORKERS", "8")
from rp_common import COHORTS, HERE, INLET, TI_FILE  # noqa: E402

sys.path.insert(0, str(INLET))
import pandas as pd  # noqa: E402
import run_inlet_definition as R  # noqa: E402

assert R.WORKERS <= 8


def main():
    rep = {}
    for cohort, path in COHORTS.items():
        t0 = time.time()
        cand = pd.read_csv(path)
        t, n_uniq = R.entry_table(cand)
        rep[cohort] = dict(rows=len(t), unique_operating_points=n_uniq, frozen_reproduction=R.reproduce(t),
                           runtime_s=round(time.time() - t0, 1))
        out = pd.DataFrame({"entry": cand.entry, "cost_S6TI": t[R.col("true_inert", "6.86")],
                            "purge_S6TI": t["purge_true_inert_6.86"]})
        out.to_csv(TI_FILE[cohort], index=False)
        print(cohort, rep[cohort]["rows"], n_uniq, rep[cohort]["frozen_reproduction"]["max_relative_difference"],
              rep[cohort]["runtime_s"], "s")
    (HERE / "true_inert_reproduction.json").write_text(json.dumps(rep, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
