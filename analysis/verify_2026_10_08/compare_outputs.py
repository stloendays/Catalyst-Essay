"""Compare regenerated outputs in the working tree with the committed versions (HEAD).

    python analysis/verify_2026_10_08/compare_outputs.py FILE [FILE ...] [--rtol 1e-6]

CSV: same columns and rows; booleans, integers stored as text and strings exactly; floating-point columns to a
relative tolerance (NaN equals NaN). JSON: tools/compare_json_numbers.py rules (integers and strings exactly, floats to
the tolerance). Used by the verify-2026-10-08 workflow to show that a clean GitHub runner reproduces the committed
verification outputs. Exits 1 and lists every difference otherwise.
"""
import argparse
import io
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))
from compare_json_numbers import walk  # noqa: E402


def committed(path):
    return subprocess.run(["git", "-C", str(REPO), "show", f"HEAD:{path}"], capture_output=True, check=True).stdout


def compare_csv(path, rtol):
    a = pd.read_csv(io.BytesIO(committed(path)), encoding="utf-8-sig", keep_default_na=False, na_values=[""])
    b = pd.read_csv(REPO / path, encoding="utf-8-sig", keep_default_na=False, na_values=[""])
    out = []
    if list(a.columns) != list(b.columns):
        return [f"{path}: columns differ"]
    if len(a) != len(b):
        return [f"{path}: {len(a)} rows committed, {len(b)} regenerated"]
    worst = 0.0
    for c in a.columns:
        x, y = a[c], b[c]
        if pd.api.types.is_float_dtype(x) or pd.api.types.is_float_dtype(y):
            xv, yv = x.to_numpy(float), y.to_numpy(float)
            ok = np.isclose(xv, yv, rtol=rtol, atol=1e-12, equal_nan=True)
            if not ok.all():
                i = int(np.argmax(~ok))
                out.append(f"{path}:{c}: {int((~ok).sum())} values differ, first row {i}: {xv[i]!r} vs {yv[i]!r}")
            both = np.isfinite(xv) & np.isfinite(yv) & (np.abs(xv) > 1e-12)
            if both.any():
                worst = max(worst, float(np.max(np.abs(yv[both] / xv[both] - 1.0))))
        elif not x.fillna("").astype(str).equals(y.fillna("").astype(str)):
            n = int((x.fillna("").astype(str) != y.fillna("").astype(str)).sum())
            out.append(f"{path}:{c}: {n} entries differ")
    print(f"{path}: {len(a)} rows, max relative difference {worst:.2e}")
    return out


def compare_json(path, rtol):
    a = json.loads(committed(path).decode("utf-8"))
    b = json.loads((REPO / path).read_text(encoding="utf-8"))
    out = []
    walk(a, b, path, rtol, 1e-12, set(), out)
    print(f"{path}: {'identical within tolerance' if not out else f'{len(out)} differences'}")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--rtol", type=float, default=1e-6)
    args = ap.parse_args()
    problems = []
    for f in args.files:
        problems += (compare_json if f.endswith(".json") else compare_csv)(f, args.rtol)
    if problems:
        print("\nDIFFERENCES:")
        print("\n".join(problems))
        sys.exit(1)
    print(f"\nAll {len(args.files)} files reproduce the committed outputs (rtol {args.rtol:g}).")


if __name__ == "__main__":
    main()
