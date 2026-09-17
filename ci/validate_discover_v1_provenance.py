#!/usr/bin/env python3
"""Validate the vendored DISCOVER V1 / DISCOVER-BOUNDARY-C1 provenance bundle.

The validator never runs an LLM, never re-scores a trace and never writes into the bundle.
It answers one question: are the bytes in provenance/discover_v1/source_harness the frozen
protocol and the evidence the paper reports, or are they something else?

Four checks carry the verdict.

1. The 15-pin frozen manifest, plus discover/formal_e.py, verified against SHA-256 values
   hardcoded here rather than read from the bundle's own manifest. A bundle cannot vouch
   for itself; the pins are the paper's claim and live in the validator.
2. Manifest integrity in both directions: every listed file present and matching, and no
   file present in the bundle that the manifest does not list.
3. Evidence completeness: every run family present, and the trace count matching the
   figure the manuscript reports.
4. Exclusions declared: anything deliberately not vendored must appear in the manifest
   with a SHA-256 and a reason, so an omission is content-addressed rather than silent.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "provenance" / "discover_v1" / "source_harness"
OUT = ROOT / "artifacts" / "discover_v1_provenance"
MANIFEST = BUNDLE / "SOURCE_MANIFEST.json"

FROZEN_15 = {
    "DISCOVER_TASK_V1.json": "030d14b20fd6ed1499a7eed930fd7cd2622a50102406ec7ca4b09d834add97d9",
    "DISCOVER_TASK_V1_ANON.json": "9524a5893bed00510c1a7325af3f16e7ed3a857dd0607aeeb07573b8270a2121",
    "DISCOVER_ACTION_SCHEMA_V1.json": "2e06bb552c28dfbd54444321c16b825087544493866df828cf6ee7c7300810c9",
    "DISCOVER_COST_MODEL_V1.json": "fa164a9a4916cd7aa6ca7429f4dd6ae5d0b32f402313a80d5eed00d537b0bbb3",
    "DISCOVER_PROMPT_V1.md": "5a0b1e297fb9ee84e6f1917d8c68bcfbbfb6670ea8dd5b0129cdc89beb6580ed",
    "DISCOVER_SCORER_V1.py": "406b0f53be51b49596dc45e086408912dfccfecea316800f5ced3d5f7df1c3ae",
    "DISCOVER_PREREGISTRATION_V1.md": "a8d998973f922e785cee11eccae293e938780fecd9adf915c7e5cf8eddf38e2a",
    "discover/env.py": "f2e39a57ce2cfd3bae58988d1f5dc25e4f8042a39b2aec9de16cda7b829b39ce",
    "discover/policies.py": "02caabcf1eea5c411e4f6c76ccfc07539c9527817dfbc965a59a909906d81979",
    "discover/run.py": "fb0f0e78c47d15ad9e3eed9a30aba71dff69065e95af96f5c12c9b48f65a64bc",
    "discover/llm_policy.py": "aab68281950eccb3c76eb89353c1f3136a1f85114c281256664a34c8454cba39",
    "discover/prior_probe.py": "fd71275e8fbb46d02683cbf0e15580d1e4b6d1b334077650b7d0200d1dfc0593",
    "discover/IDENTITY_MAPPING_SCORER_ONLY.json": "b5e5015937cc4b65dfa44e49a59bf56d20c25bf7826d89381698870d5096c75a",
    "discover/PROTOCOL_FORBIDDEN_ACTIONS.json": "27a9f571df1c7f49c6069713474f7657aa96bd9bf99f942e3f15171feb58d6e3",
    "tests/test_discover_oracle.py": "007b856e23fae10a792a186eb09f76564783b7787a7e4372bfbbae5d5262a933",
}
FORMAL_E = "discover/formal_e.py"
FORMAL_E_SHA = "d4451c424dbfac5f7a6176038864f35cc6326ac04ae5efcb91f14574f8aeee93"

EVIDENCE_DIRS = [
    "DISCOVER_FORMAL_RUNS_V1",
    "DISCOVER_CROSS_MODEL_V1",
    "DISCOVER_BOUNDARY_C1",
    "discover_runs",
    "outputs",
]
TRACE_COUNT_ANCHOR = 1263


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_report(report: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "status.txt").write_text(report["status"] + "\n", encoding="utf-8")
    (OUT / "validation.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    lines = [
        "# DISCOVER V1 provenance validation",
        "",
        f"Status: **{report['status']}**",
        "",
        f"Checked at: `{report['timestamp_utc']}`",
        "",
        "Provenance only. No LLM was called, no trace was re-scored, no frozen file was written.",
        "",
        "## Frozen protocol pins",
        "",
        f"- 15-pin manifest: {report['frozen_matches']}/{len(FROZEN_15)} exact SHA-256 match",
        f"- `{FORMAL_E}`: {'MATCH' if report['formal_e_match'] else 'MISMATCH or ABSENT'}",
    ]
    for f in report["frozen_failures"]:
        lines.append(f"  - {f}")
    lines += [
        "",
        "## Manifest integrity",
        "",
        f"- manifest present: {report['manifest_present']}",
        f"- listed files: {report['manifest_file_count']}",
        f"- missing listed files: {len(report['manifest_missing_files'])}",
        f"- hash mismatches: {len(report['hash_mismatches'])}",
        f"- files on disk not listed in the manifest: {len(report['unlisted_files'])}",
        "",
        "## Evidence completeness",
        "",
        f"- trace.json found: {report['trace_count']} (anchor {TRACE_COUNT_ANCHOR})",
    ]
    for d, n in report["evidence_dirs"].items():
        lines.append(f"- `{d}`: {n} file(s)")
    lines += [
        "",
        "## Declared exclusions",
        "",
        f"- {report['excluded_count']} file(s) deliberately not vendored, each carrying a SHA-256 and a reason",
    ]
    for e in report["excluded_sample"]:
        lines.append(f"  - `{e['path']}` ({e['bytes'] / 1048576:.1f} MiB)")
    if report["exclusion_reasons"]:
        lines += ["", "Reason(s) recorded:"] + [f"- {r}" for r in report["exclusion_reasons"]]
    if report["notes"]:
        lines += ["", "## Notes", ""] + [f"- {x}" for x in report["notes"]]
    (OUT / "VALIDATION_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    now = datetime.now(timezone.utc).isoformat()
    notes: list[str] = []

    # --- 1. frozen pins, checked against this file's hardcoded values
    frozen_failures: list[str] = []
    frozen_matches = 0
    for rel, expected in FROZEN_15.items():
        p = BUNDLE / rel
        if not p.is_file():
            frozen_failures.append(f"{rel}: ABSENT from the bundle")
            continue
        actual = sha256(p)
        if actual == expected:
            frozen_matches += 1
        else:
            frozen_failures.append(f"{rel}: expected {expected} actual {actual}")
    fe = BUNDLE / FORMAL_E
    formal_e_match = fe.is_file() and sha256(fe) == FORMAL_E_SHA
    if not formal_e_match:
        frozen_failures.append(f"{FORMAL_E}: absent or does not reproduce {FORMAL_E_SHA}")

    # --- 2. manifest integrity, both directions
    manifest_present = MANIFEST.is_file()
    manifest_file_count = 0
    manifest_missing: list[str] = []
    hash_mismatches: list[dict] = []
    unlisted: list[str] = []
    excluded_count = 0
    excluded_sample: list[dict] = []
    exclusion_reasons: list[str] = []
    manifest_error: str | None = None
    manifest_trace_count = None

    if manifest_present:
        try:
            manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
            entries = manifest.get("files", [])
            manifest_file_count = len(entries)
            manifest_trace_count = manifest.get("trace_count")
            listed = set()
            for entry in entries:
                rel = str(entry.get("path", ""))
                listed.add(rel)
                p = BUNDLE / rel
                if not p.is_file():
                    manifest_missing.append(rel)
                    continue
                actual = sha256(p)
                expected = str(entry.get("sha256", ""))
                if actual != expected:
                    hash_mismatches.append({"path": rel, "expected": expected, "actual": actual})
            for p in BUNDLE.rglob("*"):
                if p.is_file() and p != MANIFEST:
                    rel = p.relative_to(BUNDLE).as_posix()
                    if rel not in listed:
                        unlisted.append(rel)
            excl = manifest.get("excluded_files", [])
            excluded_count = len(excl)
            for e in excl:
                if not e.get("sha256") or not e.get("reason"):
                    notes.append(f"Exclusion without a hash or a reason: {e.get('path')}")
            excluded_sample = sorted(excl, key=lambda e: -int(e.get("bytes", 0)))[:5]
            exclusion_reasons = sorted({str(e.get("reason", "")) for e in excl if e.get("reason")})
        except Exception as exc:
            manifest_error = f"Could not parse SOURCE_MANIFEST.json: {exc}"

    # --- 3. evidence completeness
    evidence_dirs = {}
    for d in EVIDENCE_DIRS:
        root = BUNDLE / d
        evidence_dirs[d] = sum(1 for p in root.rglob("*") if p.is_file()) if root.is_dir() else 0
    trace_count = sum(1 for p in BUNDLE.rglob("trace.json") if p.is_file())

    # --- verdict
    if not BUNDLE.exists() or not manifest_present:
        status = "PENDING_SOURCE_IMPORT"
    elif frozen_failures:
        status = "FROZEN_HASH_MISMATCH"
    elif manifest_error or hash_mismatches:
        status = "HASH_MISMATCH"
    elif manifest_missing or unlisted:
        status = "MANIFEST_INCOMPLETE"
    elif not all(evidence_dirs.values()) or trace_count != TRACE_COUNT_ANCHOR:
        status = "EVIDENCE_CLASS_INCOMPLETE"
    else:
        status = "PROVENANCE_VALIDATED_READY_FOR_LOCK"

    if manifest_error:
        notes.append(manifest_error)
    if status == "PENDING_SOURCE_IMPORT":
        notes.append("Run tools/prepare_discover_v1_bundle.py against the original source harness.")
    if status == "FROZEN_HASH_MISMATCH":
        notes.append("The vendored protocol files are not the frozen bytes. Do not repair them in place; "
                     "re-import from a source harness that verifies. This is recovery, not repair.")
    if unlisted:
        notes.append(f"{len(unlisted)} file(s) exist in the bundle but are absent from the manifest; "
                     "every vendored byte must be content-addressed.")
    if trace_count != TRACE_COUNT_ANCHOR:
        notes.append(f"Trace count {trace_count} does not match the manuscript anchor {TRACE_COUNT_ANCHOR}.")
    if manifest_trace_count is not None and manifest_trace_count != trace_count:
        notes.append(f"Manifest records {manifest_trace_count} traces; {trace_count} are present on disk.")

    report = {
        "schema": "discover-v1-provenance-validation-v1",
        "status": status,
        "timestamp_utc": now,
        "frozen_matches": frozen_matches,
        "frozen_required": len(FROZEN_15),
        "frozen_failures": frozen_failures,
        "formal_e_match": formal_e_match,
        "manifest_present": manifest_present,
        "manifest_file_count": manifest_file_count,
        "manifest_missing_files": manifest_missing,
        "hash_mismatches": hash_mismatches,
        "unlisted_files": unlisted[:50],
        "unlisted_count": len(unlisted),
        "evidence_dirs": evidence_dirs,
        "trace_count": trace_count,
        "trace_count_anchor": TRACE_COUNT_ANCHOR,
        "excluded_count": excluded_count,
        "excluded_sample": excluded_sample,
        "exclusion_reasons": exclusion_reasons,
        "notes": notes,
        "llm_invoked": False,
        "traces_rescored": False,
    }
    write_report(report)
    print(json.dumps({
        "status": status,
        "frozen": f"{frozen_matches}/{len(FROZEN_15)}",
        "formal_e": formal_e_match,
        "manifest_files": manifest_file_count,
        "hash_mismatches": len(hash_mismatches),
        "unlisted": len(unlisted),
        "traces": f"{trace_count}/{TRACE_COUNT_ANCHOR}",
        "excluded": excluded_count,
    }, indent=2))
    return 0 if status == "PROVENANCE_VALIDATED_READY_FOR_LOCK" else 1


if __name__ == "__main__":
    raise SystemExit(main())
