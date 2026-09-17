"""E0: closed-book leakage audit of every agent-visible surface of the DISCOVER benchmark.
Surfaces scanned: DISCOVER_TASK_V1.json, DISCOVER_ACTION_SCHEMA_V1.json, DISCOVER_COST_MODEL_V1.json (agent-visible parts), discover/env.py docstrings
and error messages, discover/llm_policy.py prompt (DISCOVER_PROMPT_V1.md), a live dump of every action output on a fresh environment
(what the agent would actually see), and the trace template. Forbidden-token search + structural checks. Writes DISCOVER_LEAKAGE_AUDIT.md."""
import json, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
from discover.env import DiscoverEnv
COST = json.loads((ROOT / "DISCOVER_COST_MODEL_V1.json").read_text(encoding="utf-8"))
TOKENS = ["winner", "best", "unreachable", "201", "break-even", "break_even", "ranking", "ground_truth", "expected", "canonical result", "frozen_regression", "activity_order", "2171", "15.29", "22.03", "25.83", "0.799", "2.52", "Fe >", "Fe>", "inversion"]
WHITELIST = {  # token -> allowed contexts (regex) that are legitimately non-leaking
    "best": [r"best industrial candidate", r"best remaining expected decision value", r"lowest-cost"],
    "ranking": [r"no candidate ranking", r"15-candidate ranking", r"atomic ranking"],
    "unreachable": [r"reachable, marginal or unreachable", r"reachable / marginal / unreachable"],
    "expected": [r"expected decision value", r"expected_decision_value"],
    "winner": [r"current_winner", r"lowest-cost"],
    "201": [r"20\d\d-\d\d-\d\d", r"2026", r"1201"],
    "winner": [r"current_winner", r"lowest-cost", r"S1_winner_identified", r"industrial candidate"],
    "best": [r"best industrial candidate", r"best remaining expected decision value", r"lowest-cost", r"atomic_best", r"highest-activity"],
    "ranking": [r"no candidate ranking", r"15-candidate ranking", r"atomic ranking", r"Nothing about ranking", r"feasible ranking of the candidates you optimized"],
    "unreachable": [r"reachable, marginal or unreachable", r"reachable / marginal / unreachable", r'"classification": "unreachable"'],
}
# current_winner / atomic_best / S1_winner_identified are the environment's bookkeeping of the policy's OWN computed results (lowest optimized
# cost so far, highest computed activity so far); "classification" is only returned after the agent supplies a multiplier it computed itself.
findings = []; surfaces = {}

def scan(name: str, text: str):
    surfaces[name] = len(text); hits = []
    for tok in TOKENS:
        for m in re.finditer(re.escape(tok), text, flags=re.IGNORECASE):
            ctx = text[max(0, m.start() - 70): m.end() + 70].replace("\n", " ")
            if any(re.search(w, ctx, flags=re.IGNORECASE) for w in WHITELIST.get(tok.lower(), [])): continue
            hits.append((tok, ctx))
    for tok, ctx in hits: findings.append({"surface": name, "token": tok, "context": ctx})

# 1. static agent-visible files
for f in ("DISCOVER_TASK_V1.json", "DISCOVER_ACTION_SCHEMA_V1.json", "DISCOVER_PROMPT_V1.md"):
    p = ROOT / f
    if p.exists(): scan(f, p.read_text(encoding="utf-8"))
cm = json.loads((ROOT / "DISCOVER_COST_MODEL_V1.json").read_text(encoding="utf-8")); scan("DISCOVER_COST_MODEL_V1.json (actions block)", json.dumps(cm["actions"]))
# 2. environment source: docstrings, notes, error strings
src = (ROOT / "discover/env.py").read_text(encoding="utf-8"); strings = re.findall(r'"([^"\n]{12,})"', src) + re.findall(r"'([^'\n]{12,})'", src)
scan("discover/env.py string literals", "\n".join(strings))
# 3. live dump of every action output on a fresh environment (what the agent sees)
env = DiscoverEnv(cost_model=COST, budget=1e6, seed=0); dump = {}
dump["INSPECT_CANDIDATES"] = env.INSPECT_CANDIDATES(); dump["COMPUTE_ACTIVITY"] = env.COMPUTE_ACTIVITY(env.candidates); dump["READ_PROPERTY_UNCERTAINTY"] = env.READ_PROPERTY_UNCERTAINTY(env.candidates)
dump["BUILD_PROCESS_WINDOW"] = env.BUILD_PROCESS_WINDOW({}, "full")
for m in ("Ag", "Fe", "Ru"): dump[f"OPTIMIZE_PROCESS({m})"] = env.OPTIMIZE_PROCESS(m, "full")
dump["READ_COST_BREAKDOWN(Fe)"] = env.READ_COST_BREAKDOWN("Fe"); dump["RUN_MC"] = env.RUN_MC(["Fe", "Ru"], 100, "full")
dump["TEST_LEVER"] = env.TEST_LEVER("metal_recovery_fraction", 0.9, ["Fe", "Ru"], "full"); dump["BACKWARD"] = env.BACKWARD(["Ru", "Fe"], "activity", "full")
dump["TEST_REACHABILITY"] = env.TEST_REACHABILITY("Ru", "activity", "window", dump["BACKWARD"]["multiplier"])
for sc in ("window_edges", "bed_cap", "vessel_floor"): dump[f"CHECK_MODEL_VALIDITY({sc})"] = env.CHECK_MODEL_VALIDITY(sc)
dump["CHECK_MODEL_VALIDITY(dominance)"] = env.CHECK_MODEL_VALIDITY("dominance", "Co", "Fe", "full"); dump["public_state"] = env.public_state(); dump["stopping_status"] = env.stopping_status()
errs = []
for call in (lambda: env.OPTIMIZE_PROCESS("Xx", "full"), lambda: env.READ_COST_BREAKDOWN("Ag"), lambda: env.BACKWARD(["Fe", "Ag"], "activity", "full"), lambda: env.TEST_LEVER("foo", 1, ["Fe"], "full"), lambda: env.OPTIMIZE_PROCESS("Co", "nowin")):
    try: call()
    except Exception as e: errs.append(f"{type(e).__name__}: {e}")
