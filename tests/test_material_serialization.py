"""Every catalog material round-trips through dataclasses.asdict and JSON, tables included.

Consumers serialize materials (artifact records, caches, web payloads).
The temperature-table field must not break that, even when empty, which
is every material's default.
"""

from __future__ import annotations

import dataclasses
import json

from emergent_matter_materials import MATERIALS, PropertyTable, Thermal


def test_gate_every_catalog_material_serializes_to_json():
    failures = []
    for s_id, material in MATERIALS.items():
        try:
            json.dumps(dataclasses.asdict(material))
        except TypeError as err:
            failures.append(f"{s_id}: {err}")
    assert not failures, "\n".join(failures)


def test_populated_tables_serialize_with_every_row_and_its_provenance():
    thermal = Thermal(
        temperature_tables={
            "thermal_conductivity": PropertyTable.from_rows(
                [(25.0, 10.0), (500.0, 16.0)],
                s_units="W/(m*K)",
                s_source="Test source A",
                s_confidence="datasheet",
            )
        }
    )
    payload = json.loads(json.dumps(dataclasses.asdict(thermal)))
    rows = payload["temperature_tables"]["thermal_conductivity"]["points"]
    assert [r["d_temperature_C"] for r in rows] == [25.0, 500.0]
    assert {r["value"]["s_source"] for r in rows} == {"Test source A"}
