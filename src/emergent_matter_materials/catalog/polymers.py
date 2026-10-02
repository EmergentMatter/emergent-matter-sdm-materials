"""Polymers: engineering plastics (Tier-1-only catalog).

Under the v0.2.0 "Tier 1 only" policy, this file contains only
PropertyValues with confidence in {measured, datasheet, standard}.

As of v0.7.1 the catalog holds seven polymer materials, with every
already-cited primary source swept for published-but-not-stored
fields and N/A-by-physics gaps explained in s_notes:

| Material            | Tier 1 fields | Primary source(s)                  |
|---------------------|---------------|------------------------------------|
| peek_unfilled       | 12            | Victrex 450G TDS (March 2026)      |
| pei_ultem_1010      | 11            | SABIC Ultem 1010 Americas TDS 2017 |
| nylon12_sls         | 7             | EOS PA 2200 (Jul 2022)             |
| pla_3dprint         | 8             | Prusament PLA TDS v1.1 (Feb 2022)  |
| nomex_410           | 6             | DuPont K-20612-2 (04/16)           |
| mw_pai_class_200    | 13            | Solvay Torlon 4203L (Oct 2014)     |
| mw_pur_class_130    | 1             | NEMA MW 1000 / IEC 60317-1         |

Deleted in v0.2.0, and still awaiting a Tier-1 source:
- tpu_95a: all values were MatWeb-aggregated
- petg_fdm: aggregator + Tier-2 paper

Restored as Tier-1 in v0.5.0:
- pla_3dprint: Prusament PLA (Prusa Polymers a.s.) TDS, Feb 2022

v0.6.0 sweep (this revision): Tier-1 fields restored from
already-cited primary sources:
- pei_ultem_1010   density (1.27 g/cm^3), flexural strength,
                   thermal conductivity, CTE: all from SABIC TDS
- mw_pai_class_200 Young's modulus, ultimate tensile, Poisson ratio,
                   flexural strength, CTE: all from Solvay Torlon
                   4203L TDS (with same bulk-PAI-resin caveat as the
                   already-cited density)
- peek_unfilled    flexural strength: from Victrex 450G TDS
- pla_3dprint      flexural strength: from Prusament PLA TDS
- nylon12_sls      melting_temp midpoint: from EOS PA 2200 TDS
- nomex_410        relative permittivity: from DuPont TDS Table I
- nomex_410 + mw_pur_class_130: material-level s_notes explaining
                   physics-meaningful N/A fields (Nomex E/nu because
                   it is calendered aramid PAPER, MW PUR because no
                   Tier-1 bulk-resin TDS has surfaced)

v0.7.0 sweep (this revision): thermal + structural gap fills
from already-cited primary sources:
- peek_unfilled    specific_heat = 2160 J/(kg*K) at 25 C (Victrex
                   450G TDS, ISO 22007-4)
- pei_ultem_1010   poisson_ratio = 0.36 (SABIC Ultem 1010 typical
                   amorphous PEI scalar) + specific_heat = 2000
                   J/(kg*K) at 25 C (SABIC Ultem 1010 TDS)
- nomex_410        volume resistivity_at_20C = 1e16 Ohm*m at
                   20 C dry (DuPont K-20612-2; humidity-sensitive,
                   see s_notes)

v0.7.1 sweep (this revision): third-pass exhaustive sweep.
Single category of gap surfaced across three materials: VOLUME
RESISTIVITY at room temperature, plainly published in the bulk-
polymer TDS Electrical sections but not previously stored:
- peek_unfilled    resistivity_at_20C = 1.0e14 Ohm*m at 23 C
                   (Victrex 450G TDS, IEC 60093; the TDS also
                   publishes T-series 1e15 at 125 C / 1e9 at 275 C)
- pei_ultem_1010   resistivity_at_20C = 1.0e15 Ohm*m
                   (SABIC Ultem 1010 TDS, ASTM D257)
- mw_pai_class_200 resistivity_at_20C = 2.0e15 Ohm*m
                   (Solvay Torlon 4203L TDS, ASTM D257; same bulk-
                   PAI-resin caveat as other Solvay-sourced values
                   on this material)

What the v0.7.1 sweep CONFIRMED REMAIN GENUINE GAPS (verified
against the actual cited PDFs, not third-party hints):
- EOS PA 2200 TDS (Jul 2022) does NOT publish thermal_conductivity,
  specific_heat, CTE, or glass_transition. Earlier v0.1.x values
  for these came from MatWeb (Tier 3) and are correctly removed.
  The current TDS DOES publish Z-direction tensile data (Modulus
  1650 MPa, Strength 42 MPa, strain at break 4%): schema is
  isotropic-scalar so this anisotropy detail has no slot.
- Prusament PLA TDS v1.1 (Feb 2022) does NOT publish thermal_
  conductivity, specific_heat, CTE, or fatigue. It publishes Heat
  Deflection Temperature 55 C at both 0.45 MPa and 1.80 MPa
  (ISO 75): no HDT slot exists in the schema.
- Solvay Torlon 4203L TDS does NOT publish specific_heat or
  fatigue endurance (only a qualitative 'fatigue resistant'
  feature bullet: the Solvay PAI Design Guide carries S-N curves
  but is a different publication, not the cited TDS).
- Victrex 450G TDS does NOT publish a scalar UTS, fatigue
  endurance limit, emissivity, or temp_coeff_resistivity (these
  remain confirmed gaps from v0.2.4: verified again).
- SABIC Ultem 1010 TDS does NOT publish cross-flow CTE, fatigue,
  emissivity, or temp_coeff_resistivity (verified gaps from
  v0.6.0). It DOES publish HDT 207 C / 198 C at 0.45 / 1.82 MPa
  and Vicat B/50 = 218 C: no HDT or Vicat slots in schema.
- DuPont Nomex 410 TDS does NOT publish specific_heat, CTE,
  emissivity, or a scalar temp_coeff_resistivity. The TDS shows
  qualitative T-dependence of resistivity in Figure 3 but no
  scalar TCR; humidity dominates over temperature anyway. The
  existing 1e16 Ohm*m value carries soft-bounded order-of-
  magnitude s_notes consistent with the TDS Table II (oven-dry
  6e16 Ohm*cm at 0.25 mm = 6e14 Ohm*m at the standard reference
  thickness; the catalog's 1e16 Ohm*m matches the upper end of
  the published range; see s_notes on that field for the design
  recommendation).
- MW PUR Class 130: confirmed Tier-1 bulk-PUR-resin TDS sourcing
  gap unchanged from v0.6.0. No PUR-enamel-resin primary
  publication has been found; only the grade-defining 130 C
  remains the single PropertyValue.

N/A-by-physics notes (apply to EVERY polymer in this file unless
explicitly overridden: these are NOT sourcing gaps but physics-
meaningful absences):

- ``curie_temp``, only applies to ferromagnetic materials (above the
  Curie point, spontaneous magnetization vanishes). Polymers are
  not ferromagnetic; correctly ``None`` on every polymer here.

- ``saturation_flux`` / ``coercivity`` / ``remanence``: same
  reasoning. These are hard- and soft-magnetic-only properties.
  Polymers do not carry magnetic domains, so the field-versus-flux
  loop these scalars summarize does not exist.

- ``relative_permeability`` ≈ 1.0 for all polymers (within a part-
  per-million of vacuum because organic backbones carry no
  unpaired d-electrons). Left ``None`` rather than restating the
  bulk-vacuum value 25 times across the catalog. Consumers needing
  μ_r for a polymer should assume 1.0.

- ``crystal_anisotropy`` (the C_ij Voigt stiffness tensor +
  single-crystal slip data in the CrystalAnisotropy group): polymers
  are amorphous (Ultem 1010, PAI, Nomex paper, PUR enamel) or
  semi-crystalline (PEEK 450G, PLA, PA12) blends of chain
  conformations. Even for semi-crystalline grades the spherulite-
  scale crystallinity is randomly oriented at the bulk-engineering
  length scale, so the single-crystal anisotropic tensor does NOT
  apply at the bulk-property level for engineering use. The
  isotropic Young's modulus + Poisson ratio scalars in
  ``structural`` already capture the engineering-relevant
  stiffness.
"""

from __future__ import annotations

from emergent_matter_materials.electromagnetic import Electromagnetic
from emergent_matter_materials.material import Material
from emergent_matter_materials.property_value import PropertyValue as _PV
from emergent_matter_materials.structural import Structural
from emergent_matter_materials.thermal import Thermal

_S_CATALOG_VERSION = "1.0.0"
_S_LAST_REVIEWED = "2026-05-24"

