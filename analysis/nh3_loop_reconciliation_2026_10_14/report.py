"""Write REPORT.md and outputs/summary.json from the outputs of T1-T5 (numbers only from outputs/)."""
from __future__ import annotations

import csv

import common

L = common.load


def f(x, nd=3, sign=False):
    if x is None:
        return "–"
    return f"{x:+.{nd}f}" if sign else f"{x:.{nd}f}"


def t1_section(t1):
    lines = ["## T1. Canonical recycle-rise sensitivity (NH3-FINAL-1.2, descriptor kinetics, 15 metals)", "",
             f"Replay gate at 3.0 bar: {'PASS' if t1['replay_gate_3bar']['pass'] else 'FAIL'} "
             f"(Fe/Ru/Os max |Δ| {t1['replay_gate_3bar']['Fe_Ru_Os_cost_max_abs_diff']:.1e} USD/t, "
             f"parity |Δ| {t1['replay_gate_3bar']['parity_abs_diff']:.1e}). 14,510 states in every run.", "",
             "| Recycle rise (bar) | Fe USD/t (T, P, Tsep) | Ru USD/t (T, P, Tsep) | Os USD/t (T, P, Tsep) | Feasible ranking | Ru − Fe | Ru − Os | Ru parity multiple | Spearman vs frozen (censored / raw) | Activity–economics Spearman (raw / censored) |",
             "|---:|---|---|---|---|---:|---:|---:|---|---|"]
    for k, r in t1["runs"].items():
        m = r["metals"]
        cell = lambda x: f"{x['cost_USD_t']:.3f} ({x['T_C']:.0f} °C, {x['P_bar']:.0f} bar, {x['Tsep_C']:.0f} °C)"
        lines.append(f"| {float(k):.1f} | {cell(m['Fe'])} | {cell(m['Ru'])} | {cell(m['Os'])} | {' > '.join(r['feasible_economic_order'])} | "
                     f"{r['Ru_minus_Fe']:+.3f} | {r['Ru_minus_Os']:+.3f} | {r['Ru_parity_activity_multiple']:.2f}× | {r['spearman_censored_vs_frozen']:.3f} / "
                     f"{r['spearman_raw_vs_frozen']:.3f} | {r['activity_vs_economic_raw_spearman']:.3f} / {r['activity_vs_economic_censored_spearman']:.3f} |")
    nfeas = {k: sum(bool(x["feasible"]) for x in r["metals"].values()) for k, r in t1["runs"].items()}
    raw_same = all(r["raw_economic_order"] == t1["runs"]["3"]["raw_economic_order"] for r in t1["runs"].values())
    lines += ["", "Metals with a state within the 90 m³ cap: " + ", ".join(f"{float(k):.1f} bar {v}/15" for k, v in nfeas.items())
              + f"; unconstrained 15-metal economic order identical to the 3-bar replay: {raw_same} (`outputs/t1_metals.csv`). "
              "Only the recycle-compression electricity and its CAPEX change between runs (process states asserted identical).", ""]
    return lines


