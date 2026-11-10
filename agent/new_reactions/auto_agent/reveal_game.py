"""REVEAL: budgeted decisions on the masked literature database, one fixed plant model for everyone.

Mapped from DISCOVER / DISCOVER-V2-STOP (docs/DISCOVER_V2_STOP_RESULTS_2026-09-26.md;
provenance/discover_v1/source_harness/discover/env.py stopping_status; tools/discover/v2_stop_analysis.py).

Database: the usable literature records of a reaction (db/truth.json). Each run shuffles the paper codes and the
record order (seeded), so nothing can be learned across runs from ids.
Visible: paper code, catalyst, composition, T, P, feed, lab conversion, reactant conversion rate.
Masked: selectivity and stability (time-on-stream test), two cells per record, 1 unit each.
Plant model: plant_framework.py + configs/<rxn>_ours.json (version and SHA-256 saved with every run).
Decision: one record = a catalyst at an operating condition.

Bounds: for a record, the cost lower bound takes selectivity 1 if masked and the best stability (no regeneration
penalty) if masked; a record is EXACT when its selectivity is revealed and its stability is revealed or cannot move
its cost (no regeneration in the plant).
Value of information of a masked cell, given the current knowledge (logged for every reveal):
  flip   = 1 if the cell's best case makes the record cheaper than the best exact record (the choice can change);
  ERR    = expected regret reduction E[max(0, J_best - J(cell))], selectivity drawn from the revealed selectivities
           of the same paper (>= 3) or uniform 0.5-1, stability from the revealed cycle times or log-uniform 1-1000 h.
Rule (S1 and S2 and S3):
  S1 an exact record exists;  S2 no non-exact record has a lower bound below the best exact cost;
  S3 the laboratory optimum (highest lab rate) is the best exact record, or it is exact (its backward design - the
     selectivity it would need to match the choice - is then a free fixed computation).
Arms: none (rule not shown or enforced), gate (after the rule first holds a reveal runs only if its flip value is 1;
rejected at 0 units; 3 consecutive rejections end the run), hard (the run ends at the first action after which the
rule holds; the choice is the best exact record).
Metrics: decision correct (chosen = optimum of the fully revealed database), regret %, units spent, units at which the
rule first held (armed), units after it (post-rule spend), rule at stop, tokens, turns.

  python reveal_game.py baselines
  python reveal_game.py agent <rxn> <budget_frac|inf> <arm> <seed> [--model gpt-5.5]
"""
from __future__ import annotations

import hashlib
import json
import math
import random
import statistics as st
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
NR = HERE.parent
sys.path.insert(0, str(NR))
sys.path.insert(0, str(NR.parent / "extraction"))
import analyze as an  # noqa: E402
import plant_framework as fw  # noqa: E402

OUT = HERE / "reveal"
T_BEST = 1e5


