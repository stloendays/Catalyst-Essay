"""开源权重模型跨模型验证运行器（DISCOVER V1 冻结协议不变，2026-09-26 计划，未运行）。

计划：../Catalyst-Essay/docs/OPEN_WEIGHTS_CROSS_MODEL_PLAN_2026-09-26.md（中文 Word 版同名）。

本脚本不含任何协议逻辑：策略 E 的 run 全部经由冻结驱动 discover.formal_e.run_one（与 V1 正式运行字节一致），
S-gate 臂经由 discover.v2_stop_runner.run_one；评分只用冻结的 DISCOVER_SCORER_V1。它只负责：
  1. 冻结哈希核查（前/后）；
  2. 端点探针：确认 OPENAI_BASE_URL 指向的 vLLM 端点能做工具调用；
  3. 准入测试：3 次 225 CU 干跑，零畸形调用 / 零未声明参数 / 零空轮 才准入；
  4. 按预注册顺序跑格：225 → 175 → 75 →（条件）5000 →（条件）S-gate 75/5000，每格 20 run，绝不重跑；
  5. 汇总：每格 P(full) 与 Wilson 95% CI、与 C1 三档的 Fisher 精确检验、窄窗口使用、规则触发/触发后花费、接口错误数。

用法（harness 根目录；先 export OPENAI_BASE_URL=http://<host>:8000/v1 与占位 OPENAI_API_KEY）：
  python discover/open_weights_runner.py serve-cmd --model Qwen/Qwen3-32B
  python discover/open_weights_runner.py hashcheck --label openweights_before
  python discover/open_weights_runner.py probe   --model Qwen3-32B
  python discover/open_weights_runner.py admit   --model Qwen3-32B
  python discover/open_weights_runner.py cells   --model Qwen3-32B
  python discover/open_weights_runner.py analyse --model Qwen3-32B
  python discover/open_weights_runner.py hashcheck --label openweights_after
"""
from __future__ import annotations
import argparse, csv, glob, hashlib, json, math, os, platform, statistics as st, sys, time, traceback
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "discover"))
from discover import formal_e                                    # 冻结策略 E 驱动（import，不复制）
from discover import v2_stop_runner                              # S-gate 臂驱动
import DISCOVER_SCORER_V1 as S                                   # 冻结 scorer
from c1_stopping_test import analyse as stopping_analyse         # 只读回放：规则触发点与触发后花费

OUT = ROOT / "DISCOVER_OPEN_WEIGHTS"
FROZEN = json.loads((ROOT / "DISCOVER_FROZEN_V1.json").read_text(encoding="utf-8"))
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
FULL_DOMAIN = 14136
CANDIDATES = {  # 优先级顺序；--tp 为张量并行 GPU 数；parser 为 vLLM 工具调用解析器
    "Qwen3-32B": {"hf": "Qwen/Qwen3-32B", "tp": 4, "parser": "hermes", "extra": "--reasoning-parser qwen3", "note": "主选；主格关闭思维模式"},
    "gpt-oss-120b": {"hf": "openai/gpt-oss-120b", "tp": 4, "parser": "openai", "extra": "", "note": "第二谱系；推理强度用服务器默认"},
    "Qwen3-235B-A22B": {"hf": "Qwen/Qwen3-235B-A22B-FP8", "tp": 8, "parser": "hermes", "extra": "--reasoning-parser qwen3", "note": "仅当前两者均准入且节点空闲"},
}
C1_REF = ROOT / "DISCOVER_BOUNDARY_C1" / "data" / "discover_boundary_c1_overrun_runs.csv"   # C1 三档每 run 完成标志


# ---------------------------------------------------------------- 1. 哈希
def hashcheck(label: str) -> dict:
    mism = [f for f, h in FROZEN["sha256"].items() if sha(ROOT / f) != h]
    rec = {"label": label, "utc": datetime.now(timezone.utc).isoformat(), "frozen_files": len(FROZEN["sha256"]), "mismatches": mism,
           "result": "PASS" if not mism else "FAIL", "formal_e_sha256": sha(ROOT / "discover/formal_e.py"), "runner_sha256": sha(Path(__file__)),
           "host": platform.node(), "OPENAI_BASE_URL": os.environ.get("OPENAI_BASE_URL")}
    (OUT / "metadata").mkdir(parents=True, exist_ok=True)
    (OUT / "metadata" / f"hashcheck_{label}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json").write_text(json.dumps(rec, indent=2), encoding="utf-8")
    print(json.dumps(rec, ensure_ascii=False)); return rec


