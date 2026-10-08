"""Audit printed-value provenance of methanol product selectivities.

Independent, read-only source audit. It never recomputes economic costs,
alters candidate records, or changes the selected thermodynamic treatment.

Why: the printed-only cohort requires printed X_CO2 and S_MeOH, but missing
CO/CH4 selectivities can still be completed via the model's carbon closure.
In addition, when both CO and CH4 are printed, the closure treats CO as the
remainder instead of copying its reported value.

Source records are read from the *exact pinned extraction commit* used by
the existing S5 verification code. Model inputs and group decisions are read
from the already committed verification CSV outputs.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import math
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
VERIFY = REPO / "analysis" / "verify_2026_10_08"
SOURCE_COMMIT = "86dcd76218e2fd5218d6da74e8f6092c0f1c2f3c"
SOURCE_PATH = "agent/extraction/out/records_normalized.csv"
PRINTED_Q = {"=", "<", "<="}
PLOT_SOURCES = {"plot", "SI-plot"}
COST_VARIANTS = ("lab", "cost_f0.95")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def read_pinned_records() -> list[dict[str, str]]:
    output = subprocess.run(
        ["git", "-C", str(REPO), "show", f"{SOURCE_COMMIT}:{SOURCE_PATH}"],
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        encoding="utf-8",
    ).stdout
    return list(csv.DictReader(io.StringIO(output)))


def number(s: str) -> float | None:
    if s is None or str(s).strip() == "":
        return None
    try:
        val = float(s)
    except (ValueError, TypeError):
        return None
    return val if math.isfinite(val) else None


def printed(record: dict[str, str], key: str) -> bool:
    value = number(record.get(key + "_pct", ""))
    qualifier = record.get(key + "_q", "")
    source = record.get(key + "_src", "")
    return value is not None and qualifier in PRINTED_Q and source not in PLOT_SOURCES


def approx_equal(a: str, b: str, eps: float = 1e-5) -> bool:
    aa, bb = number(a), number(b)
    return aa is not None and bb is not None and abs(aa - bb) <= eps


def index_records(records: list[dict[str, str]]) -> dict[tuple[str, str], list[dict[str, str]]]:
    idx: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for r in records:
        idx[(r.get("doi", ""), r.get("entry_label", ""))].append(r)
    return idx


def match_record(point: dict[str, str],
                 idx: dict[tuple[str, str], list[dict[str, str]]]
                 ) -> tuple[dict[str, str] | None, str]:
    key = (point.get("doi", ""), point.get("entry", ""))
    matches = idx.get(key, [])
    if len(matches) == 1:
        return matches[0], "unique"
    if not matches:
        return None, "not_found"

    # Multiple entries may share a manuscript label. Do not choose arbitrarily.
    label = point.get("catalyst", "")
    matched = [r for r in matches
               if label == (r.get("catalyst_name", "") + " [" + r.get("entry_label", "") + "]")
               and approx_equal(point.get("T_C", ""), str((number(r.get("T_K", "")) or -999) - 273.15), 0.06)
               and approx_equal(point.get("P_bar", ""), r.get("P_bar", ""), 0.06)]
    if len(matched) == 1:
        return matched[0], "disambiguated"
    return None, "ambiguous"


def candidate_report(point: dict[str, str],
                     record: dict[str, str] | None, match_status: str) -> dict:
    result = {
        "doi": point.get("doi", ""), "entry": point.get("entry", ""),
        "group": point.get("group", ""), "catalyst": point.get("catalyst", ""),
        "T_C": point.get("T_C", ""), "source_match": match_status,
        "has_printed_X": False, "has_printed_MeOH": False,
        "has_printed_CO": False, "has_printed_CH4": False,
        "missing_CO": False, "missing_CH4": False,
        "modeled_CO_pct": 100 * float(point.get("SCO") or 0),
        "modeled_CH4_pct": 100 * float(point.get("SCH4") or 0),
        "reported_CO_pct": "", "reported_CH4_pct": "",
        "CO_closed_vs_reported_delta_pp": "",
        "CO_delta_gt1pp": False, "CO_delta_gt5pp": False,
        "qualifier_CO": "", "qualifier_CH4": "",
        "source_completeness": "unresolved",
        "unreported_carbon_category": "",
    }
    if record is None:
        return result

    for field in ("X_CO2", "S_MeOH", "S_CO", "S_CH4"):
        name = {"X_CO2": "X", "S_MeOH": "MeOH",
                "S_CO": "CO", "S_CH4": "CH4"}[field]
        result["has_printed_" + name] = printed(record, field)
    co, ch4 = result["has_printed_CO"], result["has_printed_CH4"]
    result["missing_CO"], result["missing_CH4"] = not co, not ch4
    result["qualifier_CO"] = record.get("S_CO_q", "")
    result["qualifier_CH4"] = record.get("S_CH4_q", "")
    result["source_completeness"] = (
        "all_three_selectivities_printed" if co and ch4
        else "MeOH_and_CO_printed" if co
        else "MeOH_and_CH4_printed" if ch4
        else "only_MeOH_printed"
    )
    result["unreported_carbon_category"] = (
        "imputed_methane_from_reported_CO" if co and not ch4
        else "imputed_CO_from_reported_CH4" if ch4 and not co
        else "no_other_product_selectivity_printed" if not co and not ch4
        else ""
    )
    cval, mval = number(record.get("S_CO_pct", "")), number(record.get("S_CH4_pct", ""))
    result["reported_CO_pct"] = cval if cval is not None else ""
    result["reported_CH4_pct"] = mval if mval is not None else ""
    # "<" and "<=" are upper bounds, not equalities; cannot infer a numerical
    # discrepancy from the reported bound. The source processing uses 0 for "<".
    if co and record.get("S_CO_q") == "=":
        delta = result["modeled_CO_pct"] - cval
        result["CO_closed_vs_reported_delta_pp"] = round(delta, 8)
        result["CO_delta_gt1pp"] = abs(delta) > 1.0 + 1e-6
        result["CO_delta_gt5pp"] = abs(delta) > 5.0 + 1e-6
    return result


def audit(points: list[dict[str, str]], groups: list[dict[str, str]],
          records: list[dict[str, str]], base: str = "thermo",
          mode: str = "printed") -> tuple[dict, list[dict], list[dict]]:
    idx = index_records(records)
    selected = [p for p in points if p.get("base") == base and p.get("mode") == mode]
    candidates: list[dict] = []
    by_label: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for p in selected:
        record, status = match_record(p, idx)
        result = candidate_report(p, record, status)
        candidates.append(result)
        by_label[(p.get("group", ""), p.get("catalyst", ""))].append(result)

    by_group: dict[str, list[dict]] = defaultdict(list)
    for p in selected:
        by_group[p.get("group", "")].append(p)
    eligible = {k for k, v in by_group.items() if len(v) >= 2}

    group_results: list[dict] = []
    scenario: dict[str, dict] = {}
    for cost_col in COST_VARIANTS:
        members = [g for g in groups if g.get("base") == base and
                   g.get("mode") == mode and g.get("cost_col") == cost_col]
        counts = Counter()
        errors: list[str] = []
        if {g["group"] for g in members} != eligible:
            errors.append("Group sets differ between candidate points and recorded leaderboards")
        for g in members:
            mismatch = g.get("mismatch", "").lower() == "true"
            regret = float(g["regret"])
            leaders = []
            for k in ("sty_leader", "cost_leader"):
                hits = by_label.get((g["group"], g.get(k, "")), [])
                if len(hits) != 1:
                    errors.append(f"Winner source join ambiguous: {g['group']} {k}, matches={len(hits)}")
                leaders.append(hits[0] if len(hits) == 1 else None)

            unresolved = any(x is None or x["source_match"] in ("not_found", "ambiguous")
                             for x in leaders)
            missing_species = any(x and (x["missing_CO"] or x["missing_CH4"])
                                  for x in leaders)
            co_reassigned = any(x and x["CO_delta_gt5pp"] for x in leaders)
            record = {
                "cost_col": cost_col, "doi": g.get("doi", ""),
                "group": g["group"], "mismatch": mismatch, "regret": regret,
                "source_unresolved": unresolved,
                "either_leader_missing_CO_or_CH4": missing_species,
                "either_leader_reported_CO_shift_gt5pp": co_reassigned,
                "either_leader_has_closure_assumption": missing_species or co_reassigned,
                "sty_leader_source_completeness": (
                    leaders[0]["source_completeness"] if leaders[0] else "unresolved"),
                "cost_leader_source_completeness": (
                    leaders[1]["source_completeness"] if leaders[1] else "unresolved"),
            }
            group_results.append(record)
            counts["groups"] += 1
            if mismatch:
                counts["mismatches"] += 1
                counts["mismatches_gt5pct"] += int(regret > 0.05)
                counts["mismatch_winner_missing_CO_or_CH4"] += int(missing_species)
                counts["mismatch_winner_reported_CO_shift_gt5pp"] += int(co_reassigned)
                counts["mismatch_winner_either_closure"] += int(missing_species or co_reassigned)
                counts["gt5pct_winner_either_closure"] += int(regret > 0.05 and
                                                             (missing_species or co_reassigned))
            counts["source_unresolved_groups"] += int(unresolved)
        scenario[cost_col] = dict(counts, errors=errors)

    c = Counter()
    for x in candidates:
        c["candidates"] += 1
        c["source_unique"] += int(x["source_match"] in ("unique", "disambiguated"))
        c["missing_CO"] += int(x["missing_CO"])
        c["missing_CH4"] += int(x["missing_CH4"])
        c["missing_either"] += int(x["missing_CO"] or x["missing_CH4"])
        c["both_CO_CH4_printed"] += int(x["has_printed_CO"] and x["has_printed_CH4"])
        c["reported_CO_closed_delta_gt1pp"] += int(x["CO_delta_gt1pp"])
        c["reported_CO_closed_delta_gt5pp"] += int(x["CO_delta_gt5pp"])
        c["printed_X_and_MeOH"] += int(x["has_printed_X"] and x["has_printed_MeOH"])
        c["source_unresolved"] += int(x["source_match"] in ("not_found", "ambiguous"))
    return {
        "status": "REVIEW_ONLY_NOT_FROZEN",
        "base": base, "mode": mode,
        "source_commit": SOURCE_COMMIT, "candidates": dict(c),
        "scenario": scenario,
        "scientific_scope": "provenance of printed component values and model-imputed selectivities; no reranking",
    }, candidates, group_results


def write_csv(path: Path, records: list[dict]) -> None:
    if not records:
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0].keys()))
        writer.writeheader()
        writer.writerows(records)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--points", type=Path,
                        default=VERIFY / "conversion_sensitivity_points.csv")
    parser.add_argument("--groups", type=Path,
                        default=VERIFY / "conversion_sensitivity_groups.csv")
    parser.add_argument("--records", type=Path, default=None,
                        help="Optional original records CSV; otherwise read pinned git-show source")
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--base", choices=("thermo", "orig"), default="thermo")
    parser.add_argument("--mode", choices=("printed", "all"), default="printed")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    originals = read_csv(args.records) if args.records else read_pinned_records()
    summary, candidates, groups = audit(
        read_csv(args.points), read_csv(args.groups), originals,
        base=args.base, mode=args.mode)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "selectivity_source_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_csv(args.out_dir / "selectivity_source_candidates.csv", candidates)
    write_csv(args.out_dir / "selectivity_source_groups.csv", groups)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    errors = [e for x in summary["scenario"].values() for e in x["errors"]]
    if args.strict and (errors or summary["candidates"]["source_unresolved"] > 0):
        print("Unresolved entries need inspection; not a model failure.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