class Env:
    def __init__(self, rx, budget_frac, seed, arm="none"):
        self.rx, self.arm, self.seed = rx, arm, seed
        self.cfg = fw.load(rx, "ours")
        cfg_path = NR / "configs" / f"{rx}_ours.json"
        self.model_id = dict(framework=fw.FRAMEWORK_VERSION, config=cfg_path.name,
                             config_sha256=hashlib.sha256(cfg_path.read_bytes()).hexdigest()[:16])
        truth = json.loads((HERE / "db" / "truth.json").read_text(encoding="utf-8"))[rx]
        rows = {(r["paper"], int(r["idx"])): r for r in an.load(rx)}
        rng = random.Random(seed)
        papers = sorted({t["paper"] for t in truth})
        codes = [f"P{i + 1:02d}" for i in range(len(papers))]
        rng.shuffle(codes)
        pmap = dict(zip(papers, codes))
        order = list(range(len(truth)))
        rng.shuffle(order)
        self.recs, self.idmap = {}, {}
        for k, j in enumerate(order):
            t = truth[j]
            rid = f"R{k + 1:03d}"
            base = rows[(t["_true_paper"], int(t["_idx"]))]["rec"]
            rec = dict(base, xeq_lab=fw.lab_xeq(self.cfg, base))
            self.recs[rid] = dict(rid=rid, paper=pmap[t["paper"]], catalyst=t["catalyst"], composition=t["composition_wt_pct"],
                                  T_C=t["T_C"], P_bar=t["P_bar"], lab_conversion=t["lab_conversion"],
                                  lab_rate=t["lab_reactant_conversion_rate_mol_per_kg_h"], S=t["_selectivity"],
                                  t_cycle=base.get("t_cycle_h"), stab=t["_stability"], rec=rec, true_id=t["rec_id"])
            self.idmap[rid] = t["rec_id"]
        self.regen = self.cfg["regeneration"]["enabled"]
        self.budget = None if budget_frac == "inf" else max(1, int(round(float(budget_frac) * 2 * len(self.recs))))
        self.rev = {}                     # (rid, field) -> True
        self.spent, self.armed_at, self.backward_done, self.consec_rejects = 0, None, set(), 0
        self.log = []
        self._cache = {}
        self.truth_cost = {r: self.cost(r, self.recs[r]["S"], self.recs[r]["t_cycle"]) for r in self.recs}
        self.opt = min(self.truth_cost, key=self.truth_cost.get)
        self.lab_best = max(self.recs, key=lambda r: self.recs[r]["lab_rate"])
        self._arm_check()

    # ---------------- plant model (fixed)
    def cost(self, rid, S, t_cycle):
        key = (rid, round(S, 6), None if t_cycle is None else round(t_cycle, 3))
        if key not in self._cache:
            r = self.recs[rid]
            rec = dict(r["rec"], S=S, r=r["rec"]["r"] / r["rec"]["S"] * S, t_cycle_h=t_cycle)
            self._cache[key] = fw.cost(self.cfg, rec)
        return self._cache[key]

    def known(self, rid, field):
        return (rid, field) in self.rev

    def stab_matters(self):
        return self.regen

    def exact(self, rid):
        return self.known(rid, "selectivity") and (self.known(rid, "stability") or not self.stab_matters())

    def bounds(self, rid):
        r = self.recs[rid]
        S = r["S"] if self.known(rid, "selectivity") else 1.0
        t_lb = r["t_cycle"] if (self.known(rid, "stability") or not self.stab_matters()) else T_BEST
        lb = self.cost(rid, S, t_lb)
        if self.exact(rid):
            return lb, lb
        return lb, None

    def best_exact(self):
        ex = [(self.truth_cost[r], r) for r in self.recs if self.exact(r)]
        return min(ex) if ex else (math.inf, None)

    # ---------------- rule
    def s123(self):
        bc, br = self.best_exact()
        s1 = br is not None
        s2 = s1 and all(self.bounds(r)[0] >= bc - 1e-9 for r in self.recs if not self.exact(r))
        s3 = s2 and (self.lab_best == br or self.exact(self.lab_best))   # backward of the lab optimum is a free, fixed computation
        return s1, s2, s3

    def rule(self):
        return all(self.s123())

    def _arm_check(self):
        if self.armed_at is None and self.rule():
            self.armed_at = self.spent

    # ---------------- value of information
    def voi(self, rid, field):
        bc, _ = self.best_exact()
        r = self.recs[rid]
        S_now = r["S"] if self.known(rid, "selectivity") else None
        t_now = r["t_cycle"] if self.known(rid, "stability") else None
        if field == "selectivity":
            best_case = self.cost(rid, 1.0, t_now if t_now is not None else (T_BEST if self.stab_matters() else r["t_cycle"]))
            same = [self.recs[x]["S"] for x in self.recs if self.recs[x]["paper"] == r["paper"] and self.known(x, "selectivity")]
            grid = sorted(same) if len(same) >= 3 else [0.5 + 0.05 * i for i in range(11)]
            vals = [self.cost(rid, s, t_now if t_now is not None else (T_BEST if self.stab_matters() else r["t_cycle"])) for s in grid]
        else:
            if not self.stab_matters():
                return dict(flip=0, err=0.0)
            S_use = S_now if S_now is not None else 1.0
            best_case = self.cost(rid, S_use, T_BEST)
            ts = [self.recs[x]["t_cycle"] for x in self.recs if self.known(x, "stability") and self.recs[x]["t_cycle"]]
            grid = sorted(ts) if len(ts) >= 3 else [10 ** (3 * i / 10) for i in range(11)]
            vals = [self.cost(rid, S_use, t) for t in grid]
        flip = int(best_case < bc - 1e-9)
        err = 0.0 if math.isinf(bc) else sum(max(0.0, bc - v) for v in vals) / len(vals)
        return dict(flip=flip, err=round(err, 3))

    # ---------------- actions
    def reveal(self, cells):
        out = []
        for c in cells:
            rid, field = c["rec_id"], c["field"]
            if rid not in self.recs:
                out.append(dict(c, error="unknown id")); continue
            if self.known(rid, field):
                out.append(dict(c, note="already revealed")); continue
            if self.budget is not None and self.spent >= self.budget:
                out.append(dict(c, error="budget exhausted")); continue
            if self.arm == "hard" and self.rule():
                out.append(dict(c, error="not executed: the run ended when rule R held (hard stop)"))
                continue
            v = self.voi(rid, field)
            if self.arm == "gate" and self.armed_at is not None and v["flip"] == 0:
                self.consec_rejects += 1
                out.append(dict(c, error="rejected by the gate: this cell cannot change the choice (0 units)"))
                self.log.append(dict(step=len(self.log) + 1, action="reject", rec_id=rid, field=field, spent=self.spent, **v))
                continue
            self.consec_rejects = 0
            self.rev[(rid, field)] = True
            self.spent += 1
            r = self.recs[rid]
            val = r["S"] if field == "selectivity" else (r["stab"] if any(r["stab"].values()) else "not reported")
            bc, br = self.best_exact()
            self.log.append(dict(step=len(self.log) + 1, action="reveal", rec_id=rid, true_id=self.idmap[rid], field=field,
                                 spent=self.spent, choice_now=br, choice_cost=None if br is None else round(bc, 3),
                                 rule=self.rule(), **v))
            res = dict(c, value=val)
            lb, ex = self.bounds(rid)
            res.update(plant_cost=round(ex, 2) if ex is not None else None, cost_lower_bound=round(lb, 2))
            out.append(res)
            self._arm_check()
        return out

    def backward(self, rid):
        """Selectivity this record would need to match the best exact record (with its known stability)."""
        bc, br = self.best_exact()
        if br is None or rid not in self.recs:
            return dict(error="no exact record yet" if br is None else "unknown id")
        r = self.recs[rid]
        t = r["t_cycle"] if (self.known(rid, "stability") or not self.stab_matters()) else T_BEST
        self.backward_done.add(rid)
        lo, hi = 0.05, 1.0
        if self.cost(rid, hi, t) > bc:
            res = dict(rec_id=rid, selectivity_needed="above 1 (cannot match)")
        else:
            for _ in range(40):
                mid = (lo + hi) / 2
                lo, hi = (mid, hi) if self.cost(rid, mid, t) > bc else (lo, mid)
            res = dict(rec_id=rid, selectivity_needed=round(hi, 4))
        self._arm_check()
        return res

    def view(self, rid):
        r = self.recs[rid]
        lb, ex = self.bounds(rid)
        v = dict(rec_id=rid, paper=r["paper"], catalyst=r["catalyst"][:36], T_C=r["T_C"], P_bar=r["P_bar"],
                 lab_conversion=r["lab_conversion"], lab_rate=r["lab_rate"],
                 selectivity=r["S"] if self.known(rid, "selectivity") else "MASKED",
                 stability=("revealed" if self.known(rid, "stability") else ("no effect" if not self.stab_matters() else "MASKED")))
        v.update(plant_cost=round(ex, 2)) if ex is not None else v.update(cost_lower_bound=round(lb, 2))
        return v

    def score(self, chosen):
        o = self.truth_cost[self.opt]
        c = self.truth_cost.get(chosen)
        return dict(chosen=chosen, chosen_true_id=self.idmap.get(chosen), optimum=self.opt, optimum_true_id=self.idmap[self.opt],
                    correct=chosen == self.opt, regret_pct=None if c is None else round(100 * (c - o) / o, 4),
                    spent=self.spent, budget=self.budget, armed_at=self.armed_at,
                    post_rule=None if self.armed_at is None else self.spent - self.armed_at, rule_at_stop=self.rule(),
                    chosen_exact=chosen in self.recs and self.exact(chosen))


