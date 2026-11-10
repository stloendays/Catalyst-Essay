"""AI screening of candidates2_<rxn>.csv by title + abstract (API-YES, gpt-5.6-sol), 40 per call, strict JSON.
Writes screen_<rxn>.csv (doi, include, confidence, reason) and logs tokens to token_usage_screen.csv."""
import csv
import json
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "extraction"))
import llm_route  # noqa: E402
import openai  # noqa: E402

MODEL = "gpt-5.6-sol"
CRIT = {
    "pdh": ("Include only experimental papers on NON-OXIDATIVE propane dehydrogenation to propylene over a heterogeneous "
            "catalyst that report propane conversion and propylene selectivity (or yield/rate) under stated conditions. "
            "Exclude: oxidative dehydrogenation (O2, CO2, N2O, chemical looping), reviews, purely computational/DFT/kinetic-model "
            "papers, membrane/process-only or techno-economic papers, other alkanes only."),
    "ch4": ("Include only experimental papers on THERMOCATALYTIC CO2 methanation (CO2 + H2 -> CH4) over a heterogeneous "
            "catalyst that report CO2 conversion and CH4 selectivity (or yield/rate) under stated conditions. Exclude: "
            "photocatalytic, photothermal, electrochemical, plasma, biological methanation; CO-only methanation; integrated "
            "capture-methanation dual-function materials run in cycles; reviews; purely computational, reactor-model or "
            "techno-economic papers."),
}
SCHEMA = {"type": "object", "additionalProperties": False, "required": ["items"],
          "properties": {"items": {"type": "array", "items": {
              "type": "object", "additionalProperties": False, "required": ["doi", "include", "confidence", "reason"],
              "properties": {"doi": {"type": "string"}, "include": {"type": "boolean"},
                             "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
                             "reason": {"type": "string"}}}}}}


def main(rx):
    rows = list(csv.DictReader(open(HERE / f"candidates2_{rx}.csv", encoding="utf-8")))
    client = openai.OpenAI(api_key=llm_route.api_yes_key(MODEL), base_url=llm_route.API_YES_URL, timeout=900)
    out_p = HERE / f"screen_{rx}.csv"
    done = {r["doi"] for r in csv.DictReader(open(out_p, encoding="utf-8"))} if out_p.exists() else set()
    todo = [r for r in rows if r["doi"] not in done]
    for i in range(0, len(todo), 40):
        batch = todo[i:i + 40]
        text = "\n\n".join(f"DOI: {r['doi']}\nTitle: {r['title']}\nAbstract: {r['abstract'] or '(none)'}" for r in batch)
        t0 = time.time()
        for attempt in range(3):
            try:
                pieces, final = [], None
                for ev in client.responses.create(model=MODEL, instructions="Screen papers for a catalyst-performance database. " + CRIT[rx] +
                                                  " Without an abstract decide from the title; use confidence 'low'. Return one item per DOI.",
                                                  input=[{"role": "user", "content": text}], store=False, stream=True,
                                                  reasoning={"effort": "low"},
                                                  text={"format": {"type": "json_schema", "name": "screen", "strict": True, "schema": SCHEMA}}):
                    if ev.type == "response.output_text.delta":
                        pieces.append(ev.delta)
                    elif ev.type in ("response.completed", "response.incomplete"):
                        final = ev.response
                items = json.loads("".join(pieces))["items"]
                break
            except Exception as e:  # noqa: BLE001
                print("retry", e)
                time.sleep(10)
        new = not out_p.exists()
        with open(out_p, "a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, ["doi", "include", "confidence", "reason"])
            if new:
                w.writeheader()
            w.writerows(items)
        u = final.usage
        up = HERE / "token_usage_screen.csv"
        new = not up.exists()
        with open(up, "a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            if new:
                w.writerow(["timestamp", "rxn", "n", "prompt_tokens", "completion_tokens", "seconds", "model", "route"])
            w.writerow([datetime.now().isoformat(timespec="seconds"), rx, len(batch), u.input_tokens, u.output_tokens,
                        round(time.time() - t0, 1), MODEL, "api-yes"])
        print(rx, i + len(batch), "/", len(todo), sum(x["include"] for x in items), "included", flush=True)


if __name__ == "__main__":
    main(sys.argv[1])
