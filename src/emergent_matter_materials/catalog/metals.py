"""Metals: structural alloys + conductors (Tier-1-only catalog).

Under the v0.2.0 "Tier 1 only" policy, this file contains only
PropertyValues with confidence in {measured, datasheet, standard}.
Aggregator-tier MatWeb data and unverified handbook values from
v0.1.x have been removed; the corresponding gaps are left unpopulated
until a Tier 1 source is verified.

Six metals are populated at Tier 1. As of v0.6.0 every material here
has structural + thermal coverage (E, nu, yield/UTS, density, k, c_p,
CTE for all; melting_temp for all except steel_4140; full crystal-
anisotropy single-crystal C_ij + per-structure constants for all six):

| Material            | Source canon                                     |
|---------------------|--------------------------------------------------|
| pure_copper         | ASM Vol 2 + CDA C10100 + NIST JPCRD + CRC        |
| aluminum_6061_t6    | ASM Vol 2 + Aluminum ADM 2017 + ASTM B221        |
| steel_4140          | ASM Vol 1 (normalized 870 C, 25 mm) + TimkenSteel|
| stainless_304       | AK Steel PDS + Atlas + Outokumpu + ASTM A240     |
| stainless_316       | AK Steel PDS + Atlas + Outokumpu + ASTM A240     |
| titanium_6al_4v     | ASM Vol 2 + ASTM B348 Grade 5 + Boyer Atlas      |

v0.6.0 (this revision) restored:
- pure_copper structural (E, nu, yield, UTS) from ASM Vol 2 + CDA
  C10100 annealed-O60 spec; thermal CTE + melting_temp from CRC
  Handbook (NIST SRD IPTS-90 fixed point for Cu liquidus).
- titanium_6al_4v full structural (E=113.8 GPa, nu=0.342, yield=880,
  UTS=950, density=4430) + full thermal (k=6.7, c_p=560, max_op=400 C,
  CTE=8.6e-6, T_melt=1604 C solidus) from ASM Vol 2 + ASTM B348.

Earlier revisions:
- v0.2.1 restored pure_copper EM + thermal + density (NIST JPCRD +
  CDA C10100 + CRC Handbook).
- v0.2.2 fully restored aluminum_6061_t6 and stainless_304/316.
- v0.2.7 fully restored steel_4140 (ASM Vol 1 normalized-25mm row).

v0.7.1 (this revision), third exhaustive audit pass: NO new data added.
This pass walked every Material x every schema slot x every cited primary
source and confirmed the v0.6.0 + v0.7.0 sweeps drained the cited-source
pond. The remaining unpopulated slots are bucketed as follows:

- N/A by physics (correctly None across this file):
  * Structural.flexural_strength on all six (brittle-material slot;
    ductile metals fail by yielding, not flexural rupture).
  * Electromagnetic.{saturation_flux, coercivity, remanence,
    temp_coeff_remanence} on Cu/Al/304/316/Ti-6Al-4V (permanent-magnet
    or strong-ferromagnet slots; these five are dia/para/weakly-
    paramagnetic).
  * Electromagnetic.{dielectric_strength, relative_permittivity} on all
    six (conductor slots; not defined for bulk metals).
  * Thermal.{glass_transition, curie_temp} on all five non-ferromagnets
    (polymer / Curie-point N/A for these classes).
  * Thermal.emissivity on all six (surface property, not a bulk-material
    Tier-1 entry: depends on oxide layer / polish / coating).

- Tier-1 cited but value genuinely not single-scalar / not published:
  * pure_copper.thermal.max_operating_temp: Cu anneal-softens
    progressively above ~200 C; ASM Vol 2 + CDA C10100 do not publish
    a single canonical "Cu max op temp" scalar.
  * aluminum_6061_t6.thermal.max_operating_temp: 6061-T6 over-ages
    above ~150-175 C with measurable strength loss; ADM publishes a
    strength-vs-temperature derating curve, not a single scalar.
  * steel_4140.thermal.melting_temp: ASM Vol 1 normalized-4140 row does
    not publish solidus/liquidus; ASM Ready Reference Table 5.3 is
    paywalled. The 1416 C aggregator value lacks Tier-1 primary citation.

- Deferred for substantive reasons (NOT a sourcing gap):
  * steel_4140 EM group (mu_r, saturation_flux, coercivity, remanence):
    heat-treatment-specific; no single Tier-1 value valid across
    annealed/normalized/Q&T conditions. Future heat-treatment-specific
    entry planned.
  * titanium_6al_4v.electromagnetic.relative_permeability: weakly
    paramagnetic ~1.00018. CRC Handbook Section 12 has Ti/Al/V molar
    susceptibilities, but computing mu_r for Ti-6Al-4V requires mass-
    weighted alloy-density derivation rather than a directly tabulated
    value. Engineering-effectively unity; deferred as derived-tier.

All remaining followups are left unpopulated until a Tier 1 source is verified.

v0.7.0 closed remaining EM/thermal gaps:
- pure_copper + aluminum_6061_t6: relative_permeability (CRC Handbook
  Section 12 magnetic susceptibilities: Cu diamagnetic 0.999994, Al
  paramagnetic 1.000022).
- stainless_304 + stainless_316: temp_coeff_resistivity + melting_temp
  (AK Steel PDS 20-500 C resistivity rise + PDS melting-range upper bound).
- steel_4140: curie_temp = 770 C (Bozorth Ch. 7 + ASM Vol 1).
- steel_4140 EM group intentionally not added: mu_r of 4140 varies
  200-1000 with heat treatment (annealed vs normalized vs quenched-and-
  tempered) and there is no single Tier-1 value valid across conditions.
  4140 IS ferromagnetic but its EM response is condition-specific;
  deferred to a future heat-treatment-specific entry.

N/A-by-physics notes (correctly None across this file):
- ``Thermal.glass_transition``: polymer-only concept (chain segmental
  mobility onset); not defined for metals.
- ``Electromagnetic.temp_coeff_remanence`` / ``coercivity`` /
  ``remanence`` / ``saturation_flux``: permanent-magnet / strong-
  ferromagnet properties. Of the six metals here, only steel_4140 is
  strongly ferromagnetic; its remanence/coercivity/B_sat depend on
  heat treatment (200-1000 mu_r range) and are deferred per above.
  Cu/Al/304/316/Ti-6Al-4V are diamagnetic, paramagnetic, or weakly-
  paramagnetic austenitic: these slots are N/A by physics.
- ``Electromagnetic.relative_permeability`` on Ti-6Al-4V: also weakly
  paramagnetic (~1.00018, dominated by Ti); engineering-effectively
  unity. Not populated this revision: followup gap.

All remaining gaps are left unpopulated until a Tier 1 source is verified.
"""

from __future__ import annotations

from emergent_matter_materials.crystal_anisotropy import CrystalAnisotropy
from emergent_matter_materials.electromagnetic import Electromagnetic
from emergent_matter_materials.material import Material
from emergent_matter_materials.property_value import PropertyValue as _PV
from emergent_matter_materials.structural import Structural
from emergent_matter_materials.thermal import Thermal

# Every entry is stamped with the first release, 1.0.0. A later release that
# adds or re-reviews an entry gives that entry its own s_catalog_version
# instead of relabeling the untouched ones.
_S_CATALOG_VERSION = "1.0.0"
_S_LAST_REVIEWED = "2026-05-24"

# ── Crystal-anisotropy primary sources (v0.4.0) ─────────────────────────────
_OVERTON_GAFFNEY_1955 = (
    "Overton & Gaffney, 'Temperature Variation of the Elastic Constants of "
    "Cubic Elements. I. Copper,' Physical Review 98(4):969-977 (15 May 1955). "
    "DOI 10.1103/PhysRev.98.969. The canonical ultrasonic-measurement paper "
    "for single-crystal Cu C_ij: cited by ~every Cu crystal-plasticity FEM "
    "study. Values at 300 K: C11=168.4, C12=121.4, C44=75.4 GPa."
)
_STOBBS_SWORN_1971 = (
    "Stobbs & Sworn, 'The weak beam technique as applied to the determination "
    "of the stacking-fault energy of copper,' Philosophical Magazine "
    "24(192):1365-1381 (1971). DOI 10.1080/14786437108217418. Weak-beam TEM "
    "measurement on pure Cu single crystals: gamma_SFE = 78 +/- 8 mJ/m^2."
)
_FROST_ASHBY_1982 = (
    "Frost & Ashby, 'Deformation-Mechanism Maps: The Plasticity and Creep of "
    "Metals and Ceramics' (Pergamon Press, 1982), Chapter 6 (Cu, p.21). The "
    "compiled reference for pure-Cu Peierls + athermal CRSS at room "
    "temperature: tau_CRSS = 0.4 MPa for well-annealed pure Cu single "
    "crystals."
)
_KAMM_ALERS_1964 = (
    "Kamm & Alers, 'Low-Temperature Elastic Moduli of Aluminum,' Journal of "
    "Applied Physics 35(2):327-330 (February 1964). DOI 10.1063/1.1713309. "
    "Ultrasonic measurements on Al single crystals from 4.2 K to 300 K; "
    "300 K values: C11=107.3, C12=60.9, C44=28.3 GPa."
)
_CARTER_HOLMES_1977 = (
    "Carter & Holmes, 'The stacking-fault energy of nickel and aluminium,' "
    "Philosophical Magazine 35(5):1161-1172 (1977). DOI "
    "10.1080/14786437708232942. Node-spacing TEM measurement: Al SFE = "
    "166 +/- 15 mJ/m^2 (much higher than Cu's 78, which is why Al rarely "
    "twins)."
)
_LEDBETTER_1984 = (
    "Ledbetter, 'Predicted single-crystal elastic constants of stainless-"
    "steel 316,' Zeitschrift fuer Metallkunde 75(7):551-555 (1984). The "
    "reference single-crystal elastic-constant compilation for AISI 304 + "
    "316 austenitic gamma-Fe matrices, derived from polycrystal aggregate "
    "inversion. 304: C11=197, C12=122, C44=124 GPa; 316: C11=204, C12=133, "
    "C44=126 GPa (Mo slightly stiffens 316)."
)
_SCHRAMM_REED_1975 = (
    "Schramm & Reed, 'Stacking fault energies of seven commercial austenitic "
    "stainless steels,' Metallurgical Transactions A 6(7):1345-1351 (July "
    "1975). DOI 10.1007/BF02641927. The canonical SFE reference for "
    "commercial austenitic SS: 304 = 21 mJ/m^2 (low, drives TRIP / "
    "mechanical twinning); 316 = 78 mJ/m^2 (Mo addition raises SFE roughly "
    "4x, suppressing strain-induced martensite)."
)
_RAYNE_CHANDRASEKHAR_1961 = (
    "Rayne & Chandrasekhar, 'Elastic Constants of Iron from 4.2 to 300 K,' "
    "Physical Review 122(6):1714-1716 (15 June 1961). DOI 10.1103/PhysRev."
    "122.1714. The canonical ultrasonic-measurement paper for alpha-Fe (BCC) "
    "single-crystal C_ij. 300 K values: C11=231.4, C12=134.7, C44=116.4 GPa."
)
_FISHER_RENKEN_1964 = (
    "Fisher & Renken, 'Single-Crystal Elastic Moduli and the hcp -> bcc "
    "Transformation in Ti, Zr, and Hf,' Physical Review 135(2A):A482-A494 "
    "(20 July 1964). DOI 10.1103/PhysRev.135.A482. Ultrasonic measurements "
    "across the alpha-beta transition. Alpha-Ti at 300 K: C11=162.4, "
    "C12=92.0, C13=69.0, C33=180.7, C44=46.7 GPa."
)
_HALL_1960 = (
    "Hall, 'Elastic constants of a Fe-50at%Co single crystal,' Transactions "
    "of the Metallurgical Society of AIME 218(2):619-624 (June 1960). The "
    "single-crystal C_ij measurement for B2-ordered FeCo (the chemistry of "
    "Carpenter Hiperco 50): C11=252, C12=144, C44=134 GPa. Ordering below "
    "~720 C (the order-disorder transition) raises C44 vs disordered Co-Fe."
)
_MACHOVA_KADECKOVA_1977 = (
    "Machova & Kadeckova, 'Elastic constants of iron-silicon alloy single "
    "crystals,' Czechoslovak Journal of Physics B 27(5):555-563 (1977). DOI "
    "10.1007/BF01587814. Direct ultrasonic measurement on Fe-Si single "
    "crystals across composition 0-6.5 wt% Si. At 3 wt% Si (M19 / M270-35A "
    "composition): C11=226, C12=138, C44=115 GPa (alpha-Fe softened ~3-4% "
    "per wt% Si solid-solution addition vs the pure-Fe Rayne-Chandrasekhar "
    "baseline)."
)
_FROST_ASHBY_FE_BCC = (
    "Frost & Ashby, 'Deformation-Mechanism Maps' (Pergamon, 1982), Chapter "
    "8 (alpha-Fe + BCC alloys). Reference compilation for BCC slip systems, "
    "Peierls-Nabarro stress, and lattice-friction CRSS: used here as a "
    "secondary citation source for the alpha-Fe Burgers vector formula |b| "
    "= a*sqrt(3)/2 for <111> slip on {110}, {112}, {123} planes."
)

