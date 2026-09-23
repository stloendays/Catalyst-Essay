"""Figure 5 — coupling topology decides whether an upstream ranking reshapes or survives.

Composite, 183 mm wide.
  a  pathway graphs drawn from the two frozen models: NH3 cost pools from
     analysis/supervisor_2026_09_20/nh3_cost_decomposition.csv; MeOH module drivers from
     data/meoh/meoh_d01_v3.json and leverages from data/meoh/meoh_candidate_ranking_D01v3.csv
  b  renders/Au_TiO2_2to6nm.png (build_au_tio2.py)
  c-e data/rank_preservation_control_v1_1.csv, data/rank_preservation_semiopen_v1_3_summary.csv
  f  rank correlations reported for the three systems (NH3-FINAL-1.1, MEOH-D01-v3, control V1.1/V1.3)

    pur_bridge_env/python make_fig5.py            -> Fig5.{svg,pdf,png}
"""
import csv
import json
import os
import sys

import matplotlib.image as mpimg
import numpy as np
from matplotlib.patches import FancyBboxPatch, PathPatch
from matplotlib.path import Path
from matplotlib.ticker import FixedLocator, LogLocator, MultipleLocator, NullFormatter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from style import FE, INK, MID, OS, PALE_B, PALE_G, PAPER, RED, RU, TINT_B, TINT_G, Page, boxed  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))


def read_csv(path):
    return list(csv.DictReader(open(path, encoding="utf-8")))


decomp = {r["cost_pool"]: float(r["Ru_minus_Fe_USD_t"]) for r in
          read_csv(os.path.join(REPO, "analysis/supervisor_2026_09_20/nh3_cost_decomposition.csv"))}
d01 = json.load(open(os.path.join(REPO, "data/meoh/meoh_d01_v3.json"), encoding="utf-8"))
modules = {m["name"]: m["driven_by"] for m in d01["economic_modules"]}
c55 = {r["candidate"]: r for r in read_csv(os.path.join(REPO, "data/meoh/meoh_candidate_ranking_D01v3.csv"))}["5 wt% Re | 250 C"]
au = read_csv(os.path.join(REPO, "data/rank_preservation_control_v1_1.csv"))
semi = read_csv(os.path.join(REPO, "data/rank_preservation_semiopen_v1_3_summary.csv"))
meta = json.load(open(os.path.join(HERE, "renders", "Au_TiO2_2to6nm.json"), encoding="utf-8"))
assert abs(decomp["TOTAL"] - 6.738890111189871) < 1e-9
assert modules["H2_feed"][:3] == ["S_CH4", "S_MeOH", "purge_fraction"]
assert "recycle_flow" in modules["compression"] and "catalyst_mass" in modules["equipment_ACC"]
assert [float(r["diameter_nm"]) for r in au] == [2, 3, 4, 5, 6]

GOLD = ["#E8D291", "#DDBF6C", "#C9A24C", "#A8843B", "#86672D"]
pg = Page(183.0, 164.0)


# ---- helpers for the pathway graphs ------------------------------------------------------------
def node(ax, x, y, w, h, title, sub=None, fc="white", ec=INK, bold=True, color=INK, fs=6.0):
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle="round,pad=0,rounding_size=1.0",
                                fc=fc, ec=ec, lw=0.55, zorder=3))
    if sub:
        ax.text(x, y + 0.95, title, ha="center", va="center", fontsize=fs, fontweight="bold" if bold else "normal",
                color=color, zorder=4)
        ax.text(x, y - 1.35, sub, ha="center", va="center", fontsize=5.3, color=MID, zorder=4)
    else:
        ax.text(x, y, title, ha="center", va="center", fontsize=fs, fontweight="bold" if bold else "normal",
                color=color, zorder=4)
    return (x - w / 2, x + w / 2, y)


