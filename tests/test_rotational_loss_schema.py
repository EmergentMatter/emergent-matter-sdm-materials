"""Tests for the RotationalLossData scaffold (rotational-loss Phase 1).

Schema-only phase: these tests use SYNTHETIC records exclusively. No real
rotational-loss data exists in the catalog yet (every material's
``rotational_loss_models`` is the default empty tuple). The tests prove:

- the three axes stay separate (source confidence / completeness Level /
  consumability), never collapsed;
- Option C's scoped source policy is enforced (validated source set =
  {measured, datasheet, standard, handbook}; Tier-3/4 recordable but not
  validated-consumable);
- the completeness ladder (Level 0-3) classifies and gates correctly;
- metadata honesty is enforced (blank rejected; sentinels accepted);
- inconsistent form/payload combinations are rejected;
- the additive field does not perturb existing catalog behavior, the flat
  accessor map, the units validator, or the JAX pytree.
"""

from __future__ import annotations

import dataclasses

import pytest

from emergent_matter_materials import (
    Electromagnetic,
    RotationalLossData,
    get_material,
)
from emergent_matter_materials.accessors import _PROPERTY_MAP
from emergent_matter_materials.property_value import PropertyValue as PV
from emergent_matter_materials.rotational_loss import (
    ROTATIONAL_RESOLVER_STATUSES,
    STATUS_MISSING_ROTATIONAL_LOSS_DATA,
    STATUS_ROTATIONAL_LOSS_DIAGNOSTIC_ONLY,
    STATUS_ROTATIONAL_LOSS_INCOMPLETE,
    STATUS_ROTATIONAL_LOSS_OUT_OF_RANGE,
)

# ── fixtures / helpers ──────────────────────────────────────────────────────


def _l3_curve(**over):
    """A valid Level-3, validated-consumable `curve` record; overridable."""
    base = {
        "s_form": "curve",
        "n_completeness_level": 3,
        "s_source": "Synthetic RSST fixture, not a real measurement.",
        "s_confidence": "handbook",
        "d_B_table_T": (1.0, 1.25, 1.5),
        "d_f_table_Hz": (50.0, 50.0, 50.0),
        "d_P_rot_table_W_per_kg": (3.0, 4.2, 5.5),
        "d_validity_B_range_T": (0.5, 1.6),
        "d_validity_freq_range_Hz": (10.0, 400.0),
        "s_material_as_published": "Synthetic NO Si-Fe grade X",
        "s_measurement_method": "RSST circular-locus (synthetic)",
    }
    base.update(over)
    return base


# ── Gate 2/3: existing records + default empty tuple ────────────────────────


def test_existing_material_has_empty_rotational_models():
    """Existing catalog materials carry no rotational data (default empty)."""
    m19 = get_material("m19_silicon_steel")
    assert m19.electromagnetic.rotational_loss_models == ()


def test_default_rotational_models_is_empty_tuple():
    em = Electromagnetic()
    assert em.rotational_loss_models == ()
    assert isinstance(em.rotational_loss_models, tuple)


def test_bare_electromagnetic_still_constructs():
    """Adding the field must not make the empty group harder to build."""
    assert Electromagnetic().rotational_loss_models == ()


# ── Gate 4: Level 0 citation-only ───────────────────────────────────────────


def test_level0_citation_only_validates():
    rec = RotationalLossData(
        s_form="citation_only",
        n_completeness_level=0,
        s_source="Author et al., 'Rotational loss in NO steel', IEEE TMAG (synthetic).",
        s_confidence="handbook",
        s_notes="Abstract mentions rotational loss exceeds alternating near 1.5 T.",
    )
    assert rec.n_completeness_level == 0
    assert rec.b_validated_consumable is False
    assert rec.b_source_admissible is True  # source is fine; completeness is not


# ── Gate 5: Level 1 recordable with honest incomplete metadata ──────────────


