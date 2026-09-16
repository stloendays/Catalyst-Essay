#!/usr/bin/env python3
"""Render Extended Data Figures 1-3 for the Agent line.

Allocation fixed in docs/F10_AGENT_FIGURE_SPEC_AND_ED_SI_PLAN_2026-09-13.md section 3.
Metric definitions fixed by docs/AGENT_METRIC_DEFINITIONS_SOURCE_OF_TRUTH_2026-09-13.md.

RENDERING ONLY. Every plotted value is read from committed CSVs; nothing is hand-entered.
  ED1  data/discover_boundary_c1_decision_components.csv + data/discover_boundary_c1_error_taxonomy_summary.csv
  ED2  data/discover_boundary_c1_error_taxonomy_summary.csv
  ED3  data/discover_boundary_c1_uncapped_breakeven_audit.csv

Usage (from the repository root):
  python figures/agent/render_ED_agent_panels.py
"""
from __future__ import annotations
import csv
import hashlib
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
OUT = ROOT / "figures" / "agent"
COMP = DATA / "discover_boundary_c1_decision_components.csv"
TAX = DATA / "discover_boundary_c1_error_taxonomy_summary.csv"
AUDIT = DATA / "discover_boundary_c1_uncapped_breakeven_audit.csv"

COL = {"strong": "#1f77b4", "mini": "#ff7f0e", "nano": "#d62728"}
INK, GREY, BAND = "#1a1a1a", "#5a5a5a", "#9ecae1"
D_THRESHOLD = 206.0


def load(p: Path) -> list[dict]:
    with p.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def style():
    plt.rcParams.update({
        "font.size": 9, "axes.labelsize": 9, "axes.titlesize": 9, "legend.fontsize": 7.6,
        "xtick.labelsize": 8, "ytick.labelsize": 8, "axes.edgecolor": INK, "axes.labelcolor": INK,
        "text.color": INK, "xtick.color": INK, "ytick.color": INK, "axes.linewidth": 0.8,
        "savefig.bbox": "tight", "figure.dpi": 150,
    })


def save(fig, stem: str) -> list[Path]:
    OUT.mkdir(parents=True, exist_ok=True)
    out = []
    for ext, kw in (("svg", {}), ("pdf", {}), ("png", {"dpi": 600})):
        f = OUT / f"{stem}.{ext}"
        fig.savefig(f, **kw)
        out.append(f)
    plt.close(fig)
    return out


# ------------------------------------------------------------------ ED1
def ed1(comp, tax):
    c = {(r["tier"], r["arm"], int(r["budget_CU"])): r for r in comp}
    t = {(r["tier"], r["arm"], int(float(r["budget_CU"]))): r for r in tax}
    e, e2 = c[("mini", "E", 175)], c[("mini", "E2", 175)]
    te, te2 = t[("mini", "E", 175)], t[("mini", "E2", 175)]
    n = int(e["n"])

    chain = ["k_built_window", "k_winner", "k_ran_BACKWARD", "k_ran_TEST_REACHABILITY", "k_complete_decision"]
    chain_lab = ["built a\nprocess window", "correct\nwinner", "ran\nBACKWARD", "classified\nreachability", "complete\ndecision"]
    errs = [("interface", "interface"), ("no_tool_call_turns", "no tool call"), ("budget", "budget"),
            ("sequencing", "sequencing"), ("premature_OPTIMIZE", "premature\nOPTIMIZE")]

    fig, axes = plt.subplots(1, 2, figsize=(9.6, 3.5), gridspec_kw={"wspace": 0.30})

    ax = axes[0]
    x = range(len(chain))
    w = 0.38
    ax.bar([i - w / 2 for i in x], [int(e[k]) for k in chain], w, color=GREY, label="frozen interface (E)")
    ax.bar([i + w / 2 for i in x], [int(e2[k]) for k in chain], w, color=COL["mini"], label="typed + budget-aware (E2)")
    ax.set_xticks(list(x))
    ax.set_xticklabels(chain_lab, fontsize=7.2)
    ax.set_ylim(0, n * 1.18)
    ax.set_ylabel(f"runs (of {n})")
    ax.set_title("a   decision chain, mini at 175 CU", loc="left", fontweight="bold")
    ax.legend(frameon=False, loc="upper right")
    ax.grid(True, axis="y", lw=0.4, color="#d9d9d9")
    ax.set_axisbelow(True)
    for i, k in enumerate(chain):
        for off, r in ((-w / 2, e), (w / 2, e2)):
            v = int(r[k])
            ax.annotate(str(v), (i + off, v), ha="center", va="bottom", fontsize=6.8, xytext=(0, 1.5),
                        textcoords="offset points")

    ax = axes[1]
    x = range(len(errs))
    ax.bar([i - w / 2 for i in x], [int(te[k]) for k, _ in errs], w, color=GREY, label="frozen interface (E)")
    ax.bar([i + w / 2 for i in x], [int(te2[k]) for k, _ in errs], w, color=COL["mini"], label="typed + budget-aware (E2)")
    ax.set_xticks(list(x))
    ax.set_xticklabels([lab for _, lab in errs], fontsize=7.2)
    ax.set_ylabel("count over the cell")
    ax.set_title("b   where the failures moved", loc="left", fontweight="bold")
    ax.grid(True, axis="y", lw=0.4, color="#d9d9d9")
    ax.set_axisbelow(True)
    for i, (k, _) in enumerate(errs):
        for off, r in ((-w / 2, te), (w / 2, te2)):
            v = int(r[k])
            ax.annotate(str(v), (i + off, v), ha="center", va="bottom", fontsize=6.8, xytext=(0, 1.5),
                        textcoords="offset points")
    return save(fig, "ED1_mini_interface_intervention")


