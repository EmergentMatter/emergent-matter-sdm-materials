"""Tests for the Electromagnetic group dataclass."""

from __future__ import annotations

import pytest

from emergent_matter_materials.electromagnetic import Electromagnetic
from emergent_matter_materials.property_value import PropertyValue as PV


def test_empty_construction_ok():
    """All fields optional; empty Electromagnetic is valid (used for
    materials with no EM characterization)."""
    em = Electromagnetic()
    assert em.resistivity_at_20C is None
    assert em.saturation_flux is None


def test_conductor_partial_construction():
    em = Electromagnetic(
        resistivity_at_20C=PV(
            d_value=1.68e-8, s_units="Ohm*m", s_source="x", s_confidence="handbook"
        ),
        temp_coeff_resistivity=PV(
            d_value=3.93e-3, s_units="1/K", s_source="x", s_confidence="handbook"
        ),
    )
    assert em.d_resistivity_at_20C_ohm_m == 1.68e-8


def test_missing_field_accessor_raises():
    em = Electromagnetic()
    with pytest.raises(ValueError, match="not defined for this material"):
        _ = em.d_saturation_flux_T


def test_resistivity_at_T_with_required_fields():
    em = Electromagnetic(
        resistivity_at_20C=PV(
            d_value=1.68e-8, s_units="Ohm*m", s_source="x", s_confidence="handbook"
        ),
        temp_coeff_resistivity=PV(
            d_value=3.93e-3, s_units="1/K", s_source="x", s_confidence="handbook"
        ),
    )
    rho_20 = em.d_resistivity_at_T(20.0)
    rho_100 = em.d_resistivity_at_T(100.0)
    assert rho_20 == pytest.approx(1.68e-8)
    # at 100 C: rho_20 * (1 + 0.00393 * 80) = 1.68e-8 * 1.3144 ≈ 2.208e-8
    assert rho_100 == pytest.approx(1.68e-8 * (1.0 + 3.93e-3 * 80.0))


def test_resistivity_at_T_without_fields_raises():
    em = Electromagnetic()  # no resistivity fields
    with pytest.raises(ValueError, match="not defined"):
        em.d_resistivity_at_T(50.0)


def test_resistivity_jax_traceable():
    """The operating-point callable must work with jnp arrays."""
    pytest.importorskip("jax")
    import jax.numpy as jnp

    em = Electromagnetic(
        resistivity_at_20C=PV(
            d_value=1.68e-8, s_units="Ohm*m", s_source="x", s_confidence="handbook"
        ),
        temp_coeff_resistivity=PV(
            d_value=3.93e-3, s_units="1/K", s_source="x", s_confidence="handbook"
        ),
    )
    T = jnp.array([20.0, 50.0, 100.0, 150.0])
    rho_T = em.d_resistivity_at_T(T)
    assert rho_T.shape == (4,)
    # First value should match the room-temperature anchor
    assert float(rho_T[0]) == pytest.approx(1.68e-8, rel=1e-6)
    # Values should be monotonically increasing in T
    assert all(float(rho_T[i + 1]) > float(rho_T[i]) for i in range(3))


def test_resistivity_jax_grad():
    """Backprop through resistivity_at_T(T) must work."""
    pytest.importorskip("jax")
    import jax

    em = Electromagnetic(
        resistivity_at_20C=PV(
            d_value=1.68e-8, s_units="Ohm*m", s_source="x", s_confidence="handbook"
        ),
        temp_coeff_resistivity=PV(
            d_value=3.93e-3, s_units="1/K", s_source="x", s_confidence="handbook"
        ),
    )
    drho_dT = jax.grad(em.d_resistivity_at_T)(50.0)
    # d(rho)/dT = rho_20 * alpha = 1.68e-8 * 3.93e-3 ≈ 6.6e-11
    assert float(drho_dT) == pytest.approx(1.68e-8 * 3.93e-3, rel=1e-6)


def test_relative_permeability_diamagnetic_accepted():
    """v0.7.0 relaxed the μ_r ≥ 1.0 rule to μ_r > 0.0: diamagnetic
    materials are real engineering physics (Cu winding susceptibility
    matters for MRI shimming + low-noise solenoid design). CRC Handbook
    95th ed. Section 12 publishes Tier-1 diamagnetic susceptibilities."""
    # Cu's published value: must NOT raise
    em = Electromagnetic(
        relative_permeability=PV(
            d_value=0.999994,
            s_units="",
            s_source="CRC Handbook 95th ed.",
            s_confidence="standard",
        ),
    )
    assert em.relative_permeability.d_value == 0.999994


def test_relative_permeability_zero_or_negative_rejected():
    """μ_r ≤ 0 is unphysical and still rejected even after v0.7.0's
    diamagnetic relaxation."""
    with pytest.raises(ValueError, match="relative_permeability must be > 0"):
        Electromagnetic(
            relative_permeability=PV(
                d_value=0.0, s_units="", s_source="x", s_confidence="handbook"
            ),
        )
    with pytest.raises(ValueError, match="relative_permeability must be > 0"):
        Electromagnetic(
            relative_permeability=PV(
                d_value=-0.5, s_units="", s_source="x", s_confidence="handbook"
            ),
        )


