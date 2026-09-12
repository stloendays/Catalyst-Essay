"""
DISCOVER-BOUNDARY-C1: exact break-even / reachability audit of the strong non-binding-allowance cell (2026-09-12).

Per-run audit of the 20 strong runs at the non-binding 5000-CU allowance. Read-only replay of existing traces: no model
is called, no frozen file is modified, no scientific value is recomputed. Every quantity is taken from the trace and
compared against the frozen reference in DISCOVER_SCORER_V1.GT.

Audited per run:
  scored_break_even     the multiplier the frozen final_answer() reports = FIRST BACKWARD record for (atomic_best, winner)
  all_backward          every successful BACKWARD record for the decision pair, in execution order, with its window
  scored_reachability   the classification the frozen final_answer() reports = FIRST classified TEST_REACHABILITY for atomic_best
  all_reachability      every classified TEST_REACHABILITY record, in execution order
  headroom              the max-gain values the environment returned, against GT headroom
  first_stable_CU       ledger-true cumulative CU (budget - remaining_budget) at the first step from which the full
                        decision stays correct to the end
  final_CU              spent_CU at stop

Any field that the raw trace cannot establish is emitted as the string "NOT_IN_TRACE" and listed in the gaps section
rather than inferred.

Usage (from harness root):
  python discover/c1_uncapped_breakeven_audit.py
  python discover/c1_uncapped_breakeven_audit.py --glob "DISCOVER_BOUNDARY_C1/runs/gpt-5.5-2026-04-23/traces/anonymous/*B225*"
"""
from __future__ import annotations
import argparse, csv, glob, json, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "discover"))
import DISCOVER_SCORER_V1 as S
from boundary_c1_metrics import _replay_answers, _full

OUT = ROOT / "DISCOVER_BOUNDARY_C1"
DATA = OUT / "data"
MISSING = "NOT_IN_TRACE"
DEFAULT_GLOB = "DISCOVER_BOUNDARY_C1/runs/gpt-5.5-2026-04-23/traces/anonymous/*B5000*c1uncapped*"
REL_TOL = 1e-9


def _demapped(path: Path) -> dict:
    t = json.loads(path.read_text(encoding="utf-8"))
    mp = path.parent / "identity_mapping.json"
    if not mp.exists():
        return t  # caller records the gap
    m = json.loads(mp.read_text(encoding="utf-8"))["public_to_real"]
    return S._demap(t, m)