_VICTREX_PEEK_450G_SHEET = (
    "Victrex Manufacturing Limited, 'VICTREX PEEK POLYMER 450G: General "
    "Information' technical datasheet, Revision Date March 2026, "
    "retrieved 2026-05-24 from "
    "https://www.victrex.com/-/media/downloads/datasheets/victrex_tds_450g.pdf"
)
_VICTREX_FLUID_MGMT_FLYER = (
    "Victrex plc, 'VICTREX PEEK in Hydraulic Applications: Fluid Management "
    "with Confidence' product flyer (2020-07), p.3 PEEK Product Range comparison "
    "table: PEEK 450G Compressive Strength 125 MPa (ISO 604, break, 23 C), "
    "Tensile Modulus 4,000 MPa (ISO 527, 23 C), POISSON RATIO 0.38. Retrieved "
    "2026-05-24 from "
    "https://www.victrex.com/-/media/downloads/literature/en/"
    "2020-07_fluidmanagementflyer_web.pdf"
)
_SABIC_ULTEM_1010_SHEET = (
    "SABIC, 'ULTEM Resin 1010: Region Americas Technical Data Sheet', "
    "Revision 20170706, retrieved 2026-05-24 from "
    "https://pc-api-public.sabic.com/uploads/9d4c50ad/5562/e711/80fb/"
    "005056857ef3/ULTEM%E2%84%A2%20%20Resin_1010_Americas_Technical_Data_Sheet.pdf"
)
_EOS_PA2200_SHEET = (
    "EOS GmbH, 'PA 2200 Material Data Sheet' (current MDS page), "
    "specifically grade 'PA 2200 Balance' (the standard 120 µm layer "
    "thickness variant: EOS also publishes a 'PA 2200 CarbonReduced' "
    "variant with reduced CO2e footprint, NOT used here). Values are "
    "XY-direction SLS-printed specimens. Catalog values verified via "
    "v0.7.3 manual fetch from https://www.eos.info/polymer-solutions/"
    "polymer-materials/data-sheets/mds-pa-2200 (Tensile Modulus 1650 "
    "MPa, Tensile Strength 48 MPa X/Y / 42 MPa Z, Density 0.93 g/cm^3, "
    "Melting Temp 176 °C, Vicat Softening 176 °C, HDT @ 1.80 MPa 64 X "
    "/ 57 Z, HDT @ 0.45 MPa 157 X / 145 Z). The EOS MDS does NOT "
    "publish thermal conductivity, specific heat, CTE, glass "
    "transition, fatigue endurance, or a continuous-use temperature "
    "scalar: those slots are correctly None on this material."
)
_FORMLABS_NYLON12_POWDER = (
    "Formlabs, Inc., 'Nylon 12 Powder' SLS technical data sheet (SLS Powders "
    "product line), Rev. 01 (prepared 2020-08-19), document FLP12G01, "
    "retrieved 2026-06-22 "
    "from https://formlabs-media.formlabs.com/datasheets/2001447-TDS-ENUS-0.pdf "
    "(read directly). This is the powder Formlabs developed "
    "specifically for the Fuse Series SLS printers. Mechanical-properties "
    "block: Ultimate Tensile Strength 50 MPa, "
    "Tensile Modulus 1850 MPa, Elongation at Break X/Y 11% / Z 6%, all "
    "ASTM D638 Type 1; Flexural Strength 66 MPa (ASTM D790-15). Specimens "
    "printed on Fuse 1, conditioned 50% RH / 23 °C for 7 days before testing. "
    "The TDS publishes a single tensile-strength scalar (UTS) and does NOT "
    "publish a distinct yield strength."
)
_DUPONT_NOMEX_410 = (
    "DuPont, 'Technical Data Sheet DuPont(TM) Nomex(R) 410', document K-20612-2 "
    "(04/16), Copyright 2016. Retrieved 2026-05-24 from "
    "https://www.dupont.com/content/dam/aramids/amer/us/en/safety/public/"
    "documents/en/DPT16_21668_Nomex_410_Tech_Data_Sheet_me03_REFERENCE.pdf"
)
_SOLVAY_TORLON_4203L = (
    "Solvay Specialty Polymers, 'Torlon 4203L Polyamide-imide (PAI)' technical "
    "data sheet, Revision 2014-10-22. PAI resin underlying NEMA Class 200 "
    "magnet wire enamels (the wire itself is graded by NEMA MW 35-C; this "
    "resin sheet gives the bulk polymer properties). Retrieved 2026-05-24 from "
    "https://cn.drakeplastics.com/wp-content/uploads/2020/01/Torlon-4203L.pdf"
)
_PRUSAMENT_PLA_TDS = (
    "Prusa Polymers a.s., 'Prusament PLA: Technical datasheet,' Version "
    "1.1 (last update 2022-07-27). Single canonical TDS for the Prusament "
    "PLA filament line (color-to-color variation < 5% per Prusa). FDM-"
    "printed test specimens per ISO 527-1 (tensile, both modulus + yield) "
    "and ISO 178 (flexural), printed on Original Prusa i3 MK3 with 0.20 mm "
    "FAST layers, 100% rectilinear infill, 215 °C nozzle, 60 °C bed (per "
    "TDS p.3 method footnote (3)). Filament-level density and HDT values "
    "are on TDS p.2 'Typical material properties' table; 3D-printed-"
    "specimen mechanical values are on TDS p.2 'Mechanical properties of "
    "3D printed testing specimens' table. Retrieved 2026-05-24 from "
    "https://prusament.com/pla/ (the 'Download tech sheet' link returns a "
    "ZIP containing per-locale PDFs including 1_PLA_Prusament_TDS_2022_EN."
    "pdf). v0.7.3 manual verification: directly read this TDS PDF (3 "
    "pages, 1.5 MB) and confirmed every catalog PV against the published "
    "row. Earlier catalog citations of 'ISO 527-2' corrected to ISO 527-1 "
    "per the TDS specimens table."
)
_PRUSAMENT_PETG_TDS = (
    "Prusa Polymers a.s., 'Prusament PETG: Technical datasheet,' Version 1.1 "
    "(last update 2022-02-16), retrieved 2026-09-17 from "
    "https://storage.googleapis.com/prusa3d-content-prod-14e8-wordpress-prusament-prod/"
    "2023/10/9f8d2165-tds_prusament-petg_n_en.pdf (linked from "
    "https://prusament.com/materials/prusament-petg/). p.2 'Typical material "
    "properties' table (filament level: density ISO 1183, HDT ISO 75) and p.2 "
    "'Mechanical properties of 3D printed testing specimens' table (ISO 527-1 "
    "tensile, ISO 178 flexural; horizontal and vertical x-z print directions); "
    "specimens printed on an Original Prusa i3 MK3, 0.20 mm FAST layers, 100% "
    "rectilinear infill, 250 C nozzle, 80 C bed, per p.3 footnote (2)"
)
_DUPONT_KAPTON_HN = (
    "DuPont 'Kapton HN Polyimide Film' technical data sheet, document QE-10206 "
    "(03/26), published by Qnity Electronics (the DuPont electronics business); "
    "product specification H-38479 (6/18); retrieved 2026-09-17 from "
    "https://www.qnityelectronics.com/content/dam/electronics/amer/us/en/"
    "electronics/public/documents/en/QE-10206-Kapton-HN-Data-Sheet.pdf. "
    "Table 1 'Physical Properties of Kapton HN at 23 C' (per-gauge columns; the "
    "25 um / 1 mil column is used here), Table 2 'Thermal Properties of Kapton HN "
    "Film', Table 3 'Typical Electrical Properties of Kapton HN Film at 23 C, "
    "50% RH'"
)
_HENKEL_STYCAST_2850FT_CAT9 = (
    "Henkel, 'LOCTITE STYCAST 2850FT CAT 9' Technical Data Sheet (October 2024), "
    "retrieved 2026-09-17 from "
    "https://datasheets.tdx.henkel.com/LOCTITE-STYCAST-2850FT-CAT-9-en_GL.pdf. "
    "'Typical Properties of Cured Material' and 'Typical Cured Performance as "
    "Mixed' tables for STYCAST 2850FT cured with CAT 9 (100:3.5 by weight, room "
    "temperature cure), and 'Typical Uncured Properties as Mixed'"
)
_BASF_ELASTOLLAN_RANGE = (
    "BASF Polyurethanes GmbH, 'Thermoplastic Polyurethane Elastomers (TPU) "
    "Elastollan - Product Range' brochure (September 2016), 'Elastollan 11 Series' "
    "table, column '1195 A 10', retrieved 2026-09-17 from "
    "https://www.basf.com/dam/jcr:f7c775d7-afe0-3dca-a44c-856e0853a81d/basf/www/kr/"
    "documents/ko/product/Thermoplastic%20Polyurethane_Elastollan_Product%20Range.pdf "
    "(typical values on injection-moulded specimens; DIN test procedures per row)"
)
_NEMA_MW_35C = (
    "NEMA MW 35-C 'Magnet Wire, Insulated, Polyamide-Imide Film, 200 degC' "
    "wire grade standard (defines minimum dielectric breakdown + insulation "
    "build dimensions per AWG; via CnC Tech transcription Rev. 2016-11-18). "
    "Retrieved 2026-05-24 from "
    "https://media.digikey.com/pdf/Data%20Sheets/CNC%20Tech%20PDFs/MW35C_Spec.pdf"
)
_NEMA_MW_1000_PUR_130 = (
    "ANSI/NEMA MW 1000 'Magnet Wire' standard, grade MW 130 ('Polyurethane "
    "Bondable - 130') and MW 135 ('Polyurethane Nylon Bondable - 130'), "
    "thermal class 130 degC; corroborated by IEC 60317-1 ('Solderable "
    "polyurethane enamelled round copper wire, class 130': general "
    "requirements) and IEC 60317-2 / 60317-4 (sole-coating and bonding-layer "
    "variants, both titled 'class 130'). The Class 130 designation IS the "
    "130 degC continuous-service operating-temperature spec: that is what "
    "the standard defines (UL 1446 / IEC 60172 temperature-index method "
    "underpins the thermal-class number). Cross-referenced via MWS Wire "
    "Industries 'Magnet Wire Insulation Guide' (Print Revision April 2014), "
    "the published NEMA-vs-IEC-vs-Federal-Spec cross-reference table for "
    "magnet-wire insulations, retrieved 2026-05-24 from "
    "https://mwswire.com/wp-content/uploads/2024/01/MWS-techbook.pdf "
    "(p.2 'Magnet Wire Insulation Guide' table, Class 130 C row: PB130 / "
    "MW 130 / IEC 60317-2 and PNB130 / MW 135). For dielectric constant of "
    "the same MWS publication see p.11 'Multifilar Magnet Wire: General "
    "Product Information' table (Polyurethane 155 / MW 79-C / dielectric "
    "constant 3.70). For the IEC standards portal listings of "
    "IEC 60317-1/-2/-4 (titles include the phrase 'class 130'), see "
    "https://www.sis.se/en/produkter/electrical-engineering/electrical-"
    "wires-and-cables/wires/iec6031742015/ and "
    "https://standards.globalspec.com/std/13407163/IEC%2060317-2."
)


# ── PEEK 450G (Victrex unfilled) ───────────────────────────────────────────

peek_unfilled = Material(
    s_id="peek_unfilled",
    s_description="PEEK (Polyether Ether Ketone), unfilled: Victrex 450G",
    s_category="polymer",
    s_specification="Victrex PEEK 450G (unfilled, semi-crystalline, standard flow)",
    s_catalog_version=_S_CATALOG_VERSION,
    s_last_reviewed=_S_LAST_REVIEWED,
    structural=Structural(
        youngs_modulus=_PV(
            d_value=4.0e9,
            s_units="Pa",
            s_source=_VICTREX_PEEK_450G_SHEET + " -- Tensile Modulus (23 C) = 4000 MPa (ISO 527-1)",
            s_condition="23 C, ISO 527-1",
            s_confidence="datasheet",
        ),
        poisson_ratio=_PV(
            d_value=0.38,
            s_units="",
            s_source=_VICTREX_FLUID_MGMT_FLYER,
            s_condition="23 C, unfilled PEEK 450G",
            s_confidence="datasheet",
            s_notes=(
                "v0.2.4 (2026-05-24) restored from gap. The Victrex 450G "
                "General Information TDS does NOT publish a Poisson ratio "
                "scalar; this 0.38 value comes from a different Victrex "
                "publication, the 'PEEK in Hydraulic Applications' product "
                "flyer (2020-07), which has a dedicated comparison table on "
                "p.3 explicitly listing PEEK 450G Poisson ratio = 0.38 "
                "(vs steel 0.30; same 0.38 for the filled grades 450CA30, "
                "90HMF20, and ABV300). Both are Tier 1 vendor publications "
                "from Victrex plc, so the citation is Tier 1 datasheet. "
                "Round 3 independent cross-check (2026-05-24) did NOT "
                "replicate this find: it checked only the 450G General "
                "Information TDS + Materials Properties Guide and reported "
                "'no Victrex primary scalar.' The hydraulic-applications "
                "flyer is a less-discovered but legitimate Victrex Tier 1 "
                "publication; URL preserved in s_source for replication."
            ),
        ),
        yield_stress=_PV(
            d_value=98e6,
            s_units="Pa",
            s_source=_VICTREX_PEEK_450G_SHEET
            + " -- Tensile Stress at Yield (23 C) = 98.0 MPa (ISO 527-2)",
            s_condition="23 C yield, ISO 527-2",
            s_confidence="datasheet",
        ),
        density=_PV(
            d_value=1300.0,
            s_units="kg/m^3",
            s_source=_VICTREX_PEEK_450G_SHEET
            + " -- Density (Crystalline) = 1.30 g/cm^3 (ISO 1183)",
            s_condition="crystalline, 23 C",
            s_confidence="datasheet",
        ),
        flexural_strength=_PV(
            d_value=165e6,
            s_units="Pa",
            s_source=_VICTREX_PEEK_450G_SHEET
            + " -- Flexural Stress (yield, 23 C) = 165 MPa (ISO 178)",
            s_condition="23 C, ISO 178 yield, 2 mm specimen",
            s_confidence="datasheet",
            s_notes=(
                "v0.6.0 sweep added: the Victrex 450G TDS Flexural Stress "
                "table lists 165 MPa at yield (23 C) plus 125 MPa at 3.5% "
                "strain (23 C) and a temperature series 85/19/12.5 MPa at "
                "125/175/275 C. PEEK is a ductile semi-crystalline polymer, "
                "not a brittle ceramic, so the flexural-strength slot here "
                "captures the published 3-pt-bend peak stress without the "
                "brittle-flex caveats that apply to sintered NdFeB / SmCo / "
                "ceramics. Yield in pure tension (98 MPa) remains the "
                "primary ductile-design metric; flex is supplied for bending-"
                "dominated bearing-housing / spline-fit stress states."
            ),
        ),
    ),
    electromagnetic=Electromagnetic(
        resistivity_at_20C=_PV(
            d_value=1.0e14,
            s_units="Ohm*m",
            s_source=_VICTREX_PEEK_450G_SHEET + " -- Volume Resistivity at 23 C = 1.0E+16 ohms*cm "
            "(IEC 60093). Converted to Ohm*m by /100.",
            s_condition="23 C, IEC 60093",
            s_confidence="datasheet",
            s_notes=(
                "v0.7.1 sweep added. The Victrex 450G TDS Electrical "
                "table publishes Volume Resistivity per IEC 60093 as a "
                "temperature series: 1.0E+16 Ohm*cm at 23 C (stored "
                "here), 1.0E+15 at 125 C, and 1.0E+9 at 275 C. The "
                "five-orders-of-magnitude drop from 23 C to 275 C is "
                "typical for an amorphous-glassy-state polymer crossing "
                "Tg (143 C) into rubbery state: IONIC mobility rises "
                "sharply once chain segmental motion unlocks. For most "
                "motor/bearing-housing designs at <=125 C, the stored "
                "23 C scalar is the appropriate insulation-resistance "
                "anchor; above Tg, designers should consult the full "
                "T-dependent curve in the Victrex TDS."
            ),
        ),
        dielectric_strength=_PV(
            d_value=23e6,
            s_units="V/m",
            s_source=_VICTREX_PEEK_450G_SHEET + " -- Dielectric Strength at 2.00 mm = 23.0 kV/mm "
            "(IEC 60243-1)",
            s_condition="2.00 mm thickness, IEC 60243-1",
            s_confidence="datasheet",
        ),
        relative_permittivity=_PV(
            d_value=3.10,
            s_units="",
            s_source=_VICTREX_PEEK_450G_SHEET + " -- Dielectric Constant at 23 C, 1 kHz = 3.10",
            s_condition="23 C, 1 kHz, IEC 60250",
            s_confidence="datasheet",
        ),
    ),
    thermal=Thermal(
        thermal_conductivity=_PV(
            d_value=0.29,
            s_units="W/(m*K)",
            s_source=_VICTREX_PEEK_450G_SHEET
            + " -- Thermal Conductivity at 23 C (average, ISO 22007-4)",
            s_condition="23 C, ISO 22007-4 average direction",
            s_confidence="datasheet",
        ),
        max_operating_temp=_PV(
            d_value=260.0,
            s_units="C",
            s_source=_VICTREX_PEEK_450G_SHEET + " -- RTI Electrical (UL 746B) = 260 C",
            s_condition="continuous service, UL 746B RTI Electrical",
            s_confidence="datasheet",
        ),
        glass_transition=_PV(
            d_value=143.0,
            s_units="C",
            s_source=_VICTREX_PEEK_450G_SHEET + " -- Glass Transition (onset, ISO 11357-2) = 143 C",
            s_condition="onset Tg, ISO 11357-2",
            s_confidence="datasheet",
        ),
        melting_temp=_PV(
            d_value=343.0,
            s_units="C",
            s_source=_VICTREX_PEEK_450G_SHEET + " -- Melting Temperature = 343 C (ISO 11357-3)",
            s_confidence="datasheet",
        ),
        thermal_expansion=_PV(
            d_value=55e-6,
            s_units="1/K",
            s_source=_VICTREX_PEEK_450G_SHEET
            + " -- CLTE Average below Tg = 55 ppm/K (ISO 11359-2)",
            s_condition="below Tg (< 143 C), average direction",
            s_confidence="datasheet",
        ),
        # v0.7.2: specific_heat REMOVED. The v0.7.0 sweep added 2160 J/(kg·K)
        # citing the Victrex 450G TDS (March 2026 revision), but the v0.7.2
        # URL-fetch validation against the current revision did NOT find a
        # specific-heat row, only DTUL, Tg, Tm, CLTE, k, RTI. The c_p
        # value may have been in an older Victrex revision or a different
        # Victrex document, but the cited TDS does not currently publish
        # it. Under strict Tier-1, the field is removed. Not yet sourced at Tier 1; an
        # alternate Tier-1 source is needed (older Victrex rev, Victrex Properties Guide
        # brochure, or NIST polymer database).
    ),
)


