"""Public accessor API: MATERIALS dict + flat + provenance lookups.

Three layers of access:

1. **Object access**: ``get_material("m19")`` returns the full
   ``Material`` object. Use this when you want to navigate to a
   specific group/property: ``mat.structural.d_yield_stress_Pa``.

2. **Flat SI accessor**: ``get("m19", "B_sat")`` returns a bare float
   in SI units. Backward-compatible with sdm-core's existing
   ``materials.get()`` so the import-shim migration is a no-op at
   call sites.

3. **Provenance accessor**: ``get_with_metadata("m19", "B_sat")``
   returns the full ``PropertyValue`` (number + units + source +
   condition + confidence + notes). Use this for traceable
   optimization runs where the optimization artifact should record
   not just "B_sat=2.03" but "B_sat=2.03 from AK Steel M19 datasheet
   at B=1.5T f=60Hz, confidence=datasheet."

**Aliases.**
``_ALIASES`` maps short engineering shorthand (``"Cu"``, ``"M19"``) to
canonical catalog keys (``"pure_copper"``, ``"m19_silicon_steel"``).
The rule: an alias only lands if it has a **single canonical
interpretation** OR the alias **carries the disambiguating
grade/temper in the alias itself**. Bare ambiguous strings like
``"Al"`` (which alloy? 6061-T6? 7075? cast?) and ``"NdFeB"`` (which
grade? N35 / N42 / N50?) are **deliberately omitted**: engineering
optimization needs the disambiguator, not a coin flip.
"""

from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING, TypedDict

from emergent_matter_materials.property_value import PropertyValue
from emergent_matter_materials.structural import (
    StructuralStrength,
    StructuralStrengthUnavailable,
)
from emergent_matter_materials.units_map import _PROPERTY_EXPECTED_UNITS

if TYPE_CHECKING:
    from emergent_matter_materials.material import Material


# ============================================================================
# MATERIALS catalog: populated by catalog/_loader.py at module import
# ============================================================================

#: The full catalog. Populated by ``catalog/_loader.load_all()`` at import
#: time. Keys are canonical snake_case material IDs; values are
#: :class:`~emergent_matter_materials.material.Material` instances with
#: per-property provenance.
MATERIALS: dict[str, Material] = {}


# ============================================================================
# Aliases: short names that resolve to canonical s_id
# ============================================================================

