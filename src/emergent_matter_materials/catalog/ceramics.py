"""Ceramics: electrically insulating substrate and package materials.

Sintered polycrystalline ceramics for power-module substrates, LED
packages, and high-temperature insulation. Every value is the vendor's
published typical for the named grade; none of these materials has a
crystal_anisotropy group (polycrystalline, randomly oriented grains, no
engineering-scale single-crystal tensor).

Where a vendor publishes a bound rather than a value (volume resistivity
"> 10^14 ohm*cm", dielectric strength "> 15 kV/mm"), the bound is stored
and ``s_condition`` says so; a consumer must not read it as a typical.

Hardness: CoorsTek publishes Knoop hardness, which is a different indenter
from Vickers and is not converted. Maruwa publishes Vickers hardness in GPa,
which is the same measurement in different units (1 HV = 9.80665 MPa) and is
converted.
"""

from __future__ import annotations

from emergent_matter_materials.electromagnetic import Electromagnetic
from emergent_matter_materials.material import Material
from emergent_matter_materials.property_value import PropertyValue as _PV
from emergent_matter_materials.structural import Structural
from emergent_matter_materials.thermal import Thermal

_S_CATALOG_VERSION = "1.0.0"
_S_LAST_REVIEWED = "2026-09-17"

_COORSTEK_ADVANCED_ALUMINA = (
    "CoorsTek, 'Advanced Alumina: Materials & Manufacturing Processes' brochure "
    "((c) 2023 CoorsTek, document code 01023 L), properties table, AD-96 column "
    "(Nom. 96% Al2O3), retrieved 2026-09-17 from "
    "https://www.coorstek.com/media/4235/advanced-alumina.pdf"
)
_MARUWA_ALN_SUBSTRATES = (
    "MARUWA Co., Ltd., 'Aluminum Nitride (AlN) Substrates' product page, "
    "'Characteristic Values' table, AN-170 column (undated web page; retrieved "
    "2026-09-17 from https://www.maruwa-g.com/e/products/ceramic/000314.html)"
)


# ── CoorsTek AD-96 alumina ─────────────────────────────────────────────────

