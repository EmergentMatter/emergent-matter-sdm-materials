"""FlowCurve: temperature-dependent plastic flow stress with per-point provenance.

Elastic-plastic solvers describe hardening as flow stress against
equivalent plastic strain, one isotherm per temperature (and, for
rate-dependent data, per strain rate). Process simulation for metal
additive manufacturing reads exactly this table: at each temperature,
the stress at which the material flows after a given amount of plastic
strain.

A ``FlowCurve`` is that table flattened into ``FlowPoint`` rows of
(temperature, optional strain rate, plastic strain, stress). Each stress
is a full ``PropertyValue``, so every point carries its own source,
condition, and confidence. That matters more here than for a
one-variable table: a hardening curve is often stitched from
room-temperature tensile data and separate elevated-temperature tests.

Conventions:
  - Strain is equivalent *plastic* strain (total strain minus elastic
    strain), dimensionless, >= 0. A point at plastic strain 0 is the
    initial yield of that isotherm. A point at 0.002 is the 0.2% offset
    yield.
  - Whether stress and strain are true (Cauchy stress, logarithmic
    strain) or engineering values is stated by
    ``FlowCurve.s_stress_strain_measure``. Solvers almost always want
    true values; mixing the two is the classic data-entry error, so a
    source that doesn't say is recorded as ``"unspecified"`` rather than
    guessed.
  - An isotherm need not start at plastic strain 0. Some sources start
    at a few percent strain; the curve keeps what the source published
    rather than inventing a yield point. A solver that needs a zero-strain
    start must check ``isotherm(...)[0].d_plastic_strain`` itself.
  - Strain rate is optional, but a curve is either rate-independent (no
    point has a rate) or fully rate-dependent (every point has one).
  - Temperatures are in C, stress in Pa, strain rate in 1/s.

``FlowCurve`` attaches to ``Structural.flow_curve``. It does not replace
``Structural.yield_stress``, which stays the headline 0.2% offset value
at its stated condition.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal, get_args

from emergent_matter_materials.property_table import _check_temperature_C
from emergent_matter_materials.property_value import ConfidenceLevel, PropertyValue
from emergent_matter_materials.units_map import expected_units_for

StressStrainMeasure = Literal["true", "engineering", "unspecified"]

#: Runtime counterpart of `StressStrainMeasure` (STYLE.md: derive with get_args()).
_VALID_STRESS_STRAIN_MEASURES: frozenset[str] = frozenset(get_args(StressStrainMeasure))


@dataclass(frozen=True)
class FlowPoint:
    """One row of a ``FlowCurve``: flow stress at a temperature, strain rate, and plastic strain."""

    d_temperature_C: float
    d_plastic_strain: float
    stress: PropertyValue
    # 1/s. None for rate-independent data.
    d_strain_rate_per_s: float | None = None

    def __post_init__(self) -> None:
        _check_temperature_C("FlowPoint.d_temperature_C", self.d_temperature_C)
        s_at = f"at {self.d_temperature_C} C"
        if isinstance(self.d_plastic_strain, bool) or not isinstance(
            self.d_plastic_strain, (int, float)
        ):
            raise TypeError(
                f"FlowPoint.d_plastic_strain must be float or int, "
                f"got {type(self.d_plastic_strain).__name__}: {self.d_plastic_strain!r}"
            )
        if not math.isfinite(self.d_plastic_strain) or self.d_plastic_strain < 0.0:
            raise ValueError(
                f"FlowPoint.d_plastic_strain must be finite and >= 0, "
                f"got {self.d_plastic_strain} {s_at}"
            )
        if self.d_strain_rate_per_s is not None and (
            isinstance(self.d_strain_rate_per_s, bool)
            or not isinstance(self.d_strain_rate_per_s, (int, float))
            or not math.isfinite(self.d_strain_rate_per_s)
            or self.d_strain_rate_per_s <= 0.0
        ):
            raise ValueError(
                f"FlowPoint.d_strain_rate_per_s must be a finite positive number or None, "
                f"got {self.d_strain_rate_per_s!r} {s_at}"
            )
        if not isinstance(self.stress, PropertyValue):
            raise TypeError(
                f"FlowPoint.stress must be a PropertyValue, got {type(self.stress).__name__}"
            )
        s_expected = expected_units_for("flow_stress")
        if self.stress.s_units != s_expected:
            raise ValueError(
                f"FlowPoint.stress: wrong units. Expected {s_expected!r}, got "
                f"{self.stress.s_units!r} {s_at}, plastic strain {self.d_plastic_strain}"
            )
        if not math.isfinite(self.stress.d_value) or self.stress.d_value <= 0.0:
            raise ValueError(
                f"FlowPoint.stress must be finite and positive, got {self.stress.d_value} Pa "
                f"{s_at}, plastic strain {self.d_plastic_strain}"
            )

    @property
    def _order_key(self) -> tuple[float, float]:
        """(temperature, strain rate): the isotherm a point belongs to."""
        d_rate = -1.0 if self.d_strain_rate_per_s is None else self.d_strain_rate_per_s
        return (self.d_temperature_C, d_rate)


@dataclass(frozen=True)
class FlowCurve:
    """Flow stress against plastic strain, one isotherm per temperature (and strain rate).

    Validation (``__post_init__``):
      1. At least one point.
      2. Either no point has a strain rate or every point does.
      3. Points ordered by temperature, then strain rate, then plastic
         strain: temperature never decreases, rate never decreases within
         a temperature, and plastic strain strictly increases within one
         (temperature, rate) isotherm. This keeps each isotherm contiguous
         and rules out duplicate points.
      4. ``s_stress_strain_measure`` is one of ``StressStrainMeasure``.
    """

    points: tuple[FlowPoint, ...]
    s_stress_strain_measure: StressStrainMeasure = "unspecified"
    s_curve_notes: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.points, tuple):
            raise TypeError(
                f"FlowCurve.points must be a tuple of FlowPoint, got {type(self.points).__name__}"
            )
        if not self.points:
            raise ValueError("FlowCurve.points must contain at least one FlowPoint")
        for point in self.points:
            if not isinstance(point, FlowPoint):
                raise TypeError(
                    f"FlowCurve.points entries must be FlowPoint, got {type(point).__name__}"
                )
        if self.s_stress_strain_measure not in _VALID_STRESS_STRAIN_MEASURES:
            raise ValueError(
                f"FlowCurve.s_stress_strain_measure must be one of "
                f"{sorted(_VALID_STRESS_STRAIN_MEASURES)}, got {self.s_stress_strain_measure!r}"
            )

        n_with_rate = sum(p.d_strain_rate_per_s is not None for p in self.points)
        if n_with_rate not in (0, len(self.points)):
            raise ValueError(
                "FlowCurve strain rate must be set on every point or on none: "
                f"{n_with_rate} of {len(self.points)} points have one"
            )

        for p0, p1 in zip(self.points, self.points[1:], strict=False):
            if p1._order_key < p0._order_key:
                raise ValueError(
                    f"FlowCurve points must be ordered by temperature, then strain rate: "
                    f"{p0.d_temperature_C} C (rate {p0.d_strain_rate_per_s}) is followed by "
                    f"{p1.d_temperature_C} C (rate {p1.d_strain_rate_per_s})"
                )
            if p1._order_key == p0._order_key and p1.d_plastic_strain <= p0.d_plastic_strain:
                raise ValueError(
                    f"FlowCurve plastic strain must strictly increase within an isotherm: "
                    f"at {p0.d_temperature_C} C, {p0.d_plastic_strain} is followed by "
                    f"{p1.d_plastic_strain}"
                )

    @classmethod
    def from_rows(
        cls,
        rows: Sequence[tuple[float, float, float]],
        *,
        s_source: str,
        s_confidence: ConfidenceLevel,
        s_condition: str = "",
        s_point_notes: str = "",
        s_stress_strain_measure: StressStrainMeasure = "unspecified",
        s_curve_notes: str = "",
    ) -> FlowCurve:
        """Build a rate-independent curve whose points share one provenance.

        Rate-dependent curves, or points from different sources, are built
        from ``FlowPoint`` objects directly.

        Args:
            rows: ``(temperature_C, plastic_strain, stress_Pa)`` triples,
                ordered by temperature, then plastic strain.
            s_source: Citation stamped on every point.
            s_confidence: Confidence stamped on every point.
            s_condition: Condition stamped on every point (temperature and
                strain live in the point itself).
            s_point_notes: Notes stamped on every point's ``PropertyValue``.
            s_stress_strain_measure: True, engineering, or unspecified.
            s_curve_notes: Notes about the curve as a whole.

        Returns:
            A validated ``FlowCurve``.
        """
        s_units = expected_units_for("flow_stress")
        return cls(
            points=tuple(
                FlowPoint(
                    d_temperature_C=d_temperature_C,
                    d_plastic_strain=d_plastic_strain,
                    stress=PropertyValue(
                        d_value=d_stress,
                        s_units=s_units,
                        s_source=s_source,
                        s_condition=s_condition,
                        s_confidence=s_confidence,
                        s_notes=s_point_notes,
                    ),
                )
                for d_temperature_C, d_plastic_strain, d_stress in rows
            ),
            s_stress_strain_measure=s_stress_strain_measure,
            s_curve_notes=s_curve_notes,
        )

    @property
    def b_is_rate_dependent(self) -> bool:
        return self.points[0].d_strain_rate_per_s is not None

    @property
    def d_temperatures_C(self) -> tuple[float, ...]:
        """The distinct isotherm temperatures, ascending."""
        return tuple(sorted({float(p.d_temperature_C) for p in self.points}))

    @property
    def d_strain_rates_per_s(self) -> tuple[float, ...]:
        """The distinct strain rates, ascending; empty for a rate-independent curve."""
        return tuple(
            sorted(
                {p.d_strain_rate_per_s for p in self.points if p.d_strain_rate_per_s is not None}
            )
        )

    def isotherm(
        self, d_temperature_C: float, *, d_strain_rate_per_s: float | None = None
    ) -> tuple[FlowPoint, ...]:
        """The points of one isotherm, ordered by plastic strain.

        Args:
            d_temperature_C: The isotherm's exact temperature.
            d_strain_rate_per_s: Required for a rate-dependent curve,
                must be None otherwise.

        Raises:
            ValueError: No isotherm matches exactly, or the strain rate
                argument doesn't fit the curve. Interpolating between
                isotherms is a solver choice (linear, Arrhenius,
                Johnson-Cook), so it is not done here.
        """
        if self.b_is_rate_dependent and d_strain_rate_per_s is None:
            raise ValueError(
                f"FlowCurve is rate-dependent; pass d_strain_rate_per_s, one of "
                f"{list(self.d_strain_rates_per_s)}"
            )
        if not self.b_is_rate_dependent and d_strain_rate_per_s is not None:
            raise ValueError("FlowCurve is rate-independent; d_strain_rate_per_s must be None")
        isotherm = tuple(
            p
            for p in self.points
            if p.d_temperature_C == d_temperature_C and p.d_strain_rate_per_s == d_strain_rate_per_s
        )
        if not isotherm:
            raise ValueError(
                f"FlowCurve has no isotherm at {d_temperature_C} C"
                f"{'' if d_strain_rate_per_s is None else f', {d_strain_rate_per_s} 1/s'}; "
                f"temperatures available: {list(self.d_temperatures_C)}"
            )
        return isotherm


__all__ = [
    "FlowCurve",
    "FlowPoint",
    "StressStrainMeasure",
]