def test_level1_recordable_with_honest_missing_metadata():
    rec = RotationalLossData(
        s_form="curve",
        n_completeness_level=1,
        s_source="Synthetic single-frequency rotational curve.",
        s_confidence="handbook",
        d_B_table_T=(1.0, 1.2, 1.4),
        d_P_rot_table_W_per_kg=(2.0, 3.0, 4.0),
        # incomplete metadata represented HONESTLY, not guessed:
        s_processing_state="not_reported",
        s_test_geometry="not_reported",
        s_uncertainty="not_reported",
        s_waveform_locus="unknown",
        d_lamination_thickness_m=None,  # None == not reported
        d_temperature_C=None,
    )
    assert rec.n_completeness_level == 1
    assert rec.b_validated_consumable is False
    # missing metadata is represented honestly (sentinels / None), not guessed:
    assert rec.s_processing_state == "not_reported"
    assert rec.d_lamination_thickness_m is None
    assert rec.d_temperature_C is None


# ── Gate 6: Level 2 diagnostic, not validated-consumable ────────────────────


def test_level2_diagnostic_not_validated_consumable():
    rec = RotationalLossData(
        s_form="ratio",
        n_completeness_level=2,
        s_source="Synthetic R(B) screening ratio at one frequency.",
        s_confidence="measured",  # even a Tier-1 source...
        d_B_table_T=(1.0, 1.3, 1.5),
        d_ratio_table=(1.6, 1.9, 1.4),  # R peaks then falls toward saturation
    )
    assert rec.b_source_admissible is True
    # ...is still NOT validated-consumable because completeness < Level 3:
    assert rec.b_validated_consumable is False


# ── Gate 7: Level 3 + validated source set → validated-consumable ───────────


@pytest.mark.parametrize("conf", ["measured", "datasheet", "standard", "handbook"])
def test_level3_validated_source_is_consumable(conf):
    rec = RotationalLossData(**_l3_curve(s_confidence=conf))
    assert rec.b_source_admissible is True
    assert rec.b_validated_consumable is True


# ── Gate 8: Level 3 + Tier-3/4 source → recordable but NOT consumable ───────


@pytest.mark.parametrize("conf", ["aggregator", "derived", "estimated"])
def test_level3_tier34_source_recordable_but_not_consumable(conf):
    # The record still CONSTRUCTS (recordable for traceability/diagnostics)...
    rec = RotationalLossData(**_l3_curve(s_confidence=conf))
    assert rec.n_completeness_level == 3
    # ...but the scoped Option-C policy bars it from validated use:
    assert rec.b_source_admissible is False
    assert rec.b_validated_consumable is False


def test_axes_do_not_collapse():
    """Source-admissible and validated-consumable are distinct axes."""
    # Tier-1 source but only Level 2: source-admissible True, consumable False.
    diag = RotationalLossData(**_l3_curve(s_confidence="measured", n_completeness_level=2))
    assert diag.b_source_admissible is True
    assert diag.b_validated_consumable is False
    # Level 3 but aggregator source: source-admissible False, consumable False.
    agg = RotationalLossData(**_l3_curve(s_confidence="aggregator"))
    assert agg.b_source_admissible is False
    assert agg.b_validated_consumable is False


# ── Gate 9: metadata honesty, blanks rejected, sentinels accepted ──────────


@pytest.mark.parametrize(
    "field",
    [
        "s_processing_state",
        "s_measurement_method",
        "s_test_geometry",
        "s_waveform_locus",
        "s_uncertainty",
    ],
)
def test_blank_metadata_rejected(field):
    with pytest.raises(ValueError, match="must be non-empty"):
        RotationalLossData(**_l3_curve(**{field: "   "}))


@pytest.mark.parametrize("sentinel", ["unknown", "not_reported", "not_applicable"])
def test_sentinels_accepted_for_metadata(sentinel):
    # Use a Level-1 record so s_measurement_method may legitimately be a
    # sentinel (Level 3 requires a real method, tested separately).
    rec = RotationalLossData(
        s_form="curve",
        n_completeness_level=1,
        s_source="synthetic",
        s_confidence="handbook",
        d_B_table_T=(1.0, 1.5),
        d_P_rot_table_W_per_kg=(3.0, 5.0),
        s_processing_state=sentinel,
        s_measurement_method=sentinel,
        s_test_geometry=sentinel,
        s_waveform_locus=sentinel,
        s_uncertainty=sentinel,
    )
    assert rec.s_test_geometry == sentinel


