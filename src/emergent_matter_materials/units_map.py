"""Single source of truth for canonical SI units per material property.

Each ``PropertyValue.s_units`` MUST match the entry in
:data:`_PROPERTY_EXPECTED_UNITS` for the property slot it occupies. The
group dataclasses (``Structural``, ``Electromagnetic``, ``Thermal``,
``Manufacturing``) enforce this in ``__post_init__``: a wrong units
string is a construction-time ``ValueError``.

**Why this exists.**
Without enforcement, ``s_units`` becomes a decorative comment and drifts:
someone ports MPa values into Pa-typed slots, no one notices, the catalog
silently corrupts. The fix is the same shape as enforcing a dataclass
field's type: declare the contract once, check on construction.

**Conventions:**

- **Stress / pressure / modulus**: ``"Pa"`` (not MPa). Internal SI.
- **Density**: ``"kg/m^3"`` (not g/cc).
- **Temperatures**: ``"C"`` (degrees Celsius). Hot-path accessors named
  with ``_C`` suffix. Note: this is *the* exception to "everything SI";
  Celsius is what every datasheet uses and converting would just add
  friction to entry creation + reading. Temperature *differences* still
  use Kelvin (``"1/K"`` for CTE and temp coefficients).
- **Dimensionless**: empty string ``""`` (not ``"unitless"`` or ``"1"``).
  Used for Poisson ratio, relative permeability, relative permittivity,
  shrinkage fraction, anisotropy factor, emissivity.
- **Operators in unit strings**: ``"*"`` for multiplication, ``"/"`` for
  division, parentheses for grouping. ``"W/(m*K)"``, ``"J/(kg*K)"``,
  ``"kg/m^3"``. ASCII only (no Greek letters or Unicode) so unit strings
  round-trip cleanly through JSON/YAML.
"""

from __future__ import annotations

#: Canonical SI units string per property slot. Every PropertyValue's
#: ``s_units`` must match the value in this table for the dataclass field
#: it occupies.
# fmt: off
# Hand-aligned so a scan down the value column catches a wrong unit at a
# glance; ruff format would collapse the alignment without changing meaning.
_PROPERTY_EXPECTED_UNITS: dict[str, str] = {
    # ── Structural ────────────────────────────────────────────────────
    "youngs_modulus":            "Pa",
    "poisson_ratio":             "",            # dimensionless
    "yield_stress":              "Pa",
    "fatigue_endurance":         "Pa",
    "ultimate_tensile":          "Pa",
    "flexural_strength":         "Pa",          # brittle-fracture peak-stress scalar (ASTM C1161-class 3-pt bend)  # noqa: E501
    "density":                   "kg/m^3",
    "hardness_vickers":          "HV",          # Vickers hardness number (kgf/mm^2), reported unitless by convention  # noqa: E501
    "compressive_strength":      "Pa",          # compressive envelope (brittle sintered magnets)
    # ── Electromagnetic ───────────────────────────────────────────────
    "resistivity_at_20C":        "Ohm*m",
    "temp_coeff_resistivity":    "1/K",
    "relative_permeability":     "",            # dimensionless
    "saturation_flux":           "T",
    "coercivity":                "A/m",
    "remanence":                 "T",
    "temp_coeff_remanence":      "1/K",
    "temp_coeff_coercivity":     "1/K",         # α(HcJ), fractional ΔHcJ per K
    "recoil_permeability":       "",            # dimensionless, μ_rec ≈ 1.02-1.10 sintered RE PMs
    "energy_product_max":        "J/m^3",       # (BH)max nominal; 1 MGOe = 7957.7 J/m^3
    "core_loss":                 "W/kg",        # at s_condition's (B_ref, f_ref)
    "dielectric_strength":       "V/m",
    "relative_permittivity":     "",            # dimensionless
    # ── Thermal ───────────────────────────────────────────────────────
    "thermal_conductivity":      "W/(m*K)",
    "specific_heat":             "J/(kg*K)",
    "max_operating_temp":        "C",
    "thermal_expansion":         "1/K",
    "thermal_expansion_perpendicular": "1/K",   # CTE perpendicular to the easy axis (anisotropic magnets)  # noqa: E501
    "glass_transition":          "C",
    "curie_temp":                "C",
    "melting_temp":              "C",
    "emissivity":                "",            # dimensionless
    # ── Manufacturing (per-ProcessFit) ────────────────────────────────
    "shrinkage_linear":          "",            # dimensionless fraction
    "min_wall_thickness":        "m",
    "min_feature_size":          "m",
    "anisotropy_factor_z_vs_xy": "",
    "max_unsupported_overhang":  "deg",
    "typical_layer_height":      "m",
    # ── Crystal anisotropy (v0.4.0) ───────────────────────────────────
    # Single-crystal elastic stiffness tensor (Voigt notation) + crystallographic
    # constants for crystal-plasticity FEM, dislocation-density hardening, and
    # texture-aware structural simulation.
    "c11":                       "Pa",
    "c12":                       "Pa",
    "c13":                       "Pa",
    "c33":                       "Pa",
    "c44":                       "Pa",
    "c66":                       "Pa",
    "burgers_vector":            "m",
    "stacking_fault_energy":     "J/m^2",
    "crss_initial":              "Pa",
}
# fmt: on


def expected_units_for(s_field_name: str) -> str:
    """Look up the canonical units string for a property slot.

    Raises ``KeyError`` if the field isn't a known property. Group
    dataclasses use this in ``__post_init__`` to validate every
    PropertyValue they hold.
    """
    if s_field_name not in _PROPERTY_EXPECTED_UNITS:
        raise KeyError(
            f"No expected-units entry for {s_field_name!r}. "
            f"Known properties: {sorted(_PROPERTY_EXPECTED_UNITS)}"
        )
    return _PROPERTY_EXPECTED_UNITS[s_field_name]


__all__ = [
    "_PROPERTY_EXPECTED_UNITS",
    "expected_units_for",
]
