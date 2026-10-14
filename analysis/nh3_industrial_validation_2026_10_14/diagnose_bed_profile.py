#!/usr/bin/env python3
"""Source-conditioned S-200 converter bed-profile falsification, no refitting.

Reports required kinetic-scale equivalents only for the *fixed measured bed
temperature targets*; volume ratios cannot be interpreted as fitted kinetic
orders or an industrial effectiveness-factor measurement.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from audit_industrial import SRC, V12, rows, enforce_pin

PIN_CASE_RESULTS = "3a4116999a8c6765154970e057f46be3c82a420f"
PIN_CASE_INPUTS = "25816cab4aa12a5fd835981ead9135a304cee9fe"


def diagnose():
    enforce_pin(V12 / "results_cases.json", PIN_CASE_RESULTS)
    enforce_pin(SRC / "benchmark_cases.csv", PIN_CASE_INPUTS)
    model = json.loads((V12 / "results_cases.json").read_text(encoding="utf-8"))["model"]
    cases = {r["case_id"]: r for r in rows(SRC / "benchmark_cases.csv")}
    entries = []
    for group in ("LIU919A", "LIU919B"):
        forward_id, inverse_id = group + "_FWD", group + "_INV"
        cfg = json.loads(cases[forward_id]["beds"])
        fwd = model[forward_id]["beds"]
        inv = model[inverse_id]["beds"]
        if len(cfg) != 2 or len(fwd) != 2 or len(inv) != 2:
            raise AssertionError("S-200 fixed-design audit requires two source-matched beds")
        for idx in range(2):
            cat, T_in, V = cfg[idx]
            bf, bi = fwd[idx], inv[idx]
            assert cat == "Fe" and bf["catalyst"] == cat and bi["catalyst"] == cat
            assert abs(float(T_in) - bf["T_in_C"]) < 1e-9
            assert abs(float(V) - bf["V_m3"]) < 1e-9
            m3_needed = float(bi["V_model_m3"])
            ratio = m3_needed / V
            entries.append(dict(case=group, bed=idx + 1, installed_m3=V, required_m3_for_printed_heat_rise=m3_needed,
                                required_volume_over_installed=ratio,
                                modeled_forward_Tout_C=bf["T_out_C"],
                                source_outlet_T_C=bi["T_out_C"],
                                model_minus_source_T_K=bf["T_out_C"] - bi["T_out_C"],
                                interpretation="fixed-trajectory rate-equivalent only; not a fitted effectiveness factor"))
    for group in ("LIU919A", "LIU919B"):
        first, second = (next(r for r in entries if r["case"] == group and r["bed"] == j) for j in (1, 2))
        assert first["required_volume_over_installed"] > 1.5
        assert 0.9 < second["required_volume_over_installed"] < 1.1
        assert abs(first["required_volume_over_installed"] - second["required_volume_over_installed"]) > 0.4
    return entries


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", type=Path, required=True)
    args = ap.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    entries = diagnose()
    with (args.out_dir / "bed_profile_4.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(entries[0]))
        w.writeheader()
        w.writerows(entries)
    (args.out_dir / "bed_profile_summary.json").write_text(json.dumps({
        "n": 4,
        "source_conditioned": True,
        "equal_kinetic_rate_multiplier_for_both_beds": False,
        "status": "MODEL_PROFILE_MISMATCH_NOT_FITTED",
        "rows": entries,
    }, indent=2) + "\n", encoding="utf-8")
    lines = ["# Liu S-200 converter bed-local model mismatch (non-fitting audit)", "",
             "With the published inlet composition, bed temperatures and installed volumes "
             "(S-200 126.4 and 134.0 bar), the model inverse calculation requires:",
             "", "| Pressure case | Bed | Installed m3 | Required m3 at printed rise | Required / installed |",
             "|---|---:|---:|---:|---:|"]
    for e in entries:
        lines.append(f"| {e['case']} | {e['bed']} | {e['installed_m3']:.2f} | "
                     f"{e['required_m3_for_printed_heat_rise']:.2f} | "
                     f"{e['required_volume_over_installed']:.3f} |")
    lines += ["", "The first bed needs about 1.63x modeled catalyst, while the second needs about 1.0x. "
              "Hence a single uniform kinetic rate multiplier cannot simultaneously reconcile both "
              "measured temperature targets under this fixed-trajectory calculation.",
              "This does NOT identify the cause: particle effectiveness, heat transfer, feed mixing, "
              "interbed composition, enthalpy/kinetic basis and hydraulics are still unresolved.",
              "This is NOT a new preregistered pass statistic.", ""]
    (args.out_dir / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    print("PASS: 4 source-conditioned bed checks; two distinct rate-equivalent discrepancies")


if __name__ == "__main__":
    main()
