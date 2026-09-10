"""
DISCOVER-BOUNDARY-C1 batch runner. Adds NO protocol logic: policy-E runs go through the frozen driver
discover.formal_e.run_one (byte-identical to V1) and D reference runs through the frozen discover.run.run_policy.
Only budget, run index, output directory and tag are set here. Frozen hashes are checked and recorded before and after.

Usage (from harness root):
  python discover/boundary_c1_runner.py hashcheck  --label before
  python discover/boundary_c1_runner.py smoke      --model gpt-5.5-2026-04-23 --budgets 150,175,200,225,250
  python discover/boundary_c1_runner.py e          --model gpt-5.5-2026-04-23 --budgets 150,175,200,225,250 --runs 20 --start-run 0
  python discover/boundary_c1_runner.py d          --budgets 150,175,225
  python discover/boundary_c1_runner.py hashcheck  --label after
"""
from __future__ import annotations
import argparse, hashlib, json, shutil, sys, time, traceback
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
from discover import formal_e                      # frozen driver (imported, not copied)
from discover import run as frozen_run             # frozen policy runner for D
OUT = ROOT / "DISCOVER_BOUNDARY_C1"
FROZEN = json.loads((ROOT / "DISCOVER_FROZEN_V1.json").read_text(encoding="utf-8"))
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


def hashcheck(label: str) -> dict:
    mism = [f for f, h in FROZEN["sha256"].items() if sha(ROOT / f) != h]
    rec = {"label": label, "utc": datetime.now(timezone.utc).isoformat(), "frozen_files": len(FROZEN["sha256"]), "mismatches": mism, "result": "PASS" if not mism else "FAIL",
           "formal_e_sha256": sha(ROOT / "discover/formal_e.py"), "runner_sha256": sha(Path(__file__)), "metrics_sha256": sha(ROOT / "discover/boundary_c1_metrics.py") if (ROOT / "discover/boundary_c1_metrics.py").exists() else None}
    (OUT / "metadata").mkdir(parents=True, exist_ok=True)
    (OUT / "metadata" / f"hashcheck_{label}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json").write_text(json.dumps(rec, indent=2), encoding="utf-8")
    print(json.dumps(rec)); return rec


def run_e(model: str, budgets: list[float], runs: int, start: int, tag: str, subdir: str, log: Path):
    out_root = OUT / subdir / model
    with open(log, "a", encoding="utf-8") as lf:
        for b in budgets:
            for r in range(start, start + runs):
                t0 = time.time()
                try:
                    rd = formal_e.run_one("anonymous", float(b), r, model, out_root, {}, tag)
                    t = json.loads((rd / "trace.json").read_text(encoding="utf-8"))
                    line = f"{model} B={b:.0f} r={r} -> winner {t['final']['answer']['industrial_winner']} spent {t['final']['spent_CU']:.0f} steps {len(t['steps'])} tokens {t['llm_meta']['tokens']} retries {t['llm_meta']['infra_retries']} {time.time()-t0:.0f}s | {t['final']['why_stop'][:70]}"
                except Exception as e:
                    line = f"{model} B={b:.0f} r={r} -> DRIVER EXCEPTION {e!r}\n{traceback.format_exc()}"
                print(line, flush=True); lf.write(line + "\n"); lf.flush()


def run_d(budgets: list[float]):
    dest = OUT / "D_reference" / "traces" / "anonymous"; dest.mkdir(parents=True, exist_ok=True)
    for b in budgets:
        rd = frozen_run.run_policy("D_fixed_voi", float(b), seed=0, tag="c1", anonymous=True)
        target = dest / rd.name; shutil.move(str(rd), str(target)); print("D", b, "->", target.relative_to(ROOT))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(); ap.add_argument("cmd", choices=["hashcheck", "smoke", "e", "d"])
    ap.add_argument("--model", default="gpt-5.5-2026-04-23"); ap.add_argument("--budgets", default="150,175,200,225,250"); ap.add_argument("--runs", type=int, default=20)
    ap.add_argument("--start-run", type=int, default=0); ap.add_argument("--label", default="check"); ap.add_argument("--tag", default="c1")
    a = ap.parse_args(); budgets = [float(x) for x in a.budgets.split(",")]
    (OUT / "logs").mkdir(parents=True, exist_ok=True)
    if a.cmd == "hashcheck": hashcheck(a.label)
    elif a.cmd == "smoke": run_e(a.model, budgets, 1, 99, "smoke", "smoke", OUT / "logs" / f"smoke_{a.model}.log")
    elif a.cmd == "e": run_e(a.model, budgets, a.runs, a.start_run, a.tag, "runs", OUT / "logs" / f"e_{a.model}_B{a.budgets.replace(',', '-')}.log")
    elif a.cmd == "d": run_d(budgets)
