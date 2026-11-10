"""Full autonomous mode of the agent (runner.py --full): from a reaction name to the report, no human step.

The agent decides; the shared tools do the mechanical work:
  search_papers / screen_papers   OpenAlex search; LLM include/exclude on title+abstract with the agent's criteria
  download_papers / ocr_papers     open-access + NUS proxy download; Docling OCR (GPU), both locked machine-wide
  extract_papers                   one LLM call per paper, standard schema, in parallel (chain.extract)
  check_config                     the agent writes the reaction's plant parameters ONCE (configs/TEMPLATE.json)
  run_chain                        normalise -> self-check -> plant cost -> rankings -> attribution -> backward
                                   design -> sensitivity, in the shared framework (chain.py, plant_framework.py)
"""
from __future__ import annotations

import csv
import json
import shutil
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
NR = HERE.parent
sys.path.insert(0, str(NR))
import chain  # noqa: E402

METHOD_FULL = """You are a research agent. Given only a reaction, run the whole analysis chain of this project on your own and write the report. Nobody will answer questions; decide everything yourself and work only through the tools.

Goal: from the open literature on the reaction, find where the industrial bottleneck lies, which literature catalyst a plant would choose, and whether the way papers rank catalysts (conversion, productivity) agrees with what a plant would choose. Aim for about {n_target} papers with usable data (fewer is acceptable if the literature is thin; do not chase more than {n_max} downloads).

Steps (the tools do the mechanical work; you make the choices):
1. search_papers (OpenAlex, open access; note that OpenAlex stems title words, so check the returned titles), then screen_papers with your inclusion criteria: experimental papers on this reaction over heterogeneous catalysts that report conversion and selectivity under stated conditions; exclude reviews, computational/TEA-only papers and other reaction modes. Prefer papers whose abstracts suggest tables of performance data and a spread of catalyst families.
2. download_papers for your choice (failures are dropped), ocr_papers, extract_papers (tell it the key reactant, the product, the co-feed whose ratio matters and the scope).
3. Write the plant configuration ONCE: copy configs/TEMPLATE.json (read it with read_file) to config.json, fill every field for a world-scale plant of this reaction, sourcing every number with web_search (official statistics, open techno-economic papers, company filings, licensor data) and recording it in 'sources'; unsourced values are marked as assumptions and given a range in 'uncertain'. Metal prices: start from configs/metal_prices.json (copied to your workspace) and add any missing element. Run check_config until it reports no problems and the reference plant cost is consistent with a published plant or TEA cost (state the comparison). Do not rewrite the model: the framework is fixed; you choose the parameters and the two switches.
4. run_chain(config.json): it normalises the records, runs the self-check, costs every usable record with the plant optimising its per-pass conversion, and returns rankings, attribution, elasticities, backward design and sensitivity.
5. Write report.md: papers used and dropped with reasons; records extracted and usable; self-check; parameter table with sources; reference plant cost and its breakdown; paper ranking vs plant ranking (counts with denominators, other catalyst vs other temperature, regrets); the bottleneck (which catalyst property or non-catalyst factor carries the cost, with the elasticities); the catalyst a plant would choose; backward design; sensitivity; what the data could not support; time and token cost of the run from ledger.json. Then call finish.

Rules: never invent numbers or sources. Keep tool outputs small. Budget about {max_turns} tool turns."""

