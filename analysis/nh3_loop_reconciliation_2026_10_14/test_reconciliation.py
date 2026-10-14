"""pytest checks of the reconciliation code (fast) and of the committed outputs."""
from __future__ import annotations

import math
from dataclasses import replace

import numpy as np
import pytest

import common
import closed_loop as CL
import economics as E
import kinetic_bridge as KB
import kinetics as K
import staged as S

RNG = np.random.default_rng(20261014)


@pytest.fixture(scope="module")
def cold_record():
    import cold_worker
    return cold_worker.job((90.0, 0.12, -10.0, 0.01, CL.TARGET_TPD))


def test_bases_are_the_93_and_94_price_bases():
    import source_domains as SD
    assert CL.B94 == SD.PRICE
    assert CL.B93 == E.EconomicSettings()
    assert (CL.B94.H2_USD_kg, CL.B94.N2_USD_kg, CL.B94.ru_recovery, CL.B94.metal_rate) == (3.0, 0.06, 0.90, 0.12)
    assert (CL.B93.H2_USD_kg, CL.B93.N2_USD_kg, CL.B93.ru_recovery, CL.B93.metal_rate) == (2.0, 0.10, 0.9555, 0.12)


def test_vectorised_rates_equal_kinetic_bridge():
    for _ in range(40):
        T = RNG.uniform(623.0, 803.0)
        P = RNG.uniform(60.0, 300.0)
        flow = RNG.uniform([0.1, 0.3, 0.0, 0.0, 0.01], [0.3, 0.8, 0.1, 0.05, 0.15])
        for cat, key in (("F", "Fe"), ("R", "Ru")):
            a = float(S.rate_m3(cat, np.array([T]), P, flow[:, None])[0])
            b = KB.rate_m3(key, T, P, flow)
            assert math.isclose(a, b, rel_tol=1e-10, abs_tol=1e-12), (cat, T, P, a, b)


def test_matrix_enthalpy_equals_kinetics_enthalpy():
    n = RNG.uniform(0.0, 2.0, size=(5, 7))
    T = RNG.uniform(600.0, 820.0, size=7)
    ref_h = sum(n[i] * K.enthalpy(s, T) for i, s in enumerate(S.SPECIES))
    ref_cp = sum(n[i] * K.cp(s, T) for i, s in enumerate(S.SPECIES))
    assert np.allclose(S.enthalpy(n, T), ref_h, rtol=1e-12, atol=1e-6)
    assert np.allclose(S.heat_capacity(n, T), ref_cp, rtol=1e-12)


def test_adiabatic_bed_conserves_enthalpy_and_rise_is_industrial(cold_record):
    f = np.asarray(cold_record["feed_kmol_h"]) / 3.6
    xi = 0.2 * cold_record["extent_kmol_h"] / 3.6
    T, n = S.adiabatic_T(f, 0.0, 673.15, np.array([xi]))
    h0 = S.enthalpy((f + S.NU * 0.0)[:, None], np.array([673.15]))[0]
    assert abs(S.enthalpy(n, T)[0] - h0) < 1e-6 * abs(h0)
    y_in = f[4] / f.sum()
    y_out = (f[4] + xi) / (f.sum() - xi)
    rise_per_pct = (T[0] - 673.15) / (100 * (y_out - y_in))
    assert 13.0 < rise_per_pct < 17.0, rise_per_pct          # industrial 14-15 K per 1% NH3


def test_bed_quadrature_converged_and_isothermal_limit(cold_record):
    f = np.asarray(cold_record["feed_kmol_h"]) / 3.6
    xi_tot = cold_record["extent_kmol_h"] / 3.6
    v64, _ = S.bed("R", f, 90.0, 0.0, 0.3 * xi_tot, 683.15)
    x, w = np.polynomial.legendre.leggauss(400)
    keep = (S.GL_X, S.GL_W)
    try:
        S.GL_X, S.GL_W = x, w
        v400, _ = S.bed("R", f, 90.0, 0.0, 0.3 * xi_tot, 683.15)
    finally:
        S.GL_X, S.GL_W = keep
    assert abs(v64 / v400 - 1) < 1e-6
    # tiny extent: adiabatic and isothermal (kinetic_bridge.size_bed) beds coincide
    small = 1e-4 * xi_tot
    va, _ = S.bed("F", f, 90.0, 0.0, small, 683.15)
    vi = KB.size_bed("Fe", 683.15, 90.0, f * 3.6, small * 3.6)["bed_m3"]
    assert abs(va / vi - 1) < 1e-3


