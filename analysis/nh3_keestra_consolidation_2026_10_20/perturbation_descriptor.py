"""Descriptor-only rerun of the registered design with upgraded benchmark magnitudes.

Run with NH3_MODEL=1.2 and PYTHONDONTWRITEBYTECODE=1 using the core interpreter.
The upstream library, interpolation, perturbation parameters and gap semantics are
imported unchanged. Scenario enumeration, CSV fields and summary follow its main().
"""
import itertools
import json
import math
import os
import sys
import time
from pathlib import Path

os.environ["NH3_MODEL"] = "1.2"
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "nh3_benchmark_error_table_2026_10_19"))
import run_error_table as E
import numpy as np
from run_error_table import (Library, PerturbedHarness, S, NM, hc, ANCHOR_FE, ANCHOR_RU,
                             scenario_params, gap, write_csv, _phi, _interp_logtof,
                             _opt, _c, _o, _flip, _first, _key, _clean)

COMPARISONS = ["descriptor Ru - Fe", "descriptor Os - Fe"]


def evaluate(lib, comp=1.0, kin=("Fe", 1.0), dT=0.0):
    """The descriptor portion of E.evaluate, with its process-cost restoration."""
    h = lib.h
    saved = h.state_process_cost
    h.state_process_cost = lib.process_cost(comp)
    try:
        mode, factor = kin
        d = {}
        for metal, amount in (("Fe", factor), ("Ru", factor if mode == "all" else 1.0),
                              ("Os", factor if mode == "all" else 1.0)):
            total, volume, _, _ = h.cost_arrays(metal, lib.logtof(metal, dT), alpha=1.0 / amount)
            d[metal] = _opt(h, total, volume)
        return {"descriptor Ru - Fe": (d["Fe"], d["Ru"]),
                "descriptor Os - Fe": (d["Fe"], d["Os"])}
    finally:
        h.state_process_cost = saved


class Tee:
    def __init__(self, stream, log):
        self.stream, self.log = stream, log

    def write(self, text):
        self.stream.write(text)
        self.log.write(text)
        self.flush()

    def flush(self):
        self.stream.flush()
        self.log.flush()


def main():
    t0 = time.time()
    M = json.loads((HERE / "perturbation_magnitudes.json").read_text(encoding="utf-8"))
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
    print(f"anchors OK: Fe {fe['cost']:.6f} / Ru {ru['cost']:.6f}; Fe { _o(fe) }; Ru { _o(ru) }", flush=True)
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
    assert len(scen) == 157
    assert sum(s["kind"] == "single" for s in scen) == 28
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
                Fe_cost=_c(fe), Ru_cost=_c(ru), gap_Ru_minus_Fe="nan" if math.isnan(g) else _c(g), baseline_gap=round(base_gap[c], 6),
                first=_first(g), flip=_flip(g, base_gap[c]),
                Fe_opt=_o(fe), Ru_opt=_o(ru)))
    write_csv(HERE / "perturbation_descriptor_results.csv", out)

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
        finite = [s for s in singles if math.isfinite(gap(s["res"][c]))]
        smallest = min(finite, key=lambda s: gap(s["res"][c]))
        cs["min_finite_single"] = dict(scenario=smallest["name"], gap=gap(smallest["res"][c]))
        cs["single_feasibility"] = dict(
            finite=len(finite), Fe_infeasible=sum(gap(s["res"][c]) == -math.inf for s in singles),
            other_infeasible=sum(gap(s["res"][c]) == math.inf for s in singles),
            neither_feasible=sum(math.isnan(gap(s["res"][c])) for s in singles))
        summ2["comparisons"][c] = cs
    summ2["seconds"] = time.time() - t0
    (HERE / "perturbation_descriptor_summary.json").write_text(json.dumps(_clean(summ2), indent=1) + "\n", encoding="utf-8")
    for c in COMPARISONS:
        cs = summ2["comparisons"][c]
        print(f"\n{c}: baseline {cs['baseline_gap']:+.3f}; single flips {cs['n_single_flips']}/{cs['n_singles']}")
        print("   smallest finite single:", cs["min_finite_single"], "feasibility:", cs["single_feasibility"])
        for mag in ("typical", "max"):
            j, w = cs["joint_Ru_favouring"][mag], cs["worst_corner"][mag]
            print(f"   {mag:7s} joint Ru-favouring {j['gap']:+.3f} ({j['scenario']}); worst corner {w['gap']:+.3f} "
                  f"({w['scenario']}); corners flipped {w['n_flipped']}/{w['n_corners']}, no decision {w['n_no_decision']}")
    print(f"\ndone in {time.time() - t0:.0f} s")


if __name__ == "__main__":
    with (HERE / "perturbation_descriptor_stdout.txt").open("w", encoding="utf-8") as log:
        original = sys.stdout
        sys.stdout = Tee(original, log)
        try:
            main()
        finally:
            sys.stdout = original
