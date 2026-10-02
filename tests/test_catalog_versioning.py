"""Tests for catalog version metadata.

Three version sources must stay in lockstep:

  1. ``pyproject.toml`` `[project]` `version`: what `pip install`,
     `uv pip`, and Python's package metadata see.
  2. ``emergent_matter_materials.__version__``: the Python module's
     advertised package version.
  3. ``emergent_matter_materials.__catalog_version__``: the data
     semver, bumped independently in principle but in practice always
     kept synced with __version__ for this package (the catalog is
     the package's primary deliverable).

Drift in any of the three breaks downstream consumers. The v1.3.0
release shipped with `pyproject.toml` stuck at the original `0.1.0`
scaffold value while the module reported `1.3.0`, which meant
`importlib.metadata.version("emergent-matter-sdm-materials")` returned
`0.1.0` and a hypothetical downstream pin like
`emergent-matter-sdm-materials >= 1.3.0` would have failed to resolve.
The tests below prevent recurrence.
"""

from __future__ import annotations

import importlib.metadata
import re
from pathlib import Path

from emergent_matter_materials import __catalog_version__, __version__
from emergent_matter_materials.accessors import MATERIALS

_SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(?:[.-]\w+)?$")
_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_PYPROJECT_VERSION_RE = re.compile(r'^version\s*=\s*"([^"]+)"', re.MULTILINE)


def _read_pyproject_version() -> str:
    """Parse `[project] version = "X.Y.Z"` directly from pyproject.toml.

    We avoid using `tomllib` or `tomli_w`: a tiny regex is enough for
    the single `version = "..."` line and keeps this test free of any
    extra dependency. The regex deliberately anchors to the start of a
    line so it never confuses the `[project]` version with a
    transitive dependency's pin or a build-system version.
    """
    repo_root = Path(__file__).resolve().parents[1]
    pyproject = (repo_root / "pyproject.toml").read_text(encoding="utf-8")
    m = _PYPROJECT_VERSION_RE.search(pyproject)
    if m is None:
        raise AssertionError('pyproject.toml does not contain a top-level `version = "..."` line.')
    return m.group(1)


def test_catalog_version_is_semver():
    assert _SEMVER_RE.match(__catalog_version__), (
        f"__catalog_version__ {__catalog_version__!r} is not semver"
    )


def test_every_material_catalog_version_is_semver():
    for s_id, m in MATERIALS.items():
        assert _SEMVER_RE.match(m.s_catalog_version), (
            f"{s_id}: s_catalog_version {m.s_catalog_version!r} is not semver"
        )


def test_every_material_last_reviewed_iso_date():
    for s_id, m in MATERIALS.items():
        assert _ISO_DATE_RE.match(m.s_last_reviewed), (
            f"{s_id}: s_last_reviewed {m.s_last_reviewed!r} is not ISO 8601 YYYY-MM-DD"
        )


# An unreleased tree carries this catalog version until the first release
# bumps it; no stamp can be checked against a release that does not exist yet.
_UNRELEASED = "0.0.0"


def _stamps_ahead_of(catalog_version: str, stamps: dict[str, str]) -> list[str]:
    """The s_ids whose stamp is newer than ``catalog_version``. Empty for an
    unreleased tree."""
    if catalog_version == _UNRELEASED:
        return []
    cur = tuple(int(p) for p in catalog_version.split("."))
    return [s_id for s_id, stamp in stamps.items() if tuple(int(p) for p in stamp.split(".")) > cur]


def test_no_material_version_exceeds_package_catalog_version():
    """A Material's s_catalog_version <= __catalog_version__.
    Materials shouldn't claim a future catalog version."""
    stamps = {s_id: m.s_catalog_version for s_id, m in MATERIALS.items()}
    assert _stamps_ahead_of(__catalog_version__, stamps) == []


def test_stamp_check_flags_a_stamp_newer_than_the_catalog():
    assert _stamps_ahead_of("1.0.0", {"a": "1.0.0", "b": "1.0.1"}) == ["b"]
    assert _stamps_ahead_of("2.1.0", {"a": "1.9.9", "b": "2.1.0"}) == []


def test_stamp_check_skips_an_unreleased_tree():
    assert _stamps_ahead_of(_UNRELEASED, {"a": "1.0.0", "b": "9.9.9"}) == []


# ── Cross-source version consistency (added after the v1.3.0 drift) ────


def test_module_version_matches_catalog_version():
    """``__version__`` and ``__catalog_version__`` must agree.

    They have independent semver rules in principle (package semver
    vs. data semver), but in practice this package's primary deliverable
    IS the catalog data, so the two always move together. Drift here
    would mean a downstream optimizer recording "ran against
    emergent-matter-sdm-materials __version__=X, __catalog_version__=Y"
    with X != Y, which is a provenance-recording footgun.
    """
    assert __version__ == __catalog_version__, (
        f"__version__ ({__version__!r}) drifted from "
        f"__catalog_version__ ({__catalog_version__!r}). Bump both "
        f"together when cutting a release."
    )


def test_pyproject_version_matches_module_version():
    """``pyproject.toml`` `[project] version` must match ``__version__``.

    Drift here breaks ``importlib.metadata.version()`` resolution, which
    in turn breaks any downstream `emergent-matter-sdm-materials >= X.Y.Z`
    dependency pin. The v1.3.0 release shipped with pyproject stuck at
    0.1.0 while the module reported 1.3.0; this test would have caught
    it. When bumping the version, edit BOTH pyproject.toml AND
    __init__.py, then run ``uv sync`` to refresh uv.lock.
    """
    pyproject_version = _read_pyproject_version()
    assert pyproject_version == __version__, (
        f"pyproject.toml version ({pyproject_version!r}) drifted from "
        f"module __version__ ({__version__!r}). Update pyproject.toml "
        f"and re-run `uv sync` to refresh uv.lock."
    )


def test_installed_package_metadata_matches_module_version():
    """``importlib.metadata.version("emergent-matter-sdm-materials")``
    must match ``__version__``.

    This is the strictest gate: it catches the case where pyproject.toml
    has been edited but the editable install hasn't been refreshed
    (which would still pass ``test_pyproject_version_matches_module_version``
    above but fail in any downstream consumer that resolves via
    ``importlib.metadata``).

    If this test fails locally after a version bump, run
    ``uv sync --all-extras`` to refresh the editable install and try
    again.
    """
    try:
        installed = importlib.metadata.version("emergent-matter-sdm-materials")
    except importlib.metadata.PackageNotFoundError:
        # Package not installed (e.g. running from a fresh checkout
        # without `uv sync`). Skip rather than fail: the previous test
        # already validates the pyproject side.
        import pytest

        pytest.skip(
            "emergent-matter-sdm-materials not installed; "
            "run `uv sync --all-extras` to enable this gate"
        )
    assert installed == __version__, (
        f"importlib.metadata reports installed version {installed!r}, "
        f"but module __version__ is {__version__!r}. The editable "
        f"install is stale; run `uv sync --all-extras` to refresh."
    )
