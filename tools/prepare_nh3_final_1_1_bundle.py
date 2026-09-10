#!/usr/bin/env python3
"""Copy the already-completed NH3-FINAL-1.1 provenance into Catalyst-Essay.

This is an import/content-addressing utility only. It never imports the NH3 model,
never executes the model, and never changes files in the source harness.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DEST_ROOT = REPO / "provenance" / "nh3_final_1_1" / "source_harness"
MAX_FILE_BYTES = 45 * 1024 * 1024
CANONICAL_RUN = "outputs/nh3_final_20260905T134204Z"

CORE_FILES = [
    "configs/nh3_final.yaml",
    "configs/nh3_final_1.0_archived.yaml",
    "PRESSURE_CAPEX_INDEPENDENT_AUDIT_2026-09-05.md",
    "audits/audit_pressure_capex_handcalc_2026-09-05.py",
    "PROMOTE_NH3_FINAL_1_1_CHECKLIST.md",
    "NH3_FINAL_1_1_CONSISTENCY_CLOSURE.md",
]

TEXT_SUFFIXES = {".md", ".txt", ".csv", ".json", ".yaml", ".yml", ".py", ".r", ".R"}
FIG_SUFFIXES = {".svg", ".pdf", ".png", ".tif", ".tiff"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def copy_one(source_root: Path, rel: str, copied: list[dict], missing: list[str], skipped: list[dict]) -> None:
    src = source_root / rel
    if not src.exists():
        missing.append(rel)
        return
    if src.is_dir():
        for f in sorted(p for p in src.rglob("*") if p.is_file()):
            subrel = f.relative_to(source_root).as_posix()
            copy_file(source_root, subrel, copied, skipped)
    else:
        copy_file(source_root, rel, copied, skipped)


def copy_file(source_root: Path, rel: str, copied: list[dict], skipped: list[dict]) -> None:
    src = source_root / rel
    size = src.stat().st_size
    if size > MAX_FILE_BYTES:
        skipped.append({"path": rel, "bytes": size, "reason": "over_45_MiB"})
        return
    dst = DEST_ROOT / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    copied.append({
        "path": rel,
        "bytes": size,
        "sha256": sha256(dst),
    })


def collect_canonical_root_metadata(source_root: Path, copied: list[dict], skipped: list[dict]) -> list[str]:
    """Copy root-level metadata/summary files but leave large state libraries alone."""
    run_root = source_root / CANONICAL_RUN
    if not run_root.is_dir():
        return [CANONICAL_RUN]
    patterns = ("*summary*", "*manifest*", "*metadata*", "*result*", "*status*", "*config*")
    seen: set[Path] = set()
    for pat in patterns:
        for f in run_root.glob(pat):
            if f.is_file() and f not in seen:
                seen.add(f)
                copy_file(source_root, f.relative_to(source_root).as_posix(), copied, skipped)
    return []


def figure_candidates(source_root: Path) -> dict[str, list[str]]:
    figroot = source_root / "figures"
    out = {f"F{i}": [] for i in range(1, 7)}
    if not figroot.is_dir():
        return out
    files = [p for p in figroot.rglob("*") if p.is_file() and p.suffix.lower() in FIG_SUFFIXES]
    for i in range(1, 7):
        # Deliberately conservative: only explicit F1/F01/Figure1/Figure01 tokens.
        rx = re.compile(rf"(?i)(?:^|[^a-z0-9])(?:f0?{i}|figure[_ .-]?0?{i})(?:[^0-9]|$)")
        out[f"F{i}"] = [p.relative_to(source_root).as_posix() for p in files if rx.search(p.name)]
    return out


def copy_figure_candidates(source_root: Path, candidates: dict[str, list[str]], copied: list[dict], skipped: list[dict]) -> None:
    rels = sorted({p for vals in candidates.values() for p in vals})
    for rel in rels:
        copy_file(source_root, rel, copied, skipped)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-root", required=True, help="Root of the original NH3 source harness")
    ap.add_argument("--clean", action="store_true", help="Remove a prior imported source_harness bundle first")
    args = ap.parse_args()

    source_root = Path(args.source_root).expanduser().resolve()
    if not source_root.is_dir():
        raise SystemExit(f"Source root does not exist or is not a directory: {source_root}")
    if source_root == REPO or DEST_ROOT in source_root.parents:
        raise SystemExit("--source-root must point to the original source harness, not the destination bundle")

    if args.clean and DEST_ROOT.exists():
        shutil.rmtree(DEST_ROOT)
    DEST_ROOT.mkdir(parents=True, exist_ok=True)

    copied: list[dict] = []
    missing: list[str] = []
    skipped: list[dict] = []

    for rel in CORE_FILES:
        copy_one(source_root, rel, copied, missing, skipped)

    # The closure directory is the canonical direct source for rolling ranks, MC,
    # backward design, scaling reachability and lever calculations.
    copy_one(source_root, f"{CANONICAL_RUN}/closure", copied, missing, skipped)
    missing.extend(collect_canonical_root_metadata(source_root, copied, skipped))

    candidates = figure_candidates(source_root)
    copy_figure_candidates(source_root, candidates, copied, skipped)

    # Unique explicit figure-name match is accepted automatically; otherwise CI will
    # require the user/local agent to resolve the mapping from the original harness.
    fmap: dict[str, str | None] = {}
    ambiguous: dict[str, list[str]] = {}
    for fid, vals in candidates.items():
        # Prefer vectors; retain unique candidate only when one logical file stem exists.
        stems = {}
        for rel in vals:
            stems.setdefault(str(Path(rel).with_suffix("")), []).append(rel)
        if len(stems) == 1:
            files = next(iter(stems.values()))
            preferred = sorted(files, key=lambda x: ({".svg": 0, ".pdf": 1, ".png": 2, ".tif": 3, ".tiff": 4}.get(Path(x).suffix.lower(), 9), x))
            fmap[fid] = preferred[0]
        else:
            fmap[fid] = None
            if vals:
                ambiguous[fid] = vals

    manifest = {
        "schema": "nh3-final-1.1-provenance-import-v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "source_root_name": source_root.name,
        "canonical_run": CANONICAL_RUN,
        "files": sorted(copied, key=lambda x: x["path"]),
        "missing_expected_paths": sorted(set(missing)),
        "skipped_files": skipped,
        "note": "Content-addressed import only; no scientific calculation executed.",
    }
    (DEST_ROOT / "SOURCE_MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (DEST_ROOT / "FIGURE_ASSET_MAP.json").write_text(json.dumps({
        "schema": "nh3-final-1.1-figure-map-v1",
        "figures": fmap,
        "ambiguous_candidates": ambiguous,
        "instruction": "Resolve only against the original source-harness F1-F6 assets; do not substitute FINAL-1.0 figures.",
    }, indent=2), encoding="utf-8")

    lines = [
        "# NH3-FINAL-1.1 import report",
        "",
        f"Source root name: `{source_root.name}`",
        f"Canonical run anchor: `{CANONICAL_RUN}`",
        "",
        f"Copied files: **{len(copied)}**",
        f"Missing expected paths: **{len(set(missing))}**",
        f"Skipped large files: **{len(skipped)}**",
        "",
        "No model calculation was executed.",
        "",
        "## Figure mapping",
        "",
    ]
    for fid in [f"F{i}" for i in range(1, 7)]:
        lines.append(f"- {fid}: `{fmap[fid]}`" if fmap[fid] else f"- {fid}: unresolved")
    if missing:
        lines += ["", "## Missing expected paths", ""] + [f"- `{x}`" for x in sorted(set(missing))]
    if skipped:
        lines += ["", "## Skipped files", ""] + [f"- `{x['path']}` ({x['bytes']} bytes; {x['reason']})" for x in skipped]
    (DEST_ROOT / "IMPORT_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Prepared {len(copied)} files under {DEST_ROOT}")
    if missing:
        print("Missing expected paths:")
        for x in sorted(set(missing)):
            print(" -", x)
    if ambiguous:
        print("Ambiguous figure mappings:", ", ".join(sorted(ambiguous)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
