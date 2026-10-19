"""A derived material reuses its base, records each override and why, and never takes its id.

Pins that inherited values are the base's own objects (nothing copied),
that each override form (scalar, removal, whole table, single row, flow
curve) lands where it says and is re-validated, that conflicting or
reasonless overrides are rejected, and that the lineage survives
serialization.
"""

from __future__ import annotations

import dataclasses
import json

import pytest

from emergent_matter_materials import (
    MATERIALS,
    Derivation,
    FieldOverride,
    FlowCurve,
    Material,
    PropertyTable,
    PropertyValue,
    TablePoint,
    TableRowRemoval,
    derive_material,
    material_fingerprint,
)

#: Interpolation is plain linear arithmetic; this only absorbs float rounding.
INTERP_REL_TOL = 1e-12

_BASE_ID = "stainless_316"


def _base() -> Material:
    return MATERIALS[_BASE_ID]


def _pv(d_value: float, s_units: str, s_source: str = "EM lab report 7") -> PropertyValue:
    return PropertyValue(
        d_value=d_value, s_units=s_units, s_source=s_source, s_confidence="measured"
    )


def _k_table() -> PropertyTable:
    return PropertyTable.from_rows(
        [(25.0, 14.0), (500.0, 19.0), (1000.0, 25.0)],
        s_units="W/(m*K)",
        s_source="EM lab report 7",
        s_confidence="measured",
    )


def _derive(*overrides: FieldOverride, s_id: str = "em_stainless_316") -> Material:
    return derive_material(
        _base(),
        s_expected_base_fingerprint=material_fingerprint(_base()),
        s_id=s_id,
        overrides=overrides,
        s_catalog_version="0.1.0",
        s_last_reviewed="2026-10-16",
    )


def _override(s_path: str, value, s_reason: str = "Measured on our powder lot") -> FieldOverride:
    return FieldOverride(s_path, value, s_reason)


# ── Inheritance and lineage ────────────────────────────────────────────────


def test_inherited_values_are_the_bases_own_objects():
    derived = _derive(_override("thermal.temperature_tables.thermal_conductivity", _k_table()))
    base = _base()
    assert derived.structural is base.structural
    assert derived.thermal.thermal_conductivity is base.thermal.thermal_conductivity
    assert derived.s_category == base.s_category


def test_derivation_records_base_version_and_each_override_with_its_reason():
    derived = _derive(_override("thermal.temperature_tables.thermal_conductivity", _k_table()))
    lineage = derived.derivation
    assert lineage.s_base_id == _BASE_ID
    assert lineage.s_base_catalog_version == _base().s_catalog_version
    assert lineage.s_paths == ("thermal.temperature_tables.thermal_conductivity",)
    assert lineage.b_is_overridden("thermal.temperature_tables.thermal_conductivity")
    assert not lineage.b_is_overridden("thermal.thermal_conductivity")
    assert lineage.overrides_for("thermal.temperature_tables.thermal_conductivity")[0].s_reason == (
        "Measured on our powder lot"
    )


def test_description_and_specification_default_from_the_base():
    derived = _derive(_override("thermal.thermal_conductivity", _pv(15.0, "W/(m*K)")))
    assert derived.s_description == f"{_base().s_description} (derived from {_BASE_ID})"
    assert derived.s_specification == _base().s_specification
    assert derived.s_catalog_version == "0.1.0"


def test_authored_materials_have_no_derivation():
    assert all(m.derivation is None for m in MATERIALS.values())


# ── Each override form ─────────────────────────────────────────────────────


def test_scalar_override_replaces_the_value():
    derived = _derive(_override("thermal.thermal_conductivity", _pv(15.0, "W/(m*K)")))
    assert derived.thermal.thermal_conductivity.d_value == 15.0
    assert derived.thermal.thermal_conductivity.s_source == "EM lab report 7"


def test_none_override_removes_an_inherited_value():
    derived = _derive(
        _override("thermal.thermal_conductivity", None, "Upstream value is for bar stock")
    )
    assert derived.thermal.thermal_conductivity is None
    assert _base().thermal.thermal_conductivity is not None


