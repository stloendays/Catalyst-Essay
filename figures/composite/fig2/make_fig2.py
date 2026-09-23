"""Figure 2 — metal cost and process reoptimization jointly define the ammonia decision boundary.

Composite, 183 x 170 mm.
  fig2_pressure_envelopes.csv, fig2_ru_price_sweep.csv   fig2_model.py (frozen NH3-FINAL-1.1 harness)
  renders/bed_*.png, renders/beds.json                     build_beds.py (OVITO)
  closure/mc_draws.csv                                     NH3-FINAL-1.1 provenance, 1,000 descriptor draws
  analysis/supervisor_2026_09_20/*                         cost decomposition, equal-price test, joint cost MC

    pur_bridge_env/python make_fig2.py            -> Fig2.{svg,pdf,png}
"""
import csv
import json
import os
import sys

import numpy as np
from matplotlib.patches import Circle, FancyBboxPatch, Polygon, Rectangle
from matplotlib.ticker import FixedLocator, LogLocator, MultipleLocator, NullFormatter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from style import (DARK_B, DARK_G, FE, INK, LINE, MID, OS, OTHER, PALE_B, PALE_G, PAPER, RED, RU,  # noqa: E402
                   TINT_B, Page, boxed, crop_rgba, fmt_minus)

REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SUP = os.path.join(REPO, "analysis", "supervisor_2026_09_20")
CLOSURE = os.path.join(REPO, "provenance/nh3_final_1_1/source_harness/outputs/"
                             "nh3_final_20260905T134204Z/closure")


def read_csv(path):
    return list(csv.DictReader(open(path, encoding="utf-8")))


env = read_csv(os.path.join(HERE, "fig2_pressure_envelopes.csv"))
sweep = read_csv(os.path.join(HERE, "fig2_ru_price_sweep.csv"))
parity = sweep.pop()                                   # last row: the Ru = Fe price
decomp = {r["cost_pool"]: r for r in read_csv(os.path.join(SUP, "nh3_cost_decomposition.csv"))}
f3 = {r["metric"]: float(r["value"]) for r in read_csv(os.path.join(SUP, "f3_panel_summary.csv"))}
hist = read_csv(os.path.join(SUP, "nh3_cost_mc_histogram.csv"))
draws = read_csv(os.path.join(CLOSURE, "mc_draws.csv"))
EN = {r["metal"]: float(r["E_N_eV"]) for r in read_csv(os.path.join(HERE, "..", "fig1", "fig1_metals.csv"))}


def curve(case):
    rr = [r for r in env if r["case"] == case]
    return np.array([float(r["P_bar"]) for r in rr]), np.array([float(r["cost"]) for r in rr]), rr


OPT = {}
for case in ("Fe", "Ru", "Os", "Ru_at_Fe_price"):
    OPT[case] = {k: (float(v) if k != "case" else v) for k, v in min(curve(case)[2], key=lambda r: float(r["cost"])).items()}
# the harness recomputation and the frozen supervisor decomposition are the same numbers
for pool, key in (("metal_inventory", "metal_cost"), ("fresh_compression_electricity", "fresh_comp"),
                  ("compressor_CAPEX", "compressor_capex"), ("refrigeration_electricity", "refrigeration")):
    assert abs(float(decomp[pool]["Ru_canonical_USD_t"]) - OPT["Ru"][key]) < 1e-9
    assert abs(float(decomp[pool]["Ru_equal_price_reoptimized_USD_t"]) - OPT["Ru_at_Fe_price"][key]) < 1e-9
assert abs(float(decomp["TOTAL"]["Ru_equal_price_reoptimized_USD_t"]) - OPT["Ru_at_Fe_price"]["cost"]) < 1e-9

pg = Page(183.0, 170.0)

# ---- a: the synthesis loop -----------------------------------------------------
pg.letter("a", 2.0, 168.0)
a = pg.canvas(4.0, 114.0, 96.0, 52.0)
a.text(1.5, 50.0, r"NH$_3$ synthesis loop", fontsize=7, fontweight="bold", va="top")
y0 = 23.0
arrow = dict(arrowstyle="-|>", lw=0.7, color=INK, mutation_scale=5.5, shrinkA=0, shrinkB=0)


def line(xs, ys):
    a.plot(xs, ys, color=INK, lw=0.7, solid_capstyle="butt", zorder=2)