# ------------------------------------------------------------------ deterministic baselines (same model)
def pick(env):
    return env.best_exact()[1] or min(env.recs, key=lambda r: env.bounds(r)[0])


def policy_bnb(env, rng=None):
    while not env.rule():
        if env.budget is not None and env.spent >= env.budget:
            break
        open_ = sorted((env.bounds(r)[0], r) for r in env.recs if not env.exact(r))
        bc, br = env.best_exact()
        if open_ and open_[0][0] < bc - 1e-9:
            rid = open_[0][1]
            field = "selectivity" if not env.known(rid, "selectivity") else "stability"
            env.reveal([dict(rec_id=rid, field=field)])
            continue
        lb = env.lab_best
        if not env.known(lb, "selectivity"):
            env.reveal([dict(rec_id=lb, field="selectivity")])
        elif env.stab_matters() and not env.known(lb, "stability"):
            env.reveal([dict(rec_id=lb, field="stability")])
        else:
            env.backward(lb)
    return pick(env)


def policy_rate_greedy(env, rng=None):
    for r in sorted(env.recs, key=lambda r: -env.recs[r]["lab_rate"]):
        for f in ("selectivity", "stability"):
            if env.budget is not None and env.spent >= env.budget:
                return pick(env)
            env.reveal([dict(rec_id=r, field=f)])
    return pick(env)