def test_level3_requires_real_measurement_method_not_sentinel():
    with pytest.raises(ValueError, match="measurement_method"):
        RotationalLossData(**_l3_curve(s_measurement_method="not_reported"))


def test_level3_requires_material_identity():
    with pytest.raises(ValueError, match="material_as_published"):
        RotationalLossData(**_l3_curve(s_material_as_published=""))


def test_level3_requires_validity_ranges():
    with pytest.raises(ValueError, match="d_validity_B_range_T required"):
        RotationalLossData(**_l3_curve(d_validity_B_range_T=None))
    with pytest.raises(ValueError, match="d_validity_freq_range_Hz required"):
        RotationalLossData(**_l3_curve(d_validity_freq_range_Hz=None))


# ── Gate 10: inconsistent form/payload combinations rejected ────────────────


def test_citation_only_with_payload_rejected():
    with pytest.raises(ValueError, match="citation_only"):
        RotationalLossData(
            s_form="citation_only",
            n_completeness_level=0,
            s_source="x",
            s_confidence="handbook",
            d_B_table_T=(1.0, 1.5),
            d_P_rot_table_W_per_kg=(3.0, 5.0),
        )


def test_level0_requires_citation_only_form():
    with pytest.raises(ValueError, match="Level 0 requires"):
        RotationalLossData(
            s_form="curve",
            n_completeness_level=0,
            s_source="x",
            s_confidence="handbook",
            d_B_table_T=(1.0, 1.5),
            d_P_rot_table_W_per_kg=(3.0, 5.0),
        )


def test_curve_missing_payload_rejected():
    with pytest.raises(ValueError, match="curve form requires"):
        RotationalLossData(
            s_form="curve",
            n_completeness_level=1,
            s_source="x",
            s_confidence="handbook",
            d_B_table_T=(1.0, 1.5),  # missing d_P_rot_table_W_per_kg
        )


def test_ratio_with_model_coefficients_rejected():
    with pytest.raises(ValueError, match="ratio form"):
        RotationalLossData(
            s_form="ratio",
            n_completeness_level=1,
            s_source="x",
            s_confidence="handbook",
            d_B_table_T=(1.0, 1.5),
            d_ratio_table=(1.6, 1.4),
            s_model_id="something",
            model_coefficients=(("a", 1.0),),
        )


def test_model_form_requires_model_id_and_coeffs():
    with pytest.raises(ValueError, match="model_coefficients|model_id"):
        RotationalLossData(
            s_form="model_coefficients",
            n_completeness_level=2,
            s_source="x",
            s_confidence="handbook",
            s_model_id="",  # missing
            model_coefficients=None,  # missing
        )


def test_misaligned_tables_rejected():
    with pytest.raises(ValueError, match="row-aligned"):
        RotationalLossData(
            s_form="curve",
            n_completeness_level=1,
            s_source="x",
            s_confidence="handbook",
            d_B_table_T=(1.0, 1.5),
            d_P_rot_table_W_per_kg=(3.0, 5.0, 7.0),  # length mismatch
        )


def test_nonpositive_table_value_rejected():
    with pytest.raises(ValueError, match="must be positive"):
        RotationalLossData(
            s_form="curve",
            n_completeness_level=1,
            s_source="x",
            s_confidence="handbook",
            d_B_table_T=(0.0, 1.5),  # B must be > 0
            d_P_rot_table_W_per_kg=(3.0, 5.0),
        )


def test_inverted_validity_range_rejected():
    with pytest.raises(ValueError, match="lo < hi"):
        RotationalLossData(**_l3_curve(d_validity_freq_range_Hz=(400.0, 10.0)))


def test_valid_model_coefficients_form():
    rec = RotationalLossData(
        s_form="model_coefficients",
        n_completeness_level=2,
        s_source="Synthetic rotational model params.",
        s_confidence="handbook",
        s_model_id="two_term_rotational_v0",
        model_coefficients=(("k_r", 1.3e-3), ("p", 1.8)),
    )
    assert rec.b_validated_consumable is False  # Level 2
    assert rec.model_coefficients[0] == ("k_r", 1.3e-3)


