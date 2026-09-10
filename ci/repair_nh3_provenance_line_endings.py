#!/usr/bin/env python3
"""Repair only cross-platform line-ending changes in the NH3-FINAL-1.1 bundle.

For each file listed in SOURCE_MANIFEST.json, compare the checked-out bytes to the
source SHA-256. If the current bytes differ, try exactly two reversible text-line
ending candidates: LF->CRLF and CRLF->LF. A file is rewritten only if one candidate
matches the source manifest hash exactly. Any mismatch that cannot be repaired by
one of those exact transforms aborts the run.

This does not alter scientific values, parse or rewrite structured data, or rerun
any model calculation.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "provenance" / "nh3_final_1_1" / "source_harness"
MANIFEST = BUNDLE / "SOURCE_MANIFEST.json"
REPORT_DIR = ROOT / "artifacts" / "nh3_final_1_1_provenance"
REPORT_DIR.mkdir(parents=True, exist_ok=True)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def lf_to_crlf(data: bytes) -> bytes:
    # Canonicalize existing CRLF to LF first so the transform is idempotent.
    return data.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")


def crlf_to_lf(data: bytes) -> bytes:
    return data.replace(b"\r\n", b"\n")


def main() -> int:
    if not MANIFEST.is_file():
        raise SystemExit(f"Missing manifest: {MANIFEST}")

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    repaired: list[dict[str, str]] = []
    unchanged: list[str] = []
    unresolved: list[dict[str, str]] = []
    missing: list[str] = []

    for rec in manifest.get("files", []):
        rel = rec["path"]
        expected = rec["sha256"]
        path = BUNDLE / rel
        if not path.is_file():
            missing.append(rel)
            continue

        data = path.read_bytes()
        current = sha256(data)
        if current == expected:
            unchanged.append(rel)
            continue

        candidates = [
            ("LF_TO_CRLF", lf_to_crlf(data)),
            ("CRLF_TO_LF", crlf_to_lf(data)),
        ]
        matched = None
        for transform, candidate in candidates:
            if candidate != data and sha256(candidate) == expected:
                matched = (transform, candidate)
                break

        if matched is None:
            unresolved.append({"path": rel, "expected": expected, "actual": current})
            continue

        transform, candidate = matched
        path.write_bytes(candidate)
        repaired.append({
            "path": rel,
            "transform": transform,
            "sha256": expected,
        })

    report = {
        "schema": "nh3-final-1.1-line-ending-repair-v1",
        "manifest_files": len(manifest.get("files", [])),
        "unchanged": len(unchanged),
        "repaired": repaired,
        "missing": missing,
        "unresolved": unresolved,
        "scientific_calculation_executed": False,
        "rule": "rewrite only when a pure line-ending transform reproduces the source SHA-256 exactly",
    }
    (REPORT_DIR / "LINE_ENDING_REPAIR.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )

    print(json.dumps({
        "manifest_files": report["manifest_files"],
        "unchanged": report["unchanged"],
        "repaired": len(repaired),
        "missing": len(missing),
        "unresolved": len(unresolved),
    }, indent=2))

    if missing or unresolved:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
