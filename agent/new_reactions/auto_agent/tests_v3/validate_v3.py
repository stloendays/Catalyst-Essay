"""Offline V3 integration tests. All workspaces are temporary; no runner/API init."""
import copy
import csv
import json
import math
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import build_mode as bm
from basis_gate import check_basis, basis_values
from physics_gate import check_physics, formula_mw, CATEGORIES


def leaf(v):
    return dict(value=v, evidence=dict(type="published", source="https://example.org/toy", location="Table 1", low=None, high=None))


def basis_fixture():
    return dict(battery_limit="Synthetic fixture only: feed to product, no upstream production.",
        capacity_t_per_y=leaf(1e5), operating_hours_per_y=leaf(8000),
        feeds={s: dict(T_K=leaf(300), P_bar=leaf(30), purity_mol_frac=leaf(1)) for s in ("H2", "CO2")},
        product={"CH4": dict(P_bar=leaf(1), purity_mol_frac=leaf(1))}, utilities={}, purchased_preheat_reason=None)


def validate_upper_bounds(mod, out, flow):
    b = basis_fixture()
    assert check_physics(mod, out, flow, b) == []
    with tempfile.TemporaryDirectory(prefix="v3-basis-") as tmp:
        p = Path(tmp)/"basis.json"
        p.write_text(json.dumps(b), encoding="utf-8")
        assert not check_basis(p)
        bad = copy.deepcopy(b)
        bad["feeds"]["H2"]["P_bar"]["evidence"] = dict(type="assumption", low=31, high=40)
        p.write_text(json.dumps(bad), encoding="utf-8")
        assert check_basis(p)
    ext, f = copy.deepcopy(out), copy.deepcopy(flow)
    wmin = 100*1000*8.314462618*300*math.log(60/30)/1e9
    power = 1.5*wmin
    kw = power*1e5/8000/.0036
    comp = dict(name="compressor", type="compressor", kmol_per_t=100, T_in_K=300,
                P_in_bar=30, P_out_bar=60, power_GJ_per_t=power, purchased_energy_GJ_per_t=power,
                internal_fuel_GJ_per_t=0, capex_usd=kw*1000)
    ext["physics"]["units"].append(comp)
    f["units"].append(dict(name="compressor", type="compressor"))
    f["streams"][0]["to"] = "compressor"
    ext["balances"]["energy_GJ_per_t"] += power
    ext["balances"]["capex_usd"] += comp["capex_usd"]
    assert check_physics(mod, ext, f, b) == [], check_physics(mod, ext, f, b)
    cases = []
    bad = copy.deepcopy(ext)
    bad["physics"]["units"][-1]["power_GJ_per_t"] = 4*wmin
    bad["physics"]["units"][-1]["purchased_energy_GJ_per_t"] = 4*wmin
    cases.append(("power 4x isothermal", bad, "compressor_upper"))
    bad = copy.deepcopy(ext)
    bad["physics"]["units"][-1]["P_in_bar"] = 1
    cases.append(("boundary inlet 1 vs 30 bar", bad, "boundary_feed_state"))
    bad = copy.deepcopy(ext)
    bad["physics"]["units"][-1]["capex_usd"] = kw*300000
    cases.append(("compressor 300000 USD/kW", bad, "capital_plausibility"))
    bad = copy.deepcopy(ext)
    bad["physics"]["units"][-1]["purchased_energy_GJ_per_t"] = power*4
    cases.append(("purchased primary energy 4x power", bad, "compressor_upper"))
    bad = copy.deepcopy(ext)
    bad["physics"]["units"].append(dict(name="furnace", type="furnace", purchased_energy_GJ_per_t=2,
        internal_fuel_GJ_per_t=0, capex_usd=2*1e5/8000/.0036*500))
    cases.append(("exothermic purchased preheat", bad, "exothermic_preheat"))
    bad = copy.deepcopy(ext)
    bad["physics"]["units"].append(dict(name="regen", type="regenerator", purchased_energy_GJ_per_t=0,
        internal_fuel_GJ_per_t=0, capex_usd=0))
    f_zero = copy.deepcopy(f)
    f_zero["units"].append(dict(name="regen", type="regenerator"))
    cases.append(("zero-duty regenerator without evidence", bad, "zero_duty"))
    print("V3 toy with basis: PASS")
    for label, value, check in cases:
        failures = check_physics(mod, value, f_zero if label.startswith("zero-duty") else f, b)
        assert any(check in s for s in failures), (label, failures)
        print(f"V3 broken {label}: rejected [{check}]")
    ok = copy.deepcopy(b)
    ok["zero_duty_evidence"] = {"regen": dict(type="published", source="https://example.org/toy", location="Table 2", low=None, high=None)}
    assert not any("zero_duty" in x for x in check_physics(mod, cases[-1][1], f_zero, ok))
    print("V3.1 zero-duty regenerator with published evidence: accepted")


