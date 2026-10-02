"""Crystal anisotropy property group (v0.4.0).

Single-crystal elastic stiffness tensor (Voigt notation) + crystallographic
constants. Useful for:

- **Crystal-plasticity FEM** (JAX-CPFEM, DAMASK, MOOSE-CPFE): slip-system
  shear-strain rate from resolved shear stress + initial CRSS + hardening.
- **Dislocation-density-based hardening models**: Burgers vector enters
  Taylor-equation strengthening, stacking fault energy controls cross-slip
  + twin propensity.
- **Texture-aware structural simulation**: anisotropic stiffness from
  C_ij and orientation-distribution function gives effective polycrystal
  Hill / Hashin-Shtrikman bounds.

**Independent stiffness constants by crystal structure (Voigt notation):**

- **Cubic (FCC / BCC)**: 3 independent: C11, C12, C44.
  C66 = C44, C13 = C12, C33 = C11 are not independent.
- **Hexagonal (HCP)**: 5 independent: C11, C12, C13, C33, C44.
  C66 = (C11 - C12) / 2 is derived, not stored.
- **Tetragonal / rhombohedral**: 6 independent: C11, C12, C13, C33,
  C44, C66 (rhombohedral additionally has off-diagonal C14, but that
  is not stored here for v0.4.0: the diagonal 6 are the practical
  engineering subset).

The dataclass enforces these structural rules in ``__post_init__``: a
cubic crystal with non-None C13/C33/C66 raises, an HCP crystal missing
C13 or C33 raises, etc.

**When to populate vs leave None:**

- **populate** for crystalline materials where slip-mode plasticity or
  elastic anisotropy is relevant to the consumer (pure metals, austenitic
  / ferritic stainless steels, ferrite phase of alloy steels, HCP
  alpha-Ti, ordered-B2 Co-Fe, electrical steels).
- **leave None** for amorphous materials (Metglas, polymers: no crystal
  structure), nanocrystalline composites where ~10nm grains average to
  isotropic behavior at engineering scale (Vitroperm), or brittle
  intermetallics whose CrystalAnisotropy data is sparse and where mechanical
  anisotropy is not the design lever (NdFeB / SmCo magnets: sized by B_r
  / H_cJ / mechanical containment, not C_ij).

**When to populate ``crss_initial``.**
Only for pure metals or low-alloy systems where slip is the dominant
yielding mechanism. **Skip for**: precipitate-hardened alloys (6061-T6
yielding is dominated by Mg2Si precipitates, not slip resistance),
martensitic steels (4140-QT yielding is dominated by lath/packet
microstructure), and brittle intermetallics (NdFeB fractures before
yielding).
"""

from __future__ import annotations

from dataclasses import dataclass

from emergent_matter_materials.property_value import PropertyValue
from emergent_matter_materials.validation import _validate_group_units

#: Allowed s_crystal_structure values. Extend as new materials need them.
_CRYSTAL_STRUCTURES: frozenset[str] = frozenset(
    {
        "FCC",
        "BCC",
        "HCP",
        "tetragonal",
        "rhombohedral",
    }
)


