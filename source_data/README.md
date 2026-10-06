# Source Data

One workbook per figure, in the manuscript numbering of 2026-10-07:

| Workbook | Figure | Renderer |
|---|---|---|
| `SourceData_Fig1.xlsx` | Fig. 1, ammonia ranking reversal | `figures/composite/fig1/make_fig1.py` |
| `SourceData_Fig2.xlsx` | Fig. 2, laboratory leaderboards vs plant-cost leaderboards | `figures/composite/fig_field/make_fig_field.py` |
| `SourceData_Fig3.xlsx` | Fig. 3, metal price and process optimization | `figures/composite/fig2/make_fig2.py` |
| `SourceData_Fig4.xlsx` | Fig. 4, backward design | `figures/composite/fig3/make_fig3.py` |
| `SourceData_Fig5.xlsx` | Fig. 5, methanol Re/TiO2 mechanism | `figures/composite/fig4/make_fig4.py` |
| `SourceData_Fig6.xlsx` | Fig. 6, process routes and Au/TiO2 control | `figures/composite/fig5/make_fig5.py` |
| `SourceData_EDFig1.xlsx` … `SourceData_EDFig7.xlsx` | Extended Data Figs 1–7 | `figures/extended_data/render_extended_data.py` |

- **Layout.** Each workbook opens with a `README` sheet that lists, for every sheet and block, the source file and any
  filter. Then comes one sheet per panel. A panel that plots several arrays (a curve and points, say, or a bar chart
  plus its error bars) holds them as titled blocks on its sheet.
- **Schematic panels.** Panels that are only a schematic or a rendered structure get a sheet that says so.
- **Where the numbers come from.** Every number is read from the CSV or JSON file the renderer reads, with the same
  filters and arithmetic. Values that a renderer types into a label are written here from their source file, and the
  block note says which.
- **Extended Data.** These tables come from `figures/extended_data/ed_data.py`, the same module the figures are drawn
  from.

Build (about 10 s):

```
D:\Research\CatalystForge\.venv\Scripts\python.exe tools/build_source_data.py
```
