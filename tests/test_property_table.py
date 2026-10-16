"""A PropertyTable is an ascending, single-unit temperature table, sourced per row.

Pins the table's shape invariants, its interpolation contract (linear
inside the range, loud outside it unless clamped), and the read-only,
hashable PropertyTableMap that groups store tables in.
"""

from __future__ import annotations

import pytest

from emergent_matter_materials import PropertyTable, PropertyTableMap, PropertyValue, TablePoint

#: Interpolation is plain linear arithmetic on a handful of floats; the
#: tolerance only absorbs float rounding, not modelling error.
INTERP_REL_TOL = 1e-12


def _pv(
    d_value: float, *, s_units: str = "W/(m*K)", s_source: str = "Test source A"
) -> PropertyValue:
    return PropertyValue(
        d_value=d_value, s_units=s_units, s_source=s_source, s_confidence="datasheet"
    )


def _table(*rows: tuple[float, float]) -> PropertyTable:
    return PropertyTable.from_rows(
        rows, s_units="W/(m*K)", s_source="Test source A", s_confidence="datasheet"
    )


def test_from_rows_stamps_the_shared_provenance_on_every_point():
    table = PropertyTable.from_rows(
        [(25.0, 10.0), (500.0, 16.0)],
        s_units="W/(m*K)",
        s_source="Vendor TDS rev B",
        s_confidence="datasheet",
        s_condition="wrought, annealed",
        s_point_notes="laser flash",
    )
    assert table.d_temperatures_C == (25.0, 500.0)
    assert table.d_values == (10.0, 16.0)
    for point in table.points:
        assert point.value.s_source == "Vendor TDS rev B"
        assert point.value.s_condition == "wrought, annealed"
        assert point.value.s_confidence == "datasheet"
        assert point.value.s_notes == "laser flash"


def test_each_point_can_cite_a_different_source():
    """The reason provenance is per point: one curve, several tests."""
    table = PropertyTable(
        points=(
            TablePoint(25.0, _pv(10.0, s_source="Room-temperature tensile lab")),
            TablePoint(1000.0, _pv(25.0, s_source="High-temperature laser flash lab")),
        )
    )
    assert [p.value.s_source for p in table.points] == [
        "Room-temperature tensile lab",
        "High-temperature laser flash lab",
    ]


def test_single_row_table_is_allowed_and_answers_at_its_temperature():
    table = _table((25.0, 0.7))
    assert table.value_at(25.0) == 0.7


@pytest.mark.parametrize(
    ("points", "match"),
    [
        ((), "at least one TablePoint"),
        (
            (TablePoint(100.0, _pv(1.0)), TablePoint(25.0, _pv(2.0))),
            "strictly ascending",
        ),
        (
            (TablePoint(25.0, _pv(1.0)), TablePoint(25.0, _pv(2.0))),
            "strictly ascending",
        ),
        (
            (TablePoint(25.0, _pv(1.0)), TablePoint(100.0, _pv(2.0, s_units="J/(kg*K)"))),
            "share one unit",
        ),
    ],
    ids=["empty", "descending", "duplicate-temperature", "mixed-units"],
)
def test_malformed_tables_are_rejected(points, match):
    with pytest.raises(ValueError, match=match):
        PropertyTable(points=points)


def test_points_must_be_a_tuple_not_a_list():
    with pytest.raises(TypeError, match="must be a tuple"):
        PropertyTable(points=[TablePoint(25.0, _pv(1.0))])  # type: ignore[arg-type]


def test_point_below_absolute_zero_is_rejected():
    with pytest.raises(ValueError, match="below absolute zero"):
        TablePoint(-300.0, _pv(1.0))


def test_point_value_must_be_a_property_value():
    with pytest.raises(TypeError, match="must be a PropertyValue"):
        TablePoint(25.0, 1.0)  # type: ignore[arg-type]


def test_value_at_returns_exact_rows_and_interpolates_between_them():
    table = _table((0.0, 10.0), (100.0, 20.0), (300.0, 60.0))
    assert table.value_at(100.0) == 20.0
    assert table.value_at(50.0) == pytest.approx(15.0, rel=INTERP_REL_TOL)
    assert table.value_at(200.0) == pytest.approx(40.0, rel=INTERP_REL_TOL)


def test_value_at_outside_the_range_raises_unless_clamped():
    table = _table((25.0, 10.0), (500.0, 16.0))
    with pytest.raises(ValueError, match=r"outside the tabulated range \[25.0, 500.0\] C"):
        table.value_at(600.0)
    with pytest.raises(ValueError, match="outside the tabulated range"):
        table.value_at(0.0)
    assert table.value_at(600.0, b_clamp=True) == 16.0
    assert table.value_at(0.0, b_clamp=True) == 10.0


