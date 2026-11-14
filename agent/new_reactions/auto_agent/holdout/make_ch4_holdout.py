"""Writes holdout/ch4.json and holdout/PREREG_AI_BUILD_CH4.json (run before the first CO2-methanation AI build).

Sources chosen from holdout/ch4_holdout_research.md (2026-11-12). Build mode V2 (flowsheet first, physics-consistency gate) is the
user's decision of 2026-11-12 after the PDH builds all missed regeneration, compression and separation energy.
"""
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

H = Path(__file__).resolve().parent
A = H.parent
sys.path.insert(0, str(A.parent))
import analyze as an  # noqa: E402

D59 = ("https://www.storeandgo.info/fileadmin/downloads/deliverables_2020/"
       "20200713-STOREandGO_D5.9_DVGW_Final_report_on_evaluation_of_technologies_and_processes.pdf")
MW_SNG_T_Y = 25950 / 50          # t CH4 per year per MW SNG (HHV 55.5 MJ/kg, 8000 h/y; D5.9 p.31, p.71)

hold = {
    "rxn": "ch4", "written": datetime.now().isoformat(timespec="seconds"),
    "note": "Evaluation side only. Never copied into an agent workspace. Chosen before the first AI build.",
    "sources": [
        {"name": "STORE&GO D5.9 Final report on evaluation of technologies and processes (DVGW-EBI/KIT, v2.0, 2020)", "url": D59},
        {"name": "Schlautmann et al., Chem. Ing. Tech. 93 (2021) 568 (same data)", "url": "https://doi.org/10.1002/cite.202000187"},
        {"name": "Electrochaea P2G-BioCat final report, ForskEL 2014-1-12164 (capital cross-check)",
         "url": "https://energiforskning.dk/sites/energiforskning.dk/files/slutrapporter/12164_final_report_p2g_biocat.pdf"}],
    "dois": ["10.1002/cite.202000187", "10.1016/j.apenergy.2020.114780"],
    "url_fragments": ["storeandgo", "cordis.europa.eu/project/id/691797", "cite.202000187", "publikationen.bibliothek.kit.edu/1000130144",
                      "s0306261920302920", "12164_final_report_p2g_biocat", "energiforskning.dk/sites/energiforskning.dk/files/slutrapporter/12164",
                      "database.co2value.eu/projects/7", "stloendays", "catalyst-essay"],
    "keyword_sets": [["falkenhagen", "720 €/kw"], ["falkenhagen", "3740"], ["falkenhagen", "360 €/kw"], ["solothurn", "380 €/kw"],
                     ["store&go", "methanation", "capex"], ["460 m³/h", "6450"], ["25 kw/mw", "methanation"],
                     ["falkenhagen", "0.8 kwh/m³"], ["biocat", "63.54"], ["avedøre", "methanation", "dkk"]],
    "targets": {
        "H2 per t CH4": {"quantity": "boundary_in:H2", "value": 0.505, "tol": 0.05,
                         "source": "D5.9 Table 4-1 p.35 (measured, Falkenhagen: 708 kW H2 -> 549 kW SNG, HHV) and Table 5-2 p.68 (5 MW design: 6450 kW H2)"},
        "CO2 per t CH4": {"quantity": "boundary_in:CO2", "value": 2.785, "tol": 0.05,
                          "source": "D5.9 Table 5-2 p.68: 460 m3(STP)/h CO2 per 5 MW SNG (design); Audi Werlte 2.8 t/t as support"},
        "purchased energy GJ per t": {"quantity": "energy_GJ_per_t", "value": 3.84, "tol": 0.35,
                                      "source": "D5.9 Table 5-2 / p.70: methanation electricity 0.29 kWh/m3 SNG (25 kW/MW) = 1.46 GJe/t, primary at 0.38; CO2 supply and grid injection outside the boundary"},
        "installed capital per annual t": {"quantity": "capex_usd_per_t_y", "value": 784, "tol": [-0.30, 0.50],
                                           "scale_curve": [[round(5 * MW_SNG_T_Y), 1567], [round(10 * MW_SNG_T_Y), 1035], [round(50 * MW_SNG_T_Y), 784]],
                                           "source": "D5.9 p.63, Table 1-2 p.7, Table 5-1 p.67: optimised Falkenhagen design 720 / ~475 / 360 EUR/kW SNG at 5 / 10 / 50 MW (EUR2017, 1.1297 USD/EUR); methanation unit only; tolerance AACE class 4"}},
    "reported_not_gated": {
        "measured methanation electricity at demo scale, primary GJ/t": {"value": 10.6, "basis": "D5.9 Table 4-2 p.39: 0.8 kWh/m3 SNG at Falkenhagen (0.58 MW), /0.38; Solothurn 1.0 kWh/m3 -> 13.2"},
        "BioCat 50 MWe methanation capital USD/(t/y)": {"value": [560, 700], "basis": "BioCat final report Fig. 1.8 p.24: 63.54 MDKK"},
        "hand-built model capital USD/(t/y)": {"value": 449, "basis": "configs/ch4_ours.json (Goetz 2016, 175 EUR/kW); below the -30 % band of this holdout"}},
    "pass_rule": {"min_within": 4,
                  "rule": "pass = all four targets within tolerance; partial = three within and none beyond twice the tolerance; fail otherwise. "
                          "Capital target = log-log interpolation of scale_curve at the build's capacity (evaluate_builds.py)."}}
