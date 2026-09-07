from __future__ import annotations

import csv
import math
import random
from dataclasses import dataclass
from pathlib import Path

OUT = Path("artifacts")
OUT.mkdir(exist_ok=True)

WEIGHTS = {
    "same_material_family": 2.0,
    "price_confounding_absent": 2.0,
    "fixed_stream_condition_justified": 2.0,
    "low_recycle_separation_coupling": 2.0,
    "same_kinetic_regime": 2.0,
    "independent_activity_evidence": 2.0,
    "low_deactivation_selectivity_risk": 1.5,
    "industrial_relevance": 1.5,
}

@dataclass
class Candidate:
    key: str
    reaction: str
    catalyst_series: str
    evidence: str
    source: str
    scores: dict[str, float]
    note: str

CANDIDATES = [
    Candidate(
        key="au_tio2_co_oxidation",
        reaction="CO oxidation",
        catalyst_series="Au/TiO2 particle-size series, 1.5-6 nm",
        evidence=(
            "Published model-catalyst study reports a monotonic increase in TOF with decreasing Au particle diameter "
            "over 1.5-6 nm, at 80 and 170 C and across all tested O2:CO ratios/pressures; reported TOF scales approximately d^-1.8."
        ),
        source="J. Catal. 369 (2019) 175-180; DOI: 10.1016/j.jcat.2018.10.038",
        scores={
            "same_material_family": 1.0,
            "price_confounding_absent": 1.0,
            "fixed_stream_condition_justified": 1.0,
            "low_recycle_separation_coupling": 1.0,
            "same_kinetic_regime": 0.9,
            "independent_activity_evidence": 1.0,
            "low_deactivation_selectivity_risk": 0.9,
            "industrial_relevance": 0.65,
        },
        note="Best structural rank-preservation candidate; final application-scale kinetics should be independently verified before manuscript use.",
    ),
    Candidate(
        key="pt_al2o3_co_oxidation",
        reaction="CO oxidation",
        catalyst_series="Pt/Al2O3 particle-size series, 1-4 nm at 170 C",
        evidence=(
            "Published study reports that 1, 2, 3 and 4 nm Pt/Al2O3 catalysts appear to remain in the same kinetic regime at 170 C; "
            "surface-normalized activity is particle-size dependent with a maximum near 2 nm."
        ),
        source="J. Catal. 377 (2019) 662-672; DOI: 10.1016/j.jcat.2019.07.049",
        scores={
            "same_material_family": 1.0,
            "price_confounding_absent": 1.0,
            "fixed_stream_condition_justified": 1.0,
            "low_recycle_separation_coupling": 1.0,
            "same_kinetic_regime": 1.0,
            "independent_activity_evidence": 1.0,
            "low_deactivation_selectivity_risk": 0.8,
            "industrial_relevance": 0.9,
        },
        note="Best backup if emission-control realism is prioritized; use measured productivity ranking rather than particle size itself as the upstream ranking variable.",
    ),
    Candidate(
        key="pt_al2o3_no_oxidation",
        reaction="NO oxidation",
        catalyst_series="Pt/Al2O3 particle-size series, 1-10 nm",
        evidence=(
            "Published diesel-exhaust study reports size-dependent activity and strong preference for larger Pt particles for NO oxidation."
        ),
        source="Appl. Catal. B 126 (2012) 315-325; DOI: 10.1016/j.apcatb.2012.07.029",
        scores={
            "same_material_family": 1.0,
            "price_confounding_absent": 1.0,
            "fixed_stream_condition_justified": 0.9,
            "low_recycle_separation_coupling": 0.9,
            "same_kinetic_regime": 0.65,
            "independent_activity_evidence": 1.0,
            "low_deactivation_selectivity_risk": 0.6,
            "industrial_relevance": 1.0,
        },
        note="Useful but less clean because surface oxidation and NO/NO2 thermodynamics add extra state dependence.",
    ),
    Candidate(
        key="pd_al2o3_co_oxidation",
        reaction="CO oxidation",
        catalyst_series="Pd/alumina size-selected cluster series",
        evidence=(
            "Published cluster studies show size-dependent CO oxidation, but the dominant kinetic sensitivity changes with experimental mode/condition."
        ),
        source="Int. J. Mass Spectrom. 354-355 (2013/2014); DOI: 10.1016/j.ijms.2014.07.044",
        scores={
            "same_material_family": 1.0,
            "price_confounding_absent": 1.0,
            "fixed_stream_condition_justified": 0.9,
            "low_recycle_separation_coupling": 1.0,
            "same_kinetic_regime": 0.45,
            "independent_activity_evidence": 0.9,
            "low_deactivation_selectivity_risk": 0.65,
            "industrial_relevance": 0.55,
        },
        note="Mechanistic-regime sensitivity makes it weaker as a clean preservation control.",
    ),
    Candidate(
        key="pt_al2o3_propane_dehydrogenation",
        reaction="Propane dehydrogenation",
        catalyst_series="Pt/Al2O3 size series from single atoms to nanoparticles",
        evidence=(
            "Published work shows size-dependent activity, but also strong size dependence of selectivity and coke stability."
        ),
        source="ACS Catal. 10 (2020) 12932-12942; DOI: 10.1021/acscatal.0c03286",
        scores={
            "same_material_family": 1.0,
            "price_confounding_absent": 1.0,
            "fixed_stream_condition_justified": 0.7,
            "low_recycle_separation_coupling": 0.45,
            "same_kinetic_regime": 0.45,
            "independent_activity_evidence": 1.0,
            "low_deactivation_selectivity_risk": 0.2,
            "industrial_relevance": 1.0,
        },
        note="Reject as preservation control: selectivity and coking create competing downstream penalties.",
    ),
]

