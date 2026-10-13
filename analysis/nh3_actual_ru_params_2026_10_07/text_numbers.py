"""Text numbers of the actual-Ru ammonia analysis, NH3-FINAL-1.1 -> NH3-FINAL-1.2: writes nh3_1_2/TEXT_NUMBERS.md.

Reads committed outputs only (no harness, standard library only). For each model:
  * this folder's summary.json and fig3d_readings.csv (1.1) or nh3_1_2/ (1.2), written by run_params.py;
  * figures/composite/fig2/[nh3_1_2/]fig2_ru_bed_sensitivity.csv and fig2_ru_actual_cost_points.csv
    (fig2_ru_actual_cost.py; the 490 kg m-3 markers and the own-bed increments of the text come from there);
  * analysis/nh3_mc_ru_actual_2026_10_06/[nh3_1_2/]summary.json (run_mc_ru_actual.py; its A_bed is A_comm of set R_all).
The overlaps are asserted equal first (to 1e-9). The 1.1 column equals the numbers of the current text (docs/ at the
branch point of the 1.2 port, 2026-10-13).

    python text_numbers.py
"""
import csv
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
FIG2 = REPO / "figures" / "composite" / "fig2"
MC = REPO / "analysis" / "nh3_mc_ru_actual_2026_10_06"
U_MIN = 11.0
R_LO, R_HI = 0.90, 0.9555
W_HEAD = 0.08
TOL = 1e-9


def rows(p):
    return list(csv.DictReader(open(p, encoding="utf-8")))


def load(v):
    sub = "" if v == "1.1" else "nh3_1_2"
    return dict(S=json.loads((HERE / sub / "summary.json").read_text(encoding="utf-8")),
                rd=rows(HERE / sub / "fig3d_readings.csv"),
                bed=rows(FIG2 / sub / "fig2_ru_bed_sensitivity.csv"),
                pts={x["key"]: x for x in rows(FIG2 / sub / "fig2_ru_actual_cost_points.csv")},
                mc=json.loads((MC / sub / "summary.json").read_text(encoding="utf-8")))


def sg(x, d=2):
    return ("−" if x < 0 else "+") + f"{abs(x):.{d}f}"


def rg(a, b, d=2):
    return f"{a:.{d}f}–{b:.{d}f}"


