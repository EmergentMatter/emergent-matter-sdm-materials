"""Tests for the PropertyValue wrapper."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from emergent_matter_materials.property_value import PropertyValue

# ── Construction happy path ────────────────────────────────────────────────


def test_construct_with_required_fields():
    pv = PropertyValue(
        d_value=205e9,
        s_units="Pa",
        s_source="Shigley 10e",
        s_confidence="handbook",
    )
    assert pv.d_value == 205e9
    assert pv.s_units == "Pa"
    assert pv.s_source == "Shigley 10e"
    assert pv.s_condition == ""  # default
    assert pv.s_confidence == "handbook"
    assert pv.s_notes == ""  # default


def test_construct_with_all_fields():
    pv = PropertyValue(
        d_value=1.5,
        s_units="T",
        s_source="vendor TDS",
        s_condition="B=1T, f=50Hz",
        s_confidence="datasheet",
        s_notes="Steinmetz coefficient at single operating point",
    )
    assert pv.s_condition == "B=1T, f=50Hz"
    assert pv.s_notes.startswith("Steinmetz")


def test_construct_is_frozen():
    pv = PropertyValue(d_value=1.0, s_units="Pa", s_source="x", s_confidence="handbook")
    # frozen dataclass: mutation raises FrozenInstanceError
    with pytest.raises(FrozenInstanceError):
        pv.d_value = 2.0  # type: ignore[misc]


# ── Confidence enum gate ───────────────────────────────────────────────────


@pytest.mark.parametrize(
    "s_conf",
    [
        "measured",
        "datasheet",
        "standard",
        "handbook",
        "aggregator",
        "derived",
        "estimated",
        "placeholder",
        "unspecified",
    ],
)
def test_valid_confidence_levels_accepted(s_conf):
    pv = PropertyValue(
        d_value=1.0,
        s_units="Pa",
        s_source="x" if s_conf != "placeholder" else "",
        s_confidence=s_conf,
        s_notes="pending" if s_conf == "placeholder" else "",
    )
    assert pv.s_confidence == s_conf


def test_invalid_confidence_rejected():
    with pytest.raises(ValueError, match="s_confidence must be one of"):
        PropertyValue(d_value=1.0, s_units="Pa", s_source="x", s_confidence="bogus")  # type: ignore[arg-type]


# ── Source-non-empty gate ──────────────────────────────────────────────────


def test_empty_source_rejected_for_handbook():
    with pytest.raises(ValueError, match="non-empty s_source"):
        PropertyValue(d_value=1.0, s_units="Pa", s_source="", s_confidence="handbook")


def test_empty_source_rejected_for_datasheet():
    with pytest.raises(ValueError, match="non-empty s_source"):
        PropertyValue(d_value=1.0, s_units="Pa", s_source="", s_confidence="datasheet")


def test_empty_source_rejected_for_measured():
    with pytest.raises(ValueError, match="non-empty s_source"):
        PropertyValue(d_value=1.0, s_units="Pa", s_source="", s_confidence="measured")


def test_empty_source_rejected_for_unspecified():
    with pytest.raises(ValueError, match="non-empty s_source"):
        PropertyValue(d_value=1.0, s_units="Pa", s_source="", s_confidence="unspecified")


# ── Placeholder gate ───────────────────────────────────────────────────────


def test_placeholder_with_notes_accepted_with_empty_source():
    pv = PropertyValue(
        d_value=1.0,
        s_units="Pa",
        s_source="",
        s_confidence="placeholder",
        s_notes="awaiting lab measurement",
    )
    assert pv.s_confidence == "placeholder"


def test_placeholder_without_notes_rejected():
    with pytest.raises(ValueError, match="placeholder.*s_notes"):
        PropertyValue(
            d_value=1.0,
            s_units="Pa",
            s_source="",
            s_confidence="placeholder",
            s_notes="",  # empty: gate fires
        )


def test_placeholder_with_source_accepted_without_notes():
    # If source IS provided, placeholder doesn't require notes
    pv = PropertyValue(
        d_value=1.0,
        s_units="Pa",
        s_source="partial vendor TDS, pending verification",
        s_confidence="placeholder",
    )
    assert pv.s_confidence == "placeholder"


# ── d_value type gate ──────────────────────────────────────────────────────


def test_d_value_float_accepted():
    pv = PropertyValue(d_value=1.5, s_units="Pa", s_source="x", s_confidence="handbook")
    assert isinstance(pv.d_value, float)


def test_d_value_int_accepted():
    pv = PropertyValue(d_value=205, s_units="Pa", s_source="x", s_confidence="handbook")
    assert pv.d_value == 205


def test_d_value_bool_rejected():
    # Bool is a subclass of int in Python: defensive guard prevents
    # `True` accidentally being treated as a numeric 1.0
    with pytest.raises(TypeError, match="d_value must be float"):
        PropertyValue(
            d_value=True,
            s_units="Pa",
            s_source="x",  # type: ignore[arg-type]
            s_confidence="handbook",
        )


def test_d_value_string_rejected():
    with pytest.raises(TypeError, match="d_value must be float"):
        PropertyValue(
            d_value="1.0",
            s_units="Pa",
            s_source="x",  # type: ignore[arg-type]
            s_confidence="handbook",
        )


# ── Display-unit converters ────────────────────────────────────────────────


def test_as_MPa_converts_from_Pa():
    pv = PropertyValue(d_value=205e9, s_units="Pa", s_source="x", s_confidence="handbook")
    assert pv.as_MPa() == pytest.approx(205000.0)


def test_as_MPa_rejects_non_Pa_units():
    pv = PropertyValue(d_value=205.0, s_units="MPa", s_source="x", s_confidence="handbook")
    with pytest.raises(ValueError, match="expects s_units='Pa'"):
        pv.as_MPa()


def test_as_g_cc_converts_from_kg_m3():
    pv = PropertyValue(d_value=8960.0, s_units="kg/m^3", s_source="x", s_confidence="handbook")
    assert pv.as_g_cc() == pytest.approx(8.960)


def test_as_g_cc_rejects_non_kg_m3():
    pv = PropertyValue(d_value=8.96, s_units="g/cc", s_source="x", s_confidence="handbook")
    with pytest.raises(ValueError, match="expects s_units='kg/m\\^3'"):
        pv.as_g_cc()