#: Short-name → canonical-s_id map. See module docstring for the
#: disambiguation rule.
# fmt: off
# Hand-aligned so a scan down the value column is easy; ruff format would
# collapse the alignment without changing meaning.
_ALIASES: dict[str, str] = {
    # ── Unambiguous (pure forms; only one canonical material)
    "Cu":         "pure_copper",
    # "Fe" intentionally not registered: pure iron isn't in v0.1.0 catalog,
    # and the Fe alloys in the catalog are M19/M270/Hiperco/4140 which each
    # carry their own grade-disambiguating canonical names.

    # ── Specific grades / tempers (alias carries the disambiguator)
    "Al_6061_T6": "aluminum_6061_t6",
    "Al_1350":    "aluminum_1350_ec",   # EC-grade winding/conductor aluminium
    "Al_EC":      "aluminum_1350_ec",   # "electrical conductor grade" shorthand
    "Ti_6Al_4V":  "titanium_6al_4v",
    "SS304":      "stainless_304",
    "SS316":      "stainless_316",
    "SS17_4PH_H900": "stainless_17_4ph_h900",
    "17_4PH_H900": "stainless_17_4ph_h900",
    "C93200":     "c93200_bearing_bronze",
    "SAE_660":    "c93200_bearing_bronze",
    "Steel_4140": "steel_4140",
    "PEEK":       "peek_unfilled",
    "PEI":        "pei_ultem_1010",
    "NdFeB_N35":  "ndfeb_n35",
    "NdFeB_N42":  "ndfeb_n42",
    "NdFeB_N50":  "ndfeb_n50",
    "NdFeB_N42SH":"ndfeb_n42sh",
    "NdFeB_N42UH":"ndfeb_n42uh",
    "NdFeB_N42EH":"ndfeb_n42eh",
    "SmCo_2_17":  "smco_2_17",   # canonical Sm2Co17 alias (BHmax 28 MGOe Recoma 28 grade)
    "Recoma_28":  "smco_2_17",   # Arnold's commercial grade name for the same Recoma 28 entry
    "Alnico_5":   "alnico_5_cast",
    "AlNiCo_5":   "alnico_5_cast",
    "Hiperco":    "hiperco_50",

    # ── Print-process-tied (the consumer is the printing layer)
    "PA12_SLS":   "nylon12_sls",
    "PLA":        "pla_3dprint",
    "Prusament_PLA": "pla_3dprint",  # vendor-flavored alias for the same material
    "PETG":       "petg_3dprint",
    "Prusament_PETG": "petg_3dprint",

    # ── Insulation systems (added in v0.2.2 / v0.2.5)
    "Nomex_410":  "nomex_410",
    "Kapton_HN":  "kapton_hn",
    "Stycast_2850FT": "stycast_2850ft",
    "TPU_95A":    "tpu_elastollan_1195a",   # Shore 96A / 48D per the BASF range table
    "Elastollan_1195A": "tpu_elastollan_1195a",
    "MW_PAI_200": "mw_pai_class_200",
    "MW_PUR_130": "mw_pur_class_130",

    # ── Soft magnetic
    "M19":        "m19_silicon_steel",
    "M270_35A":   "m270_35a_silicon_steel",
    "Metglas_2605": "metglas_2605sa1",
    "Vitroperm_500F": "vitroperm_500f",
    "3C95":       "mnzn_ferrite_3c95",
    "MnZn_3C95":  "mnzn_ferrite_3c95",
    "MuMETAL":    "mu_metal",
    "Mu_Metal":   "mu_metal",

    # ── Ceramics
    "AD96":       "alumina_ad96",
    "Alumina_96": "alumina_ad96",
    "AlN_AN170":  "aln_maruwa_an170",

    # ── v0.2.0 Tier-1-only cleanup removed these aliases along with
    #    their materials for lack of Tier 1 sourcing; restoring them needs
    #    Tier 1 sources; some restored in v0.2.1:
    #   "M19" -> m19_silicon_steel  RESTORED in v0.2.1
    #   "MnZn" -> mnzn_ferrite        RESTORED as "3C95" -> mnzn_ferrite_3c95
    #   "ferrite_magnet" -> ferrite_y30
    #   "AlNiCo_5" -> alnico_5      RESTORED as "Alnico_5" -> alnico_5_cast
    #   "PLA_FDM" -> pla_fdm
    #   "PETG_FDM" -> petg_fdm        RESTORED as "PETG" -> petg_3dprint
    #   "TPU" -> tpu_95a            RESTORED as "TPU_95A" -> tpu_elastollan_1195a
}
# fmt: on

# Deliberately NOT in _ALIASES (would be ambiguous):
#   "Al", which alloy? 6061-T6 vs 7075 vs cast aluminum
#   "NdFeB", which grade? N35 / N42 / N50 differ by ~30% in B_r
#   "PA12", which process? SLS vs MJF vs injection-molded
#   "Steel", which alloy? 1018 mild vs 4140 vs 304 stainless


# ============================================================================
# Property dispatch: short SI property name → (group, field_name) path
# ============================================================================

