"""Figure 1 — a globally correlated catalyst screen inverts at the industrial decision frontier.

Composite, 183 mm wide. Data from fig1_metals.csv / fig1_rolling.csv (written by
fig1_data.py from pinned provenance) and the model's own volcano curve
(closure/scaling_reachability.csv). Step-site renders from build_structures.py.

    pur_bridge_env/python make_fig1.py            -> Fig1.{svg,pdf,png}
"""
import csv
import math
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.image as mpimg  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
CURVE = os.path.join(REPO, "provenance/nh3_final_1_1/source_harness/outputs/"
                           "nh3_final_20260905T134204Z/closure/scaling_reachability.csv")

# ---- visual system ---------------------------------------------------------
INK, MID, GRID = "#1B1B1B", "#6B6F76", "#E4E4E4"
C = {"Fe": "#89AA7B", "Ru": "#7789B7", "Os": "#9DACCB"}
OTHER, RED = "#B3B8C0", "#EB6969"
TINT_G, TINT_B, PAPER = "#E4ECDE", "#E3E7F0", "#F0EEEF"
W_MM, H_MM = 183.0, 170.0

plt.rcParams.update({
    "font.family": "Arial", "font.size": 7, "axes.linewidth": 0.6,
    "axes.edgecolor": INK, "axes.labelcolor": INK, "text.color": INK,
    "xtick.color": INK, "ytick.color": INK, "xtick.labelsize": 6.5, "ytick.labelsize": 6.5,
    "xtick.direction": "in", "ytick.direction": "in",
    "xtick.major.size": 2.4, "ytick.major.size": 2.4, "xtick.minor.size": 1.3, "ytick.minor.size": 1.3,
    "xtick.major.width": 0.6, "ytick.major.width": 0.6, "xtick.minor.width": 0.5, "ytick.minor.width": 0.5,
    "axes.labelsize": 7, "axes.labelpad": 2.0,
    "mathtext.fontset": "custom", "mathtext.rm": "Arial", "mathtext.it": "Arial:italic",
    "mathtext.bf": "Arial:bold", "mathtext.default": "regular",
    "svg.fonttype": "none", "pdf.fonttype": 42, "legend.frameon": False,
})

fig = plt.figure(figsize=(W_MM / 25.4, H_MM / 25.4))


def ax_mm(x, y, w, h, **kw):
    """Axes placed in millimetres from the figure's bottom-left corner."""
    return fig.add_axes([x / W_MM, y / H_MM, w / W_MM, h / H_MM], **kw)


def letter(ch, x, y):
    fig.text(x / W_MM, y / H_MM, ch, fontsize=9, fontweight="bold", va="top", ha="left")


def read_csv(path):
    return list(csv.DictReader(open(path, encoding="utf-8")))


metals = read_csv(os.path.join(HERE, "fig1_metals.csv"))
rolling = read_csv(os.path.join(HERE, "fig1_rolling.csv"))
M = {r["metal"]: {k: (float(v) if k != "metal" else v) for k, v in r.items()} for r in metals}
curve = read_csv(CURVE)
cE = np.array([float(r["E_N_eV"]) for r in curve])
cG = np.array([float(r["gain_673K"]) for r in curve])
curve_logtof = M["Ru"]["logTOF_673K"] + np.log10(cG)


def color_of(m):
    return C.get(m, OTHER)


def crop_rgba(path):
    img = mpimg.imread(path)
    a = img[:, :, 3] if img.shape[2] == 4 else (img[:, :, :3].min(axis=2) < 0.98).astype(float)
    ys, xs = np.where(a > 0.02)
    pad = 6
    return img[max(ys.min() - pad, 0):ys.max() + pad, max(xs.min() - pad, 0):xs.max() + pad]


def boxed(ax):
    for s in ax.spines.values():
        s.set_linewidth(0.6)
    ax.tick_params(which="both", top=False, right=False)


# ---- a: forward propagation and backward design ----------------------------
letter("a", 2.0, 168.0)
ax = ax_mm(4.0, 114.0, 118.0, 52.0)
ax.set_xlim(0, 118)
ax.set_ylim(0, 52)
ax.set_aspect("equal")
ax.axis("off")
xs = [12.0, 36.0, 60.0, 84.0, 107.0]
yc = 31.0
ax.text(1.0, 50.0, "Forward propagation", fontsize=7, fontweight="bold", va="top")