# ── Gate 11: not in the flat _PROPERTY_MAP ──────────────────────────────────


def test_rotational_models_not_in_property_map():
    assert "rotational_loss_models" not in _PROPERTY_MAP
    # and no rotational key sneaked in:
    assert not any("rotational" in k for k in _PROPERTY_MAP)


# ── Gate 12: _validate_group_units does not crash on the composite ──────────


def test_units_validator_tolerates_rotational_field():
    # Construct an Electromagnetic that has BOTH a units-validated PV field
    # AND a rotational record. If _validate_group_units tried to read
    # .s_units on the tuple/composite this would raise.
    em = Electromagnetic(
        saturation_flux=PV(d_value=1.5, s_units="T", s_source="x", s_confidence="datasheet"),
        rotational_loss_models=(RotationalLossData(**_l3_curve()),),
    )
    assert em.d_saturation_flux_T == 1.5
    assert len(em.rotational_loss_models) == 1


def test_non_record_in_tuple_rejected():
    with pytest.raises(ValueError, match="RotationalLossData instances"):
        Electromagnetic(rotational_loss_models=("not a record",))


def test_non_tuple_rejected():
    with pytest.raises(ValueError, match="must be a tuple"):
        Electromagnetic(rotational_loss_models=[RotationalLossData(**_l3_curve())])


# ── Gate 13: to_jax_pytree safely omits rotational data ─────────────────────


def test_to_jax_pytree_omits_rotational_data():
    pytest.importorskip("jax")
    from emergent_matter_materials.jax_interop import to_jax_pytree

    m19 = get_material("m19_silicon_steel")
    em2 = dataclasses.replace(
        m19.electromagnetic,
        rotational_loss_models=(RotationalLossData(**_l3_curve()),),
    )
    m2 = dataclasses.replace(m19, electromagnetic=em2)
    tree = to_jax_pytree(m2, s_missing="omit")

    # rotational data is intentionally NOT flattened into the pytree...
    assert "rotational_loss_models" not in tree["electromagnetic"]
    # ...but the existing composite (steinmetz) and scalars still flatten:
    assert "steinmetz" in tree["electromagnetic"]
    assert "resistivity_at_20C" in tree["electromagnetic"]


# ── Gate 14: no existing alternating / B-H behavior changes ─────────────────


def test_existing_steinmetz_and_bh_unchanged():
    m19 = get_material("m19_silicon_steel").electromagnetic
    # Steinmetz round-trip still exact:
    k, a, b = m19.d_steinmetz_k, m19.d_steinmetz_alpha, m19.d_steinmetz_beta
    assert k * 60.0**a * 1.5**b == pytest.approx(3.42, rel=1e-12)
    # B-H curve still the 16-point DC table:
    assert len(m19.d_bh_curve_B_T) == 16
    assert m19.d_bh_curve_B_T[-1] == pytest.approx(2.1)


# ── status vocabulary present + exact (cross-repo contract) ─────────────────


def test_scaffold_is_public_and_attached_to_the_electromagnetic_group():
    """The rotational-loss scaffold is exported and reachable from every
    material's electromagnetic group. Version equality is owned by
    test_catalog_versioning.py."""
    assert dataclasses.is_dataclass(RotationalLossData)
    assert "rotational_loss_models" in {f.name for f in dataclasses.fields(Electromagnetic)}


def test_status_strings_are_exact():
    assert STATUS_MISSING_ROTATIONAL_LOSS_DATA == "missing_rotational_loss_data"
    assert STATUS_ROTATIONAL_LOSS_OUT_OF_RANGE == "rotational_loss_out_of_range"
    assert STATUS_ROTATIONAL_LOSS_INCOMPLETE == "rotational_loss_incomplete"
    assert STATUS_ROTATIONAL_LOSS_DIAGNOSTIC_ONLY == "rotational_loss_diagnostic_only"
    assert {
        "missing_rotational_loss_data",
        "rotational_loss_out_of_range",
        "rotational_loss_incomplete",
        "rotational_loss_diagnostic_only",
    } == ROTATIONAL_RESOLVER_STATUSES
