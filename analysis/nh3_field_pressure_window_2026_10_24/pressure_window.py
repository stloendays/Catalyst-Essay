"""Ammonia within-paper comparisons (12/44, descriptor kinetics) with each catalyst's plant pressure held near the
pressure at which its rate was measured.

The descriptor mapping calibrates each catalyst at its laboratory T and P (effective descriptor E_eff plus residual
activity factor), then lets the plant optimum range over 10-1,000 bar. Descriptor kinetics give Ru an apparent H2
order of about +2.4 against a measured +0.3, so a pressure range far above the calibration point may favour Ru. Here
the plant states are restricted to P <= max(10 bar, k x P_lab) (10 bar is the lowest state of the process library) for
k = 1, 2, 5 and 10, and the within-paper count is redone. Nothing else changes: E_eff and the residual activity are the
frozen values of candidates_printed.csv, and the plant cost is the same harness call (run_supported_chain.plant_cost).

Gate: with no pressure restriction every primary entry reproduces its frozen cost_USD_t (to 1e-4; E_eff is stored to
5 significant figures), and the count is 12/44.

    set NH3_MODEL=1.2
    python pressure_window.py      -> summary.json, candidates_pressure_window.csv, group_metrics_<variant>.csv
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

assert os.environ.get("NH3_MODEL") == "1.2", "run with NH3_MODEL=1.2"
HERE = Path(__file__).resolve().parent
AN = HERE.parent
sys.path.insert(0, str(AN / "nh3_field_2026_10_06"))
_argv, sys.argv = sys.argv, sys.argv[:1]
import run_field_chain as F  # noqa: E402
sys.argv = _argv
SC, hc = F.SC, F.hc

SRC = AN / "nh3_field_expansion_2026_10_12" / "nh3_1_2" / "runs" / "pooled_vf_screen" / "candidates_printed.csv"
FACTORS = (None, 1.0, 2.0, 5.0, 10.0)
P_FLOOR = 10.0

_PCAP = None
_orig_eval = hc.NH3Harness.eval_scenario


def _eval_capped(self, metal, base_logvec, alpha=1.0, price=None, life_y=None, recovery=None):
    """eval_scenario with the states restricted to P <= _PCAP (bar); identical arithmetic otherwise."""
    if _PCAP is None:
        return _orig_eval(self, metal, base_logvec, alpha, price, life_y, recovery)
    total, V, metal_cost, reactor = self.cost_arrays(metal, base_logvec, price=price, life_y=life_y, recovery=recovery,
                                                     alpha=alpha)
    mask = (V <= self.V_CAP) & (self.state_P <= _PCAP + 1e-9)
    if not np.any(mask):
        raise RuntimeError("No feasible state")
    i = int(np.argmin(np.where(mask, total, np.inf)))
    return {"total_cost": float(total[i]), "V_m3": float(V[i]), "T_C": float(self.state_T[i]),
            "P_bar": float(self.state_P[i])}


hc.NH3Harness.eval_scenario = _eval_capped


def cost(h, resp, r, pcap):
    global _PCAP
    _PCAP = pcap
    fused = bool(r.fused)
    w = 0.7151 if fused else float(r.metal_wt_pct) / 100.0
    bed = 2500.0 if fused else SC.BED_SUPPORTED
    best = SC.plant_cost(h, resp, r.metal, 10.0 ** float(r.log10_alpha_res), w, bed, E=float(r.E_eff_eV))
    _PCAP = None
    return (np.nan, np.nan) if best is None else (best["total_cost"], best["P_bar"])


def main():
    F._init()
    h, resp = F._H, F._RESP
    c = pd.read_csv(SRC, keep_default_na=False, na_values=[""])
    c["fused"] = c.fused.astype(str).str.lower().isin(("true", "1"))
    prim = c[c.status.str.startswith("primary") & c.cost_USD_t.notna()].copy()
    prim["P_lab_bar"] = prim.P_MPa * 10.0

    out, gms = {}, {}
    for k in FACTORS:
        name = "unrestricted" if k is None else f"P_le_{k:g}x_lab"
        cc, pp = [], []
        for r in prim.itertuples():
            pcap = None if k is None else max(P_FLOOR, k * r.P_lab_bar)
            a, b = cost(h, resp, r, pcap)
            cc.append(a)
            pp.append(b)
        prim[f"cost_{name}"], prim[f"P_opt_{name}"] = cc, pp
        gm, s = F.aggregate(prim, cost_col=f"cost_{name}", label=name, boot=True)
        s["entries_infeasible"] = int(np.isnan(cc).sum())
        s["top1_mismatch_regret_gt_5pct"] = int((gm.top1_mismatch & (gm.regret > 0.05)).sum())
        gm.to_csv(HERE / f"group_metrics_{name}.csv", index=False)
        gms[name] = gm
        out[name] = s
        print(name, s["groups"], s["top1_mismatch_groups"], s["top1_mismatch_regret_gt_5pct"],
              s.get("mismatch_kinds", {}).keys(), "infeasible", s["entries_infeasible"], flush=True)

    d = (prim.cost_unrestricted - prim.cost_USD_t).abs() / prim.cost_USD_t
    gate = dict(max_rel_dev_from_frozen=float(d.max()), groups=out["unrestricted"]["groups"],
                mismatch=out["unrestricted"]["top1_mismatch_groups"])
    gate["ok"] = gate["max_rel_dev_from_frozen"] < 1e-4 and (gate["groups"], gate["mismatch"]) == (44, 12)
    assert gate["ok"], gate

    base = gms["unrestricted"].set_index("group")
    trans = {}
    for name, gm in gms.items():
        if name == "unrestricted":
            continue
        j = base[["top1_mismatch", "mismatch_kind"]].join(gm.set_index("group")[["top1_mismatch", "mismatch_kind"]],
                                                           lsuffix="_free", rsuffix="_window", how="outer")
        trans[name] = dict(
            kept=int(((j.top1_mismatch_free == True) & (j.top1_mismatch_window == True)).sum()),  # noqa: E712
            lost=int(((j.top1_mismatch_free == True) & (j.top1_mismatch_window != True)).sum()),  # noqa: E712
            gained=int(((j.top1_mismatch_free != True) & (j.top1_mismatch_window == True)).sum()),  # noqa: E712
            groups_dropped=int(j.top1_mismatch_window.isna().sum()),
            unrestricted_mismatch_in_same_groups=int((j.top1_mismatch_free[j.top1_mismatch_window.notna()] == True).sum()))  # noqa: E712
    by_metal_P = prim.groupby("metal")[[f"P_opt_{n}" for n in out]].median().round(1).to_dict()
    summ = dict(gate=gate, P_floor_bar=P_FLOOR, variants=out, transitions_vs_unrestricted=trans,
                median_P_opt_by_metal=by_metal_P,
                P_lab_bar=prim.P_lab_bar.value_counts().sort_index().to_dict())
    (HERE / "summary.json").write_text(json.dumps(summ, indent=1, default=float) + "\n", encoding="utf-8")
    prim.to_csv(HERE / "candidates_pressure_window.csv", index=False)


if __name__ == "__main__":
    main()
