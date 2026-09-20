---
name: junbo-research-gist
description: "Create or update Junbo Tong's research GIST working documents: concise, figure-led Chinese scientific briefs that preserve an existing GIST's chapter order and visual logic while replacing stale results with verified current evidence. Use when the user asks for a GIST, Gist工作文档, a v2/v3 update of an existing research brief, a Tencent/Word research summary built from a prior GIST, or a compact advisor-facing scientific story with figures and references. Preserve prior versions; version filenames only as v1, v2, v3, etc., never with labels such as 中文版、修订版、最终版、增补版 or 新版."
---

# Junbo Research Gist

Produce a GIST as an advisor-facing scientific working document: a compact canonical story supported by decisive figures, headline numbers and traceable references. Treat the previous GIST as the structural/style baseline, not as the source of truth for scientific values.

## Core workflow

1. **Recover the prior GIST.** If a previous GIST exists, preserve its chapter order, argument flow, approximate figure density and restrained academic style. Update by replacement and insertion rather than wholesale redesign.
2. **Resolve the current evidence.** Use verified data, frozen/audited analysis outputs and the current manuscript/repository before older Word/Tencent drafts. Do not let an old GIST override a newer validated result.
3. **Freeze the canonical story.** Reduce the project to one central question plus 3–6 dependent claims. Map each claim to a figure, number or external source.
4. **Build figure-first sections.** Each major section should normally follow `question -> figure -> headline number -> interpretation`. Keep the existing figure map when it is still scientifically valid.
5. **Update references with the science.** Put citation markers near claims and include a real bibliography. Prefer primary sources for model inputs, closest prior art for novelty, and a small number of strong context papers.
6. **Export and inspect.** If producing DOCX, also follow the `docx` skill and render every page for visual QA before delivery.

## Scientific story rules

- Write **Chinese-first** prose. Keep fixed technical terms in English when translation would reduce precision, e.g. `descriptor`, `microkinetic model`, `process reoptimization`, `Top-1`, `alpha*`, `oracle CU`.
- Keep **mechanism**, **framework**, **Agent**, and **provenance** separate:
  - mechanism = why a scientific ranking/behavior changes;
  - framework = how scales or analysis stages connect;
  - Agent = how finite compute is allocated inside the defined scientific chain;
  - provenance = where exact runs, hashes and engineering artifacts live.
- Put the physical/scientific story before the Agent story. Agent should not become the paper's main subject unless the user explicitly changes the project framing.
- Use `claim -> quantitative evidence -> comparison -> interpretation` for result prose.
- State supported mechanisms directly. Do not weaken them merely to sound cautious.
- If a new counterfactual or audit changes a previous conclusion, rewrite the conclusion rather than hiding the conflict.

## Default GIST architecture

Adapt as needed, but prefer this order for catalyst/process projects:

1. 研究问题
2. 多尺度框架 / scientific workflow
3. 主案例的 ranking change / main finding
4. uncertainty and decision stability
5. process reoptimization / operating consequence
6. backward design and reachability
7. decisive counterfactuals / causal tests
8. transfer case across reaction or system
9. mechanism comparison and preservation/control case
10. Agent / finite-compute decision allocation
11. Discussion
12. Conclusions
13. References

For the current Catalyst Economic Leverage project, preserve the established logic:

`atomic ranking -> economic ranking -> decision-frontier uncertainty -> process reoptimization -> backward target -> reachability -> cross-reaction transfer -> preservation control -> Agent compute allocation`.

## Figure rules

- The GIST is **figure-led**. Do not collapse a mature 8–10 figure scientific story into 2–3 decorative summary graphics.
- Prefer existing canonical figures from the repository when they remain correct. Redraw only when the source figure is stale, illegible, stylistically inconsistent, or the user asks for a new visualization.
- When redrawing, preserve the underlying data and scientific meaning; change presentation, not results.
- One figure should answer one named scientific question. Place a short Chinese interpretation directly below it.
- Use Chinese labels for explanatory diagrams when helpful; keep universally standard scientific notation and units unchanged.
- Do not insert screenshots of internal notes, version-control UI, terminal output, engineering manifests, or source tables unless explicitly requested.
- Avoid oversized poster-style composite figures inside a normal GIST unless the user specifically asks for a one-page overview.

## References

A GIST must include references when the scientific story depends on literature.

Use three layers:

1. **Direct source literature** — equations, datasets, catalyst states, calibration parameters.
2. **Closest prior art** — define what previous work already established and what this project adds.
3. **Context literature** — descriptor screening, uncertainty, TEA, autonomous science, etc.

Place `[1]`, `[2]`, etc. near the relevant prose, then give a bibliography at the end. Do not leave references as a disconnected final-page list with no in-text citation logic.

Prefer primary sources over reviews when a concrete model number comes from a paper. Keep the main GIST bibliography selective rather than exhaustive.

## Versioning and filenames

Treat version naming as a hard rule:

- Use only numeric versions: `GIST-v1`, `GIST-v2`, `GIST-v3`, ...
- For files, prefer `GIST-v2.docx`, `GIST-v3.docx`, etc.
- If a project prefix is required, use a stable prefix plus numeric version, e.g. `Catalyst-GIST-v3.docx`.
- **Never** append labels such as `中文版`, `修订版`, `最终版`, `增补版`, `新版`, `final`, `new`, or dates as a substitute for the version number unless the user explicitly requests them.
- Never overwrite an earlier GIST version unless the user explicitly tells you to do so.
- Do not put a visible “版本说明” or changelog box at the start of the GIST unless explicitly requested.

## Material to keep out of the main GIST

Do not expose internal project-control language in the document body:

- `可以写 / 不要写` tables;
- TODO/FIXME notes;
- claim-risk or defensive-writing notes;
- commit hashes, run IDs, frozen tags, CI details;
- internal prompts or Agent instructions;
- provenance engineering names;
- development history that does not advance the scientific argument;
- meta labels such as “中文版”“修订版”“增补版”.

Move necessary reproducibility detail to SI/repository/provenance, not the GIST narrative.

## Style

- Keep prose concise, natural and journal-like rather than report-like.
- Prefer short paragraphs over dense bullet stacks.
- Use black text, restrained academic formatting and readable body text of at least 10 pt unless a source template requires otherwise.
- Avoid decorative dashboards, excessive gradients, callout boxes and generic AI styling.
- Use tables only when a true comparison is clearer than prose or a figure.
- Do not repeatedly use rhetorical constructions such as “不是……而是……”. State the scientific relationship directly.

## Quality check before delivery

Verify all of the following:

- The old GIST still exists and the new artifact uses the next numeric version.
- Every headline number matches the current source of truth.
- No stale claim survived a newer counterfactual or audit.
- The central story can be summarized in four sentences or fewer.
- Major claims each have a figure or quantitative anchor.
- Figures are numerous enough to preserve the project's scientific evidence chain.
- References appear in-text and in the bibliography.
- Agent material follows, rather than replaces, the physical scientific story.
- No version-note box, internal author instruction, TODO or engineering/provenance clutter remains.
- If DOCX was created, render and inspect every page before sharing it.

For a more explicit section template and editing pattern, read `references/gist-template.md`.
