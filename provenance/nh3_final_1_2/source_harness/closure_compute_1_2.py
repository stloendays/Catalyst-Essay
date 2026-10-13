"""NH3-FINAL-1.2 closure (copy of audits/closure_compute_1_1_2026-09-05.py of the NH3-FINAL-1.1 harness; only the run selection\nand the output name differ). Recompute every NH3 ground-truth quantity from the canonical NH3-FINAL-1.2 run.
Read-only w.r.t. the run; writes outputs/<canonical_run>/closure/*. The Monte Carlo replication must reproduce the run's MC
summary exactly (asserted) before any per-draw detail is written."""
import csv, json, math, sys
from pathlib import Path
import numpy as np, yaml
from scipy.optimize import brentq
from scipy.stats import kendalltau, spearmanr
ROOT = Path(__file__).resolve().parent; sys.path.insert(0, str(ROOT))
from harness_core import NH3Harness, EN0_CANON
PINS = {"canonical_run": "outputs/" + (sys.argv[1] if len(sys.argv) > 1 else (ROOT / "CANONICAL_RUN.txt").read_text(encoding="utf-8").strip())}; RUN = ROOT / PINS["canonical_run"]
OUT = RUN / "closure"; OUT.mkdir(exist_ok=True)
res = json.loads((RUN / "results.json").read_text(encoding="utf-8")); cfg = yaml.safe_load((RUN / "manifest_resolved.yaml").read_text(encoding="utf-8"))
det = res["deterministic"]; mc0 = res["monte_carlo"]; bk = res["backward_reachability"]
h = NH3Harness(cfg, ROOT); resp, cp, cached = h.build_or_load_response(); assert cached and resp.shape == (h.NSTATE, len(h.EGRID))
M = h.activity_order; act_order = det["activity_order"]

# ---------------- 1-3. ranking, rolling rho/tau, operating points
arank = {m: i + 1 for i, m in enumerate(act_order)}
raw_cost = {m: det["metals"][m]["unconstrained"]["total_cost"] for m in M}
feas_cost = {m: (det["metals"][m]["feasible"] or {}).get("total_cost") for m in M}
rows = []
for K in range(3, 16):
    sub = act_order[:K]; ar = [arank[m] for m in sub]
    er = {m: i + 1 for i, m in enumerate(sorted(sub, key=lambda m: raw_cost[m]))}
    fset = [m for m in sub if feas_cost[m] is not None]; fo = sorted(fset, key=lambda m: feas_cost[m]); fr = {m: i + 1 for i, m in enumerate(fo)}
    nf = len(fo); tie = (nf + 1 + K) / 2.0 if nf < K else None; cr = [fr[m] if m in fr else tie for m in sub]
    rho_raw = float(spearmanr(ar, [er[m] for m in sub]).statistic); tau_raw = float(kendalltau(ar, [er[m] for m in sub]).statistic)
    rho_c = float(spearmanr(ar, cr).statistic) if len(set(cr)) > 1 else math.nan; tau_c = float(kendalltau(ar, cr).statistic) if len(set(cr)) > 1 else math.nan
    rows.append(dict(K=K, rho_raw=rho_raw, tau_raw=tau_raw, rho_censored=rho_c, tau_censored=tau_c, n_feasible=nf))
