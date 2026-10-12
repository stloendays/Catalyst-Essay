"""Paper leaderboards versus plant-cost leaderboards for literature CO2-to-methanol catalysts: the frozen methanol field
result (author decisions of 2026-10-08) and its sensitivities.

Input: the literature-extraction Agent's normalized records (agent/extraction/out/records_normalized.csv), used as
extracted, with no manual correction. Every record with CO2 conversion, methanol selectivity, temperature, pressure
and H2/CO2 (and a dry CO2/H2 feed) is a candidate operating point.

Primary cohort: printed values only (meoh_candidates.printed_entry): CO2 conversion and methanol selectivity printed,
and every CO / CH4 selectivity the paper reports printed too; a printed STY defines the group basis only where it is
itself printed. Entries read from plots enter the all-entries sensitivity.

Comparison groups. Within one paper, entries tested at the same pressure, H2/CO2 ratio and space velocity form one
group: the comparison the paper itself makes (catalysts, and temperatures of one catalyst). Groups with at least two
entries are scored. One measurement printed in several places counts once (same catalyst, temperature and values).

Paper leaderboard. Methanol space-time yield per g catalyst. One productivity basis per group
(meoh_candidates.group_basis): the printed STY when every entry prints it, unless printed STY / conversion-derived
productivity varies by more than 3x within the group; otherwise STY from the mass space velocity, otherwise from the
volumetric space velocity with a bulk density of 1.0 g/mL (0.5 and 2.0 g/mL tested).

Plant leaderboard (frozen treatment, step S5 of analysis/verify_2026_10_08/meoh_decomposition.py). Net production cost
(EUR/t MeOH) from the generalized recycle-economics model (data/meoh/meoh_general_model.py) at each entry's own
pressure, H2/CO2 and temperature: recycled CO bounded by RWGS and CO-hydrogenation equilibrium, the per-pass CO2
conversion the laboratory value capped where the loop outlet reaches CO2-hydrogenation equilibrium, cost-optimal purge
over the canonical grid. Selectivity closure follows the workbook: S_MeOH and S_CH4 as reported ("<1" -> 0), CO-like
residual 1 - S_MeOH - S_CH4; when S_CH4 is not reported, S_CH4 = 1 - S_MeOH - S_CO if S_CO is reported, else 0.

Sensitivities (summary "variants" on the printed cohort unless stated): all entries (plot readings included), the
reactor-inlet non-H2/CO2 limit of the workbook (6.86 %, step S6; x 1.5, 2, 3 and absolute limits 4-30 %), laboratory
conversion uncapped (step S4), inert CO, 2 % purge, bulk density 0.5 / 2.0 g/mL, the leaderboard by X*S, X or
S_MeOH, without the paper with the most groups, entries whose reported selectivities sum to >= 95 %, and isothermal
catalyst comparisons (entries of a group at one temperature naming at least two catalysts). Disagreements are split
by kind with their denominators (mismatch_kinds.classify). Conversion raised with catalyst inventory and the
unreported CO / CH4 split are in run_conversion_sensitivity.py and run_selectivity_split.py.

Self-check (Agent consistency with the hand-built case): the extracted Gothe et al. 2025 Table 4 entries are run
through the same code path; their costs must equal the frozen Table 4 results, including the four canonical states.

Parallel over unique operating points, INV_WORKERS processes (default 4).

Outputs (this folder): literature_candidates.csv (printed cohort, the primary), literature_candidates_all_entries.csv,
group_metrics.csv (primary), group_metrics_all_entries.csv, group_metrics_inlet_limit.csv,
group_metrics_isothermal.csv, selfcheck_gothe_table4.csv, summary.json.
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
                             build_candidates, catalyst_key, gothe_selfcheck, plant_costs_star, read_records)
from mismatch_kinds import classify, leader_differences  # noqa: E402

sys.path.insert(0, str(REPO / "agent"))
from selfcheck_gate import require  # noqa: E402

WORKERS = int(os.environ.get("INV_WORKERS", "4"))
TREATMENT = ("printed values only; recycled CO bounded by RWGS and CO-hydrogenation equilibrium; per-pass conversion "
             "capped at the loop's CO2-hydrogenation equilibrium; cost-optimal purge, no inlet limit (step S5)")


def regret_bins(gm):
    m = gm[gm.top1_mismatch]
    return {f"gt{int(t * 100)}pct": dict(groups=int((m.regret > t).sum()), papers=int(m[m.regret > t].doi.nunique()))
            for t in (0.01, 0.05, 0.10)}


def scored(frame, cost_col, label, up_col="STY", with_kinds=False):
    gm, s = aggregate(frame, cost_col, up_col=up_col, label=label)
    if s:
        s["regret_bins"] = regret_bins(gm)
        if with_kinds:
            gm, s["kinds"] = classify(frame, gm, cost_col)
    return gm, s


def main():
    require()          # ACSA scores new candidates only after reproducing all three hand-built cases
    t0 = time.time()
    records = read_records()
    sets = {"printed": build_candidates(records, printed_only=True),
            "all": build_candidates(records, printed_only=False)}
    keys = sorted({tuple(float(r[k]) for k in ROW_KEYS) for c in sets.values() for r in c[ROW_KEYS].to_dict("records")})
    with Pool(WORKERS) as pool:
        res = pool.map(plant_costs_star, [(dict(zip(ROW_KEYS, k)), RHO_SCALES) for k in keys], chunksize=4)
    table = dict(zip(keys, res))
    for name, c in sets.items():
        costs = pd.DataFrame([table[tuple(float(r[k]) for k in ROW_KEYS)] for r in c[ROW_KEYS].to_dict("records")],
                             index=c.index)
        sets[name] = c = pd.concat([c, costs], axis=1)
        c["feasible"] = np.isfinite(c.cost_recycled_opt)
        c["XS"] = c.X * c.SMeOH
    cand, alle = sets["printed"], sets["all"]

    # ------------------------------------------------------------ self-check ----------------------------------
    got = alle[alle.doi == GOTHE_DOI].copy()
    check = gothe_selfcheck(got)
    selfcheck_max = float(check.abs_diff.max())
    canon = check[(check.canonical_state != "") & (check.treatment == "inert")]

    # ------------------------------------------------------------ primary -------------------------------------
    primary_gm, primary = scored(cand, "cost_recycled_opt", "primary: " + TREATMENT, with_kinds=True)
    primary["bootstrap"] = bootstrap(primary_gm)
    primary["leader_differences"] = leader_differences(cand, primary_gm, "cost_recycled_opt", "purge_recycled_opt")

    # ------------------------------------------------------------ sensitivities -------------------------------
    all_gm, all_entries = scored(alle, "cost_recycled_opt", "all entries, plot readings included", with_kinds=True)
    all_entries["bootstrap"] = bootstrap(all_gm)
    inlet_gm, inlet = scored(cand, "cost_recycled_opt_inlet", "reactor-inlet non-H2/CO2 <= 6.86 % (step S6)",
                             with_kinds=True)
    inlet["bootstrap"] = bootstrap(inlet_gm)
    variants = {
        "inlet_limit_6.86pct": inlet,
        **{f"inlet_limit_x{m:g}": scored(cand, f"cost_recycled_opt_limit_x{m:g}", f"inlet limit 6.86 % x {m:g}")[1]
           for m in (1.5, 2.0, 3.0)},
        "conversion_uncapped": scored(cand, "cost_recycled_opt_uncapped",
                                      "laboratory conversion uncapped (step S4)")[1],
        "recycled_2pct": scored(cand, "cost_recycled_2pct", "2 % purge")[1],
        "inert_opt": scored(cand, "cost_inert_opt", "inert CO, optimal purge")[1],
        "inert_opt_inlet_limit": scored(cand, "cost_inert_opt_inlet", "inert CO, inlet limit 6.86 %")[1],
        "inert_2pct": scored(cand, "cost_inert_2pct", "inert CO, 2 % purge")[1],
        **{f"density_{name[3:]}": scored(cand, f"cost_recycled_opt_{name}", f"density {name[3:]} g/mL")[1]
           for name in RHO_SCALES},
        "leaderboard_X_times_S": scored(cand, "cost_recycled_opt", "X*S leaderboard", up_col="XS")[1],
        "leaderboard_X": scored(cand, "cost_recycled_opt", "X leaderboard", up_col="X")[1],
        "leaderboard_S_MeOH": scored(cand, "cost_recycled_opt", "S_MeOH leaderboard", up_col="SMeOH")[1],
        "methanol_products_only": scored(cand[~cand.other_products], "cost_recycled_opt",
                                         "reported S_MeOH+S_CO+S_CH4 >= 95 %")[1],
        "all_entries": all_entries,
        "all_entries_inert_opt": scored(alle, "cost_inert_opt", "all entries, inert CO")[1],
        "all_entries_inlet_limit": scored(alle, "cost_recycled_opt_inlet", "all entries, inlet limit 6.86 %")[1],
        "all_entries_leaderboard_S_MeOH": scored(alle, "cost_recycled_opt", "all entries, S_MeOH leaderboard",
                                                 up_col="SMeOH")[1],
    }
    biggest = primary_gm.groupby("doi").size().idxmax()          # paper contributing the most scored groups
    variants["without_paper_with_most_groups"] = scored(cand[cand.doi != biggest], "cost_recycled_opt",
                                                        f"without {biggest}")[1]
    limit_sweep = {f"{lim * 100:g}%": scored(cand, f"cost_recycled_opt_lim{lim * 100:g}",
                                             f"inlet limit {lim * 100:g} %")[1] for lim in LIMIT_SWEEP}
    limit_sweep["none (primary)"] = {k: primary[k] for k in ("groups", "top1_mismatch_groups", "papers")}

    # isothermal catalyst comparisons: within a group, the entries at one temperature that name at least two
    # different catalysts (the paper's catalyst ranking at fixed T, P, H2/CO2 and space velocity)
    iso = cand.copy()
    iso["group"] = iso.group + " | T " + iso.T_C.round(1).map("{:g}".format)
    ncat = iso.groupby("group").catalyst.agg(lambda s: s.map(catalyst_key).nunique())
    iso = iso[iso.group.isin(ncat[ncat >= 2].index)]
    iso_gm, isothermal = scored(iso, "cost_recycled_opt", "isothermal catalyst comparisons, primary")
    isothermal["bootstrap"] = bootstrap(iso_gm)
    isothermal_variants = {"inlet_limit_6.86pct": scored(iso, "cost_recycled_opt_inlet", "isothermal, inlet limit")[1],
                           "all_entries": None}
    iso_all = alle.copy()
    iso_all["group"] = iso_all.group + " | T " + iso_all.T_C.round(1).map("{:g}".format)
    nca = iso_all.groupby("group").catalyst.agg(lambda s: s.map(catalyst_key).nunique())
    isothermal_variants["all_entries"] = scored(iso_all[iso_all.group.isin(nca[nca >= 2].index)], "cost_recycled_opt",
                                                "isothermal, all entries")[1]
    isothermal["variants"] = isothermal_variants

    # bookkeeping of the thermodynamic treatment (primary cohort, entries in scored groups)
    n = cand.groupby("group").size()
    ing = cand[cand.group.isin(n[n >= 2].index)]
    thermo = dict(
        entries_in_scored_groups=int(len(ing)),
        conversion_capped_at_some_purge=int((ing.n_capped_recycled > 0).sum()),
        conversion_capped_at_primary_optimum=int((ing.X_eff_recycled_opt < ing.X * (1 - 1e-9)).sum()),
        equilibrium_feasible_at_primary_optimum=int(ing.equilibrium_feasible_at_opt_recycled.sum()),
        inlet_nonreactive_at_primary_optimum_quantiles={q: float(ing.nonreactive_at_opt_recycled.quantile(q))
                                                        for q in (0.1, 0.5, 0.9, 1.0)},
        entries_outside_inlet_limit_at_primary_optimum=int((ing.nonreactive_at_opt_recycled > G.NONREACTIVE_MAX).sum()),
        entries_with_no_purge_level_within_inlet_limit=int((ing.n_inlet_ok_recycled == 0).sum()),
        inlet_limit=float(G.NONREACTIVE_MAX),
        purge_primary_quantiles={q: float(ing.purge_recycled_opt.quantile(q)) for q in (0.0, 0.1, 0.5, 0.9, 1.0)},
        purge_at_grid_corner=int((ing.purge_recycled_opt <= G.PURGES[0] + 1e-12).sum()))
    cohort = dict(
        entries=int(len(cand)), entries_in_scored_groups=int(len(ing)), papers_with_entries=int(cand.doi.nunique()),
        ch4_selectivity_not_printed=int((~ing.ch4_printed).sum()),
        co_selectivity_not_printed=int((~ing.co_printed).sum()),
        neither_printed=int((~ing.ch4_printed & ~ing.co_printed).sum()),
        sty_basis_counts={k: int(v) for k, v in primary_gm.basis.value_counts().items()},
        all_entries=int(len(alle)))

    # ------------------------------------------------------------ outputs -------------------------------------
    keep = ["group", "doi", "entry", "catalyst", "catalyst_key", "T_C", "P_bar", "h2_co2", "ghsv_key", "X", "SMeOH",
            "SCO", "SCH4", "reported_S_sum", "other_products", "plot_read", "printed", "sty_printed", "ch4_printed",
            "co_printed", "sty_basis", "STY", "y_co2", "feasible",
            "cost_recycled_opt", "purge_recycled_opt", "X_eff_recycled_opt", "n_capped_recycled",
            "equilibrium_feasible_at_opt_recycled", "nonreactive_at_opt_recycled", "co2_hyd_approach_at_opt_recycled",
            "cost_recycled_opt_inlet", "purge_recycled_opt_inlet", "n_inlet_ok_recycled",
            "cost_recycled_opt_limit_x1.5", "cost_recycled_opt_limit_x2", "cost_recycled_opt_limit_x3",
            *[f"cost_recycled_opt_lim{lim * 100:g}" for lim in LIMIT_SWEEP],
            "cost_recycled_opt_uncapped", "cost_recycled_2pct", "cost_recycled_2pct_inlet",
            "cost_inert_opt", "purge_inert_opt", "cost_inert_opt_inlet", "cost_inert_2pct", "cost_inert_2pct_inlet",
            "cost_recycled_opt_rho0.5", "cost_recycled_opt_rho2", "source", "location"]
    for name, c in (("literature_candidates.csv", cand), ("literature_candidates_all_entries.csv", alle)):
        # full precision: downstream reruns rebuild costs from these inputs
        c.sort_values(["group", "STY"], ascending=[True, False])[keep].to_csv(HERE / name, index=False,
                                                                           float_format="%.12g")
    primary_gm.to_csv(HERE / "group_metrics.csv", index=False, float_format="%.6g")
    all_gm.to_csv(HERE / "group_metrics_all_entries.csv", index=False, float_format="%.6g")
    inlet_gm.to_csv(HERE / "group_metrics_inlet_limit.csv", index=False, float_format="%.6g")
    iso_gm.to_csv(HERE / "group_metrics_isothermal.csv", index=False, float_format="%.6g")
    check.to_csv(HERE / "selfcheck_gothe_table4.csv", index=False, float_format="%.10g")
    summary = dict(
        treatment=TREATMENT, records_in=int(len(records)), cohort=cohort,
        duplicate_entries_counted_once=dict(printed=int(cand.attrs.get("duplicates_removed", 0)),
                                            all=int(alle.attrs.get("duplicates_removed", 0))),
        primary=primary, thermodynamics=thermo, variants=variants, limit_sweep=limit_sweep, isothermal=isothermal,
        selfcheck=dict(entries=int(len(got)), max_abs_diff_eur_t=selfcheck_max,
                       canonical_states={r.canonical_state: round(r.agent, 2) for r in canon.itertuples()}),
        unique_operating_points=len(keys), runtime_s=round(time.time() - t0, 1), workers=WORKERS,
    )
    (HERE / "summary.json").write_text(json.dumps(summary, indent=1, default=float) + "\n", encoding="utf-8")
    p = summary["primary"]
    print(json.dumps(summary, indent=1, default=float))
    print(f"\nprimary {p['top1_mismatch_groups']}/{p['groups']} groups, {p['papers_with_mismatch']}/{p['papers']} papers;"
          f" regret > 5 %: {p['regret_bins']['gt5pct']['groups']}; all entries "
          f"{all_entries['top1_mismatch_groups']}/{all_entries['groups']}; inlet limit "
          f"{inlet['top1_mismatch_groups']}/{inlet['groups']}")


if __name__ == "__main__":
    main()
