"""Tests for the public accessor API: MATERIALS, get, aliases, registry."""

from __future__ import annotations

import pytest

from emergent_matter_materials.accessors import (
    _ALIASES,
    _PROPERTY_MAP,
    MATERIALS,
    get,
    get_material,
    get_with_metadata,
    list_aliases,
    list_materials,
    list_properties,
    material_summary,
    register_material,
)
from emergent_matter_materials.property_value import PropertyValue as PV

# ── Catalog presence ───────────────────────────────────────────────────────


def test_materials_dict_populated():
    """v0.2.0 Tier-1-only catalog has 14 materials (down from v0.1.x's 21).
    Floor of 10 catches catastrophic regression."""
    assert len(MATERIALS) >= 10


def test_pure_copper_present():
    assert "pure_copper" in MATERIALS


def test_ndfeb_n42_present():
    assert "ndfeb_n42" in MATERIALS


def test_v0_2_0_deleted_materials_NOT_present():
    """v0.2.0 deleted these for lack of Tier 1 sources: recovery needs
    new Tier 1 sources. Some have been
    restored in later patches (m19_silicon_steel in v0.2.1)."""
    still_deleted = {"mnzn_ferrite", "ferrite_y30", "alnico_5", "tpu_95a", "pla_fdm", "petg_fdm"}
    for s_id in still_deleted:
        assert s_id not in MATERIALS, f"{s_id} was deleted in v0.2.0: should not be in catalog"


# ── get_material + alias resolution ────────────────────────────────────────


def test_get_material_by_canonical_id():
    m = get_material("pure_copper")
    assert m.s_id == "pure_copper"


def test_get_material_by_alias():
    m = get_material("Cu")
    assert m.s_id == "pure_copper"


def test_get_material_unknown_raises():
    with pytest.raises(KeyError, match="Unknown material"):
        get_material("totally_made_up")


def test_alias_M270_35A_resolves():
    """M270-35A: grade-defining core_loss is in EN 10106."""
    m = get_material("M270_35A")
    assert m.s_id == "m270_35a_silicon_steel"


def test_alias_M19_resolves():
    """v0.2.1 restored M19 alias when m19_silicon_steel returned with
    Tier 1 core_loss (Cleveland-Cliffs DI-MAX June 2023) + thermal_k
    (NREL IJHMT 2018)."""
    m = get_material("M19")
    assert m.s_id == "m19_silicon_steel"


def test_bare_Al_NOT_registered():
    """Bare 'Al' is deliberately ambiguous: must NOT be in aliases."""
    assert "Al" not in _ALIASES
    with pytest.raises(KeyError):
        get_material("Al")


def test_bare_NdFeB_NOT_registered():
    """Bare 'NdFeB' is ambiguous between N35/N42/N50 grades."""
    assert "NdFeB" not in _ALIASES
    with pytest.raises(KeyError):
        get_material("NdFeB")


def test_bare_Steel_NOT_registered():
    assert "Steel" not in _ALIASES
    with pytest.raises(KeyError):
        get_material("Steel")


def test_all_aliases_resolve_to_valid_materials():
    """Every alias's target must be a real catalog material."""
    for alias, target in _ALIASES.items():
        assert target in MATERIALS, (
            f"Alias {alias!r} → {target!r} but {target!r} is not in MATERIALS"
        )


# ── get + get_with_metadata ────────────────────────────────────────────────


def test_get_returns_float():
    """Use a Tier-1-verified property: Hiperco 50 density is from
    Carpenter E200 datasheet."""
    val = get("Hiperco", "rho")
    assert isinstance(val, float)
    assert val == 8110.0


def test_get_with_metadata_returns_propertyvalue():
    pv = get_with_metadata("Hiperco", "rho")
    assert pv.d_value == 8110.0
    assert pv.s_units == "kg/m^3"
    assert pv.s_source != ""
    assert pv.s_confidence == "datasheet"


