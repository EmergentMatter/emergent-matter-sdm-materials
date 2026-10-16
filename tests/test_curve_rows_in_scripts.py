"""The catalog doc and validation manifest list every curve point with its provenance.

No catalog material carries tables yet, so the smoke tests that run the
scripts over MATERIALS never reach the curve code paths. This file injects
a synthetic material and checks both scripts emit one line per point,
with that point's condition and source.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from emergent_matter_materials import (
    MATERIALS,
    FlowCurve,
    Material,
    PropertyTable,
    Structural,
    Thermal,
)

_SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
_PROBE_ID = "curve_probe"


def _load_script(s_name: str):
    spec = importlib.util.spec_from_file_location(s_name, _SCRIPTS / f"{s_name}.py")
    if spec is None or spec.loader is None:
        pytest.fail(f"Could not load scripts/{s_name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _probe_material() -> Material:
    return Material(
        s_id=_PROBE_ID,
        s_description="Curve probe",
        s_category="metal",
        s_specification="PROBE",
        s_catalog_version="1.0.0",
        s_last_reviewed="2026-10-16",
        thermal=Thermal(
            temperature_tables={
                "thermal_expansion": PropertyTable.from_rows(
                    [(100.0, 1.1e-5), (500.0, 1.4e-5)],
                    s_units="1/K",
                    s_source="Probe dilatometry report",
                    s_confidence="measured",
                    s_condition="annealed, dilatometer",
                    d_reference_temperature_C=20.0,
                )
            }
        ),
        structural=Structural(
            flow_curve=FlowCurve.from_rows(
                [(25.0, 0.0, 276e6), (25.0, 0.05, 310e6)],
                s_source="Probe tensile report",
                s_confidence="measured",
                s_condition="as-built, XY",
                s_stress_strain_measure="true",
            )
        ),
    )


def test_catalog_doc_lists_each_curve_point_with_condition_and_source(monkeypatch):
    monkeypatch.setitem(MATERIALS, _PROBE_ID, _probe_material())
    s_section = _load_script("generate_catalog_doc")._build_material_section(_PROBE_ID)

    cte_rows = [r for r in s_section.splitlines() if r.startswith("| `thermal_expansion")]
    assert len(cte_rows) == 2
    assert all("secant from 20 C" in r for r in cte_rows)
    assert all("annealed, dilatometer" in r and "Probe dilatometry report" in r for r in cte_rows)

    flow_rows = [r for r in s_section.splitlines() if r.startswith("| `flow_curve")]
    assert len(flow_rows) == 2
    assert all("(true stress-strain)" in r and "as-built, XY" in r for r in flow_rows)
    assert "plastic strain 0.05" in flow_rows[1]


def test_validation_manifest_has_one_row_per_curve_point(monkeypatch):
    monkeypatch.setitem(MATERIALS, _PROBE_ID, _probe_material())
    rows = [
        r for r in _load_script("validation_manifest")._walk_pvs() if r["material_id"] == _PROBE_ID
    ]
    assert sorted(r["field"] for r in rows) == [
        "flow_curve@25.0C,eps_p=0.0",
        "flow_curve@25.0C,eps_p=0.05",
        "thermal_expansion@100.0C",
        "thermal_expansion@500.0C",
    ]
    assert {r["s_condition"] for r in rows} == {"annealed, dilatometer", "as-built, XY"}
