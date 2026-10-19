#!/usr/bin/env python3
"""Source-pinned exploratory NH3-FINAL-1.2 Fe/Fe-first/Ru/C phase atlas.

No kinetics, process model, economics, solver or main manuscript modified.
This is a categorical reanalysis of EXISTING staged-converter design envelopes.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
import math
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "analysis" / "nh3_staged_converter_2026_10_12" / "nh3_1_2"
FILES = {
    "boundary_price_financing.csv": "7ce211cb750c4e83a9994f9a286667bd874ef2df",
    "boundary_pressure.csv": "7cd6775690b07d652978ad12f3159c1cb8276a72",
    "design_library.csv": "5f2187c846d8d30b8a3bd3d4dc93164d52f3496a",
}
LOOPS = ((90.0, -20.0), (150.0, -5.0))
RECOVERIES = (0.9, 0.9555)
CLASSES = ("FFF", "FFR", "FRR", "RRR")
LABELS = {"FFF": "Fe only", "FFR": "Fe-Fe-Ru/C", "FRR": "Fe-Ru/C-Ru/C", "RRR": "Ru/C only"}
RATE_STEP = .005
NOMINAL_RU_PRICE = 53852.5
EPS_ROUND = 3e-5
CLOSE_001 = 0.01
CLOSE_010 = 0.10


def assert_that(truth: bool, message: str):
    if not truth:
        raise AssertionError(message)


def verify_git_blob(path: Path, expected: str):
    blob = path.read_bytes()
    actual = hashlib.sha1(
        b"blob " + str(len(blob)).encode("ascii") + b"\0" + blob
    ).hexdigest()
    assert_that(actual == expected, f"SOURCE PIN MISMATCH: {path}: {actual} != {expected}")
    return {"file": str(path.relative_to(ROOT)), "git_blob": actual, "bytes": len(blob)}


def read_csv(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def to_float(row, key):
    x = float(row[key])
    assert_that(math.isfinite(x), f"nonfinite {key} in {row}")
    return x


def source_key(row):
    return (to_float(row, "P_bar"), to_float(row, "Tsep_C"),
            to_float(row, "recovery"), to_float(row, "p_Ru"),
            to_float(row, "fin_rate"))


def winner_costs(row):
    F = to_float(row, "all_Fe")
    S = to_float(row, "staged")
    R = to_float(row, "all_Ru")
    assert_that(all(x > 0 for x in (F, S, R)), "nonpositive cost in source")
    tag = min(("FFF", F), ("staged", S), ("RRR", R), key=lambda z: z[1])[0]
    if tag == "staged":
        tag = row["staged_pattern"]
        assert_that(tag in ("FFR", "FRR"), "unsupported staged pattern in envelope")
    assert_that(row["best"] in CLASSES, "unknown source winner")
    actual = {"FFF": F, "FFR": S, "FRR": S, "RRR": R}[row["best"]]
    assert_that(actual <= min(F, S, R) + 1.1e-5,
                "source-selected catalyst no longer near numerical optimum")
    assert_that(tag == row["best"] or abs(actual-min(F,S,R)) < 1.1e-5,
                "source-selected pattern contradicted by envelope cost")
    gap = sorted((F, S, R))[1] - sorted((F, S, R))[0]
    # The competing nonchosen staged subpattern is not printed in the envelope
    # output. This is only a *three-family* margin (FFF/staged/RRR).
    return dict(label=row["best"], F=F, S=S, R=R, cost=actual,
                family_margin=max(0.,gap),
                staged_strict=int(S+1.1e-5<min(F,R)),
                better_pure_regret=max(0.,min(F,R)/S-1.0) if S+1.1e-5<min(F,R) else 0.)


def load_phase():
    pins=[verify_git_blob(SOURCE/f,blob) for f,blob in FILES.items()]
    raw=read_csv(SOURCE/"boundary_price_financing.csv")
    assert_that(len(raw)==4100, "4,100 source rows changed")
    phase={}
    for row in raw:
        k=source_key(row)
        assert_that(k not in phase, f"duplicate source scenario {k}")
        P,T,r,p,i=k
        assert_that((P,T) in LOOPS and r in RECOVERIES, "unsupported process/recovery")
        win=winner_costs(row)
        phase[k] = (row,win)
    prices=sorted({k[3] for k in phase})
    rates=sorted({k[4] for k in phase})
    assert_that(len(prices)==41 and len(rates)==25, "source Ru price/rate dimensions changed")
    assert_that(abs(prices[0]-2000.) <.01 and abs(prices[-1]-200000.)<.01,
                "source price domain changed")
    assert_that(all(abs(rt-i*RATE_STEP)<1e-8 for i,rt in enumerate(rates)),
                "source interest step/limit changed")
    for (P,T) in LOOPS:
        for r in RECOVERIES:
            for p in prices:
                for rate in rates:
                    assert_that((P,T,r,p,rate) in phase,"missing full Cartesian cost record")
    return phase,prices,rates,pins


def check_price_envelopes(phase,prices,rates):
    violations=0
    price_groups=0
    binary_sign_switches=0
    samples=[]
    for P,T in LOOPS:
        for r in RECOVERIES:
            for rate in rates:
                z=[phase[P,T,r,p,rate][1] for p in prices]
                fe=[x["F"] for x in z]
                ru=[x["R"] for x in z]
                stage=[x["S"] for x in z]
                assert_that(max(fe)-min(fe)<EPS_ROUND,
                    f"Fe-only price invariance failed: P={P}, recovery={r}, finance={rate}")
                assert_that(all(b+EPS_ROUND>=a for a,b in zip(ru[:-1],ru[1:])),
                    f"pure Ru price monotonicity failed at P={P}, recovery={r}, finance={rate}")
                assert_that(all(b+EPS_ROUND>=a for a,b in zip(stage[:-1],stage[1:])),
                    f"staged Ru price monotonicity failed at P={P}, recovery={r}, finance={rate}")
                gap=[x["R"]-x["F"] for x in z]
                assert_that(all(b+EPS_ROUND>=a for a,b in zip(gap[:-1],gap[1:])),
                    "Ru minus Fe binary price gap unexpectedly decreases")
                signs=[-1 if v<-EPS_ROUND else 1 if v>EPS_ROUND else 0 for v in gap]
                switches=sum(a==-1 and b==1 for a,b in zip(signs[:-1],signs[1:]))
                assert_that(not any(a==1 and b==-1 for a,b in zip(signs[:-1],signs[1:])),
                            "forbidden Fe->Ru reverse crossing as Ru price rises")
                assert_that(switches<=1,"two binary crossings along price")
                binary_sign_switches+=switches
                price_groups+=1
                if switches:
                    j=next(j for j in range(len(signs)-1) if signs[j]==-1 and signs[j+1]==1)
                    bracket=[z[j]["label"],z[j+1]["label"]]
                    samples.append(dict(P_bar=P,Tsep_C=T,recovery=r,fin_rate=rate,
                       p_binary_equal_low=prices[j],p_binary_equal_high=prices[j+1],
                       decision_at_lower=bracket[0],decision_at_upper=bracket[1],
                       staged_best_at_both_near_parity=int(all(x in ("FFR","FRR") for x in bracket))))
    return dict(groups_checked=price_groups,nondecreasing_cost_assertions_passed=True,
        binary_sign_crossings_bracketed=binary_sign_switches,
        hidden_binary_crossing_brackets_with_staged_best_at_both=sum(x["staged_best_at_both_near_parity"] for x in samples)),samples


def summarize_cells(phase,prices,rates):
    rows=[]
    for (P,T) in LOOPS:
        for r in RECOVERIES:
            cohort=[phase[P,T,r,p,rate][1] for rate in rates for p in prices]
            cnt=Counter(x["label"] for x in cohort)
            strict=[x for x in cohort if x["staged_strict"]]
            close01=sum(x["family_margin"] < CLOSE_001 for x in cohort)
            close10=sum(x["family_margin"] < CLOSE_010 for x in cohort)
            rows.append(dict(P_bar=P,Tsep_C=T,recovery=r,total=len(cohort),
                FFF=cnt["FFF"],FFR=cnt["FFR"],FRR=cnt["FRR"],RRR=cnt["RRR"],
                staged_strict_better_than_both_pure=len(strict),
                staged_strict_fraction=len(strict)/len(cohort),
                stage_vs_better_pure_median_relative_regret=(
                    statistics.median(x["better_pure_regret"] for x in strict) if strict else None),
                stage_vs_better_pure_max_relative_regret=(
                    max(x["better_pure_regret"] for x in strict) if strict else None),
                n_three_family_gap_below_0p01_USD_t=close01,
                n_three_family_gap_below_0p10_USD_t=close10))
    assert_that(len(rows)==4 and sum(r["total"] for r in rows)==4100,
                "phase row statistics lost model cells")
    return rows


def price_financing_paths(phase,prices,rates):
    rows=[]
    for (P,T) in LOOPS:
        for r in RECOVERIES:
            for rate in rates:
                seq=[phase[P,T,r,p,rate][1]["label"] for p in prices]
                for j,(a,b) in enumerate(zip(seq[:-1],seq[1:])):
                    if a!=b:
                        rows.append(dict(P_bar=P,Tsep_C=T,recovery=r,fin_rate=rate,
                            price_lower_USD_kg=prices[j],price_upper_USD_kg=prices[j+1],
                            from_pattern=a,to_pattern=b,
                            interpretation="discrete sampled price interval containing a category change, not a continuous root"))
    return rows


def exact_nominal_price_paths(rates):
    source=read_csv(SOURCE/"boundary_pressure.csv")
    out=[]
    for (P,T) in LOOPS:
        cohort=[x for x in source if
          float(x["P_bar"])==P and float(x["Tsep_C"])==T
          and float(x["recovery"])==0.9555 and
          float(x["p_Ru"])==NOMINAL_RU_PRICE and x["accounting"]=="dcf"]
        cohort=sorted(cohort,key=lambda z:float(z["fin_rate"]))
        assert_that(len(cohort)==25 and
           all(abs(float(z["fin_rate"])-r)<1e-8 for z,r in zip(cohort,rates)),
           "nominal price independent 25-rate source rows missing")
        for item in cohort:
            w=winner_costs(item)
            assert_that(w["label"]==item["best"],"source nominal winner changed")
        for i in range(1,len(cohort)):
            before,after=cohort[i-1],cohort[i]
            if before["best"]!=after["best"]:
                out.append(dict(P_bar=P,Tsep_C=T,p_Ru=NOMINAL_RU_PRICE,recovery=.9555,
                    lower_finance_rate=to_float(before,"fin_rate"),
                    upper_finance_rate=to_float(after,"fin_rate"),
                    from_best=before["best"],to_best=after["best"],
                    source_interval_resolution="0.5 percentage point; no precise continuous crossing inferred"))
    return out


def recovery_stability(phase,prices,rates):
    out=[]
    for P,T in LOOPS:
        changed=0
        improvements=[]
        direction={}
        for p in prices:
            for rate in rates:
                l=phase[P,T,.9,p,rate][1]
                h=phase[P,T,.9555,p,rate][1]
                delta=h["cost"]-l["cost"]
                assert_that(delta<=EPS_ROUND,
                            "higher recovery makes global optimum MORE expensive")
                improvements.append(-delta)
                changed+=l["label"]!=h["label"]
                name=l["label"]+"->"+h["label"]
                if l["label"]!=h["label"]:
                    direction[name]=direction.get(name,0)+1
        out.append(dict(P_bar=P,Tsep_C=T,n_grid_pairs=len(prices)*len(rates),
            n_winner_class_changes=changed,
            mean_cost_decrease_USD_t=statistics.mean(improvements),
            max_cost_decrease_USD_t=max(improvements),
            changes_by_pattern=direction))
    return out


def csv_write(path,rows):
    rows=list(rows)
    assert_that(rows,"do not create empty evidence file "+str(path))
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def edges_log(z):
    return [z[0]**1.5/z[1]**.5]+[(a*b)**.5 for a,b in zip(z[:-1],z[1:])]+[z[-1]**1.5/z[-2]**.5]


def edges_linear(z):
    return [z[0]-(z[1]-z[0])/2]+[(a+b)/2 for a,b in zip(z[:-1],z[1:])]+[z[-1]+(z[-1]-z[-2])/2]


def plot(phase,prices,rates,out):
    # All image data come directly from the source grid, no interpolation of pattern label.
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap,BoundaryNorm
    from matplotlib.patches import Patch
    color=["#78848b","#a8c4ab","#e0b576","#6e92b7"]
    cmap=ListedColormap(color)
    norm=BoundaryNorm([-.5,.5,1.5,2.5,3.5],4)
    fig,axs=plt.subplots(2,2,figsize=(12.5,9),layout="constrained",sharex=True,sharey=True)
    xp=edges_log(prices)
    yp=edges_linear([100*x for x in rates])
    for i,recovery in enumerate(RECOVERIES):
        for j,(P,T) in enumerate(LOOPS):
            ax=axs[i,j]
            z=[[CLASSES.index(phase[P,T,recovery,p,rate][1]["label"]) for p in prices] for rate in rates]
            ax.pcolormesh(xp,yp,z,cmap=cmap,norm=norm,shading="flat",
                          linewidth=0,rasterized=True)
            ax.axvline(NOMINAL_RU_PRICE,color="#21272e",lw=1.6,ls="--",alpha=.8)
            ax.set_xscale("log")
            ax.set_title(f"Fixed mask: {P:.0f} bar, separator {T:.0f} °C; Ru recovery {100*recovery:.2f}%")
            ax.set_xlim(prices[0]/1.08,prices[-1]*1.08)
            ax.set_ylim(-.3,12.3)
            if i==1:ax.set_xlabel("Hypothetical Ru metal price (USD/kg, log scale)")
            if j==0:ax.set_ylabel("Catalyst-metal financing rate (%/year)")
            ax.grid(False)
    fig.suptitle("Model-conditioned NH3 catalyst choice | fixed 3-bed design library",fontsize=14)
    fig.legend(handles=[Patch(facecolor=color[i],label=LABELS[label]) for i,label in enumerate(CLASSES)],
               loc="outside lower center",ncol=4,bbox_to_anchor=(.5,-.02),frameon=False)
    fig.savefig(out/"01_NH3_catalyst_decision_atlas.png",dpi=240,bbox_inches="tight")
    fig.savefig(out/"01_NH3_catalyst_decision_atlas.svg",bbox_inches="tight")
    plt.close(fig)


def make_report(summary,paths,out):
    lines=[
     "# Fe / Fe-first staged / Ru-C economic decision atlas (exploratory)",
     "",
     "**No new plant simulation was run.** All 4,100 cells re-label the original NH3-FINAL-1.2 three-bed design-library costs. NH3 manuscript and its 15-metal descriptor economics remain frozen.",
     "",
     "## Scenario assumptions",
     "Two JOINT process masks (90bar/-20°C and 150bar/-5°C); Ru gross recovery 90% or 95.55%; hypothetical Ru metal prices $2,000–$200,000/kg and financing 0–12% annually. Fe and supported promoted Ru/C evaluated through original design-library FFF, FFR, FRR, RRR patterns. A grid cell is a model-design choice, **not an experimentally validated industrial material recommendation or a probability**.",
     "",
     "## Exact grid winner counts",
     "| Mask | Recovery | All Fe | Fe-Fe-Ru | Fe-Ru-Ru | All Ru | Strict staged < both pure | Three-family margin < $0.01/t |",
     "|---|---:|---:|---:|---:|---:|---:|---:|"
    ]
    for z in summary["panels"]:
        lines.append(f"| {z['P_bar']:.0f}bar/{z['Tsep_C']:.0f}°C | {100*z['recovery']:.2f}% | {z['FFF']} | {z['FFR']} | {z['FRR']} | {z['RRR']} | {z['staged_strict_better_than_both_pure']} | {z['n_three_family_gap_below_0p01_USD_t']} |")
    lines.extend(["","## Exact nominal Ru price: $53,852.5/kg, Ru recovery 95.55%",
       "Transitions below are source-SAMPLED rate brackets, not precise continuum roots:",
       "| Mask | Winner change | Financing-rate bracket (%/year) |",
       "|---|---|---|"])
    for t in paths:
        lines.append(f"| {t['P_bar']:.0f}bar/{t['Tsep_C']:.0f}°C | {t['from_best']} → {t['to_best']} | {100*t['lower_finance_rate']:.1f}–{100*t['upper_finance_rate']:.1f} |")
    lines.extend(["","## Mathematical interpretation",
        "Proposition 1: if A's feasible domain contains B's and A's modeled cost dominates B pointwise throughout B's domain, optimizing cannot reverse A's lead. This is a sufficient condition, not verified as a physical fact by these 4,100 economic outcomes.",
        "Proposition 4: for a fixed design library and fixed financing/recovery, the min of nonnegative-price-slope design costs is monotone in Ru price. A binary Fe/Ru equality is not necessarily the actual optimum boundary when FFR/FRR costs are lower.",
        f"Price slice monotonicity checked on {summary['price_envelope_checks']['groups_checked']} independent recovery/finance/mask combinations; all passed.",
        "","## Essential empirical limitations",
        "The original Fe Dyson–Simon experimental pressure-fit domain is about 151–313bar, while promoted Ru/C Rossetti is 50–100bar; the two DO NOT overlap, so neither process mask validates matched-pressure physical Fe/Ru kinetic performance.",
        "The 90bar Fe predictions and 150bar Ru/C predictions extrapolate kinetic domains. Pressure masks also change separator temperature. Ru pricing and recovery/lease scenarios are hypothetical and may not correspond to commercial Ru buyback terms.",
        "The precomputed lower envelope is taken over a finite existing staged design library, not a newly certified global continuous process optimization. Near-tie ambiguity must be retained. No original manuscript result has been changed.",
        "","## Reproducibility",
        "GitHub Actions rechecks immutable source SHA, grid geometry, 4-way winner consistency, monotonic single-metal-price pathways and exact nominal-price sensitivity. Machine-readable audit outputs and raw categorical PNG/SVG phase plots are uploaded as workflow artifacts.",
        ""
    ])
    (out/"REPORT.md").write_text("\n".join(lines),encoding="utf-8")


def main():
    a=argparse.ArgumentParser()
    a.add_argument("--out",type=Path,required=True)
    a.add_argument("--no-plot",action="store_true")
    args=a.parse_args()
    out=args.out.resolve()
    out.mkdir(parents=True,exist_ok=True)
    phase,prices,rates,pins=load_phase()
    panels=summarize_cells(phase,prices,rates)
    checks,crossings=check_price_envelopes(phase,prices,rates)
    crossing_paths=price_financing_paths(phase,prices,rates)
    nominal_paths=exact_nominal_price_paths(rates)
    rec=recovery_stability(phase,prices,rates)
    records=[]
    for k,(source,w) in sorted(phase.items()):
        P,T,r,p,rate=k
        records.append(dict(P_bar=P,Tsep_C=T,gross_Ru_recovery=r,
          Ru_price_USD_kg=p,metal_financing_rate=rate,
          chosen_pattern=w["label"],model_cost_USD_t=w["cost"],
          all_Fe_cost_USD_t=w["F"],best_staged_cost_USD_t=w["S"],
          all_RuC_cost_USD_t=w["R"],
          staged_strict_vs_both_pure=w["staged_strict"],
          regret_better_pure_if_staged_chosen=w["better_pure_regret"],
          family_margin_to_runner_up_USD_t=w["family_margin"],
          margin_excludes_unprinted_other_staged_pattern=True))
    csv_write(out/"01_categorical_price_finance_4100.csv",records)
    csv_write(out/"02_nominal_price_rate_transitions.csv",nominal_paths)
    csv_write(out/"03_price_slice_pattern_transitions.csv",crossing_paths)
    csv_write(out/"04_binary_Fe_Ru_parity_brackets.csv",crossings)
    summary=dict(status="EXPLORATORY_SOURCE_PINNED_STAGED_LIBRARY_ATLAS__NOT_INDUSTRIAL_VALIDATION",
      source_model="NH3-FINAL-1.2 staged Fe / promoted Ru/C PFR design-library lower envelope",
      source_pins=pins,n_cells=len(phase),n_price=len(prices),n_financing=len(rates),
      process_masks=[dict(P_bar=P,Tsep_C=T) for P,T in LOOPS],
      assumed_gross_Ru_recovery=RECOVERIES,
      classes=list(CLASSES),
      n_near_ties_0p01_total=sum(z["n_three_family_gap_below_0p01_USD_t"] for z in panels),
      n_near_ties_0p10_total=sum(z["n_three_family_gap_below_0p10_USD_t"] for z in panels),
      panels=panels,price_envelope_checks=checks,
      nominal_ru_price_USD_kg=NOMINAL_RU_PRICE,
      nominal_price_recovery=.9555,
      nominal_price_pattern_brackets=nominal_paths,
      recovery_sensitivity=rec,
      science_limitation="Fe source 151-313bar vs Ru/C source 50-100bar; masks not common experimentally valid pressure domain",
      no_new_continuous_optimizer_run=True,
      manuscript_and_frozen_results_modified=False)
    (out/"summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    if not args.no_plot:
        plot(phase,prices,rates,out)
    make_report(summary,nominal_paths,out)
    print(json.dumps({"status":summary["status"],"n_cells":len(phase),
      "panels":panels,"nominal_transitions":nominal_paths,
      "recovery_changes":rec,"binary_parity":checks},ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
