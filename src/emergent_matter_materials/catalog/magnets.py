"""Permanent magnets: NdFeB + SmCo grades (Tier-1-only catalog).

Under the v0.2.0 "Tier 1 only" policy, this file contains only
PropertyValues with confidence in {measured, datasheet, standard}.

Three plain NdFeB grades + three high-temp variants + one SmCo 2:17
grade, all verified against Arnold Magnetics PDFs.

| Material    | Tier 1 fields                                | Per-grade PDF                  |
|-------------|----------------------------------------------|--------------------------------|
| ndfeb_n35   | EM trio + thermal + density + flexural       | Arnold N35 PDF Rev. 210607     |
| ndfeb_n42   | EM trio + thermal + density + flexural       | Arnold N42 PDF Rev. 210607     |
| ndfeb_n50   | EM trio + thermal + density + flexural       | Arnold N50 PDF Rev. 210802     |
| ndfeb_n42sh | EM trio + thermal + density + flexural       | Arnold N42SH PDF Rev. 020821   |
| ndfeb_n42uh | EM trio + thermal + density + flexural       | Arnold N42UH PDF Rev. 210607   |
| ndfeb_n42eh | EM trio + thermal + density + flexural       | Arnold N42EH PDF Rev. 151021a  |
| smco_2_17   | EM trio + thermal (5) + structural (3:       | Arnold Recoma combined catalog |
|             | density, E, flexural)                        | Rev. 160205a (Recoma 28 page   |
|             |                                              | Rev. 131025)                   |

v0.2.4 (2026-05-24): structural flexural strength restored across all
six NdFeB grades using the per-grade PDFs' "Flexural Strength" line
(41,300 psi / 285 MPa, identical across all sintered NdFeB grades).
Initially stored in the ``ultimate_tensile`` slot per v0.2.x schema;
v0.3.0 moved to the new dedicated ``flexural_strength`` slot.
N35 and N50 per-grade PDFs newly retrieved this release: N42 PDF was
already in the verification trail. Stored in ``ultimate_tensile`` with
notes documenting the brittle-fracture flexural-vs-tensile convention.
ALSO new in v0.2.4: ``smco_2_17`` (Sm2Co17 high-temperature permanent
magnet) added: the rare-earth alternative to NdFeB for service above
200 C (Curie temp 825 C vs NdFeB's 310 C; Tw 350 C vs NdFeB EH's 200 C).
Sourced from the Arnold Recoma combined SmCo catalog: per-grade Recoma 28
page (Rev. 131025) for the bulk of the fields, plus the catalog summary
table on p.2 (Rev. 160205a) for the cross-grade verification.

v0.6.0 (2026-05-24): Per-grade-PDF re-sweep + explicit N/A-by-physics
documentation pass. The full text of each Arnold per-grade PDF
(N35/N42/N50/N42SH/N42UH/N42EH Rev. 210607/210802/020821/151021a) and
the Recoma combined catalog (Recoma 28 page Rev. 131025) was extracted
and inspected field-by-field. Findings:

  Arnold publishes per grade BUT no v0.6.0 schema slot exists:
   - Hardness, Vickers = 620 Hv (all NdFeB grades); 600 Hv (Recoma 28;
     earlier notes said 800, which is its compressive strength in MPa).
   - α(HcJ) reversible temperature coefficient of intrinsic coercivity:
     -0.62 %/°C (N35/N42/N50 plain), -0.55 (N42SH), -0.51 (N42UH),
     -0.42 (N42EH), -0.24 (Recoma 28). Schema only has
     temp_coeff_remanence (α(Br)).
   - α(Br) perpendicular-axis = 0.11 %/°C: Arnold publishes BOTH C//
     and C⊥; v0.6.0 schema's temp_coeff_remanence stores only one
     scalar.
   - Coercivity HcB (regular): published alongside HcJ (intrinsic);
     schema slot Electromagnetic.coercivity stores HcJ per existing
     v0.2.4 convention.
   - CTE perpendicular = -1×10⁻⁶/K (plain, SH, UH), -0.1×10⁻⁶/K (EH).
     Schema's thermal_expansion stores only the parallel value.
   - Recoma 28 only: Compressive Strength = 116,000 psi / 800 MPa.
     No schema slot for compressive_strength.
   - BHmax energy product (kJ/m³ range) published; schema has no slot.

  Arnold lists row but value is BLANK (cannot store at Tier 1):
   - Electrical Resistivity, ρ (mΩ·cm): the "Other Properties" block
     row is present on every per-grade PDF and on every catalog page,
     but the value cell is empty. Arnold does NOT publish a ρ number
     for sintered NdFeB or sintered Sm2Co17. Generic handbook values
     (~1.4-1.6 µΩ·m for NdFeB) are Tier-2 and rejected.
   - Specific heat on N35/N42/N50 per-grade PDFs is also blank, but
     the catalog Rev. 181031 plain-grade pages DO list 460 J/(kg·K)
     numerically: already stored from v0.2.2.

  Fields that stay None on Structural for brittle sintered NdFeB:
  these are N/A-BY-PHYSICS, not sourcing gaps:
   - ``youngs_modulus``: sintered NdFeB is a brittle intermetallic;
     the elastic modulus is physically meaningful for the linear
     range, but Arnold publishes no number. Single-crystal C_ij DO
     exist (Hirosawa, Tokuhara, Sagawa, Yamamoto, Fujimura 1986
     J. Appl. Phys. 59(3):873) and an aggregate Voigt-Reuss-Hill E
     ~150-160 GPa could be derived, but a derived value would
     violate the Tier-1-only policy (confidence='derived' is Tier 4).
   - ``poisson_ratio``: Arnold publishes no Poisson ratio.
   - ``yield_stress``: physically N/A for brittle sintered NdFeB
     and SmCo. The material has no plastic-yield region; it fractures
     elastically. Asking for σ_y on Nd2Fe14B is asking a question the
     physics doesn't answer.
   - ``ultimate_tensile``: physically N/A (same brittle-intermetallic
     argument). Arnold publishes only flexural strength as the
     fracture-mode scalar; that lives in ``flexural_strength``.
   - ``fatigue_endurance``: brittle materials don't have a clean
     Basquin-curve endurance limit; Arnold publishes no fatigue data.

  Each flexural_strength PropertyValue's s_notes was expanded with an
  explicit N/A-BY-PHYSICS CONVENTION block documenting the above so a
  downstream consumer reading the None values knows they're physics-
  driven, not awaiting a TODO closure.

  Electromagnetic N/A-BY-PHYSICS for permanent magnets:
   - ``relative_permeability``: the schema slot stores the soft-magnetic
     μ_r (near origin / at saturation operating points). For permanent
     magnets the operating point sits on the 2nd-quadrant demag curve,
     not at μ_r ≈ const, and the soft-magnetic μ_r and PM recoil-line
     slope are physically distinct quantities. The slot stays None for
     hard magnets to prevent any downstream consumer from ingesting a
     PM scalar into a soft-magnetic μ_r-typed code path. The defining
     "magnetization" EM scalars for a hard magnet are B_r (stored in
     ``remanence``) and H_c (stored in ``coercivity``); the small-
     signal PM permeability for FEM purposes is stored separately in
     ``recoil_permeability`` (added v1.1.0; see below).
   - ``recoil_permeability`` (added v1.1.0): μ_rec = (1/μ₀)·(dB/dH),
     the small-signal slope of the recoil line on the 2nd-quadrant
     B-H curve. Defined in IEC 60404-8-1 as an "additional magnetic
     property" of hard magnets. Populated for ALL 7 magnets in this
     catalog. Source provenance per grade (Shin-Etsu's public per-grade
     coverage is NOT 1:1 with the Arnold grade lineup):
       * ndfeb_n50:   direct Shin-Etsu N50 datasheet, μr = 1.05
       * ndfeb_n42sh: direct/near-direct Shin-Etsu N42SH-R datasheet,
                      μr = 1.05 ("-R" is a Shin-Etsu commercial suffix)
       * ndfeb_n35, ndfeb_n42: Arnold family-typical 1.05 + Shin-Etsu
                      N50/N52 corroboration (no exact-grade Shin-Etsu
                      sheet for N35 or N42)
       * ndfeb_n42uh: Arnold family-typical 1.05 + Shin-Etsu N47UH-GR
                      UH-family corroboration (no exact N42UH sheet)
       * ndfeb_n42eh: Arnold family-typical 1.05 + high-coercivity
                      NdFeB corroboration via Shin-Etsu N47UH-GR
       * smco_2_17:   representative high-energy Sm-Co datasheet
                      (Shin-Etsu R32HS), μr = 1.02, not exact-grade
                      for Recoma 28 but the closest publicly-tabulated
                      Sm2Co17 high-energy sheet listing μ_rec
     This is the right input for FEM magnetostatic solvers that build
     per-region reluctivity ν = 1/(μ₀·μ_rec) for PM regions.
   - ``saturation_flux``: physically not applicable. A permanent
     magnet is operated near its remanence point on the 2nd-quadrant
     demag curve, not driven to saturation by an external H field;
     B_sat is the soft-magnetics envelope quantity for FeCo/SiFe/
     Permendur cores, not for sintered hard magnets. Use B_r
     (remanence) as the magnetization scalar instead.
   - Coercivity HcB (regular, normal): published alongside HcJ
     (intrinsic) on Arnold per-grade PDFs; the schema's
     ``coercivity`` slot stores HcJ by v0.2.4 convention (intrinsic
     is the demag-margin-relevant scalar for motor design: HcJ is
     what guarantees the magnet doesn't lose magnetization under an
     opposing-field excursion). HcB is computable from HcJ and B_r
     via the recoil-line slope and is not stored separately.

  Thermal N/A vs. "not on this datasheet":
   - ``specific_heat`` is sometimes blank on a per-grade PDF and
     present on the broader catalog page (e.g. N35/N42/N50 per-grade
     PDFs blank, catalog Rev. 181031 plain-grade pages list
     460 J/(kg·K)). The PROPERTY exists for these materials: c_p is
     a well-defined thermophysical scalar, but vendor publication is
     inconsistent: it's typical in the primary literature (lab cp
     calorimetry) but often absent from commercial datasheets. Where
     Arnold publishes c_p (NdFeB plain via catalog; all Recoma 2:17
     via per-grade page) it is stored at Tier 1; where Arnold is
     silent and no other Tier 1 source exists, the slot stays None.
     This is a SOURCING gap, not an N/A-by-physics gap: distinct
     from the structural and EM N/A scalars above.

  All seven materials in this catalog (six NdFeB grades + Recoma 28)
  DO populate ``electromagnetic.temp_coeff_remanence`` α(B_r): the
  one temperature-coefficient slot the schema currently exposes.

Schema expansion candidates surfaced in v0.6.0 / v0.7.0:

  RESOLVED: every slot below now exists (``temp_coeff_coercivity`` since
  v1.8.0; ``hardness_vickers``, ``compressive_strength``,
  ``thermal_expansion_perpendicular`` and ``energy_product_max``) and is populated on
  each magnet where Arnold publishes the value.
  The list is kept for the engineering rationale behind each field.

  These are real engineering needs published by Arnold (and standard
  in the permanent-magnet literature) for which v0.6.0's schema has
  no slot. None are inventable from the existing fields. Listed here
  as input to a future v0.8.0+ MINOR bump:

   - ``hardness_HV`` (Vickers hardness, kgf/mm² or HV): Arnold
     publishes 620 HV for all NdFeB grades and 600 HV for Recoma 28.
     Drives machining/grinding feasibility and abrasive-wear margins.
   - ``temp_coeff_coercivity`` α(H_cJ) (1/K): separate slot from
     α(B_r). Arnold publishes per grade: -0.62 %/°C (N35/N42/N50
     plain), -0.55 (N42SH), -0.51 (N42UH), -0.42 (N42EH), -0.24
     (Recoma 28). This is the *defining* thermal-stability scalar
     for high-temperature motor design (demag-margin shrinks faster
     with T than remanence does). Critical missing slot.
   - ``BHmax`` energy product (kJ/m³ or MGOe): the figure-of-merit
     for permanent-magnet selection and the basis for Arnold's
     grade-numbering convention (N35 = 35 MGOe, Recoma 28 = 28 MGOe).
     Currently inferable from remanence × coercivity envelope but
     not stored directly; downstream selection logic re-derives it
     instead of reading a field.
   - ``compressive_strength`` (Pa): Arnold publishes 116,000 psi /
     800 MPa for Recoma 28. Brittle intermetallics fracture in
     bending at flexural_strength (already stored) but typically
     sustain 5-7× higher load in pure compression; the schema
     currently has no slot for the compressive envelope. Relevant
     for press-fit retention sizing and rotor-hub interference fits.
   - ``perpendicular_thermal_expansion`` (1/K): Arnold publishes
     anisotropic CTE for all sintered magnets (NdFeB: 7e-6 parallel
     vs -1e-6 perpendicular; Recoma 28: 11e-6 vs 13e-6). The
     v0.6.0 schema's ``thermal.thermal_expansion`` is a single
     scalar storing the parallel-axis value. Anisotropic CTE
     matters for sleeve/can interference fits and for FEA thermal
     stress on rotor-magnet bonded joints.

  Each of the above is published on the Arnold per-grade PDFs
  (or, for BHmax, on every catalog summary page) at datasheet
  confidence: adding the slots would let those values land at
  Tier 1 immediately. Until then, the values live in s_notes /
  module-docstring narrative form for traceability.

v0.7.1 (2026-05-24): EXHAUSTIVE third audit pass. v0.6.0 had already
swept this file twice (initial pass + v0.7.0 follow-up). The v0.7.1
sweep walked the Arnold per-grade PDFs (N35/N42/N50/N42SH/N42UH/N42EH
Rev. 210607/210802/020821/151021a) and the Recoma combined catalog
(Recoma 28 page Rev. 131025 + summary p.2 Rev. 160205a) field-by-field
against EVERY existing schema slot for every magnet entry, looking for
any Tier-1 datasheet value that had been missed in the prior two
passes.

  Net result: ZERO new PropertyValues added across all seven magnets.
  v0.6.0 was already complete. All NEW Tier-1 candidates surfaced in
  this third pass map to schema slots explicitly deferred
  to a future MINOR bump (hardness_HV, α(HcJ), perpendicular CTE,
  BHmax, compressive_strength); see "Schema expansion candidates"
  block above. No values were invented. The version was bumped to
  record the audit-pass coverage for downstream provenance tracking.

  Fields re-verified populated (no change needed):
   - All 7 magnets: structural.density, structural.flexural_strength
     (NdFeB 285 MPa, SmCo 120 MPa), thermal.thermal_conductivity,
     thermal.specific_heat (460 NdFeB / 350 SmCo J/(kg·K)),
     thermal.max_operating_temp, thermal.curie_temp,
     thermal.thermal_expansion (parallel-axis value per convention),
     electromagnetic.remanence, electromagnetic.coercivity (HcJ min),
     electromagnetic.temp_coeff_remanence α(Br).
   - smco_2_17 ALSO has structural.youngs_modulus (140 GPa, Arnold-
     published: sintered NdFeB does NOT have an Arnold-published E,
     stays None at Tier 1).

  Fields re-confirmed N/A-by-physics or sourcing-gap (no change):
   - electromagnetic.resistivity_at_20C: Arnold sheet row is BLANK
     for ALL 7 magnets (sourcing gap, not addable at Tier 1).
   - electromagnetic.temp_coeff_resistivity: N/A (ρ itself missing).
   - electromagnetic.relative_permeability: N/A-by-physics (recoil
     μ_rec is not the same scalar as soft-magnetic μ_r).
   - electromagnetic.saturation_flux: N/A-by-physics (hard magnets
     operate on 2nd-quadrant demag curve, not at B_sat).
   - electromagnetic.core_loss: N/A-by-physics (permanent magnets
     are not AC-driven soft cores; W/kg loss is meaningless here).
   - electromagnetic.dielectric_strength: N/A-by-physics (sintered
     NdFeB and Sm2Co17 are conductive intermetallics, not dielectrics).
   - electromagnetic.relative_permittivity: N/A-by-physics (same
     reason: conductive intermetallics, not dielectrics).
   - thermal.emissivity: Arnold does NOT publish emissivity for
     either sintered NdFeB or sintered Sm2Co17 on any of the cited
     PDFs (sourcing gap; emissivity is highly surface-finish-dependent
     and not a clean material scalar for magnet bodies: typically
     measured post-coating, e.g. NiCuNi plating vs. epoxy paint).
   - thermal.glass_transition: N/A-by-physics (sintered crystalline
     intermetallics have no T_g; this is a polymer/amorphous scalar).
   - thermal.melting_temp: Arnold does NOT publish a melting point
     on any per-grade PDF. NdFeB undergoes incongruent melting around
     1180 °C (peritectic decomposition of Nd2Fe14B → Nd-rich liquid +
     α-Fe), and Sm2Co17 melts around 1330 °C, but those are general
     handbook/phase-diagram numbers, not vendor-published, so Tier-1
     policy blocks them. Sourcing gap.
   - structural.youngs_modulus: Arnold publishes for SmCo (140 GPa,
     stored) but NOT for sintered NdFeB; the value for NdFeB stays
     None at Tier 1 per the existing N/A-BY-PHYSICS convention
     (single-crystal C_ij measurements exist but derived V-R-H E
     would be confidence='derived' = Tier 4, forbidden).
   - structural.poisson_ratio, .yield_stress, .ultimate_tensile,
     .fatigue_endurance: N/A-by-physics for all 7 (brittle
     intermetallics with no plastic-yield region; Arnold publishes
     only flexural strength as the fracture-mode scalar).

  Tier-1 values that WERE found on the Arnold sheets but BLOCKED by
  the v0.7.1 task constraint (no schema expansion):
   - Hardness HV (620 NdFeB / 600 SmCo): blocked.
   - α(HcJ) per grade (-0.62 to -0.24 %/°C): blocked.
   - Perpendicular CTE (-1 to 13e-6/K): blocked.
   - BHmax energy product (35 MGOe NdFeB / 28 MGOe SmCo): blocked.
   - Compressive strength (800 MPa SmCo only): blocked.
  These remain documented in the "Schema expansion candidates" block
  above as the future v0.8.0+ MINOR-bump targets.

Deleted in v0.2.0, and still awaiting a Tier-1 source:
- ferrite_y30: all values were derived/handbook without primary source
- alnico_5: same

Followup work:
- For NdFeB E, ν, fatigue: would need a measured study on sintered
  Nd-Fe-B (e.g. publications by Pippan, Wachter, or similar fracture-
  mechanics groups); Arnold and most other vendors don't publish these.
- For ferrite Y30 and AlNiCo 5, pull Arnold ferrite + AlNiCo PDFs
  or IEC 60404 standard documents to restore those materials.
- For SmCo, add high-temp / temperature-stabilized variants (Recoma HT,
  Recoma STAB) and the other 2:17 grades (Recoma 30/32/33E/35E) for
  designers who want higher BHmax at the cost of slightly reduced HcJ
  headroom.
"""

