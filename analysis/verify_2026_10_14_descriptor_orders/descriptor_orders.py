"""Apparent reaction orders of the descriptor microkinetics (Condition.logtof) for Fe and Ru, NH3-FINAL-1.1 and 1.2.

Condition of the main text: 90 bar, 400 C, H2/N2 = 3, 2 % NH3 (far from equilibrium). Order in species i =
d log10 TOF / d log10 p_i with the other partial pressures fixed (central difference, +-0.01 in log10 p_i). Under 1.2 the
gas activities carry Newton-Cooper fugacity coefficients evaluated at the perturbed total pressure, so the orders are with
respect to partial pressure, as the measured orders they are compared with. Same definition as
analysis/verify_2026_10_12_hybrid_bed/hybrid_bed_feasibility.py (forward difference 0.02 there; reproduced below).

    python descriptor_orders.py      -> descriptor_orders.json
"""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "analysis"))
T_K, P, Y_NH3, D = 673.15, 90.0, 0.02, 0.01


def orders_for(version):
    os.environ["NH3_MODEL"] = version
    for m in [k for k in sys.modules if k in ("nh3_model", "harness_core")]:
        del sys.modules[m]
    import nh3_model as NM
    hc = NM.core()
    h = NM.harness()
    yN, yH = (1 - Y_NH3) * 0.25, (1 - Y_NH3) * 0.75
    p0 = [P * yN, P * yH, P * Y_NH3]
    out = {}
    for metal in ("Fe", "Ru"):
        e = hc.EN0_CANON[metal]
        lt = lambda p: h.ctx.condition(T_K, *p).logtof(e)
        o = {}
        for i, sp in enumerate(("N2", "H2", "NH3")):
            up, dn = list(p0), list(p0)
            up[i] *= 10 ** D
            dn[i] /= 10 ** D
            o[sp] = (lt(up) - lt(dn)) / (2 * D)
        fwd = {}
        for i, sp in enumerate(("N2", "H2", "NH3")):  # forward 0.02, the definition of the 2026-10-12 hybrid-bed check
            up = list(p0)
            up[i] *= 10 ** 0.02
            fwd[sp] = (lt(up) - lt(p0)) / 0.02
        out[metal] = dict(central=o, forward_0p02=fwd)
    return dict(model=NM.LABEL, run=NM.RUNS[version], states=h.NSTATE, orders=out)


def main():
    res = {"condition": dict(T_C=400.0, P_bar=P, y_NH3=Y_NH3, H2_N2=3.0), "1.1": orders_for("1.1"), "1.2": orders_for("1.2")}
    (HERE / "descriptor_orders.json").write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8")
    for v in ("1.1", "1.2"):
        for m in ("Fe", "Ru"):
            o = res[v]["orders"][m]["central"]
            print(v, m, " ".join(f"{k} {x:+.2f}" for k, x in o.items()))


if __name__ == "__main__":
    main()
