# Figure 8 — Origin rebuild, 2026-09-23

A re-render of Figure 8 from the same frozen D01 v3 inputs. **The science is
unchanged and the locked assets one directory up are untouched**; this is a
rendering alternative, not a new result.

## Why

The committed render (`../F08_MeOH_selectivity_recycle_D01v3.*`) carries four
layout defects, visible at full size:

| Defect | In the rebuild |
|---|---|
| `2% canonical` annotation drawn on top of the legend entry `5 wt% Re / 200 C` | legend replaced by direct series labels; annotation sits at the top of the 2% line |
| panel b's axis title `Local economic leverage \|d ln C / d ln x\|` truncated at the right edge | complete |
| panel letter `b` placed outside the left edge of panel a; panel b unlabelled | `a` and `b` each at their own panel's top left |
| y-axis title colliding with the tick labels | clear |

Also corrected: `0.376` was clipped at panel b's frame; `EUR t-1` is now a real
superscript and `CH4` a real subscript.

## Provenance

`f08_prep.py` regenerates the Origin inputs from the frozen CSVs and asserts,
exactly as `../render_F08_selectivity_recycle.R` does, that

- the purge sweep has 396 levels spanning 0.5–40 %, and
- the three leverage values equal the frozen D01 v3 values to within 1e-12.

It stops rather than plotting if either fails. Values plotted:

```
2 % canonical NPC   5 wt% Re / 200 C  943.30  (economic winner)
                    1 wt% Re / 200 C  966.96
                    1 wt% Re / 250 C  974.99  (upstream STY-per-g-Re winner)
                    5 wt% Re / 250 C 1258.17
leverage at 5 wt% Re / 250 C   STY 0.0028943 | conversion 0.0588278 | CH4 suppression 0.3757939
                               CH4/conversion = 6.39x   CH4/STY = 129.84x
```

## Build

Origin 2024 via the originlab MCP, one graph per panel — multi-layer panel
positioning is a silent no-op on this install, so the panels are composed after
export by `png_compose.py`.

Every text object in an Origin export carries a stray rule along it at cap
height. It is removed from the **SVG**, which is then rasterised; the PNG is
never edited, because the rule sits exactly on the top bar of capital letters.

```
clean_origin_export.py  <panel>.svg          # strips the rules (14 in a, 10 in b)
chrome --headless=new --force-device-scale-factor=1 \
       --default-background-color=FFFFFFFF --window-size=2400,1837 \
       --screenshot=<panel>.png file:///<panel>.svg
png_compose.py F08_panel_a.png F08_panel_b.png F08_...origin.png
```

`clean_origin_export.py` lives in the PUR-NEW analysis tree; the measured Origin
behaviour behind all of this is recorded in the `nature-figures` skill's
`references/origin-facts.md`.

## Files

| File | What |
|---|---|
| `F08_MeOH_selectivity_recycle_origin.png` | composed figure, 4061 × 1761 (≈ 560 dpi at 183 mm) |
| `F08_panel_a.svg` / `F08_panel_b.svg` | cleaned vector, one per panel — the editable form |
| `F08_panel_a.png` / `F08_panel_b.png` | the rasterised panels the composite is built from |
| `f08_panel_a.csv`, `f08_panel_b.csv`, `f08_panel_b_highlight.csv` | Origin inputs, generated |
| `f08_prep.py` | regenerates those CSVs from the frozen sources, with the guards |
| `png_compose.py` | ink-box crop, height match, side-by-side composition |

## Status

Not promoted. `docs/F8_METHANOL_FIGURE_LOCK_SPEC.md` still points at the locked
render, and `../F08_RENDER_SHA256.txt` still describes it. Promoting this one
means updating both, and that is a decision about the figure, not about the
rendering.
