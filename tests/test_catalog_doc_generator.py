"""Smoke tests for ``scripts/generate_catalog_doc.py``.

The catalog doc generator walks every Material at import time, so this
test catches any new material / new property / new group that breaks
the generator's assumptions (e.g. a non-PropertyValue field accidentally
slipping into a group dataclass, an unrecognized s_confidence value, a
material whose s_specification contains pipe characters that would break
markdown table rendering).

This is a smoke test, not a content-validation test: it confirms the
generator runs to completion and produces a non-empty document with the
expected sections.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPT_PATH = _REPO_ROOT / "scripts" / "generate_catalog_doc.py"


def _load_generator():
    """Import scripts/generate_catalog_doc.py as a module."""
    spec = importlib.util.spec_from_file_location("generate_catalog_doc", _SCRIPT_PATH)
    if spec is None or spec.loader is None:
        pytest.fail(f"Could not load generator from {_SCRIPT_PATH}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_generator_script_exists():
    """Generator script lives where the README says it does."""
    assert _SCRIPT_PATH.exists(), (
        f"Catalog doc generator missing at {_SCRIPT_PATH}. "
        f"README + CLAUDE.md reference it; if you moved it, update them."
    )


def test_generator_runs_and_produces_doc():
    """Generator walks every Material without raising + emits a doc."""
    mod = _load_generator()
    s_doc = mod.build()
    assert isinstance(s_doc, str)
    assert len(s_doc) > 1000, "Generated catalog doc is suspiciously small"


def test_generator_lists_every_material():
    """Every Material.s_id appears in the generated markdown."""
    from emergent_matter_materials import MATERIALS

    mod = _load_generator()
    s_doc = mod.build()
    for s_id in MATERIALS:
        assert f"`{s_id}`" in s_doc, (
            f"Material {s_id!r} not present in generated catalog.md: "
            f"the generator dropped it silently."
        )


def test_generator_lists_every_alias():
    """Every registered alias appears in the alias table."""
    from emergent_matter_materials import list_aliases

    mod = _load_generator()
    s_doc = mod.build()
    for s_alias in list_aliases():
        assert f"`{s_alias}`" in s_doc, f"Alias {s_alias!r} missing from generated catalog.md."


def test_generator_marks_doc_as_auto_generated():
    """Document opens with the do-not-hand-edit warning."""
    mod = _load_generator()
    s_doc = mod.build()
    assert "auto-generated" in s_doc.split("\n", 5)[2].lower(), (
        "Generator should mark the doc as auto-generated near the top so "
        "humans don't edit it by hand and lose changes on the next run."
    )


def test_generator_reports_current_versions():
    """Top of doc reflects the current __version__ and __catalog_version__."""
    from emergent_matter_materials import __catalog_version__, __version__

    mod = _load_generator()
    s_doc = mod.build()
    assert __catalog_version__ in s_doc
    assert __version__ in s_doc
