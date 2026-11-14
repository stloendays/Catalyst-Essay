"""Cell table of the REVEAL runs, in the layout of DISCOVER-V2-STOP (docs/DISCOVER_V2_STOP_RESULTS_2026-09-26.md):
per reaction x budget x arm x model: runs, correct, median/max regret, median spend, median units at which the rule
first held (computed in every arm, shown to the agent only in gate/hard), runs paying after the rule, median and max
post-rule spend, reveals with flip value 0 (could not change the choice), tokens per run.
Writes reveal/cells.csv and reveal/cells.md."""
import csv
import json
import statistics as st
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
R = HERE / "reveal"


def med(xs):
    xs = [x for x in xs if x is not None]
    return st.median(xs) if xs else None


def main():
    src = R / "agent_runs_replayed.jsonl" if (R / "agent_runs_replayed.jsonl").exists() else R / "agent_runs.jsonl"
    runs = [json.loads(l) for l in open(src, encoding="utf-8")]
    cells = defaultdict(list)
    for r in runs:
        cells[(r["rxn"], str(r.get("budget_frac", r.get("budget"))), r["arm"], r["model"])].append(r)
    rows = []
    for (rx, b, arm, model), rs in sorted(cells.items()):
        flip0 = n_rev = 0
        for r in rs:
            p = R / "runs" / f"{rx}_{b}_{arm}_{model}_{r['seed']}.json"
            if p.exists():
                steps = json.loads(p.read_text(encoding="utf-8"))["steps"]
                rev = [s for s in steps if s["action"] == "reveal"]
                n_rev += len(rev)
                flip0 += sum(1 for s in rev if s["flip"] == 0)
        armed = [r["armed_at"] for r in rs if r["armed_at"] is not None]
        post = [r["post_rule"] for r in rs if r["post_rule"] is not None]
        rows.append(dict(rxn=rx, budget=b, arm=arm, model=model, runs=len(rs), correct=sum(r["correct"] for r in rs),
                         median_regret_pct=med([r["regret_pct"] for r in rs]), max_regret_pct=max(r["regret_pct"] or 0 for r in rs),
                         median_spent=med([r["spent"] for r in rs]), rule_reached=len(armed), median_armed=med(armed),
                         paid_after_rule=sum(1 for x in post if x > 0), median_post_rule=med(post), max_post_rule=max(post) if post else None,
                         reveals=n_rev, reveals_flip0=flip0, median_tokens=med([r["tokens"] for r in rs]),
                         median_turns=med([r["turns"] for r in rs])))
    with open(R / "cells.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    hdr = list(rows[0])
    md = ["| " + " | ".join(hdr) + " |", "|" + "---|" * len(hdr)] + ["| " + " | ".join(str(r[k]) for k in hdr) + " |" for r in rows]
    (R / "cells.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()


def replay():
    """Recompute the rule point and post-rule spend of every run from its logged reveals (same seed, same plant model),
    as the DISCOVER stopping-test replay (tools/discover/c1_stopping_test.py). Writes reveal/agent_runs_replayed.jsonl."""
    import sys
    sys.path.insert(0, str(HERE))
    import reveal_game as rg
    out = []
    for l in open(R / "agent_runs.jsonl", encoding="utf-8"):
        r = json.loads(l)
        b = str(r.get("budget_frac", r.get("budget")))
        p = R / "runs" / f"{r['rxn']}_{b}_{r['arm']}_{r['model']}_{r['seed']}.json"
        steps = json.loads(p.read_text(encoding="utf-8"))["steps"]
        env = rg.Env(r["rxn"], b, r["seed"], "none")
        for s in steps:
            if s["action"] == "reveal":
                env.reveal([dict(rec_id=s["rec_id"], field=s["field"])])
        sc = env.score(r["chosen"])
        r.update(armed_at=sc["armed_at"], post_rule=sc["post_rule"], rule_at_stop=sc["rule_at_stop"], replayed=True)
        assert sc["spent"] == r["spent"] and sc["correct"] == r["correct"], (p, sc, r)
        out.append(r)
    with open(R / "agent_runs_replayed.jsonl", "w", encoding="utf-8") as f:
        for r in out:
            f.write(json.dumps(r) + "\n")
    print("replayed", len(out))
