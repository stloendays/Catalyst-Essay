"""Run without APIs: cfpy agent/new_reactions/auto_agent/physics_gate_validate.py.

Literature windows are the task's declared validation targets, not fitted data.
All diagnostics run before the final assertion so approximation failures remain visible.
"""
from __future__ import annotations

import copy
import json
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import physics_gate
from physics_gate import (SHOMATE, THERMO, species_thermo, CATEGORIES, check_flowsheet, check_physics, equilibrium_conversion,
                          formula_elements, formula_mw, reaction_dH)


def validate():
    pdh = {"C3H8": -1, "C3H6": 1, "H2": 1}
    meth = {"CO2": -1, "H2": -4, "CH4": 1, "H2O": 2}
    ammonia = {"NH3": -2, "N2": 1, "H2": 3}
    rows = []
    for label, nu, key, feed, t, low, high in (
        ("PDH Xeq, 873 K, 1 bar", pdh, "C3H8", {"C3H8": 1}, 873, .43, .55),
        ("PDH Xeq, 823 K, 1 bar", pdh, "C3H8", {"C3H8": 1}, 823, .27, .39),
        ("Methanation Xeq, 573 K, 1 bar", meth, "CO2", {"CO2": .2, "H2": .8}, 573, .93, .99),
        ("Methanation Xeq, 773 K, 1 bar", meth, "CO2", {"CO2": .2, "H2": .8}, 773, .60, .80),
        ("NH3 decomposition Xeq, 673 K, 1 bar", ammonia, "NH3", {"NH3": 1}, 673, .98, 1),
    ):
        value = equilibrium_conversion(nu, key, feed, t, 1)
        with patch.dict(physics_gate.__dict__, SHOMATE={}):
            old = equilibrium_conversion(nu, key, feed, t, 1)
        rows.append((label, value, old, f"[{low:.2f}, {high:.2f}]", low <= value <= high))
    for label, nu, target in (("PDH dH298 (kJ/mol reaction)", pdh, 124),
                               ("Methanation dH298 (kJ/mol reaction)", meth, -165)):
        value = reaction_dH(nu, 298.15) / 1000
        with patch.dict(physics_gate.__dict__, SHOMATE={}):
            old = reaction_dH(nu, 298.15) / 1000
        rows.append((label, value, old, f"{target} +/- 3", abs(value - target) <= 3))
    print(f"{'Quantity':43} {'Shomate':>12} {'Constant Cp':>12} {'Acceptance':>17} {'Result':>7}")
    for label, value, old, window, passed in rows:
        print(f"{label:43} {value:12.6f} {old:12.6f} {window:>17} {'PASS' if passed else 'FAIL':>7}")

    for label, nu, key, feed, t, p in (
        *[(f"Methanation Xeq, {t} K, 20 bar", meth, "CO2", {"CO2": .2, "H2": .8}, t, 20)
          for t in (573, 623, 673)],
        ("PDH Xeq, 873 K, 0.5 bar", pdh, "C3H8", {"C3H8": 1}, 873, .5),
    ):
        value = equilibrium_conversion(nu, key, feed, t, p)
        with patch.dict(physics_gate.__dict__, SHOMATE={}):
            old = equilibrium_conversion(nu, key, feed, t, p)
        print(f"{label:43} {value:12.6f} {old:12.6f} {'information only':>17}")
    print("Constant Cp fallback (no WebBook Shomate): " + ", ".join(s for s in THERMO if s not in SHOMATE))
    # Reference anchors and continuity at every fit transition, including all high ranges.
    for species, (hf, entropy, _) in THERMO.items():
        h, s = species_thermo(species, 298.15)
        assert abs(h-hf*1000) < 1e-8 and abs(s-entropy) < 1e-10
        for _, boundary, _ in SHOMATE.get(species, [])[:-1]:
            left, right = species_thermo(species, boundary-1e-6), species_thermo(species, boundary+1e-6)
            assert abs(left[0]-right[0]) < .01 and abs(left[1]-right[1]) < 1e-4
    print("Thermo anchors and all fit transitions: PASS")

    assert formula_elements("C2H5OH") == {"C": 2, "H": 6, "O": 1}
    assert formula_elements("CH3OH") == {"C": 1, "H": 4, "O": 1}
    mod = SimpleNamespace(REACTION=dict(key="CO2", product="CH4", nu=meth,
                                       MW={s: formula_mw(s) for s in meth}))
    mw = formula_mw
    # One tonne methane with stoichiometric external reactants and water byproduct;
    # reactor per-pass conversion can be smaller because unconverted feed recycles.
    out = {
        "cost_usd_per_t": 100, "parts": dict(feed=60, energy=10, capital=20, catalyst=5, other=5),
        "operating": dict(T_K=573, P_bar=1, per_pass_conversion=.9),
        "balances": dict(key_feed_t_per_t=mw("CO2") / mw("CH4"), energy_GJ_per_t=1,
                         capex_usd=1e6, capacity_t_per_y=1e5),
        "physics": {
            "reactor": dict(T_K=573, P_bar=1, feed_mol_frac={"CO2": .2, "H2": .8},
                            per_pass_conversion=.9, heat_duty_GJ_per_t=-12),
            "boundary": {"in_t_per_t": {"CO2": mw("CO2") / mw("CH4"), "H2": 4 * mw("H2") / mw("CH4")},
                         "out_t_per_t": {"CH4": 1., "H2O": 2 * mw("H2O") / mw("CH4")}},
            "units": [dict(name="reactor", type="reactor", purchased_energy_GJ_per_t=1.,
                           internal_fuel_GJ_per_t=0., capex_usd=1e6)]}}
    flow = {
        "units": [dict(name="reactor", type="reactor", purpose="Catalytic conversion with cooling",
                       inlets=["feed"], outlets=["product"])],
        "streams": [{"name": "feed", "from": "boundary", "to": "reactor", "species": ["CO2", "H2"]},
                    {"name": "product", "from": "reactor", "to": "boundary", "species": ["CH4", "H2O"]}],
        "checklist": {category: {"excluded": "Toy validation fixture only; this category is outside its deliberately minimal scope."}
                      for category in CATEGORIES},
        "diagram": "boundary --> reactor --> boundary"}
    flow["checklist"]["reactor_heat_supply_or_removal"] = {"included": ["reactor"]}
    with tempfile.TemporaryDirectory(prefix="physics-gate-") as tmp:
        path = Path(tmp) / "flowsheet.json"
        path.write_text(json.dumps(flow), encoding="utf-8")
        assert check_flowsheet(path) == [], check_flowsheet(path)
        broken_flow = copy.deepcopy(flow)
        broken_flow["units"][0]["inlets"] = ["unknown"]
        path.write_text(json.dumps(broken_flow), encoding="utf-8")
        assert any("inlets" in f for f in check_flowsheet(path))
    failures = check_physics(mod, out, flow)
    assert failures == [], failures
    print("Toy methanation: PASS (all physics checks)")

    broken = copy.deepcopy(out)
    broken["physics"]["boundary"]["in_t_per_t"]["H2"] *= 2
    bad_nu = SimpleNamespace(REACTION=dict(mod.REACTION, nu=dict(meth, H2=-3)))
    cases = [("element imbalance", bad_nu, broken, "element_balance")]
    broken = copy.deepcopy(out)
    broken["physics"]["reactor"].update(T_K=773, per_pass_conversion=.99)
    cases.append(("conversion above equilibrium", mod, broken, "equilibrium"))
    broken = copy.deepcopy(out)
    broken["physics"]["reactor"]["heat_duty_GJ_per_t"] = 0
    cases.append(("reactor heat duty zero", mod, broken, "reaction_heat"))
    broken = copy.deepcopy(out)
    broken["balances"]["capex_usd"] *= 2
    cases.append(("unit capex mismatch", mod, broken, "accounting"))
    for label, model, broken, expected in cases:
        failures = check_physics(model, broken, flow)
        assert any(expected in f for f in failures), (label, failures)
        print(f"Broken {label}: correctly rejected [{expected}]")

    # Exercise compressor/separation lower bounds independently of the four requested cases.
    extended = copy.deepcopy(out)
    extended["physics"]["units"] += [
        dict(name="compressor", type="compressor", kmol_per_t=100, T_in_K=300,
             P_in_bar=1, P_out_bar=10, power_GJ_per_t=.6, purchased_energy_GJ_per_t=.6,
             internal_fuel_GJ_per_t=0, capex_usd=1e5),
        dict(name="separator", type="separation", feed={"kmol_per_t": 100, "mol_frac": {"CH4": .5, "H2O": .5}},
             outlets=[{"kmol_per_t": 50, "mol_frac": {"CH4": 1}},
                      {"kmol_per_t": 50, "mol_frac": {"H2O": 1}}],
             purchased_energy_GJ_per_t=.2, internal_fuel_GJ_per_t=0, capex_usd=1e5)]
    extended["balances"].update(energy_GJ_per_t=1.8, capex_usd=1.2e6)
    extended_flow = copy.deepcopy(flow)
    extended_flow["units"] = [{"name": u["name"], "type": u["type"]} for u in extended["physics"]["units"]]
    assert check_physics(mod, extended, extended_flow) == []
    for unit, field, value, expected in ((1, "power_GJ_per_t", 0, "isothermal"),
                                         (1, "P_out_bar", 1, "P_out <= P_in"),
                                         (2, "purchased_energy_GJ_per_t", 0, "mixing minimum")):
        broken = copy.deepcopy(extended)
        broken["physics"]["units"][unit][field] = value
        failures = check_physics(mod, broken, extended_flow)
        assert any(expected in f for f in failures), failures
    unknown = copy.deepcopy(out)
    unknown["physics"]["reactor"]["feed_mol_frac"] = {"CO2": .19, "H2": .8, "He": .01}
    assert any("no thermo data for He" in f for f in check_physics(mod, unknown, flow))
    print("Additional checks: PASS (formula parser, flowsheet graph, compressor, separation, missing thermo)")
    validate_build_integration(mod, out, flow)
    from tests_v3.validate_v3 import validate_upper_bounds
    validate_upper_bounds(mod, out, flow)
    outside = [label for label, _, _, _, ok in rows if not ok]
    if outside:
        print("Outside literature windows (fixed thermo retained): " + "; ".join(outside), flush=True)
    assert not outside, "Shomate literature validation failed: " + "; ".join(outside)


