"""NH3-FINAL-1.2 plant benchmark: per-item error table, and Fe-vs-Ru robustness to the benchmark errors.

    NH3_MODEL is forced to 1.2.  python run_error_table.py      (about 7.5 min, one process)

Part 1  error_table.csv (64 rows) and error_summary.csv (per table, per quantity group) from the registered 1.2
        re-score analysis/validation_nh3_plant_2026_10_13/nh3_1_2/results_metrics.csv. Nothing is re-judged; the
        pass/fail column is copied from that file.
Part 2  Each failing quantity group is mapped to the model component that controls it. That component is perturbed by
        the observed benchmark error (median = "typical", maximum = "max"; both directions), both catalysts are
        re-optimised over the perturbed NH3-FINAL-1.2 process-state library, and the Fe-Ru gap is recomputed for the
        canonical descriptor-kinetics gate (Fe, Ru, Os) and the measured-kinetics comparison (Dyson-Simon Fe vs
        Rossetti Ru/C: benchmark formulation, supported Ru/C at 0 and 12 %/y). All 2^5 sign corners x {Fe-only, all-catalyst
        catalyst amount} are also run at each magnitude (joint perturbation). -> perturbation_results.csv,
        perturbation_summary.json.

The frozen harness (provenance/nh3_final_1_2/source_harness/harness_core.py) and the measured-kinetics code
(analysis/nh3_staged_converter_2026_10_12/kinetics_swap.py) are imported unchanged. Perturbations are applied to an
in-memory subclass instance (separator vapour, approach to equilibrium) or to its cost arrays (compression, catalyst
amount, bed temperature). The canonical anchors are asserted on the unperturbed path before anything is perturbed.
"""
from __future__ import annotations

import csv
import itertools
import json
import math
import os
import statistics
import sys
import time
from pathlib import Path

os.environ["NH3_MODEL"] = "1.2"

import numpy as np  # noqa: E402

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
BENCH = REPO / "analysis" / "validation_nh3_plant_2026_10_13"
sys.path.insert(0, str(REPO / "analysis" / "nh3_staged_converter_2026_10_12"))
import kinetics_swap as S  # noqa: E402

hc, NM = S.hc, S.NM
assert NM.VERSION == "1.2"

ANCHOR_FE, ANCHOR_RU = 11.515784, 16.632749          # canonical NH3-FINAL-1.2 gate (results.json, 6 d.p.)
MEASURED = dict(Fe=14.925644, Ru_bench=33.07, Ru_bench_100_200=38.26, RuC_0=-3.46, RuC_12=1.452025)

# --------------------------------------------------------------------------------------------------------------------
# Part 1: error table
# --------------------------------------------------------------------------------------------------------------------

PLANT = {
    "TOP140": "Topsoe 140 bar loop (Dybkjaer 1995)", "TOP220": "Topsoe 220 bar loop (Dybkjaer 1995)",
    "UHDE188": "Krupp-Uhde 188 bar loop (Appl 2011)", "S250": "Topsoe S-250 137 bar (Liu 2013)",
    "UHDE160": "Uhde 160 bar (Liu 2013)", "PFI266": "PFI 266 bar (Orphanides 2006)",
    "KELLOGG150": "Kellogg 150 bar (Hooper 1991)", "BRAUN150": "Braun 150 bar (Liu 2013)",
    "LIU_KELLOGG": "Kellogg 140 bar (Liu 2013 Table 9.2)", "LIU_TOPSOE": "Topsoe 260 bar (Liu 2013 Table 9.2)",
    "LIU_AMV": "ICI AMV 100 bar (Liu 2013 Table 9.2)", "LIU_SMALL": "small/medium 314 bar (Liu 2013 Table 9.2)",
    "CASALE250": "Casale 250 bar converter (US patent)", "LIU93_151": "1000 t/d 151 bar loop (Liu 2013 Table 9.3)",
    "UHDE2000": "Uhde 2000 t/d 195 bar (Lippmann & Frisse 2004)", "LIU919A": "S-200 126 bar circulator (Liu 2013 Table 9.19A)",
    "LIU919A_FWD": "S-200 126 bar converter, forward (Liu 9.19A)", "LIU919B_FWD": "S-200 134 bar converter, forward (Liu 9.19B)",
    "LIU919A_INV": "S-200 126 bar converter, inverse (Liu 9.19A)", "LIU919B_INV": "S-200 134 bar converter, inverse (Liu 9.19B)",
    "TOP220_MINVOL/TOP140_MINVOL": "Topsoe 220/140 bar minimum-volume ratio",
    "TOP140_DESIGN": "cost-optimal all-Fe converter at Topsoe 140 bar loop",
    "TOP220_DESIGN": "cost-optimal all-Fe converter at Topsoe 220 bar loop",
    "UHDE188_DESIGN": "cost-optimal all-Fe converter at Krupp-Uhde 188 bar loop",
    "KAAP_DESIGN": "cost-optimal KAAP layout, 89 bar", "OPT_FE": "model Fe optimum vs industrial Fe windows",
    "STAGED_ALL": "staged Fe/Ru converter optima", "STAGED_90BAR": "staged 90 bar KAAP-type loop",
    "STAGED_PRESSURE": "staged optima across pressure", "OPT_RUC_0PCT": "supported Ru/C optimum, 0 %/y",
    "OPT_RUC_12PCT": "supported Ru/C vs Fe, 12 %/y", "ULLMANN_T5": "BASF NH3 saturation table (Ullmann Table 5)",
}

