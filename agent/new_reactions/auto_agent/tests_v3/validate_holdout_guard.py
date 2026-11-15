"""Held-out guard (2026-11-15): spelling variants, keyword sets and DOIs in tool arguments, replayed on the strings that
leaked in ch4_v34_t4/t5; ordinary methanation text passes."""
import json
import sys
from pathlib import Path

A = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(A))
from runner import holdout_hit  # noqa: E402

h = json.loads((A / "holdout" / "ch4.json").read_text(encoding="utf-8"))
for leaked in ["search: STORE&GO methanation demonstration Falkenhagen", "Store & Go final report",
               'parameter,value,source\ncapex,1,https://doi.org/10.1002/CITE.202000187', "Falkenhagen plant 720 €/kW SNG"]:
    assert holdout_hit(h, leaked), leaked
for clean in ["CO2 methanation Ni catalyst kinetics fixed bed", "Sabatier reactor TREMP recycle", "store go"]:
    assert holdout_hit(h, clean) is None, clean
for t in Path("D:/agent_runs").glob("ch4_v34_t[45]/sources.csv"):
    assert holdout_hit(h, t.read_text(encoding="utf-8")), t
print("holdout guard: variants, keyword sets, DOI in arguments caught; clean text passes; t4/t5 sources.csv caught: PASS")
