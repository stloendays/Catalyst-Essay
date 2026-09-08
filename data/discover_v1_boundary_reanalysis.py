"""Post-hoc boundary reanalysis for frozen DISCOVER V1.

This script does not modify, rescore, or rerun any frozen DISCOVER V1 trace.
It reads the published aggregate table only and asks two narrower questions:

1) How much does policy E change complete-decision success relative to
   deterministic policy D as a function of CU budget?
2) For the strong model, when both policies recover the same complete decision,
   does policy E reduce total scientific compute?

Outputs are diagnostic/exploratory and must not be used to replace the
pre-registered DISCOVER V1 E-vs-D Go criterion.
"""
from __future__ import annotations

import math
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "cross_model_scores_2026-09-06.csv"
OUT_SUMMARY = ROOT / "data" / "discover_v1_boundary_diagnostics_2026-09-08.csv"
OUT_EFF = ROOT / "data" / "discover_v1_strong_efficiency_diagnostics_2026-09-08.csv"
FIG1 = ROOT / "figures" / "discover_v1_delta_pfull_vs_budget.png"
FIG2 = ROOT / "figures" / "discover_v1_strong_compute_saving_vs_budget.png"

BUDGETS = [200, 250, 300, 500, 800, 1200, 2000]
TIERS = {
    "gpt-5.4-nano-2026-03-17": "nano",
    "gpt-5.4-mini-2026-03-17": "mini",
    "gpt-5.5-2026-04-23": "strong",
}


def wilson(k: int, n: int, z: float = 1.959963984540054) -> tuple[float, float]:
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def main() -> None:
    df = pd.read_csv(SRC)

    d = df[(df.policy == "D_fixed_voi") & (df.variant == "anonymous")].copy()
    d = d.set_index("budget_CU")

    rows: list[dict] = []
    for model, short in TIERS.items():
        e = df[
            (df.model == model)
            & (df.policy == "E_llm_agent")
            & (df.variant == "anonymous")
        ].copy()
        e = e.set_index("budget_CU")
        for b in BUDGETS:
            p_e = float(e.loc[b, "P_full_decision_correct"])
            n = int(e.loc[b, "n"])
            k = int(round(p_e * n))
            lo, hi = wilson(k, n)
            p_d = float(d.loc[b, "P_full_decision_correct"])
            rows.append(
                {
                    "tier": short,
                    "budget_CU": b,
                    "E_full_correct": p_e,
                    "D_full_correct": p_d,
                    "delta_P_full_E_minus_D": p_e - p_d,
                    "delta_CI_lo": lo - p_d,
                    "delta_CI_hi": hi - p_d,
                    "E_n": n,
                }
            )

    out = pd.DataFrame(rows)
    out.to_csv(OUT_SUMMARY, index=False)

    FIG1.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8.2, 5.2))
    for short in ["nano", "mini", "strong"]:
        sub = out[out.tier == short]
        y = sub.delta_P_full_E_minus_D.to_numpy()
        yerr = [
            y - sub.delta_CI_lo.to_numpy(),
            sub.delta_CI_hi.to_numpy() - y,
        ]
        ax.errorbar(
            sub.budget_CU,
            y,
            yerr=yerr,
            marker="o",
            linewidth=1.5,
            capsize=3,
            label=short,
        )
    ax.axhline(0, linewidth=1)
    ax.set_xscale("log")
    ax.set_xticks(BUDGETS)
    ax.set_xticklabels([str(b) for b in BUDGETS])
    ax.set_xlabel("Scientific-compute budget (CU)")
    ax.set_ylabel(r"$\Delta P_{full}=P_{full}^{E}-P_{full}^{D}$")
    ax.set_title("DISCOVER V1: observed adaptive-policy advantage vs compute budget")
    ax.legend(frameon=False)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(FIG1, dpi=220, bbox_inches="tight")
    plt.close(fig)

    strong = df[
        (df.model == "gpt-5.5-2026-04-23")
        & (df.policy == "E_llm_agent")
        & (df.variant == "anonymous")
    ].copy().set_index("budget_CU")

    eff_rows: list[dict] = []
    for b in BUDGETS:
        e_spent = float(strong.loc[b, "mean_spent_CU"])
        d_spent = float(d.loc[b, "mean_spent_CU"])
        eff_rows.append(
            {
                "budget_CU": b,
                "D_mean_spent_CU": d_spent,
                "strong_E_mean_spent_CU": e_spent,
                "relative_total_CU_saving_pct": 100 * (d_spent - e_spent) / d_spent,
                "D_full_correct": float(d.loc[b, "P_full_decision_correct"]),
                "strong_E_full_correct": float(strong.loc[b, "P_full_decision_correct"]),
                "D_CU_to_stable_correct": d.loc[b, "mean_CU_to_stable_correct"],
                "strong_E_CU_to_stable_correct": strong.loc[b, "mean_CU_to_stable_correct"],
                "D_unnecessary_CU_fraction": d.loc[b, "mean_unnecessary_CU_fraction"],
                "strong_E_unnecessary_CU_fraction": strong.loc[b, "mean_unnecessary_CU_fraction"],
            }
        )
    eff = pd.DataFrame(eff_rows)
    eff.to_csv(OUT_EFF, index=False)

    fig, ax = plt.subplots(figsize=(8.2, 5.2))
    ax.plot(eff.budget_CU, eff.relative_total_CU_saving_pct, marker="o", linewidth=1.6)
    ax.axhline(0, linewidth=1)
    ax.set_xscale("log")
    ax.set_xticks(BUDGETS)
    ax.set_xticklabels([str(b) for b in BUDGETS])
    ax.set_xlabel("Scientific-compute budget (CU)")
    ax.set_ylabel("Total CU saving of E vs D (%)")
    ax.set_title("Strong model: total-compute difference after adaptive allocation")
    ax.annotate(
        "D full decision fails here",
        xy=(200, float(eff.loc[eff.budget_CU == 200, "relative_total_CU_saving_pct"].iloc[0])),
        xytext=(250, 24),
        arrowprops={"arrowstyle": "->"},
    )
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(FIG2, dpi=220, bbox_inches="tight")
    plt.close(fig)

    print(f"wrote {OUT_SUMMARY.relative_to(ROOT)}")
    print(f"wrote {OUT_EFF.relative_to(ROOT)}")
    print(f"wrote {FIG1.relative_to(ROOT)}")
    print(f"wrote {FIG2.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
