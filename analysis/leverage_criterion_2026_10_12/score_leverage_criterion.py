"""Scoring of the leverage criterion (PROTOCOL.md section 6) from the case files written by run_leverage_criterion.py.

    python analysis/leverage_criterion_2026_10_12/score_leverage_criterion.py

Reads cases.csv, properties.csv, meoh_pairwise.csv and run_record.json; writes summary.json and results_tables.md.
Sections marked "exploratory" were added after the first scored run (descriptive only; no criterion changed).
"""
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
INPUTS = ["controls/au_tio2_rank_preservation_v1_1.py", "controls/au_tio2_rank_preservation_v1_1_config.json",
          "provenance/discover_v1/source_harness/harness_core.py",
          "provenance/discover_v1/source_harness/outputs/nh3_final_20260905T134204Z/results.json",
          "provenance/nh3_final_1_1/source_harness/inputs/ammonia_activity_volcano_s1_v1.xlsx",
          "data/meoh/meoh_d01_model.py", "data/meoh/meoh_general_model.py",
          "analysis/meoh_literature_inversion_2026_10_05/literature_candidates.csv",
          "analysis/leverage_criterion_2026_10_12/PROTOCOL.md"]


def sha256_text_normalized(path):
    """SHA-256 of a file with CRLF read as LF (text files), so Windows and Linux checkouts hash alike."""
    b = path.read_bytes()
    return hashlib.sha256(b if path.suffix == ".xlsx" else b.replace(b"\r\n", b"\n")).hexdigest()


CLASSES =["upstream metric", "metal price / loading", "temperature / operating window", "single-pass conversion",
           "selectivity CO", "selectivity CH4", "selectivity CO+CH4"]


def as_bool(s):
    return s.map(lambda v: None if pd.isna(v) else (v if isinstance(v, bool) else str(v) == "True"))


def confusion(df, col):
    d = df[df[col].notna()]
    a = d.actual_inverted.astype(bool).to_numpy()
    p = d[col].astype(bool).to_numpy()
    tp, fn = int((a & p).sum()), int((a & ~p).sum())
    fp, tn = int((~a & p).sum()), int((~a & ~p).sum())
    n = len(d)
    return dict(n=n, actual_inverted=int(a.sum()), TP=tp, FN=fn, FP=fp, TN=tn,
                accuracy=(tp + tn) / n if n else None, sensitivity=tp / (tp + fn) if tp + fn else None,
                specificity=tn / (tn + fp) if tn + fp else None,
                always_preserve_accuracy=(tn + fp) / n if n else None,
                majority_accuracy=max(tp + fn, tn + fp) / n if n else None, excluded=int(len(df) - n))


def cluster_bootstrap(df, correct_col, n=10_000, seed=20261006):
    """Paper-cluster bootstrap (resample papers with replacement; every case of a drawn paper enters)."""
    d = df[df[correct_col].notna()]
    per = d.groupby("doi")[correct_col].agg(lambda v: float(np.sum(v.astype(bool)))).to_frame("sum")
    per["count"] = d.groupby("doi").size()
    s, c = per["sum"].to_numpy(float), per["count"].to_numpy(float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(per), size=(n, len(per)))
    frac = s[idx].sum(1) / c[idx].sum(1)
    lo, hi = np.percentile(frac, [2.5, 97.5])
    return dict(resamples=n, papers=len(per), seed=seed, accuracy=float(s.sum() / c.sum()), ci95=[float(lo), float(hi)])


