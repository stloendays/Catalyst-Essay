"""POST-HOC diagnostic (not preregistered), written 2026-11-14 after evaluate_builds.py reported an empty common record set for
NH3 decomposition (the three builds extracted different papers and catalyst names, so the preregistered intersection of
records is empty and the pairwise ranking Spearman is undefined).

Here every model costs the UNION of the three builds' usable records (same record mapping as evaluate_builds.common_records),
and pairwise Spearman is computed on the records that all models cost successfully. Report only; it changes no verdict.

    cfpy posthoc_union_rank.py <rxn> <run> <run> [<run> ...]   -> evaluation/<rxn>_posthoc_union_rank.json
"""
import csv
import itertools
import json
import math
import sys
import time
from pathlib import Path

from scipy.stats import spearmanr

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from evaluate_builds import load_model  # noqa: E402


def records(run):
    out = {}
    with (Path(run) / "records.csv").open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if str(r.get("usable", "True")).lower() not in ("true", "1"):
                continue
            key = (r["paper"], "".join(r["catalyst"].lower().split()), round(float(r["T_K"])))

            def num(k, fallback=None):
                v = r.get(k, fallback)
                return None if v in (None, "", "None") else float(v)
            out["|".join(map(str, key))] = dict(paper=r["paper"], idx=int(r.get("idx", 0)), catalyst=r["catalyst"], T_K=num("T_K"),
                                                P_bar=num("P_bar"), X=num("X"), S=num("S"), r=num("r", r.get("r_kg_kg_h")),
                                                y_key=num("y_key"), y_cofeed=num("y_h2", r.get("y_cofeed")), t_cycle_h=num("t_cycle_h"),
                                                components=json.loads(r.get("elements", r.get("components", "[]"))))
    return out


def main(rx, runs):
    union, origin = {}, {}
    for run in runs:
        for k, v in records(run).items():
            union.setdefault(k, v)
            origin.setdefault(k, []).append(Path(run).name)
    costs, seconds = {}, {}
    for run in runs:
        m = load_model(run)
        t = time.time()
        c = {}
        for k, x in union.items():
            try:
                c[k] = float(m.plant_cost(dict(x))["cost_usd_per_t"])
            except Exception:  # noqa: BLE001
                c[k] = math.nan
        costs[Path(run).name] = c
        seconds[Path(run).name] = round(time.time() - t, 1)
    names = list(costs)
    ok = [k for k in union if all(math.isfinite(costs[n][k]) for n in names)]
    pair = {f"{a} vs {b}": round(spearmanr([costs[a][k] for k in ok], [costs[b][k] for k in ok]).statistic, 3)
            for a, b in itertools.combinations(names, 2)} if len(ok) > 2 else {}
    cheapest = {n: (lambda k: dict(key=k, catalyst=union[k]["catalyst"], cost=costs[n][k]))(min(ok, key=lambda k: costs[n][k]))
                for n in names} if ok else {}
    out = dict(rxn=rx, status="post-hoc diagnostic, not preregistered; changes no verdict", union_records=len(union),
               records_per_build={n: sum(1 for k in union if n in origin[k]) for n in names},
               shared_by_all=sum(1 for k in union if len(origin[k]) == len(runs)),
               costed_by_each={n: sum(1 for k in union if math.isfinite(costs[n][k])) for n in names},
               costed_by_all=len(ok), pairwise_spearman=pair, pairwise_ge08=all(v >= 0.8 for v in pair.values()) if pair else None,
               cheapest_on_union=cheapest, seconds=seconds)
    p = HERE / "evaluation" / f"{rx}_posthoc_union_rank.json"
    p.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
