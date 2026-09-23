# Manuscript editorial locks

Snapshot: **2026-09-23**

These are author-level editorial decisions for the current manuscript. They should be preserved in future manuscript polishing unless the author explicitly reopens the specific item.

## LOCK-01 — Agent manuscript role

The manuscript-level role of the Agent is **the scaling layer / reusable execution pattern of the multiscale analysis**.

Required interpretation:

- Reaction-specific kinetic, process and economic tools remain responsible for the scientific calculations.
- The language-model policy selects which deterministic calculations to invoke for each decision instance.
- This separation makes the ranking–parity–reachability analysis repeatedly executable across candidate sets without manually scripting a complete calculation sequence for every case.
- The non-binding 5,000-CU result is used to explain the mechanism of the budget effect: budget pressure induces search compression, while a non-binding budget removes that pressure and permits additional post-stability computation.
- The non-binding result **must not be used to demote the Agent to merely a budget-saving heuristic or to replace the manuscript-level scaling/reusability claim**.
- Do not rewrite the Discussion into a conclusion that the Agent's main role is only that it is computationally advantageous under constrained budgets. The budget study is a mechanistic qualification of the scaling layer, not a replacement for it.

This lock remains active unless the author explicitly asks to reconsider the Agent's manuscript-level role.

## LOCK-02 — Reader-facing semantic names

Reader-facing manuscript, figure, README and supervisor-facing documents should use the semantic names defined in `docs/SCIENTIFIC_NAMING.md`. Development-version labels remain only where provenance or implementation traceability requires them.

Do not create new reader-facing `V1.x`-style names unless the author explicitly asks for versioned nomenclature.


## LOCK-03 — No legacy-name mapping in reader-facing documents

Do not display internal development identifiers or explicit legacy-name → scientific-name mappings in reader-facing material.

- Use the scientific name directly.
- Do not write constructions of the form `internal label → scientific label`.
- Do not add a “historical provenance key” column to README, STATUS, manuscript-facing tables or naming guides.
- Historical identifiers may remain only where they are operationally necessary for provenance, frozen manifests, implementation paths or Git history.
- If a reader-facing document needs to point to provenance, link to the provenance location without reproducing the internal development identifier in the prose.

This lock remains active unless the author explicitly asks to expose historical identifiers.