# stage 1: step site render
ru_img = crop_rgba(os.path.join(HERE, "renders", "Ru_211_N.png"))
h_img = 17.0
w_img = h_img * ru_img.shape[1] / ru_img.shape[0]
ax.imshow(ru_img, extent=(xs[0] - w_img / 2, xs[0] + w_img / 2, yc - h_img / 2, yc + h_img / 2), zorder=3)

# stage 2: microkinetic volcano icon (the model curve, normalised)
vx = np.interp(np.linspace(0, 1, 60), (cE - cE.min()) / (cE.max() - cE.min()), (cE - cE.min()) / (cE.max() - cE.min()))
vy = np.interp(vx, (cE - cE.min()) / (cE.max() - cE.min()),
               (curve_logtof - curve_logtof.min()) / (curve_logtof.max() - curve_logtof.min()))
ax.plot([xs[1] - 8.0, xs[1] - 8.0, xs[1] + 8.0], [yc + 7.0, yc - 7.0, yc - 7.0], color=MID, lw=0.6, zorder=1)
ax.plot(xs[1] - 7.5 + 15.0 * vx, yc - 6.0 + 12.0 * vy, color=INK, lw=0.9, zorder=2)
for m, off in (("Ru", 0.0), ("Fe", 0.0)):
    e = (M[m]["E_N_eV"] - cE.min()) / (cE.max() - cE.min())
    t = (M[m]["logTOF_673K"] - curve_logtof.min()) / (curve_logtof.max() - curve_logtof.min())
    ax.plot(xs[1] - 7.5 + 15.0 * e, yc - 6.0 + 12.0 * t, "o", ms=3.4, mfc=C[m], mec=INK, mew=0.4, zorder=3)
ax.text(xs[1] - 7.8, yc + 5.6, "TOF", fontsize=5.5, color=MID, va="top")
ax.text(xs[1] + 7.8, yc - 7.2, r"$E_\mathrm{N}$", fontsize=5.5, color=MID, ha="right", va="bottom")

# stage 3: packed-bed converter
ax.add_patch(FancyBboxPatch((xs[2] - 4.2, yc - 8.5), 8.4, 17.0, boxstyle="round,pad=0,rounding_size=2.6",
                            fc="white", ec=INK, lw=0.8, zorder=2))
rng = np.random.default_rng(7)
bx = rng.uniform(xs[2] - 3.2, xs[2] + 3.2, 70)
by = rng.uniform(yc - 6.2, yc + 3.6, 70)
ax.scatter(bx, by, s=2.2, c=C["Ru"], edgecolors="none", zorder=3)
ax.plot([xs[2] - 3.6, xs[2] + 3.6], [yc + 4.4] * 2, color=INK, lw=0.5, zorder=3)
ax.annotate("", xy=(xs[2], yc + 8.4), xytext=(xs[2], yc + 11.5),
            arrowprops=dict(arrowstyle="-|>", lw=0.6, color=MID, mutation_scale=5))
ax.annotate("", xy=(xs[2], yc - 11.5), xytext=(xs[2], yc - 8.4),
            arrowprops=dict(arrowstyle="-|>", lw=0.6, color=MID, mutation_scale=5))

# stage 4: synthesis loop (compressor -> converter -> separator -> recycle)
cx0 = xs[3] - 9.0
ax.add_patch(Polygon([[cx0 - 2.4, yc - 3.2], [cx0 - 2.4, yc + 3.2], [cx0 + 2.4, yc + 1.8], [cx0 + 2.4, yc - 1.8]],
                     closed=True, fc="white", ec=INK, lw=0.7, zorder=2))
ax.add_patch(Rectangle((xs[3] - 1.6, yc - 5.5), 3.2, 11.0, fc="white", ec=INK, lw=0.7, zorder=2))
ax.add_patch(Rectangle((xs[3] - 1.2, yc - 4.2), 2.4, 7.0, fc=C["Ru"], ec="none", alpha=0.55, zorder=3))
sx = xs[3] + 8.2
ax.add_patch(FancyBboxPatch((sx - 2.2, yc - 4.0), 4.4, 8.0, boxstyle="round,pad=0,rounding_size=1.4",
                            fc="white", ec=INK, lw=0.7, zorder=2))
