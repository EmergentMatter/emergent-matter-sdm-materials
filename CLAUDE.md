# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Code standard

Follow [STYLE.md](STYLE.md) at the repo root for all code, comments, tests, and docs. It wins over habit. Pull request descriptions follow [.github/PULL_REQUEST_TEMPLATE.md](.github/PULL_REQUEST_TEMPLATE.md).

## What This Is

`emergent-matter-sdm-materials` is the **Layer-0 substrate** for materials data across the Software Defined Matter ecosystem. One repo, one composed schema, one merged catalog spanning structural + electromagnetic + thermal + manufacturing properties, with per-property provenance enforced by validators.

Created 2026-05-24 by consolidating the earlier per-repo materials files, including the API surface (aliases, SI accessor, registry) from `emergent-matter-sdm-core/src/software_defined_matter/materials/materials.py`, into one repo.

The motivating use case is a multi-physics optimizer that needs cross-physics queries (e.g., M19 silicon steel's Young's modulus AND saturation flux AND CTE in one place). Keeping the catalog in its own repo decouples it from sdm-core's geometry release cadence.

## Build & Run

```bash
uv sync --all-extras       # dev (pytest) + jax (optional pytree converter)
uv run pytest              # full suite; provenance-strength tests gate the catalog
uv run pytest -k provenance   # provenance gate only
uv run pytest -k units        # units enforcement only
```

## Architecture

