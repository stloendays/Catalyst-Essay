#!/usr/bin/env python3
"""Render F10 - main-text Agent figure (three panels).

Scientific design frozen in docs/F10_AGENT_FIGURE_SPEC_AND_ED_SI_PLAN_2026-09-13.md.
Metric definitions fixed by docs/AGENT_METRIC_DEFINITIONS_SOURCE_OF_TRUTH_2026-09-13.md.

This script performs RENDERING ONLY. Every plotted value is read from
data/agent_figure_panel_data_2026-09-13.csv (built by tools/discover/build_agent_figure_data.py) and from
data/discover_boundary_c1_error_taxonomy_summary.csv for the median smallest-window series. Nothing is hand-entered.

Usage (from the repository root):
  python figures/agent/render_F10_agent_envelope.py
"""
from __future__ import annotations
import csv
import hashlib
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

ROOT = Path(__file__).resolve().parents[2]
PANEL = ROOT / "data" / "agent_figure_panel_data_2026-09-13.csv"
TAX = ROOT / "data" / "discover_boundary_c1_error_taxonomy_summary.csv"
OUT = ROOT / "figures" / "agent"
STEM = "F10_agent_capability_bounded_envelope"

D_THRESHOLD = 206.0          # policy D full-decision completion threshold, CU
LOWEST_STABLE = 75.0         # lowest strong budget with 20/20 completion, CU
FULL_DOMAIN = 14136          # admissible process states
NON_BINDING = 5000.0         # the non-binding allowance, plotted on its own axis

COL = {"strong": "#1f77b4", "mini": "#ff7f0e", "nano": "#d62728"}
INK = "#1a1a1a"
GREY = "#5a5a5a"
BAND = "#9ecae1"


