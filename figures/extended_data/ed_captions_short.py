"""Reader-facing Extended Data captions (2026-10-21, author: short, descriptive captions in the style of Nature-family
papers; one clause per panel, conditions at the end, no result numbers). The numbered, source-linked captions that
render_extended_data.py generates from the panel tables are kept in ED_CAPTIONS_DETAILED.md for provenance.
"""

SHORT = {
    1: ("Accuracy of the extraction agent on the methanol literature",
        "**a**, Strict accuracy of the extracted CO$_2$ conversion (X), methanol selectivity (S$_{MeOH}$) and space-time "
        "yield (STY) against two curated datasets, by where the value is printed (main-text tables, SI tables, "
        "main-text plots, SI plots). **b**, Recall of curated entries per dataset."),
    2: ("Full optimizations saved by the lower bound on cost",
        "**a**, Lower bound against full plant cost for the methanol candidates, evaluated in full (blue) or excluded. "
        "**b**, The same for the bimetallic ammonia surfaces within the bed limit; dashed, Fe benchmark. **c**, Share "
        "of candidates evaluated in full in each search."),
    3: ("Robustness of the methanol leader changes",
        "**a**, Paper-cluster bootstrap distribution of the share of comparisons in which the STY leader is not the "
        "plant-cost leader. **b**, Disagreements against the regret threshold. **c**, Disagreements under "
        "re-measurement of every entry at one, two and four times the measurement error, against the noise floor. "
        "**d**, Persistence of each disagreement under re-measurement; triangles, near-infeasible cases. **e**, "
        "Disagreements under each robustness variant; hatched, cost gap above 5%. Filled, inert-limited loop (CO, "
        "CH$_4$ and N$_2$ at most 6.86% of the reactor inlet); open, no limit. **f**, Persistence under re-measurement "
        "of each change of catalyst in the 63 comparisons with at least two catalysts, with more catalyst loaded and "
        "at laboratory conversion, in the inert-limited loop; dots, cost gap above 5%. Dark bars in **d** and **f**, "
        "persistent in at least 90% of 2,000 draws."),
    4: ("The methanol plant model against published plant assessments",
        "**a**, Cost terms of a reference CO$_2$-to-methanol plant, model against reference. **b**, Model cost against "
        "the reported production cost or break-even price of 12 studies at their own inputs; band, ±5%. **c**, Loop "
        "metrics relative to the reference plant. **d**, Disagreements in the loop without an inlet limit under "
        "plant-model variants."),
    5: ("Measured ammonia catalysts of a review through the plant model",
        "**a**, Plant cost against laboratory rate per gram of metal for the primary catalysts of ref. 26, without "
        "metal recovery; dashed, Fe benchmark. **b**, Plant cost by metal; bars, lowest cost per metal."),
    6: ("Bimetallic surfaces through the ammonia model, by element layer",
        "Plant cost against log$_{10}$ TOF at 673 K for the surfaces whose optimum fits the 90 m$^3$ bed limit; dashed, "
        "Fe benchmark. **a**, Transition metals only; green, one of Fe, Co, Ni or Cu with Cr, Mo or W. **b**, With "
        "group 3–5 elements. **c**, With sp metals."),
    7: ("Supported Ru/C against fused iron with measured rate laws: robustness",
        "**a**, Ru/C − Fe catalyst-dependent cost at Ru financing rates of 0 and 12% per year for the base case and 15 "
        "variants, at each catalyst's own optimum (circles) and in the KAAP-type loop (diamonds). **b**, Break-even "
        "financing rate of each case; shaded, disclosed catalyst-metal lease rates; red, the reference rate. Each "
        "catalyst is optimized inside the pressure range of its rate law."),
    8: ("Rank preservation in the Au/TiO$_2$ control and the catalyst-life channel",
        "**a**, The five Au particle sizes on one TiO$_2$(110) support, to scale (illustrative models). **b**, Full order, "
        "2 nm leader and full inversion against the life exponent λ with candidate-specific kinetic and operating "
        "variation over 273–293 K; shaded, the carbonate-loss regime (λ ≈ 0). **c**, Catalyst required relative to "
        "2 nm particles at the nominal size exponents. **d**, Share of draws keeping the full order and the 2 nm "
        "leader against the per-size activity scatter σ; dashed, σ = 0.25. **e**, Probability that 2 nm particles "
        "stay the least-cost catalyst when catalyst life scales as d$^{λ}$; dashed, λ = n + m."),
    9: ("Ru against Ni in CO$_2$ methanation, from an independent reactor study",
        "**a**, Ru − Ni catalyst-dependent cost per MWh of SNG against plant scale, central parameters (line) and "
        "Monte Carlo median with 5–95% range (points). **b**, Probability that Ru is cheaper. **c**, The two sides of "
        "the decision criterion, r$_V$(1 + φ$_{proc}$) and Π, and inventory alone (r$_V$)."),
    10: ("Purge boundary and inlet-limited methanol loops",
         "**a**, Net production cost along an extended purge grid for every scored entry in the loop without an inlet "
         "limit. **b**, Reactor-inlet content of species other than H$_2$ and CO$_2$ along the same grid; shaded, "
         "published loop designs; dashed, the loop that anchors the cost model. **c**, Optimal purge and **d**, recycle "
         "ratio under each loop treatment. **e**, Disagreements against the inlet limit, counting CO, CH$_4$ and N$_2$ "
         "(circles) or CH$_4$ and N$_2$ only (squares)."),
}


def text():
    out = ["# Extended Data figure captions", "",
           "Reader-facing captions; the numbered, source-linked captions are in ED_CAPTIONS_DETAILED.md and the "
           "numbers in `source_data/SourceData_EDFig{N}.xlsx`.", ""]
    for n in sorted(SHORT):
        title, body = SHORT[n]
        out += ["## Extended Data Fig. %d | %s" % (n, title), "", body, ""]
    return "\n".join(out)