class Harness(bm.BuildMixin):
    def __init__(self, ws):
        self.ws, self.tok = ws, dict(agent_in=0, agent_out=0, extract_in=0, extract_out=0)
        self.reaction, self.model = "toy", "stub"
        self.setup_build("toy", {})
    def log(self, event):
        pass
    def _records(self):
        return [dict(paper="toy", idx=i, catalyst="Ni toy", T_K=573, P_bar=1, X=.9, S=1,
                     r=r, y_key=.2, y_cofeed=.8, t_cycle_h=None, components=[["Ni", 10]]) for i, r in enumerate((1., 2., 3.))]
    def _critic_call(self, payload):
        assert set(payload) == {"reaction", "physics", "parts", "flowsheet.json", "basis.json", "sources.csv", "evidence_debt.json"}
        return {"issues": [dict(id="units", severity="major", unit_or_item="toy", issue="Verify units", check_suggested="Inspect unit conversion")]}, 12, 7


def fixtures():
    nu = dict(CO2=-1, H2=-4, CH4=1, H2O=2)
    mw = formula_mw
    reaction = dict(key="CO2", product="CH4", cofeed="H2", nu=nu, MW={s: mw(s) for s in nu})
    out = dict(name="toy", cost_usd_per_t=100, parts=dict(feed=60, energy=10, capital=20, catalyst=5, other=5),
        operating=dict(T_K=573, P_bar=1, per_pass_conversion=.9),
        balances=dict(key_feed_t_per_t=mw("CO2")/mw("CH4"), energy_GJ_per_t=1, capex_usd=1e6, capacity_t_per_y=1e5),
        physics=dict(reactor=dict(T_K=573, P_bar=1, feed_mol_frac=dict(CO2=.2, H2=.8), per_pass_conversion=.9, heat_duty_GJ_per_t=-12),
            boundary=dict(in_t_per_t=dict(CO2=mw("CO2")/mw("CH4"), H2=4*mw("H2")/mw("CH4")), out_t_per_t=dict(CH4=1, H2O=2*mw("H2O")/mw("CH4"))),
            units=[dict(name="reactor", type="reactor", purchased_energy_GJ_per_t=1, internal_fuel_GJ_per_t=0, capex_usd=1e6)]))
    flow = dict(units=[dict(name="reactor", type="reactor", purpose="conversion and cooling", inlets=["feed"], outlets=["product"])],
        streams=[dict(name="feed", **{"from": "boundary", "to": "reactor"}, species=["CO2", "H2"]),
                 dict(name="product", **{"from": "reactor", "to": "boundary"}, species=["CH4", "H2O"])],
        checklist={c: dict(excluded="Synthetic validation fixture with a deliberately minimal process scope.") for c in CATEGORIES}, diagram="boundary -> reactor -> boundary")
    flow["checklist"]["reactor_heat_supply_or_removal"] = dict(included=["reactor"])
    return reaction, out, flow


