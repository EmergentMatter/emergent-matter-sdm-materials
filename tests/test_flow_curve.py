"""A FlowCurve holds contiguous isotherms of flow stress vs plastic strain, sourced per point.

Pins the point invariants (non-negative plastic strain, positive stress in
Pa), the ordering rule that keeps isotherms contiguous, and the isotherm
lookup that refuses to interpolate between temperatures.
"""

from __future__ import annotations

import pytest

from emergent_matter_materials import FlowCurve, FlowPoint, PropertyValue


def _stress(d_value_Pa: float, *, s_units: str = "Pa") -> PropertyValue:
    return PropertyValue(
        d_value=d_value_Pa, s_units=s_units, s_source="Test tensile lab", s_confidence="measured"
    )


def _curve() -> FlowCurve:
    return FlowCurve.from_rows(
        [
            (25.0, 0.0, 276e6),
            (25.0, 0.05, 310e6),
            (400.0, 0.0, 50e6),
            (400.0, 0.05, 60e6),
        ],
        s_source="Test tensile lab",
        s_confidence="measured",
    )


def test_from_rows_builds_points_with_shared_provenance():
    curve = _curve()
    assert len(curve.points) == 4
    assert {p.stress.s_source for p in curve.points} == {"Test tensile lab"}
    assert {p.stress.s_units for p in curve.points} == {"Pa"}


def test_isotherm_returns_one_temperature_in_strain_order():
    curve = _curve()
    assert curve.d_temperatures_C == (25.0, 400.0)
    isotherm = curve.isotherm(400.0)
    assert [p.d_plastic_strain for p in isotherm] == [0.0, 0.05]
    assert [p.stress.d_value for p in isotherm] == [50e6, 60e6]


def test_isotherm_lookup_does_not_interpolate_between_temperatures():
    with pytest.raises(
        ValueError, match=r"no isotherm at 200.0 C; temperatures available: \[25.0, 400.0\]"
    ):
        _curve().isotherm(200.0)


def test_isotherm_may_start_above_zero_plastic_strain():
    """Some sources start at a few percent strain; the curve keeps that."""
    curve = FlowCurve(points=(FlowPoint(25.0, 0.02, _stress(215e6)),))
    assert curve.isotherm(25.0)[0].d_plastic_strain == 0.02


@pytest.mark.parametrize(
    ("kwargs", "error", "match"),
    [
        ({"d_plastic_strain": -0.01}, ValueError, "must be finite and >= 0"),
        ({"stress": _stress(276.0, s_units="MPa")}, ValueError, "wrong units"),
        ({"stress": _stress(0.0)}, ValueError, "must be finite and positive"),
        ({"d_temperature_C": -300.0}, ValueError, "below absolute zero"),
        ({"d_temperature_C": True}, TypeError, "must be float or int"),
    ],
    ids=["negative-strain", "MPa-not-Pa", "zero-stress", "below-absolute-zero", "bool-temperature"],
)
def test_bad_points_are_rejected(kwargs, error, match):
    point_kwargs = {"d_temperature_C": 25.0, "d_plastic_strain": 0.0, "stress": _stress(276e6)}
    point_kwargs.update(kwargs)
    with pytest.raises(error, match=match):
        FlowPoint(**point_kwargs)


@pytest.mark.parametrize(
    ("rows", "match"),
    [
        ([], "at least one FlowPoint"),
        ([(400.0, 0.0, 50e6), (25.0, 0.0, 276e6)], "ordered by temperature"),
        ([(25.0, 0.05, 310e6), (25.0, 0.0, 276e6)], "strictly increase within an isotherm"),
        ([(25.0, 0.0, 276e6), (25.0, 0.0, 280e6)], "strictly increase within an isotherm"),
    ],
    ids=["empty", "temperature-decreases", "strain-decreases", "duplicate-point"],
)
def test_misordered_curves_are_rejected(rows, match):
    with pytest.raises(ValueError, match=match):
        FlowCurve.from_rows(rows, s_source="Test tensile lab", s_confidence="measured")


@pytest.mark.parametrize(
    "kwargs",
    [
        {"d_temperature_C": float("nan")},
        {"d_temperature_C": float("inf")},
        {"d_plastic_strain": float("nan")},
        {"stress": _stress(float("nan"))},
        {"stress": _stress(float("inf"))},
        {"d_strain_rate_per_s": float("nan")},
        {"d_strain_rate_per_s": 0.0},
    ],
    ids=["nan-T", "inf-T", "nan-strain", "nan-stress", "inf-stress", "nan-rate", "zero-rate"],
)
def test_non_finite_or_non_physical_point_values_are_rejected(kwargs):
    point_kwargs = {"d_temperature_C": 25.0, "d_plastic_strain": 0.0, "stress": _stress(276e6)}
    point_kwargs.update(kwargs)
    with pytest.raises(ValueError, match="finite"):
        FlowPoint(**point_kwargs)


def _rate_point(d_t: float, d_rate: float, d_strain: float, d_stress: float) -> FlowPoint:
    return FlowPoint(d_t, d_strain, _stress(d_stress), d_strain_rate_per_s=d_rate)


def test_rate_dependent_curve_keeps_one_isotherm_per_temperature_and_rate():
    curve = FlowCurve(
        points=(
            _rate_point(800.0, 0.001, 0.0, 100e6),
            _rate_point(800.0, 0.001, 0.05, 120e6),
            _rate_point(800.0, 1.0, 0.0, 180e6),
            _rate_point(800.0, 1.0, 0.05, 210e6),
        ),
        s_stress_strain_measure="true",
    )
    assert curve.b_is_rate_dependent
    assert curve.d_strain_rates_per_s == (0.001, 1.0)
    assert [p.stress.d_value for p in curve.isotherm(800.0, d_strain_rate_per_s=1.0)] == [
        180e6,
        210e6,
    ]
    with pytest.raises(ValueError, match="rate-dependent; pass d_strain_rate_per_s"):
        curve.isotherm(800.0)


def test_strain_rate_must_be_on_every_point_or_none():
    with pytest.raises(ValueError, match="set on every point or on none: 1 of 2"):
        FlowCurve(
            points=(
                FlowPoint(25.0, 0.0, _stress(276e6)),
                _rate_point(25.0, 1.0, 0.05, 310e6),
            )
        )


def test_rates_must_not_decrease_within_a_temperature():
    with pytest.raises(ValueError, match="ordered by temperature, then strain rate"):
        FlowCurve(
            points=(_rate_point(800.0, 1.0, 0.0, 180e6), _rate_point(800.0, 0.001, 0.0, 100e6))
        )


def test_stress_strain_measure_defaults_to_unspecified_and_rejects_unknown_values():
    assert _curve().s_stress_strain_measure == "unspecified"
    with pytest.raises(ValueError, match="s_stress_strain_measure must be one of"):
        FlowCurve(points=_curve().points, s_stress_strain_measure="nominal")  # type: ignore[arg-type]
