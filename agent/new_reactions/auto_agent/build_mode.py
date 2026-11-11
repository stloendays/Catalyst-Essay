"""AI-built models (runner.py --build <rxn>): the agent builds the reaction-specific plant model itself.

Advisor, 2026-11-11 (docs/SUPERVISOR_FEEDBACK_2026-11-11.md): AI takes over the whole pipeline including the modeling
step - mechanism, kinetics, reactor, flowsheet, cost model and parameters; humans only inspect; validation against
published TEA that is HELD OUT from the agent; hand-built models are hidden references.

What is fixed (generic infrastructure): search, screening calls, download, Docling OCR, LLM extraction schema, unit
normalisation, the model-contract checks, the NCE ranking metrics, the ledger. What the agent decides and writes:
inclusion criteria, extraction scope, model structure, kinetics, reactor/flowsheet, parameters with sources, model code.

Isolation: the workspace is outside the repository (D:/agent_runs/<run>); scripts the agent runs may not use absolute
paths or '..'; every script is kept. Held-out validation sources (auto_agent/holdout/<rxn>.json, never shown to the
agent) are blocked in download_papers and audited afterwards in the web-search trace (audit_holdout.py).
Stage ledger: the agent declares its stage (set_stage); agent tokens, extraction tokens and wall time accrue to it.

Model contract (model.py written by the agent):
  REACTION = {"key": <formula>, "product": <formula>, "cofeed": <formula or None>, "MW": {formula: g/mol}}
  def reference() -> dict            # the industrial reference plant, same keys as plant_cost(), plus "name"
  def plant_cost(rec: dict) -> dict  # rec: T_K, P_bar, X, S, r (kg product/kg cat/h, lab), y_key, y_cofeed, t_cycle_h,
                                     #      components [[element, wt% or None], ...], catalyst
      returns {"cost_usd_per_t": float,
               "parts": {"feed": .., "energy": .., "capital": .., "catalyst": .., "other": ..},   # USD/t, sum = cost
               "operating": {"T_K": .., "P_bar": .., "per_pass_conversion": ..},
               "balances": {"key_feed_t_per_t": .., "energy_GJ_per_t": .., "capex_usd": .., "capacity_t_per_y": ..}}
"""
from __future__ import annotations

import csv
import importlib.util
import json
import math
import re
import statistics as st
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
NR = HERE.parent
sys.path.insert(0, str(NR))
import chain  # noqa: E402
import nce_metrics as nm  # noqa: E402

AGENT_ROOT = Path(r"D:\agent_runs")
STAGES = ["search", "screening", "download_ocr", "extraction", "mechanism_kinetics", "reactor_flowsheet", "parameters",
          "model_code", "model_checks", "analysis", "report"]

