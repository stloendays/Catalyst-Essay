from __future__ import annotations

import csv
import random
from pathlib import Path

OUT = Path("artifacts")
OUT.mkdir(exist_ok=True)

# Ex-ante criteria: higher score means a cleaner preservation control before any full TEA is built.
WEIGHTS = {
    "same_material_family": 2.0,
    "price_confounding_absent": 2.0,
    "fixed_stream_condition_justified": 2.0,
    "low_recycle_separation_coupling": 2.0,
    "same_kinetic_regime": 2.0,
    "independent_activity_evidence": 2.0,
    "monotonic_activity_order": 2.0,
    "low_deactivation_selectivity_risk": 1.5,
    "industrial_relevance": 1.5,
}

CANDIDATES = [
    {
        "key": "au_tio2_co_oxidation",
        "label": "CO oxidation — Au/TiO2 particle-size series, 1.5-6 nm",
        "source": "J. Catal. 369 (2019) 175-180; DOI: 10.1016/j.jcat.2018.10.038",
        "evidence": "TOF increases monotonically as Au diameter decreases over 1.5-6 nm; reported approximately TOF ~ d^-1.8 across the tested conditions.",
        "scores": [1.0, 1.0, 1.0, 1.0, 0.9, 1.0, 1.0, 0.9, 0.65],
        "note": "Cleanest structural preservation candidate; application-scale kinetics still need independent validation.",
    },
    {
        "key": "pt_al2o3_co_oxidation",
        "label": "CO oxidation — Pt/Al2O3 particle-size series, 1-4 nm at 170 C",
        "source": "J. Catal. 377 (2019) 662-672; DOI: 10.1016/j.jcat.2019.07.049",
        "evidence": "1, 2, 3 and 4 nm Pt/Al2O3 appear to remain in the same kinetic regime at 170 C, with a particle-size-dependent activity maximum near 2 nm.",
        "scores": [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.6, 0.8, 0.9],
        "note": "Best realism-oriented backup; stronger emission-control relevance but the activity-size relation is not monotonic.",
    },
    {
        "key": "pt_al2o3_no_oxidation",
        "label": "NO oxidation — Pt/Al2O3 particle-size series, 1-10 nm",
        "source": "Appl. Catal. B 126 (2012) 315-325; DOI: 10.1016/j.apcatb.2012.07.029",
        "evidence": "Size-dependent activity is documented under diesel-exhaust conditions, but surface oxidation and NO/NO2 thermodynamics add state dependence.",
        "scores": [1.0, 1.0, 0.9, 0.9, 0.65, 1.0, 0.7, 0.6, 1.0],
        "note": "Useful but less clean because thermodynamic and oxidation-state effects can create competing pathways.",
    },
    {
        "key": "pd_al2o3_co_oxidation",
        "label": "CO oxidation — Pd/alumina size-selected cluster series",
        "source": "Int. J. Mass Spectrom.; DOI: 10.1016/j.ijms.2014.07.044",
        "evidence": "Size-dependent CO oxidation is documented, but the dominant kinetic sensitivity changes with condition and experimental mode.",
        "scores": [1.0, 1.0, 0.9, 1.0, 0.45, 0.9, 0.4, 0.65, 0.55],
        "note": "Mechanistic-regime sensitivity makes it a weaker preservation control.",
    },
    {
        "key": "pt_al2o3_propane_dehydrogenation",
        "label": "Propane dehydrogenation — Pt/Al2O3 size series",
        "source": "ACS Catal. 10 (2020) 12932-12942; DOI: 10.1021/acscatal.0c03286",
        "evidence": "Activity, selectivity and coke stability all vary strongly with Pt size.",
        "scores": [1.0, 1.0, 0.7, 0.45, 0.45, 1.0, 0.4, 0.2, 1.0],
        "note": "Reject for this role because selectivity and coking create competing economic penalties.",
    },
]

KEYS = list(WEIGHTS)

def score(c):
    return sum(WEIGHTS[k] * v for k, v in zip(KEYS, c["scores"]))

ranked = sorted(CANDIDATES, key=score, reverse=True)

# Structural stress test for the leading candidate only.
# Literature: TOF ~ d^-1.8. Approximate exposed surface area per Au mass ~ 1/d,
# giving a control-only mass-specific productivity proxy ~ d^-2.8.
rng = random.Random(20260907)
diameters = [1.5, 2.0, 3.0, 4.0, 5.0, 6.0]
productivity = {d: d ** -2.8 for d in diameters}
activity_rank = sorted(diameters, key=lambda d: productivity[d], reverse=True)
preserved = 0
n_trials = 10000
for _ in range(n_trials):
    fixed = rng.uniform(0.0, 100.0)
    catalyst_coeff = 10 ** rng.uniform(-2.0, 3.0)
    reactor_coeff = 10 ** rng.uniform(-2.0, 3.0)
    exponent = rng.uniform(0.4, 1.0)
    costs = {}
    for d in diameters:
        inventory = 1.0 / productivity[d]
        costs[d] = fixed + catalyst_coeff * inventory + reactor_coeff * inventory ** exponent
    if sorted(diameters, key=lambda d: costs[d]) == activity_rank:
        preserved += 1
preserve_fraction = preserved / n_trials

with (OUT / "rank_preservation_candidate_scores_v2.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["rank", "key", "candidate", "score", "max_score", "source", "note"])
    for i, c in enumerate(ranked, 1):
        w.writerow([i, c["key"], c["label"], f"{score(c):.3f}", f"{sum(WEIGHTS.values()):.3f}", c["source"], c["note"]])

best = ranked[0]
lines = [
    "# Rank-Preservation Control Screen V2",
    "",
    "This is an ex-ante candidate screen and structural stress test, not a manuscript TEA result.",
    "",
    "## Ranking",
    "",
    "| Rank | Candidate | Score |",
    "|---:|---|---:|",
]
for i, c in enumerate(ranked, 1):
    lines.append(f"| {i} | {c['label']} | {score(c):.2f}/{sum(WEIGHTS.values()):.1f} |")
lines += [
    "",
    "## Leading candidate",
    "",
    f"**{best['label']}**",
    "",
    best["evidence"],
    "",
    f"Primary literature anchor: **{best['source']}**.",
    "",
    "The candidate is attractive because all states share the same active element and support, catalyst-price ordering is removed as a cross-candidate confounder, the stream can be fixed externally, and the published activity trend is monotonic across the particle-size range.",
    "",
    "## Structural stress test",
    "",
    f"Productivity rank: **{' > '.join(f'{d:g} nm' for d in activity_rank)}**.",
    "",
    f"Exact rank preservation across {n_trials:,} randomized positive monotonic inventory/reactor cost mappings: **{preserve_fraction:.4f}**.",
    "",
    "The 1.0000 value is expected from the deliberately monotonic control structure; it only shows that this control design does not introduce an internal competing penalty. It does not replace an independently calibrated kinetic/process-economic model.",
    "",
    "## Decision",
    "",
    "Proceed to literature validation and preregistration for fixed-condition **Au/TiO2 CO oxidation particle-size control**. Keep **Pt/Al2O3 CO oxidation at 170 C** as the realism-oriented backup if application-scale evidence for the Au/TiO2 series is insufficient.",
]

(OUT / "RANK_PRESERVATION_SCREEN_V2.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines))
