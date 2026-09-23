"""Figure 4 — methanol catalyst states re-rank through a selectivity-recycle pathway.

Composite, 183 mm wide. Frozen MEOH-D01-v3 data only:
  data/meoh/meoh_candidate_ranking_D01v3.csv     measured catalyst metrics, loop state and NPC at 2 % purge
  data/meoh/meoh_purge_robustness_D01v3.csv      396 purge levels, 0.5-40 %
  analysis/supervisor_2026_09_20/meoh_rank_probability_matrix.csv   5,000-draw rank probabilities
Re/TiO2 renders from build_re_tio2.py.

    pur_bridge_env/python make_fig4.py            -> Fig4.{svg,pdf,png}
"""
import csv
import os
import sys

import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, FancyBboxPatch, Polygon, Rectangle
from matplotlib.ticker import FixedLocator, LogLocator, MultipleLocator, NullFormatter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from style import INK, LINE, MID, PALE_B, PAPER, RED, Page, boxed, crop_rgba  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))


def read_csv(path):
    return list(csv.DictReader(open(path, encoding="utf-8")))


cand = {r["candidate"]: r for r in read_csv(os.path.join(REPO, "data/meoh/meoh_candidate_ranking_D01v3.csv"))}
purge = read_csv(os.path.join(REPO, "data/meoh/meoh_purge_robustness_D01v3.csv"))
rankp = read_csv(os.path.join(REPO, "analysis/supervisor_2026_09_20/meoh_rank_probability_matrix.csv"))
assert len(purge) == 396

KEY = {"1wtRe_200C": "1 wt% Re | 200 C", "5wtRe_200C": "5 wt% Re | 200 C",
       "1wtRe_250C": "1 wt% Re | 250 C", "5wtRe_250C": "5 wt% Re | 250 C"}
LABEL = {"1wtRe_200C": "1 wt%, 200 °C", "5wtRe_200C": "5 wt%, 200 °C",
         "1wtRe_250C": "1 wt%, 250 °C", "5wtRe_250C": "5 wt%, 250 °C"}
SHORT = {k: v.replace(" wt%", "%") for k, v in LABEL.items()}
COLOR = {"1wtRe_200C": "#ACBF9F", "5wtRe_200C": "#6E8E62", "1wtRe_250C": "#9DACCB", "5wtRe_250C": "#56679A"}
WIN = "5wtRe_200C"                                                          # upstream #3, economic #1
ECON = sorted(KEY, key=lambda k: int(cand[KEY[k]]["economic_rank"]))        # rows, economic rank 1..4
UP = sorted(KEY, key=lambda k: int(cand[KEY[k]]["rank_STY_per_gRe"]))
assert ECON == ["5wtRe_200C", "1wtRe_200C", "1wtRe_250C", "5wtRe_250C"]
assert UP == ["1wtRe_250C", "1wtRe_200C", "5wtRe_200C", "5wtRe_250C"]
for r in rankp:
    assert float(r["rank_%d" % (ECON.index(r["candidate"]) + 1)]) == 1.0, "rank matrix is not the identity"
assert len(rankp) == 8

pg = Page(183.0, 168.0)

# ---- a: CO2-to-methanol loop -------------------------------------------------------------
pg.letter("a", 2.0, 166.0)
a = pg.canvas(4.0, 112.0, 104.0, 52.0)
a.text(1.5, 50.0, "CO$_2$-to-methanol loop", fontsize=7, fontweight="bold", va="top")
y0 = 20.0
arrow = dict(arrowstyle="-|>", lw=0.7, color=INK, mutation_scale=5.5, shrinkA=0, shrinkB=0)


def line(xs, ys):
    a.plot(xs, ys, color=INK, lw=0.7, solid_capstyle="butt", zorder=2)


def flow(x0, y0_, x1, y1, color=INK):
    a.annotate("", xy=(x1, y1), xytext=(x0, y0_), arrowprops=dict(arrow, color=color), zorder=2)


def compressor(xc, yc, w=7.0, h1=8.4, h2=4.4, left_wide=True):
    x0, x1 = (xc - w / 2, xc + w / 2) if left_wide else (xc + w / 2, xc - w / 2)
    a.add_patch(Polygon([[x0, yc - h1 / 2], [x0, yc + h1 / 2], [x1, yc + h2 / 2], [x1, yc - h2 / 2]],
                        closed=True, fc="white", ec=INK, lw=0.8, zorder=3))


