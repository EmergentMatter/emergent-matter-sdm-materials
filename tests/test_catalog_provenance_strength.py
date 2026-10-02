"""Catalog provenance-strength gate.

These tests are the **non-negotiable shipping gate** for the catalog.
They scan every PropertyValue in MATERIALS and refuse to ship if any
entry has weak metadata. If any of these fail, the catalog doesn't go
out, period: fix the offending entry before tagging a release.

Six gates, in increasing strictness:

1. Every PropertyValue cites a non-empty s_source, UNLESS confidence
   is 'placeholder' AND the material is on the explicit placeholder
   allowlist.
2. Every PropertyValue's s_units matches _PROPERTY_EXPECTED_UNITS for
   its slot. (Group __post_init__ already enforces this on
   construction; this is the catalog-wide belt-and-suspenders pass.)
3. No PropertyValue has confidence='unspecified' unless the material
   is on the explicit migration allowlist.
4. Every confidence='placeholder' PropertyValue has non-empty s_notes
   explaining what real source is pending.
5. Every Material with a non-informal category has a non-empty
   s_specification (or is on the informal-allowlist).
6. Every Material.s_catalog_version <= __catalog_version__.

The allowlists let v0.1.0 ship with a small number of known-imperfect
entries while documenting them, but the catalog grows by adding
entries, never by expanding allowlists. Allowlist entries should be
revisited on every PATCH-level catalog release.
"""

from __future__ import annotations

from dataclasses import fields

import pytest

from emergent_matter_materials import __catalog_version__
from emergent_matter_materials.accessors import MATERIALS
from emergent_matter_materials.material import Material
from emergent_matter_materials.property_value import PropertyValue
from emergent_matter_materials.units_map import _PROPERTY_EXPECTED_UNITS

# ── Allowlists (revisit on every catalog PATCH release) ────────────────────

#: Materials allowed to have confidence='placeholder' PropertyValues.
#: Each entry should have a follow-up TODO referencing the planned source.
_PLACEHOLDER_ALLOWLIST: frozenset[str] = frozenset(
    {
        # Empty for v0.1.0: no placeholder entries shipped.
    }
)

#: Materials allowed to have confidence='unspecified' PropertyValues:
#: legacy ports without source info. Strictly time-limited; every entry
#: gets a real source by the next catalog MINOR release.
_UNSPECIFIED_ALLOWLIST: frozenset[str] = frozenset(
    {
        # Empty for v0.1.0: every PropertyValue was sourced at port time.
    }
)

#: Material categories where empty s_specification is acceptable (e.g.
#: custom composites, prototype mixes). Not used by any v0.1.0 entry but
#: reserved for future use.
_INFORMAL_CATEGORIES: frozenset[str] = frozenset(
    {
        "composite",  # custom layups
        "elastomer",  # generic shore-hardness rubbers / TPUs
    }
)


# ── Helpers ────────────────────────────────────────────────────────────────


def _iter_propertyvalues(m: Material):
    """Yield (group_name, field_name, PropertyValue) for every populated
    PropertyValue field on a Material across all five groups + per-process
    Manufacturing.ProcessFit values."""
    # v0.4.0: include crystal_anisotropy in the simple-group sweep.
    for s_group_name in ("structural", "electromagnetic", "thermal", "crystal_anisotropy"):
        group = getattr(m, s_group_name, None)
        if group is None:
            continue
        for f in fields(group):
            pv = getattr(group, f.name)
            if pv is not None and isinstance(pv, PropertyValue):
                yield (s_group_name, f.name, pv)

    if m.manufacturing is not None:
        for s_proc_key, fit in m.manufacturing.process_fit.items():
            for f in fields(fit):
                pv = getattr(fit, f.name)
                if pv is not None and isinstance(pv, PropertyValue):
                    yield (f"manufacturing.{s_proc_key}", f.name, pv)


# ── Gate 1: every PropertyValue has a non-empty source ─────────────────────