# physical quantity groups (label, unit of the deviation, perturbed component or None)
GROUPS = [
    ("converter inlet NH3", ["A01", "A04", "A07", "A14", "A16"], "SEP"),
    ("separator vapour NH3", ["V01"], "SEP"),
    ("outlet / net NH3, loop states", ["A02", "A05", "A08", "A11", "A12", "A13", "A15", "A17", "A18", "A20", "A22",
                                       "A24", "A26"], "APP"),
    ("outlet NH3, converter forward runs", ["B03", "B07"], None),
    ("outlet NH3, cost-optimal converter designs", ["B10", "B13", "B16", "B20"], "APP"),
    ("outlet NH3, Fe optimum", ["C06"], None),
    ("converter flow and feed/make-up", ["A03", "A06", "A09", "A10"], None),
    ("space velocity", ["A19", "A21", "A23", "A25", "A27", "C07"], None),
    ("compressor power", ["E01", "E02", "E03"], "COMP"),
    ("bed volume, plant conditions", ["A28", "B04", "B08", "B09"], "KIN"),
    ("bed volume, cost-optimal designs and Fe optimum", ["B12", "B15", "B18", "C05"], "KIN"),
    ("bed outlet temperature, forward runs", ["B01", "B02", "B05", "B06"], "TBED"),
    ("bed-1 inlet temperature, cost-optimal designs", ["B11", "B14", "B17"], "TBED"),
    ("Fe optimum loop pressure", ["C01", "C02"], None),
    ("Fe optimum temperature", ["C03"], None),
    ("Fe optimum separator temperature", ["C04"], None),
    ("Fe/Ru choice and staging", ["B19", "C08", "C09", "C10", "C11", "C12"], None),
]
GROUP_OF = {m: g for g, ids, _ in GROUPS for m in ids}
COMPONENT_OF_GROUP = {g: c for g, _, c in GROUPS}


def rows(p):
    return list(csv.DictReader(Path(p).open(encoding="utf-8")))


def fnum(x):
    return float(x) if x not in ("", None) else None


def deviation(m, model_str, windows):
    """Signed deviation of the model from the industrial value. Point values: (model - ref) / ref; bands and windows:
    0 inside, otherwise against the nearest edge (also against the midpoint). Temperatures (unit C): model - ref in C.
    V01 (model / table ratio): ratio - 1. Logical and threshold rules: no numeric deviation."""
    kind = m["rule"].split(":")[0]
    out = dict(reference="", dev_basis="", signed_dev=None, dev_unit="", abs_dev=None, dev_vs_mid=None, log_ratio=None)
    if kind in ("equals", "below", "above"):
        out.update(reference=m["rule"], dev_basis="logical / threshold rule (no numeric deviation)", dev_unit="n/a")
        return out
    model = float(model_str)
    temp = m["unit"] == "C"
    if m["metric_id"] == "V01":
        lo = hi = None
        ref, basis = 1.0, "model/table ratio - 1 (separator vapour vs BASF table)"
    elif m["industrial_value"]:
        lo = hi = None
        ref, basis = float(m["industrial_value"]), "point value"
    else:
        if kind == "window":
            w = windows[m["rule"].split(":")[1]]
            lo, hi = w
        else:
            lo, hi = float(m["industrial_low"]), float(m["industrial_high"])
        if lo <= model <= hi:
            ref, basis = None, f"inside published range {lo:g}-{hi:g}"
        else:
            ref = lo if model < lo else hi
            basis = f"nearest edge of published range {lo:g}-{hi:g}"
    if temp:
        d = 0.0 if ref is None else model - ref
        out.update(signed_dev=d, dev_unit="C", abs_dev=abs(d))
        if lo is not None:
            out["dev_vs_mid"] = model - 0.5 * (lo + hi)
    else:
        d = 0.0 if ref is None else 100.0 * (model / ref - 1.0)
        out.update(signed_dev=d, dev_unit="%", abs_dev=abs(d), log_ratio=0.0 if ref is None else math.log(model / ref))
        if lo is not None:
            out["dev_vs_mid"] = 100.0 * (model / (0.5 * (lo + hi)) - 1.0)
    out.update(reference="" if ref is None else f"{ref:g}", dev_basis=basis)
    return out