FULL_TOOLS = [
    {"type": "web_search"},
    {"type": "function", "name": "search_papers", "strict": True,
     "description": "OpenAlex search of open-access articles; appends to candidates.csv. Returns doi, year, title, venue, citations, has_pdf, short abstract.",
     "parameters": {"type": "object", "additionalProperties": False, "required": ["query", "title_terms", "n", "from_year"],
                    "properties": {"query": {"type": "string"}, "title_terms": {"type": "string"}, "n": {"type": "integer"},
                                   "from_year": {"type": "integer"}}}},
    {"type": "function", "name": "screen_papers", "strict": True,
     "description": "LLM include/exclude of every unscreened paper in candidates.csv by title and abstract with your criteria; returns the included ones (doi, title, citations, confidence).",
     "parameters": {"type": "object", "additionalProperties": False, "required": ["criteria"],
                    "properties": {"criteria": {"type": "string"}}}},
    {"type": "function", "name": "download_papers", "strict": True,
     "description": "Download PDFs (open-access locations, then the NUS library proxy) into pdf/. Returns status per DOI.",
     "parameters": {"type": "object", "additionalProperties": False, "required": ["dois"],
                    "properties": {"dois": {"type": "array", "items": {"type": "string"}}}}},
    {"type": "function", "name": "ocr_papers", "strict": True,
     "description": "Docling OCR of every PDF in pdf/ not yet parsed (ocr/<stem>.md + figure crops).",
     "parameters": {"type": "object", "additionalProperties": False, "required": [], "properties": {}}},
    {"type": "function", "name": "extract_papers", "strict": True,
     "description": "Extract catalyst-performance records from every parsed paper not yet extracted (standard schema, one LLM call per paper, in parallel).",
     "parameters": {"type": "object", "additionalProperties": False, "required": ["reaction", "key_reactant", "product", "cofeed", "scope"],
                    "properties": {"reaction": {"type": "string"}, "key_reactant": {"type": "string", "description": "formula, e.g. C3H8"},
                                   "product": {"type": "string", "description": "formula"}, "cofeed": {"type": "string", "description": "formula or 'none'"},
                                   "scope": {"type": "string", "description": "what is in and out of scope for this reaction"}}}},
    {"type": "function", "name": "read_file", "strict": True,
     "description": "Read lines of a text file in the workspace.",
     "parameters": {"type": "object", "additionalProperties": False, "required": ["path", "start", "n"],
                    "properties": {"path": {"type": "string"}, "start": {"type": "integer"}, "n": {"type": "integer"}}}},
    {"type": "function", "name": "write_file", "strict": True,
     "description": "Write a text file in the workspace.",
     "parameters": {"type": "object", "additionalProperties": False, "required": ["path", "content"],
                    "properties": {"path": {"type": "string"}, "content": {"type": "string"}}}},
    {"type": "function", "name": "check_config", "strict": True,
     "description": "Validate the plant config and compute the reference plant (cost, breakdown, per-pass conversion, equilibrium).",
     "parameters": {"type": "object", "additionalProperties": False, "required": ["path"],
                    "properties": {"path": {"type": "string"}}}},
    {"type": "function", "name": "run_chain", "strict": True,
     "description": "Normalise + self-check + plant cost + rankings + attribution + backward design + sensitivity with this config. Writes records.csv, costs_main.csv, summary_main.json, sensitivity.csv.",
     "parameters": {"type": "object", "additionalProperties": False, "required": ["config_path"],
                    "properties": {"config_path": {"type": "string"}}}},
    {"type": "function", "name": "finish", "strict": True,
     "description": "End the run after report.md is written.",
     "parameters": {"type": "object", "additionalProperties": False, "required": ["summary"],
                    "properties": {"summary": {"type": "string"}}}},
]