#: Short property name → (group_attr, group_field) lookup. Used by
#: ``get()`` and ``get_with_metadata()`` to route flat names to the
#: right group + field path. Values are SI-native: there are no
#: conversion factors here; the catalog stores SI internally.
# fmt: off
# Hand-aligned so a scan down the value column is easy; ruff format would
# collapse the alignment without changing meaning.
_PROPERTY_MAP: dict[str, tuple[str, str]] = {
    # ── Structural
    "rho":          ("structural", "density"),
    "E":            ("structural", "youngs_modulus"),
    "nu":           ("structural", "poisson_ratio"),
    "sigma_y":      ("structural", "yield_stress"),
    "UTS":          ("structural", "ultimate_tensile"),
    "sigma_flex":   ("structural", "flexural_strength"),
    "sigma_f":      ("structural", "fatigue_endurance"),
    "sigma_c":      ("structural", "compressive_strength"),
    "HV":           ("structural", "hardness_vickers"),
    # ── Electromagnetic
    "resistivity":  ("electromagnetic", "resistivity_at_20C"),
    "alpha_rho":    ("electromagnetic", "temp_coeff_resistivity"),
    "mu_r":         ("electromagnetic", "relative_permeability"),
    "mu_r_recoil":  ("electromagnetic", "recoil_permeability"),
    "B_sat":        ("electromagnetic", "saturation_flux"),
    "B_r":          ("electromagnetic", "remanence"),
    "H_c":          ("electromagnetic", "coercivity"),
    "alpha_Br":     ("electromagnetic", "temp_coeff_remanence"),
    "alpha_HcJ":    ("electromagnetic", "temp_coeff_coercivity"),
    "BH_max":       ("electromagnetic", "energy_product_max"),
    "core_loss":    ("electromagnetic", "core_loss"),
    "E_dielectric": ("electromagnetic", "dielectric_strength"),
    "epsilon_r":    ("electromagnetic", "relative_permittivity"),
    # ── Thermal
    "k_thermal":    ("thermal", "thermal_conductivity"),
    "c_p":          ("thermal", "specific_heat"),
    "T_max":        ("thermal", "max_operating_temp"),
    "CTE":          ("thermal", "thermal_expansion"),
    "CTE_perp":     ("thermal", "thermal_expansion_perpendicular"),
    "T_g":          ("thermal", "glass_transition"),
    "T_c":          ("thermal", "curie_temp"),
    "T_melt":       ("thermal", "melting_temp"),
    "emissivity":   ("thermal", "emissivity"),
    # ── Crystal anisotropy (v0.4.0)
    "C11":          ("crystal_anisotropy", "c11"),
    "C12":          ("crystal_anisotropy", "c12"),
    "C13":          ("crystal_anisotropy", "c13"),
    "C33":          ("crystal_anisotropy", "c33"),
    "C44":          ("crystal_anisotropy", "c44"),
    "C66":          ("crystal_anisotropy", "c66"),
    "b":            ("crystal_anisotropy", "burgers_vector"),
    "gamma_SFE":    ("crystal_anisotropy", "stacking_fault_energy"),
    "tau_CRSS":     ("crystal_anisotropy", "crss_initial"),
}
# fmt: on


# ============================================================================
# Accessor functions
# ============================================================================


def get_material(s_material: str) -> Material:
    """Resolve an alias or canonical s_id to a Material object.

    Args:
        s_material: Either a canonical ``s_id`` (e.g. ``"pure_copper"``)
            or a registered alias (e.g. ``"Cu"``). Aliases are documented
            in ``_ALIASES``; bare ambiguous strings (``"Al"``, ``"NdFeB"``)
            are deliberately not registered.

    Raises:
        KeyError: ``s_material`` is neither a canonical key nor a registered alias.
    """
    s_key = _ALIASES.get(s_material, s_material)
    if s_key not in MATERIALS:
        raise KeyError(
            f"Unknown material {s_material!r}. "
            f"Not found in MATERIALS or _ALIASES. "
            f"Known aliases include: {sorted(_ALIASES)[:8]}..."
        )
    return MATERIALS[s_key]


def get_with_metadata(s_material: str, s_property: str) -> PropertyValue:
    """Return the full ``PropertyValue`` for a material+property pair.

    Useful when downstream code needs to record provenance, e.g. an
    optimization artifact citing "yield_stress=415 MPa from MatWeb
    4140 QT, confidence=handbook." Use this OVER ``get()`` whenever
    metadata matters.

    Raises:
        KeyError: material name or property name unrecognized.
        ValueError: the material doesn't have the requested property
            (the group is None, or the field within the group is None).
    """
    mat = get_material(s_material)

    if s_property not in _PROPERTY_MAP:
        raise KeyError(f"Unknown property {s_property!r}. Available: {sorted(_PROPERTY_MAP)}")
    s_group, s_field = _PROPERTY_MAP[s_property]

    group_obj = getattr(mat, s_group)
    if group_obj is None:
        raise ValueError(
            f"Material {mat.s_id!r} has no {s_group} group (cannot get property {s_property!r})"
        )

    pv = getattr(group_obj, s_field)
    if pv is None:
        raise ValueError(
            f"Material {mat.s_id!r} has {s_group} group but {s_field!r} "
            f"is None (material doesn't have this property)"
        )
    return pv


def get(s_material: str, s_property: str) -> float:
    """Return a property's bare SI float for a material.

    Backward-compatible with sdm-core's existing ``materials.get()``.
    Storage is SI internally so there's no conversion involved: this
    is just a shortcut over ``get_with_metadata().d_value``.

    Args:
        s_material: Material identifier (canonical s_id or alias).
        s_property: Short property name. Use ``list_properties()`` for
            the full set.

    Raises:
        KeyError: material name or property name unrecognized.
        ValueError: material doesn't have the requested property.
    """
    return get_with_metadata(s_material, s_property).d_value