_ALUMINUM_ADM = (
    "Aluminum Association, 'Aluminum Standards and Data 2017' (the data "
    "appendix to the Aluminum Design Manual). Tier 1 standard reference "
    "for AA 6061-T6 wrought-product mechanical/thermal/electrical "
    "properties. Retrieved 2026-05-24 (digest via ASM Aerospace Spec "
    "Metals at asm.matweb.com/search/SpecificMaterial.asp?bassnum="
    "ma6061t6 which reproduces ADM tables verbatim)."
)
_ASM_HANDBOOK_VOL2 = (
    "ASM Handbook Volume 2: Properties and Selection: Nonferrous Alloys "
    "and Special-Purpose Materials (10th ed.), 6061 alloy entry. The "
    "canonical metallurgy reference for wrought-aluminum properties."
)
_IEC_60889 = (
    "IEC 60889:1987, 'Hard-drawn aluminium wire for overhead line "
    "conductors': the international standard defining the reference "
    "electrical properties of EC-grade (1350) aluminium conductor. "
    "Volume resistivity at 20 C = 0.028264 Ohm*mm^2/m = 2.8264e-8 Ohm*m "
    "(the 61.0% IACS reference; the standard states this 'shall be used "
    "as the standard resistivity for the purpose of calculation'). "
    "Temperature coefficient of resistance at 20 C, alpha_20 = "
    "0.00403 /K. Verified 2026-06-17: the resistivity figure against the "
    "IEC 60889 standard text, and both figures against the IEC "
    "60028/60889 reference table at iee-business.com, which "
    "independently lists Al = 2.828e-8 Ohm*m / alpha 0.00403 and Cu = "
    "1.724e-8 / 0.00393 (the Cu alpha matching this catalog's pure_copper "
    "value, a cross-check that the reference table is reliable)."
)
_ASTM_B221 = (
    "ASTM B221-21, 'Standard Specification for Aluminum and Aluminum-"
    "Alloy Extruded Bars, Rods, Wire, Profiles, and Tubes,' defines "
    "minimum mechanical properties for 6061-T6 extrusions. Mill TDS "
    "values are 'typical' (above the spec minimum)."
)
_CLF_17_4PH_PDS = (
    "Cleveland-Cliffs '17-4 PH Stainless Steel' Product Data Bulletin (May 2021, "
    "(c) 2021 Cleveland-Cliffs Inc.), retrieved 2026-09-17 from "
    "https://d1io3yog0oux5.cloudfront.net/_0b7af4ee15fd94d01f7a17c02e843ab6/"
    "clevelandcliffs/db/1190/10503/file/CLF_ProductData_17-4-PHSS_052021.pdf. "
    "Table 2 'Typical Mechanical Properties' and Table 3 'Properties Acceptable "
    "for Material Specification' (sheets and strip), H 900 column; Table 9 "
    "'Physical Properties', H 900 column"
)
_CDA_C93200 = (
    "Copper Development Association, alloy C93200 (Cast Bronzes, Copper-Tin-Lead "
    "Alloys / High-Leaded Tin Bronzes) page in the CDA alloy database, 'Physical "
    "Properties' and 'Mechanical Properties' tables (room temperature, 68 F / 20 C), "
    "retrieved 2026-09-17 from https://alloys.copper.org/alloy/C93200"
)
_AK_STEEL_304_PDS = (
    "AK Steel '304/304L Stainless Steel' Product Data Sheet, Doc# "
    "304/304L-S-8-01-07 (Rev. 7/07), retrieved 2026-05-24 from "
    "https://www.spacematdb.com/spacemat/manudatasheets/304_304L_Data_Sheet.pdf"
)
_AK_STEEL_316_PDS = (
    "AK Steel '316/316L Stainless Steel' Product Data Bulletin (Rev. 12/13/16), "
    "retrieved 2026-05-24 from http://asremavad.com/wp-content/uploads/"
    "2018/11/AK-steel-316-stainless-steel-data-sheet.pdf"
)
_ASTM_A240 = (
    "ASTM A240/A240M, 'Standard Specification for Chromium and Chromium-"
    "Nickel Stainless Steel Plate, Sheet, and Strip,' minimum property "
    "values for 304/316 annealed (yield ≥ 205 MPa, UTS ≥ 515 MPa). "
    "Reproduced verbatim in AK Steel + Atlas Steels mill TDSes."
)
_ASM_HANDBOOK_VOL1_4140_NORM = (
    "ASM Handbook Volume 1: 'Properties and Selection: Irons, Steels, and "
    "High-Performance Alloys' (10th ed., 1990), AISI 4140 normalized at "
    "870 C (1600 F), air cooled, 25 mm (1 in.) round entry. Source-of-"
    "record for normalized 4140 alloy steel data. The ASM-hosted matweb "
    "digest at asm.matweb.com cites ASM Vol 1 10th Ed. 1990 explicitly "
    "as its primary reference (verified via asm.matweb.com GetReference."
    "asp?bassnum=M434BB for the 4xxx Cr-Mo family; same source applies "
    "to the 4140 normalized 25mm round row). The exact tabulated values "
    "are republished verbatim by the MW Components (Elgin) 'Alloy Steel "
    "Grade 4140 Fact Sheet,' retrieved 2026-05-24 from "
    "https://www.mwcomponents.com/uploads/Resource-Center/"
    "Elgin-Material-Sheets/Alloy-Steel-Grade-4140-Fact-Sheet_"
    "Elgin-Website.pdf, which reproduces the ASM Vol 1 normalized-25mm "
    "row including the 870 C / air cooled / 25 mm size qualifier."
)
_TIMKEN_PRACTICAL_DATA_18 = (
    "TimkenSteel, 'Practical Data for Metallurgists' (18th Edition, 2017), "
    "p.126 'Handy Physical Constants', STEEL CONSTANTS table: Modulus "
    "of Elasticity (steel) = 30 x 10^6 psi (206.84 GPa); Density of "
    "Carbon & Low-Alloy Steels = 0.283 lbm/in^3 = 7.84 g/cm^3 = 7840 "
    "kg/m^3. These are generic-for-low-alloy-steels constants that "
    "apply to AISI 4140 as a Cr-Mo low-alloy steel. Retrieved 2026-05-24 "
    "from https://22178764.fs1.hubspotusercontent-na1.net/hubfs/"
    "22178764/Sullivansteelservice_May2023/PDF/Practical-Data-For-"
    "Metallurgists-TimkenSteel_20170126.pdf"
)

# ── Pure-Cu primary sources added in v0.6.0 ─────────────────────────────────
_ASM_HANDBOOK_VOL2_CU = (
    "ASM Handbook Volume 2: Properties and Selection: Nonferrous Alloys "
    "and Special-Purpose Materials (10th ed., 1990), 'Properties of Wrought "
    "Coppers' section. The canonical Tier-1 standard reference for pure-Cu "
    "elastic constants, mechanical properties (annealed temper), CTE, and "
    "melting point. ASM Vol 2 is the source-of-record across the metallurgy "
    "industry for wrought-copper data; ASTM B187 / CDA C10100 reference back "
    "to it for the elastic-constant and ductile-mechanical entries."
)
_CDA_C10100_ANNEALED = (
    "Copper Development Association (CDA) 'C10100 Oxygen-Free Electronic "
    "Copper / OFE' alloy spec sheet, Mechanical Properties section: "
    "annealed temper OS050 (0.050 mm grain size flat product per the "
    "live CDA tabulation), Yield Strength 0.5% extension = 10 ksi "
    "(69 MPa), Tensile Strength = 32 ksi (220 MPa). v0.7.2 corrected "
    "the temper-code reference from 'O60' (ASTM B187/B49 wrought-rod) "
    "to 'OS050' (the flat-product row CDA actually publishes the "
    "cited scalar against, per v0.7.2 validation); numeric values "
    "unchanged. Retrieved 2026-05-24 from "
    "https://alloys.copper.org/alloy/C10100"
)
_CRC_HANDBOOK_PURE_CU = (
    "CRC Handbook of Chemistry and Physics (95th-100th editions), 'Physical "
    "Properties of the Pure Elements' table: pure-Cu canonical thermophysical "
    "constants: linear coefficient of thermal expansion at 25 deg C = 16.5 "
    "ppm/K (16.5e-6 /K); melting point = 1084.62 deg C (1357.77 K, the IPTS-90 "
    "Cu fixed point used by NIST as a primary thermometric calibration). The "
    "1085 C value used here rounds the IPTS-90 fixed-point liquidus. The CRC "
    "compilation in turn cites NIST SRD for these primary constants."
)

# ── Ti-6Al-4V primary sources added in v0.6.0 ───────────────────────────────
_ASTM_B348_GRADE5 = (
    "ASTM B348/B348M, 'Standard Specification for Titanium and Titanium "
    "Alloy Bars and Billets,' Grade 5 (Ti-6Al-4V) annealed minimum "
    "mechanical properties: Yield Strength 0.2% offset >= 120,000 psi "
    "(827 MPa), Ultimate Tensile Strength >= 130,000 psi (896 MPa). "
    "Reproduced verbatim in vendor mill TDSes (TIMET, Carpenter, ATI). "
    "ASTM B348 is the grade-defining Tier-1 standard for wrought Ti-6Al-4V "
    "bar/billet: the spec the material is purchased against."
)
_ASM_HANDBOOK_VOL2_TI64 = (
    "ASM Handbook Volume 2: Properties and Selection: Nonferrous Alloys "
    "and Special-Purpose Materials (10th ed., 1990), 'Ti-6Al-4V (Ti-6-4 / "
    "Grade 5)' alloy entry in the Titanium Alloys section. The canonical "
    "Tier-1 standard reference for Ti-6Al-4V annealed thermophysical and "
    "mechanical properties: Young's modulus = 113.8 GPa (16.5 Mpsi), "
    "Poisson's ratio = 0.342, density = 4.43 g/cm^3 (4430 kg/m^3), thermal "
    "conductivity at 20 C = 6.7 W/(m*K), specific heat at 20 C = 560 "
    "J/(kg*K), CTE 20-100 C = 8.6e-6 /K, liquidus = 1604-1660 C (typical "
    "1660 C, the upper bound of the published range), beta-transus = "
    "995 +/- 15 C. Typical mill yield and UTS for annealed Ti-6Al-4V are "
    "880 MPa and 950 MPa (above the ASTM B348 minimum of 827/896 MPa)."
)
_TI64_MAX_OP_TEMP = (
    "ASM Handbook Vol 2 + Boyer/Welsch/Collings 'Materials Properties "
    "Handbook: Titanium Alloys' (ASM Intl, 1994), continuous-service "
    "temperature ceiling for Ti-6Al-4V at 400 deg C (the alpha-2 ordered-"
    "phase precipitation onset and the long-term creep-strength knee). "
    "Above 400 C, oxide-layer scaling + alpha-case embrittlement + creep "
    "dominate; intermittent service to 540 C is possible but the "
    "continuous-service Tier-1 ceiling is 400 C."
)

# ── v0.7.0 EM/thermal primary sources ───────────────────────────────────────
_CRC_HANDBOOK_MAGNETICS = (
    "CRC Handbook of Chemistry and Physics, 95th ed. (2014), Section 12, "
    "Magnetic Susceptibility of the Elements. The canonical Tier-1 "
    "compilation of room-temperature mass + molar magnetic susceptibilities "
    "for the elements; relative permeability mu_r = 1 + chi_v (volume "
    "susceptibility) is derived from the tabulated molar susceptibility "
    "by chi_v = chi_mol * rho / M. Cu (diamagnetic): chi_mol = -5.46e-6 "
    "cm^3/mol -> mu_r = 0.999994 at 20 C. Al (paramagnetic): chi_mol = "
    "+16.5e-6 cm^3/mol -> mu_r = 1.000022 at 20 C. These values are "
    "dominated by the bulk-element response; alloying additions at the "
    "wt-percent level do not shift mu_r meaningfully at this precision "
    "(both Cu and Al-6061 are practically non-magnetic for engineering "
    "purposes)."
)
_BOZORTH_FERROMAGNETISM = (
    "Bozorth, *Ferromagnetism* (IEEE Press reissue 1993, orig. Van Nostrand "
    "1951), Chapter 7 'Iron and its alloys.' The canonical engineering "
    "reference for ferromagnetic Curie temperatures and saturation "
    "magnetizations. Pure alpha-Fe Curie point T_c = 770 C (1043 K); "
    "low-alloy ferritic steels (4140, 4340, AISI 4xxx series) retain "
    "essentially the pure-Fe Curie temperature within +/- 10 C: Cr/Mo/Ni "
    "additions at the wt-percent level perturb T_c only weakly. Cross-"
    "referenced by ASM Handbook Vol 1 (Properties and Selection: Irons, "
    "Steels, and High-Performance Alloys), magnetic-properties section."
)


# ── Pure copper (annealed) ──────────────────────────────────────────────────

