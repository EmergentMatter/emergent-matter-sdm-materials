"""Tests for the second sourcing-backlog batch: seven new Tier-1 materials.

Covers C93200 bearing bronze, AlN, alumina, MuMETAL, Alnico 5, Stycast 2850FT
and TPU. Every value below was read
from the vendor document named in the entry's ``s_source`` on 2026-09-17.
"""

from __future__ import annotations

import pytest

from emergent_matter_materials import get, get_material

_NEW = {
    "alumina_ad96": "ceramic",
    "aln_maruwa_an170": "ceramic",
    "stycast_2850ft": "polymer",
    "tpu_elastollan_1195a": "elastomer",
    "c93200_bearing_bronze": "metal",
    "alnico_5_cast": "magnet",
    "mu_metal": "soft_magnetic",
}


@pytest.mark.parametrize(("s_id", "s_category"), sorted(_NEW.items()))
def test_present_with_category(s_id, s_category):
    m = get_material(s_id)
    assert m.s_category == s_category
    assert m.s_specification.strip()
    assert m.crystal_anisotropy is None


@pytest.mark.parametrize(
    ("s_alias", "s_id"),
    [
        ("AD96", "alumina_ad96"),
        ("Alumina_96", "alumina_ad96"),
        ("AlN_AN170", "aln_maruwa_an170"),
        ("Stycast_2850FT", "stycast_2850ft"),
        ("TPU_95A", "tpu_elastollan_1195a"),
        ("Elastollan_1195A", "tpu_elastollan_1195a"),
        ("C93200", "c93200_bearing_bronze"),
        ("SAE_660", "c93200_bearing_bronze"),
        ("Alnico_5", "alnico_5_cast"),
        ("AlNiCo_5", "alnico_5_cast"),
        ("MuMETAL", "mu_metal"),
        ("Mu_Metal", "mu_metal"),
    ],
)
def test_aliases_resolve(s_alias, s_id):
    assert get_material(s_alias).s_id == s_id


def test_alumina_ad96_values():
    assert get("AD96", "E") == pytest.approx(303e9)
    assert get("AD96", "nu") == pytest.approx(0.21)
    assert get("AD96", "sigma_flex") == pytest.approx(343e6)
    assert get("AD96", "sigma_c") == pytest.approx(2068e6)
    assert get("AD96", "rho") == pytest.approx(3720.0)
    assert get("AD96", "k_thermal") == pytest.approx(24.7)
    assert get("AD96", "CTE") == pytest.approx(8.2e-6)
    assert get("AD96", "epsilon_r") == pytest.approx(9.0)
    m = get_material("alumina_ad96")
    assert "LOWER BOUND" in m.electromagnetic.resistivity_at_20C.s_condition
    assert m.structural.hardness_vickers is None  # Knoop, not Vickers, on the sheet


def test_aln_an170_values():
    assert get("AlN_AN170", "k_thermal") == pytest.approx(180.0)
    assert get("AlN_AN170", "sigma_flex") == pytest.approx(450e6)
    assert get("AlN_AN170", "E") == pytest.approx(320e9)
    assert get("AlN_AN170", "rho") == pytest.approx(3300.0)
    assert get("AlN_AN170", "CTE") == pytest.approx(4.6e-6)
    assert get("AlN_AN170", "HV") == pytest.approx(11e9 / 9.80665e6, rel=1e-4)  # 11 GPa


def test_stycast_values():
    assert get("Stycast_2850FT", "k_thermal") == pytest.approx(1.25)
    assert get("Stycast_2850FT", "T_g") == pytest.approx(86.0)
    assert get("Stycast_2850FT", "T_max") == pytest.approx(130.0)
    assert get("Stycast_2850FT", "CTE") == pytest.approx(35e-6)
    assert get("Stycast_2850FT", "sigma_flex") == pytest.approx(92e6)
    assert get("Stycast_2850FT", "sigma_c") == pytest.approx(155e6)
    assert get("Stycast_2850FT", "E_dielectric") == pytest.approx(14.4e6)
    assert get("Stycast_2850FT", "resistivity") == pytest.approx(1e13)


def test_tpu_values_and_gaps():
    m = get_material("tpu_elastollan_1195a")
    assert m.structural.d_ultimate_tensile_Pa == pytest.approx(55e6)
    assert m.structural.d_density_kg_m3 == pytest.approx(1150.0)
    assert m.structural.yield_stress is None  # TPU has no yield point
    assert m.structural.youngs_modulus is None  # not published for A-hardness grades
    assert m.thermal is None


def test_c93200_stores_minimums_and_converted_physicals():
    m = get_material("C93200")
    assert m.structural.d_yield_stress_Pa == pytest.approx(96.5e6)
    assert m.structural.d_ultimate_tensile_Pa == pytest.approx(207e6)
    assert m.structural.d_fatigue_endurance_Pa == pytest.approx(110e6)
    assert m.structural.d_compressive_strength_Pa == pytest.approx(317e6)
    assert m.structural.d_youngs_modulus_Pa == pytest.approx(100e9)
    assert m.electromagnetic.d_resistivity_at_20C_ohm_m == pytest.approx(1.7241e-8 / 0.12, rel=1e-3)
    assert m.thermal.d_thermal_conductivity_W_mK == pytest.approx(58.2, rel=1e-2)
    assert m.thermal.d_melting_temp_C == pytest.approx(977.0)
    for pv in (m.structural.yield_stress, m.thermal.melting_temp):
        assert pv.s_confidence == "standard"  # CDA is the association reference


def test_alnico_5_values_and_honest_gaps():
    m = get_material("alnico_5_cast")
    assert m.electromagnetic.d_remanence_T == pytest.approx(1.25)
    assert m.electromagnetic.d_energy_product_max_J_m3 == pytest.approx(43.8e3)
    assert m.electromagnetic.d_recoil_permeability == pytest.approx(3.7)
    assert m.electromagnetic.coercivity is None  # brochure gives HcB, not HcJ
    assert m.electromagnetic.temp_coeff_remanence is None  # curves only
    assert m.thermal.curie_temp is None
    assert m.structural.d_density_kg_m3 == pytest.approx(7310.0)


def test_mu_metal_values():
    m = get_material("MuMETAL")
    assert m.electromagnetic.d_saturation_flux_T == pytest.approx(0.75)
    assert m.electromagnetic.d_coercivity_A_m == pytest.approx(0.4)
    assert m.electromagnetic.d_relative_permeability == pytest.approx(400000.0)
    assert m.thermal.d_curie_temp_C == pytest.approx(420.0)
    assert m.structural.d_yield_stress_Pa == pytest.approx(280e6)
    assert m.structural.hardness_vickers is None  # published as a 130-170 range


@pytest.mark.parametrize("s_id", sorted(_NEW))
def test_every_new_value_is_tier_1(s_id):
    m = get_material(s_id)
    for group in (m.structural, m.electromagnetic, m.thermal):
        if group is None:
            continue
        for s_field in vars(group):
            pv = getattr(group, s_field)
            if pv is not None and hasattr(pv, "s_confidence"):
                assert pv.s_confidence in {"datasheet", "standard"}, (s_id, s_field)