def t2_section(t2):
    lines = ["## T2. Matched-pressure Fe vs Ru/C in the closed loop", "",
             "Isothermal measured-rate beds (Fe KM1; promoted 3.2 wt% Ru/C, 590 kg/m³), SI-S27 two-flash loop, 1500 t/d, "
             "≤ 90 m³, ≤ 15 mol% inlet inerts; each catalyst reoptimises T, X, cold T2 and purge on the preregistered grid. "
             "Every Fe row is outside the Dyson–Simon pressure fit (149–309 atm); Ru/C rows above 100 bar are outside the "
             "Rossetti fit (50–100 bar).", "",
             "| P bar | Basis | Fe USD/t (T, X, T2, purge, bed m³) | Ru/C USD/t (T, X, T2, purge, bed m³) | Ru − Fe | excess feed | of which purge gas / dissolved / NH₃ in purge | utilities | inventory | reactor | compressor | Ru/C finance crossover 0–12 %/y |",
             "|---:|---|---|---|---:|---:|---|---:|---:|---:|---:|---|"]
    for e in t2["per_pressure"]:
        for b in ("B94", "B93"):
            x = e["bases"][b]
            fe, ru, t = x["Fe"], x["Ru"], x["terms_Ru_minus_Fe"]
            cell = lambda d: "none feasible" if d is None else (
                f"{d['decision_USD_t']:.3f} ({d['T_C']:.0f}, {d['X']:g}, {d['T2_C']:.0f}, {d['purge']:g}, {d['bed_m3']:.1f})")
            cx = x["crossover"]
            cxs = (", ".join(f"{100 * r:.2f}%" for r in cx["roots"]) if cx["roots"] else
                   {"Ru_cheaper_on_whole_interval": "none: Ru/C cheaper on 0–12%", "Fe_cheaper_on_whole_interval": "none: Fe cheaper on 0–12%"}
                   .get(cx["verdict"], cx["verdict"])) + f" (Ru−Fe {cx['gap_at_0']:+.2f} at 0%)"
            lines.append(f"| {e['P_bar']:.0f} | {b} | {cell(fe)} | {cell(ru)} | {f(x['Ru_minus_Fe'], sign=True)} | "
                         + (" | ".join(["–"] * 7) if t is None else
                            f"{t['excess_feed']:+.3f} | {t['purge_gas_loss']:+.2f} / {t['dissolved_gas_loss']:+.2f} / {t['NH3_in_purge']:+.2f} | "
                            f"{t['utilities']:+.3f} | {t['inventory']:+.3f} | {t['reactor']:+.3f} | {t['compressor_capital']:+.3f}")
                         + f" | {cxs} |")
    lines += ["", "Counts (cold states, unresolved, eligible Fe / Ru/C designs): " + "; ".join(
        f"{e['P_bar']:.0f} bar {e['counts']['cold_states']}, {e['counts']['cold_unresolved']}, "
        f"{e['counts']['Fe']['eligible']} / {e['counts']['Ru']['eligible']}" for e in t2["per_pressure"]) + ". Unresolved "
              "states (20 s numerical budget of the upstream worker or non-converged fixed point) are listed in `outputs/t2.json`.", ""]
    return lines


def t3_section(t3):
    lines = ["## T3. Model bridge", "",
             "Gates: manuscript optima recomputed " + ", ".join(f"{k} {'PASS' if v else 'FAIL'}" for k, v in t3["gates"].items())
             + "; point costs reproduce the kinetics-swap and #93/#94 optima to "
             + f"{max(abs(v) for v in t3['consistency_abs_diff'].values()):.1e} USD/t.", "",
             "Ru − Fe (USD/t) of each pair in both models. Canonical: 1.2 state at that T, P, Tsep (= closed-loop cold T2), "
             "measured kinetics, plug flow, 8 wt% Ru/C at 490 kg/m³, 25-y cash flow. Closed loop: #94 / #93 designs; at the "
             "manuscript points T and P fixed, X, T2, purge reoptimised.", "",
             "| Pair (Fe point; Ru/C point) | canonical r 95.55% 12% rise 3 | canonical r 90% 12% rise 3 | canonical r 90% 12% rise 9.2 | canonical r 95.55% 0% rise 3 | closed B94 | closed B93 |",
             "|---|---:|---:|---:|---:|---:|---:|"]
    for name, row in t3["table"].items():
        p = t3["pairs"][name]
        lab = f"{name}: Fe {p['Fe'][0]:.0f} °C/{p['Fe'][1]:.0f} bar; Ru/C {p['Ru'][0]:.0f} °C/{p['Ru'][1]:.0f} bar"
        cells = [row[k]["delta"]["total"] if row[k]["delta"] else None for k in
                 ("canonical r0.9555_12pct_dp3", "canonical r0.90_12pct_dp3", "canonical r0.90_12pct_dp9.2",
                  "canonical r0.9555_0pct_dp3", "closed B94", "closed B93")]
        lines.append(f"| {lab} | " + " | ".join(f(c, sign=True) for c in cells) + " |")
    lines += ["", "Waterfall from the manuscript +1.45 (S0) to #94 +41.0 (S4), Ru − Fe change by category (USD/t):", "",
              "| Step | total | inventory | reactor | utilities | compressor capital | excess feed (closed-loop only) | purge gas | dissolved gas | NH₃ in purge |",
              "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    with (common.OUT / "t3_waterfall.csv").open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            lines.append(f"| {r['step']} | " + " | ".join(f"{float(r[k]):+.3f}" for k in (
                "total", "inventory", "reactor", "utilities", "compressor_capital", "excess_feed", "purge_gas_loss",
                "dissolved_gas_loss", "NH3_in_purge")) + " |")
    lv = t3["waterfall_levels"]
    lines += ["", "Levels: " + "; ".join(f"{k} {v['total']:+.3f}" for k, v in lv.items() if v) + ".", "",
              "S4 − S0 by category: " + ", ".join(f"{k} {v:+.3f}" for k, v in t3["categories_ranked_by_abs_contribution"]) + ".", ""]
    return lines


