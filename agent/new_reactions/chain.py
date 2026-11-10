"""The analysis chain as reusable functions for any reaction configured for plant_framework.py.

Stages (all deterministic except extract(), which reads each paper with one LLM call):
  extract     standard record schema for <key reactant> -> <product>, Docling text + performance figures
  normalise   units, composition by element, productivity (printed rate or feed flow x X x S, flagged),
              first-order deactivation, physical gates (rate > 50 kg/kg/h = unit error; X, S in (0, 1])
  verify      every value marked printed must appear as a number in the paper (Docling text or PDF text layer)
  analyse     plant cost of every usable record; within-paper ranking (productivity, conversion, selectivity
              leader vs cheapest); one-at-a-time attribution to the reference; elasticities; selectivity needed to
              reach the reference cost; one-at-a-time sensitivity over the config's 'uncertain' list
Used by the autonomous agent (auto_agent/runner.py) as tools and by the hand-built run for the model comparison.
"""
from __future__ import annotations

import base64
import concurrent.futures as cf
import copy
import csv
import json
import math
import re
import statistics as st
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from scipy.optimize import brentq

import normalize as nz
import plant_framework as fw

NUM = {"type": "object", "additionalProperties": False, "required": ["value", "unit", "qualifier"],
       "properties": {"value": {"type": ["number", "null"]}, "unit": {"type": ["string", "null"]},
                      "qualifier": {"type": "string", "enum": ["=", "~", "<", ">", "missing"]}}}
RATE_BASIS = {"type": "string", "enum": ["per_g_catalyst", "per_g_metal", "per_site", "per_volume", "unknown"]}
FIELDS = {
    "entry_label": {"type": "string"}, "catalyst_name": {"type": "string"},
    "components": {"type": "array", "items": {"type": "object", "additionalProperties": False,
                   "required": ["component", "role", "loading_wt_pct"],
                   "properties": {"component": {"type": "string"},
                                  "role": {"type": "string", "enum": ["active_metal", "active_oxide", "promoter", "support"]},
                                  "loading_wt_pct": {"type": ["number", "null"]}}}},
    "temperature": NUM, "pressure": NUM, "feed_composition": {"type": ["string", "null"]},
    "key_reactant_fraction": NUM, "cofeed_ratio": NUM,
    "space_velocity": NUM,
    "space_velocity_basis": {"type": "string", "enum": ["per_mass_catalyst", "per_volume_catalyst", "per_mass_metal", "unknown"]},
    "catalyst_mass": NUM, "total_flow": NUM, "time_on_stream": NUM,
    "key_conversion": NUM, "product_selectivity": NUM, "product_yield": NUM, "product_rate": NUM,
    "product_rate_basis": RATE_BASIS,
    "stability_initial_conversion": NUM, "stability_final_conversion": NUM, "stability_duration": NUM,
    "data_source_type": {"type": "string", "enum": ["table", "text", "figure"]},
    "location": {"type": "string"}, "page": {"type": ["integer", "null"]},
}
SCHEMA = {"type": "object", "additionalProperties": False, "required": ["records", "notes"],
          "properties": {"records": {"type": "array", "items": {"type": "object", "additionalProperties": False,
                                                               "required": list(FIELDS), "properties": FIELDS}},
                         "notes": {"type": "string"}}}
PERF = ("conversion", "selectivity", "yield", "rate", "activity", "stability", "time on stream", "performance",
        "productivity", "space-time", "tof")

EXTRACT_PROMPT = """You extract experimental catalyst-performance data for {reaction} from one research paper, for a plant cost model.
The paper is a Docling parse (reading-order text with '=== PAGE n ===' markers, tables as Markdown under '[TABLE k]'), followed by images of its performance figures.
Key reactant: {key}. Product: {product}. Co-feed whose ratio to the key reactant matters: {cofeed}.
{scope}
One record per catalyst x reaction-condition entry measured in THIS paper (each catalyst at each temperature / pressure / feed / space velocity / time-on-stream point).
- key_conversion = conversion of {key}; product_selectivity = selectivity to {product}; product_rate = formation rate of {product} (or STY / productivity) exactly as printed, with unit and basis.
- key_reactant_fraction = mole/volume fraction of {key} in the feed when stated or computable from stated flows; cofeed_ratio = moles of {cofeed} per mole of {key} in the feed.
- Copy numbers exactly as printed in the paper's own unit (apply power-of-ten multipliers from headers/axis labels); null + qualifier 'missing' when absent; '=' printed, '~' read from a plot, '<'/'>' bounds. A condition stated once for a table/figure/series applies to all its entries (say where in location).
- Stability tests: one record per run with initial and final conversion and duration; main fields carry the initial values.
- components: active metals/oxides, promoters, support, with wt% only when stated in wt%.
- Never compute or guess; a wrong number is worse than a null."""