def weighted_score(c: Candidate) -> float:
    return sum(WEIGHTS[k] * c.scores[k] for k in WEIGHTS)


def au_tio2_structural_stress_test(n_trials: int = 10000, seed: int = 20260907):
    """Stress-test only the monotonic propagation structure for the leading candidate.

    Uses the published TOF~d^-1.8 trend. For spherical particles, exposed surface area per Au mass scales ~1/d,
    so a simple mass-specific productivity proxy scales ~d^-2.8. The downstream cost is intentionally restricted
    to positive monotonic inventory/reactor terms under externally fixed T/P/feed. This is a structural control test,
    not a calibrated TEA.
    """
    rng = random.Random(seed)
    diameters = [1.5, 2.0, 3.0, 4.0, 5.0, 6.0]
    prod = {d: d ** -2.8 for d in diameters}
    activity_rank = sorted(diameters, key=lambda d: prod[d], reverse=True)
    preserved = 0
    for _ in range(n_trials):
        fixed = rng.uniform(0.0, 100.0)
        catalyst_coeff = 10 ** rng.uniform(-2.0, 3.0)
        reactor_coeff = 10 ** rng.uniform(-2.0, 3.0)
        exponent = rng.uniform(0.4, 1.0)
        costs = {}
        for d in diameters:
            inventory = 1.0 / prod[d]
            costs[d] = fixed + catalyst_coeff * inventory + reactor_coeff * (inventory ** exponent)
        economic_rank = sorted(diameters, key=lambda d: costs[d])
        if economic_rank == activity_rank:
            preserved += 1
    return diameters, prod, activity_rank, preserved / n_trials


ranked = sorted(CANDIDATES, key=weighted_score, reverse=True)

with (OUT / "rank_preservation_candidate_scores.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["rank", "key", "reaction", "catalyst_series", "weighted_score", "max_score", "source", "note"])
    for i, c in enumerate(ranked, 1):
        w.writerow([i, c.key, c.reaction, c.catalyst_series, f"{weighted_score(c):.3f}", f"{sum(WEIGHTS.values()):.3f}", c.source, c.note])

_, prod, activity_rank, preserve_fraction = au_tio2_structural_stress_test()

lines = [
    "# Rank-Preservation Control Screen V1",
    "",
    "This is an **ex-ante screening tool**, not a manuscript result. It ranks candidate control systems by structural cleanliness and independent literature support before any full process-economic model is built.",
    "",
    "## Candidate ranking",
    "",
    "| Rank | Candidate | Score | Main reason |",
    "|---:|---|---:|---|",
]
for i, c in enumerate(ranked, 1):
    lines.append(f"| {i} | {c.reaction}: {c.catalyst_series} | {weighted_score(c):.2f}/{sum(WEIGHTS.values()):.1f} | {c.note} |")

best = ranked[0]
lines += [
    "",
    "## Selected candidate",
    "",
    f"**{best.reaction} — {best.catalyst_series}**",
    "",
    best.evidence,
    "",
    f"Primary literature anchor: **{best.source}**.",
    "",
    "Why it is attractive as a preservation control:",
    "",
    "- candidate states share the same active element and support, suppressing catalyst-price reordering across candidates;",
    "- the reaction network is simple and can be evaluated at an externally fixed stream condition;",
    "- no recycle/separation topology change is required for the control definition;",
    "- the literature reports a monotonic particle-size/activity trend across the studied range;",
    "- under a fixed-condition inventory-limited mapping, higher mass-specific productivity maps monotonically to lower required catalyst inventory and reactor burden.",
    "",
    "## Structural rank-preservation stress test",
    "",
    "Using the reported `TOF ~ d^-1.8` trend and a spherical-particle surface-area scaling `~1/d`, the control-only mass-specific productivity proxy is `~d^-2.8`.",
    "",
    f"Activity/productivity rank (best -> worst): **{' > '.join(str(d) + ' nm' for d in activity_rank)}**.",
    "",
    f"Across 10,000 randomized positive monotonic inventory/reactor cost mappings, exact rank preservation = **{preserve_fraction:.4f}**.",
    "",
    "This 1.0000 result is expected from the control structure; it is a check that the proposed downstream mapping does not itself introduce a competing penalty. It is **not** evidence that a calibrated industrial TEA will necessarily preserve the ranking.",
    "",
    "## Recommended next step",
    "",
    "Build a preregistered fixed-condition CO-oxidation control around the leading Au/TiO2 particle-size series, but first replace the structural proxy with independently sourced activity/productivity data at a defensible application condition. Keep Pt/Al2O3 CO oxidation at 170 C as the backup because it has stronger emission-control relevance and a documented common kinetic regime across 1-4 nm particles.",
    "",
    "## Sources encoded in this screen",
    "",
]
for c in CANDIDATES:
    lines.append(f"- {c.source} — {c.reaction}, {c.catalyst_series}.")

(OUT / "RANK_PRESERVATION_SCREEN_V1.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

print("\n".join(lines))
