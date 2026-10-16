"""Group tables and flow curves obey their scalar slots' rules, and every consumer sees them.

Pins that a table key must be a scalar slot of its group, in that slot's
units, with that slot's physical range enforced on every row; that groups
stay hashable and replace-able with tables attached; that the new scalar
slots validate; and that coverage() and the JAX pytree report tables.
"""

from __future__ import annotations

import dataclasses

import pytest

from emergent_matter_materials import (
    Electromagnetic,
    FlowCurve,
    Material,
    PropertyTable,
    PropertyTableMap,
    PropertyValue,
    Structural,
    Thermal,
    coverage,
)

#: JAX defaults to float32, which carries about 7 significant digits; this
#: tolerance absorbs that storage rounding, not any computation.
FLOAT32_REL_TOL = 1e-6


def _pv(d_value: float, s_units: str) -> PropertyValue:
    return PropertyValue(
        d_value=d_value, s_units=s_units, s_source="Test source A", s_confidence="datasheet"
    )


def _table(rows, s_units: str, **kwargs) -> PropertyTable:
    return PropertyTable.from_rows(
        rows, s_units=s_units, s_source="Test source A", s_confidence="datasheet", **kwargs
    )


def _conductivity_table() -> PropertyTable:
    return _table([(25.0, 10.0), (500.0, 16.0), (1000.0, 25.0)], "W/(m*K)")


def _material(**groups) -> Material:
    return Material(
        s_id="test_alloy",
        s_description="Test alloy",
        s_category="metal",
        s_specification="TEST-1",
        s_catalog_version="1.0.0",
        s_last_reviewed="2026-10-16",
        **groups,
    )


# ── Attaching and reading tables ───────────────────────────────────────────


def test_a_plain_dict_of_tables_is_frozen_into_a_read_only_map():
    thermal = Thermal(temperature_tables={"thermal_conductivity": _conductivity_table()})
    assert isinstance(thermal.temperature_tables, PropertyTableMap)
    assert thermal.table("thermal_conductivity").value_at(500.0) == 16.0


def test_a_table_can_exist_without_its_scalar_slot():
    thermal = Thermal(temperature_tables={"thermal_conductivity": _conductivity_table()})
    assert thermal.thermal_conductivity is None


def test_asking_for_a_missing_table_names_the_tables_that_exist():
    thermal = Thermal(temperature_tables={"thermal_conductivity": _conductivity_table()})
    with pytest.raises(
        ValueError, match=r"no table for 'specific_heat'.*\['thermal_conductivity'\]"
    ):
        thermal.table("specific_heat")


def test_every_group_with_tables_defaults_to_an_empty_map():
    for group in (Structural(), Thermal(), Electromagnetic()):
        assert len(group.temperature_tables) == 0


def test_electromagnetic_resistivity_can_be_tabulated():
    em = Electromagnetic(
        temperature_tables={
            "resistivity": _table([(20.0, 1.7e-8), (200.0, 3.0e-8)], "Ohm*m"),
        }
    )
    assert em.table("resistivity").value_at(20.0) == 1.7e-8


def test_resistivity_is_tabulated_under_its_property_name_not_the_20c_slot():
    with pytest.raises(ValueError, match="'resistivity_at_20C' is not a tabulable property"):
        Electromagnetic(
            temperature_tables={"resistivity_at_20C": _table([(20.0, 1.7e-8)], "Ohm*m")}
        )


def test_electromagnetic_rows_get_the_electromagnetic_range_checks():
    with pytest.raises(ValueError, match=r"'resistivity'\] point at 200.0 C: .*must be positive"):
        Electromagnetic(
            temperature_tables={"resistivity": _table([(20.0, 1.7e-8), (200.0, -1.0)], "Ohm*m")}
        )


# ── Validation reaches every row ───────────────────────────────────────────


def test_table_key_must_be_a_tabulable_property_of_the_group():
    with pytest.raises(ValueError, match="'youngs_modulus' is not a tabulable property of Thermal"):
        Thermal(temperature_tables={"youngs_modulus": _table([(25.0, 2e11)], "Pa")})


def test_table_units_must_match_the_slot():
    with pytest.raises(
        ValueError, match=r"temperature_tables\['thermal_conductivity'\]: wrong units"
    ):
        Thermal(temperature_tables={"thermal_conductivity": _table([(25.0, 0.01)], "W/(mm*K)")})


def test_table_value_must_be_a_property_table():
    with pytest.raises(TypeError, match="must be a PropertyTable"):
        Thermal(temperature_tables={"thermal_conductivity": 10.0})  # type: ignore[dict-item]


