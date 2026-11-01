"""Thermodynamic, stoichiometric, and numerical regression tests."""
import math
import pytest
from model import FE,RU_CEO2,rate,kp_full,activities,equilibrium_extent,stage,bed_sequence
from run import compare,threshold,FEED,T

def test_gibbs_equilibrium():
    assert 8e-5<kp_full(T)<1e-4
    assert kp_full(673.15)>kp_full(T)>kp_full(723.15)

@pytest.mark.parametrize("eos",["ideal","srk"])
def test_equilibrium_rate_vanishes(eos):
    x=equilibrium_extent(T,80,FEED,eos)
    f=(1-x,3-3*x,.1+2*x)
    a,b,c=activities(T,80,f,eos)
    assert math.isclose(c*c/(a*b**3),kp_full(T),rel_tol=2e-8)
    assert abs(rate(FE,T,80,f,eos=eos))<1e-10
    assert abs(rate(RU_CEO2,T,80,f,eos=eos))<1e-10

@pytest.mark.parametrize("cat",[FE,RU_CEO2])
def test_rate_sign_changes_across_equilibrium(cat):
    x=equilibrium_extent(T,80,FEED)*1.01
    assert rate(cat,T,80,FEED)>0
    assert rate(cat,T,80,(1-x,3-3*x,.1+2*x))<0

def test_mass_balance():
    f=stage(FEED,FE,T,80,60)
    x=1-f[0]
    assert math.isclose(f[1],3-3*x,abs_tol=2e-10)
    assert math.isclose(f[2],.1+2*x,abs_tol=2e-10)

def test_equal_fe_stages():
    x=stage(FEED,FE,T,80,60)
    y=bed_sequence(FEED,("Fe","Fe"),(30,30),(T,T),80)["outlet"]
    assert all(math.isclose(a,b,abs_tol=1e-8) for a,b in zip(x,y))

def test_original_not_forced_to_win():
    r=compare(80,60,1.)
    assert r["Fe_only"]>r["Fe_to_Ru"]>r["Ru_to_Fe"]
    assert math.isclose(r["Fe_only"],.167364,abs_tol=8e-5)

def test_hypothetical_crossover():
    r=compare(80,60,20.)
    assert r["Fe_to_Ru"]>r["Ru_to_Fe"]>r["Fe_only"]
    assert math.isclose(r["Fe_to_Ru"],.220117,abs_tol=8e-5)
    assert 6.4<threshold(80,60)<6.9
    assert 10.8<threshold(80,60,mode="dh")<11.3

def test_source_immutability():
    assert RU_CEO2.adsorption_h2[0]==-87100.
    assert FE.ea==144000.

def test_invalid():
    with pytest.raises(ValueError):stage(FEED,FE,T,80,-1)
    with pytest.raises(ValueError):rate(FE,T,80,FEED,-1)
    with pytest.raises(ValueError):
        bed_sequence(FEED,("Fe","Ru"),(30,30),(T,T),80,ru_h2_shift_j=40000)
