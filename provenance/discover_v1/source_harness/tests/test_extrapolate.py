import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "agent"))
import extrapolate as X
from reaction_case import validate, strip_for_agent

NH3 = "cases/reaction_cases/nh3_final_1.0.json"; MEOH = "cases/reaction_cases/meoh_d01_v3.json"


def test_anchor_cases_validate_and_strip():
    for p in (NH3, MEOH):
        c = json.loads((ROOT / p).read_text(encoding="utf-8")); assert validate(c) == []
        assert "pathway_hints" in c and "pathway_hints" not in strip_for_agent(c)
        assert "pathway_hints" not in X.INSPECT_REACTION_CASE(p)


def test_causal_graph_signals_separate_the_anchors():
    n = X.BUILD_CAUSAL_GRAPH(NH3)["signals"]; m = X.BUILD_CAUSAL_GRAPH(MEOH)["signals"]
    assert n["selectivity_driven_modules"] == [] and "metal_cost" in n["activity_driven_modules"] and not n["inerts_accumulate_with_purge"]
    assert set(m["selectivity_driven_modules"]) >= {"H2_feed", "CO2_feed"} and m["inerts_accumulate_with_purge"]
    assert n["catalyst_specific_cost_share"] > m["catalyst_specific_cost_share"]


def test_case_eligibility_rules():
    e = {r["lever"]: r["status"] for r in X.TEST_CASE_LEVER_ELIGIBILITY(NH3, [{"lever": "engineering.max_catalyst_bed_m3", "direction": "increase"}, {"lever": "electricity_price", "direction": "decrease"},
                                                                                {"lever": "metal_cost", "direction": "increase"}, {"lever": "E_N (improve activity)", "direction": "decrease"}])["results"]}
    assert e["engineering.max_catalyst_bed_m3"] == "inactive_constraint" and e["electricity_price"] == "common_mode_external" and e["metal_cost"] == "eligible" and e["E_N_eV"] == "eligible"
    e = {r["lever"]: r["status"] for r in X.TEST_CASE_LEVER_ELIGIBILITY(MEOH, [{"lever": "P_bar", "direction": "increase"}, {"lever": "direct_OPEX_residual", "direction": "decrease"}, {"lever": "S_CH4", "direction": "decrease"}])["results"]}
    assert e["P_bar"] == "inactive_constraint" and e["direct_OPEX_residual"] == "out_of_scope" and e["S_CH4"] == "eligible"


def test_fuzzy_name_resolution():
    known = ["metal_cost", "engineering.max_catalyst_bed_m3", "E_N_eV", "P_bar", "P_optimum"]
    assert X._resolve_name("bed cap", known) == "engineering.max_catalyst_bed_m3"
    assert X._resolve_name("E_N (improve activity)", known) == "E_N_eV"
    assert X._resolve_name("operating_pressure (P_optimum)", known) == "P_optimum"
    assert X._resolve_name("something unrelated", known) == "something unrelated"


def test_benchmark_cases_are_closed_book():
    gt = json.loads((ROOT / "benchmark/extrapolation_v1/ground_truth.json").read_text(encoding="utf-8"))
    for cid in gt["cases"]:
        c = json.loads((ROOT / f"benchmark/extrapolation_v1/cases/{cid}.json").read_text(encoding="utf-8"))
        assert "pathway_hints" not in c and "construction" not in c and validate(c) == []
        txt = json.dumps(c).lower(); assert "ammonia" not in txt and "methanol" not in txt and "nh3" not in txt.replace("nh3-final", "")
