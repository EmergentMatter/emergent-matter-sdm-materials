"""Tests for the first sourcing-backlog batch: four new Tier-1 materials.

Covers 17-4 PH, MnZn ferrite, Kapton HN and PETG.
Every value below was read from the vendor document named in the entry's
``s_source`` on 2026-09-17.
"""

from __future__ import annotations

import pytest

from emergent_matter_materials import get, get_material, get_with_metadata

_NEW = {
    "petg_3dprint": "polymer",
    "kapton_hn": "polymer",
    "stainless_17_4ph_h900": "metal",
    "mnzn_ferrite_3c95": "soft_magnetic",
}


@pytest.mark.parametrize(("s_id", "s_category"), sorted(_NEW.items()))
def test_present_with_category_and_specification(s_id, s_category):
    m = get_material(s_id)
    assert m.s_category == s_category
    assert m.s_specification.strip()


@pytest.mark.parametrize(
    ("s_alias", "s_id"),
    [
        ("PETG", "petg_3dprint"),
        ("Prusament_PETG", "petg_3dprint"),
        ("Kapton_HN", "kapton_hn"),
        ("SS17_4PH_H900", "stainless_17_4ph_h900"),
        ("17_4PH_H900", "stainless_17_4ph_h900"),
        ("3C95", "mnzn_ferrite_3c95"),
        ("MnZn_3C95", "mnzn_ferrite_3c95"),
    ],
)
def test_aliases_resolve(s_alias, s_id):
    assert get_material(s_alias).s_id == s_id


def test_petg_values_are_the_horizontal_print_direction():
    assert get("PETG", "E") == pytest.approx(1.5e9)
    assert get("PETG", "sigma_y") == pytest.approx(47e6)
    assert get("PETG", "sigma_flex") == pytest.approx(66e6)
    assert get("PETG", "rho") == pytest.approx(1270.0)
    assert get("PETG", "T_max") == pytest.approx(68.0)
    assert get_material("PETG").structural.ultimate_tensile is None  # not on the TDS


def test_kapton_hn_values_are_the_25um_column():
    assert get("Kapton_HN", "UTS") == pytest.approx(231e6)
    assert get("Kapton_HN", "E") == pytest.approx(2.76e9)
    assert get("Kapton_HN", "nu") == pytest.approx(0.34)
    assert get("Kapton_HN", "E_dielectric") == pytest.approx(303e6)
    assert get("Kapton_HN", "epsilon_r") == pytest.approx(3.4)
    assert get("Kapton_HN", "resistivity") == pytest.approx(1.5e15)
    assert get("Kapton_HN", "k_thermal") == pytest.approx(0.20)
    assert get("Kapton_HN", "c_p") == pytest.approx(1090.0)
    assert get("Kapton_HN", "CTE") == pytest.approx(20e-6)
    m = get_material("kapton_hn")
    assert m.thermal.glass_transition is None  # sheet gives a 360-410 C range only
    assert m.thermal.melting_temp is None  # sheet: 'Melting Point: None'


def test_17_4ph_h900_stores_specification_minimums():
    m = get_material("stainless_17_4ph_h900")
    assert m.structural.d_yield_stress_Pa == pytest.approx(1172e6)
    assert m.structural.d_ultimate_tensile_Pa == pytest.approx(1310e6)
    assert m.structural.d_youngs_modulus_Pa == pytest.approx(197e9)
    assert m.structural.d_poisson_ratio == pytest.approx(0.272)
    assert m.structural.d_density_kg_m3 == pytest.approx(7800.0)
    assert m.electromagnetic.d_resistivity_at_20C_ohm_m == pytest.approx(7.7e-7)
    assert m.thermal.d_specific_heat_J_kgK == pytest.approx(460.0)
    assert m.thermal.d_thermal_expansion_per_K == pytest.approx(10.8e-6)
    assert "149 C" in get_with_metadata("17_4PH_H900", "k_thermal").s_condition
    assert m.structural.hardness_vickers is None  # bulletin gives Rockwell C only


def test_3c95_ferrite_values():
    m = get_material("3C95")
    assert m.electromagnetic.d_relative_permeability == pytest.approx(3000.0)
    assert m.electromagnetic.d_saturation_flux_T == pytest.approx(0.53)
    assert m.electromagnetic.d_resistivity_at_20C_ohm_m == pytest.approx(5.0)
    assert m.thermal.d_curie_temp_C == pytest.approx(215.0)
    assert m.structural.d_density_kg_m3 == pytest.approx(4800.0)
    assert m.electromagnetic.core_loss is None  # published per volume only; no derivation
    assert m.crystal_anisotropy is None


@pytest.mark.parametrize("s_id", sorted(_NEW))
def test_every_new_value_is_datasheet_confidence(s_id):
    m = get_material(s_id)
    for group in (m.structural, m.electromagnetic, m.thermal):
        if group is None:
            continue
        for s_field in vars(group):
            pv = getattr(group, s_field)
            if pv is not None and hasattr(pv, "s_confidence"):
                assert pv.s_confidence == "datasheet", (s_id, s_field)
