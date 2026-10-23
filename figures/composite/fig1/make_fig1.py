"""Figure 1 — a globally correlated catalyst screen inverts at its top, where the plant decides.

Composite, 183 mm wide. Data from fig1_metals.csv / fig1_rolling.csv (written by
fig1_data.py from pinned provenance), the model's own volcano curve
(closure/scaling_reachability.csv) and the Fe cost pools of the panel-a cost icon
(results.json), all from the NH3-FINAL-1.2 canonical run. Step-site renders from build_structures.py.

    pur_bridge_env/python make_fig1.py            -> Fig1.{svg,pdf,png}
"""
import csv
import json
import math
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.image as mpimg  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
RUN = os.path.join(REPO, "provenance/nh3_final_1_2/source_harness/outputs/nh3_final_1_2_20261013")
CURVE = os.path.join(RUN, "closure", "scaling_reachability.csv")
FE_POOLS = json.load(open(os.path.join(RUN, "results.json"), encoding="utf-8"))[
    "deterministic"]["metals"]["Fe"]["feasible"]["breakdown"]

# ---- visual system ---------------------------------------------------------
# palette of figures/composite/style.py (2026-10-21)
INK, MID, GRID = "#1B1B1B", "#5F646C", "#E4E4E4"
C = {"Fe": "#6E9F60", "Ru": "#5677B5", "Os": "#97ABD4"}
OTHER, RED = "#B5B9C1", "#D9474F"
TINT_G, TINT_B, PAPER = "#EAF2E5", "#E8EDF7", "#F3F1F0"
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


def mnum(fmt, v):
    """A number with a typographic minus sign."""
    return (fmt % v).replace("-", "−")


OFF = ("Ag", "Au")                                     # off-scale metals, values printed beside the arrows


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


# ---- a: three optima along the forward chain (laid out in the editable Fig1a.pptx) ----
# Fig1a.pptx holds panel a with its letter as native text, boxes and arrows (author's layout, 2026-10-23); it was
# derived from this script's former matplotlib drawing (tools/svg_panel_to_pptx.py) and is placed from its 600-dpi
# export Fig1a_from_pptx.png at the position that drawing occupied: top-left 0.942 mm, 0.713 mm; 121.691 x 55.880 mm.
PANEL_A = dict(png="Fig1a_from_pptx.png", left=0.942, top=0.713, w=121.691, h=55.880)
_pa = mpimg.imread(os.path.join(HERE, PANEL_A["png"]))
_ax_a = ax_mm(PANEL_A["left"], H_MM - PANEL_A["top"] - PANEL_A["h"], PANEL_A["w"], PANEL_A["h"])
_ax_a.imshow(_pa, extent=(0, 1, 0, 1), aspect="auto", interpolation="none")
_ax_a.axis("off")

# ---- b: the three frontier candidates --------------------------------------
letter("b", 124.0, 168.0)
axb = ax_mm(125.0, 114.0, 56.0, 52.0)
axb.set_xlim(0, 56)
axb.set_ylim(0, 52)
axb.axis("off")
axb.text(0.5, 50.0, "The three leaders", fontsize=7, fontweight="bold", va="top")
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
axc.text(sum(fr) / 2, -30.6, "three\nleaders", fontsize=5.3, color="#304C86", ha="center", va="bottom")
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
axc.text(2.55, -26.4, "Ag, Au\n(%s)" % ", ".join(mnum("%d", round(M[m]["logTOF_673K"])) for m in OFF), fontsize=5.3, color=MID, ha="center", va="bottom")
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
axd.text(3.3, lim90 + 0.6, "90 m$^3$ bed limit", fontsize=5.8, color="#467238", ha="right", va="bottom")
axd.text(3.3, -4.2, "feasible bed", fontsize=5.8, color="#467238", ha="right", va="bottom")
scatter_metals(axd, "E_N_eV", "log10_min_bed_m3", clip=(-5, 25))
lab_d = {"Ru": ("Ru", -6, -1, "right"), "Os": ("Os", 6, 1, "left"), "Fe": ("Fe", -6, 0, "right"),
         "Rh": ("Rh, Ir", -6, 4, "right"), "Co": ("Co", 6, 0, "left"), "Ni": ("Ni", 6, 0, "left"),
         "Re": ("Re, Mo", 0, 7, "center"), "W": ("W", 6, 0, "left"), "Pd": ("Pd, Pt", -6, 0, "right"),
         "Cu": ("Cu", -6, 0, "right")}
