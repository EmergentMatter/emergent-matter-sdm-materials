"""Tests for the Manufacturing + ProcessFit dataclasses."""

from __future__ import annotations

import pytest

from emergent_matter_materials.manufacturing import Manufacturing, ProcessFit
from emergent_matter_materials.property_value import PropertyValue as PV


def _ok_fit():
    return ProcessFit(
        shrinkage_linear=PV(d_value=0.005, s_units="", s_source="x", s_confidence="handbook"),
        min_wall_thickness=PV(d_value=0.0008, s_units="m", s_source="x", s_confidence="handbook"),
        min_feature_size=PV(d_value=0.0005, s_units="m", s_source="x", s_confidence="handbook"),
    )


def test_processfit_minimum_construct():
    fit = _ok_fit()
    assert fit.shrinkage_linear.d_value == 0.005


def test_processfit_with_all_optional_fields():
    fit = ProcessFit(
        shrinkage_linear=PV(d_value=0.005, s_units="", s_source="x", s_confidence="handbook"),
        min_wall_thickness=PV(d_value=0.0008, s_units="m", s_source="x", s_confidence="handbook"),
        min_feature_size=PV(d_value=0.0005, s_units="m", s_source="x", s_confidence="handbook"),
        anisotropy_factor_z_vs_xy=PV(
            d_value=0.7, s_units="", s_source="x", s_confidence="handbook"
        ),
        max_unsupported_overhang=PV(
            d_value=45.0, s_units="deg", s_source="x", s_confidence="handbook"
        ),
        typical_layer_height=PV(d_value=0.0002, s_units="m", s_source="x", s_confidence="handbook"),
    )
    assert fit.anisotropy_factor_z_vs_xy.d_value == 0.7


def test_processfit_shrinkage_above_10pct_rejected():
    """Catches the unit-error case of 5.0 instead of 0.005."""
    with pytest.raises(ValueError, match="shrinkage_linear must be in"):
        ProcessFit(
            shrinkage_linear=PV(d_value=5.0, s_units="", s_source="x", s_confidence="handbook"),
            min_wall_thickness=PV(
                d_value=0.0008, s_units="m", s_source="x", s_confidence="handbook"
            ),
            min_feature_size=PV(d_value=0.0005, s_units="m", s_source="x", s_confidence="handbook"),
        )


def test_processfit_anisotropy_above_1_rejected():
    """Z is never STRONGER than XY in additive: catches sign mistakes."""
    with pytest.raises(ValueError, match="anisotropy_factor_z_vs_xy must be in"):
        ProcessFit(
            shrinkage_linear=PV(d_value=0.005, s_units="", s_source="x", s_confidence="handbook"),
            min_wall_thickness=PV(
                d_value=0.0008, s_units="m", s_source="x", s_confidence="handbook"
            ),
            min_feature_size=PV(d_value=0.0005, s_units="m", s_source="x", s_confidence="handbook"),
            anisotropy_factor_z_vs_xy=PV(
                d_value=1.5, s_units="", s_source="x", s_confidence="handbook"
            ),
        )


def test_processfit_overhang_above_90_rejected():
    with pytest.raises(ValueError, match="max_unsupported_overhang must be in"):
        ProcessFit(
            shrinkage_linear=PV(d_value=0.005, s_units="", s_source="x", s_confidence="handbook"),
            min_wall_thickness=PV(
                d_value=0.0008, s_units="m", s_source="x", s_confidence="handbook"
            ),
            min_feature_size=PV(d_value=0.0005, s_units="m", s_source="x", s_confidence="handbook"),
            max_unsupported_overhang=PV(
                d_value=100.0, s_units="deg", s_source="x", s_confidence="handbook"
            ),
        )


def test_manufacturing_construct_with_fit():
    fit = _ok_fit()
    mfg = Manufacturing(
        s_recommended_processes=("FFF_PLA", "SLS_PA12"),
        process_fit={"FFF_PLA": fit},
    )
    assert "FFF_PLA" in mfg.process_fit
    assert mfg.fit_for("FFF_PLA") is fit


def test_manufacturing_fit_not_in_recommended_rejected():
    fit = _ok_fit()
    with pytest.raises(ValueError, match="not in s_recommended_processes"):
        Manufacturing(
            s_recommended_processes=("FFF_PLA",),
            process_fit={"SLS_PA12": fit},  # key not in recommended
        )


def test_manufacturing_fit_for_unknown_key_raises():
    fit = _ok_fit()
    mfg = Manufacturing(
        s_recommended_processes=("FFF_PLA",),
        process_fit={"FFF_PLA": fit},
    )
    with pytest.raises(ValueError, match="No ProcessFit for"):
        mfg.fit_for("SLS_PA12")


def test_manufacturing_empty_fit_allowed():
    # Process can be recommended without a populated fit (filled in over time)
    mfg = Manufacturing(s_recommended_processes=("FFF_PLA", "CNC_BILLET"))
    assert mfg.process_fit == {}