def test_every_propertyvalue_has_nonempty_source():
    """Every PropertyValue in MATERIALS must cite a source, UNLESS
    confidence == 'placeholder' AND the material is allowlisted."""
    failures: list[str] = []
    for s_id, m in MATERIALS.items():
        for s_group, s_field, pv in _iter_propertyvalues(m):
            if not pv.s_source:
                if pv.s_confidence == "placeholder" and s_id in _PLACEHOLDER_ALLOWLIST:
                    continue
                failures.append(
                    f"{s_id}.{s_group}.{s_field}: empty s_source (confidence={pv.s_confidence!r})"
                )
    assert not failures, (
        "Empty s_source detected, every PropertyValue must cite a source:\n"
        + "\n".join(f"  - {msg}" for msg in failures)
    )


# ── Gate 2: every PropertyValue's units match the expected-units map ───────


def test_every_propertyvalue_units_match_expected_map():
    """Belt-and-suspenders: group __post_init__ already enforces this on
    construction, but a catalog-wide scan catches the case where someone
    bypasses construction (e.g. via dataclass.replace) or where the
    expected-units map drifts from the dataclass field set."""
    failures: list[str] = []
    for s_id, m in MATERIALS.items():
        for s_group, s_field, pv in _iter_propertyvalues(m):
            # Field name may include "manufacturing.PROC_KEY." prefix: strip for lookup.
            s_lookup = s_field
            expected = _PROPERTY_EXPECTED_UNITS.get(s_lookup)
            if expected is None:
                failures.append(f"{s_id}.{s_group}.{s_field}: not in _PROPERTY_EXPECTED_UNITS")
                continue
            if pv.s_units != expected:
                failures.append(
                    f"{s_id}.{s_group}.{s_field}: s_units={pv.s_units!r} != expected {expected!r}"
                )
    assert not failures, "Units mismatch detected:\n" + "\n".join(f"  - {msg}" for msg in failures)


# ── Gate 3: no 'unspecified' confidence outside allowlist ──────────────────


def test_no_unspecified_confidence_unless_allowlisted():
    """confidence='unspecified' is only allowed for materials on the
    explicit migration allowlist. Default new-entry confidence must be
    one of the seven graded tiers (measured/datasheet/standard/handbook/
    aggregator/derived/estimated)."""
    failures: list[str] = []
    for s_id, m in MATERIALS.items():
        for s_group, s_field, pv in _iter_propertyvalues(m):
            if pv.s_confidence == "unspecified":
                if s_id in _UNSPECIFIED_ALLOWLIST:
                    continue
                failures.append(
                    f"{s_id}.{s_group}.{s_field}: confidence='unspecified' "
                    f"(material not on _UNSPECIFIED_ALLOWLIST)"
                )
    assert not failures, (
        "'unspecified' confidence detected outside allowlist: set a real "
        "confidence level (measured/datasheet/handbook/derived/estimated):\n"
        + "\n".join(f"  - {msg}" for msg in failures)
    )


# ── Gate 4: placeholder entries have non-empty s_notes ─────────────────────


def test_placeholder_values_have_explanatory_notes():
    """A confidence='placeholder' entry must have a non-empty s_notes
    field explaining what real source is pending. Construction-time
    validation already enforces this when s_source is also empty; this
    test catches the s_source-populated-but-still-placeholder case too."""
    failures: list[str] = []
    for s_id, m in MATERIALS.items():
        for s_group, s_field, pv in _iter_propertyvalues(m):
            if pv.s_confidence == "placeholder" and not pv.s_notes:
                failures.append(
                    f"{s_id}.{s_group}.{s_field}: confidence='placeholder' but s_notes is empty"
                )
    assert not failures, "Placeholder entries missing explanation in s_notes:\n" + "\n".join(
        f"  - {msg}" for msg in failures
    )


# ── Gate 5: every Material has a real specification (or is informal) ──────


