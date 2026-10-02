"""Materials-side resolver for rotational-flux core-loss data (Phase 2).

Answers exactly one question: *given a Material and a requested (B, f, T)
operating point, what rotational-loss data exists for it, and what is its
eligibility status*: absent, incomplete, diagnostic-only, out-of-range, or
validated-consumable?

What this resolver is NOT:

- It does **not** compute a rotational-loss number. There is no loss math, no
  interpolation, no fitting anywhere on the materials side. It resolves DATA
  ELIGIBILITY only. The returned `RotationalLossResolveResult` carries a
  status + the selected record + provenance, never a watt value.
- It does **not** fall back to alternating `SteinmetzData` as if it were
  rotational data. A rotating B-locus is a different physical problem from a
  1-D alternating waveform (Phase 0A). The result may *flag* that alternating
  data exists (`b_alternating_steinmetz_present`) purely as information, but
  the resolver never substitutes it.
- It does **not** invent fake zeros. Missing / incomplete / out-of-range never
  collapses to "0 W": it returns a blocked status that the consumer must
  honour.

Phase 2 uses SYNTHETIC fixtures only; the catalog still holds zero real
rotational records (every material's `rotational_loss_models` is the empty
tuple). This module proves the policy machinery before any RSST paper is
sourced.

Three axes (Phase 0B) drive the outcome, never collapsed:
  - source confidence (`s_confidence`): the Option-C admitted set is
    {measured, datasheet, standard, handbook};
  - data completeness (`n_completeness_level`, Level 0-3);
  - the queried operating point's position relative to the record's declared
    validity ranges.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

from emergent_matter_materials.rotational_loss import (
    STATUS_MISSING_ROTATIONAL_LOSS_DATA,
    STATUS_ROTATIONAL_LOSS_DIAGNOSTIC_ONLY,
    STATUS_ROTATIONAL_LOSS_INCOMPLETE,
    STATUS_ROTATIONAL_LOSS_OUT_OF_RANGE,
    STATUS_ROTATIONAL_LOSS_VALIDATED_CONSUMABLE,
    RotationalLossData,
)

if TYPE_CHECKING:
    # Type-only import to avoid the material -> electromagnetic ->
    # rotational_loss import cycle. At runtime the resolver only needs duck
    # access to `material.s_id` and `material.electromagnetic`.
    from emergent_matter_materials.material import Material


#: Source-confidence total order for deterministic tie-breaks (higher = more
#: authoritative). Mirrors the source-priority hierarchy; used ONLY to break
#: ties between same-rung records, never to admit/deny (admission is the
#: separate `b_source_admissible` gate on the record itself).
_CONFIDENCE_RANK: dict[str, int] = {
    "measured": 7,
    "datasheet": 6,
    "standard": 5,
    "handbook": 4,
    "aggregator": 3,
    "derived": 2,
    "estimated": 1,
    "placeholder": 0,
    "unspecified": 0,
}


@dataclass(frozen=True)
class RotationalLossResolveResult:
    """Structured eligibility result for a rotational-loss data query.

    Carries a status + the selected record + its provenance/axes, NEVER a
    computed loss number. `s_status` is one of `ROTATIONAL_RESOLVE_OUTCOMES`.
    """

    s_status: str
    record: RotationalLossData | None
    s_material_id: str
    s_material_as_published: str
    n_completeness_level: int | None
    s_confidence: str | None
    b_validated_consumable: bool
    b_diagnostic_only: bool
    s_validity_verdict: str  # "in_range" | "out_of_range:B|f|T"
    #   | "no_validity_declared" | "no_records"
    s_source: str
    s_notes: str
    d_query_B_T: float
    d_query_f_Hz: float
    d_query_temperature_C: float | None
    n_records_considered: int
    #: Informational ONLY: True if the material carries an alternating-flux
    #: SteinmetzData. The resolver records this so a consumer knows alternating
    #: data exists, but it NEVER substitutes it for rotational data.
    b_alternating_steinmetz_present: bool


# ── helpers ──────────────────────────────────────────────────────────────────


def _eligibility(rec: RotationalLossData) -> str:
    """Classify a record into 'validated' / 'diagnostic' / 'recordable'.

    - validated  : Level 3 AND admitted source ({measured,datasheet,standard,
                   handbook}), i.e. `rec.b_validated_consumable`.
    - diagnostic : Level 2 (any source), OR Level 3 with a NON-admitted source
                   (Tier-3/4: aggregator/derived/estimated, data-complete but
                   source bars validation).
    - recordable : Level 0 or 1 (citation / incomplete).
    """
    if rec.b_validated_consumable:
        return "validated"
    if rec.n_completeness_level == 2 or (
        rec.n_completeness_level == 3 and not rec.b_source_admissible
    ):
        return "diagnostic"
    return "recordable"


def _range_check(
    rec: RotationalLossData,
    B_T: float,
    f_Hz: float,
    temperature_C: float | None,
) -> tuple[bool, str]:
    """Check the query against the record's DECLARED validity ranges.

    Returns ``(in_range, verdict)``. An axis with no declared range does not
    constrain (cannot be out-of-range on an undeclared axis). Temperature is
    checked only when both a range is declared AND a temperature was queried.

    verdict ∈ {"in_range", "out_of_range:B", "out_of_range:f",
               "out_of_range:T", "no_validity_declared"}.
    """
    declared = False
    for rng, val, axis in (
        (rec.d_validity_B_range_T, B_T, "B"),
        (rec.d_validity_freq_range_Hz, f_Hz, "f"),
        (rec.d_validity_temperature_range_C, temperature_C, "T"),
    ):
        if rng is None:
            continue
        if axis == "T" and temperature_C is None:
            continue  # temperature not queried → that axis does not constrain
        declared = True
        lo, hi = rng
        if val is None:
            # Unreachable in practice: B_T/f_Hz are validated finite-positive
            # floats before this is called, and the T axis already `continue`d
            # above when temperature_C is None. mypy can't carry that
            # per-axis narrowing across the heterogeneous (rng, val, axis)
            # tuples in the loop above, so this guard makes the comparison
            # below honestly `float`-only instead of silencing it with a cast.
            continue
        if not (lo <= val <= hi):
            return False, f"out_of_range:{axis}"
    if not declared:
        return True, "no_validity_declared"
    return True, "in_range"


def _rung(eligibility: str, in_range: bool) -> int:
    """Selection-ladder rung (lower = preferred). Encodes Phase 2's locked
    selection order: actionable in-range results first, then the validated
    out-of-range signal, then diagnostic out-of-range, then recordable.

      0  validated  + in-range   → the only path to validated_consumable
      1  diagnostic + in-range   → actionable screening datum
      2  validated  + out-range  → "you have validated data, not at this point"
      3  diagnostic + out-range
      4  recordable (L0/L1, any range)
    """
    if eligibility == "validated" and in_range:
        return 0
    if eligibility == "diagnostic" and in_range:
        return 1
    if eligibility == "validated" and not in_range:
        return 2
    if eligibility == "diagnostic" and not in_range:
        return 3
    return 4


def _status_for(eligibility: str, in_range: bool) -> str:
    if eligibility == "validated":
        return (
            STATUS_ROTATIONAL_LOSS_VALIDATED_CONSUMABLE
            if in_range
            else STATUS_ROTATIONAL_LOSS_OUT_OF_RANGE
        )
    if eligibility == "diagnostic":
        return STATUS_ROTATIONAL_LOSS_DIAGNOSTIC_ONLY
    return STATUS_ROTATIONAL_LOSS_INCOMPLETE


# ── resolver ─────────────────────────────────────────────────────────────────


def resolve_rotational_loss_data_from_material(
    material: Material,
    *,
    B_T: float,
    f_Hz: float,
    temperature_C: float | None = None,
) -> RotationalLossResolveResult:
    """Resolve rotational-loss data eligibility for a material at (B, f[, T]).

    Returns a `RotationalLossResolveResult` (status + selected record +
    provenance). Does NOT compute loss. Never falls back to alternating
    Steinmetz data. Never returns a fake zero.

    Selection ladder (deterministic; preferred first):

      1. validated-consumable AND in-range  → validated_consumable
      2. diagnostic AND in-range            → diagnostic_only
      3. validated-consumable AND out-of-range → out_of_range
      4. diagnostic AND out-of-range        → diagnostic_only
      5. recordable (Level 0/1)             → incomplete
      6. no records                         → missing_rotational_loss_data

    Within a rung, ties break by: higher completeness Level, then higher
    source-confidence rank, then lowest original tuple index (first-declared
    wins: stable + provenance-preserving). A higher-quality in-range record is
    never silently passed over for a lower-quality one.

    Raises:
        ValueError: B_T or f_Hz is not finite-positive, or temperature_C
            (when given) is not finite.
    """
    if not (
        isinstance(B_T, (int, float))
        and not isinstance(B_T, bool)
        and math.isfinite(B_T)
        and B_T > 0.0
    ):
        raise ValueError(f"B_T must be a finite positive flux density, got {B_T!r}")
    if not (
        isinstance(f_Hz, (int, float))
        and not isinstance(f_Hz, bool)
        and math.isfinite(f_Hz)
        and f_Hz > 0.0
    ):
        raise ValueError(f"f_Hz must be a finite positive frequency, got {f_Hz!r}")
    if temperature_C is not None and not (
        isinstance(temperature_C, (int, float))
        and not isinstance(temperature_C, bool)
        and math.isfinite(temperature_C)
    ):
        raise ValueError(f"temperature_C must be finite when given, got {temperature_C!r}")

    s_material_id = getattr(material, "s_id", "") or ""
    em = getattr(material, "electromagnetic", None)
    records: tuple[RotationalLossData, ...] = (
        tuple(em.rotational_loss_models) if em is not None else ()
    )
    b_alt = em is not None and getattr(em, "steinmetz", None) is not None

    d_B = float(B_T)
    d_f = float(f_Hz)
    d_T = None if temperature_C is None else float(temperature_C)

    if not records:
        return RotationalLossResolveResult(
            s_status=STATUS_MISSING_ROTATIONAL_LOSS_DATA,
            record=None,
            s_material_id=s_material_id,
            s_material_as_published="",
            n_completeness_level=None,
            s_confidence=None,
            b_validated_consumable=False,
            b_diagnostic_only=False,
            s_validity_verdict="no_records",
            s_source="",
            s_notes=(
                "No rotational-loss records on this material; rotational flux "
                "cells must defer (solver disposition "
                "rotational_flux_not_modeled). NOT a zero-loss claim."
            ),
            d_query_B_T=d_B,
            d_query_f_Hz=d_f,
            d_query_temperature_C=d_T,
            n_records_considered=0,
            b_alternating_steinmetz_present=b_alt,
        )

    # Classify + score every record.
    scored = []
    for idx, rec in enumerate(records):
        elig = _eligibility(rec)
        in_range, verdict = _range_check(rec, d_B, d_f, d_T)
        scored.append((idx, rec, elig, in_range, verdict))

    # Deterministic selection: best rung, then higher completeness, then higher
    # source-confidence rank, then lowest original index (stable).
    best = min(
        scored,
        key=lambda s: (
            _rung(s[2], s[3]),
            -s[1].n_completeness_level,
            -_CONFIDENCE_RANK.get(s[1].s_confidence, 0),
            s[0],
        ),
    )
    _idx, rec, elig, in_range, verdict = best
    status = _status_for(elig, in_range)

    # Preserve the "higher-quality data exists but is out of range" signal even
    # when an in-range lower-quality record was (correctly) selected.
    notes_parts = [rec.s_notes] if rec.s_notes else []
    if status != STATUS_ROTATIONAL_LOSS_VALIDATED_CONSUMABLE and any(
        s[2] == "validated" and not s[3] for s in scored
    ):
        notes_parts.append(
            "Resolver note: a validated-consumable record exists for this "
            "material but is OUT OF RANGE at the queried operating point; an "
            "in-range lower-eligibility record was selected instead. No "
            "validated rotational-loss number is available here."
        )

    return RotationalLossResolveResult(
        s_status=status,
        record=rec,
        s_material_id=s_material_id,
        s_material_as_published=rec.s_material_as_published,
        n_completeness_level=rec.n_completeness_level,
        s_confidence=rec.s_confidence,
        b_validated_consumable=(status == STATUS_ROTATIONAL_LOSS_VALIDATED_CONSUMABLE),
        b_diagnostic_only=(status == STATUS_ROTATIONAL_LOSS_DIAGNOSTIC_ONLY),
        s_validity_verdict=verdict,
        s_source=rec.s_source,
        s_notes=" | ".join(notes_parts),
        d_query_B_T=d_B,
        d_query_f_Hz=d_f,
        d_query_temperature_C=d_T,
        n_records_considered=len(records),
        b_alternating_steinmetz_present=b_alt,
    )


__all__ = [
    "RotationalLossResolveResult",
    "resolve_rotational_loss_data_from_material",
]
