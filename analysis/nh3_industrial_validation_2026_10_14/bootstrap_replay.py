#!/usr/bin/env python3
"""Bootstrap the existing NH3 industrial benchmark without changing scientific modules.

The repository has two different files named nh3_model.py:
  analysis/nh3_model.py (shared selected-version module)
  analysis/validation_nh3_plant_2026_10_13/nh3_model.py (plant benchmark adapter)

staged_converter/converter.py imports the FIRST module as nh3_model, while the
plant benchmark imports the SECOND. In a bare clean runner the latter is still
partially imported when converter.py requests the former, raising a circular
import. Prime the shared converter dependencies before loading the adapter.
No process/kinetic/economic function is patched or modified.
"""
from __future__ import annotations

import argparse
import importlib
import runpy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ANALYSIS = ROOT / "analysis"
STAGED = ANALYSIS / "nh3_staged_converter_2026_10_12"
PLANT = ANALYSIS / "validation_nh3_plant_2026_10_13"


def prepare() -> None:
    sys.path.insert(0, str(ANALYSIS))
    shared = importlib.import_module("nh3_model")
    assert shared.__file__ and Path(shared.__file__).resolve() == ANALYSIS / "nh3_model.py"
    assert shared.VERSION == "1.2", "Full replay requires NH3_MODEL=1.2"

    sys.path.insert(0, str(STAGED))
    converter = importlib.import_module("converter")
    swap = importlib.import_module("kinetics_swap")
    assert converter.NM is shared, "Converter must bind the shared version selector"
    # Benchmark adapter must now be importable under its own expected top-level
    # name. Converter and kinetics already retain module references to shared.
    old = sys.modules.pop("nh3_model")
    assert old is shared
    sys.path.insert(0, str(PLANT))
    adapter = importlib.import_module("nh3_model")
    assert adapter.__file__ and Path(adapter.__file__).resolve() == PLANT / "nh3_model.py"
    assert adapter.NM.VERSION == shared.VERSION
    assert adapter.C is converter and adapter.S is swap
    assert adapter.VERSION == "1.2"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("test", "benchmark"))
    parser.add_argument("--workers", type=int, default=2)
    args = parser.parse_args()
    prepare()
    if args.mode == "test":
        suite = unittest.defaultTestLoader.discover(str(PLANT), pattern="test_reproduce.py")
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        if not result.wasSuccessful():
            raise SystemExit(1)
    else:
        sys.argv = [str(PLANT / "run_benchmark.py"), "--workers", str(args.workers)]
        runpy.run_path(str(PLANT / "run_benchmark.py"), run_name="__main__")


if __name__ == "__main__":
    main()