for m, (txt, dx, dy, ha) in lab_d.items():
    axd.annotate(txt, (M[m]["E_N_eV"], M[m]["log10_min_bed_m3"]), xytext=(dx, dy), textcoords="offset points",
                 fontsize=5.8 if m not in C else 6.5, fontweight="bold" if m in C else "normal",
                 color=INK if m in C else MID, ha=ha, va="center")
# Ag and Au lie above the axis range: arrows leave the frame at the top, values given beside them and in the caption
for m, dx in (("Ag", -0.06), ("Au", 0.06)):
    axd.annotate("", xy=(M[m]["E_N_eV"] + dx, 27.4), xytext=(M[m]["E_N_eV"] + dx, 23.2),
                 arrowprops=dict(arrowstyle="-|>", lw=0.5, color=MID, mutation_scale=4), annotation_clip=False)
axd.text(2.55, 27.5, "Ag, Au (%s)" % ", ".join("%d" % round(M[m]["log10_min_bed_m3"]) for m in OFF), fontsize=5.3,
         color=MID, ha="center", va="bottom", clip_on=False)
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
axe.text(0.03, 0.97, "Ag, Au off scale\n(TOF %s)" % ", ".join("10$^{%s}$" % mnum("%d", round(M[m]["logTOF_673K"]))
                                                           for m in OFF), transform=axe.transAxes,
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
    axf.text(-0.12, a, m, ha="right", va="center", fontsize=6.3 if front else 5.6,
             fontweight="bold" if front else "normal", color=INK if front else MID)
    axf.text(1.12, e, m, ha="left", va="center", fontsize=6.3 if front else 5.6,
             fontweight="bold" if front else "normal", color=INK if front else MID)
for xa in (-0.055, 1.055):          # rank axes between the labels and the markers
    axf.plot([xa, xa], [0.55, 15.45], color=INK, lw=0.6, solid_capstyle="butt", zorder=2)
axf.text(0, -0.25, "Atomic\nactivity rank", ha="center", va="bottom", fontsize=6.3)
axf.text(1, -0.25, "Economic\nrank", ha="center", va="bottom", fontsize=6.3)
axf.text(0.5, 16.55, "top 3: ρ = %s" % mnum("%.2f", float(rolling[0]["rho_raw"])), ha="center", va="center", fontsize=6.3, color=RED,
         fontweight="bold")
axf.text(0.5, 17.6, "all 15: ρ = %.3f" % float(rolling[-1]["rho_raw"]), ha="center", va="center", fontsize=6.0,
         color=MID)

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
axg.annotate("K = %d: ρ = %s" % (K[0], mnum("%.2f", rho[0])), (K[0], rho[0]), xytext=(8, -2), textcoords="offset points",
             fontsize=6.0, color=RED, fontweight="bold", va="center")
axg.annotate("K = 15: ρ = %.3f" % rho[-1], (K[-1], rho[-1]), xytext=(14.6, 0.30), textcoords="data",
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
axh.set_ylim(0, 26)
axh.set_ylabel(r"Catalyst-dependent cost (USD t$^{-1}$ NH$_3$)")
axh.yaxis.set_minor_locator(matplotlib.ticker.MultipleLocator(2.5))
axh.text(0.5, 0.965, "economic #1 = atomic #3", transform=axh.transAxes, ha="center", va="top",
         fontsize=6.3, color=RED, fontweight="bold")

sys.path.insert(0, os.path.dirname(HERE))
import tweak  # noqa: E402  hand adjustments from Fig1.tweaks.json (tools/figure_tweak.py)
tweak.apply(fig, HERE, "Fig1")
for ext in ("svg", "pdf", "png"):
    fig.savefig(os.path.join(HERE, "Fig1." + ext), dpi=600, facecolor=fig.get_facecolor())
print("wrote Fig1.{svg,pdf,png}  %.0f x %.0f mm" % (W_MM, H_MM))
