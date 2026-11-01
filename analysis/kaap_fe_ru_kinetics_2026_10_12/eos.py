"""SRK gas-phase fugacity sensitivity (NOT a source-calibrated process EOS).

The 2024 experimental paper used SRK with its own phase-equilibrium convention;
here all binary interactions are zero, an unverified sensitivity assumption.
"""
import math
import numpy as np

R = 8.314462618
CRITICAL = {
    "N2": (126.2, 33.98, 0.0372),
    "H2": (33.2, 12.80, -0.218),
    "NH3": (405.4, 113.53, 0.256),
}

def srk_phi(T, P_bar, flow, kij=0.):
    if not 0 <= kij <= 0.1:
        raise ValueError("Unfitted SRK binary-interaction sensitivity only")
    x = np.asarray(flow, dtype=float)
    if np.min(x) <= 0:
        raise ValueError("Positive flows required")
    y = x / sum(x)
    ai, bi = [], []
    for species in ("N2", "H2", "NH3"):
        Tc, Pc_bar, omega = CRITICAL[species]
        m = 0.480 + 1.574 * omega - 0.176 * omega**2
        ai.append(0.42747 * R**2 * Tc**2 / (Pc_bar * 1e5) *
                  (1 + m * (1 - math.sqrt(T / Tc)))**2)
        bi.append(0.08664 * R * Tc / (Pc_bar * 1e5))
    ai, bi = np.array(ai), np.array(bi)
    aij = np.sqrt(np.outer(ai, ai))
    aij[~np.eye(3, dtype=bool)] *= (1 - kij)
    a, b = float(y @ aij @ y), float(y @ bi)
    P = P_bar * 1e5
    A, B = a * P / (R*T)**2, b * P / (R*T)
    roots = np.roots([1, -1, A - B - B**2, -A*B])
    gas = [float(r.real) for r in roots if abs(r.imag) < 1e-7 and r.real > B]
    if not gas:
        raise ArithmeticError("No SRK gas root")
    Z = max(gas)
    lnphi = (bi/b) * (Z-1) - math.log(Z-B) - (A/B) * (
        2*(aij @ y)/a - bi/b) * math.log(1+B/Z)
    return tuple(float(v) for v in np.exp(lnphi))
