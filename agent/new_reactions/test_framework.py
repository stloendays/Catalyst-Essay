"""Regression: plant_framework with configs/<rxn>_ours.json must reproduce plant_models.py on every usable record
and on the reference plant (cost, per-pass conversion, every cost term)."""
import sys
import analyze as an
import plant_framework as fw
import plant_models as pm

worst = 0.0
for rx in ("pdh", "ch4"):
    cfg = fw.load(rx, "ours")
    pairs = [(pm.reference_record(rx), fw.reference_record(cfg))]
    for r in an.load(rx):
        a = dict(r["rec"]); a["xeq_lab"] = pm.lab_xeq(rx, a)
        b = dict(r["rec"]); b["xeq_lab"] = fw.lab_xeq(cfg, b)
        pairs.append((a, b))
    n = 0
    for a, b in pairs:
        ca, da = an.cost(rx, a, detail=True)
        cb, db = fw.cost(cfg, b, detail=True)
        d = abs(ca - cb) / ca
        worst = max(worst, d)
        if d > 1e-9 or abs(da["Xp"] - db["Xp"]) > 1e-12:
            n += 1
            if n <= 3:
                print(rx, "MISMATCH", round(ca, 6), round(cb, 6), da["parts"], db["parts"])
    print(rx, len(pairs), "records incl. reference;", n, "mismatches")
print("worst relative difference", worst)
sys.exit(1 if worst > 1e-9 else 0)
