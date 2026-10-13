"""Compare two JSON result files: equal structure, equal strings/booleans/integers, floats within a relative 1e-6
(cross-platform floating-point noise). Keys named in SKIP are ignored.

    python compare_json.py regenerated.json committed.json
"""
import json
import math
import sys

SKIP = {"runtime_s", "max_rel_cost_diff_vs_frozen"}


def cmp(a, b, path="$"):
    if isinstance(a, dict) and isinstance(b, dict):
        ka, kb = set(a) - SKIP, set(b) - SKIP
        if ka != kb:
            yield f"{path}: keys {sorted(ka ^ kb)}"
        for k in sorted(ka & kb):
            yield from cmp(a[k], b[k], f"{path}.{k}")
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            yield f"{path}: length {len(a)} != {len(b)}"
        for i, (x, y) in enumerate(zip(a, b)):
            yield from cmp(x, y, f"{path}[{i}]")
    elif isinstance(a, float) or isinstance(b, float):
        if not (isinstance(a, (int, float)) and isinstance(b, (int, float))):
            yield f"{path}: {a!r} != {b!r}"
        elif not (math.isclose(a, b, rel_tol=1e-6, abs_tol=1e-12) or (math.isnan(a) and math.isnan(b))):
            yield f"{path}: {a!r} != {b!r}"
    elif a != b:
        yield f"{path}: {a!r} != {b!r}"


if __name__ == "__main__":
    a, b = (json.load(open(p, encoding="utf-8")) for p in sys.argv[1:3])
    diffs = list(cmp(a, b))
    for d in diffs[:50]:
        print(d)
    print("identical within tolerance" if not diffs else f"{len(diffs)} differences")
    sys.exit(1 if diffs else 0)