# ── PEI Ultem 1010 (SABIC) ──────────────────────────────────────────────────

pei_ultem_1010 = Material(
    s_id="pei_ultem_1010",
    s_description="PEI (Polyetherimide): SABIC Ultem 1010, unfilled amorphous",
    s_category="polymer",
    s_specification=(
        "SABIC Ultem Resin 1010 (Americas region): amorphous, transparent, general-purpose PEI"
    ),
    s_catalog_version=_S_CATALOG_VERSION,
    s_last_reviewed=_S_LAST_REVIEWED,
    structural=Structural(
        youngs_modulus=_PV(
            d_value=3.58e9,
            s_units="Pa",
            s_source=_SABIC_ULTEM_1010_SHEET
            + " -- Tensile Modulus, 5 mm/min = 3580 MPa (ASTM D 638)",
            s_condition="5 mm/min, ASTM D 638",
            s_confidence="datasheet",
        ),
        # v0.7.2: poisson_ratio REMOVED. v0.7.0 added 0.36 citing SABIC
        # Ultem 1010 TDS, but v0.7.2 URL-fetch validation confirmed the
        # actual TDS does NOT publish a Poisson ratio row. The v0.7.0
        # s_notes even said "(typical for amorphous PEI)": that was a
        # red flag we missed. Under strict Tier-1, the field is removed.
        # Not yet sourced at Tier 1.
        yield_stress=_PV(
            d_value=110e6,
            s_units="Pa",
            s_source=_SABIC_ULTEM_1010_SHEET + " -- Tensile Stress at Yield (Type I, 5 mm/min) = "
            "110 MPa (ASTM D 638)",
            s_condition="Type I tensile, 5 mm/min yield, ASTM D 638",
            s_confidence="datasheet",
        ),
        flexural_strength=_PV(
            d_value=165e6,
            s_units="Pa",
            s_source=_SABIC_ULTEM_1010_SHEET
            + " -- Flexural Stress at yield, 2.6 mm/min, 100 mm span = "
            "165 MPa (ASTM D 790)",
            s_condition="23 C yield, 2.6 mm/min, 100 mm span, ASTM D 790",
            s_confidence="datasheet",
            s_notes=(
                "v0.6.0 sweep added. PEI Ultem 1010 is an amorphous "
                "engineering thermoplastic with ductile yield, so this "
                "flex-strength slot stores the SABIC TDS Flexural Stress "
                "at YIELD (the brittle-flex caveat that applies to "
                "sintered NdFeB / SmCo / ceramics does NOT apply here). "
                "Cross-check: flexural modulus = 3510 MPa per the same "
                "ASTM D 790 row: very close to tensile modulus 3580 MPa "
                "as expected for an isotropic amorphous polymer."
            ),
        ),
        density=_PV(
            d_value=1270.0,
            s_units="kg/m^3",
            s_source=_SABIC_ULTEM_1010_SHEET + " -- Specific Gravity = 1.27 (ASTM D 792)",
            s_condition="23 C, ASTM D 792",
            s_confidence="datasheet",
            s_notes=(
                "v0.6.0 sweep added. Was MISSING from v0.5.0 despite the "
                "SABIC Ultem 1010 Americas TDS plainly publishing Specific "
                "Gravity = 1.27 in its PHYSICAL section (ASTM D 792). "
                "Converted via the rule that specific gravity is "
                "dimensionless ratio rho/rho_water at 23 C with rho_water "
                "~ 1000 kg/m^3, giving 1270 kg/m^3."
            ),
        ),
    ),
    electromagnetic=Electromagnetic(
        resistivity_at_20C=_PV(
            d_value=1.0e15,
            s_units="Ohm*m",
            s_source=_SABIC_ULTEM_1010_SHEET
            + " -- Volume Resistivity = 1.E+17 Ohm*cm (ASTM D 257). "
            "Converted to Ohm*m by /100.",
            s_condition="23 C, ASTM D 257",
            s_confidence="datasheet",
            s_notes=(
                "v0.7.1 sweep added. SABIC publishes Volume Resistivity "
                "as 1.E+17 Ohm*cm = 1.E+15 Ohm*m per ASTM D257 in the "
                "ELECTRICAL section of the Ultem 1010 Americas TDS. "
                "Higher than PEEK 450G (1e14 Ohm*m at 23 C) because "
                "amorphous PEI is more insulating at room T than semi-"
                "crystalline PEEK whose crystalline-amorphous boundary "
                "regions provide ionic conduction pathways. Used "
                "downstream for insulation-design resistance "
                "calculations alongside the stored dielectric_strength "
                "32.6 MV/m for high-voltage standoff design."
            ),
        ),
        dielectric_strength=_PV(
            d_value=32.6e6,
            s_units="V/m",
            s_source=_SABIC_ULTEM_1010_SHEET
            + " -- Dielectric Strength in air at 1.6 mm = 32.6 kV/mm "
            "(ASTM D 149)",
            s_condition="1.6 mm thickness, in air, ASTM D 149",
            s_confidence="datasheet",
        ),
        relative_permittivity=_PV(
            d_value=3.15,
            s_units="",
            s_source=_SABIC_ULTEM_1010_SHEET
            + " -- Relative Permittivity at 1 kHz = 3.15 (ASTM D 150)",
            s_condition="1 kHz, ASTM D 150",
            s_confidence="datasheet",
        ),
    ),
    thermal=Thermal(
        thermal_conductivity=_PV(
            d_value=0.22,
            s_units="W/(m*K)",
            s_source=_SABIC_ULTEM_1010_SHEET + " -- Thermal Conductivity = 0.22 W/m-C (ASTM C177)",
            s_condition="ASTM C177 guarded-hot-plate, room temperature",
            s_confidence="datasheet",
            s_notes=(
                "v0.6.0 sweep added. Listed in the SABIC TDS THERMAL "
                "section. Note: 0.22 W/(m*K) is typical for amorphous "
                "polyetherimides: slightly below PEEK 450G (0.29 "
                "W/(m*K)) because amorphous structure scatters phonons "
                "more than PEEK's semi-crystalline order."
            ),
        ),
        thermal_expansion=_PV(
            d_value=5.58e-5,
            s_units="1/K",
            s_source=_SABIC_ULTEM_1010_SHEET + " -- CTE, -20 C to 150 C, flow = 5.58E-05 1/C "
            "(ASTM E 831)",
            s_condition=("-20 to 150 C interval, flow direction, ASTM E 831"),
            s_confidence="datasheet",
            s_notes=(
                "v0.6.0 sweep added. The SABIC TDS lists CTE only in the "
                "flow direction; cross-flow not published. For amorphous "
                "PEI the through-thickness vs flow anisotropy is small "
                "(unlike fiber-reinforced grades). Note: this value "
                "spans -20 to 150 C, well below the 217 C glass "
                "transition, so it represents the glassy-state CTE. "
                "Above Tg the value rises substantially as is typical "
                "for polymers; SABIC does not publish above-Tg CTE for "
                "Ultem 1010."
            ),
        ),
        max_operating_temp=_PV(
            d_value=170.0,
            s_units="C",
            s_source=_SABIC_ULTEM_1010_SHEET + " -- RTI (Relative Temperature Index, UL 746B): "
            "170 C continuous use for Electrical, Mechanical "
            "with impact, and Mechanical without impact",
            s_condition="continuous service, UL 746B RTI",
            s_confidence="datasheet",
            s_notes=(
                "v0.7.2 CORRECTED: earlier catalog stored 200 C and "
                "cited 'Description: high strength, modulus and "
                "stiffness up to 200 C'. The v0.7.2 URL-fetch validation "
                "confirmed that phrase is NOT in the actual SABIC TDS; "
                "the only published long-term-use temperature scalar "
                "is RTI = 170 C (UL 746B, three categories all agree). "
                "Updated to the TDS-canonical value."
            ),
        ),
        glass_transition=_PV(
            d_value=217.0,
            s_units="C",
            s_source=_SABIC_ULTEM_1010_SHEET
            + " -- Description: 'glass transition temperature (Tg) of "
            "217 C'",
            s_confidence="datasheet",
        ),
        # v0.7.2: specific_heat REMOVED. v0.7.0 added 2000 J/(kg·K)
        # citing the SABIC Ultem 1010 TDS, but v0.7.2 URL-fetch
        # validation confirmed no "Specific Heat" row exists in this
        # TDS. Under strict Tier-1, the field is removed. Not yet sourced at Tier 1.
    ),
)


# ── Nylon-12 SLS (PA12) ─────────────────────────────────────────────────────

