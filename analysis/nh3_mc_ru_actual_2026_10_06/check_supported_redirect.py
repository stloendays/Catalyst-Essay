"""Check that run_mc_ru_actual.derive_supported() -- analysis/nh3_supported_2026_10_06/run_supported_chain.main(),
unchanged, on the selected harness, written to a temporary folder -- reproduces the committed
analysis/nh3_supported_2026_10_06/supported_candidates.csv cell for cell under NH3_MODEL=1.1. This is what makes the
1.2 measured-catalyst inputs (variants B and B0) a re-derivation on the same definition.

    NH3_MODEL=1.1 python check_supported_redirect.py
"""
import csv
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("run_mc_ru_actual", HERE / "run_mc_ru_actual.py")
mc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mc)
assert mc.NM.VERSION == "1.1", "the committed supported_candidates.csv is the 1.1 one"
h = mc.NM.harness()
response, _cp, cached = h.build_or_load_response()
assert cached, "response surface is not cached; refusing to rebuild a frozen asset"
rows = mc.derive_supported(h, response)
with mc.SUPPORTED.open(encoding="utf-8") as f:
    ref = list(csv.DictReader(f))
assert [r["id"] for r in rows] == [r["id"] for r in ref], "row ids differ"
diff = [(a["id"], k, a[k], b[k]) for a, b in zip(rows, ref) for k in ref[0] if a[k] != b[k]]
print(f"rows {len(rows)} / committed {len(ref)}; cell differences {len(diff)}; "
      f"measured Ru catalysts {sum(mc.is_measured_ru(x) for x in rows)}")
assert not diff, diff[:10]
