"""Log one human intervention in an AI run (the supervisor asked for every intervention to be counted).

Usage: python log_human.py <run_dir> <stage> <type> <minutes> "<note>"
type: review | correction | missing_data | model_change | rerun | rejection | infrastructure
'infrastructure' = a fix to the fixed tools (not to the agent's scientific work); reported separately.
"""
import csv
import sys
from datetime import datetime
from pathlib import Path

TYPES = {"review", "correction", "missing_data", "model_change", "rerun", "rejection", "infrastructure"}


def log(run_dir, stage, typ, minutes, note):
    assert typ in TYPES, typ
    p = Path(run_dir) / "human_log.csv"
    new = not p.exists()
    with open(p, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["time", "stage", "type", "minutes", "note"])
        w.writerow([datetime.now().isoformat(timespec="seconds"), stage, typ, minutes, note])


if __name__ == "__main__":
    log(*sys.argv[1:6])
