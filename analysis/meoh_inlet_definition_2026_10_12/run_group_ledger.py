"""How the 83 comparison groups of the all-entries cohort become the 40 groups of the printed primary (supervisor Q2).

Inputs: the frozen candidate tables of analysis/meoh_literature_inversion_2026_10_05
  literature_candidates_all_entries.csv   every entry, plot readings included (scored: 909 entries, 83 groups, 44 papers)
  literature_candidates.csv               printed-value cohort (scored: 310 entries, 40 groups, 28 papers)
A group is scored when it holds at least two entries with a finite cost (meoh_candidates.aggregate).

group_ledger.csv: every scored all-entries group with its paper, entries, printed entries (entries of the printed
cohort in that group), plot-read entries, whether it is scored in the printed primary and, if not, why:
  paper without printed values   the paper has no entry in the printed cohort
  fewer than 2 printed entries   the paper has printed entries, but this group has 0 or 1
  other                          two or more printed entries and still not scored (none expected)

Checks: the grouping rule (same paper, pressure, H2/CO2, space velocity) is the same in both cohorts: (1) the group key
of every row of both tables is rebuilt from doi, P_bar, h2_co2 and ghsv_key exactly as meoh_candidates.build_candidates
writes it; (2) every printed-cohort entry is in the all-entries table under the same group; (3) rebuilding both cohorts
from agent/extraction/out/records_normalized.csv with build_candidates (printed_only True / False, the only difference)
gives the same entries and groups as the frozen tables. Also: the all-entries result under S5 and under the 6.86 %
inlet limit from the frozen cost columns (frozen: 35/83 and 54/82), split by kept and dropped groups.

Outputs (this folder): group_ledger.csv, ledger_summary.json.
"""
import json

import numpy as np
import pandas as pd

from common import BANSODE, CANDIDATES, CANDIDATES_ALL, HERE, aggregate, classify
from meoh_candidates import build_candidates, read_records

REASONS = ("paper without printed values", "fewer than 2 printed entries", "other")


def group_key(f):
    return (f.doi + " | " + f.P_bar.map("{:g} bar".format) + " | H2/CO2 " + f.h2_co2.map("{:.3g}".format) + " | "
            + f.ghsv_key)


def scored_groups(f, col="cost_recycled_opt"):
    n = f[np.isfinite(f[col].astype(float))].groupby("group").size()
    return n[n >= 2]


def grouping_checks(p, a):
    out = dict(group_key_rebuilt_printed=bool((group_key(p) == p.group).all()),
               group_key_rebuilt_all=bool((group_key(a) == a.group).all()))
    m = p.merge(a[["doi", "entry", "catalyst", "T_C", "group"]], on=["doi", "entry", "catalyst", "T_C"], how="left",
                suffixes=("", "_all"), validate="one_to_one")
    out["printed_entries_found_in_all_entries"] = int(m.group_all.notna().sum())
    out["printed_entries"] = len(p)
    out["printed_entries_same_group_in_all_entries"] = int((m.group == m.group_all).sum())
    rec = read_records()
    for name, flag, frozen in (("printed", True, p), ("all", False, a)):
        b = build_candidates(rec, printed_only=flag)
        k = lambda f: set(zip(f.doi, f.entry, f.catalyst, f.group))  # noqa: E731
        out[f"rebuilt_from_records_{name}_identical"] = bool(k(b) == k(frozen) and len(b) == len(frozen))
    out["identical"] = all(v for k, v in out.items() if isinstance(v, bool)) and (
        out["printed_entries"] == out["printed_entries_found_in_all_entries"]
        == out["printed_entries_same_group_in_all_entries"])
    if not out["identical"]:
        raise SystemExit(f"STOP: grouping differs between cohorts: {out}")
    return out


def result(f, col, groups=None):
    gm, s = aggregate(f, col, up_col="STY")
    gm, k = classify(f, gm, col)
    if groups is not None:
        gm = gm[gm.group.isin(groups)]
    m = gm[gm.top1_mismatch]
    return gm, dict(groups=len(gm), different_leader=len(m), gt5pct=int((m.regret > 0.05).sum()),
                    papers=int(gm.doi.nunique()), papers_with_disagreement=int(m.doi.nunique()),
                    entries=int(gm.n.sum()))