def test_get_on_deleted_property_raises():
    """v0.6.0 restored Cu structural (E, nu, yield, UTS) + thermal CTE +
    melting_temp. Test a still-deleted property: Cu's thermal.max_operating_temp
    has no Tier 1 source (Cu loses temper progressively above ~200 C without
    a canonical scalar max-op-temp in ASM Vol 2)."""
    with pytest.raises(ValueError, match="is None"):
        get("Cu", "T_max")


def test_get_unknown_property_raises():
    with pytest.raises(KeyError, match="Unknown property"):
        get("Cu", "made_up_property")


def test_get_missing_group_raises():
    """4140 steel has no electromagnetic group → asking for B_sat raises."""
    with pytest.raises(ValueError, match="has no electromagnetic group"):
        get("Steel_4140", "B_sat")


def test_get_missing_field_raises():
    """Hiperco has thermal group but no specific_heat (Carpenter E200
    doesn't publish c_p; v0.6.0 docs flag this as a sourcing gap that
    has no Tier-1 primary). Previously this test used Hiperco.B_r as
    the canary, but v0.7.0 restored B_r = 2.0 T from the Carpenter
    E200 datasheet, so c_p is the new still-None canary."""
    with pytest.raises(ValueError, match="is None"):
        get("Hiperco", "c_p")


# ── Property map coverage ──────────────────────────────────────────────────


def test_property_map_has_all_standard_short_names():
    for short in ("rho", "E", "nu", "sigma_y", "UTS", "sigma_f"):
        assert short in _PROPERTY_MAP, f"{short!r} missing from _PROPERTY_MAP"


def test_property_map_has_EM_names():
    for short in ("resistivity", "mu_r", "B_sat", "B_r", "H_c", "core_loss"):
        assert short in _PROPERTY_MAP


def test_property_map_has_thermal_names():
    for short in ("k_thermal", "c_p", "T_max", "CTE", "T_g", "T_c"):
        assert short in _PROPERTY_MAP


# ── list_* helpers ─────────────────────────────────────────────────────────


def test_list_materials_returns_all():
    ids = list_materials()
    assert "pure_copper" in ids
    assert "hiperco_50" in ids
    assert ids == sorted(ids)


def test_list_materials_by_category_metal():
    metals = list_materials(s_category="metal")
    assert "pure_copper" in metals
    assert "aluminum_6061_t6" in metals


def test_list_materials_by_category_magnet():
    magnets = list_materials(s_category="magnet")
    assert "ndfeb_n42" in magnets
    # ferrite_y30 + alnico_5 were deleted in v0.2.0


def test_list_materials_by_category_soft_magnetic():
    soft = list_materials(s_category="soft_magnetic")
    assert "hiperco_50" in soft
    assert "m270_35a_silicon_steel" in soft
    # m19_silicon_steel + mnzn_ferrite were deleted in v0.2.0


def test_list_properties_includes_known():
    props = list_properties()
    assert "rho" in props
    assert "B_sat" in props
    assert "k_thermal" in props
    assert props == sorted(props)


def test_list_aliases_returns_copy():
    a1 = list_aliases()
    a1["new_alias"] = "fake"
    a2 = list_aliases()
    assert "new_alias" not in a2  # mutation didn't affect internal state


# ── material_summary ───────────────────────────────────────────────────────


def test_material_summary_includes_specification():
    s = material_summary("hiperco_50")
    assert "Carpenter" in s or "Hiperco" in s


def test_material_summary_lists_groups():
    s = material_summary("Hiperco")
    # Hiperco has structural + electromagnetic + thermal
    assert "structural" in s
    assert "electromagnetic" in s
    assert "thermal" in s


# ── register_material ──────────────────────────────────────────────────────


