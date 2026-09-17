"""Per-pressure minimum feasible cost for Fe/Ru/Os on an extended grid (read-only; uses the harness class)."""
import sys, json, csv, numpy as np, yaml
from pathlib import Path
ROOT = Path(r"D:/论文-AI4S/Catalyst_Economic_Leverage_Automation_Harness_v0.1")
sys.path.insert(0, str(ROOT))
from harness_core import NH3Harness, EN0_CANON
cfg = yaml.safe_load((ROOT / sys.argv[1]).read_text(encoding="utf-8"))
h = NH3Harness(cfg, ROOT)
print("NSTATE", h.NSTATE, "P grid", h.P_GRID_BAR[0], "..", h.P_GRID_BAR[-1])
rows = []
for m in ("Fe", "Ru", "Os"):
    logvec = h.frozen_state_logtof(EN0_CANON[m]); total, V, metal, reactor = h.cost_arrays(m, logvec); feas = V <= h.V_CAP
    for P in h.P_GRID_BAR:
        idx = np.where((h.state_P == P) & feas)[0]
        if len(idx) == 0: continue
        i = idx[int(np.argmin(total[idx]))]
        rows.append(dict(metal=m, P_bar=float(P), cost=float(total[i]), T_C=float(h.state_T[i]), Tsep_C=float(h.state_Tsep[i]), V_m3=float(V[i]),
                         metal_cost=float(metal[i]), reactor=float(reactor[i]), fresh_comp=float(h.state_fresh[i]), recycle_comp=float(h.state_reccomp[i]), refrig=float(h.state_refrig[i]), logTOF=float(logvec[i])))
out = Path(sys.argv[2]); 
with out.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print("wrote", out)
show = {100,150,200,250,300,350,400,450,500,600,700,800,900,1000}
for m in ("Fe","Ru","Os"):
    print(f"--- {m}: P_bar | cost | T | Tsep | V_m3 | metal | reactor | fresh | recyc | refrig")
    best = min((r for r in rows if r["metal"]==m), key=lambda r: r["cost"])
    for r in rows:
        if r["metal"]==m and r["P_bar"] in show:
            print(f"{r['P_bar']:6.0f} | {r['cost']:9.4f} | {r['T_C']:4.0f} | {r['Tsep_C']:4.0f} | {r['V_m3']:8.4f} | {r['metal_cost']:.4f} | {r['reactor']:.4f} | {r['fresh_comp']:.4f} | {r['recycle_comp']:.4f} | {r['refrig']:.4f}")
    print(f"   global min for {m}: {best['cost']:.6f} USD/t at P={best['P_bar']:.0f} T={best['T_C']:.0f} Tsep={best['Tsep_C']:.0f}")
