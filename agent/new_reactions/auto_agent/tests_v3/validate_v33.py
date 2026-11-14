"""V3.3: library install, milestone handoff, read-only fixed files."""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import build_mode as bm  # noqa: E402
import runner  # noqa: E402


class H(bm.BuildMixin):
    def __init__(self, ws):
        self.ws, self.tok = ws, dict(agent_in=0, agent_out=0, extract_in=0, extract_out=0)
        self.reaction, self.model = "toy (A -> B)", "stub"
        self.setup_build("toy", {})

    def log(self, event):
        pass


with tempfile.TemporaryDirectory() as tmp:
    ws = Path(tmp)
    h = H(ws)
    assert h.build_version == "V3.3-process-design"
    assert (ws / "unitops.py").exists() and (ws / "physics_gate.py").exists()
    h.b_set_stage("parameters", "prices cited from prices.json; capacity 100 kt/y from source X")
    assert not getattr(h, "reset_pending", None)
    (ws / "decisions.jsonl").write_text(json.dumps({"topic": "reactor", "choice": "adiabatic fixed bed"}) + "\n", encoding="utf-8")
    (ws / "model_check.json").write_text(json.dumps({"passed": True}), encoding="utf-8")
    h.b_set_stage("model_code", "flowsheet accepted; writing model.py")
    assert h.reset_pending == "model_code"
    text = bm.stage_handoff(h, "model_code")
    assert "capacity 100 kt/y" in text and "adiabatic fixed bed" in text and "model_check.json passed" in text, text
    print("milestone handoff: notes, decisions and gate status carried: PASS")
    h.reset_pending = None
    h.b_set_stage("model_checks", "checks")
    h.b_set_stage("model_code", "back to the code")
    assert not h.reset_pending, "a milestone resets the context only on its first entry"
    print("milestone reset only once per stage: PASS")
    snap = runner.seal_snapshot(ws)
    (ws / "unitops.py").write_text("tampered", encoding="utf-8")
    msg = runner.seal_restore(ws, snap)
    assert "unitops.py" in msg and (ws / "unitops.py").read_text(encoding="utf-8") != "tampered"
    print("fixed library is read-only (edit reverted): PASS")
    assert "Process design procedure (V3.3" in bm.METHOD_BUILD_V33 and "unitops.py" in bm.METHOD_BUILD_V33
    print("V3.3 prompt present: PASS")