from __future__ import annotations

from emergent_matter_materials.electromagnetic import Electromagnetic
from emergent_matter_materials.material import Material
from emergent_matter_materials.property_value import PropertyValue as _PV
from emergent_matter_materials.structural import Structural
from emergent_matter_materials.thermal import Thermal

_S_CATALOG_VERSION = "1.0.0"
_S_LAST_REVIEWED = "2026-06-17"

_ARNOLD_CAST_ALNICO_BROCHURE = (
    "Arnold Magnetic Technologies, 'Cast ALNICO Permanent Magnets' brochure (February "
    "2003, Rev. C), p.6.4 'Magnetic and Physical Properties (Typical Values)' table "
    "for Alnico 5, 5cc, 6 & ArKomax 800, and p.6.5 physical-properties table, Alnico 5 "
    "rows; retrieved 2026-09-17 from "
    "https://www.arnoldmagnetics.com/wp-content/uploads/2017/10/"
    "Cast-Alnico-Permanent-Magnet-Brochure-101117-1.pdf"
)
_ARNOLD_N35_SHEET = (
    "Arnold Magnetic Technologies, 'Sintered Neodymium-Iron-Boron Magnets: N35', "
    "single-grade datasheet Rev. 210607, p.1 nominal/min/max table and 'Other "
    "Properties' block, retrieved 2026-05-24 from "
    "https://www.arnoldmagnetics.com/wp-content/uploads/2017/11/N35-151021.pdf"
)
_ARNOLD_N42_SHEET = (
    "Arnold Magnetic Technologies, 'Sintered Neodymium-Iron-Boron Magnets: N42', "
    "single-grade datasheet Rev. 210607, p.1 nominal/min/max table and thermal "
    "properties block, retrieved 2026-05-24 from "
    "https://www.arnoldmagnetics.com/wp-content/uploads/2017/11/N42-151021.pdf"
)
_ARNOLD_N50_SHEET = (
    "Arnold Magnetic Technologies, 'Sintered Neodymium-Iron-Boron Magnets: N50', "
    "single-grade datasheet Rev. 210802, p.1 nominal/min/max table and 'Other "
    "Properties' block, retrieved 2026-05-24 from "
    "https://www.arnoldmagnetics.com/wp-content/uploads/2017/11/N50-151021.pdf"
)
_ARNOLD_CATALOG = (
    "Arnold Magnetic Technologies, 'Neodymium-Iron-Boron Magnet Grades: Summary "
    "Product List & Reference Guide', catalog Rev. 181031, pp.1-4 grade tables "
    "and pp.7/10/13 per-grade 'Other Properties' blocks, retrieved 2026-05-24 from "
    "https://www.arnoldmagnetics.com/wp-content/uploads/2017/10/Catalog-151021.pdf"
)
_ARNOLD_N42SH_SHEET = (
    "Arnold Magnetic Technologies, 'Sintered Neodymium-Iron-Boron Magnets: N42SH', "
    "single-grade datasheet Rev. 020821, retrieved 2026-05-24 from "
    "https://www.arnoldmagnetics.com/wp-content/uploads/2017/11/N42SH-151021.pdf"
)
_ARNOLD_N42UH_SHEET = (
    "Arnold Magnetic Technologies, 'Sintered Neodymium-Iron-Boron Magnets: N42UH', "
    "single-grade datasheet Rev. 210607, retrieved 2026-05-24 from "
    "https://www.arnoldmagnetics.com/wp-content/uploads/2017/11/N42UH-151021.pdf"
)
_ARNOLD_N42EH_SHEET = (
    "Arnold Magnetic Technologies, 'Sintered Neodymium-Iron-Boron Magnets: N42EH', "
    "single-grade datasheet Rev. 151021a, retrieved 2026-05-24 from "
    "https://www.arnoldmagnetics.com/wp-content/uploads/2017/11/N42EH-151021.pdf"
)
_ARNOLD_RECOMA_CATALOG = (
    "Arnold Magnetic Technologies, 'Recoma: The complete range of SmCo5 and Sm2Co17 "
    "alloys', combined product catalog 'Recoma-Combined-160301.pdf', summary-table page "
    "Rev. 160205a (p.2 grade table; covers Recoma 18-35E), retrieved 2026-05-24 from "
    "https://www.arnoldmagnetics.com/wp-content/uploads/2017/10/Recoma-Combined-160301.pdf"
)
_ARNOLD_RECOMA_28_PAGE = (
    "Arnold Magnetic Technologies, 'Recoma 28: Sintered Sm2Co17', per-grade page in "
    "the Recoma combined catalog 'Recoma-Combined-160301.pdf', page rev. 131025 "
    "(magnetic/thermal/'Other Properties' tables for Recoma 28 specifically), "
    "retrieved 2026-05-24 from "
    "https://www.arnoldmagnetics.com/wp-content/uploads/2017/10/Recoma-Combined-160301.pdf"
)

# ── v1.1.0 recoil-permeability sources ─────────────────────────────────────
#
# IEC 60404-8-1 is the international standard defining the symbol μ_rec
# and the unit (dimensionless), plus treating μ_rec as an "additional
# magnetic property" alongside Br/HcB/HcJ/(BH)max. The standard's typical-
# value tables for RE-Co and RE-Fe-B families are paywalled past the
# public preview, so IEC is used here as the DEFINITION source (cited in
# s_notes), not the VALUE source.
#
# Arnold's SMMA 2004 conference presentation 'NdFeB for High-Temperature
# Motor Applications' (Constantinides & Gulick) is the Tier-1 manufacturer
# literature source for the NdFeB family-level value 1.05. Arnold is the
# manufacturer and publishes this as design guidance for motor designers;
# treated as confidence='datasheet' under the same rule that places the
# Arnold per-grade PDFs at datasheet confidence.
#
# Shin-Etsu per-grade NdFeB and SmCo datasheets are direct vendor TDSes
# that publish 'Recoil Permeability μr [-]' as a scalar row on each
# product sheet. Shin-Etsu sheets are at confidence='datasheet'.
_IEC_60404_8_1 = (
    "IEC 60404-8-1, 'Magnetic materials - Part 8-1: Specifications for "
    "individual materials - Magnetically hard materials': defines recoil "
    "permeability μ_rec (dimensionless, symbol μ_rec) as the mean slope "
    "ΔB/ΔH of the recoil line on the second-quadrant B-H curve. Treated "
    "as an 'additional magnetic property' alongside Br / HcB / HcJ / "
    "(BH)max in the standard's per-family tables (public preview shows "
    "the field's existence but exact value tables are paywalled)"
)
_ARNOLD_NDFEB_HIGH_TEMP_PAPER = (
    "Arnold Magnetic Technologies, 'NdFeB for High-Temperature Motor "
    "Applications' (Steve Constantinides with Dale Gulick, SMMA Fall "
    "Technical Conference, November 3-5, 2004), retrieved 2026-05-29, "
    "re-fetched and verified against the PDF 2026-06-10, from "
    "https://www.arnoldmagnetics.com/wp-content/uploads/2017/10/"
    "NdFeB-for-high-temperature-motor-applications.pdf: slide 13 "
    "('Permeance Coefficient, Pc'): 'Typical values of μr for NdFeB "
    "are 1.05'; slide-13 speaker notes broaden: 'Typical values of "
    "Recoil Permeability are about 1.05 for sintered Ferrite, SmCo and "
    "NdFeB. ... Bonded Neo magnets range from about 1.1 to 1.7, "
    "depending upon grade.' (v1.3.1 citation fix: v1.1.0 wrote 'SMMA "
    "2004 Spring Conference'; the title page says Fall Technical "
    "Conference, November 3-5, 2004.)"
)
_SHINETSU_N50_SHEET = (
    "Shin-Etsu Chemical Co., 'N50' Nd-Fe-B Magnet single-grade datasheet "
    "(English; sheet footer: 'contents effective as of April 2016'), "
    "retrieved 2026-05-29, re-fetched and verified against the PDF "
    "2026-06-10, from "
    "https://www.shinetsu.co.jp/serem/e/download/N50sheet.pdf, "
    "page-2 'Standard Characteristics' table: 'Recoil Permeability "
    "μr [-] = 1.05' (page 1 is the demag-curve chart; footer notes "
    "'This product is manufactured under the license from Hitachi "
    "Metals, Ltd.')"
)
_SHINETSU_N52_SHEET = (
    "Shin-Etsu Chemical Co., 'N52' Nd-Fe-B Magnet single-grade datasheet "
    "(English; sheet footer: 'contents effective as of April 2018'), "
    "retrieved 2026-05-29, re-fetched and verified against the PDF "
    "2026-06-10, from "
    "https://www.shinetsu.co.jp/serem/e/download/N52sheet.pdf, "
    "page-2 'Standard Characteristics' table: 'Recoil Permeability "
    "μr [-] = 1.05' (page 1 is the demag-curve chart)"
)
_SHINETSU_N42SH_R_SHEET = (
    "Shin-Etsu Chemical Co., 'N42SH-R' Nd-Fe-B Magnet single-grade "
    "datasheet (English; sheet footer: 'contents effective as of "
    "February 2019'), retrieved 2026-05-29, re-fetched and verified "
    "against the PDF 2026-06-10, from "
    "https://www.shinetsu.co.jp/serem/e/download/N42SH-Rsheet.pdf, "
    "page-2 'Standard Characteristics' table: 'Recoil Permeability "
    "μr [-] = 1.05'; HcJ >= 1671 kA/m (21 kOe) on the same table "
    "confirms SH-class coercivity. (v1.3.1 citation fix: v1.1.0 stored "
    "only the download-directory URL; exact document URL confirmed by "
    "fetch.)"
)
_SHINETSU_N47UH_GR_SHEET = (
    "Shin-Etsu Chemical Co., 'N47UH-GR' Nd-Fe-B Magnet single-grade "
    "datasheet (English; sheet footer: 'contents effective as of April "
    "2016'), retrieved 2026-05-29, re-fetched and verified against the "
    "PDF 2026-06-10, from "
    "https://www.shinetsu.co.jp/serem/e/download/N47UH-GRsheet.pdf, "
    "page-2 'Standard Characteristics' table: 'Recoil Permeability "
    "μr [-] = 1.05'; HcJ >= 1989 kA/m (25 kOe) on the same table "
    "confirms UH-class coercivity (UH-family per-grade exemplar)"
)
_SHINETSU_R32HS_SHEET = (
    "Shin-Etsu Chemical Co., 'R32HS' Sm-Co Magnet single-grade datasheet "
    "(English; sheet footer: 'contents effective as of April 2016'), "
    "retrieved 2026-05-29, re-fetched and verified against the PDF "
    "2026-06-10, from "
    "https://www.shinetsu.co.jp/serem/e/download/R32HSsheet.pdf, "
    "page-2 'Standard Characteristics' table: 'Recoil Permeability "
    "μr [-] = 1.02'. Representative high-energy Sm-Co grade: Br "
    "1.10-1.18 T, (BH)max 223-263 kJ/m³ (28-33 MGOe), Curie 820 °C: "
    "consistent with sintered Sm2Co17 high-energy alloys. (v1.3.1 "
    "citation fix: v1.1.0 cited the product-download page without the "
    "document URL; exact URL confirmed by fetch.)"
)


