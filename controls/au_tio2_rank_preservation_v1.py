from __future__ import annotations

import csv
import math
import random
from pathlib import Path

OUT = Path("artifacts/au_tio2_rank_preservation_v1")
OUT.mkdir(parents=True, exist_ok=True)

DIAMETERS_NM = [2.0, 3.0, 4.0, 5.0, 6.0]
SEED = 20260907
N_DRAWS = 10000


def ranks(values, reverse=False):
    order = sorted(range(len(values)), key=lambda i: values[i], reverse=reverse)
    r = [0] * len(values)
    for rank, idx in enumerate(order, 1):
        r[idx] = rank
    return r


def pearson(x, y):
    mx = sum(x) / len(x)
    my = sum(y) / len(y)
    num = sum((a - mx) * (b - my) for a, b in zip(x, y))
    denx = math.sqrt(sum((a - mx) ** 2 for a in x))
    deny = math.sqrt(sum((b - my) ** 2 for b in y))
    return num / (denx * deny)


def spearman_from_rankings(activity, cost):
    # High activity is rank 1; low cost is rank 1.
    ra = ranks(activity, reverse=True)
    rc = ranks(cost, reverse=False)
    return pearson(ra, rc)


def kendall_tau_from_rankings(activity, cost):
    concordant = 0
    discordant = 0
    n = len(activity)
    for i in range(n):
        for j in range(i + 1, n):
            a = activity[i] - activity[j]
            # For preservation, higher activity should mean lower cost.
            c = cost[j] - cost[i]
            if a * c > 0:
                concordant += 1
            elif a * c < 0:
                discordant += 1
    return (concordant - discordant) / (concordant + discordant)


def pairwise_inversions(activity, cost):
    inv = 0
    n = len(activity)
    for i in range(n):
        for j in range(i + 1, n):
            if (activity[i] - activity[j]) * (cost[j] - cost[i]) < 0:
                inv += 1
    return inv


def compute_state(n_exp=1.7, m_exp=1.0, a=1.0, b=1.0, gamma=0.7, common=10.0):
    tof = [(d / 2.0) ** (-n_exp) for d in DIAMETERS_NM]
    dispersion = [(d / 2.0) ** (-m_exp) for d in DIAMETERS_NM]
    q_mass = [t * disp for t, disp in zip(tof, dispersion)]
    inventory = [1.0 / q for q in q_mass]
    cost = [common + a * m + b * (m ** gamma) for m in inventory]
    return tof, dispersion, q_mass, inventory, cost


def top_order(values, reverse=False, k=3):
    return [DIAMETERS_NM[i] for i in sorted(range(len(values)), key=lambda i: values[i], reverse=reverse)[:k]]


# Nominal frozen calculation.
tof, dispersion, q_mass, inventory, cost = compute_state()
rho = spearman_from_rankings(tof, cost)
tau = kendall_tau_from_rankings(tof, cost)
inversions = pairwise_inversions(tof, cost)
activity_order = top_order(tof, reverse=True, k=len(DIAMETERS_NM))
cost_order = top_order(cost, reverse=False, k=len(DIAMETERS_NM))
top3_activity = activity_order[:3]
top3_cost = cost_order[:3]

winner_preserved = activity_order[0] == cost_order[0]
top3_preserved = top3_activity == top3_cost

# Preregistered Monte Carlo: common-series physics uncertainty + positive economic coefficients.
rng = random.Random(SEED)
full_preserved = 0
mc_rows = []
for draw in range(N_DRAWS):
    n_exp = max(0.05, rng.gauss(1.7, 0.2))
    m_exp = rng.uniform(0.8, 1.2)
    a = 10 ** rng.uniform(-2.0, 2.0)
    b = 10 ** rng.uniform(-2.0, 2.0)
    gamma = rng.uniform(0.4, 1.0)
    common = 10 ** rng.uniform(-2.0, 3.0)
    a_tof, _, _, _, a_cost = compute_state(n_exp, m_exp, a, b, gamma, common)
    a_order = top_order(a_tof, reverse=True, k=len(DIAMETERS_NM))
    c_order = top_order(a_cost, reverse=False, k=len(DIAMETERS_NM))
    preserved = a_order == c_order
    full_preserved += int(preserved)
    if draw < 100:
        mc_rows.append([draw, n_exp, m_exp, a, b, gamma, common, int(preserved)])