def flow(x0, y0_, x1, y1):
    a.annotate("", xy=(x1, y1), xytext=(x0, y0_), arrowprops=arrow, zorder=2)


def unit_label(x, y, head, sub, va="top"):
    n = head.count("\n") + 1
    a.text(x, y, head, ha="center", va="top", fontsize=6.2, fontweight="bold", linespacing=1.05)
    a.text(x, y - 2.5 * n - 0.6, sub, ha="center", va="top", fontsize=5.5, color=MID, linespacing=1.15)


def tag(x, y, text):
    a.text(x, y, text, ha="center", va="center", fontsize=5.8, style="italic", zorder=6,
           bbox=dict(boxstyle="round,pad=0.25,rounding_size=0.8", fc=PAPER, ec=MID, lw=0.4))


# fresh feed and fresh-feed compressor
a.text(0.5, y0 + 1.8, r"N$_2$ + 3H$_2$", fontsize=5.8, va="bottom")
a.text(0.5, y0 - 1.8, "30 bar", fontsize=5.5, color=MID, va="top")
flow(0.5, y0, 12.0, y0)
a.add_patch(Polygon([[12.0, y0 - 4.4], [12.0, y0 + 4.4], [20.0, y0 + 2.3], [20.0, y0 - 2.3]],
                    closed=True, fc="white", ec=INK, lw=0.8, zorder=3))
unit_label(16.0, y0 - 6.4, "Fresh-feed\ncompressor", "electricity,\ncapital")
# mixer and converter
xm = 27.0
flow(20.0, y0, xm - 0.2, y0)
a.add_patch(Circle((xm, y0), 0.75, fc=INK, ec="none", zorder=4))
xr, wr, hr = 40.0, 10.0, 26.0
flow(xm, y0, xr - wr / 2, y0)
a.add_patch(FancyBboxPatch((xr - wr / 2, y0 - hr / 2), wr, hr, boxstyle="round,pad=0,rounding_size=3.6",
                           fc="white", ec=INK, lw=0.9, zorder=3))
rng = np.random.default_rng(3)
px = rng.uniform(xr - wr / 2 + 1.2, xr + wr / 2 - 1.2, 170)
py = rng.uniform(y0 - hr / 2 + 3.4, y0 + hr / 2 - 4.4, 170)
a.scatter(px, py, s=3.4, c=OTHER, edgecolors="#8B9098", linewidths=0.2, zorder=4)
for yy in (y0 + hr / 2 - 3.8, y0 - hr / 2 + 2.8):
    a.plot([xr - wr / 2 + 0.8, xr + wr / 2 - 0.8], [yy, yy], color=INK, lw=0.45, zorder=4)
unit_label(xr, y0 - hr / 2 - 1.6, "Converter", "metal inventory,\nreactor, vessel\npressure premium")
tag(xr - 9.3, y0 + 8.6, "T, P")
# chiller
xh = 55.5
line([xr + wr / 2, xh - 3.2], [y0, y0])
a.add_patch(Circle((xh, y0), 3.2, fc="white", ec=INK, lw=0.8, zorder=3))
zz = np.array([[-3.0, 0], [-1.6, 1.5], [-0.5, -1.5], [0.5, 1.5], [1.6, -1.5], [3.0, 0]])
a.plot(xh + zz[:, 0] * 0.95, y0 + zz[:, 1] * 1.05, color=INK, lw=0.6, zorder=4)
unit_label(xh, y0 - 5.2, "Chiller", "refrigeration\nbelow 30 °C")
# separator
xs_, ws, hs = 70.5, 7.5, 16.0
flow(xh + 3.2, y0, xs_ - ws / 2, y0)
a.add_patch(FancyBboxPatch((xs_ - ws / 2, y0 - hs / 2), ws, hs, boxstyle="round,pad=0,rounding_size=2.5",
                           fc="white", ec=INK, lw=0.9, zorder=3))