nylon12_sls = Material(
    s_id="nylon12_sls",
    s_description="Selective Laser Sintered Nylon 12 (PA12)",
    s_category="polymer",
    s_specification="EOS PA 2200 (also Formlabs Nylon 12, HP MJF PA12)",
    s_catalog_version=_S_CATALOG_VERSION,
    s_last_reviewed="2026-06-22",
    structural=Structural(
        youngs_modulus=_PV(
            d_value=1.65e9,
            s_units="Pa",
            s_source=_EOS_PA2200_SHEET + " -- Young's modulus 1650 MPa for EOS PA 2200 Balance "
            "1.0 grade (XY direction). v0.7.2 corrected from "
            "1700 MPa (grade-mix -- 1700 is the Performance 1.0 "
            "grade modulus; rest of the PA12 catalog values "
            "are from the Balance 1.0 grade with UTS = 48 MPa "
            "and density = 0.93 g/cm^3, so this catalog entry "
            "is now consistently Balance 1.0).",
            s_condition="XY build orientation, EOS PA 2200 Balance 1.0",
            s_confidence="datasheet",
        ),
        # v0.7.2: yield_stress REMOVED. The catalog stored 48 MPa labeled
        # "Tensile yield" but the EOS PA 2200 TDS publishes only ONE
        # tensile-strength scalar (48 MPa): there's no separate yield
        # column. PA12 has no clear yield-vs-UTS distinction in this TDS
        # presentation. The 48 MPa value is correctly stored as
        # ultimate_tensile below. Under strict Tier-1, removing the
        # duplicate-labeled yield_stress field.
        # v1.9.1: yield_stress STAYS None, re-confirmed, not an oversight.
        # A downstream structural tool skips any
        # material whose yield_stress is None, so this was revisited by
        # reading the Formlabs Nylon 12 Powder TDS (the Fuse-series powder)
        # directly. That sheet ALSO publishes only a single UTS
        # (50 MPa) and no distinct yield. Since SLS PA12 elongation at break
        # is 6-11%, a real yield would sit BELOW the UTS; storing UTS here
        # would overstate yield. The strength scalar lives in ultimate_tensile
        # (re-sourced to Formlabs, 50 MPa); a consumer that needs a strength
        # limit should read ultimate_tensile when yield_stress is None.
        # v0.7.2: fatigue_endurance REMOVED. v0.2.x stored 24 MPa at 10^6
        # cycles R=0.1 citing EOS, but v0.7.2 URL-fetch validation across
        # 5 EOS revisions confirmed no fatigue row exists in any EOS PA
        # 2200 TDS. The value likely came from the Formlabs Nylon 12 SLS
        # cross-reference in the original citation string, but without a
        # direct Formlabs-TDS source-of-record this can't ship as Tier 1.
        # Not yet sourced at Tier 1.
        ultimate_tensile=_PV(
            d_value=50e6,
            s_units="Pa",
            s_source=_FORMLABS_NYLON12_POWDER + " -- Ultimate Tensile Strength = 50 MPa (ASTM D638 "
            "Type 1). Re-sourced in v1.9.1 from EOS PA 2200 "
            "Balance 1.0 (48 MPa) to the Formlabs Nylon 12 Powder "
            "TDS -- the data sheet for the Fuse-series powder the "
            "downstream structural consumer actually prints.",
            s_condition=(
                "Fuse 1, ASTM D638 Type 1; specimens conditioned 50% RH / "
                "23 °C / 7 days. UTS reported as a single scalar (build "
                "orientation not split for strength)."
            ),
            s_confidence="datasheet",
            s_notes=(
                "This is the design strength allowable for SLS PA12: the "
                "material fails at low strain (Formlabs elongation at break "
                "X/Y 11% / Z 6%) with no ductile plateau, so the UTS is the "
                "peak engineering stress and the appropriate scalar for an "
                "FEM stress constraint. No distinct YIELD strength is "
                "populated (yield_stress stays None): neither the Formlabs "
                "nor the EOS TDS publishes one, and a true yield for a "
                "<=11%-elongation grade lies BELOW this UTS: copying UTS "
                "into yield_stress would overstate yield and is forbidden "
                "under the Tier-1 / no-fabrication rule. Anisotropy + "
                "cross-check (catalog's v0.7.3-verified EOS PA 2200 "
                "Balance 1.0 data): EOS lists Tensile Strength 48 MPa X/Y "
                "and 42 MPa Z, consistent with Formlabs 50 MPa within ~4%; "
                "parts built vertically (Z) should be derated toward "
                "~42 MPa. Consumers reading yield_stress for a strength "
                "limit should fall back to ultimate_tensile."
            ),
        ),
        density=_PV(
            d_value=930.0,
            s_units="kg/m^3",
            s_source=_EOS_PA2200_SHEET + " -- density 0.93 g/cm^3",
            s_confidence="datasheet",
        ),
    ),
    thermal=Thermal(
        # v0.7.2: max_operating_temp REMOVED. v0.2.x stored 160 C citing
        # EOS "continuous use temperature", but v0.7.2 URL-fetch validation
        # across 5 EOS PA 2200 revisions confirmed no such scalar exists.
        # Closest available EOS scalars are Vicat A/50 = 181 C and Vicat
        # B/50 = 163 C; HDT @ 0.45 MPa = 157/145 C (X/Z); HDT @ 1.80 MPa
        # = 64/57 C (X/Z): all are deflection-onset, not continuous-use.
        # Under strict Tier-1, removing. Not yet sourced at Tier 1.
        melting_temp=_PV(
            d_value=176.0,
            s_units="C",
            s_source=_EOS_PA2200_SHEET + " -- Melting point per EN ISO 11357-1 = 176 C",
            s_condition="EN ISO 11357-1 DSC",
            s_confidence="datasheet",
            s_notes=(
                "v0.7.2 CORRECTED s_notes: earlier sweep claimed the "
                "EOS TDS published a '172-180 C range, 176 C is the "
                "midpoint'. The v0.7.2 URL-fetch validation across 5 "
                "EOS revisions confirmed the TDS publishes a single "
                "scalar 176 C (sometimes shown as 178), not an "
                "explicit range. Value is unchanged; s_notes corrected. "
                "SLS-processed PA12 has a slightly broader and lower "
                "melting endotherm than virgin PA12 because of "
                "repeated thermal cycling of the powder bed."
            ),
        ),
    ),
)


# ── DuPont Nomex 410 calendered aramid paper ───────────────────────────────
#
# v0.2.2 addition. The dominant motor stator slot-liner insulation.
# Properties listed for 0.25 mm thickness (the standard motor-slot size).
# Dielectric strength and tensile vary with thickness; see source for
# the full 11-thickness tables.

nomex_410 = Material(
    s_id="nomex_410",
    s_description="DuPont Nomex 410 calendered aramid paper, 0.25 mm thickness",
    s_category="polymer",
    s_specification=(
        "DuPont Nomex 410 (meta-aramid PMIA, calendered insulation paper), "
        "0.25 mm / 10 mil nominal thickness; Class C (220 degC continuous "
        "via UL 746B RTI). Available 0.05-0.76 mm."
    ),
    s_catalog_version=_S_CATALOG_VERSION,
    s_last_reviewed=_S_LAST_REVIEWED,
    structural=Structural(
        ultimate_tensile=_PV(
            d_value=118e6,
            s_units="Pa",
            s_source=_DUPONT_NOMEX_410 + " -- Table III p.3, MD tensile 296 N/cm at 0.25 mm "
            "nominal thickness. Stress = 296 N / (1 cm * 0.25 mm) = "
            "296 N / 2.5 mm^2 = 118.4 MPa.",
            s_condition="machine direction (MD), 0.25 mm, ASTM D828",
            s_confidence="datasheet",
            s_notes=(
                "Cross-direction (XD) is 161 N/cm at 0.25 mm = 64.4 MPa per "
                "the same DuPont Table III: Nomex 410 is anisotropic from "
                "calendering. MD value used as the primary tensile scalar "
                "since slot-liner stress is dominated by axial pull in motor "
                "applications. v0.2.3 corrected from 114 MPa (arithmetic "
                "error in v0.2.2, independent audit caught: "
                "296 N/cm at 0.25 mm = 118.4 MPa, not 114)."
            ),
        ),
        density=_PV(
            d_value=960.0,
            s_units="kg/m^3",
            s_source=_DUPONT_NOMEX_410 + " -- Table III p.3, density 0.96 g/cm^3 at 0.25 mm. "
            "Range across all thicknesses: 720-1130 kg/m^3 "
            "(calendering increases density with thickness).",
            s_condition="0.25 mm calendered Nomex 410",
            s_confidence="datasheet",
            s_notes=(
                "MATERIAL-WIDE N/A-BY-PHYSICS CAVEAT (applies to every "
                "value in this Material; v0.6.0): Nomex 410 has NO "
                "Young's modulus and NO Poisson ratio because it is a "
                "fibrous calendered meta-aramid PAPER, not a bulk "
                "isotropic solid. The stress-strain response is "
                "nonlinear from very low strain (the felted PMIA fibers "
                "straighten and slip past each other as load builds), "
                "and there is no characteristic linear-elastic modulus "
                "to report. The DuPont K-20612-2 TDS publishes a "
                "tensile-at-strain Vickers table per thickness "
                "(Table III: ASTM D828 N/cm at break, with elongation "
                "22% MD / 18% XD at 0.25 mm) but explicitly no Young's "
                "modulus scalar. For fracture-mode sizing use the "
                "stored ultimate_tensile (118 MPa MD / 64 MPa XD "
                "documented in s_notes there); for stiffness modeling "
                "consult the full DuPont stress-strain curve, which is "
                "not a single Young's modulus. The structural slot "
                "leaves youngs_modulus, poisson_ratio, yield_stress, "
                "and fatigue_endurance as None on purpose: they are "
                "physically meaningless for calendered aramid paper, "
                "NOT a TODO."
            ),
        ),
    ),
    electromagnetic=Electromagnetic(
        resistivity_at_20C=_PV(
            d_value=2.0e14,
            s_units="Ohm*m",
            s_source=_DUPONT_NOMEX_410 + " -- Table II 'Electrical Properties as a Function "
            "of Relative Humidity' at 0.25 mm: volume "
            "resistivity = 2 × 10^16 Ω·cm = 2 × 10^14 Ω·m at "
            "50% RH, 23 °C (standard engineering conditions)",
            s_condition="23 C, 50% RH (standard conditions), 0.25 mm",
            s_confidence="datasheet",
            s_notes=(
                "v0.7.1 corrected: third-party audit caught that the "
                "v0.7.0 value 1.0e16 Ω·m was off by ~100x. The actual "
                "DuPont K-20612-2 Table II publishes a 3-point humidity "
                "scan at 0.25 mm thickness:\n"
                "  - 6 × 10^16 Ω·cm = 6e14 Ω·m at oven-dry (worst-case high)\n"
                "  - 2 × 10^16 Ω·cm = 2e14 Ω·m at 50% RH (standard)\n"
                "  - 2 × 10^14 Ω·cm = 2e12 Ω·m at 96% RH (worst-case low)\n"
                "Stored: the 50% RH 'standard conditions' value, 2e14 "
                "Ω·m. Calendered paper structure wicks water into fiber "
                "interstices, hence the 100x drop from dry to 96% RH. "
                "For sealed-housing dry-operating motor applications use "
                "the 6e14 dry value; for unsealed high-humidity envs "
                "expect 2e12 drift. Cross-reference Table II's humidity-"
                "dependent dielectric-loss and dielectric-constant data "
                "for high-RH motor environments."
            ),
        ),
        dielectric_strength=_PV(
            d_value=33e6,
            s_units="V/m",
            s_source=_DUPONT_NOMEX_410
            + " -- Table I p.1, AC rapid-rise dielectric strength 33 kV/mm "
            "at 0.25 mm (ASTM D149). At thinner samples it rises "
            "(0.13 mm: 28 kV/mm; 0.05 mm: 18 kV/mm) -- thickness-"
            "dependent.",
            s_condition="0.25 mm thickness, AC rapid rise, ASTM D149",
            s_confidence="datasheet",
            s_notes=(
                "DESIGN DERATING: the 33 MV/m rapid-rise value is the "
                "INSTANTANEOUS breakdown, NOT a continuous-service rating. "
                "DuPont's continuous-stress design guidance from the same "
                "TDS is <=1.6 kV/mm = 1.6 MV/m (40 V/mil), i.e. ~20:1 below "
                "rapid-rise breakdown. Use 1.6 MV/m for steady-state insulation "
                "sizing in motor slot liners; 33 MV/m only for transient "
                "withstand. (SynFlex recommends an even-more-conservative "
                "1.2 MV/m for permanent stress.)"
            ),
        ),
        relative_permittivity=_PV(
            d_value=2.7,
            s_units="",
            s_source=_DUPONT_NOMEX_410 + " -- Table I p.1, Dielectric Constant at 60 Hz = 2.7 "
            "at 0.25 mm nominal thickness (ASTM D150)",
            s_condition="0.25 mm thickness, 60 Hz, dry, ASTM D150",
            s_confidence="datasheet",
            s_notes=(
                "v0.6.0 sweep added. The DuPont K-20612-2 TDS Table I "
                "publishes dielectric constant per thickness; at 0.25 "
                "mm (the standard motor-slot size) the 60 Hz value is "
                "2.7. The same table publishes a full thickness series "
                "(1.6 at 0.05 mm, 1.8 at 0.10 mm, 2.4 at 0.13 mm, 2.7 "
                "at 0.18 mm, 2.7 at 0.25 mm, 2.9 at 0.30 mm, 3.2 at "
                "0.38 mm, 3.4 at 0.51 mm, 3.7 at 0.61 mm and 0.076 mm), "
                "increasing with thickness as the calendered density "
                "rises. Table II shows minor humidity dependence: at "
                "0.25 mm, dielectric constant moves 2.5 (oven dry) -> "
                "2.7 (50% RH) -> 3.2 (96% RH). 60 Hz vs 1 kHz also "
                "minor (2.6 at 1 kHz, 50% RH per Table II). Frequency "
                "dependence is essentially flat up to 10^4 Hz per the "
                "TDS narrative."
            ),
        ),
    ),
    thermal=Thermal(
        thermal_conductivity=_PV(
            d_value=0.139,
            s_units="W/(m*K)",
            s_source=_DUPONT_NOMEX_410 + " -- Table IV p.6, through-thickness k 0.139 W/(m*K) at "
            "0.25 mm at 150 C (ASTM E1530). In-plane k is not "
            "published.",
            s_condition="through-thickness, 0.25 mm, 150 C, ASTM E1530",
            s_confidence="datasheet",
        ),
        max_operating_temp=_PV(
            d_value=220.0,
            s_units="C",
            s_source=_DUPONT_NOMEX_410 + " -- Table VI p.7, UL 746B RTI Electrical 220 C / RTI "
            "Mechanical 220 C (Class C insulation, exceeds Class H 180 C)",
            s_condition="continuous service per UL 746B RTI",
            s_confidence="datasheet",
        ),
    ),
)


