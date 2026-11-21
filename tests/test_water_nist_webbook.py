"""Gate: every number in the water entry matches the saved NIST WebBook response.

The water entry in ``catalog/liquids.py`` is typed in from the raw NIST
Chemistry WebBook files under ``data/nist_webbook_water/``. These tests read
those files, check they are the bytes ``SOURCE.json`` records, and check each
catalogued value (table rows and headline scalars) against the NIST row at
the same temperature in the file whose query URL the value cites. They also
check that no liquid row the catalog claims to use was skipped.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import pytest

from emergent_matter_materials import MATERIALS, PropertyValue, get, get_material

_DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "nist_webbook_water"

#: Catalog slot to (group, NIST column, factor from NIST units to catalog units).
_SLOTS: dict[str, tuple[str, str, float]] = {
    "density": ("structural", "Density (kg/m3)", 1.0),
    "dynamic_viscosity": ("thermal", "Viscosity (Pa*s)", 1.0),
    "thermal_conductivity": ("thermal", "Therm. Cond. (W/m*K)", 1.0),
    "specific_heat": ("thermal", "Cp (J/g*K)", 1000.0),
}

#: The catalog writes NIST's printed digits, so the only difference allowed
#: is float rounding of the x1000 specific-heat conversion.
_REL_TOL = 1e-12


def _source() -> dict:
    return json.loads((_DATA_DIR / "SOURCE.json").read_text(encoding="utf-8"))


def _rows(s_file: str) -> list[dict[str, str]]:
    with (_DATA_DIR / s_file).open(encoding="ascii", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def _nist_row(s_url: str, d_temperature_C: float) -> dict[str, str]:
    """The NIST liquid row at a temperature, from the file fetched with ``s_url``."""
    (s_file,) = (name for name, meta in _source()["files"].items() if meta["url"] == s_url)
    matches = [
        row
        for row in _rows(s_file)
        if float(row["Temperature (C)"]) == d_temperature_C and row["Phase"] == "liquid"
    ]
    assert len(matches) == 1, f"{s_file}: expected one liquid row at {d_temperature_C} C"
    return matches[0]


def _cited_url(pv: PropertyValue) -> str:
    """The NIST query URL a value cites (one of the URLs in SOURCE.json)."""
    urls = [meta["url"] for meta in _source()["files"].values() if meta["url"] in pv.s_source]
    assert len(urls) == 1, f"value cites {len(urls)} NIST query URLs: {pv.s_source!r}"
    return urls[0]


def _check_against_nist(s_slot: str, d_temperature_C: float, pv: PropertyValue) -> None:
    _s_group, s_column, d_factor = _SLOTS[s_slot]
    row = _nist_row(_cited_url(pv), d_temperature_C)
    assert row["Pressure (MPa)"] == "0.101325"
    assert pv.d_value == pytest.approx(float(row[s_column]) * d_factor, rel=_REL_TOL), (
        f"water {s_slot} at {d_temperature_C} C: catalog {pv.d_value}, NIST {row[s_column]}"
    )
    assert f"'{s_column}'" in pv.s_source
    assert pv.s_confidence == "standard"


def test_saved_nist_files_are_the_recorded_bytes():
    for s_file, meta in _source()["files"].items():
        s_digest = hashlib.sha256((_DATA_DIR / s_file).read_bytes()).hexdigest()
        assert s_digest == meta["sha256"], f"{s_file} changed since it was fetched"


@pytest.mark.parametrize("s_slot", sorted(_SLOTS), ids=sorted(_SLOTS))
def test_every_water_table_row_matches_nist(s_slot):
    s_group, _s_column, _d_factor = _SLOTS[s_slot]
    table = getattr(MATERIALS["water"], s_group).table(s_slot)
    for point in table.points:
        _check_against_nist(s_slot, point.d_temperature_C, point.value)


@pytest.mark.parametrize("s_slot", sorted(_SLOTS), ids=sorted(_SLOTS))
def test_every_water_headline_scalar_matches_nist(s_slot):
    s_group, _s_column, _d_factor = _SLOTS[s_slot]
    pv = getattr(getattr(MATERIALS["water"], s_group), s_slot)
    _check_against_nist(s_slot, 20.0, pv)


def test_water_tables_use_every_liquid_row_of_the_5c_query():
    """No NIST liquid row from 5 C to the boiling point is left out, and none is invented."""
    s_file = "water_isobar_0.101325MPa_5C_to_100C.tsv"
    d_nist = [float(r["Temperature (C)"]) for r in _rows(s_file) if r["Phase"] == "liquid"]
    for s_slot, (s_group, _s_column, _d_factor) in _SLOTS.items():
        table = getattr(MATERIALS["water"], s_group).table(s_slot)
        assert list(table.d_temperatures_C) == [0.01, *d_nist], s_slot


def test_water_table_ends_at_the_saturated_liquid_row():
    rows = _rows("water_isobar_0.101325MPa_5C_to_100C.tsv")
    n_last_liquid = max(i for i, r in enumerate(rows) if r["Phase"] == "liquid")
    assert rows[n_last_liquid + 1]["Phase"] == "vapor"
    table = MATERIALS["water"].thermal.table("dynamic_viscosity")
    assert table.d_temperatures_C[-1] == float(rows[n_last_liquid]["Temperature (C)"])
    assert "saturated liquid" in table.points[-1].value.s_condition


def test_water_is_a_liquid_reachable_by_alias():
    water = get_material("H2O")
    assert water.s_category == "liquid"
    assert get("H2O", "mu_dyn") == pytest.approx(1.00160e-3, rel=_REL_TOL)


def test_water_interpolates_inside_and_raises_outside_the_liquid_range():
    table = MATERIALS["water"].thermal.table("dynamic_viscosity")
    d_mid = table.value_at(22.5)
    assert d_mid == pytest.approx(0.5 * (1.00160e-3 + 0.890022e-3), rel=_REL_TOL)
    with pytest.raises(ValueError, match="outside the tabulated range"):
        table.value_at(100.0)
