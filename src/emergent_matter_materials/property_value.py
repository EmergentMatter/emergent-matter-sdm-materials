"""PropertyValue: a single physical property value with full provenance.

Every numeric property in the materials catalog is stored as a
``PropertyValue``, never as a bare float. The wrapper carries five pieces of
metadata alongside the number:

- ``d_value``: the SI-units numeric value
- ``s_units``: the units string; validator-enforced against
  :data:`~emergent_matter_materials.units_map._PROPERTY_EXPECTED_UNITS`
- ``s_source``: citation (book, datasheet, paper, vendor TDS)
- ``s_condition``: operating point or sample state
- ``s_confidence``: provenance grade (enum)
- ``s_notes``: free-form clarification

Consumers reach the bare float via convenience accessors on the enclosing
group dataclass (see ``Structural.d_youngs_modulus_Pa``, etc.). The
``PropertyValue`` itself stays metadata-rich for cross-physics traceability
and so ``get_with_metadata()`` can answer "where did this number come from
and at what conditions" without round-tripping through the float.

The ``s_units`` field is NOT decorative. The enclosing group dataclass's
``__post_init__`` checks that every PropertyValue's ``s_units`` matches the
canonical SI string in ``_PROPERTY_EXPECTED_UNITS`` for the slot it
occupies. A wrong unit string is a construction-time ValueError. This is
the gate that prevents silent unit drift in the catalog.

**Confidence enum (source-priority hierarchy).**
The ``s_confidence`` enum is a strict authority ranking: when two
sources disagree on the same property, the HIGHER-tier source wins.
See this repo's ``CLAUDE.md``, "Source-priority hierarchy" section,
for the full conflict-resolution rules.

Tier 1 (PRIMARY):
- ``measured``: direct lab measurement on the specific material lot
- ``datasheet``: vendor TDS (Arnold, Carpenter, Victrex, SABIC, EOS,
  Formlabs, etc.). Authoritative for commercial alloys, polymers,
  and magnets where the material IS what the vendor ships.
- ``standard``: national/international published reference data
  (NIST SRD / JPCRD, ASTM/AMS specs, EN/ISO standards, MMPDS,
  Aluminum Association ADM). Authoritative for pure-element
  thermophysical data and grade-defining alloy specs.

Tier 2 (AUTHORITATIVE SECONDARY):
- ``handbook``: peer-reviewed engineering handbooks (ASM Handbook,
  Shigley's MED, CRC Handbook, Boyer Atlas of Fatigue Curves) and
  peer-reviewed papers. Authoritative when Tier 1 doesn't cover.

Tier 3 (AGGREGATOR):
- ``aggregator``: database aggregators (MatWeb, ULProspector,
  SpecialChem, Citrination paper-mined, university course materials).
  Use only when Tier 1+2 silent. `s_source` MUST name the aggregator
  explicitly so a consumer knows the value is one hop from a primary
  measurement.

Tier 4 (INFERRED):
- ``derived``: computed from other properties, unit-converted from
  imperial, range-averaged, or fitted-model output. Must explain
  derivation in `s_notes`.
- ``estimated``: rough engineering rule-of-thumb (σ_e ≈ 0.5 σ_UTS,
  etc.). Must explain reasoning in `s_notes`.

Special:
- ``placeholder``: known-bad stand-in; requires non-empty `s_notes`
  explaining what real source is pending. Allowed only on the
  explicit placeholder allowlist.
- ``unspecified``: legacy port without source info. Rejected by
  provenance-strength gate tests unless the material is on the
  migration allowlist.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, get_args

ConfidenceLevel = Literal[
    # Tier 1: primary
    "measured",
    "datasheet",
    "standard",
    # Tier 2: authoritative secondary
    "handbook",
    # Tier 3: aggregator
    "aggregator",
    # Tier 4: inferred
    "derived",
    "estimated",
    # Special
    "placeholder",
    "unspecified",
]

#: Runtime counterpart of `ConfidenceLevel`, derived with `get_args()` so it
#: can never drift from the Literal (STYLE.md: never hand-copy a Literal's
#: members into a separate tuple/frozenset).
_VALID_CONFIDENCE_LEVELS: frozenset[str] = frozenset(get_args(ConfidenceLevel))

#: Tier-1 (primary) confidence levels. Used by the provenance-distribution
#: gate to count "solid sourcing": datasheet + standard + measured.
_TIER_1_CONFIDENCE: frozenset[str] = frozenset(
    {
        "measured",
        "datasheet",
        "standard",
    }
)

#: Solid-sourcing confidence levels: Tier 1 OR Tier 2.
_SOLID_CONFIDENCE: frozenset[str] = frozenset(
    {
        "measured",
        "datasheet",
        "standard",
        "handbook",
    }
)


@dataclass(frozen=True)
class PropertyValue:
    """A single physical property value with full provenance.

    See module docstring for the design philosophy. ``__post_init__`` validates
    field shapes (confidence enum, source-non-empty rules); the *units*
    validation is done by the enclosing group dataclass because only it
    knows which property slot this value occupies.
    """

    d_value: float
    s_units: str
    s_source: str
    s_condition: str = ""
    s_confidence: ConfidenceLevel = "unspecified"
    s_notes: str = ""

    def __post_init__(self) -> None:
        # Type-check d_value defensively: accepting numpy/jax scalars would
        # break frozen-dataclass equality + the SI-converter assumptions.
        if not isinstance(self.d_value, (int, float)) or isinstance(self.d_value, bool):
            raise TypeError(
                f"PropertyValue.d_value must be float or int, "
                f"got {type(self.d_value).__name__}: {self.d_value!r}"
            )

        # Confidence enum.
        if self.s_confidence not in _VALID_CONFIDENCE_LEVELS:
            raise ValueError(
                f"PropertyValue.s_confidence must be one of "
                f"{sorted(_VALID_CONFIDENCE_LEVELS)}, "
                f"got {self.s_confidence!r}"
            )

        # Source-non-empty rule, with one exception for placeholders.
        # A "placeholder" entry is known-bad, but the GATE is that you
        # must explain what's pending in s_notes. No silent placeholders.
        if not self.s_source:
            if self.s_confidence == "placeholder":
                if not self.s_notes:
                    raise ValueError(
                        "PropertyValue with confidence='placeholder' must "
                        "have non-empty s_notes explaining what real source "
                        "is pending"
                    )
            else:
                raise ValueError(
                    f"PropertyValue requires non-empty s_source unless "
                    f"s_confidence='placeholder' (with explanatory s_notes); "
                    f"got s_source='', s_confidence={self.s_confidence!r}"
                )

    # ── Display-unit conveniences (additive; storage stays SI)

    def as_MPa(self) -> float:
        """For Pa-stored values, return the value in MPa.

        Convenience for human-friendly stress display. Asserts the
        stored units are Pa.
        """
        if self.s_units != "Pa":
            raise ValueError(f"as_MPa() expects s_units='Pa', got {self.s_units!r}")
        return self.d_value / 1e6

    def as_g_cc(self) -> float:
        """For kg/m^3-stored values (density), return value in g/cc."""
        if self.s_units != "kg/m^3":
            raise ValueError(f"as_g_cc() expects s_units='kg/m^3', got {self.s_units!r}")
        return self.d_value / 1e3


__all__ = [
    "ConfidenceLevel",
    "PropertyValue",
]
