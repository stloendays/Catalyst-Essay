#!/usr/bin/env python3
"""Render Extended Data Figure 4 for the Agent line: DISCOVER-V2-STOP stopping arms against the frozen C1 cells.

RENDERING ONLY. Every plotted value is read from committed CSVs; nothing is hand-entered.
  ED4  data/discover_v2_stop/v2_stop_runs_2026-09-26.csv   (180 V2-STOP runs, frozen scorer V1)
       data/discover_boundary_c1_overrun_runs.csv          (frozen C1 policy-E cells of the same model: spend, completion)
       data/discover_boundary_c1_error_taxonomy_runs.csv   (same cells: canonical narrow-window use)

Panel a: per-run final spend for the frozen protocol (C1) and the three stopping arms at 75, 225 and 5,000 CU,
         with cell medians; complete-decision count per cell in the margin.
Panel b: runs using a narrow process window, and runs paying for any action after the S1-S3 rule first held.

Usage (from the repository root):
  python figures/agent/render_ED4_v2stop.py
Appends its own entries to figures/agent/ED_RENDER_SHA256.txt (replacing earlier ED4 entries) without touching
the ED1-ED3 entries written by render_ED_agent_panels.py.
"""
from __future__ import annotations
import csv
import hashlib
import statistics as st
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.ticker
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
V2 = ROOT / "data" / "discover_v2_stop" / "v2_stop_runs_2026-09-26.csv"
C1 = ROOT / "data" / "discover_boundary_c1_overrun_runs.csv"
C1TAX = ROOT / "data" / "discover_boundary_c1_error_taxonomy_runs.csv"
OUT = ROOT / "figures" / "agent"
INK, GREY = "#1a1a1a", "#5a5a5a"
COL = {"C1": "#7f7f7f", "hard": "#d62728", "gate": "#1f77b4", "anytime": "#2ca02c"}
LAB = {"C1": "frozen V1 protocol (C1)", "hard": "S-hard: forced stop", "gate": "S-gate: flip-capable actions only",
       "anytime": "S-anytime: prompt-only scoping"}
CELLS = (75.0, 225.0, 5000.0)


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


def groups(v2: list[dict], c1: list[dict]) -> dict:
    g = {}
    narrow = {r["run_dir"]: int(r["narrow_window_canonical"]) for r in load(C1TAX) if r["tier"] == "strong" and r["arm"] == "E"}
    for r in c1:
        if r["tier"] != "strong" or r["arm"] != "E":
            continue
        b = float(r["budget_CU"])
        if b in CELLS:
            g.setdefault(("C1", b), []).append({"spent": float(r["final_used_CU"]), "full": int(r["full_decision_correct"]),
                                                "narrow": narrow[r["run_dir"]], "post": None})
    for r in v2:
        b = float(r["budget_CU"])
        g.setdefault((r["arm"], b), []).append({"spent": float(r["spent_CU"]), "full": int(r["full_decision_correct"]),
                                                "narrow": int(r["narrow_window"]),
                                                "post": float(r["post_arm_CU"]) if r["post_arm_CU"] else None})
    return g


