"""Figure: arrangement costs, KAAP-type converter paths and decision maps.  python plot_staged.py -> staged_converter.png"""
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.colors import ListedColormap  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

import kinetics as K  # noqa: E402

HERE = Path(__file__).resolve().parent
INK, INK2, GRID = "#0b0b0b", "#52514e", "#d9d8d4"
COL = {"all-Fe": "#2a78d6", "Fe-first, Ru/C downstream": "#eb6834", "all-Ru/C": "#1baf7a",
       "Ru/C-first, Fe downstream": "#eda100"}
ARR = {"FFF": "all-Fe", "FFR": "Fe-first, Ru/C downstream", "FRR": "Fe-first, Ru/C downstream", "RRR": "all-Ru/C",
       "RFF": "Ru/C-first, Fe downstream", "RRF": "Ru/C-first, Fe downstream"}
CAT = ["all-Fe", "Fe-first, Ru/C downstream", "all-Ru/C"]
plt.rcParams.update({"font.size": 9, "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.titlesize": 10, "axes.titleweight": "bold", "text.color": INK})


def rows(name):
    with (HERE / name).open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def costs_panel(ax, arr, econ, title):
    loops = ["KAAP-type 90 bar, -20 C", "conventional 150 bar, -5 C", "conventional 200 bar, -5 C"]
    names = list(COL)
    w = 0.2
    for j, an in enumerate(names):
        vals = []
        for lp in loops:
            c = [float(r["cost"]) for r in arr if r["loop"] == lp and r["economics"] == econ and r["mode"] == "adiabatic"
                 and ARR[r["pattern"]] == an]
            vals.append(min(c))
        x = np.arange(len(loops)) + (j - 1.5) * w
        ax.bar(x, vals, w * 0.92, color=COL[an], label=an, zorder=3)
    ax.set_xticks(range(len(loops)))
    ax.set_xticklabels(["90 bar, -20 °C\n(KAAP-type)", "150 bar, -5 °C", "200 bar, -5 °C"])
    ax.set_ylabel("USD per t NH$_3$")
    lo = min(float(r["cost"]) for r in arr if r["economics"] == econ and r["mode"] == "adiabatic")
    hi = max(float(r["cost"]) for r in arr if r["economics"] == econ and r["mode"] == "adiabatic")
    ax.set_ylim(lo - 0.6, hi + 0.3)
    ax.grid(axis="y", color=GRID, lw=0.6, zorder=0)
    ax.set_title(title, loc="left")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def path_panel(ax, arr):
    econ = "benchmark accounting, r 95.55%"
    sel = [r for r in arr if r["loop"] == "KAAP-type 90 bar, -20 C" and r["economics"] == econ and r["mode"] == "adiabatic"]
    Ts = np.linspace(330, 560, 60)
    yeq = [100 * K.equilibrium_y_nh3(T + 273.15, 90.0, inerts=0.08) for T in Ts]
    ax.plot(yeq, Ts, color=INK2, lw=1.2, ls="--", label="equilibrium (Gillespie-Beattie, fugacity)")
    for pat, an in (("FFF", "all-Fe"), ("FRR", "Fe-first, Ru/C downstream"), ("RRR", "all-Ru/C")):
        r = [x for x in sel if x["pattern"] == pat][0]
        yin = 100 * float(r["y_NH3_in"])
        beds = r["beds_T_in_out_C"].split(";")
        youts = [100 * float(v) for v in r["beds_y_NH3_out"].split(";")]
        y0 = yin
        for b, y1 in zip(beds, youts):
            cat, t = b.split(":")
            t0, t1 = (float(v) for v in t.split("-"))
            if y1 - y0 > 1e-4:
                ax.plot([y0, y1], [t0, t1], color=COL[an], lw=2.4 if cat == "Ru" else 1.6,
                        solid_capstyle="round", zorder=3)
                ax.plot([y1, y1], [t1, t1 - 2], color=COL[an], lw=0.1)
            y0 = y1
        ax.plot([], [], color=COL[an], lw=2, label=f"{an} ({pat}): {float(r['cost']):.2f} USD/t")
    ax.set_xlabel("NH$_3$ mole fraction (%)")
    ax.set_ylabel("Temperature (°C)")
    ax.set_xlim(0, 22)
    ax.set_ylim(340, 545)
    ax.axhline(460, color=COL["all-Ru/C"], lw=0.7, ls=":")
    ax.text(21.5, 463, "Ru/C limit 460 °C", ha="right", fontsize=7, color=INK2)
    ax.axhline(530, color=COL["all-Fe"], lw=0.7, ls=":")
    ax.text(21.5, 533, "fused Fe limit 530 °C", ha="right", fontsize=7, color=INK2)
    ax.legend(fontsize=6.5, frameon=False, loc="lower right")
    ax.set_title("c  KAAP-type loop: optimal adiabatic paths", loc="left")
    ax.grid(color=GRID, lw=0.5)


