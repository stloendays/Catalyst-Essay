"""Build db/truth.json for the masked-database agent from the usable records of ../analyze.load:
paper codes instead of DOIs; visible conditions, lab conversion and the reactant conversion rate
(product rate / selectivity, so the visible columns carry no selectivity); masked selectivity and stability."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import analyze as an  # noqa: E402

MW = {"pdh": 42.081, "ch4": 16.043}
out = {}
for rx in ("pdh", "ch4"):
    rows = an.load(rx)
    papers = {p: f"P{i + 1:02d}" for i, p in enumerate(sorted({r["paper"] for r in rows}))}
    db = []
    for i, r in enumerate(rows):
        src = {"printed": "from printed rate"}.get(r["r_src"], "from feed flow x conversion")
        db.append(dict(
            rec_id=f"{rx.upper()}-{i + 1:03d}", paper=papers[r["paper"]], catalyst=r["catalyst"],
            composition_wt_pct=r["elements"], T_C=round(r["T_K"] - 273.15, 1), P_bar=round(r["P_bar"], 3),
            feed=r["feed"], key_reactant_fraction=r["y_key"], h2_fraction=r["y_h2"],
            lab_conversion=round(r["X"], 4), value_source=r["source"],
            lab_reactant_conversion_rate_mol_per_kg_h=round(r["r_kg_kg_h"] * 1000 / (r["S"] * MW[rx]), 4),
            rate_source=src,
            _selectivity=round(r["S"], 4), _lab_productivity_kg_per_kg_h=r["r_kg_kg_h"],
            _stability=dict(initial_conversion=r["X0"] or None, final_conversion=r["Xf"] or None,
                            duration_h=r["stab_dur_h"] or None, cycle_h_to_lose_10pct=r["t_cycle_h"]),
            _true_paper=r["paper"], _idx=r["idx"]))
    out[rx] = db
    print(rx, len(db), "records", len(papers), "papers", 2 * len(db), "masked cells")
(HERE / "db").mkdir(exist_ok=True)
(HERE / "db" / "truth.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