alumina_ad96 = Material(
    s_id="alumina_ad96",
    s_description="CoorsTek AD-96 alumina ceramic (nominal 96% Al2O3), power-substrate grade",
    s_category="ceramic",
    s_specification=(
        "CoorsTek AD-96, nominal 96% Al2O3 sintered alumina (white), per the CoorsTek "
        "Advanced Alumina properties table"
    ),
    s_catalog_version=_S_CATALOG_VERSION,
    s_last_reviewed=_S_LAST_REVIEWED,
    structural=Structural(
        youngs_modulus=_PV(
            d_value=303e9,
            s_units="Pa",
            s_source=_COORSTEK_ADVANCED_ALUMINA + " -- Elastic Modulus, 20 C = 303 GPa",
            s_condition="20 C",
            s_confidence="datasheet",
        ),
        poisson_ratio=_PV(
            d_value=0.21,
            s_units="",
            s_source=_COORSTEK_ADVANCED_ALUMINA + " -- Poisson's Ratio, 20 C = 0.21",
            s_condition="20 C",
            s_confidence="datasheet",
        ),
        flexural_strength=_PV(
            d_value=343e6,
            s_units="Pa",
            s_source=_COORSTEK_ADVANCED_ALUMINA
            + " -- 4-PT Flexural Strength (MOR), 20 C = 343 MPa",
            s_condition="20 C, 4-point bend (modulus of rupture)",
            s_confidence="datasheet",
            s_notes=(
                "Brittle ceramic: this is the fracture envelope in bending. No yield "
                "or tensile UTS is published, and none is physically meaningful; "
                "yield_stress and ultimate_tensile stay None."
            ),
        ),
        compressive_strength=_PV(
            d_value=2068e6,
            s_units="Pa",
            s_source=_COORSTEK_ADVANCED_ALUMINA + " -- Compressive Strength, 20 C = 2068 MPa",
            s_condition="20 C",
            s_confidence="datasheet",
            s_notes="About 6x the flexural strength, the usual ratio for dense alumina.",
        ),
        density=_PV(
            d_value=3720.0,
            s_units="kg/m^3",
            s_source=_COORSTEK_ADVANCED_ALUMINA + " -- Density = 3.72 g/cm3",
            s_condition="20 C, sintered",
            s_confidence="datasheet",
        ),
        # hardness_vickers stays None: the table publishes Knoop hardness
        # (11.5 GPa, 1000 g load), a different indenter that is not converted.
    ),
    electromagnetic=Electromagnetic(
        resistivity_at_20C=_PV(
            d_value=1e12,
            s_units="Ohm*m",
            s_source=_COORSTEK_ADVANCED_ALUMINA + " -- Volume Resistivity, 25 C = > 10^14 ohm-cm. "
            "Converted to Ohm*m by /100.",
            s_condition="25 C; LOWER BOUND (table publishes '> 10^14 ohm-cm', not a value)",
            s_confidence="datasheet",
            s_notes=(
                "Falls steeply with temperature on the same table: 4 x 10^9 ohm-cm at "
                "500 C, 1 x 10^6 ohm-cm at 1000 C."
            ),
        ),
        dielectric_strength=_PV(
            d_value=8.3e6,
            s_units="V/m",
            s_source=_COORSTEK_ADVANCED_ALUMINA + " -- Dielectric Strength, 6.35 mm thickness = "
            "8.3 ac-kV/mm",
            s_condition="AC, 6.35 mm thick specimen",
            s_confidence="datasheet",
            s_notes="Thickness-dependent; thin substrates withstand more per mm.",
        ),
        relative_permittivity=_PV(
            d_value=9.0,
            s_units="",
            s_source=_COORSTEK_ADVANCED_ALUMINA + " -- Dielectric Constant, 1 MHz, 25 C = 9.0",
            s_condition="1 MHz, 25 C",
            s_confidence="datasheet",
            s_notes="Dielectric loss tan delta = 0.0002 at 1 MHz on the same table.",
        ),
    ),
    thermal=Thermal(
        thermal_conductivity=_PV(
            d_value=24.7,
            s_units="W/(m*K)",
            s_source=_COORSTEK_ADVANCED_ALUMINA + " -- Thermal Conductivity, 20 C = 24.7 W/m K",
            s_condition="20 C",
            s_confidence="datasheet",
        ),
        specific_heat=_PV(
            d_value=880.0,
            s_units="J/(kg*K)",
            s_source=_COORSTEK_ADVANCED_ALUMINA + " -- Specific Heat, 100 C = 880 J/kg*K",
            s_condition="100 C",
            s_confidence="datasheet",
        ),
        thermal_expansion=_PV(
            d_value=8.2e-6,
            s_units="1/K",
            s_source=_COORSTEK_ADVANCED_ALUMINA + " -- Coefficient of Thermal Expansion, "
            "25-1000 C = 8.2 x 10^-6 /C",
            s_condition="25-1000 C mean",
            s_confidence="datasheet",
        ),
        # max_operating_temp stays None: the brochure publishes no maximum use
        # temperature for AD-96.
    ),
)


# ── MARUWA AN-170 aluminum nitride ─────────────────────────────────────────