def build_error_table():
    res = {r["metric_id"]: r for r in rows(BENCH / "nh3_1_2" / "results_metrics.csv")}
    met = rows(BENCH / "benchmark_metrics.csv")
    win = {}
    for w in rows(BENCH / "industrial_windows.csv"):
        win[w["window_id"]] = (float(w["window_low"]), float(w["window_high"]))
    table = []
    for m in met:
        r = res[m["metric_id"]]
        d = deviation(m, r["model"], win)
        ind = m["industrial_value"] or (f"{m['industrial_low']}-{m['industrial_high']}" if m["industrial_low"] else "")
        if m["rule"].startswith("window:"):
            ind = "{:g}-{:g} ({})".format(*win[m["rule"].split(":")[1]], m["rule"].split(":")[1])
        elif not ind:
            ind = m["rule"]
        table.append(dict(
            metric_id=m["metric_id"], table=m["table"], case_id=m["case_id"], plant_case=PLANT[m["case_id"]],
            quantity=m["quantity"], quantity_group=GROUP_OF[m["metric_id"]], model=r["model"], industrial=ind,
            unit=m["unit"], reference_used=d["reference"], deviation_basis=d["dev_basis"],
            signed_deviation=_r(d["signed_dev"]), deviation_unit=d["dev_unit"], abs_deviation=_r(d["abs_dev"]),
            signed_deviation_vs_range_midpoint=_r(d["dev_vs_mid"]), log_model_over_ref=_r(d["log_ratio"], 4),
            tolerance_rule=m["rule"], registered_deviation_text=r["deviation"], pass_=r["pass_"]))
    assert len(table) == 64 and sum(t["pass_"] == "pass" for t in table) == 32
    return table


def _r(x, nd=2):
    return "" if x is None else round(float(x), nd)


def _stats(sub):
    num = [t for t in sub if t["abs_deviation"] != ""]
    out = dict(n=len(sub), n_pass=sum(t["pass_"] == "pass" for t in sub), n_logical=len(sub) - len(num))
    for unit in ("%", "C"):
        u = [t for t in num if t["deviation_unit"] == unit]
        key = "pct" if unit == "%" else "C"
        if not u:
            out.update({f"n_{key}": 0, f"typical_abs_dev_{key}": "", f"max_abs_dev_{key}": "", f"max_id_{key}": "",
                        f"median_signed_dev_{key}": ""})
            continue
        a = [float(t["abs_deviation"]) for t in u]
        s = [float(t["signed_deviation"]) for t in u]
        i = int(np.argmax(a))
        out.update({f"n_{key}": len(u), f"typical_abs_dev_{key}": round(statistics.median(a), 1),
                    f"max_abs_dev_{key}": round(a[i], 1), f"max_id_{key}": u[i]["metric_id"],
                    f"median_signed_dev_{key}": round(statistics.median(s), 1)})
    sg = [float(t["signed_deviation"]) for t in num if float(t["signed_deviation"]) != 0.0]
    nu, no = sum(x < 0 for x in sg), sum(x > 0 for x in sg)
    out["n_under"], out["n_over"], out["n_inside_range"] = nu, no, len(num) - nu - no
    out["sign"] = ("" if not num else "none (all inside)" if not sg else "under-prediction" if no == 0 else
                   "over-prediction" if nu == 0 else "mixed")
    out["failing_ids"] = " ".join(t["metric_id"] for t in sub if t["pass_"] != "pass")
    return out


def build_summary(table):
    out = []
    for tb in ("A", "E", "B", "C", "V"):
        sub = [t for t in table if t["table"] == tb]
        out.append(dict(level="table", group=tb, component="", **_stats(sub)))
    for g, ids, comp in GROUPS:
        sub = [t for t in table if t["metric_id"] in ids]
        out.append(dict(level="quantity group", group=g, component=comp or "", **_stats(sub)))
    out.append(dict(level="all", group="all 64", component="", **_stats(table)))
    return out


def write_csv(path, recs):
    with Path(path).open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(recs[0]))
        w.writeheader()
        w.writerows(recs)


# --------------------------------------------------------------------------------------------------------------------
# Part 2: perturbation of the controlling components
# --------------------------------------------------------------------------------------------------------------------

