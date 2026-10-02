"""Tests for the BHCurveData dataclass (v1.2.0)."""

from __future__ import annotations

import math
import warnings

import pytest

from emergent_matter_materials.bh_curve import BHCurveData, MU_0_H_per_m

# ── A typical-valid M19-shaped curve, used as a baseline ───────────────


def _valid_kwargs():
    return {
        "d_B_table_T": (0.2, 0.4, 0.7, 1.0, 1.2, 1.3, 1.4, 1.5, 1.55, 1.6),
        "d_H_table_A_m": (31.9, 44.9, 67.3, 106.0, 164.0, 235.0, 435.0, 1109.0, 1813.0, 2802.0),
        "s_source": "EMERF Lamination Steels Third Edition (Sprague 2007), M-19 page",
        "s_condition": "DC virgin curve, 20 C, as-sheared 29-ga M-19",
        "s_confidence": "datasheet",
    }


# ── Construction + access ──────────────────────────────────────────────


def test_valid_construction():
    c = BHCurveData(**_valid_kwargs())
    assert len(c.d_B_table_T) == len(c.d_H_table_A_m) == 10
    assert c.s_confidence == "datasheet"
    assert c.s_notes == ""
    assert c.s_digitization_method == ""


def test_frozen_dataclass_immutable():
    c = BHCurveData(**_valid_kwargs())
    with pytest.raises((AttributeError, Exception)):
        c.d_B_table_T = (0.0,)


def test_mu0_constant_value():
    assert MU_0_H_per_m == pytest.approx(4.0e-7 * math.pi, rel=1e-15)


# ── Length + shape validation ──────────────────────────────────────────


def test_length_mismatch_rejected():
    kwargs = _valid_kwargs()
    kwargs["d_H_table_A_m"] = kwargs["d_H_table_A_m"][:-1]  # drop one
    with pytest.raises(ValueError, match="length mismatch"):
        BHCurveData(**kwargs)


def test_too_few_points_rejected():
    kwargs = _valid_kwargs()
    kwargs["d_B_table_T"] = (0.5, 1.0)
    kwargs["d_H_table_A_m"] = (50.0, 200.0)
    with pytest.raises(ValueError, match="at least 3 points"):
        BHCurveData(**kwargs)


def test_three_points_minimum_accepted():
    """Smallest valid table is 3 points (per validator rule (1))."""
    c = BHCurveData(
        d_B_table_T=(0.5, 1.0, 1.5),
        d_H_table_A_m=(50.0, 200.0, 1700.0),
        s_source="x",
        s_condition="x",
        s_confidence="datasheet",
    )
    assert len(c.d_B_table_T) == 3


# ── Monotonicity validation ────────────────────────────────────────────


def test_non_monotone_B_rejected():
    kwargs = _valid_kwargs()
    bad_B = list(kwargs["d_B_table_T"])
    bad_B[3] = bad_B[2]  # equal, not strictly ascending
    kwargs["d_B_table_T"] = tuple(bad_B)
    with pytest.raises(ValueError, match="d_B_table_T must be strictly ascending"):
        BHCurveData(**kwargs)


def test_non_monotone_H_rejected():
    kwargs = _valid_kwargs()
    bad_H = list(kwargs["d_H_table_A_m"])
    bad_H[3] = bad_H[2] - 10.0  # decreasing
    kwargs["d_H_table_A_m"] = tuple(bad_H)
    with pytest.raises(ValueError, match="d_H_table_A_m must be strictly ascending"):
        BHCurveData(**kwargs)


# ── Non-negative start ─────────────────────────────────────────────────


def test_negative_B_start_rejected():
    kwargs = _valid_kwargs()
    kwargs["d_B_table_T"] = (-0.01,) + kwargs["d_B_table_T"][1:]
    with pytest.raises(ValueError, match="d_B_table_T must start at >= 0"):
        BHCurveData(**kwargs)


