#!/usr/bin/env python3
"""Read-only replay of manuscript-level DISCOVER V1 / C1 headline endpoints.

This script deliberately imports the original frozen DISCOVER_SCORER_V1.py from the
vendored provenance bundle and applies its score_trace() function to the original
committed traces.  It does not call an LLM, modify a frozen file, regenerate a trace,
or substitute a modern scorer.

The purpose is narrower than the provenance validator:
  provenance validator -> are these the exact bytes that were run?
  this replay           -> do those exact scorer bytes recover the paper's headline
                           decision endpoints from those exact trace bytes?

The primary complete-decision endpoint is whatever the frozen scorer implements.  In
DISCOVER V1 that is winner_correct AND pair_decision_correct AND
reachability_correct.  Numerical recovery of the BACKWARD parity multiplier is checked
separately, using the tolerances fixed in the original analysis code:
  * V1 cross-model "exact" break-even: relative error <= 1% (BE_TOL = 0.01)
  * C1 canonical backward target: relative error < 1e-6 (the C1 audit convention)
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "provenance" / "discover_v1" / "source_harness"
SCORER_PATH = BUNDLE / "DISCOVER_SCORER_V1.py"
OUT = ROOT / "artifacts" / "discover_v1_scorer_replay"

SCORER_SHA256 = "406b0f53be51b49596dc45e086408912dfccfecea316800f5ced3d5f7df1c3ae"
STRONG_MODEL = "gpt-5.5-2026-04-23"
MINI_MODEL = "gpt-5.4-mini-2026-03-17"
NANO_MODEL = "gpt-5.4-nano-2026-03-17"

# Manuscript-level closed-book V1 headline: 35 anonymous policy-E runs per tier.
CROSS_MODEL_ANCHORS = {
    "nano": {"model": NANO_MODEL, "n": 35, "complete": 6},
    "mini": {"model": MINI_MODEL, "n": 35, "complete": 15},
    "strong": {"model": STRONG_MODEL, "n": 35, "complete": 35, "break_even_exact": 34},
}

# Canonical C1 / extension primary-endpoint cells.  These are sample-size aware: the
# 200-CU and 250-CU cells have n=8 and n=9 rather than being described as n=20.
C1_COMPLETE_ANCHORS = {
    50: (20, 13),
    75: (20, 20),
    100: (20, 19),
    125: (20, 20),
    150: (20, 20),
    175: (20, 19),
    200: (8, 8),
    225: (20, 20),
    250: (9, 9),
    5000: (20, 20),  # non-binding-allowance control, reported separately in the manuscript
}

# C1 scored canonical backward target.  The frozen final_answer convention reports the
# FIRST decision-pair BACKWARD record; the C1 audit calls it canonical when rel. error <1e-6.
C1_BACKWARD_ANCHORS = {
    50: (20, 2),
    75: (20, 9),
    100: (20, 9),
    125: (20, 11),
    150: (20, 11),
    175: (20, 15),
    225: (20, 20),
}

V1_BE_TOL = 0.01
C1_CANONICAL_BE_TOL = 1e-6


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_frozen_scorer():
    if not SCORER_PATH.is_file():
        raise SystemExit(f"frozen scorer absent: {SCORER_PATH}")
    actual = sha256(SCORER_PATH)
    if actual != SCORER_SHA256:
        raise SystemExit(f"frozen scorer SHA mismatch: expected {SCORER_SHA256}, actual {actual}")
    spec = importlib.util.spec_from_file_location("DISCOVER_SCORER_V1_replay", SCORER_PATH)
    if spec is None or spec.loader is None:
        raise SystemExit("could not create import specification for frozen scorer")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def response_model(trace: dict, fallback: str | None = None) -> str | None:
    meta = trace.get("metadata") or {}
    return meta.get("response_model") or fallback


def replay_policy_e_anonymous(scorer, root: Path, expected_model: str | None = None) -> list[dict]:
    if not root.is_dir():
        raise SystemExit(f"trace root absent: {root}")
    rows: list[dict] = []
    for path in sorted(root.rglob("trace.json")):
        # Cheap pre-filter before invoking the frozen scorer.  Scoring itself is always done
        # by the frozen scorer, not by reimplementing its endpoint here.
        trace = json.loads(path.read_text(encoding="utf-8"))
        if "_smoke" in str(path):
            continue
        if trace.get("policy") != "E_llm_agent":
            continue
        if trace.get("task_variant", "named") != "anonymous":
            continue
        if expected_model is not None:
            mdl = response_model(trace, expected_model)
            if mdl != expected_model:
                continue
        row = scorer.score_trace(path)
        row["source_path"] = path.relative_to(BUNDLE).as_posix()
        rows.append(row)
    return rows


def fail_if(label: str, actual, expected, failures: list[str]) -> None:
    if actual != expected:
        failures.append(f"{label}: expected {expected!r}, got {actual!r}")


def cross_model_replay(scorer, failures: list[str]) -> dict:
    roots = {
        "nano": BUNDLE / "DISCOVER_CROSS_MODEL_V1" / "gpt-5.4-nano" / "traces" / "anonymous",
        "mini": BUNDLE / "DISCOVER_CROSS_MODEL_V1" / "gpt-5.4-mini" / "traces" / "anonymous",
        "strong": BUNDLE / "DISCOVER_FORMAL_RUNS_V1" / "traces" / "anonymous",
    }
    out = {}
    for tier, anchor in CROSS_MODEL_ANCHORS.items():
        rows = replay_policy_e_anonymous(scorer, roots[tier], anchor["model"])
        n = len(rows)
        complete = sum(bool(r["full_decision_correct"]) for r in rows)
        be_reported = sum(r["break_even_rel_error"] is not None for r in rows)
        be_exact = sum(
            r["break_even_rel_error"] is not None and r["break_even_rel_error"] <= V1_BE_TOL
            for r in rows
        )
        fail_if(f"cross-model {tier} n", n, anchor["n"], failures)
        fail_if(f"cross-model {tier} complete", complete, anchor["complete"], failures)
        if "break_even_exact" in anchor:
            fail_if(f"cross-model {tier} break-even exact", be_exact, anchor["break_even_exact"], failures)
        out[tier] = {
            "model": anchor["model"],
            "n": n,
            "complete": complete,
            "break_even_reported": be_reported,
            "break_even_exact_1pct": be_exact,
        }
    return out


def c1_replay(scorer, failures: list[str]) -> dict:
    root = (
        BUNDLE
        / "DISCOVER_BOUNDARY_C1"
        / "runs"
        / STRONG_MODEL
        / "traces"
        / "anonymous"
    )
    rows = replay_policy_e_anonymous(scorer, root, STRONG_MODEL)
    by_budget: dict[int, list[dict]] = defaultdict(list)
    for r in rows:
        b = int(round(float(r["budget_CU"])))
        by_budget[b].append(r)

    complete_summary = {}
    for budget, (expected_n, expected_complete) in C1_COMPLETE_ANCHORS.items():
        rs = by_budget.get(budget, [])
        actual_n = len(rs)
        actual_complete = sum(bool(r["full_decision_correct"]) for r in rs)
        fail_if(f"C1 {budget} CU n", actual_n, expected_n, failures)
        fail_if(f"C1 {budget} CU complete", actual_complete, expected_complete, failures)
        complete_summary[str(budget)] = {"n": actual_n, "complete": actual_complete}

    backward_summary = {}
    for budget, (expected_n, expected_canonical) in C1_BACKWARD_ANCHORS.items():
        rs = by_budget.get(budget, [])
        actual_n = len(rs)
        actual_canonical = sum(
            r["break_even_rel_error"] is not None
            and r["break_even_rel_error"] < C1_CANONICAL_BE_TOL
            for r in rs
        )
        fail_if(f"C1 {budget} CU backward n", actual_n, expected_n, failures)
        fail_if(f"C1 {budget} CU canonical backward", actual_canonical, expected_canonical, failures)
        backward_summary[str(budget)] = {"n": actual_n, "canonical_backward": actual_canonical}

    # Threshold statements are derived from the replayed, explicitly tested cells rather
    # than copied from prose.
    stable_complete_budgets = [
        b for b, vals in sorted(complete_summary.items(), key=lambda kv: int(kv[0]))
        if vals["n"] == 20 and vals["complete"] == 20
    ]
    canonical_target_budgets = [
        b for b, vals in sorted(backward_summary.items(), key=lambda kv: int(kv[0]))
        if vals["n"] == 20 and vals["canonical_backward"] == 20
    ]
    lowest_stable_complete = int(stable_complete_budgets[0]) if stable_complete_budgets else None
    lowest_canonical_target = int(canonical_target_budgets[0]) if canonical_target_budgets else None
    fail_if("lowest tested stable complete-decision budget", lowest_stable_complete, 75, failures)
    fail_if("lowest tested 20/20 canonical-target budget", lowest_canonical_target, 225, failures)

    return {
        "scored_trace_count": len(rows),
        "complete_by_budget": complete_summary,
        "canonical_backward_by_budget": backward_summary,
        "lowest_tested_stable_complete_budget_CU": lowest_stable_complete,
        "lowest_tested_20_of_20_canonical_backward_budget_CU": lowest_canonical_target,
    }


def write_report(report: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "replay.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    cm = report["cross_model"]
    c1 = report["c1"]
    lines = [
        "# DISCOVER V1 frozen-scorer headline replay",
        "",
        f"Status: **{report['status']}**",
        "",
        f"Checked at: `{report['timestamp_utc']}`",
        "",
        "Read-only replay. No LLM was called, no trace was generated, and no frozen file was modified.",
        "",
        "## Frozen scorer",
        "",
        f"- SHA-256: `{report['scorer_sha256']}`",
        "- primary endpoint is evaluated by the original `DISCOVER_SCORER_V1.score_trace()`",
        "",
        "## Cross-model anonymous closed-book replay",
        "",
        "| tier | n | complete decision | break-even exact within 1% |",
        "|---|---:|---:|---:|",
    ]
    for tier in ("nano", "mini", "strong"):
        r = cm[tier]
        lines.append(f"| {tier} | {r['n']} | {r['complete']}/{r['n']} | {r['break_even_exact_1pct']}/{r['n']} |")
    lines += [
        "",
        "## Strong-tier C1 / extension complete-decision replay",
        "",
        "| budget (CU) | n | complete decision |",
        "|---:|---:|---:|",
    ]
    for b in sorted(c1["complete_by_budget"], key=int):
        r = c1["complete_by_budget"][b]
        lines.append(f"| {b} | {r['n']} | {r['complete']}/{r['n']} |")
    lines += [
        "",
        "## Canonical BACKWARD-target replay",
        "",
        "The C1 convention scores the first decision-pair BACKWARD record carried by the frozen final answer as canonical when relative error is < 1e-6.",
        "",
        "| budget (CU) | n | canonical target |",
        "|---:|---:|---:|",
    ]
    for b in sorted(c1["canonical_backward_by_budget"], key=int):
        r = c1["canonical_backward_by_budget"][b]
        lines.append(f"| {b} | {r['n']} | {r['canonical_backward']}/{r['n']} |")
    lines += [
        "",
        "## Recovered thresholds",
        "",
        f"- lowest tested stable 20/20 complete-decision budget: **{c1['lowest_tested_stable_complete_budget_CU']} CU**",
        f"- lowest tested 20/20 canonical BACKWARD-target budget: **{c1['lowest_tested_20_of_20_canonical_backward_budget_CU']} CU**",
    ]
    if report["failures"]:
        lines += ["", "## Mismatches", ""] + [f"- {x}" for x in report["failures"]]
    (OUT / "HEADLINE_REPLAY_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (OUT / "status.txt").write_text(report["status"] + "\n", encoding="utf-8")


def main() -> int:
    scorer = load_frozen_scorer()
    failures: list[str] = []
    cross_model = cross_model_replay(scorer, failures)
    c1 = c1_replay(scorer, failures)
    status = "SCORER_REPLAY_PASS" if not failures else "SCORER_REPLAY_MISMATCH"
    report = {
        "schema": "discover-v1-frozen-scorer-headline-replay-v1",
        "status": status,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "scorer_sha256": sha256(SCORER_PATH),
        "llm_invoked": False,
        "traces_generated": False,
        "traces_rescored": True,
        "frozen_files_modified": False,
        "scientific_recomputation": False,
        "cross_model": cross_model,
        "c1": c1,
        "failures": failures,
    }
    write_report(report)
    print(json.dumps(report, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
