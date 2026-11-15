"""Read-only recovery of a relocated Python venv with an unusable launcher.

Invoked with a SAME major/minor base interpreter, -I -S. Only the IDAES
environment site-packages is added; harness environment packages stay absent.
No venv changes, installs, or in-process IDAES imports in the harness.
"""
from pathlib import Path
import runpy
import sys
root=Path(sys.argv.pop(1)).resolve()
cfg=(root/'pyvenv.cfg').read_text(encoding='utf-8')
version=next(line.split('=',1)[1].strip() for line in cfg.splitlines() if line.startswith('version_info'))
if tuple(map(int,version.split('.')[:2]))!=sys.version_info[:2]:
    raise RuntimeError('relocated IDAES environment requires same Python major/minor')
sys.path.insert(0,str(root/'Lib'/'site-packages'))
sys.prefix=sys.exec_prefix=str(root)
sys.argv[0]=str(Path(__file__).with_name('run_case.py'))
runpy.run_path(sys.argv[0],run_name='__main__')
