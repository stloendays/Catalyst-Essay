"""Audit the current live manuscript against committed scientific sources.

This checker is intentionally section-aware rather than phrase-fragile. It verifies that
current canonical/derived numbers appear in the Results section where they belong,
including the closed strict-scaling x lifecycle reachability result.

Since the supervisor decisions of 2026-10-12 (docs/SUPERVISOR_FEEDBACK_2026-10-12.md) it checks the
inert-limited methanol loop (S6) as the primary result with the unlimited loop (S5) alongside, the
measured Fe/Ru rate laws and the staged converter, both Ru-inventory financing conventions, and the
reference numbering. The checks follow the wording of the revision of 2026-10-13 (commit 2d9feb2) and cover the
83 -> 40 group ledger table of the Supplementary Information (docs/SI_TABLES.md) and the numbering of the
Supplementary Tables. Standard library only (CI runs it without the project requirements).

Since 2026-10-14 every ammonia check reads the NH3-FINAL-1.2 outputs: the canonical run
provenance/nh3_final_1_2/source_harness/outputs/nh3_final_1_2_20261013 and the ported analyses in <folder>/nh3_1_2/
(same file names as the 1.1 files one level up; READMEs there). The tokens follow the 1.2 wording of the main text and
the Supplementary Information (manuscript-advisor-2026-10-13 at b6e438f), including the direction of each statement where
the source fixes it (e.g. Ru cheaper than Fe where the text says so). Methanol, Au/TiO2 and agent-extraction checks read
the sources they read before.

Result lines: PASS, FAIL (exit code 1) and WARN. WARN marks a manuscript number that disagrees with
its merged source; it is reported, not counted as a failure, because this audit never edits the text.

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
ROOT = Path(__file__).resolve().parents[1]
TEXT_PATH = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "docs/MANUSCRIPT_MAIN_TEXT.md"
HARNESS_12 = ROOT / "provenance/nh3_final_1_2/source_harness"
RUN = HARNESS_12 / "outputs/nh3_final_1_2_20261013"          # canonical NH3-FINAL-1.2 run
SUP = ROOT / "analysis/supervisor_2026_09_20/nh3_1_2"
V12 = "nh3_1_2"                                             # sub-folder of each ported ammonia analysis

raw_text = TEXT_PATH.read_text(encoding="utf-8")
text = re.sub(r"\s+", " ", raw_text).replace("−", "-")
methods = re.sub(r"\s+", " ", raw_text[raw_text.index("## Methods"):]).replace("−", "-")


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


def ok(label, condition, detail="", warn=False):
    """warn=True marks a manuscript number that disagrees with its merged source. It is printed as WARN and counted
    separately, not as a failure: this audit never edits the manuscript, it reports the disagreement."""
    checks.append((label, bool(condition), detail, warn))


def tokens(label, haystack, *needles, warn=False):
    missing = [n for n in needles if n not in haystack]
    ok(label, not missing, "missing: " + ", ".join(missing) if missing else "", warn=warn)


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
tokens(
    "Main text: ammonia ranking reversal, regret and its annual value",
    main_section("Process economics reverse the leading ammonia ranking"),
    f"over {det['process_state_count']:,} process states",
    f"at {m['Fe']['feasible']['total_cost']:.3f}, {m['Ru']['feasible']['total_cost']:.3f} and "
    f"{m['Os']['feasible']['total_cost']:.3f} US dollars per tonne of NH₃",
    f"The Spearman correlation across all 15 metals remains {det['raw_global_spearman']:.3f}, whereas among the three "
    f"leaders Spearman rho is {head['top3_spearman']:.2f}",
    f"would raise the catalyst-dependent cost by {100 * R_NH3:.1f}%",
    f"The {GAP_NH3:.3f} US dollars per tonne difference",
    f"{GAP_NH3 * ANNUAL_T / 1e6:.2f} million US dollars per year for a {_yaml_num(manifest, 'production_tpd'):,.0f} t/d plant",
)

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
tokens(
    "NH3 descriptor error-dependence sensitivity",
    s2,
    f"The independent case gives atomistic-winner frequencies of {100 * float(rho0['P_atomic_top1_Ru']):.1f}% for Ru, "
    f"{100 * float(rho0['P_atomic_top1_Os']):.1f}% for Os and {100 * float(rho0['P_atomic_top1_Fe']):.1f}% for Fe, against "
    f"{100 * _aw['Ru']:.1f}%, {100 * _aw['Os']:.1f}% and {100 * _aw['Fe']:.1f}% in the {len(draws):,} frozen draws",
    f"at latent pairwise correlation {float(rho9['latent_pairwise_correlation']):g}, Fe is the atomistic winner in "
    f"{100 * float(rho9['P_atomic_top1_Fe']):.1f}% of draws compared with {100 * float(rho0['P_atomic_top1_Fe']):.1f}% in "
    f"the matched independent audit",
    "Gaussian copula",
    "common-offset",
)
ok(
    "NH3 copula Fe-top1 anchors: positive error correlation raises the Fe top-1 share (as the text states)",
    int(rho0["n_draws"]) == int(rho9["n_draws"]) > len(draws)
    and float(rho9["P_atomic_top1_Fe"]) > float(rho0["P_atomic_top1_Fe"])
    and all(abs(float(r_["P_atomic_top1_Ru"]) + float(r_["P_atomic_top1_Os"]) + float(r_["P_atomic_top1_Fe"]) - 1)
            < 1e-9 for r_ in (rho0, rho9)),
)

# ----- Results 3: backward target and reachability ----------------------------
s3 = section("Backward design separates the required catalyst-property region from physical reachability")
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
    "NH3 lifecycle parity at the current Ru activity (SI Note 7)",
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
       f"constructed from the {_n_sweep_states} distinct process states already visited by the independently "
       f"reoptimized Ru price sweep")
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
m_bw = main_section("Backward design separates the required catalyst-property region from physical reachability")
tokens(
    "Main text: backward design, scaling reach and the lifecycle closure on the strict-scaling manifold",
    m_bw,
    f"Ru reaches the Fe cost only after a {bw['Ru_activity_break_even_multiplier']:.2f}-fold increase; the 5th–95th "
    f"percentile requirement under economic uncertainty is {a['p05']:.2f}–{a['p95']:.0f}-fold",
    f"at most {bw['Ru_scaling_max_gain_673K']:.3f}-fold at 673 K and {bw['Ru_scaling_max_gain_all_states']:.3f}-fold "
    f"across all process conditions, and the lowest strict-scaling Ru cost, {bw['Ru_best_scaling_cost_USD_t']:.3f} US "
    f"dollars per tonne at *E*_N = {bw['Ru_best_scaling_EN_eV']:.3f} eV, remains above the Fe cost",
    f"at 99% recovery, a 10-year lifetime needs at most a {t10:.3f}-fold gain and a 20-year lifetime none",
    f"across all {SJ['process_states']:,} process states",
    f"\\(q^*={_q / 10 ** _qe:.4f}\\times10^{{{_qe}}}\\ \\mathrm{{y}}^{{-1}}\\)",
    f"At a {_cor['life_y']:.0f}-year lifetime and {100 * _cor['recovery_fraction']:.0f}% recovery the best strict-scaling "
    f"state costs {_cor['best_strict_scaling_cost_USD_t']:.3f} US dollars per tonne, "
    f"{abs(_cor['margin_vs_Fe_USD_t']):.3f} US dollars per tonne below Fe, and parity requires "
    f"{100 * _bx['required_recovery_at_20y']:.3f}% recovery at 20 years or a "
    f"{_bx['required_life_at_99pct_recovery_y']:.2f}-year lifetime at 99% recovery",
)
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
    "1.000",
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
tokens("Au zero decision regret", s5, "zero selection regret")
ok("Au regret source", float(regret["AuTiO2"]["normalized_decision_regret"]) == 0.0)

# ----- Discussion / Methods semantic locks ------------------------------------
discussion = raw_text[raw_text.index("## Discussion"):raw_text.index("## Methods")]
_chi = {"NH3": float(transfer12["NH3"]["pairwise_transfer_index_chi"]),          # NH3-FINAL-1.2
        "MeOH": float(transfer["MeOH"]["pairwise_transfer_index_chi"]),
        "AuTiO2": float(transfer["AuTiO2"]["pairwise_transfer_index_chi"])}
tokens(
    "pairwise transfer-index interpretation",
    discussion,
    "χ_AB",
    f"{_chi['NH3']:+.3f} for Ru versus Fe",
    f"{_chi['MeOH']:+.3f}",
    f"{_chi['AuTiO2']:+.2f}",
)
tokens("Discussion: transfer index read as the share of the upstream advantage that reaches the objective", discussion,
       f"an {float(transfer['AuTiO2']['upstream_metric_ratio_sA_over_sB']):.1f}-fold mass-activity advantage",
       f"an {1 / float(transfer['AuTiO2']['downstream_objective_ratio_JA_over_JB']):.1f}-fold smaller catalyst requirement",
       f"a {float(transfer['MeOH']['upstream_metric_ratio_sA_over_sB']):.1f}-fold space-time-yield advantage ends as a "
       f"{(float(transfer['MeOH']['downstream_objective_ratio_JA_over_JB']) - 1) * 100:.1f}% higher production cost",
       f"a {float(transfer12['NH3']['upstream_metric_ratio_sA_over_sB']):.0f}-fold intrinsic turnover advantage of Ru over Fe "
       f"ends as a {(float(transfer12['NH3']['downstream_objective_ratio_JA_over_JB']) - 1) * 100:.0f}% higher")
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
    "the economic objective contains the terms that respond directly to catalyst identity",
    "Common upstream H₂/N₂ supply contributions are held fixed",
)
tokens(  # the draw-level table itself is checked above ("NH3 regret MC source")
    "NH3 draw-level cost-MC reconstruction lock",
    methods,
    f"The preregistered economic Monte Carlo analysis uses {cmc['draws']:,} samples with seed {cmc['seed']}",
    "The draw sequence is generated from the seed and priors, and normalized regret is computed draw-by-draw as "
    "(C_Ru - C_Fe)/C_Fe",
)
ok(
    "no stale pending joint-reachability language",
    "Strict scaling-consistent joint reachability is not yet promoted" not in raw_text
    and "PENDING_EXACT_CACHE_SWEEP" not in raw_text,
)

# ----- 2026-10-05 additions: actual Ru catalyst cost, literature gains, methanol backward design --------------
ac = {r["key"]: r for r in rows(f"figures/composite/fig2/{V12}/fig2_ru_actual_cost_points.csv")}
tokens(
    "NH3 actual-catalyst cost (Fig. 2d)",
    s2,
    f"exposes {pc(float(ac['supp_rec_hi']['u']) / 100)}% of its Ru atoms",
    f"{float(ac['supp_rec_hi']['p_eff_USD_kg']):.0f}–{float(ac['supp_rec90']['p_eff_USD_kg']):.0f}",
    f"{float(ac['supp_rec_hi']['cost']):.2f}–{float(ac['supp_rec90']['cost']):.2f}",
    # the gap's sign decides the wording: with the 0.9555 recovery bound both ends lie above Fe
    (f"from {abs(float(ac['supp_rec_hi']['gap_to_Fe'])):.2f} below to {float(ac['supp_rec90']['gap_to_Fe']):.2f} above Fe"
     if float(ac['supp_rec_hi']['gap_to_Fe']) < 0 else
     f"{float(ac['supp_rec_hi']['gap_to_Fe']):.2f}–{float(ac['supp_rec90']['gap_to_Fe']):.2f} above Fe"),
    f"{float(ac['supp_rec_hi']['alpha_star']):.1f}–{float(ac['supp_rec90']['alpha_star']):.1f}-fold",
    f"{float(ac['kaap_hi']['cost']):.2f}–{float(ac['kaap90']['cost']):.2f}",
    f"{float(ac['fe_kaap']['cost']):.2f}",
)
ok("NH3 actual-catalyst: Ru/C with recovery below Fe in the KAAP loop",
   float(ac["kaap90"]["cost"]) < float(ac["fe_kaap"]["cost"]) and float(ac["kaap_hi"]["cost"]) < float(ac["fe_kaap"]["cost"]))
_fe_kaap_swap = _j(f"analysis/nh3_staged_converter_2026_10_12/{V12}/kinetics_swap.json")["frozen_anchor_check"]["Fe_KAAP"]
ok("NH3 actual-catalyst: parity without an activity gain at the upper recovery bound only (alpha* < 1 < alpha* at 90 %)",
   float(ac["supp_rec_hi"]["alpha_star"]) < 1 < float(ac["supp_rec90"]["alpha_star"])
   and abs(float(ac["pure"]["cost"]) - m["Ru"]["feasible"]["total_cost"]) < 1e-12
   and abs(float(ac["fe_kaap"]["cost"]) - _fe_kaap_swap["cost"]) < 1e-5)
tokens(
    "Main text: actual-catalyst reading of the price sweep (Fig. 3d)",
    main_section("Metal price and process optimization decide the Fe–Ru ranking"),
    f"Read at the effective Ru price p(1 - r)/u, {float(ac['supp_rec_hi']['p_eff_USD_kg']):.0f}–"
    f"{float(ac['supp_rec90']['p_eff_USD_kg']):.0f} US dollars per kilogram, Ru costs "
    f"{float(ac['supp_rec_hi']['cost']):.2f}–{float(ac['supp_rec90']['cost']):.2f} US dollars per tonne of NH₃, from "
    f"{abs(float(ac['supp_rec_hi']['gap_to_Fe'])):.2f} below to {float(ac['supp_rec90']['gap_to_Fe']):.2f} above Fe, and "
    f"reaches parity without any activity gain at {pc(float(ac['supp_rec_hi']['recovery']), 2)}% recovery "
    f"({float(ac['supp_rec_hi']['alpha_star']):.1f}–{float(ac['supp_rec90']['alpha_star']):.1f}-fold across the recovery "
    f"range",
    f"it costs {float(ac['kaap_hi']['cost']):.2f}–{float(ac['kaap90']['cost']):.2f} in the benchmark reading",
    f"against {float(ac['fe_kaap']['cost']):.2f} for fused iron in that loop",
)
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
    "NH3 literature gains against the 1.2 parity band (SI Note 7)",
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
tokens(
    "Agent pruning, methanol",
    s6,
    f"needs the full optimization for {mp['evaluated']} of the {mp['full']} candidates "
    f"({mp['excluded']} excluded, {mp['excluded_fraction'] * 100:.1f}%)",
    f"plant-cost leader of all {mpr['groups']} groups",
    f"at {mpr['compute_fraction_recycled_opt'] * 100:.0f}% of the compute",
)
ok("Agent pruning, methanol: bound valid and no leader missed", mpr["bound_valid_all"] and mp["leader_missed"] == 0)

FE_COST_ALLOY = _j(ALY + "alloy_backward_summary.json")["Fe_cost_USD_t"]

# ----- NH3 bimetallic surfaces ----------------------------------------------------------------------------------
s7 = section("Outside nitride formers and sp metals, surfaces that undercut Fe pair a cheap 3d metal with a group-6 metal")
m_alloy = main_section("Outside nitride formers and sp metals, surfaces that undercut Fe pair a cheap 3d metal with a "
                       "group-6 metal")
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
tokens(
    "Main text: alloy screen, its activity leader and the lower bound",
    m_alloy,
    f"the {alloy['surfaces_fetched']:,} bimetallic and pure-metal surfaces",
    f"Among the {tm['costed']} surfaces that contain only transition metals outside groups 3–5, {tm['feasible']} satisfy",
    f"{word(len(glob_below), cap=True)} undercut Fe when the database is bridged linearly onto the model's descriptor and "
    f"{word(len(anch_below))} under an element-anchored bridge",
    f"The most active surface ranks {ordinal(rg['upstream_winner_economic_rank'])} economically "
    f"({chem(rg['upstream_winner'])}, {rg['regret'] * 100:.1f}% regret) and at its own price would need a "
    f"{fold(float(lead_g['alpha_star']))}-fold activity increase to reach Fe",
    f"excludes {ext_all['pruning']['pruned']:,} of the {ext_all['costed']:,} priced surfaces "
    f"({ext_all['pruning']['fraction_saved'] * 100:.1f}%)",
)

# ----- NH3 actual-catalyst Monte Carlo -------------------------------------------------------------------------
MCA = f"analysis/nh3_mc_ru_actual_2026_10_06/{V12}/"
mca = _j(MCA + "summary.json")
wa = mca["A_where_Ru_wins"]
s2_full = section("Metal price and process optimization jointly determine the Fe-Ru ranking")
mcd_rows = rows(MCA + "draws.csv")
# every probability recomputed from the committed draw table: Fe against Ru read at p(1 - r)/u (A), on a commercial
# Ru/C bed (A_bed), and with the measured Ru catalysts with and without recovery (B, B0)
_pw = {k: sum(float(r_["Fe"]) < float(r_[f"Ru_{k}"]) for r_ in mcd_rows) / len(mcd_rows) for k in ("A", "A_bed", "B", "B0")}
_b_win = sorted({r_["measured_catalyst"] for r_ in mcd_rows if float(r_["Ru_B"]) < float(r_["Fe"])})
_wt = mca["ranges"]["A_bed_Ru_wt_pct"]
_wt_mid = (_wt[0] + _wt[1]) / 2                                  # the midpoint of the sampled Ru content
tokens(
    "NH3 actual-catalyst Monte Carlo",
    s2_full,
    f"Ru is cheaper in {wa['P_Ru_wins'] * 100:.1f}% of draws when it is read at the effective price p(1 - r)/u in the "
    f"benchmark bed",
    f"and in {mca['A_bed_where_Ru_wins']['P_Ru_wins'] * 100:.1f}% when a commercial Ru/C bed "
    f"({_wt[0]:g}–{_wt[1]:g} wt% Ru, "
    f"{mca['ranges']['bed_density_kg_m3'][0]:.0f}–{mca['ranges']['bed_density_kg_m3'][1]:.0f} kg m⁻³)",
    f"Fe is cheaper in {mca['B']['P_Fe_cheaper'] * 100:.1f}% of draws with recovery and {mca['B0']['P_Fe_cheaper'] * 100:.1f}% without",
    f"the Ru wins come from {word(len(mca['B_Ru_winning_catalysts']))} of the {mca['ranges']['measured_Ru_catalysts']} catalysts",
)
ok("NH3 actual-catalyst MC: base reproduced (same draws as the preregistered 1.2 cost MC)",
   mca["base_reproduced"]["P_Fe_cheaper"] == cmc["full_14136_state_direct_cost_verification"]["P_C_Fe_lt_C_Ru"] == 1.0
   and abs(mca["base_reproduced"]["min_gap_USD_t"]
           - cmc["full_14136_state_direct_cost_verification"]["minimum_Ru_minus_Fe_USD_t"]) < 1e-9
   and len(mcd_rows) == mca["draws"] == cmc["draws"]
   and all(abs(float(r_["Fe"]) - float(c_["Fe_cost_USD_t"])) < 1e-9 for r_, c_ in zip(mcd_rows, cmc_draws)))
ok("NH3 actual-catalyst MC: probabilities and the winning measured catalysts recomputed from the draws; Ru ahead in A and "
   "A_bed, Fe ahead in B and B0 (the direction the text states)",
   all(abs(_pw[k] - mca[k]["P_Fe_cheaper"]) < 1e-12 for k in ("A", "A_bed", "B", "B0"))
   and abs(1 - _pw["A"] - wa["P_Ru_wins"]) < 1e-12 and abs(1 - _pw["A_bed"] - mca["A_bed_where_Ru_wins"]["P_Ru_wins"]) < 1e-12
   and wa["P_Ru_wins"] > 0.5 and mca["A_bed_where_Ru_wins"]["P_Ru_wins"] > 0.5
   and mca["B"]["P_Fe_cheaper"] > 0.5 and mca["B0"]["P_Fe_cheaper"] > 0.5
   and _b_win == sorted(mca["B_Ru_winning_catalysts"]),
   ", ".join(_b_win))


def _win(sel):
    sub_ = [r_ for r_ in mcd_rows if sel(r_)]
    return sum(float(r_["Ru_A_bed"]) < float(r_["Fe"]) for r_ in sub_) / len(sub_)


_tu = _quantiles([float(r_["u"]) for r_ in mcd_rows], [1 / 3, 2 / 3])
_tr = _quantiles([float(r_["r"]) for r_ in mcd_rows], [1 / 3, 2 / 3])
tokens(
    "NH3 actual-catalyst MC: where Ru wins",
    s2_full,
    f"Ru wins in {_win(lambda r_: float(r_['u']) < _tu[0]) * 100:.0f}% of draws with u in its lowest tercile",
    f"{_win(lambda r_: float(r_['u']) >= _tu[1]) * 100:.0f}% with u in its top tercile",
    f"{_win(lambda r_: float(r_['u']) >= _tu[1] and float(r_['r']) >= _tr[1]) * 100:.0f}% with u and r both in their top terciles",
    f"from {_win(lambda r_: float(r_['r']) < _tr[0]) * 100:.0f}% to {_win(lambda r_: float(r_['r']) >= _tr[1]) * 100:.0f}% "
    "between its lowest and top terciles",
    f"from {_win(lambda r_: float(r_['A_bed_wt_pct']) < _wt_mid) * 100:.0f}% below {_wt_mid:g} wt% to "
    f"{_win(lambda r_: float(r_['A_bed_wt_pct']) >= _wt_mid) * 100:.0f}% above",
)
ok("NH3 actual-catalyst MC: the audit's terciles and split reproduce the committed where-Ru-wins summary",
   all(abs(x - y) < 1e-9 for x, y in zip(_tu, mca["A_bed_where_Ru_wins"]["u_terciles"]))
   and abs(_win(lambda r_: float(r_["u"]) < _tu[0]) - mca["A_bed_where_Ru_wins"]["P_Ru_wins_given_u_lowest_tercile"]) < 1e-12
   and abs(_win(lambda r_: float(r_["A_bed_wt_pct"]) < _wt_mid)
           - mca["A_bed_where_Ru_wins"]["P_Ru_wins_given_Ru_content_lt_7.5_wt_pct"]) < 1e-12)
tokens(
    "Main text: actual-catalyst Monte Carlo summary",
    main_section("Metal price and process optimization decide the Fe–Ru ranking"),
    f"Ru is cheaper in {mca['A_bed_where_Ru_wins']['P_Ru_wins'] * 100:.1f}% of draws for a commercial Ru/C bed "
    f"({_wt[0]:g}–{_wt[1]:g} wt% Ru, {mca['ranges']['bed_density_kg_m3'][0]:.0f}–"
    f"{mca['ranges']['bed_density_kg_m3'][1]:.0f} kg m⁻³), whereas Fe stays cheaper in {mca['B']['P_Fe_cheaper'] * 100:.1f}% "
    f"with the activities and Ru contents of the {mca['ranges']['measured_Ru_catalysts']} measured Ru catalysts",
)

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
    "Main text: measured catalysts of the review (rate and cost uncorrelated, two undercut Fe)",
    main_section("Published laboratory leaders are often not the plant-cost leaders"),
    f"Across the {sup['primary']} catalysts tabulated in a review of ammonia-synthesis catalysts",
    f"laboratory rate and plant cost are uncorrelated (Spearman ρ = {ov['spearman_rate_vs_cost']:.2f}), and only "
    f"{word(len(_below))} of them",
    f"undercut the fused-iron benchmark without metal recovery, by {_and(_below_pct)}",
)
errata = rows("agent/nh3_supported/out/primary_errata.csv")
tokens("NH3 measured: errata and Methods row count", text,
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
    f"extracted {fd['papers_in_set']} primary ammonia-synthesis papers",
    f"For the {fev['matched']} entries that the review also tabulates",
    f"the rate in {fev['matched'] - rate_ev['extraction_errors']} of {fev['matched']}",
    f"form {FP['groups']} comparisons",
    f"in {FP['top1_mismatch_groups']} of them ({FP['top1_mismatch_fraction'] * 100:.0f}%; 95% confidence interval "
    f"{fci[0] * 100:.0f}–{fci[1] * 100:.0f}% from resampling papers), in {FP['papers_with_mismatch']} of {FP['papers']} papers",
    f"median regret of {FP['regret_median_mismatched'] * 100:.0f}%",
    f"in {fk['different metal']['groups']} comparisons a catalyst of another metal is the plant-cost leader, "
    f"in {_fe_dm} of them an Fe catalyst on the same support",
    f"in {fk['fused-Fe reference vs supported catalyst']['groups']} a commercial fused-iron catalyst",
    f"With 90% Ru recovery the disagreement is {FV['Ru_recovery_90pct']['top1_mismatch_groups']} of {FP['groups']}",
    f"raises it to {FV['per_g_metal_leaderboard']['top1_mismatch_groups']}",
    f"With plot-read entries included the comparisons number {FV['all_entries']['groups']} and the disagreement "
    f"{FV['all_entries']['top1_mismatch_groups']}",
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
tokens(
    "NH3 field: printed entries below the Fe benchmark",
    s9,
    f"{word(len(_fc), cap=True)} printed entries in this set undercut the fused-iron benchmark: the commercial fused-iron "
    f"reference of one paper ({float(_fc_fused[0]['cost_USD_t']):.2f} US dollars per tonne)" if len(_fc_fused) == 1 else
    "one fused-iron reference below Fe",
    f"a {_fc_other[0]['metal_wt_pct']} wt% {_fc_other[0]['catalyst'].split('-')[0]} catalyst at {_fc_other[0]['T_C']} °C and "
    f"{_fmt_p(_fc_other[0]['P_MPa'])} MPa ({float(_fc_other[0]['cost_USD_t']):.2f}) and at {_fc_other[1]['T_C']} °C and "
    f"{_fmt_p(_fc_other[1]['P_MPa'])} MPa ({float(_fc_other[1]['cost_USD_t']):.2f})" if len(_fc_other) == 2 else
    "two other entries below Fe",
)
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
    "SI Note 4: second batch and both batches",
    s9,
    f"of {fx['screening']['screened']} screened papers, {fx['screening_with_si']['included']} were included, and "
    f"{B2['papers']} of them supply {B2['groups']} comparisons with printed values",
    f"In {B2['mismatch']} of the {B2['groups']} the laboratory leader is not the plant-cost leader ({pc(B2['fraction'])}%; "
    f"95% confidence interval {pc(B2['ci95'][0], 1)}–{pc(B2['ci95'][1], 1)}%), in {B2['papers_with_mismatch']} of the "
    f"{B2['papers']} papers, with a median regret of {pc(B2['regret_median_mismatched'])}% where the leaders differ; in "
    f"{B2['kinds']['fused-Fe reference vs supported catalyst']} of the {B2['mismatch']} a fused-iron reference catalyst is "
    f"the plant-cost leader",
    f"Across both batches the leaders differ in {PL['mismatch']} of {PL['groups']} comparisons ({pc(PL['fraction'])}%; 95% "
    f"confidence interval {pc(PL['ci95'][0])}–{pc(PL['ci95'][1])}%), in {PL['papers_with_mismatch']} of {PL['papers']} "
    f"papers, and {PL['regret_gt5pct']['groups']} of the {PL['mismatch']} have a regret above 5%",
    f"Without the commercial fused-iron references the disagreement is {R1V['without_fused_Fe_references']['mismatch']} of "
    f"{R1V['without_fused_Fe_references']['groups']} in the first batch and {PLV['without_fused_Fe_references']['mismatch']} "
    f"of {PLV['without_fused_Fe_references']['groups']} across both; ranking by rate per gram of metal gives "
    f"{PLV['per_g_metal_leaderboard']['mismatch']} of {PLV['per_g_metal_leaderboard']['groups']}, 90% Ru recovery "
    f"{PLV['Ru_recovery_90pct']['mismatch']} of {PLV['Ru_recovery_90pct']['groups']}, and with plot-read entries included "
    f"the leaders differ in {PLV['all_entries']['mismatch']} of {PLV['all_entries']['groups']} comparisons",
    f"In {len(_p_below)} of the {PL['groups']} comparisons the plant-cost leader undercuts the fused-iron benchmark: the "
    f"{word(len(_p_fused))} commercial fused-iron references "
    f"({min(float(r['plant_winner_cost']) for r in _p_fused):.2f}–{max(float(r['plant_winner_cost']) for r in _p_fused):.2f} "
    f"US dollars per tonne) and the {_p_other[0]['plant_winner'].split('-')[0]} catalyst at {_p_other_c[0]['T_C']} °C and "
    f"{_fmt_p(_p_other_c[0]['P_MPa'])} MPa ({float(_p_other[0]['plant_winner_cost']):.2f})" if len(_p_other) == 1
    and _p_other_c else "one non-fused plant-cost leader below Fe",
)
tokens(
    "Main text: second batch and both batches",
    main_section("Published laboratory leaders are often not the plant-cost leaders"),
    f"adds {B2['groups']} comparisons from {B2['papers']} papers, {B2['mismatch']} of them with a different leader; across "
    f"both batches the leaders differ in {PL['mismatch']} of {PL['groups']} comparisons ({pc(PL['fraction'])}%; 95% "
    f"confidence interval {pc(PL['ci95'][0])}–{pc(PL['ci95'][1])}%), and in {R1V['without_fused_Fe_references']['mismatch']} "
    f"of {R1V['without_fused_Fe_references']['groups']} and {PLV['without_fused_Fe_references']['mismatch']} of "
    f"{PLV['without_fused_Fe_references']['groups']} when the commercial fused-iron references are removed",
)
tokens("Methods: second batch of ammonia papers", methods,
       f"A second batch of {fx['screening']['screened']} papers was screened, extracted with Supporting Information and "
       f"scored under a protocol committed before extraction ({fx['screening_with_si']['included']} included)")

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
cvr = _j("analysis/verify_2026_10_12_s6_conversion/s6_conversion_summary.json")["scenarios"]
cv5 = _j("analysis/meoh_literature_inversion_2026_10_05/conversion_sensitivity_summary.json")["scenarios"]
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
tokens("Main text: 83 -> 40 comparison groups", m_field,
       f"giving {pp['groups']} comparisons with {pp['entries']} entries in {pp['papers']} papers; with plot-read values "
       f"the same rule gives {ae['groups']} comparisons in {ae['papers']} papers")
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
_ledger_csv = rows("analysis/meoh_inlet_definition_2026_10_12/group_ledger.csv")
ok(f"SI Table {LEDGER_TABLE}: the 83 -> 40 ledger lists every group once (83 rows, 40 kept) with the ledger's drop reasons",
   _lt is not None and (int(_lt.group(2)), int(_lt.group(3))) == (ae["groups"], pp["groups"])
   and len(_lrows) == len(_ledger_csv) == ae["groups"] == 83
   and len({(r[1], r[2]) for r in _lrows}) == len(_lrows)
   and _lstat.count("kept") == pp["groups"] == 40
   and _lstat.count("dropped: no printed values in the paper") == gr["paper without printed values"]
   and _lstat.count("dropped: fewer than two printed entries") == gr["fewer than 2 printed entries"],
   f"{len(_lrows)} rows, {_lstat.count('kept')} kept" if _lt else "table not found in docs/SI_TABLES.md")
ok(f"SI Table {LEDGER_TABLE}: verdict totals equal the frozen S6/S5 primary and the all-entries sensitivity",
   len(_ltot) == 1 and _ltot[0][-4:] == [f"**{n6} of {g6}**", f"**{n5} of {g5}**"] + [
       f"**{led['all_entries_result'][k]['different_leader']} of {led['all_entries_result'][k]['groups']}**"
       for k in ("S6_6_86pct", "S5")],
   " | ".join(_ltot[0][-4:]) if _ltot else "no total row")
tokens("Methods: 83 -> 40 comparison groups", methods,
       f"of the {ae['groups']} groups that include plot-read values, {gr['paper without printed values']} come from "
       f"{pr['paper without printed values']} papers without printed values and {gr['fewer than 2 printed entries']} have "
       f"fewer than two printed entries, which leaves the {pp['groups']} groups of the primary analysis (Supplementary "
       f"Table {LEDGER_TABLE})")
tokens("SI Note 3: 83 -> 40 comparison groups", s8,
       f"giving {pp['groups']} comparisons with {pp['entries']} entries in {pp['papers']} papers. With plot-read values the "
       f"same rule gives {ae['groups']} comparisons in {ae['papers']} papers; {gr['paper without printed values']} of them "
       f"come from {pr['paper without printed values']} papers without printed values and "
       f"{gr['fewer than 2 printed entries']} have fewer than two printed entries (Supplementary Table {LEDGER_TABLE})")

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

# main text: field result
tokens("Main text: methanol field result, inlet-limited loop (S6) primary and S5 alongside", m_field,
       f"{lit['candidates']} operating points from {lit['papers_with_candidates']} studies",
       f"CO, methane and N₂ together are limited to {pc(LIM, 2)}% of the reactor inlet, the cost model's limit for the "
       f"loop that anchors it ({dfmt(dsum(_anchor, CMN), 2)}% CO and N₂ in that loop's stream table",
       f"not the plant-cost leader in {n6} of {g6} comparisons ({s6pc}%; 95% confidence interval "
       f"{pc(ci6[0])}–{pc(ci6[1])}% from resampling papers), {gt5_6} of them with a cost gap above 5%, spread over "
       f"{S6['papers_with_mismatch']} of the {S6['papers']} papers, and {inv6[0]:,} of {inv6[1]:,} pairwise orderings "
       f"({pc(S6['pairwise_inversion_fraction'])}%) invert",
       f"the leaders differ in {n5} of {g5} comparisons ({s5pc}%), {gt5_5} of them above 5%",
       f"the laboratory leader is not the plant-cost leader in {s5pc}–{s6pc}% of comparisons")


def _scan(defn, lim):
    return idf["scenarios"][f"{defn}|{lim}"]


_band = [_scan("frozen", L) for L in idf["limits_pct"] if L != "none" and 5 <= float(L) <= 10]
tokens("Main text: 5-15 % stability of the inlet limit", m_field,
       f"inlet limits of 5–10% ({min(s['different_leader'] for s in _band)}–{max(s['different_leader'] for s in _band)} "
       f"of {g6}, {min(s['gt5pct'] for s in _band)}–{max(s['gt5pct'] for s in _band)} above 5%)",
       f"weakens towards 15% ({_scan('frozen', '12')['different_leader']} and {_scan('frozen', '15')['different_leader']} "
       f"of {g6} at 12% and 15%, {_scan('frozen', '12')['gt5pct']} and {_scan('frozen', '15')['gt5pct']} above 5%")
oc6, sT6, oT6 = k6["other_catalyst"], k6["cat_sameT"], k6["other_temperature"]
tokens("Main text: kinds of S6 disagreement", m_field,
       f"another catalyst in {oc6['groups']} of the {oc6['of']} comparisons that contain at least two catalysts, "
       f"{oc6['gt5pct']} of them above 5%; in {sT6['groups']} it runs at the paper leader's temperature, {sT6['gt5pct']} "
       f"of these above 5% and from {sT6['gt5pct_papers']} papers",
       f"same catalyst at another temperature in {oT6['groups']} of the {oT6['of']} comparisons that contain a temperature "
       f"series, {oT6['gt5pct']} above 5%")
_gm6 = [r for r in rows("analysis/meoh_literature_inversion_2026_10_05/group_metrics_inlet_limit.csv")
        if r["top1_mismatch"] == "True"]
_sT = [r for r in _gm6 if r["kind"] == "other catalyst, same temperature"]
_sT5 = [r for r in _sT if float(r["regret"]) > 0.05]
ok("MeOH S6 kinds recomputed from the frozen group metrics",
   len(_gm6) == n6 and len(_sT) == sT6["groups"] and len(_sT5) == sT6["gt5pct"]
   and len({r["doi"] for r in _sT5}) == sT6["gt5pct_papers"])
lS6, lX6, lS5, lX5 = F6["leaderboard_SMeOH"], F6["leaderboard_X"], F5["leaderboard_SMeOH"], F5["leaderboard_X"]
tokens("Main text: other laboratory metrics (conversion and selectivity in both loops)", m_field,
       f"in the inert-limited loop ranking by conversion disagrees almost as often as ranking by space-time yield "
       f"({lX6['disagreements']} of {lX6['groups']}) and ranking by methanol selectivity in {lS6['disagreements']} of "
       f"{lS6['groups']}, with larger misses (median regret {pc(lS6['median_regret_disagreements'])}%); without the limit "
       f"selectivity is the worst proxy ({lS5['disagreements']} of {lS5['groups']})")
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
tokens("Main text: S6 robustness (sampling, measurement, near-infeasibility, sensitivities)", m_field,
       f"Re-measuring every entry {st6['noise_model']['draws']:,} times",
       f"keeps {km1_6['observed_mismatches_kept_in_ge_90pct']} of the {n6} disagreements in at least 90% of "
       f"re-measurements, whereas measurement noise alone changes a paper's space-time-yield leader in "
       f"{km1_6['sty_leader_differs_from_reported_mean']:.0f} comparisons (95% range {nfq[0]:.0f}–{nfq[1]:.0f})",
       f"In {ni['near-infeasible']['groups']} of the {n6} the paper leader meets the inlet limit only with a large purge "
       f"and costs more than twice its cost without the limit; the other {ni['ordinary']['groups']}, "
       f"{ni['ordinary']['gt5pct']} of them above 5%, involve no such jump",
       f"without the study that supplies most comparisons ({wb6['disagreements']} of {wb6['groups']}, {wb6['gt5pct']} "
       f"above 5%)",
       f"when plot-read entries are added ({ae6['different_leader']} of {ae6['groups']} comparisons)",
       f"close to methanol, CO and methane ({cl6['disagreements']} of {cl6['groups']})",
       f"set to either bound ({min(sp6)}–{max(sp6)} of {g6})",
       f"with recycled CO treated as inert ({ic6['disagreements']} of {ic6['groups']})",
       f"priced from its composition ({cc6['disagreements']} of {cc6['groups']})",
       f"raise its conversion towards equilibrium ({cr6['top1_mismatch_groups']} of {cr6['groups']}, {cr6['gt5pct']} "
       f"above 5%, from {cr6['gt5pct_papers']} papers)",
       f"Limiting methane and N₂ alone and leaving CO unlimited gives {co6['disagreements']} of {co6['groups']}, "
       f"{co6['gt5pct']} above 5%")
_nb = bnd["scenarios"]["S6"]["near_infeasibility"]
ok("MeOH S6 near-infeasible: every one meets the twofold-cost rule (as the text describes them)",
   _nb["by_criterion"]["lab_cost_gt2x_S5"] == ni["near-infeasible"]["groups"] == _nb["near_infeasible"]["groups"]
   and ni["ordinary"]["groups"] + ni["near-infeasible"]["groups"] == n6)

# main text: mechanism and the InNi3C0.5 example
mc6, mc5 = F6["mechanism"], F5["mechanism"]
_none = _scan("frozen", "none")
tokens("Main text: by-product mechanism of the S6 disagreements", m_field,
       f"the reactor feed carries a median {pc(_none['co_share_median'], 1)}% CO",
       f"against {min(_pub_co):.1f}–{max(_pub_co):.1f}% in published loop designs",
       f"more selective to methanol than the paper leader in {mc6['plant_leader_more_selective']['count']} of the "
       f"{mc6['disagreements']} disagreements and makes less CO in {mc6['plant_leader_less_CO']['count']}",
       f"higher single-pass conversion ({mc5['plant_leader_higher_conversion']['count']} of {mc5['disagreements']})")
_gm40 = {r["group"] for r in rows("analysis/meoh_literature_inversion_2026_10_05/group_metrics.csv")}
_ec = [r for r in rows("analysis/meoh_inlet_definition_2026_10_12/entry_costs.csv") if r["group"] in _gm40]
_co_none = sorted(float(r["co_frozen_none"]) for r in _ec)
_coq = _quantiles(_co_none, [0.1, 0.9])
ok("MeOH S5 inlet CO: median of the 310 scored entries equals the merged summary",
   len(_ec) == P0["entries"] and abs(_quantiles(_co_none, [0.5])[0] - _none["co_share_median"]) < 1e-9)
tokens("Main text: inlet CO without the limit, median and 90th percentile", m_field,
       f"median {pc(_none['co_share_median'], 1)}% CO (90th percentile {pc(_coq[1])}%)")
_cand = rows("analysis/meoh_literature_inversion_2026_10_05/literature_candidates.csv")
_gm5 = {r["group"]: r for r in rows("analysis/meoh_literature_inversion_2026_10_05/group_metrics.csv")}
_ex = []
for g in _gm6:      # S6 disagreements whose STY leader is on m-ZrO2, S6 plant leader on SiO2, and no S5 disagreement
    if ("InNi3C0.5/m-ZrO2" in g["upstream_winner"] and "InNi3C0.5/SiO2" in g["economic_winner"]
            and _gm5[g["group"]]["top1_mismatch"] == "False"):
        a = next(c for c in _cand if c["group"] == g["group"] and c["catalyst"] == g["upstream_winner"])
        b = next(c for c in _cand if c["group"] == g["group"] and c["catalyst"] == g["economic_winner"])
        _ex.append((g["group"],
                    f"at {float(a['T_C']):.0f} °C and {float(a['P_bar']) / 10:.0f} MPa",
                    f"the space-time-yield leader on m-ZrO₂ ({pc(float(a['X']), 1)}% conversion, {pc(float(a['SMeOH']))}% "
                    f"methanol selectivity, {pc(float(a['SCO']))}% CO) needs a {pc(float(a['purge_recycled_opt_inlet']), 1)}% "
                    f"purge and costs {float(a['cost_recycled_opt_inlet']):,.0f} euros per tonne, against "
                    f"{float(b['cost_recycled_opt_inlet']):,.0f} for the catalyst on SiO₂ ({pc(float(b['X']), 1)}% conversion, "
                    f"{pc(float(b['SMeOH']))}% selectivity, {pc(float(b['SCO']))}% CO) at "
                    f"{pc(float(b['purge_recycled_opt_inlet']), 1)}% purge; without the limit the order is reversed, "
                    f"{float(a['cost_recycled_opt']):,.0f} against {float(b['cost_recycled_opt']):,.0f}"))
_hit = [e for e in _ex if e[1] in m_field and e[2] in m_field]
ok("Main text: InNi3C0.5 example (S6 leader on SiO2, S5 leader on m-ZrO2) matches one frozen group",
   len(_hit) == 1, "" if _hit else "expected one of: " + " || ".join(e[1] + " ... " + e[2] for e in _ex))
_bd = bnd["bansode_doi"]
_bgm5 = [r for r in _gm5.values() if r["doi"] == _bd]
_maxdoi = [max(rows(f"analysis/meoh_literature_inversion_2026_10_05/{f}"), key=lambda r: float(r["regret"]))["doi"]
           for f in ("group_metrics.csv", "group_metrics_inlet_limit.csv")]
ok("MeOH: the high-pressure Cu/Al2O3 study supplies the largest regret in both loops",
   _maxdoi == [_bd, _bd] and len(_bgm5) == bnd["bansode_groups"] and "c2cy20604h" in V["without_paper_with_most_groups"]["variant"])
tokens("Main text: the high-pressure Cu/Al2O3 study", m_field,
       f"supplies {bnd['bansode_groups']} of the {g6} comparisons[35] gives the largest regrets in both loops")

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
    tokens("Main text: Re/TiO2 states under the inlet limit (order, costs, space-time-yield winner's regret)",
           main_section("Selectivity, recycle and purge reshape the methanol ranking"),
           f"Within the {pc(LIM, 2)}% inlet limit, at each state's optimal purge, the order becomes "
           + _and(f"{h['Re_wt%']} wt% Re at {float(h['T_C']):.0f} °C" for h, _ in _hbs)
           + " (" + _and(f"{float(e['cost_recycled_opt_inlet']):,.0f}" for _, e in _hbs) + " euros per tonne), and the "
           f"space-time-yield winner stays {['first', 'second', 'third', 'fourth'][_hbs.index(_hbw)]}, now at "
           f"{pc(_hbr, 1)}% regret")

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
       f"median {pc(_none['co_share_median'], 1)}% CO (10th–90th percentile {pc(_coq[0], 1)}–{pc(_coq[1])}%), against "
       f"{min(_pub_co):.1f}–{max(_pub_co):.1f}% in the published designs",
       "CO makes up more than 80% of the limited quantity",
       f"the median purge rises from {pc(_none['purge_median'], 1)}% to {pc(_scan('frozen', '6.86')['purge_median'], 1)}%")
ok("MeOH S6: CO is more than 80 % of the limited inlet quantity at the limited optimum",
   _scan("frozen", "6.86")["co_fraction_of_nonreactive_median"] > 0.8)
r1_6 = {r["threshold"]: r for r in st6["regret_threshold_curve"]}
r1_5 = {r["threshold"]: r for r in st5["regret_threshold_curve"]}
tokens("SI Note 3: S6 primary and S5 alongside", s8,
       f"{lit['candidates']} operating points", f"from {lit['papers_with_candidates']} studies",
       f"giving {P0['groups']} comparisons with {P0['entries']} entries in {P0['papers']} papers",
       f"in {n6} of {g6} comparisons ({s6pc}%; 95% confidence interval {pc(ci6[0])}–{pc(ci6[1])}% from resampling "
       f"papers), {gt5_6} of them with a cost gap above 5%, spread over {S6['papers_with_mismatch']} of the "
       f"{S6['papers']} papers ({p6['gt5pct_papers']} with a gap above 5%), and {inv6[0]:,} of {inv6[1]:,} pairwise "
       f"orderings invert",
       f"Without the limit the leaders differ in {n5} of {g5} ({s5pc}%; {pc(ci5[0])}–{pc(ci5[1])}%), {gt5_5} above 5%, "
       f"in {P0['papers_with_mismatch']} papers, and {inv5[0]:,} of {inv5[1]:,} orderings invert",
       f"The regret exceeds 1%, 5% and 10% in {r1_6[0.01]['groups']}, {r1_6[0.05]['groups']} and {r1_6[0.1]['groups']} "
       f"of the {n6} disagreements ({r1_5[0.01]['groups']}, {r1_5[0.05]['groups']} and {r1_5[0.1]['groups']} of the {n5} "
       f"without the limit)",
       f"Of the {oc6['of']} comparisons that contain at least two catalysts, {oc6['groups']} have another catalyst as "
       f"plant-cost leader ({oc6['gt5pct']} above 5%; without the limit {k5['other_catalyst']['groups']}, "
       f"{k5['other_catalyst']['gt5pct']} above 5%), {sT6['groups']} of them at the paper leader's temperature "
       f"({sT6['gt5pct']} above 5%, from {sT6['gt5pct_papers']} papers; "
       + ("none" if k5["cat_sameT"]["gt5pct"] == 0 else str(k5["cat_sameT"]["gt5pct"])) + " above 5% without the limit)",
       f"of the {oT6['of']} that contain a temperature series, {oT6['groups']} have the same catalyst at another "
       f"temperature as plant-cost leader ({oT6['gt5pct']} above 5%; without the limit {k5['other_temperature']['groups']}, "
       f"{k5['other_temperature']['gt5pct']} above 5%)",
       f"Ranking by methanol selectivity disagrees in {lS6['disagreements']} of {lS6['groups']} comparisons with a median "
       f"regret of {pc(lS6['median_regret_disagreements'])}% ({lS5['disagreements']} of {lS5['groups']} and "
       f"{pc(lS5['median_regret_disagreements'])}% without the limit), and ranking by conversion in {lX6['disagreements']} "
       f"of {lX6['groups']} ({lX5['disagreements']} without the limit)")
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
tokens("SI Note 3: inlet-limit scan 4-30 %, CO-excluded limit and inert CO", s8,
       f"At limits of {_and(_lims)}% the leaders differ in {_and(_scan('frozen', L)['different_leader'] for L in _lims)} "
       f"of {g6} comparisons, with {_and(_scan('frozen', L)['gt5pct'] for L in _lims)} above 5%",
       f"in the paper-resampling interval the excess over the unlimited loop stays above zero up to {pc(_ex_dl)}% for all "
       f"disagreements and up to {pc(_ex_g5)}% for those above 5%, and vanishes at {pc(_ex_gone)}%",
       f"With plot-read entries the inert-limited loop scores {ae6['groups']} of the {ae['groups']} groups, because "
       f"{['no', 'one', 'two', 'three'][ae['groups'] - ae6['groups']]} group keeps fewer than two entries that can meet "
       f"the limit",
       f"gives {min(_ti)}–{max(_ti)} of {g6} at every limit ({co6['disagreements']} at {pc(LIM, 2)}%, {co6['gt5pct']} above "
       f"5%)",
       f"Treating recycled CO as inert gives {ic5['disagreements']} of {ic5['groups']} without the limit ({ic5['gt5pct']} "
       f"above 5%) and {ic6['disagreements']} with it ({ic6['gt5pct']} above 5%)")
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
tokens("SI Note 3: S6 robustness and sensitivities", s8,
       f"keeps {km1_6['observed_mismatches_kept_in_ge_90pct']} of the {n6} disagreements in at least 90% of "
       f"re-measurements ({km1_5['observed_mismatches_kept_in_ge_90pct']} of {n5} without the limit), whereas measurement "
       f"noise alone changes a paper's space-time-yield leader in {km1_6['sty_leader_differs_from_reported_mean']:.0f} "
       f"comparisons (95% range {nfq[0]:.0f}–{nfq[1]:.0f}); at twice the noise "
       f"{km2_6['observed_mismatches_kept_in_ge_90pct']} of {n6} stay",
       f"In {ni['near-infeasible']['groups']} of the {n6} disagreements the paper leader meets the limit only with a large "
       f"purge and costs more than twice its cost without the limit (near-infeasible); the other {ni['ordinary']['groups']} "
       f"({ni['ordinary']['gt5pct']} above 5%, {len(_rob_g & _ord)} of them robust to re-measurement) involve no such jump",
       f"without the study that supplies most comparisons ({wb6['disagreements']} of {wb6['groups']}, {wb6['gt5pct']} above "
       f"5%; {wb5['disagreements']} of {wb5['groups']} without the limit)",
       f"when entries with plot-read values are added ({ae6['different_leader']} of {ae6['groups']} comparisons; "
       f"{ae5['different_leader']} of {ae5['groups']} without the limit)",
       f"close to methanol, CO and methane ({cl6['disagreements']} of {cl6['groups']})",
       f"set to either bound ({min(sp6)}–{max(sp6)} of {g6})",
       f"over three years ({cc6['disagreements']} of {cc6['groups']}, {cc6['gt5pct']} above 5%)",
       f"raise its conversion towards equilibrium gives {cr6['top1_mismatch_groups']} of {cr6['groups']}, {cr6['gt5pct']} "
       f"above 5% from {cr6['gt5pct_papers']} papers, with another catalyst at the same temperature above 5% in "
       f"{cr6['gt5pct_by_kind']['other catalyst, same temperature']['groups']} comparisons from "
       f"{cr6['gt5pct_by_kind']['other catalyst, same temperature']['papers']} papers; without the limit the same "
       f"allowance gives {cr5['top1_mismatch_groups']} of {cr5['groups']}, {cr5['gt5pct']} above 5%")
pbs = _j("analysis/meoh_literature_inversion_2026_10_05/purge_boundary_summary.json")
_pbb, _pbx = pbs["boundary"], pbs["boundary"]["at_extended_optimum"]
_pext = [r for r in rows("analysis/meoh_literature_inversion_2026_10_05/group_metrics_purge_extended.csv")
         if r["top1_mismatch"] == "True"]
ok("MeOH S5 purge optimum at the 0.5 % grid floor for every entry", _pbb["canonical_optimum_at_0p5pct"] == pbs["entries"])
tokens("SI Note 3: S5 purge grid extended below 0.5 %", s8,
       f"moves it below 0.5% for {_pbb['extended_optimum_below_0p5pct']} of {pbs['entries']} entries (median "
       f"{pc(_pbx['purge']['median'], 3)}%)",
       f"a median {pc(_pbx['inlet_mol_frac']['nonreactive']['median'])}% of species other than H₂ and CO₂ at a recycle "
       f"ratio of {_pbx['recycle_ratio']['median']:.0f}, against {pbs['anchor_loop']['recycle_ratio']:.2f} in the anchor loop",
       f"the disagreement is {len(_pext)} of {pbs['groups']}, {sum(float(r['regret']) > 0.05 for r in _pext)} above 5%")
tokens("SI Note 3: by-product mechanism and the Cu/Al2O3 study", s8,
       f"more selective to methanol than the paper leader in {mc6['plant_leader_more_selective']['count']} of the "
       f"{mc6['disagreements']} disagreements, makes less CO in {mc6['plant_leader_less_CO']['count']} and runs at higher "
       f"single-pass conversion in {mc6['plant_leader_higher_conversion']['count']}; without the limit it runs at higher "
       f"conversion in {mc5['plant_leader_higher_conversion']['count']} of {mc5['disagreements']}",
       f"supplies {bnd['bansode_groups']} of the {g6} comparisons and the largest regrets in both loops",
       f"without it the leaders differ in {wb6['disagreements']} of {wb6['groups']} comparisons with the limit and in "
       f"{wb5['disagreements']} of {wb5['groups']} without it")

# Methods: definition of the limit and of near-infeasibility
_lim_scen = [v["limit"] for k, v in bnd["scenarios"].items() if k.startswith("lim")]
tokens("Methods: inlet limit, its scan and the near-infeasibility rule", methods,
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
tokens("Abstract headline numbers", text, f"{ext_all['costed']:,} alloy and metal surfaces",
       f"{lit['papers_with_candidates']} methanol studies and {fd['papers_in_set']} ammonia studies",
       f"in {pc(FP['top1_mismatch_fraction'])}% of ammonia cases and in {s5pc}–{s6pc}% of methanol cases",
       f"({gt5_5} and {gt5_6} of {g6} with a cost gap above 5%)")
tokens("Discussion: field-level shares", main_section_h2("Discussion"),
       f"in {pc(FP['top1_mismatch_fraction'])}% of ammonia comparisons and, depending on whether the recycle loop limits "
       f"the species that build up at the reactor inlet, in {s5pc}–{s6pc}% of methanol comparisons ({gt5_5} and {gt5_6} "
       f"of {g6} with a cost gap above 5%)",
       "ranking by conversion or by selectivity fails as well, with larger misses")
tokens("Results: single-metric proxies in the methanol field", m_field,
       f"ranking by conversion disagrees almost as often as ranking by space-time yield ({lX6['disagreements']} of "
       f"{lX6['groups']}) and ranking by methanol selectivity in {lS6['disagreements']} of {lS6['groups']}",
       f"without the limit selectivity is the worst proxy ({lS5['disagreements']} of {lS5['groups']})")

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
tokens("Methods: response-surface validation of the primary (S6) noise result", methods, _rs_s6)
tokens("MeOH literature: response-surface validation in Methods (S5 runs)", methods,
       f"{_rs_s6} and {_v['verdict_disagreements_total']} of {_v['verdicts_compared']:,} without the limit differ from "
       f"exact runs of complete replicates")
_pv = [v["top1_mismatch_groups"] for k, v in pb["variants"].items()
       if not k.startswith(("catalyst", "combined", "baseline"))]
tokens("MeOH plant benchmark: loop, recycle and price variants (S5 runs)", text,
       f"disagreement at {min(_pv)}–{max(_pv)} of {P0['groups']} comparisons")
ok("MeOH plant benchmark: baseline reproduces the S5 headline",
   pb["check"]["baseline_top1"] == f"{P0['top1_mismatch_groups']}/{P0['groups']}")

# main-text summaries written in the 2026-10-07 compression (the full statements live in the Supplementary Notes)
m_feru = main_section("Metal price and process optimization decide the Fe–Ru ranking")
_layer = {r["metal"]: r for r in rows(FEB + "inversion_layer_common_reference.csv")}
_repl = {k: float(_layer[k]["annualized_replacement_cost_USD_t_NH3"]) for k in ("Fe", "Ru", "Os")}
_ru_win = sum(r["economic_winner"] == "Ru" for r in draws)
tokens("Main text: layer-wise reversal, process optimization moves the gap into compression, descriptor winners", m_feru,
       f"annualized metal replacement of {_repl['Fe']:.3f} US dollars per tonne for Fe against {_repl['Ru']:.2f} for Ru",
       f"Setting the Ru price equal to the Fe value of {r8['price_USD_kg']:.0f} US dollars per kilogram and reoptimizing "
       f"makes Ru the cheaper catalyst ({r8['total_cost_USD_t']:.3f} against {fe['total_cost']:.3f} US dollars per tonne)",
       f"places Fe–Ru parity at {float(parity['price_USD_kg']):.2f} US dollars per kilogram",
       "Process optimization does not close the gap but moves it into compression",
       f"Ru moves to about {ru['T_C']:.0f} °C and {ru['P_bar']:.0f} bar, where a small bed holds little metal, while Fe "
       f"operates near {fe['T_C']:.0f} °C and {fe['P_bar']:.0f} bar",
       f"The {gap:.3f} US dollars per tonne at the two optima comes mainly from fresh-feed compression "
       f"(+{_pools['fresh_compression_electricity']:.3f}), metal inventory (+{_pools['metal_inventory']:.3f}) and "
       f"compressor capital (+{_pools['compressor_CAPEX']:.3f}), partly offset by vessel, recycle-compression and reactor terms",
       f"Fe ranks first economically in {100 * fe_win / len(draws):.1f}% and Ru in {100 * _ru_win / len(draws):.1f}%, in most "
       f"of the latter because the Fe bed exceeds the {_yaml_num(manifest, 'max_catalyst_bed_m3'):.0f} m³ limit")
tokens("SI Note 6: layer-wise check, replacement cost at the common reference against the total gap", s2_full,
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
_fci = FP["bootstrap_papers"]["mismatch_fraction_ci95"]
tokens("Main text: field-level ammonia result and extraction recall", m_field,
       f"in {FP['top1_mismatch_groups']} of them ({FP['top1_mismatch_fraction'] * 100:.0f}%",
       f"95% confidence interval {_fci[0] * 100:.0f}–{_fci[1] * 100:.0f}% from resampling papers), in "
       f"{FP['papers_with_mismatch']} of {FP['papers']} papers, with a median regret of "
       f"{FP['regret_median_mismatched'] * 100:.0f}% where the leaders differ",
       f"In {fk['different metal']['groups']} comparisons a catalyst of another metal is the plant-cost leader, in "
       f"{'all ' + str(_fe_dm) if _fe_dm == fk['different metal']['groups'] else _fe_dm} an Fe catalyst on the same support",
       f"in {fk['fused-Fe reference vs supported catalyst']['groups']} a commercial fused-iron catalyst",
       f"{tot['matched']} of the {tot['curated']} curated entries")
_ea = json.loads((ROOT / "analysis/verify_2026_10_08/errata_adjudication_summary.json").read_text(encoding="utf-8"))
_ec = _ea["confirmed"]
tokens("Methods: curated-data errors counted by root cause (errata adjudication)", text,
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
ok("Fe-Ru financing sources agree (PR #57 cash flow reproduced by PR #70; 32 lease contracts)",
   abs(fin["regressions"]["pr57_owned_12pct_Ru_USD_t"] - f12["Ru_USD_t"]) < 1e-9
   and abs(fin["regressions"]["pr57_owned_12pct_Fe_USD_t"] - f12["Fe_same_loop_USD_t"]) < 1e-9
   and abs(fin["regressions"]["owned_parity_rate"] - dcf["financing_hurdle_rate"]) < 1e-12
   and len(leases) == pbf["n"] and (_rates[0], _rates[-1]) == (pbf["pbf_min"], pbf["pbf_max"])
   and abs(_quantiles(_rates, [0.5])[0] - pbf["pbf_median"]) < 1e-9
   and (hl["pbf_min"]["rate_pct"], hl["pbf_max"]["rate_pct"]) == (pbf["pbf_min"], pbf["pbf_max"]))
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
m_feru2 = main_section("Metal price and process optimization decide the Fe–Ru ranking")
_conv = {
    "main": (m_feru2, [
        "they charge the Ru inventory, as the benchmark model does, only for the metal lost at each replacement",
        f"at the {pc(i_hi)}% rate applied to equipment brings Ru to parity with Fe in the KAAP-type loop "
        f"({f12['Ru_USD_t']:.2f} against {f12['Fe_same_loop_USD_t']:.2f} US dollars per tonne)",
        f"it costs {-rc0['Ru_minus_Fe_global']:.2f} US dollars per tonne less than Fe when the Ru inventory carries no "
        f"financing charge and {rc12['Ru_minus_Fe_global']:.2f} more at {pc(i_hi)}% per year (in the KAAP-type loop "
        f"{-rc0['Ru_minus_Fe_KAAP']:.2f} less and {rc12['Ru_minus_Fe_KAAP']:.2f} more)"]),
    "SI": (s2_full, [
        "These readings charge the Ru inventory, as the benchmark model does, only for the metal lost at each replacement",
        f"gives the same result when nothing is discounted ({f0['gap_Ru_minus_Fe_USD_t']:.2f} US dollars per tonne against "
        f"Fe in the KAAP-type loop at {pc(geo['w'])} wt% Ru, {geo['rho']:.0f} kg m⁻³ and {pc(geo['physical_r'], 2)}% recovery)",
        f"Financing the inventory at the {pc(i_hi)}% rate applied to equipment puts Ru at {f12['Ru_USD_t']:.2f} against "
        f"{f12['Fe_same_loop_USD_t']:.2f} for Fe in that loop",
        f"costs {-rc0['Ru_minus_Fe_global']:.2f} US dollars per tonne less than Fe without metal financing and "
        f"{rc12['Ru_minus_Fe_global']:.2f} more at {pc(i_hi)}% per year (KAAP-type loop: {-rc0['Ru_minus_Fe_KAAP']:.2f} less "
        f"and {rc12['Ru_minus_Fe_KAAP']:.2f} more)"]),
}
_miss = [f"{where}: {n}" for where, (hay, needles) in _conv.items() for n in needles if n not in hay]
# 1.2 direction: with descriptor kinetics, financing at the 12 % equipment rate brings Ru to parity in the KAAP-type loop
# (Ru still marginally below Fe, break-even rate equal to 12 % at the integer-percent precision of the text); with
# measured kinetics Ru/C is cheaper at 0 % and dearer at 12 %
_hurdle = dcf["financing_hurdle_rate"]
ok("Fe-Ru: both Ru-inventory financing conventions reported (no financing charge and 12 % per year), main text and SI",
   not _miss and rc0["Ru_minus_Fe_global"] < 0 < rc12["Ru_minus_Fe_global"]
   and rc0["Ru_minus_Fe_KAAP"] < 0 < rc12["Ru_minus_Fe_KAAP"]
   and f0["gap_Ru_minus_Fe_USD_t"] < f12["Ru_USD_t"] - f12["Fe_same_loop_USD_t"] < 0
   and abs(f12["gap_Ru_minus_Fe_USD_t"] - (f12["Ru_USD_t"] - f12["Fe_same_loop_USD_t"])) < 1e-12
   and _hurdle > i_hi and round(100 * _hurdle) == round(100 * i_hi),
   "missing: " + ", ".join(_miss) if _miss else f"break-even {100 * _hurdle:.2f} %/y")
tokens("Fe-Ru: Ru recovery stated as an optional scenario (main text, Methods, SI)", m_feru2 + methods + s2_full,
       "since the baseline ranking assumes no recovery",
       "Metal recovery is an optional scenario input, not a condition imposed on the baseline metal comparison",
       "Metal recovery is an optional Ru/C scenario")
_g_own = [hl[k]["owned_gap_USD_t"] for k in ("pbf_min", "pbf_max")]
_g_lease = [hl[k]["lease_gap_USD_t"] for k in ("pbf_min", "pbf_max")]
_ag_own, _ag_lease = sorted(abs(x) for x in _g_own), sorted(abs(x) for x in _g_lease)
ok("Fe-Ru KAAP financing: Ru below Fe (owned and leased) at both ends of the disclosed lease rates; the owned break-even "
   "is the dcf hurdle rate and lies above the lease rates",
   all(x < 0 for x in _g_own + _g_lease) and abs(fin["regressions"]["owned_parity_rate"] - _hurdle) < 1e-12
   and pbf["pbf_max"] / 100 < fin["regressions"]["lease_parity_rent"] < _hurdle
   and all(abs(hl[k]["owned_gap_USD_t"] - (hl[k]["owned_Ru_USD_t"] - hl[k]["owned_Fe_USD_t"])) < 1e-12
           for k in ("pbf_min", "pbf_max")))
tokens("Main text: KAAP financing parity and documented lease rates", m_feru2,
       f"Ru stays cheaper at any metal financing rate below {pc(_hurdle, 1)}% per year",
       f"at the {pbf['pbf_min']:.2f}–{pbf['pbf_max']:.2f}% per year that one refiner disclosed for {pbf['n']} platinum-group "
       f"catalyst-metal leases, Ru is {_ag_own[0]:.2f}–{_ag_own[1]:.2f} below Fe ({_ag_lease[0]:.2f}–"
       f"{_ag_lease[1]:.2f} if leased")
tokens("SI Note 6: financing parity, lease contracts and owned / leased gaps", s2_full,
       f"Ru stays cheaper at any metal financing rate below {pc(_hurdle, 2)}% per year "
       f"(a lease rent below {pc(fin['regressions']['lease_parity_rent'], 2)}% per year for a supplier-owned lease without "
       f"deposit)",
       f"{pbf['n']} fixed-rate platinum-group catalyst-metal leases of one US refiner ({min(_fy)}–{max(_fy)}, "
       f"{pbf['pbf_min']:.2f}–{pbf['pbf_max']:.2f}% per year, median {pbf['pbf_median']:.2f}%; "
       f"{sum(r['metal'] == 'not stated' for r in leases)} of the {pbf['n']} do not name the metal)",
       f"At these rates Ru is {_ag_own[0]:.2f}–{_ag_own[1]:.2f} US dollars per tonne below Fe when owned and "
       f"{_ag_lease[0]:.2f}–{_ag_lease[1]:.2f} when leased")
_LC = _load_module("lifecycle_cashflow", ROOT / "analysis/nh3_ru_net_recovery_boundary_2026_10_12/lifecycle_cashflow.py")
LIFE, PLANT_Y = _ynum("catalyst_life_y"), dcf["frozen_plant_years"]
_buy, _coll = _LC.lifecycle_dates(LIFE, PLANT_Y)
tokens("Methods: lifecycle cash-flow variant (dates and financing range)", methods,
       f"(purchases at {_and(f'{t:.0f}' for t in _buy)} years; recovered Ru credited at replacement and at closure)",
       f"discounted at a metal-specific rate of {pc(i_lo)}–{pc(i_hi)}% per year, and above {pc(i_hi)}% to locate the "
       f"break-even rate",
       f"over the {PLANT_Y:.0f}-year plant life")
ok("Methods: recovered Ru is credited at each replacement and at closure",
   _coll[:-1] == _buy[1:] and _coll[-1] == PLANT_Y and dcf["frozen_catalyst_life_y"] == LIFE)

# measured frontier kinetics
_mult_all = [v["Ru_activity_multiple_for_parity"] for v in ksw["variants"]]
fe_o, ru_o = val["apparent_orders_90bar"]["Fe_DysonSimon_400C"], val["apparent_orders_90bar"]["Ru_C_Rossetti_400C"]
_ruv = val["Ru_C_Rossetti2006_Table2"]["all_points_N2_basis"]
_rr = val["rate_ratio_90bar"]
fe_rng, ru_rng = _yrange("Fe_DysonSimon", "atm"), _yrange("Ru_C_Rossetti", "bar")
ru_trng = _yrange("Ru_C_Rossetti", "C")
kb100 = kh["Ru_benchmark_best_100_200_bar"]
_rr_lo, _rr_hi = _rr["400C_yNH3_0.02"]["Ru_over_Fe_per_kg"], _rr["400C_yNH3_0.14"]["Ru_over_Fe_per_kg"]
# Ru benchmark pressure profile of the headline variant (plug flow, measured rates, 1.2 states): the "broad optimum" is
# the largest excess over the optimum inside the pressure interval the SI names, printed as an upper bound
_prof = [r_ for r_ in rows(SC12 + "kinetics_swap_pressure_profiles.csv")
         if (r_["states"], r_["sizing"], r_["scale"]) == (_states12, kh["sizing"], kh["scale"])]
_prof_opt = min(float(r_["Ru_benchmark"]) for r_ in _prof)
_bo = re.search(r"broad optimum around (\d+) bar, within [\d.]+ of it from (\d+) to (\d+) bar", s2_full)
_bo_lo, _bo_hi = (float(_bo.group(2)), float(_bo.group(3))) if _bo else (0.0, 0.0)
_bo_dev = max((float(r_["Ru_benchmark"]) - _prof_opt for r_ in _prof if _bo_lo <= float(r_["P_bar"]) <= _bo_hi),
              default=float("inf"))
ok("NH3 measured kinetics: Ru's best 100-200 bar state lies in that range and costs more than its optimum; the optimum "
   "lies outside 100-200 bar inside the broad-optimum interval; Ru/C keeps a positive H2 order; Ru/C is held to the top of "
   "its measured temperature range",
   100 <= kb100["P_bar"] <= 200 and kb100["cost"] > kh["Ru_benchmark"]["cost"]
   and not 100 <= kh["Ru_benchmark"]["P_bar"] <= 200 and ru_o["H2"] > 0 and _ynum("T_max_Ru_C") == ru_trng[1]
   and _bo is not None and _bo_lo <= kh["Ru_benchmark"]["P_bar"] <= _bo_hi
   and abs(_prof_opt - kh["Ru_benchmark"]["cost"]) < 1e-5
   and abs(fsw["3_Ru_price_parity_benchmark"]["Ru_benchmark_best_100_200_bar_minus_optimum"]
           - (kb100["cost"] - kh["Ru_benchmark"]["cost"])) < 1e-4,
   f"max excess {_bo_dev:.3f} USD/t over {_bo_lo:.0f}-{_bo_hi:.0f} bar")
tokens("Abstract: measured rate laws lower the Ru activity requirement", main_section_h2("Abstract"),
       f"with descriptor kinetics it would need a {bw['Ru_activity_break_even_multiplier']:.0f}-fold activity gain",
       f"Measured rate laws for the two frontier catalysts lower that requirement to "
       f"{kh['Ru_activity_multiple_for_parity']:.0f}-fold")
tokens("Main text: measured Fe and Ru/C rate laws for the frontier pair", m_feru2,
       f"against {ru_o['H2']:+.1f} and {ru_o['NH3']:+.1f} for promoted Ru/C, whose hydrogen adsorption lowers but does "
       f"not reverse the hydrogen order",
       f"in NH₃ against {fe_o['NH3']:.1f} measured",
       f"Fe costs {kh['Fe']['cost']:.2f} US dollars per tonne at {kh['Fe']['T_C']:.0f} °C and {kh['Fe']['P_bar']:.0f} bar; "
       f"Ru costs {kh['Ru_benchmark']['cost']:.2f} at a broad optimum around {kh['Ru_benchmark']['P_bar']:.0f} bar, and "
       f"{kb100['cost']:.2f} at best in the 100–200 bar range, and would need a "
       f"{kh['Ru_activity_multiple_for_parity']:.0f}-fold activity gain for parity "
       f"({min(_mult_all):.0f}–{max(_mult_all):.0f}-fold across bed-sizing and calibration variants), against "
       f"{bw['Ru_activity_break_even_multiplier']:.0f}-fold with the descriptor kinetics",
       f"For supported Ru/C the measured kinetics move the decision to the financing of the Ru inventory. Its optimum is "
       f"at {rc0['Ru_C_global']['P_bar']:.0f} bar",
       f"Ru/C is held to {_ynum('T_max_Ru_C'):.0f} °C, the top of its measured range",
       f"the Ru/C rate advantage per kilogram grows from {_rr_lo:.0f}-fold at 2% to {_rr_hi:.0f}-fold at 14% NH₃")
ok("NH3 measured kinetics: the 1.2 port has the sizing x calibration variants only (no equilibrium variant)",
   {(v["sizing"], v["scale"]) for v in ksw["variants"]} == {("plug", "source"), ("plug", "FCAL"), ("inlet", "source"),
                                                            ("inlet", "FCAL")} and len(ksw["variants"]) == 4
   and min(_mult_all) == kh["Ru_activity_multiple_for_parity"])
tokens("SI Note 6: measured rate laws, validation and costs", s2_full,
       f"(apparent orders N₂ {fe_o['N2']:+.2f}, H₂ {fe_o['H2']:+.2f}, NH₃ {fe_o['NH3']:+.2f})",
       f"reproduces the {_ruv['n']} measured points of its source with a mean error of {pc(_ruv['mean_abs_rel_err'], 1)}%",
       f"the pair gives Fe {kh['Fe']['cost']:.2f} US dollars per tonne at {kh['Fe']['T_C']:.0f} °C, {kh['Fe']['P_bar']:.0f} "
       f"bar and a {kh['Fe']['Tsep_C']:.0f} °C separator and Ru in the benchmark formulation "
       f"{kh['Ru_benchmark']['cost']:.2f} at a broad optimum around {kh['Ru_benchmark']['P_bar']:.0f} bar, within "
       f"{ceil2(_bo_dev)} of it from {_bo_lo:.0f} to {_bo_hi:.0f} bar ({kb100['cost']:.2f} at best between 100 and 200 bar); "
       f"the activity multiple for parity is {kh['Ru_activity_multiple_for_parity']:.2f} "
       f"({min(_mult_all):.2f}–{max(_mult_all):.2f} across",
       f"against {bw['Ru_activity_break_even_multiplier']:.2f} with the descriptor kinetics",
       f"Supported Ru/C ({pc(_ynum('Ru_wt_frac_commercial'))} wt% Ru, {_ynum('Ru_C_bed_density_kg_m3'):.0f} kg m⁻³, "
       f"{pc(r_hi, 2)}% recovery) has its optimum at {rc0['Ru_C_global']['P_bar']:.0f} bar",
       f"from {_rr_lo:.0f}-fold at 2% to {_rr_hi:.0f}-fold at 14% NH₃ (90 bar, 400 °C)",
       f"the fused-iron law was fitted at {fe_rng[0]}–{fe_rng[1]} atm and the Ru/C law at {ru_rng[0]}–{ru_rng[1]} bar")
tokens("SI Note 6: apparent orders of the Ru/C rate law", s2_full,
       f"(N₂ {ru_o['N2']:+.2f}, H₂ {ru_o['H2']:+.2f}, NH₃ {ru_o['NH3']:+.2f})")
tokens("Methods: measured rate laws and the staged converter", methods,
       f"the Ru/C law reproduces the {_ruv['n']} measured points of its source with a mean error of "
       f"{pc(_ruv['mean_abs_rel_err'])}%.",
       f"The fused-iron law was fitted at {fe_rng[0]}–{fe_rng[1]} atm and the Ru/C law at {ru_rng[0]}–{ru_rng[1]} bar",
       f"each filled with fused iron (up to {_ynum('T_max_Fe_C'):.0f} °C) or Ru/C (up to {_ynum('T_max_Ru_C'):.0f} °C, the "
       f"top of its measured range), at {_ylist('loops_bar')[0] / 10:.0f} MPa with a {_ynum('separator_C'):.0f} °C separator "
       f"and {pc(_ynum('inerts_typical'))}% inerts",
       f"so the Fe optimum at {kh['Fe']['P_bar']:.0f} bar and the {_ylist('loops_bar')[0] / 10:.0f} MPa loop extrapolate the "
       f"former, and every Ru optimum above {ru_rng[1]} bar the latter")
ATM_BAR = 1.01325                                                  # bar per atm (definition)
ok("Methods: the Fe optimum and the 9 MPa loop lie below the fitted fused-iron pressure range",
   kh["Fe"]["P_bar"] < fe_rng[0] * ATM_BAR and _ylist("loops_bar")[0] < fe_rng[0] * ATM_BAR
   and kh["Ru_benchmark"]["P_bar"] > ru_rng[1] and kb100["P_bar"] > ru_rng[1])

# measured kinetics: break-even metal financing rate of supported Ru/C against Fe (frontier provenance, 1.2)
_be = fsw["1_breakeven_financing_rate"]
_be_g, _be_k = _be[f"r {r_hi} global"]["rate"], _be[f"r {r_hi} KAAP"]["rate"]
_be_g90, _be_k90 = _be[f"r {r_lo} global"]["rate"], _be[f"r {r_lo} KAAP"]["rate"]
tokens("Main text: measured-kinetics break-even financing rates", m_feru2,
       f"it stays cheaper than Fe up to a financing rate of {pc(_be_g, 1)}% per year, and in the KAAP-type loop up to "
       f"{pc(_be_k, 1)}% per year, above the disclosed lease rates")
tokens("SI Note 6: measured-kinetics break-even financing rates", s2_full,
       f"It stays cheaper than Fe up to a metal financing rate of {pc(_be_g, 2)}% per year, and in the KAAP-type loop up "
       f"to {pc(_be_k, 2)}% per year ({pc(_be_g90, 2)}% and {pc(_be_k90, 2)}% at {pc(r_lo)}% recovery)")
ok("Measured-kinetics break-even: Ru/C and Fe cost the same there, both rates exceed the disclosed lease rates, and the "
   "rates bracket the 0 %/y and 12 %/y signs",
   all(abs(_be[k]["Ru_C"]["cost"] - _be[k]["Fe"]["cost"]) < 1e-5 for k in _be)
   and min(_be_g, _be_k) > pbf["pbf_max"] / 100 and i_lo < _be_k < _be_g < i_hi
   and _be_g90 < _be_g and _be_k90 < _be_k
   and abs(fsw["reproduced_headline"]["RuC_minus_Fe"][f"cashflow {i_lo * 100:.0f}% r {r_hi}"]["global_"]
           - rc0["Ru_minus_Fe_global"]) < 1e-5
   and abs(fsw["reproduced_headline"]["RuC_minus_Fe"][f"cashflow {i_hi * 100:.0f}% r {r_hi}"]["KAAP"]
           - rc12["Ru_minus_Fe_KAAP"]) < 1e-5,
   f"{100 * _be_g:.2f} / {100 * _be_k:.2f} %/y")
# the 16 robustness cases (frontier_swap_robustness.csv); an infeasible Fe bed is -inf and counts as a Ru/C win
_rb = [{k: float(x) if x not in ("", None) and k != "case" else x for k, x in r_.items()} for r_ in fsw_rob]
_rbs = fsw["5_robustness"]["summary"]


def _rb_count(col, sign):
    return sum((r_[col] > 0) if sign > 0 else (r_[col] < 0) for r_ in _rb)


_be_rng = {lp: sorted(r_[f"breakeven_{lp}"] for r_ in _rb if r_[f"breakeven_{lp}"] != "") for lp in ("global", "KAAP")}
_fe12_exc = [r_["case"] for r_ in _rb if r_["gap_12_global"] < 0]
_fe_inf_k = [r_["case"] for r_ in _rb if r_["gap_12_KAAP"] == float("-inf")]
tokens("SI Note 6: measured-kinetics robustness cases", s2_full,
       f"Across {len(_rb)} cases that vary",
       f"Ru/C is cheaper than Fe without metal financing in all {len(_rb)} in both loops",
       f"the break-even financing rate spans {pc(_be_rng['global'][0], 2)}–{pc(_be_rng['global'][-1], 2)}% per year in the "
       f"main loop and {pc(_be_rng['KAAP'][0], 2)}–{pc(_be_rng['KAAP'][-1], 2)}% per year in the KAAP-type loop",
       f"At {pc(i_hi)}% per year Fe is cheaper in {_rb_count('gap_12_global', 1)} of the {len(_rb)} cases in the main loop",
       f"and in {_rb_count('gap_12_KAAP', 1)} of {len(_rb)} in the KAAP-type loop")
ok("Measured-kinetics robustness: counts recomputed from the 16 cases equal the summary; the main-loop exceptions at 12 %/y "
   "are a halved Fe effectiveness and a doubled converter premium; in the KAAP-type loop a halved Fe effectiveness leaves "
   "no Fe bed",
   len(_rb) == _rbs["global"]["n_cases"] == _rbs["KAAP"]["n_cases"]
   and _rb_count("gap_0_global", -1) == _rbs["global"]["RuC_ahead_at_0"] == len(_rb)
   and _rb_count("gap_0_KAAP", -1) == _rbs["KAAP"]["RuC_ahead_at_0"] == len(_rb)
   and _rb_count("gap_12_global", 1) == _rbs["global"]["Fe_ahead_at_12"]
   and _rb_count("gap_12_KAAP", 1) == _rbs["KAAP"]["Fe_ahead_at_12"]
   and sorted(_fe12_exc) == sorted(_rbs["global"]["exceptions_12"]) == ["Fe effectiveness 0.5", "converter premium x2"]
   and _fe_inf_k == _rbs["KAAP"]["Fe_infeasible"] == ["Fe effectiveness 0.5"]
   and next(r_ for r_ in _rb if r_["case"] == "base")["breakeven_global"] == round(_be_g, 6),
   "; ".join(_fe12_exc))
tokens("Discussion: financing threshold of supported Ru in the KAAP-type loop, measured and descriptor kinetics",
       main_section_h2("Discussion"),
       f"as long as its inventory is financed below {100 * _be_k:.0f}–{100 * _hurdle:.0f}% per year, depending on the kinetics",
       f"Ru would need a {bw['Ru_activity_break_even_multiplier']:.0f}-fold activity gain, far beyond the "
       f"{bw['Ru_scaling_max_gain_all_states']:.1f}-fold reachable along its scaling relation")

# apparent reaction orders of the descriptor kinetics (analysis/verify_2026_10_14_descriptor_orders, central differences)
_do = _j("analysis/verify_2026_10_14_descriptor_orders/descriptor_orders.json")
_do12, _doc = _do["1.2"], _do["condition"]
_dru, _dfe = _do12["orders"]["Ru"]["central"], _do12["orders"]["Fe"]["central"]
_dcond = f"{_doc['P_bar']:.0f} bar, {_doc['T_C']:.0f} °C and {pc(_doc['y_NH3'])}%"
tokens("Main text: apparent orders of the descriptor kinetics for Ru and fused iron", m_feru2,
       f"at {_dcond} ammonia they give apparent orders of {_dru['H2']:+.1f} in H₂ and {_dru['NH3']:+.1f} in NH₃",
       f"and fused iron {_dfe['NH3']:+.1f} in NH₃ against {fe_o['NH3']:.1f} measured")
tokens("SI Note 6: apparent orders of the descriptor kinetics", s2_full,
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
_th = {k: re.search(_thermo_re, hay) for k, hay in (("Methods", methods), ("SI Note 1", s1))}
ok("Thermodynamic basis: model-minus-Gillespie-Beattie NH3 formation free energy of the DFT gas energies lies inside the "
   "printed range (Methods and SI Note 1); NH3-FINAL-1.2 has no offset",
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
       f"The plant calibration of catalyst productivity is {_cal_txt}")
ok("Fused-iron calibration: the 1.2 recalibrated F_CAL is the run's F_CAL and reproduces the frozen Fe bed",
   abs(_cal["variants"]["v1_2"]["recalibrated"]["F_CAL"] - ksw["frozen_anchor_check"]["model"]["F_CAL"]) < 1e-5
   and abs(_cal["variants"]["v1_2"]["recalibrated"]["Fe_bed_at_calibration_state"]
           - _cal["variants"]["v1_1"]["fixed_FCAL"]["Fe_bed_at_calibration_state"]) < 1e-9
   and abs(_cal["variants"]["v1_2"]["recalibrated"]["metals"]["Fe"]["feasible"]["cost"]
           - m["Fe"]["feasible"]["total_cost"]) < 1e-12
   and _cal_txt in methods and _cal_txt in s1)

# industrial plant benchmark of NH3-FINAL-1.2 (SI Note 1; analysis/validation_nh3_plant_2026_10_13/nh3_1_2)
PBM = f"analysis/validation_nh3_plant_2026_10_13/{V12}/"
_pbs = _j(PBM + "summary.json")
_pbm = rows(PBM + "results_metrics.csv")
_pbA = [r_ for r_ in _pbm if r_["table"] == "A"]
tokens("SI Note 1: industrial plant benchmark", s1,
       f"The model passes {sum(r_['pass_'] == 'pass' for r_ in _pbm)} of {len(_pbm)} preregistered comparisons with "
       f"industrial ammonia plants, among them {sum(r_['pass_'] == 'pass' for r_ in _pbA)} of the {len(_pbA)} comparisons "
       f"with the loop states of {len({r_['case_id'] for r_ in _pbA})} industrial loop records")
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
_mcache = {}


def _mult(acc, rec, i):
    if acc == "frozen":
        return 1.0 - rec
    if (rec, i) not in _mcache:
        _mcache[(rec, i)] = _LC.annualized_metal_multiplier(
            _LC.MetalCashflow(project_y=PLANT_Y, catalyst_life_y=LIFE, discount_rate=i, gross_recovery=rec), 1.0,
            legacy_life_y=LIFE)
    return _mcache[(rec, i)]


def _decide(loop, p_ru, rec, i, acc="dcf"):
    m0 = _mult(acc, 0.0, i)
    c_ru, c_fe, c_sup = p_ru * _mult(acc, rec, i) / LIFE, P_FE * m0 / LIFE, P_SUP * m0 / LIFE
    res = {}
    for pat in PATS:
        best = None
        for nc, ru, fe, rcat, frac in _lib[(loop[0], loop[1], pat)]:
            c = nc + (c_ru * ru + c_fe * fe + c_sup * rcat) / ANNUAL
            if best is None or c < best[0]:
                best = (c, frac)
        res[pat] = best
    staged = min(("FFR", "FRR"), key=lambda q: res[q][0])
    best = min(PATS, key=lambda q: res[q][0])
    return {"best": best, "best_frac": res[best][1], "staged_minus_Fe": res[staged][0] - res["FFF"][0]}


def _cls(loop, p_ru, rec, i):
    b = _decide(loop, p_ru, rec, i)["best"]
    return "ru" if b == "RRR" else "fe" if b == "FFF" else "st"


def _window(loop, p_ru, rec, top=0.20, step=0.0005):
    """Financing-rate window in which a Fe-first staged design is the optimum: all-Ru/C below, all-Fe above."""
    xs = [k * step for k in range(int(round(top / step)) + 1)]
    cl = [_cls(loop, p_ru, rec, x) for x in xs]
    if not re.fullmatch(r"(ru,)*(st,)+(fe,)+", ",".join(cl) + ","):
        return None

    def edge(a, b, right):
        for _ in range(60):
            mid = (a + b) / 2
            a, b = (a, mid) if _cls(loop, p_ru, rec, mid) == right else (mid, b)
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
_save = [-_decide(KAAP, P_RU, r_hi, x / 100)["staged_minus_Fe"] for x in _lease3]
ok("Staged converter: the documented lease rates lie inside the Fe-first window, where staging saves cost",
   w95["lo"] < lease_lo and lease_hi < w95["hi"] and w95["all_ru_below"] and min(_save) > 0)
_order = [a.get("best", "") for a in ssum["arrangements"]] + [s.get("best", "") for s in ssum["sensitivities"]]
ok("Staged converter: a Ru/C-first converter is optimal in no case tested",
   _order and all(not re.search(r"R.*F", b) for b in _order) and not w150["all_ru_below"] and not w200["all_ru_below"])
_lease_rng = f"{pbf['pbf_min']:.2f}–{pbf['pbf_max']:.2f}% per year"
tokens("Abstract and Discussion: staged converter at financing rates that contain the disclosed lease rates", text,
       f"is the least-cost design at {pc(w95['lo'], 1)}–{pc(w95['hi'], 1)}% per year, a range that contains the disclosed "
       f"lease rates for platinum-group catalyst metal",
       "at metal-financing rates that contain the disclosed lease rates for platinum-group catalyst metal")
tokens("Main text: staged converter window and savings", m_feru2,
       f"three-bed converter at {KAAP[0] / 10:.0f} MPa",
       f"for Ru financing rates of {pc(w95['lo'], 1)}–{pc(w95['hi'], 1)}% per year",
       "all-Ru/C wins below that range, all-Fe above it, and a converter with Ru/C first is never optimal",
       f"The {_lease_rng} disclosed for platinum-group catalyst-metal leases falls inside this window, where staging saves "
       f"{min(_save):.2f}–{max(_save):.2f} US dollars per tonne over an all-Fe converter")
# Ru/C share of the least-cost converter across the window, as the committed boundary output gives it on its 0.5-point
# financing grid: at the first grid rate inside the window, and the share of the staged design that all-Fe replaces at
# the upper edge (the envelope ported above gives the same 0.0444 just below the edge). Exactly at the lower edge a 56 %
# design is optimal over 0.01 percentage points only (0.83-0.84 % per year), below the grid's resolution.
_bk = sorted((r for r in _bp if (float(r["P_bar"]), float(r["Tsep_C"])) == KAAP and r["accounting"] == "dcf"
              and float(r["recovery"]) == r_hi and float(r["p_Ru"]) == P_RU), key=lambda r: float(r["fin_rate"]))
_bk_in = [r for r in _bk if r["best"] in ("FFR", "FRR")]
_bk_fe = next(r for r in _bk if r["best"] == "FFF")
_sh_lo, _sh_hi = float(_bk_in[0]["best_Ru_volume_fraction"]), float(_bk_fe["staged_Ru_volume_fraction"])
_sh_seq = [float(r["best_Ru_volume_fraction"]) for r in _bk_in]
ok("Staged converter: the optimal Ru/C share falls across the window; grid and envelope agree at the upper edge",
   all(a >= b for a, b in zip(_sh_seq, _sh_seq[1:])) and w95["lo"] < float(_bk_in[0]["fin_rate"])
   and float(_bk_in[-1]["fin_rate"]) < w95["hi"] < float(_bk_fe["fin_rate"])
   and abs(_decide(KAAP, P_RU, r_hi, w95["hi"] - 1e-7)["best_frac"] - _sh_hi) < 1e-6)
tokens("SI Note 6: staged converter, Ru/C share across the window", s2_full,
       f"the Ru/C share of the catalyst volume falls from {pc(_sh_lo)}% to about {pc(_sh_hi)}% across the window",
       "a converter with Ru/C first is optimal in no case tested")
tokens("SI Note 6: staged-converter window edges (2 decimals)", s2_full,
       f"all-Ru/C for Ru financing rates of 0–{pc(w95['lo'], 2)}% per year",
       f"for {pc(w95['lo'], 2)}–{pc(w95['hi'], 2)}% per year", f"all-Fe above {pc(w95['hi'], 2)}% per year")
tokens("SI Note 6: staged window at 90 % recovery and at Ru price -30 % / +30 %", s2_full,
       f"The window moves with recovery ({pc(w90['lo'], 2)}–{pc(w90['hi'], 2)}% per year at {pc(r_lo)}%)",
       f"({pc(wm30['lo'], 2)}–{pc(wm30['hi'], 2)}% at -30%, {pc(wp30['lo'], 2)}–{pc(wp30['hi'], 2)}% at +30%)")
tokens("SI Note 6: staging savings at the documented lease rates", s2_full,
       f"staging saves {_and(f'{s:.2f}' for s in _save)} US dollars per tonne over an all-Fe converter at "
       f"{_and(f'{x:.2f}' for x in _lease3)}% per year")
tokens("SI Note 6: staged converter at 150 and 200 bar, all-Ru/C never wins", s2_full,
       f"in the {C150[0]:.0f} and {C200[0]:.0f} bar loops with a {C150[1]:.0f} °C separator the staged converter is optimal "
       f"up to {pc(w150['hi'], 2)}% and {pc(w200['hi'], 2)}% per year and all-Ru/C never wins")
ok("Staged converter: the 150 and 200 bar loops share one separator temperature", C150[1] == C200[1])
_mb = json.loads((ROOT / "analysis/verify_2026_10_12_metal_basis/metal_basis_summary.json").read_text(encoding="utf-8"))
_pb6 = _mb["S6"]["paper_basis"]
ok("MeOH per-gram-of-Re basis: per-gram-of-catalyst counts reproduce the S5 and S6 frozen kinds",
   _mb["S6"]["per_g_catalyst"]["other_catalyst"]["groups"] == oc6["groups"]
   and _mb["S6"]["per_g_catalyst"]["other_temperature"]["groups"] == oT6["groups"]
   and _mb["S5"]["per_g_catalyst"]["other_catalyst"]["groups"] == k5["other_catalyst"]["groups"]
   and _pb6["different_winner"] == n6 and _pb6["gt5pct"] == gt5_6)
_pb5 = _mb["S5"]["paper_basis"]
tokens("Methods: one paper ranked per gram of Re (counts with and without the inlet limit)", methods,
       f"become {_pb6['other_catalyst']['groups']} of {_pb6['other_catalyst']['of']} and "
       f"{_pb6['other_temperature']['groups']} of {_pb6['other_temperature']['of']} in the inert-limited loop "
       f"({_pb5['other_catalyst']['groups']} of {_pb5['other_catalyst']['of']} and {_pb5['other_temperature']['groups']} "
       f"of {_pb5['other_temperature']['of']} without the limit), while the totals are unchanged")
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
tokens("Main text: recycle-rise sensitivity costs", raw_text,
       *[f"{float(r['cost_USD_t']):.2f}" for r in _t1_92])
tokens("SI Note 6: recycle-rise sensitivity costs", s2_full,
       *[f"{float(r['cost_USD_t']):.3f}" for r in _t1_92 + _t1_60],
       f"{float(_t1[('Ru', 9.2)]['cost_USD_t']) - float(_t1[('Fe', 9.2)]['cost_USD_t']):.2f} US dollars per tonne above Fe")
_t3 = {(r["pair"], r["model_basis"], r["catalyst"]): float(r["total_USD_t"]) for r in rows(_LR + "t3_points.csv")}
_cl = _t3[("c93_closed_220bar", "closed B93", "Ru")] - _t3[("c93_closed_220bar", "closed B93", "Fe")]
_cn = _t3[("c93_closed_220bar", "canonical r0.9555_12pct_dp3", "Ru")] - _t3[("c93_closed_220bar", "canonical r0.9555_12pct_dp3", "Fe")]
tokens("Main text and SI Note 6: independent loop Ru/C minus Fe at 220 bar against the loop model", raw_text + s2_full,
       f"{_cl:.2f} US dollars per tonne above fused iron", f"against {_cn:.2f}",
       f"fused iron {_t3[('c93_closed_220bar', 'closed B93', 'Fe')]:.3f} and Ru/C {_t3[('c93_closed_220bar', 'closed B93', 'Ru')]:.3f}")
_up = _j(_LR + "upstream_93_94.json")
ok("NH3 loop check: the independent loop rerun reproduces PR #93 (Fe 47.245, Ru 49.484)",
   abs(_t3[("c93_closed_220bar", "closed B93", "Fe")] - 47.245) < 5e-4 and abs(_t3[("c93_closed_220bar", "closed B93", "Ru")] - 49.484) < 5e-4,
   str(list(_up)[:4]))

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
tokens("MeOH: recycled CO converted up to CO-hydrogenation equilibrium, main text and Methods (PR #84)", text,
       f"converted per pass up to CO-hydrogenation equilibrium, the upper end of its thermodynamic window "
       f"({_hi['disagreements']} of {_hi['groups']}, {_hi['gt5pct']} above 5%)",
       "recycled CO converted up to CO-hydrogenation equilibrium are reported as sensitivities")
tokens("SI Note 3: recycled CO converted up to CO-hydrogenation equilibrium (PR #84)", _si_flat,
       f"gives {_hn['disagreements']} of {_hn['groups']} without the limit ({_hn['gt5pct']} above 5%) and "
       f"{_hi['disagreements']} with it ({_hi['gt5pct']} above 5%, {_hi['papers_with_disagreement']} papers)",
       f"then falls to {pc(_hi['median_inlet_co_share_at_optimum'], 1)}%")
ok("PR #84 gate: the central rule reproduces the frozen columns and anchors",
   all(v["passed"] for v in _cob["gate"].values()) and all(_cob["frozen_anchors"].values()))

# ----- Report -----------------------------------------------------------------
failed = [(label, detail) for label, passed, detail, warn in checks if not passed and not warn]
warned = [(label, detail) for label, passed, detail, warn in checks if not passed and warn]
for label, passed, detail, warn in checks:
    print(("PASS " if passed else "WARN " if warn else "FAIL ") + label + (f" | {detail}" if detail else ""))
print(f"{len(checks)} checks, {len(failed)} failed, {len(warned)} warnings "
      "(WARN: a manuscript number that disagrees with its merged source; the text is not edited here)")
raise SystemExit(1 if failed else 0)