def edge(ax, a, b, lw=0.7, color=MID, alpha=1.0):
    """Cubic curve from the right side of node a to the left side of node b."""
    x0, y0, x1, y1 = a[1], a[2], b[0], b[2]
    dx = 0.45 * (x1 - x0)
    path = Path([(x0, y0), (x0 + dx, y0), (x1 - dx, y1), (x1, y1)],
                [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4])
    ax.add_patch(PathPatch(path, fc="none", ec=color, lw=lw, alpha=alpha, zorder=2, capstyle="butt"))


def col_heads(ax, xs, names, y):
    for x, n in zip(xs, names):
        ax.text(x, y, n, ha="center", va="bottom", fontsize=5.6, color=MID, fontweight="bold")


# ---- a: the two pathways -------------------------------------------------------------------------
pg.letter("a", 2.0, 162.0)
pg.title("Catalyst-to-process pathways, each against its own economic objective", 6.0, 162.4)
# NH3: catalyst -> process -> cost pools (Ru - Fe, USD/t) -> decision
g1 = pg.canvas(3.0, 104.0, 92.0, 52.0)
g1.text(0.5, 50.0, "NH$_3$ synthesis: Ru against Fe", fontsize=6.6, fontweight="bold", va="top")
X = [9.5, 32.0, 47.0, 84.0]
col_heads(g1, [X[0], X[1], 59.5, X[3]], ["catalyst", "process", "cost pool, Ru − Fe", "decision"], 44.0)
price = node(g1, X[0], 35.0, 18.0, 5.6, "Metal price", "USD kg$^{-1}$", fc=TINT_B, bold=False, fs=5.8)
act = node(g1, X[0], 23.0, 18.0, 5.6, "Intrinsic activity", "E$_\\mathrm{N}$ → TOF", fc=TINT_B, bold=False, fs=5.8)
inv = node(g1, X[1], 32.0, 20.0, 5.6, "Catalyst inventory", "bed volume", bold=False, fs=5.8)
reg = node(g1, X[1], 14.0, 20.0, 5.6, "Operating regime", "T, P, T$_\\mathrm{sep}$", bold=False, fs=5.8)
pools = [("metal_inventory", "metal inventory", "inv"),
         ("reactor_base", "reactor base", "inv"),
         ("vessel_pressure_premium", "vessel pressure", "both"),
         ("fresh_compression_electricity", "fresh compression", "reg"),
         ("compressor_CAPEX", "compressor capital", "reg"),
         ("refrigeration_electricity", "refrigeration", "reg"),
         ("recycle_compression_electricity", "recycle compression", "reg")]
ypool = np.linspace(39.5, 3.0, len(pools))
dec1 = node(g1, X[3], 21.0, 13.5, 9.0, "Fe first", "Ru − Fe +%.2f" % decomp["TOTAL"], fc="#E4ECDE",
            color="#3F5A36")
edge(g1, price, inv, lw=1.0, color=RU)
edge(g1, act, inv, lw=1.6, color=RU)
XL, XR = X[2], 72.0                                    # pool label start, value end
for (key, name, src), y in zip(pools, ypool):
    v = decomp[key]
    g1.text(XL + 0.6, y, name, ha="left", va="center", fontsize=5.5, zorder=4)
    g1.text(XR, y, ("%+.2f" % v).replace("-", "−"), ha="right", va="center", fontsize=5.5,
            fontweight="bold" if abs(v) > 1 else "normal", zorder=4)
    g1.plot([XL, XR], [y - 2.0, y - 2.0], color="#E4E4E4", lw=0.4, zorder=1)
    for s in ([inv, reg] if src == "both" else [inv if src == "inv" else reg]):
        edge(g1, s, (XL, XL, y), lw=0.5, color="#9097A3")
    edge(g1, (XR, XR + 0.8, y), dec1, lw=0.35 + 0.55 * abs(v), color=RU if v > 0 else FE, alpha=0.85)
# the inventory-regime coupling: a dearer metal buys a smaller bed with pressure
g1.annotate("", xy=(X[1] - 6.0, reg[2] + 2.9), xytext=(X[1] - 6.0, inv[2] - 2.9),
            arrowprops=dict(arrowstyle="<|-|>", lw=0.8, color=RED, mutation_scale=5, shrinkA=0, shrinkB=0))