def slug(s):
    return re.sub(r"[^A-Za-z0-9]+", "_", s)[:60]


# ------------------------------------------------------------------ extraction
def extract(ws, client_factory, model, reaction, key, product, cofeed, scope, stems=None, workers=6,
            usage_csv=None, effort="medium"):
    """Extract every ocr/<stem>.md of the workspace not yet in extracted/ (or the given stems), in parallel."""
    ocr = Path(ws) / "ocr"
    out = Path(ws) / "extracted"
    out.mkdir(exist_ok=True)
    mds = [p for p in sorted(ocr.glob("*.md")) if (stems is None or p.stem in stems) and not (out / f"{p.stem}.json").exists()]
    system = EXTRACT_PROMPT.format(reaction=reaction, key=key, product=product, cofeed=cofeed or "none", scope=scope)

    def one(md):
        figs = json.loads((md.parent / (md.stem + "_figs.json")).read_text(encoding="utf-8"))
        chosen = [f for f in figs if f["caption"] and any(w in f["caption"].lower() for w in PERF)][:8]
        content = [{"type": "input_text", "text": md.read_text(encoding="utf-8")}]
        for f in chosen:
            p = md.parent / (md.stem + "_figs") / f["file"]
            if p.exists():
                content.append({"type": "input_text", "text": f"[Image: page {f['page']}] {f['caption'][:500]}"})
                content.append({"type": "input_image", "detail": "high",
                                "image_url": "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode()})
        client = client_factory()
        t0 = time.time()
        for attempt in range(3):
            try:
                pieces, final = [], None
                for ev in client.responses.create(model=model, instructions=system, input=[{"role": "user", "content": content}],
                                                  text={"format": {"type": "json_schema", "name": "records", "strict": True, "schema": SCHEMA}},
                                                  reasoning={"effort": effort}, store=False, stream=True):
                    if ev.type == "response.output_text.delta":
                        pieces.append(ev.delta)
                    elif ev.type in ("response.completed", "response.incomplete"):
                        final = ev.response
                if final is None:
                    raise RuntimeError("no final response")
                data = json.loads("".join(pieces))
                break
            except Exception as e:  # noqa: BLE001
                err = f"{type(e).__name__}: {str(e)[:200]}"
                time.sleep(10 * (attempt + 1))
        else:
            return dict(paper=md.stem, error=err)
        u = final.usage
        data["_meta"] = dict(model=model, images=len(chosen), tokens_in=u.input_tokens, tokens_out=u.output_tokens,
                             seconds=round(time.time() - t0, 1))
        (out / f"{md.stem}.json").write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
        row = dict(timestamp=datetime.now().isoformat(timespec="seconds"), paper=md.stem, model=model, images=len(chosen),
                   prompt_tokens=u.input_tokens, completion_tokens=u.output_tokens, n_records=len(data["records"]),
                   seconds=round(time.time() - t0, 1))
        if usage_csv:
            new = not Path(usage_csv).exists()
            with open(usage_csv, "a", newline="", encoding="utf-8") as fh:
                w = csv.DictWriter(fh, list(row))
                if new:
                    w.writeheader()
                w.writerow(row)
        return row

    with cf.ThreadPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(one, mds))


# ------------------------------------------------------------------ normalisation
def normalise(ws, cfg):
    key, product = cfg["stoich"]["key"], cfg["stoich"]["product"]
    nz.MW.update({s: v["MW"] for s, v in cfg["species"].items()})
    cofeed = next(iter(cfg["lab_feed"]["default_ratio"]), None)
    rows, gates = [], defaultdict(int)
    for f in sorted((Path(ws) / "extracted").glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        for i, x in enumerate(d.get("records", [])):
            els = nz.elements(x["components"])
            act = [e for e in els if e[2] in ("active_metal", "active_oxide")]
            metal_wt = sum(e[1] for e in act if e[1]) if act else None
            T = nz.temp_K(x["temperature"])
            P = nz.pres_bar(x["pressure"]) or 1.01325
            X, S, Y = nz.frac(x["key_conversion"]), nz.frac(x["product_selectivity"]), nz.frac(x["product_yield"])
            if X is None and Y is not None and S:
                X = Y / S
            if S is None and Y is not None and X:
                S = Y / X
            y = nz.frac(x["key_reactant_fraction"]) if nz.num(x["key_reactant_fraction"]) else nz.feed_fraction(x["feed_composition"], key)
            ff = nz.feed_flows(x["feed_composition"])
            if not y and ff.get(key) and len(ff) > 1:
                y = ff[key] / sum(ff.values())
            ratio = nz.num(x["cofeed_ratio"])
            y_co = (ratio * y) if (ratio is not None and y) else (nz.feed_fraction(x["feed_composition"], cofeed) if cofeed else None)
            r = nz.rate_kg_per_kg_h(x["product_rate"], x["product_rate_basis"], product, metal_wt) or None
            r_src = "printed" if r else None
            if r and r > nz.R_MAX_PRINTED:
                gates["printed rate > 50 kg/kg/h (unit error)"] += 1
                r, r_src = None, None
            if r is None and X and S and y:
                m, fl = nz.mass_g(x["catalyst_mass"]), nz.flow_ml_min(x["total_flow"])
                if not fl and len(ff) > 1:
                    fl = sum(ff.values())
                sv, svu = nz.num(x["space_velocity"]), (x["space_velocity"].get("unit") or "").lower()
                mol = None
                if fl and m:
                    mol, r_src = fl * y * 60 / 22414 / m, "derived"
                elif sv and ("ml" in svu or "l" in svu) and x["space_velocity_basis"] == "per_mass_catalyst":
                    mol, r_src = sv * (1000 if "ml" not in svu else 1) * y / 22414, "derived"
                elif sv and x["space_velocity_basis"] == "per_mass_catalyst" and "h" in svu and "l" not in svu:
                    mol, r_src = sv / nz.MW[key], "derived"          # WHSV on the key-reactant mass
                elif sv and x["space_velocity_basis"] == "per_volume_catalyst" and "h" in svu and "g" not in svu:
                    mol, r_src = sv * y / 22.414 / nz.RHO_BED_KG_L / 1000, "derived_rho"
                if mol:
                    r = mol * X * S * nz.MW[product]
            X0, Xf, td = nz.frac(x["stability_initial_conversion"]), nz.frac(x["stability_final_conversion"]), nz.hours(x["stability_duration"])
            kd = tcyc = None
            if X0 and Xf and td and 0 < Xf < 1 and 0 < X0 < 1:
                kd = max((math.log((1 - Xf) / Xf) - math.log((1 - X0) / X0)) / td, 1e-6)
                tcyc = (math.log((1 - 0.9 * X0) / (0.9 * X0)) - math.log((1 - X0) / X0)) / kd
            ok = bool(T and X and S and r and 0 < X <= 1 and 0 < S <= 1)
            if X and X > 1:
                gates["conversion > 1"] += 1
            if S and S > 1:
                gates["selectivity > 1"] += 1
            rows.append(dict(paper=f.stem, idx=i, catalyst=x["catalyst_name"], elements=json.dumps([[e[0], e[1]] for e in els]),
                             T_K=T, P_bar=P, y_key=y, y_h2=y_co, X=X, S=S, r=r, r_src=r_src, t_cycle_h=tcyc, kd_h=kd,
                             X0=X0, Xf=Xf, stab_h=td, source=x["data_source_type"], location=x["location"], usable=ok))
    with open(Path(ws) / "records.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    return rows, dict(gates)


def verify(ws):
    import pypdfium2 as pdfium
    fields = ("temperature", "key_conversion", "product_selectivity", "product_yield", "product_rate", "space_velocity",
              "stability_initial_conversion", "stability_final_conversion")
    printed = found = plot = 0
    for f in sorted((Path(ws) / "extracted").glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        md = (Path(ws) / "ocr" / f"{f.stem}.md").read_text(encoding="utf-8")
        pdfp = next((p for p in (Path(ws) / "pdf").glob("*.pdf") if p.stem[:60] == f.stem), None)
        raw = ""
        if pdfp:
            doc = pdfium.PdfDocument(str(pdfp))
            raw = " ".join(doc[i].get_textpage().get_text_range() for i in range(len(doc)))
            doc.close()
        pool = {float(m) for m in re.findall(r"\d+(?:\.\d+)?", (md + " " + raw).replace(",", ""))}
        for r in d.get("records", []):
            for k in fields:
                v = r[k]
                if v["value"] is None:
                    continue
                if v["qualifier"] == "~":
                    plot += 1
                    continue
                if v["qualifier"] == "missing":
                    continue
                x = abs(float(v["value"]))
                cands = {x, round(x * 100, 6), round(x / 100, 6), round(x * 1e3, 6), round(x / 1e3, 6), round(x - 273.15, 2), round(x + 273.15, 2)}
                if x:
                    e = int(f"{x:e}".split("e")[1])
                    cands |= {round(x / 10 ** e, 6), round(x / 10 ** (e - 2), 6)}
                printed += 1
                found += any(abs(c - p) <= 1e-6 * max(1, p) for c in cands for p in pool)
    return dict(printed=printed, found=found, plot_readings=plot, traceable=round(found / max(printed, 1), 3))


# ------------------------------------------------------------------ analysis
def _recs(rows):
    out = []
    for r in rows:
        if not r["usable"]:
            continue
        comps = [dict(element=e, wt_pct=w) for e, w in json.loads(r["elements"])]
        out.append(dict(r, rec=dict(T_K=r["T_K"], X=r["X"], S=r["S"], r=r["r"], components=comps, t_cycle_h=r["t_cycle_h"],
                                    P_bar=r["P_bar"], y_key=r["y_key"], y_h2=r["y_h2"])))
    return out


def analyse(ws, cfg, rows, tag="main"):
    recs = _recs(rows)
    ref = fw.reference_record(cfg)
    c_ref, d_ref = fw.cost(cfg, ref, detail=True)
    for r in recs:
        r["rec"]["xeq_lab"] = fw.lab_xeq(cfg, r["rec"])
        r["cost"], d = fw.cost(cfg, r["rec"], detail=True)
        r["Xp"] = d["Xp"]
    # groups: same paper, pressure, feed
    G = defaultdict(list)
    for r in recs:
        G[(r["paper"], round(r["P_bar"], 1), round(r["y_key"] or 0, 2))].append(r)
    G = {k: v for k, v in G.items() if len({(x["catalyst"], round(x["T_K"])) for x in v}) >= 2}
    rank = {}
    for mname, fn in (("productivity", lambda r: r["r"]), ("conversion", lambda r: r["X"]), ("selectivity", lambda r: r["S"])):
        s = dict(groups=len(G), differ=0, other_catalyst=0, other_temperature=0, regret_gt_1pct=0, max_regret_pct=0.0)
        for m in G.values():
            best, top = min(m, key=lambda r: r["cost"]), max(m, key=fn)
            if top is not best and top["cost"] > best["cost"] + 1e-9:
                reg = (top["cost"] - best["cost"]) / best["cost"]
                s["differ"] += 1
                s["other_catalyst" if top["catalyst"] != best["catalyst"] else "other_temperature"] += 1
                s["regret_gt_1pct"] += reg > 0.01
                s["max_regret_pct"] = max(s["max_regret_pct"], round(100 * reg, 2))
        rank[mname] = s
    # attribution and elasticities
    props = {"selectivity": ("S",), "activity": ("X", "r", "xeq_lab"), "temperature": ("T_K",), "metal": ("components",),
             "stability": ("t_cycle_h",)}
    tot = defaultdict(float)
    for r in recs:
        for name, ks in props.items():
            x = copy.deepcopy(ref)
            for k in ks:
                if k == "t_cycle_h" and r["rec"].get(k) is None:
                    continue
                x[k] = r["rec"][k]
            tot[name] += abs(fw.cost(cfg, x) - c_ref)
    T = sum(tot.values()) or 1
    attribution = {k: round(v / T, 3) for k, v in tot.items()}
    el = {"+1 pt selectivity": fw.cost(cfg, dict(ref, S=min(ref["S"] + 0.01, 1.0))) - c_ref,
          "activity x2": fw.cost(cfg, dict(ref, r=ref["r"] * 2)) - c_ref}
    if cfg["regeneration"]["enabled"] and ref.get("t_cycle_h"):
        el["stability x10"] = fw.cost(cfg, dict(ref, t_cycle_h=ref["t_cycle_h"] * 10)) - c_ref
    key = cfg["stoich"]["key"]
    cfg2 = copy.deepcopy(cfg)
    cfg2["species"][key]["price_usd_t"] *= 0.99
    fw.init_reference(cfg2)
    el[f"{key} price -1 %"] = fw.cost(cfg2, ref) - c_ref
    expensive = max((s for s, v in cfg["species"].items() if v.get("price_usd_t")), key=lambda s: cfg["species"][s]["price_usd_t"])
    if expensive != key:
        cfg3 = copy.deepcopy(cfg)
        cfg3["species"][expensive]["price_usd_t"] *= 0.99
        fw.init_reference(cfg3)
        el[f"{expensive} price -1 %"] = fw.cost(cfg3, ref) - c_ref
    # backward: selectivity needed to reach the reference cost
    need = []
    for r in recs:
        f = lambda S: fw.cost(cfg, dict(r["rec"], S=S)) - c_ref  # noqa: E731
        try:
            need.append(brentq(f, 0.3, 1.0) if f(1.0) < 0 < f(0.3) else None)
        except ValueError:
            need.append(None)
    costs = sorted(r["cost"] for r in recs)
    best = min(recs, key=lambda r: r["cost"])
    summary = dict(
        parameter_set=cfg.get("parameter_set"), n_usable=len(recs), n_records=len(rows), n_papers=len({r["paper"] for r in recs}),
        reference=dict(name=cfg["reference"]["name"], cost=round(c_ref, 2), parts={k: round(v, 2) for k, v in d_ref["parts"].items()},
                       largest=max(d_ref["parts"], key=d_ref["parts"].get)),
        cheapest=dict(paper=best["paper"], catalyst=best["catalyst"], T_C=round(best["T_K"] - 273.15), cost=round(best["cost"], 2)),
        cost_quantiles=dict(min=round(costs[0], 1), median=round(st.median(costs), 1), max=round(costs[-1], 1)),
        below_reference=sum(c < c_ref for c in costs), ranking=rank, attribution_share=attribution,
        cost_change_at_reference={k: round(v, 3) for k, v in el.items()},
        selectivity_needed_reachable=sum(1 for s in need if s), records_X_below_half_Xp=sum(1 for r in recs if r["X"] < 0.5 * r["Xp"]))
    with open(Path(ws) / f"costs_{tag}.csv", "w", newline="", encoding="utf-8") as fh:
        keys = [k for k in recs[0] if k != "rec"]
        w = csv.DictWriter(fh, keys)
        w.writeheader()
        w.writerows({k: r[k] for k in keys} for r in recs)
    (Path(ws) / f"summary_{tag}.json").write_text(json.dumps(summary, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o)), encoding="utf-8")
    return summary


def sensitivity(ws, cfg, rows):
    """One-at-a-time over cfg['uncertain'] = [{path: 'species.C3H8.price_usd_t', low, high, source}]."""
    out = []
    for u in cfg.get("uncertain", []):
        for side in ("low", "high"):
            c2 = copy.deepcopy(cfg)
            d = c2
            ks = u["path"].split(".")
            for k in ks[:-1]:
                d = d[k]
            d[ks[-1]] = u[side]
            fw.init_reference(c2)
            s = analyse(ws, c2, rows, tag="sens")
            out.append(dict(param=u["path"], side=side, value=u[side], ref_cost=s["reference"]["cost"],
                            largest=s["reference"]["largest"],
                            largest_share=round(s["reference"]["parts"][s["reference"]["largest"]] / s["reference"]["cost"], 3),
                            productivity_leader_differs=s["ranking"]["productivity"]["differ"],
                            cheapest=s["cheapest"]["catalyst"], below_reference=s["below_reference"]))
    for p in ("costs_sens.csv", "summary_sens.json"):
        (Path(ws) / p).unlink(missing_ok=True)
    if out:
        with open(Path(ws) / "sensitivity.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, list(out[0]))
            w.writeheader()
            w.writerows(out)
    return out


def check_config(cfg):
    """Schema and sanity checks of a reaction config; returns (problems, reference summary)."""
    need = ["species", "stoich", "thermo", "plant", "lab_feed", "switches", "energy", "capex", "catalyst", "regeneration",
            "reference", "finance", "prices", "metal_usd_per_kg", "sources"]
    probs = [f"missing '{k}'" for k in need if k not in cfg]
    if probs:
        return probs, None
    nu = cfg["stoich"]["nu"]
    for s in nu:
        if s not in cfg["species"]:
            probs.append(f"species '{s}' not in species")
    for s, v in nu.items():
        if v < 0 and not cfg["species"].get(s, {}).get("price_usd_t") and cfg["species"].get(s, {}).get("price_usd_t") != 0:
            probs.append(f"reactant '{s}' has no price_usd_t")
    sh = cfg["capex"]
    if abs(sh["fixed_share"] + sh["throughput_share"] + sh["reactor_share"] - 1) > 1e-6:
        probs.append("capex shares must sum to 1")
    try:
        fw.init_reference(cfg)
        c, d = fw.cost(cfg, fw.reference_record(cfg), detail=True)
        ref = dict(cost=round(c, 2), parts={k: round(v, 2) for k, v in d["parts"].items()}, Xp=round(d["Xp"], 3),
                   Xeq_plant=round(d["Xeq"], 3))
    except Exception as e:  # noqa: BLE001
        return probs + [f"reference cost failed: {type(e).__name__}: {e}"], None
    return probs, ref