COMPONENTS = {
    "SEP": ("separator vapour NH3, y_sep = p_sat(T_sep)/P (VLE)", ["A01", "A04", "A07", "A14", "A16", "V01"]),
    "APP": ("per-pass conversion, approach to equilibrium 0.8", ["A02", "A05", "A08", "A11", "A12", "A13", "A15", "A17",
                                                                "A18", "A20", "A22", "A24", "A26", "B10", "B13", "B16",
                                                                "B20"]),
    "COMP": ("compression power (fresh + recycle; compressor capex follows), i.e. eta_eff = 0.75/k",
             ["E01", "E02", "E03"]),
    "KIN": ("catalyst amount per state (rate multiplier / bed sizing)", ["A28", "B04", "B08", "B09", "B12", "B15", "B18",
                                                                        "C05"]),
    "TBED": ("effective bed temperature of the rate (isothermal bed at T + dT; loop state unchanged)",
             ["B01", "B02", "B05", "B06", "B11", "B14", "B17"]),
}


def magnitudes(table):
    """Typical (median) and maximum observed error of each component's metrics: factor exp(|ln(model/ref)|) for
    multiplicative components, |dT| in C for TBED."""
    by = {t["metric_id"]: t for t in table}
    out = {}
    for c, (_, ids) in COMPONENTS.items():
        if c == "TBED":
            a = [float(by[i]["abs_deviation"]) for i in ids]
        else:
            a = [abs(float(by[i]["log_model_over_ref"])) for i in ids]
        i = int(np.argmax(a))
        typ, mx = statistics.median(a), a[i]
        if c == "TBED":
            out[c] = dict(typical=typ, max=mx, max_id=ids[i], unit="C")
        else:
            out[c] = dict(typical=math.exp(typ), max=math.exp(mx), max_id=ids[i], unit="factor",
                          typical_abs_dev_pct=statistics.median(abs(float(by[j]["signed_deviation"])) for j in ids),
                          max_abs_dev_pct=abs(float(by[ids[i]]["signed_deviation"])))
    # KIN also at the largest error of the plant-condition sizing rows alone (measured beds, not cost-optimal designs)
    ids = ["A28", "B04", "B08", "B09"]
    a = [abs(float(by[i]["log_model_over_ref"])) for i in ids]
    out["KIN"]["max_plant_sizing"] = math.exp(max(a))
    out["KIN"]["max_plant_sizing_id"] = ids[int(np.argmax(a))]
    return out


class PerturbedHarness(hc.NH3Harness):
    """The frozen 1.2 harness with the separator vapour multiplied by `sep`, the approach to equilibrium set to
    `approach` and compression power multiplied by `comp` (through the compressor efficiency); defaults = canonical."""

    def __init__(self, cfg, root, sep=1.0, approach=None, comp=1.0):
        self._sep, self._approach, self._comp = float(sep), approach, float(comp)
        super().__init__(cfg, root)

    def _init_controls(self):
        super()._init_controls()
        if self._approach is not None:
            self.APPROACH_EQ = float(self._approach)
        if self._comp != 1.0:
            self.COMPRESSOR_ETA = self.COMPRESSOR_ETA / self._comp

    def psat_nh3_bar(self, T_C):
        return super().psat_nh3_bar(T_C) * self._sep


class Library:
    """One process-state library (sep, approach) with cached kinetics; compression is a cost-term rescaling."""

    def __init__(self, sep=1.0, approach=None):
        self.h = PerturbedHarness(S.CFG, S.ROOT, sep=sep, approach=approach)
        h = self.h
        self.base_fresh, self.base_rec = h.state_fresh.copy(), h.state_reccomp.copy()
        self.refrig = h.state_refrig.copy()
        self.st = S.state_arrays(h)
        self._lt, self._am, self._pc = {}, {}, {}

    def process_cost(self, k):
        if k not in self._pc:
            h = self.h
            if k == 1.0:
                self._pc[k] = h.state_process_cost.copy()
            else:
                f, r = self.base_fresh * k, self.base_rec * k
                capex = np.array([h.compressor_capex_USD_t(a) + h.compressor_capex_USD_t(b) for a, b in zip(f, r)])
                self._pc[k] = f + r + self.refrig + capex
        return self._pc[k]

    def logtof(self, metal, dT):
        key = (metal, dT)
        if key not in self._lt:
            h = self.h
            if dT == 0.0:
                self._lt[key] = h.frozen_state_logtof(hc.EN0_CANON[metal])
            else:                          # same descriptor interpolation, each state's gas at T + dT
                conds = [h.ctx.condition(s["T_C"] + 273.15 + dT, s["condition"].pN2 / _phi(h, s, 0),
                                         s["condition"].pH2 / _phi(h, s, 1), s["condition"].pNH3 / _phi(h, s, 2))
                         for s in h.process_states]
                self._lt[key] = _interp_logtof(h, conds, hc.EN0_CANON[metal])
        return self._lt[key]

    def amounts(self, dT):
        if dT not in self._am:
            st = dict(self.st)
            st["T"] = self.st["T"] + dT
            self._am[dT] = (S.amount(st, S.rate_fe_m3, self.h, "plug"), S.amount(st, S.rate_ru_kgRu, self.h, "plug"))
        return self._am[dT]


