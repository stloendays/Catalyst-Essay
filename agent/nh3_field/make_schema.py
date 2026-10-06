"""Writes schema.json (OpenAI strict structured-output schema) for ammonia-synthesis catalyst records.
Edit here, not in schema.json. Same numeric-field convention as the methanol agent (agent/extraction/make_schema.py)."""
import json
from pathlib import Path

NUM = {
    "type": "object",
    "additionalProperties": False,
    "required": ["value", "unit", "qualifier", "location", "page"],
    "properties": {
        "value": {"type": ["number", "null"], "description": "Number exactly as reported (no unit conversion). null if the paper does not report it for this entry."},
        "unit": {"type": ["string", "null"], "description": "Unit as reported, e.g. '°C', 'K', 'MPa', 'bar', 'atm', 'wt%', 'mL g-1 h-1', 'h-1', 'vol%', 'ppm', 'umol g-1 h-1', 'mmol gRu-1 h-1', 's-1'."},
        "qualifier": {"type": ["string", "null"], "enum": ["=", "<", ">", "<=", ">=", "~", None],
                      "description": "'=' for a printed number, '<'/'>' for bounds, '~' for a value read off a plot."},
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
        "component": {"type": "string", "description": "Element or compound, e.g. 'Ru', 'Fe', 'Cs', 'BaO', 'MgO', 'C12A7:e-'."},
        "role": {"type": "string", "enum": ["active_metal", "promoter", "support"]},
        "loading": num,
    },
}

RECORD = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "entry_label": {"type": "string", "description": "Short unique label, e.g. 'Table 1 row 3' or 'Fig 3a, 400 C'."},
        "catalyst_name": {"type": "string", "description": "Catalyst name exactly as the paper writes it."},
        "composition": {"type": ["string", "null"], "description": "Composition as stated, e.g. '2 wt% Ru, Cs/Ru = 1'."},
        "active_metal": {"type": ["string", "null"], "description": "Element symbol of the catalytic metal (Ru, Fe, Co, Ni, Mo, Os, Re, ...). Several metals: join with ';' (e.g. 'Co;Mo'). Promoters and support cations are not active metals."},
        "metal_loading": num,
        "components": {"type": "array", "items": COMPONENT},
        "support": {"type": ["string", "null"]},
        "promoters": {"type": "array", "items": {"type": "string"}},
        "preparation": {"type": ["string", "null"], "description": "Distinguishing preparation detail (method, calcination/reduction T, morphology) when the paper uses it to tell catalysts apart."},
        "temperature": num,
        "pressure": num,
        "h2_n2_ratio": num,
        "feed_composition": {"type": ["string", "null"], "description": "Feed as stated, e.g. 'H2/N2 = 3', '75% H2, 25% N2'."},
        "space_velocity": num,
        "space_velocity_basis": {"type": "string", "enum": ["per_mass_catalyst", "per_volume_catalyst", "unspecified"]},
        "catalyst_mass": num,
        "total_flow": num,
        "time_on_stream": num,
        "outlet_nh3": num,
        "rate": num,
        "rate_basis": {"type": "string", "enum": ["per_g_catalyst", "per_g_metal", "per_mol_metal", "per_mL_catalyst", "per_m2", "other", "unspecified"]},
        "tof": num,
        "tof_basis": {"type": ["string", "null"], "description": "How the TOF is normalised, e.g. 'per surface Ru atom (CO chemisorption)', 'per total Ru'."},
        "operation_mode": {"type": "string", "enum": ["steady_thermal_catalytic", "chemical_looping", "plasma", "electric_field", "microwave", "photo", "other"]},
        "data_source_type": {"type": "string", "enum": ["table", "text", "figure", "mixed"]},
        "primary_location": {"type": "string", "description": "Main table/figure holding the rate."},
        "primary_page": {"type": ["integer", "null"]},
        "notes": {"type": ["string", "null"], "description": "Anything needed to interpret the entry (e.g. 'conditions from Experimental 2.3', 'equilibrium-limited', 'after 50 h on stream')."},
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
