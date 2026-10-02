"""Tests for the SteinmetzData composite type and the M19 v1.3 entry.

Catalog v1.3.0 adds soft-magnetic Steinmetz core-loss coefficients. The
SteinmetzData dataclass (``emergent_matter_materials.steinmetz``)
stores the (k, alpha, beta) triple plus the reference operating point
and full provenance; it attaches to ``Electromagnetic.steinmetz`` as a
composite, and three float accessors on Electromagnetic expose the
triple to the consuming-side magnetostatic FEM solver.

A downstream FEM consumer reads:

    em = material.electromagnetic
    k = getattr(em, "d_steinmetz_k", None)
    alpha = getattr(em, "d_steinmetz_alpha", None)
    beta = getattr(em, "d_steinmetz_beta", None)
    # if None → "missing_material_loss_data"; else use Steinmetz fit

The tests below cover:

  1. M19 has all three Steinmetz fields populated and positive.
  2. M19 round-trips the reference point (3.42 W/kg @ 1.5 T, 60 Hz).
  3. alpha and beta are in reasonable bounds (catalog literature
     bounds for soft-magnetic alloys).
  4. core_loss provenance exists and has a non-empty source string.
  5. M19 structural density exists (a core-loss kernel needs it for the
     kg → m³ conversion).
  6. The new fields are optional / backward-compatible (every other
     catalog material survives v1.3 without populating Steinmetz).

Plus dataclass-level validation tests covering positivity, round-trip,
exponent bounds, confidence-enum, and the validity-range integrity.
"""

from __future__ import annotations

import dataclasses
import math

import pytest

from emergent_matter_materials import (
    Electromagnetic,
    SteinmetzData,
    get_material,
    list_materials,
)
from emergent_matter_materials.property_value import PropertyValue

# ──────────────────────────────────────────────────────────────────────
# Version anchors
# ──────────────────────────────────────────────────────────────────────


def test_steinmetz_schema_is_public_and_populated():
    """The Steinmetz schema is exported and the catalog carries data for it.
    Version equality between pyproject / __version__ / __catalog_version__ is
    owned by tests/test_catalog_versioning.py."""
    assert dataclasses.is_dataclass(SteinmetzData)
    with_data = [
        s_id
        for s_id in list_materials()
        if (em := get_material(s_id).electromagnetic) is not None and em.d_steinmetz_k is not None
    ]
    assert "m19_silicon_steel" in with_data


# ──────────────────────────────────────────────────────────────────────
# M19 catalog entry: the six acceptance gates from the brief
# ──────────────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def m19_em():
    """Electromagnetic group from M19 silicon steel."""
    m19 = get_material("m19_silicon_steel")
    return m19.electromagnetic


def test_m19_steinmetz_fields_populated_and_positive(m19_em):
    """Gate 1: M19 has all three Steinmetz fields populated and positive."""
    assert m19_em.d_steinmetz_k is not None
    assert m19_em.d_steinmetz_alpha is not None
    assert m19_em.d_steinmetz_beta is not None
    assert m19_em.d_steinmetz_k > 0.0
    assert m19_em.d_steinmetz_alpha > 0.0
    assert m19_em.d_steinmetz_beta > 0.0


def test_m19_steinmetz_round_trips_reference_point(m19_em):
    """Gate 2: k · f_ref^alpha · B_ref^beta ≈ P_ref = 3.42 W/kg.

    Source of truth: the calibration formula. Single-point fits should
    round-trip to float precision (<= 1e-12 relative).
    """
    k = m19_em.d_steinmetz_k
    alpha = m19_em.d_steinmetz_alpha
    beta = m19_em.d_steinmetz_beta
    P_pred = k * 60.0**alpha * 1.5**beta
    assert P_pred == pytest.approx(3.42, rel=1e-12), (
        f"M19 Steinmetz round-trip: "
        f"k · 60^{alpha} · 1.5^{beta} = {P_pred:.9f} W/kg "
        f"vs reference 3.42 W/kg. k must be derived from the "
        f"reference triple, not hardcoded."
    )