pure_copper = Material(
    s_id="pure_copper",
    s_description="OFE/OFHC pure copper, annealed",
    s_category="metal",
    s_specification="UNS C10100 (OFE copper) per ASTM B187, annealed, 101% IACS",
    s_catalog_version=_S_CATALOG_VERSION,
    s_last_reviewed=_S_LAST_REVIEWED,
    structural=Structural(
        youngs_modulus=_PV(
            d_value=117e9,
            s_units="Pa",
            s_source=_ASM_HANDBOOK_VOL2_CU + " -- Young's modulus for pure annealed Cu (wrought, "
            "OFE/OFHC class) = 117 GPa (17 Mpsi). This is the "
            "canonical pure-Cu elastic modulus tabulated by ASM "
            "Vol 2 and reproduced by every downstream Cu spec.",
            s_condition="20 C, annealed",
            s_confidence="standard",
        ),
        poisson_ratio=_PV(
            d_value=0.34,
            s_units="",
            s_source=_ASM_HANDBOOK_VOL2_CU + " -- Poisson's ratio for pure annealed Cu = 0.34, the "
            "canonical wrought-copper value tabulated in ASM Vol 2.",
            s_condition="20 C, annealed",
            s_confidence="standard",
        ),
        yield_stress=_PV(
            d_value=69e6,
            s_units="Pa",
            s_source=_CDA_C10100_ANNEALED
            + " -- Yield Strength (0.5% extension under load) = 10 ksi "
            "= 69 MPa for annealed (O60) temper. Per ASTM B187 / B49 "
            "wrought-rod specs.",
            s_condition="0.5% extension under load, annealed (O60) temper",
            s_confidence="standard",
            s_notes=(
                "CDA C10100 publishes yield at 0.5% extension under load (the "
                "B187 convention), NOT the 0.2% offset convention used for "
                "steels. Annealed Cu has a rounded stress-strain curve so the "
                "two values are close (69 vs ~70 MPa) but not identical. "
                "Cold-worked Cu yields much higher (e.g. H02 half-hard "
                "30 ksi = 207 MPa, H04 hard 36 ksi = 248 MPa). The 69 MPa "
                "value here is the annealed-OFE reference."
            ),
        ),
        ultimate_tensile=_PV(
            d_value=220e6,
            s_units="Pa",
            s_source=_CDA_C10100_ANNEALED + " -- Tensile Strength = 32 ksi = 220 MPa for annealed "
            "(O60) temper, per ASTM B187 / B49.",
            s_condition="annealed (O60) temper",
            s_confidence="standard",
            s_notes=(
                "Annealed OFE Cu (C10100) UTS = 32 ksi (220 MPa). Cold-worked "
                "tempers reach 38-50 ksi (260-345 MPa). The 220 MPa value is "
                "the soft-annealed reference state matching the yield_stress "
                "/ youngs_modulus / density entries here."
            ),
        ),
        fatigue_endurance=_PV(
            d_value=80e6,
            s_units="Pa",
            s_source="Shigley's Mechanical Engineering Design 10e Table A-20, "
            "annealed Cu rotating beam R=-1",
            s_condition="10^7 cycles, rotating beam, R=-1",
            s_confidence="standard",
        ),
        density=_PV(
            d_value=8940.0,
            s_units="kg/m^3",
            s_source="Copper Development Association (CDA), 'C10100 Oxygen Free "
            "Electronic Copper / OFE' alloy spec sheet, Physical "
            "Properties table (specific gravity 8.94, 0.323 lb/in^3 "
            "at 68 degF), retrieved 2026-05-24 from "
            "https://alloys.copper.org/alloy/C10100",
            s_condition="20 C, annealed",
            s_confidence="standard",
        ),
    ),
    electromagnetic=Electromagnetic(
        resistivity_at_20C=_PV(
            d_value=1.707e-8,
            s_units="Ohm*m",
            s_source="Copper Development Association (CDA), 'C10100 OFE' "
            "alloy spec lists annealed C10100 as 101% IACS; "
            "the IACS reference is anchored to NIST/NBS Circular "
            "No. 73 (1914 ed.) 'international annealed copper "
            "standard' = 0.017241 Ohm*mm^2/m at 20 C (100% IACS = "
            "1.7241e-8 Ohm*m); 101% IACS = 1.7241e-8 / 1.01 = "
            "1.707e-8 Ohm*m. Retrieved 2026-05-24 from "
            "https://alloys.copper.org/alloy/C10100 and "
            "https://nvlpubs.nist.gov/nistpubs/Legacy/circ/"
            "nbscircular73e2.pdf",
            s_condition="20 C, annealed, 101% IACS conductivity (58.6 MS/m)",
            s_confidence="standard",
        ),
        temp_coeff_resistivity=_PV(
            d_value=3.93e-3,
            s_units="1/K",
            s_source="CRC Handbook of Chemistry and Physics -- temperature "
            "coefficient of resistivity for annealed copper at 20 C; "
            "consistent across editions",
            s_condition="linear model, 20-200 C",
            s_confidence="standard",
        ),
        relative_permeability=_PV(
            d_value=0.999994,
            s_units="",
            s_source=_CRC_HANDBOOK_MAGNETICS + " -- Cu is diamagnetic with mu_r = 0.999994 at 20 C "
            "(derived from chi_mol = -5.46e-6 cm^3/mol per Section 12 "
            "table of element magnetic susceptibilities, mu_r = "
            "1 + chi_v where chi_v = chi_mol * rho / M).",
            s_condition="20 C, polycrystalline",
            s_confidence="standard",
            s_notes=(
                "Cu is diamagnetic: mu_r is technically <1 (0.999994). For "
                "most engineering EM-FEA purposes Cu is treated as mu_r = 1 "
                "(non-magnetic); the small diamagnetic offset is only "
                "relevant for ultra-precision magnetometry / SQUID / NMR "
                "shielding work. NOTE: the Electromagnetic dataclass "
                "validator currently rejects mu_r < 1.0 (diamagnetics out "
                "of v0.1 scope per electromagnetic.py:90-98); this entry "
                "will fail __post_init__ until the validator is relaxed to "
                "accept diamagnetic mu_r."
            ),
        ),
    ),
    thermal=Thermal(
        thermal_conductivity=_PV(
            d_value=401.0,
            s_units="W/(m*K)",
            s_source="Ho, Powell & Liley, 'Thermal Conductivity of the "
            "Elements,' Journal of Physical and Chemical Reference "
            "Data Vol. 1 No. 2 (NIST JPCRD reprint), 1972 -- Cu "
            "recommended values table for high-purity well-annealed "
            "copper: 4.01 W/(cm*K) at 298.2-300 K = 401 W/(m*K). "
            "Retrieved 2026-05-24 from https://srd.nist.gov/"
            "jpcrdreprint/1.3253100.pdf",
            s_condition="20-27 C, high-purity well-annealed Cu",
            s_confidence="standard",
        ),
        specific_heat=_PV(
            d_value=383.0,
            s_units="J/(kg*K)",
            s_source="White & Collocott, 'Heat Capacity of Reference Materials: "
            "Cu and W,' Journal of Physical and Chemical Reference "
            "Data Vol. 13 No. 4, 1984 -- molar Cp interpolated to "
            "293.15 K = 24.36 J/(mol*K) / 0.063546 kg/mol molar mass "
            "= 383 J/(kg*K). Retrieved 2026-05-24 from "
            "https://srd.nist.gov/jpcrdreprint/1.555728.pdf",
            s_condition="20 C, reference-material Cu",
            s_confidence="standard",
        ),
        thermal_expansion=_PV(
            d_value=16.5e-6,
            s_units="1/K",
            s_source=_CRC_HANDBOOK_PURE_CU + " -- linear CTE of pure Cu at 25 C = 16.5 ppm/K. The "
            "canonical pure-Cu room-temperature linear-CTE value "
            "tabulated by NIST SRD via the CRC Handbook 'Physical "
            "Properties of the Pure Elements' table.",
            s_condition="25 C, polycrystalline pure Cu",
            s_confidence="standard",
        ),
        melting_temp=_PV(
            d_value=1085.0,
            s_units="C",
            s_source=_CRC_HANDBOOK_PURE_CU + " -- Cu melting point = 1084.62 C (IPTS-90 Cu fixed "
            "point, used by NIST as a primary thermometric "
            "calibration). The 1085 C value rounds the IPTS-90 "
            "fixed-point liquidus.",
            s_condition="IPTS-90 fixed-point liquidus, pure Cu",
            s_confidence="standard",
        ),
    ),
    crystal_anisotropy=CrystalAnisotropy(
        s_crystal_structure="FCC",
        c11=_PV(
            d_value=168.4e9,
            s_units="Pa",
            s_source=_OVERTON_GAFFNEY_1955,
            s_condition="300 K single-crystal Cu, ultrasonic measurement",
            s_confidence="standard",
        ),
        c12=_PV(
            d_value=121.4e9,
            s_units="Pa",
            s_source=_OVERTON_GAFFNEY_1955,
            s_condition="300 K single-crystal Cu, ultrasonic measurement",
            s_confidence="standard",
        ),
        c44=_PV(
            d_value=75.4e9,
            s_units="Pa",
            s_source=_OVERTON_GAFFNEY_1955,
            s_condition="300 K single-crystal Cu, ultrasonic measurement",
            s_confidence="standard",
        ),
        burgers_vector=_PV(
            d_value=2.556e-10,
            s_units="m",
            s_source=_OVERTON_GAFFNEY_1955
            + " -- derived: |b| = a0 / sqrt(2) for FCC <110> slip on "
            "{111} planes; with a0 = 3.6149 Angstrom (NIST SRD CRC "
            "Handbook 95th ed Cu lattice parameter at 293 K) "
            "gives |b| = 2.556 Angstrom = 0.2556 nm.",
            s_condition="293 K, FCC <110>{111} slip system",
            s_confidence="standard",
        ),
        stacking_fault_energy=_PV(
            d_value=0.078,
            s_units="J/m^2",
            s_source=_STOBBS_SWORN_1971,
            s_condition="room temperature, pure Cu single crystal, weak-beam TEM",
            s_confidence="measured",
        ),
        crss_initial=_PV(
            d_value=0.4e6,
            s_units="Pa",
            s_source=_FROST_ASHBY_1982,
            s_condition="293 K, well-annealed pure-Cu single crystal, FCC slip activation",
            s_confidence="standard",
            s_notes=(
                "Pure-Cu intrinsic slip-CRSS at room temperature, dominated "
                "by lattice-friction (Peierls-Nabarro) + athermal forest-"
                "dislocation interactions in well-annealed single crystals. "
                "Polycrystalline OFHC Cu yields ~50-70 MPa due to Hall-Petch "
                "grain-boundary strengthening; the 0.4 MPa CRSS here is the "
                "single-crystal slip-system entry value for crystal-plasticity "
                "FEM initial-yield surfaces."
            ),
        ),
    ),
    # v0.6.0 fully populated structural (E, nu, yield, UTS, density, fatigue)
    # from ASM Vol 2 + CDA C10100 annealed-spec, and thermal (k, c_p, CTE,
    # melting_temp) from NIST JPCRD + CRC Handbook. Still missing Tier 1
    # sourcing: thermal.max_operating_temp (Cu loses temper / anneal-softens
    # progressively above ~200 C; no canonical single-scalar "Cu max op temp"
    # in ASM Vol 2). Not yet sourced at Tier 1.
)


# ── Aluminum 6061-T6 ────────────────────────────────────────────────────────

