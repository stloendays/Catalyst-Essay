"""Time and cost of the AI pipeline (results/ledger_summary.json, results/ledger_stages.csv).

Wall-clock stage times come from the file timestamps written by each stage (t_*.txt, manifests, logs);
LLM tokens and seconds from token_usage.csv (every call, including the superseded first pass, is counted as spent).
Price: gpt-5.5 at USD 5 per M input and USD 30 per M output tokens, as in agent/extraction/README.md.
Manual baseline: Gartlehner et al. (randomised trial of extraction strategies): 107 min per study for single
extraction plus verification, 172 min for dual extraction; plot digitisation is not included in those figures.
"""
import csv
import json
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRICE_IN, PRICE_OUT = 5.0, 30.0


def main(stages):
    rows = list(csv.DictReader(open(HERE / "token_usage.csv", encoding="utf-8")))
    by = {}
    for r in rows:
        b = by.setdefault(r["rxn"], dict(calls=0, prompt=0, completion=0, seconds=0.0))
        b["calls"] += 1
        b["prompt"] += int(r["prompt_tokens"])
        b["completion"] += int(r["completion_tokens"])
        b["seconds"] += float(r["seconds"])
    for b in by.values():
        b["usd"] = b["prompt"] / 1e6 * PRICE_IN + b["completion"] / 1e6 * PRICE_OUT
    st_rows = []
    for name, (a, z, note) in stages.items():
        s = (datetime.fromisoformat(z) - datetime.fromisoformat(a)).total_seconds()
        st_rows.append(dict(stage=name, start=a, end=z, minutes=round(s / 60, 1), note=note))
    with open(HERE / "results" / "ledger_stages.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, list(st_rows[0]))
        w.writeheader()
        w.writerows(st_rows)
    summary = dict(llm=by, llm_total_usd=sum(b["usd"] for b in by.values()),
                   llm_total_tokens=sum(b["prompt"] + b["completion"] for b in by.values()), stages=st_rows)
    (HERE / "results" / "ledger_summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main(json.loads(Path(HERE / "stages.json").read_text(encoding="utf-8")))
