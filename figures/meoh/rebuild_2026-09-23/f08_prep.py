"""Build Origin-ready inputs for Figure 8 from the frozen D01 v3 CSVs.
Applies the same guards the R renderer does, so a changed input stops here."""
import csv
import os

REPO = r"D:\论文-AI4S\Catalyst-Essay"
OUT = os.path.dirname(os.path.abspath(__file__))

NPC = ["NPC_1 wt% Re | 200 C", "NPC_5 wt% Re | 200 C",
       "NPC_1 wt% Re | 250 C", "NPC_5 wt% Re | 250 C"]
SHORT = ["1 wt% Re / 200 C", "5 wt% Re / 200 C",
         "1 wt% Re / 250 C", "5 wt% Re / 250 C"]

rows = list(csv.DictReader(open(os.path.join(REPO, "data/meoh/meoh_purge_robustness_D01v3.csv"),
                                encoding="utf-8")))
assert len(rows) == 396, "expected 396 purge levels, found %d" % len(rows)
p = [float(r["purge"]) for r in rows]
assert abs(min(p) - 0.005) < 1e-12 and abs(max(p) - 0.40) < 1e-12, "purge range is not 0.5-40%"

with open(os.path.join(OUT, "f08_panel_a.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["Purge"] + SHORT)
    for r in rows:
        w.writerow(["%.6g" % (float(r["purge"]) * 100)] + ["%.6g" % float(r[c]) for c in NPC])

anchor = [r for r in rows if abs(float(r["purge"]) - 0.02) < 1e-12]
assert len(anchor) == 1, "canonical 2% purge row not uniquely found"
a = anchor[0]
with open(os.path.join(OUT, "f08_anchor.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["Purge"] + SHORT)
    w.writerow(["2"] + ["%.6g" % float(a[c]) for c in NPC])

cand = {r["candidate"]: r for r in csv.DictReader(
    open(os.path.join(REPO, "data/meoh/meoh_candidate_ranking_D01v3.csv"), encoding="utf-8"))}
b = cand["5 wt% Re | 250 C"]
lev = [("STY", float(b["L_STY"])),
       ("Single-pass conversion", float(b["L_conversion"])),
       ("CH4 suppression", float(b["L_CH4_suppression"]))]
frozen = [0.00289430146472775, 0.05882776006061632, 0.3757939247335326]
for (n, v), f in zip(lev, frozen):
    assert abs(v - f) < 1e-12, "%s leverage differs from the frozen D01 v3 value" % n

with open(os.path.join(OUT, "f08_panel_b.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["Y", "Leverage"])
    for y, (n, v) in zip([3, 2, 1], lev):          # top row first
        w.writerow([y, "%.10g" % v])

print("panel a: %d rows, purge %.3g-%.3g %%" % (len(rows), min(p) * 100, max(p) * 100))
print("anchor 2%%: " + ", ".join("%s=%s" % (s, a[c]) for s, c in zip(SHORT, NPC)))
print("panel b: " + ", ".join("%s=%.6g" % (n, v) for n, v in lev))
print("CH4/conversion = %.3f   CH4/STY = %.3f" % (lev[2][1] / lev[1][1], lev[2][1] / lev[0][1]))
ymin = min(min(float(r[c]) for c in NPC) for r in rows)
ymax = max(max(float(r[c]) for c in NPC) for r in rows)
print("NPC range: %.1f - %.1f EUR/t" % (ymin, ymax))
