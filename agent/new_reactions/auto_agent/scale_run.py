"""Scaling experiment: papers -> time and cost, and the paper count after which the conclusions stop changing.

  python scale_run.py process <rxn>     # every PDF in ../pdf/<rxn>/: Docling, extraction (gpt-5.5, standard schema), timed per paper
  python scale_run.py curves <rxn>      # subsets of k papers (k = 5, 10, 20, 30, all; 20 random orders each): conclusions and cost
Workspace scale/<rxn>/. Per-paper time and tokens in scale/<rxn>/per_paper.csv; curves in scale/<rxn>/curves.csv.
"""
import csv
import json
import os
import random
import shutil
import statistics as st
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
NR = HERE.parent
sys.path.insert(0, str(NR))
sys.path.insert(0, str(NR.parent / "extraction"))
import chain  # noqa: E402
import llm_route  # noqa: E402
import plant_framework as fw  # noqa: E402

DOCLING_PY = r"D:\Tools\docling-env\Scripts\python.exe"
OCR_LOCK = HERE / "ocr.lock"
SCOPE = {"pdh": "Non-oxidative propane dehydrogenation only (no O2/CO2/N2O co-feed, no chemical looping, no butane/ethane-only runs).",
         "ch4": "Thermocatalytic CO2 methanation only (no photo/electro/plasma, no CO-only methanation, no dry reforming).",
         "nh3dec": "Thermocatalytic ammonia decomposition to hydrogen only (no electrochemical, plasma or membrane-only data).",
         "rwgs": "Thermocatalytic reverse water-gas shift only (no electro/photo/plasma, no chemical looping cycles).",
         "etoh": "Gas-phase ethanol dehydration to ethylene only (no diethyl ether-only, no ethanol-to-hydrocarbons/propylene/butadiene)."}


