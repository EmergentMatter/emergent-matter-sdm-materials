"""Rotational-flux core-loss data scaffold (Phase 1: schema only).

This module is the *place* where rotational-loss data could live later. It
adds no real records; it defines the `RotationalLossData` composite, its
validators, the locked status vocabulary, and the materials-side data/source
admissibility gate. Real records, a resolver, RSST ingestion, and the
downstream solver consumer are all FUTURE work (see the implementation sequence
in `docs/adr/0001-rotational-loss-source-policy.md` Decision 6).

**Why rotational loss needs its own type at all.**
A rotating B-locus is a different physical problem from a one-dimensional
alternating waveform. The existing alternating-flux Steinmetz `(k, α, β)`
coefficients (`SteinmetzData`) and DC magnetization curves (`BHCurveData`)
do NOT, by themselves, validate rotational-flux loss. No rotational data →
no validated rotational loss. This type is the contract a future
magnetostatics rotational-loss model would consume.

**Three orthogonal axes** (Phase 0B Decision 2, DO NOT conflate):

- **source-Tier N**: source confidence / origin quality. Stored in
  `s_confidence` (the existing `ConfidenceLevel` enum). source-confidence
  ONLY; never overloaded with completeness or model meaning.
- **Level N**: data completeness. Stored in `n_completeness_level` (0-3).
- **Model-Tier N**: what a downstream solver may DO with the data.
  NOT stored here; computed by the consumer from completeness + source +
  its own model availability.

**Source policy** (Phase 0B Decision 1, Option C, scoped exception).
The catalog is source-Tier-1-only for every normal `PropertyValue`. Rotational
loss is a SCOPED exception: because RSST / rotational data is essentially
never vendor- or standards-published, source-Tier-2 (`handbook`,
peer-reviewed literature) is admissible *for rotational-loss records only*.
The validated-consumable source set is therefore exactly source-Tier-1 ∪
source-Tier-2 = ``{measured, datasheet, standard, handbook}``
(`_VALIDATED_ROTATIONAL_SOURCE_SET`). source-Tier-3/4 (`aggregator`,
`derived`, `estimated`) records may be RECORDED for traceability/diagnostics
but are never validated-consumable.

The exception is enforced *structurally*, not by reviewer vigilance:
rotational data lives in this distinct composite type, never in a
`PropertyValue`. The existing Tier-1 provenance gate
(`tests/test_catalog_provenance_strength.py`) iterates `PropertyValue`
instances and therefore physically never sees a `RotationalLossData`: it is
not relaxed, and the Tier-1 guarantee for every non-rotational property is
untouched. A future, separate rotational provenance gate owns this subdomain.

**Completeness ladder** (Phase 0A §1):

- **Level 0**: citation / insufficient numerical data. `s_form ==
  "citation_only"`; provenance only; no usable numeric payload. Not
  validated-consumable.
- **Level 1**: recordable numerical data, incomplete metadata. Not
  validated-consumable.
- **Level 2**: diagnostic / screening usable. Not validated-consumable.
- **Level 3**: complete enough to be validated-consumable *if* the source
  policy also admits it. Mandatory fields enforced in `__post_init__`.

The Level 1 vs Level 2 distinction is a curator judgement about diagnostic
usefulness (both require numeric payload + a source + at least one
independent variable, and neither is validated-consumable), so the validator
treats them with the same structural minimum. The hard structural gate is
Level 3.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal, get_args

from emergent_matter_materials.property_value import (
    _VALID_CONFIDENCE_LEVELS,
    ConfidenceLevel,
)

# ── Locked vocabulary ───────────────────────────────────────────────────────

#: The data forms a rotational-loss record may take (Phase 0A §2).
RotationalLossForm = Literal[
    "citation_only",  # provenance only, Level 0
    "curve",  # measured P_rot(B[,f]) (e.g. RSST)
    "ratio",  # R(B[,f]) = P_rot / P_alt, dimensionless
    "model_coefficients",  # parameters for a named rotational loss model
    "vector_model",  # parameters for a named vector-hysteresis model
]

#: Runtime counterpart of `RotationalLossForm`, derived with `get_args()` so
#: it can never drift from the Literal (STYLE.md: never hand-copy a Literal's
#: members into a separate tuple/frozenset).
_FORMS: frozenset[str] = frozenset(get_args(RotationalLossForm))

#: Explicit "missing metadata" sentinels (Phase 0A §3). Missing metadata is
#: represented as exactly one of these, NEVER guessed, NEVER left blank.
#:   - not_reported : the source could have stated it but didn't
#:   - unknown      : cannot be determined even by inference
#:   - not_applicable : the field is meaningless for this record
_SENTINELS: frozenset[str] = frozenset(
    {
        "unknown",
        "not_reported",
        "not_applicable",
    }
)

#: String metadata fields that must be represented honestly: non-empty,
#: either real content or a sentinel. Construction with "" is rejected so a
#: blank can never silently stand in for a guess. (s_material_as_published is
#: governed by the per-Level rules instead; s_notes / s_digitization_method /
#: s_model_id may legitimately be empty.)
_HONESTY_TRACKED_STR_FIELDS: tuple[str, ...] = (
    "s_processing_state",
    "s_measurement_method",
    "s_test_geometry",
    "s_waveform_locus",
    "s_uncertainty",
)

#: Source-confidence values admissible to VALIDATED rotational use under the
#: Phase 0B Option-C scoped exception: source-Tier-1 ∪ source-Tier-2.
#: source-Tier-3/4 (aggregator/derived/estimated) are recordable but cap at
#: diagnostic.
_VALIDATED_ROTATIONAL_SOURCE_SET: frozenset[str] = frozenset(
    {
        "measured",
        "datasheet",
        "standard",  # source-Tier 1
        "handbook",  # source-Tier 2 (the scoped exception)
    }
)


# ── Locked status vocabulary (Phase 0B Decision 5) ──────────────────────────
#
# Materials/resolver statuses. NO resolver is wired in Phase 1: these are
# defined here so the FUTURE resolver and downstream solvers share
# exact strings (the v1.3.0→v1.3.1 pyproject-drift episode is the standing
# reminder that cross-repo string contracts are worth pinning early).

STATUS_MISSING_ROTATIONAL_LOSS_DATA: str = "missing_rotational_loss_data"
STATUS_ROTATIONAL_LOSS_OUT_OF_RANGE: str = "rotational_loss_out_of_range"
STATUS_ROTATIONAL_LOSS_INCOMPLETE: str = "rotational_loss_incomplete"
STATUS_ROTATIONAL_LOSS_DIAGNOSTIC_ONLY: str = "rotational_loss_diagnostic_only"

#: The four LOCKED (Phase 0B Decision 5) blocked/diagnostic resolver statuses.
#: Frozen: do not extend this set (a test asserts it is exactly these four).
ROTATIONAL_RESOLVER_STATUSES: frozenset[str] = frozenset(
    {
        STATUS_MISSING_ROTATIONAL_LOSS_DATA,
        STATUS_ROTATIONAL_LOSS_OUT_OF_RANGE,
        STATUS_ROTATIONAL_LOSS_INCOMPLETE,
        STATUS_ROTATIONAL_LOSS_DIAGNOSTIC_ONLY,
    }
)

#: Success status, added in the rotational-loss Phase 2 resolver. CONSERVATIVE
#: meaning: the record is data/source ELIGIBLE for validated rotational use at
#: the queried operating point (completeness Level 3 AND admitted source AND in
#: range). It does NOT mean a loss number was computed: no loss math exists on
#: the materials side. Kept out of ROTATIONAL_RESOLVER_STATUSES so that locked
#: 4-set stays exactly as Phase 0B froze it.
STATUS_ROTATIONAL_LOSS_VALIDATED_CONSUMABLE: str = "rotational_loss_validated_consumable"

#: Every status the Phase 2 resolver can return = the locked four + the Phase 2
#: success status.
ROTATIONAL_RESOLVE_OUTCOMES: frozenset[str] = ROTATIONAL_RESOLVER_STATUSES | {
    STATUS_ROTATIONAL_LOSS_VALIDATED_CONSUMABLE
}

#: Solver-side cell disposition. Owned by the magnetostatic FEM solver, NOT by this
#: repo: documented here only so the relationship is discoverable: a rotating
#: cell is dispositioned ``rotational_flux_not_modeled`` BECAUSE the materials
#: resolver returned one of the statuses above (cause → effect).
MAGNETOSTATICS_DISPOSITION_ROTATIONAL_NOT_MODELED: str = "rotational_flux_not_modeled"


@dataclass(frozen=True)
class RotationalLossData:
    """One rotational-flux core-loss record with provenance + completeness.

    Additive composite for the future field
    ``Electromagnetic.rotational_loss_models: tuple[RotationalLossData, ...]``.
    Follows the `BHCurveData` / `SteinmetzData` precedent: frozen, own
    provenance, own `__post_init__` validators, consumed via the object path
    (never the flat `get()` accessor), excluded from `_validate_group_units`
    and from `to_jax_pytree`.

    Phase 1 adds the type only. No real records, no resolver, no loss math.

    Required (no default):
      - ``s_form``: one of `_FORMS`.
      - ``n_completeness_level``: 0..3 (the completeness axis; NOT source
        confidence).
      - ``s_source``: non-empty Tier-1-or-Tier-2 citation.
      - ``s_confidence``: source confidence (the existing `ConfidenceLevel`
        enum). source-quality ONLY; never overloaded.

    Form-specific payload (exactly the fields its form needs; others must be
    absent, enforced):
      - ``curve``: ``d_B_table_T`` + ``d_P_rot_table_W_per_kg`` (+ optional
        ``d_f_table_Hz``), row-aligned (index i is one measurement point).
      - ``ratio``: ``d_B_table_T`` + ``d_ratio_table`` (+ optional
        ``d_f_table_Hz``), row-aligned. ``d_ratio_table`` is dimensionless
        R = P_rot / P_alt.
      - ``model_coefficients`` / ``vector_model``: ``s_model_id`` +
        ``model_coefficients`` (the model identity is part of the contract:
        coefficients are meaningless without the equation they parameterize).
      - ``citation_only``: NO payload (Level 0 only).

    Validity limits (mandatory at Level 3 for B and f; optional below):
      - ``d_validity_B_range_T``, ``d_validity_freq_range_Hz``,
        ``d_validity_temperature_range_C``.

    Metadata (honest-or-sentinel; numeric None == not reported):
      - ``s_material_as_published``: the source's own material naming
        (required real content at Level 3; may be empty below while
        normalization is pending).
      - ``d_lamination_thickness_m``, ``d_temperature_C``: None == not
        reported.
      - ``s_processing_state``, ``s_measurement_method``, ``s_test_geometry``,
        ``s_waveform_locus``, ``s_uncertainty``: must be real content or a
        sentinel (`unknown` / `not_reported` / `not_applicable`); blank is
        rejected.
      - ``s_digitization_method``: empty == table-published; non-empty ==
        graph-derived (mirrors `BHCurveData`; RSST curves are often
        graph-only in papers).
      - ``s_notes``: free-form.
    """

    # ── required ──
    s_form: RotationalLossForm
    n_completeness_level: int
    s_source: str
    s_confidence: ConfidenceLevel

    # ── form-specific payload (default absent) ──
    d_B_table_T: tuple[float, ...] | None = None
    d_f_table_Hz: tuple[float, ...] | None = None
    d_P_rot_table_W_per_kg: tuple[float, ...] | None = None
    d_ratio_table: tuple[float, ...] | None = None
    s_model_id: str = ""
    model_coefficients: tuple[tuple[str, float], ...] | None = None

    # ── validity limits ──
    d_validity_B_range_T: tuple[float, float] | None = None
    d_validity_freq_range_Hz: tuple[float, float] | None = None
    d_validity_temperature_range_C: tuple[float, float] | None = None

    # ── metadata ──
    s_material_as_published: str = ""
    d_lamination_thickness_m: float | None = None
    d_temperature_C: float | None = None
    s_processing_state: str = "not_reported"
    s_measurement_method: str = "not_reported"
    s_test_geometry: str = "not_reported"
    s_waveform_locus: str = "unknown"
    s_uncertainty: str = "not_reported"
    s_digitization_method: str = ""
    s_notes: str = ""

    # ── validators ──────────────────────────────────────────────────────────

    def __post_init__(self) -> None:
        # (1) form
        if self.s_form not in _FORMS:
            raise ValueError(
                f"RotationalLossData.s_form must be one of {sorted(_FORMS)}, got {self.s_form!r}"
            )

        # (2) completeness level: int 0..3 (reject bool, which is an int subclass)
        if isinstance(self.n_completeness_level, bool) or self.n_completeness_level not in (
            0,
            1,
            2,
            3,
        ):
            raise ValueError(
                f"RotationalLossData.n_completeness_level must be int 0..3, "
                f"got {self.n_completeness_level!r}"
            )

        # (3) source non-empty
        if not (isinstance(self.s_source, str) and self.s_source.strip()):
            raise ValueError("RotationalLossData.s_source must be a non-empty citation.")

        # (4) source confidence is a valid enum value (source-quality axis)
        if self.s_confidence not in _VALID_CONFIDENCE_LEVELS:
            raise ValueError(
                f"RotationalLossData.s_confidence must be a ConfidenceLevel "
                f"({sorted(_VALID_CONFIDENCE_LEVELS)}), got {self.s_confidence!r}"
            )

        # (5) metadata honesty: tracked string fields must be non-empty
        #     (real content or a sentinel); blank is rejected so it can never
        #     silently stand in for a guess.
        for fname in _HONESTY_TRACKED_STR_FIELDS:
            v = getattr(self, fname)
            if not (isinstance(v, str) and v.strip()):
                raise ValueError(
                    f"RotationalLossData.{fname} must be non-empty: represent "
                    f"missing metadata explicitly as one of {sorted(_SENTINELS)} "
                    f"(or give real content). Blank is rejected (no silent guess)."
                )

        # (6) form <-> completeness coupling
        if self.s_form == "citation_only" and self.n_completeness_level != 0:
            raise ValueError(
                "citation_only form requires n_completeness_level == 0 "
                "(citation/insufficient-data only)."
            )
        if self.n_completeness_level == 0 and self.s_form != "citation_only":
            raise ValueError(
                "Level 0 requires s_form == 'citation_only' (no usable numeric "
                "payload). A form carrying numeric data is Level >= 1."
            )

        # (7) payload presence per form
        has_any_table = any(
            t is not None
            for t in (
                self.d_B_table_T,
                self.d_f_table_Hz,
                self.d_P_rot_table_W_per_kg,
                self.d_ratio_table,
            )
        )
        has_model = bool(self.s_model_id.strip()) or self.model_coefficients is not None

        if self.s_form == "citation_only":
            if has_any_table or has_model:
                raise ValueError(
                    "citation_only must carry NO numeric payload and NO model "
                    "coefficients (it is provenance-only)."
                )
        elif self.s_form == "curve":
            if self.d_B_table_T is None or self.d_P_rot_table_W_per_kg is None:
                raise ValueError("curve form requires d_B_table_T and d_P_rot_table_W_per_kg.")
            if self.d_ratio_table is not None or has_model:
                raise ValueError("curve form must not carry d_ratio_table or model coefficients.")
        elif self.s_form == "ratio":
            if self.d_B_table_T is None or self.d_ratio_table is None:
                raise ValueError(
                    "ratio form requires d_B_table_T and d_ratio_table "
                    "(dimensionless R = P_rot / P_alt)."
                )
            if self.d_P_rot_table_W_per_kg is not None or has_model:
                raise ValueError("ratio form must not carry a P_rot curve or model coefficients.")
        else:  # model_coefficients / vector_model
            if not self.s_model_id.strip() or self.model_coefficients is None:
                raise ValueError(
                    f"{self.s_form} form requires s_model_id and "
                    f"model_coefficients (the model identity is part of the "
                    f"contract)."
                )
            if has_any_table:
                raise ValueError(f"{self.s_form} form must not carry numeric tables.")

        # (8) numeric-table integrity: finite, positive, row-aligned
        present_tables: list[tuple[str, tuple[float, ...]]] = []
        for fname, t in (
            ("d_B_table_T", self.d_B_table_T),
            ("d_f_table_Hz", self.d_f_table_Hz),
            ("d_P_rot_table_W_per_kg", self.d_P_rot_table_W_per_kg),
            ("d_ratio_table", self.d_ratio_table),
        ):
            if t is None:
                continue
            if len(t) < 1:
                raise ValueError(f"RotationalLossData.{fname} must have >= 1 point.")
            for x in t:
                if not (isinstance(x, (int, float)) and math.isfinite(x)):
                    raise ValueError(f"RotationalLossData.{fname} has non-finite value {x!r}.")
                if x <= 0.0:
                    raise ValueError(
                        f"RotationalLossData.{fname} values must be positive "
                        f"(B, f, P_rot, and the R ratio are all > 0), got {x}."
                    )
            present_tables.append((fname, t))
        if present_tables and len({len(t) for _, t in present_tables}) != 1:
            raise ValueError(
                "RotationalLossData numeric tables must be row-aligned "
                "(equal length, index i is one measurement point): "
                + ", ".join(f"{n}={len(t)}" for n, t in present_tables)
            )

        # model_coefficients integrity
        if self.model_coefficients is not None:
            for pair in self.model_coefficients:
                if not (
                    isinstance(pair, tuple)
                    and len(pair) == 2
                    and isinstance(pair[0], str)
                    and isinstance(pair[1], (int, float))
                    and not isinstance(pair[1], bool)
                ):
                    raise ValueError(
                        "RotationalLossData.model_coefficients must be a tuple "
                        "of (name: str, value: float) pairs, got "
                        f"{pair!r}."
                    )

        # (9) validity-range integrity
        for fname, rng, allow_negative in (
            ("d_validity_B_range_T", self.d_validity_B_range_T, False),
            ("d_validity_freq_range_Hz", self.d_validity_freq_range_Hz, False),
            ("d_validity_temperature_range_C", self.d_validity_temperature_range_C, True),
        ):
            if rng is None:
                continue
            if len(rng) != 2:
                raise ValueError(f"RotationalLossData.{fname} must be (lo, hi).")
            lo, hi = rng
            if not (math.isfinite(lo) and math.isfinite(hi)):
                raise ValueError(f"RotationalLossData.{fname} bounds must be finite.")
            if not allow_negative and lo < 0.0:
                raise ValueError(f"RotationalLossData.{fname} lower bound must be >= 0.")
            if not lo < hi:
                raise ValueError(f"RotationalLossData.{fname} must have lo < hi, got {rng}.")

        # numeric-metadata sanity (when present)
        if self.d_lamination_thickness_m is not None and (
            not (
                math.isfinite(self.d_lamination_thickness_m) and self.d_lamination_thickness_m > 0.0
            )
        ):
            raise ValueError(
                "RotationalLossData.d_lamination_thickness_m must be positive "
                "when given (use None for not-reported)."
            )
        if self.d_temperature_C is not None and not math.isfinite(self.d_temperature_C):
            raise ValueError(
                "RotationalLossData.d_temperature_C must be finite when given "
                "(use None for not-reported)."
            )

        # (10) Level-3 strict mandatory gate: the nine admission guardrails
        #      (Phase 0B Decision 1.1). source-Tier does NOT lower this bar;
        #      a Tier-2 record must clear full Level 3 exactly as Tier-1 would.
        if self.n_completeness_level == 3:
            problems: list[str] = []
            if not (
                self.s_material_as_published.strip()
                and self.s_material_as_published not in _SENTINELS
            ):
                problems.append(
                    "s_material_as_published must be real content "
                    "(material identity/grade sufficiently clear)"
                )
            if self.d_validity_B_range_T is None:
                problems.append("d_validity_B_range_T required (flux-density range known)")
            if self.d_validity_freq_range_Hz is None:
                problems.append("d_validity_freq_range_Hz required (frequency range known)")
            if self.s_measurement_method in _SENTINELS:
                problems.append(
                    "s_measurement_method must name the method/experiment "
                    "context (not a sentinel) at Level 3"
                )
            # payload presence is already enforced per-form above; citation_only
            # cannot reach Level 3 (form<->level coupling), so a Level-3 record
            # necessarily carries a numeric/model payload.
            if problems:
                raise ValueError(
                    "Level 3 (validated-consumable) record is missing mandatory "
                    "fields: " + "; ".join(problems) + ". Lower n_completeness_"
                    "level to record it honestly, or supply the missing fields."
                )

    # ── materials-side data/source admissibility gates ────────────────────────
    #
    # NEITHER of these computes loss or asserts a solver-side loss model is
    # correct. They apply ONLY the materials-side data + source gate. The
    # Model-Tier the consumer ultimately assigns also depends on the
    # consumer's own model availability.

    @property
    def b_source_admissible(self) -> bool:
        """True iff the SOURCE confidence is in the validated rotational set
        ``{measured, datasheet, standard, handbook}`` (source-Tier 1 ∪ 2).

        Source-confidence gate ONLY: ignores completeness. source-Tier-3/4
        (`aggregator` / `derived` / `estimated`) returns False (recordable for
        traceability/diagnostics, never validated-consumable).
        """
        return self.s_confidence in _VALIDATED_ROTATIONAL_SOURCE_SET

    @property
    def b_validated_consumable(self) -> bool:
        """True iff this record may feed a VALIDATED rotational-loss number on
        the materials side: completeness Level 3 AND `b_source_admissible`.

        This is the materials-side DATA + SOURCE gate only. It does NOT compute
        loss and does NOT assert that any solver-side loss model is valid:
        Model-Tier 2 additionally requires the consumer's own model. A False
        result means the record is recordable and/or diagnostic-only.
        """
        return self.n_completeness_level == 3 and self.b_source_admissible


__all__ = [
    "MAGNETOSTATICS_DISPOSITION_ROTATIONAL_NOT_MODELED",
    "ROTATIONAL_RESOLVER_STATUSES",
    "ROTATIONAL_RESOLVE_OUTCOMES",
    "STATUS_MISSING_ROTATIONAL_LOSS_DATA",
    "STATUS_ROTATIONAL_LOSS_DIAGNOSTIC_ONLY",
    "STATUS_ROTATIONAL_LOSS_INCOMPLETE",
    "STATUS_ROTATIONAL_LOSS_OUT_OF_RANGE",
    "STATUS_ROTATIONAL_LOSS_VALIDATED_CONSUMABLE",
    "RotationalLossData",
    "RotationalLossForm",
]
