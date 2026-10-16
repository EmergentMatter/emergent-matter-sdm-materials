"""2026-10-16 sweep: Young's modulus, Poisson's ratio and thermal gaps filled
from producer datasheets and standards (each value pinned to its source)."""

import pytest

from emergent_matter_materials import get_material


def test_bambu_tpu_95a_hf_printed_values():
    m = get_material("tpu_95a_hf_bambu")
    assert m.structural.d_youngs_modulus_Pa == pytest.approx(9.8e6)  # X-Y, ISO 527
    assert m.structural.d_ultimate_tensile_Pa == pytest.approx(27.3e6)
    assert m.structural.d_density_kg_m3 == pytest.approx(1220.0)
    assert m.structural.poisson_ratio is None and m.structural.yield_stress is None
    assert m.thermal.d_melting_temp_C == pytest.approx(183.0)


def test_sintered_ndfeb_modulus_is_the_mmpa_class_value():
    for key in ("ndfeb_n35", "ndfeb_n42", "ndfeb_n50", "ndfeb_n42sh", "ndfeb_n42uh", "ndfeb_n42eh"):
        pv = get_material(key).structural.youngs_modulus
        assert pv.d_value == pytest.approx(152e9)
        assert pv.s_confidence == "standard"


def test_alnico_5_service_limit_aluminium_1350_and_soft_magnetics():
    assert get_material("alnico_5_cast").thermal.d_max_operating_temp_C == pytest.approx(525.0)
    al = get_material("aluminum_1350_ec")
    assert al.structural.d_youngs_modulus_Pa == pytest.approx(68.9e9)
    assert al.thermal.d_thermal_conductivity_W_mK == pytest.approx(229.0)
    assert al.thermal.specific_heat is None  # garbled unit on the source page
    assert get_material("vitroperm_500f").structural.d_youngs_modulus_Pa == pytest.approx(150e9)
    assert get_material("metglas_2605sa1").thermal.d_melting_temp_C == pytest.approx(1180.0)
    assert get_material("alumina_ad96").thermal.d_max_operating_temp_C == pytest.approx(1700.0)
    assert get_material("mnzn_ferrite_3c95").structural.youngs_modulus is None  # family range only


def test_polymer_gaps_from_producer_documents():
    pa = get_material("nylon12_sls").thermal
    assert pa.d_thermal_expansion_per_K == pytest.approx(1.09e-4)
    assert pa.d_specific_heat_J_kgK == pytest.approx(2350.0)
    assert get_material("pei_ultem_1010").structural.d_poisson_ratio == pytest.approx(0.36)
    assert get_material("mw_pai_class_200").thermal.d_specific_heat_J_kgK == pytest.approx(1012.0)
    assert get_material("kapton_hn").thermal.glass_transition is None  # a range only: stays empty
    assert get_material("pla_3dprint").thermal.glass_transition is None  # a range only: stays empty
