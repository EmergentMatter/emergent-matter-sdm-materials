"""Schema tests for the v0.4.0 CrystalAnisotropy dataclass.

Verifies construction-time validation: required-vs-optional fields per
crystal structure, units enforcement via _PROPERTY_EXPECTED_UNITS, and
the derived-property accessors (Zener ratio, c66_derived).
"""

from __future__ import annotations

import pytest

from emergent_matter_materials import CrystalAnisotropy, PropertyValue


def _pv(d_value: float, s_units: str = "Pa") -> PropertyValue:
    """Test fixture: minimum-viable PropertyValue."""
    return PropertyValue(
        d_value=d_value,
        s_units=s_units,
        s_source="test fixture",
        s_condition="test",
        s_confidence="datasheet",
    )


# ── Crystal-structure enum ─────────────────────────────────────────────────


def test_unknown_crystal_structure_raises():
    with pytest.raises(ValueError, match="Unknown crystal structure"):
        CrystalAnisotropy(
            s_crystal_structure="orthorhombic",  # not yet in v0.4.0 enum
            c11=_pv(200e9),
            c12=_pv(100e9),
            c44=_pv(50e9),
        )


def test_empty_string_crystal_structure_raises():
    with pytest.raises(ValueError, match="Unknown crystal structure"):
        CrystalAnisotropy(
            s_crystal_structure="",
            c11=_pv(200e9),
            c12=_pv(100e9),
            c44=_pv(50e9),
        )


# ── Cubic (FCC / BCC): only C11/C12/C44 independent ────────────────────────


def test_fcc_accepts_minimal_cubic_constants():
    ca = CrystalAnisotropy(
        s_crystal_structure="FCC",
        c11=_pv(168.4e9),
        c12=_pv(121.4e9),
        c44=_pv(75.4e9),
    )
    assert ca.d_c11_Pa == 168.4e9
    assert ca.d_c12_Pa == 121.4e9
    assert ca.d_c44_Pa == 75.4e9


def test_bcc_accepts_minimal_cubic_constants():
    ca = CrystalAnisotropy(
        s_crystal_structure="BCC",
        c11=_pv(231.4e9),
        c12=_pv(134.7e9),
        c44=_pv(116.4e9),
    )
    assert ca.d_c11_Pa == 231.4e9


def test_fcc_rejects_c13():
    with pytest.raises(ValueError, match="c13 must be None"):
        CrystalAnisotropy(
            s_crystal_structure="FCC",
            c11=_pv(200e9),
            c12=_pv(100e9),
            c44=_pv(50e9),
            c13=_pv(100e9),  # bogus for cubic
        )


def test_bcc_rejects_c33():
    with pytest.raises(ValueError, match="c33 must be None"):
        CrystalAnisotropy(
            s_crystal_structure="BCC",
            c11=_pv(200e9),
            c12=_pv(100e9),
            c44=_pv(50e9),
            c33=_pv(200e9),
        )


def test_fcc_rejects_c66():
    with pytest.raises(ValueError, match="c66 must be None"):
        CrystalAnisotropy(
            s_crystal_structure="FCC",
            c11=_pv(200e9),
            c12=_pv(100e9),
            c44=_pv(50e9),
            c66=_pv(50e9),  # cubic c66=c44 derived, not stored
        )


# ── HCP: 5 independent (C11, C12, C13, C33, C44); reject C66 ───────────────


def test_hcp_requires_c13():
    with pytest.raises(ValueError, match="c13 is required"):
        CrystalAnisotropy(
            s_crystal_structure="HCP",
            c11=_pv(162.4e9),
            c12=_pv(92e9),
            c44=_pv(46.7e9),
            # c13 missing
            c33=_pv(180.7e9),
        )


def test_hcp_requires_c33():
    with pytest.raises(ValueError, match="c33 is required"):
        CrystalAnisotropy(
            s_crystal_structure="HCP",
            c11=_pv(162.4e9),
            c12=_pv(92e9),
            c44=_pv(46.7e9),
            c13=_pv(69e9),
            # c33 missing
        )


