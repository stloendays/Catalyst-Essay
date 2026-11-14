"""Raw-data ledger of every AI modelling run (advisor 2026-11-13: for each run record the reaction, the materials, the
tokens and the cost; part of the experiment's raw data). Deterministic, read-only on the run folders; rerun at any time.

    cfpy run_ledger.py            -> evaluation/run_ledger/RUN_LEDGER.csv, RUN_STAGES.csv, RUN_LEDGER.md  (runs from SINCE on)
    cfpy run_ledger.py --local    -> D:/论文-AI4S/work/run_ledger_local/ (all runs; local only, not in the repository)

Sources per run folder: ledger.json (model, routes, tokens, wall time, status, USD at the gpt-5.5 list price as written by
runner.py), stage_ledger.csv (per stage), build_version.json, records.csv (papers, records, catalysts, elements),
analysis.json (reference plant, cheapest catalyst), model_check.json. Run folders: D:/agent_runs/* (build mode) and
auto_agent/runs/* (database / lean / full modes).
Role follows the train/test split (docs/TRAIN_TEST_SPLIT.md): PDH, CO2 methanation and the early trials are development
runs (their results shaped the rules); NH3 decomposition and the NH3 / methanol blind builds are test runs.
"""
import csv
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOTS = [Path("D:/agent_runs"), HERE / "runs"]
OUT = HERE / "evaluation" / "run_ledger"
LOCAL_OUT = Path("D:/论文-AI4S/work/run_ledger_local")
SINCE = "2026-11-14T11:00"   # repository ledger starts with the A9 harness (first run ch4_v31_t1); earlier runs stay local

RXN_KEYS = [("propane dehydrogenation", "pdh"), ("methanation", "ch4"), ("ammonia decomposition", "nh3dec"),
            ("ammonia synthesis", "nh3"), ("methanol", "meoh"), ("ethanol", "etoh")]
RXN_NAME = {"pdh": "丙烷脱氢", "ch4": "CO2 甲烷化", "nh3dec": "氨分解", "nh3": "NH3 合成（盲测）", "meoh": "CO2 制甲醇（盲测）",
            "etoh": "乙醇脱水（试跑）"}
# Runs that are not valid results, with the reason (operator records, 2026-11-10..13).
INVALID = {
    "nh3dec_b1": "stopped by the operator at turn 137/140, hung in a fixed tool (before A3)",
    "nh3dec_b2": "turn limit 140 in atomic_model",
    "nh3dec_b3": "turn limit 140 in report",
    "nh3dec_b4": "stopped by the operator at turn 288/300 after about 3 h inside one fixed tool (A2 code, no tool deadline)",
    "nh3dec_b5": "holdout leak: opened the held-out TEA paper by web search (turn 62); held-out abstracts in search results (A6)",
    "nh3dec_b6": "harness crash at finish: KeyError on an evidence_debt.json the agent wrote itself (fixed in A5)",
    "nh3dec_b8": "turn limit 300 (replaced by nh3dec_b10)",
    "nh3_b1_stopped_140turns": "stopped during extraction before A2 (started with 140 turns); not evaluated",
    "nh3_b2_stopped_140turns": "stopped during extraction before A2 (started with 140 turns); not evaluated",
    "nh3_b3_stopped_140turns": "stopped during extraction before A2 (started with 140 turns); not evaluated",
    "smoke_v3_nh3dec": "harness smoke test (4 turns), no model",
}


def rxn_key(text):
    t = (text or "").lower()
    return next((k for s, k in RXN_KEYS if s in t), "other")


def jload(p):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def version(run):
    v = jload(run / "build_version.json")
    if v:
        return v.get("version")
    if run.parent.name == "runs":
        return "db/lean/full mode"
    return "V2-flowsheet" if (run / "flowsheet.json").exists() else "V1"


def role(name, key):
    if name.startswith("smoke"):
        return "smoke"
    return "test" if key in ("nh3dec", "nh3", "meoh") else "development"


def materials(run):
    p = run / "records.csv"
    if not p.exists():
        return {}
    rows = list(csv.DictReader(p.open(encoding="utf-8", errors="replace")))
    el = Counter()
    for r in rows:
        try:
            for e, _w in json.loads(r.get("elements") or "[]"):
                el[e] += 1
        except Exception:
            pass
    usable = [r for r in rows if str(r.get("usable", "True")).lower() == "true"]
    return {"n_papers": len({r.get("paper") for r in rows}), "n_records": len(rows), "n_usable_records": len(usable),
            "n_catalysts": len({r.get("catalyst") for r in rows}),
            "elements_top": " ".join(f"{e}:{n}" for e, n in el.most_common(10))}