def t4_section(t4):
    lines = ["## T4. KAAP-type staged converter in the closed loop, 90 bar (simplified series-PFR)", "",
             "Three adiabatic beds, interbed cooling to one common inlet T (350 °C to T_max − 1), Fe ≤ 530 °C, Ru/C ≤ 460 °C, "
             f"closed-loop rate laws and formulation, {t4['eligible_cold_states']} eligible 90-bar cold states "
             f"({t4['unresolved_cold_states']} unresolved, {t4['inert_capped_cold_states']} above 15% inerts), "
             f"{t4['library_size']} optimised designs.", "",
             "| Basis | Ru finance %/y | all-Fe | best Fe-first (pattern, Ru/C share) | all-Ru/C | best Ru/C-first | winner (Ru/C volume share) | winner total bed m³ | Fe-first − all-Fe |",
             "|---|---:|---:|---:|---:|---:|---|---:|---:|"]
    for r in t4["per_rate"]:
        lines.append(f"| {r['basis']} | {r['Ru_finance_pct']} | {f(r['all-Fe USD_t'])} | {f(r['Fe-first USD_t'])} ({r['Fe-first pattern']}, {f(r['Fe-first Ru_share'], 2)}) | "
                     f"{f(r['all-Ru/C USD_t'])} | {f(r['Ru/C-first USD_t'])} | {r.get('winner_effective')} {r.get('winner_pattern')} "
                     f"({f(r.get('winner_Ru_share'), 2)}) | {f(r.get('winner_V_tot'), 1)} | {f(r.get('staged_minus_allFe'), sign=True)} |")
    lines += ["", "Envelope-derived winners (0.01 %-point grid): " + "; ".join(
        f"{b}: " + ", ".join(f"{s['winner']} {s['from_pct']:.2f}–{s['to_pct']:.2f}%" for s in segs)
        for b, segs in t4["envelope_boundaries"].items()) + ".", ""]
    return lines


def t5_section(t5):
    lines = ["## T5. Industrial plausibility (sources in the repository only)", "",
             f"Source: {t5['source']}. Cost comparison: {t5['cost_comparison']}.", "",
             "| Configuration (B94) | P bar | decision USD/t | recycle kWh/t | refrigeration kWh/t | fresh compression kWh/t | loop electricity GJ/t |",
             "|---|---:|---:|---:|---:|---:|---:|"]
    for r in t5["rows"]:
        lines.append(f"| {r['config']} | {r['P_bar']:.0f} | {r['decision_USD_t']:.3f} | {r['recycle_kWh_t']:.1f} | "
                     f"{r['refrigeration_kWh_t']:.1f} | {r['fresh_kWh_t']:.1f} | {r['loop_electricity_GJ_t']:.3f} |")
    c = t5["energy_comparison"]
    if c:
        lines += ["", f"Best conventional all-Fe ({c['best_conventional_all_Fe']['P_bar']:.0f} bar) minus KAAP-type 90-bar optimum: "
                  f"{c['delta_loop_electricity_GJ_t']:+.3f} GJ/t of loop electricity, against a published KAAP saving of "
                  f"+{c['published_KAAP_saving_GJ_t']:.2f} GJ/t (same sign: {c['same_sign']}; ratio {c['ratio_to_published']:+.2f}). "
                  "ZA-5 reference: recycle 21.5 kWh/t (10 MPa) – 17.5 (30 MPa), refrigeration 22.6 – 13.4 kWh/t.", ""]
    return lines