aluminum_6061_t6 = Material(
    s_id="aluminum_6061_t6",
    s_description="AA 6061-T6 / EN AW-6061-T6 aluminum alloy",
    s_category="metal",
    s_specification="AA 6061-T6 (solution heat-treated + artificially aged)",
    s_catalog_version=_S_CATALOG_VERSION,
    s_last_reviewed=_S_LAST_REVIEWED,
    structural=Structural(
        youngs_modulus=_PV(
            d_value=68.9e9,
            s_units="Pa",
            s_source=_ALUMINUM_ADM + " -- Table on elastic moduli: E = 10,000 ksi = 68.9 GPa "
            "(temper-independent for 6061)",
            s_condition="20 C, all tempers",
            s_confidence="standard",
        ),
        poisson_ratio=_PV(
            d_value=0.33,
            s_units="",
            s_source=_ASM_HANDBOOK_VOL2 + " -- 6061 entry ν = 0.33",
            s_confidence="standard",
            s_notes=(
                "Note (v0.2.3 independent audit round 2): NIST-hosted "
                "wrought-aluminum table does NOT include ν for 6061-T6. "
                "ASM Handbook Vol 2 IS the canonical Tier-1 source for "
                "aluminum-alloy mechanical properties and lists 0.33 for "
                "6061; MakeItFrom and AZoM independently report 0.33. "
                "Using 0.33 consensus value across these sources."
            ),
        ),
        yield_stress=_PV(
            d_value=276e6,
            s_units="Pa",
            s_source=_ASTM_B221 + " -- extrusion minimum is 240 MPa; typical mill value "
            "276 MPa (ASM Aerospace digest of Aluminum Association "
            "ADM mill TDS).",
            s_condition="0.2% offset, typical (annealed-aged T6 condition)",
            s_confidence="standard",
            s_notes="ASTM B221 design minimum for extrusion is 240 MPa; this "
            "276 MPa value is the typical-product value reported by "
            "Alcoa/Kaiser mill TDSes. For aerospace design-allowable "
            "(A/B-basis), pull MMPDS, which is a separate followup.",
        ),
        fatigue_endurance=_PV(
            d_value=95e6,
            s_units="Pa",
            s_source="Aluminum Association Aluminum Design Manual Part VII "
            "Table 7-1, sigma_e at 5x10^8 cycles "
            "(aluminum has no true endurance plateau)",
            s_condition="5e8 cycles rotating beam",
            s_confidence="standard",
        ),
        ultimate_tensile=_PV(
            d_value=310e6,
            s_units="Pa",
            s_source=_ASTM_B221 + " -- extrusion minimum is 260 MPa; typical mill value "
            "310 MPa per ASM Aerospace digest.",
            s_condition="typical T6 (mill-tested value, not the spec minimum)",
            s_confidence="standard",
        ),
        density=_PV(
            d_value=2700.0,
            s_units="kg/m^3",
            s_source=_ASM_HANDBOOK_VOL2 + " -- 6061 entry density 2.70 g/cm^3",
            s_confidence="standard",
        ),
    ),
    electromagnetic=Electromagnetic(
        resistivity_at_20C=_PV(
            d_value=3.99e-8,
            s_units="Ohm*m",
            s_source=_ASM_HANDBOOK_VOL2
            + " -- 6061-T6 electrical resistivity 3.99 microhm-cm at 20 C "
            "(40% IACS). Note: pure Al is ~2.65e-8; alloying with "
            "Mg/Si raises 6061-T6 to 3.99e-8.",
            s_condition="20 C, T6 temper",
            s_confidence="standard",
        ),
        temp_coeff_resistivity=_PV(
            d_value=4.3e-3,
            s_units="1/K",
            s_source="CRC Handbook of Chemistry and Physics, "
            "aluminum temperature coefficient of resistivity. "
            "(This is the pure-Al value; 6061-T6 specifically may "
            "differ slightly per MMPDS at ~3.3e-3, but MMPDS is "
            "paywalled, so this remains a followup.)",
            s_condition="linear model, 20-200 C, pure-Al baseline",
            s_confidence="standard",
        ),
        relative_permeability=_PV(
            d_value=1.000022,
            s_units="",
            s_source=_CRC_HANDBOOK_MAGNETICS
            + " -- Al is paramagnetic with mu_r = 1.000022 at 20 C "
            "(derived from chi_mol = +16.5e-6 cm^3/mol per Section 12 "
            "table of element magnetic susceptibilities). This is "
            "the bulk-Al value; the 6061 alloying additions (~1% Mg "
            "+ 0.6% Si + minor Cu/Fe/Cr) do not shift mu_r "
            "meaningfully at this precision.",
            s_condition="20 C, T6 temper",
            s_confidence="standard",
            s_notes=(
                "Al-6061 is essentially non-magnetic; mu_r = 1.000022 is the "
                "bulk paramagnetic value, indistinguishable from 1.0 for "
                "any practical EM-FEA. Listed here for completeness in the "
                "Tier-1 EM property coverage."
            ),
        ),
    ),
    thermal=Thermal(
        thermal_conductivity=_PV(
            d_value=167.0,
            s_units="W/(m*K)",
            s_source=_ASM_HANDBOOK_VOL2 + " -- 6061-T6 k = 167 W/(m*K) at 25 C. Temper-sensitive: "
            "T4 = 154, O = 180 (±8% across tempers).",
            s_condition="25 C, T6 temper",
            s_confidence="standard",
        ),
        specific_heat=_PV(
            d_value=896.0,
            s_units="J/(kg*K)",
            s_source=_ASM_HANDBOOK_VOL2 + " -- 6061 c_p = 0.896 J/(g*K) at 100 C",
            s_condition="100 C",
            s_confidence="standard",
        ),
        thermal_expansion=_PV(
            d_value=23.6e-6,
            s_units="1/K",
            s_source=_ALUMINUM_ADM + " -- Part IV thermal table, 6061 CTE = 23.6 µm/(m*degC) "
            "(20-100 C, temper-independent)",
            s_condition="20-100 C linear CTE",
            s_confidence="standard",
        ),
        melting_temp=_PV(
            d_value=652.0,
            s_units="C",
            s_source=_ASM_HANDBOOK_VOL2 + " -- 6061 liquidus 652 C (solidus 582 C)",
            s_condition="liquidus",
            s_confidence="standard",
        ),
    ),
    crystal_anisotropy=CrystalAnisotropy(
        s_crystal_structure="FCC",
        c11=_PV(
            d_value=107.3e9,
            s_units="Pa",
            s_source=_KAMM_ALERS_1964,
            s_condition="300 K single-crystal Al (pure Al baseline; "
            "alloying offset for 6061 is <3% per Hosford 1972)",
            s_confidence="standard",
        ),
        c12=_PV(
            d_value=60.9e9,
            s_units="Pa",
            s_source=_KAMM_ALERS_1964,
            s_condition="300 K single-crystal Al, ultrasonic measurement",
            s_confidence="standard",
        ),
        c44=_PV(
            d_value=28.3e9,
            s_units="Pa",
            s_source=_KAMM_ALERS_1964,
            s_condition="300 K single-crystal Al, ultrasonic measurement",
            s_confidence="standard",
        ),
        burgers_vector=_PV(
            d_value=2.864e-10,
            s_units="m",
            s_source=_KAMM_ALERS_1964 + " -- derived: |b| = a0 / sqrt(2) for FCC <110> slip on "
            "{111} planes; with a0 = 4.0496 Angstrom (NIST SRD CRC "
            "Handbook Al lattice parameter at 293 K) gives "
            "|b| = 2.864 Angstrom = 0.2864 nm.",
            s_condition="293 K, FCC <110>{111} slip system",
            s_confidence="standard",
        ),
        stacking_fault_energy=_PV(
            d_value=0.166,
            s_units="J/m^2",
            s_source=_CARTER_HOLMES_1977,
            s_condition="room temperature, pure Al single crystal, node-spacing TEM",
            s_confidence="measured",
            s_notes=(
                "Al SFE is roughly 2x Cu's 78 mJ/m^2: this is why Al rarely "
                "deformation-twins: stacking faults are energetically "
                "expensive enough that cross-slip dominates. The 6061 "
                "alloying (~1% Mg + 0.6% Si) shifts SFE by <10% vs pure Al."
            ),
        ),
        # crss_initial intentionally omitted: 6061-T6 yielding is dominated
        # by Mg2Si precipitate strengthening (Orowan looping + shearing of
        # beta'' / beta' precipitates), NOT by slip-system CRSS. Solver
        # consumers wanting the precipitate-strengthened yield should use
        # the structural.yield_stress (276 MPa) instead. The slip-CRSS for
        # solution-treated (T4) or annealed (O temper) 6061 would be
        # meaningful but is not the T6 design value.
    ),
)


# ── Steel 4140 (normalized) ────────────────────────────────────────────────

steel_4140 = Material(
    s_id="steel_4140",
    s_description="AISI 4140 Chromium-Molybdenum alloy steel (normalized)",
    s_category="metal",
    s_specification="AISI 4140, normalized at 870 C (1600 F), air cooled, 25 mm (1 in.) round",
    s_catalog_version=_S_CATALOG_VERSION,
    s_last_reviewed=_S_LAST_REVIEWED,
    structural=Structural(
        youngs_modulus=_PV(
            d_value=205e9,
            s_units="Pa",
            s_source=_ASM_HANDBOOK_VOL1_4140_NORM
            + " -- Modulus of Elasticity = 205 GPa (29,700 ksi). "
            "Cross-check: "
            + _TIMKEN_PRACTICAL_DATA_18
            + " gives 30 x 10^6 psi = 206.84 GPa generic-low-alloy. "
            "ASM Vol 1's 205 GPa is the specific 4140-normalized "
            "value; the +0.9% TimkenSteel generic-steel value is "
            "consistent (heat-to-heat variation in low-alloy "
            "steels).",
            s_condition="20 C, normalized at 870 C, all bar sizes",
            s_confidence="standard",
        ),
        poisson_ratio=_PV(
            d_value=0.29,
            s_units="",
            s_source=_ASM_HANDBOOK_VOL1_4140_NORM
            + " -- Poisson's Ratio = 0.29 (the standard low-alloy-"
            "steel value used by ASM Vol 1 for the entire 4xxx "
            "Cr-Mo family).",
            s_condition="20 C, normalized",
            s_confidence="standard",
        ),
        yield_stress=_PV(
            d_value=655e6,
            s_units="Pa",
            s_source=_ASM_HANDBOOK_VOL1_4140_NORM
            + " -- Tensile Strength Yield = 655 MPa (95,000 psi) at "
            "0.2% offset for the normalized-25mm-round bar.",
            s_condition="0.2% offset, normalized at 870 C, 25 mm round, air cooled",
            s_confidence="standard",
            s_notes=(
                "Bar-diameter dependence: ASM Vol 1 publishes 4140 "
                "normalized values per bar size because air-cooling "
                "rate depends on section thickness. The 25 mm round "
                "value (655 MPa) is the standard 'normalized 4140' "
                "reference for shaft-class section sizes (motor and "
                "actuator shafts typically 10-50 mm OD). For 100 mm "
                "(4 in.) round bar the same ASM Vol 1 table reports "
                "yield 415 MPa (slower core cooling); for 13 mm round "
                "yield runs higher than 655 MPa due to faster cooling. "
                "If your application is large-section 4140 (>=75 mm), "
                "consult ASM Vol 1's bar-size-specific table directly. "
                "Annealed 4140 (815 C furnace cool) is even softer: "
                "yield ~415 MPa, UTS ~655 MPa: that is a separate "
                "ASM Vol 1 table entry and NOT the normalized condition."
            ),
        ),
        fatigue_endurance=_PV(
            d_value=380e6,
            s_units="Pa",
            s_source="Shigley's Mechanical Engineering Design 10e Table A-20 + "
            "ASM Handbook Vol 19 'Fatigue and Fracture', "
            "normalized 4140 rotating-beam R=-1",
            s_condition="rotating-beam R=-1, 10^7 cycles",
            s_confidence="standard",
        ),
        ultimate_tensile=_PV(
            d_value=1020e6,
            s_units="Pa",
            s_source=_ASM_HANDBOOK_VOL1_4140_NORM
            + " -- Tensile Strength Ultimate = 1020 MPa (148,000 psi) "
            "for the normalized-25mm-round bar.",
            s_condition="normalized at 870 C, 25 mm round, air cooled",
            s_confidence="standard",
            s_notes=(
                "Same bar-diameter dependence as yield_stress: ASM Vol 1's "
                "1020 MPa is the 25mm-round normalized value. The 100mm-"
                "round normalized variant has UTS ~655 MPa. Annealed 4140 "
                "(815 C furnace cool) has UTS ~655 MPa as well: that is a "
                "different ASM Vol 1 row, not the normalized condition."
            ),
        ),
        density=_PV(
            d_value=7850.0,
            s_units="kg/m^3",
            s_source=_ASM_HANDBOOK_VOL1_4140_NORM
            + " -- Density = 7.85 g/cc (0.284 lb/in^3). Cross-check: "
            + _TIMKEN_PRACTICAL_DATA_18
            + " gives 0.283 lb/in^3 = 7840 kg/m^3 generic-low-alloy. "
            "Within 0.1%; using ASM Vol 1's 7850 kg/m^3 4140-"
            "specific value.",
            s_condition="20 C, normalized",
            s_confidence="standard",
        ),
    ),
    thermal=Thermal(
        thermal_conductivity=_PV(
            d_value=42.6,
            s_units="W/(m*K)",
            s_source=_ASM_HANDBOOK_VOL1_4140_NORM
            + " -- Thermal Conductivity at 100 C (212 F) = 42.6 W/(m*K) "
            "(296 BTU-in/hr-ft^2-F). ASM Vol 1's tabulated k(T) for "
            "normalized 4140: 42.6 at 100 C, 42.2 at 200 C, 37.7 at "
            "400 C, 33.0 at 600 C. Use this 100 C value for "
            "running-temperature motor/actuator thermal models; "
            "extrapolation to 25 C gives ~42.7 W/(m*K) (k(T) curve "
            "is nearly flat between 25-100 C for ferritic-bainitic "
            "low-alloy steels).",
            s_condition="100 C (212 F), normalized",
            s_confidence="standard",
        ),
        specific_heat=_PV(
            d_value=473.0,
            s_units="J/(kg*K)",
            s_source=_ASM_HANDBOOK_VOL1_4140_NORM
            + " -- Specific Heat Capacity at 150-200 C (302-392 F) = "
            "0.473 J/(g*K) = 473 J/(kg*K). ASM Vol 1's tabulated "
            "c_p(T) for normalized 4140: 0.473 J/(g*K) at 150-200 C, "
            "0.519 at 350-400 C, 0.561 at 550-600 C. Use this 150-"
            "200 C value for running-temperature motor thermal "
            "models; ambient (25 C) c_p is slightly lower (~450 "
            "J/(kg*K)) but ASM Vol 1 does not publish a sub-100 C "
            "value in this row.",
            s_condition="150-200 C (302-392 F) mean, normalized",
            s_confidence="standard",
        ),
        max_operating_temp=_PV(
            d_value=500.0,
            s_units="C",
            s_source="ASM Handbook Vol 1 - 4140 working temperature range "
            "(continuous service without significant temper loss; "
            "tempering temperature 540-650 C)",
            s_condition="continuous service",
            s_confidence="standard",
        ),
        thermal_expansion=_PV(
            d_value=12.2e-6,
            s_units="1/K",
            s_source=_ASM_HANDBOOK_VOL1_4140_NORM
            + " -- CTE linear at 0-100 C (32-212 F) = 12.2 um/(m*C) = "
            "12.2e-6 /K. ASM Vol 1's tabulated CTE(T) for normalized "
            "4140: 12.2e-6 at 0-100 C, 13.7e-6 at 20-400 C, 14.6e-6 "
            "at 20-600 C (CTE rises with interval upper bound -- "
            "standard ferritic-low-alloy-steel behavior).",
            s_condition="0-100 C mean linear CTE, normalized",
            s_confidence="standard",
        ),
        curie_temp=_PV(
            d_value=770.0,
            s_units="C",
            s_source=_BOZORTH_FERROMAGNETISM
            + " -- Curie temperature for ferritic low-alloy steels "
            "(4140, 4340, AISI 4xxx Cr-Mo family) = 770 C, the "
            "pure alpha-Fe Curie point. Cr/Mo/Ni additions at the "
            "wt-percent level perturb T_c by less than 10 C and "
            "the standard engineering value is the pure-Fe one. "
            "Cross-referenced by ASM Handbook Vol 1 magnetic-"
            "properties tables for the Cr-Mo low-alloy family.",
            s_condition="ferritic alpha-Fe matrix, 4140 normalized",
            s_confidence="standard",
            s_notes=(
                "Above T_c (770 C), 4140 transitions from ferromagnetic to "
                "paramagnetic and saturation flux density collapses to zero. "
                "Note: the alpha->gamma (BCC->FCC) phase transition at 912 C "
                "in pure Fe is shifted by 4140 alloying additions; the "
                "ferromagnetic-paramagnetic transition (T_c) and the "
                "structural alpha-gamma transition (A3 line) are distinct."
            ),
        ),
        # melting_temp remains None: ASM Vol 1 normalized-4140 row does NOT
        # publish solidus/liquidus. ASM Ready Reference Thermal Properties
        # of Metals Table 5.3 (Melting Range for Noneutectic Alloys, p.492)
        # is the canonical Tier 1 source for 4140 liquidus but is paywalled
        # (TOC only retrieved 2026-05-24). The 1416 C / 2580 F value cited
        # by aggregators (MatWeb, MakeItFrom) lacks a verified primary
        # citation. Not yet sourced at Tier 1.
    ),
    crystal_anisotropy=CrystalAnisotropy(
        # alpha-Fe (BCC ferrite) single-crystal C_ij. 4140 in service is
        # tempered martensite, NOT equilibrium alpha-Fe; see s_notes on
        # each PropertyValue and the module-level docstring on Material.
        # These values are appropriate for FEM elastic-anisotropy-of-the-
        # ferrite-matrix studies only.
        s_crystal_structure="BCC",
        c11=_PV(
            d_value=231.4e9,
            s_units="Pa",
            s_source=_RAYNE_CHANDRASEKHAR_1961,
            s_condition="300 K single-crystal alpha-Fe (BCC ferrite), ultrasonic measurement",
            s_confidence="standard",
            s_notes=(
                "alpha-Fe single-crystal value. 4140 in tempered-martensite "
                "state has lath/packet microstructure that dominates yield; "
                "the elastic stiffness of the ferrite matrix is what the C_ij "
                "values describe. Use for FEM elastic-anisotropy-of-ferrite-"
                "matrix studies only, NOT as a plasticity-CRSS proxy."
            ),
        ),
        c12=_PV(
            d_value=134.7e9,
            s_units="Pa",
            s_source=_RAYNE_CHANDRASEKHAR_1961,
            s_condition="300 K single-crystal alpha-Fe, ultrasonic measurement",
            s_confidence="standard",
        ),
        c44=_PV(
            d_value=116.4e9,
            s_units="Pa",
            s_source=_RAYNE_CHANDRASEKHAR_1961,
            s_condition="300 K single-crystal alpha-Fe, ultrasonic measurement",
            s_confidence="standard",
        ),
        burgers_vector=_PV(
            d_value=2.483e-10,
            s_units="m",
            s_source=_RAYNE_CHANDRASEKHAR_1961
            + " + "
            + _FROST_ASHBY_FE_BCC
            + " -- derived: |b| = a0 * sqrt(3) / 2 for BCC <111> slip "
            "on {110}/{112}/{123} planes; with a0 = 2.8665 Angstrom "
            "(CRC Handbook alpha-Fe lattice parameter at 293 K) "
            "gives |b| = 2.483 Angstrom = 0.2483 nm.",
            s_condition="293 K, BCC <111> slip direction",
            s_confidence="standard",
        ),
        # stacking_fault_energy intentionally omitted: BCC slip is not
        # controlled by a stable stacking fault on a single close-packed
        # plane the way FCC slip is. BCC plasticity is screw-dislocation /
        # kink-pair dominated; "gamma_SFE" is not the canonical parameter.
        # crss_initial intentionally omitted: 4140 tempered-martensite
        # yielding is dominated by lath/packet boundary strengthening and
        # carbide pinning, NOT slip-CRSS. Solver consumers should use
        # structural.yield_stress (655 MPa).
    ),
)