def test_origin_start_accepted():
    """(0, 0) as the first point must be allowed: common for full curves."""
    c = BHCurveData(
        d_B_table_T=(0.0, 0.5, 1.0, 1.5),
        d_H_table_A_m=(0.0, 60.0, 200.0, 1700.0),
        s_source="x",
        s_condition="x",
        s_confidence="datasheet",
    )
    # initial slope is computed on the (0.5 → 1.0) interval since (0,0)
    # is skipped to avoid 0/0
    assert c.d_B_table_T[0] == 0.0
    assert c.d_H_table_A_m[0] == 0.0


# ── Ferromagnetic initial-slope validation ─────────────────────────────


def test_initial_slope_below_mu0_rejected():
    """If initial ΔB/ΔH <= μ₀, the material isn't ferromagnetic: reject."""
    # H rising fast, B rising slow → ΔB/ΔH well below μ₀
    with pytest.raises(ValueError, match="initial secant permeability"):
        BHCurveData(
            d_B_table_T=(0.0, 1e-10, 2e-10),
            d_H_table_A_m=(0.0, 1.0, 2.0),
            s_source="x",
            s_condition="x",
            s_confidence="datasheet",
        )


def test_initial_slope_just_above_mu0_accepted():
    """Just above μ₀ should pass: boundary check."""
    # ΔB/ΔH = 2·μ₀ over the first interval → comfortably ferromagnetic
    d_dB = 2.0 * MU_0_H_per_m * 100.0
    c = BHCurveData(
        d_B_table_T=(0.0, d_dB, 2 * d_dB, 3 * d_dB),
        d_H_table_A_m=(0.0, 100.0, 200.0, 300.0),
        s_source="x",
        s_condition="x",
        s_confidence="datasheet",
    )
    assert c.d_B_table_T[1] == d_dB


# ── Final-slope warning (warning, not error) ───────────────────────────


def test_final_slope_warning_fires_when_high_H_unsaturated():
    """If H_max is in the deep-saturation regime but final slope is still
    >> μ₀, a warning should fire (not an error)."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        BHCurveData(
            d_B_table_T=(0.5, 1.0, 1.5, 2.0),
            # H_max = 1e5 (well above the 5e4 saturation threshold), but
            # final ΔB/ΔH = 0.5 / (1e5 - 5e4) = 1e-5 ≈ 8·μ₀: well above
            # the 2·μ₀ warning trigger
            d_H_table_A_m=(50.0, 200.0, 50000.0, 100000.0),
            s_source="x",
            s_condition="x",
            s_confidence="datasheet",
        )
    msgs = [str(w.message) for w in caught if "final secant" in str(w.message)]
    assert len(msgs) == 1, f"expected 1 final-slope warning, got {msgs}"


def test_final_slope_no_warning_when_low_H():
    """If H_max is below the saturation threshold, no warning even if
    final slope is high (vendor table legitimately stops early)."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        BHCurveData(
            d_B_table_T=(0.5, 1.0, 1.5),
            d_H_table_A_m=(50.0, 200.0, 1700.0),  # H_max < 5e4
            s_source="x",
            s_condition="x",
            s_confidence="datasheet",
        )
    msgs = [str(w.message) for w in caught if "final secant" in str(w.message)]
    assert len(msgs) == 0, f"expected no warning for low-H table, got {msgs}"


# ── Confidence gate ────────────────────────────────────────────────────


def test_handbook_confidence_rejected():
    """Tier-2 handbook confidence must be rejected for BHCurveData."""
    kwargs = _valid_kwargs()
    kwargs["s_confidence"] = "handbook"
    with pytest.raises(ValueError, match="must be Tier 1"):
        BHCurveData(**kwargs)


def test_aggregator_confidence_rejected():
    kwargs = _valid_kwargs()
    kwargs["s_confidence"] = "aggregator"
    with pytest.raises(ValueError, match="must be Tier 1"):
        BHCurveData(**kwargs)


