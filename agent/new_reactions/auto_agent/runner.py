"""Autonomous agent that runs the whole analysis chain for one reaction, through the local API-YES gateway.

The agent gets the reaction name, the method (the chain used for NH3 and methanol in this repository, described in
words) and tools. It chooses the papers, downloads them, runs Docling, designs its own extraction schema, writes its
own normalisation, plant model and analysis code, sources plant parameters on the web, and writes the report.
Nothing from the hand-orchestrated run in ../ (code, parameters, results) is visible to it.

Usage: python runner.py <run_name> "<reaction description>" [--model gpt-5.6-sol] [--max-turns 90]
Workspace: runs/<run_name>/ ; trace: runs/<run_name>/trace.jsonl ; ledger: runs/<run_name>/ledger.json
"""
from __future__ import annotations

import argparse
import base64
import csv
import json
import os
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[0] / ".." / "extraction"))
sys.path.insert(0, str(HERE.parents[1] / "extraction"))
import llm_route  # noqa: E402

PY = r"C:\Users\ASUS\.local\bin\cfpy"
DOCLING_PY = r"D:\Tools\docling-env\Scripts\python.exe"
NUS_FETCH = r"D:\Tools\nus-fetch\nus-fetch.cmd"
OCR_SCRIPT = HERE.parent / "ocr_docling.py"
OCR_LOCK = HERE / "ocr.lock"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36",
      "Accept": "application/pdf,*/*"}
MAX_OUT = 7000

METHOD = """You are a research agent. Run, end to end and on your own, the analysis chain below for the reaction given by the user. Work only through the tools. Decide everything yourself; nobody will answer questions.

Goal: show, from the open literature, where the industrial bottleneck of this reaction lies and whether the way papers rank catalysts agrees with what a plant would choose. Report the time and the cost of your own run at the end (the harness logs tokens and time; read them with read_file('ledger.json')).

The chain (the same thinking as the ammonia and methanol studies of this project):
1. Literature: search for experimental catalyst papers on the reaction (open access preferred), screen titles/abstracts, keep 8-12 papers that report catalyst performance (conversion, selectivity, rate/productivity, stability) under stated conditions. Exclude reviews and purely computational papers. Download them; papers that fail to download are simply dropped.
2. OCR: run ocr_papers (Docling: reading-order text with page markers, tables as Markdown, figure crops).
3. Extraction: design the record fields a plant model needs (catalyst and composition with wt% loadings, T, P, feed composition, space velocity or flow and catalyst mass, conversion, selectivity, formation rate with unit and basis, stability: initial/final conversion and duration). Call extract_records per paper. Printed numbers are copied as printed; plot readings are marked approximate.
4. Normalise to consistent units with your own Python (run_python). Derive productivity (kg product per kg catalyst per h) from the printed rate or from feed flow x conversion x selectivity, and flag derived values. Apply physical plausibility gates (impossible rates, conversions above equilibrium) and self-check: every value marked printed should be found as a number in the paper text (ocr/*.md).
5. Plant model: build a transparent plant cost model in USD per tonne of product for a world-scale plant: raw materials, energy, capital (annualised, scaled with throughput/recycle and reactor size), catalyst (inventory from productivity, metal prices, lifetime, precious-metal recovery), regeneration if relevant, by-product credits. Source every parameter with web_search (official statistics, open techno-economic papers, company filings) and record the source in a sources table; mark unsourced values as assumptions. Let the plant optimise its free operating variable(s) (for example the per-pass conversion up to near equilibrium, trading recycle against catalyst amount). Move activity from lab to plant in a physically consistent way: a lab test at low conversion is limited by contact time, a plant can load more catalyst, so use a kinetic law (for example first-order approach to equilibrium) rather than charging the plant the lab conversion. Selectivity keeps its lab value; flag records measured far below the plant conversion. Compute the industrial reference catalyst/plant from published plant data and check the model against any published plant or TEA cost.
6. Analysis:
   a. Plant cost of every usable record.
   b. Paper ranking vs plant ranking: in each comparison group (same paper, same pressure and feed) compare the leader by each lab metric (productivity, conversion, selectivity) with the cheapest plant option. Count disagreements, split them into "other catalyst" vs "same catalyst at another temperature", and give the regret (extra plant cost of the lab choice).
   c. Bottleneck: cost breakdown of the reference plant; one-at-a-time attribution of each record's cost gap to the reference (selectivity, activity, temperature, stability, metal cost); cost change at the reference for +1 point selectivity, x2 activity, x10 stability, and a small change in the main raw-material price. State which property (or which non-catalyst factor) carries the plant cost.
   d. Backward design: what a literature catalyst would need (selectivity, activity, or price) to reach the industrial reference cost.
   e. One-at-a-time sensitivity of the conclusions to the uncertain parameters.
7. Report: write report.md in the workspace with: papers used and dropped (with reason); extraction counts and self-check result; parameter table with sources; results of 6a-6e with numbers and denominators; the bottleneck conclusion; what the data could not support; time and cost of the run from ledger.json. Save the data and scripts you used. Then call finish.

Rules: never invent numbers or sources; if something cannot be found, say so and use a stated assumption with a range. Keep tool outputs small (print summaries, not whole tables). The workspace is your current directory; scripts you run start there. Budget: about {max_turns} tool turns; plan accordingly and finish with a complete report."""

