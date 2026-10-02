# 0001: Rotational-loss data source policy

## Status

Accepted. The schema and resolver this decision authorizes have shipped
(`RotationalLossData` in v1.5.0, `resolve_rotational_loss_data_from_material`
in v1.6.0). Sourcing real rotational-loss data and wiring downstream solver
consumption have not; see Consequences.

## Context

A downstream magnetostatic finite-element (FEM) solver can detect a
rotating, non-collinear `B` locus per cell and defers it as `rotational_flux_not_modeled`. It cannot
honestly assign a validated rotational-flux loss number, because the
catalog had no rotational-loss data at all.

The catalog has been source-Tier-1-only since v0.2.0: every `PropertyValue`
must be `measured`, `datasheet`, or `standard` ("bad data is worse than no
data"). Rotational-loss data, in the real world, is overwhelmingly published
in peer-reviewed academic literature, i.e. source-Tier-2 (`handbook`).
Vendors essentially never publish it; it is a research-grade measurement,
usually from a Rotational Single Sheet Tester (RSST). Under a strict
Tier-1-only reading, validated rotational loss could never exist for any
material: there is almost no Tier-1 rotational source to admit.

Three candidate answers were considered:

- **Hold the line.** Keep Tier-1-only, unmodified. Honest, but the feature
  never ships: rotational cells stay deferred indefinitely, since no vendor
  or standards body is likely to publish rotational-loss data.
- **Widen the catalog-wide rule.** Permit `handbook` (source-Tier-2)
  confidence everywhere, not just for rotational data. Rejected: this
  weakens the Tier-1 guarantee for every existing and future property, for
  a need that is specific to one physical quantity.
- **Scope the exception by type.** Keep the catalog-wide Tier-1 rule
  exactly as it is, and declare rotational-loss data a separate, explicitly
  Tier-2-permitted subdomain, structurally incapable of touching any other
  property. This is the option that was adopted.

A second hazard shaped the decision as much as the source-policy question
itself: the word "Tier" was about to be overloaded three ways in the same
feature. A rotational-loss record needs to answer three independent
questions that must never be conflated, or a screening guess can quietly
become a fake validated number: how authoritative is the source
(source-confidence), how much data and metadata is present
(data-completeness), and what a consumer is allowed to do with it
(model fidelity). The catalog had already been bitten once by exactly this
class of overload: `SteinmetzData.s_confidence` holds a calibration-method
label while everywhere else `s_confidence` means source quality (the rename has not been done yet).

## Decision

Adopted the scoped exception, with a locked vocabulary and a locked build
order.

**Source policy.** The catalog-wide Tier-1-only rule is unchanged for every
non-rotational property. Rotational-loss data is a separate, explicitly
scoped subdomain in which source-Tier-2 (`handbook`) is admissible to
validated use, alongside the existing source-Tier-1 set: the validated set
is `{measured, datasheet, standard, handbook}`. A Tier-2 rotational record
does not get an easier completeness bar: it must clear the same full
data-completeness ladder a Tier-1 record would. Source-Tier-3/4
(`aggregator`, `derived`, `estimated`) rotational data may be recorded for
traceability but never reaches validated eligibility.

The non-leak guarantee is structural, not a review convention: rotational
data lives in its own composite type, `RotationalLossData`, never in a
`PropertyValue`. The existing provenance gate
(`tests/test_catalog_provenance_strength.py`) iterates `PropertyValue`
instances and therefore never sees rotational data; it was not relaxed. A
separate rotational provenance gate owns the rotational subdomain, so the
two gates operate on disjoint types and the exception cannot leak to
non-rotational properties even by future accident.

**Vocabulary.** Three axes, never conflated and never abbreviated to a bare
"Tier N": **source-Tier N** (the existing `ConfidenceLevel` enum),
**Level N** (data completeness, 0 through 3), and **Model-Tier N** (what a
downstream solver may do with the data; computed by the consumer, not
stored in the catalog). `s_confidence` stays source-confidence only. Full
definitions, including the Level 0-3 completeness ladder and its
mandatory-field rules, live in `RotationalLossData`'s own docstring in
`src/emergent_matter_materials/rotational_loss.py`; this record does not
duplicate them.

**Field shape.** Additive, default-empty, on `Electromagnetic`:
`rotational_loss_models: tuple[RotationalLossData, ...] = ()`. A tuple, not
a single optional field, because one material can carry multiple
rotational-loss records that differ by source, data form, completeness
Level, frequency, or measurement method, and the future resolver needs to
select among them for a given `(B, f, T)` query.

**Integration pattern.** Follows `BHCurveData` and `SteinmetzData`: excluded
from the units validator (it is not a `PropertyValue`), excluded from the
flat SI accessor map, consumed through the object path
(`material.electromagnetic.rotational_loss_models`), and excluded from
`to_jax_pytree` flattening until a real consumer needs it in a pytree.

**Status vocabulary**, frozen for cross-repo string matching: the resolver
returns one of `missing_rotational_loss_data`,
`rotational_loss_out_of_range`, `rotational_loss_incomplete`, or
`rotational_loss_diagnostic_only`; the solver's own
`rotational_flux_not_modeled` disposition composes with these as effect
follows cause. A blocked or diagnostic result never collapses to `0 W` in a
validated total. Full behavior is documented in
`resolve_rotational_loss_data_from_material`'s own docstring in
`src/emergent_matter_materials/rotational_resolver.py`.

**Build order**, each step separately reviewable and none skipped: schema
scaffold, then synthetic fixtures, then the resolver, then classification
and status tests, then real sourced data, then downstream solver consumption.
Fake data never substitutes for real data; the resolver must be stable
before any cross-repo consumption.

## Consequences

Shipped: the `RotationalLossData` schema and its type-scoped provenance
gate (v1.5.0), and the eligibility resolver against synthetic fixtures
(v1.6.0). Every material still resolves `missing_rotational_loss_data`;
there is no real rotational-loss data in the catalog, no loss computation,
and no downstream solver consumption.

Deferred: sourcing real rotational-loss records is a separate piece of
work, condensing what three source-hunting passes tried and why each came
up short. Downstream solver consumption cannot start until real data exists
and the resolver has classification and status-behavior test coverage
against it.

One question from the original framing was flagged for confirmation and
never explicitly closed: whether source-Tier-3/4 rotational data should be
excluded entirely, rather than capped at diagnostic-only use. This does not
block the schema or resolver already shipped, but should be settled before
the first real Tier-3/4 rotational record is ever recorded.