p_full = full_preserved / N_DRAWS

# Independent slope sensitivity anchors.
sensitivities = []
for label, n_exp in [("primary_nominal", 1.7), ("secondary_low_slope", 0.9), ("secondary_model_planar", 1.8)]:
    s_tof, _, _, _, s_cost = compute_state(n_exp=n_exp)
    sensitivities.append(
        {
            "label": label,
            "n": n_exp,
            "rho": spearman_from_rankings(s_tof, s_cost),
            "tau": kendall_tau_from_rankings(s_tof, s_cost),
            "inversions": pairwise_inversions(s_tof, s_cost),
            "activity_order": top_order(s_tof, reverse=True, k=len(DIAMETERS_NM)),
            "cost_order": top_order(s_cost, reverse=False, k=len(DIAMETERS_NM)),
        }
    )

criteria = {
    "C1_winner_preserved": winner_preserved,
    "C2_full_spearman_ge_0_95": rho >= 0.95,
    "C3_kendall_ge_0_90": tau >= 0.90,
    "C4_zero_pairwise_inversions": inversions == 0,
    "C5_top3_exact": top3_preserved,
    "C6_mc_full_preservation_ge_0_95": p_full >= 0.95,
}
all_pass = all(criteria.values())

with (OUT / "canonical_relative_results.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["candidate", "diameter_nm", "tof_rel", "dispersion_rel", "mass_productivity_rel", "inventory_rel", "economic_index"])
    for d, t, disp, q, m, c in zip(DIAMETERS_NM, tof, dispersion, q_mass, inventory, cost):
        w.writerow([f"AuTiO2_d{int(d)}", d, f"{t:.10f}", f"{disp:.10f}", f"{q:.10f}", f"{m:.10f}", f"{c:.10f}"])

with (OUT / "mc_first_100.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["draw", "n_exp", "m_exp", "a", "b", "gamma", "common", "full_rank_preserved"])
    w.writerows(mc_rows)

report = [
    "# Au/TiO2 Rank-Preservation Control V1 — Frozen run",
    "",
    "This result uses only relative, literature-anchored quantities. It is not an absolute industrial TEA.",
    "",
    "## Nominal ranking",
    "",
    f"- Intrinsic-activity order: **{' > '.join(f'{d:g} nm' for d in activity_order)}**",
    f"- Economic-burden order: **{' > '.join(f'{d:g} nm' for d in cost_order)}** (best = lowest burden)",
    f"- Spearman rho: **{rho:.3f}**",
    f"- Kendall tau: **{tau:.3f}**",
    f"- Pairwise inversions: **{inversions}**",
    f"- Top-3 exact preservation: **{top3_preserved}**",
    "",
    "## Preregistered uncertainty result",
    "",
    f"- Monte Carlo draws: **{N_DRAWS}**",
    f"- Full-rank preservation probability: **{p_full:.4f}**",
    "",
    "## Criteria",
    "",
]
for key, value in criteria.items():
    report.append(f"- {key}: **{'PASS' if value else 'FAIL'}**")
report += [
    "",
    f"Overall preregistered control result: **{'PASS' if all_pass else 'FAIL'}**",
    "",
    "## Independent slope sensitivity",
    "",
]
for s in sensitivities:
    report.append(
        f"- {s['label']} (`n={s['n']}`): rho={s['rho']:.3f}, tau={s['tau']:.3f}, inversions={s['inversions']}; "
        f"activity={' > '.join(f'{d:g}' for d in s['activity_order'])}; economic={' > '.join(f'{d:g}' for d in s['cost_order'])}."
    )

report += [
    "",
    "## Interpretation",
    "",
    "The control is constructed so that catalyst activity and dispersion both reduce required Au/TiO2 inventory, while every downstream catalyst-dependent cost term is positive and monotonic in that inventory. The calculation therefore tests whether the implementation preserves the preregistered monotonic mapping and whether common-series parameter uncertainty changes the ordering.",
    "",
    "A PASS supports only the methodological statement that the multiscale framework does not intrinsically force ranking inversion when no competing downstream penalty is introduced. It does not imply that all Au/TiO2 catalysts, all CO-oxidation conditions or a calibrated industrial process will preserve this ordering.",
]

(OUT / "RANK_PRESERVATION_CONTROL_V1_REPORT.md").write_text("\n".join(report) + "\n", encoding="utf-8")

print("\n".join(report))
