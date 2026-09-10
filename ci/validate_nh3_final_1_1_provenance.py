#!/usr/bin/env python3
"""Validate a content-addressed NH3-FINAL-1.1 provenance import.

The validator never runs scientific models. It only checks the imported source-harness
files, hashes, canonical textual anchors, evidence classes and F1-F6 asset mapping.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "provenance" / "nh3_final_1_1" / "source_harness"
OUT = ROOT / "artifacts" / "nh3_final_1_1_provenance"
OUT.mkdir(parents=True, exist_ok=True)

MANIFEST = BUNDLE / "SOURCE_MANIFEST.json"
FIGMAP = BUNDLE / "FIGURE_ASSET_MAP.json"
CANONICAL_DOC = BUNDLE / "NH3_FINAL_1_1_CONSISTENCY_CLOSURE.md"
PRESSURE_CAPEX_REPORT = BUNDLE / "NH3_FINAL_1_1_PRESSURE_CAPEX_REPORT_2026-09-05.md"
PRESSURE_CAPEX_AUDIT = BUNDLE / "PRESSURE_CAPEX_INDEPENDENT_AUDIT_2026-09-05.md"
# The frozen manuscript anchors are distributed across the FINAL-1.1 record set: the
# consistency closure, the FINAL-1.1 pressure/CAPEX run report and its independent audit.
# Only FINAL-1.1 documents belong here; archived FINAL-1.0 records are never read.
CANONICAL_DOCS = [CANONICAL_DOC, PRESSURE_CAPEX_REPORT, PRESSURE_CAPEX_AUDIT]
CANONICAL_RUN = BUNDLE / "outputs" / "nh3_final_20260905T134204Z"
CLOSURE = CANONICAL_RUN / "closure"

CORE_PATHS = [
    BUNDLE / "configs" / "nh3_final.yaml",
    PRESSURE_CAPEX_AUDIT,
    PRESSURE_CAPEX_REPORT,
    BUNDLE / "audits" / "audit_pressure_capex_handcalc_2026-09-05.py",
    BUNDLE / "PROMOTE_NH3_FINAL_1_1_CHECKLIST.md",
    CANONICAL_DOC,
    CLOSURE,
]

# These values are frozen manuscript anchors. They are checked against the imported
# FINAL-1.1 consistency-closure record, not against a newly calculated result.
ANCHORS = {
    "Fe_cost": [r"15\.292"],
    "Ru_cost": [r"22\.031"],
    "Os_cost": [r"25\.832"],
    "top3_spearman": [r"(?:-|−)0\.50"],
    "full15_raw_spearman": [r"0\.929"],
    "Fe_feasibility": [r"0\.799", r"79\.9\s*%"],
    "Fe_top1_survival": [r"0\.282", r"28\.2\s*%"],
    "Fe_top3_actionable": [r"0\.940", r"94\.0\s*%", r"94\s*%"],
    "Ru_break_even": [r"201\.22"],
    "headroom_673K": [r"1\.090"],
    "headroom_process_max": [r"2\.525"],
    "strict_scaling_Ru_min_cost": [r"21\.398"],
    "strict_scaling_E_N": [r"(?:-|−)1\.215"],
}

FIG_SUFFIXES = {".svg", ".pdf", ".png", ".tif", ".tiff"}
DATA_SUFFIXES = {".csv", ".json", ".tsv", ".xlsx", ".parquet", ".npz", ".npy"}
EVIDENCE_CLASSES = {
    "F1_ranking_cost": ("rank", "ranking", "cost", "candidate"),
    "F2_rolling_rank": ("rolling", "spearman", "kendall", "top-k", "topk"),
    "F3_uncertainty_MC": ("monte", "mc", "uncert", "draw", "feasib"),
    "F4_operating_envelope": ("pressure", "envelope", "profile", "operating", "optimum"),
    "F5_backward_break_even": ("backward", "break-even", "breakeven", "parity", "activity"),
    "F6_scaling_reachability": ("scaling", "reachability", "headroom", "manifold"),
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def safe_text(path: Path, limit: int = 300_000) -> str:
    if path.suffix.lower() not in {".md", ".txt", ".csv", ".json", ".yaml", ".yml", ".py", ".r"}:
        return ""
    try:
        return path.read_text(encoding="utf-8", errors="replace")[:limit]
    except Exception:
        return ""


def classify_data_evidence() -> dict[str, list[str]]:
    hits = {k: [] for k in EVIDENCE_CLASSES}
    if not BUNDLE.exists():
        return hits
    for path in BUNDLE.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in DATA_SUFFIXES:
            continue
        text = (path.relative_to(BUNDLE).as_posix() + " " + safe_text(path, 60_000)).lower()
        for cls, terms in EVIDENCE_CLASSES.items():
            if any(t in text for t in terms):
                hits[cls].append(path.relative_to(BUNDLE).as_posix())
    for cls in hits:
        hits[cls] = sorted(set(hits[cls]))
    return hits


def write_report(report: dict) -> None:
    (OUT / "status.txt").write_text(report["status"] + "\n", encoding="utf-8")
    (OUT / "validation.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    lines = [
        "# NH3-FINAL-1.1 provenance closure validation",
        "",
        f"Status: **{report['status']}**",
        "",
        f"Checked at: `{report['timestamp_utc']}`",
        "",
        "This validation is provenance-only; no scientific model was executed.",
        "",
        "## Core source paths",
        "",
    ]
    for p, ok in report["core_paths"].items():
        lines.append(f"- `{p}`: {'present' if ok else 'missing'}")
    lines += ["", "## Manifest integrity", ""]
    lines.append(f"- manifest present: {report['manifest_present']}")
    lines.append(f"- listed files: {report['manifest_file_count']}")
    lines.append(f"- missing listed files: {len(report['manifest_missing_files'])}")
    lines.append(f"- hash mismatches: {len(report['hash_mismatches'])}")
    lines += ["", "## Canonical anchor check", ""]
    for key, ok in report["canonical_anchor_matches"].items():
        lines.append(f"- {key}: {'PASS' if ok else 'not established from imported consistency record'}")
    lines += ["", "## F1-F6 source-data classes", ""]
    for key, vals in report["evidence_classes"].items():
        lines.append(f"- {key}: {len(vals)} candidate data file(s)")
    lines += ["", "## F1-F6 figure map", ""]
    for fid, item in report["figure_map"].items():
        lines.append(f"- {fid}: {item if item else 'unresolved'}")
    if report["notes"]:
        lines += ["", "## Notes", ""] + [f"- {x}" for x in report["notes"]]
    (OUT / "VALIDATION_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    now = datetime.now(timezone.utc).isoformat()
    core = {rel(p): p.exists() for p in CORE_PATHS}
    notes: list[str] = []
    manifest_present = MANIFEST.is_file()
    manifest_file_count = 0
    manifest_missing: list[str] = []
    hash_mismatches: list[dict[str, str]] = []
    manifest_error: str | None = None

    manifest = None
    if manifest_present:
        try:
            manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
            entries = manifest.get("files", [])
            manifest_file_count = len(entries)
            if manifest.get("canonical_run") != "outputs/nh3_final_20260905T134204Z":
                manifest_error = "Manifest canonical_run does not match frozen run anchor."
            for entry in entries:
                p = BUNDLE / str(entry.get("path", ""))
                if not p.is_file():
                    manifest_missing.append(str(entry.get("path", "")))
                    continue
                actual = sha256(p)
                expected = str(entry.get("sha256", ""))
                if actual != expected:
                    hash_mismatches.append({"path": str(entry.get("path", "")), "expected": expected, "actual": actual})
        except Exception as exc:
            manifest_error = f"Could not parse SOURCE_MANIFEST.json: {exc}"

    canonical_text = "\n".join(safe_text(doc) for doc in CANONICAL_DOCS)
    anchor_matches: dict[str, bool] = {}
    for key, patterns in ANCHORS.items():
        anchor_matches[key] = any(re.search(pat, canonical_text, flags=re.IGNORECASE) for pat in patterns)

    evidence = classify_data_evidence()

    figmap: dict[str, str | None] = {f"F{i}": None for i in range(1, 7)}
    figmap_error: str | None = None
    if FIGMAP.is_file():
        try:
            raw = json.loads(FIGMAP.read_text(encoding="utf-8"))
            for fid in figmap:
                value = raw.get("figures", {}).get(fid)
                if isinstance(value, str) and value:
                    p = BUNDLE / value
                    if p.is_file() and p.suffix.lower() in FIG_SUFFIXES:
                        figmap[fid] = value
                    else:
                        notes.append(f"{fid} mapped asset is missing or has an unsupported extension: {value}")
        except Exception as exc:
            figmap_error = f"Could not parse FIGURE_ASSET_MAP.json: {exc}"

    if not BUNDLE.exists() or not manifest_present:
        status = "PENDING_SOURCE_IMPORT"
    elif manifest_error or manifest_missing or hash_mismatches:
        status = "HASH_MISMATCH" if hash_mismatches else "PENDING_SOURCE_IMPORT"
    elif not all(core.values()):
        status = "PENDING_SOURCE_IMPORT"
    elif not all(anchor_matches.values()):
        status = "CANONICAL_EVIDENCE_INCOMPLETE"
    elif not all(evidence.values()):
        status = "SOURCE_DATA_CLASS_INCOMPLETE"
    elif figmap_error or not all(figmap.values()):
        status = "FIGURE_MAPPING_INCOMPLETE"
    else:
        status = "PROVENANCE_VALIDATED_READY_FOR_LOCK"

    if manifest_error:
        notes.append(manifest_error)
    if figmap_error:
        notes.append(figmap_error)
    if status == "PENDING_SOURCE_IMPORT":
        notes.append("Copy the original FINAL-1.1 source-harness evidence with tools/prepare_nh3_final_1_1_bundle.py; do not substitute archived FINAL-1.0 files.")
    if status == "CANONICAL_EVIDENCE_INCOMPLETE":
        notes.append("The imported FINAL-1.1 consistency record does not expose every frozen manuscript anchor; do not lock F1-F6 until the direct source record is complete.")
    if status == "SOURCE_DATA_CLASS_INCOMPLETE":
        notes.append("At least one F1-F6 evidence class lacks a directly imported data file; import the missing closure/profile data instead of reconstructing it from manuscript values.")
    if status == "FIGURE_MAPPING_INCOMPLETE":
        notes.append("Resolve FIGURE_ASSET_MAP.json against the original FINAL-1.1 figures directory. Renaming is allowed only after preserving the original path/hash in the manifest.")

    report = {
        "schema": "nh3-final-1.1-provenance-validation-v1",
        "status": status,
        "timestamp_utc": now,
        "canonical_run_anchor": "outputs/nh3_final_20260905T134204Z",
        "core_paths": core,
        "manifest_present": manifest_present,
        "manifest_file_count": manifest_file_count,
        "manifest_missing_files": manifest_missing,
        "hash_mismatches": hash_mismatches,
        "canonical_anchor_matches": anchor_matches,
        "evidence_classes": evidence,
        "figure_map": figmap,
        "notes": notes,
        "scientific_calculation_executed": False,
    }
    write_report(report)
    print(json.dumps({
        "status": status,
        "manifest_file_count": manifest_file_count,
        "core_present": sum(core.values()),
        "core_required": len(core),
        "canonical_anchors": f"{sum(anchor_matches.values())}/{len(anchor_matches)}",
        "evidence_classes": f"{sum(bool(v) for v in evidence.values())}/{len(evidence)}",
        "figures_mapped": f"{sum(bool(v) for v in figmap.values())}/6",
    }, indent=2))
    # Pending provenance is a scientifically valid state, not an infrastructure error.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