def test_m19_steinmetz_exponents_in_literature_bounds(m19_em):
    """Gate 3: alpha in [1.4, 1.8], beta in [1.6, 2.4]."""
    alpha = m19_em.d_steinmetz_alpha
    beta = m19_em.d_steinmetz_beta
    assert 1.4 <= alpha <= 1.8, (
        f"alpha={alpha} outside literature range [1.4, 1.8] for soft-magnetic alloys."
    )
    assert 1.6 <= beta <= 2.4, (
        f"beta={beta} outside literature range [1.6, 2.4] for soft-magnetic alloys."
    )


def test_m19_core_loss_provenance_non_empty(m19_em):
    """Gate 4: core_loss provenance exists with non-empty source string."""
    assert m19_em.core_loss is not None
    assert isinstance(m19_em.core_loss, PropertyValue)
    assert m19_em.core_loss.s_source.strip() != ""
    # And the SteinmetzData composite carries its own provenance
    assert m19_em.steinmetz is not None
    assert m19_em.steinmetz.s_source.strip() != ""
    assert m19_em.steinmetz.s_calibration_method == "single_point_literature_alpha_beta"


def test_m19_density_present(m19_em):
    """Gate 5: M19.structural.density is populated.

    A downstream core-loss kernel converts W/kg → W/m³ via
    the catalog's structural density; missing density would make the
    Steinmetz triple unusable at the FEM level.
    """
    m19 = get_material("m19_silicon_steel")
    assert m19.structural is not None
    assert m19.structural.density is not None
    assert m19.structural.d_density_kg_m3 > 0.0


def test_steinmetz_is_optional_backward_compatible():
    """Gate 6: existing catalog materials without a Steinmetz fit
    still construct successfully (the new field is Optional)."""
    # Every catalog material must construct cleanly under v1.3 even if
    # it doesn't populate the new Steinmetz field. Walk the catalog
    # and verify each material's electromagnetic group accepts the
    # new schema without requiring Steinmetz data.
    n_total = 0
    n_with_steinmetz = 0
    for s_id in list_materials():
        mat = get_material(s_id)
        em = mat.electromagnetic
        if em is None:
            # Polymers + structural-only metals legitimately have no EM
            # group; that's fine.
            continue
        n_total += 1
        # The accessors return None gracefully when steinmetz is absent.
        k = em.d_steinmetz_k
        alpha = em.d_steinmetz_alpha
        beta = em.d_steinmetz_beta
        if em.steinmetz is None:
            assert k is None and alpha is None and beta is None, (
                f"{s_id}: steinmetz composite is None but accessor "
                f"returned non-None (k={k}, alpha={alpha}, beta={beta})"
            )
        else:
            n_with_steinmetz += 1
            assert k is not None and alpha is not None and beta is not None

    # Sanity: at least one material (M19) has the Steinmetz triple now.
    assert n_with_steinmetz >= 1, (
        f"v1.3 should populate Steinmetz on at least M19; found "
        f"{n_with_steinmetz}/{n_total} EM-populated materials"
    )


# ──────────────────────────────────────────────────────────────────────
# SteinmetzData dataclass: validator coverage
# ──────────────────────────────────────────────────────────────────────


def _valid_kwargs(**overrides):
    """Build a minimal valid SteinmetzData kwargs dict; overrides applied."""
    P_ref, f_ref, B_ref = 3.42, 60.0, 1.5
    alpha, beta = 1.6, 2.0
    k = P_ref / (f_ref**alpha * B_ref**beta)
    base = {
        "d_k": k,
        "d_alpha": alpha,
        "d_beta": beta,
        "d_reference_loss_W_per_kg": P_ref,
        "d_reference_frequency_Hz": f_ref,
        "d_reference_B_pk_T": B_ref,
        "d_validity_freq_range_Hz": (20.0, 400.0),
        "d_validity_B_range_T": (0.5, 1.8),
        "s_source": "Test fixture, M19 anchor 3.42 W/kg @ 1.5 T / 60 Hz.",
        "s_calibration_method": "single_point_literature_alpha_beta",
        "s_condition": "test fixture",
        "s_notes": "",
    }
    base.update(overrides)
    return base