class FullMixin:
    def setup_full(self):
        shutil.copy(NR / "configs" / "TEMPLATE.json", self.ws / "configs_TEMPLATE.json")
        (self.ws / "configs").mkdir(exist_ok=True)
        shutil.copy(NR / "configs" / "TEMPLATE.json", self.ws / "configs" / "TEMPLATE.json")
        shutil.copy(NR / "configs" / "metal_prices.json", self.ws / "configs" / "metal_prices.json")

    def f_search_papers(self, query, title_terms, n, from_year):
        out = json.loads(self.t_search_papers(query, title_terms, n, from_year))
        p = self.ws / "candidates.csv"
        have = set()
        if p.exists():
            have = {r["doi"] for r in csv.DictReader(open(p, encoding="utf-8"))}
        new = [r for r in out if r["doi"] and r["doi"] not in have]
        with open(p, "a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, ["doi", "year", "title", "venue", "cites", "has_pdf", "abstract", "screened", "include", "confidence", "reason"])
            if not have:
                w.writeheader()
            for r in new:
                w.writerow(dict(r, screened="", include="", confidence="", reason=""))
        short = [dict(doi=r["doi"], year=r["year"], title=(r["title"] or "")[:110], cites=r["cites"], has_pdf=r["has_pdf"]) for r in out]
        return json.dumps(dict(new=len(new), total_candidates=len(have) + len(new), results=short[:40]), ensure_ascii=False)

    def f_screen_papers(self, criteria):
        p = self.ws / "candidates.csv"
        rows = list(csv.DictReader(open(p, encoding="utf-8")))
        todo = [r for r in rows if not r["screened"]]
        schema = {"type": "object", "additionalProperties": False, "required": ["items"],
                  "properties": {"items": {"type": "array", "items": {"type": "object", "additionalProperties": False,
                                 "required": ["doi", "include", "confidence", "reason"],
                                 "properties": {"doi": {"type": "string"}, "include": {"type": "boolean"},
                                                "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
                                                "reason": {"type": "string"}}}}}}
        res = {}
        for i in range(0, len(todo), 40):
            batch = todo[i:i + 40]
            text = "\n\n".join(f"DOI: {r['doi']}\nTitle: {r['title']}\nAbstract: {r['abstract'] or '(none)'}" for r in batch)
            _, out_text, final = self.respond([{"role": "user", "content": text}],
                                              "Screen papers for a catalyst-performance database. " + criteria +
                                              " Without an abstract decide from the title with confidence 'low'. One item per DOI.",
                                              None, effort="low", schema=schema)
            self.tok["extract_in"] += final.usage.input_tokens
            self.tok["extract_out"] += final.usage.output_tokens
            for it in json.loads(out_text)["items"]:
                res[it["doi"]] = it
        for r in rows:
            if r["doi"] in res:
                it = res[r["doi"]]
                r.update(screened="1", include=str(it["include"]), confidence=it["confidence"], reason=it["reason"][:200])
        with open(p, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, list(rows[0]))
            w.writeheader()
            w.writerows(rows)
        inc = [r for r in rows if r["include"] == "True"]
        inc.sort(key=lambda r: (r["confidence"] != "high", -int(r["cites"] or 0)))
        return json.dumps(dict(screened_now=len(todo), included_total=len(inc),
                               included=[dict(doi=r["doi"], title=r["title"][:100], cites=r["cites"], conf=r["confidence"],
                                              has_pdf=r["has_pdf"]) for r in inc[:60]]), ensure_ascii=False)

    def f_extract_papers(self, reaction, key_reactant, product, cofeed, scope):
        def factory():
            return self.extract_router.client
        rows = chain.extract(self.ws, factory, self.extract_model, reaction, key_reactant, product,
                             None if cofeed.lower() == "none" else cofeed, scope, workers=self.extract_workers,
                             usage_csv=self.ws / "token_usage_extract.csv")
        for r in rows:
            if "prompt_tokens" in r:
                self.tok["extract_in"] += r["prompt_tokens"]
                self.tok["extract_out"] += r["completion_tokens"]
                self.tok["extract_calls"] += 1
        return json.dumps(dict(extracted=[dict(paper=r["paper"], n=r.get("n_records"), error=r.get("error")) for r in rows],
                               files=len(list((self.ws / "extracted").glob("*.json")))))

    def _cfg(self, path):
        cfg = json.loads(self.path(path).read_text(encoding="utf-8"))
        mp = json.loads((self.ws / "configs" / "metal_prices.json").read_text(encoding="utf-8"))
        cfg.setdefault("metal_usd_per_kg", {})
        for k, v in mp.items():
            if not k.startswith("_"):
                cfg["metal_usd_per_kg"].setdefault(k, v)
        return cfg

    def f_check_config(self, path):
        try:
            cfg = self._cfg(path)
        except Exception as e:  # noqa: BLE001
            return f"config not readable: {e}"
        probs, ref = chain.check_config(cfg)
        return json.dumps(dict(problems=probs, reference=ref))

    def f_run_chain(self, config_path):
        cfg = self._cfg(config_path)
        probs, _ = chain.check_config(cfg)
        if probs:
            return json.dumps(dict(problems=probs))
        rows, gates = chain.normalise(self.ws, cfg)
        ver = chain.verify(self.ws)
        if not any(r["usable"] for r in rows):
            return json.dumps(dict(records=len(rows), usable=0, gates=gates, verify=ver))
        s = chain.analyse(self.ws, cfg, rows)
        sens = chain.sensitivity(self.ws, cfg, rows)
        res = json.dumps(dict(records=len(rows), gates=gates, verify=ver, summary=s,
                              sensitivity=[{k: v for k, v in x.items()} for x in sens][:24]), default=str)
        (self.ws / "chain_result.json").write_text(res, encoding="utf-8")
        return res