TOOLS = [
    {"type": "web_search"},
    {"type": "function", "name": "search_papers", "strict": True,
     "description": "OpenAlex search for open-access journal articles. Returns doi, year, venue, citations, has_pdf and a short abstract.",
     "parameters": {"type": "object", "additionalProperties": False, "required": ["query", "title_terms", "n", "from_year"],
                    "properties": {"query": {"type": "string"}, "title_terms": {"type": "string", "description": "words that must appear in the title"},
                                   "n": {"type": "integer"}, "from_year": {"type": "integer"}}}},
    {"type": "function", "name": "download_papers", "strict": True,
     "description": "Download the PDFs of these DOIs into pdf/ (open-access locations first, then the NUS library proxy). Returns status per DOI.",
     "parameters": {"type": "object", "additionalProperties": False, "required": ["dois"],
                    "properties": {"dois": {"type": "array", "items": {"type": "string"}}}}},
    {"type": "function", "name": "ocr_papers", "strict": True,
     "description": "Run Docling (GPU) on every PDF in pdf/ not yet parsed: ocr/<stem>.md and figure crops ocr/<stem>_figs/ with captions in ocr/<stem>_figs.json.",
     "parameters": {"type": "object", "additionalProperties": False, "required": [], "properties": {}}},
    {"type": "function", "name": "extract_records", "strict": True,
     "description": "LLM extraction of catalyst-performance records from one paper (its Docling text + up to 12 figure crops chosen by caption keywords). You define the fields; number fields come back as {value, unit, qualifier '='|'~'|'<'|'>'|'missing'}. Output: extracted/<stem>.json.",
     "parameters": {"type": "object", "additionalProperties": False, "required": ["paper_stem", "instructions", "fields", "figure_keywords"],
                    "properties": {"paper_stem": {"type": "string"},
                                   "instructions": {"type": "string", "description": "scope and rules for this reaction"},
                                   "fields": {"type": "array", "items": {"type": "object", "additionalProperties": False,
                                              "required": ["name", "kind", "description"],
                                              "properties": {"name": {"type": "string"}, "kind": {"type": "string", "enum": ["number", "string", "integer"]},
                                                             "description": {"type": "string"}}}},
                                   "figure_keywords": {"type": "array", "items": {"type": "string"}}}}},
    {"type": "function", "name": "read_file", "strict": True,
     "description": "Read part of a text file in the workspace (lines start..start+n).",
     "parameters": {"type": "object", "additionalProperties": False, "required": ["path", "start", "n"],
                    "properties": {"path": {"type": "string"}, "start": {"type": "integer"}, "n": {"type": "integer"}}}},
    {"type": "function", "name": "write_file", "strict": True,
     "description": "Write a text file in the workspace.",
     "parameters": {"type": "object", "additionalProperties": False, "required": ["path", "content"],
                    "properties": {"path": {"type": "string"}, "content": {"type": "string"}}}},
    {"type": "function", "name": "run_python", "strict": True,
     "description": "Save the code as scripts/<name>.py in the workspace and run it there (Python 3.12 with numpy, scipy, pandas, matplotlib, pypdfium2). Returns stdout/stderr (truncated).",
     "parameters": {"type": "object", "additionalProperties": False, "required": ["name", "code", "timeout_s"],
                    "properties": {"name": {"type": "string"}, "code": {"type": "string"}, "timeout_s": {"type": "integer"}}}},
    {"type": "function", "name": "finish", "strict": True,
     "description": "End the run after report.md is written.",
     "parameters": {"type": "object", "additionalProperties": False, "required": ["summary"],
                    "properties": {"summary": {"type": "string"}}}},
]


