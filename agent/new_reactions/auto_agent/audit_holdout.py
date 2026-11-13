"""Leakage audit of an AI-built-model run: did the agent touch a held-out validation source?

Checks the run's trace (web searches, opened pages, downloads, blocked downloads), sources.csv and report.md for any
held-out identifier (DOI, URL fragment, or keyword set) from holdout/<rxn>.json. A run with a hit is invalid and is
rerun (preregistration). Usage: python audit_holdout.py <run_dir> <rxn>
"""
import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def audit(run_dir, rxn, holdout_path=None, output_dir=None):
    run = Path(run_dir)
    h = json.loads((Path(holdout_path) if holdout_path else HERE / "holdout" / f"{rxn}.json").read_text(encoding="utf-8"))
    needles = [d.lower() for d in h.get("dois", [])] + [u.lower() for u in h.get("url_fragments", [])]
    keysets = [[k.lower() for k in ks] for ks in h.get("keyword_sets", [])]
    texts = []
    for l in open(run / "trace.jsonl", encoding="utf-8"):
        x = json.loads(l)
        if "web_search" in x or "holdout_blocked" in x or x.get("tool") in ("download_papers", "search_papers"):
            texts.append(("trace", json.dumps(x, ensure_ascii=False).lower()))
    for f in ("sources.csv", "report.md", "candidates.csv"):
        p = run / f
        if p.exists():
            texts.append((f, p.read_text(encoding="utf-8", errors="replace").lower()))
    hits = []
    for p in run.rglob("*"):
        if not p.is_file() or p.name == "holdout_audit.json" or "__pycache__" in p.parts:
            continue
        name = str(p.relative_to(run))
        if __import__("re").match(r".*_builds\.json", p.name.lower()):
            hits.append(dict(where=name, match="evaluation output filename"))
        if p.name != "trace.jsonl":
            try:
                if "holdout" in p.read_text(encoding="utf-8").lower():
                    hits.append(dict(where=name, match="holdout string in workspace file"))
            except (UnicodeError, OSError):
                pass
        else:
            for line in p.read_text(encoding="utf-8").splitlines():
                entry = json.loads(line)
                # System logging/download-block entries and tool definitions are not agent-written content.
                args = entry.get("args", {})
                if entry.get("tool") in ("write_file", "run_python") and "holdout" in json.dumps(args).lower():
                    hits.append(dict(where="trace agent content", match="holdout"))
                if "holdout" in str(entry.get("message", "")).lower():
                    hits.append(dict(where="trace agent message", match="holdout"))
    for where, t in texts:
        for n in needles:
            if n and n in t:
                hits.append(dict(where=where, match=n))
        for ks in keysets:
            if all(k in t for k in ks):
                hits.append(dict(where=where, match=" + ".join(ks)))
    blocked = sum(1 for l in open(run / "trace.jsonl", encoding="utf-8") if "holdout_blocked" in l)
    # candidates.csv lists search results the agent saw only as titles; a hit there alone is a warning, not a leak
    leak = [x for x in hits if x["where"] != "candidates.csv"]
    res = dict(run=str(run), rxn=rxn, leak=bool(leak), hits=hits[:30], downloads_blocked=blocked)
    dest = Path(output_dir) if output_dir else run
    dest.mkdir(exist_ok=True, parents=True)
    (dest / "holdout_audit.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(json.dumps(res, indent=1))
    return res


if __name__ == "__main__":
    audit(sys.argv[1], sys.argv[2])
