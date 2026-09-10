# Claim-to-evidence audit — Addendum A2: NH3 provenance closure

Date: **2026-09-10**

This addendum closes the remaining NH3-FINAL-1.1 provenance dependency identified in the first claim-to-evidence audit.

## Final validation state

`artifacts/nh3_final_1_1_provenance/status.txt` = **`PROVENANCE_VALIDATED_READY_FOR_LOCK`**.

Cross-platform GitHub Actions validation established:

- 13/13 canonical numerical anchors PASS;
- 6/6 F1-F6 evidence classes present;
- 6/6 canonical figure mappings present;
- 28/28 manifest-listed source files present;
- 0 source-manifest hash mismatches;
- 0 scientific model reruns.

The canonical source bundle is vendored at `provenance/nh3_final_1_1/source_harness/` and is byte-preserved across platforms by `.gitattributes`.

## Audit-status change

The following NH3 claim families move from provenance class **B / HOLD** to **A / directly traceable**:

- atomic and optimized economic rankings;
- Fe/Ru/Os reduced catalyst-dependent costs;
- Top-3 and full-15 rank correlations;
- Monte Carlo feasibility and ranking-stability quantities;
- Ru activity-only break-even target;
- scaling-consistent activity headroom and strict-scaling Ru minimum cost.

Machine-readable claim status is updated in `data/claim_evidence_registry_2026-09-10.csv`.

## Figure-lock change

F1-F6 move from **HOLD** to **LOCKED**. Exact canonical SVG paths, source SHA-256 values and Git blob SHAs are recorded in `docs/NH3_FINAL_1_1_FIGURE_LOCK_2026-09-10.md` and `data/figure_lock_registry_2026-09-10.csv`.

This closure does not alter any NH3-FINAL-1.1 scientific value. It only restores direct source provenance and cross-platform byte identity.

## Remaining evidence boundary

The only main Figure 9A limitation remains the historical cross-reaction normalized-leverage number: **273–410 (~328 midpoint)** is not a current FINAL-1.1 claim because the original pre-audit NH3 TOF economic-leverage metric implementation has not been established. F9A remains qualitative-only.

With this exception explicitly bounded, the core NH3, MeOH, rank-preservation and Agent evidence chains are ready for manuscript production.