ax.add_patch(Rectangle((sx - 1.9, yc - 3.7), 3.8, 2.4, fc="#C6CCDC", ec="none", zorder=3))
for x0, x1 in ((cx0 + 2.4, xs[3] - 1.6), (xs[3] + 1.6, sx - 2.2)):
    ax.annotate("", xy=(x1, yc), xytext=(x0, yc), arrowprops=dict(arrowstyle="-|>", lw=0.6, color=INK,
                                                                     mutation_scale=5, shrinkA=0, shrinkB=0))
ax.plot([sx, sx, cx0, cx0], [yc + 4.0, yc + 8.2, yc + 8.2, yc + 3.2], color=INK, lw=0.6, zorder=2)
ax.annotate("", xy=(cx0, yc + 3.3), xytext=(cx0, yc + 5.0),
            arrowprops=dict(arrowstyle="-|>", lw=0.6, color=INK, mutation_scale=5, shrinkA=0, shrinkB=0))
ax.text((sx + cx0) / 2, yc + 8.8, "recycle", fontsize=5.3, color=MID, ha="center", va="bottom")
ax.annotate("", xy=(sx, yc - 8.4), xytext=(sx, yc - 4.0),
            arrowprops=dict(arrowstyle="-|>", lw=0.6, color=INK, mutation_scale=5, shrinkA=0, shrinkB=0))
ax.text(sx + 0.8, yc - 8.6, r"NH$_3$(l)", fontsize=5.3, color=MID, va="top")

# stage 5: catalyst-dependent cost stack
segs = [("fresh-feed\ncompression", 9.66, "#C6CCDC"), ("compressor\nCAPEX", 3.87, "#9DACCB"),
        ("vessel + reactor", 0.92, "#CBD7C3"), ("recycle", 0.76, "#ACBF9F")]
tot = sum(s[1] for s in segs)
y0 = yc - 8.0
for name, v, col in segs:
    hh = 16.0 * v / tot
    ax.add_patch(Rectangle((xs[4] - 3.6, y0), 7.2, hh, fc=col, ec="white", lw=0.5, zorder=2))
    y0 += hh
ax.add_patch(Rectangle((xs[4] - 3.6, yc - 8.0), 7.2, 16.0, fc="none", ec=INK, lw=0.6, zorder=3))
ax.text(xs[4] + 5.0, yc + 8.0, "USD t$^{-1}$", fontsize=5.3, color=MID, va="top")

labels = [("Atomic descriptor", r"N* at the step, $E_\mathrm{N}$"),
          ("Microkinetics", "TOF at 673 K"),
          ("Catalyst inventory", r"$V_\mathrm{bed}\leq$ 90 m$^3$"),
          ("Synthesis loop", r"$T$, $P$, $T_\mathrm{sep}$ reoptimized"),
          ("Economics", "catalyst-dependent cost")]
for x, (t1, t2) in zip(xs, labels):
    ax.text(x, yc - 13.0, t1, ha="center", va="top", fontsize=6.5, fontweight="bold")
    ax.text(x, yc - 16.6, t2, ha="center", va="top", fontsize=6.0, color=MID)
# stage-to-stage connectors at mid-height, edge to edge
for x0, x1 in ((xs[0] + 10.0, xs[1] - 9.4), (xs[1] + 9.0, xs[2] - 5.0),
               (xs[2] + 5.0, cx0 - 2.5), (sx + 2.9, xs[4] - 4.4)):
    ax.annotate("", xy=(x1, yc), xytext=(x0, yc),
                arrowprops=dict(arrowstyle="-|>", lw=1.0, color=INK, mutation_scale=7, shrinkA=0, shrinkB=0))
# backward design return path
ax.add_patch(FancyArrowPatch((xs[4], 4.6), (xs[0], 4.6), arrowstyle="-|>", mutation_scale=8,
                             lw=0.9, color=RED, linestyle=(0, (3, 2)), connectionstyle="arc3,rad=0"))