def test_valid_minimal_construction():
    """A minimal valid SteinmetzData round-trips cleanly."""
    sd = SteinmetzData(**_valid_kwargs())
    # Round-trip is bit-for-bit exact (single-point fit).
    P_pred = sd.d_k * sd.d_reference_frequency_Hz**sd.d_alpha * sd.d_reference_B_pk_T**sd.d_beta
    assert P_pred == pytest.approx(sd.d_reference_loss_W_per_kg, rel=1e-12)


@pytest.mark.parametrize(
    "field",
    [
        "d_k",
        "d_alpha",
        "d_beta",
        "d_reference_loss_W_per_kg",
        "d_reference_frequency_Hz",
        "d_reference_B_pk_T",
    ],
)
def test_non_positive_value_rejected(field):
    """Every dimensional field must be positive finite."""
    with pytest.raises(ValueError, match=r"must be positive finite"):
        SteinmetzData(**_valid_kwargs(**{field: 0.0}))
    with pytest.raises(ValueError, match=r"must be positive finite"):
        SteinmetzData(**_valid_kwargs(**{field: -1.0}))


def test_empty_source_rejected():
    with pytest.raises(ValueError, match=r"s_source"):
        SteinmetzData(**_valid_kwargs(s_source=""))
    with pytest.raises(ValueError, match=r"s_source"):
        SteinmetzData(**_valid_kwargs(s_source="   "))


def test_unknown_confidence_rejected():
    with pytest.raises(ValueError, match=r"s_calibration_method"):
        SteinmetzData(**_valid_kwargs(s_calibration_method="aggregator"))
    with pytest.raises(ValueError, match=r"s_calibration_method"):
        SteinmetzData(**_valid_kwargs(s_calibration_method=""))


def test_round_trip_mismatch_rejected():
    """k that doesn't round-trip to within 2% of P_ref → ValueError."""
    # Take a valid k and corrupt it by 10%: should reject.
    valid = _valid_kwargs()
    with pytest.raises(ValueError, match=r"round-trip"):
        SteinmetzData(**{**valid, "d_k": valid["d_k"] * 1.10})


def test_alpha_out_of_bounds_rejected():
    with pytest.raises(ValueError, match=r"d_alpha"):
        # Need to also fix k so round-trip passes before the alpha-bounds check
        kw = _valid_kwargs()
        bad_alpha = 1.0
        kw["d_alpha"] = bad_alpha
        kw["d_k"] = kw["d_reference_loss_W_per_kg"] / (
            kw["d_reference_frequency_Hz"] ** bad_alpha * kw["d_reference_B_pk_T"] ** kw["d_beta"]
        )
        SteinmetzData(**kw)


def test_beta_out_of_bounds_rejected():
    with pytest.raises(ValueError, match=r"d_beta"):
        kw = _valid_kwargs()
        bad_beta = 3.0
        kw["d_beta"] = bad_beta
        kw["d_k"] = kw["d_reference_loss_W_per_kg"] / (
            kw["d_reference_frequency_Hz"] ** kw["d_alpha"] * kw["d_reference_B_pk_T"] ** bad_beta
        )
        SteinmetzData(**kw)


def test_validity_range_must_contain_reference():
    """Reference (f_ref, B_ref) must lie inside the declared validity envelope."""
    with pytest.raises(ValueError, match=r"validity"):
        SteinmetzData(**_valid_kwargs(d_validity_freq_range_Hz=(100.0, 400.0)))
    with pytest.raises(ValueError, match=r"validity"):
        SteinmetzData(**_valid_kwargs(d_validity_B_range_T=(0.5, 1.4)))


