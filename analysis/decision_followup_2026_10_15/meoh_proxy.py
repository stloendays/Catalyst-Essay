#!/usr/bin/env python3
"""Model-conditional, paper-held-out S5->S6 cost transfer without test-time S6 oracle."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from hashlib import sha256
import json
import math
from pathlib import Path
import random
import statistics

ROOT = Path(__file__).resolve().parents[2]
L = 0.0686
RIDGE = 0.10
SEED = 20261015
FEATURES = ("activation", "CO_x_activation", "CH4_x_activation")
BASELINES = ("STY", "S", "S5", "one_feature", "three_feature")
ANCHORS = {"S5": 15, "S6": 28}
EPS = 1.0e-12


def require(condition, explanation):
    if not condition:
        raise AssertionError(explanation)


def read(path):
    with (ROOT / path).open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def save_csv(path, records, keys=None):
    records = list(records)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys or list(records[0]), extrasaction="ignore")
        w.writeheader()
        w.writerows(records)


def value(obj, key):
    try:
        x = float(obj[key])
    except (KeyError, TypeError, ValueError):
        return math.nan
    return x if math.isfinite(x) else math.nan


def valid_positive(x):
    return math.isfinite(x) and x > 0


def features(row):
    q = row["q"]
    a = max(0.0, math.log(max(q, 1e-12) / L))
    return (a, a * row["SCO"] / (row["SMeOH"] + 0.05),
            a * row["SCH4"] / (row["SMeOH"] + 0.05))


def load_cohort():
    raw = read("analysis/meoh_literature_inversion_2026_10_05/literature_candidates.csv")
    included = read("analysis/meoh_literature_inversion_2026_10_05/group_metrics_inlet_limit.csv")
    groups_included = {r["group"] for r in included}
    require(len(included) == 40 and len(groups_included) == 40, "scored-group lock changed")
    selected = [r for r in raw if r["group"] in groups_included]
    require(len(raw) == 351 and len(selected) == 310, "printed candidate denominator changed")
    outcome_raw = read("analysis/meoh_constraint_boundary_2026_10_12/boundary_groups.csv")
    outcomes = {(r["group"], r["scenario"]): r for r in outcome_raw}
    require(len(outcomes) == len(outcome_raw), "duplicate source ledger")
    for scenario, n in ANCHORS.items():
        require(sum(r["mismatch"].lower() == "true" for r in outcome_raw if r["scenario"] == scenario) == n,
                f"original {scenario} inversion anchor changed")
    candidates, labels = [], {}
    for i, r in enumerate(selected):
        identifier = (r["group"], r["entry"])
        require(identifier not in labels, f"duplicate group/entry: {identifier}")
        j5, j6 = value(r, "cost_recycled_opt"), value(r, "cost_recycled_opt_inlet")
        q, st, select = value(r, "nonreactive_at_opt_recycled"), value(r, "STY"), value(r, "SMeOH")
        co, methane = value(r, "SCO"), value(r, "SCH4")
        p5, p6 = value(r, "purge_recycled_opt"), value(r, "purge_recycled_opt_inlet")
        require(valid_positive(j5) and math.isfinite(q) and 0 <= q < 1, f"invalid S5 {identifier}")
        require(math.isfinite(st) and math.isfinite(select) and 0 < select <= 1, f"invalid lab {identifier}")
        require(0 <= co <= 1 and 0 <= methane <= 1, f"invalid carbon split {identifier}")
        require(valid_positive(p5), f"invalid S5 purge {identifier}")
        if valid_positive(j6):
            require(j6 >= j5 * (1 - 1e-6), f"constrained optimum cheaper than unconstrained: {identifier}")
        else:
            j6 = math.nan
        # Training/prediction feature object intentionally contains NO S6 fields.
        candidates.append(dict(id=identifier, group=r["group"], entry=r["entry"],
            catalyst=r["catalyst"], material=r["catalyst_key"], doi=r["doi"], row_order=i,
            J5=j5, q=q, STY=st, SMeOH=select, SCO=co, SCH4=methane, p5=p5))
        # Labels in separate dictionary: accessible only to training-paper target and scoring routines.
        labels[identifier] = dict(J6=j6, p6=p6)
    groups = defaultdict(list)
    for c in candidates:
        groups[c["group"]].append(c)
    papers = sorted({r["doi"] for r in candidates})
    require(len(groups) == 40 and len(papers) == 28, "group/paper count drift")
    for g, cs in groups.items():
        require(len(cs) >= 2 and len({c["id"] for c in cs}) == len(cs), f"duplicate/short group {g}")
        for scen in ANCHORS:
            require((g, scen) in outcomes, f"missing frozen {scen} group {g}")
            winner = outcomes[(g, scen)]["plant_leader"]
            require(sum(c["catalyst"] == winner for c in cs) == 1,
                    f"frozen winning entry missing from evaluated cohort {g}, {scen}")
    return candidates, labels, dict(groups), papers, outcomes


def fit(training, labels, nfeatures):
    # Per-paper equal weight, and within each paper equal weight per eligible record.
    bypaper = defaultdict(list)
    for c in training:
        if valid_positive(labels[c["id"]]["J6"]):
            bypaper[c["doi"]].append(c)
    require(len(bypaper) >= 2, "too few training papers")
    gram = [[0.0] * nfeatures for _ in range(nfeatures)]
    rhs = [0.0] * nfeatures
    max_negative_y = 0.0
    for paper, records in bypaper.items():
        weight = 1.0 / len(records)
        for c in records:
            x = features(c)[:nfeatures]
            y = math.log(labels[c["id"]]["J6"] / c["J5"])
            max_negative_y = min(max_negative_y, y)
            require(y >= -1e-6, "negative cap cost penalty")
            y = max(0.0, y)
            for j in range(nfeatures):
                rhs[j] += weight * x[j] * y
                for k in range(nfeatures):
                    gram[j][k] += weight * x[j] * x[k]
    beta = [0.0] * nfeatures
    count = 0
    for iteration in range(4000):
        maxchange = 0.0
        for j in range(nfeatures):
            net = rhs[j] - sum(gram[j][k] * beta[k] for k in range(nfeatures) if k != j)
            updated = max(0.0, net / (gram[j][j] + RIDGE))
            maxchange = max(maxchange, abs(updated - beta[j]))
            beta[j] = updated
        count = iteration + 1
        if maxchange < 1e-12:
            break
    require(all(math.isfinite(b) and b >= 0 for b in beta), "nonphysical penalty coefficients")
    return beta, count, len(bypaper), sum(len(v) for v in bypaper.values()), max_negative_y


def predict_cost(c, beta):
    return c["J5"] * math.exp(min(100., sum(a * b for a,b in zip(features(c), beta))))


def choose(entries, method, beta=None, lab_name=None):
    if method == "STY":
        require(lab_name is not None, "missing frozen STY source winner")
        matches = [c for c in entries if c["catalyst"] == lab_name]
        require(len(matches) == 1, "ambiguous source STY tie")
        return matches[0]
    if method == "S":
        return sorted(entries, key=lambda c: (-c["SMeOH"], -c["STY"], c["row_order"]))[0]
    if method == "S5":
        return min(entries, key=lambda c: (c["J5"], c["row_order"]))
    require(beta is not None and method in ("one_feature", "three_feature"), "unregistered predictor")
    return min(entries, key=lambda c: (predict_cost(c, beta), c["row_order"]))


def score_one(choice, plant_name, labels, truth):
    c = labels[choice["id"]]["J6"]
    correct = int(choice["catalyst"] == plant_name)
    if not valid_positive(c):
        require(not correct, "an infeasible row cannot be the real S6 optimizer")
        return dict(correct=0, feasible=0, regret=None)
    r = max(0.0, c / truth - 1)
    require(r >= 0, "negative regret")
    return dict(correct=correct, feasible=1, regret=r)


def exact_paper_bootstrap(rows, col):
    docs = sorted({r["doi"] for r in rows})
    mapping = {p: [r for r in rows if r["doi"] == p] for p in docs}
    rng = random.Random(SEED)
    samples = []
    for _ in range(5000):
        cohort = [x for p in rng.choices(docs, k=len(docs)) for x in mapping[p]]
        samples.append(sum(r[col] for r in cohort) / len(cohort))
    samples.sort()
    return [samples[124], samples[4874]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    candidates, labels, groups, papers, outcomes = load_cohort()
    bypaper = defaultdict(list)
    for c in candidates:
        bypaper[c["doi"]].append(c)
    # This is the ONLY block accessing S6 training labels for fitting, and it excludes the heldout DOI.
    predictions = {}
    fold_rows = []
    for test_paper in papers:
        train = [c for c in candidates if c["doi"] != test_paper]
        require(len(train) + len(bypaper[test_paper]) == len(candidates), "DOI disjointness")
        require(test_paper not in {c["doi"] for c in train}, "heldout DOI leak")
        fit1 = fit(train, labels, 1)
        fit3 = fit(train, labels, 3)
        train_dois = sorted({c["doi"] for c in train})
        fold_rows.append(dict(heldout_doi=test_paper, heldout_entries=len(bypaper[test_paper]),
            train_papers=len(train_dois), train_entries=len(train),
            train_doi_sha256=sha256("\n".join(train_dois).encode()).hexdigest(),
            one_feature_beta=json.dumps(fit1[0]), three_feature_beta=json.dumps(fit3[0]),
            one_feature_sweeps=fit1[1], three_feature_sweeps=fit3[1],
            one_feature_training_entries=fit1[3], three_feature_training_entries=fit3[3]))
        for c in bypaper[test_paper]:
            predictions[c["id"]] = dict(one_feature=predict_cost(c, fit1[0]),
                                        three_feature=predict_cost(c, fit3[0]),
                                        fold=test_paper)
    require(len(predictions) == len(candidates), "heldout prediction coverage")
    # Predictions above are complete, frozen in memory before opening outcome labels for scoring.
    save_csv(out / "01_fold_coefficients.csv", fold_rows)
    pred_rows = []
    for c in candidates:
        item = predictions[c["id"]]
        p = dict(group=c["group"],doi=c["doi"],entry=c["entry"],material=c["material"],
                 J5=c["J5"],q_S5=c["q"],activation=features(c)[0],STY=c["STY"],
                 SMeOH=c["SMeOH"],SCO=c["SCO"],SCH4=c["SCH4"],
                 Jhat6_one_feature=item["one_feature"],Jhat6_three_feature=item["three_feature"],
                 heldout_fold=item["fold"])
        pred_rows.append(p)
    # Store predictions before any outcome-based metrics/reporting on this run.
    save_csv(out / "02_blind_paper_predictions.csv", pred_rows)
    rows = []
    candidate_error = []
    for g, entries in sorted(groups.items()):
        published = outcomes[(g, "S6")]
        plant = published["plant_leader"]
        true_cost = float(published["c_plant"])
        require(true_cost > 0, "bad frozen plant-cost optimum")
        source_lab = outcomes[(g, "S5")]["lab_leader"]
        beta1 = dict((c["id"], predictions[c["id"]]["one_feature"]) for c in entries)
        beta3 = dict((c["id"], predictions[c["id"]]["three_feature"]) for c in entries)
        picks = {
            "STY": choose(entries, "STY", lab_name=source_lab),
            "S": choose(entries, "S"),
            "S5": choose(entries, "S5"),
            "one_feature": min(entries, key=lambda c: (beta1[c["id"]],c["row_order"])),
            "three_feature": min(entries, key=lambda c: (beta3[c["id"]],c["row_order"]))}
        record = dict(group=g, doi=entries[0]["doi"], plant_leader=plant, source_lab_leader=source_lab,
            n=len(entries), reported_class=published["class"],
            model_cost_true=true_cost, model_S6_regret_frozen=float(published["regret"]))
        for method, pick in picks.items():
            assessment = score_one(pick, plant, labels, true_cost)
            record.update({method+"_chosen":pick["catalyst"],method+"_material":pick["material"],
                method+"_correct":assessment["correct"],method+"_feasible":assessment["feasible"],
                method+"_regret":assessment["regret"]})
        ordered = sorted((beta3[c["id"]],c["row_order"],c) for c in entries)
        require(len(ordered)>=2,"no second choice for confidence diagnostic")
        margin = (ordered[1][0] - ordered[0][0]) / max(ordered[0][0],1e-12)
        record["three_feature_predicted_margin"]=margin
        record["three_feature_decisive_5pct"]=int(margin>=.05)
        lab = picks["STY"]
        record["STY_lab_s5_nonreactive"]=lab["q"]
        record["STY_lab_S5_purge"]=lab["p5"]
        record["STY_lab_S6_purge_observed"]=labels[lab["id"]]["p6"]
        record["STY_lab_S6_purge_delta_posthoc"]=labels[lab["id"]]["p6"]-lab["p5"]
        for c in entries:
            actual=labels[c["id"]]["J6"]
            candidate_error.append(dict(group=g,doi=c["doi"],entry=c["entry"],
                actual_J6=actual, J5=c["J5"],predicted_one=beta1[c["id"]],
                predicted_three=beta3[c["id"]],
                log_err_one=math.log(beta1[c["id"]]/actual) if valid_positive(actual) else "",
                log_err_three=math.log(beta3[c["id"]]/actual) if valid_positive(actual) else "",
                p5=c["p5"],p6_observed_posthoc=labels[c["id"]]["p6"]))
        rows.append(record)
    save_csv(out / "03_group_predictions_and_regret.csv",rows)
    save_csv(out / "04_posthoc_candidate_errors.csv",candidate_error)
    require(sum(x["STY_correct"] for x in rows)==12, "frozen STY first-choice accuracy changed")
    # Frozen selectivity's 23/40 applies to a tied *choice set*, not automatically the deterministic first pick.
    tie_correct = 0
    for g,es in groups.items():
        max_s=max(c["SMeOH"] for c in es)
        ties=[c for c in es if c["SMeOH"]>=max_s-1e-9*abs(max_s)]
        best_sty=max(c["STY"] for c in ties)
        tie_set=[c for c in ties if c["STY"]>=best_sty-1e-12]
        if any(c["catalyst"]==outcomes[(g,"S6")]["plant_leader"] for c in tie_set):tie_correct+=1
    require(tie_correct==23,f"frozen selectivity tie-set anchor changed: {tie_correct}")
    score = {}
    for method in BASELINES:
        good = [r for r in rows if r[method+"_feasible"]]
        all_reg=[r[method+"_regret"] for r in good]
        score[method] = dict(correct=sum(r[method+"_correct"] for r in rows),
            accuracy=sum(r[method+"_correct"] for r in rows)/len(rows),
            infeasible=40-len(good),
            mean_regret=statistics.mean(all_reg) if good else None,
            median_regret=statistics.median(all_reg) if good else None,
            regret_gt5pct=sum(z>.05 for z in all_reg),
            accuracy_paper_bootstrap_95=exact_paper_bootstrap(rows, method+"_correct"))
    if all(x["S_feasible"] and x["three_feature_feasible"] and x["S5_feasible"] for x in rows):
        for comparison in ("S", "S5", "STY"):
            for measure in ("correct", "regret"):
                col = f"paired_three_minus_{comparison}_{measure}"
                for r in rows:
                    r[col] = r["three_feature_"+measure] - r[comparison+"_"+measure]
                score["three_feature"][col+"_bootstrap_95"] = exact_paper_bootstrap(rows, col)
    decisive=[r for r in rows if r["three_feature_decisive_5pct"]]
    score["three_feature_abstention_5pct"]=dict(n=len(decisive),
        coverage=len(decisive)/40,
        accuracy=(statistics.mean(r["three_feature_correct"] for r in decisive) if decisive else None),
        mean_regret=(statistics.mean(r["three_feature_regret"] for r in decisive) if decisive else None),
        infeasible=sum(not r["three_feature_feasible"] for r in decisive))
    valid3=[abs(float(r["log_err_three"])) for r in candidate_error if isinstance(r["log_err_three"],float)]
    valid1=[abs(float(r["log_err_one"])) for r in candidate_error if isinstance(r["log_err_one"],float)]
    report = {"status":"MODEL_CONDITIONAL_INTERNAL_HELDOUT_PAPERS_ONLY",
        "protocol":"PROTOCOL.md fixed before implementation","total_source_printed_rows":351,
        "scored_entries":310,"groups":40,"papers":28,
        "frozen_anchors":{"S5_inversions":15,"S6_inversions":28,
                          "STY_first_choice_correct":12,"selectivity_tie_set_correct":tie_correct},
        "surrogate_training":{"paper_balanced":True,"lambda":RIDGE,
            "target":"log_J6_over_J5_on_training_DOIs_only",
            "features":FEATURES,"test_time_S6_feasibility_used":False},
        "performance":score,
        "candidate_abs_log_cost_error_mean":{"one_feature":statistics.mean(valid1),
                                              "three_feature":statistics.mean(valid3)},
        "notes":["The S5 cost features require per-candidate S5 process optimization.",
                 "Training labels are plant MODEL costs, not independent measured industrial costs.",
                 "The negative/positive comparison is descriptive on the existing 40 groups.",
                 "S6 outcome data are read in the scoring pass only for each heldout paper.",
                 "No post-hoc corrections, industrial validation or prospective generalization."]}
    (out / "summary.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    lines=["# Paper-held-out S5-to-S6 cost transfer (source-model-conditioned)","",
      "40 frozen within-paper comparisons; 310 scored entries; 28 papers.","",
      "| Predictor | Correct /40 | Mean regret | >5% regret | Infeasible selections |",
      "|---|---:|---:|---:|---:|"]
    for method in BASELINES:
        v=score[method];lines.append(f"| {method} | {v['correct']}/40 | {v['mean_regret']:.3f} | {v['regret_gt5pct']} | {v['infeasible']} |")
    abst=score["three_feature_abstention_5pct"]
    lines+=["",f"5% prediction-margin gate accepts {abst['n']}/40 groups.",
             "The surrogate is trained on *other papers' process-model S6 outputs*; it does not use the held-out paper's S6 outputs or S6 feasibility to select. This is NOT a predictor based only on laboratory data.",
             "All retrospective outcomes, including worse performance or infeasible choices, are retained.",
             "Study 4 of the previous PR confirms that NH3 industrial closure is still not established."]
    (out/"REPORT.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    print(json.dumps({"anchors":report["frozen_anchors"],
                      "scores":{k:{"correct":v["correct"],"mean_regret":v["mean_regret"],"infeasible":v["infeasible"]} for k,v in score.items() if k in BASELINES},
                      "abstention":abst},indent=2))


if __name__ == "__main__":
    main()