def one(run):
    led = jload(run / "ledger.json")
    if not led or not (run / "trace.jsonl").exists():  # *_oracle folders are re-evaluated copies without LLM calls
        return None, []
    tok = led.get("tokens", {})
    key = rxn_key(led.get("reaction"))
    an = jload(run / "analysis.json") or {}
    mc = jload(run / "model_check.json") or {}
    status = led.get("status")
    if run.name in INVALID:
        valid = "invalid: " + INVALID[run.name]
    elif status == "running":
        valid = "running"
    elif status == "finished" and (mc.get("passed") or run.parent.name == "runs"):
        valid = "valid"
    else:
        valid = f"invalid: status {status}, model_check passed={mc.get('passed')}"
    ref = an.get("reference") or {}
    ch = an.get("cheapest") or {}
    crit = tok.get("critic_in", 0) + tok.get("critic_out", 0)
    row = {"run": run.name, "folder": str(run).replace("\\", "/"), "reaction_key": key, "reaction_cn": RXN_NAME.get(key, key),
           "reaction": led.get("reaction"), "role": role(run.name, key), "build_mode": version(run), "validity": valid,
           "status": status, "start": led.get("start"), "last_update": led.get("now"), "wall_minutes": led.get("wall_minutes"),
           "model": led.get("model"), "route": led.get("route"), "extract_model": led.get("extract_model"),
           "extract_route": led.get("extract_route"), "critic_model": "gpt-5.6-luna" if crit else "",
           "agent_calls": tok.get("agent_calls"), "extract_calls": tok.get("extract_calls"),
           "agent_in": tok.get("agent_in", 0), "agent_out": tok.get("agent_out", 0), "extract_in": tok.get("extract_in", 0),
           "extract_out": tok.get("extract_out", 0), "critic_in": tok.get("critic_in", 0), "critic_out": tok.get("critic_out", 0),
           "tokens_total": led.get("tokens_total"), "usd_at_gpt55_list": led.get("usd_equivalent_at_gpt55_list_price"),
           **materials(run), "reference_plant": ref.get("name", ""), "reference_cost_usd_per_t": ref.get("cost", ""),
           "cheapest_catalyst": ch.get("catalyst", ""), "cheapest_cost_usd_per_t": ch.get("cost", "")}
    stages = []
    sp = run / "stage_ledger.csv"
    if sp.exists():
        for s in csv.DictReader(sp.open(encoding="utf-8")):
            stages.append({"run": run.name, "reaction_key": key, **s})
    return row, stages


def fmt(x, nd=0):
    try:
        return f"{float(x):,.{nd}f}"
    except (TypeError, ValueError):
        return "" if x is None else str(x)


def main(local=False):
    out_dir = LOCAL_OUT if local else OUT
    rows, stages = [], []
    for root in ROOTS:
        for run in sorted(p for p in root.iterdir() if p.is_dir()):
            r, s = one(run)
            if r and (local or (r["start"] or "") >= SINCE):
                rows.append(r)
                stages += s
    rows.sort(key=lambda r: (r["role"], r["reaction_key"], r["start"] or ""))
    out_dir.mkdir(parents=True, exist_ok=True)
    cols = list(dict.fromkeys(k for r in rows for k in r))
    with (out_dir / "RUN_LEDGER.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, cols)
        w.writeheader()
        w.writerows(rows)
    scols = list(dict.fromkeys(k for s in stages for k in s))
    with (out_dir / "RUN_STAGES.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, scols)
        w.writeheader()
        w.writerows(stages)

    L = ["# AI 建模运行账本（原始数据）", "",
         "由 `run_ledger.py` 从各运行目录的 `ledger.json`、`stage_ledger.csv`、`records.csv` 自动生成；逐行明细见 "
         "`RUN_LEDGER.csv`，分阶段明细见 `RUN_STAGES.csv`。费用按 gpt-5.5 公开标价折算（输入 token 含重复发送的历史上下文）。", "",
         "## 按反应和用途汇总", "",
         "| 用途 | 反应 | 运行次数 | 有效 | 无效 | 运行中 | 总 token（百万） | 折算费用（USD） | 总时长（小时） |",
         "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    groups = {}
    for r in rows:
        groups.setdefault((r["role"], r["reaction_cn"]), []).append(r)
    tot = [0, 0.0, 0.0]
    for (ro, rx), g in groups.items():
        t = sum(r["tokens_total"] or 0 for r in g)
        u = sum(r["usd_at_gpt55_list"] or 0 for r in g)
        h = sum(r["wall_minutes"] or 0 for r in g) / 60
        tot[0] += t
        tot[1] += u
        tot[2] += h
        n = Counter("valid" if r["validity"] == "valid" else "running" if r["validity"] == "running" else "invalid" for r in g)
        L.append(f"| {ro} | {rx} | {len(g)} | {n['valid']} | {n['invalid']} | {n['running']} | {t / 1e6:.1f} | {u:,.0f} | {h:.1f} |")
    L.append(f"| 合计 | | {len(rows)} | | | | {tot[0] / 1e6:.1f} | {tot[1]:,.0f} | {tot[2]:.1f} |")
    L += ["", "## 逐次运行", "",
          "| 运行 | 反应 | 用途 | 建模版本 | 结论 | 模型 / 路由 | 轮数 | 输入 token | 输出 token | 审查 token | 折算 USD | 时长 min | 论文 / 记录 / 催化剂 | 主要元素（记录数） |",
          "|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---|---|"]
    for r in rows:
        tin = r["agent_in"] + r["extract_in"]
        tout = r["agent_out"] + r["extract_out"]
        crit = r["critic_in"] + r["critic_out"]
        mat = f"{r.get('n_papers', '')} / {r.get('n_records', '')} / {r.get('n_catalysts', '')}" if "n_records" in r else ""
        L.append(f"| {r['run']} | {r['reaction_cn']} | {r['role']} | {r['build_mode']} | {r['validity']} | {r['model']} / "
                 f"{r['route']} | {r['agent_calls']} | {fmt(tin)} | {fmt(tout)} | {fmt(crit)} | {fmt(r['usd_at_gpt55_list'], 1)} | "
                 f"{fmt(r['wall_minutes'], 1)} | {mat} | {r.get('elements_top', '')} |")
    (out_dir / "RUN_LEDGER.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"{len(rows)} runs, {len(stages)} stage rows -> {out_dir}")
    print(f"total tokens {tot[0] / 1e6:.1f} M, USD at gpt-5.5 list {tot[1]:,.0f}, wall {tot[2]:.1f} h")


if __name__ == "__main__":
    import sys
    main(local="--local" in sys.argv)
