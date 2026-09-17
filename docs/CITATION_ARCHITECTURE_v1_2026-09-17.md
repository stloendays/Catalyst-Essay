# Citation architecture v1 — 2026-09-17

This document organizes the manuscript literature by scientific function rather than by chronology. The objective is to keep the main text selective: foundational papers establish the field, source papers justify model inputs, and closest-prior-art papers define what is genuinely new in the present work.

## 1. Foundational literature: establish the intellectual baseline

These references should appear early in the Introduction and only be repeated when they directly support a mechanistic statement.

### Descriptor, scaling and computational screening

- Nørskov et al., *Nature Chemistry* (2009): computational catalyst design as a descriptor-driven paradigm.
- Greeley et al., *Nature Materials* (2006): high-throughput first-principles catalyst screening.
- Zhao et al., *Nature Reviews Materials* (2019): scaling relationships and reactivity descriptors as a catalyst-design framework.
- Abild-Pedersen et al., *Physical Review Letters* (2007): adsorption-energy scaling relations.
- Bligaard et al., *Journal of Catalysis* (2004): BEP relations and volcano behavior.
- Medford et al., *Catalysis Letters* (2015): descriptor-based microkinetic mapping through CatMAP.
- Bruix et al., *Nature Catalysis* (2019): first-principles multiscale modelling from surface chemistry toward experimentally relevant behavior.
- Ulissi et al., *Nature Communications* (2017): uncertainty-aware reduction of reaction-network complexity.

**Use in the paper:** establish that descriptor compression, scaling and microkinetic propagation are mature tools. Do not imply that linking scales is itself the novelty.

### Adaptive sampling and uncertainty

- Lookman et al., *npj Computational Materials* (2019): active learning and uncertainty-guided adaptive sampling.
- Wellendorff et al., *Physical Review B* (2012): Bayesian error estimation for surface-science density functionals.

**Use in the paper:** support the idea that uncertainty should be evaluated against the observable or decision being resolved, rather than treated as a uniform reason for more computation.

### Autonomous and agentic science

- Yao et al., ReAct (2023): interleaved reasoning and tool actions.
- Bran et al., *Nature Machine Intelligence* (2024): chemistry tool use by LLMs.
- Boiko et al., *Nature* (2023): autonomous chemical research with LLMs.
- Burger et al., *Nature* (2020), Bédard et al., *Science* (2018), Dragone et al., *Nature Communications* (2017), Shields et al., *Nature* (2021), Tom et al., *Chemical Reviews* (2024): autonomous laboratories, reaction optimization and self-driving experimentation.
- Lai et al., *Industrial & Engineering Chemistry Research* (2023), Morandi et al., *Nature Chemical Engineering* (2026), Liu & Ou, *npj Artificial Intelligence* (2026), Ramos et al., *Chemical Science* (2025): catalyst-focused and chemistry-agent context.

**Use in the paper:** establish the broader agent/autonomy landscape, then narrow immediately to the present question: allocation of finite scientific compute within a frozen decision chain.

## 2. Direct source literature: justify the actual scientific inputs

These references are not optional background citations. They support concrete physical inputs, candidate definitions or calibration choices and should remain close to the corresponding Methods or Results statements.

### Ammonia

- Logadottir et al., *Journal of Catalysis* (2001): ammonia BEP/volcano relation.
- Honkala et al., *Science* (2005): first-principles ammonia-synthesis mechanism and activity landscape.
- Jacobsen et al., *Journal of the American Chemical Society* (2001): catalyst design by interpolation in the periodic table; useful historical support for the Ru/Os/Fe activity landscape and descriptor-driven ammonia catalyst design.

### Methanol

- Gothe et al., *ACS Catalysis* (2025): primary source for the four Re/TiO2 catalyst-temperature states used in the D01 v3 reconstruction.
- Pérez-Fortes et al., *Applied Energy* (2016): process-scale CO2-to-methanol TEA, including recycle/separation context.
- Jadhav et al., *Chemical Engineering Research and Design* (2014): process and catalytic context for CO2 hydrogenation to methanol.

### Au/TiO2 control

- Haruta et al., *Chemistry Letters* (1987): low-temperature CO oxidation by supported Au.
- Valden et al., *Science* (1998): particle-size-dependent onset of Au/TiO2 activity.
- Janssens et al., *Journal of Catalysis* (2006): absolute-rate anchor, loading and dispersion.
- Overbury et al., *Journal of Catalysis* (2006): closest-loading Au-size dependence used for the nominal exponent.

**Rule:** when a number in the model comes directly from a paper, cite the primary source rather than only a review.

## 3. Closest prior art: define novelty precisely

This is the most important literature layer for Discussion and the final Introduction paragraph. These papers should be cited explicitly because they narrow what the present manuscript can legitimately claim as new.

### Jacobsen et al., Journal of Catalysis 205, 382–387 (2002)

**Reference:** Jacobsen, C. J. H. et al. *Optimal catalyst curves: Connecting density functional theory calculations with industrial reactor design and catalyst selection.* Journal of Catalysis **205**, 382–387 (2002). doi:10.1006/jcat.2001.3442.

**What it already established:** DFT + microkinetics can identify an optimal nitrogen-binding energy as a function of ammonia reaction conditions, explicitly linking catalyst descriptors, reactor conditions and catalyst selection.

**What the present work adds:** the central observable is not the location of an optimal descriptor alone, but whether a discrete candidate ranking survives propagation to an explicit industrial economic objective. The present work also localizes ranking failure at the decision frontier, propagates uncertainty to the decision, back-propagates economic parity into a catalyst-property target, tests scaling-consistent reachability, transfers the mechanism across reactions, includes a rank-preservation counterfactual and evaluates decision-aware compute allocation.

