# Data and code availability

Status: **the evidence is vendored and validated.** The DOI placeholder below is the only
item still outstanding, and it is minted from the repository rather than from a separate
upload.

## What was done, and why this way

The DISCOVER V1 protocol and every trace behind the agent results are vendored into this
repository at `provenance/discover_v1/source_harness/`, content-addressed by
`SOURCE_MANIFEST.json` and checked by `ci/validate_discover_v1_provenance.py`. This is the
same pattern as the NH3-FINAL-1.1 bundle, and it was chosen over an external archive after
measuring what it actually costs.

| | |
|---|---|
| Files vendored | 3,778 |
| Bytes vendored | 207.0 MiB |
| `trace.json` files | 1,263 (matches the manuscript anchor) |
| Growth of `.git` | 12 MiB → 38 MiB |
| Largest single object | 898 KiB |

The evidence is almost entirely JSON, and 3,721 of the evidence files are only 2,117
distinct blobs, so content-addressed storage deduplicates them at no cost. An external
deposit was unnecessary: it would have split one record across two hosts and made the
scorer unreadable without a download, for no saving that matters.

**One deliberate exclusion.** `cache/` holds three precomputed response-surface `.npz`
files totalling 221 MiB. They are derived artefacts, regenerable from the deterministic
harness; they are already-compressed binary that version control cannot pack; and the
largest is 128 MiB, above the 100 MiB per-file limit of the hosting service. They are
excluded by policy, and each one's SHA-256 and the reason are recorded in the manifest's
`excluded_files`, so the omission is content-addressed rather than silent.

## What the validator checks

`ci/validate_discover_v1_provenance.py` returns `PROVENANCE_VALIDATED_READY_FOR_LOCK` only
when all four hold. Current run: **all four pass.**

1. **Frozen pins.** The 15 protocol files and `discover/formal_e.py` reproduce their pinned
   SHA-256. The expected values are hardcoded in the validator, not read from the bundle's
   own manifest — a bundle cannot vouch for itself, so regenerating the manifest cannot
   launder a changed protocol file.
2. **Manifest integrity in both directions.** Every listed file is present and matches, and
   no file exists in the bundle that the manifest does not list. The second direction is the
   one that catches a file quietly added later.
3. **Evidence completeness.** All five run families present; `trace.json` count equals the
   1,263 the manuscript reports.
4. **Declared exclusions.** Anything not vendored carries a SHA-256 and a stated reason.

`.gitattributes` marks the bundle `-text`, so line-ending normalisation cannot alter the
bytes on checkout and invalidate the hashes on someone else's machine.

This also closes a defect: SI §7 asserts a SHA-256 for `formal_e.py`. That file is now in
the repository, so the assertion is resolvable by a referee instead of being a claim about
a file they cannot obtain.

## Remaining step: mint the DOI from the repository

Journals want a DOI; the repository is already the complete record, so the DOI should be
minted *from* it rather than from a parallel upload.

1. Enable the **GitHub–Zenodo integration** for `stloendays/Catalyst-Essay`.
2. Tag and publish a GitHub release:

```bash
git tag -a discover-v1-deposit-1.0 -m "Frozen DISCOVER V1 protocol and C1 evidence, validated"
git push origin discover-v1-deposit-1.0
```

3. Publishing the release archives the repository at that tag and mints a DOI
   automatically. No separate upload, and the archived bytes are by construction the bytes
   the validator passed.
4. Zenodo issues two DOIs. The **concept DOI** always resolves to the newest version; the
   **version DOI** resolves to exactly the archived tag. **Cite the version DOI** — the claim
   being supported is about specific bytes.
5. In the Zenodo record, set the license (the data are CC BY 4.0; the code keeps the
   repository's own license — do not put code under CC BY) and add `isSupplementTo`
   pointing at the manuscript DOI once it exists.

## Draft: Data availability

> All data supporting this work are in the manuscript repository at
> [https://github.com/stloendays/Catalyst-Essay], archived at DOI [10.5281/zenodo.XXXXXXX].
> The agent evidence — 1,263 scored traces across `DISCOVER_FORMAL_RUNS_V1`,
> `DISCOVER_CROSS_MODEL_V1`, `DISCOVER_BOUNDARY_C1` and `discover_runs`, with the
> corresponding run metadata and per-trace score files — is vendored at
> `provenance/discover_v1/source_harness/` under a SHA-256 manifest covering every file.
> The frozen NH3-FINAL-1.1 source harness, including the canonical run
> `outputs/nh3_final_20260905T134204Z` and its closure data, is vendored at
> `provenance/nh3_final_1_1/`. Precomputed response-surface caches are omitted as
> regenerable derived artefacts; their SHA-256 values and the reason are recorded in the
> manifest.

## Draft: Code availability

> The frozen DISCOVER V1 protocol — task, prompt, 11-action schema, compute-unit cost
> model, scorer, stopping rule and the A–D baseline policies — together with the policy-E
> driver, the deterministic multiscale harness and all analysis and figure-rendering
> scripts, is available in the manuscript repository at
> [https://github.com/stloendays/Catalyst-Essay] and archived at DOI
> [10.5281/zenodo.XXXXXXX]. The protocol files are pinned by SHA-256 in
> `DISCOVER_FROZEN_V1.json` and were verified 15/15 before and after every batch of runs
> reported here. `ci/validate_discover_v1_provenance.py` re-verifies the pins, the manifest
> in both directions, the trace count and the declared exclusions, and reports
> `PROVENANCE_VALIDATED_READY_FOR_LOCK`. Figures are regenerated from the committed data
> files by the scripts in `figures/`, each carrying a SHA-256 render manifest.

## Draft: one sentence for Methods

> Every reported quantity is regenerated from frozen, content-addressed artefacts by
> scripts under version control: protocol files are pinned by SHA-256 and re-verified
> before and after each batch, figure assets carry render manifests, and the derived data
> tables are rebuilt from the raw traces rather than transcribed.

## Checklist before submission

- [x] `prepare_discover_v1_bundle.py` run; its frozen-verification gate passed 15/15
- [x] `validate_discover_v1_provenance.py` returns `PROVENANCE_VALIDATED_READY_FOR_LOCK`
- [x] `.gitattributes` protects the bundle bytes from line-ending normalisation
- [x] Exclusions declared with SHA-256 and reason
- [x] SI §7's `formal_e.py` hash now resolvable in-repo
- [ ] GitHub–Zenodo integration enabled
- [ ] Release tag published and the version DOI pasted into the manuscript
- [ ] `isSupplementTo` linked once the manuscript DOI exists