ax.plot([xs[4], xs[4]], [4.6, yc - 20.0], color=RED, lw=0.9, ls=(0, (3, 2)))
ax.plot([xs[0], xs[0]], [4.6, yc - 20.0], color=RED, lw=0.9, ls=(0, (3, 2)))
ax.text((xs[0] + xs[4]) / 2, 6.0, "Backward design: activity multiplier α* needed for parity  vs  "
        "headroom reachable on the scaling line", fontsize=6.0, color=RED, ha="center", va="bottom")

# ---- b: the three frontier candidates --------------------------------------
letter("b", 124.0, 168.0)
axb = ax_mm(125.0, 114.0, 56.0, 52.0)
axb.set_xlim(0, 56)
axb.set_ylim(0, 52)
axb.axis("off")
axb.text(0.5, 50.0, "Decision-frontier candidates", fontsize=7, fontweight="bold", va="top")
order = ["Ru", "Os", "Fe"]
fmt_price = {"Ru": "53,853", "Os": "142,650", "Fe": "8"}
for i, m in enumerate(order):
    img = crop_rgba(os.path.join(HERE, "renders", "%s_211_N.png" % m))
    cx = 9.3 + i * 18.7
    hh = 15.5
    ww = hh * img.shape[1] / img.shape[0]
    if ww > 17.5:
        ww, hh = 17.5, 17.5 * img.shape[0] / img.shape[1]
    axb.imshow(img, extent=(cx - ww / 2, cx + ww / 2, 30.0 - hh / 2, 30.0 + hh / 2), zorder=2)
    axb.text(cx, 19.8, m, ha="center", va="top", fontsize=8, fontweight="bold", color=INK)
    axb.plot([cx - 5.5, cx + 5.5], [20.8, 20.8], color=C[m], lw=2.2, solid_capstyle="butt")
    axb.text(cx, 16.2, r"$E_\mathrm{N}$ = %s eV" % ("%.2f" % M[m]["E_N_eV"]).replace("-", "−"),
             ha="center", va="top", fontsize=6)
    axb.text(cx, 12.6, "USD %s kg$^{-1}$" % fmt_price[m], ha="center", va="top", fontsize=6)
    ar, er = int(M[m]["atomic_rank"]), int(M[m]["economic_rank"])
    axb.text(cx, 8.4, "#%d  →  #%d" % (ar, er), ha="center", va="top", fontsize=6.5,
             fontweight="bold", color=RED if m == "Fe" else INK)
axb.text(28.0, 3.2, "atomic rank  →  economic rank", ha="center", va="top", fontsize=5.8, color=MID)

# ---- row 2 ------------------------------------------------------------------
ROW2_Y, ROW2_H = 66.0, 36.0
COLS = [(14.0, 46.0), (75.0, 46.0), (135.0, 46.0)]


def scatter_metals(axx, xkey, ykey, xfun=lambda v: v, yfun=lambda v: v, clip=None):
    for r in metals:
        m = r["metal"]
        x, y = xfun(float(r[xkey])), yfun(float(r[ykey]))
        if clip and not (clip[0] <= y <= clip[1]):
            continue
        front = m in C
        axx.plot(x, y, "o", ms=4.2 if front else 3.0, mfc=color_of(m), mec=INK if front else "#8B9098",
                 mew=0.5 if front else 0.3, zorder=4 if front else 3)


# c: volcano
letter("c", 2.0, ROW2_Y + ROW2_H + 6.0)
axc = ax_mm(COLS[0][0], ROW2_Y, COLS[0][1], ROW2_H)
boxed(axc)
fr = (min(M[m]["E_N_eV"] for m in C) - 0.09, max(M[m]["E_N_eV"] for m in C) + 0.09)
axc.axvspan(*fr, color=TINT_B, zorder=0, lw=0)
axc.text(sum(fr) / 2, -30.6, "decision\nfrontier", fontsize=5.3, color="#5A6480", ha="center", va="bottom")
axc.plot(cE, curve_logtof, color=INK, lw=0.9, zorder=2)
scatter_metals(axc, "E_N_eV", "logTOF_673K", clip=(-32, 1))
lab_c = {"Ru": ("Ru", -6, 5, "right"), "Os": ("Os", 6, 5, "left"), "Fe": ("Fe", -6, -1, "right"),
         "Rh": ("Rh, Ir", 6, 2, "left"), "Co": ("Co", 6, 0, "left"), "Ni": ("Ni", 6, 0, "left"),
         "Re": ("Re, Mo", 6, -4, "left"), "W": ("W", 6, -1, "left"), "Pd": ("Pd, Pt", 6, 0, "left"),
         "Cu": ("Cu", 6, 0, "left")}