# ── Magnet wire enamel: PAI Class 200 (NEMA MW 35-C) ──────────────────────
#
# v0.2.2 addition. The winding insulation coating on magnet wire.
# Properties are for the BULK PAI POLYMER (basis Solvay Torlon 4203L);
# wire-level properties (e.g., dielectric breakdown of the finished
# wire) depend on AWG + build thickness and live in the s_notes per
# property, not as numeric fields.

mw_pai_class_200 = Material(
    s_id="mw_pai_class_200",
    s_description=(
        "Magnet wire enamel: polyamide-imide (PAI) film, NEMA MW 35-C "
        "Class 200: bulk polymer properties (PAI resin)"
    ),
    s_category="polymer",
    s_specification=(
        "NEMA MW 35-C Class 200 enamelled wire grade; the polymer is "
        "Solvay Torlon 4203L unfilled PAI resin (the chemical basis of "
        "most modern Class 200 magnet wire coatings). Wire-level "
        "dielectric + thermal-class properties are graded per NEMA "
        "MW 1000 / IEC 60317-13; polymer bulk properties from Solvay "
        "Torlon 4203L TDS."
    ),
    s_catalog_version=_S_CATALOG_VERSION,
    s_last_reviewed=_S_LAST_REVIEWED,
    structural=Structural(
        youngs_modulus=_PV(
            d_value=4.48e9,
            s_units="Pa",
            s_source=_SOLVAY_TORLON_4203L + " -- Tensile Modulus = 4480 MPa (ASTM D638, Type I "
            "specimen)",
            s_condition=("23 C, ASTM D638 Type I, BULK PAI resin (NOT finished wire film)"),
            s_confidence="datasheet",
            s_notes=(
                "v0.6.0 sweep added. Same bulk-vs-finished-wire-film "
                "caveat as density: this is Solvay Torlon 4203L PAI "
                "resin tested per ASTM D638, NOT the modulus of the "
                "thin cured enamel on finished magnet wire. The Solvay "
                "TDS also publishes Tensile Modulus = 4900 MPa via "
                "ASTM D1708 (microtensile geometry): the 4480 MPa "
                "D638 value is the standard engineering reference and "
                "is stored here. Cross-check: Flexural Modulus = 5030 "
                "MPa at 23 C (Solvay TDS D790), consistent with the "
                "tensile value within ~10%."
            ),
        ),
        poisson_ratio=_PV(
            d_value=0.45,
            s_units="",
            s_source=_SOLVAY_TORLON_4203L + " -- Poisson's Ratio = 0.45 (ASTM E132)",
            s_condition="23 C, ASTM E132, bulk PAI resin",
            s_confidence="datasheet",
            s_notes=(
                "v0.6.0 sweep added. Solvay's TDS publishes nu = 0.45 "
                "via ASTM E132. This is high for an engineering "
                "polymer (most amorphous thermoplastics are 0.35-0.42); "
                "PAI's high value reflects strong intermolecular "
                "hydrogen bonding and near-incompressibility. Same "
                "bulk-resin caveat as the density and Young's modulus "
                "above: this is the bulk-resin scalar, not the "
                "Poisson ratio of the thin cured enamel film on "
                "finished magnet wire. Used downstream by stress-"
                "analysis code; if a consumer is modeling magnet-wire "
                "winding stiffness rather than bulk PAI, treat as "
                "a starting point and apply geometric corrections "
                "for build thickness."
            ),
        ),
        ultimate_tensile=_PV(
            d_value=152e6,
            s_units="Pa",
            s_source=_SOLVAY_TORLON_4203L + " -- Tensile Strength = 152 MPa (ASTM D638, Type I "
            "specimen, dry-as-molded)",
            s_condition=("23 C, ASTM D638 Type I, BULK PAI resin (NOT finished wire film)"),
            s_confidence="datasheet",
            s_notes=(
                "v0.6.0 sweep added. PAI 4203L is ductile (7.6% "
                "elongation at break per D638) so the Solvay TDS "
                "publishes a single Tensile Strength scalar, which "
                "for a ductile thermoplastic is the peak engineering "
                "stress on the stress-strain curve. Stored in "
                "ultimate_tensile (NOT in flexural_strength) because "
                "this is a pure-tension ductile strength scalar, not "
                "a 3-pt-bend brittle peak. Cross-check: Tensile Stress "
                "by ASTM D1708 microtensile = 192 MPa (higher because "
                "of the shorter gauge length). The Solvay TDS also "
                "publishes a Flexural Strength = 241 MPa at 23 C "
                "(ASTM D790) which is stored separately in "
                "flexural_strength. Same bulk-PAI-resin caveat as "
                "density/E/Poisson: this is the bulk-resin value, "
                "not the finished-wire enamel film."
            ),
        ),
        flexural_strength=_PV(
            d_value=241e6,
            s_units="Pa",
            s_source=_SOLVAY_TORLON_4203L + " -- Flexural Strength at 23 C = 241 MPa (ASTM D790)",
            s_condition="23 C, ASTM D790, bulk PAI resin",
            s_confidence="datasheet",
            s_notes=(
                "v0.6.0 sweep added. PAI is a ductile polymer (unlike "
                "sintered NdFeB / SmCo where flex is the only "
                "available peak-stress scalar), so this flexural-"
                "strength value coexists with a real ultimate_tensile "
                "value (152 MPa): the 241 MPa flex peak is ~1.6x "
                "tensile, consistent with the bending-out-of-flaws "
                "ratio for ductile thermoplastics. Solvay TDS also "
                "publishes 118 MPa at 232 C (substantial roll-off "
                "above 232 C, still well below Tg = 277 C: typical "
                "thermoplastic creep at elevated T). Same bulk-PAI-"
                "resin caveat as density."
            ),
        ),
        density=_PV(
            d_value=1420.0,
            s_units="kg/m^3",
            s_source=_SOLVAY_TORLON_4203L + " -- specific gravity 1.42 (ASTM D792)",
            s_condition="20 C, unfilled BULK PAI resin (NOT finished wire film)",
            s_confidence="datasheet",
            s_notes=(
                "CAVEAT (added v0.2.3 per independent audit round 2): "
                "this is the bulk-resin density of Solvay Torlon 4203L PAI. "
                "The DENSITY OF THE THIN INSULATION FILM ON FINISHED MAGNET "
                "WIRE may differ slightly from the bulk-resin value due to "
                "calendering, cure-shrinkage, and trace voids in the build-up. "
                "NEMA MW 35-C and Superior Essex GP/MR-200 do NOT publish a "
                "wire-level insulation-film density scalar. For winding-mass "
                "estimation, use this 1420 kg/m^3 bulk value combined with "
                "the wire's specified build thickness (AWG + heavy/single "
                "build per the same NEMA spec): accept ~5% uncertainty on "
                "the insulation mass term until a measured value is sourced."
            ),
        ),
    ),
    electromagnetic=Electromagnetic(
        resistivity_at_20C=_PV(
            d_value=2.0e15,
            s_units="Ohm*m",
            s_source=_SOLVAY_TORLON_4203L + " -- Volume Resistivity = 2.0E+17 ohms*cm (ASTM D257). "
            "Converted to Ohm*m by /100.",
            s_condition="23 C, ASTM D257, bulk PAI resin",
            s_confidence="datasheet",
            s_notes=(
                "v0.7.1 sweep added. Solvay TDS publishes Volume "
                "Resistivity = 2.0E+17 Ohm*cm = 2.0E+15 Ohm*m (ASTM "
                "D257); Surface Resistivity = 5.0E+18 ohms (the same "
                "TDS). Higher than both PEEK 450G (1e14 Ohm*m) and PEI "
                "Ultem 1010 (1e15 Ohm*m): PAI's rigid imide backbone "
                "and high glass transition (~277 C) keep ionic mobility "
                "low at room T. Same bulk-PAI-resin caveat as the "
                "structural values: this is bulk-resin volume "
                "resistivity, NOT the finished-wire enamel film's "
                "insulation resistance (which is geometry-driven per "
                "NEMA MW 35-C). Used for insulation-design margin "
                "alongside dielectric_strength 18 MV/m."
            ),
        ),
        relative_permittivity=_PV(
            d_value=4.20,
            s_units="",
            s_source=_SOLVAY_TORLON_4203L + " -- Dielectric Constant at 60 Hz = 4.20 (ASTM D150). "
            "TDS also publishes 3.90 at 1 MHz (frequency-"
            "dependent dispersion); the 60 Hz value matches "
            "the catalog's power-line-frequency convention "
            "used for Nomex and other low-frequency insulator "
            "applications.",
            s_condition="60 Hz, ASTM D150, bulk PAI resin",
            s_confidence="datasheet",
            s_notes=(
                "v0.7.3 manual verification: changed from 4.1 "
                "(interpolated at 1 kHz between TDS's 60 Hz and 1 MHz "
                "anchor points) to 4.20 (TDS-direct value at 60 Hz). "
                "The interpolation was technically a derivation, not "
                "Tier-1: the actual TDS only publishes 60 Hz and "
                "1 MHz endpoints. Convention here aligns with Nomex's "
                "60 Hz storage. For 1 MHz applications, use TDS value "
                "3.90 directly."
            ),
        ),
        dielectric_strength=_PV(
            d_value=23e6,
            s_units="V/m",
            s_source=_SOLVAY_TORLON_4203L + " -- Dielectric Strength = 23 kV/mm (ASTM D149), "
            "bulk PAI resin. TDS does not specify specimen "
            "thickness for this row (ASTM D149 short-time "
            "default is 1/8 in / 3.2 mm specimen, but the "
            "specific thickness is NOT in the cited row).",
            s_condition="ASTM D149 short-time, bulk PAI resin (specimen thickness not stated in TDS)",  # noqa: E501
            s_confidence="datasheet",
            s_notes=(
                "v0.7.1 corrected: third-party audit caught that "
                "v0.2.2 had stored 18 MV/m with a vague 'intrinsic ~18 "
                "kV/mm' citation, but the Solvay Torlon 4203L TDS "
                "plainly publishes 23 kV/mm per ASTM D149 in its "
                "ELECTRICAL properties table. Updated to the actual "
                "TDS-published value. This is the BULK polymer value "
                "for a 3.2 mm specimen: the finished-magnet-wire "
                "breakdown value per NEMA MW 35-C depends on AWG + "
                "build (e.g., 22 AWG Heavy build minimum dielectric "
                "breakdown 4620 V is geometry-driven, not material-"
                "driven)."
            ),
        ),
    ),
    thermal=Thermal(
        thermal_conductivity=_PV(
            d_value=0.26,
            s_units="W/(m*K)",
            s_source=_SOLVAY_TORLON_4203L + " -- k = 0.26 W/(m*K) (ASTM C177)",
            s_condition="20 C, unfilled PAI resin",
            s_confidence="datasheet",
        ),
        thermal_expansion=_PV(
            d_value=3.1e-5,
            s_units="1/K",
            s_source=_SOLVAY_TORLON_4203L + " -- CLTE Flow = 3.1E-5 cm/cm/C (ASTM E831)",
            s_condition="flow direction, ASTM E831, bulk PAI resin",
            s_confidence="datasheet",
            s_notes=(
                "v0.6.0 sweep added. Solvay TDS publishes only the "
                "flow-direction CLTE; cross-flow not published. PAI "
                "has a low CTE for an unfilled polymer (31 ppm/K vs "
                "PEEK 55 ppm/K, Ultem 1010 56 ppm/K): the rigid "
                "imide backbone and aromatic linkages give "
                "near-thermoset thermal dimensional stability. Same "
                "bulk-PAI-resin caveat as the structural values: this "
                "is bulk-resin CTE, not the CTE of the cured enamel "
                "on finished magnet wire. The wire-level effective "
                "CTE on a copper substrate is dominated by the Cu "
                "thermal-expansion mismatch (~17 ppm/K Cu vs 31 ppm/K "
                "PAI bulk), which sets up stress in the enamel film "
                "across thermal cycles. Designers should use this 31 "
                "ppm/K value combined with Cu CTE to estimate "
                "interface stress, NOT as a wire-pair CTE."
            ),
        ),
        max_operating_temp=_PV(
            d_value=200.0,
            s_units="C",
            s_source=_NEMA_MW_35C + " -- Class 200 = 200 C continuous service temperature "
            "(grade-defining value of the NEMA MW 35-C standard)",
            s_condition="continuous service, NEMA MW 35-C grade",
            s_confidence="standard",
        ),
        glass_transition=_PV(
            d_value=277.0,
            s_units="C",
            s_source=_SOLVAY_TORLON_4203L + " -- Torlon 4203L Tg = 277 C (DSC, footnote 2: "
            "'Tg, onset, Solvay method, 2nd heat. Method is "
            "equivalent to ISO 11357-2') per Solvay TDS "
            "THERMAL properties table",
            s_condition="DSC onset, Solvay method 2nd heat (ISO 11357-2 equivalent)",
            s_confidence="datasheet",
            s_notes=(
                "v0.7.1 corrected: third-party audit caught that "
                "v0.2.2 stored 275 °C citing 'DMA, ASTM D5023', but the "
                "Solvay TDS plainly publishes 277 °C via DSC (footnote: "
                "Solvay method, equivalent to ISO 11357-2). The 275 C "
                "DMA value is a different measurement, not the TDS "
                "primary. Updated to the TDS-canonical DSC scalar."
            ),
        ),
    ),
)


