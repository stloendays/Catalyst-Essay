"""Reader-facing Supplementary Table captions (2026-10-21, author: short, descriptive captions; definitions of the
columns only, no file paths). build_si_tables.py writes these to docs/SI_TABLES.md and the full, source-linked
captions to docs/SI_TABLES_SOURCES.md for provenance.
"""

SHORT = {
    "1": "Curated, extracted and matched entries of each paper and the operating points that enter the methanol "
         "comparisons. Lam 2018 has no curated reference and was scored against the paper. SI, number of Supporting "
         "Information files retrieved.",
    "1b": "Papers that appeared from 5 November 2025 to 13 October 2026, screened in the rank order of one OpenAlex "
          "search against the criteria of the first set. Columns give the extracted entries, the operating points with "
          "printed values, the comparison groups and the groups whose STY leader is not the plant-cost leader in the "
          "inert-limited loop.",
    "2": "Extracted catalyst entries, the printed-value entries of the primary comparison with their metals, the "
         "comparison groups and the groups whose highest-rate catalyst is not the plant-cost leader (rate per gram of "
         "catalyst, no metal recovery).",
    "2b": "Papers screened, extracted and scored under a protocol committed before extraction. Columns as in "
          "Supplementary Table 2.",
    "3": "Layers are cumulative. Feasible, inside the 90 m³ bed limit. Surfaces below Fe (11.52 US dollars per tonne "
         "of NH₃) are listed in order of cost under the linear bridge, with their cost under the element-anchored "
         "bridge. Pruned, excluded by the lower bound on cost before the full optimization. False prunes, pruned "
         "surfaces whose full optimization falls below Fe. The 101 surfaces containing Tc are not costed.",
    "4a": "Deviation, (model − industrial)/industrial for point values, the difference in °C for temperatures and the "
          "distance to the nearer edge for reported ranges (0 inside the range). Typical and largest, median absolute "
          "and maximum deviation of the items of a quantity. Component, the model component perturbed in "
          "Supplementary Table 4b. Converter items use the measured rate laws of fused iron and Ru/C inside their "
          "fitted pressure ranges. Four logical items have no numeric deviation, and C08 and C10 keep the scores of "
          "the original benchmark campaign.",
    "4b": "Catalyst-dependent cost difference at the reoptimized optima (US dollars per tonne of NH₃, positive: Fe "
          "cheaper), with each model component perturbed in both directions by the deviations of Supplementary Table "
          "4a. Descriptor, descriptor kinetics. Measured, the rate laws of fused iron and Ru/C inside their fitted "
          "pressure ranges, for the benchmark bed and for supported Ru/C (95.55% recovery, metal financing at 0 or 12% "
          "per year). Combinations: every component at the same magnitude, each in the direction that favours Ru, and "
          "the least favourable of the 64 sign combinations. No feasible Fe or Ru/C, no state of that catalyst within "
          "the 90 m³ limit.",
    "4c": "Industrial, the reported value or range. Logical items compare a decision (yes or no) or a threshold. "
          "Deviation as in Supplementary Table 4a, signed (negative: model low).",
    "5a": "Terrace and step-site N formation energies of the 14 metals with both values in the descriptor source, and "
          "the step value predicted with that metal left out.",
    "5b": "Ordinary least squares on Supplementary Table 5a. The 14-metal fit is the relation used for Fe, and its "
          "residual standard error is the Fe descriptor uncertainty. The strong-binding branch (terrace "
          "\\(E_{\\mathrm{N}}\\le-0.5\\) eV: Mo, Os, Re, Ru, W) is a sensitivity check. Prediction interval, Student t "
          "with n − 2 degrees of freedom.",
    "6a": "Printed, value printed in the source. Derived, arithmetic on printed values. Secondary, pilot-plant values "
          "tabulated by Dieterich 2020. Figure, read off a figure.",
    "6b": "M1, anchor loop (calibration point). M2, three-step variant of the anchor loop. M3, economic optimum of the "
          "Re/TiO₂ states (5 wt% Re, 200 °C, 2% purge). M4, optimum at its own purge (1 wt% Re, 200 °C, 0.5% purge). "
          "M5–M12, at the operating points of the Lurgi CO₂ pilot, González-Garay, Pérez-Fortes 2016, Van-Dal 2013, "
          "Szima 2018, Nyári 2022 (two loops) and Nieminen 2019. Reference values are in Supplementary Table 6c.",
    "6c": "An asterisk marks a pilot-plant value tabulated by Dieterich 2020.",
    "6d": "Euros per tonne of methanol. Like-for-like, feed, compression electricity, catalyst replacement and capital "
          "annuity at the study's own rate, plus its own fixed operating cost. For Pérez-Fortes 2016 the reference is "
          "the break-even methanol price (production cost plus capital recovery). Anchor convention, the model's full "
          "net production cost.",
    "6e": "The model is run at each study's own capacity and cost year.",
    "6f": "Groups whose STY leader is not the plant-cost leader, papers affected, pairwise orderings inverted, median "
          "regret of these groups, and groups whose verdict or plant-cost leader changes, with each plant term taken "
          "from its primary source.",
    "7": "One row per comparison group of all entries (one paper, same pressure, H₂/CO₂ ratio and space velocity, plot "
         "readings included). Entries, all entries / entries with printed conversion and selectivities. Printed "
         "values define the 81 groups of the primary analysis. Verdict, whether the STY leader is not the plant-cost "
         "leader, with the regret where it is not, in the inert-limited loop (CO, methane and N₂ at most 6.86% of the "
         "reactor inlet) and without the limit. Set, first or second extraction. –, fewer than two entries that meet "
         "the limit.",
    "8a": "A root cause is one mechanism in one source paper. Error rules group the cells of one paper, field and cause. "
          "Rows are records of conditions the paper did not test. A derived STY is counted only with the input error "
          "it inherits (last column).",
    "8b": "Definition, the printed STY differs from the value the dataset derives from yield and space velocity, or "
          "the paper prints STY on bases it does not reconcile. Minor, at most 2% and at most one unit of the last "
          "printed digit. The printed values are used for scoring.",
}