def numbers(v):
    D = load(v)
    S, rd, bed, pts, mcp = D["S"], D["rd"], D["bed"], D["pts"], D["mc"]
    fe, fe_k = S["fixed"]["Fe_main_loop"], S["fixed"]["Fe_KAAP_loop"]
    key = {("main", R_LO): "supp_rec90", ("main", R_HI): "supp_rec_hi", ("KAAP", R_LO): "kaap90", ("KAAP", R_HI): "kaap_hi"}

    # overlaps: this analysis against the Fig. 2 tables and the actual-Ru Monte Carlo of the same model
    assert abs(float(pts["fe_kaap"]["cost"]) - fe_k) < TOL and abs(float(pts["supp_rec90"]["Fe_same_loop_cost"]) - fe) < TOL
    n = 0
    for x in rd:
        if x["set"] == "benchmark_bed" and (x["loop"], float(x["recovery"])) in key:
            assert abs(float(pts[key[(x["loop"], float(x["recovery"]))]]["cost"]) - float(x["cost"])) < TOL
            n += 1
        if x["set"] == "R_all":
            c = next(c for c in bed if c["key"] == key[(x["loop"], float(x["recovery"]))]
                     and float(c["w_Ru"]) == float(x["w_Ru"]) and float(c["rho_bed_kg_m3"]) == float(x["rho_bed_kg_m3"]))
            assert abs(float(c["cost"]) - float(x["cost"])) < TOL
            n += 1
    assert n == 28, n
    mc = S["monte_carlo"]["R_all"]
    for mine, theirs in (("A", "A"), ("A_comm", "A_bed"), ("B", "B"), ("B0", "B0")):
        assert mc[mine]["P_Fe_cheaper"] == mcp[theirs]["P_Fe_cheaper"], (v, mine)

    out = {}
    b = S["benchmark_bed"]
    br = [b["r90"], b["r95.55"]]
    out["p_eff"] = rg(min(x["main"]["p_eff_USD_kg"] for x in br), max(x["main"]["p_eff_USD_kg"] for x in br), 0) + " USD/kg"
    c = [x["main"]["cost"] for x in br]
    g = [x["main"]["gap_to_Fe"] for x in br]
    out["bench_main"] = f"{rg(min(c), max(c))} USD/t; {sg(min(g))} to {sg(max(g))} vs Fe"
    st = sorted({(float(x["T_C"]), float(x["P_bar"])) for x in rd
                 if x["set"] == "benchmark_bed" and x["loop"] == "main" and float(x["recovery"]) in (R_LO, R_HI)})
    out["bench_state"] = "; ".join(f"{t:.0f} °C, {p:.0f} bar" for t, p in st)
    a = [x["main"]["alpha_star"] for x in br]
    out["bench_alpha"] = rg(min(a), max(a)) + "-fold"
    ck = [x["KAAP"]["cost"] for x in br]
    gk = [x["KAAP"]["gap_to_Fe"] for x in br]
    out["bench_kaap"] = f"{rg(min(ck), max(ck))} USD/t; {sg(min(gk))} to {sg(max(gk))} vs Fe in the loop"
    out["fe"] = f"{fe:.2f} USD/t"
    out["fe_kaap"] = f"{fe_k:.2f} USD/t"
    pstar = b["parity_price_USD_kg"]
    p_ru = float(pts["pure"]["p_eff_USD_kg"])
    out["pstar"] = f"{pstar:.2f} USD/kg"
    out["u_parity"] = " / ".join(f"{p_ru * (1 - r) / pstar:.1f}" for r in (R_HI, R_LO))

    for loop in ("main", "KAAP"):
        h = S["fig3d_own_bed"]["R_all"][loop]
        hw, env = h["at_headline_w"], h["envelope_all_w"]
        ref = fe if loop == "main" else fe_k
        out[f"own_{loop}"] = (f"{rg(*hw['cost'])} USD/t; {sg(hw['gap_to_Fe'][0])} to {sg(hw['gap_to_Fe'][1])} vs Fe"
                              f"{'' if loop == 'main' else ' in the loop'} ({ref:.2f})")
        out[f"own_{loop}_alpha"] = rg(*hw["alpha_star"], d=2 if loop == "main" else 3) + "-fold"
        out[f"env_{loop}"] = rg(*env["cost"]) + " USD/t"
        # corners below Fe at 8 wt%, every bed density of the Fig. 2 table (430, 490, 550)
        cs = [x for x in bed if float(x["w_Ru"]) == W_HEAD and x["key"] in (key[(loop, R_LO)], key[(loop, R_HI)])]
        below = [f"{100 * (R_LO if x['key'] == key[(loop, R_LO)] else R_HI):g}% at {float(x['rho_bed_kg_m3']):.0f} "
                 f"({sg(float(x['gap_to_Fe_reference']), 3)})" for x in cs if float(x["gap_to_Fe_reference"]) < 0]
        near = [f"{100 * (R_LO if x['key'] == key[(loop, R_LO)] else R_HI):g}% at {float(x['rho_bed_kg_m3']):.0f} "
                f"({sg(float(x['gap_to_Fe_reference']), 3)})" for x in cs if 0 <= float(x["gap_to_Fe_reference"]) < 0.02]
        out[f"below_{loop}"] = (f"{len(below)} of {len(cs)}" + (": " + ", ".join(below) if below else "")
                                + ("; within 0.02 above: " + ", ".join(near) if near else ""))
        m490 = [x for x in cs if float(x["rho_bed_kg_m3"]) == 490.0]
        mk = {x["key"]: x for x in m490}
        out[f"marker_{loop}"] = (f"{float(mk[key[(loop, R_LO)]]['cost']):.2f}–{float(mk[key[(loop, R_HI)]]['cost']):.2f} USD/t "
                                 f"(r 90% → 95.55%)")
        if loop == "main":
            al = [float(x["alpha_star_supported_bed"]) for x in m490]
            out["marker_alpha"] = rg(min(al), max(al), 1) + "×"
        dl = [float(x["delta_vs_benchmark_bed"]) for x in cs]
        out[f"delta_{loop}"] = rg(min(dl), max(dl)) + " USD/t"
    d0 = [float(x["delta_vs_benchmark_bed"]) for x in bed if x["key"] == "supported" and float(x["w_Ru"]) == W_HEAD]
    out["delta_none"] = rg(min(d0), max(d0)) + " USD/t"

    def p(name):
        x = mc[name]
        return (f"{100 * x['P_Fe_cheaper']:.1f}% [{100 * x['CI95_Clopper_Pearson'][0]:.1f}, "
                f"{100 * x['CI95_Clopper_Pearson'][1]:.1f}]; median Ru − Fe {sg(x['gap_quantiles_USD_t']['p50'])} USD/t")
    for name in ("A", "A_comm", "B", "B0"):
        out["mc_" + name] = p(name)
    return out