def main():
    p, a = pd.read_csv(CANDIDATES), pd.read_csv(CANDIDATES_ALL)
    checks = grouping_checks(p, a)
    A, P = scored_groups(a), scored_groups(p)
    if set(P.index) - set(A.index):
        raise SystemExit("STOP: a printed-cohort group is not an all-entries group")
    papers_printed = set(p.doi)
    n_printed = p.groupby("group").size()
    g_all = a.groupby("group")
    rows = []
    for g in A.index:
        x = g_all.get_group(g)
        npr = int(n_printed.get(g, 0))
        scored = g in P.index
        if scored:
            reason = ""
        elif x.doi.iloc[0] not in papers_printed:
            reason = REASONS[0]
        elif npr < 2:
            reason = REASONS[1]
        else:
            reason = REASONS[2]
        rows.append(dict(group=g, doi=x.doi.iloc[0], P_bar=x.P_bar.iloc[0], h2_co2=x.h2_co2.iloc[0],
                         ghsv_key=x.ghsv_key.iloc[0], entries=len(x), printed_entries=npr,
                         printed_entries_scored=int(P.get(g, 0)),
                         plot_read_entries=int(x.plot_read.sum()),
                         nonprinted_other_entries=int((~x.printed & ~x.plot_read).sum()),
                         catalysts=int(x.catalyst_key.nunique()), sty_basis_all_entries=x.sty_basis.iloc[0],
                         scored_in_printed_primary=scored, reason_not_scored=reason))
    led = pd.DataFrame(rows).sort_values(["scored_in_printed_primary", "doi", "group"], ascending=[False, True, True])

    # all-entries result, frozen columns; split by groups kept / dropped in the printed primary
    gm_s5, s5 = result(a, "cost_recycled_opt")
    gm_s6, s6 = result(a, "cost_recycled_opt_inlet")
    led = led.merge(gm_s5[["group", "top1_mismatch", "regret"]].rename(
        columns={"top1_mismatch": "all_entries_S5_different_leader", "regret": "all_entries_S5_regret"}),
        on="group", how="left")
    led = led.merge(gm_s6[["group", "top1_mismatch", "regret"]].rename(
        columns={"top1_mismatch": "all_entries_S6_different_leader", "regret": "all_entries_S6_regret"}),
        on="group", how="left")
    pr_s5 = result(p, "cost_recycled_opt")[1]
    pr_s6 = result(p, "cost_recycled_opt_inlet")[1]
    kept = set(P.index)
    dropped = set(A.index) - kept
    split = {}
    for col, tag in (("cost_recycled_opt", "S5"), ("cost_recycled_opt_inlet", "S6_6.86pct")):
        split[tag] = dict(kept_40_groups_all_entries=result(a, col, kept)[1],
                          dropped_43_groups_all_entries=result(a, col, dropped)[1],
                          printed_primary=pr_s5 if tag == "S5" else pr_s6)
    # groups that disagree in all entries but agree in the printed cohort (same group key, plot readings removed)
    pg = aggregate(p, "cost_recycled_opt")[0].set_index("group").top1_mismatch
    led["printed_S5_different_leader"] = led.group.map(pg)

    # papers
    pl = led.groupby("doi").agg(groups=("group", "size"), groups_scored=("scored_in_printed_primary", "sum"),
                                entries=("entries", "sum"), printed_entries=("printed_entries", "sum"))
    pl["kept"] = pl.groups_scored > 0
    pl["reason_dropped"] = np.where(pl.kept, "", np.where(pl.printed_entries == 0, REASONS[0],
                                                          "printed entries, but fewer than 2 in every group"))
    dropped_led = led[~led.scored_in_printed_primary]
    summary = dict(
        all_entries=dict(groups=len(A), entries=int(A.sum()), papers=int(led.doi.nunique())),
        printed_primary=dict(groups=len(P), entries=int(P.sum()), papers=int(p[p.group.isin(P.index)].doi.nunique())),
        groups_dropped=len(dropped),
        groups_dropped_by_reason={r: int((dropped_led.reason_not_scored == r).sum()) for r in REASONS},
        groups_dropped_by_printed_entries={str(k): int(v) for k, v in
                                           dropped_led.printed_entries.value_counts().sort_index().items()},
        groups_dropped_in_kept_papers=int(dropped_led.doi.isin(pl.index[pl.kept]).sum()),
        groups_dropped_in_dropped_papers=int(dropped_led.doi.isin(pl.index[~pl.kept]).sum()),
        entries_dropped=int(A.sum() - P.sum()),
        entries_in_kept_groups_all_entries=int(led[led.scored_in_printed_primary].entries.sum()),
        entries_in_kept_groups_not_printed=int(led[led.scored_in_printed_primary].entries.sum() - P.sum()),
        papers_dropped=int((~pl.kept).sum()),
        papers_dropped_by_reason={k: int(v) for k, v in pl[~pl.kept].reason_dropped.value_counts().items()},
        papers_dropped_list=pl[~pl.kept].reset_index()[["doi", "groups", "entries", "printed_entries",
                                                        "reason_dropped"]].to_dict("records"),
        bansode_groups=dict(all_entries=int((led.doi == BANSODE).sum()),
                            printed_primary=int(((led.doi == BANSODE) & led.scored_in_printed_primary).sum())),
        grouping_rule="same paper (doi), pressure, H2/CO2 and space velocity (meoh_candidates.build_candidates)",
        grouping_checks=checks,
        all_entries_result=dict(S5=s5, S6_6_86pct=s6),
        all_entries_result_split=split,
        kept_groups_disagreement_change_S5=dict(
            all_entries_yes_printed_no=int((led.all_entries_S5_different_leader.eq(True)
                                            & led.printed_S5_different_leader.eq(False)).sum()),
            all_entries_no_printed_yes=int((led.all_entries_S5_different_leader.eq(False)
                                            & led.printed_S5_different_leader.eq(True)).sum())),
    )
    led.to_csv(HERE / "group_ledger.csv", index=False, float_format="%.6g")
    (HERE / "ledger_summary.json").write_text(json.dumps(summary, indent=1, default=float) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "papers_dropped_list"}, indent=1, default=float))


if __name__ == "__main__":
    main()
