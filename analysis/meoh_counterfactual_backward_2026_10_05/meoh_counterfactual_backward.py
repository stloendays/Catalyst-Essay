"""Methanol: counterfactual and backward design, the two steps the ammonia case already has.

Counterfactual (analogue of the ammonia equal-price test): remove the selectivity difference between states by
moving every state's CH4 selectivity into methanol (S_CH4 = 0, CO-like unchanged), re-solve the plant model at the
canonical 2 % purge and ask whether the space-time-yield ranking returns. A second counterfactual equalizes
conversion instead (all states at the mean X).

Backward design (analogue of alpha*): how much must the space-time-yield winner (1 wt% Re, 250 C) improve, one
property at a time, to become the economic optimum (cost <= 5 wt% Re, 200 C)? Properties: STY per g Re (multiplier),
single-pass CO2 conversion (absolute), CH4 selectivity (moved to methanol), CO-like selectivity (moved to methanol).
Each target is compared with what the same study measured for that catalyst family (Table 3/4 of Gothe et al.).

Inputs: workbook Candidate_Inputs (Table 3), engine data/meoh/meoh_d01_model.py; canonical cost parameters.
Outputs: counterfactual_ranks.csv, backward_targets.csv, summary.json in this folder.
"""
import csv
import json
import sys
from pathlib import Path

import numpy as np
import openpyxl
from scipy.optimize import brentq
from scipy.stats import kendalltau, spearmanr

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "data" / "meoh"))
import meoh_d01_model as M  # noqa: E402

wb = openpyxl.load_workbook(REPO / "data/meoh/MeOH_D01_ExplicitRecycleSeparationEconomics_v3.0.xlsx", data_only=True)
C = {}
for r in range(5, 9):
    v = [wb["Candidate_Inputs"].cell(r, j).value for j in range(1, 9)]
    C[v[0]] = dict(name=v[0], Re_wt=float(v[1]), T_C=v[2], STY=float(v[3]), X=float(v[4]), SMeOH=float(v[5]),
                   SCH4=float(v[6]), SCO=float(v[7]))
names = list(C)
UPW, ECW = "1 wt% Re | 250 C", "5 wt% Re | 200 C"


def cost(c):
    return float(M.cost(c)["cost_eur_t"])


def ranking(cands):
    cs = {n: cost(c) for n, c in cands.items()}
    up = [cands[n]["STY"] for n in names]
    econ = [-cs[n] for n in names]
    order = sorted(names, key=lambda n: cs[n])
    return cs, order, float(spearmanr(up, econ).statistic), float(kendalltau(up, econ).statistic)


rows = []
base_c, base_o, base_rho, base_tau = ranking(C)
assert abs(base_c[UPW] - 961.509497) < 1e-5 and base_o[0] == ECW
rows.append(dict(case="canonical (Table 3)", order=" > ".join(base_o), rho=base_rho, tau=base_tau,
                 **{"NPC_" + n: base_c[n] for n in names}))

# counterfactual 1: no CH4 anywhere (moved to methanol)
cf1 = {n: dict(c, SMeOH=c["SMeOH"] + c["SCH4"], SCH4=0.0) for n, c in C.items()}
c1, o1, r1, t1 = ranking(cf1)
rows.append(dict(case="CH4 selectivity removed (moved to MeOH)", order=" > ".join(o1), rho=r1, tau=t1,
                 **{"NPC_" + n: c1[n] for n in names}))
# counterfactual 2: equal conversion
xm = float(np.mean([c["X"] for c in C.values()]))
cf2 = {n: dict(c, X=xm) for n, c in C.items()}
c2, o2, r2, t2 = ranking(cf2)
rows.append(dict(case="conversion equalized (X = %.4f)" % xm, order=" > ".join(o2), rho=r2, tau=t2,
                 **{"NPC_" + n: c2[n] for n in names}))
