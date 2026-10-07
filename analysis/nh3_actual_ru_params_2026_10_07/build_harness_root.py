"""Build an NH3-FINAL-1.1 harness root from the repository and compute only the response columns the actual-Ru
analyses read.

The frozen response surface (14,136 process states x 1,201 descriptor grid points) is not in the repository. The
analyses only interpolate it at a few descriptor values (NH3Harness.interp_state_vector reads grid columns j and j + 1
around each descriptor). This script computes exactly those columns with the harness's own Condition.logtof, for

  * the 15 pure metals (EN0_CANON; the self-check gate and the Fe / Ru vectors of every analysis), and
  * the effective descriptors of the measured Ru catalysts drawn in variant B
    (analysis/nh3_supported_2026_10_06/supported_candidates.csv, same filter as run_mc_ru_actual.py),

and writes them into the cache file the harness expects. Every other column is NaN, so a read outside the computed
set propagates NaN instead of a number. Run on the CI runner only; the file is never committed.

    python build_harness_root.py <harness_root> [--workers N]
"""
import argparse
import csv
import hashlib
import json
import math
import shutil
import sys
import time
from multiprocessing import get_context
from pathlib import Path

import numpy as np
import yaml

REPO = Path(__file__).resolve().parents[2]
CORE = REPO / "provenance" / "discover_v1" / "source_harness"
RUN_NAME = "nh3_final_20260905T134204Z"
WORKBOOK = REPO / "provenance" / "nh3_final_1_1" / "source_harness" / "inputs" / "ammonia_activity_volcano_s1_v1.xlsx"
WORKBOOK_SHA256 = "fc259c5311744cccb82a7bc80ba4529f9bd34c61ed7933890dac70f016dce9ba"
SUPPORTED = REPO / "analysis" / "nh3_supported_2026_10_06" / "supported_candidates.csv"

H = None  # harness, inherited by forked workers


def _column(j):
    e = float(H.EGRID[j])
    return j, np.array([s["condition"].logtof(e) for s in H.process_states], dtype=float)


def needed_columns(h, xs):
    cols = set()
    for x in xs:  # same arithmetic as NH3Harness.interp_state_vector
        x = min(max(float(x), float(h.EGRID[0])), float(h.EGRID[-1]))
        pos = (x - h.EGRID[0]) / (h.EGRID[1] - h.EGRID[0])
        j = int(math.floor(pos))
        cols.update([len(h.EGRID) - 1] if j >= len(h.EGRID) - 1 else [j, j + 1])
    return sorted(cols)


def main():
    global H
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    root = Path(a.root)

    sha = hashlib.sha256(WORKBOOK.read_bytes()).hexdigest()
    if sha != WORKBOOK_SHA256:
        raise SystemExit(f"input workbook hash {sha} != pinned {WORKBOOK_SHA256}")
    (root / "inputs").mkdir(parents=True, exist_ok=True)
    shutil.copy2(CORE / "harness_core.py", root / "harness_core.py")
    shutil.copy2(WORKBOOK, root / "inputs" / WORKBOOK.name)
    run = root / "outputs" / RUN_NAME
    run.mkdir(parents=True, exist_ok=True)
    for f in ("manifest_resolved.yaml", "results.json"):
        shutil.copy2(CORE / "outputs" / RUN_NAME / f, run / f)

    sys.path.insert(0, str(root))
    import harness_core as hc
    t0 = time.time()
    H = hc.NH3Harness(yaml.safe_load((run / "manifest_resolved.yaml").read_text(encoding="utf-8")), root)
    assert H.NSTATE == 14136, H.NSTATE
    print(f"harness built: {H.NSTATE} states, {len(H.EGRID)} grid points ({time.time() - t0:.0f} s)", flush=True)

    meas = [x for x in csv.DictReader(SUPPORTED.open(encoding="utf-8"))
            if x["status"].startswith("primary") and x["active_metals"] == "Ru" and x["cost_USD_t"] != ""]
    xs = [hc.EN0_CANON[m] for m in hc.ACTIVITY_ORDER_CANON] + [float(x["E_eff_eV"]) for x in meas]
    cols = needed_columns(H, xs)
    print(f"descriptors: 15 pure metals + {len(meas)} measured Ru catalysts -> {len(cols)} of {len(H.EGRID)} columns",
          flush=True)

    resp = np.full((H.NSTATE, len(H.EGRID)), np.nan)
    t0 = time.time()
    with get_context("fork").Pool(a.workers) as pool:
        for n, (j, col) in enumerate(pool.imap_unordered(_column, cols), 1):
            resp[:, j] = col
            if n % 10 == 0 or n == len(cols):
                print(f"  columns {n}/{len(cols)} ({time.time() - t0:.0f} s)", flush=True)
    assert np.isfinite(resp[:, cols]).all()
    cp = H.response_cache_path()
    cp.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(cp, response=resp, EGRID=H.EGRID)
    meta = {"cache": cp.name, "workbook_sha256": sha, "states": H.NSTATE, "grid_points": len(H.EGRID),
            "columns_computed": cols, "measured_Ru_catalysts": len(meas), "seconds": round(time.time() - t0, 1)}
    (root / "partial_response_columns.json").write_text(json.dumps(meta, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {cp} ({len(cols)} columns)")


if __name__ == "__main__":
    main()
