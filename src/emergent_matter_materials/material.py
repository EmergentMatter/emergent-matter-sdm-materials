"""Material: the composite type for a single catalog entry.

Aggregates the five physics groups (structural, electromagnetic,
thermal, manufacturing, crystal_anisotropy) under a single identity.
Each group is optional: a material that's only structural (e.g. a
generic SLS PA12 for housings) can leave ``electromagnetic = None``,
and asking for ``mat.electromagnetic.d_relative_permeability`` will
raise an ``AttributeError`` (None has no attribute): louder than
silently returning a default.

The ``crystal_anisotropy`` group was added in v0.4.0 for single-crystal
elastic stiffness (C_ij), Burgers vector, stacking fault energy, and
slip-CRSS: relevant to crystal-plasticity FEM and dislocation-
density-based hardening models. Populated only for crystalline metals
and alloys; amorphous / nanocrystalline / polymer materials leave it
None.

**Material identity vs catalog identity.** Two distinct identity fields:

- ``s_id`` is the **catalog key**: snake_case, stable, machine-
  friendly. The key in ``MATERIALS["m19_silicon_steel"]``. Aliases
  resolve to this. Renaming an ``s_id`` is a MAJOR catalog version bump.
- ``s_specification`` is the **real-world designation**: formal
  grade/standard as a human would cite it on a drawing. Examples:
  ``"AISI 4140 QT"``, ``"EN AW-6061-T6"``, ``"AK Steel M19 29ga
  fully-processed"``, ``"Hitachi NEOMAX-42H"``, ``"EOS PA 2200"``.
  Empty string is allowed for materials with no formal designation
  (e.g. custom composites), but the provenance-strength tests gate
  this: non-empty is the default expectation.

**Versioning fields.**
- ``s_catalog_version``, which catalog release introduced or last
  reviewed this material entry (semver). Allows cross-version diffs
  to find which materials changed between releases.
- ``s_last_reviewed``: ISO 8601 date of last manual review of the
  citations and values. Periodic reviews can advance this without
  bumping ``s_catalog_version``.

Both are populated per-material; the package-level
``__catalog_version__`` in ``__init__.py`` is the high-water mark
(every material's ``s_catalog_version <= __catalog_version__``:
enforced by a provenance-gate test).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, get_args

from emergent_matter_materials.crystal_anisotropy import CrystalAnisotropy
from emergent_matter_materials.electromagnetic import Electromagnetic
from emergent_matter_materials.manufacturing import Manufacturing
from emergent_matter_materials.structural import Structural
from emergent_matter_materials.thermal import Thermal

MaterialCategory = Literal[
    "metal",
    "polymer",
    "ceramic",
    "composite",
    "elastomer",
    "magnet",  # permanent-magnet alloys (NdFeB, ferrite, AlNiCo)
    "soft_magnetic",  # core materials (silicon steel, Hiperco, MnZn ferrite)
]

#: Runtime counterpart of `MaterialCategory`, derived with `get_args()` so it
#: can never drift from the Literal (STYLE.md: never hand-copy a Literal's
#: members into a separate tuple/frozenset).
_VALID_CATEGORIES: frozenset[str] = frozenset(get_args(MaterialCategory))


@dataclass(frozen=True)
class Material:
    """A catalog entry composing up to four physics-property groups
    under a single material identity."""

    # ── Identity
    s_id: str  # catalog key, e.g. "m19_silicon_steel"
    s_description: str  # human-readable
    s_category: MaterialCategory
    s_specification: str  # formal grade/standard; "" allowed for informal materials

    # ── Catalog versioning
    s_catalog_version: str  # semver of the catalog release that authored/reviewed this entry
    s_last_reviewed: str  # ISO 8601 date "YYYY-MM-DD"

    # ── Physics groups (all optional)
    structural: Structural | None = None
    electromagnetic: Electromagnetic | None = None
    thermal: Thermal | None = None
    manufacturing: Manufacturing | None = None
    crystal_anisotropy: CrystalAnisotropy | None = None

    def __post_init__(self) -> None:
        # s_id sanity
        if not self.s_id:
            raise ValueError("Material.s_id cannot be empty")
        if self.s_id != self.s_id.lower():
            raise ValueError(f"Material.s_id should be snake_case lowercase, got {self.s_id!r}")
        if " " in self.s_id:
            raise ValueError(f"Material.s_id must not contain spaces, got {self.s_id!r}")

        if not self.s_description:
            raise ValueError(f"Material.s_description cannot be empty (s_id={self.s_id!r})")

        # Category enum
        if self.s_category not in _VALID_CATEGORIES:
            raise ValueError(
                f"Material.s_category must be one of {sorted(_VALID_CATEGORIES)}, "
                f"got {self.s_category!r} on s_id={self.s_id!r}"
            )

        # Versioning fields non-empty
        if not self.s_catalog_version:
            raise ValueError(f"Material.s_catalog_version cannot be empty (s_id={self.s_id!r})")
        if not self.s_last_reviewed:
            raise ValueError(f"Material.s_last_reviewed cannot be empty (s_id={self.s_id!r})")
        # Loose ISO 8601 date format check
        if not (
            len(self.s_last_reviewed) == 10
            and self.s_last_reviewed[4] == "-"
            and self.s_last_reviewed[7] == "-"
        ):
            raise ValueError(
                f"Material.s_last_reviewed must be ISO 8601 YYYY-MM-DD, "
                f"got {self.s_last_reviewed!r} (s_id={self.s_id!r})"
            )

        # s_specification can be empty, but only for certain categories where
        # informal materials are expected. For metals/polymers/magnets, every
        # catalog material should have a formal designation. The provenance
        # gate tests enforce this; we don't gate it here to allow placeholder
        # entries during development.

        # At least one group should be populated: a Material with no
        # physics is meaningless catalog noise.
        if all(
            g is None
            for g in (
                self.structural,
                self.electromagnetic,
                self.thermal,
                self.manufacturing,
                self.crystal_anisotropy,
            )
        ):
            raise ValueError(
                f"Material {self.s_id!r} has no physics groups populated. "
                f"At least one of structural / electromagnetic / thermal / "
                f"manufacturing / crystal_anisotropy must be non-None."
            )


__all__ = [
    "Material",
    "MaterialCategory",
]
