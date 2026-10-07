"""Compare the files rewritten by rerunning the committed baseline scripts on the cloud harness root with their
committed versions (git HEAD). Numbers must agree to |a - b| <= 1e-9 + 1e-8 |b| (brentq roots to xtol 1e-11 in log10),
text fields exactly; P values are multiples of 1/5,000, so they are compared exactly.

    python validate_baseline.py <path> [<path> ...]      (paths relative to the repository root)
"""
import csv
import io
import json
import math
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def close(a, b):
    if isinstance(b, float) and (math.isinf(b) or math.isnan(b)):
        return (math.isnan(a) and math.isnan(b)) or a == b
    return abs(a - b) <= 1e-9 + 1e-8 * abs(b)


def num(s):
    try:
        return float(s)
    except ValueError:
        return None


def cmp_json(a, b, path, bad):
    if isinstance(b, dict):
        if set(a) != set(b):
            bad.append(f"{path}: keys differ")
        for k in b:
            if k in a:
                cmp_json(a[k], b[k], f"{path}.{k}", bad)
    elif isinstance(b, list):
        if len(a) != len(b):
            bad.append(f"{path}: length {len(a)} != {len(b)}")
        for i, (x, y) in enumerate(zip(a, b)):
            cmp_json(x, y, f"{path}[{i}]", bad)
    elif isinstance(b, (int, float)) and not isinstance(b, bool):
        exact = path.endswith("P_Fe_cheaper") or path.endswith("P_Ru_wins")
        if (a != b) if exact else not close(float(a), float(b)):
            bad.append(f"{path}: {a} != {b}")
    elif a != b:
        bad.append(f"{path}: {a!r} != {b!r}")


def main():
    failed = 0
    for rel in sys.argv[1:]:
        old = subprocess.run(["git", "show", f"HEAD:{rel}"], cwd=REPO, capture_output=True, text=True, check=True,
                             encoding="utf-8").stdout
        new = (REPO / rel).read_text(encoding="utf-8")
        bad, n = [], 0
        if rel.endswith(".json"):
            cmp_json(json.loads(new), json.loads(old), "$", bad)
        else:
            ro, rn = list(csv.reader(io.StringIO(old))), list(csv.reader(io.StringIO(new)))
            if len(ro) != len(rn) or ro[0] != rn[0]:
                bad.append(f"rows {len(rn)} vs {len(ro)} or header differs")
            for i, (x, y) in enumerate(zip(rn[1:], ro[1:]), 1):
                for c, (p, q) in enumerate(zip(x, y)):
                    fp, fq = num(p), num(q)
                    n += 1
                    if (fp is None or fq is None) and p != q or (fp is not None and fq is not None and not close(fp, fq)):
                        bad.append(f"row {i} {ro[0][c]}: {p} != {q}")
        print(f"{'OK  ' if not bad else 'FAIL'} {rel}" + (f" ({n} cells)" if n else ""))
        for b in bad[:20]:
            print("     ", b)
        failed += bool(bad)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