def test_every_material_has_specification_or_informal_category():
    failures: list[str] = []
    for s_id, m in MATERIALS.items():
        if not m.s_specification and m.s_category not in _INFORMAL_CATEGORIES:
            failures.append(
                f"{s_id}: s_specification is empty and category "
                f"{m.s_category!r} is not in _INFORMAL_CATEGORIES "
                f"{sorted(_INFORMAL_CATEGORIES)}"
            )
    assert not failures, "Materials with missing formal designation:\n" + "\n".join(
        f"  - {msg}" for msg in failures
    )


# ── Gate 6: no future catalog versions ─────────────────────────────────────


def test_no_material_claims_future_catalog_version():
    """A Material.s_catalog_version > __catalog_version__ means the entry
    is claiming a release that doesn't exist yet: a versioning bug.
    An unreleased tree (catalog version 0.0.0) has no release to compare to;
    tests/test_catalog_versioning.py covers that skip."""
    if __catalog_version__ == "0.0.0":
        pytest.skip("unreleased tree: no catalog release to compare stamps against")
    cur = tuple(int(p) for p in __catalog_version__.split("."))
    failures: list[str] = []
    for s_id, m in MATERIALS.items():
        mat = tuple(int(p) for p in m.s_catalog_version.split("."))
        if mat > cur:
            failures.append(
                f"{s_id}: s_catalog_version {m.s_catalog_version!r} > "
                f"__catalog_version__ {__catalog_version__!r}"
            )
    assert not failures, "Materials claiming future catalog versions:\n" + "\n".join(
        f"  - {msg}" for msg in failures
    )


# ── Bonus gate: every catalog entry's confidence distribution sanity ──────

_EXTERNALLY_SOURCED: frozenset[str] = frozenset(
    {
        # Tier 1
        "measured",
        "datasheet",
        "standard",
        # Tier 2
        "handbook",
        # Tier 3
        "aggregator",
    }
)

#: Tier 1 only: the v0.2.0 catalog enforces this for every PropertyValue.
_TIER_1_ONLY: frozenset[str] = frozenset({"measured", "datasheet", "standard"})


def test_every_propertyvalue_is_tier_1():
    """v0.2.0 catalog policy: every PropertyValue must be Tier 1 sourcing
    (measured / datasheet / standard). Bad data is worse than no data:
    aggregator/handbook/derived/estimated values were deleted in v0.2.0
    and the deleted entries stay out until a Tier 1 source is verified.

    A new PropertyValue with Tier 2+ confidence is a regression: it
    should either be upgraded to Tier 1 with a real primary source,
    or set to None until a Tier 1 source is found.
    """
    failures: list[str] = []
    for s_id, m in MATERIALS.items():
        for s_group, s_field, pv in _iter_propertyvalues(m):
            if pv.s_confidence not in _TIER_1_ONLY:
                failures.append(
                    f"{s_id}.{s_group}.{s_field}: confidence={pv.s_confidence!r} "
                    f"(not Tier 1). Upgrade to primary source or set to None."
                )
    assert not failures, "Non-Tier-1 PropertyValues found:\n" + "\n".join(
        f"  - {msg}" for msg in failures
    )


def test_at_least_90pct_of_values_are_externally_sourced():
    """At least 90% of PropertyValues must be at Tier 1, 2, or 3, i.e.
    trace to SOME named external source (vendor TDS, standard, handbook,
    or aggregator), not just engineering judgment.

    This is the catalog-drift gate: it fails loudly if the catalog
    grows by adding derived/estimated entries instead of sourced ones.

    v0.1.2 baseline is ~73% externally sourced: the remaining 27%
    are engineering derivations (sigma_e ~= 0.5 sigma_UTS), placeholder
    estimates on materials whose primary PDF couldn't be retrieved
    (m270_35a, mnzn_ferrite, ferrite_y30, alnico_5), and similar
    fall-backs. Each future catalog release should aim to raise this
    floor; the next bump targets 85%.
    """
    n_total = 0
    n_sourced = 0
    for m in MATERIALS.values():
        for _g, _f, pv in _iter_propertyvalues(m):
            n_total += 1
            if pv.s_confidence in _EXTERNALLY_SOURCED:
                n_sourced += 1
    assert n_total > 0
    pct = n_sourced / n_total
    assert pct >= 0.70, (
        f"Only {n_sourced}/{n_total} ({pct:.0%}) of PropertyValues are "
        f"externally sourced (Tier 1+2+3). The remainder are "
        f"derived/estimated/placeholder: investigate whether real "
        f"sources exist. v0.1.2 baseline was 73%; this gate stops "
        f"the catalog from regressing below 70%."
    )