def test_validity_range_inverted_rejected():
    with pytest.raises(ValueError, match=r"validity"):
        SteinmetzData(**_valid_kwargs(d_validity_freq_range_Hz=(400.0, 100.0)))


def test_validity_ranges_optional():
    """Both validity-range tuples can be None."""
    sd = SteinmetzData(
        **_valid_kwargs(
            d_validity_freq_range_Hz=None,
            d_validity_B_range_T=None,
        )
    )
    assert sd.d_validity_freq_range_Hz is None
    assert sd.d_validity_B_range_T is None


# ──────────────────────────────────────────────────────────────────────
# Electromagnetic-level integration: accessors return None when absent
# ──────────────────────────────────────────────────────────────────────


def test_electromagnetic_without_steinmetz_returns_none_accessors():
    """A bare Electromagnetic() returns None for every Steinmetz accessor."""
    em = Electromagnetic()
    assert em.steinmetz is None
    assert em.d_steinmetz_k is None
    assert em.d_steinmetz_alpha is None
    assert em.d_steinmetz_beta is None


def test_electromagnetic_with_steinmetz_routes_accessors():
    """Accessors return floats when the composite is present."""
    sd = SteinmetzData(**_valid_kwargs())
    em = Electromagnetic(steinmetz=sd)
    assert em.d_steinmetz_k == pytest.approx(sd.d_k, rel=1e-12)
    assert em.d_steinmetz_alpha == sd.d_alpha
    assert em.d_steinmetz_beta == sd.d_beta


# ──────────────────────────────────────────────────────────────────────
# Consumer compatibility: emulate a downstream FEM reader
# ──────────────────────────────────────────────────────────────────────


def test_fem_consumer_pattern_on_m19():
    """A downstream FEM consumer reads via getattr(..., None). Works on M19."""
    m19 = get_material("m19_silicon_steel")
    em = m19.electromagnetic
    k = getattr(em, "d_steinmetz_k", None)
    alpha = getattr(em, "d_steinmetz_alpha", None)
    beta = getattr(em, "d_steinmetz_beta", None)
    assert k is not None and alpha is not None and beta is not None
    # And the round-trip works
    P_pred = k * 60.0**alpha * 1.5**beta
    assert P_pred == pytest.approx(3.42, rel=1e-12)
    # density present for kg → m³
    rho = m19.structural.d_density_kg_m3
    assert rho > 0.0


def test_fem_consumer_pattern_on_pure_copper():
    """A downstream FEM consumer sees None on materials without Steinmetz."""
    cu = get_material("pure_copper")
    em = cu.electromagnetic
    k = getattr(em, "d_steinmetz_k", None)
    alpha = getattr(em, "d_steinmetz_alpha", None)
    beta = getattr(em, "d_steinmetz_beta", None)
    assert k is None
    assert alpha is None
    assert beta is None


# ──────────────────────────────────────────────────────────────────────
# v1.4.0 multi-point fits: M270-35A + Hiperco 50
#
# The grids below are transcribed from the cited vendor PDFs and are
# the same data scripts/fit_steinmetz.py fits (that script is the
# source of truth for the stored exponents; rerun it to reproduce).
# Embedding them here turns the source tables into a regression
# anchor: if anyone edits the stored (k, alpha, beta), these tests
# re-measure the fit quality against the actual Tier-1 data.
# ──────────────────────────────────────────────────────────────────────

