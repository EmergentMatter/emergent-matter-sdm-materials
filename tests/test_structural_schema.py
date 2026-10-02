"""Tests for the Structural group dataclass: cross-property invariants."""

from __future__ import annotations

import pytest

from emergent_matter_materials.property_value import PropertyValue as PV
from emergent_matter_materials.structural import Structural


def _base():
    return {
        "youngs_modulus": PV(d_value=205e9, s_units="Pa", s_source="x", s_confidence="handbook"),
        "poisson_ratio": PV(d_value=0.3, s_units="", s_source="x", s_confidence="handbook"),
        "yield_stress": PV(d_value=400e6, s_units="Pa", s_source="x", s_confidence="handbook"),
        "fatigue_endurance": PV(d_value=200e6, s_units="Pa", s_source="x", s_confidence="handbook"),
        "ultimate_tensile": PV(d_value=550e6, s_units="Pa", s_source="x", s_confidence="handbook"),
        "density": PV(d_value=8000.0, s_units="kg/m^3", s_source="x", s_confidence="handbook"),
    }


def test_happy_path():
    s = Structural(**_base())
    assert s.d_youngs_modulus_Pa == 205e9
    assert s.d_poisson_ratio == 0.3
    assert s.d_density_kg_m3 == 8000.0


def test_poisson_ratio_lower_bound_rejected():
    base = _base()
    base["poisson_ratio"] = PV(d_value=-0.1, s_units="", s_source="x", s_confidence="handbook")
    with pytest.raises(ValueError, match="poisson_ratio must be in"):
        Structural(**base)


def test_poisson_ratio_upper_bound_rejected():
    base = _base()
    base["poisson_ratio"] = PV(d_value=0.5, s_units="", s_source="x", s_confidence="handbook")
    with pytest.raises(ValueError, match="poisson_ratio must be in"):
        Structural(**base)


def test_poisson_ratio_zero_rejected():
    base = _base()
    base["poisson_ratio"] = PV(d_value=0.0, s_units="", s_source="x", s_confidence="handbook")
    with pytest.raises(ValueError, match="poisson_ratio must be in"):
        Structural(**base)


def test_negative_density_rejected():
    base = _base()
    base["density"] = PV(d_value=-1.0, s_units="kg/m^3", s_source="x", s_confidence="handbook")
    with pytest.raises(ValueError, match="density must be positive"):
        Structural(**base)


def test_yield_exceeding_uts_rejected():
    """Yield stress > UTS is physically impossible: catches data entry errors."""
    base = _base()
    base["yield_stress"] = PV(d_value=600e6, s_units="Pa", s_source="x", s_confidence="handbook")
    # yield 600 > UTS 550 → must raise
    with pytest.raises(ValueError, match="yield_stress.*>.*ultimate_tensile"):
        Structural(**base)


def test_yield_equal_to_uts_accepted():
    """For brittle materials, UTS ≈ yield: equality is allowed."""
    base = _base()
    base["yield_stress"] = PV(d_value=550e6, s_units="Pa", s_source="x", s_confidence="handbook")
    base["ultimate_tensile"] = PV(
        d_value=550e6, s_units="Pa", s_source="x", s_confidence="handbook"
    )
    s = Structural(**base)
    assert s.d_yield_stress_Pa == s.d_ultimate_tensile_Pa


def test_zero_youngs_modulus_rejected():
    base = _base()
    base["youngs_modulus"] = PV(d_value=0.0, s_units="Pa", s_source="x", s_confidence="handbook")
    with pytest.raises(ValueError, match="youngs_modulus must be positive"):
        Structural(**base)


def test_all_accessors_return_floats():
    s = Structural(**_base())
    for attr_name in (
        "d_youngs_modulus_Pa",
        "d_poisson_ratio",
        "d_yield_stress_Pa",
        "d_fatigue_endurance_Pa",
        "d_ultimate_tensile_Pa",
        "d_density_kg_m3",
    ):
        val = getattr(s, attr_name)
        assert isinstance(val, float), f"{attr_name} returned {type(val).__name__}, not float"
