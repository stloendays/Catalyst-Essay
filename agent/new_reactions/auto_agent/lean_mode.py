"""Lean autonomous mode (runner.py --lean <rxn>): the agent only chooses; everything else is fixed code.

The agent chooses the search terms, which papers to keep, which to replace and the extraction scope. Download,
OCR, extraction, usability check, plant cost (configs/<rxn>_ours.json, fixed), NCE metrics and the report are fixed
code. No web search, no file reading, no config writing, no critic; tool outputs are summaries.
Accounting written with the report: candidates found and screened, papers downloaded, usable, replaced (with the
reason), tokens split into extraction (per paper) and agent decisions.
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
NR = HERE.parent
sys.path.insert(0, str(NR))
import chain  # noqa: E402
import plant_framework as fw  # noqa: E402

METHOD_LEAN = """You are a research agent. Fixed tools do all the work; you make the choices. Reaction: {reaction} (key reactant {key}, product {product}).
Goal: {n_target} papers with usable data (download at most {n_max}).
1. search_papers, then screen_papers with your inclusion criteria (experimental papers on this reaction that report feed, conversion, selectivity and flow / space velocity / catalyst mass; no reviews, no computational-only papers, no other reaction modes).
2. download_papers for the most promising (prefer data-rich abstracts and a spread of catalyst families), then process_papers (OCR + extraction + usability check).
3. Papers without usable records: call replace_papers with each DOI and the reason, then download and process replacements, until the goal or the download limit is reached.
4. run_analysis (fixed plant model; it writes the report with the NCE metrics), then finish with one or two sentences on which catalyst and condition a plant should use and why.
Reply only with tool calls; at most one line of text per turn. Budget about {max_turns} turns."""

LEAN_TOOLS = [
    {"type": "function", "name": "search_papers", "strict": True,
     "description": "OpenAlex search (falls back to Crossref); adds to candidates. Returns counts and the top titles.",
     "parameters": {"type": "object", "additionalProperties": False, "required": ["query", "title_terms", "n", "from_year"],
                    "properties": {"query": {"type": "string"}, "title_terms": {"type": "string"}, "n": {"type": "integer"},
                                   "from_year": {"type": "integer"}}}},
    {"type": "function", "name": "screen_papers", "strict": True,
     "description": "LLM include/exclude of unscreened candidates with your criteria; returns the included ones (doi, short title, citations, has_pdf).",
     "parameters": {"type": "object", "additionalProperties": False, "required": ["criteria"], "properties": {"criteria": {"type": "string"}}}},
    {"type": "function", "name": "download_papers", "strict": True,
     "description": "Download PDFs (open access, then NUS proxy). Returns ok/failed counts and the failed DOIs.",
     "parameters": {"type": "object", "additionalProperties": False, "required": ["dois"],
                    "properties": {"dois": {"type": "array", "items": {"type": "string"}}}}},
    {"type": "function", "name": "process_papers", "strict": True,
     "description": "OCR + extraction + usability check of every downloaded paper not yet processed. Returns per paper: records, usable, the main missing field.",
     "parameters": {"type": "object", "additionalProperties": False, "required": ["scope"],
                    "properties": {"scope": {"type": "string", "description": "what is in and out of scope for this reaction"}}}},
    {"type": "function", "name": "replace_papers", "strict": True,
     "description": "Log papers you drop (no usable data) with the reason; they stay on disk but leave the analysis set.",
     "parameters": {"type": "object", "additionalProperties": False, "required": ["drops"],
                    "properties": {"drops": {"type": "array", "items": {"type": "object", "additionalProperties": False,
                                   "required": ["paper", "reason"],
                                   "properties": {"paper": {"type": "string"}, "reason": {"type": "string"}}}}}}},
    {"type": "function", "name": "run_analysis", "strict": True,
     "description": "Fixed plant model + NCE metrics on the usable records of the kept papers; writes report.md. Returns the headline numbers.",
     "parameters": {"type": "object", "additionalProperties": False, "required": [], "properties": {}}},
    {"type": "function", "name": "finish", "strict": True,
     "description": "End the run with your decision in one or two sentences.",
     "parameters": {"type": "object", "additionalProperties": False, "required": ["summary"], "properties": {"summary": {"type": "string"}}}},
]


class LeanMixin:
    def setup_lean(self, rxn):
        self.rxn = rxn
        self.cfg_path = NR / "configs" / f"{rxn}_ours.json"
        self.cfg = fw.load(rxn, "ours")
        self.dropped = {}

    def _paper_of(self, stem):
        return stem

    def l_search_papers(self, query, title_terms, n, from_year):
        return self.f_search_papers(query, title_terms, n, from_year)

    def l_screen_papers(self, criteria):
        return self.f_screen_papers(criteria)

    def _shared_cache(self):
        """DOI -> PDF already in the shared folder pdf/<rxn>/ (the user's manual downloads and earlier runs)."""
        import re
        d = NR / "pdf" / self.rxn
        cache = {}
        man = d / "manifest.csv"
        if man.exists():
            for r in csv.DictReader(open(man, encoding="utf-8-sig")):
                if r.get("status") in ("ok", "skip") and r.get("file") and (d / r["file"]).exists():
                    cache[r["doi"].lower()] = d / r["file"]
        for p in d.glob("*.pdf"):
            cache.setdefault(p.stem.replace("_", ".", 1).lower(), p)       # 10_1021_x -> 10.1021_x (fetch_oa naming)
            m = re.match(r"(10)_(\d{4,5})_(.+)", p.stem)
            if m:
                cache.setdefault(f"10.{m.group(2)}/{m.group(3)}".lower().replace("_", "."), p)
        return cache

    def l_download_papers(self, dois):
        import re
        import shutil
        cache = self._shared_cache()
        todo, from_cache = [], 0
        for doi in dois:
            src = cache.get(doi.lower()) or cache.get(doi.lower().replace("/", ".").replace("-", "."))
            dst = self.ws / "pdf" / (re.sub(r"[^A-Za-z0-9]+", "_", doi)[:60] + ".pdf")
            if src and not dst.exists():
                shutil.copy(src, dst)
                from_cache += 1
            elif not dst.exists():
                todo.append(doi)
        res = json.loads(self.t_download_papers(todo)) if todo else []
        ok = [r for r in res if r["status"] == "ok"]
        return json.dumps(dict(from_shared_folder=from_cache, downloaded=len(ok), failed=[r["doi"] for r in res if r["status"] != "ok"],
                               pdfs_total=len(list((self.ws / "pdf").glob("*.pdf")))))

    def l_process_papers(self, scope):
        self.t_ocr_papers()
        key, product = self.cfg["stoich"]["key"], self.cfg["stoich"]["product"]
        cofeed = next(iter(self.cfg["lab_feed"]["default_ratio"]), "none")
        self.f_extract_papers(self.cfg["name"], key, product, cofeed, scope)
        rows, gates = chain.normalise(self.ws, self.cfg)
        per = defaultdict(lambda: dict(records=0, usable=0, miss=Counter()))
        for r in rows:
            p = per[r["paper"]]
            p["records"] += 1
            p["usable"] += bool(r["usable"])
            if not r["usable"]:
                for k, lab in (("T_K", "temperature"), ("X", "conversion"), ("S", "selectivity"), ("r", "rate or flow+mass")):
                    if not r[k]:
                        p["miss"][lab] += 1
                        break
        for f in (self.ws / "extracted").glob("*.json"):
            per.setdefault(f.stem, dict(records=0, usable=0, miss=Counter({"no records": 1})))
        out = []
        for stem, p in sorted(per.items()):
            out.append(dict(paper=stem, records=p["records"], usable=p["usable"],
                            main_missing=(p["miss"].most_common(1)[0][0] if p["miss"] else ""), dropped=stem in self.dropped))
        with open(self.ws / "paper_log.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, ["paper", "records", "usable", "main_missing", "dropped", "drop_reason"])
            w.writeheader()
            for o in out:
                w.writerow(dict(o, drop_reason=self.dropped.get(o["paper"], "")))
        kept = [o for o in out if not o["dropped"]]
        return json.dumps(dict(papers=out, usable_papers=sum(o["usable"] > 0 for o in kept), gates=gates))

    def l_replace_papers(self, drops):
        for d in drops:
            self.dropped[d["paper"]] = d["reason"][:200]
        return json.dumps(dict(dropped_total=len(self.dropped)))

    def l_run_analysis(self):
        rows, gates = chain.normalise(self.ws, self.cfg)
        rows = [r for r in rows if r["paper"] not in self.dropped]
        ver = chain.verify(self.ws)
        if not any(r["usable"] for r in rows):
            return json.dumps(dict(error="no usable records"))
        s = chain.analyse(self.ws, self.cfg, rows)
        sens = chain.sensitivity(self.ws, self.cfg, rows)
        self.analysis = dict(summary=s, verify=ver, gates=gates, sensitivity=sens)
        self.write_report()
        return json.dumps(dict(n_usable=s["n_usable"], papers=s["n_papers"], reference=s["reference"]["cost"],
                               largest=s["reference"]["largest"], cheapest=s["cheapest"], ranking=s["ranking"],
                               attribution=s["attribution_share"], elasticities=s["cost_change_at_reference"],
                               traceable=ver["traceable"]), default=str)

    def write_report(self, decision=""):
        a = self.analysis
        s, ver = a["summary"], a["verify"]
        cand = list(csv.DictReader(open(self.ws / "candidates.csv", encoding="utf-8"))) if (self.ws / "candidates.csv").exists() else []
        log = list(csv.DictReader(open(self.ws / "paper_log.csv", encoding="utf-8"))) if (self.ws / "paper_log.csv").exists() else []
        led = json.loads((self.ws / "ledger.json").read_text(encoding="utf-8")) if (self.ws / "ledger.json").exists() else {}
        ex = list(csv.DictReader(open(self.ws / "token_usage_extract.csv", encoding="utf-8"))) if (self.ws / "token_usage_extract.csv").exists() else []
        ext_tok = sum(int(r["prompt_tokens"]) + int(r["completion_tokens"]) for r in ex)
        rk = s["ranking"]
        L = [f"# {self.cfg['name']}: autonomous run {datetime.now():%Y-%m-%d %H:%M}", "",
             f"Plant model: plant_framework {fw.FRAMEWORK_VERSION}, {self.cfg_path.name} "
             f"(SHA-256 {hashlib.sha256(self.cfg_path.read_bytes()).hexdigest()[:16]}).", "",
             "## Papers", "",
             f"candidates found {len(cand)}, screened {sum(1 for c in cand if c.get('screened'))}, included {sum(1 for c in cand if c.get('include') == 'True')}; "
             f"downloaded {len(list((self.ws / 'pdf').glob('*.pdf')))}; processed {len(log)}; "
             f"with usable records {sum(1 for r in log if int(r['usable']) > 0 and r['dropped'] != 'True')}; replaced/dropped {len(self.dropped)}.", ""]
        for p, why in self.dropped.items():
            L.append(f"- dropped {p}: {why}")
        L += ["", "## Data", "",
              f"records {s['n_records']}, usable {s['n_usable']} from {s['n_papers']} papers; printed values found in the paper "
              f"{ver['found']}/{ver['printed']} ({ver['traceable']}); plot readings {ver['plot_readings']}. Every record keeps its page and "
              "table/figure location in records.csv.", "",
              "## Plant cost (NCE metrics)", "",
              f"reference plant ({s['reference']['name']}): {s['reference']['cost']} USD/t; parts {s['reference']['parts']}; largest {s['reference']['largest']}.",
              f"cheapest literature record: {s['cheapest']}; records below the reference {s['below_reference']} of {s['n_usable']}.", "",
              "Same definitions as the NCE methanol and NH3 field results (nce_metrics.py reproduces 26/63, 50/81 and 12/44 from the NCE tables).", "",
              "| lab metric | level | groups (papers) | lab leader is not the cheapest | 95 % CI | other catalyst | same catalyst, other T | regret > 5 % | median regret of changed |",
              "|---|---|---:|---:|---|---:|---:|---:|---:|"]
        for m, v in rk.items():
            for lvl in ("catalyst_level", "point_level"):
                x = v[lvl]
                if not x.get("groups"):
                    L.append(f"| {m} | {lvl.replace('_', ' ')} | 0 | - | - | - | - | - | - |")
                    continue
                k = x.get("kinds", {})
                L.append(f"| {m} | {lvl.replace('_', ' ')} | {x['groups']} ({x['papers']}) | {x['changed']} | {x['ci95']} | "
                         f"{k.get('other catalyst', '') if lvl == 'point_level' else ''} | {k.get('same catalyst, other temperature', '') if lvl == 'point_level' else ''} | "
                         f"{x['gt5pct']} | {x['median_regret_changed']} |")
        L += ["", f"attribution of the cost gap to the reference: {s['attribution_share']}",
              f"cost change at the reference: {s['cost_change_at_reference']}",
              f"backward design: {s['selectivity_needed_reachable']} records can reach the reference cost by selectivity alone; "
              f"{s['records_X_below_half_Xp']} records measured below half the plant per-pass conversion.", "",
              "## Sensitivity", ""]
        for x in a["sensitivity"]:
            L.append(f"- {x['param']} {x['side']} {x['value']}: reference {x['ref_cost']}, largest {x['largest']} ({x['largest_share']}), "
                     f"productivity leader differs {x['productivity_leader_differs']}, cheapest {x['cheapest']}")
        L += ["", "## Run", "",
              f"wall {led.get('wall_minutes')} min; agent decisions {led.get('tokens', {}).get('agent_in', 0) + led.get('tokens', {}).get('agent_out', 0)} tokens; "
              f"extraction {ext_tok} tokens over {len(ex)} papers ({round(ext_tok / max(len(ex), 1))} per paper).", ""]
        if decision:
            L += ["## Decision", "", decision, ""]
        (self.ws / "report.md").write_text("\n".join(L), encoding="utf-8")
