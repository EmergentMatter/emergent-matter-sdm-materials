"""PropertyTable: a temperature-dependent property with per-point provenance.

A scalar ``PropertyValue`` answers "what is this property at one stated
condition". Thermal and thermo-mechanical solvers (additive-manufacturing
process simulation, welding, heat treatment) need the property across a
temperature range instead: conductivity from room temperature to the
melt, modulus collapsing above 800 C, and so on.

``PropertyTable`` stores that range as ascending rows. Each row is a
``TablePoint``: an independent-variable temperature plus a full
``PropertyValue``. Provenance is per point, not per table, because the
rows of one published curve often come from different tests. A
room-temperature modulus from a tensile test and a 1000 C modulus from
a dynamic resonance test can sit in the same table, each with its own
source, condition, and confidence. Reusing ``PropertyValue`` for the row
also means every existing provenance rule (non-empty source, confidence
enum, placeholder notes) applies to every point with no new code.

Tables attach to a group through its ``temperature_tables`` mapping,
keyed by the property they extend (``"thermal_conductivity"``,
``"youngs_modulus"``). The group validates the key, the units, and the
property's physical range on every point. The scalar slot stays the
headline value and is independent of the table: a material may have a
table without a scalar, a scalar without a table, or both.

**Secant quantities.** Some published curves are mean values from a
reference temperature, not instantaneous ones. The common case is the
mean coefficient of thermal expansion (CTE), where the row at T holds
``(L(T) - L(T_ref)) / (L(T_ref) * (T - T_ref))``. Such a table sets
``d_reference_temperature_C``; ``None`` means every value is an
instantaneous (point) value. The owning group decides which properties
may be secant.

Temperatures are in degrees C, matching the catalog convention for
temperatures (see ``units_map``). Every temperature and value must be
finite: a NaN compares false against everything, so it would slip past
every ordering and range check.
"""

from __future__ import annotations

import math
from bisect import bisect_left
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from functools import cached_property
from typing import Any, NoReturn

from emergent_matter_materials.property_value import ConfidenceLevel, PropertyValue

#: Absolute zero in C. A table row below this is a units error (K entered as C
#: with the wrong sign, or a typo), not physics.
_ABSOLUTE_ZERO_C: float = -273.15


def _check_temperature_C(s_owner: str, d_temperature_C: object) -> None:
    """Shared check for every temperature a table or curve stores: a finite number >= 0 K."""
    if isinstance(d_temperature_C, bool) or not isinstance(d_temperature_C, (int, float)):
        raise TypeError(
            f"{s_owner} must be float or int, "
            f"got {type(d_temperature_C).__name__}: {d_temperature_C!r}"
        )
    if not math.isfinite(d_temperature_C):
        raise ValueError(f"{s_owner} must be finite, got {d_temperature_C}")
    if d_temperature_C < _ABSOLUTE_ZERO_C:
        raise ValueError(
            f"{s_owner} = {d_temperature_C} C is below absolute zero ({_ABSOLUTE_ZERO_C} C)"
        )


@dataclass(frozen=True)
class TablePoint:
    """One row of a ``PropertyTable``: a temperature and the value there.

    ``value`` is a full ``PropertyValue``, so the row carries its own
    source, condition, confidence, and notes.
    """

    d_temperature_C: float
    value: PropertyValue

    def __post_init__(self) -> None:
        _check_temperature_C("TablePoint.d_temperature_C", self.d_temperature_C)
        if not isinstance(self.value, PropertyValue):
            raise TypeError(
                f"TablePoint.value must be a PropertyValue, got {type(self.value).__name__}"
            )
        if not math.isfinite(self.value.d_value):
            raise ValueError(
                f"TablePoint.value.d_value must be finite, got {self.value.d_value} "
                f"at {self.d_temperature_C} C"
            )