def test_row_override_replaces_one_row_and_keeps_the_rest_with_their_sources():
    first = _derive(_override("thermal.temperature_tables.thermal_conductivity", _k_table()))
    better_row = TablePoint(1000.0, _pv(23.5, "W/(m*K)", s_source="EM laser flash run 12"))
    derived = derive_material(
        first,
        s_expected_base_fingerprint=material_fingerprint(first),
        s_id="em_stainless_316_v2",
        overrides=[_override("thermal.temperature_tables.thermal_conductivity", better_row)],
        s_catalog_version="0.1.1",
        s_last_reviewed="2026-10-16",
    )
    table = derived.thermal.table("thermal_conductivity")
    assert table.d_values == (14.0, 19.0, 23.5)
    assert [p.value.s_source for p in table.points] == [
        "EM lab report 7",
        "EM lab report 7",
        "EM laser flash run 12",
    ]
    assert derived.derivation.s_base_id == "em_stainless_316"


def test_row_override_at_a_new_temperature_inserts_it_in_order():
    first = _derive(_override("thermal.temperature_tables.thermal_conductivity", _k_table()))
    derived = derive_material(
        first,
        s_expected_base_fingerprint=material_fingerprint(first),
        s_id="em_stainless_316_v2",
        overrides=[
            _override(
                "thermal.temperature_tables.thermal_conductivity",
                TablePoint(750.0, _pv(22.0, "W/(m*K)")),
            )
        ],
        s_catalog_version="0.1.1",
        s_last_reviewed="2026-10-16",
    )
    table = derived.thermal.table("thermal_conductivity")
    assert table.d_temperatures_C == (25.0, 500.0, 750.0, 1000.0)
    assert table.value_at(750.0) == pytest.approx(22.0, rel=INTERP_REL_TOL)


def test_row_override_on_a_missing_table_starts_one():
    derived = _derive(
        _override("thermal.temperature_tables.emissivity", TablePoint(25.0, _pv(0.3, "")))
    )
    assert derived.thermal.table("emissivity").d_values == (0.3,)


def test_flow_curve_override_lands_on_structural():
    curve = FlowCurve.from_rows(
        [(25.0, 0.0, 290e6)], s_source="EM tensile run 3", s_confidence="measured"
    )
    derived = _derive(_override("structural.flow_curve", curve))
    assert derived.structural.flow_curve is curve
    assert derived.structural.youngs_modulus is _base().structural.youngs_modulus


def test_override_can_create_a_group_the_base_lacks():
    base = MATERIALS["pure_copper"]
    assert base.electromagnetic is not None
    no_thermal = dataclasses.replace(base, s_id="probe_no_thermal", thermal=None)
    derived = derive_material(
        no_thermal,
        s_expected_base_fingerprint=material_fingerprint(no_thermal),
        s_id="em_probe",
        overrides=[_override("thermal.thermal_conductivity", _pv(390.0, "W/(m*K)"))],
        s_catalog_version="0.1.0",
        s_last_reviewed="2026-10-16",
    )
    assert derived.thermal.thermal_conductivity.d_value == 390.0


# ── Every override is validated ────────────────────────────────────────────


def test_overrides_are_validated_by_the_groups_own_rules():
    with pytest.raises(ValueError, match="'thermal.emissivity'.*emissivity must be in"):
        _derive(_override("thermal.emissivity", _pv(1.5, "")))
    with pytest.raises(ValueError, match="wrong units"):
        _derive(_override("thermal.thermal_conductivity", _pv(0.015, "W/(mm*K)")))


def test_derived_material_must_take_a_new_id():
    with pytest.raises(ValueError, match="always gets a new id"):
        _derive(_override("thermal.thermal_conductivity", _pv(15.0, "W/(m*K)")), s_id=_BASE_ID)


def test_a_derivation_with_no_overrides_is_rejected():
    with pytest.raises(ValueError, match="no overrides"):
        _derive()


def test_every_override_needs_a_reason():
    with pytest.raises(ValueError, match="s_reason must say why"):
        FieldOverride("thermal.thermal_conductivity", _pv(15.0, "W/(m*K)"), "  ")