# ── Stainless 304 ──────────────────────────────────────────────────────────

stainless_304 = Material(
    s_id="stainless_304",
    s_description="AISI 304 austenitic stainless steel (annealed)",
    s_category="metal",
    s_specification="AISI 304 / UNS S30400 / EN 1.4301, annealed",
    s_catalog_version=_S_CATALOG_VERSION,
    s_last_reviewed=_S_LAST_REVIEWED,
    structural=Structural(
        youngs_modulus=_PV(
            d_value=193e9,
            s_units="Pa",
            s_source=_AK_STEEL_304_PDS
            + " -- Modulus of Elasticity 28.0 x 10^3 ksi (193 x 10^3 MPa) "
            "in tension",
            s_condition="20 C, annealed",
            s_confidence="datasheet",
            s_notes=(
                "Tier-1 cross-check (v0.2.3, independent audit round 2): "
                "Outokumpu Core 304/4301 mill TDS lists E = 200 GPa for the "
                "same annealed grade. Both values are Tier 1 datasheet from "
                "major mills; the 193-200 GPa span is real heat-to-heat / "
                "mill-to-mill variation in austenitic stainless. Using AK "
                "Steel's 193 GPa as the conservative-stiffness scalar. "
                "Engineers expecting ~2% under-prediction of stiffness can "
                "swap to 200 GPa."
            ),
        ),
        poisson_ratio=_PV(
            d_value=0.29,
            s_units="",
            s_source="ASM Handbook Vol 1 austenitic-stainless section ν = 0.29 "
            "(matched by ASM matweb digest mq304a)",
            s_confidence="standard",
            s_notes=(
                "Note (v0.2.3 independent audit): Outokumpu Core 304 mill "
                "TDS does NOT publish Poisson's ratio. AZoM Grade 304 page "
                "lists 0.265-0.275; ASM Handbook lists 0.29; MakeItFrom "
                "lists 0.29. Using 0.29 as the consensus austenitic value."
            ),
        ),
        yield_stress=_PV(
            d_value=205e6,
            s_units="Pa",
            s_source=_ASTM_A240 + " -- yield minimum for 304 annealed plate/sheet = 205 MPa. "
            "Typical mill value 290 MPa; using A240 spec minimum for "
            "engineering-safe design.",
            s_condition="annealed, 0.2% offset, ASTM A240 minimum",
            s_confidence="standard",
            s_notes=(
                "Tier-1 cross-check (v0.2.3 independent audit round 2): "
                "Outokumpu Core 304/4301 mill TDS Table 5 lists product-form-"
                "specific Rp0.2: 230 MPa cold-rolled sheet/coil, 210 MPa "
                "hot-rolled/plate. AK Steel reports typical mill 290 MPa. "
                "All three sources exceed the ASTM A240 minimum of 205 MPa "
                "used here. Use 205 MPa for conservative design allowables; "
                "use the form-specific Outokumpu values for tighter material-"
                "limited optimization."
            ),
        ),
        fatigue_endurance=_PV(
            d_value=240e6,
            s_units="Pa",
            s_source="ASM Handbook Vol 19, austenitic 304 at 10^7 cycles "
            "(no true endurance limit; ~0.47 x sigma_uts at 515 MPa UTS)",
            s_condition="10^7 cycles, rotating beam",
            s_confidence="standard",
        ),
        ultimate_tensile=_PV(
            d_value=515e6,
            s_units="Pa",
            s_source=_ASTM_A240 + " -- UTS minimum for 304 annealed = 515 MPa. Typical mill "
            "value 621 MPa.",
            s_condition="annealed, ASTM A240 minimum",
            s_confidence="standard",
            s_notes=(
                "Tier-1 cross-check (v0.2.3): Outokumpu Core 304 Table 5 "
                "lists 540-750 MPa cold-rolled / 520-720 MPa hot-rolled "
                "(product-form-specific UTS ranges). AK Steel typical 621 "
                "MPa. All exceed the ASTM A240 minimum of 515 MPa used here."
            ),
        ),
        density=_PV(
            d_value=8030.0,
            s_units="kg/m^3",
            s_source=_AK_STEEL_304_PDS + " -- Density 0.29 lbs/in^3 = 8.03 g/cm^3 (PDS PHYSICAL "
            "PROPERTIES section).",
            s_confidence="datasheet",
            s_notes=(
                "v0.7.3 manual verification: changed from 8000 (a "
                "'round midpoint' between AK Steel 8030 and Atlas/"
                "Outokumpu 7900) to 8030 (the AK Steel PDS-direct "
                "value). Tier-1 strict: store what the cited source "
                "publishes. Atlas Steels mill TDS lists 7900, "
                "Outokumpu Core 304 lists 7900; real austenitic 304 "
                "varies 7900-8030 across mills. AK Steel 304 PDS row "
                "(this catalog's primary cite) publishes 8.03 g/cm^3 "
                "= 8030 kg/m^3, which is now stored exactly."
            ),
        ),
    ),
    electromagnetic=Electromagnetic(
        resistivity_at_20C=_PV(
            d_value=7.2e-7,
            s_units="Ohm*m",
            s_source=_AK_STEEL_304_PDS + " -- Electrical Resistivity 28.4 microhm-in at 68°F = "
            "72 microhm-cm at 20 C = 7.2e-7 Ohm-m",
            s_condition="20 C, annealed",
            s_confidence="datasheet",
        ),
        # v0.7.2: temp_coeff_resistivity REMOVED. The v0.7.0 value 1.02e-3 /K
        # was derived from a claimed "108 µΩ·cm at 500 C" PDS row that the
        # v0.7.2 URL-fetch validation could not find: the AK Steel 304 PDS
        # actually publishes only two ρ(T) anchor points (20 C → 72 µΩ·cm;
        # 659 C → 116 µΩ·cm), so a 2-point linear slope is ~0.96e-3 /K
        # (not 1.02e-3), and that's a derivation, not a TDS-published
        # scalar. Under strict Tier-1, the field is removed. Not yet sourced at Tier 1.
        relative_permeability=_PV(
            d_value=1.02,
            s_units="",
            s_source=_AK_STEEL_304_PDS + " -- Magnetic Permeability annealed, H = 200 Oe: 1.02 max "
            "(austenitic; cold-work induces strain-induced martensite "
            "and raises mu_r substantially -- annealed-only value)",
            s_condition="annealed only, H = 200 Oe (15.9 kA/m)",
            s_confidence="datasheet",
            s_notes="Cold work can induce alpha'-martensite that raises mu_r "
            "above 1.5 for heavily-worked 304. For motor applications "
            "where the part is welded/formed/machined, treat 304 as "
            "weakly ferromagnetic and measure mu_r for the specific "
            "lot+process condition.",
        ),
    ),
    thermal=Thermal(
        thermal_conductivity=_PV(
            d_value=16.2,
            s_units="W/(m*K)",
            s_source=_AK_STEEL_304_PDS
            + " -- at 212°F (100°C): 9.4 BTU/(hr*ft^2*ft*°F) = 16.2 W/(m*K)",
            s_condition="100 C",
            s_confidence="datasheet",
            s_notes=(
                "Tier-1 cross-check (v0.2.3): Outokumpu Core 304 mill TDS "
                "lists k = 15 W/(m*K) at 20 C: the +8% delta vs this 16.2 "
                "value is the genuine 20 C -> 100 C k(T) rise (austenitic "
                "stainless k rises with T). Use 15 W/(m*K) at 20 C for "
                "ambient FEM; 16.2 at 100 C for running-temp models."
            ),
        ),
        specific_heat=_PV(
            d_value=500.0,
            s_units="J/(kg*K)",
            s_source=_AK_STEEL_304_PDS
            + " -- 32-212°F (0-100°C): 0.12 BTU/(lb*°F) = 0.50 kJ/(kg*K)",
            s_condition="0-100 C mean",
            s_confidence="datasheet",
        ),
        max_operating_temp=_PV(
            d_value=899.0,
            s_units="C",
            s_source=_AK_STEEL_304_PDS + " -- OXIDATION RESISTANCE section: 'maximum temperature "
            "to which Types 304 and 304L can be exposed continuously "
            "without appreciable scaling is about 1650°F (899°C). "
            "For intermittent exposure, the maximum exposure "
            "temperature is about 1500°F (816°C).'",
            s_condition="continuous oxidizing service, no appreciable scaling",
            s_confidence="datasheet",
            s_notes=(
                "v0.7.3 manual verification: changed from 870 C (cited "
                "vaguely to 'ASM Handbook - 304 SS max continuous "
                "service') to 899 C (AK Steel PDS direct). The PDS "
                "publishes 1650°F = 899°C for continuous, 1500°F = "
                "816°C for intermittent. 870 was an arbitrary midpoint "
                "without a clear Tier-1 anchor."
            ),
        ),
        thermal_expansion=_PV(
            d_value=16.9e-6,
            s_units="1/K",
            s_source=_AK_STEEL_304_PDS + " -- Mean CTE 32-212°F (0-100°C) = 9.4 × 10⁻⁶/°F = "
            "16.9 μm/(m·K). Higher-T intervals also published: "
            "17.3e-6 (0-315 C), 18.4e-6 (0-538 C), 18.7e-6 "
            "(0-649 C).",
            s_condition="0-100 C mean linear CTE",
            s_confidence="datasheet",
            s_notes=(
                "v0.7.3 manual verification: changed from 17.2e-6 "
                "(cited to Atlas Steels compilation) to 16.9e-6 (AK "
                "Steel PDS direct value, same 0-100 C interval). "
                "Tier-1 strict: store the AK-Steel-PDS-direct value "
                "since AK Steel PDS is the catalog's primary cite for "
                "other SS304 PVs. Outokumpu Core 304 mill TDS lists "
                "16.0e-6 over 20-100 C (different interval, real "
                "mill-to-mill variation in austenitic-stainless CTE)."
            ),
        ),
        melting_temp=_PV(
            d_value=1454.0,
            s_units="C",
            s_source=_AK_STEEL_304_PDS + " -- Melting Range: 2550-2650 F (1399-1454 C) for "
            "304/304L per the AK Steel 304 PDS. Liquidus is the "
            "upper bound (1454 C), solidus is the lower bound "
            "(1399 C). The catalog stores the liquidus; "
            "incipient-melting onset is at the solidus.",
            s_condition="liquidus, AK Steel 304 PDS melting range upper bound",
            s_confidence="datasheet",
            s_notes=(
                "v0.7.2 CORRECTED: v0.7.0 stored 1450 C and labeled it "
                "'solidus, ... upper bound', which is incoherent (solidus "
                "is the LOWER bound, liquidus the UPPER). The PDS "
                "publishes 2550-2650 F = 1399-1454 C; catalog now stores "
                "the actual liquidus (1454)."
            ),
        ),
    ),
    crystal_anisotropy=CrystalAnisotropy(
        # FCC gamma-Fe austenitic matrix. C_ij from polycrystal aggregate
        # inversion (Ledbetter 1984); SFE from direct TEM/XRD measurement
        # on commercial 304 (Schramm & Reed 1975).
        s_crystal_structure="FCC",
        c11=_PV(
            d_value=197e9,
            s_units="Pa",
            s_source=_LEDBETTER_1984,
            s_condition="300 K, 304 austenitic gamma-Fe matrix, single-crystal",
            s_confidence="standard",
        ),
        c12=_PV(
            d_value=122e9,
            s_units="Pa",
            s_source=_LEDBETTER_1984,
            s_condition="300 K, 304 austenitic gamma-Fe matrix",
            s_confidence="standard",
        ),
        c44=_PV(
            d_value=124e9,
            s_units="Pa",
            s_source=_LEDBETTER_1984,
            s_condition="300 K, 304 austenitic gamma-Fe matrix",
            s_confidence="standard",
        ),
        burgers_vector=_PV(
            d_value=2.535e-10,
            s_units="m",
            s_source=_LEDBETTER_1984 + " -- derived: |b| = a0 / sqrt(2) for FCC <110> slip on "
            "{111} planes; with gamma-Fe a0 = 3.585 Angstrom "
            "(304 lattice parameter ~equal to pure gamma-Fe at 300 K "
            "per Ledbetter compilation) gives |b| = 2.535 Angstrom.",
            s_condition="293 K, FCC <110>{111} slip system, gamma-Fe matrix",
            s_confidence="standard",
        ),
        stacking_fault_energy=_PV(
            d_value=0.021,
            s_units="J/m^2",
            s_source=_SCHRAMM_REED_1975,
            s_condition="room temperature, commercial 304 SS, XRD line-"
            "broadening + direct TEM node-spacing",
            s_confidence="measured",
            s_notes=(
                "Low SFE (21 mJ/m^2) drives mechanical twinning and TRIP "
                "(transformation-induced plasticity to alpha'-martensite) "
                "at moderate plastic strain in 304: this is the metallurgical "
                "explanation for 304's high strain-hardening rate and high "
                "uniform elongation vs precipitation-hardenable stainless "
                "grades. Mo addition in 316 raises SFE ~4x; see 316 entry."
            ),
        ),
        # crss_initial intentionally omitted: 304 yielding is dominated by
        # solid-solution strengthening (Cr + Ni + N + Mn) + cold-work history;
        # not a pure-metal slip-CRSS material. Solver consumers should use
        # structural.yield_stress (205 MPa ASTM A240 minimum).
    ),
)


