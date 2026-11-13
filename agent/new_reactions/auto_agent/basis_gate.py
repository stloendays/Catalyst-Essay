"""Evidence-bearing design basis; no reaction-specific data."""
import json
import math
import re


def evidence(ev, value=None):
    if not isinstance(ev, dict):
        raise ValueError("evidence must be a mapping")
    typ = ev.get("type")
    if typ in ("measured", "published"):
        if not re.search(r"https?://|10\.\d{4,9}/", ev.get("source", "")) or not ev.get("location", "").strip():
            raise ValueError("published/measured evidence needs URL/DOI and location")
    elif typ == "assumption":
        lo, hi = float(ev["low"]), float(ev["high"])
        if not all(math.isfinite(x) for x in (lo, hi)) or lo > hi or (value is not None and not lo <= value <= hi):
            raise ValueError("assumption requires finite low <= value <= high")
    else:
        raise ValueError("invalid evidence type")


def basis_values(basis, prefix="basis"):
    out = {}
    def walk(x, path):
        if isinstance(x, dict):
            if "value" in x:
                out[path] = x
            else:
                for k, v in x.items():
                    if k not in ("evidence", "purchased_preheat_reason", "zero_duty_evidence"):
                        walk(v, path + "." + k)
    walk(basis, prefix)
    return out


def check_basis(path):
    try:
        try:
            from .physics_gate import formula_elements
        except ImportError:
            from physics_gate import formula_elements
        b = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(b["battery_limit"], str) or not b["battery_limit"].strip():
            raise ValueError("battery_limit missing")
        for k in ("capacity_t_per_y", "operating_hours_per_y"):
            if b[k]["value"] <= 0:
                raise ValueError(k + " must be positive")
        if b["operating_hours_per_y"]["value"] > 8784:
            raise ValueError("operating hours exceed a year")
        for side, fields in (("feeds", ("T_K", "P_bar", "purity_mol_frac")), ("product", ("P_bar", "purity_mol_frac"))):
            if not b[side]:
                raise ValueError(side + " missing")
            for species, state in b[side].items():
                formula_elements(species)
                for field in fields:
                    v = state[field]["value"]
                    if v <= 0 or (field == "purity_mol_frac" and v > 1):
                        raise ValueError("invalid " + field)
        if not isinstance(b["utilities"], dict):
            raise ValueError("utilities must be a mapping")
        for v in b["utilities"].values():
            if not v.get("unit"):
                raise ValueError("utility unit missing")
            if "usd" in v["unit"].lower():
                raise ValueError("prices are not basis values: cite them from prices.json in sources.csv (type price_table)")
        for name, leaf in basis_values(b).items():
            v = leaf["value"]
            if isinstance(v, bool) or not isinstance(v, (float, int)) or not math.isfinite(v):
                raise ValueError(name + ": value must be numeric and finite")
            evidence(leaf["evidence"], v)
        if b.get("purchased_preheat_reason") is not None:
            evidence(b["purchased_preheat_reason"])
        for name, ev in (b.get("zero_duty_evidence") or {}).items():
            if not isinstance(ev, dict) or ev.get("type") not in ("measured", "published"):
                raise ValueError("zero_duty_evidence " + name + " must be measured/published")
            evidence(ev)
        return []
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        return ["basis: " + str(exc)]
