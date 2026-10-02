"""Electromagnetic property group.

All fields are optional: different material classes care about
different subsets:

- **Conductors** (Cu, Al): need ``resistivity_at_20C`` and
  ``temp_coeff_resistivity`` for winding loss + thermal coupling.
- **Soft magnetic** (M19 silicon steel, MnZn ferrite, Hiperco):
  need ``relative_permeability``, ``saturation_flux``, ``core_loss``.
- **Permanent magnets** (NdFeB, ferrite, AlNiCo): need ``coercivity``,
  ``remanence``, ``temp_coeff_remanence``.
- **Insulators** (PEEK, PEI): need ``dielectric_strength``,
  ``relative_permittivity``.

A consumer asking for a property a material doesn't have gets a clear
``ValueError`` from the hot-path accessor, not silent corruption.

**Operating-point callables.**
``d_resistivity_at_T(d_T_C)`` is JAX-traceable: accepts a ``jnp``
scalar, returns the same type, no Python-side branching. Backprop
through temperature works. Uses the standard linear-temperature-
coefficient resistivity model.

Other operating-point dependencies (μ_r vs B amplitude, core_loss vs
frequency/flux) are stored as one operating-point snapshot in v0.1
with the conditions in ``PropertyValue.s_condition``; full curve-
fitted models can be added in v0.2 when an EM-loss optimizer needs
them.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from emergent_matter_materials.bh_curve import BHCurveData
from emergent_matter_materials.property_value import PropertyValue
from emergent_matter_materials.rotational_loss import RotationalLossData
from emergent_matter_materials.steinmetz import SteinmetzData
from emergent_matter_materials.validation import _validate_group_units

if TYPE_CHECKING:
    # Type-only: `jax` stays an optional extra (STYLE.md's lazy-import rule),
    # and `from __future__ import annotations` means this name is never
    # resolved at runtime, only by mypy.
    import jax


@dataclass(frozen=True)
class Electromagnetic:
    """Electromagnetic properties: all fields optional, populated per
    material class. Validators reject mismatched units on whichever
    fields ARE populated."""

    # ── Conductors
    resistivity_at_20C: PropertyValue | None = None
    temp_coeff_resistivity: PropertyValue | None = None

    # ── Soft magnetic
    relative_permeability: PropertyValue | None = None
    saturation_flux: PropertyValue | None = None
    # Tabulated DC (or quasi-static) magnetization curve. Stored as a
    # composite BHCurveData carrying its own provenance (s_source,
    # s_condition, s_confidence, s_notes) and a strict-monotonicity +
    # ferromagnetic-initial-slope validator. Consumed by magnetostatic
    # FEM solvers that need the full nonlinear ν(||B||) constitutive
    # relation, not just a scalar μ_r. Added v1.2.0. See
    # ``emergent_matter_materials.bh_curve`` for the dataclass.
    bh_curve: BHCurveData | None = None

    # ── Hard magnetic (permanent magnets)
    coercivity: PropertyValue | None = None
    remanence: PropertyValue | None = None
    temp_coeff_remanence: PropertyValue | None = None
    # Reversible temperature coefficient of intrinsic coercivity α(HcJ),
    # 1/K (i.e. fractional ΔHcJ per K, same convention as
    # temp_coeff_remanence). For permanent magnets this is the
    # demag-margin-vs-temperature scalar: HcJ falls with temperature
    # faster (more negative α) than Br does, so a motor's worst-case
    # demag check at peak operating temperature is governed by α(HcJ),
    # not α(Br). Published per grade on the same vendor TDS as HcJ
    # itself. Added v1.8.0.
    temp_coeff_coercivity: PropertyValue | None = None
    # Recoil permeability μ_rec: small-signal slope (1/μ₀)·(dB/dH) of the
    # recoil line on the 2nd-quadrant B-H curve. Used by FEM magnetostatics
    # solvers to build per-region reluctivity ν = 1/(μ₀·μ_rec) for PM
    # regions. Stored as a SEPARATE slot from ``relative_permeability``
    # because the two quantities are physically distinct: ``relative_
    # permeability`` is the soft-magnetic μ_r near origin / at saturation
    # operating points, which is N/A-by-physics for hard magnets sitting
    # on the 2nd-quadrant demag curve. μ_rec is the permanent-magnet
    # equivalent and is defined in IEC 60404-8-1 as an "additional
    # magnetic property". Dimensionless, typically 1.02-1.10.
    recoil_permeability: PropertyValue | None = None
    # Maximum energy product (BH)max, J/m³ (1 MGOe = 7957.7 J/m³): the figure
    # of merit for permanent-magnet grade selection. Arnold's grade numbers are
    # the nominal (BH)max in MGOe (N42 = 42 MGOe). Stored as the vendor's
    # NOMINAL value; s_notes carries the published min/max band.
    energy_product_max: PropertyValue | None = None

    # ── Core loss (Steinmetz at one operating point in v0.1; s_condition
    #             carries the B_ref and f_ref the value was measured at)
    core_loss: PropertyValue | None = None

    # ── Steinmetz fit coefficients (v1.3.0). Composite SteinmetzData
    # carrying the (k, alpha, beta) triple, the reference point the fit
    # was anchored on, validity ranges, and provenance. Used by
    # magnetostatic FEM solvers that evaluate
    # P_core_specific[W/kg] = k · f^alpha · B_pk^beta at arbitrary
    # operating points inside the validity envelope. Optional; materials
    # without a validated fit leave this None and downstream
    # core-loss code reports "missing_material_loss_data". See
    # `emergent_matter_materials.steinmetz` for the dataclass.
    steinmetz: SteinmetzData | None = None

    # ── Rotational-flux core loss (v1.x scaffold; Phase 1: schema only).
    # A TUPLE of composite RotationalLossData records (default empty), so one
    # material may carry several records differing by source / form /
    # completeness Level / frequency / measurement method without schema
    # churn. A rotating B-locus is a different physical problem from the 1-D
    # alternating waveform that `steinmetz` / `core_loss` model: alternating
    # coefficients do NOT validate rotational loss. Empty tuple == "no
    # rotational data" (the default and current state for every material).
    # Consumed via the object path only; intentionally NOT in the flat
    # `_PROPERTY_MAP`, NOT in `_validate_group_units` group_fields (it is a
    # composite collection, not a PropertyValue), and skipped by
    # `to_jax_pytree`. See `emergent_matter_materials.rotational_loss` and
    # docs/adr/0001-rotational-loss-source-policy.md.
    rotational_loss_models: tuple[RotationalLossData, ...] = ()

    # ── Insulators
    dielectric_strength: PropertyValue | None = None
    relative_permittivity: PropertyValue | None = None

    def __post_init__(self) -> None:
        _validate_group_units(
            self,
            group_fields={
                "resistivity_at_20C",
                "temp_coeff_resistivity",
                "relative_permeability",
                "saturation_flux",
                "coercivity",
                "remanence",
                "temp_coeff_remanence",
                "temp_coeff_coercivity",
                "recoil_permeability",
                "energy_product_max",
                "core_loss",
                "dielectric_strength",
                "relative_permittivity",
            },
            b_optional=True,
        )

        # Positivity on the dimensional ones that ARE present
        for f_name in (
            "resistivity_at_20C",
            "saturation_flux",
            "coercivity",
            "remanence",
            "energy_product_max",
            "core_loss",
            "dielectric_strength",
        ):
            pv = getattr(self, f_name)
            if pv is not None and pv.d_value <= 0.0:
                raise ValueError(f"Electromagnetic.{f_name} must be positive, got {pv.d_value}")

        # Relative permeability > 0: covers diamagnetic (μ_r < 1, e.g.
        # pure_copper at 0.999994), non-magnetic (μ_r ≈ 1), paramagnetic
        # (μ_r > 1 but small, e.g. aluminum_6061_t6 at 1.000022), and
        # soft-magnetic (μ_r in 10³-10⁵). v0.7.0 relaxed the previous
        # μ_r ≥ 1 rule: diamagnetics are real engineering physics (Cu
        # winding susceptibility matters for MRI shimming + low-noise
        # solenoid design) and have well-established Tier-1 sources
        # (CRC Handbook 95th ed. Section 12, NIST SRD).
        if self.relative_permeability is not None and self.relative_permeability.d_value <= 0.0:
            raise ValueError(
                f"Electromagnetic.relative_permeability must be > 0 "
                f"(diamagnetic μ_r < 1 is allowed as of v0.7.0; "
                f"zero or negative is unphysical), "
                f"got {self.relative_permeability.d_value}"
            )

        # Relative permittivity >= 1 (same logic; vacuum has ε_r=1)
        if self.relative_permittivity is not None and self.relative_permittivity.d_value < 1.0:
            raise ValueError(
                f"Electromagnetic.relative_permittivity must be >= 1.0, "
                f"got {self.relative_permittivity.d_value}"
            )

        # Recoil permeability > 0: physically near 1.0+ for sintered
        # rare-earth PMs (1.02-1.10 range). Zero or negative is
        # unphysical. We do NOT enforce μ_rec >= 1 because Arnold's
        # measurement white paper notes the value depends slightly on
        # the measurement start/end points and some published values
        # for bonded grades are reported just below 1.0: > 0 is the
        # safe physical floor.
        if self.recoil_permeability is not None and self.recoil_permeability.d_value <= 0.0:
            raise ValueError(
                f"Electromagnetic.recoil_permeability must be > 0 "
                f"(zero or negative is unphysical), "
                f"got {self.recoil_permeability.d_value}"
            )

        # rotational_loss_models: composite collection (NOT a PropertyValue,
        # so deliberately absent from _validate_group_units group_fields and
        # from _PROPERTY_MAP). Each element validates itself in its own
        # __post_init__; here we only guard the container shape so a stray
        # non-record can't slip into the tuple.
        if not isinstance(self.rotational_loss_models, tuple):
            # TRY004 suppressed deliberately: every __post_init__ validator in
            # this package raises ValueError, and test_rotational_loss_schema.py
            # asserts ValueError for both of these guards. Switching to
            # TypeError would be a public API break, not a lint fix.
            raise ValueError(  # noqa: TRY004
                "Electromagnetic.rotational_loss_models must be a tuple "
                f"(got {type(self.rotational_loss_models).__name__}); use the "
                f"default empty tuple () when there is no rotational data."
            )
        for rec in self.rotational_loss_models:
            if not isinstance(rec, RotationalLossData):
                raise ValueError(  # noqa: TRY004  (see rationale above)
                    "Electromagnetic.rotational_loss_models entries must be "
                    f"RotationalLossData instances, got {type(rec).__name__}."
                )

    # ── Hot-path accessors (None-safe: raise on missing)

    def _req(self, s_field_name: str) -> PropertyValue:
        pv = getattr(self, s_field_name)
        if pv is None:
            raise ValueError(
                f"Electromagnetic.{s_field_name} not defined for this material "
                f"(field is None: material doesn't have this property)"
            )
        return pv

    @property
    def d_resistivity_at_20C_ohm_m(self) -> float:
        return self._req("resistivity_at_20C").d_value

    @property
    def d_temp_coeff_resistivity_per_K(self) -> float:
        return self._req("temp_coeff_resistivity").d_value

    @property
    def d_relative_permeability(self) -> float:
        return self._req("relative_permeability").d_value

    @property
    def d_saturation_flux_T(self) -> float:
        return self._req("saturation_flux").d_value

    @property
    def d_coercivity_A_m(self) -> float:
        return self._req("coercivity").d_value

    @property
    def d_remanence_T(self) -> float:
        return self._req("remanence").d_value

    @property
    def d_temp_coeff_remanence_per_K(self) -> float:
        return self._req("temp_coeff_remanence").d_value

    @property
    def d_temp_coeff_coercivity_per_K(self) -> float:
        """Reversible temp coefficient of intrinsic coercivity α(HcJ), 1/K.

        Fractional ΔHcJ per K (e.g. -6.2e-3 for plain sintered NdFeB).
        Raises ValueError if the material has no published α(HcJ).
        """
        return self._req("temp_coeff_coercivity").d_value

    @property
    def d_recoil_permeability(self) -> float:
        """Recoil permeability μ_rec, dimensionless.

        Small-signal slope (1/μ₀)·(dB/dH) of the recoil line on the
        2nd-quadrant B-H curve. Used to derive PM-region reluctivity
        ν = 1/(μ₀·μ_rec) in magnetostatic FEM solvers.
        """
        return self._req("recoil_permeability").d_value

    @property
    def d_energy_product_max_J_m3(self) -> float:
        return self._req("energy_product_max").d_value

    @property
    def d_core_loss_W_kg(self) -> float:
        return self._req("core_loss").d_value

    @property
    def d_dielectric_strength_V_m(self) -> float:
        return self._req("dielectric_strength").d_value

    @property
    def d_relative_permittivity(self) -> float:
        return self._req("relative_permittivity").d_value

    # ── Steinmetz hot-path accessors (v1.3.0)
    #
    # Downstream FEM consumers read these via
    # `getattr(em, "d_steinmetz_k", None)`. They return `None` (not
    # raise) when the underlying `steinmetz` composite is absent, so
    # downstream code can branch on missing-data without try/except.
    # This is the only block of accessors in this group that returns
    # `None` instead of raising: the rest use `_req()` which raises
    # `ValueError` on missing. The semantics differ because the
    # Steinmetz triple is consumed by an opt-in core-loss code path
    # that must distinguish "no validated fit" (None) from "fit
    # present" (numeric).

    @property
    def d_steinmetz_k(self) -> float | None:
        """Steinmetz prefactor `k`, units `[W/kg] / (Hz^alpha · T^beta)`.

        Returns `None` if no Steinmetz fit is recorded for this
        material; the downstream core-loss code consumes this via
        `getattr(em, "d_steinmetz_k", None)` and treats `None` as
        the missing-data signal.
        """
        return None if self.steinmetz is None else self.steinmetz.d_k

    @property
    def d_steinmetz_alpha(self) -> float | None:
        """Steinmetz frequency exponent. `None` if no fit."""
        return None if self.steinmetz is None else self.steinmetz.d_alpha

    @property
    def d_steinmetz_beta(self) -> float | None:
        """Steinmetz flux-density exponent. `None` if no fit."""
        return None if self.steinmetz is None else self.steinmetz.d_beta

    # ── B-H curve hot-path accessors (v1.2.0)
    #
    # Direct field access is `em.bh_curve` -> `BHCurveData | None`. The
    # `d_bh_curve_B_T` / `d_bh_curve_H_A_m` accessors below raise
    # ValueError via `_req()` when the field is None: same None-safety
    # pattern as the rest of the hot-path accessors.

    @property
    def d_bh_curve_B_T(self) -> tuple[float, ...]:
        """B-table from the tabulated DC magnetization curve, in tesla.

        Strictly ascending tuple paired index-for-index with
        ``d_bh_curve_H_A_m``. Raises ``ValueError`` if the underlying
        ``bh_curve`` field is None (material has no published curve in
        this catalog).
        """
        return self._req_bh_curve().d_B_table_T

    @property
    def d_bh_curve_H_A_m(self) -> tuple[float, ...]:
        """H-table from the tabulated DC magnetization curve, in A/m.

        Strictly ascending tuple paired index-for-index with
        ``d_bh_curve_B_T``. Raises ``ValueError`` if the underlying
        ``bh_curve`` field is None.
        """
        return self._req_bh_curve().d_H_table_A_m

    def _req_bh_curve(self) -> BHCurveData:
        """Same None-safety as ``_req``, typed for the ``BHCurveData``
        composite instead of ``PropertyValue`` -- ``bh_curve`` is the only
        composite (non-``PropertyValue``) field with hot-path accessors in
        this group.
        """
        if self.bh_curve is None:
            raise ValueError(
                "Electromagnetic.bh_curve not defined for this material "
                "(field is None, material doesn't have this property)"
            )
        return self.bh_curve

    # ── Operating-point callable (JAX-traceable)

    def d_resistivity_at_T(self, d_T_C: float | jax.Array) -> float | jax.Array:
        """Linear-temperature-coefficient resistivity model.

        JAX-traceable: accepts a ``jnp`` scalar (or array) for
        ``d_T_C`` and returns the same type without Python-side
        branching, so consumers can ``jax.grad`` / ``jax.vmap`` through
        temperature. Typed as ``float | jax.Array`` rather than ``Any``:
        the arithmetic below is agnostic to which one it gets, and `jax`
        stays an optional, lazily-imported extra (the `jax.Array` name
        here is type-only, per the ``TYPE_CHECKING`` import above).

        Standard linear-temperature-coefficient resistivity model.

        Raises ``ValueError`` if the underlying ``resistivity_at_20C``
        or ``temp_coeff_resistivity`` fields are None.
        """
        d_rho_20 = self._req("resistivity_at_20C").d_value
        d_alpha = self._req("temp_coeff_resistivity").d_value
        return d_rho_20 * (1.0 + d_alpha * (d_T_C - 20.0))


__all__ = ["Electromagnetic"]
