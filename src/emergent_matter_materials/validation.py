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

from dataclasses import fields
from typing import TYPE_CHECKING, Any

from emergent_matter_materials.units_map import _PROPERTY_EXPECTED_UNITS

if TYPE_CHECKING:
    from emergent_matter_materials.property_value import PropertyValue


def _validate_group_units(
    instance: Any,
    group_fields: set[str],
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


def _require_positive(name: str, pv: PropertyValue | None) -> None:
    """Validate that a PropertyValue's numeric value is strictly positive.

    Skips silently if ``pv`` is None (use in optional-field contexts).
    """
    if pv is None:
        return
    if pv.d_value <= 0.0:
        raise ValueError(f"{name} must be positive, got {pv.d_value}")


__all__ = [
    "_require_positive",
    "_validate_group_units",
]
