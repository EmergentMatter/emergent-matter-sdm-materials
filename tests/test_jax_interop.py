"""Tests for to_jax_pytree() with all three missing-policy modes."""

from __future__ import annotations

import pytest

from emergent_matter_materials.accessors import get_material

# The imports below must follow this guard -- it's what lets the module
# skip cleanly when jax isn't installed, instead of failing at collection
# with ModuleNotFoundError.
jax = pytest.importorskip("jax")  # noqa: E402
import jax.numpy as jnp  # noqa: E402

from emergent_matter_materials.jax_interop import to_jax_pytree  # noqa: E402

# ── Mode: error (default) ──────────────────────────────────────────────────


def test_error_mode_raises_on_missing_em_fields():
    """Hiperco has EM group but missing fields (no remanence, etc.)."""
    hiperco = get_material("Hiperco")
    with pytest.raises(ValueError, match="s_missing='error'"):
        to_jax_pytree(hiperco)  # default is "error"


# ── Mode: omit ─────────────────────────────────────────────────────────────


def test_omit_mode_drops_none_fields():
    """v0.7.0: Hiperco EM has mu_r, B_sat, core_loss, coercivity,
    remanence, resistivity_at_20C populated (all from Carpenter E200);
    temp_coeff_resistivity + temp_coeff_remanence remain None
    (Carpenter does not publish either)."""
    hiperco = get_material("Hiperco")
    tree = to_jax_pytree(hiperco, s_missing="omit")
    em = tree["electromagnetic"]
    assert "relative_permeability" in em
    assert "saturation_flux" in em
    assert "core_loss" in em
    assert "temp_coeff_resistivity" not in em  # Carpenter doesn't publish
    assert "temp_coeff_remanence" not in em  # permanent-magnet-only field


def test_omit_mode_preserves_full_groups():
    hiperco = get_material("Hiperco")
    tree = to_jax_pytree(hiperco, s_missing="omit")
    # Hiperco density from Carpenter datasheet is 8110 kg/m^3
    assert float(tree["structural"]["density"]) == 8110.0


def test_omit_mode_returns_jnp_scalars():
    hiperco = get_material("Hiperco")
    tree = to_jax_pytree(hiperco, s_missing="omit")
    val = tree["structural"]["youngs_modulus"]
    assert hasattr(val, "shape"), f"expected jnp array, got {type(val).__name__}"


# ── Mode: nan ──────────────────────────────────────────────────────────────


def test_nan_mode_fills_missing_with_nan():
    hiperco = get_material("Hiperco")
    tree = to_jax_pytree(hiperco, s_missing="nan")
    em = tree["electromagnetic"]
    # v0.7.0: Hiperco.remanence is now populated (= 2.0 T per Carpenter).
    # Fields Hiperco still doesn't have (temp_coeff_remanence, only
    # relevant for permanent magnets) get nan-filled.
    assert "temp_coeff_remanence" in em
    assert jnp.isnan(em["temp_coeff_remanence"]).item()


def test_nan_mode_preserves_populated_values():
    hiperco = get_material("Hiperco")
    tree = to_jax_pytree(hiperco, s_missing="nan")
    # B_sat is populated: must be the real value
    b_sat = tree["electromagnetic"]["saturation_flux"]
    assert not jnp.isnan(b_sat).item()
    assert float(b_sat) == pytest.approx(2.40, rel=1e-5)


def test_nan_mode_shape_stable_across_materials():
    """Two materials with EM groups should produce identical pytree shapes
    under nan mode (the schema enumerates all fields)."""
    n35_tree = to_jax_pytree(get_material("NdFeB_N35"), s_missing="nan")
    n42_tree = to_jax_pytree(get_material("NdFeB_N42"), s_missing="nan")
    assert sorted(n35_tree["electromagnetic"].keys()) == sorted(n42_tree["electromagnetic"].keys())


# ── Argument validation ────────────────────────────────────────────────────


def test_bad_missing_policy_rejected():
    cu = get_material("Cu")
    with pytest.raises(ValueError, match="must be 'omit', 'nan', or 'error'"):
        to_jax_pytree(cu, s_missing="silent")  # type: ignore[arg-type]


# ── Absent groups (not just absent fields) ─────────────────────────────────


def test_absent_group_omitted_in_omit_and_nan_modes():
    """Ti-6Al-4V has no electromagnetic group after v0.2.0 Tier 1 cleanup
    (resistivity wasn't in any Tier 1 source). Test that omit/nan modes
    handle this cleanly."""
    ti = get_material("Ti_6Al_4V")
    assert ti.electromagnetic is None

    for s_missing in ("omit", "nan"):
        tree = to_jax_pytree(ti, s_missing=s_missing)
        assert "electromagnetic" not in tree
        assert "structural" in tree


def test_absent_group_with_optional_fields_raises_in_error_mode():
    """error mode is strict: any None field on a populated group raises.
    Steel 4140 has Structural with only fatigue_endurance populated."""
    steel = get_material("Steel_4140")
    with pytest.raises(ValueError, match="s_missing='error'"):
        to_jax_pytree(steel, s_missing="error")