def cat_index(best):
    return {"FFF": 0, "FFR": 1, "FRR": 1, "RRR": 2}[best]


def map_panel(ax, bpf, P, Ts, r_, title):
    sel = [x for x in bpf if float(x["P_bar"]) == P and float(x["Tsep_C"]) == Ts and abs(float(x["recovery"]) - r_) < 1e-9]
    prices = sorted({float(x["p_Ru"]) for x in sel})
    rates = sorted({float(x["fin_rate"]) for x in sel})
    Z = np.zeros((len(rates), len(prices)))
    G = np.zeros_like(Z)
    for x in sel:
        i, j = rates.index(float(x["fin_rate"])), prices.index(float(x["p_Ru"]))
        Z[i, j] = cat_index(x["best"])
        G[i, j] = float(x["staged_minus_Fe"])
    cmap = ListedColormap([COL[c] for c in CAT])
    ax.pcolormesh(prices, 100 * np.array(rates), Z, cmap=cmap, vmin=-0.5, vmax=2.5, shading="nearest", alpha=0.85)
    cs = ax.contour(prices, 100 * np.array(rates), G, levels=[0.0], colors=INK, linewidths=1.2)
    ax.set_xscale("log")
    ax.plot([53852.5], [0], marker="o", ms=6, mfc="white", mec=INK, clip_on=False, zorder=5)
    ax.plot([53852.5], [12], marker="s", ms=6, mfc="white", mec=INK, clip_on=False, zorder=5)
    ax.set_xlabel("Ru price (USD per kg)")
    ax.set_ylabel("Ru inventory financing (% per year)")
    ax.set_title(title, loc="left")


def pressure_panel(ax, bp):
    sel = [x for x in bp if x["accounting"] == "dcf" and float(x["Tsep_C"]) == -20.0]
    Ps = sorted({float(x["P_bar"]) for x in sel})
    rates = sorted({float(x["fin_rate"]) for x in sel})
    Z = np.zeros((len(rates), len(Ps)))
    G = np.zeros_like(Z)
    for x in sel:
        i, j = rates.index(float(x["fin_rate"])), Ps.index(float(x["P_bar"]))
        Z[i, j] = cat_index(x["best"])
        G[i, j] = float(x["staged_minus_Fe"])
    cmap = ListedColormap([COL[c] for c in CAT])
    ax.pcolormesh(Ps, 100 * np.array(rates), Z, cmap=cmap, vmin=-0.5, vmax=2.5, shading="nearest", alpha=0.85)
    ax.contour(Ps, 100 * np.array(rates), G, levels=[0.0], colors=INK, linewidths=1.2)
    ax.set_xlabel("Loop pressure (bar), separator -20 °C")
    ax.set_ylabel("Ru inventory financing (% per year)")
    ax.set_title("f  Pressure x financing (Ru 53,852.5 USD/kg, r 95.55%)", loc="left")


def main():
    arr = rows("arrangements.csv")
    bpf = rows("boundary_price_financing.csv")
    bp = rows("boundary_pressure.csv")
    fig, axs = plt.subplots(2, 3, figsize=(15, 8.6), constrained_layout=True)
    costs_panel(axs[0, 0], arr, "benchmark accounting, r 95.55%", "a  Benchmark metal accounting, r 95.55%")
    costs_panel(axs[0, 1], arr, "25-y cash flow, financing 12%, r 95.55%", "b  25-y cash flow, Ru financed at 12%")
    axs[0, 0].legend(fontsize=7, frameon=False, loc="upper left")
    path_panel(axs[0, 2], arr)
    map_panel(axs[1, 0], bpf, 90.0, -20.0, 0.9555, "d  KAAP-type 90 bar: optimum, r 95.55%")
    map_panel(axs[1, 1], bpf, 150.0, -5.0, 0.9555, "e  150 bar, -5 °C: optimum, r 95.55%")
    pressure_panel(axs[1, 2], bp)
    handles = [Patch(color=COL[c], label=c) for c in CAT] + [
        plt.Line2D([], [], color=INK, lw=1.2, label="staged Fe->Ru/C = all-Fe"),
        plt.Line2D([], [], marker="o", ls="", mfc="white", mec=INK, label="53,852.5 USD/kg, 0%"),
        plt.Line2D([], [], marker="s", ls="", mfc="white", mec=INK, label="53,852.5 USD/kg, 12%")]
    axs[1, 2].legend(handles=handles, fontsize=7, frameon=True, loc="upper right", framealpha=0.9)
    fig.suptitle("Staged Fe / Ru/C ammonia converter with measured rate laws (Dyson-Simon fused Fe; Rossetti 2006 Ru/C, "
                 "8 wt% Ru, 490 kg m$^{-3}$); 1,000 t/d, 8% inerts, adiabatic beds", fontsize=10, color=INK)
    fig.savefig(HERE / "staged_converter.png", dpi=160)
    print("wrote staged_converter.png")


if __name__ == "__main__":
    main()