def load(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def fnum(v):
    return None if v in ("", None) else float(v)


def main() -> int:
    rows = load(PANEL)
    tax = {(r["tier"], r["arm"], int(float(r["budget_CU"]))): r for r in load(TAX)}

    def cells(tier, arm="E", exclude_non_binding=True):
        out = [r for r in rows if r["tier"] == tier and r["arm"] == arm]
        if exclude_non_binding:
            out = [r for r in out if not int(r["is_non_binding_allowance"])]
        return sorted(out, key=lambda r: int(r["budget_CU"]))

    nb = next(r for r in rows if int(r["is_non_binding_allowance"]))

    plt.rcParams.update({
        "font.size": 9, "axes.labelsize": 9, "axes.titlesize": 9,
        "xtick.labelsize": 8, "ytick.labelsize": 8, "legend.fontsize": 7.4,
        "axes.edgecolor": INK, "axes.labelcolor": INK, "text.color": INK,
        "xtick.color": INK, "ytick.color": INK, "axes.linewidth": 0.8,
        "savefig.bbox": "tight", "figure.dpi": 150,
    })

    fig = plt.figure(figsize=(13.6, 4.0))
    gs = fig.add_gridspec(1, 3, wspace=0.50, left=0.050, right=0.988, bottom=0.16, top=0.88)
    axes = []
    for i in range(3):
        sub = gs[0, i].subgridspec(1, 2, width_ratios=[5.2, 1.0], wspace=0.06)
        axes.append((fig.add_subplot(sub[0, 0]), fig.add_subplot(sub[0, 1])))

    def style_pair(ax, axn, ylabel, ylim=None, logy=False):
        for a in (ax, axn):
            a.grid(True, which="major", lw=0.4, color="#d9d9d9", zorder=0)
            a.set_axisbelow(True)
            a.tick_params(direction="out", length=3)
        ax.set_xscale("log")
        ax.set_xlim(42, 470)
        ax.set_xticks([50, 75, 100, 150, 200, 250, 400])
        ax.set_xticklabels(["50", "75", "100", "150", "200", "250", "400"])
        ax.minorticks_off()
        axn.set_xlim(0, 1)
        axn.set_xticks([0.5])
        axn.set_xticklabels(["non-binding\n5000 CU"], fontsize=7.2)
        axn.tick_params(axis="y", labelleft=False, length=0)
        axn.spines["left"].set_linestyle((0, (2, 2)))
        if logy:
            ax.set_yscale("log")
            axn.set_yscale("log")
        if ylim:
            ax.set_ylim(*ylim)
            axn.set_ylim(*ylim)
        ax.set_ylabel(ylabel)
        ax.set_xlabel("compute budget (CU)")

    def vrefs(ax, labels=True):
        ax.axvline(D_THRESHOLD, color=GREY, lw=0.9, ls="--", zorder=1)
        ax.axvline(LOWEST_STABLE, color=COL["strong"], lw=0.9, ls=":", zorder=1)
        if labels:
            ax.annotate("policy D threshold 206 CU", xy=(D_THRESHOLD, 0.985),
                        xycoords=("data", "axes fraction"), xytext=(-3, 0), textcoords="offset points",
                        fontsize=6.8, color=GREY, ha="right", va="top", rotation=90)
            ax.annotate("lowest stable strong budget 75 CU", xy=(LOWEST_STABLE, 0.015),
                        xycoords=("data", "axes fraction"), xytext=(4, 0), textcoords="offset points",
                        fontsize=6.8, color=COL["strong"], ha="left", va="bottom", rotation=90)

    # ---------------------------------------------------------------- panel a
    ax, axn = axes[0]
    style_pair(ax, axn, "P(complete decision)", ylim=(-0.06, 1.09))
    vrefs(ax)
    for tier, marker in (("strong", "o"), ("mini", "s"), ("nano", "^")):
        cs = cells(tier)
        x = [float(r["budget_CU"]) for r in cs]
        y = [float(r["p_complete_decision"]) for r in cs]
        lo = [y[i] - float(cs[i]["ci_lo"]) for i in range(len(cs))]
        hi = [float(cs[i]["ci_hi"]) - y[i] for i in range(len(cs))]
        ax.errorbar(x, y, yerr=[lo, hi], color=COL[tier], marker=marker, ms=4.2, lw=1.3,
                    capsize=2.2, elinewidth=0.8, zorder=3, label=f"{tier} (policy E)")
    y = float(nb["p_complete_decision"])
    axn.errorbar([0.5], [y], yerr=[[y - float(nb["ci_lo"])], [float(nb["ci_hi"]) - y]],
                 color=COL["strong"], marker="o", ms=4.2, capsize=2.2, elinewidth=0.8, zorder=3)
    floor = next(r for r in cells("strong") if int(r["budget_CU"]) == 50)
    ax.annotate("affordability floor at 50 CU\n13/20 complete; winner and\ndecision pair still 20/20",
                xy=(50, float(floor["p_complete_decision"])), xycoords="data",
                xytext=(0.40, 0.235), textcoords="axes fraction",
                fontsize=6.8, color=INK, ha="left", va="bottom",
                arrowprops=dict(arrowstyle="-", lw=0.6, color=GREY,
                                connectionstyle="angle,angleA=0,angleB=90,rad=3"))
    ax.set_title("a   decision recovery and capability boundary", loc="left", fontweight="bold")

    # ---------------------------------------------------------------- panel b
    ax, axn = axes[1]
    style_pair(ax, axn, "fraction of runs using\nnarrow-window allocation", ylim=(-0.06, 1.09))
    vrefs(ax, labels=False)
    for tier, marker in (("strong", "o"), ("mini", "s"), ("nano", "^")):
        cs = [r for r in cells(tier) if r["narrow_window_fraction"] not in ("", None)]
        ax.plot([float(r["budget_CU"]) for r in cs], [float(r["narrow_window_fraction"]) for r in cs],
                color=COL[tier], marker=marker, ms=4.2, lw=1.3, zorder=3, label=f"{tier} (policy E)")
    axn.plot([0.5], [float(nb["narrow_window_fraction"])], color=COL["strong"], marker="o", ms=4.2, zorder=3)
    axw = ax.twinx()
    axw.set_yscale("log")
    axw.set_ylim(380, 40000)
    axw.set_ylabel(f"median smallest window\n(states, of {FULL_DOMAIN:,})", color=GREY)
    axw.tick_params(axis="y", colors=GREY, labelsize=8, direction="out", length=3)
    axw.spines["right"].set_color(GREY)
    wx, wy = [], []
    for r in cells("strong"):
        t = tax.get(("strong", "E", int(float(r["budget_CU"]))))
        v = fnum(t["min_window_states_median"]) if t else None
        if v is not None:
            wx.append(float(r["budget_CU"]))
            wy.append(v)
    axw.scatter(wx, wy, s=16, facecolor="none", edgecolor=GREY, lw=0.9, zorder=2, marker="D")
    axw.axhline(FULL_DOMAIN, color=GREY, lw=0.6, ls="-.", zorder=1)
    axw.annotate(f"full domain {FULL_DOMAIN:,} (no narrowing)", xy=(0.97, FULL_DOMAIN),
                 xycoords=("axes fraction", "data"), xytext=(0, 4), textcoords="offset points",
                 fontsize=6.8, color=GREY, ha="right")
    ax.set_title("b   allocation mechanism", loc="left", fontweight="bold")
    ax.legend(loc="center left", frameon=False, handlelength=1.6, bbox_to_anchor=(0.015, 0.60))
    axw.legend(handles=[Line2D([], [], marker="D", color=GREY, lw=0, mfc="none", ms=4)],
               labels=["median smallest window (right axis)"], loc="center left", frameon=False,
               bbox_to_anchor=(0.015, 0.40), handlelength=1.2, fontsize=7.0, labelcolor=GREY)

    # ---------------------------------------------------------------- panel c
    ax, axn = axes[2]
    style_pair(ax, axn, "CU spent", ylim=(30, 9000), logy=True)
    ax.axvline(D_THRESHOLD, color=GREY, lw=0.9, ls="--", zorder=1)
    ax.axvline(LOWEST_STABLE, color=COL["strong"], lw=0.9, ls=":", zorder=1)
    for a in (ax, axn):
        a.axhline(D_THRESHOLD, color=GREY, lw=0.9, ls="--", zorder=1)
    cs = [r for r in cells("strong") if r["decision_stable_CU_median"] not in ("", None)]
    xs = [float(r["budget_CU"]) for r in cs]
    st = [float(r["decision_stable_CU_median"]) for r in cs]
    fu = [float(r["final_used_CU_median"]) for r in cs]
    for x, s_, f_ in zip(xs, st, fu):
        ax.plot([x, x], [s_, f_], color=BAND, lw=3.2, solid_capstyle="butt", zorder=2)
    ax.plot(xs, st, color=COL["strong"], marker="o", ms=4.2, lw=1.3, zorder=3, label="median decision-stable CU")
    ax.plot(xs, fu, color=INK, marker="v", ms=4.2, lw=1.3, zorder=3, label="median final-used CU")
    s_nb, f_nb = float(nb["decision_stable_CU_median"]), float(nb["final_used_CU_median"])
    axn.plot([0.5, 0.5], [s_nb, f_nb], color=BAND, lw=3.2, solid_capstyle="butt", zorder=2)
    axn.plot([0.5], [s_nb], color=COL["strong"], marker="o", ms=4.2, zorder=3)
    axn.plot([0.5], [f_nb], color=INK, marker="v", ms=4.2, zorder=3)
    nb_max = float(nb["final_used_CU_range"].split("-")[1])
    axn.plot([0.5], [nb_max], color=INK, marker="v", ms=4.6, mfc="none", mew=0.9, zorder=3)
    axn.annotate(f"{nb_max:.0f} CU\n(single run)", xy=(0.5, nb_max), xytext=(0, 7),
                 textcoords="offset points", fontsize=6.6, color=INK, ha="center", va="bottom")
    ax.annotate(f"non-binding allowance: median {f_nb:.0f} CU = {f_nb / D_THRESHOLD:.1f}x D",
                xy=(0.985, 0.96), xycoords="axes fraction", fontsize=6.9, color=INK, ha="right", va="top")
    ax.annotate("206 CU", xy=(0.02, D_THRESHOLD), xycoords=("axes fraction", "data"),
                xytext=(0, 3), textcoords="offset points", fontsize=6.8, color=GREY)
    ax.set_title("c   upper cost boundary", loc="left", fontweight="bold")
    ax.legend(loc="upper left", frameon=False, handlelength=1.6, bbox_to_anchor=(0.015, 0.88))

    OUT.mkdir(parents=True, exist_ok=True)
    written = []
    for ext, kw in (("svg", {}), ("pdf", {}), ("png", {"dpi": 600})):
        f = OUT / f"{STEM}.{ext}"
        fig.savefig(f, **kw)
        written.append(f)
    plt.close(fig)

    man = OUT / "F10_RENDER_SHA256.txt"
    lines = [f"# F10 render manifest - {STEM}",
             "# spec: docs/F10_AGENT_FIGURE_SPEC_AND_ED_SI_PLAN_2026-09-13.md", ""]
    for f in written + [PANEL, TAX, Path(__file__)]:
        h = hashlib.sha256(f.read_bytes()).hexdigest()
        lines.append(f"{h}  {f.relative_to(ROOT).as_posix()}")
    man.write_text("\n".join(lines) + "\n", encoding="utf-8")

    for f in written:
        print(f"wrote {f.relative_to(ROOT).as_posix()}  ({f.stat().st_size:,} bytes)")
    print(f"wrote {man.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
