"""Run ONLY in IDAES environment. JSON input/output, no network or LLM calls.

IDAES modular Ideal/FTPx property package, NIST Shomate coefficients from
the fixed gate data. Pure-property expressions are independently assembled
as Pyomo expressions. Ideal liquid enthalpy = ideal gas minus CRC latent heat;
flash is Raoult (or insoluble permanent gas), not an EOS/aqueous chemistry model.
IDAES reference: https://idaes-pse.readthedocs.io/en/stable/reference_guides/
model_libraries/generic/property_models/generic/index.html
"""
from __future__ import annotations
import contextlib
import json
from pathlib import Path
import sys


def solve_case(case):
    import math
    import pyomo.environ as pyo
    from pyomo.opt import check_optimal_termination
    from idaes.core import FlowsheetBlock, Component, VaporPhase, LiquidPhase, PhaseType
    from idaes.models.properties.modular_properties.base.generic_property import GenericParameterBlock
    from idaes.models.properties.modular_properties.base.generic_reaction import GenericReactionParameterBlock
    from idaes.models.properties.modular_properties.base.utility import ConcentrationForm
    from idaes.models.properties.modular_properties.state_definitions import FTPx
    from idaes.models.properties.modular_properties.eos.ideal import Ideal
    from idaes.models.properties.modular_properties.phase_equil import SmoothVLE
    from idaes.models.properties.modular_properties.phase_equil.bubble_dew import IdealBubbleDew
    from idaes.models.properties.modular_properties.phase_equil.forms import fugacity
    from idaes.models.properties.modular_properties.reactions.dh_rxn import constant_dh_rxn
    from idaes.models.properties.modular_properties.reactions.equilibrium_forms import log_power_law_equil
    from idaes.models.properties.modular_properties.reactions.equilibrium_constant import ConstantKeq
    from idaes.models.unit_models import (PressureChanger, Heater, Flash, Mixer, Separator,
                                         StoichiometricReactor, EquilibriumReactor, GibbsReactor)
    from idaes.models.unit_models.pressure_changer import ThermodynamicAssumption
    from idaes.models.unit_models.mixer import MomentumMixingType
    from idaes.models.unit_models.separator import SplittingType
    from idaes.core.util.model_statistics import degrees_of_freedom
    from idaes.core.util import scaling as iscale
    # Import fixed physical DATA only (no harness unit implementations).
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
    from physics_gate import SHOMATE,THERMO,formula_elements,formula_mw
    from unitops_equipment import ANTOINE, PERMANENT
    # The runner imports the source table above, never calls its computations.
    units=pyo.units
    latent={'H2O':40.65,'NH3':23.33,'CH3OH':35.21,'C2H5OH':38.56,'C3H8':19.04,'CO2':15.33}

    def raw(coeff,t):
        a,b,c,d,e,f,g,h=coeff; z=t/1000
        return a*z+b*z*z/2+c*z**3/3+d*z**4/4-e/z+f, a*pyo.log(z)+b*z+c*z*z/2+d*z**3/3-e/(2*z*z)+g

    def thermo_expr(s,T,which):
        hf,sref,cp=THERMO[s]
        if s not in SHOMATE:
            return (hf*1000+cp*(T-298.15)) if which=='h' else sref+cp*pyo.log(T/298.15)
        rows=SHOMATE[s]; initial=raw(rows[0][2],298.15)[0 if which=='h' else 1]
        offset=(hf if which=='h' else sref)-pyo.value(initial)
        expressions=[]
        for i,(lo,hi,c) in enumerate(rows):
            if i:
                boundary=rows[i-1][1]
                offset+=pyo.value(raw(rows[i-1][2],boundary)[0 if which=='h' else 1]-raw(c,boundary)[0 if which=='h' else 1])
            expr=raw(c,T)[0 if which=='h' else 1]+offset
            expressions.append(expr*(1000 if which=='h' else 1))
        expr=expressions[-1]
        for i in reversed(range(len(rows)-1)):
            expr=pyo.Expr_if(IF=T<=rows[i][1],THEN=expressions[i],ELSE=expr)
        return expr

    class Gas:
        class enth_mol_ig_comp:
            @staticmethod
            def return_expression(b,c,T):
                return thermo_expr(c.local_name,T/units.K,'h')*units.J/units.mol
        class entr_mol_ig_comp:
            @staticmethod
            def return_expression(b,c,T):
                return thermo_expr(c.local_name,T/units.K,'s')*units.J/units.mol/units.K
        class cp_mol_ig_comp:
            @staticmethod
            def return_expression(b,c,T):
                s=c.local_name; t=T/units.K/1000
                if s not in SHOMATE: cp=THERMO[s][2]
                else:
                    expressions=[a+bb*t+cc*t*t+d*t**3+e/t**2 for lo,hi,(a,bb,cc,d,e,*_) in SHOMATE[s]]
                    cp=expressions[-1]
                    for i in reversed(range(len(expressions)-1)):
                        cp=pyo.Expr_if(IF=T/units.K<=SHOMATE[s][i][1],THEN=expressions[i],ELSE=cp)
                return cp*units.J/units.mol/units.K
    class Liquid:
        class enth_mol_liq_comp:
            @staticmethod
            def return_expression(b,c,T):
                return Gas.enth_mol_ig_comp.return_expression(b,c,T)-latent[c.local_name]*1000*units.J/units.mol
        class dens_mol_liq_comp:
            @staticmethod
            def return_expression(b,c,T):
                # Not used in equilibrium, work or energy: no liquid pump supported.
                return 1e4*units.mol/units.m**3
    psat_rows={}
    class Psat:
        @staticmethod
        def return_expression(b,c,T,dT=False):
            if dT: raise ValueError('psat derivatives not supported')
            _,_,a,bb,cc=psat_rows[c.local_name]
            return 10**(a-bb/(T/units.K+cc))*1e5*units.Pa

    def package(species,flash,nominal):
        components={}
        for s in species:
            if s not in THERMO: raise ValueError('unsupported species '+s)
            c=dict(type=Component,elemental_composition=formula_elements(s),
                   cp_mol_ig_comp=Gas,enth_mol_ig_comp=Gas,entr_mol_ig_comp=Gas,
                   parameter_data=dict(mw=(formula_mw(s)/1000,units.kg/units.mol)))
            if flash:
                if s in PERMANENT or (s in ('CH4','CO2') and nominal>=({'CH4':190.564,'CO2':304.1282}[s])):
                    c['valid_phase_types']=[PhaseType.vaporPhase]
                else:
                    row=next((r for r in ANTOINE.get(s,[]) if r[0]<=nominal<=r[1]),None)
                    if row is None or s not in latent: raise ValueError('flash lacks validated liquid/psat data for '+s)
                    psat_rows[s]=row
                    c.update(enth_mol_liq_comp=Liquid,dens_mol_liq_comp=Liquid,pressure_sat_comp=Psat,
                             phase_equilibrium_form={('Vap','Liq'):fugacity})
            components[s]=c
        cfg=dict(components=components,phases={'Vap':dict(type=VaporPhase,equation_of_state=Ideal)},
                 base_units=dict(time=units.s,length=units.m,mass=units.kg,amount=units.mol,temperature=units.K),
                 state_definition=FTPx,state_bounds=dict(flow_mol=(1e-12,1000,1e9),temperature=(298.15,nominal,6000),pressure=(1,1e5,1e9)),
                 pressure_ref=(1e5,units.Pa),temperature_ref=(298.15,units.K))
        if flash:
            cfg['phases']['Liq']=dict(type=LiquidPhase,equation_of_state=Ideal)
            cfg.update(phases_in_equilibrium=[('Vap','Liq')],phase_equilibrium_state={('Vap','Liq'):SmoothVLE},bubble_dew_method=IdealBubbleDew)
        return GenericParameterBlock(**cfg)

    def fix_inlet(port,feed,T,P):
        if T<298.15 or P<=0 or not feed or any(n<0 or not math.isfinite(n) for n in feed.values()) or sum(feed.values())<=0:
            raise ValueError('invalid inlet or T below fixed gas thermo domain')
        total=sum(feed.values()); port.flow_mol[0].fix(total*1000)
        port.temperature[0].fix(T); port.pressure[0].fix(P*1e5)
        for t,s in port.mole_frac_comp:
            port.mole_frac_comp[t,s].fix(feed.get(s,0)/total)

    def read_port(port,species):
        n=pyo.value(port.flow_mol[0])/1000
        return dict(T_out_K=pyo.value(port.temperature[0]),P_out_bar=pyo.value(port.pressure[0])/1e5,
                    outlet_kmol_per_t={s:n*pyo.value(port.mole_frac_comp[0,s]) for s in species})

    solver=pyo.SolverFactory('ipopt')
    if not solver.available(exception_flag=False): raise RuntimeError('ipopt unavailable: check IDAES_BIN/PATH')
    solver.options.update(dict(tol=1e-9,max_iter=1000))
    outputs=[]; by_name={}; m=pyo.ConcreteModel(); m.fs=FlowsheetBlock(dynamic=False)
    for idx,spec in enumerate(case['units']):
        kind=spec['type']; name=spec.get('name',str(idx))
        if name in by_name: raise ValueError('duplicate name')
        feed=spec.get('feed')
        if spec.get('inlet_from'):
            upstream=by_name[spec['inlet_from']]; feed=upstream['outlet_kmol_per_t']
        if not feed: raise ValueError('explicit feed or prior inlet_from required')
        tin=spec['T_in_K']; pin=spec['P_in_bar']; tout=spec.get('T_out_K',tin); pout=spec.get('P_out_bar',pin)
        species=sorted(set(feed).union(*(set(r) for r in spec.get('nu_list',[]))))
        if kind=='Mixer': species=sorted(set().union(*(set(f['feed']) for f in spec['inlets'])))
        pp=package(species,kind=='Flash',tout); setattr(m.fs,'props_'+str(idx),pp)
        kw=dict(property_package=pp)
        if kind in ('Compressor','PressureChanger'):
            u=PressureChanger(**kw,compressor=pout>=pin,thermodynamic_assumption=ThermodynamicAssumption.isentropic)
        elif kind=='Heater': u=Heater(**kw,has_pressure_change=True)
        elif kind=='Flash': u=Flash(**kw,has_heat_transfer=True,has_pressure_change=True)
        elif kind=='Mixer': u=Mixer(**kw,inlet_list=['in'+str(i) for i in range(len(spec['inlets']))],momentum_mixing_type=MomentumMixingType.none)
        elif kind=='Separator': u=Separator(**kw,outlet_list=['product','tail'],split_basis=SplittingType.componentFlow)
        elif kind in ('EquilibriumReactor','StoichiometricReactor'):
            reactions={}
            for j,nu in enumerate(spec['nu_list']):
                # Equilibrium at specified T/P; K_y from property package standard
                # H/S (no harness equilibrium solver or supplied conversion).
                t=tout
                dg=sum(v*(pyo.value(thermo_expr(s,t,'h'))-t*pyo.value(thermo_expr(s,t,'s'))) for s,v in nu.items())
                ky=math.exp(-dg/(8.314462618*t))*pout**(-sum(nu.values()))
                reactions['r'+str(j)]=dict(stoichiometry={('Vap',s):v for s,v in nu.items()},
                    heat_of_reaction=constant_dh_rxn,equilibrium_constant=ConstantKeq,equilibrium_form=log_power_law_equil,
                    concentration_form=ConcentrationForm.moleFraction,
                    parameter_data=dict(dh_rxn_ref=(sum(v*pyo.value(thermo_expr(s,t,'h')) for s,v in nu.items()),units.J/units.mol),
                                        k_eq_ref=(ky,units.dimensionless)))
            if not reactions: raise ValueError('nu_list required')
            if kind=='StoichiometricReactor':
                # IDAES stoichiometric unit uses rate_reaction_stoichiometry;
                # a rate package with zero fixed Arrhenius rate is never evaluated.
                from idaes.models.properties.modular_properties.reactions.rate_constant import arrhenius
                from idaes.models.properties.modular_properties.reactions.rate_forms import power_law_rate
                rates={k:dict(stoichiometry=v['stoichiometry'],heat_of_reaction=constant_dh_rxn,
                            rate_constant=arrhenius,rate_form=power_law_rate,concentration_form=ConcentrationForm.moleFraction,
                            parameter_data=dict(dh_rxn_ref=v['parameter_data']['dh_rxn_ref'],
                                                arrhenius_const=(0.,units.mol/units.m**3/units.s),energy_activation=(0.,units.J/units.mol))) for k,v in reactions.items()}
                rp=GenericReactionParameterBlock(property_package=pp,rate_reactions=rates,base_units=dict(pp.config.base_units))
            else: rp=GenericReactionParameterBlock(property_package=pp,equilibrium_reactions=reactions,base_units=dict(pp.config.base_units))
            setattr(m.fs,'rxn_'+str(idx),rp)
            cls=StoichiometricReactor if kind=='StoichiometricReactor' else EquilibriumReactor
            if kind=='EquilibriumReactor': kw.update(has_rate_reactions=False,has_equilibrium_reactions=True)
            u=cls(**kw,reaction_package=rp,has_heat_transfer=True,has_pressure_change=True)
        elif kind=='GibbsReactor': u=GibbsReactor(**kw,has_heat_transfer=True,has_pressure_change=True)
        else: raise ValueError('unsupported IDAES unit type '+kind)
        setattr(m.fs,'unit_'+str(idx),u)
        if kind=='Mixer':
            for j,f in enumerate(spec['inlets']): fix_inlet(getattr(u,'in'+str(j)),f['feed'],f['T_in_K'],f['P_in_bar'])
            u.outlet.pressure[0].fix(pout*1e5)
        else: fix_inlet(u.inlet,feed,tin,pin)
        if kind in ('Compressor','PressureChanger'):
            u.outlet.pressure[0].fix(pout*1e5); u.efficiency_isentropic[0].fix(spec.get('eta_isentropic',.75))
        elif kind=='Separator':
            for s in species: u.split_fraction[0,'product',s].fix(spec['split_fraction'][s])
        elif kind!='Mixer':
            port=u.vap_outlet if kind=='Flash' else u.outlet
            port.temperature[0].fix(tout); u.deltaP[0].fix((pout-pin)*1e5)
            if kind=='StoichiometricReactor':
                for j,x in enumerate(spec['extents_kmol_per_t']): u.control_volume.rate_reaction_extent[0,'r'+str(j)].fix(x*1000)
        dof=degrees_of_freedom(u)
        if dof!=0: raise ValueError(f'{name}: degrees of freedom {dof}, expected 0')
        # Scale balance equations to keep the synthetic throughput well conditioned.
        iscale.calculate_scaling_factors(u)
        result=solver.solve(u,tee=False)
        if not check_optimal_termination(result): raise RuntimeError(f'{name}: {result.solver.termination_condition}')
        port=u.vap_outlet if kind=='Flash' else u.product if kind=='Separator' else u.outlet
        out=dict(name=name,type=kind,**read_port(port,species),solver_status=str(result.solver.termination_condition))
        if kind=='Flash':
            liquid=read_port(u.liq_outlet,species)
            out['vapor_kmol_per_t']=out['outlet_kmol_per_t']; out['liquid_kmol_per_t']=liquid['outlet_kmol_per_t']
            out['outlet_kmol_per_t']={s:out['vapor_kmol_per_t'][s]+out['liquid_kmol_per_t'][s] for s in species}
            out['vapor_fraction']=sum(out['vapor_kmol_per_t'].values())/sum(feed.values())
        if kind=='Separator': out['tail_kmol_per_t']=read_port(u.tail,species)['outlet_kmol_per_t']
        if hasattr(u,'work_mechanical'): out['power_GJ_per_t']=pyo.value(u.work_mechanical[0])/1e9
        if hasattr(u,'heat_duty'): out['heat_duty_GJ_per_t']=pyo.value(u.heat_duty[0])/1e9
        outputs.append(out); by_name[name]=out
    return dict(ok=True,solver_status='optimal',units=outputs,property_basis='NIST ideal gas; Raoult ideal liquid; 1 t/s synthetic basis')


if __name__=='__main__':
    target=Path(sys.argv[2])
    try:
        # IDAES/Pyomo diagnostic logging must not corrupt JSON protocol.
        with contextlib.redirect_stdout(sys.stderr):
            result=solve_case(json.loads(Path(sys.argv[1]).read_text(encoding='utf-8')))
    except Exception as exc:
        result=dict(ok=False,error=f'{type(exc).__name__}: {exc}')
    target.write_text(json.dumps(result,allow_nan=False),encoding='utf-8')
    sys.exit(0 if result['ok'] else 1)
