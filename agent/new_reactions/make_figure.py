"""Summary figure of the AI-run pipeline on the two new reactions (results/fig_new_reactions.{svg,pdf,png}).
Row 1 PDH, row 2 CO2 methanation: (a, d) reference plant cost split; (b, e) lab productivity vs plant cost of every
usable literature record; (c, f) cost change at the reference plant for a catalyst improvement vs a feed-price change.
House style: figures/composite/style.py (Page)."""
import copy
import csv
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "figures" / "composite"))
from style import DARK_B, DARK_G, FE, GRID, INK, MID, OTHER, RED, RU, Page, boxed, fmt_minus  # noqa: E402

import analyze as an  # noqa: E402
import plant_models as pm  # noqa: E402

LABEL = {"feed": "Propane", "h2_credit": "H$_2$ credit", "light_ends_credit": "Fuel credit", "energy": "Energy",
         "capital": "Capital + O&M", "catalyst": "Catalyst", "regeneration": "Regeneration",
         "hydrogen": "H$_2$", "co2": "CO$_2$", "power": "Power"}
COL = {"feed": RU, "hydrogen": RU, "co2": FE, "energy": FE, "power": FE, "capital": OTHER, "catalyst": RED,
       "regeneration": DARK_G, "h2_credit": GRID, "light_ends_credit": GRID}


def family(rxn, cat):
    c = cat.replace(" ", "")
    if rxn == "pdh":
        for k in ("Pt", "Ga", "Fe", "Co", "Zn"):
            if k in c:
                return k
        return "other"
    for k in ("Ru", "Co", "Ni"):
        if k in c:
            return k
    return "other"


FAM_COL = {"Pt": RU, "Ga": FE, "Fe": DARK_G, "Co": DARK_B, "Zn": MID, "Ni": FE, "Ru": RU, "other": OTHER}


def bar_split(ax, parts, total, title_unit):
    pos = {k: v for k, v in parts.items() if v > 0}
    neg = {k: v for k, v in parts.items() if v < 0}
    left = 0
    for k, v in sorted(pos.items(), key=lambda t: -t[1]):
        ax.barh(0, v, left=left, color=COL.get(k, OTHER), edgecolor="white", lw=0.4, height=0.55)
        if v / total > 0.15:
            ax.text(left + v / 2, 0, "%s\n%.0f" % (LABEL[k], v), ha="center", va="center", fontsize=5.6, color="white")
        left += v
    nl = 0
    for k, v in neg.items():
        ax.barh(-0.62, v, left=nl, color="#BFBFBF", edgecolor="white", lw=0.4, height=0.35)
        nl += v
    small = [k for k, v in pos.items() if v / total <= 0.15]
    ax.text(left, 0.40, ", ".join("%s %.1f" % (LABEL[k], pos[k]) for k in sorted(small, key=lambda k: -pos[k])),
            ha="right", va="bottom", fontsize=5.4, color=INK)
    if neg:
        ax.text(6, -0.62, "credits %.0f (H$_2$, fuel)" % -sum(neg.values()), ha="left", va="center", fontsize=5.4)
    ax.axvline(total, color=INK, lw=0.7, ls=(0, (2, 1.5)))
    ax.text(total, -0.98, "net %.0f %s" % (total, title_unit), ha="right", va="center", fontsize=5.8)
    ax.set_ylim(-1.15, 0.85)
    ax.set_yticks([])
    boxed(ax)


def scatter(ax, rxn, rows, c_ref, xlabel, ylim):
    for fam in sorted({family(rxn, r["catalyst"]) for r in rows}):
        sub = [r for r in rows if family(rxn, r["catalyst"]) == fam]
        ax.scatter([r["r_kg_kg_h"] for r in sub], [r["cost"] for r in sub], s=7, color=FAM_COL[fam],
                   edgecolor="white", lw=0.25, label=fam, zorder=3)
    ax.axhline(c_ref, color=INK, lw=0.7, ls=(0, (2, 1.5)))
    ax.set_xscale("log")
    ax.set_ylim(*ylim)
    ax.set_xlabel(xlabel)
    ax.legend(fontsize=5.4, loc="upper right", handletextpad=0.1, borderaxespad=0.2, ncol=2, columnspacing=0.6)
    boxed(ax)


