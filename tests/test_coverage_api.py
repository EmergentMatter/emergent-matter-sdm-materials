"""Tests for the coverage() introspection API.

A machine-readable "what data is present/missing/unsupported" report so
consumers (FEM solvers, design tools) can plan queries without
exception-driven probing. Pure introspection: no physics, no data, no
mutation.
"""

from __future__ import annotations

import dataclasses

import pytest

from emergent_matter_materials import (
    RotationalLossData,
    coverage,
    get_material,
    list_materials,
)

_GROUPS = {"structural", "electromagnetic", "thermal", "manufacturing", "crystal_anisotropy"}


# ── shape ───────────────────────────────────────────────────────────────────


def test_top_level_shape():
    c = coverage("pure_copper")
    assert c["s_id"] == "pure_copper"
    assert c["s_category"] == "metal"
    assert set(c["groups"]) == _GROUPS  # all five groups always keyed


def test_accepts_alias_and_object():
    by_alias = coverage("Cu")
    by_object = coverage(get_material("pure_copper"))
    assert by_alias["s_id"] == by_object["s_id"] == "pure_copper"
    assert by_alias == by_object


def test_group_field_accounting_consistent():
    """n_present + len(missing) == n_total, and missing == the False fields."""
    for s_id in list_materials():
        c = coverage(s_id)
        for info in c["groups"].values():
            assert info["n_present"] + len(info["missing"]) == info["n_total"]
            assert set(info["missing"]) == {k for k, v in info["fields"].items() if not v}
            assert info["n_present"] == sum(1 for v in info["fields"].values() if v)


def test_absent_group_reported_present_false():
    c = coverage("pure_copper")
    assert c["groups"]["manufacturing"]["present"] is False  # None on all materials
    assert c["groups"]["manufacturing"]["fields"] == {}
    # a magnet has no crystal_anisotropy group:
    assert coverage("ndfeb_n42")["groups"]["crystal_anisotropy"]["present"] is False


# ── scalar fields ───────────────────────────────────────────────────────────


def test_copper_em_scalar_coverage():
    em = coverage("pure_copper")["groups"]["electromagnetic"]
    assert em["fields"]["resistivity_at_20C"] is True
    assert em["fields"]["temp_coeff_resistivity"] is True
    assert em["fields"]["relative_permeability"] is True
    assert em["fields"]["saturation_flux"] is False  # not a magnet
    assert "saturation_flux" in em["missing"]


# ── composites ──────────────────────────────────────────────────────────────


def test_composites_reported():
    """bh_curve/steinmetz -> bool; rotational_loss_models -> int count."""
    m270 = coverage("m270_35a_silicon_steel")["groups"]["electromagnetic"]["composites"]
    assert m270["bh_curve"] is True
    assert m270["steinmetz"] is True
    assert m270["rotational_loss_models"] == 0

    cu = coverage("pure_copper")["groups"]["electromagnetic"]["composites"]
    assert cu["bh_curve"] is False
    assert cu["steinmetz"] is False
    assert cu["rotational_loss_models"] == 0


def test_magnet_new_v18_field_present():
    """The v1.8.0 temp_coeff_coercivity shows up as a populated scalar."""
    em = coverage("ndfeb_n42")["groups"]["electromagnetic"]
    assert em["fields"]["temp_coeff_coercivity"] is True
    assert em["fields"]["recoil_permeability"] is True
    assert em["fields"]["remanence"] is True


def test_rotational_count_reflects_records():
    """A material with N synthetic rotational records reports that count."""
    rec = RotationalLossData(
        s_form="citation_only",
        n_completeness_level=0,
        s_source="synthetic",
        s_confidence="handbook",
    )
    base = get_material("m19_silicon_steel")
    em = dataclasses.replace(base.electromagnetic, rotational_loss_models=(rec, rec))
    mat = dataclasses.replace(base, electromagnetic=em)
    cov = coverage(mat)
    assert cov["groups"]["electromagnetic"]["composites"]["rotational_loss_models"] == 2


# ── metadata strings are not counted as data slots ──────────────────────────


def test_string_metadata_not_in_accounting():
    """crystal_anisotropy.s_crystal_structure is metadata, not a data slot:
    it must not appear in fields or composites."""
    # Use a material WITH a crystal_anisotropy group:
    ca = coverage("pure_copper")["groups"]["crystal_anisotropy"]
    assert ca["present"] is True
    assert "s_crystal_structure" not in ca["fields"]
    assert "s_crystal_structure" not in ca["composites"]
    # the actual C_ij slots ARE counted:
    assert "c11" in ca["fields"]


# ── purity: no mutation / deterministic ─────────────────────────────────────


def test_idempotent_no_mutation():
    before = coverage("ndfeb_n42")
    after = coverage("ndfeb_n42")
    assert before == after
    # catalog object unchanged (coverage reads only):
    assert get_material("ndfeb_n42").electromagnetic.temp_coeff_coercivity is not None


def test_unknown_material_raises_keyerror():
    with pytest.raises(KeyError):
        coverage("not_a_real_material")


# ── works for every catalog material without error ──────────────────────────


def test_runs_for_entire_catalog():
    for s_id in list_materials():
        c = coverage(s_id)
        assert c["s_id"] == s_id
        assert set(c["groups"]) == _GROUPS