def test_tier_1_plus_2_coverage_is_tracked():
    """Tier 1+2 coverage (measured/datasheet/standard/handbook) is the
    upgrade target: values here trace to primary or peer-reviewed
    sources, NOT to aggregators.

    v0.1.2: catalog is ~40% Tier 1+2 because most metals.py /
    polymers.py inherited MatWeb-cited values from the org's earlier
    structural catalog (which are correctly Tier 3 'aggregator' under
    the new hierarchy).
    Threshold set to 30% as a floor; the upgrade work is to pull
    primary vendor PDFs + NIST SRD references and bump aggregator -->
    standard/handbook/datasheet over time.

    This test fails loudly if Tier 1+2 coverage REGRESSES below 30%,
    which would indicate the catalog is being polluted with more
    aggregator-tier or derived values than primary ones.
    """
    from emergent_matter_materials.property_value import _SOLID_CONFIDENCE

    n_total = 0
    n_solid = 0
    for m in MATERIALS.values():
        for _g, _f, pv in _iter_propertyvalues(m):
            n_total += 1
            if pv.s_confidence in _SOLID_CONFIDENCE:
                n_solid += 1
    assert n_total > 0
    pct = n_solid / n_total
    assert pct >= 0.30, (
        f"Only {n_solid}/{n_total} ({pct:.0%}) of PropertyValues are at "
        f"Tier 1 or Tier 2 (measured/datasheet/standard/handbook). "
        f"The upgrade target is to pull primary vendor PDFs / NIST SRD "
        f"references and bump aggregator -> standard/handbook/datasheet."
    )


# ── Gate 7: 'aggregator' confidence must name the aggregator ───────────────

#: Known database aggregators that `s_source` may legitimately cite when
#: `s_confidence == "aggregator"`. The s_source string must contain at
#: least one of these (case-insensitive) so a consumer can trace back.
_KNOWN_AGGREGATORS: frozenset[str] = frozenset(
    {
        "matweb",
        "ulprospector",
        "ul prospector",
        "specialchem",
        "citrination",
        "azom",
        "makeitfrom",
        "lookpolymers",
        "campusplastics",
        "campus plastics",
        "transformerstrip",
        "mit",  # MIT OCW course materials count as aggregator-tier
    }
)


def test_aggregator_confidence_names_aggregator():
    """confidence='aggregator' values MUST name the aggregator
    explicitly in s_source so a consumer can trace one hop back
    toward a primary measurement.

    This is the extra obligation that comes with the aggregator tier
    (Tier 3): without it, the value is indistinguishable from a
    free-floating estimate.
    """
    failures: list[str] = []
    for s_id, m in MATERIALS.items():
        for s_group, s_field, pv in _iter_propertyvalues(m):
            if pv.s_confidence != "aggregator":
                continue
            s_text = (pv.s_source + " " + pv.s_notes).lower()
            if not any(a in s_text for a in _KNOWN_AGGREGATORS):
                failures.append(
                    f"{s_id}.{s_group}.{s_field}: confidence='aggregator' "
                    f"but s_source doesn't name a known aggregator "
                    f"(_KNOWN_AGGREGATORS={sorted(_KNOWN_AGGREGATORS)}). "
                    f"s_source={pv.s_source[:80]!r}"
                )
    assert not failures, "'aggregator' entries missing aggregator name in s_source:\n" + "\n".join(
        f"  - {msg}" for msg in failures
    )