def list_materials(s_category: str | None = None) -> list[str]:
    """Return sorted list of canonical material IDs.

    Args:
        s_category: If given, restrict to materials in that category.
            Use ``None`` (default) for the full catalog.
    """
    if s_category is None:
        return sorted(MATERIALS)
    return sorted(s_id for s_id, mat in MATERIALS.items() if mat.s_category == s_category)


def list_properties() -> list[str]:
    """Return sorted list of short property names accepted by ``get()``."""
    return sorted(_PROPERTY_MAP)


def list_aliases() -> dict[str, str]:
    """Return a copy of the alias→canonical-id map."""
    return dict(_ALIASES)


def material_summary(s_material: str) -> str:
    """Return a multi-line human-readable summary of a material.

    Shows: s_id, s_description, s_specification, s_category,
    populated groups, and the structural top-line (E, σ_y, ρ).
    """
    mat = get_material(s_material)
    lines = [
        f"Material: {mat.s_id} ({mat.s_specification or '<no spec>'})",
        f"  Description: {mat.s_description}",
        f"  Category:    {mat.s_category}",
        f"  Catalog:     v{mat.s_catalog_version}, reviewed {mat.s_last_reviewed}",
        "  Groups:      "
        + ", ".join(
            g_name
            for g_name in ("structural", "electromagnetic", "thermal", "manufacturing")
            if getattr(mat, g_name) is not None
        ),
    ]
    if mat.structural is not None:
        s = mat.structural
        parts: list[str] = []
        if s.youngs_modulus is not None:
            parts.append(f"E = {s.d_youngs_modulus_Pa:.3e} Pa")
        # Strength via the consumer-safe resolver: must NOT assume yield_stress
        # exists (e.g. SLS PA12 has only ultimate_tensile). Show the basis.
        try:
            strength = s.resolve_design_strength()
            parts.append(f"sigma = {strength.d_value_Pa:.3e} Pa (basis: {strength.s_basis})")
        except StructuralStrengthUnavailable:
            parts.append("sigma = n/a (no strength basis)")
        if s.density is not None:
            parts.append(f"rho = {s.d_density_kg_m3} kg/m^3")
        if parts:
            lines.append("  " + ", ".join(parts))
    return "\n".join(lines)


#: The five property-group attribute names on a Material, in display order.
_GROUP_NAMES: tuple[str, ...] = (
    "structural",
    "electromagnetic",
    "thermal",
    "manufacturing",
    "crystal_anisotropy",
)


class _GroupCoverage(TypedDict):
    """Per-group entry of a :func:`coverage` report. See that function's
    docstring for the field semantics."""

    present: bool
    fields: dict[str, bool]
    n_present: int
    n_total: int
    missing: list[str]
    composites: dict[str, bool | int]


class CoverageReport(TypedDict):
    """Return shape of :func:`coverage`. Still a plain ``dict`` at runtime --
    this only adds static typing on top of the shape documented there."""

    s_id: str
    s_category: str
    groups: dict[str, _GroupCoverage]