def label(x, y, head, sub=None, ha="center"):
    a.text(x, y, head, ha=ha, va="top", fontsize=6.2, fontweight="bold", linespacing=1.05)
    if sub:
        n = head.count("\n") + 1
        a.text(x, y - 2.5 * n - 0.5, sub, ha=ha, va="top", fontsize=5.5, color=MID, linespacing=1.12)


a.text(0.5, y0 + 1.8, "CO$_2$ + H$_2$", fontsize=5.8, va="bottom")
flow(0.5, y0, 9.5, y0)
compressor(13.0, y0)
label(13.0, y0 - 5.8, "Feed\ncompressor", "feed gas,\nelectricity")
xm = 22.0
flow(16.5, y0, xm - 0.2, y0)
a.add_patch(Circle((xm, y0), 0.75, fc=INK, ec="none", zorder=4))
xr, wr, hr = 32.5, 9.0, 22.0
flow(xm, y0, xr - wr / 2, y0)
a.add_patch(FancyBboxPatch((xr - wr / 2, y0 - hr / 2), wr, hr, boxstyle="round,pad=0,rounding_size=3.2",
                           fc="white", ec=INK, lw=0.9, zorder=3))
rng = np.random.default_rng(5)
px = rng.uniform(xr - wr / 2 + 1.1, xr + wr / 2 - 1.1, 140)
py = rng.uniform(y0 - hr / 2 + 3.0, y0 + hr / 2 - 4.0, 140)
a.scatter(px, py, s=3.2, c="#B9C1D3", edgecolors="#8B9098", linewidths=0.2, zorder=4)
label(xr, y0 - hr / 2 - 1.3, "Reactor", "Re/TiO$_2$")
a.text(xr + wr / 2 + 1.0, y0 + 2.2, "CH$_3$OH\n+ CH$_4$", fontsize=5.5, va="bottom", ha="left",
       linespacing=1.05)
# flash
xf, wf, hf = 50.0, 7.0, 14.0
flow(xr + wr / 2, y0, xf - wf / 2, y0)
a.add_patch(FancyBboxPatch((xf - wf / 2, y0 - hf / 2), wf, hf, boxstyle="round,pad=0,rounding_size=2.3",
                           fc="white", ec=INK, lw=0.9, zorder=3))
a.add_patch(Rectangle((xf - wf / 2 + 0.35, y0 - hf / 2 + 0.6), wf - 0.7, 3.8, fc=PALE_B, ec="none", zorder=4))
a.text(xf + wf / 2 + 0.8, y0 + 3.2, "Flash", fontsize=6.2, fontweight="bold", va="center", ha="left")
# distillation of the crude
xd = 66.0
line([xf, xf, xd - 2.3], [y0 - hf / 2, 7.0, 7.0])
a.add_patch(FancyBboxPatch((xd - 2.3, 2.0), 4.6, 15.5, boxstyle="round,pad=0,rounding_size=1.7",
                           fc="white", ec=INK, lw=0.8, zorder=3))
for yy in np.linspace(4.3, 15.2, 5):
    a.plot([xd - 1.6, xd + 1.6], [yy, yy], color=INK, lw=0.4, zorder=4)
flow(xd + 2.3, 15.5, xd + 7.0, 15.5)
a.text(xd + 7.5, 15.5, "CH$_3$OH", fontsize=5.8, va="center")
flow(xd + 2.3, 4.0, xd + 7.0, 4.0)
a.text(xd + 7.5, 4.0, "H$_2$O", fontsize=5.8, va="center")
a.text(xd, 18.3, "Distillation", ha="center", va="bottom", fontsize=6.2, fontweight="bold")
# vapour: purge split and recycle
yv = 33.0
xs_ = 60.0
line([xf, xf, xs_], [y0 + hf / 2, yv, yv])
a.add_patch(Circle((xs_, yv), 0.75, fc=INK, ec="none", zorder=4))
flow(xs_, yv, xs_ + 11.0, yv, color=RED)
a.text(xs_ + 11.6, yv + 0.3, "purge", fontsize=6.2, fontweight="bold", color=RED, va="bottom")
a.text(xs_ + 11.6, yv - 0.3, "CH$_4$, CO, N$_2$\nwith H$_2$, CO$_2$", fontsize=5.5, color=MID, va="top",
       linespacing=1.1)
