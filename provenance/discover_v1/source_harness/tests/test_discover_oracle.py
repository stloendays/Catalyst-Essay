"""Oracle-leakage tests for the DISCOVER benchmark (PHASE E blocking checks 1-2, 2026-09-06).

(1) Stopping rule S1-S4 must depend only on agent-visible evidence (the policy's own computed results + public candidate data).
(2) Policy D's u / g / b / cost terms must come only from the current public state; policies never touch the harness, the manifest,
    the frozen block, results files or future action results.
Static checks read the source; behavioural checks perturb public data and verify the stopping status follows the public state."""
import inspect, json, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
from discover import env as ENV, policies as POL

FORBIDDEN = r"_cfg\b|frozen_regression|activity_order_expected|results\.json|scenarios_registry|GT\b|ground_truth|canonical_run|self\._h\b|env\._h\b|_cfg\["


def _src(fn): return inspect.getsource(fn)


def test_stopping_rule_uses_only_public_state():
    src = _src(ENV.DiscoverEnv.stopping_status) + _src(ENV.DiscoverEnv.current_winner) + _src(ENV.DiscoverEnv.screened_dominated)
    assert not re.search(FORBIDDEN, src), re.search(FORBIDDEN, src)
    # every attribute referenced is a public-state container or public candidate data
    attrs = set(re.findall(r"self\.(\w+)", src))
    allowed = {"optimized", "activity", "candidates", "backward", "reachability", "budget", "screened_dominated", "current_winner", "_price"}
    assert attrs <= allowed, attrs - allowed


def test_policies_never_touch_hidden_state():
    src = (ROOT / "discover/policies.py").read_text(encoding="utf-8")
    assert not re.search(r"env\._h\b|env\._cfg|frozen_regression|activity_order_expected|results\.json|scenarios_registry|ground_truth|canonical", src)
    d = _src(POL.FixedVOIPolicy)
    used = set(re.findall(r"env\.(\w+)", d))
    allowed = {"current_winner", "screened_dominated", "activity", "_price", "candidates", "optimized", "uncertainty_read", "mc", "budget"}
    assert used <= allowed, used - allowed


def test_stop_is_allowed_with_wrong_conclusion_and_penalised_only_by_scorer():
    """The runner lets a policy stop whenever it wants; may_stop is advisory. Here: a policy that optimizes only one expensive candidate."""
    e = ENV.DiscoverEnv(cost_model={"actions": {}}, budget=1e6); e.BUILD_PROCESS_WINDOW({}, "full"); e.COMPUTE_ACTIVITY(e.candidates)
    e.OPTIMIZE_PROCESS("Os", "full"); st = e.stopping_status()
    assert st["S1_winner_identified"] and st["current_winner"] == "Os"           # the environment reports the policy's own (wrong) leader
    assert not st["S2_no_unresolved_candidate"] and "Fe" in st["unresolved_candidates"] and "Ru" in st["unresolved_candidates"]
    e.close()


def test_screening_follows_public_price_and_activity_not_hidden_truth():
    """Perturb the PUBLIC price table: the screening / S2 verdict must follow the perturbed public data."""
    e = ENV.DiscoverEnv(cost_model={"actions": {}}, budget=1e6); e.BUILD_PROCESS_WINDOW({}, "full"); e.COMPUTE_ACTIVITY(e.candidates); e.OPTIMIZE_PROCESS("Fe", "full")
    base_unresolved = set(e.stopping_status()["unresolved_candidates"])
    assert "Co" not in base_unresolved                       # Co: lower activity and higher price than Fe -> screened
    e._price["Co"] = 0.001                                   # make Co publicly cheaper than Fe
    assert "Co" in set(e.stopping_status()["unresolved_candidates"])
    e.close()


def test_anonymous_variant_is_isomorphic_and_mapping_is_scorer_only():
    a = ENV.DiscoverEnv(cost_model={"actions": {}}, budget=1e6, anonymous=True); n = ENV.DiscoverEnv(cost_model={"actions": {}}, budget=1e6)
    assert all(c.startswith("candidate_") for c in a.candidates) and len(a.candidates) == 15
    m = a.identity_mapping()["public_to_real"]
    for pub, real in m.items():
        assert a._EN0[pub] == n._EN0[real] and a._price[pub] == n._price[real] and a._unc[pub] == n._unc[real]
    a.BUILD_PROCESS_WINDOW({}, "full"); n.BUILD_PROCESS_WINDOW({}, "full")
    inv = {v: k for k, v in m.items()}
    ra = a.OPTIMIZE_PROCESS(inv["Fe"], "full"); rn = n.OPTIMIZE_PROCESS("Fe", "full")
    assert ra["cost_USD_t"] == rn["cost_USD_t"] and ra["P_bar"] == rn["P_bar"] and ra["metal"] == inv["Fe"]
    assert not re.search(r"\b(Fe|Ru|Os)\b", json.dumps(a.public_state()) + json.dumps(a.INSPECT_CANDIDATES()))
    a.close(); n.close()
