#!/usr/bin/env python3
"""Compare a fresh run (e.g. CI) with the committed outputs (PREREGISTRATION.md, 'Outputs').

Fails if a reported cost moves by more than 0.01 USD/t (T1: 1e-9), a crossover or boundary rate by more than
0.05 %-point, or a winner / ranking / verdict changes.
    python check_regression.py --fresh <dir> [--committed outputs]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import common

TOL, TOL_T1, TOL_RATE = 0.01, 1e-9, 0.0005


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--fresh", required=True, type=Path)
    p.add_argument("--committed", type=Path, default=common.HERE / "outputs")
    a = p.parse_args()
    A, B = common.load(a.committed / "summary.json"), common.load(a.fresh / "summary.json")
    bad = []

    def num(path, x, y, tol):
        if x is None or y is None:
            if x != y:
                bad.append(f"{path}: {x} vs {y}")
        elif abs(x - y) > tol:
            bad.append(f"{path}: {x} vs {y} (|d| {abs(x - y):.3g} > {tol})")

    def same(path, x, y):
        if x != y:
            bad.append(f"{path}: {x} vs {y}")

    for k in A["T1"]:
        for m in ("Fe", "Ru", "Os", "Ru_minus_Fe"):
            num(f"T1/{k}/{m}", A["T1"][k][m], B["T1"][k][m], TOL_T1)
        num(f"T1/{k}/parity", A["T1"][k]["Ru_parity_multiple"], B["T1"][k]["Ru_parity_multiple"], 1e-6)
        same(f"T1/{k}/ranking", A["T1"][k]["ranking"], B["T1"][k]["ranking"])
    same("T1_gate", A["T1_gate"], B["T1_gate"])
    for k in A["T2"]:
        for m in ("Fe", "Ru", "Ru_minus_Fe"):
            num(f"T2/{k}/{m}", A["T2"][k][m], B["T2"][k][m], TOL)
        same(f"T2/{k}/verdict", A["T2"][k]["crossover_verdict"], B["T2"][k]["crossover_verdict"])
        if len(A["T2"][k]["crossover"]) != len(B["T2"][k]["crossover"]):
            bad.append(f"T2/{k}/crossover count")
        else:
            for i, (x, y) in enumerate(zip(A["T2"][k]["crossover"], B["T2"][k]["crossover"])):
                num(f"T2/{k}/crossover{i}", x, y, TOL_RATE)
    same("T3/gates", A["T3"]["gates"], B["T3"]["gates"])
    for k in A["T3"]["levels"]:
        num(f"T3/{k}", A["T3"]["levels"][k], B["T3"]["levels"][k], TOL)
    for k in A["T4"]["per_rate"]:
        x, y = A["T4"]["per_rate"][k], B["T4"]["per_rate"][k]
        same(f"T4/{k}/winner", (x["winner"], x["pattern"]), (y["winner"], y["pattern"]))
        for m in ("USD_t", "all_Fe", "Fe_first", "all_Ru"):
            num(f"T4/{k}/{m}", x[m], y[m], TOL)
    for b, segs in A["T4"]["envelope_boundaries"].items():
        s2 = B["T4"]["envelope_boundaries"][b]
        same(f"T4/{b}/winners", [s["winner"] for s in segs], [s["winner"] for s in s2])
        if len(segs) == len(s2):
            for s, t in zip(segs, s2):
                num(f"T4/{b}/{s['winner']}/to", s["to_pct"] / 100, t["to_pct"] / 100, TOL_RATE)
    num("T5/delta_GJ_t", A["T5"]["delta_GJ_t"], B["T5"]["delta_GJ_t"], 1e-3)
    same("upstream_gates", A["upstream_gates"], B["upstream_gates"])
    if bad:
        print("REGRESSION FAIL")
        for line in bad:
            print("  " + line)
        sys.exit(1)
    print("REGRESSION PASS: fresh run reproduces every committed reported quantity within tolerance")


if __name__ == "__main__":
    main()