for m, (txt, dx, dy, ha) in lab_c.items():
    axc.annotate(txt, (M[m]["E_N_eV"], M[m]["logTOF_673K"]), xytext=(dx, dy), textcoords="offset points",
                 fontsize=5.8 if m not in C else 6.5, fontweight="bold" if m in C else "normal",
                 color=INK if m in C else MID, ha=ha, va="center")
for m, dx in (("Ag", -0.06), ("Au", 0.06)):
    axc.annotate("", xy=(M[m]["E_N_eV"] + dx, -31.6), xytext=(M[m]["E_N_eV"] + dx, -27.2),
                 arrowprops=dict(arrowstyle="-|>", lw=0.5, color=MID, mutation_scale=4))
axc.text(2.55, -26.4, "Ag, Au\n(−52, −53)", fontsize=5.3, color=MID, ha="center", va="bottom")
axc.set_xlim(-2.5, 3.4)
axc.set_ylim(-32, 1.5)
axc.set_xlabel(r"$E_\mathrm{N}$ at the step (eV)")
axc.set_ylabel(r"log$_{10}$ TOF at 673 K (s$^{-1}$)")
axc.minorticks_on()

# d: minimum catalyst bed
letter("d", 63.0, ROW2_Y + ROW2_H + 6.0)
axd = ax_mm(COLS[1][0], ROW2_Y, COLS[1][1], ROW2_H)
boxed(axd)
lim90 = math.log10(90.0)
axd.axhspan(-5, lim90, color=TINT_G, zorder=0, lw=0)
axd.axhline(lim90, color=C["Fe"], lw=0.8, ls=(0, (3, 2)), zorder=1)
axd.text(3.3, lim90 + 0.6, "90 m$^3$ bed limit", fontsize=5.8, color="#5E7A52", ha="right", va="bottom")
axd.text(3.3, -4.2, "industrially feasible", fontsize=5.8, color="#5E7A52", ha="right", va="bottom")
scatter_metals(axd, "E_N_eV", "log10_min_bed_m3", clip=(-5, 25))
lab_d = {"Ru": ("Ru", -6, -1, "right"), "Os": ("Os", 6, 1, "left"), "Fe": ("Fe", -6, 0, "right"),
         "Rh": ("Rh, Ir", -6, 4, "right"), "Co": ("Co", 6, 0, "left"), "Ni": ("Ni", 6, 0, "left"),
         "Re": ("Re, Mo", 0, 7, "center"), "W": ("W", 6, 0, "left"), "Pd": ("Pd, Pt", -6, 0, "right"),
         "Cu": ("Cu", -6, 0, "right")}
for m, (txt, dx, dy, ha) in lab_d.items():
    axd.annotate(txt, (M[m]["E_N_eV"], M[m]["log10_min_bed_m3"]), xytext=(dx, dy), textcoords="offset points",
                 fontsize=5.8 if m not in C else 6.5, fontweight="bold" if m in C else "normal",
                 color=INK if m in C else MID, ha=ha, va="center")
for m, dx in (("Ag", -0.06), ("Au", 0.06)):
    axd.annotate("", xy=(M[m]["E_N_eV"] + dx, 24.6), xytext=(M[m]["E_N_eV"] + dx, 20.2),
                 arrowprops=dict(arrowstyle="-|>", lw=0.5, color=MID, mutation_scale=4))
axd.text(2.55, 19.5, "Ag, Au\n(43, 45)", fontsize=5.3, color=MID, ha="center", va="top")
axd.set_xlim(-2.5, 3.4)
axd.set_ylim(-5, 25)
axd.set_xlabel(r"$E_\mathrm{N}$ at the step (eV)")
axd.set_ylabel(r"log$_{10}$ minimum bed volume (m$^3$)")
axd.minorticks_on()

# e: price versus activity
letter("e", 123.0, ROW2_Y + ROW2_H + 6.0)
axe = ax_mm(COLS[2][0], ROW2_Y, COLS[2][1], ROW2_H)
boxed(axe)
for r in metals:
    m = r["metal"]
    x, y = float(r["logTOF_673K"]), float(r["price_USD_kg"])
    if x < -31:
        continue
    front = m in C
    axe.plot(x, y, "o", ms=4.2 if front else 3.0, mfc=color_of(m), mec=INK if front else "#8B9098",
             mew=0.5 if front else 0.3, zorder=4 if front else 3)
