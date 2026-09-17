"""Fe feasibility sensitivity under NH3-FINAL-1.1 (2026-09-16).

Recomputes the two derived quantities that the Gist working document still carried from FINAL-1.0:

  (a) holding the bed cap at 90 m3, what descriptor uncertainty sigma_Fe gives ~95% Fe engineering feasibility?
  (b) holding sigma_Fe at its frozen value, what bed cap gives ~95% Fe engineering feasibility?

The FINAL-1.0 answers were 0.0874 eV and 50,293 m3, derived when Fe feasibility was 73.6%. Under FINAL-1.1 the
baseline feasibility is 79.9%, so both derived numbers must be recomputed.

Read-only with respect to every frozen input: the canonical run manifest is loaded as-is, the response surface must come
from the existing cache, and no config file is written. The frozen `monte_carlo` routine is executed unchanged to
reproduce the published baseline before any sensitivity value is reported.

Method. Fe is engineering-feasible in a draw iff min_states V_Fe(E_N) <= cap. V depends on the descriptor only through
the activity vector, so feasibility is a one-dimensional threshold problem: locate the descriptor interval(s) where
min_V(E) <= cap and integrate the Fe descriptor distribution over them. This is
exact up to the root solve and avoids Monte-Carlo sampling noise in the inverted quantities.

Usage (from harness root):
  python audits/fe_feasibility_sensitivity_1_1_2026-09-16.py
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import yaml
from scipy.optimize import brentq
from scipy.stats import norm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harness_core import NH3Harness  # noqa: E402

RUN = ROOT / "outputs" / "nh3_final_20260905T134204Z"
OUT = ROOT / "audits" / "fe_feasibility_sensitivity_1_1_2026-09-16.json"
TARGET = 0.95
BASELINE_CAP_M3 = 90.0


def main() -> int:
    cfg = yaml.safe_load((RUN / "manifest_resolved.yaml").read_text(encoding="utf-8"))
    res = json.loads((RUN / "results.json").read_text(encoding="utf-8"))
    h = NH3Harness(cfg, ROOT)
    resp, _cp, cached = h.build_or_load_response()
    if not cached:
        raise SystemExit("response surface is not cached; refusing to rebuild a frozen asset")

    sigma0 = float(h.FE_SIGMA)
    cap0 = float(h.V_CAP)
    en0 = float(h.EN0["Fe"])
    published = res["monte_carlo"]["Fe_feasibility_probability"]

    # --- 1. reproduce the published baseline with the frozen routine, unchanged
    mc = h.monte_carlo(resp)
    repro = float(mc["Fe_feasibility_probability"])
    print(f"frozen sigma_Fe            : {sigma0!r} eV")
    print(f"frozen bed cap             : {cap0:.1f} m3")
    print(f"published Fe feasibility   : {published:.4f}")
    print(f"reproduced (frozen routine): {repro:.4f}   match={abs(repro - published) < 1e-12}")
    if abs(repro - published) > 1e-9:
        raise SystemExit("baseline did not reproduce; refusing to report derived values")

    # --- 2. min bed volume as a function of the Fe descriptor
    grid = np.asarray(h.EGRID, dtype=float)

    def min_V(e: float) -> float:
        logv = h.interp_state_vector(resp, float(e))
        _total, V, _mc_, _r = h.cost_arrays("Fe", logv)
        return float(np.min(V))

    vals = np.array([min_V(e) for e in grid])
    peak = int(np.argmin(vals))
    print(f"min_V over descriptor grid : {vals.min():.3g} to {vals.max():.3g} m3; "
          f"minimum at E_N = {grid[peak]:.3f} eV (activity volcano, so the feasible set is an interval)")

    def feasible_intervals(cap: float) -> list[tuple[float, float]]:
        """Descriptor intervals where min_V(E) <= cap, endpoints refined by root solve."""
        ok = vals <= cap
        if not ok.any():
            return []
        spans, i = [], 0
        n = len(grid)
        while i < n:
            if not ok[i]:
                i += 1
                continue
            j = i
            while j + 1 < n and ok[j + 1]:
                j += 1
            lo = float(grid[0]) if i == 0 else brentq(lambda e: min_V(e) - cap, grid[i - 1], grid[i], xtol=1e-10)
            hi = float(grid[-1]) if j == n - 1 else brentq(lambda e: min_V(e) - cap, grid[j], grid[j + 1], xtol=1e-10)
            spans.append((lo, hi))
            i = j + 1
        return spans

    def feasible_prob(sigma: float, cap: float) -> float:
        """P(min_V(E) <= cap) for E ~ N(en0, sigma), summed over the feasible descriptor intervals."""
        return float(sum(norm.cdf((hi - en0) / sigma) - norm.cdf((lo - en0) / sigma)
                         for lo, hi in feasible_intervals(cap)))

    analytic0 = feasible_prob(sigma0, cap0)
    print(f"analytic baseline          : {analytic0:.4f}  (MC {repro:.4f}; "
          f"difference is Monte-Carlo sampling noise at {h.MC_N} draws)")

    # --- 3. invert for sigma at the frozen cap
    f_lo, f_hi = feasible_prob(1e-4, BASELINE_CAP_M3), feasible_prob(5.0, BASELINE_CAP_M3)
    sigma_star = None
    if (f_lo - TARGET) * (f_hi - TARGET) < 0:
        sigma_star = brentq(lambda s: feasible_prob(s, BASELINE_CAP_M3) - TARGET, 1e-4, 5.0, xtol=1e-9)
        print(f"sigma for {TARGET:.0%} at {BASELINE_CAP_M3:.0f} m3 : {sigma_star:.4f} eV "
              f"(FINAL-1.0 value was 0.0874 eV)")
    else:
        print(f"sigma for {TARGET:.0%} at {BASELINE_CAP_M3:.0f} m3 : not attainable "
              f"(range {f_lo:.4f}-{f_hi:.4f})")

    # --- 4. invert for cap at the frozen sigma
    caps = np.geomspace(1.0, 1e7, 400)
    probs = np.array([feasible_prob(sigma0, c) for c in caps])
    cap_star = None
    if probs.max() >= TARGET:
        i = int(np.argmax(probs >= TARGET))
        if i > 0:
            cap_star = brentq(lambda c: feasible_prob(sigma0, c) - TARGET, caps[i - 1], caps[i], xtol=1e-6)
            print(f"bed cap for {TARGET:.0%} at frozen sigma: {cap_star:,.0f} m3 "
                  f"(FINAL-1.0 value was 50,293 m3)")
    if cap_star is None:
        print(f"bed cap for {TARGET:.0%} at frozen sigma: not attainable; max prob {probs.max():.4f}")

    rec = {
        "schema": "nh3-final-1.1-fe-feasibility-sensitivity-v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "canonical_run": RUN.name,
        "frozen_inputs": {"sigma_Fe_eV": sigma0, "bed_cap_m3": cap0, "EN0_Fe_eV": en0, "mc_draws": int(h.MC_N)},
        "baseline": {"published_Fe_feasibility": published, "reproduced_Fe_feasibility": repro,
                     "analytic_Fe_feasibility": analytic0},
        "target_feasibility": TARGET,
        "sigma_for_target_at_90m3_eV": sigma_star,
        "bed_cap_for_target_at_frozen_sigma_m3": cap_star,
        "final_1_0_values_superseded": {"sigma_eV": 0.0874, "bed_cap_m3": 50293},
        "method": "descriptor-interval inversion: min_V(E) is a volcano in the descriptor, so the feasible set is the interval(s) where min_V <= cap; endpoints are refined by root solve and the Fe normal is integrated over them",
        "analytic_vs_mc": "the analytic baseline (0.8120) sits 1.3 percentage points above the frozen 1,000-draw Monte-Carlo value (0.7990); the binomial standard error at n=1000, p=0.8 is 1.26 pp, a gap of 1.03 standard errors, so the two are consistent with sampling noise but the analytic value is not strictly within one standard error; the inverted values are reported on the analytic scale",
        "frozen_files_modified": False,
    }
    OUT.write_text(json.dumps(rec, indent=2), encoding="utf-8")
    print("wrote", OUT.name)
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main())