# ── Magnet wire enamel: PUR Class 130 (NEMA MW 1000 grade MW 130 / IEC 60317-1) ──
#
# v0.2.5 addition. The low-cost, low-temperature counterpart to
# mw_pai_class_200 above. Polyurethane (PUR) wire enamel is the dominant
# insulation on consumer-grade motor windings, transformer coils,
# solenoids, and small-appliance brushless rotors where the operating
# temperature stays at or below the 130 degC NEMA Class 130 ceiling.
#
# Sourcing posture:
#   - max_operating_temp = 130 degC is the GRADE-DEFINING value of NEMA
#     MW 1000 (grade MW 130, "Polyurethane Bondable - 130") and IEC
#     60317-1 / 60317-2 / 60317-4. The 130 in the grade designation IS
#     the 130 degC continuous-service spec, so this anchor is Tier 1
#     "standard" by definition.
#   - All OTHER bulk-PUR-resin properties (density, Tg, k_thermal,
#     epsilon_r, E_dielectric) require a primary TDS for the actual
#     rigid PUR wire-enamel resin, which, unlike PAI/Torlon (which has
#     a Solvay bulk-resin TDS), is NOT widely published. The closest
#     adjacent value found is dielectric_constant = 3.70 from MWS Wire
#     Industries' Multifilar Magnet Wire table for Polyurethane 155
#     (MW 79-C); applying it to the Class 130 grade is a derivation /
#     inference, not a primary value, so it is OMITTED per the Tier-1
#     policy. Bulk-elastomer PUR sheets (Lubrizol Estane, BASF
#     Elastollan, Covestro Desmopan) are thermoplastic elastomers and
#     are NOT chemically analogous to the rigid thermosetting PUR film
#     used on magnet wire, so they are also not used.
#   - Wire-level dielectric breakdown values (kV per AWG/build) are
#     geometry-driven, not material-driven, and live in NEMA MW 1000
#     Annex tables, not as a scalar material property. See s_notes on
#     max_operating_temp for the design-implication summary.

mw_pur_class_130 = Material(
    s_id="mw_pur_class_130",
    s_description=(
        "Magnet wire enamel: polyurethane (PUR) film, NEMA MW 1000 grade "
        "MW 130 (Polyurethane Bondable - 130) / IEC 60317-1 Class 130: "
        "low-cost, low-temperature winding insulation"
    ),
    s_category="polymer",
    s_specification=(
        "NEMA MW 1000 grade MW 130 'Polyurethane Bondable - 130' (equivalent "
        "to IEC 60317-1 'Solderable polyurethane enamelled round copper "
        "wire, class 130' general requirements + IEC 60317-2 / 60317-4 "
        "variants); the polymer is a rigid thermosetting polyurethane "
        "wire-enamel resin (specific resin formulation is vendor- and "
        "lot-dependent: Elantas Isonel-PU, Schenectady IsoMid, and "
        "MicroLab Vamac variants all qualify against the NEMA grade). "
        "Wire-level dielectric + thermal-class properties are graded per "
        "NEMA MW 1000 / IEC 60317-1; no bulk PUR-enamel-resin TDS at "
        "Tier 1 has been sourced, so the catalog entry presently records "
        "only the grade-defining 130 degC operating temperature."
    ),
    s_catalog_version=_S_CATALOG_VERSION,
    s_last_reviewed=_S_LAST_REVIEWED,
    thermal=Thermal(
        max_operating_temp=_PV(
            d_value=130.0,
            s_units="C",
            s_source=_NEMA_MW_1000_PUR_130 + " -- Class 130 = 130 C continuous service temperature "
            "(grade-defining value of NEMA MW 1000 grade MW 130 "
            "AND of IEC 60317-1 / 60317-2 / 60317-4 -- their "
            "titles literally include the phrase 'class 130')",
            s_condition="continuous service, NEMA MW 1000 grade MW 130 / IEC 60317-1 Class 130",
            s_confidence="standard",
            s_notes=(
                "MATERIAL-WIDE GAP CAVEAT (applies to every value in "
                "this Material; reaffirmed in v0.6.0 sweep): MW PUR "
                "Class 130 lacks bulk-resin structural data because "
                "NO Tier-1 PUR enamel resin TDS has been found yet: "
                "wire-level mechanical properties are AWG/build "
                "dependent. This is NOT an N/A-by-physics case (PUR "
                "enamels DO have well-defined bulk density, modulus, "
                "k, etc.): it is a genuine SOURCING gap. The v0.6.0 "
                "pursuit (2026-05-24) searched Elantas Isonel "
                "(Isonel-PU 31-398 surfaced but is an IMPREGNATING "
                "resin, not a wire-enamel film TDS), Schenectady "
                "IsoMid (no public TDS), Covestro Desmodur W / Mondur "
                "PR (these are isocyanate INTERMEDIATES, not finished "
                "wire enamels), and Asahi Yupiace U (no English "
                "TDS). No Tier-1 bulk PUR wire-enamel-resin scalar "
                "data could be retrieved. The bulk PUR THERMOPLASTIC-"
                "ELASTOMER TDSes (Lubrizol Estane, BASF Elastollan, "
                "Covestro Desmopan) are NOT chemically analogous to "
                "a rigid wire-enamel film and were deliberately NOT "
                "cross-applied. Also rejected: MWS Multifilar table's "
                "dielectric_constant = 3.70 (it is for Polyurethane "
                "155 / MW 79-C, a DIFFERENT grade, so applying it "
                "would be a derivation that the Tier-1 policy "
                "forbids). The same 'bulk polymer vs finished wire "
                "film' caveat as mw_pai_class_200 applies in "
                "principle but cannot be tested until a bulk-resin "
                "TDS exists. For wire-level dielectric breakdown by "
                "AWG + build (single / heavy / triple), consult NEMA "
                "MW 1000 Section 3.8 + Annex tables; those are "
                "geometry-driven and not material-scalar properties. "
                "A Tier-1 wire-enamel resin TDS is still needed "
                "(Elantas, Schenectady, or Hitachi Chemical) for bulk "
                "density / E / nu / k / epsilon_r / dielectric_strength "
                "of the rigid thermosetting PUR enamel film."
            ),
        ),
    ),
)


# ── Prusament PLA: FDM print polymer (Prusa Core One default) ─────────────
#
# v0.5.0 addition. The dominant FDM filament for desktop 3D printing;
# a common default material for the Prusa Core One+.
# Originally deleted in v0.2.0's Tier-1 sweep because the previous
# values were MatWeb-aggregated; restored here with a vendor TDS
# (Prusa Polymers / Prusa Research) citation.