def policy_rate_pick(env, rng=None):
    return env.lab_best


def policy_random(env, rng):
    cells = [dict(rec_id=r, field=f) for r in env.recs for f in ("selectivity", "stability")]
    rng.shuffle(cells)
    for c in cells:
        if env.budget is not None and env.spent >= env.budget:
            break
        env.reveal([c])
    return pick(env)


def baselines():
    OUT.mkdir(exist_ok=True)
    rows = []
    for rx in ("pdh", "ch4"):
        for frac in ("0.1", "0.3", "inf"):
            for name, pol, reps in (("bnb", policy_bnb, 5), ("rate_greedy", policy_rate_greedy, 5),
                                    ("rate_pick", policy_rate_pick, 5), ("random", policy_random, 50)):
                res = []
                for k in range(reps):
                    env = Env(rx, frac, seed=1000 + k)
                    res.append(env.score(pol(env, random.Random(k))))
                rows.append(dict(rxn=rx, budget=frac, cells=2 * len(env.recs), budget_units=res[0]["budget"], policy=name,
                                 n=reps, correct=sum(r["correct"] for r in res),
                                 median_regret_pct=st.median(r["regret_pct"] for r in res),
                                 max_regret_pct=max(r["regret_pct"] for r in res), median_spent=st.median(r["spent"] for r in res),
                                 median_armed=st.median([r["armed_at"] for r in res if r["armed_at"] is not None] or [-1]),
                                 rule_at_stop=sum(r["rule_at_stop"] for r in res), model=env.model_id))
                print({k: v for k, v in rows[-1].items() if k != "model"}, flush=True)
    (OUT / "baselines.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")


