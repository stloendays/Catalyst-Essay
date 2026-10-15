# Additional cross-source check: two Uhde industrial separator vapor streams (post-hoc)

**Post-outcome extension preregistration:** This test is defined AFTER our BASF table CV and five plant-inlet outcomes were viewed and AFTER the independent Uhde 12-stream data were inspected, but BEFORE computing the source-fitted vapor predictions for the two separator streams. It is an exploratory, already-observed-source transfer, NOT an independent blinded prospective field validation.

## Primary source and exact points

- Read the unchanged, Git-blob-pinned source snapshot from the separate open source-accounting PR #90, path 'analysis/nh3_source_matched_loop_v0/figure57_streams.csv' on its branch 'paper/nh3-uhde-stream-simulation-2026-10-14'. Source: Appl (2011), *Ammonia, 2. Production Processes*, Ullmann, Figure 57 p.211, DOI 10.1002/14356007.o02_o11. Pinned Git blob **7d511a788895d1f3ab825f9db9a3f0929db44460**. Abort if that source changes. GitHub Action fetches source through original branch into ephemeral artifacts. Do not commit new copies of source rows or misrepresent observations as predictions of kinetic catalysis.
- Two actual numbered GAS streams, from the **same ONE plant**, NOT independent industrial studies:
  - Source stream 5 first-separator vapor: **21 °C, 180.2 bar, 8.51 mol% NH3**; note PR #90 explains that pressure is assigned from the co-vessel liquid/pressure boundary, not a separately instrumented gas-phase pressure measurement. Inert CH4+Ar source ≈14.45 mol%.
  - Stream 6 refrigerated second-separator vapor: **0 °C, 178.8 bar, 4.18 mol% NH3**, CH4+Ar ≈11.08 mol%.
- Verify all 12 source rows, source DOI/page/figure and mole-fraction normalization from the exact blob, but evaluate ONLY stream gas 5 and 6. No fitting to either value.

## Models and fixed comparison

- Same M0 original Antoine p_sat(T)/P, same M1 and M2 effective log-fugacity-factor correction coefficients trained by 'vle_cv.fit()' exclusively on the 28 independent BASF N2:H2=1:3 vapor source values, and same no-fit BASF table bilinear interpolation via existing 'diagnose_separator_vle.source_interpolation()'. No alternative model, fit/training split, or case selection chosen after the two-point result.
- Apply each method to each gas source T/P, compute error against actual printed stream NH3 mol%, and record source composition (N2,H2,CH4,Ar,NH3), source T/P, published Figure57 source, and whether predicted vapor is within **±20% and ±10% relative error**. These are descriptive fixed sensitivity bands, not added metrics to original preregistered 64 scores.
- A source VLE model might approximate Uhde gas separator vapor even though it fails to predict the five published REACTOR INLET targets through a simplified recycle loop. This distinction must be explicit and is the scientific question. Only two related gas streams (n=2; common plant) are available; no significance test, fabricated uncertainty or generalized 5-component EOS claim.
- If two Uhde points agree and five external inlet cases fail, interpret as evidence consistent with an importance of flowsheet/mixing/composition, NOT proof that VLE physics is entirely correct or the loop topology is the only cause. Real plant vapor gas has sizable CH4 and Ar unlike BASF reference N2:H2=1:3; PR #90 reconstructs source process material balance from printed streams rather than independent dynamical validation.
- No changes to source data, frozen NH3-FINAL-1.2 model, industrial pass count (32/64) or manuscript. New code and CI contract live ONLY in this PR folder/workflow. No secrets.