# Cogent SURA M270-35A (June 2008): W/kg at f Hz, fit window only.
_M270_GRID = {
    50.0: [
        (0.5, 0.31),
        (0.6, 0.43),
        (0.7, 0.54),
        (0.8, 0.68),
        (0.9, 0.83),
        (1.0, 1.01),
        (1.1, 1.20),
        (1.2, 1.42),
        (1.3, 1.70),
        (1.4, 2.12),
        (1.5, 2.47),
        (1.6, 2.80),
        (1.7, 3.05),
        (1.8, 3.25),
    ],
    100.0: [
        (0.5, 0.80),
        (0.6, 1.06),
        (0.7, 1.38),
        (0.8, 1.73),
        (0.9, 2.10),
        (1.0, 2.51),
        (1.1, 2.98),
        (1.2, 3.51),
        (1.3, 4.15),
        (1.4, 4.97),
        (1.5, 5.92),
    ],
    200.0: [
        (0.5, 1.91),
        (0.6, 2.61),
        (0.7, 3.39),
        (0.8, 4.26),
        (0.9, 5.23),
        (1.0, 6.30),
        (1.1, 7.51),
        (1.2, 8.88),
        (1.3, 10.5),
        (1.4, 12.5),
        (1.5, 14.9),
    ],
    400.0: [
        (0.5, 4.94),
        (0.6, 6.84),
        (0.7, 9.00),
        (0.8, 11.4),
        (0.9, 14.2),
        (1.0, 17.3),
        (1.1, 20.9),
        (1.2, 24.9),
        (1.3, 29.5),
        (1.4, 35.4),
        (1.5, 41.8),
    ],
}

# Carpenter Hiperco 50 E200 p.2: 0.014 in strip, typical magnetic anneal.
_HIPERCO_GRID = {
    60.0: [(1.0, 1.5), (1.5, 2.5), (2.0, 3.7)],
    400.0: [(1.0, 15.0), (1.5, 35.0), (2.0, 63.0)],
    1000.0: [(1.0, 60.0), (1.5, 160.0), (2.0, 340.0)],
}


def _grid_fit_stats(grid, k, alpha, beta):
    """RMS + worst relative residual of k·f^alpha·B^beta over a grid."""
    rels = [(k * f**alpha * B**beta - P) / P for f, rows in grid.items() for (B, P) in rows]
    rms = math.sqrt(sum(r * r for r in rels) / len(rels))
    worst = max(abs(r) for r in rels)
    return rms, worst


@pytest.fixture(scope="module")
def m270_em():
    return get_material("m270_35a_silicon_steel").electromagnetic


@pytest.fixture(scope="module")
def hiperco_em():
    return get_material("hiperco_50").electromagnetic


def test_m270_steinmetz_round_trips_anchor(m270_em):
    """k·50^alpha·1.5^beta == 2.47 W/kg (Cogent TYPICAL anchor) exactly.

    Note the anchor is deliberately the typical 2.47, NOT the EN 10106
    grade-max 2.70 stored in core_loss: the fit is anchored to the
    typical surface it was fitted on (see s_notes).
    """
    sd = m270_em.steinmetz
    assert sd is not None
    assert sd.s_calibration_method == "multi_point_fitted"
    P_pred = sd.d_k * 50.0**sd.d_alpha * 1.5**sd.d_beta
    assert P_pred == pytest.approx(2.47, rel=1e-12)


def test_hiperco_steinmetz_round_trips_anchor(hiperco_em):
    """k·60^alpha·1.5^beta == 2.5 W/kg: same point as core_loss PV."""
    sd = hiperco_em.steinmetz
    assert sd is not None
    assert sd.s_calibration_method == "multi_point_fitted"
    P_pred = sd.d_k * 60.0**sd.d_alpha * 1.5**sd.d_beta
    assert P_pred == pytest.approx(2.5, rel=1e-12)
    # Anchor consistency with the scalar core_loss PropertyValue:
    assert hiperco_em.core_loss.d_value == pytest.approx(sd.d_reference_loss_W_per_kg)


