"""Time and cost ledger of the AI pipeline: one row per stage per reaction (ledger.csv)."""
import csv, sys, time
from datetime import datetime
from pathlib import Path
L = Path(__file__).resolve().parent / "ledger.csv"
F = ["reaction", "stage", "start", "end", "seconds", "llm_tokens", "llm_cost_usd", "note"]
def log(reaction, stage, start, end, tokens=0, cost=0.0, note=""):
    new = not L.exists()
    with L.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, F)
        if new: w.writeheader()
        s = datetime.fromisoformat(start); e = datetime.fromisoformat(end)
        w.writerow(dict(reaction=reaction, stage=stage, start=start, end=end, seconds=round((e - s).total_seconds()),
                        llm_tokens=tokens, llm_cost_usd=round(cost, 3), note=note))
if __name__ == "__main__":
    log(*sys.argv[1:5], *(sys.argv[5:]))
