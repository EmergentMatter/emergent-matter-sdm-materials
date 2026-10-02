"""Structural property group.

Six required PropertyValue fields covering the standard structural / FEM
inputs: Young's modulus, Poisson's ratio, yield, fatigue endurance,
ultimate tensile, density. All six are required, if you only have
partial structural data, leave the entire ``structural`` slot on
``Material`` as ``None`` rather than constructing an incomplete
``Structural``.

**Three-way strength architecture** (preserved from the org's earlier
structural catalog): this module exposes yield, fatigue endurance, AND ultimate tensile
separately because the right stress metric is context-dependent:

- **Yield (σ_y)**: appropriate for positioning bearings / static
  mounts that rotate only to configure then lock. Permanent set is the
  failure mode.
- **Fatigue endurance (σ_e)**: the right metric for continuously-
  cycling parts (bearings under rotating load, flexures, motor coils
  bearing reciprocating stress). σ_y under-predicts failure for
  cyclic loads. The org's earlier structural catalog defaults to this
  for bearing auto-force + the optimizer stress constraint.
- **Ultimate tensile (σ_UTS)**: peak-overload / fracture-only sizing,
  for one-shot impact / jam / crash. NOT appropriate for continuous
  operation; consumers must opt in explicitly when fracture is the
  only concern.
- **Flexural strength (σ_flex)**: added v0.3.0 for brittle materials
  (sintered NdFeB, SmCo 2:17, ceramics) where there is NO ductile
  yield and the vendor publishes only a 3-point-bend ASTM-C1161-class
  rupture stress. Storing this in ``ultimate_tensile`` would be
  misleading: σ_flex on a brittle material is typically 1.3-1.6× the
  equivalent tensile fracture stress because the bend specimen
  compresses out surface flaws on the tension side. Use σ_flex as a
  fracture envelope (σ_max < σ_flex under bending), NOT as a ductile
  yield. For pure-tension stress states on brittle materials,
  derate ~30-40%.

Each value carries its own citation via the PropertyValue's
``s_source``, so a consumer can reason about provenance per-metric.
"""

from __future__ import annotations

from dataclasses import dataclass

from emergent_matter_materials.property_value import PropertyValue
from emergent_matter_materials.validation import _validate_group_units


class StructuralStrengthUnavailable(ValueError):
    """Raised when a material has no usable structural strength basis.

    Neither ``yield_stress`` nor ``ultimate_tensile`` is populated, so
    :meth:`Structural.resolve_design_strength` cannot return a documented
    allowable. Subclasses ``ValueError`` so existing ``except ValueError``
    handlers (e.g. around ``_req``) keep working unchanged.
    """


#: Strength-basis vocabulary returned by the design-strength resolver. A
#: downstream UI can render "strength basis: <token>".
STRENGTH_BASIS_YIELD = "yield_stress"  # 0.2%-offset yield (vendor/standard)
STRENGTH_BASIS_ULTIMATE = "ultimate_tensile"  # Tier-1 UTS, no derate applied
STRENGTH_BASIS_DERATED_ULTIMATE = "derated_ultimate_tensile"  # UTS * caller-supplied derate
STRENGTH_BASIS_UNKNOWN = "unknown"  # no yield and no UTS (probe only)

#: All recognized basis tokens (the first three are value-bearing; "unknown"
#: is only ever returned by the non-raising :attr:`Structural.s_strength_basis`
#: probe: resolution raises instead of returning it).
STRENGTH_BASES = (
    STRENGTH_BASIS_YIELD,
    STRENGTH_BASIS_ULTIMATE,
    STRENGTH_BASIS_DERATED_ULTIMATE,
    STRENGTH_BASIS_UNKNOWN,
)


@dataclass(frozen=True)
class StructuralStrength:
    """A resolved structural strength allowable plus the basis it came from.

    Returned by :meth:`Structural.resolve_design_strength`. ``s_basis`` is one
    of the value-bearing ``STRENGTH_BASIS_*`` tokens (never ``"unknown"``:
    resolution raises rather than return an unusable result). ``s_source`` is
    copied verbatim from the underlying PropertyValue so provenance travels
    with the value; a UI can show "strength basis: UTS, <source>".
    ``d_derate_factor`` is set only when ``s_basis`` is the derated token.
    """

    d_value_Pa: float
    s_basis: str
    s_units: str
    s_source: str
    d_derate_factor: float | None = None