See [the schema diagram](README.md#schema-in-one-diagram) in the README:
`PropertyValue` composes into physics groups, physics groups compose into
`Material`.

Group `__post_init__` enforces `_PROPERTY_EXPECTED_UNITS`: an unexpected
units string is a construction-time error, not a runtime surprise deep in
a solver.

## Naming conventions

Shared baseline: see [STYLE.md](STYLE.md), the `d_`/`n_`/`b_`/`s_` prefix
convention on scalar fields, with the unit in the name for a hot-path
accessor (`d_youngs_modulus_Pa`, `d_density_kg_m3`).

Materials-specific addition (not in STYLE.md): a composite dataclass name
(`PropertyValue`, `Structural`, `Material`) carries no prefix.

## Catalog policy (v0.2.0): Tier 1 only

**Bad data is worse than no data.** Every PropertyValue in the catalog must have `s_confidence` in `{measured, datasheet, standard}`, i.e. **Tier 1**. Aggregator-tier data (MatWeb, ULProspector, Citrination) and unverified handbook references were removed in v0.2.0. The deleted data stays out until a Tier 1 source is verified.

What this means in practice:

- **Adding a new PropertyValue** requires consulting a primary source (vendor TDS, national standard, or NIST SRD). A `s_source` that just says "MatWeb" or "Shigley's" (when the value isn't directly in a Shigley table, i.e. the source is a generic handbook reference rather than a specific citation) gets rejected by the provenance gates.
- **Adding a new material** requires at least one PropertyValue at Tier 1. If you can only find aggregator-grade data for a material, leave the material out until a Tier 1 source turns up.
- **All group fields are Optional.** Materials may have only a subset of properties populated (e.g. `nylon12_sls` has structural + max-op-temp from EOS PA 2200, but no thermal-conductivity yet because the EOS TDS doesn't list it). Solvers should handle missing fields gracefully via the `_req()` accessor pattern, which raises a clear "field is None" error saying the Tier 1 source is not yet available.
- **Per-property `s_confidence` is still tracked** for downstream introspection (e.g., an optimizer artifact could record "this run used catalog v0.2.0; all input properties were 'datasheet' confidence"). The optimizer itself doesn't branch on confidence, but provenance traceability is engineering data.

The deleted v0.1.x materials are recovered one-by-one as their primary sources are verified; the checklist is whatever still lacks a Tier 1 source.

The catalog's schema and accessor API have been frozen since v0.4.0. Catalog
updates are triggered by real downstream-use issues (an optimizer flags an
implausible value, a vendor TDS gets a revision), not by preemptive
verification passes: a preemptive pass surfaced more catalog-policy
hair-splitting than real errors the one time it was tried.

## Source-priority hierarchy (the rule for "which source wins")

When two sources disagree on a property value, **higher tier wins**. Never average. The chosen value's `s_source` cites the higher-tier source, and `s_notes` records the disagreement so a downstream consumer can trace it.

The four-tier hierarchy maps directly onto `s_confidence`:

| Tier | `s_confidence` | What it means | Authoritative for |
|---|---|---|---|
| **1** | `measured` | Direct lab measurement on the specific material lot | The lot you measured (rarest) |
| **1** | `datasheet` | Vendor TDS: Arnold N42 PDF, Carpenter Hiperco E200, Victrex PEEK 450G, SABIC Ultem 1010, EOS PA 2200 | Commercial alloys, polymers, magnets (the material **is** what the vendor ships) |
| **1** | `standard` | National/international published reference data: NIST SRD/JPCRD, ASTM/AMS specs, EN/ISO standards, MMPDS, Aluminum Association ADM | Pure elements (thermophysical), industry-standard alloys, grade-defining specs |
| **2** | `handbook` | Peer-reviewed engineering handbooks: ASM Handbook, Shigley's MED, CRC Handbook, Boyer Atlas of Fatigue Curves, peer-reviewed papers | Generic alloys, structural materials when Tier 1 silent |
| **3** | `aggregator` | Database aggregators: MatWeb, ULProspector, SpecialChem, Citrination paper-mined, university course materials | Cross-reference; use only when Tier 1+2 silent. Must name the aggregator in `s_source` |
| **4** | `derived` | Computed from other properties, unit-converted, range-averaged, fitted-model output | Last-resort defaults; must explain derivation in `s_notes` |
| **4** | `estimated` | Engineering rule-of-thumb (`σ_e ≈ 0.5 σ_UTS`, etc.) | Last-resort; explain reasoning in `s_notes` |

**Critical: authority depends on the material class.** For Carpenter Hiperco's saturation flux, the Carpenter datasheet is Tier 1 (the material **is** what Carpenter ships, so the vendor TDS wins). For pure copper's thermal conductivity at 300 K, NIST SRD is Tier 1 (settled physics, so `standard` wins over a vendor's repeat of NIST's number). For "AISI 4140" structural data, ASM Handbook Vol 1 + MMPDS allowables outrank any single vendor TDS because the standard is the spec.

**Conflict resolution rule:**

```
Two sources, different values:
1. Take the value from the HIGHEST tier source.
2. Same tier? Take the more recent revision.
3. Same tier + same date? Take the more specific (this grade/temper vs general).
4. Record the loser in s_notes:
   "Tier 1 [Source X] = Y (used); Tier 2 [Source Z] = W (rejected)."
NEVER average. NEVER downgrade confidence to soft-resolve a disagreement.
```

**`aggregator` confidence carries extra obligation:** `s_source` MUST name the aggregator (MatWeb, ULProspector, Citrination, etc.) explicitly so the consumer knows the value is one hop removed from a primary measurement. Test `test_aggregator_confidence_names_aggregator` enforces this.

**Citation discipline (v1.3.1):** no citation detail (conference name/season, table number, page number, test standard, revision date) goes into `s_source` unless it was actually seen in the fetched document. Inferences from standards/conventions (e.g. "EN 10106 conformity implies Epstein per IEC 60404-2") belong in `s_notes`/`s_condition`, explicitly labeled as inferred. This is the v1.0–v1.3 audit's main lesson: the drafting pipeline's failure mode is not fabricated values (zero found), it is embellished citations ("Spring Conference" that was Fall, a "Table 3.2" nobody verified, a test method stated as if printed on a brochure that doesn't mention it).

## Provenance gates

The catalog ships through `tests/test_catalog_provenance_strength.py`. These are non-negotiable for v0.1.0:

1. Every `PropertyValue` cites a source (`s_source` non-empty), unless confidence is `"placeholder"` AND the material is on the explicit placeholder allowlist.
2. Every `PropertyValue.s_units` matches `_PROPERTY_EXPECTED_UNITS` for its slot.
3. Confidence is never `"unspecified"` unless the material is on the explicit migration allowlist (legacy ports without source info, each with a TODO).
4. `confidence="placeholder"` entries have non-empty `s_notes` explaining what real source is pending.
5. Every `Material` has a non-empty `s_specification` OR is in a category that allows informal materials (e.g. `composite`).
6. Every `Material.s_catalog_version <= __catalog_version__`.

These tests run at catalog import time. If they fail, the catalog doesn't ship.

## Catalog data format

For v0.1.0: Python catalog files in `src/emergent_matter_materials/catalog/`. The `_loader.py` module is the **only** seam that knows the data format, switching to YAML/TOML later is a localized change inside `_loader.py` with no public-API impact. Defer the migration until the catalog exceeds ~50 materials or non-coders need to edit it.

## JAX integration

JAX is an **optional extra** (`uv sync --extra jax`). The core dataclasses use plain Python floats. JAX-aware code lives in:

- `jax_interop.py::to_jax_pytree(material, s_missing="omit"|"nan"|"error")`: lazy-imports JAX
- `Electromagnetic.d_resistivity_at_T(T)`: JAX-traceable operating-point callable

**Discrete material choice is NOT this library's concern.** Materials are catalog entries from physics; selecting between them is a discrete optimization problem. The optimizer handles continuous-relaxation (SIMP-style multi-material density) over catalog entries, that math lives in the optimizer, not here.

## Human-readable catalog

`docs/catalog.md` is an auto-generated inventory of every material with all PropertyValues, source citations, conditions, and confidence levels in markdown tables. Regenerate with:

```bash
uv run python scripts/generate_catalog_doc.py
```

The generator is the only thing that writes `docs/catalog.md`. Do NOT hand-edit it, fix the Python catalog files (`src/emergent_matter_materials/catalog/*.py`) and regenerate. A smoke test (`tests/test_catalog_doc_generator.py`) verifies the generator runs to completion and lists every material + alias.
