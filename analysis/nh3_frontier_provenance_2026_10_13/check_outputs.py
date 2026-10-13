"""Compare a rerun with the committed outputs.

    python check_outputs.py <committed_dir> <rerun_dir>

frontier_swap.json: every number within 1e-6 (deterministic array arithmetic).
staged_window.json: window edges within 0.2 %/y, savings within 0.02 USD/t, same optimal arrangement at the savings
points (optimiser noise of differential evolution is ~1e-3 USD/t).
"""
import json
import sys
from pathlib import Path


def walk(a, b, path, tol, bad):
    if isinstance(a, dict):
        for k in a:
            walk(a[k], b.get(k) if isinstance(b, dict) else None, f"{path}.{k}", tol, bad)
    elif isinstance(a, list):
        if not isinstance(b, list) or len(a) != len(b):
            bad.append((path, "length", a, b))
            return
        for k, (x, y) in enumerate(zip(a, b)):
            walk(x, y, f"{path}[{k}]", tol, bad)
    elif isinstance(a, (int, float)) and not isinstance(a, bool):
        if not isinstance(b, (int, float)) or abs(a - b) > tol:
            bad.append((path, a, b))
    elif a != b:
        bad.append((path, a, b))


def main():
    old, new = Path(sys.argv[1]), Path(sys.argv[2])
    bad = []
    walk(json.loads((old / "frontier_swap.json").read_text()), json.loads((new / "frontier_swap.json").read_text()),
         "frontier_swap", 1e-6, bad)
    a = json.loads((old / "staged_window.json").read_text())
    b = json.loads((new / "staged_window.json").read_text())
    for c, v in a["cases"].items():
        for kind in ("lower", "upper"):
            x, y = v["window_direct"][kind], b["cases"][c]["window_direct"][kind]
            if len(x) != len(y) or any(abs(p - q) > 0.002 for p, q in zip(x, y)):
                bad.append((f"{c} {kind} edge", x, y))
    for k, v in a["base_savings_vs_all_Fe"].items():
        w = b["base_savings_vs_all_Fe"][k]
        if abs(v["saving_best"] - w["saving_best"]) > 0.02 or v["best"] != w["best"]:
            bad.append((f"saving {k}", v, w))
    for x in bad[:50]:
        print("DIFF", x)
    print(f"{len(bad)} differences")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
