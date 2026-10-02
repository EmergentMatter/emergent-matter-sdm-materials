"""Tests for operating-point callables (e.g. resistivity_at_T).

The callable infrastructure itself is JAX-traceable and well-tested at
the unit level (test_electromagnetic_schema.py). These integration
tests exercise the callable on actual catalog data, but v0.2.0
removed pure_copper and aluminum_6061_t6 resistivity values because
they weren't sourced from a Tier 1 primary. As a result, these tests
construct a synthetic Electromagnetic with Tier 1-equivalent values
to verify the callable still works end-to-end.

When NIST SRD JPCRD 7 (Thermal Conductivity of the Elements) or
JPCRD 9 (Electrical Resistivity of Pure Metals) is properly cited
in pure_copper / aluminum_6061_t6, these tests can be re-pointed at
catalog materials.
"""

from __future__ import annotations

import pytest

from emergent_matter_materials.electromagnetic import Electromagnetic
from emergent_matter_materials.property_value import PropertyValue as PV


def _cu_synthetic() -> Electromagnetic:
    """Synthetic Cu electromagnetic: values are textbook Cu, marked
    'standard' to satisfy schema validation. Once NIST SRD is cited
    in pure_copper, this can be deleted in favor of the real catalog
    entry."""
    return Electromagnetic(
        resistivity_at_20C=PV(
            d_value=1.68e-8,
            s_units="Ohm*m",
            s_source="Synthetic test fixture (textbook Cu); replace with "
            "NIST SRD JPCRD 7 citation once pure_copper has it.",
            s_confidence="standard",
        ),
        temp_coeff_resistivity=PV(
            d_value=3.93e-3,
            s_units="1/K",
            s_source="Synthetic test fixture (textbook Cu)",
            s_confidence="standard",
        ),
    )


def test_resistivity_at_20C_equals_anchor():
    em = _cu_synthetic()
    rho_20 = em.d_resistivity_at_T(20.0)
    expected = em.d_resistivity_at_20C_ohm_m
    assert float(rho_20) == pytest.approx(expected, rel=1e-9)


def test_resistivity_increases_with_temperature():
    em = _cu_synthetic()
    rho_20 = float(em.d_resistivity_at_T(20.0))
    rho_100 = float(em.d_resistivity_at_T(100.0))
    rho_200 = float(em.d_resistivity_at_T(200.0))
    assert rho_20 < rho_100 < rho_200


def test_resistivity_at_T_vmap():
    """JAX vmap over temperature."""
    pytest.importorskip("jax")
    import jax
    import jax.numpy as jnp

    em = _cu_synthetic()
    T_array = jnp.linspace(20.0, 200.0, 10)
    rho_array = jax.vmap(em.d_resistivity_at_T)(T_array)
    assert rho_array.shape == (10,)
    for i in range(9):
        assert float(rho_array[i + 1]) > float(rho_array[i])


def test_resistivity_at_T_grad():
    """Backprop through resistivity_at_T(T) for downstream optimizers."""
    pytest.importorskip("jax")
    import jax

    em = _cu_synthetic()
    drho_dT = jax.grad(em.d_resistivity_at_T)(50.0)
    expected = 1.68e-8 * 3.93e-3
    assert float(drho_dT) == pytest.approx(expected, rel=1e-6)