@pytest.mark.parametrize(
    ("s_path", "value", "error", "match"),
    [
        ("optical.refractive_index", None, ValueError, "group must be one of"),
        ("thermal.not_a_slot", None, ValueError, "not an overridable field"),
        ("thermal.temperature_tables", None, ValueError, "not an overridable field"),
        (
            "electromagnetic.bh_curve",
            None,
            ValueError,
            "PropertyValue slots and structural.flow_curve only",
        ),
        (
            "crystal_anisotropy.temperature_tables.c11",
            None,
            ValueError,
            "has no temperature_tables",
        ),
        ("thermal.a.b.c", None, ValueError, "must be '<group>.<slot>'"),
        ("thermal.thermal_conductivity", _k_table(), TypeError, "takes PropertyValue"),
        (
            "thermal.temperature_tables.thermal_conductivity",
            _pv(1.0, "W/(m*K)"),
            TypeError,
            "takes PropertyTable or TablePoint",
        ),
        ("structural.flow_curve", _pv(1.0, "Pa"), TypeError, "takes FlowCurve"),
    ],
    ids=[
        "unknown-group",
        "unknown-slot",
        "bare-tables-field",
        "composite-not-overridable",
        "group-without-tables",
        "too-deep",
        "table-into-scalar",
        "scalar-into-table",
        "scalar-into-flow-curve",
    ],
)
def test_malformed_overrides_are_rejected(s_path, value, error, match):
    with pytest.raises(error, match=match):
        FieldOverride(s_path, value, "reason")


def test_conflicting_overrides_are_rejected():
    s_path = "thermal.temperature_tables.thermal_conductivity"
    row = TablePoint(500.0, _pv(19.5, "W/(m*K)"))
    with pytest.raises(ValueError, match="overridden more than once"):
        _derive(
            _override("thermal.thermal_conductivity", _pv(15.0, "W/(m*K)")),
            _override("thermal.thermal_conductivity", _pv(16.0, "W/(m*K)")),
        )
    with pytest.raises(ValueError, match=r"row at 500.0 C .* more than once"):
        _derive(_override(s_path, row), _override(s_path, row))
    with pytest.raises(ValueError, match="both as a whole table and row by row"):
        _derive(_override(s_path, _k_table()), _override(s_path, row))


def test_crystal_anisotropy_cannot_be_created_from_nothing():
    base = MATERIALS["pure_copper"]
    no_crystal = dataclasses.replace(base, s_id="probe_no_crystal", crystal_anisotropy=None)
    with pytest.raises(ValueError, match="has required fields"):
        derive_material(
            no_crystal,
            s_expected_base_fingerprint=material_fingerprint(no_crystal),
            s_id="em_probe",
            overrides=[_override("crystal_anisotropy.c11", _pv(1.7e11, "Pa"))],
            s_catalog_version="0.1.0",
            s_last_reviewed="2026-10-16",
        )


def test_material_rejects_a_derivation_naming_itself_as_base():
    with pytest.raises(ValueError, match="cannot be derived from itself"):
        dataclasses.replace(
            _base(),
            derivation=Derivation(
                s_base_id=_BASE_ID,
                s_base_catalog_version="1.0.0",
                s_base_fingerprint="0123456789abcdef",
                overrides=(_override("thermal.thermal_conductivity", _pv(15.0, "W/(m*K)")),),
            ),
        )


# ── Derived materials behave like any other ────────────────────────────────


def test_derived_material_is_hashable_and_serializes_with_its_lineage():
    derived = _derive(_override("thermal.temperature_tables.thermal_conductivity", _k_table()))
    assert hash(derived) == hash(
        _derive(_override("thermal.temperature_tables.thermal_conductivity", _k_table()))
    )
    payload = json.loads(json.dumps(dataclasses.asdict(derived)))
    assert payload["derivation"]["s_base_id"] == _BASE_ID
    assert payload["derivation"]["overrides"][0]["s_reason"] == "Measured on our powder lot"


# ── Review-driven guarantees ───────────────────────────────────────────────