ROWS = [  # key, quantity, where the text uses it
    ("p_eff", "Effective Ru price p(1 − r)/u, u = 11, r = 90–95.55% (input only)", "main l.43; SI l.59"),
    ("bench_main", "Benchmark-bed reading, main loop", "main l.43; SI l.59; Fig. 3d caption"),
    ("bench_state", "… its optimum states (90% and 95.55%)", "SI l.59 (\"450 °C and 195–200 bar\")"),
    ("bench_alpha", "… activity multiple α* for parity", "main l.43; SI l.59; Fig. 3d caption"),
    ("bench_kaap", "Benchmark-bed reading, KAAP loop (90 bar, T_sep −20 °C)", "main l.43; SI l.59; Fig. 3d caption"),
    ("fe", "Fe optimum, main loop", "reference of every main-loop gap"),
    ("fe_kaap", "Fe in the KAAP loop", "main l.43; SI l.59; Fig. 3d caption"),
    ("pstar", "Parity price of the Fig. 2d sweep", "Fig. 3d caption (\"164 US dollars per kilogram\")"),
    ("u_parity", "u needed for parity at r = 95.55% / 90%", "docs/SOURCE_OF_TRUTH (cited from TEXT_NUMBERS.md)"),
    ("own_main", "Own Ru/C bed, 8 wt% Ru, 430–550 kg m⁻³, r 90–95.55%, main loop", "main l.43; SI l.59"),
    ("own_main_alpha", "… α* for parity, main loop", "SI l.59"),
    ("below_main", "… corners below Fe, main loop (8 wt%; 430, 490, 550 kg m⁻³ × 2 recoveries)", "main l.43 (\"stays above it\")"),
    ("own_KAAP", "Own Ru/C bed, 8 wt% Ru, 430–550 kg m⁻³, KAAP loop", "main l.43; SI l.59"),
    ("own_KAAP_alpha", "… α* for parity, KAAP loop", "SI l.59"),
    ("below_KAAP", "… corners below Fe in the KAAP loop (same 6 corners)", "main l.43; SI l.59"),
    ("env_main", "Own bed over 5–10 wt% Ru, main loop", "SI l.59; Fig. 3d caption (bars)"),
    ("env_KAAP", "Own bed over 5–10 wt% Ru, KAAP loop", "SI l.59; Fig. 3d caption (bars)"),
    ("marker_main", "Fig. 3d squares, 8 wt%, 490 kg m⁻³, main loop", "Fig. 3d caption"),
    ("marker_KAAP", "Fig. 3d squares, 8 wt%, 490 kg m⁻³, KAAP loop", "Fig. 3d caption"),
    ("marker_alpha", "Fig. 3d bottom, own-bed α* at the squares", "Fig. 3d caption (\"2.4–3.4×\")"),
    ("delta_none", "Own bed minus benchmark reading, 8 wt%, 430–550, no recovery", "main l.93"),
    ("delta_main", "… with 90–95.55% recovery, main loop", "main l.93"),
    ("delta_KAAP", "… with 90–95.55% recovery, KAAP loop", "main l.93"),
    ("mc_A", "Monte Carlo, benchmark bed at p(1 − r)/u (A): P(Fe cheaper) [95% CI]", "SI l.69; ED Fig. 7a"),
    ("mc_A_comm", "Monte Carlo, commercial Ru/C bed 5–10 wt%, 430–550 kg m⁻³ (A_bed of the text = A_comm here)",
     "main l.43; SI l.69; ED Fig. 7a"),
    ("mc_B", "Monte Carlo, 54 measured Ru catalysts with recovery (B)", "main l.43; SI l.69; ED Fig. 7a"),
    ("mc_B0", "Monte Carlo, measured catalysts without recovery (B0)", "SI l.69; ED Fig. 7a"),
]


