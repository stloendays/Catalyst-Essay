"""Default-mode reproduction check: a script run with MEOH_FIELD_SET=first (the default) must regenerate its committed
outputs. Compares every given file in the working tree with its committed version (git HEAD): byte-identical, or
else numerically identical (numbers to 1e-9 relative or 1e-12 absolute, every other field exactly); keys that hold run
time or machine timing are skipped. Prints one line per file and exits 1 if any file differs.

    python compare_default.py [--skip KEY ...] FILE ...      (paths relative to the repository root)
"""
import argparse
import csv
import io
import json
import math
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
RTOL, ATOL = 1e-9, 1e-12
SKIP = {"runtime_s", "timing_s", "compute_fraction_recycled_opt", "workers"}     # run time and process count


def committed(path):
    return subprocess.run(["git", "show", f"HEAD:{path}"], cwd=REPO, capture_output=True, check=True).stdout


def num(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v


def same_value(a, b):
    if a == b:
        return True
    x, y = num(a), num(b)
    if x is None or y is None or isinstance(a, bool) or isinstance(b, bool):
        return False
    if math.isnan(x) and math.isnan(y):
        return True
    return abs(x - y) <= max(ATOL, RTOL * max(abs(x), abs(y)))


def worst(a, b):
    x, y = num(a), num(b)
    if x is None or y is None or a == b or (math.isnan(x) and math.isnan(y)):
        return 0.0
    return abs(x - y) / max(abs(x), abs(y), 1e-300)


def json_diff(a, b, path, skip, w):
    if isinstance(a, dict):
        if not isinstance(b, dict) or a.keys() != b.keys():
            return path or "/"
        for k in a:
            if k in skip:
                continue
            d = json_diff(a[k], b[k], f"{path}.{k}", skip, w)
            if d:
                return d
        return None
    if isinstance(a, list):
        if not isinstance(b, list) or len(a) != len(b):
            return path
        for i, (x, y) in enumerate(zip(a, b)):
            d = json_diff(x, y, f"{path}[{i}]", skip, w)
            if d:
                return d
        return None
    w[0] = max(w[0], worst(a, b))
    return None if same_value(a, b) else path


def csv_diff(a, b, w):
    ra, rb = list(csv.reader(io.StringIO(a))), list(csv.reader(io.StringIO(b)))
    if len(ra) != len(rb):
        return f"rows {len(ra)} != {len(rb)}"
    for i, (x, y) in enumerate(zip(ra, rb)):
        if len(x) != len(y):
            return f"row {i}: {len(x)} != {len(y)} fields"
        for j, (u, v) in enumerate(zip(x, y)):
            w[0] = max(w[0], worst(u, v))
            if not same_value(u, v):
                return f"row {i} field {ra[0][j] if j < len(ra[0]) else j}: {u!r} != {v!r}"
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip", nargs="*", default=[])
    ap.add_argument("files", nargs="+")
    args = ap.parse_args()
    skip = SKIP | set(args.skip)
    bad = 0
    for f in args.files:
        new, old = (REPO / f).read_bytes(), committed(f)
        if not f.endswith(".gz"):      # the checkout may carry CRLF line ends
            new, old = new.replace(bytes([13, 10]), bytes([10])), old.replace(bytes([13, 10]), bytes([10]))
        if new == old:
            print(f"byte-identical         {f}")
            continue
        w = [0.0]
        if f.endswith(".json"):
            d = json_diff(json.loads(new), json.loads(old), "", skip, w)
        elif f.endswith((".csv", ".csv.gz")):
            if f.endswith(".gz"):
                import gzip
                new, old = gzip.decompress(new), gzip.decompress(old)
            d = csv_diff(new.decode("utf-8"), old.decode("utf-8"), w)
        else:
            d = "differs (not a JSON or CSV file)"
        if d:
            bad += 1
            print(f"DIFFERS                {f}: {d}")
        else:
            print(f"numerically identical  {f} (max relative difference {w[0]:.1e})")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