# counterfactual 3: both
cf3 = {n: dict(c, X=xm, SMeOH=c["SMeOH"] + c["SCH4"], SCH4=0.0) for n, c in C.items()}
c3, o3, r3, t3 = ranking(cf3)
rows.append(dict(case="CH4 removed and conversion equalized", order=" > ".join(o3), rho=r3, tau=t3,
                 **{"NPC_" + n: c3[n] for n in names}))
with open(HERE / "counterfactual_ranks.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
    w.writeheader()
    w.writerows(rows)

# backward design for the STY winner
target = base_c[ECW]
u = C[UPW]


def gap_sty(m):
    return cost(dict(u, STY=u["STY"] * m)) - target


def gap_x(x):
    return cost(dict(u, X=x)) - target


bw = []
try:
    m_star = brentq(gap_sty, 1.0, 1e6)
except ValueError:
    m_star = float("inf")
c_inf = cost(dict(u, STY=u["STY"] * 1e9))
bw.append(dict(property="STY per g Re (multiplier)", current=u["STY"], required=m_star if np.isfinite(m_star) else "unreachable",
               note="cost at unlimited STY = %.2f EUR/t vs target %.2f" % (c_inf, target)))
x_star = brentq(gap_x, u["X"], 0.95)
bw.append(dict(property="single-pass CO2 conversion", current=u["X"], required=x_star,
               note="absolute; Table 3 range for the same catalysts 0.19-0.40"))
c_noch4 = cost(dict(u, SMeOH=u["SMeOH"] + u["SCH4"], SCH4=0.0))
c_noco = cost(dict(u, SMeOH=u["SMeOH"] + u["SCO"], SCO=0.0))
c_pure = cost(dict(u, SMeOH=1.0, SCH4=0.0, SCO=0.0))
bw.append(dict(property="CH4 selectivity -> 0 (to MeOH)", current=u["SCH4"], required="insufficient alone" if c_noch4 > target else 0.0,
               note="cost %.2f EUR/t" % c_noch4))
bw.append(dict(property="CO-like selectivity -> 0 (to MeOH)", current=u["SCO"], required="insufficient alone" if c_noco > target else 0.0,
               note="cost %.2f EUR/t" % c_noco))
bw.append(dict(property="100% MeOH selectivity", current=u["SMeOH"], required="insufficient alone" if c_pure > target else 1.0,
               note="cost %.2f EUR/t" % c_pure))


def gap_xs(x):
    return cost(dict(u, X=x, SMeOH=1.0, SCH4=0.0, SCO=0.0)) - target


if gap_xs(u["X"]) > 0:
    bw.append(dict(property="conversion at 100% MeOH selectivity", current=u["X"], required=brentq(gap_xs, u["X"], 0.95),
                   note="joint target"))


def gap_sch4_to_co(f):
    """Fraction f of the CO-like selectivity moved to methanol, CH4 removed."""
    return cost(dict(u, SMeOH=u["SMeOH"] + u["SCH4"] + f * u["SCO"], SCH4=0.0, SCO=(1 - f) * u["SCO"])) - target


if gap_sch4_to_co(0.0) > 0 > gap_sch4_to_co(1.0):
    f_star = brentq(gap_sch4_to_co, 0.0, 1.0)
    bw.append(dict(property="CH4 -> 0 and CO-like reduced", current=u["SCO"], required=(1 - f_star) * u["SCO"],
                   note="CO-like selectivity at parity with CH4 removed (absolute fraction)"))
with open(HERE / "backward_targets.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(bw[0]), lineterminator="\n")
    w.writeheader()
    w.writerows(bw)

summary = dict(target_EUR_t=target, upstream_winner=UPW, economic_winner=ECW, counterfactuals=rows, backward=bw)
json.dump(summary, open(HERE / "summary.json", "w", encoding="utf-8"), indent=1, default=str)
for r in rows:
    print("%-42s rho %+.2f tau %+.2f  %s" % (r["case"], r["rho"], r["tau"], r["order"]))
for b in bw:
    print("%-38s current %-6s required %-20s %s" % (b["property"], b["current"], b["required"], b["note"]))