a.add_patch(Rectangle((xs_ - ws / 2 + 0.35, y0 - hs / 2 + 0.6), ws - 0.7, 4.4, fc=PALE_B, ec="none", zorder=4))
flow(xs_, y0 - hs / 2, xs_, y0 - hs / 2 - 5.2)
a.text(xs_ + 1.0, y0 - hs / 2 - 5.6, r"NH$_3$(l)", fontsize=5.8, va="top")
a.text(xs_ + ws / 2 + 1.0, y0 - hs / 2 + 1.0, "Separator", ha="left", va="bottom", fontsize=6.2, fontweight="bold")
tag(xs_ - 9.0, y0 + 8.6, "T$_\\mathrm{sep}$")
# recycle loop with circulator
yr = y0 + 19.0
xo = xs_ + ws / 2 + 3.4
line([xs_ + ws / 2, xo, xo], [y0 + 4.0, y0 + 4.0, yr])
xc = 55.5
line([xo, xc + 3.2], [yr, yr])
a.add_patch(Polygon([[xc + 3.2, yr - 3.5], [xc + 3.2, yr + 3.5], [xc - 3.2, yr + 1.9], [xc - 3.2, yr - 1.9]],
                    closed=True, fc="white", ec=INK, lw=0.8, zorder=3))
line([xc - 3.2, xm], [yr, yr])
flow(xm, yr, xm, y0 + 0.9)
a.text(xc, yr + 4.3, "Recycle compressor", ha="center", va="bottom", fontsize=6.2, fontweight="bold")
a.text(xc, yr - 4.2, "electricity, capital", ha="center", va="top", fontsize=5.5, color=MID)

# ---- b: catalyst beds to scale ----------------------------------------------------
pg.letter("b", 101.0, 168.0)
b = pg.canvas(103.0, 114.0, 78.0, 52.0)
b.text(0.5, 50.0, "Catalyst bed at each optimum, to scale", fontsize=7, fontweight="bold", va="top")
imgs = {m: crop_rgba(os.path.join(HERE, "renders", "bed_%s.png" % m), pad=2) for m in ("Fe", "Ru", "Ru_at_Fe_price")}
mm_per_px = 28.0 / imgs["Fe"].shape[0]
base_y = 17.0
place = {"Fe": 10.5, "Ru": 37.0, "Ru_at_Fe_price": 63.5}
half_w = {}
for m, xc_ in place.items():
    img = imgs[m]
    hh, ww = img.shape[0] * mm_per_px, img.shape[1] * mm_per_px
    half_w[m] = ww / 2
    b.imshow(img, extent=(xc_ - ww / 2, xc_ + ww / 2, base_y, base_y + hh), zorder=3, interpolation="lanczos")
b.plot([0.5, 77.5], [base_y - 0.3] * 2, color=LINE, lw=0.6, zorder=1)
names = {"Fe": "Fe", "Ru": "Ru", "Ru_at_Fe_price": "Ru, priced as Fe"}
for m, xc_ in place.items():
    o = OPT[m]
    V = o["V_m3"]
    b.text(xc_, base_y - 1.4, names[m], ha="center", va="top", fontsize=6.3, fontweight="bold")
    b.text(xc_, base_y - 4.3, (("%.3f" if V < 1 else "%.1f") % V) + " m$^3$ · %d bar" % o["P_bar"],
           ha="center", va="top", fontsize=6.0)
    b.text(xc_, base_y - 7.0, "%d °C · T$_\\mathrm{sep}$ %d °C" % (o["T_C"], o["Tsep_C"]),
           ha="center", va="top", fontsize=5.8)
    b.text(xc_, base_y - 9.9, "metal %.3f USD t$^{-1}$" % o["metal_cost"], ha="center", va="top", fontsize=5.6,
           color=MID)
vr = OPT["Fe"]["V_m3"] / OPT["Ru"]["V_m3"]
mr = OPT["Ru"]["metal_cost"] / OPT["Fe"]["metal_cost"]
vq = OPT["Ru_at_Fe_price"]["V_m3"] / OPT["Ru"]["V_m3"]
ya = base_y + 5.5
for (x0, x1, top, bot) in ((place["Fe"] + half_w["Fe"] + 1.0, place["Ru"] - half_w["Ru"] - 1.0,
                            "%d× smaller bed" % round(vr), "%d× metal cost" % round(mr)),
                           (place["Ru"] + half_w["Ru"] + 1.0, place["Ru_at_Fe_price"] - half_w["Ru_at_Fe_price"] - 1.0,
                            "priced as Fe", "%d× larger bed" % round(vq))):
    b.annotate("", xy=(x1, ya), xytext=(x0, ya),
               arrowprops=dict(arrowstyle="-|>", lw=0.6, color=MID, mutation_scale=5, shrinkA=0, shrinkB=0))
    b.text((x0 + x1) / 2, ya + 1.0, top, ha="center", va="bottom", fontsize=5.8)
    b.text((x0 + x1) / 2, ya - 1.0, bot, ha="center", va="top", fontsize=5.8)
