#!/usr/bin/env python3
"""Read-only, group-aligned audit of the frozen methanol and ammonia results.

An intersection of separate treatments is NOT a joint catalyst-loading/purge result.
Uses only committed CSV files; outputs go to a separate, disposable directory.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ME = Path("analysis/meoh_literature_inversion_2026_10_05")
BANSODE = "10.1039/c2cy20604h"
FILES = {
    "S5": "group_metrics.csv",
    "extended": "group_metrics_purge_extended.csv",
    "inlet_4p92": "group_metrics_purge_published_min.csv",
    "inlet_6p86": "group_metrics_purge_anchor.csv",
    "inlet_10p25": "group_metrics_purge_published_max.csv",
}
INLETS = ("inlet_4p92", "inlet_6p86", "inlet_10p25")


def read(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def keyed(rows, origin):
    answer = {}
    for row in rows:
        key = row["group"]
        if key in answer:
            raise ValueError(f"Duplicate group {key} in {origin}")
        answer[key] = row
    return answer


def mismatch(row):
    return row["top1_mismatch"].casefold() == "true"


def material(row):
    return mismatch(row) and float(row["regret"]) > 0.05


def audit(root: Path, output: Path):
    me = root / ME
    tables = {key: keyed(read(me / filename), key) for key, filename in FILES.items()}
    conversion = (r for r in read(me / "conversion_sensitivity_groups.csv")
                  if r["mode"] == "printed" and r["cost_col"] == "cost_f0.95")
    tables["inventory_f0p95"] = keyed(conversion, "inventory_f0p95")
    groups = set(tables["S5"])
    for name, rows in tables.items():
        if set(rows) != groups:
            raise AssertionError(f"{name} has a different comparison cohort")
        for g in groups:
            if rows[g]["doi"] != tables["S5"][g]["doi"]:
                raise AssertionError(f"{name} has a different DOI for {g}")
            if rows[g]["upstream_winner"] != tables["S5"][g]["upstream_winner"]:
                raise AssertionError(f"{name} has a different upstream leader for {g}")

    cand = keyed(
        ({**r, "group": r["group"] + "\x1f" + r["catalyst"]}
         for r in read(me / "literature_candidates.csv")),
        "literature_candidates.csv")
    out = []
    for group in sorted(groups):
        rows = {key: table[group] for key, table in tables.items()}
        ref = rows["S5"]
        anchor = rows["inlet_6p86"]
        up = cand[group + "\x1f" + ref["upstream_winner"]]
        down = cand[group + "\x1f" + anchor["economic_winner"]]
        complete = all(item[column].casefold() == "true"
                       for item in (up, down)
                       for column in ("sty_printed", "co_printed", "ch4_printed"))
        robust = all(material(rows[k]) for k in INLETS)
        same_temp = robust and all(rows[k]["kind"] == "other catalyst, same temperature" for k in INLETS)
        o = {
            "group": group, "doi": ref["doi"],
            "robust_inlet_gt5": robust,
            "sameT_other_catalyst_robust": same_temp,
            "complete_printed_three_fields_both_leaders_at_anchor": complete,
            "stable_economic_leader_all_inlets": (
                len({rows[k]["economic_winner"] for k in INLETS}) == 1),
        }
        for tag, r in rows.items():
            o[tag + "_mismatch"] = mismatch(r)
            o[tag + "_regret"] = float(r["regret"])
            o[tag + "_kind"] = r.get("kind", "")
            o[tag + "_economic_leader"] = r["economic_winner"]
        out.append(o)

    robust = [r for r in out if r["robust_inlet_gt5"]]
    same = [r for r in robust if r["sameT_other_catalyst_robust"]]
    without = [r for r in robust if r["doi"] != BANSODE]
    nh3 = read(root / "analysis/nh3_field_2026_10_06/group_metrics_printed.csv")
    nh3_bad = [r for r in nh3 if mismatch(r)]
    nm = [r for r in nh3_bad if r["mismatch_kind"] == "different metal"]
    summary = {
        "caution": "Post-hoc intersection of independently computed sensitivities; not joint m-p optimization.",
        "methanol": {
            "groups": len(out), "papers": len({r["doi"] for r in out}),
            "scenarios": {name: {
                "mismatch": sum(mismatch(row) for row in table.values()),
                "regret_gt5": sum(material(row) for row in table.values()),
                "regret_gt5_without_bansode": sum(
                    material(row) and row["doi"] != BANSODE for row in table.values())
            } for name, table in tables.items()},
            "inlet_intersection": {
                "regret_gt5": len(robust), "papers": len({r["doi"] for r in robust}),
                "regret_gt5_without_bansode": len(without),
                "papers_without_bansode": len({r["doi"] for r in without}),
                "same_temperature_other_catalyst": len(same),
                "same_temperature_other_catalyst_papers": len({r["doi"] for r in same}),
                "fully_printed_leader_pairs_at_anchor": sum(
                    r["complete_printed_three_fields_both_leaders_at_anchor"] for r in same),
                "sameT_dois": sorted(r["doi"] for r in same),
            }
        },
        "ammonia": {
            "groups": len(nh3), "papers": len({r["doi"] for r in nh3}),
            "mismatch": len(nh3_bad),
            "different_metal": len(nm), "different_metal_papers": len({r["doi"] for r in nm}),
            "kinds": dict(Counter(r["mismatch_kind"] for r in nh3_bad)),
        },
    }
    output.mkdir(parents=True, exist_ok=True)
    with (output / "cross_scenario_groups.csv").open("w", newline="", encoding="utf-8") as fd:
        writer = csv.DictWriter(fd, fieldnames=list(out[0]))
        writer.writeheader()
        writer.writerows(out)
    (output / "audit_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return summary


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--repo", type=Path, default=ROOT)
    p.add_argument("--output", type=Path, default=ROOT / "analysis/field_robustness_2026_10_12/output")
    p.add_argument("--check-frozen", action="store_true")
    a = p.parse_args()
    s = audit(a.repo, a.output)
    print(json.dumps(s, indent=2, ensure_ascii=False))
    if a.check_frozen:
        m, h = s["methanol"], s["ammonia"]
        assert (m["groups"], m["scenarios"]["S5"]["mismatch"],
                m["scenarios"]["extended"]["mismatch"]) == (40, 15, 14)
        z = m["inlet_intersection"]
        assert (z["regret_gt5"], z["regret_gt5_without_bansode"],
                z["same_temperature_other_catalyst"],
                z["same_temperature_other_catalyst_papers"],
                z["fully_printed_leader_pairs_at_anchor"]) == (16, 12, 7, 7, 2)
        assert (h["groups"], h["mismatch"], h["different_metal"],
                h["different_metal_papers"]) == (33, 7, 3, 2)


if __name__ == "__main__":
    main()