# ---------------------------------------------------------------- 2. 服务与探针
def serve_cmd(model: str) -> str:
    c = CANDIDATES[model]
    cmd = (f"vllm serve {c['hf']} --served-model-name {model} --tensor-parallel-size {c['tp']} --max-model-len 65536 "
           f"--enable-auto-tool-choice --tool-call-parser {c['parser']} {c['extra']} --port 8000 --dtype auto").replace("  ", " ")
    print(cmd); print("# 客户端:  export OPENAI_BASE_URL=http://<host>:8000/v1 ; export OPENAI_API_KEY=local-placeholder"); return cmd


def probe(model: str) -> dict:
    """端点能否做工具调用、上下文是否 ≥ 65536。不计入任何统计。"""
    from openai import OpenAI
    cli = OpenAI(api_key=os.environ.get("OPENAI_API_KEY") or "local-placeholder", base_url=os.environ["OPENAI_BASE_URL"], timeout=120.0)
    ctx = None
    try:
        m = next(x for x in cli.models.list().data if x.id == model); ctx = getattr(m, "max_model_len", None)
    except Exception as e: print("models.list:", repr(e))
    tools = [{"type": "function", "function": {"name": "PING", "description": "reply with the number given", "parameters": {"type": "object", "properties": {"n": {"type": "integer"}}, "required": ["n"]}}}]
    r = cli.chat.completions.create(model=model, messages=[{"role": "user", "content": "Call PING with n=7."}], tools=tools, tool_choice="auto")
    calls = r.choices[0].message.tool_calls or []
    ok = bool(calls) and calls[0].function.name == "PING" and json.loads(calls[0].function.arguments or "{}").get("n") == 7
    rec = {"model": model, "response_model": r.model, "tool_call_ok": ok, "max_model_len": ctx, "utc": datetime.now(timezone.utc).isoformat()}
    (OUT / "metadata").mkdir(parents=True, exist_ok=True); (OUT / "metadata" / f"probe_{model}.json").write_text(json.dumps(rec, indent=2), encoding="utf-8")
    print(json.dumps(rec)); return rec


# ---------------------------------------------------------------- 3. 准入
def interface_errors(t: dict) -> dict:
    """畸形/未声明参数/未知动作/空轮的计数（0 CU 错误，按冻结驱动记录的错误串判定）。"""
    n_invalid = n_unknown = 0
    for s in t["steps"]:
        r = s.get("result")
        if isinstance(r, dict) and isinstance(r.get("error"), str):
            if r["error"].startswith("InvalidArguments"): n_invalid += 1
            if r["error"].startswith("ValueError: unknown action"): n_unknown += 1
    return {"invalid_arguments": n_invalid, "unknown_action": n_unknown, "no_tool_call_turns": t["llm_meta"]["malformed_turns"],
            "unparseable_json": t["llm_meta"]["infra_retries"], "why_stop": t["final"]["why_stop"][:60]}


def admit(model: str) -> bool:
    out_root = OUT / model / "admission"; log = []
    for r in range(3):
        rd = formal_e.run_one("anonymous", 225.0, 900 + r, model, out_root, {}, "admit")
        t = json.loads((rd / "trace.json").read_text(encoding="utf-8")); e = interface_errors(t); e["run_dir"] = rd.name; log.append(e); print(e)
    ok = all(e["invalid_arguments"] == 0 and e["unknown_action"] == 0 and e["no_tool_call_turns"] == 0 and not e["why_stop"].startswith("malformed") for e in log)
    rec = {"model": model, "admitted": ok, "runs": log, "criteria": "3×225 CU：InvalidArguments=0, unknown action=0, 空轮=0, 不以 malformed_action_limit 结束", "utc": datetime.now(timezone.utc).isoformat()}
    p = OUT / "ADMISSION.jsonl"; OUT.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f: f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print("ADMITTED" if ok else "REJECTED", model); return ok


# ---------------------------------------------------------------- 4. 格序
def cell_full(model: str, budget: float, sub: str = "runs") -> tuple[int, int]:
    ps = glob.glob(str(OUT / model / sub / "traces" / "anonymous" / f"*_B{int(budget)}_r*" / "trace.json"))
    sc = [S.score_trace(Path(p).resolve()) for p in ps]
    return sum(int(x["full_decision_correct"]) for x in sc), len(sc)


