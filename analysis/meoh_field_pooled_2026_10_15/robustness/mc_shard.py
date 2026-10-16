"""Exact model runs of the combined-set noise analysis, split into shards: the frozen script's enumerate / compute /
merge workflow (analysis/meoh_main_result_stats_2026_10_06/run_main_result_stats.py) with the S6 wrapper's run
(meoh_s6_robustness_2026_10_13/run_stats_wrapper.exact_cost_both: one conversion-capped sweep gives the S6 cost and
the S5 cost of the same perturbed entry).

    MEOH_FIELD_SET=combined STATS_MODE=enumerate STATS_JOBS_OUT=JOBS python run_stats_wrapper.py s6   (list the runs)
    python mc_shard.py compute JOBS SHARD N OUT     jobs[SHARD::N], STATS_WORKERS processes -> OUT (key,cost_s6,cost_s5)
    python mc_shard.py merge PART...                S6 costs into stats_s6/exact_cache.csv.gz, S5 costs into
                                                    stats_s6/s5_crosscheck.csv.gz
then run_stats_wrapper.py s6 again (enumerate for the draws, compute, merge, and the final run reads the cache).
"""
import os
import pickle
import sys
from multiprocessing import Pool

os.environ["MEOH_FIELD_SET"] = "combined"
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
CMD, ARGS = sys.argv[1], sys.argv[2:]
sys.argv = [sys.argv[0], "s6"]                       # the wrapper reads its treatment from argv
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "meoh_s6_robustness_2026_10_13"))
import pandas as pd  # noqa: E402

import run_stats_wrapper as W  # noqa: E402

R = W.R


def compute(jobs_file, shard, nshards, out):
    with open(jobs_file, "rb") as f:
        jobs = pickle.load(f)["jobs"][int(shard)::int(nshards)]
    with Pool(R.WORKERS) as pool:
        res = pool.map(W.exact_cost_both, [j for _, j in jobs], chunksize=2)
    pd.DataFrame(dict(key=[k for k, _ in jobs], cost_s6=[r[1] for r in res], cost_s5=[r[0] for r in res])).to_csv(
        out, index=False, float_format="%.12g")
    print(f"shard {shard}/{nshards}: {len(jobs)} runs -> {out}", flush=True)


def merge(parts):
    cache = R.exact_cache()
    n0 = len(cache)
    for p in parts:
        t = pd.read_csv(p, dtype={"key": str, "cost_s6": float, "cost_s5": float})
        cache.update(zip(t.key, t.cost_s6))
        W._S5_SEEN.update(zip(t.key, t.cost_s5))
    R.save_cache()
    W.save_crosscheck()
    print(f"S6 cache {n0} -> {len(cache)} runs; S5 runs recorded {len(W._S5_SEEN)}", flush=True)


if __name__ == "__main__":
    {"compute": lambda: compute(*ARGS), "merge": lambda: merge(ARGS)}[CMD]()