# ── v1.1.0 recoil-permeability builder ─────────────────────────────────────
# Centralizes the s_notes prose so every NdFeB grade carries the same
# definition citation + downstream-use context.


def _ndfeb_recoil_permeability(
    d_value: float,
    s_primary_source: str,
    s_corroborating_source: str,
    s_grade_condition: str,
) -> _PV:
    """Build a recoil_permeability PropertyValue for a sintered NdFeB grade.

    Args:
        d_value: μ_rec scalar (typically 1.05 for sintered NdFeB).
        s_primary_source: Tier-1 source string that directly publishes
            the value for this grade (or for the nearest exemplar where
            exact-grade Shin-Etsu sheets don't exist, the Arnold
            family-level paper).
        s_corroborating_source: Secondary Tier-1 source, typically the
            other side of the family/per-grade pair.
        s_grade_condition: s_condition string for this specific grade
            (e.g. 'sintered NdFeB, plain' vs 'sintered NdFeB Dy-doped
            SH grade').
    """
    return _PV(
        d_value=d_value,
        s_units="",
        s_source=(f"{s_primary_source} || corroborated by {s_corroborating_source}"),
        s_condition=f"20 C, small-signal μ_rec, {s_grade_condition}",
        s_confidence="datasheet",
        s_notes=(
            "Recoil permeability μ_rec = (1/μ₀)·(dB/dH) is the small-"
            "signal slope of the recoil line on the 2nd-quadrant B-H "
            "demag curve. Definition source: " + _IEC_60404_8_1 + ". "
            "Arnold's measurement white paper notes the value depends "
            "slightly on the measurement start/end points; the catalog "
            "scalar represents the typical operating-point value used "
            "in motor-design literature. "
            ""
            "v1.1.0 (2026-05-29): field added to support downstream "
            "magnetostatic FEM ν = 1/(μ₀·μ_rec) per-region "
            "reluctivity for PM regions. The schema's "
            "relative_permeability slot stays None for hard magnets "
            "(N/A-by-physics; see module docstring 'Electromagnetic "
            "N/A-BY-PHYSICS for permanent magnets' block); μ_rec is "
            "the separately-defined small-signal PM permeability that "
            "the FEM solver actually needs. The two scalars are similar "
            "in magnitude but physically distinct quantities."
        ),
    )


def _smco_recoil_permeability(d_value: float, s_grade_condition: str) -> _PV:
    """SmCo recoil_permeability builder.

    SmCo μ_rec is more grade-dependent than NdFeB. Shin-Etsu R32HS is a
    representative high-energy Sm-Co per-grade datasheet that lists
    μr = 1.02; it is NOT the same exact grade as Arnold Recoma 28, but
    it is the closest publicly-tabulated Sm2Co17 high-energy sheet that
    lists μ_rec at all. Arnold's broader family statement gives ~1.05
    for sintered SmCo as a class. The catalog uses R32HS's 1.02 as a
    representative high-energy-class scalar, accepting ~5% uncertainty
    across the broader Sm2Co17 population.
    """
    return _PV(
        d_value=d_value,
        s_units="",
        s_source=(
            _SHINETSU_R32HS_SHEET
            + " || Arnold family-level reference: "
            + _ARNOLD_NDFEB_HIGH_TEMP_PAPER
        ),
        s_condition=f"20 C, small-signal μ_rec, {s_grade_condition}",
        s_confidence="datasheet",
        s_notes=(
            "Recoil permeability μ_rec = (1/μ₀)·(dB/dH); definition "
            "source: " + _IEC_60404_8_1 + ". "
            ""
            "SmCo μ_rec is more grade-dependent than NdFeB. Shin-Etsu "
            "R32HS publishes 1.02 for a representative high-energy "
            "Sm-Co grade; R32HS is NOT exactly the same grade as Arnold "
            "Recoma 28, but is the closest publicly-tabulated Sm2Co17 "
            "high-energy per-grade datasheet that lists μ_rec at all. "
            "Arnold's broader family statement gives ~1.05 for sintered "
            "SmCo as a class. The catalog stores R32HS's 1.02 as a "
            "REPRESENTATIVE high-energy-class scalar, not as an "
            "exact-grade match. Downstream FEM consumers using a single "
            "scalar should expect ~5% uncertainty across the broader "
            "Sm2Co17 population (1.02-1.10 is the realistic per-grade "
            "range documented in the open literature). "
            ""
            "v1.1.0 (2026-05-29): field added to support downstream "
            "magnetostatic FEM ν = 1/(μ₀·μ_rec) per-region "
            "reluctivity for PM regions."
        ),
    )


def _energy_product_max(
    d_nominal_kJ_m3: float,
    d_min_kJ_m3: float,
    d_nominal_MGOe: float,
    s_source_sheet: str,
    s_grade: str,
    d_max_kJ_m3: float | None = None,
) -> _PV:
    """(BH)max as published in the sheet's min / nominal / max table.

    Stored as the NOMINAL value in J/m^3 (the sheets publish kJ/m^3 and
    MGOe rows side by side); the published band goes in s_notes so a
    consumer sizing to a worst-case magnet can read it back. Never
    derived from Br x HcJ.
    """
    s_band = (
        f"min {d_min_kJ_m3:g}, max {d_max_kJ_m3:g} kJ/m3"
        if d_max_kJ_m3 is not None
        else f"min {d_min_kJ_m3:g} kJ/m3 (no max column published)"
    )
    return _PV(
        d_value=d_nominal_kJ_m3 * 1e3,
        s_units="J/m^3",
        s_source=s_source_sheet + " -- 'BHmax, Maximum Energy Product' row: nominal "
        f"{d_nominal_kJ_m3:g} kJ/m3 ({d_nominal_MGOe:g} MGOe); {s_band}",
        s_condition="20 C, nominal (sheet min/nominal/max table)",
        s_confidence="datasheet",
        s_notes=(
            f"{s_grade}: the grade number is the nominal (BH)max in MGOe "
            "(1 MGOe = 7.9577 kJ/m3). Nominal stored, matching the Br "
            "convention in this file."
        ),
    )


def _ndfeb_structural(s_source_sheet: str) -> Structural:
    """Sintered NdFeB structural: density + flexural strength at Tier 1.

    Two fields populate from the per-grade Arnold PDF (N35 Rev. 210607,
    N42 Rev. 210607, N50 Rev. 210802: confirmed v0.2.4 across all three
    per-grade PDFs):

    - ``density`` = 7.6 g/cm^3 (identical across N35/N42/N50)
    - ``ultimate_tensile`` = 285 MPa from "Flexural Strength" line in the
      "Other Properties" block (identical 41,300 psi / 285 MPa across
      N35/N42/N50, also identical across all 11 plain-grade pages in the
      Arnold catalog Rev. 181031). Stored in ``ultimate_tensile`` because
      flexural strength IS the brittle-fracture peak-stress scalar for
      sintered NdFeB: the schema's "fracture-mode" slot per
      ``Structural.__doc__``. The 3-point-bend test (ASTM C1161-class)
      typically yields slightly higher numbers than a hypothetical
      tensile test on the same brittle material; consumers using this
      for stress sizing must treat it as a fracture envelope, not a
      ductile yield. ``s_notes`` documents this convention.

    FLAGGED MISSING from Arnold sources (still TODO):
    - ``youngs_modulus``: Arnold publishes no elastic modulus.
      Handbook values cluster around 150-160 GPa but are not Tier 1.
    - ``poisson_ratio``: Arnold publishes no Poisson ratio.
      Handbook values ~0.24 but not Tier 1.
    - ``yield_stress``, NOT APPLICABLE for brittle sintered NdFeB; no
      0.2% offset yield exists for this material class.
    - ``fatigue_endurance``: Arnold publishes no fatigue data.
      NdFeB fatigue is unusual to publish; brittle materials don't have
      a clean Basquin-curve endurance limit. Stays None pending a
      measured study or peer-reviewed paper.

    Density and flexural strength are identical across N35/N42/N50 per
    Arnold per-grade PDFs (v0.2.4 verification 2026-05-24). The
    s_source_sheet parameter records which specific per-grade PDF
    provided the verification for that grade.
    """
    return Structural(
        flexural_strength=_PV(
            d_value=285e6,
            s_units="Pa",
            s_source=s_source_sheet + " -- 'Flexural Strength' in 'Other Properties' block: "
            "41,300 psi / 285 MPa (identical value also published "
            "in Arnold catalog Rev. 181031 on all 11 plain-grade "
            "pages for the sintered NdFeB family)",
            s_condition="20 C, sintered; 3-point bend test "
            "(ASTM C1161-class brittle-flexure method)",
            s_confidence="datasheet",
            s_notes=(
                "Sintered NdFeB is brittle: no ductile yield or tensile "
                "UTS exists. Arnold publishes ONLY flexural strength "
                "(no tensile UTS, no compressive strength, no yield). "
                "v0.3.0 (2026-05-24) moved this value from the "
                "ultimate_tensile slot to the new flexural_strength slot "
                "(the schema's brittle-fracture peak-stress field; see "
                "Structural module docstring). Flexural strength on "
                "brittle materials is typically 1.3-1.6x the equivalent "
                "tensile fracture stress because the bend specimen "
                "compresses out surface flaws on the tension side; use "
                "this value as a fracture envelope (σ_max < σ_flexural "
                "under bending), NOT as a ductile yield. For pure-tension "
                "stress states, derate ~30-40%. "
                ""
                "N/A-BY-PHYSICS CONVENTION (v0.6.0 documentation pass): "
                "sintered NdFeB is a brittle intermetallic: Nd2Fe14B "
                "polycrystalline aggregate sintered with a Nd-rich "
                "grain-boundary phase. Yield stress and ductile UTS are "
                "physically not applicable: the material fractures "
                "elastically with no plastic-yield region. Arnold "
                "publishes ONLY flexural strength (ASTM C1161 3-point "
                "bend), which IS the brittle-fracture peak-stress scalar "
                "stored here. The None values on Structural.youngs_modulus, "
                "poisson_ratio, yield_stress, ultimate_tensile, and "
                "fatigue_endurance reflect this physics, NOT a sourcing "
                "gap. (Aside: single-crystal C_ij measurements DO exist "
                "for Nd2Fe14B: Hirosawa, Tokuhara, Sagawa, Yamamoto, "
                "Fujimura 1986 J. Appl. Phys. 59(3):873, and an "
                "aggregate Voigt-Reuss-Hill polycrystalline E in the "
                "150-160 GPa range could be derived, but a derived value "
                "would carry confidence='derived' which the v0.2.0 "
                "Tier-1-only policy forbids. A peer-reviewed "
                "direct-measurement on sintered polycrystalline Nd-Fe-B "
                "would be Tier-1 acceptable if located.) Arnold also "
                "publishes Hardness Vickers (620 Hv) and α(HcJ) per "
                "grade; both now have their own slots (hardness_vickers, "
                "electromagnetic.temp_coeff_coercivity)."
            ),
        ),
        density=_PV(
            d_value=7600.0,
            s_units="kg/m^3",
            s_source=s_source_sheet + " -- density 7.6 g/cm^3",
            s_condition="20 C, sintered",
            s_confidence="datasheet",
        ),
        hardness_vickers=_PV(
            d_value=620.0,
            s_units="HV",
            s_source=s_source_sheet + " -- 'Other Properties' block: Hardness, Vickers = 620 Hv",
            s_condition="20 C, sintered",
            s_confidence="datasheet",
            s_notes=(
                "Identical 620 Hv on every sintered NdFeB grade, on both the "
                "per-grade standalone sheets and the combined catalog Rev. 181031 "
                "per-grade pages. Vickers hardness number (kgf/mm^2), stored "
                "unitless by convention."
            ),
        ),
    )