# ------------------------------------------------------------------ ED2
def ed2(tax):
    rows = [r for r in tax if r["arm"] == "E" and int(float(r["budget_CU"])) != 5000]
    order = {"strong": 0, "mini": 1, "nano": 2}
    rows.sort(key=lambda r: (order[r["tier"]], int(float(r["budget_CU"]))))
    labels = [f"{r['tier']}\n{int(float(r['budget_CU']))}" for r in rows]
    iface = [int(r["interface"]) for r in rows]
    budg = [int(r["budget"]) for r in rows]
    seq = [int(r["sequencing"]) for r in rows]

    fig, ax = plt.subplots(figsize=(9.6, 3.4))
    x = range(len(rows))
    ax.bar(x, iface, 0.68, label="interface", color="#6baed6")
    ax.bar(x, budg, 0.68, bottom=iface, label="budget", color="#fd8d3c")
    ax.bar(x, seq, 0.68, bottom=[i + b for i, b in zip(iface, budg)], label="sequencing", color="#74c476")
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, fontsize=7.0)
    ax.set_ylabel("0-CU action errors")
    ax.set_xlabel("tier and compute budget (CU)")
    ax.set_title("Failure mechanism by tier and budget (frozen interface)", loc="left", fontweight="bold")
    ax.legend(frameon=False, ncol=3, loc="upper left")
    ax.grid(True, axis="y", lw=0.4, color="#d9d9d9")
    ax.set_axisbelow(True)
    for i, r in enumerate(rows):
        tot = int(r["action_errors"])
        if tot:
            ax.annotate(str(tot), (i, tot), ha="center", va="bottom", fontsize=6.8, xytext=(0, 2),
                        textcoords="offset points", color=INK)
    return save(fig, "ED2_failure_mechanism_by_tier")


# ------------------------------------------------------------------ ED3
def ed3(audit):
    rows = sorted(audit, key=lambda r: float(r["final_CU"]))
    stable = [float(r["first_stable_CU"]) for r in rows]
    final = [float(r["final_CU"]) for r in rows]
    y = range(len(rows))

    fig, ax = plt.subplots(figsize=(7.6, 4.2))
    for i, (s, f) in enumerate(zip(stable, final)):
        ax.plot([s, f], [i, i], color=BAND, lw=3.0, solid_capstyle="butt", zorder=2)
    ax.scatter(stable, list(y), s=26, color=COL["strong"], zorder=3, label="decision-stable CU")
    ax.scatter(final, list(y), s=26, color=INK, marker="v", zorder=3, label="final spend")
    ax.axvline(D_THRESHOLD, color=GREY, ls="--", lw=0.9, zorder=1)
    ax.annotate("policy D threshold 206 CU", xy=(D_THRESHOLD, len(rows) - 0.5), xytext=(4, 0),
                textcoords="offset points", fontsize=6.9, color=GREY, va="top")
    ax.set_xscale("log")
    ax.set_yticks(list(y))
    ax.set_yticklabels([f"r{r['run_index']}" for r in rows], fontsize=6.6)
    ax.set_xlabel("CU spent")
    ax.set_ylabel("run")
    ax.set_title("Per-run decision-stable versus final spend, non-binding 5000-CU allowance",
                 loc="left", fontweight="bold", fontsize=9)
    ax.legend(frameon=False, loc="lower right")
    ax.grid(True, axis="x", lw=0.4, color="#d9d9d9")
    ax.set_axisbelow(True)
    return save(fig, "ED3_non_binding_per_run_spread")


def main() -> int:
    style()
    comp, tax, audit = load(COMP), load(TAX), load(AUDIT)
    written = ed1(comp, tax) + ed2(tax) + ed3(audit)
    man = OUT / "ED_RENDER_SHA256.txt"
    lines = ["# Extended Data Agent panels render manifest",
             "# spec: docs/F10_AGENT_FIGURE_SPEC_AND_ED_SI_PLAN_2026-09-13.md section 3", ""]
    for f in written + [COMP, TAX, AUDIT, Path(__file__)]:
        lines.append(f"{hashlib.sha256(f.read_bytes()).hexdigest()}  {f.relative_to(ROOT).as_posix()}")
    man.write_text("\n".join(lines) + "\n", encoding="utf-8")
    for f in written:
        print(f"wrote {f.relative_to(ROOT).as_posix()}")
    print(f"wrote {man.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