def test_each_tier1_level_accepted():
    for level in ("measured", "datasheet", "standard"):
        kwargs = _valid_kwargs()
        kwargs["s_confidence"] = level
        c = BHCurveData(**kwargs)
        assert c.s_confidence == level


# ── Source provenance gate ─────────────────────────────────────────────


def test_empty_source_rejected():
    kwargs = _valid_kwargs()
    kwargs["s_source"] = ""
    with pytest.raises(ValueError, match="s_source must be a non-empty"):
        BHCurveData(**kwargs)


def test_whitespace_only_source_rejected():
    kwargs = _valid_kwargs()
    kwargs["s_source"] = "   \t\n  "
    with pytest.raises(ValueError, match="s_source must be a non-empty"):
        BHCurveData(**kwargs)


# ── Digitization marker ────────────────────────────────────────────────


def test_digitization_method_default_empty():
    c = BHCurveData(**_valid_kwargs())
    assert c.s_digitization_method == ""


def test_digitization_method_set_for_graph_derived():
    kwargs = _valid_kwargs()
    kwargs["s_digitization_method"] = (
        "WebPlotDigitizer on Metglas POWERLITE Figure 3, ~12 points; "
        "±3% on B-axis from grid resolution"
    )
    c = BHCurveData(**kwargs)
    assert "WebPlotDigitizer" in c.s_digitization_method


# ── Integration test: load the catalog and verify the 3 v1.2 curves ──


def test_catalog_m19_bh_curve_loaded():
    """The actual M19 curve in the catalog must round-trip."""
    import emergent_matter_materials as emm

    m19 = emm.get_material("m19_silicon_steel")
    c = m19.electromagnetic.bh_curve
    assert c is not None
    assert len(c.d_B_table_T) == 16
    assert c.d_B_table_T[0] == pytest.approx(0.200)
    assert c.d_B_table_T[-1] == pytest.approx(2.100)
    assert c.d_H_table_A_m[0] == pytest.approx(31.9)
    assert c.d_H_table_A_m[-1] == pytest.approx(88491.0)
    assert c.s_confidence == "datasheet"
    assert "EMERF" in c.s_source or "Lamination Steels" in c.s_source


def test_catalog_m270_35a_bh_curve_loaded():
    import emergent_matter_materials as emm

    m270 = emm.get_material("m270_35a_silicon_steel")
    c = m270.electromagnetic.bh_curve
    assert c is not None
    assert len(c.d_B_table_T) == 18
    assert c.d_B_table_T[0] == pytest.approx(0.1)
    assert c.d_B_table_T[-1] == pytest.approx(1.8)
    assert "50 Hz" in c.s_condition.lower() or "50 hz" in c.s_condition.lower()


def test_catalog_hiperco_bh_curve_loaded_with_warning_acknowledged():
    """Hiperco 50's curve starts post-knee at B=2.10 T: the curve loads
    cleanly but the final-slope check is allowed to warn."""
    import emergent_matter_materials as emm

    h = emm.get_material("hiperco_50")
    c = h.electromagnetic.bh_curve
    assert c is not None
    assert len(c.d_B_table_T) == 6
    assert c.d_B_table_T[0] == pytest.approx(2.10)
    assert c.d_H_table_A_m[0] == pytest.approx(400.0)
    # explicit consumer warning must be in s_notes
    assert "POST-KNEE" in c.s_notes


def test_catalog_other_materials_have_no_bh_curve():
    """Only the three soft-magnetic materials with published curves
    should have bh_curve populated in v1.2: everything else None."""
    import emergent_matter_materials as emm

    expect_populated = {"m19_silicon_steel", "m270_35a_silicon_steel", "hiperco_50"}
    for s_id in emm.list_materials():
        mat = emm.get_material(s_id)
        if mat.electromagnetic is None:
            continue
        if s_id in expect_populated:
            assert mat.electromagnetic.bh_curve is not None, (
                f"{s_id} expected to have bh_curve populated"
            )
        else:
            assert mat.electromagnetic.bh_curve is None, (
                f"{s_id} unexpectedly has bh_curve populated"
            )