def validate():
    reaction, out, flow = fixtures()
    with tempfile.TemporaryDirectory(prefix="v3-offline-") as tmp:
        ws = Path(tmp)
        h = Harness(ws)
        b = basis_fixture()
        for name, doc in (("basis.json", b), ("flowsheet.json", flow)):
            (ws/name).write_text(json.dumps(doc), encoding="utf-8")
        assert json.loads(h.b_submit_flowsheet())["passed"]
        params = {k: v["value"] for k, v in basis_values(b).items()}
        params.update(important=10., irrelevant=1.)
        (ws/"sources.csv").write_text("parameter,value,unit,source,location,type,low,high\nimportant,10,USD,,,assumption,0,30\nirrelevant,1,-,,,assumption,0,2\n", encoding="utf-8")
        model = "import copy\nREACTION="+repr(reaction)+"\nPARAMS="+repr(params)+"\nOUT="+repr(out)+"\nREC="+repr(h._records()[0])+"\n"+'''
def reference():
    o=copy.deepcopy(OUT)
    o['parts']['other'] += PARAMS['important']
    o['cost_usd_per_t'] = sum(o['parts'].values())
    o['record']=dict(REC)
    return o
def plant_cost(rec):
    return reference()
'''
        (ws/"model.py").write_text(model, encoding="utf-8")
        for topic in ("mechanism", "kinetics", "reactor", "separation", "boundary"):
            h.b_record_decision(topic, "toy choice", ["toy alternative"], "test fixture", ["assumption"])
        result = json.loads(h.b_check_model())
        assert result["passed"], result
        original_model = (ws/"model.py").read_text(encoding="utf-8")
        (ws/"model.py").write_text(original_model.replace("PARAMS['important']", "10."), encoding="utf-8")
        assert "params" in json.loads(h.b_check_model())["failures"]
        (ws/"model.py").write_text(original_model, encoding="utf-8")
        assert json.loads(h.b_check_model())["passed"]
        print("PARAMS cached/unused assumptions negative control: rejected [params]")
        debt = json.loads(h.b_assess_assumptions())
        assert [x["item"] for x in debt["items"]] == ["important"], debt
        critique = json.loads(h.b_request_critique())
        assert h.tok["critic_in"] == 12 and h.tok["critic_out"] == 7
        assert any("open debt" in s for s in h.build_finish_errors())
        assert any("unanswered major" in s for s in h.build_finish_errors())
        h.b_resolve_debt("important", "kept_as_uncertainty", "The synthetic price range remains uncertain and materially changes the reference cost.", "assumption")
        h.b_respond_critique(critique["issues"][0]["id"], "rejected", "The fixture is intentionally synthetic; conversion was checked.")
        (ws/"report.md").write_text("Uncertainty: important", encoding="utf-8")
        (ws/"analysis.json").write_text("{}", encoding="utf-8")
        assert any("sensitivity" in x for x in h.build_finish_errors())
        sens = json.loads(h.b_run_sensitivity())
        assert sens["parameters"][0]["parameter"] == "important" and sens["parameters"][0]["cost_swing_pct"] > 20, sens
        assert not h.build_finish_errors(), h.build_finish_errors()
        print("V3.1 deterministic run_sensitivity: top item important, finish requires current sensitivity.json: PASS")
        # price table: cited rows pass, self-set prices fail
        import shutil
        shutil.copyfile(Path(bm.__file__).with_name("prices.json"), ws/"prices.json")
        src = (ws/"sources.csv").read_text(encoding="utf-8")
        nl = chr(10)
        (ws/"sources.csv").write_text(src + "h2_price,3.0,USD/kg,prices.json:hydrogen,,price_table,," + nl, encoding="utf-8")
        assert bm.price_failures(ws) == [], bm.price_failures(ws)
        (ws/"sources.csv").write_text(src + "h2_price,5.0,USD/kg,https://example.org,Table 1,published,," + nl, encoding="utf-8")
        assert bm.price_failures(ws) and "prices.json" in bm.price_failures(ws)[0]
        (ws/"sources.csv").write_text(src + "h2_price,2.0,USD/kg,prices.json:hydrogen,,price_table,," + nl, encoding="utf-8")
        assert bm.price_failures(ws)
        (ws/"sources.csv").write_text(src, encoding="utf-8")
        (ws/"prices.json").unlink()
        print("V3.1 price table: cited row accepted; published self-set price and altered table value rejected: PASS")
        h.b_request_critique()
        assert "at most two" in h.b_request_critique()
        print("Dry V3: submit/check PASS; debt exactly important (27.2727% cost swing), irrelevant unchanged; finish blocked before debt/critic responses; resolve+report PASS; critic tokens=24/14, third round refused")
        # Narrowing must be demonstrated by an assessment of edited evidence.
        text = (ws/"sources.csv").read_text(encoding="utf-8").replace("assumption,0,30", "assumption,9,11")
        (ws/"sources.csv").write_text(text, encoding="utf-8")
        assert any("current inputs" in x for x in h.build_finish_errors())
        assert json.loads(h.b_check_model())["passed"]
        assert not json.loads(h.b_assess_assumptions())["items"]
        assert json.loads(h.b_resolve_debt("important", "narrowed", "Range revised using fixture evidence", "https://example.org/toy Table 1"))["status"] == "narrowed"
        print("Debt narrowing: old range [0,30] -> [9,11], no flagged item, narrowed accepted: PASS")
        validate_atomic(h)
    bm.METHOD_BUILD.format(reaction="toy", stages="toy", n_target=1, n_max=2, max_turns=3)