METHOD_BUILD = """You are a research agent. Build, from the open literature, the economic model of an industrial plant for {reaction} and use it to analyse which literature catalysts a plant would choose. Nobody will answer questions; decide everything yourself. Fixed tools do searching, downloading, OCR, extraction and the checks; you make every scientific and modeling decision.

Questions to answer: Does the laboratory ranking of catalysts (activity, conversion, selectivity) predict the catalyst and operating condition a plant would choose? Where does the ranking change, and why? Which catalyst property controls the plant cost, and which effects are attenuated by feedstock cost, equilibrium, recycle, separation, equipment or operation?

Work in stages and call set_stage when you start each one ({stages}).
1. search / screening: find experimental catalyst papers on this reaction ({n_target} papers with usable data, at most {n_max} downloads) and screen them with explicit criteria; say why papers are excluded.
2. download_ocr / extraction: download_papers, ocr_papers, extract_papers (tell it the key reactant, product, co-feed and scope). check_records reports per paper which records are usable.
3. mechanism_kinetics: decide how lab activity transfers to plant conditions (rate law or approach-to-equilibrium form, equilibrium, deactivation) and justify it from the evidence.
4. reactor_flowsheet: decide the reactor type and operating variables, and whether recycle, separation, compression, heat supply, regeneration and catalyst replacement must be represented; justify each.
5. parameters: source every plant parameter (prices, capacity, energy, capital, catalyst life, ...) with web_search, record each with its source in sources.csv (columns: parameter, value, unit, source, location, type = measured | published | assumption, low, high).
6. model_code: write model.py following the contract below (numpy/scipy only; relative paths only). The plant should optimise its free operating variable(s) (for example per-pass conversion against recycle and catalyst amount).
7. model_checks: call check_model until it passes; fix the model, not the checks.
8. analysis: call run_analysis (it costs every usable record with your model and computes the ranking metrics), then explain the results.
9. report: write report.md: papers and exclusions; model choices with their justification (mechanism, kinetics, reactor, flowsheet, what is and is not represented); parameter table (sources.csv); reference plant cost and breakdown; ranking results with denominators; the controlling catalyst property; sensitivity of the conclusion to the uncertain parameters (run your model); what the evidence could not support. Then call finish.

Model contract (model.py):
  REACTION = {{"key": <formula>, "product": <formula>, "cofeed": <formula or None>, "MW": {{formula: g/mol}}}}
  def reference() -> dict   # the industrial reference plant (published plant data): same keys as plant_cost, plus "name" and "record" = the reference catalyst written as a plant_cost input
  def plant_cost(rec) -> dict
     rec: T_K, P_bar, X (lab conversion of the key reactant), S (lab selectivity), r (lab productivity, kg product per kg catalyst per h), y_key, y_cofeed (lab feed mole fractions), t_cycle_h (hours to lose 10 % activity, or None), components ([[element, wt% or None], ...]), catalyst (name)
     returns {{"cost_usd_per_t": .., "parts": {{"feed": .., "energy": .., "capital": .., "catalyst": .., "other": ..}}, "operating": {{"T_K": .., "P_bar": .., "per_pass_conversion": ..}}, "balances": {{"key_feed_t_per_t": .., "energy_GJ_per_t": .. (purchased fuel and electricity as primary energy), "capex_usd": .. (installed capital of the plant), "capacity_t_per_y": ..}}}}  (USD per tonne of product; parts sum to the cost)

Rules: never invent numbers or sources; every cost the report quotes must come from your model, not be copied from a study. Reply with tool calls; keep text to one line per turn. Budget about {max_turns} turns."""

BUILD_TOOLS = [
    {"type": "web_search"},
    {"type": "function", "name": "set_stage", "strict": True, "description": "Declare the stage you are starting (for the time and cost ledger).",
     "parameters": {"type": "object", "additionalProperties": False, "required": ["stage", "note"],
                    "properties": {"stage": {"type": "string", "enum": STAGES}, "note": {"type": "string"}}}},
    {"type": "function", "name": "check_records", "strict": True,
     "description": "Normalise the extracted records (units, productivity from rate or flow x X x S, plausibility gates) for the given reaction card and report per paper: records, usable, main missing field.",
     "parameters": {"type": "object", "additionalProperties": False, "required": ["key", "product", "cofeed"],
                    "properties": {"key": {"type": "string"}, "product": {"type": "string"}, "cofeed": {"type": "string"}}}},
    {"type": "function", "name": "check_model", "strict": True,
     "description": "Import model.py and test the contract on the reference plant and every usable record: finite positive cost, parts sum to the cost, per-pass conversion in (0, 1], key feed >= stoichiometric minimum, cost non-increasing in selectivity and in activity, deterministic. Returns pass/fail per check and the reference plant.",
     "parameters": {"type": "object", "additionalProperties": False, "required": [], "properties": {}}},
    {"type": "function", "name": "run_analysis", "strict": True,
     "description": "Cost every usable record with model.py and compute: lab vs plant ranking (catalyst level and operating-point level, other catalyst vs same catalyst at another temperature, regret, paper bootstrap), one-at-a-time attribution (selectivity, activity, temperature, stability, metal) and cost changes at the reference. Writes costs.csv and analysis.json; returns the summary.",
     "parameters": {"type": "object", "additionalProperties": False, "required": [], "properties": {}}},
]