def _phi(h, s, j):
    """Newton-Cooper coefficient used in the state's microkinetic condition (to recover the partial pressures)."""
    return hc.newton_cooper_phi(s["T_C"] + 273.15, s["P_bar"])[j] if h.FUGACITY_IN_MKM else 1.0


def _interp_logtof(h, conds, EN):
    x = min(max(float(EN), float(h.EGRID[0])), float(h.EGRID[-1]))
    pos = (x - float(h.EGRID[0])) / float(h.EGRID[1] - h.EGRID[0])
    j = int(math.floor(pos))
    e0, e1, f = float(h.EGRID[j]), float(h.EGRID[j + 1]), pos - j
    return np.array([c.logtof(e0) * (1.0 - f) + c.logtof(e1) * f for c in conds])


def _opt(h, total, V, mask=None):
    t = np.where(np.isfinite(V) & (V <= h.V_CAP), total, np.inf)
    if mask is not None:
        t = np.where(mask, t, np.inf)
    i = int(np.argmin(t))
    if not np.isfinite(t[i]):
        return None
    return dict(cost=float(t[i]), T_C=float(h.state_T[i]), P_bar=float(h.state_P[i]), Tsep_C=float(h.state_Tsep[i]),
                V_m3=float(V[i]))


def evaluate(lib, comp=1.0, kin=("Fe", 1.0), dT=0.0):
    """Fe and Ru optima of the six comparisons on library lib. kin = (which, f): catalyst amount x f for Fe only
    ('Fe') or for every catalyst ('all'), i.e. the rate divided by f."""
    h = lib.h
    pc_saved = h.state_process_cost
    h.state_process_cost = lib.process_cost(comp)
    try:
        which, f = kin
        fFe, fRu = f, (f if which == "all" else 1.0)
        out = {}
        # (a) descriptor kinetics, canonical gate (alpha divides the active mass)
        d = {}
        for m, fm in (("Fe", fFe), ("Ru", fRu), ("Os", fRu)):
            tot, V, _, _ = h.cost_arrays(m, lib.logtof(m, dT), alpha=1.0 / fm)
            d[m] = _opt(h, tot, V)
        out["descriptor Ru - Fe"] = (d["Fe"], d["Ru"])
        out["descriptor Os - Fe"] = (d["Fe"], d["Os"])
        # (b) measured kinetics (kinetics_swap.evaluate, plug flow, source rates), re-implemented on the cost arrays
        fe_V, ru_M = lib.amounts(dT)
        fe_V, ru_M = fe_V * fFe, ru_M * fRu
        fe_tot = S.costs(h, fe_V, fe_V * h.ACTIVE_FRACTION * h.BED_DENSITY, hc.PRICE["Fe"], S.multiplier("benchmark", 0.0, 0.0))[0]
        fe = _opt(h, fe_tot, fe_V)
        V_b = ru_M * S.U / (h.ACTIVE_FRACTION * h.BED_DENSITY)
        rb = S.costs(h, V_b, ru_M * S.U, S.P_RU, 1.0)[0]
        out["measured benchmark Ru - Fe (unconstrained)"] = (fe, _opt(h, rb, V_b))
        out["measured benchmark Ru - Fe (Ru 100-200 bar)"] = (fe, _opt(h, rb, V_b, (h.state_P >= 100.0) & (h.state_P <= 200.0)))
        V_s = ru_M / (S.W * S.RHO)
        for i, lab in ((0.0, "0"), (0.12, "12")):
            fe_i = S.costs(h, fe_V, fe_V * h.ACTIVE_FRACTION * h.BED_DENSITY, hc.PRICE["Fe"], S.multiplier("cashflow", 0.0, i))[0]
            ru_i = S.costs(h, V_s, ru_M, S.P_RU, S.multiplier("cashflow", 0.9555, i))[0]
            out[f"measured supported Ru/C - Fe ({lab} %/y)"] = (_opt(h, fe_i, fe_V), _opt(h, ru_i, V_s))
        return out
    finally:
        h.state_process_cost = pc_saved


COMPARISONS = ["descriptor Ru - Fe", "descriptor Os - Fe", "measured benchmark Ru - Fe (unconstrained)",
               "measured benchmark Ru - Fe (Ru 100-200 bar)", "measured supported Ru/C - Fe (0 %/y)",
               "measured supported Ru/C - Fe (12 %/y)"]


def gap(pair):
    """Ru - Fe at the two optima; +inf if only Ru has no feasible state, -inf if only Fe, nan if neither."""
    fe, ru = pair
    if fe is None and ru is None:
        return math.nan
    if fe is None:
        return -math.inf               # Fe infeasible everywhere: Ru wins
    if ru is None:
        return math.inf
    return ru["cost"] - fe["cost"]