def validate_atomic(h):
    # Generic abstract A2+B->AB network, thermo mapped to real formula aliases
    # H2 + C2H4 -> C2H6 for the fixed thermo gate (no ammonia-specific data).
    reaction, out, flow = fixtures()
    nu = dict(H2=-1, C2H4=-1, C2H6=1)
    reaction = dict(key="C2H4", product="C2H6", cofeed="H2", nu=nu, MW={s: formula_mw(s) for s in nu})
    out["balances"]["key_feed_t_per_t"] = formula_mw("C2H4")/formula_mw("C2H6")
    out["physics"]["reactor"].update(feed_mol_frac=dict(H2=.5, C2H4=.5), heat_duty_GJ_per_t=-6)
    out["physics"]["boundary"] = dict(in_t_per_t={s: formula_mw(s)/formula_mw("C2H6") for s in ("H2", "C2H4")}, out_t_per_t=dict(C2H6=1))
    out["record"] = h._records()[0]
    flow["streams"][0]["species"] = ["H2", "C2H4"]
    flow["streams"][1]["species"] = ["C2H6"]
    b = basis_fixture()
    b["feeds"]["C2H4"] = b["feeds"].pop("CO2")
    b["product"]["C2H6"] = b["product"].pop("CH4")
    (h.ws/"basis.json").write_text(json.dumps(b), encoding="utf-8")
    (h.ws/"flowsheet.json").write_text(json.dumps(flow), encoding="utf-8")
    # Atomic fixture's plant has the SAME overall reaction as atomic.py.
    (h.ws/"model.py").write_text("import copy\nREACTION="+repr(reaction)+"\nOUT="+repr(out)+"\ndef reference(): return copy.deepcopy(OUT)\ndef plant_cost(rec): return reference()\n", encoding="utf-8")
    atomic = '''import math
from physics_gate import species_thermo, R
ATOMIC=dict(descriptor='toy D, eV, arbitrary reference', overall=dict(H2=-1,C2H4=-1,C2H6=1), sources=['https://example.org/toy Table 1'], descriptor_range=[-1,1],site_assumptions='Toy site density and loading held constant',reference_metal='Ni', reference_metal_price_usd_per_kg=10, stronger_binding='more_negative')
DESCRIPTORS=dict(Ni=dict(value=-.5,source='https://example.org/toy',location='Table 1',metal_price_usd_per_kg=10))
def affinity(T,p):
    dg=sum(v*(lambda hs:hs[0]-T*hs[1])(species_thermo(s,T)) for s,v in ATOMIC['overall'].items())
    return dg/(R*T)+sum(v*math.log(max(p.get(s,1e-8),1e-300)) for s,v in ATOMIC['overall'].items())
def net_tof(D,T_K,p_bar):
    return math.exp(-D*D)*(-math.tanh(affinity(T_K,p_bar)))
def logtof(D,T_K,p_bar):
    return math.log10(max(net_tof(D,T_K,p_bar),1e-300))
def record_from_descriptor(D,metal_price_usd_per_kg=None):
    return dict(T_K=573,P_bar=1,X=.9,S=1,r=math.exp(-D*D)*3,y_key=.2,y_cofeed=.8,t_cycle_h=None,components=[['Ni',10]],catalyst='Ni toy',metal_price_usd_per_kg=metal_price_usd_per_kg)
def rate_from_descriptor(D,rec):
    return math.exp(-D*D)*3
'''
    (h.ws/"atomic.py").write_text(atomic, encoding="utf-8")
    h.atomic = True
    checked = json.loads(h.b_check_atomic())
    assert checked["passed"], checked
    original = (h.ws/"atomic.py").read_text(encoding="utf-8")
    (h.ws/"atomic.py").write_text(original.replace("(-math.tanh(affinity(T_K,p_bar)))", "math.tanh(affinity(T_K,p_bar))"), encoding="utf-8")
    assert not json.loads(h.b_check_atomic())["passed"]
    (h.ws/"atomic.py").write_text(original, encoding="utf-8")
    assert json.loads(h.b_check_atomic())["passed"]
    h.b_run_analysis()
    result = json.loads(h.b_run_three_optima())
    for field in ("atomic_optimum", "laboratory_optimum", "industrial_optimum", "lab_to_descriptor", "backward_design", "pairwise_disagreement", "atom_to_plant_attribution"):
        assert field in result
    assert result["atomic_optimum"]["D"] == 0
    assert len(result["lab_to_descriptor"]) == 3
    print("Atomic toy A2+B->AB (formula aliases H2+C2H4->C2H6): check_atomic PASS; D*=0, mapping 3/3; three_optima all 7 sections: PASS")


if __name__ == "__main__":
    validate()
