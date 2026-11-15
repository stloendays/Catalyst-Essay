"""Amendment A14 (2026-11-15): unit library UO-2.0 and the IDAES adapter, plus a correction of the fixed thermo table.

UO-2.0 adds pre-written, tested modules (flash and water knockout, equilibrium / staged / PFR / CSTR reactors, catalyst
inventory, Ergun, two-component membrane, PSA energy, Kremser absorber, stripper heat, FUG distillation, heat exchanger
with LMTD, problem-table pinch targeting, steam generation, Turton equipment cost with CEPCI) so the agent assembles
these units instead of writing them. idaes_check (T1) re-computes the reference plant's mapped units in IDAES 2.13
(separate env, subprocess) and flags differences above 5 %. Thermo correction: CH3OH, C2H5OH, C2H6, C3H8, C3H6 had no gas
Shomate fit and used a constant Cp298 (298 -> 700 K enthalpy 26-33 % low); Shomate A-E fitted to the chemicals/thermo
ideal-gas Cp (298-1000 K, <= 0.5 % fit error). Found by an independent-property cross-check now in validate_idaes.py.
No holdout, target, tolerance, price or gate threshold change.
"""
import hashlib
import json
from datetime import datetime
from pathlib import Path

H = Path(__file__).resolve().parent
A = H.parent
previous = json.loads((H / 'PREREG_V31_A13.json').read_text(encoding='utf-8'))
files = list(dict.fromkeys(list(previous['frozen_sha256']) + [
    'unitops.py', 'unitops_equipment.py', 'idaes_adapter.py', 'idaes_runner/run_case.py', 'idaes_runner/property_check.py',
    'physics_gate.py', 'registry.py', 'tests_v3/validate_uo2.py', 'tests_v3/validate_idaes.py', 'docs/UO2_LIBRARY.md',
    'holdout/make_prereg_a14.py']))
doc = dict(id='V3.1-A14', written=datetime.now().isoformat(timespec='seconds'), amends='PREREG_V31_A13.json',
           build_mode_version='V3.6-hybrid-workflow', unit_library='UO-2.0', idaes='idaes-pse 2.13.0, pyomo 6.10.1',
           change=__doc__.strip(), frozen_sha256={f: hashlib.sha256((A / f).read_bytes()).hexdigest() for f in files})
(H / 'PREREG_V31_A14.json').write_text(json.dumps(doc, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
print('written PREREG_V31_A14.json; frozen files:', len(files))
