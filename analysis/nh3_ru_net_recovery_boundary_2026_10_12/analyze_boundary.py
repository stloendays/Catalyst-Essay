"""Summarize the independently computed NH3 Ru/Fe boundary and plot a decision map.

This post-processing reads only Action-produced outputs. No kinetic/process calculations
are fabricated, interpolated or added here. The parity line eta=q*/r is exact within
the frozen process grid and the multiplicative credited-price assumption.
"""
from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
MAX_PROMOTED_RECOVERY = 0.9555


def read_rows(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_rows(path, rows):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main():
    costs_path = HERE / "cost_surface.csv"
    boundaries_path = HERE / "parity_boundary.csv"
    costs = read_rows(costs_path)
    boundaries = read_rows(boundaries_path)
    assert len(costs) == 378 and len(boundaries) == 54, "Unexpected input coverage"

    by_geometry = defaultdict(list)
    for row in boundaries:
        key = (row["loop"], float(row["w_Ru"]), float(row["rho_kg_m3"]))
        by_geometry[key].append(row)

    decision = []
    q_by_geometry = {}
    for (loop, w, rho), entries in sorted(by_geometry.items()):
        assert len(entries) == 3
        q_values = [float(x["effective_credit_parity"]) for x in entries if x["effective_credit_parity"]]
        assert len(q_values) in (0, 3)
        if q_values:
            assert max(q_values) - min(q_values) < 1e-12, "Parity must not depend on eta"
            q = q_values[0]
        else:
            q = None
        q_by_geometry[(loop, w, rho)] = q
        for row in entries:
            eta = float(row["net_realization"])
            expected = (q is not None and q <= eta * MAX_PROMOTED_RECOVERY)
            assert (row["parity_in_promoted_range"] == "True") == expected
        decision.append({
            "loop": loop,
            "Ru_loading_fraction": w,
            "bed_density_kg_m3": rho,
            "q_parity_effective_credit": "" if q is None else q,
            "r_parity_if_eta_100pct": "" if q is None else q,
            "r_parity_if_eta_90pct": "" if q is None or q > 0.9 else q / 0.9,
            "eta_parity_at_promoted_recovery_9555": "" if q is None else q / MAX_PROMOTED_RECOVERY,
            "promoted_parity_if_eta_100pct": q is not None and q <= MAX_PROMOTED_RECOVERY,
            "promoted_parity_if_eta_90pct": q is not None and q <= 0.90 * MAX_PROMOTED_RECOVERY,
        })
    assert len(decision) == 18
    write_rows(HERE / "decision_thresholds.csv", decision)

    counts = {}
    for loop in ("main", "KAAP"):
        counts[loop] = {}
        for eta in (0.8, 0.9, 1.0):
            subset = [c for c in costs if c["loop"] == loop and float(c["net_realization"]) == eta]
            assert len(subset) == 63
            wins = sum(float(c["gap_same_loop_USD_t"]) < -1e-9 for c in subset)
            counts[loop][str(eta)] = {"Ru_cheaper": wins, "cases": len(subset)}
    assert counts["main"]["1.0"]["Ru_cheaper"] == 0

    key = ("KAAP", 0.08, 490.0)
    q = q_by_geometry[key]
    assert q is not None
    def cost_at(r, eta):
        match = [c for c in costs if c["loop"] == "KAAP"
                 and float(c["w_Ru"]) == key[1] and float(c["rho_kg_m3"]) == key[2]
                 and abs(float(c["recovery"]) - r) < 1e-10
                 and float(c["net_realization"]) == eta]
        assert len(match) == 1, (r, eta, len(match))
        return {"Ru_USD_t": float(match[0]["Ru_cost_USD_t"]),
                "Fe_same_loop_USD_t": float(match[0]["Fe_same_loop_USD_t"]),
                "gap_Ru_minus_Fe_USD_t": float(match[0]["gap_same_loop_USD_t"])}
    comparisons = {str(eta): cost_at(MAX_PROMOTED_RECOVERY, eta) for eta in (0.8, 0.9, 1.0)}
    report = {
        "source": "GitHub Actions derived NH3-FINAL-1.1 cost_surface/parity_boundary",
        "source_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in (costs_path, boundaries_path)},
        "counts_by_loop_and_net_realization": counts,
        "reference": {"loop": "KAAP", "Ru_loading": 0.08, "bed_density_kg_m3": 490.0},
        "critical_effective_net_credit": q,
        "critical_physical_recovery_if_full_realization": q,
        "critical_physical_recovery_if_90pct_realization": q / 0.90,
        "critical_monetary_realization_at_9555pct_recovery": q / MAX_PROMOTED_RECOVERY,
        "cost_at_9555pct_physical_recovery": comparisons,
        "meaning": "Cost equality is conditional on the KAAP pressure/temperature mask and on the frozen replacement-cost convention; eta is not a measured economic parameter.",
    }
    (HERE / "decision_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # This figure shows a numerical calculation, not a schematic ranking volcano.
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    fig, axes = plt.subplots(1, 2, figsize=(11.6, 4.5), constrained_layout=True)
    selected_r = sorted({float(c["recovery"]) for c in costs
                         if c["loop"] == "KAAP" and float(c["recovery"]) >= 0.9})
    for eta in (1.0, 0.9, 0.8):
        gaps = [cost_at(r, eta)["gap_Ru_minus_Fe_USD_t"] for r in selected_r]
        axes[0].plot([100*r for r in selected_r], gaps, marker="o", label=f"Net realization {100*eta:.0f}%")
    axes[0].axhline(0, linewidth=1, linestyle="--")
    axes[0].set_xlabel("Physical Ru recovery (%)")
    axes[0].set_ylabel("Ru - Fe same-loop cost (USD/t NH3)")
    axes[0].set_title("(a) Recovery credit sensitivity")
    axes[0].legend(fontsize=8)
    axes[0].grid(alpha=0.2)

    r = np.linspace(0.85, 1.0, 300)
    eta_boundary = q / r
    axes[1].plot(r * 100, 100 * eta_boundary, linewidth=2, label="Equal Ru and Fe cost")
    axes[1].fill_between(r * 100, np.clip(100 * eta_boundary, 80, 100), 100,
                         where=eta_boundary <= 1.0, alpha=0.18, label="Ru lower-cost region")
    axes[1].axvline(MAX_PROMOTED_RECOVERY * 100, linestyle="--", linewidth=1,
                    label="Promoted Ru/C recovery upper bound")
    axes[1].scatter([MAX_PROMOTED_RECOVERY * 100], [100*q/MAX_PROMOTED_RECOVERY], s=35)
    axes[1].set_xlim(85, 100)
    axes[1].set_ylim(80, 101)
    axes[1].set_xlabel("Physical Ru recovery (%)")
    axes[1].set_ylabel("Net value realization (%)")
    axes[1].set_title("(b) Model-conditional decision frontier")
    axes[1].legend(fontsize=7, loc="lower left")
    axes[1].grid(alpha=0.2)
    fig.suptitle("KAAP-type loop, Ru/C 8 wt%, bed density 490 kg/m3, u=11", fontsize=12)
    fig.savefig(HERE / "ru_fe_net_recovery_decision.png", dpi=200)
    fig.savefig(HERE / "ru_fe_net_recovery_decision.pdf")
    plt.close(fig)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
