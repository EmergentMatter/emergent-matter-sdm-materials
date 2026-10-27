"""The exact Formlabs grade keeps manufacturer provenance and missing yield explicit."""

from __future__ import annotations

import pytest

from emergent_matter_materials import get_material, get_structural_strength


def test_formlabs_grade_uses_v2_printed_density_and_tensile_modulus() -> None:
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


def test_formlabs_grade_does_not_invent_yield_poisson_or_fatigue() -> None:
    structural = get_material("formlabs_nylon12_powder").structural
    assert structural is not None
    assert structural.yield_stress is None
    assert structural.fatigue_endurance is None
    assert structural.poisson_ratio is None
    assert structural.stress_relaxation_temp is None
    assert not structural.temperature_tables
    assert get_structural_strength("formlabs_nylon12_powder").s_basis == "ultimate_tensile"
    assert get_material("nylon12_sls").structural.density.d_value == 930.0


def test_formlabs_expansion_retains_the_reported_range_and_si_units() -> None:
    material = get_material("formlabs_nylon12_powder")
    assert material.thermal is not None
    expansion = material.thermal.thermal_expansion
    assert expansion is not None
    # A strict relative tolerance checks the micrometre/metre conversion.
    assert expansion.d_value == pytest.approx(118e-6, rel=1e-12, abs=0.0)
    assert expansion.s_units == "1/K"
    assert "-30 to 140 C" in expansion.s_condition
    assert "ASTM E 831-19" in expansion.s_source
    assert expansion.s_confidence == "datasheet"


def test_formlabs_heat_deflection_is_not_a_service_limit_or_melting_point() -> None:
    material = get_material("formlabs_nylon12_powder")
    assert material.thermal is not None
    assert material.thermal.max_operating_temp is None
    assert material.thermal.melting_temp is None
    assert not material.thermal.temperature_tables
    # Fuse machine guidance must not become an intrinsic PA12 process preset.
    assert material.manufacturing is None
