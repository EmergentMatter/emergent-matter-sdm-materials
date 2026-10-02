"""Tests for the per-property units-map enforcement.

The contract: every PropertyValue's s_units MUST match
_PROPERTY_EXPECTED_UNITS for the field slot it occupies on its group
dataclass. Mismatch raises ValueError at construction time.
"""

from __future__ import annotations

import pytest

from emergent_matter_materials.electromagnetic import Electromagnetic
from emergent_matter_materials.property_value import PropertyValue as PV
from emergent_matter_materials.structural import Structural
from emergent_matter_materials.thermal import Thermal
from emergent_matter_materials.units_map import (
    _PROPERTY_EXPECTED_UNITS,
    expected_units_for,
)


def _ok_structural():
    """Build a structurally-valid Structural for substitution-attack tests."""
    return {
        "youngs_modulus": PV(d_value=205e9, s_units="Pa", s_source="x", s_confidence="handbook"),
        "poisson_ratio": PV(d_value=0.3, s_units="", s_source="x", s_confidence="handbook"),
        "yield_stress": PV(d_value=400e6, s_units="Pa", s_source="x", s_confidence="handbook"),
        "fatigue_endurance": PV(d_value=200e6, s_units="Pa", s_source="x", s_confidence="handbook"),
        "ultimate_tensile": PV(d_value=550e6, s_units="Pa", s_source="x", s_confidence="handbook"),
        "density": PV(d_value=8000.0, s_units="kg/m^3", s_source="x", s_confidence="handbook"),
    }


# ── _PROPERTY_EXPECTED_UNITS sanity ────────────────────────────────────────


def test_expected_units_for_known_property():
    assert expected_units_for("youngs_modulus") == "Pa"
    assert expected_units_for("density") == "kg/m^3"
    assert expected_units_for("saturation_flux") == "T"
    assert expected_units_for("thermal_conductivity") == "W/(m*K)"
    assert expected_units_for("poisson_ratio") == ""  # dimensionless


def test_expected_units_for_unknown_property_raises():
    with pytest.raises(KeyError, match="No expected-units entry"):
        expected_units_for("not_a_real_property")


def test_property_units_table_has_expected_entry_count():
    # Sanity gate: 9 structural + 13 EM + 9 thermal + 6 mfg + 9 crystal = 46
    # v0.3.0 added flexural_strength to Structural for brittle materials.
    # v0.4.0 added 9 entries for CrystalAnisotropy (c11/c12/c13/c33/c44/c66,
    # burgers_vector, stacking_fault_energy, crss_initial).
    # v1.1.0 added recoil_permeability to Electromagnetic (μ_rec for PMs).
    # v1.8.0 added temp_coeff_coercivity to Electromagnetic (α(HcJ) for PMs).
    # The magnet schema expansion added hardness_vickers + compressive_strength (Structural),
    # thermal_expansion_perpendicular (Thermal), energy_product_max (EM).
    assert len(_PROPERTY_EXPECTED_UNITS) == 46


# ── Structural units enforcement ───────────────────────────────────────────


def test_structural_accepts_correct_units():
    s = Structural(**_ok_structural())
    assert s.d_youngs_modulus_Pa == 205e9


def test_structural_rejects_MPa_in_Pa_slot():
    base = _ok_structural()
    base["youngs_modulus"] = PV(
        d_value=205e9,
        s_units="MPa",  # WRONG
        s_source="x",
        s_confidence="handbook",
    )
    with pytest.raises(ValueError, match="wrong units.*Expected 'Pa', got 'MPa'"):
        Structural(**base)


def test_structural_rejects_g_cc_in_density_slot():
    base = _ok_structural()
    base["density"] = PV(
        d_value=8.96,
        s_units="g/cc",  # WRONG
        s_source="x",
        s_confidence="handbook",
    )
    with pytest.raises(ValueError, match="wrong units.*Expected 'kg/m\\^3', got 'g/cc'"):
        Structural(**base)