def validate_build_integration(model, out, flow):
    """Exercise only the mixin, never instantiate runner.Run (which probes paid APIs)."""
    import build_mode

    class Harness(build_mode.BuildMixin):
        def __init__(self, ws):
            self.ws, self.events, self.tok = ws, [], {}
            self.setup_build("toy", {})
            self.build_version = "V2-flowsheet-physics"  # Explicit legacy workspace compatibility test.

        def log(self, event):
            self.events.append(event)

        def t_write_file(self, path, content):
            (self.ws / path).write_text(content, encoding="utf-8")
            return "delegated write"

        def t_run_python(self, name, code, timeout_s):
            return "delegated run"

        def _load_model(self):
            return SimpleNamespace(REACTION=model.REACTION, reference=lambda: copy.deepcopy(out),
                                   plant_cost=lambda rec: copy.deepcopy(out))

        def _records(self):
            return [dict(paper="toy", idx=i, S=.9, r=1) for i in range(41)]

    with tempfile.TemporaryDirectory(prefix="physics-build-") as tmp:
        h = Harness(Path(tmp))
        assert h.events[0] == {"build_mode_version": "V3-five-layer"}
        assert "draw the flowsheet first" in h.b_write_file("./model.py", "x")
        assert "draw the flowsheet first" in h.b_run_python("x", "open('model.py')", 1)
        assert "flowsheet" in json.loads(h.b_check_model())["failures"]
        assert not json.loads(h.b_submit_flowsheet())["passed"]
        assert h.b_write_file("flowsheet.json", json.dumps(flow)) == "delegated write"
        assert json.loads(h.b_submit_flowsheet())["passed"]
        assert h.flowsheet_ok_time and (h.ws / "flowsheet.md").is_file()
        assert h.b_write_file("model.py", "# test") == "delegated write"
        assert h.b_run_python("x", "open('model.py')", 1) == "delegated run"
        (h.ws / "sources.csv").write_text("parameter,value,unit,source,location,type,low,high\nx,1,-,,,assumption,0,2\n", encoding="utf-8")
        with patch.object(build_mode, "check_physics", wraps=check_physics) as gate:
            result = json.loads(h.b_check_model())
            assert result["passed"], result
            assert result["records_tested"] == 41 and gate.call_count == 41
        with patch.object(build_mode, "check_physics", return_value=["injected failure"] * 7):
            result = json.loads(h.b_check_model())
            assert not result["passed"] and len(result["failures"]["physics"]) == 6
            assert result["failures"]["physics"][-1] == "... 282 more"
        changed = copy.deepcopy(flow)
        changed["diagram"] += "\nrevision"
        h.b_write_file("flowsheet.json", json.dumps(changed))
        assert "flowsheet" in json.loads(h.b_check_model())["failures"]
        assert json.loads(h.b_submit_flowsheet())["passed"]
        assert len([e for e in h.events if "flowsheet_submitted" in e]) == 2
        assert json.loads(h.b_check_model())["passed"]
        changed["checklist"] = {}
        h.b_write_file("flowsheet.json", json.dumps(changed))
        assert not json.loads(h.b_submit_flowsheet())["passed"]
        assert not h.flowsheet_ok_time
    build_mode.METHOD_BUILD.format(reaction="toy", stages="toy", n_target=1, n_max=2, max_turns=3)
    print("Build integration: PASS (guards, submission/resubmission, version/hash logs, reference + 40 records, 5-sample truncation, prompt)")


if __name__ == "__main__":
    validate()
