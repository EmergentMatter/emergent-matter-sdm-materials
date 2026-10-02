"""Unified multi-physics materials substrate for the EmergentMatter SDM ecosystem.

Public API surface assembled here for one-stop import. See README.md for the
schema diagram.
"""

from __future__ import annotations

__version__ = "0.0.0"

# Data semver, bumps independently of package semver:
#   MAJOR: schema break or material removal (downstream pinning breaks)
#   MINOR: add materials / add new fields / add new aliases
#   PATCH: correct values / update citations / refine conditions
#
# Optimization artifacts should record both: "optimized against
# emergent-matter-sdm-materials __version__=X.Y.Z, __catalog_version__=A.B.C".
__catalog_version__ = "0.0.0"


# ── Core wrapper
# ── Accessor API
from emergent_matter_materials.accessors import (
    MATERIALS,
    CoverageReport,
    coverage,
    get,
    get_material,
    get_structural_strength,
    get_with_metadata,
    list_aliases,
    list_materials,
    list_properties,
    material_summary,
    register_material,
)

# ── Composite multi-valued types
from emergent_matter_materials.bh_curve import BHCurveData

# ── Auto-load catalog at import time so MATERIALS is ready for consumers
from emergent_matter_materials.catalog._loader import load_all as _load_catalog
from emergent_matter_materials.crystal_anisotropy import CrystalAnisotropy
from emergent_matter_materials.electromagnetic import Electromagnetic
from emergent_matter_materials.manufacturing import Manufacturing, ProcessFit

# ── Composite type
from emergent_matter_materials.material import Material, MaterialCategory
from emergent_matter_materials.property_value import (
    ConfidenceLevel,
    PropertyValue,
)
from emergent_matter_materials.rotational_loss import RotationalLossData, RotationalLossForm
from emergent_matter_materials.steinmetz import SteinmetzData

# ── Group dataclasses
from emergent_matter_materials.structural import (
    STRENGTH_BASES,
    STRENGTH_BASIS_DERATED_ULTIMATE,
    STRENGTH_BASIS_ULTIMATE,
    STRENGTH_BASIS_UNKNOWN,
    STRENGTH_BASIS_YIELD,
    Structural,
    StructuralStrength,
    StructuralStrengthUnavailable,
)
from emergent_matter_materials.thermal import Thermal

# ── Units-map helpers (occasionally useful for downstream validators)
from emergent_matter_materials.units_map import expected_units_for

_load_catalog()
del _load_catalog


__all__ = [
    # Accessors
    "MATERIALS",
    "STRENGTH_BASES",
    "STRENGTH_BASIS_DERATED_ULTIMATE",
    "STRENGTH_BASIS_ULTIMATE",
    "STRENGTH_BASIS_UNKNOWN",
    "STRENGTH_BASIS_YIELD",
    # Composite multi-valued types
    "BHCurveData",
    # Core
    "ConfidenceLevel",
    "CoverageReport",
    "CrystalAnisotropy",
    "Electromagnetic",
    "Manufacturing",
    # Composite
    "Material",
    "MaterialCategory",
    "ProcessFit",
    "PropertyValue",
    "RotationalLossData",
    "RotationalLossForm",
    "SteinmetzData",
    # Groups
    "Structural",
    # Structural strength resolver (v1.10.0)
    "StructuralStrength",
    "StructuralStrengthUnavailable",
    "Thermal",
    "__catalog_version__",
    "__version__",
    "coverage",
    # Helpers
    "expected_units_for",
    "get",
    "get_material",
    "get_structural_strength",
    "get_with_metadata",
    "list_aliases",
    "list_materials",
    "list_properties",
    "material_summary",
    "register_material",
]
