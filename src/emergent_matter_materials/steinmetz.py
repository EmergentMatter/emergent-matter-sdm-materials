"""Steinmetz core-loss coefficients for soft-magnetic materials (v1.3.0).

`SteinmetzData` stores a calibrated single-frequency Steinmetz triple
`(k, alpha, beta)` along with the reference operating point the fit
was anchored on and full provenance (s_source, s_calibration_method,
s_condition, s_notes). It is a composite field on `Electromagnetic`
for materials where a downstream FEM consumer needs to evaluate
specific core loss as

    P_core_specific [W/kg] = k · f^alpha · B_pk^beta

at arbitrary `(f, B_pk)` inside the calibration's validity range.

Why a dedicated dataclass instead of three independent `PropertyValue`
fields:

1. The triple `(k, alpha, beta)` is one calibration object, not three
   independent measurements. They share one source, one
   reference-point condition, one confidence. Splitting them into
   three PropertyValues would either duplicate the provenance or
   leave two of the three with `s_source = "see steinmetz_k"`,
   which the catalog's per-property provenance discipline forbids.
2. `k`'s units are non-trivial: `[W/kg] / (Hz^alpha · T^beta)`. The
   string depends on the values of `alpha` and `beta`, so no fixed
   `s_units` can be enforced by `_validate_group_units`. A
   composite dataclass with an internal round-trip validator is a
   better fit than three loose PropertyValues with a forced
   placeholder unit string.
3. Matches the `BHCurveData` (v1.2.0) precedent for "composite
   multi-valued physics with its own provenance + own validators."

Calibration policy (initial v1.3.0):

- **Single-point literature alpha/beta**: when the catalog has one
  measured `(P_ref, f_ref, B_ref)` point (e.g. M19 silicon steel's
  3.42 W/kg at 1.5 T, 60 Hz from Cleveland-Cliffs DI-MAX 2023), fix
  `alpha` and `beta` from literature-typical values for the material
  class (NO Si-Fe: alpha commonly 1.5-1.7, beta ~2; the v1.3.0
  'Pyrhönen Table 3.2' attribution was retracted in v1.3.1 as
  unverifiable) and compute `k = P_ref / (f_ref^alpha · B_ref^beta)`
  from the reference triple. The round-trip
  `k · f_ref^alpha · B_ref^beta == P_ref` is the source of truth
  and is enforced in `__post_init__`.
- **Multi-point fitted** (implemented v1.4.0 for M270-35A and
  Hiperco 50), "grid-fitted exponents, anchor-derived k":
  `(alpha, beta)` from a free log-space least-squares fit of
  `ln P = c + alpha·ln f + beta·ln B` over the vendor's published
  multi-frequency loss grid (see `scripts/fit_steinmetz.py` for the
  reproducible fit), then `k` RE-DERIVED in catalog code from the
  grade-defining reference point so the round-trip validator passes
  exactly at the anchor. Grid residual statistics (RMS / worst
  relative error) are recorded in `s_notes`: a single power law
  cannot capture the f·B interaction across wide grids, so expect
  ~10-25% at window corners.
- **Production** (reserved): for fits externally validated against
  an FEM core-loss reference or a vendor's reference motor.

Out of scope for v1.3 (deferred): Bertotti separation
`(k_h, k_c, k_e)`, PWM ripple losses, strand-eddy / proximity
coefficients, temperature-dependence of `k`, anisotropic loss.

This dataclass is **consumed by** a downstream magnetostatic FEM
solver's materials adapter, which reads the catalog Material and
returns `(k, alpha, beta, provenance)` to its core-loss kernel.
The reader uses `getattr(em, "d_steinmetz_k", None)` on the
`Electromagnetic` group, so the catalog exposes float accessors
`d_steinmetz_k` / `d_steinmetz_alpha` / `d_steinmetz_beta` on
`Electromagnetic` that delegate to this composite.

**Field naming: `s_calibration_method` (renamed from `s_confidence`).**
This field holds CALIBRATION-METHOD labels
(`"single_point_literature_alpha_beta"`, `"multi_point_fitted"`,
`"production"`), which is semantically distinct from how the rest of
the catalog uses `s_confidence`, i.e., SOURCE-QUALITY labels
(`"datasheet"`, `"standard"`, `"measured"`, etc.). The two concepts are
orthogonal, and this file's source-quality tier is captured separately
by the parent `Electromagnetic.core_loss.s_confidence` PropertyValue
("datasheet" for M19's 3.42 W/kg anchor from Cleveland-Cliffs DI-MAX
2023).

The field shipped as `s_confidence` in v1.3.0 to match the consumer-side
brief verbatim, and was renamed to remove the naming overload.
`s_confidence` remains a deprecated alias for one release cycle: passing
it to the constructor, or reading it as an attribute, emits a
`DeprecationWarning` and maps to `s_calibration_method`. The alias is
removed in the next MAJOR release.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from typing import Any, Literal, get_args

#: `s_calibration_method` values. Three calibration regimes, mirroring the
#: consumer-side loss-data brief that motivated v1.3.0.
_CalibrationMethod = Literal[
    "single_point_literature_alpha_beta",
    "multi_point_fitted",
    "production",
]

#: Runtime counterpart of `_CalibrationMethod`, derived with `get_args()` so
#: it can never drift from the Literal (STYLE.md: never hand-copy a Literal's
#: members into a separate tuple).
_ALLOWED_CALIBRATION_METHODS: tuple[str, ...] = get_args(_CalibrationMethod)

#: Message for the one-release-cycle `s_confidence` alias (see module docstring).
_S_CONFIDENCE_DEPRECATION = (
    "SteinmetzData.s_confidence is deprecated and will be removed in the next "
    "MAJOR release; use s_calibration_method (it holds a calibration-method "
    "label, not a source-quality tier)."
)

#: Round-trip tolerance for the
#: `k · f_ref^alpha · B_ref^beta == P_ref` check.
#: Single-point fits round-trip to float precision by construction;
#: multi-point LSQ may have ~2% residuals at the anchor point.
_ROUND_TRIP_TOL_REL: float = 0.02

#: Literature bounds on the Steinmetz exponents for soft-magnetic alloys.
#: alpha (frequency exponent) commonly runs 1.3-1.8 for electrical
#: steels: the hysteresis-dominated limit is alpha -> 1, eddy-dominated
#: pushes toward 2; measured thin-gauge NO Si-Fe at power frequency
#: genuinely sits near 1.3-1.4 (the v1.4.0 M270-35A grid LSQ gives
#: alpha = 1.346 over 50-400 Hz: that measured value is what widened
#: the v1.3 floor of 1.4 down to 1.3). beta (flux-density exponent)
#: is in [1.6, 2.4] for the same class.
#: (v1.3.1 note: an earlier revision of this comment cited 'Pyrhönen
#: Table 3.2' for the alpha range: that specific table attribution
#: was never verified and is retracted; treat these as generic
#: literature envelopes.)
_ALPHA_BOUNDS: tuple[float, float] = (1.3, 1.8)
_BETA_BOUNDS: tuple[float, float] = (1.6, 2.4)


@dataclass(frozen=True)
class SteinmetzData:
    """Steinmetz core-loss coefficient triple `(k, alpha, beta)`
    with calibration anchor and full provenance.

    Use:

        em = Electromagnetic(
            core_loss=PropertyValue(d_value=3.42, s_units='W/kg', ...),
            steinmetz=SteinmetzData(
                d_k=k_computed,                         # NEVER hardcode
                d_alpha=1.6, d_beta=2.0,
                d_reference_loss_W_per_kg=3.42,
                d_reference_frequency_Hz=60.0,
                d_reference_B_pk_T=1.5,
                d_validity_freq_range_Hz=(50.0, 400.0),
                d_validity_B_range_T=(0.5, 1.8),
                s_source='...',
                s_calibration_method='single_point_literature_alpha_beta',
                s_condition='...',
            ),
        )

    The `k` value MUST be derived from the reference triple
    `(P_ref, f_ref, B_ref)` with the chosen `(alpha, beta)`. Hard-
    coding an approximate numerical `k` (e.g. copying "2.172e-3" from
    docs) is forbidden by convention: recompute it in code so the
    round-trip is exact and the source of truth is the formula
    `k = P_ref / (f_ref^alpha · B_ref^beta)`. The round-trip is
    re-verified in `__post_init__`; mismatches > 2% relative raise.

    Args:
        d_k: Steinmetz prefactor `k`, units `[W/kg] / (Hz^alpha · T^beta)`.
            Always derived from the reference triple, never hardcoded.
        d_alpha: Frequency exponent. Literature range `[1.3, 1.8]` for
            electrical steels / Co-Fe (floor widened from 1.4 in v1.4.0:
            measured thin-gauge NO Si-Fe at power frequency is hysteresis-
            dominated and genuinely fits alpha ≈ 1.35); bounds enforced in
            `__post_init__`.
        d_beta: Flux-density exponent. Literature range `[1.6, 2.4]` for
            Si-Fe / Co-Fe.
        d_reference_loss_W_per_kg: The single catalog reference point
            `P_ref` the fit was anchored on, in W/kg.
        d_reference_frequency_Hz: Reference frequency `f_ref` [Hz]
            (typically 50 or 60 Hz for utility-grade silicon steels).
        d_reference_B_pk_T: Reference peak flux density `B_ref` [T]
            (typically 1.5 T for Si-Fe datasheet single-point specs).
        d_validity_freq_range_Hz: `(f_min, f_max)` frequencies [Hz] where
            the fit is trusted. For single-point fits, this is a
            literature judgement, not a measurement bound. None means
            caller should default to treating the reference frequency as
            the only validated point.
        d_validity_B_range_T: Same idea, for peak flux density.
        s_source: Tier-1 primary citation for the reference triple AND
            the provenance of the chosen `alpha` / `beta`. Non-empty.
        s_calibration_method: One of `"single_point_literature_alpha_beta"`,
            `"multi_point_fitted"`, `"production"`. See module docstring.
            This is a CALIBRATION-METHOD label, not a source-quality tier
            (the latter lives on the parent
            `Electromagnetic.core_loss.s_confidence` PropertyValue). The
            pre-rename keyword `s_confidence` is still accepted for one
            release cycle and emits a `DeprecationWarning`.
        s_condition: Material condition matching the `core_loss`
            PropertyValue's `s_condition` (lamination gauge, anneal
            state, test standard, rolling-direction vs Epstein, etc.).
        s_notes: Free-form cross-references and consumer warnings.

    Validation (`__post_init__`):

      1. All `d_*` values are positive finite.
      2. `s_source` non-empty after strip.
      3. `s_calibration_method` in the allowed set.
      4. Round-trip: `k · f_ref^alpha · B_ref^beta == P_ref` to
         `_ROUND_TRIP_TOL_REL` relative (default 2%).
      5. `alpha` in `_ALPHA_BOUNDS` (default `[1.3, 1.8]`).
      6. `beta` in `_BETA_BOUNDS` (default `[1.6, 2.4]`).
      7. Validity-range tuples (if not None): `f_min < f_max`,
         `B_min < B_max`, all positive; and the reference
         `(f_ref, B_ref)` lies inside both ranges.
    """

    d_k: float
    d_alpha: float
    d_beta: float
    d_reference_loss_W_per_kg: float
    d_reference_frequency_Hz: float
    d_reference_B_pk_T: float
    d_validity_freq_range_Hz: tuple[float, float] | None
    d_validity_B_range_T: tuple[float, float] | None
    s_source: str
    s_calibration_method: _CalibrationMethod
    s_condition: str = ""
    s_notes: str = ""

    @property
    def s_confidence(self) -> _CalibrationMethod:
        """Deprecated alias for ``s_calibration_method``; removed next MAJOR."""
        warnings.warn(_S_CONFIDENCE_DEPRECATION, DeprecationWarning, stacklevel=2)
        return self.s_calibration_method

    def __post_init__(self) -> None:
        # ── (1) Positivity + finiteness
        for f_name in (
            "d_k",
            "d_alpha",
            "d_beta",
            "d_reference_loss_W_per_kg",
            "d_reference_frequency_Hz",
            "d_reference_B_pk_T",
        ):
            v = getattr(self, f_name)
            if (
                not isinstance(v, (int, float))
                # NaN is the only value unequal to itself; this is the idiomatic
                # NaN test, not an accidental self-comparison.
                or v != v  # noqa: PLR0124
                or v == float("inf")
                or v == float("-inf")
                or v <= 0.0
            ):
                raise ValueError(f"SteinmetzData.{f_name} must be positive finite, got {v!r}")

        # ── (2) Source non-empty
        if not (isinstance(self.s_source, str) and self.s_source.strip()):
            raise ValueError(
                "SteinmetzData.s_source must be a non-empty string "
                "(catalog requires Tier-1 primary citation for the "
                "reference triple AND the chosen alpha/beta)."
            )

        # ── (3) Calibration-method enum
        if self.s_calibration_method not in _ALLOWED_CALIBRATION_METHODS:
            raise ValueError(
                f"SteinmetzData.s_calibration_method must be one of "
                f"{_ALLOWED_CALIBRATION_METHODS!r}, got {self.s_calibration_method!r}"
            )

        # ── (4) Round-trip: k · f_ref^alpha · B_ref^beta == P_ref
        #
        # For single-point fits this is exact-by-construction up to
        # float precision (we computed k by inverting this formula),
        # so the 2% tolerance is generous. For multi-point fits the
        # residual at the anchor point is bounded by the LSQ
        # convergence; 2% is a sane catalog gate.
        P_pred = (
            self.d_k
            * (self.d_reference_frequency_Hz**self.d_alpha)
            * (self.d_reference_B_pk_T**self.d_beta)
        )
        rel_err = abs(P_pred - self.d_reference_loss_W_per_kg) / self.d_reference_loss_W_per_kg
        if rel_err > _ROUND_TRIP_TOL_REL:
            raise ValueError(
                f"SteinmetzData round-trip failed: "
                f"k·f_ref^alpha·B_ref^beta = {P_pred:.6f} W/kg vs "
                f"reference {self.d_reference_loss_W_per_kg:.6f} W/kg "
                f"(rel err {rel_err:.2%} > {_ROUND_TRIP_TOL_REL:.0%}). "
                f"k must be derived from the reference triple as "
                f"k = P_ref / (f_ref^alpha · B_ref^beta); do NOT "
                f"hardcode an approximate value."
            )

        # ── (5) alpha bounds
        if not (_ALPHA_BOUNDS[0] <= self.d_alpha <= _ALPHA_BOUNDS[1]):
            raise ValueError(
                f"SteinmetzData.d_alpha={self.d_alpha} outside literature "
                f"range {_ALPHA_BOUNDS} for soft-magnetic alloys "
                f"(Si-Fe / Co-Fe / amorphous / nanocrystalline). "
                f"If a wider range is needed, document the source in "
                f"s_notes and consider extending _ALPHA_BOUNDS in the "
                f"schema with a literature citation."
            )

        # ── (6) beta bounds
        if not (_BETA_BOUNDS[0] <= self.d_beta <= _BETA_BOUNDS[1]):
            raise ValueError(
                f"SteinmetzData.d_beta={self.d_beta} outside literature "
                f"range {_BETA_BOUNDS} for soft-magnetic alloys."
            )

        # ── (7) Validity ranges (if supplied)
        if self.d_validity_freq_range_Hz is not None:
            f_min, f_max = self.d_validity_freq_range_Hz
            if not (0.0 < f_min < f_max):
                raise ValueError(
                    f"SteinmetzData.d_validity_freq_range_Hz must be "
                    f"(f_min, f_max) with 0 < f_min < f_max; "
                    f"got {self.d_validity_freq_range_Hz}"
                )
            if not (f_min <= self.d_reference_frequency_Hz <= f_max):
                raise ValueError(
                    f"SteinmetzData.d_reference_frequency_Hz="
                    f"{self.d_reference_frequency_Hz} lies outside the "
                    f"declared validity range {self.d_validity_freq_range_Hz}. "
                    f"Either widen the range or drop the anchor."
                )
        if self.d_validity_B_range_T is not None:
            B_min, B_max = self.d_validity_B_range_T
            if not (0.0 < B_min < B_max):
                raise ValueError(
                    f"SteinmetzData.d_validity_B_range_T must be "
                    f"(B_min, B_max) with 0 < B_min < B_max; "
                    f"got {self.d_validity_B_range_T}"
                )
            if not (B_min <= self.d_reference_B_pk_T <= B_max):
                raise ValueError(
                    f"SteinmetzData.d_reference_B_pk_T="
                    f"{self.d_reference_B_pk_T} lies outside the "
                    f"declared validity range {self.d_validity_B_range_T}."
                )


__all__ = ["SteinmetzData"]


# ── Constructor alias: accept the pre-rename keyword for one release cycle.
#
# The dataclass generates __init__ at decoration time, so the alias has to
# wrap it here rather than live in __post_init__ (which never sees unknown
# keywords). Positional index 9 is s_calibration_method.
_dataclass_init = SteinmetzData.__init__


def _init_with_alias(
    self: SteinmetzData,
    *args: Any,
    s_confidence: _CalibrationMethod | None = None,
    **kwargs: Any,
) -> None:
    if s_confidence is not None:
        warnings.warn(_S_CONFIDENCE_DEPRECATION, DeprecationWarning, stacklevel=2)
        if "s_calibration_method" in kwargs or len(args) >= 10:
            raise TypeError(
                "SteinmetzData: pass s_calibration_method or the deprecated s_confidence, not both"
            )
        kwargs["s_calibration_method"] = s_confidence
    _dataclass_init(self, *args, **kwargs)


SteinmetzData.__init__ = _init_with_alias  # type: ignore[method-assign]
