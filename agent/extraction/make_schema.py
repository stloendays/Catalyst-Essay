"""Writes schema.json (OpenAI strict structured-output schema). Edit here, not in schema.json."""
import json
from pathlib import Path

NUM = {
    "type": "object",
    "additionalProperties": False,
    "required": ["value", "unit", "qualifier", "location", "page"],
    "properties": {
        "value": {"type": ["number", "null"], "description": "Number exactly as reported (no unit conversion). null if the paper does not report it for this entry."},
        "unit": {"type": ["string", "null"], "description": "Unit as reported, e.g. 'K', '°C', 'MPa', 'bar', '%', 'mL g-1 h-1', 'h-1', 'g', 'g_MeOH g_cat-1 h-1', 'mmol g-1 h-1', 'wt%'."},
        "qualifier": {"type": ["string", "null"], "enum": ["=", "<", ">", "<=", ">=", "~", None],
                      "description": "'=' for a printed number, '<'/'>' for bounds such as '<1', '~' for a value read off a plot."},
        "location": {"type": ["string", "null"], "description": "Where the number is printed: 'Table 2', 'Figure 3b', 'Experimental section 2.3', 'Table 1 footnote'."},
        "page": {"type": ["integer", "null"], "description": "1-based PDF page from the === PAGE n === marker."},
    },
}

num = {"$ref": "#/$defs/num"}
COMPONENT = {
    "type": "object",
    "additionalProperties": False,
    "required": ["component", "role", "loading"],
    "properties": {
        "component": {"type": "string", "description": "Element or oxide, e.g. 'Cu', 'ZnO', 'In2O3', 'Pd'."},
        "role": {"type": "string", "enum": ["active_metal", "active_oxide", "promoter", "support"]},
        "loading": num,
    },
}

RECORD = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "entry_label": {"type": "string", "description": "Short unique label, e.g. 'Table 2 row 3' or 'Fig 4a, 533 K'."},
        "catalyst_name": {"type": "string", "description": "Catalyst name exactly as the paper writes it."},
        "composition": {"type": ["string", "null"], "description": "Formula-style composition as stated, e.g. 'CuO/ZnO/Al2O3 = 60/30/10 wt%'."},
        "components": {"type": "array", "items": COMPONENT},
        "support": {"type": ["string", "null"]},
        "promoters": {"type": "array", "items": {"type": "string"}},
        "preparation": {"type": ["string", "null"], "description": "Distinguishing preparation detail (method, calcination/reduction T) when the paper uses it to tell catalysts apart."},
        "temperature": num,
        "pressure": num,
        "h2_co2_ratio": num,
        "feed_composition": {"type": ["string", "null"], "description": "Feed as stated, e.g. 'H2/CO2/N2 = 72/24/4'."},
        "ghsv": num,
        "ghsv_basis": {"type": "string", "enum": ["per_mass_catalyst", "per_volume_catalyst", "per_mass_metal", "unspecified"]},
        "catalyst_mass": num,
        "total_flow": num,
        "time_on_stream": num,
        "co2_conversion": num,
        "selectivity_ch3oh": num,
        "selectivity_co": num,
        "selectivity_ch4": num,
        "selectivity_basis": {"type": "string", "enum": ["carbon_molar", "unspecified", "other"]},
        "methanol_sty": num,
        "sty_basis": {"type": "string", "enum": ["per_g_catalyst", "per_g_metal", "per_mL_catalyst", "per_mol_metal", "per_m2", "other", "unspecified"]},
        "data_source_type": {"type": "string", "enum": ["table", "text", "figure", "mixed"]},
        "primary_location": {"type": "string", "description": "Main table/figure holding the performance numbers."},
        "primary_page": {"type": ["integer", "null"]},
        "notes": {"type": ["string", "null"], "description": "Anything needed to interpret the entry (e.g. 'conditions from Experimental 2.3', 'equilibrium-limited')."},
    },
}
RECORD["required"] = list(RECORD["properties"].keys())

SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["doi", "title", "records", "extraction_notes"],
    "properties": {
        "doi": {"type": "string"},
        "title": {"type": "string"},
        "records": {"type": "array", "items": RECORD},
        "extraction_notes": {"type": ["string", "null"], "description": "Paper-level notes: data only in SI, figures not readable, etc."},
    },
    "$defs": {"num": NUM},
}

if __name__ == "__main__":
    Path(__file__).with_name("schema.json").write_text(json.dumps(SCHEMA, indent=1, ensure_ascii=False), encoding="utf-8")
    print("schema.json written")