pla_3dprint = Material(
    s_id="pla_3dprint",
    s_description=(
        "Prusament PLA: FDM-printed polylactic acid filament (canonical Prusa Core One material)"
    ),
    s_category="polymer",
    s_specification=(
        "Prusament PLA, Prusa Research a.s. (FDM filament, 1.75 mm "
        "diameter, line-standard mechanical properties across colorways; "
        "test specimens FDM-printed per Prusament TDS profile)"
    ),
    s_catalog_version=_S_CATALOG_VERSION,
    s_last_reviewed=_S_LAST_REVIEWED,
    structural=Structural(
        youngs_modulus=_PV(
            d_value=2.30e9,
            s_units="Pa",
            s_source=_PRUSAMENT_PLA_TDS + " -- Tensile Modulus = 2.3 ± 0.1 GPa (ISO 527-1, "
            "FDM-printed specimen)",
            s_condition="23 C, ISO 527-1, FDM-printed Prusament PLA",
            s_confidence="datasheet",
            s_notes=(
                "v0.7.2 CORRECTED: v0.5.0 stored 2.20 GPa citing "
                "'ISO 527-2'. v0.7.2 URL-fetch validation of the actual "
                "Prusament PLA TDS v1.1 (2022-07-27) confirms the value "
                "is 2.3 ± 0.1 GPa per ISO 527-1 (note: 527-1, not "
                "527-2: the latter is for tensile-test specimen "
                "dimensions, the former is the test method)."
            ),
        ),
        yield_stress=_PV(
            d_value=51e6,
            s_units="Pa",
            s_source=_PRUSAMENT_PLA_TDS + " -- Tensile Yield Strength = 51 ± 3 MPa (ISO "
            "527-1, FDM-printed specimen)",
            s_condition="23 C yield, ISO 527-1, FDM-printed Prusament PLA",
            s_confidence="datasheet",
            s_notes=(
                "v0.7.2 CORRECTED: v0.5.0 stored 50 MPa citing 'ISO "
                "527-2'. v0.7.2 URL-fetch validation of the actual "
                "Prusament PLA TDS v1.1 confirms the value is 51 ± 3 "
                "MPa per ISO 527-1. Within the band, but the TDS "
                "midpoint is 51, not 50."
            ),
        ),
        # v0.7.2: ultimate_tensile REMOVED. v0.5.0 stored 60 MPa citing
        # Prusament TDS, but v0.7.2 URL-fetch validation confirmed the
        # TDS has no UTS column, only Tensile Yield Strength. PLA is
        # ductile-ish with UTS ≈ yield in practice, so the engineering
        # information is captured in yield_stress above. Under strict
        # Tier-1, removing the unsourced field.
        density=_PV(
            d_value=1240.0,
            s_units="kg/m^3",
            s_source=_PRUSAMENT_PLA_TDS + " -- Density = 1.24 g/cm^3 (ISO 1183-1)",
            s_condition="23 C, FDM-printed bulk density",
            s_confidence="datasheet",
        ),
        flexural_strength=_PV(
            d_value=83e6,
            s_units="Pa",
            s_source=_PRUSAMENT_PLA_TDS + " -- Flexural Strength horizontal print direction = "
            "83 +/- 6 MPa (ISO 178); vertical x-z = 99 +/- 1 MPa",
            s_condition=(
                "23 C, ISO 178 3-pt bend, FDM-printed Original Prusa i3 "
                "MK3, horizontal print orientation, 0.20 mm layers, "
                "100% rectilinear infill"
            ),
            s_confidence="datasheet",
            s_notes=(
                "v0.6.0 sweep added. The Prusament TDS publishes "
                "flexural strength in TWO print orientations: "
                "horizontal = 83 +/- 6 MPa, vertical x-z = 99 +/- 1 "
                "MPa. The horizontal value is stored as the more "
                "conservative scalar (FDM is weakest in inter-layer "
                "adhesion which the horizontal-print bend test "
                "exercises). Cross-check: flexural modulus = 3.1 GPa "
                "horizontal / 3.2 GPa vertical: 40% stiffer than the "
                "tensile modulus 2.3 GPa, which is unusual but "
                "consistent with FDM-printed parts where layer-to-"
                "layer porosity is in tension when pulled axially but "
                "compressed out when loaded in bending. PLA is "
                "ductile-ish (~3% elongation at yield) so this flex-"
                "strength slot stores a real peak-stress value, not "
                "a brittle-fracture analog. Use the horizontal value "
                "as the FDM-design floor; use the vertical value only "
                "when the part is printed with the load axis aligned "
                "with the build z direction."
            ),
        ),
    ),
    thermal=Thermal(
        max_operating_temp=_PV(
            d_value=55.0,
            s_units="C",
            s_source=_PRUSAMENT_PLA_TDS + " -- Heat Deflection Temperature at 0.45 MPa = "
            "55 C (ISO 75, FDM-printed Prusament PLA)",
            s_condition="HDT @ 0.45 MPa, ISO 75, FDM-printed",
            s_confidence="datasheet",
            s_notes=(
                "v0.7.2 RE-SOURCED: v0.5.0 stored 50 C citing the "
                "Prusament TDS for 'Maximum service temperature' but "
                "v0.7.2 validation confirmed the TDS does NOT publish "
                "a max-service-temperature scalar. The TDS DOES publish "
                "HDT @ 0.45 MPa = 55 C (ISO 75), which is the closest "
                "actually-TDS-published proxy for the continuous-"
                "service ceiling. The semantics are slightly different "
                "(HDT is deflection-onset at low load; max service is "
                "creep-onset under design load) but the 55 C value is "
                "in the right ballpark and is now genuinely Tier-1. "
                "For continuous-service design, anneal to crystallize "
                "the print → service temperature rises to ~110-130 C; "
                "or switch to a higher-T_g filament (PETG, PEEK)."
            ),
        ),
        # v0.7.2: glass_transition REMOVED. v0.5.0 stored 60 C citing
        # the Prusament TDS, but v0.7.2 URL-fetch validation confirmed
        # the TDS has no Tg row. The 60 C value matches the published
        # PLA family Tg per NatureWorks Ingeo 4043D TDS + ASTM D3418
        # DSC, but those upstream sources are currently Salesforce-
        # gated and can't be Tier-1 cited. Under strict Tier-1, the
        # field is removed. Not yet sourced at Tier 1; the
        # target is to acquire NatureWorks Ingeo Salesforce access or substitute a
        # published Tier-1 PLA Tg measurement.
        # v0.7.2: melting_temp REMOVED. Same rationale as glass_transition
        # above: Prusament TDS doesn't publish a Tm scalar, and the
        # upstream Ingeo TDS (which does publish 145-160 C DSC peak)
        # is Salesforce-gated. The Prusament product LANDING PAGE
        # mentions ~175 C melt temp, which contradicts the catalog's
        # 155 C and was the third independent signal that the value
        # wasn't Prusament-sourced. Under strict Tier-1, removed.
        # Not yet sourced at Tier 1.
    ),
)


# ── Prusament PETG: FDM print polymer ─────────────────────────────────────
#
# Restores the FDM PETG category that v0.2.0 deleted (petg_fdm, whose values
# were MatWeb-aggregated) under a new id with a vendor TDS citation. Follows
# the pla_3dprint pattern: the horizontal-print value is stored as the
# conservative FDM scalar and the vertical x-z value is recorded in s_source.

petg_3dprint = Material(
    s_id="petg_3dprint",
    s_description="Prusament PETG: FDM-printed glycol-modified PET filament",
    s_category="polymer",
    s_specification=(
        "Prusament PETG, Prusa Polymers a.s. (FDM filament, 1.75 +/- 0.02 mm "
        "diameter; test specimens FDM-printed per the Prusament TDS profile)"
    ),
    s_catalog_version=_S_CATALOG_VERSION,
    s_last_reviewed=_S_LAST_REVIEWED,
    structural=Structural(
        youngs_modulus=_PV(
            d_value=1.5e9,
            s_units="Pa",
            s_source=_PRUSAMENT_PETG_TDS + " -- Tensile Modulus, horizontal print direction = "
            "1.5 +/- 0.1 GPa (ISO 527-1, FDM-printed specimen); vertical x-z = 1.6 +/- 0.1 GPa",
            s_condition="23 C, ISO 527-1, FDM-printed Prusament PETG, horizontal print direction",
            s_confidence="datasheet",
            s_notes=(
                "Horizontal value stored as the conservative FDM scalar (same "
                "convention as pla_3dprint). Roughly 35% less stiff than "
                "Prusament PLA (2.3 GPa), the expected PETG-vs-PLA trade."
            ),
        ),
        yield_stress=_PV(
            d_value=47e6,
            s_units="Pa",
            s_source=_PRUSAMENT_PETG_TDS + " -- Tensile Yield Strength, horizontal print "
            "direction = 47 +/- 2 MPa (ISO 527-1); vertical x-z = 50 +/- 1 MPa; filament-level "
            "'Tensile Yield Strength for Filament' = 46 +/- 1 MPa (ISO 527)",
            s_condition="23 C yield, ISO 527-1, FDM-printed Prusament PETG, horizontal",
            s_confidence="datasheet",
            s_notes=(
                "PETG is ductile (5.1% elongation at yield per the same table), "
                "so this is a real yield, not a brittle-fracture proxy. The TDS "
                "publishes no ultimate tensile strength row; ultimate_tensile "
                "stays None rather than copying yield into it."
            ),
        ),
        flexural_strength=_PV(
            d_value=66e6,
            s_units="Pa",
            s_source=_PRUSAMENT_PETG_TDS + " -- Flexural Strength, horizontal print direction = "
            "66 +/- 2 MPa (ISO 178); vertical x-z = 70 +/- 1 MPa",
            s_condition=(
                "23 C, ISO 178 3-pt bend, FDM-printed Original Prusa i3 MK3, "
                "horizontal print orientation, 0.20 mm layers, 100% rectilinear infill"
            ),
            s_confidence="datasheet",
            s_notes=(
                "Flexural modulus on the same table: 1.7 GPa horizontal / 1.6 GPa "
                "vertical x-z. Ductile material, so this slot stores a real "
                "peak-stress value, not a brittle-fracture analog."
            ),
        ),
        density=_PV(
            d_value=1270.0,
            s_units="kg/m^3",
            s_source=_PRUSAMENT_PETG_TDS + " -- Density = 1.27 g/cm3 (ISO 1183)",
            s_condition="23 C, ISO 1183, filament",
            s_confidence="datasheet",
        ),
    ),
    thermal=Thermal(
        max_operating_temp=_PV(
            d_value=68.0,
            s_units="C",
            s_source=_PRUSAMENT_PETG_TDS + " -- Heat Deflection Temperature at 0.45 MPa = 68 C "
            "(ISO 75); the 1.80 MPa HDT is also 68 C",
            s_condition="HDT @ 0.45 MPa, ISO 75, FDM-printed",
            s_confidence="datasheet",
            s_notes=(
                "Same HDT-as-continuous-service-ceiling convention as pla_3dprint: "
                "the TDS publishes no max-service-temperature, Tg, or Tm scalar, "
                "and HDT is the closest TDS-published proxy. The product page "
                "quotes 'temperature resistance 68 C', consistent with this row. "
                "glass_transition and melting_temp stay None (not on the TDS)."
            ),
        ),
    ),
)


# ── DuPont Kapton HN: polyimide film (flex-circuit and slot insulation) ────
#
# Values are the 25 um (1 mil) column of Table 1 and the corresponding rows
# of Tables 2 and 3. Kapton HN is sold from 12.7 to 125 um; tensile strength,
# modulus, density, and the thermal rows are gauge-independent on the sheet,
# while dielectric strength and elongation vary with thickness (recorded in
# s_notes so a consumer at another gauge knows to re-read the sheet).

kapton_hn = Material(
    s_id="kapton_hn",
    s_description="DuPont Kapton HN general-purpose polyimide film, 25 um (1 mil) gauge",
    s_category="polymer",
    s_specification=(
        "DuPont Kapton HN polyimide film, 25 um / 1 mil nominal gauge (product "
        "specification H-38479; certified to ASTM D5213 type 1, item A). "
        "Available 12.7-125 um."
    ),
    s_catalog_version=_S_CATALOG_VERSION,
    s_last_reviewed=_S_LAST_REVIEWED,
    structural=Structural(
        youngs_modulus=_PV(
            d_value=2.76e9,
            s_units="Pa",
            s_source=_DUPONT_KAPTON_HN + " -- Table 1, Tensile Modulus at 23 C = 400,000 psi "
            "(2.76 GPa), identical across all listed gauges",
            s_condition="23 C, 25 um film; 25 x 150 mm specimen, 50 mm/min (Table 1 footnote)",
            s_confidence="datasheet",
            s_notes="Falls to 290,000 psi (2.0 GPa) at 200 C per the same table.",
        ),
        poisson_ratio=_PV(
            d_value=0.34,
            s_units="",
            s_source=_DUPONT_KAPTON_HN + " -- Table 1, Poisson's Ratio = 0.34",
            s_condition="23 C, film",
            s_confidence="datasheet",
        ),
        yield_stress=_PV(
            d_value=69e6,
            s_units="Pa",
            s_source=_DUPONT_KAPTON_HN + " -- Table 1, 'Yield Point at 3%' at 23 C = 69 MPa "
            "(10,000 psi), identical across all listed gauges",
            s_condition="23 C, 3% yield point (film convention), 25 um film",
            s_confidence="datasheet",
            s_notes=(
                "Polyimide film has no 0.2%-offset yield; the sheet's 'Yield Point "
                "at 3%' is the vendor's yield definition and is stored as-is. Falls "
                "to 41 MPa at 200 C. 'Stress to produce 5% elongation' = 90 MPa on "
                "the same table."
            ),
        ),
        ultimate_tensile=_PV(
            d_value=231e6,
            s_units="Pa",
            s_source=_DUPONT_KAPTON_HN + " -- Table 1, Ultimate Tensile Strength at 23 C = "
            "33,500 psi (231 MPa), identical across all listed gauges",
            s_condition="23 C, 25 um film, tensile at break",
            s_confidence="datasheet",
            s_notes=(
                "Falls to 20,000 psi (138 MPa) at 200 C. Ultimate elongation is "
                "gauge-dependent (65% at 12.7 um to 82% at 125 um; 72% at 25 um)."
            ),
        ),
        density=_PV(
            d_value=1420.0,
            s_units="kg/m^3",
            s_source=_DUPONT_KAPTON_HN + " -- Table 1, Density = 1.42 g/cc, all gauges",
            s_condition="23 C",
            s_confidence="datasheet",
        ),
    ),
    electromagnetic=Electromagnetic(
        resistivity_at_20C=_PV(
            d_value=1.5e15,
            s_units="Ohm*m",
            s_source=_DUPONT_KAPTON_HN + " -- Table 3, Volume Resistivity, 25 um = 1.5 x 10^17 "
            "ohm*cm (ASTM D-257). Converted to ohm*m by /100.",
            s_condition="23 C, 50% RH, ASTM D-257, 25 um film",
            s_confidence="datasheet",
            s_notes="Gauge-dependent on the sheet: 1.5e17 ohm*cm at 12.7-50 um, 1.0e17 at 125 um.",
        ),
        dielectric_strength=_PV(
            d_value=303e6,
            s_units="V/m",
            s_source=_DUPONT_KAPTON_HN + " -- Table 3, Dielectric Strength, 25 um (1 mil) = "
            "303 V/um (7700 V/mil), 60 Hz, 1/4 in electrodes, 500 V/s rise (ASTM D-149)",
            s_condition="23 C, 50% RH, 60 Hz, ASTM D-149, 25 um film",
            s_confidence="datasheet",
            s_notes=(
                "Strongly gauge-dependent, as for every film: 315 V/um at 12.7 um "
                "down to 154 V/um at 125 um. Re-read Table 3 for any other gauge; "
                "do not scale this value."
            ),
        ),
        relative_permittivity=_PV(
            d_value=3.4,
            s_units="",
            s_source=_DUPONT_KAPTON_HN + " -- Table 3, Dielectric Constant, 25 um = 3.4 at 1 kHz "
            "(ASTM D-150)",
            s_condition="23 C, 50% RH, 1 kHz, ASTM D-150, 25 um film",
            s_confidence="datasheet",
            s_notes="3.4 at 12.7-50 um, 3.5 at 75-125 um. Dissipation factor 0.0018 at 25 um.",
        ),
    ),
    thermal=Thermal(
        thermal_conductivity=_PV(
            d_value=0.20,
            s_units="W/(m*K)",
            s_source=_DUPONT_KAPTON_HN + " -- Table 2, Coefficient of Thermal Conductivity = "
            "0.20 W/m*K (4.8 x 10^-4 cal/s*cm*C) at 296 K (ASTM D5470)",
            s_condition="23 C (296 K), ASTM D5470",
            s_confidence="datasheet",
        ),
        specific_heat=_PV(
            d_value=1090.0,
            s_units="J/(kg*K)",
            s_source=_DUPONT_KAPTON_HN + " -- Table 2, Specific Heat = 1.09 J/g*K (0.261 cal/g*C), "
            "differential calorimetry",
            s_condition="differential calorimetry; temperature not stated on the sheet",
            s_confidence="datasheet",
        ),
        thermal_expansion=_PV(
            d_value=20e-6,
            s_units="1/K",
            s_source=_DUPONT_KAPTON_HN + " -- Table 2, Thermal Coefficient of Linear Expansion = "
            "20 ppm/C (11 ppm/F) over -14 to 38 C (ASTM D-696)",
            s_condition="-14 to 38 C, ASTM D-696, as-received film",
            s_confidence="datasheet",
            s_notes=(
                "Table 4 gives the thermally exposed 25 um film 17 ppm/C over "
                "30-100 C and higher values in the 100-400 C bands; the film also "
                "shrinks irreversibly on first heating (0.17% after 30 min at "
                "150 C). Use the Table 2 as-received value for room-temperature "
                "fit-up and re-read Table 4 for elevated-temperature design."
            ),
        ),
        # glass_transition intentionally None: the sheet gives only a range
        # ("a second order transition occurs between 360 C and 410 C ... assumed
        # to be the glass transition"), not a scalar. melting_temp is None because
        # the sheet states 'Melting Point: None' (ASTM E-794); polyimide does not
        # melt. max_operating_temp is None because the sheet describes use from
        # -269 C to 400 C but publishes no rated continuous-service temperature
        # (no UL 746B RTI row).
    ),
)


