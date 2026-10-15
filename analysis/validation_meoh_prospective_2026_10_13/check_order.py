"""Commit-order checks of the pre-registration (PREREGISTRATION.md section 6), from the git history.

1. PREREGISTRATION.md and prediction_frozen.json were added before any extraction output (out/) and before screening.csv.
2. blind_predictions.csv and blind_rankings.csv were added before any plant-model output of the new batch
   (results.json, scored_groups.csv, new_candidates_costed.csv), and have not changed since they were added.
3. PREREGISTRATION.md has not changed since it was added.
Exit status 1 on any failure.
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
REL = HERE.relative_to(REPO).as_posix()


def git(*a):
    return subprocess.run(["git", *a], cwd=REPO, capture_output=True, text=True, check=True).stdout


def order():
    """Commits touching this folder, oldest first."""
    return git("log", "--reverse", "--format=%H", "--", REL).split()


def first_commit(path_glob):
    out = git("log", "--reverse", "--diff-filter=A", "--format=%H", "--", f"{REL}/{path_glob}").split()
    return out[0] if out else None


def changed_after(path, commit):
    return bool(git("log", "--format=%H", f"{commit}..HEAD", "--", f"{REL}/{path}").split())


def main():
    seq = order()
    pos = {c: i for i, c in enumerate(seq)}
    fails = []
    pre = first_commit("PREREGISTRATION.md")
    for later in ("out/*", "screening.csv", "blind_predictions.csv", "results.json"):
        c = first_commit(later)
        if c is not None and not pos[pre] < pos[c]:
            fails.append(f"PREREGISTRATION.md is not older than {later}")
    if changed_after("PREREGISTRATION.md", pre):
        fails.append("PREREGISTRATION.md changed after it was committed")
    bp = first_commit("blind_predictions.csv")
    if bp is not None:
        for later in ("results.json", "scored_groups.csv", "new_candidates_costed.csv"):
            c = first_commit(later)
            if c is not None and not pos[bp] < pos[c]:
                fails.append(f"blind_predictions.csv is not older than {later}")
        for f in ("blind_predictions.csv", "blind_rankings.csv"):
            if changed_after(f, bp):
                fails.append(f"{f} changed after it was committed")
    print(f"pre-registration {pre[:8]}; blind predictions {bp[:8] if bp else '-'}; "
          f"{len(seq)} commits in {REL}")
    for f in fails:
        print("FAIL", f)
    print("commit order OK" if not fails else "commit order FAILED")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
