"""The extraction paper set (paper_set.txt): DOI -> reference set used to score it (gothe, themecat, suvarna, review)."""
from __future__ import annotations

from pathlib import Path

PAPER_SET = Path(__file__).resolve().parent / "paper_set.txt"


def load_paper_set() -> dict[str, str]:
    out = {}
    for line in PAPER_SET.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            doi, ref = line.split()
            out[doi.lower()] = ref
    return out