@dataclass(frozen=True)
class PropertyTable:
    """A property tabulated against temperature, ascending, one unit throughout.

    Validation (``__post_init__``):
      1. At least one point. A single-row table is legal: some sources
         publish a property at one temperature but in tabular form, and
         keeping it as a table preserves that row's temperature.
      2. Temperatures strictly ascending (no duplicates).
      3. Every point uses the same ``s_units``. The owning group checks
         that unit against the slot's canonical unit.
      4. ``d_reference_temperature_C``, when set, is a finite temperature.

    Property-specific checks (emissivity in [0, 1], positive conductivity,
    which properties may be secant) run in the owning group, which knows
    which property the table extends.
    """

    points: tuple[TablePoint, ...]
    # Non-None marks a secant (mean) table measured from this temperature,
    # e.g. mean CTE. None means every value is an instantaneous value.
    d_reference_temperature_C: float | None = None
    # About the table as a whole; each row's notes live on its PropertyValue.
    s_table_notes: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.points, tuple):
            raise TypeError(
                f"PropertyTable.points must be a tuple of TablePoint, "
                f"got {type(self.points).__name__}"
            )
        if not self.points:
            raise ValueError("PropertyTable.points must contain at least one TablePoint")
        for point in self.points:
            if not isinstance(point, TablePoint):
                raise TypeError(
                    f"PropertyTable.points entries must be TablePoint, got {type(point).__name__}"
                )

        for p0, p1 in zip(self.points, self.points[1:], strict=False):
            if p1.d_temperature_C <= p0.d_temperature_C:
                raise ValueError(
                    f"PropertyTable temperatures must be strictly ascending: "
                    f"{p0.d_temperature_C} C is followed by {p1.d_temperature_C} C"
                )

        s_units = self.points[0].value.s_units
        for point in self.points[1:]:
            if point.value.s_units != s_units:
                raise ValueError(
                    f"PropertyTable points must share one unit: the point at "
                    f"{self.points[0].d_temperature_C} C uses {s_units!r}, the point at "
                    f"{point.d_temperature_C} C uses {point.value.s_units!r}"
                )

        if self.d_reference_temperature_C is not None:
            _check_temperature_C(
                "PropertyTable.d_reference_temperature_C", self.d_reference_temperature_C
            )

    @classmethod
    def from_rows(
        cls,
        rows: Sequence[tuple[float, float]],
        *,
        s_units: str,
        s_source: str,
        s_confidence: ConfidenceLevel,
        s_condition: str = "",
        s_point_notes: str = "",
        d_reference_temperature_C: float | None = None,
        s_table_notes: str = "",
    ) -> PropertyTable:
        """Build a table whose rows share one provenance.

        Convenience for the common case of a whole curve from one source.
        Each row still becomes its own ``PropertyValue``, so a later edit
        can replace a single row with a better-sourced one. When rows come
        from different sources, build ``TablePoint`` objects directly.

        Args:
            rows: ``(temperature_C, value)`` pairs, ascending by temperature.
            s_units: Canonical units of the property this table extends.
            s_source: Citation stamped on every row.
            s_confidence: Confidence stamped on every row.
            s_condition: Condition stamped on every row. Each row's
                temperature is stored in ``d_temperature_C``, so this holds
                everything else (product form, test method, heat treatment).
            s_point_notes: Notes stamped on every row's ``PropertyValue``.
            d_reference_temperature_C: See the class docstring.
            s_table_notes: Notes about the table as a whole.

        Returns:
            A validated ``PropertyTable``.
        """
        return cls(
            points=tuple(
                TablePoint(
                    d_temperature_C=d_temperature_C,
                    value=PropertyValue(
                        d_value=d_value,
                        s_units=s_units,
                        s_source=s_source,
                        s_condition=s_condition,
                        s_confidence=s_confidence,
                        s_notes=s_point_notes,
                    ),
                )
                for d_temperature_C, d_value in rows
            ),
            d_reference_temperature_C=d_reference_temperature_C,
            s_table_notes=s_table_notes,
        )

    @property
    def s_units(self) -> str:
        """The unit shared by every point."""
        return self.points[0].value.s_units

    # cached_property writes straight into the instance __dict__, which a
    # frozen dataclass allows; the cache is derived, so eq and hash ignore it.
    @cached_property
    def d_temperatures_C(self) -> tuple[float, ...]:
        return tuple(float(p.d_temperature_C) for p in self.points)

    @cached_property
    def d_values(self) -> tuple[float, ...]:
        return tuple(float(p.value.d_value) for p in self.points)

    @property
    def b_is_secant(self) -> bool:
        """True when values are means from ``d_reference_temperature_C``."""
        return self.d_reference_temperature_C is not None

    def bracket_at(self, d_temperature_C: float) -> tuple[TablePoint, TablePoint]:
        """The two rows a query temperature falls between, for provenance of an interpolated value.

        A query exactly on a row returns that row twice. A solver that
        records where a number came from cites both rows' sources.

        Raises:
            ValueError: The temperature is non-finite or outside the
                tabulated range.
        """
        n_lo, n_hi = self._bracket_indices(d_temperature_C)
        return self.points[n_lo], self.points[n_hi]

    def value_at(self, d_temperature_C: float, *, b_clamp: bool = False) -> float:
        """Linearly interpolate the table at a temperature.

        Outside the tabulated range this raises by default: silently
        holding the end value would hide that the source never covered
        the temperature. Pass ``b_clamp=True`` to hold the nearest end
        value explicitly. (``jnp.interp`` on the pytree arrays clamps
        silently, so a traced solver should range-check itself.)

        Args:
            d_temperature_C: Query temperature in C.
            b_clamp: Hold the end value outside the tabulated range
                instead of raising.

        Returns:
            The interpolated value, in ``s_units``.

        Raises:
            ValueError: The temperature is non-finite, or outside the
                tabulated range and ``b_clamp`` is False.
        """
        d_temps = self.d_temperatures_C
        d_vals = self.d_values
        if b_clamp and math.isfinite(d_temperature_C):
            if d_temperature_C < d_temps[0]:
                return d_vals[0]
            if d_temperature_C > d_temps[-1]:
                return d_vals[-1]
        n_lo, n_hi = self._bracket_indices(d_temperature_C)
        if n_lo == n_hi:
            return d_vals[n_lo]
        d_frac = (d_temperature_C - d_temps[n_lo]) / (d_temps[n_hi] - d_temps[n_lo])
        return d_vals[n_lo] + d_frac * (d_vals[n_hi] - d_vals[n_lo])

    def _bracket_indices(self, d_temperature_C: float) -> tuple[int, int]:
        """Indices of the rows around an in-range query; equal when it sits on a row."""
        if not math.isfinite(d_temperature_C):
            raise ValueError(
                f"PropertyTable query temperature must be finite, got {d_temperature_C}"
            )
        d_temps = self.d_temperatures_C
        d_lo, d_hi = d_temps[0], d_temps[-1]
        if d_temperature_C < d_lo or d_temperature_C > d_hi:
            raise ValueError(
                f"PropertyTable query at {d_temperature_C} C is outside the tabulated "
                f"range [{d_lo}, {d_hi}] C; value_at(..., b_clamp=True) holds the end value"
            )
        # In range, so bisect_left lands on the first row >= the query. That
        # row is either the query itself or the upper neighbour of a row
        # strictly below it, so n_hi - 1 is never negative here.
        n_hi = bisect_left(d_temps, d_temperature_C)
        if d_temps[n_hi] == d_temperature_C:
            return n_hi, n_hi
        return n_hi - 1, n_hi