def test_register_material_name_mismatch_rejected():
    from emergent_matter_materials.material import Material
    from emergent_matter_materials.structural import Structural

    s = Structural(
        youngs_modulus=PV(d_value=1e9, s_units="Pa", s_source="x", s_confidence="handbook"),
        poisson_ratio=PV(d_value=0.3, s_units="", s_source="x", s_confidence="handbook"),
        yield_stress=PV(d_value=1e8, s_units="Pa", s_source="x", s_confidence="handbook"),
        fatigue_endurance=PV(d_value=5e7, s_units="Pa", s_source="x", s_confidence="handbook"),
        ultimate_tensile=PV(d_value=2e8, s_units="Pa", s_source="x", s_confidence="handbook"),
        density=PV(d_value=2000.0, s_units="kg/m^3", s_source="x", s_confidence="handbook"),
    )
    m = Material(
        s_id="my_custom",
        s_description="Custom",
        s_category="composite",
        s_specification="custom",
        s_catalog_version="0.1.0",
        s_last_reviewed="2026-05-24",
        structural=s,
    )
    with pytest.raises(ValueError, match="name.*!= Material.s_id"):
        register_material("wrong_name", m)


# ── v0.4.0: crystal_anisotropy short-name accessors ────────────────────────


def test_get_C11_returns_cu_elastic_constant():
    """Short-name accessor 'C11' routes through _PROPERTY_MAP to
    crystal_anisotropy.c11 on the resolved material."""
    val = get("Cu", "C11")
    assert val == 168.4e9


def test_get_C12_routing():
    val = get("Cu", "C12")
    assert val == 121.4e9


def test_get_C44_routing():
    val = get("Cu", "C44")
    assert val == 75.4e9


def test_get_burgers_vector_short_name():
    val = get("Cu", "b")
    assert abs(val - 2.556e-10) < 1e-13


def test_get_stacking_fault_energy_short_name():
    val = get("Cu", "gamma_SFE")
    assert val == 0.078


def test_get_crss_short_name():
    val = get("Cu", "tau_CRSS")
    assert val == 0.4e6


def test_get_with_metadata_C11_carries_tier1_citation():
    pv = get_with_metadata("M19", "C11")
    assert pv.d_value == 226e9
    assert pv.s_units == "Pa"
    assert pv.s_confidence in {"measured", "datasheet", "standard"}
    # The Machova-Kadeckova 1977 primary should be cited
    assert "Machova" in pv.s_source or "Machová" in pv.s_source


def test_get_C13_hcp_on_titanium():
    """Ti-6Al-4V is HCP: C13 is populated (non-cubic constant)."""
    val = get("Ti_6Al_4V", "C13")
    assert val == 69.0e9


def test_get_C13_fcc_raises():
    """Cubic materials have C13 = None (= C12 by symmetry, not stored)."""
    with pytest.raises(ValueError, match="None"):
        get("Cu", "C13")


def test_get_C66_on_cubic_raises():
    """Cubic materials have C66 = None (= C44 by symmetry)."""
    with pytest.raises(ValueError, match="None"):
        get("M19", "C66")


def test_get_crss_on_alloy_raises():
    """Steel 4140 + alloys do NOT have crss_initial populated."""
    with pytest.raises(ValueError, match="None"):
        get("Steel_4140", "tau_CRSS")


def test_property_map_includes_crystal_anisotropy_entries():
    """v0.4.0 adds 9 short names to _PROPERTY_MAP routing to crystal_anisotropy."""
    expected = {"C11", "C12", "C13", "C33", "C44", "C66", "b", "gamma_SFE", "tau_CRSS"}
    assert expected.issubset(set(_PROPERTY_MAP)), (
        f"Missing v0.4.0 short names: {expected - set(_PROPERTY_MAP)}"
    )
    for name in expected:
        group, _field = _PROPERTY_MAP[name]
        assert group == "crystal_anisotropy", (
            f"_PROPERTY_MAP[{name!r}] routes to {group!r}, not crystal_anisotropy"
        )