axe.set_yscale("log")
lab_e = {"Ru": ("Ru", -6, -2, "right"), "Os": ("Os", -6, 2, "right"), "Fe": ("Fe", -6, 0, "right"),
         "Rh": ("Rh, Ir", -6, 0, "right"), "Co": ("Co", 6, 0, "left"), "Re": ("Re", 6, 0, "left"),
         "Mo": ("Mo", 0, 7, "center"), "Ni": ("Ni", 6, 0, "left"), "W": ("W", -6, 0, "right"),
         "Pd": ("Pd, Pt", 6, 0, "left"), "Cu": ("Cu", 6, 0, "left")}
for m, (txt, dx, dy, ha) in lab_e.items():
    axe.annotate(txt, (M[m]["logTOF_673K"], M[m]["price_USD_kg"]), xytext=(dx, dy), textcoords="offset points",
                 fontsize=5.8 if m not in C else 6.5, fontweight="bold" if m in C else "normal",
                 color=INK if m in C else MID, ha=ha, va="center")
fe, ru = M["Fe"], M["Ru"]
axe.annotate("", xy=(ru["logTOF_673K"] + 0.05, fe["price_USD_kg"]), xytext=(fe["logTOF_673K"], fe["price_USD_kg"]),
             arrowprops=dict(arrowstyle="-|>", lw=0.6, color=RED, mutation_scale=5, shrinkA=3))
axe.annotate("", xy=(ru["logTOF_673K"], ru["price_USD_kg"] * 0.8),
             xytext=(ru["logTOF_673K"], fe["price_USD_kg"] * 1.25),
             arrowprops=dict(arrowstyle="-|>", lw=0.6, color=RED, mutation_scale=5))
axe.text((fe["logTOF_673K"] + ru["logTOF_673K"]) / 2, fe["price_USD_kg"] * 0.55,
         "%d× activity" % round(10 ** (ru["logTOF_673K"] - fe["logTOF_673K"])),
         fontsize=5.8, color=RED, ha="center", va="top")
axe.text(ru["logTOF_673K"] - 0.5, math.sqrt(fe["price_USD_kg"] * ru["price_USD_kg"]),
         "%s×\nprice" % format(round(ru["price_USD_kg"] / fe["price_USD_kg"]), ","),
         fontsize=5.8, color=RED, ha="right", va="center")
axe.set_xlim(-30, 0.5)
axe.set_ylim(1, 2e6)
axe.set_xlabel(r"log$_{10}$ TOF at 673 K (s$^{-1}$)")
axe.set_ylabel(r"Metal price (USD kg$^{-1}$)")
axe.text(0.03, 0.97, "Ag, Au off scale\n(TOF 10$^{−52}$, 10$^{−53}$)", transform=axe.transAxes,
         fontsize=5.3, color=MID, ha="left", va="top")

# ---- row 3 ------------------------------------------------------------------
ROW3_Y, ROW3_H = 11.0, 36.0

# f: rank slopegraph
letter("f", 2.0, ROW3_Y + ROW3_H + 6.0)
axf = ax_mm(8.0, ROW3_Y, 54.0, ROW3_H)
axf.set_xlim(-0.55, 1.55)
axf.set_ylim(17.9, 0.3)
axf.axis("off")
for r in metals:
    m = r["metal"]
    a, e = float(r["atomic_rank"]), float(r["economic_rank"])
    front = m in C
    axf.plot([0, 1], [a, e], color=color_of(m) if front else "#C9CDD3", lw=1.6 if front else 0.6,
             zorder=3 if front else 1, solid_capstyle="round")
    axf.plot([0, 1], [a, e], "o", ms=3.0 if front else 2.0, color=color_of(m) if front else "#AEB3BA",
             mec=INK if front else "none", mew=0.4, zorder=4)
    axf.text(-0.08, a, m, ha="right", va="center", fontsize=6.3 if front else 5.6,
             fontweight="bold" if front else "normal", color=INK if front else MID)
    axf.text(1.08, e, m, ha="left", va="center", fontsize=6.3 if front else 5.6,
             fontweight="bold" if front else "normal", color=INK if front else MID)
