"""Compare two JSON result files: integers and strings exactly, floats to a relative tolerance.

    python tools/compare_json_numbers.py COMMITTED.json REGENERATED.json [--rtol 1e-6] [--ignore runtime_s workers]

Used by the reproduction workflows: a rerun on a GitHub runner (Linux, its own BLAS) must give the committed counts
exactly and the committed costs to floating-point agreement. Exits 1 and lists every difference otherwise.
"""
import argparse
import json
import math
import sys


def walk(a, b, path, rtol, atol, ignore, out):
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k in ignore:
                continue
            if k not in a or k not in b:
                out.append(f"{path}/{k}: only in {'committed' if k in a else 'regenerated'}")
                continue
            walk(a[k], b[k], f"{path}/{k}", rtol, atol, ignore, out)
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            out.append(f"{path}: length {len(a)} vs {len(b)}")
            return
        for i, (x, y) in enumerate(zip(a, b)):
            walk(x, y, f"{path}[{i}]", rtol, atol, ignore, out)
    elif isinstance(a, bool) or isinstance(b, bool) or isinstance(a, str) or isinstance(b, str) or a is None or b is None:
        if a != b:
            out.append(f"{path}: {a!r} vs {b!r}")
    elif isinstance(a, int) and isinstance(b, int):
        if a != b:
            out.append(f"{path}: {a} vs {b}")
    elif isinstance(a, (int, float)) and isinstance(b, (int, float)):
        fa, fb = float(a), float(b)
        if math.isnan(fa) and math.isnan(fb):
            return
        if not math.isclose(fa, fb, rel_tol=rtol, abs_tol=atol):
            out.append(f"{path}: {fa!r} vs {fb!r}")
    elif a != b:
        out.append(f"{path}: {a!r} vs {b!r}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("committed")
    ap.add_argument("regenerated")
    ap.add_argument("--rtol", type=float, default=1e-6)
    ap.add_argument("--atol", type=float, default=1e-9)
    ap.add_argument("--ignore", nargs="*", default=["runtime_s", "workers", "timestamp"])
    a = ap.parse_args()
    with open(a.committed, encoding="utf-8") as f:
        x = json.load(f)
    with open(a.regenerated, encoding="utf-8") as f:
        y = json.load(f)
    out = []
    walk(x, y, "", a.rtol, a.atol, set(a.ignore), out)
    for line in out[:200]:
        print(line)
    print(f"{len(out)} difference(s) between {a.committed} and {a.regenerated}")
    sys.exit(1 if out else 0)


if __name__ == "__main__":
    main()
