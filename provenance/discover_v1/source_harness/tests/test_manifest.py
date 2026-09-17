from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_canonical_manifest_is_1_1():
    c = yaml.safe_load((ROOT / 'configs/nh3_final.yaml').read_text(encoding='utf-8'))
    assert c['project']['model_version'] == 'NH3-FINAL-1.1'
    assert c['process']['pressure_bar'] == {'start': 10, 'stop': 1000, 'step': 5}
    assert c['economics']['pressure_capex']['enabled'] is True
    assert c['uncertainty']['draws'] == 1000 and c['uncertainty']['seed'] == 20260816
    assert c['engineering']['max_catalyst_bed_m3'] == 90.0
    assert c['frozen_regression']['process_state_count'] == 14136


def test_archived_1_0_manifest_immutable():
    c = yaml.safe_load((ROOT / 'configs/nh3_final_1.0_archived.yaml').read_text(encoding='utf-8'))
    assert c['project']['model_version'] == 'NH3-FINAL-1.0'
    assert c['process']['pressure_bar']['stop'] == 300 and 'pressure_capex' not in c['economics']
    assert c['frozen_regression']['process_state_count'] == 3636
