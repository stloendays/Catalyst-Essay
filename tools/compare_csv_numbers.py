"""Compare two CSV result files: same columns and rows, text exactly, numbers to a relative tolerance.

    python tools/compare_csv_numbers.py COMMITTED.csv REGENERATED.csv [--rtol 1e-9] [--sort entry dim x]

Used by the reproduction workflows next to compare_json_numbers.py. --sort orders both files by the given columns
first (for files whose row order depends on how the work was split). Exits 1 and lists every difference otherwise.
"""
import argparse
import math
import sys

import numpy as np
import pandas as pd


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("committed")
    ap.add_argument("regenerated")
    ap.add_argument("--rtol", type=float, default=1e-9)
    ap.add_argument("--atol", type=float, default=0.0)
    ap.add_argument("--sort", nargs="*", default=[])
    a = ap.parse_args()
    x, y = pd.read_csv(a.committed), pd.read_csv(a.regenerated)
    out = []
    if list(x.columns) != list(y.columns):
        out.append(f"columns {list(x.columns)} vs {list(y.columns)}")
    elif len(x) != len(y):
        out.append(f"rows {len(x)} vs {len(y)}")
    else:
        if a.sort:
            x = x.sort_values(a.sort, kind="stable").reset_index(drop=True)
            y = y.sort_values(a.sort, kind="stable").reset_index(drop=True)
        for col in x.columns:
            for i, (p, q) in enumerate(zip(x[col], y[col])):
                num = all(isinstance(v, (int, float, np.number)) and not isinstance(v, (bool, np.bool_)) for v in (p, q))
                if num:
                    fp, fq = float(p), float(q)
                    if math.isnan(fp) and math.isnan(fq):
                        continue
                    if not math.isclose(fp, fq, rel_tol=a.rtol, abs_tol=a.atol):
                        out.append(f"row {i} {col}: {fp!r} vs {fq!r}")
                elif p != q and not (pd.isna(p) and pd.isna(q)):
                    out.append(f"row {i} {col}: {p!r} vs {q!r}")
    for line in out[:200]:
        print(line)
    print(f"{len(out)} difference(s) between {a.committed} and {a.regenerated}")
    sys.exit(1 if out else 0)


if __name__ == "__main__":
    main()
