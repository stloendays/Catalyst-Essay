"""Score an agent run on the masked database against the full truth, with the hand-built plant model (../).

Usage: python evaluate_agent.py <run_name> <rxn> <chosen rec_id>
Prints: plant cost and rank of the chosen record under the reference model, regret vs the cheapest record,
reveal budget used, and the same regret for three baselines with the same information:
  lab-rate leader (highest reactant conversion rate x nothing else), lab-conversion leader, and
  random reveal (selectivity of a random 30 % of records revealed, cheapest of those chosen; 2,000 draws).
"""
import json
import random
import statistics as st
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import analyze as an  # noqa: E402
import plant_models as pm  # noqa: E402


def main(run, rxn, chosen):
    truth = json.loads((HERE / "db" / "truth.json").read_text(encoding="utf-8"))[rxn]
    rows = an.load(rxn)
    key = {(r["paper"], int(r["idx"])): r for r in rows}
    cost = {}
    for t in truth:
        r = key[(t["_true_paper"], int(t["_idx"]))]
        r["rec"]["xeq_lab"] = pm.lab_xeq(rxn, r["rec"])
        cost[t["rec_id"]] = an.cost(rxn, r["rec"])
    ids = sorted(cost, key=cost.get)
    best = ids[0]
    led = json.loads((HERE / "runs" / run / "ledger.json").read_text(encoding="utf-8"))

    def regret(i):
        return (cost[i] - cost[best]) / cost[best]

    by_rate = max(truth, key=lambda t: t["lab_reactant_conversion_rate_mol_per_kg_h"])["rec_id"]
    by_conv = max(truth, key=lambda t: t["lab_conversion"])["rec_id"]
    rnd = []
    rng = random.Random(0)
    k = max(1, int(0.3 * len(truth)))
    for _ in range(2000):
        pick = rng.sample(ids, k)
        rnd.append(regret(min(pick, key=cost.get)))
    out = dict(run=run, rxn=rxn, records=len(truth), best=best, best_cost=round(cost[best], 2),
               chosen=chosen, chosen_cost=round(cost[chosen], 2), chosen_rank=ids.index(chosen) + 1,
               chosen_regret_pct=round(100 * regret(chosen), 3),
               baseline_rate_leader=dict(rec=by_rate, rank=ids.index(by_rate) + 1, regret_pct=round(100 * regret(by_rate), 3)),
               baseline_conversion_leader=dict(rec=by_conv, rank=ids.index(by_conv) + 1, regret_pct=round(100 * regret(by_conv), 3)),
               baseline_random_reveal_30pct=dict(median_regret_pct=round(100 * st.median(rnd), 3),
                                                 p90_regret_pct=round(100 * sorted(rnd)[int(0.9 * len(rnd))], 3)),
               reveal_spent=led.get("reveal_spent"), reveal_budget=led.get("reveal_budget"),
               wall_minutes=led.get("wall_minutes"), tokens_total=led.get("tokens_total"),
               usd_equivalent=led.get("usd_equivalent_at_gpt55_list_price"))
    (HERE / "runs" / run / "evaluation.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main(*sys.argv[1:4])