def process(rx):
    ws = HERE / "scale" / rx
    for d in ("pdf", "ocr", "extracted"):
        (ws / d).mkdir(parents=True, exist_ok=True)
    for p in (NR / "pdf" / rx).glob("*.pdf"):
        dst = ws / "pdf" / (p.stem[:60] + ".pdf")
        if not dst.exists():
            shutil.copy(p, dst)
    t0 = time.time()
    while OCR_LOCK.exists() and time.time() - OCR_LOCK.stat().st_mtime < 3600:
        time.sleep(10)
    OCR_LOCK.write_text(str(os.getpid()))
    try:
        r = subprocess.run([DOCLING_PY, str(NR / "ocr_docling.py"), "_scale_", "4.0"], cwd=str(ws), capture_output=True, text=True,
                           env=dict(os.environ, DOCLING_SRC=str(ws / "pdf"), DOCLING_DST=str(ws / "ocr")), encoding="utf-8", errors="replace")
    finally:
        OCR_LOCK.unlink(missing_ok=True)
    t_ocr = time.time() - t0
    import ast
    ocr = {}
    for line in r.stdout.splitlines():
        if line.startswith("{"):
            d = ast.literal_eval(line)
            ocr[Path(d["pdf"]).stem[:60]] = d
    cfg = fw.load(rx, "ours")
    router = llm_route.Router("gpt-5.5")

    def probe(client):        # API-YES lists gpt-5.5 but refuses it: move to the route that serves it before the parallel calls
        for _ in client.responses.create(model="gpt-5.5", input="Reply with OK.", store=False, stream=True, max_output_tokens=16):
            pass
        return client._route
    print("extraction route", router.call(probe), flush=True)
    t1 = time.time()
    rows = chain.extract(ws, lambda: router.client, "gpt-5.5", cfg["name"], cfg["stoich"]["key"], cfg["stoich"]["product"],
                         next(iter(cfg["lab_feed"]["default_ratio"]), None), SCOPE[rx], workers=6,
                         usage_csv=ws / "token_usage_extract.csv")
    t_ext = time.time() - t1
    log = ws / "stage_times.json"
    hist = json.loads(log.read_text()) if log.exists() else []
    hist.append(dict(ocr_wall_s=round(t_ocr, 1), ocr_papers_now=len(ocr), extract_wall_s=round(t_ext, 1), extract_papers_now=len(rows),
                     errors=[x for x in rows if "error" in x]))
    log.write_text(json.dumps(hist, indent=1), encoding="utf-8")
    # per-paper table: OCR seconds (Docling log), extraction seconds and tokens
    old = {}
    if (ws / "ocr_times.json").exists():
        old = json.loads((ws / "ocr_times.json").read_text())
    old.update({k: v for k, v in ocr.items()})
    olog = ws / "ocr" / "ocr_log.json"            # written by ocr_docling.py itself, survives restarts
    if olog.exists():
        for d in json.loads(olog.read_text(encoding="utf-8")):
            old.setdefault(Path(d["pdf"]).stem[:60], d)
    (ws / "ocr_times.json").write_text(json.dumps(old, indent=1), encoding="utf-8")
    ex = {r["paper"]: r for r in csv.DictReader(open(ws / "token_usage_extract.csv", encoding="utf-8"))}
    with open(ws / "per_paper.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["paper", "pages", "ocr_s", "extract_s", "prompt_tokens", "completion_tokens", "usd_gpt55", "n_records"])
        for p in sorted(ex):
            o = old.get(p, {})
            e = ex[p]
            usd = int(e["prompt_tokens"]) * 5e-6 + int(e["completion_tokens"]) * 30e-6
            w.writerow([p, o.get("pages"), o.get("seconds"), e["seconds"], e["prompt_tokens"], e["completion_tokens"], round(usd, 4), e["n_records"]])
    print(rx, "ocr", round(t_ocr), "s,", len(ocr), "papers; extraction", round(t_ext), "s,", len(rows), "papers")


def curves(rx, ks=(5, 10, 20, 30), reps=20):
    ws = HERE / "scale" / rx
    cfg = fw.load(rx, "ours")
    rows, _ = chain.normalise(ws, cfg)
    per = {r["paper"]: r for r in csv.DictReader(open(ws / "per_paper.csv", encoding="utf-8"))}
    papers = sorted({r["paper"] for r in rows if r["usable"]})
    allp = sorted(per)
    out = []
    full = chain.analyse(ws, cfg, rows, tag="full")
    for k in list(ks) + [len(allp)]:
        if k > len(allp):
            continue
        for rep in range(reps if k < len(allp) else 1):
            sub = set(random.Random(1000 * k + rep).sample(allp, k))
            rs = [r for r in rows if r["paper"] in sub]
            if not any(r["usable"] for r in rs):
                continue
            s = chain.analyse(ws, cfg, rs, tag="sub")
            pl = s["ranking"]["productivity"]["catalyst_level"]
            cost = sum(float(per[p]["usd_gpt55"]) for p in sub)
            secs = sum(float(per[p]["extract_s"] or 0) + float(per[p]["ocr_s"] or 0) for p in sub)
            out.append(dict(k=k, rep=rep, usable_papers=s["n_papers"], usable_records=s["n_usable"], largest=s["reference"]["largest"],
                            cheapest=s["cheapest"]["catalyst"], cheapest_is_full=s["cheapest"]["catalyst"] == full["cheapest"]["catalyst"],
                            changed=pl.get("changed"), groups=pl.get("groups"), fraction=pl.get("fraction"),
                            top_attribution=max(s["attribution_share"], key=s["attribution_share"].get),
                            usd_extraction=round(cost, 2), serial_seconds=round(secs)))
    for p in ("costs_sub.csv", "summary_sub.json"):
        (ws / p).unlink(missing_ok=True)
    with open(ws / "curves.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, list(out[0]))
        w.writeheader()
        w.writerows(out)
    for k in sorted({o["k"] for o in out}):
        o = [x for x in out if x["k"] == k]
        print(rx, "k", k, "runs", len(o), "cheapest = full", sum(x["cheapest_is_full"] for x in o), "top attribution",
              {a: sum(x["top_attribution"] == a for x in o) for a in {x["top_attribution"] for x in o}},
              "median fraction", st.median([x["fraction"] for x in o if x["fraction"] is not None] or [0]),
              "median USD", st.median(x["usd_extraction"] for x in o))


if __name__ == "__main__":
    if sys.argv[1] in ("process", "curves"):
        {"process": process, "curves": curves}[sys.argv[1]](sys.argv[2])


def table(rx):
    """Rebuild per_paper.csv from ocr/ocr_log.json (Docling) and token_usage_extract.csv (extraction)."""
    ws = HERE / "scale" / rx
    ocr = {Path(d["pdf"]).stem[:60]: d for d in json.loads((ws / "ocr" / "ocr_log.json").read_text(encoding="utf-8"))}
    ex = {r["paper"]: r for r in csv.DictReader(open(ws / "token_usage_extract.csv", encoding="utf-8"))}
    with open(ws / "per_paper.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["paper", "pages", "ocr_s", "extract_s", "prompt_tokens", "completion_tokens", "usd_gpt55", "n_records"])
        for p in sorted(ex):
            o, e = ocr.get(p, {}), ex[p]
            w.writerow([p, o.get("pages"), o.get("seconds"), e["seconds"], e["prompt_tokens"], e["completion_tokens"],
                        round(int(e["prompt_tokens"]) * 5e-6 + int(e["completion_tokens"]) * 30e-6, 4), e["n_records"]])
    print(rx, len(ex), "papers in per_paper.csv;", sum(1 for p in ex if p in ocr), "with OCR time")


if __name__ == "__main__" and sys.argv[1] == "table":
    table(sys.argv[2])
