"""Every value added in the 2026-10 gap fill reads back as its source prints it,
and every gap the sources leave open stays empty rather than being estimated."""

from __future__ import annotations

import pytest

from emergent_matter_materials import get_material

# Stored values are copied from the documents (or a stated exact unit
# conversion), so they must read back to float precision.
EXACT = 1e-12

NDFEB = ("ndfeb_n35", "ndfeb_n42", "ndfeb_n50", "ndfeb_n42sh", "ndfeb_n42uh", "ndfeb_n42eh")


def test_bambu_tpu_95a_hf_carries_its_printed_specimen_values():
    m = get_material("tpu_95a_hf_bambu")
    assert m.structural.d_youngs_modulus_Pa == pytest.approx(9.8e6, rel=EXACT)
    assert m.structural.d_ultimate_tensile_Pa == pytest.approx(27.3e6, rel=EXACT)
    assert m.structural.d_density_kg_m3 == pytest.approx(1220.0, rel=EXACT)
    assert m.thermal.d_melting_temp_C == pytest.approx(183.0, rel=EXACT)
    assert m.structural.poisson_ratio is None  # not published
    assert m.structural.yield_stress is None  # TPU has no yield point


def test_sintered_ndfeb_modulus_is_the_mmpa_class_value_and_poisson_stays_empty():
    for key in NDFEB:
        s = get_material(key).structural
        assert s.d_youngs_modulus_Pa == pytest.approx(152e9, rel=EXACT)
        assert s.youngs_modulus.s_confidence == "standard"
        assert s.poisson_ratio is None


def test_alnico_5_service_limit_is_the_mmpa_value():
    m = get_material("alnico_5_cast")
    assert m.thermal.d_max_operating_temp_C == pytest.approx(525.0, rel=EXACT)
    assert m.structural.poisson_ratio is None


def test_aluminium_1350_carries_the_wire_makers_values_but_not_its_garbled_specific_heat():
    m = get_material("aluminum_1350_ec")
    assert m.structural.d_youngs_modulus_Pa == pytest.approx(68.9e9, rel=EXACT)
    assert m.thermal.d_thermal_conductivity_W_mK == pytest.approx(229.0, rel=EXACT)
    assert m.thermal.d_thermal_expansion_per_K == pytest.approx(23.6e-6, rel=EXACT)
    assert m.thermal.d_melting_temp_C == pytest.approx(657.0, rel=EXACT)
    assert m.thermal.specific_heat is None
    assert m.structural.poisson_ratio is None


def test_soft_magnetic_gaps_stay_empty_where_only_family_or_unstated_values_exist():
    assert get_material("metglas_2605sa1").thermal.d_melting_temp_C == pytest.approx(
        1180.0, rel=EXACT
    )
    assert get_material("vitroperm_500f").structural is None or (
        get_material("vitroperm_500f").structural.youngs_modulus is None
    )
    ferrite = get_material("mnzn_ferrite_3c95")
    assert ferrite.structural is None or ferrite.structural.youngs_modulus is None
    assert ferrite.thermal.thermal_conductivity is None
    assert ferrite.thermal.specific_heat is None
    assert ferrite.thermal.thermal_expansion is None
    for key in ("hiperco_50", "metglas_2605sa1", "vitroperm_500f", "mu_metal"):
        s = get_material(key).structural
        assert s is None or s.poisson_ratio is None


def test_alumina_ad96_use_limit_is_the_rev_j_chart_value():
    assert get_material("alumina_ad96").thermal.d_max_operating_temp_C == pytest.approx(
        1700.0, rel=EXACT
    )


def test_polymer_values_read_back_and_descriptive_service_limits_are_not_stored():
    pa = get_material("nylon12_sls").thermal
    assert pa.d_thermal_expansion_per_K == pytest.approx(1.09e-4, rel=EXACT)
    assert pa.d_specific_heat_J_kgK == pytest.approx(2350.0, rel=EXACT)
    assert pa.d_thermal_conductivity_W_mK == pytest.approx(0.144, rel=EXACT)
    assert pa.max_operating_temp is None  # "-40 C till +80 C" is a generic PA 12 statement
    assert (
        get_material("kapton_hn").thermal.max_operating_temp is None
    )  # "used successfully at 400 C"
    assert get_material("pei_ultem_1010").structural.d_poisson_ratio == pytest.approx(
        0.36, rel=EXACT
    )
    assert get_material("mw_pai_class_200").thermal.d_specific_heat_J_kgK == pytest.approx(
        1012.0, rel=EXACT
    )
    assert get_material(
        "tpu_elastollan_1195a"
    ).thermal.d_thermal_conductivity_W_mK == pytest.approx(0.30, rel=EXACT)


def test_range_only_and_bound_only_values_stay_empty():
    assert get_material("kapton_hn").thermal.glass_transition is None  # 360-410 C range
    pla = get_material("pla_3dprint").thermal
    assert pla.glass_transition is None and pla.melting_temp is None  # SDS ranges
    petg = get_material("petg_3dprint")
    assert petg.thermal is None or petg.thermal.melting_temp is None  # SDS "> 220 C" bound


def test_bambu_tpu_has_its_own_alias():
    assert get_material("Bambu_TPU_95A_HF").s_id == "tpu_95a_hf_bambu"
