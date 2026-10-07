"""Paper leaderboards versus plant-cost leaderboards for literature CO2-to-methanol catalysts.

Input: the literature-extraction Agent's normalized records (agent/extraction/out/records_normalized.csv), used as
extracted, with no manual correction. Every record with CO2 conversion, methanol selectivity, temperature, pressure
and H2/CO2 is a candidate operating point.

Comparison groups. Within one paper, entries tested at the same pressure, H2/CO2 ratio and space velocity form one
group: the comparison the paper itself makes (catalysts, and temperatures of one catalyst, as in the frozen
four-state case). Groups with at least two entries are scored.

Paper leaderboard. Methanol space-time yield per g catalyst, the productivity figure papers use to rank catalysts.
One productivity basis per group (meoh_candidates.group_basis): the printed STY when every entry prints it, unless
printed STY / conversion-derived productivity (mass-GHSV, or density-assumed volumetric-GHSV STY) varies by more
than 3x within the group; otherwise STY derived from the mass space velocity, otherwise from the volumetric space
velocity with a bulk density of 1.0 g/mL (0.5 and 2.0 g/mL tested). Derived STY = GHSV x y_CO2 x X x S_MeOH /
22.414 x 32.042.

Plant leaderboard. Net production cost (EUR/t MeOH) from the generalized recycle-economics model
(data/meoh/meoh_general_model.py) at each entry's own pressure, H2/CO2 and temperature, with catalyst mass from the
group's productivity basis. Primary: recycled CO (central rule, capped at CO-hydrogenation equilibrium), cost-optimal
purge among the eligible purge levels, those whose reactor-inlet non-H2/CO2 fraction is within the workbook's own
limit (meoh_d01_model.SOURCE_NONREACTIVE_REFERENCE). The per-pass CO2 conversion is the laboratory value, capped where
the loop outlet would pass CO2-hydrogenation equilibrium (meoh_general_model.purge_sweep). A candidate with no eligible
purge level is infeasible and leaves both leaderboards of its group. Variants:
no nonreactive limit, the uncapped laboratory conversion (the treatment before 2026-10-07), inert CO, 2 % purge. Selectivity closure follows the workbook: S_MeOH and
S_CH4 as reported ("<1" -> 0), CO-like residual 1 - S_MeOH - S_CH4; when S_CH4 is not reported, S_CH4 = 1 - S_MeOH -
S_CO if S_CO is reported, else 0.

Self-check (Agent consistency with the hand-built case): the extracted Gothe et al. 2025 Table 4 entries are run
through the same code path; their costs must equal the frozen Table 4 results, including the four canonical states.

Parallel over candidates, INV_WORKERS processes (default 4).
Limit sweep: the primary at absolute limits of 4-30 % on the reactor-inlet non-H2/CO2 fraction (summary limit_sweep).
Isothermal catalyst comparisons: the entries of a group at one temperature that name at least two catalysts, the
paper's catalyst ranking at fixed conditions (summary isothermal, group_metrics_isothermal.csv).

Outputs (this folder): literature_candidates.csv, group_metrics.csv, group_metrics_unconstrained.csv,
group_metrics_isothermal.csv, summary.json.
"""
import json
import os
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "data" / "meoh"))
sys.path.insert(0, str(HERE))
import meoh_general_model as G  # noqa: E402

from meoh_candidates import (GOTHE_DOI, LIMIT_SWEEP, RHO_SCALES, ROW_KEYS, aggregate, bootstrap,  # noqa: E402
                             build_candidates, gothe_selfcheck, plant_costs_star, read_records)
from mismatch_kinds import base as catalyst_base  # noqa: E402

sys.path.insert(0, str(REPO / "agent"))
from selfcheck_gate import require  # noqa: E402

WORKERS = int(os.environ.get("INV_WORKERS", "4"))