def deltas(rxn):
    ref = pm.reference_record(rxn)
    c0 = an.cost(rxn, ref)
    out = []
    if rxn == "pdh":
        out.append(("+1 pt selectivity", an.cost(rxn, dict(ref, S=ref["S"] + 0.01)) - c0, RED))
        out.append(("activity x2", an.cost(rxn, dict(ref, r=ref["r"] * 2)) - c0, RED))
        out.append(("cycle x10", an.cost(rxn, dict(ref, t_cycle_h=ref["t_cycle_h"] * 10)) - c0, RED))
        base = copy.deepcopy(pm.PARAMS)
        pm.PARAMS["pdh"]["prices"]["propane_usd_t"] -= 10
        out.append(("propane -10 USD/t", an.cost(rxn, ref) - c0, RU))
        pm.PARAMS.clear(); pm.PARAMS.update(base); pm.init_reference()
    else:
        rows = an.load(rxn)
        for r in rows:
            r["rec"]["xeq_lab"] = pm.lab_xeq(rxn, r["rec"])
        best = min(an.cost(rxn, r["rec"]) for r in rows)
        out.append(("best literature catalyst", best - c0, RED))
        out.append(("activity x2", an.cost(rxn, dict(ref, r=ref["r"] * 2)) - c0, RED))
        base = copy.deepcopy(pm.PARAMS)
        pm.PARAMS["ch4"]["prices"]["h2_usd_kg"] -= 0.25
        out.append(("H$_2$ -0.25 USD/kg", an.cost(rxn, ref) - c0, RU))
        pm.PARAMS.clear(); pm.PARAMS.update(base); pm.init_reference()
    return out


def bars(ax, items, unit):
    y = np.arange(len(items))[::-1]
    for yi, (lab, v, col) in zip(y, items):
        ax.barh(yi, v, color=col, height=0.55)
        ax.text(v - 0.6 if v < 0 else v + 0.6, yi, fmt_minus("%.1f" % v), va="center",
                ha="right" if v < 0 else "left", fontsize=5.8)
    ax.set_yticks(y)
    ax.set_yticklabels([i[0] for i in items], fontsize=6)
    ax.axvline(0, color=INK, lw=0.6)
    lo = min(v for _, v, _ in items)
    ax.set_xlim(lo * 1.45, max(0, max(v for _, v, _ in items)) + abs(lo) * 0.15)
    ax.set_xlabel(unit)
    boxed(ax)


def main():
    pg = Page(183.0, 118.0)
    rows_y = {"pdh": 67.0, "ch4": 9.0}
    for rxn, unit, xl, ylim in (("pdh", "USD t$^{-1}$ C$_3$H$_6$", "Lab productivity (kg C$_3$H$_6$ kg$^{-1}$ h$^{-1}$)", (780, 1600)),
                                ("ch4", "USD t$^{-1}$ CH$_4$", "Lab productivity (kg CH$_4$ kg$^{-1}$ h$^{-1}$)", (1900, 2450))):
        y0 = rows_y[rxn]
        s = json.loads((HERE / "results" / f"{rxn}_summary.json").read_text(encoding="utf-8"))
        rows = list(csv.DictReader(open(HERE / "results" / f"{rxn}_costs.csv", encoding="utf-8")))
        for r in rows:
            r["r_kg_kg_h"], r["cost"] = float(r["r_kg_kg_h"]), float(r["cost"])
        a = pg.ax(10, y0, 50, 30)
        bar_split(a, s["reference"]["parts"], s["reference"]["cost"], unit.split()[0] + " t$^{-1}$")
        a.set_xlabel(unit)
        b = pg.ax(72, y0, 48, 34)
        scatter(b, rxn, rows, s["reference"]["cost"], xl, ylim)
        b.set_ylabel("Plant cost (%s)" % unit)
        c = pg.ax(150, y0 + 2, 30, 32)
        bars(c, deltas(rxn), "Cost change (%s)" % unit)
        letters = "abc" if rxn == "pdh" else "def"
        for ch, x in zip(letters, (2, 61, 121)):
            pg.letter(ch, x, y0 + 39)
        pg.title("Propane dehydrogenation (reference: Pt–Sn/Al$_2$O$_3$, Oleflex-type)" if rxn == "pdh"
                 else "CO$_2$ methanation (reference: Ni/Al$_2$O$_3$)", 2, y0 + 46)
    pg.save(str(HERE / "results"), "fig_new_reactions")


if __name__ == "__main__":
    main()