def main():
    cases = pd.read_csv(HERE / "cases.csv")
    props = pd.read_csv(HERE / "properties.csv")
    prs = pd.read_csv(HERE / "meoh_pairwise.csv")
    rec = json.loads((HERE / "run_record.json").read_text(encoding="utf-8"))
    for col in ("actual_inverted", "pred_L", "pred_F", "pred_D", "correct_L", "correct_F", "correct_D"):
        cases[col] = as_bool(cases[col])
    for col in ("actual_inverted", "pred_L"):
        prs[col] = as_bool(prs[col])
    props["actual_inverted"] = as_bool(props["actual_inverted"])

    sets = {"Au nominal": cases[cases.system == "Au"], "NH3": cases[cases.system == "NH3"],
            "MeOH S5": cases[(cases.system == "MeOH") & (cases.scenario == "S5")],
            "MeOH S6": cases[(cases.system == "MeOH") & (cases.scenario == "S6")],
            "Re/TiO2": cases[cases.system == "Re"]}
    sets["pooled (Au + NH3 + MeOH S5 + Re)"] = pd.concat([sets[k] for k in ("Au nominal", "NH3", "MeOH S5", "Re/TiO2")])
    sets["pooled (Au + NH3 + MeOH S6 + Re)"] = pd.concat([sets[k] for k in ("Au nominal", "NH3", "MeOH S6", "Re/TiO2")])
    conf = {crit: {name: confusion(d, f"pred_{crit}") for name, d in sets.items()} for crit in ("L", "F", "D")}
    au = rec["au_draws"]
    for crit in ("L", "F"):
        conf[crit]["Au draws"] = dict(n=au["cases"], actual_inverted=au["actual_inverted"],
                                      predicted_inverted=au[f"{crit}_pred_inverted"],
                                      accuracy=au[f"{crit}_correct"] / au["cases"])
    boot = {}
    for sc in ("S5", "S6"):
        d = sets[f"MeOH {sc}"]
        boot[f"MeOH {sc} C1"] = cluster_bootstrap(d, "correct_L")
        boot[f"MeOH {sc} C2"] = cluster_bootstrap(d, "correct_F")
        q = prs[prs.scenario == sc].copy()
        q["correct_L"] = q.pred_L == q.actual_inverted
        boot[f"MeOH {sc} all pairs C1"] = cluster_bootstrap(q, "correct_L")
    pair_conf = {sc: confusion(prs[prs.scenario == sc], "pred_L") for sc in ("S5", "S6")}

    # ---- regret explained (inverted cases)
    regret = {}
    for name in ("NH3", "MeOH S5", "MeOH S6", "Re/TiO2"):
        d = sets[name]
        inv = d[d.actual_inverted.astype(bool) & d.carrying_property.notna()]
        R = inv.C_i - inv.C_j
        rho = spearmanr(d.U_L + d.O_L, d.dlnC_actual).statistic
        regret[name] = dict(
            inverted_cases=int(len(inv)), regret_sum=float(R.sum()), regret_median_rel=float(inv.regret_rel.median()),
            carrying_class_counts={k: int(v) for k, v in inv.carrying_class.value_counts().items()},
            carrying_share_median=float(inv.carrying_share_of_regret.median()),
            upstream_share_median=float(inv.upstream_share_of_regret.median()),
            pathway_pool_share_weighted=float((inv.pathway_pool_share_of_regret * R).sum() / R.sum()),
            pathway_pool_share_median=float(inv.pathway_pool_share_of_regret.median()),
            C1_reproduced_share_of_regret=float(inv.R_hat_L.sum() / R.sum()),
            C1_spearman_predicted_vs_actual_dlnC=float(rho) if np.isfinite(rho) else None)

    # ---- attribution by property class (exact D)
    pp = props.dropna(subset=["phi_D"])
    attribution = {}
    for (s, sc, inv), d in pp.groupby(["system", "scenario", "actual_inverted"]):
        n = d.case_id.nunique()
        out = {}
        for cl, e in d.groupby("property_class"):
            share = e.phi_D_share_of_abs_total.sum() / n          # cases without this class contribute 0
            out[cl] = dict(mean_pct_of_Ci=float(e.phi_D_pct_of_Ci.sum() / n), median_pct_of_Ci_where_present=float(
                e.phi_D_pct_of_Ci.median()), cases_with_class=int(e.case_id.nunique()), mean_share_of_abs_total=float(share))
        attribution[f"{s} / {sc} / {'inverted' if inv else 'preserved'}"] = dict(cases=int(n), classes=out)

    # ---- exploratory (added after the first scored run; descriptive only)
    me = cases[cases.system == "MeOH"]
    kind_tab = {}
    for sc, d in me[me.actual_inverted.astype(bool)].groupby("scenario"):
        kind_tab[sc] = {f"{k} | {c}": int(v) for (k, c), v in d.groupby([d.kind.fillna(""), "carrying_class"]).size().items()}
    s6 = sets["MeOH S6"]
    miss = s6[(s6.correct_L == False)]  # noqa: E712
    hit = s6[(s6.correct_L == True) & s6.actual_inverted.astype(bool)]  # noqa: E712
    exploratory = dict(
        carrying_class_by_disagreement_kind=kind_tab,
        S6_C1_misses=dict(cases=int(len(miss)), plant_leader_at_lower_purge=int((miss.purge_j < miss.purge_i - 1e-12).sum()),
                          median_purge_i=float(miss.purge_i.median()), median_purge_j=float(miss.purge_j.median()),
                          O_L_positive=int((miss.O_L > 0).sum())),
        S6_C1_hits_inverted=dict(cases=int(len(hit)), plant_leader_at_lower_purge=int((hit.purge_j < hit.purge_i - 1e-12).sum()),
                                 median_purge_i=float(hit.purge_i.median()), median_purge_j=float(hit.purge_j.median())),
        S5_purges=dict(all_at_grid_floor=bool((sets["MeOH S5"][["purge_i", "purge_j"]] == 0.005).all().all())),
        bansode_2013_cases=int((me.doi == "10.1039/c2cy20604h").sum()),
        merged_selectivity_cases=me.loc[me.merged_selectivity.astype(str) == "True", "case_id"].tolist())

    flags = dict(U_L_nonpositive=int((cases.U_L <= 0).sum()), U_D_nonpositive=int((cases.U_D <= 0).sum()),
                 U_F_nonpositive=int((cases.U_F <= 0).sum()),
                 D_identity_failures=int((cases.correct_D == False).sum()),  # noqa: E712
                 L_wrong=cases.loc[cases.correct_L == False, "case_id"].tolist(),  # noqa: E712
                 F_wrong=cases.loc[cases.correct_F == False, "case_id"].tolist())  # noqa: E712
    summary = dict(protocol=dict(file="PROTOCOL.md", committed_before_outcomes="0c94d80"),
                   inputs_sha256_lf={p: sha256_text_normalized(REPO / p) for p in INPUTS}, gates=rec["gates"],
                   confusion=dict(C1_first_order=conf["L"], C2_fixed_design=conf["F"], D_identity_check=conf["D"]),
                   meoh_all_pairs_C1=pair_conf, bootstrap=boot, regret_explained=regret, attribution=attribution,
                   flags=flags, exploratory=exploratory, runtime_s=rec["runtime_s"], workers=rec["workers"])
    (HERE / "summary.json").write_text(json.dumps(summary, indent=1, default=float) + "\n", encoding="utf-8")
    write_tables(summary, cases, props)
    print(json.dumps({k: summary[k] for k in ("confusion", "bootstrap", "regret_explained")}, indent=1, default=float))