def test_override_order_does_not_change_the_result():
    """Cross-field checks see the final group, not a half-applied one."""
    new_yield = _override("structural.yield_stress", _pv(618e6, "Pa"))
    new_uts = _override("structural.ultimate_tensile", _pv(772e6, "Pa"))
    a = _derive(new_yield, new_uts)
    b = _derive(new_uts, new_yield)
    assert a.structural == b.structural
    assert a.structural.yield_stress.d_value == 618e6


def test_a_generator_of_overrides_is_applied_not_silently_dropped():
    derived = _derive(
        *(o for o in [_override("thermal.thermal_conductivity", _pv(99.0, "W/(m*K)"))])
    )
    gen_derived = derive_material(
        _base(),
        s_id="em_gen",
        s_expected_base_fingerprint=material_fingerprint(_base()),
        overrides=(o for o in [_override("thermal.thermal_conductivity", _pv(99.0, "W/(m*K)"))]),
        s_catalog_version="0.1.0",
        s_last_reviewed="2026-10-16",
    )
    assert derived.thermal.thermal_conductivity.d_value == 99.0
    assert gen_derived.thermal.thermal_conductivity.d_value == 99.0
    assert len(gen_derived.derivation.overrides) == 1


@pytest.mark.parametrize(
    ("s_path", "value", "match"),
    [
        ("thermal.glass_transition", None, "nothing to remove at 'thermal.glass_transition'"),
        ("thermal.temperature_tables.emissivity", None, "no such table"),
        (
            "thermal.temperature_tables.thermal_conductivity",
            TableRowRemoval(500.0),
            "has no row at 500.0 C to remove",
        ),
    ],
    ids=["absent-scalar", "absent-table", "absent-row"],
)
def test_removing_something_the_base_lacks_is_rejected(s_path, value, match):
    with pytest.raises(ValueError, match=match):
        _derive(_override(s_path, value))


def test_override_table_key_must_be_tabulable():
    with pytest.raises(ValueError, match="'melting_temp' is not a tabulable property of thermal"):
        FieldOverride("thermal.temperature_tables.melting_temp", None, "reason")


def test_a_row_can_be_removed_and_the_last_removal_drops_the_table():
    first = _derive(_override("thermal.temperature_tables.thermal_conductivity", _k_table()))
    s_path = "thermal.temperature_tables.thermal_conductivity"
    fewer = derive_material(
        first,
        s_id="em_v2",
        s_expected_base_fingerprint=material_fingerprint(first),
        overrides=[_override(s_path, TableRowRemoval(1000.0), "Suspect furnace drift")],
        s_catalog_version="0.1.1",
        s_last_reviewed="2026-10-16",
    )
    assert fewer.thermal.table("thermal_conductivity").d_temperatures_C == (25.0, 500.0)
    gone = derive_material(
        fewer,
        s_id="em_v3",
        s_expected_base_fingerprint=material_fingerprint(fewer),
        overrides=[
            _override(s_path, TableRowRemoval(25.0), "Suspect"),
            _override(s_path, TableRowRemoval(500.0), "Suspect"),
        ],
        s_catalog_version="0.1.2",
        s_last_reviewed="2026-10-16",
    )
    assert "thermal_conductivity" not in gone.thermal.temperature_tables


def test_a_changed_base_is_caught_and_the_new_fingerprint_is_reported():
    s_stale = "0000000000000000"
    with pytest.raises(ValueError, match="changed since this derivation was reviewed") as info:
        derive_material(
            _base(),
            s_id="em_stale",
            s_expected_base_fingerprint=s_stale,
            overrides=[_override("thermal.thermal_conductivity", _pv(15.0, "W/(m*K)"))],
            s_catalog_version="0.1.0",
            s_last_reviewed="2026-10-16",
        )
    assert f"s_expected_base_fingerprint={material_fingerprint(_base())!r}" in str(info.value)


def test_fingerprint_changes_with_any_value_and_is_stable_otherwise():
    base = _base()
    assert material_fingerprint(base) == material_fingerprint(dataclasses.replace(base))
    nudged = dataclasses.replace(
        base,
        thermal=dataclasses.replace(base.thermal, thermal_conductivity=_pv(16.3, "W/(m*K)")),
    )
    assert material_fingerprint(nudged) != material_fingerprint(base)