def run_cell(model: str, budget: float, runs: int, tag: str, sub: str = "runs", start: int = 0):
    (OUT / "logs").mkdir(parents=True, exist_ok=True)
    with (OUT / "logs" / f"{model}_B{int(budget)}_{tag}.log").open("a", encoding="utf-8") as lf:
        for r in range(start, start + runs):
            t0 = time.time()
            try:
                rd = formal_e.run_one("anonymous", float(budget), r, model, OUT / model / sub, {}, tag)
                t = json.loads((rd / "trace.json").read_text(encoding="utf-8"))
                line = f"{model} B={budget:.0f} r={r} -> winner {t['final']['answer']['industrial_winner']} spent {t['final']['spent_CU']:.0f} steps {len(t['steps'])} tokens {t['llm_meta']['tokens']} {time.time()-t0:.0f}s | {t['final']['why_stop'][:70]}"
            except Exception as e:
                line = f"{model} B={budget:.0f} r={r} -> DRIVER EXCEPTION {e!r}\n{traceback.format_exc()}"
            print(line, flush=True); lf.write(line + "\n"); lf.flush()


def cells(model: str, runs: int = 20):
    """预注册顺序：225 → 175 → 75 →（225 格 ≥19/20 才跑）5000 →（75 格 ≥19/20 才跑）S-gate 75 与 5000。"""
    admitted = any(json.loads(l)["model"] == model and json.loads(l)["admitted"] for l in (OUT / "ADMISSION.jsonl").read_text(encoding="utf-8").splitlines()) if (OUT / "ADMISSION.jsonl").exists() else False
    if not admitted: raise SystemExit(f"{model} 未通过准入测试；先运行 admit")
    for b in (225.0, 175.0, 75.0):
        k, n = cell_full(model, b)
        if n >= runs: print(f"skip B={b:.0f}: 已有 {n} run"); continue
        run_cell(model, b, runs - n, "ow", start=n)
    k225, _ = cell_full(model, 225.0); k75, _ = cell_full(model, 75.0)
    print(f"225 CU 完成 {k225}/20，75 CU 完成 {k75}/20")
    if k225 >= 19:
        k, n = cell_full(model, 5000.0)
        if n < runs: run_cell(model, 5000.0, runs - n, "owuncapped", start=n)
    else: print("5000 CU 格按预注册跳过（225 格 < 19/20）")
    if k75 >= 19:
        for b in (75.0, 5000.0):
            have = len(glob.glob(str(OUT / model / "gate" / "gate" / "traces" / "anonymous" / f"*_B{int(b)}_r*" / "trace.json")))
            for r in range(have, runs):
                rd = v2_stop_runner.run_one("gate", b, r, model, OUT / model / "gate", {}, "owgate"); print("gate", b, r, rd.name)
    else: print("S-gate 臂按预注册跳过（75 格 < 19/20）")


# ---------------------------------------------------------------- 5. 汇总
def wilson(k: int, n: int, z: float = 1.959964) -> tuple[float, float]:
    if n == 0: return (float("nan"), float("nan"))
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def fisher(a: int, b: int, c: int, d: int) -> float:
    """双侧 Fisher 精确检验，表 [[a,b],[c,d]]。"""
    from math import comb
    n = a + b + c + d; r1, c1 = a + b, a + c
    p_obs = comb(r1, a) * comb(n - r1, c1 - a) / comb(n, c1); p = 0.0
    for x in range(max(0, c1 - (n - r1)), min(r1, c1) + 1):
        px = comb(r1, x) * comb(n - r1, c1 - x) / comb(n, c1)
        if px <= p_obs * (1 + 1e-9): p += px
    return min(1.0, p)


def narrow_window_used(t: dict) -> int:
    built = set()
    for s in t["steps"]:
        r = s.get("result")
        if s["chosen_action"] == "BUILD_PROCESS_WINDOW" and isinstance(r, dict) and "error" not in r and r.get("n_states", FULL_DOMAIN) < FULL_DOMAIN: built.add(r.get("window"))
        if built and isinstance(r, dict) and "error" not in r and (s.get("chosen_args") or {}).get("window") in built and s["chosen_action"] != "BUILD_PROCESS_WINDOW": return 1
    return 0