# ------------------------------------------------------------------ the agent: decisions only
PROMPT = """You choose the catalyst and operating condition for an industrial {reaction} plant from a database of {n} literature records (catalyst x condition) from {p} papers. A fixed plant model (USD per tonne of product) is built; you do not build models. Each record shows its catalyst, conditions, lab conversion and lab rate (the lab ranking a paper would use). Its selectivity and its stability test are MASKED; reveal(...) uncovers one cell for 1 unit. A record's plant cost is exact when its selectivity is known and its stability is known or has no effect; otherwise the tools give the cost lower bound (best case of the masked cells). Budget: {budget}. Reference industrial plant: {ref:.1f} USD/t. Reply only with tool calls; keep any text to one line.{rule}

Decide what to reveal and when to stop, then call choose(rec_id) with the record a plant should use."""
RULE_TEXT = {
    "none": "",
    "gate": ("\n\nStop rule R = S1 and S2 and S3. S1: an exactly costed record exists. S2: no non-exact record has a lower bound below the "
             "best exact cost. S3: the highest-lab-rate record (the paper ranking's choice) is the best exact record, or it is exact. "
             "After R first holds, a reveal is executed only if it can change the choice; other reveals are rejected (0 units; three "
             "rejections in a row end the run)."),
    "hard": ("\n\nStop rule R = S1 and S2 and S3. S1: an exactly costed record exists. S2: no non-exact record has a lower bound below the "
             "best exact cost. S3: the highest-lab-rate record (the paper ranking's choice) is the best exact record, or it is exact. "
             "The run ends as soon as R holds, with the best exact record as the choice."),
}
REACTION = {"pdh": "non-oxidative propane dehydrogenation (propylene)", "ch4": "CO2 methanation (synthetic natural gas)"}
TOOLS = [
    {"type": "function", "name": "overview", "strict": True,
     "description": "Budget, spend, best exact record, number of records whose lower bound is below it, and the k most promising records.",
     "parameters": {"type": "object", "additionalProperties": False, "required": ["k"], "properties": {"k": {"type": "integer"}}}},
    {"type": "function", "name": "list_records", "strict": True,
     "description": "k records (max 20) ordered by 'cost' (exact or lower bound), 'lab_rate' or 'lab_conversion', from offset.",
     "parameters": {"type": "object", "additionalProperties": False, "required": ["order", "k", "offset"],
                    "properties": {"order": {"type": "string", "enum": ["cost", "lab_rate", "lab_conversion"]},
                                   "k": {"type": "integer"}, "offset": {"type": "integer"}}}},
    {"type": "function", "name": "reveal", "strict": True,
     "description": "Reveal cells (1 unit each).",
     "parameters": {"type": "object", "additionalProperties": False, "required": ["cells"],
                    "properties": {"cells": {"type": "array", "items": {"type": "object", "additionalProperties": False,
                                   "required": ["rec_id", "field"],
                                   "properties": {"rec_id": {"type": "string"},
                                                  "field": {"type": "string", "enum": ["selectivity", "stability"]}}}}}}},
    {"type": "function", "name": "backward", "strict": True,
     "description": "Selectivity a record would need to match the best exact record (free).",
     "parameters": {"type": "object", "additionalProperties": False, "required": ["rec_id"], "properties": {"rec_id": {"type": "string"}}}},
    {"type": "function", "name": "choose", "strict": True,
     "description": "Final answer; ends the run.",
     "parameters": {"type": "object", "additionalProperties": False, "required": ["rec_id"], "properties": {"rec_id": {"type": "string"}}}},
]


def t_overview(env, k):
    bc, br = env.best_exact()
    open_ = sorted((env.bounds(r)[0], r) for r in env.recs if not env.exact(r))
    below = sum(1 for lb, _ in open_ if lb < bc - 1e-9)
    top = sorted(env.recs, key=lambda r: env.bounds(r)[0])[:max(1, min(k, 15))]
    d = dict(budget=env.budget if env.budget is not None else "unlimited", spent=env.spent,
             best_exact=None if br is None else dict(rec_id=br, plant_cost=round(bc, 2)), non_exact_below_best=below,
             top=[env.view(r) for r in top])
    if env.arm != "none":
        s1, s2, s3 = env.s123()
        d["rule"] = dict(S1=s1, S2=s2, S3=s3)
    return d


def t_list(env, order, k, offset):
    key = {"cost": lambda r: env.bounds(r)[0], "lab_rate": lambda r: -env.recs[r]["lab_rate"],
           "lab_conversion": lambda r: -env.recs[r]["lab_conversion"]}[order]
    rs = sorted(env.recs, key=key)[max(0, offset):max(0, offset) + max(1, min(k, 20))]
    return [env.view(r) for r in rs]


