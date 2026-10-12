"""boundary_curve.png / .svg from boundary_curve.csv (run_boundary.py).

a: groups whose STY leader is not the plant-cost leader, and those with a regret above 5 %, against the limit on the
   reactor-inlet non-H2/CO2 fraction; bands are the paper-cluster bootstrap 95 % intervals; S5 (no limit) is the
   unconstrained end; S6 (6.86 %) is marked; the span of published CO2-to-methanol loop designs is shaded.
b: the same disagreements split into ordinary (regret <= 1 and STY leader <= 2x its S5 cost) with a regret <= 5 % or
   > 5 %, and near-infeasible STY leaders.
"""
import sys

import numpy as np
import pandas as pd

from common import HERE, PUBLISHED_RANGE, REPO

sys.path.insert(0, str(REPO / "figures" / "composite"))
import style as S  # noqa: E402  (shared visual system; matplotlib with the Agg backend)
import matplotlib.pyplot as plt  # noqa: E402

X_NONE = 36.0          # x position of S5, the unconstrained end, after an axis break


def xpos(c):
    return np.where(c.limit_pct.notna(), c.limit_pct, X_NONE)


def main():
    c = pd.read_csv(HERE / "boundary_curve.csv")
    c = c[c.on_curve].copy()
    c["x"] = xpos(c)
    lim = c[c.scenario.str.startswith("lim")].sort_values("x")
    s6, s5 = c[c.scenario == "S6"].iloc[0], c[c.scenario == "S5"].iloc[0]
    n = int(c.groups.iloc[0])

    page = S.Page(183, 72)
    ax = page.ax(14, 11, 92, 56)
    bx = page.ax(127, 11, 52, 56)

    # ---- a
    lo_pub, hi_pub = (100 * v for v in PUBLISHED_RANGE)
    ax.axvspan(lo_pub, hi_pub, color=S.TINT_G, lw=0, zorder=0)
    ax.text((lo_pub + hi_pub) / 2, n * 0.985, "published\nloop designs", ha="center", va="top", fontsize=6,
            color=S.DARK_G)
    series = (("fraction", "different leader", S.DARK_B, S.PALE_B, "o"),
              ("gt5pct_fraction", "regret > 5 %", S.RED, "#F6C9C9", "s"))
    for key, label, col, band, mk in series:
        lo, hi = ("fraction_ci_lo", "fraction_ci_hi") if key == "fraction" else ("gt5pct_ci_lo", "gt5pct_ci_hi")
        ax.fill_between(lim.x, n * lim[lo], n * lim[hi], color=band, alpha=0.55, lw=0, zorder=1)
        ax.plot(lim.x, n * lim[key], color=col, lw=1.0, marker=mk, ms=3.0, zorder=3, label=label)
        # S5 at the unconstrained end, with its interval
        ax.errorbar([X_NONE], [n * s5[key]], yerr=[[n * (s5[key] - s5[lo])], [n * (s5[hi] - s5[key])]],
                    color=col, marker=mk, ms=3.0, lw=0.8, capsize=1.8, zorder=3)
        ax.plot([lim.x.iloc[-1], X_NONE], [n * lim[key].iloc[-1], n * s5[key]], color=col, lw=0.8, ls=":", zorder=2)
        ax.plot([s6.x], [n * s6[key]], marker="D", ms=3.6, mfc="white", mec=col, mew=0.9, ls="none", zorder=4)
    ax.annotate("S6", (s6.x, n * s6.fraction), xytext=(s6.x + 0.9, n * s6.fraction + 3.0), fontsize=6,
                arrowprops=dict(arrowstyle="-", lw=0.5, color=S.INK))
    ax.text(X_NONE + 0.9, n * s5.fraction + 0.6, "S5", ha="left", va="bottom", fontsize=6)
    ax.set_xlim(2, X_NONE + 2.5)
    ticks = [4, 6, 8, 10, 12, 15, 20, 25, 30, X_NONE]
    ax.set_xticks(ticks)
    ax.set_xticklabels([f"{t:g}" for t in ticks[:-1]] + ["none"])
    # axis break between 30 % and "none"
    for xb in (32.6, 33.4):
        ax.plot([xb - 0.35, xb + 0.35], [-1.6, 1.6], color=S.INK, lw=0.6, clip_on=False, zorder=5)
    ax.set_ylim(0, n)
    ax.set_yticks(range(0, n + 1, 10))
    ax.set_xlabel("Limit on the reactor-inlet non-H$_2$/CO$_2$ fraction (%)")
    ax.set_ylabel(f"Comparison groups (of {n})")
    ax.legend(loc="lower left", fontsize=6, handlelength=2.0, borderaxespad=0.4)
    S.boxed(ax)

    # ---- b
    order = list(lim.scenario[:3]) + ["S6"] + list(lim.scenario[3:]) + ["S5"]
    d = c.set_index("scenario").loc[order]
    ordinary_le5 = d.ordinary - d.ordinary_gt5pct
    y = np.arange(len(order))
    bx.barh(y, ordinary_le5, color=S.PALE_B, height=0.68, label="ordinary, regret ≤ 5 %")
    bx.barh(y, d.ordinary_gt5pct, left=ordinary_le5, color=S.DARK_B, height=0.68, label="ordinary, regret > 5 %")
    bx.barh(y, d.near_infeasible, left=d.ordinary, color=S.RED, height=0.68, label="near-infeasible STY leader")
    bx.set_yticks(y)
    bx.set_yticklabels([s.replace("lim", "") + (" %" if s.startswith("lim") else "") if s != "S6" else "6.86 % (S6)"
                        for s in order[:-1]] + ["none (S5)"])
    bx.invert_yaxis()
    bx.set_xlim(0, n)
    bx.set_xticks(range(0, n + 1, 10))
    bx.set_xlabel("Groups with a different leader")
    bx.legend(loc="lower right", fontsize=5.6, handlelength=1.2, borderaxespad=0.3)
    S.boxed(bx)

    page.letter("a", 1, 71)
    page.letter("b", 110, 71)
    for ext in ("png", "svg"):
        page.fig.savefig(HERE / f"boundary_curve.{ext}", dpi=600, facecolor="white")
    print("wrote boundary_curve.{png,svg}")


if __name__ == "__main__":
    main()
