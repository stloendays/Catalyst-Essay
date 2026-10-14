"""PR + actual uploaded SI S27 k(T), two-phase flash, and process interfaces.

SI supplies Ar/H2/N2/O2--NH3 interactions, not CH4--NH3. Missing pairs are
explicit engineering assumptions. Neither ms2 reproduction nor all original
literature pointwise passes are conditions for operating this research model.
Temperatures of the cold section are not applied to the hot-reactor kinetics.
"""
from __future__ import annotations
from dataclasses import dataclass
import json
import math
from pathlib import Path
import numpy as np
from scipy.optimize import brentq, minimize

HERE = Path(__file__).resolve().parent
PARAMS = json.loads((HERE / "si_parameters.json").read_text())
NAMES = ("N2", "H2", "CH4", "Ar", "NH3")
R = 8.31446261815324
TC = np.array([126.192, 33.1443326883, 190.5640026513, 150.687, 405.5599999733])
PC = np.array([3395800.444647145, 1296357.6060553, 4599200.4742824, 4863000.544876669, 11363391.157414673])
OMEGA = np.array([.0372, -.219, .01142, -.00219, .2556905229865023])
MW = np.array([28.0134, 2.01588, 16.0425, 39.948, 17.031])
# Explicit constant-Cp engineering approximation around the cold section,
# not an SI result; the reference offset cancels in nonreactive cold duties.
CP_IDEAL = np.array([29.124, 28.836, 35.69, 20.786, 35.65])
NU = np.array([-.5, -1.5, 0., 0., 1.])


def fractions(z):
    z = np.asarray(z, dtype=float)
    if z.shape != (5,) or not np.all(np.isfinite(z)) or np.min(z) < 0 or z.sum() <= 0:
        raise ValueError("Five finite nonnegative molar fractions/flows required")
    return z / z.sum()


def interactions(T, methane_k=0.0, mode="si2024"):
    """Symmetric matrix and exact d(kij)/dT; absent CH4 term is a scenario."""
    if not 200 <= T <= 450:
        raise ValueError("Cold-section numerical envelope is 200--450 K, not a claimed source validity range")
    k = np.zeros((5, 5)); dk = k.copy()
    if mode == "si2024":
        for i, name in enumerate(NAMES[:-1]):
            if name in PARAMS["PR"]:
                a0, a1, a2, _ = PARAMS["PR"][name]
                k[i, 4] = k[4, i] = a0 + a1*T + a2*T*T
                dk[i, 4] = dk[4, i] = a1 + 2*a2*T
    elif mode != "zero":
        raise ValueError("EOS mode must be 'si2024' or 'zero'")
    k[2, 4] = k[4, 2] = methane_k
    return k, dk


def roots_pr(A, B):
    # Numpy polynomial root computation avoids fragile discriminant branches.
    rr = np.roots([1., -(1.-B), A-3*B*B-2*B, -A*B+B*B+B**3])
    valid = sorted(float(v.real) for v in rr if abs(v.imag) < 1e-8 and v.real > B+1e-12)
    if not valid:
        raise RuntimeError("No admissible PR volume root")
    return valid


@dataclass
class Flash:
    beta: float
    x: np.ndarray
    y: np.ndarray
    residual: float
    iterations: int
    phase: str
    gibbs_improvement: float


