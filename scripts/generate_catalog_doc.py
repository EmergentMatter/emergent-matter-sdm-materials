"""Generate ``docs/catalog.md``: human-readable catalog inventory.

Walks every Material in ``MATERIALS``, walks each populated group, and
emits a markdown document with one section per material listing every
PropertyValue: value, units, condition, confidence, source.

Run from repo root:

    uv run python scripts/generate_catalog_doc.py

This script is the only thing that writes ``docs/catalog.md``. If you
edit the markdown by hand, the next run overwrites your changes: fix
the catalog files instead, then regenerate.
"""

from __future__ import annotations

import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

# Allow running from anywhere; resolve repo root relative to this script.
_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "src"))

# noqa: E402 for both imports below -- must follow the sys.path.insert
# above, which makes the package importable when this script is run from
# outside the repo root; there's no earlier point they could move to.
from emergent_matter_materials import (  # noqa: E402
    MATERIALS,
    __catalog_version__,
    __version__,
    list_aliases,
)
from emergent_matter_materials.property_value import PropertyValue  # noqa: E402

_OUTPUT_PATH = _REPO_ROOT / "docs" / "catalog.md"

#: Display order for groups within each material section.
_GROUP_ORDER = ("structural", "electromagnetic", "thermal", "manufacturing", "crystal_anisotropy")

#: Display order for fields within each group. Anything not listed
#: appears in dataclass-declared order after the listed fields.
_FIELD_ORDER = {
    "structural": (
        "youngs_modulus",
        "poisson_ratio",
        "yield_stress",
        "ultimate_tensile",
        "flexural_strength",
        "compressive_strength",
        "fatigue_endurance",
        "density",
        "hardness_vickers",
    ),
    "electromagnetic": (
        "resistivity_at_20C",
        "temp_coeff_resistivity",
        "relative_permeability",
        "saturation_flux",
        "remanence",
        "coercivity",
        "energy_product_max",
        "temp_coeff_remanence",
        "core_loss",
        "dielectric_strength",
        "relative_permittivity",
    ),
    "thermal": (
        "thermal_conductivity",
        "specific_heat",
        "max_operating_temp",
        "thermal_expansion",
        "thermal_expansion_perpendicular",
        "glass_transition",
        "curie_temp",
        "melting_temp",
        "emissivity",
    ),
    "crystal_anisotropy": (
        # Cubic-trio first, then non-cubic constants, then crystallographic
        # / micromechanical scalars. Reads top-to-bottom like the source
        # paper tables (Overton-Gaffney, Fisher-Renken, Hirosawa et al.).
        "c11",
        "c12",
        "c44",
        "c13",
        "c33",
        "c66",
        "burgers_vector",
        "stacking_fault_energy",
        "crss_initial",
    ),
}


def _format_value(pv: PropertyValue) -> str:
    """Format a PropertyValue's numeric value with units string.

    Uses scientific notation for very small or very large magnitudes;
    otherwise plain float. Dimensionless values omit the units.
    """
    d_value = pv.d_value
    s_units = pv.s_units
    abs_v = abs(d_value)
    if abs_v == 0:
        s_num = "0"
    elif abs_v < 1e-3 or abs_v >= 1e5:
        s_num = f"{d_value:.3e}"
    elif abs_v >= 100:
        s_num = f"{d_value:.1f}"
    else:
        s_num = f"{d_value:g}"
    if s_units == "":
        return s_num
    return f"{s_num} {s_units}"


def _format_property_row(s_field: str, pv: PropertyValue) -> str:
    """One markdown table row for a single PropertyValue.

    Columns: property | value+units | condition | confidence | source.
    Source is the FIRST line of s_source (after stripping " -- ..." trailing
    citation-detail) to keep the table readable; the full s_source lives
    in the Python catalog files.
    """
    s_value = _format_value(pv)
    s_condition = pv.s_condition.replace("|", "\\|") if pv.s_condition else ""
    s_confidence = pv.s_confidence
    # Source: keep the document-identifier portion (everything before " -- ",
    # which is our convention for separating citation from value detail).
    # If no " -- " separator, take first 140 chars. Collapse whitespace.
    s_source = pv.s_source.split(" -- ")[0].strip()
    s_source = " ".join(s_source.split())  # collapse \n + multi-space
    if len(s_source) > 140:
        s_source = s_source[:137].rstrip() + "..."
    s_source = s_source.replace("|", "\\|")
    return f"| `{s_field}` | {s_value} | {s_condition} | `{s_confidence}` | {s_source} |"


def _iter_group_fields(group_obj, s_group_name: str):
    """Yield (s_field_name, PropertyValue) for every populated field in a group.

    Walks in _FIELD_ORDER first, then any remaining dataclass-declared
    fields. Skips None values.
    """
    seen = set()
    if s_group_name in _FIELD_ORDER:
        for s_field in _FIELD_ORDER[s_group_name]:
            if s_field in group_obj.__dataclass_fields__:
                pv = getattr(group_obj, s_field)
                if pv is not None:
                    seen.add(s_field)
                    yield s_field, pv
    for s_field in group_obj.__dataclass_fields__:
        if s_field in seen:
            continue
        pv = getattr(group_obj, s_field, None)
        if pv is None:
            continue
        # Skip non-PropertyValue fields (e.g. Manufacturing's s_recommended_processes)
        if not isinstance(pv, PropertyValue):
            continue
        yield s_field, pv


