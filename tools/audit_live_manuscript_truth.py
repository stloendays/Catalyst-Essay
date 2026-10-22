"""Audit the current live manuscript against committed scientific sources.

This checker is intentionally section-aware rather than phrase-fragile. It verifies that
current canonical/derived numbers appear in the Results section where they belong,
including the closed strict-scaling x lifecycle reachability result.

The frozen descriptor screen, strict-scaling/lifecycle closure, methanol loop and agent
checks retain their committed sources. The 2026-10-21 manuscript revision uses measured
Fe/Ru/C rate laws inside their fitted ranges, the median disclosed lease rate, the
conversion-raised catalyst-level methanol result, Au lifetime boundaries and external
CO2 methanation. Numerical checks cover the main text, Supplementary Notes, Supplementary Methods
and detailed numerical figure captions. Reference order uses the short reader-facing
captions. The compressed Nature Chemical Engineering layout has an unheaded
introduction and the former Table 1 in Supplementary Note 7. Format checks enforce
word limits, six main figures and three numbered display equations. Definitions
retained in the main-text Methods are checked there; secondary numbers are anchored
to their SI subsection, table or detailed caption. Standard library only (CI needs
no project requirements).

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


# Resolve citations by stable source identity, independent of editorial renumbering.
_reference_entries = [(int(n), entry) for n, entry in re.findall(
    r"^(\d+)\.\s+(.+)$", raw_text.split("## Working references", 1)[1], re.M)]


def reference_number(identity):
    """Require a unique DOI/title match; missing/duplicate entries fail callers, not crash."""
    matches = [n for n, entry in _reference_entries if identity.casefold() in entry.casefold()]
    return matches[0] if len(matches) == 1 else None


def rows(path):
    with open(ROOT / path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


SI_PATH = ROOT / "docs/SUPPLEMENTARY_INFORMATION.md"
raw_si = SI_PATH.read_text(encoding="utf-8") if SI_PATH.exists() else ""


def _table_section(key):
    """One reader-facing generated table, excluding neighbouring tables."""
    raw = (ROOT / "docs/SI_TABLES.md").read_text(encoding="utf-8")
    match = re.search(r"^### Supplementary Table " + re.escape(key) + r" \|[^\n]*\n(.*?)(?=^### |\Z)", raw, re.M | re.S)
    return re.sub(r"\s+", " ", match.group(0)).replace("−", "-") if match else ""



def _block(raw, i, marker):
    j = raw.find("\n### ", i + len(marker))
    d = raw.find("\n## ", i + len(marker))
    ends = [x for x in (j, d) if x >= 0]
    j = min(ends) if ends else len(raw)
    return re.sub(r"\s+", " ", raw[i:j]).replace("−", "-")


def _caption(path, heading):
    raw = (ROOT / path).read_text(encoding="utf-8")
    marker = "## " + heading + " |"
    return _block(raw, raw.index(marker), marker).replace("**", "")


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
    """A top-level section, with Abstract limited to its single paragraph."""
    if heading == "Abstract":
        return re.sub(r"\s+", " ", _abstract).replace("−", "-")
    i = raw_text.index("\n## " + heading + "\n") + 1
    j = raw_text.find("\n## ", i + 3)
    return re.sub(r"\s+", " ", raw_text[i:j if j >= 0 else len(raw_text)]).replace("−", "-")


# The former main-text Table 1 is the final table in Supplementary Note 7.
_feru_match = re.search(r"\*\*Ru against fused iron on each kinetic basis\.\*\*(.*?)(?=^### |\Z)", raw_si, re.M | re.S)
_feru_table = re.sub(r"\s+", " ", _feru_match.group(1)).replace("−", "-") if _feru_match else ""

# The first Results subsection is the screen/parity story; its headline is editorial.
# Keep its numerical assertions active even when the heading wording changes.
_nh3_result = re.search(r"^## Results[ \t]*\n+(### [^\n]+)", raw_text, re.M)
NH3_MAIN = _block(raw_text, _nh3_result.start(1), _nh3_result.group(1)) if _nh3_result else ""


# Only the first paragraph after Abstract is the abstract in the NCE layout.
_front = raw_text.split("## Abstract", 1)[1].split("## Results", 1)[0].strip()
_abstract, _, _introduction = _front.partition("\n\n")
_main_prose = _introduction + "\n" + raw_text.split("## Results", 1)[1].split("## Methods", 1)[0]

checks = []


def ok(label, condition, detail=""):
    """Every source disagreement fails the audit; the manuscript is never changed."""
    checks.append((label, bool(condition), detail))


def tokens(label, haystack, *needles):
    missing = [n for n in needles if n not in haystack]
    ok(label, not missing, "source-derived text missing: " + ", ".join(missing) if missing else "")


# (1.3 direct-path descriptor costs differ from the cached-surface anchors by < 5e-3 USD/t: direct vs interpolated kinetics.)
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
    f"raises the catalyst-dependent cost by {GAP_NH3:.3f} US dollars per tonne",
    f"amounts to {GAP_NH3 * ANNUAL_T / 1e6:.2f} million US dollars per year",
    f"For a "
    f"{_yaml_num(manifest, 'production_tpd'):,.0f} t/d plant, which at a capacity factor of "
    f"{_yaml_num(manifest, 'capacity_factor'):.2f} produces {ANNUAL_T:,.0f} t of NH₃ per year",
)
tokens("Main text: ammonia ranking reversal and regret",
    NH3_MAIN,
    f"over {det['process_state_count']:,} process states",
    f"at {m['Fe']['feasible']['total_cost']:.2f}, {m['Ru']['feasible']['total_cost']:.2f} and {m['Os']['feasible']['total_cost']:.2f} US dollars per tonne of NH₃",
    f"Spearman ρ = {det['raw_global_spearman']:.3f} across 15 metals",
    f"ρ = {head['top3_spearman']:.2f} among the three leaders",
    f"raise the catalyst-dependent cost by {100 * R_NH3:.1f}%",
    f"or {GAP_NH3:.2f} US dollars per tonne")
# The annual value remains source-checked in SI Note 1 above.

# ----- Results 2: price/process/uncertainty ----------------------------------
s2 = section("Metal price and process optimization jointly determine the Fe–Ru ranking")
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
    f"Fe has an interior optimum near {fe['T_C']:.0f} °C and {fe['P_bar']:.0f} bar, whereas Ru favours about "
    f"{ru['T_C']:.0f} °C and {ru['P_bar']:.0f} bar, both with a {fe['Tsep_C']:.0f} °C separator",
    f"set to the Fe value of {r8['price_USD_kg']:.0f} US dollars per kilogram",
    f"the Ru optimum shifts to {r8['T_C']:.0f} °C and "
    f"{r8['P_bar']:.0f} bar and its cost falls to {r8['total_cost_USD_t']:.3f} US dollars per tonne, "
    f"{-eq['Ru_minus_Fe_USD_t']:.3f} below Fe",
    f"places Fe–Ru parity at {float(parity['price_USD_kg']):.2f} US dollars per kilogram, where Ru operates at "
    f"{float(parity['T_C']):.0f} °C and {float(parity['P_bar']):.0f} bar with a {float(parity['V_m3']):.2f} m³ bed",
    f"the optimum moves from {float(_sw0['P_bar']):.0f} bar and an {float(_sw0['V_m3']):.1f} m³ bed at "
    f"{float(_sw0['price_USD_kg']):.0f} US dollar per kilogram to {float(_swN['P_bar']):.0f} bar and a "
    f"{float(_swN['V_m3']):.3f} m³ bed at {float(_swN['price_USD_kg']) / 10 ** _swN_e:g} × 10{str(_swN_e).translate(str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹"))} US dollars per kilogram",
)
ok("NH3 equal-price counterfactual: Ru below Fe after reoptimization (source sign); parity row closes the gap",
   eq["Ru_minus_Fe_USD_t"] < 0 and eq["economic_order_after_equalization"] == "Ru < Fe"
   and abs(r8["total_cost_USD_t"] - m["Fe"]["feasible"]["total_cost"] - eq["Ru_minus_Fe_USD_t"]) < 1e-12
   and abs(float(parity["cost"]) - m["Fe"]["feasible"]["total_cost"]) < 1e-9
   and float(price_sweep[0]["price_USD_kg"]) < r8["price_USD_kg"] < float(parity["price_USD_kg"])
   < eq["Ru_canonical"]["price_USD_kg"] < float(_swN["price_USD_kg"]))
_pools = {k: float(r_["Ru_minus_Fe_USD_t"]) for k, r_ in dec.items() if k != "TOTAL"}
_pos = sorted((k for k in _pools if _pools[k] > 0), key=lambda k: -_pools[k])
tokens("NH3 cost-gap decomposition", s2, f"{gap:.3f} in total, of which compression of fresh feed contributes +{_pools['fresh_compression_electricity']:.3f}, metal inventory +{_pools['metal_inventory']:.3f} and compressor capital +{_pools['compressor_CAPEX']:.3f}")
ok("NH3 cost-gap decomposition: the pools sum to the gap; compression, metal and compressor capital carry it in that "
   "order, vessel, recycle and reactor terms offset it, and neither optimum is refrigerated",
   abs(sum(_pools.values()) - gap) < 1e-9 and abs(gap - GAP_NH3) < 1e-12
   and _pos == ["fresh_compression_electricity", "metal_inventory", "compressor_CAPEX"]
   and all(_pools[k] < 0 for k in ("vessel_pressure_premium", "recycle_compression_electricity", "reactor_base"))
   and float(dec["refrigeration_electricity"]["Fe_canonical_USD_t"]) == 0.0
   and float(dec["refrigeration_electricity"]["Ru_canonical_USD_t"]) == 0.0,
   " > ".join(_pos))
claim_tokens("NH3 descriptor uncertainty semantics",
    ("SI Note 7", s2, [f"{100*mc['Fe_feasibility_probability']:.1f}%", f"{100*fe_win/len(draws):.1f}%", f"{100*mc['top3_actionable']:.1f}%", f"{100*mc['top1_survival']:.1f}%"]),
    ("Figure 4", _caption("docs/MAIN_FIGURE_CAPTIONS_DETAILED_2026-10-21.md", "Figure 4"),
     [f"The {len(draws):,} descriptor-uncertainty samples", f"Fe {fe_win}, Ru {len(draws) - fe_win}"]))

v = cmc["full_14136_state_direct_cost_verification"]
a = cmc["alpha_star"]
tokens(
    "NH3 cost-MC and parity-target distribution",
    s2,
    f"{cmc['draws']:,}",
    f"{v['P_C_Fe_lt_C_Ru']:.3f}",
    f"{v['minimum_Ru_minus_Fe_USD_t']:.3f}",
    f"{a['p05']:.2f}-, {a['p50']:.2f}- and {a['p95']:.2f}-fold",
    f"{a['p95']:.2f}-fold",
)
rq = regret_mc["regret_quantiles"]
tokens("NH3 cost-MC decision-regret distribution",
    s2,
    f"{100*rq['p05']:.2f}%",
    f"{100*rq['p50']:.2f}%",
    f"{100*rq['p95']:.2f}%")
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
tokens("NH3 lifecycle parity at the current Ru activity (SI Note 8)", s3,
    f"At the Ru price of {P_RU0:,.1f} US dollars per kilogram this requires about {100 * _r_at(L_REF):.2f}% recovery for a {L_REF:.0f}-year lifetime, {100 * _r_at(L_MAX):.2f}% for a {L_MAX:.0f}-year lifetime, or a {L99:.1f}-year lifetime at {pc(R_MAX)}% recovery")
ok("NH3 lifecycle parity keypoints: the committed 1.2 table equals p* / (P_Ru (1 - r)) on the 10-y basis; the parity "
   "lifetime at the recovery bound lies inside the prespecified lifetime range",
   abs(_lp[L_REF] - _r_at(L_REF)) < 1e-9 and abs(_lp[L_MAX] - _r_at(L_MAX)) < 1e-9
   and min(abs(k - L99) for k in _lp) < 1e-3 and L99 < L_MAX)
t10 = float(target(10, 0.99)["certified_upper_bound_required_direct_activity_multiplier"])
t15 = float(target(15, 0.99)["certified_upper_bound_required_direct_activity_multiplier"])
t20 = float(target(20, 0.99)["certified_upper_bound_required_direct_activity_multiplier"])
t20r98 = float(target(20, 0.98)["certified_upper_bound_required_direct_activity_multiplier"])
_n_sweep_states = len({(r_["T_C"], r_["P_bar"], r_["Tsep_C"]) for r_ in price_sweep})
claim_tokens("NH3 joint backward target region", ("SI Note 8", s3, [f"a 10-year life with 99% recovery needs at most a {t10:.3f}-fold activity increase, and 15- and 20-year lives need none"]), ("Supplementary Methods", supplementary_method('Ammonia synthesis'), [f"evaluated on the {_n_sweep_states} process states visited by the price sweep"]),
    ("Figure 6", _caption("docs/MAIN_FIGURE_CAPTIONS_DETAILED_2026-10-21.md", "Figure 6"),
     [f"{t10:.3f}×, {t15:.3f}× and {t20:.3f}×"]))
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
tokens("NH3 strict-scaling lifecycle closure", s3,
    f"the lowest Ru cost is {bw['Ru_best_scaling_cost_USD_t']:.3f}", f"{bw['Ru_best_scaling_EN_eV']:.3f}",
    rf"\(q^*={_q / 10 ** _qe:.4f}\times10^{{{_qe}}}\ \mathrm{{y}}^{{-1}}\)",
    f"At {_cor['life_y']:.0f} years and {100 * _cor['recovery_fraction']:.0f}% recovery the best state on the strict scaling relation", f"{_cor['best_E_N_eV']:.3f}",
    f"costs {_cor['best_strict_scaling_cost_USD_t']:.3f} US dollars per tonne, {abs(_cor['margin_vs_Fe_USD_t']):.3f} below Fe",
    f"at {float(_k15['life_y']):.0f} years {float(_k15['best_cost_USD_t']):.3f}, {abs(float(_k15['margin_vs_Fe_USD_t'])):.3f} below Fe",
    f"Parity requires {100 * _bx['required_recovery_at_20y']:.3f}% recovery at a 20-year lifetime or a {_bx['required_life_at_99pct_recovery_y']:.2f}-year lifetime at 99% recovery",
    "Lifecycle engineering thus reaches parity inside the present design space constrained by the scaling relation, where activity alone cannot")
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
    f"Ru matches Fe only after a {bw['Ru_activity_break_even_multiplier']:.0f}-fold increase in intrinsic activity ({a['p05']:.0f}–{a['p95']:.0f}-fold, 5th–95th percentile under economic uncertainty;",
    f"at most {bw['Ru_scaling_max_gain_673K']:.2f}-fold at 673 K and {bw['Ru_scaling_max_gain_all_states']:.2f}-fold across all process conditions",
    "the cheapest Ru on the strict scaling relation", f"{bw['Ru_best_scaling_EN_eV']:.3f}", f"still costs {bw['Ru_best_scaling_cost_USD_t']:.2f} US dollars per tonne",
    f"At 99% recovery, a 10-year catalyst life needs at most a {t10:.2f}-fold activity gain and a 20-year life none",
    f"\\(q^*={_q / 10 ** _qe:.2f}\\times10^{{{_qe}}}\\ \\mathrm{{y}}^{{-1}}\\)",
    f"at a {_cor['life_y']:.0f}-year life and {100 * _cor['recovery_fraction']:.0f}% recovery the best state costs {_cor['best_strict_scaling_cost_USD_t']:.2f} US dollars per tonne, {abs(_cor['margin_vs_Fe_USD_t']):.2f} below Fe")
# Full-state count and three-decimal recovery boundary remain checked in SI Note 8.

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
tokens("Au/TiO2 rank-preservation anchors",
    s5,
    "2 > 3 > 4 > 5 > 6 nm",
    "10,000",
    f"{100*float(p1['full_preservation_fraction']):.2f}%",
    f"{100*float(p2['full_preservation_fraction']):.2f}%")
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
    "realized pairwise transfer index",
    f"{_chi['NH3']:+.3f}",
    f"{_chi['MeOH']:+.3f}",
    f"is ≈ {_chi['AuTiO2']:.2f} for Au",
)
tokens(
    "Results: preserve source-normalized upstream advantages and downstream economic effects",
    m_transfer,
    f"{float(transfer['AuTiO2']['upstream_metric_ratio_sA_over_sB']):.1f} times the mass activity",
    f"{1 / float(transfer['AuTiO2']['downstream_objective_ratio_JA_over_JB']):.1f} times less catalyst",
    f"a {float(transfer['MeOH']['upstream_metric_ratio_sA_over_sB']):.1f}-fold STY advantage, "
    f"{(float(transfer['MeOH']['downstream_objective_ratio_JA_over_JB']) - 1) * 100:.1f}% higher cost",
    f"{float(transfer12['NH3']['upstream_metric_ratio_sA_over_sB']):.0f} times the TOF, {(float(transfer12['NH3']['downstream_objective_ratio_JA_over_JB']) - 1) * 100:.0f}% higher catalyst-dependent cost",
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
    "Common upstream H₂/N₂ supply contributions are held fixed",
)
tokens("NH3 draw-level cost-MC reconstruction lock", supplementary_method('Ammonia synthesis'), f"economic Monte Carlo ({cmc['draws']:,} samples)", "computes the regret draw by draw as", r"R=(C_{\mathrm{Ru}}-C_{\mathrm{Fe}})/C_{\mathrm{Fe}}")
ok(
    "no stale pending joint-reachability language",
    "Strict scaling-consistent joint reachability is not yet promoted" not in raw_text
    and "PENDING_EXACT_CACHE_SWEEP" not in raw_text,
)

# ----- 2026-10-05 additions: actual Ru catalyst cost, literature gains, methanol backward design --------------
lit = {r["id"]: r for r in rows(f"analysis/promoted_ru_literature_2026_10_05/{V12}/fig3_literature_points.csv")}
tokens(
    "NH3 literature activity gains (SI Note 8)",
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
tokens("NH3 literature gains against the 1.2 parity band (SI Note 8)", s3, f"All four lie within the {a['p05']:.2f}–{a['p95']:.0f}-fold parity band")
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
    f"ρ = -{abs(cf['CH4 selectivity removed']['rho']):.2f}",
    f"raises it to +{cf['conversion equalized']['rho']:.2f}",
    mbw["STY per g Re (multiplier)"]["note"].split("= ")[1].split(" ")[0],
    f"{float(mbw['single-pass CO2 conversion']['required']):.3f}",
)
ok("MeOH backward: STY alone cannot reach parity", mbw["STY per g Re (multiplier)"]["required"] == "unreachable")

# ----- Agent scaling: extraction accuracy, self-check, pruning ----------------------------------------------
s6 = section("An automated agent extends the analysis to catalysts from papers and databases")
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
tokens("Agent extraction accuracy",
    s6,
    f"{tot['matched']} of the {tot['curated']} curated entries ({float(tot['recall']) * 100:.0f}%)",
    n_ok("table", "X_CO2"),
    n_ok("table", "S_MeOH"),
    n_ok("SI", "X_CO2"),
    n_ok("SI", "S_MeOH"),
    n_ok("SI", "STY"),
    n_ok("plot", "X_CO2"),
    n_ok("plot", "S_MeOH"),
    f"{p18['precision_all_extracted'] * 100:.0f}% are correct in the first 18 papers",
    f"an estimated {p31['precision_all_extracted'] * 100:.0f}% in the 31 papers added later",
    f"{_ea_c['root_causes']} root causes, one mechanism in one source paper each, in {_ea_c['error_rules']} rules, "
    f"{_ea_c['value_cells_error_rules']} cells and {_ea_c['dropped_records']} rows")
ok("Agent: Gothe Table 4 extracted exactly", ext["gothe"]["matched"] == 21 and ext["gothe"]["X_CO2"] == "21/21")
canon = lit["selfcheck"]["canonical_states"]
tokens("Agent self-check",
    s6,
    "943.30, 961.51, 966.96 and 1,258.17")
ok("Agent self-check source", lit["selfcheck"]["max_abs_diff_eur_t"] < 1e-12
   and sorted(round(v, 2) for v in canon.values()) == [943.3, 961.51, 966.96, 1258.17])
ok("Agent: pure-metal self-check source", all(r["match"] for r in alloy["self_check"]))
gate = json.loads((ROOT / "agent/selfcheck_report.json").read_text(encoding="utf-8"))
au_gate = next(x for x in gate["systems"] if x["system"] == "Au/TiO2")
ok("Agent self-check gate passes for all three systems", gate["pass"] and all(x["pass"] for x in gate["systems"]))
ok("Agent Au/TiO2 extracted inputs reproduce the control", au_gate["extracted"]["pass"]
   and au_gate["extracted"]["envelope"]["full_preservation"] == 1.0 and au_gate["extracted"]["semiopen_windows_compared"] == 6)
tokens("Agent three-system self-check", supplementary_method('Adaptive Catalyst Screening Agent'), "the hand-built inputs of all three systems", "the extracted Re/TiO₂ and Au/TiO₂ inputs", "requires the results of the hand-built cases to be reproduced")
tokens(
    "Agent pruning",
    s6,
    f"{ext_all['costed']:,} priced bimetallic surfaces",
    f"excludes {ext_all['pruning']['pruned']:,} ({ext_all['pruning']['fraction_saved'] * 100:.1f}%)",
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
    f"{word(len(anch_below), cap=True)} do so under the bridge anchored to each element",
    f"ranks {ordinal(rg['upstream_winner_economic_rank'])} economically",
    f"({chem(rg['upstream_winner'])}, {rg['regret'] * 100:.1f}% regret)",
    f"{ordinal(ra['upstream_winner_economic_rank'])} ({chem(ra['upstream_winner'])}, {ra['regret'] * 100:.1f}%)",
    f"{rg['spearman']:.2f} and {ra['spearman']:.2f}",
    f"{_and(chem(x) for x in both_below)} remain below Fe under both",
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
tokens("NH3 alloy counterfactual and backward design",
    s7,
    f"({float(lead_g['cost_at_Fe_price_USD_t']):.2f} and {float(lead_a['cost_at_Fe_price_USD_t']):.2f} US dollars per tonne)",
    f"they need {fold(float(lead_g['alpha_star']))}-fold and {fold(float(lead_a['alpha_star']))}-fold activity increases",
    f"below {float(lead_g['best_scaling_cost_USD_t']):.2f} and {float(lead_a['best_scaling_cost_USD_t']):.2f} US dollars per tonne")
ok("NH3 alloy: leaders undercut Fe only at the Fe price",
   float(lead_g["cost_at_Fe_price_USD_t"]) < FE_COST_ALLOY < float(lead_g["cost_USD_t"])
   and float(lead_a["cost_at_Fe_price_USD_t"]) < FE_COST_ALLOY < float(lead_a["cost_USD_t"])
   and float(lead_g["best_scaling_cost_USD_t"]) > FE_COST_ALLOY and float(lead_a["best_scaling_cost_USD_t"]) > FE_COST_ALLOY
   and float(cu3cr["alpha_star"]) < 1)
ok("NH3 alloy: the surfaces below Fe in both bridges beat Fe in the backward table under both routes",
   all(abw[(s_, r_)]["beats_Fe"] == "True" for s_ in both_below for r_ in ("global", "anchored")))
claim_tokens("Main text: alloy screen, its activity leader and the lower bound",
    ("main text", m_alloy, [f"Of the {alloy['surfaces_fetched']:,} bimetallic and pure metal surfaces",
    f"{tm['costed']} contain only transition metals outside groups 3–5",
    f"{word(len(glob_below))} of them undercut Fe when the database is bridged linearly onto the model's descriptor, {word(len(anch_below))} under a bridge anchored to each element",
    f"The most active surface, {chem(rg['upstream_winner'])}, ranks only {ordinal(rg['upstream_winner_economic_rank'])} on cost ({rg['regret'] * 100:.1f}% regret)"]),
    ("SI Note 6", s7, [f"{tm['feasible']} satisfy the 90 m³ limit on bed volume"]),
    ("SI Notes", section("An automated agent extends the analysis to catalysts from papers and databases"),
    [f"excludes {ext_all['pruning']['pruned']:,} ({ext_all['pruning']['fraction_saved'] * 100:.1f}%)"]))

s2_full = section("Metal price and process optimization jointly determine the Fe–Ru ranking")

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
tokens("NH3 measured catalysts",
    s9,
    f"the {adj['rows']} catalyst rows",
    f"within a factor of {math.ceil(_fa_factor * 10) / 10:.1f}",
    f"Of the {sup['primary']} catalysts in the primary set ({pm['Ru']['n']} Ru, {pm['Fe']['n']} Fe, {pm['Co']['n']} Co and {pm['Ni']['n']} Ni)",
    f"the one with the highest laboratory rate, {ov['rate_leader']}, "
    f"costs {ov['rate_leader_cost']:.2f} US dollars per tonne, {ov['regret'] * 100:.0f}% above",
    f"(Spearman ρ = {ov['spearman_rate_vs_cost']:.2f})",
    f"({float(sgm['81']['regret']) * 100:.1f}% and {float(sgm['82']['regret']) * 100:.1f}% regret)",
    f"{word(len(_below), cap=True)} measured catalysts undercut the fused-iron benchmark without metal recovery",
    f"({chem(_below[0][1]['best'])}, {_below[0][1]['cost_min']:.2f} US dollars per tonne)",
    f"({chem(_below[1][1]['best'])}, {_below[1][1]['cost_min']:.2f})",
    f"with 90% Ru recovery {word(len(sup['sensitivity']['Ru_recovery90']['below_Fe']))} Ru catalysts do")
ok("NH3 measured: without recovery exactly one Ru and one Fe catalyst undercut the Fe benchmark (after the primary-paper "
   "errata); the plant-cost leader is the cheapest of them",
   [k for k, _ in _below] == ["Ru", "Fe"] and all(x["below_Fe"] == 1 for _, x in _below)
   and sum(x["below_Fe"] for x in pm.values()) == 2 and all(x["cost_min"] < FE_SUP for _, x in _below)
   and ov["plant_leader"] == _below[0][1]["best"] and abs(ov["plant_leader_cost"] - _below[0][1]["cost_min"]) < 1e-12
   and abs(FE_SUP - m["Fe"]["feasible"]["total_cost"]) < 1e-12)
tokens(
    "Main text: measured catalysts of the review (rate and cost uncorrelated)",
    main_section("Laboratory leaders are often not the plant-cost leaders"),
    f"Across the {sup['primary']} catalysts of a review",
    f"laboratory rate and plant cost are uncorrelated (Spearman ρ = {ov['spearman_rate_vs_cost']:.2f}",
    # The two below-Fe catalysts and their costs remain checked in SI Note 4; the percentage margins were removed.
)
errata = rows("agent/nh3_supported/out/primary_errata.csv")
claim_tokens("NH3 measured: errata and Methods row count", ("SI Note 4", s9, ["ten transcription errors in nine rows"]), ("Supplementary Methods", supplementary_method('Measured ammonia catalysts'), [f"({sup['primary'] + sup['flagged']} of {sup['rows']} rows)"]))
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
    f"the rate is correct in {fev['matched'] - rate_ev['extraction_errors']} of {fev['matched']}",
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
claim_tokens("SI Note 4: both batches",
    ("Supplementary Methods", supplementary_method('Measured ammonia catalysts'), [f"a further {fx['screening_with_si']['included']} of {fx['screening']['screened']} papers screened under a protocol fixed before extraction (Supplementary Table 2b)"]),
    ("SI Note 4", s9, [f"form {PL['groups']} comparisons in {PL['papers']} papers", f"not the plant-cost leader in {PL['mismatch']} of them ({pc(PL['fraction'])}%; 95% confidence interval {pc(PL['ci95'][0])}–{pc(PL['ci95'][1])}%)",
    f"in {PL['papers_with_mismatch']} of {PL['papers']} papers", f"{PL['regret_gt5pct']['groups']} of the {PL['mismatch']} have a regret above 5%",
    f"Ranking by rate per gram of metal gives {PLV['per_g_metal_leaderboard']['mismatch']} of {PLV['per_g_metal_leaderboard']['groups']}",
    f"90% Ru recovery {PLV['Ru_recovery_90pct']['mismatch']} of {PLV['Ru_recovery_90pct']['groups']}",
    f"In {len(_p_below)} of the {PL['groups']} comparisons the plant-cost leader undercuts the fused-iron benchmark",
    f"({min(float(r['plant_winner_cost']) for r in _p_fused):.2f}–{max(float(r['plant_winner_cost']) for r in _p_fused):.2f} US dollars per tonne)",
    f"a {_p_other_c[0]['metal_wt_pct']} wt% {_p_other[0]['plant_winner'].split('-')[0]} catalyst at {_p_other_c[0]['T_C']} °C and {_fmt_p(_p_other_c[0]['P_MPa'])} MPa ({float(_p_other[0]['plant_winner_cost']):.2f})"]))
# the main text reports the pooled 44 comparisons (kinds from the pooled run's printed summary)
_pls = _j(FX + "runs/pooled_vf_screen/summary_printed.json")["primary"]
_plk = _pls["mismatch_kinds"]
_pl_fe = _pls["different_metal_split"]["Fe plant winner, same support family"]["groups"]
ok("NH3 pooled: the run summary equals the report numbers",
   (_pls["groups"], _pls["papers"], _pls["top1_mismatch_groups"]) == (PL["groups"], PL["papers"], PL["mismatch"])
   and {k: v["groups"] for k, v in _plk.items()} == PL["kinds"]
   and abs(_pls["regret_median_mismatched"] - PL["regret_median_mismatched"]) < 1e-12)
claim_tokens("Main text: pooled ammonia result (both batches)",
    ("main text", main_section("Laboratory leaders are often not the plant-cost leaders"),
    [f"In {PL['mismatch']} of {PL['groups']} comparisons ({pc(PL['fraction'])}%; 95% confidence interval {pc(PL['ci95'][0])}–{pc(PL['ci95'][1])}%)",
    f"{PL['regret_gt5pct']['groups']} of them by more than 5% (Fig. 2c)",
    f"{word(_pl_fe, cap=True)} times the winner is an Fe catalyst on the same support as the faster Ru",
    f"{word(_plk['fused-Fe reference vs supported catalyst']['groups'])} times the commercial fused-iron reference that the authors' new catalyst outperformed in the laboratory"]),
    ("SI Notes", s9, [f"{PL['groups']} comparisons in {PL['papers']} papers",
    "Ranking by rate per gram of metal gives " + f"{PLV['per_g_metal_leaderboard']['mismatch']} of {PLV['per_g_metal_leaderboard']['groups']}"]))
tokens("Methods: second batch of ammonia papers", supplementary_method('Measured ammonia catalysts'), f"a further {fx['screening_with_si']['included']} of {fx['screening']['screened']} papers screened under a protocol fixed before extraction (Supplementary Table 2b)", f"({NPL['entries']} entries in {NPL['groups']} groups)")
tokens("SI Note 4: pooled ammonia kinds", s9,
    f"{PL['regret_gt5pct']['groups']} of the {PL['mismatch']} have a regret above 5% (median {pc(PL['regret_median_mismatched'])}%)",
    f"commercial fused-iron reference in {_plk['fused-Fe reference vs supported catalyst']['groups']} of the {PL['mismatch']}",
    f"a catalyst of another metal in {_plk['different metal']['groups']} (an Fe catalyst on the same support in all {_pl_fe})",
    f"the same metal on another support or with another promoter in {_plk['same metal and metal content']['groups']}",
    f"the same metal at another content in {_plk['same metal, different metal content']['groups']}")
_sit = (ROOT / "docs/SI_TABLES.md").read_text(encoding="utf-8")
SI_SOURCES = (ROOT / "docs/SI_TABLES_SOURCES.md").read_text(encoding="utf-8")
ok("SI Table 2b: the later ammonia papers with their groups and different winners",
   bool(re.search(rf"^### Supplementary Table 2b \| The {fx['screening_with_si']['included']} later ammonia-synthesis "
                  rf"papers", SI_SOURCES, re.M))
   and "analysis/nh3_field_expansion_2026_10_12/PROTOCOL.md" in SI_SOURCES
   and f"| **Total** |  |  | **{fx['screening_with_si']['included']} papers** |" in _sit
   and f"**{B2['groups']}** | **{B2['mismatch']}** |" in _sit)

# ----- MeOH published leaderboards: inert-limited loop S6 primary, S5 alongside ------------------------------------
# Supervisor decision of 2026-10-12 (docs/SUPERVISOR_FEEDBACK_2026-10-12.md): the primary methanol loop limits the
# reactor-inlet CH4 + CO + N2 to 6.86 % (S6, frozen column cost_recycled_opt_inlet); the loop without the limit (S5,
# frozen column cost_recycled_opt) is reported alongside. Every number is read from the merged analyses:
#   analysis/meoh_literature_inversion_2026_10_05 (frozen columns), meoh_constraint_boundary_2026_10_12 (#69),
#   meoh_inlet_definition_2026_10_12 (#73), verify_2026_10_12_s6_conversion (#67), meoh_s6_robustness_2026_10_13 (#79).
s8 = section("Paper leaderboards and plant-cost leaderboards often disagree in methanol")   # Supplementary Note 3
m_field = main_section("Laboratory leaders are often not the plant-cost leaders")
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
       f"{pl6['groups']} comparisons within papers, {pl6['entries']} entries",
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
                r"analysis[ \t]*$", SI_SOURCES, re.M)
LEDGER_TABLE = int(_lt.group(1)) if _lt else -1
_lrows, _lhead, _ltot = [], [], []
if _lt:
    _table = re.search(rf"^### Supplementary Table {LEDGER_TABLE} \|.*$", SIT, re.M)
    _start = _table.end() if _table else len(SIT)
    _j_ = SIT.find("\n### ", _start)
    _cells = [[c.strip() for c in ln.strip().strip("|").split("|")]
              for ln in SIT[_start:_j_ if _j_ >= 0 else len(SIT)].splitlines() if ln.startswith("| ")]
    _lhead, _body_rows = (_cells[0], _cells[1:]) if _cells else ([], [])
    _ltot = [r for r in _body_rows if r[0] == "**Total**"]
    _lrows = [r for r in _body_rows if r[0] != "**Total**"]
_lstat = [r[_lhead.index("Status")] for r in _lrows] if "Status" in _lhead else []
_ledger_csv = rows(LEDC + "group_ledger.csv")
ok(f"SI Table {LEDGER_TABLE}: the combined 161 -> 81 ledger lists every group once (161 rows, 81 kept) with the ledger's "
   f"drop reasons",
   _lt is not None and (LEDC + "group_ledger.csv") in SI_SOURCES
   and (int(_lt.group(2)), int(_lt.group(3))) == (aec["groups"], ppc["groups"])
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
tokens("Methods: combined comparison grouping rule", supplementary_method('Methanol comparisons within papers'), "Comparison groups contain the entries of one paper at the same pressure, H₂/CO₂ ratio and space velocity (Supplementary Table 7)")
tokens("SI Note 3: 161 -> 81 comparison groups", s8, f"{pl6['groups']} comparisons with {pl6['entries']} entries in {pl6['papers']} papers ({len(_ledger_csv)} groups with values read from plots, Supplementary Table 7)")

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
    ("main text", m_field, [f"spares {_pr8['excluded_fraction'] * 100:.1f}% of the full methanol optimizations without missing a plant-cost leader"]),
    ("SI Notes", section("An automated agent extends the analysis to catalysts from papers and databases"),
    [f"spares the full optimization for {_frac(_pr8['spared'])[0]} of the {_frac(_pr8['spared'])[1]} candidates ({_pr8['excluded_fraction'] * 100:.1f}%)",
    f"at {_pr8['compute_share'] * 100:.0f}% of the compute"]))
# main text: field result
claim_tokens("Main text: methanol field result, inlet-limited loop (S6) primary and S5 alongside",
    ("main text", m_field, [f"at most {pc(LIM, 2)}% CO, methane and N₂, the limit of the loop that anchors the cost model",
    f"differ in {pl6['disagreements']} of {pl6['groups']} comparisons",
    f"Without the limit the leaders differ in only {pl5['disagreements']} of {pl5['groups']} comparisons",
    f"limiting methane and N₂ alone gives {_frac(_rin['co_excluded_6_86']['disagreements'])[0]}.", "It is CO build-up"]),
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
tokens("Main text: 5-10 % stability of the inlet limit (combined set)", m_field, "inlet limits of 5–10%")
_sweep_limits = sorted((k for k in _sw if k != "none"), key=float)
tokens("SI Note 3: inlet-limit sweep endpoints", s8, f"inlet limit is raised from {min(map(float, _sweep_limits)):g}% to {max(map(float, _sweep_limits)):g}%", f"falls from {_frac(_sw[_sweep_limits[0]]['disagreements'])[0]} to {_frac(_sw[_sweep_limits[-1]]['disagreements'])[0]} of {pl6['groups']}, against {pl5['disagreements']} without a limit")

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
       f"Ranking by conversion disagrees in {_qX6['disagreements']} of {_qX6['groups']} comparisons and by methanol "
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
    ("main text", m_field, [f"{_frac(_rn['kept_ge90pct']['k1'])[0]} of the {_frac(_rn['kept_ge90pct']['k1'])[1]} persist in at least 90% of {st6['noise_model']['draws']:,} re-measurements",
    "every product closure, catalyst price and plant-term variant tested"]),
    ("SI Notes", s8, [f"{PL6['without_bansode']['disagreements']} of {PL6['without_bansode']['groups']}",
    f"the count stays between {int(RB['9_plant_variants']['combined']['S6'].split()[0].split('-')[0])} and {PL6['inert_co']['disagreements']} of {pl6['groups']}"]))
tokens("SI Note 3: Measurement noise alone changes the laboratory leader", s8,
       f"measurement noise alone changes a paper's STY leader in "
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
    f"against {min(_pub_co):.1f}–{max(_pub_co):.1f}% in industrial loop designs",
    f"The plant-cost leader is the more selective catalyst in {PL6['mechanism']['plant_leader_more_selective']['count']} of the {PL6['mechanism']['disagreements']} disagreements"]),
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
            f"On m-ZrO₂, InNi₃C₀.₅ gives the highest STY ({pc(float(a['SCO']))}% CO) but needs a "
            f"{pc(float(a['purge_recycled_opt_inlet']), 1)}% purge and costs {float(a['cost_recycled_opt_inlet']):,.0f} euros per tonne",
            f"on SiO₂ ({pc(float(b['SCO']))}% CO) it runs at {pc(float(b['purge_recycled_opt_inlet']), 1)}% purge for "
            f"{float(b['cost_recycled_opt_inlet']):,.0f}"]))
_hit = [e for e in _ex if all(n in m_field for n in e[1])]
ok("Main text: InNi3C0.5 example (inlet-limited costs and purge) matches one frozen group",
   len(_hit) == 1, "" if _hit else "expected one frozen group: " + " || ".join("; ".join(e[1]) for e in _ex))

# Conversion and methanol selectivity have no reader-facing numeric anchor.
# Retain source-to-source checks for the group matching the printed CO/purge/cost.
_inni_records = rows("agent/extraction/out/records_normalized.csv")
_inni_source_matches = []
for _group, _needles in _hit:
    _g = next(g for g in _gm6 if g["group"] == _group)
    for _winner in ("upstream_winner", "economic_winner"):
        _c = next(c for c in _cand if c["group"] == _group and c["catalyst"] == _g[_winner])
        _records = [r for r in _inni_records if r['doi'] == _c['doi'] and r['entry_label'] == _c['entry']]
        _inni_source_matches.append(len(_records) == 1 and all(
            abs(float(_c[k]) * 100 - float(_records[0][v])) < 1e-9
            for k, v in (("X", "X_CO2_pct"), ("SMeOH", "S_MeOH_pct"))))
ok("MeOH source-only: retired InNi3C0.5 conversion and methanol selectivity equal extraction ledger",
   len(_hit) == 1 and len(_inni_source_matches) == 2 and all(_inni_source_matches))

_bd = bnd["bansode_doi"]
_bgm5 = [r for r in _gm5.values() if r["doi"] == _bd]
_maxdoi = [max(rows(f"analysis/meoh_literature_inversion_2026_10_05/{f}"), key=lambda r: float(r["regret"]))["doi"]
           for f in ("group_metrics.csv", "group_metrics_inlet_limit.csv")]
ok("MeOH: the high-pressure Cu/Al2O3 study supplies the largest regret in both loops",
   _maxdoi == [_bd, _bd] and len(_bgm5) == bnd["bansode_groups"] and "c2cy20604h" in V["without_paper_with_most_groups"]["variant"])
# Its removed eight-comparison count remains cross-source checked on both sides
# of this prose assertion (the group table, boundary summary and pooled summary).
tokens("Main text: the high-pressure Cu/Al2O3 study (combined set)", m_field,
       f"a high-pressure Cu/Al₂O₃ study[{reference_number(_bd)}] gives the largest regrets without the limit")
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
tokens("SI Note 3: species counted and the published loop inlets", s8, f"CO, methane and N₂ at the reactor inlet to {pc(LIM, 2)}%", f"loop designs carry {_cmn_rng} CO, methane and N₂ at the reactor inlet", f"CO at the reactor inlet is a median {pc(_rin['inlet_co_without_limit']['median'], 1)}% (10th and 90th percentiles {pc(_rin['inlet_co_without_limit']['p10'], 1)}% and {pc(_rin['inlet_co_without_limit']['p90'])}%), against {min(_pub_co):.1f}–{max(_pub_co):.1f}% in the industrial designs")
ok("MeOH S6: CO is more than 80 % of the limited inlet quantity at the limited optimum",
   _scan("frozen", "6.86")["co_fraction_of_nonreactive_median"] > 0.8)
r1_6 = {r["threshold"]: r for r in st6["regret_threshold_curve"]}
r1_5 = {r["threshold"]: r for r in st5["regret_threshold_curve"]}
tokens("SI Note 3: operating points of the extraction set", s8, f"{lit['candidates']} operating points", f"from {lit['papers_with_candidates']} papers")
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
tokens("Methods: inlet limit and near-infeasibility rule", supplementary_method('Methanol comparisons within papers'), f"stays at or below {pc(LIM, 2)}%, the limit of the loop that anchors the cost model", "exceeds twice its cost without the limit or the regret exceeds 100%")
ok("Methods: near-infeasibility rule is the merged rule (regret > 1 or > 2x the S5 cost)",
   "regret > 1" in bnd["near_infeasible_rule"] and "2x" in bnd["near_infeasible_rule"]
   and abs(bnd["published_range"][0] - min(float(r["non_h2co2_pct"]) for r in _pub) / 100) < 1e-4
   and abs(bnd["published_range"][1] - max(float(r["non_h2co2_pct"]) for r in _pub) / 100) < 1e-4)

# Abstract and Discussion: catalyst-level shares in the compressed NCE narrative.
# The priced alloy count is retained in SI Note 2.
tokens("Abstract headline numbers", main_section_h2("Abstract"),
       f"nor is the fastest catalyst in {NPL['mismatch']} of {NPL['groups']} ammonia comparisons")
claim_tokens("Results and SI Note 2: alloy count and field counts",
    ("SI Note 2", s6, [f"{ext_all['costed']:,} priced bimetallic surfaces"]),
    ("main text", m_field, [f"ACSA extracted {fd['papers_in_set'] + fx['screening_with_si']['included']} primary ammonia synthesis papers (Supplementary Tables 2 and 2b)"]))
tokens("Discussion: field-level shares", main_section_h2("Discussion"),
    "In a third of the methanol comparisons and more than a quarter of the ammonia comparisons",
    "the catalyst that a paper's own data rank first is not the one a plant would build",
    "A plant would also usually run a catalyst cooler than at its best laboratory temperature")
_bl = _j("analysis/validation_meoh_prospective_2026_10_13/results.json")["primary (printed, corrected)"]["S6"]
_bls = _bl["stats"]
ok("MeOH blind rule: the committed predictions equal the rule on every comparison of the second set",
   _bl["rule"] == "S" and _bl["blind_predictions_equal_rule"] == _bls["rule_accuracy"]["denominator"] == 41)
# 2026-10-19: the blind selectivity-rule prediction is no longer reported in the main text
_cap = _j("analysis/meoh_field_pooled_2026_10_15/cap_robustness/summary.json")
ok("MeOH inlet-limit robustness: 81 groups, caps 5-10%, 5% tolerance",
   _cap["groups"] == pl6["groups"] and _cap["caps_pct"] == ["5", "6", "6.86", "8", "10"] and _cap["tolerance"] == 0.05)
tokens("SI Note 3: inlet-limit robustness of the plant-cost leader", s8, f"is within 5% of the cheapest operating point at every limit from 5 to 10% in {_cap['s6_leader']['within_tolerance']} of {_cap['groups']} comparisons, against {_cap['minimax']['within_tolerance']} for an oracle that knows every limit's costs, {_cap['selectivity']['within_tolerance']} for the most selective entry and {_cap['sty_leader']['within_tolerance']} for the paper's STY leader")

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
          f"{len(_k1) * g6:,} at the reported noise level) differ in the inert-limited loop")
# Exact-run/response-surface agreement counts were removed from the SI.
# The per-replicate S6 totals and cross-source S5 validation gate above remain.
_pv = [v["top1_mismatch_groups"] for k, v in pb["variants"].items()
       if not k.startswith(("catalyst", "combined", "baseline"))]
_pvc = _j("analysis/meoh_field_pooled_2026_10_15/robustness/plant_variants/sensitivity_summary.json")
_pvx = {k: v["top1_mismatch_groups"] for k, v in _pvc["variants"].items()
        if not k.startswith(("catalyst", "combined", "baseline"))}
_pv5 = [v for k, v in _pvx.items() if "|" not in k]
_pv6 = [v for k, v in _pvx.items() if k.endswith("|S6")]
ok("MeOH plant variants, combined set: baseline equals the combined S5 result; S5 and S6 variants paired",
   _pvc["check"]["baseline_top1"] == f"{pl5['disagreements']}/{pl5['groups']}" and len(_pv5) == len(_pv6) > 0)
_battery = [pl6['disagreements'], PL6['inert_co']['disagreements'], *_pv6]
_battery += [_frac(v['disagreements'])[0] for k, v in RB['3_co_bound']['combined'].items() if k.endswith('|6.86')]
for _key in ('4_conversion', '5_catalyst', '6_split'):
    _battery += [_frac(v['disagreements'])[0] for k, v in RB[_key]['S6']['combined'].items()
                 if isinstance(v, dict) and 'disagreements' in v and not k.startswith('all|')]
tokens("MeOH variant battery: printed range covers the source scenarios", s8,
       f"the count stays between {min(_battery)} and {max(_battery)} of {pl6['groups']}")

ok("MeOH plant benchmark: baseline reproduces the S5 headline",
   pb["check"]["baseline_top1"] == f"{P0['top1_mismatch_groups']}/{P0['groups']}")

# main-text summaries written in the 2026-10-07 compression (the full statements live in the Supplementary Notes)
m_feru = main_section("Bulk Ru loses on the price of its metal")
_layer = {r["metal"]: r for r in rows(FEB + "inversion_layer_common_reference.csv")}
_repl = {k: float(_layer[k]["annualized_replacement_cost_USD_t_NH3"]) for k in ("Fe", "Ru", "Os")}
_ru_win = sum(r["economic_winner"] == "Ru" for r in draws)
claim_tokens("Main text: layer-wise reversal, process optimization moves the gap into compression, descriptor winners",
    ("main text", m_feru, [f"at {_repl['Fe']:.3f} US dollars per tonne for Fe against {_repl['Ru']:.2f} for Ru",
    f"Priced as iron, at {r8['price_USD_kg']:.0f} US dollars per kilogram, Ru wins ({r8['total_cost_USD_t']:.2f} against {fe['total_cost']:.2f} US dollars per tonne)",
    f"places parity at {float(parity['price_USD_kg']):.0f} US dollars per kilogram",
    "process optimization only moves it",
    f"Ru retreats to about {ru['T_C']:.0f} °C, {ru['P_bar']:.0f} bar and a small bed while Fe runs near {fe['T_C']:.0f} °C and {fe['P_bar']:.0f} bar",
    f"the {gap:.2f} US dollars per tonne between them reappears mainly as compression of fresh feed (+{_pools['fresh_compression_electricity']:.3f}), metal inventory (+{_pools['metal_inventory']:.3f}) and compressor capital (+{_pools['compressor_CAPEX']:.3f})",
    f"first in {100 * fe_win / len(draws):.1f}% of {len(draws):,} descriptor samples"]),
    ("Supplementary Methods", supplementary_method("Ammonia synthesis"), [f"{_yaml_num(manifest, 'max_catalyst_bed_m3'):.0f} m³ limit on bed volume"]))
_cmin = min(float(r["Ru_minus_Fe_USD_t"]) for r in cmc_draws)
claim_tokens("Main text: economic Monte Carlo, Fe cheaper in every draw and the smallest difference",
    ("main text", m_feru, [f"Fe is cheaper in all {len(cmc_draws):,} draws of prices, capital cost and catalyst lifetime"]),
    ("SI Notes", s2_full, [f"smallest Ru - Fe difference of {_cmin:.3f} US dollars per tonne"]))
ok("NH3 economic Monte Carlo: Ru dearer than Fe in every draw", _cmin > 0)
tokens("SI Note 7: layer-wise replacement costs and total gap", s2_full, f"annualized metal replacement of {_repl['Fe']:.3f}, {_repl['Ru']:.2f} and {_repl['Os']:.2f} US dollars per tonne for Fe, Ru and Os", f"the Ru - Fe difference grows from {_repl['Ru'] - _repl['Fe']:.2f} US dollars per tonne in metal replacement to {gap:.3f} in total")
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
tokens("SI Note 2: curated-data errors counted by root cause (errata adjudication)", s6, f"{_ec['root_causes']} root causes", f"{_ec['value_cells_error_rules']} cells")
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
m_feru2 = (main_section("Bulk Ru loses on the price of its metal") + " "
           + main_section("Supported Ru/C turns the choice into one of metal financing") + " "
           + main_section("The optimizer recovers the industrial bed order"))
KAAP_P = IR["c_0_KAAP"]["Ru"]["P_bar"]
_LC = _load_module("lifecycle_cashflow", ROOT / "analysis/nh3_ru_net_recovery_boundary_2026_10_12/lifecycle_cashflow.py")
LIFE, PLANT_Y = _ynum("catalyst_life_y"), dcf["frozen_plant_years"]
_buy, _coll = _LC.lifecycle_dates(LIFE, PLANT_Y)
tokens("Methods: lifecycle cash-flow variant (dates and financing range)", methods,
       f"every metal purchase (at {_and(f'{t:.0f}' for t in _buy)} years) and credit for recovered metal (at replacement and closure) at its date",
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
       f"The fused-iron law gives {_mp['model_pct']['Keestra KM1R_1964']:.1f}% NH₃ against "
       f"{_mp['measured_pct']['magnetite']:.0f}% measured",
       f"it requires {_bvr['min']:.2f}–{_bvr['max']:.1f} times the bed",
       f"Fe costs "
       f"{ia['Fe']['cost']:.2f} US dollars per tonne at {ia['Fe']['T_C']:.0f} °C, {ia['Fe']['P_bar']:.0f} bar and a "
       f"{ia['Fe']['Tsep_C']:.0f} °C separator and Ru in the benchmark formulation {ia['Ru']['cost']:.2f} at "
       f"{ia['Ru']['P_bar']:.0f} bar. The activity multiple for parity is {IR['parity']:.2f} "
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
       f"The Ru/C law reproduces the {_ruv['n']} measured points of its source with a mean error of {pc(_ruv['mean_abs_rel_err'])}%",
       f"the fused-iron law the outlet of a commercial magnetite catalyst at 100 bar within {100 * _mp['rel_err']['Keestra KM1R_1964 vs magnetite']:.0f}%",
       "Each catalyst is optimized only over the states inside its fitted pressure range",
       f"each bed filled with fused iron (up to {_ynum('T_max_Fe_C'):.0f} °C) or Ru/C (up to {_ynum('T_max_Ru_C'):.0f} °C, the top of its measured range)",
       f"at {_ylist('loops_bar')[0] / 10:.0f} MPa, a {_ynum('separator_C'):.0f} °C separator and {pc(_ynum('inerts_typical'))}% inerts")

ok("Methods: the 9 MPa loop lies inside both fitted pressure ranges",
   fe_irng[0] <= _ylist("loops_bar")[0] <= fe_irng[1] and ru_irng[0] <= _ylist("loops_bar")[0] <= ru_irng[1]
   and KAAP_P == _ylist("loops_bar")[0])

# measured kinetics: break-even metal financing rate of supported Ru/C against Fe (frontier provenance, 1.2)
_be_g, _be_k = IR["b_breakeven"]["rate"], IR["c_breakeven_KAAP"]["rate"]
_be_g90, _be_k90 = IR["b_breakeven_r90"]["rate"], IR["c_breakeven_KAAP_r90"]["rate"]
ok("Measured Ru/C rows of SI Note 7 table: both optima at the stated pressure (Ru/C at the top of its fitted range)",
   IR["b_0"]["Ru"]["P_bar"] == IR["b_12"]["Ru"]["P_bar"] == ru_irng[1]
   and IR["c_0_KAAP"]["Fe"]["P_bar"] == IR["c_12_KAAP"]["Ru"]["P_bar"] == KAAP_P)
tokens("SI Note 7: measured-kinetics break-even financing rates", s2_full,
       f"Ru/C stays cheaper than Fe up to a metal financing rate of {pc(_be_g, 2)}% per year, and in the KAAP-type loop up "
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


tokens("SI Note 7: measured-kinetics robustness cases",
    s2_full,
    f"Across {len(_rb)} cases that vary",
    f"the break-even financing rate spans {pc(_rbs['global']['breakeven_range'][0], 2)}–"
       f"{pc(_rbs['global']['breakeven_range'][1], 2)}% per year in the main loop and "
       f"{pc(_rbs['KAAP']['breakeven_range'][0], 2)}–{pc(_rbs['KAAP']['breakeven_range'][1], 2)}% per year in the "
       f"KAAP-type loop")
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
tokens("Main text: descriptor versus measured Ru H2 order", m_feru2,
       f"giving Ru an apparent H₂ order of {_dru['H2']:+.1f} where {ru_o['H2']:+.1f} is measured")
# The individual NH3 orders remain checked against SI Note 7 below.
tokens("SI Note 7: apparent orders of the descriptor kinetics", s2_full,
       f"At {_dcond} NH₃ the descriptor kinetics give Ru apparent orders of {_dru['H2']:+.1f} in H₂ and "
       f"{_dru['NH3']:+.1f} in NH₃ and fused iron {_dfe['NH3']:+.1f} in NH₃")
ok("Descriptor apparent orders: the 1.2 model of the canonical run; Ru H2 order above the measured Ru/C order; fused-iron "
   "NH3 inhibition weaker than measured (the contrast the text draws)",
   _do12["model"] == "NH3-FINAL-1.2" and _do12["run"] == RUN.name and _do12["states"] == det["process_state_count"]
   and _dru["H2"] > ru_o["H2"] > 0 and _dru["NH3"] < ru_o["NH3"] < 0 and fe_o["NH3"] < _dfe["NH3"] < 0
   and all(abs(_do12["orders"][mt]["central"][s_] - _do12["orders"][mt]["forward_0p02"][s_]) < 0.05
           for mt in ("Ru", "Fe") for s_ in ("N2", "H2", "NH3")))

# The old numerical DFT/GB offset range was removed in the SI compression.
# Retain the cross-source equilibrium consistency gate for the current NH3 model.
_hb = _j("analysis/verify_2026_10_12_hybrid_bed/hybrid_bed_feasibility.json")["equilibrium"]
_off = [(e_["dGf_model_kJ_mol"] - e_["dGf_exp_kJ_mol"]) / 96.485 for e_ in _hb]
ok("Thermodynamic sources: DFT/GB offsets positive; NH3-FINAL-1.2 has no equilibrium offset",
   len(_off) >= 3 and all(x > 0 for x in _off)
   and abs(sup["nh3_model"]["y_eq_model_over_exp"]["min"] - 1) < 1e-12
   and abs(sup["nh3_model"]["y_eq_model_over_exp"]["max"] - 1) < 1e-12)
_cal = _j("provenance/nh3_final_1_2/source_harness/calibration_comparison.json")
_cs = _cal["calibration_state"]
_cal_txt = f"Catalyst productivity is calibrated on the fused-iron bed at {_cs['T_C']:.0f} °C, {_cs['P_bar']:.0f} bar and a {_cs['Tsep_C']:.0f} °C separator"
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
   and _cal_txt in supplementary_method("Ammonia synthesis") and _cal_txt in methods)

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
claim_tokens("NH3 descriptor perturbation: SI margins and Table 4b joint/plant-volume values",
    ("SI Note 7", s2_full, [f"smallest margin +{_pdd['min_finite_single']['gap']:.2f} US dollars per tonne", f"(smallest margin +{_pdd['worst_corner']['typical']['gap']:.2f})", f"{_pdd['worst_corner']['max']['n_flipped']} of 64 combinations reverse", f"multiplied by {_pdmag['max']:.2f}"]),
    ("SI Table 4b", _table_section('4b'), [f"| all five, each towards Ru, typical | – | +{_pdd['joint_Ru_favouring']['typical']['gap']:.2f} |", f"| all five, each towards Ru, largest | – | +{_pdd['joint_Ru_favouring']['max']['gap']:.2f} |", f"| catalyst amount (Fe), largest at plant conditions, + | catalyst amount ×{_pdmag['max_plant_sizing']:.2f} (Fe) | +{_pdps[0]:.2f} |"]))
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
tokens("SI Note 7: staged converter, Ru/C share across the window",
    s2_full,
    f"The Ru/C share of the catalyst volume falls from {pc(_sh_lo)}% to {pc(_sh_hi)}% across the window",
    "a converter with Ru/C first is optimal in no case tested")
tokens("SI Note 7: staged-converter window edges (2 decimals)", s2_full,
       f"fused iron upstream with Ru/C downstream for Ru financing rates of 0–{pc(wK['95']['hi'], 2)}% per year",
       "and as all-Fe above")
tokens("SI Note 7: staged window at 90 % recovery and at Ru price -30 % / +30 %", s2_full, f"The window moves with recovery ({_lo0(wK['90'])}–{pc(wK['90']['hi'], 2)}% per year at {pc(r_lo)}%)", f"({_lo0(wK['m30'])}–{pc(wK['m30']['hi'], 2)}% at -30%, 0–{pc(wK['p30']['hi'], 2)}% at +30%)")
# The three-rate savings list was removed; the reference-rate saving is checked
# against IRS/IRF below in "NH3 staged: median-rate arrangement, Fe share and savings".

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
tokens("SI Note 7 table: recycle-rise sensitivity costs", _feru_table,
       f"| Descriptor | Benchmark, 9.2 bar recycle rise | Benchmark bed | {float(_t1_92[0]['cost_USD_t']):.2f} | "
       f"{float(_t1_92[1]['cost_USD_t']):.2f} | – (order of all 15 metals unchanged) |")
tokens("SI Note 7: recycle-rise sensitivity costs", s2_full, *[f"{float(r['cost_USD_t']):.3f}" for r in _t1_92], "rank order of all 15 metals unchanged")
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
   "SI citations resolve",
   _st_heads == list(range(1, len(_st_heads) + 1)) and _st_order == _st_heads and set(_st_si) <= set(_st_heads),
   f"tables {_st_heads}, main-text order {_st_order}")

# ----- Recycled CO converted up to CO-hydrogenation equilibrium (merged PR #84) -------------------------------
_cob = _j("analysis/meoh_co_conversion_bound_2026_10_13/summary.json")
_hi, _hn = _cob["results"]["high"]["6.86"], _cob["results"]["high"]["none"]
_si_flat = re.sub(r"\s+", " ", raw_si)
tokens("SI Note 3: recycled-CO variant definition", s8, "recycled CO inert or converted up to CO-hydrogenation equilibrium")
# Removed SI-only detail; no current reader-facing numeric anchor remains.
ok("PR #84 gate: the central rule reproduces the frozen columns and anchors",
   all(v["passed"] for v in _cob["gate"].values()) and all(_cob["frozen_anchors"].values()))

# ----- Supervisor revision 2026-10-21: current claims and their committed sources -----------------
# Keep each numerical assertion local to the relevant section, with formatting derived from the source.
_rcat, _rstrict = _cr["cat_primary"], _cr["cat_strict"]
tokens("MeOH main: conversion-raised catalyst headline and paper-bootstrap interval", m_field,
       f"In {_rcat['changed']} of the {_rcat['groups_2plus_catalysts']} comparisons that contain at least two catalysts "
       f"({pc(_rcat['fraction'])}%; 95% confidence interval {pc(_rcat['ci95'][0])}–{pc(_rcat['ci95'][1])}%)",
       f"in {_rcat['gt5pct']} of them building it would cost more than 5% extra")
tokens("SI Note 3: papers with conversion-raised catalyst disagreements", s8,
       f"from {_rcat['papers_changed']} of their")
# The >10% count remains checked in MeOH SI: conversion raised counts, regret thresholds and interval.
tokens("MeOH main: laboratory conversion companion", m_field,
       f"the count is {_cc['changed']} of {_cc['groups_2plus_catalysts']} ({pc(_cc['fraction'])}%)")
# The 18/52 and 22/52 strict identities remain checked in the two MeOH SI count checks below.

tokens("MeOH main: operating-point counts and temperature shift", m_field,
       f"Of {_ct['catalysts_with_2plus_T']} catalysts measured at several temperatures, {_ct['plant_T_differs']} are cheapest to run",
       f"{_ct['plant_colder']} of them at a lower one, by a median of {_quantiles(_ctC, [0.5])[0]:.0f} °C")
# The conversion-raised point-level count was removed; catalyst-level counts remain below.
for _name, _c, _strict in (("conversion raised", _rcat, _rstrict),
                          ("laboratory conversion", _cc, CL['cat_strict']['comparison'])):
    tokens(f"MeOH SI: {_name} counts, regret thresholds and interval", s8,
           f"{_c['changed']} of {'the ' if _name == 'conversion raised' else ''}{_c['groups_2plus_catalysts']}",
           f"{pc(_c['fraction'], 1)}%; {('paper-cluster bootstrap 95% confidence interval ' if _name == 'conversion raised' else '')}"
           f"{pc(_c['ci95'][0], 1)}–{pc(_c['ci95'][1], 1)}%",
           f"{_c['gt1pct']}, {_c['gt5pct']} and {_c['gt10pct']}",
           (f"{_strict['changed']} of {_strict['groups_2plus_catalysts']} ({pc(_strict['fraction'], 1)}%; "
            f"{pc(_strict['ci95'][0], 1)}–{pc(_strict['ci95'][1], 1)}%" if _name == 'conversion raised' else
            f"{_strict['changed']} of {_strict['groups_2plus_catalysts']} with the stricter identity"))
# The single Re/TiO2 comparison switches to its plant leader on a per-Re STY basis.
_rrows = rows("analysis/meoh_catalyst_level_2026_10_19/groups_catalyst_level_conversion_raised.csv")
_re = [r for r in _rrows if r['doi'] == '10.1021/acscatal.5c05984']
ok("MeOH per-Re source: raised Re/TiO2 contributes one change above 5%",
   len(_re) == 1 and _re[0]['changed'] == 'True' and float(_re[0]['gap']) > .05
   and sum(r['changed'] == 'True' for r in _rrows) == _rcat['changed'])
# Per-Re catalyst-count prose was removed; the per-Re source gates remain above.
tokens("Abstract: conversion-raised methanol and ammonia field shares", main_section_h2("Abstract"),
       f"{_rcat['changed']} of {_rcat['groups_2plus_catalysts']} methanol comparisons",
       f"{NPL['mismatch']} of {NPL['groups']} ammonia comparisons")

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
       "It is applied to Ru by analogy")
tokens("NH3 main: supported Ru/C savings at median lease rate", m_feru2,
       f"At that rate Ru/C is the cheaper catalyst, by {-float(_fr['benchmark_RuC_minus_Fe']):.2f} US dollars per tonne at the two catalysts' own optima and {-float(_fr['KAAP_RuC_minus_Fe']):.2f} in the KAAP-type loop")
claim_tokens("NH3 main and SI Note 7: owned and supplier-lease break-even rates",
    ("main text", m_feru2, [f"flips it at {pc(_bes['benchmark_owned'], 2)}% per year",
       f"and at {pc(_bes['KAAP_owned'], 2)}%"]),
    ("SI Note 7", s2_full, [f"the break-even lease rates are {pc(_bes['benchmark_lease_unsecured'], 2)}% and {pc(_bes['KAAP_lease_unsecured'], 2)}% per year"]))
claim_tokens("NH3 Abstract, Results and Discussion: measured Ru/C financing thresholds",
    ("Abstract", main_section_h2("Abstract"), [f"financed below {pc(_bes['KAAP_owned'], 1)}–{pc(_bes['benchmark_owned'], 1)}% per year"]),
    ("Results", NH3_MAIN, [f"financed below {pc(_bes['KAAP_owned'], 1)}–{pc(_bes['benchmark_owned'], 1)}% per year"]),
    ("Discussion", discussion, [f"below {pc(_bes['benchmark_owned'], 1)}% per year at the two catalysts' own optima and {pc(_bes['KAAP_owned'], 1)}% in a KAAP-type loop"]))
for _basis, _prefix, _be in (("own optima", "b", 'benchmark_owned'), ("KAAP-type", "c", 'KAAP_owned')):
    _z = IR['b_0' if _prefix == 'b' else 'c_0_KAAP']
    _h = IR['b_12' if _prefix == 'b' else 'c_12_KAAP']
    tokens(f"NH3 SI Note 7 table: {_basis} costs and reference-rate savings", _feru_table,
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
    ("SI Notes", s2_full, [f"Fe costs {ia['Fe']['cost']:.2f} US dollars per tonne at {ia['Fe']['T_C']:.0f} °C, {ia['Fe']['P_bar']:.0f} bar",
    f"{ia['Ru']['cost']:.2f} at {ia['Ru']['P_bar']:.0f} bar",
    f"{IR['parity']:.2f} ({min(_mult_ir):.2f}–{max(_mult_ir):.2f}"]))
tokens("NH3 SI Note 7 table: bulk measured and descriptor parity rows", _feru_table,
       f"| Descriptor | Benchmark | Benchmark bed | {fe['total_cost']:.2f} | {ru['total_cost']:.2f} |",
       f"| {ia['Fe']['cost']:.2f} | {ia['Ru']['cost']:.2f} ({ia['Ru']['P_bar']:.0f} bar) | activity rises {IR['parity']:.0f}-fold",
       f"activity rises {bw['Ru_activity_break_even_multiplier']:.0f}-fold, or Ru costs {float(parity['price_USD_kg']):.0f} US dollars per kilogram")
_st = IRS['window_keestra']['best_at'][f'{_rate:.2f} %/y']
tokens("NH3 staged: median-rate arrangement, Fe share and savings", m_feru2,
       f"from 0 to {pc(_bes['staged_Fe_first_beats_Fe_below'], 2)}% per year",
       f"fused iron fills {pc(1 - _st['best_Ru_volume_fraction'])}% of the catalyst volume",
       f"saves { -_st['staged_minus_Fe']:.2f} US dollars per tonne")
tokens("NH3 SI Note 7 table: staged reference-rate costs", _feru_table,
       f"| {_st['all_Fe']:.2f} (all Fe) | {_st['staged']:.2f} at {_rate:.2f}% per year |")
ok("NH3 staged source: reference financing row matches measured in-range envelope",
   _st['best'] == _fr['staged_optimal'] == 'FRR'
   and abs(_st['staged'] - float(_fr['staged_optimal_cost'])) < 1e-5
   and abs(_bes['staged_Fe_first_beats_Fe_below'] - wK['95']['hi']) < 2e-4)
claim_tokens("NH3 staged: measured inhibition and rate advantage",
    ("main text", m_feru2, [f"{_rr_lo:.0f}-fold at 2% NH₃ to {_rr_hi:.0f}-fold at 14%"]),
    ("SI Note 7", s2_full, [f"NH₃ {fe_o['NH3']:+.2f}", f"NH₃ {ru_o['NH3']:+.2f}"]))

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
    tokens(f"NH3 Table 4a: {_qty} typical deviation", _table_section("4a"), f"| {_qty} | {_er['n']} | {_er['n_pass']} | {float(_er['typical_abs_dev_pct']):.1f}% |")
_er = _e_new['bed volume, cost-optimal designs and Fe optimum']
tokens("NH3 Table 4a: cost-optimal bed volume deviation", _table_section("4a"), f"| bed volume, cost-optimal designs and Fe optimum | {_er['n']} | {_er['n_pass']} | {float(_er['typical_abs_dev_pct']):.1f}% |")
tokens("NH3 SI Table 4a: cost-optimal bed deviation (removed main-text rounding)", _table_section("4a"),
       f"| bed volume, cost-optimal designs and Fe optimum | {_er['n']} | {_er['n_pass']} | {float(_er['typical_abs_dev_pct']):.1f}% |")
_pert = _j(KC + 'perturbation_summary.json')
_p0 = _pert['comparisons']['benchmark supported 0']['magnitudes']['typical']
_p12 = _pert['comparisons']['benchmark supported 0.12']['magnitudes']['typical']
tokens("NH3 SI perturbation: benchmark single-deviation shifts at 0 and 12 percent", s2_full,
       f"{_p0['single_shift_min']:.2f} to {_p0['single_shift_max']:+.2f}",
       f"{_p12['single_shift_min']:.2f} to {_p12['single_shift_max']:+.2f}")
# KAAP shift ranges and reversing-corner counts were removed from the SI.
_p0 = _pert['comparisons']['benchmark supported 0']['magnitudes']['typical']
_p12 = _pert['comparisons']['benchmark supported 0.12']['magnitudes']['typical']
tokens("NH3 SI Note 7 perturbation: single shifts (removed main-text rounding)", s2_full,
       f"{_p0['single_shift_min']:.2f} to {_p0['single_shift_max']:+.2f} US dollars per tonne without financing",
       f"{_p12['single_shift_min']:.2f} to {_p12['single_shift_max']:+.2f} at 12% per year")
_bulk = _pert['comparisons']['bulk benchmark']['magnitudes']['typical']
# Bulk minimum margin is no longer printed; the largest catalyst factor remains in Table 4b.
tokens("NH3 Table 4b: largest catalyst-amount factor", _table_section('4b'),
       f"catalyst amount ×{_pert['magnitudes']['KIN']['max']:.2f} (Fe)")
_prk = _j(KC + 'pr_loop_results.json')['comparisons']['KAAP_90bar_m20C_grid_optimum']
tokens("NH3 SI: Peng–Robinson KAAP cost gaps and financing break-evens", s2_full,
       f"{_prk['PR_gap']:.2f} US dollars per tonne", f"against {_prk['canonical_gap']:.2f} in the cost model",
       f"break-even of {pc(_prk['PR_break_even'], 2)}% per year, against {pc(_prk['canonical_break_even'], 2)}%")
ok("NH3 Peng–Robinson source: both fitted domains and positive 12-percent gap",
   all(_prk['PR'][c]['rate_P_inside_source_range'] and _prk['PR'][c]['rate_T_inside_source_range'] for c in ('Fe','Ru'))
   and _prk['PR_gap'] > 0 and abs(_prk['PR_gap'] - (_prk['PR']['Ru']['total_USD_t'] - _prk['PR']['Fe']['total_USD_t'])) < 1e-9)

_auv = _j('artifacts/au_tio2_decision_boundary_v2/summary.json')
_ap = _auv['V2_0_per_candidate_mc_primary']
tokens("Au SI: candidate-specific scatter, full order and leader",
    s5,
    f"{_ap['sigma_ln']:.2f}",
    f"{pc(_ap['full_preservation'], 2)}% of {_ap['draws']:,} draws",
    f"{pc(_ap['winner_2nm_probability'], 2)}%")
# The adjacent-pair inversion probabilities were removed from the SI.
# The per-sigma sensitivity lists and adjacent-pair inversion probabilities were
# removed from the SI; the primary scatter and retained lifetime results are checked.
_life = _auv['L2_lifetime']
tokens("Au SI: lifetime flip ratios and exponent boundary", s5,
       *[f"{v:.3f}" for v in _life['adjacent_flip_thresholds'].values()],
       "every pair inverts", f"{_life['q_star_nominal']:.1f}",
       f"({_life['q_star_range_over_shared_exponents'][0]:.1f}–{_life['q_star_range_over_shared_exponents'][1]:.1f}")
_cut = rows('artifacts/au_tio2_decision_boundary_v2/l2_q_cut_shared_nm_sampled.csv')
for _q in (1.8, 2.0):
    _a = next(r for r in _cut if abs(float(r['q']) - _q) < 1e-8)
    tokens(f"Au SI: sampled-exponent leader at lambda {_q:.1f}", s5,
           f"{dfmt(Decimal(_a['p_winner_2nm']) * 100, 1)}%", f"λ = {_q:.1f}")
for _a in _auv['L2_L3_combined_273_293K_moderate']:
    if _a['q'] < 0: continue
    if _a['q'] in (0, 1.0, 1.9):
        tokens(f"Au SI: combined operating and lifetime full order at lambda {_a['q']:g}", s5,
               f"{pc(_a['full_preservation_fraction'], 2)}%")
    elif _a['q'] in (2.5, 3.0):
        tokens(f"Au SI: fully inverted at lambda {_a['q']:g}", s5, f"{pc(_a['fully_inverted_fraction'], 2)}%")
# Intermediate full-order and combined leader lists were removed in the SI compression.
_am = main_section('Without a price or selectivity channel the ranking holds, and catalyst life sets its limit')
tokens("Au main: rounded candidate-specific and operating preservation", _am,
       f"{pc(_ap['winner_2nm_probability'], 1)}%", f"{pc(_ap['full_preservation'], 1)}%",
       f"{pc(_auv['L3_semiopen']['primary_273_293K_moderate']['full_preservation_fraction'], 1)}%")

SAB = 'analysis/sabatier_ru_ni_2026_10_19/results/'
_sab = _j(SAB + 'summary.json')
_sc, _smc = _sab['central'], _sab['monte_carlo']
_sab_si = section('Ru against Ni in CO₂ methanation')
tokens("Sabatier main: volume ratio, price ratio and central parity", m_chi,
       f"{_sc['Pi']:.2f}", "exceeds", f"{_sc['r_V']:.2f}", "catalyst inventory alone favours Ni at every scale", f"below {_sc['parity_scale_mw']:.2f} MW")
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
tokens("Sabatier SI: deterministic scenario parity range", _sab_si,
    f"boundary between {min(float(r['parity_scale_mw']) for r in _ss):.2f} and {max(float(r['parity_scale_mw']) for r in _ss):.1f} MW")
ok("Sabatier sources: deterministic endpoint order and boundary count",
   all(r['ranking_0p1MW'] == 'Ru>Ni' and r['ranking_100MW'] == 'Ni>Ru' for r in _ss)
   and len(_bmap) == _sab['boundary']['n_points'])
_sweep = rows(SAB + 'central_sweep.csv')
_phi10 = next(float(r['phi_proc']) for r in _sweep if abs(float(r['scale_mw'])-10) < 1e-8)
tokens("Sabatier SI: process leverage across scale and at parity",
    _sab_si,
    f"{_sc['phi_proc_0p1MW']:.2f} at 0.1 MW",
    f"{(_sc['Pi'] / _sc['r_V'] - 1):.2f} at the parity scale",
    f"{_sc['phi_proc_100MW']:.3f} at 100 MW")

# Numerical caption claims live in the detailed captions. Reference-order checks above
# deliberately continue to read the short, reader-facing captions.
_f5 = _caption("docs/MAIN_FIGURE_CAPTIONS_DETAILED_2026-10-21.md", "Figure 5")
_ed7 = _caption("figures/extended_data/ED_CAPTIONS_DETAILED.md", "Extended Data Fig. 7")
_ed8 = _caption("figures/extended_data/ED_CAPTIONS_DETAILED.md", "Extended Data Fig. 8")
_ed9 = _caption("figures/extended_data/ED_CAPTIONS_DETAILED.md", "Extended Data Fig. 9")
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
       "The plant-cost leader of a comparison is its plant-level optimum")
tokens("Methods semantic lock: catalyst identity and ranking over operating points", main_section("CO₂-to-methanol"),
       "What counts as a different catalyst was fixed before any comparison was counted",
       "composition (promoters and dopants included), loading of the active component, support or synthesis",
       "Entries of one sample that differ only in reaction temperature, time on stream, activation or reactor operating mode are one catalyst at different operating points",
       "Each catalyst enters the laboratory ranking at its highest STY and the plant ranking at its lowest cost",
       "A stricter identity merges samples that differ only in synthesis")
_activity_ratio = 10 ** (m['Ru']['activity_logTOF'] - m['Fe']['activity_logTOF'])
_price_ratio = eq['Ru_canonical']['price_USD_kg'] / r8['price_USD_kg']
tokens("NH3 main: intrinsic turnover and metal-price ratios", NH3_MAIN,
       f"Ru turns over {_activity_ratio:.0f} times faster than Fe but costs {_price_ratio:,.0f} times more per kilogram")
ok("MeOH main and SI: catalyst fractions are two model treatments, not a confidence interval",
   f"{_rcat['changed']} of the {_rcat['groups_2plus_catalysts']}" in m_field
   and f"{_cc['changed']} of {_cc['groups_2plus_catalysts']}" in m_field
   and pc(_rcat['fraction']) == "33" and pc(_cc['fraction']) == "41"
   and _rcat['groups_2plus_catalysts'] == _cc['groups_2plus_catalysts']
   and f"at {pc(_rcat['fraction'])}–{pc(_cc['fraction'])}%" in s8
   and "a range over two model treatments rather than a confidence interval" in s8,
   f"source fractions {_rcat['changed']}/{_rcat['groups_2plus_catalysts']} ({pc(_rcat['fraction'], 1)}%) and "
   f"{_cc['changed']}/{_cc['groups_2plus_catalysts']} ({pc(_cc['fraction'], 1)}%)")

# ----- Author-requested prose checks (2026-10-21) -------------------------------
def _outside_parentheses_semicolons(body):
    """Report prose semicolons outside parentheses/brackets, skipping Markdown tables."""
    depth = 0
    brackets = 0
    locations = []
    for line_number, line in enumerate(body.splitlines(), 1):
        if line.lstrip().startswith("|"):
            continue
        for column, char in enumerate(line, 1):
            if char == "(":
                depth += 1
            elif char == ")":
                depth = max(0, depth - 1)
            elif char == "[":
                brackets += 1
            elif char == "]":
                brackets = max(0, brackets - 1)
            elif char == ";" and depth == 0 and brackets == 0:
                locations.append(f"{line_number}:{column}")
    return locations


_semicolons = _outside_parentheses_semicolons(_body)
ok("Main prose: no sentence-joining semicolons outside parentheses and tables",
   not _semicolons, "line:column " + ", ".join(_semicolons) if _semicolons else "")
_intro = re.sub(r"\s+", " ", _introduction).replace("−", "-")
for _abbr, _expanded in (("STY", "space-time yield"), ("TOF", "turnover frequency")):
    _definition = re.compile(r"\b" + re.escape(_expanded) + r"\s*\(" + _abbr + r"\)")
    _definitions = list(_definition.finditer(_body))
    _first_use = re.search(r"\b" + _abbr + r"\b", _body)
    ok(f"Main body: {_abbr} defined once in Introduction before abbreviated use",
       len(_definitions) == 1 and bool(_definition.search(_intro))
       and _first_use is not None
       and _definitions[0].start() < _first_use.start() < _definitions[0].end(),
       f"{len(_definitions)} definitions; first abbreviation must be in its definition")
for _abbr, _expanded in (("STY", "space-time yields?"), ("TOF", "turnover frequency"),
                         ("KAAP", "Kellogg Advanced Ammonia Process"), ("SNG", "synthetic natural gas")):
    _definition = re.compile(r"\b" + _expanded + r"\s*\(" + _abbr + r"s?(?:, [^)]*)?\)")
    _definitions = list(_definition.finditer(raw_si))
    _first_use = re.search(r"\b" + _abbr + r"s?\b", raw_si)
    ok(f"SI text: {_abbr} defined once, at its first use",
       len(_definitions) == 1 and _first_use is not None
       and _definitions[0].start() < _first_use.start() < _definitions[0].end(),
       f"{len(_definitions)} definitions; first abbreviation must be in its definition")
_lease_fy = sorted({int(m.group(1)) for r in rows("analysis/nh3_ru_metal_financing_evidence_2026_10_12/"
                                                  "pbf_catalyst_lease_contracts.csv")
                     for m in [re.search(r"(?:FY|Q\d )(\d{4})", r["first_disclosed_in"])] if m})
_lease_ref = reference_number("Annual reports on Form 10-K")
ok(f"Lease filings: years in SI Methods and ref. {_lease_ref} match the 32 contracts",
   f"filings for {_lease_fy[0]}–{_lease_fy[-1]}" in raw_si
   and _lease_ref is not None
   and any(n == _lease_ref and f"fiscal years {_lease_fy[0]} and 2015–{_lease_fy[-1]}" in entry
           for n, entry in _reference_entries), f"filing years {_lease_fy}")
ok("Main text and SI: no institutional library wording",
   "institutional library" not in text.casefold()
   and "institutional library" not in re.sub(r"\s+", " ", raw_si).casefold())



_si_semicolons = _outside_parentheses_semicolons(raw_si)
ok("SI prose: no sentence-joining semicolons outside parentheses, brackets and tables",
   not _si_semicolons, "line:column " + ", ".join(_si_semicolons) if _si_semicolons else "")
# STY and TOF are defined once in the main Introduction (checked above).
# The compressed SI uses those abbreviations without repeating the expansions.

_si_headings = "\n".join(re.findall(r"^#{1,6} .+$", raw_si, re.M))
# Inspect headings and prose captions only; table rows and the source companion carry provenance.
_table_blocks = re.findall(r"^### Supplementary Table ([0-9]+[a-z]?) \|[^\n]*\n(.*?)(?=^### |\Z)",
                           SIT, re.M | re.S)
_reader_captions = "\n".join(line for line in SIT.splitlines()
                              if not line.lstrip().startswith(("|", "<!--")))
_forbidden = re.compile(r"\b(?:published|frozen|canonical|registered)\b", re.I)
for _scope, _prose in (("headings", _si_headings), ("reader-facing table captions", _reader_captions)):
    _bad_words = [line.strip() for line in _prose.splitlines() if _forbidden.search(line)]
    ok(f"SI {_scope}: no Published, frozen, canonical or registered",
       not _bad_words, " | ".join(_bad_words))

_short_spec = importlib.util.spec_from_file_location("si_table_captions_short", ROOT / "tools/si_table_captions_short.py")
_short_module = importlib.util.module_from_spec(_short_spec)
_short_spec.loader.exec_module(_short_module)
_short_errors = []
for _key, _expected in _short_module.SHORT.items():
    _matches = [body for key, body in _table_blocks if key == _key]
    _source_count = len(re.findall(r"^### Supplementary Table " + re.escape(_key) + r" \|", SI_SOURCES, re.M))
    _actual = _matches[0].split("\n|", 1)[0].strip() if len(_matches) == 1 else ""
    if len(_matches) != 1 or _source_count != 1 or re.sub(r"\s+", " ", _actual) != re.sub(r"\s+", " ", _expected):
        _short_errors.append(_key)
ok("SI tables: every SHORT key matches one generated table, its short caption and source companion",
   not _short_errors, "mismatched keys: " + ", ".join(_short_errors) if _short_errors else "")

# ----- P2 extraction ledger and compressed reader-facing prose (2026-10-21) -----
_p2 = _j("analysis/extraction_ledger_2026_10_21/summary.json")
_p2_rows = rows("analysis/extraction_ledger_2026_10_21/ledger_100.csv")
_p2_types = ("printed, table", "printed, text/caption", "derived", "plot-read")
_p2_locations = ("main text", "Supporting Information")
_p2_correct = lambda r: r['correct'] == 'True'
_p2_counts = {t: dict(n=sum(r['source_type'] == t for r in _p2_rows),
                       correct=sum(r['source_type'] == t and _p2_correct(r) for r in _p2_rows))
              for t in _p2_types}
_p2_loc_counts = {f"{t} | {loc}": dict(n=len(group), correct=sum(map(_p2_correct, group)))
                  for t in _p2_types for loc in _p2_locations
                  if (group := [r for r in _p2_rows if (r['source_type'], r['location']) == (t, loc)])}
_p2_papers = {r['doi'] for r in _p2_rows}
ok("P2 ledger: sample size, paper count, ten values per paper and accuracy recounted from CSV",
   len(_p2_rows) == _p2['values'] == 100 and len(_p2_papers) == _p2['papers'] == 10
   and sorted(int(r['id']) for r in _p2_rows) == list(range(1, 101))
   and all(sum(r['doi'] == doi for r in _p2_rows) == 10 for doi in _p2_papers)
   and all(r['correct'] in ('True', 'False') and r['location'] in _p2_locations for r in _p2_rows)
   and sum(map(_p2_correct, _p2_rows)) == _p2['correct'] == 98)
ok("P2 ledger: source-type counts and correct counts equal CSV recount",
   _p2_counts == _p2['by_source_type'] and all(r['source_type'] in _p2_types for r in _p2_rows))
ok("P2 ledger: source-type/location counts equal CSV recount",
   _p2_loc_counts == _p2['by_source_type_and_location'])
_p2_errors = [dict(id=int(r['id']), doi=r['doi'], note=r['note']) for r in _p2_rows if not _p2_correct(r)]
ok("P2 ledger: errors are values 40 and 99 and their evidence equals the summary",
   _p2_errors == _p2['errors'] and [r['id'] for r in _p2_errors] == [40, 99])
_p2_plot = {f"{source} | {field}": dict(n=int(row['n_extracted']), correct=int(row['n_correct_strict']))
            for (source, field), row in src.items()
            if source in ('plot', 'SI-plot') and field in ('X_CO2', 'S_MeOH', 'STY')}
_p2_pooled = {field: {key: sum(v[key] for k, v in _p2_plot.items() if k.endswith(' | ' + field))
                      for key in ('n', 'correct')} for field in ('X_CO2', 'S_MeOH', 'STY')}
ok("P2 plot-read: summary source counts equal the curated-comparison CSV",
   _p2_plot == _p2['plot_read_vs_curated']['by_source'])
ok("P2 plot-read: pooled counts recounted as X 185/229, S 73/207 and STY 18/151",
   _p2_pooled == _p2['plot_read_vs_curated']['pooled']
   and [(v['correct'], v['n']) for v in _p2_pooled.values()] == [(185, 229), (73, 207), (18, 151)])

# Parse complete table rows, so an unrelated occurrence cannot satisfy a missing/wrong cell.
_p2_raw_table = re.search(r"^### Supplementary Table 9 \|[^\n]*\n(.*?)(?=^### |\Z)", SIT, re.M | re.S)
_p2_table_rows = [[cell.strip().replace('**', '') for cell in line.strip().strip('|').split('|')]
                  for line in (_p2_raw_table.group(1).splitlines() if _p2_raw_table else [])
                  if line.lstrip().startswith('|')]
_p2_data_rows = _p2_table_rows[2:]
_p2_labels = ("Printed, table", "Printed, text or caption", "Derived from printed numbers", "Read off a plot")
for _type, _label in zip(_p2_types, _p2_labels):
    _counts = _p2['by_source_type'][_type]
    _locs = [_p2['by_source_type_and_location'].get(f"{_type} | {loc}", {'n': 0})['n']
             for loc in _p2_locations]
    _expected = [_label, *map(str, _locs),
                 f"{_counts['correct']} / {_counts['n']}" if _counts['n'] else '–',
                 f"{100 * _counts['correct'] / _counts['n']:.0f} %" if _counts['n'] else '–']
    ok(f"SI Table 9: {_label} cells equal P2 summary",
       [r for r in _p2_data_rows if r[0] == _label] == [_expected])
_p2_total_locs = [sum(v['n'] for k, v in _p2_loc_counts.items() if k.endswith(' | ' + loc))
                  for loc in _p2_locations]
ok("SI Table 9: total row equals P2 summary (98/100)",
   [r for r in _p2_data_rows if r[0] == 'Total'] ==
   [['Total', *map(str, _p2_total_locs), f"{_p2['correct']} / {_p2['values']}", f"{100 * _p2['correct'] / _p2['values']:.0f} %"]]
   and len(_p2_data_rows) == 8)
for _field, _label in (('X_CO2', 'CO₂ conversion'), ('S_MeOH', 'methanol selectivity'), ('STY', 'STY')):
    _counts = _p2['plot_read_vs_curated']['pooled'][_field]
    _label = f"Read off a plot, {_label} (against curated data)"
    ok(f"SI Table 9: pooled {_field} accuracy equals P2 summary",
       [r for r in _p2_data_rows if r[0] == _label] ==
       [[_label, '', '', f"{_counts['correct']} / {_counts['n']}", f"{100 * _counts['correct'] / _counts['n']:.0f} %"]])

tokens("P2 main Methods: 100 values, 98 correct and the two errors at the catalyst level", methods,
       f"A random sample of {_p2['values']} extracted values from {_p2['papers']} papers",
       f"Of these, {_p2['correct']} are correct",
       f"The {word(len(_p2_errors))} errors",
       "a conversion printed for a stability test and attached to a table entry of the same catalyst",
       "a methanol formation rate recorded as STY without the paper's name for it",
       "change no comparison at the catalyst level (Supplementary Table 9)")
_p2_method = supplementary_method('Adaptive Catalyst Screening Agent')
_p2_by = _p2['by_source_type']
# Derive the prose spelling from the summary count.
_p2_spelled_correct = {98: 'Ninety-eight'}.get(_p2['correct'], str(_p2['correct']))
claim_tokens("P2 SI: sample composition, 98 correct and both errors match the ledger",
    ("SI Note 2", s6, [f"{_p2['correct']} of {_p2['values']} sampled values are correct (Supplementary Table 9)"]),
    ("SI Methods", _p2_method, [
       f"sample of {_p2['values']} extracted values, ten from each of {_p2['papers']} papers",
       f"{_p2_by['printed, table']['n']} are printed in tables, {_p2_by['printed, text/caption']['n']} in the text or captions and {_p2_by['derived']['n']} are H₂/CO₂ ratios derived from printed feed compositions",
       "none is read off a plot" if _p2_by['plot-read']['n'] == 0 else f"{_p2_by['plot-read']['n']} are read off a plot",
       f"{_p2_spelled_correct} are correct", "One error is a CO₂ conversion printed for a stability test and attached to a table entry of the same catalyst",
       "the other a methanol formation rate recorded as STY without the paper's name for it",
       "Removing the first changes no comparison at the catalyst level",
       "The second converts to the same STY and changes no comparison"]))
_p2_effect = _p2['error_effect_frei_2019']['inlet_limited']
_p2_before, _p2_after = _p2_effect['as_extracted'], _p2_effect['corrected']
ok("P2 correction: 50 to 51 of 81 is one additional point-level disagreement",
   _p2_before['disagreements'] == pl6['disagreements'] == 50
   and _p2_before['groups'] == _p2_after['groups'] == pl6['groups'] == 81
   and _p2_after['disagreements'] == _p2_before['disagreements'] + 1 == 51
   and not _p2_before['group_disagrees'] and _p2_after['group_disagrees'])
tokens("P2 SI Methods: point-level effect equals the inlet-limited summary", _p2_method,
       f"adds one disagreement to the count at the point level for the loop with the inlet limit ({_p2_after['disagreements']} instead of {_p2_before['disagreements']} of {_p2_after['groups']})")


# Ota #99 is a metric-name error: convert the printed rate independently and
# compare both ledger/summary evidence and the actual pooled model input.
_p2_ota = _p2['error_effect_ota_2012']
_p2_ota_rows = [r for r in _p2_rows if int(r['id']) == 99]
_p2_ota_models = [r for r in rows("analysis/meoh_field_pooled_2026_10_15/pooled_candidates.csv")
                  if r['doi'] == '10.1016/j.jcat.2012.05.020' and r['entry'] == 'Table 2, PdMgAl']
_p2_ota_row = _p2_ota_rows[0] if len(_p2_ota_rows) == 1 else {}
_p2_ota_rate = re.fullmatch(r"([0-9.]+) µmol/min gcat", _p2_ota_row.get('extracted_value', ''))
_p2_ota_sty = (float(_p2_ota_rate[1]) * 1e-6 * 32.04 * 60) if _p2_ota_rate else math.nan
ok("P2 Ota #99: printed methanol rate converts to the pooled model STY without changing comparisons",
   _p2_ota_row.get('doi') == '10.1016/j.jcat.2012.05.020'
   and _p2_ota_row.get('experimental_entry') == 'Table 2, PdMgAl'
   and _p2_ota_row.get('field') == 'STY (printed)'
   and 'rate of methanol' in _p2_ota_row.get('precise_table_figure_location', '')
   and _p2_ota_row.get('correct') == 'False'
   and _p2_ota_rate is not None
   and float(_p2_ota_rate[1]) == _p2_ota['printed_rate_umol_per_g_min'] == 0.3
   and round(_p2_ota_sty, 6) == _p2_ota['sty_g_per_g_h'] == _p2_ota['model_sty'] == 0.000577
   and len(_p2_ota_models) == 1
   and round(float(_p2_ota_models[0]['STY']), 6) == _p2_ota['model_sty']
   and abs(float(_p2_ota_models[0]['STY']) - _p2_ota_sty) < 1e-6
   and _p2_ota['comparisons_changed'] == 0)

for _path, _raw in (("docs/MANUSCRIPT_MAIN_TEXT.md (body)", _body),
                    ("docs/SUPPLEMENTARY_INFORMATION.md", raw_si),
                    ("docs/MAIN_FIGURE_CAPTIONS.md", (ROOT / 'docs/MAIN_FIGURE_CAPTIONS.md').read_text(encoding='utf-8')),
                    ("figures/extended_data/ED_CAPTIONS.md", (ROOT / 'figures/extended_data/ED_CAPTIONS.md').read_text(encoding='utf-8')),
                    ("docs/SI_TABLES.md", SIT)):
    _hits = [f"{i}: {line.strip()}" for i, line in enumerate(_raw.splitlines(), 1)
             if re.search(r"\b(?:frozen|canonical|registered)\b", line, re.I)]
    ok(f"Reader-facing wording: no frozen/canonical/registered in {_path}", not _hits, ' | '.join(_hits))
_si_word_count = len(raw_si.split())
ok("SI compression: fewer than 10,000 whitespace-delimited words", _si_word_count < 10_000,
   f"{_si_word_count:,} words")

# ----- Reframed ammonia headline and added references (2026-10-21) --------------
# The screen's parity price and activity-only backward calculation define the claim.
_price_reduction = pc(1 - P_STAR / P_RU0)
_activity_multiple = f"{bw['Ru_activity_break_even_multiplier']:.0f}"
_results_heading = re.search(r"^## Results\s*\n+### ([^\n]+)", raw_text, re.M)
_heading_text = _results_heading.group(1) if _results_heading else ""
_measured_reduction = 100 * (1 - IR['bench_price_parity']['factor_vs_current'])
# 2026-10-22: Ru/C leads the ammonia story; the "over 90%" bound now lives in the Abstract.
_headline_bound = re.search(r"bulk Ru must cost over (\d+)% less", main_section_h2("Abstract"))
ok("NH3 Abstract: bulk-Ru 'over 90%' is below both source price reductions",
   "Ru leads in activity and loses on the price of its metal" == _heading_text
   and _headline_bound is not None
   and float(_headline_bound[1]) < 100 * (1 - P_STAR / P_RU0)
   and float(_headline_bound[1]) < _measured_reduction)
tokens("NH3 Abstract: parity requirements equal descriptor and measured sources",
       main_section_h2("Abstract"),
       "Ru must cost over 90% less to match iron",
       f"or become {IR['parity']:.0f}–{_activity_multiple} times more active",
       "far beyond what its scaling relation allows")
tokens("NH3 first Results section: parity requirements equal the price sweep and backward calculation",
       NH3_MAIN, f"{_price_reduction}% lower", f"{_activity_multiple}-fold activity gain")
tokens("NH3 first Results section: measured parity requirements equal their sources",
       NH3_MAIN, f"measured rate laws give {_measured_reduction:.0f}% or {IR['parity']:.0f}-fold")
tokens("MeOH main: inlet inert range equals SI Note 3 and stream-table species sums",
       m_field, f"loop designs carry {_cmn_rng} CO, methane and N₂ at the reactor inlet")

for _doi in ("10.1002/cite.201800026", "10.1002/cite.202200022", "10.3389/fenrg.2020.00005"):
    _number = reference_number("doi:" + _doi + ".")
    ok(f"References: added DOI {_doi} has one list entry and a main-body citation",
       _number is not None and _number in _cited(_body), f"resolved reference {_number}")

_review_ref = reference_number("10.1002/aesr.202000043")
ok("Extended Data 5: review reference follows its DOI after renumbering",
   _review_ref is not None and f"ref. {_review_ref}" in
   _caption("figures/extended_data/ED_CAPTIONS.md", "Extended Data Fig. 5"))

# ----- Catalyst-level inlet-limit scan (2026-10-21) -----------------------------
_CAT_SCAN = "analysis/meoh_catalyst_level_2026_10_19/"
_limit_scan = _j(_CAT_SCAN + "summary_limit_scan.json")
_raised_scan = _j(_CAT_SCAN + "summary_raised_limit_scan.json")
_no_limit = _j(_CAT_SCAN + "summary_no_limit.json")
_limits = ("4", "5", "6.86", "8", "10")
# Cross-check the independently costed laboratory rows against the pooled cost
# columns. Check each row separately so a disagreement identifies its limit.
for _limit in _limits:
    _lab = _raised_scan[_limit]['laboratory_conversion']
    _pooled_lab = _limit_scan[_limit]['catalyst_level']
    ok(f"MeOH catalyst scan: {_limit}% laboratory row agrees across both scans",
       all(_lab[k] == _pooled_lab[k] for k in ('changed', 'groups', 'gt5pct', 'papers_changed')))
for _name, _primary in (("laboratory_conversion", _cc), ("conversion_raised", _rcat)):
    _row = _raised_scan['6.86'][_name]
    ok(f"MeOH catalyst scan: 6.86% {_name} reproduces primary counts",
       _row['changed'] == _primary['changed']
       and _row['groups'] == _primary['groups_2plus_catalysts']
       and _row['gt5pct'] == _primary['gt5pct']
       and _row['papers_changed'] == _primary['papers_changed'])
_no_lab = _no_limit['laboratory_conversion']['cat_primary']
_no_raised = _no_limit['conversion_raised']['cost_f0.95']['cat_primary']
ok("MeOH catalyst scan: unlimited laboratory row reproduces no-limit summary",
   _limit_scan['none']['catalyst_level'] == {
       'changed': _no_lab['changed'], 'groups': _no_lab['groups_2plus_catalysts'],
       'gt5pct': _no_lab['gt5pct'], 'papers_changed': _no_lab['papers_changed']})
ok("MeOH no-limit point counts reproduce the pooled result and limit scan",
   _no_limit['point_level']['groups'] == pl5['groups'] == _limit_scan['none']['point_level']['groups']
   and _no_limit['point_level']['changed'] == pl5['disagreements'] == _limit_scan['none']['point_level']['changed']
   and _no_limit['point_level']['gt5pct'] == pl5['gt5pct'])
ok("MeOH no-limit catalyst denominators agree at laboratory and raised conversion",
   _no_lab['groups_2plus_catalysts'] == _no_raised['groups_2plus_catalysts'])
tokens("MeOH main: no-limit catalyst counts equal the no-limit summary", m_field,
       f"between catalysts in {_no_lab['changed']} of {_no_lab['groups_2plus_catalysts']} at laboratory conversion "
       f"and {_no_raised['changed']} with more catalyst loaded")
# A single local sentence binds all five ordered counts to their limits and
# denominator range; no number can pass by occurring elsewhere in the Note.
_scan_denominators = [r[n]['groups'] for r in _raised_scan.values()
                      for n in ('conversion_raised', 'laboratory_conversion')]
_scan_den_range = f"{min(_scan_denominators)}–{max(_scan_denominators)}"
for _name, _prefix, _tail in (
        ('conversion_raised', 'Between catalysts, with more catalyst loaded, the leaders differ in ',
         f" of {_scan_den_range} comparisons at limits of {_and(_limits)}%, and in {_no_raised['changed']} without a limit."),
        ('laboratory_conversion', 'At laboratory conversion the counts are ',
         f", and {_no_lab['changed']} without a limit.")):
    _counts = [_raised_scan[k][_name]['changed'] for k in _limits]
    tokens(f"MeOH SI Note 3: {_name} scan counts and no-limit count equal summaries",
           s8, _prefix + _and(_counts) + _tail)
# The main-text range uses only 5, 6.86, 8 and 10%, excluding the 4% sensitivity.
_industrial_limits = ("5", "6.86", "8", "10")
_ranges = {}
for _name in ('conversion_raised', 'laboratory_conversion'):
    _counts = [_raised_scan[k][_name]['changed'] for k in _industrial_limits]
    _ranges[_name] = f"{min(_counts)}–{max(_counts)}"
_industrial_groups = [_raised_scan[k][n]['groups'] for k in _industrial_limits
                      for n in ('conversion_raised', 'laboratory_conversion')]
tokens("MeOH main: 5–10% ranges are scan minima and maxima", m_field,
       f"Across inlet limits of {min(map(float, _industrial_limits)):g}–{max(map(float, _industrial_limits)):g}%, "
       f"the range of industrial loop designs, the leaders differ in {_ranges['conversion_raised']} of "
       f"{min(_industrial_groups)}–{max(_industrial_groups)} comparisons with more catalyst loaded "
       f"and in {_ranges['laboratory_conversion']} at laboratory conversion")
# Retain the revised semantic scope where the manuscript now defines the ranking.
claim_tokens("Abstract leader and Methods: catalyst inventory and measured-point scope",
    ("Abstract", main_section_h2("Abstract"), ["the catalyst with the highest space-time yield"]),
    ("main Methods", methods, ["over its measured operating points and the catalyst inventory a plant would choose"]))
for _scope, _claim in (("main Methods", methods),
                       ("Supplementary Methods", supplementary_method('Multiscale decision analysis'))):
    tokens(f"{_scope}: methanol optimum includes catalyst inventory", _claim,
           "over its measured operating points and the catalyst inventory a plant would choose")

# ----- Nature Chemical Engineering compressed format (2026-10-21) ---------------
# Whitespace-delimited words: retain citations and inline maths, exclude headings
# and display-equation lines. This reproduces the author's 144 / 3,471 counts.
_prose_lines = [line for line in _main_prose.splitlines()
                if not line.lstrip().startswith(("#", "$$"))]
_abstract_words = len(_abstract.split())
_main_words = len("\n".join(_prose_lines).split())
ok("NCE format: abstract at most 150 words", 0 < _abstract_words <= 150,
   f"{_abstract_words} words (limit 150)")
ok("NCE format: unheaded introduction, Results and Discussion at most 3,500 words",
   bool(_introduction.strip()) and not re.search(r"^## Introduction\b", _introduction, re.M)
   and 0 < _main_words <= 3500,
   f"{_main_words:,} words (limit 3,500)")
_main_body = raw_text.split("## Working references", 1)[0]
ok("NCE format: no main-text Table 1 display item",
   not re.search(r"\bTable\s+1\b|^\s*\|", _main_body, re.M))
# Remove Extended Data/Supplementary citations before counting main figures.
_main_citations = re.sub(r"(?:Extended Data|Supplementary)\s+(?:Figs?\.|Figures?)\s+[^;)\n]+",
                          "", _main_body)
_main_figures = set()
for _citation in re.findall(r"\b(?:Figs?\.|Figures?)\s+(\d+[a-z]?(?:\s*(?:[–−-]\s*\d+[a-z]?|,\s*(?:\d+[a-z]?|[a-z])))*)", _main_citations):
    for _part in _citation.split(","):
        _ends = list(map(int, re.findall(r"\d+", _part)))
        if _ends:
            _main_figures.update(range(_ends[0], _ends[-1] + 1))
# Methods may identify tables in a cited source ("Tables 1–6 of ref. 39").
# These are source locations, not display items of this manuscript.
_own_displays = re.sub(r"\bTables?\s+\d+(?:\s*[–-]\s*\d+)?\s+of\s+ref\.\s*\d+", "", _main_body)
_main_tables = re.findall(r"(?<!Supplementary )\bTables?\s+\d+", _own_displays)
ok("NCE format: at most six main-text displays, figures 1–6 and no table",
   _main_figures == set(range(1, 7)) and not _main_tables,
   f"figures {sorted(_main_figures)}; tables {_main_tables}")
_displays = re.findall(r"\$\$(.*?)\$\$", _main_body, re.S)
_equation_numbers = [re.search(r"\\qquad\s*\((\d+)\)\s*$", equation) for equation in _displays]
ok("NCE format: display equations numbered (1)–(3) in appearance order",
   len(_displays) == 3 and all(_equation_numbers)
   and [int(m.group(1)) for m in _equation_numbers] == [1, 2, 3],
   f"numbers {[m.group(1) if m else 'missing' for m in _equation_numbers]}")

tokens("Main text: compressed promoter activity range", m_bw,
       f"Promotion raises Ru activity {min(float(r['factor_high']) for r in _prom):.0f}- to more than {max(float(r['factor_high']) for r in _prom):.0f}-fold")


# ----- Items A-D of the 2026-10-22 revision -------------------------------------
# D: ammonia field comparisons on measured rate laws (analysis/nh3_field_measured_kinetics_2026_10_22).
_md = _j("analysis/nh3_field_measured_kinetics_2026_10_22/summary.json")
_mdp, _mde = _md["primary_measured"], _md["entries"]
ok("D gates: frozen 12/44, Keestra Fe 15.307473, Rossetti zero at equilibrium",
   all(v["ok"] for v in _md["gates"].values()) and (_md["frozen_descriptor"]["groups"], _md["frozen_descriptor"]["top1_mismatch_groups"]) == (NPL["groups"], NPL["mismatch"]))
claim_tokens("D: measured-law basis in SI Note 4 equals its source",
    ("SI Note 4", s9, [f"Of the {_mde['total']} entries, {_mde['lab_outside_fitted_range']} were measured outside",
                       f"{_mde['infeasible_primary']} entries need more than the 90 m³ bed",
                       f"In the {_mdp['groups']} comparisons that keep two buildable entries the leaders differ in {_mdp['top1_mismatch_groups']}, all above 5%",
                       f"gives {_md['g_integral_calibration']['top1_mismatch_groups']} of {_md['g_integral_calibration']['groups']}",
                       f"gives {_md['a_ru_cholewa_as_printed']['top1_mismatch_groups']} of {_md['a_ru_cholewa_as_printed']['groups']}",
                       f"{_md['gates']['cholewa_as_printed_H2N2_ratio_info']['ratio_15_over_30']:.2f}-fold rate gain"]))
ok("D: >5 % count equals the mismatch count on the measured basis", _mdp["regret_gt5pct_groups"] == _mdp["top1_mismatch_groups"])
ok("D: integral, ranked-last and anchored variants agree",
   len({(_md[k]["top1_mismatch_groups"], _md[k]["groups"]) for k in ("f_infeasible_ranked_last", "g_integral_calibration", "h_anchored_on_fused_reference")}) == 1)
# A+B: NH3-FINAL-1.3 structural check (analysis/nh3_final_1_3_2026_10_22).
_r13 = _j("analysis/nh3_final_1_3_2026_10_22/results.json")
_d13, _m13, _g13 = _r13["descriptor"]["1.3"], _r13["measured"]["1.3"], _r13["gates"]["G1_vle_holdout"]
_d12 = _r13["descriptor"]["1.2_direct"]
ok("1.3: 1.2 recomputed on the same path equals the canonical anchors",
   all(abs(_d12["metals"][m]["cost"] - det["metals"][m]["feasible"]["total_cost"]) < 5e-3 for m in ("Fe", "Ru", "Os"))
   and abs(_r13["measured"]["1.2"]["breakeven_own_optima"]["rate"] - _bes["benchmark_owned"]) < 1e-6)
claim_tokens("1.3: SI Note 7 and main text equal results.json",
    ("SI Note 7", s2_full, [f"within {100 * _g13[0]['dev_1_3']:.1f}% and {100 * _g13[1]['dev_1_3']:.1f}%",
                            f"Fe, Ru and Os cost {_d13['metals']['Fe']['cost']:.2f}, {_d13['metals']['Ru']['cost']:.2f} and {_d13['metals']['Os']['cost']:.2f} US dollars per tonne",
                            f"Fe {_d13['Ru_minus_Fe']:.2f})",
                            f"Ru matches Fe at {_d13['Ru_price_parity_USD_kg']:.0f} US dollars per kilogram or with an {_d13['Ru_activity_multiple_for_parity']:.0f}-fold activity gain",
                            f"bulk Ru needs {_m13['bulk_Ru_activity_parity']:.1f}-fold or {_m13['bulk_Ru_price_parity']['price_USD_kg']:,.0f} US dollars per kilogram",
                            f"Ru/C is {-_m13['own_optima_2.10']['gap']:.2f} and {-_m13['KAAP_2.10']['gap']:.2f} US dollars per tonne cheaper",
                            f"break-even {100 * _m13['breakeven_own_optima']['rate']:.2f}% and {100 * _m13['breakeven_KAAP']['rate']:.2f}% per year"]),
    ("main text", m_feru, [f"the gap stays at {_d13['Ru_minus_Fe']:.2f} US dollars per tonne"]))
ok("1.3: both separator hold-outs within 7 % (main-text wording)", all(abs(g["dev_1_3"]) < 0.07 for g in _g13))

# ----- Report -----------------------------------------------------------------
failed = [(label, detail) for label, passed, detail in checks if not passed]
for label, passed, detail in checks:
    print(("PASS " if passed else "FAIL ") + label + (f" | {detail}" if detail else ""))
print(f"{len(checks)} checks, {len(failed)} failed")
raise SystemExit(1 if failed else 0)