def audit_one(path: Path) -> dict:
    gaps: list[str] = []
    if not (path.parent / "identity_mapping.json").exists():
        gaps.append("identity_mapping.json absent: candidate ids cannot be resolved to metals")
    t = _demapped(path)
    steps = t["steps"]
    fin = t["final"]
    ans = fin["answer"]
    pair = list(S.DECISION_PAIR)          # ("Ru", "Fe") = (atomic best, economic winner)
    gt_be = float(S.GT["break_even"])
    gt_reach = S.GT["reachability"]

    backward, reach = [], []
    for s in steps:
        r = s.get("result")
        if not isinstance(r, dict) or "error" in r:
            continue
        if s.get("chosen_action") == "BACKWARD" and r.get("multiplier") is not None:
            w = r.get("window")
            n = next((x["result"]["n_states"] for x in steps
                      if x.get("chosen_action") == "BUILD_PROCESS_WINDOW" and isinstance(x.get("result"), dict)
                      and x["result"].get("window") == w), MISSING)
            backward.append({"step": s["step"], "pair": r.get("pair"), "multiplier": float(r["multiplier"]),
                             "window": w, "window_states": n,
                             "parity_state": r.get("state_at_parity", MISSING)})
        if s.get("chosen_action") == "TEST_REACHABILITY" and "classification" in r:
            reach.append({"step": s["step"], "metal": r.get("metal"), "classification": r["classification"],
                          "required_multiplier": r.get("required_multiplier", MISSING),
                          "max_gain": r.get("max_gain_across_process_states", r.get("max_gain_on_descriptor_manifold_at_reference", MISSING))})

    dp = [b for b in backward if b["pair"] == pair]
    scored_be = ans.get("parity_multiplier_atomic_best_vs_winner")
    scored_reach = ans.get("reachability_classification")
    if scored_be is None:
        gaps.append("frozen answer carries no parity multiplier for the decision pair")
    if scored_reach is None:
        gaps.append("frozen answer carries no reachability classification")

    # cross-check: the frozen answer must equal the FIRST decision-pair BACKWARD record
    first_dp = dp[0]["multiplier"] if dp else None
    consistent = (scored_be is not None and first_dp is not None
                  and abs(scored_be - first_dp) <= REL_TOL * max(1.0, abs(first_dp)))

    answers = _replay_answers(t)
    flags = [_full(a) for a in answers]
    if flags and flags[-1]:
        k = len(flags) - 1
        while k > 0 and flags[k - 1]:
            k -= 1
        first_stable = float(t["budget_CU"]) - float(steps[k]["remaining_budget"])
    else:
        first_stable = None

    hv = sorted({round(float(r["max_gain"]), 4) for r in reach if r["max_gain"] != MISSING})
    gt_head = S.GT.get("headroom", MISSING)

    return {
        "run_dir": path.parent.name,
        "run_index": t.get("run_index"),
        "budget_CU": float(t["budget_CU"]),
        "steps": len(steps),
        "scored_winner": ans.get("industrial_winner"),
        "winner_matches_frozen": ans.get("industrial_winner") == S.GT["winner"],
        "scored_break_even": scored_be if scored_be is not None else MISSING,
        "break_even_rel_error": (abs(scored_be - gt_be) / gt_be) if isinstance(scored_be, (int, float)) else MISSING,
        "break_even_is_canonical": bool(isinstance(scored_be, (int, float)) and abs(scored_be - gt_be) / gt_be < 1e-6),
        "n_decision_pair_BACKWARD": len(dp),
        "first_decision_pair_multiplier": first_dp if first_dp is not None else MISSING,
        "any_BACKWARD_canonical": bool(any(abs(b["multiplier"] - gt_be) / gt_be < 1e-6 for b in dp)),
        "scored_equals_first_record": consistent,
        "all_decision_pair_multipliers": json.dumps([round(b["multiplier"], 6) for b in dp]),
        "decision_pair_windows": json.dumps([[b["window"], b["window_states"]] for b in dp]),
        "scored_reachability": scored_reach if scored_reach is not None else MISSING,
        "reachability_matches_frozen": scored_reach == gt_reach,
        "n_classified_reachability": len(reach),
        "all_reachability": json.dumps([[r["step"], r["metal"], r["classification"]] for r in reach]),
        "headroom_values_returned": json.dumps(hv),
        "gt_headroom": json.dumps(gt_head),
        "first_stable_CU": first_stable if first_stable is not None else MISSING,
        "final_CU": float(fin["spent_CU"]),
        "overrun_CU": (float(fin["spent_CU"]) - first_stable) if first_stable is not None else MISSING,
        "remaining_at_stop": float(fin["remaining_budget"]),
        "stop_self": str(fin["why_stop"]).startswith("agent STOP"),
        "gaps": json.dumps(gaps),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--glob", default=DEFAULT_GLOB)
    ap.add_argument("--out", default="discover_boundary_c1_uncapped_breakeven_audit")
    a = ap.parse_args()
    paths = sorted(Path(p).parent for p in glob.glob(str(ROOT / a.glob / "trace.json")))
    if not paths:
        raise SystemExit(f"no traces matched {a.glob}")
    rows = [audit_one(p / "trace.json") for p in paths]
    rows.sort(key=lambda r: int(r["run_index"]))

    DATA.mkdir(parents=True, exist_ok=True)
    csv_path = DATA / f"{a.out}.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    gt_be = float(S.GT["break_even"])
    print(f"frozen reference: break_even = {gt_be!r}  reachability = {S.GT['reachability']!r}  winner = {S.GT['winner']!r}")
    print(f"headroom in GT: {json.dumps(S.GT.get('headroom', MISSING))}")
    print()
    def fmt(v, spec):
        return format(v, spec) if isinstance(v, (int, float)) else str(v)

    hdr = ("run", "steps", "win", "scored_BE", "relerr", "=1st", "nBW", "anyBWcanon", "reach", "stable", "final", "over")
    print("%3s %5s %5s %14s %9s %5s %4s %10s %12s %7s %7s %6s" % hdr)
    for r in rows:
        print("%3s %5s %5s %14s %9s %5s %4s %10s %12s %7s %7s %6s" % (
            r["run_index"], r["steps"], r["winner_matches_frozen"],
            fmt(r["scored_break_even"], ".6f"),
            fmt(r["break_even_rel_error"], ".2e"),
            r["scored_equals_first_record"], r["n_decision_pair_BACKWARD"], r["any_BACKWARD_canonical"],
            r["scored_reachability"],
            fmt(r["first_stable_CU"], ".0f"), fmt(r["final_CU"], ".0f"), fmt(r["overrun_CU"], ".0f"),
        ))

    n = len(rows)
    canon = sum(r["break_even_is_canonical"] for r in rows)
    anyc = sum(r["any_BACKWARD_canonical"] for r in rows)
    reach_ok = sum(r["reachability_matches_frozen"] for r in rows)
    win_ok = sum(r["winner_matches_frozen"] for r in rows)
    cons = sum(1 for r in rows if r["scored_equals_first_record"])
    allgaps = [g for r in rows for g in json.loads(r["gaps"])]
    heads = sorted({tuple(json.loads(r["headroom_values_returned"])) for r in rows})
    print()
    print(f"n = {n}")
    print(f"  winner == frozen                    : {win_ok}/{n}")
    print(f"  scored reachability == frozen        : {reach_ok}/{n}")
    print(f"  scored break-even == canonical       : {canon}/{n}")
    print(f"  ANY decision-pair BACKWARD canonical : {anyc}/{n}")
    print(f"  scored BE == first record (convention): {cons}/{n}")
    print(f"  distinct headroom value sets returned : {heads}")
    print(f"  gaps (fields not establishable from the raw trace): {len(allgaps)}")
    for g in sorted(set(allgaps)):
        print(f"    - {g}")
    (DATA / f"{a.out}_metadata.json").write_text(json.dumps({
        "schema": "discover-boundary-c1-uncapped-breakeven-audit-v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "glob": a.glob,
        "frozen_reference": {"break_even": gt_be, "reachability": S.GT["reachability"], "winner": S.GT["winner"],
                             "headroom": S.GT.get("headroom", MISSING)},
        "runs": n,
        "missing_field_sentinel": MISSING,
        "scientific_recomputation": False,
    }, indent=2), encoding="utf-8")
    print("\nwrote", csv_path.name)
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main())
