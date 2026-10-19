# PROTOCOL — Ranking-preservation theorem + NH3 economic decision atlas

Date: 2026-10-19. **Fixed BEFORE writing new study code or computing new aggregate statistics.** Exploratory mathematics and a READ-ONLY reanalysis of already computed NH3-FINAL-1.2 staged-converter designs. NOT a new industrial validation, a new kinetic experiment, or a manuscript change.

## T1 — Rank-preservation sufficient conditions

For catalysts A and B with higher-is-better metric s_A > s_B, let F_A and F_B be nonempty feasible operating-policy sets and J_i(u) a shared, explicitly named lower-is-better downstream cost objective. Use infimum if minima do not exist.

1. **Theorem (feasible superset + pointwise cost dominance).** If F_B is a subset of F_A and J_A(u) <= J_B(u) for EVERY u in F_B, then C_A*=inf_F_A J_A <= C_B*=inf_F_B J_B. If J_A(u) <= J_B(u)-d throughout F_B, then C_A* <= C_B*-d. The mere upstream ranking s_A>s_B does not establish either condition.
2. **Contrapositive.** If C_A*>C_B*, either inclusion or pointwise dominance fails, possibly both. This does NOT identify a unique causal mechanism: prices, inventory, catalyst lifetime, recycle and feasible process topology may jointly violate the premises.
3. **Bounded-model-error addendum (fixed feasible sets).** If absolute J_i(u)-Jhat_i(u) <= eps_i uniformly on F_i, then |C_i*-Chat_i*|<=eps_i. Therefore Chat_B*-Chat_A*>eps_A+eps_B certifies the A win. NO eps values are inferred here for errors in industrial plant physics. Structural feasibility-set uncertainty invalidates this certificate.
4. **Fixed-optimum identity (when B optimum u_B* is feasible for A).** C_A*-C_B* = [J_A(u_B*)-J_B(u_B*)] - [J_A(u_B*)-C_A*]. The second bracket is nonnegative. Consequently an observed inversion against A requires an even larger A disadvantage at B's optimum. If u_B* is outside F_A, identity undefined.
5. **Price-envelope lemma.** If every fixed design d has cost J_d(p)=a_d+b_d*p with nonnegative Ru metal inventory b_d at fixed financing/recovery/loop, its lower envelope min_d J_d(p) is nondecreasing, concave and piecewise affine. All-Fe has zero Ru-price slope, so binary all-Ru-minus-all-Fe cost can have at most one crossing in SIGN as Ru price increases (possibly a flat equality interval). A mixed-bed competitor can beat BOTH, so binary parity need not be an actual industrial optimal-decision boundary.

### Counterexamples and proof gates

- Exhaustive finite discrete tests verify inclusion+pointwise theorem and strict margin.
- Demonstrate s_A>s_B and expensive A on a shared F can yield C_A*>C_B*.
- Demonstrate pointwise A domination only on F_A INTERSECTION F_B does not suffice when B is feasible at a cheaper state unavailable to A.
- Test synthetic price envelopes and an intermediate mixed-catalyst winner.
- All real-system applications require comparable cost objective and feasible operating domain. Au/TiO2 is a fixed-condition inverse-activity control, NOT proof for arbitrary industrial costs; do not infer real NH3/MeOH feasibility-set inclusion from these theorems.

## P1 — Existing supported Ru/C + Fe-first three-bed design atlas

Source files (NH3-FINAL-1.2) and immutable original Git blobs:
- analysis/nh3_staged_converter_2026_10_12/nh3_1_2/boundary_price_financing.csv — 7ce211cb750c4e83a9994f9a286667bd874ef2df
- analysis/nh3_staged_converter_2026_10_12/nh3_1_2/boundary_pressure.csv — 7cd6775690b07d652978ad12f3159c1cb8276a72
- analysis/nh3_staged_converter_2026_10_12/nh3_1_2/design_library.csv — 5f2187c846d8d30b8a3bd3d4dc93164d52f3496a (provenance; not rerun here).

Source grid: EXACTLY 4100 precomputed rows, 2 fixed process masks (P=90 bar/Tsep=-20 C and P=150 bar/Tsep=-5 C) x recovery assumptions 0.90 and 0.9555 x 41 Ru price samples ($2000–$200000/kg) x 25 metal financing rates (0–12%/y in 0.5-percentage-point steps). Decisions among FFF=all-Fe, RRR=all promoted supported Ru/C, FRR and FFR=Fe-first staged catalysts. This stage-flow optimization and objective are NOT the main paper's original 15-metal descriptor optimum or its catalyst-dependent-only cost.

Fixed metrics:
1. Validate source Git blobs, 4100 unique Cartesian rows, two distinct process masks. If altered, FAIL; no silent source repairs.
2. Confirm best class equals source minimum over all_Fe, staged, all_Ru within source rounded tolerance 1e-5 USD/t. For staged best use staged_pattern FFR/FRR. Report per-mask/recovery exact class counts and near-ties where minimum margin to runner-up is <0.01 or <0.10 USD/t.
3. Quantify cases where staged beats both pure alternatives; compute relative regret if choosing the better pure competitor: min(all_Fe,all_Ru)/staged -1. Report count, median, max in each panel. This is NOT laboratory-to-industry regret.
4. For each mask/recovery/rate, verify all-Fe cost independent of Ru PRICE and all-Ru/staged cost nondecreasing as price rises (tolerance 3e-5 USD/t for source printed rounding). Assert binary cost sign crosses no more than once.
5. At NOMINAL p_Ru = $53,852.5/kg and recovery 0.9555, read the independent exact-price boundary_pressure.csv source, select only corresponding (90,-20) and (150,-5) process masks. Report winner transition BRACKETS from 0.5%-point rates, not falsely precise interpolated continuum roots.
6. Join the two recovery scenarios at identical mask/price/rate: report design-choice changes. Recovery has been assumed as gross salt recovery in prior evidence; not verified saleable metallic Ru buyback.
7. Produce source-grid categorical 2x2 phase figure, 90/150 bar columns vs 90/95.55% recovery rows, four distinct Fe/FFR/FRR/Ru regions. Use price LOG axis, rate linear axis, discrete pcolormesh (no smoothing). Mark $53,852.5/kg source nominal vertical reference. Publish both PNG/SVG and CSV/JSON/Markdown as read-only CI artifacts, not manuscript figures.
8. Figure/source data and class counts are DETERMINISTIC conditional model-grid results, not probability of physical plant choice. Where cost margins are near zero, display/tally economic near-degeneracy.

## Model limitations / paper firewall

- Fe Dyson–Simon measured kinetics fit 149–309 atm (~151–313bar), promoted Ru/C Rossetti fit 50–100bar; NO common experimental fitted pressure window. Fe at 90bar, Ru/C at 150bar are extrapolations; neither phase panel independently establishes same-pressure measured-kinetics ranking validity.
- Changing between the 90bar/-20 C and 150bar/-5 C MASK changes pressure AND separator setpoint; do not interpret as a pressure-only effect.
- Ru pricing and financing range includes hypothetical, extreme scenarios; no Ru lease contract or monetary buyback calibration is validated.
- All output costs are discrete library lower-envelope estimates, which may be upper bounds on true fully continuous design optimization. No new optimizer evaluations in this study.
- New files ONLY analysis/rank_preservation_phase_2026_10_19 and .github/workflows/rank-preservation-phase-2026-10-19.yml. DO NOT edit docs/, figures/, source_data/, provenance/, original analysis/, manuscript, frozen results or models.
- Save results to GitHub Actions artifacts and open a DRAFT PR; scientific author review required before using any new paper claim.