@dataclass(frozen=True)
class CrystalAnisotropy:
    """Single-crystal elastic stiffness tensor + crystallographic constants.

    See module docstring for the structure-vs-fields rules and the
    populate-vs-None policy.

    Required fields (all crystal structures):
        s_crystal_structure: one of ``"FCC" | "BCC" | "HCP" | "tetragonal" | "rhombohedral"``
        c11, c12, c44: PropertyValue, units "Pa"

    Conditionally required:
        c13, c33: PropertyValue for HCP/tetragonal/rhombohedral; must be None for cubic.
        c66: PropertyValue for tetragonal/rhombohedral; must be None for cubic + HCP.

    Optional crystallographic / micromechanical fields:
        burgers_vector: |b| in meters (derived from lattice parameter + slip direction)
        stacking_fault_energy: J/m^2 (FCC-only in practice; controls twin vs slip mode)
        crss_initial: Pa (pure-metal slip-CRSS; see module docstring for skip rules)
    """

    s_crystal_structure: str

    # Cubic constants (all crystal structures require these three)
    c11: PropertyValue
    c12: PropertyValue
    c44: PropertyValue

    # Non-cubic constants
    c13: PropertyValue | None = None
    c33: PropertyValue | None = None
    c66: PropertyValue | None = None

    # Crystallographic / micromechanical
    burgers_vector: PropertyValue | None = None
    stacking_fault_energy: PropertyValue | None = None
    crss_initial: PropertyValue | None = None

    def __post_init__(self) -> None:
        # Validate the structure enum first: downstream rules depend on it.
        if self.s_crystal_structure not in _CRYSTAL_STRUCTURES:
            raise ValueError(
                f"Unknown crystal structure {self.s_crystal_structure!r}, "
                f"allowed: {sorted(_CRYSTAL_STRUCTURES)}"
            )

        # Validate units for every populated field via the shared helper.
        _validate_group_units(
            self,
            group_fields={
                "c11",
                "c12",
                "c44",
                "c13",
                "c33",
                "c66",
                "burgers_vector",
                "stacking_fault_energy",
                "crss_initial",
            },
            b_optional=True,
        )

        # Required-cubic-trio enforcement (c11/c12/c44 cannot be None).
        for s_field in ("c11", "c12", "c44"):
            if getattr(self, s_field) is None:
                raise ValueError(
                    f"CrystalAnisotropy.{s_field} is required for all crystal "
                    f"structures (got None for s_crystal_structure="
                    f"{self.s_crystal_structure!r})"
                )

        # Positivity for elastic constants (negative C_ij is unphysical).
        for s_field in ("c11", "c12", "c44", "c13", "c33", "c66"):
            pv = getattr(self, s_field)
            if pv is not None and pv.d_value <= 0.0:
                raise ValueError(f"CrystalAnisotropy.{s_field} must be positive, got {pv.d_value}")
        for s_field in ("burgers_vector", "stacking_fault_energy", "crss_initial"):
            pv = getattr(self, s_field)
            if pv is not None and pv.d_value <= 0.0:
                raise ValueError(f"CrystalAnisotropy.{s_field} must be positive, got {pv.d_value}")

        # Structure-specific independence rules
        cs = self.s_crystal_structure
        if cs in {"FCC", "BCC"}:
            for s_field in ("c13", "c33", "c66"):
                if getattr(self, s_field) is not None:
                    raise ValueError(
                        f"Cubic {cs} crystal: {s_field} must be None, cubic "
                        f"crystals have only C11/C12/C44 independent "
                        f"(C66=C44, C13=C12, C33=C11 are derived)"
                    )
        elif cs == "HCP":
            for s_field in ("c13", "c33"):
                if getattr(self, s_field) is None:
                    raise ValueError(
                        f"HCP crystal: {s_field} is required (HCP has 5 "
                        f"independent constants C11/C12/C13/C33/C44)"
                    )
            if self.c66 is not None:
                raise ValueError(
                    "HCP crystal: c66 must be None, derived as (C11-C12)/2; "
                    "use d_c66_derived_Pa accessor for the computed value"
                )
        elif cs in {"tetragonal", "rhombohedral"}:
            for s_field in ("c13", "c33", "c66"):
                if getattr(self, s_field) is None:
                    raise ValueError(
                        f"{cs} crystal: {s_field} is required (6 independent "
                        f"constants C11/C12/C13/C33/C44/C66)"
                    )

    # ── Float accessors (hot path for solvers) ───────────────────────────

    @property
    def d_c11_Pa(self) -> float:
        return self.c11.d_value

    @property
    def d_c12_Pa(self) -> float:
        return self.c12.d_value

    @property
    def d_c44_Pa(self) -> float:
        return self.c44.d_value

    @property
    def d_c13_Pa(self) -> float:
        if self.c13 is None:
            raise ValueError(
                f"c13 not defined for {self.s_crystal_structure} crystal "
                f"(cubic: c13=c12 by symmetry; access d_c12_Pa instead)"
            )
        return self.c13.d_value

    @property
    def d_c33_Pa(self) -> float:
        if self.c33 is None:
            raise ValueError(
                f"c33 not defined for {self.s_crystal_structure} crystal "
                f"(cubic: c33=c11 by symmetry; access d_c11_Pa instead)"
            )
        return self.c33.d_value

    @property
    def d_c66_Pa(self) -> float:
        if self.c66 is None:
            raise ValueError(
                f"c66 not stored for {self.s_crystal_structure} crystal "
                f"(cubic: c66=c44; HCP: c66=(c11-c12)/2, "
                f"use d_c66_derived_Pa for HCP)"
            )
        return self.c66.d_value

    @property
    def d_c66_derived_Pa(self) -> float:
        """C66 = (C11 - C12) / 2 for HCP. For cubic crystals returns C44.

        For tetragonal/rhombohedral with stored C66, returns that.
        """
        if self.c66 is not None:
            return self.c66.d_value
        if self.s_crystal_structure == "HCP":
            return 0.5 * (self.c11.d_value - self.c12.d_value)
        # Cubic: by symmetry C66 = C44
        return self.c44.d_value

    @property
    def d_burgers_vector_m(self) -> float:
        if self.burgers_vector is None:
            raise ValueError("burgers_vector not defined for this material")
        return self.burgers_vector.d_value

    @property
    def d_stacking_fault_energy_J_m2(self) -> float:
        if self.stacking_fault_energy is None:
            raise ValueError(
                "stacking_fault_energy not defined for this material "
                "(BCC + HCP rarely have a canonical SFE; populated for FCC)"
            )
        return self.stacking_fault_energy.d_value

    @property
    def d_crss_initial_Pa(self) -> float:
        if self.crss_initial is None:
            raise ValueError(
                "crss_initial not defined for this material "
                "(see module docstring for the skip-vs-populate policy)"
            )
        return self.crss_initial.d_value

    # ── Derived: Zener anisotropy ratio (cubic crystals only) ───────────

    @property
    def d_zener_anisotropy(self) -> float:
        """Zener anisotropy ratio A = 2·C44 / (C11 - C12).

        A = 1: elastically isotropic (e.g. tungsten ~1.0).
        A > 1: stiffer along <111> than <100> (FCC Cu ~3.2; γ-Fe ~3.3).
        A < 1: stiffer along <100> than <111> (rare for engineering metals).

        Defined only for cubic (FCC, BCC). Raises for HCP / tetragonal /
        rhombohedral: those have separate anisotropy parameters (e.g.
        the HCP Zener-like ratio uses C33/C11).
        """
        if self.s_crystal_structure not in {"FCC", "BCC"}:
            raise ValueError(
                f"Zener anisotropy defined only for cubic crystals; "
                f"got {self.s_crystal_structure!r}"
            )
        denominator = self.c11.d_value - self.c12.d_value
        if denominator == 0.0:
            raise ValueError("Zener anisotropy undefined: C11 = C12 (would divide by zero)")
        return 2.0 * self.c44.d_value / denominator


__all__ = ["CrystalAnisotropy"]
