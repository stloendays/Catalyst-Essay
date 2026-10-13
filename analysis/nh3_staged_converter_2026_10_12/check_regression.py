"""Compare a fresh run with the committed outputs.

    python check_regression.py <committed_dir> <new_dir>
    NH3_MODEL=1.2: python check_regression.py <copy of nh3_1_2> nh3_1_2   (no validation_summary.json there: skipped)

Fails if an optimal cost moved by more than 0.02 USD/t (or 0.2 %), if the optimal arrangement of a case changed while
the two arrangements are more than 0.02 USD/t apart, or if a kinetic validation statistic moved by more than 1e-6.
"""
import csv
import json
import sys
from pathlib import Path

TOL = 0.02


def rows(p):
    with Path(p).open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    old, new = Path(sys.argv[1]), Path(sys.argv[2])
    bad = []
    if (old / "validation_summary.json").exists() or (new / "validation_summary.json").exists():
        vo = json.loads((old / "validation_summary.json").read_text(encoding="utf-8"))
        vn = json.loads((new / "validation_summary.json").read_text(encoding="utf-8"))
        for k in ("all_points_N2_basis", "H2_N2_3_points_N2_basis"):
            a, b = vo["Ru_C_Rossetti2006_Table2"][k]["mean_abs_rel_err"], vn["Ru_C_Rossetti2006_Table2"][k]["mean_abs_rel_err"]
            if abs(a - b) > 1e-6:
                bad.append(f"validation {k}: {a} -> {b}")
    ko = json.loads((old / "kinetics_swap.json").read_text(encoding="utf-8"))
    kn = json.loads((new / "kinetics_swap.json").read_text(encoding="utf-8"))
    if len(ko["variants"]) != len(kn["variants"]):
        bad.append(f"kinetics_swap: {len(ko['variants'])} vs {len(kn['variants'])} variants")
    for a, b in zip(ko["variants"], kn["variants"]):
        tag = (a["states"], a["sizing"], a["scale"])
        pairs = [("Fe", a["Fe"]["cost"], b["Fe"]["cost"]), ("Ru_benchmark", a["Ru_benchmark"]["cost"], b["Ru_benchmark"]["cost"]),
                 ("alpha", a["Ru_activity_multiple_for_parity"], b["Ru_activity_multiple_for_parity"])]
        pairs += [(k, a["Ru_C_supported"][k]["Ru_C_global"]["cost"], b["Ru_C_supported"][k]["Ru_C_global"]["cost"])
                  for k in a["Ru_C_supported"]]
        for k, x, y in pairs:
            if abs(x - y) > 1e-4 * max(1.0, abs(x)):
                bad.append(f"kinetics_swap {tag} {k}: {x} -> {y}")
    arr = {"FFF": "all-Fe", "RRR": "all-Ru/C", "FFR": "Fe-first", "FRR": "Fe-first", "RFF": "Ru-first", "RRF": "Ru-first",
           "FFFF": "all-Fe", "RRRR": "all-Ru/C", "FRRR": "Fe-first", "FFRR": "Fe-first", "FFFR": "Fe-first"}
    for name, keys in (("arrangements.csv", ("loop", "economics", "mode")), ("sensitivities.csv", ("case", "economics"))):
        def best(path):
            out = {}
            for r in rows(path):
                k = tuple(r[x] for x in keys) + (arr[r["pattern"]],)
                out[k] = min(out.get(k, 1e9), float(r["cost"]))
            return out
        o, n = best(old / name), best(new / name)
        for k, v in o.items():
            if k not in n:
                bad.append(f"{name} missing {k}")
            elif abs(n[k] - v) > max(TOL, 0.002 * v):
                bad.append(f"{name} {k}: {v:.4f} -> {n[k]:.4f}")
        cases = {}
        for k, v in o.items():
            cases.setdefault(k[:-1], {})[k[-1]] = (v, n.get(k, 1e9))
        for case, d in cases.items():
            bo = min(d, key=lambda p: d[p][0])
            bn = min(d, key=lambda p: d[p][1])
            if bo != bn and abs(d[bo][1] - d[bn][1]) > TOL:
                bad.append(f"{name} {case}: best {bo} -> {bn}")
    for name in ("boundary_price_financing.csv", "boundary_pressure.csv"):
        o, n = rows(old / name), rows(new / name)
        flips = sum(1 for a, b in zip(o, n) if a["best"] != b["best"] and abs(float(a["staged_minus_Fe"])) > TOL)
        if len(o) != len(n) or flips:
            bad.append(f"{name}: {len(o)} vs {len(n)} rows, {flips} decision changes away from the boundary")
    if bad:
        print("REGRESSION\n" + "\n".join(bad))
        sys.exit(1)
    print("regression check passed")


if __name__ == "__main__":
    main()