def ed4(g: dict) -> list[Path]:
    order = ["C1", "hard", "gate", "anytime"]
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(10.4, 4.6), gridspec_kw={"width_ratios": [2.1, 1.0], "wspace": 0.42})
    rows = []
    y = 0
    for b in CELLS[::-1]:
        for k in order[::-1]:
            rs = g[(k, b)]
            rows.append((y, k, b, rs))
            y += 1
        y += 1.7
    import random
    rng = random.Random(20260926)
    for yy, k, b, rs in rows:
        xs = [r["spent"] for r in rs]
        jitter = [yy + rng.uniform(-0.22, 0.22) for _ in xs]
        ax.scatter(xs, jitter, s=14, color=COL[k], alpha=0.75, lw=0, zorder=3)
        med = st.median(xs)
        ax.plot([med, med], [yy - 0.36, yy + 0.36], color=INK, lw=1.6, zorder=4)
        ax.text(6200, yy, f"{sum(r['full'] for r in rs)}/{len(rs)}", va="center", ha="left", fontsize=7.2, color=INK)
    ax.set_xscale("log")
    ax.set_xlim(28, 9000)
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}"))
    ax.set_yticks([yy for yy, *_ in rows])
    ax.set_yticklabels([LAB[k].split(":")[0] for _, k, _, _ in rows], fontsize=7.4)
    tops = {}
    for yy, k, b, rs in rows:
        tops[b] = max(tops.get(b, -1), yy)
    for b in CELLS:
        ax.text(30, tops[b] + 0.85, f"{b:.0f}-CU allowance", fontsize=7.6, fontweight="bold", va="center", ha="left", color=GREY)
        ax.axvline(b, color=GREY, ls=":", lw=0.7, zorder=1)
    ax.text(6200, max(yy for yy, *_ in rows) + 0.85, "complete", fontsize=7.2, color=INK, ha="left", va="center")
    ax.set_xlabel("final spend (CU, log scale); bar = cell median")
    ax.set_title("Final spend per run: frozen protocol versus the three stopping arms", loc="left",
                 fontweight="bold", fontsize=9)
    ax.grid(True, axis="x", lw=0.4, color="#d9d9d9")
    ax.set_axisbelow(True)
    ax.set_ylim(-0.8, max(yy for yy, *_ in rows) + 1.5)

    # panel b: narrow-window use and post-rule paying runs
    w = 0.19
    xs = range(len(CELLS))
    for i, k in enumerate(order):
        narrow = [sum(r["narrow"] for r in g[(k, b)]) for b in CELLS]
        bx.bar([x + (i - 1.5) * w for x in xs], narrow, w, color=COL[k], label=LAB[k])
    bx.set_xticks(list(xs))
    bx.set_xticklabels([f"{b:.0f} CU" for b in CELLS])
    bx.set_ylabel("runs of 20 using a narrow process window")
    bx.set_ylim(0, 27)
    bx.set_yticks(range(0, 21, 5))
    bx.set_title("Narrow-window use", loc="left", fontweight="bold", fontsize=9)
    bx.legend(frameon=False, loc="upper right", fontsize=6.8)
    post = {k: [sum(1 for r in g[(k, b)] if (r["post"] or 0) > 0) for b in CELLS] for k in order[1:]}
    print("runs paying after the rule first held:", {k: dict(zip([f"{b:.0f}" for b in CELLS], v)) for k, v in post.items()})
    bx.grid(True, axis="y", lw=0.4, color="#d9d9d9")
    bx.set_axisbelow(True)
    for a, letter in ((ax, "a"), (bx, "b")):
        a.text(-0.02 if a is bx else -0.16, 1.04, letter, transform=a.transAxes, fontsize=11, fontweight="bold")

    OUT.mkdir(parents=True, exist_ok=True)
    out = []
    for ext, kw in (("svg", {}), ("pdf", {}), ("png", {"dpi": 600})):
        f = OUT / f"ED4_v2stop_stopping_arms.{ext}"
        fig.savefig(f, **kw)
        out.append(f)
    plt.close(fig)
    return out


def main() -> int:
    style()
    g = groups(load(V2), load(C1))
    for k in ("C1", "hard", "gate", "anytime"):
        for b in CELLS:
            assert len(g[(k, b)]) == 20, (k, b, len(g[(k, b)]))
    written = ed4(g)
    man = OUT / "ED_RENDER_SHA256.txt"
    keep = [ln for ln in man.read_text(encoding="utf-8").splitlines()
            if "ED4_" not in ln and "discover_v2_stop" not in ln and "render_ED4" not in ln and ln.strip() != "# ED4 (DISCOVER-V2-STOP), appended by render_ED4_v2stop.py"]
    lines = keep + ["# ED4 (DISCOVER-V2-STOP), appended by render_ED4_v2stop.py"]
    for f in written + [V2, C1, C1TAX, Path(__file__)]:
        lines.append(f"{hashlib.sha256(f.read_bytes()).hexdigest()}  {f.relative_to(ROOT).as_posix()}")
    man.write_text("\n".join(lines) + "\n", encoding="utf-8")
    for f in written:
        print(f"wrote {f.relative_to(ROOT).as_posix()}")
    print(f"updated {man.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
