# DISCOVER V1 provenance validation

Status: **PROVENANCE_VALIDATED_READY_FOR_LOCK**

Checked at: `2026-09-17T07:31:41.622390+00:00`

Provenance only. No LLM was called, no trace was re-scored, no frozen file was written.

## Frozen protocol pins

- 15-pin manifest: 15/15 exact SHA-256 match
- `discover/formal_e.py`: MATCH

## Manifest integrity

- manifest present: True
- listed files: 3778
- missing listed files: 0
- hash mismatches: 0
- files on disk not listed in the manifest: 0

## Evidence completeness

- trace.json found: 1263 (anchor 1263)
- `DISCOVER_FORMAL_RUNS_V1`: 880 file(s)
- `DISCOVER_CROSS_MODEL_V1`: 445 file(s)
- `DISCOVER_BOUNDARY_C1`: 1136 file(s)
- `discover_runs`: 722 file(s)
- `outputs`: 538 file(s)

## Declared exclusions

- 3 file(s) deliberately not vendored, each carrying a SHA-256 and a reason
  - `cache/response_fc259c5311744ccc_-2.6_3.4_0.005_14136.npz` (122.3 MiB)
  - `cache/response_fc259c5311744ccc_-2.6_3.4_0.005_6636.npz` (57.4 MiB)
  - `cache/response_fc259c5311744ccc_-2.6_3.4_0.005_3636.npz` (31.4 MiB)

Reason(s) recorded:
- derived response-surface cache: regenerable, binary-incompressible, largest member exceeds the 100 MiB per-file hosting limit
