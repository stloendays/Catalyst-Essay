# When is catalyst ranking preserved? Conditional results (exploratory mathematical note)

## Definitions and comparison discipline

Write A and B for two catalysts or catalyst/operating-point technologies. A has the higher upstream metric (activity, selectivity or space-time yield): s_A>s_B. A *larger s alone is not sufficient* for a cost dominance statement. Let F_A and F_B be the **possibly different** nonempty sets of feasible operating policies and J_i(u) be a COMMON lower-is-better economic objective, defined on F_i. Set C_i*=inf_{u in F_i} J_i(u). Comparing different denominators (e.g. full MeOH plant cost against NH3 catalyst-only component) is not a proof of a universal order.

### Proposition 1: sufficient ranking-preservation condition

Suppose

(i) F_B is a subset of F_A, and
(ii) J_A(u) <= J_B(u) for every u in F_B.

Then

    inf_{u in F_A} J_A(u)
        <= inf_{u in F_B} J_A(u)
        <= inf_{u in F_B} J_B(u),

so **C_A*<=C_B***. If a constant d>=0 further satisfies J_A(u)<=J_B(u)-d for all u in F_B, the right inequality is sharpened by d: C_A*<=C_B*-d. (The claim remains valid with infima rather than achieved minima.)

The economically relevant premise is *global cost dominance on a shared feasible comparison*, not the observation that A has larger turnover or yield at one published state. A higher upstream activity metric does not itself ensure either premise.

**Contrapositive.** If A is more costly after each candidate has separately optimized its own admissible operating policy, then either A lacks at least one B-feasible operation or there exists a B-feasible operation where A has higher cost, or both. The inverse statement does not single out metal price, lifetime, process constraints, energy, purge or any one causal mechanism.

### Proposition 2: bounded-error certificate

Hold F_A and F_B fixed. Suppose both estimated cost surfaces obey uniform additive bounds |J_i(u)-Jhat_i(u)|<=eps_i for all u in F_i. Then

    |C_i* - Chat_i*| <= eps_i

because taking an infimum preserves uniform bounds. Hence if

    Chat_B* - Chat_A* > eps_A + eps_B,

the true ranking has C_A*<C_B*. If this margin does not hold, **nothing follows** about which candidate truly wins. Estimating physically honest eps_i for unresolved multi-component NH3 plant thermodynamics, kinetics and finance would require additional validated error evidence that this note does not provide. Structural changes to feasibility are not covered.

### Proposition 3: exact fixed-B-optimum decomposition

When B attains an optimum at u_B* AND u_B* belongs to F_A,

    C_A* - C_B*
      = [J_A(u_B*) - J_B(u_B*)] - [J_A(u_B*) - C_A*].

The second bracket is nonnegative and is the advantage A obtains by reoptimizing its own feasible policy away from u_B*. A positive optimized cost gap against A implies a pointwise cost disadvantage at u_B* strictly at least as large. If u_B* is infeasible for A, this algebraic comparison cannot be applied; it must not be treated as an empirical penalty by extrapolating the process model.

### Proposition 4: metal-price envelope and phase topology

Fix a specific process mask, gross metal-recovery fraction and capital/metal financing convention. In the existing NH3 staged design library, each feasible design d has a nonmetal contribution a_d and nonnegative catalyst Ru-metal loading b_d, with cost

    J_d(p) = a_d + b_d * p,  p >=0.

The lower envelope over a FINITE precomputed fixed design set,

    C*(p) = min_d [a_d + b_d*p],

is nondecreasing (each line is), concave (pointwise minimum of affine functions) and piecewise affine. The optimized Fe-only cost C_FFF is price-invariant because it has b_d=0. Therefore D(p)=C_RRR(p)-C_FFF(p) cannot change from Fe-cheaper (D>0) to Ru-cheaper (D<0) as p increases. There is at most one sign transition in the binary pure-catalyst comparison.

However, the relevant industrial decision is

    min(C_FFF, C_FFR, C_FRR, C_RRR).

A third feasible staged design can be strictly cheaper than both pure options. **The binary parity point C_FFF=C_RRR is not sufficient to describe the true decision frontier.** This is a conditional theorem for Ru *price* variation at fixed feasible design library; it makes no claim that Ru-metal recovery, interest rate or plant location alone preserves any monotone order.

### Counterexamples (falsify false generalizations)

1. **Activity without cost dominance.** Let s_A=2,s_B=1, F_A=F_B={u}, J_A(u)=12 and J_B(u)=10. A is the activity leader, B is cheaper. Thus s_A>s_B does not imply rank preservation.
2. **Overlap dominance without feasible-set inclusion.** Let F_A={u_1}, F_B={u_1,u_2}; let J_A(u_1)=1, J_B(u_1)=2, J_B(u_2)=0.5. A is cheaper at every COMPARABLE u yet B wins globally because its additional feasible operating mode costs 0.5.
3. **A third option hides binary parity.** At some Ru price p_0 let C_FFF(p_0)=10, C_RRR(p_0)=10, and C_FRR(p_0)=9. Both pure designs are tied, but neither is optimal.

## Relationship to the three manuscript systems

- **Au/TiO2:** The fixed-condition construction maps greater mass activity to lower required catalyst mass, holding other terms constant. This satisfies a simple scalar inverse map within its defined control, not a theorem that all Au-based industrial costs are monotone.
- **NH3:** Fe/Ru intrinsic activity ranks can be overwhelmed by catalyst inventory cost, metal financing and candidate-dependent optimal operating conditions. A same-loop Fe/Ru/C model also requires consistent measured kinetic applicability; existing Fe and promoted Ru/C experimental pressure fit windows are disjoint.
- **CO2-to-MeOH:** The group ranking includes catalyst formulation and reported operating-point changes, while selectivity can change recycle CO, purge and modeled feasibility. Some candidates' feasible policy sets and pointwise costs are unknown outside the printed literature points, so applying Proposition 1 to the full plant cannot be assumed.

This note therefore adds **conceptual falsifiability and a precise preservation theorem**, not a new universal predictor. The manuscript's pairwise realized χ is descriptive of calculated downstream outcomes and cannot be converted into forecast accuracy by this theorem.

## What would be required for an empirically predictive test

To apply Proposition 1 before full plant-cost evaluation one must measure or bound (a) comparable candidate feasible operating policies, (b) pointwise economic cost differences on the weaker candidate's feasible domain, and (c) uncertainty in the resulting optimum margin. The present NH3 phase atlas summarizes ALREADY OPTIMIZED design-library outcomes, so it remains an interpretive economic map rather than a fast lab-only prediction algorithm.