def test_pure_designs_reproduce_economics_evaluate(cold_record):
    for e in (CL.B94, CL.B93, replace(CL.B94, metal_rate=0.0)):
        loop = S.loop_terms(cold_record, 90.0, 400.0, e)
        for V_Fe, V_Ru in ((40.0, 0.0), (0.0, 30.0), (25.0, 20.0)):
            d = {"V_Fe": V_Fe, "V_Ru": V_Ru, "V_tot": V_Fe + V_Ru}
            ref = S.mixed_evaluate(V_Fe, V_Ru, 90.0, cold_record, 400.0, e)
            assert abs(S.cost(d, loop, 90.0, e)[0] - ref) < 1e-9
            if V_Ru == 0.0:
                rec = CL.with_heat(cold_record, 400.0)
                assert abs(ref - E.evaluate("Fe", V_Fe, 90.0, rec, e)["decision_relevant_cost_USD_t"]) < 1e-9
            if V_Fe == 0.0:
                rec = CL.with_heat(cold_record, 400.0)
                assert abs(ref - E.evaluate("Ru", V_Ru, 90.0, rec, e)["decision_relevant_cost_USD_t"]) < 1e-9


def test_feed_split_is_an_identity(cold_record):
    rows = [r for r in CL.size_candidates({"s": {"state_id": "s", "P_bar": 90.0, "X": 0.12, "T2_C": -10.0, "purge": 0.01,
                                                 "record": cold_record}}, temps=(425.0,)) if r.get("feasible")]
    assert rows
    for e in CL.BASES.values():
        c = CL.price(rows[0], cold_record, e)
        parts = c["purge_gas_loss"] + c["dissolved_gas_loss"] + c["NH3_in_purge"] + c["feed_cost_decomposition_residual_USD_t"]
        assert abs(parts - c["excess_feed_USD_t"]) < 1e-9
        assert abs(c["feed_cost_decomposition_residual_USD_t"]) < 1e-6


def test_canonical_recycle_rise_changes_only_recycle_compression():
    import canonical as CAN
    h = CAN.build()
    g = CAN.with_recycle_rise(h, 9.2)                # asserts identical state set, X and recycle ratio
    i = int(np.argmin(np.abs(h.state_P - 140.0) + np.abs(h.state_T - 450.0) + np.abs(h.state_Tsep - 30.0)))
    P = h.state_P[i]
    ratio = math.log(P / (P - 9.2)) / math.log(P / (P - 3.0))
    assert math.isclose(g.state_reccomp[i] / h.state_reccomp[i], ratio, rel_tol=1e-12)
    assert np.array_equal(g.state_fresh, h.state_fresh) and np.array_equal(g.state_refrig, h.state_refrig)


# --- committed outputs -----------------------------------------------------------------------------------------------

OUT = common.HERE / "outputs"
needs_outputs = pytest.mark.skipif(not (OUT / "summary.json").exists(), reason="outputs not generated")


@needs_outputs
def test_outputs_gates_pass():
    s = common.load(OUT / "summary.json")
    assert s["T1_gate"] is True
    assert all(s["upstream_gates"].values())
    assert all(s["T3"]["gates"].values())
    t1 = common.load(OUT / "t1.json")
    frozen = {"Fe": 11.515783597, "Ru": 16.632749359, "Os": 19.746544}
    for m, v in frozen.items():
        assert abs(t1["runs"]["3"]["metals"][m]["cost_USD_t"] - v) < 1e-6


@needs_outputs
def test_outputs_t2_consistent_with_94_and_decompositions_close():
    t2 = common.load(OUT / "t2.json")
    up = common.load(OUT / "upstream_93_94.json")
    e100 = next(e for e in t2["per_pressure"] if e["P_bar"] == 100.0)
    # the #94 Ru/C optimum lies on the 100-bar grid; T2 must find it (or something cheaper)
    assert e100["bases"]["B94"]["Ru"]["decision_USD_t"] <= up["u94"]["nominal_selected"]["Ru"]["decision_USD_t"] + 1e-9
    for e in t2["per_pressure"]:
        for b in e["bases"].values():
            if b["terms_Ru_minus_Fe"] is not None:
                t = b["terms_Ru_minus_Fe"]
                s = sum(t[k] for k in ("excess_feed", "utilities", "inventory", "reactor", "compressor_capital", "hot_duty"))
                assert abs(s - b["Ru_minus_Fe"]) < 1e-6


@needs_outputs
def test_outputs_t3_waterfall_closes():
    t3 = common.load(OUT / "t3.json")
    lv = t3["waterfall_levels"]
    keys = list(lv)
    assert abs(lv[keys[0]]["total"] - 1.452) < 1e-3
    assert abs(lv[keys[4]]["total"] - (82.636 - 41.634)) < 2e-3
    assert abs(sum(t3["gap_by_category"].values()) - t3["gap_S4_minus_S0"]) < 1e-6


@needs_outputs
def test_outputs_t4_rows_complete():
    t4 = common.load(OUT / "t4.json")
    assert len(t4["per_rate"]) == 26
    for r in t4["per_rate"]:
        assert r["winner_class"] in ("all-Fe", "Fe-first", "all-Ru/C", "Ru/C-first")
        assert r["winner_V_tot"] <= 90.0 + 1e-9
