"""Audit the current live manuscript against committed scientific sources.

This checker is intentionally section-aware rather than phrase-fragile. It verifies that
current canonical/derived numbers appear in the Results section where they belong,
including the closed strict-scaling x lifecycle reachability result.

The frozen descriptor screen, strict-scaling/lifecycle closure, methanol loop and agent
checks retain their committed sources. The 2026-10-21 manuscript revision uses measured
Fe/Ru/C rate laws inside their fitted ranges, the median disclosed lease rate, the
conversion-raised catalyst-level methanol result, Au lifetime boundaries and external
CO2 methanation. Numerical checks cover the main text, Supplementary Notes, Supplementary Methods
and revised figure captions. Definitions retained in the shortened main-text Methods
are checked there; secondary details are anchored to their specific SI subsection. Standard library only (CI needs no project requirements).

Result lines: PASS and FAIL (exit code 1). Source disagreements remain failures; the text is never edited.

Usage:
  python tools/audit_live_manuscript_truth.py [docs/MANUSCRIPT_MAIN_TEXT.md]
"""
from __future__ import annotations

import csv
import importlib.util
import json
import math
import re
import sys
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")       # the labels carry subscripts; a cp936/gbk console cannot print them
sys.dont_write_bytecode = True  # Auditing must not create runtime files in the source tree.
ROOT = Path(__file__).resolve().parents[1]
TEXT_PATH = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "docs/MANUSCRIPT_MAIN_TEXT.md"
HARNESS_12 = ROOT / "provenance/nh3_final_1_2/source_harness"
RUN = HARNESS_12 / "outputs/nh3_final_1_2_20261013"          # canonical NH3-FINAL-1.2 run
SUP = ROOT / "analysis/supervisor_2026_09_20/nh3_1_2"
V12 = "nh3_1_2"                                             # sub-folder of each ported ammonia analysis

raw_text = TEXT_PATH.read_text(encoding="utf-8")
text = re.sub(r"\s+", " ", raw_text).replace("−", "-")
methods = re.sub(r"\s+", " ", raw_text[raw_text.index("## Methods"):].split("## Working references")[0]).replace("−", "-")