def test_hcp_rejects_c66():
    with pytest.raises(ValueError, match="c66 must be None"):
        CrystalAnisotropy(
            s_crystal_structure="HCP",
            c11=_pv(162.4e9),
            c12=_pv(92e9),
            c44=_pv(46.7e9),
            c13=_pv(69e9),
            c33=_pv(180.7e9),
            c66=_pv(35e9),  # HCP c66 = (c11-c12)/2, derived not stored
        )


def test_hcp_accepts_five_constants():
    ca = CrystalAnisotropy(
        s_crystal_structure="HCP",
        c11=_pv(162.4e9),
        c12=_pv(92e9),
        c44=_pv(46.7e9),
        c13=_pv(69e9),
        c33=_pv(180.7e9),
    )
    assert ca.d_c33_Pa == 180.7e9
    # Derived c66 = (c11 - c12) / 2
    assert ca.d_c66_derived_Pa == 0.5 * (162.4e9 - 92e9)


# ── Tetragonal / rhombohedral: 6 independent ───────────────────────────────


def test_tetragonal_requires_all_six():
    with pytest.raises(ValueError, match="c66 is required"):
        CrystalAnisotropy(
            s_crystal_structure="tetragonal",
            c11=_pv(250e9),
            c12=_pv(130e9),
            c44=_pv(110e9),
            c13=_pv(110e9),
            c33=_pv(200e9),
            # c66 missing
        )


def test_rhombohedral_accepts_six_constants():
    ca = CrystalAnisotropy(
        s_crystal_structure="rhombohedral",
        c11=_pv(330e9),
        c12=_pv(120e9),
        c44=_pv(95e9),
        c13=_pv(110e9),
        c33=_pv(395e9),
        c66=_pv(105e9),
    )
    assert ca.d_c66_Pa == 105e9


# ── Units enforcement ──────────────────────────────────────────────────────


def test_wrong_units_on_c11_raises():
    with pytest.raises(ValueError, match="wrong units"):
        CrystalAnisotropy(
            s_crystal_structure="FCC",
            c11=_pv(168.4, s_units="GPa"),  # WRONG: must be Pa
            c12=_pv(121.4e9),
            c44=_pv(75.4e9),
        )


def test_wrong_units_on_burgers_vector_raises():
    with pytest.raises(ValueError, match="wrong units"):
        CrystalAnisotropy(
            s_crystal_structure="FCC",
            c11=_pv(168.4e9),
            c12=_pv(121.4e9),
            c44=_pv(75.4e9),
            burgers_vector=_pv(0.2556, s_units="nm"),  # WRONG: must be m
        )


def test_wrong_units_on_stacking_fault_energy_raises():
    with pytest.raises(ValueError, match="wrong units"):
        CrystalAnisotropy(
            s_crystal_structure="FCC",
            c11=_pv(168.4e9),
            c12=_pv(121.4e9),
            c44=_pv(75.4e9),
            stacking_fault_energy=_pv(78, s_units="mJ/m^2"),  # WRONG: J/m^2
        )


# ── Positivity validation ──────────────────────────────────────────────────


def test_negative_c11_raises():
    with pytest.raises(ValueError, match="must be positive"):
        CrystalAnisotropy(
            s_crystal_structure="FCC",
            c11=_pv(-1.0),
            c12=_pv(100e9),
            c44=_pv(50e9),
        )


def test_zero_burgers_vector_raises():
    with pytest.raises(ValueError, match="must be positive"):
        CrystalAnisotropy(
            s_crystal_structure="FCC",
            c11=_pv(200e9),
            c12=_pv(100e9),
            c44=_pv(50e9),
            burgers_vector=_pv(0.0, s_units="m"),
        )


# ── Zener anisotropy derived property ──────────────────────────────────────


