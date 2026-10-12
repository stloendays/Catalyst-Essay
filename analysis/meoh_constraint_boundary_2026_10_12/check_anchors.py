"""Reproduction anchors of Task A and Task B; exits 1 on any failure.

  1. The quick check the task started from (reversals, regret > 5 %, papers) and S6 28 / 40.
  2. The frozen field result (analysis/meoh_literature_inversion_2026_10_05): summary.json primary, its paper-cluster
     bootstrap interval, every scenario of its limit sweep, the S6, S4 and without-Bansode variants, the X*S and
     S_MeOH leaderboards, and mismatch_kinds.json (kinds and leader differences).
  3. Task B's STY baseline equals 40 minus Task A's disagreements in every scenario.
  4. Pre-registration: PROTOCOL_B.md was committed before run_rules.py and any rules_* output existed, in a commit
     that touches no Task B code or output (needs the git history; skipped with a note when there is none).
"""
import json
import subprocess
import sys

import pandas as pd

from common import HERE, INV, REPO

QUICK = {"lim4": (28, 25, 23), "lim10": (24, 18, 18), "lim20": (19, 10, 13), "lim30": (16, 8, 10), "S5": (15, 7, 9)}
fails, passes = [], []


def check(name, got, want):
    (passes if got == want else fails).append(f"{name}: got {got!r}, want {want!r}")


def close(name, got, want, rtol=1e-9):
    ok = abs(got - want) <= rtol * max(abs(want), 1e-300)
    (passes if ok else fails).append(f"{name}: got {got!r}, want {want!r}")


def main():
    a = json.loads((HERE / "boundary_summary.json").read_text(encoding="utf-8"))["scenarios"]
    b = json.loads((HERE / "rules_summary.json").read_text(encoding="utf-8"))
    fz = json.loads((INV / "summary.json").read_text(encoding="utf-8"))
    mk = json.loads((INV / "mismatch_kinds.json").read_text(encoding="utf-8"))

    # 1. quick check
    for s, (rev, gt5, pap) in QUICK.items():
        c = a[s]["counts"]
        check(f"quick {s}", (c["different_leader"], c["gt5pct"], c["papers"]), (rev, gt5, pap))
    check("quick S6 different leader", a["S6"]["counts"]["different_leader"], 28)

    # 2. frozen field result
    p, c5 = fz["primary"], a["S5"]["counts"]
    check("frozen S5 groups / papers", (c5["groups"], a["S5"]["papers"]), (p["groups"], p["papers"]))
    check("frozen S5 different leader", c5["different_leader"], p["top1_mismatch_groups"])
    check("frozen S5 papers", c5["papers"], p["papers_with_mismatch"])
    for k in ("gt1pct", "gt5pct", "gt10pct"):
        check(f"frozen S5 regret {k}", c5[k], p["regret_bins"][k]["groups"])
    check("frozen S5 papers > 5 %", c5["papers_gt5pct"], p["regret_bins"]["gt5pct"]["papers"])
    close("frozen S5 regret max", a["S5"]["regret"]["max"], p["regret_max"], 1e-9)
    close("frozen S5 median regret of disagreements", a["S5"]["regret"]["median_of_disagreements"],
          p["regret_median_mismatched"], 1e-9)
    for i in (0, 1):
        close(f"frozen S5 bootstrap ci95[{i}]", a["S5"]["bootstrap"]["different_leader"]["ci95"][i],
              p["bootstrap"]["ci95"][i], 1e-12)
    for L in (4, 5, 6, 8, 10, 12, 15, 20, 25, 30):
        f, s = fz["limit_sweep"][f"{L}%"], a[f"lim{L}"]
        check(f"frozen lim{L} different leader / papers / infeasible",
              (s["counts"]["different_leader"], s["counts"]["papers"], s["candidates_infeasible"]),
              (f["top1_mismatch_groups"], f["papers_with_mismatch"], f["candidates_infeasible"]))
        check(f"frozen lim{L} regret bins",
              tuple(s["counts"][k] for k in ("gt1pct", "gt5pct", "gt10pct")),
              tuple(f["regret_bins"][k]["groups"] for k in ("gt1pct", "gt5pct", "gt10pct")))
        close(f"frozen lim{L} regret max", s["regret"]["max"], f["regret_max"], 1e-9)
    v = fz["variants"]
    check("frozen S6 different leader", a["S6"]["counts"]["different_leader"], v["inlet_limit_6.86pct"]["top1_mismatch_groups"])
    check("frozen S4 different leader", a["S4_uncapped"]["counts"]["different_leader"],
          v["conversion_uncapped"]["top1_mismatch_groups"])
    check("frozen S5 without Bansode", a["S5"]["without_bansode"]["different_leader"],
          v["without_paper_with_most_groups"]["top1_mismatch_groups"])
    fx = b["per_scenario"]["S5"]["fixed_rules"]
    check("frozen leaderboard X*S", 40 - fx["X*S"]["correct"], v["leaderboard_X_times_S"]["top1_mismatch_groups"])
    check("frozen leaderboard S_MeOH", 40 - fx["S"]["correct"], v["leaderboard_S_MeOH"]["top1_mismatch_groups"])
    k = a["S5"]["kinds"]
    for tag in ("cat_sameT", "cat_and_T", "T", "same_record", "other_catalyst", "other_temperature"):
        for f_ in ("groups", "gt5pct", "gt10pct", "papers"):
            check(f"frozen kinds {tag} {f_}", k[tag][f_], mk[tag][f_])
    m, ld = a["S5"]["mechanism"], mk["leader_differences"]
    for f_ in ("plant_more_selective", "plant_less_CO", "plant_cooler", "plant_higher_conversion"):
        check(f"frozen leader differences {f_}", m[f_], ld[f_.replace("plant_", "plant_leader_")])

    # 3. Task B baseline = Task A
    for s, d in b["per_scenario"].items():
        check(f"B STY baseline {s}", d["sty_baseline"]["correct"], 40 - a[s]["counts"]["different_leader"])

    # 4. pre-registration order
    rel = HERE.relative_to(REPO).as_posix()
    try:
        def first_commit(path):
            out = subprocess.run(["git", "log", "--diff-filter=A", "--format=%H", "--", path], cwd=REPO,
                                 capture_output=True, text=True, check=True).stdout.split()
            return out[-1] if out else None
        proto, rules = first_commit(f"{rel}/PROTOCOL_B.md"), first_commit(f"{rel}/run_rules.py")
        if proto is None or rules is None:
            raise RuntimeError("history not available")
        touched = subprocess.run(["git", "show", "--name-only", "--format=", proto], cwd=REPO, capture_output=True,
                                 text=True, check=True).stdout.split()
        before = subprocess.run(["git", "merge-base", "--is-ancestor", proto, rules], cwd=REPO).returncode == 0
        check("protocol committed before run_rules.py", before and proto != rules, True)
        check("protocol commit touches no Task B code or output",
              [t for t in touched if t.startswith(f"{rel}/") and t != f"{rel}/PROTOCOL_B.md"], [])
    except (RuntimeError, subprocess.CalledProcessError, FileNotFoundError) as e:
        passes.append(f"pre-registration order not checked ({e})")

    for line in passes:
        print("ok  ", line)
    for line in fails:
        print("FAIL", line)
    print(f"{len(passes)} passed, {len(fails)} failed")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
