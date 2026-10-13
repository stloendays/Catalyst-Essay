"""Ru metal-price sweep with full process reoptimization, for the selected NH3 model (NH3_MODEL=1.1|1.2).

The certified direct-activity/lifecycle target region (build_certified_inner_surface.py) reuses only the process
states visited by this sweep, and its alpha = 1 anchor is the sweep's Fe-Ru parity price. For NH3-FINAL-1.1 the sweep
is figures/composite/fig2/fig2_ru_price_sweep.csv (written by figures/composite/fig2/fig2_model.py). This file
computes the same sweep on the same definition (same price grid, 90 m3 bed cap, log-price bisection for parity, same
columns) for either model, so the 1.2 target region does not depend on the Fig. 2 port:

    NH3_MODEL=1.1  recompute and compare byte-for-byte with figures/composite/fig2/fig2_ru_price_sweep.csv (no write)
    NH3_MODEL=1.2  write nh3_1_2/ru_price_sweep.csv; if figures/composite/fig2/nh3_1_2/fig2_ru_price_sweep.csv exists,
                   check that it is identical

Only the Ru and Fe state vectors at their canonical descriptors are evaluated (two grid points per state, as in
NH3Harness.frozen_state_logtof); the response surface is not read and never rebuilt.

    python ru_price_sweep.py [--out FILE]
"""
from __future__ import annotations

import argparse
import csv
import io
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "analysis"))
import nh3_model as NM  # noqa: E402

POOLS = ("metal_cost", "reactor_base", "vessel_pressure_premium", "fresh_comp",
         "recycle_comp", "refrigeration", "compressor_capex")
FIELDS = ["price_USD_kg", "cost", "T_C", "P_bar", "Tsep_C", "V_m3", *POOLS]
FIG2_11 = REPO / "figures/composite/fig2/fig2_ru_price_sweep.csv"
FIG2_12 = REPO / "figures/composite/fig2/nh3_1_2/fig2_ru_price_sweep.csv"


def compute():
    """Rows of the sweep (last row: Fe-Ru parity price), exactly as fig2_model.py builds them."""
    hc = NM.core()
    A = NM.anchors()
    h = NM.harness()
    if h.NSTATE != A["NSTATE"]:
        raise SystemExit(f"process-state count drift: {h.NSTATE} vs {A['NSTATE']}")
    PRICE = hc.PRICE
    logvec = {m: h.frozen_state_logtof(hc.EN0_CANON[m]) for m in ("Fe", "Ru")}

    def optimum(metal, price=None):
        total, V, metal_cost, reactor = h.cost_arrays(metal, logvec[metal], price=price)
        ok = V <= h.V_CAP
        if not ok.any():
            return None
        i = int(np.argmin(np.where(ok, total, np.inf)))
        row = dict(cost=float(total[i]), T_C=float(h.state_T[i]), P_bar=float(h.state_P[i]),
                   Tsep_C=float(h.state_Tsep[i]), V_m3=float(V[i]))
        row.update(h.cost_breakdown_at(metal, V, metal_cost, reactor, i))
        return row

    # the selected run's optima reproduce before anything is written
    for m in ("Fe", "Ru"):
        o = optimum(m)
        if abs(o["cost"] - A[m]) > 1e-9 or (o["T_C"], o["P_bar"], o["Tsep_C"]) != tuple(A[m + "_optimum"]):
            raise SystemExit(f"{m} optimum does not reproduce {A['run']}: {o} vs {A[m]} {A[m + '_optimum']}")

    fe_cost = A["Fe"]
    prices = sorted(set(np.round(np.logspace(0, math.log10(3e5), 241), 6).tolist() + [PRICE["Fe"], PRICE["Ru"]]))
    sweep = [dict(price_USD_kg=p, **optimum("Ru", p)) for p in prices]
    costs = np.array([r["cost"] for r in sweep])
    assert np.all(np.diff(costs) >= -1e-12), "Ru optimum is not monotone in its price"
    lo, hi = math.log10(PRICE["Fe"]), math.log10(PRICE["Ru"])
    for _ in range(80):  # bisection on log price for Ru = Fe
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if optimum("Ru", 10.0 ** mid)["cost"] < fe_cost else (lo, mid)
    p_star = 10.0 ** hi
    sweep.append(dict(price_USD_kg=p_star, **optimum("Ru", p_star)))
    return sweep


def lf(b: bytes) -> bytes:
    return b.replace(b"\r\n", b"\n")


def to_text(rows) -> str:
    buf = io.StringIO(newline="")
    w = csv.DictWriter(buf, fieldnames=FIELDS, lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()
    rows = compute()
    text = to_text(rows)
    p = rows[-1]
    print(f"{NM.LABEL}: {len(rows) - 1} prices, {len({(r['T_C'], r['P_bar'], r['Tsep_C']) for r in rows})} distinct "
          f"states; Ru = Fe at {p['price_USD_kg']:.6f} USD/kg ({p['T_C']:.0f} C, {p['P_bar']:.0f} bar, "
          f"Tsep {p['Tsep_C']:.0f} C, V {p['V_m3']:.4f} m3)")
    out = args.out or (NM.out_dir(HERE) / "ru_price_sweep.csv" if NM.VERSION != "1.1" else None)
    if out is not None:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(text.encode("utf-8"))
        print("wrote", out)
    if NM.VERSION == "1.1":
        # the committed blob is LF; a Windows checkout with core.autocrlf may hold CRLF
        same = lf(FIG2_11.read_bytes()) == text.encode("utf-8")
        print("byte-identical to figures/composite/fig2/fig2_ru_price_sweep.csv:", same)
        if not same:
            raise SystemExit("1.1 sweep does not reproduce the committed Fig. 2 sweep")
    if NM.VERSION == "1.2" and FIG2_12.exists():
        same = lf(FIG2_12.read_bytes()) == text.encode("utf-8")
        print("identical to figures/composite/fig2/nh3_1_2/fig2_ru_price_sweep.csv:", same)
        if not same:
            raise SystemExit("1.2 sweep differs from the Fig. 2 1.2 sweep")


if __name__ == "__main__":
    main()