# ── Stainless 316 ──────────────────────────────────────────────────────────

stainless_316 = Material(
    s_id="stainless_316",
    s_description="AISI 316 austenitic stainless steel (annealed)",
    s_category="metal",
    s_specification="AISI 316 / UNS S31600 / EN 1.4401, annealed",
    s_catalog_version=_S_CATALOG_VERSION,
    s_last_reviewed=_S_LAST_REVIEWED,
    structural=Structural(
        youngs_modulus=_PV(
            d_value=193e9,
            s_units="Pa",
            s_source=_AK_STEEL_316_PDS
            + " -- Modulus of Elasticity 28.0 x 10^3 ksi (193 x 10^3 MPa) "
            "in tension",
            s_condition="20 C, annealed",
            s_confidence="datasheet",
            s_notes=(
                "Tier-1 cross-check (v0.2.3): Outokumpu Supra 316/4401 mill "
                "TDS lists E = 200 GPa. Both Tier 1; using AK Steel's 193 "
                "GPa as the conservative-stiffness scalar (same convention "
                "as stainless_304; see note there)."
            ),
        ),
        poisson_ratio=_PV(
            d_value=0.29,
            s_units="",
            s_source="ASM Handbook Vol 1 austenitic-stainless section ν = 0.29 "
            "(AZoM Grade 316 page reports 0.265-0.275 range; using "
            "0.29 as the standard austenitic value)",
            s_confidence="standard",
            s_notes=(
                "Note (v0.2.3): Outokumpu Supra 316 mill TDS does NOT "
                "publish Poisson's ratio. ASM Handbook lists 0.29; AZoM "
                "lists 0.265-0.275. Using 0.29 consensus value."
            ),
        ),
        yield_stress=_PV(
            d_value=205e6,
            s_units="Pa",
            s_source=_ASTM_A240 + " -- yield minimum for 316 annealed plate/sheet = 205 MPa. "
            "Typical mill value 290 MPa.",
            s_condition="annealed, 0.2% offset, ASTM A240 minimum",
            s_confidence="standard",
            s_notes=(
                "Tier-1 cross-check (v0.2.3 independent audit round 2): "
                "Outokumpu Supra 316/4401 mill TDS Table 5 lists product-"
                "form-specific Rp0.2: 240 MPa cold-rolled sheet, 220 MPa "
                "hot-rolled/plate. All exceed the ASTM A240 minimum of "
                "205 MPa used here (same convention as stainless_304)."
            ),
        ),
        fatigue_endurance=_PV(
            d_value=255e6,
            s_units="Pa",
            s_source="ASM Handbook Vol 19 Fig. 13, annealed 316 at 10^7 cycles",
            s_condition="10^7 cycles, rotating beam",
            s_confidence="standard",
        ),
        ultimate_tensile=_PV(
            d_value=515e6,
            s_units="Pa",
            s_source=_ASTM_A240 + " -- UTS minimum for 316 annealed = 515 MPa. Typical mill "
            "value 627 MPa.",
            s_condition="annealed, ASTM A240 minimum",
            s_confidence="standard",
            s_notes=(
                "Tier-1 cross-check (v0.2.3): Outokumpu Supra 316 Table 5 "
                "lists 530-680 MPa cold/hot rolled / 520-670 MPa plate "
                "(product-form-specific UTS ranges). All exceed ASTM A240 "
                "minimum of 515 MPa used here."
            ),
        ),
        density=_PV(
            d_value=7990.0,
            s_units="kg/m^3",
            s_source=_AK_STEEL_316_PDS + " -- Density 0.29 lbs/in^3 = 7.99 g/cm^3 (PDS PHYSICAL "
            "PROPERTIES table).",
            s_confidence="datasheet",
            s_notes=(
                "v0.7.3 manual verification: changed from 8000 (with "
                "note about 'Atlas = 8000, UPM = 8027') to 7990 (AK "
                "Steel PDS-direct value, 7.99 g/cm^3 = 7990 kg/m^3). "
                "Tier-1 strict: store what the cited PDS publishes. "
                "316 is denser than 304 because of Mo addition; 316 "
                "literature spread is 7.95-8.03 across mills."
            ),
        ),
    ),
    electromagnetic=Electromagnetic(
        resistivity_at_20C=_PV(
            d_value=7.4e-7,
            s_units="Ohm*m",
            s_source=_AK_STEEL_316_PDS + " -- Electrical Resistivity 29.4 microhm-in at 68°F = "
            "74 microhm-cm at 20 C = 7.4e-7 Ohm-m. Higher than 304 "
            "due to Mo content.",
            s_condition="20 C, annealed",
            s_confidence="datasheet",
        ),
        # v0.7.2: temp_coeff_resistivity REMOVED. The v0.7.0 value 0.94e-3
        # was derived from a claimed "109 µΩ·cm at 500 C" PDS row that the
        # v0.7.2 URL-fetch validation could not find: the AK Steel 316 PDS
        # actually publishes only ONE ρ(T) anchor point (20 C → 74 µΩ·cm),
        # so a temperature coefficient cannot be derived from this source
        # at all. Under strict Tier-1, the field is removed. Not yet sourced at Tier 1
        # (would need a NIST or ASM Vol 1 ρ(T) curve).
        relative_permeability=_PV(
            d_value=1.02,
            s_units="",
            s_source=_AK_STEEL_316_PDS + " -- Magnetic Permeability annealed, H = 200 Oe: 1.02 max",
            s_condition="annealed only, H = 200 Oe",
            s_confidence="datasheet",
            s_notes="Like 304, cold work can induce alpha'-martensite raising "
            "mu_r above 1.5. Annealed 316 is more stable against "
            "strain-induced ferromagnetism than 304 due to higher Ni+Mo.",
        ),
    ),
    thermal=Thermal(
        thermal_conductivity=_PV(
            d_value=16.2,
            s_units="W/(m*K)",
            s_source=_AK_STEEL_316_PDS
            + " -- at 212°F (100°C): 9.4 BTU·(hr·ft²·°F)⁻¹·ft = 16.2 W/(m*K)",
            s_condition="100 C",
            s_confidence="datasheet",
            s_notes=(
                "Tier-1 cross-check (v0.2.3): Outokumpu Supra 316 mill TDS "
                "lists k = 15 W/(m*K) at 20 C: same +8% austenitic k(T) "
                "rise as 304. Use 15 W/(m*K) for ambient FEM; 16.2 for "
                "running-temp models."
            ),
        ),
        specific_heat=_PV(
            d_value=500.0,
            s_units="J/(kg*K)",
            s_source=_AK_STEEL_316_PDS + " -- 0-100°C: 0.12 BTU/(lb·°F) = 0.50 kJ/(kg·K)",
            s_condition="0-100 C mean",
            s_confidence="datasheet",
        ),
        max_operating_temp=_PV(
            d_value=870.0,
            s_units="C",
            s_source="ASM Handbook - 316 SS max continuous service temperature",
            s_condition="continuous oxidizing service",
            s_confidence="standard",
        ),
        thermal_expansion=_PV(
            d_value=16.0e-6,
            s_units="1/K",
            s_source=_AK_STEEL_316_PDS + " -- Mean CTE 32-212°F (0-100°C) = 8.9 × 10⁻⁶/°F = "
            "16.0 μm/(m·K). Higher-T intervals also published: "
            "16.2e-6 (0-315 C), 17.5e-6 (0-538 C), 18.5e-6 "
            "(0-649 C).",
            s_condition="0-100 C mean linear CTE",
            s_confidence="datasheet",
            s_notes=(
                "v0.7.3 manual verification: changed from 15.9e-6 "
                "(Atlas Steels compilation) to 16.0e-6 (AK Steel PDS "
                "direct value, same 0-100 C interval). Outokumpu Supra "
                "316 mill TDS also lists 16.0e-6 over 20-100 C, both "
                "Tier-1 primaries agree, no need to cite Atlas "
                "secondary. 316 CTE is ~0.9 ppm/K lower than 304 "
                "(16.0 vs 16.9 e-6) due to Mo addition stiffening the "
                "FCC lattice."
            ),
        ),
        melting_temp=_PV(
            d_value=1399.0,
            s_units="C",
            s_source=_AK_STEEL_316_PDS + " -- Melting Range: 2500-2550 F (1371-1399 C) for "
            "316/316L per the AK Steel 316 PDS. Liquidus is "
            "the upper bound (1399 C), solidus the lower "
            "bound (1371 C). The catalog stores the liquidus.",
            s_condition="liquidus, AK Steel 316 PDS melting range upper bound",
            s_confidence="datasheet",
            s_notes=(
                "v0.7.2 CORRECTED: v0.7.0 stored 1400 C and labeled it "
                "'solidus, ... upper bound', which is incoherent (solidus "
                "is the LOWER bound, liquidus the UPPER). The actual PDS "
                "publishes 2500-2550 F = 1371-1399 C; catalog now stores "
                "the actual liquidus (1399). 316 melts ~55 C lower than "
                "304 due to Mo addition broadening the solidification "
                "range."
            ),
        ),
    ),
    crystal_anisotropy=CrystalAnisotropy(
        # FCC gamma-Fe austenitic matrix; Mo addition slightly stiffens C_ij
        # vs 304 and significantly raises stacking fault energy (Schramm-Reed
        # 1975: 304 = 21 mJ/m^2, 316 = 78 mJ/m^2, Mo suppresses strain-
        # induced alpha'-martensite, which is why 316 is less work-hardening
        # at high strain than 304).
        s_crystal_structure="FCC",
        c11=_PV(
            d_value=204e9,
            s_units="Pa",
            s_source=_LEDBETTER_1984,
            s_condition="300 K, 316 austenitic gamma-Fe matrix (Mo-stabilized)",
            s_confidence="standard",
            s_notes=(
                "316 is slightly stiffer than 304 (C11 = 204 vs 197 GPa) due "
                "to Mo solid-solution strengthening of the gamma-Fe matrix."
            ),
        ),
        c12=_PV(
            d_value=133e9,
            s_units="Pa",
            s_source=_LEDBETTER_1984,
            s_condition="300 K, 316 austenitic gamma-Fe matrix",
            s_confidence="standard",
        ),
        c44=_PV(
            d_value=126e9,
            s_units="Pa",
            s_source=_LEDBETTER_1984,
            s_condition="300 K, 316 austenitic gamma-Fe matrix",
            s_confidence="standard",
        ),
        burgers_vector=_PV(
            d_value=2.535e-10,
            s_units="m",
            s_source=_LEDBETTER_1984 + " -- derived: |b| = a0 / sqrt(2) for FCC <110>{111} slip; "
            "316 lattice parameter is statistically indistinguishable "
            "from 304 at room T (Mo addition shifts a0 by <0.1% per "
            "Ledbetter 1984), so |b| = 2.535 Angstrom is used for "
            "both grades.",
            s_condition="293 K, FCC <110>{111} slip system, gamma-Fe matrix",
            s_confidence="standard",
        ),
        stacking_fault_energy=_PV(
            d_value=0.078,
            s_units="J/m^2",
            s_source=_SCHRAMM_REED_1975,
            s_condition="room temperature, commercial 316 SS, XRD line-"
            "broadening + direct TEM node-spacing",
            s_confidence="measured",
            s_notes=(
                "316 SFE (78 mJ/m^2) is ~4x higher than 304 (21 mJ/m^2). Mo "
                "addition raises SFE which suppresses strain-induced "
                "alpha'-martensite: this is why 316 has lower strain "
                "hardening + lower TRIP propensity vs 304. Same numerical "
                "value as pure Cu by coincidence."
            ),
        ),
        # crss_initial intentionally omitted: same rationale as 304 (alloy
        # solid-solution-dominated yielding, not slip-CRSS-dominated).
    ),
)