class BuildMixin:
    def setup_build(self, rxn, holdout):
        self.rxn = rxn
        self.holdout = holdout or {}
        self.stage, self.stage_t0 = "search", time.time()
        self.stage_rows = []
        self.stage_tok0 = dict(self.tok)

    # ---------------- ledger
    def _close_stage(self):
        now = time.time()
        d = {k: self.tok[k] - self.stage_tok0.get(k, 0) for k in self.tok}
        usd = ((d["agent_in"] + d["extract_in"]) * 5 + (d["agent_out"] + d["extract_out"]) * 30) / 1e6
        self.stage_rows.append(dict(stage=self.stage, start=datetime.fromtimestamp(self.stage_t0).isoformat(timespec="seconds"),
                                    wall_s=round(now - self.stage_t0, 1), agent_in=d["agent_in"], agent_out=d["agent_out"],
                                    extract_in=d["extract_in"], extract_out=d["extract_out"], usd_gpt55=round(usd, 3)))
        with open(self.ws / "stage_ledger.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, list(self.stage_rows[0]))
            w.writeheader()
            w.writerows(self.stage_rows)
        self.stage_t0, self.stage_tok0 = now, dict(self.tok)

    def b_set_stage(self, stage, note):
        if stage != self.stage:
            self._close_stage()
            self.stage = stage
        self.log({"stage": stage, "note": note[:300]})
        return json.dumps(dict(stage=stage))

    # ---------------- guarded script runner and download block
    def b_run_python(self, name, code, timeout_s):
        if re.search(r"[A-Za-z]:[\\/]", code) or ".." in re.sub(r"\.\.\.", "", code) or "os.chdir" in code:
            return "rejected: use relative paths inside the workspace only (no drive letters, no '..', no chdir)"
        return self.t_run_python(name, code, timeout_s)

    def b_download_papers(self, dois):
        block = {d.lower() for d in self.holdout.get("dois", [])}
        ok = [d for d in dois if d.lower() not in block]
        blocked = [d for d in dois if d.lower() in block]
        res = json.loads(self.t_download_papers(ok)) if ok else []
        if blocked:
            self.log({"holdout_blocked": blocked})
            res += [dict(doi=d, status="unavailable") for d in blocked]
        return json.dumps(res)

    def b_search_papers(self, query, title_terms, n, from_year):
        return self.f_search_papers(query, title_terms, n, from_year)

    def b_screen_papers(self, criteria):
        return self.f_screen_papers(criteria)

    def b_extract_papers(self, reaction, key_reactant, product, cofeed, scope):
        return self.f_extract_papers(reaction, key_reactant, product, cofeed, scope)

    # ---------------- records with a minimal reaction card (no plant parameters)
    @staticmethod
    def formula_mw(f):
        """Molar mass from a formula such as C3H8, C2H5OH, CO2, NH3 (generic data, not a modeling choice)."""
        A = dict(H=1.008, C=12.011, N=14.007, O=15.999, S=32.06, Cl=35.45, F=18.998, Ar=39.948, He=4.0026)
        tot = 0.0
        for el, n in re.findall(r"([A-Z][a-z]?)(\d*)", f):
            tot += A[el] * (int(n) if n else 1)
        return round(tot, 3)

    def _card_cfg(self, key, product, cofeed):
        names = {key, product} | ({cofeed} if cofeed and cofeed != "none" else set())
        species = {s: {"MW": self.formula_mw(s)} for s in names if s}
        return {"stoich": {"key": key, "product": product}, "species": species,
                "lab_feed": {"default_y_key": None, "default_ratio": ({cofeed: None} if cofeed and cofeed != "none" else {})}}

    def b_check_records(self, key, product, cofeed):
        self.card = (key, product, cofeed)
        rows, gates = chain.normalise(self.ws, self._card_cfg(key, product, cofeed))
        per = {}
        for r in rows:
            p = per.setdefault(r["paper"], dict(records=0, usable=0, miss={}))
            p["records"] += 1
            p["usable"] += bool(r["usable"])
            if not r["usable"]:
                for k, lab in (("T_K", "temperature"), ("X", "conversion"), ("S", "selectivity"), ("r", "rate or flow+mass")):
                    if not r[k]:
                        p["miss"][lab] = p["miss"].get(lab, 0) + 1
                        break
        out = [dict(paper=k, records=v["records"], usable=v["usable"], main_missing=max(v["miss"], key=v["miss"].get) if v["miss"] else "")
               for k, v in sorted(per.items())]
        return json.dumps(dict(papers=out, usable_records=sum(o["usable"] for o in out), gates=gates))

    # ---------------- model contract
    def _load_model(self):
        spec = importlib.util.spec_from_file_location(f"agent_model_{time.time_ns()}", self.ws / "model.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def _records(self):
        key, product, cofeed = getattr(self, "card", (None, None, None))
        rows, _ = chain.normalise(self.ws, self._card_cfg(key, product, cofeed))
        recs = []
        for r in rows:
            if r["usable"]:
                recs.append(dict(paper=r["paper"], idx=r["idx"], catalyst=r["catalyst"], T_K=r["T_K"], P_bar=r["P_bar"], X=r["X"],
                                 S=r["S"], r=r["r"], y_key=r["y_key"], y_cofeed=r["y_h2"], t_cycle_h=r["t_cycle_h"],
                                 components=json.loads(r["elements"]), location=r["location"], page=r.get("page")))
        return recs

    def b_check_model(self):
        checks, ref = {}, None
        try:
            m = self._load_model()
            ref = m.reference()
            key, product = m.REACTION["key"], m.REACTION["product"]
            stoich_min = m.REACTION["MW"][key] / m.REACTION["MW"][product]
        except Exception as e:  # noqa: BLE001
            return json.dumps(dict(passed=False, error=f"{type(e).__name__}: {str(e)[:400]}"))
        recs = self._records()
        fails = {k: [] for k in ("finite_positive", "parts_sum", "conversion_range", "stoichiometry", "monotone_selectivity",
                                 "monotone_activity", "deterministic", "exception")}
        for i, rec in enumerate([None] + recs):
            try:
                out = ref if rec is None else m.plant_cost(rec)
                c = out["cost_usd_per_t"]
                tag = "reference" if rec is None else f"{rec['paper']}#{rec['idx']}"
                if not (math.isfinite(c) and c > 0):
                    fails["finite_positive"].append(tag)
                if abs(sum(out["parts"].values()) - c) > 0.005 * abs(c):
                    fails["parts_sum"].append(tag)
                x = out["operating"]["per_pass_conversion"]
                if not (0 < x <= 1):
                    fails["conversion_range"].append(tag)
                if out["balances"]["key_feed_t_per_t"] < 0.99 * stoich_min:
                    fails["stoichiometry"].append(tag)
                for k in ("energy_GJ_per_t", "capex_usd", "capacity_t_per_y"):
                    v = out["balances"].get(k)
                    if v is None or not math.isfinite(v) or v < 0:
                        fails.setdefault("balances_fields", []).append(f"{tag}: {k}")
                if rec is not None and i <= 40:          # perturbation checks on the first 40 records (time)
                    if m.plant_cost(dict(rec, S=min(1.0, rec["S"] + 0.05)))["cost_usd_per_t"] > c * (1 + 1e-6):
                        fails["monotone_selectivity"].append(tag)
                    if m.plant_cost(dict(rec, r=rec["r"] * 2))["cost_usd_per_t"] > c * (1 + 1e-6):
                        fails["monotone_activity"].append(tag)
                    if abs(m.plant_cost(dict(rec))["cost_usd_per_t"] - c) > 1e-9 * c:
                        fails["deterministic"].append(tag)
            except Exception as e:  # noqa: BLE001
                fails["exception"].append(f"{'reference' if rec is None else rec['paper']}: {type(e).__name__}: {str(e)[:120]}")
        res = dict(passed=not any(fails.values()), records_tested=len(recs),
                   failures={k: v[:5] + ([f"... {len(v) - 5} more"] if len(v) > 5 else []) for k, v in fails.items() if v},
                   reference=dict(name=ref.get("name"), cost=ref.get("cost_usd_per_t"), parts=ref.get("parts"), operating=ref.get("operating")))
        (self.ws / "model_check.json").write_text(json.dumps(res, indent=1, default=str), encoding="utf-8")
        return json.dumps(res, default=str)

    # ---------------- analysis with the agent's model and the NCE metrics
    def b_run_analysis(self):
        import copy
        import pandas as pd
        m = self._load_model()
        recs = self._records()
        ref = m.reference()
        c_ref = ref["cost_usd_per_t"]
        rows = []
        for r in recs:
            o = m.plant_cost(r)
            rows.append(dict(r, cost=o["cost_usd_per_t"], **{"part_" + k: v for k, v in o["parts"].items()},
                             plant_T_K=o["operating"].get("T_K"), plant_P_bar=o["operating"].get("P_bar"),
                             per_pass=o["operating"].get("per_pass_conversion")))
        df = pd.DataFrame(rows)
        df.drop(columns=["components"]).to_csv(self.ws / "costs.csv", index=False)
        df["group"] = [f"{p} | {round(P, 1)} bar | y {round(y or 0, 3)}" for p, P, y in zip(df.paper, df.P_bar, df.y_key)]
        df["catkey"] = [re.sub(r"\s+", "", str(c).lower()) for c in df.catalyst]
        rank = {lab: nm.metrics(df.rename(columns={"r": "productivity", "X": "conversion", "S": "selectivity"}).assign(
                    cost=df.cost), group="group", catalyst="catkey", lab=lab, cost="cost", paper="paper")
                for lab in ("productivity", "conversion", "selectivity")}
        # one-at-a-time attribution: swap one property of the reference to the record's value (reference as a record)
        base = dict(ref["record"])          # the reference catalyst as a plant_cost input (contract)
        props = {"selectivity": ("S",), "activity": ("X", "r", "y_key", "y_cofeed", "P_bar"), "temperature": ("T_K",),
                 "stability": ("t_cycle_h",), "metal": ("components",)}
        attr = {k: 0.0 for k in props}
        c_base = m.plant_cost(base)["cost_usd_per_t"]
        for r in recs:
            for k, keys in props.items():
                x = copy.deepcopy(base)
                for kk in keys:
                    x[kk] = r[kk]
                try:
                    attr[k] += abs(m.plant_cost(x)["cost_usd_per_t"] - c_base)
                except Exception:  # noqa: BLE001
                    pass
        tot = sum(attr.values()) or 1
        el = {}
        for name, mod in (("+1 pt selectivity", dict(S=min(1.0, base["S"] + 0.01))), ("activity x2", dict(r=base["r"] * 2))):
            try:
                el[name] = m.plant_cost(dict(base, **mod))["cost_usd_per_t"] - c_base
            except Exception:  # noqa: BLE001
                pass
        best = df.loc[df.cost.idxmin()]
        s = dict(model_sha256=__import__("hashlib").sha256((self.ws / "model.py").read_bytes()).hexdigest()[:16],
                 n_usable=len(df), papers=int(df.paper.nunique()), reference=dict(name=ref.get("name"), cost=c_ref, parts=ref["parts"]),
                 reference_largest=max(ref["parts"], key=ref["parts"].get),
                 cheapest=dict(paper=best.paper, catalyst=best.catalyst, T_C=round(best.T_K - 273.15), cost=float(best.cost)),
                 below_reference=int((df.cost < c_ref).sum()), ranking=rank,
                 attribution_share={k: round(v / tot, 3) for k, v in attr.items()}, cost_change_at_reference=el)
        (self.ws / "analysis.json").write_text(json.dumps(s, indent=1, default=str), encoding="utf-8")
        return json.dumps(s, default=str)

    def finish_build(self):
        self._close_stage()