def _ndfeb_thermal_plain_grade(d_max_op_C: float, s_grade: str) -> Thermal:
    """Sintered NdFeB thermal properties from Arnold N42 PDF Rev. 210607
    + Arnold Catalog Rev. 181031 'Other Properties' blocks.

    Five fields populate: thermal_conductivity, max_operating_temp,
    curie_temp, thermal_expansion (all from per-grade PDF), and
    specific_heat (from catalog 'Other Properties' block: v0.2.2
    addition; v0.2.0 conclusion that this wasn't in Arnold sources
    was wrong; it's in catalog pp.7/10/13 per-grade tables).

    d_max_op_C varies by plain-grade temperature class (Tw column in
    Arnold catalog Rev. 181031); same plain-grade behavior across
    N35/N42/N50 (all = 80 C per the catalog table).
    """
    return Thermal(
        thermal_conductivity=_PV(
            d_value=6.7,
            s_units="W/(m*K)",
            s_source=_ARNOLD_N42_SHEET + " -- 5.8 kcal/(m*hr*degC) per the Arnold N42 "
            "standalone PDF Thermal Properties table "
            "(converted: 5.8 × 1.163 = 6.74 W/(m·K), "
            "rounded to 6.7 in the catalog).",
            s_condition="20 C",
            s_confidence="datasheet",
            s_notes=(
                "v0.7.5 REVERT: the v0.7.4 commit changed this to "
                "6.16 W/(m·K) on the reasoning that the standalone "
                "PDF's left column ('C //') was the parallel direction "
                "= 5.3 kcal = 6.16 W/(m·K), while the catalog's "
                "previous value 6.7 corresponded to the right column "
                "('C ⊥') = 5.8 kcal = 6.74. Reverted "
                "because (a) the parallel/perpendicular column-"
                "ordering convention has genuine ambiguity that "
                "cannot be independently verified without external "
                "literature, and (b) for motor thermal-dissipation "
                "calculations the relevant k direction is "
                "perpendicular to the easy axis (heat flows radially "
                "through the stator iron, NOT along the c-axis of "
                "the magnet). If the previous value 6.7 corresponds "
                "to the perpendicular direction, it's the more "
                "engineering-useful number anyway. The s_condition "
                "above is intentionally left unlabeled ('20 C' "
                "without parallel/perpendicular qualifier) until "
                "external literature or Arnold direct-confirmation "
                "resolves the column convention. The standalone PDF "
                "publishes 5.3 // 5.8 ⊥ kcal/(m·hr·°C); convert by "
                "× 1.163 if a directional value is required."
            ),
        ),
        specific_heat=_PV(
            d_value=460.0,
            s_units="J/(kg*K)",
            s_source=_ARNOLD_CATALOG + " -- 'Other Properties' block per-grade page lists "
            "Specific Heat = 460 J/(kg*K) (measured between 20-140 C). "
            "Identical across N35/N42/N50 plain grades. Cross-"
            "check: standalone Rev. 210607 publishes 0.11 cal/g·°C "
            "= 460.7 J/(kg·K), agrees within rounding.",
            s_condition="20-140 C, sintered",
            s_confidence="datasheet",
        ),
        max_operating_temp=_PV(
            d_value=d_max_op_C,
            s_units="C",
            s_source=_ARNOLD_CATALOG + f" -- Tw max column for {s_grade}",
            s_condition="continuous service, recoverable demagnetization",
            s_confidence="datasheet",
        ),
        curie_temp=_PV(
            d_value=310.0,
            s_units="C",
            s_source=_ARNOLD_N42_SHEET + " -- Tc = 310 C",
            s_confidence="datasheet",
        ),
        thermal_expansion=_PV(
            d_value=7.0e-6,
            s_units="1/K",
            s_source=_ARNOLD_N42_SHEET + " -- CTE 7 × 10⁻⁶ /°C in the 'C //' column of the "
            "standalone PDF Thermal Properties table; the 'C ⊥' "
            "column publishes -1 × 10⁻⁶ /°C. Per CTE physics for "
            "sintered NdFeB (inverse-magnetostriction effect "
            "→ slight negative CTE perpendicular to c-axis), "
            "the +7 in 'C //' is consistent with the parallel "
            "(easy-axis) direction.",
            s_condition="parallel to easy axis, 20-200 C",
            s_confidence="datasheet",
            s_notes=(
                "v0.7.5: value 7.0e-6 unchanged across the v0.7.3 → "
                "v0.7.4 → v0.7.5 history. The CTE direction convention "
                "is independently checkable against physics (sintered "
                "NdFeB has positive CTE parallel-to-easy-axis, slightly "
                "negative perpendicular) which agrees with the standalone "
                "PDF's 7 // -1 ⊥ ordering. So unlike the k value, the "
                "parallel/perpendicular labeling here is on solid "
                "ground."
            ),
        ),
        thermal_expansion_perpendicular=_PV(
            d_value=-1.0e-6,
            s_units="1/K",
            s_source=_ARNOLD_N42_SHEET + " -- CTE -1 × 10⁻⁶ /°C in the 'C ⊥' column of the "
            "standalone PDF Thermal Properties table (the N35 Rev. 210607 and N50 "
            "Rev. 210802 standalones publish the identical 7 // -1 ⊥ pair)",
            s_condition="perpendicular to easy axis, 20-200 C",
            s_confidence="datasheet",
            s_notes=(
                "Slightly NEGATIVE: sintered NdFeB contracts on heating "
                "perpendicular to the c-axis (inverse-magnetostriction effect). "
                "Source-of-record matches the parallel value above (same "
                "standalone sheet). The older combined catalog Rev. 181031 "
                "per-grade pages publish -0.1 × 10⁻⁶ /°C perpendicular (with "
                "7.5 parallel) for these grades: same tier, older revision, so "
                "the standalone wins per the source-priority rule. Rejected "
                "value recorded here, never averaged."
            ),
        ),
    )


def _ndfeb_high_temp_thermal(
    d_max_op_C: float,
    s_grade: str,
    s_source_sheet: str,
    d_density_kg_m3: float = 7600.0,
    d_k_W_mK: float = 6.7,
    d_CTE_per_K: float = 7.5e-6,
    d_CTE_perp_per_K: float = -0.1e-6,
) -> Thermal:
    """Sintered NdFeB thermal for the high-temp dysprosium-doped grades.

    Defaults preserve the v0.7.3 catalog values:
      k = 6.7 W/(m·K) (from 5.8 kcal × 1.163, see plain-grade helper
                       for the parallel/perpendicular column-ordering
                       discussion).
      CTE = 7.5 × 10⁻⁶/°C (from the older Arnold Catalog 151021a per-
                            grade page).

    N42EH overrides both parameters because its standalone PDF
    (Rev. 151021a) publishes k = 7.6 W/(m·K) single (no parallel/
    perpendicular split, no kcal units) and CTE = 7.5 × 10⁻⁶/°C
    (matches the helper default coincidentally, so the override is
    cosmetic for documentation).

    v0.7.5 REVERT: v0.7.4 had switched defaults to k=6.16 and
    CTE=7.0e-6 (from newer 2021 Arnold standalones). Reverted
    per parallel/perpendicular column-ordering concern (k specifically
    has genuine direction-convention ambiguity that affects which
    column value should be stored). See the plain helper s_notes for
    the full thermodynamics/physics rationale.
    """
    return Thermal(
        thermal_conductivity=_PV(
            d_value=d_k_W_mK,
            s_units="W/(m*K)",
            s_source=s_source_sheet + f" -- k = {d_k_W_mK} W/(m·K) from the per-grade "
            "PDF Physical Properties row. SH/UH default 6.7 "
            "matches 5.8 kcal/(m·hr·°C) × 1.163 = 6.74 (the "
            "value in the right-column of the standalone "
            "PDF; see v0.7.5 plain-helper s_notes for the "
            "parallel/perpendicular discussion). EH "
            "publishes 7.6 W/(m·K) single -- no kcal split.",
            s_condition="20 C",
            s_confidence="datasheet",
            s_notes=(
                "v0.7.5: see plain-grade thermal helper for the "
                "parallel/perpendicular column-ordering discussion. "
                "Default value 6.7 W/(m·K) preserves v0.7.3 catalog "
                "state, which is the engineering-relevant value for "
                "the perpendicular direction (heat dissipation "
                "through stator iron). N42EH override (7.6 W/(m·K)) "
                "stands because the EH standalone publishes a single "
                "isotropic value with no direction split."
            ),
        ),
        specific_heat=_PV(
            d_value=460.0,
            s_units="J/(kg*K)",
            s_source=_ARNOLD_CATALOG + f" -- per-grade 'Other Properties' block for {s_grade}, "
            "same value as plain N42 (sintered NdFeB family). "
            "Cross-check: standalone Rev. 020821/210607/151021a "
            "publishes 0.11 cal/g·°C = 460.7 J/(kg·K).",
            s_condition="20-140 C, sintered",
            s_confidence="datasheet",
        ),
        max_operating_temp=_PV(
            d_value=d_max_op_C,
            s_units="C",
            s_source=_ARNOLD_CATALOG + f" -- Tw max column for {s_grade}",
            s_condition="continuous service, recoverable demagnetization",
            s_confidence="datasheet",
        ),
        curie_temp=_PV(
            d_value=310.0,
            s_units="C",
            s_source=s_source_sheet + " -- Tc = 310 C (per-grade PDF)",
            s_confidence="datasheet",
        ),
        thermal_expansion=_PV(
            d_value=d_CTE_per_K,
            s_units="1/K",
            s_source=_ARNOLD_CATALOG + f" -- CTE = {d_CTE_per_K * 1e6:.1f} × 10⁻⁶/°C "
            "parallel-to-c-axis per the Catalog 151021a per-"
            "grade page for SH/UH (= 7.5e-6). Newer 2021 "
            "standalones publish 7e-6 // for SH/UH (slight "
            "value drift between Arnold publications -- see "
            "v0.7.5 changelog for the cross-source decision "
            "rationale). N42EH publishes 7.5 × 10⁻⁶/°C in "
            "its own standalone -- matches the default.",
            s_condition="parallel to easy axis, 20-200 C",
            s_confidence="datasheet",
            s_notes=(
                "v0.7.5 REVERT: v0.7.4 had switched SH/UH CTE to "
                "7.0e-6 (newer standalones); reverted to 7.5e-6 "
                "(older Catalog 151021a) for consistency with the k "
                "revert (same older-Catalog-vs-newer-Standalone "
                "decision). The 7% difference between 7.5 and 7.0 "
                "is within the typical batch-to-batch variation for "
                "sintered NdFeB. N42EH stays at 7.5e-6 because its "
                "own standalone publishes that value."
            ),
        ),
        thermal_expansion_perpendicular=_PV(
            d_value=d_CTE_perp_per_K,
            s_units="1/K",
            s_source=_ARNOLD_CATALOG + f" -- CTE = {d_CTE_perp_per_K * 1e6:.1f} × 10⁻⁶/°C "
            "perpendicular-to-c-axis per the Catalog Rev. 181031 per-grade page "
            "(same source-of-record as the parallel value above)",
            s_condition="perpendicular to easy axis, 20-200 C",
            s_confidence="datasheet",
            s_notes=(
                "Source-of-record follows the parallel CTE above (Catalog Rev. "
                "181031, per the v0.7.5 cross-source decision). The newer "
                "standalone sheets for N42SH (Rev. 020821) and N42UH (Rev. "
                "210607) publish -1 × 10⁻⁶ /°C perpendicular with 7 parallel; "
                "the N42EH standalone (Rev. 151021a) agrees with the catalog at "
                "-0.1 / 7.5. Rejected values recorded here, never averaged."
            ),
        ),
    )


def _ndfeb_high_temp_structural(
    d_density_kg_m3: float = 7600.0, s_source_sheet: str = ""
) -> Structural:
    """High-temp sintered NdFeB structural.

    Two fields populate from the per-grade Arnold PDF for the SH/UH/EH
    high-temp variants (v0.2.4 verification pass 2026-05-24):

    - ``density``: varies slightly between SH/UH (7.6 g/cc) and EH (7.5 g/cc).
    - ``flexural_strength`` = 285 MPa from "Flexural Strength" line in the
      "Other Properties" block (identical 41,300 psi / 285 MPa across all
      Arnold sintered NdFeB grades: plain, M, H, SH, UH, EH). Stored in
      the v0.3.0 ``flexural_strength`` slot (was ``ultimate_tensile`` in
      v0.2.4-v0.2.8 before the schema clarification).

    Young's modulus, Poisson ratio, yield stress, ultimate tensile,
    fatigue endurance: NOT in Arnold sources, stay None. See
    ``_ndfeb_structural`` docstring for full flagging notes.
    """
    return Structural(
        flexural_strength=_PV(
            d_value=285e6,
            s_units="Pa",
            s_source=s_source_sheet + " -- 'Flexural Strength' in 'Other Properties' block: "
            "41,300 psi / 285 MPa (identical value across all "
            "sintered NdFeB grades in Arnold catalog Rev. 181031)",
            s_condition="20 C, sintered; 3-point bend test "
            "(ASTM C1161-class brittle-flexure method)",
            s_confidence="datasheet",
            s_notes=(
                "Brittle-fracture flexural strength, NOT ductile UTS. "
                "Treat as a fracture envelope, not a yield. For "
                "pure-tension stress states, derate ~30-40%. See "
                "_ndfeb_structural() docstring for the full convention. "
                "v0.3.0 moved from ultimate_tensile slot to "
                "flexural_strength slot. "
                ""
                "N/A-BY-PHYSICS CONVENTION (v0.6.0 documentation pass): "
                "sintered NdFeB is a brittle intermetallic: Nd2Fe14B "
                "polycrystalline aggregate (Dy-doped on SH/UH/EH grades) "
                "with a rare-earth-rich grain-boundary phase. Yield "
                "stress and ductile UTS are physically not applicable: "
                "the material fractures elastically with no plastic "
                "yield region. Arnold publishes ONLY flexural strength "
                "(ASTM C1161 3-point bend), which IS the brittle-"
                "fracture peak-stress scalar stored here. The None "
                "values on Structural.youngs_modulus, poisson_ratio, "
                "yield_stress, ultimate_tensile, and fatigue_endurance "
                "reflect this physics, NOT a sourcing gap. Single-"
                "crystal C_ij DO exist for Nd2Fe14B (Hirosawa et al. "
                "1986 J. Appl. Phys. 59:873) and an aggregate Voigt-"
                "Reuss-Hill E ~150-160 GPa could be derived, but a "
                "derived value would carry confidence='derived' which "
                "the v0.2.0 Tier-1-only policy forbids."
            ),
        ),
        density=_PV(
            d_value=d_density_kg_m3,
            s_units="kg/m^3",
            s_source=s_source_sheet + f" -- density {d_density_kg_m3 / 1000} g/cm^3",
            s_condition="20 C, sintered",
            s_confidence="datasheet",
        ),
        hardness_vickers=_PV(
            d_value=620.0,
            s_units="HV",
            s_source=s_source_sheet + " -- 'Other Properties' block: Hardness, Vickers = 620 Hv",
            s_condition="20 C, sintered",
            s_confidence="datasheet",
            s_notes=(
                "Identical 620 Hv on every sintered NdFeB grade, on both the "
                "per-grade standalone sheets and the combined catalog Rev. 181031 "
                "per-grade pages. Vickers hardness number (kgf/mm^2), stored "
                "unitless by convention."
            ),
        ),
    )