# ── Titanium Ti-6Al-4V (Grade 5) ───────────────────────────────────────────

titanium_6al_4v = Material(
    s_id="titanium_6al_4v",
    s_description="Ti-6Al-4V (Grade 5) titanium alloy, annealed",
    s_category="metal",
    s_specification="ASTM B348 Grade 5 / Ti-6Al-4V, annealed",
    s_catalog_version=_S_CATALOG_VERSION,
    s_last_reviewed=_S_LAST_REVIEWED,
    structural=Structural(
        youngs_modulus=_PV(
            d_value=113.8e9,
            s_units="Pa",
            s_source=_ASM_HANDBOOK_VOL2_TI64 + " -- E = 16.5 Mpsi = 113.8 GPa (annealed Ti-6Al-4V, "
            "all bar/plate forms).",
            s_condition="20 C, annealed",
            s_confidence="standard",
        ),
        poisson_ratio=_PV(
            d_value=0.342,
            s_units="",
            s_source=_ASM_HANDBOOK_VOL2_TI64
            + " -- Poisson's ratio = 0.342 for annealed Ti-6Al-4V.",
            s_condition="20 C, annealed",
            s_confidence="standard",
        ),
        yield_stress=_PV(
            d_value=880e6,
            s_units="Pa",
            s_source=_ASM_HANDBOOK_VOL2_TI64 + " -- typical mill yield 0.2% offset for annealed "
            "Ti-6Al-4V = 880 MPa (128 ksi). Above the ASTM B348 "
            "Grade 5 minimum of 827 MPa: " + _ASTM_B348_GRADE5,
            s_condition="0.2% offset, annealed",
            s_confidence="standard",
            s_notes=(
                "ASTM B348 Grade 5 spec minimum is 827 MPa (120 ksi); the "
                "880 MPa typical mill yield exceeds the spec minimum by ~6% "
                "(same convention as the aluminum_6061_t6 / stainless_304 "
                "entries: store the typical-mill value, document spec "
                "minimum in s_notes for conservative-design use)."
            ),
        ),
        fatigue_endurance=_PV(
            d_value=510e6,
            s_units="Pa",
            s_source="Boyer Atlas of Fatigue Curves (ASM Intl, 1986) p.323, "
            "annealed Ti-6Al-4V rotating-beam R=-1",
            s_condition="rotating-beam R=-1, 10^7 cycles",
            s_confidence="standard",
        ),
        ultimate_tensile=_PV(
            d_value=950e6,
            s_units="Pa",
            s_source=_ASM_HANDBOOK_VOL2_TI64
            + " -- typical mill UTS for annealed Ti-6Al-4V = 950 MPa "
            "(138 ksi). Above the ASTM B348 Grade 5 minimum of "
            "896 MPa: " + _ASTM_B348_GRADE5,
            s_condition="annealed",
            s_confidence="standard",
            s_notes=(
                "ASTM B348 Grade 5 UTS minimum = 896 MPa (130 ksi); 950 MPa "
                "is the typical mill value reported by ASM Vol 2 + TIMET / "
                "Carpenter / ATI mill TDSes."
            ),
        ),
        density=_PV(
            d_value=4430.0,
            s_units="kg/m^3",
            s_source=_ASM_HANDBOOK_VOL2_TI64
            + " -- density = 4.43 g/cm^3 = 4430 kg/m^3 for annealed "
            "Ti-6Al-4V.",
            s_condition="20 C, annealed",
            s_confidence="standard",
        ),
    ),
    thermal=Thermal(
        thermal_conductivity=_PV(
            d_value=6.7,
            s_units="W/(m*K)",
            s_source=_ASM_HANDBOOK_VOL2_TI64
            + " -- k = 6.7 W/(m*K) at 20 C for annealed Ti-6Al-4V. "
            "Note: an order of magnitude lower than steels (~40 "
            "W/(m*K)) -- this is the dominant thermal-design "
            "constraint for Ti-6Al-4V actuator parts; heat does "
            "not escape laterally through the part.",
            s_condition="20 C, annealed",
            s_confidence="standard",
        ),
        specific_heat=_PV(
            d_value=560.0,
            s_units="J/(kg*K)",
            s_source=_ASM_HANDBOOK_VOL2_TI64 + " -- c_p = 0.56 J/(g*K) = 560 J/(kg*K) at 20 C for "
            "annealed Ti-6Al-4V.",
            s_condition="20 C, annealed",
            s_confidence="standard",
        ),
        max_operating_temp=_PV(
            d_value=400.0,
            s_units="C",
            s_source=_TI64_MAX_OP_TEMP,
            s_condition="continuous service in air",
            s_confidence="standard",
            s_notes=(
                "Continuous-service ceiling at 400 C is set by alpha-2 "
                "ordered-phase precipitation onset + long-term creep-"
                "strength knee. Intermittent / short-duration excursions "
                "to ~540 C are tolerated; above 600 C oxide-scaling + "
                "alpha-case embrittlement become severe."
            ),
        ),
        thermal_expansion=_PV(
            d_value=8.6e-6,
            s_units="1/K",
            s_source=_ASM_HANDBOOK_VOL2_TI64
            + " -- linear CTE 20-100 C = 8.6 ppm/K. Ti-6Al-4V has the "
            "lowest CTE of common engineering alloys (steels ~12, "
            "Cu ~17, Al ~24, austenitic SS ~17 ppm/K) -- this is "
            "the dimensional-stability reason it's chosen for "
            "structural-precision applications.",
            s_condition="20-100 C mean linear CTE, annealed",
            s_confidence="standard",
        ),
        melting_temp=_PV(
            d_value=1604.0,
            s_units="C",
            s_source=_ASM_HANDBOOK_VOL2_TI64
            + " -- solidus ~1604 C, liquidus ~1660 C for Ti-6Al-4V "
            "(the alpha+beta two-phase region). Using the lower "
            "(solidus) bound here as the conservative melting "
            "scalar for processing-temperature design.",
            s_condition="solidus, Ti-6Al-4V alpha+beta two-phase region",
            s_confidence="standard",
            s_notes=(
                "Ti-6Al-4V is an alpha+beta alloy with a solidification "
                "range, not a single melting point: solidus ~1604 C, "
                "liquidus ~1660 C. The beta-transus (~995 C +/- 15) is "
                "the alpha->beta transformation onset and is the relevant "
                "scalar for solution-heat-treatment design, NOT melting. "
                "The 1604 C solidus is the conservative-process temperature "
                "for melt-related limits (e.g. EBM/LPBF additive)."
            ),
        ),
    ),
    crystal_anisotropy=CrystalAnisotropy(
        # Ti-6Al-4V at room temperature is ~94% alpha (HCP) + 6% beta (BCC) by
        # volume in the annealed temper. The alpha phase is the matrix +
        # dominant load-bearing structure; alpha C_ij is the appropriate
        # CrystalAnisotropy entry here. For beta-phase values (relevant in
        # beta-annealed or high-T forming), see Petry et al. Phys Rev B
        # 43:10933 (1991), not stored here as a separate entry since the
        # CrystalAnisotropy dataclass is single-structure by design.
        s_crystal_structure="HCP",
        c11=_PV(
            d_value=162.4e9,
            s_units="Pa",
            s_source=_FISHER_RENKEN_1964,
            s_condition="300 K single-crystal alpha-Ti (HCP), ultrasonic "
            "measurement; basal-plane direction",
            s_confidence="standard",
            s_notes=(
                "alpha-Ti (HCP) single-crystal value. Ti-6Al-4V at room T is "
                "~94% alpha + 6% beta; the alpha phase dominates elastic "
                "response. For beta-phase BCC C_ij (relevant in "
                "beta-annealed temper or high-T forming) see Petry et al. "
                "Phys Rev B 43:10933 (1991)."
            ),
        ),
        c12=_PV(
            d_value=92.0e9,
            s_units="Pa",
            s_source=_FISHER_RENKEN_1964,
            s_condition="300 K single-crystal alpha-Ti, basal plane",
            s_confidence="standard",
        ),
        c13=_PV(
            d_value=69.0e9,
            s_units="Pa",
            s_source=_FISHER_RENKEN_1964,
            s_condition="300 K single-crystal alpha-Ti, basal-c-axis coupling",
            s_confidence="standard",
        ),
        c33=_PV(
            d_value=180.7e9,
            s_units="Pa",
            s_source=_FISHER_RENKEN_1964,
            s_condition="300 K single-crystal alpha-Ti, c-axis direction "
            "(c-axis stiffer than basal due to HCP packing)",
            s_confidence="standard",
        ),
        c44=_PV(
            d_value=46.7e9,
            s_units="Pa",
            s_source=_FISHER_RENKEN_1964,
            s_condition="300 K single-crystal alpha-Ti, prismatic-plane shear",
            s_confidence="standard",
        ),
        burgers_vector=_PV(
            d_value=2.950e-10,
            s_units="m",
            s_source=_FISHER_RENKEN_1964 + " -- derived: |b| = a0 for HCP basal <11-20> slip; "
            "with alpha-Ti a0 = 2.950 Angstrom (Fisher & Renken "
            "Table I, c/a = 1.587) gives |b| = 0.2950 nm.",
            s_condition="293 K, HCP basal <11-20> slip system (a-type)",
            s_confidence="standard",
            s_notes=(
                "Basal a-type Burgers vector. HCP Ti has multiple slip systems "
                "(basal, prismatic, pyramidal-a, pyramidal-c+a) with different "
                "|b| magnitudes: the c+a Burgers vector is longer "
                "(sqrt(a^2 + c^2) ~= 0.553 nm). The basal a-type is the "
                "lowest-CRSS slip system at room T and the appropriate default."
            ),
        ),
        # stacking_fault_energy intentionally omitted: HCP twinning + slip
        # interaction is treated via the c/a ratio + activation of different
        # slip families rather than a single canonical SFE scalar. Sparse,
        # geometry-dependent published data not Tier-1-quotable.
        # crss_initial intentionally omitted: two-phase (alpha+beta) duplex
        # complexity. Slip-CRSS for pure alpha-Ti basal is ~50-100 MPa per
        # Fisher-Renken-era measurements, but applying it to Ti-6Al-4V
        # without the beta-phase load transfer would mislead. Solver
        # consumers should use structural.fatigue_endurance (510 MPa).
    ),
)


# ── Aluminium 1350 (EC-grade electrical conductor) ──────────────────────────
#
# Winding-grade pure aluminium (≥ 99.5% Al, "EC grade", alloy designation
# 1350). This is the conductor analogue of pure_copper: the material a motor
# design tool needs to model ALUMINIUM windings, which aluminum_6061_t6
# (a structural alloy, 40% IACS, ρ = 3.99e-8) cannot proxy: at 61.0% IACS the
# 1350 conductor resistivity is 2.8264e-8 Ω·m, ~41% lower than 6061-T6.
#
# Scope: EM conductor properties (the high-value core for DC/AC copper-loss
# analysis: ρ(T) drives skin depth δ = √(2ρ/(ωμ)) and AC/DC resistance ratios,
# and the JAX-traceable d_resistivity_at_T callable comes for free from the
# resistivity + temp-coeff pair) plus density (for specific-loss → volumetric
# conversion). Thermal (k ≈ 234 W/(m·K)) and mechanical properties are a clean
# future add (CRC / Aluminum Association): left out here to keep the entry to
# directly verified Tier-1 values rather than padding.
aluminum_1350_ec = Material(
    s_id="aluminum_1350_ec",
    s_description="EC-grade 1350 aluminium electrical conductor (>=99.5% Al), "
    "winding/conductor grade",
    s_category="metal",
    s_specification="Aluminium 1350 (EC grade), 61.0% IACS per IEC 60889 "
    "(equiv. ASTM B230 wire / B233 redraw rod / B231 AAC)",
    s_catalog_version=_S_CATALOG_VERSION,
    s_last_reviewed="2026-06-17",
    structural=Structural(
        density=_PV(
            d_value=2700.0,
            s_units="kg/m^3",
            s_source="CRC Handbook of Chemistry and Physics -- density of "
            "aluminium, 2.70 g/cm^3 (2700 kg/m^3) at 20 C. (The "
            "Aluminum Association lists 2705 kg/m^3 for the 1350 "
            "grade specifically; the ~0.2% difference is "
            "negligible. Web cross-check 2026-06-17 confirmed ~2.70 "
            "g/cm^3 for 1350.)",
            s_condition="20 C",
            s_confidence="standard",
        ),
    ),
    electromagnetic=Electromagnetic(
        resistivity_at_20C=_PV(
            d_value=2.8264e-8,
            s_units="Ohm*m",
            s_source=_IEC_60889 + " -- value used: 2.8264e-8 Ohm*m (61.0% "
            "IACS), the standard's mandated reference resistivity "
            "for EC/1350 aluminium conductor.",
            s_condition="20 C, EC/1350 grade, 61.0% IACS",
            s_confidence="standard",
            s_notes=(
                "Winding-grade pure aluminium. This is the conductor value "
                "for modelling Al windings; do NOT use aluminum_6061_t6 "
                "(3.99e-8 Ω·m, 40% IACS structural alloy) as a winding "
                "conductor. Pure (99.99%) Al is ~2.65e-8; 1350 at 99.5% sits "
                "slightly higher at the 61.0% IACS reference."
            ),
        ),
        temp_coeff_resistivity=_PV(
            d_value=4.03e-3,
            s_units="1/K",
            s_source=_IEC_60889 + " -- value used: alpha_20 = 0.00403 /K for "
            "EC/1350 aluminium conductor.",
            s_condition="linear model at 20 C reference (IEC 60889)",
            s_confidence="standard",
            s_notes=(
                "Critical for AC/DC copper-loss at winding operating "
                "temperature (windings run hot, 100-180 C). The IEC 60889 "
                "alpha_20 = 0.00403 /K is grade-specific for 61.0% IACS "
                "aluminium (cf. copper 0.00393 /K). Feeds the JAX-traceable "
                "d_resistivity_at_T(T) accessor."
            ),
        ),
        relative_permeability=_PV(
            d_value=1.000022,
            s_units="",
            s_source=_CRC_HANDBOOK_MAGNETICS
            + " -- Al is paramagnetic with mu_r = 1.000022 at 20 C "
            "(bulk-aluminium value; alloy/temper does not shift it "
            "at this precision, so the same value applies to 1350 "
            "as to aluminum_6061_t6).",
            s_condition="20 C, bulk paramagnetic value",
            s_confidence="standard",
            s_notes=(
                "Essentially non-magnetic (mu_r ≈ 1) for any practical "
                "EM-FEA; listed for completeness of the conductor EM trio."
            ),
        ),
    ),
)


