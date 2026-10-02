"""Catalog-wide integrity tests.

These run against the populated MATERIALS catalog (not synthetic
test fixtures) to verify nothing has slipped through the per-entry
validators with bad cross-references or schema drift.
"""

from __future__ import annotations

from emergent_matter_materials.accessors import _ALIASES, _PROPERTY_MAP, MATERIALS


def test_catalog_has_at_least_10_materials():
    """v0.2.0 floor: 14 materials. Test catches catastrophic shrinkage."""
    assert len(MATERIALS) >= 10


def test_catalog_has_at_most_50_materials():
    """If we exceed 50, time to consider YAML/TOML migration."""
    assert len(MATERIALS) <= 50


def test_every_s_id_matches_key():
    for s_key, m in MATERIALS.items():
        assert m.s_id == s_key, f"MATERIALS[{s_key!r}].s_id = {m.s_id!r}"


def test_every_material_has_at_least_one_group():
    """Material.__post_init__ already enforces this; this is the
    catalog-wide belt-and-suspenders check."""
    for s_id, m in MATERIALS.items():
        populated = [
            g
            for g in (
                m.structural,
                m.electromagnetic,
                m.thermal,
                m.manufacturing,
                m.crystal_anisotropy,
            )
            if g is not None
        ]
        assert len(populated) >= 1, f"Material {s_id!r} has no populated groups"


def test_every_material_has_at_least_one_populated_group():
    """v0.2.0: under Tier 1 only, some materials have sparse data
    (e.g., aluminum_6061_t6 has only fatigue + temp_coeff_resistivity).
    Test that every material still has SOMETHING populated: Material
    __post_init__ already enforces this; this is the belt-and-suspenders
    scan."""
    for s_id, m in MATERIALS.items():
        groups = [m.structural, m.electromagnetic, m.thermal, m.manufacturing, m.crystal_anisotropy]
        assert any(g is not None for g in groups), f"Material {s_id!r} has no populated groups"


def test_every_alias_target_exists():
    for alias, target in _ALIASES.items():
        assert target in MATERIALS, f"alias {alias!r} → {target!r} not in MATERIALS"


def test_every_property_in_map_uses_known_group():
    valid_groups = {
        "structural",
        "electromagnetic",
        "thermal",
        "manufacturing",
        "crystal_anisotropy",
    }
    for prop, (group, _field) in _PROPERTY_MAP.items():
        assert group in valid_groups, f"_PROPERTY_MAP[{prop!r}] uses unknown group {group!r}"


def test_each_category_represented():
    """The catalog has >= 1 entry per advertised category."""
    cats_in_catalog = {m.s_category for m in MATERIALS.values()}
    # We require at least metal + polymer + magnet + soft_magnetic in v0.1
    required = {"metal", "polymer", "magnet", "soft_magnetic"}
    missing = required - cats_in_catalog
    assert not missing, f"Required categories missing from catalog: {missing}"


# ── v0.4.0 CrystalAnisotropy integrity ──────────────────────────────────────

#: Phase 1 materials that MUST have crystal_anisotropy populated (Tier 1
#: sourceable, slip-dominated or elastic-anisotropy-relevant).
_PHASE1_CRYSTAL_ANISOTROPY = frozenset(
    {
        "pure_copper",
        "aluminum_6061_t6",
        "stainless_304",
        "stainless_316",
        "steel_4140",
        "titanium_6al_4v",
        "hiperco_50",
        "m19_silicon_steel",
        "m270_35a_silicon_steel",
    }
)

#: Materials that MUST have crystal_anisotropy=None (amorphous, nano-
#: crystalline averaged, polymers: no meaningful single-crystal C_ij at
#: engineering scale).
_AMORPHOUS_AND_POLYMERS = frozenset(
    {
        "metglas_2605sa1",
        "vitroperm_500f",
        "peek_unfilled",
        "pei_ultem_1010",
        "nylon12_sls",
        "nomex_410",
        "mw_pai_class_200",
        "mw_pur_class_130",
        "petg_3dprint",
        "kapton_hn",
        "mnzn_ferrite_3c95",  # sintered polycrystalline ceramic, no single-crystal C_ij
        "alumina_ad96",
        "aln_maruwa_an170",
        "stycast_2850ft",
        "tpu_elastollan_1195a",
    }
)


def test_phase1_materials_all_have_crystal_anisotropy():
    """v0.4.0 contract: 9 Phase 1 materials all populated."""
    for s_id in _PHASE1_CRYSTAL_ANISOTROPY:
        assert s_id in MATERIALS, f"Phase 1 material {s_id!r} missing from catalog"
        m = MATERIALS[s_id]
        assert m.crystal_anisotropy is not None, (
            f"Phase 1 material {s_id!r} missing crystal_anisotropy: "
            f"v0.4.0 promises this is populated"
        )