assert (round(vr), round(mr), round(vq)) == (258, 26, 143)

# ---- c: pressure envelopes -------------------------------------------------------------
RY0, RH = 63.0, 34.0
pg.letter("c", 2.0, RY0 + RH + 7.0)
c = pg.ax(13.0, RY0, 44.0, RH)
boxed(c)
styles = {"Os": (OS, "-", 1.0), "Ru": (RU, "-", 1.1), "Fe": (FE, "-", 1.1), "Ru_at_Fe_price": (RU, (0, (3, 1.6)), 1.0)}
for case, (col, ls, lw) in styles.items():
    P, cost, _ = curve(case)
    c.plot(P, cost, color=col, ls=ls, lw=lw, zorder=3)
    o = OPT[case]
    hollow = case == "Ru_at_Fe_price"
    c.plot(o["P_bar"], o["cost"], "o", ms=3.6, mfc="white" if hollow else col, mec=RU if hollow else INK,
           mew=0.6, zorder=5)
lead = dict(arrowstyle="-", lw=0.45, color=MID, shrinkA=0.5, shrinkB=2.0)
c.annotate("Fe  15.29 (180 bar)", (180, OPT["Fe"]["cost"]), xytext=(420, 14.6), fontsize=5.8, color=DARK_G,
           fontweight="bold", va="center", arrowprops=lead)
c.annotate("Ru  22.03 (425 bar)", (425, OPT["Ru"]["cost"]), xytext=(520, 20.0), fontsize=5.8, color=DARK_B,
           fontweight="bold", va="center", arrowprops=lead)
c.annotate("Os  25.83 (425 bar)", (425, OPT["Os"]["cost"]), xytext=(470, 28.4), fontsize=5.8, color=DARK_B,
           va="center", arrowprops=lead)
c.text(25, 13.2, "Ru priced as Fe\n14.71 (170 bar)", fontsize=5.6, color=DARK_B, va="top", ha="left",
       linespacing=1.1)
c.text(0.97, 0.04, r"$T$, $T_\mathrm{sep}$ reoptimized", transform=c.transAxes, ha="right", va="bottom",
       fontsize=5.6, color=MID)
c.set_xlim(0, 1000)
c.set_ylim(10.5, 30)
c.set_xlabel("Synthesis pressure (bar)")
c.set_ylabel(r"Lowest cost (USD t$^{-1}$ NH$_3$)")
c.xaxis.set_minor_locator(MultipleLocator(100))
c.yaxis.set_minor_locator(MultipleLocator(1))

# ---- d: Ru metal price sweep -------------------------------------------------------------
pg.letter("d", 62.0, RY0 + RH + 7.0)
d1 = pg.ax(75.0, RY0 + 13.0, 42.0, RH - 13.0)
d2 = pg.ax(75.0, RY0, 42.0, 11.5, sharex=d1)
boxed(d1)
boxed(d2)
pr = np.array([float(r["price_USD_kg"]) for r in sweep])
co = np.array([float(r["cost"]) for r in sweep])
Popt = np.array([float(r["P_bar"]) for r in sweep])
Vopt = np.array([float(r["V_m3"]) for r in sweep])
fe_cost = OPT["Fe"]["cost"]
p_star = float(parity["price_USD_kg"])
for ax_ in (d1, d2):
    ax_.axvspan(1.0, p_star, color=TINT_B, lw=0, zorder=0)
d1.axhline(fe_cost, color=FE, lw=0.9, ls=(0, (3, 1.6)), zorder=2)
d1.text(2.2e5, fe_cost + 0.4, "Fe 15.29", fontsize=5.8, color=DARK_G, ha="right", va="bottom", fontweight="bold")
d1.plot(pr, co, color=RU, lw=1.2, zorder=3)
i8 = int(np.argmin(np.abs(pr - 8.0)))
ic = int(np.argmin(np.abs(pr - 53852.5)))
for i in (i8, ic):
    d1.plot(pr[i], co[i], "o", ms=3.4, mfc=RU, mec=INK, mew=0.5, zorder=5)
