# Figure 8 — Origin rebuild, 2026-09-23

The build behind the canonical Figure 8 assets one directory up
(`../F08_MeOH_selectivity_recycle_D01v3.{svg,pdf,png}`), promoted on 2026-09-23.
It re-renders the same frozen D01 v3 inputs: **the science is unchanged**, only
the rendering is.

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
export.

Every text object in an Origin export carries a stray rule along it at cap
height. It is removed from the **SVG**; the PNG is never edited, because the rule
sits exactly on the top bar of capital letters.

```
python f08_prep.py                               # Origin inputs, with the frozen-value guards
# build the two panels in Origin, export each as SVG
clean_origin_export.py  F08_panel_a.svg          # strips 14 text rules
clean_origin_export.py  F08_panel_b.svg          # strips 10
chrome --headless=new --force-device-scale-factor=1 --default-background-color=FFFFFFFF
       --window-size=2400,1837 --screenshot=F08_panel_x.png file:///F08_panel_x.svg   # one command
python render_composite.py ..                    # -> ../F08_MeOH_selectivity_recycle_D01v3.{svg,png,pdf}
```

`render_composite.py` calls `compose_svg.py`, which crops each panel to its ink
box, nests both in one 183-mm SVG, prefixes element ids per panel, and converts
Origin's single-rectangle clipping masks to clip paths. The masks matter: PDF
writers flatten masked content into a bitmap, so with them left in place every
curve in the PDF was a raster. The PDF and PNG are then printed and rasterised
from that one SVG, so the three canonical files cannot drift apart.

`clean_origin_export.py` lives in the PUR-NEW analysis tree; the measured Origin
behaviour behind all of this is recorded in the `nature-figures` skill's
`references/origin-facts.md`.

## Files

| File | What |
|---|---|
| `F08_panel_a.svg` / `F08_panel_b.svg` | cleaned vector, one per panel |
| `F08_panel_a.png` / `F08_panel_b.png` | rasterised panels; `compose_svg.py` measures ink boxes on them |
| `f08_panel_a.csv`, `f08_panel_b.csv`, `f08_panel_b_highlight.csv` | Origin inputs, generated |
| `f08_prep.py` | regenerates those CSVs from the frozen sources, with the guards |
| `compose_svg.py` | panels → one vector SVG |
| `render_composite.py` | SVG → canonical `.svg` / `.pdf` / `.png` |
| `png_compose.py` | PNG reader used by `compose_svg.py` (and the earlier raster-only composite) |

## Status

**Locked** on 2026-09-23. `../F08_RENDER_SHA256.txt` pins the two frozen inputs,
every script and panel above, and the three canonical outputs; CI re-verifies it
on every push. The 2026-09-10 R render it replaced remains in git history, and
its renderer (`../render_F08_selectivity_recycle.R`) still runs on CI as a
reference without writing to `figures/`.