def test_amorphous_and_polymers_have_no_crystal_anisotropy():
    """Materials with no single-crystal structure must NOT carry C_ij."""
    for s_id in _AMORPHOUS_AND_POLYMERS:
        assert s_id in MATERIALS, f"Material {s_id!r} missing from catalog"
        m = MATERIALS[s_id]
        assert m.crystal_anisotropy is None, (
            f"Material {s_id!r} has crystal_anisotropy populated, but it's on "
            f"the amorphous/polymer skip-list: no meaningful single-crystal "
            f"C_ij at engineering scale. Remove the crystal_anisotropy "
            f"argument or move {s_id!r} off the skip-list."
        )


def test_cu_zener_anisotropy_in_canonical_band():
    """Pure Cu Zener A = 2*C44/(C11-C12) ~ 3.21 from Overton-Gaffney 1955."""
    cu = MATERIALS["pure_copper"]
    A = cu.crystal_anisotropy.d_zener_anisotropy
    assert 3.0 <= A <= 3.4, f"pure_copper Zener anisotropy out of band: {A:.3f}"


def test_al6061_zener_anisotropy_in_canonical_band():
    """Al ~1.22 from Kamm-Alers 1964 (relatively isotropic for an FCC metal)."""
    al = MATERIALS["aluminum_6061_t6"]
    A = al.crystal_anisotropy.d_zener_anisotropy
    assert 1.1 <= A <= 1.4, f"aluminum_6061_t6 Zener out of band: {A:.3f}"


def test_alpha_fe_based_zener_in_canonical_band():
    """BCC alpha-Fe-based materials (4140 ferrite, Hiperco B2 FeCo, Fe-3Si
    M19/M270) should sit in Zener ~2.0-3.0: classic BCC anisotropy."""
    for s_id in ("steel_4140", "hiperco_50", "m19_silicon_steel", "m270_35a_silicon_steel"):
        m = MATERIALS[s_id]
        A = m.crystal_anisotropy.d_zener_anisotropy
        assert 2.0 <= A <= 3.0, (
            f"{s_id!r} Zener anisotropy out of BCC-Fe-family band [2.0, 3.0]: got {A:.3f}"
        )


def test_gamma_fe_austenitic_zener_in_canonical_band():
    """FCC gamma-Fe austenitic stainless (304, 316): highly anisotropic
    (~3.3-3.6 from Ledbetter 1984; higher than alpha-Fe BCC bands)."""
    for s_id in ("stainless_304", "stainless_316"):
        m = MATERIALS[s_id]
        A = m.crystal_anisotropy.d_zener_anisotropy
        assert 3.0 <= A <= 3.7, (
            f"{s_id!r} Zener anisotropy out of FCC-gamma-Fe band [3.0, 3.7]: got {A:.3f}"
        )


def test_phase1_zener_or_hcp_derived_accessor_works():
    """Every Phase 1 material's elastic-anisotropy accessor returns a finite
    positive number (Zener for cubic, d_c66_derived_Pa for HCP)."""
    for s_id in _PHASE1_CRYSTAL_ANISOTROPY:
        ca = MATERIALS[s_id].crystal_anisotropy
        if ca.s_crystal_structure in ("FCC", "BCC"):
            A = ca.d_zener_anisotropy
            assert A > 0 and A < 100, f"{s_id!r} Zener pathological: {A}"
        elif ca.s_crystal_structure == "HCP":
            c66 = ca.d_c66_derived_Pa
            assert c66 > 0 and c66 < 1e12, f"{s_id!r} c66 pathological: {c66}"


def test_phase1_fcc_metals_have_stacking_fault_energy():
    """FCC metals where slip-mode matters should have gamma_SFE populated
    (BCC + HCP do not have a canonical SFE scalar)."""
    fcc_with_sfe = {"pure_copper", "aluminum_6061_t6", "stainless_304", "stainless_316"}
    for s_id in fcc_with_sfe:
        ca = MATERIALS[s_id].crystal_anisotropy
        assert ca.stacking_fault_energy is not None, (
            f"FCC Phase 1 material {s_id!r} missing stacking_fault_energy"
        )
        sfe = ca.d_stacking_fault_energy_J_m2
        # FCC engineering SFEs span 0.01 to 0.30 J/m^2
        assert 0.01 <= sfe <= 0.30, f"{s_id!r} SFE physically implausible: {sfe} J/m^2"


def test_burgers_vector_in_physical_range():
    """All populated Burgers vectors should be ~0.2-0.5 nm
    (atomic-spacing scale; FCC <110> a/sqrt(2), BCC <111> a*sqrt(3)/2)."""
    for s_id, m in MATERIALS.items():
        if m.crystal_anisotropy is None:
            continue
        if m.crystal_anisotropy.burgers_vector is None:
            continue
        b = m.crystal_anisotropy.d_burgers_vector_m
        assert 2.0e-10 <= b <= 5.0e-10, (
            f"{s_id!r} Burgers vector |b| = {b * 1e9:.4f} nm out of physical range [0.20, 0.50] nm"
        )
