"""Tests for aluminum_1350_ec: winding-grade EC aluminium conductor.

Added in the Commercial Readiness Sprint 1. Verifies the new conductor
material is present, carries the IEC 60889 Tier-1 EM properties, is reachable
via the flat accessor + aliases, and is distinct from the structural 6061-T6
alloy (which must NOT be used as a winding conductor).
"""

from __future__ import annotations

import pytest

from emergent_matter_materials import get, get_material, get_with_metadata


def test_material_present_and_metal():
    m = get_material("aluminum_1350_ec")
    assert m.s_id == "aluminum_1350_ec"
    assert m.s_category == "metal"
    assert "1350" in m.s_specification and "IEC 60889" in m.s_specification


def test_aliases_resolve():
    for alias in ("Al_1350", "Al_EC"):
        assert get_material(alias).s_id == "aluminum_1350_ec"


def test_resistivity_iec60889_value():
    """61.0% IACS reference: ρ20 = 2.8264e-8 Ω·m (IEC 60889)."""
    assert get("aluminum_1350_ec", "resistivity") == pytest.approx(2.8264e-8, rel=1e-9)
    pv = get_with_metadata("aluminum_1350_ec", "resistivity")
    assert pv.s_confidence == "standard"
    assert "IEC 60889" in pv.s_source


def test_temp_coeff_iec60889_value():
    assert get("aluminum_1350_ec", "alpha_rho") == pytest.approx(4.03e-3, rel=1e-9)


def test_relative_permeability_paramagnetic():
    mu_r = get("aluminum_1350_ec", "mu_r")
    assert mu_r == pytest.approx(1.000022, rel=1e-9)
    assert mu_r > 1.0  # paramagnetic


def test_density_present():
    assert get("aluminum_1350_ec", "rho") == pytest.approx(2700.0)


def test_resistivity_at_T_callable_works():
    """The JAX-traceable ρ(T) accessor must work and rise with temperature:
    this is what an AC/DC copper-loss model consumes for hot windings."""
    em = get_material("aluminum_1350_ec").electromagnetic
    rho_20 = em.d_resistivity_at_T(20.0)
    rho_150 = em.d_resistivity_at_T(150.0)
    assert rho_20 == pytest.approx(2.8264e-8, rel=1e-9)
    # ρ(150) = ρ20 * (1 + α*(150-20)) = 2.8264e-8 * (1 + 0.00403*130)
    assert rho_150 == pytest.approx(2.8264e-8 * (1.0 + 4.03e-3 * 130.0), rel=1e-9)
    assert rho_150 > rho_20


def test_distinct_from_6061_structural_alloy():
    """1350 conductor must be clearly lower-resistivity than 6061-T6
    structural alloy: proving 6061 cannot proxy for a winding conductor."""
    rho_1350 = get("aluminum_1350_ec", "resistivity")
    rho_6061 = get("aluminum_6061_t6", "resistivity")
    assert rho_1350 < rho_6061
    # ~41% lower (2.8264e-8 vs 3.99e-8)
    assert rho_1350 / rho_6061 == pytest.approx(2.8264e-8 / 3.99e-8, rel=1e-6)


def test_no_geometry_fields_crept_in():
    """Conductor GEOMETRY (strand count, fill factor, etc.) must NOT live on
    the material, only bulk material properties. Guard: the material exposes
    no field whose name suggests winding geometry."""
    m = get_material("aluminum_1350_ec")
    banned = ("strand", "litz", "fill_factor", "slot", "turns", "awg", "gauge")
    for group_name in (
        "structural",
        "electromagnetic",
        "thermal",
        "manufacturing",
        "crystal_anisotropy",
    ):
        group = getattr(m, group_name)
        if group is None:
            continue
        import dataclasses

        for f in dataclasses.fields(group):
            assert not any(b in f.name.lower() for b in banned), (
                f"geometry-like field {f.name!r} on {group_name}"
            )
