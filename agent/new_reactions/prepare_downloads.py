"""Download lists for the three new reactions (manual download by the user through nus-fetch).

For each reaction: OpenAlex title search (open access not required, the user downloads through the NUS library),
LLM screening by title + abstract (API-YES gpt-5.6-sol) with two answers - include, and how likely the paper reports
performance data a plant model can use (conversion and selectivity with feed, flow/space velocity, catalyst mass) -
then the top N by (include, data likelihood, confidence, citations). Writes downloads/<rxn>_dois.txt (one DOI per
line, ranked), downloads/<rxn>_candidates.csv (all screened, with reasons) and logs tokens.
"""
import csv
import json
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "extraction"))
import llm_route  # noqa: E402
import openai  # noqa: E402

N_PICK = 15
MODEL = "gpt-5.6-sol"
REACTIONS = {
    "nh3dec": dict(titles=['"ammonia decomposition"', '"NH3 decomposition"'], must=("ammonia", "nh3"),
                   crit="experimental thermocatalytic ammonia decomposition to hydrogen (2 NH3 -> N2 + 3 H2) over heterogeneous catalysts, "
                        "reporting NH3 conversion (and H2 production rate) under stated temperature and space velocity. Exclude "
                        "electrochemical, plasma, photocatalytic, membrane-reactor-only, reviews, DFT/kinetic-model-only, engine/combustion papers."),
    "rwgs": dict(titles=['"reverse water gas shift"', '"reverse water-gas shift"', '"RWGS"'], must=("reverse", "rwgs"),
                 crit="experimental thermocatalytic reverse water-gas shift (CO2 + H2 -> CO + H2O) over heterogeneous catalysts, reporting "
                      "CO2 conversion and CO selectivity under stated conditions. Exclude electrochemical, plasma, photocatalytic, chemical "
                      "looping only, reviews, DFT/kinetic-model-only, process-simulation/TEA-only papers."),
    "etoh": dict(titles=['"ethanol dehydration"', '"dehydration of ethanol"'], must=("ethanol",),
                 crit="experimental gas-phase catalytic dehydration of ethanol to ethylene over heterogeneous catalysts (zeolites, alumina, "
                      "heteropolyacids, etc.), reporting ethanol conversion and ethylene selectivity under stated temperature and space "
                      "velocity. Exclude dehydration to diethyl ether only, ethanol to propylene/aromatics/butadiene/hydrocarbons, liquid-phase, "
                      "reviews, DFT-only, process-simulation/TEA-only papers."),
}
SCHEMA = {"type": "object", "additionalProperties": False, "required": ["items"],
          "properties": {"items": {"type": "array", "items": {
              "type": "object", "additionalProperties": False,
              "required": ["doi", "include", "confidence", "data_likelihood", "reason"],
              "properties": {"doi": {"type": "string"}, "include": {"type": "boolean"},
                             "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
                             "data_likelihood": {"type": "string", "enum": ["high", "medium", "low"]},
                             "reason": {"type": "string"}}}}}}
RANK = {"high": 0, "medium": 1, "low": 2}


def inv(ab):
    return " ".join(w for _, w in sorted((p, w) for w, ps in (ab or {}).items() for p in ps))


def search(rx):
    res = {}
    for q in REACTIONS[rx]["titles"]:
        for page in (1, 2):
            url = ("https://api.openalex.org/works?filter=title.search:" + urllib.parse.quote(q) +
                   ",type:article,from_publication_date:2010-01-01,has_doi:true"
                   f"&sort=cited_by_count:desc&per-page=200&page={page}")
            for wait in (0, 20, 60):
                time.sleep(wait)
                try:
                    d = json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "catalyst-essay-pipeline"}), timeout=90))
                    break
                except Exception as e:  # noqa: BLE001
                    print("retry", q, page, e)
            else:
                continue
            for w in d["results"]:
                t = (w.get("title") or "").lower()
                if any(m in t for m in REACTIONS[rx]["must"]):
                    res[w["id"]] = w
            if len(d["results"]) < 200:
                break
    rows = []
    for w in res.values():
        loc = w.get("best_oa_location") or {}
        rows.append(dict(doi=(w.get("doi") or "").replace("https://doi.org/", "").lower(), year=w.get("publication_year"),
                         title=w.get("title"), venue=((w.get("primary_location") or {}).get("source") or {}).get("display_name"),
                         cites=w.get("cited_by_count") or 0, open_access=bool(loc.get("pdf_url")),
                         abstract=inv(w.get("abstract_inverted_index"))[:1500]))
    rows.sort(key=lambda r: -r["cites"])
    return rows


