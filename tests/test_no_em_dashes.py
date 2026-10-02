"""STYLE.md forbids em dashes in every shipped file; this pins it for the code tree.

The rule exists because this repo's prose ships: ``s_notes`` and ``s_source``
strings are read back by consumers through ``get_with_metadata()``. Markdown
at the repo root is covered by the org template checks; this test covers the
Python under ``src/``, ``tests/``, and ``scripts/``, which those checks skip.
"""

from __future__ import annotations

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCANNED_DIRS = ("src", "tests", "scripts")
_EM_DASH = chr(0x2014)  # spelled out so this file passes its own scan


def _python_files() -> list[Path]:
    return sorted(p for d in _SCANNED_DIRS for p in (_REPO_ROOT / d).rglob("*.py"))


def test_scan_covers_the_code_tree():
    """Guard against the scan silently going empty if the layout moves."""
    assert len(_python_files()) > 10


def test_no_em_dash_in_shipped_python():
    offenders = []
    for path in _python_files():
        for n_line, s_line in enumerate(path.read_text(encoding="utf-8").split("\n"), start=1):
            if _EM_DASH in s_line:
                offenders.append(f"{path.relative_to(_REPO_ROOT)}:{n_line}")
    assert not offenders, (
        "Em dash (U+2014) found in shipped Python. STYLE.md: use plain "
        "punctuation, and keep the ' -- ' separator for s_source citation detail.\n"
        + "\n".join(offenders[:40])
    )
