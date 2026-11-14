"""Build db/truth.json for the masked-database agent from the usable records of ../analyze.load:
paper codes instead of DOIs; visible conditions, lab conversion and the reactant conversion rate
(product rate / selectivity, so the visible columns carry no selectivity); masked selectivity and stability.

Record ids and paper codes are stable: a record already in db/truth.json keeps its id and paper code (matched on
paper file stem and record index); new records and papers are numbered after the existing ones."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import analyze as an  # noqa: E402

MW = {"pdh": 42.081, "ch4": 16.043}
path = HERE / "db" / "truth.json"
old = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
out = {}
for rx in ("pdh", "ch4"):
    rows = an.load(rx)
    prev = old.get(rx, [])
    id_of = {(t["_true_paper"], int(t["_idx"])): t["rec_id"] for t in prev}
    code_of = {t["_true_paper"]: t["paper"] for t in prev}
    n_id = max([int(t["rec_id"].split("-")[1]) for t in prev] or [0])
    n_code = max([int(t["paper"][1:]) for t in prev] or [0])
    for p in sorted({r["paper"] for r in rows}):
        if p not in code_of:
            n_code += 1
            code_of[p] = f"P{n_code:02d}"
    db = []
    for r in rows:
        key = (r["paper"], int(r["idx"]))
        if key not in id_of:
            n_id += 1
            id_of[key] = f"{rx.upper()}-{n_id:03d}"
        src = {"printed": "from printed rate"}.get(r["r_src"], "from feed flow x conversion")
        db.append(dict(
            rec_id=id_of[key], paper=code_of[r["paper"]], catalyst=r["catalyst"],
            composition_wt_pct=r["elements"], T_C=round(r["T_K"] - 273.15, 1), P_bar=round(r["P_bar"], 3),
            feed=r["feed"], key_reactant_fraction=r["y_key"], h2_fraction=r["y_h2"],
            lab_conversion=round(r["X"], 4), value_source=r["source"],
            lab_reactant_conversion_rate_mol_per_kg_h=round(r["r_kg_kg_h"] * 1000 / (r["S"] * MW[rx]), 4),
            rate_source=src,
            _selectivity=round(r["S"], 4), _lab_productivity_kg_per_kg_h=r["r_kg_kg_h"],
            _stability=dict(initial_conversion=r["X0"] or None, final_conversion=r["Xf"] or None,
                            duration_h=r["stab_dur_h"] or None, cycle_h_to_lose_10pct=r["t_cycle_h"]),
            _true_paper=r["paper"], _idx=r["idx"]))
    db.sort(key=lambda t: t["rec_id"])
    out[rx] = db
    print(rx, len(db), "records", len({t["paper"] for t in db}), "papers", 2 * len(db), "masked cells")
path.parent.mkdir(exist_ok=True)
path.write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
