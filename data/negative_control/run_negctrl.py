"""Run NEGATIVE CONTROL V0.1 end to end: frozen-hash check -> deterministic chain -> leverage -> MC -> NH3 reference -> outputs."""
from __future__ import annotations
import csv, hashlib, json, platform, sys, time
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "negative_control"))
from n2o_core import N2OHarness, nh3_reference_metrics, PRICE, MW  # noqa: E402

VER = sys.argv[1] if len(sys.argv) > 1 else "v0_1"
CFG = ROOT / f"configs/n2o_negcontrol_{VER}.yaml"
FROZEN = ROOT / f"NEGATIVE_CONTROL_{VER.upper()}_FROZEN.json"


def sha(p: Path) -> str: return hashlib.sha256(p.read_bytes()).hexdigest()


def _mc_chunk(args):
    cfg, seed_offset, n = args
    h = N2OHarness(cfg)
    u = cfg["uncertainty"]; hw = float(u["descriptor_uniform_half_width_eV"]); rng = np.random.default_rng(int(u["seed"]) + seed_offset)
    crit = cfg["rank_preservation_criteria"]; rows = []
    for _ in range(n):
        draw = {m: h.dEO[m] + rng.uniform(-hw, hw) for m in h.metals}
        act = {m: h.atomic_logtof(draw[m]) for m in h.metals}
        ao = sorted(h.metals, key=lambda m: act[m], reverse=True)
        cost = {}
        for m in h.metals:
            o = h.optimize(m, dEO_override=draw[m])["feasible"]; cost[m] = o["total"] if o else None
        mt = h.rank_metrics(ao, cost, h.metals)
        rows.append({"atomic_winner": ao[0], "economic_winner": mt["economic_winner"], "C1": mt["atomic_winner_is_economic_winner"],
                     "top3": mt["top3_spearman"], "top5": mt["top5_spearman"], "full": mt["full_spearman"], "tau": mt["full_kendall"],
                     "inv_frac": mt["pairwise_inversion_fraction"], "n_feasible": mt["n_feasible"],
                     "C2": (mt["top3_spearman"] == mt["top3_spearman"]) and mt["top3_spearman"] >= float(crit["C2_top3_spearman_min"])})
    return rows