**Manuscript placement:** Introduction paragraph 1 or 3; Discussion paragraph on novelty relative to integrated catalyst/reactor design.

### Rangarajan, Maravelias & Mavrikakis, J. Phys. Chem. C 121, 25847–25863 (2017)

**Reference:** Rangarajan, S., Maravelias, C. T. & Mavrikakis, M. *Sequential-Optimization-Based Framework for Robust Modeling and Design of Heterogeneous Catalytic Systems.* Journal of Physical Chemistry C **121**, 25847–25863 (2017). doi:10.1021/acs.jpcc.7b08089.

**What it already established:** optimization-based integration of mechanistic modelling and catalyst design, including robustness to model uncertainty.

**What the present work adds:** a ranking-centric objective tied to industrial economics; explicit preservation/inversion diagnostics; reaction-specific coupling topology; backward economic reachability; a falsification control; and a finite-compute agent benchmark whose endpoint is a scientific decision rather than catalyst activity alone.

**Manuscript placement:** Introduction after the first-principles multiscale literature; Discussion in the novelty-positioning paragraph.

### Bardow, Steur & Gross, Ind. Eng. Chem. Res. 49, 2834–2840 (2010)

**Reference:** Bardow, A., Steur, K. & Gross, J. *Continuous-Molecular Targeting for Integrated Solvent and Process Design.* Industrial & Engineering Chemistry Research **49**, 2834–2840 (2010). doi:10.1021/ie901281w.

**What it already established:** process-level objectives can be inverted into an idealized molecular target and then mapped back toward realizable materials; integrated material/process design is therefore not conceptually new.

**What the present work adds:** the backward target is defined for a catalyst property, is compared directly with a physically constrained catalyst scaling manifold, and is embedded in a ranking/decision framework with explicit industrial candidate selection.

**Manuscript placement:** Discussion paragraph on backward design. One citation is sufficient; do not overemphasize the solvent-design analogy.

## 4. Recommended Introduction citation architecture

A concise high-impact Introduction can use the literature in four moves.

**Paragraph 1 — mature upstream screening paradigm.** Cite Nørskov 2009, Greeley 2006, Zhao 2019, Abild-Pedersen 2007, Bligaard 2004, CatMAP 2015 and Bruix 2019. Then cite Jacobsen 2002 and Rangarajan 2017 to acknowledge that catalyst descriptors have already been linked to reactor conditions and optimization. This prevents an exaggerated novelty claim.

**Paragraph 2 — unresolved comparative problem.** No dense citation stack is needed. State that prior work largely optimizes predicted activity, descriptor position or process performance, whereas the present question is whether the *ordering among candidates* is conserved at the industrial decision frontier. This is the conceptual gap.

**Paragraph 3 — forward/backward design.** Introduce the bidirectional framework. Bardow 2010 can be cited as broader integrated material/process inverse-design precedent. The novelty is the combination of economic parity, catalyst-property reachability and rank preservation/inversion.

**Paragraph 4 — reaction systems and agent layer.** Use primary source papers for ammonia, Re/TiO2 and Au/TiO2. Keep the agent literature compressed to ReAct, ChemCrow, Coscientist and one autonomous-lab review in the main text; move the rest to Methods/SI if word count becomes tight.

## 5. Recommended Discussion citation architecture

The Discussion should use references to define boundaries, not to re-document every result.

**Decision-frontier paragraph:** cite descriptor/scaling literature only once. The manuscript contribution is the distinction between global rank agreement and frontier fidelity.

**Backward-design paragraph:** cite Jacobsen 2002, Rangarajan 2017 and Bardow 2010. Write the novelty as a progression: prior work links catalyst descriptors to operating conditions and optimization; here the industrial economic gap is inverted into a catalyst target and then tested against physical reachability.

**Cross-reaction paragraph:** cite Gothe 2025 and Pérez-Fortes 2016 for the methanol pathway, plus ammonia source literature for the activity-inventory pathway. Avoid claiming a universal quantitative leverage ratio.

**Control paragraph:** cite Janssens and Overbury as direct calibration sources; Haruta and Valden can remain supporting historical context.

**Agent paragraph:** cite ReAct, ChemCrow, Coscientist, Shields and Tom. Use the catalyst-agent papers to position the benchmark, but emphasize that DISCOVER differs by freezing the scientific environment and scoring decision recovery under an explicit compute budget.

## 6. Main-text versus Supporting Information allocation

For the main manuscript, a reference count around 30–40 is appropriate if the Introduction remains compact. The following references are high-priority main-text citations: Nørskov 2009; Zhao 2019; Bruix 2019; Jacobsen 2002; Rangarajan 2017; Logadottir 2001; Honkala 2005; Gothe 2025; Pérez-Fortes 2016; Janssens 2006; Overbury 2006; ReAct 2023; ChemCrow 2024; Coscientist 2023; Tom 2024.

Other references can move to Methods or SI without weakening the conceptual argument. In particular, multiple autonomy-platform precedents should not crowd the main Discussion, and historical Au papers can be moved to Methods if the main-text citation density becomes high.

## 7. Novelty sentence recommended for the manuscript

A concise positioning sentence that accurately acknowledges prior art is:

> Prior work has linked first-principles catalyst descriptors to reactor conditions, catalyst selection and optimization; here we ask a different comparative question—whether the ranking among candidate catalysts survives propagation to an industrial economic objective, and, when it does not, whether the economic gap can be mapped back to a physically reachable catalyst target.

This sentence should replace any wording that implies the manuscript is the first to connect atomistic modelling with reactor or process design.