def test_relative_permittivity_below_1_rejected():
    with pytest.raises(ValueError, match="relative_permittivity must be >= 1.0"):
        Electromagnetic(
            relative_permittivity=PV(
                d_value=0.5, s_units="", s_source="x", s_confidence="handbook"
            ),
        )


def test_negative_saturation_flux_rejected():
    with pytest.raises(ValueError, match="saturation_flux must be positive"):
        Electromagnetic(
            saturation_flux=PV(d_value=-1.0, s_units="T", s_source="x", s_confidence="handbook"),
        )


def test_negative_resistivity_rejected():
    with pytest.raises(ValueError, match="resistivity_at_20C must be positive"):
        Electromagnetic(
            resistivity_at_20C=PV(
                d_value=-1e-8, s_units="Ohm*m", s_source="x", s_confidence="handbook"
            ),
        )


# ── Recoil permeability (v1.1.0) ─────────────────────────────────────────


def test_recoil_permeability_typical_value_accepted():
    """Sintered NdFeB μ_rec ≈ 1.05: must construct and round-trip."""
    em = Electromagnetic(
        recoil_permeability=PV(
            d_value=1.05,
            s_units="",
            s_source="Arnold/Shin-Etsu",
            s_confidence="datasheet",
        ),
    )
    assert em.d_recoil_permeability == pytest.approx(1.05)


def test_recoil_permeability_missing_raises():
    em = Electromagnetic()
    with pytest.raises(ValueError, match="recoil_permeability"):
        _ = em.d_recoil_permeability


def test_recoil_permeability_zero_rejected():
    """μ_rec = 0 is unphysical."""
    with pytest.raises(ValueError, match="recoil_permeability must be > 0"):
        Electromagnetic(
            recoil_permeability=PV(
                d_value=0.0,
                s_units="",
                s_source="x",
                s_confidence="handbook",
            ),
        )


def test_recoil_permeability_negative_rejected():
    with pytest.raises(ValueError, match="recoil_permeability must be > 0"):
        Electromagnetic(
            recoil_permeability=PV(
                d_value=-0.5,
                s_units="",
                s_source="x",
                s_confidence="handbook",
            ),
        )


def test_recoil_permeability_dimensionless_units_enforced():
    """μ_rec is dimensionless; non-empty units must be rejected by the
    units validator (it's not 'T' or 'A/m')."""
    with pytest.raises(ValueError):
        Electromagnetic(
            recoil_permeability=PV(
                d_value=1.05,
                s_units="H/m",  # wrong: μ_rec is dimensionless
                s_source="x",
                s_confidence="handbook",
            ),
        )


def test_recoil_permeability_separate_from_relative_permeability():
    """The two slots are physically distinct: populating one must NOT
    populate the other. Hard magnets in the catalog leave
    relative_permeability None and populate recoil_permeability."""
    em = Electromagnetic(
        recoil_permeability=PV(
            d_value=1.05,
            s_units="",
            s_source="x",
            s_confidence="datasheet",
        ),
    )
    assert em.relative_permeability is None
    assert em.recoil_permeability is not None
    # accessor for the missing slot still raises:
    with pytest.raises(ValueError, match="relative_permeability"):
        _ = em.d_relative_permeability


# ── BH curve field (v1.2.0) ──────────────────────────────────────────────


def test_bh_curve_field_accepts_BHCurveData():
    from emergent_matter_materials.bh_curve import BHCurveData

    em = Electromagnetic(
        bh_curve=BHCurveData(
            d_B_table_T=(0.5, 1.0, 1.5),
            d_H_table_A_m=(50.0, 200.0, 1700.0),
            s_source="x",
            s_condition="DC virgin curve, 20 C",
            s_confidence="datasheet",
        ),
    )
    assert em.bh_curve is not None
    assert em.d_bh_curve_B_T == (0.5, 1.0, 1.5)
    assert em.d_bh_curve_H_A_m == (50.0, 200.0, 1700.0)


def test_bh_curve_None_default():
    em = Electromagnetic()
    assert em.bh_curve is None


def test_bh_curve_accessor_raises_when_None():
    em = Electromagnetic()
    with pytest.raises(ValueError, match="bh_curve"):
        _ = em.d_bh_curve_B_T
    with pytest.raises(ValueError, match="bh_curve"):
        _ = em.d_bh_curve_H_A_m


def test_bh_curve_does_not_trigger_units_validation():
    """bh_curve is a composite, not a PropertyValue: it must NOT be in
    the units-validator group_fields set (otherwise _validate_group_units
    would crash trying to read .s_units on a BHCurveData)."""
    from emergent_matter_materials.bh_curve import BHCurveData

    # If this raises, the validator is incorrectly trying to validate
    # bh_curve as a PropertyValue.
    em = Electromagnetic(
        bh_curve=BHCurveData(
            d_B_table_T=(0.5, 1.0, 1.5),
            d_H_table_A_m=(50.0, 200.0, 1700.0),
            s_source="x",
            s_condition="x",
            s_confidence="datasheet",
        ),
    )
    assert em.bh_curve is not None