yr = 41.0
xc = 42.0
line([xs_, xs_, xc + 3.5], [yv, yr, yr])
compressor(xc, yr, left_wide=False)
line([xc - 3.5, xm], [yr, yr])
flow(xm, yr, xm, y0 + 0.9)
a.text(xc, yr + 4.6, "Recycle compressor", ha="center", va="bottom", fontsize=6.2, fontweight="bold")
a.text(xs_ - 1.2, yr + 0.8, "CH$_4$ builds up", fontsize=5.5, color=MID, va="bottom", ha="right")
a.text(xs_ + 1.6, 37.0, "purge fraction", fontsize=5.8, style="italic", va="center", ha="left", zorder=6,
       bbox=dict(boxstyle="round,pad=0.25,rounding_size=0.8", fc=PAPER, ec=MID, lw=0.4))
# the pathway, top to bottom
chain = ["S$_\\mathrm{CH_4}$ ↑", "CH$_4$ in the loop ↑", "recycle and purge\nlosses ↑", "H$_2$ feed and\ncompression ↑"]
cy = [25.0, 18.6, 11.6, 3.6]
for t, yy in zip(chain, cy):
    a.text(92.0, yy, t, ha="center", va="center", fontsize=5.9, linespacing=1.05,
           fontweight="bold" if t is chain[0] else "normal", color=RED if t is chain[0] else INK)
for y_a, y_b in ((cy[0] - 1.6, cy[1] + 1.6), (cy[1] - 1.6, cy[2] + 2.9), (cy[2] - 2.9, cy[3] + 2.9)):
    a.annotate("", xy=(92.0, y_b), xytext=(92.0, y_a),
               arrowprops=dict(arrowstyle="-|>", lw=0.6, color=MID, mutation_scale=5, shrinkA=0, shrinkB=0))

# ---- b: Re/TiO2 at two loadings ----------------------------------------------------------------
pg.letter("b", 110.0, 166.0)
b = pg.canvas(112.0, 112.0, 69.0, 52.0)
b.text(0.5, 50.0, "Re/TiO$_2$ catalyst states (schematic)", fontsize=7, fontweight="bold", va="top")
b.text(0.5, 45.8, "measured at 200 and 250 °C, 100 bar,\nCO$_2$ : H$_2$ = 1 : 4", fontsize=5.6, color=MID,
       va="top", linespacing=1.1)
for i, (tag, name, sub) in enumerate((("1wt", "1 wt% Re", "12 Re atoms"), ("5wt", "5 wt% Re", "60 Re atoms"))):
    img = crop_rgba(os.path.join(HERE, "renders", "ReTiO2_%s.png" % tag), pad=2)
    w = 50.0
    h = w * img.shape[0] / img.shape[1]
    yb = 19.5 - i * (h + 1.5)
    b.imshow(img, extent=(19.0, 19.0 + w, yb, yb + h), zorder=3, interpolation="lanczos")
    b.text(0.5, yb + h / 2 + 1.6, name, fontsize=6.4, fontweight="bold", va="center")
    b.text(0.5, yb + h / 2 - 1.8, sub, fontsize=5.6, color=MID, va="center")

# ---- c: from catalyst to loop to cost ---------------------------------------------------------------
CY, CH = 70.0, 25.0
pg.letter("c", 2.0, CY + CH + 12.0)
cols = [("STY_gMeOH_gRe_h", "STY", "g g$_\\mathrm{Re}^{-1}$ h$^{-1}$", 1.0, 82, "%d"),
        ("X_CO2", "CO$_2$ conv.", "%", 100.0, 52, "%d"),
        ("S_CH4", "CH$_4$ select.", "%", 100.0, 34, "%d"),
        ("CH4_fraction", "CH$_4$ in loop", "%", 100.0, 64, "%.1f"),
        ("recycle_kmol_h", "Recycle", "10$^3$ kmol h$^{-1}$", 1e-3, 205, "%.1f"),
        ("H2_feed_EUR_t", "H$_2$ feed", "EUR t$^{-1}$", 1.0, 1200, "%d"),
        ("NPC_EUR_t_2pct_purge", "Net cost", "EUR t$^{-1}$", 1.0, 1650, "%d")]
x0, cw, gap, ggap = 30.0, 12.6, 2.6, 2.6
xpos, xcur = [], x0
for k in range(len(cols)):
    xpos.append(xcur)
    xcur += cw + gap + (ggap if k in (2, 5) else 0.0)