class PropertyTableMap(dict[str, PropertyTable]):
    """Read-only, hashable ``dict`` from a property name to its ``PropertyTable``.

    Groups store ``temperature_tables`` as this type. A plain ``dict``
    field would make the frozen group dataclasses unhashable, and with
    them every ``Material`` that has a populated group, which would break
    any consumer caching on materials. It subclasses ``dict`` (rather than
    only implementing ``Mapping``) so ``dataclasses.asdict`` recurses into
    it and ``json.dumps(asdict(material))`` keeps working.

    Groups accept any mapping at construction and convert it, so callers
    can pass a plain ``dict`` literal and ``dataclasses.replace`` keeps
    working. The constructor copies its input, so a caller mutating the
    dict it passed in can't reach into a frozen group.
    """

    def __init__(
        self,
        tables: Mapping[str, PropertyTable] | Iterable[tuple[str, PropertyTable]] = (),
    ) -> None:
        # dict.__init__ fills storage directly, bypassing the blocked __setitem__.
        super().__init__(tables)

    def _readonly(self, *_args: Any, **_kwargs: Any) -> NoReturn:
        raise TypeError("PropertyTableMap is read-only; build a new one instead")

    __setitem__ = _readonly
    __delitem__ = _readonly
    __ior__ = _readonly
    clear = _readonly
    pop = _readonly
    popitem = _readonly
    setdefault = _readonly
    update = _readonly

    def __hash__(self) -> int:  # type: ignore[override]
        return hash(frozenset(self.items()))

    def __reduce__(self) -> tuple[type[PropertyTableMap], tuple[dict[str, PropertyTable]]]:
        # The default dict reduce rebuilds by calling __setitem__, which is
        # blocked; rebuild through the constructor instead (pickle, copy).
        return (type(self), (dict(self),))

    def __repr__(self) -> str:
        return f"PropertyTableMap({dict(self)!r})"


def _require_table(group: Any, s_field_name: str) -> PropertyTable:
    """Return ``group.temperature_tables[s_field_name]`` or raise a clear error.

    ``group`` is any group dataclass with a ``temperature_tables`` field;
    typed ``Any`` to avoid importing the groups (they import this module).
    """
    tables: Mapping[str, PropertyTable] = group.temperature_tables
    if s_field_name not in tables:
        raise ValueError(
            f"{type(group).__name__}.temperature_tables has no table for "
            f"{s_field_name!r}; tables present: {sorted(tables)}"
        )
    return tables[s_field_name]


__all__ = [
    "PropertyTable",
    "PropertyTableMap",
    "TablePoint",
]
