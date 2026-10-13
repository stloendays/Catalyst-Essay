"""The staged converter (converter.py, run_staged.py, boundary.py) is the same calculation under NH3-FINAL-1.1 and 1.2.

The converter takes from the harness only economic controls and cost functions (compression, refrigeration, converter
vessel and pressure premium, NH3 vapour pressure, plant output); its equilibrium, rates and per-pass conversion are its
own (Gillespie-Beattie Ka, Newton-Cooper fugacities: kinetics.py), and it never uses the harness process states or F_CAL.
NH3-FINAL-1.2 changes only the thermo block (loop equilibrium, microkinetic activities) and F_CAL. This script checks:

  1. the controls set by NH3Harness._init_controls from the 1.1 and the 1.2 manifest are equal except F_CAL;
  2. the source of every harness function the converter calls is the same in the 1.1 and the 1.2 core;
  3. converter.evaluate is bit-identical with either harness for every design of the committed design library and
     arrangement table (re-evaluated at their printed x) and for random designs of every pattern, loop and bed mode;
  4. complete optimisations (differential evolution + Nelder-Mead, as in run_staged.py) return bit-identical results;
  4b. with the 1.1 harness every committed library and arrangement design re-evaluates to its committed cost (within the
     rounding of the printed x; NH3-FINAL-1.1 reproduction without the 8-CPU-hour rerun of run_staged.py);
  5. the run_staged.py outputs in nh3_1_2/ are byte copies of the committed 1.1 outputs (written with --write).

    python staged_invariance_1_2.py            # checks 1-5 (5 only if nh3_1_2/ holds the files)
    python staged_invariance_1_2.py --write    # checks 1-4, copies the five run_staged.py outputs to nh3_1_2/ and writes
                                               # nh3_1_2/staged_invariance.json
Then  NH3_MODEL=1.2 python boundary.py  rebuilds the decision maps of 1.2 from nh3_1_2/design_library.csv.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import inspect
import json
import shutil
import sys
from pathlib import Path

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))
CORES = {"1.1": REPO / "provenance" / "discover_v1" / "source_harness" / "harness_core.py",
         "1.2": REPO / "provenance" / "nh3_final_1_2" / "source_harness" / "harness_core.py"}
MANIFESTS = {"1.1": REPO / "provenance" / "discover_v1" / "source_harness" / "outputs" / "nh3_final_20260905T134204Z"
             / "manifest_resolved.yaml",
             "1.2": REPO / "provenance" / "nh3_final_1_2" / "source_harness" / "outputs" / "nh3_final_1_2_20261013"
             / "manifest_resolved.yaml"}
USED = ("_init_controls", "psat_nh3_bar", "refriger_cost", "turton_cp0", "compressor_capex_USD_t",
        "vessel_pressure_premium")
EXPECTED_DIFF = {"F_CAL"}                    # the only control 1.2 changes; the converter never reads it
COMMITTED_TOL = 1e-3                         # USD/t; rounding of the printed x (check_regression.py allows 0.02)
STAGED_FILES = ("arrangements.csv", "sensitivities.csv", "design_library.csv", "envelope_checks.csv", "summary.json")


def _load(version):
    spec = importlib.util.spec_from_file_location(f"harness_core_{version.replace('.', '_')}", CORES[version])
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def controls(version, mod=None):
    mod = mod or _load(version)
    h = mod.NH3Harness.__new__(mod.NH3Harness)
    h.cfg = yaml.safe_load(MANIFESTS[version].read_text(encoding="utf-8"))
    h._init_controls()
    return mod, h


def _same(a, b):
    if isinstance(a, np.ndarray) or isinstance(b, np.ndarray):
        return np.array_equal(np.asarray(a), np.asarray(b))
    return a == b


def compare_controls():
    m11, h11 = controls("1.1")
    m12, h12 = controls("1.2")
    v11 = {k: v for k, v in vars(h11).items() if k != "cfg"}
    v12 = {k: v for k, v in vars(h12).items() if k != "cfg"}
    diff = sorted(k for k in set(v11) | set(v12) if k not in v11 or k not in v12 or not _same(v11[k], v12[k]))
    src = {name: inspect.getsource(getattr(m11.NH3Harness, name)) == inspect.getsource(getattr(m12.NH3Harness, name))
           for name in USED}
    consts = {c: getattr(m11, c) == getattr(m12, c) for c in ("MW_NH3_KG_MOL", "R", "T_COMP") if hasattr(m11, c)}
    return h11, h12, dict(n_controls=len(v11), differing_controls=diff,
                          F_CAL={"1.1": float(h11.F_CAL), "1.2": float(h12.F_CAL)},
                          same_function_source=src, same_module_constants=consts)


def _designs():
    """(x, pattern, loop, econ, mode) from the committed design library and arrangement table, plus random designs."""
    import converter as C
    import run_staged as R
    out = []
    with (HERE / "design_library.csv").open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            out.append(([float(v) for v in r["x"].split(";")], R.PATTERNS[r["pattern"]],
                        C.Loop(float(r["P_bar"]), float(r["Tsep_C"]), float(r["inerts"])),
                        C.Econ(c_Ru=float(r["c_Ru"]), c_Fe=float(r["c_Fe"])), r["mode"]))
    with (HERE / "arrangements.csv").open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            out.append(([float(v) for v in r["x"].split(";")], R.PATTERNS[r["pattern"]],
                        C.Loop(float(r["P_bar"]), float(r["Tsep_C"]), float(r["inerts"])),
                        C.Econ(**R.ECON[r["economics"]]), r["mode"]))
    rng = np.random.default_rng(20261013)
    loops = [C.Loop(P, Ts) for P, Ts in R.LIBRARY_LOOPS] + [C.Loop(90.0, -20.0, 0.0)]
    econs = [C.Econ(**e) for e in R.ECON.values()]
    for name, pat in R.PATTERNS.items():
        for mode in ("adiabatic", "isothermal"):
            b = np.array(C.bounds(pat, mode))
            for _ in range(12):
                x = b[:, 0] + rng.random(len(b)) * (b[:, 1] - b[:, 0])
                out.append((list(x), pat, loops[rng.integers(len(loops))], econs[rng.integers(len(econs))], mode))
    return out


def compare_evaluate(h11, h12):
    import converter as C
    keep = C.H
    designs = _designs()
    res = {}
    try:
        for tag, h in (("1.1", h11), ("1.2", h12)):
            C.H = h
            res[tag] = np.array([C.evaluate(x, pat, loop, econ, mode) for x, pat, loop, econ, mode in designs])
    finally:
        C.H = keep
    a, b = res["1.1"], res["1.2"]
    same = (a == b) | (np.isnan(a) & np.isnan(b))
    diff = np.abs(a[~same] - b[~same])
    return dict(n_designs=len(designs), n_bit_identical=int(same.sum()), n_finite=int(np.isfinite(a).sum()),
                max_abs_diff=float(diff.max()) if diff.size else 0.0)


def committed_costs(h11):
    """NH3-FINAL-1.1 reproduction of the committed run_staged.py outputs without the 8-CPU-hour rerun: every design of
    design_library.csv and arrangements.csv re-evaluated with the 1.1 harness at its printed x (5 decimals) against its
    printed cost (6 decimals). A few optima sit on a discontinuity of the cost (an isothermal bed exactly at the catalyst's
    maximum temperature, where its attainable extent drops to zero; the recycle-compressor CAPEX step; the 90 m3 cap), so
    the rounding of x can move them across it; those are re-evaluated at the corners of the printing interval
    (each coordinate +-4.9e-6) and the closest cost is reported."""
    import itertools
    import converter as C
    import run_staged as R
    keep = C.H
    direct, best, n_step = [], [], 0
    try:
        C.H = h11
        for name, econ in (("design_library.csv", lambda r: C.Econ(c_Ru=float(r["c_Ru"]), c_Fe=float(r["c_Fe"]))),
                           ("arrangements.csv", lambda r: C.Econ(**R.ECON[r["economics"]]))):
            with (HERE / name).open(encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    x = np.array([float(t) for t in r["x"].split(";")])
                    args = (R.PATTERNS[r["pattern"]], C.Loop(float(r["P_bar"]), float(r["Tsep_C"]), float(r["inerts"])),
                            econ(r), r["mode"])
                    ref = float(r["cost"])
                    d = abs(C.evaluate(x, *args, detail=True)[0] - ref)
                    direct.append(d)
                    if not d < 1e-4:
                        n_step += 1
                        for s in itertools.product((-4.9e-6, 0.0, 4.9e-6), repeat=len(x)):
                            d = min(d, abs(C.evaluate(x + np.array(s), *args, detail=True)[0] - ref))
                    best.append(d)
    finally:
        C.H = keep
    direct, best = np.array(direct), np.array(best)
    return dict(n_designs=int(direct.size), n_within_1e_4_at_printed_x=int((direct < 1e-4).sum()),
                median_abs_diff_at_printed_x_USD_t=float(np.median(direct)),
                n_on_discontinuity=n_step, max_abs_diff_USD_t=float(best.max()))


def compare_solve(h11, h12):
    import converter as C
    import run_staged as R
    jobs = [dict(loop=R.kaap(), econ=R.ECON[R.B95], pattern="FRR", mode="adiabatic", tag=dict(check="KAAP FRR")),
            dict(loop=R.kaap(P_bar=150.0, Tsep_C=-5.0), econ=R.ECON[R.D12], pattern="FFR", mode="isothermal",
                 tag=dict(check="150 bar FFR isothermal"))]
    keep = C.H
    out = []
    try:
        for job in jobs:
            rec = {}
            for tag, h in (("1.1", h11), ("1.2", h12)):
                C.H = h
                r = R.solve(job)
                rec[tag] = (r["cost"], r["x"], r["V_m3"], r["Ru_volume_fraction"])
            out.append(dict(job=job["tag"]["check"], cost=rec["1.1"][0], bit_identical=rec["1.1"] == rec["1.2"]))
    finally:
        C.H = keep
    return out


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    h11, h12, ctl = compare_controls()
    print("controls:", json.dumps(ctl))
    ev = compare_evaluate(h11, h12)
    print("evaluate:", json.dumps(ev))
    so = compare_solve(h11, h12)
    print("solve:", json.dumps(so))
    cc = committed_costs(h11)
    print("committed 1.1 costs at printed x:", json.dumps(cc))
    ok = (set(ctl["differing_controls"]) == EXPECTED_DIFF and all(ctl["same_function_source"].values())
          and all(ctl["same_module_constants"].values()) and ev["n_bit_identical"] == ev["n_designs"]
          and all(s["bit_identical"] for s in so) and cc["max_abs_diff_USD_t"] < COMMITTED_TOL)
    if not ok:
        print("INVARIANCE FAILED")
        sys.exit(1)
    dst = HERE / "nh3_1_2"
    if a.write:
        dst.mkdir(exist_ok=True)
        for name in STAGED_FILES:
            shutil.copyfile(HERE / name, dst / name)
    copies = {name: dict(sha256=sha(HERE / name), identical=(dst / name).exists() and sha(dst / name) == sha(HERE / name))
              for name in STAGED_FILES}
    print("copies:", json.dumps({k: v["identical"] for k, v in copies.items()}))
    if a.write:
        (dst / "staged_invariance.json").write_text(json.dumps(dict(
            statement="converter.py / run_staged.py / boundary.py give bit-identical results under NH3-FINAL-1.1 and "
                      "1.2; the run_staged.py outputs in this folder are byte copies of the committed 1.1 outputs",
            controls=ctl, evaluate=ev, solve=so, committed_1_1_costs_at_printed_x=cc, copies=copies), indent=1) + "\n", encoding="utf-8")
    elif any((dst / n).exists() for n in STAGED_FILES) and not all(v["identical"] for v in copies.values()):
        print("nh3_1_2/ copies differ from the committed 1.1 outputs")
        sys.exit(1)
    print("staged converter invariant under NH3-FINAL-1.2")


if __name__ == "__main__":
    main()
