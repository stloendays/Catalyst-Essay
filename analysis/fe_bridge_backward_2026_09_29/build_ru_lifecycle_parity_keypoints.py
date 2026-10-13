"""Lifetime/recovery needed for Fe-Ru parity at the current Ru activity (README section 2), for NH3_MODEL=1.1|1.2.

At fixed intrinsic Ru activity, recovery r and lifetime L enter the Ru replacement cost through the same factor as the
price, so parity is P_Ru (1 - r) (10 y / L) <= P*, with P* the Fe-Ru parity price of the fully reoptimized Ru price
sweep (last row; 1.1: figures/composite/fig2/fig2_ru_price_sweep.csv, 1.2: nh3_1_2/ru_price_sweep.csv).

    NH3_MODEL=1.1  checks the committed ru_lifecycle_parity_keypoints.csv numerically (no write); its 32.877-y row
                   was entered by hand and is reported, not regenerated
    NH3_MODEL=1.2  writes nh3_1_2/ru_lifecycle_parity_keypoints.csv (same columns; the hand row is replaced by the
                   99 %-recovery lifetime L* = P_Ru 0.01 (10 y) / P*, rounded to 0.001 y)
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "analysis"))
import nh3_model as NM  # noqa: E402

P_RU = 53852.5
SWEEP = (ROOT / "figures/composite/fig2/fig2_ru_price_sweep.csv" if NM.VERSION == "1.1"
         else NM.out_dir(HERE) / "ru_price_sweep.csv")
with SWEEP.open(encoding="utf-8", newline="") as fh:
    P_STAR = float(list(csv.DictReader(fh))[-1]["price_USD_kg"])
L_STAR = P_RU * 0.01 * 10.0 / P_STAR


def row(life):
    rec = 1.0 - P_STAR / P_RU * (life / 10.0)
    return {"lifetime_y": life, "required_recovery_fraction": rec, "required_recovery_percent": 100.0 * rec,
            "effective_Ru_price_at_99pct_recovery_USD_kg": P_RU * 0.01 * 10.0 / life}


print(f"{NM.LABEL}: parity price P* = {P_STAR:.6f} USD/kg; 10 y -> {100 * row(10)['required_recovery_fraction']:.4f}% "
      f"recovery, 20 y -> {100 * row(20)['required_recovery_fraction']:.4f}%, 99% recovery -> {L_STAR:.3f} y")

if NM.VERSION == "1.1":
    with (HERE / "ru_lifecycle_parity_keypoints.csv").open(encoding="utf-8", newline="") as fh:
        committed = list(csv.DictReader(fh))
    worst = 0.0
    for r in committed:
        life = float(r["lifetime_y"])
        if life == 32.877:
            print(f"hand-entered row {dict(r)}; exact 99%-recovery lifetime is {L_STAR:.4f} y")
            continue
        new = row(life)
        for k, v in new.items():
            worst = max(worst, abs(float(r[k]) - v) / abs(v))
    print(f"committed 1.1 rows reproduce to max relative difference {worst:.1e} (printed precision)")
    if worst > 1e-6:
        raise SystemExit("1.1 lifecycle parity keypoints do not reproduce")
else:
    lives = sorted([5, 10, 20, 30, 40, 50, round(L_STAR, 3)])
    out = NM.out_dir(HERE) / "ru_lifecycle_parity_keypoints.csv"
    with out.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["lifetime_y", "required_recovery_fraction", "required_recovery_percent",
                    "effective_Ru_price_at_99pct_recovery_USD_kg"])
        for life in lives:
            r = row(life)
            w.writerow([life, f"{r['required_recovery_fraction']:.15f}", f"{r['required_recovery_percent']:.13f}",
                        round(r["effective_Ru_price_at_99pct_recovery_USD_kg"], 4)])
    print("wrote", out)
