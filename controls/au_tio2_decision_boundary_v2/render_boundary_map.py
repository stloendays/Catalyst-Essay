"""Render the (q, n + m) decision-boundary map from the committed CSV. Output is a PNG next to the CSV
(artifacts/, not figures/). Purely a view of l2_boundary_map_q_vs_nm.csv; no numbers are produced here."""
from __future__ import annotations

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
ART = ROOT / "artifacts" / "au_tio2_decision_boundary_v2"
rows = list(csv.DictReader((ART / "l2_boundary_map_q_vs_nm.csv").open(encoding="utf-8")))
qs = sorted({float(r["q"]) for r in rows})
nms = sorted({float(r["n_plus_m"]) for r in rows})
grid = {(float(r["q"]), float(r["n_plus_m"])): r for r in rows}
P = np.array([[float(grid[(q, nm)]["p_preserved"]) for q in qs] for nm in nms])
F = np.array([[float(grid[(q, nm)]["p_fully_inverted"]) for q in qs] for nm in nms])

fig, axes = plt.subplots(1, 2, figsize=(10, 4), constrained_layout=True)
for ax, Z, title in ((axes[0], P, "P(full order preserved)"), (axes[1], F, "P(fully inverted)")):
    im = ax.pcolormesh(qs, nms, Z, vmin=0, vmax=1, shading="nearest", cmap="viridis")
    ax.plot([min(qs), max(qs)], [min(qs), max(qs)], "w--", lw=1.2, label="deterministic boundary q = n + m")
    ax.axhline(1.9, color="w", lw=0.8, ls=":")
    ax.set_xlabel("lifetime exponent q  (tau ∝ d^q)")
    ax.set_ylabel("activity exponent n + m  (activity ∝ d^-(n+m))")
    ax.set_title(title + ", per-candidate sigma = 0.25")
    ax.set_xlim(min(qs), max(qs))
    ax.set_ylim(min(nms), max(nms))
    fig.colorbar(im, ax=ax)
axes[0].legend(loc="upper left", fontsize=8)
fig.savefig(ART / "l2_boundary_map_q_vs_nm.png", dpi=150)
print("wrote", ART / "l2_boundary_map_q_vs_nm.png")