g1.text(X[1] - 4.8, 23.0, "coupled by\nthe optimizer", fontsize=5.4, color=RED, fontweight="bold", va="center",
        linespacing=1.05)

# MeOH
g2 = pg.canvas(97.0, 104.0, 85.0, 52.0)
g2.text(0.5, 50.0, "CO$_2$ to methanol: four Re/TiO$_2$ states", fontsize=6.6, fontweight="bold", va="top")
X = [9.0, 30.5, 53.5, 75.5]
col_heads(g2, X, ["catalyst", "loop", "cost pool", "decision"], 44.0)
lev = {"S_CH4": float(c55["L_CH4_suppression"]), "X_CO2": float(c55["L_conversion"]), "STY": float(c55["L_STY"])}
sel = node(g2, X[0], 35.0, 17.0, 5.6, "CH$_4$ selectivity", "leverage %.3f" % lev["S_CH4"], fc="#FBE3E3",
           color=RED)
conv = node(g2, X[0], 23.5, 17.0, 5.6, "Conversion", "leverage %.3f" % lev["X_CO2"], fc=TINT_B)
sty = node(g2, X[0], 12.0, 17.0, 5.6, "STY per g Re", "leverage %.4f" % lev["STY"], fc=TINT_B)
ch4 = node(g2, X[1], 37.0, 17.0, 4.6, "CH$_4$ in loop gas", fs=5.6)
rec = node(g2, X[1], 27.5, 17.0, 4.6, "Recycle flow", fs=5.6)
pur = node(g2, X[1], 18.0, 17.0, 4.6, "Purge losses", fs=5.6)
cat = node(g2, X[1], 8.5, 17.0, 4.6, "Catalyst mass", fs=5.6)
h2 = node(g2, X[2], 36.0, 17.0, 4.6, "H$_2$ feed", bold=False, fs=5.6)
co2 = node(g2, X[2], 27.0, 17.0, 4.6, "CO$_2$ feed", bold=False, fs=5.6)
cmp_ = node(g2, X[2], 18.0, 17.0, 4.6, "compression", bold=False, fs=5.6)
eqp = node(g2, X[2], 9.0, 17.0, 4.6, "equipment", bold=False, fs=5.6)
dec2 = node(g2, X[3], 21.0, 14.0, 9.0, "5 wt%, 200 °C", "first of four", fc="#E4ECDE", color="#3F5A36", fs=5.6)
w_of = {k: 0.45 + 2.2 * (np.log10(v) + 3.0) / 2.6 for k, v in lev.items()}
edge(g2, sel, ch4, lw=w_of["S_CH4"], color=RED)
edge(g2, sel, pur, lw=w_of["S_CH4"] * 0.7, color=RED, alpha=0.8)
edge(g2, conv, rec, lw=w_of["X_CO2"], color=RU)
edge(g2, sty, cat, lw=w_of["STY"], color=RU)
for s, t in ((ch4, h2), (pur, h2), (pur, co2), (ch4, cmp_), (rec, cmp_), (rec, eqp), (pur, eqp), (cat, eqp)):
    edge(g2, s, t, lw=0.5, color="#9097A3")
for t in (h2, co2, cmp_, eqp):
    edge(g2, t, dec2, lw=0.6, color="#9097A3")
g2.text(X[2], 1.2, "drivers from the D01 cost modules", fontsize=5.3, color=MID, ha="center", va="bottom")

