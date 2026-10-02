"""Tests for the Thermal group dataclass."""

from __future__ import annotations

import pytest

from emergent_matter_materials.property_value import PropertyValue as PV
from emergent_matter_materials.thermal import Thermal


def _req():
    return {
        "thermal_conductivity": PV(
            d_value=401.0, s_units="W/(m*K)", s_source="x", s_confidence="handbook"
        ),
        "specific_heat": PV(
            d_value=385.0, s_units="J/(kg*K)", s_source="x", s_confidence="handbook"
        ),
        "max_operating_temp": PV(
            d_value=200.0, s_units="C", s_source="x", s_confidence="datasheet"
        ),
    }


def test_minimum_required_construction():
    t = Thermal(**_req())
    assert t.d_thermal_conductivity_W_mK == 401.0


def test_all_optional_fields_populated():
    t = Thermal(
        **_req(),
        thermal_expansion=PV(d_value=16.5e-6, s_units="1/K", s_source="x", s_confidence="handbook"),
        glass_transition=PV(d_value=60.0, s_units="C", s_source="x", s_confidence="handbook"),
        curie_temp=PV(d_value=745.0, s_units="C", s_source="x", s_confidence="handbook"),
        melting_temp=PV(d_value=1085.0, s_units="C", s_source="x", s_confidence="handbook"),
        emissivity=PV(d_value=0.5, s_units="", s_source="x", s_confidence="handbook"),
    )
    assert t.d_thermal_expansion_per_K == pytest.approx(16.5e-6)
    assert t.d_curie_temp_C == 745.0
    assert t.d_emissivity == 0.5


def test_missing_optional_accessor_raises():
    t = Thermal(**_req())
    with pytest.raises(ValueError, match="not defined"):
        _ = t.d_glass_transition_C


def test_zero_thermal_conductivity_rejected():
    req = _req()
    req["thermal_conductivity"] = PV(
        d_value=0.0, s_units="W/(m*K)", s_source="x", s_confidence="handbook"
    )
    with pytest.raises(ValueError, match="thermal_conductivity must be positive"):
        Thermal(**req)


def test_negative_specific_heat_rejected():
    req = _req()
    req["specific_heat"] = PV(
        d_value=-1.0, s_units="J/(kg*K)", s_source="x", s_confidence="handbook"
    )
    with pytest.raises(ValueError, match="specific_heat must be positive"):
        Thermal(**req)


def test_subzero_max_op_temp_below_abs_zero_rejected():
    req = _req()
    req["max_operating_temp"] = PV(
        d_value=-300.0, s_units="C", s_source="x", s_confidence="handbook"
    )
    with pytest.raises(ValueError, match="below absolute zero"):
        Thermal(**req)


def test_emissivity_above_1_rejected():
    with pytest.raises(ValueError, match="emissivity must be in"):
        Thermal(
            **_req(),
            emissivity=PV(d_value=1.5, s_units="", s_source="x", s_confidence="handbook"),
        )


def test_emissivity_below_0_rejected():
    with pytest.raises(ValueError, match="emissivity must be in"):
        Thermal(
            **_req(),
            emissivity=PV(d_value=-0.1, s_units="", s_source="x", s_confidence="handbook"),
        )
