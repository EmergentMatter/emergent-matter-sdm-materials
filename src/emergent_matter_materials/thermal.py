"""Thermal property group.

Three required fields (``thermal_conductivity``, ``specific_heat``,
``max_operating_temp``): present on essentially every engineering
material, plus five optional fields populated where the data exists:
``thermal_expansion`` (CTE), ``glass_transition`` (polymers only),
``curie_temp`` (ferromagnetics: full demag above this point),
``melting_temp``, ``emissivity``.

The three required fields are what a winding thermal model needs at
minimum: conduction to dissipate winding I²R, heat capacity for
transient temp rise, and a temperature ceiling.
"""

from __future__ import annotations

from dataclasses import dataclass

from emergent_matter_materials.property_value import PropertyValue
from emergent_matter_materials.validation import _validate_group_units


@dataclass(frozen=True)
class Thermal:
    """Thermal properties: all fields optional (Tier-1-only policy).

    Under v0.2.0 "Tier 1 only" policy, only fields with verified
    primary-source data populate. A material may have only a subset
    (e.g. just max_operating_temp from a vendor TDS, with
    thermal_conductivity and specific_heat unverified). At least one
    field should be populated, if a material has nothing thermal,
    leave the entire ``thermal`` slot on Material as ``None`` rather
    than constructing an empty Thermal.
    """

    thermal_conductivity: PropertyValue | None = None  # W/(m·K)
    specific_heat: PropertyValue | None = None  # J/(kg·K)
    max_operating_temp: PropertyValue | None = None  # °C
    thermal_expansion: PropertyValue | None = None  # 1/K (CTE)
    # 1/K, CTE perpendicular to the easy/c axis for anisotropic sintered
    # magnets; thermal_expansion holds the parallel value by convention.
    # May be negative (sintered NdFeB contracts on heating across the c axis).
    thermal_expansion_perpendicular: PropertyValue | None = None
    glass_transition: PropertyValue | None = None  # °C (polymers)
    curie_temp: PropertyValue | None = None  # °C (ferromagnetics)
    melting_temp: PropertyValue | None = None  # °C
    emissivity: PropertyValue | None = None  # dimensionless

    def __post_init__(self) -> None:
        _validate_group_units(
            self,
            group_fields={
                "thermal_conductivity",
                "specific_heat",
                "max_operating_temp",
                "thermal_expansion",
                "thermal_expansion_perpendicular",
                "glass_transition",
                "curie_temp",
                "melting_temp",
                "emissivity",
            },
            b_optional=True,
        )

        # Positivity / range invariants, only on present fields
        if self.thermal_conductivity is not None and self.thermal_conductivity.d_value <= 0.0:
            raise ValueError(
                f"thermal_conductivity must be positive, got {self.thermal_conductivity.d_value}"
            )
        if self.specific_heat is not None and self.specific_heat.d_value <= 0.0:
            raise ValueError(f"specific_heat must be positive, got {self.specific_heat.d_value}")
        if self.max_operating_temp is not None and self.max_operating_temp.d_value < -273.15:
            raise ValueError(
                f"max_operating_temp = {self.max_operating_temp.d_value} C "
                f"is below absolute zero; check the source citation."
            )
        if self.emissivity is not None and not (0.0 <= self.emissivity.d_value <= 1.0):
            raise ValueError(f"emissivity must be in [0, 1], got {self.emissivity.d_value}")

    # ── Hot-path accessors (raise on missing)

    def _req(self, s_field_name: str) -> PropertyValue:
        pv = getattr(self, s_field_name)
        if pv is None:
            raise ValueError(
                f"Thermal.{s_field_name} not defined for this material "
                f"(field is None: Tier 1 source not yet available)"
            )
        return pv

    @property
    def d_thermal_conductivity_W_mK(self) -> float:
        return self._req("thermal_conductivity").d_value

    @property
    def d_specific_heat_J_kgK(self) -> float:
        return self._req("specific_heat").d_value

    @property
    def d_max_operating_temp_C(self) -> float:
        return self._req("max_operating_temp").d_value

    @property
    def d_thermal_expansion_per_K(self) -> float:
        return self._req("thermal_expansion").d_value

    @property
    def d_thermal_expansion_perpendicular_per_K(self) -> float:
        return self._req("thermal_expansion_perpendicular").d_value

    @property
    def d_glass_transition_C(self) -> float:
        return self._req("glass_transition").d_value

    @property
    def d_curie_temp_C(self) -> float:
        return self._req("curie_temp").d_value

    @property
    def d_melting_temp_C(self) -> float:
        return self._req("melting_temp").d_value

    @property
    def d_emissivity(self) -> float:
        return self._req("emissivity").d_value


__all__ = ["Thermal"]
