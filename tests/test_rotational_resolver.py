"""Tests for the rotational-loss resolver (Phase 2): synthetic fixtures only.

No real rotational data: fixtures attach SYNTHETIC RotationalLossData records
to real catalog materials via `dataclasses.replace` (which builds new frozen
instances; the catalog itself is never mutated). The resolver computes
eligibility/status, never a loss number.
"""

from __future__ import annotations

import dataclasses

import pytest

from emergent_matter_materials import (
    RotationalLossData,
    get_material,
)
from emergent_matter_materials.rotational_loss import (
    ROTATIONAL_RESOLVE_OUTCOMES,
    STATUS_MISSING_ROTATIONAL_LOSS_DATA,
    STATUS_ROTATIONAL_LOSS_DIAGNOSTIC_ONLY,
    STATUS_ROTATIONAL_LOSS_INCOMPLETE,
    STATUS_ROTATIONAL_LOSS_OUT_OF_RANGE,
    STATUS_ROTATIONAL_LOSS_VALIDATED_CONSUMABLE,
)
from emergent_matter_materials.rotational_resolver import (
    RotationalLossResolveResult,
    resolve_rotational_loss_data_from_material,
)

# ── synthetic record builders ───────────────────────────────────────────────


def _rec_level3(confidence="handbook", **over):
    """A valid, validated-eligible-if-source-admitted Level-3 curve record."""
    base = {
        "s_form": "curve",
        "n_completeness_level": 3,
        "s_source": "Synthetic RSST fixture (Level 3), not real data.",
        "s_confidence": confidence,
        "d_B_table_T": (1.0, 1.25, 1.5),
        "d_f_table_Hz": (50.0, 50.0, 50.0),
        "d_P_rot_table_W_per_kg": (3.0, 4.2, 5.5),
        "d_validity_B_range_T": (0.5, 1.6),
        "d_validity_freq_range_Hz": (10.0, 400.0),
        "s_material_as_published": "Synthetic grade X",
        "s_measurement_method": "RSST circular-locus (synthetic)",
    }
    base.update(over)
    return RotationalLossData(**base)


def _rec_level2(**over):
    base = {
        "s_form": "ratio",
        "n_completeness_level": 2,
        "s_source": "Synthetic R(B) screening ratio (Level 2).",
        "s_confidence": "measured",
        "d_B_table_T": (1.0, 1.3, 1.5),
        "d_ratio_table": (1.6, 1.9, 1.4),
        "d_validity_B_range_T": (0.8, 1.5),
        "d_validity_freq_range_Hz": (40.0, 60.0),
    }
    base.update(over)
    return RotationalLossData(**base)


def _rec_level1(**over):
    base = {
        "s_form": "curve",
        "n_completeness_level": 1,
        "s_source": "Synthetic recordable curve (Level 1), incomplete metadata.",
        "s_confidence": "handbook",
        "d_B_table_T": (1.0, 1.4),
        "d_P_rot_table_W_per_kg": (2.0, 4.0),
    }
    base.update(over)
    return RotationalLossData(**base)


def _rec_level0(**over):
    base = {
        "s_form": "citation_only",
        "n_completeness_level": 0,
        "s_source": "Author et al., synthetic citation, no usable numerical data.",
        "s_confidence": "handbook",
    }
    base.update(over)
    return RotationalLossData(**base)


def _material_with(records, base_id="pure_copper"):
    """Attach synthetic records to a real material via frozen `replace`."""
    base = get_material(base_id)
    em = dataclasses.replace(base.electromagnetic, rotational_loss_models=tuple(records))
    return dataclasses.replace(base, electromagnetic=em)


def _resolve(records, *, B_T=1.25, f_Hz=50.0, temperature_C=None, base_id="pure_copper"):
    return resolve_rotational_loss_data_from_material(
        _material_with(records, base_id=base_id),
        B_T=B_T,
        f_Hz=f_Hz,
        temperature_C=temperature_C,
    )


# ── structured result, never a loss number ─────────────────────────────────


def test_result_is_structured_not_a_number():
    res = _resolve([_rec_level3()])
    assert isinstance(res, RotationalLossResolveResult)
    assert res.s_status in ROTATIONAL_RESOLVE_OUTCOMES
    # No attribute on the result is a computed loss / watt value:
    assert not any(
        "loss_w" in f.name.lower() or f.name.lower().endswith("_w_per_kg")
        for f in dataclasses.fields(res)
    )


# ── absent ──────────────────────────────────────────────────────────────────


def test_absent_real_material_resolves_missing():
    """A real catalog material (empty rotational_loss_models) → missing."""
    m19 = get_material("m19_silicon_steel")
    res = resolve_rotational_loss_data_from_material(m19, B_T=1.0, f_Hz=50.0)
    assert res.s_status == STATUS_MISSING_ROTATIONAL_LOSS_DATA
    assert res.record is None
    assert res.b_validated_consumable is False
    assert res.s_validity_verdict == "no_records"
    assert res.n_records_considered == 0


