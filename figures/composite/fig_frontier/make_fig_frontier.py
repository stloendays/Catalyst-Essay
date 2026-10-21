"""Figure 5 (2026-10-21): supported Ru/C against fused iron with measured rate laws, each inside its fitted pressure
range (fused iron: Keestra et al. 2025 Model 3, Topsoe KM1R 1964 activity, 1-324 bar; Ru/C: Rossetti et al. 2006,
50-100 bar). Supervisor, 2026-10-20: the Fe-upstream / Ru/C-downstream bed order that the optimizer selects gets its
own main-text panel; one Ru/C - Fe cost curve against the metal financing rate with its break-even points.

    a  Ru/C - Fe against the metal financing rate: KAAP-type loop (90 bar, -20 C) and each catalyst at its own
       in-range optimum; documented catalyst-metal lease rates (32 PBF leases, 1.35-5.10 %/y, median 2.10 %/y)
       analysis/nh3_keestra_consolidation_2026_10_20/financing_curves.csv, summary.json
       analysis/nh3_ru_metal_financing_evidence_2026_10_12/pbf_catalyst_lease_contracts.csv
    b  three-bed adiabatic converter at 9 MPa: best all-Fe, Fe-first, all-Ru/C and Ru/C-first designs against the rate
       same financing_curves.csv (from analysis/nh3_fe_inrange_kinetics_2026_10_19/staged_KM1R_1964_design_library.csv)
    c  the least-cost converter at the reference rate (2.10 %/y): bed catalysts, volumes and temperatures
       analysis/nh3_fe_inrange_kinetics_2026_10_19/staged_KM1R_1964_design_library.csv (+ boundary.charges)
    d  Ru/C (8 wt%) to fused-iron rate ratio per kg and per m3 of bed against NH3, 90 bar, 400 C
       analysis/nh3_fe_inrange_kinetics_2026_10_19/validation.json (rate_ratio_90bar_Keestra)

    D:\\Tools\\pur_bridge_env\\Scripts\\python.exe make_fig_frontier.py   (NH3_MODEL=1.2 for panel c)
"""
import csv
import json
import os
import statistics
import sys

import numpy as np
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Rectangle

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(HERE, ".."))
from style import DARK_B, DARK_G, FE, INK, MID, PALE_B, PALE_G, RED, RU, TINT_B, TINT_G, Page, boxed  # noqa: E402

CONS = os.environ.get("FRONTIER_CONS", os.path.join(REPO, "analysis", "nh3_keestra_consolidation_2026_10_20"))
INR = os.path.join(REPO, "analysis", "nh3_fe_inrange_kinetics_2026_10_19")
LEASE = os.path.join(REPO, "analysis", "nh3_ru_metal_financing_evidence_2026_10_12", "pbf_catalyst_lease_contracts.csv")
REF_RATE = 2.10   # %/y, median of the 32 disclosed catalyst-metal leases (reference rate of the manuscript)


