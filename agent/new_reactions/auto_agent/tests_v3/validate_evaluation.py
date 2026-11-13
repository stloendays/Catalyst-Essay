"""Offline evaluation compatibility, common-record fallback and hidden-reference tests."""
import json
import contextlib
import io
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import evaluate_builds as ev


def _validate():
    for rx in ("pdh", "ch4"):
        before = json.loads((Path(tempfile.gettempdir()) / f"v3_{rx}_before.json").read_text(encoding="utf-8"))
        after = json.loads((ev.HERE / "evaluation" / f"{rx}_builds.json").read_text(encoding="utf-8"))
        assert after.pop("common_record_count") == (59 if rx == "pdh" else 255)
        for b in after["builds"].values():  # field added with the grouped (atomic) targets; empty for PDH/CH4
            if b.get("group_targets") == {}:
                b.pop("group_targets")
        assert before == after, rx
        for name, result in after["builds"].items():
            print(f"{Path(name).name}: cost={result['reference_cost']:.12g}; {result['tea_within']}/{result['tea_n']}; verdict={result['tea_verdict']}; unchanged")
        print(f"{rx}: ALL numerical/verdict fields identical (JSON equality excluding added common_record_count)")
    with tempfile.TemporaryDirectory(prefix="v3-evaluation-") as tmp:
        ws = Path(tmp)
        runs = [ws/str(i) for i in range(2)]
        for i, p in enumerate(runs):
            p.mkdir()
            (p/"records.csv").write_text("paper,idx,catalyst,T_K,P_bar,X,S,r,y_key,y_h2,t_cycle_h,elements,usable\np,1,Ni toy,600,1,0.5,1,2,1,,,[],True\n" +
                ("q,2,Fe,610,1,0.4,1,1,1,,,[],True\n" if i == 0 else ""), encoding="utf-8")
        common = ev.common_records("missing_synthetic_reaction", runs)
        assert len(common) == 1 and common[0]["r"] == 2 and common[0]["components"] == []
        print("Missing data common-record fallback: intersection 1/2, contract conversion PASS")
        ref = dict(balances={}, parts={}, cost_usd_per_t=1)
        target = dict(quantity="total_cost", value=1.1, tol_abs=.2, source="toy")
        assert ev.evaluate_targets(ref, dict(toy=target))["toy"]["within"]
        (ws/"atomic.py").write_text("ATOMIC={'descriptor_range':[-2,2]}\nDESCRIPTORS={}\ndef logtof(D,T_K,p_bar): return -(D-.4)**2\n", encoding="utf-8")
        targets = dict(toy=dict(quantity="atomic_optimum_D", value=.4, tol_abs=.02,
                               conditions=dict(T_K=673, p_bar=dict(NH3=.9, N2=.025, H2=.075)), source="toy"))
        assert ev.evaluate_targets(ref, targets, ws)["toy"]["within"]
        print("tol_abs and atomic optimum at target conditions: PASS (D=0.4)")
        hidden = ev.hidden_atomic_reference(ws, dict(targets=targets))
        print("Hidden reference:", json.dumps(hidden))
        assert hidden["status"] == "computed_report_only", hidden
        assert all(x["spearman"] is not None for x in hidden["results"])
    validate_audit()


def validate_audit():
    import audit_holdout as audit
    with tempfile.TemporaryDirectory(prefix="v3-audit-") as tmp:
        p = Path(tmp)
        (p/"trace.jsonl").write_text(json.dumps({"tool_definitions": "holdout definitions"})+"\n", encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):
            assert not audit.audit(p, "ch4")["leak"]
            (p/"report.md").write_text("holdout", encoding="utf-8")
            assert audit.audit(p, "ch4")["leak"]
            (p/"report.md").write_text("synthetic report", encoding="utf-8")
            (p/"ch4_builds.json.backup").write_text("{}", encoding="utf-8")
            assert audit.audit(p, "ch4")["leak"]
        print("Leak audit: clean/tool definitions PASS; agent-written holdout string and evaluation filename prefix rejected: PASS")


def validate():
    paths = [ev.HERE/"evaluation"/f"{rx}_builds.json" for rx in ("pdh", "ch4")]
    originals = {p: p.read_bytes() for p in paths}
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            for rx in ("pdh", "ch4"):
                ev.main(rx, [f"D:/agent_runs/{rx}_b{i}" for i in (1, 2, 3)])
        _validate()
    finally:
        for p, data in originals.items():
            p.write_bytes(data)
            assert p.read_bytes() == data
        print("Evaluation artifacts restored byte-for-byte after regression tests")


if __name__ == "__main__":
    validate()