def run_agent(rx, frac, arm, seed, model="gpt-5.5", max_turns=30):
    import llm_route
    env = Env(rx, frac, seed, arm)
    router = llm_route.Router(model)          # API-YES first, then the advisor key
    instr = PROMPT.format(reaction=REACTION[rx], n=len(env.recs), p=len({r["paper"] for r in env.recs.values()}),
                          budget=f"{env.budget} units" if env.budget is not None else "unlimited", ref=fw.cost(env.cfg, fw.reference_record(env.cfg)),
                          rule=RULE_TEXT[arm])
    items = [{"role": "user", "content": "Start."}]
    tok_in = tok_out = turns = 0
    chosen, ended_by = None, None
    t0 = time.time()
    while turns < max_turns and chosen is None:
        turns += 1

        def call(client):
            out, final = [], None
            for ev in client.responses.create(model=model, instructions=instr, input=items, tools=TOOLS, store=False, stream=True,
                                              include=["reasoning.encrypted_content"], reasoning={"effort": "medium"}):
                if ev.type == "response.output_item.done":
                    out.append(ev.item)
                elif ev.type in ("response.completed", "response.incomplete", "response.failed"):
                    final = ev.response
            if final is None:
                raise RuntimeError("no final response")
            return out, final
        out, final = router.call(call)
        tok_in += final.usage.input_tokens
        tok_out += final.usage.output_tokens
        calls = []
        for o in out:
            d = o.model_dump(exclude_none=True)
            if o.type == "function_call":
                d.pop("status", None)
                calls.append(o)
            items.append(d)
        if not calls:
            items.append({"role": "user", "content": "Use the tools; finish with choose."})
            continue
        for c in calls:
            a = json.loads(c.arguments or "{}")
            if c.name == "overview":
                res = t_overview(env, a["k"])
            elif c.name == "list_records":
                res = t_list(env, a["order"], a["k"], a["offset"])
            elif c.name == "reveal":
                res = dict(results=env.reveal(a["cells"]), spent=env.spent)
            elif c.name == "backward":
                res = env.backward(a["rec_id"])
            else:
                chosen, ended_by = a["rec_id"], "choose"
                res = "ok"
            items.append({"type": "function_call_output", "call_id": c.call_id, "output": json.dumps(res, default=str)})
            if arm == "hard" and env.rule() and chosen is None:
                chosen, ended_by = env.best_exact()[1], "hard stop"
            if arm == "gate" and env.consec_rejects >= 3 and chosen is None:
                chosen, ended_by = pick(env), "three rejections"
            if chosen:
                break
    if chosen is None:
        chosen, ended_by = pick(env), "turn limit"
    sc = env.score(chosen)
    rec = dict(rxn=rx, budget_frac=frac, arm=arm, seed=seed, model=model, route=router.client._route, ended_by=ended_by, **sc,
               turns=turns, tokens_in=tok_in, tokens_out=tok_out, tokens=tok_in + tok_out, seconds=round(time.time() - t0, 1),
               plant_model=env.model_id, timestamp=datetime.now().isoformat(timespec="seconds"))
    d = OUT / "runs"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{rx}_{frac}_{arm}_{model}_{seed}.json").write_text(json.dumps(dict(result=rec, steps=env.log), indent=1, default=str),
                                                              encoding="utf-8")
    with open(OUT / "agent_runs.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, default=str) + "\n")
    print(json.dumps({k: rec[k] for k in ("rxn", "budget_frac", "arm", "seed", "model", "correct", "regret_pct", "spent", "armed_at",
                                          "post_rule", "turns", "tokens", "ended_by")}, default=str), flush=True)
    return rec


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "baselines":
        baselines()
    elif cmd == "agent":
        model = sys.argv[sys.argv.index("--model") + 1] if "--model" in sys.argv else "gpt-5.5"
        run_agent(sys.argv[2], sys.argv[3], sys.argv[4], int(sys.argv[5]), model)
