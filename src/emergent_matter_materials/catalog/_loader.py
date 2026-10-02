"""Catalog loader: assembles MATERIALS from per-category modules.

This is the single seam in the codebase that knows the catalog data
format. For v0.1.0 we use Python data files (one module per
category). If/when the catalog grows beyond ~50 materials or non-
coders need to edit entries, switching to YAML/TOML is a localized
change inside this module: the public API stays identical.

Call sites read from ``accessors.MATERIALS`` which is populated by
this loader on first import.
"""

from __future__ import annotations

from emergent_matter_materials.accessors import MATERIALS
from emergent_matter_materials.material import Material


def _merge(s_module_name: str, catalog_dict: dict[str, Material]) -> None:
    """Merge a category module's CATALOG dict into MATERIALS, asserting no
    key collisions across categories."""
    for s_id, m in catalog_dict.items():
        if s_id in MATERIALS:
            raise ValueError(
                f"Material s_id collision: {s_id!r} already registered from "
                f"another catalog module. Source: {s_module_name}."
            )
        if s_id != m.s_id:
            raise ValueError(
                f"Catalog dict key {s_id!r} != Material.s_id {m.s_id!r} in {s_module_name}"
            )
        MATERIALS[s_id] = m


def load_all() -> None:
    """Populate the top-level MATERIALS dict from every category module.

    Idempotent: re-calling does nothing if the catalog is already loaded.
    """
    if MATERIALS:
        return

    # Import lazily so that the loader file itself has no upward dependency
    # on the catalog data files (avoids circular import nightmares if a
    # data file needs to reference accessors for any reason).
    from emergent_matter_materials.catalog import (
        ceramics,
        magnets,
        metals,
        polymers,
        soft_magnetic,
    )

    _merge("catalog.metals", metals.CATALOG)
    _merge("catalog.polymers", polymers.CATALOG)
    _merge("catalog.magnets", magnets.CATALOG)
    _merge("catalog.soft_magnetic", soft_magnetic.CATALOG)
    _merge("catalog.ceramics", ceramics.CATALOG)


__all__ = ["load_all"]