aln_maruwa_an170 = Material(
    s_id="aln_maruwa_an170",
    s_description=(
        "MARUWA AN-170 aluminum nitride ceramic substrate (180 W/(m*K) grade), power-module "
        "and LED-package substrate"
    ),
    s_category="ceramic",
    s_specification=(
        "MARUWA AlN substrate grade AN-170 (gray), 0.25-1.5 mm thickness, per the MARUWA "
        "AlN substrates characteristic-values table"
    ),
    s_catalog_version=_S_CATALOG_VERSION,
    s_last_reviewed=_S_LAST_REVIEWED,
    structural=Structural(
        youngs_modulus=_PV(
            d_value=320e9,
            s_units="Pa",
            s_source=_MARUWA_ALN_SUBSTRATES + " -- Modulus of elasticity = 320 GPa (AN-170 only)",
            s_condition="room temperature",
            s_confidence="datasheet",
        ),
        flexural_strength=_PV(
            d_value=450e6,
            s_units="Pa",
            s_source=_MARUWA_ALN_SUBSTRATES + " -- Bending strength, 3-point method = 450 MPa",
            s_condition="room temperature, 3-point bend",
            s_confidence="datasheet",
            s_notes=(
                "Brittle ceramic: fracture envelope in bending; yield_stress and "
                "ultimate_tensile stay None. The higher-conductivity grades trade "
                "strength for conductivity (AN-200: 400 MPa, AN-230: 350 MPa)."
            ),
        ),
        density=_PV(
            d_value=3300.0,
            s_units="kg/m^3",
            s_source=_MARUWA_ALN_SUBSTRATES + " -- Bulk density = 3.30 g/cm3",
            s_condition="room temperature, sintered",
            s_confidence="datasheet",
        ),
        hardness_vickers=_PV(
            d_value=1121.7,
            s_units="HV",
            s_source=_MARUWA_ALN_SUBSTRATES + " -- Vickers hardness = 11 GPa. Converted to the "
            "Vickers hardness number: 11 GPa / 9.80665 MPa per HV = 1121.7 HV.",
            s_condition="room temperature; source publishes 2 significant figures (11 GPa)",
            s_confidence="datasheet",
            s_notes="Unit conversion only (same indenter, same measurement).",
        ),
    ),
    electromagnetic=Electromagnetic(
        resistivity_at_20C=_PV(
            d_value=1e12,
            s_units="Ohm*m",
            s_source=_MARUWA_ALN_SUBSTRATES + " -- Volume resistivity, 25 C = > 10^14 Ohm*cm. "
            "Converted to Ohm*m by /100.",
            s_condition="25 C; LOWER BOUND (table publishes '> 10^14', not a value)",
            s_confidence="datasheet",
        ),
        dielectric_strength=_PV(
            d_value=15e6,
            s_units="V/m",
            s_source=_MARUWA_ALN_SUBSTRATES + " -- Breakdown strength, DC = > 15 kV/mm",
            s_condition="DC; LOWER BOUND (table publishes '> 15', not a value)",
            s_confidence="datasheet",
        ),
        relative_permittivity=_PV(
            d_value=8.5,
            s_units="",
            s_source=_MARUWA_ALN_SUBSTRATES + " -- Dielectric constant, 1 MHz = 8.5",
            s_condition="1 MHz",
            s_confidence="datasheet",
            s_notes="Dielectric loss factor 0.3 x 10^-3 at 1 MHz on the same table.",
        ),
    ),
    thermal=Thermal(
        thermal_conductivity=_PV(
            d_value=180.0,
            s_units="W/(m*K)",
            s_source=_MARUWA_ALN_SUBSTRATES + " -- Thermal conductivity, 25 C = 180 W/(m*K) "
            "(AN-170 column)",
            s_condition="25 C",
            s_confidence="datasheet",
            s_notes=(
                "Falls to 120 W/(m*K) at 300 C. The grade name (170) is the "
                "nominal class; the table's typical is 180. Roughly 7x AD-96 alumina."
            ),
        ),
        specific_heat=_PV(
            d_value=720.0,
            s_units="J/(kg*K)",
            s_source=_MARUWA_ALN_SUBSTRATES + " -- Specific heat, 25 C = 720 J/(kg*K)",
            s_condition="25 C",
            s_confidence="datasheet",
        ),
        thermal_expansion=_PV(
            d_value=4.6e-6,
            s_units="1/K",
            s_source=_MARUWA_ALN_SUBSTRATES + " -- Coefficient of thermal expansion, 40-400 C = "
            "4.6 x 10^-6 /K",
            s_condition="40-400 C mean",
            s_confidence="datasheet",
            s_notes="5.2 x 10^-6 /K over 40-800 C on the same table; close to silicon's CTE.",
        ),
    ),
)


CATALOG: dict[str, Material] = {
    alumina_ad96.s_id: alumina_ad96,
    aln_maruwa_an170.s_id: aln_maruwa_an170,
}


__all__ = [
    "CATALOG",
    "aln_maruwa_an170",
    "alumina_ad96",
]
