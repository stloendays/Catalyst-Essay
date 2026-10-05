"""Fetch N* adsorption energies of the Mamun et al. (2019) bimetallic surfaces from Catalysis-Hub.

Source: Mamun, Winther, Boes & Bligaard, "High-throughput calculations of catalytic properties of bimetallic
alloy surfaces", Scientific Data 6, 76 (2019), doi:10.1038/s41597-019-0080-z; Catalysis-Hub pubId
MamunHighT2019 (CC BY 4.0). Only the reaction 0.5 N2(g) + * -> N* is kept, one row per adsorption site.

The Catalysis-Hub key is read from the keyring (service "catalysis-hub", user "api_key") or the
CATHUB_API_KEY environment variable and sent only as a request header.

    python fetch_mamun_n_binding.py   -> mamun2019_N_binding_sites.csv
"""
import csv
import json
import os
from pathlib import Path

import requests

URL = "https://api-catalysis-hub.slac.stanford.edu/graphql"
HERE = Path(__file__).resolve().parent
OUT = HERE / "mamun2019_N_binding_sites.csv"


def api_key():
    key = os.environ.get("CATHUB_API_KEY")
    if key:
        return key
    try:
        import keyring
        return keyring.get_password("catalysis-hub", "api_key")
    except ImportError:
        return None


def main():
    headers = {"Content-Type": "application/json"}
    key = api_key()
    if key:
        headers["X-API-Key"] = key
    rows, after = [], ""
    while True:
        cursor = f', after: "{after}"' if after else ""
        query = ('{ reactions(first: 500, pubId: "MamunHighT2019", reactants: "~N2gas", products: "Nstar"%s) '
                 '{ totalCount pageInfo { hasNextPage endCursor } edges { node { id Equation chemicalComposition '
                 'surfaceComposition facet sites reactionEnergy reactants products } } } }' % cursor)
        r = requests.post(URL, json={"query": query}, headers=headers, timeout=120)
        r.raise_for_status()
        data = r.json()
        if "errors" in data:
            raise SystemExit(data["errors"])
        block = data["data"]["reactions"]
        rows += [e["node"] for e in block["edges"]]
        if not block["pageInfo"]["hasNextPage"]:
            break
        after = block["pageInfo"]["endCursor"]
    keep = [n for n in rows if n["Equation"] == "0.5N2(g) + * -> N*"]
    keep.sort(key=lambda n: (n["surfaceComposition"], n["facet"], n["sites"], n["reactionEnergy"]))
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["cathub_id", "surface_composition", "bulk_composition", "facet", "site", "E_N_eV"])
        for n in keep:
            w.writerow([n["id"], n["surfaceComposition"], n["chemicalComposition"], n["facet"],
                        json.loads(n["sites"]).get("N", ""), f"{n['reactionEnergy']:.6f}"])
    print(f"{len(keep)} N* rows ({len({n['surfaceComposition'] for n in keep})} surfaces) -> {OUT.name}")


if __name__ == "__main__":
    main()
