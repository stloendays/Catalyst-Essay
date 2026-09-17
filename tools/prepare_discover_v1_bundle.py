#!/usr/bin/env python3
"""Vendor the frozen DISCOVER V1 / DISCOVER-BOUNDARY-C1 evidence into Catalyst-Essay.

Import and content-addressing utility only. It reads the source harness, writes into
provenance/discover_v1/source_harness, and never modifies the source harness, never runs
an LLM, never re-scores a trace and never touches a frozen file.

The gate: the 15-pin frozen manifest and discover/formal_e.py must reproduce their pinned
SHA-256 before a single byte is copied. A source that does not verify is not the frozen
harness, and vendoring it would publish a corrupted protocol under the paper's name.

Deliberate exclusion: cache/ holds the precomputed response-surface .npz files. They are
derived artefacts, regenerable from the deterministic harness, already-compressed binary
that version control cannot pack, and the largest of them exceeds the 100 MiB per-file
limit of the hosting service. They are excluded by policy and their SHA-256 is recorded in
the manifest, so the omission is itself content-addressed rather than silent.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DEST_ROOT = REPO / "provenance" / "discover_v1" / "source_harness"
MAX_FILE_BYTES = 45 * 1024 * 1024

# The 15 frozen protocol files and their pinned SHA-256. These values are the paper's
# claim about what was run; they are hardcoded here rather than read from the manifest so
# that regenerating the manifest cannot launder a changed protocol file.
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
# Cited by SI section 7 but not part of the 15-pin manifest.
FORMAL_E = "discover/formal_e.py"
FORMAL_E_SHA = "d4451c424dbfac5f7a6176038864f35cc6326ac04ae5efcb91f14574f8aeee93"

# Driver, environment core, and every analysis script that produced a committed table.
CODE_GLOBS = ["discover/*.py", "discover/*.json", "tests/*.py", "tests/*.json"]
CODE_FILES = ["harness_core.py", "DISCOVER_FROZEN_V1.json"]

# The frozen written record: preregistration, audits, cost-model report, failure analysis.
RECORD_GLOBS = ["DISCOVER_*.md", "DISCOVER_*.csv"]

# Bulk evidence: every scored trace, run metadata, per-run score file and rendered panel.
EVIDENCE_DIRS = [
    "DISCOVER_FORMAL_RUNS_V1",
    "DISCOVER_CROSS_MODEL_V1",
    "DISCOVER_BOUNDARY_C1",
    "discover_runs",
    "outputs",
]

# Excluded by policy; hashed and declared rather than dropped.
EXCLUDED_DIRS = [("cache", "derived response-surface cache: regenerable, binary-incompressible, "
                           "largest member exceeds the 100 MiB per-file hosting limit")]

TRACE_COUNT_ANCHOR = 1263


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_frozen(source_root: Path) -> list[str]:
    """Return a list of failures. Empty means the source is the frozen harness."""
    bad: list[str] = []
    for rel, expected in FROZEN_15.items():
        p = source_root / rel
        if not p.is_file():
            bad.append(f"{rel}: ABSENT")
            continue
        actual = sha256(p)
        if actual != expected:
            bad.append(f"{rel}: expected {expected} actual {actual}")
    p = source_root / FORMAL_E
    if not p.is_file():
        bad.append(f"{FORMAL_E}: ABSENT")
    else:
        actual = sha256(p)
        if actual != FORMAL_E_SHA:
            bad.append(f"{FORMAL_E}: expected {FORMAL_E_SHA} actual {actual}")
    return bad


def copy_file(source_root: Path, rel: str, copied: list[dict], skipped: list[dict], seen: set[str]) -> None:
    if rel in seen:
        return
    src = source_root / rel
    if not src.is_file():
        return
    size = src.stat().st_size
    if size > MAX_FILE_BYTES:
        skipped.append({"path": rel, "bytes": size, "reason": "over_45_MiB"})
        return
    dst = DEST_ROOT / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    seen.add(rel)
    copied.append({"path": rel, "bytes": size, "sha256": sha256(dst)})


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-root", required=True, help="Root of the original DISCOVER V1 source harness")
    ap.add_argument("--clean", action="store_true", help="Remove a prior imported source_harness bundle first")
    args = ap.parse_args()

    source_root = Path(args.source_root).expanduser().resolve()
    if not source_root.is_dir():
        raise SystemExit(f"Source root does not exist or is not a directory: {source_root}")
    if source_root == REPO or DEST_ROOT in source_root.parents:
        raise SystemExit("--source-root must point to the original source harness, not the destination bundle")

    print("verifying the 15-pin frozen manifest before copying anything")
    bad = verify_frozen(source_root)
    if bad:
        print("\nFROZEN VERIFICATION FAILED - nothing was copied:")
        for b in bad:
            print("  " + b)
        return 1
    print(f"  {len(FROZEN_15)}/{len(FROZEN_15)} frozen files verified, plus {FORMAL_E}\n")

    if args.clean and DEST_ROOT.exists():
        shutil.rmtree(DEST_ROOT)
    DEST_ROOT.mkdir(parents=True, exist_ok=True)

    copied: list[dict] = []
    skipped: list[dict] = []
    seen: set[str] = set()

    print("copying frozen protocol files")
    for rel in FROZEN_15:
        copy_file(source_root, rel, copied, skipped, seen)
    copy_file(source_root, FORMAL_E, copied, skipped, seen)

    print("copying driver, environment core and analysis scripts")
    for rel in CODE_FILES:
        copy_file(source_root, rel, copied, skipped, seen)
    for pattern in CODE_GLOBS:
        for p in sorted(source_root.glob(pattern)):
            if p.is_file():
                copy_file(source_root, p.relative_to(source_root).as_posix(), copied, skipped, seen)

    print("copying the frozen written record")
    for pattern in RECORD_GLOBS:
        for p in sorted(source_root.glob(pattern)):
            if p.is_file():
                copy_file(source_root, p.relative_to(source_root).as_posix(), copied, skipped, seen)

    print("copying run evidence")
    for d in EVIDENCE_DIRS:
        root = source_root / d
        if not root.is_dir():
            print(f"  ABSENT: {d}")
            continue
        before = len(copied)
        for p in sorted(root.rglob("*")):
            if p.is_file():
                copy_file(source_root, p.relative_to(source_root).as_posix(), copied, skipped, seen)
        print(f"  {d}: {len(copied) - before} files")

    excluded: list[dict] = []
    for d, reason in EXCLUDED_DIRS:
        root = source_root / d
        if not root.is_dir():
            continue
        for p in sorted(root.rglob("*")):
            if p.is_file():
                excluded.append({
                    "path": p.relative_to(source_root).as_posix(),
                    "bytes": p.stat().st_size,
                    "sha256": sha256(p),
                    "reason": reason,
                })
    print(f"declared exclusions: {len(excluded)} file(s)")

    traces = sum(1 for e in copied if e["path"].endswith("/trace.json"))

    manifest = {
        "schema": "discover-v1-provenance-import-v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "source_root_name": source_root.name,
        "frozen_pin_count": len(FROZEN_15),
        "frozen_verified_at_import": True,
        "formal_e_sha256": FORMAL_E_SHA,
        "trace_count": traces,
        "trace_count_anchor": TRACE_COUNT_ANCHOR,
        "evidence_dirs": EVIDENCE_DIRS,
        "file_count": len(copied),
        "total_bytes": sum(e["bytes"] for e in copied),
        "files": copied,
        "skipped_files": skipped,
        "excluded_files": excluded,
        "scientific_calculation_executed": False,
    }
    (DEST_ROOT / "SOURCE_MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"\nfiles vendored: {len(copied)}")
    print(f"bytes vendored: {manifest['total_bytes'] / 1048576:.1f} MiB")
    print(f"trace.json:     {traces} (anchor {TRACE_COUNT_ANCHOR})")
    print(f"skipped:        {len(skipped)}")
    print(f"manifest:       {DEST_ROOT / 'SOURCE_MANIFEST.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
