<a id="readme-top"></a>

# emergent-matter-sdm-materials

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-033388.svg)](LICENSE)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-0055FF.svg)](https://www.python.org/downloads/)
[![uv](https://img.shields.io/badge/packaged%20with-uv-DE5FE9.svg)](https://docs.astral.sh/uv/)

**Unified multi-physics materials substrate for the Software Defined Matter ecosystem.**

One repo, one composed schema, one merged catalog spanning **structural + electromagnetic + thermal + manufacturing + crystal-anisotropy** properties, with per-property provenance (units, source, condition, confidence) validator-enforced at construction time. Designed so a multi-physics optimizer can answer "what's M19 silicon steel's saturation flux AND core loss AND thermal conductivity?" without juggling separate material files per physics domain.

**Catalog status:** every `PropertyValue` in the catalog is **100% Tier 1** (vendor TDS / national standard / measured), gated by `tests/test_catalog_provenance_strength.py`: the build fails if any value slips through with weak metadata. CI runs the full suite on every push. See [`docs/catalog.md`](docs/catalog.md) for the exact material/property counts (auto-generated, always current) and `CHANGELOG.md` for what shipped recently.

Includes a **consumer-safe structural strength resolver** (`get_structural_strength(material)` / `Structural.resolve_design_strength()` / `.d_design_strength_Pa` / `.s_strength_basis`) that returns a documented strength scalar (`yield_stress` → `ultimate_tensile`, else fails loud) plus its **basis**, so structural tools can use materials like SLS PA12 without faking a yield. Consumers still define design margins and applicable load, temperature, creep and fatigue limits.

For the exact Formlabs PA12 grade, use `get_material("formlabs_nylon12_powder")`. Its modulus, density, strengths and thermal expansion cite the Formlabs FLP12G01 V2 datasheet. The broader `nylon12_sls` entry retains its existing sources. Neither entry invents a yield or fatigue limit. See [Fuse manufacturing guidance](#fuse-manufacturing-guidance) for printer-specific limits and finishing considerations.

**Browse the catalog as a document:** see [`docs/catalog.md`](docs/catalog.md). Auto-generated from the Python source, it lists every material's properties + source citations + conditions + confidence levels in human-readable tables. Regenerate with `uv run python scripts/generate_catalog_doc.py`.

## Install

Zero runtime dependencies. JAX is an *optional* extra used only by the `to_jax_pytree()` convenience converter; consumers without JAX can ignore it.

**As a dependency, from the Software Defined Matter package index** (not PyPI). Browse versions and file hashes at [get.softwaredefinedmatter.com](https://get.softwaredefinedmatter.com/):

```bash
uv pip install emergent-matter-sdm-materials --index https://get.softwaredefinedmatter.com/simple
```

In a uv project, declare the index once and pin the package to it, so its name never resolves from public PyPI:

```toml
[[tool.uv.index]]
name = "em"
url = "https://get.softwaredefinedmatter.com/simple"
explicit = true

[tool.uv.sources]
emergent-matter-sdm-materials = { index = "em" }
```

A wheel and sdist are also attached to every [GitHub Release](https://github.com/EmergentMatter/emergent-matter-sdm-materials/releases).

**From a clone, for contributing or running the examples above:**

```bash
git clone https://github.com/EmergentMatter/emergent-matter-sdm-materials.git
cd emergent-matter-sdm-materials
uv sync --all-extras       # adds dev (pytest) + jax (optional pytree converter)
```

## Quick start

```python
from emergent_matter_materials import MATERIALS, get, get_with_metadata

# Cross-physics query: multi-group lookup on one Material object
m19 = MATERIALS["m19_silicon_steel"]
m19.s_specification  # "Cleveland-Cliffs DI-MAX M-19, ASTM A677 grade 36F155, ..."
m19.electromagnetic.d_saturation_flux_T  # 2.0
m19.electromagnetic.d_core_loss_W_kg  # 3.42 (at 1.5T/60Hz)
m19.thermal.d_thermal_conductivity_W_mK  # 21.9 (measured lamination stack)

# Legacy SI accessor: backward-compatible with sdm-core's materials.get()
get("Cu", "rho")  # 8940.0

# Full provenance lookup: for traceable optimization artifacts
meta = get_with_metadata("M19", "B_sat")
meta.d_value  # 2.0
meta.s_units  # "T"
meta.s_source  # "DOE/Ames elt234, comparison table B_s = 2.0 T..."
meta.s_condition  # "20 C, saturation polarization for 3.2% Si-Fe"
meta.s_confidence  # "standard"
meta.s_notes  # "Caveat: ASTM A677 does NOT formally tabulate B_sat..."

# Consumer-safe structural strength: resolves yield_stress, else ultimate_tensile,
# else raises StructuralStrengthUnavailable; reports the basis so a consumer
# never has to guess whether it got a yield or an ultimate value
from emergent_matter_materials import get_structural_strength

s = get_structural_strength("PA12_SLS")
s.d_value_Pa  # 5.0e7
s.s_basis  # "ultimate_tensile"  (SLS PA12 has no Tier-1 yield)
get_structural_strength("Steel_4140").s_basis  # "yield_stress"      (true yield used first)
```

Not every property is populated on every material: group fields are `Optional`, and `_req()` on each group raises a clear error if a solver hits a missing field. What is still missing is data whose Tier 1 source has not been verified yet.

## Schema in one diagram

```
PropertyValue   (value + units + source + condition + confidence + notes)
    ▲
    │  composes (one per scalar slot, one per table row, one per flow point)
    │
PropertyTable (temperature -> PropertyValue rows)  |  FlowCurve (temperature, plastic strain -> stress)
    ▲
    │  attach to
    │
Structural | Electromagnetic | Thermal | Manufacturing | CrystalAnisotropy
    ▲
    │  composes
    │
Material   (id + description + category + specification + versioning,
            with each physics group above optional)
```

The `crystal_anisotropy` group (v0.4.0) carries single-crystal elastic stiffness tensor (Voigt C11/C12/C44/C13/C33/C66), Burgers vector, stacking fault energy, and slip-CRSS, all used for crystal-plasticity FEM, dislocation-density hardening, and texture-aware structural simulation. Populated for the crystalline metals (FCC, BCC and HCP alike); explicitly None for amorphous, nanocrystalline, and polymer materials, where a single-crystal tensor has no meaning.

The catalog is arranged as one module per material family under
`catalog/`, which `catalog/_loader.py` assembles into `MATERIALS` at import
time. Adding a family means adding a module there; the directory listing is
the index of what exists.

Every numeric property is a `PropertyValue`, never a bare float. Convenience accessors (`d_youngs_modulus_Pa`, `d_density_kg_m3`, ...) on each group return bare floats for solver hot paths.

## Temperature-dependent data

Thermal and thermo-mechanical solvers need a property across a temperature range, not at one condition. `Structural`, `Thermal`, and `Electromagnetic` each carry a `temperature_tables` mapping, keyed by the scalar slot a table extends:

```python
from emergent_matter_materials import PropertyTable, Thermal

thermal = Thermal(
    temperature_tables={
        "thermal_conductivity": PropertyTable.from_rows(
            [(25.0, 11.4), (500.0, 18.3), (1000.0, 25.9)],  # (C, W/(m*K))
            s_units="W/(m*K)",
            s_source="<vendor TDS, revision, table>",
            s_confidence="datasheet",
        ),
    }
)
thermal.table("thermal_conductivity").value_at(750.0)  # linear; raises outside 25-1000 C
```

- **Provenance is per point.** Each row is a full `PropertyValue`, because the rows of one curve often come from different tests (a room-temperature tensile test and a high-temperature resonance test, say). `from_rows` stamps one source on every row; build `TablePoint`s directly when rows differ. Every provenance gate scans every row.
- **The slot's rules apply to every row.** A table key must be a property of its group that can vary with temperature (not a temperature itself, like `melting_temp`), in that property's units, and each row must pass the scalar slot's range check (emissivity in [0, 1], positive conductivity, ...). Resistivity is tabulated under the key `"resistivity"`.
- **Secant tables declare it.** A mean coefficient of thermal expansion (CTE), or a mean specific heat, measured from a reference temperature sets `d_reference_temperature_C`; no other property accepts one. `bracket_at(T)` returns the rows an interpolated value came from, for citing both.
- **Plasticity is a `FlowCurve`** on `Structural.flow_curve`: flow stress against equivalent plastic strain, one isotherm per temperature (and per strain rate, for rate-dependent data), each point sourced. The curve states whether it holds true or engineering stress-strain, or `"unspecified"` when the source doesn't say.
- **Melting range and process-simulation scalars**: `Thermal.solidus_temp`, `Thermal.liquidus_temp`, `Thermal.latent_heat_fusion`, and `Structural.stress_relaxation_temp`.

The scalar slot stays the headline value and is independent of its table. `to_jax_pytree()` flattens each table into paired arrays ready for `jnp.interp`. Note that `jnp.interp` clamps silently outside the table, where `value_at` raises; a traced solver should check the range itself.

## Deriving a material from a catalog entry

A downstream catalog often has better or extra data for a material this catalog already holds. `derive_material` builds a new entry from the base instead of copying it. Everything not overridden is the base's own object, so nothing is duplicated, and every override is recorded with a required reason:

```python
from emergent_matter_materials import MATERIALS, FieldOverride, PropertyTable, derive_material

ours = derive_material(
    MATERIALS["stainless_316"],
    s_id="em_stainless_316",  # a new id: never the base's, never any registered entry's
    # material_fingerprint() of the base when these overrides were reviewed. If the
    # open-source entry's data changes, this raises and prints the new value to
    # re-review; version and review-date bumps alone don't change it.
    s_expected_base_fingerprint="83ad259a17ea177a",
    overrides=[
        FieldOverride(
            "thermal.temperature_tables.thermal_conductivity",
            PropertyTable.from_rows(
                [(25.0, 14.0), (500.0, 19.0), (1000.0, 25.0)],
                s_units="W/(m*K)",
                s_source="<lab report, run, date>",
                s_confidence="measured",
            ),
            s_reason="Measured on our powder lot; the base entry has no curve",
        ),
    ],
    s_catalog_version="0.1.0",
    s_last_reviewed="2026-10-16",
)
ours.structural is MATERIALS["stainless_316"].structural  # True: inherited, not copied
ours.derivation.b_is_overridden("thermal.thermal_conductivity")  # False: still the base's scalar
```

An override targets a scalar slot (`"thermal.thermal_conductivity"`), the flow curve (`"structural.flow_curve"`), or a table (`"thermal.temperature_tables.<key>"`). A `PropertyTable` replaces the whole table; a `TablePoint` replaces or inserts one row and keeps every other row with its own source; a `TableRowRemoval` drops one row; `None` removes an inherited value. A removal must remove something, so a typo can't pass as an audited change. All overrides for a group are applied together and validated once by the group's own rules, so their order doesn't matter.

`Material.derivation` records the base id, catalog version, and fingerprint, every override, and the base's own derivation when deriving from a derived entry, so `b_is_overridden(path)` answers across the whole chain.

## Tier 1 only: bad data is worse than no data

Since v0.2.0 the catalog accepts **only primary sources**:

| `s_confidence` | What it means | Examples |
|---|---|---|
| `measured` | Direct lab measurement on the specific material lot | NREL/IJHMT 2018 lamination-stack k(M19) |
| `datasheet` | Vendor technical data sheet | Arnold N42 PDF, Carpenter Hiperco E200, Victrex 450G TDS |
| `standard` | National/international published reference data | NIST SRD/JPCRD, ASTM, EN/ISO, MMPDS, Aluminum Association ADM |

Aggregator-tier data (MatWeb, AZoM, MakeItFrom, ULProspector) and generic handbook references are **explicitly forbidden** as primary sources. The `tests/test_catalog_provenance_strength.py` suite gates the build: if any PropertyValue lacks a Tier-1 citation, the catalog doesn't ship.

When two Tier-1 sources disagree, the catalog records **both** in `s_notes`; we never average. See `CLAUDE.md` for the full source-priority resolution rule.

## Provenance is engineering data, not bookkeeping

Cross-physics merges mean a single material entry has values from multiple sources at different conditions. Per-property metadata lives alongside the numeric value and is validator-enforced:

- **Units are not decorative**: `s_units` MUST match the canonical SI string for the property's slot. Mismatch raises `ValueError` at construction time.
- **Source non-empty**: every value cites a source with revision/date/URL where applicable.
- **Conditions captured**: e.g. core_loss's `s_condition` records the `B_ref` and `f_ref` operating point the value was measured at (`"B_ref=1.5 T, f_ref=60 Hz"`).
- **Cross-check notes preserved**: when third-party verification disagrees, the rationale stays in `s_notes` so downstream consumers can trace it.


## Catalog inventory

See [`docs/catalog.md`](docs/catalog.md) for the generated, always-current inventory: every material, grouped by category, with every property, source, and confidence level.

**Aliases** like `"Cu"`, `"M19"`, `"NdFeB_N42SH"`, `"Metglas_2605"`, `"Recoma_28"` resolve to canonical IDs through `_ALIASES`. Ambiguous bare names (`"Al"`, `"NdFeB"`, `"Steel"`) are deliberately omitted to force grade/temper disambiguation.

## Documentation

[`docs/`](docs/) holds what supports the catalog but doesn't belong in
this README or `CLAUDE.md`: the generated catalog inventory and
architecture decision records.
[`docs/README.md`](docs/README.md) explains what each location means
and how it ages, rather than indexing it by filename. [STYLE.md](STYLE.md)
and [CONTRIBUTING.md](CONTRIBUTING.md) cover house style and how a
change ships.

## Fuse manufacturing guidance

These vendor guidelines apply to Formlabs Nylon 12 Powder on the Fuse 1 generation.
They are manufacturing references, not intrinsic material properties or structural
allowables. Checked 2026-10-25; confirm the actual printer and PreForm settings.

| Feature | Manufacturer guidance |
|---|---|
| Supported or unsupported walls | Vertical 0.6 mm; horizontal 0.3 mm. Features at these limits can still distort. |
| Pins or wires | Diameter at least 0.8 mm. |
| Holes | Diameter at least 1.0 mm; provide cleaning access. |
| Enclosed cavities | At least two powder exits, each at least 3.5 mm diameter. |
| Separate mating parts | Clearance 0.2 mm for features below 20 mm²; 0.4 mm above 20 mm². |
| Printed-in-place assemblies | Clearance 0.3 mm below 20 mm²; 0.6 mm above 20 mm². |
| Independent parts in the build | Spacing 2 mm recommended; 1 mm minimum. |
| Largest Nylon 12 part | 160.2 × 160.2 × 297.3 mm; XY chamber corners have 16 mm inner radius. Check fit in PreForm. |

Source: [Formlabs Fuse design specifications](https://formlabs.com/support/Design-specifications-for-3D-models-Fuse-1/).
The source does not assign the assembly-clearance category at exactly 20 mm².
For accurate concentric bores, it recommends an undersized pilot followed by reaming.

The manufacturer's [dimensional study](https://formlabs.com/white-papers/measuring-sls-dimensional-accuracy-and-print-repeatability/)
reports an XY benchmark of ±max(0.3 mm, 0.5% of dimension). It measures witness
parts and build variation; this is not a guarantee for a bearing seat, hole position
or press fit. A tight-fit design needs a representative coupon, finishing allowance
and inspection after the intended cleaning and conditioning. Matching nominal CAD
diameters does not establish an interference fit.

Keep machine calibration and shrink compensation in process configuration, outside
`Material.manufacturing`. The material's thermal-expansion scalar does not define
sintering shrinkage. Short-term strength and heat-deflection tests do not establish
bolt-preload retention, bonded-insert pullout, fatigue life or continuous service
temperature. Those require application-specific evidence.

## Consumers

- `emergent-matter-sdm-core`: geometry substrate; re-exports from this repo via an import shim during migration
- `emergent-matter-sdm-processes`: machine-specific presets layered over this catalog's process-family manufacturing defaults

## Versioning

Two levels, mechanically locked together by `[tool.em-release]` in `pyproject.toml`: every release writes both in lockstep, and `tests/test_catalog_versioning.py` fails the build if they ever drift apart:

- `__version__` (package semver): the release version, also what `pip`/`uv` see.
- `__catalog_version__` (data semver): `MAJOR` breaks schema, `MINOR` adds materials/fields, `PATCH` corrects values/citations. Every `Material.s_catalog_version` must be `<=` this value (provenance-gate enforced).

Optimization artifacts cite both: `"optimized against emergent-matter-sdm-materials __version__=X.Y.Z, __catalog_version__=X.Y.Z"`.

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for how a release actually ships.

## Built with

| | |
|---|---|
| [uv](https://docs.astral.sh/uv/) | Packaging, the locked dev environment, and the src-layout + hatchling build |
| [JAX](https://docs.jax.dev/) | Optional pytree conversion via `to_jax_pytree()`; not required to read the catalog |
| [pytest](https://docs.pytest.org/) | The full test suite, including the provenance-strength and units gates |
| [ruff](https://docs.astral.sh/ruff/) | Linting and formatting |
| [mypy](https://mypy-lang.org/) | Static typing, `disallow_untyped_defs` |

The package itself has no required runtime dependencies.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for how a change ships: the
changeset a pull request needs, and how a release is cut.
[STYLE.md](STYLE.md) is the house style for code, tests, and docs, and
it wins over habit.

By participating you agree to the
[Code of Conduct](CODE_OF_CONDUCT.md).

## Support

Questions and usage help go to
[Discussions](https://github.com/EmergentMatter/emergent-matter-sdm/discussions);
bugs and feature requests go to
[Issues](https://github.com/EmergentMatter/emergent-matter-sdm-materials/issues).
See [SUPPORT.md](SUPPORT.md) for what is and is not supported.

For security reports, do not open a public issue. Follow
[SECURITY.md](SECURITY.md).

## License

Apache-2.0. See [`LICENSE`](LICENSE) and [`NOTICE`](NOTICE).

## Acknowledgments

Every catalog value cites its source at the point of use; see
[`docs/catalog.md`](docs/catalog.md) for the full per-material,
per-property citation list. The catalog draws on national and
international standards (NIST SRD/JPCRD, ASTM, EN/ISO, MMPDS, the
Aluminum Association's Aluminum Design Manual), engineering reference
handbooks (the ASM Handbook, the CRC Handbook of Chemistry and
Physics, Shigley's Mechanical Engineering Design, Boyer's Atlas of
Fatigue Curves), and vendor technical data sheets cited per material
in the catalog.

Citing these sources is not an endorsement by them of this project.

<p align="right">(<a href="#readme-top">back to top</a>)</p>