assert abs(rows[0]["rho_raw"] - det["rolling"][0]["rho_raw"]) < 1e-12 and abs(rows[-1]["rho_raw"] - det["raw_global_spearman"]) < 1e-12
with (OUT / "rolling_topk_rho_tau.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

# ---------------- 4-6. Monte Carlo replication with per-draw detail (must reproduce the run's summary)
rng = np.random.default_rng(h.MC_SEED); NM = len(M); ens = np.zeros((h.MC_N, NM))
for d in range(h.MC_N):
    for j, m in enumerate(M):
        ens[d, j] = rng.normal(h.EN0[m], h.FE_SIGMA) if m == "Fe" else rng.uniform(h.EN0[m] - h.OTHER_HALF_WIDTH, h.EN0[m] + h.OTHER_HALF_WIDTH)
activity_mc = np.empty_like(ens)
for j, m in enumerate(M): activity_mc[:, j] = np.interp(ens[:, j], h.EGRID, h.response_base)
draws = []; raw_rhos = []; cens_rhos = []; top1 = []; top3a = []; top3c = []; nfeas = []; fe_feas = []
feas_count = {m: 0 for m in M}; trans = {}
for d in range(h.MC_N):
    aidx = np.argsort(-activity_mc[d]); arnk = np.empty(NM, int); arnk[aidx] = np.arange(1, NM + 1)
    rc = np.empty(NM); fc = np.full(NM, np.inf)
    for j, m in enumerate(M):
        logv = h.interp_state_vector(resp, ens[d, j]); total, V, _, _ = h.cost_arrays(m, logv); rc[j] = float(np.min(total)); mask = V <= h.V_CAP
        if np.any(mask): fc[j] = float(np.min(np.where(mask, total, np.inf)))
    ridx = np.argsort(rc); rrnk = np.empty(NM, int); rrnk[ridx] = np.arange(1, NM + 1); raw_rhos.append(float(spearmanr(arnk, rrnk).statistic)); rw = M[int(ridx[0])]
    fidx = np.where(np.isfinite(fc))[0]; nf = len(fidx); nfeas.append(nf); fe_feas.append(bool(np.isfinite(fc[M.index("Fe")])))
    for j in fidx: feas_count[M[j]] += 1
    aw = M[aidx[0]]; ew = None
    if nf:
        fsort = fidx[np.argsort(fc[fidx])]; frank = {int(i): k + 1 for k, i in enumerate(fsort)}; tie = (nf + 1 + NM) / 2.0 if nf < NM else None
        cr = np.array([frank[i] if i in frank else tie for i in range(NM)], float)
        cens_rhos.append(float(spearmanr(arnk, cr).statistic) if len(set(cr)) > 1 else math.nan)
        top1.append(float(aidx[0] == fsort[0])); a3 = set(aidx[:3]); f3 = set(fsort[:3]); inter = len(a3 & f3); top3a.append(inter / 3.0); top3c.append(inter / min(3, nf))
        ew = M[fsort[0]]
    else:
        cens_rhos.append(math.nan); top1.append(0.0); top3a.append(0.0); top3c.append(math.nan)
    trans[(aw, ew)] = trans.get((aw, ew), 0) + 1
    draws.append(dict(draw=d, E_N_Fe=ens[d, M.index("Fe")], E_N_Ru=ens[d, M.index("Ru")], E_N_Os=ens[d, M.index("Os")], n_feasible=nf, atomic_winner=aw, raw_cost_winner=rw, economic_winner=ew,
                      Fe_feasible=int(fe_feas[-1]), rho_raw=raw_rhos[-1], rho_censored=cens_rhos[-1], top1=top1[-1], top3_actionable=top3a[-1]))
summ = {"raw_rho_mean": float(np.mean(raw_rhos)), "censored_rho_mean": float(np.nanmean(cens_rhos)), "top1_survival": float(np.mean(top1)), "top3_actionable": float(np.mean(top3a)),
        "top3_conditional": float(np.nanmean(top3c)), "mean_feasible_count": float(np.mean(nfeas)), "Fe_feasibility_probability": float(np.mean(fe_feas))}
for k, v in summ.items(): assert abs(v - mc0[k]) < 1e-12, (k, v, mc0[k])
print("MC replication reproduces the run summary exactly:", {k: round(v, 4) for k, v in summ.items()})
with (OUT / "mc_draws.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(draws[0])); w.writeheader(); w.writerows(draws)
from collections import Counter
mc_detail = {"summary": summ, "feasibility_probability": {m: feas_count[m] / h.MC_N for m in M},
             "feasible_set_size_distribution": {str(k): v / h.MC_N for k, v in sorted(Counter(nfeas).items())},
             "winner_transition_fraction": {f"{a}->{e}": n / h.MC_N for (a, e), n in sorted(trans.items(), key=lambda kv: -kv[1])},
             "top1_raw_before_feasibility": float(np.mean([1.0 if dr["atomic_winner"] == dr["raw_cost_winner"] else 0.0 for dr in draws]))}
(OUT / "mc_detail.json").write_text(json.dumps(mc_detail, indent=2), encoding="utf-8")

# ---------------- 7-9. break-even sweep, scaling reachability curve, strict-scaling minimum
fe_log = h.interp_state_vector(resp, h.EN0["Fe"]); ru_log = h.interp_state_vector(resp, h.EN0["Ru"]); FE = h.eval_scenario("Fe", fe_log)["total_cost"]
sweep = []
for la in np.linspace(-1, 6, 71):
    s = h.eval_scenario("Ru", ru_log, alpha=10 ** la); sweep.append(dict(log10_alpha=float(la), alpha=10 ** la, Ru_cost=s["total_cost"], T_C=s["T_C"], P_bar=s["P_bar"], Tsep_C=s["Tsep_C"], V_m3=s["V_m3"]))
alpha_star = bk["Ru_activity_break_even_multiplier"]; sbe = h.eval_scenario("Ru", ru_log, alpha=alpha_star)
assert abs(sbe["total_cost"] - FE) < 1e-6
with (OUT / "breakeven_sweep.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(sweep[0])); w.writeheader(); w.writerows(sweep)
base_ru = float(h.base_condition.logtof(h.EN0["Ru"])); ref_gain = 10 ** (h.response_base - base_ru)
ru_state = h.interp_state_vector(resp, h.EN0["Ru"]); state_gain_vec = np.power(10.0, np.max(resp, axis=1) - ru_state)
maskE = (h.EGRID >= -2.2) & (h.EGRID <= 0.2); strict = []
for j in np.where(maskE)[0]:
    total, V, _, _ = h.cost_arrays("Ru", resp[:, j]); ok = V <= h.V_CAP
    strict.append(dict(E_N_eV=float(h.EGRID[j]), gain_673K=float(ref_gain[j]), Ru_min_feasible_cost=float(np.min(np.where(ok, total, np.inf))) if np.any(ok) else None))
with (OUT / "scaling_reachability.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(strict[0])); w.writeheader(); w.writerows(strict)
best = min((r for r in strict if r["Ru_min_feasible_cost"] is not None), key=lambda r: r["Ru_min_feasible_cost"])
assert abs(best["Ru_min_feasible_cost"] - bk["Ru_best_scaling_cost_USD_t"]) < 1e-9 and abs(float(np.max(ref_gain)) - bk["Ru_scaling_max_gain_673K"]) < 1e-9 and abs(float(np.max(state_gain_vec)) - bk["Ru_scaling_max_gain_all_states"]) < 1e-9

# ---------------- headline summary
f = {m: det["metals"][m]["feasible"] for m in ("Fe", "Ru", "Os")}
head = {"model_version": cfg["project"]["model_version"], "canonical_run": PINS["canonical_run"], "process_state_count": det["process_state_count"],
        "activity_order": act_order, "feasible_economic_order": det["feasible_economic_order"], "raw_economic_order": det["raw_economic_order"],
        "top3_spearman": det["rolling"][0]["rho_raw"], "top3_kendall": rows[0]["tau_raw"], "global_spearman_raw": det["raw_global_spearman"], "global_kendall_raw": rows[-1]["tau_raw"],
        "global_spearman_censored": det["censored_global_spearman"],
        "optima": {m: {k: f[m][k] for k in ("total_cost", "T_C", "P_bar", "Tsep_C", "V_m3", "logTOF")} | {"breakdown": f[m]["breakdown"]} for m in f},
        "Ru_over_Fe": f["Ru"]["total_cost"] / f["Fe"]["total_cost"], "Ru_minus_Fe": f["Ru"]["total_cost"] - f["Fe"]["total_cost"],
        "monte_carlo": summ, "feasibility_probability": mc_detail["feasibility_probability"], "feasible_set_size_distribution": mc_detail["feasible_set_size_distribution"],
        "winner_transition_fraction": mc_detail["winner_transition_fraction"], "top1_raw_before_feasibility": mc_detail["top1_raw_before_feasibility"],
        "backward": bk | {"break_even_state": {k: sbe[k] for k in ("T_C", "P_bar", "Tsep_C", "V_m3")}, "Fe_cost_at_parity": FE, "best_scaling_E_N": best["E_N_eV"]}}
(OUT / "headline_1_2.json").write_text(json.dumps(head, indent=2), encoding="utf-8")
print(json.dumps({k: head[k] for k in ("feasible_economic_order", "top3_spearman", "top3_kendall", "global_spearman_raw", "global_kendall_raw", "Ru_over_Fe")}, indent=None))
print("break-even state:", head["backward"]["break_even_state"], "| best scaling E_N", best["E_N_eV"])
print("wrote", OUT)