def main():
    require()          # ACSA scores new candidates only after reproducing all three hand-built cases
    t0 = time.time()
    cand = build_candidates()
    n_dup = cand.attrs["duplicates_removed"]
    rows = cand[ROW_KEYS].to_dict("records")
    with Pool(WORKERS) as pool:
        res = pool.map(plant_costs_star, [(r, RHO_SCALES) for r in rows], chunksize=4)
    cand = pd.concat([cand, pd.DataFrame(res)], axis=1)
    cand["feasible"] = np.isfinite(cand.cost_recycled_opt)

    # ------------------------------------------------------------ self-check ----------------------------------
    got = cand[cand.doi == GOTHE_DOI].copy()
    check = gothe_selfcheck(got)
    selfcheck_max = float(check.abs_diff.max())
    canon = check[(check.canonical_state != "") & (check.treatment == "inert")]

    # ------------------------------------------------------------ group metrics -------------------------------
    primary_gm, primary = aggregate(cand, "cost_recycled_opt", label="primary: recycled CO, eligible optimal purge, STY leaderboard")
    unc_gm, unc = aggregate(cand, "cost_recycled_opt_unconstrained", label="recycled CO, optimal purge without the nonreactive limit")
    variants = {"recycled_opt_unconstrained": unc,
                "recycled_opt_uncapped": aggregate(cand, "cost_recycled_opt_uncapped",
                                                   label="treatment before 2026-10-07: laboratory X uncapped, no limit")[1],
                "recycled_opt_limit_ch4_n2_only": aggregate(cand, "cost_recycled_opt_limit_ch4n2",
                                                            label="diagnostic: limit on CH4 + N2 (CO not counted)")[1],
                **{f"recycled_opt_limit_x{m:g}": aggregate(cand, f"cost_recycled_opt_limit_x{m:g}",
                                                          label=f"nonreactive limit x {m:g}")[1] for m in (1.5, 2.0, 3.0)},
                "recycled_2pct": aggregate(cand, "cost_recycled_2pct", label="2 % purge (eligible)")[1],
                "recycled_2pct_unconstrained": aggregate(cand, "cost_recycled_2pct_unconstrained", label="2 % purge, unconstrained")[1],
                "inert_opt": aggregate(cand, "cost_inert_opt", label="inert CO, eligible optimal purge")[1],
                "inert_opt_unconstrained": aggregate(cand, "cost_inert_opt_unconstrained", label="inert CO, unconstrained")[1],
                "inert_2pct": aggregate(cand, "cost_inert_2pct", label="inert CO, 2 % purge (eligible)")[1]}
    for name in RHO_SCALES:
        variants[f"density_{name[3:]}"] = aggregate(cand, f"cost_recycled_opt_{name}", label=f"density {name[3:]} g/mL")[1]
    cand["XS"] = cand.X * cand.SMeOH
    variants["leaderboard_X_times_S"] = aggregate(cand, "cost_recycled_opt", up_col="XS", label="X*S leaderboard")[1]
    variants["leaderboard_X"] = aggregate(cand, "cost_recycled_opt", up_col="X", label="X leaderboard")[1]
    variants["leaderboard_S_MeOH"] = aggregate(cand, "cost_recycled_opt", up_col="SMeOH", label="S_MeOH leaderboard")[1]
    variants["printed_values_only"] = aggregate(cand[~cand.plot_read], "cost_recycled_opt", label="no plot readings")[1]
    biggest = primary_gm.groupby("doi").size().idxmax()          # paper contributing the most scored groups
    variants["without_paper_with_most_groups"] = aggregate(cand[cand.doi != biggest], "cost_recycled_opt",
                                                           label=f"without {biggest}")[1]
    variants["methanol_products_only"] = aggregate(cand[~cand.other_products], "cost_recycled_opt",
                                                   label="reported S_MeOH+S_CO+S_CH4 >= 95 %")[1]
    # limit sweep: the primary at absolute limits on the reactor-inlet non-H2/CO2 fraction
    limit_sweep = {}
    for lim in LIMIT_SWEEP:
        col = f"cost_recycled_opt_lim{lim * 100:g}"
        limit_sweep[f"{lim * 100:g}%"] = aggregate(cand, col, label=f"nonreactive limit {lim * 100:g} %")[1]
    limit_sweep["none"] = variants["recycled_opt_unconstrained"]

    # isothermal catalyst comparisons: within a group, the entries at one temperature that name at least two
    # different catalysts (the paper's catalyst ranking at fixed T, P, H2/CO2 and space velocity, as in ammonia)
    iso = cand.copy()
    iso["group"] = iso.group + " | T " + iso.T_C.round(1).map("{:g}".format)
    ncat = iso.groupby("group").catalyst.agg(lambda s: s.map(catalyst_base).nunique())
    iso = iso[iso.group.isin(ncat[ncat >= 2].index)]
    iso_gm, isothermal = aggregate(iso, "cost_recycled_opt", label="isothermal catalyst comparisons, primary")
    isothermal["bootstrap"] = bootstrap(iso_gm)
    isothermal_sweep = {f"{lim * 100:g}%": aggregate(iso, f"cost_recycled_opt_lim{lim * 100:g}",
                                                     label=f"isothermal, limit {lim * 100:g} %")[1]
                        for lim in LIMIT_SWEEP}
    isothermal_sweep["reference 6.86%"] = isothermal
    isothermal_sweep["none"] = aggregate(iso, "cost_recycled_opt_unconstrained", label="isothermal, no limit")[1]
    isothermal_sweep["uncapped, no limit (earlier treatment)"] = aggregate(
        iso, "cost_recycled_opt_uncapped", label="isothermal, uncapped, no limit")[1]
    iso_gm.to_csv(HERE / "group_metrics_isothermal.csv", index=False, float_format="%.6g")

    primary["bootstrap"] = bootstrap(primary_gm)
    unc["bootstrap"] = bootstrap(unc_gm)

    # infeasibility bookkeeping (primary treatment)
    scored_groups = cand.groupby("group").size()
    in_groups = cand[cand.group.isin(scored_groups[scored_groups >= 2].index)]
    infeasible = dict(
        candidates=int((~cand.feasible).sum()), of=int(len(cand)),
        candidates_in_groups_of_two_or_more=int((~in_groups.feasible).sum()), of_in_groups=int(len(in_groups)),
        groups_with_an_infeasible_candidate=int(in_groups.groupby("group").feasible.apply(lambda s: (~s).any()).sum()),
        groups_lost=primary["groups_lost_to_infeasibility"],
        papers=int(cand.loc[~cand.feasible, "doi"].nunique()),
        conversion_capped_at_some_purge=int((cand.n_capped_recycled > 0).sum()),
        conversion_capped_at_primary_optimum=int((cand.X_eff_recycled_opt < cand.X * (1 - 1e-9)).sum()),
        above_equilibrium_at_unconstrained_optimum=int((cand.co2_hyd_approach_at_unconstrained_recycled > 1 + 1e-4).sum()),
        nonreactive_at_unconstrained_optimum_quantiles={q: float(cand.nonreactive_at_unconstrained_recycled.quantile(q))
                                                        for q in (0.1, 0.5, 0.9, 1.0)},
        nonreactive_limit=float(G.NONREACTIVE_MAX),
        purge_primary_quantiles={q: float(cand.purge_recycled_opt.quantile(q)) for q in (0.0, 0.1, 0.5, 0.9, 1.0)},
        purge_unconstrained_at_grid_corner=int((cand.purge_recycled_opt_unconstrained <= G.PURGES[0] + 1e-12).sum()))

    # ------------------------------------------------------------ outputs -------------------------------------
    keep = ["group", "doi", "entry", "catalyst", "T_C", "P_bar", "h2_co2", "ghsv_key", "X", "SMeOH", "SCO", "SCH4",
            "reported_S_sum", "other_products", "plot_read", "sty_basis", "STY", "feasible",
            "cost_recycled_opt", "purge_recycled_opt", "n_eligible_recycled", "X_eff_recycled_opt", "n_capped_recycled",
            "cost_recycled_opt_uncapped", "cost_recycled_opt_limit_x1.5", "cost_recycled_opt_limit_x2",
            "cost_recycled_opt_limit_x3", *[f"cost_recycled_opt_lim{lim * 100:g}" for lim in LIMIT_SWEEP],
            "cost_recycled_opt_eqonly", "purge_recycled_opt_eqonly", "cost_recycled_opt_limit_ch4n2",
            "cost_recycled_opt_unconstrained", "purge_recycled_opt_unconstrained",
            "nonreactive_at_unconstrained_recycled", "co2_hyd_approach_at_unconstrained_recycled",
            "cost_recycled_2pct", "cost_recycled_2pct_unconstrained",
            "cost_inert_opt", "purge_inert_opt", "cost_inert_opt_unconstrained", "purge_inert_opt_unconstrained",
            "cost_inert_2pct", "cost_inert_2pct_unconstrained",
            "cost_recycled_opt_rho0.5", "cost_recycled_opt_rho2", "source", "location"]
    cand.sort_values(["group", "STY"], ascending=[True, False])[keep].to_csv(HERE / "literature_candidates.csv",
                                                                           index=False, float_format="%.12g")  # full precision: downstream reruns rebuild costs from these inputs
    primary_gm.to_csv(HERE / "group_metrics.csv", index=False, float_format="%.6g")
    unc_gm.to_csv(HERE / "group_metrics_unconstrained.csv", index=False, float_format="%.6g")
    check.to_csv(HERE / "selfcheck_gothe_table4.csv", index=False, float_format="%.10g")
    summary = dict(
        records_in=int(len(read_records())), candidates=int(len(cand)), papers_with_candidates=int(cand.doi.nunique()),
        duplicate_entries_counted_once=int(n_dup),
        primary=primary, infeasible=infeasible, variants=variants, limit_sweep=limit_sweep,
        isothermal=isothermal_sweep,
        selfcheck=dict(entries=int(len(got)), max_abs_diff_eur_t=selfcheck_max,
                       canonical_states={r.canonical_state: round(r.agent, 2) for r in canon.itertuples()}),
        runtime_s=round(time.time() - t0, 1), workers=WORKERS,
    )
    (HERE / "summary.json").write_text(json.dumps(summary, indent=1, default=float) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1, default=float))


if __name__ == "__main__":
    main()
