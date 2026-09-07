"""Diagnostic (not part of the frozen protocol): rerun the deterministic chain with every metal at the same price to isolate
the price (inventory) channel from the process (temperature / volume) channel. Writes diagnostics_equal_price.json into the run dir."""
import json, sys, yaml
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "negative_control"))
import n2o_core
from n2o_core import N2OHarness
run = Path(sys.argv[1]); cfg = yaml.safe_load((ROOT / sys.argv[2]).read_text(encoding="utf-8"))
out = {}
for label, price in [("all_at_Ni_price", n2o_core.PRICE["Ni"]), ("all_at_Rh_price", n2o_core.PRICE["Rh"]), ("price_zero", 0.0)]:
    saved = dict(n2o_core.PRICE)
    for m in saved: n2o_core.PRICE[m] = price
    h = N2OHarness(cfg); det = h.deterministic(); mf = det["metrics_feasible_censored"]
    out[label] = {"price_USD_kg": price, "economic_order_feasible": mf["economic_order_feasible"], "atomic_order": det["activity_order"],
                  "top3_spearman": mf["top3_spearman"], "top5_spearman": mf["top5_spearman"], "full_spearman": mf["full_spearman"], "full_kendall": mf["full_kendall"],
                  "pairwise_inversion_fraction": mf["pairwise_inversion_fraction"], "winner_preserved": mf["atomic_winner_is_economic_winner"],
                  "optima": {m: ({"T_C": det["metals"][m]["feasible"]["T_C"], "cost": det["metals"][m]["feasible"]["total"], "heating": det["metals"][m]["feasible"]["heating"], "metal_cost": det["metals"][m]["feasible"]["metal_cost"]} if det["metals"][m]["feasible"] else None) for m in h.metals}}
    n2o_core.PRICE.update(saved)
    print(label, "| winner", mf["atomic_winner"], "->", mf["economic_winner"], "| top3 %.2f top5 %.2f full %.2f tau %.2f inv %.2f" % (mf["top3_spearman"], mf["top5_spearman"], mf["full_spearman"], mf["full_kendall"], mf["pairwise_inversion_fraction"]))
    print("   econ:", mf["economic_order_feasible"])
(run / "diagnostics_equal_price.json").write_text(json.dumps(out, indent=1, default=float), encoding="utf-8")