def test_absent_does_not_emit_zero():
    res = _resolve([])
    assert res.s_status == STATUS_MISSING_ROTATIONAL_LOSS_DATA
    # no numeric loss anywhere; query echo is the only numeric content
    assert res.record is None


# ── Level 0 / 1 → incomplete ────────────────────────────────────────────────


def test_level0_resolves_incomplete():
    res = _resolve([_rec_level0()])
    assert res.s_status == STATUS_ROTATIONAL_LOSS_INCOMPLETE
    assert res.b_validated_consumable is False
    assert res.n_completeness_level == 0


def test_level1_resolves_incomplete():
    res = _resolve([_rec_level1()])
    assert res.s_status == STATUS_ROTATIONAL_LOSS_INCOMPLETE
    assert res.b_validated_consumable is False
    assert res.n_completeness_level == 1


# ── Level 2 → diagnostic-only ───────────────────────────────────────────────


def test_level2_resolves_diagnostic_only():
    res = _resolve([_rec_level2()], B_T=1.2, f_Hz=50.0)
    assert res.s_status == STATUS_ROTATIONAL_LOSS_DIAGNOSTIC_ONLY
    assert res.b_diagnostic_only is True
    assert res.b_validated_consumable is False


# ── Level 3 admitted source, in range → validated-consumable ────────────────


@pytest.mark.parametrize("conf", ["measured", "datasheet", "standard", "handbook"])
def test_level3_admitted_in_range_is_validated_consumable(conf):
    res = _resolve([_rec_level3(confidence=conf)], B_T=1.25, f_Hz=50.0)
    assert res.s_status == STATUS_ROTATIONAL_LOSS_VALIDATED_CONSUMABLE
    assert res.b_validated_consumable is True
    assert res.b_diagnostic_only is False
    assert res.s_validity_verdict == "in_range"
    assert res.s_confidence == conf


# ── Level 3 Tier-3/4 source → NOT validated-consumable ──────────────────────


@pytest.mark.parametrize("conf", ["aggregator", "derived", "estimated"])
def test_level3_tier34_source_not_validated_consumable(conf):
    res = _resolve([_rec_level3(confidence=conf)], B_T=1.25, f_Hz=50.0)
    assert res.s_status != STATUS_ROTATIONAL_LOSS_VALIDATED_CONSUMABLE
    assert res.s_status == STATUS_ROTATIONAL_LOSS_DIAGNOSTIC_ONLY
    assert res.b_validated_consumable is False


# ── out-of-range B / f / T → out_of_range (validated source) ────────────────


def test_out_of_range_B_returns_out_of_range():
    res = _resolve([_rec_level3()], B_T=2.0, f_Hz=50.0)  # B range (0.5,1.6)
    assert res.s_status == STATUS_ROTATIONAL_LOSS_OUT_OF_RANGE
    assert res.s_validity_verdict == "out_of_range:B"
    assert res.b_validated_consumable is False


def test_out_of_range_frequency_returns_out_of_range():
    res = _resolve([_rec_level3()], B_T=1.25, f_Hz=1000.0)  # f range (10,400)
    assert res.s_status == STATUS_ROTATIONAL_LOSS_OUT_OF_RANGE
    assert res.s_validity_verdict == "out_of_range:f"


def test_out_of_range_temperature_returns_out_of_range():
    rec = _rec_level3(d_validity_temperature_range_C=(20.0, 120.0))
    res = _resolve([rec], B_T=1.25, f_Hz=50.0, temperature_C=200.0)
    assert res.s_status == STATUS_ROTATIONAL_LOSS_OUT_OF_RANGE
    assert res.s_validity_verdict == "out_of_range:T"


def test_temperature_not_queried_does_not_constrain():
    rec = _rec_level3(d_validity_temperature_range_C=(20.0, 120.0))
    # No temperature_C passed → T axis does not constrain → still validated.
    res = _resolve([rec], B_T=1.25, f_Hz=50.0)
    assert res.s_status == STATUS_ROTATIONAL_LOSS_VALIDATED_CONSUMABLE


# ── deterministic multi-record selection ────────────────────────────────────


def test_validated_in_range_beats_diagnostic_in_range():
    recs = [_rec_level2(), _rec_level3(confidence="handbook")]
    res = _resolve(recs, B_T=1.25, f_Hz=50.0)
    assert res.s_status == STATUS_ROTATIONAL_LOSS_VALIDATED_CONSUMABLE
    assert res.n_completeness_level == 3