# ── NdFeB N35 ──────────────────────────────────────────────────────────────

ndfeb_n35 = Material(
    s_id="ndfeb_n35",
    s_description="Sintered NdFeB permanent magnet, grade N35",
    s_category="magnet",
    s_specification="Sintered NdFeB N35 (Arnold catalog N35, equiv. Hitachi NEOMAX-35 etc.)",
    s_catalog_version=_S_CATALOG_VERSION,
    s_last_reviewed=_S_LAST_REVIEWED,
    structural=_ndfeb_structural(s_source_sheet=_ARNOLD_N35_SHEET),
    electromagnetic=Electromagnetic(
        energy_product_max=_energy_product_max(
            d_nominal_kJ_m3=283,
            d_min_kJ_m3=263,
            d_max_kJ_m3=302,
            d_nominal_MGOe=36,
            s_source_sheet=_ARNOLD_N35_SHEET,
            s_grade="N35",
        ),
        remanence=_PV(
            d_value=1.21,
            s_units="T",
            s_source=_ARNOLD_CATALOG + " -- N35 typical Br = 1210 mT",
            s_condition="20 C, typical",
            s_confidence="datasheet",
            s_notes=(
                "B_r is the EM magnetization scalar for a permanent "
                "magnet (the schema's saturation_flux slot is "
                "N/A-by-physics for hard magnets; see module docstring "
                "Electromagnetic N/A section). Arnold also publishes "
                "BHmax (N35 = 35 MGOe = 279 kJ/m³) and α(HcJ) per "
                "grade, but v0.6.0 has no schema slot for either; "
                "deferred to v0.8.0+ (see module docstring 'Schema "
                "expansion candidates')."
            ),
        ),
        coercivity=_PV(
            d_value=955e3,
            s_units="A/m",
            s_source=_ARNOLD_CATALOG + " -- N35 min HcJ (intrinsic) = 955 kA/m",
            s_condition="20 C, intrinsic coercivity HcJ (min value)",
            s_confidence="datasheet",
            s_notes=(
                "HcJ (intrinsic) is the demag-margin-relevant coercivity "
                "scalar: what guarantees the magnet doesn't lose "
                "magnetization under an opposing field. Arnold also "
                "publishes HcB (regular coercivity) but v0.6.0 schema's "
                "coercivity slot stores HcJ by convention. The grade's "
                "temperature coefficient of intrinsic coercivity "
                "α(HcJ) = -0.62 %/°C is published per grade but has no "
                "schema slot (only α(B_r) is currently exposed via "
                "temp_coeff_remanence). See module docstring."
            ),
        ),
        temp_coeff_remanence=_PV(
            d_value=-1.2e-3,
            s_units="1/K",
            s_source=_ARNOLD_CATALOG + " -- alpha(Br) = -0.12 %/degC",
            s_condition="measured 20-80 C",
            s_confidence="datasheet",
        ),
        temp_coeff_coercivity=_PV(
            d_value=-6.2e-3,
            s_units="1/K",
            s_source=_ARNOLD_N35_SHEET + " -- Reversible Temperature Coefficient of Coercivity "
            "α(HcJ) = -0.62 %/°C, measured 20-80 °C (N35 standalone "
            "PDF Rev. 210607, 'Reversible Temperature Coefficients' "
            "block). Read directly from the Arnold PDF in the v1.8.0 "
            "source-verification pass (NOT from prior docstring "
            "narrative). Cross-check: Shin-Etsu plain-grade sheets "
            "α(HcJ) ≈ -0.61 to -0.64 %/K (N52 / N50).",
            s_condition="reversible α(HcJ), measured 20-80 C, intrinsic coercivity HcJ",
            s_confidence="datasheet",
            s_notes=(
                "Demag-margin-vs-temperature scalar: HcJ falls ~5x faster "
                "with temperature than Br (α(HcJ)=-0.62 vs α(Br)=-0.12 %/°C), "
                "so a motor's worst-case demag check at peak operating "
                "temperature is governed by this, not α(Br). The 20-80 °C "
                "range matches the plain-grade max operating temperature."
            ),
        ),
        resistivity_at_20C=_PV(
            d_value=1.5e-6,
            s_units="Ohm*m",
            s_source=_ARNOLD_N35_SHEET + " -- Electrical Resistivity = 150 // 130 µΩ·cm "
            "(parallel to easy axis // perpendicular) per the "
            "Arnold N35 standalone PDF Rev. 210607 'Other "
            "Properties' row. Stored parallel-direction value "
            "150 µΩ·cm = 1.5e-6 Ω·m.",
            s_condition="parallel to easy axis, 20 C",
            s_confidence="datasheet",
            s_notes=(
                "v0.7.4 ADDED: earlier passes (v0.2.x through v0.7.2) "
                "wrongly concluded the Arnold per-grade resistivity "
                "cells were blank. v0.7.3 manual verification confirmed "
                "Rev. 210607 publishes 150 µΩ·cm parallel and 130 µΩ·cm "
                "perpendicular. Stored parallel direction here; "
                "perpendicular = 130 µΩ·cm = 1.3e-6 Ω·m if needed. "
                "Eddy-current loss models for NdFeB rotor segments "
                "depend on this value."
            ),
        ),
        # μ_rec: Arnold family-typical value (no Shin-Etsu exact-N35
        # sheet exists publicly; Shin-Etsu per-grade sheets in the lineup
        # corroborate 1.05 across all sintered NdFeB grades they DO
        # publish).
        recoil_permeability=_ndfeb_recoil_permeability(
            d_value=1.05,
            s_primary_source=_ARNOLD_NDFEB_HIGH_TEMP_PAPER,
            s_corroborating_source=(_SHINETSU_N50_SHEET + " (sintered-NdFeB family corroboration)"),
            s_grade_condition="sintered NdFeB, plain N35 grade "
            "(Arnold family-typical + Shin-Etsu N50 "
            "corroboration; no exact-grade Shin-Etsu "
            "N35 sheet)",
        ),
    ),
    thermal=_ndfeb_thermal_plain_grade(d_max_op_C=80.0, s_grade="N35"),
)


# ── NdFeB N42 ──────────────────────────────────────────────────────────────

ndfeb_n42 = Material(
    s_id="ndfeb_n42",
    s_description="Sintered NdFeB permanent magnet, grade N42",
    s_category="magnet",
    s_specification="Sintered NdFeB N42 (Arnold catalog N42, equiv. Hitachi NEOMAX-42 etc.)",
    s_catalog_version=_S_CATALOG_VERSION,
    s_last_reviewed=_S_LAST_REVIEWED,
    structural=_ndfeb_structural(s_source_sheet=_ARNOLD_N42_SHEET),
    electromagnetic=Electromagnetic(
        energy_product_max=_energy_product_max(
            d_nominal_kJ_m3=334,
            d_min_kJ_m3=318,
            d_max_kJ_m3=350,
            d_nominal_MGOe=42,
            s_source_sheet=_ARNOLD_N42_SHEET,
            s_grade="N42",
        ),
        remanence=_PV(
            d_value=1.315,
            s_units="T",
            s_source=_ARNOLD_N42_SHEET + " -- Br typical = 13,150 G = 1.315 T",
            s_condition="20 C, typical",
            s_confidence="datasheet",
        ),
        coercivity=_PV(
            d_value=955e3,
            s_units="A/m",
            s_source=_ARNOLD_N42_SHEET + " -- HcJ (intrinsic) min = 955 kA/m = 12,000 Oe",
            s_condition="20 C, intrinsic coercivity HcJ (min)",
            s_confidence="datasheet",
        ),
        temp_coeff_remanence=_PV(
            d_value=-1.2e-3,
            s_units="1/K",
            s_source=_ARNOLD_N42_SHEET + " -- alpha(Br) = -0.12 %/degC",
            s_condition="20-80 C",
            s_confidence="datasheet",
        ),
        temp_coeff_coercivity=_PV(
            d_value=-6.2e-3,
            s_units="1/K",
            s_source=_ARNOLD_N42_SHEET + " -- Reversible Temperature Coefficient of Coercivity "
            "α(HcJ) = -0.62 %/°C, measured 20-80 °C (N42 standalone "
            "PDF Rev. 210607, 'Reversible Temperature Coefficients' "
            "block). Read directly from the Arnold PDF in the v1.8.0 "
            "source-verification pass. Cross-check: Shin-Etsu N52 "
            "sheet α(HcJ) = -0.61 %/K.",
            s_condition="reversible α(HcJ), measured 20-80 C, intrinsic coercivity HcJ",
            s_confidence="datasheet",
            s_notes=(
                "HcJ falls ~5x faster with temperature than Br "
                "(α(HcJ)=-0.62 vs α(Br)=-0.12 %/°C): the demag-margin "
                "driver for motor design at elevated temperature."
            ),
        ),
        resistivity_at_20C=_PV(
            d_value=1.5e-6,
            s_units="Ohm*m",
            s_source=_ARNOLD_N42_SHEET + " -- Electrical Resistivity = 150 // 130 µΩ·cm "
            "(parallel to easy axis // perpendicular) per the "
            "Arnold N42 standalone PDF Rev. 210607.",
            s_condition="parallel to easy axis, 20 C",
            s_confidence="datasheet",
            s_notes="v0.7.4 ADDED: 150 µΩ·cm = 1.5e-6 Ω·m parallel.",
        ),
        # μ_rec: Arnold family-typical value; Shin-Etsu N52 sheet (closest
        # plain-grade neighbor with public per-grade sheet) corroborates.
        # No exact-grade Shin-Etsu N42 sheet exists publicly.
        recoil_permeability=_ndfeb_recoil_permeability(
            d_value=1.05,
            s_primary_source=_ARNOLD_NDFEB_HIGH_TEMP_PAPER,
            s_corroborating_source=(_SHINETSU_N52_SHEET + " (plain-grade family neighbor)"),
            s_grade_condition="sintered NdFeB, plain N42 grade "
            "(Arnold family-typical + Shin-Etsu N52 "
            "corroboration; no exact-grade Shin-Etsu "
            "N42 sheet)",
        ),
    ),
    thermal=_ndfeb_thermal_plain_grade(d_max_op_C=80.0, s_grade="N42"),
)


# ── NdFeB N50 ──────────────────────────────────────────────────────────────

ndfeb_n50 = Material(
    s_id="ndfeb_n50",
    s_description="Sintered NdFeB permanent magnet, grade N50",
    s_category="magnet",
    s_specification="Sintered NdFeB N50 (Arnold catalog N50, equiv. Hitachi NEOMAX-50 etc.)",
    s_catalog_version=_S_CATALOG_VERSION,
    s_last_reviewed=_S_LAST_REVIEWED,
    structural=_ndfeb_structural(s_source_sheet=_ARNOLD_N50_SHEET),
    electromagnetic=Electromagnetic(
        energy_product_max=_energy_product_max(
            d_nominal_kJ_m3=390,
            d_min_kJ_m3=374,
            d_max_kJ_m3=406,
            d_nominal_MGOe=49,
            s_source_sheet=_ARNOLD_N50_SHEET,
            s_grade="N50",
        ),
        remanence=_PV(
            d_value=1.425,
            s_units="T",
            s_source=_ARNOLD_CATALOG + " -- N50 typical Br = 14250 G = 1.425 T",
            s_condition="20 C, typical",
            s_confidence="datasheet",
        ),
        coercivity=_PV(
            d_value=875e3,
            s_units="A/m",
            s_source=_ARNOLD_CATALOG + " -- N50 min HcJ (intrinsic) = 875 kA/m",
            s_condition="20 C, intrinsic coercivity HcJ (min)",
            s_confidence="datasheet",
        ),
        temp_coeff_remanence=_PV(
            d_value=-1.2e-3,
            s_units="1/K",
            s_source=_ARNOLD_CATALOG + " -- alpha(Br) = -0.12 %/degC",
            s_confidence="datasheet",
        ),
        temp_coeff_coercivity=_PV(
            d_value=-6.2e-3,
            s_units="1/K",
            s_source=_ARNOLD_N50_SHEET + " -- Reversible Temperature Coefficient of Coercivity "
            "α(HcJ) = -0.62 %/°C, measured 20-80 °C (N50 standalone "
            "PDF Rev. 210802, 'Reversible Temperature Coefficients' "
            "block). Read directly from the Arnold PDF in the v1.8.0 "
            "source-verification pass. Cross-check: Shin-Etsu N50 "
            "sheet α(HcJ) = -0.64 %/K.",
            s_condition="reversible α(HcJ), measured 20-80 C, intrinsic coercivity HcJ",
            s_confidence="datasheet",
            s_notes=(
                "HcJ falls ~5x faster with temperature than Br "
                "(α(HcJ)=-0.62 vs α(Br)=-0.12 %/°C): the demag-margin "
                "driver for motor design at elevated temperature."
            ),
        ),
        resistivity_at_20C=_PV(
            d_value=1.5e-6,
            s_units="Ohm*m",
            s_source=_ARNOLD_N50_SHEET + " -- Electrical Resistivity = 150 // 130 µΩ·cm "
            "(parallel // perpendicular) per the Arnold N50 "
            "standalone PDF.",
            s_condition="parallel to easy axis, 20 C",
            s_confidence="datasheet",
            s_notes="v0.7.4 ADDED: 150 µΩ·cm = 1.5e-6 Ω·m parallel.",
        ),
        # μ_rec: direct per-grade match (this is the only NdFeB grade in
        # the catalog with a 1:1 Shin-Etsu sheet): Shin-Etsu N50 sheet
        # primary. Arnold family-level paper corroborates the broader
        # sintered-NdFeB scalar.
        recoil_permeability=_ndfeb_recoil_permeability(
            d_value=1.05,
            s_primary_source=_SHINETSU_N50_SHEET,
            s_corroborating_source=_ARNOLD_NDFEB_HIGH_TEMP_PAPER,
            s_grade_condition="sintered NdFeB, plain N50 grade "
            "(direct Shin-Etsu N50 per-grade match)",
        ),
    ),
    thermal=_ndfeb_thermal_plain_grade(d_max_op_C=80.0, s_grade="N50"),
)