def test_m270_steinmetz_exponents_in_bounds(m270_em):
    """alpha in the v1.4-widened [1.3, 1.8] (measured 1.346: thin-gauge
    NO Si-Fe at power frequency is hysteresis-dominated); beta in
    [1.6, 2.4]."""
    sd = m270_em.steinmetz
    assert 1.3 <= sd.d_alpha <= 1.8
    assert 1.6 <= sd.d_beta <= 2.4


def test_hiperco_steinmetz_exponents_in_bounds(hiperco_em):
    sd = hiperco_em.steinmetz
    assert 1.3 <= sd.d_alpha <= 1.8
    assert 1.6 <= sd.d_beta <= 2.4


def test_m270_steinmetz_grid_fit_quality(m270_em):
    """Re-anchored model vs the 47-point Cogent window: RMS ~11.4%,
    worst ~+19% (conservatively high; see s_notes). Gates set with
    headroom so only a real regression (wrong exponents / wrong k)
    trips them."""
    sd = m270_em.steinmetz
    rms, worst = _grid_fit_stats(_M270_GRID, sd.d_k, sd.d_alpha, sd.d_beta)
    assert rms < 0.13, f"M270 Steinmetz RMS rel err {rms:.1%} (expected ~11.4%)"
    assert worst < 0.22, f"M270 worst rel err {worst:.1%} (expected ~19%)"


def test_hiperco_steinmetz_grid_fit_quality(hiperco_em):
    """Re-anchored model vs the 9-point E200 factorial: RMS ~15.8%,
    worst ~24.6% (single power law can't capture the f·B interaction;
    exact at the 60 Hz / 1.5 T anchor by construction)."""
    sd = hiperco_em.steinmetz
    rms, worst = _grid_fit_stats(_HIPERCO_GRID, sd.d_k, sd.d_alpha, sd.d_beta)
    assert rms < 0.18, f"Hiperco Steinmetz RMS rel err {rms:.1%} (expected ~15.8%)"
    assert worst < 0.27, f"Hiperco worst rel err {worst:.1%} (expected ~24.6%)"


def test_steinmetz_populated_exactly_on_expected_materials():
    """v1.4: exactly M19 + M270-35A + Hiperco 50 carry a Steinmetz fit;
    every other EM-populated material returns None (same exclusivity
    style as the bh_curve coverage test)."""
    expected = {"m19_silicon_steel", "m270_35a_silicon_steel", "hiperco_50"}
    populated = set()
    for s_id in list_materials():
        mat = get_material(s_id)
        if mat.electromagnetic is None:
            continue
        if mat.electromagnetic.steinmetz is not None:
            populated.add(s_id)
    assert populated == expected, (
        f"Steinmetz coverage drifted: expected {sorted(expected)}, got {sorted(populated)}"
    )


# ──────────────────────────────────────────────────────────────────────
# Deprecated alias: s_confidence -> s_calibration_method
# ──────────────────────────────────────────────────────────────────────


def test_s_confidence_keyword_is_a_deprecated_alias():
    kwargs = _valid_kwargs()
    method = kwargs.pop("s_calibration_method")
    with pytest.warns(DeprecationWarning, match="s_calibration_method"):
        sd = SteinmetzData(**kwargs, s_confidence=method)
    assert sd.s_calibration_method == method


def test_s_confidence_attribute_read_is_a_deprecated_alias():
    sd = SteinmetzData(**_valid_kwargs())
    with pytest.warns(DeprecationWarning, match="s_calibration_method"):
        assert sd.s_confidence == sd.s_calibration_method


def test_passing_both_names_is_an_error():
    with pytest.warns(DeprecationWarning), pytest.raises(TypeError, match="not both"):
        SteinmetzData(**_valid_kwargs(), s_confidence="multi_point_fitted")


def test_s_confidence_is_not_a_dataclass_field():
    """The alias is a property, so asdict()/fields() consumers see only the new name."""
    assert "s_confidence" not in {f.name for f in dataclasses.fields(SteinmetzData)}
    assert "s_calibration_method" in {f.name for f in dataclasses.fields(SteinmetzData)}
