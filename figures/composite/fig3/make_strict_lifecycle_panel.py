"""Render the Figure 3 strict-scaling x lifecycle reachability panel on its own.

This is a production helper for the Fig. 3 composite (make_fig3.py, panel d). It does not
overwrite the composite Fig3 files.

Inputs are the promoted exact NH3-FINAL-1.2 outputs under
analysis/fe_bridge_backward_2026_09_29/nh3_1_2/ (canonical run nh3_final_1_2_20261013).
Every annotated number is read from scaling_lifecycle_exact_summary.json.
"""
from __future__ import annotations

import csv
import json
import os

import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
AN = os.path.join(REPO, "analysis", "fe_bridge_backward_2026_09_29", "nh3_1_2")
BOUNDARY = os.path.join(AN, "scaling_lifecycle_exact_global_boundary.csv")
SUMMARY = os.path.join(AN, "scaling_lifecycle_exact_summary.json")


def read_csv(path):
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


rows = read_csv(BOUNDARY)
summary = json.load(open(SUMMARY, encoding="utf-8"))
assert summary["process_states"] == 14510
corner = summary["tested_lifecycle_envelope"]["best_corner"]
margin = float(corner["margin_vs_Fe_USD_t"])
rec20 = 100.0 * float(summary["boundary_examples"]["required_recovery_at_20y"])
life99 = float(summary["boundary_examples"]["required_life_at_99pct_recovery_y"])

life = [float(r["life_y"]) for r in rows]
recovery = [100.0 * float(r["required_recovery_fraction"]) for r in rows]

fig, ax = plt.subplots(figsize=(3.45, 2.55))
ax.plot(life, recovery, lw=1.4)
ax.axvline(20.0, lw=0.8, ls="--")
ax.axhline(99.0, lw=0.8, ls="--")
ax.scatter([20.0], [99.0], s=24, zorder=4)
ax.scatter([20.0], [rec20], s=24, zorder=4)
ax.scatter([life99], [99.0], s=24, zorder=4)
ax.annotate(
    "tested corner\n%s USD t$^{-1}$ vs Fe" % ("%+.3f" % margin).replace("-", "−"),
    (20.0, 99.0),
    xytext=(27.0, 99.85),
    va="top",
    fontsize=7,
    arrowprops=dict(arrowstyle="-", lw=0.5),
)
ax.annotate(
    "parity: %.3f%% at 20 y" % rec20,
    (20.0, rec20),
    xytext=(22.0, 96.7),
    fontsize=7,
    arrowprops=dict(arrowstyle="-", lw=0.5),
)
ax.annotate(
    "parity: %.2f y at 99%%" % life99,
    (life99, 99.0),
    xytext=(6.0, 97.6),
    fontsize=7,
    arrowprops=dict(arrowstyle="-", lw=0.5),
)
ax.set_xlim(4, 51)
ax.set_ylim(95.5, 100.05)
ax.set_xlabel("Catalyst lifetime (y)")
ax.set_ylabel("Ru recovery for Fe parity (%)")
ax.set_title("Strict-scaling × lifecycle reachability", fontsize=8)
ax.grid(alpha=0.18)
fig.tight_layout()
fig.savefig(os.path.join(HERE, "Fig3_strict_lifecycle_panel.svg"))
fig.savefig(os.path.join(HERE, "Fig3_strict_lifecycle_panel.png"), dpi=300)