# ── NdFeB N42SH (high-temp, Dy-doped, Tw=150°C) ───────────────────────────

ndfeb_n42sh = Material(
    s_id="ndfeb_n42sh",
    s_description="Sintered NdFeB high-temp permanent magnet, grade N42SH (Tw=150 C)",
    s_category="magnet",
    s_specification=(
        "Sintered NdFeB N42SH (dysprosium-doped variant for elevated-"
        "temperature continuous service, Arnold catalog N42SH)"
    ),
    s_catalog_version=_S_CATALOG_VERSION,
    s_last_reviewed=_S_LAST_REVIEWED,
    structural=_ndfeb_high_temp_structural(
        d_density_kg_m3=7600.0,
        s_source_sheet=_ARNOLD_N42SH_SHEET,
    ),
    electromagnetic=Electromagnetic(
        energy_product_max=_energy_product_max(
            d_nominal_kJ_m3=330,
            d_min_kJ_m3=310,
            d_max_kJ_m3=350,
            d_nominal_MGOe=42,
            s_source_sheet=_ARNOLD_N42SH_SHEET,
            s_grade="N42SH",
        ),
        remanence=_PV(
            d_value=1.310,
            s_units="T",
            s_source=_ARNOLD_N42SH_SHEET
            + " -- Br typical = 13,100 G = 1.310 T (range 12,800-13,400 G)",
            s_condition="20 C, typical",
            s_confidence="datasheet",
        ),
        coercivity=_PV(
            d_value=1592e3,
            s_units="A/m",
            s_source=_ARNOLD_N42SH_SHEET + " -- HcJ (intrinsic) min = 1592 kA/m = 20,000 Oe",
            s_condition="20 C, intrinsic coercivity HcJ (min)",
            s_confidence="datasheet",
        ),
        temp_coeff_remanence=_PV(
            d_value=-1.2e-3,
            s_units="1/K",
            s_source=_ARNOLD_N42SH_SHEET + " -- alpha(Br) = -0.12 %/degC (20-150 C)",
            s_confidence="datasheet",
        ),
        temp_coeff_coercivity=_PV(
            d_value=-5.5e-3,
            s_units="1/K",
            s_source=_ARNOLD_N42SH_SHEET + " -- Reversible Temperature Coefficient of Coercivity "
            "α(HcJ) = -0.55 %/°C, measured 20-150 °C (N42SH "
            "standalone PDF Rev. 020821). Read directly from the "
            "Arnold PDF in the v1.8.0 source-verification pass. "
            "Cross-check: Shin-Etsu N42SH-R sheet α(HcJ) = "
            "-0.54 %/K.",
            s_condition="reversible α(HcJ), measured 20-150 C, intrinsic coercivity HcJ",
            s_confidence="datasheet",
            s_notes=(
                "SH grade: α(HcJ)=-0.55 %/°C, less negative than plain "
                "NdFeB (-0.62): the Dy doping that raises HcJ also "
                "improves its thermal stability. Measured over the wider "
                "20-150 °C SH service range."
            ),
        ),
        resistivity_at_20C=_PV(
            d_value=1.5e-6,
            s_units="Ohm*m",
            s_source=_ARNOLD_N42SH_SHEET + " -- Electrical Resistivity = 150 // 130 µΩ·cm "
            "(parallel // perpendicular) per the N42SH "
            "standalone PDF Rev. 020821.",
            s_condition="parallel to easy axis, 20 C",
            s_confidence="datasheet",
            s_notes="v0.7.4 ADDED: 150 µΩ·cm = 1.5e-6 Ω·m parallel.",
        ),
        # μ_rec, direct/near-direct per-grade match: Shin-Etsu N42SH-R
        # sheet primary ("-R" is a Shin-Etsu commercial suffix on the
        # SH grade family, equivalent in datasheet specification). Arnold
        # family-level paper corroborates the broader sintered-NdFeB
        # scalar.
        recoil_permeability=_ndfeb_recoil_permeability(
            d_value=1.05,
            s_primary_source=_SHINETSU_N42SH_R_SHEET,
            s_corroborating_source=_ARNOLD_NDFEB_HIGH_TEMP_PAPER,
            s_grade_condition="sintered NdFeB Dy-doped SH grade "
            "(direct/near-direct Shin-Etsu N42SH-R "
            "per-grade match)",
        ),
    ),
    thermal=_ndfeb_high_temp_thermal(
        d_max_op_C=150.0,
        s_grade="N42SH",
        s_source_sheet=_ARNOLD_N42SH_SHEET,
    ),
)


# ── NdFeB N42UH (ultra-high-temp, Tw=180°C) ───────────────────────────────

ndfeb_n42uh = Material(
    s_id="ndfeb_n42uh",
    s_description="Sintered NdFeB ultra-high-temp permanent magnet, grade N42UH (Tw=180 C)",
    s_category="magnet",
    s_specification="Sintered NdFeB N42UH (Arnold catalog N42UH)",
    s_catalog_version=_S_CATALOG_VERSION,
    s_last_reviewed=_S_LAST_REVIEWED,
    structural=_ndfeb_high_temp_structural(
        d_density_kg_m3=7600.0,
        s_source_sheet=_ARNOLD_N42UH_SHEET,
    ),
    electromagnetic=Electromagnetic(
        energy_product_max=_energy_product_max(
            d_nominal_kJ_m3=330,
            d_min_kJ_m3=310,
            d_max_kJ_m3=350,
            d_nominal_MGOe=42,
            s_source_sheet=_ARNOLD_N42UH_SHEET,
            s_grade="N42UH",
        ),
        remanence=_PV(
            d_value=1.310,
            s_units="T",
            s_source=_ARNOLD_N42UH_SHEET + " -- Br typical = 13,100 G = 1.310 T",
            s_condition="20 C, typical",
            s_confidence="datasheet",
        ),
        coercivity=_PV(
            d_value=1990e3,
            s_units="A/m",
            s_source=_ARNOLD_N42UH_SHEET + " -- HcJ (intrinsic) min = 1990 kA/m = 25,000 Oe",
            s_condition="20 C, intrinsic coercivity HcJ (min)",
            s_confidence="datasheet",
        ),
        temp_coeff_remanence=_PV(
            d_value=-1.2e-3,
            s_units="1/K",
            s_source=_ARNOLD_N42UH_SHEET + " -- alpha(Br) = -0.12 %/degC (20-180 C)",
            s_confidence="datasheet",
        ),
        temp_coeff_coercivity=_PV(
            d_value=-5.1e-3,
            s_units="1/K",
            s_source=_ARNOLD_N42UH_SHEET + " -- Reversible Temperature Coefficient of Coercivity "
            "α(HcJ) = -0.51 %/°C, measured 20-180 °C (N42UH "
            "standalone PDF Rev. 210607). Read directly from the "
            "Arnold PDF in the v1.8.0 source-verification pass. "
            "Cross-check: Shin-Etsu N47UH-GR sheet α(HcJ) = "
            "-0.50 %/K.",
            s_condition="reversible α(HcJ), measured 20-180 C, intrinsic coercivity HcJ",
            s_confidence="datasheet",
            s_notes=(
                "UH grade: α(HcJ)=-0.51 %/°C, between SH (-0.55) and EH "
                "(-0.42); higher Dy/Tb content gives progressively better "
                "coercivity thermal stability. Measured over 20-180 °C."
            ),
        ),
        resistivity_at_20C=_PV(
            d_value=1.5e-6,
            s_units="Ohm*m",
            s_source=_ARNOLD_N42UH_SHEET + " -- Electrical Resistivity = 150 // 130 µΩ·cm "
            "(parallel // perpendicular) per the N42UH "
            "standalone PDF Rev. 210607.",
            s_condition="parallel to easy axis, 20 C",
            s_confidence="datasheet",
            s_notes="v0.7.4 ADDED: 150 µΩ·cm = 1.5e-6 Ω·m parallel.",
        ),
        # μ_rec: Arnold family-typical value; Shin-Etsu N47UH-GR (closest
        # public per-grade UH-family sheet) corroborates μr = 1.05. No
        # exact-grade Shin-Etsu N42UH sheet exists publicly, but the
        # UH-family value is consistent across the grades Shin-Etsu
        # publishes.
        recoil_permeability=_ndfeb_recoil_permeability(
            d_value=1.05,
            s_primary_source=_ARNOLD_NDFEB_HIGH_TEMP_PAPER,
            s_corroborating_source=(
                _SHINETSU_N47UH_GR_SHEET + " (UH-family per-grade exemplar; nearest public match)"
            ),
            s_grade_condition="sintered NdFeB Dy-doped UH grade "
            "(Arnold family-typical + Shin-Etsu "
            "N47UH-GR UH-family corroboration; no "
            "exact-grade Shin-Etsu N42UH sheet)",
        ),
    ),
    thermal=_ndfeb_high_temp_thermal(
        d_max_op_C=180.0,
        s_grade="N42UH",
        s_source_sheet=_ARNOLD_N42UH_SHEET,
    ),
)


# ── NdFeB N42EH (extreme-high-temp, Tw=200°C) ─────────────────────────────

ndfeb_n42eh = Material(
    s_id="ndfeb_n42eh",
    s_description="Sintered NdFeB extreme-high-temp permanent magnet, grade N42EH (Tw=200 C)",
    s_category="magnet",
    s_specification="Sintered NdFeB N42EH (Arnold catalog N42EH)",
    s_catalog_version=_S_CATALOG_VERSION,
    s_last_reviewed=_S_LAST_REVIEWED,
    structural=_ndfeb_high_temp_structural(
        d_density_kg_m3=7500.0,
        s_source_sheet=_ARNOLD_N42EH_SHEET,
    ),
    electromagnetic=Electromagnetic(
        energy_product_max=_energy_product_max(
            d_nominal_kJ_m3=326,
            d_min_kJ_m3=310,
            d_max_kJ_m3=342,
            d_nominal_MGOe=41,
            s_source_sheet=_ARNOLD_N42EH_SHEET,
            s_grade="N42EH",
        ),
        remanence=_PV(
            d_value=1.310,
            s_units="T",
            s_source=_ARNOLD_N42EH_SHEET
            + " -- Br typical = 13,100 G = 1.310 T (range 12,800-13,400 G)",
            s_condition="20 C, typical",
            s_confidence="datasheet",
        ),
        coercivity=_PV(
            d_value=2308e3,
            s_units="A/m",
            s_source=_ARNOLD_N42EH_SHEET + " -- HcJ (intrinsic) min = 2308 kA/m = 29,000 Oe",
            s_condition="20 C, intrinsic coercivity HcJ (min)",
            s_confidence="datasheet",
        ),
        temp_coeff_remanence=_PV(
            d_value=-1.2e-3,
            s_units="1/K",
            s_source=_ARNOLD_N42EH_SHEET + " -- alpha(Br) = -0.12 %/degC (20-200 C)",
            s_confidence="datasheet",
        ),
        temp_coeff_coercivity=_PV(
            d_value=-4.2e-3,
            s_units="1/K",
            s_source=_ARNOLD_N42EH_SHEET + " -- Reversible Temperature Coefficient of Coercivity "
            "α(HcJ) = -0.42 %/°C, measured 20-200 °C (N42EH "
            "standalone PDF Rev. 151021a; published as -0.420). "
            "Read directly from the Arnold PDF in the v1.8.0 "
            "source-verification pass.",
            s_condition="reversible α(HcJ), measured 20-200 C, intrinsic coercivity HcJ",
            s_confidence="datasheet",
            s_notes=(
                "EH grade: α(HcJ)=-0.42 %/°C, the most thermally stable "
                "coercivity of the NdFeB grades here (highest Dy/Tb "
                "content), measured over the full 20-200 °C EH service "
                "range. This is what lets EH hold demag margin at the "
                "highest motor operating temperatures."
            ),
        ),
        resistivity_at_20C=_PV(
            d_value=1.8e-6,
            s_units="Ohm*m",
            s_source=_ARNOLD_N42EH_SHEET + " -- Electrical Resistivity = 180 µΩ·cm (single "
            "value, NO parallel/perpendicular split unlike "
            "the SH/UH grades) per the N42EH standalone PDF "
            "Rev. 151021a.",
            s_condition="20 C",
            s_confidence="datasheet",
            s_notes=(
                "v0.7.4 ADDED. N42EH is the outlier: its standalone "
                "PDF publishes 180 µΩ·cm as a single isotropic value, "
                "whereas N42SH/UH/plain grades publish 150 // 130 ⊥. "
                "The Dy/Tb-enriched grain-boundary phase in EH grades "
                "raises the bulk resistivity AND apparently averages "
                "the anisotropy out of the published spec (or Arnold "
                "simply reports single instead of split for this grade)."
            ),
        ),
        # μ_rec: Arnold family-typical value; corroborated by a Shin-Etsu
        # high-coercivity NdFeB datasheet (N47UH-GR: no exact-grade Shin-
        # Etsu N42EH sheet exists publicly, but Dy/Tb-doping doesn't shift
        # μ_rec materially within the sintered-NdFeB family per Arnold's
        # broader statement, and Shin-Etsu's high-coercivity exemplar
        # reports the same 1.05).
        recoil_permeability=_ndfeb_recoil_permeability(
            d_value=1.05,
            s_primary_source=_ARNOLD_NDFEB_HIGH_TEMP_PAPER,
            s_corroborating_source=(
                _SHINETSU_N47UH_GR_SHEET + " (high-coercivity NdFeB exemplar: nearest publicly-"
                "tabulated Shin-Etsu Dy-doped grade)"
            ),
            s_grade_condition="sintered NdFeB Dy/Tb-doped EH grade "
            "(Arnold family-typical + high-coercivity "
            "NdFeB corroboration)",
        ),
    ),
    thermal=_ndfeb_high_temp_thermal(
        d_max_op_C=200.0,
        s_grade="N42EH",
        d_k_W_mK=7.6,  # N42EH standalone publishes k=7.6 W/(m·K) single
        d_CTE_per_K=7.5e-6,  # N42EH standalone publishes 7.5e-6 parallel (vs SH/UH 7.0e-6)
        d_CTE_perp_per_K=-0.1e-6,  # N42EH standalone and Catalog Rev. 181031 agree
        s_source_sheet=_ARNOLD_N42EH_SHEET,
    ),
)