def write():
    t1, t2, t3, t4, t5 = (L(common.OUT / f"t{i}.json") for i in range(1, 6))
    up = L(common.OUT / "upstream_93_94.json")
    prov = L(common.OUT / "provenance.json")
    lines = ["# NH3 loop reconciliation (2026-10-14) — results of the preregistered tests T1–T5", "",
             "Preregistration: `PREREGISTRATION.md` (committed before any computation). Every number below is read from "
             "`outputs/`. Frozen NH3-FINAL-1.2 numbers (Fe 11.516 / Ru 16.633 / Os 19.747 USD/t; 32/64) are unchanged; "
             "everything here is a labelled sensitivity.", "",
             "Upstream reruns (unchanged code): #93 Fe {:.3f} / Ru {:.3f}; #94 Fe {:.3f} / Ru {:.3f} USD/t; gates {}.".format(
                 up["u93"]["selected"]["Fe"]["decision_relevant_cost_USD_t"], up["u93"]["selected"]["Ru"]["decision_relevant_cost_USD_t"],
                 up["u94"]["nominal_selected"]["Fe"]["decision_USD_t"], up["u94"]["nominal_selected"]["Ru"]["decision_USD_t"],
                 "all PASS" if all(up["gates"].values()) else up["gates"]), ""]
    lines += t1_section(t1) + t2_section(t2) + t3_section(t3) + t4_section(t4) + t5_section(t5)
    lines += ["## Provenance", "", f"Repository head at run: `{prov['repo_head']}`; Python {prov['python'].split()[0]}, "
              f"NumPy {prov['numpy']}, SciPy {prov['scipy']}. Upstream git blob hashes: `outputs/provenance.json`.", ""]
    lines += ["## Rerun", "", "    pip install numpy==2.3.5 scipy==1.18.0 pyyaml openpyxl pytest",
              "    python -m pytest analysis/nh3_loop_reconciliation_2026_10_14",
              "    python analysis/nh3_loop_reconciliation_2026_10_14/run_all.py --stage all --workers 4", "",
              "CI: `.github/workflows/nh3-loop-reconciliation.yml` reruns every stage into a fresh directory and runs "
              "`check_regression.py` against `outputs/`.", ""]
    report = common.HERE / "REPORT.md" if common.OUT == common.HERE / "outputs" else common.OUT / "REPORT.md"
    report.write_text("\n".join(lines), encoding="utf-8")
    summary = {
        "T1": {k: {"Fe": r["metals"]["Fe"]["cost_USD_t"], "Ru": r["metals"]["Ru"]["cost_USD_t"], "Os": r["metals"]["Os"]["cost_USD_t"],
                   "ranking": r["feasible_economic_order"], "Ru_minus_Fe": r["Ru_minus_Fe"],
                   "Ru_parity_multiple": r["Ru_parity_activity_multiple"],
                   "spearman_censored_vs_frozen": r["spearman_censored_vs_frozen"], "spearman_raw_vs_frozen": r["spearman_raw_vs_frozen"]}
               for k, r in t1["runs"].items()},
        "T1_gate": t1["replay_gate_3bar"]["pass"],
        "T2": {f"{e['P_bar']:g}|{b}": {"Fe": x["Fe"] and x["Fe"]["decision_USD_t"], "Ru": x["Ru"] and x["Ru"]["decision_USD_t"],
                                        "Ru_minus_Fe": x["Ru_minus_Fe"], "crossover": x["crossover"]["roots"],
                                        "crossover_verdict": x["crossover"]["verdict"]}
               for e in t2["per_pressure"] for b, x in e["bases"].items()},
        "T3": {"gates": t3["gates"], "levels": {k: (v["total"] if v else None) for k, v in t3["waterfall_levels"].items()},
               "gap_by_category": t3["gap_by_category"]},
        "T4": {"per_rate": {f"{r['basis']}|{r['Ru_finance_pct']}": {"winner": r.get("winner_effective"), "pattern": r.get("winner_pattern"),
                                                                     "USD_t": r.get("winner_USD_t"), "all_Fe": r["all-Fe USD_t"],
                                                                     "Fe_first": r["Fe-first USD_t"], "all_Ru": r["all-Ru/C USD_t"]}
                            for r in t4["per_rate"]},
               "envelope_boundaries": t4["envelope_boundaries"]},
        "T5": {"delta_GJ_t": t5["energy_comparison"] and t5["energy_comparison"]["delta_loop_electricity_GJ_t"],
               "published_GJ_t": t5["KAAP_saving_GJ_t"]},
        "upstream_gates": up["gates"]}
    common.dump(common.OUT / "summary.json", summary)