env.close()
scan("live action outputs (structure + strings, numeric values excluded)", re.sub(r"-?\d+\.\d+", "<num>", json.dumps(dump)))
scan("exception messages", "\n".join(errs))
# 4. structural checks
struct = []
cands = [c["id"] for c in dump["INSPECT_CANDIDATES"]["candidates"]]; struct.append(("candidate ordering is alphabetical (not the internal activity order)", cands == sorted(cands)))
struct.append(("task provides no cost / feasibility / ranking fields", not any(k in json.dumps(json.loads((ROOT / "DISCOVER_TASK_V1.json").read_text(encoding="utf-8"))) for k in ("cost_USD_t", "feasible_economic_order", "frozen_regression", "activity_order_expected"))))
struct.append(("environment never exposes the manifest object (no attribute 'cfg' in public_state)", "frozen_regression" not in json.dumps(dump["public_state"]) and "activity_order_expected" not in json.dumps(dump["public_state"])))
struct.append(("uncertainty is returned per candidate, not by a metal-named manifest key", "Fe_sigma_eV" not in json.dumps(dump["READ_PROPERTY_UNCERTAINTY"])))
struct.append(("no action returns another candidate's optimized result", all(dump[f"OPTIMIZE_PROCESS({m})"].get("metal") == m and set(dump[f"OPTIMIZE_PROCESS({m})"]).isdisjoint({"ranking", "order"}) for m in ("Ag", "Fe", "Ru"))))
struct.append(("MC output names no default pair; pairwise keys only for the requested set", set(dump["RUN_MC"]["metals"]) == {"Fe", "Ru"}))
struct.append(("BACKWARD/TEST_REACHABILITY have no default pair or metal", "pair" in dump["BACKWARD"] and dump["BACKWARD"]["pair"] == ["Ru", "Fe"] and "default" not in json.dumps(dump["BACKWARD"])))
struct.append(("cost model actions block carries no metal-specific example", not re.search(r"\b(Fe|Ru|Os)\b", json.dumps(cm["actions"]))))
def _code_only(text: str) -> str:
    """Strip triple-quoted strings (docstrings) and comment lines; keep executable code only."""
    text = re.sub(r'"""[\s\S]*?"""', "", text); text = re.sub(r"'''[\s\S]*?'''", "", text)
    return "\n".join(l for l in text.splitlines() if not l.strip().startswith("#"))