d1.text(1.35, fe_cost + 0.7, "8 USD kg$^{-1}$: %.2f" % co[i8], fontsize=5.6, ha="left", va="bottom")
d1.annotate("53,853 USD kg$^{-1}$\n%.2f" % co[ic], (pr[ic], co[ic]), xytext=(-5, 4), textcoords="offset points",
            fontsize=5.6, ha="right", va="bottom", linespacing=1.1)
d1.plot(p_star, fe_cost, "o", ms=4.0, mfc=RED, mec=INK, mew=0.5, zorder=6)
d1.text(p_star * 1.45, fe_cost - 1.25, "parity at %d USD kg$^{-1}$" % round(p_star), fontsize=5.8, color=RED,
        fontweight="bold", va="center", ha="left")
d1.text(1.5, 26.0, "Ru cheaper", fontsize=5.6, color=DARK_B, va="top")
d1.set_xscale("log")
d1.set_xlim(1.0, 3e5)
d1.set_ylim(12.6, 26.6)
d1.yaxis.set_major_locator(FixedLocator([15, 20, 25]))
d1.yaxis.set_minor_locator(MultipleLocator(1))
d1.set_ylabel(r"Ru cost (USD t$^{-1}$)")
d1.tick_params(axis="x", labelbottom=False)
d2.step(pr, Popt, where="post", color=INK, lw=0.8)
d2.set_ylim(100, 500)
d2.yaxis.set_major_locator(FixedLocator([200, 400]))
d2.set_ylabel("$P_\\mathrm{opt}$\n(bar)", labelpad=1.5)
d2.set_xscale("log")
d2.xaxis.set_major_locator(LogLocator(base=10, numticks=8))
d2.xaxis.set_minor_locator(LogLocator(base=10, subs=np.arange(2, 10), numticks=12))
d2.xaxis.set_minor_formatter(NullFormatter())
d2.set_xlabel(r"Ru metal price (USD kg$^{-1}$)")
d2.text(1.5, 470, "bed %.1f m$^3$" % Vopt[i8], fontsize=5.5, color=MID, va="top")
d2.text(2.4e5, 140, "bed %.3f m$^3$" % Vopt[ic], fontsize=5.5, color=MID, va="bottom", ha="right")

# ---- e: where the canonical gap sits, and the equal-price intervention ---------------------------
pg.letter("e", 121.0, RY0 + RH + 7.0)
e = pg.ax(147.5, RY0, 33.5, RH)
boxed(e)
order = [("fresh_compression_electricity", "fresh compression"), ("metal_inventory", "metal inventory"),
         ("compressor_CAPEX", "compressor capital"), ("refrigeration_electricity", "refrigeration"),
         ("vessel_pressure_premium", "vessel pressure"), ("recycle_compression_electricity", "recycle compression"),
         ("reactor_base", "reactor base")]
fe_tot = float(decomp["TOTAL"]["Fe_canonical_USD_t"])
ru_tot = float(decomp["TOTAL"]["Ru_canonical_USD_t"])
eq_tot = float(decomp["TOTAL"]["Ru_equal_price_reoptimized_USD_t"])
X0 = 13.5
ypos = list(range(len(order) + 2))[::-1]          # Fe row at top, then the pools, then Ru
bh = 0.62
e.barh(ypos[0], fe_tot - X0, left=X0, height=bh, color=FE, ec=INK, lw=0.5, zorder=3)
e.text(fe_tot + 0.3, ypos[0], "%.3f" % fe_tot, va="center", fontsize=5.8, fontweight="bold")
run = fe_tot
for k, (pool, name) in enumerate(order):
    dv = float(decomp[pool]["Ru_minus_Fe_USD_t"])
    y = ypos[k + 1]
    e.barh(y, dv, left=run, height=bh, color=PALE_B if dv > 0 else PALE_G, ec=INK, lw=0.45, zorder=3)
    e.plot([run, run], [y + bh / 2, y + 1 - bh / 2], color=MID, lw=0.4, zorder=2)
    e.text(max(run, run + dv) + 0.3, y, fmt_minus("%+.3f" % dv), va="center", fontsize=5.5)
    run += dv