def rows(path):
    with open(path, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


fc = rows(os.path.join(CONS, "financing_curves.csv"))
r = np.array([float(x["financing_rate_pct"]) for x in fc])
bench = np.array([float(x["benchmark_RuC_minus_Fe"]) for x in fc])
kaap = np.array([float(x["KAAP_RuC_minus_Fe"]) for x in fc])
s_fe = np.array([float(x["staged_all_Fe"]) for x in fc])
s_ff = np.array([float(x["staged_Fe_first"]) for x in fc])
s_rr = np.array([float(x["staged_all_RuC"]) for x in fc])
s_rf = np.array([float(x["staged_Ru_first"]) for x in fc])
opt = [x["staged_optimal"] for x in fc]

leases = [float(x["annual_rate_pct"]) for x in rows(LEASE)]
assert len(leases) == 32 and (min(leases), statistics.median(leases), max(leases)) == (1.35, 2.10, 5.10), leases


def crossing(x, y):
    i = int(np.where((y[:-1] < 0) & (y[1:] >= 0))[0][0])
    return float(np.interp(0.0, [y[i], y[i + 1]], [x[i], x[i + 1]]))


be_kaap, be_bench = crossing(r, kaap), crossing(r, bench)
assert abs(be_kaap - 4.57) < 0.03 and abs(be_bench - 6.49) < 0.03, (be_kaap, be_bench)
assert abs(kaap[0] + 1.209) < 2e-3 and abs(bench[0] + 3.826) < 2e-3
fe_first = np.array([o in ("FFR", "FRR") for o in opt])
win_grid = float(r[fe_first].max())
win_hi = 100 * json.load(open(os.path.join(INR, "staged_KM1R_1964_summary.json"), encoding="utf-8"))["window_keestra"]["staged_beats_all_Fe_below"]
assert win_grid <= win_hi < win_grid + 0.05, (win_grid, win_hi)
assert not any(o.startswith("R") and o != "RRR" for o in opt), "a Ru/C-first design is optimal somewhere"
assert abs(win_hi - 5.46) < 0.005, win_hi
i_ref = int(np.argmin(np.abs(r - REF_RATE)))
assert abs(r[i_ref] - REF_RATE) < 1e-9

pg = Page(180.0, 104.0)

# ---- a: Ru/C - Fe against the metal financing rate ---------------------------------------------------------------
a = pg.ax(14, 60, 66, 38)
a.axvspan(min(leases), max(leases), color=TINT_B, lw=0, zorder=0)
a.axhline(0, color=INK, lw=0.5, zorder=1)
a.plot(r, kaap, color=RU, lw=1.2, zorder=3, label="KAAP-type loop")
a.plot(r, bench, color=DARK_B, lw=0.9, ls=(0, (3, 1.5)), zorder=3, label="each at own optimum")
a.axvline(REF_RATE, color=RED, lw=0.7, zorder=2)
for be, y in ((be_kaap, kaap), (be_bench, bench)):
    a.plot(be, 0, "o", ms=3.2, mfc="white", mec=INK, mew=0.6, zorder=5)
a.text(be_kaap, 0.25, "%.2f" % be_kaap, fontsize=5.4, ha="right", va="bottom")
a.text(be_bench + 0.2, -0.25, "%.2f" % be_bench, fontsize=5.4, ha="left", va="top")
a.text(REF_RATE + 0.15, 2.45, "reference\n%.2f%%" % REF_RATE, fontsize=5.4, color=RED, va="top", linespacing=1.0)
a.text((min(leases) + max(leases)) / 2, -4.05, "disclosed\nleases", fontsize=5.3, color=DARK_B, ha="center",
       va="bottom", linespacing=1.0)
a.text(11.8, -3.95, "Ru/C cheaper", fontsize=5.4, ha="right", va="bottom", color=DARK_B)
a.text(11.8, 0.15, "Fe cheaper", fontsize=5.4, ha="right", va="bottom", color=DARK_G)
a.set_xlim(0, 12)
a.set_ylim(-4.2, 2.6)
a.set_xticks([0, 2, 4, 6, 8, 10, 12])
a.set_xlabel("Ru financing rate (% per year)")
a.set_ylabel(r"Ru/C $-$ Fe (USD t$^{-1}$ NH$_3$)")
a.legend(frameon=False, fontsize=5.3, loc="lower right", bbox_to_anchor=(1.0, 0.13), handlelength=2.2)   # empty lower right
boxed(a)
pg.letter("a", 2, 102)

# ---- b: three-bed converter, best design of each arrangement -----------------------------------------------------
b = pg.ax(108, 60, 70, 38)
b.axvspan(0, win_hi, color=TINT_G, lw=0, zorder=0)
b.plot(r, s_fe, color=FE, lw=1.1, label="all Fe", zorder=3)
b.plot(r, s_rr, color=RU, lw=1.1, label="all Ru/C", zorder=3)
b.plot(r, s_rf, color=MID, lw=0.8, ls=(0, (1.2, 1.2)), label="Ru/C first", zorder=3)
b.plot(r, s_ff, color=INK, lw=1.3, label="Fe first", zorder=4)
b.axvline(REF_RATE, color=RED, lw=0.7, zorder=2)
b.text(2.35, 17.24, "Fe first optimal"+chr(10)+"0–%.2f%%" % win_hi, fontsize=5.4, ha="left", va="bottom",
       color=DARK_G, linespacing=1.0)
b.set_xlim(0, 12)
b.set_ylim(17.2, 19.0)
b.set_xticks([0, 2, 4, 6, 8, 10, 12])
b.set_xlabel("Ru financing rate (% per year)")
b.set_ylabel(r"cost (USD t$^{-1}$ NH$_3$)")
b.legend(frameon=False, fontsize=5.3, loc="upper right", handlelength=2.0)
boxed(b)
pg.letter("b", 96, 102)

# ---- c: the least-cost converter at the reference rate -----------------------------------------------------------
sys.path.insert(0, os.path.join(REPO, "analysis", "nh3_staged_converter_2026_10_12"))
import boundary as B  # noqa: E402

lib = [x for x in rows(os.path.join(INR, "staged_KM1R_1964_design_library.csv"))
       if float(x["P_bar"]) == 90.0 and float(x["Tsep_C"]) == -20.0]
c_ru, c_fe, c_sup = B.charges(53852.5, 0.9555, REF_RATE / 100)
out_t = B.C.H.annual_output_t


def cost(x):
    return float(x["noncatalyst"]) + (c_ru * float(x["Ru_metal_kg"]) + c_fe * float(x["mass_Fe_kg"])
                                      + c_sup * float(x["mass_Ru_cat_kg"])) / out_t


best = min(lib, key=cost)
assert abs(cost(best) - float(fc[i_ref]["staged_optimal_cost"])) < 1e-6, (cost(best), fc[i_ref]["staged_optimal_cost"])
pat = best["pattern"]
vols = [float(v) for v in best["beds_volume_m3"].split(";")]
temps = ["%.0f–%.0f" % tuple(float(v) for v in t.split(":")[1].split("-")) for t in best["beds_T_in_out_C"].split(";")]
ynh3 = [100 * float(v) for v in best["beds_y_NH3_out"].split(";")]
# drawn as the converter itself: gas runs left to right through three adiabatic beds (lengths to scale with volume)
# separated by interbed coolers
c = pg.canvas(4, 4, 104, 44)
rng = np.random.default_rng(7)
XS, XE, YB, YT = 16.0, 92.0, 14.0, 28.0          # vessel interior
COOL = 7.0                                        # cooler slot between beds
scale = (XE - XS - 2 * COOL - 2.0) / sum(vols)
c.add_patch(FancyBboxPatch((XS - 1.2, YB - 1.2), XE - XS + 2.4, YT - YB + 2.4, boxstyle="round,pad=0,rounding_size=3",
                           fc="white", ec=INK, lw=0.8, zorder=1))
x = XS + 1.0
fe_frac = 1 - float(best["Ru_volume_fraction"])
for k, (cat, v, t, yo) in enumerate(zip(pat, vols, temps, ynh3)):
    L = v * scale
    col, dark = (FE, DARK_G) if cat == "F" else (RU, DARK_B)
    c.add_patch(Rectangle((x, YB + 0.6), L, YT - YB - 1.2, fc=col, ec="none", alpha=0.9, zorder=2))
    n = int(28 * L)
    c.scatter(rng.uniform(x + 0.6, x + L - 0.6, n), rng.uniform(YB + 1.3, YT - 1.3, n), s=0.9, c=dark, lw=0,
              zorder=3)
    c.text(x + L / 2, YT + 6.6, "Fe" if cat == "F" else "Ru/C", ha="center", va="bottom", fontsize=6.4,
           fontweight="bold", color=dark)
    c.text(x + L / 2, YT + 2.6, "%.1f m$^3$" % v, ha="center", va="bottom", fontsize=5.4, color=INK)
    c.text(x + L / 2, YB - 2.4, "%s °C" % t, ha="center", va="top", fontsize=5.4, color=INK)
    c.text(x + L / 2, YB - 5.8, "%.1f%% NH$_3$" % yo, ha="center", va="top", fontsize=5.4, color=INK)
    x += L
    if k < 2:
        cx = x + COOL / 2
        c.add_patch(Circle((cx, (YB + YT) / 2), 2.4, fc="white", ec=INK, lw=0.6, zorder=3))
        zz = np.linspace(cx - 1.6, cx + 1.6, 7)
        c.plot(zz, (YB + YT) / 2 + 1.0 * np.array([0, 1, -1, 1, -1, 1, 0]), color=INK, lw=0.5, zorder=4)
        x += COOL
c.annotate("", xy=(XS - 1.4, (YB + YT) / 2), xytext=(4.0, (YB + YT) / 2),
           arrowprops=dict(arrowstyle="-|>", lw=0.8, color=INK, mutation_scale=6))
c.text(4.0, (YB + YT) / 2 + 2.0, "N$_2$ + 3H$_2$", fontsize=5.6, va="bottom", ha="left")
c.annotate("", xy=(103.0, (YB + YT) / 2), xytext=(XE + 1.4, (YB + YT) / 2),
           arrowprops=dict(arrowstyle="-|>", lw=0.8, color=INK, mutation_scale=6))
c.text(103.0, (YB + YT) / 2 + 2.0, "to loop", fontsize=5.6, va="bottom", ha="right")
c.text(54, 44.0, "Least-cost converter at %.2f%% per year, 9 MPa" % REF_RATE, ha="center", va="top", fontsize=6.4,
       fontweight="bold")
c.text(54, 40.2, "fused iron %d%% of the catalyst volume" % round(100 * fe_frac), ha="center", va="top", fontsize=5.6,
       color=DARK_G)
pg.letter("c", 2, 50)

# ---- d: rate ratio along the bed -----------------------------------------------------------------------------------
val = json.load(open(os.path.join(INR, "validation.json"), encoding="utf-8"))["rate_ratio_90bar_Keestra"]
yv = sorted(val, key=lambda k: float(k.split("_")[-1]))
xa = np.array([100 * float(k.split("_")[-1]) for k in yv])
pk = np.array([val[k]["Ru_over_Fe_per_kg"] for k in yv])
pm = np.array([val[k]["Ru_over_Fe_per_m3"] for k in yv])
assert round(pk[0]) == 9 and round(pk[-1]) == 62
d = pg.ax(130, 10, 48, 36)
d.plot(xa, pk, "-o", color=RU, ms=2.6, mec=INK, mew=0.3, lw=0.9, label="per kg")
d.plot(xa, pm, "-s", color=PALE_B, ms=2.6, mec=INK, mew=0.3, lw=0.9, label="per m$^3$")
d.set_yscale("log")
d.set_ylim(1, 100)
d.set_xlim(0, 16)
d.set_xticks([0, 4, 8, 12, 16])
d.set_xlabel("NH$_3$ (%)")
d.set_ylabel("Ru/C to Fe rate ratio", labelpad=1)
d.yaxis.set_major_formatter(__import__("matplotlib").ticker.FuncFormatter(lambda v, _: "%g" % v))
for x_, y_ in ((xa[0], pk[0]), (xa[-1], pk[-1])):
    d.text(x_, y_ * 1.25, "%d" % round(y_), fontsize=5.3, ha="center", va="bottom")
d.legend(frameon=False, fontsize=5.0, loc="lower right", handlelength=1.2, borderaxespad=0.2)
boxed(d)
pg.letter("d", 118, 50)

pg.save(HERE, "FigFrontier")
print("break-even KAAP %.3f, each at own optimum %.3f %%/y; Fe-first optimal up to %.2f %%/y; at %.2f %%/y: "
      "%s, Ru/C %.0f %% of volume, staged %.3f vs all-Fe %.3f USD/t" % (
          be_kaap, be_bench, win_hi, REF_RATE, pat, 100 * float(best["Ru_volume_fraction"]), cost(best), s_fe[i_ref]))