def coverage(material: str | Material) -> CoverageReport:
    """Machine-readable coverage report: what data a material has vs. lacks.

    A boring, side-effect-free introspection helper so a consumer (e.g. a
    motor/actuator optimizer) can ask "what can I safely read off this
    material?" WITHOUT exception-driven probing through ``get_with_metadata``
    or parsing the human ``material_summary``. It computes NO physics, adds NO
    data, and does not touch ``get`` / ``get_with_metadata`` behavior or the
    provenance rules.

    Args:
        material: a catalog id / alias (``str``, resolved via
            :func:`get_material`) OR a ``Material`` object directly.

    Returns a nested ``dict``::

        {
          "s_id": "m270_35a_silicon_steel",
          "s_category": "soft_magnetic",
          "groups": {
            "<group>": {
              "present": bool,            # the group itself is not None
              "fields": {name: bool},     # scalar PropertyValue slots: populated?
              "n_present": int,
              "n_total": int,
              "missing": [name, ...],     # sorted; the False entries of `fields`
              "composites": {name: bool|int},   # bh_curve/steinmetz -> bool;
                                                 # rotational_loss_models -> count
            },
            ...  # all five groups always keyed; absent groups -> present=False
          },
        }

    Field classification (driven by existing catalog structure, not hardcoded
    physics):

    - A group field whose name is in ``_PROPERTY_EXPECTED_UNITS`` is a scalar
      ``PropertyValue`` slot; it is "present" iff non-None.
    - A composite field (``bh_curve``, ``steinmetz``) reports a present/absent
      ``bool``; a collection/mapping composite (``rotational_loss_models``,
      Manufacturing ``process_fit``) reports an ``int`` count.
    - Plain string metadata (e.g. ``crystal_anisotropy.s_crystal_structure``)
      is not a data slot and is omitted from the accounting.

    NOTE: "missing" means the field is ``None``, which may be a genuine
    sourcing gap OR N/A-by-physics (e.g. ``c66`` on a cubic crystal,
    ``saturation_flux`` on a permanent magnet). This helper reports presence,
    not whether a field *ought* to be filled; consult the catalog s_notes for
    the N/A-vs-gap distinction.
    """
    mat = get_material(material) if isinstance(material, str) else material

    groups: dict[str, _GroupCoverage] = {}
    for g_name in _GROUP_NAMES:
        group = getattr(mat, g_name, None)
        if group is None:
            groups[g_name] = {
                "present": False,
                "fields": {},
                "n_present": 0,
                "n_total": 0,
                "missing": [],
                "composites": {},
            }
            continue

        fields_cov: dict[str, bool] = {}
        composites: dict[str, bool | int] = {}
        for f in dataclasses.fields(group):
            val = getattr(group, f.name)
            if f.name in _PROPERTY_EXPECTED_UNITS:
                fields_cov[f.name] = val is not None  # scalar PV slot
            elif isinstance(val, str):
                continue  # metadata, not a data slot
            elif isinstance(val, (tuple, list, dict)):
                composites[f.name] = len(val)  # collection composite -> count
            else:
                composites[f.name] = val is not None  # singular composite -> present?

        groups[g_name] = {
            "present": True,
            "fields": fields_cov,
            "n_present": sum(1 for v in fields_cov.values() if v),
            "n_total": len(fields_cov),
            "missing": sorted(k for k, v in fields_cov.items() if not v),
            "composites": composites,
        }

    return {"s_id": mat.s_id, "s_category": mat.s_category, "groups": groups}


def get_structural_strength(
    material: str | Material, *, ultimate_derate: float | None = None
) -> StructuralStrength:
    """Resolve a material's usable structural strength scalar + its basis.

    Consumer-safe entry point so structural tools (FEM stress constraints,
    material-selection dropdowns) get a single documented allowable WITHOUT
    each re-implementing a yield-then-ultimate fallback policy. Mirrors
    :func:`coverage` ergonomics: accepts an id / alias string OR a ``Material``.

    Resolution (see :meth:`Structural.resolve_design_strength`):
    ``yield_stress`` -> ``ultimate_tensile`` (optionally derated) -> raise.
    ``result.s_basis`` is ``"yield_stress"``, ``"ultimate_tensile"``, or
    ``"derated_ultimate_tensile"``, so a UI can show the strength basis and a
    consumer never has to guess whether it got a yield or an ultimate value.

    Args:
        material: catalog id / alias (``str``) OR a ``Material`` object.
        ultimate_derate: optional caller-owned factor in ``(0, 1]``, applied
            only on the ``ultimate_tensile`` fallback (basis then becomes
            ``"derated_ultimate_tensile"``). The factor is an application
            safety choice, never catalog data.

    Raises:
        KeyError: unknown material id / alias.
        StructuralStrengthUnavailable: the material has no structural group, or
            neither ``yield_stress`` nor ``ultimate_tensile`` is populated.
    """
    mat = get_material(material) if isinstance(material, str) else material
    if mat.structural is None:
        raise StructuralStrengthUnavailable(
            f"Material {mat.s_id!r} has no structural group; no strength basis."
        )
    return mat.structural.resolve_design_strength(ultimate_derate=ultimate_derate)


def register_material(s_name: str, m: Material) -> None:
    """Add or update a material entry in the runtime catalog.

    Validates that ``s_name`` matches ``m.s_id`` (catch typos). For
    introducing aliases, the caller must also append to ``_ALIASES``
    explicitly: register_material doesn't manage aliases.

    Raises:
        ValueError: ``s_name`` doesn't match ``m.s_id``.
    """
    if s_name != m.s_id:
        raise ValueError(f"register_material name {s_name!r} != Material.s_id {m.s_id!r}")
    MATERIALS[s_name] = m


__all__ = [
    "MATERIALS",
    "_ALIASES",
    "_PROPERTY_MAP",
    "CoverageReport",
    "coverage",
    "get",
    "get_material",
    "get_structural_strength",
    "get_with_metadata",
    "list_aliases",
    "list_materials",
    "list_properties",
    "material_summary",
    "register_material",
]