# ---- b: the Au/TiO2 control, to scale --------------------------------------------------------------
RY = 62.0
pg.letter("b", 2.0, RY + 34.0)
pg.title("Rank-preservation control: Au/TiO$_2$, CO oxidation, 2–6 nm Au", 6.0, RY + 34.4)
img = mpimg.imread(os.path.join(HERE, "renders", "Au_TiO2_2to6nm.png"))
ys_, xs_ = np.where(img[:, :, 3] > 0.02)
x0p, x1p, y0p, y1p = xs_.min(), xs_.max() + 1, ys_.min(), ys_.max() + 1
img = img[y0p:y1p, x0p:x1p]
bw = 118.0
bh = bw * img.shape[0] / img.shape[1]
bx = pg.canvas(3.0, RY + 5.5, bw, bh)
bx.imshow(img, extent=(0, bw, 0, bh), interpolation="lanczos", zorder=2)
sx = bw / img.shape[1]
for d, cx, n_at in zip(meta["diameters_nm"], meta["centre_x_px"], meta["au_atoms"]):
    bx.text((cx - x0p) * sx, -1.4, "%d nm" % d, ha="center", va="top", fontsize=6.3, fontweight="bold")
    bx.text((cx - x0p) * sx, -4.5, "%s Au atoms" % format(n_at, ","), ha="center", va="top", fontsize=5.4,
            color=MID)

# ---- c: activity rank to burden rank, no crossings ---------------------------------------------------
pg.letter("c", 126.0, RY + 34.0)
c = pg.ax(136.0, RY + 1.0, 30.0, 26.0)
c.set_xlim(-0.2, 1.2)
c.set_ylim(5.5, 0.4)
c.axis("off")
act_v = [float(r["mass_activity_umol_CO_gcat_s"]) for r in au]
bur_v = [float(r["procurement_burden_vs_best"]) for r in au]
for i, (r, col) in enumerate(zip(au, GOLD)):
    rank = i + 1
    c.plot([0, 1], [rank, rank], color=col, lw=2.0, solid_capstyle="round", zorder=2)
    c.plot([0, 1], [rank, rank], "o", ms=3.6, mfc=col, mec=INK, mew=0.4, zorder=3)
    c.text(-0.1, rank, "%d nm" % float(r["diameter_nm"]), ha="right", va="center", fontsize=5.9)
    c.text(1.1, rank, "%.3f×" % bur_v[i], ha="left", va="center", fontsize=5.9,
           fontweight="bold" if i == 4 else "normal")
c.text(0, 0.05, "activity", ha="center", va="bottom", fontsize=6.0, fontweight="bold")
c.text(1, 0.05, "burden", ha="center", va="bottom", fontsize=6.0, fontweight="bold")
c.text(0.5, 5.95, "ρ = τ = 1.000, no inversions", ha="center", va="top", fontsize=5.9, fontweight="bold")
c.text(0.5, 6.75, "order kept in 10,000 / 10,000 draws", ha="center", va="top", fontsize=5.6, color=MID)

# ---- d: mass activity and required catalyst ----------------------------------------------------------
LY, LH = 12.0, 32.0
pg.letter("d", 2.0, LY + LH + 7.0)
d = pg.ax(14.0, LY, 40.0, LH)
boxed(d)
dia = np.array([float(r["diameter_nm"]) for r in au])
req = np.array([float(r["required_catalyst_mass_mg"]) for r in au])
d.plot(dia, act_v, color=INK, lw=0.9, zorder=2)
d.scatter(dia, act_v, s=16, c=GOLD, edgecolors=INK, linewidths=0.4, zorder=3)
d.set_yscale("log")
d.set_ylim(0.8, 15)
d.set_ylabel(r"Mass activity (µmol g$^{-1}$ s$^{-1}$)")
d.set_xlabel("Au diameter (nm)")
d.set_xlim(1.5, 6.5)
d.xaxis.set_major_locator(FixedLocator([2, 3, 4, 5, 6]))
d.yaxis.set_major_locator(FixedLocator([1, 2, 5, 10]))
d.set_yticklabels(["1", "2", "5", "10"])
d.yaxis.set_minor_formatter(NullFormatter())
d2 = d.twinx()
d2.plot(dia, req, color=MID, lw=0.9, ls=(0, (3, 1.6)), zorder=2)
d2.scatter(dia, req, s=14, marker="s", c="white", edgecolors=MID, linewidths=0.6, zorder=3)
d2.set_yscale("log")
d2.set_ylim(12, 250)
d2.yaxis.set_major_locator(FixedLocator([20, 50, 100, 200]))
d2.set_yticklabels(["20", "50", "100", "200"])
d2.yaxis.set_minor_formatter(NullFormatter())
d2.set_ylabel("Required catalyst (mg)", color=MID)
d2.tick_params(axis="y", colors=MID, which="both", direction="in")
d2.spines["right"].set_color(MID)
d.text(2.25, 11.5, "mass activity", fontsize=5.6, va="center")
d2.text(5.05, 62, "required\ncatalyst", fontsize=5.6, va="center", ha="left", color=MID, linespacing=1.05)

