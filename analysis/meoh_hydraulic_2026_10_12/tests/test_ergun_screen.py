"""No-fabrication Ergun and source-TEA regression tests (synthetic hydraulics)."""
from __future__ import annotations

import json
import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from ergun_screen import (BedGeometry,GasInlet,ergun,ensure_feasible,process,
                          recost_recycle_from_dP)

ROOT=Path(__file__).resolve().parents[3]


def synthetic():
    """Illustrative unit-test-only bed. NOT claimed source or design geometry."""
    b=BedGeometry(parallel_beds=8,length_m=4.,inner_diameter_m=2.,
                  pellet_diameter_m=.005,pellet_sphericity=.9,
                  void_fraction=.45,packed_bulk_density_kg_m3=900.)
    g=GasInlet(pressure_bar=70.,temperature_K=550.,
               total_flow_kmol_h=3000.,viscosity_Pa_s=2e-5,
               mean_molecular_weight_kg_mol=.020,
               compressibility_Z=.9)
    return b,g


class ErgunHydraulicTests(unittest.TestCase):
    def test_geometry_and_gas_hard_validation(self):
        bed,gas=synthetic()
        self.assertGreater(bed.volume_m3,0)
        self.assertGreater(bed.total_catalyst_capacity_t,0)
        with self.assertRaises(ValueError):
            BedGeometry(8,4,2,.005,.9,1.0,900)
        with self.assertRaises(ValueError):
            BedGeometry(8,4,2,-.005,.9,.45,900)
        with self.assertRaises(ValueError):
            BedGeometry(0,4,2,.005,.9,.45,900)
        with self.assertRaises(ValueError):
            GasInlet(70,550,3000,-2e-5,.02,.9)

    def test_pressure_drop_has_correct_physics_and_zero_flow(self):
        bed,gas=synthetic()
        v=ergun(bed,gas)
        self.assertTrue(v["isothermal_positive_outlet_exists"])
        self.assertGreater(v["predicted_bed_pressure_drop_bar"],0)
        self.assertGreater(v["inlet_viscous_dPdz_Pa_m"],0)
        self.assertGreater(v["inlet_inertial_dPdz_Pa_m"],0)
        z=ergun(bed,GasInlet(70,550,0,2e-5,.02,.9))
        self.assertEqual(z["predicted_bed_pressure_drop_bar"],0)
        self.assertEqual(z["superficial_velocity_m_s"],0)

    def test_pressure_drop_convergence_for_small_losses(self):
        bed,gas=synthetic()
        bed=BedGeometry(bed.parallel_beds,.001,bed.inner_diameter_m,
                        bed.pellet_diameter_m,bed.pellet_sphericity,
                        bed.void_fraction,bed.packed_bulk_density_kg_m3)
        v=ergun(bed,gas)
        self.assertAlmostEqual(v["predicted_bed_pressure_drop_bar"],
                               v["constant_inlet_gradient_pressure_drop_bar"],delta=1e-7)

    def test_pressure_drop_monotonicity_flow_pellet_and_parallel_beds(self):
        b,g=synthetic()
        low=ergun(b,g)["predicted_bed_pressure_drop_bar"]
        hi=ergun(b,GasInlet(g.pressure_bar,g.temperature_K,
               2*g.total_flow_kmol_h,g.viscosity_Pa_s,
               g.mean_molecular_weight_kg_mol,g.compressibility_Z))["predicted_bed_pressure_drop_bar"]
        self.assertGreater(hi,low)
        fine=ergun(BedGeometry(b.parallel_beds,b.length_m,b.inner_diameter_m,
                    b.pellet_diameter_m/2,b.pellet_sphericity,
                    b.void_fraction,b.packed_bulk_density_kg_m3),g)
        self.assertGreater(fine["predicted_bed_pressure_drop_bar"],low)
        spread=ergun(BedGeometry(b.parallel_beds*2,b.length_m,b.inner_diameter_m,
                      b.pellet_diameter_m,b.pellet_sphericity,
                      b.void_fraction,b.packed_bulk_density_kg_m3),g)
        self.assertLess(spread["predicted_bed_pressure_drop_bar"],low)

    def test_capacity_and_pressure_masks_are_independent(self):
        b,g=synthetic()
        v=ergun(b,g)
        dp=v["predicted_bed_pressure_drop_bar"]
        inventory=b.total_catalyst_capacity_t
        self.assertTrue(ensure_feasible(v,maximum_dp_bar=dp+.01,
                                        required_catalyst_t=inventory-.01)["feasible"])
        self.assertFalse(ensure_feasible(v,maximum_dp_bar=dp-.0001,
                                         required_catalyst_t=inventory-.01)["feasible"])
        self.assertFalse(ensure_feasible(v,maximum_dp_bar=dp+.01,
                                         required_catalyst_t=inventory+.01)["feasible"])

    def test_missing_actual_bed_properties_fail_closed(self):
        p=ROOT/"analysis/meoh_hydraulic_2026_10_12/bed_input_requirements.json"
        out=process(json.loads(p.read_text()))
        self.assertEqual(out["status"],"blocked_missing_physical_measurements")
        self.assertFalse(out["any_pressure_drop_claim"])
        self.assertIn("geometry.pellet_diameter_m",out["missing_required_source_fields"])
        self.assertIn("fluid.viscosity_Pa_s",out["missing_required_source_fields"])
        self.assertIn("physical_constraints.maximum_allowable_bed_deltaP_bar",out["missing_required_source_fields"])

    def test_model_repricing_at_original_fixed_drop_is_exact(self):
        sys.path.insert(0,str(ROOT/"data/meoh"))
        import meoh_general_model as G
        c=dict(X=.19,SMeOH=.99,SCO=.01,SCH4=0.,STY=.55)
        src=G.cost(c,purge=.02,x_co="recycled_central",P_bar=100.,
                   h2_co2=4,T_C=200,STY_per_g_cat=.55)
        # This must reconstruct the ORIGINAL cost for the exact fixed
        # model assumption. Otherwise the additional capex equation drifted.
        repriced=recost_recycle_from_dP(src,100,G.M.LOOP_DP_BAR)
        self.assertAlmostEqual(float(repriced["hydraulic_repriced_NPC_EUR_t"]),
                               float(src["cost_eur_t"]),delta=1e-7)
        self.assertAlmostEqual(float(repriced["hydraulic_repriced_recycle_MW"]),
                               float(src["P_rec_MW"]),delta=1e-10)
        smaller=recost_recycle_from_dP(src,100,.75)
        larger=recost_recycle_from_dP(src,100,3.)
        self.assertLess(float(smaller["hydraulic_repriced_NPC_EUR_t"]),
                        float(src["cost_eur_t"]))
        self.assertGreater(float(larger["hydraulic_repriced_NPC_EUR_t"]),
                           float(src["cost_eur_t"]))


if __name__=="__main__":
    unittest.main()