axf.text(0, -0.25, "Atomic\nactivity rank", ha="center", va="bottom", fontsize=6.3)
axf.text(1, -0.25, "Economic\nrank", ha="center", va="bottom", fontsize=6.3)
axf.text(0.5, 16.55, "top 3: ρ = −0.50", ha="center", va="center", fontsize=6.3, color=RED,
         fontweight="bold")
axf.text(0.5, 17.6, "all 15: ρ = 0.929", ha="center", va="center", fontsize=6.0, color=MID)

# g: rolling Top-K fidelity
letter("g", 63.0, ROW3_Y + ROW3_H + 6.0)
axg = ax_mm(COLS[1][0], ROW3_Y, COLS[1][1], ROW3_H)
boxed(axg)
K = np.array([float(r["K"]) for r in rolling])
rho = np.array([float(r["rho_raw"]) for r in rolling])
axg.axhline(0, color=MID, lw=0.5, ls=(0, (2, 2)), zorder=1)
axg.fill_between(K, rho, 0, where=rho < 0, color=RED, alpha=0.18, lw=0, interpolate=True)
axg.plot(K, rho, color=INK, lw=0.9, zorder=2)
axg.plot(K, rho, "o", ms=3.0, mfc="white", mec=INK, mew=0.6, zorder=3)
axg.plot(K[0], rho[0], "o", ms=4.2, mfc=RED, mec=INK, mew=0.5, zorder=4)
axg.annotate("K = 3: ρ = −0.50", (K[0], rho[0]), xytext=(8, -2), textcoords="offset points",
             fontsize=6.0, color=RED, fontweight="bold", va="center")
axg.annotate("K = 15: ρ = 0.929", (K[-1], rho[-1]), xytext=(14.6, 0.30), textcoords="data",
             fontsize=6.0, color=INK, ha="right", va="center",
             arrowprops=dict(arrowstyle="-", lw=0.5, color=MID, shrinkA=1, shrinkB=3))
axg.set_xlim(2.3, 15.7)
axg.set_ylim(-0.75, 1.1)
axg.set_xticks([3, 6, 9, 12, 15])
axg.set_xlabel("Top-K candidates by activity")
axg.set_ylabel(r"Spearman $\rho$ (atomic vs economic)")
axg.minorticks_on()

# h: the frontier decision
letter("h", 123.0, ROW3_Y + ROW3_H + 6.0)
axh = ax_mm(COLS[2][0], ROW3_Y, COLS[2][1], ROW3_H)
boxed(axh)
bars = ["Fe", "Ru", "Os"]
vals = [M[m]["cost_USD_t"] for m in bars]
axh.bar(range(3), vals, width=0.62, color=[C[m] for m in bars], edgecolor=INK, linewidth=0.6, zorder=2)
for i, (m, v) in enumerate(zip(bars, vals)):
    axh.text(i, v + 0.6, "%.3f" % v, ha="center", va="bottom", fontsize=6.3, fontweight="bold")
    axh.text(i, -0.135, "atomic #%d" % int(M[m]["atomic_rank"]), transform=axh.get_xaxis_transform(),
             ha="center", va="top", fontsize=5.9, color=RED if m == "Fe" else MID,
             fontweight="bold" if m == "Fe" else "normal")
axh.set_xticks(range(3))
axh.set_xticklabels(bars, fontsize=6.8, fontweight="bold")
axh.tick_params(axis="x", length=0)
axh.set_ylim(0, 34)
axh.set_ylabel(r"Catalyst-dependent cost (USD t$^{-1}$ NH$_3$)")
axh.yaxis.set_minor_locator(matplotlib.ticker.MultipleLocator(2.5))
axh.text(0.5, 0.965, "economic #1 = atomic #3", transform=axh.transAxes, ha="center", va="top",
         fontsize=6.3, color=RED, fontweight="bold")

for ext in ("svg", "pdf", "png"):
    fig.savefig(os.path.join(HERE, "Fig1." + ext), dpi=600 if ext == "png" else None, facecolor="white")
print("wrote Fig1.{svg,pdf,png}  %.0f x %.0f mm" % (W_MM, H_MM))
