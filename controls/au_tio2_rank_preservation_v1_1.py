from __future__ import annotations

import csv
import hashlib
import json
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "controls" / "au_tio2_rank_preservation_v1_1_config.json"
OUT = ROOT / "artifacts" / "au_tio2_rank_preservation_v1_1"
OUT.mkdir(parents=True, exist_ok=True)

CFG = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ranks(values, reverse=False):
    order = sorted(range(len(values)), key=lambda i: values[i], reverse=reverse)
    out = [0] * len(values)
    for rank, idx in enumerate(order, 1):
        out[idx] = rank
    return out


def pearson(x, y):
    mx = sum(x) / len(x)
    my = sum(y) / len(y)
    num = sum((a - mx) * (b - my) for a, b in zip(x, y))
    den = math.sqrt(sum((a - mx) ** 2 for a in x) * sum((b - my) ** 2 for b in y))
    return num / den


def spearman(activity, burden):
    return pearson(ranks(activity, reverse=True), ranks(burden, reverse=False))


def kendall(activity, burden):
    c = d = 0
    for i in range(len(activity)):
        for j in range(i + 1, len(activity)):
            a = activity[i] - activity[j]
            b = burden[j] - burden[i]  # preservation: higher activity -> lower burden
            if a * b > 0:
                c += 1
            elif a * b < 0:
                d += 1
    return (c - d) / (c + d)


def inversions(activity, burden):
    inv = 0
    for i in range(len(activity)):
        for j in range(i + 1, len(activity)):
            if (activity[i] - activity[j]) * (burden[j] - burden[i]) < 0:
                inv += 1
    return inv


def candidate_state(d_nm: float, n_tof: float, m_disp: float):
    ref = CFG["literature_reference"]
    d_ref = ref["average_diameter_nm"]
    disp_ref = ref["dispersion_fraction"]
    r_ref = ref["stabilized_activity_umol_CO_gcat_s"]
    au_frac = ref["au_loading_mass_fraction"]

    tof_scale = (d_nm / d_ref) ** (-n_tof)
    dispersion = disp_ref * (d_ref / d_nm) ** m_disp
    dispersion = min(1.0, dispersion)
    dispersion_scale = dispersion / disp_ref
    mass_activity = r_ref * tof_scale * dispersion_scale

    flow_mol_s = (
        ref["reaction_flow_Nml_min"] * 1e-3
        / CFG["reactor_model"]["normal_molar_volume_L_mol"]
        / 60.0
    )
    y_co = ref["feed_CO_mole_fraction"]
    w_ref_g = ref["catalyst_mass_mg"] / 1000.0
    r_ref_mol_g_s = r_ref * 1e-6
    k_ref = r_ref_mol_g_s / y_co
    theta_ref = k_ref * w_ref_g / flow_mol_s
    x_target = 1.0 - math.exp(-theta_ref)

    r_mol_g_s = mass_activity * 1e-6
    k = r_mol_g_s / y_co
    required_mass_g = -math.log(1.0 - x_target) * flow_mol_s / k
    required_au_g = required_mass_g * au_frac

    return {
        "diameter_nm": d_nm,
        "tof_scale_vs_2p10nm": tof_scale,
        "dispersion_fraction": dispersion,
        "mass_activity_umol_CO_gcat_s": mass_activity,
        "required_catalyst_mass_mg": required_mass_g * 1000.0,
        "required_Au_mass_mg": required_au_g * 1000.0,
        "target_conversion_fraction": x_target,
    }


def order_by(rows, key, reverse=False):
    return [r["diameter_nm"] for r in sorted(rows, key=lambda r: r[key], reverse=reverse)]


# Frozen nominal calculation.
n_nom = CFG["size_activity_relation"]["nominal_tof_exponent"]
m_nom = CFG["geometry"]["dispersion_exponent_nominal"]
diameters = CFG["candidate_diameters_nm"]
rows = [candidate_state(d, n_nom, m_nom) for d in diameters]

best_mass = min(r["required_catalyst_mass_mg"] for r in rows)
ref_mass = CFG["literature_reference"]["catalyst_mass_mg"]
for r in rows:
    r["procurement_burden_vs_best"] = r["required_catalyst_mass_mg"] / best_mass
    r["catalyst_mass_vs_literature_ref"] = r["required_catalyst_mass_mg"] / ref_mass

activity = [r["mass_activity_umol_CO_gcat_s"] for r in rows]
burden = [r["required_catalyst_mass_mg"] for r in rows]
rho = spearman(activity, burden)
tau = kendall(activity, burden)
inv = inversions(activity, burden)
activity_order = order_by(rows, "mass_activity_umol_CO_gcat_s", reverse=True)
burden_order = order_by(rows, "required_catalyst_mass_mg", reverse=False)

