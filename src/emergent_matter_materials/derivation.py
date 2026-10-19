"""Derived materials: an existing catalog material plus recorded overrides, under a new id.

A downstream catalog often has better or extra data for a material this
catalog already holds: a measured conductivity curve for an alloy whose
open-source entry has only a room-temperature scalar, or a vendor's
lot-specific yield. Copying the whole entry to add one curve duplicates
every other value and silently freezes them at the copy's date.

``derive_material`` builds the new entry from the base instead. The
derived ``Material`` references the base's ``PropertyValue`` objects for
everything not overridden, so nothing is duplicated, and records each
override with a required reason in ``Material.derivation``. A consumer
can ask of any field whether it is inherited or overridden, by what, and
why.

**Always a new id.** A derived material never takes its base's ``s_id``,
or any id already registered in ``MATERIALS``. Two entries under one id
would make which data a consumer gets depend on which package registered
last; a new id makes the choice explicit at every call site.

**Pinned to the base it was reviewed against.** Inherited data flows in
from whatever base is installed, so an upstream revision would otherwise
change a derived entry with nobody looking. Each derivation states the
``material_fingerprint`` of the base it was reviewed against; when the
installed base differs, ``derive_material`` raises and prints the new
fingerprint, like a lockfile. Re-review the overrides against the new
base, then update the expected fingerprint. The fingerprint covers
populated data only: version strings, review dates, and absent fields
are left out, so a release that only bumps bookkeeping or adds an
optional field never forces a re-review.

**What an override can target** (``FieldOverride.s_path``):

- ``"<group>.<slot>"``: a scalar slot, e.g. ``"thermal.thermal_conductivity"``.
  Value: a ``PropertyValue``, or ``None`` to remove an inherited value.
- ``"structural.flow_curve"``: the whole flow curve (``FlowCurve`` or ``None``).
- ``"<group>.temperature_tables.<key>"``: a table, e.g.
  ``"thermal.temperature_tables.thermal_conductivity"``. Value: a
  ``PropertyTable`` replaces the whole table; a ``TablePoint`` replaces
  the row at its temperature, or inserts it in order if no row sits
  there, keeping every other row and its provenance; a
  ``TableRowRemoval`` drops one row; ``None`` removes the table.

A removal must remove something: removing a value, table, or row the
base doesn't have raises, so a typo can't masquerade as an audited
change. All overrides for one group are applied together and validated
once by the group's normal constructor, so the result doesn't depend on
override order and a derived material obeys every rule a catalog entry
does. Overrides apply to ``structural``, ``thermal``, ``electromagnetic``,
and ``crystal_anisotropy``; the first three are created if the base lacks
them and an override adds data, while ``crystal_anisotropy`` has required
fields and can only be overridden where the base has one.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
from collections.abc import Iterable
from dataclasses import dataclass, fields
from typing import TYPE_CHECKING, Any

from emergent_matter_materials.crystal_anisotropy import CrystalAnisotropy
from emergent_matter_materials.electromagnetic import _ELECTROMAGNETIC_TABLE_SLOTS, Electromagnetic
from emergent_matter_materials.flow_curve import FlowCurve
from emergent_matter_materials.property_table import PropertyTable, TablePoint, _check_temperature_C
from emergent_matter_materials.property_value import PropertyValue
from emergent_matter_materials.structural import _STRUCTURAL_TABLE_SLOTS, Structural
from emergent_matter_materials.thermal import _THERMAL_TABLE_SLOTS, Thermal
from emergent_matter_materials.units_map import _PROPERTY_EXPECTED_UNITS

if TYPE_CHECKING:
    from emergent_matter_materials.material import Material

#: Groups an override may target, and the class used to create one the base lacks.
_GROUP_CLASSES: dict[str, type] = {
    "structural": Structural,
    "thermal": Thermal,
    "electromagnetic": Electromagnetic,
    "crystal_anisotropy": CrystalAnisotropy,
}

#: Groups whose fields are all optional, so an override can create them.
_CREATABLE_GROUPS: frozenset[str] = frozenset({"structural", "thermal", "electromagnetic"})

#: Valid temperature-table keys per group.
_TABLE_KEYS: dict[str, frozenset[str]] = {
    "structural": frozenset(_STRUCTURAL_TABLE_SLOTS),
    "thermal": frozenset(_THERMAL_TABLE_SLOTS),
    "electromagnetic": frozenset(_ELECTROMAGNETIC_TABLE_SLOTS),
}

#: Bookkeeping keys the fingerprint ignores: they change on releases and
#: reviews without any data changing.
_FINGERPRINT_IGNORED_KEYS: frozenset[str] = frozenset(
    {"s_catalog_version", "s_last_reviewed", "s_base_catalog_version"}
)

#: Hex digits kept from the SHA-256 fingerprint: short enough to paste,
#: long enough that an accidental collision is not a practical concern.
_N_FINGERPRINT_HEX = 16


@dataclass(frozen=True)
class TableRowRemoval:
    """Override value that drops the row at one temperature from a table."""

    d_temperature_C: float

    def __post_init__(self) -> None:
        _check_temperature_C("TableRowRemoval.d_temperature_C", self.d_temperature_C)


_OverrideValue = PropertyValue | PropertyTable | TablePoint | TableRowRemoval | FlowCurve | None


@dataclass(frozen=True)
class FieldOverride:
    """One recorded change from a base material: where, the new value, and why.

    See the module docstring for the path forms and the value each takes.
    ``s_reason`` is required: an override without a recorded reason is
    indistinguishable from a copy-paste accident.

    A ``TablePoint`` inserted into a secant table (mean CTE) must itself be
    a mean from that table's ``d_reference_temperature_C``; the reference
    is the table's, not the row's.
    """

    s_path: str
    value: _OverrideValue
    s_reason: str

    def __post_init__(self) -> None:
        for s_name in ("s_path", "s_reason"):
            if not isinstance(getattr(self, s_name), str):
                raise TypeError(
                    f"FieldOverride.{s_name} must be str, "
                    f"got {type(getattr(self, s_name)).__name__}"
                )
        if not self.s_reason.strip():
            raise ValueError(f"FieldOverride({self.s_path!r}).s_reason must say why it overrides")

        parts = self.s_path.split(".")
        s_group = parts[0]
        if s_group not in _GROUP_CLASSES:
            raise ValueError(
                f"FieldOverride path {self.s_path!r}: group must be one of {sorted(_GROUP_CLASSES)}"
            )
        group_fields = {f.name for f in fields(_GROUP_CLASSES[s_group])}

        expected: tuple[type, ...]
        if len(parts) == 2:
            s_field = parts[1]
            if s_field == "flow_curve" and s_field in group_fields:
                expected = (FlowCurve,)
            elif s_field in group_fields and s_field in _PROPERTY_EXPECTED_UNITS:
                expected = (PropertyValue,)
            else:
                raise ValueError(
                    f"FieldOverride path {self.s_path!r}: {s_field!r} is not an overridable "
                    f"field of {s_group} (PropertyValue slots and structural.flow_curve only)"
                )
        elif len(parts) == 3 and parts[1] == "temperature_tables":
            if s_group not in _TABLE_KEYS:
                raise ValueError(
                    f"FieldOverride path {self.s_path!r}: {s_group} has no temperature_tables"
                )
            if parts[2] not in _TABLE_KEYS[s_group]:
                raise ValueError(
                    f"FieldOverride path {self.s_path!r}: {parts[2]!r} is not a tabulable "
                    f"property of {s_group}. Valid keys: {sorted(_TABLE_KEYS[s_group])}"
                )
            expected = (PropertyTable, TablePoint, TableRowRemoval)
        else:
            raise ValueError(
                f"FieldOverride path {self.s_path!r} must be '<group>.<slot>' or "
                f"'<group>.temperature_tables.<key>'"
            )

        if self.value is not None and not isinstance(self.value, expected):
            raise TypeError(
                f"FieldOverride path {self.s_path!r} takes "
                f"{' or '.join(t.__name__ for t in expected)} or None, "
                f"got {type(self.value).__name__}"
            )

    @property
    def s_group(self) -> str:
        return self.s_path.split(".")[0]

    @property
    def b_is_row(self) -> bool:
        """True when this override replaces, inserts, or removes a single table row."""
        return isinstance(self.value, (TablePoint, TableRowRemoval))


@dataclass(frozen=True)
class Derivation:
    """How a derived material was built: its base and every override, in order.

    ``base_derivation`` is the base's own derivation when the base was
    itself derived, so a chain keeps its full lineage.
    """

    s_base_id: str
    s_base_catalog_version: str
    # material_fingerprint() of the base the overrides were reviewed against.
    s_base_fingerprint: str
    overrides: tuple[FieldOverride, ...]
    base_derivation: Derivation | None = None

    def __post_init__(self) -> None:
        for s_name in ("s_base_id", "s_base_catalog_version", "s_base_fingerprint"):
            s_val = getattr(self, s_name)
            if not isinstance(s_val, str) or not s_val:
                raise ValueError(f"Derivation.{s_name} must be a non-empty str, got {s_val!r}")
        if not isinstance(self.overrides, tuple) or not all(
            isinstance(o, FieldOverride) for o in self.overrides
        ):
            raise TypeError("Derivation.overrides must be a tuple of FieldOverride")
        if not self.overrides:
            raise ValueError("Derivation.overrides cannot be empty: nothing was derived")
        if self.base_derivation is not None and not isinstance(self.base_derivation, Derivation):
            raise TypeError(
                f"Derivation.base_derivation must be a Derivation or None, "
                f"got {type(self.base_derivation).__name__}"
            )

    @property
    def s_root_base_id(self) -> str:
        """The authored (non-derived) material at the start of the chain."""
        return (
            self.s_base_id if self.base_derivation is None else self.base_derivation.s_root_base_id
        )

    @property
    def s_paths(self) -> tuple[str, ...]:
        """Every overridden path across the chain, each once, oldest first."""
        s_older = () if self.base_derivation is None else self.base_derivation.s_paths
        return tuple(dict.fromkeys((*s_older, *(o.s_path for o in self.overrides))))

    def overrides_for(self, s_path: str) -> tuple[FieldOverride, ...]:
        """Every override at a path across the chain, newest first.

        Several entries mean single table rows were changed, or a later
        derivation overrode an earlier one. An empty tuple means the value
        at that path comes from the root base unchanged.
        """
        own = tuple(o for o in reversed(self.overrides) if o.s_path == s_path)
        older = () if self.base_derivation is None else self.base_derivation.overrides_for(s_path)
        return own + older

    def b_is_overridden(self, s_path: str) -> bool:
        return bool(self.overrides_for(s_path))


def _canonical_data(node: Any) -> Any:
    """``node`` with bookkeeping and absent values stripped, for fingerprinting.

    Drops the version and review-date keys at every depth, and every None
    or empty value, so the fingerprint moves only when populated data
    does. A schema release that adds an optional field, or a catalog
    release that bumps a version or a review date, leaves it unchanged.
    """
    if isinstance(node, dict):
        out = {}
        for s_key, value in node.items():
            if s_key in _FINGERPRINT_IGNORED_KEYS:
                continue
            canonical = _canonical_data(value)
            if canonical is None or canonical == {} or canonical == []:
                continue
            out[s_key] = canonical
        return out
    if isinstance(node, (list, tuple)):
        return [_canonical_data(item) for item in node]
    return node


def material_fingerprint(material: Material) -> str:
    """A short, stable hash of a material's populated data, for pinning a derivation's base.

    Any change to a value, unit, source, condition, confidence, note, or
    table row changes it. Version strings, review dates, and absent
    (None or empty) fields don't, so a release that only bumps
    bookkeeping or adds an optional field never forces a re-review.
    """
    s_canonical = json.dumps(_canonical_data(dataclasses.asdict(material)), sort_keys=True)
    return hashlib.sha256(s_canonical.encode("utf-8")).hexdigest()[:_N_FINGERPRINT_HEX]


def _check_no_conflicts(overrides: tuple[FieldOverride, ...]) -> None:
    """Each target is overridden once: no repeated path, row, or whole-table-plus-row mix."""
    seen_whole: set[str] = set()
    seen_rows: set[tuple[str, float]] = set()
    for o in overrides:
        if isinstance(o.value, (TablePoint, TableRowRemoval)):
            row_key = (o.s_path, float(o.value.d_temperature_C))
            if row_key in seen_rows:
                raise ValueError(
                    f"derive_material: the row at {o.value.d_temperature_C} C of "
                    f"{o.s_path!r} is overridden more than once"
                )
            seen_rows.add(row_key)
        else:
            if o.s_path in seen_whole:
                raise ValueError(f"derive_material: {o.s_path!r} is overridden more than once")
            seen_whole.add(o.s_path)
    for s_path, _d_t in seen_rows:
        if s_path in seen_whole:
            raise ValueError(
                f"derive_material: {s_path!r} is overridden both as a whole table and "
                f"row by row; pass the final table, or rows only"
            )


def _apply_row(table: PropertyTable | None, override: FieldOverride) -> PropertyTable | None:
    """Apply one row override; None when the last row is removed."""
    if isinstance(override.value, TablePoint):
        point = override.value
        if table is None:
            return PropertyTable(points=(point,))
        rows = {p.d_temperature_C: p for p in table.points}
        rows[point.d_temperature_C] = point
        return dataclasses.replace(table, points=tuple(rows[t] for t in sorted(rows)))

    removal = override.value
    if not isinstance(removal, TableRowRemoval):
        raise TypeError(f"_apply_row: unexpected value {type(removal).__name__}")
    d_t = removal.d_temperature_C
    if table is None or d_t not in table.d_temperatures_C:
        raise ValueError(
            f"derive_material: {override.s_path!r} has no row at {d_t} C to remove"
            + ("" if table is None else f"; rows: {list(table.d_temperatures_C)}")
        )
    remaining = tuple(p for p in table.points if p.d_temperature_C != d_t)
    return dataclasses.replace(table, points=remaining) if remaining else None


def _b_is_empty(group: Any) -> bool:
    """True when every field of a group is None or an empty collection."""
    for f in fields(group):
        val = getattr(group, f.name)
        if val is None or (isinstance(val, (tuple, dict)) and not val):
            continue
        return False
    return True


def _apply_group(s_group: str, group: Any, overrides: list[FieldOverride], s_base_id: str) -> Any:
    """Apply every override for one group, then validate the group once."""
    s_where = f"{s_group} of base {s_base_id!r}"
    b_adds_data = any(
        o.value is not None and not isinstance(o.value, TableRowRemoval) for o in overrides
    )
    if group is None:
        if not b_adds_data:
            raise ValueError(f"derive_material: nothing to remove; the {s_where} is absent")
        if s_group not in _CREATABLE_GROUPS:
            raise ValueError(
                f"derive_material: base {s_base_id!r} has no {s_group} group, and {s_group} "
                f"has required fields, so overrides can't create it"
            )
        group = _GROUP_CLASSES[s_group]()

    scalars: dict[str, Any] = {}
    tables: dict[str, PropertyTable] | None = None
    for o in overrides:
        parts = o.s_path.split(".")
        if len(parts) == 2:
            if o.value is None and getattr(group, parts[1]) is None:
                raise ValueError(
                    f"derive_material: nothing to remove at {o.s_path!r}; it is None on the "
                    f"{s_where}"
                )
            scalars[parts[1]] = o.value
            continue
        if tables is None:
            tables = dict(group.temperature_tables)
        s_key = parts[2]
        if o.value is None:
            if s_key not in tables:
                raise ValueError(
                    f"derive_material: nothing to remove at {o.s_path!r}; the {s_where} has "
                    f"no such table"
                )
            del tables[s_key]
        elif isinstance(o.value, PropertyTable):
            tables[s_key] = o.value
        else:
            new_table = _apply_row(tables.get(s_key), o)
            if new_table is None:
                del tables[s_key]
            else:
                tables[s_key] = new_table

    if tables is not None:
        scalars["temperature_tables"] = tables
    try:
        rebuilt = dataclasses.replace(group, **scalars)
    except ValueError as err:
        s_paths = ", ".join(repr(o.s_path) for o in overrides)
        raise ValueError(f"derive_material: overrides {s_paths}: {err}") from err
    return None if _b_is_empty(rebuilt) else rebuilt


def derive_material(
    base: Material,
    *,
    s_id: str,
    overrides: Iterable[FieldOverride],
    s_expected_base_fingerprint: str,
    s_catalog_version: str,
    s_last_reviewed: str,
    s_description: str | None = None,
    s_specification: str | None = None,
) -> Material:
    """Build a new material from ``base`` with recorded, validated overrides.

    Args:
        base: The material to derive from (typically an open-source entry).
        s_id: The new material's id. Must differ from ``base.s_id`` and
            from every id already in ``MATERIALS``.
        overrides: The changes. Each target may appear once (single table
            rows at distinct temperatures count separately). All overrides
            for a group apply together, so their order doesn't matter.
        s_expected_base_fingerprint: ``material_fingerprint(base)`` as it was
            when these overrides were reviewed. A mismatch means the base
            changed upstream; re-review, then update this value.
        s_catalog_version: Catalog version of the derived entry (the
            downstream catalog's, not the base's).
        s_last_reviewed: ISO 8601 date the derivation was last reviewed.
        s_description: Defaults to the base's description, marked as
            derived the first time a chain derives from an authored entry.
        s_specification: Defaults to the base's specification.

    Returns:
        The derived ``Material``. Its ``derivation`` records the base id,
        version, and fingerprint, every override, and, when the base was
        itself derived, the base's derivation.

    Raises:
        TypeError: ``base`` is not a ``Material`` or an override is not a
            ``FieldOverride``.
        ValueError: ``s_id`` equals the base's or any registered catalog
            id, the base's fingerprint
            doesn't match, overrides conflict or remove nothing, an
            override needs a group that can't be created, or a rebuilt
            group fails its own validation.
    """
    from emergent_matter_materials.material import Material

    if not isinstance(base, Material):
        raise TypeError(f"derive_material: base must be a Material, got {type(base).__name__}")
    overrides = tuple(overrides)
    for o in overrides:
        if not isinstance(o, FieldOverride):
            raise TypeError(
                f"derive_material: overrides must be FieldOverride, got {type(o).__name__}"
            )
    if s_id == base.s_id:
        raise ValueError(
            f"derive_material: s_id {s_id!r} equals the base's. A derived material always "
            f"gets a new id so it never shadows its base."
        )
    from emergent_matter_materials.accessors import MATERIALS

    if s_id in MATERIALS:
        raise ValueError(
            f"derive_material: s_id {s_id!r} is already a catalog entry, and registering the "
            f"derived material would overwrite it. Pick an id no entry uses."
        )
    if not overrides:
        raise ValueError(
            "derive_material: no overrides. Use the base material directly instead of a copy."
        )
    s_fingerprint = material_fingerprint(base)
    if s_fingerprint != s_expected_base_fingerprint:
        raise ValueError(
            f"derive_material({s_id!r}): base {base.s_id!r} changed since this derivation was "
            f"reviewed (expected fingerprint {s_expected_base_fingerprint!r}, installed "
            f"{s_fingerprint!r}). Re-review the overrides against the new base, then set "
            f"s_expected_base_fingerprint={s_fingerprint!r}."
        )
    _check_no_conflicts(overrides)

    by_group: dict[str, list[FieldOverride]] = {}
    for o in overrides:
        by_group.setdefault(o.s_group, []).append(o)
    groups = {
        s_group: _apply_group(s_group, getattr(base, s_group), group_overrides, base.s_id)
        for s_group, group_overrides in by_group.items()
    }

    if s_description is None:
        s_description = (
            base.s_description
            if base.derivation is not None
            else f"{base.s_description} (derived from {base.s_id})"
        )
    return dataclasses.replace(
        base,
        s_id=s_id,
        s_description=s_description,
        s_specification=s_specification if s_specification is not None else base.s_specification,
        s_catalog_version=s_catalog_version,
        s_last_reviewed=s_last_reviewed,
        derivation=Derivation(
            s_base_id=base.s_id,
            s_base_catalog_version=base.s_catalog_version,
            s_base_fingerprint=s_fingerprint,
            overrides=overrides,
            base_derivation=base.derivation,
        ),
        **groups,
    )


__all__ = [
    "Derivation",
    "FieldOverride",
    "TableRowRemoval",
    "derive_material",
    "material_fingerprint",
]