def rows(path):
    with open(ROOT / path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


SI_PATH = ROOT / "docs/SUPPLEMENTARY_INFORMATION.md"
raw_si = SI_PATH.read_text(encoding="utf-8") if SI_PATH.exists() else ""


def _block(raw, i, marker):
    j = raw.find("\n### ", i + len(marker))
    d = raw.find("\n## ", i + len(marker))
    ends = [x for x in (j, d) if x >= 0]
    j = min(ends) if ends else len(raw)
    return re.sub(r"\s+", " ", raw[i:j]).replace("−", "-")


def section(heading):
    """The full results of a section: its Supplementary Note when one has that title (the main text keeps a shorter
    version since the 2026-10-07 compression), otherwise the main-text subsection."""
    m = re.search(r"^### Supplementary Note \d+ \| " + re.escape(heading) + r"[ \t]*$", raw_si, re.M)
    if m:
        return _block(raw_si, m.start(), m.group(0))
    marker = "### " + heading
    return _block(raw_text, raw_text.index(marker), marker)


def main_section(heading):
    marker = "### " + heading
    return _block(raw_text, raw_text.index(marker), marker)


def main_section_h2(heading):
    """A top-level section of the main text (## heading), up to the next ## heading."""
    i = raw_text.index("\n## " + heading + "\n") + 1
    j = raw_text.find("\n## ", i + 3)
    return re.sub(r"\s+", " ", raw_text[i:j if j >= 0 else len(raw_text)]).replace("−", "-")


checks = []


def ok(label, condition, detail=""):
    """Every source disagreement fails the audit; the manuscript is never changed."""
    checks.append((label, bool(condition), detail))


def tokens(label, haystack, *needles):
    missing = [n for n in needles if n not in haystack]
    ok(label, not missing, "source-derived text missing: " + ", ".join(missing) if missing else "")


# Re-anchored checks can retain a secondary number in its precise SI section.
# Each anchor is mandatory: a stale number in main text cannot pass via an SI fallback.
def claim_tokens(label, *anchors):
    missing = []
    for scope, haystack, needles in anchors:
        missing.extend(f"{scope}: {n}" for n in needles if n not in haystack)
    ok(label, not missing, "source-derived text missing: " + "; ".join(missing) if missing else "")


def supplementary_method(heading):
    marker = "### " + heading
    start = raw_si.index("## Supplementary Methods")
    return _block(raw_si, raw_si.index(marker, start), marker)


def _j(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def pc(x, digits=0):
    """A fraction as a percentage number, formatted as the manuscript prints it."""
    return f"{x * 100:.{digits}f}"


def _and(items):
    items = [str(x) for x in items]
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]


def dsum(row, cols):
    """Exact sum of decimal strings as printed in a source table."""
    return sum((Decimal(row[c]) for c in cols), Decimal(0))


def dfmt(x, digits):
    """A printed decimal rounded half up to `digits` decimals, never to more decimals than the source prints."""
    digits = min(digits, max(0, -x.as_tuple().exponent))
    return str(x.quantize(Decimal(1).scaleb(-digits), rounding=ROUND_HALF_UP))


def _quantiles(values, qs):
    """numpy.quantile's default (linear) interpolation; the audit runs without numpy."""
    v = sorted(values)
    out = []
    for q in qs:
        h_ = (len(v) - 1) * q
        lo = int(h_)
        out.append(v[lo] + (v[min(lo + 1, len(v) - 1)] - v[lo]) * (h_ - lo))
    return out


_NUM_WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve"]


def word(n, cap=False):
    """A count as the manuscript spells it ('five', or 'Five' at the start of a sentence)."""
    w = _NUM_WORDS[n]
    return w.capitalize() if cap else w


def ordinal(n):
    return f"{n}{'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


_SUB = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")


def chem(s):
    """A formula as printed: digits that follow an element symbol or a closing bracket become subscripts."""
    return re.sub(r"(?<=[A-Za-z)])\d+", lambda mt: mt.group(0).translate(_SUB), s)


def fold(x):
    """An activity multiple as printed: one decimal below 10, none above."""
    return f"{x:.1f}" if x < 10 else f"{x:.0f}"


def ceil2(x):
    """An upper bound printed with two decimals ('within 0.64')."""
    return f"{math.ceil(x * 100 - 1e-9) / 100:.2f}" if math.isfinite(x) else "(not computable)"


def _yaml_num(text_, key):
    return float(re.search(rf"^\s*{key}:\s*([-+\d.eE]+)", text_, re.M).group(1))


# ----- ammonia sources: NH3-FINAL-1.2 -------------------------------------------------------------------------
res = json.loads((RUN / "results.json").read_text(encoding="utf-8"))
det = res["deterministic"]
mc = res["monte_carlo"]
bw = res["backward_reachability"]
head = json.loads((RUN / "closure/headline_1_2.json").read_text(encoding="utf-8"))
draws = rows(RUN.relative_to(ROOT) / "closure/mc_draws.csv")
manifest = (RUN / "manifest_resolved.yaml").read_text(encoding="utf-8")
eq = json.loads((SUP / "nh3_ru_price_equalization.json").read_text(encoding="utf-8"))
dec = {r["cost_pool"]: r for r in rows(SUP.relative_to(ROOT) / "nh3_cost_decomposition.csv")}
cmc = json.loads((SUP / "nh3_cost_mc_summary.json").read_text(encoding="utf-8"))
cmc_draws = rows(SUP.relative_to(ROOT) / "nh3_cost_mc_draws.csv")
price_sweep = rows(f"figures/composite/fig2/{V12}/fig2_ru_price_sweep.csv")
parity = price_sweep[-1]
FEB = f"analysis/fe_bridge_backward_2026_09_29/{V12}/"
targets = rows(FEB + "activity_lifecycle_target_keypoints.csv")
strict_joint = _j(FEB + "scaling_lifecycle_exact_summary.json")
strict_keys = rows(FEB + "scaling_lifecycle_exact_keypoints.csv")
life_parity = rows(FEB + "ru_lifecycle_parity_keypoints.csv")
NFU = "analysis/nonfigure_upgrades_2026_09_29/"
regret = {r["system"]: r for r in rows(NFU + "decision_regret_summary.csv")}                 # MeOH and Au/TiO2 rows
transfer = {r["system"]: r for r in rows(NFU + "pairwise_inversion_index.csv")}              # MeOH and Au/TiO2 rows
regret12 = {r["system"]: r for r in rows(NFU + V12 + "/decision_regret_summary.csv")}        # NH3 row, 1.2
transfer12 = {r["system"]: r for r in rows(NFU + V12 + "/pairwise_inversion_index.csv")}     # NH3 row, 1.2
corr_uq = rows(NFU + V12 + "/descriptor_correlation_sensitivity.csv")
stop_eff = json.loads((ROOT / "analysis/nonfigure_upgrades_2026_09_29/agent_stopping_efficiency.json").read_text(encoding="utf-8"))
regret_mc = _j(NFU + V12 + "/nh3_cost_mc_regret_summary.json")
ok("NH3 sources: the audit reads the canonical NH3-FINAL-1.2 run and its ported analyses",
   (HARNESS_12 / "CANONICAL_RUN.txt").read_text(encoding="utf-8").strip() == RUN.name
   and head["model_version"] == "NH3-FINAL-1.2" and det["process_state_count"] == head["process_state_count"]
   and eq["model"] == cmc["model"] == regret_mc["model"] == "NH3-FINAL-1.2" and eq["run"] == cmc["run"] == RUN.name
   and strict_joint["process_states"] == det["process_state_count"]
   and abs(eq["Fe_canonical"]["total_cost_USD_t"] - det["metals"]["Fe"]["feasible"]["total_cost"]) < 1e-12
   and abs(eq["Ru_canonical"]["total_cost_USD_t"] - det["metals"]["Ru"]["feasible"]["total_cost"]) < 1e-12
   and abs(strict_joint["Fe_reference_cost_USD_t"] - det["metals"]["Fe"]["feasible"]["total_cost"]) < 1e-12,
   RUN.name)

meoh = {r["candidate"]: r for r in rows("data/meoh/meoh_candidate_ranking_D01v3.csv")}
meoh_prov = json.loads((ROOT / "data/meoh/meoh_candidate_ranking_D01v3_provenance.json").read_text(encoding="utf-8"))
purge = rows("data/meoh/meoh_purge_robustness_D01v3.csv")
meoh_mc = json.loads((ROOT / "analysis/meoh_measurement_mc_2026_10_05/mc_summary.json").read_text(encoding="utf-8"))[
    "sets"]["canonical"]["k=1"]
au = rows("data/rank_preservation_control_v1_1.csv")
semi = {(r["window"], r["stress"]): r for r in rows("data/rank_preservation_semiopen_v1_3_summary.csv")}

panel = rows("data/agent_figure_panel_data_2026-09-13.csv")
comp = rows("data/discover_boundary_c1_decision_components.csv")
orc = {r["metric"]: float(r["value"]) for r in rows("analysis/supervisor_2026_09_20/agent_oracle_summary.csv")}
schema = json.loads((ROOT / "provenance/discover_v1/source_harness/DISCOVER_ACTION_SCHEMA_V1.json").read_text(encoding="utf-8"))


def target(life, recovery):
    return next(
        r for r in targets
        if int(r["catalyst_life_y"]) == life
        and abs(float(r["Ru_recovery_fraction"]) - recovery) < 1e-12
    )


def agent_cell(tier, budget, arm="E"):
    return next(r for r in panel if r["tier"] == tier and r["arm"] == arm and r["budget_CU"] == str(budget))


# ----- Results 1: NH3 ranking -------------------------------------------------
s1 = section("Process and economic evaluation reverse the leading ammonia ranking")
m = det["metals"]
tokens(
    "NH3 ranking/cost anchors in correct section",
    s1,
    f"{m['Fe']['feasible']['total_cost']:.3f}",
    f"{m['Ru']['feasible']['total_cost']:.3f}",
    f"{m['Os']['feasible']['total_cost']:.3f}",
    f"{head['top3_spearman']:.2f}",
    f"{head['top3_kendall']:.2f}",
    f"{det['raw_global_spearman']:.3f}",
)
ok("NH3 atomic top3 source", det["activity_order"][:3] == ["Ru", "Os", "Fe"])
ok("NH3 economic top3 source", det["raw_economic_order"][:3] == ["Fe", "Ru", "Os"])
R_NH3 = float(regret12["NH3"]["normalized_decision_regret"])
GAP_NH3 = m["Ru"]["feasible"]["total_cost"] - m["Fe"]["feasible"]["total_cost"]
tokens(
    "NH3 decision regret in ranking section",
    s1,
    f"{100 * R_NH3:.1f}%",
)
ok(
    "NH3 decision regret source",
    abs(R_NH3 - GAP_NH3 / m["Fe"]["feasible"]["total_cost"]) < 1e-12
    and (regret12["NH3"]["upstream_selection"], regret12["NH3"]["downstream_optimum"])
    == (det["activity_order"][0], det["feasible_economic_order"][0])
    and abs(regret_mc["deterministic_regret"] - R_NH3) < 1e-12,
)
# the catalyst-controlled cost per year: Ru - Fe at the two optima times the plant's annual output (manifest)
ANNUAL_T = _yaml_num(manifest, "production_tpd") * 365 * _yaml_num(manifest, "capacity_factor")
tokens(
    "SI Note 1: Ru - Fe difference and its annual value",
    s1,
    f"normalized decision regret of **{100 * R_NH3:.1f}%**",
    f"The {GAP_NH3:.3f} US dollars per tonne difference",
    f"amounts to {GAP_NH3 * ANNUAL_T / 1e6:.2f} million US dollars per year for a "
    f"{_yaml_num(manifest, 'production_tpd'):,.0f} t/d plant, which at a capacity factor of "
    f"{_yaml_num(manifest, 'capacity_factor'):.2f} produces {ANNUAL_T:,.0f} t of NH₃ per year",
)
tokens("Main text: ammonia ranking reversal, regret and its annual value",
    main_section("The most active ammonia catalyst is not the cheapest to run"),
    f"over {det['process_state_count']:,} process states",
    f"at {m['Fe']['feasible']['total_cost']:.2f}, {m['Ru']['feasible']['total_cost']:.2f} and {m['Os']['feasible']['total_cost']:.2f} US dollars per tonne of NH₃",
    f"Spearman correlation of {det['raw_global_spearman']:.3f} across all 15 metals",
    f"ρ = {head['top3_spearman']:.2f} among the three leaders",
    f"raise the catalyst-dependent cost by {100 * R_NH3:.1f}%",
    f"The {GAP_NH3:.2f} US dollars per tonne",
    f"{GAP_NH3 * ANNUAL_T / 1e6:.2f} million US dollars a year for a {_yaml_num(manifest, 'production_tpd'):,.0f} t/d plant")

# ----- Results 2: price/process/uncertainty ----------------------------------
s2 = section("Metal price and process optimization jointly determine the Fe-Ru ranking")
fe = m["Fe"]["feasible"]
ru = m["Ru"]["feasible"]
r8 = eq["Ru_price_equalized_to_Fe"]
gap = float(dec["TOTAL"]["Ru_minus_Fe_USD_t"])
fe_win = sum(r["economic_winner"] == "Fe" for r in draws)
_sw0, _swN = price_sweep[0], price_sweep[-2]                  # first and last price of the sweep (the last row is parity)
_swN_e = int(math.floor(math.log10(float(_swN["price_USD_kg"]))))
tokens(
    "NH3 operating/equal-price anchors",
    s2,
    f"Fe has an interior optimum near {fe['T_C']:.0f} °C and {fe['P_bar']:.0f} bar, whereas Ru favors approximately "
    f"{ru['T_C']:.0f} °C and {ru['P_bar']:.0f} bar, both with a {fe['Tsep_C']:.0f} °C separator",
    f"equal to the Fe value of {r8['price_USD_kg']:.0f} US dollars per kilogram",
    f"The Ru optimum shifts from {ru['T_C']:.0f} °C and {ru['P_bar']:.0f} bar to {r8['T_C']:.0f} °C and "
    f"{r8['P_bar']:.0f} bar, and its optimized cost falls to {r8['total_cost_USD_t']:.3f} US dollars per tonne of NH₃, "
    f"{-eq['Ru_minus_Fe_USD_t']:.3f} US dollars per tonne below Fe",
    f"places Fe-Ru parity at {float(parity['price_USD_kg']):.2f} US dollars per kilogram. At this price, Ru operates at "
    f"{float(parity['T_C']):.0f} °C and {float(parity['P_bar']):.0f} bar with a {float(parity['V_m3']):.2f} m³ catalyst bed",
    f"the optimum moves from {float(_sw0['P_bar']):.0f} bar and an {float(_sw0['V_m3']):.1f} m³ bed at "
    f"{float(_sw0['price_USD_kg']):.0f} US dollar per kilogram to {float(_swN['P_bar']):.0f} bar and a "
    f"{float(_swN['V_m3']):.3f} m³ bed at {float(_swN['price_USD_kg']) / 10 ** _swN_e:g} × 10^{_swN_e} US dollars per kilogram",
)
ok("NH3 equal-price counterfactual: Ru below Fe after reoptimization (source sign); parity row closes the gap",
   eq["Ru_minus_Fe_USD_t"] < 0 and eq["economic_order_after_equalization"] == "Ru < Fe"
   and abs(r8["total_cost_USD_t"] - m["Fe"]["feasible"]["total_cost"] - eq["Ru_minus_Fe_USD_t"]) < 1e-12
   and abs(float(parity["cost"]) - m["Fe"]["feasible"]["total_cost"]) < 1e-9
   and float(price_sweep[0]["price_USD_kg"]) < r8["price_USD_kg"] < float(parity["price_USD_kg"])
   < eq["Ru_canonical"]["price_USD_kg"] < float(_swN["price_USD_kg"]))
_pools = {k: float(r_["Ru_minus_Fe_USD_t"]) for k, r_ in dec.items() if k != "TOTAL"}
_pos = sorted((k for k in _pools if _pools[k] > 0), key=lambda k: -_pools[k])
tokens(
    "NH3 canonical cost-gap decomposition",
    s2,
    f"{gap:.3f}",
    f"Fresh-feed compression contributes +{_pools['fresh_compression_electricity']:.3f} US dollars per tonne, metal "
    f"inventory +{_pools['metal_inventory']:.3f} and compressor capital +{_pools['compressor_CAPEX']:.3f}, while vessel "
    f"pressure, recycle compression and reactor-base terms partly offset these contributions; neither optimum uses "
    f"refrigeration",
)
ok("NH3 cost-gap decomposition: the pools sum to the gap; compression, metal and compressor capital carry it in that "
   "order, vessel, recycle and reactor terms offset it, and neither optimum is refrigerated",
   abs(sum(_pools.values()) - gap) < 1e-9 and abs(gap - GAP_NH3) < 1e-12
   and _pos == ["fresh_compression_electricity", "metal_inventory", "compressor_CAPEX"]
   and all(_pools[k] < 0 for k in ("vessel_pressure_premium", "recycle_compression_electricity", "reactor_base"))
   and float(dec["refrigeration_electricity"]["Fe_canonical_USD_t"]) == 0.0
   and float(dec["refrigeration_electricity"]["Ru_canonical_USD_t"]) == 0.0,
   " > ".join(_pos))
tokens(
    "NH3 descriptor uncertainty semantics",
    s2,
    f"{100*mc['Fe_feasibility_probability']:.1f}%",
    f"{100*fe_win/len(draws):.1f}%",
    f"({fe_win}/{len(draws)})",
    f"{100*mc['top3_actionable']:.1f}%",
    f"{100*mc['top1_survival']:.1f}%",
)
v = cmc["full_14136_state_direct_cost_verification"]
a = cmc["alpha_star"]
tokens(
    "NH3 cost-MC and parity-target distribution",
    s2,
    f"{cmc['draws']:,}",
    f"{v['P_C_Fe_lt_C_Ru']:.3f}",
    f"{v['minimum_Ru_minus_Fe_USD_t']:.3f}",
    f"{a['p05']:.2f}-fold",
    f"{a['p50']:.2f}-fold",
    f"{a['p95']:.2f}-fold",
)
rq = regret_mc["regret_quantiles"]
tokens(
    "NH3 cost-MC decision-regret distribution",
    s2,
    f"{100*rq['p05']:.2f}%",
    f"{100*rq['p50']:.2f}%",
    f"{100*rq['p95']:.2f}%",
    f"R remains positive in all {regret_mc['draws']:,} draws",
)
# the committed draw-level table of the same preregistered draws (seed, priors and N of the regret summary): its
# per-draw regret (C_Ru - C_Fe)/C_Fe reproduces the summary quantiles, its gap and alpha* the cost-MC summary
_dr = [(float(r_["Ru_cost_USD_t"]) - float(r_["Fe_cost_USD_t"])) / float(r_["Fe_cost_USD_t"]) for r_ in cmc_draws]
_dq = _quantiles(_dr, [0.05, 0.5, 0.95])
_ga = _quantiles([float(r_["Ru_minus_Fe_USD_t"]) for r_ in cmc_draws], [0.05, 0.5, 0.95])
_aq = _quantiles([float(r_["alpha_star"]) for r_ in cmc_draws], [0.05, 0.5, 0.95])
ok(
    "NH3 regret MC source: the committed 1.2 draw table reproduces the regret and cost-MC summaries",
    regret_mc["draws"] == cmc["draws"] == len(cmc_draws) and regret_mc["seed"] == cmc["seed"]
    and [int(r_["draw"]) for r_ in cmc_draws] == list(range(len(cmc_draws)))
    and regret_mc["P_regret_gt_0"] == 1.0 and min(_dr) > 0 and regret_mc["count_regret_gt_0"] == len(_dr)
    and all(abs(x - rq[k]) < 1e-12 for x, k in zip(_dq, ("p05", "p50", "p95")))
    and abs(min(_dr) - rq["min"]) < 1e-12 and abs(max(_dr) - rq["max"]) < 1e-12
    and all(abs(x - v["Ru_minus_Fe_USD_t_quantiles"][k]) < 1e-9 for x, k in zip(_ga, ("p05", "p50", "p95")))
    and abs(min(float(r_["Ru_minus_Fe_USD_t"]) for r_ in cmc_draws) - v["minimum_Ru_minus_Fe_USD_t"]) < 1e-9
    and all(abs(x / a[k] - 1) < 1e-9 for x, k in zip(_aq, ("p05", "p50", "p95"))),
)
rho0 = next(r for r in corr_uq if abs(float(r["latent_pairwise_correlation"]) - 0.0) < 1e-12)
rho9 = next(r for r in corr_uq if abs(float(r["latent_pairwise_correlation"]) - 0.9) < 1e-12)
_aw = {k: sum(r_["atomic_winner"] == k for r_ in draws) / len(draws) for k in ("Ru", "Os", "Fe")}
ok(
    "NH3 copula Fe-top1 anchors: positive error correlation raises the Fe top-1 share (source check)",
    int(rho0["n_draws"]) == int(rho9["n_draws"]) > len(draws)
    and float(rho9["P_atomic_top1_Fe"]) > float(rho0["P_atomic_top1_Fe"])
    and all(abs(float(r_["P_atomic_top1_Ru"]) + float(r_["P_atomic_top1_Os"]) + float(r_["P_atomic_top1_Fe"]) - 1)
            < 1e-9 for r_ in (rho0, rho9)),
)

# ----- Results 3: backward target and reachability ----------------------------
s3 = section("Lifecycle engineering, not activity, brings Ru to parity")
tokens(
    "NH3 activity-only backward/reachability anchors",
    s3,
    f"{bw['Ru_activity_break_even_multiplier']:.2f}-fold",
    f"{bw['Ru_scaling_max_gain_673K']:.3f}-fold",
    f"{bw['Ru_scaling_max_gain_all_states']:.3f}-fold",
    f"{bw['Ru_best_scaling_cost_USD_t']:.3f}",
    f"{bw['Ru_best_scaling_EN_eV']:.3f}",
    f"{a['p05']:.2f}-fold",
    f"{float(parity['price_USD_kg']):.2f}",
)
# lifecycle parity at the current Ru activity: P_Ru (1 - r)(L_ref / L) <= p*, L_ref the frozen 10-y catalyst life; the
# prespecified lifecycle box (lifetime and recovery bounds) is that of the strict-scaling closure
P_RU0, P_STAR, L_REF = eq["Ru_canonical"]["price_USD_kg"], float(parity["price_USD_kg"]), _yaml_num(manifest, "catalyst_life_y")
L_MAX, R_MAX = (strict_joint["tested_lifecycle_envelope"]["max_life_y"],
                strict_joint["tested_lifecycle_envelope"]["max_recovery_fraction"])
_r_at = lambda life: 1 - P_STAR * life / (L_REF * P_RU0)          # recovery needed at lifetime `life`
L99 = L_REF * P_RU0 * (1 - R_MAX) / P_STAR                        # lifetime needed at the recovery bound
_lp = {float(r_["lifetime_y"]): float(r_["required_recovery_fraction"]) for r_ in life_parity}
tokens(
    "NH3 lifecycle parity at the current Ru activity (SI Note 8)",
    s3,
    f"At the baseline Ru price of {P_RU0:,.1f} US dollars per kilogram, this requires approximately "
    f"{100 * _r_at(L_REF):.2f}% recovery for a {L_REF:.0f}-year lifetime, {100 * _r_at(L_MAX):.2f}% for a "
    f"{L_MAX:.0f}-year lifetime, or a {L99:.1f}-year lifetime at {pc(R_MAX)}% recovery",
    f"{pc(R_MAX)}% optimistic recovery bound therefore reach parity at the current Ru activity for lifetimes above "
    f"{L99:.1f} years",
)
ok("NH3 lifecycle parity keypoints: the committed 1.2 table equals p* / (P_Ru (1 - r)) on the 10-y basis; the parity "
   "lifetime at the recovery bound lies inside the prespecified lifetime range",
   abs(_lp[L_REF] - _r_at(L_REF)) < 1e-9 and abs(_lp[L_MAX] - _r_at(L_MAX)) < 1e-9
   and min(abs(k - L99) for k in _lp) < 1e-3 and L99 < L_MAX)
t10 = float(target(10, 0.99)["certified_upper_bound_required_direct_activity_multiplier"])
t15 = float(target(15, 0.99)["certified_upper_bound_required_direct_activity_multiplier"])
t20 = float(target(20, 0.99)["certified_upper_bound_required_direct_activity_multiplier"])
t20r98 = float(target(20, 0.98)["certified_upper_bound_required_direct_activity_multiplier"])
_n_sweep_states = len({(r_["T_C"], r_["P_bar"], r_["Tsep_C"]) for r_ in price_sweep})
tokens(
    "NH3 joint backward target region",
    s3,
    f"evaluated the {_n_sweep_states} distinct process states already visited by the fully reoptimized Ru price sweep",
    f"With 99% Ru recovery, a 10-year catalyst life requires at most a {t10:.3f}-fold activity increase, whereas 15- and "
    f"20-year lives require none (direct activity multipliers of at most {t15:.3f} and {t20:.3f}); a 20-year lifetime "
    f"with 98% recovery requires at most {t20r98:.3f}-fold",
)
tokens("Methods: the conservative lifecycle target region uses the states of the Ru price sweep", methods,
       f"uses the {_n_sweep_states} states visited by the reoptimized price sweep")
ok("joint target ordering", t20 < t15 < t10)
ok("joint target: a 10-year life at 99 % recovery needs a gain, 15 and 20 years need none (multiplier below 1)",
   t20 < t15 < 1 < t10)
ok("20y/98 target equals 10y/99 within audit", abs(t20r98 - t10) < 1e-9)
SJ = strict_joint
_cor = SJ["tested_lifecycle_envelope"]["best_corner"]
_bx = SJ["boundary_examples"]
_q = SJ["critical_lifecycle_factor_q_per_y"]
_qe = int(math.floor(math.log10(_q)))
_k15 = next(r_ for r_ in strict_keys if float(r_["life_y"]) == 15 and float(r_["recovery"]) == 0.99)
tokens(
    "NH3 strict-scaling lifecycle closure",
    s3,
    f"The canonical strict-scaling minimum, {bw['Ru_best_scaling_cost_USD_t']:.3f} US dollars per tonne at *E*_N = "
    f"{bw['Ru_best_scaling_EN_eV']:.3f} eV, is reproduced before lifecycle changes are introduced",
    f"\\(q^*={_q / 10 ** _qe:.4f}\\times10^{{{_qe}}}\\ \\mathrm{{y}}^{{-1}}\\)",
    f"at {_cor['life_y']:.0f} years and {100 * _cor['recovery_fraction']:.0f}% recovery the best strict-scaling state "
    f"occurs at *E*_N = {_cor['best_E_N_eV']:.3f} eV and costs {_cor['best_strict_scaling_cost_USD_t']:.3f} US dollars "
    f"per tonne, {abs(_cor['margin_vs_Fe_USD_t']):.3f} US dollars per tonne below Fe",
    f"at {float(_k15['life_y']):.0f} years and {100 * float(_k15['recovery']):.0f}% recovery it costs "
    f"{float(_k15['best_cost_USD_t']):.3f}, {abs(float(_k15['margin_vs_Fe_USD_t'])):.3f} below Fe",
    f"Parity requires {100 * _bx['required_recovery_at_20y']:.3f}% recovery at a 20-year lifetime or, equivalently, a "
    f"{_bx['required_life_at_99pct_recovery_y']:.2f}-year lifetime at 99% recovery",
    "Lifecycle engineering thus reaches parity inside the present scaling-constrained design space, where activity alone "
    "cannot",
)
ok(
    "strict-scaling tested lifecycle box reaches parity (intersects the strict-scaling manifold; corner below Fe)",
    SJ["tested_lifecycle_envelope"]["intersects_strict_scaling_manifold"] is True
    and _cor["margin_vs_Fe_USD_t"] < 0 and float(_k15["margin_vs_Fe_USD_t"]) < 0 and _k15["reaches_parity"] == "true"
    and abs(_cor["best_strict_scaling_cost_USD_t"] - SJ["Fe_reference_cost_USD_t"] - _cor["margin_vs_Fe_USD_t"]) < 1e-9
    and _bx["required_recovery_at_20y"] < _cor["recovery_fraction"]
    and _bx["required_life_at_99pct_recovery_y"] < _cor["life_y"]
    and abs(_bx["required_recovery_at_20y"] - (1 - 20 * _q)) < 1e-12
    and abs(_bx["required_life_at_99pct_recovery_y"] - (1 - 0.99) / _q) < 1e-9,
)
# replaces the 1.1 check that data/manuscript_headline_results_2026-09-20.csv carries the strict-scaling verdict: that
# table holds NH3-FINAL-1.1 rows only and has no 1.2 counterpart; the 1.2 closure is checked through its own gate
ok(
    "strict-scaling 1.2 closure gate: the canonical strict-scaling Ru minimum of the 1.2 run is reproduced first",
    SJ["baseline_regression_anchor"]["status"] == "PASS"
    and abs(SJ["baseline_regression_anchor"]["canonical_Ru_cost_target_USD_t"] - bw["Ru_best_scaling_cost_USD_t"]) < 1e-12
    and abs(SJ["baseline_regression_anchor"]["Ru_cost_USD_t"] - bw["Ru_best_scaling_cost_USD_t"]) < 1e-9
    and SJ["baseline_regression_anchor"]["E_N_eV"] == bw["Ru_best_scaling_EN_eV"],
)
m_bw = main_section("Lifecycle engineering, not activity, brings Ru to parity")
tokens("Main text: backward design, scaling reach and the lifecycle closure on the strict-scaling manifold", m_bw,
    f"Ru matches Fe only after a {bw['Ru_activity_break_even_multiplier']:.0f}-fold increase ({a['p05']:.0f}–{a['p95']:.0f}-fold, 5th–95th percentile under economic uncertainty;",
    f"at most {bw['Ru_scaling_max_gain_673K']:.2f}-fold at 673 K and {bw['Ru_scaling_max_gain_all_states']:.2f}-fold across all process conditions",
    f"at *E*_N = {bw['Ru_best_scaling_EN_eV']:.3f} eV, still costs {bw['Ru_best_scaling_cost_USD_t']:.2f} US dollars per tonne",
    f"At 99% recovery, a 10-year catalyst life needs at most a {t10:.2f}-fold activity gain and a 20-year life none",
    f"across all {SJ['process_states']:,} process states",
    f"\\(q^*={_q / 10 ** _qe:.2f}\\times10^{{{_qe}}}\\ \\mathrm{{y}}^{{-1}}\\)",
    f"at a {_cor['life_y']:.0f}-year life it requires {100 * _bx['required_recovery_at_20y']:.2f}% recovery",
    f"at {100 * _cor['recovery_fraction']:.0f}% recovery the best strict-scaling state costs {_cor['best_strict_scaling_cost_USD_t']:.2f} US dollars per tonne, {abs(_cor['margin_vs_Fe_USD_t']):.2f} below Fe")

ok("Main text: strict-scaling Ru minimum above Fe (activity alone cannot reach parity)",
   bw["Ru_best_scaling_cost_USD_t"] > m["Fe"]["feasible"]["total_cost"]
   and bw["Ru_scaling_max_gain_all_states"] < a["p05"] < bw["Ru_activity_break_even_multiplier"] < a["p95"])
ok(
    "strict-scaling lifecycle audit scripts present",
    (ROOT / "analysis/fe_bridge_backward_2026_09_29/run_statewise_strict_scaling_lifecycle.py").exists()
    and (ROOT / "analysis/fe_bridge_backward_2026_09_29/run_exact_scaling_lifecycle_surface.py").exists(),
)

# ----- Results 4: methanol ----------------------------------------------------
s4 = section("Selectivity, recycle and purge reshape the methanol ranking")
econ_order = sorted(meoh, key=lambda k: int(meoh[k]["economic_rank"]))
npc = [round(float(meoh[k]["NPC_EUR_t_2pct_purge"])) for k in econ_order]
sty_metric = meoh_prov["metrics"]["STY_per_gRe (intrinsic productivity, reaction-case atomic_rank)"]
c55 = meoh["5 wt% Re | 250 C"]
tokens(
    "MeOH canonical ranking/economics",
    s4,
    "2% purge",
    *(f"{x:,}" for x in npc),
    f"{sty_metric['spearman']:.2f}",
    f"{sty_metric['kendall']:.2f}",
    "two of six",
)
tokens(
    "MeOH leverage/purge robustness",
    s4,
    f"{float(c55['L_CH4_suppression']):.5f}",
    f"{float(c55['L_conversion']):.5f}",
    f"{float(c55['L_STY']):.5f}",
    f"{len(purge)}",
    f"{100*min(float(r['purge']) for r in purge):.1f}%",
    f"{round(100*max(float(r['purge']) for r in purge))}%",
    f"{max(float(r['spearman']) for r in purge):.2f}",
)
ok("MeOH at least one inversion across purge", min(int(r["pairwise_inversions"]) for r in purge) == 1)
tokens("MeOH decision regret", s4, "1.93%")
tokens(
    "MeOH measurement Monte Carlo",
    s4,
    "5,000",
    f"{round(meoh_mc['P_winner_stays_first'] * 5000):,}",
    f"{100 * meoh_mc['P_winner_stays_first']:.1f}%",
    f"{round(meoh_mc['second_vs_third']['P_inverted'] * 5000):,}",
    f"{100 * meoh_mc['second_vs_third']['P_inverted']:.1f}%",
    f"{round(meoh_mc['P_upstream_winner_1wtRe_250C_economic_first'] * 5000)}",
)
ok("MeOH measurement MC: last place fixed", meoh_mc["rank_probability"]["5wtRe_250C"][3] == 1.0)
ok(
    "MeOH regret source",
    abs(float(regret["MeOH"]["normalized_decision_regret"]) - 0.019304569066044774) < 1e-12,
)

# ----- Results 5: rank-preservation control ----------------------------------
s5 = section("Catalyst effects on process operation determine whether rankings change")
p1 = semi[("primary_273_293K", "moderate")]
p2 = semi[("sensitivity_273_313K", "moderate")]
tokens(
    "Au/TiO2 rank-preservation anchors",
    s5,
    "2 > 3 > 4 > 5 > 6 nm",
    "10,000",
    f"{100*float(p1['full_preservation_fraction']):.2f}%",
    str(p1["mean_spearman_rho"]),
    f"{100*float(p2['full_preservation_fraction']):.2f}%",
    str(p2["mean_spearman_rho"]),
)
ok(
    "Au activity monotone",
    all(
        float(a["mass_activity_umol_CO_gcat_s"]) > float(b["mass_activity_umol_CO_gcat_s"])
        for a, b in zip(au, au[1:])
    ),
)

# ----- Discussion / Methods semantic locks ------------------------------------
discussion = raw_text[raw_text.index("## Discussion"):raw_text.index("## Methods")]
_chi = {"NH3": float(transfer12["NH3"]["pairwise_transfer_index_chi"]),          # NH3-FINAL-1.2
        "MeOH": float(transfer["MeOH"]["pairwise_transfer_index_chi"]),
        "AuTiO2": float(transfer["AuTiO2"]["pairwise_transfer_index_chi"])}
# The polished transfer paragraph closes the Au control; Sabatier retains its own section below.
m_transfer = main_section("Without a price or selectivity channel the ranking holds, and catalyst life sets its limit")
m_chi = main_section("An external case: Ru against Ni in CO₂ methanation")
tokens(
    "pairwise realized-transfer diagnostic, not forecasting criterion",
    m_transfer,
    "χ_AB",
    f"{_chi['NH3']:+.3f}",
    f"{_chi['MeOH']:+.3f}",
    f"is ≈ {_chi['AuTiO2']:.2f} for Au",
    "realized pairwise transfer index",
)
tokens(
    "Results: preserve source-normalized upstream advantages and downstream economic effects",
    m_transfer,
    f"have {float(transfer['AuTiO2']['upstream_metric_ratio_sA_over_sB']):.1f} times the mass activity",
    f"need {1 / float(transfer['AuTiO2']['downstream_objective_ratio_JA_over_JB']):.1f} times less catalyst",
    f"a {float(transfer['MeOH']['upstream_metric_ratio_sA_over_sB']):.1f}-fold space-time-yield advantage comes with a "
    f"{(float(transfer['MeOH']['downstream_objective_ratio_JA_over_JB']) - 1) * 100:.1f}% higher production cost",
    f"{float(transfer12['NH3']['upstream_metric_ratio_sA_over_sB']):.0f} times the intrinsic turnover frequency comes with a {(float(transfer12['NH3']['downstream_objective_ratio_JA_over_JB']) - 1) * 100:.0f}% higher catalyst-dependent cost",
)
_t12 = transfer12["NH3"]
ok(
    "pairwise transfer-index source signs",
    _chi["NH3"] > 0 and _chi["MeOH"] > 0 and _chi["AuTiO2"] < 0
    # 1.2: chi = ln(J_Ru/J_Fe) / ln(s_Ru/s_Fe) with J the optimized costs and s the 673 K reference TOFs of the run
    and abs(float(_t12["downstream_objective_ratio_JA_over_JB"])
            - m["Ru"]["feasible"]["total_cost"] / m["Fe"]["feasible"]["total_cost"]) < 1e-12
    and abs(math.log10(float(_t12["upstream_metric_ratio_sA_over_sB"]))
            - (m["Ru"]["activity_logTOF"] - m["Fe"]["activity_logTOF"])) < 1e-9
    and abs(_chi["NH3"] - math.log(float(_t12["downstream_objective_ratio_JA_over_JB"]))
            / math.log(float(_t12["upstream_metric_ratio_sA_over_sB"]))) < 1e-12,
)
tokens(  # wording of the 2026-09-30 scope framing: the objective holds only catalyst-responsive terms
    "NH3 reduced-cost scope lock",
    methods,
    "the objective contains the terms that respond to catalyst identity and performance",
    "common upstream H₂/N₂ supply contributions are held fixed",
)
tokens(  # the draw-level table itself is checked above ("NH3 regret MC source")
    "NH3 draw-level cost-MC reconstruction lock",
    supplementary_method('Ammonia synthesis'),
    f"The economic Monte Carlo analysis uses {cmc['draws']:,} samples with seed {cmc['seed']}",
    "Normalized regret is computed draw-by-draw as (C_Ru - C_Fe)/C_Fe",
)
ok(
    "no stale pending joint-reachability language",
    "Strict scaling-consistent joint reachability is not yet promoted" not in raw_text
    and "PENDING_EXACT_CACHE_SWEEP" not in raw_text,
)

# ----- 2026-10-05 additions: actual Ru catalyst cost, literature gains, methanol backward design --------------
lit = {r["id"]: r for r in rows(f"analysis/promoted_ru_literature_2026_10_05/{V12}/fig3_literature_points.csv")}
tokens(
    "NH3 literature activity gains (Fig. 3a)",
    s3,
    f"{float(lit['P01']['factor_low']):.0f}- and {float(lit['P02']['factor_low']):.0f}-fold",
    f"more than {float(lit['P03']['factor_high']):.0f}-fold at 5 MPa",
    f"more than {float(lit['P04']['factor_high']):.0f}-fold",
    f"{float(lit['E01']['factor_low']):.1f}-fold",
    f"{float(lit['E10']['factor_low']):.1f}-fold",
    f"{float(lit['E09']['factor_low']):.1f}-fold",
    f"{float(lit['C01']['factor_low']):.1f}-fold",
)
_band = _j(f"analysis/promoted_ru_literature_2026_10_05/{V12}/parity_band.json")
_prom = [lit[k] for k in ("P01", "P02", "P03", "P04")]
tokens(
    "NH3 literature gains against the 1.2 parity band (SI Note 8)",
    s3,
    f"all four lie within the {a['p05']:.2f}–{a['p95']:.0f}-fold parity band, and the "
    f"{float(lit['P04']['factor_high']):.0f}-fold Cs–Ru/MgO gain exceeds the {bw['Ru_activity_break_even_multiplier']:.2f}-fold "
    f"central requirement",
)
ok("NH3 literature gains: the four promoter gains lie in the cost-MC band, only Cs-Ru/MgO exceeds alpha*, the support and "
   "confinement gains lie below the band",
   all(a["p05"] <= float(r_["factor_high"]) <= a["p95"] for r_ in _prom)
   and [float(r_["factor_high"]) > bw["Ru_activity_break_even_multiplier"] for r_ in _prom] == [False, False, False, True]
   and all(float(lit[k]["factor_high"]) < a["p05"] for k in ("P05", "E01", "E10", "E09", "C01"))
   and abs(_band["band"]["p05"] - a["p05"]) < 1e-12 and abs(_band["band"]["p95"] - a["p95"]) < 1e-12
   and abs(_band["band"]["alpha_star"] - bw["Ru_activity_break_even_multiplier"]) < 1e-12)
mcb = json.loads((ROOT / "analysis/meoh_counterfactual_backward_2026_10_05/summary.json").read_text(encoding="utf-8"))
cf = {r["case"].split(" (")[0]: r for r in mcb["counterfactuals"]}
mbw = {r["property"]: r for r in mcb["backward"]}
tokens(
    "MeOH counterfactual and backward design",
    s4,
    f"rho = -{abs(cf['CH4 selectivity removed']['rho']):.2f}",
    f"rho to +{cf['conversion equalized']['rho']:.2f}",
    mbw["STY per g Re (multiplier)"]["note"].split("= ")[1].split(" ")[0],
    f"{float(mbw['single-pass CO2 conversion']['required']):.3f}",
)
ok("MeOH backward: STY alone cannot reach parity", mbw["STY per g Re (multiplier)"]["required"] == "unreachable")

# ----- Agent scaling: extraction accuracy, self-check, pruning ----------------------------------------------
s6 = section("An automated agent extends the analysis to published and computed catalysts")
ent = {r["doi"]: r for r in rows("agent/extraction/eval/entry_metrics.csv")}
tot = ent["TOTAL"]
src = {(r["source_type"], r["field"]): r for r in rows("agent/extraction/eval/field_accuracy_by_source.csv")}


def n_ok(source, field):
    r = src[(source, field)]
    return f"{r['n_correct_strict']} of {r['n_extracted']}"


ext = json.loads((ROOT / "agent/extraction/eval/summary.json").read_text(encoding="utf-8"))
p18, p31 = ext["precision"]["first18"], ext["precision"]["added31"]
err = ext["errata"]
_ea_c = json.loads((ROOT / "analysis/verify_2026_10_08/errata_adjudication_summary.json")
                  .read_text(encoding="utf-8"))["confirmed"]
lit = json.loads((ROOT / "analysis/meoh_literature_inversion_2026_10_05/summary.json").read_text(encoding="utf-8"))
ALY = f"analysis/nh3_alloy_extension_2026_10_05/{V12}/"                      # ammonia alloy chain, NH3-FINAL-1.2
alloy = _j(ALY + "summary.json")
ext_all = alloy["extended_with_usgs_prices"]
tokens(
    "Agent extraction accuracy",
    s6,
    f"{ext['matching']['ambiguous_pairs']} of the {ext['matching']['pairs']} pairs",
    f"{tot['matched']} of the {tot['curated']} curated entries ({float(tot['recall']) * 100:.0f}%)",
    n_ok("table", "X_CO2"), n_ok("table", "S_MeOH"),
    n_ok("SI", "X_CO2"), n_ok("SI", "S_MeOH"), n_ok("SI", "STY"),
    n_ok("plot", "X_CO2"), n_ok("plot", "S_MeOH"),
    f"{p18['precision_all_extracted'] * 100:.0f}% are correct in the first 18 papers",
    f"({p18['unmatched_correct']} of the "
    f"{p18['unmatched_correct'] + p18['unmatched_duplicate'] + p18['unmatched_wrong']} reviewed are correct, "
    f"{p18['unmatched_unreviewed']} are not yet reviewed)",
    f"an estimated {p31['precision_all_extracted'] * 100:.0f}% in the 31 papers added later",
    f"{p31['pooled_sample'].split('/')[0]} of a random {p31['pooled_sample'].split('/')[1]} such entries",
    # errata counted by root cause (analysis/verify_2026_10_08/errata_adjudication.py), not by changed cell
    f"{_ea_c['root_causes']} root causes, one mechanism in one source paper each, in {_ea_c['error_rules']} rules, "
    f"{_ea_c['value_cells_error_rules']} cells and {_ea_c['dropped_records']} rows",
)
ok("Agent: Gothe Table 4 extracted exactly", ext["gothe"]["matched"] == 21 and ext["gothe"]["X_CO2"] == "21/21")
canon = lit["selfcheck"]["canonical_states"]
tokens(
    "Agent self-check",
    s6,
    "2.3 × 10⁻¹³",
    "943.30, 961.51, 966.96 and 1,258.17",
)
ok("Agent self-check source", lit["selfcheck"]["max_abs_diff_eur_t"] < 1e-12
   and sorted(round(v, 2) for v in canon.values()) == [943.3, 961.51, 966.96, 1258.17])
ok("Agent: pure-metal self-check source", all(r["match"] for r in alloy["self_check"]))
gate = json.loads((ROOT / "agent/selfcheck_report.json").read_text(encoding="utf-8"))
au_gate = next(x for x in gate["systems"] if x["system"] == "Au/TiO2")
ok("Agent self-check gate passes for all three systems", gate["pass"] and all(x["pass"] for x in gate["systems"]))
ok("Agent Au/TiO2 extracted inputs reproduce the control", au_gate["extracted"]["pass"]
   and au_gate["extracted"]["envelope"]["full_preservation"] == 1.0 and au_gate["extracted"]["semiopen_windows_compared"] == 6)
tokens("Agent Au/TiO2 self-check", s6, "all three systems", "all 10,000 literature-envelope samples", "six operating-window stress tests")
tokens(
    "Agent pruning",
    s6,
    f"{ext_all['costed']:,} priced bimetallic surfaces",
    f"excludes {ext_all['pruning']['pruned']:,} candidates ({ext_all['pruning']['fraction_saved'] * 100:.1f}%)",
)
ok("Agent pruning: no false exclusion", ext_all["pruning"]["false_prunes"] == [])
mpr = json.loads((ROOT / "analysis/meoh_pruning_2026_10_06/summary.json").read_text(encoding="utf-8"))
mp = mpr["pruning"]["recycled_opt"]
ok("Agent pruning, methanol: bound valid and no leader missed", mpr["bound_valid_all"] and mp["leader_missed"] == 0)

FE_COST_ALLOY = _j(ALY + "alloy_backward_summary.json")["Fe_cost_USD_t"]

# ----- NH3 bimetallic surfaces ----------------------------------------------------------------------------------
s7 = section("Alloy surfaces that undercut Fe pair a cheap 3d metal with a group-6 metal")
m_alloy = main_section("Alloy surfaces that undercut Fe pair a cheap 3d metal with a group-6 metal")
tm = alloy["extended_excluding_sp_and_group3to5"]
glob_below = tm["below_Fe_surfaces"]
anch_below = [x[0] for x in tm["below_Fe_anchored_surfaces"]]
both_below = [x for x in glob_below if x in anch_below]
rg, ra = tm["route_global"], tm["route_anchored"]
tokens(
    "NH3 alloy screen",
    s7,
    f"{alloy['surfaces_fetched']:,} bimetallic and pure-metal surfaces",
    f"Among the {tm['costed']} surfaces", f"{tm['feasible']} satisfy",
    *[chem(x) for x in glob_below], *[chem(x) for x in anch_below],
    f"{word(len(glob_below), cap=True)} undercut Fe under the linear bridge: {chem(rg['economic_winner'])} "
    f"({rg['economic_winner_cost']:.2f} US dollars per tonne)",
    f"{word(len(anch_below), cap=True)} do so under the element-anchored bridge",
    f"ranks {ordinal(rg['upstream_winner_economic_rank'])} economically",
    f"({chem(rg['upstream_winner'])}, {rg['regret'] * 100:.1f}% regret)",
    f"{ordinal(ra['upstream_winner_economic_rank'])} ({chem(ra['upstream_winner'])}, {ra['regret'] * 100:.1f}%)",
    f"{rg['spearman']:.2f} and {ra['spearman']:.2f}",
    f"{_and(chem(x) for x in both_below)} remain below Fe under both bridges",
)
ok("NH3 alloy: below-Fe family is cheap 3d + group 6", tm["below_Fe_either_route_all_3d_plus_group6"])
ok("NH3 alloy: counts in text match source (below-Fe lists, their counts, the both-bridges set, the cheapest surface)",
   len(glob_below) == tm["below_Fe"] and len(anch_below) == tm["below_Fe_anchored"]
   and both_below == tm["below_Fe_both_routes"] and glob_below[0] == rg["economic_winner"]
   and rg["economic_winner_cost"] < FE_COST_ALLOY and tm["Fe_cost_USD_t"] == FE_COST_ALLOY
   and abs(FE_COST_ALLOY - m["Fe"]["feasible"]["total_cost"]) < 1e-12,
   f"{len(glob_below)} / {len(anch_below)}")
abw = {(r["surface"], r["route"]): r for r in rows(ALY + "alloy_backward.csv")}
lead_g, lead_a = abw[(rg["upstream_winner"], "global")], abw[(ra["upstream_winner"], "anchored")]
cu3cr = abw[(rg["economic_winner"], "global")]
tokens(
    "NH3 alloy counterfactual and backward design",
    s7,
    f"({float(lead_g['cost_at_Fe_price_USD_t']):.2f} and {float(lead_a['cost_at_Fe_price_USD_t']):.2f} US dollars per tonne)",
    f"they need {fold(float(lead_g['alpha_star']))}-fold and {fold(float(lead_a['alpha_star']))}-fold activity increases",
    f"below {float(lead_g['best_scaling_cost_USD_t']):.2f} and {float(lead_a['best_scaling_cost_USD_t']):.2f} US dollars per tonne",
    f"{chem(rg['economic_winner'])} keeps its lead with {float(cu3cr['alpha_star']) * 100:.0f}% of its activity",
)
ok("NH3 alloy: leaders undercut Fe only at the Fe price",
   float(lead_g["cost_at_Fe_price_USD_t"]) < FE_COST_ALLOY < float(lead_g["cost_USD_t"])
   and float(lead_a["cost_at_Fe_price_USD_t"]) < FE_COST_ALLOY < float(lead_a["cost_USD_t"])
   and float(lead_g["best_scaling_cost_USD_t"]) > FE_COST_ALLOY and float(lead_a["best_scaling_cost_USD_t"]) > FE_COST_ALLOY
   and float(cu3cr["alpha_star"]) < 1)
ok("NH3 alloy: the surfaces below Fe in both bridges beat Fe in the backward table under both routes",
   all(abw[(s_, r_)]["beats_Fe"] == "True" for s_ in both_below for r_ in ("global", "anchored")))
claim_tokens("Main text: alloy screen, its activity leader and the lower bound",
    ("main text", m_alloy, [f"the {alloy['surfaces_fetched']:,} bimetallic and pure-metal surfaces",
    f"Of the {tm['costed']} surfaces made only of transition metals outside groups 3–5, {tm['feasible']} fit",
    f"{word(len(glob_below))} undercut Fe when the database is bridged linearly onto the model's descriptor, {word(len(anch_below))} under an element-anchored bridge",
    f"The most active surface, {chem(rg['upstream_winner'])}, ranks only {ordinal(rg['upstream_winner_economic_rank'])} on cost ({rg['regret'] * 100:.1f}% regret)",
    f"excludes {ext_all['pruning']['fraction_saved'] * 100:.1f}% of the {ext_all['costed']:,} priced surfaces"]),
    ("SI Notes", section("An automated agent extends the analysis to published and computed catalysts"),
    [f"excludes {ext_all['pruning']['pruned']:,} candidates ({ext_all['pruning']['fraction_saved'] * 100:.1f}%)"]))

s2_full = section("Metal price and process optimization jointly determine the Fe-Ru ranking")

# ----- NH3 measured catalysts --------------------------------------------------------------------------------
s9 = section("Measured ammonia catalysts rank differently by laboratory rate and by plant cost")
SUPP = f"analysis/nh3_supported_2026_10_06/{V12}/"
sup = _j(SUPP + "summary.json")
adj = json.loads((ROOT / "agent/nh3_supported/out/adjudication_summary.json").read_text(encoding="utf-8"))
pm, ov = sup["per_metal"], sup["overall"]
fa = sorted((v for _, v in sup["fused_fe_alpha"]), reverse=True)
_fa_factor = max(max(fa), 1 / min(fa))                     # how far the calibration misses the two fused-iron rates
sgm = {r["ref"]: r for r in rows(SUPP + "group_metrics.csv")}
FE_SUP = sup["Fe_benchmark_USD_t"]
_below = sorted(((k, pm[k]) for k in pm if pm[k]["below_Fe"]), key=lambda kv: kv[1]["cost_min"])   # cheapest first
_below_pct = [f"{(1 - x['cost_min'] / FE_SUP) * 100:.0f}%" for _, x in _below]
tokens(
    "NH3 measured catalysts",
    s9,
    f"the {adj['rows']} catalyst rows", f"agree on {adj['agree']} of {adj['numeric_fields']} numeric fields",
    f"within a factor of {math.ceil(_fa_factor * 10) / 10:.1f} (α = {fa[0]:.2f} and {fa[1]:.2f})",
    f"Of the {sup['primary']} catalysts in the primary set ({pm['Ru']['n']} Ru, {pm['Fe']['n']} Fe, {pm['Co']['n']} Co and {pm['Ni']['n']} Ni)",
    f"the one with the highest laboratory rate, {ov['rate_leader']}, "
    f"costs {ov['rate_leader_cost']:.2f} US dollars per tonne, {ov['regret'] * 100:.0f}% above",
    f"(Spearman ρ = {ov['spearman_rate_vs_cost']:.2f})",
    f"({float(sgm['81']['regret']) * 100:.1f}% and {float(sgm['82']['regret']) * 100:.1f}% regret)",
    f"{word(len(_below), cap=True)} measured catalysts undercut the fused-iron benchmark without metal recovery",
    f"({chem(_below[0][1]['best'])}, {_below[0][1]['cost_min']:.2f} US dollars per tonne)",
    f"({chem(_below[1][1]['best'])}, {_below[1][1]['cost_min']:.2f}), by {_and(_below_pct)}",
    f"with 90% Ru recovery {word(len(sup['sensitivity']['Ru_recovery90']['below_Fe']))} Ru catalysts do",
)
ok("NH3 measured: without recovery exactly one Ru and one Fe catalyst undercut the Fe benchmark (after the primary-paper "
   "errata); the plant-cost leader is the cheapest of them",
   [k for k, _ in _below] == ["Ru", "Fe"] and all(x["below_Fe"] == 1 for _, x in _below)
   and sum(x["below_Fe"] for x in pm.values()) == 2 and all(x["cost_min"] < FE_SUP for _, x in _below)
   and ov["plant_leader"] == _below[0][1]["best"] and abs(ov["plant_leader_cost"] - _below[0][1]["cost_min"]) < 1e-12
   and abs(FE_SUP - m["Fe"]["feasible"]["total_cost"]) < 1e-12)
tokens(
    "Main text: measured catalysts of the review (rate and cost uncorrelated)",
    main_section("Published laboratory leaders are often not the plant-cost leaders"),
    f"Across the {sup['primary']} catalysts of a review of ammonia-synthesis catalysts",
    f"laboratory rate and plant cost are uncorrelated (Spearman ρ = {ov['spearman_rate_vs_cost']:.2f};",
    # The two below-Fe catalysts and their 4% / 3% margins remain checked in NH3 measured catalysts (SI Note 4).
)
errata = rows("agent/nh3_supported/out/primary_errata.csv")
tokens("NH3 measured: errata and Methods row count", supplementary_method("Measured ammonia catalysts"),
       "ten transcription errors in nine rows",
       f"enter the chain: {sup['rows'] - sup['outside']} of {sup['rows']} rows")
ok("NH3 measured: errata file covers nine review rows", len({(r["page"], r["row"]) for r in errata}) == 9,
   f"{len({(r['page'], r['row']) for r in errata})} rows")

# ----- NH3 field statistic (30 primary papers) ------------------------------------------------------------------
FLD = f"analysis/nh3_field_2026_10_06/{V12}/"
fd = _j(FLD + "summary.json")
fev = json.loads((ROOT / "agent/nh3_field/eval/summary.json").read_text(encoding="utf-8"))
fpr = _j(FLD + "summary_printed.json")
FP, FV = fpr["primary"], fpr["variants"]          # frozen ammonia field result: printed values only
fk = FP["mismatch_kinds"]
fci = FP["bootstrap_papers"]["mismatch_fraction_ci95"]
rate_ev = next(f for f in fev["fields"] if f["field"] == "rate")
_fe_dm = sum(1 for r in rows(FLD + "group_metrics_printed.csv")
             if r["mismatch_kind"] == "different metal" and r["plant_winner"].startswith("Fe"))
tokens(
    "NH3 field statistic",
    s9,
    f"For the {fev['matched']} entries that the review also tabulates",
    f"the rate in {fev['matched'] - rate_ev['extraction_errors']} of {fev['matched']}",
)
# printed entries below the Fe benchmark (the 1.1 statement "every catalyst below the benchmark is an iron catalyst"
# no longer holds on 1.2: the text names the fused-iron reference and two Co entries, and the check follows it)
FE_FLD = fd["Fe_benchmark_USD_t"]
_fc = sorted((r for r in rows(FLD + "candidates_printed.csv")
              if r["status"].startswith("primary") and r["cost_USD_t"] and float(r["cost_USD_t"]) < FE_FLD),
             key=lambda r: float(r["cost_USD_t"]))
_fc_fused = [r for r in _fc if r["fused"] == "True"]
_fc_other = [r for r in _fc if r["fused"] != "True"]
_fmt_p = lambda x: f"{float(x):g}"                                   # 1 MPa, 6.1 MPa as printed
ok("NH3 field: the printed entries below the Fe benchmark are one fused-iron reference and two entries of one Co catalyst",
   len(_fc_fused) == 1 and _fc_fused[0]["metal"] == "Fe" and len(_fc_other) == 2
   and len({(r["catalyst"], r["metal"], r["metal_wt_pct"], r["doi"]) for r in _fc_other}) == 1 and _fc_other[0]["metal"] == "Co"
   and abs(FE_FLD - m["Fe"]["feasible"]["total_cost"]) < 1e-12,
   f"{len(_fc)} below Fe")
ok("NH3 measured: same-support Fe/Ru studies favour Fe on cost",
   all(sgm[k]["same"] == "False" and "Fe" in sgm[k]["plant_leader"] and "Ru" in sgm[k]["rate_leader"] for k in ("81", "82")))
ok("NH3 measured: fused-iron calibration within the printed factor",
   all(1 / (math.ceil(_fa_factor * 10) / 10) <= x <= math.ceil(_fa_factor * 10) / 10 for x in fa), f"{_fa_factor:.3f}")

# ----- NH3 field, second batch and both batches (analysis/nh3_field_expansion_2026_10_12, PR #78, rescored on 1.2) -------
FX = f"analysis/nh3_field_expansion_2026_10_12/{V12}/"
fx = _j(FX + "report_numbers.json")
B2, PL = fx["batch2_vf"]["primary"], fx["pooled_vf"]["primary"]
B2V, PLV, R1V = fx["batch2_vf"]["variants"], fx["pooled_vf"]["variants"], fx["round1"]["variants"]
NPL = PL                                    # PL is reused for the methanol pooled summary below
_pgm = rows(FX + "runs/pooled_vf_screen/group_metrics_printed.csv")
_p_below = sorted((r for r in _pgm if float(r["plant_winner_cost"]) < fx["model"]["Fe_USD_t"]),
                  key=lambda r: float(r["plant_winner_cost"]))
_p_fused = [r for r in _p_below if r["mismatch_kind"] == "fused-Fe reference vs supported catalyst"]
_p_other = [r for r in _p_below if r not in _p_fused]
_p_other_c = [c for c in _fc_other if _p_other and c["catalyst"] == _p_other[0]["plant_winner"]
              and abs(float(c["cost_USD_t"]) - float(_p_other[0]["plant_winner_cost"])) < 1e-9]
ok("NH3 field batches: round 1 of the pooled report equals the frozen round-1 result; same model and Fe benchmark",
   (fx["round1"]["primary"]["groups"], fx["round1"]["primary"]["mismatch"], fx["round1"]["primary"]["papers"])
   == (FP["groups"], FP["top1_mismatch_groups"], FP["papers"])
   and fx["round1"]["primary"]["ci95"] == FP["bootstrap_papers"]["mismatch_fraction_ci95"]
   and fx["model"]["label"] == "NH3-FINAL-1.2" and abs(fx["model"]["Fe_USD_t"] - FE_FLD) < 1e-12
   and PL["groups"] == FP["groups"] + B2["groups"] and PL["papers"] == FP["papers"] + B2["papers"]
   and PL["mismatch"] == FP["top1_mismatch_groups"] + B2["mismatch"]
   and len(_pgm) == PL["groups"] and sum(r["top1_mismatch"] == "True" for r in _pgm) == PL["mismatch"])
tokens(
    "SI Note 4: both batches",
    s9,
    f"a further {fx['screening_with_si']['included']} of {fx['screening']['screened']} papers screened under a protocol "
    f"committed before extraction (Supplementary Table 2b)",
    f"form {PL['groups']} comparisons in {PL['papers']} papers. The catalyst with the highest rate per gram of catalyst is "
    f"not the plant-cost leader in {PL['mismatch']} of them ({pc(PL['fraction'])}%; 95% confidence interval "
    f"{pc(PL['ci95'][0])}–{pc(PL['ci95'][1])}% from resampling papers), in {PL['papers_with_mismatch']} of {PL['papers']} "
    f"papers, and {PL['regret_gt5pct']['groups']} of the {PL['mismatch']} have a regret above 5%",
    f"Without the commercial fused-iron references the leaders differ in {PLV['without_fused_Fe_references']['mismatch']} "
    f"of {PLV['without_fused_Fe_references']['groups']}; ranking by rate per gram of metal gives "
    f"{PLV['per_g_metal_leaderboard']['mismatch']} of {PLV['per_g_metal_leaderboard']['groups']}, 90% Ru recovery "
    f"{PLV['Ru_recovery_90pct']['mismatch']} of {PLV['Ru_recovery_90pct']['groups']}, and with plot-read entries included "
    f"the leaders differ in {PLV['all_entries']['mismatch']} of {PLV['all_entries']['groups']} comparisons",
    f"In {len(_p_below)} of the {PL['groups']} comparisons the plant-cost leader undercuts the fused-iron benchmark: the "
    f"{word(len(_p_fused))} commercial fused-iron references "
    f"({min(float(r['plant_winner_cost']) for r in _p_fused):.2f}–{max(float(r['plant_winner_cost']) for r in _p_fused):.2f} "
    f"US dollars per tonne) and a {_p_other_c[0]['metal_wt_pct']} wt% {_p_other[0]['plant_winner'].split('-')[0]} catalyst "
    f"at {_p_other_c[0]['T_C']} °C and {_fmt_p(_p_other_c[0]['P_MPa'])} MPa ({float(_p_other[0]['plant_winner_cost']):.2f})"
    if len(_p_other) == 1 and _p_other_c else "one non-fused plant-cost leader below Fe",
)
# the main text reports the pooled 44 comparisons (kinds from the pooled run's printed summary)
_pls = _j(FX + "runs/pooled_vf_screen/summary_printed.json")["primary"]
_plk = _pls["mismatch_kinds"]
_pl_fe = _pls["different_metal_split"]["Fe plant winner, same support family"]["groups"]
ok("NH3 pooled: the run summary equals the report numbers",
   (_pls["groups"], _pls["papers"], _pls["top1_mismatch_groups"]) == (PL["groups"], PL["papers"], PL["mismatch"])
   and {k: v["groups"] for k, v in _plk.items()} == PL["kinds"]
   and abs(_pls["regret_median_mismatched"] - PL["regret_median_mismatched"]) < 1e-12)
claim_tokens("Main text: pooled ammonia result (both batches)",
    ("main text", main_section("Published laboratory leaders are often not the plant-cost leaders"),
    [f"In {PL['mismatch']} of {PL['groups']} comparisons ({pc(PL['fraction'])}%; 95% confidence interval {pc(PL['ci95'][0])}–{pc(PL['ci95'][1])}%)",
    f"{PL['regret_gt5pct']['groups']} of them by more than 5% (Fig. 2c)",
    f"{word(_pl_fe, cap=True)} times the winner is an Fe catalyst on the same support as the faster Ru",
    f"{word(_plk['fused-Fe reference vs supported catalyst']['groups'])} times a commercial fused-iron catalyst"]),
    ("SI Notes", s9, [f"{PL['groups']} comparisons in {PL['papers']} papers",
    f"Without the commercial fused-iron references the leaders differ in {PLV['without_fused_Fe_references']['mismatch']} of {PLV['without_fused_Fe_references']['groups']}"]))
tokens("Methods: second batch of ammonia papers", supplementary_method('Measured ammonia catalysts'),
       f"A second batch of {fx['screening']['screened']} papers was screened, extracted with Supporting Information and "
       f"scored under a protocol committed before extraction ({fx['screening_with_si']['included']} included; "
       f"Supplementary Table 2b); the pooled comparisons are the result ({PL['entries']} printed entries in "
       f"{PL['groups']} groups; all entries, {PLV['all_entries']['mismatch']} of {PLV['all_entries']['groups']} groups)")
tokens("SI Note 4: pooled ammonia kinds", s9,
       f"{PL['regret_gt5pct']['groups']} of the {PL['mismatch']} have a regret above 5% (median "
       f"{pc(PL['regret_median_mismatched'])}%). A commercial fused-iron reference is the plant-cost leader in "
       f"{_plk['fused-Fe reference vs supported catalyst']['groups']} of the {PL['mismatch']}, a catalyst of another metal "
       f"in {_plk['different metal']['groups']} (an Fe catalyst on the same support in all {_pl_fe}), the same metal and "
       f"content on another support or with another promoter in {_plk['same metal and metal content']['groups']} and the "
       f"same metal at another content in {_plk['same metal, different metal content']['groups']}")
_sit = (ROOT / "docs/SI_TABLES.md").read_text(encoding="utf-8")
ok("SI Table 2b: the later ammonia papers with their groups and different winners",
   bool(re.search(rf"^### Supplementary Table 2b \| The {fx['screening_with_si']['included']} later ammonia-synthesis "
                  rf"papers", _sit, re.M))
   and f"| **Total** |  |  | **{fx['screening_with_si']['included']} papers** |" in _sit
   and f"**{B2['groups']}** | **{B2['mismatch']}** |" in _sit)

# ----- MeOH published leaderboards: inert-limited loop S6 primary, S5 alongside ------------------------------------
# Supervisor decision of 2026-10-12 (docs/SUPERVISOR_FEEDBACK_2026-10-12.md): the primary methanol loop limits the
# reactor-inlet CH4 + CO + N2 to 6.86 % (S6, frozen column cost_recycled_opt_inlet); the loop without the limit (S5,
# frozen column cost_recycled_opt) is reported alongside. Every number is read from the merged analyses:
#   analysis/meoh_literature_inversion_2026_10_05 (frozen columns), meoh_constraint_boundary_2026_10_12 (#69),
#   meoh_inlet_definition_2026_10_12 (#73), verify_2026_10_12_s6_conversion (#67), meoh_s6_robustness_2026_10_13 (#79).
s8 = section("Published methanol leaderboards and plant-cost leaderboards often disagree")   # Supplementary Note 3
m_field = main_section("Published laboratory leaders are often not the plant-cost leaders")
P0 = lit["primary"]                       # S5
V = lit["variants"]
S6 = V["inlet_limit_6.86pct"]             # S6
ROB = "analysis/meoh_s6_robustness_2026_10_13/"
fc = _j(ROB + "frozen_columns.json")
F5, F6 = fc["S5"], fc["S6"]
p5, p6 = F5["primary"], F6["primary"]
st5, st6 = _j(ROB + "stats_s5/summary.json"), _j(ROB + "stats_s6/summary.json")
rob = _j(ROB + "results.json")
ssp = _j(ROB + "selectivity_split.json")
ccs = _j(ROB + "catalyst_cost.json")
bnd = _j("analysis/meoh_constraint_boundary_2026_10_12/boundary_summary.json")
idf = _j("analysis/meoh_inlet_definition_2026_10_12/summary.json")
led = _j("analysis/meoh_inlet_definition_2026_10_12/ledger_summary.json")
# the same ledger on both extractions combined (MEOH_FIELD_SET=combined): SI Table 6 and the Methods
LEDC = "analysis/meoh_field_pooled_2026_10_15/robustness/group_ledger/"
ledc = _j(LEDC + "ledger_summary.json")
cvr = _j("analysis/verify_2026_10_12_s6_conversion/s6_conversion_summary.json")["scenarios"]
cv5 = _j("analysis/meoh_literature_inversion_2026_10_05/conversion_sensitivity_summary.json")["scenarios"]
# since 2026-10-15 the main-text methanol field result is the combined set of both extractions (40 + 41 groups);
# the first-extraction sources above still carry the analyses run on the first 40 comparisons only
PL = _j("analysis/meoh_field_pooled_2026_10_15/summary.json")
PL6, PL5 = PL["S6"], PL["S5"]
pl6, pl5 = PL6["primary"], PL5["primary"]
plci6, plci5 = pl6["bootstrap_frozen_inversion"]["ci95"], pl5["bootstrap_frozen_inversion"]["ci95"]
# since 2026-10-16 the robustness numbers of the main text are the combined-set reruns (first set reproduced in each)
RB = _j("analysis/meoh_field_pooled_2026_10_15/robustness/summary.json")
assert not RB["checks_failed"], RB["checks_failed"]
_rn = RB["1_noise"]["S6"]["combined"]
_rin = RB["2_inlet"]["combined"]
_frac = lambda s: tuple(int(x) for x in s.split("/"))  # noqa: E731
LIM = bnd["s6_limit"]
n6, g6 = S6["top1_mismatch_groups"], S6["groups"]
n5, g5 = P0["top1_mismatch_groups"], P0["groups"]
gt5_6, gt5_5 = S6["regret_bins"]["gt5pct"]["groups"], P0["regret_bins"]["gt5pct"]["groups"]
ci6, ci5 = S6["bootstrap"]["ci95"], P0["bootstrap"]["ci95"]
inv6 = [int(x) for x in S6["pairwise_inversions"].split("/")]
inv5 = [int(x) for x in P0["pairwise_inversions"].split("/")]
k5, k6 = F5["kinds"], F6["kinds"]
ok("MeOH S6: the merged analyses agree on the frozen inlet-limited and unlimited columns",
   n6 == p6["disagreements"] == bnd["scenarios"]["S6"]["counts"]["different_leader"]
   == idf["scenarios"]["frozen|6.86"]["different_leader"] == cvr["printed|lab"]["top1_mismatch_groups"]
   == st6["point_estimate"]["groups"]
   and gt5_6 == p6["gt5pct"] == bnd["scenarios"]["S6"]["counts"]["gt5pct"] == idf["scenarios"]["frozen|6.86"]["gt5pct"]
   == cvr["printed|lab"]["gt5pct"]
   and S6["pairwise_inversions"] == p6["pairwise_inversions"] and S6["papers_with_mismatch"] == p6["papers_with_disagreement"]
   and n5 == p5["disagreements"] == idf["scenarios"]["frozen|none"]["different_leader"] == st5["point_estimate"]["groups"]
   and gt5_5 == p5["gt5pct"] and P0["pairwise_inversions"] == p5["pairwise_inversions"]
   and ci6 == p6["bootstrap_frozen_inversion"]["ci95"] and ci5 == p5["bootstrap_frozen_inversion"]["ci95"]
   and abs(LIM - idf["s6_limit_exact"]) < 1e-12 and abs(LIM - lit["thermodynamics"]["inlet_limit"]) < 1e-12
   and all(rob["anchors"].values()) and all(fc["anchors"].values()) and all(a["ok"] for a in idf["anchors"].values()))
ok("MeOH S6: the limit counts CH4 + CO + N2 (frozen definition)",
   idf["definitions"]["frozen"].startswith("CH4 + CO + N2") and idf["definitions"]["true_inert"].startswith("CH4 + N2"))
s6pc, s5pc = pc(S6["top1_mismatch_fraction"]), pc(P0["top1_mismatch_fraction"])

# the 83 -> 40 groups (printed values only, same grouping rule)
pp, ae = led["printed_primary"], led["all_entries"]
gr, pr = led["groups_dropped_by_reason"], led["papers_dropped_by_reason"]
ok("MeOH 83 -> 40 ledger: identical grouping rule, every dropped group accounted for",
   led["grouping_checks"]["identical"] and gr["other"] == 0
   and pp["groups"] + gr["paper without printed values"] + gr["fewer than 2 printed entries"] == ae["groups"]
   and (pp["groups"], pp["entries"], pp["papers"]) == (P0["groups"], P0["entries"], P0["papers"]))
ppc, aec = ledc["printed_primary"], ledc["all_entries"]
grc, prc = ledc["groups_dropped_by_reason"], ledc["papers_dropped_by_reason"]
ok("MeOH combined ledger: identical grouping rule, every dropped group accounted for, kept groups equal the combined primary",
   ledc["grouping_checks"]["identical"] and grc["other"] == 0
   and ppc["groups"] + grc["paper without printed values"] + grc["fewer than 2 printed entries"] == aec["groups"]
   and (ppc["groups"], ppc["entries"], ppc["papers"]) == (pl6["groups"], pl6["entries"], pl6["papers"]))
tokens("Main text: combined comparison groups of both extractions", m_field,
       f"{pl6['groups']} within-paper comparisons, {pl6['entries']} entries",
       f"in {pl6['papers']} papers")
ok("MeOH combined set: the first extraction alone reproduces the frozen primary groups and verdicts",
   (PL6["by_set"]["first"]["groups"], PL6["by_set"]["first"]["papers"]) == (pp["groups"], pp["papers"])
   and PL6["by_set"]["first"]["disagreements"] == S6["top1_mismatch_groups"]
   and PL5["by_set"]["first"]["disagreements"] == P0["top1_mismatch_groups"]
   and PL6["by_set"]["first"]["groups"] + PL6["by_set"]["second"]["groups"] == pl6["groups"]
   and PL["sets"]["first"]["operating_points"] == lit["candidates"])
# the per-group ledger table of the Supplementary Information (tools/build_si_tables.py, from group_ledger.csv)
SIT = (ROOT / "docs/SI_TABLES.md").read_text(encoding="utf-8")
_lt = re.search(r"^### Supplementary Table (\d+) \| The (\d+) methanol comparison groups and the (\d+) of the primary "
                r"analysis[ \t]*$", SIT, re.M)
LEDGER_TABLE = int(_lt.group(1)) if _lt else -1
_lrows, _lhead, _ltot = [], [], []
if _lt:
    _j_ = SIT.find("\n### ", _lt.end())
    _cells = [[c.strip() for c in ln.strip().strip("|").split("|")]
              for ln in SIT[_lt.end():_j_ if _j_ >= 0 else len(SIT)].splitlines() if ln.startswith("| ")]
    _lhead, _body_rows = _cells[0], _cells[1:]
    _ltot = [r for r in _body_rows if r[0] == "**Total**"]
    _lrows = [r for r in _body_rows if r[0] != "**Total**"]
_lstat = [r[_lhead.index("Status")] for r in _lrows] if "Status" in _lhead else []
_ledger_csv = rows(LEDC + "group_ledger.csv")
ok(f"SI Table {LEDGER_TABLE}: the combined 161 -> 81 ledger lists every group once (161 rows, 81 kept) with the ledger's "
   f"drop reasons",
   _lt is not None and (int(_lt.group(2)), int(_lt.group(3))) == (aec["groups"], ppc["groups"])
   and len(_lrows) == len(_ledger_csv) == aec["groups"] == 161
   and _lstat.count("kept") == ppc["groups"] == 81
   and _lstat.count("dropped: no printed values in the paper") == grc["paper without printed values"]
   and _lstat.count("dropped: fewer than two printed entries") == grc["fewer than 2 printed entries"],
   f"{len(_lrows)} rows, {_lstat.count('kept')} kept" if _lt else "table not found in docs/SI_TABLES.md")
ok(f"SI Table {LEDGER_TABLE}: verdict totals equal the combined S6/S5 primary and the all-entries sensitivity",
   len(_ltot) == 1 and _ltot[0][-4:] == [f"**{pl6['disagreements']} of {pl6['groups']}**",
                                         f"**{pl5['disagreements']} of {pl5['groups']}**"] + [
       f"**{ledc['all_entries_result'][k]['different_leader']} of {ledc['all_entries_result'][k]['groups']}**"
       for k in ("S6_6_86pct", "S5")],
   " | ".join(_ltot[0][-4:]) if _ltot else "no total row")
tokens("Methods: combined 161 -> 81 comparison groups", supplementary_method('Published methanol comparisons'),
       f"of the {aec['groups']} groups that include plot-read values, {grc['paper without printed values']} come from "
       f"{prc['paper without printed values']} papers without printed values and {grc['fewer than 2 printed entries']} "
       f"have fewer than two printed entries, which leaves the {ppc['groups']} groups of the primary analysis "
       f"(Supplementary Table {LEDGER_TABLE})")
tokens("SI Note 3: 161 -> 81 comparison groups", s8,
       f"{ppc['groups']} comparisons with {PL6['entries'] if 'entries' in PL6 else 632} entries in {pl6['papers']} papers",
       f"With plot-read values the same rule gives {aec['groups']} groups, of which {grc['paper without printed values']} "
       f"come from {prc['paper without printed values']} papers without printed values and "
       f"{grc['fewer than 2 printed entries']} have fewer than two printed entries (Supplementary Table {LEDGER_TABLE})")

# published loop designs (reactor-inlet mol% as printed in their stream tables): CO + CH4 + N2, the species the limit
# counts, and all species other than H2 and CO2
_pub = rows("analysis/meoh_literature_inversion_2026_10_05/inlet_inert_literature.csv")
_pub_co = [float(r["CO"]) for r in _pub]
_anchor = next(r for r in _pub if "reference loop" in r["case"])
_three = next(r for r in _pub if "Three-step" in r["case"])
CMN = ("CO", "CH4", "N2")
_cmn = [dsum(r, CMN) for r in _pub]
_nonr = [Decimal(r["non_h2co2_pct"]) for r in _pub]
_four = ["no", "one", "two", "three", "four", "five"][len(_pub)]
ok("MeOH published loops: the anchor loop has no methane, so its limited species are CO and N2",
   Decimal(_anchor["CH4"]) == 0 and len(_pub) == 4)

_pr8 = RB["8_pruning"]["combined"]
ok("Agent pruning, methanol (81 comparisons): bound misses no plant-cost leader", _pr8["leaders_missed"] == 0)
claim_tokens("Agent pruning, methanol (81 comparisons), SI Note 2 and main text",
    ("main text", m_field, [f"spares {_pr8['excluded_fraction'] * 100:.1f}% of the full plant optimizations without missing a single plant-cost leader"]),
    ("SI Notes", section("An automated agent extends the analysis to published and computed catalysts"),
    [f"spares the full optimization for {_frac(_pr8['spared'])[0]} of the {_frac(_pr8['spared'])[1]} candidates ({_pr8['excluded_fraction'] * 100:.1f}%)",
    f"at {_pr8['compute_share'] * 100:.0f}% of the compute"]))
# main text: field result
claim_tokens("Main text: methanol field result, inlet-limited loop (S6) primary and S5 alongside",
    ("main text", m_field, [f"at most {pc(LIM, 2)}% CO, methane and N₂, the limit of the loop that anchors the cost model",
    f"differ in {pl6['disagreements']} of {pl6['groups']} comparisons",
    f"Without the limit the leaders differ in only {pl5['disagreements']} of {pl5['groups']} comparisons",
    f"limiting methane and N₂ alone gives {_frac(_rin['co_excluded_6_86']['disagreements'])[0]}, so it is CO build-up"]),
    ("SI Notes", s8, [f"{lit['candidates']} operating points", f"from {lit['papers_with_candidates']} papers",
    f"and {PL['sets']['second']['operating_points']} from {PL['sets']['second']['papers']} of",
    f"{pl6['groups']} comparisons with {pl6['entries']} entries in {pl6['papers']} papers",
    f"{pl6['disagreements']} of {pl6['groups']} comparisons ({pc(pl6['fraction'], 1)}%; {pc(plci6[0], 1)}–{pc(plci6[1], 1)}%)"]))
# SI Note 3 retains the 6.46% stream-table value, 42 above 5%, and the unlimited fraction.

tokens("SI Note 3: operating-point regret count and unlimited fraction", s8,
       f"in {pl6['disagreements']} of {pl6['groups']} comparisons "
       f"({pc(pl6['fraction'], 1)}%; {pc(plci6[0], 1)}–{pc(plci6[1], 1)}%), "
       f"{pl6['gt5pct']} with a cost gap above 5%",
       f"Without the inlet limit the leaders differ in {pl5['disagreements']} of {pl5['groups']} comparisons "
       f"({pc(pl5['fraction'], 1)}%; {pc(plci5[0], 1)}–{pc(plci5[1], 1)}%)")



def _scan(defn, lim):
    return idf["scenarios"][f"{defn}|{lim}"]


_band = [_scan("frozen", L) for L in idf["limits_pct"] if L != "none" and 5 <= float(L) <= 10]
_sw = _rin["sweep"]
_bd5 = [_sw[k] for k in ("5", "6", "6.86", "8", "10")]
claim_tokens("Main text: 5-10 % stability of the inlet limit (combined set)",
    ("main text", m_field, ["inlet limits of 5–10%"]),
    ("SI Notes", s8, ["the space-time-yield leader differs in " + _and(_frac(_sw[k]['disagreements'])[0] for k in sorted((k for k in _sw if k != "none"), key=float)) + " comparisons"]))
_sweep_limits = sorted((k for k in _sw if k != "none"), key=float)
tokens("SI Note 3: inlet-limit sweep, including 34 disagreements at 15%", s8,
       "Over inlet limits of " + _and(_sweep_limits) + "%",
       "the space-time-yield leader differs in "
       + _and(_frac(_sw[k]['disagreements'])[0] for k in _sweep_limits) + " comparisons")

oc6, sT6, oT6 = k6["other_catalyst"], k6["cat_sameT"], k6["other_temperature"]
_pk = PL6["kinds"]
# catalyst-level comparison (supervisor 2026-10-19): each catalyst at its best measured point, identity rules committed
# before the count (analysis/meoh_catalyst_level_2026_10_19, RULES.md); the point-level count is kept as the total
CL = _j("analysis/meoh_catalyst_level_2026_10_19/summary.json")
_cp, _cs = CL["cat_primary"], CL["cat_strict"]
_cc, _ct, _c50 = _cp["comparison"], _cp["operating_point"], _cp["point_level_50_split"]
_cr = CL["conversion_raised"]["cost_f0.95"]
_ctT = rows("analysis/meoh_catalyst_level_2026_10_19/catalysts_temperature.csv")
_ctD = [r for r in _ctT if r["T_differs"] == "True"]
_ctC = [float(r["T_sty_best"]) - float(r["T_cost_best"]) for r in _ctD if float(r["T_cost_best"]) < float(r["T_sty_best"])]
ok("MeOH catalyst level: the point-level anchor is the pooled S6 result; the 50 split into catalyst changes, one catalyst "
   "leading both and single-catalyst groups; every catalyst-level change is a point-level disagreement",
   CL["point_level_total"] == {"groups": pl6["groups"], "changed": pl6["disagreements"], "gt5pct": pl6["gt5pct"],
                               "papers": pl6["papers"]}
   and _c50["catalyst_level_change"] + _c50["same_catalyst_leads_both"] + _c50["single_catalyst_groups"]
   == pl6["disagreements"] and _c50["catalyst_level_change_not_in_point_level"] == 0
   and _c50["catalyst_level_change"] == _cc["changed"]
   and all(CL["conversion_raised"][k]["cat_primary"]["changed"] == _cr["cat_primary"]["changed"]
           for k in ("cost_f0.9", "cost_f0.99", "cost_two_sided"))
   and len(_ctT) == _ct["catalysts_with_2plus_T"] and len(_ctD) == _ct["plant_T_differs"]
   and len(_ctC) == _ct["plant_colder"])
_glr = [r for r in rows("analysis/meoh_catalyst_level_2026_10_19/groups_catalyst_level.csv")
        if r["doi"] == "10.1021/acscatal.5c05984"]
ok("MeOH catalyst level, per gram of Re: the Re/TiO2 group changes catalyst (above 5 %) per gram of catalyst, and its "
   "per-gram-of-Re leader (1 wt% Re) is its plant-cost leader",
   len(_glr) == 1 and _glr[0]["changed"] == "True" and float(_glr[0]["gap"]) > 0.05
   and _glr[0]["plant_leader"] == "1wt%re/tio2")
_gm6 = [r for r in rows("analysis/meoh_literature_inversion_2026_10_05/group_metrics_inlet_limit.csv")
        if r["top1_mismatch"] == "True"]
_sT = [r for r in _gm6 if r["kind"] == "other catalyst, same temperature"]
_sT5 = [r for r in _sT if float(r["regret"]) > 0.05]
ok("MeOH S6 kinds recomputed from the frozen group metrics",
   len(_gm6) == n6 and len(_sT) == sT6["groups"] and len(_sT5) == sT6["gt5pct"]
   and len({r["doi"] for r in _sT5}) == sT6["gt5pct_papers"])
lS6, lX6, lS5, lX5 = F6["leaderboard_SMeOH"], F6["leaderboard_X"], F5["leaderboard_SMeOH"], F5["leaderboard_X"]
_qX6, _qS6, _qS5 = PL6["leaderboard_X"], PL6["leaderboard_SMeOH"], PL5["leaderboard_SMeOH"]
tokens("Main text: other laboratory metrics (combined set, both loops)", m_field,
       f"ranking by conversion disagrees in {_qX6['disagreements']} of {_qX6['groups']} comparisons and ranking by methanol "
       f"selectivity in {_qS6['disagreements']},")
ok("MeOH combined set: conversion misses more often than STY; selectivity is the worst proxy without the limit",
   _qX6["disagreements"] > pl6["disagreements"]
   and _qS5["disagreements"] > max(pl5["disagreements"], PL5["leaderboard_X"]["disagreements"],
                                   PL5["leaderboard_XS"]["disagreements"]))
_yx5 = V["leaderboard_X_times_S"]["top1_mismatch_groups"]
ok("MeOH laboratory metrics: conversion one short of space-time yield with the limit, larger selectivity misses, "
   "selectivity the worst proxy without the limit",
   0 < n6 - lX6["disagreements"] <= 1
   and lS6["median_regret_disagreements"] > max(lX6["median_regret_disagreements"],
                                                _quantiles(sorted(float(r["regret"]) for r in _gm6), [0.5])[0])
   and lS5["disagreements"] > max(n5, lX5["disagreements"], _yx5))
ok("MeOH S5 alternative leaderboards equal the frozen variants",
   (lS5["disagreements"], lX5["disagreements"]) == (V["leaderboard_S_MeOH"]["top1_mismatch_groups"],
                                                    V["leaderboard_X"]["top1_mismatch_groups"]))

# main text: robustness
km1_6, km2_6, km1_5 = st6["noise"]["meas_k1"], st6["noise"]["meas_k2"], st5["noise"]["meas_k1"]
nfq = km1_6["sty_leader_differs_from_reported_q025_q975"]
ni = F6["near_infeasibility"]
wb6, wb5 = F6["without_bansode"], F5["without_bansode"]
ae6, ae5 = led["all_entries_result"]["S6_6_86pct"], led["all_entries_result"]["S5"]
cl6 = F6["closure_ge95"]
sp6 = [ssp["S6"][b]["disagreements"] for b in ("low", "high")]
ic6, ic5 = F6["inert_co"], F5["inert_co"]
cc6 = ccs["S6"]["variants"]["composition_3y"]
cr6, cr5 = cvr["printed|cost_f0.95"], cv5["printed|cost_f0.95"]
co6 = F6["co_excluded_ch4_n2"]
ok("MeOH S6 sensitivities agree across the merged analyses",
   (ae6["different_leader"], ae6["groups"]) == (V["all_entries_inlet_limit"]["top1_mismatch_groups"],
                                                V["all_entries_inlet_limit"]["groups"])
   and (ae5["different_leader"], ae5["groups"]) == (V["all_entries"]["top1_mismatch_groups"], V["all_entries"]["groups"])
   and ic6["disagreements"] == V["inert_opt_inlet_limit"]["top1_mismatch_groups"]
   and ic5["disagreements"] == V["inert_opt"]["top1_mismatch_groups"]
   and (co6["disagreements"], co6["gt5pct"]) == (_scan("true_inert", "6.86")["different_leader"],
                                                  _scan("true_inert", "6.86")["gt5pct"])
   and ssp["S6"]["convention"]["disagreements"] == n6 and ccs["S6"]["variants"]["off"]["disagreements"] == n6
   and all((cvr[f"printed|{k}"]["top1_mismatch_groups"], cvr[f"printed|{k}"]["gt5pct"])
           == (cr6["top1_mismatch_groups"], cr6["gt5pct"]) for k in ("cost_f0.9", "cost_f0.99", "cost_two_sided")))
_var81 = [_frac(RB["6_split"]["S6"]["combined"][b_]["disagreements"])[0] for b_ in ("low", "high")] + [
    PL6["inert_co"]["disagreements"], _frac(RB["3_co_bound"]["combined"]["high|6.86"]["disagreements"])[0],
    _frac(RB["5_catalyst"]["S6"]["combined"]["composition_3y"]["disagreements"])[0],
    _frac(RB["4_conversion"]["S6"]["combined"]["printed|cost_f0.95"]["disagreements"])[0]] + [
    int(x) for x in RB["9_plant_variants"]["combined"]["S6"].split(" ")[0].split("-")]
claim_tokens("Main text: S6 robustness (sampling, measurement, variants)",
    ("main text", m_field, [f"{_frac(_rn['kept_ge90pct']['k1'])[0]} of the {_frac(_rn['kept_ge90pct']['k1'])[1]} persisting in at least 90% of {st6['noise_model']['draws']:,} re-measurements",
    "every closure, price and plant-term variant tested"]),
    ("SI Notes", s8, [f"{PL6['without_bansode']['disagreements']} of {PL6['without_bansode']['groups']}",
    f"with recycled CO treated as inert ({PL6['inert_co']['disagreements']} of {pl6['groups']})",
    f"the plant-term variants {RB['9_plant_variants']['combined']['S6'].split()[0].replace('-', '–')} of {pl6['groups']}"]))
tokens("SI Note 3: measurement noise alone changes the laboratory leader", s8,
       f"measurement noise alone changes a paper's space-time-yield leader in "
       f"{_rn['noise_only_sty_leader_changes']['mean']:.1f} comparisons on average (95% range "
       f"{_rn['noise_only_sty_leader_changes']['range95'][0]:.0f}–"
       f"{_rn['noise_only_sty_leader_changes']['range95'][1]:.0f})")
ok("MeOH combined robustness: every first-set anchor reproduced in the combined reruns",
   all(RB[k][s]["first_set_anchor_reproduced"] for k in ("1_noise", "4_conversion", "5_catalyst", "6_split", "7_all_entries")
       for s in ("S6", "S5")) and all(RB[k]["first_set_anchor_reproduced"] for k in ("2_inlet", "3_co_bound", "8_pruning")))
_nb = bnd["scenarios"]["S6"]["near_infeasibility"]
ok("MeOH S6 near-infeasible: every one meets the twofold-cost rule (as the text describes them)",
   _nb["by_criterion"]["lab_cost_gt2x_S5"] == ni["near-infeasible"]["groups"] == _nb["near_infeasible"]["groups"]
   and ni["ordinary"]["groups"] + ni["near-infeasible"]["groups"] == n6)

# main text: mechanism and the InNi3C0.5 example
mc6, mc5 = F6["mechanism"], F5["mechanism"]
_none = _scan("frozen", "none")
claim_tokens("Main text: by-product mechanism of the S6 disagreements",
    ("main text", m_field, [f"the reactor feed would carry a median {pc(_rin['inlet_co_without_limit']['median'], 1)}% CO",
    f"against {min(_pub_co):.1f}–{max(_pub_co):.1f}% in published loop designs",
    f"the plant-cost leader is the more selective catalyst in {PL6['mechanism']['plant_leader_more_selective']['count']} of the {PL6['mechanism']['disagreements']} disagreements"]),
    ("SI Notes", s8, [f"makes less CO in {PL6['mechanism']['plant_leader_less_CO']['count']}"]))
_gm40 = {r["group"] for r in rows("analysis/meoh_literature_inversion_2026_10_05/group_metrics.csv")}
_ec = [r for r in rows("analysis/meoh_inlet_definition_2026_10_12/entry_costs.csv") if r["group"] in _gm40]
_co_none = sorted(float(r["co_frozen_none"]) for r in _ec)
_coq = _quantiles(_co_none, [0.1, 0.9])
ok("MeOH S5 inlet CO: median of the 310 scored entries equals the merged summary",
   len(_ec) == P0["entries"] and abs(_quantiles(_co_none, [0.5])[0] - _none["co_share_median"]) < 1e-9)
tokens("Main text: inlet CO without the limit, median", m_field,
       f"median {pc(_rin['inlet_co_without_limit']['median'], 1)}% CO")
# The 90th percentile remains source-checked in SI Note 3: species counted and the published loop inlets.
_cand = rows("analysis/meoh_literature_inversion_2026_10_05/literature_candidates.csv")
_gm5 = {r["group"]: r for r in rows("analysis/meoh_literature_inversion_2026_10_05/group_metrics.csv")}
_ex = []
for g in _gm6:      # S6 disagreements whose STY leader is on m-ZrO2, S6 plant leader on SiO2, and no S5 disagreement
    if ("InNi3C0.5/m-ZrO2" in g["upstream_winner"] and "InNi3C0.5/SiO2" in g["economic_winner"]
            and _gm5[g["group"]]["top1_mismatch"] == "False"):
        a = next(c for c in _cand if c["group"] == g["group"] and c["catalyst"] == g["upstream_winner"])
        b = next(c for c in _cand if c["group"] == g["group"] and c["catalyst"] == g["economic_winner"])
        _ex.append((g["group"], [
            f"on m-ZrO₂ it gives the highest space-time yield ({pc(float(a['X']), 1)}% conversion, "
            f"{pc(float(a['SMeOH']))}% methanol selectivity, {pc(float(a['SCO']))}% CO) but needs a "
            f"{pc(float(a['purge_recycled_opt_inlet']), 1)}% purge and costs {float(a['cost_recycled_opt_inlet']):,.0f} euros per tonne",
            f"on SiO₂ ({pc(float(b['X']), 1)}% conversion, {pc(float(b['SMeOH']))}% selectivity, "
            f"{pc(float(b['SCO']))}% CO) it runs at {pc(float(b['purge_recycled_opt_inlet']), 1)}% purge for "
            f"{float(b['cost_recycled_opt_inlet']):,.0f}"]))
_hit = [e for e in _ex if all(n in m_field for n in e[1])]
ok("Main text: InNi3C0.5 example (inlet-limited costs and purge) matches one frozen group",
   len(_hit) == 1, "" if _hit else "expected one frozen group: " + " || ".join("; ".join(e[1]) for e in _ex))

_bd = bnd["bansode_doi"]
_bgm5 = [r for r in _gm5.values() if r["doi"] == _bd]
_maxdoi = [max(rows(f"analysis/meoh_literature_inversion_2026_10_05/{f}"), key=lambda r: float(r["regret"]))["doi"]
           for f in ("group_metrics.csv", "group_metrics_inlet_limit.csv")]
ok("MeOH: the high-pressure Cu/Al2O3 study supplies the largest regret in both loops",
   _maxdoi == [_bd, _bd] and len(_bgm5) == bnd["bansode_groups"] and "c2cy20604h" in V["without_paper_with_most_groups"]["variant"])
tokens("Main text: the high-pressure Cu/Al2O3 study (combined set)", m_field,
       f"supplies {PL6['bansode']['groups']} comparisons[36] gives the largest regrets without the limit")
ok("MeOH combined set: the Cu/Al2O3 study has the largest regret without the limit, not with it",
   PL5["bansode"]["is_largest"] and not PL6["bansode"]["is_largest"] and PL6["bansode"]["groups"] == bnd["bansode_groups"])

# main text: the four Re/TiO2 states of the hand-built case under the inlet limit. They are the Table 4 entries of the
# extracted Gothe group at 100 bar, H2/CO2 4 and 10 NL/g/h whose conversion and selectivities equal the hand-built
# states; their inlet-limited costs come from the frozen column cost_recycled_opt_inlet.
_hb = rows("data/meoh/meoh_candidate_ranking_D01v3.csv")
_go = [c for c in _cand if c["group"].startswith("10.1021/acscatal.5c05984 | 100 bar | H2/CO2 4 | 10 NL/g/h")]


def _hb_entry(h):
    hit = [c for c in _go if c["catalyst_key"] == f"{h['Re_wt%']}wt%re/tio2" and float(c["T_C"]) == float(h["T_C"])
           and all(abs(float(c[a]) - float(h[b])) < 1e-9 for a, b in (("X", "X_CO2"), ("SMeOH", "S_MeOH"), ("SCH4", "S_CH4")))]
    return hit[0] if len(hit) == 1 else None


_hbe = [(h, _hb_entry(h)) for h in _hb]
ok("MeOH Re/TiO2: each hand-built state is exactly one extracted Table 4 entry", all(e for _, e in _hbe) and len(_hbe) == 4)
if all(e for _, e in _hbe):
    _hbs = sorted(_hbe, key=lambda t: float(t[1]["cost_recycled_opt_inlet"]))
    _hbw = next(t for t in _hbe if t[0]["rank_STY_per_gRe"] == "1")          # space-time-yield winner per gram of Re
    _hbr = float(_hbw[1]["cost_recycled_opt_inlet"]) / float(_hbs[0][1]["cost_recycled_opt_inlet"]) - 1
    # The 6.6% inlet-limited regret is no longer stated in either manuscript file.
    # Retain the cross-source check against the independently frozen S6 group table;
    # do not require the author to restore a deleted secondary claim.
    _hbg = next(g for g in _gm6 if g["group"] == _hbw[1]["group"])
    ok("MeOH source-only: retired inlet-limited Re/TiO2 regret agrees across frozen tables",
       _hbs.index(_hbw) == 1
       and f"{float(_hbs[0][1]['cost_recycled_opt_inlet']):.3f}" == _hbg["economic_winner_cost"]
       and pc(_hbr, 1) == pc(float(_hbw[1]["cost_recycled_opt_inlet"]) / float(_hbg["economic_winner_cost"]) - 1, 1),
       f"not stated in main text or SI; cross-source costs agree at printed precision; source regret {pc(_hbr, 1)}%, rank {_hbs.index(_hbw) + 1}")


# Supplementary Note 3
_other = sorted((x for r, x in zip(_pub, _cmn) if r not in (_anchor, _three)), reverse=True)
_cmn_rng = f"{dfmt(min(_cmn), 1)}–{dfmt(max(_cmn), 1)}%"
_nonr_rng = f"{dfmt(min(_nonr), 1)}–{dfmt(max(_nonr), 1)}%"
tokens("SI Note 3: species counted and the published loop inlets", s8,
       f"(CO, methane and N₂) to {pc(LIM, 2)}%",
       f"The published loop designs carry {_cmn_rng} CO, methane and N₂ at the reactor inlet: "
       f"{dfmt(dsum(_anchor, CMN), 2)}% in the anchor loop ({dfmt(Decimal(_anchor['CO']), 2)}% CO, "
       f"{dfmt(Decimal(_anchor['N2']), 2)}% N₂; {dfmt(Decimal(_anchor['non_h2co2_pct']), 2)}% with methanol and water; the "
       f"cost model's limit is {pc(LIM, 2)}%), {dfmt(dsum(_three, CMN), 2)}% in its three-reactor variant, and "
       f"{_and(dfmt(x, 2) + '%' for x in _other)} in two further designs ({_nonr_rng} of all species other than H₂ and "
       f"CO₂)",
       f"reactor-inlet CO is a median {pc(_rin['inlet_co_without_limit']['median'], 1)}% (10th and 90th percentiles "
       f"{pc(_rin['inlet_co_without_limit']['p10'], 1)}% and {pc(_rin['inlet_co_without_limit']['p90'])}%), against "
       f"{min(_pub_co):.1f}–{max(_pub_co):.1f}% in the published designs")
ok("MeOH S6: CO is more than 80 % of the limited inlet quantity at the limited optimum",
   _scan("frozen", "6.86")["co_fraction_of_nonreactive_median"] > 0.8)
r1_6 = {r["threshold"]: r for r in st6["regret_threshold_curve"]}
r1_5 = {r["threshold"]: r for r in st5["regret_threshold_curve"]}
tokens("SI Note 3: operating points of the extraction set", s8,
       f"{lit['candidates']} operating points", f"from {lit['papers_with_candidates']} papers of the extraction set")
ok("MeOH S6 regret thresholds equal the frozen regret bins",
   (r1_6[0.01]["groups"], r1_6[0.05]["groups"], r1_6[0.1]["groups"])
   == (S6["regret_bins"]["gt1pct"]["groups"], S6["regret_bins"]["gt5pct"]["groups"], S6["regret_bins"]["gt10pct"]["groups"]))
_lims = [L for L in idf["limits_pct"] if L != "none"]
_ti = [_scan("true_inert", L)["different_leader"] for L in _lims]
# paper-bootstrap 95 % interval of the excess over the unlimited loop along the limit scan (merged boundary analysis)
_bsc = sorted(((v["limit"], v["bootstrap"]) for k, v in bnd["scenarios"].items() if k.startswith("lim") or k == "S6"),
              key=lambda t: t[0])


def _above_until(metric):
    """Largest limit up to which the lower end of the interval of the excess stays above zero at every limit."""
    up = None
    for lim, b in _bsc:
        if b[metric + "_minus_S5"]["ci95"][0] <= 0:
            break
        up = lim
    return up


_ex_dl, _ex_g5 = _above_until("different_leader"), _above_until("gt5pct")
_ex_gone = next(lim for lim, b in _bsc if all(b[x + "_minus_S5"]["ci95"][0] <= 0 for x in ("different_leader", "gt5pct")))
ok("MeOH inlet limit: the excess over S5 (paper bootstrap) vanishes at the limit that follows the last one above zero",
   None not in (_ex_dl, _ex_g5) and _ex_g5 <= _ex_dl < _ex_gone
   and [lim for lim, _ in _bsc][[lim for lim, _ in _bsc].index(_ex_dl) + 1] == _ex_gone)
ok("MeOH all entries: exactly the groups without an S6 verdict in the ledger are missing from the inert-limited count",
   sum(1 for r in rows("analysis/meoh_inlet_definition_2026_10_12/group_ledger.csv")
       if r["all_entries_S6_different_leader"] == "") == ae["groups"] - ae6["groups"])
_rob_g = {r["group"] for r in rows(ROB + "stats_s6/group_noise_probabilities.csv")
          if r["observed_mismatch"] == "True" and float(r["p_mismatch_meas_k1"]) >= 0.9}
_s6g = [r for r in rows(ROB + "s6_groups.csv") if r["mismatch"] == "True"]
_ord = {r["group"] for r in _s6g if r["cls"] == "ordinary"}


def _n_ordinary(threshold):
    return sum(not (float(r["regret"]) > 1 or float(r["sty_leader_cost_vs_S5"]) > threshold) for r in _s6g)


ok("MeOH S6 noise-robust and ordinary disagreements recomputed from the group outputs",
   len(_rob_g) == km1_6["observed_mismatches_kept_in_ge_90pct"] and len(_ord) == ni["ordinary"]["groups"]
   and len(_rob_g & _ord) == rob["noise_robust_S6_k1_ordinary"]["ordinary"] and _n_ordinary(2) == len(_ord))
pbs = _j("analysis/meoh_literature_inversion_2026_10_05/purge_boundary_summary.json")
_pbb, _pbx = pbs["boundary"], pbs["boundary"]["at_extended_optimum"]
_pext = [r for r in rows("analysis/meoh_literature_inversion_2026_10_05/group_metrics_purge_extended.csv")
         if r["top1_mismatch"] == "True"]
ok("MeOH S5 purge optimum at the 0.5 % grid floor for every entry", _pbb["canonical_optimum_at_0p5pct"] == pbs["entries"])

# Methods: definition of the limit and of near-infeasibility
_lim_scen = [v["limit"] for k, v in bnd["scenarios"].items() if k.startswith("lim")]
tokens("Methods: inlet limit, its scan and the near-infeasibility rule", supplementary_method('Published methanol comparisons'),
       f"stays at or below {pc(LIM, 2)}%, the cost model's limit for the loop that anchors it "
       f"({dfmt(dsum(_anchor, CMN), 2)}% CO and N₂ in its stream table, {dfmt(Decimal(_anchor['non_h2co2_pct']), 2)}% with "
       f"methanol and water",
       f"limits of {pc(min(_lim_scen))}–{pc(max(_lim_scen))}%, spanning the {_cmn_rng} of CO, methane and N₂ "
       f"({_nonr_rng} of all species other than H₂ and CO₂) in {_four} published loop designs",
       "exceeds twice its cost without the limit or the regret exceeds 100%")
ok("Methods: near-infeasibility rule is the merged rule (regret > 1 or > 2x the S5 cost)",
   "regret > 1" in bnd["near_infeasible_rule"] and "2x" in bnd["near_infeasible_rule"]
   and abs(bnd["published_range"][0] - min(float(r["non_h2co2_pct"]) for r in _pub) / 100) < 1e-4
   and abs(bnd["published_range"][1] - max(float(r["non_h2co2_pct"]) for r in _pub) / 100) < 1e-4)

# Abstract and Discussion
# since 2026-10-15 the abstract and Discussion lead with the inlet-limited loop (S6, approved primary) and give the
# unlimited loop (S5) in the Discussion and Results; the alloy count is reported in the Results only
tokens("Abstract headline numbers", main_section_h2("Abstract"),
       f"nor is the catalyst with the highest rate in {NPL['mismatch']} of {NPL['groups']} ammonia comparisons "
       f"({pc(NPL['fraction'])}%)")
tokens("Results: alloy count and field counts", text, f"{ext_all['costed']:,} priced surfaces",
       f"ACSA extracted {fd['papers_in_set'] + fx['screening_with_si']['included']} primary ammonia-synthesis papers "
       f"(Supplementary Tables 2 and 2b)")
tokens("Discussion: field-level shares", main_section_h2("Discussion"),
    "In a third of the methanol comparisons between catalysts and in more than a quarter of the ammonia comparisons",
    "the catalyst a paper ranks first is not the one a plant would build",
    "the temperature at which a catalyst performs best in the laboratory is usually not where a plant would run it")
_bl = _j("analysis/validation_meoh_prospective_2026_10_13/results.json")["primary (printed, corrected)"]["S6"]
_bls = _bl["stats"]
ok("MeOH blind rule: the committed predictions equal the rule on every comparison of the second set",
   _bl["rule"] == "S" and _bl["blind_predictions_equal_rule"] == _bls["rule_accuracy"]["denominator"] == 41)
# 2026-10-19: the blind selectivity-rule prediction is no longer reported in the main text
_cap = _j("analysis/meoh_field_pooled_2026_10_15/cap_robustness/summary.json")
ok("MeOH inlet-limit robustness: 81 groups, caps 5-10%, 5% tolerance",
   _cap["groups"] == pl6["groups"] and _cap["caps_pct"] == ["5", "6", "6.86", "8", "10"] and _cap["tolerance"] == 0.05)
tokens("SI Note 3: inlet-limit robustness of the plant-cost leader", s8,
       f"is within 5% of the cheapest operating point at every limit from 5 to 10% in "
       f"{_cap['s6_leader']['within_tolerance']} of {_cap['groups']} comparisons, against "
       f"{_cap['minimax']['within_tolerance']} for an oracle that knows every limit's costs (the leader at 6.86% is that "
       f"oracle's choice in {_cap['s6_leader_is_minimax_choice']}), {_cap['selectivity']['within_tolerance']} for the most "
       f"selective entry and {_cap['sty_leader']['within_tolerance']} for the paper's space-time-yield leader")

# Response-surface validation of both noise results (S6 primary and S5) against exact runs of complete replicates
pb = json.loads((ROOT / "analysis/meoh_plant_benchmark_2026_10_06/sensitivity_summary.json").read_text(encoding="utf-8"))
st = json.loads((ROOT / "analysis/meoh_main_result_stats_2026_10_06/summary.json").read_text(encoding="utf-8"))
_v, _v6, _v5 = st["validation"], st6["validation"], st5["validation"]
_val6 = rows(ROB + "stats_s6/validation.csv")
_k1 = [r for r in _val6 if r["scenario"] == "meas_k1"]
_k1_diff = sum(int(r["groups_with_different_verdict"]) for r in _k1)
ok("MeOH response-surface validation: per-replicate rows sum to the S6 total; the S5 rerun equals the frozen S5 analysis",
   sum(int(r["groups_with_different_verdict"]) for r in _val6) == _v6["verdict_disagreements_total"]
   and len(_val6) * g6 == _v6["verdicts_compared"] and len(_k1) == _v6["replicates_per_scenario"]
   and (_v5["verdict_disagreements_total"], _v5["verdicts_compared"]) == (_v["verdict_disagreements_total"],
                                                                          _v["verdicts_compared"]))
_rs_s6 = (f"{_v6['verdict_disagreements_total']} of {_v6['verdicts_compared']:,} group verdicts ({_k1_diff} of "
          f"{len(_k1) * g6:,} at the reported noise level) in the inert-limited loop")
tokens("Methods: response-surface validation of the primary (S6) noise result", supplementary_method('Published methanol comparisons'), _rs_s6)
tokens("MeOH literature: response-surface validation in Methods (S5 runs)", supplementary_method('Published methanol comparisons'),
       f"{_rs_s6} and {_v['verdict_disagreements_total']} of {_v['verdicts_compared']:,} without the limit differ from "
       f"exact runs of complete replicates")
_pv = [v["top1_mismatch_groups"] for k, v in pb["variants"].items()
       if not k.startswith(("catalyst", "combined", "baseline"))]
_pvc = _j("analysis/meoh_field_pooled_2026_10_15/robustness/plant_variants/sensitivity_summary.json")
_pvx = {k: v["top1_mismatch_groups"] for k, v in _pvc["variants"].items()
        if not k.startswith(("catalyst", "combined", "baseline"))}
_pv5 = [v for k, v in _pvx.items() if "|" not in k]
_pv6 = [v for k, v in _pvx.items() if k.endswith("|S6")]
ok("MeOH plant variants, combined set: baseline equals the combined S5 result; S5 and S6 variants paired",
   _pvc["check"]["baseline_top1"] == f"{pl5['disagreements']}/{pl5['groups']}" and len(_pv5) == len(_pv6) > 0)
tokens("MeOH plant benchmark: loop, recycle and price variants (combined set)", supplementary_method("CO₂-to-methanol"),
       f"leaves the space-time-yield disagreement at {min(_pv5)}–{max(_pv5)} of {pl5['groups']} comparisons without the "
       f"inlet limit and {min(_pv6)}–{max(_pv6)} of {pl6['groups']} with it (Extended Data Fig. 4)")
ok("MeOH plant benchmark: baseline reproduces the S5 headline",
   pb["check"]["baseline_top1"] == f"{P0['top1_mismatch_groups']}/{P0['groups']}")

# main-text summaries written in the 2026-10-07 compression (the full statements live in the Supplementary Notes)
m_feru = main_section("What Ru must cost to match fused iron")
_layer = {r["metal"]: r for r in rows(FEB + "inversion_layer_common_reference.csv")}
_repl = {k: float(_layer[k]["annualized_replacement_cost_USD_t_NH3"]) for k in ("Fe", "Ru", "Os")}
_ru_win = sum(r["economic_winner"] == "Ru" for r in draws)
claim_tokens("Main text: layer-wise reversal, process optimization moves the gap into compression, descriptor winners",
    ("main text", m_feru, [f"at {_repl['Fe']:.3f} US dollars per tonne of annualized metal replacement for Fe against {_repl['Ru']:.2f} for Ru",
    f"Priced as iron, at {r8['price_USD_kg']:.0f} US dollars per kilogram, Ru wins ({r8['total_cost_USD_t']:.2f} against {fe['total_cost']:.2f} US dollars per tonne)",
    f"places parity at {float(parity['price_USD_kg']):.0f} US dollars per kilogram",
    "Process optimization cannot remove it, only move it",
    f"Ru retreats to about {ru['T_C']:.0f} °C and {ru['P_bar']:.0f} bar, where a small bed holds little metal, while Fe runs near {fe['T_C']:.0f} °C and {fe['P_bar']:.0f} bar",
    f"the {gap:.2f} US dollars per tonne between them reappears mainly as fresh-feed compression (+{_pools['fresh_compression_electricity']:.3f}), metal inventory (+{_pools['metal_inventory']:.3f}) and compressor capital (+{_pools['compressor_CAPEX']:.3f})",
    f"first in {100 * fe_win / len(draws):.1f}% of {len(draws):,} descriptor samples"]),
    ("SI Notes", s2_full, [f"{_yaml_num(manifest, 'max_catalyst_bed_m3'):.0f} m³ bed-volume limit"]))
_cmin = min(float(r["Ru_minus_Fe_USD_t"]) for r in cmc_draws)
claim_tokens("Main text: economic Monte Carlo, Fe cheaper in every draw and the smallest difference",
    ("main text", m_feru, [f"Fe is cheaper in every one of {len(cmc_draws):,} draws of metal prices, capital cost, electricity price and catalyst lifetime"]),
    ("SI Notes", s2_full, [f"minimum sampled Ru-Fe cost difference of {_cmin:.3f} US dollars per tonne"]))
ok("NH3 economic Monte Carlo: Ru dearer than Fe in every draw", _cmin > 0)
tokens("SI Note 7: layer-wise check, replacement cost at the common reference against the total gap", s2_full,
       f"the annualized metal replacement is {_repl['Fe']:.3f} US dollars per tonne of NH₃ for Fe, {_repl['Ru']:.2f} for Ru "
       f"and {_repl['Os']:.2f} for Os",
       f"leaves Ru less costly than Fe ({r8['total_cost_USD_t']:.3f} versus {fe['total_cost']:.3f} US dollars per tonne of NH₃)",
       f"the Ru - Fe difference goes from {_repl['Ru'] - _repl['Fe']:.2f} US dollars per tonne in metal replacement at the "
       f"common reference to {gap:.3f} in total, and most of it moves into fresh-feed compression, metal inventory and "
       f"compressor capital")
ok("Layer-wise check: replacement order Fe < Ru < Os; process optimization does not close the gap (total Ru - Fe exceeds "
   "the replacement-cost gap) and fresh-feed compression carries the largest share",
   _repl["Fe"] < _repl["Ru"] < _repl["Os"] and gap > _repl["Ru"] - _repl["Fe"] > 0
   and _pos[0] == "fresh_compression_electricity" and _pools["fresh_compression_electricity"] > gap / 2
   and [r_["metal"] for r_ in sorted(_layer.values(), key=lambda r_: int(r_["activity_rank"]))] == det["activity_order"][:3])
ok("Descriptor samples: most Ru wins are Fe-bed-infeasible draws",
   2 * sum(r["economic_winner"] == "Ru" and str(r.get("Fe_feasible", "")).strip() in ("0", "False", "false")
           for r in draws) > _ru_win)
tokens("Main text: ammonia extraction recall", m_field, f"{tot['matched']} of {tot['curated']} entries")
_ea = json.loads((ROOT / "analysis/verify_2026_10_08/errata_adjudication_summary.json").read_text(encoding="utf-8"))
_ec = _ea["confirmed"]
tokens("Methods: curated-data errors counted by root cause (errata adjudication)", supplementary_method("Adaptive Catalyst Screening Agent"),
       f"{_ec['root_causes']} root causes", f"{_ec['value_cells_error_rules']} cells")
ok("Methods: no first-pass errata count (331 cells / 148 / 280)",
   not re.search(r"\b331 cells\b|\b280 cells\b|\b148 (?:errors|rules)\b", text))
# ----- Fe-Ru: Ru inventory financing, measured frontier kinetics and the staged converter ---------------------------
# Supervisor decisions of 2026-10-12: report both conventions for the Ru inventory (no financing charge, as the benchmark
# model; financed at the 12 % equipment rate) wherever the KAAP comparison appears; replace the Fe-Ru kinetics by measured
# rate laws; add the staged converter. Sources: analysis/nh3_ru_net_recovery_boundary_2026_10_12 (#57),
# nh3_ru_metal_financing_evidence_2026_10_12 (#70), nh3_staged_converter_2026_10_12 (#75),
# nh3_frontier_provenance_2026_10_13 (measured-kinetics break-even rates), each in its nh3_1_2/ sub-folder; the descriptor
# apparent orders from analysis/verify_2026_10_14_descriptor_orders. Model-independent inputs keep their single files:
# the lease contracts (pbf_catalyst_lease_contracts.csv), the rate-law validation (validation_summary.json), the
# staged-converter parameters (parameters.yaml) and the cash-flow code (lifecycle_cashflow.py).


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


SC = "analysis/nh3_staged_converter_2026_10_12/"
SC12 = SC + V12 + "/"           # 1.2 kinetics swap; converter files are byte copies (staged_invariance.json)
dcf = _j(f"analysis/nh3_ru_net_recovery_boundary_2026_10_12/{V12}/lifecycle_dcf_report.json")
fin = _j(f"analysis/nh3_ru_metal_financing_evidence_2026_10_12/{V12}/summary.json")
leases = rows("analysis/nh3_ru_metal_financing_evidence_2026_10_12/pbf_catalyst_lease_contracts.csv")
ksw = _j(SC12 + "kinetics_swap.json")
val = _j(SC + "validation_summary.json")
ssum = _j(SC12 + "summary.json")
sbnd = _j(SC12 + "boundary_summary.json")
_par = (ROOT / SC / "parameters.yaml").read_text(encoding="utf-8")
fsw = _j(f"analysis/nh3_frontier_provenance_2026_10_13/{V12}/frontier_swap.json")
fsw_rob = rows(f"analysis/nh3_frontier_provenance_2026_10_13/{V12}/frontier_swap_robustness.csv")
# supervisor 2026-10-19: each catalyst optimized only inside the pressure range its rate law was fitted on. Fused iron:
# Keestra et al. 2025 Model 3 (1-324 bar, KM1R-1964 activity), Ru/C: Rossetti 2006 (50-100 bar); the manuscript's
# measured-kinetics numbers come from analysis/nh3_fe_inrange_kinetics_2026_10_19 (Dyson-Simon outputs above stay the
# provenance the in-range scripts reproduce first)
IRD = "analysis/nh3_fe_inrange_kinetics_2026_10_19/"
_ir_all = _j(IRD + "results.json")
IR = _ir_all["Fe_Keestra"]["Keestra KM1R-1964, source Kf"]
IRV = _j(IRD + "validation.json")
IRR = _j(IRD + "robustness.json")
IRS = _j(IRD + "staged_KM1R_1964_summary.json")
ok("Fe-Ru financing and frontier sources are the NH3-FINAL-1.2 ports",
   fin["model"]["label"] == "NH3-FINAL-1.2" and fin["model"]["run"] == RUN.name
   and ksw["frozen_anchor_check"]["model"]["run"] == RUN.name and fsw["model"]["run"] == RUN.name
   and abs(fin["model"]["headline_Fe_USD_t_reproduced"] - m["Fe"]["feasible"]["total_cost"]) < 1e-12
   and abs(ksw["frozen_anchor_check"]["model"]["Ru_activity_multiple_for_parity_descriptor"]
           - bw["Ru_activity_break_even_multiplier"]) < 1e-5)


def _ynum(key):
    return float(re.search(rf"^\s*{key}:\s*([-+\d.eE]+)", _par, re.M).group(1))


def _ylist(key):
    return [float(x) for x in re.search(rf"^\s*{key}:\s*\[([^\]]*)\]", _par, re.M).group(1).split(",")]


def _yrange(block, unit):
    v = re.search(rf"^  {block}:.*?^    validity:\s*\"([^\"]*)\"", _par, re.M | re.S).group(1)
    return [int(x) for x in re.search(rf"(\d+)-(\d+) {unit}\b", v).groups()]


f0, f12 = dcf["flagship_results"]["zero_carrying_ideal"], dcf["flagship_results"]["project_12pct_ideal"]
geo = dcf["flagship_geometry"]
hl, pbf = fin["headline"], fin["pbf_fixed_rates_pct"]
_rates = sorted(float(r["annual_rate_pct"]) for r in leases)
_fy = [int(y) for r in leases for y in re.findall(r"FY(\d{4})", r["first_disclosed_in"])]
_states12 = ksw["frozen_anchor_check"]["model"]["version"]          # the 1.2 port runs on the 1.2 states only
_rc = [v for v in ksw["variants"] if v["sizing"] == "plug" and v["scale"] == "source" and v["states"] == _states12]
kh = _rc[0]                                           # headline: plug flow, measured rates, NH3-FINAL-1.2 states
r_hi, r_lo = max(_ylist("Ru_recovery")), min(_ylist("Ru_recovery"))
i_lo, i_hi = min(_ylist("metal_financing_rate")), max(_ylist("metal_financing_rate"))
rc0 = kh["Ru_C_supported"][f"cashflow {i_lo * 100:.0f}% r {r_hi}"]
rc12 = kh["Ru_C_supported"][f"cashflow {i_hi * 100:.0f}% r {r_hi}"]
ok("NH3 measured kinetics: frozen Fe and Ru optima reproduced before the swap",
   len(_rc) == 1 and abs(ksw["frozen_anchor_check"]["Fe"]["cost"] - m["Fe"]["feasible"]["total_cost"]) < 1e-5
   and abs(ksw["frozen_anchor_check"]["Ru"]["cost"] - m["Ru"]["feasible"]["total_cost"]) < 1e-5
   and all(v["states"] == _states12 and v["n_states"] == det["process_state_count"] for v in ksw["variants"])
   # the frontier provenance rerun reproduces the headline variant it extends
   and abs(fsw["reproduced_headline"]["Fe"]["cost"] - kh["Fe"]["cost"]) < 1e-5
   and abs(fsw["reproduced_headline"]["Ru_benchmark"]["cost"] - kh["Ru_benchmark"]["cost"]) < 1e-5
   and abs(fsw["reproduced_headline"]["parity_multiple"] - kh["Ru_activity_multiple_for_parity"]) < 1e-5)

# both financing conventions (replaces the 2026-10-12 check that no lifecycle-financing claim appears)
m_feru2 = (main_section("What Ru must cost to match fused iron") + " "
           + main_section("The optimizer recovers the industrial bed order"))
KAAP_P = IR["c_0_KAAP"]["Ru"]["P_bar"]
_LC = _load_module("lifecycle_cashflow", ROOT / "analysis/nh3_ru_net_recovery_boundary_2026_10_12/lifecycle_cashflow.py")
LIFE, PLANT_Y = _ynum("catalyst_life_y"), dcf["frozen_plant_years"]
_buy, _coll = _LC.lifecycle_dates(LIFE, PLANT_Y)
tokens("Methods: lifecycle cash-flow variant (dates and financing range)", methods,
       f"every metal purchase (at {_and(f'{t:.0f}' for t in _buy)} years) and recovered-metal credit (at replacement and closure) at its date",
       f"discounted at a metal financing rate of {pc(i_lo)}–{pc(i_hi)}% per year with Fe on the same convention",
       f"over the {PLANT_Y:.0f}-year plant life")
ok("Methods: recovered Ru is credited at each replacement and at closure",
   _coll[:-1] == _buy[1:] and _coll[-1] == PLANT_Y and dcf["frozen_catalyst_life_y"] == LIFE)

# measured frontier kinetics
_mult_all = [v["Ru_activity_multiple_for_parity"] for v in ksw["variants"]]
ru_o = val["apparent_orders_90bar"]["Ru_C_Rossetti_400C"]
fe_o = IRV["apparent_orders_90bar_400C_2pct"]["Fe_Keestra_KM1R1964"]
_ruv = val["Ru_C_Rossetti2006_Table2"]["all_points_N2_basis"]
_rr = IRV["rate_ratio_90bar_Keestra"]
fe_rng, ru_rng = _yrange("Fe_DysonSimon", "atm"), _yrange("Ru_C_Rossetti", "bar")
ru_trng = _yrange("Ru_C_Rossetti", "C")
_rr_lo, _rr_hi = _rr["400C_yNH3_0.02"]["Ru_over_Fe_per_kg"], _rr["400C_yNH3_0.14"]["Ru_over_Fe_per_kg"]
_irr = _ir_all["ranges"]
fe_irng, ru_irng = _irr["Fe_Keestra"]["P"], _irr["Ru_C_Rossetti"]["P"]
ia = IR["a"]
_mult_ir = list(IR["parity_variants"].values())
_mp = IRV["micropilot_430C_100bar_30000h"]
_bvr = IRV["bed_volume_Keestra_KM1R1964_over_DysonSimon, 155-310 bar (Dyson-Simon range)"]
ok("NH3 measured kinetics in range: the Dyson-Simon in-range numbers are reproduced first; every optimum lies inside its "
   "law's fitted pressure range; Ru/C keeps a positive H2 order; Ru/C is held to the top of its measured temperature range",
   all(fe_irng[0] <= x["Fe"]["P_bar"] <= fe_irng[1] and ru_irng[0] <= x["Ru"]["P_bar"] <= ru_irng[1]
       for x in (IR["a"], IR["b_0"], IR["b_12"], IR["c_0_KAAP"], IR["c_12_KAAP"]))
   and ru_o["H2"] > 0 and _ynum("T_max_Ru_C") == ru_trng[1]
   and abs(_ir_all["Fe_DysonSimon_in_range"]["a"]["Fe"]["cost"] - 15.08) < 0.005
   and min(_mult_ir) == IR["parity"] and abs(IR["parity_variants"]["plug/source"] - IR["parity"]) < 1e-9)
_bp = IR["bench_price_parity"]
ok("NH3 measured kinetics in range: bulk-Ru parity price reproduces Fe at the Fe optimum and lies below the model Ru price",
   abs(_bp["Ru"]["cost"] - _bp["Fe"]["cost"]) < 1e-6 and abs(_bp["Fe"]["cost"] - ia["Fe"]["cost"]) < 1e-9
   and abs(_bp["price_USD_kg"] / _bp["factor_vs_current"] - _ynum("Ru_USD_kg")) < 1e-3 * _ynum("Ru_USD_kg"))
tokens("Main text: descriptor parity price against the model Ru price", m_feru2,
       f"places parity at {float(parity['price_USD_kg']):.0f} US dollars per kilogram, "
       f"{pc(1 - float(parity['price_USD_kg']) / _ynum('Ru_USD_kg'))}% below the Ru price of the model")
tokens("SI Note 7: measured rate laws, validation and costs", s2_full,
       f"fitted from {fe_irng[0]:.0f} to {fe_irng[1]:.0f} bar",
       f"(apparent orders N₂ {fe_o['N2']:+.2f}, H₂ {fe_o['H2']:+.2f}, NH₃ {fe_o['NH3']:+.2f})",
       f"reproduces the {_ruv['n']} measured points of its source with a mean error of {pc(_ruv['mean_abs_rel_err'], 1)}%",
       f"the fused-iron law gives {_mp['model_pct']['Keestra KM1R_1964']:.1f}% NH₃ against "
       f"{_mp['measured_pct']['magnetite']:.0f}% measured",
       f"it requires {_bvr['min']:.2f}–{_bvr['max']:.1f} times their bed",
       f"(fused iron {fe_irng[0]:.0f}–{fe_irng[1]:.0f} bar, Ru/C {ru_irng[0]:.0f}–{ru_irng[1]:.0f} bar), the pair gives Fe "
       f"{ia['Fe']['cost']:.2f} US dollars per tonne at {ia['Fe']['T_C']:.0f} °C, {ia['Fe']['P_bar']:.0f} bar and a "
       f"{ia['Fe']['Tsep_C']:.0f} °C separator and Ru in the benchmark formulation {ia['Ru']['cost']:.2f} at "
       f"{ia['Ru']['P_bar']:.0f} bar; the activity multiple for parity is {IR['parity']:.2f} "
       f"({min(_mult_ir):.2f}–{max(_mult_ir):.2f} across",
       f"against {bw['Ru_activity_break_even_multiplier']:.2f} with the descriptor kinetics",
       f"Supported Ru/C ({pc(_ynum('Ru_wt_frac_commercial'))} wt% Ru, {_ynum('Ru_C_bed_density_kg_m3'):.0f} kg m⁻³, "
       f"{pc(r_hi, 2)}% recovery) has its optimum at {IR['b_0']['Ru']['P_bar']:.0f} bar",
       f"from {_rr_lo:.0f}-fold at 2% to {_rr_hi:.0f}-fold at 14% NH₃ (90 bar, 400 °C)")
ok("SI Note 7: fused-iron law checks (micropilot within 16 %, bed ratio to Dyson-Simon from 1.05 in its range)",
   abs(_mp["rel_err"]["Keestra KM1R_1964 vs magnetite"]) < 0.165 and 1.0 < _bvr["min"] < _bvr["max"])
tokens("SI Note 7: apparent orders of the Ru/C rate law", s2_full,
       f"(N₂ {ru_o['N2']:+.2f}, H₂ {ru_o['H2']:+.2f}, NH₃ {ru_o['NH3']:+.2f})")
tokens("Methods: measured rate laws and the staged converter", methods,
       f"fitted to data from {fe_irng[0]:.0f} to {fe_irng[1]:.0f} bar, with the activity factor (0.350) of the Topsoe KM1R catalyst",
       f"fitted at {ru_irng[0]:.0f}–{ru_irng[1]:.0f} bar",
       f"the Ru/C law reproduces the {_ruv['n']} measured points of its source with a mean error of {pc(_ruv['mean_abs_rel_err'])}%",
       f"the fused-iron law the outlet of a commercial magnetite catalyst at 100 bar within {100 * _mp['rel_err']['Keestra KM1R_1964 vs magnetite']:.0f}%",
       "each catalyst is optimized only over the states inside its fitted pressure range",
       f"each bed filled with fused iron (up to {_ynum('T_max_Fe_C'):.0f} °C) or Ru/C (up to {_ynum('T_max_Ru_C'):.0f} °C, the top of its measured range)",
       f"at {_ylist('loops_bar')[0] / 10:.0f} MPa, a {_ynum('separator_C'):.0f} °C separator and {pc(_ynum('inerts_typical'))}% inerts")

ok("Methods: the 9 MPa loop lies inside both fitted pressure ranges",
   fe_irng[0] <= _ylist("loops_bar")[0] <= fe_irng[1] and ru_irng[0] <= _ylist("loops_bar")[0] <= ru_irng[1]
   and KAAP_P == _ylist("loops_bar")[0])

# measured kinetics: break-even metal financing rate of supported Ru/C against Fe (frontier provenance, 1.2)
_be_g, _be_k = IR["b_breakeven"]["rate"], IR["c_breakeven_KAAP"]["rate"]
_be_g90, _be_k90 = IR["b_breakeven_r90"]["rate"], IR["c_breakeven_KAAP_r90"]["rate"]
ok("Measured Ru/C rows of Table 1: both optima at the stated pressure (Ru/C at the top of its fitted range)",
   IR["b_0"]["Ru"]["P_bar"] == IR["b_12"]["Ru"]["P_bar"] == ru_irng[1]
   and IR["c_0_KAAP"]["Fe"]["P_bar"] == IR["c_12_KAAP"]["Ru"]["P_bar"] == KAAP_P)
tokens("SI Note 7: measured-kinetics break-even financing rates", s2_full,
       f"It stays cheaper than Fe up to a metal financing rate of {pc(_be_g, 2)}% per year, and in the KAAP-type loop up "
       f"to {pc(_be_k, 2)}% per year ({pc(_be_g90, 2)}% and {pc(_be_k90, 2)}% at {pc(r_lo)}% recovery)")
ok("Measured-kinetics break-even (in range): Ru/C and Fe cost the same there and the rates bracket the 0 %/y and "
   "12 %/y signs",
   all(abs(IR[k]["Ru"]["cost"] - IR[k]["Fe"]["cost"]) < 1e-5
       for k in ("b_breakeven", "c_breakeven_KAAP", "b_breakeven_r90", "c_breakeven_KAAP_r90"))
   and i_lo < _be_k < _be_g < i_hi and _be_g90 < _be_g and _be_k90 < _be_k,
   f"{100 * _be_g:.2f} / {100 * _be_k:.2f} %/y")
# the 16 robustness cases, each catalyst in its fitted range (robustness_inrange.py); an infeasible Fe bed is -inf
_rb = IRR["cases"]
_rbs = IRR["summary"]


def _rb_count(col, sign):
    return sum(((r_[col] if r_[col] is not None else -math.inf) > 0) if sign > 0
               else ((r_[col] if r_[col] is not None else -math.inf) < 0) for r_ in _rb)


tokens("SI Note 7: measured-kinetics robustness cases", s2_full,
       f"Across {len(_rb)} cases that vary",
       f"Ru/C is cheaper than Fe without metal financing in all {_rb_count('gap_0_global', -1)} in the main loop and in "
       f"{_rb_count('gap_0_KAAP', -1)} in the KAAP-type loop, all but inlet-rate sizing",
       f"the break-even financing rate spans {pc(_rbs['global']['breakeven_range'][0], 2)}–"
       f"{pc(_rbs['global']['breakeven_range'][1], 2)}% per year in the main loop and "
       f"{pc(_rbs['KAAP']['breakeven_range'][0], 2)}–{pc(_rbs['KAAP']['breakeven_range'][1], 2)}% per year in the "
       f"KAAP-type loop",
       f"At {pc(i_hi)}% per year Fe is cheaper in {_rbs['global']['Fe_ahead_at_12']} of the {len(_rb)} cases in both loops, "
       f"all but a halved Fe effectiveness")
ok("Measured-kinetics robustness (in range): base case equals the headline; exceptions at 12 %/y are a halved Fe "
   "effectiveness only; in the KAAP-type loop a halved Fe effectiveness leaves no Fe bed",
   len(_rb) == 16 and _rbs["global"]["Fe_ahead_at_12"] == _rbs["KAAP"]["Fe_ahead_at_12"] == 15
   and _rbs["global"]["exceptions_12"] == _rbs["KAAP"]["exceptions_12"] == ["Fe effectiveness 0.5"]
   and _rbs["KAAP"]["infeasible"] == ["Fe effectiveness 0.5"] and _rbs["KAAP"]["exceptions_0"] == ["inlet-rate sizing"]
   and abs(next(r_ for r_ in _rb if r_["case"] == "base")["breakeven_global"] - _be_g) < 1e-6)

# apparent reaction orders of the descriptor kinetics (analysis/verify_2026_10_14_descriptor_orders, central differences)
_do = _j("analysis/verify_2026_10_14_descriptor_orders/descriptor_orders.json")
_do12, _doc = _do["1.2"], _do["condition"]
_dru, _dfe = _do12["orders"]["Ru"]["central"], _do12["orders"]["Fe"]["central"]
_dcond = f"{_doc['P_bar']:.0f} bar, {_doc['T_C']:.0f} °C and {pc(_doc['y_NH3'])}%"
tokens("Main text: apparent orders of the descriptor kinetics for Ru and fused iron", m_feru2,
       f"at {_dcond} NH₃ they give Ru apparent orders of {_dru['H2']:+.1f} in H₂ and {_dru['NH3']:+.1f} in NH₃",
       f"and fused iron {_dfe['NH3']:+.1f} in NH₃ against {fe_o['NH3']:.1f} measured")
tokens("SI Note 7: apparent orders of the descriptor kinetics", s2_full,
       f"At {_dcond} NH₃ the descriptor kinetics give Ru apparent orders of {_dru['H2']:+.1f} in H₂ and "
       f"{_dru['NH3']:+.1f} in NH₃ and fused iron {_dfe['NH3']:+.1f} in NH₃")
ok("Descriptor apparent orders: the 1.2 model of the canonical run; Ru H2 order above the measured Ru/C order; fused-iron "
   "NH3 inhibition weaker than measured (the contrast the text draws)",
   _do12["model"] == "NH3-FINAL-1.2" and _do12["run"] == RUN.name and _do12["states"] == det["process_state_count"]
   and _dru["H2"] > ru_o["H2"] > 0 and _dru["NH3"] < ru_o["NH3"] < 0 and fe_o["NH3"] < _dfe["NH3"] < 0
   and all(abs(_do12["orders"][mt]["central"][s_] - _do12["orders"][mt]["forward_0p02"][s_]) < 0.05
           for mt in ("Ru", "Fe") for s_ in ("N2", "H2", "NH3")))

# thermodynamic basis of NH3-FINAL-1.2 (Methods and SI Note 1): Gillespie-Beattie NH3 formation free energy instead of
# the DFT gas energies of the activity source. The committed model-vs-GB comparison is the 1.1 model's dGf against the
# Gillespie-Beattie value at 400, 425 and 450 C (analysis/verify_2026_10_12_hybrid_bed/hybrid_bed_feasibility.json,
# kJ/mol with the script's 96.485 kJ/mol per eV). No committed output tabulates the 350 and 500 C ends of the printed
# 0.064-0.065 eV range, so the check is that every committed offset lies inside the printed range; on 1.2 the offset is
# zero (y_eq,model / y_eq,exp = 1 over all 83 laboratory rows of the supported chain).
_hb = _j("analysis/verify_2026_10_12_hybrid_bed/hybrid_bed_feasibility.json")["equilibrium"]
_off = [(e_["dGf_model_kJ_mol"] - e_["dGf_exp_kJ_mol"]) / 96.485 for e_ in _hb]
_thermo_re = r"the NH₃ formation free energy is taken at each temperature from the Gillespie–Beattie equilibrium " \
             r"constant,\[\d+\] in place of the DFT gas energies of the activity source, which place it " \
             r"(\d\.\d+)–(\d\.\d+) eV per NH₃ higher"
_th = {k: re.search(_thermo_re, hay) for k, hay in (("Supplementary Methods", supplementary_method("Ammonia synthesis")), ("SI Note 1", s1))}
ok("Thermodynamic basis: model-minus-Gillespie-Beattie NH3 formation free energy of the DFT gas energies lies inside the "
   "printed range (Supplementary Methods and SI Note 1); NH3-FINAL-1.2 has no offset",
   all(_th.values()) and all(float(t_.group(1)) - 5e-4 <= x <= float(t_.group(2)) + 5e-4
                             for t_ in _th.values() for x in _off)
   and len(_off) >= 3 and all(x > 0 for x in _off)
   and abs(sup["nh3_model"]["y_eq_model_over_exp"]["min"] - 1) < 1e-12
   and abs(sup["nh3_model"]["y_eq_model_over_exp"]["max"] - 1) < 1e-12,
   ", ".join(f"{e_['T_C']} C {x:.4f} eV" for e_, x in zip(_hb, _off)))
_cal = _j("provenance/nh3_final_1_2/source_harness/calibration_comparison.json")
_cs = _cal["calibration_state"]
_cal_txt = f"fixed by the fused-iron bed at {_cs['T_C']:.0f} °C, {_cs['P_bar']:.0f} bar and a {_cs['Tsep_C']:.0f} °C separator"
tokens("Methods and SI Note 1: thermodynamic basis and the fused-iron calibration state", methods + " " + s1,
       "N₂, H₂ and NH₃ enter the loop equilibrium and the microkinetic gas activities as fugacities with Newton–Cooper "
       "coefficients",
       f"Catalyst productivity is calibrated on the fused-iron bed at {_cs['T_C']:.0f} °C, {_cs['P_bar']:.0f} bar and a {_cs['Tsep_C']:.0f} °C separator")
ok("Fused-iron calibration: the 1.2 recalibrated F_CAL is the run's F_CAL and reproduces the frozen Fe bed",
   abs(_cal["variants"]["v1_2"]["recalibrated"]["F_CAL"] - ksw["frozen_anchor_check"]["model"]["F_CAL"]) < 1e-5
   and abs(_cal["variants"]["v1_2"]["recalibrated"]["Fe_bed_at_calibration_state"]
           - _cal["variants"]["v1_1"]["fixed_FCAL"]["Fe_bed_at_calibration_state"]) < 1e-9
   and abs(_cal["variants"]["v1_2"]["recalibrated"]["metals"]["Fe"]["feasible"]["cost"]
           - m["Fe"]["feasible"]["total_cost"]) < 1e-12
   and _cal_txt in supplementary_method("Ammonia synthesis") and _cal_txt in s1)

# industrial plant benchmark of NH3-FINAL-1.2 (SI Note 1; analysis/validation_nh3_plant_2026_10_13/nh3_1_2)
PBM = f"analysis/validation_nh3_plant_2026_10_13/{V12}/"
_pbs = _j(PBM + "summary.json")
_pbm = rows(PBM + "results_metrics.csv")
_pbA = [r_ for r_ in _pbm if r_["table"] == "A"]
# error table and Fe-Ru perturbation (analysis/nh3_benchmark_error_table_2026_10_19; supervisor 2026-10-19)
NB = "analysis/nh3_benchmark_error_table_2026_10_19/"
_es = {r_["group"]: r_ for r_ in rows(NB + "error_summary.csv")}
_et = rows(NB + "error_table.csv")
_pr = rows(NB + "perturbation_results.csv")
_psum = _j(NB + "perturbation_summary.json")
_g = lambda k: _es[k]
_sgl = [r_ for r_ in _pr if r_["kind"] == "single"]
_d_rf = [float(r_["gap_Ru_minus_Fe"]) for r_ in _sgl if r_["comparison"] == "descriptor Ru - Fe"]
_rc12 = [float(r_["gap_Ru_minus_Fe"]) - float(r_["baseline_gap"]) for r_ in _sgl
         if r_["comparison"] == "measured supported Ru/C - Fe (12 %/y)" and r_["magnitude"] == "typical"]
_wc = _psum["comparisons"]["descriptor Ru - Fe"]["worst_corner"]["typical"]["gap"]
ok("NH3 benchmark perturbation: no single deviation reverses descriptor Fe-Ru, nor any sign combination at the typical "
   "deviations; measured benchmark Ru never ahead",
   len(_d_rf) == 28 and min(_d_rf) > 0 and _wc > 0
   and _psum["comparisons"]["descriptor Ru - Fe"]["n_single_flips"] == 0
   and _psum["comparisons"]["measured benchmark Ru - Fe (unconstrained)"]["n_single_flips"] == 0)
# descriptor branch at the Keestra-upgraded magnitudes (analysis/nh3_keestra_consolidation_2026_10_20, 2026-10-21)
_pdd = _j("analysis/nh3_keestra_consolidation_2026_10_20/perturbation_descriptor_summary.json")["comparisons"]["descriptor Ru - Fe"]
_pdr = rows("analysis/nh3_keestra_consolidation_2026_10_20/perturbation_descriptor_results.csv")
_pdmag = _j("analysis/nh3_keestra_consolidation_2026_10_20/perturbation_magnitudes.json")["KIN"]
_pdps = [float(r_["gap_Ru_minus_Fe"]) for r_ in _pdr if r_["comparison"] == "descriptor Ru - Fe"
         and r_["scenario"] == "KIN_Fe + max_plant_sizing"]
_pdrev = [r_ for r_ in _pdr if r_["comparison"] == "descriptor Ru - Fe" and r_["kind"] == "corner"
          and r_["magnitude"] == "max" and float(r_["gap_Ru_minus_Fe"]) < 0]
tokens("NH3 descriptor perturbation at the upgraded magnitudes: margins, reversing corners and the bed factors",
       raw_si,
       f"smallest margin +{_pdd['min_finite_single']['gap']:.2f} US dollars per tonne",
       f"(smallest margin +{_pdd['worst_corner']['typical']['gap']:.2f})",
       f"by +{_pdd['joint_Ru_favouring']['typical']['gap']:.2f} when each moves",
       f"that combination leaves +{_pdd['joint_Ru_favouring']['max']['gap']:.2f}",
       f"{_pdd['worst_corner']['max']['n_flipped']} of 64 sign combinations reverse",
       f"multiplied by {_pdmag['max']:.2f}", f"(×{_pdmag['max_plant_sizing']:.2f}) the margin is +{_pdps[0]:.2f}")
tokens("Main text: descriptor perturbation margins at the upgraded magnitudes", raw_text,
       f"with a smallest margin of {_pdd['min_finite_single']['gap']:.2f} US dollars per tonne",
       f"(smallest margin {_pdd['worst_corner']['typical']['gap']:.2f}; Supplementary Note 7)")
ok("NH3 descriptor perturbation: every reversing corner at the largest deviations has the largest catalyst-amount factor",
   len(_pdrev) == _pdd["worst_corner"]["max"]["n_flipped"]
   and all(abs(float(r_["catalyst_amount_factor"]) - _pdmag["max"]) < 5e-4 for r_ in _pdrev))
_flow = [float(_g(k)["typical_abs_dev_pct"]) for k in ("converter flow and feed/make-up", "space velocity",
                                                      "bed volume, plant conditions")]
ok("Plant benchmark: the metric table reproduces the 1.2 summary and anchors to the canonical run",
   _pbs["model_version"] == "NH3-FINAL-1.2" and _pbs["n_metrics"] == len(_pbm)
   and _pbs["n_pass"] == sum(r_["pass_"] == "pass" for r_ in _pbm)
   and _pbs["by_table"]["A"] == f"{sum(r_['pass_'] == 'pass' for r_ in _pbA)}/{len(_pbA)}"
   and abs(_pbs["anchors"]["frozen_Fe"] - m["Fe"]["feasible"]["total_cost"]) < 1e-5
   and abs(_pbs["anchors"]["measured_Fe"]["cost"] - kh["Fe"]["cost"]) < 1e-5)

# staged converter: the lower envelope of the committed design library (boundary.py, ported without numpy)
P_FE, P_SUP, P_RU = _ynum("Fe_catalyst_USD_kg"), _ynum("Ru_C_support_USD_kg"), _ynum("Ru_USD_kg")
PATS = ("FFF", "FFR", "FRR", "RRR")
_lib, _ann = {}, []
for r in rows(SC12 + "design_library.csv"):
    _lib.setdefault((float(r["P_bar"]), float(r["Tsep_C"]), r["pattern"]), []).append(
        tuple(float(r[c]) for c in ("noncatalyst", "Ru_metal_kg", "mass_Fe_kg", "mass_Ru_cat_kg", "Ru_volume_fraction")))
    _cat = float(r["cost"]) - float(r["noncatalyst"])
    _ann.append((_cat, (float(r["c_Ru"]) * float(r["Ru_metal_kg"]) + float(r["c_Fe"]) * float(r["mass_Fe_kg"])
                        + float(r["c_Fe"]) * P_SUP / P_FE * float(r["mass_Ru_cat_kg"])) / _cat if _cat > 0 else 0.0))
ANNUAL = max(_ann)[1]          # annual NH3 output, from the library row with the largest catalyst term
_libK = {}                      # KAAP-type loop, Keestra fused iron and Rossetti Ru/C (both inside their fitted ranges)
for r in rows(IRD + "staged_KM1R_1964_design_library.csv"):
    _libK.setdefault((float(r["P_bar"]), float(r["Tsep_C"]), r["pattern"]), []).append(
        tuple(float(r[c]) for c in ("noncatalyst", "Ru_metal_kg", "mass_Fe_kg", "mass_Ru_cat_kg", "Ru_volume_fraction")))
_mcache = {}


def _mult(acc, rec, i):
    if acc == "frozen":
        return 1.0 - rec
    if (rec, i) not in _mcache:
        _mcache[(rec, i)] = _LC.annualized_metal_multiplier(
            _LC.MetalCashflow(project_y=PLANT_Y, catalyst_life_y=LIFE, discount_rate=i, gross_recovery=rec), 1.0,
            legacy_life_y=LIFE)
    return _mcache[(rec, i)]


def _decide(loop, p_ru, rec, i, acc="dcf", lib=None):
    lib = _lib if lib is None else lib
    m0 = _mult(acc, 0.0, i)
    c_ru, c_fe, c_sup = p_ru * _mult(acc, rec, i) / LIFE, P_FE * m0 / LIFE, P_SUP * m0 / LIFE
    res = {}
    for pat in PATS:
        best = None
        for nc, ru, fe, rcat, frac in lib[(loop[0], loop[1], pat)]:
            c = nc + (c_ru * ru + c_fe * fe + c_sup * rcat) / ANNUAL
            if best is None or c < best[0]:
                best = (c, frac)
        res[pat] = best
    staged = min(("FFR", "FRR"), key=lambda q: res[q][0])
    best = min(PATS, key=lambda q: res[q][0])
    return {"best": best, "best_frac": res[best][1], "staged_minus_Fe": res[staged][0] - res["FFF"][0]}


def _cls(loop, p_ru, rec, i, lib=None):
    b = _decide(loop, p_ru, rec, i, lib=lib)["best"]
    return "ru" if b == "RRR" else "fe" if b == "FFF" else "st"


def _window(loop, p_ru, rec, top=0.20, step=0.0005, lib=None):
    """Financing-rate window in which a Fe-first staged design is the optimum: all-Ru/C below, all-Fe above."""
    xs = [k * step for k in range(int(round(top / step)) + 1)]
    cl = [_cls(loop, p_ru, rec, x, lib) for x in xs]
    if not re.fullmatch(r"(ru,)*(st,)+(fe,)+", ",".join(cl) + ","):
        return None

    def edge(a, b, right):
        for _ in range(60):
            mid = (a + b) / 2
            a, b = (a, mid) if _cls(loop, p_ru, rec, mid, lib) == right else (mid, b)
        return (a + b) / 2

    j_st, j_fe = cl.index("st"), cl.index("fe")
    lo = 0.0 if j_st == 0 else edge(xs[j_st - 1], xs[j_st], "st")
    return {"lo": lo, "hi": edge(xs[j_fe - 1], xs[j_fe], "fe"), "all_ru_below": j_st > 0}


_bp = rows(SC12 + "boundary_pressure.csv")
_bad = []
for r in _bp:
    d = _decide((float(r["P_bar"]), float(r["Tsep_C"])), float(r["p_Ru"]), float(r["recovery"]), float(r["fin_rate"]),
                "frozen" if r["accounting"] == "benchmark" else "dcf")
    if d["best"] != r["best"] or abs(d["staged_minus_Fe"] - float(r["staged_minus_Fe"])) > 2e-6:
        _bad.append(r)
ok("Staged converter: the audit's envelope reproduces boundary_pressure.csv (all loops, rates, accountings)",
   not _bad and len(_bp) > 200 and 330 <= ANNUAL / _ynum("production_tpd") <= 365,
   f"{len(_bad)} rows differ" if _bad else f"{len(_bp)} rows")
_loops = {k.split(" bar")[0].split()[-1]: tuple(v) for k, v in ssum["inputs"]["loops"].items()}   # converter loops
KAAP, C150, C200 = _loops["90"], _loops["150"], _loops["200"]
w95 = _window(KAAP, P_RU, r_hi)
w90 = _window(KAAP, P_RU, r_lo)
w150, w200 = _window(C150, P_RU, r_hi), _window(C200, P_RU, r_hi)
wm30, wp30 = _window(KAAP, 0.7 * P_RU, r_hi), _window(KAAP, 1.3 * P_RU, r_hi)
wK = {k: _window(KAAP, p_, r_, lib=_libK) for k, p_, r_ in (("95", P_RU, r_hi), ("90", P_RU, r_lo),
                                                             ("m30", 0.7 * P_RU, r_hi), ("p30", 1.3 * P_RU, r_hi))}
ok("Staged converter (both laws in range): windows exist and match the in-range summary",
   None not in wK.values() and abs(wK["95"]["hi"] - IRS["window_keestra"]["staged_beats_all_Fe_below"]) < 2e-4
   and not wK["95"]["all_ru_below"] and IRS["Ru_first_never_optimal"]
   and IRS["envelope_check"]["max_envelope_minus_direct"] < 0.01)
_crit = {(c["P_bar"], c["Tsep_C"], c["recovery"], c["p_Ru"]): c["staged_beats_Fe_below"]
         for c in sbnd["critical_financing_rate"]}
_pres = {(c["P_bar"], c["Tsep_C"]): c["staged_beats_Fe_below_rate"] for c in sbnd["pressure"]}
ok("Staged converter: windows exist and their upper edges match boundary_summary.json",
   None not in (w95, w90, w150, w200, wm30, wp30)
   and abs(w95["hi"] - _crit[(KAAP[0], KAAP[1], r_hi, P_RU)]) < 2e-4
   and abs(w90["hi"] - _crit[(KAAP[0], KAAP[1], r_lo, P_RU)]) < 2e-4
   and abs(w150["hi"] - _pres[C150]) < 2e-4 and abs(w200["hi"] - _pres[C200]) < 2e-4)
lease_lo, lease_hi = pbf["pbf_min"] / 100, pbf["pbf_max"] / 100
_lease3 = [hl[k]["rate_pct"] for k in ("pbf_min", "pbf_median", "pbf_max")]
_save = [-_decide(KAAP, P_RU, r_hi, x / 100, lib=_libK)["staged_minus_Fe"] for x in _lease3]
ok("Staged converter (in range): the documented lease rates lie inside the Fe-first window, where staging saves cost",
   wK["95"]["lo"] < lease_lo and lease_hi < wK["95"]["hi"] and min(_save) > 0)
_order = [a.get("best", "") for a in ssum["arrangements"]] + [s.get("best", "") for s in ssum["sensitivities"]]
ok("Staged converter: a Ru/C-first converter is optimal in no case tested",
   _order and all(not re.search(r"R.*F", b) for b in _order) and not w150["all_ru_below"] and not w200["all_ru_below"])
_lease_rng = f"{pbf['pbf_min']:.2f}–{pbf['pbf_max']:.2f}% per year"
# since 2026-10-19 the abstract states the industrial result (Ru inventory financed at the 12 % equipment rate: fused iron
# least-cost with measured kinetics in every loop and in the three-bed converter) and the financing window in which Ru
# enters; the Discussion keeps the staged-converter / lease-rate statement
ok("Industrial Fe result: at the 12 %/y equipment rate Ru/C is dearer than Fe with measured kinetics in both loops, and "
   "the three-bed optimum is all-Fe (upper window edge below 12 %/y)",
   IR["b_12"]["gap"] > 0 and IR["c_12_KAAP"]["gap"] > 0 and wK["95"]["hi"] < i_hi
   and _decide(KAAP, P_RU, r_hi, i_hi, lib=_libK)["best"] == "FFF")
def _lo0(w):
    """Lower window edge as printed: '0' when the Fe-first design is already optimal at 0 %/y."""
    return "0" if w["lo"] == 0.0 else pc(w["lo"], 2)


# Ru/C share of the least-cost (Fe-first) converter across the in-range window: at 0 %/y and just below the upper edge
_sh_lo = _decide(KAAP, P_RU, r_hi, 0.0, lib=_libK)["best_frac"]
_sh_hi = _decide(KAAP, P_RU, r_hi, wK["95"]["hi"] - 1e-7, lib=_libK)["best_frac"]
ok("Staged converter (in range): the optimal Ru/C share falls across the window",
   _sh_lo > _sh_hi > 0 and _decide(KAAP, P_RU, r_hi, 0.0, lib=_libK)["best"] in ("FFR", "FRR"))
tokens("SI Note 7: staged converter, Ru/C share across the window", s2_full,
       f"the Ru/C share of the catalyst volume falls from {pc(_sh_lo)}% to {pc(_sh_hi)}% across the window",
       "a converter with Ru/C first is optimal in no case tested",
       "with both rate laws inside their fitted pressure ranges")
tokens("SI Note 7: staged-converter window edges (2 decimals)", s2_full,
       f"fused iron upstream with Ru/C downstream for Ru financing rates of 0–{pc(wK['95']['hi'], 2)}% per year",
       f"all-Fe above {pc(wK['95']['hi'], 2)}% per year")
tokens("SI Note 7: staged window at 90 % recovery and at Ru price -30 % / +30 %", s2_full,
       f"The window moves with recovery ({_lo0(wK['90'])}–{pc(wK['90']['hi'], 2)}% per year at {pc(r_lo)}%)",
       f"({_lo0(wK['m30'])}–{pc(wK['m30']['hi'], 2)}% at -30%, with all-Ru/C cheapest below "
       f"{pc(wK['m30']['lo'], 2)}%; {_lo0(wK['p30'])}–{pc(wK['p30']['hi'], 2)}% at +30%)")
tokens("SI Note 7: staging savings at the documented lease rates", s2_full,
       f"staging saves {_and(f'{s:.2f}' for s in _save)} US dollars per tonne over an all-Fe converter at "
       f"{_and(f'{x:.2f}' for x in _lease3)}% per year")
ok("Staged converter: the 150 and 200 bar loops share one separator temperature", C150[1] == C200[1])
_mb = json.loads((ROOT / "analysis/verify_2026_10_12_metal_basis/metal_basis_summary.json").read_text(encoding="utf-8"))
_pb6 = _mb["S6"]["paper_basis"]
ok("MeOH per-gram-of-Re basis: per-gram-of-catalyst counts reproduce the S5 and S6 frozen kinds",
   _mb["S6"]["per_g_catalyst"]["other_catalyst"]["groups"] == oc6["groups"]
   and _mb["S6"]["per_g_catalyst"]["other_temperature"]["groups"] == oT6["groups"]
   and _mb["S5"]["per_g_catalyst"]["other_catalyst"]["groups"] == k5["other_catalyst"]["groups"]
   and _pb6["different_winner"] == n6 and _pb6["gt5pct"] == gt5_6)
_pb5 = _mb["S5"]["paper_basis"]
ok("MeOH per-gram-of-Re basis: totals unchanged in both loops", _pb5["different_winner"] == n5 and _pb6["different_winner"] == n6)
ok("no compute-budget Agent section in the manuscript",
   "Adaptive calculation selection makes the multiscale analysis repeatedly executable" not in raw_text
   and "5,000-CU" not in raw_text)

# ----- NH3 loop checks (PR #95): recycle-rise sensitivity and the independent five-component loop -----------------
_LR = "analysis/nh3_loop_reconciliation_2026_10_14/outputs/"
_t1 = {(r["metal"], float(r["recycle_pressure_rise_bar"])): r for r in rows(_LR + "t1_metals.csv")}
_t1_92 = [_t1[(m, 9.2)] for m in ("Fe", "Ru", "Os")]
_t1_60 = [_t1[(m, 6.0)] for m in ("Fe", "Ru", "Os")]
ok("NH3 loop check T1: the 3 bar replay equals the frozen Fe/Ru/Os costs",
   all(abs(float(_t1[(m, 3.0)]["cost_USD_t"]) - float(_t1[(m, 3.0)]["frozen_cost_USD_t"])) < 1e-9 for m in ("Fe", "Ru", "Os")))
ok("NH3 loop check T1: rank order of all 15 metals unchanged at 6.0 and 9.2 bar",
   all(r["censored_rank"] == r["frozen_censored_rank"] and r["raw_rank"] == r["frozen_raw_rank"]
       for k, r in _t1.items()) and len({k[0] for k in _t1}) == 15)
tokens("Main text (Table 1): recycle-rise sensitivity costs", raw_text,
       f"| Descriptor | Benchmark, 9.2 bar recycle rise | Benchmark bed | {float(_t1_92[0]['cost_USD_t']):.2f} | "
       f"{float(_t1_92[1]['cost_USD_t']):.2f} | – (order of all 15 metals unchanged) |")
tokens("SI Note 7: recycle-rise sensitivity costs", s2_full,
       *[f"{float(r['cost_USD_t']):.3f}" for r in _t1_92 + _t1_60],
       f"{float(_t1[('Ru', 9.2)]['cost_USD_t']) - float(_t1[('Fe', 9.2)]['cost_USD_t']):.2f} US dollars per tonne above Fe")
# ----- References: numbered 1..N by first citation in the main body; caption-only references after them ------------
_body, _reflist = raw_text.split("## Working references", 1)
_ref_ids = [int(x) for x in re.findall(r"^(\d+)\.\s", _reflist, re.M)]
_captions = ((ROOT / "docs/MAIN_FIGURE_CAPTIONS.md").read_text(encoding="utf-8") + "\n"
             + (ROOT / "figures/extended_data/ED_CAPTIONS.md").read_text(encoding="utf-8"))
_CIT = re.compile(r"\[(\d+(?:\s*[–-]\s*\d+)?(?:\s*,\s*\d+(?:\s*[–-]\s*\d+)?)*)\]|\brefs?\.\s*(\d+)")
_bad_ranges = []


def _cited(s):
    """Reference numbers in order of appearance: [n], [n,m], [n–m] and 'ref. n'."""
    out = []
    for mt in _CIT.finditer(s):
        if mt.group(2):
            out.append(int(mt.group(2)))
            continue
        for part in mt.group(1).split(","):
            ends = [int(x) for x in re.split(r"\s*[–-]\s*", part.strip())]
            if len(ends) == 2 and ends[0] >= ends[1]:
                _bad_ranges.append(part.strip())
            out.extend(range(ends[0], ends[-1] + 1))
    return out


def _first_order(seq):
    seen = []
    for n_ in seq:
        if n_ not in seen:
            seen.append(n_)
    return seen


_b_order = _first_order(_cited(_body))
_c_only = [n_ for n_ in _first_order(_cited(_captions)) if n_ not in _b_order]
_all_cited = set(_cited(_body)) | set(_cited(_captions)) | set(_cited(raw_si))
ok("References: list numbered 1..N without gaps or repeats", _ref_ids == list(range(1, len(_ref_ids) + 1)),
   f"{len(_ref_ids)} entries, caption-only {_c_only}")
_dev = next((f"position {k + 1} is [{n_}]" for k, n_ in enumerate(_b_order) if n_ != k + 1), "")
ok("References: numbered in order of first citation in the main body", not _dev and not _bad_ranges,
   _dev or ("descending ranges: " + ", ".join(_bad_ranges) if _bad_ranges else ""))
ok("References: those cited only in figure captions follow the main-body references, in caption order",
   _c_only == list(range(len(_b_order) + 1, len(_b_order) + 1 + len(_c_only))),
   "" if _c_only == list(range(len(_b_order) + 1, len(_b_order) + 1 + len(_c_only))) else f"caption-only {_c_only}")
_missing = sorted(_all_cited - set(_ref_ids))
ok("References: every [n] in the main text, captions and SI exists in the list", not _missing,
   f"missing {_missing}" if _missing else "")
_uncited = sorted(set(_ref_ids) - set(_b_order) - set(_c_only))
ok("References: every listed reference is cited in the main body or a caption", not _uncited,
   f"uncited {_uncited}" if _uncited else "")

# ----- Supplementary Tables: numbered 1..N in order of first citation in the main text ------------------------------
_st_heads = sorted({int(x) for x in re.findall(r"^### Supplementary Table (\d+)", SIT, re.M)})
_st_order = _first_order(int(x) for x in re.findall(r"Supplementary Tables? (\d+)", _body))
_st_si = [int(x) for x in re.findall(r"Supplementary Tables? (\d+)", raw_si)]
ok("Supplementary Tables: 1..N in order of first main-text citation, all cited, SI cites only existing tables, "
   "SI states the range",
   _st_heads == list(range(1, len(_st_heads) + 1)) and _st_order == _st_heads and set(_st_si) <= set(_st_heads)
   and f"Supplementary Tables 1–{len(_st_heads)} follow the notes" in raw_si,
   f"tables {_st_heads}, main-text order {_st_order}")

# ----- Recycled CO converted up to CO-hydrogenation equilibrium (merged PR #84) -------------------------------
_cob = _j("analysis/meoh_co_conversion_bound_2026_10_13/summary.json")
_hi, _hn = _cob["results"]["high"]["6.86"], _cob["results"]["high"]["none"]
_si_flat = re.sub(r"\s+", " ", raw_si)
tokens("MeOH: recycled CO converted up to CO-hydrogenation equilibrium, main text and Methods (PR #84)", supplementary_method("Published methanol comparisons"),
       "recycled CO converted up to CO-hydrogenation equilibrium are reported as sensitivities")
tokens("SI Note 3: recycled CO converted up to CO-hydrogenation equilibrium (PR #84)", _si_flat,
       f"Recycled CO converted up to CO-hydrogenation equilibrium gives "
       f"{RB['3_co_bound']['combined']['high|6.86']['disagreements'].replace('/', ' of ')} "
       f"({RB['3_co_bound']['combined']['high|6.86']['gt5pct']} above 5%; "
       f"{_frac(RB['3_co_bound']['combined']['high|none']['disagreements'])[0]} without the limit)")
ok("PR #84 gate: the central rule reproduces the frozen columns and anchors",
   all(v["passed"] for v in _cob["gate"].values()) and all(_cob["frozen_anchors"].values()))

# ----- Supervisor revision 2026-10-21: current claims and their committed sources -----------------
# Keep each numerical assertion local to the relevant section, with formatting derived from the source.
_rcat, _rstrict = _cr["cat_primary"], _cr["cat_strict"]
tokens("MeOH main: conversion-raised catalyst headline and paper-bootstrap interval", m_field,
       f"In {_rcat['changed']} of the {_rcat['groups_2plus_catalysts']} comparisons that contain at least two catalysts "
       f"({pc(_rcat['fraction'])}%; 95% confidence interval {pc(_rcat['ci95'][0])}–{pc(_rcat['ci95'][1])}%), "
       f"from {_rcat['papers_changed']} papers",
       f"in {_rcat['gt5pct']} of them building it would cost more than 5% extra")
# The >10% count remains checked in MeOH SI: conversion raised counts, regret thresholds and interval.
tokens("MeOH main: laboratory conversion companion", m_field,
       f"the count rises to {_cc['changed']} of {_cc['groups_2plus_catalysts']} ({pc(_cc['fraction'])}%)")
# The 18/52 and 22/52 strict identities remain checked in the two MeOH SI count checks below.

tokens("MeOH main: operating-point counts and temperature shift", m_field,
       f"of {_ct['catalysts_with_2plus_T']} catalysts measured at several temperatures, {_ct['plant_T_differs']} are cheapest to run",
       f"{_ct['plant_colder']} of them at a lower one, by a median of {_quantiles(_ctC, [0.5])[0]:.0f} °C")
tokens("MeOH SI: conversion-raised operating-point count", s8,
       f"a catalyst loading more catalyst to raise its conversion {_cr['point_level']['changed']} "
       f"of {_cr['point_level']['groups']}")
for _name, _c, _strict in (("conversion raised", _rcat, _rstrict),
                          ("laboratory conversion", _cc, CL['cat_strict']['comparison'])):
    tokens(f"MeOH SI: {_name} counts, regret thresholds and interval", s8,
           f"{_c['changed']} of {'the ' if _name == 'conversion raised' else ''}{_c['groups_2plus_catalysts']}",
           f"{pc(_c['fraction'], 1)}%; {('paper-cluster bootstrap 95% confidence interval ' if _name == 'conversion raised' else '')}"
           f"{pc(_c['ci95'][0], 1)}–{pc(_c['ci95'][1], 1)}%",
           f"{_c['gt1pct']}, {_c['gt5pct']} and {_c['gt10pct']}",
           f"{_strict['changed']} of {_strict['groups_2plus_catalysts']} ({pc(_strict['fraction'], 1)}%; "
           f"{pc(_strict['ci95'][0], 1)}–{pc(_strict['ci95'][1], 1)}%")
# The single Re/TiO2 comparison switches to its plant leader on a per-Re STY basis.
_rrows = rows("analysis/meoh_catalyst_level_2026_10_19/groups_catalyst_level_conversion_raised.csv")
_re = [r for r in _rrows if r['doi'] == '10.1021/acscatal.5c05984']
ok("MeOH per-Re source: raised Re/TiO2 contributes one change above 5%",
   len(_re) == 1 and _re[0]['changed'] == 'True' and float(_re[0]['gap']) > .05
   and sum(r['changed'] == 'True' for r in _rrows) == _rcat['changed'])
tokens("MeOH Methods: per-Re catalyst counts under both conversions", supplementary_method('Published methanol comparisons'),
       f"{_rcat['changed'] - len(_re)} of {_rcat['groups_2plus_catalysts']} changes of catalyst "
       f"({_rcat['gt5pct'] - len(_re)} above 5%",
       f"{_cc['changed'] - len(_glr)} of {_cc['groups_2plus_catalysts']} and {_cc['gt5pct'] - len(_glr)} above 5% at laboratory conversion")
tokens("Abstract: conversion-raised methanol and ammonia field shares", main_section_h2("Abstract"),
       f"{_rcat['changed']} of {_rcat['groups_2plus_catalysts']} methanol comparisons between catalysts ({pc(_rcat['fraction'])}%)",
       f"{NPL['mismatch']} of {NPL['groups']} ammonia comparisons ({pc(NPL['fraction'])}%)")

KC = "analysis/nh3_keestra_consolidation_2026_10_20/"
_kcs = _j(KC + "summary.json")
_bes = _kcs['D']['breakevens']
_fc = rows(KC + "financing_curves.csv")
_rates = sorted(float(r['annual_rate_pct']) for r in leases)
_rate = (_rates[(len(_rates)-1)//2] + _rates[len(_rates)//2]) / 2

def _finance(rate_pct):
    # All three reported lease anchors are explicit rows, not an interpolation of optima.
    return next(r for r in _fc if abs(float(r['financing_rate_pct']) - rate_pct) < 1e-8)

_fr = _finance(_rate)
tokens("NH3 reference: median and range of the disclosed PBF leases", m_feru2,
       f"{len(_rates)} fixed-rate leases of platinum and palladium catalyst metal",
       f"{min(_rates):.2f}–{max(_rates):.2f}% per year, median {_rate:.2f}%")
tokens("NH3 reference: financing rate and fitted pressure ranges in Methods", methods,
       f"median of the {len(_rates)} fixed annual rates",
       f"({min(_rates):.2f}–{max(_rates):.2f}% per year",
       f"fitted to data from {fe_irng[0]:.0f} to {fe_irng[1]:.0f} bar",
       f"fitted at {ru_irng[0]:.0f}–{ru_irng[1]:.0f} bar",
       "it is applied to Ru by analogy")
tokens("NH3 main: supported Ru/C savings at median lease rate", m_feru2,
       f"At that rate Ru/C is the cheaper catalyst, by {-float(_fr['benchmark_RuC_minus_Fe']):.2f} US dollars per tonne at the two catalysts' own optima and {-float(_fr['KAAP_RuC_minus_Fe']):.2f} in the KAAP-type loop")
tokens("NH3 main: owned and supplier-lease break-even rates", m_feru2,
       f"it flips at {pc(_bes['benchmark_owned'], 2)}% per year",
       f"or {pc(_bes['KAAP_owned'], 2)}% in a KAAP-type loop",
       f"the break-even rates are {pc(_bes['benchmark_lease_unsecured'], 2)} and {pc(_bes['KAAP_lease_unsecured'], 2)}% per year")
tokens("NH3 Abstract and Discussion: measured Ru/C financing thresholds", main_section_h2("Abstract") + " " + discussion,
       f"undercuts fused iron whenever its Ru is financed below {pc(_bes['KAAP_owned'], 1)}–{pc(_bes['benchmark_owned'], 1)}% per year",
       f"below {pc(_bes['benchmark_owned'], 1)}% per year at the two catalysts' own optima and {pc(_bes['KAAP_owned'], 1)}% in a KAAP-type loop")
for _basis, _prefix, _be in (("own optima", "b", 'benchmark_owned'), ("KAAP-type", "c", 'KAAP_owned')):
    _z = IR['b_0' if _prefix == 'b' else 'c_0_KAAP']
    _h = IR['b_12' if _prefix == 'b' else 'c_12_KAAP']
    tokens(f"NH3 Table 1: {_basis} costs and reference-rate savings", m_feru2,
           f"| {_z['Fe']['cost']:.2f} / {_h['Fe']['cost']:.2f} | {_z['Ru']['cost']:.2f} / {_h['Ru']['cost']:.2f}",
           f"{ -float(_fr['benchmark_RuC_minus_Fe' if _prefix == 'b' else 'KAAP_RuC_minus_Fe']):.2f} cheaper at {_rate:.2f}% per year; "
           f"parity at {pc(_bes[_be], 2)}% per year")
    tokens(f"NH3 SI: {_basis} no-financing and equipment-rate gaps", s2_full,
           f"{-_z['gap']:.2f} less and {_h['gap']:.2f} more" if _prefix == 'c' else
           f"{-_z['gap']:.2f} US dollars per tonne less than Fe without metal financing and {_h['gap']:.2f} more")
_lof, _hif = _finance(min(_rates)), _finance(max(_rates))
tokens("NH3 SI: savings across disclosed lease range", s2_full,
       f"{-float(_lof['benchmark_RuC_minus_Fe']):.2f}–{-float(_hif['benchmark_RuC_minus_Fe']):.2f}",
       f"{-float(_lof['KAAP_RuC_minus_Fe']):.2f}", f"{float(_hif['KAAP_RuC_minus_Fe']):.2f}")
claim_tokens("NH3 main: measured rate-law costs and bulk parity requirements",
    ("main text", m_feru2, [f"a {IR['parity']:.0f}-fold activity gain or a {pc(1 - IR['bench_price_parity']['factor_vs_current'])}% lower price, {IR['bench_price_parity']['price_USD_kg']:,.0f} US dollars per kilogram, to match fused iron at {ia['Fe']['cost']:.2f} US dollars per tonne"]),
    ("SI Notes", s2_full, [f"Fe {ia['Fe']['cost']:.2f} US dollars per tonne at {ia['Fe']['T_C']:.0f} °C, {ia['Fe']['P_bar']:.0f} bar",
    f"{ia['Ru']['cost']:.2f} at {ia['Ru']['P_bar']:.0f} bar",
    f"{IR['parity']:.2f} ({min(_mult_ir):.2f}–{max(_mult_ir):.2f}"]))
tokens("NH3 Table 1: bulk measured and descriptor parity rows", m_feru2,
       f"| {ia['Fe']['cost']:.2f} | {ia['Ru']['cost']:.2f} ({ia['Ru']['P_bar']:.0f} bar) | activity rises {IR['parity']:.0f}-fold",
       f"activity rises {bw['Ru_activity_break_even_multiplier']:.0f}-fold, or Ru costs {float(parity['price_USD_kg']):.0f} US dollars per kilogram")
_st = IRS['window_keestra']['best_at'][f'{_rate:.2f} %/y']
tokens("NH3 staged: median-rate arrangement, Fe share and savings", m_feru2,
       f"from 0 to {pc(_bes['staged_Fe_first_beats_Fe_below'], 2)}% per year",
       f"fused iron {pc(1 - _st['best_Ru_volume_fraction'])}% of the catalyst volume",
       f"{ -_st['staged_minus_Fe']:.2f} US dollars per tonne less",
       f"| {_st['all_Fe']:.2f} (all Fe) | {_st['staged']:.2f} at {_rate:.2f}% per year |")
ok("NH3 staged source: reference financing row matches measured in-range envelope",
   _st['best'] == _fr['staged_optimal'] == 'FRR'
   and abs(_st['staged'] - float(_fr['staged_optimal_cost'])) < 1e-5
   and abs(_bes['staged_Fe_first_beats_Fe_below'] - wK['95']['hi']) < 2e-4)
tokens("NH3 staged: measured inhibition and rate advantage", m_feru2,
       f"apparent NH₃ orders {fe_o['NH3']:.2f} and {ru_o['NH3']:.2f}",
       f"{_rr_lo:.0f}-fold at 2% NH₃ to {_rr_hi:.0f}-fold at 14%")

_e_new = {r['group']: r for r in rows(KC + 'error_summary.csv')}
_et_new = rows(KC + 'error_table.csv')
_tb = _j(KC + 'table_b_summary.json')
_a_new = _e_new['A']
tokens("NH3 SI benchmark: measured converter totals and loop-state counts", s1,
       f"compared with {_tb['n_metrics']} values",
       f"{_tb['n_pass']} lie within their tolerance, among them {_a_new['n_pass']} of the {_a_new['n']} loop states",
       f"{len({r['case_id'] for r in _pbA})} industrial loop records")
ok("NH3 benchmark source: consolidated summary agrees with all item verdicts",
   len(_et_new) == _tb['n_metrics'] and sum(r['pass_'] == 'pass' for r in _et_new) == _tb['n_pass'])
for _qty in ('converter flow and feed/make-up', 'bed volume, plant conditions', 'space velocity'):
    _er = _e_new[_qty]
    tokens(f"NH3 SI benchmark: {_qty} typical deviation", s1, f"{float(_er['typical_abs_dev_pct']):.1f}%")
_er = _e_new['bed volume, cost-optimal designs and Fe optimum']
tokens("NH3 benchmark: cost-optimal bed volume deviation", s1, f"{float(_er['typical_abs_dev_pct']):.1f}%")
tokens("NH3 main benchmark: rounded bed volume deviation", m_feru2,
       f"converter designs ({float(_er['typical_abs_dev_pct']):.0f}%)")
_pert = _j(KC + 'perturbation_summary.json')
for _loop in ('benchmark', 'KAAP'):
    _p0 = _pert['comparisons'][f'{_loop} supported 0']['magnitudes']['typical']
    _p12 = _pert['comparisons'][f'{_loop} supported 0.12']['magnitudes']['typical']
    tokens(f"NH3 SI perturbation: {_loop} single-deviation shifts at 0 and 12 percent", s2_full,
           f"{_p0['single_shift_min']:.2f} to {_p0['single_shift_max']:+.2f}",
           f"{_p12['single_shift_min']:.2f} to {_p12['single_shift_max']:+.2f}",
           f"{_p12['n_corners_Ru_ahead']} of the 64" if _loop == 'benchmark' else f"{_p12['n_corners_Ru_ahead']} of 64")
_p0 = _pert['comparisons']['benchmark supported 0']['magnitudes']['typical']
_p12 = _pert['comparisons']['benchmark supported 0.12']['magnitudes']['typical']
tokens("NH3 main perturbation: maximum typical single shifts", m_feru2,
       f"at most {max(abs(_p0['single_shift_min']), abs(_p0['single_shift_max'])):.1f} US dollars per tonne without financing "
       f"and {max(abs(_p12['single_shift_min']), abs(_p12['single_shift_max'])):.1f} at 12% per year")
_bulk = _pert['comparisons']['bulk benchmark']['magnitudes']['typical']
tokens("NH3 SI perturbation: bulk margin and largest catalyst-amount deviation", s2_full,
       f"smallest margin +{_bulk['min_corner_gap']:.1f} US dollars per tonne",
       f"Fe bed multiplied by {_pert['magnitudes']['KIN']['max']:.2f}")
_prk = _j(KC + 'pr_loop_results.json')['comparisons']['KAAP_90bar_m20C_grid_optimum']
tokens("NH3 SI: Peng–Robinson KAAP cost gaps and financing break-evens", s2_full,
       f"{_prk['PR_gap']:.2f} US dollars per tonne", f"against {_prk['canonical_gap']:.2f} in the cost model",
       f"break-even of {pc(_prk['PR_break_even'], 2)}% per year, against {pc(_prk['canonical_break_even'], 2)}%")
ok("NH3 Peng–Robinson source: both fitted domains and positive 12-percent gap",
   all(_prk['PR'][c]['rate_P_inside_source_range'] and _prk['PR'][c]['rate_T_inside_source_range'] for c in ('Fe','Ru'))
   and _prk['PR_gap'] > 0 and abs(_prk['PR_gap'] - (_prk['PR']['Ru']['total_USD_t'] - _prk['PR']['Fe']['total_USD_t'])) < 1e-9)

_auv = _j('artifacts/au_tio2_decision_boundary_v2/summary.json')
_ap = _auv['V2_0_per_candidate_mc_primary']
tokens("Au SI: candidate-specific scatter, full order and leader", s5,
       f"σ = {_ap['sigma_ln']:.2f}", f"{pc(_ap['full_preservation'], 2)}% of {_ap['draws']:,} draws",
       f"{pc(_ap['winner_2nm_probability'], 2)}%", f"mean ρ = {_ap['mean_spearman_rho']:.4f}")
tokens("Au SI: adjacent-pair inversion probabilities", s5,
       *[f"{pc(v, 2)}%" for v in _ap['adjacent_inversion_rate'].values()])
for _a in _auv['V2_0_per_candidate_mc_all_sigma']:
    if _a['primary']: continue
    tokens(f"Au SI: scatter sweep sigma {_a['sigma_ln']:.2f}", s5,
           f"{_a['sigma_ln']:.2f}", f"{pc(_a['full_preservation'], 2)}%",
           f"{pc(_a['winner_2nm_probability'], 2) if _a['winner_2nm_probability'] < 1 else '100'}%")
_life = _auv['L2_lifetime']
tokens("Au SI: lifetime flip ratios and exponent boundary", s5,
       *[f"{v:.3f}" for v in _life['adjacent_flip_thresholds'].values()],
       f"λ = n + m = {_life['q_star_nominal']:.1f} "
       f"({_life['q_star_range_over_shared_exponents'][0]:.1f}–{_life['q_star_range_over_shared_exponents'][1]:.1f}")
_cut = rows('artifacts/au_tio2_decision_boundary_v2/l2_q_cut_shared_nm_sampled.csv')
for _q in (1.8, 2.0):
    _a = next(r for r in _cut if abs(float(r['q']) - _q) < 1e-8)
    tokens(f"Au SI: sampled-exponent leader at lambda {_q:.1f}", s5,
           f"{dfmt(Decimal(_a['p_winner_2nm']) * 100, 1)}%", f"λ = {_q:.1f}")
for _a in _auv['L2_L3_combined_273_293K_moderate']:
    if _a['q'] < 0: continue
    if _a['q'] <= 1.9:
        tokens(f"Au SI: combined operating and lifetime full order at lambda {_a['q']:g}", s5,
               f"{pc(_a['full_preservation_fraction'], 2)}%")
        if _a['q'] >= 1:
            tokens(f"Au SI: combined leader at lambda {_a['q']:g}", s5, f"{pc(_a['winner_2nm_probability'], 2)}%")
    else:
        tokens(f"Au SI: fully inverted at lambda {_a['q']:g}", s5, f"{pc(_a['fully_inverted_fraction'], 2)}%")
_am = main_section('Without a price or selectivity channel the ranking holds, and catalyst life sets its limit')
tokens("Au main: rounded candidate-specific and operating preservation", _am,
       f"{pc(_ap['winner_2nm_probability'], 1)}%", f"{pc(_ap['full_preservation'], 1)}%",
       f"{pc(_auv['L3_semiopen']['primary_273_293K_moderate']['full_preservation_fraction'], 1)}%")

SAB = 'analysis/sabatier_ru_ni_2026_10_19/results/'
_sab = _j(SAB + 'summary.json')
_sc, _smc = _sab['central'], _sab['monte_carlo']
_sab_si = section('Ru against Ni in CO₂ methanation')
tokens("Sabatier main: volume ratio, price ratio and central parity", m_chi,
       f"Π = {_sc['Pi']:.2f} exceeds *r*_V = {_sc['r_V']:.2f}", f"below {_sc['parity_scale_mw']:.2f} MW")
tokens("Sabatier main and SI: MC parity median and interval", m_chi + ' ' + _sab_si,
       f"median {_smc['parity_scale_median_mw']:.2f} MW",
       f"5–95% range {_smc['parity_scale_p05_mw']:.2f}–{_smc['parity_scale_p95_mw']:.1f} MW")
tokens("Sabatier main: endpoint probabilities", m_chi,
       f"Ru is cheaper in {pc(_smc['p_ru_cheaper_by_scale']['0.1'], 1)}% of draws at 0.1 MW and in "
       f"{pc(_smc['p_ru_cheaper_by_scale']['100'], 2)}% at 100 MW")
tokens("Sabatier SI: central costs and precise parity", _sab_si,
       f"Ru costs {_sc['cost_Ru_0p1MW']:.2f} against {_sc['cost_Ni_0p1MW']:.2f}",
       f"{_sc['cost_Ru_100MW']:.2f} against {_sc['cost_Ni_100MW']:.2f} at 100 MW",
       f"parity lies at {_sc['parity_scale_mw']:.3f} MW")
_ss = rows(SAB + 'scenarios.csv')
_bmap = rows(SAB + 'boundary_curve.csv')
tokens("Sabatier SI: deterministic scenario parity range and boundary points", _sab_si,
       f"boundary between {min(float(r['parity_scale_mw']) for r in _ss):.2f} and "
       f"{max(float(r['parity_scale_mw']) for r in _ss):.1f} MW",
       f"all {_sab['boundary']['n_root']} points")
ok("Sabatier sources: deterministic endpoint order and boundary count",
   all(r['ranking_0p1MW'] == 'Ru>Ni' and r['ranking_100MW'] == 'Ni>Ru' for r in _ss)
   and len(_bmap) == _sab['boundary']['n_points'])
_sweep = rows(SAB + 'central_sweep.csv')
_phi10 = next(float(r['phi_proc']) for r in _sweep if abs(float(r['scale_mw'])-10) < 1e-8)
tokens("Sabatier SI: process leverage across scale and at parity", _sab_si,
       f"{_sc['phi_proc_0p1MW']:.2f} at 0.1 MW",
       f"{(_sc['Pi'] / _sc['r_V'] - 1):.2f} at the parity scale",
       f"{_phi10:.2f} at 10 MW", f"{_sc['phi_proc_100MW']:.3f} at 100 MW")

# Captions are part of the live scientific claim, and use their new figure locations.
def _caption(path, heading):
    raw = (ROOT / path).read_text(encoding="utf-8")
    marker = "## " + heading + " |"
    return _block(raw, raw.index(marker), marker).replace("**", "")

_f5 = _caption("docs/MAIN_FIGURE_CAPTIONS.md", "Figure 5")
_ed7 = _caption("figures/extended_data/ED_CAPTIONS.md", "Extended Data Fig. 7")
_ed8 = _caption("figures/extended_data/ED_CAPTIONS.md", "Extended Data Fig. 8")
_ed9 = _caption("figures/extended_data/ED_CAPTIONS.md", "Extended Data Fig. 9")
tokens("Figure 5: owned break-evens and median-rate savings", _f5,
       f"{pc(_bes['KAAP_owned'], 2)} and {pc(_bes['benchmark_owned'], 2)}% per year",
       f"{_rate:.2f}% per year",
       f"{-float(_fr['KAAP_RuC_minus_Fe']):.2f} and {-float(_fr['benchmark_RuC_minus_Fe']):.2f} US dollars per tonne cheaper")
tokens("Figure 5: staged window, Ru fraction and design costs", _f5,
       f"0 to {pc(_bes['staged_Fe_first_beats_Fe_below'], 2)}% per year",
       f"Ru/C {pc(_st['best_Ru_volume_fraction'])}% of the catalyst volume",
       f"{_st['staged']:.2f} against {_st['all_Fe']:.2f} US dollars per tonne")
_b1 = [float(r['signed_deviation']) for r in _et_new
       if r['quantity_group'] == 'bed-1 inlet temperature, cost-optimal designs']
tokens("NH3 SI benchmark: first-bed temperature above industrial window", s1,
       f"first bed {min(_b1):.0f}–{max(_b1):.0f} °C above the industrial window")
_rb_csv = rows(IRD + 'robustness.csv')
for _basis, _col, _word in (("own optima", 'breakeven_global', 'at the own optima'),
                            ("KAAP-type", 'breakeven_KAAP', 'in the KAAP-type loop')):
    _rrates = [float(r[_col]) for r in _rb_csv if r[_col] and math.isfinite(float(r[_col])) and float(r[_col]) > 0]
    tokens(f"Extended Data 7: {_basis} robustness financing range", _ed7,
           f"{pc(min(_rrates), 2)}–{pc(max(_rrates), 2)} % per year {_word}")
tokens("Extended Data 8: candidate-specific scatter preservation", _ed8,
       f"full order kept in {pc(_ap['full_preservation'], 1)} % and 2 nm leader in {pc(_ap['winner_2nm_probability'], 1)} %")
_acomb = {a['q']: a for a in _auv['L2_L3_combined_273_293K_moderate']}
tokens("Extended Data 8: combined lifetime preservation and inversion", _ed8,
       f"full order kept in {pc(_acomb[0]['full_preservation_fraction'], 1)} % at λ = 0, "
       f"{pc(_acomb[1]['full_preservation_fraction'], 1)} % at λ = 1.0 and "
       f"{pc(_acomb[1.9]['full_preservation_fraction'], 1)} % at λ = 1.9",
       f"fully inverted in {pc(_acomb[3]['fully_inverted_fraction'], 1)} % at λ = 3")
tokens("Extended Data 9: central parity and scale-specific probabilities", _ed9,
       f"parity at {_sc['parity_scale_mw']:.2f} MW",
       *[f"{k} MW {pc(v, 2 if k in ('30', '100') else 1)} %" for k, v in _smc['p_ru_cheaper_by_scale'].items()])
tokens("Extended Data 9: price ratio and endpoint process leverage", _ed9,
       f"Π = {_sc['Pi']:.2f}", f"{_sc['phi_proc_0p1MW']:.2f} at 0.1 MW",
       f"{_sc['phi_proc_100MW']:.3f} at 100 MW")
# Roots are counted from the boundary CSV, rather than accepting the summary count alone.
ok("Sabatier source: every boundary root matches the process-leverage criterion",
   sum(r['status'] == 'root' for r in _bmap) == _sab['boundary']['n_root']
   and all(r['status'] == r['status_leverage']
           and (r['status'] != 'root' or abs(float(r['log10_diff'])) < 1e-9) for r in _bmap))

# Reprice every committed measured-kinetics arrangement to recover the actual panel-c design.
_design_rows = rows(IRD + 'staged_KM1R_1964_design_library.csv')
_i_ref = _rate / 100
_cm0 = _mult('dcf', 0, _i_ref)
_cmr = _mult('dcf', r_hi, _i_ref)

def _reference_design_cost(r):
    return float(r['noncatalyst']) + (P_RU * _cmr * float(r['Ru_metal_kg'])
           + _cm0 * (P_FE * float(r['mass_Fe_kg']) + P_SUP * float(r['mass_Ru_cat_kg']))) / LIFE / ANNUAL

_ref_design = min((r for r in _design_rows if (float(r['P_bar']), float(r['Tsep_C'])) == KAAP),
                  key=_reference_design_cost)
_fig5_svg = (ROOT / 'figures/composite/fig_frontier/FigFrontier.svg').read_text(encoding='utf-8')
_volumes = [float(v) for v in _ref_design['beds_volume_m3'].split(';')]
ok("Figure 5: reference-rate bed volumes from repriced measured design library",
   _ref_design['pattern'] == _fr['staged_optimal']
   and abs(_reference_design_cost(_ref_design) - float(_fr['staged_optimal_cost'])) < 1e-5
   and all(f"<!-- {v:.1f} m$^3$ -->" in _fig5_svg for v in _volumes),
   "source bed volumes: " + "/".join(f"{v:.1f}" for v in _volumes) + " m³")

# Semantic definitions that remain in the shortened main-text Methods must be checked there.
tokens("Methods semantic lock: plant-level optimum and candidate-specific operating point", methods,
       "The plant-level optimum of a set of catalysts is the catalyst with the lowest value of its system's objective under the stated process and economic conditions",
       "each catalyst at the operating point that minimizes the objective",
       "The plant-cost leader of a published comparison is its plant-level optimum")
tokens("Methods semantic lock: catalyst identity and ranking over operating points", main_section("CO₂-to-methanol"),
       "What counts as a different catalyst was fixed before any comparison was counted",
       "composition (promoters and dopants included), loading of the active component, support or synthesis",
       "entries of one sample that differ only in reaction temperature, time on stream, activation or reactor operating mode are one catalyst at different operating points",
       "Each catalyst enters the laboratory ranking with its highest space-time yield and the plant ranking with its lowest plant cost over its operating points",
       "a stricter identity merges samples that differ only in synthesis")
_activity_ratio = 10 ** (m['Ru']['activity_logTOF'] - m['Fe']['activity_logTOF'])
_price_ratio = eq['Ru_canonical']['price_USD_kg'] / r8['price_USD_kg']
tokens("NH3 main: intrinsic turnover and metal-price ratios", main_section("The most active ammonia catalyst is not the cheapest to run"),
       f"Ru turns over {_activity_ratio:.0f} times faster than Fe and costs {_price_ratio:,.0f} times more per kilogram")
ok("MeOH main: third-to-two-fifths range is the two model treatments, not a confidence interval",
   "between a third and two-fifths" in m_field
   and pc(_rcat['fraction']) == "33" and pc(_cc['fraction']) == "41"
   and _rcat['groups_2plus_catalysts'] == _cc['groups_2plus_catalysts']
   and f"at {pc(_rcat['fraction'])}–{pc(_cc['fraction'])}%" in s8
   and "this range spans two model treatments and is not a confidence interval" in s8,
   f"source fractions {_rcat['changed']}/{_rcat['groups_2plus_catalysts']} ({pc(_rcat['fraction'], 1)}%) and "
   f"{_cc['changed']}/{_cc['groups_2plus_catalysts']} ({pc(_cc['fraction'], 1)}%)")

# ----- Report -----------------------------------------------------------------
failed = [(label, detail) for label, passed, detail in checks if not passed]
for label, passed, detail in checks:
    print(("PASS " if passed else "FAIL ") + label + (f" | {detail}" if detail else ""))
print(f"{len(checks)} checks, {len(failed)} failed")
raise SystemExit(1 if failed else 0)