def f3(x):
    return "–" if x is None or (isinstance(x, float) and not np.isfinite(x)) else f"{x:.3f}"


def write_tables(s, cases, props):
    L = []
    for crit, title in (("C1_first_order", "C1, first order at the upstream leader's optimum (primary)"),
                        ("C2_fixed_design", "C2, fixed-design Shapley (secondary)")):
        L += [f"### {title}", "", "| Set | n | inverted | TP | FN | FP | TN | accuracy | always-preserve | sensitivity | specificity |",
              "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
        for name, c in s["confusion"][crit].items():
            if "TP" not in c:
                L.append(f"| {name} | {c['n']:,} | {c['actual_inverted']} | – | – | – | – | {f3(c['accuracy'])} | – | – | – |")
                continue
            L.append(f"| {name} | {c['n']} | {c['actual_inverted']} | {c['TP']} | {c['FN']} | {c['FP']} | {c['TN']} | "
                     f"{f3(c['accuracy'])} | {f3(c['always_preserve_accuracy'])} | {f3(c['sensitivity'])} | {f3(c['specificity'])} |")
        L.append("")
    L += ["### Methanol, paper-cluster bootstrap of accuracy (10,000 resamples of the 28 papers)", "",
          "| Set | accuracy | 95 % CI |", "|---|---:|---|"]
    for k, b in s["bootstrap"].items():
        L.append(f"| {k} | {b['accuracy']:.3f} | {b['ci95'][0]:.3f}–{b['ci95'][1]:.3f} |")
    L += ["", "### Methanol, every STY-ordered within-group pair, C1 (secondary set)", "",
          "| Scenario | pairs | inverted | TP | FN | FP | TN | accuracy | always-preserve |",
          "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for sc, c in s["meoh_all_pairs_C1"].items():
        L.append(f"| {sc} | {c['n']} | {c['actual_inverted']} | {c['TP']} | {c['FN']} | {c['FP']} | {c['TN']} | "
                 f"{f3(c['accuracy'])} | {f3(c['always_preserve_accuracy'])} |")
    L += ["", "### Regret explained (inverted cases)", "",
          "| System | inverted | carrying property (cases) | carrying share of regret, median | upstream share, median | "
          "pathway-pool share of regret | C1 reproduced share | Spearman, C1 vs actual ln(C_j/C_i) |",
          "|---|---:|---|---:|---:|---:|---:|---:|"]
    for name, r in s["regret_explained"].items():
        cc = ", ".join(f"{k} ({v})" for k, v in r["carrying_class_counts"].items())
        L.append(f"| {name} | {r['inverted_cases']} | {cc} | {r['carrying_share_median']:.2f} | "
                 f"{r['upstream_share_median']:.2f} | {r['pathway_pool_share_weighted']:.2f} | "
                 f"{r['C1_reproduced_share_of_regret']:.2f} | {f3(r['C1_spearman_predicted_vs_actual_dlnC'])} |")
    L += ["", "### Attribution by property class (exact D): mean phi as % of C_i [mean signed share of sum |phi|]", "",
          "Negative favours j (the plant-cost competitor). Cases where a class is not a player count as 0.", "",
          "| System / scenario / outcome | n | " + " | ".join(CLASSES) + " |", "|---|---:|" + "---:|" * len(CLASSES)]
    for key, d in s["attribution"].items():
        cells = []
        for c in CLASSES:
            v = d["classes"].get(c)
            cells.append("0" if v is None else f"{v['mean_pct_of_Ci']:+.3g} [{v['mean_share_of_abs_total']:+.2f}]")
        L.append(f"| {key} | {d['cases']} | " + " | ".join(cells) + " |")
    L += ["", "### Small systems, per case (phi_D in cost units; U_L + O_L in ln J)", "",
          "| Case | C_i | C_j | actual | phi_D by property | U_L + O_L | C1 | C2 |", "|---|---:|---:|---|---|---:|---|---|"]
    lab = lambda b: "inverted" if b else "preserved"  # noqa: E731
    for _, k in cases[cases.system.isin(["Au", "NH3", "Re"])].iterrows():
        pp = props[props.case_id == k.case_id]
        ph = "; ".join(f"{r.property} {r.phi_D:+.4g}" for r in pp.itertuples())
        L.append(f"| {k.case_id} | {k.C_i:.5g} | {k.C_j:.5g} | {lab(k.actual_inverted)} | {ph} | {k.U_L + k.O_L:+.4f} | "
                 f"{lab(k.pred_L)} | {lab(k.pred_F)} |")
    (HERE / "results_tables.md").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