def test_cu_zener_anisotropy_matches_expected():
    """Cu Zener should be ~3.21 (close to canonical 3.2 from Overton-Gaffney)."""
    ca = CrystalAnisotropy(
        s_crystal_structure="FCC",
        c11=_pv(168.4e9),
        c12=_pv(121.4e9),
        c44=_pv(75.4e9),
    )
    A = ca.d_zener_anisotropy
    assert 3.15 < A < 3.25, f"Cu Zener should be ~3.21, got {A}"


def test_iron_zener_anisotropy_matches_expected():
    """alpha-Fe Zener should be ~2.41 from Rayne-Chandrasekhar."""
    ca = CrystalAnisotropy(
        s_crystal_structure="BCC",
        c11=_pv(231.4e9),
        c12=_pv(134.7e9),
        c44=_pv(116.4e9),
    )
    A = ca.d_zener_anisotropy
    assert 2.35 < A < 2.50, f"alpha-Fe Zener should be ~2.41, got {A}"


def test_zener_raises_for_hcp():
    """Zener anisotropy is cubic-only; HCP needs different anisotropy measures."""
    ca = CrystalAnisotropy(
        s_crystal_structure="HCP",
        c11=_pv(162.4e9),
        c12=_pv(92e9),
        c44=_pv(46.7e9),
        c13=_pv(69e9),
        c33=_pv(180.7e9),
    )
    with pytest.raises(ValueError, match="only for cubic"):
        _ = ca.d_zener_anisotropy


def test_zener_raises_when_c11_equals_c12():
    """Pathological case (isotropic limit): would divide by zero."""
    ca = CrystalAnisotropy(
        s_crystal_structure="FCC",
        c11=_pv(150e9),
        c12=_pv(150e9),
        c44=_pv(75e9),  # degenerate
    )
    with pytest.raises(ValueError, match="divide by zero"):
        _ = ca.d_zener_anisotropy


# ── d_c66_derived_Pa for HCP + cubic ───────────────────────────────────────


def test_c66_derived_for_cubic_equals_c44():
    ca = CrystalAnisotropy(
        s_crystal_structure="FCC",
        c11=_pv(168.4e9),
        c12=_pv(121.4e9),
        c44=_pv(75.4e9),
    )
    assert ca.d_c66_derived_Pa == 75.4e9


def test_c66_derived_for_hcp_formula():
    ca = CrystalAnisotropy(
        s_crystal_structure="HCP",
        c11=_pv(162.4e9),
        c12=_pv(92e9),
        c44=_pv(46.7e9),
        c13=_pv(69e9),
        c33=_pv(180.7e9),
    )
    expected = 0.5 * (162.4e9 - 92e9)
    assert ca.d_c66_derived_Pa == expected


# ── Float accessors raise on missing optional fields ──────────────────────


def test_burgers_vector_accessor_raises_when_none():
    ca = CrystalAnisotropy(
        s_crystal_structure="FCC",
        c11=_pv(168.4e9),
        c12=_pv(121.4e9),
        c44=_pv(75.4e9),
    )
    with pytest.raises(ValueError, match="burgers_vector not defined"):
        _ = ca.d_burgers_vector_m


def test_sfe_accessor_raises_when_none():
    ca = CrystalAnisotropy(
        s_crystal_structure="BCC",
        c11=_pv(231.4e9),
        c12=_pv(134.7e9),
        c44=_pv(116.4e9),
    )
    with pytest.raises(ValueError, match="stacking_fault_energy"):
        _ = ca.d_stacking_fault_energy_J_m2


def test_crss_accessor_raises_when_none():
    ca = CrystalAnisotropy(
        s_crystal_structure="FCC",
        c11=_pv(168.4e9),
        c12=_pv(121.4e9),
        c44=_pv(75.4e9),
    )
    with pytest.raises(ValueError, match="crss_initial"):
        _ = ca.d_crss_initial_Pa


# ── Required-trio enforcement ──────────────────────────────────────────────


def test_missing_c11_raises_on_construction():
    with pytest.raises(TypeError):  # dataclass missing required positional/keyword
        CrystalAnisotropy(
            s_crystal_structure="FCC",
            c12=_pv(121.4e9),
            c44=_pv(75.4e9),
        )
