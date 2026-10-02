<a id="readme-top"></a>

# emergent-matter-sdm-materials

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-033388.svg)](LICENSE)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-0055FF.svg)](https://www.python.org/downloads/)
[![uv](https://img.shields.io/badge/packaged%20with-uv-DE5FE9.svg)](https://docs.astral.sh/uv/)

**Unified multi-physics materials substrate for the Software Defined Matter ecosystem.**

One repo, one composed schema, one merged catalog spanning **structural + electromagnetic + thermal + manufacturing + crystal-anisotropy** properties, with per-property provenance (units, source, condition, confidence) validator-enforced at construction time. Designed so a multi-physics optimizer can answer "what's M19 silicon steel's saturation flux AND core loss AND thermal conductivity?" without juggling separate material files per physics domain.

**Catalog status:** every `PropertyValue` in the catalog is **100% Tier 1** (vendor TDS / national standard / measured), gated by `tests/test_catalog_provenance_strength.py`: the build fails if any value slips through with weak metadata. CI runs the full suite on every push. See [`docs/catalog.md`](docs/catalog.md) for the exact material/property counts (auto-generated, always current) and `CHANGELOG.md` for what shipped recently.

Includes a **consumer-safe structural strength resolver** (`get_structural_strength(material)` / `Structural.resolve_design_strength()` / `.d_design_strength_Pa` / `.s_strength_basis`) that returns a documented allowable (`yield_stress` → `ultimate_tensile`, else fails loud) plus its **basis**, so structural tools get a usable strength for materials like SLS PA12 (basis `ultimate_tensile`, 50 MPa) without faking a yield.

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
    │  composes
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