from db_mode import DB_TOOLS, METHOD_DB, DBMixin  # noqa: E402
from full_mode import FULL_TOOLS, METHOD_FULL, FullMixin  # noqa: E402
import strategies as sg  # noqa: E402
from lean_mode import LEAN_TOOLS, METHOD_LEAN, LeanMixin  # noqa: E402
from build_mode import AGENT_ROOT, BUILD_TOOLS, METHOD_BUILD, STAGES, BuildMixin  # noqa: E402
NUS_LOCK = HERE / "nus.lock"


class Run(DBMixin, FullMixin, LeanMixin, BuildMixin):
    def __init__(self, name, reaction, model, max_turns, db_key=None, budget_frac=0.3, full=False, n_target=12,
                 n_max=20, extract_model="gpt-5.6-sol", lean=None, build=None):
        self.build = build
        self.ws = (AGENT_ROOT / name) if build else (HERE / "runs" / name)   # build runs live outside the repository
        for d in ("pdf", "ocr", "extracted", "scripts"):
            (self.ws / d).mkdir(parents=True, exist_ok=True)
        self.reaction, self.model, self.max_turns = reaction, model, max_turns
        self.t0 = time.time()
        self.start_iso = datetime.now().isoformat(timespec="seconds")
        self.tok = {"agent_in": 0, "agent_out": 0, "extract_in": 0, "extract_out": 0, "agent_calls": 0, "extract_calls": 0}
        self.tool_time = {}
        self.db_key = db_key
        if db_key:
            self.setup_db(HERE / "db" / "truth.json", db_key, budget_frac)
        self.full, self.n_target, self.n_max, self.lean = full or bool(lean), n_target, n_max, lean
        if self.full or build:
            if not build:
                self.setup_full()
            self.extract_model, self.extract_workers = extract_model, 4
            self.extract_router = llm_route.Router(extract_model)   # API-YES first, then the advisor key

            def probe(client):
                for _ in client.responses.create(model=extract_model, input=[{"role": "user", "content": "Reply with OK."}], store=False, stream=True,
                                                 max_output_tokens=16):
                    pass
                return client._route
            self.extract_route = self.extract_router.call(probe)    # moves on when a route refuses the model
        if build:
            hp = HERE / "holdout" / f"{build}.json"
            self.setup_build(build, json.loads(hp.read_text(encoding="utf-8")) if hp.exists() else {})
        self.router = llm_route.Router(model)        # API-YES first, then the advisor key (llm_route order)

    # ------------------------------------------------------------ bookkeeping
    def log(self, rec):
        rec["t"] = round(time.time() - self.t0, 1)
        with open(self.ws / "trace.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    def write_ledger(self, status="running"):
        led = dict(status=status, reaction=self.reaction, model=self.model, route=getattr(getattr(self, "router", None), "client", None) and self.router.client._route,
                   extract_model=getattr(self, "extract_model", None), extract_route=getattr(self, "extract_route", None),
                   start=self.start_iso, now=datetime.now().isoformat(timespec="seconds"),
                   wall_minutes=round((time.time() - self.t0) / 60, 1), tokens=self.tok,
                   tokens_total=sum(v for k, v in self.tok.items() if "calls" not in k),
                   tool_seconds={k: round(v, 1) for k, v in self.tool_time.items()},
                   reveal_budget=getattr(self, "budget", None), reveal_spent=getattr(self, "spent", None),
                   usd_equivalent_at_gpt55_list_price=round(((self.tok["agent_in"] + self.tok["extract_in"]) * 5
                                                             + (self.tok["agent_out"] + self.tok["extract_out"]) * 30) / 1e6, 2))
        (self.ws / "ledger.json").write_text(json.dumps(led, indent=1), encoding="utf-8")

    def path(self, p):
        q = (self.ws / p).resolve()
        if not str(q).startswith(str(self.ws.resolve())):
            raise ValueError("path outside the workspace")
        return q

    # ------------------------------------------------------------ LLM
    def respond(self, items, instructions, tools, effort="medium", schema=None):
        kw = dict(model=self.model, instructions=instructions, input=items, store=False, stream=True,
                  reasoning={"effort": effort})
        if tools:
            kw["tools"] = tools
            kw["include"] = ["reasoning.encrypted_content"]
        if schema:
            kw["text"] = {"format": {"type": "json_schema", "name": "records", "strict": True, "schema": schema}}
        for attempt in range(4):
            try:
                out, text, final = [], [], None
                client = self.router.client
                for ev in client.responses.create(**kw):
                    if ev.type == "response.output_item.done":
                        out.append(ev.item)
                    elif ev.type == "response.output_text.delta":
                        text.append(ev.delta)
                    elif ev.type in ("response.completed", "response.incomplete", "response.failed"):
                        final = ev.response
                if final is None:
                    raise RuntimeError("stream ended without a final response")
                return out, "".join(text), final
            except Exception as e:  # noqa: BLE001
                self.log({"error": f"{type(e).__name__}: {str(e)[:300]}", "attempt": attempt, "route": self.router.client._route})
                if llm_route.is_exhausted(e) and self.router.order:
                    self.router._next()
                    continue
                time.sleep(10 * (attempt + 1))
        raise RuntimeError("LLM call failed 4 times")

    # ------------------------------------------------------------ tools
    def t_search_papers(self, query, title_terms, n, from_year):
        url = ("https://api.openalex.org/works?search=" + urllib.parse.quote(query) + "&filter=title.search:"
               + urllib.parse.quote(title_terms) + f",is_oa:true,type:article,publication_year:{from_year}-2026,has_doi:true"
               + f"&sort=cited_by_count:desc&per-page={min(n, 50)}")
        key = os.environ.get("OPENALEX_API_KEY")
        if key:
            url += "&api_key=" + urllib.parse.quote(key)
        data = None
        for wait in (0, 20, 60, 120):
            time.sleep(wait)
            try:
                data = json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "catalyst-essay-agent"}), timeout=60))
                break
            except urllib.error.HTTPError as e:
                if e.code != 429:
                    raise
        if data is None:
            return self._search_crossref(query, title_terms, n, from_year)
        out = []
        for w in data["results"]:
            ab = w.get("abstract_inverted_index") or {}
            abstract = " ".join(x for _, x in sorted((p, k) for k, ps in ab.items() for p in ps))[:350]
            loc = w.get("best_oa_location") or {}
            out.append(dict(doi=(w.get("doi") or "").replace("https://doi.org/", ""), year=w.get("publication_year"),
                            title=w.get("title"), venue=(loc.get("source") or {}).get("display_name"),
                            cites=w.get("cited_by_count"), has_pdf=bool(loc.get("pdf_url")), abstract=abstract))
        return json.dumps(out, ensure_ascii=False)

    def _search_crossref(self, query, title_terms, n, from_year):
        """Fallback when OpenAlex is rate-limited: Crossref works search (no key); OA status unknown (has_pdf None)."""
        url = ("https://api.crossref.org/works?query.bibliographic=" + urllib.parse.quote(f"{title_terms} {query}")
               + f"&filter=from-pub-date:{from_year},type:journal-article&rows={min(n, 50)}"
               + "&select=DOI,title,issued,container-title,is-referenced-by-count,abstract")
        data = json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "catalyst-essay-agent"}), timeout=60))
        out = []
        for w in data["message"]["items"]:
            title = (w.get("title") or [""])[0]
            if not all(t.lower()[:6] in title.lower() for t in title_terms.split()):
                continue
            ab = re.sub(r"<[^>]+>", " ", w.get("abstract") or "")[:350]
            out.append(dict(doi=w["DOI"].lower(), year=(w.get("issued", {}).get("date-parts") or [[None]])[0][0], title=title,
                            venue=(w.get("container-title") or [""])[0], cites=w.get("is-referenced-by-count"), has_pdf=None,
                            abstract=ab))
        self.log({"search_fallback": "crossref", "n": len(out)})
        return json.dumps(out, ensure_ascii=False)

    def t_download_papers(self, dois):
        import pypdfium2 as pdfium
        res, failed = [], []
        for doi in dois:
            dst = self.ws / "pdf" / (re.sub(r"[^A-Za-z0-9]+", "_", doi)[:60] + ".pdf")
            if dst.exists():
                res.append(dict(doi=doi, status="ok", file=dst.name)); continue
            try:
                w = json.load(urllib.request.urlopen(urllib.request.Request("https://api.openalex.org/works/doi:" + doi,
                              headers={"User-Agent": "catalyst-essay-agent"}), timeout=60))
            except Exception as e:  # noqa: BLE001
                res.append(dict(doi=doi, status="not in OpenAlex")); continue
            urls = list(dict.fromkeys(l.get("pdf_url") for l in [w.get("best_oa_location") or {}] + (w.get("locations") or [])
                                      if l and l.get("pdf_url")))
            title_words = re.findall(r"[a-z]{5,}", (w.get("title") or "").lower())[:6]
            ok = False
            for u in urls:
                try:
                    b = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60).read()
                except Exception:  # noqa: BLE001
                    continue
                if not b.startswith(b"%PDF"):
                    continue
                dst.write_bytes(b)
                try:
                    pdf = pdfium.PdfDocument(str(dst))
                    txt = " ".join(pdf[i].get_textpage().get_text_range() for i in range(min(2, len(pdf)))).lower()
                    n = len(pdf)
                    pdf.close()
                except Exception:  # noqa: BLE001
                    dst.unlink(); continue
                if doi.lower() in txt or sum(x in txt for x in title_words) >= max(3, len(title_words) - 2):
                    res.append(dict(doi=doi, status="ok", file=dst.name, pages=n, route="open access")); ok = True; break
                dst.unlink()
            if not ok:
                failed.append(doi)
        if failed:
            lst = self.ws / "pdf" / "_nus_todo.txt"
            lst.write_text("\n".join(failed), encoding="utf-8")
            while NUS_LOCK.exists() and time.time() - NUS_LOCK.stat().st_mtime < 1800:
                time.sleep(5)
            NUS_LOCK.write_text(str(os.getpid()))
            try:
                subprocess.run(["cmd", "/c", NUS_FETCH, "fetch", "-f", str(lst), "-o", str(self.ws / "pdf"), "--headless"],
                               capture_output=True, timeout=900)
            finally:
                NUS_LOCK.unlink(missing_ok=True)
            man = self.ws / "pdf" / "manifest.csv"
            got = {}
            if man.exists():
                for r in csv.DictReader(open(man, encoding="utf-8-sig")):
                    got[r["doi"]] = r
            for doi in failed:
                r = got.get(doi)
                if r and r["status"] in ("ok", "skip") and r.get("file"):
                    src = self.ws / "pdf" / r["file"]
                    dst = self.ws / "pdf" / (re.sub(r"[^A-Za-z0-9]+", "_", doi)[:60] + ".pdf")
                    if src.exists() and src != dst:
                        src.replace(dst)
                    res.append(dict(doi=doi, status="ok", file=dst.name, pages=r.get("pages"), route="NUS proxy"))
                else:
                    res.append(dict(doi=doi, status="failed", note=(r or {}).get("note", "")[:80] if r else "no PDF"))
        return json.dumps(res)

    def t_ocr_papers(self):
        while OCR_LOCK.exists() and time.time() - OCR_LOCK.stat().st_mtime < 1800:
            time.sleep(5)
        OCR_LOCK.write_text(str(os.getpid()))
        try:
            p = subprocess.run([DOCLING_PY, str(OCR_SCRIPT), "_agent_", "4.0"], cwd=str(self.ws),
                               capture_output=True, text=True, timeout=3000,
                               env=dict(os.environ, DOCLING_SRC=str(self.ws / "pdf"), DOCLING_DST=str(self.ws / "ocr")))
        finally:
            OCR_LOCK.unlink(missing_ok=True)
        import ast
        logs = [ast.literal_eval(l) for l in p.stdout.splitlines() if l.startswith("{")] if p.returncode == 0 else []
        files = sorted(x.name for x in (self.ws / "ocr").glob("*.md"))
        return json.dumps(dict(returncode=p.returncode, parsed_now=logs, md_files=files,
                               stderr_tail=p.stderr[-600:] if p.returncode else ""), default=str)

    def t_extract_records(self, paper_stem, instructions, fields, figure_keywords):
        md = self.path(f"ocr/{paper_stem}.md")
        if not md.exists():
            return f"no ocr/{paper_stem}.md; files: " + ", ".join(x.stem for x in (self.ws / 'ocr').glob('*.md'))
        num = {"type": "object", "additionalProperties": False, "required": ["value", "unit", "qualifier"],
               "properties": {"value": {"type": ["number", "null"]}, "unit": {"type": ["string", "null"]},
                              "qualifier": {"type": "string", "enum": ["=", "~", "<", ">", "missing"]}}}
        props = {}
        for f in fields:
            props[f["name"]] = (num if f["kind"] == "number" else
                                {"type": ["integer", "null"], "description": f["description"]} if f["kind"] == "integer" else
                                {"type": ["string", "null"], "description": f["description"]})
        for extra in ("location", "data_source_type"):
            props.setdefault(extra, {"type": ["string", "null"]})
        rec = {"type": "object", "additionalProperties": False, "required": list(props), "properties": props}
        schema = {"type": "object", "additionalProperties": False, "required": ["records", "notes"],
                  "properties": {"records": {"type": "array", "items": rec}, "notes": {"type": "string"}}}
        figs = json.loads((md.parent / (md.stem + "_figs.json")).read_text(encoding="utf-8"))
        kws = [k.lower() for k in figure_keywords] or ["conversion", "selectivity"]
        chosen = [f for f in figs if f["caption"] and any(k in f["caption"].lower() for k in kws)][:12]
        content = [{"type": "input_text", "text": md.read_text(encoding="utf-8")}]
        for f in chosen:
            p = md.parent / (md.stem + "_figs") / f["file"]
            if p.exists():
                content.append({"type": "input_text", "text": f"[Image: picture on page {f['page']}] {f['caption'][:500]}"})
                content.append({"type": "input_image", "detail": "high",
                                "image_url": "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode()})
        field_doc = "\n".join(f"- {f['name']} ({f['kind']}): {f['description']}" for f in fields)
        sysmsg = ("You extract experimental data from one research paper given as a Docling parse (text with '=== PAGE n ===' "
                  "markers, Markdown tables) plus images of selected figures. Copy numbers exactly as printed with their unit; "
                  "qualifier '=' printed, '~' read from a plot, 'missing' when absent (value null). Never compute or guess. "
                  "One record per catalyst x condition measured in this paper. Fields:\n" + field_doc + "\n\n" + instructions)
        t = time.time()
        _, text, final = self.respond([{"role": "user", "content": content}], sysmsg, None, effort="medium", schema=schema)
        u = final.usage
        self.tok["extract_in"] += u.input_tokens
        self.tok["extract_out"] += u.output_tokens
        self.tok["extract_calls"] += 1
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            data = {"records": [], "notes": "UNPARSEABLE"}
        data["_meta"] = dict(tokens_in=u.input_tokens, tokens_out=u.output_tokens, seconds=round(time.time() - t, 1),
                             images=len(chosen), model=self.model)
        (self.ws / "extracted" / f"{paper_stem}.json").write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
        return json.dumps(dict(file=f"extracted/{paper_stem}.json", n_records=len(data["records"]), images=len(chosen),
                               notes=data.get("notes", "")[:600]))

    def t_read_file(self, path, start, n):
        lines = self.path(path).read_text(encoding="utf-8", errors="replace").splitlines()
        return f"[{len(lines)} lines]\n" + "\n".join(lines[max(0, start):max(0, start) + min(n, 400)])

    def t_write_file(self, path, content):
        p = self.path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return f"wrote {path} ({len(content)} chars)"

    def t_run_python(self, name, code, timeout_s):
        p = self.path(f"scripts/{re.sub(r'[^A-Za-z0-9_]+', '_', name)}.py")
        p.write_text(code, encoding="utf-8")
        try:
            r = subprocess.run(["bash", PY.replace("\\", "/"), str(p)], cwd=str(self.ws), capture_output=True, text=True,
                               timeout=min(max(timeout_s, 10), 900), encoding="utf-8", errors="replace")
            out = (r.stdout or "") + ("\n[stderr]\n" + r.stderr[-3000:] if r.stderr else "") + f"\n[exit {r.returncode}]"
        except subprocess.TimeoutExpired:
            out = "[timeout]"
        return out

    # ------------------------------------------------------------ loop
    def run(self):
        if self.db_key:
            instructions = METHOD_DB.format(max_turns=self.max_turns, n_papers=len({r["paper"] for r in self.db}),
                                            budget=self.budget, n_masked=self.n_masked)
            tools = DB_TOOLS + [t for t in TOOLS if t.get("name") in ("read_file", "write_file", "run_python", "finish")]
        elif self.build:
            instructions = METHOD_BUILD.format(reaction=self.reaction, stages=", ".join(STAGES), n_target=self.n_target,
                                               n_max=self.n_max, max_turns=self.max_turns)
            keep = ("search_papers", "screen_papers", "download_papers", "ocr_papers", "extract_papers", "read_file", "write_file", "finish")
            tools = BUILD_TOOLS + [t for t in FULL_TOOLS + TOOLS if t.get("name") in keep and t.get("type") == "function"]
            tools = list({t.get("name", t["type"]): t for t in tools}.values()) + [t for t in TOOLS if t.get("name") == "run_python"]
        elif self.lean:
            self.setup_lean(self.lean)
            instructions = METHOD_LEAN.format(reaction=self.cfg["name"], key=self.cfg["stoich"]["key"], product=self.cfg["stoich"]["product"],
                                              n_target=self.n_target, n_max=self.n_max, max_turns=self.max_turns)
            tools = LEAN_TOOLS
        elif self.full:
            instructions = METHOD_FULL.format(max_turns=self.max_turns, n_target=self.n_target, n_max=self.n_max)
            tools = FULL_TOOLS + [sg.UPDATE_PLAN_TOOL]
        else:
            instructions = METHOD.format(max_turns=self.max_turns)
            tools = TOOLS
        items = [{"role": "user", "content": f"Reaction: {self.reaction}. Start now."}]
        critic_rounds = 0
        if self.full and not self.lean:
            plan = sg.make_plan(self, instructions, tools)
            items = [{"role": "user", "content": f"Reaction: {self.reaction}.\nYour plan (plan.json; mark progress with "
                                                 "update_plan, revise a step if needed):\n"
                                                 + json.dumps(plan, ensure_ascii=False) + "\nStart now."}]
        self.log({"start": self.reaction, "model": self.model})
        summary = None
        for turn in range(self.max_turns):
            if turn == self.max_turns - 8:
                items.append({"role": "user", "content": "Eight tool turns left: write report.md now and finish."})
            out, text, final = self.respond(items, instructions, tools, effort="medium")
            u = final.usage
            self.tok["agent_in"] += u.input_tokens
            self.tok["agent_out"] += u.output_tokens
            self.tok["agent_calls"] += 1
            calls = []
            for o in out:
                d = o.model_dump(exclude_none=True)
                d.pop("status", None) if o.type == "function_call" else None
                items.append(d)
                if o.type == "function_call":
                    calls.append(o)
                elif o.type == "message":
                    self.log({"turn": turn, "message": text[:1500]})
                elif o.type == "web_search_call":
                    self.log({"turn": turn, "web_search": str(getattr(o, "action", ""))[:300]})
            if not calls:
                items.append({"role": "user", "content": "Continue with the tools; call finish when report.md is written."})
                continue
            for c in calls:
                args = json.loads(c.arguments or "{}")
                t = time.time()
                if c.name == "finish" and self.full and not self.lean and critic_rounds < 2:
                    critic_rounds += 1
                    res = sg.critique(self, critic_rounds)
                    major = [i for i in res["issues"] if i["severity"] == "major"]
                    if res["verdict"] == "pass" or not major:
                        summary = args.get("summary", "")
                        out_s = "ok (critic passed)"
                    else:
                        out_s = ("NOT FINISHED: an independent reviewer found major issues; fix report.md (and rerun tools if "
                                 "needed), then call finish again:\n" + json.dumps(major, ensure_ascii=False))
                elif c.name == "finish":
                    summary = args.get("summary", "")
                    out_s = "ok"
                elif c.name == "update_plan":
                    out_s = sg.update_plan(self, **args)
                else:
                    try:
                        prefix = ("b_" if self.build and hasattr(self, "b_" + c.name) else
                                  "l_" if self.lean and hasattr(self, "l_" + c.name) else
                                  "f_" if self.full and hasattr(self, "f_" + c.name) else "t_")
                        out_s = getattr(self, prefix + c.name)(**args)
                    except Exception as e:  # noqa: BLE001
                        out_s = f"ERROR {type(e).__name__}: {str(e)[:500]}"
                dt = time.time() - t
                self.tool_time[c.name] = self.tool_time.get(c.name, 0) + dt
                if len(out_s) > MAX_OUT:
                    out_s = out_s[:MAX_OUT] + f"\n...[truncated {len(out_s) - MAX_OUT} chars]"
                items.append({"type": "function_call_output", "call_id": c.call_id, "output": out_s})
                short = {k: (v if len(str(v)) < 200 else str(v)[:200] + "...") for k, v in args.items()}
                self.log({"turn": turn, "tool": c.name, "args": short, "seconds": round(dt, 1), "output": out_s[:800]})
            self.write_ledger()
            if summary is not None:
                break
        if self.build:
            self.finish_build()
        self.write_ledger("finished" if summary is not None else "turn limit")
        if self.lean and getattr(self, "analysis", None):
            self.write_report(decision=summary or "")
        self.log({"end": summary})
        print(json.dumps(json.loads((self.ws / "ledger.json").read_text()), indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("name")
    ap.add_argument("reaction")
    ap.add_argument("--model", default="gpt-5.6-sol")
    ap.add_argument("--max-turns", type=int, default=90)
    ap.add_argument("--db", default=None, help="pdh | ch4: masked literature database instead of downloading papers")
    ap.add_argument("--budget-frac", type=float, default=0.3)
    ap.add_argument("--full", action="store_true", help="complete autonomous run from the reaction name")
    ap.add_argument("--n-target", type=int, default=12)
    ap.add_argument("--n-max", type=int, default=20)
    ap.add_argument("--extract-model", default="gpt-5.6-sol")
    ap.add_argument("--lean", default=None, help="pdh|ch4|nh3dec|rwgs|etoh: lean autonomous run with the fixed plant model")
    ap.add_argument("--build", default=None, help="pdh|ch4|nh3|meoh: the agent builds the plant model itself (workspace D:/agent_runs)")
    a = ap.parse_args()
    Run(a.name, a.reaction, a.model, a.max_turns, a.db, a.budget_frac, a.full, a.n_target, a.n_max, a.extract_model, a.lean, a.build).run()
