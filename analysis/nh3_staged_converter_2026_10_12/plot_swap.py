"""Figure: NH3-FINAL-1.1 cost against loop pressure with descriptor and measured Fe/Ru kinetics.
    python plot_swap.py -> kinetics_swap.png"""
import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

HERE = Path(__file__).resolve().parent
INK, INK2, GRID = "#0b0b0b", "#52514e", "#d9d8d4"
FE, RU, RUC = "#2a78d6", "#eb6834", "#1baf7a"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.titlesize": 10, "axes.titleweight": "bold", "text.color": INK})


def series(rows, states, sizing, scale, key):
    sel = [r for r in rows if r["states"] == states and r["sizing"] == sizing and r["scale"] == scale and r.get(key)]
    P = np.array([float(r["P_bar"]) for r in sel])
    v = np.array([float(r[key]) for r in sel])
    o = np.argsort(P)
    return P[o], v[o]


def main():
    with (HERE / "kinetics_swap_pressure_profiles.csv").open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    summ = json.loads((HERE / "kinetics_swap.json").read_text(encoding="utf-8"))
    fig, axs = plt.subplots(1, 2, figsize=(12.5, 4.8), constrained_layout=True, sharey=True)
    for ax, states, title in ((axs[0], "frozen", "a  NH3-FINAL-1.1 process states (model equilibrium)"),
                              (axs[1], "GB", "b  Process states at the Gillespie-Beattie equilibrium")):
        if states == "frozen":
            for key, col, lab in (("Fe", FE, "Fe, descriptor (frozen)"), ("Ru_benchmark", RU, "Ru benchmark, descriptor (frozen)")):
                P, v = series(rows, "frozen", "descriptor", "F_CAL", key)
                ax.plot(P, v, color=col, lw=1.2, ls="--", label=lab)
        for key, col, lab in (("Fe", FE, "Fe, Dyson-Simon"), ("Ru_benchmark", RU, "Ru benchmark, Rossetti Ru/C / u"),
                              ("Ru_C_supported_r9555", RUC, "Ru/C 8 wt%, r 95.55%")):
            P, v = series(rows, states, "plug", "source", key)
            ax.plot(P, v, color=col, lw=2.0, label=lab + " (measured, plug flow)")
            i = int(np.argmin(v))
            ax.plot(P[i], v[i], marker="o", ms=6, mfc="white", mec=col, mew=1.6, zorder=5)
            dy = 8 if key == "Fe" else -13
            ax.annotate(f"{P[i]:.0f} bar", (P[i], v[i]), xytext=(0, dy), textcoords="offset points", ha="center",
                        fontsize=7.5, color=INK2)
        ax.set_xscale("log")
        ax.set_xlim(40, 1000)
        ax.set_xticks([50, 100, 200, 500, 1000])
        ax.set_xticklabels(["50", "100", "200", "500", "1000"])
        ax.minorticks_off()
        ax.set_ylim(9, 40)
        ax.set_xlabel("Loop pressure (bar), best T and separator at each pressure")
        ax.grid(color=GRID, lw=0.5)
        ax.set_title(title, loc="left")
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        ax.axvspan(50, 100, color=RUC, alpha=0.08, lw=0)
        ax.text(70, 39, "Ru/C data\n50-100 bar", ha="center", va="top", fontsize=7, color=INK2)
    axs[0].set_ylabel("USD per t NH$_3$ (benchmark metal accounting)")
    axs[0].legend(fontsize=7, frameon=False, loc="upper right")
    v = [x for x in summ["variants"] if x["sizing"] == "plug" and x["scale"] == "source" and x["states"] == "frozen"][0]
    fig.suptitle(f"Kinetics swap in NH3-FINAL-1.1: Ru parity multiple {v['Ru_activity_multiple_for_parity']:.1f}x "
                 f"(descriptor 201.2x); 14,136 frozen states, plug-flow sizing, source-calibrated rates", fontsize=10)
    fig.savefig(HERE / "kinetics_swap.png", dpi=160)
    print("wrote kinetics_swap.png")


if __name__ == "__main__":
    main()
