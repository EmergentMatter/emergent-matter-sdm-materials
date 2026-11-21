# 0002: Liquids use the existing groups, with viscosity in Thermal

## Status

Proposed with the first liquid entry (water).

## Context

A downstream laminar flow and conjugate heat transfer solver needs water's
density, dynamic viscosity, thermal conductivity and specific heat across
its liquid range. The catalog already had slots for density (`Structural`),
conductivity and specific heat (`Thermal`), and temperature tables for all
of them. It had no viscosity slot and no category for a liquid.

Three shapes were considered:

- **A separate `Fluid` record type** next to `Material`. Every accessor
  (`get`, `get_material`, `coverage`, `to_jax_pytree`, `derive_material`)
  and every consumer would then have to handle two record types, and
  density, conductivity and specific heat would be defined twice.
- **A new `fluid` physics group on `Material`.** One home for flow
  properties, but each place that lists the groups (the JAX converter, the
  coverage report, derivation, the catalog document, the validation
  manifest) would need to learn it, and density would either move out of
  `Structural` or exist in two groups.
- **A `dynamic_viscosity` slot on `Thermal` and a `liquid` category.**

## Decision

Add `dynamic_viscosity` (units `Pa*s`, positive, tabulable) to `Thermal`,
and add `liquid` to `MaterialCategory`. A liquid's density stays in
`Structural.density`. Viscosity is a transport property like thermal
conductivity, and a flow solver reads it with conductivity and specific
heat, so it sits in the same group.

## Consequences

- No accessor, converter or document generator changes shape.
  `to_jax_pytree` already flattens the new slot and its table.
- `Thermal` now holds one slot that is not thermal in the strict sense.
  If more flow-only properties arrive (surface tension, bulk viscosity,
  vapor pressure), a `fluid` group may be the better home, and a later
  record would supersede this one.
- Water's tables cover its liquid range at 0.101325 MPa only. Pressure is
  recorded in each row's condition, not as a table axis.