assert abs(run - ru_tot) < 1e-9
e.plot([run, run], [ypos[-2] - bh / 2, ypos[-1] + bh / 2], color=MID, lw=0.4, zorder=2)
e.barh(ypos[-1], ru_tot - X0, left=X0, height=bh, color=RU, ec=INK, lw=0.5, zorder=3)
e.text(ru_tot + 0.3, ypos[-1], "%.3f" % ru_tot, va="center", fontsize=5.8, fontweight="bold")
yq = ypos[-1] - 1.35
e.barh(yq, eq_tot - X0, left=X0, height=bh, color="white", ec=RU, lw=0.8, hatch="//////", zorder=3)
e.text(fe_tot + 0.3, yq, "%.3f" % eq_tot, va="center", fontsize=5.8, fontweight="bold", color=RED)
e.axvline(fe_tot, color=FE, lw=0.7, ls=(0, (2, 1.5)), zorder=1)
e.set_yticks(ypos + [yq])
e.set_yticklabels(["Fe"] + [n for _, n in order] + ["Ru", "Ru, priced as Fe"], fontsize=6.0)
for t in e.get_yticklabels():
    if t.get_text() in ("Fe", "Ru", "Ru, priced as Fe"):
        t.set_fontweight("bold")
e.tick_params(axis="y", length=0)
e.set_xlim(X0, 26.3)
e.set_ylim(yq - 0.7, ypos[0] + 0.7)
e.xaxis.set_major_locator(FixedLocator([14, 18, 22, 26]))
e.xaxis.set_minor_locator(MultipleLocator(1))
e.set_xlabel(r"Cost (USD t$^{-1}$ NH$_3$)")

# ---- f: descriptor draws, coloured by the economic winner ----------------------------------------
LY0, LH = 11.0, 34.0
pg.letter("f", 2.0, LY0 + LH + 6.5)
f = pg.ax(13.0, LY0, 40.0, LH)
boxed(f)
xF = np.array([float(r["E_N_Fe"]) for r in draws])
yR = np.array([float(r["E_N_Ru"]) for r in draws])
win = np.array([r["economic_winner"] for r in draws])
feas = np.array([r["Fe_feasible"] == "1" for r in draws])
assert set(win) == {"Fe", "Ru"} and int((win == "Fe").sum()) == 681 and int(feas.sum()) == 799
lo_f, hi_f = xF[feas].min(), xF[feas].max()
assert feas[(xF >= lo_f) & (xF <= hi_f)].all(), "Fe feasibility is not one descriptor interval"
f.axvspan(-3, lo_f, color="#F3F3F3", lw=0, zorder=0)
f.axvspan(hi_f, 0, color="#F3F3F3", lw=0, zorder=0)
for xv in (lo_f, hi_f):
    f.axvline(xv, color=MID, lw=0.5, ls=(0, (2, 1.5)), zorder=1)
f.scatter(xF[win == "Ru"], yR[win == "Ru"], s=2.2, c=RU, edgecolors="none", zorder=2, alpha=0.9)
f.scatter(xF[win == "Fe"], yR[win == "Fe"], s=2.2, c=FE, edgecolors="none", zorder=3, alpha=0.9)
f.plot(EN["Fe"], EN["Ru"], marker="*", ms=6.5, mfc="white", mec=INK, mew=0.6, zorder=5)
f.text(EN["Fe"] + 0.05, EN["Ru"] + 0.012, "canonical", fontsize=5.5, va="bottom", color=INK, fontweight="bold",
       bbox=dict(boxstyle="square,pad=0.1", fc="white", ec="none", alpha=0.8), zorder=6)
f.text(0.5 * (lo_f + hi_f), -1.305, "Fe feasible", ha="center", va="bottom", fontsize=5.6, color=MID)
f.text(lo_f - 0.04, -0.985, "bed > 90 m$^3$", ha="right", va="top", fontsize=5.5, color=MID,
       bbox=dict(boxstyle="square,pad=0.1", fc="#F3F3F3", ec="none", alpha=0.85), zorder=6)
f.set_xlim(-2.12, -0.62)
f.set_ylim(-1.31, -0.97)
f.set_xlabel(r"Fe $E_\mathrm{N}$ draw (eV)")
f.set_ylabel(r"Ru $E_\mathrm{N}$ draw (eV)")
f.xaxis.set_minor_locator(MultipleLocator(0.1))
f.yaxis.set_minor_locator(MultipleLocator(0.02))
f.set_xticks([-2.0, -1.5, -1.0])
f.set_xticklabels([fmt_minus("%.1f" % v) for v in (-2.0, -1.5, -1.0)])
f.set_yticks([-1.3, -1.2, -1.1, -1.0])
f.set_yticklabels([fmt_minus("%.1f" % v) for v in (-1.3, -1.2, -1.1, -1.0)])
f.text(1.03, 0.98, "economic\nwinner", transform=f.transAxes, fontsize=5.6, va="top", color=MID)
for yy, col, txt in ((0.74, FE, "Fe  681"), (0.64, RU, "Ru  319")):
    f.plot([1.06], [yy], "o", ms=3.0, mfc=col, mec="none", transform=f.transAxes, clip_on=False)
    f.text(1.1, yy, txt, transform=f.transAxes, fontsize=5.8, va="center")