# Literature-envelope robustness: published TOF exponent range plus a modest geometric scaling sensitivity.
rng = random.Random(CFG["uncertainty"]["seed"])
mc_n = CFG["uncertainty"]["draws"]
full_preserved = 0
min_rho = 1.0
mc_preview = []
for draw in range(mc_n):
    n = rng.uniform(CFG["uncertainty"]["tof_exponent_min"], CFG["uncertainty"]["tof_exponent_max"])
    m = rng.uniform(CFG["uncertainty"]["dispersion_exponent_min"], CFG["uncertainty"]["dispersion_exponent_max"])
    rr = [candidate_state(d, n, m) for d in diameters]
    aa = [r["mass_activity_umol_CO_gcat_s"] for r in rr]
    bb = [r["required_catalyst_mass_mg"] for r in rr]
    rrho = spearman(aa, bb)
    preserved = order_by(rr, "mass_activity_umol_CO_gcat_s", True) == order_by(rr, "required_catalyst_mass_mg", False)
    full_preserved += int(preserved)
    min_rho = min(min_rho, rrho)
    if draw < 100:
        mc_preview.append([draw, n, m, rrho, int(preserved)])
p_full = full_preserved / mc_n

criteria = {
    "C1_winner_preserved": activity_order[0] == burden_order[0],
    "C2_full_spearman_ge_0_95": rho >= CFG["pass_criteria"]["full_spearman_min"],
    "C3_kendall_ge_0_90": tau >= CFG["pass_criteria"]["kendall_min"],
    "C4_zero_pairwise_inversions": inv <= CFG["pass_criteria"]["pairwise_inversions_max"],
    "C5_top3_exact": activity_order[:3] == burden_order[:3],
    "C6_mc_full_preservation_ge_0_95": p_full >= CFG["pass_criteria"]["mc_full_preservation_min"],
}
all_pass = all(criteria.values())

# Explicit adjustment ledger relative to V1 nominal structure.
v1_n = 1.7
v1_m = 1.0
v11_n = n_nom
v11_m = m_nom
v1_eff = v1_n + v1_m
v11_eff = v11_n + v11_m
v1_dynamic = (6.0 / 2.0) ** v1_eff
v11_dynamic = (6.0 / 2.0) ** v11_eff

adjustments = [
    ["reference_diameter_nm", 2.0, CFG["literature_reference"]["average_diameter_nm"], 100.0 * (CFG["literature_reference"]["average_diameter_nm"] / 2.0 - 1.0), "Janssens 2006 measured average diameter"],
    ["nominal_TOF_size_exponent", v1_n, v11_n, 100.0 * (v11_n / v1_n - 1.0), "Changed to the 4.5 wt% Overbury series to match the 4.40 wt% absolute-rate anchor"],
    ["effective_mass_activity_exponent", v1_eff, v11_eff, 100.0 * (v11_eff / v1_eff - 1.0), "TOF exponent plus inverse-diameter dispersion scaling"],
    ["6nm_to_2nm_required_mass_ratio", v1_dynamic, v11_dynamic, 100.0 * (v11_dynamic / v1_dynamic - 1.0), "Literature calibration compresses the burden spread without changing order"],
    ["absolute_dispersion_anchor", 1.0, CFG["literature_reference"]["dispersion_fraction"], -62.0, "V1 used a normalized relative anchor; V1.1 uses measured 38% dispersion at 2.10 nm"],
]

