"""Writes holdout/PREREG_AI_BUILD_NH3DEC_A1.json (evaluation-side amendment, before any NH3-decomposition result) and
holdout/PREREG_BLIND_NH3.json, holdout/PREREG_BLIND_MEOH.json (before the first blind build)."""
import hashlib
import json
from datetime import datetime
from pathlib import Path

H = Path(__file__).resolve().parent
A = H.parent
ROUTE = A.parents[1] / "extraction" / "llm_route.py"
now = datetime.now().isoformat(timespec="seconds")


def sha(files):
    out = {f: hashlib.sha256((A / f).read_bytes()).hexdigest() for f in files}
    out["../../extraction/llm_route.py"] = hashlib.sha256(ROUTE.read_bytes()).hexdigest()
    return out


amend = {
    "id": "AI-BUILD-NH3DEC-V3.1-A1", "written": now, "amends": "PREREG_AI_BUILD_NH3DEC.json",
    "change": ("evaluation side only, written while the three builds were still in search/screening/download and before any of their "
               "output was looked at: evaluate_builds.py accepts an empty target set (blind tests), optional holdout/output paths, and "
               "the report-only hidden atomic reference now also reports a full seven-step MKM next to the quasi-equilibrium reverse "
               "branch (plus a floating-point fix at the grid tail); audit_holdout.py accepts optional paths. Gating code, targets, "
               "tolerances and the pass rule are unchanged."),
    "frozen_sha256": sha(["evaluate_builds.py", "audit_holdout.py"])}
(H / "PREREG_AI_BUILD_NH3DEC_A1.json").write_text(json.dumps(amend, indent=1, ensure_ascii=False), encoding="utf-8")

COMMON = {
    "guidance": ("docs/SUPERVISOR_FEEDBACK_2026-11-11.md sections 5.1 and 6.2 (branch supervisor/2026-11-11-nce-ai-modeling): freeze the "
                 "hand-built models; the agent sees only the reaction, the objective and public evidence; compare costs, operating "
                 "conditions, cost breakdown, lab-vs-plant rankings, bottleneck conclusions, system boundary, key assumptions and "
                 "uncertainty; diagnose differences instead of only reporting whether a ranking matched."),
    "build_mode": "V3.1-five-layer, identical code to AI-BUILD-NH3DEC-V3.1 (model gpt-5.6-sol, critic gpt-5.6-luna, fixed prices.json)",
    "not_visible_to_the_agent": ["the hand-built model code, configs, parameters, reports and rankings (data/meoh/*, analysis/*, "
                                 "provenance/*, agent/nh3_field/*, configs/*)", "auto_agent/holdout/*, blind_eval.py, evaluate_builds.py",
                                 "the paper's repository and derived documents (url fragments and keyword sets in holdout/<rxn>.json)"],
    "builds": "3 independent builds <rxn>_b1..b3; a build failing check_model at finish or with a holdout leak is invalid, replaced and reported",
    "evaluation": ("blind_eval.py <rxn> on the paper's own record set (converted to the contract input; denominators reported): "
                   "lab-vs-plant disagreement counts with the paper's grouping and > 5 % cost-gap rule, paper bootstrap CI, per-group "
                   "agreement with the hand verdicts, record-cost Spearman vs the hand model, reference-plant breakdown and operating point "
                   "vs the hand reference, bottleneck conclusions, rule-based difference diagnosis (boundary / structure / parameters / "
                   "data / numerics), and agreement across the three builds (spread <= 20 %, pairwise Spearman >= 0.8, robust / majority / "
                   "model-dependent per conclusion, median-reference primary build). No TEA gate. No selection of builds by fit."),
    "ledger": "stage_ledger.csv per build (incl. critic tokens); human_log.csv",
}
blind = {
    "nh3": dict(COMMON, id="BLIND-NH3-V3.1", written=now,
                task="runner.py <run> 'ammonia synthesis from N2 and H2 (N2 + 3 H2 -> 2 NH3)' --build nh3 --atomic",
                hand_reference=("NCE ammonia harness 1.2 (provenance/nh3_final_1_2/source_harness, configs/nh3_final_1_2.yaml): 12/44 "
                                "printed-primary groups (8/44 above 5 %); atomic layer: intrinsic order Ru > Os > Fe, strict-scaling "
                                "optimum E_N -1.18 eV; the harness cost is a reduced catalyst-dependent cost (no purchased H2/N2)"),
                frozen_sha256=sha(["runner.py", "build_mode.py", "physics_gate.py", "basis_gate.py", "atomic_layer.py", "mkm_solver.py",
                                   "prices.json", "blind_eval.py", "holdout/nh3.json"])),
    "meoh": dict(COMMON, id="BLIND-MEOH-V3.1", written=now,
                 task="runner.py <run> 'CO2 hydrogenation to methanol (CO2 + 3 H2 -> CH3OH + H2O)' --build meoh",
                 hand_reference=("NCE methanol model (data/meoh/meoh_d01_model.py, meoh_general_model.py): 26/63 with lab conversion "
                                 "held fixed (19/63 above 5 %) and 21/63 with conversion raised to 0.95 X_eq (10/63 above 5 %); both "
                                 "reported"),
                 frozen_sha256=sha(["runner.py", "build_mode.py", "physics_gate.py", "basis_gate.py", "atomic_layer.py", "mkm_solver.py",
                                    "prices.json", "blind_eval.py", "holdout/meoh.json"])),
}
for rx, d in blind.items():
    (H / f"PREREG_BLIND_{rx.upper()}.json").write_text(json.dumps(d, indent=1, ensure_ascii=False), encoding="utf-8")
print("written NH3DEC A1 amendment and blind preregistrations")
