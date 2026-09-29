# Manuscript source of truth — 2026-09-29

This page is the publication-facing **single truth hierarchy** for the current manuscript. It distinguishes frozen canonical results, audited derived extensions and calculations that are prepared but not yet promoted.

## Rule

A number may enter the main manuscript only when it is either:

1. **CANONICAL** — frozen in the provenance-closed scientific source; or
2. **DERIVED-A** — deterministically derived from canonical sources with a committed reproducible audit.

A prepared calculation with no completed output is **PENDING** and must not be written as a scientific conclusion.

## NH3 — canonical FINAL-1.1

| Quantity | Current value | State | Authoritative source |
|---|---:|---|---|
| atomic top-3 | Ru > Os > Fe | CANONICAL | FINAL-1.1 results |
| economic top-3 | Fe > Ru > Os | CANONICAL | FINAL-1.1 results |
| Fe / Ru / Os cost | 15.292 / 22.031 / 25.832 USD/t NH3 | CANONICAL | FINAL-1.1 results |
| Top-3 Spearman / Kendall | -0.50 / -0.33 | CANONICAL | rolling rank closure |
| full-15 raw Spearman | 0.929 | CANONICAL | rolling rank closure |
| Fe feasibility | 79.9% | CANONICAL | descriptor MC |
| Fe economic Top-1 | 68.1% (681/1000) | DERIVED-A | frozen descriptor-MC draws |
| atomic-to-economic Top-1 survival | 28.2% | CANONICAL | descriptor MC |
| Top-3 actionable | 94.0% | CANONICAL | descriptor MC |
| Ru activity-only parity | 201.22x | CANONICAL | backward sweep |
| scaling gain at 673 K | 1.090x | CANONICAL | scaling reachability |
| maximum state-specific scaling gain | 2.525x | CANONICAL | scaling reachability |
| strict-scaling minimum Ru cost | 21.398 USD/t at E_N = -1.215 eV | CANONICAL | scaling reachability |

**Semantic lock:** 68.1% is the probability that Fe is the economic Top-1 in the frozen descriptor draws. **28.2% is a different metric**: the probability that the atomistic Top-1 identity survives into the economic Top-1.

## NH3 — audited derived extensions

| Quantity | Current value | State | Authoritative source |
|---|---:|---|---|
| Ru at Fe metal price | 14.712 USD/t | DERIVED-A | 2026-09-20 equal-price audit |
| Ru-Fe parity metal price | 163.76 USD/kg Ru | DERIVED-A | full Ru price sweep |
| joint cost MC P(C_Fe < C_Ru) | 1.000 (5000/5000) | DERIVED-A | preregistered cost MC |
| alpha* p05 / median / p95 | 70.78x / 174.27x / 462.00x | DERIVED-A | cost MC |
| direct target: 10 y + 99% recovery | alpha_req <= 2.41794x | DERIVED-A | 53-state target audit |
| direct target: 15 y + 99% recovery | alpha_req <= 1.74213x | DERIVED-A | 53-state target audit |
| direct target: 20 y + 99% recovery | alpha_req <= 1.40129x | DERIVED-A | 53-state target audit |
| direct target: 20 y + 98% recovery | alpha_req <= 2.41794x | DERIVED-A | 53-state target audit |

The direct activity/lifecycle values are **backward targets**, not physical-reachability results. The 53-state restriction makes them conservative upper bounds on the activity multiplier required for parity.

## NH3 — strict-scaling lifecycle reachability closure

The joint backward target has now been tested against the **strict E_N scaling manifold** with all **14,136 FINAL-1.1 process states** and no new DFT.

| Quantity | Current value | State | Authoritative source |
|---|---:|---|---|
| canonical strict-scaling anchor | 21.397873 USD/t at E_N = -1.215 eV | CANONICAL | FINAL-1.1 scaling reachability |
| critical lifecycle factor q* = (1-r)/L | 4.40683454e-4 y^-1 | DERIVED-A | strict-scaling lifecycle audit |
| equivalent Ru parity price on 10-y basis | 237.319 USD/kg | DERIVED-A | strict-scaling lifecycle audit |
| strict-scaling parity descriptor/state | E_N = -1.230 eV; 425 C / 190 bar / 30 C; 4.298 m3 | DERIVED-A | strict-scaling lifecycle audit |
| best point inside L<=20 y, r<=0.99 | 20 y + 99%; 15.36249 USD/t | DERIVED-A | strict-scaling lifecycle audit |
| miss versus Fe at tested-box corner | +0.07078 USD/t (+0.46%) | DERIVED-A | strict-scaling lifecycle audit |
| required recovery at 20 y | 99.1186% | DERIVED-A | strict-scaling lifecycle audit |
| required lifetime at 99% recovery | 22.69 y | DERIVED-A | strict-scaling lifecycle audit |

**Decision:** the prespecified lifecycle box (**life <= 20 y; recovery <= 0.99**) does **not** intersect the strict scaling manifold, although the boundary lies just outside it.

**Semantic lock:** the **2.525x** all-state scaling gain remains a state-specific activity diagnostic. It is not used as a uniform activity multiplier in the joint reachability result.

Authoritative derived files:

- `analysis/fe_bridge_backward_2026_09_29/scaling_lifecycle_exact_summary.json`
- `analysis/fe_bridge_backward_2026_09_29/scaling_lifecycle_exact_keypoints.csv`
- `analysis/fe_bridge_backward_2026_09_29/scaling_lifecycle_exact_global_boundary.csv`
- `analysis/fe_bridge_backward_2026_09_29/run_statewise_strict_scaling_lifecycle.py`

## First NH3 inversion layer

The layer-wise causal audit is:

```text
intrinsic activity                 Ru > Os > Fe
minimum catalyst demand            Ru > Os > Fe
full process, Ru priced as Fe      Ru remains below Fe in cost
actual-price inventory economics   Fe < Ru < Os   <-- first explicit flip
full canonical optimization        Fe < Ru < Os   <-- flip amplified
```

The manuscript interpretation is therefore: **metal-price-weighted catalyst inventory triggers the Fe-Ru inversion; the coupled process response amplifies the resulting cost gap.**

## Other active scientific families

- **Methanol recycle-economics model:** MEOH-D01-v3.
- **Au/TiO2 rank-preservation control:** V1.1, with V1.3 as supporting semi-open robustness.
- **Adaptive Catalyst Screening Agent:** DISCOVER V1 + DISCOVER-BOUNDARY-C1.

Their current manuscript-facing values remain in `data/manuscript_headline_results_2026-09-20.csv` and `docs/RESULTS_AT_A_GLANCE.md`.

## Machine gates

- backward direct-target reproducibility: GitHub Actions run **36516398387 — PASS**
- section-aware live manuscript truth audit: GitHub Actions run **36516694081 — PASS**

The active automated manuscript audit is:

`tools/audit_live_manuscript_truth.py`

The older phrase-sensitive checker is retained for development history but is no longer the publication gate.

## Retired/superseded values

Historical FINAL-1.0 values and retired cross-reaction metrics remain traceable only through `docs/RETIRED_RESULTS.md`; they must not be reintroduced into current figures, captions or manuscript text.
