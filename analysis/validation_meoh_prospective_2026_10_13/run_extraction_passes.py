"""Run the four pre-registered extraction passes (PREREGISTRATION.md section 5) on the prospective batch through pv.py,
with the pre-registered caps (8 M tokens in total, 3 M per pass, 40 papers), and write hub_status.json for the
monitor hub. Rerunnable: papers whose raw output exists are skipped by the frozen extractor.

    python run_extraction_passes.py            # one sweep of all passes
    python run_extraction_passes.py --loop --interval 30   # retry every 30 min until all passes are complete
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
PY = sys.executable
PASSES = [("main", "raw"), ("figures", "raw_figures"), ("si", "raw_si"), ("si_figures", "raw_si_figures")]
CAPS = ["--token-cap", "8000000", "--pass-cap", "3000000", "--max-papers", "40"]
LOG = HERE / "extraction_driver.log"
STATUS = HERE / "hub_status.json"


def included() -> list[str]:
    with (HERE / "screening.csv").open(encoding="utf-8") as f:
        return [r["doi"].lower() for r in csv.DictReader(f) if r.get("decision") == "include"]


def tokens() -> int:
    p = OUT / "token_usage.csv"
    if not p.exists():
        return 0
    with p.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return sum(int(r.get("total_tokens") or 0) for r in rows)


def done(sub: str) -> int:
    d = OUT / sub
    return len(list(d.glob("*.json"))) if d.exists() else 0


def write_status(state: str, attention: list[str], finished: bool, interval: int) -> None:
    n = len(included())
    rows, tags = [], []
    for p, sub in PASSES:
        k = done(sub)
        rows.append([p, f"{k}", "主文 40 篇；其余轮次只对有对应页面的论文"])
        tags.append("done" if (p == "main" and k >= n) else "run")
    now = dt.datetime.now()
    STATUS.write_text(json.dumps({
        "updated": now.isoformat(timespec="seconds"),
        "headline": state,
        "summary": f"已用 token {tokens():,} / 8,000,000",
        "done": finished,
        "table": {"cols": ["抽取轮次", "已完成论文", "说明"], "rows": rows, "tags": tags},
        "attention": attention,
        "working": "",
        "notes": ["预注册：PREREGISTRATION.md §5；路线 API-YES → 导师 key"],
        "next": "" if finished else (now + dt.timedelta(minutes=interval)).isoformat(timespec="seconds"),
        "results": [{"label": "抽取用量", "path": str(OUT / "token_usage.csv")},
                    {"label": "驱动日志", "path": str(LOG)}],
        "error": "",
    }, ensure_ascii=False, indent=1), encoding="utf-8")


ROUTE_ARGS = ["--api-yes"]       # --advisor-key: call the advisor key directly (extract_records.py without --api-yes)


def sweep() -> tuple[bool, str]:
    """Run every pass once. Returns (all_complete, last_stop_reason)."""
    reason = ""
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    for p, sub in PASSES:
        before = done(sub)
        with LOG.open("a", encoding="utf-8") as log:
            log.write(f"\n=== {dt.datetime.now():%Y-%m-%d %H:%M:%S} pass {p} (done {before}) ===\n")
            log.flush()
            r = subprocess.run([PY, str(HERE / "pv.py"), "extract", "--pass", p, *ROUTE_ARGS, *CAPS],
                               cwd=HERE, env=env, stdout=log, stderr=subprocess.STDOUT,
                               creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        text = LOG.read_text(encoding="utf-8", errors="replace").splitlines()[-30:]
        stop = [t for t in text if t.startswith("STOP") or "no route serves" in t]
        if stop:
            reason = stop[-1]
            return False, reason
        if r.returncode != 0:
            return False, f"pass {p} exited {r.returncode}"
        errors = [t for t in text if "ERROR" in t]
        if errors:
            reason = errors[-1].strip()
    # complete when a full sweep produced no errors (every eligible paper has output or was skipped as existing)
    return reason == "", reason


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--loop", action="store_true")
    ap.add_argument("--interval", type=int, default=30, help="minutes between retries")
    ap.add_argument("--advisor-key", action="store_true",
                    help="skip API-YES (its ChatGPT-account route rejects gpt-5.5 with HTTP 400, which the router does "
                         "not treat as exhausted) and call the advisor key directly")
    a = ap.parse_args()
    if a.advisor_key:
        ROUTE_ARGS.clear()
    while True:
        write_status("抽取进行中", [], False, a.interval)
        complete, reason = sweep()
        if complete:
            write_status("四轮抽取完成，等待 Claude 做 PDF 核对、盲预测提交和打分", [
                "抽取已完成：需要 Claude 继续预注册流程（PDF 核对 → 提交盲预测 → 跑模型打分 → 开 PR）"], True, a.interval)
            return
        write_status(f"本轮停止：{reason}", [] if "no route" in reason else [f"抽取停止：{reason}"],
                     False, a.interval)
        if not a.loop or reason.startswith("STOP: token cap"):
            return
        time.sleep(a.interval * 60)


if __name__ == "__main__":
    main()