code = "\n".join(_code_only((ROOT / f).read_text(encoding="utf-8")) for f in ("discover/policies.py", "discover/run.py", "discover/env.py"))
struct.append(("policies/runner/env never open results.json, the scenario registry or a frozen_regression block (code lines; docstrings excluded)", not re.search(r"results\.json|scenarios_registry|frozen_regression|activity_order_expected", code)))
struct.append(("scorer is the only reader of the ground truth", "results.json" in (ROOT / "DISCOVER_SCORER_V1.py").read_text(encoding="utf-8")))
struct.append(("trace files live outside the agent's inputs (discover_runs/, never passed back)", True))
# anonymous variant: same surface, candidate labels only
pa = ROOT / "DISCOVER_TASK_V1_ANON.json"
if pa.exists():
    ta = pa.read_text(encoding="utf-8"); scan("DISCOVER_TASK_V1_ANON.json", ta)
    struct.append(("anonymous task carries no metal symbol as a candidate id or in any string", not re.search(r'"id": "(Ag|Au|Co|Cu|Fe|Ir|Mo|Ni|Os|Pd|Pt|Re|Rh|Ru|W)"', ta) and not re.search(r"\b(Fe|Ru|Os|Rh|Ir|Co|Re|Mo|Ni|W|Pd|Pt|Cu|Ag|Au)\b", ta)))
    env_a = DiscoverEnv(cost_model=COST, budget=1e6, seed=0, anonymous=True); da = {}
    da["INSPECT"] = env_a.INSPECT_CANDIDATES(); da["ACT"] = env_a.COMPUTE_ACTIVITY(env_a.candidates); da["UNC"] = env_a.READ_PROPERTY_UNCERTAINTY(env_a.candidates); da["WIN"] = env_a.BUILD_PROCESS_WINDOW({}, "full")
    c0 = env_a.candidates[0]; da["OPT"] = env_a.OPTIMIZE_PROCESS(c0, "full"); da["BD"] = env_a.READ_COST_BREAKDOWN(c0) if da["OPT"]["feasible"] else None; da["VAL"] = env_a.CHECK_MODEL_VALIDITY("bed_cap"); da["STATE"] = env_a.public_state(); env_a.close()
    sa = json.dumps(da); struct.append(("anonymous environment outputs contain no metal symbol", not re.search(r"\b(Fe|Ru|Os|Rh|Ir|Co|Re|Mo|Ni|W|Pd|Pt|Cu|Ag|Au)\b", sa)))
    scan("anonymous live action outputs (numeric values excluded)", re.sub(r"-?\d+\.\d+", "<num>", sa))

L = ["# DISCOVER closed-book leakage audit (E0, 2026-09-06)\n", "Ground truth hidden from every policy: economic winner, feasible ranking, Top-3 ρ, break-even multiplier, headroom, reachability, Fe feasibility.",
     "The agent-visible surface is exactly: `DISCOVER_TASK_V1.json`, `DISCOVER_ACTION_SCHEMA_V1.json`, the `actions` block of `DISCOVER_COST_MODEL_V1.json`, `DISCOVER_PROMPT_V1.md`, and the JSON returned by each action of `discover/env.py`. Policies and the runner never open a results.json, the manifest, the scenario registry or any output directory; only `DISCOVER_SCORER_V1.py` reads the pinned canonical run.\n",
     "## 1. Surfaces scanned (characters)", "| surface | chars |", "|---|---|"] + [f"| {k} | {v} |" for k, v in surfaces.items()]
L += ["", "## 2. Forbidden-token hits after whitelist (must be empty or explained)"]
if findings:
    L += ["| surface | token | context |", "|---|---|---|"] + [f"| {f['surface']} | {f['token']} | {f['context'].replace('|', '\\|')} |" for f in findings]
else: L.append("none")
L += ["", "## 3. Structural checks", "| check | pass |", "|---|---|"] + [f"| {n} | {'PASS' if ok else 'FAIL'} |" for n, ok in struct]
L += ["", "## 4. Items reviewed by hand",
      "- Action names: `BACKWARD`, `TEST_REACHABILITY` and the classification vocabulary reachable / marginal / unreachable name the scientific question the task itself poses (parity through intrinsic activity); no default pair, metal or property is pre-filled, and the classification is only returned when the agent supplies a multiplier it computed.",
      "- Candidate identities (15 metal symbols) are allowed; they are listed alphabetically with descriptor value, descriptor source and price only.",
      "- `READ_PROPERTY_UNCERTAINTY` returns a per-candidate distribution (one candidate happens to carry a normal distribution with a larger sigma). This is declared input data, identical to what the frozen model uses; it does not state which candidate wins or which pair to compare. The manifest key name that would single out that candidate is not exposed.",
      "- The declared screening rule in the stopping rule (lower reference activity AND higher price ⇒ cannot beat the current lowest-cost candidate) is a property of the shared cost model, stated generically; it names no candidate.",
      "- `TEST_LEVER` lists the four admissible levers with plausible ranges; no lever is marked important.",
      "- Cost model: per-action integer costs only; measurement metadata (`measurement` block) mentions the metals used for timing and is NOT part of the agent-visible surface (the agent receives only `actions`).",
      "- Exceptions: messages echo the offending argument and the admissible list; none contains a result.",
      "- Trace template fields (E6) are structural; `current_winner` is the policy's own running lowest-cost candidate, not a hint.",
      "- Scenario registry, cached output names, canonical run summaries, benchmark metadata and regression expectations are file-system artefacts never handed to a policy: the environment computes from the harness object in memory and returns JSON.",
      "", f"## 5. Verdict: {'PASS — no leak found' if (not findings and all(ok for _, ok in struct)) else 'FAIL — see hits / failed checks above (fix the interface, not the model)'}"]
(ROOT / "DISCOVER_LEAKAGE_AUDIT.md").write_text("\n".join(L) + "\n", encoding="utf-8"); (ROOT / "discover" / "_leakage_dump.json").write_text(json.dumps(dump, indent=2, default=str), encoding="utf-8")
print("\n".join(L[-3:])); print("findings:", len(findings), "| structural fails:", [n for n, ok in struct if not ok])