# ── LOCTITE STYCAST 2850FT (with CAT 9): thermally conductive epoxy encapsulant
#
# The standard stator/coil potting compound. Cured properties depend on the
# catalyst; CAT 9 (room-temperature cure) is the general-purpose system and
# the one stored here. Other catalysts (11, 23LV, 24LV) change Tg, CTE, and
# the operating range and would be separate entries.

stycast_2850ft = Material(
    s_id="stycast_2850ft",
    s_description=(
        "Henkel LOCTITE STYCAST 2850FT thermally conductive, electrically insulating epoxy "
        "encapsulant, cured with CAT 9"
    ),
    s_category="polymer",
    s_specification=(
        "LOCTITE STYCAST 2850FT (alumina-filled epoxy, black) with LOCTITE CAT 9, mixed "
        "100:3.5 by weight, cured 16-24 h at 25 C (or 1-2 h at 65 C) per the Henkel TDS"
    ),
    s_catalog_version=_S_CATALOG_VERSION,
    s_last_reviewed=_S_LAST_REVIEWED,
    structural=Structural(
        flexural_strength=_PV(
            d_value=92e6,
            s_units="Pa",
            s_source=_HENKEL_STYCAST_2850FT_CAT9 + " -- Flexural strength = 92 N/mm2 (13,300 psi), "
            "cured with CAT 9",
            s_condition="cured, room temperature",
            s_confidence="datasheet",
            s_notes=(
                "Highly filled thermoset: brittle in bending, so this is a fracture "
                "envelope. The TDS publishes no tensile strength or modulus; "
                "youngs_modulus, yield_stress, and ultimate_tensile stay None."
            ),
        ),
        compressive_strength=_PV(
            d_value=155e6,
            s_units="Pa",
            s_source=_HENKEL_STYCAST_2850FT_CAT9
            + " -- Compressive strength = 155 N/mm2 (22,500 psi), "
            "cured with CAT 9",
            s_condition="cured, room temperature",
            s_confidence="datasheet",
        ),
        density=_PV(
            d_value=2290.0,
            s_units="kg/m^3",
            s_source=_HENKEL_STYCAST_2850FT_CAT9 + " -- 'Typical Uncured Properties as Mixed': "
            "Density = 2.29 g/cm3 (STYCAST 2850FT with CAT 9)",
            s_condition="as mixed, uncured (TDS publishes no cured density; linear shrinkage 0.2%)",
            s_confidence="datasheet",
            s_notes=(
                "Resin alone is 2.4 g/cm3, catalyst 1.0 g/cm3. With 0.2% linear cure "
                "shrinkage the cured density is within 1% of the mixed value, but "
                "only the mixed value is published, so that is what is stored."
            ),
        ),
        # hardness_vickers stays None: the TDS publishes Shore D 96, a durometer
        # scale that does not convert to Vickers.
    ),
    electromagnetic=Electromagnetic(
        resistivity_at_20C=_PV(
            d_value=1e13,
            s_units="Ohm*m",
            s_source=_HENKEL_STYCAST_2850FT_CAT9
            + " -- Volume resistivity @ 25 C = 1 x 10^15 ohm-cm. "
            "Converted to Ohm*m by /100.",
            s_condition="25 C, cured",
            s_confidence="datasheet",
        ),
        dielectric_strength=_PV(
            d_value=14.4e6,
            s_units="V/m",
            s_source=_HENKEL_STYCAST_2850FT_CAT9 + " -- Dielectric strength = 14.4 kV/mm",
            s_condition="cured; specimen thickness not stated on the TDS",
            s_confidence="datasheet",
        ),
        relative_permittivity=_PV(
            d_value=5.01,
            s_units="",
            s_source=_HENKEL_STYCAST_2850FT_CAT9 + " -- Dielectric constant / Dissipation factor "
            "@ 1 MHz = 5.01 / 0.028",
            s_condition="1 MHz, cured",
            s_confidence="datasheet",
        ),
    ),
    thermal=Thermal(
        thermal_conductivity=_PV(
            d_value=1.25,
            s_units="W/(m*K)",
            s_source=_HENKEL_STYCAST_2850FT_CAT9 + " -- Thermal conductivity = 1.25 W/(m-K)",
            s_condition="cured; temperature not stated on the TDS",
            s_confidence="datasheet",
            s_notes="About 5x an unfilled epoxy; the alumina filler is the point of this grade.",
        ),
        max_operating_temp=_PV(
            d_value=130.0,
            s_units="C",
            s_source=_HENKEL_STYCAST_2850FT_CAT9 + " -- Operating temperature, C = -40 to 130 "
            "(CAT 9 system)",
            s_condition="continuous, cured with CAT 9",
            s_confidence="datasheet",
            s_notes=(
                "Catalyst-dependent: the uncatalysed 2850FT TDS quotes -40 to 175 C "
                "continuous for the higher-temperature catalyst systems. CAT 9 is the "
                "limiting case stored here."
            ),
        ),
        thermal_expansion=_PV(
            d_value=35.0e-6,
            s_units="1/K",
            s_source=_HENKEL_STYCAST_2850FT_CAT9 + " -- Coefficient of thermal expansion, ppm: "
            "Alpha 1 = 35.0 (below Tg); Alpha 2 = 98.9 (above Tg)",
            s_condition="below Tg (alpha 1), cured with CAT 9",
            s_confidence="datasheet",
            s_notes=(
                "Alpha 2 (above the 86 C Tg) is 98.9 ppm/K, nearly 3x. Potting that "
                "runs above Tg sees the higher value; design the stator fit-up "
                "against alpha 2 if the winding hot spot exceeds ~86 C."
            ),
        ),
        glass_transition=_PV(
            d_value=86.0,
            s_units="C",
            s_source=_HENKEL_STYCAST_2850FT_CAT9 + " -- Glass transition temperature = 86 C",
            s_condition="cured with CAT 9",
            s_confidence="datasheet",
        ),
    ),
)


# ── BASF Elastollan 1195 A: Shore 95A polyether TPU (soft-robotics / flexure grade)
#
# The v0.2.0 catalog deleted tpu_95a for MatWeb sourcing. The BASF product
# range brochure tabulates the whole Elastollan line from the vendor; the
# 1195 A 10 column is the Shore ~95A polyether grade. Only the structural
# rows that map to schema slots are stored; TPU has no yield point and the
# brochure publishes no E-modulus for the A-hardness grades.

tpu_elastollan_1195a = Material(
    s_id="tpu_elastollan_1195a",
    s_description="BASF Elastollan 1195 A polyether thermoplastic polyurethane, Shore 96A / 48D",
    s_category="elastomer",
    s_specification=(
        "BASF Elastollan 1195 A 10 (11 Series polyether TPU, cylindrical granules, no "
        "lubricant), typical values on injection-moulded specimens per the BASF "
        "product range brochure"
    ),
    s_catalog_version=_S_CATALOG_VERSION,
    s_last_reviewed=_S_LAST_REVIEWED,
    structural=Structural(
        ultimate_tensile=_PV(
            d_value=55e6,
            s_units="Pa",
            s_source=_BASF_ELASTOLLAN_RANGE + " -- Tensile strength = 55 MPa (DIN 53504-S2)",
            s_condition="23 C, DIN 53504 S2 specimen, injection moulded",
            s_confidence="datasheet",
            s_notes=(
                "Elongation at break 500%; stress at 20/100/300% elongation = 6/10/18 "
                "MPa on the same table. TPU has no yield point, so yield_stress stays "
                "None. E-modulus is published only for the D-hardness grades; "
                "youngs_modulus stays None. Hardness Shore A 96 / Shore D 48 (DIN ISO "
                "7619-1, 3 s) is a durometer scale with no Vickers slot."
            ),
        ),
        density=_PV(
            d_value=1150.0,
            s_units="kg/m^3",
            s_source=_BASF_ELASTOLLAN_RANGE + " -- Density = 1.15 g/cm3 (DIN EN ISO 1183-1-A)",
            s_condition="23 C, DIN EN ISO 1183-1-A",
            s_confidence="datasheet",
        ),
    ),
    # No thermal group: the brochure publishes no Tg, Vicat, or service-temperature
    # row for the 11 Series, and the grade-specific TDS was not obtainable.
)


# ── Catalog dict
CATALOG: dict[str, Material] = {
    peek_unfilled.s_id: peek_unfilled,
    pei_ultem_1010.s_id: pei_ultem_1010,
    nylon12_sls.s_id: nylon12_sls,
    pla_3dprint.s_id: pla_3dprint,
    petg_3dprint.s_id: petg_3dprint,
    kapton_hn.s_id: kapton_hn,
    stycast_2850ft.s_id: stycast_2850ft,
    tpu_elastollan_1195a.s_id: tpu_elastollan_1195a,
    nomex_410.s_id: nomex_410,
    mw_pai_class_200.s_id: mw_pai_class_200,
    mw_pur_class_130.s_id: mw_pur_class_130,
}


__all__ = [
    "CATALOG",
    "kapton_hn",
    "mw_pai_class_200",
    "mw_pur_class_130",
    "nomex_410",
    "nylon12_sls",
    "peek_unfilled",
    "pei_ultem_1010",
    "petg_3dprint",
    "pla_3dprint",
    "stycast_2850ft",
    "tpu_elastollan_1195a",
]
