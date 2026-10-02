"""Tests for the magnet schema expansion: hardness, compressive strength,
perpendicular CTE, and (BH)max.

Per-grade values were read directly from the Arnold per-grade standalone
sheets (N35 Rev. 210607, N42 Rev. 210607, N50 Rev. 210802, N42SH Rev. 020821,
N42UH Rev. 210607, N42EH Rev. 151021a) and the Recoma 28 page (Rev. 131025)
of the Recoma combined catalog, cross-checked against the Arnold combined
NdFeB catalog Rev. 181031.
"""

from __future__ import annotations

import pytest

from emergent_matter_materials import Electromagnetic, Structural, Thermal, get, get_material
from emergent_matter_materials.accessors import _PROPERTY_MAP
from emergent_matter_materials.property_value import PropertyValue as PV

# ── schema ──────────────────────────────────────────────────────────────────


def _pv(d_value: float, s_units: str) -> PV:
    return PV(d_value=d_value, s_units=s_units, s_source="x", s_confidence="datasheet")


def test_structural_fields_and_accessors():
    s = Structural(hardness_vickers=_pv(620.0, "HV"), compressive_strength=_pv(800e6, "Pa"))
    assert s.d_hardness_HV == 620.0
    assert s.d_compressive_strength_Pa == 800e6


def test_thermal_perpendicular_cte_may_be_negative():
    t = Thermal(thermal_expansion_perpendicular=_pv(-1.0e-6, "1/K"))
    assert t.d_thermal_expansion_perpendicular_per_K == pytest.approx(-1.0e-6)


def test_electromagnetic_energy_product_accessor():
    em = Electromagnetic(energy_product_max=_pv(334e3, "J/m^3"))
    assert em.d_energy_product_max_J_m3 == 334e3


@pytest.mark.parametrize(
    ("group", "field", "accessor"),
    [
        (Structural, "hardness_vickers", "d_hardness_HV"),
        (Structural, "compressive_strength", "d_compressive_strength_Pa"),
        (Thermal, "thermal_expansion_perpendicular", "d_thermal_expansion_perpendicular_per_K"),
        (Electromagnetic, "energy_product_max", "d_energy_product_max_J_m3"),
    ],
)
def test_accessor_raises_when_absent(group, field, accessor):
    with pytest.raises(ValueError, match=field):
        getattr(group(), accessor)


@pytest.mark.parametrize(
    ("group", "field", "d_value", "s_wrong_units"),
    [
        (Structural, "hardness_vickers", 620.0, ""),
        (Structural, "compressive_strength", 800e6, "MPa"),
        (Thermal, "thermal_expansion_perpendicular", -1e-6, "ppm/K"),
        (Electromagnetic, "energy_product_max", 334e3, "kJ/m^3"),
    ],
)
def test_units_enforced(group, field, d_value, s_wrong_units):
    with pytest.raises(ValueError):
        group(**{field: _pv(d_value, s_wrong_units)})


@pytest.mark.parametrize(
    ("group", "field", "s_units"),
    [
        (Structural, "hardness_vickers", "HV"),
        (Structural, "compressive_strength", "Pa"),
        (Electromagnetic, "energy_product_max", "J/m^3"),
    ],
)
def test_positivity_enforced(group, field, s_units):
    with pytest.raises(ValueError, match="must be positive"):
        group(**{field: _pv(0.0, s_units)})


def test_short_names_in_property_map():
    assert _PROPERTY_MAP["HV"] == ("structural", "hardness_vickers")
    assert _PROPERTY_MAP["sigma_c"] == ("structural", "compressive_strength")
    assert _PROPERTY_MAP["CTE_perp"] == ("thermal", "thermal_expansion_perpendicular")
    assert _PROPERTY_MAP["BH_max"] == ("electromagnetic", "energy_product_max")


# ── catalog values (verified against the sheets named in the module docstring) ──

_MAGNETS = (
    "ndfeb_n35",
    "ndfeb_n42",
    "ndfeb_n50",
    "ndfeb_n42sh",
    "ndfeb_n42uh",
    "ndfeb_n42eh",
    "smco_2_17",
)

# nominal (BH)max in J/m^3, from the kJ/m3 row of each sheet's min/nominal/max table
_EXPECTED_BHMAX = {
    "ndfeb_n35": 283e3,  # 263 / 283 / 302 kJ/m3
    "ndfeb_n42": 334e3,  # 318 / 334 / 350
    "ndfeb_n50": 390e3,  # 374 / 390 / 406
    "ndfeb_n42sh": 330e3,  # 310 / 330 / 350
    "ndfeb_n42uh": 330e3,  # 310 / 330 / 350
    "ndfeb_n42eh": 326e3,  # 310 / 326 / 342
    "smco_2_17": 225e3,  # 195 min / 225 nominal (Recoma 28 page)
}

# perpendicular CTE, 1/K; source-of-record follows each grade's parallel value
_EXPECTED_CTE_PERP = {
    "ndfeb_n35": -1.0e-6,  # standalone sheets (7 // -1 perp)
    "ndfeb_n42": -1.0e-6,
    "ndfeb_n50": -1.0e-6,
    "ndfeb_n42sh": -0.1e-6,  # Catalog Rev. 181031 (7.5 // -0.1), per the v0.7.5 decision
    "ndfeb_n42uh": -0.1e-6,
    "ndfeb_n42eh": -0.1e-6,  # standalone and catalog agree
    "smco_2_17": 13.0e-6,  # Recoma 28 page: 11 // 13 perp
}


@pytest.mark.parametrize("s_id", _MAGNETS)
def test_hardness_populated_on_every_magnet(s_id):
    m = get_material(s_id)
    d_expected = 600.0 if s_id == "smco_2_17" else 620.0
    assert m.structural.d_hardness_HV == d_expected
    assert m.structural.hardness_vickers.s_confidence == "datasheet"


@pytest.mark.parametrize("s_id", _MAGNETS)
def test_energy_product_populated_on_every_magnet(s_id):
    m = get_material(s_id)
    assert m.electromagnetic.d_energy_product_max_J_m3 == pytest.approx(_EXPECTED_BHMAX[s_id])
    assert get(s_id, "BH_max") == pytest.approx(_EXPECTED_BHMAX[s_id])


@pytest.mark.parametrize("s_id", _MAGNETS)
def test_perpendicular_cte_populated_on_every_magnet(s_id):
    m = get_material(s_id)
    assert m.thermal.d_thermal_expansion_perpendicular_per_K == pytest.approx(
        _EXPECTED_CTE_PERP[s_id]
    )
    # the parallel value is still the one in the legacy slot
    assert m.thermal.thermal_expansion is not None


def test_compressive_strength_only_where_arnold_publishes_it():
    assert get_material("smco_2_17").structural.d_compressive_strength_Pa == 800e6
    for s_id in _MAGNETS[:-1]:
        assert get_material(s_id).structural.compressive_strength is None


def test_recoma_hardness_is_600_not_800():
    """Earlier module notes quoted 800 Hv; the Rev. 131025 page says 600 Hv
    (800 is the compressive strength in MPa on the same page)."""
    assert get("smco_2_17", "HV") == 600.0


def test_non_magnets_leave_the_new_slots_empty():
    cu = get_material("pure_copper")
    assert cu.structural.hardness_vickers is None
    assert cu.electromagnetic.energy_product_max is None
    assert cu.thermal.thermal_expansion_perpendicular is None