def scenario_params(M, which_mag, signs, kin_mode):
    """signs: dict component -> +1/-1/0; kin_mode 'Fe' or 'all'. Returns (sep, approach, comp, kin, dT)."""
    a0 = 0.8
    sep, approach, comp, kinf, dT = 1.0, None, 1.0, 1.0, 0.0
    v = {c: M[c].get(which_mag) for c in M}
    if signs.get("SEP"):
        sep = v["SEP"] if signs["SEP"] > 0 else 1.0 / v["SEP"]                 # + raises separator vapour (to plants)
    if signs.get("APP"):
        approach = a0 / v["APP"] if signs["APP"] > 0 else min(a0 * v["APP"], 0.99)   # + lowers per-pass conversion
    if signs.get("COMP"):
        comp = v["COMP"] if signs["COMP"] > 0 else 1.0 / v["COMP"]             # + raises compression power (to plants)
    if signs.get("KIN"):
        kinf = v["KIN"] if signs["KIN"] > 0 else 1.0 / v["KIN"]                # + larger catalyst amount (slower rate)
    if signs.get("TBED"):
        dT = v["TBED"] if signs["TBED"] > 0 else -v["TBED"]
    return sep, approach, comp, (kin_mode, kinf), dT


def main():
    t0 = time.time()
    # ---- Part 1
    table = build_error_table()
    write_csv(HERE / "error_table.csv", table)
    summ = build_summary(table)
    write_csv(HERE / "error_summary.csv", summ)
    M = magnitudes(table)
    print("magnitudes:", json.dumps(M, indent=1), flush=True)

    # ---- anchors on the unperturbed path
    base = Library()
    h = base.h
    assert h.NSTATE == 14510
    r0 = evaluate(base)
    fe, ru = r0["descriptor Ru - Fe"]
    assert abs(fe["cost"] - ANCHOR_FE) < 5e-7 and abs(ru["cost"] - ANCHOR_RU) < 5e-7, (fe, ru)
    A = NM.anchors()
    assert abs(fe["cost"] - A["Fe"]) < 1e-9 and abs(ru["cost"] - A["Ru"]) < 1e-9
    assert (fe["T_C"], fe["P_bar"], fe["Tsep_C"]) == (425.0, 105.0, 30.0) and (ru["T_C"], ru["P_bar"], ru["Tsep_C"]) == (450.0, 220.0, 30.0)
    # measured kinetics: this code path against kinetics_swap.evaluate itself
    ref = S.evaluate(h, base.st, "plug", "source", 1.0)
    mfe = r0["measured benchmark Ru - Fe (unconstrained)"][0]
    assert abs(mfe["cost"] - MEASURED["Fe"]) < 1e-5 and abs(mfe["cost"] - ref["Fe"]["cost"]) < 1e-12
    assert abs(r0["measured benchmark Ru - Fe (unconstrained)"][1]["cost"] - ref["Ru_benchmark"]["cost"]) < 1e-12
    assert abs(r0["measured benchmark Ru - Fe (Ru 100-200 bar)"][1]["cost"] - ref["Ru_benchmark_best_100_200_bar"]["cost"]) < 1e-12
    for lab, key in (("0", "cashflow 0% r 0.9555"), ("12", "cashflow 12% r 0.9555")):
        g = gap(r0[f"measured supported Ru/C - Fe ({lab} %/y)"])
        assert abs(g - ref["Ru_C_supported"][key]["Ru_minus_Fe_global"]) < 1e-12
    assert abs(gap(r0["measured supported Ru/C - Fe (12 %/y)"]) - MEASURED["RuC_12"]) < 1e-5
    assert abs(gap(r0["measured supported Ru/C - Fe (0 %/y)"]) - MEASURED["RuC_0"]) < 5e-3
    assert abs(r0["measured benchmark Ru - Fe (Ru 100-200 bar)"][1]["cost"] - MEASURED["Ru_bench_100_200"]) < 5e-3
    assert abs(r0["measured benchmark Ru - Fe (unconstrained)"][1]["cost"] - MEASURED["Ru_bench"]) < 5e-3
    print(f"anchors OK: descriptor Fe {fe['cost']:.6f} / Ru {ru['cost']:.6f}; measured Fe {mfe['cost']:.6f}; "
          f"Ru/C-Fe 0 %/y {gap(r0['measured supported Ru/C - Fe (0 %/y)']):+.4f}, 12 %/y "
          f"{gap(r0['measured supported Ru/C - Fe (12 %/y)']):+.6f}  ({time.time() - t0:.0f} s)", flush=True)
    # compression rescaling == rebuilding the states with eta/k (checked once)
    k = M["COMP"]["typical"]
    hk = PerturbedHarness(S.CFG, S.ROOT, comp=k)
    assert hk.NSTATE == h.NSTATE and np.allclose(hk.state_process_cost, base.process_cost(k), rtol=1e-12, atol=1e-12)
    del hk
    # the shifted-temperature descriptor path with dT = 0 reproduces the frozen interpolation (first 300 states)
    sub = h.process_states[:300]
    conds = [h.ctx.condition(s["T_C"] + 273.15, s["condition"].pN2 / _phi(h, s, 0), s["condition"].pH2 / _phi(h, s, 1),
                             s["condition"].pNH3 / _phi(h, s, 2)) for s in sub]
    for m in ("Fe", "Ru"):
        assert np.allclose(_interp_logtof(h, conds, hc.EN0_CANON[m]), base.logtof(m, 0.0)[:300], rtol=0, atol=1e-9)
    base_gap = {c: gap(r0[c]) for c in COMPARISONS}

    # ---- scenarios
    comps = ["SEP", "APP", "COMP", "KIN", "TBED"]
    scen = [dict(name="baseline", kind="baseline", mag="", signs={}, kin_mode="Fe")]
    for km in ("Fe", "all"):
        for s in (+1, -1):
            scen.append(dict(name=f"{'KIN_Fe' if km == 'Fe' else 'KIN_all'} {'+' if s > 0 else '-'} max_plant_sizing",
                             kind="single", mag="max_plant_sizing", component="KIN", signs={"KIN": s}, kin_mode=km))
    for mag in ("typical", "max"):
        for c in comps:
            modes = ("Fe", "all") if c == "KIN" else ("Fe",)
            for km in modes:
                for s in (+1, -1):
                    lab = c if c != "KIN" else ("KIN_Fe" if km == "Fe" else "KIN_all")
                    scen.append(dict(name=f"{lab} {'+' if s > 0 else '-'} {mag}", kind="single", mag=mag,
                                     component=lab, signs={c: s}, kin_mode=km))
        for sg in itertools.product((+1, -1), repeat=5):
            for km in ("Fe", "all"):
                signs = dict(zip(comps, sg))
                scen.append(dict(name="joint " + " ".join(f"{c}{'+' if s > 0 else '-'}" for c, s in signs.items())
                                 + f" KIN[{km}] {mag}", kind="corner", mag=mag, signs=signs, kin_mode=km))
    for s in scen:
        s["params"] = (1.0, None, 1.0, ("Fe", 1.0), 0.0) if s["kind"] == "baseline" else \
            scenario_params(M, s["mag"], s["signs"], s["kin_mode"])
    groups = {}
    for s in scen:
        groups.setdefault(s["params"][:2], []).append(s)
    print(f"{len(scen)} scenarios on {len(groups)} state libraries", flush=True)

    results = []
    for (sep, app), ss in groups.items():
        lib = base if (sep, app) == (1.0, None) else Library(sep, app)
        for s in ss:
            _, _, comp, kin, dT = s["params"]
            r = evaluate(lib, comp, kin, dT)
            s["n_states"] = lib.h.NSTATE
            s["res"] = r
            results.append(s)
        print(f"  library sep {sep:.3f} approach {app if app is not None else 0.8:.3f}: {lib.h.NSTATE} states, "
              f"{len(ss)} scenarios ({time.time() - t0:.0f} s)", flush=True)
        if lib is not base:
            del lib

    # ---- outputs
    out = []
    for s in results:
        sep, app, comp, (km, kf), dT = s["params"]
        for c in COMPARISONS:
            fe, ru = s["res"][c]
            g = gap(s["res"][c])
            out.append(dict(
                scenario=s["name"], kind=s["kind"], magnitude=s["mag"],
                separator_vapour_factor=round(sep, 4), approach_to_equilibrium=round(app if app is not None else 0.8, 4),
                compression_power_factor=round(comp, 4), catalyst_amount_factor=round(kf, 4),
                catalyst_amount_applies_to=("Fe only" if km == "Fe" else "all catalysts") if kf != 1.0 else "",
                bed_temperature_offset_C=round(dT, 2), n_states=s["n_states"], comparison=c,
                Fe_cost=_c(fe), Ru_cost=_c(ru), gap_Ru_minus_Fe=_c(g), baseline_gap=round(base_gap[c], 6),
                first=_first(g), flip=_flip(g, base_gap[c]),
                Fe_opt=_o(fe), Ru_opt=_o(ru)))
    write_csv(HERE / "perturbation_results.csv", out)

    # summary: Ru-favouring direction of each single component, joint Ru-favouring and worst corner per comparison
    summ2 = dict(magnitudes=M, baseline={c: base_gap[c] for c in COMPARISONS}, comparisons={})
    for c in COMPARISONS:
        cs = dict(baseline_gap=base_gap[c], singles={}, joint_Ru_favouring={}, worst_corner={})
        for mag in ("typical", "max"):
            fav = {}
            for comp_ in ("SEP", "APP", "COMP", "TBED"):
                g = {sg: gap(next(s for s in results if s["name"] == f"{comp_} {sg} {mag}")["res"][c]) for sg in "+-"}
                d = min(g, key=lambda x: _key(g[x]))
                fav[comp_] = +1 if d == "+" else -1
                cs["singles"][f"{comp_} {mag}"] = dict(plus=g["+"], minus=g["-"], Ru_favouring=d)
            gk = {(km, sg): gap(next(s for s in results if s["name"] == f"{'KIN_Fe' if km == 'Fe' else 'KIN_all'} {sg} {mag}")["res"][c])
                  for km in ("Fe", "all") for sg in "+-"}
            kbest = min(gk, key=lambda x: _key(gk[x]))
            cs["singles"][f"KIN {mag}"] = {f"{km}{sg}": v for (km, sg), v in gk.items()} | dict(Ru_favouring=f"{kbest[0]}{kbest[1]}")
            fav["KIN"] = +1 if kbest[1] == "+" else -1
            name = "joint " + " ".join(f"{k}{'+' if fav[k] > 0 else '-'}" for k in comps) + f" KIN[{kbest[0]}] {mag}"
            js = next(s for s in results if s["name"] == name)
            cs["joint_Ru_favouring"][mag] = dict(scenario=name, gap=gap(js["res"][c]), Fe=_c(js["res"][c][0]),
                                                 Ru=_c(js["res"][c][1]), Fe_opt=_o(js["res"][c][0]), Ru_opt=_o(js["res"][c][1]))
            corners = [s for s in results if s["kind"] == "corner" and s["mag"] == mag]
            w = min(corners, key=lambda s: _key(gap(s["res"][c])))
            cs["worst_corner"][mag] = dict(scenario=w["name"], gap=gap(w["res"][c]), Fe=_c(w["res"][c][0]),
                                           Ru=_c(w["res"][c][1]), Fe_opt=_o(w["res"][c][0]), Ru_opt=_o(w["res"][c][1]),
                                           n_flipped=sum(_flip(gap(s["res"][c]), base_gap[c]) == "yes" for s in corners),
                                           n_no_decision=sum(_flip(gap(s["res"][c]), base_gap[c]) == "no decision" for s in corners),
                                           n_corners=len(corners))
        singles = [s for s in results if s["kind"] == "single"]
        cs["single_flips"] = [s["name"] for s in singles if _flip(gap(s["res"][c]), base_gap[c]) == "yes"]
        cs["n_single_flips"] = len(cs["single_flips"])
        cs["n_singles"] = len(singles)
        summ2["comparisons"][c] = cs
    summ2["seconds"] = time.time() - t0
    (HERE / "perturbation_summary.json").write_text(json.dumps(_clean(summ2), indent=1) + "\n", encoding="utf-8")
    for c in COMPARISONS:
        cs = summ2["comparisons"][c]
        print(f"\n{c}: baseline {cs['baseline_gap']:+.3f}; single flips {cs['n_single_flips']}/{cs['n_singles']}")
        for mag in ("typical", "max"):
            j, w = cs["joint_Ru_favouring"][mag], cs["worst_corner"][mag]
            print(f"   {mag:7s} joint Ru-favouring {j['gap']:+.3f} ({j['scenario']}); worst corner {w['gap']:+.3f} "
                  f"({w['scenario']}); corners flipped {w['n_flipped']}/{w['n_corners']}, no decision {w['n_no_decision']}")
    print(f"\ndone in {time.time() - t0:.0f} s")


def _first(g):
    return "neither feasible" if math.isnan(g) else "Fe" if g > 0 else "Ru" if g < 0 else "tie"


def _flip(g, g0):
    return "no decision" if math.isnan(g) else ("yes" if (g > 0) != (g0 > 0) else "no")


def _key(g):
    return math.inf if math.isnan(g) else g


def _c(x):
    if x is None:
        return "infeasible"
    if isinstance(x, dict):
        x = x["cost"]
    return round(float(x), 6) if math.isfinite(x) else ("+inf" if x > 0 else "-inf")


def _o(d):
    return "" if d is None else f"{d['T_C']:.0f} C / {d['P_bar']:.0f} bar / {d['Tsep_C']:.0f} C / {d['V_m3']:.1f} m3"


def _clean(o):
    if isinstance(o, (float, np.floating)):
        return round(float(o), 6) if math.isfinite(o) else str(o)
    if isinstance(o, dict):
        return {str(k): _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_clean(v) for v in o]
    return o


if __name__ == "__main__":
    main()
