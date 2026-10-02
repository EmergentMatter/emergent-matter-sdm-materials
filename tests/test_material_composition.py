"""Tests for the Material composite dataclass."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from emergent_matter_materials.material import _VALID_CATEGORIES, Material
from emergent_matter_materials.property_value import PropertyValue as PV
from emergent_matter_materials.structural import Structural


def _ok_structural():
    return Structural(
        youngs_modulus=PV(d_value=205e9, s_units="Pa", s_source="x", s_confidence="handbook"),
        poisson_ratio=PV(d_value=0.3, s_units="", s_source="x", s_confidence="handbook"),
        yield_stress=PV(d_value=400e6, s_units="Pa", s_source="x", s_confidence="handbook"),
        fatigue_endurance=PV(d_value=200e6, s_units="Pa", s_source="x", s_confidence="handbook"),
        ultimate_tensile=PV(d_value=550e6, s_units="Pa", s_source="x", s_confidence="handbook"),
        density=PV(d_value=8000.0, s_units="kg/m^3", s_source="x", s_confidence="handbook"),
    )


def _ok_material(**kwargs):
    base = {
        "s_id": "test_steel",
        "s_description": "Test steel",
        "s_category": "metal",
        "s_specification": "TEST 1234",
        "s_catalog_version": "0.1.0",
        "s_last_reviewed": "2026-05-24",
        "structural": _ok_structural(),
    }
    base.update(kwargs)
    return Material(**base)


def test_minimum_valid_construction():
    m = _ok_material()
    assert m.s_id == "test_steel"
    assert m.s_category == "metal"


def test_empty_s_id_rejected():
    with pytest.raises(ValueError, match="s_id cannot be empty"):
        _ok_material(s_id="")


def test_uppercase_s_id_rejected():
    with pytest.raises(ValueError, match="snake_case lowercase"):
        _ok_material(s_id="TestSteel")


def test_s_id_with_space_rejected():
    with pytest.raises(ValueError, match="must not contain spaces"):
        _ok_material(s_id="test steel")


def test_empty_description_rejected():
    with pytest.raises(ValueError, match="s_description cannot be empty"):
        _ok_material(s_description="")


def test_invalid_category_rejected():
    with pytest.raises(ValueError, match="s_category must be one of"):
        _ok_material(s_category="liquid")  # type: ignore[arg-type]


def test_all_valid_categories_accepted():
    for cat in _VALID_CATEGORIES:
        m = _ok_material(s_category=cat)
        assert m.s_category == cat


def test_empty_catalog_version_rejected():
    with pytest.raises(ValueError, match="s_catalog_version cannot be empty"):
        _ok_material(s_catalog_version="")


def test_bad_iso_date_rejected():
    with pytest.raises(ValueError, match="ISO 8601 YYYY-MM-DD"):
        _ok_material(s_last_reviewed="May 24, 2026")


def test_iso_date_required_format():
    # too short
    with pytest.raises(ValueError, match="ISO 8601"):
        _ok_material(s_last_reviewed="2026-5-24")


def test_no_physics_groups_rejected():
    """A material with no physics groups is catalog noise."""
    with pytest.raises(ValueError, match="no physics groups populated"):
        _ok_material(structural=None)


def test_specification_can_be_empty():
    """For informal materials (custom composites), s_specification can be ''."""
    m = _ok_material(s_specification="")
    assert m.s_specification == ""


def test_material_is_frozen():
    m = _ok_material()
    with pytest.raises(FrozenInstanceError):
        m.s_id = "renamed"  # type: ignore[misc]