# ── SmCo 2:17 (Recoma 28, the standard 2:17 grade for motor design) ──────
#
# The Sm2Co17 family is the high-temperature alternative to NdFeB:
# - Curie temp 825 C (vs NdFeB 310 C) → far above any motor operating point.
# - Max recommended use temp (Tw) 350 C (vs NdFeB plain 80 C, EH 200 C).
# - Reversible α(Br) = -0.035 %/°C (vs NdFeB -0.12 %/°C) → ~3.4x better
#   temperature stability of magnetization.
# - Lower Br (1.04-1.10 T typical, 28-grade) than mid-NdFeB (~1.3 T), but
#   the temperature headroom is what justifies the trade for aerospace,
#   starter-generator, and downhole/under-the-hood automotive motors.
#
# Arnold publishes 16+ Recoma 2:17 grades (Recoma 24HE through 35E in the
# main catalog, plus HT and STAB variants). For v0.2.4 we add ONE grade,
# Recoma 28, because:
#  1. The grade-number convention is BHmax in MGOe → "28" = 28 MGOe =
#     225 kJ/m³, which sits mid-range in the family and is the most
#     commonly-specified grade in motor-design literature.
#  2. It's the closest 2:17 analog to plain NdFeB N42 (which dominates the
#     NdFeB side of this catalog), so consumers can A/B compare 2:17 vs
#     NdFeB at roughly matched BHmax (28 MGOe SmCo vs 42 MGOe NdFeB
#     within the same BHmax/Tw bandwidth).
#  3. Recoma 28 is documented on a dedicated per-grade page in the
#     Recoma combined catalog with all magnetic + thermal + "Other
#     Properties" fields populated: full Tier 1 coverage.
#
# Additional 2:17 grades (Recoma 30/32/33E/35E) and the SmCo5 family
# (Recoma 18/20/22/25) are deferred to a future release; see module
# docstring "Followup work".

smco_2_17 = Material(
    s_id="smco_2_17",
    s_description="Sintered Sm2Co17 (samarium-cobalt 2:17) permanent magnet, Arnold Recoma 28 grade",  # noqa: E501
    s_category="magnet",
    s_specification=(
        "Arnold Recoma 28 / Sm2Co17 sintered SmCo, transverse-pressed "
        "(BHmax nominal 28 MGOe = 225 kJ/m^3, range 25-28 MGOe / 195-225 kJ/m^3)"
    ),
    s_catalog_version=_S_CATALOG_VERSION,
    s_last_reviewed=_S_LAST_REVIEWED,
    structural=Structural(
        # Density: Recoma 28 per-grade page lists 8.3 g/cm^3; catalog
        # summary table (p.2 Rev. 160205a) lists 8.3 g/cm^3 for Recoma 28
        # (the 2:17 family is 8.3-8.4 g/cm^3 across grades). Use 8300.
        density=_PV(
            d_value=8300.0,
            s_units="kg/m^3",
            s_source=_ARNOLD_RECOMA_28_PAGE + " -- 'Other Properties' block Density = 8.3 g/cm^3 "
            "(cross-confirmed by catalog summary p.2 Rev. 160205a "
            "Density column for Recoma 28)",
            s_condition="20 C, sintered Sm2Co17",
            s_confidence="datasheet",
        ),
        # Young's modulus: Recoma 28 per-grade page lists 140 GPa
        # ("Young's Modulus" line in the "Other Properties" block).
        # This is an Arnold-published value, not a derived/handbook number;
        # it sits at Tier 1 datasheet.
        youngs_modulus=_PV(
            d_value=140e9,
            s_units="Pa",
            s_source=_ARNOLD_RECOMA_28_PAGE
            + " -- 'Other Properties' block Young's Modulus = 140 GPa",
            s_condition="20 C, sintered Sm2Co17, isotropic estimate "
            "(Arnold does not break into parallel/perp axes)",
            s_confidence="datasheet",
            s_notes=(
                "Sintered Sm2Co17 is magnetically anisotropic but elastically "
                "near-isotropic; Arnold publishes a single E without an axis "
                "qualifier, matching the convention for sintered rare-earth "
                "magnets. Same 140 GPa value appears on every per-grade Recoma "
                "2:17 page in the combined catalog."
            ),
        ),
        # Flexural strength: stored in v0.3.0's dedicated flexural_strength
        # slot (was ultimate_tensile in v0.2.4-v0.2.8). Sm2Co17 is brittle
        # like sintered NdFeB; Arnold publishes flexural-strength as the
        # only fracture-mode scalar.
        flexural_strength=_PV(
            d_value=120e6,
            s_units="Pa",
            s_source=_ARNOLD_RECOMA_28_PAGE + " -- 'Other Properties' block Flexural Strength = "
            "17,400 psi / 120 MPa",
            s_condition="20 C, sintered Sm2Co17; 3-point bend test "
            "(ASTM C1161-class brittle-flexure method)",
            s_confidence="datasheet",
            s_notes=(
                "Brittle-fracture flexural strength, NOT ductile UTS. "
                "Sintered Sm2Co17 has no ductile yield (brittle "
                "ceramic-like intermetallic). v0.3.0 moved this value "
                "from the ultimate_tensile slot to the dedicated "
                "flexural_strength slot: same schema clarification "
                "applied to all six NdFeB grades. For pure-tension "
                "stress states, derate ~30-40% from flexural value "
                "(the bend specimen compresses out surface flaws on "
                "the tension side). 120 MPa is identical across all "
                "Recoma 2:17 grades in the catalog (SmCo5 grades "
                "publish 145 MPa instead, the 5:1 phase is slightly "
                "stronger in bend). "
                ""
                "N/A-BY-PHYSICS CONVENTION (v0.6.0 documentation pass): "
                "sintered Sm2Co17 is a brittle intermetallic (Sm2Co17 "
                "rhombohedral hard phase + SmCo5 grain-boundary phase "
                "+ Cu/Fe/Zr ternary additions). Yield stress, ductile "
                "UTS, and fatigue endurance are physically not "
                "applicable: like sintered NdFeB, the material "
                "fractures elastically with no plastic-yield region. "
                "Arnold publishes flexural strength (stored here), "
                "Young's modulus (stored in youngs_modulus: the "
                "elastic-only modulus is meaningful for a brittle "
                "intermetallic), AND compressive strength "
                "(116,000 psi / 800 MPa per Recoma 28 page Rev. "
                "131025 'Other Properties' block). Compressive "
                "strength has no schema slot in v0.6.0 (the schema "
                "covers tension/bend/yield/UTS but not compression: "
                "a future MINOR bump could add Structural."
                "compressive_strength). The None values on "
                "poisson_ratio, yield_stress, ultimate_tensile, and "
                "fatigue_endurance reflect this brittle-intermetallic "
                "physics + Arnold's non-publication of those scalars, "
                "NOT a sourcing gap."
            ),
        ),
        # Poisson, yield, fatigue: NOT in Arnold sources, stay None.
        # Same flagging rationale as NdFeB: sintered SmCo is brittle, so
        # yield is not meaningful, and Arnold publishes neither Poisson
        # nor a fatigue endurance limit.
        compressive_strength=_PV(
            d_value=800e6,
            s_units="Pa",
            s_source=_ARNOLD_RECOMA_28_PAGE
            + " -- 'Other Properties' block Compressive Strength = 116,000 psi / 800 MPa",
            s_condition="20 C, sintered Sm2Co17",
            s_confidence="datasheet",
            s_notes=(
                "Brittle intermetallic: ~6.7x the flexural strength (120 MPa) "
                "stored above, the usual compression-vs-bending ratio for "
                "sintered rare-earth magnets. Use for press-fit / interference "
                "retention sizing; bending and tension are still governed by "
                "flexural_strength. Arnold publishes no compressive strength on "
                "the sintered NdFeB sheets, so those slots stay None."
            ),
        ),
        hardness_vickers=_PV(
            d_value=600.0,
            s_units="HV",
            s_source=_ARNOLD_RECOMA_28_PAGE
            + " -- 'Other Properties' block Hardness, Vickers = 600 Hv",
            s_condition="20 C, sintered Sm2Co17",
            s_confidence="datasheet",
            s_notes=(
                "Read directly from the Recoma 28 page (Rev. 131025). Earlier "
                "notes in this module quoted 800 Hv; that figure is the page's "
                "compressive strength in MPa, not its hardness. Corrected here."
            ),
        ),
        # ALSO on the Recoma 28 page but with no schema slot:
        #   alpha(Br) ⊥          = -0.035 %/°C (already used; perpendicular
        #                          axis tracks the parallel for Sm2Co17:
        #                          no separate perp value listed)
        #   Electrical Resistivity row exists but value-cell is blank
        #   (Arnold does not publish a Sm2Co17 ρ number: same as NdFeB).
    ),
    electromagnetic=Electromagnetic(
        energy_product_max=_energy_product_max(
            d_nominal_kJ_m3=225,
            d_min_kJ_m3=195,
            d_nominal_MGOe=28,
            s_source_sheet=_ARNOLD_RECOMA_28_PAGE + " (per-grade page min/nominal table; the "
            "catalog summary p.2 Rev. 160205a lists typ 225 / min 195 kJ/m3 too)",
            s_grade="Recoma 28",
        ),
        # Remanence. Recoma 28 per-grade page: Br typical = 1.10 T (11,000 G),
        # min = 1.04 T (10,400 G). Use nominal/typical for consistency with
        # NdFeB N42 entry (which uses Br_typ = 1.315 T from the per-grade PDF).
        remanence=_PV(
            d_value=1.10,
            s_units="T",
            s_source=_ARNOLD_RECOMA_28_PAGE
            + " -- Br typical = 11,000 G = 1.10 T (range 10,400-11,000 G)",
            s_condition="20 C, typical (Recoma 28 nominal)",
            s_confidence="datasheet",
            s_notes=(
                "Anisotropic transverse-pressed grade ('T' designator in "
                "Arnold's product-designator column on the catalog summary "
                "page). Br measured parallel to the magnetization (easy) "
                "axis."
            ),
        ),
        # Intrinsic coercivity. Recoma 28 per-grade page: HcJ typical
        # = 2000 kA/m (25,000 Oe), min = 1200 kA/m (15,000 Oe). Use the
        # MIN value, matching the NdFeB convention in this file
        # (motor-design conservative: assume the worst-corner HcJ that
        # Arnold guarantees). Min is also what the summary table lists
        # as a guaranteed lower bound on HcJ for the 28-grade.
        coercivity=_PV(
            d_value=1200e3,
            s_units="A/m",
            s_source=_ARNOLD_RECOMA_28_PAGE + " -- HcJ (intrinsic) min = 1,200 kA/m = 15,000 Oe "
            "(typical 2,000 kA/m / 25,000 Oe). Min used to match "
            "the NdFeB convention in this file.",
            s_condition="20 C, intrinsic coercivity HcJ (min)",
            s_confidence="datasheet",
            s_notes=(
                "Recoma 28's TYPICAL HcJ is 2000 kA/m: comparable to NdFeB "
                "N42UH. The (195/120) product designator from the catalog "
                "summary page p.2 indicates Recoma 28 = BHmax 195 kJ/m^3 "
                "minimum / HcJ 1200 kA/m minimum. Using the min HcJ for "
                "demag-margin calculations as Arnold-guaranteed worst-case."
            ),
        ),
        # Temperature coefficient of remanence: Recoma 28 per-grade page
        # explicitly lists α(Br) = -0.035 %/°C over 20-150 °C. This is the
        # *defining advantage* of SmCo 2:17 vs NdFeB: ~3.4x lower than
        # NdFeB's -0.12 %/°C, meaning a 100 °C rise from 20 to 120 °C drops
        # Br by only 3.5% (vs NdFeB's 12%).
        #
        # The asking task's "typically -3.0e-4" is from generic handbook
        # tables for "Sm2Co17" as a class; Arnold's per-grade datasheet is
        # higher Tier 1 (vendor TDS > handbook). Per this repo's
        # source-priority hierarchy (higher tier wins, never averaged --
        # see CLAUDE.md), vendor TDS wins. Recording the handbook
        # discrepancy in s_notes for downstream traceability.
        temp_coeff_remanence=_PV(
            d_value=-3.5e-4,
            s_units="1/K",
            s_source=_ARNOLD_RECOMA_28_PAGE + " -- Reversible Temperature Coefficient of Induction "
            "α(Br) = -0.035 %/°C (measured 20-150 °C). Cross-"
            "confirmed by Arnold catalog summary p.2 Rev. 160205a "
            "'Temperature Coefficient of Br (20-150 °C)' column = "
            "-0.035 %/°C for Recoma 28.",
            s_condition="measured 20-150 C, parallel to easy axis",
            s_confidence="datasheet",
            s_notes=(
                "Tier 1 [Arnold Recoma 28 per-grade page Rev. 131025] = "
                "-0.035 %/°C (used). Generic 2:17 handbook value sometimes "
                "quoted as -0.030 %/°C (rejected: lower-tier source, "
                "not grade-specific). This is the defining advantage of "
                "Sm2Co17 vs NdFeB: ~3.4x lower α(Br) magnitude (vs "
                "NdFeB's -0.12 %/°C). Per the source-priority rule: "
                "vendor TDS Tier 1 wins over handbook Tier 2."
            ),
        ),
        temp_coeff_coercivity=_PV(
            d_value=-2.4e-3,
            s_units="1/K",
            s_source=_ARNOLD_RECOMA_28_PAGE
            + " -- Reversible Temperature Coefficient of Coercivity "
            "alpha(HcJ) = -0.24 %/degC, measured 20-150 degC "
            "(Recoma 28 per-grade page Rev. 131025, 'Reversible "
            "Temperature Coefficients' block). Read directly from "
            "the Arnold Recoma combined-catalog Recoma 28 page in "
            "the v1.8.0 source-verification pass. Cross-check: "
            "Shin-Etsu R32HS Sm-Co sheet alpha(HcJ) = -0.27 %/K "
            "(a representative Sm2Co17 high-energy grade, not "
            "Recoma 28 exactly).",
            s_condition="reversible alpha(HcJ), measured 20-150 C, intrinsic coercivity HcJ",
            s_confidence="datasheet",
            s_notes=(
                "Sm2Co17's alpha(HcJ) = -0.24 %/degC is far less negative "
                "than any NdFeB grade here (plain -0.62, even EH -0.42), so "
                "its coercivity holds up dramatically better with "
                "temperature: a core reason SmCo is chosen over NdFeB for "
                "the hottest demag-critical motor/aerospace applications "
                "(alongside its 825 C Curie point and Tw 350 C)."
            ),
        ),
        # μ_rec: Shin-Etsu R32HS sheet publishes 1.02 for a representative
        # high-energy Sm-Co grade. R32HS is NOT the same exact grade as
        # Arnold Recoma 28, but is the closest publicly-tabulated Sm2Co17
        # high-energy per-grade sheet listing μ_rec at all. Arnold's
        # broader family statement gives ~1.05 for sintered SmCo as a
        # class; the catalog uses R32HS's 1.02 as a representative
        # high-energy-class scalar, not as an exact-grade match.
        recoil_permeability=_smco_recoil_permeability(
            d_value=1.02,
            s_grade_condition="sintered Sm2Co17 high-energy grade "
            "(Arnold Recoma 28; Shin-Etsu R32HS is a "
            "representative high-energy Sm-Co per-grade "
            "datasheet, not an exact-grade Recoma 28 "
            "match)",
        ),
    ),
    thermal=Thermal(
        # Thermal conductivity: Recoma 28 per-grade page lists 10 W/(m·K)
        # (single value, no axis qualifier: Arnold publishes Sm2Co17 k as
        # isotropic at this resolution). Same value across all Recoma 2:17
        # pages.
        thermal_conductivity=_PV(
            d_value=10.0,
            s_units="W/(m*K)",
            s_source=_ARNOLD_RECOMA_28_PAGE + " -- Thermal Conductivity = 10 W/(m·K)",
            s_condition="20 C, sintered Sm2Co17",
            s_confidence="datasheet",
        ),
        # Specific heat: Recoma 28 per-grade page lists 350 J/(kg·K)
        # (measured between 20-150 °C per footnote 3 on the page). Same
        # across all Recoma 2:17 pages.
        specific_heat=_PV(
            d_value=350.0,
            s_units="J/(kg*K)",
            s_source=_ARNOLD_RECOMA_28_PAGE
            + " -- Specific Heat = 350 J/(kg·K) (measured 20-150 °C)",
            s_condition="20-150 C, sintered Sm2Co17",
            s_confidence="datasheet",
        ),
        # Max recommended use temperature: Recoma 28 per-grade page
        # lists 350 °C (the Tw_max for the 2:17 family with HE-class HcJ).
        # The catalog summary table (p.2) lists 350 °C in the "Maximum
        # Operating Temperature" column for Recoma 28.
        max_operating_temp=_PV(
            d_value=350.0,
            s_units="C",
            s_source=_ARNOLD_RECOMA_28_PAGE + " -- Max. Recommended Use Temperature = 350 °C. "
            "Cross-confirmed by Arnold catalog summary p.2 "
            "Rev. 160205a 'Maximum Operating Temperature' "
            "column for Recoma 28 = 350 °C.",
            s_condition="continuous service, recoverable demagnetization; "
            "value may be lower in the presence of strong "
            "demagnetizing fields or on a low load-line "
            "(per Arnold catalog footnote 3)",
            s_confidence="datasheet",
            s_notes=(
                "Tw=350 °C is the key reason for choosing Sm2Co17 over "
                "NdFeB. The highest-Tw plain-NdFeB grade in this catalog "
                "(N42EH) is rated 200 °C; Recoma 28 adds 150 °C of "
                "thermal headroom for aerospace, downhole, and "
                "under-the-hood automotive applications."
            ),
        ),
        # Curie temperature. Recoma 28 per-grade page: 825 °C. Catalog
        # summary table p.2 doesn't list Tc but the per-grade pages all
        # converge on 825 °C for the 2:17 family (compared to 725 °C
        # for the SmCo5 family on the same catalog's SmCo5 pages).
        curie_temp=_PV(
            d_value=825.0,
            s_units="C",
            s_source=_ARNOLD_RECOMA_28_PAGE + " -- Curie Temperature Tc = 825 °C",
            s_condition="sintered Sm2Co17",
            s_confidence="datasheet",
            s_notes=(
                "2.7x higher than NdFeB's Tc (310 °C). Combined with the "
                "lower α(Br), this is what makes Sm2Co17 the rare-earth "
                "magnet of choice for high-temperature continuous service."
            ),
        ),
        # CTE: Recoma 28 per-grade page lists 11 × 10⁻⁶ /°C parallel
        # to the easy axis (footnote: "C //") and 13 × 10⁻⁶ /°C
        # perpendicular ("C ⊥"), measured between 20-200 °C per footnote 2.
        # Following the NdFeB convention in this file, we record the
        # PARALLEL value (with-grain) and document the anisotropy in
        # s_source. Note the 2:17 family has a much smaller magnitude
        # of CTE anisotropy than NdFeB (Recoma 28: 11/13 vs NdFeB: 7/-1).
        thermal_expansion=_PV(
            d_value=11.0e-6,
            s_units="1/K",
            s_source=_ARNOLD_RECOMA_28_PAGE
            + " -- Coefficient of Thermal Expansion = 11 × 10⁻⁶ /°C "
            "parallel to C-axis (perpendicular is 13 × 10⁻⁶ /°C; "
            "measured 20-200 °C)",
            s_condition="parallel to easy axis, 20-200 C",
            s_confidence="datasheet",
            s_notes=(
                "Sintered Sm2Co17 is magnetically anisotropic but "
                "CTE-anisotropy is mild (11 vs 13 × 10⁻⁶ /K, ~18% "
                "difference): much smaller than NdFeB's anisotropy "
                "(7 parallel vs -1 perpendicular × 10⁻⁶ /K, where the "
                "perpendicular axis actually contracts on heating). "
                "Parallel CTE used here to match the NdFeB-entry convention."
            ),
        ),
        thermal_expansion_perpendicular=_PV(
            d_value=13.0e-6,
            s_units="1/K",
            s_source=_ARNOLD_RECOMA_28_PAGE
            + " -- Coefficient of Thermal Expansion = 13 × 10⁻⁶ /°C perpendicular "
            "to C-axis ('C ⊥' column; measured 20-200 °C)",
            s_condition="perpendicular to easy axis, 20-200 C",
            s_confidence="datasheet",
            s_notes=(
                "Mild anisotropy for Sm2Co17 (13 ⊥ vs 11 // × 10⁻⁶ /K), both "
                "positive, unlike sintered NdFeB where the perpendicular axis "
                "contracts on heating."
            ),
        ),
    ),
)