(H / "ch4.json").write_text(json.dumps(hold, indent=1, ensure_ascii=False), encoding="utf-8")

n_common = len(an.load("ch4"))
prereg = {
    "id": "AI-BUILD-CH4-V2", "written": datetime.now().isoformat(timespec="seconds"),
    "guidance": ("docs/SUPERVISOR_FEEDBACK_2026-11-11.md and the supervisor's reply of 2026-11-11 (PDH first, then methanation, then NH3/MeOH "
                 "blind tests; validation TEA held out; tolerances and the disagreement rule fixed in advance)."),
    "change_from_pdh": ("build mode V2 (user decision 2026-11-12): the agent draws the process first (flowsheet.json with an 8-category "
                        "checklist, submit_flowsheet) and may write model.py only afterwards; model energy and capital are sums over the "
                        "flowsheet units; check_model adds a physics-consistency gate (element and mass balance, per-pass conversion <= "
                        "equilibrium + 0.03 with NIST Shomate thermo, reaction heat, heat supply, isothermal minimum compression work, "
                        "minimum separation work, unit-sum accounting). The three PDH builds keep their V1 results."),
    "task": "runner.py --build ch4 --reaction 'CO2 methanation (CO2 + 4 H2 -> CH4 + 2 H2O)'",
    "agent": {"model": "gpt-5.5", "route": "API-YES credential 邪修gpt", "extraction_model": "gpt-5.5", "max_turns": 110,
              "n_target_papers": 12, "n_max_downloads": 20,
              "workspace": "D:/agent_runs/<run> (outside the repository); scripts restricted to relative paths"},
    "not_visible_to_the_agent": ["agent/new_reactions/plant_models.py, plant_framework.py, configs/*, params*.json, SOURCES.md, results/*",
                                 "auto_agent/holdout/*", "the NCE repository and its PRs (url fragments audited)"],
    "builds": ("3 independent builds ch4_b1..b3 (separate workspaces); a build that fails check_model at finish or whose holdout audit "
               "finds a leak is invalid and replaced; every replacement is reported"),
    "diagnostic": ("one PDH build with V2 (pdh_v2_d1) to see whether flowsheet-first closes the PDH energy gap; reported as a diagnostic, "
                   "it does not replace or join the three V1 PDH builds"),
    "validation": ("evaluate_builds.py against holdout/ch4.json (H2 and CO2 t/t +-5 %, purchased primary energy GJ/t +-35 %, capital per "
                   "annual t -30/+50 % on the D5.9 scale curve at the build's capacity); pass/partial/fail as in pass_rule"),
    "agreement_rule": {
        "per_conclusion": (f"largest cost item, controlling catalyst property, cheapest catalyst on the common record set (the {n_common} "
                           "PR #122 CH4 records): robust = 3/3, majority = 2/3, model-dependent = no majority; all three builds reported"),
        "quantitative": "reference-cost spread max/min - 1 <= 20 % and every pairwise Spearman of record costs >= 0.8 is called consistent",
        "primary_build": "the build with the median reference cost, fixed before the holdout comparison is looked at",
        "selection": "no selection of builds by TEA fit"},
    "ledger": "stage_ledger.csv per build; human_log.csv (every human intervention with type and minutes)",
    "frozen_sha256": {f: hashlib.sha256((A / f).read_bytes()).hexdigest()
                      for f in ["runner.py", "build_mode.py", "physics_gate.py", "full_mode.py", "evaluate_builds.py", "audit_holdout.py",
                                "holdout/ch4.json"]}}
(H / "PREREG_AI_BUILD_CH4.json").write_text(json.dumps(prereg, indent=1, ensure_ascii=False), encoding="utf-8")
print(f"written ch4.json and PREREG_AI_BUILD_CH4.json; common CH4 records {n_common}")