@dataclass(frozen=True)
class Structural:
    """Structural properties: all fields optional (Tier-1-only policy).

    Under the v0.2.0 "Tier 1 only" policy, only fields with verified
    primary-source data populate. A material may have only a subset
    of structural properties (e.g. only fatigue_endurance from
    Shigley's; only E and density from a vendor TDS). At least one
    field should be populated, if a material has nothing structural,
    leave the entire ``structural`` slot on Material as ``None``
    rather than constructing an empty Structural.
    """

    youngs_modulus: PropertyValue | None = None  # Pa
    poisson_ratio: PropertyValue | None = None  # dimensionless, 0 < ν < 0.5
    yield_stress: PropertyValue | None = None  # Pa, 0.2% offset for metals
    fatigue_endurance: PropertyValue | None = None  # Pa, 10⁷ cycles fully-reversed for metals
    ultimate_tensile: PropertyValue | None = None  # Pa, ductile fracture
    flexural_strength: PropertyValue | None = (
        None  # Pa, ASTM C1161-class 3-pt bend (brittle materials)
    )
    density: PropertyValue | None = None  # kg/m³
    # Vickers hardness number HV (kgf/mm² by definition, reported unitless by
    # convention). Drives machining/grinding feasibility and abrasive-wear
    # margins; published per grade on sintered-magnet datasheets.
    hardness_vickers: PropertyValue | None = None
    # Compressive strength, Pa. Brittle intermetallics fracture in bending at
    # flexural_strength but carry a far higher load in pure compression; this
    # is the compressive envelope for press-fit and interference sizing.
    compressive_strength: PropertyValue | None = None

    def __post_init__(self) -> None:
        _validate_group_units(
            self,
            group_fields={
                "youngs_modulus",
                "poisson_ratio",
                "yield_stress",
                "fatigue_endurance",
                "ultimate_tensile",
                "flexural_strength",
                "density",
                "hardness_vickers",
                "compressive_strength",
            },
            b_optional=True,
        )

        # Poisson ratio physical range (only if present)
        if self.poisson_ratio is not None and not (0.0 < self.poisson_ratio.d_value < 0.5):
            raise ValueError(
                f"poisson_ratio must be in (0.0, 0.5), got {self.poisson_ratio.d_value}"
            )

        # Positivity for dimensional quantities, only on present fields
        for f_name in (
            "youngs_modulus",
            "yield_stress",
            "fatigue_endurance",
            "ultimate_tensile",
            "flexural_strength",
            "density",
            "hardness_vickers",
            "compressive_strength",
        ):
            pv = getattr(self, f_name)
            if pv is not None and pv.d_value <= 0.0:
                raise ValueError(f"Structural.{f_name} must be positive, got {pv.d_value}")

        # Sanity ordering: yield <= UTS, only if both present
        if (
            self.yield_stress is not None
            and self.ultimate_tensile is not None
            and self.yield_stress.d_value > self.ultimate_tensile.d_value
        ):
            raise ValueError(
                f"Structural: yield_stress ({self.yield_stress.d_value} Pa) > "
                f"ultimate_tensile ({self.ultimate_tensile.d_value} Pa). "
                f"This is physically impossible; check the source citations."
            )

    # ── Solver-hot-path numeric accessors (raise on missing)

    def _req(self, s_field_name: str) -> PropertyValue:
        pv = getattr(self, s_field_name)
        if pv is None:
            raise ValueError(
                f"Structural.{s_field_name} not defined for this material "
                f"(field is None: Tier 1 source not yet available)"
            )
        return pv

    @property
    def d_youngs_modulus_Pa(self) -> float:
        return self._req("youngs_modulus").d_value

    @property
    def d_poisson_ratio(self) -> float:
        return self._req("poisson_ratio").d_value

    @property
    def d_yield_stress_Pa(self) -> float:
        return self._req("yield_stress").d_value

    @property
    def d_fatigue_endurance_Pa(self) -> float:
        return self._req("fatigue_endurance").d_value

    @property
    def d_ultimate_tensile_Pa(self) -> float:
        return self._req("ultimate_tensile").d_value

    @property
    def d_flexural_strength_Pa(self) -> float:
        return self._req("flexural_strength").d_value

    @property
    def d_density_kg_m3(self) -> float:
        return self._req("density").d_value

    @property
    def d_hardness_HV(self) -> float:
        return self._req("hardness_vickers").d_value

    @property
    def d_compressive_strength_Pa(self) -> float:
        return self._req("compressive_strength").d_value

    # ── Consumer-safe design-strength resolution (added v1.10.0)

    def resolve_design_strength(
        self, *, ultimate_derate: float | None = None
    ) -> StructuralStrength:
        """Resolve a single usable structural strength scalar + its basis.

        Resolution order (the generic static / quasi-static allowable):

        1. ``yield_stress``     -> basis ``"yield_stress"``
        2. ``ultimate_tensile`` -> basis ``"ultimate_tensile"`` (or
           ``"derated_ultimate_tensile"`` when ``ultimate_derate`` is given)

        Raises :class:`StructuralStrengthUnavailable` (a ``ValueError``) if
        neither is populated: it never silently returns 0 or guesses a value.

        This lets a structural consumer use materials like SLS PA12, whose
        datasheet reports a tensile strength but no distinct yield, WITHOUT
        pretending UTS is yield. ``s_basis`` tells the consumer/UI which
        quantity it received so it can label it and derate if appropriate.

        Deliberately does NOT auto-substitute ``fatigue_endurance`` or
        ``flexural_strength``: those are load-context-specific (fatigue for
        cyclic loads; flexural is a 3-pt-bend envelope that must be derated
        ~30-40% for pure tension; see the module docstring). A consumer that
        needs them reads those dedicated accessors explicitly. This resolver
        answers the narrower "is there a usable static strength basis, and
        which is it?" used for material selection / screening.

        Args:
            ultimate_derate: optional factor in ``(0, 1]`` applied ONLY when
                resolution falls through to ``ultimate_tensile`` (i.e. no yield
                is available). The caller owns this number: it is an
                application safety choice, NOT catalog data, and when supplied
                the basis is reported as ``"derated_ultimate_tensile"`` so the
                derate's provenance is explicit. Ignored when ``yield_stress``
                is used (yield is already a design quantity).
        """
        if self.yield_stress is not None:
            pv = self.yield_stress
            return StructuralStrength(pv.d_value, STRENGTH_BASIS_YIELD, pv.s_units, pv.s_source)
        if self.ultimate_tensile is not None:
            pv = self.ultimate_tensile
            if ultimate_derate is not None:
                if not (0.0 < ultimate_derate <= 1.0):
                    raise ValueError(f"ultimate_derate must be in (0, 1], got {ultimate_derate}")
                return StructuralStrength(
                    pv.d_value * ultimate_derate,
                    STRENGTH_BASIS_DERATED_ULTIMATE,
                    pv.s_units,
                    pv.s_source,
                    d_derate_factor=ultimate_derate,
                )
            return StructuralStrength(pv.d_value, STRENGTH_BASIS_ULTIMATE, pv.s_units, pv.s_source)
        raise StructuralStrengthUnavailable(
            "No structural strength basis available: both yield_stress and "
            "ultimate_tensile are None. Populate a Tier-1 strength value, or "
            "treat this material as having no strength data (s_strength_basis "
            "returns 'unknown')."
        )

    @property
    def d_design_strength_Pa(self) -> float:
        """Bare-float design-strength allowable (solver hot path).

        Convenience over :meth:`resolve_design_strength` (no derate): resolves
        ``yield_stress`` then ``ultimate_tensile``. Raises
        :class:`StructuralStrengthUnavailable` if neither exists.
        """
        return self.resolve_design_strength().d_value_Pa

    @property
    def s_strength_basis(self) -> str:
        """Non-raising basis probe: ``"yield_stress"``, ``"ultimate_tensile"``,
        or ``"unknown"``.

        Lets a UI display the basis and gate material selection WITHOUT
        catching an exception (mirrors the ``coverage()`` philosophy). Returns
        ``"unknown"`` when no strength basis exists; in that case
        :meth:`resolve_design_strength` and :attr:`d_design_strength_Pa` raise.
        """
        if self.yield_stress is not None:
            return STRENGTH_BASIS_YIELD
        if self.ultimate_tensile is not None:
            return STRENGTH_BASIS_ULTIMATE
        return STRENGTH_BASIS_UNKNOWN


__all__ = [
    "STRENGTH_BASES",
    "STRENGTH_BASIS_DERATED_ULTIMATE",
    "STRENGTH_BASIS_ULTIMATE",
    "STRENGTH_BASIS_UNKNOWN",
    "STRENGTH_BASIS_YIELD",
    "Structural",
    "StructuralStrength",
    "StructuralStrengthUnavailable",
]