# ---- e: semi-open robustness ---------------------------------------------------------------------------
pg.letter("e", 70.0, LY + LH + 7.0)
e = pg.ax(82.0, LY, 38.0, LH)
boxed(e)
stress = ["mild", "moderate", "strong"]
win = {"primary_273_293K": ("273–293 K", "#7789B7"), "sensitivity_273_313K": ("273–313 K", "#C6CCDC")}
xb = np.arange(3)
for j, (key, (lab_, col)) in enumerate(win.items()):
    vals = [100 * float(next(r for r in semi if r["window"] == key and r["stress"] == s)["full_preservation_fraction"])
            for s in stress]
    e.bar(xb + (j - 0.5) * 0.36, vals, width=0.34, color=col, ec=INK, lw=0.45, zorder=3, label=lab_)
    for x_, v in zip(xb + (j - 0.5) * 0.36, vals):
        e.text(x_, v + 1.5, "%.1f" % v, ha="center", va="bottom", fontsize=5.0, rotation=90)
e.axhline(100, color=INK, lw=0.5, ls=(0, (2, 1.5)))
e.set_xticks(xb)
e.set_xticklabels(["mild", "moderate", "strong"], fontsize=6.0)
e.tick_params(axis="x", length=0)
e.set_ylim(0, 128)
e.yaxis.set_major_locator(FixedLocator([0, 25, 50, 75, 100]))
e.set_ylabel("Exact order kept (%)")
e.set_xlabel("Candidate-specific freedom")
e.legend(loc="upper right", fontsize=5.4, handlelength=1.0, handletextpad=0.4, borderaxespad=0.2, ncol=2,
         columnspacing=0.8)

# ---- f: rank fidelity across the three systems -----------------------------------------------------------
pg.letter("f", 124.0, LY + LH + 7.0)
f = pg.ax(151.0, LY, 30.0, LH)
boxed(f)
rows = [("NH$_3$, all 15 metals", 0.929, None, INK),
        ("NH$_3$, frontier top 3", -0.50, None, RED),
        ("MeOH, 4 states", 0.20, (-0.6, 0.4), INK),
        ("Au/TiO$_2$, 5 sizes", 1.000, None, INK),
        ("Au, semi-open mean", 0.99214, None, MID)]
for i, (name, v, rng_, col) in enumerate(rows):
    if rng_:
        f.plot(rng_, [i, i], color=OS, lw=2.4, solid_capstyle="round", zorder=2)
    f.plot(v, i, "o", ms=4.0, mfc=col if col != MID else "white", mec=INK if col != MID else MID, mew=0.6, zorder=3)
f.axvline(0, color=MID, lw=0.5, ls=(0, (2, 1.5)))
f.set_yticks(range(len(rows)))
f.set_yticklabels([r[0] for r in rows], fontsize=5.8)
for t, r in zip(f.get_yticklabels(), rows):
    if r[3] == RED:
        t.set_color(RED)
        t.set_fontweight("bold")
f.tick_params(axis="y", length=0)
f.set_ylim(len(rows) - 0.4, -0.6)
f.set_xlim(-1.05, 1.1)
f.xaxis.set_major_locator(FixedLocator([-1, 0, 1]))
f.xaxis.set_minor_locator(MultipleLocator(0.25))
f.set_xlabel("Upstream → downstream ρ")
f.text(-0.62, 2.42, "purge 0.5–40%", fontsize=5.0, color=MID, va="top", ha="center")

pg.save(HERE, "Fig5")