def _build_inventory_table() -> str:
    """Top-level inventory table: one row per material."""
    out = [
        "| Material ID | Category | Specification |",
        "|---|---|---|",
    ]
    for s_id in sorted(MATERIALS):
        m = MATERIALS[s_id]
        s_spec = m.s_specification.replace("|", "\\|")
        if len(s_spec) > 90:
            s_spec = s_spec[:87].rstrip() + "..."
        out.append(f"| `{s_id}` | {m.s_category} | {s_spec} |")
    return "\n".join(out)


def _build_alias_table() -> str:
    """Alias → canonical ID table."""
    aliases = list_aliases()
    out = [
        "| Alias | Resolves to |",
        "|---|---|",
    ]
    for s_alias, s_canonical in sorted(aliases.items()):
        out.append(f"| `{s_alias}` | `{s_canonical}` |")
    return "\n".join(out)


def _build_material_section(s_id: str) -> str:
    """One full markdown section for a single material."""
    m = MATERIALS[s_id]
    out = [f"### `{s_id}`", ""]
    out.append(f"**Description:** {m.s_description}")
    out.append("")
    out.append(f"**Specification:** {m.s_specification}")
    out.append("")
    out.append(
        f"**Category:** `{m.s_category}` &nbsp;·&nbsp; "
        f"**Catalog version:** {m.s_catalog_version} &nbsp;·&nbsp; "
        f"**Last reviewed:** {m.s_last_reviewed}"
    )
    out.append("")

    # Collect populated groups
    populated_groups = []
    for s_group_name in _GROUP_ORDER:
        group_obj = getattr(m, s_group_name, None)
        if group_obj is None:
            continue
        rows = list(_iter_group_fields(group_obj, s_group_name))
        if rows:
            populated_groups.append((s_group_name, rows))

    if not populated_groups:
        out.append("*(No populated property groups: all Tier-1 sources still TODO.)*")
        out.append("")
        return "\n".join(out)

    for s_group_name, rows in populated_groups:
        out.append(f"#### {s_group_name.replace('_', ' ').title()}")
        out.append("")
        # Surface non-PropertyValue group-level metadata where useful.
        # crystal_anisotropy carries s_crystal_structure (FCC/BCC/HCP/...)
        # which is essential context for reading the C_ij values.
        if s_group_name == "crystal_anisotropy":
            group_obj = m.crystal_anisotropy
            out.append(f"**Crystal structure:** `{group_obj.s_crystal_structure}`")
            if group_obj.s_crystal_structure in ("FCC", "BCC"):
                A = group_obj.d_zener_anisotropy
                out.append(f"&nbsp;·&nbsp; **Zener anisotropy:** `{A:.2f}` (= 2·C44 / (C11-C12))")
            elif group_obj.s_crystal_structure == "HCP":
                out.append(
                    f"&nbsp;·&nbsp; **Derived C66:** "
                    f"`{group_obj.d_c66_derived_Pa:.3e} Pa` "
                    f"(= (C11-C12)/2)"
                )
            out.append("")
        # Surface the consumer-safe strength basis (v1.10.0) so a downstream
        # UI can show "strength basis: yield" vs "strength basis: UTS" without
        # re-deriving it. Mirrors get_structural_strength() resolution.
        if s_group_name == "structural":
            group_obj = m.structural
            s_basis = group_obj.s_strength_basis
            if s_basis == "unknown":
                out.append("**Strength basis:** none (no `yield_stress` or `ultimate_tensile`)")
            else:
                _strength = group_obj.resolve_design_strength()
                out.append(
                    f"**Strength basis:** `{s_basis}` &nbsp;·&nbsp; "
                    f"{_strength.d_value_Pa / 1e6:.1f} MPa &nbsp;·&nbsp; the "
                    f"design allowable `get_structural_strength()` returns"
                )
            out.append("")
        out.append("| Property | Value | Condition | Confidence | Source (head) |")
        out.append("|---|---|---|---|---|")
        for s_field, pv in rows:
            out.append(_format_property_row(s_field, pv))
        out.append("")

    return "\n".join(out)