rows_y = {k: 3 - i for i, k in enumerate(ECON)}
for k, (col, title, unit, scale, vmax, fmt) in enumerate(cols):
    ax = pg.ax(xpos[k], CY, cw, CH)
    ax.set_xlim(0, vmax)
    ax.set_ylim(-0.6, 3.6)
    ax.axis("off")
    ax.plot([0, 0], [-0.5, 3.5], color=INK, lw=0.5)
    for key in ECON:
        v = float(cand[KEY[key]][col]) * scale
        y = rows_y[key]
        ax.barh(y, v, height=0.62, color=COLOR[key], ec=INK, lw=0.4, zorder=3)
        txt = "<1" if (col == "S_CH4" and v == 0) else fmt % v
        ax.text(v + vmax * 0.035, y, txt, va="center", fontsize=5.7, zorder=4)
    ax.text(0, 4.3, title, fontsize=6.0, fontweight="bold", va="bottom", ha="left")
    ax.text(0, 3.72, unit, fontsize=5.4, color=MID, va="bottom", ha="left")
lab = pg.ax(4.0, CY, 25.0, CH)
lab.set_xlim(0, 1)
lab.set_ylim(-0.6, 3.6)
lab.axis("off")
lab.text(0.0, 4.3, "Catalyst state", fontsize=6.0, fontweight="bold", va="bottom")
lab.text(0.0, 3.72, "in net-cost order", fontsize=5.4, color=MID, va="bottom")
for key in ECON:
    lab.plot(0.06, rows_y[key], "s", ms=4.2, mfc=COLOR[key], mec=INK, mew=0.4)
    lab.text(0.17, rows_y[key], LABEL[key], va="center", fontsize=6.0,
             fontweight="bold" if key == WIN else "normal", color=RED if key == WIN else INK)
for (k0, k1, text) in ((0, 2, "Catalyst, measured"), (3, 5, "Loop at 2% purge"), (6, 6, "Plant")):
    xa, xb = xpos[k0], xpos[k1] + cw
    pg.fig.text(xa / pg.W, (CY + CH + 8.6) / pg.H, text, fontsize=6.3, fontweight="bold", va="bottom")
    pg.fig.add_artist(Line2D([xa / pg.W, xb / pg.W], [(CY + CH + 8.1) / pg.H] * 2, color=INK, lw=0.5))

# ---- d: rank probability under the cost draws -----------------------------------------------------
xm0 = 148.0
pg.letter("d", xm0 - 4.5, CY + CH + 12.0)
m = pg.ax(xm0, CY, 30.0, CH)
m.set_xlim(-0.5, 3.5)
m.set_ylim(-0.6, 3.6)
m.axis("off")
for i, key in enumerate(ECON):
    y = rows_y[key]
    for j in range(4):
        on = j == i
        m.add_patch(Rectangle((j - 0.46, y - 0.4), 0.92, 0.8, fc="#3E4452" if on else "white", ec=LINE, lw=0.5))
        if on:
            m.text(j, y, "1.00", ha="center", va="center", fontsize=5.3, color="white", fontweight="bold")
for j in range(4):
    m.text(j, 3.72, "#%d" % (j + 1), ha="center", va="bottom", fontsize=5.7)
pg.fig.text(xm0 / pg.W, (CY + CH + 8.6) / pg.H, "Rank probability", fontsize=6.3, fontweight="bold", va="bottom")
pg.fig.text(xm0 / pg.W, (CY + CH + 5.6) / pg.H, "5,000 cost draws", fontsize=5.4, color=MID, va="bottom")
m.text(1.5, -0.8, "canonical and active-Re\nboundaries, 5,000 / 5,000", ha="center", va="top", fontsize=5.4,
       color=MID, linespacing=1.1)

# ---- e: upstream to economic rank --------------------------------------------------------------------
LY, LH = 12.0, 36.0
pg.letter("e", 2.0, LY + LH + 7.0)
e = pg.ax(19.0, LY + 5.0, 20.0, LH - 7.0)
e.set_xlim(-0.12, 1.12)
e.set_ylim(4.5, 0.5)
e.axis("off")
for key in KEY:
    u, v = int(cand[KEY[key]]["rank_STY_per_gRe"]), int(cand[KEY[key]]["economic_rank"])
    hl = key == WIN
    e.plot([0, 1], [u, v], color=COLOR[key], lw=2.0 if hl else 1.3, solid_capstyle="round", zorder=4 if hl else 3)
    e.plot([0, 1], [u, v], "o", ms=3.4, mfc=COLOR[key], mec=INK, mew=0.4, zorder=5)
    for x_, r_, ha in ((-0.1, u, "right"), (1.1, v, "left")):
        e.text(x_, r_, LABEL[key], ha=ha, va="center", fontsize=5.8, fontweight="bold" if hl else "normal",
               color=RED if hl else INK)