def main():
    t0 = time.time()
    fz = json.loads(FROZEN.read_text(encoding="utf-8"))
    mism = [f for f, hsh in fz["sha256"].items() if sha(ROOT / f) != hsh]
    assert not mism, f"frozen mismatch: {mism}"
    cfg = yaml.safe_load(CFG.read_text(encoding="utf-8"))
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = ROOT / "outputs" / f"n2o_negctrl_{VER}_{ts}"; out.mkdir(parents=True); (out / "figures").mkdir()
    h = N2OHarness(cfg)
    print("states per candidate:", len(h.T_grid_C) * len(h.D_grid), "| t N2O/y:", round(h.t_N2O_y, 1), flush=True)
    det = h.deterministic()
    print("atomic:", det["activity_order"], flush=True)
    print("economic (feasible):", det["metrics_feasible_censored"]["economic_order_feasible"], flush=True)
    lev = {m: h.leverage(m) for m in h.metals}
    print("leverage done", round(time.time() - t0), "s", flush=True)
    # MC, parallel over draws
    n = int(cfg["uncertainty"]["draws"]); workers = 8; per = n // workers
    chunks = [(cfg, k * 1000003, per + (1 if k < n - per * workers else 0)) for k in range(workers)]
    with ProcessPoolExecutor(max_workers=workers) as ex:
        rows = [r for part in ex.map(_mc_chunk, chunks) for r in part]
    assert len(rows) == n
    crit = cfg["rank_preservation_criteria"]
    def okall(r):
        return r["C1"] and r["C2"] and r["top5"] >= float(crit["C3_top5_spearman_min"]) and r["full"] >= float(crit["C4_full_set_spearman_min"]) \
            and r["inv_frac"] <= float(crit["C5_pairwise_inversion_fraction_max"]) and r["tau"] >= float(crit["C6_kendall_tau_full_min"])
    ew = {}; aw = {}
    for r in rows:
        ew[r["economic_winner"]] = ew.get(r["economic_winner"], 0) + 1; aw[r["atomic_winner"]] = aw.get(r["atomic_winner"], 0) + 1
    t3 = np.array([r["top3"] for r in rows], float)
    mc = {"draws": n, "seed": int(cfg["uncertainty"]["seed"]), "seed_note": "per-worker streams seed + k*1000003, 8 workers; draw order not identical to a single-stream run",
          "half_width_eV": float(cfg["uncertainty"]["descriptor_uniform_half_width_eV"]),
          "P_C1_winner_preserved": sum(r["C1"] for r in rows) / n, "P_C2_top3_rho_ge_0.5": sum(bool(r["C2"]) for r in rows) / n, "P_all_criteria": sum(okall(r) for r in rows) / n,
          "top3_rho_mean": float(np.nanmean(t3)), "top3_rho_p10_p90": [float(np.nanpercentile(t3, 10)), float(np.nanpercentile(t3, 90))],
          "full_rho_mean": float(np.nanmean([r["full"] for r in rows])), "inv_frac_mean": float(np.nanmean([r["inv_frac"] for r in rows])),
          "economic_winner_counts": ew, "atomic_winner_counts": aw, "draws_table": rows}
    print("MC done", round(time.time() - t0), "s", flush=True)
    nh3 = nh3_reference_metrics(ROOT / cfg["reference_comparison"]["nh3_canonical_run"] / "results.json")
    # criteria evaluation
    mf = det["metrics_feasible_censored"]
    checks = {"C1_atomic_winner_is_economic_winner": mf["atomic_winner_is_economic_winner"],
              "C2_top3_spearman": (mf["top3_spearman"], mf["top3_spearman"] >= float(crit["C2_top3_spearman_min"])),
              "C3_top5_spearman": (mf["top5_spearman"], mf["top5_spearman"] >= float(crit["C3_top5_spearman_min"])),
              "C4_full_spearman": (mf["full_spearman"], mf["full_spearman"] >= float(crit["C4_full_set_spearman_min"])),
              "C5_pairwise_inversion_fraction": (mf["pairwise_inversion_fraction"], mf["pairwise_inversion_fraction"] <= float(crit["C5_pairwise_inversion_fraction_max"])),
              "C6_full_kendall": (mf["full_kendall"], mf["full_kendall"] >= float(crit["C6_kendall_tau_full_min"]))}
    passed = all(v if isinstance(v, bool) else v[1] for v in checks.values())
    results = {"project": cfg["project"], "run_id": out.name, "status": "PASS" if passed else "FAIL", "criteria": checks, "deterministic": det, "leverage": lev, "monte_carlo": mc,
               "nh3_reference": nh3, "prices_USD_kg": {m: PRICE[m] for m in h.metals}, "MW_kg_mol": {m: MW[m] for m in h.metals},
               "plant": {"t_N2O_destroyed_per_y": h.t_N2O_y, "F_N2O_mol_s": h.F_N2O, "tail_gas_mol_s": h.mol_s, "crf": h.crf}}
    (out / "results.json").write_text(json.dumps(results, indent=1, default=float), encoding="utf-8")
    prov = {"created_utc": datetime.now(timezone.utc).isoformat(), "python": sys.version, "platform": platform.platform(), "config": str(CFG.relative_to(ROOT)), "config_sha256": sha(CFG),
            "frozen_file": FROZEN.name, "frozen_sha256": sha(FROZEN), "frozen_hash_check": "PASS", "code_sha256": {"negative_control/n2o_core.py": sha(ROOT / "negative_control/n2o_core.py"), "negative_control/run_negctrl.py": sha(Path(__file__))},
            "harness_core_sha256": sha(ROOT / "harness_core.py"), "nh3_reference_results_sha256": sha(ROOT / cfg["reference_comparison"]["nh3_canonical_run"] / "results.json"),
            "model_version": cfg["project"]["model_version"], "git": "harness root is not a git repository; provenance = hashes above", "wall_s": time.time() - t0}
    (out / "provenance.json").write_text(json.dumps(prov, indent=2), encoding="utf-8")
    # canonical CSV
    with open(out / "canonical_results.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["metal", "dEO_eV", "atomic_rank", "atomic_log10TOF_ref", "theta_O_ref", "economic_rank_feasible", "feasible", "cost_USD_per_tN2O", "T_opt_C", "D_opt_m", "L_m", "V_m3", "metal_kg", "dP_bar", "metal_cost", "reactor_base", "vessel_pressure_premium", "heating", "pressure_drop", "elasticity_dlnC_dlnTOF", "price_USD_kg"])
        erank = {m: i + 1 for i, m in enumerate(mf["economic_order_feasible"])}
        for i, m in enumerate(det["activity_order"]):
            d = det["metals"][m]; fe = d["feasible"]
            w.writerow([m, d["dEO"], i + 1, round(d["activity_logTOF"], 4), round(d["theta_O_ref"], 5), erank.get(m, ""), bool(fe)] + ([round(fe["total"], 3), fe["T_C"], fe["D_m"], round(fe["L_m"], 3), round(fe["V_m3"], 3), round(fe["metal_kg"], 2), round(fe["dP_bar"], 4), round(fe["metal_cost"], 3), round(fe["reactor_base"], 3), round(fe["vessel_pressure_premium"], 4), round(fe["heating"], 3), round(fe["pressure_drop"], 3)] if fe else [""] * 12) + [lev[m]["elasticity_dlnC_dlnTOF"], PRICE[m]])
    print("wrote", out, "status", results["status"], round(time.time() - t0), "s")
    return out


if __name__ == "__main__":
    main()
