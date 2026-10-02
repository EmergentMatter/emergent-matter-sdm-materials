"""Catalog modules.

Each category module (metals, polymers, magnets, soft_magnetic, ceramics) exposes
a ``CATALOG`` dict mapping s_id → Material. The ``_loader.py`` module
walks the category modules and assembles them into the top-level
``MATERIALS`` dict that ``accessors.py`` consumes.

The loader is the **only** module that knows the catalog format. To
migrate from Python data files to YAML/TOML later, change only
``_loader.py``; the public API stays identical.
"""

from __future__ import annotations
