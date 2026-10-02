"""Tests for the consumer-safe structural design-strength resolver (v1.10.0).

A structural consumer (e.g. a design tool) needs a single usable
strength allowable + its basis WITHOUT implementing its own yield->ultimate
fallback or pretending UTS is yield. These tests pin that behavior:
yield_stress first, then ultimate_tensile (optionally derated), else fail loud.
"""

from __future__ import annotations

import dataclasses

import pytest

from emergent_matter_materials import (
    StructuralStrength,
    StructuralStrengthUnavailable,
    get_material,
    get_structural_strength,
    list_materials,
    material_summary,
)
from emergent_matter_materials.property_value import PropertyValue
from emergent_matter_materials.structural import (
    STRENGTH_BASIS_DERATED_ULTIMATE,
    STRENGTH_BASIS_ULTIMATE,
    STRENGTH_BASIS_UNKNOWN,
    STRENGTH_BASIS_YIELD,
    Structural,
)

_KNOWN_BASES = {
    STRENGTH_BASIS_YIELD,
    STRENGTH_BASIS_ULTIMATE,
    STRENGTH_BASIS_DERATED_ULTIMATE,
    STRENGTH_BASIS_UNKNOWN,
}


# ── nylon12_sls: usable strength via ultimate_tensile, NOT a faked yield ──────


def test_nylon_has_usable_strength_via_ultimate():
    r = get_structural_strength("nylon12_sls")
    assert r.d_value_Pa == 50e6
    assert r.s_basis == STRENGTH_BASIS_ULTIMATE
    assert r.s_basis != STRENGTH_BASIS_YIELD
    assert r.s_units == "Pa"
    assert "Formlabs" in r.s_source


def test_nylon_yield_still_absent():
    # The resolver must not have caused a faked yield to appear.
    assert get_material("nylon12_sls").structural.yield_stress is None


def test_nylon_bare_accessor_and_probe():
    s = get_material("nylon12_sls").structural
    assert s.d_design_strength_Pa == 50e6
    assert s.s_strength_basis == STRENGTH_BASIS_ULTIMATE


# ── materials with a true yield use yield first ──────────────────────────────


def test_yield_material_prefers_yield():
    s = get_material("steel_4140").structural
    assert s.yield_stress is not None and s.ultimate_tensile is not None  # precondition
    r = s.resolve_design_strength()
    assert r.s_basis == STRENGTH_BASIS_YIELD
    assert r.d_value_Pa == s.d_yield_stress_Pa
    # the resolver picked the lower (correct design) quantity
    assert r.d_value_Pa < s.d_ultimate_tensile_Pa


# ── fail loud when neither yield nor ultimate exists ─────────────────────────


def _density_only_structural() -> Structural:
    return Structural(
        density=PropertyValue(
            d_value=1000.0,
            s_units="kg/m^3",
            s_source="synthetic test fixture",
            s_confidence="datasheet",
        )
    )


def test_no_strength_basis_raises():
    s = _density_only_structural()
    assert s.s_strength_basis == STRENGTH_BASIS_UNKNOWN
    with pytest.raises(StructuralStrengthUnavailable):
        s.resolve_design_strength()
    with pytest.raises(StructuralStrengthUnavailable):
        _ = s.d_design_strength_Pa


def test_unavailable_is_valueerror_subclass():
    # Existing `except ValueError` handlers must keep catching it.
    assert issubclass(StructuralStrengthUnavailable, ValueError)


def test_no_structural_group_raises():
    no_struct = dataclasses.replace(get_material("nylon12_sls"), structural=None)
    with pytest.raises(StructuralStrengthUnavailable):
        get_structural_strength(no_struct)


# ── optional caller-owned derate ─────────────────────────────────────────────


def test_ultimate_derate_applied():
    r = get_structural_strength("nylon12_sls", ultimate_derate=0.6)
    assert r.s_basis == STRENGTH_BASIS_DERATED_ULTIMATE
    assert r.d_value_Pa == pytest.approx(50e6 * 0.6)
    assert r.d_derate_factor == 0.6


def test_derate_ignored_when_yield_present():
    r = get_structural_strength("steel_4140", ultimate_derate=0.5)
    assert r.s_basis == STRENGTH_BASIS_YIELD  # yield wins; derate not applied
    assert r.d_derate_factor is None
    assert r.d_value_Pa == get_material("steel_4140").structural.d_yield_stress_Pa


@pytest.mark.parametrize("bad", [0.0, -0.1, 1.5, 2.0])
def test_invalid_derate_rejected(bad):
    s = get_material("nylon12_sls").structural
    with pytest.raises(ValueError):
        s.resolve_design_strength(ultimate_derate=bad)


# ── top-level helper ergonomics ──────────────────────────────────────────────


def test_helper_accepts_alias_and_object():
    by_alias = get_structural_strength("PA12_SLS")
    by_obj = get_structural_strength(get_material("nylon12_sls"))
    assert by_alias == by_obj
    assert isinstance(by_alias, StructuralStrength)


def test_helper_unknown_material_raises_keyerror():
    with pytest.raises(KeyError):
        get_structural_strength("not_a_real_material")


# ── whole-catalog consistency ────────────────────────────────────────────────


def test_basis_consistent_across_catalog():
    for s_id in list_materials():
        s = get_material(s_id).structural
        if s is None:
            continue
        basis = s.s_strength_basis
        assert basis in _KNOWN_BASES
        if basis == STRENGTH_BASIS_UNKNOWN:
            with pytest.raises(StructuralStrengthUnavailable):
                s.resolve_design_strength()
        else:
            r = s.resolve_design_strength()
            assert r.d_value_Pa > 0.0
            assert r.s_basis == basis


# ── regression: material_summary no longer crashes on no-yield materials ─────


def test_material_summary_handles_no_yield():
    out = material_summary("nylon12_sls")  # previously raised on d_yield_stress_Pa
    assert "basis:" in out
    assert "ultimate_tensile" in out
