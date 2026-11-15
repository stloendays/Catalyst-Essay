"""Amendment A13: generic V3.6 hybrid workflow, registry and typed interfaces.

Amends A12; preserves existing holdout targets, prices, scoring, and physical gate
thresholds. Adds source coverage, experimental subprocess validation, progressive
DAG revisions, declared ranking strategy and integer/continuous separation.
Evidence: offline synthetic acceptance and development t7 reference replay only;
no API/LLM calls, no held-out numerical evidence used to choose new rules.
"""
import hashlib
import json
from datetime import datetime
from pathlib import Path

H=Path(__file__).resolve().parent
A=H.parent
previous=json.loads((H/'PREREG_V31_A12.json').read_text(encoding='utf-8'))
files=list(dict.fromkeys(list(previous['frozen_sha256'])+[
    'registry.py','interfaces.py','workflow.py','design_opt.py','tests_v3/validate_v35.py',
    'tests_v3/validate_v36.py','tests_v3/run_v36_acceptance.py',
    'docs/V36_HYBRID_HARNESS.md','docs/TRAIN_TEST_SPLIT.md','holdout/make_prereg_a13.py']))
doc=dict(id='V3.1-A13',written=datetime.now().isoformat(timespec='seconds'),amends='PREREG_V31_A12.json',
         build_mode_version='V3.6-hybrid-workflow',unit_library='UO-1.1',change=__doc__.strip(),
         frozen_sha256={f:hashlib.sha256((A/f).read_bytes()).hexdigest() for f in files})
target=H/'PREREG_V31_A13.json'
with target.open('x',encoding='utf-8') as f:
    f.write(json.dumps(doc,indent=1,ensure_ascii=False)+'\n')
print('written PREREG_V31_A13.json; frozen files:',len(files))
