"""Render the new Figure 3 strict-scaling x lifecycle reachability panel.

This is a production helper for the next Fig. 3 composite rebuild. It does not
overwrite the current five-panel Fig3 files.

Inputs are the promoted exact outputs under
analysis/fe_bridge_backward_2026_09_29/.
"""
from __future__ import annotations

import csv
import os

import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
AN = os.path.join(REPO, "analysis", "fe_bridge_backward_2026_09_29")
BOUNDARY = os.path.join(AN, "scaling_lifecycle_exact_global_boundary.csv")


def read_csv(path):
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


rows = read_csv(BOUNDARY)
life = [float(r["life_y"]) for r in rows]
recovery = [100.0 * float(r["required_recovery_fraction"]) for r in rows]

fig, ax = plt.subplots(figsize=(3.45, 2.55))
ax.plot(life, recovery, lw=1.4)
ax.axvline(20.0, lw=0.8, ls="--")
ax.axhline(99.0, lw=0.8, ls="--")
ax.scatter([20.0], [99.0], s=24, zorder=4)
ax.scatter([20.0], [99.1186330920211], s=24, zorder=4)
ax.annotate(
    "tested corner\n+0.071 USD t$^{-1}$",
    (20.0, 99.0),
    xytext=(26.0, 99.43),
    fontsize=7,
    arrowprops=dict(arrowstyle="-", lw=0.5),
)
ax.annotate(
    "parity: 99.1186% at 20 y",
    (20.0, 99.1186330920211),
    xytext=(6.0, 98.45),
    fontsize=7,
    arrowprops=dict(arrowstyle="-", lw=0.5),
)
ax.set_xlim(4, 51)
ax.set_ylim(97.5, 100.0)
ax.set_xlabel("Catalyst lifetime (y)")
ax.set_ylabel("Ru recovery for Fe parity (%)")
ax.set_title("Strict-scaling × lifecycle reachability", fontsize=8)
ax.grid(alpha=0.18)
fig.tight_layout()
fig.savefig(os.path.join(HERE, "Fig3_strict_lifecycle_panel.svg"))
fig.savefig(os.path.join(HERE, "Fig3_strict_lifecycle_panel.png"), dpi=300)
