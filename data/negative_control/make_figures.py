"""Figures F1-F5 for a negative-control run directory (reads results.json only). Usage: make_figures.py <run_dir>"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

run = Path(sys.argv[1]); r = json.loads((run / "results.json").read_text(encoding="utf-8"))
ver = r["project"]["model_version"]; det = r["deterministic"]; mf = det["metrics_feasible_censored"]; fig_dir = run / "figures"
plt.rcParams.update({"font.size": 13, "axes.labelsize": 14, "axes.titlesize": 15, "legend.fontsize": 12})
metals = det["activity_order"]; M = det["metals"]
feas = [m for m in metals if M[m]["feasible"]]
erank = {m: i + 1 for i, m in enumerate(mf["economic_order_feasible"])}
PGM = {"Ru", "Os", "Rh", "Ir", "Pd", "Pt", "Au", "Ag", "Re"}

# F1 atomic vs economic ranking
fig, ax = plt.subplots(figsize=(9, 7))
for i, m in enumerate(metals):
    ar = i + 1; er = erank.get(m)
    if er is None:
        ax.plot(ar, len(metals) + 1, "x", color="black", ms=9); ax.text(ar, len(metals) + 1.35, m, ha="center", fontsize=12)
    else:
        c = "#d62728" if m == metals[0] else ("#1f77b4" if m in PGM else "#2ca02c")
        ax.plot(ar, er, "o", color=c, ms=10, mec="black"); ax.text(ar, er + 0.45, m, ha="center", fontsize=12)
ax.plot([0.5, len(metals) + 0.5], [0.5, len(metals) + 0.5], ":", color="black", lw=1)
ax.set_xlabel("atomic activity rank (450 °C, common condition)"); ax.set_yticks(list(range(1, len(metals) + 2)))
ax.set_yticklabels([str(k) for k in range(1, len(metals) + 1)] + ["infeasible"]); ax.set_ylabel("economic rank (per-candidate re-optimized)")
ax.set_title(f"{ver}: Top-3 ρ = {mf['top3_spearman']:.2f}, full ρ = {mf['full_spearman']:.2f}, τ = {mf['full_kendall']:.2f}", fontsize=14)
ax.invert_yaxis(); ax.grid(color="#dddddd", lw=0.6); fig.tight_layout(); fig.savefig(fig_dir / "F1_ranking_propagation.png", dpi=160); plt.close(fig)

# F2 rolling top-K (N2O vs NH3)
fig, ax = plt.subplots(figsize=(9, 5.5))
ks = [x["K"] for x in mf["rolling"]]; ax.plot(ks, [x["rho"] for x in mf["rolling"]], "o-", color="#1f77b4", lw=2.2, ms=8, label=f"N2O ({ver}, feasible-censored)")
raw = det["metrics_raw_unconstrained"]["rolling"]; ax.plot([x["K"] for x in raw], [x["rho"] for x in raw], "s--", color="#1f77b4", lw=1.5, ms=6, label="N2O (unconstrained)")
nh = r["nh3_reference"]["feasible_censored"]["rolling"]; ax.plot([x["K"] for x in nh], [x["rho"] for x in nh], "^-", color="#d62728", lw=2.2, ms=8, label="NH3-FINAL-1.1 (feasible-censored)")
ax.axhline(0, color="black", lw=0.8); ax.set_xlabel("K highest-activity candidates retained"); ax.set_ylabel("Spearman ρ (atomic vs economic)")
ax.set_ylim(-1.05, 1.05); ax.grid(color="#dddddd", lw=0.6); ax.legend(loc="lower right"); ax.set_title("Rolling Top-K rank correlation")
fig.tight_layout(); fig.savefig(fig_dir / "F2_rolling_topk.png", dpi=160); plt.close(fig)

# F3 cost decomposition (feasible candidates, atomic order)
pools = ["metal_cost", "reactor_base", "vessel_pressure_premium", "heating", "pressure_drop"]
labels = {"metal_cost": "metal inventory", "reactor_base": "reactor base CAPEX", "vessel_pressure_premium": "vessel pressure premium", "heating": "heating fuel", "pressure_drop": "expander work lost (ΔP)"}
cols = {"metal_cost": "#d62728", "reactor_base": "#8c564b", "vessel_pressure_premium": "#9467bd", "heating": "#ff7f0e", "pressure_drop": "#1f77b4"}
fig, ax = plt.subplots(figsize=(11, 6))
x = np.arange(len(feas)); bottom = np.zeros(len(feas))
for p in pools:
    v = np.array([M[m]["feasible"][p] for m in feas]); ax.bar(x, v, bottom=bottom, color=cols[p], label=labels[p], edgecolor="black", lw=0.5); bottom += v
ax.set_xticks(x); ax.set_xticklabels([f"{m}\n{M[m]['feasible']['T_C']:.0f} °C" for m in feas]); ax.set_ylabel("USD per t N2O destroyed"); ax.set_yscale("log")
ax.set_title(f"{ver}: cost pools at each candidate's own optimum (atomic-rank order)"); ax.legend(loc="upper left"); ax.grid(axis="y", color="#dddddd", lw=0.6)
fig.tight_layout(); fig.savefig(fig_dir / "F3_cost_decomposition.png", dpi=160); plt.close(fig)

# F4 operating envelopes: feasible cost vs T for each candidate
fig, ax = plt.subplots(figsize=(11, 6.5))
cmap = plt.get_cmap("tab20")
for i, m in enumerate(metals):
    env = M[m]["envelope"]; T = [e["T_C"] for e in env if e["total"] is not None]; c = [e["total"] for e in env if e["total"] is not None]
    if not T: continue
    ax.plot(T, c, lw=2 if m in feas[:3] else 1.2, color=cmap(i % 20), label=m)
    fe = M[m]["feasible"]
    if fe: ax.plot(fe["T_C"], fe["total"], "o", color=cmap(i % 20), ms=7, mec="black")
ax.axvline(r["project"].get("available_temperature_C", 420) if isinstance(r["project"], dict) and "available_temperature_C" in r["project"] else 420, color="black", ls=":", lw=1)
ax.set_yscale("log"); ax.set_xlabel("reactor temperature (°C)"); ax.set_ylabel("USD per t N2O (best feasible bed diameter at each T)")
ax.set_title(f"{ver}: cost vs T per candidate (dot = own optimum; dotted line = available tail-gas T)", fontsize=13); ax.legend(ncol=5, loc="upper right"); ax.grid(color="#dddddd", lw=0.6)
fig.tight_layout(); fig.savefig(fig_dir / "F4_operating_envelopes.png", dpi=160); plt.close(fig)

# F5 MC rank preservation
mc = r["monte_carlo"]; t3 = np.array([d["top3"] for d in mc["draws_table"]], float)
fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
axes[0].hist(t3[~np.isnan(t3)], bins=np.linspace(-1, 1, 21), color="#1f77b4", edgecolor="black")
axes[0].axvline(0.5, color="#d62728", lw=2, ls="--"); axes[0].set_xlabel("Top-3 Spearman ρ per draw"); axes[0].set_ylabel("draws")
axes[0].set_title(f"±{mc['half_width_eV']} eV, {mc['draws']} draws: P(ρ₃ ≥ 0.5) = {mc['P_C2_top3_rho_ge_0.5']:.2f}", fontsize=13)
ew = mc["economic_winner_counts"]; aw = mc["atomic_winner_counts"]; names = sorted(set(ew) | set(aw), key=lambda k: -(ew.get(k, 0) + aw.get(k, 0)))
xx = np.arange(len(names)); axes[1].bar(xx - 0.2, [aw.get(k, 0) / mc["draws"] for k in names], 0.4, color="#2ca02c", label="atomic winner", edgecolor="black")
axes[1].bar(xx + 0.2, [ew.get(k, 0) / mc["draws"] for k in names], 0.4, color="#d62728", label="economic winner", edgecolor="black")
axes[1].set_xticks(xx); axes[1].set_xticklabels([str(k) for k in names]); axes[1].set_ylabel("fraction of draws"); axes[1].legend()
axes[1].set_title(f"P(atomic winner = economic winner) = {mc['P_C1_winner_preserved']:.2f}", fontsize=13)
for a in axes: a.grid(axis="y", color="#dddddd", lw=0.6)
fig.tight_layout(); fig.savefig(fig_dir / "F5_mc_rank_preservation.png", dpi=160); plt.close(fig)
print("figures written to", fig_dir)