def test_diagnostic_in_range_beats_validated_out_of_range_but_flags_it():
    # validated record valid only up to B=1.6; diagnostic valid up to 1.5.
    # Query B=1.45: validated is in range too... pick a B where validated is
    # OUT and diagnostic is IN. Validated B-range (0.5,1.6); make a diagnostic
    # whose range covers a point the validated one does not.
    validated = _rec_level3(d_validity_B_range_T=(0.5, 1.2))  # in-range up to 1.2
    diagnostic = _rec_level2(
        d_validity_B_range_T=(1.0, 1.6), d_validity_freq_range_Hz=(10.0, 400.0)
    )
    res = _resolve([validated, diagnostic], B_T=1.5, f_Hz=50.0)
    # validated is out of range at 1.5; diagnostic is in range → diagnostic_only
    assert res.s_status == STATUS_ROTATIONAL_LOSS_DIAGNOSTIC_ONLY
    assert res.b_diagnostic_only is True
    # ...but the result must SURFACE that a validated record exists out of range
    assert "validated-consumable record exists" in res.s_notes


def test_selection_is_deterministic_across_order():
    a = _rec_level3(confidence="handbook", s_source="rec A")
    b = _rec_level3(confidence="measured", s_source="rec B")  # higher conf rank
    r1 = _resolve([a, b], B_T=1.25, f_Hz=50.0)
    r2 = _resolve([b, a], B_T=1.25, f_Hz=50.0)
    # Same record chosen regardless of tuple order (higher confidence wins the
    # tie); both validated_consumable, both cite the measured record.
    assert r1.s_status == r2.s_status == STATUS_ROTATIONAL_LOSS_VALIDATED_CONSUMABLE
    assert r1.s_source == r2.s_source == "rec B"


def test_higher_quality_in_range_not_passed_over():
    """An in-range validated record is never skipped for an in-range diagnostic."""
    res = _resolve([_rec_level3(), _rec_level2()], B_T=1.2, f_Hz=50.0)
    assert res.s_status == STATUS_ROTATIONAL_LOSS_VALIDATED_CONSUMABLE


# ── provenance survives ─────────────────────────────────────────────────────


def test_provenance_survives():
    rec = _rec_level3(s_source="Distinctive synthetic provenance string 42")
    res = _resolve([rec], B_T=1.25, f_Hz=50.0)
    assert res.s_source == "Distinctive synthetic provenance string 42"
    assert res.s_material_as_published == "Synthetic grade X"
    assert res.record is rec


# ── no fallback to alternating Steinmetz ────────────────────────────────────


def test_no_fallback_to_alternating_steinmetz():
    # m19 HAS a SteinmetzData (alternating) but NO rotational data.
    m19 = get_material("m19_silicon_steel")
    assert m19.electromagnetic.steinmetz is not None
    res = resolve_rotational_loss_data_from_material(m19, B_T=1.5, f_Hz=60.0)
    # Resolver must NOT borrow the alternating fit: it reports missing...
    assert res.s_status == STATUS_MISSING_ROTATIONAL_LOSS_DATA
    assert res.record is None
    # ...while honestly flagging that alternating data exists (informational).
    assert res.b_alternating_steinmetz_present is True


def test_alternating_flag_false_when_no_steinmetz():
    # pure_copper has no SteinmetzData; attach a rotational record.
    res = _resolve([_rec_level3()], base_id="pure_copper")
    assert res.b_alternating_steinmetz_present is False


# ── query validation ────────────────────────────────────────────────────────


@pytest.mark.parametrize("bad", [0.0, -1.0, float("inf"), float("nan")])
def test_invalid_B_rejected(bad):
    with pytest.raises(ValueError, match="B_T"):
        _resolve([_rec_level3()], B_T=bad)


@pytest.mark.parametrize("bad", [0.0, -5.0, float("nan")])
def test_invalid_frequency_rejected(bad):
    with pytest.raises(ValueError, match="f_Hz"):
        _resolve([_rec_level3()], f_Hz=bad)


def test_invalid_temperature_rejected():
    with pytest.raises(ValueError, match="temperature_C"):
        _resolve([_rec_level3()], temperature_C=float("inf"))


# ── existing catalog behavior unchanged ─────────────────────────────────────


def test_resolver_contract_is_public():
    """The resolver and its eligibility statuses are importable from their
    module. Version equality is owned by test_catalog_versioning.py."""
    assert callable(resolve_rotational_loss_data_from_material)
    assert ROTATIONAL_RESOLVE_OUTCOMES


def test_catalog_materials_all_resolve_missing_in_phase2():
    """Phase 2 has zero real rotational data, EVERY catalog material resolves
    missing (proof the resolver doesn't hallucinate data)."""
    from emergent_matter_materials import list_materials

    for s_id in list_materials():
        mat = get_material(s_id)
        if mat.electromagnetic is None:
            continue
        res = resolve_rotational_loss_data_from_material(mat, B_T=1.0, f_Hz=50.0)
        assert res.s_status == STATUS_MISSING_ROTATIONAL_LOSS_DATA, (
            f"{s_id} unexpectedly resolved {res.s_status}: no real rotational "
            f"data should exist in Phase 2"
        )