# ── Catalog dict
# ── Cast Alnico 5 ──────────────────────────────────────────────────────────
#
# The legacy high-temperature magnet alloy; v0.2.0 deleted alnico_5 for
# handbook sourcing. Restored under a new id from Arnold's cast Alnico
# brochure. The brochure tabulates Br, BHmax, the normal coercive force HcB,
# recoil permeability, and physical properties, but NOT HcJ, temperature
# coefficients, or a maximum operating temperature (those appear only as
# curve plots), so those slots stay None.

alnico_5_cast = Material(
    s_id="alnico_5_cast",
    s_description="Cast Alnico 5 anisotropic permanent magnet (Al-Ni-Co-Fe), the standard grade",
    s_category="magnet",
    s_specification=(
        "Arnold cast Alnico 5 (anisotropic, the most widely used Alnico grade), typical "
        "values per the Arnold Cast ALNICO brochure Rev. C"
    ),
    s_catalog_version=_S_CATALOG_VERSION,
    s_last_reviewed=_S_LAST_REVIEWED,
    structural=Structural(
        ultimate_tensile=_PV(
            d_value=40e6,
            s_units="Pa",
            s_source=_ARNOLD_CAST_ALNICO_BROCHURE
            + " -- Tensile Strength, Alnico 5 = 5500 psi / 40 N/mm2",
            s_condition="room temperature, cast",
            s_confidence="datasheet",
            s_notes=(
                "Brittle cast intermetallic: this is the tensile fracture stress, not a "
                "ductile UTS; yield_stress stays None. Rockwell C 50 hardness on the "
                "same table is not a Vickers value and is not converted."
            ),
        ),
        flexural_strength=_PV(
            d_value=70e6,
            s_units="Pa",
            s_source=_ARNOLD_CAST_ALNICO_BROCHURE + " -- Transverse Modulus of Rupture, Alnico 5 = "
            "10000 psi / 70 N/mm2",
            s_condition="room temperature, cast, transverse bend",
            s_confidence="datasheet",
        ),
        density=_PV(
            d_value=7310.0,
            s_units="kg/m^3",
            s_source=_ARNOLD_CAST_ALNICO_BROCHURE
            + " -- Density, Alnico 5 = 0.264 lb/in3 / 7.31 g/cm3",
            s_condition="room temperature, cast",
            s_confidence="datasheet",
        ),
    ),
    electromagnetic=Electromagnetic(
        remanence=_PV(
            d_value=1.25,
            s_units="T",
            s_source=_ARNOLD_CAST_ALNICO_BROCHURE
            + " -- Residual Induction Br, Alnico 5 = 12500 G / "
            "1250 mT (typical)",
            s_condition="20 C, typical",
            s_confidence="datasheet",
            s_notes=(
                "The brochure publishes the NORMAL coercive force HcB = 640 Oe / 51 kA/m, "
                "not the intrinsic HcJ this catalog's coercivity slot stores, so "
                "coercivity stays None rather than mis-filing HcB. Alnico's low "
                "coercivity (vs 1.3 T remanence) is why it demagnetises easily in "
                "open circuit; required magnetising field 3000 Oe / 240 kA/m."
            ),
        ),
        energy_product_max=_PV(
            d_value=43.8e3,
            s_units="J/m^3",
            s_source=_ARNOLD_CAST_ALNICO_BROCHURE + " -- Max. Energy Product Bd x Hd, Alnico 5 = "
            "5.50 MGOe / 43.8 kJ/m3 (typical)",
            s_condition="20 C, typical (single value; no min/max band published)",
            s_confidence="datasheet",
            s_notes="Induction at maximum energy product = 10000 G / 1000 mT on the same table.",
        ),
        recoil_permeability=_PV(
            d_value=3.7,
            s_units="",
            s_source=_ARNOLD_CAST_ALNICO_BROCHURE + " -- Recoil Permeability, Alnico 5 = 3.7 G/Oe",
            s_condition="20 C, typical",
            s_confidence="datasheet",
            s_notes=(
                "G/Oe is dimensionless relative permeability. Far above the ~1.05 of "
                "sintered rare-earth magnets: Alnico's recoil line is steep, which is "
                "the load-line sensitivity designers work around with keepers."
            ),
        ),
        resistivity_at_20C=_PV(
            d_value=47e-8,
            s_units="Ohm*m",
            s_source=_ARNOLD_CAST_ALNICO_BROCHURE
            + " -- Electrical Resistivity, Alnico 5 = 47 uOhm cm "
            "at 25 C. Converted to Ohm*m (x 1e-8).",
            s_condition="25 C",
            s_confidence="datasheet",
        ),
    ),
    thermal=Thermal(
        thermal_expansion=_PV(
            d_value=11.5e-6,
            s_units="1/K",
            s_source=_ARNOLD_CAST_ALNICO_BROCHURE
            + " -- Coefficient of Thermal Expansion, Alnico 5 = "
            "11.5 per C x 10^6",
            s_condition="room temperature; temperature range not stated in the brochure",
            s_confidence="datasheet",
            s_notes=(
                "Curie temperature, maximum operating temperature, and reversible "
                "temperature coefficients are shown only as curve plots in the "
                "brochure (Temperature Effects pages), not tabulated; those slots stay "
                "None rather than being read off a graph."
            ),
        ),
    ),
)


CATALOG: dict[str, Material] = {
    ndfeb_n35.s_id: ndfeb_n35,
    ndfeb_n42.s_id: ndfeb_n42,
    ndfeb_n50.s_id: ndfeb_n50,
    ndfeb_n42sh.s_id: ndfeb_n42sh,
    ndfeb_n42uh.s_id: ndfeb_n42uh,
    ndfeb_n42eh.s_id: ndfeb_n42eh,
    smco_2_17.s_id: smco_2_17,
    alnico_5_cast.s_id: alnico_5_cast,
}


__all__ = [
    "CATALOG",
    "alnico_5_cast",
    "ndfeb_n35",
    "ndfeb_n42",
    "ndfeb_n42eh",
    "ndfeb_n42sh",
    "ndfeb_n42uh",
    "ndfeb_n50",
    "smco_2_17",
]
