"""The exact Formlabs grade keeps manufacturer provenance and missing yield explicit."""

from __future__ import annotations

from emergent_matter_materials import get_material, get_structural_strength


def test_formlabs_grade_uses_v2_printed_density_and_tensile_modulus():
    material = get_material("formlabs_nylon12_powder")
    structural = material.structural
    assert structural is not None
    assert structural.density.d_value == 990.0
    assert structural.youngs_modulus.d_value == 1.9e9
    assert structural.ultimate_tensile.d_value == 50e6
    assert structural.flexural_strength.d_value == 66e6
    assert "2026-10-04" in structural.density.s_source
    assert "48 hours" in structural.density.s_condition
    assert "https://formlabs.com/materials/tds/nylon-12-powder/" in structural.density.s_source


def test_formlabs_grade_does_not_invent_yield_poisson_or_fatigue():
    structural = get_material("formlabs_nylon12_powder").structural
    assert structural is not None
    assert structural.yield_stress is None
    assert structural.fatigue_endurance is None
    assert structural.poisson_ratio is None
    assert get_structural_strength("formlabs_nylon12_powder").s_basis == "ultimate_tensile"
    assert get_material("nylon12_sls").structural.density.d_value == 930.0