def test_a_chain_keeps_its_full_lineage():
    v1 = _derive(_override("thermal.thermal_conductivity", _pv(15.0, "W/(m*K)")), s_id="em_a")
    v2 = derive_material(
        v1,
        s_id="em_b",
        s_expected_base_fingerprint=material_fingerprint(v1),
        overrides=[_override("thermal.specific_heat", _pv(480.0, "J/(kg*K)"))],
        s_catalog_version="0.1.1",
        s_last_reviewed="2026-10-16",
    )
    lineage = v2.derivation
    assert lineage.s_base_id == "em_a"
    assert lineage.s_root_base_id == _BASE_ID
    assert lineage.b_is_overridden("thermal.thermal_conductivity")
    assert lineage.s_paths == ("thermal.thermal_conductivity", "thermal.specific_heat")
    assert v2.s_description == v1.s_description  # no stacked "(derived from ...)" suffixes


def test_removals_never_leave_an_empty_group():
    base = MATERIALS["pure_copper"]
    only_em = dataclasses.replace(base, s_id="probe_only_em", thermal=None, structural=None)
    with pytest.raises(ValueError, match="nothing to remove; the thermal of base"):
        derive_material(
            only_em,
            s_id="em_probe",
            s_expected_base_fingerprint=material_fingerprint(only_em),
            overrides=[_override("thermal.thermal_conductivity", None)],
            s_catalog_version="0.1.0",
            s_last_reviewed="2026-10-16",
        )


@pytest.mark.parametrize(
    ("call", "match"),
    [
        (lambda: FieldOverride("thermal.thermal_conductivity", None, None), "s_reason must be str"),
        (lambda: FieldOverride(None, None, "why"), "s_path must be str"),
        (
            lambda: derive_material(
                "stainless_316",
                s_id="em_x",
                s_expected_base_fingerprint="x",
                overrides=[],
                s_catalog_version="0.1.0",
                s_last_reviewed="2026-10-16",
            ),
            "base must be a Material",
        ),
        (
            lambda: derive_material(
                _base(),
                s_id="em_x",
                s_expected_base_fingerprint="x",
                overrides=["thermal.thermal_conductivity"],
                s_catalog_version="0.1.0",
                s_last_reviewed="2026-10-16",
            ),
            "overrides must be FieldOverride",
        ),
    ],
    ids=["reason-none", "path-none", "base-str", "override-str"],
)
def test_wrong_argument_types_raise_type_errors_that_name_the_field(call, match):
    with pytest.raises(TypeError, match=match):
        call()


# ── PR review: fingerprint scope, registered-id collisions ────────────────


def test_fingerprint_ignores_version_and_review_date_bumps():
    base = _base()
    bumped = dataclasses.replace(base, s_catalog_version="9.9.9", s_last_reviewed="2030-01-01")
    assert material_fingerprint(bumped) == material_fingerprint(base)


def test_fingerprint_ignores_absent_fields_so_a_new_optional_field_changes_nothing():
    """A schema release adding an optional field adds a None or empty value to asdict()."""
    from emergent_matter_materials.derivation import _canonical_data

    before = {"structural": {"density": {"d_value": 7990.0}}, "derivation": None}
    after = {
        **before,
        "structural": {**before["structural"], "new_slot": None, "new_tables": {}},
        "new_group": None,
    }
    assert _canonical_data(after) == _canonical_data(before)


def test_fingerprint_moves_when_a_source_citation_changes():
    base = _base()
    k = base.thermal.thermal_conductivity
    recited = dataclasses.replace(
        base,
        thermal=dataclasses.replace(
            base.thermal,
            thermal_conductivity=dataclasses.replace(k, s_source=k.s_source + " rev B"),
        ),
    )
    assert material_fingerprint(recited) != material_fingerprint(base)


def test_derived_id_cannot_take_another_catalog_entrys_id():
    assert "aluminum_6061_t6" in MATERIALS
    with pytest.raises(ValueError, match="'aluminum_6061_t6' is already a catalog entry"):
        _derive(
            _override("thermal.thermal_conductivity", _pv(15.0, "W/(m*K)")),
            s_id="aluminum_6061_t6",
        )