def _build_summary_stats() -> str:
    """Top-of-document summary: catalog version, counts, confidence breakdown."""
    n_materials = len(MATERIALS)

    by_cat = Counter()
    confidence_counts = Counter()
    n_pv = 0
    for m in MATERIALS.values():
        by_cat[m.s_category] += 1
        for s_group in _GROUP_ORDER:
            group_obj = getattr(m, s_group, None)
            if group_obj is None:
                continue
            for _, pv in _iter_group_fields(group_obj, s_group):
                confidence_counts[pv.s_confidence] += 1
                n_pv += 1

    out = []
    out.append(
        f"**Catalog version:** `{__catalog_version__}` &nbsp;·&nbsp; "
        f"**Package version:** `{__version__}`"
    )
    out.append("")
    out.append(
        f"**{n_materials} materials** &nbsp;·&nbsp; "
        f"**{n_pv} PropertyValues** &nbsp;·&nbsp; "
        f"**100% Tier 1**"
    )
    out.append("")
    out.append("**Confidence breakdown:**")
    out.append("")
    out.append("| `s_confidence` | Count | Share |")
    out.append("|---|---:|---:|")
    for s_conf in ("measured", "datasheet", "standard"):
        n = confidence_counts.get(s_conf, 0)
        pct = (100.0 * n / n_pv) if n_pv else 0.0
        out.append(f"| `{s_conf}` | {n} | {pct:.1f}% |")
    out.append("")
    out.append("**By category:**")
    out.append("")
    out.append("| Category | Count |")
    out.append("|---|---:|")
    for cat in sorted(by_cat):
        out.append(f"| `{cat}` | {by_cat[cat]} |")
    return "\n".join(out)


def build() -> str:
    """Return the full markdown document as one string."""
    s_generated_utc = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")

    out = []
    out.append("# emergent-matter-sdm-materials: catalog inventory")
    out.append("")
    out.append(
        "**This document is auto-generated. Edit the Python catalog "
        "files, then regenerate with `uv run python scripts/"
        "generate_catalog_doc.py`. Do not hand-edit this file.**"
    )
    out.append("")
    out.append(f"_Last generated: {s_generated_utc}_")
    out.append("")
    out.append("---")
    out.append("")
    out.append("## Summary")
    out.append("")
    out.append(_build_summary_stats())
    out.append("")
    out.append("---")
    out.append("")
    out.append("## Inventory")
    out.append("")
    out.append(_build_inventory_table())
    out.append("")
    out.append("---")
    out.append("")
    out.append("## Aliases (short names accepted by `get()` / `get_material()`)")
    out.append("")
    out.append(_build_alias_table())
    out.append("")
    out.append(
        "**Deliberately NOT registered** (too ambiguous for engineering "
        "optimization without a disambiguator):"
    )
    out.append("")
    out.append('- `"Al"`, which alloy? 6061-T6 vs 7075 vs cast.')
    out.append('- `"NdFeB"`, which grade? N35 / N42 / N50 differ by ~30% in B_r.')
    out.append('- `"PA12"`, which process? SLS vs MJF vs injection-molded.')
    out.append('- `"Steel"`, which alloy? 1018 mild vs 4140 vs 304 stainless.')
    out.append("")
    out.append("---")
    out.append("")
    out.append("## Material details")
    out.append("")
    out.append(
        "Properties are listed only when a Tier-1 primary source "
        "exists. Missing fields (`youngs_modulus` left out, etc.) mean "
        "the verification work is still outstanding "
        "and consumers should "
        "treat them as unknown rather than zero."
    )
    out.append("")

    # Group by category for navigation
    by_cat = {}
    for s_id, m in MATERIALS.items():
        by_cat.setdefault(m.s_category, []).append(s_id)

    for s_cat in sorted(by_cat):
        out.append(f"### Category: `{s_cat}`")
        out.append("")
        for s_id in sorted(by_cat[s_cat]):
            out.append(_build_material_section(s_id))
        out.append("---")
        out.append("")

    out.append("## Source-priority hierarchy")
    out.append("")
    out.append("All values in this catalog satisfy **Tier 1**:")
    out.append("")
    out.append("| `s_confidence` | What it means | Examples |")
    out.append("|---|---|---|")
    # Each row below is one literal markdown table cell; splitting the
    # string would embed a line break in the rendered cell text, so these
    # stay over the line limit on purpose. noqa: E501 on each.
    out.append(
        "| `measured` | Direct lab measurement on the specific material lot | NREL/IJHMT 2018 M19 lamination stack k |"  # noqa: E501
    )
    out.append(
        "| `datasheet` | Vendor technical data sheet | Arnold N42 PDF, Carpenter Hiperco E200, Victrex 450G TDS |"  # noqa: E501
    )
    out.append(
        "| `standard` | National/international published reference data | NIST SRD/JPCRD, ASTM, EN/ISO, MMPDS, Aluminum Association ADM |"  # noqa: E501
    )
    out.append("")
    out.append(
        "Aggregator data (MatWeb, AZoM, MakeItFrom, ULProspector) and "
        "generic handbook references are **forbidden** as primary "
        "sources: they're acceptable only as secondary cross-checks "
        "captured in `s_notes`."
    )
    out.append("")
    out.append(
        "When two Tier-1 sources disagree, the catalog records both "
        "in `s_notes` per the source-priority conflict-resolution rule "
        "(no averaging; higher tier wins; document the loser)."
    )
    out.append("")

    return "\n".join(out)


def main() -> None:
    s_doc = build()
    _OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    _OUTPUT_PATH.write_text(s_doc, encoding="utf-8")
    n_lines = s_doc.count("\n") + 1
    print(f"Wrote {_OUTPUT_PATH.relative_to(_REPO_ROOT)} ({n_lines} lines, {len(s_doc):,} bytes)")


if __name__ == "__main__":
    main()