def facts():
    """The statements printed below, asserted on the data rather than typed."""
    D = {v: load(v) for v in ("1.1", "1.2")}
    gap = lambda v, k, rho, w=W_HEAD: next(float(x["gap_to_Fe_reference"]) for x in D[v]["bed"]  # noqa: E731
                                           if x["key"] == k and float(x["w_Ru"]) == w and float(x["rho_bed_kg_m3"]) == rho)
    b = {v: D[v]["S"]["benchmark_bed"] for v in D}
    assert b["1.1"]["r90"]["main"]["gap_to_Fe"] > 0 and b["1.1"]["r95.55"]["main"]["gap_to_Fe"] > 0
    assert b["1.2"]["r90"]["main"]["gap_to_Fe"] > 0 > b["1.2"]["r95.55"]["main"]["gap_to_Fe"]
    main_keys, kaap_keys, rhos = ("supp_rec90", "supp_rec_hi"), ("kaap90", "kaap_hi"), (430.0, 490.0, 550.0)
    assert all(gap("1.1", k, r) > 0 for k in main_keys for r in rhos)
    g11 = [gap("1.1", k, r) for k in main_keys for r in rhos]
    assert gap("1.2", "supp_rec_hi", 550.0) < 0 <= gap("1.2", "supp_rec_hi", 490.0) < 0.002
    assert gap("1.2", "supp_rec_hi", 430.0) > 0 and all(gap("1.2", "supp_rec90", r) > 0 for r in rhos)
    assert gap("1.1", "kaap90", 430.0) > 0
    assert all(float(x["gap_to_Fe_reference"]) < 0 for x in D["1.2"]["bed"] if x["key"] in kaap_keys)
    assert all(x["gap_to_Fe"] < 0 for x in (b["1.2"]["r90"]["KAAP"], b["1.2"]["r95.55"]["KAAP"]))
    mc = {v: D[v]["S"]["monte_carlo"]["R_all"] for v in D}
    assert mc["1.1"]["A_comm"]["gap_quantiles_USD_t"]["p50"] > 0 > mc["1.2"]["A_comm"]["gap_quantiles_USD_t"]["p50"]
    assert all(mc[v][n]["P_Fe_cheaper"] > 0.9 for v in D for n in ("B", "B0"))
    return dict(g11=(min(g11), max(g11)), g490=gap("1.2", "supp_rec_hi", 490.0), g550=gap("1.2", "supp_rec_hi", 550.0),
                k430=gap("1.1", "kaap90", 430.0),
                P=(mc["1.1"]["A_comm"]["P_Fe_cheaper"], mc["1.2"]["A_comm"]["P_Fe_cheaper"]))


def main():
    n11, n12 = numbers("1.1"), numbers("1.2")
    F = facts()
    L = ["# Text numbers of the actual-Ru analysis on NH3-FINAL-1.2", "",
         "Written by `text_numbers.py` from the committed outputs of both models (no harness). Literature inputs as in",
         "the current text: u = 11 (Fig. 3d) or log-uniform 11–50 (Monte Carlo), r = 0.90–0.9555, commercial Ru/C at",
         "8 wt% Ru (5–10 wt%), bed density 430–550 kg m⁻³, KAAP loop at 90 bar and T_sep −20 °C. The 1.1 column equals",
         "the numbers printed in `docs/` at the branch point (2026-10-13); line numbers refer to that version",
         "(main = `docs/MANUSCRIPT_MAIN_TEXT.md`, SI = `docs/SUPPLEMENTARY_INFORMATION.md`, Fig. 3d caption =",
         "`docs/MAIN_FIGURE_CAPTIONS.md` l.17, ED Fig. 7a = `figures/extended_data/ED_CAPTIONS.md`).", "",
         "Gaps are Ru − Fe in the same loop. Sources: own-bed rows at 430/550 kg m⁻³, benchmark-bed rows and the",
         "Monte Carlo from `summary.json` / `fig3d_readings.csv` (this analysis, set R_all); the 490 kg m⁻³ markers and",
         "the own-bed increments from `figures/composite/fig2/nh3_1_2/fig2_ru_bed_sensitivity.csv`; every overlap",
         "between the three sources is asserted equal to 1e-9 first.", "",
         "| Quantity | Used in | NH3-FINAL-1.1 | NH3-FINAL-1.2 |", "|---|---|---|---|"]
    for k, q, where in ROWS:
        L.append(f"| {q} | {where} | {n11[k]} | **{n12[k]}** |")
    L += ["", "Statements whose truth changes under 1.2 (each asserted on the data by `facts()`):", "",
          "- Benchmark-bed reading, main loop: below Fe at 95.55% recovery (1.1: above Fe at both ends of the range).",
          f"- Own bed at 8 wt%, main loop: below Fe at 95.55% recovery in the 550 kg m⁻³ bed ({sg(F['g550'], 3)}) and",
          f"  {sg(F['g490'], 4)} USD/t from Fe in the 490 kg m⁻³ bed; above Fe at 90% recovery and at 430 kg m⁻³",
          f"  (1.1: above Fe at every corner, {sg(F['g11'][0])} to {sg(F['g11'][1])}). The main-l.43 clause \"stays",
          "  above it in the high-pressure Fe loop\" therefore no longer holds at the upper recovery.",
          "- Own bed, KAAP loop: below Fe at every recovery, bed density and Ru content in the tables (1.1: above Fe at 90%",
          f"  recovery in the 430 kg m⁻³ bed, {sg(F['k430'], 3)}).",
          f"- Monte Carlo, commercial Ru/C bed: P(Fe cheaper) {F['P'][0]:.3f} → {F['P'][1]:.3f}, and the median Ru − Fe",
          "  gap changes sign (Ru is cheaper in most draws). The measured catalysts (B, B0) keep Fe ahead (> 90%).", ""]
    out = HERE / "nh3_1_2" / "TEXT_NUMBERS.md"
    out.write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