def test_tables_field_must_be_a_mapping():
    with pytest.raises(TypeError, match="must be a mapping"):
        Thermal(temperature_tables=[_conductivity_table()])  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("s_slot", "rows", "s_units", "match"),
    [
        (
            "emissivity",
            [(25.0, 0.5), (1500.0, 1.2)],
            "",
            "point at 1500.0 C: emissivity must be in",
        ),
        (
            "thermal_conductivity",
            [(25.0, 10.0), (900.0, -1.0)],
            "W/(m*K)",
            "point at 900.0 C: thermal_conductivity must be positive",
        ),
        (
            "specific_heat",
            [(25.0, 0.0)],
            "J/(kg*K)",
            "point at 25.0 C: specific_heat must be positive",
        ),
    ],
    ids=["emissivity-above-one", "negative-conductivity", "zero-specific-heat"],
)
def test_every_row_passes_the_slots_own_range_check(s_slot, rows, s_units, match):
    with pytest.raises(ValueError, match=match):
        Thermal(temperature_tables={s_slot: _table(rows, s_units)})


def test_structural_rows_get_the_structural_range_checks():
    with pytest.raises(ValueError, match=r"poisson_ratio'\] point at 1100.0 C"):
        Structural(temperature_tables={"poisson_ratio": _table([(25.0, 0.3), (1100.0, 0.6)], "")})


def test_only_cte_tables_may_be_secant():
    secant_cte = _table([(100.0, 1.1e-5), (500.0, 1.4e-5)], "1/K", d_reference_temperature_C=20.0)
    assert (
        Thermal(temperature_tables={"thermal_expansion": secant_cte})
        .table("thermal_expansion")
        .b_is_secant
    )

    secant_k = _table([(25.0, 10.0)], "W/(m*K)", d_reference_temperature_C=20.0)
    with pytest.raises(ValueError, match="only .* tables can be secant"):
        Thermal(temperature_tables={"thermal_conductivity": secant_k})


# ── New scalar slots ───────────────────────────────────────────────────────


def test_melting_range_slots_validate_and_read_back():
    thermal = Thermal(
        solidus_temp=_pv(1260.0, "C"),
        liquidus_temp=_pv(1336.0, "C"),
        latent_heat_fusion=_pv(2.27e5, "J/kg"),
    )
    assert thermal.d_solidus_temp_C == 1260.0
    assert thermal.d_liquidus_temp_C == 1336.0
    assert thermal.d_latent_heat_fusion_J_kg == 2.27e5


def test_solidus_above_liquidus_is_rejected():
    with pytest.raises(ValueError, match="solidus can't exceed the liquidus"):
        Thermal(solidus_temp=_pv(1400.0, "C"), liquidus_temp=_pv(1300.0, "C"))


def test_latent_heat_must_be_positive():
    with pytest.raises(ValueError, match="latent_heat_fusion must be positive"):
        Thermal(latent_heat_fusion=_pv(0.0, "J/kg"))


def test_stress_relaxation_temp_reads_back_and_rejects_below_absolute_zero():
    assert Structural(stress_relaxation_temp=_pv(640.0, "C")).d_stress_relaxation_temp_C == 640.0
    with pytest.raises(
        ValueError, match="stress_relaxation_temp = -300.0 C is below absolute zero"
    ):
        Structural(stress_relaxation_temp=_pv(-300.0, "C"))


def test_flow_curve_slot_rejects_other_types():
    with pytest.raises(TypeError, match="Structural.flow_curve must be a FlowCurve"):
        Structural(flow_curve=((25.0, 0.0, 276e6),))  # type: ignore[arg-type]


# ── Groups stay hashable and replace-able ──────────────────────────────────


def test_groups_and_materials_with_tables_stay_hashable():
    thermal = Thermal(temperature_tables={"thermal_conductivity": _conductivity_table()})
    structural = Structural(
        flow_curve=FlowCurve.from_rows(
            [(25.0, 0.0, 276e6)], s_source="Test source A", s_confidence="datasheet"
        )
    )
    material = _material(structural=structural, thermal=thermal)
    assert hash(material) == hash(_material(structural=structural, thermal=thermal))


def test_replace_revalidates_and_refreezes_tables():
    thermal = Thermal(temperature_tables={"thermal_conductivity": _conductivity_table()})
    swapped = dataclasses.replace(
        thermal, temperature_tables={"specific_heat": _table([(25.0, 450.0)], "J/(kg*K)")}
    )
    assert isinstance(swapped.temperature_tables, PropertyTableMap)
    assert list(swapped.temperature_tables) == ["specific_heat"]
    with pytest.raises(ValueError, match="not a tabulable property"):
        dataclasses.replace(thermal, temperature_tables={"bogus": _conductivity_table()})


# ── Consumers see tables ───────────────────────────────────────────────────