def test_reference_temperature_marks_a_secant_table():
    table = PropertyTable.from_rows(
        [(100.0, 1.1e-5)],
        s_units="1/K",
        s_source="Test source A",
        s_confidence="datasheet",
        d_reference_temperature_C=20.0,
    )
    assert table.b_is_secant
    assert not _table((25.0, 1.0)).b_is_secant


def test_table_map_copies_its_input_so_later_mutation_cannot_reach_it():
    source = {"thermal_conductivity": _table((25.0, 10.0))}
    tables = PropertyTableMap(source)
    source["specific_heat"] = _table((25.0, 500.0))
    assert list(tables) == ["thermal_conductivity"]


def test_table_map_is_read_only():
    tables = PropertyTableMap({"thermal_conductivity": _table((25.0, 10.0))})
    with pytest.raises(TypeError):
        tables["specific_heat"] = _table((25.0, 500.0))  # type: ignore[index]


def test_table_map_is_hashable_and_compares_by_content():
    a = PropertyTableMap({"thermal_conductivity": _table((25.0, 10.0))})
    b = PropertyTableMap({"thermal_conductivity": _table((25.0, 10.0))})
    assert a == b
    assert hash(a) == hash(b)
    assert a == {"thermal_conductivity": _table((25.0, 10.0))}


@pytest.mark.parametrize(
    "d_bad", [float("nan"), float("inf"), float("-inf")], ids=["nan", "inf", "-inf"]
)
def test_non_finite_temperatures_are_rejected(d_bad):
    with pytest.raises(ValueError, match="must be finite"):
        TablePoint(d_bad, _pv(1.0))


@pytest.mark.parametrize("d_bad", [float("nan"), float("inf")], ids=["nan", "inf"])
def test_non_finite_values_are_rejected(d_bad):
    with pytest.raises(ValueError, match="value.d_value must be finite"):
        TablePoint(25.0, _pv(d_bad))


@pytest.mark.parametrize(
    ("d_reference", "error"),
    [(float("nan"), ValueError), (True, TypeError), ("20", TypeError)],
    ids=["nan", "bool", "str"],
)
def test_reference_temperature_must_be_a_finite_number(d_reference, error):
    with pytest.raises(error, match="d_reference_temperature_C"):
        PropertyTable(points=(TablePoint(100.0, _pv(1.0)),), d_reference_temperature_C=d_reference)


def test_non_finite_query_raises_even_when_clamping():
    two_rows = _table((25.0, 10.0), (500.0, 16.0))
    one_row = _table((25.0, 0.7))
    for table in (two_rows, one_row):
        for b_clamp in (False, True):
            with pytest.raises(ValueError, match="query temperature must be finite"):
                table.value_at(float("nan"), b_clamp=b_clamp)


def test_single_row_table_raises_off_its_temperature_unless_clamped():
    table = _table((25.0, 0.7))
    with pytest.raises(ValueError, match="outside the tabulated range"):
        table.value_at(26.0)
    assert table.value_at(1000.0, b_clamp=True) == 0.7


def test_bracket_at_returns_the_rows_an_interpolated_value_came_from():
    table = PropertyTable(
        points=(
            TablePoint(25.0, _pv(10.0, s_source="Lab A")),
            TablePoint(500.0, _pv(16.0, s_source="Lab B")),
        )
    )
    lo, hi = table.bracket_at(200.0)
    assert (lo.value.s_source, hi.value.s_source) == ("Lab A", "Lab B")
    on_row = table.bracket_at(500.0)
    assert on_row[0] is on_row[1]


def test_table_map_survives_pickle_and_deepcopy():
    import copy
    import pickle

    tables = PropertyTableMap({"thermal_conductivity": _table((25.0, 10.0))})
    for clone in (pickle.loads(pickle.dumps(tables)), copy.deepcopy(tables), copy.copy(tables)):
        assert isinstance(clone, PropertyTableMap)
        assert clone == tables


def test_table_map_blocks_every_mutator():
    tables = PropertyTableMap({"thermal_conductivity": _table((25.0, 10.0))})
    for mutate in (
        lambda: tables.update({}),
        lambda: tables.pop("thermal_conductivity"),
        lambda: tables.setdefault("x", None),
        tables.clear,
        tables.popitem,
    ):
        with pytest.raises(TypeError, match="read-only"):
            mutate()
    assert list(tables) == ["thermal_conductivity"]
