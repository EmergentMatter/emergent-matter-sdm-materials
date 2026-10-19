"""Shared validation helpers used by group dataclasses' ``__post_init__``.

This module hosts the cross-cutting validators: the things that aren't
specific to one physics group. Per-group invariants (Poisson range,
positive densities, required-field presence) live in each group module's
``__post_init__``.

The validators here are construction-time checks; the catalog-wide
provenance gates (every entry has a source, no unflagged placeholders,
etc.) live in ``tests/test_catalog_provenance_strength.py`` and run at
catalog import time during test collection.
"""

from __future__ import annotations

from collections.abc import Mapping
from collections.abc import Set as AbstractSet
from dataclasses import fields
from typing import TYPE_CHECKING, Any

from emergent_matter_materials.units_map import _PROPERTY_EXPECTED_UNITS

if TYPE_CHECKING:
    from emergent_matter_materials.property_value import PropertyValue


def _validate_group_units(
    instance: Any,
    group_fields: AbstractSet[str],
    *,
    b_optional: bool = False,
) -> None:
    """Validate every PropertyValue field on ``instance`` against the
    canonical units map.

    Args:
        instance: The group dataclass instance (``Structural``,
            ``Electromagnetic``, ``Thermal``, ``ProcessFit``). Iterated
            via ``dataclasses.fields(instance)``.
        group_fields: The subset of field names on ``instance`` that are
            PropertyValue-typed and should be validated. (The class may
            also carry non-PropertyValue fields like ``s_recommended_processes``
            on ``Manufacturing``; those are skipped.)
        b_optional: If True, fields whose value is ``None`` are accepted
            (used by ``Electromagnetic`` and the optional ``Thermal``
            fields). If False, ``None`` raises ``ValueError``: used for
            ``Structural`` where every field is required.

    Raises:
        ValueError: a PropertyValue's ``s_units`` doesn't match the
            canonical units for its slot, OR a required field is None.
    """
    for f in fields(instance):
        if f.name not in group_fields:
            continue

        value = getattr(instance, f.name)
        if value is None:
            if b_optional:
                continue
            raise ValueError(f"{type(instance).__name__}.{f.name} is required (cannot be None)")

        expected_units = _PROPERTY_EXPECTED_UNITS.get(f.name)
        if expected_units is None:
            raise ValueError(
                f"{type(instance).__name__}.{f.name}: no expected-units entry "
                f"in _PROPERTY_EXPECTED_UNITS. Add one to units_map.py."
            )

        if value.s_units != expected_units:
            raise ValueError(
                f"{type(instance).__name__}.{f.name}: wrong units. "
                f"Expected {expected_units!r}, got {value.s_units!r} "
                f"(d_value={value.d_value}, s_source={value.s_source!r})"
            )


#: Properties whose tables may be secant (mean-from-reference) tables: mean
#: CTE, and the mean specific heat some steel datasheets publish. Allowing a
#: reference temperature anywhere else would hide a data-entry mistake.
_SECANT_TABLE_KEYS: frozenset[str] = frozenset(
    {"thermal_expansion", "thermal_expansion_perpendicular", "specific_heat"}
)


def _normalize_temperature_tables(
    instance: Any,
    table_slots: Mapping[str, str],
) -> None:
    """Validate ``instance.temperature_tables`` and freeze it into a ``PropertyTableMap``.

    Runs inside a frozen group's ``__post_init__``, so it rebinds the field
    with ``object.__setattr__``.

    Args:
        instance: The group being constructed.
        table_slots: The group's tabulable properties: table key to the
            scalar slot whose units and range checks the table borrows.
            Usually identical names; a key differs from its slot only
            when the slot name is condition-specific (``"resistivity"``
            borrows ``resistivity_at_20C``).

    Checks, per table:
      - the key is one of the group's tabulable properties (temperatures
        themselves, like ``melting_temp``, can't be tabulated against
        temperature);
      - the value is a ``PropertyTable`` in the slot's canonical units;
      - a reference temperature appears only on a secant-capable property;
      - every point passes the slot's own single-field range checks
        (positive conductivity, emissivity in [0, 1], ...). These are
        reused by building a throwaway group with the point as the scalar.
        Cross-field invariants (yield <= UTS) need two tables at once, so
        the owning group checks those itself.

    Raises:
        TypeError: the field is not a mapping, or a value is not a
            ``PropertyTable``.
        ValueError: any check above fails. The message names the group,
            the key, and the offending temperature.
    """
    # Imported here: property_table is a leaf module, but keeping this
    # import local means validation.py never forms a cycle with it.
    from emergent_matter_materials.property_table import PropertyTable, PropertyTableMap

    s_group = type(instance).__name__
    tables = instance.temperature_tables
    if not isinstance(tables, Mapping):
        raise TypeError(
            f"{s_group}.temperature_tables must be a mapping of slot name to "
            f"PropertyTable, got {type(tables).__name__}"
        )

    for s_key, table in tables.items():
        if s_key not in table_slots:
            raise ValueError(
                f"{s_group}.temperature_tables key {s_key!r} is not a tabulable property of "
                f"{s_group}. Valid keys: {sorted(table_slots)}"
            )
        s_slot = table_slots[s_key]
        if not isinstance(table, PropertyTable):
            raise TypeError(
                f"{s_group}.temperature_tables[{s_key!r}] must be a PropertyTable, "
                f"got {type(table).__name__}"
            )
        s_expected = _PROPERTY_EXPECTED_UNITS[s_slot]
        if table.s_units != s_expected:
            raise ValueError(
                f"{s_group}.temperature_tables[{s_key!r}]: wrong units. "
                f"Expected {s_expected!r}, got {table.s_units!r}"
            )
        if table.b_is_secant and s_key not in _SECANT_TABLE_KEYS:
            raise ValueError(
                f"{s_group}.temperature_tables[{s_key!r}] sets "
                f"d_reference_temperature_C, but only {sorted(_SECANT_TABLE_KEYS)} "
                f"tables can be secant"
            )
        for point in table.points:
            try:
                type(instance)(**{s_slot: point.value})
            except ValueError as err:
                raise ValueError(
                    f"{s_group}.temperature_tables[{s_key!r}] point at "
                    f"{point.d_temperature_C} C: {err}"
                ) from err

    if not isinstance(tables, PropertyTableMap):
        object.__setattr__(instance, "temperature_tables", PropertyTableMap(tables))


def _require_positive(name: str, pv: PropertyValue | None) -> None:
    """Validate that a PropertyValue's numeric value is strictly positive.

    Skips silently if ``pv`` is None (use in optional-field contexts).
    """
    if pv is None:
        return
    if pv.d_value <= 0.0:
        raise ValueError(f"{name} must be positive, got {pv.d_value}")


__all__ = [
    "_normalize_temperature_tables",
    "_require_positive",
    "_validate_group_units",
]