def screen(rx, rows, limit=320):
    # API-YES (gpt-5.6-sol) first; when its usage window is used up, the advisor key with gpt-5.5 (llm_route order)
    routes = []
    k = llm_route.api_yes_key(MODEL)
    if k:
        routes.append((openai.OpenAI(api_key=k, base_url=llm_route.API_YES_URL, timeout=900), MODEL, "api-yes"))
    adv = llm_route.make_client("advisor-openai", "gpt-5.5")
    if adv is not None:
        routes.append((adv, "gpt-5.5", "advisor-openai"))
    client, model, route = routes.pop(0)
    out, tok = {}, [0, 0]
    rows = rows[:limit]
    for i in range(0, len(rows), 40):
        batch = rows[i:i + 40]
        text = "\n\n".join(f"DOI: {r['doi']}\nTitle: {r['title']}\nAbstract: {r['abstract'] or '(none)'}" for r in batch)
        for attempt in range(3):
            try:
                pieces, final = [], None
                for ev in client.responses.create(
                        model=model, input=[{"role": "user", "content": text}], store=False, stream=True, reasoning={"effort": "low"},
                        instructions=("Screen papers for a catalyst-performance database. Include only " + REACTIONS[rx]["crit"] +
                                      " data_likelihood: how likely the paper reports, for several catalysts or conditions, conversion and "
                                      "selectivity together with feed composition and flow/space velocity or catalyst mass (tables or clear "
                                      "plots): high/medium/low. Without an abstract judge from the title with confidence 'low'. One item per DOI."),
                        text={"format": {"type": "json_schema", "name": "screen", "strict": True, "schema": SCHEMA}}):
                    if ev.type == "response.output_text.delta":
                        pieces.append(ev.delta)
                    elif ev.type in ("response.completed", "response.incomplete"):
                        final = ev.response
                for it in json.loads("".join(pieces))["items"]:
                    out[it["doi"].lower()] = it
                tok[0] += final.usage.input_tokens
                tok[1] += final.usage.output_tokens
                break
            except Exception as e:  # noqa: BLE001
                print("retry screen", route, str(e)[:120])
                if llm_route.is_exhausted(e) and routes:
                    client, model, route = routes.pop(0)
                    print("switched to", route, model)
                else:
                    time.sleep(15)
    screen.route = route
    return out, tok


def main():
    d = HERE / "downloads"
    d.mkdir(exist_ok=True)
    for rx in sys.argv[1:] or list(REACTIONS):
        rows = search(rx)
        sc, tok = screen(rx, rows)
        for r in rows:
            s = sc.get(r["doi"], {})
            r.update(include=s.get("include"), confidence=s.get("confidence"), data_likelihood=s.get("data_likelihood"),
                     reason=(s.get("reason") or "")[:200])
        with open(d / f"{rx}_candidates.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, [k for k in rows[0] if k != "abstract"], extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)
        inc = [r for r in rows if r["include"] is True]
        inc.sort(key=lambda r: (RANK.get(r["data_likelihood"], 3), RANK.get(r["confidence"], 3), -r["cites"]))
        pick = inc[:N_PICK]
        (d / f"{rx}_dois.txt").write_text("\n".join(r["doi"] for r in pick) + "\n", encoding="utf-8")
        with open(d / "token_usage_prepare.csv", "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([datetime.now().isoformat(timespec="seconds"), rx, len(rows), len(sc), tok[0], tok[1], "gpt-5.6-sol/gpt-5.5", getattr(screen, "route", "")])
        print(rx, len(rows), "found;", len(sc), "screened;", len(inc), "included;", "picked", len(pick),
              "(data high:", sum(r["data_likelihood"] == "high" for r in pick), ", open access:", sum(r["open_access"] for r in pick), ")",
              "tokens", tok)


if __name__ == "__main__":
    main()