class State:
    """Fixed T,P precomputes interactions for fast recycle iteration."""
    def __init__(self, T, P, methane_k=0., mode="si2024"):
        self.T, self.P = float(T), float(P)
        if not 0 < P <= 1e8:
            raise ValueError("Absolute pressure must be 0 < P <= 100 MPa")
        self.k, self.dk = interactions(T, methane_k, mode)
        kap = .37464 + 1.54226*OMEGA - .26992*OMEGA**2
        sq = np.sqrt(T/TC); f = 1.+kap*(1.-sq)
        aa0 = .45724*R**2*TC**2/PC
        self.a = aa0*f*f
        da = -aa0*f*kap/(TC*sq)
        aa = np.sqrt(np.outer(self.a, self.a))
        self.aij = aa*(1.-self.k)
        self.daij = .5*self.aij*(da[:,None]/self.a[:,None]+da[None,:]/self.a[None,:])-aa*self.dk
        self.b = .07780*R*TC/PC

    def properties(self, z, phase="vapor"):
        z = fractions(z)
        am = float(z@self.aij@z); bm = float(z@self.b)
        A = am*self.P/(R*self.T)**2; B = bm*self.P/(R*self.T)
        candidates = roots_pr(A,B)
        out = []
        for Z in candidates:
            fac = math.log((Z+(1+math.sqrt(2))*B)/(Z+(1-math.sqrt(2))*B))
            lp = self.b/bm*(Z-1)-math.log(Z-B)-A/(2*math.sqrt(2)*B)*(2*(self.aij@z)/am-self.b/bm)*fac
            hdep = R*self.T*(Z-1)+(self.T*float(z@self.daij@z)-am)/(2*math.sqrt(2)*bm)*fac
            h = float(z@CP_IDEAL)*(self.T-298.15)+hdep
            out.append((Z,lp,h))
        if phase=="liquid": return out[0]
        if phase=="vapor": return out[-1]
        if phase=="stable": return min(out,key=lambda v:float(z@v[1]))
        raise ValueError("Unknown phase-root selection")

    def gibbs(self,z,phase="stable"):
        z=fractions(z); active=z>0
        lp=self.properties(z,phase)[1]
        return float(z[active]@(np.log(z[active])+lp[active]))

    def stability(self,z,plane=None,starts=None):
        """Multi-start local TPD minimization, not a proof of global stability."""
        z=fractions(z); mask=z>1e-16; ix=np.flatnonzero(mask)
        if plane is None:
            lp=self.properties(z,"stable")[1]
            plane=np.log(np.maximum(z,1e-300))+lp
        n=len(ix)
        if n==1: return {"minimum_tpd":0.,"trials":1,"candidate":z.tolist()}
        if starts is None:
            starts=[z, np.array([.01,.01,.01,.01,.96]), np.array([.20,.74,.02,.02,.02])]
            starts += [np.eye(5)[j]*.9+.1*z for j in ix]
        best=(0.,z)
        for initial in starts:
            init=np.maximum(np.asarray(initial)[mask],1e-14); init/=init.sum()
            def unpack(t):
                logits=np.append(t,0.); logits-=max(logits)
                w=np.exp(logits);w/=sum(w)
                full=np.zeros(5);full[mask]=w
                return full
            def objective(t):
                w=unpack(t); lp=self.properties(w,"stable")[1]
                return float(w[mask]@(np.log(w[mask])+lp[mask]-plane[mask]))
            x0=np.log(init[:-1]/init[-1])
            res=minimize(objective,x0,method="L-BFGS-B",bounds=[(-32,32)]*(n-1),options={"maxiter":120,"ftol":1e-12})
            if float(res.fun)<best[0]:best=(float(res.fun),unpack(res.x))
        return {"minimum_tpd":best[0],"trials":len(starts),"candidate":best[1].tolist(),"scope":"multi-start local TPD check"}

    def quick_stability(self,z):
        """Successive-substitution TPD seeds for inner-loop phase detection.

        Final converged process states still receive multi-start minimization.
        """
        z=fractions(z); mask=z>1e-16
        plane=np.log(np.maximum(z,1e-300))+self.properties(z,"stable")[1]
        starts=[np.array([.001,.001,.001,.001,.996]),
                np.array([.22,.74,.015,.015,.01])]
        best=(0.,z); all_ok=True
        for initial in starts:
            w=initial.copy();w[~mask]=0;w/=sum(w)
            converged=False
            for _ in range(120):
                lp=self.properties(w,"stable")[1]
                W=np.exp(np.clip(plane-lp,-700,100));W[~mask]=0
                new=W/sum(W)
                if np.max(np.abs(new-w))<1e-10:
                    w=new;converged=True;break
                w=.25*w+.75*new
            lp=self.properties(w,"stable")[1]
            val=float(w[mask]@(np.log(w[mask])+lp[mask]-plane[mask]))
            if val<best[0]:best=(val,w)
            all_ok=all_ok and converged
        if not all_ok and best[0]>-1e-8:return self.stability(z)
        return {"minimum_tpd":best[0],"candidate":best[1].tolist(),"scope":"two-start stationary TPD screen"}

    def flash(self,z,stability=False):
        z=fractions(z); mask=z>1e-16
        lnK=np.log(PC/self.P)+5.373*(1+OMEGA)*(1-TC/self.T)
        for it in range(180):
            K=np.exp(np.clip(lnK,-40,40))
            rr=lambda b:float(np.sum(z*(K-1)/(1+b*(K-1))))
            f0,f1=rr(0.),rr(1.)
            if f0<=0 or f1>=0:
                # Do not turn 'Wilson has no root' into an unverified phase assertion.
                chk=self.quick_stability(z)
                if chk["minimum_tpd"] >= -1e-8:
                    single=self.properties(z,"stable")[0]
                    beta=1. if single>.45 else 0.
                    return Flash(beta,z.copy(),z.copy(),0.,it+1,"single_vapor" if beta else "single_liquid",0.)
                w=np.array(chk["candidate"])
                if w[4]>z[4]:lnK=np.log(np.maximum(z,1e-20)/np.maximum(w,1e-20))
                else:lnK=np.log(np.maximum(w,1e-20)/np.maximum(z,1e-20))
                # An incipient tangent-plane trial sits exactly at beta=0/1.
                # Scale K into an interior RR bracket without changing its
                # composition ratios. This is a numerical seed, not a fit.
                trial=np.exp(np.clip(lnK,-35,35))
                alo=1.0/float(z@trial); ahi=float(z@(1.0/trial))
                if ahi <= alo*(1+1e-12):
                    raise RuntimeError("Unstable phase trial has no distinct split seed")
                lnK += .5*(math.log(alo)+math.log(ahi))
                continue
            b=brentq(rr,0.,1.,xtol=2e-14)
            x=z/(1+b*(K-1)); y=K*x
            lx=self.properties(x,"liquid")[1];ly=self.properties(y,"vapor")[1]
            desired=lx-ly
            error=float(np.max(np.abs((lnK-desired)[mask])))
            if error<2e-9:
                g=(1-b)*self.gibbs(x,"liquid")+b*self.gibbs(y,"vapor")
                dg=g-self.gibbs(z)
                if dg>2e-7:raise RuntimeError("Flash raises Gibbs energy relative to single phase")
                if np.max(np.abs(z-((1-b)*x+b*y)))>1e-9:raise RuntimeError("Flash violates component balance")
                if stability:
                    plane=np.log(np.maximum(x,1e-300))+lx
                    chk=self.stability(z,plane,[x,y,z])
                    if chk["minimum_tpd"] < -1e-6:raise RuntimeError("Flash fails local tangent-plane stability check")
                return Flash(float(b),x,y,error,it+1,"two_phase",dg)
            lnK=.3*lnK+.7*desired
        raise RuntimeError("PR flash did not converge; no observed phase is substituted")

    def split(self,flow,stability=False):
        flow=np.asarray(flow,dtype=float); n=float(flow.sum())
        r=self.flash(flow,stability)
        return n*r.beta*r.y, n*(1-r.beta)*r.x, r


def compression(flow, T, Pin, Pout, methane_k=0.,mode="si2024",eta=.75):
    if not 0<Pin<=Pout or not 0<eta<=1:raise ValueError("Invalid compressor boundary/efficiency")
    z=fractions(flow); total=float(sum(flow))
    logs=np.linspace(math.log(Pin),math.log(Pout),17)
    Z=np.array([State(T,math.exp(v),methane_k,mode).properties(z)[0] for v in logs])
    integ=(logs[-1]-logs[0])/48*(Z[0]+Z[-1]+4*sum(Z[1:-1:2])+2*sum(Z[2:-1:2]))
    reversible=total*1000/3600*R*T*integ/1e6
    return {"reversible_MW":float(reversible),"shaft_MW":float(reversible/eta),"eta_assumed":eta,"scope":"isothermal equivalent work / assumed efficiency, not vendor compressor map"}