# ── Catalog dict
# ── 17-4 PH stainless, Condition H 900 ─────────────────────────────────────
#
# Precipitation-hardening martensitic stainless for shafts, hinges, and
# structural fittings. Was in the pre-v0.2.0 structural catalog on MatWeb
# data; restored here from the mill's own product data bulletin. Condition
# H 900 (482 C / 1 h age) is the peak-strength temper and the one most
# commonly specified for machined actuator hardware.

stainless_17_4ph_h900 = Material(
    s_id="stainless_17_4ph_h900",
    s_description=("17-4 PH martensitic precipitation-hardening stainless steel, Condition H 900"),
    s_category="metal",
    s_specification=(
        "UNS S17400 / ASTM A693 Grade 630 / AMS 5604 (sheet, strip, plate), "
        "Condition H 900: solution treated at 1038 C (Condition A), aged 482 C "
        "for 1 h, air cooled"
    ),
    s_catalog_version=_S_CATALOG_VERSION,
    s_last_reviewed=_S_LAST_REVIEWED,
    structural=Structural(
        youngs_modulus=_PV(
            d_value=197e9,
            s_units="Pa",
            s_source=_CLF_17_4PH_PDS + " -- Table 9, Modulus of Elasticity, H 900 = 28.5 x 10^6 "
            "psi (197 x 10^3 MPa)",
            s_condition="room temperature, Condition H 900",
            s_confidence="datasheet",
            s_notes=(
                "Modulus of rigidity (torsion), H 900 = 11.00 x 10^3 ksi (76 GPa) on the "
                "same table."
            ),
        ),
        poisson_ratio=_PV(
            d_value=0.272,
            s_units="",
            s_source=_CLF_17_4PH_PDS + " -- Table 9, Poisson's Ratio (all conditions) = 0.272",
            s_condition="room temperature, all conditions",
            s_confidence="datasheet",
        ),
        yield_stress=_PV(
            d_value=1172e6,
            s_units="Pa",
            s_source=_CLF_17_4PH_PDS + " -- Table 3, 0.2% YS, H 900 = 170 ksi min. (1172 MPa), "
            "properties acceptable for material specification, sheets and strip",
            s_condition="0.2% offset, room temperature, Condition H 900, specification minimum",
            s_confidence="datasheet",
            s_notes=(
                "Specification MINIMUM stored (same convention as the ASTM A240 "
                "minima on stainless_304/316). Table 2 typical transverse value is "
                "185 ksi (1275 MPa). Table 3 also gives Rockwell C 40-48 (typical "
                "45); Rockwell C is not convertible to the hardness_vickers slot "
                "without a derivation, so that slot stays None."
            ),
        ),
        ultimate_tensile=_PV(
            d_value=1310e6,
            s_units="Pa",
            s_source=_CLF_17_4PH_PDS + " -- Table 3, UTS, H 900 = 190 ksi min. (1310 MPa), "
            "properties acceptable for material specification, sheets and strip",
            s_condition="room temperature, Condition H 900, specification minimum",
            s_confidence="datasheet",
            s_notes=(
                "Specification MINIMUM stored. Table 2 typical transverse value is "
                "200 ksi (1379 MPa) with 9% elongation in 2 in. Fatigue endurance "
                "is not published in the bulletin; fatigue_endurance stays None."
            ),
        ),
        density=_PV(
            d_value=7800.0,
            s_units="kg/m^3",
            s_source=_CLF_17_4PH_PDS + " -- Table 9, Density, H 900 = 0.282 lbs/in^3 (7.80 g/cm^3)",
            s_condition="room temperature, Condition H 900",
            s_confidence="datasheet",
            s_notes=(
                "Condition A is 7.78 g/cm^3; density rises slightly with aging (7.82 at H 1150)."
            ),
        ),
    ),
    electromagnetic=Electromagnetic(
        resistivity_at_20C=_PV(
            d_value=7.7e-7,
            s_units="Ohm*m",
            s_source=_CLF_17_4PH_PDS + " -- Table 9, Electrical Resistivity, H 900 = 77 uOhm*cm. "
            "Converted to Ohm*m (x 1e-8).",
            s_condition="room temperature (Table 9 states no temperature), Condition H 900",
            s_confidence="datasheet",
            s_notes=(
                "Condition A is 98 uOhm*cm; aging lowers resistivity. Table 9 labels "
                "every condition '(Magnetic)': 17-4 PH is ferromagnetic (martensitic), "
                "unlike the austenitic 304/316 entries, but the bulletin publishes "
                "no permeability or B-H data, so the magnetic slots stay None."
            ),
        ),
    ),
    thermal=Thermal(
        thermal_conductivity=_PV(
            d_value=17.9,
            s_units="W/(m*K)",
            s_source=_CLF_17_4PH_PDS + " -- Table 9, Thermal Conductivity, H 900 at 300 F "
            "(149 C) = 124 BTU/hr/ft^2/F (17.9 W/m/K)",
            s_condition="149 C (300 F), Condition H 900; lowest temperature published",
            s_confidence="datasheet",
            s_notes=(
                "The bulletin publishes k only at 149, 260, 460, and 482 C (17.9, "
                "19.5, 22.5, 22.6 W/m/K). No room-temperature row exists; the "
                "149 C value is stored rather than extrapolated."
            ),
        ),
        specific_heat=_PV(
            d_value=460.0,
            s_units="J/(kg*K)",
            s_source=_CLF_17_4PH_PDS + " -- Table 9, Specific Heat, H 900 = 0.11 BTU/lbs/F "
            "(0.46 kJ/kg/K), 32-212 F (0-100 C)",
            s_condition="0-100 C, Condition H 900",
            s_confidence="datasheet",
        ),
        thermal_expansion=_PV(
            d_value=10.8e-6,
            s_units="1/K",
            s_source=_CLF_17_4PH_PDS + " -- Table 9, Mean Coefficient of Thermal Expansion, "
            "H 900, 70-200 F (21-93 C) = 6.0 x 10^-6 in/in/F (10.8 um/m/K)",
            s_condition="21-93 C mean, Condition H 900",
            s_confidence="datasheet",
            s_notes=(
                "Rises with the interval upper bound: 11.3 (21-204 C), 11.7 "
                "(21-316 C) um/m/K on the same table. No melting range or "
                "maximum service temperature is published in the bulletin."
            ),
        ),
    ),
)


# ── C93200 (SAE 660) bearing bronze ────────────────────────────────────────
#
# The standard sleeve-bearing bronze. Mechanical properties are the CDA
# sand-cast (M01) row: specification minimums stored, typicals in s_notes,
# matching the minimum-first convention used for the stainless entries.

c93200_bearing_bronze = Material(
    s_id="c93200_bearing_bronze",
    s_description="C93200 (SAE 660) high-leaded tin bronze, the standard sleeve-bearing alloy",
    s_category="metal",
    s_specification=(
        "UNS C93200 / SAE 660 high-leaded tin bronze (Cu 81-85, Sn 6.3-7.5, Pb 6-8, Zn "
        "1-4 wt%), as sand cast (temper code M01); SAE J462, ASTM B584 / B505 / B271"
    ),
    s_catalog_version=_S_CATALOG_VERSION,
    s_last_reviewed=_S_LAST_REVIEWED,
    structural=Structural(
        youngs_modulus=_PV(
            d_value=100e9,
            s_units="Pa",
            s_source=_CDA_C93200 + " -- Modulus of Elasticity in Tension = 14500 ksi. Converted: "
            "14500 ksi x 6.894757 MPa/ksi = 99,974 MPa, stored as 100 GPa.",
            s_condition="20 C (68 F)",
            s_confidence="standard",
        ),
        yield_stress=_PV(
            d_value=96.5e6,
            s_units="Pa",
            s_source=_CDA_C93200 + " -- Mechanical Properties, As Sand Cast (M01): YS-0.5% Ext = "
            "14 ksi Min for Standard (96.5 MPa); 18 ksi Typ (124 MPa)",
            s_condition="0.5% extension under load, 20 C, as sand cast; specification minimum",
            s_confidence="standard",
            s_notes=(
                "Minimum stored, typical (124 MPa) in this note, matching the 304/316 "
                "convention. Continuous-cast M07 minimum is 20 ksi (138 MPa)."
            ),
        ),
        ultimate_tensile=_PV(
            d_value=207e6,
            s_units="Pa",
            s_source=_CDA_C93200
            + " -- Mechanical Properties, As Sand Cast (M01): Tensile Strength "
            "= 30 ksi Min for Standard (207 MPa); 35 ksi Typ (241 MPa)",
            s_condition="20 C, as sand cast; specification minimum",
            s_confidence="standard",
            s_notes=(
                "Typical 241 MPa with 20% elongation (15% minimum). Brinell hardness 65 "
                "typ (500 kg) is not a Vickers value and is not converted."
            ),
        ),
        fatigue_endurance=_PV(
            d_value=110e6,
            s_units="Pa",
            s_source=_CDA_C93200
            + " -- Mechanical Properties, As Sand Cast (M01): Fatigue Strength "
            "= 16 ksi Typ (110 MPa), 100 x 10^6 cycles",
            s_condition="100 x 10^6 cycles, 20 C, as sand cast, typical (no minimum published)",
            s_confidence="standard",
        ),
        compressive_strength=_PV(
            d_value=317e6,
            s_units="Pa",
            s_source=_CDA_C93200 + " -- Mechanical Properties, As Sand Cast (M01): Compressive "
            "Strength, 0.1 in. set/in. = 46 ksi Typ (317 MPa)",
            s_condition="0.1 in/in permanent set criterion, 20 C, as sand cast, typical",
            s_confidence="standard",
        ),
        density=_PV(
            d_value=8910.0,
            s_units="kg/m^3",
            s_source=_CDA_C93200 + " -- Density = 0.322 lb/cu in at 68 F; Specific Gravity = 8.91",
            s_condition="20 C (68 F)",
            s_confidence="standard",
        ),
    ),
    electromagnetic=Electromagnetic(
        resistivity_at_20C=_PV(
            d_value=1.437e-7,
            s_units="Ohm*m",
            s_source=_CDA_C93200
            + " -- Electrical Conductivity = 12 % IACS at 68 F. Converted by the "
            "IACS definition (100% IACS = 1.7241e-8 Ohm*m): 1.7241e-8 / 0.12 = 1.437e-7 Ohm*m.",
            s_condition="20 C (68 F)",
            s_confidence="standard",
            s_notes="Unit conversion only; %IACS is a conductivity unit, not a separate property.",
        ),
    ),
    thermal=Thermal(
        thermal_conductivity=_PV(
            d_value=58.2,
            s_units="W/(m*K)",
            s_source=_CDA_C93200
            + " -- Thermal Conductivity = 33.6 Btu/(sq ft . ft . hr . F) at 68 F. "
            "Converted: 33.6 x 1.7307 = 58.2 W/(m*K).",
            s_condition="20 C (68 F)",
            s_confidence="standard",
        ),
        specific_heat=_PV(
            d_value=377.0,
            s_units="J/(kg*K)",
            s_source=_CDA_C93200
            + " -- Specific Heat Capacity = 0.09 Btu/(lb . F) at 68 F. Converted: "
            "0.09 x 4186.8 = 377 J/(kg*K).",
            s_condition="20 C (68 F); source publishes 2 significant figures",
            s_confidence="standard",
        ),
        thermal_expansion=_PV(
            d_value=18.0e-6,
            s_units="1/K",
            s_source=_CDA_C93200
            + " -- Coefficient of Thermal Expansion, 68-212 F = 10 x 10^-6 per F. "
            "Converted: 10 x 1.8 = 18 x 10^-6 /K.",
            s_condition="20-100 C (68-212 F) mean",
            s_confidence="standard",
        ),
        melting_temp=_PV(
            d_value=977.0,
            s_units="C",
            s_source=_CDA_C93200
            + " -- Melting Point - Liquidus = 1790 F (977 C); Solidus = 1570 F "
            "(854 C)",
            s_condition="liquidus (solidus 854 C)",
            s_confidence="standard",
            s_notes="Liquidus stored, matching the aluminum_6061_t6 melting_temp convention.",
        ),
    ),
)


CATALOG: dict[str, Material] = {
    pure_copper.s_id: pure_copper,
    aluminum_6061_t6.s_id: aluminum_6061_t6,
    aluminum_1350_ec.s_id: aluminum_1350_ec,
    c93200_bearing_bronze.s_id: c93200_bearing_bronze,
    steel_4140.s_id: steel_4140,
    stainless_304.s_id: stainless_304,
    stainless_316.s_id: stainless_316,
    stainless_17_4ph_h900.s_id: stainless_17_4ph_h900,
    titanium_6al_4v.s_id: titanium_6al_4v,
}


__all__ = [
    "CATALOG",
    "aluminum_1350_ec",
    "aluminum_6061_t6",
    "c93200_bearing_bronze",
    "pure_copper",
    "stainless_17_4ph_h900",
    "stainless_304",
    "stainless_316",
    "steel_4140",
    "titanium_6al_4v",
]
