"""Masked-database mode of the autonomous agent (runner.py --db pdh|ch4).

The literature records already extracted by the pipeline (../data/<rxn>_records.csv, usable set of analyze.load) are
given to the agent with paper codes instead of DOIs and with two fields masked: product selectivity and the
time-on-stream stability test. reveal() uncovers one (record, field) cell for one budget unit, as in the online
label-reveal experiments of the ICML line. The truth table (db/truth.json) stays with the harness.
"""
import csv
import json

METHOD_DB = """You are a research agent. Run, end to end and on your own, the analysis chain below for the reaction given by the user. Work only through the tools. Decide everything yourself; nobody will answer questions.

Goal: from a literature database of measured catalysts, find where the industrial bottleneck of this reaction lies, which catalyst a plant would choose, and whether the way papers rank catalysts (by conversion or productivity) agrees with what a plant would choose. Report the time and the cost of your own run at the end (read_file('ledger.json')).

The database (get_database) holds catalyst x condition records extracted from {n_papers} papers (paper codes only). Visible for every record: catalyst, composition (element, wt%), T, P, feed, lab conversion, and the lab rate at which the key reactant is converted (mol per kg catalyst per h, from the printed rate or from feed flow x conversion; product productivity = this rate x selectivity x molar mass of the product). Masked: 'selectivity' (product selectivity, fraction) and 'stability' (initial/final conversion and duration of a time-on-stream test, when the paper reported one). reveal(...) uncovers one field of one record for 1 unit of budget; the budget is {budget} units for {n_masked} masked cells. Unrevealed values stay unknown: spend the budget where it can change the plant decision and the bottleneck conclusion, and say how your conclusions depend on what you left masked. Do not look the papers or the catalysts up on the web; use web_search only for plant, process and market data.

The chain (the same thinking as the ammonia and methanol studies of this project):
1. Plant model: build a transparent plant cost model in USD per tonne of product for a world-scale plant: raw materials, energy, capital (annualised, scaled with throughput/recycle and reactor size), catalyst (inventory from productivity, metal prices, lifetime, precious-metal recovery), regeneration if relevant, by-product credits. Source every parameter with web_search (official statistics, open techno-economic papers, company filings) and keep a sources table; mark unsourced values as assumptions with a range. Let the plant optimise its free operating variable(s) (for example the per-pass conversion up to near equilibrium, trading recycle against catalyst amount). Move activity from lab to plant in a physically consistent way: a lab test at low conversion is limited by contact time and a plant can load more catalyst, so use a kinetic law (for example first-order approach to equilibrium with the lab feed and with the plant feed) rather than charging the plant the lab conversion. Selectivity keeps its lab value. Build the industrial reference catalyst/plant from published plant data and check the model against a published plant or TEA cost.
2. Decide what to reveal (you may reveal in several rounds, updating the model between rounds).
3. Analysis:
   a. Plant cost of every record you can cost (state how masked selectivity/stability were treated for the others).
   b. Paper ranking vs plant ranking: in each comparison group (same paper, same pressure and feed) compare the leader by each lab metric with the cheapest plant option; count disagreements, split into "other catalyst" vs "same catalyst at another temperature", and give the regret (extra plant cost of the lab choice).
   c. Bottleneck: cost breakdown of the reference plant; one-at-a-time attribution of each record's cost gap to the reference (selectivity, activity, temperature, stability, metal cost); cost change at the reference for +1 point selectivity, x2 activity, x10 stability and a small change in the main raw-material price. State which property (or which non-catalyst factor) carries the plant cost.
   d. Backward design: what a literature catalyst would need (selectivity, activity or price) to reach the industrial reference cost.
   e. One-at-a-time sensitivity of the conclusions to the uncertain parameters.
4. Report: write report.md in the workspace: reveal strategy and budget used; parameter table with sources; results a-e with numbers and denominators; the catalyst a plant would choose (record id) and the bottleneck conclusion; what the masked data could not support; time and cost of the run from ledger.json. Save your scripts and data. Then call finish.

Rules: never invent numbers or sources; if something cannot be found, say so and use a stated assumption with a range. Keep tool outputs small (print summaries, not whole tables). The workspace is your current directory; scripts you run start there. Budget: about {max_turns} tool turns; plan accordingly and finish with a complete report."""

DB_TOOLS = [
    {"type": "web_search"},
    {"type": "function", "name": "get_database", "strict": True,
     "description": "Write the visible database to db/visible.csv in the workspace (masked fields shown as MASKED) and return a summary.",
     "parameters": {"type": "object", "additionalProperties": False, "required": [], "properties": {}}},
    {"type": "function", "name": "reveal", "strict": True,
     "description": "Uncover masked fields; 1 budget unit per (record, field). Revealed values are appended to db/revealed.csv.",
     "parameters": {"type": "object", "additionalProperties": False, "required": ["requests"],
                    "properties": {"requests": {"type": "array", "items": {
                        "type": "object", "additionalProperties": False, "required": ["rec_id", "field"],
                        "properties": {"rec_id": {"type": "string"},
                                       "field": {"type": "string", "enum": ["selectivity", "stability"]}}}}}}},
]


class DBMixin:
    def setup_db(self, truth_path, key, budget_frac):
        self.db = json.loads(truth_path.read_text(encoding="utf-8"))[key]
        self.db_by_id = {r["rec_id"]: r for r in self.db}
        self.n_masked = 2 * len(self.db)
        self.budget = int(round(budget_frac * self.n_masked))
        self.spent = 0
        self.revealed = {}

    def t_get_database(self):
        rows = []
        for r in self.db:
            v = {k: r[k] for k in r if not k.startswith("_")}
            v["selectivity"] = self.revealed.get((r["rec_id"], "selectivity"), "MASKED")
            k2 = (r["rec_id"], "stability")
            v["stability"] = json.dumps(self.revealed[k2]) if k2 in self.revealed else "MASKED"
            rows.append(v)
        (self.ws / "db").mkdir(exist_ok=True)
        with open(self.ws / "db" / "visible.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, list(rows[0]))
            w.writeheader()
            w.writerows(rows)
        return json.dumps(dict(file="db/visible.csv", records=len(rows), papers=len({r["paper"] for r in rows}),
                               columns=list(rows[0]), budget_left=self.budget - self.spent))

    def t_reveal(self, requests):
        out = []
        (self.ws / "db").mkdir(exist_ok=True)
        for q in requests:
            key = (q["rec_id"], q["field"])
            rec = self.db_by_id.get(q["rec_id"])
            if rec is None:
                out.append(dict(q, error="unknown rec_id"))
                continue
            if key in self.revealed:
                out.append(dict(q, value=self.revealed[key], note="already revealed"))
                continue
            if self.spent >= self.budget:
                out.append(dict(q, error="budget exhausted"))
                continue
            v = rec["_selectivity"] if q["field"] == "selectivity" else rec["_stability"]
            self.revealed[key] = v
            self.spent += 1
            out.append(dict(q, value=v))
            path = self.ws / "db" / "revealed.csv"
            new = not path.exists()
            with open(path, "a", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                if new:
                    w.writerow(["rec_id", "field", "value"])
                w.writerow([q["rec_id"], q["field"], json.dumps(v)])
        self.write_ledger()
        return json.dumps(dict(results=out, spent=self.spent, budget_left=self.budget - self.spent))
