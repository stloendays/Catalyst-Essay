"""Analytical dissociative adsorption / associative desorption cycle, no APIs."""
import math
from mkm_solver import solve


def validate():
    # A2 + 2* <-> 2A* <-> B2 + 2*. Both steps reversible, kf=kr=1.
    spec = dict(species={"A*": 1}, gases={"A2": 4., "B2": 1.}, T_K=600,
                overall={"A2": -1, "B2": 1}, steps=[
                    dict(name="adsorb", stoich={"A2": -1, "*": -2, "A*": 2}, Ea=0., dE=0., prefactor=1.),
                    dict(name="desorb", stoich={"A*": -2, "B2": 1, "*": 2}, Ea=0., dE=0., prefactor=1.)])
    ratio = math.sqrt((4+1)/2)
    for step in spec["steps"]:
        step.update(Ea=.2, prefactor=math.exp(.2/(8.617333262145e-5*600)))
    theta = ratio/(1+ratio)
    analytic = theta**2-(1-theta)**2
    got = solve(spec)
    assert abs(got["coverages"]["A*"]-theta) < 1e-8
    assert abs(got["TOF"]-analytic) < 1e-8
    assert abs(sum(got["degree_of_rate_control"])-1) < 2e-4, got
    print(f"LH analytical theta={theta:.12g}, solver={got['coverages']['A*']:.12g}; TOF analytic={analytic:.12g}, solver={got['TOF']:.12g}; DRC sum={sum(got['degree_of_rate_control']):.9g}: PASS")
    spec["gases"]["A2"] = 1.
    eq = solve(spec, drc=False)
    assert abs(eq["TOF"]) < 1e-10
    print(f"Equilibrium net TOF={eq['TOF']:.6g}: PASS")
    spec["steps"][0]["dE"] = -.05
    result = solve(spec, drc=False)
    assert abs(result["log_kf_over_kr"][0] - .05/(8.617333262145e-5*600)) < 1e-12
    print("Detailed-balance log(kf/kr)=-dG/kT: PASS")
    spec["gas_corrections"] = {"B2": .02}
    spec["gases"]["B2"] = math.exp(.03/(8.617333262145e-5*600))
    assert abs(solve(spec, drc=False)["TOF"]) < 1e-10
    print("Gas free-energy corrections, nonzero-energy equilibrium: PASS")
    from unittest.mock import patch
    from types import SimpleNamespace
    import mkm_solver
    original = mkm_solver.root
    calls = [0]
    def force_fallback(fn, initial, **kw):
        calls[0] += 1
        return SimpleNamespace(x=initial) if calls[0] <= 3 else original(fn, initial, **kw)
    spec["gases"]["B2"] = 1.
    with patch.object(mkm_solver, "root", side_effect=force_fallback):
        fallback = solve(spec, drc=False)
    assert fallback["method"] == "BDF+root"
    assert fallback["residual"] < 1e-10
    print("Forced initial-root failure -> BDF log-coverage fallback: PASS")


if __name__ == "__main__":
    validate()