def analyse(model: str):
    ref = {}
    if C1_REF.exists():
        for r in csv.DictReader(C1_REF.open(encoding="utf-8")):
            if r["arm"] == "E": ref.setdefault((r["tier"], float(r["budget_CU"])), []).append(int(r["full_decision_correct"]))
    rows = []
    for p in sorted(glob.glob(str(OUT / model / "runs" / "traces" / "anonymous" / "*" / "trace.json"))):
        p = Path(p); t = json.loads(p.read_text(encoding="utf-8"))
        if t["final"]["why_stop"].startswith("infrastructure_failure"): continue
        sc = S.score_trace(p.resolve()); stp = stopping_analyse(p, "OW") or {}; ie = interface_errors(t)
        rows.append({"model": model, "budget_CU": float(t["budget_CU"]), "run_index": t["run_index"], "full": int(sc["full_decision_correct"]), "win": int(sc["winner_correct"]),
                     "pair": int(sc["pair_decision_correct"]), "reach": int(sc["reachability_correct"]), "spent_CU": float(sc["spent_CU"]), "narrow_window": narrow_window_used(t),
                     "S123_reached": stp.get("S123_reached"), "S123_CU": stp.get("S123_CU"), "post_S123_CU": stp.get("post_S123_CU"), "decision_stable_CU": stp.get("decision_stable_CU"),
                     "interface_errors": ie["invalid_arguments"] + ie["unknown_action"], "no_tool_call_turns": ie["no_tool_call_turns"], "why_stop": t["final"]["why_stop"][:60]})
    if not rows: raise SystemExit("无 trace")
    (OUT / "data").mkdir(parents=True, exist_ok=True)
    with (OUT / "data" / f"{model}_runs.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    L = [f"# {model} — DISCOVER V1 冻结协议，匿名任务（{datetime.now(timezone.utc):%Y-%m-%d}）", "",
         "| CU | n | P(full) [Wilson 95%] | win/pair/reach | 窄窗口 | 规则触发 | 触发后花费中位 | 接口错误 run | vs strong p | vs mini p | vs nano p |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    cells_out = []
    for b in sorted({r["budget_CU"] for r in rows}):
        rs = [r for r in rows if r["budget_CU"] == b]; k, n = sum(r["full"] for r in rs), len(rs); lo, hi = wilson(k, n)
        pv = {}
        for tier in ("strong", "mini", "nano"):
            c1 = ref.get((tier, b)); pv[tier] = fisher(k, n - k, sum(c1), len(c1) - sum(c1)) if c1 else float("nan")
        reached = [r for r in rs if r["S123_reached"]]
        cell = {"budget_CU": b, "n": n, "full": k, "ci_lo": round(lo, 3), "ci_hi": round(hi, 3), "win": sum(r["win"] for r in rs), "pair": sum(r["pair"] for r in rs), "reach": sum(r["reach"] for r in rs),
                "narrow": sum(r["narrow_window"] for r in rs), "S123_reached": len(reached), "median_post_S123": st.median([r["post_S123_CU"] for r in reached]) if reached else None,
                "runs_with_interface_error": sum(1 for r in rs if r["interface_errors"] > 0), **{f"p_vs_{t}": pv[t] for t in pv}}
        cells_out.append(cell)
        L.append(f"| {b:.0f} | {n} | {k}/{n} = {k/n:.2f} [{lo:.2f}, {hi:.2f}] | {cell['win']}/{cell['pair']}/{cell['reach']} | {cell['narrow']} | {cell['S123_reached']} | {cell['median_post_S123']} | {cell['runs_with_interface_error']} | {pv['strong']:.3g} | {pv['mini']:.3g} | {pv['nano']:.3g} |")
    with (OUT / "data" / f"{model}_cells.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(cells_out[0].keys())); w.writeheader(); w.writerows(cells_out)
    k225 = next((c for c in cells_out if c["budget_CU"] == 225.0), None); k75 = next((c for c in cells_out if c["budget_CU"] == 75.0), None)
    verdict = "未判定（格未跑齐）"
    if k225 and k75:
        verdict = "H-transfer：强档位机制在开源模型上复现" if (k225["full"] >= 19 and k75["full"] >= 19 and k75["narrow"] >= 15) else ("H-tier：开源模型落在闭源弱档位之间或以下" if k225["full"] < 19 or k75["full"] < 19 else "介于两者之间：按实测报告")
    L += ["", f"**预注册判据结果：{verdict}**", "", "H-transfer = 225 CU ≥19/20 且 75 CU ≥19/20 且 75 CU 窄窗口 ≥15/20；H-tier = 225 CU <19/20，或 225 ≥19/20 但 75 CU <15/20 窄窗口且 <19/20 完成。"]
    (OUT / "data" / f"{model}_summary.md").write_text("\n".join(L) + "\n", encoding="utf-8"); print("\n".join(L))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(); ap.add_argument("cmd", choices=["serve-cmd", "hashcheck", "probe", "admit", "cells", "analyse"])
    ap.add_argument("--model", default="Qwen3-32B"); ap.add_argument("--label", default="check"); ap.add_argument("--runs", type=int, default=20)
    a = ap.parse_args()
    if a.cmd == "serve-cmd": serve_cmd(a.model)
    elif a.cmd == "hashcheck": hashcheck(a.label)
    elif a.cmd == "probe": probe(a.model)
    elif a.cmd == "admit": admit(a.model)
    elif a.cmd == "cells": cells(a.model, a.runs)
    else: analyse(a.model)
