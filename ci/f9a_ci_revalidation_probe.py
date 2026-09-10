#!/usr/bin/env python3
"""Conservative CI probe for F9A FINAL-1.1 revalidation.

This script does not invent a replacement leverage metric. It searches the full git
history for the exact historical implementation/evidence and checks whether the
frozen NH3-FINAL-1.1 harness required by the revalidation task is available to CI.
It emits one of the task's allowed classifications.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "f9a_ci"
OUT.mkdir(parents=True, exist_ok=True)

MEOH_CH4 = 0.3757939247335326
DENOM = [0.020, 0.025, 0.030]
REQUIRED_CURRENT = [
    "configs/nh3_final.yaml",
    "outputs/nh3_final_20260905T134204Z",
]
HISTORICAL_NEEDLES = [
    "0.000916",
    "0.001374",
    "0.0458",
    "273–410",
    "273-410",
]
CODE_EXTS = {".py", ".r", ".R", ".jl", ".m", ".sh", ".ipynb"}
TEXT_EXTS = CODE_EXTS | {".md", ".txt", ".csv", ".json", ".yaml", ".yml"}


def sh(*args: str, check: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(args), cwd=ROOT, text=True, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, check=check
    )


def sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def rev_objects() -> list[tuple[str, str]]:
    p = sh("git", "rev-list", "--all", "--objects")
    out: list[tuple[str, str]] = []
    for line in p.stdout.splitlines():
        parts = line.split(" ", 1)
        if len(parts) == 2:
            out.append((parts[0], parts[1]))
    return out


def commits_for_string(needle: str) -> list[str]:
    p = sh("git", "log", "--all", "--format=%H", f"-S{needle}", "--", ".")
    return [x.strip() for x in p.stdout.splitlines() if x.strip()]


def files_in_commit(commit: str) -> list[str]:
    p = sh("git", "show", "--pretty=format:", "--name-only", commit)
    return sorted({x.strip() for x in p.stdout.splitlines() if x.strip()})


def show_text(commit: str, path: str) -> str | None:
    p = sh("git", "show", f"{commit}:{path}")
    if p.returncode != 0:
        return None
    text = p.stdout
    if "\x00" in text:
        return None
    return text


def source_score(text: str) -> int:
    low = text.lower()
    tokens = [
        "tof", "activity", "leverage", "elasticity", "d ln", "dln",
        "log(", "np.log", "perturb", "finite", "reopt", "optimiz",
    ]
    return sum(t in low for t in tokens)


head = sh("git", "rev-parse", "HEAD").stdout.strip()
objects = rev_objects()
all_paths = [p for _, p in objects]

current_presence = {p: (ROOT / p).exists() for p in REQUIRED_CURRENT}
current_hashes = {
    p: sha256(ROOT / p) if (ROOT / p).is_file() else None
    for p in REQUIRED_CURRENT
}

filename_history = {
    "nh3_final_paths": sorted({p for p in all_paths if "nh3_final" in p.lower()}),
    "leverage_paths": sorted({p for p in all_paths if "leverage" in p.lower()}),
    "cross_reaction_paths": sorted({p for p in all_paths if "cross" in p.lower() and "reaction" in p.lower()}),
}

needle_hits: dict[str, list[dict[str, object]]] = {}
implementation_candidates: list[dict[str, object]] = []
seen = set()
for needle in HISTORICAL_NEEDLES:
    hits: list[dict[str, object]] = []
    for commit in commits_for_string(needle)[:50]:
        for path in files_in_commit(commit):
            ext = Path(path).suffix
            if ext not in TEXT_EXTS:
                continue
            text = show_text(commit, path)
            if text is None or needle not in text:
                continue
            score = source_score(text)
            rec = {"commit": commit, "path": path, "score": score}
            hits.append(rec)
            key = (commit, path)
            if ext in CODE_EXTS and score >= 4 and key not in seen:
                seen.add(key)
                implementation_candidates.append(rec)
    needle_hits[needle] = hits

# Also inspect current text files named like leverage/cross-reaction even when the exact
# rounded headline values are not embedded in the implementation.
for path in sorted(ROOT.rglob("*")):
    if not path.is_file() or path.suffix not in TEXT_EXTS:
        continue
    rel = path.relative_to(ROOT).as_posix()
    lowname = rel.lower()
    if not any(k in lowname for k in ("leverage", "cross_reaction", "cross-reaction")):
        continue
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        continue
    score = source_score(text)
    if path.suffix in CODE_EXTS and score >= 6:
        key = (head, rel)
        if key not in seen:
            seen.add(key)
            implementation_candidates.append({"commit": head, "path": rel, "score": score})

metric_equivalence_established = False
metric_reason = (
    "No code-level historical source was recovered that simultaneously establishes "
    "the TOF/activity perturbation, finite-difference definition, economic reoptimization "
    "and raw reduced-cost leverage required by the frozen task."
)

# Conservative rule: rounded values in prose/snapshots are not enough. A candidate code
# file must be found; even then CI only marks equivalence if the file visibly contains
# both a TOF/activity term and an optimization/reoptimization term and a logarithmic
# elasticity construction.
verified_candidates: list[dict[str, object]] = []
for rec in implementation_candidates:
    text = show_text(str(rec["commit"]), str(rec["path"]))
    if text is None and str(rec["commit"]) == head:
        try:
            text = (ROOT / str(rec["path"])).read_text(encoding="utf-8")
        except Exception:
            text = None
    if not text:
        continue
    low = text.lower()
    has_activity = ("tof" in low or "activity" in low)
    has_opt = ("reopt" in low or "optimiz" in low)
    has_log = ("dln" in low or "d ln" in low or "np.log" in low or "log(" in low)
    if has_activity and has_opt and has_log:
        verified_candidates.append(rec)

if len(verified_candidates) == 1:
    metric_equivalence_established = True
    metric_reason = "Exactly one code-level historical implementation candidate satisfies the conservative structural checks."
elif len(verified_candidates) > 1:
    metric_reason = "Multiple code-level candidates satisfy structural checks; CI cannot prove which one generated the historical metric without an immutable source pointer."

harness_available = all(current_presence.values())
if not metric_equivalence_established:
    classification = "METRIC_EQUIVALENCE_NOT_ESTABLISHED"
elif not harness_available:
    classification = "FINAL1_1_CALCULATION_FAILED"
else:
    # The frozen task requires executing the exact recovered implementation, not a newly
    # reconstructed proxy. This probe intentionally refuses to guess the driver call.
    classification = "FINAL1_1_CALCULATION_FAILED"
    metric_reason += " The required exact driver invocation is not encoded in the repository; no substitute calculation was run."

report = {
    "classification": classification,
    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    "git_head": head,
    "frozen_constants": {
        "meoh_ch4_suppression_leverage": MEOH_CH4,
        "denominator_fractions": DENOM,
        "canonical_run_anchor": "outputs/nh3_final_20260905T134204Z",
    },
    "current_presence": current_presence,
    "current_hashes": current_hashes,
    "filename_history": filename_history,
    "historical_string_hits": needle_hits,
    "implementation_candidates": implementation_candidates,
    "verified_candidates": verified_candidates,
    "metric_equivalence_established": metric_equivalence_established,
    "metric_reason": metric_reason,
    "harness_available_in_ci": harness_available,
    "normalized_final1_1_values": None,
    "meoh_over_nh3_ratios": None,
    "scientific_rule": "No new proxy metric and no cost-ratio rescaling of the historical 273-410 result.",
}

(OUT / "f9a_ci_revalidation.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
(OUT / "classification.txt").write_text(classification + "\n", encoding="utf-8")

lines = [
    "# F9A FINAL-1.1 GitHub Actions revalidation attempt",
    "",
    f"Classification: **{classification}**",
    "",
    f"Git HEAD: `{head}`",
    "",
    "## CI availability",
    "",
]
for p, ok in current_presence.items():
    lines.append(f"- `{p}`: {'present' if ok else 'missing'}")
lines += [
    "",
    "## Metric-equivalence audit",
    "",
    metric_reason,
    "",
    f"Code-level implementation candidates: **{len(implementation_candidates)}**; conservatively verified candidates: **{len(verified_candidates)}**.",
    "",
    "Rounded manuscript values or prose summaries do not establish metric equivalence by themselves.",
    "",
    "## Scientific decision",
    "",
]
if classification == "METRIC_EQUIVALENCE_NOT_ESTABLISHED":
    lines.append("F9A remains qualitative/HOLD. No FINAL-1.1 quantitative ratio was generated.")
elif classification == "FINAL1_1_CALCULATION_FAILED":
    lines.append("The exact metric may be partly recoverable, but the frozen FINAL-1.1 calculation could not be executed safely in this CI checkout. F9A remains HOLD.")
else:
    lines.append("PASS_REVALIDATED")
lines += [
    "",
    "This CI probe intentionally does not rescale the old 273–410 range by the change in Fe cost.",
]
(OUT / "CROSS_REACTION_FINAL1_1_CI_ATTEMPT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

print(json.dumps({
    "classification": classification,
    "metric_equivalence_established": metric_equivalence_established,
    "harness_available_in_ci": harness_available,
    "implementation_candidates": len(implementation_candidates),
    "verified_candidates": len(verified_candidates),
}, indent=2))
