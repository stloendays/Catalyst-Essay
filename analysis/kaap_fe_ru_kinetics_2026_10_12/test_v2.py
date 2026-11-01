"""Independent Cholewa Eq (11)/(12) tests and fairness checks."""
import math
import pytest
from model import R, FE, RU_CEO2, rate, kp_full, activities, equilibrium_extent, bed_sequence
from run_v2 import compare, critical_gain, local_replacement_gain, thermochemistry, INLET, T_K

def paper_equation(c,T,P):
    n,h,a=activities(T,P,INLET)
    z=a/h**1.5
    nterm=math.sqrt(kp_full(T))*math.sqrt(n)*z**(-c.alpha)-z**(1-c.alpha)
    den=1.
    for ads,p,scale in ((c.adsorption_h2,h,1.5),(c.adsorption_nh3,a,1.)):
        if ads:
            H,S,f=ads
            den+=math.exp(-H/(R*T)+S/R)*p**(scale*f)
    return c.k0*math.exp(-c.ea/(R*T))*nterm/den

@pytest.mark.parametrize("c",[FE,RU_CEO2])
@pytest.mark.parametrize("T",[623.15,673.15,698.15,723.15])
@pytest.mark.parametrize("P",[10.,45.,80.])
def test_exact_fitted_expression(c,T,P):
    assert math.isclose(rate(c,T,P,INLET),paper_equation(c,T,P),rel_tol=2e-13)

@pytest.mark.parametrize("eos",["ideal","srk"])
def test_equilibrium_zero_rate(eos):
    x=equilibrium_extent(T_K,80.,INLET,eos=eos)
    f=(1-x,3-3*x,.1+2*x)
    assert abs(rate(FE,T_K,80.,f,eos=eos))<1e-9
    assert abs(rate(RU_CEO2,T_K,80.,f,eos=eos))<1e-9

@pytest.mark.parametrize("P",[45.,80.])
@pytest.mark.parametrize("eos",["ideal","srk"])
def test_fe_first_better_order_but_not_better_than_fe(P,eos):
    r=compare(P,30.,30.,1.,eos=eos)
    assert r["all_Fe"]>r["Fe_then_Ru"]>r["Ru_then_Fe"]>r["all_Ru"]

def test_equal_material_mass_across_order():
    r=compare(80.,15.,45.,3.)
    explicit=bed_sequence(INLET,("Ru","Fe"),(45.,15.),(T_K,T_K),80.,ru_gain=3.)["X_N2"]
    assert math.isclose(r["Ru_then_Fe"],explicit,rel_tol=1e-12)

@pytest.mark.parametrize("eos",["ideal","srk"])
def test_hypothetical_7x_crossover(eos):
    r=compare(80.,30.,30.,7.,eos=eos)
    assert r["Fe_then_Ru"]>r["all_Fe"]>r["Ru_then_Fe"]
    assert 6.4<critical_gain(80.,30.,30.,eos=eos)<6.9

@pytest.mark.parametrize("T_C,nist,gb",[(400.,.231430603,.220346025),(425.,.185717676,.176427823),(450.,.148384705,.140727909)])
def test_thermo_anchor(T_C,nist,gb):
    r=thermochemistry(T_C+273.15)
    assert abs(r["yNH3_NIST"]-nist)<5e-7
    assert abs(r["yNH3_GB"]-gb)<5e-7

def test_parity_solver():
    g=critical_gain(80.,30.,30.)
    r=compare(80.,30.,30.,g)
    assert abs(r["Fe_then_Ru"]-r["all_Fe"])<2e-8
    assert local_replacement_gain(80.,60.)<g