with (OUT / "physical_results.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)

with (OUT / "adjustment_ledger.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["parameter", "V1_value", "V1_1_value", "change_percent", "basis"])
    w.writerows(adjustments)

with (OUT / "literature_envelope_first_100.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["draw", "tof_exponent", "dispersion_exponent", "spearman", "full_rank_preserved"])
    w.writerows(mc_preview)

frozen = {
    "version": CFG["version"],
    "config_sha256": sha256(CONFIG_PATH),
    "runner_sha256": sha256(Path(__file__)),
}
(OUT / "FROZEN_HASHES.json").write_text(json.dumps(frozen, indent=2) + "\n", encoding="utf-8")

x_pct = rows[0]["target_conversion_fraction"] * 100.0
report = [
    "# Au/TiO2 Rank-Preservation Control V1.1 — literature-calibrated physical mapping",
    "",
    "V1.1 preserves V1 and replaces the arbitrary downstream burden coefficients with a literature-anchored fixed-condition reactor calculation. No parameter was fitted to an observed economic ranking.",
    "",
    "## Literature anchor used in the calculation",
    "",
    "Janssens et al., Journal of Catalysis 240 (2006) 108-113, DOI 10.1016/j.jcat.2006.03.008:",
    "",
    "- Au/TiO2 average Au diameter: **2.10 nm**",
    "- Au loading: **4.40 wt%**",
    "- measured dispersion: **38%**",
    "- stabilized CO oxidation activity after 10-15 h: **8.8 umol CO gcat^-1 s^-1**",
    "- catalyst mass: **21.4 mg**",
    "- reaction condition: **273.15 K, 1 atm, 1% CO / 21% O2 / 78% Ar**",
    "- Au/TiO2 reaction flow: **214.4 Nml min^-1**",
    "- quartz U-tube inner diameter: **2 mm**; powder size **125-300 um**",
    "",
    f"Using the paper's pseudo-first-order plug-flow relation, these values imply a reference conversion of **{x_pct:.2f}%**. This conversion is derived from the literature experiment and is not manually chosen.",
    "",
    "For particle-size dependence, the nominal TOF exponent is changed from V1's 1.7 to **0.9**, because Overbury et al. report TOF ~ d^(-0.9 +/- 0.2) for their **4.5 wt%** Au/TiO2 series, which is the closest loading match to the 4.40 wt% absolute-rate anchor. The stronger 1.7 and 1.8 exponents remain secondary sensitivity bounds.",
    "",
    "## Adjustment magnitude relative to V1",
    "",
    "| Quantity | V1 | V1.1 | Change |",
    "|---|---:|---:|---:|",
]
for p, old, new, pct, _ in adjustments[:4]:
    report.append(f"| {p} | {old:.4g} | {new:.4g} | {pct:+.1f}% |")
report += [
    "",
    "Additional structural changes:",
    "",
    "- the V1 normalized dispersion anchor is replaced by the measured **38% at 2.10 nm**;",
    "- arbitrary V1 economic coefficients (`a`, `b`, `gamma`, `common`) are removed completely;",
    "- absolute catalyst activity, Au loading, catalyst mass, feed, flow, temperature and reactor diameter are now literature anchored;",
    "- absolute USD is still not reported because a process-scale catalyst replacement interval and reactor CAPEX basis are not supplied by these sources.",
    "",
    "## V1.1 physical results",
    "",
    "| Au diameter | mass activity (umol gcat^-1 s^-1) | required catalyst (mg) | required Au (mg) | burden vs best |",
    "|---:|---:|---:|---:|---:|",
]
for r in rows:
    report.append(
        f"| {r['diameter_nm']:.0f} nm | {r['mass_activity_umol_CO_gcat_s']:.4f} | {r['required_catalyst_mass_mg']:.3f} | {r['required_Au_mass_mg']:.3f} | {r['procurement_burden_vs_best']:.3f}x |"
    )
report += [
    "",
    f"Activity order: **{' > '.join(f'{d:g} nm' for d in activity_order)}**",
    f"Catalyst-cost / packing-burden order: **{' > '.join(f'{d:g} nm' for d in burden_order)}** (best to worst)",
    f"Spearman rho: **{rho:.3f}**",
    f"Kendall tau: **{tau:.3f}**",
    f"Pairwise inversions: **{inv}**",
    "",
    "## Literature-envelope robustness",
    "",
    f"Across **{mc_n:,}** draws spanning TOF exponents {CFG['uncertainty']['tof_exponent_min']}-{CFG['uncertainty']['tof_exponent_max']} and dispersion exponents {CFG['uncertainty']['dispersion_exponent_min']}-{CFG['uncertainty']['dispersion_exponent_max']}, exact full-rank preservation = **{p_full:.4f}** and minimum Spearman rho = **{min_rho:.3f}**.",
    "",
    "## Frozen criteria",
    "",
]
for key, value in criteria.items():
    report.append(f"- {key}: **{'PASS' if value else 'FAIL'}**")
report += [
    "",
    f"Overall V1.1 result: **{'PASS' if all_pass else 'FAIL'}**",
    "",
    "## Interpretation",
    "",
    "The literature calibration substantially reduces the predicted catalyst-burden spread compared with V1 (the 6 nm/2 nm mass ratio falls from about 19.4x to about 8.1x), but the ordering is unchanged. The preservation therefore does not depend on the original arbitrary burden coefficients. It follows from the independently supported monotonic size-activity relation combined with a fixed process condition and a common Au/TiO2 composition.",
    "",
    "This remains a rank-preservation control rather than a full industrial TEA. Its valid claim is that the multiscale implementation can preserve an upstream ordering when the downstream mapping is physically monotonic and no competing process-severity or topology penalty is introduced.",
]

(OUT / "RANK_PRESERVATION_CONTROL_V1_1_REPORT.md").write_text("\n".join(report) + "\n", encoding="utf-8")
print("\n".join(report))
