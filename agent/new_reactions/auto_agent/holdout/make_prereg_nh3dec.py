"""Writes holdout/PREREG_AI_BUILD_NH3DEC.json (run after nh3dec.json, before the first ammonia-decomposition AI build)."""
import hashlib
import json
from datetime import datetime
from pathlib import Path

H = Path(__file__).resolve().parent
A = H.parent
ROUTE = A.parents[1] / "extraction" / "llm_route.py"
FROZEN = ["runner.py", "build_mode.py", "physics_gate.py", "basis_gate.py", "atomic_layer.py", "mkm_solver.py", "full_mode.py",
          "evaluate_builds.py", "audit_holdout.py", "holdout/nh3dec.json"]

prereg = {
    "id": "AI-BUILD-NH3DEC-V3", "written": datetime.now().isoformat(timespec="seconds"),
    "guidance": ("docs/SUPERVISOR_FEEDBACK_2026-11-11.md (AI takes over the modeling, validation TEA held out, disagreement rule fixed in "
                 "advance); user 2026-11-13: build mode V3 after the five-layer design (Notion 40), model gpt-5.6-sol via API-YES "
                 "credential GPT-personal, and ammonia decomposition as the new reaction that covers the three optima (atomic, laboratory, "
                 "industrial) of the NCE paper."),
    "build_mode": ("V3-five-layer (docs/V3_FIVE_LAYER_DESIGN.md): design basis with evidence (basis.json), PARAMS contract, decisions log, "
                   "physics gate with V2 lower bounds plus upper bounds and capital plausibility, evidence debt from assumption sensitivity "
                   "(10 % of cost or energy) that must be resolved before finish, one independent critic (fresh context, artefacts only, "
                   "at most 2 rounds); --atomic: literature-built atomic.py on the generic mkm_solver.py, check_atomic, run_three_optima. "
                   "V3 was designed after the CO2-methanation holdout results were seen, so methanation is not evidence for V3; "
                   "ammonia decomposition is its first test."),
    "task": "runner.py <run> 'ammonia decomposition to hydrogen (2 NH3 -> N2 + 3 H2)' --build nh3dec --atomic",
    "agent": {"model": "gpt-5.6-sol", "route": "API-YES credential GPT-personal (fallback: credential 邪修gpt, then other routes)",
              "extraction_model": "gpt-5.6-sol", "critic_model": "gpt-5.6-sol (separate call, fresh context)", "max_turns": 140,
              "n_target_papers": 12, "n_max_downloads": 20,
              "workspace": "D:/agent_runs/<run> (outside the repository); scripts restricted to relative paths"},
    "not_visible_to_the_agent": [
        "agent/new_reactions/plant_models.py, plant_framework.py, configs/* (incl. nh3dec_ours.json), params*.json, SOURCES.md, results/*",
        "the NCE ammonia harness (provenance/*/source_harness, analysis/*): its scaling fits, descriptor values and optimum",
        "auto_agent/holdout/*", "the NCE repository and its PRs (url fragments audited)"],
    "builds": ("3 independent builds nh3dec_b1..b3 (separate workspaces); a build that fails check_model or check_atomic at finish, or whose "
               "holdout audit finds a leak, is invalid and replaced; every replacement is reported"),
    "validation": {
        "plant": ("evaluate_builds.py against holdout/nh3dec.json: NH3 incl. fuel 7.28 t/t H2 +-12 %, fired duty + primary electricity "
                  "45.6 GJ/t +-35 %, capital per annual t H2 on the Ishimoto scale curve -30/+50 %; pass = 3/3, partial = 2/3 and none "
                  "beyond twice the tolerance, fail otherwise"),
        "atomic": ("optimum N binding weaker than the build's own Ru value by 0.33 +- 0.20 eV at 850 K, 0.99/0.0075/0.0025 bar "
                   "NH3/H2/N2 (Hansgen 2010); within / outside, reported separately"),
        "hidden_reference_report_only": ("hand-built plant model configs/nh3dec_ours.json (Spearman on common records); NCE harness "
                                         "reverse-direction volcano (argmax and Spearman; method still being checked, not gated)")},
    "agreement_rule": {
        "per_conclusion": ("largest cost item, controlling catalyst property, cheapest catalyst on the common record set (records present in "
                           "all three builds), atomic optimum descriptor relative to Ru (agree if within 0.2 eV), laboratory optimum, "
                           "industrial optimum: robust = 3/3, majority = 2/3, model-dependent = no majority; all three builds reported"),
        "quantitative": "reference-cost spread max/min - 1 <= 20 % and every pairwise Spearman of record costs >= 0.8 is called consistent",
        "primary_build": "the build with the median reference cost, fixed before the holdout comparison is looked at",
        "selection": "no selection of builds by TEA fit"},
    "ledger": "stage_ledger.csv per build (incl. critic tokens); human_log.csv (every human intervention with type and minutes)",
    "frozen_sha256": {**{f: hashlib.sha256((A / f).read_bytes()).hexdigest() for f in FROZEN},
                      "../../extraction/llm_route.py": hashlib.sha256(ROUTE.read_bytes()).hexdigest()}}
(H / "PREREG_AI_BUILD_NH3DEC.json").write_text(json.dumps(prereg, indent=1, ensure_ascii=False), encoding="utf-8")
print("written PREREG_AI_BUILD_NH3DEC.json")