def test_coverage_counts_tables_and_reports_the_flow_curve():
    material = _material(
        thermal=Thermal(temperature_tables={"thermal_conductivity": _conductivity_table()}),
        structural=Structural(
            flow_curve=FlowCurve.from_rows(
                [(25.0, 0.0, 276e6)], s_source="Test source A", s_confidence="datasheet"
            )
        ),
    )
    groups = coverage(material)["groups"]
    assert groups["thermal"]["composites"]["temperature_tables"] == 1
    assert groups["structural"]["composites"]["temperature_tables"] == 0
    assert groups["structural"]["composites"]["flow_curve"] is True
    assert "temperature_tables" not in groups["thermal"]["fields"]


def test_jax_pytree_flattens_tables_and_flow_curves_into_arrays():
    pytest.importorskip("jax")
    from emergent_matter_materials.jax_interop import to_jax_pytree

    material = _material(
        thermal=Thermal(
            temperature_tables={
                "thermal_conductivity": _conductivity_table(),
                "thermal_expansion": _table(
                    [(100.0, 1.1e-5), (500.0, 1.4e-5)], "1/K", d_reference_temperature_C=20.0
                ),
            }
        ),
        structural=Structural(
            flow_curve=FlowCurve.from_rows(
                [(25.0, 0.0, 276e6), (25.0, 0.05, 310e6)],
                s_source="Test source A",
                s_confidence="datasheet",
            )
        ),
    )
    tree = to_jax_pytree(material, s_missing="omit")
    k_table = tree["thermal"]["temperature_tables"]["thermal_conductivity"]
    assert k_table["d_temperatures_C"].tolist() == pytest.approx(
        [25.0, 500.0, 1000.0], rel=FLOAT32_REL_TOL
    )
    assert k_table["d_values"].tolist() == pytest.approx([10.0, 16.0, 25.0], rel=FLOAT32_REL_TOL)
    assert "d_reference_temperature_C" not in k_table
    cte = tree["thermal"]["temperature_tables"]["thermal_expansion"]
    assert float(cte["d_reference_temperature_C"]) == pytest.approx(20.0, rel=FLOAT32_REL_TOL)
    flow = tree["structural"]["flow_curve"]
    assert flow["d_plastic_strains"].tolist() == pytest.approx([0.0, 0.05], rel=FLOAT32_REL_TOL)
    assert flow["d_stresses_Pa"].tolist() == pytest.approx([276e6, 310e6], rel=FLOAT32_REL_TOL)


def test_jax_pytree_skips_an_empty_table_map_under_every_policy():
    pytest.importorskip("jax")
    from emergent_matter_materials.jax_interop import to_jax_pytree

    material = _material(thermal=Thermal(thermal_conductivity=_pv(10.0, "W/(m*K)")))
    for s_missing in ("omit", "nan"):
        assert "temperature_tables" not in to_jax_pytree(material, s_missing=s_missing)["thermal"]


@pytest.mark.parametrize(
    ("group_cls", "s_key", "s_units"),
    [
        (Thermal, "melting_temp", "C"),
        (Thermal, "solidus_temp", "C"),
        (Thermal, "curie_temp", "C"),
        (Thermal, "max_operating_temp", "C"),
        (Thermal, "latent_heat_fusion", "J/kg"),
        (Structural, "stress_relaxation_temp", "C"),
    ],
    ids=["melting", "solidus", "curie", "max-operating", "latent-heat", "stress-relaxation"],
)
def test_temperatures_themselves_cannot_be_tabulated_against_temperature(group_cls, s_key, s_units):
    with pytest.raises(ValueError, match=f"'{s_key}' is not a tabulable property"):
        group_cls(temperature_tables={s_key: _table([(25.0, 1000.0)], s_units)})


def test_mean_specific_heat_may_be_secant():
    table = _table([(100.0, 460.0)], "J/(kg*K)", d_reference_temperature_C=20.0)
    assert Thermal(temperature_tables={"specific_heat": table}).table("specific_heat").b_is_secant


def test_yield_above_uts_at_a_shared_table_temperature_is_rejected():
    with pytest.raises(ValueError, match=r"yield_stress \(500000000.0 Pa\) > ultimate_tensile"):
        Structural(
            temperature_tables={
                "yield_stress": _table([(25.0, 500e6), (600.0, 200e6)], "Pa"),
                "ultimate_tensile": _table([(25.0, 300e6)], "Pa"),
            }
        )


def test_yield_and_uts_tables_at_different_temperatures_are_not_compared():
    structural = Structural(
        temperature_tables={
            "yield_stress": _table([(25.0, 500e6)], "Pa"),
            "ultimate_tensile": _table([(600.0, 300e6)], "Pa"),
        }
    )
    assert len(structural.temperature_tables) == 2


def test_positional_thermal_construction_keeps_its_old_meaning():
    """New Thermal fields are declared after emissivity, so the 9th positional arg is unchanged."""
    args = [None] * 8 + [_pv(0.5, "")]
    assert Thermal(*args).emissivity.d_value == 0.5
