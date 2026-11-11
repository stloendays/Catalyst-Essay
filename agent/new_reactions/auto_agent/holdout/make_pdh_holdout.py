"""Writes holdout/pdh.json and holdout/PREREG_AI_BUILD_PDH.json (run before the first AI build)."""
import hashlib
import json
from datetime import datetime
from pathlib import Path

H = Path(__file__).resolve().parent
A = H.parent
hold = {
    "rxn": "pdh", "written": datetime.now().isoformat(timespec="seconds"),
    "note": "Evaluation side only. Never copied into an agent workspace. Chosen before the first AI build.",
    "sources": [
        {"name": "PetroLogistics LP Form 10-K FY2012 (Catofin plant, Houston)",
         "url": "https://www.sec.gov/Archives/edgar/data/0001523733/000110465913018856/a12-28443_110k.htm"},
        {"name": "PetroLogistics LP 424B4 prospectus 2012 (same plant)",
         "url": "https://www.sec.gov/Archives/edgar/data/1523733/000104746912005401/a2209406z424b4.htm"},
        {"name": "Enterprise Products Mont Belvieu PDH, EPA GHG PSD permit application, Dec 2012 (and EPA statement of basis)",
         "url": "https://archive.epa.gov/region6/6pd/air/pd-r/ghg/web/pdf/enterprise-propane-dehydrogenation-app.pdf"}],
    "dois": [],
    "url_fragments": ["edgar/data/0001523733", "edgar/data/1523733", "petrologistics", "region6/6pd/air/pd-r/ghg",
                      "enterprise-propane", "stloendays", "catalyst-essay"],
    "keyword_sets": [["enterprise", "propane dehydrogenation", "1,300,000,000"], ["enterprise", "pdh", "1.654 billion"]],
    "targets": {
        "propane per t propylene": {"quantity": "feed_t_per_t", "value": 1.20, "tol": 0.05,
                                    "source": "PetroLogistics 10-K FY2012 MD&A: 1.0 lb propylene per 1.2 lb propane"},
        "purchased energy GJ per t": {"quantity": "energy_GJ_per_t", "value": 17.5, "tol": 0.35,
                                      "source": "PetroLogistics 424B4: 9.96 M MMBtu natural gas for ~601 kt propylene; EPA application heat-duty cap ~27 GJ/t is an upper bound"},
        "installed capital per annual t": {"quantity": "capex_usd_per_t_y", "value": 1.30e9 / 750e3, "tol": [-0.30, 0.50],
                                           "source": "Enterprise EPA application s6.1: 1.30 bn USD (2012) for 750 kt/y; tolerance AACE class 4 (-30/+50 %)"}},
    "reported_not_gated": {
        "production cost 2012 USD/t (no by-product credit)": {"value": 882, "basis": "PetroLogistics 10-K: 504.2 M USD / 571.5 kt; propane at 1.00 USD/gal"},
        "propane share of production cost": {"value": 0.75, "basis": "PetroLogistics 10-K, 2012 prices"},
        "capital recovery factor": {"value": 0.0944, "basis": "Enterprise: 7 %, 20 y"}},
    "pass_rule": {"min_within": 3,
                  "rule": "pass = all three targets within tolerance; partial = two within and none beyond twice the tolerance; fail otherwise"}}
(H / "pdh.json").write_text(json.dumps(hold, indent=1), encoding="utf-8")

prereg = {
    "id": "AI-BUILD-PDH-V1", "written": datetime.now().isoformat(timespec="seconds"),
    "guidance": ("docs/SUPERVISOR_FEEDBACK_2026-11-11.md (PR #123) and the supervisor's reply of 2026-11-11: validation TEA held out; "
                 "tolerances set by us; rule for disagreeing builds fixed in advance; PDH first, then methanation, then NH3/MeOH blind tests."),
    "task": ("runner.py --build pdh: from the reaction name the agent searches, screens, extracts, chooses mechanism/kinetics/reactor/"
             "flowsheet, sources parameters, writes model.py (contract in build_mode.py), passes check_model, runs the ranking analysis, writes the report."),
    "agent": {"model": "gpt-5.5", "route": "API-YES credential 邪修gpt", "extraction_model": "gpt-5.5", "max_turns": 90,
              "n_target_papers": 12, "n_max_downloads": 20,
              "workspace": "D:/agent_runs/<run> (outside the repository); scripts restricted to relative paths"},
    "not_visible_to_the_agent": ["agent/new_reactions/plant_models.py, plant_framework.py, configs/*, params*.json, SOURCES.md, results/*",
                                 "auto_agent/holdout/*", "the NCE repository and its PRs (url fragments audited)"],
    "builds": ("3 independent builds (separate workspaces, no shared files); a build that fails check_model at finish or whose holdout "
               "audit finds a leak is invalid and replaced by a new build; every replacement is reported"),
    "validation": ("evaluate_builds.py against holdout/pdh.json targets (propane t/t +-5 %, purchased energy GJ/t +-35 %, capital per "
                   "annual t -30/+50 %); pass/partial/fail as in pass_rule; total cost and shares reported, not gated"),
    "agreement_rule": {
        "per_conclusion": ("largest cost item, controlling catalyst property, cheapest catalyst on the common record set (the 59 PR #122 "
                           "PDH records): robust = 3/3 agree, majority = 2/3, model-dependent = no majority; all three builds reported"),
        "quantitative": ("reference-cost spread max/min - 1 and pairwise Spearman of record costs on the common set; spread <= 20 % and "
                         "every Spearman >= 0.8 is called consistent"),
        "primary_build": "the build with the median reference cost, fixed before the holdout comparison is looked at",
        "selection": "no selection of builds by TEA fit"},
    "ledger": ("stage_ledger.csv (agent and extraction tokens, wall time, USD at gpt-5.5 list price per stage); human_log.csv (every "
               "human intervention with type and minutes; infrastructure fixes listed separately)"),
    "frozen_sha256": {f: hashlib.sha256((A / f).read_bytes()).hexdigest()
                      for f in ["runner.py", "build_mode.py", "full_mode.py", "evaluate_builds.py", "audit_holdout.py", "holdout/pdh.json"]}}
(H / "PREREG_AI_BUILD_PDH.json").write_text(json.dumps(prereg, indent=1, ensure_ascii=False), encoding="utf-8")
print("written pdh.json and PREREG_AI_BUILD_PDH.json")