e.text(0, 0.1, "STY per g Re", ha="center", va="bottom", fontsize=6.0, fontweight="bold")
e.text(1, 0.1, "Net cost", ha="center", va="bottom", fontsize=6.0, fontweight="bold")
e.text(0.5, 5.15, "ρ = 0.20,  τ = 0.00", ha="center", va="top", fontsize=6.0, color=RED, fontweight="bold")
e.text(0.5, 5.8, "3 of 6 pairs inverted", ha="center", va="top", fontsize=5.8, color=MID)

# ---- f: purge sweep ------------------------------------------------------------------------------------
pg.letter("f", 66.0, LY + LH + 7.0)
f1 = pg.ax(79.0, LY + 13.0, 46.0, LH - 13.0)
f2 = pg.ax(79.0, LY, 46.0, 11.0, sharex=f1)
boxed(f1)
boxed(f2)
pp = np.array([float(r["purge"]) for r in purge]) * 100
ends = {}
for key in KEY:
    ys = np.array([float(r["NPC_" + KEY[key]]) for r in purge])
    f1.plot(pp, ys, color=COLOR[key], lw=1.4 if key == WIN else 1.1, zorder=4 if key == WIN else 3)
    ends[key] = ys[-1]
for ax_ in (f1, f2):
    ax_.axvline(2.0, color=MID, lw=0.5, ls=(0, (2, 1.5)), zorder=1)
f1.text(2.8, 2700, "2% canonical", fontsize=5.5, color=MID, va="top")
for key, yv_ in ends.items():
    f1.text(41.0, yv_, SHORT[key], fontsize=5.4, va="center", ha="left",
            color=RED if key == WIN else INK, fontweight="bold" if key == WIN else "normal")
f1.set_xlim(0, 57)
f1.set_ylim(800, 2850)
f1.yaxis.set_major_locator(FixedLocator([1000, 1500, 2000, 2500]))
f1.yaxis.set_minor_locator(MultipleLocator(250))
f1.set_ylabel(r"Net cost (EUR t$^{-1}$)")
f1.tick_params(axis="x", labelbottom=False)
rho = np.array([float(r["spearman"]) for r in purge])
assert abs(rho.max() - 0.4) < 1e-12
f2.step(pp, rho, where="mid", color=INK, lw=0.8)
f2.axhline(0.4, color=RED, lw=0.5, ls=(0, (2, 1.5)))
f2.text(56.0, 0.47, "max 0.40", fontsize=5.4, color=RED, ha="right", va="bottom")
f2.set_ylim(-0.8, 0.85)
f2.yaxis.set_major_locator(FixedLocator([-0.5, 0, 0.5]))
f2.set_yticklabels(["−0.5", "0", "0.5"])
f2.set_ylabel("ρ", labelpad=2.0)
f2.set_xlabel("Purge fraction (%)")
f2.xaxis.set_major_locator(FixedLocator([0, 10, 20, 30, 40]))
f2.xaxis.set_minor_locator(MultipleLocator(5))

# ---- g: local economic leverage ----------------------------------------------------------------------------
pg.letter("g", 129.0, LY + LH + 7.0)
g = pg.ax(152.0, LY, 29.0, LH - 7.0)
boxed(g)
c55 = cand[KEY["5wtRe_250C"]]
lev = [("CH$_4$ suppression", float(c55["L_CH4_suppression"]), RED),
       ("Single-pass\nconversion", float(c55["L_conversion"]), "#56679A"),
       ("STY", float(c55["L_STY"]), "#9DACCB")]
for i, (name, v, col) in enumerate(lev):
    g.barh(i, v - 1e-3, left=1e-3, height=0.56, color=col, ec=INK, lw=0.45, zorder=3)
    g.text(v * 1.3, i, "%.5f" % v, va="center", fontsize=5.8, fontweight="bold" if i == 0 else "normal")
g.set_xscale("log")
g.set_xlim(1e-3, 12.0)
g.set_ylim(2.6, -0.6)
g.set_yticks(range(3))
g.set_yticklabels([x[0] for x in lev], fontsize=6.0, linespacing=1.0)
g.tick_params(axis="y", length=0)
g.xaxis.set_major_locator(FixedLocator([1e-3, 1e-2, 1e-1, 1, 10]))
g.xaxis.set_minor_locator(LogLocator(base=10, subs=np.arange(2, 10), numticks=12))
g.xaxis.set_minor_formatter(NullFormatter())
g.set_xlabel(r"|d ln $C$ / d ln $x$|")
g.text(0.0, 1.04, "local leverage at 5 wt%, 250 °C", transform=g.transAxes, ha="left", va="bottom",
       fontsize=5.6, color=MID)

pg.save(HERE, "Fig4")