def test_structural_rejects_blank_units_on_poisson_replacement():
    base = _ok_structural()
    base["poisson_ratio"] = PV(
        d_value=0.3,
        s_units="dimensionless",  # WRONG - should be ""
        s_source="x",
        s_confidence="handbook",
    )
    with pytest.raises(ValueError, match="wrong units"):
        Structural(**base)


# ── Electromagnetic units enforcement (optional fields)  ───────────────────


def test_electromagnetic_empty_construct_ok():
    # All fields optional: empty construction is valid
    em = Electromagnetic()
    assert em.resistivity_at_20C is None


def test_electromagnetic_accepts_correct_units():
    em = Electromagnetic(
        resistivity_at_20C=PV(
            d_value=1.68e-8, s_units="Ohm*m", s_source="x", s_confidence="handbook"
        ),
        saturation_flux=PV(d_value=2.03, s_units="T", s_source="x", s_confidence="datasheet"),
    )
    assert em.d_resistivity_at_20C_ohm_m == 1.68e-8
    assert em.d_saturation_flux_T == 2.03


def test_electromagnetic_rejects_wrong_units_on_resistivity():
    with pytest.raises(ValueError, match="wrong units.*Expected 'Ohm\\*m'"):
        Electromagnetic(
            resistivity_at_20C=PV(
                d_value=1.68e-8,
                s_units="ohm-meter",  # WRONG (space, dash)
                s_source="x",
                s_confidence="handbook",
            ),
        )


def test_electromagnetic_rejects_gauss_for_saturation_flux():
    with pytest.raises(ValueError, match="wrong units.*Expected 'T'"):
        Electromagnetic(
            saturation_flux=PV(
                d_value=20300.0,
                s_units="G",  # WRONG (Gauss not Tesla)
                s_source="x",
                s_confidence="handbook",
            ),
        )


# ── Thermal units enforcement ──────────────────────────────────────────────


def test_thermal_minimum_required_fields():
    t = Thermal(
        thermal_conductivity=PV(
            d_value=401.0, s_units="W/(m*K)", s_source="x", s_confidence="handbook"
        ),
        specific_heat=PV(d_value=385.0, s_units="J/(kg*K)", s_source="x", s_confidence="handbook"),
        max_operating_temp=PV(d_value=200.0, s_units="C", s_source="x", s_confidence="datasheet"),
    )
    assert t.d_thermal_conductivity_W_mK == 401.0


def test_thermal_rejects_K_for_max_op_temp():
    # max_operating_temp is conventionally in Celsius (datasheet convention)
    with pytest.raises(ValueError, match="wrong units.*Expected 'C'"):
        Thermal(
            thermal_conductivity=PV(
                d_value=401.0, s_units="W/(m*K)", s_source="x", s_confidence="handbook"
            ),
            specific_heat=PV(
                d_value=385.0, s_units="J/(kg*K)", s_source="x", s_confidence="handbook"
            ),
            max_operating_temp=PV(
                d_value=473.0,
                s_units="K",  # WRONG
                s_source="x",
                s_confidence="handbook",
            ),
        )


def test_thermal_all_fields_optional():
    """v0.2.0: every Thermal field is optional. None on previously-required
    fields is now legal (was raising ValueError in v0.1.x)."""
    t = Thermal(
        thermal_conductivity=None,
        specific_heat=PV(d_value=385.0, s_units="J/(kg*K)", s_source="x", s_confidence="datasheet"),
        max_operating_temp=PV(d_value=200.0, s_units="C", s_source="x", s_confidence="datasheet"),
    )
    # The None field raises only when the hot-path accessor tries to read it
    with pytest.raises(ValueError, match="not defined"):
        _ = t.d_thermal_conductivity_W_mK
    # The populated fields work
    assert t.d_specific_heat_J_kgK == 385.0
