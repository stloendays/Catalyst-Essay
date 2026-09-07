"""X9: pooled cross-model outcomes with Wilson 95 % CI (reads CROSS_MODEL_STATS_V1.csv only)."""
from __future__ import annotations
import csv
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
rows = [r for r in csv.DictReader(open(ROOT / "CROSS_MODEL_STATS_V1.csv", encoding="utf-8")) if r["section"] == "wilson"]
TIERS = ["nano", "mini", "5.5"]
LABEL = {"nano": "gpt-5.4-nano", "mini": "gpt-5.4-mini", "5.5": "gpt-5.5"}
STRATA = ["pooled", "<=300 CU", ">=500 CU"]
METRICS = ["P(win)", "P(pair)", "P(reach)", "P(full)"]
COLORS = {"nano": "#d62728", "mini": "#ff7f0e", "5.5": "#1f77b4"}
MARK = {"pooled": "o", "<=300 CU": "s", ">=500 CU": "^"}

plt.rcParams.update({"font.size": 13, "axes.labelsize": 14, "axes.titlesize": 15, "legend.fontsize": 12})
fig, axes = plt.subplots(1, 2, figsize=(15, 10), sharey=True)
for ax, variant in zip(axes, ["anonymous", "named"]):
    y = 0
    yticks, ylabels = [], []
    for m in METRICS:
        for t in TIERS:
            for s in STRATA:
                r = next(x for x in rows if x["variant"] == variant and x["tier"] == t and x["stratum"] == s and x["metric"] == m)
                p, lo, hi = float(r["p"]), float(r["ci_lo"]), float(r["ci_hi"])
                ax.plot([lo, hi], [y, y], color=COLORS[t], lw=2.2)
                ax.plot(p, y, marker=MARK[s], color=COLORS[t], ms=8, mec="black", mew=0.6)
                ax.text(1.03, y, f"{r['k']}/{r['n']}", va="center", fontsize=11, color="black")
                if s == "pooled":
                    yticks.append(y + 1)
                    ylabels.append(f"{m}  {LABEL[t]}")
                y += 1.15
            y += 0.7
        y += 1.4
    ax.set_yticks(yticks)
    ax.set_yticklabels(ylabels)
    ax.set_xlim(-0.02, 1.16)
    ax.set_xlabel("probability (Wilson 95 % CI)")
    ax.set_title(f"{variant} task, policy E, 5 runs x 7 budgets per tier")
    ax.axvline(1.0, color="black", lw=0.8, ls=":")
    ax.grid(axis="x", color="#cccccc", lw=0.6)
axes[0].invert_yaxis()
from matplotlib.lines import Line2D
handles = [Line2D([], [], marker=MARK[s], color="black", ls="", ms=8, label={"pooled": "pooled (n=35)", "<=300 CU": "<= 300 CU (n=15)", ">=500 CU": ">= 500 CU (n=20)"}[s]) for s in STRATA]
handles += [Line2D([], [], color=COLORS[t], lw=3, label=LABEL[t]) for t in TIERS]
fig.legend(handles=handles, loc="lower center", ncol=6, frameon=False, bbox_to_anchor=(0.5, 0.0))
fig.suptitle("DISCOVER V1 cross-model outcomes (frozen scorer; per-tier trend Z = 6.95 for P(full), anonymous)", fontsize=15)
fig.tight_layout(rect=(0, 0.05, 1, 1))
out = ROOT / "DISCOVER_CROSS_MODEL_V1" / "figures" / "X9_wilson_ci_pooled.png"
fig.savefig(out, dpi=160)
print(out)