# ---- g: decision endpoints under descriptor uncertainty -------------------------------------------
pg.letter("g", 70.0, LY0 + LH + 6.5)
g = pg.ax(97.0, LY0, 26.0, LH)
boxed(g)
bars = [("Fe feasible,\nbed ≤ 90 m$^3$", f3["Fe_feasible_descriptor_MC"], FE),
        ("Fe economic Top-1", f3["Fe_economic_top1_descriptor_MC"], FE),
        ("Atomic Top-1 =\neconomic Top-1", f3["top1_survival_descriptor_MC"], OTHER),
        ("Fe in actionable\nTop-3", f3["Fe_top3_actionable_descriptor_MC"], FE)]
for i, (name, v, col) in enumerate(bars):
    y = len(bars) - 1 - i
    g.barh(y, 100 * v, height=0.58, color=col, ec=INK, lw=0.5, zorder=3)
    g.text(100 * v + 2.5, y, "%.1f%%" % (100 * v), va="center", fontsize=6.0, fontweight="bold")
g.set_yticks(range(len(bars))[::-1])
g.set_yticklabels([bb[0] for bb in bars], fontsize=6.0, linespacing=1.0)
g.tick_params(axis="y", length=0)
g.set_xlim(0, 130)
g.set_ylim(-0.6, len(bars) - 0.4)
g.xaxis.set_major_locator(FixedLocator([0, 50, 100]))
g.xaxis.set_minor_locator(MultipleLocator(10))
g.set_xlabel("Share of 1,000 draws (%)")

# ---- h: joint cost Monte Carlo ------------------------------------------------------------------------
pg.letter("h", 129.0, LY0 + LH + 6.5)
hh_ = pg.ax(139.0, LY0, 42.0, LH)
boxed(hh_)
dl = np.array([float(r["delta_left"]) for r in hist])
dr = np.array([float(r["delta_right"]) for r in hist])
dc = np.array([float(r["delta_count"]) for r in hist])
assert int(dc.sum()) == 5000
hh_.bar(dl, dc, width=dr - dl, align="edge", color=OS, ec="white", lw=0.3, zorder=3)
hh_.axvline(0, color=RED, lw=0.9, ls=(0, (3, 1.6)), zorder=4)
hh_.text(0.35, 380, "Ru = Fe", color=RED, fontsize=5.8, fontweight="bold", va="top")
med = f3["median_Ru_minus_Fe_cost_MC"]
mn = f3["min_Ru_minus_Fe_cost_MC"]
hh_.axvline(med, color=INK, lw=0.6, zorder=4)
hh_.text(med + 0.3, 380, "median %.2f" % med, fontsize=5.6, va="top")
hh_.annotate("min %.2f" % mn, (mn, 36), xytext=(mn - 0.2, 150), fontsize=5.6, ha="right", va="bottom",
             arrowprops=dict(arrowstyle="-", lw=0.5, color=MID, shrinkA=1, shrinkB=1))
hh_.text(0.97, 0.66, "Fe cheaper in\n5,000 / 5,000\ndraws", transform=hh_.transAxes, ha="right", va="top",
         fontsize=6.0, fontweight="bold", linespacing=1.15)
hh_.set_xlim(-1.5, 16.5)
hh_.set_ylim(0, 400)
hh_.xaxis.set_major_locator(FixedLocator([0, 4, 8, 12, 16]))
hh_.xaxis.set_minor_locator(MultipleLocator(1))
hh_.yaxis.set_minor_locator(MultipleLocator(50))
hh_.set_xlabel(r"$C_\mathrm{Ru} - C_\mathrm{Fe}$ (USD t$^{-1}$ NH$_3$)")
hh_.set_ylabel("Draws")

pg.save(HERE, "Fig2")
