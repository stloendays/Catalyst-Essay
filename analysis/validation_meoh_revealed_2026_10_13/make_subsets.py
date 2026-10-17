"""Write the pre-registered subsets (composition only; no STY, conversion, selectivity or cost is read or written).

For each cohort (printed = frozen primary, 351 rows / groups with >= 2 entries: 40 groups, 310 entries, 28 papers;
extended = every entry incl. plot readings, 996 rows / 83 groups, 909 entries, 44 papers) the script writes one row per
entry of a group with >= 2 entries: group, doi, catalyst, family, Cu-based, scale class, H3-alt class, and the H1 /
H1-broad membership of its group. Run before any outcome is computed; its outputs are committed with
PREREGISTRATION.md.

Outputs: subsets_printed.csv, subsets_extended.csv, subsets_summary.json
"""
import json
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
INV = REPO / "analysis" / "meoh_literature_inversion_2026_10_05"
sys.path.insert(0, str(HERE))
from families import cu_based, family, scale_class, scale_class_alt  # noqa: E402

COHORTS = {"printed": INV / "literature_candidates.csv", "extended": INV / "literature_candidates_all_entries.csv"}
KEEP = ["group", "doi", "entry", "catalyst"]          # composition-only columns


def subsets(path):
    d = pd.read_csv(path, usecols=KEEP)
    n = d.groupby("group").size()
    d = d[d.group.isin(n[n >= 2].index)].copy()
    d["family"] = [family(c, doi) for c, doi in zip(d.catalyst, d.doi)]
    d["cu_based"] = d.family.map(cu_based)
    d["scale"] = [scale_class(c, doi) for c, doi in zip(d.catalyst, d.doi)]
    d["scale_alt"] = [scale_class_alt(c, doi) for c, doi in zip(d.catalyst, d.doi)]
    h1, h1b = {}, {}
    for g, gg in d.groupby("group"):
        fam = set(gg.family) - {"blank"}
        h1[g] = "CuZnAl" in fam and len(fam - {"CuZnAl"}) > 0
        h1b[g] = any(cu_based(f) for f in fam) and any(not cu_based(f) for f in fam)
    d["h1_group"] = d.group.map(h1)
    d["h1_broad_group"] = d.group.map(h1b)
    return d


def main():
    summ = {}
    for name, path in COHORTS.items():
        d = subsets(path)
        d.to_csv(HERE / f"subsets_{name}.csv", index=False)
        nb = d[d.family != "blank"]
        summ[name] = dict(
            groups=int(d.group.nunique()), entries=int(len(d)), papers=int(d.doi.nunique()),
            blank_entries=int((d.family == "blank").sum()),
            family_entries={k: int(v) for k, v in nb.family.value_counts().sort_index().items()},
            family_papers={k: int(v) for k, v in nb.groupby("family").doi.nunique().sort_index().items()},
            scale_entries={k: int(v) for k, v in nb.scale.value_counts().sort_index().items()},
            scale_papers={k: int(v) for k, v in nb.groupby("scale").doi.nunique().sort_index().items()},
            scale_alt_entries={k: int(v) for k, v in nb.scale_alt.value_counts().sort_index().items()},
            h1_groups=sorted(d.loc[d.h1_group, "group"].unique().tolist()),
            h1_papers=int(d.loc[d.h1_group, "doi"].nunique()),
            h1_broad_groups=sorted(d.loc[d.h1_broad_group, "group"].unique().tolist()),
            h1_broad_papers=int(d.loc[d.h1_broad_group, "doi"].nunique()))
    (HERE / "subsets_summary.json").write_text(json.dumps(summ, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summ, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
